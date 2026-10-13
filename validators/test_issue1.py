#!/usr/bin/env python3
"""Tests of the issue #1 validator, being rebuilt just like the validator itself.

What is covered here: `suite_run`, `skill_invoked` and `probe_intact`, which entered with these
tests, and the **contract of the metrics** - every name a scenario declares is indeed produced,
checked by calling the validator rather than by rereading its text. It is the only omission of
the lot that is discovered only after spending a matrix.

One test on the **material** comes on top: the probe is a single file for its two jobs, and
`scoring_probe()` rewrites nothing but its import line and the guard after it. Both anchors of
that rewrite are guarded here, because an anchor that no longer bites returns an uncorrected
probe - an unexported `frame` would then read as a missing correction, over a whole campaign.

The **reference trees** are covered against real code: the etalon of NEON is cloned once, from
the URL of `trysquare.toml` at the tag the scenario names, and the probe, run as if the agent had
written it, must fail exactly the defect of each variant. `test_quality` is covered the same way.
These tests need `git`, network access to the repository and `node`; without them they are
skipped, and every other test still runs offline.

What is not covered yet: the scoring of the probe on an agent's tree, `in_scope`.

    cd validators
    uv run --project .. python -m unittest test_issue1 -v
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

import issue1
from trysquare.assay import Assay, Metric, ToolCall, report

HERE = Path(__file__).resolve().parent
SCENARIOS = HERE.parent / "scenarios"

# The absolute path of the brick, as `--skill` passed it before trysquare 0.12: archives from then
# are still replayed, and that is the path the agent read in them.
BRICK = "/tmp/campaign/materials/skills/test-gaps/SKILL.md"
# The copy trysquare drops in the clone, which `--skill` points at since 0.12. The same file,
# another path, and the reason why detection is on the file name and not on the path.
COPY = ".pi/skills/test-gaps/SKILL.md"


def read(path: str, **rest) -> ToolCall:
    return ToolCall(name="read", arguments={"path": path, **rest}, failed=False)


def shell(command: str, failed: bool = False) -> ToolCall:
    return ToolCall(name="bash", arguments={"command": command}, failed=failed)


class TestSuiteRun(unittest.TestCase):
    """The column says "the agent ran the suite himself", and it said false 180 times in a row on
    a matrix where all 180 runs had run it.

    The cause was a comparator: `RUN_COMMANDS` was a list of exact strings, and
    `deepseek-v4-flash` prefixes every call with the working directory where `gemma-4-31b` types a
    bare `npm test`. What varies from one model to the next is not the command, it is what the
    agent puts around it, so recognition is a pattern in the command.

    The forms below are **taken from the archives** of `results/`, not imagined: that is what makes
    them useful when a third model brings a fourth one.
    """

    def ran(self, *commands: str) -> Metric:
        return issue1.suite_run(
            Assay.fake(tool_calls=tuple(shell(c) for c in commands))
        )

    def test_the_bare_form_counts(self):
        """`gemma-4-31b`, 133 times in the archives."""
        self.assertTrue(self.ran("npm test"))

    def test_the_form_prefixed_by_the_directory_counts(self):
        """`deepseek-v4-flash`, 664 times: the form the exact comparator refused."""
        self.assertTrue(self.ran("cd /tmp/campaign/ab12/repo && npm test"))

    def test_the_form_with_redirected_output_counts(self):
        """80 times in the archives, and refused as well."""
        self.assertTrue(self.ran("npm test 2>&1 | tail -30"))

    def test_npm_run_test_counts(self):
        self.assertTrue(self.ran("npm run test"))

    def test_node_test_counts_whatever_the_path(self):
        self.assertTrue(self.ran("node --test game/neon.test.js"))
        self.assertTrue(self.ran("cd /tmp/x && node --test"))
        self.assertTrue(self.ran("node game/neon.test.js"))

    def test_a_failing_run_counts_anyway(self):
        """A red suite comes back with `isError`, like a command that does not exist. The suite
        did run, and excluding it would score the quality of the work on the process column.
        """
        metric = issue1.suite_run(
            Assay.fake(tool_calls=(shell("npm test", failed=True),))
        )
        self.assertTrue(metric)

    def test_an_echo_announcing_the_run_is_not_enough_on_its_own(self):
        """The risk that belongs to the pattern, and its bound. The six commands of the archives
        that mention the string without executing it all chain a real run in the same line, so no
        false positive is observable there; this case keeps the only form where the distinction
        would be visible.
        """
        self.assertFalse(self.ran('echo "we should run npm-test"'))

    def test_without_a_run_the_reason_copies_the_commands(self):
        """It is this reason that made the flaw visible: it showed an `npm test` in the list of
        commands "where no run was found".
        """
        metric = self.ran("ls -la", "cat package.json")
        self.assertFalse(metric)
        self.assertIn("ls -la", metric.reason)
        self.assertIn("cat package.json", metric.reason)

    def test_without_any_shell_call_the_reason_says_so(self):
        metric = issue1.suite_run(Assay.fake(tool_calls=(read("game/neon.js"),)))
        self.assertFalse(metric)
        self.assertIn("no shell call", metric.reason)


class TestTestsAdded(unittest.TestCase):
    """The column counts the cases of the suite `npm test` runs, not of one file of it.

    34 archived runs wrote their tests into a new `game/*.test.js` and read false here, because
    only `game/neon.test.js` was counted. `AGENTS.md` only says "the tests are run with `npm test`",
    and `npm test` runs `game/**/*.test.js`: such a file is part of the suite.
    """

    ETALON = {
        "game/neon.test.js": "test('a', () => {});\n" * 6,
        "game/neon.js": "export const x = 1;\n",
        "README.md": "test('not a test file', () => {});\n",
    }

    def counted(self, tree: dict[str, str], given: frozenset[str] = frozenset()) -> Metric:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, text in tree.items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(text)
            return issue1.tests_added(
                Assay.fake(
                    repo=str(root),
                    given=given,
                    files_at_etalon=tuple(self.ETALON),
                    sources_at_etalon=lambda pattern, exclude=None: self.ETALON[pattern],
                )
            )

    def test_cases_added_to_the_existing_file_count(self):
        metric = self.counted({**self.ETALON, "game/neon.test.js": "test('a', () => {});\n" * 8})
        self.assertTrue(metric)
        self.assertIn("2 more cases", metric.reason)

    def test_a_new_test_file_of_the_suite_counts(self):
        metric = self.counted({**self.ETALON, "game/bricks.test.js": "test('b', () => {});\n" * 3})
        self.assertTrue(metric)
        self.assertIn("3 more cases", metric.reason)
        self.assertIn("game/bricks.test.js", metric.reason)

    def test_a_nested_test_file_of_the_suite_counts(self):
        metric = self.counted({**self.ETALON, "game/sub/bricks.test.js": "it('b', () => {});\n"})
        self.assertTrue(metric)

    def test_a_test_file_npm_test_does_not_run_does_not_count(self):
        metric = self.counted({**self.ETALON, ".scratch/repro.test.js": "test('b', () => {});\n"})
        self.assertFalse(metric)

    def test_the_provided_probe_is_not_the_agents_work(self):
        probe = issue1.PROBE.read_text()
        metric = self.counted(
            {**self.ETALON, issue1.PROBE_FILE: probe}, given=frozenset({issue1.PROBE_FILE})
        )
        self.assertFalse(metric)
        self.assertIn("same as at the etalon", metric.reason)

    def test_an_untouched_suite_reads_false(self):
        metric = self.counted(dict(self.ETALON))
        self.assertFalse(metric)
        self.assertIn("6 cases, same as at the etalon", metric.reason)

    def test_cases_removed_read_false(self):
        metric = self.counted({**self.ETALON, "game/neon.test.js": "test('a', () => {});\n" * 4})
        self.assertFalse(metric)
        self.assertIn("2 fewer cases", metric.reason)


class TestSkillInvoked(unittest.TestCase):
    """The column says "the body of the skill entered the context", not "the skill was useful". It
    separates a loaded brick from a brick that was read.

    And it counts **both** mechanisms by which that body arrives, because they leave opposite
    traces: loaded by its name, the agent has to read the `SKILL.md` himself, which is a tool call;
    referenced by `/skill:<name>` in the prompt, it is expanded client side and there is nothing
    left to read. Counting only the first one makes the column false on runs whose prompt carried
    the whole body from beginning to end.
    """

    def invoked(self, *calls: ToolCall, expanded: tuple[str, ...] = ()) -> Metric:
        return issue1.skill_invoked(
            Assay.fake(tool_calls=tuple(calls), skills_expanded=expanded)
        )

    def test_reading_the_brick_counts(self):
        self.assertTrue(self.invoked(read(BRICK)))

    def test_a_skill_expanded_in_the_prompt_counts_without_any_call(self):
        """A prompt that invokes the skill. `/skill:tie-cases-3` gets the whole
        `SKILL.md` pasted into the first message: the body is there before the agent moves, so he
        has no reason to read it and reads none. The reason names the skill, otherwise the green
        column would not say which one."""
        metric = self.invoked(shell("npm test"), expanded=("tie-cases-3",))
        self.assertTrue(metric)
        self.assertIn("tie-cases-3", metric.reason)

    def test_expanded_and_reread_counts_once_per_trace(self):
        """Both mechanisms can coexist - nothing stops an agent from rereading a skill that was
        already pasted for him - and the reason must then say both, because they are not the same
        facts about the session."""
        metric = self.invoked(read(BRICK), expanded=("test-gaps",))
        self.assertTrue(metric)
        self.assertIn("test-gaps", metric.reason)
        self.assertIn(BRICK, metric.reason)

    def test_reading_the_copy_in_the_clone_counts_too(self):
        """Both paths designate the same skill: trysquare loads it through `--skill` **and** copies
        it into `.pi/skills/`, and the agent may read either one. Detection by exact path would
        miss half of them."""
        self.assertTrue(self.invoked(read(COPY)))

    def test_a_cat_in_the_shell_counts(self):
        self.assertTrue(self.invoked(shell(f"cat {COPY}")))

    def test_without_a_read_it_is_false_and_the_reason_says_both_halves(self):
        """The case of the cells without a skill, and that of a cell which has one and does not
        open it. Both return false, and that is what the scenario accepts: the reason is a fact
        about the session, true in both cases.

        It names **both** halves of the question, otherwise a cell whose prompt invokes the skill
        and whose expansion had stopped working would read "the agent did not open the skill"
        instead of "the prompt did not carry it"."""
        metric = self.invoked(read("game/neon.js"), shell("npm test"))
        self.assertFalse(metric)
        self.assertIn("2 tool calls", metric.reason)
        self.assertIn("expanded in the prompt", metric.reason)

    def test_a_run_without_any_call_is_false_and_says_so(self):
        metric = self.invoked()
        self.assertFalse(metric)
        self.assertIn("0 tool calls", metric.reason)

    def test_writing_a_skill_md_is_not_invoking_it(self):
        """A write is not a read. An agent who wrote a `SKILL.md`, out of zeal or by mistake, must
        not mark a process column."""
        write = ToolCall(name="write", arguments={"path": COPY}, failed=False)
        self.assertFalse(self.invoked(write))

    def test_a_failing_call_does_not_count(self):
        """Unlike `suite_run`, where an `npm test` that comes back red did run the suite. Here the
        failing call returned nothing: the body of the skill did not enter the context, so it was
        not invoked."""
        self.assertFalse(self.invoked(shell(f"cat {COPY}", failed=True)))

    def test_a_dedicated_tool_would_count_by_its_name(self):
        """The inventory of tools ages with the agent. pi goes through `read` today
        (`docs/skills.md`); the day it gains a dedicated tool, the column must keep counting
        instead of switching off in silence."""
        future = ToolCall(name="skill", arguments={"name": "test-gaps"}, failed=False)
        self.assertTrue(self.invoked(future))

    def test_without_a_session_the_metric_keeps_quiet_instead_of_saying_false(self):
        """A missing session comes from the harness and says nothing about the agent. `unjudged`
        shrinks the denominator visibly, where false would record a failing the agent did not
        commit."""
        metric = issue1.skill_invoked(Assay.fake())
        self.assertIsNone(report({"skill_invoked": metric})["metrics"].get("skill_invoked"))

    def test_a_base_without_expansion_keeps_quiet_instead_of_counting_half(self):
        """A base older than `skills_expanded` can only answer half the question, and half an
        answer would make every cell whose prompt invokes the skill come out false.
        Keeping quiet shrinks the denominator visibly instead of publishing a column whose reading
        is wrong."""
        metric = issue1.skill_invoked(Assay.fake(tool_calls=(read("game/neon.js"),)))
        self.assertIsNone(report({"skill_invoked": metric})["metrics"].get("skill_invoked"))


class TestProbeIntact(unittest.TestCase):
    """Is the test given to the agent still the one that was given?

    The `add_tests` cells hand the agent the test that judges him, which opens the answer that costs
    nothing: loosen the assertion. The scoring is not fooled, it rewrites its own copy, so this
    column protects nothing, it separates two green runs that did not do the same thing.
    """

    def tree(self, tmp: str, content: str | None) -> Path:
        root = Path(tmp)
        (root / "game").mkdir(parents=True, exist_ok=True)
        if content is not None:
            (root / issue1.PROBE_FILE).write_text(content)
        return root

    def judge(self, tmp: str, content: str | None, provided: bool = True) -> Metric:
        root = self.tree(tmp, content)
        given = frozenset({issue1.PROBE_FILE}) if provided else frozenset()
        return issue1.probe_intact(Assay.fake(repo=str(root), given=given))

    def test_the_probe_as_it_is_is_intact(self):
        with tempfile.TemporaryDirectory() as tmp:
            metric = self.judge(tmp, issue1.PROBE.read_text())
        self.assertTrue(metric.value)

    def test_a_loosened_assertion_is_seen(self):
        """One byte is enough, and that is deliberate: judging the "spirit" of the test would take
        a judge."""
        with tempfile.TemporaryDirectory() as tmp:
            metric = self.judge(tmp, issue1.PROBE.read_text() + "\n")
        self.assertFalse(metric.value)
        self.assertIn("modified", metric.reason)

    def test_a_deleted_probe_is_seen(self):
        with tempfile.TemporaryDirectory() as tmp:
            metric = self.judge(tmp, None)
        self.assertFalse(metric.value)
        self.assertIn("deleted", metric.reason)

    def test_a_cell_without_a_probe_is_not_applicable_rather_than_false(self):
        """"The probe is intact" has no truth value where there is no probe. Without `run.given`,
        the absence of the file would read as a deletion."""
        with tempfile.TemporaryDirectory() as tmp:
            metric = self.judge(tmp, None, provided=False)
        self.assertIsNone(report({"probe_intact": metric})["metrics"].get("probe_intact"))

    def test_the_provided_file_is_indeed_next_door(self):
        """The validator compares the tree against this very file: if it moves, the column lies."""
        self.assertTrue(issue1.PROBE.is_file(), issue1.PROBE)


class TestTheScoringProbe(unittest.TestCase):
    """The probe as the agent reads it, and the same one as it scores.

    A single file holds both jobs, and `scoring_probe()` rewrites its import line for the scoring.
    This is not cosmetic: without that rewrite, a correct fix from an agent who dropped the
    `export` of `frame()` does not even link, and the five columns fall silent together on it.
    With a rewrite that no longer bites because the source moved, it is worse: it falls silent
    without saying so.
    """

    # `paddle` was removed from the probe and from `GROUPS` after the n20 campaign: this test
    # still demanded it, and it therefore failed on a deliberate state of the validator. A list
    # written by hand facing another list is only worth something if both are corrected together;
    # this one is kept because it makes the removal of a column visible, which is never a
    # maintenance gesture but a decision about the experiment.
    EXPECTED_GROUPS = ("brick", "corner", "exit", "neighbors", "tunneling")

    def cases(self, text: str) -> dict:
        """The assertions of each group, as written."""
        groups: dict[str, list[str]] = {}
        current = None
        for line in text.splitlines():
            start = re.match(r"describe\('(\w+)'", line)
            if start:
                current = start.group(1)
                groups[current] = []
            elif current and re.match(r"\s+(test\(|assert\.|state\.(ball|bricks) =)", line):
                groups[current].append(line.strip())
        return groups

    def test_the_probe_carries_the_five_groups_that_GROUPS_declares(self):
        """`bounces()` returns one column per group. A group missing from the probe would read
        "no case played", hence not applicable, on every run of the campaign."""
        self.assertEqual(sorted(self.cases(issue1.PROBE.read_text())), sorted(issue1.GROUPS))
        self.assertEqual(sorted(issue1.GROUPS), sorted(self.EXPECTED_GROUPS))

    def test_the_source_imports_frame_directly_and_not_the_harness_name(self):
        """`internalFrame` is the alias the validator adds to `game/neon.js` itself. A source that
        named it would make the agent write that name, and the second export would be a duplicate:
        the module would no longer compile, in the cells that read the probe."""
        source = issue1.PROBE.read_text()
        self.assertNotIn("internalFrame", source)
        self.assertEqual(source.count(issue1.SOURCE_IMPORT), 1)

    def test_both_anchors_of_the_rewrite_bite_exactly_once(self):
        """The guard of the same name lives in `scoring_probe()`, but it raises there at run time,
        that is to say in the middle of a campaign. Here, it breaks the validator's suite."""
        source = issue1.PROBE.read_text()
        for anchor in (issue1.SOURCE_IMPORT, issue1.GUARD_ANCHOR):
            self.assertEqual(source.count(anchor), 1, anchor)

    def test_the_scoring_goes_through_the_alias_and_keeps_its_grip(self):
        scoring = issue1.scoring_probe()
        self.assertIn(issue1.SCORING_IMPORT, scoring)
        self.assertNotIn(issue1.SOURCE_IMPORT, scoring)
        self.assertIn(issue1.GUARD.strip(), scoring)

    def test_the_scoring_changes_no_case(self):
        """The cells that receive the brick must be scored on what they read, otherwise it measures
        "does the agent guess a second scale" instead of "does he correct himself"."""
        self.assertEqual(
            self.cases(issue1.PROBE.read_text()),
            self.cases(issue1.scoring_probe()),
        )

    def test_a_source_that_drifts_raises_instead_of_scoring_sideways(self):
        """A probe that was not rewritten would score an unexported `frame` as a missing
        correction. Keeping quiet here would cost a whole campaign before anyone noticed, so the
        rewrite raises rather than returning a text it did not manage to correct.

        The drift is played on a real source, copied and reworked: that is the form it will take,
        somebody reordering the import, and not a constant being replaced."""
        drifted = issue1.PROBE.read_text().replace(issue1.SOURCE_IMPORT, "  frame as loop,\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "probe.test.js"
            path.write_text(drifted)
            real, issue1.PROBE = issue1.PROBE, path
            try:
                with self.assertRaises(RuntimeError) as raised:
                    issue1.scoring_probe()
            finally:
                issue1.PROBE = real
        self.assertIn("frame,", str(raised.exception))


# The etalon, cloned once per test run rather than copied into this repository: a copy would keep
# passing after the tag moved, while the campaign would run against the new etalon.
_ETALON: list[Path] = []
_ETALON_HOME = tempfile.TemporaryDirectory(prefix="issue1-etalon-")


def etalon() -> Path:
    """The tree of the measured repository at its etalon, or a skip saying why it is missing."""
    if _ETALON:
        return _ETALON[0]
    if not shutil.which("node"):
        raise unittest.SkipTest("node is needed to run the reference trees")
    url = tomllib.loads((HERE.parent / "trysquare.toml").read_text())["repos"]["neon"]
    tag = tomllib.loads((SCENARIOS / "issue1-skill.toml").read_text())["task"]["etalon"]
    root = Path(_ETALON_HOME.name) / "neon"
    done = subprocess.run(
        ["git", "clone", "--quiet", "--depth", "1", "--branch", tag, url, str(root)],
        capture_output=True,
        text=True,
    )
    if done.returncode != 0:
        raise unittest.SkipTest(f"could not clone {url} at {tag}: {done.stderr.strip()}")
    shutil.rmtree(root / ".git")
    _ETALON.append(root)
    return root


def probe_on(root: Path):
    """What `run.probe` does, on a tree of this machine: copy, drop, write, run, read the JSON."""

    def run(command, write, append, drop, timeout):
        with tempfile.TemporaryDirectory() as where:
            tree = Path(where) / "tree"
            shutil.copytree(root, tree)
            for victim in tree.rglob(drop) if drop else []:
                victim.unlink()
            for name, text in (write or {}).items():
                (tree / name).write_text(text)
            for name, text in (append or {}).items():
                (tree / name).write_text((tree / name).read_text() + text)
            done = subprocess.run(command, cwd=tree, capture_output=True, text=True, timeout=60)
            return json.loads(done.stdout)

    return run


def agent_tree(tmp: str, tests: str) -> Path:
    """The etalon, with `tests` as the agent's `game/neon.test.js` and the game left unfixed."""
    root = Path(tmp) / "agent"
    shutil.copytree(etalon(), root)
    (root / issue1.TEST_FILE).write_text(tests)
    return root


def scored(root: Path) -> dict:
    run = Assay.fake(
        sources_at_etalon=(etalon() / issue1.SOURCE_FILE).read_text(),
        given=(),
        probe=probe_on(root),
    )
    return report(issue1.test_quality(run))


# One face of the brick, written the way the skills ask: a precondition on the contact, then the
# invariant. It catches the wrong axis and nothing else.
LEFT_FACE = """
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { frame, createState, BRICK_W, BRICK_H, BALL_R } from './neon.js';

const ctx = new Proxy({}, { get: () => () => {} });

test('left face flips vx', () => {
  const state = createState(1);
  state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
  state.ball = { x: 96, y: 110, r: BALL_R, vx: 300, vy: 30 };
  assert.ok(state.ball.x + state.ball.r > 100);
  frame(ctx, state);
  assert.ok(state.ball.vx < 0);
  assert.ok(state.ball.vy > 0);
});
"""


class TestTheReferenceTrees(unittest.TestCase):
    """The reference trees are only worth what the probe says of them.

    The probe is the best test suite there is for issue #1, so it is run here as if the agent had
    written it: it must pass everything on the complete correction, fail everything on the etalon,
    and fail exactly the group of each defect on its variant. The etalon's own six tests must pass
    everywhere, since the correction touches nothing they test.
    """

    EXPECTED = {
        "complete": {"brick": 4, "corner": 1, "exit": 4, "neighbors": 2, "tunneling": 1},
        "etalon": {"brick": 0, "corner": 0, "exit": 0, "neighbors": 0, "tunneling": 0},
        "corner": {"brick": 4, "corner": 0, "exit": 4, "neighbors": 2, "tunneling": 1},
        "exit": {"brick": 4, "corner": 1, "exit": 0, "neighbors": 2, "tunneling": 1},
        "neighbors": {"brick": 4, "corner": 1, "exit": 4, "neighbors": 0, "tunneling": 1},
        "tunneling": {"brick": 4, "corner": 1, "exit": 4, "neighbors": 2, "tunneling": 0},
    }

    @classmethod
    def setUpClass(cls):
        etalon()

    def passed(self, variant: str, source: str | None = None) -> dict[str, int]:
        if source is None:
            source = issue1.reference_source((etalon() / issue1.SOURCE_FILE).read_text(), variant)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "tree"
            shutil.copytree(etalon(), root)
            shutil.copy(issue1.PROBE, root / issue1.PROBE_FILE)
            answer = probe_on(root)(
                ["node", "--test", f"--test-reporter={issue1.REPORTER}", "game/**/*.test.js"],
                {issue1.SOURCE_FILE: source},
                None,
                None,
                60,
            )
        self.assertNotIn("error", answer)
        counts: dict[str, int] = {}
        for case in answer["cases"]:
            counts[case["group"]] = counts.get(case["group"], 0) + case["ok"]
        return counts

    def test_each_variant_fails_exactly_its_group(self):
        for variant, expected in self.EXPECTED.items():
            with self.subTest(variant=variant):
                counts = self.passed(variant)
                self.assertEqual(counts.pop("", None), 6, "the etalon's own tests")
                self.assertEqual(counts, expected)

    def test_the_wrong_axis_fails_the_side_faces(self):
        self.assertLess(self.passed("axis")["brick"], 4)

    def test_a_correction_moved_into_step_scores_with_frame_left_as_it_was(self):
        """The probe calls `frame()` first. The etalon's block there switches the brick off
        without a bounce, and a correction moved into `step()` may leave it in place: the game
        never reaches it, since `step()` runs first, so the probe must not either. It undoes what
        a `frame()` that did not deflect did before it tries `step()`."""
        etalon_source = (etalon() / issue1.SOURCE_FILE).read_text()
        moved = "  ball.y += ball.vy * dt;\n"
        self.assertEqual(etalon_source.count(moved), 1)
        source = etalon_source.replace(
            issue1.STEP_ANCHOR, "  __record(ball);\n" + issue1.STEP_ANCHOR
        ).replace(moved, moved + "  __resolveBricks(state);\n")
        source += issue1.REFERENCE_FIX.read_text().replace("__VARIANT__", "complete")
        counts = self.passed("complete", source)
        counts.pop("", None)
        self.assertEqual(counts, self.EXPECTED["complete"])

    def test_a_sweep_that_frame_remembers_between_calls_scores(self):
        """The undo puts back what `frame()` changed, and must keep what it only added.

        A form found in the archives (`agents_no/8f1eeaee` of the DeepSeek-V4.1-Flash n40 matrix,
        among others): `frame()` sweeps from `state.prevBall` and writes it back at its end, for
        the next call. In the game `frame()` runs every tick, so that field always exists. An undo
        that deleted the keys the first `frame()` added left the last `frame()` nothing to sweep
        from, and scored `tunneling` false on a complete correction.
        """
        source = issue1.reference_source((etalon() / issue1.SOURCE_FILE).read_text(), "complete")
        recorded = "  __record(ball);\n" + issue1.STEP_ANCHOR
        read = "  const from = __previous.get(ball);\n  __previous.delete(ball);\n"
        swept = "    __sweep(state, from);\n  }\n}\n"
        for anchor in (recorded, read, swept):
            self.assertEqual(source.count(anchor), 1, anchor)
        source = (
            source.replace(recorded, issue1.STEP_ANCHOR)
            .replace(read, "  const from = state.prevBall;\n")
            .replace(swept, "    __sweep(state, from);\n  }\n  state.prevBall = { x: ball.x, y: ball.y };\n}\n")
        )
        counts = self.passed("complete", source)
        counts.pop("", None)
        self.assertEqual(counts, self.EXPECTED["complete"])


class TestTheReferenceAnchors(unittest.TestCase):
    def test_a_moved_etalon_raises_instead_of_scoring_sideways(self):
        with self.assertRaises(RuntimeError):
            issue1.reference_source("export function frame() {}\n", "complete")


class TestTestQuality(unittest.TestCase):
    """The agent's tests, run for real against the reference trees."""

    @classmethod
    def setUpClass(cls):
        etalon()

    def test_the_probe_as_the_agents_tests_detects_everything(self):
        with tempfile.TemporaryDirectory() as tmp:
            returned = scored(agent_tree(tmp, issue1.PROBE.read_text()))
        for name in issue1.TEST_QUALITY:
            self.assertTrue(returned["metrics"][name], name)

    def test_one_face_detects_the_wrong_axis_and_nothing_else(self):
        with tempfile.TemporaryDirectory() as tmp:
            metrics = scored(agent_tree(tmp, LEFT_FACE))["metrics"]
        self.assertTrue(metrics["tests_sound"])
        self.assertTrue(metrics["tests_red"])
        self.assertTrue(metrics["detects_axis"])
        for name in ("detects_corner", "detects_exit", "detects_neighbors", "detects_tunneling"):
            self.assertFalse(metrics[name], name)

    def test_a_test_that_expects_the_wrong_answer_is_not_sound_and_detects_nothing(self):
        wrong = LEFT_FACE.replace("state.ball.vx < 0", "state.ball.vx > 0")
        with tempfile.TemporaryDirectory() as tmp:
            returned = scored(agent_tree(tmp, wrong))
        self.assertFalse(returned["metrics"]["tests_sound"])
        self.assertIn("left face flips vx", returned["reasons"]["tests_sound"])
        self.assertFalse(returned["metrics"]["detects_axis"])

    def test_a_test_importing_a_name_the_etalon_lacks_is_not_judged(self):
        """Scored false, it would read as tests that detect nothing."""
        coupled = LEFT_FACE.replace("import { frame,", "import { resolveBricks, frame,")
        with tempfile.TemporaryDirectory() as tmp:
            returned = scored(agent_tree(tmp, coupled))
        for name in issue1.TEST_QUALITY:
            self.assertIn(name, returned["unjudged"], name)
        self.assertIn("resolveBricks", returned["unjudged"]["tests_sound"])


class TestJudgeTests(unittest.TestCase):
    """The verdicts alone, from which case passed on which tree."""

    CASE = ("game/neon.test.js", "faces", "left")
    OTHER = ("game/neon.test.js", "faces", "top")

    def played(self, **failing: tuple) -> dict:
        trees = ("complete", "etalon", *issue1.DEFECTS)
        return {
            tree: {case: case not in failing.get(tree, ()) for case in (self.CASE, self.OTHER)}
            for tree in trees
        }

    def test_a_case_that_fails_on_the_correction_detects_nothing(self):
        metrics = issue1.judge_tests(
            self.played(complete=(self.CASE,), etalon=(self.CASE,), axis=(self.CASE,))
        )
        self.assertFalse(metrics["tests_sound"])
        self.assertFalse(metrics["tests_red"])
        self.assertFalse(metrics["detects_axis"])

    def test_a_sound_case_that_fails_on_a_variant_detects_it(self):
        metrics = issue1.judge_tests(self.played(etalon=(self.CASE,), exit=(self.CASE,)))
        self.assertTrue(metrics["tests_sound"])
        self.assertTrue(metrics["tests_red"])
        self.assertTrue(metrics["detects_exit"])
        self.assertFalse(metrics["detects_corner"])
        self.assertIn("faces > left", metrics["detects_exit"].reason)


class TestCatalogueBuilt(unittest.TestCase):
    """The file `dynamic-playtester` wrote beside its skill, as trysquare archived it."""

    def written(self, tmp: str, text: str | None) -> Path:
        root = Path(tmp)
        if text is not None:
            catalogue = root / issue1.DYNAMIC_SKILL / issue1.CATALOGUE
            catalogue.parent.mkdir(parents=True)
            catalogue.write_text(text)
        return root

    def test_entries_are_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Assay.fake(
                skills_expanded=(issue1.DYNAMIC_SKILL,),
                skills=str(self.written(tmp, "## breakout\n\n#### a\n\n#### b\n")),
            )
            metric = issue1.catalogue_built(run)
        self.assertTrue(metric)
        self.assertEqual(metric.reason, "2 entries")

    def test_no_file_is_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Assay.fake(
                skills_expanded=(issue1.DYNAMIC_SKILL,), skills=str(self.written(tmp, None))
            )
            self.assertFalse(issue1.catalogue_built(run))

    def test_an_empty_catalogue_is_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Assay.fake(
                skills_expanded=(issue1.DYNAMIC_SKILL,), skills=str(self.written(tmp, "## x\n"))
            )
            self.assertFalse(issue1.catalogue_built(run))

    def test_another_skill_is_not_applicable(self):
        metric = issue1.catalogue_built(Assay.fake(skills_expanded=("playtester",)))
        self.assertIsNone(report({"catalogue_built": metric})["metrics"].get("catalogue_built"))


class TestTheMetricContract(unittest.TestCase):
    """What the validator returns, obtained by calling it.

    The fake only provides what the validator reads and refuses to invent the rest, so this list
    **is** the inventory of its dependencies: one read more makes this test fail instead of passing
    on an empty value.
    """

    def full_run(self, root: Path) -> Assay:
        (root / "game").mkdir(parents=True, exist_ok=True)
        (root / issue1.TEST_FILE).write_text("test('a', () => {});\n")
        return Assay.fake(
            repo=str(root),
            touched=frozenset({issue1.SOURCE_FILE}),
            sources_at_etalon="",
            probe={"cases": [{"group": key, "ok": True} for key in issue1.GROUPS]},
            tool_calls=(read(BRICK),),
            # A cell that loads the skill by its name and goes to read it: the prompt expands
            # none, and that is a measurement and not an absence of measurement. Declaring it is
            # what makes this test fail the day `skill_invoked` gains a read, which is the
            # information we want.
            skills_expanded=(),
        )

    def test_every_declared_metric_is_produced(self):
        with tempfile.TemporaryDirectory() as tmp:
            produced = set(issue1.evaluate(self.full_run(Path(tmp))))
        files = sorted(SCENARIOS.glob("*.toml"))
        self.assertTrue(files, "no scenario to check")
        for name in files:
            scenario = tomllib.loads(name.read_text())
            for block in scenario.get("validation", []):
                missing = set(block.get("metrics", ())) - produced
                self.assertEqual(missing, set(), f"{name.name} declares {missing}")

    def test_a_missing_read_never_becomes_a_false(self):
        """The fake only provides `touched`, so these metrics have nothing to read.

        None of them returns false. That is the invariant that counts: a missing measurement and a
        failed measurement are not the same thing, and the denominator shrinks visibly instead of
        recording a failing the agent did not commit.

        The validator has no read that *raises* - `or_unjudged` and the three `except` convert
        them all - so the useful guarantee is not that it refuses, it is what it returns when it
        cannot judge.
        """
        returned = report(issue1.evaluate(Assay.fake(touched=frozenset())))
        for name in (
            "tests_added",
            "suite_run",
            "skill_invoked",
            "catalogue_built",
            "bounce_bricks",
            "tests_red",
        ):
            self.assertIn(name, returned["unjudged"], name)
            self.assertIsNone(returned["metrics"].get(name), name)

    def test_a_reason_is_attached_only_if_it_says_something(self):
        """A reason is published whether it carries a success or a failure, the base being unable
        to filter. So it is up to the validator to keep quiet when it has nothing to say."""
        with tempfile.TemporaryDirectory() as tmp:
            returned = report(issue1.evaluate(self.full_run(Path(tmp))))
        self.assertTrue(returned["metrics"]["delivered"])
        self.assertNotIn("delivered", returned["reasons"])
        # This one, on the other hand, says which skill was read even on success: that is what
        # makes the column readable when several bricks can turn it true.
        self.assertIn("skill_invoked", returned["reasons"])


if __name__ == "__main__":
    unittest.main()
