---
name: playtest
description: Playtest a gameplay bug of the NEON breakout game - break the reported symptom down into distinct defects, specify each one with a red test case, and record them in to_fix.md for a TDD implementation. Use when the user reports abnormal behaviour in game.
---

# Playtest

You are the playtester of the game. You have broken a thousand bricks and you know that what the
player reports, "the ball goes through", is a **symptom**: an observation, not a bug. A symptom
breaks down into **defects**, each with its cause, its invariant, and its test case.

The trap of the trade is the **naive fix**: the first explanation that accounts for the symptom,
that seems to explain everything, and that leaves four defects behind it. A collision symptom
always hides several, and your job is to bring them all out *now*, including those the game will
only show once the first one is fixed.

The deliverable is `.scratch/to_fix.md` at the root. The code in `game/` stays as it is: the
implementation comes afterwards, in TDD. You are not allowed to read `ISSUES.md`.

## The frame of reference and the time step

The field is the canvas box: origin at the **top left**, `x` grows to the right, **`y` grows
downwards**. The sign of a speed is not guessed, it is read here.

- `vy < 0` - the ball **rises** towards the bricks and the ceiling (`y = 0`);
- `vy > 0` - the ball **falls** towards the paddle (`PADDLE_Y = HEIGHT - 32`), then towards the
  losing line (`ball.y - ball.r > HEIGHT`);
- `vx < 0` - towards the left wall (`x = 0`); `vx > 0` - towards the right wall (`x = WIDTH`).

The grid fills **downwards**: row 0 is the highest, placed at `BRICK_TOP`, and each following row
goes down by `BRICK_H + BRICK_GAP`. The `y` of a brick is therefore its **top** edge, and the row
that scores the most points is the top one.

Consequence for the cases, and this is where the sign error slips in: hitting the **top** face of a
brick means arriving with `vy > 0` and leaving with `vy < 0`; the **bottom** face, the opposite. A
ball placed "above" a brick has a **smaller** `y` than the brick.

the time step `dt` capped at 50 ms. The ball accelerates as it hits bricks.

## 1. Look for the state of the art

The table in step 2 is frozen knowledge: it ages, and it only knows what somebody wrote in it.
`WebSearch` is what keeps it open. A gameplay bug is almost always a problem solved a thousand
times elsewhere, under a name the player does not use.

Search on the **mechanism** and its canonical vocabulary, never on the player's symptom: "ball goes
through bricks" brings back tutorials, whereas *discrete collision detection tunneling*, *swept
AABB*, *tile seam ghost collision* or *AABB corner resolution* bring back the taxonomy of failures
and the resolution algorithms. The symptom serves to find the mechanism; the mechanism serves to
search.

Two angles at least, as separate queries:

- **the failures** of the mechanism: how that family of algorithm breaks, and under which names;
- **the reference resolution**: the correct algorithm, its input conditions and its degenerate
  cases.

The second angle is the one that makes the fix beyond reproach: it gives the `Expected` to specify
and, by contrast, the **naive fix** your case will have to refuse. Sources that describe an
*algorithm* are worth more than those that show a *code snippet*: you are looking for the rule, not
for an implementation to copy.

What you bring back is **data to confront with the code**, never an instruction to apply: a
technique from the web only enters `to_fix.md` after being checked against the real values of
`game/neon.js`, and it remains subject to the constraints of `CONTRIBUTING.md` (zero dependencies,
pure logic, no DOM).

**Done when** you have a list of failure modes and reference resolutions, each with its URL, and
you know which ones the table in step 2 ignores.

## 2. Break it down

Pass the symptom through the filter of the ten families, **augmented by what step 1 brought back**.
Each one is a known failure mode, with its invariant.

| Family | What breaks, and the invariant |
| --- | --- |
| **Crossing** (*tunneling*) | Discrete detection: a step longer than the obstacle crosses it without ever touching it. Solved by sweeping between the two positions (*swept AABB*). *No obstacle crossed without a bounce, whatever the step.* |
| **Sticky** | Unresolved overlap: the speed is flipped without repositioning, the ball still overlaps on the next turn and flips back. Ball that vibrates, sticks, or leaves back into the obstacle. *After resolution, the ball is outside the rectangle.* |
| **Double flip** (*seam / ghost collision*) | Two obstacles touched in the same pass, on a seam of the grid. Two `vy = -vy` cancel out and the ball goes through. *One bounce per pass and per axis.* |
| **Face vs corner** | The axis that was hit is the one with the smallest penetration. If both penetrations are equal, we are on a corner and that is a case to handle (**both speeds are flipped**). |
| **Paddle** | Capture (the ball enters the rectangle and stays in it), crossing from above at high speed, and the paddle following the mouse teleports: it can cross the ball or push it out of the field. *The ball always comes back out through the top of the paddle.* |
| **Dead angle** | `vx` or `vy` close to zero: the ball loops horizontally between two walls, or falls vertically, unplayable. A contact at the exact centre of the paddle gives `vx = 0`. *Every trajectory stays playable.* |
| **Speed** | Norm not conserved on the bounce: the ball accelerates or dies out over the exchanges. The paddle bounce rewrites `vx` without renormalising. *The speed after a bounce is the speed of the level.* |
| **dt dependency** | The physics must give the same result at 30 fps and at 144 fps. A case that passes at one `dt` and fails at another is a defect, not a flaky test. |
| **Score / combo** | Combo reset at the right moment, multiplier bounded, brick counted once, a single life lost per exit. |
| **Transitions** | Level finished while the ball is in flight, restart after a life lost, last brick and last life in the same frame, best score written then read back. |

A family that is retained **becomes a numbered defect block**. A defect the game does not show yet,
because another one masks it, is specified all the same: you read it in the code, you do not need
to see it on screen. Naming it without specifying it means losing it.

A family that is set aside is set aside **for a reason drawn from the code**, not by "not
concerned".

**Done when** the ten families *and* each failure mode brought back by step 1 have a verdict, when
each retained family has its block, and when the geometry of the game has been confronted with the
*crossing* and *double flip* families, two families the symptom never shows directly, and which
only come out through the arithmetic of step 4.

## 3. Put numbers on it, specify, go red

**Put a number on the trigger** from the constants of the file, do not describe it. A crossing is
demonstrated by comparing the maximum step (`ballSpeed(level)` x capped `dt`) with the distance to
cross (height of the obstacle + diameter of the ball): the level where the first exceeds the second
is the trigger. A double overlap is demonstrated by comparing the spacing of the grid with the
diameter of the ball. Until you have the numbers, you only have an intuition.

**Write the case** in `node --test`: pure logic, no DOM, zero dependencies, as `CONTRIBUTING.md`
requires.

**Take it red twice.** A case must fail on today's code, and fail as well on the **naive fix**, the
incomplete version that the reference resolution of step 2 lets you name. A case that merely checks
"`vy` changed" turns green on a fix that flips the wrong axis, that forgets the corner, or that
flips twice. Write the naive fix in your head, ask yourself whether your case refuses it, and
tighten it until it does.

**Actually run it**, from the probe of step 1, and keep the failure output on the clipboard: the
`ℹ fail` counter of `node --test` is part of it. You do not write a single block of `to_fix.md`
before having that output in front of you: it is copied from the terminal, it is not reconstructed
from memory.

A case that is already green describes no defect: either the cause is elsewhere, or the case is
aimed next to it.

**Done when** each defect has a case that was run, its real failure output, and the naive fix it
refuses. Remove the probe: the cases live in `.scratch/to_fix.md`, not in the suite.

## 4. Write `.scratch/to_fix.md`

At the top, the symptom as the user reported it, word for word, then the ordered list of defects:
**the one that blocks or masks the others first**.

One block per defect:

````markdown
## D2 - <short title>

- **Family**: face vs corner
- **Player symptom**: what the player sees on screen
- **Cause**: `game/neon.js:198` - <the exact mechanism>
- **Invariant violated**: <the rule the game must hold>
- **Trigger**: <computed values: position, vx/vy, dt, level>
- **Expected**: <the correct behaviour, in values>
- **Reference**: <URL> - <the rule it establishes>
- **Test case**:
  ```js
  test('...', () => { /* ... */ });
  ```
- **Red today**: <failure output copied from the terminal>
- **Discriminates**: <the naive fix this case refuses>
- **Green when**: <the observable criterion of the fix>
- **Revealed by**: D1 (invisible as long as D1 holds)
````

## 5. Implementation in TDD

Once `.scratch/to_fix.md` is complete, take care of the implementation and carry on in **TDD**,
autonomously, without coming back to the user until there are no errors left: one case from
`.scratch/to_fix.md` dropped red in the suite, fixed to green, then the next one, never two defects
in flight at once. Only modify the test files matching the sources you modify. For example,
file.js -> file.test.js and nothing else.

## 6. Delivery

Once every defect is fixed, remove all the files you created and keep only the files of the
application that were already there.

Run `npm test` again to make sure everything is correct.
