import { existsSync, mkdirSync, copyFileSync, writeFileSync } from "node:fs";
import { dirname, join, basename, relative } from "node:path";
import type { ScannedFile, RoutingDecision, Course } from "../types/index.ts";

export class OutputManager {
  /**
   * Ensure all output directories exist for a course.
   */
  ensureDirectories(course: Course): void {
    const dirs = [course.codePath, course.validatedFilesPath, course.generatedPath];

    for (const dir of dirs) {
      if (!existsSync(dir)) {
        mkdirSync(dir, { recursive: true });
      }
    }
  }

  /**
   * Get the output path for a file.
   * Flattens directory structure with underscores.
   */
  getOutputPath(
    file: ScannedFile,
    outputDir: string,
    outputFormat?: string
  ): string {
    // Get relative path from course root
    const relPath = relative(file.coursePath, file.path);
    const relDir = dirname(relPath);

    // Create flattened filename with path prefix
    let prefix = "";
    if (relDir && relDir !== ".") {
      prefix = relDir.replace(/[\\/]/g, "_") + "_";
    }

    // Determine output extension
    const currentExt = file.extension;
    const newExt = outputFormat && outputFormat !== "directory" ? outputFormat : currentExt;

    // Build output filename
    const baseName = basename(file.name, currentExt);
    const outputName = `${prefix}${baseName}${newExt}`;

    return join(outputDir, outputName);
  }

  /**
   * Copy a file to the output directory (for passthrough files).
   */
  copyFile(sourcePath: string, destPath: string): void {
    const destDir = dirname(destPath);
    if (!existsSync(destDir)) {
      mkdirSync(destDir, { recursive: true });
    }
    copyFileSync(sourcePath, destPath);
  }

  /**
   * Write content to a file.
   */
  writeFile(destPath: string, content: string): void {
    const destDir = dirname(destPath);
    if (!existsSync(destDir)) {
      mkdirSync(destDir, { recursive: true });
    }
    writeFileSync(destPath, content, "utf-8");
  }

  /**
   * Check if an output file already exists.
   */
  outputExists(outputPath: string): boolean {
    return existsSync(outputPath);
  }

  /**
   * Get the extraction directory for an archive.
   */
  getArchiveOutputDir(file: ScannedFile, outputDir: string): string {
    // Extract archive contents to a subdirectory named after the archive
    let baseName = basename(file.name, file.extension);
    // Handle compound extensions like .tar.gz
    if (baseName.endsWith(".tar")) {
      baseName = baseName.slice(0, -4);
    }
    return join(outputDir, `__extracted_${baseName}`);
  }
}
