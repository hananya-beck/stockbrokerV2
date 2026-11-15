#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { execSync } from 'node:child_process';

const input = JSON.parse(readFileSync(0, 'utf8'));
const cwd = process.env.CLAUDE_PROJECT_DIR || input.cwd || process.cwd();

// stop_hook_active means this Stop event is already a retry this hook
// triggered. Block once; on the retry, let the turn end regardless of the
// check's state, so an unfixable red doesn't trap the session in a loop.
// (Claude Code's own 8-consecutive-block cap is a last resort, not a plan.)
if (input.stop_hook_active) {
  process.exit(0);
}

try {
  execSync('npm run check', { cwd, stdio: 'pipe' });
  process.exit(0);
} catch (err) {
  const output = `${err.stdout ?? ''}${err.stderr ?? ''}`.trim();
  console.error(`BLOCKED by stop-gate hook: npm run check is red — fix it before ending the turn.\n\n${output.slice(-4000)}`);
  process.exit(2);
}
