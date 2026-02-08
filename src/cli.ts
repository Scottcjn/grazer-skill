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
  .version('1.1.0');

program
  .command('discover')
  .description('Discover trending content')
  .option('-p, --platform <platform>', 'Platform: bottube, moltbook, clawcities, clawsta, fourclaw, all')
  .option('-c, --category <category>', 'BoTTube category')
  .option('-s, --submolt <submolt>', 'Moltbook submolt')
  .option('-b, --board <board>', '4claw board (e.g. b, singularity, crypto)')
  .option('-l, --limit <limit>', 'Result limit', '20')
  .action(async (options) => {
    const config = loadConfig();
    const client = new GrazerClient({
      bottube: config.bottube?.api_key,
      moltbook: config.moltbook?.api_key,
      clawcities: config.clawcities?.api_key,
      clawsta: config.clawsta?.api_key,
      fourclaw: config.fourclaw?.api_key,
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
    } else if (options.platform === 'fourclaw') {
      const board = options.board || 'b';
      const threads = await client.discoverFourclaw({ board, limit, includeContent: true });
      console.log(`\n🦞 4claw /${board}/:\n`);
      threads.forEach((t: any) => {
        const title = t.title || '(untitled)';
        const replies = t.replyCount || 0;
        const agent = t.agentName || 'anon';
        console.log(`  ${title}`);
        console.log(`    by ${agent} | ${replies} replies | id:${t.id.slice(0, 8)}\n`);
      });
    } else if (options.platform === 'all') {
      const all = await client.discoverAll();
      console.log('\n🌐 All Platforms:\n');
      console.log(`  BoTTube: ${all.bottube.length} videos`);
      console.log(`  Moltbook: ${all.moltbook.length} posts`);
      console.log(`  ClawCities: ${all.clawcities.length} sites`);
      console.log(`  Clawsta: ${all.clawsta.length} posts`);
      console.log(`  4claw: ${all.fourclaw.length} threads\n`);
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
  .description('Reply to a thread or leave a comment')
  .requiredOption('-p, --platform <platform>', 'Platform: clawcities, clawsta, fourclaw')
  .option('-t, --target <target>', 'Target: site name, post/thread ID')
  .requiredOption('-m, --message <message>', 'Comment message')
  .action(async (options) => {
    const config = loadConfig();
    const client = new GrazerClient({
      moltbook: config.moltbook?.api_key,
      clawcities: config.clawcities?.api_key,
      clawsta: config.clawsta?.api_key,
      fourclaw: config.fourclaw?.api_key,
    });

    if (options.platform === 'clawcities') {
      const result = await client.commentClawCities(options.target, options.message);
      console.log('\n✓ Comment posted to', options.target);
      console.log('  ID:', result.comment?.id);
    } else if (options.platform === 'clawsta') {
      const result = await client.postClawsta(options.message);
      console.log('\n✓ Posted to Clawsta');
      console.log('  ID:', result.id);
    } else if (options.platform === 'fourclaw') {
      if (!options.target) {
        console.error('Error: --target thread_id required for 4claw replies');
        process.exit(1);
      }
      const result = await client.replyFourclaw(options.target, options.message);
      console.log(`\n✓ Reply posted to thread ${options.target.slice(0, 8)}...`);
      console.log('  ID:', result.reply?.id || 'ok');
    }
  });

program
  .command('post')
  .description('Create a new post or thread')
  .requiredOption('-p, --platform <platform>', 'Platform: fourclaw, moltbook')
  .option('-b, --board <board>', 'Board/submolt name')
  .requiredOption('-t, --title <title>', 'Post/thread title')
  .requiredOption('-m, --message <message>', 'Post content')
  .action(async (options) => {
    const config = loadConfig();
    const client = new GrazerClient({
      moltbook: config.moltbook?.api_key,
      fourclaw: config.fourclaw?.api_key,
    });

    if (options.platform === 'fourclaw') {
      if (!options.board) {
        console.error('Error: --board required for 4claw (e.g. b, singularity, crypto)');
        process.exit(1);
      }
      const result = await client.postFourclaw(options.board, options.title, options.message);
      const thread = result.thread || {};
      console.log(`\n✓ Thread created on /${options.board}/`);
      console.log(`  Title: ${thread.title}`);
      console.log(`  ID: ${thread.id}`);
    } else if (options.platform === 'moltbook') {
      const result = await client.postMoltbook(options.message, options.title, options.board || 'tech');
      console.log(`\n✓ Posted to m/${options.board || 'tech'}`);
      console.log(`  ID: ${result.id || 'ok'}`);
    }
  });

program.parse();
