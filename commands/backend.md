---
description: Switch Claude Code backend between multiple AWS Bedrock profiles.
allowed-tools: Bash, Read, Write, AskUserQuestion
---

# /backend - Multi-Backend Switcher

Manages routing between multiple AWS Bedrock accounts/profiles for Claude Code.

## Architecture

| Backend | Role | Cost | Model |
|---|---|---|---|
| **Profile A** | Enterprise/office work, internal tools | Free | claude-opus-4-7 |
| **Profile B** | Personal AI orchestration, planning | Paid | claude-sonnet-4-6 (default) |
| **Profile C** | Coding execution (separate CLI) | varies | n/a |

## Steps

1. Read current backend from `~/.claude/settings.json`:
   - Check `AWS_PROFILE` value to determine active backend

2. Use AskUserQuestion to confirm target backend. Options:
   - **Profile A** - for enterprise/office tasks
   - **Profile B** - for personal projects, planning (paid)
   - **Show current only** - just report, don't change

3. If switching:
   - Copy `~/.claude/settings.<target>.json` over `~/.claude/settings.json`
   - Verify with `diff ~/.claude/settings.<target>.json ~/.claude/settings.json`
   - Tell user: "Backend switched to <target>. **Restart Claude Code** to apply."
   - Show one-line cost reminder if switching to paid backend.

4. Never commit destructive changes without re-reading both files first.

## Files

- `~/.claude/settings.<profile-a>.json` - Profile A config (frozen reference)
- `~/.claude/settings.<profile-b>.json` - Profile B config (frozen reference)
- `~/.claude/settings.json` - active config (copied from one of the above)

## Rules

- Don't restart Claude Code yourself. Tell the user to do it.
- Don't edit `settings.json` field-by-field. Always copy from canonical source.
- Don't switch to external CLIs here. Those are separate processes.
