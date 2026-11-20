# MM9 Thrall body (mm9_thrall) — 3D actor, 2026-10-31

MM9 `THRALL.abc` (37 joints, 14 clips, 550 triangles): rows 90 Field Thrall L8 (`MM9 Thrall A`, THRALL1), 91 Thrall L12 (`B`, THRALL2), 92 Thrall Master L18 (`C`, THRALL3). Sturmford places Field Thralls and Thralls.
Humanoid: built on the approved route (MM9 skeleton, MM9 clips, separate head set, five-finger hands). Progress and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_thrall.glb` (`tools/install_model.py --world mm9`), variants `thrall_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, `MM9 Thrall A/B/C`, scale 100, `yaw_offset` -1.570796327, stride walk 1.3 / run 2.28 (planted foot), melee impact 0.733 s (`hattack1`'s Rattack), ranged impact 0.688 s released at `throw_hand` = `Bip01 R Finger1` (MM9's RangeAttack node, true right hand), look `Bip01 Neck, Head`, upper body `Bip01 Spine2` |
| Triangles LOD0/1/2/3 | 9,517 / 4,757 / 1,708 / 564; LOD0: limbs 3,990 (hands about 800 each), torso + skirt + ropes 1,969, head set 3,558 |
| Skeleton | 85 joints: MM9's 37, names and rest rotations unchanged, joints translated (knee, elbow, hip pivots toward the outside of the bend; leg lengths a blend of ours and MM9's) + 30 finger bones + 10 half-rotation helpers (`*_h`) + 8 skirt hinges (`Skirt_*`) |
| Clips (30 fps) | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `hattack1`, AttackRanged `Rattack1`, Hit `wince1`, Death `die1`, Dead; script clips AttackMelee2 `BigAttack`, AttackMelee3 `BigAttack2`, Fidget2, Taunt, Hit2 `wince2`, Death2 `die2` |
| Textures | limbs 2K + 1K normal + 1K ORM + 1K region mask (shared, ramps); torso 2K + 1K normal per tier, 1K ORM shared; head 2K + 1K normal per tier, flat ORM (18 images) |
| Meshy credits | **40 / 40**: body Smart Topology 5, head-only Smart Topology 5, body retexture C, A, B 10 each (backup account, no retries) |

## Tiers (deviation, recorded)
MM9 paints three designs on one mesh, so ramps alone cannot make them: a sleeveless tunic, a half pelt over one shoulder, a bare chest; and three men: an old bald man with white hair and beard, a sandy-haired man with a headband, a dark-haired man.
- **Limbs** (arms, hands, pelvis with shorts, legs, sandals): one set (tier C's paint) + region mask (skin, gear) + ramps fitted to each tier's own paint on the same layout. This is the shared-set rule.
- **Torso + skirt + ropes + collar** and **head**: their own primitive, one colour and one normal image per tier, mapped per LOD through `KHR_materials_variants` (`tier_variants.py`). The seams are under the belt, under the collar and at one ring round each upper arm.
- **Cost:** cooked torso colour 2K BC7 about 4.6 MB each, head colour about 2.8 MB. Total for the model: 35.2 MB, see "Open points".

## Route (`scripts/`)
0. **Sources**: `convert_abc_model.py --scale 0.0256` per skin, `mirror_glb.py` on the source (`source/true/`): true handedness from the start. `Bip01 R Hand` at x -0.462 on a figure facing -Y in Blender, so the anatomical right.
1. **Masters** (Codex): `references_hd/` five views of tier C from MM9 renders, `references_tiers/` the same figure repainted as tiers A and B, `references_head/00_geometry.png` a clay head sculpt (no paint, one solid hair mass). `clean_alpha.py` removes Codex's halo.
2. **Meshy**: body Smart Topology gave a clean mannequin with separate skirt, belt, rope ends, collar, sandals; hands fused. Head-only Smart Topology gave a very good face and a mushroom of hair.
3. **`head_prep.py`**: teeth shell off (MM9 has no jaw bone), hair shrunk onto the skull by a soft cap on its thickness and narrowed to MM9's slab, hairline fed down to the skin so tier A's bald forehead has no ledge, hidden skull removed.
4. **`step_a.sh`** = `fit_thrall.py` (torso centred, left half mirrored, each limb onto MM9's bone direction; arms MM9's length, legs a blend, written as moved joints) and `graft_thrall.py` (trapezius lowered, neck ring cut on a tilted plane, bridged, collar refitted).
5. **`step_b.sh`** = `rig_thrall.py` (bone heat on the skin, rules by part, eight skirt hinges), `graft_hands.py` (posed MPFB hands, 15 bones per side), `wrist_weld.py` (rings zipped by polar angle: `bridge_loops` twisted them).
6. **`quick.sh`** = `helpers_thrall.py`, `reduce_thrall.py`, clips. Gates ran on this first rig.
7. **UVs** `uv_thrall.py`, `uv_torso_fine.py`: three sets. The upload layout is the torso square (side 0.55) and the limbs square (0.45) side by side; the head has its own layout. Never re-run: the paints belong to `work/uv_v2.blend`.
8. **Paint**: three Meshy retextures at 4K on `texturing/thrall_body_upload_v2.glb`. Heads: `head_clay.py` renders our own head, Codex paints those clay views per tier (`references_head/{a,b,c}_*.png`), `project_head.py` projects front, sides, back and top onto the head UVs with a z-buffer; the face comes from the front view alone, the 3/4 views are not used (Honk's doubled irises).
9. **Textures** `textures_all.sh`: crops, grade, `soft_tex.py` (pebble band cut, normals flattened, rope toned from Meshy's yellow to MM9's tan, tier skin tone), `pale_fill.py`, `tier_ramps.py`, `seam_fix.py`.
10. **Runtime** `rebuild.sh [--install]`: `export_thrall.py` (from `work/uv_v3.blend`; skin winding recalculated), `clips_mm9.py`, `half_keys.py`, `skirt_keys.py`, `arm_bump.py`, prepare, LODs, shadow fix, ramps, `tier_variants.py`, floor, winding, viewer. `reweight.py` relaxes weights on the frozen mesh (neck band, shoulders, elbows, thumb base). `bind_actors.py` writes the binding under the flock.

Rebuild after the paid steps: `scripts/textures_all.sh`, then `REV=<rev> scripts/rebuild.sh --install` (project folder; `work/token` holds the lease token). The AO bake and `uv_torso_fine.py` need Blender; `F=... scripts/run.sh` wraps it.

## Checks (final GLB, revision r10)

| Gate | Result |
|---|---|
| Skirt `skirt_gate2.py` (48 fps; a ray from the body axis to each leg vertex, cloth rasterised to azimuth and height so jagged gaps stay open) | **Walking 0/66, Running 0/50**, Standing, Fidget, AttackMelee2, AttackMelee3, Hit, Dead 0; AttackMelee 3/66 0.3 cm, Death 1/98 0.2 cm, AttackRanged 0 (0.1 cm), script clips Fidget2 and Taunt 12 frames 0.6 cm, Hit2 14/73 3.0 cm, Death2 15/130 15.1 cm (last frames of the fall). Before the keys: Walking 66/66 14.2 cm, Running 50/50 29.8 cm |
| Collapse `collapse_gate.py` | table below; not zero |
| Arm and hand, skin only (`NOCLOTH=1 arm_hand_gate.py --outer-only --exact`) | **0 frames over 1 cm in every bound clip.** Script clips: Fidget2 L 5.8 cm 16 frames (he scratches his head: fingers in the hair), Death2 L 6.0 cm 17 frames (hand pressed on the belly). Neither corrected: both are the gesture, and a push moved it away. Finger stretch max 1.84. 15 finger bones per side |
| Arm and hand against the skirt flaps too | **Fails on bound clips:** Walking R 1.6 cm 3 frames, Hit L 4.6 cm 4 frames, Hit R 2.3 cm 1 frame, Death R 2.0 cm 2 frames; script clips Taunt R 3.2 cm 7, Hit2 L 5.0 cm 16, R 5.2 cm 24, Fidget2 R 3.2 cm 4, Death2 L 6.0 cm 23. A hand passes through a loose flap at the hip. First pass Walking L 4.5 cm 3 frames, R 3.9 cm 9, Running L 3.4 cm; the side hinges now yield to the arm (`room()` in `skirt_keys.py`). An arm bump cleared them but failed jitter in 10 clips, so it was dropped; only Hit2 L keeps a bump |
| `jitter_gate.py` against the untouched clips | **0 fails** |
| Head and foot orientation against MM9 (`orient_gate.py`) | foot soles mean under 1.2 deg, max 7.9 (Death2); head mean under 2.4 deg, max 22.8 (Hit2 easing in from Standing), bound clips max 13 (AttackRanged) |
| Arm bone directions against MM9 (`pose_compare.py`, mid-clip) | 3-10 deg in bound clips, from the eases and the small bumps; 19.8 deg in the AttackMelee2 ease-out |
| `detached_parts_audit.py` (24 fps) | 19 components, **0 detached** |
| `flat_shading_check.py` | 0.00 limbs, torso, head |
| `check_winding.py` | 0 inverted closed parts; skin winding recalculated at export after a hole showed at the wrist in close-ups |
| `texture_quality.py` | limbs atlas 60.8 %, spread 1.19, fragments 0.2 %, stretch 1.07; torso 56.2 %, 1.07, 0.6 %, 1.17; head 63.3 %, spread 1.64 (face 1.6x by design), fragments 0.0 %, stretch 1.14 |
| `floor_audit.py --world mm9` | 3 ok: stand -0.1, walk 0, living -0.1, dead 0. The first build sank 4.3 units (legs longer below the knee than MM9's); `--raise` per clip |
| Symmetry | body skin mirrored at the fit (`fit_thrall.py`), so 0 by construction before the limb poses; MM9's own bind is not symmetric (R foot forward, arms unequal), and the skirt, ropes and head are not mirrored |
| Regression `mm9_actor_models_build_every_binding` | PASS on r10: 107 descriptors on 46 models, 0 failed (r8: 101 on 44). Full `actors` suite on r5: passed 192, failed 1 (`out05_event_clearance_completes_from_monster_killed_hook`, "could not load gameplay data", the failure the Guard reported, not a thrall case) |
| `run_creature_review.py check` | 0 console errors |
| In game (`bootcamp.odm`, review root, isolated) | `review/ingame_sheet.png`: three tiers friendly and hostile, attack and hit play |

**Collapse, worst single frame per clip and region** (`review/gates/collapse.txt`, `collapse.json`, 30 fps; seen = faces any camera can see at the clip's worst frame):

| Clip | face-frames | knee L/R | groin L/R | armpit L/R | elbow L/R | neck/head | body | seen |
|---|---|---|---|---|---|---|---|---|
| Standing | 0 | 0/0 | 0/0 | 0/0 | 0/0 | 0 | 0 | 0 |
| Walking | 526 | 2/0 | 0/0 | 1/1 | 0/0 | 3 | 9 | 8 |
| Running | 413 | 4/2 | 0/0 | 5/4 | 0/0 | 8 | 7 | 10 |
| Fidget | 264 | 0/0 | 0/0 | 0/0 | 0/0 | 6 | 3 | 4 |
| Fidget2 | 831 | 0/0 | 0/0 | 8/0 | 12/0 | 9 | 3 | 6 |
| Taunt | 214 | 0/0 | 0/0 | 0/0 | 0/0 | 8 | 3 | 5 |
| AttackMelee | 269 | 0/0 | 0/0 | 0/0 | 0/5 | 13 | 4 | 9 |
| AttackMelee2 | 441 | 2/1 | 0/0 | 0/10 | 0/0 | 33 | 4 | 22 |
| AttackMelee3 | 371 | 0/0 | 0/0 | 0/13 | 0/0 | 9 | 3 | 12 |
| AttackRanged | 213 | 0/0 | 0/0 | 0/13 | 0/0 | 9 | 3 | 11 |
| Hit | 58 | 0/0 | 0/0 | 0/0 | 0/0 | 5 | 2 | 5 |
| Hit2 | 357 | 1/0 | 0/0 | 4/3 | 0/2 | 9 | 7 | 13 |
| Death | 620 | 2/0 | 0/0 | 9/4 | 3/0 | 15 | 4 | 13 |
| Death2 | 1227 | 0/1 | 0/1 | 4/1 | 9/2 | 33 | 5 | 24 |
| Dead | 372 | 0/0 | 0/0 | 0/0 | 0/0 | 9 | 2 | 9 |

First rig (before `reweight.py`, wider neck band, helpers already in): Death2 3,430 face-frames, neck 77, exposed 44; AttackMelee2 neck 60; AttackMelee3 armpit 17.
Not zero: neck/head 33 in AttackMelee2 and Death2 sits at the nape and the jaw under the head's tilt, with 18 faces exposed; armpit R 13 in AttackMelee3 and AttackRanged is the crease under the raised arm, 9 exposed. Close-ups of these poses read clean; the cat lesson says that is not proof.

Sheets (viewer shots, `review/`): `mm9_vs_ours_tiers.png` (MM9 and ours side by side, every tier, front, back, quarter; MM9 is a Blender render with its own light), `mm9_vs_ours_clips.png` (eight clip moments), `sheet_closeups_a.png`, `_b`, `_c` (knees, groin, armpits, elbow, neck, mouth in crouch `AttackMelee2`, `Death` and `Dead`, framed on the joint), `sheet_strips_a_1.png`, `_2`, same for `b` and `c` (all 15 clips, six frames each), `ingame_sheet.png`. Numbers: `review/gates/`.

## Decisions and deviations
- **Handedness**: fixed at the source. MM9's RangeAttack node is `Bip01 R Finger1`, true right hand after the mirror.
- **Hands**: Meshy fused the fingers, so MPFB hands were grafted; hand length fixed at 20.5 cm (`graft_thrall.json`), since the old hand's measure asked for 25. Thumb curl is a share of MM9's mitten thumb (`finger_alias` delta): copying it folded the thumb into a stub and stretched edges 3x.
- **Head**: head-only Meshy model, colour 2K per tier, like Yrsa's and the Mummy's. MM9 has no jaw bone, so the mouth stays closed. Hair is a rigid shell over the skull with a share on `Bip01 Ponytail1` low at the back. Tier A's bald crown is paint on the hair shell, so the crown is a little higher than a real skull.
- **Skirt**: MM9's seven flap bones are not used (keyed, unweighted). Eight hinges at the belt on solved curves, thighs first, arms second. Rope ends ride the skirt.
- **Leg proportions**: Meshy's knee sits higher than MM9's; lengths blended (thigh 0.323 m, calf 0.414 m; MM9 0.373, 0.378), foot turned by yaw only, so the sole stays flat. Pivots at knee, elbow and hip moved toward the outside of the bend.
- **Heads are projections of Codex paints on our own clay**: sharper than a Meshy paint, no credits. Codex drifted a few pixels from the clay; each view was fitted by its silhouette box, and the face comes from the front view alone. 3/4 views were made and not used.
- **Texture sizes**: the cook makes every texture power-of-two, so the first 1792 limbs and heads would have been 1024 in game. All colour is 2048.
- **Look pass** `soft_tex.py`: pebble band cut on skin, normals at 0.45-0.55, rope 0.8 and desaturated, tier skin tone 0.90 / 0.95 / 1.0. MM9 skin median sRGB (0.50, 0.32, 0.17), ours (0.46, 0.29, 0.17) on the limbs before ramps. The viewer's light makes ours read warmer than the MM9 render in the sheet.
- **Wraps**: calf and wrist wraps are paint on the limb, no geometry.
- **Sockets**: no held weapon. MM9's Thrall throws `MM9Knife` from the hand; nothing is drawn in the hand before release, as in MM9.

## Open points
- **Memory: 35.2 MB of cooked textures**, 18 images, about the same as the Mummy's 35.4 MB. Each tier beyond the first costs 9.6 MB (torso colour 4.6 + normal 1.1, head colour 2.75 + normal 1.17). The limbs are shared (4.5 + 1.1 + 0.4 + mask 0.2).
- **Hands through skirt flaps**, numbers above. Hit L 4.6 cm 4 frames is the worst on a bound clip.
- **Arm-ring seam at the shoulder on tiers A and B**: colour matched round the arm by `seam_fix.py`, but the grain differs across the ring, visible from under the arm at about 40 cm in `Dead`.
- **Armpit paint**: underarm faces no master showed are smooth; Tier B's pelt stretches a little under the arm.
- **Forehead**: two faint dimples from the sculpt's hairline remain near the temples; Codex painted over them.
- Fidget2 and Death2 fingers in the hair and belly, as above.

## Not checked
- Sturmford itself, Drangheim, Lindisfarne: the in-game check was `bootcamp.odm`. Sturmford's thralls placed by the map were not seen; indoor light not seen.
- The thrown knife leaving `throw_hand` was not seen by eye, nor the melee contact moment. Sounds not checked.
- LOD1-3 and shadow meshes by eye.
- Motion by eye: `review/playback/*.webm` exist, I read frames and numbers.
- Which script clips any behaviour plays: `baserange.scr` was not traced, so attack2, attack3, death2 are bound as script clips only.
- Loop seams measured by jitter only.
- Android cook (only on request).

User artistic acceptance: "thrall - ok" (2026-10-31)


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_thrall_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_thrall_reduce_claude/before/`.
