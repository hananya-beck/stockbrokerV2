#!/usr/bin/env node
import { readFileSync } from 'node:fs';

const input = JSON.parse(readFileSync(0, 'utf8'));
const filePath = (input?.tool_input?.file_path ?? '').replace(/\\/g, '/');

const RULES = [
  {
    test: (p) => /(^|\/)\.env([./]|$)/.test(p),
    reason: '.env files hold the GitHub token the refresh button uses at runtime — never committed, never written by the agent (AGENTS.md policy: no secrets in the repo).',
  },
  {
    test: (p) => p.endsWith('.claude/settings.json'),
    reason: '.claude/settings.json wires the hooks and permissions this harness depends on — edit it yourself, not through the agent.',
  },
  {
    test: (p) => /(^|\/)data\/(funds|nav-history)\.json$/.test(p),
    reason: 'data/funds.json and data/nav-history.json are generated daily by update-data.yml — a hand edit gets overwritten and can desync the dashboard (AGENTS.md policy).',
  },
];

for (const rule of RULES) {
  if (rule.test(filePath)) {
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: rule.reason,
      },
    }));
    process.exit(0);
  }
}

process.exit(0);
