# Hypothesis: the cells added after the first matrix of `issue1-skill`

Declared before measuring the cells added after the first matrix, and versioned. It covers those
cells only. The three other cells of `issue1-skill` were measured first, without a hypothesis,
and what follows comes from reading their runs: it is the reason for the new cells, not a
prediction about them.

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

# `dynamic_playtester_catalogue_given`: the same skill, with its catalogue already written

## The change

`materials/skills-catalogue-given/dynamic-playtester/` is the committed `dynamic-playtester`,
byte for byte, plus `references/bugs-arcade.md`. The skill only runs `catalogue.sh` when the
catalogue has no section for the genre, so the agent starts from that file and the search is out
of the cell. The prompt, the skill name and the `web-access` brick are the same as in
`dynamic_playtester`.

The catalogue was generated by the operator before this cell was declared. **Where and how it was
generated is still to be written here, before the first run.** Two edits were made to it: its
genre section was renamed from `breakout` to `brick breaker`, the genre all 25 calls to
`catalogue.sh` of the first matrix passed, so that the agent finds it. And nothing else: its 32
entries are as they were, including 25 source URLs whose path was replaced by
`[BASE64_ENCODED_DATA]` somewhere along the way. The tests do not read the sources, so this does
not change what is measured, but those entries cannot be checked against their page.

This cell separates the two halves of `dynamic_playtester`. Its runs face no 429 and no invented
catalogue, and every run gets the same catalogue, so what changes from `dynamic_playtester` is the
search, and what changes from `playtester` is the catalogue.

## Predictions

**The agent uses the given catalogue and does not rebuild it.** At most 2 runs out of 20 call
`catalogue.sh`, which their session shows. More than that means the section name does not match
the genre the agent picks, and the cell measures the search again.

**`detects_corner` stays low, near the 1/20 of `dynamic_playtester` and far from the 17/20 of
`playtester`.** This catalogue has no corner entry of its own. The corner shares an entry with the
seam ("Corner / seam double bounce between two adjacent bricks"), and its invariant, "reflected
exactly once about the correct contact normal", names no condition and no value. This is the test
of the explanation given for the first matrix: if the corner was missed because the invariant was
vague rather than because the search failed, a catalogue that is complete but vague on that point
gives the same result. If `detects_corner` rises toward `playtester`, that explanation is wrong.

**`detects_tunneling` stays near the first matrix, about one run in two.** The catalogue has two
tunneling entries, but the sentence about the order of the calls is the original one, which is
what held `playtester` to 10 of its 19 judged runs.

**Runs are shorter than in `dynamic_playtester`.** There is no nested session to wait for.

# `playtester_then_fix`: the red tests first, then the fix

## Why this cell

The skills stop at red tests: "You do not fix the game". In the first matrix the agent alone,
`nothing`, fixes the faces of the bricks (`bounce_bricks` 18/20) but never the corner or
tunneling (`bounce_corners` 0/20, `bounce_tunneling` 0/20), while the tests of the skills catch
exactly those two: `playtester_loop_order` detects the corner in 16 of 19 judged runs and
tunneling in 18 of 19. The question of this cell is whether tests written first, from a catalogue,
make the agent fix what it never sees alone.

## The change

`materials/skills-then-fix/playtester/SKILL.md` is the skill of `playtester_loop_order` with the
introduction, step 4 and the final table changed, and a step 5. Once each new test is red for the
right reason, the agent fixes the game until the whole suite passes. It changes the game and not
the tests, with one exception: a setup it finds wrong when it rereads it against the invariant
(the ball has no face, two results are possible, the position cannot be reached), which it fixes
and reports in the final table. Weakening an assertion, deleting a test or skipping it is
forbidden. The skill keeps its name, so the prompt is the same file as `playtester`.

The exception is there because the tests of the first matrix are often wrong: `tests_sound` is
0/19 in `playtester_loop_order`, nearly always because of the seam test, which places the ball's
centre on the seam inside both bricks. Without the exception the agent would have to bend the game
to that test, or weaken it.

## Predictions

The `bounce_*` columns are this cell's result, read against `nothing`.

**`bounce_corners` rises from 0/20 to at least half the runs.** The corner test is sound and
red in most runs of `playtester_loop_order`, and a corner is a few lines once the two penetrations
are compared.

**`bounce_tunneling` rises from 0/20, and stays below `bounce_corners`.** Its test is right in
18 of 19 runs, but fixing it means replacing the detection with a swept one rather than
completing it, which is the harder change.

**`bounce_bricks` and `bounce_exit` stay at the level of `nothing`, 18/20 and 19/20.** If they
drop, the fix bent the game to a wrong test.

**`bounce_neighbors` is where a wrong seam test shows.** `nothing` reaches 17/20. If this cell
falls well below, the agent made the game satisfy the seam test as written instead of fixing its
setup, and the exception in step 5 does not work.

**`tests_sound` rises above the 0/19 of `playtester_loop_order`**, for the runs where the agent
fixed a wrong setup on its way to a green suite. The `detects_*` columns are then read on the
tests as they are after the fix.

**Runs take longer, and some may hit the timeout.** `playtester_loop_order` runs have a median of
382 s and a maximum of 793 s, out of 1800 s. A run that times out produces nothing, and
`--until-complete` relaunches it.
