export interface OpportunityAssessment {
  score: number;
  signals: string[];
}

export type RankedOpportunity<T> = T & {
  _opportunity_score: number;
  _opportunity_signals: string[];
};

const SIGNALS: Array<[string, number, RegExp]> = [
  ['bounty', 8, /\bbount(?:y|ies)\b/i],
  ['reward', 6, /\brewards?\b/i],
  ['paid', 6, /\bpaid\b|\bpaying\b/i],
  ['payout', 5, /\bpayouts?\b/i],
  ['hiring', 5, /\bhiring\b|\bwe(?:'re| are) hiring\b/i],
  ['commission', 5, /\bcommissions?\b/i],
  ['grant', 4, /\bgrants?\b/i],
  ['prize', 4, /\bprizes?\b/i],
  ['compensation', 4, /\bcompensat(?:e|ed|ion)\b|\bstipends?\b/i],
  ['freelance', 4, /\bfreelance\b|\bcontract work\b/i],
];

const AMOUNT = /(?:\$\s*\d+(?:[.,]\d+)?|\b\d+(?:[.,]\d+)?\s*(?:USD|USDC|RTC|XLM|EUR|GBP)\b)/i;
const NOISE = [
  /\b(?:cron|scheduled|background) (?:job|task)s?\b/i,
  /\b(?:job|task|worker) queues?\b|\bqueue(?:d|ing)? (?:job|task)s?\b/i,
  /\b(?:job|task) runners?\b/i,
  /\b(?:job|task) orchestration\b|\borchestrat(?:e|ing) (?:jobs|tasks)\b/i,
  /\b(?:async|celery) tasks?\b/i,
];

function postText(post: Record<string, any>): string {
  const parts: string[] = [];
  for (const key of ['title', 'content', 'body', 'description', 'text']) {
    if (post[key] !== undefined && post[key] !== null) parts.push(String(post[key]));
  }
  if (Array.isArray(post.tags)) parts.push(...post.tags.map(String));
  else if (post.tags) parts.push(String(post.tags));
  return parts.join('\n');
}

export function scoreMoltbookOpportunity(post: Record<string, any>): OpportunityAssessment {
  const text = postText(post);
  let score = 0;
  const signals: string[] = [];

  for (const [label, weight, pattern] of SIGNALS) {
    if (pattern.test(text)) {
      score += weight;
      signals.push(label);
    }
  }
  if (AMOUNT.test(text)) {
    score += 5;
    signals.push('amount');
  }

  // Generic job/task language is deliberately too weak to pass alone.
  if (/\bjobs?\b/i.test(text)) score += 1;
  if (/\btasks?\b/i.test(text)) score += 1;
  for (const pattern of NOISE) {
    if (pattern.test(text)) score -= 4;
  }
  return { score, signals };
}

export function rankMoltbookOpportunities<T extends Record<string, any>>(
  posts: T[],
  limit = 20,
  minScore = 3,
): Array<RankedOpportunity<T>> {
  return posts
    .map((post, index) => {
      const assessment = scoreMoltbookOpportunity(post);
      const upvotes = Number(post.upvotes || 0) || 0;
      return { post, index, upvotes, ...assessment };
    })
    .filter((item) => item.score >= minScore)
    .sort((a, b) => b.score - a.score || b.upvotes - a.upvotes || a.index - b.index)
    .slice(0, Math.max(0, limit))
    .map((item) => ({
      ...item.post,
      _opportunity_score: item.score,
      _opportunity_signals: item.signals,
    }));
}
