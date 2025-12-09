/**
 * Type interfaces for Proto-AGI Kernel data structures.
 */

export interface Goal {
    id: string;
    createdAt: string;
    createdBy: "human" | "pak_agent" | "aie_agent";
    title: string;
    description: string;
    origin: "system" | "user" | "world_event" | "derived";
    scope: "app_local" | "multi_app" | "world_model";
    status: "active" | "paused" | "retired" | "superseded";
    priority: number;
    parentGoalId?: string;
    childGoalIds: string[];
    metricsLinked: Record<string, unknown>;
    timeHorizon: "short" | "medium" | "long";
    constraints?: string;
    evaluationNotes?: string;
    lastReviewedAt?: string;
}

export interface ValueRecord {
    id: string;
    name: string;
    description: string;
    source: "human_defined" | "system_derived" | "world_model_inferred";
    weight: number;
    conflictRules?: string;
    lastUpdatedAt?: string;
    history?: string;
}
