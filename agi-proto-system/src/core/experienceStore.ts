/**
 * Experience Store - Records, stores, and retrieves system experiences
 * for learning and improvement. Includes semantic search via embeddings.
 */

import { query } from "../integrations/db";
import { Logger } from "./logger";
import { v4 as uuid } from "uuid";
import OpenAI from "openai";
import { CONFIG } from "../config";

const log = new Logger("ExperienceStore");

export interface Experience {
    id: string;
    timestamp: string;
    type: "success" | "failure" | "partial_success" | "learning";
    context: ExperienceContext;
    action: ActionTaken;
    outcome: Outcome;
    reflection?: Reflection;
    lessonsLearned?: Lesson[];
    embedding?: number[];
}

export interface ExperienceContext {
    issue?: {
        id: string;
        description: string;
        severity: string;
    };
    plan?: {
        id: string;
        title: string;
        description: string;
    };
    diff?: {
        summary: string;
        filesTouched: string[];
        riskLevel: string;
    };
    worldState?: Record<string, unknown>;
}

export interface ActionTaken {
    attempted: string;
    deployed?: boolean;
    prUrl?: string;
    branchName?: string;
    timestamp?: string;
}

export interface Outcome {
    status: string;
    metricsImpact?: MetricsImpact;
    rollbackRequired?: boolean;
    userFeedback?: string;
    ciStatus?: string;
    reason?: string;
}

export interface MetricsImpact {
    errorRateBefore: number;
    errorRateAfter: number;
    latencyBefore: number;
    latencyAfter: number;
    customMetrics?: Record<string, { before: number; after: number }>;
}

export interface Reflection {
    summary: string;
    whatWorked: string[];
    whatFailed: string[];
    unexpectedOutcomes: string[];
    connections: string[];
    confidence: number;
}

export interface Lesson {
    id: string;
    category: string;
    insight: string;
    applicability: string;
    confidence: number;
    relatedExperiences: string[];
}

export interface QueryContext {
    recentFailures?: boolean;
    similarIssues?: boolean;
    successfulPatterns?: boolean;
    timeRangeHours?: number;
    limit?: number;
    minConfidence?: number;
    searchQuery?: string;
}

export class ExperienceStore {
    private openai: OpenAI;

    constructor() {
        this.openai = new OpenAI({ apiKey: CONFIG.OPENAI_API_KEY });
    }

    async recordExperience(exp: Omit<Experience, "id" | "timestamp" | "reflection" | "lessonsLearned" | "embedding">): Promise<Experience> {
        const id = uuid();
        const timestamp = new Date().toISOString();

        log.info("Recording experience", { id, type: exp.type });

        // Create initial experience record
        const experience: Experience = {
            id,
            timestamp,
            ...exp
        };

        // Generate embedding for semantic search
        const embeddingVector = await this.generateEmbedding(experience);
        experience.embedding = embeddingVector;

        // Store in database
        await this.storeExperience(experience);

        log.info("Experience recorded", { id });

        return experience;
    }

    /**
     * Add reflection and lessons to an existing experience
     */
    async addReflection(experienceId: string, reflection: Reflection, lessons: Lesson[]): Promise<void> {
        log.info("Adding reflection to experience", { experienceId });

        await query(
            `UPDATE experiences 
             SET reflection = $1, lessons_learned = $2
             WHERE id = $3`,
            [JSON.stringify(reflection), JSON.stringify(lessons), experienceId]
        );
    }

    /**
     * Query relevant experiences based on context
     */
    async queryRelevantExperiences(ctx: QueryContext): Promise<Experience[]> {
        const {
            recentFailures = false,
            similarIssues = false,
            successfulPatterns = false,
            timeRangeHours = 168, // 1 week default
            limit = 10,
            minConfidence = 0.0,
            searchQuery
        } = ctx;

        log.info("Querying experiences", ctx);

        // If semantic search query provided, use vector search
        if (searchQuery) {
            return this.semanticSearch(searchQuery, limit);
        }

        // Otherwise use metadata filters
        const conditions: string[] = [];
        const params: any[] = [];
        let paramIndex = 1;

        // Time range
        conditions.push(`timestamp > NOW() - INTERVAL '${timeRangeHours} hours'`);

        // Type filters
        if (recentFailures) {
            conditions.push(`type IN ('failure', 'partial_success')`);
        }

        if (successfulPatterns) {
            conditions.push(`type = 'success'`);
        }

        // Confidence filter (from reflection)
        if (minConfidence > 0) {
            conditions.push(`(reflection->>'confidence')::float >= $${paramIndex}`);
            params.push(minConfidence);
            paramIndex++;
        }

        const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

        const sql = `
            SELECT * FROM experiences 
            ${whereClause}
            ORDER BY timestamp DESC 
            LIMIT $${paramIndex}
        `;
        params.push(limit);

        const rows = await query<any>(sql, params);
        return rows.map(r => this.parseExperienceRow(r));
    }

    /**
     * Semantic search using embeddings
     */
    private async semanticSearch(searchQuery: string, limit: number): Promise<Experience[]> {
        log.info("Performing semantic search", { query: searchQuery });

        // Generate embedding for search query
        const queryEmbedding = await this.generateQueryEmbedding(searchQuery);

        // Vector similarity search (using pgvector)
        const sql = `
            SELECT *, 
                   embedding <=> $1::vector AS distance
            FROM experiences
            WHERE embedding IS NOT NULL
            ORDER BY distance
            LIMIT $2
        `;

        const rows = await query<any>(sql, [JSON.stringify(queryEmbedding), limit]);
        return rows.map(r => this.parseExperienceRow(r));
    }

    /**
     * Get experiences by type
     */
    async getExperimentsByStatus(status: string | string[], limit = 100): Promise<Experience[]> {
        const statuses = Array.isArray(status) ? status : [status];

        const placeholders = statuses.map((_, i) => `$${i + 1}`).join(", ");
        const sql = `
            SELECT * FROM experiences 
            WHERE type = ANY($1::text[])
            ORDER BY timestamp DESC 
            LIMIT $2
        `;

        const rows = await query<any>(sql, [statuses, limit]);
        return rows.map(r => this.parseExperienceRow(r));
    }

    /**
     * Get recent experiences
     */
    async getRecentExperiences(limit = 20): Promise<Experience[]> {
        const sql = `
            SELECT * FROM experiences 
            ORDER BY timestamp DESC 
            LIMIT $1
        `;

        const rows = await query<any>(sql, [limit]);
        return rows.map(r => this.parseExperienceRow(r));
    }

    /**
     * Get success rate for similar contexts
     */
    async getSuccessRate(contextType: string): Promise<number> {
        const sql = `
            SELECT 
                COUNT(*) FILTER (WHERE type = 'success') AS successes,
                COUNT(*) AS total
            FROM experiences
            WHERE context->>'issue' IS NOT NULL
            AND timestamp > NOW() - INTERVAL '30 days'
        `;

        const result = await query<any>(sql);
        if (result.length === 0 || result[0].total === 0) {
            return 0.5; // Default 50% for no data
        }

        return result[0].successes / result[0].total;
    }

    // Private helper methods

    private async generateEmbedding(experience: Experience): Promise<number[]> {
        // Create searchable text from experience
        const text = this.serializeExperienceForEmbedding(experience);

        try {
            const response = await this.openai.embeddings.create({
                model: "text-embedding-3-small",
                input: text
            });

            return response.data[0].embedding;
        } catch (error) {
            log.warn("Failed to generate embedding", error);
            return [];
        }
    }

    private async generateQueryEmbedding(query: string): Promise<number[]> {
        try {
            const response = await this.openai.embeddings.create({
                model: "text-embedding-3-small",
                input: query
            });

            return response.data[0].embedding;
        } catch (error) {
            log.error("Failed to generate query embedding", error);
            throw error;
        }
    }

    private serializeExperienceForEmbedding(exp: Experience): string {
        const parts: string[] = [];

        parts.push(`Type: ${exp.type}`);

        if (exp.context.issue) {
            parts.push(`Issue: ${exp.context.issue.description}`);
        }

        if (exp.context.plan) {
            parts.push(`Plan: ${exp.context.plan.title} - ${exp.context.plan.description}`);
        }

        if (exp.context.diff) {
            parts.push(`Changes: ${exp.context.diff.summary}`);
            parts.push(`Files: ${exp.context.diff.filesTouched.join(", ")}`);
        }

        parts.push(`Outcome: ${exp.outcome.status}`);

        if (exp.reflection) {
            parts.push(`Reflection: ${exp.reflection.summary}`);
        }

        return parts.join("\n");
    }

    private async storeExperience(exp: Experience): Promise<void> {
        await query(
            `INSERT INTO experiences 
             (id, timestamp, type, context, action, outcome, reflection, lessons_learned, embedding)
             VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
            [
                exp.id,
                exp.timestamp,
                exp.type,
                JSON.stringify(exp.context),
                JSON.stringify(exp.action),
                JSON.stringify(exp.outcome),
                exp.reflection ? JSON.stringify(exp.reflection) : null,
                exp.lessonsLearned ? JSON.stringify(exp.lessonsLearned) : null,
                exp.embedding ? JSON.stringify(exp.embedding) : null
            ]
        );
    }

    private parseExperienceRow(row: any): Experience {
        return {
            id: row.id,
            timestamp: row.timestamp,
            type: row.type,
            context: row.context,
            action: row.action,
            outcome: row.outcome,
            reflection: row.reflection || undefined,
            lessonsLearned: row.lessons_learned || undefined,
            embedding: row.embedding || undefined
        };
    }
}
