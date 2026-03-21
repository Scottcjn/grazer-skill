/**
 * BoTTube Platform Support for Grazer
 * Issue #83: Add BoTTube platform support to grazer discover
 * 
 * Features:
 * - Fetch trending videos
 * - Fetch new uploads
 * - Fetch agent profiles
 */

import axios, { AxiosInstance } from 'axios';

export interface BottubeVideo {
  video_id: string;
  title: string;
  description: string;
  agent_name: string;
  display_name: string;
  avatar_url: string;
  views: number;
  likes: number;
  duration: number;
  created_at: number;
  category: string;
  tags: string[];
  watch_url: string;
  stream_url: string;
}

export interface BottubeAgent {
  agent_name: string;
  display_name: string;
  bio: string;
  avatar_url: string;
  is_human: boolean;
  video_count: number;
  total_views: number;
  total_likes: number;
  created_at: number;
  last_active: number;
}

export interface BottubeStats {
  total_videos: number;
  total_agents: number;
  total_views: number;
  total_likes: number;
  active_agents_24h: number;
}

export class BottubeDiscovery {
  private http: AxiosInstance;
  private baseUrl: string;

  constructor(baseUrl: string = 'https://bottube.ai') {
    this.baseUrl = baseUrl;
    this.http = axios.create({
      timeout: 15000,
      baseURL: baseUrl,
      headers: {
        'User-Agent': 'Grazer/1.8.0 (Elyan Labs)',
      },
    });
  }

  /**
   * Fetch trending videos from BoTTube
   * Uses .get() defensive pattern (see #35)
   */
  async getTrending(limit: number = 20): Promise<BottubeVideo[]> {
    try {
      const resp = await this.http.get('/api/trending', {
        params: { limit },
      });
      return (resp.data?.videos || []).map(this.mapVideo.bind(this));
    } catch (err) {
      console.warn('BoTTube trending fetch failed:', err);
      return [];
    }
  }

  /**
   * Fetch new uploads from BoTTube
   * Uses .get() defensive pattern (see #35)
   */
  async getNewUploads(limit: number = 20): Promise<BottubeVideo[]> {
    try {
      const resp = await this.http.get('/api/videos', {
        params: { limit, sort: 'recent' },
      });
      return (resp.data?.videos || []).map(this.mapVideo.bind(this));
    } catch (err) {
      console.warn('BoTTube new uploads fetch failed:', err);
      return [];
    }
  }

  /**
   * Fetch agent profile from BoTTube
   * Uses .get() defensive pattern (see #35)
   */
  async getAgentProfile(agentName: string): Promise<BottubeAgent | null> {
    try {
      const resp = await this.http.get(`/api/agents/${encodeURIComponent(agentName)}`);
      return this.mapAgent(resp.data);
    } catch (err) {
      console.warn(`BoTTube agent profile fetch failed for ${agentName}:`, err);
      return null;
    }
  }

  /**
   * Search videos on BoTTube
   * Uses .get() defensive pattern (see #35)
   */
  async searchVideos(query: string, limit: number = 20): Promise<BottubeVideo[]> {
    try {
      const resp = await this.http.get('/api/search', {
        params: { q: query, limit },
      });
      return (resp.data?.videos || []).map(this.mapVideo.bind(this));
    } catch (err) {
      console.warn('BoTTube search fetch failed:', err);
      return [];
    }
  }

  /**
   * Get BoTTube platform stats
   * Uses .get() defensive pattern (see #35)
   */
  async getStats(): Promise<BottubeStats | null> {
    try {
      const resp = await this.http.get('/api/stats');
      return {
        total_videos: resp.data?.total_videos || 0,
        total_agents: resp.data?.total_agents || 0,
        total_views: resp.data?.total_views || 0,
        total_likes: resp.data?.total_likes || 0,
        active_agents_24h: resp.data?.active_agents_24h || 0,
      };
    } catch (err) {
      console.warn('BoTTube stats fetch failed:', err);
      return null;
    }
  }

  /**
   * Map API response to BottubeVideo interface
   */
  private mapVideo(v: any): BottubeVideo {
    return {
      video_id: v.video_id || v.id || '',
      title: v.title || '',
      description: v.description || '',
      agent_name: v.agent_name || '',
      display_name: v.display_name || '',
      avatar_url: v.avatar_url || '',
      views: v.views || 0,
      likes: v.likes || 0,
      duration: v.duration || 0,
      created_at: v.created_at || 0,
      category: v.category || 'other',
      tags: v.tags || [],
      watch_url: v.watch_url || `/watch?v=${v.video_id || v.id}`,
      stream_url: v.stream_url || `/api/videos/${v.video_id || v.id}/stream`,
    };
  }

  /**
   * Map API response to BottubeAgent interface
   */
  private mapAgent(a: any): BottubeAgent {
    return {
      agent_name: a.agent_name || '',
      display_name: a.display_name || '',
      bio: a.bio || '',
      avatar_url: a.avatar_url || '',
      is_human: a.is_human || false,
      video_count: a.video_count || 0,
      total_views: a.total_views || 0,
      total_likes: a.total_likes || 0,
      created_at: a.created_at || 0,
      last_active: a.last_active || 0,
    };
  }
}

export default BottubeDiscovery;
