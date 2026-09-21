export interface ShortUrlRecord {
  code: string;
  originalUrl: string;
  clickCount: number;
  createdAt: Date;
  expiresAt: Date | null;
}

/**
 * In-memory, single-process store. All methods are synchronous with no
 * `await` inside — under Node's single-threaded event loop that makes each
 * call an atomic critical section, which is what the click_count
 * concurrency guarantee (blueprint/GUARANTEES.md) relies on.
 */
export class Store {
  private readonly records = new Map<string, ShortUrlRecord>();

  /** Inserts iff `code` isn't already present. Returns whether it inserted. */
  tryInsert(record: ShortUrlRecord): boolean {
    if (this.records.has(record.code)) {
      return false;
    }
    this.records.set(record.code, record);
    return true;
  }

  get(code: string): ShortUrlRecord | undefined {
    return this.records.get(code);
  }

  incrementClickCount(code: string): void {
    const record = this.records.get(code);
    if (record) {
      record.clickCount += 1;
    }
  }
}
