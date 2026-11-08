---
name: policy-review
description: Reviews the uncommitted change against the AGENTS.md policy, in the policy-reviewer's own window, and returns only its verdict. Use when the user asks to review a change or check a diff against the rules, for example "review my change", "check my diff against the policy" or "does this break the rules". Not for bug or code-quality review, and not for the full pre-release audit, which is policy-audit.
context: fork
agent: policy-reviewer
---
Review the change below against the policy in AGENTS.md, using the rules in your instructions. Read each changed file before you judge it. Reply with your verdict only.

Changed files:
!`git diff --name-only`

Diff:
!`git diff`
