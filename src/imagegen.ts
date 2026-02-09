/**
 * Grazer ImageGen - SVG generation for 4claw posts
 *
 * Supports:
 *   1. LLM-based: Any OpenAI-compatible API generates SVG from text prompts
 *   2. Template-based: Pre-built SVG templates (no external dependencies)
 *
 * 4claw constraints: SVG only, max 4KB, raw markup, max 1 per post.
 */

import axios from 'axios';
import { createHash } from 'crypto';

const SVG_MAX_BYTES = 4096;
const SVG_NS = 'xmlns="http://www.w3.org/2000/svg"';

// ─────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────

export interface ImageGenResult {
  svg: string;
  method: 'llm' | 'template';
  bytes: number;
}

export interface FourclawMedia {
  type: 'svg';
  data: string;
  generated: boolean;
  nsfw: boolean;
}

export interface ImageGenConfig {
  llmUrl?: string;
  llmModel?: string;
  llmApiKey?: string;
}

type TemplateFn = (title: string, colors: string[]) => string;

// ─────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────

function truncate(text: string, maxlen: number): string {
  const safe = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
  return safe.length > maxlen ? safe.slice(0, maxlen - 1) + '~' : safe;
}

function hashSeed(text: string): number {
  const h = createHash('md5').update(text).digest('hex').slice(0, 8);
  return parseInt(h, 16);
}

// ─────────────────────────────────────────────────────────────
// Color Palettes
// ─────────────────────────────────────────────────────────────

const PALETTES: Record<string, string[]> = {
  tech:    ['#0d1117', '#58a6ff', '#c9d1d9'],
  crypto:  ['#1a1a2e', '#e94560', '#f5f5f5'],
  retro:   ['#2d1b69', '#ff6ec7', '#00ff9f'],
  nature:  ['#1b4332', '#52b788', '#d8f3dc'],
  dark:    ['#0a0a0a', '#bb86fc', '#e0e0e0'],
  fire:    ['#1a0000', '#ff4500', '#ffd700'],
  ocean:   ['#0a1628', '#00bcd4', '#e0f7fa'],
  default: ['#1e1e2e', '#cba6f7', '#cdd6f4'],
};

// ─────────────────────────────────────────────────────────────
// SVG Templates
// ─────────────────────────────────────────────────────────────

const TEMPLATES: Record<string, TemplateFn> = {
  circuit: (title, c) =>
    `<svg ${SVG_NS} viewBox="0 0 200 200" width="200" height="200">` +
    `<rect width="200" height="200" fill="${c[0]}"/>` +
    `<g stroke="${c[1]}" stroke-width="1.5" fill="none" opacity="0.6">` +
    `<path d="M20,100 H80 L100,80 H180"/><path d="M20,60 H60 L80,40 H140 L160,60 H180"/>` +
    `<path d="M20,140 H50 L70,160 H120 L140,140 H180"/><path d="M100,20 V60 L120,80 V140 L100,160 V180"/>` +
    `</g><g fill="${c[1]}"><circle cx="80" cy="100" r="3"/><circle cx="100" cy="80" r="3"/>` +
    `<circle cx="140" cy="60" r="3"/><circle cx="120" cy="80" r="3"/><circle cx="100" cy="160" r="3"/></g>` +
    `<text x="100" y="105" text-anchor="middle" fill="${c[2]}" font-family="monospace" font-size="11">${truncate(title, 20)}</text></svg>`,

  wave: (title, c) =>
    `<svg ${SVG_NS} viewBox="0 0 200 120" width="200" height="120">` +
    `<defs><linearGradient id="wg" x1="0" y1="0" x2="1" y2="1">` +
    `<stop offset="0%" stop-color="${c[0]}"/><stop offset="100%" stop-color="${c[1]}"/></linearGradient></defs>` +
    `<rect width="200" height="120" fill="url(#wg)"/>` +
    `<path d="M0,80 Q50,40 100,80 T200,80 V120 H0Z" fill="${c[2]}" opacity="0.3"/>` +
    `<path d="M0,90 Q50,60 100,90 T200,90 V120 H0Z" fill="${c[2]}" opacity="0.2"/>` +
    `<text x="100" y="55" text-anchor="middle" fill="#fff" font-family="sans-serif" font-size="13" font-weight="bold">${truncate(title, 22)}</text></svg>`,

  grid: (title, c) => {
    const hLines = Array.from({ length: 11 }, (_, i) =>
      `<line x1="0" y1="${i * 20}" x2="200" y2="${i * 20}"/>`).join('');
    const vLines = Array.from({ length: 11 }, (_, i) =>
      `<line x1="${i * 20}" y1="0" x2="${i * 20}" y2="200"/>`).join('');
    return `<svg ${SVG_NS} viewBox="0 0 200 200" width="200" height="200">` +
      `<rect width="200" height="200" fill="${c[0]}"/>` +
      `<g stroke="${c[1]}" stroke-width="0.5" opacity="0.15">${hLines}${vLines}</g>` +
      `<circle cx="100" cy="90" r="35" fill="none" stroke="${c[2]}" stroke-width="2"/>` +
      `<circle cx="100" cy="90" r="20" fill="${c[2]}" opacity="0.3"/>` +
      `<text x="100" y="150" text-anchor="middle" fill="${c[2]}" font-family="monospace" font-size="11">${truncate(title, 22)}</text></svg>`;
  },

  badge: (title, c) =>
    `<svg ${SVG_NS} viewBox="0 0 200 60" width="200" height="60">` +
    `<rect width="200" height="60" rx="8" fill="${c[0]}"/>` +
    `<rect x="2" y="2" width="196" height="56" rx="6" fill="none" stroke="${c[1]}" stroke-width="1" opacity="0.4"/>` +
    `<text x="100" y="36" text-anchor="middle" fill="${c[2]}" font-family="sans-serif" font-size="14" font-weight="bold">${truncate(title, 24)}</text></svg>`,

  terminal: (title, c) =>
    `<svg ${SVG_NS} viewBox="0 0 220 130" width="220" height="130">` +
    `<rect width="220" height="130" rx="6" fill="#1a1a2e"/>` +
    `<rect x="0" y="0" width="220" height="24" rx="6" fill="#16213e"/>` +
    `<circle cx="14" cy="12" r="5" fill="#e94560"/><circle cx="30" cy="12" r="5" fill="#f5a623"/><circle cx="46" cy="12" r="5" fill="#7ec850"/>` +
    `<text x="10" y="50" fill="#0f3" font-family="monospace" font-size="11">$ grazer discover</text>` +
    `<text x="10" y="68" fill="#0f3" font-family="monospace" font-size="10" opacity="0.7">&gt; ${truncate(title, 26)}</text>` +
    `<rect x="10" y="80" width="8" height="14" fill="#0f3" opacity="0.8">` +
    `<animate attributeName="opacity" values="0.8;0.2;0.8" dur="1.2s" repeatCount="indefinite"/></rect></svg>`,
};

// ─────────────────────────────────────────────────────────────
// Pickers
// ─────────────────────────────────────────────────────────────

function pickTemplate(prompt: string): string {
  const lower = prompt.toLowerCase();
  if (['code', 'terminal', 'cli', 'shell', 'hack', 'dev'].some(w => lower.includes(w))) return 'terminal';
  if (['crypto', 'blockchain', 'token', 'mining', 'defi'].some(w => lower.includes(w))) return 'circuit';
  if (['badge', 'label', 'tag', 'status'].some(w => lower.includes(w))) return 'badge';
  if (['wave', 'music', 'audio', 'vibe', 'chill'].some(w => lower.includes(w))) return 'wave';
  const names = Object.keys(TEMPLATES);
  return names[hashSeed(prompt) % names.length];
}

function pickPalette(prompt: string): string[] {
  const lower = prompt.toLowerCase();
  for (const key of Object.keys(PALETTES)) {
    if (lower.includes(key)) return PALETTES[key];
  }
  const keys = Object.keys(PALETTES);
  return PALETTES[keys[hashSeed(prompt) % keys.length]];
}

function validateSvg(svg: string): string {
  svg = svg.trim();
  if (!svg.startsWith('<svg')) throw new Error('Generated content is not valid SVG');
  if (!svg.includes('xmlns=')) svg = svg.replace('<svg', `<svg ${SVG_NS}`);
  const bytes = Buffer.byteLength(svg, 'utf-8');
  if (bytes > SVG_MAX_BYTES) throw new Error(`SVG exceeds 4KB limit (${bytes} bytes)`);
  return svg;
}

// ─────────────────────────────────────────────────────────────
// Generators
// ─────────────────────────────────────────────────────────────

const LLM_SVG_SYSTEM_PROMPT = `You are an SVG artist. Generate a single SVG image based on the user's prompt.

STRICT RULES:
- Output ONLY the raw <svg>...</svg> markup. No markdown, no explanation, no code fences.
- Must include xmlns="http://www.w3.org/2000/svg"
- Total SVG must be under 3800 bytes (leave room for wrapper)
- Use viewBox, keep dimensions reasonable (200x200 or similar)
- Use only generic fonts: sans-serif, serif, monospace
- You may use gradients, animations (<animate>, <animateTransform>), and filters
- Make it visually interesting and relevant to the prompt
- Prefer geometric/abstract art that looks good at small sizes`;

export function generateTemplateSvg(
  prompt: string,
  template?: string,
  palette?: string
): string {
  const tplName = template && TEMPLATES[template] ? template : pickTemplate(prompt);
  const colors = palette && PALETTES[palette] ? PALETTES[palette] : pickPalette(prompt);
  return validateSvg(TEMPLATES[tplName](prompt, colors));
}

export async function generateLlmSvg(
  prompt: string,
  llmUrl: string,
  llmModel = 'gpt-oss-120b',
  llmApiKey?: string,
  temperature = 0.8,
  timeout = 60000
): Promise<string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (llmApiKey) headers['Authorization'] = `Bearer ${llmApiKey}`;

  const resp = await axios.post(llmUrl, {
    model: llmModel,
    messages: [
      { role: 'system', content: LLM_SVG_SYSTEM_PROMPT },
      { role: 'user', content: `Create an SVG image: ${prompt}` },
    ],
    temperature,
    max_tokens: 2048,
  }, { headers, timeout });

  const content: string = resp.data.choices[0].message.content.trim();
  const match = content.match(/<svg[\s\S]*?<\/svg>/);
  if (!match) throw new Error('LLM did not produce valid SVG output');

  return validateSvg(match[0]);
}

export async function generateSvg(
  prompt: string,
  options: {
    llmUrl?: string;
    llmModel?: string;
    llmApiKey?: string;
    template?: string;
    palette?: string;
    preferLlm?: boolean;
  } = {}
): Promise<ImageGenResult> {
  const { llmUrl, llmModel, llmApiKey, template, palette, preferLlm = true } = options;

  // Try LLM first
  if (preferLlm && llmUrl) {
    try {
      const svg = await generateLlmSvg(prompt, llmUrl, llmModel, llmApiKey);
      return { svg, method: 'llm', bytes: Buffer.byteLength(svg, 'utf-8') };
    } catch {
      // Fall through to template
    }
  }

  // Fallback to template
  const svg = generateTemplateSvg(prompt, template, palette);
  return { svg, method: 'template', bytes: Buffer.byteLength(svg, 'utf-8') };
}

export function svgToMedia(svg: string): FourclawMedia[] {
  return [{ type: 'svg', data: svg, generated: true, nsfw: false }];
}
