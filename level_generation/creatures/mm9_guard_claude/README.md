# MM9 Guard family (mm9_guard) — 3D actor, 2026-10-30

MM9's halberd guards for the MM9 world: Guard L11 (`MONSTERS.txt` 111, `MM9 Guard A`, GUARD1), Guard Segeant L19 (112, `MM9 Guard B`, GUARD2), Guard Captain L33 (113, `MM9 Guard C`, GUARD3); body `GUARD.abc`, 35 joints, 20 clips, weapon skins GUARDPOLE (A, B) and GUARDPOLE2 (C). Waited for by the Drangheim Prison stand-ins. Built on the approved Yrsa route (MM9 skeleton, MM9 clips, grafted hands, a separate head set). Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLBs | `assets_source/worlds/mm9/models/mm9_guard.glb`, attachments `mm9_guard_halberd.glb` (A, B), `mm9_guard_halberd2.glb` (C), `tools/install_model.py --world mm9` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `mm9_guard_claude`: `scale: 100` (MONSTERS Scale 1), `yaw_offset: -1.570796327`, stride walk 1.3 / run 3.4, look `Bip01 Neck, Bip01 Head`, impact 0.456 s (Hattack1 `Rattack`), `attack_ranged` = AttackMelee2, 0.497 s (the engine requires the key; the rows are melee), halberd on `Xbase` |
| Triangles LOD0/1/2/3 | 11,904 / 5,950 / 2,136 / 703 with the halberd (418 / 208 / 74 / 22), pass 1 was 12,488; of LOD0: dark linings two rings from each rim, 1,600 hands |
| Skeleton | GUARD.abc, 35 joints, names and rest rotations unchanged, joints translated, + 15 finger bones per side + 6 hinges `Skirt_*` + 8 half-joint helpers `Bip01 <side> UpperArm_H`, `Forearm_H`, `Thigh_H`, `Calf_H` |
| Clips (30 fps) | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `Hattack1`, AttackRanged slot = AttackMelee2 `Hattack2`, Hit `wince1`, Death `die1`, Dead; script clips Fidget2, Hit2 `wince2`, Taunt, Cower (`cowerstart` + `cower` + `cowerend`), Backpedal |
| Textures | body 2K colour + 1K normal/ORM per tier, head sets 2K + 1K + 1K (leather; steel for B and C), one 1K region mask, halberds 2048x512 (procedural) |
| Meshy credits | **35 / 40**: Smart Topology 5, body A 10, body C 10, two-head job 10 (backup account) |

## Deviation: per-tier images (coordinator's note, 2026-10-30)

The rule is one shared set, region mask and colour ramps. This body breaks it where the MM9 skins differ in **design, not colour**: GUARD1 is quilted leather and cloth, GUARD2 chain with a leather mantle, GUARD3 chain, steel plates, greaves and gauntlets. Their patterns, relief and painted plate outlines cannot come from one image by a luminance ramp.

- **Kept as a ramp:** the one colour-only difference, the Sergeant's brown mantle: tier A's own leather and cloth texels in `guard_b_final.png`, plus `guard_b_region_mask.png` (R) and a 16-stop ramp from the GUARD2 skin's leather (`textures/guard_b_ramp.json`).
- **Per tier:** body colour, normal and ORM (A, B, C); head set (leather A, steel B and C, shared); halberd (MM9 has two skins, so two attachments). B has no paint of its own, it is composed from A and C (`scripts/compose_tier_b.py`).
- **Extra memory:** cooked textures 30.0 MB for the body GLB (BC7 + normals), against 13.1 MB for the Skeleton Warrior and 10.5 MB for the Imp, so about 15-18 MB more than a shared-set body. **All variants upload:** `ModelRenderer` builds textures for every material in the asset, not for the skins on the map. Measured with only tier A spawned: `texture_bytes` 389.3 -> 430.1 MB, +40.8 MB of GPU memory (pass 2, previous build; the images did not change since).
- **Runtime binds them per tier:** `actors.yml` skins `guard_a/b/c` select `KHR_materials_variants`; the cooked GLB has six materials, `Guard_A/B/C` on different images and `GuardHead_B/C` on the same one; `review/ingame_sheet.png` shows the three tiers side by side in game with their own armour, and the Captain with the dark halberd.

## Route (scripts/)

0. **Masters** (Codex through `claude_shared/codex_slot.sh`, `scripts/codex_run.sh`): `references_hd/` five tier A views, four tier C views; `references_head/` four views of each helmet on one head. Inputs: renders of the MM9 model and skins. The halberd master was refused by the image tool's safety filter; see Halberd.
1. **Meshy** Smart Topology 15k (`requests/smart_topology_v1.json`).
2. **Clean** (`clean_guard.py`): height scale, each central piece on its own mid-plane (up to 1 cm off), figure's right half kept and mirrored (MM9 is exactly symmetric; Meshy's other collar edge is jagged), pin holes and seam slits closed, per-garment reduction with joints protected, eyeball cups dropped.
3. **Fit** (`fit_guard.py`, `fit_guard.json`): joint estimates on the mesh (MM9's knee sits 7 cm low here), FK with MM9's directions and our lengths, mesh posed by a transient skin (rotations under 5 deg, hand 19).
4. **Weights** (`rig_guard.py`): structural bands, chin-nape plane (chin all Head), pieces rigid or copied from the skin under them, skirt on six hinges.
5. **Hands** (`graft_hands.py`, `graft_guard.json`): five-finger MPFB hands grafted before the UVs, so Meshy paints them as gloves; 15 finger bones; left hand follows MM9's curl by `finger_alias`.
6. **UVs** (`uv_guard.py`): never re-run, the paints belong to this layout.
7. **Paint**: `compose_guard.py` (body), `project_heads.py` (heads, see below), gentle grade, `compose_tier_b.py`.
8. **Finish** (`finish_guard.py`): dark rim linings, hidden faces out, shoulder fans, halberd, fist solved round the shaft, half-joint helpers. **Clips**: `clips_mm9.py`, `finger_keys.py`, `helper_keys.py`, `skirt_keys.py`, `hand_rest.py` (`hand_rest_guard.txt`), `pole_clear.py`, `dead_hold.py`.
9. **Runtime** (`build_runtime.sh [--install]`): prepare, LODs, shadow fix, halberd split, `tier_materials.py`, floor, winding. Viewer: `viewer_tiers.py`, `make_viewer_manifest.py`. Binding: `bind_actors.py` under the flock.

Rebuild after the paid steps: `TOKEN=<lease> scripts/build_runtime.sh --install` (project folder), then the viewer scripts. `scripts/rebuild_mesh.sh` replays the mesh chain up to the hands; never after the upload went to Meshy.

## Handedness

`scripts/mirror_source.py` (from the Skeleton Warrior's, weapon chain `Xbase` > `Xmid` added) writes `source/g*/guard*_true.glb`. `scripts/handedness.py`: raw `R Hand` x +0.664, the anatomical LEFT, weapon there; true `R Hand` x -0.664, anatomical RIGHT, weapon there. The left-hand gestures moved with it.

## Skirt

The tunic's lower part is a closed double-walled ring under the belt. Six hinges at the belt, weighted round the ring and by height; `skirt_keys.py` solves the least swing per key in the Spine frame and filters it (running maximum 0.05 s, Gaussian 0.035 s, twice that on one-shots, circular on loops); neighbours take 0.62 of each other, which keeps the ring together. Gate in Checks.

## Heads: why projected

The budget allowed one head job for two helmets, so the upload held two heads on opposite corners and the references were composites. It failed: Meshy crossed the heads between its views, the steel helmet lost its eye mask and took the lion badge. No credits for a second job. `project_heads.py` projects the Codex views directly into the head UVs (angle-weighted, helmet and skin masks by garment); relief comes from the colour's luminance. Sharper than any paint here, but: the top of the helmet is seen only at grazing angles, and tier A has 23 % of its head texels unseen (inner and hidden faces, filled from the nearest point).

## Halberd

Codex's image tool refused the prompt with a `violence` flag (`references_prop/raw/head_a_1_error.json`). No rewording was tried. `make_halberd.py` takes the outline from MM9's own pole vertices and paints both poles procedurally (0 credits, 418 triangles). It reads plainer than the Codex-painted body. Rigid on `Xbase`, tilted 4 deg in the fist in every clip, so the butt stands clear of the right boot (it stood 1.9 cm inside the toe in Standing).

## Second pass (2026-10-31)

Coordinator's seven points, 0 credits. **Credits stay 35 / 40.**

1. **Fist.** Pass 1 solved on the wrong chains (bone tails follow MM9's mitten frames, not the fingers). Now on the chains in `work/hands_v1.json`; a finger cannot close on a shaft 26 deg off its knuckle line, so the hand takes a constant 25.7 deg wrist turn (`hand_offset`, applied by `finger_keys.py`) and the pole is built turned back in the hand frame, so it points where MM9's does, plus a 4 deg tilt. Clearance 5 mm (`want`), palm 4 mm, thumb closes over the middle finger on the far side. `scripts/grip_gate.py` per clip, finger skin inside the shaft: 0.1 cm (10 vertex samples of 5 clip times) in 13 clips, **Running 0.5 cm** (MM9's keyed `Xbase` slides in the run). Wrap at the shaft: Thumb 90-135, Index 135-165, Middle 180-195, Ring 135-165 deg. `review/close_hands.png`: a fist round the shaft; `ahB_1` still shows one speck and one sliver of the thenar pad on the white shaft (it is seen from the palm side; the pad was left against the shaft on purpose).
2. **Collapse.** Eight half-joint helpers on shoulders, elbows, hips and knees, keyed at half the joint rotation (`helper_keys.py`); blend band torso -> helper -> limb, smoothed three passes. Table below.
3. **Corpse and arms.** `hand_rest.py --normal-dir` (push along the surface normal under the hand) for Death; Dead is now Death's last key on every channel (`dead_hold.py`); `pole_clear.py` rotates the halberd about the fist in Death and AttackMelee, capped at 8 deg; `--smooth Death 0.11` in `floor_ops.txt` cured the jitter. AttackMelee2's left hand turned out to meet the **right forearm**, not the belly: the forearm now counts as body in that line (`--body-extra`).
4. **White fleck.** The grey background seen through a 19-edge opening between the shoulder cap and the sleeve, a hole in Meshy's shell that the bind pose hides. Closed with a dark fan on both sides. Re-shot (`review/final/ca/AttackMelee5_3.png`, `cc/`): gone.
5. **Tone.** MM9's skin tunic is (71, 29, 16), the paint was (142, 59, 14). `compose_tier_b.py`: tier A gain .72, saturation .92; helmet gain .7; tier C trousers .76, tunic and skirt .9, chain highlights above 95 compressed x.45. Compared in game (`review/ingame_sheet.png`), where A is dark brown-red and the chain tiers are muted. Still about 1.4 x MM9's tunic value by the numbers (102 vs 71 red), left there so the quilting reads in game light; the viewer's lights run brighter than the game.
6. **Reduction.** 12,488 -> 11,904: linings two rings from each rim (was three), 8 hidden faces out (under the belt, inside the trouser top), plus the fans. LOD 5,950 / 2,136 / 703.
7. **Unchecked list.** Tier B strips done (`review/strips_b.png`). Playback done (`review/playback/`, `review/sheet_playback.png`). All variants upload: see the deviation section, +40.8 MB in GPU memory with one tier on the map.

Attempts that were dropped: a left-hand rest in AttackMelee (hand against hip and skirt, 3.2 cm, 10 frames): every setting failed the jitter gate (5.6-13.6 mm/f2 shoulder skin). A stronger push in AttackMelee2 (sigma .08) reached 3.3 cm but failed jitter at 2.29; the kept setting is 4.0 cm, jitter clean.

## Checks

Final build, pass 2 viewer `v14-20261031`; third-pass numbers in the section above. Gate outputs: `review/gates/`; pass 1's: `review/gates_v1/`.

| Gate | Pass 1 | Pass 2 |
|---|---|---|
| Handedness (`handedness.py`) | weapon on the anatomical right | unchanged |
| `skirt_gate.py` Walking | 0/49 | **0/49** |
| `skirt_gate.py` Running | 0/25 | **0/25** (per-clip margin 6.2 cm: the helper band fills the thigh there, 3/25 1.1 cm before it) |
| `skirt_gate.py` Cower | 49/125, 1.9 cm | 36/125, 1.2 cm |
| `skirt_gate.py` other clips, Death included | 0 | 0 |
| `arm_hand_gate.py` Death L / Dead L | 6.0 / 6.0 cm | **1.0 / 0.3** |
| Same, Death R / Dead R | 1.6 / 1.2 | 1.3 (2 frames) / 0 |
| Same, Cower R | 2.6 | 0.7 |
| Same, AttackMelee2 L | 4.7 (4 frames) | **4.0 (3 frames), open** |
| Same, AttackMelee L | 2.6 (6 frames) | **3.2 (10 frames), worse, open** |
| Same, Fidget2 L | 2.1 | 2.4 (51 frames, capped push) |
| `blade_gate.py` Death / Dead | 5.9 / 3.4 cm | **0 / 0** |
| Same, AttackMelee / AttackMelee2 / Cower | 1.6 / 1.4 / 0.6 | 0.9 / 1.4 (4 frames, left hand) / 0 |
| `jitter_gate.py` against MM9 | 2 fails, Death 2.18 mm/f2 | **0 fails** |
| `detached_parts_audit.py` | 0 of 30 | 0 of 30 |
| `flat_shading_check.py` | 0.00 | 0.00 |
| `check_winding.py` | 0 inverted | 0 inverted, three GLBs |
| `texture_quality.py` | body 57.4 %, head 57.8 % | same |
| `floor_audit.py --world mm9 --match 'MM9 Guard*'` | 3/3 ok | 3/3 ok: stand +0.1, walk -0.7..+0.9, living -2.1, dead 0 |
| `run_creature_review.py check` | 42 switches, 0 errors | 42 switches, 0 errors, 0 failed |
| In game (`bootcamp.odm`, review root) | ok | `review/ingame_sheet.png`: three tiers, hostile, death, corpse |

Collapse gate, faces collapsed below 20 % of their rest area or flipped, worst single frame (pass 1 -> pass 2):

| Clip | Armpit L | Armpit R | Elbow R | Groin + hem | Knee | Head | Hand R | Face-frames | Exposed |
|---|---|---|---|---|---|---|---|---|---|
| Standing | 1 -> 0 | 0 -> 1 | 0 -> 0 | 4 -> 1 | 0 -> 0 | 0 -> 0 | 18 -> 4 | 1,164 -> 280 | 10 -> 5 |
| Walking | 1 -> 0 | 0 -> 0 | 0 -> 0 | 5 -> 2 | 2 -> 0 | 0 -> 0 | 18 -> 3 | 718 -> 156 | 13 -> 6 |
| Running | 24 -> 14 | 24 -> 11 | 0 -> 0 | 20 -> 7 | 8 -> 4 | 1 -> 0 | 18 -> 3 | 764 -> 238 | 34 -> 16 |
| Fidget | 2 -> 0 | 4 -> 3 | 0 -> 1 | 4 -> 1 | 0 -> 0 | 1 -> 0 | 18 -> 4 | 1,412 -> 366 | 12 -> 6 |
| Fidget2 | 5 -> 0 | 19 -> 16 | 1 -> 0 | 4 -> 1 | 0 -> 0 | 0 -> 0 | 18 -> 4 | 1,940 -> 504 | 16 -> 10 |
| Taunt | 8 -> 6 | 17 -> 11 | 0 -> 0 | 4 -> 1 | 0 -> 0 | 1 -> 0 | 18 -> 4 | 1,157 -> 299 | 19 -> 19 |
| AttackMelee | 53 -> 51 | 41 -> 30 | 12 -> 8 | 5 -> 2 | 0 -> 0 | 15 -> 0 | 27 -> 11 | 1,943 -> 838 | 34 -> 19 |
| AttackMelee2 | 39 -> 27 | 58 -> 49 | 6 -> 5 | 11 -> 3 | 0 -> 0 | 10 -> 1 | 21 -> 6 | 2,341 -> 1,235 | 22 -> 19 |
| Hit | 7 -> 3 | 10 -> 4 | 0 -> 0 | 4 -> 1 | 0 -> 0 | 0 -> 0 | 18 -> 4 | 682 -> 166 | 14 -> 6 |
| Hit2 | 7 -> 2 | 5 -> 2 | 0 -> 0 | 4 -> 2 | 0 -> 0 | 2 -> 0 | 18 -> 4 | 669 -> 150 | 12 -> 6 |
| Cower | 51 -> 25 | 35 -> 8 | 9 -> 5 | 17 -> 6 | 2 -> 1 | 0 -> 0 | 19 -> 5 | 6,168 -> 2,438 | 44 -> 31 |
| Backpedal | 1 -> 0 | 0 -> 0 | 0 -> 0 | 5 -> 2 | 2 -> 0 | 0 -> 0 | 18 -> 3 | 787 -> 170 | 12 -> 6 |
| Death | 15 -> 4 | 42 -> 20 | 3 -> 0 | 21 -> 6 | 7 -> 3 | 14 -> 7 | 18 -> 5 | 3,248 -> 1,078 | 28 -> 20 |
| Dead | 14 -> 3 | 3 -> 2 | 0 -> 0 | 8 -> 6 | 0 -> 0 | 8 -> 2 | 18 -> 3 | 1,736 -> 589 | 28 -> 12 |

Where the rest are (`scripts/collapse_where.py`): the armpit counts that remain (AttackMelee L 51, AttackMelee2 R 49) are almost all flips of small faces folded under a raised arm: at their worst frame **2 and 3 of them can be seen by any camera**. Cower L 25 has 14 exposed, the one armpit that can really be seen, in the deep crouch. Death's head 7 is the neck under the rolled head.

Sheets (viewer shots unless noted): `review/sheet_mm9_vs_ours.png` (MM9 is a Blender render with its own camera and framing), `review/sheet_tiers.png`, `review/sheet_closeups_a.png`, `review/sheet_closeups_c.png`, `review/close_hands.png`, `review/strips_a.png`, `review/strips_b.png`, `review/strips_c.png`, `review/sheet_playback.png`, `review/ingame_sheet.png` (engine).

## Third pass (2026-10-31): helmet layers, MM9's other clips

**Cause (user: "parts of 4 eyes").** `project_heads.py` projected all four Codex views through the head with no occlusion test. Its helmet mask was hole-filled, so the face inside the helmet counted as helmet: the side views' eyes landed on the cheek plates, and on tiers B and C (no refusal there) the side views' helmet rivets landed on the throat. The mesh's opening is also one straight slot while the views and MM9 close it to a T and, on steel, an eye mask: that mask was paint on the face, cut by the helmet's edge (the hard vertical edges).

**Fix, 0 credits.**
- `head_masks.py`: face and helmet pixels per view, seeded; the side views' eye window is never helmet.
- `project_heads.py`: helmet texels take a view only where a z-buffer (`head_zbuf.py`) says that side sees them and the pixel is helmet. Skin takes the front view only, filled from the nearest skin, so no helmet can reach the face or neck. A dome of 48 viewpoints gives exposure: hidden skin and the helmet's inside go dark, and tier C's skin behind the plate is darkened by the plate's own mask.
- `make_plate.py`: real geometry, cut from the view's helmet pixels 7 mm off the face. `mm9_guard_plate_a.glb` (cheek returns, 323 tris) and `mm9_guard_plate_c.glb` (eye mask and cheek returns, 456 tris; B and C), a second attachment on `Bip01 Head`. LOD1-3 drop the rim only. 1K colour, 512 normal, 64 ORM.

Sheets at the viewer's own 1036 px, cropped, six views (front, quarter, both sides, back, below): `review/head_a.png`, `review/head_b.png`, `review/head_c.png`. MM9's heads: `references_head/mm9_head_views_a.png`, `_c.png`.

**New clips**, all MM9's, bound in `script_clips`: `sleep: Sleep`, `aware: Aware`, `cower_start: CowerStart`, `cower_end: CowerEnd`, `backpedal_run: BackpedalRun`, `death2: Death2`. **Sleep:** he dozes on his feet, head bowed on the chest, hands at the waist, the halberd upright beside him; the fist stays closed round it.

| Clip | Skirt | L hand | R hand | Halberd in body | Fist in shaft | Collapse worst armpit L / R |
|---|---|---|---|---|---|---|
| Sleep | 0/87 | 1.4 cm (27 frames) | 0 | 0 | 0.1 cm | 9 / 2 |
| Aware | 0/68 | 2.3 (8) | 0 | 0 | 0.1 | 6 / 11 |
| CowerStart | 2/34, 1.1 | 1.1 (3) | 0 after rest | 0 | not separately listed | 25 / 8 |
| CowerEnd | 3/49, 1.3 | 1.1 (1) | 0.5 after rest | 0 | not separately listed | 25 / 8 |
| BackpedalRun | 0/25 | 0 | 0 | 0 | not separately listed | under 3 |
| Death2 | 0/73 | 1.3 (2) | 0 | 0 | 0.1 | 30 / 5 |

Jitter 0 fails after `--smooth Death2 0.11` and `--smooth-loop BackpedalRun 0.05`. Detached 0. Strips `review/strips_a.png`, `_b`, `_c` hold every clip, taken before the last head paint fix. `scripts/pin_pole.py` was added for Sleep and turned out to be a no-op (MM9 does not move `Xbase` there); Sleep's fist reading of 1.6 cm in the first gate run was the pre-fix build.

Final third-pass checks, viewer `v19-20261031`: floor audit 3/3 ok, `check_winding.py` 0 inverted on all five GLBs, viewer check 60 switches 0 failed, regression `actors` passed 192, failed 1 (the same `out05` MM8 case under `--world mm9`), `mm9_actor_models_build_every_binding` PASS with 140 descriptors, 0 failed. The regression and the strips ran before the last texture-only rebuilds; the skeleton, clips and bindings did not change after them, the plate mesh and head paint did.

**Fist not refined** (coordinator, weekly limit): `mm9_highwayman_claude`'s solve is this project's solver, so there was nothing to copy. Wrap 135-195 deg; the thick grafted fingers stop short of curling back round a 3.3 cm shaft.

## Deviations and open points

- **Per-tier images**: see the section above.
- **Fist geometry**: constant 25.7 deg wrist turn and a 4 deg pole tilt against MM9's bones, so the grip closes. The pole's direction stays MM9's within that tilt.
- **Helpers**: eight bones MM9 does not have; skin in the bands follows them, the MM9 joints are unchanged.
- **Skirt**: margin 4.4 cm, 6.2 in Running, 6.0 in Death; the ring rises as one piece in Running.
- **AttackMelee2 left hand**: 4.0 cm into the right forearm, 3 frames at frame 25. MM9's arms are thin enough to pass; ours are not. Reason it stays: more push fails the jitter gate.
- **AttackMelee left hand**: 3.2 cm into hip and skirt, 10 frames, worse than pass 1's 2.6 (the deeper fist and wider skirt). Reason it stays: same, every rest failed jitter.
- **Fidget2's hip rest** stays capped at 8 cm, 2.4 cm in.
- **Running grip**: 0.5 cm, MM9's `Xbase` keys move the pole in the hand.
- **Cower**: thighs through the skirt 36/125 frames, 1.2 cm (the skirt's swing is capped at 68 deg in the deep crouch). The gate is on Walking and Running; Cower is recorded.
- **Tier tone**: A's tunic is still about 1.4 x MM9's value in texture numbers; see point 5.
- **Sergeant**: no paint of its own. Lower-leg chain is the thigh's chain tiled down the leg, gauntlets are the Captain's steel (MM9 paints chain gloves), trim on the mantle reads tan.
- **Heads**: projected by layer (third pass). The crown is stretched near the top in the Codex grazing views; horizontal streaks stay at the cheek plates' front edges; the painted window outline stays on the steel helmet's cheek in side view, with a dark gap in the old eye corner.
- **Plates**: two more attachments, 0.2-0.3 MB cooked each to re-measure, drawn on every guard. Not in the shadow meshes.
- **Halberd**: procedural paint, plainer than the body; reads pale in the viewer. MM9's grip is one-handed, kept.
- **Black wedge** between neck and collar on tier views (`review/close_neck.png`): the collar's dark lining seen from above.
- **attack_ranged** is bound to AttackMelee2 because the engine refuses a descriptor without it; the rows have no ranged attack.
- Regression `--world mm9 --headless-run-regression-suite actors` on the final build: **complete, passed 192, failed 1**, `mm9_actor_models_build_every_binding` PASS. The one failure, `out05_event_clearance_completes_from_monster_killed_hook` ("could not load gameplay data"), logs `world.yml id 'mm8' does not match active world 'mm9'`: an MM8 case under `--world mm9`, not this body. Same case failed in pass 1.
- Not used: MM9's `guardsetup`.
- **Third pass not checked**: the head in game (viewer shots only), the plates at LOD1-3, in-game playback of the new clips, whether any AI state calls `sleep` or `aware` (bound only), Death2's corpse pose against `Dead` (Dead holds Death's end), close-ups of the new clips, plate memory on the GPU.
- **Not checked**: LOD1-3 and shadow meshes by eye; playback videos themselves (their timed frames were read, the `.webm` were not watched); indoors, Drangheim Prison itself (the `save_game` preparation failed on `drangheim.odm` in pass 1, not related to this body, not retried); close-ups for tier B (A and C only); the neck close-ups in Cower and Dead (the arm and tunic hide the camera's target; they show cloth, Running and AttackMelee show the neck); GPU memory on the final build (the images are unchanged since the measurement); the guards in real combat for more than a few swings.


## Dropped MM9 clips restored (2026-10-31, run2-clips-groupB)
The `cower` hold existed only inside the stitched `Cower`. Added `CowerLoop`, bound `cower_loop`. Route as the accepted clips, then `scripts/match_loop.py` seats it on the accepted CowerStart end / CowerEnd start (one constant offset per channel; joins now 0.3 deg), and a second `hand_rest.py` push faded in and out over the loop by `scripts/blend_window.py`: MM9's tremble brought the right fist 3.2 cm into the helmet mid-loop, now 1.0 cm, 0 frames over 1 cm. The halberd attachment was not checked separately (the pose matches the accepted Cower's hold). Built with this project's own clip route in `scripts/extra_clips.sh` (soft joint-offset line now in `clips_mm9.py`), floored, then grafted with `claude_shared/graft_clips.py`: meshes, LODs, variants and the accepted clips are byte for byte (checked: old buffer a prefix of the new, old JSON unchanged). Numbers in `review/gates_extra/`, strip `review/gates_extra/strip_new.png` (numpy raster, untextured). Status: `devdocs/mm9_rework/overnight/status/clips_groupB.md`.

User artistic acceptance: "guard - good" (2026-10-31)


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_guard_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_guard_reduce_claude/before/`.
