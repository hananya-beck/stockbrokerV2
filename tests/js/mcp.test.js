import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath, URL } from 'node:url';
import process from 'node:process';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

const { funds } = JSON.parse(readFileSync(new URL('../../data/funds.json', import.meta.url), 'utf8'));
const serverPath = fileURLToPath(new URL('../../mcp/stockbroker.js', import.meta.url));

async function withServer(run) {
  const client = new Client({ name: 'stockbroker-test', version: '0.0.0' });
  const transport = new StdioClientTransport({
    command: 'node',
    args: [serverPath],
    env: { ...process.env, STOCKBROKER_DATA_PATH: 'data/funds.json' },
  });
  await client.connect(transport);
  try {
    return await run(client);
  } finally {
    await client.close();
  }
}

test('server advertises one tool, one resource and one prompt', () =>
  withServer(async (client) => {
    const tools = await client.listTools();
    const resources = await client.listResources();
    const prompts = await client.listPrompts();
    assert.deepEqual(tools.tools.map((tool) => tool.name), ['fund_metrics']);
    assert.deepEqual(resources.resources.map((resource) => resource.uri), ['stockbroker://funds']);
    assert.deepEqual(prompts.prompts.map((prompt) => prompt.name), ['monthly_split']);
  }));

test('fund_metrics returns the metrics for a known fund id', () =>
  withServer(async (client) => {
    const result = await client.callTool({ name: 'fund_metrics', arguments: { fund_id: funds[0].id } });
    assert.match(result.content[0].text, new RegExp(funds[0].id));
    assert.match(result.content[0].text, /Risk-adjusted score/);
  }));

test('fund_metrics rejects an id outside the schema before it reaches the handler', () =>
  withServer(async (client) => {
    const result = await client.callTool({ name: 'fund_metrics', arguments: { fund_id: '0000000' } });
    assert.equal(result.isError, true);
    assert.match(result.content[0].text, /Invalid arguments for tool fund_metrics/);
  }));

test('the funds resource lists every fund id', () =>
  withServer(async (client) => {
    const result = await client.readResource({ uri: 'stockbroker://funds' });
    const text = result.contents[0].text;
    for (const fund of funds) {
      assert.match(text, new RegExp(fund.id));
    }
  }));

test('monthly_split turns the amount argument into a user message', () =>
  withServer(async (client) => {
    const result = await client.getPrompt({ name: 'monthly_split', arguments: { amount: '10000' } });
    assert.match(result.messages[0].content.text, /10000/);
  }));
