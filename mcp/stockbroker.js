import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import process from 'node:process';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const dataPath = process.env.STOCKBROKER_DATA_PATH;
if (!dataPath) {
  throw new Error('STOCKBROKER_DATA_PATH is not set');
}

const root = resolve(import.meta.dirname, '..');
const readFunds = () => JSON.parse(readFileSync(resolve(root, dataPath), 'utf8'));
const fundIds = readFunds().funds.map((fund) => fund.id);

const formatScore = (score) => (score === null || score === undefined ? '—' : score.toFixed(2));
const formatPercent = (value) => (value === null || value === undefined ? '—' : `${(value * 100).toFixed(1)}%`);

const server = new McpServer({ name: 'stockbroker', version: '1.0.0' });

server.registerTool(
  'fund_metrics',
  {
    title: 'Fund metrics',
    description:
      'Read one TASE fund from the stockbroker dashboard by its numeric id: 1, 3 and 5-year returns, volatility, ' +
      'risk-adjusted score, and the suggested share of the monthly deposit. Use when the user asks how a fund ' +
      'performed or why it gets its suggested weight. Read-only; it does not refresh the data.',
    inputSchema: { fund_id: z.enum(fundIds) },
  },
  async ({ fund_id }) => {
    const fund = readFunds().funds.find((item) => item.id === fund_id);
    const { metrics: m } = fund;
    const text = [
      `${fund.name_en} (${fund.id})`,
      `Return 1y: ${formatPercent(m.return_1y)} · 3y: ${formatPercent(m.return_3y)} · 5y: ${formatPercent(m.return_5y)}`,
      `Volatility 1y: ${formatPercent(m.volatility_1y)} · 3y: ${formatPercent(m.volatility_3y)}`,
      `Risk-adjusted score: ${formatScore(m.risk_adjusted_score)} (basis: ${m.score_basis})`,
      `Suggested weight: ${formatPercent(fund.suggested_weight)}`,
      `Last price ${m.last_price} on ${m.last_date}${fund.stale ? ' (stale)' : ''}`,
    ].join('\n');
    return { content: [{ type: 'text', text }] };
  },
);

server.registerResource(
  'funds-summary',
  'stockbroker://funds',
  {
    title: 'Funds summary',
    description: 'One line per fund with its suggested weight and risk-adjusted score, plus the data timestamp.',
    mimeType: 'text/markdown',
  },
  async (uri) => {
    const { generated_at, funds } = readFunds();
    const rows = funds.map(
      (fund) =>
        `| ${fund.id} | ${fund.name_en} | ${formatPercent(fund.suggested_weight)} | ${formatScore(fund.metrics.risk_adjusted_score)} | ${fund.stale ? 'yes' : 'no'} |`,
    );
    const text = [
      `# Funds summary`,
      `Generated at ${generated_at}`,
      '',
      '| id | name | suggested weight | score | stale |',
      '| --- | --- | --- | --- | --- |',
      ...rows,
    ].join('\n');
    return { contents: [{ uri: uri.href, mimeType: 'text/markdown', text }] };
  },
);

server.registerPrompt(
  'monthly_split',
  {
    title: 'Monthly split',
    description: 'Explain how the funds would split a monthly deposit. Read-only.',
    argsSchema: { amount: z.string().optional() },
  },
  ({ amount }) => ({
    messages: [
      {
        role: 'user',
        content: {
          type: 'text',
          text:
            `Using the stockbroker://funds resource, explain how a monthly deposit of ${amount ?? 'the amount I give you'} ` +
            'would split across the funds by suggested weight. Name each fund and its shekel amount, and say which funds ' +
            'have no score. Do not change any files.',
        },
      },
    ],
  }),
);

await server.connect(new StdioServerTransport());
