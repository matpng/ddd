/**
 * Simple logger – can be extended to use structured logging.
 */

export class Logger {
    constructor(private scope: string) { }

    info(msg: string, data?: unknown) {
        console.log(`[INFO] [${this.scope}] ${msg}`, data ?? "");
    }

    warn(msg: string, data?: unknown) {
        console.warn(`[WARN] [${this.scope}] ${msg}`, data ?? "");
    }

    error(msg: string, data?: unknown) {
        console.error(`[ERROR] [${this.scope}] ${msg}`, data ?? "");
    }
}
