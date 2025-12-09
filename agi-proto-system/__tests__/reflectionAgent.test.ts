/**
 * Tests for Reflection Agent
 */

import { ReflectionAgent } from '../src/pak/reflectionAgent';
import { Experience } from '../src/core/experienceStore';

// Mock LLM client
jest.mock('../src/core/llmClient', () => ({
    llmClient: {
        complete: jest.fn().mockResolvedValue({
            content: `SUMMARY: Test reflection summary
WHAT_WORKED: 
- Good planning
- Proper testing
WHAT_FAILED:
- Incomplete coverage
UNEXPECTED:
- User feedback was positive
CONNECTIONS:
- Similar to previous issue
CONFIDENCE: 0.75`,
            provider: 'openai',
            usage: { totalTokens: 150 }
        })
    }
}));

describe('ReflectionAgent', () => {
    let agent: ReflectionAgent;

    beforeEach(() => {
        agent = new ReflectionAgent();
        jest.clearAllMocks();
    });

    describe('Experience Reflection', () => {
        it('should reflect on a success experience', async () => {
            const experience: Experience = {
                id: 'exp-1',
                timestamp: new Date().toISOString(),
                type: 'success',
                context: {
                    issue: {
                        id: 'issue-1',
                        description: 'Test issue',
                        severity: 'medium'
                    }
                },
                action: {
                    attempted: 'fix_bug'
                },
                outcome: {
                    status: 'success'
                }
            };

            const reflection = await agent.reflect(experience);

            expect(reflection).toHaveProperty('summary');
            expect(reflection).toHaveProperty('whatWorked');
            expect(reflection).toHaveProperty('whatFailed');
            expect(reflection).toHaveProperty('confidence');
        });

        it('should reflect on a failure experience', async () => {
            const experience: Experience = {
                id: 'exp-2',
                timestamp: new Date().toISOString(),
                type: 'failure',
                context: {
                    issue: {
                        id: 'issue-2',
                        description: 'Failed task',
                        severity: 'high'
                    }
                },
                action: {
                    attempted: 'risky_change'
                },
                outcome: {
                    status: 'failed',
                    reason: 'Tests failed'
                }
            };

            const reflection = await agent.reflect(experience);

            expect(reflection.summary).toBeTruthy();
            expect(Array.isArray(reflection.whatFailed)).toBe(true);
        });
    });

    describe('Lesson Extraction', () => {
        it('should extract lessons from experience', async () => {
            const experience: Experience = {
                id: 'exp-3',
                timestamp: new Date().toISOString(),
                type: 'success',
                context: {},
                action: { attempted: 'test' },
                outcome: { status: 'success' }
            };

            const reflection = {
                summary: 'Test summary',
                whatWorked: ['planning'],
                whatFailed: [],
                unexpectedOutcomes: [],
                connections: [],
                confidence: 0.8
            };

            const lessons = await agent.extractLessons(experience, reflection);

            expect(Array.isArray(lessons)).toBe(true);
            lessons.forEach(lesson => {
                expect(lesson).toHaveProperty('id');
                expect(lesson).toHaveProperty('category');
                expect(lesson).toHaveProperty('insight');
                expect(lesson).toHaveProperty('confidence');
            });
        });

        it('should categorize lessons appropriately', async () => {
            const experience: Experience = {
                id: 'exp-4',
                timestamp: new Date().toISOString(),
                type: 'learning',
                context: {},
                action: { attempted: 'test' },
                outcome: { status: 'learned' }
            };

            const reflection = {
                summary: 'Learned about deployment',
                whatWorked: ['canary deployment'],
                whatFailed: [],
                unexpectedOutcomes: [],
                connections: [],
                confidence: 0.9
            };

            const lessons = await agent.extractLessons(experience, reflection);

            lessons.forEach(lesson => {
                expect(typeof lesson.category).toBe('string');
                expect(lesson.category.length).toBeGreaterThan(0);
            });
        });
    });

    describe('Pattern Identification', () => {
        it('should identify patterns across multiple experiences', async () => {
            const experiences: Experience[] = [
                {
                    id: 'exp-5',
                    timestamp: new Date().toISOString(),
                    type: 'success',
                    context: {},
                    action: { attempted: 'test1' },
                    outcome: { status: 'success' }
                },
                {
                    id: 'exp-6',
                    timestamp: new Date().toISOString(),
                    type: 'failure',
                    context: {},
                    action: { attempted: 'test2' },
                    outcome: { status: 'failed' }
                }
            ];

            const patterns = await agent.identifyPatterns(experiences);

            expect(patterns).toHaveProperty('successPatterns');
            expect(patterns).toHaveProperty('failurePatterns');
            expect(patterns).toHaveProperty('insights');

            expect(Array.isArray(patterns.successPatterns)).toBe(true);
            expect(Array.isArray(patterns.failurePatterns)).toBe(true);
            expect(Array.isArray(patterns.insights)).toBe(true);
        });

        it('should handle empty experience list', async () => {
            const patterns = await agent.identifyPatterns([]);

            expect(patterns.successPatterns).toEqual([]);
            expect(patterns.failurePatterns).toEqual([]);
            expect(patterns.insights).toEqual([]);
        });
    });

    describe('Confidence Scoring', () => {
        it('should assign confidence scores between 0 and 1', async () => {
            const experience: Experience = {
                id: 'exp-7',
                timestamp: new Date().toISOString(),
                type: 'success',
                context: {},
                action: { attempted: 'test' },
                outcome: { status: 'success' }
            };

            const reflection = await agent.reflect(experience);

            expect(reflection.confidence).toBeGreaterThanOrEqual(0);
            expect(reflection.confidence).toBeLessThanOrEqual(1);
        });
    });
});
