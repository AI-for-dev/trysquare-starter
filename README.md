# trysquare-starter

Everything needed to replay one experiment of the course, `issue1-context`, in an environment you
throw away afterwards: the context levers of module 2.1 measured against the bounce of issue #1 of
NEON, nine configurations, one lever at a time.

The repository does not contain the measuring tool. [trysquare](https://github.com/AI-for-dev/trysquare)
is a Python package installed in a local venv; what lives here is the material of the experiment,
that is to say the scenario, the pieces given to the agent, the hypothesis written before
measuring, and the validator that scores.

## What you need before starting

| prerequisite | why |
| --- | --- |
| `uv` | creates the venv and installs trysquare |
| `node` >= 20 | the scoring probe is a `node:test` suite, run with `--test-reporter` |
| `git` | trysquare clones NEON on its tag, and the validator reads its reference there |
| `pi` | the harness being measured, installed from [pi.dev](https://pi.dev) |
| a model provider | declared in `~/.pi/agent/models.json`, see [the pi documentation](https://pi.dev/docs/latest/providers) |
| network access | GitHub for NEON and the extension, TestPyPI and PyPI for the installation, the provider for the calls |

### Install pi

pi is the agent harness the matrix measures. Its official installer:

```bash
curl -fsSL https://pi.dev/install.sh | sh
pi --version
```

If `pi` is not on the `PATH` afterwards, open a new shell or add its directory to the `PATH`
yourself.

pi then needs a provider and an API key, which cannot come from this repository: the key is
personal, and `~/.pi/agent/models.json` is the file pi reads. The shape of that file is described
in [the pi documentation](https://pi.dev/docs/latest/providers). The scenario declares the provider
and the model it expects, so read `[agent]` in `scenarios/issue1-context.toml` and make sure that
provider is the one your `models.json` declares, or change those two lines.

### Install trysquare with uv

`pyproject.toml` says where trysquare comes from, and uv does the rest. If you do not have uv yet:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then, from the root of this repository:

```bash
uv sync
```

This creates `.venv`, installs trysquare and its dependencies, and writes `uv.lock`. That lock file
is what makes a measurement repeatable: the scenario pins the measured repo by a tag, but nothing
pins trysquare itself, and a harness that does not pin itself measures the operator. Version the
lock file.

trysquare is published on TestPyPI and its dependencies on PyPI. `pyproject.toml` declares the
named index as `explicit`, so uv only looks there for the packages that name it as their source;
the others come from PyPI, and TestPyPI cannot silently supply a namesake dependency.

Check that it is there:

```bash
uv run trysquare --version
```

## Running the matrix

`uv run` puts `.venv/bin` at the head of the `PATH` for the command it launches, which matters:
trysquare runs the validator as a subprocess, and `validators/issue1.py` imports `trysquare.assay`
under a `/usr/bin/env python3` shebang. Without that, it would land on the system python, which
does not know the package.

```bash
uv run trysquare run scenarios/issue1-context.toml --output results --dry-run
uv run trysquare run scenarios/issue1-context.toml --output results --repetitions 3
uv run trysquare run scenarios/issue1-context.toml --output results
```

The first one prints the full plan without spending anything. The second is a smoke pass, enough to
see the spread; the number of repetitions goes into the name of the output directory, so it cannot
be confused with the real matrix. The third runs the matrix as the scenario declares it, 20
repetitions per configuration.

`trysquare.toml` puts the throwaway clones under `$TMPDIR`, which Linux does not always define.
Export it first if your shell has no value for it, otherwise the path starts with an empty string
and the clones land at the root of the repository:

```bash
export TMPDIR="${TMPDIR:-/tmp}"
```

The subcommands that spend nothing take the same form:

```bash
uv run trysquare render results/issue1-context_…
uv run trysquare replay results/issue1-context_… --scenario scenarios/issue1-context.toml --rescore
uv run trysquare compare results/… results/…
```

## Where to change the model and the concurrency

Both live in `scenarios/issue1-context.toml`, and nowhere else.

The provider and the model are in the `[agent]` table:

```toml
[agent]
provider = "test-ilaas"
model = "gemma-4-31b_alt"
thinking = "off"
```

They are declared in the scenario, and never inherited from the shell, because they are the two
values that decide what is being measured: an environment variable would make them invisible to
whoever reads the file. If you do not have that provider, change these two lines before running.
The tables published in the course were measured on `ilaas` and `gemma-4-31b`, against commit
`d62ccd1f` of NEON.

The number of concurrent runs is in the `[protocol]` table, with the rest of the protocol:

```toml
[protocol]
repetitions = 20
concurrency = 30
timeout = 1800
attempts = 5
```

`concurrency` is how many runs trysquare launches at the same time. Lower it if your provider rate
limits you, or if the machine cannot take it. `--repetitions` on the command line overrides
`repetitions` for one run; the other three are read from the file.

`trysquare.toml` also carries a `concurrency` under `[defaults]`, but it is only a fallback used
when a scenario says nothing. This scenario says something, so the value that runs is the one
above.

## The cost

Twenty repetitions over nine configurations take two to three hours and the tokens that go with
them. Start with `--dry-run`, which spends nothing, then with `--repetitions 3`.

## Layout

```
trysquare-starter/
  pyproject.toml     where trysquare comes from, and nothing else
  trysquare.toml     machine paths: where NEON is, where the throwaway clones live
  scenarios/         the experiment, in one self contained TOML file
  hypotheses/        what is predicted, written before measuring
  materials/         prompts, AGENTS.md, system prompt, skill, probe
  validators/        what scores
  results/           one matrix per directory
```

The paths of a scenario are relative to the scenario, which makes the directory movable in one
piece.

## The experiment

Nine configurations, including a `nothing` base that declares no delta and reproduces what somebody
does on day one: the careless request, no rules file, no reasoning budget, the agent's own system
prompt. Each of the others adds or removes one piece, and `scenarios/issue1-context.toml` says in a
comment why each one is there.

The criterion is `bounce_bricks`, and it is a probe rather than a pattern in the diff:
`materials/provided-probe/probe.test.js` places a ball already overlapping a brick, calls `frame()`,
and watches which component of the speed flips. What issue #1 asks for is a behaviour, which the
probe executes, where a pattern looked for in the diff would depend on how the agent wrote its
correction.

The validator returns twelve metrics, which the scenario declares one by one. A metric that is
declared but missing from the validator does not cost the matrix: it makes the validator fail, the
run is kept, and `replay --rescore` scores it again without spending a token.

Its tests run offline and need no model:

```bash
cd validators && uv run --project .. python -m unittest test_issue1
```

## Changing the experiment

Copy `scenarios/issue1-context.toml`, change one configuration, run it again. You will have touched
neither the tool, nor the validator, nor the other configurations.

The material in `materials/` is an experimental input, though: changing one word of a prompt changes
the measurement and invalidates the tables already published. Add a piece next to it and declare it
as one more cell, rather than rewriting the one that has already served.

## Where to go next

- [trysquare](https://github.com/AI-for-dev/trysquare) and its [documentation](https://ai-for-dev.github.io/trysquare/), for writing a scenario
- [NEON](https://github.com/AI-for-dev/neon), the measured repo, and its `ISSUES.md`
- [pi](https://pi.dev), the harness being measured
