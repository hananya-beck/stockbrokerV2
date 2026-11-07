import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

const PANE = 'stock-browser'
const DATA = 'data/funds.json'
const CAP_BYTES = 4096
const CAP_LINES = 30
// JSON.stringify writes a control character as an escape, so an escape here is one the record holds.
const CONTROL_ESCAPE = /\\u00[01][0-9a-f]/i
const CONTROL_CHARS = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g

const selectedFund = atom(
  { plugin: 'stock-browser', key: 'selectedFund' } as const,
  '',
  { shape: 'selected-fund-1' },
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
  score: number
  stale: boolean
  raw: RawFund
}

type Loaded = { funds: Fund[]; generatedAt: string } | { error: string }

const printable = (text: string) => text.replace(CONTROL_CHARS, '�')

const toFund = (raw: RawFund): Fund => ({
  id: raw.id,
  nameEn: raw.name_en,
  score: raw.metrics.risk_adjusted_score,
  stale: raw.stale,
  raw,
})

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
    const { Box, Button, Code, Text } = $.ui.resolve(e)
    const selected = await read($, selectedFund)
    const loaded = await loadFunds($)

    if ('error' in loaded) {
      return (
        <Box flexDirection="column">
          <Text>{loaded.error}</Text>
        </Box>
      )
    }

    const chosen = loaded.funds.find(fund => fund.id === selected)
    const record = chosen ? JSON.stringify(chosen.raw, null, 2) : ''
    const bytes = new TextEncoder().encode(record).byteLength
    const isOverCap = bytes > CAP_BYTES
    const recordLines = record.split('\n')
    const shown = isOverCap
      ? recordLines.slice(0, CAP_LINES).join('\n')
      : record

    return (
      <Box flexDirection="column">
        <Text dimColor>{`Data as of ${loaded.generatedAt.slice(0, 10)}`}</Text>
        {loaded.funds.map(fund => (
          <Button
            key={fund.id}
            plain
            onPress={() => update($, selectedFund, () => fund.id)}
          >
            {`${fund.id === selected ? '●' : '▸'} ${fund.score.toFixed(3)}  ${printable(fund.nameEn)}${fund.stale ? ' (stale)' : ''}`}
          </Button>
        ))}
        {selected !== '' && !chosen && (
          <Text>{`${selected} is not a fund in ${DATA}, so nothing is shown.`}</Text>
        )}
        {chosen && (
          <Text>{`${printable(chosen.nameEn)} · ${DATA} · ${bytes} B`}</Text>
        )}
        {chosen && CONTROL_ESCAPE.test(record) && (
          <Text>{'This record holds binary data, so it has no text preview.'}</Text>
        )}
        {chosen && !CONTROL_ESCAPE.test(record) && (
          <Code source={shown} language="json" startLine={1} />
        )}
        {chosen && !CONTROL_ESCAPE.test(record) && isOverCap && (
          <Text dimColor>{`${recordLines.length - CAP_LINES} more lines not shown`}</Text>
        )}
      </Box>
    )
  })
}
