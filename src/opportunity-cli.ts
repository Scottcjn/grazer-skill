#!/usr/bin/env node
/** Compatibility entry point for opportunity-focused Moltbook discovery. */

import { GrazerClient } from './index';
import { rankMoltbookOpportunities } from './opportunities';

const args = process.argv.slice(2);
const intentIndex = args.indexOf("--intent");
const opportunityMode =
  args.includes("--bounties-only") ||
  args.includes("--intent=opportunities") ||
  (intentIndex >= 0 && args[intentIndex + 1] === "opportunities");

function cleanedArgv(): string[] {
  const clean = [process.argv[0], process.argv[1]];
  for (let index = 0; index < args.length; index += 1) {
    const value = args[index];
    if (value === "--bounties-only" || value === "--intent=opportunities") continue;
    if (value === "--intent" && args[index + 1] === "opportunities") {
      index += 1;
      continue;
    }
    clean.push(value);
  }
  return clean;
}

if (opportunityMode) {
  if (args[0] !== "discover") throw new Error("opportunity mode is only valid with grazer discover");
  const hasMoltbook = args.some((value, index) =>
    value === "--platform=moltbook" ||
    value === "-p=moltbook" ||
    ((value === "--platform" || value === "-p") && args[index + 1] === "moltbook")
  );
  if (!hasMoltbook) throw new Error("opportunity mode currently requires --platform moltbook");

  const original = GrazerClient.prototype.discoverMoltbook;
  GrazerClient.prototype.discoverMoltbook = async function(options) {
    const limit = options?.limit ?? 20;
    const fetchLimit = Math.min(Math.max(limit * 5, 50), 100);
    const posts = await original.call(this, { ...options, limit: fetchLimit });
    return rankMoltbookOpportunities(posts as any[], limit) as any;
  };
  process.argv = cleanedArgv();
}

require('./cli');
