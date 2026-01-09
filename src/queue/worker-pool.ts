import type { QueueItem, ProcessingResult } from "../types/index.ts";
import { AsyncQueue } from "./async-queue.ts";

export type ProcessorFn = (item: QueueItem) => Promise<ProcessingResult>;

export class WorkerPool {
  private queue: AsyncQueue;
  private workers: Promise<void>[] = [];
  private results: ProcessingResult[] = [];
  private running = false;
  private onProgress?: (result: ProcessingResult) => void;

  constructor(
    private readonly workerCount: number,
    private readonly processor: ProcessorFn
  ) {
    this.queue = new AsyncQueue(workerCount);
  }

  setProgressCallback(callback: (result: ProcessingResult) => void): void {
    this.onProgress = callback;
  }

  async submit(item: QueueItem): Promise<void> {
    await this.queue.enqueue(item);
  }

  async submitMany(items: QueueItem[]): Promise<void> {
    await this.queue.enqueueMany(items);
  }

  async start(): Promise<void> {
    if (this.running) {
      return;
    }
    this.running = true;

    // Start worker tasks
    for (let i = 0; i < this.workerCount; i++) {
      this.workers.push(this.workerLoop(i));
    }
  }

  private async workerLoop(workerId: number): Promise<void> {
    while (this.running) {
      const item = await this.queue.dequeue();
      if (item === null) {
        break;
      }

      item.status = "processing";
      item.startedAt = new Date();

      const startTime = Date.now();
      let result: ProcessingResult;

      try {
        result = await this.processor(item);
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : String(error);
        result = {
          queueItem: item,
          success: false,
          duration: Date.now() - startTime,
          warnings: [],
        };
        item.error = {
          code: "PROCESSOR_ERROR",
          message: errorMessage,
          recoverable: false,
        };
      }

      // Update queue state based on result
      if (result.success) {
        this.queue.markCompleted(item);
      } else if (item.error?.recoverable && item.attempts < item.maxAttempts) {
        this.queue.requeue(item);
      } else {
        this.queue.markFailed(item, item.error ?? { code: "UNKNOWN", message: "Unknown error" });
      }

      this.results.push(result);

      if (this.onProgress) {
        this.onProgress(result);
      }
    }
  }

  async waitForCompletion(): Promise<ProcessingResult[]> {
    // Close the queue to signal no more items
    this.queue.close();

    // Wait for all workers to finish
    await Promise.all(this.workers);

    this.running = false;
    return this.results;
  }

  async shutdown(): Promise<void> {
    this.running = false;
    this.queue.close();
    await Promise.all(this.workers);
  }

  getStats() {
    return this.queue.getStats();
  }

  getResults(): ProcessingResult[] {
    return this.results;
  }

  getCompletedItems(): QueueItem[] {
    return this.queue.getCompletedItems();
  }

  getFailedItems(): QueueItem[] {
    return this.queue.getFailedItems();
  }

  getSkippedItems(): QueueItem[] {
    return this.queue.getSkippedItems();
  }
}
