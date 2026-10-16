# Hypothesis: the order of the calls in a test of a move

Declared before measuring the `playtester_loop_order` cell, and versioned. It covers that cell
only. The three other cells of `issue1-skill` were measured first, without a hypothesis, and what
follows comes from reading their runs: it is the reason for the new cell, not a prediction about
them.

## What the first matrix showed

The matrix of 2026-10-16 ran `ilaas`, `gemma-4-31b`, `thinking = "medium"`, 20 repetitions. The
`playtester` cell detected the corner in 16 of 18 runs, but tunneling in only 8.

NEON moves the ball in `step()` and resolves the bricks in `frame()`, and its loop calls them in
that order. A correction of tunneling has to know the segment the ball travelled, so the reference
of the validator records the position in `step()` and sweeps it in `frame()`. A test of tunneling
can only pass on a correction if it calls `step()` and then `frame()`.

Nearly every `playtester` run wrote the tunneling entry. The 8 that detect it call `step()` then
`frame()`. Six others wrote a test that fails on the complete correction, because it calls only
one of the two functions:

- `01cf1f0a`, `1346148a` and `98196844` place the ball already past the brick and call only
  `frame()`, so no correction can know where the ball came from;
- `eb438ba8` places the ball before the brick and calls only `frame()`, which does not move it;
- `5ababf54` calls only `step()`, which resolves no brick.

The skill says such a test calls the other function "only after a first pass of the symptom's
function, in the order of the loop". The sentence is the same in the French original of
hands-on-harness. Read literally it starts the test with `frame()`, and nowhere does it say that
the move has to come before the function that judges it.

## The change

`materials/skills-loop-order/playtester/SKILL.md` is a copy of the skill with that one sentence
replaced: a test that needs a move plays one turn of the loop, the move first and then the
symptom's function, `step()` then `frame()` in a game whose loop runs them in that order, on a
state written as it is before the move. It also says not to place the ball where the move would
have taken it. The skill keeps its name, so the prompt is the same file as the `playtester` cell
and the sentence is the only difference between the two.

## Predictions

**`detects_tunneling` rises well above `playtester`, to at least two runs out of three.** If the
six tests above had called `step()` then `frame()`, the first matrix would have read 14/18. The
gap with `playtester` has to be established in the resampling table. If it stays marked `o`, the
cell is inconclusive and that is what gets written, not "it helps a little".

**`detects_corner`, `detects_axis` and `detects_exit` do not move**, within the noise of 20 runs.
These entries need no move, and the new sentence applies to moves only. If one of them drops, the
sentence leaks: the agent calls `step()` in tests that did not need it, and `step()` moves the
ball out of the setup before `frame()` judges it.

**`tests_sound` stays low.** In the first matrix it was false in 13 of 18 `playtester` runs, most
often because of the seam entry ("a single bounce per axis and per step"), whose test fails on the
complete correction for reasons unrelated to the order of the calls. The variant does not touch
that entry.

## How to read it

The cell has to run with the same agent as the `playtester` cell it is read against: same
provider, model and `thinking`. The first matrix used `thinking = "medium"`, while the committed
scenario says `off`, so a fresh run of all four cells is the clean comparison. Adding the cell to
the existing output directory with `--only playtester_loop_order --resume` also works, as long as
`[agent]` is the same as on that day.
