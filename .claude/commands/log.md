---
description: Append one dated RULING, CORRECTION or DECISION line to ops/journal.md, with the reason; the owner's words quoted verbatim. Append-only.
argument-hint: <RULING|CORRECTION|DECISION> <text>
---

# /log

**Args:** `$ARGUMENTS` — the kind and the content.

## What gets logged
| Kind | When | Who said it |
|---|---|---|
| `RULING` | The owner decided something: a rule, a scope, a choice between options. | The owner, quoted verbatim. |
| `CORRECTION` | Something said or written earlier was wrong. Names the wrong line's date and what was wrong. | Whoever found it. |
| `DECISION` | Boss decided something inside its authority that a later session must know. | Boss. |

**Not logged:** a rule the owner merely repeated (apply it and point to the earlier line) · routine progress (that is the board's job) · Boss's instructions to an agent.

## Steps
1. **Get the date** — measured, never recalled: Git Bash `date +%Y-%m-%d` · PowerShell `Get-Date -Format yyyy-MM-dd`.
2. **Check it is new:** search `ops/journal.md` with the Grep tool (case-insensitive) for two or three key words of the ruling. Already there ⇒ do not log again; cite the existing line.
3. **Append one line with the Edit tool.** Read `ops/journal.md`; `old_string` = its last line exactly (add the lines above it until it is unique); `new_string` = that same text, a newline, then the new line. The Edit tool keeps the file UTF-8.
   **Never the Write tool on `ops/journal.md`** — Write replaces the whole file, and a lost journal cannot be recovered. **Never shell redirection** (`>>`, `Add-Content`, `Out-File`) — PowerShell can write UTF-16 or a BOM into the file. Never edit, reorder or delete an existing line; a wrong line gets a new CORRECTION line.
   Shapes:
   - `- <date> RULING — owner: "<exact words>" — means: <…> — reason: <…>`
   - `- <date> CORRECTION — <date of the wrong line>: "<what it said>" was wrong; correct: <…> — evidence: <command or file>`
   - `- <date> DECISION — <what Boss decided> — reason: <…>`
4. **Verify** the line landed and nothing above it moved: Read the last 3 lines of `ops/journal.md`, then
   ```
   git diff --numstat ops/journal.md     # additions only: the second number (lines deleted) must be 0
   ```
5. **Follow-on work.** A ruling that creates work adds its row to `ops/open-work.md` in the same turn.
6. **Commit** by name (same in both shells):
   ```
   git add ops/journal.md ops/open-work.md
   git commit -m "journal: <kind> <date>"
   ```
