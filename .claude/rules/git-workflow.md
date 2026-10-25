# Git workflow

These rules replace the global git rules in `C:\Users\Hananya\.claude\CLAUDE.md` for this repository. Where they conflict, follow this file.

- Work directly on `main`. Do not create local branches for exercises, stories or homework. Pull with rebase before each push.
- Commit subjects follow the existing history: `Exercise N: functional title`, for example `Exercise 9: store each fund's daily NAV series (Story 1.1)`.
- Commit bodies say what matters and not what the diff already shows. Use bullets for key details and link docs or RFCs where they exist. Break lines at natural sentence boundaries.
- Don't GPG-sign commits. Use the default git signing configuration.
- Don't add co-author trailers.
- Commit finished work when the task is complete. Don't push unless asked.
- Never force-push `main`. Pull with rebase instead.
