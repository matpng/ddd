/**
 * GoalEngineAgent – creates & updates goals (PAK layer).
 */

import { Logger } from "../core/logger";
import { query } from "../integrations/db";
import { Goal } from "../models/pakModels";
import { v4 as uuid } from "uuid";

export class GoalEngineAgent {
    private log = new Logger("GoalEngineAgent");

    async listActiveGoals(): Promise<Goal[]> {
        const rows = await query<Goal>("SELECT * FROM goals WHERE status = 'active'");
        return rows;
    }

    async createGoal(title: string, description: string): Promise<Goal> {
        const now = new Date().toISOString();
        const goal: Goal = {
            id: uuid(),
            createdAt: now,
            createdBy: "pak_agent",
            title,
            description,
            origin: "system",
            scope: "app_local",
            status: "active",
            priority: 1.0,
            childGoalIds: [],
            metricsLinked: {},
            timeHorizon: "medium"
        };

        await query(
            `INSERT INTO goals
      (id, created_at, created_by, title, description, origin, scope, status, priority,
       parent_goal_id, child_goal_ids, metrics_linked, time_horizon, constraints, evaluation_notes, last_reviewed_at)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)`,
            [
                goal.id,
                goal.createdAt,
                goal.createdBy,
                goal.title,
                goal.description,
                goal.origin,
                goal.scope,
                goal.status,
                goal.priority,
                null,
                goal.childGoalIds,
                JSON.stringify(goal.metricsLinked),
                goal.timeHorizon,
                null,
                null,
                now
            ]
        );

        this.log.info("Created new goal", goal);
        return goal;
    }

    async reprioritizeGoalsBasedOnMetrics(): Promise<void> {
        this.log.info("Reprioritizing goals based on metrics (stub).");
        // In a real system, fetch metrics & world events, then adjust priorities.
    }
}
