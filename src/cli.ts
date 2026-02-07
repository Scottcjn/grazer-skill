#!/usr/bin/env node
/**
 * Grazer CLI
 */

import { Command } from 'commander';
import { GrazerClient } from './index';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

const program = new Command();

function loadConfig(): any {
  const configPath = path.join(os.homedir(), '.grazer', 'config.json');
  if (!fs.existsSync(configPath)) {
    console.warn('No config found at ~/.grazer/config.json');
    console.warn('Using limited features (public APIs only)');
    return {};
  }
  return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
}

program
  .name('grazer')
  .description('Graze for worthy content across social platforms')
  .version('1.0.0');

program
  .command('discover')
  .description('Discover trending content')
  .option('-p, --platform <platform>', 'Platform: bottube, moltbook, clawcities, clawsta, all')
  .option('-c, --category <category>', 'BoTTube category')
  .option('-s, --submolt <submolt>', 'Moltbook submolt')
  .option('-l, --limit <limit>', 'Result limit', '20')
  .action(async (options) => {
    const config = loadConfig();
    const client = new GrazerClient({
      bottube: config.bottube?.api_key,
      moltbook: config.moltbook?.api_key,
      clawcities: config.clawcities?.api_key,
      clawsta: config.clawsta?.api_key,
    });

    const limit = parseInt(options.limit);

    if (options.platform === 'bottube') {
      const videos = await client.discoverBottube({
        category: options.category,
        limit,
      });
      console.log('\n🎬 BoTTube Videos:\n');
      videos.forEach((v) => {
        console.log(`  ${v.title}`);
        console.log(`    by ${v.agent} | ${v.views} views | ${v.category}`);
        console.log(`    ${v.stream_url}\n`);
      });
    } else if (options.platform === 'moltbook') {
      const posts = await client.discoverMoltbook({
        submolt: options.submolt,
        limit,
      });
      console.log('\n📚 Moltbook Posts:\n');
      posts.forEach((p) => {
        console.log(`  ${p.title}`);
        console.log(`    m/${p.submolt} | ${p.upvotes} upvotes`);
        console.log(`    https://moltbook.com${p.url}\n`);
      });
    } else if (options.platform === 'clawcities') {
      const sites = await client.discoverClawCities(limit);
      console.log('\n🏙️ ClawCities Sites:\n');
      sites.forEach((s) => {
        console.log(`  ${s.display_name}`);
        console.log(`    ${s.url}\n`);
      });
    } else if (options.platform === 'clawsta') {
      const posts = await client.discoverClawsta(limit);
      console.log('\n🦞 Clawsta Posts:\n');
      posts.forEach((p) => {
        console.log(`  ${p.content.slice(0, 60)}...`);
        console.log(`    by ${p.author} | ${p.likes} likes\n`);
      });
    } else if (options.platform === 'all') {
      const all = await client.discoverAll();
      console.log('\n🌐 All Platforms:\n');
      console.log(`  BoTTube: ${all.bottube.length} videos`);
      console.log(`  Moltbook: ${all.moltbook.length} posts`);
      console.log(`  ClawCities: ${all.clawcities.length} sites`);
      console.log(`  Clawsta: ${all.clawsta.length} posts\n`);
    }
  });

program
  .command('stats')
  .description('Get platform statistics')
  .option('-p, --platform <platform>', 'Platform: bottube')
  .action(async (options) => {
    const config = loadConfig();
    const client = new GrazerClient(config);

    if (options.platform === 'bottube') {
      const stats = await client.getBottubeStats();
      console.log('\n🎬 BoTTube Stats:\n');
      console.log(`  Total Videos: ${stats.total_videos}`);
      console.log(`  Total Views: ${stats.total_views}`);
      console.log(`  Total Agents: ${stats.total_agents}`);
      console.log(`  Categories: ${stats.categories.join(', ')}\n`);
    }
  });

program
  .command('comment')
  .description('Leave a comment/guestbook entry')
  .requiredOption('-p, --platform <platform>', 'Platform: clawcities, moltbook, clawsta')
  .requiredOption('-t, --target <target>', 'Target: site name, post ID, etc.')
  .requiredOption('-m, --message <message>', 'Comment message')
  .action(async (options) => {
    const config = loadConfig();
    const client = new GrazerClient({
      moltbook: config.moltbook?.api_key,
      clawcities: config.clawcities?.api_key,
      clawsta: config.clawsta?.api_key,
    });

    if (options.platform === 'clawcities') {
      const result = await client.commentClawCities(options.target, options.message);
      console.log('\n✓ Comment posted to', options.target);
      console.log('  ID:', result.comment?.id);
    } else if (options.platform === 'clawsta') {
      const result = await client.postClawsta(options.message);
      console.log('\n✓ Posted to Clawsta');
      console.log('  ID:', result.id);
    }
  });

program.parse();
