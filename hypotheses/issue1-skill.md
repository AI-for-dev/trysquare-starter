# Hypothesis: the two cells added after the first matrix of `issue1-skill`

Declared before measuring the `playtester_loop_order` and `dynamic_playtester_grounded` cells, and
versioned. It covers those two cells only. The three other cells of `issue1-skill` were measured
first, without a hypothesis, and what follows comes from reading their runs: it is the reason for
the new cells, not a prediction about them.

# `playtester_loop_order`: the order of the calls in a test of a move

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

# `dynamic_playtester_grounded`: a catalogue made of pages that were read

## What the first matrix showed

In the same matrix, once its 60 runs were all in, the `dynamic_playtester` cell detected the
corner in 1 of 20 runs, against 17 of 20 for `playtester`. Two things went wrong, and only the
second one is about the skill.

The search failed. Exa's free MCP server answered 429 to most searches, and in 18 of the 20 runs
`catalogue.sh` came back saying so: "rate limits", "internal knowledge", "synthesized". The nested
session wrote the catalogue anyway, from what the model knows, with URLs that do not exist
(`gamedev.stackexchange.com/questions/delta-time-spikes`) or that exist but were never opened.
Those runs count as valid, and nothing in `catalogue_built` sets them apart. The two catalogues
that come from real pages hold 2 and 3 entries.

The invariants are vague. `playtester` gives "when the ball penetrates as much on both axes, both
components flip", and the agent builds an exact tie. The catalogues of `dynamic_playtester` give
"the bounce angle should be a consistent reflection of the incident angle" (`8ba741c0`) or "a
weighted average of the faces" (`3238d49b`). In `3238d49b` the "corner" test enters the brick by
12 units on x and 2 on y, which is a hit on the top face: the complete correction flips `vy` only,
and the test, which expects both, fails on it.

## The change

`materials/skills-grounded/dynamic-playtester/` is a copy of the skill. It keeps the name, so the
prompt is the same file as the `dynamic_playtester` cell. Four things change.

- The collection script prints the searches and pages that failed, and the instructions tell the
  nested session to write nothing and answer `NO SOURCES` when no page was kept.
- `scripts/check-sources.mjs`, run by `catalogue.sh` after the session, removes every entry whose
  source is not one of the pages the collection returned, and deletes the catalogue when no entry
  is left. It reads those pages from the nested session, which `catalogue.sh` now keeps in
  `references/catalogue-session/` instead of throwing it away, so trysquare archives it too.
- `SKILL.md` tells the agent to stop, without writing a catalogue or tests, when `catalogue.sh`
  fails or leaves no catalogue, and to set aside the entries whose invariant is `none`.
- An invariant has the form "when <condition on the state>, <variable or property> <value>". The
  instructions show two examples from other genres, a platformer and a shoot 'em up, so that the
  form is shown without handing over an entry of the brick breaker.

The rest of the collection is unchanged: same queries, same filter, same limits, and the nested
session still runs at `--thinking low`.

## Predictions

**Without a working search, the cell measures nothing, and says so.** With the free Exa server
refusing as it did on 2026-10-16, most runs end on `NO SOURCES` and deliver no test, so
`[verdict].validity` sets them aside. That is the intended outcome: an invalid run instead of a
valid run on an invented catalogue. The cell is worth measuring only with a search that answers,
an Exa key for instance.

**Every valid run has a catalogue whose sources were all opened.** This holds by construction
through `check-sources.mjs`, and it is checked rather than assumed, by reading the archived
`catalogue-session/` of each run against its `bugs-arcade.md`.

**The catalogues are shorter than those of `dynamic_playtester`.** The invented catalogues held up
to 11 entries; the two real ones held 2 and 3. Most of the drop is entries that were never read.

**`detects_corner` rises above the 1/20 of `dynamic_playtester`, and stays below the 17/20 of
`playtester`.** It rises because a corner entry, when the search brings one, now comes with an
invariant the agent can turn into an exact tie. It stays below because nothing guarantees that the
search finds a page about corners. If it does not rise at all, the form of the invariant is not
what held the corner back, and the search is.

**`detects_tunneling` does not move.** The variant leaves the sentence about the order of the
calls untouched, so the six-run problem of `playtester` stays.
