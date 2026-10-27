# A lead agent, a review gate, and a written memory for Claude Code

One lead agent (we call it **Boss**) runs your project for you. It plans work, sends the real work to small helper agents, has every plan and every code change reviewed by two independent reviewers, and writes down what happened so the next session picks up where this one stopped. You (the **owner**) set the goals and make the rulings.

Plug-and-play is the aim: copy the files, fill in four lines, and start. `TRIAL.md` is the check. Open Claude Code in a fresh clone of this repo and ask it to follow `TRIAL.md`, to watch the whole loop work on your machine before you install the kit in your own project.

Needs: Claude Code, git, Python 3. Optional: the Codex CLI (`codex`), used as the second, independent reviewer.
Tested with: Windows 11 Pro, Claude Code 2.1, Codex CLI 0.159 (trial runs, October 2026). The trial results are not published here; run `TRIAL.md` to get your own. Not tested: macOS and Linux.

## Install
Four steps, in this order:
1. **Copy the kit files into your repo root:** `CLAUDE.md`, `.claude/` and `ops/`, next to your code. Leave out the sample (`textstats/`, `tests/`, `samples/`, `pyproject.toml`, `TRIAL.md`). Keep the MIT licence notice with the copied files, for example by copying `LICENSE` as `LICENSE-agent-workflow-kit`. If you already have a `CLAUDE.md` or `.claude/settings.json`, merge by hand.
2. **Fill in the two places that describe your project.**
   - **`CLAUDE.md` § Project.** It ships filled in for the sample project (`textstats/`). Replace the four lines with yours, starting from this template:
     ```
     - **Goal:** <one sentence: what this project must deliver>
     - **Test command:** <e.g. `pytest -q`, `npm test`> — the one command that must stay green.
     - **Protected files:** <files only one named tool may write, e.g. production data, release outputs> — also listed in `.claude/hooks/guard.py`.
     - **Main branch:** <main>
     ```
   - **`.claude/hooks/guard.py`:** the lists at the top (commands and paths that must never run or be written).
   - **On Windows,** check the hook line in `.claude/settings.json` (see Windows notes below).

   Merge the `.gitignore` lines into yours.
3. **(Optional) Install the Codex CLI** and log in. If `codex` is on your PATH, it becomes reviewer A. Without it, or when it cannot run your tests in its sandbox (checked before every code review), a second Claude reviewer in fresh context takes its place.
4. **Open Claude Code in your repo root** (the folder that holds `CLAUDE.md`) **and type `/startup`.** Opened in any other folder, Claude Code loads neither the project settings nor the safety hook, and usually doesn't know `/startup` either. If `/startup` is not recognised, you are in the wrong folder.

**How you know the install worked:** `/startup` reports `HOOK: live` (it sends one harmless command the hook must refuse, and warns you if the command ran), shows your own test command passing, and names no unfilled § Project field. It names any field still holding a `<…>` placeholder, or still describing the sample when `textstats/` is absent, and no work starts until those are filled.

The sample has one bug planted on purpose, so a trial can check how the review handles a real defect. `TRIAL.md` describes it, and it has nothing to do with your code.

## Windows notes
- **`python` vs `python3`:** on Windows the name `python3` may be missing, or may open the Microsoft Store stub instead of your real Python.
  - **The test command:** nothing to do. `/startup` tries the command as written, then `py`, then `python`, and uses the first form that runs for the whole session.
  - **The hook line** in `.claude/settings.json` calls `python3`. If `python3 --version` does not print a version, change `python3` in that line to `python` (or `py`). `/startup`'s live hook check tells you if the hook is not running.
- **Codex on Windows:** Codex runs the tests inside its own sandbox, which may not see the Python and pytest your shell sees. Before the first round of every code review, `/review` checks this by having Codex run the test command once. If Codex can't run it, a second Claude reviewer takes its place for that review, and the review record says why. Nothing to do yourself.
- **Shell:** on some Windows hosts the Git Bash shell hangs on every command, even `echo hi`. If that happens, PowerShell is the safer shell. Every command works in both: its commands are plain `git`, or give the Git Bash and PowerShell forms side by side, and file appends use Claude Code's Edit tool, never `>>`.

## What each piece does
| Piece | Job |
|---|---|
| `CLAUDE.md` | Boss's rulebook. Loaded every session. Short on purpose. |
| `/startup` | Reads the rulebook, flags any unfilled § Project field, finds the test command form that runs on this machine, reads the board and the journal tail, checks git (including a missing main branch), proves the safety hook is live, states the next task. No work before it. |
| `/plan <name>` | The plan-drafter agent writes `plans/<name>.md`; then `/review` checks it. |
| `/code <name>` | The implementer agent builds an approved plan on its own branch; tests run; commit; then `/review`. |
| `/review <plan\|code> <name>` | The review gate (below). |
| `/log` | Appends one dated line to `ops/journal.md`: a RULING, CORRECTION or DECISION, with the reason. |
| `/save` | Before a context compaction: the state-writer agent updates `ops/board.md` and `ops/session-log.md`; they are committed. (At the end, `/shutdown` runs it for you.) |
| `/shutdown` | `/save`, then checks nothing is uncommitted or still running; reports SAFE / NOT SAFE. |
| `.claude/agents/` | plan-drafter, implementer, reviewer, adjudicator, fixer, state-writer. Each refuses a request missing its INPUTS and returns only verdict, blockers and evidence paths. |
| `.claude/hooks/guard.py` | Blocks a short list of commands that cause damage you cannot undo. |
| `ops/` | The written memory: journal (rulings), open-work (the to-do list), board (what is next), session-log (what happened). |

## The review gate, in one paragraph
A plan or a code change is **frozen** at one commit. Two reviewers who never see each other read the same frozen files and the same fixed prompt: **reviewer A** is Codex (or a second Claude reviewer), **reviewer B** is the Claude reviewer agent. Each ends with `SHIP` or `CHANGES_NEEDED`. An **adjudicator** agent, in fresh context, rules every finding **APPLY** (a real defect that changes the result: fix it), **DEFER** (not proven to happen, or outside this change's scope: note it) or **DEAD** (changes nothing: drop it). One **fixer** applies every APPLY row in one pass and commits. A round with zero APPLY rows is **clean**. **A plan lands on 1 clean round; code lands on 2 clean rounds in a row.** Only then is the branch merged, with plain `git merge --no-ff`.

## How a day runs
1. `/startup` → Boss tells you the next task from `ops/board.md`.
2. You agree, or rule something else. Your rulings go to `ops/journal.md` via `/log`.
3. `/plan <name>` → `/review plan <name>` → lands.
4. `/code <name>` → `/review code <name>` → lands → merged.
5. `/save` whenever the context is getting full; `/shutdown` at the end (it saves too).

## About the hook
Claude Code runs `guard.py` before every Bash, PowerShell, Edit and Write call (and MultiEdit, NotebookEdit). **Exit code 2 blocks the call** and shows the reason to the agent. **Exit code 1 does not block** — Claude Code shows the message and carries on. `guard.py` uses exit 2 for every block. The hook is a backstop, not the rule: the rules in `CLAUDE.md` bind whether or not the hook catches them.

`/startup` tests it live every session with a harmless command. To test it yourself, ask Claude to run this, and Claude Code should refuse it:
```
echo "guard probe: drop table nothing"
```
It only prints text, so nothing happens even if the hook is off. Never test the hook with a real destructive command. You can also feed the script by hand, from the repo root:
```
Git Bash:   echo '{"tool_name":"Bash","tool_input":{"command":"git push --force"}}' | python3 .claude/hooks/guard.py; echo "exit=$?"
PowerShell: '{"tool_name":"PowerShell","tool_input":{"command":"git push --force"}}' | python .claude/hooks/guard.py; "exit=$LASTEXITCODE"
```
Expect `exit=2`.
