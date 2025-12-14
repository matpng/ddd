/**
 * Enhanced Error Handler - Centralized error handling with retry logic,
 * circuit breakers, and recovery strategies.
 */

import { Logger } from "./logger";

const log = new Logger("ErrorHandler");

export type ErrorCategory =
    | "network"
    | "authentication"
    | "rate_limit"
    | "validation"
    | "database"
    | "llm"
    | "unknown";

export interface ErrorContext {
    operation: string;
    category?: ErrorCategory;
    metadata?: Record<string, unknown>;
}

export interface RetryConfig {
    maxAttempts?: number;
    baseDelayMs?: number;
    maxDelayMs?: number;
    backoffMultiplier?: number;
    retryableErrors?: ErrorCategory[];
}

export class RecoverableError extends Error {
    constructor(
        message: string,
        public category: ErrorCategory,
        public context?: ErrorContext
    ) {
        super(message);
        this.name = "RecoverableError";
    }
}

export class NonRecoverableError extends Error {
    constructor(
        message: string,
        public category: ErrorCategory,
        public context?: ErrorContext
    ) {
        super(message);
        this.name = "NonRecoverableError";
    }
}

/**
 * Circuit Breaker pattern implementation
 */
export class CircuitBreaker {
    private failureCount = 0;
    private lastFailureTime?: number;
    private state: "closed" | "open" | "half-open" = "closed";

    constructor(
        private name: string,
        private threshold: number = 5,
        private timeoutMs: number = 60000, // 1 minute
        private resetTimeoutMs: number = 30000 // 30 seconds
    ) { }

    async execute<T>(fn: () => Promise<T>): Promise<T> {
        if (this.state === "open") {
            if (Date.now() - (this.lastFailureTime || 0) > this.resetTimeoutMs) {
                log.info(`Circuit breaker ${this.name} entering half-open state`);
                this.state = "half-open";
            } else {
                throw new Error(`Circuit breaker ${this.name} is OPEN`);
            }
        }

        try {
            const result = await fn();

            // Success - reset if we were in half-open state
            if (this.state === "half-open") {
                this.reset();
                log.info(`Circuit breaker ${this.name} closed after successful request`);
            }

            return result;
        } catch (error) {
            this.recordFailure();
            throw error;
        }
    }

    private recordFailure(): void {
        this.failureCount++;
        this.lastFailureTime = Date.now();

        if (this.failureCount >= this.threshold) {
            this.state = "open";
            log.error(
                `Circuit breaker ${this.name} OPENED after ${this.failureCount} failures`
            );
        }
    }

    private reset(): void {
        this.failureCount = 0;
        this.state = "closed";
        this.lastFailureTime = undefined;
    }

    getState(): string {
        return this.state;
    }
}

/**
 * Main Error Handler class
 */
export class ErrorHandler {
    private static circuitBreakers = new Map<string, CircuitBreaker>();

    /**
     * Categorize an error based on its properties
     */
    static categorizeError(error: any): ErrorCategory {
        if (error instanceof RecoverableError || error instanceof NonRecoverableError) {
            return error.category;
        }

        const message = error.message?.toLowerCase() || "";
        const code = error.code?.toUpperCase();

        // Network errors
        if (
            code === "ECONNREFUSED" ||
            code === "ENOTFOUND" ||
            code === "ETIMEDOUT" ||
            code === "ECONNRESET" ||
            message.includes("network") ||
            message.includes("timeout")
        ) {
            return "network";
        }

        // Authentication errors
        if (
            error.status === 401 ||
            error.status === 403 ||
            code === "28P01" || // Postgres auth failed
            message.includes("unauthorized") ||
            message.includes("forbidden") ||
            message.includes("invalid api key")
        ) {
            return "authentication";
        }

        // Rate limiting
        if (
            error.status === 429 ||
            message.includes("rate limit") ||
            message.includes("too many requests")
        ) {
            return "rate_limit";
        }

        // Validation errors
        if (
            error.status === 400 ||
            error.status === 422 ||
            message.includes("validation") ||
            message.includes("invalid")
        ) {
            return "validation";
        }

        // Database errors
        if (
            code === "3D000" || // Database doesn't exist
            message.includes("database") ||
            message.includes("postgres") ||
            message.includes("sql")
        ) {
            return "database";
        }

        // LLM errors
        if (
            message.includes("openai") ||
            message.includes("anthropic") ||
            message.includes("model") ||
            message.includes("completion")
        ) {
            return "llm";
        }

        return "unknown";
    }

    /**
     * Determine if an error is retryable
     */
    static isRetryable(error: any, category?: ErrorCategory): boolean {
        if (error instanceof NonRecoverableError) {
            return false;
        }

        if (error instanceof RecoverableError) {
            return true;
        }

        const errorCategory = category || this.categorizeError(error);

        // Retryable categories
        const retryableCategories: ErrorCategory[] = [
            "network",
            "rate_limit",
            "llm" // LLM errors might be transient
        ];

        return retryableCategories.includes(errorCategory);
    }

    /**
     * Execute operation with retry logic
     */
    static async withRetry<T>(
        fn: () => Promise<T>,
        context: ErrorContext,
        config: RetryConfig = {}
    ): Promise<T> {
        const {
            maxAttempts = 3,
            baseDelayMs = 1000,
            maxDelayMs = 30000,
            backoffMultiplier = 2
        } = config;

        let lastError: any;

        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                log.debug(`Executing ${context.operation} (attempt ${attempt}/${maxAttempts})`);
                return await fn();
            } catch (error: any) {
                lastError = error;
                const category = this.categorizeError(error);

                log.warn(
                    `${context.operation} failed (attempt ${attempt}/${maxAttempts}): ${error.message}`,
                    { category, error: error.message }
                );

                // Don't retry if not retryable or on last attempt
                if (!this.isRetryable(error, category) || attempt === maxAttempts) {
                    break;
                }

                // Calculate delay with exponential backoff
                const delay = Math.min(
                    baseDelayMs * Math.pow(backoffMultiplier, attempt - 1),
                    maxDelayMs
                );

                log.info(`Retrying ${context.operation} after ${delay}ms...`);
                await this.sleep(delay);
            }
        }

        // All retries failed
        log.error(`${context.operation} failed after ${maxAttempts} attempts`);
        throw lastError;
    }

    /**
     * Execute operation with circuit breaker
     */
    static async withCircuitBreaker<T>(
        name: string,
        fn: () => Promise<T>,
        context: ErrorContext
    ): Promise<T> {
        let breaker = this.circuitBreakers.get(name);

        if (!breaker) {
            breaker = new CircuitBreaker(name);
            this.circuitBreakers.set(name, breaker);
        }

        try {
            return await breaker.execute(fn);
        } catch (error: any) {
            const category = this.categorizeError(error);
            log.error(
                `Circuit breaker ${name} operation failed: ${error.message}`,
                { category, state: breaker.getState() }
            );
            throw error;
        }
    }

    /**
     * Execute operation with both retry and circuit breaker
     */
    static async withRetryAndCircuitBreaker<T>(
        name: string,
        fn: () => Promise<T>,
        context: ErrorContext,
        retryConfig?: RetryConfig
    ): Promise<T> {
        return this.withCircuitBreaker(
            name,
            () => this.withRetry(fn, context, retryConfig),
            context
        );
    }

    /**
     * Handle error with recovery strategy
     */
    static async handleWithRecovery<T>(
        fn: () => Promise<T>,
        context: ErrorContext,
        fallback?: () => Promise<T>
    ): Promise<T> {
        try {
            return await fn();
        } catch (error: any) {
            const category = this.categorizeError(error);

            log.error(
                `Error in ${context.operation}`,
                { category, error: error.message, metadata: context.metadata }
            );

            // Try fallback if available
            if (fallback) {
                log.info(`Attempting fallback for ${context.operation}`);
                try {
                    return await fallback();
                } catch (fallbackError: any) {
                    log.error(`Fallback also failed: ${fallbackError.message}`);
                    throw error; // Throw original error
                }
            }

            throw error;
        }
    }

    /**
     * Get circuit breaker state for monitoring
     */
    static getCircuitBreakerStates(): Record<string, string> {
        const states: Record<string, string> = {};

        for (const [name, breaker] of this.circuitBreakers.entries()) {
            states[name] = breaker.getState();
        }

        return states;
    }

    /**
     * Sleep helper
     */
    private static sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
