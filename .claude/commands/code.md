---
description: Build a landed plan on its own branch through the implementer agent, run the project's tests, commit, then gate the change with /review. Code lands on 2 clean review rounds in a row.
argument-hint: <name> — the landed plan plans/<name>.md
---

# /code

**Args:** `$ARGUMENTS` — `<name>` of a plan that has landed (merged into the main branch).

Every command below is plain `git` (or your test command) and runs the same in Git Bash and PowerShell; run them one per call.

## Steps
1. **Plan check.** `plans/<name>.md` exists on the main branch (`git log --oneline <main> -- plans/<name>.md` shows a commit) and its review record shows it landed (the Grep tool finds `GATE: LANDED` in `reviews/<name>-plan_r*.md`). Not landed ⇒ stop: run `/plan` / `/review plan` first.
2. **Branch.**
   ```
   git status --short --untracked-files=no   # must be empty
   git switch <main>
   git switch -c work/<name>
   git rev-parse HEAD            # the BASE sha — write it down; /review needs it
   ```
3. **Build.** Dispatch `implementer` with its INPUTS, filled exactly:
   - PLAN PATH: `plans/<name>.md`
   - SECTIONS: the § 4.x deliverables in scope (all of them, unless split)
   - FILES YOU OWN: the closed list of files it may create or edit
   - TEST COMMAND: the test command from `CLAUDE.md` § Project, in the form `/startup` reported for this host, plus any test paths the plan names
   - RULINGS: journal lines that settle earlier deviations, or `none`
   - REPORT PATH: `reviews/<name>_build_report.md`

   Deliverables that touch **separate** files may go to separate implementers in parallel, each with its own FILES YOU OWN. Never two implementers on one file.
4. **Accept or return.** A `DEVIATION` or `BLOCKER` in the return ⇒ Boss rules it with `/log` DECISION (scope ⇒ the owner, `/log` RULING); the implementer applies nothing of a deviation until ruled. Then re-dispatch with the same INPUTS and those journal lines as RULINGS. A ruling that changes what the plan says ⇒ amend the plan and land it again through `/review plan` first.
5. **Measure the tests yourself** — the implementer's green is UNPROVEN until Boss runs it:
   ```
   <test command>
   ```
   Red ⇒ re-dispatch the implementer with the same INPUTS. A failure that also fails on the BASE sha is pre-existing: note it in `ops/open-work.md` (it is committed in step 6), do not fix it here.
6. **Commit** by name (never `git add -A`). `/review` needs a clean tree to freeze:
   ```
   git status --short
   git add <each file from FILES YOU OWN that changed>
   git add ops/open-work.md        # only if step 5 noted a pre-existing failure
   git commit -m "<name>: build"
   ```
7. **Review.** Run `/review code <name>` with the BASE sha from step 2. Code lands on **2 clean rounds in a row**.
8. **Merge when landed:**
   ```
   git switch <main>
   git merge --no-ff work/<name> -m "<name>: landed"
   <test command>                # green on the main branch, measured
   ```
9. **Record.** On the main branch, close the row in `ops/open-work.md` and commit it by name (`/save` commits only the board and the session log):
   ```
   git add ops/open-work.md
   git commit -m "open-work: <name> closed"
   ```
   Then `/save`, unless the session ends here: `/shutdown` runs `/save` itself, so never run `/save` just before it.
