---
description: The review gate. Freeze one commit; two independent reviewers (Codex or a second Claude reviewer, plus the Claude reviewer agent) read the same frozen files and the same fixed prompt; the adjudicator rules every finding APPLY / DEFER / DEAD; one fixer applies every APPLY row and commits; repeat. A plan lands on 1 clean round, code on 2 clean rounds in a row.
argument-hint: <plan|code> <name> [base-sha for code]
---

# /review

**Args:** `$ARGUMENTS` — `<kind>` (`plan` or `code`), `<name>`, and for code the BASE sha `/code` wrote down.

**Names used below:** `GATE` = `<name>-<kind>` · `BRANCH` = `plan/<name>` or `work/<name>` · `N` = the round number (1, 2, …) · `REVIEW_DIR` = a separate checkout outside the repo where the frozen files sit: the parent folder of `git rev-parse --show-toplevel`, plus `review-<GATE>`. Boss writes it, `SHA` and every `<…>` below as literal values, so each command is plain `git` (or `codex`) that runs the same in Git Bash and PowerShell, one per call; where the shells differ, both forms are given.
All records go in `reviews/` in the main checkout and are never inside what reviewers read.

## RULES
1. **Every round reviews the whole artifact** — never only the last fix.
2. **One prompt per gate**, `reviews/<GATE>_prompt.md`, written once in round 1 from § THE PROMPT and never edited. Only exception: a fix changed the list of files under review ⇒ write it again from the template (the count is already 0 after a fix).
3. **Both reviewers get the same prompt file and the same frozen commit.** The dispatch carries the prompt path and the output path, nothing else — no round number, no list of earlier findings, no hint what to look at, no mention of the other reviewer.
4. **Two output files every round.** Fewer ⇒ the round did not happen: re-run the missing reviewer on the same freeze. Never adjudicate one reviewer alone.
5. **The last non-empty line of each output is the verdict, closed list:** `FINAL_VERDICT: SHIP` or `FINAL_VERDICT: CHANGES_NEEDED`. Anything else ⇒ that reviewer failed: re-run it (a failed Codex run ⇒ step 3's fallback, not a second Codex run).
6. **Nothing is edited between freeze and the end of adjudication.** The branch moved during the round ⇒ the round is void: freeze again, same `N`.
7. **Boss never re-rules a finding.** The adjudicator rules; Boss accepts the record or returns it naming one concrete defect.
8. **One fixer per round, after adjudication, carrying every APPLY row.** Never one fixer per finding.
9. **Clean round** = both outputs exist with legal verdicts AND the record has zero APPLY rows. **Any APPLY ⇒ count 0.**
10. **Landing:** plan ⇒ 1 clean round. Code ⇒ 2 clean rounds in a row on the same commit (a clean round makes no change, so the next round re-checks the same bytes in fresh context).
11. **Third round of this gate with findings that share one root cause** (counted over the whole gate, not only rounds in a row) ⇒ stop fixing symptoms: Boss has the fixer fix the root, or, if the root is outside the plan's scope, takes that one scope question to the owner.
12. **Rule changes bind the next gate**, never a running one.

## STEPS — one round
**1. Set up (round 1 only).**
```
git worktree add --detach "<REVIEW_DIR>" <BRANCH>
```
Files under review: plan ⇒ `plans/<name>.md`. Code ⇒ the files the branch changed, leaving out the bookkeeping folders (`/log` and `/save` may commit `ops/` on a work branch, and `reviews/` holds the records):
```
git diff --name-only <base-sha>...<BRANCH> -- . ":(exclude)ops" ":(exclude)reviews"
```
Write `reviews/<GATE>_prompt.md` (the Write tool creates `reviews/`) from § THE PROMPT:
- fill every `[…]` slot;
- keep the one regime block that applies, without its `[CODE — …]` or `[PLAN — …]` label line;
- delete the other block and its label line;
- change nothing else.

Then check it: the Grep tool on `\[[A-Z_ ]+[\]—]` over the prompt file finds nothing. That pattern catches an unfilled slot or a label line left behind.

**2. Freeze.**
```
git status --short --untracked-files=no      # must be empty: everything reviewed is committed
git rev-parse <BRANCH>                       # = SHA
git -C "<REVIEW_DIR>" checkout --detach <SHA>
git hash-object reviews/<GATE>_prompt.md     # = PROMPT_HASH
git ls-tree -r <SHA> -- <each file under review>
```
Write `reviews/<GATE>_r<N>_freeze.txt` with the Write tool: lines `gate: <GATE>`, `round: <N>`, `sha: <SHA>`, `prompt: <PROMPT_HASH>`, then the `git ls-tree` output verbatim.
The prompt hash must equal round 1's (rule 2): the Grep tool on `^prompt:` over `reviews/<GATE>_r*_freeze.txt` shows one value.

**3. Run both reviewers at once, in the background.**
- **Reviewer A** is Codex if Codex is installed and can do this gate's job. Otherwise it is the `reviewer` agent. Decide once, in round 1, and write the choice on round 1's `A by:` line (§ THE RECORD). It holds for the whole gate.
  1. **Installed?** `codex --version` does not answer ⇒ reviewer A is the `reviewer` agent.
  2. **Code gate only: can Codex run the tests?** In round 1, after the freeze and before reviewer A starts, run the test command once through Codex in the frozen folder, with the sandbox the review uses:
     ```
     codex exec -C "<REVIEW_DIR>" -s workspace-write -c project_doc_max_bytes=0 -o reviews/<GATE>_codex_probe.md "Run this exact command in the current folder: <TEST COMMAND>. Reply with its exit code on the first line, as EXIT: <n>, then the last 10 lines of its output. Change no file. If the command cannot start, say why; do not run anything in its place."
     ```
     Read `reviews/<GATE>_codex_probe.md`. It must start with `EXIT: 0` and show the test runner's own summary line (for pytest, `<n> passed`). Any of the following ⇒ Codex can't run the tests on this host, and reviewer A is the `reviewer` agent for this gate. Put the probe's first line on the `A by:` line.
     - the probe file is missing;
     - the exit code is not 0;
     - there is no summary line;
     - the text says the command was "not recognized" or "not found", or a module is missing.

     Seen in one trial run on a Windows 11 host (October 2026): inside Codex's sandbox `python3` was not recognized and the only Python had no pytest, yet Codex still returned SHIP after calling the test functions by hand.
  3. **Otherwise reviewer A is Codex.** `<SANDBOX>` is `read-only` for a plan gate and `workspace-write` for a code gate, so the tests can run; writes stay inside the throwaway `REVIEW_DIR`. `-o` makes Codex write its final answer to the file itself, as UTF-8. `project_doc_max_bytes=0` keeps any `AGENTS.md` out, so the prompt is all it gets.
     ```
     Git Bash:   codex exec -C "<REVIEW_DIR>" -s <SANDBOX> -c project_doc_max_bytes=0 -o reviews/<GATE>_r<N>_A.md - < reviews/<GATE>_prompt.md 2> reviews/<GATE>_r<N>_A.log
     PowerShell: $OutputEncoding = [Text.UTF8Encoding]::new($false); Get-Content -Raw -Encoding utf8 reviews/<GATE>_prompt.md | codex exec -C "<REVIEW_DIR>" -s <SANDBOX> -c project_doc_max_bytes=0 -o reviews/<GATE>_r<N>_A.md - 2> reviews/<GATE>_r<N>_A.log
     ```
     **A Codex run fails** if it exits non-zero, writes no output file, ends its output on an illegal last line, or writes a `TESTS NOT RUN:` line (step 4). Then don't run Codex again. Run reviewer A as the `reviewer` agent on the same freeze, use it for the rest of the gate, and give the reason on the record's `A by:` line.
  - **The `reviewer` agent as reviewer A:** dispatch it (fresh context) with the wrapper below and the output `reviews/<GATE>_r<N>_A.md`.
- **Reviewer B** — dispatch the `reviewer` agent with this wrapper, complete:
  ```
  PROMPT FILE: <abs path>/reviews/<GATE>_prompt.md
  OUTPUT FILE: <abs path>/reviews/<GATE>_r<N>_B.md
  ```

**4. Collect.** Read the last non-empty line of `reviews/<GATE>_r<N>_A.md` and `reviews/<GATE>_r<N>_B.md`. Run `git rev-parse <BRANCH>`: equal to the freeze file's `sha:` ⇒ FROZEN-OK, otherwise VOID.
A missing file or illegal last line ⇒ rule 4/5. `VOID` ⇒ rule 6.
Code gate: the Grep tool on `^TESTS NOT RUN:` over both output files. A hit means that reviewer never ran the test command, so its review doesn't count:
- **Codex** ⇒ step 3's fallback.
- **The `reviewer` agent** ⇒ re-run it once on the same freeze. A second hit ⇒ stop and tell the owner that the test command cannot run in review on this host, quoting the line.

**5. Adjudicate — every round, whatever the verdicts.** Two `SHIP` verdicts can still carry Deletions or Deferred-hardening items, and deciding that a review "has no findings" is itself a ruling (rule 7). So Boss never writes the record; dispatch `adjudicator` with its INPUTS, filled exactly:
- REVIEW FILES: `reviews/<GATE>_r<N>_A.md`, `reviews/<GATE>_r<N>_B.md`
- FREEZE FILE: `reviews/<GATE>_r<N>_freeze.txt` and `REVIEW_DIR` (where the frozen bytes are)
- CONTRACT FILES: `CLAUDE.md`, `plans/<name>.md` (code gate), plus any spec the plan cites
- OUTPUT PATH: `reviews/<GATE>_r<N>.md`

**6. Name the result.** Count APPLY rows and apply rules 9 and 10. With the Edit tool (never shell redirection), add step 3's `A by:` line under the record's `freeze:` line, and the result line as the record's last line:
```
RESULT: <CLEAN|FIX> · clean streak <0|1|2> of <1|2> · GATE: <LANDED|OPEN>
```
Check rule 11 before any fix.

**7. Fix (any APPLY).** Dispatch one `fixer` with its INPUTS, filled exactly:
- RECORD PATH: `reviews/<GATE>_r<N>.md`
- APPLY ROWS: the row ids ruled APPLY
- BRANCH and FILES: `<BRANCH>` and the files under review
- TEST COMMAND: `CLAUDE.md` § Project's, in the form `/startup` reported for this host, or `n/a (plan)`
- REPORT PATH: `reviews/<GATE>_r<N>_fix.md`

Accept it only after Boss measures: `git log --oneline -1 <BRANCH>` shows the fix commit, and the test command is green when Boss runs it. Then round `N+1` from step 2.

**8. Landed.**
```
git worktree remove --force "<REVIEW_DIR>"
```
Go back to `/plan` step 7 or `/code` step 8 to merge. After the merge, on the main branch: for every row any round of this gate ruled DEFER as "off-target", add one row to `ops/open-work.md` with the Edit tool, naming the finding and its record (`CLAUDE.md` § Scope). It waits until now because an edit on the branch mid-gate would block the next freeze or change the frozen commit. Then commit the records by name: the round files, plus the drafter's report (plan gate) or the implementer's report (code gate):
```
git add reviews/<GATE>_*
git add reviews/<name>_draft_report.md        # plan gate
git add reviews/<name>_build_report.md        # code gate
git add ops/open-work.md                      # if off-target rows were added
git commit -m "review records: <GATE> landed"
```

## THE RECORD — `reviews/<GATE>_r<N>.md`
```
# <GATE> round <N>
freeze: reviews/<GATE>_r<N>_freeze.txt · A: <SHIP|CHANGES_NEEDED> · B: <SHIP|CHANGES_NEEDED>
A by: <codex | reviewer agent — why: Codex not installed / probe <first line> / Codex run failed: <how>>   (Boss adds this line, step 6)
| id | reviewer | finding (one line) | ruling | reason | change required |
|----|----------|--------------------|--------|--------|-----------------|
RESULT: …
```

## THE PROMPT
Fill `[TITLE]`, `[REVIEW_DIR]`, `[FILES]`, and for code `[PLAN PATH]` and `[TEST_COMMAND]` (the form `/startup` reported as working on this host).
```
[TITLE] — independent review.

The frozen files are in this folder: [REVIEW_DIR]
Files under review:
[FILES]

Review the whole artifact: every claim, every value, every check, every instruction. Assume no
part of it has been reviewed before. Name each file under review in your answer, with what you
executed or verified in it. Do not edit any file.

SCRATCH — if you need scratch files (copies, test inputs, broken variants), first create one new
folder of your own: Git Bash `mktemp -d`, PowerShell
`New-Item -ItemType Directory (Join-Path $env:TEMP ([guid]::NewGuid()))`. Write, copy and delete
only inside that folder: every scratch file goes there, including backups and copies of anything
you change to test it. Never use a fixed path such as /tmp/orig.py. Apart from that folder, your
output file, and the cache files the test command itself leaves in the frozen folder, never
create, change or delete anything. Another reviewer may be working at the same time.

FINDINGS — return CHANGES_NEEDED for these four kinds only:
1. A wrong value in OUTPUT — anything the artifact prints, writes, or hands to a person.
2. A check that cannot fail — no input exists that makes it go red.
3. A measuring step that cannot detect what it claims to detect.
4. Code that contradicts a stop or safety rule the artifact states.
Everything else is a DELETION: one line under a "Deletions" heading, and SHIP anyway.
Put CHANGES_NEEDED findings under a heading whose first word is "Findings", numbered.

EVIDENCE — a finding counts only if its input really happens. Either show where it occurs (the
file and the actual line or record), or name the real configuration or recorded state that
produces it (file + field). An input you invented with no such chain goes under "Deferred
hardening", one line each, and you SHIP anyway. The written spec decides WHAT is correct; cite
the line it violates. It never proves that the input occurs.

[CODE — keep for a code review]
Spec: [PLAN PATH], in the frozen folder. It is the written spec that decides what is correct.
Run, from the frozen folder: [TEST_COMMAND]. Those tests must pass. If that command cannot run
exactly as written (the command is not found, a module is missing, anything stops it), do not
work around it, and do not call test functions by hand in its place. Write this line on its
own: TESTS NOT RUN: <what stopped it>. Then end with FINAL_VERDICT: CHANGES_NEEDED. SHIP is legal
only after the test command itself ran.
Before you call anything a deletion or return SHIP, build and run an input meant to make the
output wrong or a check fail. Report the input and what came out. Known-good inputs alone are
not enough. If you return SHIP, state what you ran: commands, inputs, outputs.

[PLAN — keep for a plan review]
The plan under review is itself the spec; it must agree with the files it cites.
Simplify first. Flag only material issues that affect the quality of the end result.
No speculative what-ifs. No implementation nits unless they create a real correctness risk.
Keep the intended design and scope; do not expand it. Flag over-specification: name what to
cut; do not rewrite or redesign.
Before you call anything a deletion or return SHIP, build the case that would make the design
produce a wrong result or leave a check unable to fail, and trace it by hand through the files
it cites. Report the case and where it came out. If you return SHIP, state what you verified:
each claim, the source you checked it against, what you found.

End with exactly one of these on its own final line, nothing after it:
FINAL_VERDICT: SHIP
FINAL_VERDICT: CHANGES_NEEDED
```
