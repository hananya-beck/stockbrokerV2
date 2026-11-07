import { expect, test } from 'claude-code/testing'

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

const FUNDS = JSON.stringify({
  generated_at: '2026-11-07T11:33:41+00:00',
  funds: [
    {
      id: 'a',
      name_en: 'Alpha',
      name_he: 'אלפא',
      metrics: {
        return_1m: 0.03,
        return_3m: -0.17,
        return_1y: 0.39,
        return_3y: 0.33,
        volatility_blended: 0.29,
        risk_adjusted_score: 1.1,
        last_date: '2026-11-06',
      },
      stale: false,
      suggested_weight: 0.2017,
    },
    {
      id: 'b',
      name_en: 'Beta',
      name_he: 'בטא',
      metrics: {
        return_1m: null,
        return_3m: null,
        return_1y: null,
        return_3y: null,
        volatility_blended: 0.1,
        risk_adjusted_score: 0.5,
        last_date: '2026-10-01',
      },
      stale: true,
      suggested_weight: 0.1,
    },
  ],
})

test('the pane ranks the funds, marks stale ones and opens one fund on a press', async ($, on) => {
  on('command.register', () => ({ value: { command: 'stock-browser' } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('fs.read', (_, e) => ({
    value: /data[\\/]funds\.json$/.test(e.path) ? FUNDS : '',
  }))

  await $.session.start({ cwd: '.', surface: 'desktop', isInteractive: true })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })

  expect((await ui.find({ key: 'b' }))?.text).toMatch(/Beta \(stale\)/)
  expect(await ui.find({ type: 'Text', text: /Suggested weight/ })).toBeUndefined()

  await ui.press({ key: 'a' })

  expect(await ui.find({ type: 'Text', text: /Suggested weight 20\.2%/ })).toBeDefined()
  await ui.unmount()
})

test('a fund file that cannot be read shows a line saying why', async ($, on) => {
  on('command.register', () => ({ value: { command: 'stock-browser' } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('fs.read', () => ({ value: '{' }))

  await $.session.start({ cwd: '.', surface: 'desktop', isInteractive: true })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })

  expect(await ui.find({ type: 'Text', text: /could not be read/ })).toBeDefined()
  await ui.unmount()
})
