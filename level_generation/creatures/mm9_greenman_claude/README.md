# MM9 The Green Man (mm9_greenman) — 3D actor, 2026-11-04

Job 6 of `devdocs/mm9_rework/overnight/FINISH_BRIEF_20261104.md` (one of the four NPCs that were on hold). MM9 `MONSTERS.txt`
row **266 "Green Man"** (GREENMAN.abc, skins greenman.dtx + Greenmanstaff.dtx, GreenMan.scr, BaseName PeasantMale, Scale 1,
L0 / HP 0); the only row naming the model, one skin, no tiers. Route: the approved MM9 humanoid route (MM9 skeleton and MM9
clips, Meshy Smart Topology + 4K retextures on our UVs, MPFB five-finger hands, separate head set), as Sigmund. Progress,
hashes and Meshy receipts: `creature_3d_progress.json`; status `devdocs/mm9_rework/overnight/status/townsfolk_greenman.md`.

## Why a new body
`claude_shared/mm9_meshcmp.py greenman:<38 built humanoid bodies>`: nearest PeasantHOM1 (after the rigid shift head p90 10 cm,
torso 49, arms 36, legs 37 cm), every other body 14-110 cm off; the skeleton matches none. GREENMAN.abc is a 56-joint Bip01 biped
(Bip01 -> Pelvis -> Spine, **five three-joint fingers per hand**, a staff bone `Bone01` under the scene root, a `ButterFly` socket
on the pelvis that no script uses), body split into per-bone pieces plus `greenman.mesh`, 2.48 m to the branch tips with the head
joint at shoulder height (a hunched leaf hood). Its bind pose is a near-T pose (arms 19 deg below horizontal, legs 18 deg apart).

## What MM9 does with him
One DAT object: Frosgard `GreenMan0` (NPC221.scr: BaseWander wandering, Rude -> Druid promotion and quest rewards, voice on Use).
GreenMan.scr's OnDamage never winces. GREENMAN.abc's own clips are **stand, fidget1, fidget2, walk** (no child model). The engine
needs run, attack, hit and death: as for Sigmund, Running, AttackMelee, Hit and Death are the **PeasantMale library's run,
hattack1, wince1, die1 retargeted** onto GREENMAN's skeleton (row BaseName PeasantMale): `scripts/retarget_mm9.py` (world-rotation
copy) with root bases (GREENMAN keys Bip01 at standing height, PeasantMale keeps Spine at the hips), the leg-length ratio 1.654
as the root scale (die1 vertical 1.4), fingers 2-4 following PeasantMale's single finger chain, and the staff bone kept in the
right hand (`follow`). Config `scripts/retarget_pmale.json` (written by `retarget_setup.py`), sheet `review/retarget/sheet_retarget.png`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_greenman.glb` (`tools/install_model.py --world mm9 --name mm9_greenman.glb` from `export/mm9_gm.glb`) |
| Binding | `actors.yml` block `mm9_greenman_claude` (`scripts/bind_actors.py` under the flock): `MM9 266 Green Man`, scale 100, `yaw_offset -1.570796327`, stride walk 1.9 / run 4.6 (`stride.py`: walk 1.73-2.10 m; run 4.5-4.9 m), look `Bip01 Neck, Bip01 Head`, impact 0.5 s; script clips stand, walk, fidget1, fidget2 |
| Rows | `mm9_npc_actor_rows.tsv`: 266 -> 451 (Treant A, the stand-in of `mm9_npc_legacy_replacements.tsv`); tables regenerated |
| Clips (30 fps) | own: Standing stand 2.5, Walking walk 1.33, Fidget fidget1 3.0, Fidget2 fidget2 4.0; retargeted PeasantMale: Running run 1.03, AttackMelee hattack1 1.03, Hit wince1 1.03, Death die1 1.47, Dead |
| Textures | body 2K colour + 1K normal/ORM; head + hands + staff set 2K colour + 1K normal/ORM; one skin, no region mask; specular 0, metallic 0 |
| Meshy credits | **25 / 60**: Smart Topology 5, body 4K retexture 10, head 4K retexture 10 (backup 2275 -> 2250) |

## Route (scripts/, repo root unless noted; Blender always through `scripts/bl.sh`, memory-capped 12G)
0. Sources: `convert_abc_model.py --scale 0.0256` (GREENMAN.abc with both skins) -> `source/mm9/greenman.glb`; PeasantMale library
   `source/mm9_lib/pmale.glb` (copied from mm9_sigmund_claude). Renders `ref_renders.py` (bind pose, staff hidden), `input_sheets.py`.
1. Codex (`codex_slot.sh`): `codex_masters.sh 1` + `codex_master_1b.sh` (run 1b: the arms raised to the near-T bind pose; run 1's
   return kept in `references_hd/run1_first/`) + `codex_masters.sh 2`; `clean_alpha.py 200`; head turnaround `codex_head.sh`
   (calm, warm, kind face); staff bark swatch `codex_staff.sh` -> `references_staff/staff_bark.png`.
2. Meshy Smart Topology 15k from `00_three_quarter.png` -> `sym_meshy.py` (`HEADF=0.82`; Meshy's legs stood 11 cm apart in depth)
   -> `fit_rig.py fit_config.json` (`mm9_join_except`: the per-bone pieces joined; `scale_ref_z`: scale from the arm underside
   height, 2.62 m to the crown tips; `leg_centroid`; `joint_set`: Neck/Head pivots moved up to our neck (z 0.83/0.93 in the bind;
   MM9's 0.75/0.79 would turn the head from the chest), clavicles kept) -> `reduce_uv.py` (15.5k -> 9.6k) -> `sym_rigged.py` ->
   `graft_hands.py graft_gm.json` (MPFB hands aligned to MM9's hand frame: `hand_dir_joint` = the middle finger root; each MPFB
   finger bone takes the rest frame of the matching MM9 finger bone) -> `head_split.py head_gm.json` (`part_box`: beard leaves into
   the head set, shoulder mantle leaves stay in the body set) -> `eye_fill.py 236,248` -> `drop_parts.py 236,248` ->
   `cuff_trim.py -0.02` -> `triangulate.py` -> `wrist_blend.py` (forearm rim tapered onto the stub) = `work/wrist_v1.blend`.
3. UVs (never re-run): `texpass_uv.py` (body 55.4 %) -> `relayout_head_sig.py` (`FACEBOX=0.085,-0.12,0.88,1.08`, face one chart).
4. Paint: retextures `requests/retexture_body_tp.json`, `retexture_head_tp.json`; `bake_ao_texpass.py`, `compose_texpass.py gm_tp`,
   gentle grade (`--saturation 0.95`), `bake_hands.py`, `skin_ref.py` (green forearm texels as the hand reference), then
   **`scripts/paint_chain.sh`**: `compose_headhand.py --ref-texels --hand-gain 1.12`, `leaf_tone.py`, `face_lines.py`,
   `leaf_jitter.py`, `wrist_vine.py`, `staff_paint.py`.
5. Geometry after UVs: `staff_build.py <texpass_head> <mm9 glb> work/staff_v3.blend 0.45` (the staff tube, 2.9 cm radius, a
   worn knot-free grip, head-set strip UVs, 100 % Bone01) -> `midline_weld.py` -> `accessory_weights.py 120 15` (every small
   leaf part takes the weights of the skin under it; hands and the staff excluded) = **`work/final_v1.blend`** -> `drop_floaters.py 6 0.01` (17 tiny Meshy slivers floating 1.1-2.8 cm off any surface in the bind pose) = **`work/final_v2.blend`**.
6. Runtime `TOKEN=<lease> BLEND=work/final_v2.blend scripts/build_runtime_gm.sh [--install]`: export, `clips_mm9.py roles_gm.json`
   (`source_offset` Bip01 1.2741; R fingers 85/60 % of MM9's curl), `staff_follow.py --offset 0.047,-0.020,0.019` (solved with
   `grip_solve.py`), `arm_const.py` (`arm_const_gm.txt`), prepare, LODs, shadow fix, extras,
   `death_ground.py`, `floor_fix.py` (`floor_ops_gm.txt`), `drop_lod_slivers.py`, `mirror_glb.py`, `fix_winding.py`, winding.
   Viewer `python3 scripts/make_viewer_manifest.py <rev> "gm=Green Man (row 266)=export/mm9_gm.glb"` (the viewer's focus heights
   are set for a 2.6 m figure in `review/viewer/review.js`). Gates `bash scripts/gates.sh` (project folder) and
   `scripts/see_through_gate.py`.
7. Binding: `flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
   level_generation/creatures/mm9_greenman_claude/scripts/bind_actors.py && python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py'`.

## Face (the user reviews it close)
Codex head turnaround: a calm, warm, kind and wise face with a faint smile, amber-green eyes, a leaf moustache and beard in
a leaf hood (MM9's face is the same yellow-green bearded man under a hood of leaves). The Meshy head retexture painted it well:
eyes open with irises, one brow per eye, one nose with two soft nostrils, closed lips in one shape under the moustache.
Fixed in paint (`paint_chain.sh`): two straight hair-thin dark lines Meshy drew across the face chart (left temple -> chin, left
eye corner -> nose; `face_lines.py`, fitted and replaced by the texels either side); the Rorschach mirror pattern on the back of
the hood (the body is symmetrised: twin leaves painted alike; `leaf_jitter.py` varies each leaf's tone). Geometry: Meshy's eyeball
cups dropped after filling the sockets (`eye_fill.py`, before the paint); `midline_weld.py` after the paint welds sub-millimetre
mirror-seam vertex pairs (77 needle faces), positions moved < 1 mm, no reshaping. The mouth slit is a 5-vertex hole the export
fills (`fill_holes_max_edges 8`).

## Checks (final build `export/mm9_gm.glb` = installed `assets_source/worlds/mm9/models/mm9_greenman.glb` sha256 9f1a7c7bb473..., `review/gates/`)
| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only --exclude-joints Bone01`, 48 fps) | 0 frames > 1 cm in every clip, both hands, **except Fidget2 L 6.0 cm (64 frames: MM9's hand strokes the beard; it sinks into the leaf beard, not the face)** and AttackMelee/Hit/Death L 1.9 cm at frame 0 only (the Standing ease pose). Before: Standing L 3.9 cm (121 f, the hand in the leaf kilt) -> 0 (5 deg constant abduction); R hand 4.3-4.9 cm in every clip (it counted the staff) -> 0. Finger stretch p99 <= 1.88, max 4.45 (Fidget2 L) |
| Staff grip (`--only-joints Bone01`) | R fingers 2.1-2.6 cm into the staff in every clip (was 4.2-4.9 cm with the 5 cm MM9-thick staff): MM9's curl is a tight fist; the staff sits in it (`review/grip_r3/sheet.png`) |
| Jitter (`jitter_gate.py` vs the clips before the floor pass) | 0 fails apart from Death (20.9 mm/f2 shoulder skin vs the retargeted fall, whose root sank 0.51 m under the floor: re-grounded by `death_ground.py`); **Death against the grounded clip: 0 fails**. Walking passes with `--raise Walking --smooth-loop Walking 0.10` (ground-loop: 2.6-4 mm/f2 fails) |
| Floor (`floor_audit.py --world mm9 --match 'MM9 266*'`) | stand 0.0, living -0.5, dead 0.0; **walk -0.3..+8.3 units: FAIL (tolerance 2.5)**: our feet are longer than MM9's and sit 10 cm further forward, so MM9's walk drove the toes 10 cm through the floor at every push-off; raising those keys (smoothed) leaves a short 8 cm all-feet-off moment. A foot-pitch fix (`foot_pitch.py`) could not clear it (the ankle itself is too low then) |
| See-through (`see_through_gate.py`, 3 mm px, 16 views) | r2 (step 6, all clips): sleeve R 646 px, L 506, trousers 505/491, torso 408, head 133 (holes Meshy left in the body shell under the kilt and the mantle) -> export hole fill up to 20 edges -> r3 (step 8; Standing, Walking, Running, Fidget, Death): sleeve R 178 (Fidget, side), L 113, trousers 94/70, torso 67, head 45, staff 1: thin slivers at leaf edges seen edge-on (`review/gates/see_through_r3_sheet.png`) |
| Detached (`detached_parts_audit.py --fps 6`) | 87 of 606 parts detached in some pose (was 116 of 617 before `accessory_weights.py` + `drop_floaters.py`): all leaf cards and slivers; 39 over 1 cm, 9 over 2 cm, worst 4.4 cm (a 2-triangle sliver already 4.4 cm off in the bind pose), the rest 2-3 cm leaves lifting off the mantle/beard in Fidget2, Running and Death. **Not 0** |
| Winding / bones / flat | 0 inverted (after `fix_winding.py`: 96 thin closed leaves turned outward); thighs 19-25 % in Fidget/Fidget2 = MM9's own hip slide (fidget1 moves the L thigh joint up to 10 cm); flat 0.02 both materials |
| Texture quality | body atlas **55.2 %**, spread 1.1, stretch p90 1.09, fragments 18.9 % (the leaves are small separate cards); head set 49.8 %, spread 1.73 (hands at half density by design, face 1.4x), fragments 33.7 % (leaves), stretch p90 4.99 (the staff strip and the export's hole-fill patches) |
| LOD0 / LODs | 12,552 / 6,031 / 1,861 / 725 triangles |
| Viewer (`run_creature_review.py check`) | 9 clip switches, 0 failed, 0 console errors (final-20261104b) |
| Regression `mm9_actor_models_build_every_binding` | **PASS** (252 descriptors on 114 models, 0 failed; `review/gates/regression_binding.log`) |

## Sheets read
`review/sheet_faces_final.png` (MM9 head views; ours front close-up, 3/4, true profile, low 3/4, party, both sides; EEVEE
viewer-like light), `review/sheet_viewer_final.png` (viewer: head front/3-4/left/back, body front/3-4/back/rear, Walking 4 frames),
`review/sheet_body_vs_mm9.png` (MM9 stand vs ours), `review/sheet_viewer_final_b.png` (the final install), `review/strip_r1/sheet.png` (every clip, front and side), `review/grip_r3/sheet.png`,
`review/faces_r1/nose_sheet.png`, `review/face_chart_zoom5.png` (the face lines before/after), `review/hands/v5_sheet.png`,
`review/head_sel.png`, `review/xray_v3.png`, `review/retarget/sheet_retarget.png`, `review/masters_check.png`, `review/head_check.png`,
`review/gates/see_through_r2_sheet.png`, `review/gates/see_through_r3_sheet.png`.
Viewer: `http://127.0.0.1:8912/level_generation/creatures/mm9_greenman_claude/review/viewer/index.html`.

## Binding plan (map placement)
Frosgard's `GreenMan0` is placed with the legacy stand-in 451 (Treant A) through `transcode_mm9_dat_to_odm.py`, so descriptor 9266
does not show in game yet; the switch for every row is the orchestrator's (TOWNSFOLK_BRIEF "Lessons from wave 1").

## Deviations and open points
- **Walk floor**: +8.3 units all-feet-off moment per step (floor audit fails; see Checks). Fixing it properly means shortening our
  feet or re-fitting the ankles to MM9's sole height.
- Running, AttackMelee, Hit and Death are retargeted PeasantMale clips (GREENMAN.abc has none); fingers 2-4 follow PeasantMale's
  single finger chain there. The `ButterFly` socket (no script uses it) and MM9's OnDamage "no wince" are not reproduced.
- Proportions: our Meshy body has shorter arms than MM9's (arm scale 0.80) and the head on a neck 13 cm higher (Neck/Head pivots
  moved there); the branch crown has nine branches (MM9 five), from the Codex masters.
- The staff is 2.9 cm in radius (MM9's is thicker) so the fist closes on it; bark from a Codex swatch, not MM9's 64 px skin.
- Twisted-vine bracelets at both wrists are an addition (they hide the hand-graft seam on the bare forearms).
- The back of the leaf hood still reads faintly mirror-symmetric at close range (per-leaf jitter softened it).
- `midline_weld.py` ran after the head paint (sub-millimetre welds on the mirror seam; no reshaping of the face).
- Not looked at in game (no map spawns the descriptor yet); LOD1-3 and shadow meshes not looked at; motion judged on strips,
  gates and four viewer walk frames, not watched at speed; the see-through r3 run sampled 5 clips at every 8th frame; sounds.

## Pass 2 (orchestrator pre-screen, 2026-11-04 afternoon; no credits) - current
1. **Walk hop, fixed at the cause.** fit_rig.py had put our knee 4.8 cm behind and our ankle 9.6 cm in front of MM9's (our Meshy legs
   are straight; MM9's bind leg has the knee forward and the ankle back). With MM9's rest rotations the ankle's forward offset swung
   down when the knee bent and drove the toes 10 cm through the floor. `leg_align.py` moves each leg's mesh in depth by a height
   field (0 at the hip, -4.8 cm at the knee, +9.6 cm at the ankle and below, times the leg-bone weight; kilt leaves on the pelvis stay)
   and the Calf/Foot/Toe0 joints by the same amounts, onto MM9's knee/ankle line. The walk's own lowest point is now -1.8..+1.7 cm
   with no floor operation at all (was -10.3..+2.2): `floor_ops_gm.txt` no longer touches Walking or Running (the run keeps its own
   flight; contact within 1.8 cm). Floor audit **ok** (walk -1.9..+1.7, tolerance 2.5); jitter Walking/Running **0**.
   Sheet `review/sheet_walk_pass2.png` (viewer, side, 4 frames, pass 1 vs pass 2).
2. **Leaves ride the skin.** `drop_slivers.py 5 0.008 5` (43 Meshy scraps of <= 5 triangles floating > 8 mm off every larger part),
   `leaf_weights.py` (every small part, per vertex, the barycentric-interpolated weights of the nearest body/head-shell face; a
   root-rigid variant, `RIGID_MAXT`, was worse: 41 parts > 1 cm), replacing `accessory_weights.py`/`drop_floaters.py`.
   Result: see Checks below.
3. **Colour toward MM9** (`colour_mm9.py`, last in `paint_chain.sh`): skin v x0.74, s x0.86, hue toward olive; leaves hue toward
   MM9's moss (0.27), s x0.70, v x0.80 (head-set leaves x0.74); bark (branches, wrist vines) v x0.78; the staff strip and the eyes
   left out. Body texture mean 74/84/28 -> 59/68/30, head 79/101/23 -> 60/72/31. Sheets `review/sheet_colour_pass2.png`
   (viewer, MM9 vs pass 1 vs pass 2), `review/sheet_faces_pass2.png` (EEVEE face sheet + full body).
4. **Lilac specks** beside the neck: `blue_specks.py` now heals each blob grown 7 px from the median of the ring round it (pass 1's
   nearest-texel fill had copied the blob's own halo and left a grey-white dot). `review/lilac_sheet.png` (texture crop before/after),
   `review/zoom_hl_pass2.png`.
Master now **`work/legs_v3.blend`** (`final_v2` -> `leg_align.py` = legs_v1 -> `drop_slivers.py` = legs_v1s -> `leaf_weights.py`).

### Pass 2 checks (final install `assets_source/worlds/mm9/models/mm9_greenman.glb`, sha256 72e57b0e741c..., viewer pass2-final-20261104)
| Gate | Pass 1 -> pass 2 |
|---|---|
| Floor audit | walk -0.3..+8.3 units FAIL -> **-1.9..+1.7 ok**; stand 0, living -1.9, dead 0 |
| Jitter | Walking/Running **0 fails** (no floor operation on either clip now); only Death vs the ungrounded retarget (20.8 mm/f2), 0 against the grounded clip |
| Detached (`--fps 6`) | 87 parts / 39 over 1 cm / worst 4.4 cm -> **71 / 16 over 1 cm / worst 3.0 cm. Not 0**: one 5-triangle scrap 3.0 cm off already in the bind pose (sits on another leaf, so `drop_slivers.py` kept it), two 1-triangle scraps 2.4 cm (Fidget, Walking), the rest 4-14 triangle chest/neck leaves 1.3-2.2 cm in single frames of Fidget, Fidget2, Running, Death |
| Arm/hand, grip, winding, flat | unchanged (arm 0 except Fidget2 L 6.0 cm beard stroke, one-shot frame 0 at 2.2 cm; grip 2.1-2.6 cm; 0 inverted; flat 0.02) |
| Texture quality | body 55.1 %, head set 49.4 % (drop of slivers), as before otherwise |
| LOD0 | 12,490 triangles |
| Regression `mm9_actor_models_build_every_binding` | **PASS** (252 descriptors on 114 models) |
| Viewer check | 9 switches, 0 failed, 0 console errors |
Sheets read (pass 2): `review/sheet_walk_pass2.png`, `review/sheet_colour_pass2.png`, `review/sheet_faces_pass2.png`, `review/sheet_head_pass2.png`,
`review/sheet_head_pass2c.png` (leaves in the worst frames), `review/sheet_pass2_final.png`, `review/lilac_sheet.png`, `review/zoom_hl_pass2.png`.


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_greenman_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_greenman_reduce_claude/before/`.
