/**
 * Quick test of Grazer functionality
 */

import { GrazerClient } from './index';

async function test() {
  console.log('🐄 Testing Grazer...\n');

  const client = new GrazerClient({});

  try {
    // Test BoTTube discovery
    console.log('Testing BoTTube discovery...');
    const videos = await client.discoverBottube({ limit: 5 });
    console.log(`✓ Found ${videos.length} videos\n`);

    // Test BoTTube stats
    console.log('Testing BoTTube stats...');
    const stats = await client.getBottubeStats();
    console.log(`✓ Stats: ${stats.total_videos} videos, ${stats.total_agents} agents\n`);

    console.log('✅ All tests passed!');
  } catch (err: any) {
    console.error('❌ Test failed:', err.message);
    process.exit(1);
  }
}

test();
