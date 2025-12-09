/**
 * Tests for Value Alignment Agent
 */

import { ValueAlignmentAgent } from '../src/pak/valueAlignmentAgent';

// Mock dependencies
jest.mock('../src/integrations/db', () => ({
    query: jest.fn().mockImplementation((sql: string, params?: any[]) => {
        // Mock different responses based on query
        if (sql.includes('SELECT * FROM values_table')) {
            return Promise.resolve([
                {
                    id: 'v1',
                    name: 'User Benefit',
                    description: 'Test value',
                    weight: 1.0,
                    source: 'human_defined',
                    examples: JSON.stringify(['example1'])
                }
            ]);
        }
        return Promise.resolve([]);
    })
}));

jest.mock('../src/core/llmClient', () => ({
    llmClient: {
        complete: jest.fn().mockResolvedValue({
            content: `SCORE: 0.8
REASONING: Test reasoning
CONCERNS: none
OPPORTUNITIES: Test opportunity
CONFIDENCE: 0.75`,
            provider: 'openai',
            usage: { totalTokens: 100 }
        })
    }
}));

describe('ValueAlignmentAgent', () => {
    let agent: ValueAlignmentAgent;

    beforeEach(() => {
        agent = new ValueAlignmentAgent();
        jest.clearAllMocks();
    });

    describe('Value Initialization', () => {
        it('should initialize default values', async () => {
            await expect(
                agent.initializeDefaultValues()
            ).resolves.not.toThrow();
        });
    });

    describe('Plan Evaluation', () => {
        it('should evaluate a simple plan', async () => {
            const plan = {
                id: 'test-plan',
                title: 'Test Plan',
                description: 'A test plan for validation',
                targetModuleIds: ['module1']
            };

            const result = await agent.evaluateAlignment(plan);

            expect(result).toHaveProperty('overallAlignment');
            expect(result).toHaveProperty('individualScores');
            expect(result).toHaveProperty('conflicts');
            expect(result).toHaveProperty('recommendation');
        });

        it('should return alignment score between -1 and 1', async () => {
            const plan = {
                id: 'test-plan',
                title: 'Test Plan',
                description: 'Test',
                targetModuleIds: []
            };

            const result = await agent.evaluateAlignment(plan);

            expect(result.overallAlignment).toBeGreaterThanOrEqual(-1);
            expect(result.overallAlignment).toBeLessThanOrEqual(1);
        });

        it('should provide a recommendation', async () => {
            const plan = {
                id: 'test-plan',
                title: 'Test',
                description: 'Test',
                targetModuleIds: []
            };

            const result = await agent.evaluateAlignment(plan);

            expect(['proceed', 'proceed_with_caution', 'human_review', 'reject'])
                .toContain(result.recommendation);
        });
    });

    describe('Value Scoring', () => {
        it('should score against individual values', async () => {
            const plan = {
                id: 'test-plan',
                title: 'Improve user experience',
                description: 'Make UI more intuitive',
                targetModuleIds: ['ui']
            };

            const result = await agent.evaluateAlignment(plan);

            expect(result.individualScores).toBeDefined();
            expect(Array.isArray(result.individualScores)).toBe(true);
        });

        it('should include reasoning for scores', async () => {
            const plan = {
                id: 'test-plan',
                title: 'Test',
                description: 'Test',
                targetModuleIds: []
            };

            const result = await agent.evaluateAlignment(plan);

            expect(result.reasoning).toBeTruthy();
            expect(typeof result.reasoning).toBe('string');
        });
    });

    describe('Conflict Detection', () => {
        it('should detect conflicts when values oppose', async () => {
            const plan = {
                id: 'test-plan',
                title: 'Test',
                description: 'Test',
                targetModuleIds: []
            };

            const result = await agent.evaluateAlignment(plan);

            expect(result.conflicts).toBeDefined();
            expect(Array.isArray(result.conflicts)).toBe(true);
        });

        it('should categorize conflict severity', async () => {
            const plan = {
                id: 'test-plan',
                title: 'Test',
                description: 'Test',
                targetModuleIds: []
            };

            const result = await agent.evaluateAlignment(plan);

            result.conflicts.forEach(conflict => {
                expect(['low', 'medium', 'high']).toContain(conflict.severity);
            });
        });
    });

    describe('Recommendation Logic', () => {
        it('should recommend proceeding for high alignment', async () => {
            // Mock high alignment score
            jest.spyOn(agent as any, 'calculateOverallAlignment')
                .mockReturnValue(0.8);

            const plan = {
                id: 'test-plan',
                title: 'Test',
                description: 'Test',
                targetModuleIds: []
            };

            const result = await agent.evaluateAlignment(plan);

            // High alignment should recommend proceed or proceed_with_caution
            expect(['proceed', 'proceed_with_caution'])
                .toContain(result.recommendation);
        });
    });
});
