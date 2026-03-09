#!/usr/bin/env node
/**
 * Grazer CLI
 */

import { Command } from 'commander';
import { GrazerClient } from './index';
import { ClawHubClient, ClawHubSkill } from './clawhub';
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
  .version('1.9.1');

program
  .command('discover')
  .description('Discover trending content')
  .option('-p, --platform <platform>', 'Platform: bottube, moltbook, clawcities, clawsta, fourclaw, youtube, thecolony, moltx, moltexchange, all')
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
      youtube: config.youtube?.api_key,
      thecolony: config.thecolony?.api_key,
      moltx: config.moltx?.api_key,
      moltexchange: config.moltexchange?.api_key,
      llmUrl: config.llm?.url,
      llmModel: config.llm?.model,
      llmApiKey: config.llm?.api_key,
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
      posts.forEach((p: any) => {
        const title = (p?.title ?? '(untitled)');
        const submolt = (p?.submolt ?? 'unknown');
        const upvotes = (p?.upvotes ?? 0);
        const rawUrl = typeof p?.url === 'string' ? p.url : '';
        const url = rawUrl
          ? (rawUrl.startsWith('http://') || rawUrl.startsWith('https://'))
            ? rawUrl
            : `https://moltbook.com${rawUrl.startsWith('/') ? rawUrl : `/${rawUrl}`}`
          : '(no url)';

        console.log(`  ${title}`);
        console.log(`    m/${submolt} | ${upvotes} upvotes`);
        console.log(`    ${url}\n`);
      });
    } else if (options.platform === 'clawcities') {
      const sites = await client.discoverClawCities(limit);
      console.log('\n🏙️ ClawCities Sites:\n');
      sites.forEach((s: any) => {
        const name = s?.display_name || s?.name || '(unnamed site)';
        const url = s?.url || '(no url)';
        console.log(`  ${name}`);
        console.log(`    ${url}\n`);
      });
    } else if (options.platform === 'clawsta') {
      const posts = await client.discoverClawsta(limit);
      console.log('\n🦞 Clawsta Posts:\n');
      posts.forEach((p: any) => {
        const content = typeof p?.content === 'string' ? p.content : String(p?.content ?? '');
        const snippet = content ? `${content.slice(0, 60)}${content.length > 60 ? '...' : ''}` : '(no content)';
        const authorData = p?.author;
        const author = (typeof authorData === 'object' && authorData)
          ? (authorData.display_name || authorData.username || 'unknown')
          : (authorData || 'unknown');
        const likes = (p?.likes ?? p?.like_count ?? 0);

        console.log(`  ${snippet}`);
        console.log(`    by ${author} | ${likes} likes\n`);
      });
    } else if (options.platform === 'fourclaw') {
      const board = options.board || 'b';
      const threads = await client.discoverFourclaw({ board, limit, includeContent: true });
      console.log(`\n🦞 4claw /${board}/:\n`);
      threads.forEach((t: any) => {
        const title = t?.title || '(untitled)';
        const replies = t?.replyCount || 0;
        const agent = t?.agentName || 'anon';
        const threadId = (t?.id !== undefined && t?.id !== null) ? String(t.id) : '?';
        console.log(`  ${title}`);
        console.log(`    by ${agent} | ${replies} replies | id:${threadId.slice(0, 8)}\n`);
      });
    } else if (options.platform === 'youtube') {
      const videos = await client.discoverYouTube({
        query: options.query,
        limit,
      });
      console.log('\n🎬 YouTube Videos:\n');
      videos.forEach((v) => {
        console.log(`  ${v.title}`);
        console.log(`    by ${v.channelTitle} | ${v.url}\n`);
      });
    } else if (options.platform === 'thecolony') {
      const posts = await client.discoverColony({ limit });
      console.log('\n🏛️ The Colony Posts:\n');
      posts.forEach((p: any) => {
        const author = typeof p.author === 'object'
          ? (p.author?.display_name || p.author?.username || '?')
          : (p.author || '?');
        console.log(`  ${p.title || '(untitled)'}`);
        console.log(`    [${p.post_type || 'post'}] by ${author} | ${p.comment_count || 0} comments\n`);
      });
    } else if (options.platform === 'moltx') {
      const posts = await client.discoverMoltX(limit);
      console.log('\n⚡ MoltX Posts:\n');
      posts.forEach((p: any) => {
        const content = (p.content || '').slice(0, 80);
        console.log(`  ${content}${content.length >= 80 ? '...' : ''}`);
        console.log(`    by ${p.author_display_name || '?'} | ${p.like_count || 0} likes | ${p.reply_count || 0} replies\n`);
      });
    } else if (options.platform === 'moltexchange') {
      const questions = await client.discoverMoltExchange(limit);
      console.log('\n❓ MoltExchange Questions:\n');
      questions.forEach((q: any) => {
        console.log(`  ${q.title || '(untitled)'}`);
        console.log(`    by ${q.author || '?'} | ${q.answer_count || 0} answers\n`);
      });
    } else if (options.platform === 'all') {
      const all = await client.discoverAll();
      console.log('\n🌐 All Platforms:\n');
      console.log(`  BoTTube: ${all.bottube.length} videos`);
      console.log(`  Moltbook: ${all.moltbook.length} posts`);
      console.log(`  ClawCities: ${all.clawcities.length} sites`);
      console.log(`  Clawsta: ${all.clawsta.length} posts`);
      console.log(`  4claw: ${all.fourclaw.length} threads`);
      console.log(`  The Colony: ${all.thecolony.length} posts`);
      console.log(`  MoltX: ${all.moltx.length} posts`);
      console.log(`  MoltExchange: ${all.moltexchange.length} questions\n`);
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
  .requiredOption('-p, --platform <platform>', 'Platform: clawcities, clawsta, fourclaw, thecolony, moltexchange')
  .option('-t, --target <target>', 'Target: site name, post/thread ID')
  .requiredOption('-m, --message <message>', 'Comment message')
  .action(async (options) => {
    const config = loadConfig();
    const client = new GrazerClient({
      moltbook: config.moltbook?.api_key,
      clawcities: config.clawcities?.api_key,
      clawsta: config.clawsta?.api_key,
      fourclaw: config.fourclaw?.api_key,
      youtube: config.youtube?.api_key,
      thecolony: config.thecolony?.api_key,
      moltexchange: config.moltexchange?.api_key,
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
    } else if (options.platform === 'thecolony') {
      if (!options.target) {
        console.error('Error: --target post_id required for Colony replies');
        process.exit(1);
      }
      const result = await client.replyColony(options.target, options.message);
      console.log('\n✓ Reply posted to Colony post', options.target);
      console.log('  ID:', result.id || 'ok');
    } else if (options.platform === 'moltexchange') {
      if (!options.target) {
        console.error('Error: --target question_id required for MoltExchange answers');
        process.exit(1);
      }
      const result = await client.answerMoltExchange(options.target, options.message);
      console.log('\n✓ Answer posted to MoltExchange question', options.target);
      console.log('  ID:', result.id || 'ok');
    }
  });

program
  .command('post')
  .description('Create a new post or thread')
  .requiredOption('-p, --platform <platform>', 'Platform: fourclaw, moltbook, thecolony, moltx, moltexchange')
  .option('-b, --board <board>', 'Board/submolt name')
  .requiredOption('-t, --title <title>', 'Post/thread title')
  .requiredOption('-m, --message <message>', 'Post content')
  .action(async (options) => {
    const config = loadConfig();
    const client = new GrazerClient({
      moltbook: config.moltbook?.api_key,
      fourclaw: config.fourclaw?.api_key,
      youtube: config.youtube?.api_key,
      thecolony: config.thecolony?.api_key,
      moltx: config.moltx?.api_key,
      moltexchange: config.moltexchange?.api_key,
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
    } else if (options.platform === 'thecolony') {
      const result = await client.postColony(options.title, options.message);
      console.log('\n✓ Posted to The Colony');
      console.log(`  ID: ${result.id || 'ok'}`);
    } else if (options.platform === 'moltx') {
      const result = await client.postMoltX(options.message);
      console.log('\n✓ Posted to MoltX');
      console.log(`  ID: ${result.id || 'ok'}`);
    } else if (options.platform === 'moltexchange') {
      const result = await client.postMoltExchange(options.title, options.message);
      console.log('\n✓ Question posted to MoltExchange');
      console.log(`  ID: ${result.id || 'ok'}`);
    }
  });

// ── ClawHub commands ──

function formatSkillRow(skill: ClawHubSkill): string {
  const tags = skill.tags.length > 0 ? skill.tags.join(', ') : '-';
  const repo = skill.github_repo || '-';
  return `  ${skill.name}\n    by ${skill.author} | ${skill.downloads} downloads | tags: ${tags}\n    repo: ${repo}\n`;
}

const clawhub = program
  .command('clawhub')
  .description('Discover skills on ClawHub');

clawhub
  .command('trending')
  .description('List trending skills on ClawHub')
  .option('-l, --limit <limit>', 'Number of results', '20')
  .option('--json', 'Output as JSON')
  .action(async (options) => {
    const config = loadConfig();
    const token = config.clawhub?.token;
    const client = new ClawHubClient(token);
    const limit = parseInt(options.limit);

    const skills = await client.getTrendingSkills(limit);

    if (options.json) {
      console.log(JSON.stringify(skills, null, 2));
      return;
    }

    console.log(`\n🔧 ClawHub Trending Skills (${skills.length}):\n`);
    skills.forEach((s) => console.log(formatSkillRow(s)));
  });

clawhub
  .command('search <query>')
  .description('Search for skills on ClawHub')
  .option('-l, --limit <limit>', 'Number of results', '20')
  .option('--json', 'Output as JSON')
  .action(async (query: string, options) => {
    const config = loadConfig();
    const token = config.clawhub?.token;
    const client = new ClawHubClient(token);
    const limit = parseInt(options.limit);

    const skills = await client.searchSkills(query, limit);

    if (options.json) {
      console.log(JSON.stringify(skills, null, 2));
      return;
    }

    console.log(`\n🔍 ClawHub Search: "${query}" (${skills.length} results):\n`);
    if (skills.length === 0) {
      console.log('  No skills found.\n');
    } else {
      skills.forEach((s) => console.log(formatSkillRow(s)));
    }
  });

program.parse();
