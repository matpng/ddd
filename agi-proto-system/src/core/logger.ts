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

    debug(msg: string, data?: unknown) {
        if (process.env.LOG_LEVEL === "debug") {
            console.log(`[DEBUG] [${this.scope}] ${msg}`, data ?? "");
        }
    }
}
