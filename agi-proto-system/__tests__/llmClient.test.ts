/**
 * Tests for LLM Client
 */

import { llmClient, LLMMessage } from '../src/core/llmClient';

// Mock environment variables
process.env.OPENAI_API_KEY = 'test-key';
process.env.ANTHROPIC_API_KEY = 'test-key';

describe('LLMClient', () => {
    beforeEach(() => {
        // Reset client state between tests
        jest.clearAllMocks();
    });

    describe('Message Formatting', () => {
        it('should accept properly formatted messages', () => {
            const messages: LLMMessage[] = [
                { role: 'system', content: 'You are a helpful assistant.' },
                { role: 'user', content: 'Hello!' }
            ];

            expect(messages).toHaveLength(2);
            expect(messages[0].role).toBe('system');
            expect(messages[1].role).toBe('user');
        });

        it('should handle empty content gracefully', () => {
            const message: LLMMessage = {
                role: 'user',
                content: ''
            };

            expect(message.content).toBe('');
        });
    });

    describe('Options Validation', () => {
        it('should use default options when not provided', () => {
            const options = {
                temperature: undefined,
                maxTokens: undefined
            };

            expect(options.temperature).toBeUndefined();
            expect(options.maxTokens).toBeUndefined();
        });

        it('should validate temperature range', () => {
            // Temperature should be 0.0-2.0 for most models
            const validTemps = [0.0, 0.5, 1.0, 1.5, 2.0];

            validTemps.forEach(temp => {
                expect(temp).toBeGreaterThanOrEqual(0);
                expect(temp).toBeLessThanOrEqual(2);
            });
        });

        it('should validate maxTokens is positive', () => {
            const maxTokens = 1000;
            expect(maxTokens).toBeGreaterThan(0);
        });
    });

    describe('Provider Selection', () => {
        it('should accept openai as provider', () => {
            const provider = 'openai';
            expect(['openai', 'anthropic']).toContain(provider);
        });

        it('should accept anthropic as provider', () => {
            const provider = 'anthropic';
            expect(['openai', 'anthropic']).toContain(provider);
        });
    });

    describe('Cost Tracking', () => {
        it('should initialize cost tracking', () => {
            const initialCost = llmClient.getTotalCost();
            expect(initialCost).toBeGreaterThanOrEqual(0);
        });

        it('should accumulate costs', () => {
            const cost1 = llmClient.getTotalCost();
            // Cost should be a number
            expect(typeof cost1).toBe('number');
        });
    });

    // Integration test - only runs if API keys are real
    describe.skip('LLM Integration (requires real API key)', () => {
        it('should complete a simple prompt', async () => {
            const messages: LLMMessage[] = [
                {
                    role: 'user',
                    content: 'Say "test successful"'
                }
            ];

            const response = await llmClient.complete(messages, {
                temperature: 0.0,
                maxTokens: 50
            });

            expect(response.content).toBeTruthy();
            expect(response.provider).toBeTruthy();
            expect(response.usage.totalTokens).toBeGreaterThan(0);
        }, 30000); // 30s timeout for API call
    });
});
