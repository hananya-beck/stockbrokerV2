#!/usr/bin/env node
// Reads the statusLine JSON Claude Code pipes on stdin and prints one line.
let raw = '';
for await (const chunk of process.stdin) raw += chunk;

let input;
try {
  input = JSON.parse(raw);
} catch {
  console.log('statusline: unreadable input');
  process.exit(0);
}

const dir = (input.workspace?.current_dir ?? input.cwd ?? '').split(/[\\/]/).pop();
const model = input.model?.display_name ?? input.model?.id ?? 'model?';
const cost = input.cost?.total_cost_usd;
const costStr = typeof cost === 'number' ? `$${cost.toFixed(2)}` : '$?';
const ctxPct = input.context_window?.used_percentage;
const ctxStr = typeof ctxPct === 'number' ? ` · ctx ${Math.round(ctxPct)}%` : '';

console.log(`${dir} · ${model} · ${costStr}${ctxStr}`);
