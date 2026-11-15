// Fixture: violates src/lib/CLAUDE.md's ban on network calls and the system clock.
export function fetchAndStamp(url) {
  const stamp = Date.now();
  return fetch(url).then((r) => ({ stamp, body: r }));
}
