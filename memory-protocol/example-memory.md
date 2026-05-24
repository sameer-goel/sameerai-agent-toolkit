---
name: feedback-no-force-push
description: Never force-push to main without explicit confirmation, even when rebasing
metadata:
  type: feedback
---

Never force-push to main/primary branches without explicit user confirmation.

**Why:** User lost work when an automated rebase + force-push overwrote a colleague's commit that hadn't been fetched locally. The commit was unrecoverable for 3 hours until someone found it in reflog on another machine.

**How to apply:** When a rebase results in divergence from remote, always show the user the delta (commits that would be lost) and ask for confirmation. Suggest `--force-with-lease` over `--force` when force-push is necessary. Never automate force-push in scripts or hooks.
