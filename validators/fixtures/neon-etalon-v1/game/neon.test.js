// neon.test.js — PARTIAL coverage (on purpose).
//
// What is covered today: the collision primitive and a couple of physics
// bounces. What is NOT covered yet: score and combo (see ISSUES.md #5), nor
// level progression. This is a starting point for the testing work ahead, not
// a complete suite.
//
// Run: `node --test "game/**/*.test.js"`  (or `npm test`)

import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  collides,
  step,
  makeBricks,
  createState,
  BRICK_ROWS,
  BRICK_COLS,
  WIDTH,
} from './neon.js';

test('collides: clear overlap detected', () => {
  const ball = { x: 100, y: 100, r: 8 };
  const brick = { x: 90, y: 90, w: 40, h: 20 };
  assert.equal(collides(ball, brick), true);
});

test('collides: ball clearly away => no collision', () => {
  const ball = { x: 300, y: 300, r: 8 };
  const brick = { x: 90, y: 90, w: 40, h: 20 };
  assert.equal(collides(ball, brick), false);
});

test('collides: edge contact (radius) detected', () => {
  const ball = { x: 85, y: 100, r: 8 }; // right edge of the ball at 93 > 90
  const brick = { x: 90, y: 90, w: 40, h: 20 };
  assert.equal(collides(ball, brick), true);
});

test('step: bounce off the left wall', () => {
  const state = createState(1);
  state.ball = { x: 2, y: 200, r: 7, vx: -300, vy: 0 };
  step(state, 1 / 60);
  assert.ok(state.ball.vx > 0, 'horizontal velocity should flip to the right');
});

test('step: ball exiting through the bottom => lost', () => {
  const state = createState(1);
  state.ball = { x: 320, y: belowField(), r: 7, vx: 0, vy: 400 };
  const lost = step(state, 1 / 60);
  assert.equal(lost, true);
});

test('makeBricks: full, all-alive grid at start', () => {
  const bricks = makeBricks(1);
  assert.equal(bricks.length, BRICK_ROWS * BRICK_COLS);
  assert.ok(bricks.every((b) => b.alive));
  assert.ok(bricks.every((b) => b.x >= 0 && b.x + b.w <= WIDTH));
});

// Small local helper: place the ball below the field without importing the
// height (coverage intentionally light).
function belowField() {
  return 500;
}

// TODO (#5): test comboMultiplier / scoreForBrick.
// TODO      : test level progression and loadBest/saveBest persistence.
