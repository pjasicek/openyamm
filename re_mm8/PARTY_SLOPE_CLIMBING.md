# Party slope climbing: original MM8, GrayFace patch, OpenEnroth and OpenYAMM

Investigated on 2026-10-25 after player reports that slopes cannot be climbed ("Alvar: Ogre fort slope leading to
the lower level is unclimbable — you're basically stuck after going down"; "the slope climbs are very problematic").

Addresses are in the verified GOG executable `mm8_orig/MM8-Rel.exe` (SHA-256 `5326d564…`, image base `0x400000`)
unless marked as the GrayFace-patched `mm8.exe` (`97be86a7…`). Decompiled with rz-ghidra from
`work/mm8-rel-5326d564-base.rzdb`; every rule below was checked in the assembly.

## Routines

| Address | Role |
|---|---|
| `0x473fee` | Party movement outdoors (ODM): input, gravity, terrain slide, collision loop, face responses |
| `0x472e86` | Party movement indoors (BLV): same structure, indoor face responses |
| `0x4836bc` | Terrain triangle steep test: height range of the triangle > 512 |
| `0x46def7` | Terrain normal |
| `0x46d6bb` / `0x46ef67` | Outdoor / indoor floor query (see [creature movement](CREATURE_MOVEMENT.md)) |
| `0x46bab0` | Gravity strength: 10, or 2 when a game flag at `[0x75cd18]+0xe24` has bit 3 set |
| `0x46baaa` | Stationary speed² threshold, 400 |

Velocities are fixed point; every collision iteration (up to 100) ends by multiplying the velocity by
`0xe484/65536 ≈ 0.8926`.

## Outdoors (`0x473fee`)

**Steep terrain.** `0x474046` tests the party's terrain triangle (range > 512; cleared underwater). On the ground,
not on a model, on a steep triangle (`0x474cea–0x474d8d`): Z snaps to the floor, `vz += -8 · gravity · dt`, then
`v += n · |n·v|` with the terrain normal. Horizontal input is **not** removed and the low-speed stop at
`0x474e4b` is skipped. In the collision loop (`0x475069–0x475175`) each axis of a step off a model is refused only
when its triangle is steep **and** the floor there is above the party's current Z (no tolerance); if both axes are
refused, the full step is allowed when it does not rise. The compared Z (`[ebp-0x2c]`) is the Z at the start of the
pass, and it becomes the swept Z (`0x4751ac`) even when both axes are refused. So a party on a steep triangle climbs in
small hops: the reflected velocity lifts it off the slope, and it advances while above the floor. A grounded party on a
gentle triangle cannot walk up into a steep one at all: the floor across the edge is above its Z.

**GrayFace `ClimbBetter`** (default on in the MM7 and MM8 patches, so in MMerge; unused in MM6; README: "Now you can climb steep
mountains, like you used to when the game came out"). `MMCommon/MMHooks.pas` patches `mm8.exe 0x4732E7` from `0xC1`
to `0x41`, turning `lea eax,[ecx+eax*8]` into `lea eax,[ecx+eax*2]`: the steep-terrain pull becomes
**2 × gravity instead of 8 ×**. MM8-Rel.exe still has `×8` at the matching `0x474d03` (`lea esi,[ecx+eax*8]`).
Players' expectation is the patched (retail 1.0) behaviour.

**Model faces** (`0x4751c4–0x47553d`), face record offsets: normal `0x00–0x08`, bounding-box Z `0x11e/0x120`,
polygon type `0x12f`:

- `small = maxZ − minZ ≤ 32` (`cmp eax, 0x20; setle` at `0x47520b`);
- `steep = normal.z < 46378` (`0x475219`, no `> 0` test), cleared underwater;
- type 3 floor: Z = vertex 0 Z + 1, `vz` clamped to ≥ 0, slow horizontal speed stopped;
- `!small && (type != 4 || steep)` (walls, steep slopes): `d = max(|n·v|, moveDistance/8)`, `v.xy += n.xy·d`,
  `v.z += n.z·d` **only if not steep**, then push out of the plane (Z only if not steep) — a steep face can't be
  climbed but does not slide the party either;
- otherwise (small faces of any type, walkable type-4 slopes): `v += n·d` on all three axes — climbs.

## Indoors (`0x472e86`)

There is **no steepness test on faces at all** (the 46378 constant occurs only in the outdoor routine and an
unrelated `0x458da9`). Face responses at `0x473ac2–0x473dd9`, BLV face record offsets: normal `0x10–0x18`, type `0x5c`:

- type 3 floor: Z = vertex 0 Z + 1, `vz ≥ 0`;
- type 4 (in-between floor/wall), **any slope**: `v += n·max(|n·v|, moveDistance/8)` on all axes — climbs;
- other types: same push plus push-out of the plane.

Standing support (`0x473751–0x473799`): on the ground, gravity applies only when the floor face's `normal.z < 0.5`
(steeper than 60°, `cmp …, 0x8000` at `0x47377c`), and then only 1 × gravity; otherwise `vz = 0`. Airborne gravity
is 2 ×. Vertical velocity persists between frames (`0xb21488`). After the sweep the floor is queried at Z + 40; a
step is refused if there is no floor or it rises more than 128 (`0x473a2a–0x473a37`).

So in MM8 a party running into a type-4 slope gains height: walking 750 units/s into a 64° face
(`n = (−0.9, 0, 0.43)`) leaves about `(143, 0, 293)` before damping, more than the per-frame gravity removes. The same
holds for MM7: its executable contains 46378 only once (its outdoor routine).

## OpenEnroth

`src/Engine/Graphics/Collisions.cpp` applies `bFaceSlopeTooSteep` (`0 < nz < 0.7077`) to indoor faces too, then
needs per-map exceptions (Tidewater Caverns, Castle Gloaming, Castle Harmondale, Hall of the Pit) and a catch-all for
invisible type-4 faces — symptoms of a rule the original indoor code does not have. Outdoors it makes steep faces
lower than **128** walkable (the original: **32**), uses a slide-plane projection, 5 collision iterations, `8 ×`
terrain slide (no ClimbBetter).

## OpenYAMM gaps

Reproduced with headless `movement_segment` probes (MM8, actor AI and collision off):

| Probe | Result |
|---|---|
| out03 (Alvar), terrain south of the Ogre fort plateau, y −1400 → 700 | Climbs (all tiles ≤ 512); not the reported spot |
| d12 (Ogre Fortress) ramp faces 388–394 (11–30°) | Climbs on a centred path |
| d12 face 319: 64°, 896 high, z 0 → −896 (`x −4544…−4112`) | Slides down; walking back up gains **0** height |
| out03 steep terrain column `x −16640`, y −19700 north (tiles 544–640) | Pushed ~600 units **downhill** in 6 s |

1. **Indoor slopes (main cause of the Ogre Fortress report).** `IndoorMovementController` blocks every face with
   `0.1 ≤ nz < 0.7077` (`indoorFaceIsSteepFloorCollisionSurface`, `indoorFloorTooSteepForUphillStep`) — the
   OpenEnroth rule, not the original. 95 of 161 MM6–MM8 dungeons have visible slopes 45–60° and ≥ 48 high that the
   original lets the party walk up with no slide at all. Original rule: type-4 faces always respond as climbable;
   standing gravity only below `nz 0.5`. The controller is shared with actors, whose original indoor rules differ
   (`0x46fb6d`), so a fix must be party-only.
2. **Steep terrain.** `OutdoorMovementController` (slope slide branch) removes the uphill component of the input on a
   steep triangle and pulls with `4 × GravityPerSecond` (= the unpatched `8 × g`). The original keeps the input and
   reflects `v += n·|n·v|`; with ClimbBetter the pull is `2 × g` (`1 × GravityPerSecond` on our scale).
3. **Steep model faces outdoors.** The extra `partyOnSteepBModel` slide (4 × gravity while standing on a steep model
   face ≥ 128 high) has no counterpart; the original only refuses the upward push. Conversely our 128 "small slope"
   height (from OpenEnroth) is more permissive than the original 32 for faces 33–127 high.
4. ~~Steep-terrain advance tolerance~~ is not a gap: the party stands one unit above the floor
   (`GroundSnapHeight`), so `z − 1 + ε` is the floor height, as in the original's `floor > z`.
5. **Not investigated:** MM8's gravity strength is 10 (or 2 with the flag above); OpenEnroth and our outdoor
   `GravityPerSecond = 1280` assume 5. This affects fall and jump arcs and every gravity-scaled slide.

## Changes made (2026-10-25)

- Gap 1: `IndoorSlopeRule::Party` (set by `IndoorPartyRuntime`) turns off the uphill-step refusal and the steep-floor
  slide response for the party; actors keep `IndoorSlopeRule::Actor`. Face 319 now climbs 827 of its 896 units in
  4 s. Not modelled: the original's slow creep (about 40 units/s with its per-tick damping) when standing still on a
  face steeper than 60°.
- Gap 2: steep terrain keeps the input, reflects `v += n·|n·v|` and pulls with ClimbBetter's 2 × gravity
  (`TerrainSlopeSlideGravityMultiplier`). A party on the steep Alvar tiles at `x −16100, y −19700` climbs 625 units in
  4 s.
- Gap 3 (`partyOnSteepBModel` slide, 32 vs 128 small-face height) is unchanged.
- Regression: `tests/scenarios/mm8_party_slopes.yml`.
