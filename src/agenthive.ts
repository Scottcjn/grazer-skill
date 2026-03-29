// SPDX-License-Identifier: MIT
/**
 * AgentHive Transport for Grazer
 * Grazer - Multi-Platform Content Discovery for AI Agents
 * @elyanlabs/grazer
 */

import axios, { AxiosInstance } from 'axios';

// ── Types ──────────────────────────────────────────────────────────────────────

export interface AgentHivePost {
  id: string;
  content: string;
  author: string;
  author_id: string;
  likes: number;
  replies: number;
  created_at: string;
  url: string;
  tags?: string[];
}

export interface AgentHiveTrending {
  trending_posts: AgentHivePost[];
  trending_agents: string[];
  trending_tags: string[];
}

export interface AgentHiveAgent {
  id: string;
  name: string;
  bio?: string;
  followers: number;
  posts: number;
  created_at: string;
}

// ── AgentHive API Client ─────────────────────────────────────────────────────────

export class AgentHiveClient {
  private http: AxiosInstance;

  constructor(apiKey?: string) {
    const headers: Record<string, string> = {
      'User-Agent': 'Grazer/1.9.1 (Elyan Labs)',
      'Accept': 'application/json',
    };
    if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;
    this.http = axios.create({
      baseURL: 'https://agenthive.to',
      timeout: 15000,
      headers,
    });
  }

  /** Discover trending posts on AgentHive. Public API, no auth required. */
  async discoverTrending(limit = 20): Promise<AgentHivePost[]> {
    const resp = await this.http.get<{ posts: AgentHivePost[] }>('/api/feed');
    return (resp.data.posts ?? []).slice(0, limit);
  }

  /** Search posts by query. Public API. */
  async searchPosts(query: string, limit = 20): Promise<AgentHivePost[]> {
    const resp = await this.http.get<{ results: AgentHivePost[] }>('/api/search', {
      params: { q: query, limit },
    });
    return (resp.data.results ?? []).slice(0, limit);
  }

  /** Get an agent profile. Public API. */
  async getAgent(name: string): Promise<AgentHiveAgent> {
    const resp = await this.http.get<AgentHiveAgent>(`/api/agents/${encodeURIComponent(name)}`);
    return resp.data;
  }

  /** Get trending agents. Public API. */
  async getTrendingAgents(limit = 20): Promise<string[]> {
    const resp = await this.http.get<{ agents: string[] }>('/api/trending');
    return (resp.data.agents ?? []).slice(0, limit);
  }

  /** Post a message. Requires API key. */
  async postMessage(content: string, apiKey: string): Promise<{ id: string; url: string }> {
    const resp = await this.http.post(
      '/api/posts',
      { content },
      { headers: { Authorization: `Bearer ${apiKey}` } }
    );
    return { id: resp.data.id, url: `https://agenthive.to/post/${resp.data.id}` };
  }

  /** Register a new agent (one-call, no form). Returns agent_id + api_key. */
  async register(name: string, bio?: string): Promise<{ agent_id: string; api_key: string }> {
    const resp = await this.http.post('/api/agents', {
      name,
      ...(bio ? { bio } : {}),
    });
    return { agent_id: resp.data.agent_id, api_key: resp.data.api_key };
  }
}

// ── CLI helpers ────────────────────────────────────────────────────────────────

export function formatAgentHivePost(post: AgentHivePost): string {
  const time = new Date(post.created_at).toLocaleDateString();
  return [
    `  @${post.author} [${time}]`,
    `  ${post.content.slice(0, 120)}${post.content.length > 120 ? '…' : ''}`,
    `  ❤️ ${post.likes} | 💬 ${post.replies} | ${post.url}`,
    '',
  ].join('\n');
}
