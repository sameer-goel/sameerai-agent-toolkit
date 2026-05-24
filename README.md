# SameerAI Agent Toolkit

A production-tested infrastructure layer for AI coding agents. Routes tasks across models, discovers and invokes skills automatically, persists memory across sessions, and bridges multiple AI backends.

Built on Claude Code + AWS Bedrock. Running daily as a real development workflow since May 2026.

## What This Does

| Component | What it solves |
|-----------|---------------|
| **Model Router** | Classifies every prompt and routes to the right model tier (Haiku for reads, Sonnet for dev, Opus for architecture/security). Keyword-matched in <50ms, no LLM call needed. |
| **Skill Matcher** | Scans user intent against all registered skills, ranks by relevance, injects top matches so the agent considers invoking them before acting. |
| **Backend Switcher** | Manages multiple AWS Bedrock profiles (free/paid/isolated) with one command. Swap between accounts without restarting your brain. |
| **Task Router** | Classifies tasks and dispatches to the right execution backend (planning vs coding vs enterprise tooling). |
| **Memory Protocol** | Layered persistence: semantic memory (cross-session), episodic memory (per-tab, auto-pruning), working memory (current turn). Structured capture with frontmatter. |
| **Context Save/Restore** | Checkpoint your working state (git, decisions, remaining work) and resume in any future session without context loss. |

## Architecture

```
User Prompt
    |
    v
[Model Router] --- classifies tier (haiku/sonnet/opus)
    |
    v
[Skill Matcher] --- fuzzy-matches 30+ registered skills
    |
    v
[Agent] --- executes with full memory context
    |
    +--> [Episodic Memory] --- captures decisions, corrections, files
    +--> [Semantic Memory] --- persists across all sessions
    +--> [Context Save]    --- checkpoint for handoff/resume
```

## Components

### Model Router (`model-router-classify.py`)

Regex-based prompt classifier. Runs as a UserPromptSubmit hook. Zero latency overhead.

- **Opus triggers:** architecture, security, vulnerability, production incidents, tradeoff analysis
- **Haiku triggers:** explanations, file reads, searches, renames, typo fixes, formatting
- **Sonnet (default):** everything else

### Skill Matcher (`hooks/skill-matcher.py`)

Scans all skill directories (local + plugin cache), extracts keywords from SKILL.md descriptions, fuzzy-matches against user prompt, surfaces top N suggestions as injected context.

Configurable via `~/.claude/skill-matcher.json`:
```json
{
  "min_score": 2,
  "max_suggestions": 3,
  "cache_ttl_sec": 3600
}
```

### Backend Switcher (`commands/backend.md`)

Manages multi-account routing for AWS Bedrock:
- Profile A: free tier (office/enterprise)
- Profile B: paid tier (personal AI orchestration)
- Profile C: isolated execution (coding CLI)

Swap with `/backend`, confirm target, restart session. Settings stored as named JSON files.

### Task Router (`commands/route.md`)

Intent classification with human-in-the-loop dispatch:
- Enterprise/internal tooling tasks go to free backend
- Code execution goes to dedicated coding CLI
- Planning/architecture stays on current orchestrator
- Mixed tasks get decomposed into sub-tasks per backend

### Memory Protocol

Three-layer persistence with clear scope boundaries:

| Layer | Scope | Pruning | Format |
|-------|-------|---------|--------|
| Semantic | all sessions | manual | Markdown + YAML frontmatter |
| Episodic | per-tab/session | auto (50 facts, 7d, 30d) | timestamped facts |
| Working | current turn | context compaction | conversation buffer |

Auto-capture rules trigger on: corrections, architecture decisions, file edits, significant commands, pre-compaction summaries.

## Usage

This toolkit is designed for Claude Code on AWS Bedrock but the patterns are portable to any agent framework.

**Install as hooks:**
```bash
# Model router
cp model-router-classify.py ~/.claude/
# Add to settings.json hooks.UserPromptSubmit

# Skill matcher
cp hooks/skill-matcher.py ~/.claude/hooks/
# Add to settings.json hooks.UserPromptSubmit

# Backend switcher
cp commands/backend.md ~/.claude/commands/
cp commands/route.md ~/.claude/commands/
```

**Memory protocol:**
```bash
mkdir -p ~/.claude/projects/<slug>/memory
# Create MEMORY.md index
# Individual memories as frontmatter-ed .md files
```

## Why This Exists

AI coding agents are powerful but stateless, single-model, and context-blind. This toolkit fixes:

1. **Wrong model for the job** - A typo fix shouldn't burn Opus tokens. An architecture decision shouldn't use Haiku.
2. **Skill discovery** - Agents don't know what they can do unless you tell them every time.
3. **Memory loss** - Every new session starts from zero. Decisions get re-litigated.
4. **Context fragmentation** - Work spans multiple tools, accounts, and sessions with no continuity.

## Status

Running in production (my daily workflow) since May 2026. Processing 40+ sessions/week across 12+ active projects.

## License

MIT
