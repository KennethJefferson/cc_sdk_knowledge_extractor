import { readFileSync } from "node:fs";
import type {
  QueueItem,
  ProcessingResult,
  RoutingDecision,
  ScannedFile,
} from "../types/index.ts";
import { SkillInvoker } from "../skills/skill-invoker.ts";
import { OutputManager } from "../output/output-manager.ts";
import { logger } from "../logging/logger.ts";

export class FileProcessor {
  private skillInvoker: SkillInvoker;
  private outputManager: OutputManager;

  constructor(projectRoot: string) {
    this.skillInvoker = new SkillInvoker(projectRoot);
    this.outputManager = new OutputManager();
  }

  /**
   * Process a queue item based on its routing decision.
   */
  async process(item: QueueItem): Promise<ProcessingResult> {
    const startTime = Date.now();
    const warnings: string[] = [];

    if (!item.routedTo) {
      return {
        queueItem: item,
        success: false,
        duration: Date.now() - startTime,
        warnings: ["No routing decision for item"],
      };
    }

    const decision = item.routedTo;

    try {
      switch (decision.method) {
        case "passthrough":
          return await this.processPassthrough(item, startTime);

        case "skill":
          return await this.processWithSkill(item, decision, startTime);

        case "archive":
          return await this.processArchive(item, decision, startTime);

        case "skip":
          return {
            queueItem: item,
            success: true,
            duration: Date.now() - startTime,
            warnings: ["File skipped (video/audio)"],
          };

        case "unsupported":
          return {
            queueItem: item,
            success: false,
            duration: Date.now() - startTime,
            warnings: [`Unsupported file type: ${item.file.extension}`],
          };

        default:
          return {
            queueItem: item,
            success: false,
            duration: Date.now() - startTime,
            warnings: [`Unknown routing method: ${decision.method}`],
          };
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return {
        queueItem: item,
        success: false,
        duration: Date.now() - startTime,
        warnings: [errorMessage],
      };
    }
  }

  /**
   * Process passthrough files (copy to output).
   */
  private async processPassthrough(
    item: QueueItem,
    startTime: number
  ): Promise<ProcessingResult> {
    if (!item.outputPath) {
      return {
        queueItem: item,
        success: false,
        duration: Date.now() - startTime,
        warnings: ["No output path specified"],
      };
    }

    try {
      this.outputManager.copyFile(item.file.path, item.outputPath);

      return {
        queueItem: item,
        success: true,
        outputPath: item.outputPath,
        outputSize: item.file.size,
        duration: Date.now() - startTime,
        warnings: [],
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return {
        queueItem: item,
        success: false,
        duration: Date.now() - startTime,
        warnings: [`Failed to copy file: ${errorMessage}`],
      };
    }
  }

  /**
   * Process files using a skill.
   */
  private async processWithSkill(
    item: QueueItem,
    decision: RoutingDecision,
    startTime: number
  ): Promise<ProcessingResult> {
    if (!decision.skillName) {
      return {
        queueItem: item,
        success: false,
        duration: Date.now() - startTime,
        warnings: ["No skill specified in routing decision"],
      };
    }

    if (!item.outputPath) {
      return {
        queueItem: item,
        success: false,
        duration: Date.now() - startTime,
        warnings: ["No output path specified"],
      };
    }

    const result = await this.skillInvoker.invokeScript({
      skillName: decision.skillName,
      prompt: "",
      filePath: item.file.path,
      outputPath: item.outputPath,
      workingDirectory: item.file.coursePath,
    });

    if (result.success) {
      return {
        queueItem: item,
        success: true,
        outputPath: item.outputPath,
        duration: Date.now() - startTime,
        tokensUsed: 0, // Direct script invocation, no tokens
        warnings: [],
      };
    } else {
      return {
        queueItem: item,
        success: false,
        duration: Date.now() - startTime,
        warnings: [result.error?.message ?? "Skill invocation failed"],
      };
    }
  }

  /**
   * Process archive files (extract and queue contents).
   */
  private async processArchive(
    item: QueueItem,
    decision: RoutingDecision,
    startTime: number
  ): Promise<ProcessingResult> {
    if (!decision.skillName) {
      return {
        queueItem: item,
        success: false,
        duration: Date.now() - startTime,
        warnings: ["No skill specified for archive extraction"],
      };
    }

    const extractDir = this.outputManager.getArchiveOutputDir(
      item.file,
      item.file.coursePath
    );

    const result = await this.skillInvoker.invokeScript({
      skillName: decision.skillName,
      prompt: "",
      filePath: item.file.path,
      outputPath: extractDir,
      workingDirectory: item.file.coursePath,
    });

    if (result.success) {
      // Return the extracted files info for further processing
      const output = result.result as { files?: Array<{ path: string }> };
      const extractedFiles = output?.files ?? [];

      return {
        queueItem: item,
        success: true,
        outputPath: extractDir,
        duration: Date.now() - startTime,
        warnings: extractedFiles.length > 0
          ? [`Extracted ${extractedFiles.length} files for further processing`]
          : [],
      };
    } else {
      return {
        queueItem: item,
        success: false,
        duration: Date.now() - startTime,
        warnings: [result.error?.message ?? "Archive extraction failed"],
      };
    }
  }
}
