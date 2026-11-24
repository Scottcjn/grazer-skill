// SPDX-License-Identifier: MIT
/**
 * Regression tests for src/notifications.ts endpoints and src/index.ts BoTTube/path-encoding fixes.
 * Run with: node --test tests-ts/
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
import { NotificationMonitor } from '../src/notifications.ts';

test('NotificationMonitor uses /api/v1/sites for ClawCities and clawsta.io for Clawsta', async () => {
  const seenUrls: string[] = [];
  const originalFetch = globalThis.fetch;

  (globalThis as any).fetch = async (url: string) => {
    seenUrls.push(String(url));
    return {
      ok: true,
      json: async () => [],
    };
  };

  try {
    const monitor = new NotificationMonitor('agent name');
    await monitor.checkNotifications({ clawcities: true, clawsta: true });
    assert.ok(
      seenUrls.includes('https://clawcities.com/api/v1/sites/agent%20name/guestbook?limit=10'),
      `unexpected URLs: ${JSON.stringify(seenUrls)}`
    );
    assert.ok(
      seenUrls.includes('https://clawsta.io/api/notifications?username=agent%20name&limit=10'),
      `unexpected URLs: ${JSON.stringify(seenUrls)}`
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('GrazerClient uses live BoTTube search/stream paths and encodes path segments safely', async () => {
  const calls: Array<{ method: string; url: string; opts?: any }> = [];

  const mockHttp: any = Object.assign(async (_cfg: any) => ({ data: {} }), {
    interceptors: { response: { use: () => {} } },
    get: async (url: string, opts?: any) => {
      calls.push({ method: 'GET', url, opts });
      if (url === 'https://bottube.ai/api/videos') {
        return {
          data: {
            videos: [{ id: 4538, video_id: 'ZJnWJ5cpbtK', title: 'Clip' }],
          },
        };
      }
      if (url === 'https://bottube.ai/api/search') {
        return { data: { videos: [{ id: 'v1', title: 'Search Hit' }] } };
      }
      return { data: {} };
    },
    post: async (url: string, body?: any, opts?: any) => {
      calls.push({ method: 'POST', url, opts: { body, opts } });
      return { data: { ok: true, access_token: 'tok' } };
    },
  });

  (globalThis as any).__grazerMockAxios = {
    default: { create: () => mockHttp },
  };

  const hook = registerHooks({
    resolve(specifier, context, nextResolve) {
      if (specifier === 'axios') {
        return { shortCircuit: true, url: 'grazer-test://axios' };
      }
      if (context.parentURL?.includes('src/index.ts') && specifier === './imagegen') {
        return { shortCircuit: true, url: 'grazer-test://imagegen' };
      }
      if (context.parentURL?.includes('src/index.ts') && specifier === './youtube') {
        return { shortCircuit: true, url: 'grazer-test://youtube' };
      }
      return nextResolve(specifier, context);
    },
    load(url, context, nextLoad) {
      if (url === 'grazer-test://axios') {
        return {
          shortCircuit: true,
          format: 'module',
          source: 'export const AxiosInstance = {}; export default globalThis.__grazerMockAxios.default;',
        };
      }
      if (url === 'grazer-test://imagegen') {
        return {
          shortCircuit: true,
          format: 'module',
          source:
            'export const generateSvg = async () => ({ svg: "" });' +
            'export const svgToMedia = () => ({});' +
            'export const generateTemplateSvg = () => "";' +
            'export const generateLlmSvg = async () => "";',
        };
      }
      if (url === 'grazer-test://youtube') {
        return {
          shortCircuit: true,
          format: 'module',
          source: 'export const YouTubeVideo = {}; export class YouTubeDiscovery { async discover(opts = {}) { return [{ opts }]; } }',
        };
      }
      return nextLoad(url, context);
    },
  });

  try {
    const mod = await import('../src/index.ts?mock=' + Date.now());
    const client = new mod.GrazerClient({
      clawcities: 'ckey',
      fourclaw: 'fkey',
      thecolony: 'tkey',
      moltexchange: 'mkey',
    });

    const videos = await client.discoverBottube();
    assert.equal(videos.length, 1);
    assert.equal(videos[0].stream_url, 'https://bottube.ai/api/videos/ZJnWJ5cpbtK/stream');

    const hits = await client.searchBottube('ai', 5);
    assert.equal(hits[0].title, 'Search Hit');
    assert.ok(calls.some((c) => c.method === 'GET' && c.url === 'https://bottube.ai/api/search'));

    const yt = await client.discoverYouTube();
    assert.equal(yt.length, 1);

    await client.discoverMoltbook();
    await client.commentClawCities('alice/../admin', 'hi');
    await client.getFourclawThread('tid?admin=1');
    await client.replyColony('pid#frag', 'reply');
    await client.answerMoltExchange('qid/extra', 'ans');

    const urls = calls.map((c) => c.url);
    assert.ok(urls.includes('https://clawcities.com/api/v1/sites/alice%2F..%2Fadmin/comments'));
    assert.ok(urls.includes('https://www.4claw.org/api/v1/threads/tid%3Fadmin%3D1'));
    assert.ok(urls.includes('https://thecolony.cc/api/v1/posts/pid%23frag/comments'));
    assert.ok(urls.includes('https://moltexchange.ai/v1/questions/qid%2Fextra/answers'));

    await assert.rejects(() => client.commentClawCities('..', 'x'), /must not be '\.' or '\.\.'/);
    await assert.rejects(() => client.getFourclawThread('   '), /must be a non-empty string/);
  } finally {
    hook.deregister();
    delete (globalThis as any).__grazerMockAxios;
  }
});
