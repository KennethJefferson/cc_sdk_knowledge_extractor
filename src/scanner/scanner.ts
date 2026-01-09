import { readdirSync, statSync, existsSync } from "node:fs";
import { join, relative, extname, basename } from "node:path";
import type { ScannedFile, FileCategory } from "../types/index.ts";
import { FILE_EXTENSIONS, SKIP_EXTENSIONS } from "../core/constants.ts";

export interface ScanOptions {
  recursive?: boolean;
  includeHidden?: boolean;
  excludePatterns?: string[];
}

export class Scanner {
  private excludePatterns: RegExp[] = [];

  constructor(options: ScanOptions = {}) {
    if (options.excludePatterns) {
      this.excludePatterns = options.excludePatterns.map(
        (p) => new RegExp(p.replace(/\*/g, ".*"))
      );
    }
  }

  /**
   * Scan a directory and return all files.
   */
  scanDirectory(
    dirPath: string,
    courseId: string,
    coursePath: string,
    options: ScanOptions = { recursive: true }
  ): ScannedFile[] {
    const files: ScannedFile[] = [];

    if (!existsSync(dirPath)) {
      return files;
    }

    this.scanRecursive(dirPath, courseId, coursePath, files, options);
    return files;
  }

  private scanRecursive(
    currentPath: string,
    courseId: string,
    coursePath: string,
    files: ScannedFile[],
    options: ScanOptions
  ): void {
    let entries: string[];
    try {
      entries = readdirSync(currentPath);
    } catch {
      return;
    }

    for (const entry of entries) {
      // Skip hidden files unless explicitly included
      if (!options.includeHidden && entry.startsWith(".")) {
        continue;
      }

      // Skip __cc prefixed directories (our output directories)
      if (entry.startsWith("__cc")) {
        continue;
      }

      const fullPath = join(currentPath, entry);

      // Check exclude patterns
      if (this.shouldExclude(fullPath)) {
        continue;
      }

      let stat;
      try {
        stat = statSync(fullPath);
      } catch {
        continue;
      }

      if (stat.isDirectory()) {
        if (options.recursive) {
          this.scanRecursive(fullPath, courseId, coursePath, files, options);
        }
      } else if (stat.isFile()) {
        const ext = this.getExtension(entry);
        const category = this.categorizeFile(ext);

        // Skip video/audio files
        if (category === "video" || category === "audio") {
          continue;
        }

        files.push({
          path: fullPath,
          relativePath: relative(coursePath, fullPath),
          name: entry,
          extension: ext,
          size: stat.size,
          category,
          courseId,
          coursePath,
        });
      }
    }
  }

  private shouldExclude(path: string): boolean {
    for (const pattern of this.excludePatterns) {
      if (pattern.test(path)) {
        return true;
      }
    }
    return false;
  }

  private getExtension(filename: string): string {
    // Handle compound extensions like .tar.gz
    const lowerName = filename.toLowerCase();
    const compoundExtensions = [".tar.gz", ".tar.bz2", ".tar.xz"];
    for (const ext of compoundExtensions) {
      if (lowerName.endsWith(ext)) {
        return ext;
      }
    }
    return extname(filename).toLowerCase();
  }

  private categorizeFile(extension: string): FileCategory {
    for (const [category, extensions] of Object.entries(FILE_EXTENSIONS)) {
      if (extensions.includes(extension)) {
        return category as FileCategory;
      }
    }
    return "unknown";
  }

  /**
   * Count files by category.
   */
  countByCategory(files: ScannedFile[]): Record<FileCategory, number> {
    const counts: Record<string, number> = {};
    for (const file of files) {
      counts[file.category] = (counts[file.category] ?? 0) + 1;
    }
    return counts as Record<FileCategory, number>;
  }

  /**
   * Get total size of files.
   */
  getTotalSize(files: ScannedFile[]): number {
    return files.reduce((sum, file) => sum + file.size, 0);
  }

  /**
   * Format size for display.
   */
  formatSize(bytes: number): string {
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
