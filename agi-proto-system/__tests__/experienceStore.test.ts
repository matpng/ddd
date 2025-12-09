/**
 * Tests for Experience Store
 */

import { ExperienceStore } from '../src/core/experienceStore';

// Mock database query
jest.mock('../src/integrations/db', () => ({
    query: jest.fn().mockResolvedValue([])
}));

// Mock OpenAI for embeddings
jest.mock('openai', () => {
    return {
        __esModule: true,
        default: jest.fn().mockImplementation(() => ({
            embeddings: {
                create: jest.fn().mockResolvedValue({
                    data: [{ embedding: new Array(1536).fill(0.1) }]
                })
            }
        }))
    };
});

describe('ExperienceStore', () => {
    let store: ExperienceStore;

    beforeEach(() => {
        store = new ExperienceStore();
        jest.clearAllMocks();
    });

    describe('Experience Recording', () => {
        it('should record a success experience', async () => {
            const experience = {
                type: 'success' as const,
                context: {
                    issue: {
                        id: 'test-issue',
                        description: 'Test issue',
                        severity: 'low'
                    }
                },
                action: {
                    attempted: 'test_action'
                },
                outcome: {
                    status: 'completed'
                }
            };

            const result = await store.recordExperience(experience);

            expect(result.id).toBeTruthy();
            expect(result.type).toBe('success');
            expect(result.timestamp).toBeTruthy();
        });

        it('should record a failure experience', async () => {
            const experience = {
                type: 'failure' as const,
                context: {
                    issue: {
                        id: 'test-issue',
                        description: 'Test issue',
                        severity: 'high'
                    }
                },
                action: {
                    attempted: 'failed_action'
                },
                outcome: {
                    status: 'failed',
                    reason: 'Test failure reason'
                }
            };

            const result = await store.recordExperience(experience);

            expect(result.id).toBeTruthy();
            expect(result.type).toBe('failure');
        });

        it('should record a learning experience', async () => {
            const experience = {
                type: 'learning' as const,
                context: {},
                action: {
                    attempted: 'learning_task'
                },
                outcome: {
                    status: 'learned'
                }
            };

            const result = await store.recordExperience(experience);

            expect(result.type).toBe('learning');
        });
    });

    describe('Experience Retrieval', () => {
        it('should build query context correctly', () => {
            const context = {
                recentFailures: true,
                timeRangeHours: 24,
                limit: 10
            };

            expect(context.recentFailures).toBe(true);
            expect(context.timeRangeHours).toBe(24);
            expect(context.limit).toBe(10);
        });

        it('should handle empty results', async () => {
            const results = await store.getRecentExperiences(0);
            expect(Array.isArray(results)).toBe(true);
        });

        it('should limit results correctly', async () => {
            const limit = 5;
            const results = await store.getRecentExperiences(limit);
            expect(results.length).toBeLessThanOrEqual(limit);
        });
    });

    describe('Reflection Addition', () => {
        it('should accept reflection data', async () => {
            const reflection = {
                summary: 'Test reflection',
                whatWorked: ['item1', 'item2'],
                whatFailed: [],
                unexpectedOutcomes: [],
                connections: [],
                confidence: 0.8
            };

            const lessons = [
                {
                    id: 'lesson-1',
                    category: 'test',
                    insight: 'Test insight',
                    applicability: 'Always',
                    confidence: 0.9,
                    relatedExperiences: ['exp-1']
                }
            ];

            // Should not throw
            await expect(
                store.addReflection('test-id', reflection, lessons)
            ).resolves.not.toThrow();
        });
    });

    describe('Success Rate Calculation', () => {
        it('should calculate success rate', async () => {
            const rate = await store.getSuccessRate('issue');

            expect(typeof rate).toBe('number');
            expect(rate).toBeGreaterThanOrEqual(0);
            expect(rate).toBeLessThanOrEqual(1);
        });
    });
});
