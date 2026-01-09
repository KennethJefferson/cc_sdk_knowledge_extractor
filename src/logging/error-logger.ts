import { writeFileSync, appendFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import type { LogEntry, ProcessingError } from "../types/index.ts";

export class ErrorLogger {
  private logPath: string;
  private initialized = false;

  constructor(outputDir: string) {
    const timestamp = this.formatTimestamp(new Date());
    this.logPath = join(outputDir, `error_${timestamp}.log`);
  }

  private formatTimestamp(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    const seconds = String(date.getSeconds()).padStart(2, "0");
    return `${year}${month}${day}_${hours}${minutes}${seconds}`;
  }

  private ensureDir(): void {
    if (!this.initialized) {
      const dir = dirname(this.logPath);
      if (!existsSync(dir)) {
        mkdirSync(dir, { recursive: true });
      }
      this.initialized = true;
    }
  }

  /**
   * Log an error to the file.
   */
  logError(
    code: string,
    message: string,
    file?: string,
    context?: Record<string, unknown>
  ): void {
    this.ensureDir();

    const timestamp = new Date().toISOString();
    const entry = this.formatEntry({
      timestamp: new Date(),
      level: "error",
      code,
      message,
      file,
      context,
    });

    appendFileSync(this.logPath, entry, "utf-8");
  }

  /**
   * Log a warning to the file.
   */
  logWarning(
    message: string,
    file?: string,
    context?: Record<string, unknown>
  ): void {
    this.ensureDir();

    const entry = this.formatEntry({
      timestamp: new Date(),
      level: "warn",
      message,
      file,
      context,
    });

    appendFileSync(this.logPath, entry, "utf-8");
  }

  /**
   * Log a processing error from a QueueItem.
   */
  logProcessingError(error: ProcessingError, filePath?: string): void {
    this.logError(error.code, error.message, filePath, error.context);
  }

  private formatEntry(entry: LogEntry): string {
    const lines: string[] = [
      `[${entry.timestamp.toISOString()}] [${entry.code ?? entry.level.toUpperCase()}] ${entry.level.toUpperCase()}`,
    ];

    if (entry.file) {
      lines.push(`  File: ${entry.file}`);
    }

    lines.push(`  Message: ${entry.message}`);

    if (entry.context) {
      for (const [key, value] of Object.entries(entry.context)) {
        lines.push(`  ${key}: ${JSON.stringify(value)}`);
      }
    }

    lines.push("---");
    return lines.join("\n") + "\n";
  }

  /**
   * Write a summary at the end of processing.
   */
  writeSummary(stats: {
    total: number;
    completed: number;
    failed: number;
    skipped: number;
    duration: number;
  }): void {
    this.ensureDir();

    const summary = [
      "",
      "=== Processing Summary ===",
      `Timestamp: ${new Date().toISOString()}`,
      `Total files: ${stats.total}`,
      `Completed: ${stats.completed}`,
      `Failed: ${stats.failed}`,
      `Skipped: ${stats.skipped}`,
      `Duration: ${(stats.duration / 1000).toFixed(2)}s`,
      "========================",
      "",
    ].join("\n");

    appendFileSync(this.logPath, summary, "utf-8");
  }

  /**
   * Get the path to the log file.
   */
  getLogPath(): string {
    return this.logPath;
  }

  /**
   * Check if any errors were logged.
   */
  hasErrors(): boolean {
    return this.initialized && existsSync(this.logPath);
  }
}
