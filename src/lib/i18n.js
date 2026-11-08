// Pure i18n core: static UI strings plus the lang-resolution logic. No fetch,
// DOM, or localStorage — index.html owns the URL and persists the choice
// there (?lang=en), not in storage (see CLAUDE.md: no browser storage).

/** @typedef {'he' | 'en'} Lang */

/** @type {Lang[]} */
export const LANGS = ['he', 'en'];

/** @type {Lang} */
export const DEFAULT_LANG = 'he';

/**
 * Parse the `lang` query param out of a location.search-style string.
 * @param {string} search - e.g. "?lang=en" or "" or "?amount=500&lang=he".
 * @returns {Lang} 'en' only when explicitly requested and valid; 'he' otherwise.
 */
export function resolveLang(search) {
  const params = new URLSearchParams(search ?? '');
  const requested = params.get('lang');
  return /** @type {Lang[]} */ (LANGS).includes(/** @type {Lang} */ (requested))
    ? /** @type {Lang} */ (requested)
    : DEFAULT_LANG;
}

/**
 * Build the URL search string with `lang` set, keeping every other param.
 * @param {string} search - Current location.search.
 * @param {Lang} lang
 * @returns {string} e.g. "?amount=500&lang=en"
 */
export function withLang(search, lang) {
  const params = new URLSearchParams(search ?? '');
  params.set('lang', lang);
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

/** @type {Record<Lang, 'rtl' | 'ltr'>} */
export const DIRECTION = { he: 'rtl', en: 'ltr' };

/** @type {Record<Lang, string>} */
export const LOCALE = { he: 'he-IL', en: 'en-US' };

/** @type {Record<Lang, Record<string, string>>} */
export const STRINGS = {
  he: {
    title: 'StockBroker — יועץ השקעות',
    langGroup: 'שפה',
    langHe: 'עברית',
    langEn: 'English',
    heading: 'לאן להפקיד החודש?',
    subheading: 'דירוג 7 המדדים/קרנות שלך לפי תשואה מותאמת סיכון, משוקללת על פני 1/3/5 שנים (ככל שיש נתונים), והצעת חלוקה להפקדה החודשית.',
    amountLabel: 'סכום להפקדה (₪):',
    refreshButton: 'רענן נתונים',
    scheduleNote: 'הנתונים נשלפים אוטומטית פעם ביום ב-05:00 UTC (08:00 שעון ישראל בקיץ, 07:00 בחורף), או מיידית בלחיצה על "רענן נתונים".',
    colFund: 'קרן',
    colId: 'מספר קרן',
    col1m: '1 חודש',
    col3m: '3 חודשים',
    col1y: 'תשואה שנתית: 1 שנה',
    col3y: '3 שנים',
    col5y: '5 שנים',
    colVol1y: 'תנודתיות (1 שנה)',
    colVol3y: 'תנודתיות (3 שנים)',
    colVol5y: 'תנודתיות (5 שנים)',
    colVolBlended: 'תנודתיות משוקללת (1/3/5)',
    colScore: 'ציון מותאם סיכון',
    colWeight: 'הקצאה מוצעת',
    colAmount: 'סכום (₪)',
    tokenLabel: 'GitHub token (fine-grained, Actions: read & write, Contents: read). נשמר בזיכרון של הלשונית בלבד.',
    tokenConfirm: 'אישור',
    tokenCancel: 'ביטול',
    disclaimerBold: 'לא ייעוץ השקעות.',
    disclaimerBody: 'הנתונים נשלפים אוטומטית מ-bizportal.co.il. הציון המותאם-סיכון הוא ממוצע משוקלל של (תשואה שנתית ÷ תנודתיות) על פני 1/3/5 שנים — ככל שיש היסטוריית מסחר ארוכה יותר, כך המשקל שלה גבוה יותר (1 שנה: 25%, 3 שנים: 35%, 5 שנים: 40%), כדי לצמצם רעש מתנודות קצרות-טווח. קרנות עם פחות משנת מסחר מלאה (מסומנות כ-N/A) מקבלות רצפת הקצאה קבועה של 3% עד שיצטבר מספיק היסטוריה. בדוק תמיד נתונים מול המקור לפני קבלת החלטה.',
    updatedPrefix: 'עודכן לאחרונה: ',
    dataLoadErrorPrefix: 'שגיאה בטעינת הנתונים: ',
    fileLoadError: 'הקובץ לא נטען ({status})',
    refreshCancelledNoToken: 'הרענון בוטל: לא הוזן טוקן',
    refreshTimeout: 'הריצה לא הסתיימה בזמן',
    summaryTotal: 'סה״כ',
    summaryFunds: 'קרנות',
    summaryScore: 'ציון משוקלל',
  },
  en: {
    title: 'StockBroker — Investment Advisor',
    langGroup: 'Language',
    langHe: 'עברית',
    langEn: 'English',
    heading: 'Where should this month’s deposit go?',
    subheading: 'Ranks your 7 indices/funds by a risk-adjusted score blended across 1/3/5-year windows (wherever history exists), and suggests how to split this month’s deposit.',
    amountLabel: 'Deposit amount (₪):',
    refreshButton: 'Refresh data',
    scheduleNote: 'Data refreshes automatically once a day at 05:00 UTC, or immediately via "Refresh data".',
    colFund: 'Fund',
    colId: 'Fund ID',
    col1m: '1 month',
    col3m: '3 months',
    col1y: 'Annualized: 1yr',
    col3y: '3yr',
    col5y: '5yr',
    colVol1y: 'Volatility (1yr)',
    colVol3y: 'Volatility (3yr)',
    colVol5y: 'Volatility (5yr)',
    colVolBlended: 'Blended volatility (1/3/5)',
    colScore: 'Risk-adj. score',
    colWeight: 'Suggested weight',
    colAmount: 'Amount (₪)',
    tokenLabel: 'GitHub token (fine-grained, Actions: read & write, Contents: read). Kept in this tab’s memory only.',
    tokenConfirm: 'Confirm',
    tokenCancel: 'Cancel',
    disclaimerBold: 'Not investment advice.',
    disclaimerBody: 'Data is pulled automatically from bizportal.co.il. The risk-adjusted score is a weighted average of (annualized return ÷ volatility) across 1/3/5-year windows — longer trading history gets more weight (1yr: 25%, 3yr: 35%, 5yr: 40%) to reduce noise from short-term swings. Funds with under a year of trading history (shown as N/A) get a fixed 3% floor allocation until enough history accumulates. Always double-check the numbers against the source before acting on them.',
    updatedPrefix: 'Last updated: ',
    dataLoadErrorPrefix: 'Error loading data: ',
    fileLoadError: 'File failed to load ({status})',
    refreshCancelledNoToken: 'Refresh cancelled: no token entered',
    refreshTimeout: 'The run did not finish in time',
    summaryTotal: 'Total',
    summaryFunds: 'funds',
    summaryScore: 'Weighted score',
  },
};

/**
 * Look up a string for the given language, falling back to the default
 * language and finally the key itself if nothing matches.
 * @param {Lang} lang
 * @param {string} key
 * @returns {string}
 */
export function t(lang, key) {
  return STRINGS[lang]?.[key] ?? STRINGS[DEFAULT_LANG]?.[key] ?? key;
}
