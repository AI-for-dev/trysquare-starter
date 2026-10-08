# Hypothesis: the workflow of module 2.2 against a single agent

Declared before measuring, and versioned. A hypothesis written afterwards is a conclusion in
disguise, and the point of writing it is to make a disappointing result publishable rather than
quietly reworded.

**State: written before the first matrix. No run of the `flow` cell has been read yet.**

## What is compared

Two cells, one lever. Both receive the well crafted request of `issue1-context`, word for word.
`single` hands it to one agent. `flow` hands it to `/run issue1`, the loop of the workflows module
adapted to issue #1 (`materials/flows/issue1.md`): the explorer and the tester read the ticket at
the same time, the planner splits it into steps, each step goes to the coder until
`.pi/checks/test.sh` passes and the reviewer approves (three attempts at most), and the auditor
sends the work back for a second round when something is still open (two rounds at most).

Every role runs on the model of `[agent]`. The comparison is between one agent and a loop of
agents on the same model, not between a cheap model and an expensive one.

The flow's planner section does not restate the per-face mechanism. It says that every case
issue #1 lists in `ISSUES.md` is part of the contract and gets a step of its own, which red test
first, and it repeats the scope and the frozen API that the request already gives. That is the
restraint of the well crafted prompt: what is measured is whether the loop gets the cases done,
not whether the planner was handed the answer.

## What is predicted

The criterion is `bounce_bricks`, the faces of a brick, read against `single`.

1. **`flow` scores higher on `bounce_bricks`.** The flow forces what a single agent may skip:
   reading the ticket before writing, one case at a time, a red test before the code, and a
   suite that has to pass before a step is done. The faces are the first case of the ticket, so
   they are where the planner's first step lands.
2. **The gap is wider on the finer columns**, `bounce_corners`, `bounce_exit` and
   `bounce_neighbors`. A single agent tends to stop at the first visible fix, and these are the
   cases the ticket lists after it. A planner that gives each case its own step reaches them by
   construction, if the steps converge.
3. **`tests_added` is higher in `flow`**, since every step starts with a red test.
4. **`flow` costs several times more**, in tokens and in time: six roles, a review per step, an
   audit per round. The verdict has to be read next to the cost columns, and a gain that only
   shows at that price is a finding, not a failure.

## What would refute it

- The gap on `bounce_bricks` is zero or negative, or its interval includes zero. The loop then
  does not get the criterion done more often than one agent does.
- `tests_added` rises while the probe columns do not. The flow then produces tests that pass
  against a behaviour the ticket does not ask for, and the reviewer and the auditor did not see
  it: the check gates on the suite, and the suite is written by the agents being gated.
- `delivered` or `in_scope` drop in `flow`. A loop that ends without a change, or that touches
  files outside `game/neon.js` and `game/neon.test.js`, is a harness defect before it is a
  result.

## What is not asserted

- Which role carries the effect. The flow is measured as a whole; removing one node at a time
  is a later matrix.
- That the course flow is the best flow for this ticket. The module says so itself: its choices
  are debatable, and this matrix measures them as written.
- Anything about a mixed-model harness, a planner on a larger model for instance.

## What to read before the verdict

- **Runs cut by the timeout.** A run killed at `[protocol] timeout` ends before combo writes
  `usage.json`, and trysquare refuses to read it as a run that cost nothing. Count them before
  reading any rate: a cell that loses its longest runs is a cell measured on its easy ones.
- **`not converged` answers.** The answer of each `flow` run ends with `ok · runs/...`, followed
  by `converged` or `not converged` since the flow ends on a loop, or with `failed at ...`. A high
  rate of loops that exhaust their attempts says the condition was not reachable, which the
  module names as the first thing to check.
- **The thinking level.** combo's subagents think at the machine's `defaultThinkingLevel`, not at
  `[agent] thinking`. trysquare refuses a run where the two differ, so a matrix that ran at all
  ran at the declared level.

## Smoke pass

Before the matrix, one `flow` run with `trysquare pi` and the same prompt, to see the flow load
and reach its first check. A `/run` that combo refuses is silent in print mode: trysquare records
it `empty`, with a detail saying no combo run directory was created.
