import type { On } from 'claude-code'
import { expect, test } from 'claude-code/testing'
import type { Engine, Mounted } from 'claude-code/testing'

const PANE = {
  plugin: 'stock-browser',
  component: 'Pane',
  requestId: 'stock-browser',
  props: {
    title: 'StockBrowser',
    isFocused: false,
    bodyColumns: 80,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 40 },
    view: {},
  },
} as const

const FUNDS_FILE = /data[\\/]funds\.json$/

const fund = (
  id: string,
  nameEn: string,
  score: number,
  extra: Record<string, unknown> = {},
) => ({
  id,
  name_en: nameEn,
  name_he: 'שם',
  metrics: {
    return_1m: 0.03,
    return_3m: -0.17,
    return_1y: 0.39,
    return_3y: 0.33,
    volatility_blended: 0.29,
    risk_adjusted_score: score,
    last_date: '2026-11-06',
  },
  stale: id === 'b',
  suggested_weight: 0.2017,
  ...extra,
})

const FUNDS = JSON.stringify({
  generated_at: '2026-11-07T11:33:41+00:00',
  funds: [
    fund('a', 'Alpha', 1.1),
    fund('b', 'Beta', 0.5),
    fund('c', 'Gamma\u0001', 0.2),
    fund('d', 'Delta', 0.1, { history: Array.from({ length: 400 }, (_, i) => i / 10) }),
  ],
})

const stubFundsFile = (on: On, text: string) => {
  on('command.register', () => ({ value: { command: 'stock-browser' } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('fs.read', (_, e) => ({ value: FUNDS_FILE.test(e.path) ? text : '' }))
}

const withPane = async (
  $: Engine,
  body: (ui: Mounted<'desktop', 'Pane'>) => Promise<void>,
) => {
  await $.session.start({ cwd: '.', surface: 'desktop', isInteractive: true })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })

  try {
    await body(ui)
  } finally {
    await ui.unmount()
  }
}

test('selecting a fund shows its record highlighted as JSON, and marks the row', async ($, on) => {
  stubFundsFile(on, FUNDS)

  await withPane($, async ui => {
    expect(await ui.find({ type: 'Code' })).toBeUndefined()
    expect((await ui.find({ key: 'b' }))?.text).toMatch(/Beta \(stale\)/)

    await ui.press({ key: 'a' })

    expect((await ui.find({ key: 'a' }))?.text).toMatch(/^●/)
    expect((await ui.find({ type: 'Code' }))?.props?.language).toBe('json')
    expect((await ui.find({ type: 'Code' }))?.props?.source).toMatch(/"name_en": "Alpha"/)
  })
})

test('a record that holds control characters shows one calm line, not a preview', async ($, on) => {
  stubFundsFile(on, FUNDS)

  await withPane($, async ui => {
    await ui.press({ key: 'c' })

    expect(await ui.find({ type: 'Text', text: /binary data/ })).toBeDefined()
    expect(await ui.find({ type: 'Code' })).toBeUndefined()
  })
})

test('a record over the cap shows its first lines and says how many are left', async ($, on) => {
  stubFundsFile(on, FUNDS)

  await withPane($, async ui => {
    await ui.press({ key: 'd' })

    const source = (await ui.find({ type: 'Code' }))?.props?.source as string
    expect(source.split('\n').length).toBe(30)
    expect(await ui.find({ type: 'Text', text: /more lines not shown/ })).toBeDefined()
  })
})

test('a fund file that cannot be read shows a line saying why', async ($, on) => {
  stubFundsFile(on, '{')

  await withPane($, async ui => {
    expect(await ui.find({ type: 'Text', text: /could not be read/ })).toBeDefined()
  })
})
