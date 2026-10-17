# Catalogue of classic arcade bugs

## breakout

### movement collision

#### Tunnelling: ball passes through brick or paddle at high speed
- Symptom: the ball visibly crosses a brick (or the paddle) without registering a hit; the player sees the ball "fly through" the target, and the hit is silently lost.
- Cause: collision is tested only against the object's position at the end of the frame, not the path swept between the previous and current position. If the per-frame displacement is larger than the brick/paddle thickness, the ball steps entirely past the collider between two samples.
- Invariant: for every frame, the segment from the ball's previous position to its new position must be tested against all colliders, not just the new point.
- Source: https://github.com/phaserjs/phaser/issues/1424

#### Lost hits when ball travels faster than the paddle is thick
- Symptom: after the ball speeds up over the course of a game, it starts going straight through the paddle instead of bouncing; doubling the update rate merely delays the effect.
- Cause: the numeric displacement per update exceeds the paddle's thickness, so no sample ever falls inside the paddle rectangle. Raising FPS only shrinks the displacement, it does not guarantee a sample inside the collider.
- Invariant: the collision test must be independent of speed; a fast ball and a slow ball crossing the same geometry must produce the same hit.
- Source: https://stackoverflow.com/questions/49457252/js-collision-detection-doesnt-work-when-ball-is-moving-faster

#### Ball trapped/stuck inside a block
- Symptom: the ball stops inside a brick and vibrates or slides along one axis; it can only escape through one face.
- Cause: on overlap the code reflects a velocity component but never moves the ball back out of the collider (no penetration resolution / rewind to contact). Each frame it re-collides and re-reflects, so it oscillates in place. Blocks of varying sizes and speeds make partial overlap the norm.
- Invariant: after resolving a collision, the ball's position must lie outside all colliders, and the next frame must not report the same collision again.
- Source: https://gamedev.stackexchange.com/questions/95817/breakout-collision-detection-ball-gets-trapped-inside-block

#### Wrong bounce axis at a block corner
- Symptom: when the ball strikes the exact corner between two blocks it dives through them and destroys three or more bricks before bouncing off incorrectly.
- Cause: side detection compares the ball centre against the rectangle edges; at a corner this test is ambiguous and only one axis is inverted (or a stale axis is chosen), so the reflected velocity still carries the ball into the neighbouring block.
- Invariant: the chosen reflection side must be the face the ball is actually penetrating, and the corrected velocity must point away from every overlapping collider.
- Source: https://discussions.unity.com/t/solved-3d-ball-in-breakout-clone-acts-unpredictably-when-colliding-with-corners/220689

#### Only one axis flipped at a two-wall corner
- Symptom: the ball ricochets off one wall straight into an adjacent one and escapes the play field.
- Cause: the collision loop `break`s on the first solid collider it resolves, so the second simultaneous collision (the perpendicular wall) is never processed and only one velocity component is changed.
- Invariant: the resolved velocity must be consistent with all contacts detected in the frame, not merely the first one.
- Source: https://github.com/bevyengine/bevy/pull/685

#### Ball "latches" onto the paddle or a brick
- Symptom: the ball sticks to the paddle/brick at a fixed y-coordinate and skitters along it for a while instead of bouncing away cleanly.
- Cause: after the velocity sign is flipped, the ball's position is left unchanged inside/on the collider, so it keeps detecting the same contact and flipping repeatedly frame after frame.
- Invariant: a single collision must produce exactly one reflection and a position outside the collider; repeated frames must not re-detect it.
- Source: https://cs50.stackexchange.com/questions/9869/in-breakout-the-ball-latches-itself-to-paddle-and-bricks-occasionally

#### Ball bounces back and forth through a paddle/brick and exits the far side
- Symptom: hitting the side of the paddle or a brick makes the ball bounce internally back and forth inside the object until it comes out the other side.
- Cause: merely negating the velocity on contact without pushing the ball out means the ball remains overlapped, and each subsequent frame it is inside the collider, reverses again with the opposite sign, and effectively oscillates while drifting through.
- Invariant: an unresolved overlap must never be allowed to reverse the velocity more than once.
- Source: https://www.reddit.com/r/cs50/comments/2f9vh3/breakout_ball_bounces_inside_paddle_and_bricks/

#### Several bricks destroyed in one frame by a single collision
- Symptom: a diagonally travelling ball takes out a whole row or a cluster of bricks "unnaturally" in one pass.
- Cause: the ball's per-frame step can intersect several bricks at once, and the code processes multiple bricks on the same sample, flipping the direction once for each brick; the code does not stop at the first collision and re-evaluate the remaining path.
- Invariant: after each resolved brick, the remaining portion of the frame's motion must be re-tested from the corrected position and direction.
- Source: https://jakesgordon.com/writing/collision-detection-in-breakout/

#### Brick collisions resolved one frame too late
- Symptom: the ball clips into the brick before it bounces, and adjacent bricks in the same row are hit in a way that looks deeper than the ball's radius.
- Cause: collisions are gathered after a full frame of movement and the reflection is applied to the already-penetrated position, so the visual contact point is inside the brick rather than at its surface.
- Invariant: the rendered position at the moment of contact must coincide with the surface of the collider.
- Source: https://jakesgordon.com/writing/collision-detection-in-breakout/

#### Circle-versus-rectangle side detection is ambiguous without rewinding
- Symptom: the ball bounces off the wrong face of a brick, most often at corners and along the brick seams.
- Cause: deciding the bounce face from the circle's current centre is unreliable because the circle can overlap two faces at once; the correct face must be inferred by rewinding to the moment of first contact and comparing the centre then.
- Invariant: the face used for reflection must correspond to the first surface the circle touched, not its position after penetration.
- Source: https://eieio.games/blog/breaktime/

#### Ball bypasses the remaining bricks after the first collision in the loop
- Symptom: a fast diagonal ball skips a line of bricks entirely, then hits a later brick, giving the impression of selective no-collision.
- Cause: the collision routine iterates bricks and resolves the first hit but does not re-run the test for the newly reflected trajectory within the same frame, so bricks the ball would have hit after the bounce are never checked.
- Invariant: the complete piecewise trajectory of the ball during one frame must be examined, including segments after a bounce.
- Source: https://stackoverflow.com/questions/16624712/problems-with-brick-collision-detection-in-breakout-game

#### Angle control uses the collision point rather than the paddle-relative offset
- Symptom: the ball's rebound angle does not change with where it struck the paddle, or changes erratically, making aiming impossible.
- Cause: the reflection is computed as a plain negation of the y-velocity, or the offset is measured against the wrong origin, instead of using the signed distance from the paddle centre as a factor for the x-velocity.
- Invariant: the outgoing angle must be a continuous function of the hit offset along the paddle, with a plain reversal at the centre.
- Source: https://stackoverflow.com/questions/33901443/breakout-paddle-collision-with-angle

### player input

#### Paddle can be driven off the edge of the screen
- Symptom: holding a direction key or moving the mouse pushes the paddle partly or wholly outside the play field, so the ball can pass where the paddle no longer exists.
- Cause: the movement code applies the input delta directly to the paddle position without clamping it to the play field bounds.
- Invariant: the paddle's full rectangle must always remain inside the horizontal play area, whatever the input.
- Source: https://stackoverflow.com/questions/72641246/breakout-game-java-paddle-going-off-right-side-of-screen

#### Paddle clamp uses the wrong dimension constant
- Symptom: the paddle still leaves the right edge (or is stopped at the wrong place) even though a clamp was written.
- Cause: the bound is computed with the window height instead of the window width (e.g. `WINDOW_HEIGHT - PADDLE_WIDTH`), so the maximum x is wrong.
- Invariant: the clamp value must be derived from the same axis as the moving coordinate and from the paddle's own extent.
- Source: https://stackoverflow.com/questions/72641246/breakout-game-java-paddle-going-off-right-side-of-screen

#### Mouse-follow paddle starts half a width past the edge
- Symptom: exactly half of the paddle hangs off the window when the cursor reaches the border.
- Cause: the paddle is positioned at `mouseX - paddleWidth/2` with no clamp, so the centre follows the cursor and the left/right halves cross the boundary.
- Invariant: after centring the paddle on the pointer, the resulting rectangle must still be clamped inside the play field.
- Source: https://www.reddit.com/r/cs50/comments/2jl5y9/pset4_breakout_paddle_going_out_of_window/

#### Unchecked NULL mouse event crashes the game
- Symptom: the window opens, but as soon as the cursor enters it the program terminates with a segmentation fault.
- Cause: `getNextEvent(MOUSE_EVENT)` is used without testing for NULL, so the first call that has no pending event dereferences a null pointer.
- Invariant: an event must be validated before any field of it is read; "no event this frame" must be a normal, handled state.
- Source: https://www.reddit.com/r/cs50/comments/28woxb/pset_4_segmentation_fault/

#### Paddle snaps to the cursor instead of moving smoothly
- Symptom: the paddle jumps to the mouse position rather than tracking it fluidly, feeling twitchy or sluggish compared with a reference implementation.
- Cause: the paddle is teleported to an absolute mouse coordinate on every move event instead of being driven by a per-frame velocity/lerp, so movement depends on event frequency and cursor jumps.
- Invariant: paddle displacement per update must be bounded (a maximum speed) irrespective of how far/fast the pointer moved.
- Source: https://www.reddit.com/r/cs50/comments/34sn8t/breakout_paddle_movement/

#### No bounds on keyboard paddle movement
- Symptom: the paddle slides off the screen while an arrow key is held and cannot be recovered.
- Cause: key events set the paddle velocity but no per-frame update clamps the position to the wall, so the paddle leaves the field and stays out.
- Invariant: every input path (keyboard, mouse, touch) must share the same bounds enforcement.
- Source: https://wiki.gdevelop.io/gdevelop5/tutorials/breakout/

#### Input applied in the event handler rather than the update loop
- Symptom: paddle motion is not smooth and can exceed bounds; behaviour differs with input device polling rate.
- Cause: movement is executed inside the key/event callback, decoupling it from the frame loop; multiple events within one frame move the paddle several steps and bounds logic is skipped.
- Invariant: input handlers should only record intent; all position changes must happen once per update under the same validation.
- Source: https://reeborg.ca/docs/breakout_py_en/paddle3.html

#### Wrong event coordinate used for the paddle axis
- Symptom: the paddle does not move horizontally (or moves on the wrong axis) when the mouse moves.
- Cause: the position is set from an unfiltered event field or the mouse handler is placed outside the main loop, so it never runs / uses a stale coordinate.
- Invariant: the handler must run inside the game loop and read the axis field matching the paddle's movement axis.
- Source: https://cs50.stackexchange.com/questions/10201/breakout-main-function-will-not-move-the-paddle-or-the-ball

#### Paddle flickers under the collision/input system
- Symptom: the paddle visibly flickers or jitters while the player moves it.
- Cause: paddle position is reconciled by the physics/collision pass from an input-set position that is overwritten every frame, producing oscillation between two candidate positions.
- Invariant: exactly one system must own the paddle's authoritative position per frame.
- Source: https://github.com/phaserjs/phaser/issues/1424

#### Paddle origin/offset makes it render too low or clipped
- Symptom: on first render the paddle sits at the very bottom of the screen, too low to be usable, until its origin is corrected.
- Cause: the position is interpreted from the object's centre, but the intended anchor is the middle-bottom of the paddle, so the sprite is drawn half a height too low.
- Invariant: the anchor/origin used for placement must match the anchor used for control and clamping.
- Source: https://developer.mozilla.org/en-US/docs/Games/Tutorials/2D_breakout_game_Phaser/Player_paddle_and_controls

#### Ball launches or resets on the wrong input state
- Symptom: the ball stays glued to the paddle, or launches immediately at start, so the player never gets the serve they expect.
- Cause: the `Stuck`/serve flag is not set and cleared exactly on the launching input, so the ball either keeps following the paddle or is released before the player is ready.
- Invariant: the ball must be attached while stuck and detached exactly once on the launch input, with a defined initial velocity.
- Source: https://learnopengl.com/In-Practice/2D-Game/Collisions/Ball

### screen edge

#### Ball escapes the arena at low frame rates
- Symptom: after letting the game run, the ball teleports through a wall and leaves the field, never to return; reproduces more often on slow machines or under load.
- Cause: at a fluctuating/low frame rate with high ball velocity, the ball moves a large distance between frames and steps over the thin wall entirely, so the edge test never sees it inside the wall.
- Invariant: the ball must remain within the arena for every possible frame delta; the wall test must cover the swept path, not only the sampled position.
- Source: https://github.com/bevyengine/bevy/issues/1240

#### Ball drifts slightly off-screen to one side
- Symptom: the ball rests or bounces a few pixels outside the right edge even though it is otherwise contained.
- Cause: the reflection clamps one edge by the ball's width/size but the opposite edge (or the radius) is not accounted for symmetrically, so the correction is off by the radius and the ball sits partly outside.
- Invariant: the containment test must treat all four edges symmetrically, using the ball's radius on every side.
- Source: https://github.com/Wolfyxon/3ds-web-stuff/issues/74

#### Ball bounces off one wall into another when walls meet
- Symptom: holding the ball in the narrow gap between paddle and wall or hitting a corner sends it flying off the walls.
- Cause: the collision loop exits after the first solid collider, so a simultaneous collision with the perpendicular wall is ignored and only one axis is reflected; alternatively the ball hits the corner and only one velocity axis changes.
- Invariant: every simultaneous wall contact must be resolved in the same frame.
- Source: https://github.com/bevyengine/bevy/pull/685

#### Walls thinner than the ball
- Symptom: intermittent wall escapes that vanish when the wall sprites are made thicker.
- Cause: the wall's collision extent is smaller than the ball's diameter, so the ball can straddle the wall without ever fully overlapping it at a sampled frame.
- Invariant: every collider must be at least as thick as the fastest body's maximum per-frame displacement (or swept collision must be used).
- Source: https://github.com/bevyengine/bevy/issues/1240

#### Ball keeps bouncing at the bottom instead of resetting
- Symptom: after missing the ball it continues to bounce along the bottom edge forever instead of returning to the start position; lives may stop dropping.
- Cause: the bottom edge is still handled as a wall (velocity reversed) and the reset branch is never reached, or the reset moves the position but does not reset the velocity, so it falls again immediately.
- Invariant: crossing the bottom with no paddle contact must consume exactly one life, reset position and velocity, and resume only after the serve input.
- Source: https://stackoverflow.com/questions/44355463/breakout-clone-lives-bug

#### Bottom edge treated as a fourth bounce wall
- Symptom: the ball never leaves play at the bottom, so the player can never lose and the game never ends.
- Cause: the bottom wall is included in the collider list, so the ball bounces off it like the other three edges and the loss condition is dead code.
- Invariant: only the top/left/right edges bounce; the bottom edge must be exclusively a loss trigger.
- Source: https://developer.mozilla.org/en-US/docs/Games/Tutorials/2D_breakout_game_pure_JavaScript/Game_over

#### Ball gets stuck under the top edge
- Symptom: the ball bounces inside the top window edge and never comes out.
- Cause: once the ball is overlapped with the top edge, the reflection and containment correction push it back against the same boundary, reproducing the overlap next frame.
- Invariant: any edge correction must place the ball fully inside the arena at a position from which it moves away from the wall.
- Source: https://www.reddit.com/r/cs50/comments/2f9vh3/breakout_ball_bounces_inside_paddle_and_bricks/

#### Ball continues its motion after falling past the paddle
- Symptom: after dropping below the paddle the ball keeps bouncing off the bottom of the window instead of resetting; the player has no chance to serve again.
- Cause: the "ball lost" test uses the paddle's row or an incorrect vertical bound, so it does not fire when the ball passes the paddle; the existing wall bounce keeps it alive.
- Invariant: the loss test must trigger as soon as the ball's bottom passes the play-field floor, independently of the paddle.
- Source: https://cs50.stackexchange.com/questions/10502/breakout-ball-continues-bouncing-after-it-moves-past-paddle

### time step

#### Ball speed tied to frame rate
- Symptom: the ball moves faster or slower depending on the machine; on a slow machine it "goes berserk" and the game is over immediately after the first serve.
- Cause: the per-frame displacement is a constant (velocity is not multiplied by the frame delta, or is multiplied by a wrong/uncapped delta), so distance travelled depends on how many frames occur per second.
- Invariant: position change per unit of real time must be constant: `position += velocity * dt`.
- Source: https://github.com/phaserjs/phaser/issues/1424

#### Unbounded delta after a stall produces huge jumps
- Symptom: after a tab is backgrounded or a frame stalls, the ball leaps a large distance and may tunnel or leave the arena.
- Cause: the elapsed time since the previous frame is used raw; a long stall yields a very large `dt`, hence a very large step.
- Invariant: the delta consumed by the simulation must be clamped to a maximum, with the excess dropped or split into fixed sub-steps.
- Source: https://www.reddit.com/r/cs50/comments/28ted1/pset4_breakout_window_is_freezing_but_wit

#### Fixed-update movement looks laggy on high refresh displays
- Symptom: on a high-refresh monitor the paddle and ball appear to stutter/judder even though the game logic is correct.
- Cause: movement is advanced by a constant amount in the fixed-update system and rendered multiple times per fixed step, so the displayed position is quantised to the fixed rate rather than the display rate.
- Invariant: rendering must interpolate between fixed simulation states so motion is smooth at the display's refresh rate.
- Source: https://github.com/bevyengine/bevy/pull/10075

#### Fixed timestep does not prevent tunnelling
- Symptom: even with fixed-step physics, a fast ball still passes through thin colliders.
- Cause: a fixed step merely fixes the size of the displacement; if that displacement still exceeds the collider thickness, the sample still hops over it. Fixed step alone is not continuous collision detection.
- Invariant: the simulation step must be small enough that max displacement is below the thinnest collider, or swept tests must be used.
- Source: https://github.com/phaserjs/phaser/issues/1424

#### Accumulator drains incorrectly, changing effective game speed
- Symptom: the game runs in slow motion or in bursts when the frame time varies, and the ball's speed changes with load.
- Cause: the delta accumulator that converts variable frame time into fixed steps is fed or drained incorrectly (e.g. not reset, or fixed step applied a wrong number of times), so updates are lost or multiplied.
- Invariant: the number of simulation steps per frame must equal the elapsed time divided by the fixed step, with the remainder carried over untouched.
- Source: https://toivjon.wordpress.com/2017/07/08/html5-breakout/

#### `pause()` in the loop throttles input and motion
- Symptom: adding a delay inside the main loop slows the paddle's responsiveness as well as the ball.
- Cause: the delay is executed in the same thread that polls input, so mouse/keyboard events are not serviced during the sleep and the paddle lags behind the pointer.
- Invariant: the frame delay must not block input handling; input must be polled before sleeping or handled asynchronously.
- Source: https://cs50.stackexchange.com/questions/24357/breakout-pausefunction-slows-the-paddle

#### Blocking wait for a click freezes the game
- Symptom: after losing a ball the window freezes with no error; debugger shows the program still running, and it only recovers on a mouse click.
- Cause: the loss path enters an infinite loop waiting for a click without continuing the event pump, so the UI thread never repaints or processes events.
- Invariant: waiting for input must return control to the event loop each frame instead of spinning/blocking.
- Source: https://www.reddit.com/r/cs50/comments/28ted1/pset4_breakout_window_is_freezing_but_wit

#### Pause toggle needs two presses / desynchronised state
- Symptom: pressing space sometimes pauses, sometimes requires two presses to resume; game state and thread state disagree.
- Cause: a boolean pause flag and the actual thread suspend/resume are updated independently, so an interleaving leaves the flag inverted relative to the running thread.
- Invariant: the pause flag and the simulation-suspended state must be changed atomically in one place.
- Source: https://stackoverflow.com/questions/20172562/java-breakout-clone-suspending-and-resuming-thread

#### Game loop runs faster than the display can render
- Symptom: visible glitches such as tearing or repeated/duplicated frames when updates outpace rendering.
- Cause: the loop assumes it defines what a frame is and generates updates against the display's refresh, which varies between devices; extra updates pile up or frames are dropped.
- Invariant: simulation cadence must be decoupled from display refresh and driven by elapsed time.
- Source: https://developer.android.com/games/develop/gameloops

#### Rendering too many objects misses the frame budget
- Symptom: frame rate drops below 60 fps and timing-sensitive bugs (tunnelling, lag) appear once many bricks and labels are drawn.
- Cause: redrawing the court, score, paddle, ball and every brick with the drawing API costs more than the 16.67 ms budget, and coarse `setTimeout`/`setInterval` resolution adds to the overrun.
- Invariant: the update+render work per frame must stay inside the frame budget, or the loop must compensate with a fixed-step accumulator.
- Source: https://jakesgordon.com/writing/rendering-breakout/

### score state

#### Score and lives never change because the display is not refreshed
- Symptom: the score stays at 0 and the ball can be missed any number of times without losing a life, even though `points++`/`lives--` are present.
- Cause: the scoreboard update call is missing, or the increment/decrement is executed on a variable that is not the one shown/read (wrong scope or wrong call site).
- Invariant: every state change must be followed by rendering the state, and the mutated variable must be the one the win/lose checks read.
- Source: https://www.reddit.com/r/cs50/comments/2yclci/breakout_have_the_entire_program_working_except/

#### Loop counter never read / shadowed, so the game never terminates
- Symptom: the ball is missed repeatedly but the loop never exits; the declared lives/bricks counters appear unchanged.
- Cause: the counter updated in one method is a different (local/shadowed) variable from the one tested in the loop condition, so the loop condition never becomes false.
- Invariant: the counter tested by the loop must be the same storage location that the collision/loss code mutates.
- Source: https://stackoverflow.com/questions/11624575/counters-not-decrementing-or-not-being-read-in-breakout

#### One miss costs several lives and empties the pool instantly
- Symptom: after a single miss the lives counter jumps to 0 and the game exits, instead of decrementing by exactly one.
- Cause: the ball is left at the bottom edge (detection condition stays true) and the loss branch runs on every frame until the reset happens, decrementing a life each time.
- Invariant: a single miss must fire the loss branch exactly once; the ball must be removed/reset before the next frame can re-trigger it.
- Source: https://cs50.stackexchange.com/questions/1973/pset4-lives-unintentional-infinite-loop

#### Win fired before all bricks are destroyed
- Symptom: the "you won" screen appears with several bricks still on screen; the counter reaches zero early.
- Cause: the brick counter is initialised or decremented incorrectly (e.g. counting removed windows, a wrong row/column total, or decrementing for non-brick collisions), so it hits zero before the board is actually clear.
- Invariant: the win condition must be derived from the actual number of remaining breakable bricks, not from an independent tally that can drift.
- Source: https://stackoverflow.com/questions/1312812/java-breakout-game-exiting-too-early

#### Game-over/win checked when counters are still zero
- Symptom: the game declares victory at the very start, before any brick is hit, or ends with bricks remaining.
- Cause: the game-over check runs on the first frame when the remaining-bricks count has not yet been initialised (still 0), so the "bricks < 1" test is true immediately.
- Invariant: the win/lose checks must only run once the board has been initialised and the game is in the playing state.
- Source: https://discussions.unity.com/t/unity-breakout-game-ending-early/600775/1

#### Brick counter hits zero while bricks remain on screen
- Symptom: the number of bricks counts down to 0 but 2–5 bricks are still visible, so the level ends early.
- Cause: the brick count is decremented on every `removeGWindow`/removal call, and some removals correspond to things other than bricks (or bricks are removed twice), so the tally fires ahead of the real board.
- Invariant: the brick count must change only when a breakable brick is actually destroyed, once per brick.
- Source: https://www.reddit.com/r/cs50/comments/2uv8j0/pset3_weird_bug_in_breakout/

#### Level advance triggers before bricks exist
- Symptom: on starting a level the board is declared clear and the game jumps forward immediately.
- Cause: the "no breakable bricks left" test runs before the first bricks have been spawned, so the initial empty board satisfies it. A guard is needed to skip the first moments after a level starts.
- Invariant: the level-complete test must be disabled until all bricks for the level have been instantiated.
- Source: https://sbox.game/facepunch/breakout/source?file=Game%2FBreakoutGame.cs

#### High scores above a threshold break the counter
- Symptom: once the score passes a certain value (e.g. 200) the on-screen score counter stops updating correctly or shows garbage.
- Cause: the score is parsed/stored with a type or routine that overflows or truncates above the limit (`parseInt`, 32-bit int, BCD digits), while the real hardware/high-score format supports larger values.
- Invariant: the score storage and display must represent the full range of achievable scores without overflow or truncation.
- Source: https://mametesters.org/view.php?id=8787

#### High-score string parsed with `parseInt` loses precision
- Symptom: a persisted high score is shown wrong after reload (rounded/truncated) once it grows large.
- Cause: the stored high score is converted with `parseInt`/`parseFloat`, which loses integer precision beyond the safe range; a BigInt-capable parse is required.
- Invariant: persisted scores must round-trip exactly between storage and display for every representable value.
- Source: https://gitlab.com/lecarore/breakout71/-/commit/751b76dfa3af2820ccd3ac23a5f1dd81a08a51e9

#### Environment reset does not reset the life counter
- Symptom: in an RL/headless harness, calling reset with a life-based episode mode keeps decrementing lives even though no steps are taken; the environment appears to no-op.
- Cause: the reset path does not reinitialise the lives/score state when `episodic_live` (life-loss-terminated episode) mode is active, so the previous episode's state leaks in.
- Invariant: a reset must restore all episode-scoped counters (lives, score, ball/paddle state) regardless of the episode termination mode.
- Source: https://github.com/sail-sg/envpool/issues/301

#### Resetting after a life loss leaves a "ghost" ball
- Symptom: after a miss, when play resumes there are two balls: one that moves and one that sits in the middle.
- Cause: the reset creates/positions a new ball without removing the old one, so the stale ball remains drawn and, in some versions, still simulated.
- Invariant: exactly one ball object must exist after a reset; the old ball must be removed before the new one is created.
- Source: https://www.reddit.com/r/cs50/comments/23pn3y/breakout_when_resetting_my_ball_i_leave_a/

#### Final brick / all-bricks-cleared detection uses the wrong liveness check
- Symptom: the game does not end when the last brick is destroyed, or ends while bricks remain, depending on the count method used.
- Cause: the win test counts active objects with a method that can include inactive/queued-for-destruction bricks, or misses the case of the very last brick, so the terminal state is evaluated inconsistently.
- Invariant: the win condition must be evaluated against the set of still-active breakable bricks only, and must fire exactly once on the transition to zero.
- Source: https://developer.mozilla.org/en-US/docs/Games/Tutorials/2D_breakout_game_Phaser/Win_the_game
