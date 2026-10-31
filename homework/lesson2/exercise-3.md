# Exercise 3 — Install BMAD, and know what it costs

> Slide 36. Command: `npx bmad-method install --yes --modules bmm --tools claude-code`
> (non-interactive, since this session drives Claude Code itself rather than a
> human at a terminal — but every decision below is the same one the
> interactive prompts would have asked: modules = `bmm` only, core is
> always added; tool = `claude-code`; defaults for everything else).

## What one install command put on disk

```
_bmad/
  _config/manifest.yaml   # what's installed, versions, IDEs
  config.toml             # shared config
  config.user.toml        # per-user answers (installer-managed)
  custom/                 # empty — never touched by the installer
  render/                 # gitignored by its own .gitignore (*  !.gitignore)
  scripts/                # Python helpers BMAD skills call via `uv run`
  core/, bmm/             # the two installed modules' assets
.claude/skills/bmad-*/    # 29 skills (agents, workflows: PRD, architecture,
                           # sprint planning, retrospective, etc.)
```

`_bmad/_config/manifest.yaml` confirms it:

```yaml
modules:
  - name: core
  - name: bmm
ides:
  - claude-code
```

## Which files I may customize

- `_bmad/custom/` — explicitly "never touched by the installer" per its own
  header comment chain. This is where durable, hand-written overrides go.
- Anywhere outside `_bmad/` and `.claude/skills/bmad-*` is untouched by BMAD
  entirely (it didn't modify `CLAUDE.md`, `package.json`, or add an
  `AGENTS.md` — that only happens when the `project-context` workflow runs,
  which is exercise 4).

## Which file does **not** survive a re-install

`_bmad/config.user.toml`'s own header says it plainly:

> "Installer-managed. Regenerated on every install — treat as read-only.
> Direct edits to this file will be overwritten on the next install."

So **`_bmad/custom/` survives a re-install untouched**; **`_bmad/config.user.toml`
does not** — it's regenerated every time (though your prior answers become
the new defaults, so in practice the *values* usually come back the same;
the *file* itself is always rewritten).

## What it now costs every session

29 `bmad-*` skills were added under `.claude/skills/`. Each skill's one-line
name + description sits in context every session (that's how the Skill tool
listing works); the full `SKILL.md` body only loads when the skill is
actually invoked. The combined size of all 29 skills' `.md` files on disk is
~764 KB, but that's not the right proxy for the always-loaded cost — only
the short descriptions are resident by default.

**This number comes from the live `/skills` view, not from me**: run `claude`
in this directory, then `/skills`, press `t` to sort by token cost. That's
the authoritative source the exercise points at (slide 36's hint), and it
isn't something a non-interactive install or a file-size estimate can
substitute for. Sorted by `t` (highest first), the 29 `bmad-*` entries:

| Skill | Tokens |
| --- | ---: |
| bmad-deep-recon | ~250 |
| bmad-review | ~180 |
| bmad-build | ~160 |
| bmad-architecture | ~130 |
| bmad-spec | ~130 |
| bmad-sprint-planning | ~130 |
| bmad-forge-idea | ~120 |
| bmad-retrospective | ~110 |
| bmad-prfaq | ~110 |
| bmad-party-mode | ~100 |
| bmad-correct-course | ~80 |
| bmad-ux | ~80 |
| bmad-advanced-elicitation | ~80 |
| bmad-project-context | ~70 |
| bmad-walkthrough | ~70 |
| bmad-help | ~70 |
| bmad-customize | ~70 |
| bmad-code-review | ~60 |
| bmad-agent-analyst | ~60 |
| bmad-qa-generate-e2e-tests | ~50 |
| bmad-agent-dev | ~50 |
| bmad-brainstorming | ~50 |
| bmad-agent-pm | ~50 |
| bmad-agent-architect | ~50 |
| bmad-create-epics-and-stories | ~50 |
| bmad-product-brief | ~50 |
| bmad-agent-ux-designer | ~40 |
| bmad-prd | ~40 |
| bmad-build-auto | ~30 |

That's **~2,520 tokens** resident every session just for the `bmad-*` skill
descriptions, before any skill body is ever loaded.
