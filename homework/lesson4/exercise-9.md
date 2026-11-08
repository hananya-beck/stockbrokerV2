# Exercise 9: A read-only agent

**Goal:** A specialist whose tool list is its policy.

## What the exercise asks
From the syllabus (Level 5 homework, exercise 9; slide 62, "Authoring an agent — the tool list is the policy").
- Create a reviewer agent for the project that checks a change against the project rules, and cannot change a file. Choose its model and effort on purpose. Plant one violation and send the agent after it.
- **Done when:** the agent file has only the tools it needs, none that edit or run commands. Delegated the planted violation, it finds it and returns only a short summary. Asked to fix it, it says it can't, and then the plant is reverted.

## What I built
`.claude/agents/policy-reviewer.md`, a project agent (so it's in git and teammates get it).

| Key | Value | Why |
| --- | --- | --- |
| `tools` | `Read, Grep, Glob` | no Edit, Write or Bash, so it can't change a file or run a command |
| `model` | `sonnet` | the rules need judgement about matches, such as comments and Date uses, not only a grep |
| `effort` | `medium` | a bounded checklist; more effort adds cost without finding more |
| `maxTurns` | `20` | a limit on a single review |

The body is the system prompt: seven rules from `AGENTS.md` (browser storage, leading slash, browser APIs in `src/lib`, colours outside the tokens file, UI text in `i18n.js`, committed tokens, hand-edited `data/funds.json`), each with the way to check it. It replies with `PASS` or `FAIL`, then one line per violation. A match inside a comment is not a violation.

## The plant
`src/lib/formatting.js` got a function, `rememberLastFund`, that calls `localStorage.setItem` (rule 1, and a browser API in the pure core). The plant was uncommitted and has been reverted.

## Results
- [x] The tool list has no Edit, Write or Bash.
- [x] Delegated (`claude -p "Use the policy-reviewer agent to review src/lib/formatting.js …"`): the reply is `FAIL` with `src/lib/formatting.js:214`, the `localStorage.setItem` call.
- [x] The first run also flagged the header comment that mentions `localStorage` (line 2). The body now says a match inside a comment isn't a violation. The rerun flags only line 214.
- [x] Asked to fix (`claude -p "Ask the policy-reviewer agent to fix …"`): the agent replies that it is read-only and can't fix it. `src/lib/formatting.js` was unchanged afterwards. The main session then offered to make the fix itself. That's the main session's behaviour, not the agent's.
- [x] The plant was reverted with `git checkout`; `git status` shows only the new agent folder.
- [x] **Diff review:** the main session ran `git diff` into a file and asked the agent to review it. The agent read the diff and the changed file with its own tools and returned `FAIL` with `index.html:486`, a leading `/` in `<img src>` (rule 2). The plant was then reverted.

## Notes
- **Reply length.** The first reply ran a few lines over the 15-line limit, and in the fix run the main session reported more than the agent said. The brief should cap the length of what the main session asks for, not only the agent's own reply.
- **Line numbers.** The agent's first reply gave line 214 and then said 215 was the call. Line 214 is correct.

## Status
The agent, the delegation, the refusal to fix, the diff review and the revert all check out.
