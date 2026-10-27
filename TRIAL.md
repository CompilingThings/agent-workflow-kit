# Trial: does the plug-and-play agent workflow work on a clean machine?

You are running in a fresh environment. This repo holds the workflow files (CLAUDE.md, .claude/agents, .claude/commands, .claude/hooks, ops/) and a tiny sample project (textstats/ with tests/, and its real input samples/notes.txt). CLAUDE.md § Project is already filled in for that sample.

**Run number:** the person who starts the trial names it, for example "this is run 3". Below, `N` is that number. No number given ⇒ use 1.

Do exactly this, using only the files in this repo and the tools a fresh machine has (git, Python 3, pytest if you install it with pip). Follow CLAUDE.md and each command file as written. Where a command step does not work as written, don't work around it silently: note it in TRIAL_REPORT.md and continue with the closest faithful step.

0. **Work from the repo root.** The session must be open in the folder that holds this file; project settings and the safety hook load only there. If it is not, say so in TRIAL_REPORT.md.
1. Run /startup as the command file `.claude/commands/startup.md` describes. If it reports `HOOK: ⚠ NOT LIVE`, record that as a FAIL in TRIAL_REPORT.md. Then go on: for this trial the owner rules "continue, and follow CLAUDE.md § Hard blocks by hand" (log it with /log RULING).
2. Run /plan for this work item: "add line_count(text) to textstats: the number of lines in text; an empty string has 0 lines; a trailing newline does not add a line". The plan covers line_count only. The plan goes through /review (a plan lands on one clean round).
3. Run /code on the approved plan: implement on its own branch, add tests, run them, commit, then /review (code lands on two clean rounds in a row). If Codex is not installed, or its test probe fails, reviewer A uses /review's fallback.
4. Merge as /review says, then run /log for one DECISION you made, then /shutdown (it runs /save itself; do not run /save separately).
5. Write TRIAL_REPORT.md: for each command and agent you used, PASS (worked as written) or FAIL (what broke, the exact step, and the fix you recommend). End with a verdict line: "PLUG AND PLAY: YES" or "PLUG AND PLAY: NO — <the blocking reasons>".

## The planted defect: it is there on purpose
The adjudicator's APPLY ruling and the fixer only run when a review finds a real defect, and a clean sample gives them nothing to do. So the sample carries one defect, planted on purpose:

- **What it is:** `textstats.word_count` splits on spaces only. Its docstring promises whitespace-separated words, but words separated by a newline or a tab are counted as one: `word_count("a\nb")` returns 1, not 2.
- **The real input it miscounts:** `samples/notes.txt`, named in CLAUDE.md § Project, has 10 words over 3 lines. The planted `word_count` returns 7 for it.
- **Why the code review should find it:** line_count goes into the same file, `textstats/__init__.py`. That makes the whole file part of the code review, and the review prompt has every reviewer run inputs meant to break the code.

Rules for the trial:
- Don't point any agent at the defect: never name it in a dispatch, and don't fix it yourself. This file sits in the repo, so a reviewer may read it. That is fine, because the trial tests how the review handles a real defect, not whether the defect can be hidden.
- Expected path: a reviewer reports the defect. The plan covers line_count only, so under CLAUDE.md § Scope the adjudicator rules it DEFER (off-target) and Boss adds a row for it to `ops/open-work.md`. A fix belongs in its own later plan, not in this gate.

In TRIAL_REPORT.md, record which of those happened. If no reviewer reports the defect, that is a FAIL of /review. If the defect is fixed inside this gate, that is a FAIL of the scope rule.

Commit everything (the branches, ops/, plans/, reviews/) in your clone, put TRIAL_REPORT.md on the branch `trial/run-N`, and stop. Use your own git identity, with no Co-Authored-By line. If a command needs an approval nobody is there to give, rewrite it so it doesn't, and record that in TRIAL_REPORT.md. Never wait for a person.
