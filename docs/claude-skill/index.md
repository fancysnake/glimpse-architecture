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

The repository is a Claude Code plugin marketplace. Inside any Claude Code
session:

```text
/plugin marketplace add fancysnake/glimpse-architecture
/plugin install glimpse@glimpse
```

Then invoke it in any project:

```text
/glimpse
```

To install the bare skill file instead, without the plugin system:

```bash
mkdir -p ~/.claude/skills/glimpse
curl -fsSL https://raw.githubusercontent.com/fancysnake/glimpse-architecture/main/skills/glimpse/SKILL.md \
  -o ~/.claude/skills/glimpse/SKILL.md
```

Or [download it](SKILL.md.txt){ download="SKILL.md" } and save it to that
path.

## Skill file

The canonical copy lives at
[`skills/glimpse/SKILL.md`](https://github.com/fancysnake/glimpse-architecture/blob/main/skills/glimpse/SKILL.md)
in the repository; the block below is generated from it. `SKILL.md` is
itself assembled from `SKILL.src.md` and the shared rule fragments in `rules/`
— editing it by hand is a mistake CI catches. Contributors run `mise run skill`.

````markdown
--8<-- "skills/glimpse/SKILL.md"
````
