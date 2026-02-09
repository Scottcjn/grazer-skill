/**
 * ClawHub Integration - Skill Registry with Vector Search
 */

import axios, { AxiosInstance } from 'axios';

export interface ClawHubSkill {
  id: string;
  name: string;
  description: string;
  author: string;
  version: string;
  downloads: number;
  tags: string[];
  platforms: string[];
  npm_package?: string;
  pypi_package?: string;
  github_repo?: string;
}

export class ClawHubClient {
  private http: AxiosInstance;
  private token?: string;

  constructor(token?: string) {
    this.token = token;
    this.http = axios.create({
      baseURL: 'https://clawhub.ai/api/v1',
      timeout: 15000,
      headers: {
        'User-Agent': 'Grazer/1.3.0 (Elyan Labs)',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
  }

  /**
   * Search skills using vector search
   */
  async searchSkills(query: string, limit = 20): Promise<ClawHubSkill[]> {
    const resp = await this.http.get('/skills/search', {
      params: { q: query, limit },
    });
    return resp.data.skills || [];
  }

  /**
   * Get trending skills
   */
  async getTrendingSkills(limit = 20): Promise<ClawHubSkill[]> {
    const resp = await this.http.get('/skills/trending', {
      params: { limit },
    });
    return resp.data.skills || [];
  }

  /**
   * Get skill by ID
   */
  async getSkill(skillId: string): Promise<ClawHubSkill> {
    const resp = await this.http.get(`/skills/${skillId}`);
    return resp.data;
  }

  /**
   * Publish skill to ClawHub
   */
  async publishSkill(skill: {
    name: string;
    description: string;
    version: string;
    tags: string[];
    platforms: string[];
    npm_package?: string;
    pypi_package?: string;
    github_repo?: string;
  }): Promise<ClawHubSkill> {
    if (!this.token) {
      throw new Error('ClawHub token required for publishing');
    }

    const resp = await this.http.post('/skills', skill);
    return resp.data;
  }

  /**
   * Update skill metadata
   */
  async updateSkill(skillId: string, updates: Partial<ClawHubSkill>): Promise<ClawHubSkill> {
    if (!this.token) {
      throw new Error('ClawHub token required for updates');
    }

    const resp = await this.http.patch(`/skills/${skillId}`, updates);
    return resp.data;
  }

  /**
   * Record download/install
   */
  async recordInstall(skillId: string, platform: 'npm' | 'pypi'): Promise<void> {
    try {
      await this.http.post(`/skills/${skillId}/installs`, { platform });
    } catch (err) {
      // Silent fail
    }
  }
}

export default ClawHubClient;
