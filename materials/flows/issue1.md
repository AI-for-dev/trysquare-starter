---
name: issue1
description: The loop of the workflows module, from the impact note to the audit, on issue #1
input: string
timeout: 15m

nodes:
  # The two readings of the ticket, at the same time: neither of them writes.
  - id: survey
    parallel:
      impact:
        - id: note
          agent: explorer
          retry: 1
          reads: [input]
      cases:
        - id: cases
          agent: tester
          retry: 1
          reads: [input]

  # The return to the planner: a second round replans what the audit left open.
  - id: round
    loop: suite.output.passed && audit.output.approved
    max: 2
    ledger: round
    do:
      - id: plan
        agent: planner
        retry: 1
        reads: [input, survey.output.impact.output, survey.output.cases.output, round.ledger]
        output: { steps: [{ text: string }] }

      # One step after the other, in the same tree.
      - id: steps
        map-from: plan.output.steps
        max: 6
        do:
          # The return to the coder: up to three attempts per step.
          - id: step
            loop: tests.output.passed && review.output.approved
            max: 3
            ledger: step
            on-fail: continue
            do:
              - id: code
                agent: coder
                retry: 1
                memory: step
                reads: [input, item.text, step.previous.tests, step.previous.review, step.ledger]

              - id: tests
                check: .pi/checks/test.sh

              - id: review
                agent: reviewer
                retry: 1
                memory: step
                verdict: step
                reads: [input, item.text, code, diff, tests]

      - id: suite
        check: .pi/checks/test.sh

      - id: audit
        agent: auditor
        retry: 1
        verdict: round
        reads: [input, steps, suite, diff, round.ledger]
---

## note
Write the impact note of the ticket named under `input`.

## cases
List the test cases the ticket named under `input` needs, saying which ones
already exist. Start with the behaviours the change must not break.

## plan
Split the ticket named under `input` into small steps, with the impact note and
the test plan as a map. When `round.ledger` is not empty, this is a second
round: plan only what the audit raised and nobody closed.

The contract is the ticket's, not yours. Every case the ticket lists in
`ISSUES.md` is part of it, and each one gets a step of its own. Only
`game/neon.js` and `game/neon.test.js` may change, and every function
`game/neon.js` already exports keeps its name and its signature.

The coder only sees the text of its step: name the files, restate the part of
the ticket the step covers, and say what "done" looks like. Each step starts
with its red test, written in `game/neon.test.js`, and ends on a green suite:
the red test and the code that turns it green go in the same step, never in
two.

## code
Carry out the step described under `item.text`, and only that step.

When `step.previous.review` follows, the reviewer did not approve your last
change: address each remark and each obligation of `step.ledger`, or say
clearly why you do not. `step.previous.tests` gives the output of the suite
after that change.

## review
Review the change made for the step described under `item.text`. The coder's
report is under `code`, the change under `diff`, the output of the suite under
`tests`. The report is a claim, the diff and the code are the evidence.
Approve, or raise what still has to change.

## audit
Review the whole change under `diff` against the ticket named under `input`.
`steps` says how the review of each step ended: a step that did not converge is
not done until the code shows it. `suite` says whether the project's tests
pass. `round.ledger` carries what a previous audit raised and nobody closed.

Approve the whole, or raise each correction on its own line.
