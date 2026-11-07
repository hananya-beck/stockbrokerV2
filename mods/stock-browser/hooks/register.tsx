import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

const PANE = 'stock-browser'
const DATA = 'data/funds.json'

const openFunds = atom(
  { plugin: 'stock-browser', key: 'openFunds' } as const,
  [] as string[],
  { shape: 'open-funds-1' },
)

type RawFund = {
  id: string
  name_en: string
  name_he: string
  metrics: {
    return_1m: number | null
    return_3m: number | null
    return_1y: number | null
    return_3y: number | null
    volatility_blended: number
    risk_adjusted_score: number
    last_date: string
  }
  stale: boolean
  suggested_weight: number
}

type RawData = { generated_at: string; funds: RawFund[] }

type Fund = {
  id: string
  nameEn: string
  nameHe: string
  score: number
  return1m: number | null
  return3m: number | null
  return1y: number | null
  return3y: number | null
  volatility: number
  weight: number
  stale: boolean
  lastDate: string
}

type Loaded = { funds: Fund[]; generatedAt: string } | { error: string }

const toFund = (raw: RawFund): Fund => ({
  id: raw.id,
  nameEn: raw.name_en,
  nameHe: raw.name_he,
  score: raw.metrics.risk_adjusted_score,
  return1m: raw.metrics.return_1m,
  return3m: raw.metrics.return_3m,
  return1y: raw.metrics.return_1y,
  return3y: raw.metrics.return_3y,
  volatility: raw.metrics.volatility_blended,
  weight: raw.suggested_weight,
  stale: raw.stale,
  lastDate: raw.metrics.last_date,
})

const percent = (value: number | null) =>
  value === null ? '—' : `${(value * 100).toFixed(1)}%`

const toggle = (list: string[], id: string) =>
  list.includes(id) ? list.filter(one => one !== id) : [...list, id]

async function loadFunds($: EngineInterface): Promise<Loaded> {
  try {
    const raw = JSON.parse(await $.fs.read(DATA)) as RawData

    return {
      funds: raw.funds.map(toFund).sort((a, b) => b.score - a.score),
      generatedAt: raw.generated_at,
    }
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error)

    return { error: `${DATA} could not be read: ${reason}` }
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'stock-browser',
      description: 'Show the fund ranking in a StockBrowser pane',
    })

    return next(e)
  })

  on('command.run', { command: 'stock-browser' }, async $ => {
    await $.ui.open({ id: PANE, title: 'StockBrowser' })

    return { text: 'StockBrowser pane opened.' }
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Button, Text } = $.ui.resolve(e)
    const open = await read($, openFunds)
    const loaded = await loadFunds($)

    if ('error' in loaded) {
      return (
        <Box flexDirection="column">
          <Text>{loaded.error}</Text>
        </Box>
      )
    }

    const room = Math.max(1, (e.viewport?.rows ?? 24) - 4)
    const lines = loaded.funds.flatMap(fund => {
      const isOpen = open.includes(fund.id)
      const label = `${isOpen ? '▾' : '▸'} ${fund.score.toFixed(3)}  ${fund.nameEn}${fund.stale ? ' (stale)' : ''}`
      const button = (
        <Button
          key={fund.id}
          plain
          onPress={() => update($, openFunds, list => toggle(list, fund.id))}
        >
          {label}
        </Button>
      )

      if (!isOpen) return [button]

      return [
        button,
        <Text>{`   Returns  1m ${percent(fund.return1m)}  3m ${percent(fund.return3m)}  1y ${percent(fund.return1y)}  3y ${percent(fund.return3y)}`}</Text>,
        <Text>{`   Volatility ${percent(fund.volatility)}   Suggested weight ${percent(fund.weight)}`}</Text>,
        <Text>{`   Last price ${fund.lastDate}   ${fund.nameHe}`}</Text>,
      ]
    })

    return (
      <Box flexDirection="column">
        <Text dimColor>{`Data as of ${loaded.generatedAt.slice(0, 10)}`}</Text>
        {lines.slice(0, room)}
        {lines.length > room && (
          <Text dimColor>{`${lines.length - room} more not shown`}</Text>
        )}
      </Box>
    )
  })
}
