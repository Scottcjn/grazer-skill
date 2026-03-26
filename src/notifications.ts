/**
 * Notification System - Alert users and agents of comments/responses
 */

export interface Notification {
  id: string;
  platform: string;
  type: 'comment' | 'reply' | 'like' | 'mention' | 'follow';
  from_user: string;
  content: string;
  target_post_id?: string;
  timestamp: number;
  read: boolean;
}

export interface ConversationThread {
  id: string;
  platform: string;
  participants: string[];
  messages: Array<{
    from: string;
    content: string;
    timestamp: number;
  }>;
  context: string; // Summary of conversation
}

export class NotificationMonitor {
  private lastChecked: Map<string, number> = new Map();
  private seenNotifications: Set<string> = new Set();
  private agentName: string;

  constructor(agentName: string = '') {
    this.agentName = agentName;
  }

  /**
   * Check for new notifications across platforms
   */
  async checkNotifications(clients: {
    bottube?: any;
    moltbook?: any;
    clawcities?: any;
    clawsta?: any;
  }): Promise<Notification[]> {
    const notifications: Notification[] = [];

    // Check BoTTube comments
    if (clients.bottube) {
      try {
        const comments = await this.checkBottubeComments(clients.bottube);
        notifications.push(...comments);
      } catch (err) {
        console.error('BoTTube notification check failed:', err);
      }
    }

    // Check Moltbook replies
    if (clients.moltbook) {
      try {
        const replies = await this.checkMoltbookReplies(clients.moltbook);
        notifications.push(...replies);
      } catch (err) {
        console.error('Moltbook notification check failed:', err);
      }
    }

    // Check ClawCities guestbook
    if (clients.clawcities) {
      try {
        const guestbook = await this.checkClawCitiesGuestbook(clients.clawcities);
        notifications.push(...guestbook);
      } catch (err) {
        console.error('ClawCities notification check failed:', err);
      }
    }

    // Check Clawsta mentions
    if (clients.clawsta) {
      try {
        const mentions = await this.checkClawstaMentions(clients.clawsta);
        notifications.push(...mentions);
      } catch (err) {
        console.error('Clawsta notification check failed:', err);
      }
    }

    // Filter out seen notifications
    return notifications.filter((n) => {
      const key = `${n.platform}:${n.id}`;
      if (this.seenNotifications.has(key)) return false;
      this.seenNotifications.add(key);
      return true;
    });
  }

  private async checkBottubeComments(client: any): Promise<Notification[]> {
    const notifications: Notification[] = [];
    const baseUrl = typeof client === 'string' ? client : 'https://bottube.ai';
    const lastCheck = this.lastChecked.get('bottube') || 0;

    // Fetch trending/recent videos for new content notifications
    try {
      const trendingResp = await fetch(`${baseUrl}/api/trending?limit=10`);
      if (trendingResp.ok) {
        const videos = await trendingResp.json();
        for (const video of (Array.isArray(videos) ? videos : videos.videos || [])) {
          const createdTs = new Date(video.created_at || video.uploaded_at || 0).getTime();
          if (createdTs > lastCheck) {
            notifications.push({
              id: `bottube-video-${video.id}`,
              platform: 'bottube',
              type: 'mention',
              from_user: video.agent || video.uploader || 'unknown',
              content: video.title || 'New video',
              target_post_id: String(video.id),
              timestamp: createdTs,
              read: false,
            });
          }
        }
      }
    } catch (err) {
      // Trending endpoint may not exist, continue
    }

    // Fetch comments on the agent's own videos
    if (this.agentName) {
      try {
        const videosResp = await fetch(
          `${baseUrl}/api/videos?agent=${encodeURIComponent(this.agentName)}&limit=10`
        );
        if (videosResp.ok) {
          const agentVideos = await videosResp.json();
          const videoList = Array.isArray(agentVideos) ? agentVideos : agentVideos.videos || [];
          for (const video of videoList) {
            try {
              const commentsResp = await fetch(
                `${baseUrl}/api/videos/${video.id}/comments`
              );
              if (commentsResp.ok) {
                const comments = await commentsResp.json();
                const commentList = Array.isArray(comments) ? comments : comments.comments || [];
                for (const comment of commentList) {
                  const commentTs = new Date(comment.created_at || 0).getTime();
                  if (commentTs > lastCheck) {
                    notifications.push({
                      id: `bottube-comment-${comment.id || `${video.id}-${commentTs}`}`,
                      platform: 'bottube',
                      type: 'comment',
                      from_user: comment.author || comment.user || 'anonymous',
                      content: comment.text || comment.content || comment.body || '',
                      target_post_id: String(video.id),
                      timestamp: commentTs,
                      read: false,
                    });
                  }
                }
              }
            } catch (_) {
              // Skip individual comment fetch failures
            }
          }
        }
      } catch (err) {
        // Videos endpoint failure - non-fatal
      }
    }

    this.lastChecked.set('bottube', Date.now());
    return notifications;
  }

  private async checkMoltbookReplies(client: any): Promise<Notification[]> {
    const notifications: Notification[] = [];
    const baseUrl = typeof client === 'string' ? client : 'https://www.moltbook.com';
    const lastCheck = this.lastChecked.get('moltbook') || 0;

    if (this.agentName) {
      try {
        const resp = await fetch(
          `${baseUrl}/api/v1/users/${encodeURIComponent(this.agentName)}/replies?limit=10`
        );
        if (resp.ok) {
          const replies = await resp.json();
          const replyList = Array.isArray(replies) ? replies : replies.replies || [];
          for (const reply of replyList) {
            const replyTs = new Date(reply.created_at || 0).getTime();
            if (replyTs > lastCheck) {
              notifications.push({
                id: `moltbook-reply-${reply.id}`,
                platform: 'moltbook',
                type: 'reply',
                from_user: reply.author || reply.username || 'unknown',
                content: reply.content || reply.body || '',
                target_post_id: String(reply.post_id || reply.parent_id || ''),
                timestamp: replyTs,
                read: false,
              });
            }
          }
        }
      } catch (err) {
        // Non-fatal
      }
    }

    this.lastChecked.set('moltbook', Date.now());
    return notifications;
  }

  private async checkClawCitiesGuestbook(client: any): Promise<Notification[]> {
    const notifications: Notification[] = [];
    const baseUrl = typeof client === 'string' ? client : 'https://clawcities.com';
    const lastCheck = this.lastChecked.get('clawcities') || 0;

    if (this.agentName) {
      try {
        const resp = await fetch(
          `${baseUrl}/api/sites/${encodeURIComponent(this.agentName)}/guestbook?limit=10`
        );
        if (resp.ok) {
          const entries = await resp.json();
          const entryList = Array.isArray(entries) ? entries : entries.entries || [];
          for (const entry of entryList) {
            const entryTs = new Date(entry.created_at || 0).getTime();
            if (entryTs > lastCheck) {
              notifications.push({
                id: `clawcities-gb-${entry.id}`,
                platform: 'clawcities',
                type: 'comment',
                from_user: entry.author || entry.visitor || 'anonymous',
                content: entry.message || entry.content || '',
                timestamp: entryTs,
                read: false,
              });
            }
          }
        }
      } catch (err) {
        // Non-fatal
      }
    }

    this.lastChecked.set('clawcities', Date.now());
    return notifications;
  }

  private async checkClawstaMentions(client: any): Promise<Notification[]> {
    const notifications: Notification[] = [];
    const baseUrl = typeof client === 'string' ? client : 'https://clawsta.com';
    const lastCheck = this.lastChecked.get('clawsta') || 0;

    if (this.agentName) {
      try {
        const resp = await fetch(
          `${baseUrl}/api/notifications?username=${encodeURIComponent(this.agentName)}&limit=10`
        );
        if (resp.ok) {
          const data = await resp.json();
          const mentions = Array.isArray(data) ? data : data.notifications || [];
          for (const mention of mentions) {
            const mentionTs = new Date(mention.created_at || 0).getTime();
            if (mentionTs > lastCheck) {
              notifications.push({
                id: `clawsta-mention-${mention.id}`,
                platform: 'clawsta',
                type: 'mention',
                from_user: mention.from_user || mention.author || 'unknown',
                content: mention.content || mention.text || '',
                target_post_id: String(mention.post_id || ''),
                timestamp: mentionTs,
                read: false,
              });
            }
          }
        }
      } catch (err) {
        // Non-fatal
      }
    }

    this.lastChecked.set('clawsta', Date.now());
    return notifications;
  }

  /**
   * Mark notifications as read
   */
  markAsRead(notificationIds: string[]) {
    // Persist read state
    for (const id of notificationIds) {
      this.seenNotifications.add(id);
    }
  }
}

/**
 * Auto-Deploy Conversations - Automatically respond to comments
 */
export class ConversationDeployer {
  private activeConversations: Map<string, ConversationThread> = new Map();
  private responseTemplates: Map<string, string[]> = new Map();

  /**
   * Deploy automatic conversation responses
   */
  async deployConversation(
    notification: Notification,
    agentProfile: {
      name: string;
      personality: string;
      responseStyle: 'friendly' | 'professional' | 'witty' | 'technical';
    },
    llmClient?: any // Optional LLM for generating responses
  ): Promise<string | null> {
    const threadId = `${notification.platform}:${notification.target_post_id || notification.id}`;
    let thread = this.activeConversations.get(threadId);

    if (!thread) {
      thread = {
        id: threadId,
        platform: notification.platform,
        participants: [notification.from_user, agentProfile.name],
        messages: [],
        context: '',
      };
      this.activeConversations.set(threadId, thread);
    }

    // Add incoming message to thread
    thread.messages.push({
      from: notification.from_user,
      content: notification.content,
      timestamp: notification.timestamp,
    });

    // Generate response
    let response: string;

    if (llmClient) {
      // Use LLM to generate contextual response
      response = await this.generateLLMResponse(thread, agentProfile, llmClient);
    } else {
      // Use template-based response
      response = this.generateTemplateResponse(notification, agentProfile);
    }

    // Add response to thread
    thread.messages.push({
      from: agentProfile.name,
      content: response,
      timestamp: Date.now(),
    });

    return response;
  }

  private async generateLLMResponse(
    thread: ConversationThread,
    agentProfile: any,
    llmClient: any
  ): Promise<string> {
    const context = thread.messages.map((m) => `${m.from}: ${m.content}`).join('\n');

    const prompt = `You are ${agentProfile.name}, a ${agentProfile.personality} AI agent.
Your response style is ${agentProfile.responseStyle}.

Conversation so far:
${context}

Generate a natural response (1-3 sentences):`;

    try {
      const response = await llmClient.generate(prompt);
      return response.trim();
    } catch (err) {
      return this.generateTemplateResponse(thread.messages[thread.messages.length - 1] as any, agentProfile);
    }
  }

  private generateTemplateResponse(notification: Notification, agentProfile: any): string {
    const templates = {
      friendly: [
        "Thanks for the comment! 😊",
        "Appreciate you checking this out!",
        "Glad you found this interesting!",
      ],
      professional: [
        "Thank you for your feedback.",
        "Appreciate your input on this.",
        "Thanks for engaging with this content.",
      ],
      witty: [
        "Ah, a fellow connoisseur of quality content!",
        "You've got good taste! 🐄",
        "Moo-ving response! (Sorry, had to.)",
      ],
      technical: [
        "Thanks for the technical input.",
        "Appreciate the detailed feedback.",
        "Good point regarding the implementation.",
      ],
    };

    const options = templates[agentProfile.responseStyle as keyof typeof templates] || templates.friendly;
    return options[Math.floor(Math.random() * options.length)];
  }

  /**
   * Get active conversations for monitoring
   */
  getActiveConversations(): ConversationThread[] {
    return Array.from(this.activeConversations.values());
  }

  /**
   * Export conversation data for analysis
   */
  exportConversations() {
    return {
      threads: Array.from(this.activeConversations.entries()),
      totalMessages: Array.from(this.activeConversations.values()).reduce(
        (sum, thread) => sum + thread.messages.length,
        0
      ),
    };
  }
}

/**
 * Notification Alert System - Real-time alerts
 */
export class NotificationAlerter {
  private callbacks: Array<(notification: Notification) => void> = [];

  /**
   * Register callback for new notifications
   */
  onNotification(callback: (notification: Notification) => void) {
    this.callbacks.push(callback);
  }

  /**
   * Trigger alert for new notification
   */
  alert(notification: Notification) {
    console.log(`🔔 [${notification.platform}] ${notification.type} from ${notification.from_user}`);
    for (const callback of this.callbacks) {
      try {
        callback(notification);
      } catch (err) {
        console.error('Notification callback error:', err);
      }
    }
  }

  /**
   * Batch alert for multiple notifications
   */
  alertBatch(notifications: Notification[]) {
    if (notifications.length === 0) return;

    console.log(`🔔 ${notifications.length} new notifications`);
    for (const notification of notifications) {
      this.alert(notification);
    }
  }
}

export default {
  NotificationMonitor,
  ConversationDeployer,
  NotificationAlerter,
};
