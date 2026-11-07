// Needs only Node 18+ (already required by `npm run check`); no npm install.
// Run from the repo root, the directory being audited: node <plugin>/skills/policy-audit/scripts/audit.mjs
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { pathToFileURL } from 'node:url';

const ROOT = process.cwd();
const SKIP_DIRS = new Set(['.git', 'node_modules', '_bmad', '_bmad-output']);

const walk = dir =>
  readdirSync(dir).flatMap(name => {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) return SKIP_DIRS.has(name) ? [] : walk(full);
    return [full];
  });

const rel = f => relative(ROOT, f).split(sep).join('/');

// Comments routinely name the banned APIs ("no localStorage"), so they must not count.
const isComment = line => /^\s*(\/\/|\*|\/\*|<!--|#)/.test(line);

const scan = (files, regex) =>
  files.flatMap(f =>
    readFileSync(f, 'utf8')
      .split('\n')
      .map((line, i) => ({ line, at: `${rel(f)}:${i + 1}` }))
      .filter(({ line }) => !isComment(line) && regex.test(line))
      .map(({ line, at }) => `${at}  ${line.trim().slice(0, 120)}`)
  );

const all = walk(ROOT);
const front = all.filter(f => /^(index\.html|src\/)/.test(rel(f)) && /\.(html|js|css)$/.test(f));
const lib = all.filter(f => rel(f).startsWith('src/lib/') && f.endsWith('.js'));
const styled = front.filter(f => !rel(f).endsWith('tokens.css'));
const text = all.filter(f => /\.(html|js|mjs|css|json|md|py|yml|yaml)$/.test(f));

const i18nParity = async () => {
  const { STRINGS } = await import(pathToFileURL(join(ROOT, 'src/lib/i18n.js')).href);
  const he = Object.keys(STRINGS.he), en = Object.keys(STRINGS.en);
  return [
    ...he.filter(k => !en.includes(k)).map(k => `STRINGS.en is missing "${k}"`),
    ...en.filter(k => !he.includes(k)).map(k => `STRINGS.he is missing "${k}"`),
  ];
};

const checks = [
  ['P1 browser storage', () => scan(front, /\b(localStorage|sessionStorage|indexedDB|document\.cookie)\b/)],
  ['P2 leading-slash paths', () => scan(front, /(\b(src|href)\s*=\s*|\bimport\b[^'"]*|\bfetch\(\s*)["'`]\/(?!\/)/)],
  ['P3 browser APIs in src/lib', () => scan(lib, /\b(fetch|document|window|navigator|setTimeout|setInterval|Date\.now|Math\.random)\b/)],
  ['P4 hard-coded colors', () => scan(styled, /#[0-9a-fA-F]{3,8}\b(?![-\w])|\b(rgb|rgba|hsl|hsla)\(/)],
  ['P5 committed tokens', () => scan(text, /\b(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})/)],
  ['P6 i18n he/en parity', i18nParity],
];

const results = [];
for (const [name, run] of checks) results.push([name, await run()]);

results.forEach(([name, hits]) => {
  console.log(`${hits.length ? 'FAIL' : 'PASS'}  ${name}`);
  hits.forEach(h => console.log(`      ${h}`));
});

const failed = results.filter(([, hits]) => hits.length).length;
console.log(failed ? `\n${failed} check(s) failed` : '\nAll policy checks passed');
process.exit(failed ? 1 : 0);
