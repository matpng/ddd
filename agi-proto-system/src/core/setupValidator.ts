/**
 * Setup Validator - Validates system configuration and dependencies
 * Ensures all required services and configuration are available before startup.
 */

import { CONFIG } from "../config";
import { Logger } from "./logger";
import { query } from "../integrations/db";
import OpenAI from "openai";
import Anthropic from "@anthropic-ai/sdk";

const log = new Logger("SetupValidator");

export interface ValidationResult {
    valid: boolean;
    errors: string[];
    warnings: string[];
    info: string[];
}

export class SetupValidator {
    private errors: string[] = [];
    private warnings: string[] = [];
    private info: string[] = [];

    /**
     * Run all validation checks
     */
    async validate(): Promise<ValidationResult> {
        log.info("Starting system validation...");

        // Reset state
        this.errors = [];
        this.warnings = [];
        this.info = [];

        // Run all validations
        await this.validateEnvironment();
        await this.validateLLMProviders();
        await this.validateDatabase();
        await this.validateIntegrations();

        const valid = this.errors.length === 0;

        if (valid) {
            log.info("✅ System validation passed");
        } else {
            log.error(`❌ System validation failed with ${this.errors.length} errors`);
        }

        return {
            valid,
            errors: this.errors,
            warnings: this.warnings,
            info: this.info
        };
    }

    /**
     * Validate environment variables
     */
    private async validateEnvironment(): Promise<void> {
        log.info("Validating environment configuration...");

        // Critical environment variables
        const critical = {
            OPENAI_API_KEY: CONFIG.OPENAI_API_KEY,
            DB_URL: CONFIG.DB_URL,
        };

        // Optional but recommended
        const recommended = {
            ANTHROPIC_API_KEY: CONFIG.ANTHROPIC_API_KEY,
            GIT_ACCESS_TOKEN: CONFIG.GIT_ACCESS_TOKEN,
            METRICS_API_KEY: CONFIG.METRICS_API_KEY,
        };

        // Check critical variables
        for (const [key, value] of Object.entries(critical)) {
            if (!value || value.trim() === "") {
                this.errors.push(`Missing critical environment variable: ${key}`);
            } else {
                this.info.push(`✓ ${key} is configured`);
            }
        }

        // Check recommended variables
        for (const [key, value] of Object.entries(recommended)) {
            if (!value || value.trim() === "") {
                this.warnings.push(`Missing recommended environment variable: ${key} (functionality may be limited)`);
            } else {
                this.info.push(`✓ ${key} is configured`);
            }
        }

        // Validate specific formats
        if (CONFIG.DB_URL && !CONFIG.DB_URL.startsWith("postgres://")) {
            this.errors.push("DB_URL must be a valid PostgreSQL connection string (postgres://...)");
        }

        if (CONFIG.GIT_REPO_URL && !CONFIG.GIT_REPO_URL.includes("/")) {
            this.warnings.push("GIT_REPO_URL format may be invalid (expected: owner/repo)");
        }
    }

    /**
     * Validate LLM provider connectivity
     */
    private async validateLLMProviders(): Promise<void> {
        log.info("Validating LLM provider connectivity...");

        // Test OpenAI
        if (CONFIG.OPENAI_API_KEY) {
            try {
                const openai = new OpenAI({ apiKey: CONFIG.OPENAI_API_KEY });

                // Simple API test - just list models to verify key works
                await openai.models.list();

                this.info.push("✓ OpenAI API key is valid and working");
            } catch (error: any) {
                if (error.status === 401) {
                    this.errors.push("OpenAI API key is invalid or expired");
                } else if (error.code === "ENOTFOUND" || error.code === "ECONNREFUSED") {
                    this.warnings.push("Cannot reach OpenAI API (network issue)");
                } else {
                    this.warnings.push(`OpenAI API check failed: ${error.message}`);
                }
            }
        }

        // Test Anthropic (optional)
        if (CONFIG.ANTHROPIC_API_KEY) {
            try {
                const anthropic = new Anthropic({ apiKey: CONFIG.ANTHROPIC_API_KEY });

                // Simple test to verify key
                // Note: We don't make actual calls to avoid costs, just verify initialization
                this.info.push("✓ Anthropic API key is configured (fallback available)");
            } catch (error: any) {
                this.warnings.push(`Anthropic API configuration issue: ${error.message}`);
            }
        }
    }

    /**
     * Validate database connectivity and schema
     */
    private async validateDatabase(): Promise<void> {
        log.info("Validating database connectivity...");

        try {
            // Test basic connectivity
            const result = await query<{ version: string }>("SELECT version()");

            if (result && result.length > 0) {
                const version = result[0].version;
                this.info.push(`✓ PostgreSQL connected: ${version.split(",")[0]}`);
            }

            // Check for pgvector extension
            try {
                const vectorCheck = await query<{ extname: string }>(
                    "SELECT * FROM pg_extension WHERE extname = 'vector'"
                );

                if (vectorCheck.length === 0) {
                    this.errors.push(
                        "pgvector extension not installed - required for semantic search. " +
                        "Run: CREATE EXTENSION vector;"
                    );
                } else {
                    this.info.push("✓ pgvector extension is installed");
                }
            } catch (error: any) {
                this.warnings.push("Could not verify pgvector extension");
            }

            // Check for required tables (basic check)
            try {
                await query("SELECT 1 FROM experiences LIMIT 1");
                this.info.push("✓ Database schema appears initialized");
            } catch (error: any) {
                this.warnings.push(
                    "Database schema may not be initialized. " +
                    "Run schema initialization on first startup."
                );
            }

        } catch (error: any) {
            if (error.code === "ECONNREFUSED") {
                this.errors.push(
                    "Cannot connect to PostgreSQL database - is it running? " +
                    `Connection string: ${this.maskConnectionString(CONFIG.DB_URL)}`
                );
            } else if (error.code === "ENOTFOUND") {
                this.errors.push(
                    `Database host not found: ${error.hostname}`
                );
            } else if (error.code === "3D000") {
                this.errors.push(
                    `Database does not exist. Create it first with: createdb agi_proto`
                );
            } else if (error.code === "28P01") {
                this.errors.push("Database authentication failed - check username/password");
            } else {
                this.errors.push(`Database connection error: ${error.message}`);
            }
        }
    }

    /**
     * Validate external integrations
     */
    private async validateIntegrations(): Promise<void> {
        log.info("Validating external integrations...");

        // Git integration
        if (CONFIG.GIT_ACCESS_TOKEN) {
            this.info.push("✓ Git access token configured");
        } else {
            this.warnings.push(
                "Git access token not configured - Git operations will fail. " +
                "Set GIT_ACCESS_TOKEN environment variable."
            );
        }

        // CI/CD integration
        if (CONFIG.CI_API_TOKEN || CONFIG.GIT_ACCESS_TOKEN) {
            this.info.push("✓ CI/CD integration configured");
        } else {
            this.warnings.push(
                "CI/CD token not configured - pipeline triggers will fail. " +
                "Set CI_API_TOKEN or it will use GIT_ACCESS_TOKEN as fallback."
            );
        }

        // Metrics integration
        if (CONFIG.METRICS_API_KEY) {
            this.info.push("✓ Metrics API configured");
        } else {
            this.warnings.push(
                "Metrics API key not configured - metrics fetching will use mock data. " +
                "Set METRICS_API_KEY for real metrics."
            );
        }

        // Discovery System integration
        if (CONFIG.METRICS_API_URL) {
            this.info.push(`✓ Discovery System URL configured: ${CONFIG.METRICS_API_URL}`);
        } else {
            this.warnings.push(
                "Discovery System URL not configured - using default. " +
                "Set METRICS_API_URL if needed."
            );
        }
    }

    /**
     * Mask connection string for safe logging
     */
    private maskConnectionString(connStr: string): string {
        try {
            const url = new URL(connStr);
            if (url.password) {
                url.password = "****";
            }
            return url.toString();
        } catch {
            return "Invalid connection string";
        }
    }

    /**
     * Print validation results in a user-friendly format
     */
    static printResults(result: ValidationResult): void {
        console.log("\n" + "=".repeat(60));
        console.log("   AGI Proto-System - Setup Validation");
        console.log("=".repeat(60) + "\n");

        if (result.info.length > 0) {
            console.log("ℹ️  Information:");
            result.info.forEach(msg => console.log(`   ${msg}`));
            console.log();
        }

        if (result.warnings.length > 0) {
            console.log("⚠️  Warnings:");
            result.warnings.forEach(msg => console.log(`   ${msg}`));
            console.log();
        }

        if (result.errors.length > 0) {
            console.log("❌ Errors:");
            result.errors.forEach(msg => console.log(`   ${msg}`));
            console.log();
        }

        console.log("=".repeat(60));

        if (result.valid) {
            console.log("✅ VALIDATION PASSED - System ready to start");
        } else {
            console.log("❌ VALIDATION FAILED - Fix errors before starting");
            console.log("\nQuick fixes:");
            console.log("  1. Copy .env.example to .env");
            console.log("  2. Add your OPENAI_API_KEY");
            console.log("  3. Ensure PostgreSQL is running");
            console.log("  4. Run: psql agi_proto -c 'CREATE EXTENSION vector;'");
        }

        console.log("=".repeat(60) + "\n");
    }
}

/**
 * Standalone validation function for easy CLI usage
 */
export async function validateSetup(): Promise<boolean> {
    const validator = new SetupValidator();
    const result = await validator.validate();

    SetupValidator.printResults(result);

    return result.valid;
}
