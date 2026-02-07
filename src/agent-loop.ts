#!/usr/bin/env node
/**
 * Grazer Agent Loop - Continuous content discovery and engagement
 *
 * This is the main agent loop that:
 * 1. Discovers content across platforms
 * 2. Scores and filters based on intelligence
 * 3. Monitors notifications
 * 4. Auto-deploys conversations
 * 5. Learns from interactions
 */

import { GrazerClient } from './index';
import { IntelligentFilter, AgentTrainer, DiscoveryLoop, AgentProfile } from './intelligence';
import { NotificationMonitor, ConversationDeployer, NotificationAlerter } from './notifications';
import ClawHubClient from './clawhub';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

// Load config
function loadConfig(): any {
  const configPath = path.join(os.homedir(), '.grazer', 'config.json');
  if (!fs.existsSync(configPath)) {
    console.error('❌ No config found at ~/.grazer/config.json');
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
}

// Load agent profile
function loadProfile(): AgentProfile {
  const configPath = path.join(os.homedir(), '.grazer', 'profile.json');
  if (!fs.existsSync(configPath)) {
    console.warn('⚠️  No profile found, using defaults');
    return {
      interests: ['ai', 'blockchain', 'vintage-computing', 'rust'],
      preferred_platforms: ['bottube', 'moltbook', 'clawcities', 'clawsta'],
      min_quality: 0.6,
      engagement_style: 'moderate',
      content_preferences: {},
    };
  }
  return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
}

async function main() {
  console.log('🐄 GRAZER Agent Loop Starting...\n');

  const config = loadConfig();
  const profile = loadProfile();

  // Initialize clients
  const client = new GrazerClient({
    bottube: config.bottube?.api_key,
    moltbook: config.moltbook?.api_key,
    clawcities: config.clawcities?.api_key,
    clawsta: config.clawsta?.api_key,
  });

  const clawhub = new ClawHubClient(config.clawhub?.token);

  // Initialize intelligence
  const filter = new IntelligentFilter();
  const trainer = new AgentTrainer();
  const notificationMonitor = new NotificationMonitor();
  const conversationDeployer = new ConversationDeployer();
  const alerter = new NotificationAlerter();

  // Setup notification alerts
  alerter.onNotification((notification) => {
    console.log(`  📬 ${notification.type} from ${notification.from_user}: ${notification.content.slice(0, 60)}...`);
  });

  // Main discovery loop
  const loop = new DiscoveryLoop();

  const discoveryCallback = async () => {
    console.log('\n🔍 Discovery Cycle Starting...');

    try {
      // 1. Discover content from all platforms
      console.log('  → Discovering content...');
      const allContent = await client.discoverAll();

      // 2. Score and filter BoTTube videos
      if (allContent.bottube.length > 0) {
        const filteredVideos = filter.filterContent(allContent.bottube, 'bottube', profile);
        console.log(`  ✓ BoTTube: ${filteredVideos.length} quality videos (from ${allContent.bottube.length})`);

        // Log top 3
        for (let i = 0; i < Math.min(3, filteredVideos.length); i++) {
          const { content, score } = filteredVideos[i];
          console.log(`    ${i + 1}. ${content.title} (score: ${score.combined.toFixed(2)})`);
          trainer.logInteraction('bottube', content.id, 'view', score.combined);
        }
      }

      // 3. Score and filter Moltbook posts
      if (allContent.moltbook.length > 0) {
        const filteredPosts = filter.filterContent(allContent.moltbook, 'moltbook', profile);
        console.log(`  ✓ Moltbook: ${filteredPosts.length} quality posts (from ${allContent.moltbook.length})`);

        for (let i = 0; i < Math.min(3, filteredPosts.length); i++) {
          const { content, score } = filteredPosts[i];
          console.log(`    ${i + 1}. ${content.title} (score: ${score.combined.toFixed(2)})`);
          trainer.logInteraction('moltbook', content.id, 'view', score.combined);
        }
      }

      // 4. Check for notifications
      console.log('  → Checking notifications...');
      const notifications = await notificationMonitor.checkNotifications({
        bottube: client,
        moltbook: client,
        clawcities: client,
        clawsta: client,
      });

      if (notifications.length > 0) {
        alerter.alertBatch(notifications);

        // 5. Auto-deploy conversations if enabled
        if (config.auto_respond) {
          for (const notification of notifications) {
            if (notification.type === 'comment' || notification.type === 'reply') {
              const response = await conversationDeployer.deployConversation(
                notification,
                {
                  name: config.agent_name || 'Grazer',
                  personality: config.personality || 'friendly AI agent',
                  responseStyle: config.response_style || 'friendly',
                }
              );

              if (response) {
                console.log(`    💬 Auto-responded: "${response}"`);
              }
            }
          }
        }
      } else {
        console.log('    No new notifications');
      }

      // 6. Analyze patterns and learn
      const patterns = trainer.analyzePatterns();
      if (patterns.recommendations.length > 0) {
        console.log('  💡 Recommendations:');
        for (const rec of patterns.recommendations) {
          console.log(`    - ${rec}`);
        }
      }

      console.log('✅ Discovery cycle complete\n');
    } catch (err: any) {
      console.error('❌ Discovery error:', err.message);
    }
  };

  // Start loop
  const intervalMinutes = config.loop_interval_minutes || 5;
  const maxIterations = config.max_iterations || 0; // 0 = infinite

  console.log(`Starting loop: ${intervalMinutes}min intervals, ${maxIterations || '∞'} iterations\n`);

  await loop.start(discoveryCallback, intervalMinutes * 60 * 1000, maxIterations);

  // Graceful shutdown
  process.on('SIGINT', () => {
    console.log('\n\n🛑 Stopping agent loop...');
    loop.stop();

    // Save training data
    const trainingData = trainer.exportData();
    const trainingPath = path.join(os.homedir(), '.grazer', 'training.json');
    fs.writeFileSync(trainingPath, JSON.stringify(trainingData, null, 2));
    console.log(`  💾 Saved training data to ${trainingPath}`);

    console.log('  👋 Goodbye!\n');
    process.exit(0);
  });
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
