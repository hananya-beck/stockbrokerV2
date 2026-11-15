import { buildFundRowViewModel } from './formatting.js';
import { t } from './i18n.js';

const NEEDS_QUOTING = /[",\r\n]/;

/**
 * @param {string} value
 * @returns {string} One RFC 4180 field: quoted only when it holds a comma, quote or newline.
 */
export function escapeCsvField(value) {
  return NEEDS_QUOTING.test(value) ? `"${value.replaceAll('"', '""')}"` : value;
}

/**
 * @param {string[]} fields
 * @returns {string} One CSV record, without a line terminator.
 */
export function toCsvRow(fields) {
  return fields.map(escapeCsvField).join(',');
}

/** @type {Array<[string, (row: import('./formatting.js').FundRowViewModel, lang: import('./i18n.js').Lang) => string]>} */
const COLUMNS = [
  ['colFund', (row, lang) => (lang === 'he' ? row.nameHe : row.nameEn)],
  ['colId', row => row.id],
  ['col1m', row => row.return1m.text],
  ['col3m', row => row.return3m.text],
  ['col1y', row => row.return1y.text],
  ['col3y', row => row.return3y.text],
  ['col5y', row => row.return5y.text],
  ['colVol1y', row => row.volatility1y.text],
  ['colVol3y', row => row.volatility3y.text],
  ['colVol5y', row => row.volatility5y.text],
  ['colVolBlended', row => row.volatilityBlended.text],
  ['colScore', row => row.riskAdjustedScore.text],
  ['colWeight', row => `${row.weightPct}%`],
  ['colAmount', row => String(row.amount)],
];

/**
 * Shape the funds, in the order given, into CSV text that mirrors the table:
 * localized header, localized fund name, and the same formatted cells.
 * The caller passes the funds already sorted the way the table shows them.
 * @param {import('./formatting.js').Fund[]} funds
 * @param {number} amount - Total deposit amount, for the amount column.
 * @param {import('./i18n.js').Lang} lang
 * @returns {string} CRLF-separated records with a trailing CRLF; header only when funds is empty.
 */
export function buildFundsCsv(funds, amount, lang) {
  const header = COLUMNS.map(([key]) => t(lang, key));
  const rows = funds.map(fund => {
    const row = buildFundRowViewModel(fund, amount);
    return COLUMNS.map(([, pick]) => pick(row, lang));
  });
  return [header, ...rows].map(toCsvRow).join('\r\n') + '\r\n';
}
