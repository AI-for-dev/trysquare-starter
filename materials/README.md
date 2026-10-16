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
| `issue1-simple-prompt-with-playtester.md` | the careless request, prefixed with `/skill:playtester` |
| `issue1-simple-prompt-with-dynamic-playtester.md` | the careless request, prefixed with `/skill:dynamic-playtester` |
| `AGENTS.md` | a project convention, as a permanent context file |
| `SYSTEM-minimal.md` | the agent's system prompt reduced to three lines |
| `skills/playtester/` | a skill from the course: red tests from a catalogue of breakout bugs written by hand |
| `skills-loop-order/playtester/` | `skills/playtester/` with one sentence changed: a test of a move calls `step()` then `frame()`, see `hypotheses/issue1-skill.md` |
| `skills-then-fix/playtester/` | `skills-loop-order/playtester/` with a fifth step: once the tests are red, fix the game until the suite passes, see `hypotheses/issue1-skill.md` |
| `skills/dynamic-playtester/` | the same procedure, with a catalogue built by web search in a nested `pi -p` session |
| `skills-grounded/dynamic-playtester/` | `skills/dynamic-playtester/` whose catalogue keeps only entries backed by a page the search opened, with invariants of the form "when <condition>, <value>", see `hypotheses/issue1-skill.md` |
| `skills-catalogue-given/dynamic-playtester/` | `skills/dynamic-playtester/` shipped with a `references/bugs-arcade.md` already written, so the search is out of the cell, see `hypotheses/issue1-skill.md` |
| `remove-issues-md.sh` | the `setup` script of the `blind` cells and of `issue1-skill`: deletes `ISSUES.md` |
| `issue1-flow-prompt.md` | the well crafted request, handed to `/run issue1` in the `flow` cell of `issue1-workflow` |
| `flows/issue1.md` | the combo flow of the workflows module, adapted to issue #1 |
| `agents/` | the six roles the flow runs, copied from hands-on-harness at `11afb5f`; the reviewer and the auditor are amended, see the scenario |
| `checks/test.sh` | what the flow's `check` nodes run: `npm test` |
| `provided-probe/probe.test.js` | the scoring probe, dropped in the tree of the `add_tests` cells |

The well crafted prompt does not copy out the bounce mechanism, although `ISSUES.md` details it in
the measured repo. That restraint is the subject of the cell: what is measured is whether pointing
at a written document is enough for it to be read, and not whether an agent can apply a hint just
handed to him.

The two skills come from `scripts/skills/` of
[hands-on-harness](https://github.com/AI-for-dev/hands-on-harness), at commit `9f48fbc`, translated
from French into English like the rest of this repository. The translation keeps every rule, URL
and line of code; the only renames are `references/consignes-catalogue.md`, now
`references/catalogue-instructions.md`, and the variables of its collection script.
`dynamic-playtester` ships without
`references/bugs-arcade.md`: building that catalogue is part of what its cell measures.

The probe is a single file for two jobs: `validators/issue1.py` drops it in a copy of the measured
tree to score every cell, and the `kind = "files"` brick of the scenario commits it into the clone
of the `add_tests` cells before the agent starts. The only thing that separates the two uses
is its import line, which the validator rewrites in its copy and follows with a guard.
