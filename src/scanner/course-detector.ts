import { readdirSync, statSync, existsSync, mkdirSync } from "node:fs";
import { join, basename } from "node:path";
import type { Course, ScannedFile } from "../types/index.ts";
import { OUTPUT_DIRS } from "../core/constants.ts";
import { Scanner } from "./scanner.ts";

export interface CourseDetectionResult {
  courses: Course[];
  warnings: string[];
  hasRootSrtFiles: boolean;
}

export class CourseDetector {
  private scanner: Scanner;

  constructor() {
    this.scanner = new Scanner();
  }

  /**
   * Detect courses in the input directory.
   * Each immediate subdirectory is treated as a course.
   */
  detectCourses(inputDir: string, contentType: string): CourseDetectionResult {
    const warnings: string[] = [];
    const courses: Course[] = [];

    if (!existsSync(inputDir)) {
      return { courses: [], warnings: ["Input directory does not exist"], hasRootSrtFiles: false };
    }

    // Check for .srt files in root (warning: user might be inside course folder)
    const rootFiles = readdirSync(inputDir);
    const hasRootSrtFiles = rootFiles.some((f) => f.toLowerCase().endsWith(".srt"));

    if (hasRootSrtFiles) {
      warnings.push(
        "Found .srt files in input root. You may be inside a course folder. " +
          "For multi-mode processing, run from the parent directory containing course folders."
      );
    }

    // Each subdirectory is a course
    for (const entry of rootFiles) {
      const entryPath = join(inputDir, entry);

      try {
        const stat = statSync(entryPath);
        if (!stat.isDirectory()) {
          continue;
        }
      } catch {
        continue;
      }

      // Skip hidden directories and __cc prefixed directories
      if (entry.startsWith(".") || entry.startsWith("__cc")) {
        continue;
      }

      const course = this.createCourse(entryPath, entry, contentType);
      courses.push(course);
    }

    if (courses.length === 0 && !hasRootSrtFiles) {
      warnings.push("No course directories found in input path");
    }

    return { courses, warnings, hasRootSrtFiles };
  }

  /**
   * Create a Course object from a directory.
   */
  private createCourse(coursePath: string, courseId: string, contentType: string): Course {
    const codePath = join(coursePath, OUTPUT_DIRS.codeFolder);
    const validatedFilesPath = join(codePath, OUTPUT_DIRS.validatedFiles);
    const generatedPath = join(codePath, `${OUTPUT_DIRS.generatedPrefix}${contentType}`);

    // Ensure CODE directory exists
    if (!existsSync(codePath)) {
      mkdirSync(codePath, { recursive: true });
    }

    // Check for existing .srt files
    const hasExistingSrt = this.hasSrtFiles(coursePath);

    // Scan all files in the course
    const files = this.scanner.scanDirectory(coursePath, courseId, coursePath);

    return {
      id: courseId,
      name: courseId, // Can be enhanced to parse a metadata file
      path: coursePath,
      codePath,
      validatedFilesPath,
      generatedPath,
      files,
      hasExistingSrt,
    };
  }

  /**
   * Check if directory contains .srt files.
   */
  private hasSrtFiles(dirPath: string): boolean {
    try {
      const entries = readdirSync(dirPath);
      return entries.some((e) => e.toLowerCase().endsWith(".srt"));
    } catch {
      return false;
    }
  }

  /**
   * Ensure output directories exist for a course.
   */
  ensureOutputDirs(course: Course): void {
    if (!existsSync(course.validatedFilesPath)) {
      mkdirSync(course.validatedFilesPath, { recursive: true });
    }
    if (!existsSync(course.generatedPath)) {
      mkdirSync(course.generatedPath, { recursive: true });
    }
  }

  /**
   * Print course summary.
   */
  printSummary(courses: Course[]): void {
    console.log(`\nDiscovered ${courses.length} course(s):\n`);

    for (const course of courses) {
      const fileCount = course.files.length;
      const totalSize = course.files.reduce((sum, f) => sum + f.size, 0);
      const sizeStr = this.formatSize(totalSize);

      console.log(`  ${course.name}`);
      console.log(`    Files: ${fileCount} (${sizeStr})`);
      console.log(`    Path: ${course.path}`);

      // Count by category
      const categories: Record<string, number> = {};
      for (const file of course.files) {
        categories[file.category] = (categories[file.category] ?? 0) + 1;
      }

      const categoryStr = Object.entries(categories)
        .map(([cat, count]) => `${cat}: ${count}`)
        .join(", ");

      if (categoryStr) {
        console.log(`    Types: ${categoryStr}`);
      }
      console.log();
    }
  }

  private formatSize(bytes: number): string {
    if (bytes >= 1024 * 1024 * 1024) {
      return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
    }
    if (bytes >= 1024 * 1024) {
      return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    }
    if (bytes >= 1024) {
      return `${(bytes / 1024).toFixed(2)} KB`;
    }
    return `${bytes} B`;
  }
}
