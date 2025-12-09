/**
 * Metrics integration – polls runtime and business metrics.
 * Now connects to Discovery System API for real metrics.
 */

import { CONFIG } from "../config";
import { RuntimeMetrics, BusinessMetrics } from "../types";
import { Logger } from "../core/logger";

const logger = new Logger("MetricsService");

interface DiscoveryMetricsResponse {
    runtime_metrics: {
        error_rate: number;
        avg_latency_ms: number;
        requests_per_min: number;
        cache_size: number;
        cache_max: number;
    };
    business_metrics: {
        total_discoveries: number;
        discoveries_last_hour: number;
        active_daemon: boolean;
        daemon_discoveries_today: number;
    };
    timestamp: string;
}

interface DiscoveryHealthResponse {
    status: string;
    timestamp: string;
    components: Record<string, any>;
    version: string;
}

export class MetricsService {
    private baseUrl: string;
    private apiKey: string;
    private retryCount: number = 3;
    private retryDelay: number = 1000; // ms
    private cache: {
        runtime?: { data: RuntimeMetrics; timestamp: number };
        business?: { data: BusinessMetrics; timestamp: number };
    } = {};
    private cacheDuration: number = 30000; // 30 seconds

    constructor() {
        this.baseUrl = CONFIG.METRICS_API_URL || "http://localhost:5000";
        this.apiKey = CONFIG.METRICS_API_KEY || "";
        logger.info(`Metrics service initialized (URL: ${this.baseUrl})`);
    }

    async getRuntimeMetrics(): Promise<RuntimeMetrics> {
        // Check cache
        if (this.cache.runtime && Date.now() - this.cache.runtime.timestamp < this.cacheDuration) {
            logger.debug("Returning cached runtime metrics");
            return this.cache.runtime.data;
        }

        logger.info("Fetching runtime metrics from Discovery System...");

        try {
            const response = await this.fetchWithRetry(`${this.baseUrl}/api/agi/metrics`);
            const data: DiscoveryMetricsResponse = await response.json();

            const metrics: RuntimeMetrics = {
                errorRate: data.runtime_metrics.error_rate,
                avgLatencyMs: data.runtime_metrics.avg_latency_ms,
                requestsPerMin: data.runtime_metrics.requests_per_min
            };

            // Cache the result
            this.cache.runtime = { data: metrics, timestamp: Date.now() };

            logger.info(`Runtime metrics retrieved: errorRate=${metrics.errorRate.toFixed(4)}, latency=${metrics.avgLatencyMs}ms`);
            return metrics;
        } catch (error) {
            logger.error(`Failed to fetch runtime metrics: ${error}`);

            // Return cached data if available, even if expired
            if (this.cache.runtime) {
                logger.warn("Using stale cached runtime metrics");
                return this.cache.runtime.data;
            }

            // Fallback to default values
            logger.warn("Using fallback runtime metrics");
            return {
                errorRate: 0.0,
                avgLatencyMs: 0,
                requestsPerMin: 0
            };
        }
    }

    async getBusinessMetrics(): Promise<BusinessMetrics> {
        // Check cache
        if (this.cache.business && Date.now() - this.cache.business.timestamp < this.cacheDuration) {
            logger.debug("Returning cached business metrics");
            return this.cache.business.data;
        }

        logger.info("Fetching business metrics from Discovery System...");

        try {
            const response = await this.fetchWithRetry(`${this.baseUrl}/api/agi/metrics`);
            const data: DiscoveryMetricsResponse = await response.json();

            const metrics: BusinessMetrics = {
                conversionRate: 0.0, // Not applicable to Discovery System
                activeUsers: data.business_metrics.total_discoveries,
                churnRate: 0.0 // Not applicable
            };

            // Cache the result
            this.cache.business = { data: metrics, timestamp: Date.now() };

            logger.info(`Business metrics retrieved: discoveries=${data.business_metrics.total_discoveries}`);
            return metrics;
        } catch (error) {
            logger.error(`Failed to fetch business metrics: ${error}`);

            // Return cached data if available, even if expired
            if (this.cache.business) {
                logger.warn("Using stale cached business metrics");
                return this.cache.business.data;
            }

            // Fallback to default values
            logger.warn("Using fallback business metrics");
            return {
                conversionRate: 0.0,
                activeUsers: 0,
                churnRate: 0.0
            };
        }
    }

    /**
     * Get detailed health status from Discovery System
     */
    async getHealthStatus(): Promise<DiscoveryHealthResponse> {
        logger.info("Checking Discovery System health...");

        try {
            const response = await this.fetchWithRetry(`${this.baseUrl}/api/agi/health`);
            const health: DiscoveryHealthResponse = await response.json();

            logger.info(`Health check: ${health.status} (version: ${health.version})`);
            return health;
        } catch (error) {
            logger.error(`Health check failed: ${error}`);
            throw error;
        }
    }

    /**
     * Fetch with automatic retries and exponential backoff
     */
    private async fetchWithRetry(url: string, attempt: number = 1): Promise<Response> {
        try {
            const headers: Record<string, string> = {
                'Content-Type': 'application/json'
            };

            if (this.apiKey) {
                headers['Authorization'] = `Bearer ${this.apiKey}`;
            }

            const response = await fetch(url, {
                method: 'GET',
                headers,
                signal: AbortSignal.timeout(5000) // 5 second timeout
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return response;
        } catch (error) {
            if (attempt < this.retryCount) {
                const delay = this.retryDelay * Math.pow(2, attempt - 1); // Exponential backoff
                logger.warn(`Fetch failed (attempt ${attempt}/${this.retryCount}), retrying in ${delay}ms...`);
                await new Promise(resolve => setTimeout(resolve, delay));
                return this.fetchWithRetry(url, attempt + 1);
            }
            throw error;
        }
    }

    /**
     * Clear the metrics cache (useful for testing)
     */
    clearCache(): void {
        this.cache = {};
        logger.debug("Metrics cache cleared");
    }
}
