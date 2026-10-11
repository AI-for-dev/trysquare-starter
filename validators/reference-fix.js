
// --- reference-fix.js -------------------------------------------------------
//
// Appended to the etalon's `game/neon.js` by `validators/issue1.py`, never shown to the agent.
// It is the correction issue #1 asks for, written once, so that the agent's **tests** can be run
// against it: a test that fails here is wrong, and a test that passes here but fails on one of the
// incomplete variants below catches that defect.
//
// `__VARIANT` is replaced by the validator. `complete` is the whole correction; every other value
// removes exactly one part of it:
//
//   axis       every brick hit flips `vy`, whatever the face
//   corner     a hit with equal penetration on both axes flips `vy` only
//   exit       the speed flips but the ball stays inside the brick
//   neighbors  bricks hit in the same pass each flip the speed, so a seam flips it twice
//   tunneling  no swept detection: a fast ball jumps over a brick
//
// The correction lives in `frame()`, where the comment of the etalon puts it. `step()` only
// records where the ball was before it moved, so that `frame()` can sweep that segment. The record
// is a WeakMap rather than a property of the ball, so that a test comparing the ball with
// `deepEqual` sees nothing.

const __VARIANT = '__VARIANT__';
const __EPS = 1e-6;
const __previous = new WeakMap();

function __record(ball) {
  __previous.set(ball, { x: ball.x, y: ball.y });
}

function __resolveBricks(state) {
  const ball = state.ball;
  const from = __previous.get(ball);
  __previous.delete(ball);

  const hits = state.bricks.filter((brick) => brick.alive && collides(ball, brick));
  if (hits.length) {
    __resolveOverlaps(state, hits);
  } else if (from && __VARIANT !== 'tunneling') {
    __sweep(state, from);
  }
}

function __hit(state, brick) {
  brick.alive = false;
  state.combo += 1;
  state.score += scoreForBrick(brick, state.combo);
}

// Which face the ball came through: the axis of the smallest penetration, both on a tie. `sx` and
// `sy` are the side the ball must leave towards.
function __face(ball, brick) {
  const left = ball.x + ball.r - brick.x;
  const right = brick.x + brick.w - (ball.x - ball.r);
  const top = ball.y + ball.r - brick.y;
  const bottom = brick.y + brick.h - (ball.y - ball.r);
  const px = Math.min(left, right);
  const py = Math.min(top, bottom);
  const sx = left < right ? -1 : 1;
  const sy = top < bottom ? -1 : 1;
  if (__VARIANT === 'axis') return { x: false, y: true, sx, sy };
  if (Math.abs(px - py) <= __EPS) return { x: __VARIANT !== 'corner', y: true, sx, sy };
  return px < py ? { x: true, y: false, sx, sy } : { x: false, y: true, sx, sy };
}

function __pushOut(ball, brick, face) {
  if (__VARIANT === 'exit') return;
  if (face.x) ball.x = face.sx < 0 ? brick.x - ball.r : brick.x + brick.w + ball.r;
  if (face.y) ball.y = face.sy < 0 ? brick.y - ball.r : brick.y + brick.h + ball.r;
}

function __resolveOverlaps(state, hits) {
  const ball = state.ball;

  if (__VARIANT === 'neighbors') {
    // Every brick detected first, then each one answers alone, by negation.
    for (const brick of hits) {
      const face = __face(ball, brick);
      if (face.x) ball.vx = -ball.vx;
      if (face.y) ball.vy = -ball.vy;
      __pushOut(ball, brick, face);
      __hit(state, brick);
    }
    return;
  }

  if (__VARIANT === 'axis') {
    const face = __face(ball, hits[0]);
    ball.vy = -ball.vy;
    __pushOut(ball, hits[0], face);
    for (const brick of hits) __hit(state, brick);
    return;
  }

  // One bounce per axis and per pass, whatever the number of bricks behind it.
  let alongX = null;
  let alongY = null;
  for (const brick of hits) {
    const face = __face(ball, brick);
    if (face.x && !alongX) alongX = { brick, face };
    if (face.y && !alongY) alongY = { brick, face };
    __hit(state, brick);
  }
  if (alongX) {
    ball.vx = alongX.face.sx * Math.abs(ball.vx);
    __pushOut(ball, alongX.brick, { x: true, y: false, sx: alongX.face.sx });
  }
  if (alongY) {
    ball.vy = alongY.face.sy * Math.abs(ball.vy);
    __pushOut(ball, alongY.brick, { x: false, y: true, sy: alongY.face.sy });
  }
}

// The segment the ball travelled since `step()` recorded it, against every brick grown by the
// radius of the ball: the first brick it enters is the one hit, at the point of contact.
function __sweep(state, from) {
  const ball = state.ball;
  const dx = ball.x - from.x;
  const dy = ball.y - from.y;
  let first = null;

  for (const brick of state.bricks) {
    if (!brick.alive) continue;
    let enter = 0;
    let leave = 1;
    let axis = null;
    let sign = 0;
    const slabs = [
      ['x', from.x, dx, brick.x - ball.r, brick.x + brick.w + ball.r],
      ['y', from.y, dy, brick.y - ball.r, brick.y + brick.h + ball.r],
    ];
    let missed = false;
    for (const [name, start, delta, low, high] of slabs) {
      if (delta === 0) {
        if (start <= low || start >= high) missed = true;
        continue;
      }
      const a = (low - start) / delta;
      const b = (high - start) / delta;
      const near = Math.min(a, b);
      if (near > enter) {
        enter = near;
        axis = name;
        sign = delta > 0 ? -1 : 1;
      }
      leave = Math.min(leave, Math.max(a, b));
    }
    if (missed || !axis || enter > leave || enter >= 1) continue;
    if (!first || enter < first.enter) first = { brick, enter, axis, sign };
  }

  if (!first) return;
  ball.x = from.x + dx * first.enter;
  ball.y = from.y + dy * first.enter;
  if (first.axis === 'x') ball.vx = first.sign * Math.abs(ball.vx);
  else ball.vy = first.sign * Math.abs(ball.vy);
  __hit(state, first.brick);
}
