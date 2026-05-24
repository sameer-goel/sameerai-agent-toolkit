---
description: Task router. Classify intent and recommend which backend/agent should handle it.
allowed-tools: Read, AskUserQuestion
---

# /route - Task Router

Classify a user's task and dispatch to the correct execution backend. Human-in-the-loop approval required before routing.

## Classification Rules

| Signal | Route |
|---|---|
| Enterprise tools, internal services, CRM, email, calendar | **Profile A** (free tier) |
| Code editing, refactoring, debugging, building features, tests | **Coding CLI** (dedicated) |
| Planning, architecture, brainstorming, research, specs, orchestration | **Orchestrator** (stay here) |
| Status check, quick question, concept explanation | **Orchestrator** (low cost) |
| Mix of above | Orchestrator for planning, then split sub-tasks per backend |

## Flow

1. Read user's task description from `$ARGUMENTS` or ask if empty.
2. Classify task type.
3. State reasoning in 2 sentences max.
4. Ask user: "Route this to <backend>?" with options: Approve / Override / Cancel
5. If approved:
   - **Profile A** - tell user to switch backend, restart, re-ask
   - **Coding CLI** - write task spec to `.tasks/<slug>.md`, tell user to launch
   - **Orchestrator** - handle here
6. Log decision to `~/.claude/routing-log.jsonl` with timestamp + task + decision.

## Output format

```
ROUTE: <backend>
WHY: <one sentence>
ACTION: <what user does next>
```

## Rules

- Don't auto-execute coding tasks even if coding CLI is the route. Hand off.
- Don't switch backend yourself. Use `/backend` for that.
- Don't skip human approval step.
