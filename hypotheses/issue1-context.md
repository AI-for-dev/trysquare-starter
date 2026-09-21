# Hypothesis: the context levers against the bounce on the bricks

Declared before measuring, and versioned. A hypothesis written afterwards is a conclusion in
disguise, and the point of writing it is to make a disappointing result publishable rather than
quietly reworded.

**State: the criterion exists, and it is not blind.** `bounce_bricks` is a probe,
`materials/provided-probe/probe.test.js`: `node:test` tests dropped in a copy of the agent's tree
made outside the clone, which place a ball already overlapping a brick by the targeted face, call
`frame()`, and require the speed component of the axis that was hit to flip while the other one
stays as it was. The off-axis component is non zero in every case, failing which a correction that
flips both axes at random would pass for a per-face correction.

One column comes with it, from the same run. `bounce_corners` plays the corner of the brick, where
the ball arrives diagonally and both components must flip. It is harder than `bounce_bricks` and
not a case apart: a correction that compares the two penetrations and flips only one of them
passes the four faces and fails at the corner.

A third column existed and was removed. `bounce_domain` played the walls of the field as a
regression guard, but they already bounce at the etalon: the column was green everywhere,
including on runs that had delivered nothing, and therefore separated no cell. A regression guard
belongs in the suite of the repo, not in the criterion of a measurement.

Checked on seven trees. The etalon scores 0/5. A per-face correction 4/5, the corner being what it
misses; the same one treating equal penetrations as a corner, 5/5, which says the column is
reachable. "Always flip vy" 2/5, "flip both axes" 1/5 - the latter only wins the corner, which is
exactly the point of the column. There remain the per-face correction extracted into a
`brickHit()` called from `step()`, 4/5 while saying where it came from on each case, and a tree
where `frame` was renamed, which returns no case but the reason for its silence.

## Four more columns, and what they should give

Added after everything above was written and **before any measurement of the widened matrix**,
from the catalogue of classic breakout bugs: the sticky bounce, the double reflection, tunneling,
the paddle. Two of them tighten the requested correction further, the other two record a latent
bug the ticket does not name. The predictions are written here so that the reading after the
measurement is not a rewording.

`bounce_exit` requires the ball to have come back out of the rectangle of the brick, which is the
second half of the correction the comment in the repo describes. **Prediction: it follows
`bounce_bricks` closely but stays below it**, because the comment names both halves in the same
sentence and a correction guided by it should do both, but flipping a speed is the gesture that
comes to mind first. The gap between the two columns is the measure of how many corrections stop
halfway.

`bounce_neighbors` plays a seam of the grid, where the ball overlaps two bricks at once.
**Prediction: noisy and not monotonic with the levers.** It does not depend on the quality of the
reasoning but on the written form: a `vy = -vy` cancels out on the second turn, a
`vy = Math.abs(vy)` does not, and a correction that repositions takes the ball out of the overlap
before the second brick and passes without even thinking about it. A context lever has no reason
to move that choice, so a clear correlation with the cells would be more surprising than its
absence.

`bounce_tunneling` demands continuous detection. **Prediction: black over the 200 runs.** No ticket
mentions the speed of the ball, the bug only shows at level 6, and fixing it means replacing the
detection rather than completing it.

`bounce_paddle` plays three flaws of `step()` that nobody asked anyone to fix. **Prediction: black
over the 200 runs**, and for a stronger reason than the previous one: even an agent who noticed
them would leave the scope by fixing them, and the framed ticket forbids it explicitly. If this
column lit up somewhere, one would have to read `in_scope` on the same line before seeing a success
in it.

The last two are therefore kept knowing that they will separate nothing. They carry no verdict, and
the only statement they will produce, "nobody went beyond what the ticket named", is worth
establishing rather than assuming.

### The etalon moved between two matrices, and that has to be read before anything else

Written afterwards, like the answer sections that follow, and placed before them because it
conditions what one is allowed to draw from them.

Two campaigns of this scenario were archived, two days apart. They declare the same
`etalon = "etalon-v1"` and **did not measure the same repo**:

| matrix | `etalon_commit` | the commit |
| --- | --- | --- |
| `…_ilaas_gemma-4-31b_n20`, 6 August | `144675b9` | *feat: neon glow pass* |
| `…_opencode-go_deepseek-v4-flash_n20`, 8 August | `d62ccd1f` | *update issue.md* |

The tag was moved between the two. What the move carries is not cosmetic: `git diff` between the
two commits touches two files, and one of them is `ISSUES.md`, whose **issue #1 is entirely
rewritten**. The version the gemma matrix read described nothing but the per-face bounce. The one
the deepseek matrix read also names the corner ("equal penetrations means a diagonal hit - flip
both components"), the exit out of the rectangle, the seam of the grid and tunneling, the last one
with numbers. The other file is `game/neon.js`, which now exports `frame`.

The consequence bears directly on prediction 2 of this file. `+well_crafted` gives
`bounce_corners` 0/20 on gemma and 19/20 on deepseek, with a rigorously identical prompt file: it
is not the prompt that changed, it is the document it points at. But the model, the provider and
the ticket changed together, so **no attribution is possible between these two matrices**, and the
only statement they allow together is "they do not compare".

Two things to take from it, and the second one is the more useful.

First, that the guard this setup claims, "a tag, cloned, never the working tree", **is not
enough**. A tag is a movable pointer, and `git tag -f` leaves no trace on the measuring side. What
caught it is `etalon_commit`, archived per run, whose docstring in `trysquare/repo.py` already said
that it is "the only trace left when a tag is moved between two matrices". The fix is upstream: an
etalon can now be a commit written out in full, which does not move.

Second, and this is the third time in the history of this scenario, that **what nearly became a
conclusion was an incident the archive knew how to name**, after the retries column and after
`suite_run`. None of the three was in a table.

The archive of 6 August is kept under `results/issue1-context_etalon-v1-at-144675b9_…`, its name
saying the commit since its tag no longer does. It only replays through the normal path with a
local clone where `etalon-v1` is put back on `144675b9`.

### A flaw of `suite_run`, the comparator this time

Distinct from the one in the next section, and found on the deepseek matrix: the column was worth
0/20 in the nine cells although the 180 runs had run the suite.

`RUN_COMMANDS` was a list of **exact strings**, on the defensible grounds that a pattern decides in
advance about what nobody has seen yet, where a list is completed by looking at what the agents
typed. The argument was right and the conclusion wrong: what varies from one model to the next is
not which command runs the suite, it is what the agent puts around it. `deepseek-v4-flash` prefixes
the working directory (`cd …/repo && npm test`, 664 times) and redirects the output
(`npm test 2>&1 | tail -30`, 80 times); `gemma-4-31b` types a bare `npm test`.

Recognition moved to a pattern, and the opposite risk, counting a mention as a run, was looked for
across the 360 archived runs: six commands contain the string in a non executing form, and all six
chain a real run in the same line.

What made the flaw visible is the reason attached to the false, which copies out the commands that
were not recognised: it showed an `npm test` in the list of commands "where no run was found". A
metric that says false without saying why would have held for a whole campaign.

### What the measurement answered

This section is about a matrix **since removed** from `results/`, whose cell names (`nothing`,
`+rule`, `+framed ticket`, `well crafted stack`) and whose `bounce_paddle` column no longer exist.
It is kept as it is: this is what was written in view of those numbers, and rewriting it in the
light of the following ones would do exactly what this file exists to prevent.

The four predictions above were written before measuring, then settled without spending a token:
`trysquare replay --rescore` replays the validator over the 240 archived trees of `results/…_n20`,
and the widened probe runs on them as it would have run on the day. The predictions are not
retouched; this paragraph is added underneath them.

| cell | bricks | exit | neighbors | tunneling | paddle |
| --- | --- | --- | --- | --- | --- |
| nothing | 12/20 | 12/20 | 8/20 | 0/20 | 0/20 |
| +thinking | 19/20 | 18/20 | 17/20 | 0/20 | 0/20 |
| +rule | 11/20 | 7/20 | 6/20 | 0/20 | 0/20 |
| +framed ticket | 18/20 | 17/20 | 15/20 | 0/20 | 0/20 |
| -system prompt | 15/20 | 11/20 | 9/20 | 0/20 | 0/20 |
| well crafted stack | 20/20 | 20/20 | 20/20 | 0/20 | 0/20 |

**`bounce_exit`: prediction held.** It follows `bounce_bricks` and stays below it everywhere except
in the base cell, where the twelve correct fixes already repositioned. The gap widens where the
correction is the least guided (`+rule` loses 4 fixes out of 11, `-system prompt` 4 out of 15) and
disappears on `well crafted stack`. It is exactly the column we hoped for: it distinguishes a
complete correction from a correction stopped halfway, and it does so on cells that
`bounce_corners` does not separate at all.

**`bounce_neighbors`: prediction wrong, and this is the most interesting result.** It had been
announced as noisy and not monotonic, on the grounds that the written form (`-vy` against
`Math.abs`) does not depend on the levers. It is in fact strictly monotonic with them, and orders
the cells like `bounce_bricks` while spreading them further apart: 8/20 at the base against 20/20
on the well crafted stack, where the criterion only goes from 12 to 20. The explanation lies in
`bounce_exit`: a correction that repositions takes the ball out of the overlap before reaching the
second brick and passes without having planned anything for it. `neighbors` therefore measures in
large part the same thing as `exit`, more severely. Two columns rather than one is still justified
(they separate by 4 runs on the base and 4 on `-system prompt`) but they are not independent, and a
reading that treated them as two distinct confirmations would count twice.

**`bounce_tunneling` and `bounce_paddle`: predictions held, 0/240 for both.** The statement they
existed to establish is established.

### A flaw of `suite_run` that this replay brought to light

It does not concern the four columns that were added, and nothing in the widening of the probe
touches this metric: every earlier column is identical down to the bit, except this one.
`suite_run` does not land back on its archived values (`+thinking` 11 then 7, `+rule` 18 then 12)
and **it is the archived values that are wrong.**

The archived session is the recording of what the agent did, and the two forms in which it is kept
agree: the `session/*.jsonl` and the base64 payload of the `session/*.html` give the same calls.
Scored against it, the 240 runs give 240/240 agreement for the replay and 230/240 for the archive.
The ten discrepancies all go the same way, the archive asserting an `npm test` the agent did not
run, and all sit in `+rule` (6) and `+thinking` (4), that is to say the two cells whose ticket does
not name the command. On `ab8180eb`, the agent made three calls (`ls -R`, `read game/neon.js`,
`edit`) and the string `npm test` appears **not once** in his session, although the archive gives
it as the reason.

The cause is written in `trysquare/assay.py`, in the docstring of `tool_calls()`: the version of
this validator that measured the matrix read `context["trace"]`, the raw stream, and glued the
calls back together by `toolCallId`. That file has since been rebuilt on the base, which reads the
**session**: "the `toolCallId` reconciliation that file needed had no cause but reading the wrong
file". The trace is deliberately not archived, five hundred times the size for nothing the per
message record does not already say, so the `trace` that `context.json` still lists points at a
purged working directory. By exactly which path that stream produced a phantom `npm test` is
therefore no longer verifiable, and does not have to be: the question "what did the agent do" is
read in the session, and that is what the code reads today.

A second symptom of the same flaw, without consequence on the verdicts: the reason of
`skill_invoked` announced an inflated number of tool calls on 120 of the 197 runs where it is
comparable (7 against 3, 11 against 5). The boolean itself is identical everywhere.

**Practical consequence.** The `suite_run` column of `results/…_n20/synthesis.md` must not be cited
as it stands. It is fixed without spending a token by a `trysquare replay --rescore`, which in the
same gesture adds the four columns above, and remeasuring the matrix, which the widening already
called for, settles the question along the way.

**What has to be said before reading anything at all in this matrix.** The shape of the probe was
chosen *after* a first matrix had run. Its six runs were all invalid, the validator being still a
skeleton and refusing to score, but their diffs were read to settle the question this file left
open, and the count is clear: three fixes out of five stayed inside `frame()`, which is neither
exported nor callable without a canvas, and the two that came out into an exported function are the
two best equipped cells. A probe limited to the exports would therefore have scored "extracted a
function" under the name of `per_face`, and its reachability would have correlated with the
treatment. Hence the instrumented copy, which exports everything the module declares at the top
level and reaches the correction wherever it landed.

That choice is therefore informed by data, and saying so is the only way not to pass it off as a
decision made blind. What it did not touch: none of the predictions below has been reread or
retouched since, and the probe knows nothing but the geometry of the bounce, never the cell that
produced it.

## Why this task rather than issue #2

The bench of module 2.1 measured issue #2, and it ends up admitting that the half of the ticket
which decides whether the work is done, "stop scanning every brick", has no mechanical form. It was
approached with a pattern in the diff, the pattern got it wrong twice, and the module concludes
that a judge is needed.

Issue #1 is of another nature. Its hard half is a **behaviour**: an impact on the top or the bottom
of a brick flips `vy`, an impact on a side flips `vx`. A behaviour is executed instead of being
recognised, so the criterion can be a probe rather than a pattern, without a judge and without
tokens.

The easy half is that the ball stops going through the bricks, which a single line achieves
(`ball.vy = -ball.vy`). The task therefore keeps the property the module needs, that a run can look
finished while half the ticket is not done, and gains a criterion nobody has to take on trust.

## What is predicted

1. **The base delivers the easy half and not the hard half.** Any bounce at all removes the most
   visible symptom, and nothing in a vague request points at the side case.
2. **Naming the ticket moves the hard half.** The mechanism is written in `ISSUES.md`, under issue
   #1, in the repo the agent already has at hand. The framed ticket does not copy it out: it names
   the issue, the scope and the stopping criterion. What is measured is therefore whether pointing
   at written material is enough for it to be read, not whether an agent can follow an instruction
   handed to him.
3. **The project rule does not move the hard half.** `materials/AGENTS.md` says nothing about this
   ticket. Its cell is a control: if it moves the criterion, then the criterion captures general
   diligence and not the lever the line names.
4. **Overflow is thinner here than on issue #2, and may discriminate nothing.** With issue #1 as
   the task, the signature of issue #1 becomes the work asked for and leaves the overflow set. Only
   issue #6 remains, alone, which is exactly the situation `scripts/bench/signatures.py` warns
   about in its own comments.
5. **The skill moves the hard half beyond the well crafted stack.** This is the prediction the
   `well crafted stack +skill` cell exists to test, and it is the most fragile of this list. The
   reasoning: the per-face bounce is a behaviour, and writing the edge case before the correction
   forces one to state what the code must do face by face, which a correction written first does
   not require. The skill does not name that mechanism (it says to look for the equality case
   between two compared quantities and to check what must not change), so if the gap exists, it
   comes from a method and not from a hint.

   Its comparison is **`well crafted stack`, not `nothing`.** It is the only cell it differs from
   by the skill alone; the gap to the verdict, which is taken against `nothing`, would mix the four
   levers of the stack with this one.

   What would refute it, specifically: both stacks return the same `bounce_bricks`. Then the skill
   produces test work without producing behaviour, which is a publishable result and not a failure
   of the brick, and `tests_added` will say so by showing that it was indeed used.

   **`skill_invoked` is read before anything else on that line.** It says whether the agent went to
   read the body of the `SKILL.md`, which pi leaves to his discretion: only the name and the
   description enter the system prompt. Nothing above is asserted about the runs where it is false.
   A brick that was never opened does not measure a working method, it measures what its
   description managed to trigger, and that would be another result, to be written in those terms.

## What would refute it

- The base reaches the hard half as often as the framed ticket. Then the criterion is not difficult
  and discriminates nothing.
- No cell reaches the hard half. Then the criterion is saturated at zero, the matrix says nothing,
  and honesty is to write that rather than go looking for a more accommodating measure.
- The `+rule` cell moves the criterion as much as the `+framed ticket` cell. Then the criterion
  measures diligence, and everything this file asserts about tickets is unsupported.
- The `probe_reached` column is not full. It says whether the probe saw the ball touch the brick,
  and this clause is its reason to exist: as long as it is true everywhere, `per_face` really does
  measure "did the agent do the hard half". As soon as it hollows out, the criterion slides towards
  "did the agent do the hard half **somewhere reachable**", which is another assertion and must be
  written in those terms in the synthesis. It is the instrumented copy that keeps it full, and not
  a property of the repo: it will hollow out the day a correction stops going through `step()` then
  `frame()`.

## The `well crafted stack +probe` cell, and what it should give

Added after everything above and **before any measurement containing it**. It asks the opposite
question to all the others: elsewhere context is given and we watch whether the agent finds the case
the request does not name; here he is given the test that judges him, red, in the tree, and we watch
whether he corrects himself. A `kind = "files"` brick drops
`materials/provided-probe/probe.test.js` at `game/probe.test.js` before the agent starts.

It is read against `well crafted stack`, the only cell it differs from by this brick alone.

The provided probe is the very file that scores, a single source, whose single import line
`issue1.py` rewrites for its scoring copy. This cell therefore also reads the two latent groups,
tunneling and paddle, which issue #1 does not command: it can make them pass where the other cells
never see them, so those two columns do not compare from one cell to the next. The first four do.

It imports `frame` from `./neon.js`, which the module does not export: on arrival the suite is
therefore red at load time, and the first thing to do is to export the render loop. This is checked:
15 red and the 6 cases of the repo green at the etalon, 21 green on a corrected tree.

1. **`bounce_bricks`, `bounce_exit` and `bounce_neighbors` go up to 20/20 or very close.** This is
   the soft prediction, and it would be almost a tautology if the cell were compared to `nothing`:
   `well crafted stack` is already at 20/20 on all three. What is measured here is therefore the
   opposite of a gain. **If the cell goes below `well crafted stack`, that is the result**, and it
   would say that receiving a red test diverts the work from the correction towards satisfying the
   test.
2. **`bounce_corners` is the column where something can happen.** It is the only one the well
   crafted stack does not saturate, the provided probe names it explicitly (the corner, both
   components), and an agent who runs the test before concluding cannot stop at a per-face
   correction. Prediction: it goes up, and it is the only gap of this cell worth citing.
3. **`probe_intact` is true everywhere, but it is the column to read first.** Loosening the
   assertion is the answer that costs nothing, the scoring is not fooled since it rewrites its own
   copy, and a single run that attempted it changes the reading of the whole bounce column.
   Prediction: 5/5 (a model of this size has no reason to prefer rewriting a test to fixing four
   lines) and a refutation is more interesting than the confirmation.
4. **`in_scope` goes down.** The provided probe is not in the scope, it is given to be read and
   satisfied, so any run that touches it leaves the scope. A drop here is not indiscipline but the
   mechanical effect of having put one more file in the tree, and `probe_intact` is what will say
   which of the two readings applies. Written before the measurement so as not to be chosen after
   it.
5. **`tests_added` goes down too, and for a reason that is not a failing.** The ticket asks for the
   edge cases "first as red tests, then green"; an agent who already has them in front of him has no
   reason to write more in `game/neon.test.js`, which the metric alone counts. A cell at `0/5` here
   would have done exactly what it was asked.

## What is not asserted

Nothing about cost. Tokens, turns and duration are reported, but a retry replays all the context
accumulated, so a cost column is only readable when retries are close to zero in the cells being
compared.

Nothing about the scope of the cell with a skill. `in_scope` is computed against two files,
`game/neon.js` and `game/neon.test.js`, and a skill that talks about tests may cause one more test
file to be created. A lower `in_scope` on that cell will say that the brick moves where tests are
written, which is neither a failure of the validator nor a lack of diligence from the agent. This
reading is written here before the measurement so as not to be chosen after it.

Nothing between the two model matrices. The model is a constant of the scenario in this tool, so the
"big model" half of the 2x2 is a separate experiment. Durations and costs only compare within one
matrix.

## Smoke passes

A run at `--repetitions 2` is **not** a test of this hypothesis and no conclusion comes out of it.
It serves to check that the harness is plugged in: every run valid, the outputs complete, and the
reasoning level recorded by each session equal to the one its cell declares.
