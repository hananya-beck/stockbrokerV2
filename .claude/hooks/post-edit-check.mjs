#!/usr/bin/env node
import { readFileSync, existsSync } from 'node:fs';

const input = JSON.parse(readFileSync(0, 'utf8'));
const filePath = (input?.tool_input?.file_path ?? '').replace(/\\/g, '/');

// Check the path first: only src/lib/**/*.js carries the no-fetch/DOM/timers
// rule from src/lib/CLAUDE.md. Everything else returns in milliseconds.
if (!/(^|\/)src\/lib\/.*\.js$/.test(filePath) || !existsSync(filePath)) {
  process.exit(0);
}

const content = readFileSync(filePath, 'utf8');

const BANNED = [
  { pattern: /\bfetch\s*\(/, name: 'fetch(' },
  { pattern: /\bdocument\./, name: 'document.*' },
  { pattern: /\bwindow\./, name: 'window.*' },
  { pattern: /\blocalStorage\b/, name: 'localStorage' },
  { pattern: /\bsessionStorage\b/, name: 'sessionStorage' },
  { pattern: /\bsetTimeout\s*\(/, name: 'setTimeout(' },
  { pattern: /\bsetInterval\s*\(/, name: 'setInterval(' },
  { pattern: /\bDate\.now\s*\(/, name: 'Date.now()' },
  { pattern: /\bMath\.random\s*\(/, name: 'Math.random()' },
];

const findings = [];
content.split('\n').forEach((line, i) => {
  // Strip a trailing // comment first — prose that mentions a banned API
  // (e.g. a header explaining what this file must NOT do) isn't a violation.
  const code = line.replace(/\/\/.*/, '');
  for (const { pattern, name } of BANNED) {
    if (pattern.test(code)) {
      findings.push(`${filePath}:${i + 1}: src/lib/CLAUDE.md bans ${name} in src/lib (no fetch/DOM/timers/Date.now/Math.random — must stay pure and deterministic)`);
    }
  }
});

if (findings.length) {
  console.error(findings.join('\n'));
  process.exit(2);
}
process.exit(0);
