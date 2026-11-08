# Exercise 10: A skill that recruits the agent

**Goal:** "How" meets "who": a procedure that runs in the specialist's own window.

## What the exercise asks
From the syllabus (Level 5 homework, exercise 10; slide 61, "Who vs how", and slide 63, the frontmatter reference).
- Write a skill whose body is the review procedure, and make it run forked onto the agent from exercise 9, so the main session gets the verdict, not the work.
- **Done when:** invoking the skill finds the same planted violation as exercise 9. `/context` before and after shows the main window barely grew. In one sentence each, say when to call the agent directly and when the skill.

## What I built
`.claude/skills/policy-review/SKILL.md`:

```yaml
---
name: policy-review
description: Reviews the uncommitted change against the AGENTS.md policy, in the policy-reviewer's own window, and returns only its verdict. …
context: fork
agent: policy-reviewer
---
```

- **The two keys.** `context: fork` runs the skill in a subagent window, and `agent: policy-reviewer` says which agent runs it. Both are kebab-case, as the skill keys must be.
- **The body is the procedure.** It names the rules to check and asks for a verdict only.
- **The diff comes in with the body.** The forked agent has only `Read`, `Grep` and `Glob`, so it can't run `git`. The skill body uses `` !`git diff --name-only` `` and `` !`git diff` ``, which run before the agent starts and put the output in its prompt.
- **Routing.** The description says what it is for and what it isn't for (bug review, and the full pre-release audit, which is `policy-audit`).

## Checks
- [x] **Finds the planted violation.** With a leading `/` in `<img src>` at `index.html:486`, `/policy-review` returned `FAIL` with that line, the same finding as exercise 9. The plant was reverted.
- [x] **The main window barely grows.** Both numbers come from `claude -p "/context"`:
  - a fresh session: Messages 10 tokens
  - the session after `/policy-review`, continued with `claude -c`: Messages 152 tokens

  So the forked review added 142 tokens to the main window. The diff and the reviewer's reading stayed in its own window.

## Agent or skill
- **The agent directly** when you want a worker on a task you describe in the moment, such as "review this file for the rules", and you don't need the procedure written down.
- **The skill** when the same procedure runs again and again, such as the pre-commit review, so the procedure is written down once and the main window only sees the verdict.

## Open
- **Rule 5 noise.** The reviewer also reported the new `<img>` element under rule 5 and then said it wasn't a string violation. Rule 5 should cover only visible text and user-facing attributes such as `alt`, `title` and `aria-label` that hold words. I haven't changed the agent yet, because that would need a rerun.

## Status
The skill runs forked onto the agent, finds the planted violation, and keeps the main window small. The rule 5 wording is still open.
