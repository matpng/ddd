/**
 * Unified LLM client supporting OpenAI and Anthropic with retry logic,
 * rate limiting, and error handling.
 */

import OpenAI from "openai";
import Anthropic from "@anthropic-ai/sdk";
import { CONFIG } from "../config";
import { Logger } from "./logger";
import { encoding_for_model } from "tiktoken";

const log = new Logger("LLMClient");

export type LLMProvider = "openai" | "anthropic";

export interface LLMMessage {
    role: "system" | "user" | "assistant";
    content: string;
}

export interface LLMCompletionOptions {
    model?: string;
    temperature?: number;
    maxTokens?: number;
    provider?: LLMProvider;
    retries?: number;
}

export interface LLMResponse {
    content: string;
    usage: {
        promptTokens: number;
        completionTokens: number;
        totalTokens: number;
    };
    provider: LLMProvider;
    model: string;
}

export class LLMClient {
    private openai: OpenAI;
    private anthropic: Anthropic;
    private totalCost = 0;

    constructor() {
        this.openai = new OpenAI({
            apiKey: CONFIG.OPENAI_API_KEY
        });

        this.anthropic = new Anthropic({
            apiKey: CONFIG.ANTHROPIC_API_KEY
        });
    }

    async complete(
        messages: LLMMessage[],
        options: LLMCompletionOptions = {}
    ): Promise<LLMResponse> {
        const {
            provider = "openai",
            model = provider === "openai" ? "gpt-4-turbo-preview" : "claude-3-5-sonnet-20241022",
            temperature = 0.7,
            maxTokens = 4096,
            retries = 3
        } = options;

        let lastError: Error | null = null;

        for (let attempt = 0; attempt < retries; attempt++) {
            try {
                if (provider === "openai") {
                    return await this.callOpenAI(messages, model, temperature, maxTokens);
                } else {
                    return await this.callAnthropic(messages, model, temperature, maxTokens);
                }
            } catch (error) {
                lastError = error as Error;
                log.warn(`LLM call failed (attempt ${attempt + 1}/${retries})`, error);

                // Exponential backoff
                if (attempt < retries - 1) {
                    const delay = Math.pow(2, attempt) * 1000;
                    await this.sleep(delay);
                }
            }
        }

        // If all retries failed, try fallback provider
        log.error("All retries failed, trying fallback provider");
        try {
            const fallbackProvider: LLMProvider = provider === "openai" ? "anthropic" : "openai";
            const fallbackModel = fallbackProvider === "openai" ? "gpt-4-turbo-preview" : "claude-3-5-sonnet-20241022";

            if (fallbackProvider === "openai") {
                return await this.callOpenAI(messages, fallbackModel, temperature, maxTokens);
            } else {
                return await this.callAnthropic(messages, fallbackModel, temperature, maxTokens);
            }
        } catch (fallbackError) {
            log.error("Fallback provider also failed", fallbackError);
            throw lastError || fallbackError;
        }
    }

    private async callOpenAI(
        messages: LLMMessage[],
        model: string,
        temperature: number,
        maxTokens: number
    ): Promise<LLMResponse> {
        const response = await this.openai.chat.completions.create({
            model,
            messages: messages.map(m => ({
                role: m.role,
                content: m.content
            })),
            temperature,
            max_tokens: maxTokens
        });

        const content = response.choices[0]?.message?.content || "";
        const usage = response.usage || { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 };

        // Track costs (approximate)
        const cost = this.calculateOpenAICost(model, usage.prompt_tokens, usage.completion_tokens);
        this.totalCost += cost;
        log.info(`OpenAI call: ${usage.total_tokens} tokens, ~$${cost.toFixed(4)}`);

        return {
            content,
            usage: {
                promptTokens: usage.prompt_tokens,
                completionTokens: usage.completion_tokens,
                totalTokens: usage.total_tokens
            },
            provider: "openai",
            model
        };
    }

    private async callAnthropic(
        messages: LLMMessage[],
        model: string,
        temperature: number,
        maxTokens: number
    ): Promise<LLMResponse> {
        // Anthropic requires system message separately
        const systemMessage = messages.find(m => m.role === "system");
        const conversationMessages = messages.filter(m => m.role !== "system");

        const response = await this.anthropic.messages.create({
            model,
            max_tokens: maxTokens,
            temperature,
            system: systemMessage?.content,
            messages: conversationMessages.map(m => ({
                role: m.role === "assistant" ? "assistant" : "user",
                content: m.content
            }))
        });

        const content = response.content[0]?.type === "text" ? response.content[0].text : "";
        const usage = response.usage;

        // Track costs
        const cost = this.calculateAnthropicCost(model, usage.input_tokens, usage.output_tokens);
        this.totalCost += cost;
        log.info(`Anthropic call: ${usage.input_tokens + usage.output_tokens} tokens, ~$${cost.toFixed(4)}`);

        return {
            content,
            usage: {
                promptTokens: usage.input_tokens,
                completionTokens: usage.output_tokens,
                totalTokens: usage.input_tokens + usage.output_tokens
            },
            provider: "anthropic",
            model
        };
    }

    countTokens(text: string, model = "gpt-4"): number {
        try {
            const encoder = encoding_for_model(model as any);
            const tokens = encoder.encode(text);
            encoder.free();
            return tokens.length;
        } catch {
            // Fallback: rough estimation
            return Math.ceil(text.length / 4);
        }
    }

    getTotalCost(): number {
        return this.totalCost;
    }

    resetCost(): void {
        this.totalCost = 0;
    }

    private calculateOpenAICost(model: string, promptTokens: number, completionTokens: number): number {
        // Approximate pricing (as of 2024)
        const pricing: Record<string, { prompt: number; completion: number }> = {
            "gpt-4-turbo-preview": { prompt: 0.01 / 1000, completion: 0.03 / 1000 },
            "gpt-4": { prompt: 0.03 / 1000, completion: 0.06 / 1000 },
            "gpt-3.5-turbo": { prompt: 0.0005 / 1000, completion: 0.0015 / 1000 }
        };

        const rates = pricing[model] || pricing["gpt-4-turbo-preview"];
        return (promptTokens * rates.prompt) + (completionTokens * rates.completion);
    }

    private calculateAnthropicCost(model: string, inputTokens: number, outputTokens: number): number {
        // Approximate pricing (as of 2024)
        const pricing: Record<string, { input: number; output: number }> = {
            "claude-3-5-sonnet-20241022": { input: 0.003 / 1000, output: 0.015 / 1000 },
            "claude-3-opus-20240229": { input: 0.015 / 1000, output: 0.075 / 1000 },
            "claude-3-sonnet-20240229": { input: 0.003 / 1000, output: 0.015 / 1000 }
        };

        const rates = pricing[model] || pricing["claude-3-5-sonnet-20241022"];
        return (inputTokens * rates.input) + (outputTokens * rates.output);
    }

    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Singleton instance
export const llmClient = new LLMClient();
