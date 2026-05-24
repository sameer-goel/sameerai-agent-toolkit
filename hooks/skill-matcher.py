#!/usr/bin/env python3
"""skill-matcher — UserPromptSubmit hook.

Scans user prompt against all skill SKILL.md descriptions (local + plugins),
ranks by fuzzy keyword overlap, and injects top matches as additional context
so Claude considers invoking them before acting.

Non-blocking: prints to stdout, Claude Code injects into next turn's context.
Silent if no strong match (threshold configurable).

Config: ~/.claude/skill-matcher.json (optional)
  {
    "min_score": 2,           // min keyword hits to surface
    "max_suggestions": 3,     // cap at N
    "ignore_prompts": ["^\\s*$", "^yes$", "^no$", "^ok$"],  // regex skip
    "cache_ttl_sec": 3600     // re-scan skills after N seconds
  }
"""
import json
import os
import re
import sys
import time
from pathlib import Path

HOME = Path.home()
CACHE_FILE = HOME / ".claude/.skill-matcher-cache.json"
CONFIG_FILE = HOME / ".claude/skill-matcher.json"

DEFAULT_CONFIG = {
    "min_score": 2,
    "max_suggestions": 3,
    "ignore_prompts": [r"^\s*$", r"^(yes|no|ok|y|n|sure|stop|cancel)\s*[.!?]?\s*$"],
    "cache_ttl_sec": 3600,
    "skill_dirs": [
        str(HOME / ".claude/skills"),
        str(HOME / ".claude/plugins/cache"),
    ],
}

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "for", "with", "in", "on",
    "at", "by", "from", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "shall", "can", "may", "might", "must", "this", "that", "these",
    "those", "i", "you", "he", "she", "it", "we", "they", "me", "my", "your",
    "his", "her", "its", "our", "their", "what", "which", "who", "whom", "whose",
    "when", "where", "why", "how", "all", "some", "any", "no", "not", "only",
    "also", "just", "really", "very", "too", "so", "as", "if", "then", "than",
    "because", "while", "before", "after", "during", "above", "below", "between",
    "out", "up", "down", "over", "under", "again", "further", "once",
    "here", "there", "now", "then", "please", "help", "want", "need", "like",
    "make", "get", "got", "give", "take", "use", "used", "using", "try",
}


def load_config():
    cfg = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            user_cfg = json.loads(CONFIG_FILE.read_text())
            cfg.update(user_cfg)
        except Exception:
            pass
    return cfg


def load_cached_skills(cfg):
    try:
        if CACHE_FILE.exists():
            cache = json.loads(CACHE_FILE.read_text())
            if time.time() - cache.get("ts", 0) < cfg["cache_ttl_sec"]:
                return cache.get("skills", [])
    except Exception:
        pass
    return None


def save_cache(skills):
    try:
        CACHE_FILE.write_text(json.dumps({"ts": time.time(), "skills": skills}))
    except Exception:
        pass


def scan_skills(cfg):
    """Walk all skill dirs, parse SKILL.md frontmatter + description."""
    skills = []
    seen = set()
    for base_s in cfg["skill_dirs"]:
        base = Path(base_s)
        if not base.exists():
            continue
        for md in base.rglob("SKILL.md"):
            try:
                content = md.read_text(errors="ignore")
            except Exception:
                continue
            # Parse YAML-ish frontmatter
            name = None
            desc_lines = []
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    fm, body = parts[1], parts[2]
                    in_desc = False
                    for line in fm.splitlines():
                        line_s = line.rstrip()
                        if line_s.startswith("name:"):
                            name = line_s.split(":", 1)[1].strip()
                        elif line_s.startswith("description:"):
                            in_desc = True
                            rest = line_s.split(":", 1)[1].strip()
                            if rest and rest != ">":
                                desc_lines.append(rest)
                        elif in_desc and line.startswith(" "):
                            desc_lines.append(line.strip())
                        elif in_desc and line.strip() and not line.startswith(" "):
                            in_desc = False
            if not name:
                name = md.parent.name
            if name in seen:
                continue
            seen.add(name)
            desc = " ".join(desc_lines)
            # Also include first ~500 chars of body for additional matching
            body_snippet = body[:500] if "body" in dir() else ""
            skills.append({
                "name": name,
                "description": desc,
                "path": str(md),
                "tokens": tokenize(name + " " + desc + " " + body_snippet),
            })
    save_cache(skills)
    return skills


def tokenize(text, aliases=None):
    """Lowercase, split non-word, drop stop words, expand aliases, return set."""
    aliases = aliases or {}
    # First check raw text for multi-char aliases like "i/o"
    text_low = text.lower()
    expanded = set()
    for alias, targets in aliases.items():
        if alias in text_low:
            expanded.update(targets)
    # regular tokens
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text_low)
    base = {w for w in words if w not in STOP_WORDS}
    # expand single-word aliases
    for w in list(base):
        if w in aliases:
            base.update(aliases[w])
    return base | expanded


def score(prompt_tokens, skill):
    """Fuzzy score: count overlapping tokens. Bonus for name-exact match."""
    hits = prompt_tokens & skill["tokens"]
    s = len(hits)
    # name-exact bonus
    name_l = skill["name"].lower().replace("-", " ").split()
    for part in name_l:
        if part in prompt_tokens:
            s += 2
    return s, hits


def should_skip(prompt, cfg):
    for pat in cfg.get("ignore_prompts", []):
        if re.match(pat, prompt, re.IGNORECASE):
            return True
    return False


def main():
    cfg = load_config()

    # Claude Code passes the prompt on stdin (per hook spec)
    try:
        raw = sys.stdin.read()
    except Exception:
        raw = ""
    # Prompt-submit hook stdin is JSON w/ prompt key
    prompt = ""
    try:
        payload = json.loads(raw)
        prompt = payload.get("prompt", "") or payload.get("user_prompt", "") or ""
    except Exception:
        prompt = raw

    if not prompt or should_skip(prompt, cfg):
        return

    skills = load_cached_skills(cfg)
    if skills is None:
        skills = scan_skills(cfg)

    aliases = cfg.get("aliases", {})
    prompt_tokens = tokenize(prompt, aliases)
    if len(prompt_tokens) < 2:
        return

    ranked = []
    for sk in skills:
        s, hits = score(prompt_tokens, sk)
        if s >= cfg["min_score"]:
            ranked.append((s, hits, sk))
    ranked.sort(key=lambda x: -x[0])

    top = ranked[: cfg["max_suggestions"]]
    if not top:
        return

    lines = ["[skill-matcher] Available skills matching this prompt:"]
    for s, hits, sk in top:
        name = sk["name"]
        desc_short = sk["description"][:100].rstrip()
        keywords = ", ".join(sorted(hits)[:6])
        lines.append(f"  • /{name} (score {s}, matched: {keywords}) — {desc_short}")
    lines.append("Consider invoking one before acting, or proceed directly if none apply.")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
