# MM8 Lizardman Peasant / Farmer / Villager: full rebuild (rebuild stream, 2026-11-11)

Audit fix ([audit](../audit_mm678_20261111/README.md), brief [REBUILD.md](../audit_mm678_20261111/fixes/REBUILD.md)
row 6), agent `rebuild-2`. The installed model was the last image-to-3D standard body with a Meshy auto-rig, Walk played
once as both attacks, spiky hands and 49 % of its texture surface on specks. Replaced as a whole: mesh, rig, clips,
textures, LODs and binding. Meshy credits **20** (Smart Topology 5, auto-rig for joint estimates 5, 4K body retexture 10).

## Route: MM9 donor skeleton and clips (Yrsa route), MM9 LIZARDORC

- **Masters**: the gated Codex masters of the 2026-10-06 run (`../mm8_m400/3d_20261006/references/`, generated from
  the native m400 bitmaps; playbook quick start 0 allows reuse), copied to `references_hd/00-04` and matted to true
  alpha (`scripts/clean_masters.py`, `*_clean.png`). Identity re-checked against the native standing views of all three
  palettes (`references_hd/native_standing_sheet.png`).
- **Body**: Meshy Smart Topology (15k) from `00_three_quarter_clean.png`: clean four-digit clawed hands (three fingers
  and a thumb, as the masters and the earlier model), fins, teeth, fringes. Placed at 1.70 m (`scripts/estimate.py`).
- **Fit** (`scripts/fit_liz.py`, after `mm6_gua_rebuild_claude/scripts/fit_gua.py`): the MM9 LIZARDORC skeleton (42 nodes,
  names and rest rotations kept), joints translated to estimates from a Meshy auto-rig of our body
  (`scripts/meshy_joints.py`, 5 credits; the slice estimate of `fit_rig.py` missed our A-pose arms) and the centre chain
  read from grid views; each limb laid along MM9's bone directions with our lengths and the mesh posed there by a
  transient skin. MM9's tail, jaw, tongue and cutlass bones carry no weight.
- **Weights** (`scripts/rig_liz.py`, structural): membership by nearest structure (torso chain, neck+head to the snout,
  arm incl. fingers, leg incl. toes); arm and leg bands along the bent limbs; torso by height; a long head ramp along
  neck->head (MM9 bends the neck at the head, lizardorc lesson); fins above the head joint rigid on the head; skirt and
  apron off the leg core fading pelvis -> thigh; 64 small pieces (fringe blades, collar teeth) rigid. Blender heat
  weights were tried first and failed (asymmetric empty pieces, toes on the pelvis).
- **Fingers** (`scripts/fingers_liz.py`): by connectivity (geodesic splits from the wrist ring), grown back to the palm
  along each digit; thumb = the digit based nearest the wrist. Chains `Finger0/01/02` (thumb), `Finger1..3` with two
  more joints each, MM9's Finger1/Finger0 rest frames, driven by MM9's mitten curl through `finger_alias`.
- **Reduce after weighting + UVs** (`scripts/reduce_uv_liz.py`): head 0.8, hands 0.7, body 0.55 -> 9,398 triangles;
  `claude_shared/uv_atlas.py`, head charts x1.8, atlas 55.1 %. Upload `texturing/body_upload_v1.glb`.
- **Paint**: 4K body retexture with the four masters (`requests/retex_body_v1.json`), downsampled once to 2K, gentle grade
  with AO baked on the layout (`scripts/compose_liz.py`). No separate head paint (budget; the 4K paint reads well on the
  head at x1.8 density). Classes by colour + rest position: garment, trim (collar, belt, hem, apron checks, shin bands),
  gold arm bands, ivory, fin membrane, scales; MR red = per-class specular mask (`openyamm_specular_mask`).
- **Tiers** (`scripts/ramps_liz.py`, the tiers project's method): mask R garment, G trim; A fitted to the paint (mean
  error 2.8 / 6.4 levels), B (Farmer, 402) and C (Villager, 403) from the native pixel pairs. Skins `m400_a/b/c`.
- **Clips** (`scripts/clips_mm9.py` from mm9_lizardorc_claude, `scripts/roles_lizp.json`): Standing `stand` 1.5 s, Walk
  `walk` 1.2 s (legs x1.2), Run `run` (legs x1.15), Sprint `run` x1.4 (legs x1.3), Fidget `fidget1` 4.0 s, Attack
  `Hattack1` 0.733 s (the empty-handed swing reads as a claw rake), Hit `wince1` 0-0.75 s at x1.5 = the native 0.5 s,
  Death `die1` 1.37 s, Corpse. Added to clips_mm9: `mirror_arm` (the lizard-orc's right hand holds a cutlass in every
  clip; in Standing, Fidget and the gaits the right arm takes the free left arm's motion mirrored across the body,
  half a cycle later in the gaits), `gain` (leg amplitude, from the Guard pilot), `dead_name`. Fidget hands pushed out of
  the skirt by `hand_rest.py` (Yrsa v2). Floor: `scripts/floor_ops.txt`.
- **Runtime** (`TOKEN=<lease> scripts/build_runtime.sh [--install]`): export, clips, material (`attach_material.py`, node
  `Lizardman_Body`), prepare, LODs (`build_actor_lods.py`), shadow tuck, region variants, far LODs by the
  lod_repair steps at r25_12, hand rest, floor fix, winding.

## Binding and regression

`assets_dev/worlds/mm8/models/actors.yml` (A/B/C): scale 121.115 (native 196 px / 1.6183 m Standing height), strides
walk 1.82, run 2.346, sprint 2.531 (`gait_gate.py` PASSED: Standard wander x1.09-1.25, chase x0.94-1.08, MAW chase
x1.22-1.26), `attack_melee`/`attack_ranged`: Attack with impact 0.3 s (right claw furthest forward), look on
`Bip01 Neck/Head`, upper body `Bip01 Spine1`. The regression `mm8_lizardman_peasant_actor_model_keeps_native_roles`
(`game/outdoor/HeadlessOutdoorDiagnostics.cpp`) now expects the new clip set and lengths (Attack added); built under the
shared lock, passes.

## Checks (installed 2026-11-11)

| Check | Before | After |
|---|---|---|
| LOD triangles | 8,245 / 4,120 / 2,744 / 2,417 | 9,398 / 4,694 / 2,324 / 1,172 |
| Rig | Meshy auto-rig 40 bones, 8 influences | MM9 LIZARDORC 42 nodes + 16 finger joints, 4 influences |
| `texture_quality.py` | atlas 44.6 %, fragments 49.4 %, density p50 500, spread 3.2, stretch p90 2.63 | atlas 55.1 %, fragments 2.1 %, p50 1,253, spread 1.86 (head x1.8 by design), stretch 1.12 |
| Attack motion ratio vs MM9 bipeds (`rebuild_measure.py`) | 0.46 (Walk played once) | **0.98** (claw rake) |
| Worst region beyond Standing | Run spine 6.6 % | Run spine 8.2 % (all clips under 12 %) |
| Hand inside the body, worst | Hit 4.6 % (4.1 cm) | Fidget 1.4 % after hand_rest (was 3.1 %) |
| Floor audit, gait gate, winding | ok / - / 0 | ok / PASSED / 0 |
| `mm8_lizardman_peasant...`, `mm6_mm7_mm8_actor_models_build_every_binding` | pass | pass (647 descriptors, 0 failed) |
| Viewer check | | 54 switches, 0 console errors |

Sheets (viewer shots, identical cameras; the installed model plays Walk where the new one plays Attack):
`review/sheet_tiers.png` (A/B/C: front, three-quarter, head, attack contact), `review/sheet_a_all.png` (tier A: four
body views, head front/three-quarter, both hands, attack wind-up and contact, walk, hit, corpse). Flat deformation
strips `review/v6_*.png`, `review/mirror_test*.png`, `review/fidget_hand2.png`. In game: `review/ingame/crop.png`
(New Sorpigal and Agar's Laboratory spawns; the peasants flee, so in game they were seen walking/running).

Open / deviations: no separate head paint; the MM9 stance is a wider, brawler's stance than the native hunched peasant
(MM9's clips as approved for the route); the armpit/lat stretches when the arms rise (Hit, Death), as on the
lizard-orc; four-digit hands kept (identity) instead of grafted five-finger MPFB hands.

Revert: `python3 tools/install_model.py level_generation/creatures/mm8_lizardman_peasant_rebuild_claude/work/before_rebuild/mm8_lizardman_peasant.glb --world mm8`,
restore the three bindings from `work/before_rebuild/actors_mm8.yml`, and the regression's clip table (git diff of
`game/outdoor/HeadlessOutdoorDiagnostics.cpp`, then rebuild).

## Follow-up 2026-11-12: rebuild reverted (user), retarget trial stopped

User, comparing the rebuild with the original in the audit compare viewer: "orig animation def better than new one",
then (2026-11-12) "lizardman definitely the older animations... just need new retexture pass". The rebuild is reverted;
the original model gets a texture pass instead ([mm8_lizardman_peasant_texpass_claude](../mm8_lizardman_peasant_texpass_claude/README.md)).

- **Revert (agent fix-lizardman-anim):** `python3 tools/install_model.py level_generation/creatures/mm8_lizardman_peasant_rebuild_claude/work/before_rebuild/mm8_lizardman_peasant.glb --world mm8`
  (sha256 77a5986a..., identical to `../audit_mm678_20261111/compare_viewer/before/worlds/mm8/models/`; assets_source and
  the cooked assets_dev GLB are byte-identical to HEAD again). The three `Lizardmen Male (Peasant)` bindings in
  `assets_dev/worlds/mm8/models/actors.yml` restored from `work/before_rebuild/actors_mm8.yml` (equal to HEAD), and the
  clip table of `mm8_lizardman_peasant_actor_model_keeps_native_roles` restored to Standing 4.0, Walk 31/30, Hit 0.5,
  Fidget 0.5, Death 0.75, Corpse 0.125 (only that hunk; the other cases' changes untouched). Game rebuilt under the
  shared lock; the case passes against the original model.
- **Retarget trial (not installed):** before the user's decision, the original's clips were retargeted onto the
  rebuilt mesh by world-rotation copy in numpy (`scripts/retarget_orig.py`, `scripts/roles_orig.json`,
  `scripts/anim_followup2.sh`): per bone a swing (hands: a full frame across the knuckles, since the rebuilt left thumb
  lies along the hand) from the rebuild's bind to the original's, pelvis displacement scaled by the pelvis heights
  (1.052), fingers held at the MM9 mitten curl; Attack = MM9's claw rake layered over the upright Standing (arms 0.7-1.0,
  spine 0.5, legs 0). It read upright and relaxed like the original (`review/followup2/v4_sheet1.png`, `v4_sheet2.png`,
  `v6_attack.png`; strides 1.554 / 3.028 / 4.673, gait_gate PASSED), but the user chose the original model as a whole.
  `work/before_followup2/` holds the rebuild GLB and its bindings, should the rebuild ever be wanted again (with
  the clip table from the git history of the regression).
