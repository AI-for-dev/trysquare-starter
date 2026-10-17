---
name: playtester
description: Turns a gameplay bug of a brick breaker (breakout) into red tests, from the catalogue of the genre's known bugs included in this skill. Use when a player reports abnormal behaviour in a brick breaker.
---

# Brick breaker playtester

A symptom reported by a player is only the visible case. Brick breakers always break in the same places, and fixing the symptom alone lets its neighbours through. So you start from the catalogue below, keep the entries that live in the same component as the symptom, and write a **red** test for each one. You do not fix the game.

## Catalogue of known bugs

Each row is a cause found in developer discussions. The invariant is the property a correct brick breaker always respects: it is what the test checks.

### Ball-brick collision

| Bug | Cause | Invariant | Source |
| --- | --- | --- | --- |
| Bounce on the wrong axis | a single response for every face (`vy = -vy`), or axis deduced from the position of the ball's centre | a side face flips `vx`, a top or bottom face flips `vy`, the other component does not change | https://stackoverflow.com/questions/1561538 ; https://stackoverflow.com/questions/62994269 |
| Corner resolved wrongly | edge tests in `else if`: only one face is kept at the corner | when the ball penetrates as much on both axes, both components flip | https://gamedev.stackexchange.com/questions/70887 |
| Ball stuck in the brick | the speed is flipped without taking the ball out; the collision is detected again on the next step and the speed flipped back | after resolution, the ball is outside the brick, in contact with the face it hit | https://learnopengl.com/In-Practice/2D-Game/Collisions/Collision-resolution ; https://gamedev.stackexchange.com/questions/95817 |
| Double bounce at the seam of two bricks | each brick answers alone: two bricks hit in the same step flip the same component twice | two adjoining bricks form a continuous surface: a single bounce per axis and per step | https://stackoverflow.com/questions/38967446 ; https://github.com/bevyengine/bevy/pull/685 |
| Crossing at high speed (tunneling) | discrete test after the move: in one step, the ball travels more than the thickness of the brick plus its diameter | no brick is crossed without being hit, at any reachable speed and at the maximum `dt` | https://github.com/bevyengine/bevy/issues/1240 ; https://stackoverflow.com/questions/61804245 |
| Destroyed brick that stays active | the brick is not removed or its state is not tested | a destroyed brick no longer makes the ball bounce and no longer scores points | https://developer.mozilla.org/en-US/docs/Games/Tutorials/2D_breakout_game_pure_JavaScript/Collision_detection |
| Bounce and destruction handled apart | the bounce moves the ball away before the destruction tests the contact | a contact produces the bounce and the destruction in the same pass | https://forum.gdevelop.io/t/brick-breaker-breakout-collision-problem/32533 |

### Ball-paddle collision

| Bug | Cause | Invariant | Source |
| --- | --- | --- | --- |
| Ball that goes through the paddle or sticks to its edge | contact detected without repositioning the ball | after contact, the ball is above the paddle and leaves upwards | https://stackoverflow.com/questions/77262029 ; https://stackoverflow.com/questions/63037446 |
| Ball stuck horizontal | `vy` is not flipped back, or the exit angle can become flat | after a bounce on the paddle, `vy` points upwards and is not zero | https://stackoverflow.com/questions/61485421 |
| Exit angle reversed | angle formula written with the wrong sign | hit left of the centre, the ball leaves towards the left, and the other way round | https://gamedev.stackexchange.com/questions/35134 |
| Paddle tested too late | the ball-paddle test is nested inside the "the ball reached the bottom" test | contact with the paddle is tested at every step | https://stackoverflow.com/questions/41962633 |

### Walls

| Bug | Cause | Invariant | Source |
| --- | --- | --- | --- |
| Ball that vibrates against a wall | bounce triggered without testing the direction of the speed | the bounce only happens if the ball is moving towards the wall; afterwards the component points inwards | https://developer.mozilla.org/en-US/docs/Games/Tutorials/2D_breakout_game_pure_JavaScript/Bounce_off_the_walls ; https://stackoverflow.com/questions/42209048 |
| Missing bounce on one side | asymmetric comparison, radius forgotten on one side | the walls are tested against the edge of the ball (`x - r`, `x + r`, `y - r`) | https://stackoverflow.com/questions/29588091 |
| Exit through a wall on a double contact | the loop stops at the first collision of the step | every collision of a step is resolved | https://github.com/bevyengine/bevy/pull/685 |
| Lost ball not detected | bottom test missing, or faulty restart | below the bottom edge, a life is lost and the ball restarts from its initial position | https://stackoverflow.com/questions/44355463 |

### Time step

| Bug | Cause | Invariant | Source |
| --- | --- | --- | --- |
| Framerate-dependent speed | movement in pixels per frame | the movement is speed × `dt` | https://stackoverflow.com/questions/16554296 |
| Speed magnitude that changes | speed changed component by component, or a force added | a bounce changes the direction, not the magnitude of the speed | https://stackoverflow.com/questions/49639346 |

### Paddle and input

| Bug | Cause | Invariant | Source |
| --- | --- | --- | --- |
| Paddle that leaves the screen | bound computed with the height, or on the centre | the position of the paddle stays within `[0, width - paddle width]` | https://stackoverflow.com/questions/72641246 ; https://stackoverflow.com/questions/22902640 |
| Paddle that drifts on its own | no dead zone on the analogue axis | without input, the paddle does not move | https://stackoverflow.com/questions/75048963 |
| Jerky paddle on the keyboard | movement applied in the event handler, subject to key repeat | the state of the keys is read at every step of the loop | https://stackoverflow.com/questions/64692791 |

### Score and state

| Bug | Cause | Invariant | Source |
| --- | --- | --- | --- |
| Brick counted twice | the collision is reported twice for the same brick | a brick scores its points and decrements the counter only once | https://discussions.unity.com/t/is-it-possible-for-oncollisionenter-to-be-called-twice-for-the-same-collision/639691 |
| Score or lives reset at the next level | the level change resets the whole state | score and lives survive the level change, only the bricks and the combo start over | https://agonzalezla.itch.io/brickburst/devlog/720248/v-0115-fix-player-scoring-errors |
| Combo never reset | reset forgotten on transitions | the combo starts again from zero when the ball is lost and at each new level | https://sbox.game/facepunch/breakout/source?file=Game%2FBreakoutGame.cs |

If the symptom matches no section, say so and describe the missing entry (bug, cause, invariant), without attributing a source to it.

## 1. Component

Read the game's code. Find the function that produces the symptom, and note how a test can reach it through the exported functions. Note in which order the game loop calls these functions at each turn. If the logic lives in a rendering function, call it with a fake canvas context, for example `new Proxy({}, { get: () => () => {} })`. Also find the axis convention (direction of `y`), and compute from the code the limit values the game can produce: maximum speed of the ball, capped `dt`, dimensions of the ball, the bricks, the paddle and the gap between bricks. Take these limits over the whole game (last level, maximum difficulty), not only at the start. Write these numbers down, the tests will refer to them.

## 2. Selection

Take from the catalogue **all** the entries of the section of the component you found. Each test you keep must make the function found in step 1 act on the objects of the symptom. It calls another exported function only if the entry requires it (a move, for example), and only after a first pass of the symptom's function, in the order of the loop: a correction written in either function must be judged the same way. An entry about another object tests another bug: set it aside. These cases come from the catalogue and not from the tickets or the tests already in the repository: that is what makes the approach valid on a game without a detailed ticket.

Write the list before coding: for each entry, its invariant and why it applies here.

## 3. Red tests, one by one

Add the tests at the end of the existing test file, one `describe` per entry kept, and one `test` per variant (each face, each axis). The `edit` tool always requires `path`.

Write **a single test at a time**, and only move on to the next once this one is red for the right reason:

1. write the test. It starts with a **precondition**: an assertion that computes the edges of the ball and of the brick and checks that they overlap, or will overlap during the step. It bears on the state you wrote by hand, before any call to the game's code, and nothing is checked between two calls: only the final result counts, since the correction can act at any stage. A "nothing happens" bug looks like a setup without contact; only the precondition tells them apart;
2. by rereading the current code, write in a comment the value the invariant's assertion will receive today;
3. `node --check <file>`, then run this single test (`node --test --test-name-pattern "<test name>" <file>`);
4. the test must fail on the invariant's assertion, with the predicted value. A failure on the precondition, another value or another error means the setup does not test what you think: fix it before going further. A test that already passes proves nothing.

Each test checked this way serves as a model for the next one.

A red test is only worth something if it passes once the game is fixed, whatever the reasonable correction. The setup must therefore admit **a single** correct result:

- **isolated**: replace the grid of bricks with one or two bricks written by hand, far from the walls and the paddle. In the grid, the gap between rows is often smaller than the ball's diameter: it also touches the neighbours and the expected result becomes ambiguous;
- **clear penetration**: the ball enters by 2 or 3 units through the targeted face and clearly more on the other axis, so that there is no doubt about the face hit. A ball placed at the centre of a brick has no face;
- **witness axis**: a non-zero speed on the axis that must not change, so that a correction that flips everything fails;
- **reachable**: only positions, speeds and dimensions the game can produce. Quote in a comment the limit value computed in step 1 and show that the setup stays below it;
- **judged from outside**: compare the edges of the ball and of the brick by an explicit computation, and use the game's direction constants. A function of the code under test cannot judge that code.

A corner is an exception to clear penetration and to the witness axis: a ball that enters as much on both axes has no face and no witness axis, and the only correct result is that both components flip. This is not an ambiguous setup.

Before writing a case, write in a comment the starting position and the only result a fixed game would accept. If you see two, change the setup. Also comment each `describe` in one line: the invariant and the catalogue entry.

## 4. Check

Run the project's test command. Move on to the fix when each entry kept has its tests, the tests that existed before still pass, and each new test fails on an `AssertionError`. Do not change the game before that point.

## 5. Fix

Fix the game until the whole suite passes. Change the game's code, not the tests.

If a test still fails on a fix you believe correct, reread its setup against the invariant of its entry. When the setup is wrong (the ball has no face, two results are possible, the position cannot be reached), fix the setup and say so in the final table. Never weaken an assertion, delete a test or skip it to make the suite pass: a test that only passes once weakened no longer checks its invariant.

Run the project's test command once more at the end. You are done when every test passes, the old ones and the new ones.

End with a table: catalogue entry, invariant, test name, reason for the first failure, and whether its setup was changed during the fix.
