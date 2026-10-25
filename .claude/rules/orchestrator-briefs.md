---
paths:
  - "prompts/**"
---

# Orchestrator briefs grant every file a story names

Added 2026-10-25. Reason: the exercise 10 orchestrator run log, Story 1.4. Session `f247599d-0588-4552-afba-b905159d3faf` was blocked because its acceptance criteria name `.claude/skills/add-fund/SKILL.md`, but the brief gave no permission for that path, and the headless launch denied the write. Retro process lesson P3.

- Before launching a story session, list every file its acceptance criteria name. Each path under `.claude/` needs an explicit grant in the launch, because the headless permission mode denies those writes by default.
- A brief that says "stay in scope" without listing the files is incomplete. Stop and fix the brief before launching.

**Bad**

```text
Build Story 1.4. Stay in scope.
```

**Good**

```text
Build Story 1.4. Its criteria name these files; you may edit each:
- scripts/fetch_data.py
- .github/workflows/update-data.yml
- .claude/skills/add-fund/SKILL.md
```

Not enforced by a test. The check is at launch time: the orchestrator compares the story's named files against the grant before it starts the session.
