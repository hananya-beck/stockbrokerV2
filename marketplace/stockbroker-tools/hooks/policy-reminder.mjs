import { readFileSync } from 'node:fs';

const reminders = [
  [
    /(^|[\\/])data[\\/]funds\.json$/,
    'data/funds.json is written by the daily bot. Do not hand-edit it; regenerate locally with scripts/fetch_data.py and do not commit the result by hand.',
  ],
  [
    /(^|[\\/])(index\.html|src[\\/].*\.(js|html|css))$/,
    'Policy: no localStorage, sessionStorage or cookies; no leading-slash paths; no hard-coded colors (use tokens); UI text goes in both STRINGS.he and STRINGS.en. Run the policy-audit skill before pushing.',
  ],
];

const { tool_input: { file_path = '' } = {} } = JSON.parse(readFileSync(0, 'utf8') || '{}');
const message = reminders.find(([pattern]) => pattern.test(file_path))?.[1];

if (message) {
  process.stdout.write(JSON.stringify({ hookSpecificOutput: { hookEventName: 'PostToolUse', additionalContext: message } }));
}
