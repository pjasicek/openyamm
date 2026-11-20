# MM9 player slope limit and step height (reverse engineering)

How steep a floor the Might and Magic IX player can walk up, what happens on steeper faces, and how high a ledge the
player steps onto without jumping. This comes from the shipped binaries. Research date 2026-11-02, using
`objdump -M intel` listings and Python constant and cross-reference scans (scratch: `re_mm8/work/mm9_slope/`,
ignored). Method and conventions follow the [monster collision RE](MM9_MONSTER_COLLISION_RE.md) and the
[render lighting RE](MM9_RENDER_LIGHTING_RE.md). LithTech is Y-up, so a face's "normal y" is its cosine to vertical.

| Binary (`mm9/game/`) | SHA-256 | Role |
| --- | --- | --- |
| `lithtech.exe` | `4e9ddd2b69db934ecbd7399dd92992004e596907da4a214450f31c5dd39e56d8` | Engine; holds the shared client/server physics (collision, stair stepping) |
| `data/cshell.dll` | `678700ff1cc795aeee49fe8427a42e1686d5a20dfdc1617eb46a8ef19f82f7ae` | Client game code: the player movement object (`clientmover.cpp`) |
| `data/object.lto` | `b1271f37e5314281035efe6425dd59051bb8a9b0271de0d75a5926a7bc37f162` | Server game code; not involved (the player moves client-side) |

## The rule

The player is a client-side model object (`models\player\player.abc`) created with flags `0x72000`, which include
`FLAG_GRAVITY` and `FLAG_STAIRSTEP`, and `Flags2` `0x11`, which selects the engine's cylinder collision. Its
half extents are the model's animation 0 (`static_model`) dims, **(15, 33, 15) LT**, times a player scale that is
initialised to 1.0. That gives a radius of 15 LT and a height of 66 LT.

**Walkable slope: a face with normal y ≥ 0.7071 (45.0°).** Only such faces lift the player in the engine's stair-step
pass. Our current 0.708 is the same limit, except that it rejects a face at exactly 45° (normal y 0.70711), which
MM9 accepts. Use 0.7071.

**Steeper faces work in two bands:**

- **Normal y from 0.1 to 0.7071 (45° to 84.3°):** the stair-step pass pushes the player's feet out of the face
  **horizontally only**, so the face blocks like a wall and cannot be climbed. The engine still records it as the
  face the player stands on, so the player counts as on the ground there (no fall state). Gravity then carries
  the player down along it. That last point is inferred and not traced through the motion code.
- **Normal y below 0.56 (steeper than 55.9°):** the client mover adds an explicit slide. Whenever it sets the
  player's velocity and the standing face's normal y is below 0.56, it zeroes the horizontal velocity and forces the
  vertical velocity to at most −100 LT/s. The player loses all control and slides or drops off. This is skipped
  while one of two mover states is set; one of them clears `FLAG_GRAVITY` (flight).
- Faces with normal y ≤ 0.1 (steeper than 84.3°) never take part in stair stepping. They are ordinary walls for
  the collision cylinder.

**Step height: half the player's half-height, 0.5 × 33 = 16.5 LT, which is 42.24 in our units (× 2.56).** The engine
runs stair stepping on the bottom quarter of the body box (offset −0.75 × dims.y, half-height 0.25 × dims.y). It
lifts the player by however far a walkable face (normal y ≥ 0.7071) reaches into that box. The ledge top must
therefore be within 16.5 LT of the feet. The box is swept from the old position to the new one, so in one frame
the reach also includes that frame's vertical movement. The collision cylinder then covers only the body above the
step zone. The step height is hard-coded to these fractions: this LithTech build has no `StairHeight` cvar or
`Get/SetStairHeight` physics call. Surfaces flagged NotAStep cannot be stepped up onto, but they can still be
landed on when the player is moving down at least that far.

## Evidence

`lithtech.exe` (image base `0x400000`). Globals used by the collision code are `0x496ae4` (the current request),
`0x496ae0` (the current CollideInfo), `0x496a98`/`0x496aa4` (P0/P1) and `0x496a88` (the stair-step offset vector).

| Address | What it does |
| --- | --- |
| `0x4467b3…0x4467fd` | Builds the collide request. Request `+0x38` is `(object flags >> 18) & 1`, which is `FLAG_STAIRSTEP` (`1<<18`). It then calls `0x414531`. |
| `0x414531` | CollideWithWorld. If request `+0x38` is set (`0x414683`), it sets offset.y = −dims.y × 0.75 (`0x482f98`) and dims.y × 0.25 (`0x482f94`), then calls the stair-step pass `0x415cfa`. Afterwards it restores the dims. If a non-step was hit, offset.y = 0; otherwise offset.y = 0.25 × dims.y and dims.y × 0.75 (`0x414703…0x414720`). It then loops up to 40 times: `Flags2 & 0x10` selects the cylinder `0x41582d`, anything else the box `0x414a1e`. After 40 tries it prints "physics recursed infinitely". |
| `0x414839` | Sets up the axis-aligned box: min/max of P0 and P1, ± request dims, + stair offset. |
| `0x415cfa` | Stair-step pass (BSP walk). Computes fDownRemaining = P0.y − P1.y. A face counts only if normal y > 0.1 (`0x415e02`, `0x489b08` = 0.1), (velocity + velocity offset) · n ≤ 0, and the face meets the box (`0x4124d4`). |
| `0x415eb5…0x415ec1` | `fld n.y; fcomp [0x489b0c]; jae` with `0x489b0c` = 0.7071 (`0x3f350481`). The constant is in `.data` and nothing writes to it, so it is not a cvar. At or above the limit (`0x415f4d`), the push is along the face normal by the deepest box-corner penetration. Below it (`0x415ec7`), the plane normal's y is zeroed and the rest normalised. The push is then horizontal, by penetration / (n·n_h). |
| `0x415fc8…0x41600f` | A face with surface flag bit `0x400000` (NotAStep) is rejected when fDownRemaining < push.y; the hit counts as a non-step. |
| `0x416014…0x4160d9` | Accepts the push: hit count +1, collision response `0x41611a`, P0 += push and P1 += push. offset.y and dims.y each shrink by push.y × 0.5, and the box is rebuilt. Sets CollideInfo `+0x10` (StandingOn) to this node, in both the steep and the walkable branch. |
| `0x41582d` | Cylinder collision: radius = min(dims.x, dims.z), height = dims.y. Its cylinder stair-step member (`[ebp-0x10c]`, `this+0x20`) is cleared at `0x415880`. So the 0.707 check in its HandleCollision (`0x4140e4`, `0x482f88` = 0.707) never runs. |
| `0x482824` | Client ILTPhysics vtable (stored at `0x40428d`). `+0x14` SetVelocity (`0x404b6a`), `+0x28` GetObjectDims, `+0x30` MoveObject, `+0x34` GetStandingOn (`0x42f3d5`). The slots come from the error-string functions; there are no stair-height slots. |

`cshell.dll` (image base `0x10000000`). The client interface is `[0x100dfc4c]` and its physics is `+0x3b0`. The player
mover's vtable is `0x100c9490`.

| Address | What it does |
| --- | --- |
| `0x10096cf0` | Creates the player object: type 1 (model), flags `0x72000` (SOLID, GRAVITY, STAIRSTEP and `1<<16`), `Flags2` `0x11`. The filename comes from `0x100424c0(0x131)` = `"models\player\" + "%splayer.abc"`. It reads the dims of animation 0 (`0x1009ae20`, the model interface `+0x30`) and passes them to vtable `+0x10`. |
| `0x1009a3b0` | Mover SetDims (vtable `+0x10`): dims × player record `+0x4c` (record `0x212e8` of the data manager, set to 1.0 in its constructor at `0x10041bbd`), then the physics SetObjectDims. |
| `0x10097c30` | Per-frame ground check, called from the update at `0x100994c0`. It calls GetStandingOn (`0x1009aca0`, physics `+0x34`). If the player stands on something, mover `+0x16b0` = CollisionInfo plane normal y and the on-ground flags are set; otherwise `+0x16b0` = 1.0. |
| `0x10099e10` | Velocity setter used by every mover (14 call sites). If `+0x16b0` < 0.56 (`0x100d723c`), and mover `+0x1594` and `+0x1590` are both 0, it writes velocity = (0, min(v.y, −100), 0) and passes it to physics SetVelocity (`0x1009ac50`, `+0x14`). `+0x1594` is set at `0x100989e8` together with clearing `FLAG_GRAVITY`. |
| `0x10096f40` | Crouch support: reads the dims of `CrouchIdle`. In `player.abc` that is (15, 20, 15). If crouching applies those dims, the crouched step height would be 10 LT. Not traced. |

Model data (`mm9/extracted/MODELS/MODELS/PLAYER/PLAYER.abc`, read with the collision-scan helper): `static_model`,
`stand1`, `stand2` and the attack animations are (15, 33, 15); the five `Crouch*` animations are (15, 20, 15).

## Confidence and open points

- **High:** the 0.7071 walkable threshold and its horizontal-push branch in the engine, the 0.56 slide rule in the
  client mover, `FLAG_STAIRSTEP` on the player, and the bottom-quarter stair box. Each is read directly from the code
  above.
- **High for standing height, medium overall:** the step height of 16.5 LT. It rests on the player's dims being
  `static_model` × 1.0. No other writer of the player record's scale was found. Crouched dims, and whether MM9
  swaps dims while crouching, were not traced.
- **Medium:** what the player feels between 45° and 55.9°. The code shows the face blocks horizontally and still
  counts as ground. The claim that gravity then slides the player down rests on the collision response and was not
  checked in the game.
- The two mover states that switch off the 0.56 slide are only partly identified: `+0x1594` turns gravity off
  (flight), and `+0x1590` is unknown.
- Monsters were not studied. They move server-side with their own flags.
- No console variable is involved anywhere: none of the three binaries holds a slope or stair-height cvar string.
