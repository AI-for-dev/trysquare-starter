# Classic bugs of the arcade genre — bug-cause catalogue

## brick breaker

### movement collision

#### Corner / seam double bounce between two adjacent bricks
- Symptom: the ball hits the point where two bricks touch and flies off unpredictably — it passes through both bricks, or comes straight back as if it had hit a flat side; with destructible bricks it eats the pair and reaches the row above.
- Cause: two brick colliders overlap the ball in the same frame and each one reflects the velocity, so the flip is applied twice (the net result is the wrong axis or no change); the side-detection routine also cannot tell which side was hit, because the ball centre sits on the seam.
- Invariant: a body must be given at most one collision response per frame, reflected exactly once about the correct contact normal.
- Source: https://discussions.unity.com/t/solved-3d-ball-in-breakout-clone-acts-unpredictably-when-colliding-with-corners/220689 ; https://discussions.unity.com/t/double-collision-detection-in-breakout-game/207751 ; https://stackoverflow.[BASE64_ENCODED_DATA]-brick-breaker-ball-hitting-in-between-two-bricks (title: "Unity Brick Breaker: Ball hitting in-between two bricks")

#### Tunnelling through bricks and walls on a large movement step
- Symptom: the ball goes straight through a brick or through the wall without any bounce, typically when it is fast or after a frame hiccup.
- Cause: the position is advanced by velocity*dt in a single step larger than the obstacle, and the collision test only samples the end-of-step position, so the ball is never observed inside the brick; a fast ball can also "tunnel through brick corners and miss collisions" entirely.
- Invariant: the swept path of the ball (radius-expanded) must be tested against every collider each step, so any overlap occurring during the step is detected.
- Source: https://gamedev.[BASE64_ENCODED_DATA]-breakout-in-opengl-and-c/ (title: "breakout in opengl and c++ | GameDev.net") ; https://stackoverflow.[BASE64_ENCODED_DATA]-game-javascript-sometimes-the-ball-goes-straight-through-instead-of-c (title: "Breakout game JavaScript - Sometimes the ball goes straight through") ; https://stackoverflow.[BASE64_ENCODED_DATA]-with-brick-collision-detection-in-breakout-game (title: "Problems with Brick Collision Detection in BreakOut game")

#### Ball trapped inside a block / wrong side detected
- Symptom: the ball gets stuck inside a brick, jitters, and leaves in a random direction after destroying several blocks in a row.
- Cause: the reflection is applied but the ball is never repositioned out of the brick, so on the next frame its centre is already inside the block and the top/side test — the "side-detection algorithm" that works fine on a real surface hit — picks the wrong side and reflects again. Making blocks of various sizes and the ball at various speeds makes the wrong pick frequent.
- Invariant: after resolving a collision the ball must be separated along the contact normal to exactly touching distance, with zero remaining overlap before the next step.
- Source: https://gamedev.stackexchange.[BASE64_ENCODED_DATA]-collision-detection-ball-gets-trapped-inside-block (title: "Breakout Collision Detection: Ball gets trapped inside block")

#### Chained multi-brick hit along a diagonal
- Symptom: while travelling diagonally the ball ploughs through several bricks in a row "in an unnatural way", scoring all of them in one pass.
- Cause: every brick overlapping the ball in the step is processed, instead of only the first one met; the correct earliest contact is never chosen and the remaining distance is not re-simulated along the new trajectory after the bounce.
- Invariant: resolve only the earliest collision along the path (largest/smallest x or y among the candidates), then continue the remaining displacement in the new direction.
- Source: https://stackoverflow.[BASE64_ENCODED_DATA]-with-brick-collision-detection-in-breakout-game (title: "Problems with Brick Collision Detection in BreakOut game") ; https://gamedev.[BASE64_ENCODED_DATA]-breakout-in-opengl-and-c/

#### Ball passes through the paddle when it hits the paddle's side or a fast-moving paddle
- Symptom: hitting the left or right side of the paddle makes the ball go through it and come out faster; with swipe/touch control a fast swipe puts the ball inside the bat.
- Cause: the ball is a rectangle/point tested against the paddle rectangle, so at the paddle's corners the intersection is ambiguous and the reflection axis is chosen wrongly; a paddle that moves enough to overlap the ball in one frame teleports the ball inside it before the collision is resolved.
- Invariant: paddle contact must be resolved as a circle against the *moving* AABB using the relative velocity and the contact normal, and the shapes must be separated afterwards.
- Source: https://stackoverflow.[BASE64_ENCODED_DATA]-game-trouble-with-ball-paddle-collisions-and-movements (title: "Breakout game: Trouble with ball/paddle collisions and movements") ; https://www.daniweb.[BASE64_ENCODED_DATA]-[BASE64_ENCODED_DATA]-ball-bouncing-physics (title: "Breakout Ball bouncing physics | DaniWeb") ; https://forum.gamemaker.io/index.php?threads/breakout-arkanoid-question.18940/

#### Paddle collision offset — collision box does not match the drawn sprite
- Symptom: the ball bounces as though the paddle were slightly above where it is drawn; the hit registers at the block edge rather than on the visible image.
- Cause: the collision test is run against the sprite's origin/top-left corner instead of its centre, or the collision mask and the rendered sprite disagree, so collision geometry and rendered geometry differ.
- Invariant: collision geometry must be identical to rendered geometry — same origin, size and position.
- Source: https://www.greenfoot.org/topics/58003/0

#### Simultaneous wall + paddle contact: one collision silently dropped
- Symptom: with the ball squeezed between the paddle and a side wall the ball ends up out of bounds — it goes through the wall.
- Cause: only the first contact of the frame is handled (early return / first hit wins), so the other contact is never resolved; with an imperfect separation the ball finishes the frame inside the wall.
- Invariant: every contact of the frame must be resolved, or the resulting state re-validated, and the ball must never be left outside the play area at the end of a frame.
- Source: https://www.reddit.[BASE64_ENCODED_DATA]_collision_detection_glitchbug_in/ (title: "Weird collision detection glitch/bug in Pong/Breakout? (C#)") ; https://scratch.mit.[BASE64_ENCODED_DATA] (title: "Need help with Breakout Ball Bounce Script - Discuss Scratch")

#### Ball sticks to the map edge with zero speed
- Symptom: the ball gets stuck on the edges of the map with no direction and no speed.
- Cause: each collision multiplies the velocity by a bounce/damping factor (or reflects an already near-zero component), so the magnitude decays to zero as contacts accumulate.
- Invariant: after every collision the speed must be renormalised to the game's speed constant, and never be below a fixed minimum.
- Source: https://stackoverflow.[BASE64_ENCODED_DATA]-game-breakout-ball-loses-speed-and-direction (title: "Unity Game BreakOut ball loses speed and direction")

### player input

#### Paddle/character only moves while the input device is moving
- Symptom: if the mouse is not continuously moved the character stops walking; the player must jiggle the pointer to keep moving.
- Cause: the displacement is computed from the accumulated mouse *delta*, so a frame with no pointer event yields a zero delta and therefore zero movement.
- Invariant: the controlled position must be a function of the current pointer position (or of the currently-held key state), never of whether events arrived this frame.
- Source: https://steamcommunity.[BASE64_ENCODED_DATA] (title: "Movement Bug?? :: BREAKOUT BABY General Discussions", https://steamcommunity.com/app/.../discussions/0/...)

#### Framerate-dependent paddle movement
- Symptom: "mouse movement seems tied to framerate"; when the framerate dips the movement is drastically altered and disorienting, the view flips 180°, or the paddle moves far less than it should.
- Cause: the per-event pointer delta is applied directly (or incremented per event) instead of being derived from a frame-rate-independent quantity, so the amount of movement depends on how many input events fired, which depends on the framerate and polling rate.
- Invariant: input-to-movement conversion must be independent of the frame rate and of the event count (consumed absolute positions, or scaling by dt).
- Source: https://steamcommunity.[BASE64_ENCODED_DATA] (title: "Bug list :: Project Breakout Bugs - Steam Community")

#### Stuck movement: paddle keeps going, or one direction stops responding
- Symptom: the paddle keeps moving after the key is released, or one side stops reacting while the other works.
- Cause: the "is button held" flag is not reliably cleared — a missed keyup (focus lost while held), or the movement applied on every keydown event instead of once in the update loop, so the flag stays true / events repeat.
- Invariant: input must be modelled as the set of currently-held keys, updated by both keydown and keyup and cleared on focus loss; movement applied once per update tick.
- Source: https://developer.mozilla.org/en-[BASE64_ENCODED_DATA]_Breakout_game_pure_JavaScript/Paddle_and_keyboard_controls (title: "Paddle and keyboard controls — MDN"); related reports: https://inputtest.online/blog-keyboard-keys

#### Paddle dragged off the play area
- Symptom: the paddle can be dragged completely off the window to the left or right (or pushed through the wall), after which the ball is unreachable.
- Cause: the position coming from the input is written directly without clamping to [0, fieldWidth - paddleWidth], or without any collider/limit stopping it at the wall.
- Invariant: after every input the paddle x must be clamped so the whole paddle stays inside the play area; the paddle must never leave the field.
- Source: https://reeborg.ca/docs/breakout_py_en/paddle3.html ; https://www.reddit.[BASE64_ENCODED_DATA]_sure_paddle_cant_be_dragged_off_screen/ (title: "Making Sure Paddle Can't Be Dragged Off Screen") ; https://discussions.unity.com/t/in-my-pong-game-how-do-i-prevent-paddle-from-going-threw-walls/64742

#### Clamping makes the paddle snap to the screen edge
- Symptom: after clamping is added, the paddle snaps to the edge of the screen instead of flat-out following the finger.
- Cause: the clamp is applied to the pointer position while the offset between the grab point and the paddle centre is not preserved, so the clamped value jumps to the boundary.
- Invariant: clamping must preserve the grab offset and only restrict the position, never displace the paddle relative to the pointer.
- Source: https://forums.unrealengine.com/t/touch-screen-breakout-paddle/468171

#### Paddle width grows without bound
- Symptom: over a long session the paddle becomes wider than the screen and can no longer be moved.
- Cause: the paddle's width is recomputed by a spawn/hit routine against the screen bounds with no maximum, so each call lets it grow further.
- Invariant: the paddle size must remain within [minSize, maxSize] and must never exceed the play area.
- Source: https://github.[BASE64_ENCODED_DATA] (title: "Fix paddle size exceeding screen bounds #402", GitHub issue)

#### Ball falls through the paddle because the ball is too fast
- Symptom: the ball is right above the paddle on one frame and below it on the next — it falls through.
- Cause: same tunnelling mechanism seen from the paddle side: without a per-second step (no Time.deltaTime / no fixed timestep) the ball is moving so fast between two frames that the overlap with the paddle collider is never sampled.
- Invariant: the ball's displacement between two checks must never exceed its radius; enforce a maximum step size (continuous detection or sub-stepping).
- Source: https://discussions.unity.com/t/creating-a-breakout-game-for-beginners-ball-falling-through-paddle/135411 ; https://scratch.mit.[BASE64_ENCODED_DATA] (title: "Issue with pong game: Ball passes through paddle - Scratch")

### screen edge

#### Bottom of the screen reflects the ball instead of costing a life
- Symptom: the ball keeps bouncing off the bottom edge after it has passed the paddle instead of being lost.
- Cause: walls are created for all four sides of the arena (or the bounce test is applied to the bottom too), and there is no separate death zone below the paddle; the ball's y is simply reflected.
- Invariant: the bottom of the playfield must never reflect the ball; crossing the paddle plane (death line) must trigger a life loss exactly once.
- Source: https://cs50.stackexchange.[BASE64_ENCODED_DATA]-ball-continues-bouncing-after-it-moves-past-paddle (title: "Breakout -- ball continues bouncing after it moves past paddle") ; https://www.studyplan.dev/sdl2/sdl2-breakout-walls

#### Ball never destroyed at the bottom: extra balls and lives draining alone
- Symptom: after losing a ball, other balls keep falling through empty space, draining lives, until the game is over.
- Cause: entering the death zone repositions the ball instead of destroying it, or the reset creates a new ball without removing the previous one, and the death-zone code runs again on every frame the ball stays below the line.
- Invariant: entering the death zone must destroy or reposition the single ball exactly once (idempotent), leaving exactly one ball in play.
- Source: https://discussions.unity.com/t/unitys-breakout-tutorial-ball-issue/129435

#### Ball escapes the playfield when the frame rate is low
- Symptom: the ball leaves the playing field entirely at low framerates (it does not bounce off the walls any more).
- Cause: the movement step is proportional to the frame time and the wall collision is only tested at the end-of-step position, so a long step jumps over the wall; the game lacks a fixed timestep for movement and physics.
- Invariant: the ball must be constrained to the playfield rectangle on every simulation step, whatever the frame time.
- Source: https://github.[BASE64_ENCODED_DATA] (title: "[Merged by Bors] - Change breakout to use fixed timestamp #1541" — "the ball is escaping the playing field at low framerates")

#### Bounce never happens: velocity re-initialised each frame
- Symptom: the ball moves but never bounces off the wall; it flies off the limit of the window.
- Cause: the velocity is declared inside the game loop, so the sign flip produced by the previous bounce is discarded at the top of the next iteration and the ball keeps its original direction.
- Invariant: position and velocity are game state: they persist across frames and change only through collisions and input.
- Source: https://www.reddit.[BASE64_ENCODED_DATA]_breakout_the_bouncing_ball/ (title: "pset4. Breakout. The bouncing ball")

#### Corner of the walls: clipping through and sticking to the stage edge
- Symptom: if the ball hits a corner of the level walls it clips through and becomes stuck at the edge of the stage; near the top wall the first collision is missed.
- Cause: the walls are separate colliders (an EdgeCollider2D for the three sides, or two colliders used for the side and top walls) and at a corner both fire — the two responses cancel or push the ball back into the wall, and with no separation the ball ends up outside the arena with no wall left to bounce on.
- Invariant: a corner contact must reflect both axes and leave the ball strictly inside the enclosing rectangle.
- Source: https://scratch.mit.[BASE64_ENCODED_DATA] (title: "Need help with Breakout Ball Bounce Script - Discuss Scratch") ; https://discussions.unity.com/t/double-collision-detection-in-breakout-game/207751 ; https://discussions.unity.[BASE64_ENCODED_DATA]-problem-883260/883260 (title: "OnCollisionEnter2D problem")

#### Perfectly axis-aligned bounce: infinite horizontal (or vertical) loop
- Symptom: the ball bounces perfectly left-right between the two walls forever without coming back into the brick field; or it locks onto the vertical axis.
- Cause: a perfectly axis-aligned reflection leaves the perpendicular component exactly at zero; if the angle becomes exactly 0° or 90° it stays there, and a paddle bounce that returns a purely vertical velocity keeps it that way (noticeable on touch input).
- Invariant: the velocity direction must never be exactly axis-aligned: enforce a minimum absolute component on both axes after every bounce (an oscillation/angle guard).
- Source: https://discussions.unity.com/t/brickbreaker-breakout-clone-help-with-boucning-left-to-right-indefinitely/510668 ; https://discussions.unity.com/t/breakout-style-ball-getting-stuck-horizontally/9132 ; https://forum.gdevelop.io/t/error-that-keeps-moving-only-up-and-down-or-side-to-side-in-breakout/63434 ; https://deepwiki.[BASE64_ENCODED_DATA].Breakout/3.5-physics-and-movement (title: "Physics and Movement | taublast/DrawnUi.Breakout", oscillation detection)

#### Trajectory flattens until the ball can no longer reach the top
- Symptom: after a paddle hit the ball goes up bouncing side to side, and its ability to reach the top of the screen keeps decreasing.
- Cause: the launch angle is derived from a fraction of the horizontal component (or clamped), so each paddle hit lowers the vertical component instead of recomputing the angle from the hit offset, flattening the trajectory.
- Invariant: speed stays constant and the launch angle is recomputed from the hit offset on each paddle contact, bounded away from horizontal.
- Source: https://discussions.unity.com/t/breakout-game-ball-bounce-problem/477625

### time step

#### Frame-rate-dependent simulation: correct at 60 Hz, broken at 144 Hz
- Symptom: the game plays correctly on a 60 Hz monitor and breaks on a 144/240 Hz display — objects tunnel through walls, the ball moves faster, jumps go higher; symmetrically, the ball escapes the field at low framerates.
- Cause: the physics runs in the render/update callback with a variable delta (or the movement is not multiplied by dt at all), so a higher frame rate runs the integration more often and the distance covered per second changes; physics engines integrate over discrete steps, which is why the theoretically correct maths fails in practice.
- Invariant: the simulation must run on a fixed timestep (accumulator, rendering interpolated) and be independent of the render rate; test at several frame rates.
- Source: https://andreleite.com/posts/2025/game-loop/fixed-timestep-game-loop/ ; https://bubble.ro/2026/07/29/the-fixed-timestep-why-your-physics-breaks-at-high-frame-rates/ ; https://bugnet.io/blog/how-to-debug-physics-bugs-that-only-happen-at-high-frame-rates ; https://github.[BASE64_ENCODED_DATA] (title: "Change breakout to use fixed timestamp #1541")

#### Frame spike feeds a huge dt: catastrophic tunnelling
- Symptom: after a hitch or a window resize the ball crosses several bricks or leaves the playfield in one frame.
- Cause: a single frame lasting a whole second hands a massive multiplier to position += velocity * dt; a catch-up loop that spawns an unbounded number of steps per frame has the same effect.
- Invariant: dt must be clamped to a maximum value and the number of catch-up steps per frame limited, so no single step can exceed a safe distance.
- Source: https://codingace.net/general/fps_and_delta_game_loop_cal.html ; https://andreleite.com/posts/2025/game-loop/fixed-timestep-game-loop/

#### Ball speed varies with the bounce angle
- Symptom: the ball travels much faster when it leaves at a sharp angle than when it bounces nearly vertically.
- Cause: the paddle response negates only vy and adds an arbitrary increment to vx (vx += (ballCentre - batCentre) * constant), so the magnitude of the velocity vector is a function of the angle instead of being fixed.
- Invariant: the speed |v| must be constant; only the direction may change on a bounce.
- Source: https://www.love2d.[BASE64_ENCODED_DATA].php?t=95718 (title: "Question about breakout - ball and paddle collision - LÖVE")

#### Ball accelerates on every collision
- Symptom: the ball's speed grows with every hit until the game is unplayable ("the speed becomes a lot faster after that").
- Cause: the velocity is modified rather than reflected — an acceleration is added on collision, or a relative-velocity reflection is applied with the wrong sign — so speed accumulates over contacts.
- Invariant: a collision reflects the direction only and preserves the magnitude, except for an explicit, bounded speed-up rule.
- Source: https://discussions.unity.com/t/breakouts-like-game-physics-problem-balls-movement/716541 ; https://discussions.unity.com/t/simple-breakout-ball-movement/689119

### score state

#### Score counted twice for a single brick
- Symptom: the score increases by two (and the brick counter decreases twice) for one brick hit.
- Cause: the collision handler runs twice for the same collision — a second collider on the brick, or the bounce re-detecting the brick before it is removed; the handler decrements the brick count, increments the score and destroys the object, so the double call is observable.
- Invariant: scoring a brick must be idempotent: a flag on the brick guarantees exactly one credit per brick.
- Source: https://discussions.unity.com/t/is-it-possible-for-oncollisionenter-to-be-called-twice-for-the-same-collision/639691 ; https://forum.gdevelop.io/t/brick-breaker-breakout-collision-problem/32533

#### Brick credited as destroyed but still alive (and vice versa)
- Symptom: bricks that should be gone still block the ball, or a brick disappears without the score/count following.
- Cause: the hit is credited immediately while the actual removal is deferred (end of frame, queue, animation), or the destruction and the bounce happen in an order that lets the same brick be resolved again; several balls then hit the same brick before it has a chance to be destroyed.
- Invariant: the brick's alive state, its removal and its contribution to the counters must change in one atomic step, and a destroyed brick must be excluded from collision tests at once.
- Source: https://stackoverflow.[BASE64_ENCODED_DATA]-counted-as-destroyed-but-not-really-destroyed (title: "GameObject counted as destroyed but not really destroyed") ; https://forum.gdevelop.io/t/brick-breaker-breakout-collision-problem/32533 ; https://www.lexaloffle.com/bbs/?tid=159861

#### Level cleared while bricks are still on screen
- Symptom: the level ends (or the win triggers) with 2-5 bricks still visible, while the brick variable already says 0.
- Cause: the remaining-brick counter is decremented without the brick actually being removed — a stale or spurious overlap decrements it — so the counter diverges from the real bricks, and the win condition trusts the counter.
- Invariant: the win condition must be derived from the same authoritative state as the bricks (count the live bricks, or keep counter and bricks inseparable and consistent).
- Source: https://www.reddit.[BASE64_ENCODED_DATA]_weird_bug_in_breakout/ (title: "[pset3] weird bug in breakout : r/cs50")

#### Brick hit not registered at all
- Symptom: the ball visibly hits a brick and nothing happens — no score, no destruction.
- Cause: the collision test never runs for that brick — the detectCollision routine was changed/emptied, only the first candidate brick is tested (early return), or a pause/timing in the loop delays the detection; a mismatched mask has the same effect.
- Invariant: every brick overlapping the ball's swept path must be tested each step; no candidate may be skipped.
- Source: https://www.reddit.[BASE64_ENCODED_DATA]_breakout_bugs/ (title: "pset4 - breakout bugs : r/cs50") ; https://stackoverflow.[BASE64_ENCODED_DATA]-detection-between-brick-and-ball-breakout-brick-breaker

#### The game never ends on a terminal state
- Symptom: the match never finishes when all bricks are cleared or the ball is lost; it only stops when the step limit is reached.
- Cause: the termination condition only checks the step counter — done = logical_or(state.done, state.time >= max_steps) — and the done flag is never set when a real end-of-game state is reached.
- Invariant: the game must terminate exactly when a terminal state is reached: all bricks cleared, ball lost with no lives left.
- Source: https://github.[BASE64_ENCODED_DATA] (title: "Fix breakout termination bug · Issue #22 · RPegoud/jym", GitHub)

#### Losing the ball restarts the whole game instead of removing one life
- Symptom: when the ball falls below the paddle the score and lives reset as if the game had restarted, instead of one life being consumed.
- Cause: the routine that resets the ball position also reinitialises the persistent counters (lives, score) — one reset function handles both transient round state and match state.
- Invariant: a ball loss must reset only the transient round state (ball position and velocity); lives and score are match state and must survive.
- Source: https://github.[BASE64_ENCODED_DATA]_days_100_web_project/issues/5850 (title: "[Feature]: Add Mouse Controls, Lives System & Pause Menu to Breakout ..." — "Right now the game resets entirely when the ball falls below the paddle") ; https://developer.mozilla.[BASE64_ENCODED_DATA]_Breakout_game_pure_[BASE64_ENCODED_DATA]_up (title: "Finishing up — MDN Breakout tutorial")
