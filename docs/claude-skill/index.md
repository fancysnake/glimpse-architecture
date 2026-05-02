# Claude Skill

GLIMPSE ships as a [Claude Code](https://claude.ai/code) skill — a compact reference file that loads the architecture rules directly into Claude's context when you invoke `/glimpse` in any project.

## What it does

The skill loads the full GLIMPSE conventions — layer responsibilities, slicing rules, import boundaries, patterns, and drift red flags — so you can ask Claude to review code, suggest where a new file belongs, or flag import violations without repeating the rules each time.

## Installation

1. Create the skills directory if it does not exist:
   ```
   mkdir -p ~/.claude/skills/glimpse
   ```

2. Save the skill file as `~/.claude/skills/glimpse/SKILL.md` with the content below.

3. Invoke it in any Claude Code session:
   ```
   /glimpse
   ```

## Skill file

The file below is the canonical `SKILL.md`. [Download SKILL.md](SKILL.md) directly, or copy it verbatim to `~/.claude/skills/glimpse/SKILL.md`.
