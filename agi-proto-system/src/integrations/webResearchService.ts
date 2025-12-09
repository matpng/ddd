/**
 * Web research integration – queries external sources for world knowledge.
 * Implements web search and content extraction.
 */

import { CONFIG } from "../config";
import { Logger } from "../core/logger";

const logger = new Logger("WebResearchService");

interface SearchResult {
    title: string;
    url: string;
    snippet: string;
    timestamp: string;
}

interface ResearchResult {
    query: string;
    results: SearchResult[];
    summary: string;
    sources: string[];
}

export class WebResearchService {
    private apiKey: string;
    private searchEngine: string;

    constructor() {
        this.apiKey = CONFIG.WEB_RESEARCH_API_KEY || "";
        this.searchEngine = CONFIG.WEB_RESEARCH_ENGINE || "duckduckgo";

        if (!this.apiKey && this.searchEngine !== "duckduckgo") {
            logger.warn("No web research API key - using DuckDuckGo HTML scraping (limited)");
        }

        logger.info(`WebResearchService initialized (engine: ${this.searchEngine})`);
    }

    /**
     * Research a topic by searching the web
     */
    async researchTopic(query: string, maxResults: number = 5): Promise<ResearchResult> {
        logger.info(`Researching topic: "${query}"`);

        try {
            const results = await this.search(query, maxResults);

            // Generate summary from results
            const summary = this.generateSummary(results);
            const sources = results.map(r => r.url);

            logger.info(`Found ${results.length} results for "${query}"`);

            return {
                query,
                results,
                summary,
                sources
            };
        } catch (error: any) {
            logger.error(`Research failed: ${error.message}`);
            return {
                query,
                results: [],
                summary: `Unable to research "${query}": ${error.message}`,
                sources: []
            };
        }
    }

    /**
     * Search the web using configured search engine
     */
    private async search(query: string, maxResults: number): Promise<SearchResult[]> {
        if (this.searchEngine === "duckduckgo") {
            return this.searchDuckDuckGo(query, maxResults);
        }

        // Fallback to simple fetch if no search engine configured
        logger.warn("No search engine configured, returning empty results");
        return [];
    }

    /**
     * Search DuckDuckGo (HTML scraping - limited but free)
     */
    private async searchDuckDuckGo(query: string, maxResults: number): Promise<SearchResult[]> {
        try {
            const encodedQuery = encodeURIComponent(query);
            const url = `https://html.duckduckgo.com/html/?q=${encodedQuery}`;

            const response = await fetch(url, {
                headers: {
                    'User-Agent': 'Mozilla/5.0 (compatible; AGI-Proto-System/1.0)'
                }
            });

            if (!response.ok) {
                throw new Error(`DuckDuckGo returned ${response.status}`);
            }

            const html = await response.text();

            // Simple HTML parsing (in production, use a proper HTML parser)
            const results = this.parseDuckDuckGoHTML(html, maxResults);

            return results;
        } catch (error: any) {
            logger.error(`DuckDuckGo search failed: ${error.message}`);
            return [];
        }
    }

    /**
     * Parse DuckDuckGo HTML results (simplified)
     */
    private parseDuckDuckGoHTML(html: string, maxResults: number): SearchResult[] {
        const results: SearchResult[] = [];

        // Very basic parsing - extract result snippets
        // In production, use a proper HTML parser like cheerio or jsdom
        const resultPattern = /<a class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)<\/a>[\s\S]*?<a class="result__snippet"[^>]*>([^<]+)<\/a>/g;

        let match;
        let count = 0;

        while ((match = resultPattern.exec(html)) !== null && count < maxResults) {
            const [, url, title, snippet] = match;

            // Decode HTML entities (basic)
            const decodedTitle = this.decodeHTML(title);
            const decodedSnippet = this.decodeHTML(snippet);

            results.push({
                title: decodedTitle.trim(),
                url: url.trim(),
                snippet: decodedSnippet.trim(),
                timestamp: new Date().toISOString()
            });

            count++;
        }

        return results;
    }

    /**
     * Decode basic HTML entities
     */
    private decodeHTML(html: string): string {
        return html
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'")
            .replace(/<[^>]+>/g, ''); // Remove any HTML tags
    }

    /**
     * Generate summary from search results
     */
    private generateSummary(results: SearchResult[]): string {
        if (results.length === 0) {
            return "No results found.";
        }

        // Combine snippets into a summary
        const snippets = results.map(r => r.snippet).join(' ');

        // Truncate if too long
        const maxLength = 500;
        if (snippets.length > maxLength) {
            return snippets.substring(0, maxLength) + '...';
        }

        return snippets;
    }

    /**
     * Fetch and extract content from a URL
     */
    async fetchContent(url: string): Promise<string> {
        logger.info(`Fetching content from ${url}`);

        try {
            const response = await fetch(url, {
                headers: {
                    'User-Agent': 'Mozilla/5.0 (compatible; AGI-Proto-System/1.0)'
                },
                signal: AbortSignal.timeout(10000) // 10 second timeout
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const html = await response.text();

            // Extract main content (very basic - in production use readability or similar)
            const textContent = this.extractTextContent(html);

            logger.info(`Fetched ${textContent.length} characters from ${url}`);
            return textContent;
        } catch (error: any) {
            logger.error(`Failed to fetch ${url}: ${error.message}`);
            throw error;
        }
    }

    /**
     * Extract text content from HTML (simplified)
     */
    private extractTextContent(html: string): string {
        // Remove scripts and styles
        let text = html
            .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
            .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '');

        // Remove HTML tags
        text = text.replace(/<[^>]+>/g, ' ');

        // Decode HTML entities
        text = this.decodeHTML(text);

        // Clean up whitespace
        text = text
            .replace(/\s+/g, ' ')
            .trim();

        // Truncate to reasonable length
        const maxLength = 10000;
        if (text.length > maxLength) {
            text = text.substring(0, maxLength) + '...';
        }

        return text;
    }
}
