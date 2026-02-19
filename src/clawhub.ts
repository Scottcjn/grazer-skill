/**
 * ClawHub Integration - Skill Registry with Vector Search
 * Uses clawdhub CLI for reliability
 */

import { execSync } from 'child_process';

export interface ClawHubSkill {
  id: string;
  name: string;
  description: string;
  author: string;
  version: string;
  downloads: number;
  tags: string[];
  platforms: string[];
  npm_package?: string;
  pypi_package?: string;
  github_repo?: string;
}

interface ClawHubCLIResult {
  name: string;
  description: string;
  author: string;
  version: string;
  downloads: number;
  tags: string[];
  platforms: string[];
  npm_package?: string;
  github_repo?: string;
}

function parseSkillLine(line: string): ClawHubCLIResult | null {
  // Parse lines like: "skill-name v1.0.0  time  Description"
  // or: "skill-name v1.0.0  Description (by author, 1.2k downloads)"
  let match = line.match(/^([^\s]+)\s+v?([^\s]+)\s+(.+?)\s+\(by\s+([^,]+),\s*([\d.]+[km]?)\s*downloads?\)/i);
  if (match) {
    const [, name, version, description, author, downloadsStr] = match;
    let downloads = 0;
    if (downloadsStr.endsWith('k')) {
      downloads = Math.round(parseFloat(downloadsStr) * 1000);
    } else if (downloadsStr.endsWith('m')) {
      downloads = Math.round(parseFloat(downloadsStr) * 1000000);
    } else {
      downloads = parseInt(downloadsStr) || 0;
    }
    return { name, version, description: description.trim(), author: author.trim(), downloads, tags: [], platforms: [] };
  }

  // Parse explore output: "name v1.0.0  time  Description"
  match = line.match(/^([^\s]+)\s+v?([^\s]+)\s+(\S+)\s+(.+)$/);
  if (match) {
    const [, name, version, , description] = match;
    return {
      name,
      version,
      description: description.trim(),
      author: 'unknown',
      downloads: 0,
      tags: [],
      platforms: [],
    };
  }

  return null;
}

export class ClawHubClient {
  private token?: string;

  constructor(token?: string) {
    this.token = token;
  }

  /**
   * Get trending skills using clawdhub CLI
   */
  async getTrendingSkills(limit = 20): Promise<ClawHubSkill[]> {
    try {
      const output = execSync(`clawdhub explore --limit ${limit} --sort trending`, {
        encoding: 'utf-8',
        timeout: 30000,
      });

      const skills: ClawHubSkill[] = [];
      const lines = output.split('\n').filter(l => l.trim());

      for (const line of lines) {
        const skill = parseSkillLine(line);
        if (skill) {
          skills.push(skill as ClawHubSkill);
        }
      }

      return skills.slice(0, limit);
    } catch (err: any) {
      throw new Error(`Failed to fetch trending skills: ${err.message}`);
    }
  }

  /**
   * Search skills using clawdhub CLI
   */
  async searchSkills(query: string, limit = 20): Promise<ClawHubSkill[]> {
    try {
      const output = execSync(`clawdhub search "${query}" --limit ${limit}`, {
        encoding: 'utf-8',
        timeout: 30000,
      });

      const skills: ClawHubSkill[] = [];
      const lines = output.split('\n').filter(l => l.trim());

      for (const line of lines) {
        const skill = parseSkillLine(line);
        if (skill) {
          skills.push(skill as ClawHubSkill);
        }
      }

      return skills.slice(0, limit);
    } catch (err: any) {
      throw new Error(`Failed to search skills: ${err.message}`);
    }
  }

  /**
   * Get skill by ID (not implemented via CLI)
   */
  async getSkill(skillId: string): Promise<ClawHubSkill> {
    throw new Error('getSkill not implemented - use search instead');
  }

  /**
   * Publish skill to ClawHub (requires token)
   */
  async publishSkill(skill: {
    name: string;
    description: string;
    version: string;
    tags: string[];
    platforms: string[];
    npm_package?: string;
    pypi_package?: string;
    github_repo?: string;
  }): Promise<ClawHubSkill> {
    throw new Error('Use clawdhub CLI to publish: clawdhub publish');
  }

  /**
   * Update skill metadata (not implemented via CLI)
   */
  async updateSkill(skillId: string, updates: Partial<ClawHubSkill>): Promise<ClawHubSkill> {
    throw new Error('Use clawdhub CLI to update');
  }

  /**
   * Record download/install (not implemented via CLI)
   */
  async recordInstall(skillId: string, platform: 'npm' | 'pypi'): Promise<void> {
    // Silent - CLI handles this
  }
}

export default ClawHubClient;
