import axios from 'axios';

export interface YouTubeVideo {
  id: string;
  title: string;
  channelTitle: string;
  description: string;
  publishedAt: string;
  url: string;
  viewCount?: string;
  likeCount?: string;
}

export class YouTubeDiscovery {
  private apiKey: string | undefined;

  constructor(apiKey?: string) {
    this.apiKey = apiKey;
  }

  /**
   * Discover videos. Uses API if key available, otherwise falls back to scraping.
   */
  async discover(options: { query?: string; limit?: number }): Promise<YouTubeVideo[]> {
    const limit = options.limit || 10;
    const query = options.query || 'AI agents';

    if (this.apiKey) {
      return this.discoverViaApi(query, limit);
    } else {
      return this.scrapeBasic(query, limit);
    }
  }

  private async discoverViaApi(query: string, limit: number): Promise<YouTubeVideo[]> {
    try {
      const url = `https://www.googleapis.com/youtube/v3/search`;
      const resp = await axios.get(url, {
        params: {
          part: 'snippet',
          q: query,
          maxResults: limit,
          type: 'video',
          key: this.apiKey,
        },
      });

      return (resp.data.items || []).map((item: any) => ({
        id: item.id?.videoId || '',
        title: item.snippet?.title || '',
        channelTitle: item.snippet?.channelTitle || '',
        description: item.snippet?.description || '',
        publishedAt: item.snippet?.publishedAt || '',
        url: `https://www.youtube.com/watch?v=${item.id?.videoId}`,
      }));
    } catch (err) {
      console.warn('YouTube API call failed, falling back to scraping:', err);
      return this.scrapeBasic(query, limit);
    }
  }

  /**
   * Lightweight scraping fallback for basic info without API key.
   */
  async scrapeBasic(query: string, limit = 5): Promise<YouTubeVideo[]> {
    try {
      const searchUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`;
      const resp = await axios.get(searchUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        },
      });

      const html = resp.data;
      const videoIds = [...html.matchAll(/\/watch\?v=([a-zA-Z0-9_-]{11})/g)].map((m: any) => m[1]);
      const uniqueIds = [...new Set(videoIds)].slice(0, limit);

      return uniqueIds.map((id) => ({
        id,
        title: 'YouTube Video (Scraped)',
        channelTitle: 'Unknown Channel',
        description: 'Metadata available via API key',
        publishedAt: new Date().toISOString(),
        url: `https://www.youtube.com/watch?v=${id}`,
      }));
    } catch (err) {
      throw new Error(`YouTube scraping failed: ${err}`);
    }
  }
}
