# Memory Protocol

A structured persistence layer for AI coding agents. Three tiers with clear scope, pruning rules, and capture triggers.

## Layers

### Semantic Memory (permanent, cross-session)

Path: `~/.claude/projects/<slug>/memory/`

Index: `MEMORY.md` (loaded every session, max 200 lines)

Individual memories as `.md` files with YAML frontmatter:

```yaml
---
name: short-kebab-slug
description: one-line summary (used for relevance matching)
metadata:
  type: user | feedback | project | reference
---

Memory content here. Link related memories with [[other-name]].
```

**Types:**
- `user` - who the user is, their role/expertise/preferences
- `feedback` - corrections and confirmed approaches (rule + why + how to apply)
- `project` - ongoing work state, decisions, deadlines
- `reference` - pointers to external systems (URLs, tools, dashboards)

### Episodic Memory (per-session, auto-pruning)

Path: `~/.claude/episodic/<sessionId>/facts.md`

Timestamped facts captured automatically:
```
2026-05-13T05:37:46Z [decision] User chose named tab files + size/TTL pruning
2026-05-13T05:42:51Z [file] Updated: CLAUDE.md (Context Memory Protocol)
2026-05-13T07:07:00Z [correction] Caveman mode must state intent before tool calls
```

**Capture triggers:**
- User corrects an approach (type: `correction`)
- Architecture/design decision made (type: `decision`)
- Files created/edited (type: `file`)
- Significant commands run (type: `cmd`)
- Before context compaction (type: `summary`)

**Pruning rules:**
- Max 50 facts per session
- Auto-archive after 7 days
- Delete after 30 days

### Working Memory (current turn only)

Lives in conversation buffer. Lost on context compaction unless captured to episodic layer via pre-compaction hook.

## Auto-Capture Script

```bash
#!/bin/bash
# episodic.sh capture <sessionId> <type> "<fact>"
SESSION_DIR="$HOME/.claude/episodic/$2"
mkdir -p "$SESSION_DIR"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [$3] $4" >> "$SESSION_DIR/facts.md"
```

## What NOT to save

- Code patterns derivable from reading the project
- Git history (use git log)
- Debugging solutions (the fix is in the code)
- Anything in CLAUDE.md files
- Ephemeral task details only useful this session

## Retrieval

Every session start loads:
1. Full `MEMORY.md` index (semantic layer)
2. Current session's episodic facts (if resuming)
3. Working memory from conversation

Agent announces loaded context in first response:
```
Loaded: N memory files, topics: [list]
Episodic: N facts (sessionId=...)
Project: <name> (<branch>)
```
