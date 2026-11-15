#!/usr/bin/env bash
set -euo pipefail

input=$(cat)
cmd=$(printf '%s' "$input" | jq -er '.tool_input.command // ""' 2>/dev/null) || {
  echo "guard-bash: couldn't read .tool_input.command from stdin JSON" >&2
  exit 2
}

deny() {
  echo "BLOCKED by guard-bash hook: $1" >&2
  exit 2
}

# rm -rf / -fr / --recursive --force / -r -f as separate flags, any order
if [[ "$cmd" =~ rm[[:space:]]+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*)([[:space:]]|$) ]] \
  || [[ "$cmd" =~ rm.*--recursive.*--force ]] \
  || [[ "$cmd" =~ rm.*--force.*--recursive ]] \
  || [[ "$cmd" =~ rm.*[[:space:]]-[rR].*[[:space:]]-f([[:space:]]|$) ]] \
  || [[ "$cmd" =~ rm.*[[:space:]]-f.*[[:space:]]-[rR]([[:space:]]|$) ]]; then
  deny "recursive force-delete (rm -rf or equivalent) is never allowed in this repo."
fi

# npm publish — this package is private and isn't meant to ship to a registry
if [[ "$cmd" =~ npm[[:space:]]+publish ]]; then
  deny "npm publish is never allowed — package.json has \"private\": true."
fi

# force-push, any spelling, including a leading "+" refspec — would wipe the
# daily data-bot's commits on main (AGENTS.md policy)
if [[ "$cmd" =~ git[[:space:]]+push.*(--force-with-lease|--force|[[:space:]]-f([[:space:]]|$)|[[:space:]]\+[^[:space:]]) ]]; then
  deny "force-push is never allowed — it can wipe the data bot's commits; pull --rebase instead (see AGENTS.md)."
fi

exit 0
