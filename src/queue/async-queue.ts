import type { QueueItem, QueueStats, QueueItemStatus } from "../types/index.ts";

export class AsyncQueue {
  private items: QueueItem[] = [];
  private processing = new Set<string>();
  private completed = new Map<string, QueueItem>();
  private failed = new Map<string, QueueItem>();
  private skipped = new Map<string, QueueItem>();
  private closed = false;
  private waiters: Array<(item: QueueItem | null) => void> = [];

  constructor(private readonly maxConcurrent: number = 1) {}

  async enqueue(item: QueueItem): Promise<void> {
    if (this.closed) {
      throw new Error("Queue is closed");
    }
    this.items.push(item);
    this.items.sort((a, b) => a.priority - b.priority);
    this.notifyWaiters();
  }

  async enqueueMany(items: QueueItem[]): Promise<void> {
    if (this.closed) {
      throw new Error("Queue is closed");
    }
    this.items.push(...items);
    this.items.sort((a, b) => a.priority - b.priority);
    this.notifyWaiters();
  }

  private notifyWaiters(): void {
    while (
      this.waiters.length > 0 &&
      this.items.length > 0 &&
      this.processing.size < this.maxConcurrent
    ) {
      const waiter = this.waiters.shift();
      const item = this.items.shift();
      if (waiter && item) {
        this.processing.add(item.id);
        waiter(item);
      }
    }
  }

  async dequeue(): Promise<QueueItem | null> {
    if (this.closed && this.items.length === 0) {
      return null;
    }

    if (this.items.length > 0 && this.processing.size < this.maxConcurrent) {
      const item = this.items.shift()!;
      this.processing.add(item.id);
      return item;
    }

    return new Promise<QueueItem | null>((resolve) => {
      if (this.closed) {
        resolve(null);
        return;
      }
      this.waiters.push(resolve);
    });
  }

  markCompleted(item: QueueItem): void {
    this.processing.delete(item.id);
    item.status = "completed";
    item.completedAt = new Date();
    this.completed.set(item.id, item);
    this.notifyWaiters();
  }

  markFailed(item: QueueItem, error: { code: string; message: string }): void {
    this.processing.delete(item.id);
    item.status = "failed";
    item.completedAt = new Date();
    item.error = { ...error, recoverable: false };
    this.failed.set(item.id, item);
    this.notifyWaiters();
  }

  markSkipped(item: QueueItem, reason: string): void {
    this.processing.delete(item.id);
    item.status = "skipped";
    item.completedAt = new Date();
    item.error = { code: "SKIPPED", message: reason, recoverable: false };
    this.skipped.set(item.id, item);
    this.notifyWaiters();
  }

  requeue(item: QueueItem): void {
    this.processing.delete(item.id);
    item.attempts += 1;
    if (item.attempts < item.maxAttempts) {
      item.status = "pending";
      this.items.push(item);
      this.items.sort((a, b) => a.priority - b.priority);
    } else {
      this.markFailed(item, {
        code: "MAX_ATTEMPTS",
        message: `Exceeded max attempts (${item.maxAttempts})`,
      });
    }
    this.notifyWaiters();
  }

  getStats(): QueueStats {
    return {
      total:
        this.items.length +
        this.processing.size +
        this.completed.size +
        this.failed.size +
        this.skipped.size,
      pending: this.items.length,
      processing: this.processing.size,
      completed: this.completed.size,
      failed: this.failed.size,
      skipped: this.skipped.size,
    };
  }

  getCompletedItems(): QueueItem[] {
    return Array.from(this.completed.values());
  }

  getFailedItems(): QueueItem[] {
    return Array.from(this.failed.values());
  }

  getSkippedItems(): QueueItem[] {
    return Array.from(this.skipped.values());
  }

  isEmpty(): boolean {
    return this.items.length === 0 && this.processing.size === 0;
  }

  isComplete(): boolean {
    return this.closed && this.isEmpty();
  }

  close(): void {
    this.closed = true;
    // Resolve all waiting dequeuers with null
    for (const waiter of this.waiters) {
      waiter(null);
    }
    this.waiters = [];
  }

  async *process(
    handler: (item: QueueItem) => Promise<void>
  ): AsyncGenerator<QueueItem> {
    while (!this.isComplete()) {
      const item = await this.dequeue();
      if (item === null) {
        break;
      }

      item.status = "processing";
      item.startedAt = new Date();

      try {
        await handler(item);
        yield item;
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : String(error);
        this.markFailed(item, { code: "HANDLER_ERROR", message: errorMessage });
        yield item;
      }
    }
  }
}

export function createQueueItem(
  file: QueueItem["file"],
  options: Partial<QueueItem> = {}
): QueueItem {
  return {
    id: crypto.randomUUID(),
    file,
    status: "pending" as QueueItemStatus,
    stage: "scan",
    priority: options.priority ?? 0,
    attempts: 0,
    maxAttempts: options.maxAttempts ?? 3,
    ...options,
  };
}
