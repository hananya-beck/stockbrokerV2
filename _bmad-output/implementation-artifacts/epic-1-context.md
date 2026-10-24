# Epic 1 Context: Keep a full NAV history

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

After this epic, the daily pipeline keeps every fund's full daily NAV series in one history file, merged across runs. A failed fetch never empties the history or silently drops a fund. The dashboard page is unchanged, so the epic delivers its value on its own: the history exists for the backtest that Epic 2 builds.

## Stories

- Story 1.1: Store each fund's daily NAV series
- Story 1.2: Merge each run into the stored history
- Story 1.3: Keep the last good data when a fetch fails
- Story 1.4: Commit the history and fund list together, atomically

## Requirements & Constraints

- Every successful run leaves one history file covering every fund in the fund list, with each fund's full daily series.
- Days are never removed by a successful run. When the source revises a close for a stored date, the new value wins.
- A failed fetch keeps that fund's previous data and marks it stale. A fund with no previous data is still listed, with no points.
- A run in which every fund fails writes nothing and exits with an error.
- The stored history for the seven current funds stays under 5 MB. This is a working target, checked by a test.
- All tests run offline. Nothing in the test suite may reach the network.

## Technical Decisions

- The producer is the only code that writes generated files under `data/`. The fund list is a human-written file that the producer reads.
- History file shape: keys are the fund ids from the fund list. Each fund has a stale flag and a list of `[date, close]` points sorted ascending by ISO date (`YYYY-MM-DD`). A missing trading day is an absent point, never a null.
- Every date in any file under `data/` is ISO. The source's day-first dates are converted in the producer only.
- A close must be a finite number above zero. Any other value is dropped, and the file is serialized so that non-finite values fail loudly rather than being written.
- Writes go to temp files in `data/` and are moved into place atomically. The history file moves first, and the fund-list file moves last.
- The commit path stages both generated files together. The workflow rebases before pushing.
- Existing producer behaviour to correct in this epic: the all-fail path currently rewrites the fund-list file, and the date in that file is written day-first.

## Cross-Story Dependencies

- 1.1 introduces the history file and its shape. 1.2 merges into that file. 1.3 relies on the merge and the previous-file read. 1.4 relies on the file shape and both writes.
- Epic 2 reads the history file at runtime. Epic 2 needs no Epic 1 story changed, but it cannot be exercised until 1.1 has produced a file.
