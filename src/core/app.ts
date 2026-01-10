import type {
  ValidatedCLIArguments,
  Course,
  QueueItem,
  ProcessingResult,
  AppResult,
  QueueStats,
  GitHubSyncResult,
  GeneratorConfig,
} from "../types/index.ts";
import { join } from "node:path";
import { CourseDetector } from "../scanner/course-detector.ts";
import { FileRouter } from "../routing/file-router.ts";
import { FileProcessor } from "../processors/file-processor.ts";
import { OutputManager } from "../output/output-manager.ts";
import { AsyncQueue, createQueueItem } from "../queue/async-queue.ts";
import { WorkerPool } from "../queue/worker-pool.ts";
import { ErrorLogger } from "../logging/error-logger.ts";
import { logger } from "../logging/logger.ts";
import { Spinner, ProgressDisplay } from "../logging/spinner.ts";
import { SkillInvoker } from "../skills/skill-invoker.ts";

export class App {
  private args: ValidatedCLIArguments;
  private courseDetector: CourseDetector;
  private fileRouter: FileRouter;
  private fileProcessor: FileProcessor;
  private outputManager: OutputManager;
  private skillInvoker: SkillInvoker;
  private projectRoot: string;
  private dryRun: boolean;

  constructor(args: ValidatedCLIArguments, projectRoot: string) {
    this.args = args;
    this.projectRoot = projectRoot;
    this.dryRun = args.dryRun;
    this.courseDetector = new CourseDetector();
    this.fileRouter = new FileRouter(projectRoot);
    this.fileProcessor = new FileProcessor(projectRoot);
    this.outputManager = new OutputManager();
    this.skillInvoker = new SkillInvoker(projectRoot);
  }

  async run(): Promise<AppResult> {
    const startTime = new Date();
    const courseResults: AppResult["courses"] = [];
    let totalStats: QueueStats = {
      total: 0,
      pending: 0,
      processing: 0,
      completed: 0,
      failed: 0,
      skipped: 0,
    };

    // 1. Discover courses
    logger.info("Discovering courses...");
    const detection = this.courseDetector.detectCourses(
      this.args.resolvedInput,
      this.args.claudeCodeGenerated
    );

    // Print warnings
    for (const warning of detection.warnings) {
      logger.warn(warning);
    }

    if (detection.courses.length === 0) {
      logger.error("No courses found to process");
      return {
        success: false,
        courses: [],
        totalStats,
        startTime,
        endTime: new Date(),
      };
    }

    // Print course summary
    this.courseDetector.printSummary(detection.courses);

    // 2. Process each course
    for (const course of detection.courses) {
      logger.info(`\nProcessing course: ${course.name}`);

      const result = await this.processCourse(course);
      courseResults.push(result);

      // Aggregate stats
      totalStats.total += result.stats.total;
      totalStats.completed += result.stats.completed;
      totalStats.failed += result.stats.failed;
      totalStats.skipped += result.stats.skipped;
    }

    // 3. Generate content for each course (skip in dry-run)
    if (this.dryRun) {
      logger.info("\n[DRY-RUN] Would generate content for each course");
    } else {
      logger.info("\nGenerating content...");
      for (const course of detection.courses) {
        await this.generateContent(course);
      }
    }

    const endTime = new Date();

    // Print final summary
    this.printFinalSummary(totalStats, startTime, endTime);

    // Print GitHub sync summary if sync was enabled
    if (this.args.githubSync && !this.dryRun) {
      this.printGitHubSyncSummary();
    }

    return {
      success: totalStats.failed === 0,
      courses: courseResults,
      totalStats,
      startTime,
      endTime,
    };
  }

  private async processCourse(course: Course): Promise<AppResult["courses"][0]> {
    const startTime = Date.now();
    const results: ProcessingResult[] = [];
    const errors: AppResult["courses"][0]["errors"] = [];

    // Ensure output directories exist (skip in dry-run)
    if (!this.dryRun) {
      this.outputManager.ensureDirectories(course);
    }

    // Create error logger for this course
    const errorLogger = new ErrorLogger(course.codePath);

    // Create queue items from files
    const queueItems: QueueItem[] = [];

    for (const file of course.files) {
      // Route the file
      const decision = this.fileRouter.routeByExtension(file);

      // Skip unsupported files
      if (decision.method === "unsupported") {
        errorLogger.logWarning(
          `Unsupported file type: ${file.extension}`,
          file.path
        );
        continue;
      }

      // Skip video/audio
      if (decision.method === "skip") {
        continue;
      }

      // Calculate output path
      const outputPath = this.outputManager.getOutputPath(
        file,
        course.validatedFilesPath,
        decision.outputFormat
      );

      // Create queue item
      const item = createQueueItem(file, {
        stage: "convert",
      });
      item.routedTo = decision;
      item.outputPath = outputPath;

      queueItems.push(item);
    }

    logger.info(`  Queued ${queueItems.length} files for processing`);

    // In dry-run mode, just show what would be processed
    if (this.dryRun) {
      logger.info("  [DRY-RUN] Would process the following files:");
      for (const item of queueItems) {
        const method = item.routedTo?.method ?? "unknown";
        const skill = item.routedTo?.skillName ?? "passthrough";
        logger.info(`    ${item.file.name} -> ${method} (${skill})`);
      }
      return {
        course,
        stats: {
          total: queueItems.length,
          pending: 0,
          processing: 0,
          completed: queueItems.length,
          failed: 0,
          skipped: 0,
        },
        results: [],
        errors: [],
        totalDuration: Date.now() - startTime,
        totalTokens: 0,
        totalCost: 0,
      };
    }

    // Create worker pool
    const workerPool = new WorkerPool(
      this.args.workers,
      async (item) => this.fileProcessor.process(item)
    );

    // Set up progress display
    const progress = new ProgressDisplay(queueItems.length);
    progress.start();

    workerPool.setProgressCallback((result) => {
      progress.update(result.queueItem.file.name, result.success);

      if (!result.success && result.queueItem.error) {
        errorLogger.logProcessingError(
          result.queueItem.error,
          result.queueItem.file.path
        );
      }
    });

    // Submit all items
    await workerPool.submitMany(queueItems);

    // Start processing
    await workerPool.start();

    // Wait for completion
    const processingResults = await workerPool.waitForCompletion();

    // Stop progress display
    progress.stop();

    // Get final stats
    const stats = workerPool.getStats();

    // Write summary to error log
    errorLogger.writeSummary({
      total: stats.total,
      completed: stats.completed,
      failed: stats.failed,
      skipped: stats.skipped,
      duration: Date.now() - startTime,
    });

    logger.info(`  Completed: ${stats.completed}, Failed: ${stats.failed}, Skipped: ${stats.skipped}`);

    return {
      course,
      stats,
      results: processingResults,
      errors,
      totalDuration: Date.now() - startTime,
      totalTokens: 0,
      totalCost: 0,
    };
  }

  private syncResults: GitHubSyncResult[] = [];

  private async generateContent(course: Course): Promise<void> {
    const generators = this.args.generators;

    for (const generator of generators) {
      const spinner = new Spinner();
      spinner.start(`Generating ${generator.type} for ${course.name}...`);

      // Each generator gets its own output directory
      const generatorOutputPath = join(course.codePath, `__ccg_${generator.type}`);

      const result = await this.skillInvoker.invokeScript({
        skillName: generator.skill,
        prompt: "",
        filePath: course.validatedFilesPath,
        outputPath: generatorOutputPath,
        workingDirectory: this.projectRoot,
      });

      if (result.success) {
        spinner.success(`Generated ${generator.type} for ${course.name}`);

        // GitHub sync if enabled
        if (this.args.githubSync) {
          await this.syncToGitHub(course, generator);
        }
      } else {
        spinner.fail(`Failed to generate ${generator.type}: ${result.error?.message}`);
      }
    }
  }

  private async syncToGitHub(course: Course, generator: GeneratorConfig): Promise<void> {
    const assetPath = join(course.codePath, `__ccg_${generator.type}`);
    const discoveryPath = join(assetPath, "discovery.json");

    const result = await this.skillInvoker.invokeGitHubSync({
      assetPath,
      assetType: generator.type,
      discoveryPath,
    });

    this.syncResults.push(result);

    if (!result.success) {
      logger.warn(`  GitHub sync failed for ${generator.type}: ${result.error}`);
    }
  }

  private printGitHubSyncSummary(): void {
    if (this.syncResults.length === 0) return;

    const successful = this.syncResults.filter(r => r.success);
    const failed = this.syncResults.filter(r => !r.success);

    console.log("\n" + "=".repeat(50));
    console.log("GitHub Sync Summary");
    console.log("=".repeat(50));
    console.log(`  Synced:  ${successful.length}`);
    console.log(`  Failed:  ${failed.length}`);
    console.log("");

    for (const result of successful) {
      console.log(`  > ${result.repoName}`);
      if (result.repoUrl) {
        console.log(`    ${result.repoUrl}`);
      }
    }

    for (const result of failed) {
      console.log(`  x ${result.repoName} (${result.error})`);
    }

    console.log("=".repeat(50));
  }

  private printFinalSummary(
    stats: QueueStats,
    startTime: Date,
    endTime: Date
  ): void {
    const duration = (endTime.getTime() - startTime.getTime()) / 1000;

    console.log("\n" + "=".repeat(50));
    console.log("Processing Complete");
    console.log("=".repeat(50));
    console.log(`  Total files:  ${stats.total}`);
    console.log(`  Completed:    ${stats.completed}`);
    console.log(`  Failed:       ${stats.failed}`);
    console.log(`  Skipped:      ${stats.skipped}`);
    console.log(`  Duration:     ${duration.toFixed(2)}s`);
    console.log("=".repeat(50));
  }
}
