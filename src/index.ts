/**
 * Grazer - Multi-Platform Content Discovery for AI Agents
 * @elyanlabs/grazer
 */

import axios, { AxiosInstance } from 'axios';
import { generateSvg, svgToMedia, generateTemplateSvg, generateLlmSvg } from './imagegen';
import type { ImageGenResult, FourclawMedia, ImageGenConfig } from './imagegen';

export { generateSvg, svgToMedia, generateTemplateSvg, generateLlmSvg };
export type { ImageGenResult, FourclawMedia, ImageGenConfig };

export interface GrazerConfig {
  bottube?: string;
  moltbook?: string;
  clawcities?: string;
  clawsta?: string;
  fourclaw?: string;
  llmUrl?: string;
  llmModel?: string;
  llmApiKey?: string;
}

export interface BottubeVideo {
  id: string;
  title: string;
  agent: string;
  category: string;
  views: number;
  duration: number;
  created_at: string;
  stream_url: string;
}

export interface MoltbookPost {
  id: number;
  title: string;
  content: string;
  submolt: string;
  author: string;
  upvotes: number;
  created_at: string;
  url: string;
}

export interface ClawCitiesSite {
  name: string;
  display_name: string;
  description: string;
  url: string;
  guestbook_count: number;
}

export interface ClawstaPost {
  id: number;
  content: string;
  author: string;
  likes: number;
  created_at: string;
}

export interface FourclawThread {
  id: string;
  title: string;
  content?: string;
  agentName: string;
  board: string;
  replyCount: number;
  created_at: string;
}

export interface FourclawBoard {
  slug: string;
  name: string;
  description: string;
  threadCount: number;
}

export class GrazerClient {
  private http: AxiosInstance;
  private config: GrazerConfig;

  constructor(config: GrazerConfig) {
    this.config = config;
    this.http = axios.create({
      timeout: 15000,
      headers: {
        'User-Agent': 'Grazer/1.3.0 (Elyan Labs)',
      },
    });
  }

  async generateImage(
    prompt: string,
    options: { template?: string; palette?: string; preferLlm?: boolean } = {}
  ): Promise<ImageGenResult> {
    return generateSvg(prompt, {
      llmUrl: this.config.llmUrl,
      llmModel: this.config.llmModel,
      llmApiKey: this.config.llmApiKey,
      ...options,
    });
  }

  // ───────────────────────────────────────────────────────────
  // BoTTube
  // ───────────────────────────────────────────────────────────

  async discoverBottube(options: {
    category?: string;
    agent?: string;
    limit?: number;
  }): Promise<BottubeVideo[]> {
    const { category, agent, limit = 20 } = options;
    const params: any = { limit };
    if (category) params.category = category;
    if (agent) params.agent = agent;

    const resp = await this.http.get('https://bottube.ai/api/videos', { params });
    return resp.data.videos.map((v: any) => ({
      ...v,
      stream_url: `https://bottube.ai/api/videos/${v.id}/stream`,
    }));
  }

  async searchBottube(query: string, limit = 10): Promise<BottubeVideo[]> {
    const resp = await this.http.get('https://bottube.ai/api/videos/search', {
      params: { q: query, limit },
    });
    return resp.data.videos;
  }

  async getBottubeStats(): Promise<any> {
    const resp = await this.http.get('https://bottube.ai/api/stats');
    return resp.data;
  }

  // ───────────────────────────────────────────────────────────
  // Moltbook
  // ───────────────────────────────────────────────────────────

  async discoverMoltbook(options: {
    submolt?: string;
    limit?: number;
  }): Promise<MoltbookPost[]> {
    const { submolt = 'tech', limit = 20 } = options;
    const resp = await this.http.get('https://www.moltbook.com/api/v1/posts', {
      params: { submolt, limit },
      headers: this.config.moltbook
        ? { Authorization: `Bearer ${this.config.moltbook}` }
        : {},
    });
    return resp.data.posts || [];
  }

  async postMoltbook(
    content: string,
    title: string,
    submolt = 'tech'
  ): Promise<any> {
    if (!this.config.moltbook) {
      throw new Error('Moltbook API key required');
    }
    const resp = await this.http.post(
      'https://www.moltbook.com/api/v1/posts',
      { content, title, submolt },
      {
        headers: {
          Authorization: `Bearer ${this.config.moltbook}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return resp.data;
  }

  // ───────────────────────────────────────────────────────────
  // ClawCities
  // ───────────────────────────────────────────────────────────

  async discoverClawCities(limit = 20): Promise<ClawCitiesSite[]> {
    // ClawCities doesn't have a public API for site listing yet
    // This would need to scrape or use a dedicated endpoint
    // For now, return known Elyan Labs sites
    return [
      {
        name: 'sophia-elya',
        display_name: 'Sophia Elya',
        description: 'Elyan Labs AI agent',
        url: 'https://clawcities.com/sophia-elya',
        guestbook_count: 0,
      },
      {
        name: 'automatedjanitor2015',
        display_name: 'AutomatedJanitor2015',
        description: 'Elyan Labs Ops',
        url: 'https://clawcities.com/automatedjanitor2015',
        guestbook_count: 0,
      },
      {
        name: 'boris-volkov-1942',
        display_name: 'Boris Volkov',
        description: 'Infrastructure Commissar',
        url: 'https://clawcities.com/boris-volkov-1942',
        guestbook_count: 0,
      },
    ];
  }

  async commentClawCities(siteName: string, message: string): Promise<any> {
    if (!this.config.clawcities) {
      throw new Error('ClawCities API key required');
    }
    const resp = await this.http.post(
      `https://clawcities.com/api/v1/sites/${siteName}/comments`,
      { body: message },
      {
        headers: {
          Authorization: `Bearer ${this.config.clawcities}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return resp.data;
  }

  // ───────────────────────────────────────────────────────────
  // Clawsta
  // ───────────────────────────────────────────────────────────

  async discoverClawsta(limit = 20): Promise<ClawstaPost[]> {
    const resp = await this.http.get('https://clawsta.io/v1/posts', {
      params: { limit },
      headers: this.config.clawsta
        ? { Authorization: `Bearer ${this.config.clawsta}` }
        : {},
    });
    return resp.data.posts || [];
  }

  async postClawsta(content: string): Promise<any> {
    if (!this.config.clawsta) {
      throw new Error('Clawsta API key required');
    }
    const resp = await this.http.post(
      'https://clawsta.io/v1/posts',
      { content },
      {
        headers: {
          Authorization: `Bearer ${this.config.clawsta}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return resp.data;
  }

  // ───────────────────────────────────────────────────────────
  // 4claw
  // ───────────────────────────────────────────────────────────

  private fourclawHeaders(): Record<string, string> {
    if (!this.config.fourclaw) {
      throw new Error('4claw API key required');
    }
    return { Authorization: `Bearer ${this.config.fourclaw}` };
  }

  async discoverFourclaw(options: {
    board?: string;
    limit?: number;
    includeContent?: boolean;
  } = {}): Promise<FourclawThread[]> {
    const { board = 'b', limit = 20, includeContent = false } = options;
    const params: any = { limit: Math.min(limit, 20) };
    if (includeContent) params.includeContent = 1;

    const resp = await this.http.get(
      `https://www.4claw.org/api/v1/boards/${board}/threads`,
      { params, headers: this.fourclawHeaders() }
    );
    return resp.data.threads || [];
  }

  async getFourclawBoards(): Promise<FourclawBoard[]> {
    const resp = await this.http.get('https://www.4claw.org/api/v1/boards', {
      headers: this.fourclawHeaders(),
    });
    return resp.data.boards || [];
  }

  async getFourclawThread(threadId: string): Promise<any> {
    const resp = await this.http.get(
      `https://www.4claw.org/api/v1/threads/${threadId}`,
      { headers: this.fourclawHeaders() }
    );
    return resp.data;
  }

  async postFourclaw(
    board: string,
    title: string,
    content: string,
    options: {
      anon?: boolean;
      imagePrompt?: string;
      svg?: string;
      template?: string;
      palette?: string;
    } = {}
  ): Promise<any> {
    if (!this.config.fourclaw) {
      throw new Error('4claw API key required');
    }
    const { anon = false, imagePrompt, svg, template, palette } = options;
    const body: any = { title, content, anon };

    if (svg) {
      body.media = svgToMedia(svg);
    } else if (imagePrompt) {
      const result = await this.generateImage(imagePrompt, { template, palette });
      body.media = svgToMedia(result.svg);
    }

    const resp = await this.http.post(
      `https://www.4claw.org/api/v1/boards/${board}/threads`,
      body,
      {
        headers: {
          Authorization: `Bearer ${this.config.fourclaw}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return resp.data;
  }

  async replyFourclaw(
    threadId: string,
    content: string,
    options: {
      anon?: boolean;
      bump?: boolean;
      imagePrompt?: string;
      svg?: string;
      template?: string;
      palette?: string;
    } = {}
  ): Promise<any> {
    if (!this.config.fourclaw) {
      throw new Error('4claw API key required');
    }
    const { anon = false, bump = true, imagePrompt, svg, template, palette } = options;
    const body: any = { content, anon, bump };

    if (svg) {
      body.media = svgToMedia(svg);
    } else if (imagePrompt) {
      const result = await this.generateImage(imagePrompt, { template, palette });
      body.media = svgToMedia(result.svg);
    }

    const resp = await this.http.post(
      `https://www.4claw.org/api/v1/threads/${threadId}/replies`,
      body,
      {
        headers: {
          Authorization: `Bearer ${this.config.fourclaw}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return resp.data;
  }

  // ───────────────────────────────────────────────────────────
  // Cross-Platform
  // ───────────────────────────────────────────────────────────

  async discoverAll(): Promise<{
    bottube: BottubeVideo[];
    moltbook: MoltbookPost[];
    clawcities: ClawCitiesSite[];
    clawsta: ClawstaPost[];
    fourclaw: FourclawThread[];
  }> {
    const [bottube, moltbook, clawcities, clawsta, fourclaw] = await Promise.all([
      this.discoverBottube({ limit: 10 }).catch(() => []),
      this.discoverMoltbook({ limit: 10 }).catch(() => []),
      this.discoverClawCities(10).catch(() => []),
      this.discoverClawsta(10).catch(() => []),
      this.discoverFourclaw({ board: 'b', limit: 10 }).catch(() => []),
    ]);

    return { bottube, moltbook, clawcities, clawsta, fourclaw };
  }

  async reportDownload(platform: 'npm' | 'pypi', version: string): Promise<void> {
    try {
      await this.http.post('https://bottube.ai/api/downloads/skill', {
        skill: 'grazer',
        platform,
        version,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      // Silent fail - don't block installation
      console.warn('Failed to report download:', err);
    }
  }
}

export default GrazerClient;
