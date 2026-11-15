#!/usr/bin/env node
import { appendFileSync, mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

// Audit only — never block, never throw. Any failure here must not stop the
// agent's turn, so every path below ends in process.exit(0).
try {
  const raw = readFileSync(0, 'utf8');
  const input = JSON.parse(raw);
  const cwd = process.env.CLAUDE_PROJECT_DIR || input.cwd || process.cwd();

  const target = (() => {
    const t = input.tool_input;
    if (!t) return undefined;
    if (typeof t.command === 'string') return t.command;
    if (typeof t.file_path === 'string') return t.file_path;
    return undefined;
  })();

  const entry = {
    ts: new Date().toISOString(),
    session_id: input.session_id,
    event: input.hook_event_name,
    tool: input.tool_name,
    target,
  };

  const logDir = join(cwd, 'logs');
  mkdirSync(logDir, { recursive: true });
  appendFileSync(join(logDir, 'agent-audit.jsonl'), `${JSON.stringify(entry)}\n`);
} catch {
  // Broken stdin, unwritable log, anything — still never block.
}

process.exit(0);
