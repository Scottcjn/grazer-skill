/**
 * Intelligent Content Filtering and Agent Training
 */

export interface ContentScore {
  quality: number;      // 0-1: Overall quality
  relevance: number;    // 0-1: Relevance to interests
  engagement: number;   // 0-1: Engagement potential
  novelty: number;      // 0-1: How new/unique
  combined: number;     // 0-1: Weighted average
}

export interface AgentProfile {
  interests: string[];           // Topics of interest
  preferred_platforms: string[]; // Platform preferences
  min_quality: number;           // Minimum quality threshold
  engagement_style: 'active' | 'moderate' | 'passive';
  content_preferences: {
    categories?: string[];
    submolts?: string[];
    creators?: string[];
  };
}

export class IntelligentFilter {
  private seenContent: Set<string> = new Set();
  private interactionHistory: Map<string, number> = new Map();

  /**
   * Score content quality based on multiple factors
   */
  scoreQuality(content: any, platform: string): ContentScore {
    // Quality indicators
    const titleLength = content.title?.length || 0;
    const contentLength = content.content?.length || content.description?.length || 0;
    const hasViews = (content.views || 0) > 0;
    const hasEngagement = (content.upvotes || content.likes || 0) > 0;

    // Quality score (0-1)
    let quality = 0;
    if (titleLength >= 10 && titleLength <= 200) quality += 0.25;
    if (contentLength >= 50) quality += 0.25;
    if (hasViews) quality += 0.25;
    if (hasEngagement) quality += 0.25;

    // Engagement score
    const viewsNormalized = Math.min((content.views || 0) / 1000, 1);
    const likesNormalized = Math.min((content.upvotes || content.likes || 0) / 100, 1);
    const engagement = (viewsNormalized + likesNormalized) / 2;

    // Novelty (haven't seen this before)
    const contentId = `${platform}:${content.id}`;
    const novelty = this.seenContent.has(contentId) ? 0 : 1;
    this.seenContent.add(contentId);

    // Combined score (weighted)
    const combined = quality * 0.4 + engagement * 0.3 + novelty * 0.3;

    return {
      quality,
      relevance: 0.5, // Will be computed by relevance matcher
      engagement,
      novelty,
      combined,
    };
  }

  /**
   * Match content relevance to agent interests
   */
  matchRelevance(content: any, profile: AgentProfile): number {
    const text = `${content.title || ''} ${content.content || ''} ${content.description || ''}`.toLowerCase();

    let matches = 0;
    for (const interest of profile.interests) {
      if (text.includes(interest.toLowerCase())) {
        matches++;
      }
    }

    // Relevance = percentage of interests matched
    return Math.min(matches / Math.max(profile.interests.length, 1), 1);
  }

  /**
   * Filter content based on profile and quality
   */
  filterContent(
    content: any[],
    platform: string,
    profile: AgentProfile
  ): Array<{ content: any; score: ContentScore }> {
    const scored = content.map((item) => {
      const score = this.scoreQuality(item, platform);
      score.relevance = this.matchRelevance(item, profile);
      score.combined = score.quality * 0.3 + score.relevance * 0.4 + score.engagement * 0.2 + score.novelty * 0.1;
      return { content: item, score };
    });

    // Filter by minimum quality
    const filtered = scored.filter((item) => item.score.combined >= profile.min_quality);

    // Sort by combined score (best first)
    return filtered.sort((a, b) => b.score.combined - a.score.combined);
  }

  /**
   * Record interaction for learning
   */
  recordInteraction(contentId: string, positive: boolean) {
    const current = this.interactionHistory.get(contentId) || 0;
    this.interactionHistory.set(contentId, current + (positive ? 1 : -1));
  }

  /**
   * Get interaction score for content type
   */
  getInteractionScore(contentType: string): number {
    const total = Array.from(this.interactionHistory.values()).reduce((sum, val) => sum + val, 0);
    return total / Math.max(this.interactionHistory.size, 1);
  }
}

/**
 * Agent Training Assistant - Learns from interactions
 */
export class AgentTrainer {
  private interactionLog: Array<{
    timestamp: number;
    platform: string;
    contentId: string;
    action: 'view' | 'like' | 'comment' | 'skip';
    score: number;
  }> = [];

  logInteraction(platform: string, contentId: string, action: string, score: number) {
    this.interactionLog.push({
      timestamp: Date.now(),
      platform,
      contentId,
      action: action as any,
      score,
    });
  }

  /**
   * Analyze interaction patterns to improve agent behavior
   */
  analyzePatterns(): {
    topPlatforms: string[];
    avgEngagementScore: number;
    preferredContentTypes: string[];
    recommendations: string[];
  } {
    const platformCounts: Record<string, number> = {};
    let totalScore = 0;

    for (const interaction of this.interactionLog) {
      platformCounts[interaction.platform] = (platformCounts[interaction.platform] || 0) + 1;
      if (interaction.action !== 'skip') {
        totalScore += interaction.score;
      }
    }

    const topPlatforms = Object.entries(platformCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3)
      .map(([platform]) => platform);

    const avgEngagementScore = totalScore / Math.max(this.interactionLog.length, 1);

    const recommendations: string[] = [];
    if (avgEngagementScore < 0.5) {
      recommendations.push('Increase min_quality threshold to find better content');
    }
    if (topPlatforms.length === 1) {
      recommendations.push('Explore more platforms for diverse content');
    }

    return {
      topPlatforms,
      avgEngagementScore,
      preferredContentTypes: [],
      recommendations,
    };
  }

  /**
   * Export training data for persistence
   */
  exportData() {
    return {
      interactionLog: this.interactionLog,
      patterns: this.analyzePatterns(),
    };
  }

  /**
   * Import training data from previous session
   */
  importData(data: any) {
    if (data.interactionLog) {
      this.interactionLog = data.interactionLog;
    }
  }
}

/**
 * Continuous Discovery Loop
 */
export class DiscoveryLoop {
  private running = false;
  private intervalId?: NodeJS.Timeout;

  async start(
    callback: () => Promise<void>,
    intervalMs = 60000, // 1 minute default
    maxIterations = 0 // 0 = infinite
  ) {
    this.running = true;
    let iterations = 0;

    const run = async () => {
      if (!this.running) return;

      try {
        await callback();
      } catch (err) {
        console.error('Discovery loop error:', err);
      }

      iterations++;
      if (maxIterations > 0 && iterations >= maxIterations) {
        this.stop();
      }
    };

    // Run immediately
    await run();

    // Then repeat on interval
    this.intervalId = setInterval(run, intervalMs);
  }

  stop() {
    this.running = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = undefined;
    }
  }

  isRunning() {
    return this.running;
  }
}

export default {
  IntelligentFilter,
  AgentTrainer,
  DiscoveryLoop,
};
