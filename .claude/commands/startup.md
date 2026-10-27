---
description: Session start. Reads CLAUDE.md and flags any unfilled § Project field, finds the test command form that runs on this host, reads ops/board.md and the journal tail, checks git (including a missing main branch), proves the safety hook is live (which also catches a session opened outside the repo root), lists open work and states the next task. No work before this.
---

# /startup

Run every step, in order, before any other work. Read-only: this command writes nothing and commits nothing (the one test run in step 2 leaves only its own cache files, which `.gitignore` covers). Every command below runs the same in Git Bash and PowerShell unless both forms are given; run them one per call.

## Steps
1. **Rules.** Read `CLAUDE.md` in full.
2. **Project filled in?** Look at the four fields in `CLAUDE.md` § Project: **Goal**, **Test command**, **Protected files**, **Main branch**. A field is unfilled if:
   - it still holds a `<…>` placeholder, or
   - the Goal starts with `(kit sample)` but the folder `textstats/` does not exist (the Glob tool on `textstats/*` finds nothing). That means the kit was copied into another repo and § Project still describes the sample, so all four fields count as unfilled.

   For each unfilled field, name it under ⚠ in the report, with how to fill it: "edit `CLAUDE.md` § Project, replace the value with yours (template: `README.md` § Install)". Any unfilled field ⇒ no work starts (step 10).

   **Test command form.** With § Project filled, run its test command once as written. The interpreter name differs between hosts: on Windows, `python3` is often missing. If the command cannot start (the shell says "not recognized" or "not found", or it says `No module named pytest`), try the same command with only the interpreter swapped, in this order: `py`, then `python`. The first form that starts is this host's form. It "starts" when it exits 0, or exits with test failures it reports itself.
   - Report it on the `TESTS:` line, with the runner's summary line.
   - Use that exact form for every TEST COMMAND you hand an agent this session, and in every review prompt.
   - Tests that run but fail ⇒ ⚠ "the main branch is red".
   - No form starts ⇒ ⚠ "no working test command on this host", with the fix, and no work starts (step 10). The fix: every form said `No module named pytest` ⇒ "install it: `<interpreter> -m pip install pytest`"; otherwise "install Python 3".
3. **Board.** Read `ops/board.md` in full. Its `## Next` block is the next task; `## Mid-flight` is work left half-done; `## Needs the owner` is open questions.
4. **Journal tail.** Read the last 30 lines of `ops/journal.md` with the Read tool. A RULING or CORRECTION newer than the board's `Last updated:` line outranks the board.
5. **Git.** Measure, never assume:
   ```
   git rev-parse --show-toplevel
   git branch --show-current
   git branch --list <main>
   git status --short
   git log --oneline -5
   git worktree list
   git stash list
   ```
   `<main>` is § Project's main branch. Each of these goes under ⚠ in the report, one line each:
   - uncommitted files;
   - an unexpected branch;
   - a leftover review worktree (`review-*` next to the repo);
   - a stash;
   - `git branch --list <main>` printing nothing. That means the main branch does not exist locally, and `/plan` and `/code` would build on the wrong base. Report it on its own line: "main branch `<main>` does not exist locally — fix: `git switch -c <main> origin/<main>` if the remote branch is the right base, or create it from the branch the owner names (record that with `/log` DECISION)".

   Do not clean anything up.
6. **Open work.** Read `ops/open-work.md`; list its open rows, one line each.
7. **Hook registered?** Read `.claude/settings.json`. It must exist, and its `PreToolUse` matcher must register `.claude/hooks/guard.py` for `Bash`, `PowerShell`, `Edit` and `Write`. A missing file, no `guard.py`, or a tool missing from the matcher ⇒ ⚠ "hook not registered for <tool>".
8. **Hook live?** A registered hook can still be off, for example when the session was opened outside the repo root. Prove it is on. Run this harmless command once with the Bash tool (or with the PowerShell tool if this host has no Bash tool):
   ```
   echo "guard probe: drop table nothing"
   ```
   It only prints text, but it matches a pattern on the guard's block list, so a live hook refuses it.
   - **Refused** with `BLOCKED by .claude/hooks/guard.py` ⇒ `HOOK: live`.
   - **It printed the text** ⇒ `HOOK: ⚠ NOT LIVE`. The shell's current folder can't tell where the session was opened (any `cd` changes it), so give both fixes, in this order: first "close this session and open Claude Code in the repo root (`<toplevel>` from step 5, the folder that holds `CLAUDE.md`), in a new session"; then "if it already was, check `.claude/settings.json` and the `python3` line in README § Windows notes". The hard blocks now have no backstop, so no work starts until the owner rules (step 10).
9. **Report to the owner**, in this shape and nothing more:
   ```
   PROJECT: filled | ⚠ unfilled: <each field> — edit CLAUDE.md § Project (template: README.md § Install)
   TESTS: <the form that runs here> · <the runner's summary line> | ⚠ the main branch is red | ⚠ no working test command on this host
   HOOK: live | ⚠ NOT LIVE — <the fix from step 8> | ⚠ not registered for <tool>
   NEXT TASK: <from the board's Next block, or "none set — owner to pick">
   MID-FLIGHT: <each item, or none>
   NEEDS THE OWNER: <each question, with Boss's recommended answer, or none>
   GIT: branch <name> · <n> uncommitted · <warnings or clean, each ⚠ from step 5 on its own line>
   OPEN WORK: <n> rows — <one line each, max 10>
   ```
10. **Only now may work start**, on the next task, unless the owner rules otherwise. No work starts while `PROJECT` shows an unfilled field, `TESTS` shows no working test command, or `HOOK` shows a ⚠, until the owner fixes it or rules to go on anyway (record that ruling with `/log` RULING). If the board names no next task, ask the owner, with Boss's recommended pick from the open work.

If `ops/` or any of its files is missing, report which, and offer to create the empty starter file. Do not invent its contents.
