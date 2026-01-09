import type { LogEntry } from "../types/index.ts";

export type LogLevel = "info" | "warn" | "error" | "debug";

export class Logger {
  private static instance: Logger;
  private verbose = false;

  private constructor() {}

  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  setVerbose(verbose: boolean): void {
    this.verbose = verbose;
  }

  info(message: string, context?: Record<string, unknown>): void {
    this.log("info", message, context);
  }

  warn(message: string, context?: Record<string, unknown>): void {
    this.log("warn", message, context);
  }

  error(message: string, context?: Record<string, unknown>): void {
    this.log("error", message, context);
  }

  debug(message: string, context?: Record<string, unknown>): void {
    if (this.verbose) {
      this.log("debug", message, context);
    }
  }

  private log(level: LogLevel, message: string, context?: Record<string, unknown>): void {
    const timestamp = new Date().toISOString();
    const prefix = this.getPrefix(level);

    let output = `${prefix} ${message}`;

    if (context && this.verbose) {
      output += ` ${JSON.stringify(context)}`;
    }

    if (level === "error") {
      console.error(output);
    } else if (level === "warn") {
      console.warn(output);
    } else {
      console.log(output);
    }
  }

  private getPrefix(level: LogLevel): string {
    const prefixes: Record<LogLevel, string> = {
      info: "[INFO]",
      warn: "[WARN]",
      error: "[ERROR]",
      debug: "[DEBUG]",
    };
    return prefixes[level];
  }

  /**
   * Log progress with a spinner-like format.
   */
  progress(current: number, total: number, message: string): void {
    const percent = Math.round((current / total) * 100);
    const bar = this.createProgressBar(percent);
    process.stdout.write(`\r${bar} ${percent}% ${message}`);
    if (current === total) {
      console.log(); // New line when complete
    }
  }

  private createProgressBar(percent: number, width: number = 20): string {
    const filled = Math.round((percent / 100) * width);
    const empty = width - filled;
    return `[${"=".repeat(filled)}${" ".repeat(empty)}]`;
  }

  /**
   * Clear the current line (for progress updates).
   */
  clearLine(): void {
    process.stdout.write("\r" + " ".repeat(80) + "\r");
  }
}

export const logger = Logger.getInstance();
