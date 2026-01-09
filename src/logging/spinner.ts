/**
 * Simple terminal spinner for progress indication.
 */
export class Spinner {
  private static readonly FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
  private frameIndex = 0;
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private message = "";
  private isRunning = false;

  /**
   * Start the spinner with an optional message.
   */
  start(message = ""): void {
    if (this.isRunning) return;

    this.message = message;
    this.isRunning = true;
    this.frameIndex = 0;

    this.intervalId = setInterval(() => {
      this.render();
      this.frameIndex = (this.frameIndex + 1) % Spinner.FRAMES.length;
    }, 80);
  }

  /**
   * Update the spinner message.
   */
  update(message: string): void {
    this.message = message;
    if (this.isRunning) {
      this.render();
    }
  }

  /**
   * Stop the spinner with a success message.
   */
  success(message?: string): void {
    this.stop("✓", message ?? this.message);
  }

  /**
   * Stop the spinner with a failure message.
   */
  fail(message?: string): void {
    this.stop("✗", message ?? this.message);
  }

  /**
   * Stop the spinner with an info message.
   */
  info(message?: string): void {
    this.stop("ℹ", message ?? this.message);
  }

  /**
   * Stop the spinner with a warning message.
   */
  warn(message?: string): void {
    this.stop("⚠", message ?? this.message);
  }

  private stop(symbol: string, message: string): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.isRunning = false;
    this.clearLine();
    console.log(`${symbol} ${message}`);
  }

  private render(): void {
    const frame = Spinner.FRAMES[this.frameIndex];
    this.clearLine();
    process.stdout.write(`${frame} ${this.message}`);
  }

  private clearLine(): void {
    process.stdout.write("\r\x1b[K");
  }
}

/**
 * Multi-line progress display for parallel operations.
 */
export class ProgressDisplay {
  private total: number;
  private completed = 0;
  private failed = 0;
  private currentFile = "";
  private startTime: number;
  private intervalId: ReturnType<typeof setInterval> | null = null;

  constructor(total: number) {
    this.total = total;
    this.startTime = Date.now();
  }

  /**
   * Start the progress display.
   */
  start(): void {
    this.intervalId = setInterval(() => this.render(), 100);
  }

  /**
   * Update progress with a completed file.
   */
  update(fileName: string, success: boolean): void {
    this.currentFile = fileName;
    if (success) {
      this.completed++;
    } else {
      this.failed++;
    }
    this.render();
  }

  /**
   * Stop the progress display.
   */
  stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.clearLine();
  }

  private render(): void {
    const elapsed = ((Date.now() - this.startTime) / 1000).toFixed(1);
    const processed = this.completed + this.failed;
    const percent = this.total > 0 ? Math.round((processed / this.total) * 100) : 0;
    const bar = this.createBar(percent);

    const status = this.failed > 0
      ? `${this.completed} OK, ${this.failed} FAIL`
      : `${this.completed} completed`;

    this.clearLine();
    process.stdout.write(
      `${bar} ${percent}% [${processed}/${this.total}] ${status} (${elapsed}s) ${this.truncate(this.currentFile, 30)}`
    );
  }

  private createBar(percent: number, width = 20): string {
    const filled = Math.round((percent / 100) * width);
    const empty = width - filled;
    return `[${"█".repeat(filled)}${"░".repeat(empty)}]`;
  }

  private truncate(str: string, maxLen: number): string {
    if (str.length <= maxLen) return str;
    return "..." + str.slice(-(maxLen - 3));
  }

  private clearLine(): void {
    process.stdout.write("\r\x1b[K");
  }
}
