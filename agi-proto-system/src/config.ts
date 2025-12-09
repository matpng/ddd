/**
 * Central configuration for the AGI Proto System.
 * In Base44, these would map to environment variables and secret config.
 */

import * as dotenv from "dotenv";
dotenv.config();

export const CONFIG = {
    ENV: process.env.NODE_ENV || "development",

    // Git / Repo integration
    GIT_PROVIDER: process.env.GIT_PROVIDER || "github",
    GIT_REPO_URL: process.env.GIT_REPO_URL || "https://github.com/example/repo.git",
    GIT_ACCESS_TOKEN: process.env.GIT_ACCESS_TOKEN || "",

    // CI/CD
    CI_API_BASE_URL: process.env.CI_API_BASE_URL || "https://ci.example.com/api",
    CI_API_TOKEN: process.env.CI_API_TOKEN || "",

    // Metrics / APM
    METRICS_API_URL: process.env.METRICS_API_URL || "https://metrics.example.com",
    METRICS_API_KEY: process.env.METRICS_API_KEY || "",

    // Web research
    RESEARCH_API_URL: process.env.RESEARCH_API_URL || "https://api.search.example.com",
    RESEARCH_API_KEY: process.env.RESEARCH_API_KEY || "",

    // OpenAI or LLM provider
    OPENAI_API_KEY: process.env.OPENAI_API_KEY || "",

    // Anthropic (backup LLM)
    ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY || "",

    // DB
    DB_URL: process.env.DB_URL || "postgres://user:pass@localhost:5432/agi_proto",

    // AIE cycle
    AIE_CYCLE_INTERVAL_SECONDS: Number(process.env.AIE_CYCLE_INTERVAL_SECONDS || 600),

    // PAK long-horizon cycles
    PAK_LONG_HORIZON_INTERVAL_HOURS: Number(process.env.PAK_LONG_HORIZON_INTERVAL_HOURS || 24)
};
