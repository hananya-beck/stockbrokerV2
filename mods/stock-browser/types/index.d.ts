declare module 'claude-code' {
  interface PluginState {
    'stock-browser': {
      openFunds: Shaped<string[]>
    }
  }
}
