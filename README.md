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

trysquare is published on TestPyPI while its release path is what is being tried out, and its
dependencies come from PyPI. An install therefore has to reach both indexes. `pyproject.toml`
declares the named index as `explicit`, so uv only looks at TestPyPI for the package that names
it as its source; everything else comes from PyPI, and TestPyPI cannot silently supply a namesake
dependency. Outside uv, the same thing is
`pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ trysquare`.

There is no `--version` flag. What checks the install, and the wiring of the experiment with it,
is `validate`: it loads the scenario, resolves the repository, checks that every path it
references exists, and spends no token.

```bash
uv run trysquare validate scenarios/issue1-context.toml
```

It ends on `ok: nothing this scenario references is missing`, and notes it when `pi` is absent
from the `PATH`, since a run would then refuse.

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

Clones and sessions live under `$TMPDIR/trysquare`, and trysquare falls back to the system
temporary directory when the shell defines no `$TMPDIR`. Nothing to set, and nothing durable to
clean up: the archive under `results/` keeps sources, and `replay` rebuilds a tree from a tag and
a diff when one is needed.

The subcommands that spend nothing take the same form. `render` and `replay` read the scenario,
not only the output directory, because that is where the metrics and the verdict are declared:

```bash
uv run trysquare render scenarios/issue1-context.toml --output results
uv run trysquare replay results/issue1-context_… --scenario scenarios/issue1-context.toml --rescore
uv run trysquare compare results/… results/…
```

### Why there is a `trysquare.toml`

A scenario names a repository by a logical name, `repo = "neon"`, and only a config file says
what that name points at on this machine. trysquare looks for `trysquare.toml` by walking up from
the scenario, so this one covers the whole directory. Two tables are all it holds, `[repos]` and
`[harness]`; everything else it could carry, from `workdir` to `concurrency`, already has the same
value built into the tool.

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
limits you, or if the machine cannot take it. `run` takes `--repetitions`, `--concurrency` and
`--timeout` as overrides for one run, and records them, so trying a lower concurrency does not
mean editing the scenario; `attempts` is read from the file only.

A scenario that said nothing here would fall back to the tool's own values, 5 and 900 and 3. This
one says something, so the values that run are the ones above.

## The cost

Twenty repetitions over nine configurations take two to three hours and the tokens that go with
them. Start with `--dry-run`, which spends nothing, then with `--repetitions 3`.

## Layout

```
trysquare-starter/
  pyproject.toml     where trysquare comes from, and nothing else
  trysquare.toml     what the logical names `neon` and `websearch` point at, and nothing else
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
