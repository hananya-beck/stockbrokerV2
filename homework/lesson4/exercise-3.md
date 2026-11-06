# Exercise 3: A description that routes

**Goal:** The description is the whole loading decision, so make it fire when it should, and only then.

## policy-audit: rewritten description
- **Key use case first.** It opens with what the skill does: an AGENTS.md policy audit with PASS/FAIL per rule and `file:line`. The description is cut at 1,536 characters, so the important part has to come first.
- **The words people really type.** I added "can I commit this", "sanity-check before I push" and the Hebrew "בדוק שהכל תקין לפני push" to the existing "audit", "policy check" and "is it safe to push".
- **Sharper negative line.** The closest look-alike is a code review of a diff. That's now sent to `bmad-code-review` or `bmad-review`, alongside the existing exclusions (fund data goes to `add-fund`, scraper failures are out of scope).
- **Size.** The description grew from 495 to 748 characters.

## bmad-party-mode: manual-only
I added `disable-model-invocation: true` to `.claude/skills/bmad-party-mode/SKILL.md`. Its 312-character description no longer sits in every session's context, and `/bmad-party-mode` still runs it.

**Why this one:**
- Party mode only makes sense when I ask for it. The model never needs it to finish a task.
- I rejected `bmad-build-auto`, even though its description says "Use when invoked by name". My orchestrator prompt (`prompts/exercise-10-orchestrator.md`) has subagents run it, and manual-only would break that loop.

**Trade-off:** `bmad-create-epics-and-stories` ([P] Party Mode) and `bmad-retrospective` ("discuss it as a team") invoke party mode through the model. Once it's manual-only, I type `/bmad-party-mode` myself at those points. The retrospective already falls back to an inline discussion when party mode is unavailable.

**Caveat:** A BMAD reinstall or upgrade rewrites the skill's `SKILL.md`, so re-check this flag after one.

## Routing tests (fresh session, skill not named)
Each request ran in its own fresh session with `claude -p --output-format stream-json`. The result records whether a `Skill` tool call appeared.

| Request | Expected | Result |
|---|---|---|
| "is it safe to push this?" | policy-audit loads | ✅ loaded |
| "run a pre-release check on the repo" | policy-audit loads | ✅ loaded |
| "בדוק שהכל תקין לפני push" | policy-audit loads | ✅ loaded |
| "review my last commit for bugs" (look-alike) | policy-audit does **not** load | ✅ not loaded |

## Cost and use
- `/context` lists `policy-audit` at about 250 tokens and doesn't list `bmad-party-mode` at all.
- Typing `/bmad-party-mode` still runs it.

`/skill-doctor`:

| Skill | Cost | Use |
|---|---|---|
| policy-audit | ~250 tokens in context, every session | 4 uses (the 3 routing tests above plus one earlier run), 579.9k tokens over 7 days |
| bmad-party-mode | none in context (`-`) | 1 use (typed `/bmad-party-mode`), 48.1k tokens over 7 days |
