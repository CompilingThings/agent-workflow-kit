---
description: Save the session state before a context compaction or at session end. The state-writer agent updates ops/board.md and ops/session-log.md from measured git state and this session's facts; Boss checks and commits those files by name.
---

# /save

Run it before a context compaction, and after any landing or ruling that moves the next task. At session end run `/shutdown` instead: it calls `/save` itself. The test: **a new session with no memory of this one must be able to resume from `ops/` and git alone.**

## Steps
1. **Collect this session's facts** (Boss, from its own context, with the Write tool, which creates `reviews/` if needed) into `reviews/save_facts.md`. It is overwritten each time and never committed (`.gitignore` lists it):
   - what landed (gate names, merge commits)
   - what is mid-flight (branch, gate, round, clean streak, next step)
   - rulings logged this session (journal dates)
   - what needs the owner (each with Boss's recommended answer)
   - the next task
   - what went wrong or was corrected — the honest part, not only the wins
2. **Dispatch `state-writer`** with its INPUTS, filled exactly:
   - FACTS FILE: `reviews/save_facts.md`
   - BOARD: `ops/board.md`
   - SESSION LOG: `ops/session-log.md`
   - REPORT PATH: `reviews/save_report.md`
3. **Check** (Boss, measured): `git diff --stat ops/board.md ops/session-log.md`, then Read the first 25 lines of `ops/board.md`. The board's `## Next` names one task; `## Mid-flight` matches `git branch` and the open review gates; the session log gained one entry and lost nothing. A defect ⇒ return to `state-writer` naming that one defect.
4. **Commit** by name (plain `git`, same in Git Bash and PowerShell):
   ```
   git add ops/board.md ops/session-log.md
   git commit -m "save: board + session log"
   ```
   If the current branch is a `plan/` or `work/` branch, commit these on it anyway; they merge with it. Never leave them uncommitted.
