#!/usr/bin/env python3
"""Tests of the issue #1 validator, being rebuilt just like the validator itself.

What is covered here: `skill_invoked` and `probe_intact`, which entered with these tests, and the
**contract of the metrics** - every name a scenario declares is indeed produced, checked by
calling the validator rather than by rereading its text. It is the only omission of the lot that
is discovered only after spending a matrix.

One test on the **material** comes on top: the probe is a single file for its two jobs, and
`scoring_probe()` rewrites nothing but its import line. Both anchors of that rewrite are guarded
here, because an anchor that no longer bites returns an uncorrected probe - an unexported `frame`
would then read as a missing correction, over a whole campaign.

What is not covered yet: the probe and its fixtures, `tests_added`, `in_scope`. They were covered
by an earlier version of these tests, against real trees, and their rebuild waits for the rebuild
of the fixtures.

    cd validators
    uv run --project .. python -m unittest test_issue1 -v
"""

from __future__ import annotations

import re
import tempfile
import tomllib
import unittest
from pathlib import Path

import issue1
from trysquare.assay import Assay, Metric, ToolCall, report

HERE = Path(__file__).resolve().parent
SCENARIOS = HERE.parent / "scenarios"

# The absolute path of the brick, as `--skill` passes it: this is the form in which the agent sees
# the skill, and therefore the form in which he reads it.
BRICK = "/tmp/campaign/materials/skills/test-gaps/SKILL.md"
# The copy trysquare drops in the clone. The same file, another path, and the reason why detection
# is on the file name and not on the path.
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


class TestSkillInvoked(unittest.TestCase):
    """The column says "the body of the skill entered the context", not "the skill was useful". It
    separates a loaded brick from a brick that was read.

    And it counts **both** mechanisms by which that body arrives, because they leave opposite
    traces: loaded by its name, the agent has to read the `SKILL.md` himself, which is a tool call;
    referenced by `/skill:<name>` in the prompt, it is expanded client side and there is nothing
    left to read. Counting only the first one made the five runs of
    `well crafted stack +skill-tie-3-force` false although the body was in their prompt from
    beginning to end.
    """

    def invoked(self, *calls: ToolCall, expanded: tuple[str, ...] = ()) -> Metric:
        return issue1.skill_invoked(
            Assay.fake(tool_calls=tuple(calls), skills_expanded=expanded)
        )

    def test_reading_the_brick_counts(self):
        self.assertTrue(self.invoked(read(BRICK)))

    def test_a_skill_expanded_in_the_prompt_counts_without_any_call(self):
        """The `-force` case, and the one that was missing. `/skill:tie-cases-3` gets the whole
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

        It names **both** halves of the question, otherwise a `-force` cell whose expansion had
        stopped working would read "the agent did not open the skill" instead of "the prompt did
        not carry it"."""
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
        answer is exactly the flaw that was just fixed: every `-force` cell would come out false.
        Keeping quiet shrinks the denominator visibly instead of publishing a column whose reading
        is wrong."""
        metric = issue1.skill_invoked(Assay.fake(tool_calls=(read("game/neon.js"),)))
        self.assertIsNone(report({"skill_invoked": metric})["metrics"].get("skill_invoked"))


class TestProbeIntact(unittest.TestCase):
    """Is the test given to the agent still the one that was given?

    The `+probe` cell hands the agent the test that judges him, which opens the answer that costs
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
    This is not cosmetic: without that rewrite, a correction left inside `frame()` - where the
    comment in the repo sends it - does not even link, and the six columns fall silent together on
    a correct run. With a rewrite that no longer bites because the source moved, it is worse: it
    falls silent without saying so.
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
        the module would no longer compile, in the only cell that reads the probe."""
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
        """The cell that receives the brick must be scored on what it read, otherwise it measures
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
            # what makes this test fail the day `skill_invoked` gains a read - which has just
            # happened, and that is the information we want.
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
        """The fake only provides `touched`, so four metrics have nothing to read.

        None of them returns false. That is the invariant that counts: a missing measurement and a
        failed measurement are not the same thing, and the denominator shrinks visibly instead of
        recording a failing the agent did not commit.

        The validator no longer has a read that *raises* - `or_unjudged` and the three `except`
        convert them all - so this test replaces the one that expected an exception: the useful
        guarantee is not that it refuses, it is what it returns when it cannot judge.
        """
        returned = report(issue1.evaluate(Assay.fake(touched=frozenset())))
        for name in ("tests_added", "suite_run", "skill_invoked", "bounce_bricks"):
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
