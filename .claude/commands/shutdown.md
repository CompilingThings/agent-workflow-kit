---
description: Session end. Runs /save, then checks that nothing is uncommitted and nothing Boss or its agents started is still running, and reports SAFE or NOT SAFE.
---

# /shutdown

## Steps
1. **Save.** Run `/save` in full. This is the session's last `/save`, so don't run one separately just before `/shutdown`: that writes a second session-log entry with nothing between the two.
2. **Nothing uncommitted** (measured; plain `git`, same in Git Bash and PowerShell):
   ```
   git status --short
   git stash list
   ```
   Tracked changes ⇒ commit them by name (if finished and tested) or report them. Untracked files ⇒ list them. (`/save`'s working files, `reviews/save_facts.md` and `reviews/save_report.md`, are in `.gitignore`, so they never show here.)
3. **Nothing running.** List every background job and agent Boss started this session (Claude Code's background tasks, `codex exec` runs, test runs, dev servers). Each is either finished, or stopped by Boss now — only what Boss or its agents started; never a process the owner runs.
4. **Open review checkouts.**
   ```
   git worktree list
   ```
   A `review-<gate>` checkout for a gate that is still open is expected: name it in the report. One for a landed gate ⇒ remove it (`git worktree remove --force <path>`).
5. **Report**, this shape and nothing more:
   ```
   SHUTDOWN: SAFE | NOT SAFE
   uncommitted: <none | each path>
   running: <none | each job>
   open gates: <none | gate · round · clean streak>
   next task (from ops/board.md): <…>
   ```
   **SAFE** only if: `/save` committed, no tracked change is left, and nothing Boss started is still running. Anything else ⇒ **NOT SAFE**, with the reason on each line.
