/**
 * DB integration – simple Postgres wrapper using pg.
 * In Base44, this would map to collections / data connectors instead.
 */

import { Pool } from "pg";
import { CONFIG } from "../config";

const pool = new Pool({
  connectionString: CONFIG.DB_URL
});

export async function query<T = unknown>(sql: string, params: unknown[] = []): Promise<T[]> {
  const client = await pool.connect();
  try {
    const res = await client.query(sql, params);
    return res.rows as T[];
  } finally {
    client.release();
  }
}

export async function initSchema(): Promise<void> {
  // NOTE: This is a minimal schema example. In production, use migrations.
  await query(`
    CREATE TABLE IF NOT EXISTS system_state_snapshots (
      id TEXT PRIMARY KEY,
      timestamp TIMESTAMPTZ NOT NULL,
      app_version TEXT,
      git_commit_hash TEXT,
      runtime_metrics JSONB,
      business_metrics JSONB,
      feature_flags JSONB,
      notes TEXT
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS experiments (
      id TEXT PRIMARY KEY,
      created_at TIMESTAMPTZ NOT NULL,
      status TEXT NOT NULL,
      title TEXT NOT NULL,
      description TEXT,
      tier TEXT,
      target_module_ids TEXT[],
      intended_goal TEXT,
      success_criteria JSONB,
      initiator_type TEXT
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS goals (
      id TEXT PRIMARY KEY,
      created_at TIMESTAMPTZ NOT NULL,
      created_by TEXT,
      title TEXT,
      description TEXT,
      origin TEXT,
      scope TEXT,
      status TEXT,
      priority NUMERIC,
      parent_goal_id TEXT,
      child_goal_ids TEXT[],
      metrics_linked JSONB,
      time_horizon TEXT,
      constraints TEXT,
      evaluation_notes TEXT,
      last_reviewed_at TIMESTAMPTZ
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS values_table (
      id TEXT PRIMARY KEY,
      name TEXT UNIQUE,
      description TEXT,
      source TEXT,
      weight NUMERIC,
      conflict_rules TEXT,
      last_updated_at TIMESTAMPTZ,
      history TEXT,
      examples JSONB
    );
  `);

  // AGI Enhancement Tables

  // Enable pgvector extension for semantic search
  await query(`CREATE EXTENSION IF NOT EXISTS vector;`).catch(() => {
    console.warn("pgvector extension not available - semantic search will be limited");
  });

  // Experiences table for learning and memory
  await query(`
    CREATE TABLE IF NOT EXISTS experiences (
      id UUID PRIMARY KEY,
      timestamp TIMESTAMPTZ NOT NULL,
      type VARCHAR(50) NOT NULL,
      context JSONB NOT NULL,
      action JSONB NOT NULL,
      outcome JSONB NOT NULL,
      reflection JSONB,
      lessons_learned JSONB[],
      embedding VECTOR(1536),
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
  `);

  await query(`
    CREATE INDEX IF NOT EXISTS idx_experiences_type ON experiences(type);
  `);

  await query(`
    CREATE INDEX IF NOT EXISTS idx_experiences_timestamp ON experiences(timestamp DESC);
  `);

  // World observations table
  await query(`
    CREATE TABLE IF NOT EXISTS world_observations (
      id UUID PRIMARY KEY,
      timestamp TIMESTAMPTZ NOT NULL,
      source VARCHAR(100) NOT NULL,
      observation_type VARCHAR(50) NOT NULL,
      data JSONB NOT NULL,
      relevance_score FLOAT,
      embedding VECTOR(1536),
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
  `);

  // Capability assessments table
  await query(`
    CREATE TABLE IF NOT EXISTS capability_assessments (
      id UUID PRIMARY KEY,
      assessed_at TIMESTAMPTZ NOT NULL,
      capability_name VARCHAR(200) NOT NULL,
      confidence FLOAT NOT NULL CHECK (confidence BETWEEN 0 AND 1),
      evidence JSONB NOT NULL,
      limitations JSONB,
      improvement_trend FLOAT,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
  `);

  // Value evaluations table  
  await query(`
    CREATE TABLE IF NOT EXISTS value_evaluations (
      id UUID PRIMARY KEY,
      plan_id VARCHAR(200) NOT NULL,
      evaluated_at TIMESTAMPTZ NOT NULL,
      value_scores JSONB NOT NULL,
      overall_alignment FLOAT NOT NULL,
      conflicts JSONB,
      resolution JSONB,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
  `);

  // Predictions table
  await query(`
    CREATE TABLE IF NOT EXISTS predictions (
      id UUID PRIMARY KEY,
      created_at TIMESTAMPTZ NOT NULL,
      prediction_type VARCHAR(100) NOT NULL,
      description TEXT NOT NULL,
      confidence FLOAT NOT NULL,
      impact_score FLOAT NOT NULL,
      time_horizon VARCHAR(50) NOT NULL,
      evidence JSONB NOT NULL,
      status VARCHAR(50) DEFAULT 'active',
      validated_at TIMESTAMPTZ,
      was_correct BOOLEAN
    );
  `);

  console.log("Database schema initialized with AGI enhancements");
}
