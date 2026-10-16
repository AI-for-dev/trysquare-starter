---
name: dynamic-playtester
description: Turns a gameplay bug of an arcade game into red tests, from a catalogue of the genre's known bugs built by web search. Use when a player reports abnormal behaviour in the game.
---

# Dynamic playtester

A symptom reported by a player is only the visible case. Arcade games always break in the same places, and fixing the symptom alone lets its neighbours through. So you start from the known bugs of the genre, keep those that live in the same component as the symptom, and write a **red** test for each one. You do not fix the game.

## 1. Catalogue

The catalogue of known bugs is `references/bugs-arcade.md`, in this skill's directory, with one `##` section per game genre.

Identify the genre of the game (README, code), in English (`shoot 'em up`, `platformer`, `maze game`...). If the catalogue has no section for this genre, or if the user asks for it to be redone, run `bash scripts/catalogue.sh "<genre>"` from the skill's directory. The script does the web search in a separate session that knows nothing of the bug, so that the catalogue covers the whole genre and not only the symptom. It can take several minutes: wait until it has finished.

The script keeps only the entries backed by a page the search actually opened. If it fails, or ends without a catalogue, stop there and say so: do not write a catalogue yourself, and do not write tests. A catalogue written from memory holds what you already believe, not the genre's known bugs.

Then read the genre's section in full.

## 2. Component

Read the game's code. Find the function that produces the symptom, and note how a test can reach it through the exported functions. Note in which order the game loop calls these functions at each turn. If the logic lives in a rendering function, call it with a fake canvas context, for example `new Proxy({}, { get: () => () => {} })`. Also find the axis convention, and compute from the code the limit values the game can produce: maximum speed, capped `dt`, dimensions. Take these limits over the whole game (last level, maximum difficulty), not only at the start. Write these numbers down, the tests will refer to them.

## 3. Selection

Take from the catalogue **all** the entries of the component you found. Each test you keep must make the function found in step 2 act on the objects of the symptom. It calls another exported function only if the entry requires it (a move, for example), and only after a first pass of the symptom's function, in the order of the loop: a correction written in either function must be judged the same way. An entry about another object tests another bug: set it aside. Set aside the entries whose invariant is `none`: the catalogue found the cause but no property a test can check. Also set aside the entries that describe a gameplay improvement rather than a defect: the invariant must be a property the player already expects from the game. These cases come from the catalogue and not from the tickets or the tests already in the repository: that is what makes the approach valid on a game without a detailed ticket.

Write the list before coding: for each entry, its invariant and why it applies here.

## 4. Red tests, one by one

Add the tests at the end of the existing test file, one `describe` per entry kept, and one `test` per variant (each side, each axis). The `edit` tool always requires `path`.

Write **a single test at a time**, and only move on to the next once this one is red for the right reason:

1. write the test. It starts with a **precondition**: an assertion that computes the edges of the objects and checks that they overlap, or will overlap during the step. It bears on the state you wrote by hand, before any call to the game's code, and nothing is checked between two calls: only the final result counts, since the correction can act at any stage. A "nothing happens" bug looks like a setup without contact; only the precondition tells them apart;
2. by rereading the current code, write in a comment the value the invariant's assertion will receive today;
3. `node --check <file>`, then run this single test (`node --test --test-name-pattern "<test name>" <file>`);
4. the test must fail on the invariant's assertion, with the predicted value. A failure on the precondition, another value or another error means the setup does not test what you think: fix it before going further. A test that already passes proves nothing.

Each test checked this way serves as a model for the next one.

A red test is only worth something if it passes once the game is fixed, whatever the reasonable correction. The setup must therefore admit **a single** correct result:

- **isolated**: replace the collections of objects of the state with one or two objects written by hand, far from the edges. In the game's scene, the object under test also touches neighbours and the expected result becomes ambiguous;
- **clear penetration**: the moving object enters by 2 or 3 units through the targeted side and clearly more on the other axis, so that there is no doubt about the side hit. An object placed at the centre of another has no side;
- **witness axis**: a non-zero speed on the axis that must not change, so that a correction that flips everything fails;
- **reachable**: only positions and speeds the game can produce. Quote in a comment the limit value computed in step 2 and show that the setup stays below it;
- **judged from outside**: compare the edges of the two objects by an explicit computation, and use the game's direction constants. A function of the code under test cannot judge that code.

A symmetric case is an exception to clear penetration and to the witness axis: an object that enters as much on both axes has no side and no witness axis, and the only correct result is symmetric too (both axes react). This is not an ambiguous setup.

Before writing a case, write in a comment the starting position and the only result a fixed game would accept. If you see two, change the setup. Also comment each `describe` in one line: the invariant and the catalogue entry.

## 5. Check

Run the project's test command. You are done when each entry kept has its tests, the tests that existed before still pass, and each new test fails on an `AssertionError`.

End with a table: catalogue entry, invariant, test name, reason for the failure.
