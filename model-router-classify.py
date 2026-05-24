#!/usr/bin/env python3
"""
Model Router Classifier
Reads UserPromptSubmit hook JSON from stdin.
Outputs systemMessage + additionalContext with tier classification.
Runs in <50ms — keyword matching only, no LLM call.
"""
import json, sys, re

# To disable temporarily, uncomment: sys.exit(0)

data = json.load(sys.stdin)
prompt = (data.get("tool_input", {}).get("prompt", "") or "").lower().strip()

# Bypass: user prefixed with >>
if prompt.startswith(">>"):
    sys.exit(0)

# ── OPUS signals ──────────────────────────────────────────────────
OPUS = [
    (r'\barchitect(ure|ural|ing)?\b',        "architecture decision"),
    (r'\bsecurity\b',                         "security concern"),
    (r'\bvulnerabilit(y|ies)\b',              "vulnerability analysis"),
    (r'\bhow should (i|we) design\b',         "design decision"),
    (r'\bdesign (system|pattern|decision)\b', "design decision"),
    (r'\breview (this|the) architecture\b',   "architecture review"),
    (r'\bproduction incident\b',              "production incident"),
    (r'\btradeoff\b',                         "tradeoff analysis"),
    (r'\bcomplex.{0,20}debug\b',              "complex debugging"),
    (r'\bscalabilit(y|ies)\b',                "scalability design"),
    (r'\bmulti.tenant\b',                     "multi-tenant architecture"),
    (r'\bauth (system|design|architecture)\b',"auth architecture"),
    (r'\bperformance (strategy|bottleneck)\b',"performance strategy"),
]

# ── HAIKU signals ─────────────────────────────────────────────────
HAIKU = [
    (r'^what (is|does|are|was)\b',            "read-only question"),
    (r'\bexplain (this|the|how)\b',           "explanation request"),
    (r'\bshow me\b',                          "display request"),
    (r'\bwhat.{0,30}(do|does|is|are)\b',     "read-only question"),
    (r'\blist (all|the|every)\b',             "list request"),
    (r'\bgrep\b|\bsearch for\b|\bfind all\b', "search task"),
    (r'\brename\b',                           "mechanical rename"),
    (r'\btypo\b|\bspelling\b',               "typo fix"),
    (r'\bwhats in\b|\bshow.{0,10}file\b',    "file read"),
    (r'\bsummar(ize|y)\b',                   "summarize request"),
    (r'\bquick(ly)?\b.{0,20}(fix|change|update)', "quick edit"),
    (r'\bformat\b.{0,20}(this|the|file)',    "formatting task"),
]

tier = "SONNET"
reason = "standard development task"

# Check OPUS first (higher priority)
for pattern, label in OPUS:
    if re.search(pattern, prompt):
        tier = "OPUS"
        reason = label
        break

# Only check HAIKU if not already OPUS
if tier == "SONNET":
    for pattern, label in HAIKU:
        if re.search(pattern, prompt):
            tier = "HAIKU"
            reason = label
            break

# Model IDs
MODELS = {
    "HAIKU":  "global.anthropic.claude-haiku-4-5-20251001-v1:0",
    "SONNET": "global.anthropic.claude-sonnet-4-6[1m]",
    "OPUS":   "global.anthropic.claude-opus-4-7",
}

model_id = MODELS[tier]
system_msg = f"[model-router] {tier} tier — {reason} → {model_id}"

additional = (
    f"model-router pre-classification: {tier} tier ({reason}). "
    f"Recommended model: {model_id}. "
    f"Follow the model-router SKILL.md routing rules."
)

out = {
    "systemMessage": system_msg,
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": additional,
    }
}

print(json.dumps(out))
