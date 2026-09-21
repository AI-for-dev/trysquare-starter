#!/usr/bin/env python3
"""Validator for NEON issue #1: the ball goes through the bricks.

Rebuilt from nothing, one metric at a time, and each one enters here with its tests and its
declaration in the scenario. A metric the scenario declares and this file does not produce
makes the run invalid: the contract breaks before the spending, not after.

Written on top of `trysquare.assay`, which carries the contract - one argument, JSON on
stdout, and three separate states: I judged, I could not judge *this metric*, I could not
judge *this run*. What is left here is the domain, and nothing else.

Current state: `delivered`, `in_scope`, `tests_added`, `suite_run`, `skill_invoked`,
`probe_intact`, and the six columns of the probe.
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

from trysquare.assay import Assay, CannotJudge, Metric, ProbeTimeout, validator

HERE = Path(__file__).resolve().parent

# The probe, as **a single file** for its two jobs. A `kind = "files"` brick drops it in the tree
# of one cell before the agent starts, at this very path, and commits it on the etalon: that cell
# works with the red suite and the specification in front of it. Every cell, that one included,
# is then scored by this same file, dropped into a copy of the measured tree outside the clone
# and run like the suite of the repo.
#
# Two twin files held that role before, one for the brick and one for the scoring. They differed
# only by their import line and by the two latent groups, and their eleven shared cases had to
# stay copied fixture by fixture, without which the cell would have measured "does the agent
# guess a second scale" instead of "does the agent correct itself". An invariant no test could
# state without rewriting the comparison at every case added: that is the kind of gap that widens
# in silence, so the two files are now one and the only line that separated them is rewritten
# here, see `scoring_probe()`.
PROBE = HERE.parent / "materials" / "provided-probe" / "probe.test.js"
PROBE_FILE = "game/probe.test.js"

# The `node:test` reporter that renders the result of the probe as JSON, because `node --test`
# only prints text for humans and `probe` reads JSON. It stays **here** and does not enter the
# copy: this is measuring machinery, while the copy must carry nothing but the agent's work and
# the tests that judge it.
REPORTER = HERE / "reporter.mjs"

SOURCE_FILE = "game/neon.js"
TEST_FILE = "game/neon.test.js"

# The only line the validator adds to the agent's `game/neon.js`. Brick collision lives in
# `frame()`, which the repo does not export: without this line, the probe would not reach the
# correction of an agent who leaves the bounce where the comment in the repo points, and would
# therefore only reach the cells that refactored along the way.
#
# An alias and not `export { frame }`: an agent who exported `frame` himself would make a
# duplicate, and the module would no longer compile. `typeof` first because an agent who moved
# `frame` elsewhere leaves nothing to export, and exporting a name that does not exist breaks the
# linking of the whole module - the probe could not even judge the walls.
INTERNAL_EXPORT = "\nexport const internalFrame = typeof frame === 'undefined' ? null : frame;\n"

# The only thing separating the probe as the agent reads it from the probe as it scores: its
# import line, and the guard that goes with it.
#
# The source imports `frame` directly, and that is what it must do. The cell that receives it has
# to export the render loop for the file to even run, its header says so, and `internalFrame` is a
# harness name that has no business under an agent's eyes: he would write it into `game/neon.js`,
# where adding `INTERNAL_EXPORT` would make it a duplicate export and the module would no longer
# compile.
#
# But the other cells receive nothing, and nothing in issue #1 asks them to export `frame`:
# scoring them on that import would make any correction left inside `frame()` unjudgeable, that is
# to say precisely where the comment in the repo sends it. The module would not even link - "does
# not provide an export named 'frame'" - and the six columns would fall silent together on a
# correct fix. The scoring copy therefore goes through the alias.
SOURCE_IMPORT = "  frame,\n"
SCORING_IMPORT = "  internalFrame as frame,\n"

# `internalFrame` is `null` when the agent moved `frame` out of the module: there was nothing to
# export then. The probe has lost its grip on the render loop and says so, instead of playing
# fifteen cases each of which would die on the same TypeError. The guard has no place in the
# source, where the direct import makes it unreachable: a missing `frame` there breaks the linking
# of the module before a single line runs.
GUARD_ANCHOR = "} from './neon.js';\n"
GUARD = "\nif (!frame) throw new Error('frame() cannot be found in game/neon.js');\n"

# The files the ticket puts within reach. The test file is **in**: issue #1 asks for the edge
# cases "first as red tests, then green", so touching them is the work asked for and not an
# overflow.
#
# This is a property of the **task**, identical for every cell. Only the well crafted ticket
# writes the constraint ("Only modify game/neon.js and game/neon.test.js"), but reading the cell
# to widen the scope would score each configuration with its own ruler - and the question the
# matrix asks is precisely whether framing the ticket changes what the agent touches.
#
# The provided probe is **not** in it, and that is deliberate: it is given to the agent to be read
# and satisfied, not to be edited. A cell that touches it therefore leaves the scope, and
# `probe_intact` says in which way - overflow and cheating are two readings, the table carries
# them separately.
SCOPE = frozenset({SOURCE_FILE, TEST_FILE})

# A test case, at the start of a line. Anchored there rather than looked for anywhere, otherwise
# `assert.equal(collides(ball, brick), true)` and the word "test" in a comment would count.
# `node:test` accepts `test`, `it` and their `.skip` / `.only` / `.todo` variants; the etalon only
# uses `test(`, and its six cases all start a line.
TEST_CASE = re.compile(r"^\s*(?:test|it)(?:\.\w+)?\s*\(", re.M)

# One `describe` of the probe gives one metric. The probe judges nothing, it reports case by case;
# the grouping is here, in a single place.
#
# `bounce_domain` existed and was removed. It played the walls of the field, which already bounce
# at the etalon: the column was green everywhere, including on runs that had delivered nothing,
# and therefore separated no cell of the matrix.
#
# The first four columns judge the correction that was asked for, from the coarsest to the finest,
# and they really do separate from one another: `exit` blackens a correction that flips the speed
# without taking the ball back out of the brick, `neighbors` blackens the one that counts the
# bounce twice when the ball overlaps two bricks of the same seam of the grid.
#
# The last two - `tunneling` and `paddle` - are **latent** bugs that issue #1 does not ask anyone
# to fix. It is the exact mirror of the flaw that got `bounce_domain` removed, and they are kept
# anyway, for a reason that one did not have: a column that is green everywhere does not
# distinguish "fixed" from "delivered nothing" and is therefore read as a success by mistake,
# whereas a black column states a verifiable fact about the matrix - nobody went beyond what the
# ticket named. They carry no verdict and enter no criterion.
#
# They are no longer black *everywhere*, and that is the accepted counterpart of the single file:
# the probe being dropped as is in the cell that receives the brick, that cell reads these two
# groups and can make them pass. The line is then read for what it is - "an agent who is shown
# these cases fixes them, the others never see them" - and not as a measure comparable to the
# first four columns, which are the only ones every cell is judged on with the same ruler.
GROUPS = {
    "brick": "bounce_bricks",
    "corner": "bounce_corners",
    "exit": "bounce_exit",
    "neighbors": "bounce_neighbors",
    "tunneling": "bounce_tunneling",
}

# The commands that run the suite, recognised by **a pattern in the command** and not by string
# equality.
#
# This list used to be a list of exact strings, on the grounds that a pattern decides in advance
# about what nobody has seen yet, where a list is completed by looking at what the agents actually
# typed. The argument was right and the conclusion wrong: what varies from one model to the next is
# not *which* command runs the suite, it is what the agent puts around it. The
# `..._opencode-go_deepseek-v4-flash_n20` matrix returned `suite_run` false in its nine cells,
# 0/180, while all 180 runs had run the suite: that model prefixes every call with the working
# directory (`cd /private/var/.../repo && npm test`, 664 times) and readily redirects the output
# (`npm test 2>&1 | tail -30`, 80 times), while `gemma-4-31b` types a bare `npm test`. A column
# blackened end to end by the comparator, on a process metric, reads like a behaviour and is not
# one.
#
# The risk of the pattern is the opposite one: counting a *mention* as a run, in an
# `echo "=== npm test ==="` or a `grep 'npm test' package.json`. It was looked for in the 360
# archived runs - six commands contain the string in a non executing form, and **all six** chain a
# real run in the same line. No false positive, then, and the reason below copies the command that
# was accepted, which makes every true as well as every false checkable by hand in the table.
RUN_COMMANDS = (
    # the form the well crafted ticket names, and `npm run test`, which is the same call for npm
    re.compile(r"\bnpm (?:run )?test\b"),
    re.compile(r"\bnode --test\b"),
    re.compile(r"\bnode +\S*neon\.test\.js\b"),
)

# The file name of a skill, and the trace left by **one** of the two ways of invoking it. The
# other - expansion in the prompt - goes through no tool and is read in `run.skills_expanded`;
# `skill_invoked` says why both are needed.
#
# pi has **no** dedicated tool for skills. Its `docs/skills.md` describes the mechanism: the system
# prompt receives only the name and the description of each loaded skill, and "when a task matches,
# the agent uses `read` to load the full SKILL.md" - the same page adding that "models don't always
# do this". A skill loaded by its name is therefore invoked by a read of its `SKILL.md`, and the
# gap between "loaded" and "read" is what the column exists to show on those cells.
#
# The file name rather than the path in the scenario, for two reasons. trysquare loads the skill
# twice - `--skill` on the absolute path of the brick, and a copy in `.pi/skills/<name>/` of the
# clone - so two paths designate the same read. And a brick name that changes must not turn the
# column falsely black: the reason is what says *which* skill was read.
SKILL_MD = "SKILL.md"

# The tools that can read a file without writing it. A write to a `SKILL.md` is not an invocation,
# and an agent who wrote one must not mark the column.
READS = frozenset({"read", "bash"})


@validator
def evaluate(run: Assay) -> dict:
    # Every reason is attached **on condition**. A reason is published whether it carries a
    # success or a failure - the base cannot filter, "failing" being definable only for a
    # boolean - so this is where one has to say nothing when there is nothing to say.
    outside = run.touched - SCOPE

    return {
        "delivered": Metric(
            bool(run.touched),
            "" if run.touched else "no file modified: the agent did not work",
        ),
        # An agent who touched nothing did not respect the scope, he did not work: without this
        # guard, `not outside` would be true on an empty set and the most inert cell of the
        # matrix would hold the best column.
        "in_scope": Metric(
            bool(run.touched) and not outside,
            f"also touched {', '.join(sorted(outside))}" if outside else "",
        ),
        # Diagnosis: there is no median of ["game/neon.js"], but this is what makes a false
        # `in_scope` readable without opening the diff.
        "touched": run.touched,
        "tests_added": or_unjudged(lambda: tests_added(run)),
        "suite_run": suite_run(run),
        "skill_invoked": skill_invoked(run),
        "probe_intact": or_unjudged(lambda: probe_intact(run)),
        **bounces(run),
    }


def or_unjudged(read) -> Metric:
    """A metric this run cannot answer, said as such.

    Without it, a single metric without an answer refuses the run and takes **all the others
    with it**, including the one that carries the verdict. The denominator shrinks visibly
    (`9/10` in the table) instead of recording a failure the agent did not deserve.
    """
    try:
        return read()
    except CannotJudge as why:
        return Metric.unjudged(str(why))


def tests_added(run: Assay) -> Metric:
    """Did the agent add test cases to `game/neon.test.js`?

    Issue #1 asks for the edge cases "first as red tests, then green", so this is an explicit
    requirement of the ticket. Counted against the etalon and not against zero: the file already
    carries six, so "the file contains tests" would be true for an agent who never touched it.

    The count is an **honest lower bound** and not a coverage measure. An agent who replaces one
    existing case by two new ones scores `+1` although he added two, and a `for` over a table of
    cases only adds one to the count. The question asked is "did he add any", for which a count is
    enough; "how many" would require running the suite and reading its report, which is the job of
    `tests`.
    """
    reference = TEST_CASE.findall(run.sources_at_etalon(TEST_FILE))
    file = run.repo / TEST_FILE

    if not file.is_file():
        return Metric(False, f"{TEST_FILE} no longer exists in the measured tree")

    after = TEST_CASE.findall(file.read_text(errors="replace"))
    gained = len(after) - len(reference)
    if gained > 0:
        return Metric(
            True,
            f"{gained} more cases than at the etalon ({len(after)} against {len(reference)})",
        )
    if gained == 0:
        return Metric(False, f"{len(after)} cases, same as at the etalon")
    return Metric(
        False,
        f"{-gained} fewer cases than at the etalon ({len(after)} against {len(reference)})",
    )


def probe_intact(run: Assay) -> Metric:
    """Is the provided probe still the one that was provided?

    The `+probe` cell hands the agent the test that judges him. That is the whole point of the
    question asked - does he correct himself when he already has the tests he needs - and it is
    also the open door to the answer that costs nothing: loosen the assertion until it passes.
    The scoring is not fooled, `bounces()` rewriting its own copy of the probe in the tree it
    judges, so this column protects nothing. It **tells**: two runs green on `bounce_bricks` are
    not worth the same depending on whether the test given was satisfied or rewritten.

    Three states, and the third one is the reason `run.given` exists. A missing file is a fact
    with two causes - never provided, or deleted along the way - and without the list of what the
    harness dropped, a run that erases the test it was given would read exactly like the six cells
    that never received one.

    **Not applicable in those six**, and that differs from `skill_invoked`, which is false there:
    "no `SKILL.md` was read" is a true fact about those sessions, whereas "the probe is intact" has
    no truth value where there is no probe. Returned without reading the name of the cell - the
    tree and the archive are what answer, not the configuration - so every cell is indeed scored
    with the same ruler.
    """
    if PROBE_FILE not in run.given:
        return Metric.unjudged("no probe was provided to this cell")

    file = run.repo / PROBE_FILE
    if not file.is_file():
        return Metric(False, "the provided probe was deleted from the tree")

    if file.read_text(errors="replace") != PROBE.read_text():
        return Metric(False, "the provided probe was modified")

    return Metric(True)


def scoring_probe() -> str:
    """The probe of the brick, with the alias in place of the direct import.

    Two substitutions on a file that stays, for everything else, the one the agent had in front of
    him: same fixtures, same assertions, same order. That is the condition for the cell that
    receives the brick to measure "does the agent correct himself" and not "does the agent guess a
    second scale".

    An anchor that does not match is a mistake of this repository, not an answer from the agent:
    it raises instead of returning an uncorrected probe, which would score an unexported `frame`
    as a missing correction. `test_issue1.py` stands guard over both anchors, so that reworking
    the import line breaks the validator's suite before it costs a campaign.
    """
    text = PROBE.read_text()
    for pattern in (SOURCE_IMPORT, GUARD_ANCHOR):
        if text.count(pattern) != 1:
            raise RuntimeError(
                f"{PROBE.name}: the anchor {pattern!r} should have been found exactly once, "
                f"found {text.count(pattern)} times. The import rewrite has to be redone."
            )
    text = text.replace(SOURCE_IMPORT, SCORING_IMPORT)
    return text.replace(GUARD_ANCHOR, GUARD_ANCHOR + GUARD)


def bounces(run: Assay) -> dict:
    """The six columns of the probe, from a single run.

    A behaviour is executed instead of being recognised: no pattern in the diff, no judge, no
    tokens, and a wrong answer is an assertion that breaks. The probe runs on a copy of the
    measured tree, after all the work of the agent.

    These are ordinary `node:test` tests, run by the command of `npm test`. What the copy receives
    comes down to three gestures: the agent's tests go, the probe takes their place with its import
    line rewritten - see `scoring_probe()` - and one line exports `frame` under the alias that this
    rewrite imports.

    `bounce_bricks` carries the criterion. It is the hard half of the ticket, and it is for it that
    this task was chosen: four faces, each of which requires the axis that was hit to flip and the
    other one not to move. The next three columns tighten the same correction more and more, each
    one blackening an incomplete form that the previous one let through:

      `bounce_corners`    the corner, where the ball arrives diagonally and both components must
                          flip. A correction that compares the two penetrations and flips only one
                          of them passes the four faces and fails here.
      `bounce_exit`       the ball has come back out of the rectangle. This is the second half of
                          the correction the comment in the repo describes, and a correction that
                          flips without repositioning leaves the bounce sticky.
      `bounce_neighbors`  two bricks of the same seam of the grid, hit in the same pass: the bounce
                          must apply once. A `vy = -vy` counted twice cancels out and the ball goes
                          through.

    The last two are latent bugs issue #1 does not ask for - `bounce_tunneling` for tunneling,
    `bounce_paddle` for the three flaws of the paddle. The comment on `GROUPS` says why they are
    kept, and why the cell that receives the brick is the only one that can make them pass: it
    reads the probe, so it sees those cases too.

    Checked on six trees, without spending a token, and the table is the deliverable of that check
    (columns in the order above):

      etalon untouched                       0/4  0/1  0/4  0/2  0/1  0/3
      per face, without repositioning        4/4  0/1  0/4  0/2  0/1  0/3
      per face, with repositioning           4/4  0/1  4/4  2/2  0/1  0/3
      complete: corner + exit + sweep        4/4  1/1  4/4  2/2  1/1  0/3
      the same, extracted into `step()`      4/4  0/1  4/4  2/2  0/1  0/3
      `frame` renamed                        no case at all, and the reason for that silence

    The second to last line is the one that matters for the machinery: it is the refactor issue #2
    invites, it carries exactly the same correction as the third one, and it must therefore be
    scored the same. It was not: `play()` falls back on `step()`, which integrates before it
    resolves, and the move blackened `bounce_neighbors` on a correct fix. The speeds of that
    fixture were lowered for that reason; the probe says so.

    Checked again after the two probes were merged into one file, on four trees and without
    spending a token. The first three return the same fifteen verdicts as before the merge, case by
    case and detail by detail; the fourth is the one that counts, since it establishes that the six
    columns are **reachable** and that none is black by construction:

      etalon untouched                         0/4  0/1  0/4  0/2  0/1  0/3
      corner + exit, inside `frame()`          4/4  1/1  4/4  2/2  0/1  0/3
      the same, extracted into `step()`        4/4  1/1  4/4  2/2  0/1  0/3
      the same + sweep + paddle fixed          4/4  1/1  4/4  2/2  1/1  3/3

    The six metrics fail or fall silent **together** when the probe could not run: it is a single
    run, so a single thing can be missing.
    """
    try:
        probe = run.probe(
            # The command of the repo, the one `npm test` runs. The reporter does not change what
            # runs, only the way the result is printed.
            ["node", "--test", f"--test-reporter={REPORTER}", "game/**/*.test.js"],
            write={PROBE_FILE: scoring_probe()},
            append={SOURCE_FILE: INTERNAL_EXPORT},
            # The agent's tests go: they do not measure what is measured here, and their cases
            # would mix with the cases of the probe in the same report. What they are worth is the
            # `tests` column, which runs them where that is their job.
            drop="*.test.js",
        )
    except ProbeTimeout as e:
        # A probe is a matter of milliseconds. Going past that means the agent's correction loops
        # forever, which is a failure of the agent and not of the harness. The base refuses by
        # default, and this is where we know more than it does.
        return {
            name: Metric(False, f"the correction does not terminate: {e}") for name in GROUPS.values()
        }
    except CannotJudge as e:
        return {name: Metric.unjudged(str(e)) for name in GROUPS.values()}

    if probe.get("error"):
        return {
            name: Metric.unjudged(f"probe impossible: {probe['error']}")
            for name in GROUPS.values()
        }

    played = probe.get("cases") or []
    return {name: group(played, key) for key, name in GROUPS.items()}


def group(played: list[dict], key: str) -> Metric:
    """A group of cases, and the name of those that failed.

    Saying which case failed and not only that there was one: "left side: vy flipped instead of
    vx, vx 300 -> 300" names a correction that picked the wrong axis, and that run does not read
    like one that did nothing.
    """
    cases = [c for c in played if c.get("group") == key]
    if not cases:
        return Metric.unjudged(f"the probe played no case of {key}")
    failed = [c for c in cases if not c.get("ok")]
    # With no failure to report, the details of the cases that carry one are reported anyway. That
    # is what lets a green column say "deflected by step() and not by frame()": the correction is
    # right, and its shape is information about the refactor.
    notable = failed or [c for c in cases if c.get("detail")]
    return Metric(
        not failed,
        " ; ".join(f"{c.get('name')}: {c.get('detail')}" for c in notable),
    )


def suite_run(run: Assay) -> Metric:
    """Did the agent run the suite himself, at least once?

    A **process** metric, read in the archived session: it says what the agent did, where `tests`
    says in which state he left the repo. The two separate in both directions, and that is why it
    exists: an agent who fixes correctly without ever checking leaves a green suite, and an agent
    who runs the suite and leaves red still did check.

    **A failing call counts.** In the archived sessions, `npm test` on a red suite comes back with
    `isError` true, exactly like a command that does not exist: the suite did run, and excluding it
    would score the quality of the work on the process column. This is the opposite of
    `ToolCall.wrote`, where a failing call wrote nothing.

    False copies out the commands the run did launch, and that is what makes `RUN_COMMANDS`
    completable: an unrecognised form can be read in the table instead of disappearing into a zero
    one would believe deserved.
    """
    try:
        calls = run.tool_calls()
    except CannotJudge as e:
        return Metric.unjudged(str(e))

    commands = {
        " ".join(str(call.arguments["command"]).split())
        for call in calls
        if "command" in call.arguments
    }
    launched = {c for c in commands if any(pattern.search(c) for pattern in RUN_COMMANDS)}
    if launched:
        return Metric(True, " ; ".join(sorted(launched)))
    if not commands:
        return Metric(False, "no shell call")
    return Metric(False, f"no run among: {' ; '.join(sorted(commands))}")


def skill_invoked(run: Assay) -> Metric:
    """Did the body of a skill enter the agent's context?

    A **process** metric, like `suite_run`, and read in the same place: the archived session, so
    replayable without spending a token. It does not say whether the skill was useful, it says
    whether its text was in front of the model - the difference between a loaded brick and a brick
    that was used, which is the first thing a cell with a skill has to establish. Without it, an
    unchanged `bounce_bricks` would read "the skill is useless" when it may say "the skill was
    never opened".

    **The two ways of loading a skill leave opposite traces**, and counting only the first one made
    this column false on three full cells:

    - `harness = ["skills-tie-cases-3"]` alone: pi puts only the name and the description in the
      system prompt, and "when a task matches, the agent uses `read` to load the full SKILL.md" -
      so the invocation **is** a tool call, and the agent may not make it (3 times out of 5 in
      `+skill-tie-3`, the same page adding that "models don't always do this").
    - a `/skill:<name>` in the prompt, which is what `issue1-simple-prompt-with-skill.md`
      does: pi expands the reference **client side** and pastes the whole `SKILL.md` into the first
      message. There is nothing left to read, so no call left to count, and the five runs of
      `well crafted stack +skill-tie-3-force` came out false although the body of the skill was in
      the prompt from beginning to end.

    That is why the column says "entered the context" and not "went to fetch it": the second has no
    meaning in a `-force` cell, where the operator answered in the agent's place. The gap between
    the two cells - initiative against constraint - is exactly the effect `-force` exists to
    measure, and it can only be read if both mechanisms mark the column.

    **It stays structurally false in the cells without a skill**, and that is deliberate rather
    than made undecidable. What it states is a fact about the session - no skill body entered it -
    and it is true there too. Making it "not applicable" would require reading the name of the
    cell, hence scoring each configuration with its own ruler, and a rename in the TOML would
    switch the column off without a word.

    The inventory of tools ages with the agent: a future tool dedicated to skills would count by
    its **name** (`skill` in it), failing which the column would switch off in silence the day pi
    stopped going through `read`.
    """
    try:
        calls = run.tool_calls()
        expanded = run.skills_expanded
    except CannotJudge as why:
        return Metric.unjudged(str(why))

    reads: set[str] = {f"{name} expanded in the prompt" for name in expanded}
    for call in calls:
        if call.failed:
            continue
        if "skill" in call.name.lower():
            reads.add(f"tool {call.name}")
            continue
        if call.name not in READS:
            continue
        path = call.arguments.get("path")
        if isinstance(path, str) and PurePosixPath(path).name == SKILL_MD:
            reads.add(path)
            continue
        command = call.arguments.get("command")
        if isinstance(command, str) and SKILL_MD in command:
            reads.add(" ".join(command.split()))

    if reads:
        return Metric(True, " ; ".join(sorted(reads)))
    # Both halves of the question, in the reason: without the first one, a `-force` cell whose
    # expansion had stopped working would read "the agent did not open the skill" instead of "the
    # prompt did not carry it".
    return Metric(
        False,
        f"no skill expanded in the prompt, and no {SKILL_MD} read "
        f"over {len(calls)} tool calls",
    )


if __name__ == "__main__":
    raise SystemExit(evaluate.cli())
