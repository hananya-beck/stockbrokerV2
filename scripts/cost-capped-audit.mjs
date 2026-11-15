#!/usr/bin/env node
// Runs a headless, read-only Claude Code audit of this repo, four rails enforced:
// read-only tool surface, a turn limit, a dollar cap, machine-readable output.
import { execFileSync } from 'node:child_process';
import { execSync } from 'node:child_process';

const DEFAULT_PROMPT =
  'Audit this repo against AGENTS.md. List any policy violations you find, ' +
  'each with its file and line number. If you find none, say so.';

function parseArgs(argv) {
  const args = { prompt: DEFAULT_PROMPT, maxTurns: 6, maxBudgetUsd: 2.0 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--prompt') args.prompt = argv[++i];
    else if (a === '--max-turns') args.maxTurns = Number(argv[++i]);
    else if (a === '--max-budget-usd') args.maxBudgetUsd = Number(argv[++i]);
    else if (a === '--model') args.model = argv[++i];
    else if (a === '--effort') args.effort = argv[++i];
  }
  return args;
}

// Proof the agent could not have edited a file: the working tree's status
// before and after the run must be byte-identical, not just "looks clean".
function gitStatus() {
  return execSync('git status --porcelain=v1', { encoding: 'utf8' });
}

function runAudit({ prompt, maxTurns, maxBudgetUsd, model, effort }) {
  const cliArgs = [
    '-p', prompt,
    '--tools', 'Read,Grep,Glob',
    '--disallowedTools', 'Edit', 'Write', 'NotebookEdit', 'Bash',
    '--permission-mode', 'dontAsk',
    '--max-turns', String(maxTurns),
    '--max-budget-usd', String(maxBudgetUsd),
    '--output-format', 'json',
  ];
  if (model) cliArgs.push('--model', model);
  if (effort) cliArgs.push('--effort', effort);

  const before = gitStatus();
  // claude exits non-zero on a hit rail (max-turns, max-budget-usd) even though
  // stdout is still valid result JSON — that JSON is what we actually want.
  let raw;
  try {
    raw = execFileSync('claude', cliArgs, { encoding: 'utf8', maxBuffer: 10 * 1024 * 1024 });
  } catch (err) {
    raw = err.stdout;
  }
  const after = gitStatus();

  const result = JSON.parse(raw);
  return {
    cost_usd: result.total_cost_usd,
    turns: result.num_turns,
    terminal_reason: result.terminal_reason,
    is_error: result.is_error,
    errors: result.errors ?? [],
    result: result.result ?? null,
    tree_unchanged: before === after,
    tree_status_before: before,
    tree_status_after: after,
  };
}

const args = parseArgs(process.argv.slice(2));
const report = runAudit(args);
console.log(JSON.stringify(report, null, 2));

if (!report.tree_unchanged) {
  console.error('cost-capped-audit: working tree changed during a read-only run — this should never happen.');
  process.exit(1);
}
process.exit(report.is_error ? 1 : 0);
