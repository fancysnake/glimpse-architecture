# Claude Skill

GLIMPSE ships as a [Claude Code](https://claude.ai/code) skill — a compact
reference file that loads the architecture rules directly into Claude's context
when you invoke `/glimpse` in any project.

## What it does

The skill loads the full GLIMPSE conventions — layer responsibilities, slicing
rules, import boundaries, patterns, and drift red flags — so you can ask Claude
to review code, suggest where a new file belongs, or flag import violations
without repeating the rules each time.

## Installation

1. Create the skills directory if it does not exist:

   ```text
   mkdir -p ~/.claude/skills/glimpse
   ```

2. Save the skill file as `~/.claude/skills/glimpse/SKILL.md` — [download
   it](SKILL.md.txt){ download="SKILL.md" }, or copy the contents from the block
   below.

3. Invoke it in any Claude Code session:

   ```text
   /glimpse
   ```

To install it straight from the command line:

```bash
mkdir -p ~/.claude/skills/glimpse
curl -fsSL https://raw.githubusercontent.com/fancysnake/glimpse-architecture/main/SKILL.md \
  -o ~/.claude/skills/glimpse/SKILL.md
```

## Skill file

The canonical copy lives at
[`SKILL.md`](https://github.com/fancysnake/glimpse-architecture/blob/main/SKILL.md)
in the repository root; the block below is generated from it.

````markdown
--8<-- "SKILL.md"
````
