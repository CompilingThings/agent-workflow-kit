#!/usr/bin/env python3
"""Hard-block hook for Claude Code (PreToolUse). Python 3 standard library only.

Claude Code sends the pending tool call as JSON on stdin. This script:
  - exits 2 to block the call (the message on stderr is shown to the agent),
  - exits 0 to allow it.
Exit 1 does not block in Claude Code - it only shows a warning - so every block here is exit 2.

Edit the two lists below for your project. The rules in CLAUDE.md bind whether or not
this hook catches a case; the hook is a backstop.
"""
import fnmatch
import json
import os
import re
import sys

# Commands that must never run. Python regular expressions, matched case-insensitively
# anywhere in a Bash or PowerShell command.
BLOCKED_COMMANDS = [
    (r"\bgit\s+push\b.*\s(--force|--force-with-lease|-f)\b", "force-push rewrites shared history"),
    (r"\bgit\s+push\b.*\s\+\S", "force-push (+refspec) rewrites shared history"),
    (r"\brm\s+(-\S+\s+)*-\S*[rR]\S*\s+(-\S+\s+)*['\"]?(/|/\*|~|~/|~/\*|\$HOME|\$HOME/|\$HOME/\*|[a-z]:[\\/]?\*?|/[a-z]/?\*?)['\"]?(\s|;|&|\||$)",
     "recursive delete of the root or home folder"),
    # PowerShell: Remove-Item (or an alias) with -Recurse, aimed at a drive root or the home folder.
    (r"\b(remove-item|ri|rm|rmdir|rd|del|erase)\b(?=[^;|&]*\s-r(ecurse)?\b)[^;|&]*\s['\"]?"
     r"(~|~[\\/]\*?|\$home|\$home[\\/]\*?|\$env:userprofile|\$env:userprofile[\\/]\*?|[a-z]:[\\/]?\*?|[\\/]\*?)"
     r"['\"]?(\s|;|&|\||$)",
     "recursive delete of the root or home folder"),
    (r"\bdrop\s+(table|database|schema)\b", "dropping a database table"),
]

# Paths that must never be written by Edit/Write, or by a shell command that writes.
# Glob patterns relative to the repo root, forward slashes. "*" also matches "/".
PROTECTED_PATHS = [
    "protected/*",  # example: replace with your production data or release outputs
]

# Shell words that write or delete a file (bash, then PowerShell cmdlets and aliases).
# A Bash or PowerShell command that names a protected path AND contains one of these
# is blocked. Matched case-insensitively.
SHELL_WRITE = (r"(>|\btee\b|\brm\b|\bmv\b|\bcp\b|\btruncate\b|\bsed\s+(-\S+\s+)*-i|\bdd\b"
               r"|\b(set|add|clear)-content\b|\bout-file\b|\b(remove|move|copy|new|rename)-item\b"
               r"|\b(del|erase|ri|move|copy|ren)\b)")

# Which input field holds the command or the file path, per tool.
COMMAND_TOOLS = ("Bash", "PowerShell")                        # tool_input.command
FILE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")   # tool_input.file_path / notebook_path


def block(reason):
    sys.stderr.write("BLOCKED by .claude/hooks/guard.py: " + reason + "\n")
    sys.exit(2)


def rel_to_repo(path, root):
    path = os.path.normpath(os.path.join(root, path))
    try:
        rel = os.path.relpath(path, root)
    except ValueError:  # different drive on Windows
        return path.replace("\\", "/")
    return rel.replace("\\", "/")


def is_protected(rel):
    return any(fnmatch.fnmatch(rel, pat) for pat in PROTECTED_PATHS)


def main():
    try:
        # utf-8-sig drops a byte-order mark: Windows PowerShell adds one when you pipe the
        # README's test line into this script by hand.
        event = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
    except ValueError:  # bad JSON or bad UTF-8 (UnicodeDecodeError is a ValueError)
        sys.stderr.write("guard.py: could not parse hook input; call allowed\n")
        sys.exit(1)  # warn, do not block

    tool = event.get("tool_name", "")
    args = event.get("tool_input") or {}
    root = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()

    if tool in COMMAND_TOOLS:
        command = args.get("command", "")
        for pattern, reason in BLOCKED_COMMANDS:
            if re.search(pattern, command, re.IGNORECASE):
                block(reason + ": " + command)
        if re.search(SHELL_WRITE, command, re.IGNORECASE):
            for pat in PROTECTED_PATHS:
                stem = pat.rstrip("*").rstrip("/")
                if stem and stem in command.replace("\\", "/"):
                    block("shell write to protected path " + pat + ": " + command)

    elif tool in FILE_TOOLS:
        path = args.get("file_path") or args.get("notebook_path") or ""
        if path and is_protected(rel_to_repo(path, root)):
            block("protected path " + path + " - write it only through its owner tool")

    sys.exit(0)


if __name__ == "__main__":
    main()
