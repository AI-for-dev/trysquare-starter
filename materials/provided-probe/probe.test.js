// probe.test.js - the edge cases of issue #1, as executable tests, **handed over in advance**.
//
// This file does not exist at the etalon. A `kind = "files"` brick of the scenario drops it in
// the measured tree before the agent starts, and commits it on the etalon: the cell that
// receives it therefore begins its work with a red suite and the specification in front of it.
// That is all this cell measures - does a model that already has the tests it needs correct
// itself?
//
// ---------------------------------------------------------------------------
// WHAT IT TAKES FOR THIS FILE TO EVEN RUN
//
// It imports `frame` from `./neon.js`, which the module **does not export** today. Until it
// does, `npm test` fails while loading the module and no case runs. Exporting the render loop
// is therefore the first thing to do, and it is one line.
// ---------------------------------------------------------------------------
//
// Fifteen cases, in six groups. The first four are issue #1, from the coarsest to the finest,
// and each one blackens a form of incomplete correction that the previous one let through:
//
//   `brick`     the four faces: the axis that was hit flips, the other one does not move.
//   `corner`    the corner: both components flip. A per-face correction fails here.
//   `exit`      the ball has come back out of the rectangle. This is the second half of what
//               the comment in `neon.js` describes itself: "plus pushing the ball back out of
//               the brick". A correction that flips without repositioning leaves the bounce
//               sticky - on the next turn the ball still overlaps and flips back.
//   `neighbors` two bricks hit in the same pass: the bounce applies once and not twice. A
//               `vy = -vy` applied twice cancels out and the ball goes through. The grid gap is
//               8 px and the ball diameter 14, so every seam of the grid is a double overlap:
//               it is the common case, not the curiosity.
//
// The last two are **other bugs that issue #1 does not mention**, found while writing the cases
// above. They are here because they live in the same collision detection and because a file of
// edge cases that kept quiet about them would be lying, not because the ticket asks for them:
//
//   `tunneling` the fast ball jumps over the brick without ever touching it. Detection is
//               discrete: it samples the position before and after the move, and at level 6
//               speed one frame of movement exceeds the height of a brick. Only continuous
//               detection - a sweep between the two positions - makes this case pass.
//
// These are ordinary `node:test` tests, like `game/neon.test.js`, run by the `npm test` command.
// Nothing here is a harness convention.

import { test, describe } from 'node:test';
import assert from 'node:assert/strict';

// One import, and not a `typeof` on each name: if one of them is missing, the module does not
// link, no case runs, and the failure says *which* name was missing. That is the right message.
import {
  frame,
  step,
  createState,
  ballSpeed,
  WIDTH,
  HEIGHT,
  BALL_R,
  BRICK_W,
  BRICK_H,
  BRICK_GAP,
} from './neon.js';

// The time step of a nominal frame, and the ceiling `boot()` applies to a frame that stuttered.
// The first four groups have no use for them - their ball already overlaps - but `tunneling`
// judges detection *during* the move, and that is exactly what these two values produce in the
// game.
const DT = 1 / 60;
const DT_MAX = 0.05;

// Every case of the first four groups places a ball **already overlapping** the brick, by 3 px
// on the targeted face and by 17 px or more on the other axis. Nothing advances by a time step
// to *reach* the brick, so nothing depends on a `dt`. The off-axis speed is small but non zero,
// so that a correction flipping both axes at random fails instead of passing.

describe('brick', () => {
  test('left side: the ball leaves towards the left', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 96, y: 110, r: BALL_R, vx: 300, vy: 30 };

    play(t, state);

    assert.ok(state.ball.vx < 0, `vx should have become negative: ${state.ball.vx}`);
    assert.ok(state.ball.vy > 0, `vy should have stayed positive: ${state.ball.vy}`);
  });

  test('right side: the ball leaves towards the right', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 176, y: 110, r: BALL_R, vx: -300, vy: 30 };

    play(t, state);

    assert.ok(state.ball.vx > 0, `vx should have become positive: ${state.ball.vx}`);
    assert.ok(state.ball.vy > 0, `vy should have stayed positive: ${state.ball.vy}`);
  });

  test('top face: the ball leaves upwards', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 136, y: 96, r: BALL_R, vx: 30, vy: 300 };

    play(t, state);

    assert.ok(state.ball.vy < 0, `vy should have become negative: ${state.ball.vy}`);
    assert.ok(state.ball.vx > 0, `vx should have stayed positive: ${state.ball.vx}`);
  });

  test('bottom face: the ball leaves downwards', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 136, y: 124, r: BALL_R, vx: 30, vy: -300 };

    play(t, state);

    assert.ok(state.ball.vy > 0, `vy should have become positive: ${state.ball.vy}`);
    assert.ok(state.ball.vx > 0, `vx should have stayed positive: ${state.ball.vx}`);
  });
});

// On the corner, the ball arrives diagonally and penetrates as much on both axes: both
// components must flip. A correction that compares the two penetrations and flips only one of
// them passes the four faces and fails here.

describe('corner', () => {
  test('top left corner: the ball leaves diagonally', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 96, y: 96, r: BALL_R, vx: 300, vy: 300 };

    play(t, state);

    assert.ok(state.ball.vx < 0, `vx should have become negative: ${state.ball.vx}`);
    assert.ok(state.ball.vy < 0, `vy should have become negative: ${state.ball.vy}`);
  });
});

// The geometric mirror of `brick`: same four fixtures, but the speed is no longer what we watch,
// the **position** is.
//
// The assertion is arithmetic and **not** `!collides(ball, brick)`: `collides` is part of the
// code under test, and judging with its own definition would make the case easier for a
// correction that had loosened it. The tolerance covers a penetration computed in floats that
// lands one ulp off the edge.
const EPS = 1e-9;

describe('exit', () => {
  test('left side: the ball comes back out on the left', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 96, y: 110, r: BALL_R, vx: 300, vy: 30 };

    play(t, state);

    const edge = state.ball.x + BALL_R;
    assert.ok(edge <= 100 + EPS, `the right edge of the ball should be back at x <= 100: ${edge}`);
  });

  test('right side: the ball comes back out on the right', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 176, y: 110, r: BALL_R, vx: -300, vy: 30 };

    play(t, state);

    const edge = state.ball.x - BALL_R;
    assert.ok(edge >= 172 - EPS, `the left edge of the ball should be back at x >= 172: ${edge}`);
  });

  test('top face: the ball comes back out above', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 136, y: 96, r: BALL_R, vx: 30, vy: 300 };

    play(t, state);

    const edge = state.ball.y + BALL_R;
    assert.ok(edge <= 100 + EPS, `the bottom edge of the ball should be back at y <= 100: ${edge}`);
  });

  test('bottom face: the ball comes back out below', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 136, y: 124, r: BALL_R, vx: 30, vy: -300 };

    play(t, state);

    const edge = state.ball.y - BALL_R;
    assert.ok(edge >= 120 - EPS, `the top edge of the ball should be back at y >= 120: ${edge}`);
  });
});

// Two bricks hit in the **same pass** of the loop, which walks every living brick. The bounce
// must apply once. Three forms of correction separate here: `vy = -vy` cancels out on the second
// turn and the ball goes through; `vy = Math.abs(vy)` is idempotent and passes; a correction that
// repositions takes the ball out of the overlap before reaching the second brick and passes too.
//
// Each fixture is tuned so that the targeted face is unambiguously the **smallest penetration**,
// 1 px against 3 on the axis of the seam, so that a minimum-penetration resolver has no choice to
// make and failure can only come from double counting.
//
// The speeds are ten times lower than elsewhere, and that is deliberate: a correction placed in
// `step()`, which integrates before it resolves, moves the ball before judging it. At 60 px/s the
// move is 1 px and the order of the penetrations holds wherever the correction lives.

describe('neighbors', () => {
  test('horizontal seam: a single bounce on two bricks side by side', (t) => {
    const state = createState(1);
    state.bricks = [
      { x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 },
      { x: 100 + BRICK_W + BRICK_GAP, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 },
    ];
    // Centred on the gap (169..183 overlaps 3 px of each brick), and 1 px below their bottom
    // face: the vertical axis wins for both.
    state.ball = { x: 176, y: 126, r: BALL_R, vx: 6, vy: -60 };

    play(t, state);

    assert.ok(state.ball.vy > 0, `vy should have flipped exactly once: ${state.ball.vy}`);
    assert.ok(state.ball.vx > 0, `vx should have stayed positive: ${state.ball.vx}`);
  });

  test('vertical seam: a single bounce on two stacked bricks', (t) => {
    const state = createState(1);
    state.bricks = [
      { x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 },
      { x: 100, y: 100 + BRICK_H + BRICK_GAP, w: BRICK_W, h: BRICK_H, row: 1, alive: true, points: 10 },
    ];
    // Centred on the gap between the rows (117..131 overlaps 3 px of each brick), and 1 px into
    // their left side: the horizontal axis wins for both.
    state.ball = { x: 94, y: 124, r: BALL_R, vx: 60, vy: 6 };

    play(t, state);

    assert.ok(state.ball.vx < 0, `vx should have flipped exactly once: ${state.ball.vx}`);
    assert.ok(state.ball.vy > 0, `vy should have stayed positive: ${state.ball.vy}`);
  });
});

// Tunneling, with the values the game produces itself and no others. `ballSpeed(6)` is 710 px/s,
// and `DT_MAX` is the ceiling `boot()` applies to a frame that stuttered: 35.5 px of movement in
// one turn of the loop, against 34 px to cross (`BRICK_H` plus the diameter of the ball).
// Detection samples before and after the jump, without ever seeing the overlap in the middle.
//
// This is the only case that needs all three steps of `play()`: the ball starts outside the
// brick, so nothing deflects before the move, and it is the `frame()` that follows which judges,
// the order `boot()` uses. The `dt` passed as a second argument is what makes the jump.
//
// No horizontal case: crossing `BRICK_W` would take more than 1720 px/s, a level the game never
// reaches. A case no game can reach judges nothing.

describe('tunneling', () => {
  test('fast ball: the brick is not crossed without being touched', (t) => {
    const state = createState(6);
    const brick = { x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 };
    state.bricks = [brick];
    // Before the move the ball occupies y 121..135, below the brick; after it, 85.5..99.5,
    // entirely above. `vx` is zero: horizontal drift would only blur the fixture, and this case
    // judges nothing but the vertical crossing.
    state.ball = { x: 136, y: 128, r: BALL_R, vx: 0, vy: -ballSpeed(6) };

    play(t, state, DT_MAX);

    assert.ok(!brick.alive, 'the brick survived a ball that went right through it');
    assert.ok(state.ball.vy > 0, `the ball should have been sent back downwards: ${state.ball.vy}`);
  });
});

// The only path by which these tests touch the game: the fifteen cases go through here and none
// of them calls `frame()` or `step()` itself. Three steps, in this order, and the first one that
// deflects the ball stops the manoeuvre.
//
// **`frame()` first, and `step()` only if `frame()` changed nothing.** Brick collision lives in
// `frame()` today, but extracting it into `step()` is a perfectly valid correction: judging on
// `frame()` alone would score that move as wrong. This fallback does not give a second chance to
// a wrong answer - a deflection on the wrong axis stays a deflection on the wrong axis - it looks
// elsewhere when nobody answered.
//
// **Then `frame()` a second time, if the move deflected nothing either.** This is the order in
// which `boot()` writes its loop: `step()` moves, `frame()` looks at what the move produced.
// `tunneling` depends on it, its ball starting outside the brick, and it also judges a correction
// that only triggers after a move instead of declaring it wrong. The first eleven cases, whose
// ball already overlaps the brick, deflected on the first step or will not deflect at all: this
// third turn changes nothing for them.
//
// Stopping at the first deflection is what keeps a correction present in both places from
// counting twice. `moved()` only looks at the speed: a brick switched off or a ball repositioned
// does not count as a deflection, and the cases that judge them read `state` themselves after the
// call returns.
function play(t, state, dt = DT) {
  const { vx, vy } = state.ball;
  const moved = () => state.ball.vx !== vx || state.ball.vy !== vy;

  frame(fakeContext(), state);
  if (moved()) return;

  step(state, dt);
  if (moved()) {
    t.diagnostic('deflected by step() and not by frame()');
    return;
  }

  frame(fakeContext(), state);
  if (moved()) t.diagnostic('deflected by frame() after the move made by step()');
}

// A canvas context that swallows everything. `frame()` only makes drawing calls, so nothing needs
// to answer correctly: an empty function for everything is enough.
function fakeContext() {
  const nothing = () => {};
  return new Proxy(
    {},
    {
      get: (_, name) => (name === 'canvas' ? { width: WIDTH, height: HEIGHT } : nothing),
      set: () => true,
    },
  );
}
