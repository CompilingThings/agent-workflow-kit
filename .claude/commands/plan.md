---
description: Draft a plan into plans/<name>.md through the plan-drafter agent, on its own branch, then gate it with /review. A plan lands on 1 clean review round.
argument-hint: <name> — <what the plan must settle>
---

# /plan

**Args:** `$ARGUMENTS` — `<name>` (lowercase, dashes; becomes the file and branch name) and what the plan must settle.

## Steps
1. **Reason check.** The task must name the goal item it moves or unblocks (`CLAUDE.md` § How Boss works). None ⇒ stop and tell the owner.
2. **Branch.** From a clean main branch (plain `git`, same in Git Bash and PowerShell, one per call):
   ```
   git status --short --untracked-files=no   # must be empty
   git switch <main>
   git switch -c plan/<name>
   ```
   No `mkdir` needed: the Write tool creates `plans/` and `reviews/` when it first writes into them.
3. **Draft.** Dispatch `plan-drafter` with its INPUTS, filled exactly:
   - OUTPUT PATH: `plans/<name>.md`
   - MUST SETTLE: what the plan has to decide (from the args or the owner's words)
   - AUTHORITIES: the closed list of files and journal lines the plan is built from
   - READ-ONLY: files the drafter may read and cite but never edit, or `none`
   - REPORT PATH: `reviews/<name>_draft_report.md`
   - TEST COMMAND: the test command from `CLAUDE.md` § Project, in the form `/startup` reported for this host
4. **Accept or return.** Read the drafter's return. Each `UNSETTLED` item ⇒ Boss rules it (`/log` DECISION); a scope question goes to the owner with Boss's recommended answer (`/log` RULING). Then re-dispatch the drafter with the same INPUTS, those journal lines added to AUTHORITIES, until no item is UNSETTLED.
5. **Commit the draft** by name:
   ```
   git add plans/<name>.md
   git commit -m "plan: <name> draft"
   ```
6. **Review.** Run `/review plan <name>`. The plan lands on **1 clean round**.
7. **Merge when landed:**
   ```
   git switch <main>
   git merge --no-ff plan/<name> -m "plan: <name> landed"
   ```
8. **Record.** On the main branch, add a line to `ops/open-work.md` for the build (`/code <name>`), and commit it by name, so `/code` starts from a clean tree:
   ```
   git add ops/open-work.md
   git commit -m "open-work: <name> build row"
   ```
   The drafter's report is committed with the review records (`/review` step 8). Run `/save` if the context is getting full.

## The plan shape (plan-drafter writes it; reviewers check it)
```
# <Name>
## 1. Problem and root cause   — the wrong assumption, the symptom that showed it, and whether this plan fixes the cause (a symptom-only plan is not drafted)
## 2. Acceptance criteria      — each: observable behaviour · the command that proves it · RED: the state that makes it fail
## 3. Out of scope             — each with the reason
## 4. Deliverables             — 4.1, 4.2 … each: files touched, what changes, why this design (alternatives named)
## 5. Order and rollback       — build order; how to undo
## 6. Review log               — one line: "Review records: reviews/<name>-plan_r*.md"
```
**Size:** at most 100 content lines. Over ⇒ cut prose, never an acceptance criterion.
