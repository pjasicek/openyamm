# MM8 Crystal Walker v2 (m596; Crystal Walker / Sentry / Guardian, monsters 148-150)

User (2026-10-19): "walker - I want you to redo this end to end like with more definition i guess ... you can use
meshy for this + the master(s) we have". This rebuild replaces the installed rigid-part model from
[`../mm8_m596_claude/`](../mm8_m596_claude/README.md), a 1,216-triangle hand-lofted mannequin.
**Status: round 7 installed 2026-10-19 (user: "ok accepted").**

[Viewer](http://127.0.0.1:8912/level_generation/creatures/mm8_m596_v2_claude/review/viewer/): installed / v2 round 1 /
round 2 / round 3 / round 4 / round 5 / round 6 / round 7 per tier, opening on round 7. Check: 216 tier/clip switches, no console errors. In-game comparison of the installed round 7:
`review/ingame/compare_walker_v7.jpg` (native sprites / old installed / v2, outdoor and indoor, same cameras), motion
`review/ingame/motion_v7.jpg`, and a hostile walker attacking the party, every 0.4 s: `review/ingame/attack_v7_sheet.jpg`.

## Route

1. **References.** The five gated HD masters of `mm8_m596_claude/references_hd/` match the native frames (broad
   shoulders, narrow waist, wedge head, backward crown, long arms, three hooked claws, prism feet). They were reused
   unchanged and copied into `references_hd/`. No native sprite went to Meshy.
2. **Geometry.** Meshy Smart Topology from `00_three_quarter.png` (`requests/geometry_v1.json`, meshy-t2, 15,000
   target faces, no texture), **5 credits**, 15,660 triangles, one closed piece.
   - `scripts/prep_mesh.py` scales it to the installed height of 1.877637 m, so the bindings' scale 101.723614 stays.
   - Soles go at z = 0, facing glTF +Z.
   - It is decimated with X symmetry to **7,000** triangles and flat shaded: the crystal facets are the triangles.
3. **Rig.** `scripts/rig.py` uses the installed walker's 18-bone hierarchy and bone names, so the actors.yml
   contract holds: `RightHand`/`LeftHand` palm sockets, `Waist` upper body, `Neck`/`Head` look.
   - Joints are fitted to this mesh from slice centroids and silhouettes (`work/joints_v1.json`,
     `review/inspect/sil_joints_v1.png`).
   - Heat weights, then rules: limbs only on their own side; claws wholly on the hand (above 0.40 m, so the wide
     prism feet never take hand weight); crown and beak on the head; no arm weight below 0.40 m.
   - Two smoothing passes, then at most 4 influences.
3b. **Head and eyes (review 2: "head has no discernable eyes").** `scripts/head_fix.py`, run before the rig.
   - The Meshy face and snout were yawed about 34° to the creature's left; the three-quarter master's head faces its
     camera. Measured on the forward-most points per 10 cm slab, they were 13-17 cm left of centre while the crown
     top was centred.
   - The face is turned back about a vertical axis through the head joint, fading in over the neck and out toward
     the crown top. The forward-most points are now within 2 cm of centre at every height (`review/inspect/
     headfix_compare.png`, before above after, top view right).
   - The masters and native frames show no distinct eyes. A gem eye is set into each side of the face: a six-sided
     faceted bipyramid, 4.2 x 2.8 cm, 12 triangles, half sunk along the surface normal at (±0.08, -0.40, 1.665),
     found by ray casts 50° off straight ahead.
   - The texture paints each gem bright amber (alternating facet brightness, roughness 0.06) in a dark plum socket
     of the face triangles within 3 cm, so the eye reads as a dark ring with an amber gem.
   - Weights: Head only. LOD0 is 7,024 triangles.
3c. **Clavicles (review 2: "right shoulder twisting", frame 29 = 0.60 s).** The rig adds `LeftShoulder` and
   `RightShoulder` between Chest and Arm (20 bones). Round 1 raised the arm 150° with Euler angles about world axes
   from a hanging rest. Near that range the composite rotation rolled the upper arm and wrapped the shoulder. Arms are
   now aimed by swing only (no roll), via a neutral out-and-forward direction, so no swing is near 180° where the
   axis is undefined. A direct swing from hanging to overhead flipped the arm (3,822°/s in the first try). The
   clavicle shares the raise (16°) and the reach.
4. **Animation.** `scripts/anim.py`, keyed at 48 fps. Poses are rotations about each joint in world rest axes, ported
   from the installed walker's `build.py`, so the native intent carries over. Every curve is a monotone cubic through
   its keys, so speed is continuous with no stop at inner keys.
   - Legs in Walking and Running use two-bone IK to planted soles. A mesh floor pass runs in Attack, Cast, Hit,
     Death and Dead.
   - Checked with `bone_velocity.py`: no clip starts with a still stretch; Standing is a slow breathing idle.
   - The largest frame-to-frame speed change is 166 deg/s at the slash in Attack; the installed Death had a
     3,512 deg/s hand flick, gone now.
5. **Texture and material.** `scripts/uv.py` (Smart UV Project, padded) and `scripts/texture.py`.
   - Triangles are grouped into 1,422 flat facets (edge-connected, within 22° of the facet normal). Each facet gets
     one tone around the native palette-596 statistics: median RGB 168,112,141, hue 330.
     - 6 % lavender or blue-violet;
     - 8 % pale pink sparkle facets at value 0.84, never white;
     - 16 % brighter;
     - 15 % deeper rose;
     - the rest a small jitter;
     - plus a soft gradient across each facet.
   - Each triangle is filled exactly (barycentric, 4x supersampled) and the islands are padded. No tone crosses a
     triangle or shows staircase edges.
   - Material `AmethystCrystal`: base colour 2048², metallic-roughness texture with per-facet roughness 0.11-0.20
     and metallic 0, `openyamm_specular` 0.8, `openyamm_edge_darkening` 0.12. Glints come from the gloss, not
     from paint.
   - All three tiers share palette 596 as in the native data, so there is no region mask or ramps.
6. **Runtime.** `tools/prepare_actor_glb.py`, then `scripts/build_lods.py` (`build_actor_lods.generate`, 4
   influences, soles, crown top and claw extremes protected): `export/mm8_m596.glb`.
   `scripts/build.sh` replays steps 4-6.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed (rigid) | 1,216 | 916 | 664 | - |
| v2 round 1 | 7,000 | 3,500 | 1,750 | 874 |
| v2 round 2 (eyes) | 7,024 | 3,512 | 1,754 | 876 |
| v2 round 3 (authored head) | 4,782 | 2,390 | 1,192 | 586 |
| v2 round 4 (body-density head) | 5,590 | 2,794 | 1,394 | 689 |
| v2 round 5 (body facet angles on the head) | 5,590 | 2,794 | 1,394 | 689 |
| v2 round 6 (no pale facets; LOD1 claw fix) | 5,590 | 2,794 | 1,394 | 689 |
| v2 round 7 (tones per small facet group) | 5,590 | 2,794 | 1,394 | 689 |

Shadow LODs match each colour LOD.

## Clips (actors.yml events unchanged: attack and cast impact 0.8333 s)

| clip | s | content |
|---|---:|---|
| Standing | 2.0 | breathing, slow weight shift, claws flexing (installed: 1.5 s, nearly frozen) |
| Walking | 1.0 | planted-sole IK gait; measured stride 0.70 m |
| Running | 0.75 | longer stride, deeper sink; stride 1.00 m |
| Attack | 1.5 | round 2 (review: "swipe from the top-right ... across to front-left"): right claw rises high on its right (0-0.40 s), coils to 0.60, swipes diagonally down across the front, at chest height in front of the body centre at 0.8333, to the front-left (0.97), recovers to Standing; trunk turns into it, neck and head counter-turn so the head faces forward throughout |
| Cast | 1.5 | separate clip: both claws rise forward-up and push toward the target through 0.8333 (glow sockets: both palms), aimed the same twist-free way |
| Hit | 0.7917 | recoil and recovery |
| Fidget | 0.625 | head turn, left claw flex |
| Death | 1.0 | knees buckle, trunk tips back, legs follow late (no feet swinging up), lies on its back |
| Dead | 1.0 | final corpse pose held |

## Gait pass (2026-10-21): Walk2 and Run2

The game moves the walker at 2.03-2.75 model units/s wandering and 4.06-5.51 chasing (tiers C-A), so the
installed Walking (0.70 m per 1.0 s) and Running (1.00 m per 0.75 s) played at 1.5-2.1x and 3.0-4.1x
(`gait_gate.py` targets: walk 2.36, run 4.72). `scripts/anim_gait2.py` adds two clips on `work/anim_v2.blend`
(saved as `work/anim_gait2.blend`, donor `work/gait2_donor.glb`); every existing clip is unchanged.

| clip | s | stride | authored speed | gait |
|---|---:|---:|---:|---|
| Walk2 | 0.75 | 1.74 m | 2.32 /s | long low stalking stride: duty 0.52 (a foot always down), the pelvis drops 15 cm at double support so the straight leg reaches 0.45 m ahead and behind, rises to 7 cm over the planted leg; pelvis yaw 7 deg into the reach, chest counter-turns, head steady, arms swing 18 deg opposite the legs |
| Run2 | 0.625 | 2.95 m | 4.72 /s | run with a flight phase: duty 0.28, lowest at mid-stance (-17 cm), highest in flight (-8.5 cm); trunk leans forward (hips 5, waist 4, chest 5 deg), head pulled up to look ahead; heels kick up 30 cm, toes up in swing; arms pump 26 deg with elbows flexed 30-40 deg |

Soles stay flat and slide back at exactly the body speed (two-bone IK, knee forward), the track 5-6 cm narrower
than at rest; every planted target is reachable (0 mm short) and no frame is under the floor (-0.3 mm).
`scripts/add_clips.py` (copied from `mm7_m386_v2_claude`) appended both clips to the installed round 7 export
(backup `work/mm8_m596_pre_gait2.glb`; the donor's Walking, Running and Attack match the installed ones exactly):
`export/mm8_m596.glb`, installed 2026-10-21 (source sha256 `78b09ad8...`).

Gate (`gait_gate.py --world mm8 --model mm8_m596.glb --candidate export/mm8_m596.glb --set walking=Walk2
--set run=Run2 --set stride_length=1.74 --set run_stride_length=2.95`): PASSED. Strides measured 1.740 / 2.943
(feet 1.738 / 2.915, trusted); window A x1.19 / x1.17, B x0.91 / x0.90, C x0.87 / x0.86 (wander Walk2 / chase
Run2); floor ok on all tiers. Winding: 0 inverted. Binding for actors.yml (applied by the coordinator):
`clips.walking: Walk2`, `animation.run: Run2`, `stride_length: 1.74`, `run_stride_length: 2.95`.

Known fault, not new: the Meshy mesh fuses the inner claws to the thighs (182 vertices with both arm and leg
weights, 74 bridging faces at |x| 0.35-0.40 m, height 0.69-0.83 m). Those faces stretch whenever hand and thigh
part: x5.0 in Walking, x7.9 Attack, x16.4 Cast, x7.3 Walk2, x10.1 Run2 (`scripts/stretch_glb.py`, every LOD), seen
as a thin dark streak from the claw to the knee when the leg trails. Arm swing was reduced (Walk2 24 -> 18,
Run2 38 -> 26 deg) to keep it small; removing it needs a re-skin or a cut between claw and thigh.

Evidence: viewer (`review/viewer/`, revisions `*_gait2`; older revisions show their Walking/Running under the
Walk2/Run2 names via `aliases` in the manifest, a small `review.js` addition), `check`: 297 switches, no errors.
Playback of every clip at 1x and 0.5x in `review/playback/` (old `Walking-*`/`Running-*` beside `Walk2-*`/`Run2-*`,
webm and frames), sheets `review/gait2_playback_sheet.png` (quarter view, old above new),
`review/gait2_left_sheet.png` and `review/gait2_quarter_sheet.png` (six phases each).

## Round 7 (2026-10-19, review: large single-tone violet/lilac patches on the forehead and muzzle side)

The patches came from tone groups. Region growing (22°) merged many jittered head triangles into one facet group,
and one tone painted all of it.

Changes in `texture.py`:
- **Group cap:** tone groups now stop growing at 3 triangles on the head and 6 on the body, and never cross parts.
  Neighbours share a tone only by chance.
- **Measured** (contiguous same-group regions): head median 3, max 3 triangles; body median 3, max 6 (1,858 groups
  in all).
- **Violet:** 3 % of groups, isolated, hue 312°, saturation +0.06 and value -0.04 against the pinks; no lilac wash.
- **Cap:** the light-pink cap from round 6 stays.

Checks:
- the specular-off renders (front and three-quarter) show no patch larger than the body's tone clusters;
- winding: 0 inverted parts;
- LODs: full height, lowest point -3.5 mm, no stretched faces;
- viewer check: 216 switches, no console errors.

Evidence:
- `review/head_r6_vs_r7.png`: rows 1-2 are round 6 above round 7 at viewer lighting; row 3 is round 7 with specular
  off;
- `review/viewer_round7.png`.

Round 6 is kept at `work/mm8_m596_v2_round6.glb`.

## Round 6 (2026-10-19, user: "some faces on the head are still white-ish?")

**Diagnosis.** I sampled the base colour under every triangle and rendered the head with specular off (Blender,
`RC_NOSPEC=1 render_clips.py`).
- **Base colour:** about 37 % of the head's triangles and 13 % of the body's had a pale base colour (value over 0.8
  or saturation under 0.22). The causes were round 1's "pale pink sparkle" facets, the baked bounce on the jaw's
  underside and the facet gradients.
- **Specular:** the rest of the pale look in the viewer was the sky reflection at grazing angles on broad upward
  head planes (the forehead).

**Changes in `texture.py`.** Glints now come only from the material, never from paint.
- **Cap:** after all tone terms, every crystal texel is capped at the palette-596 light-pink end, measured on the
  native sprites (pixels at value p75-p90: 0.74-0.84, saturation 0.33-0.26). Value is at most 0.78, saturation at
  least 0.27, and the hue is kept. The amber eyes are exempt; head and body are capped alike.
- **Result:** pale texels drop to 0 % on head and body.
- **Facet categories:** the pale facet category is now light pink (value 0.76, saturation 0.29), and the violet
  facets are deeper (saturation 0.30, value -0.06) instead of pale lavender.
- **Roughness:** crystal roughness is 0.13-0.22 per facet, and the head gets +0.11. The engine and the viewer both
  scale the grazing sky reflection by (1 - roughness), so broad head planes stop reading pale while small glints
  remain.
- **Bake:** the tone bake is triangle-exact and island-padded, as before.

**LOD1 claw stretch fixed.** `build_lods.py` keeps the claw and thigh vertices of the gap between them (|x|
0.30-0.48, z 0.55-0.90). No LOD has a stretched face in any clip now.

Checks:
- winding: 0 inverted parts;
- LODs: full height (1.8746 m), lowest point -3.5 mm;
- viewer check: 189 switches, no console errors.

Evidence:
- `review/head_r5_vs_r6.png`: rows 1-2 are round 5 above round 6 at viewer lighting (front, three-quarter, side);
  row 3 is Blender with gloss and with specular off;
- `review/viewer_round6.png`.

Round 5 is kept at `work/mm8_m596_v2_round5.glb`.

## Round 5 (2026-10-19, review: the head still shaded as a few big planes; shards single-tone blades)

The body reads faceted because neighbouring facets differ in angle, not because of edge length.
`scripts/dihedral.py` measures the dihedral angle between neighbouring faces:

| | median | p75 | p90 | under 5° |
|---|---:|---:|---:|---:|
| body, chest and shoulders | 15.4° | 24.6° | 38.9° | 16 % |
| head, round 4 (±2.5 mm jitter) | 5.5° | 15.1° | 63.4° | 47 % |
| head, round 5 (±7.5 mm normal, ±3.75 mm across) | 15.3° | 32.9° | 66.0° | 21 % |

- **Head jitter:** the normal offset was tuned (6, 9 and 12 mm tried; 7.5 mm matches the body's median). Ridges over
  28° and socket rims stay fixed, so the silhouette, brow, jaw and sockets keep their edges. The head's p90 also
  counts the crown shards' and ridges' sharp edges.
- **Crown shards:** each ring along a shard twists by up to 9° per ring and its corners are jittered 3 mm, so every
  side breaks into several planes. These take separate per-facet tones in the texture pass.
- **Evidence:** `review/head_r4_vs_r5.png`: round 4 above round 5, front, three-quarter and side close-ups at viewer
  lighting, with these numbers. `review/viewer_round5.png`.
- **LOD1 stretched face** (fixed in round 6): it is not in the head or neck. `lod_check.py` now prints stretched faces: LOD1 face 1208
  at rest (0.385, -0.067, 0.728), between the inner left claws and the thigh, stretches about 20x while the arms are
  raised in Cast. It is a LOD1 decimation joining hand and leg vertices. LOD0, LOD2 and LOD3 are clean. It was left
  as is.
- **Checks:** winding 0 inverted parts; LODs keep the full height (1.8746 m), lowest point -3.5 mm; viewer check 162
  switches, no console errors.

Round 4 is kept at `work/mm8_m596_v2_round4.glb`. The Attack is round 3's.

## Round 4 (2026-10-19, user: "head looks too low poly like less facets than the rest of the body ... make it consistent")

Same head design as round 3. Changes in `new_head.py` and `texture.py`:
- **Density:** the body's facets measure 37 mm median edge (90th percentile 59 mm) at the chest and shoulders. Hull
  edges over 48 mm are split until none remain (788 hull triangles).
- **Irregularity:** vertices are jittered ±2.5 mm along the normal and ±2 mm across it, so the facets are irregular
  like the body's. Vertices on ridges sharper than 28° and on the socket cut stay put, keeping the brow, jaw and
  sockets crisp.
- **Crown:** each shard has three rings along its length, tapering with slight irregularity (30 triangles each).
- **Tones:** the head goes through the same per-facet tone pass as the body: 1,013 facets in all, triangle-exact and
  island-padded.
- **Eyes:** larger gems (6.6 × 4.0 cm, cutter 8.6 × 5.4 cm), inset 3 mm, and brighter amber (1.0, 0.84, 0.32).
- **Neck seam:**
  - The dark line under the muzzle was a crease in the neck cap: its apex, raised in place, folded the cap under the
    jaw.
  - The cap now fans to a point inside the head, so it rises from the cut edge straight into the head.
  - The jaw's underside now slopes forward to a throat point.
  - The jaw underside and throat get a little baked bounce light (up to 40 % brighter on downward faces).
- **Size:** head 1,052 triangles, LOD0 5,590.

Checks:
- winding: 0 inverted parts;
- LODs: full height (1.8746 m), lowest point -3.5 mm, one stretched face in one clip at LOD1;
- viewer check: 135 switches, no console errors.

Evidence:
- `review/density_sheet_r4.png` (viewer lighting): round 3 head with the upper body, round 4 head close-ups, and
  round 4 with the upper body;
- `review/viewer_round4.png`.

The Attack is round 3's, unchanged. Round 3 is kept at `work/mm8_m596_v2_round3.glb`.

## Round 3 (2026-10-19, user review: "please completely re-do [the head], this is ugly"; attack "use legs also")

**Head, authored (no Meshy, no Codex).** `scripts/new_head.py` replaces round 2's `head_fix.py` in `build.sh`.
- **Removed:** the Meshy head and crown; everything inside the new head's volume; old faces in front of the kept
  back of the neck; and a leftover jaw fragment.
- **Neck:** the opening is capped and the cap poked into a faceted crystal mound, so no flat plate shows behind the
  head.
- **Skull and muzzle:** the convex hull of 34 deliberate points: a flattened wedge with a pointed muzzle, a sharp
  brow ridge and a clean jaw line, in large flat facets (68 triangles).
- **Eye sockets:** an angular pocket under each brow, cut with an exact boolean and a faceted six-sided cutter. The
  socket faces (those on the cutter surface) are painted dark plum. A smaller amber gem sits inside each pocket, its
  front 4 mm below the rim.
- **Crown:** eight diamond-section shards (base, shoulder, tip) sweeping backward and fanning out like the native
  star: top, back, upper sides, sides and low sides. The top shard is angled so the model keeps the native height
  (1.8746 m against 1.8776).
- **Size:** 232 head triangles in all, under the 300-700 target. It is closed, symmetric and flat shaded.
- **Weights:** every head vertex, crown and gems included, is weighted wholly to Head (the vertex group `HeadRigid`).
  The neck below keeps its heat weights, and the head's bottom sits over the neck stump.
- **Review:** `review/head_sheet_r3.png` shows front, three-quarter, side and from below at game height, above the
  native standing heads (sa0-sa4).

**Attack, whole body.** Impact at 0.8333 s and length 1.5 s are unchanged.
- **Legs:** the right foot stays planted by IK the whole clip. The left foot steps 30 cm forward into the swipe (lift
  0.50 s, land 0.80 s, eased, 10 cm lift with toe pitch). It stays planted forward until 1.05 s, then steps home by
  1.40 s.
- **Pelvis:** it shifts onto the right leg and back during the raise (6 cm), then lunges 13-15 cm forward and 8 cm
  down through the cut. The hips yaw with the coil and the knees bend by IK. Everything returns to Standing's pose,
  so the root ends where it started (0.0 mm).
- **Head:** neck and head counter-turn the hips, waist and chest yaw, so it faces forward throughout.
- **Locks** (`scripts/foot_lock.py`): the right ankle moves 0.0 mm. The left ankle is fixed at home and at the
  forward plant. Every clip's lowest point is -2.7 mm, at every LOD.
- **Speeds:** Attack peak 1,142°/s. The largest frame-to-frame change is 440°/s, at the swipe's own acceleration;
  the step's lift-off was smoothed to a sin² profile. The other clips are unchanged.
- **Evidence:** `review/attack_strip_front_r3.png` and `review/attack_strip_side_r3.png` (round 2 above round 3),
  `review/viewer_round3.png`.

Round 2 is kept at `work/mm8_m596_v2_round2.glb` and `work/anim_r2.blend`. In-game captures are still those of round 1.

## Round 2 (2026-10-19, user review: eyes, shoulder twist, swipe attack)

Library check first: `anim_library/mixamo/` has "Mutant Swiping", "Zombie Attack" and "Mutant Punch". Mutant Swiping is
a crouched two-arm lunge whose hips travel 0.7 m and whose head drops to 0.85 m, so it is not this upright one-claw
swipe; the attack is authored. No Meshy animation was bought.

Speeds (`bone_velocity.py`; the largest change per 1/48 s frame is the jolt measure):
- **Attack:** peak 1,162°/s at the swipe (0.79 s); largest frame-to-frame change 411°/s, at the swipe's own
  acceleration.
- **Cast:** peak 720°/s; largest change 229°/s.
- **Other clips:** the largest change is at most 176°/s.
- No clip starts still, and Attack and Cast begin and end on Standing's pose.
- Trunk lean terms use a smooth positive part instead of `max(x, 0)`; the kink made the clavicle stop dead in Cast.

`scripts/build.sh` replays head fix, rig, UVs, texture, clips, runtime and LODs in one go.

Evidence:
- `review/attack_strip_front.png`: front view every 0.125 s, round 1 above round 2;
- `review/attack_shoulder.png`: the right shoulder through the clip;
- `review/head_closeups.png`: front, three-quarter and side, textured;
- `review/viewer_round2.png`: viewer Standing and the impact frame.

The round 1 export is kept at `work/mm8_m596_v2_round1.glb`. In-game captures (`review/ingame/*_v2b.jpg`) are
round 1; round 2 changed only the head, eyes and the Attack and Cast clips, and has not been captured in game yet.

## Checks

- `check_winding.py`: 0 inverted closed parts.
- `scripts/lod_check.py` (REA_NODE=CrystalWalker; round 2 the same):
  - every LOD keeps the LOD0 bounds (height 1.8775 m, claw span 1.51 m);
  - no stretched faces in any clip;
  - the lowest point in any clip is -2.7 mm.
- Viewer check passes (`review/shots/`, `review/viewer_compare.png`).
- Clay and textured pose sheets: `review/clips_a1.png`, `clips_a2_side.png`, `clips_front.png`, `clips_t1.png`,
  `close_head.png`.
- **In game** (OpenGL desktop, isolated runs, New Sorpigal `oute3` and the `6d19` cameras of the installed
  comparison). The candidate was installed only long enough to snapshot a hard-linked assets fixture, then the
  installed model was reinstalled (`scripts/capture.sh`); the game was unchanged throughout. The fixture also set
  the v2 strides.
  - **Outdoors:** v2 reads as a faceted crystal figure close to the sprites' mauve, much more defined than the
    installed mannequin.
  - **Indoors:** close to the sprites' brightness, but with less sparkle than the native frames.

## Installed (2026-10-19)

The user accepted round 7 ("ok accepted"). The coordinator installed it:
- `python3 tools/install_model.py level_generation/creatures/mm8_m596_v2_claude/export/mm8_m596.glb --world mm8`. The
  rollback source `work/mm8_m596_source_pre_v2.glb` matched the installed a5f0bc58... first. Installed source:
  434671fd...
- `assets_dev/worlds/mm8/models/actors.yml`, Crystal Walker A/B/C: `stride_length: 0.7` and `run_stride_length: 1.0`
  (were 0.9 / 1.3), measured from this model's planted soles. Scale, sockets, events and look are unchanged.
- **Regression:** the case was renamed `mm8_crystal_walker_actor_models_keep_native_tiers_and_skinning`
  (`game/outdoor/HeadlessOutdoorDiagnostics.cpp`). It now checks the Cast clip and normalised skin weights instead
  of one influence per vertex, and keeps the height, tier, socket and simulation checks. The build passes and
  `OPENYAMM_REGRESSION_FILTER=mm8_crystal_walker ./build/game/openyamm --world mm8 --headless-run-regression-suite
  actors` passes (`review/regression.log`).

In-game captures of the installed model:
- Taken with `scripts/ingame_prepare.py v7` and `RUNS="out_walker in_walker out_attack" scripts/ingame_run.sh v7`:
  isolated `tools/run_game.sh` runs, a hard-linked assets fixture (deleted afterwards), and the same cameras and spawn
  points as before.
- `review/ingame/compare_walker_v7.jpg`: native sprites, the old installed rigid model with its material pass, and
  v2.
- `review/ingame/motion_v7.jpg` and `review/ingame/attack_v7_sheet.jpg`: a hostile tier A walking in and attacking
  the immortal party, frames every 0.4 s.
- The captures of rounds 1-2 (`v2`, `v2b`) are kept for history.

**Rollback:**
1. Copy `work/mm8_m596_source_pre_v2.glb` to a file named `mm8_m596.glb` (for example `work/restore/mm8_m596.glb`,
   as `scripts/capture.sh` does) and install that with `tools/install_model.py <file> --world mm8`.
2. Set the three bindings' strides back to 0.9 / 1.3.
3. Revert the regression case edit (rename and checks).

Bones: 20 since round 2 (the clavicles). The regression case does not check the bone count; sockets and names are
unchanged.

## Spend and records

Meshy: 5 credits (geometry_v1); no rig, texture or animation jobs, because the rig and clips are local. The canonical
record is `creature_3d_progress.json`. No commits.

## Gait rollout (2026-10-31): Sprint

Package [h22](../gait_rollout_20261031/h22/README.md) appended a `Sprint` (0.5625 s, binding stride 3.6977, 6.57 u/s)
for MAW's tier A chase (8.65 u/s, `Run2` played it at x1.83) to the installed source; every other clip, mesh and skin
is unchanged. It is keyed by `../gait_rollout_20261031/h22/scripts/walker_sprint.py`, a one-gait copy of
`scripts/anim_gait2.py` on `work/anim_gait2.blend` (read only), and appended with this project's `scripts/add_clips.py`.
Bindings (`sprint: Sprint`, `sprint_stride_length: 3.6977`) are in the package's `bindings.yml`. Rebuild:
`level_generation/creatures/gait_rollout_20261031/h22/scripts/rebuild.sh m596`. A far-LOD repair or any re-export of
this model must re-graft the Sprint (copy the new source over the package's `work/mm8_m596_pre_gait.glb` and rebuild).
Found there: claw-tip vertices weighted to both hand and shin (159 LOD0 vertices mix arm and leg weights) stretch into
a strand from the forward claw to the rear shin, +21 cm in Walk2, +30 cm in Run2, +43 cm in the Sprint; the fix is a
weight edit here.
