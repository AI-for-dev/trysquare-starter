# materials

What a scenario injects into the clone or passes to the agent, one file per piece.

These files are not documentation. The prompts, the `AGENTS.md` and the minimal system prompt are
experimental inputs: changing one word changes the measurement and invalidates the tables already
published. If a wording has to evolve, create a piece next to it and declare it as one more cell,
rather than rewriting this one.

| file | what it is |
| --- | --- |
| `issue1-simple-prompt.md` | the base task: a real but careless request |
| `issue1-well-crafted-prompt.md` | the same work, asked for properly, with a pointer to `ISSUES.md` |
| `issue1-simple-prompt-with-skill.md` | the careless request, plus the invocation of the skill |
| `AGENTS.md` | a project convention, as a permanent context file |
| `SYSTEM-minimal.md` | the agent's system prompt reduced to three lines |
| `skills/playtest/` | a skill: play the game before fixing it, and look for the edge cases |
| `remove-issues-md.sh` | the `setup` script of the `blind` cells: deletes `ISSUES.md` from the clone |
| `provided-probe/probe.test.js` | the scoring probe, dropped in the tree of the two `add_tests` cells |

The well crafted prompt does not copy out the bounce mechanism, although `ISSUES.md` details it in
the measured repo. That restraint is the subject of the cell: what is measured is whether pointing
at a written document is enough for it to be read, and not whether an agent can apply a hint just
handed to him.

The probe is a single file for two jobs: `validators/issue1.py` drops it in a copy of the measured
tree to score every cell, and the `kind = "files"` brick of the scenario commits it into the clone
of the two `add_tests` cells before the agent starts. The only line that separates the two uses is
its import, which the validator rewrites in its copy.
