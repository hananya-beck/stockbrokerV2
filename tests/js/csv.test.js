import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildFundsCsv, escapeCsvField, toCsvRow } from '../../src/lib/csv.js';
import { STRINGS } from '../../src/lib/i18n.js';

/** @returns {import('../../src/lib/formatting.js').Fund} */
function fund(overrides = {}) {
  return {
    id: '5109889',
    name_he: 'MTF מחקה ת"א 125',
    name_en: 'TASE 125',
    suggested_weight: 0.25,
    metrics: {
      return_1m: -0.01,
      return_3m: 0.02,
      return_1y: 0.176,
      return_3y: 0.3144,
      return_5y: null,
      volatility_1y: 0.188,
      volatility_3y: 0.172,
      volatility_5y: null,
      volatility_blended: 0.1789,
      risk_adjusted_score: 1.2305,
    },
    ...overrides,
  };
}

test('escapeCsvField leaves plain text alone', () => {
  assert.equal(escapeCsvField('TASE 125'), 'TASE 125');
  assert.equal(escapeCsvField(''), '');
});

test('escapeCsvField quotes commas and newlines', () => {
  assert.equal(escapeCsvField('a,b'), '"a,b"');
  assert.equal(escapeCsvField('a\nb'), '"a\nb"');
  assert.equal(escapeCsvField('a\rb'), '"a\rb"');
});

test('escapeCsvField doubles embedded quotes', () => {
  assert.equal(escapeCsvField('MTF מחקה ת"א 125'), '"MTF מחקה ת""א 125"');
});

test('toCsvRow joins escaped fields with commas', () => {
  assert.equal(toCsvRow(['a', 'b,c', '']), 'a,"b,c",');
  assert.equal(toCsvRow([]), '');
});

test('buildFundsCsv writes an English header and English names for en', () => {
  const [header, row] = buildFundsCsv([fund()], 1000, 'en').split('\r\n');
  assert.equal(header, [
    'Fund', 'Fund ID', '1 month', '3 months', 'Annualized: 1yr', '3yr', '5yr',
    'Volatility (1yr)', 'Volatility (3yr)', 'Volatility (5yr)', 'Blended volatility (1/3/5)',
    'Risk-adj. score', 'Suggested weight', 'Amount (₪)',
  ].join(','));
  assert.equal(row.split(',')[0], 'TASE 125');
});

test('buildFundsCsv writes a Hebrew header and Hebrew names for he', () => {
  const [header, row] = buildFundsCsv([fund()], 1000, 'he').split('\r\n');
  assert.ok(header.startsWith(`${STRINGS.he.colFund},${STRINGS.he.colId},`));
  assert.ok(row.startsWith('"MTF מחקה ת""א 125",5109889,'));
});

test('buildFundsCsv mirrors the table cells, with — for unknown values', () => {
  const [, row] = buildFundsCsv([fund()], 1000, 'en').split('\r\n');
  assert.equal(row, 'TASE 125,5109889,-1.0%,2.0%,17.6%,31.4%,—,18.8%,17.2%,—,17.9%,1.23,25.0%,250');
});

test('buildFundsCsv keeps the order it is given', () => {
  const a = fund({ id: 'a', name_en: 'A' });
  const b = fund({ id: 'b', name_en: 'B' });
  const ids = buildFundsCsv([b, a], 0, 'en').split('\r\n').slice(1, 3).map(r => r.split(',')[1]);
  assert.deepEqual(ids, ['b', 'a']);
});

test('buildFundsCsv scales the amount column with the deposit', () => {
  const amountOf = (/** @type {number} */ amount) =>
    buildFundsCsv([fund()], amount, 'en').split('\r\n')[1].split(',').at(-1);
  assert.equal(amountOf(0), '0');
  assert.equal(amountOf(2000), '500');
});

test('buildFundsCsv returns just the header for no funds', () => {
  const csv = buildFundsCsv([], 1000, 'en');
  assert.ok(csv.endsWith('\r\n'));
  assert.equal(csv.split('\r\n').length, 2);
});

test('buildFundsCsv ends every record with CRLF', () => {
  const csv = buildFundsCsv([fund(), fund()], 1000, 'en');
  assert.ok(csv.endsWith('\r\n'));
  assert.equal(csv.split('\r\n').length, 4);
});
