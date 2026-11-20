# MM8 Dragon Hunter (`m456`, Dragon Hunter / Crusader / Dragonslayer) reduction (2026-10-19)

User: "OK do both" (m440 and m456, the two heaviest unreduced MM8 models). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: the installed textures, three palette
variants (`KHR_materials_variants`) and region ramps stay valid. No Meshy credits. Claim confirmed with openyamm-f9 and
openyamm-f6.

Source: the installed `assets_source/worlds/mm8/models/mm8_m456.glb`, byte-identical to
`../mm8_m456_claude/export/mm8_m456.glb` (the current revision, with the 2026-10-16 sleeve-root shoulder repair and the
arm/pauldron repair), copied to `work/mm8_m456_source_pre_reduce.glb` (rollback source). One material
(`DragonHunter_A`, B/C as variants), merged 2080x1024 head/body atlas (head set u > 1056/2080), node `DragonHunter`,
59 bones, 4 influences, 8 clips. The serrated sword (`mm8_m456_sword.glb`, 820 / 376 / 172 / 60) is unchanged and not
part of this build. Scripts are copied from `../mm8_m420_reduce_claude/scripts/`; `refine_knee_lods.py`,
`check_shoulders.py` and `check_knees.py` from the production project.

## Keep sets and regions (`make_groups.py`)

Weld 7,243 -> 941 open edges; 9 coincident vertices with other weights. 34 connected pieces; `review/groups_sheet.png`.

| label | faces | ratio |
|---|---:|---|
| face (head skin, front, above 1.39 m) | 1,066 | 75 % |
| rest of the head skin (neck, back of the head under the helmet) | 379 | 50 % |
| helmet cap and gold crest | 960 | 70 % |
| right (free) hand | 1,106 | 50 % |
| knee band of the two leg pieces (0.40-0.62 m) | 977 | 100 % (the production LOD build restores knee rows; a cut band bridged the bend) |
| knee guards | 780 | 75 % (cut with the body they came out pointed) |
| rest: legs, fauld, cuirass, bracers, sleeves outside the cuirass | 7,591 | remaining budget |

Kept exactly (`work/keep_d.npy`, 4,054 faces):
- the sword (left) hand and fingers (1,112), so the fitted grip does not change;
- small pieces of up to 130 faces (908): eyes, cheek and nose guards, buckles, rivets, strap ends;
- the plume (410): decimation smoothed its jagged feather outline;
- both pauldrons (399; rigid hinge pieces of the arm/pauldron repair);
- **the shoulder repair**: the sleeves' roots under the cuirass (469 faces, |x| < 0.16 m above 1.1 m) and faces of
  the cuirass, sleeves and pauldrons within 1.2 cm of the cuirass or pauldron rims (544);
- the soles (faces below 6 cm, 194);
- 4 cm patches at the front crotch seam (the first ladder failed every step there, 33-39 mm in Death) and at both
  armpits front and back and the collar front (most of the texture drift of the 70 % steps).

## Ladder (limits for the 1.70 m height: p99 5.1 mm, max 25.5 mm)

| config | step | triangles | p99 / max mm | drift > 40, faces over 3 cm2 | |
|---|---|---:|---|---|---|
| source | | 13,269 | | | |
| a: no crotch patch, helmet 60 %, knees cut with the body | 75 % | 9,949 | 2.87 / 32.8 | | fail (crotch) |
| b = a + crotch patch | 65 % | 8,621 | 4.90 / 21.0 | 59 faces, 287 cm2 | pass; drift on the cuirass front |
| d = b + armpit/collar patches | 70 % | 9,285 | 3.82 / 17.4 | 5, 18 cm2 | pass; LOD0 knees bridged (check_knees 19.8 mm, limit 8) |
| g = d + knee band kept | 70 % | 9,285 | 4.94 / 19.4 | 18, 134 cm2 | pass; knees as installed; knee guards pointed, plume smoothed |
| m = g + knee guards 75 %, helmet 70 %, plume kept | 77 % | 10,213 | 3.94 / 17.5 | 8, 71 cm2 | pass |
| **m** | **76 %** | **10,079** | **4.39 / 19.4** | 12, 102 cm2 | **pick** |
| m | 75 % | 9,947 | 4.86 / 19.4 | 16, 130 cm2 | pass, close to p99 |

Drift locks (`drift_lock.py`) and extra patches on the cuirass buttons and bracers did not converge: every lock pushed
the cut elsewhere (the drift moved to other armour faces) and brought back a 60 mm failure in `Running:9`. The
remaining drift is on flat armour plates (bracers, cuirass sides, back plate) and is not visible in the textured
close-ups below, where the cuirass buttons, trims and rivets match.

## Checks

- **Close-ups straight from the GLBs** (`glb_close.py`, each file's own normals; installed left, reduced right):
  `review/glbclose/sheet_a.png` (head front, three-quarter, back, cuirass, back plate, sword fist, free hand; textured
  and clay), `sheet_b.png` (legs, knee in Running, crotch, both shoulders and the raised sword arm in Attack, Attack,
  Death). Face, plume, crest, cuirass buttons and trims, pauldron borders, sleeves, sword fist, knees and greaves
  match. `sheet_lod3.png`: LOD3 of both (left arm in Fidget, raised arm, torso, head): equally faceted.
- **Shoulders** (`check_shoulders.py`, the production attachment check, every clip at 120 Hz, all LODs): the sleeve
  roots stay under the cuirass; root drift at most 0.12 / 0.26 / 1.98 / 2.07 mm at LOD0-3 (limits 4 / 6 / 10 / 20),
  sleeve stretch p99 at most 2.02, max under 4.5 (`work/shoulder_check.json`).
- **Knees** (`check_knees.py`, the production chord check): maximum skinning chord error 6.9 / 7.2 / 13.5 / 23.7 mm
  at LOD0-3 (limits 8 / 16 / 24 / 40; installed 6.9 / 7.6 / 13.8 / 28.1), `work/knee_chord_error.json`.
- **Shared gates** (`claude_shared/gates/run_gates.py` with the production `gates.json`; the installed model already
  fails many rows, see `../mm8_m456_claude/review/ASSESSMENT.md`), `gate_diff.py work/gates_src/gates.json
  work/gates_r76/gates.json`: no new failing row at LOD0 or LOD1. New failures only on the distant LODs: arm-into-body
  2.18 mm against 2.0 at LOD2 (right arm in Death, Fidget, Hit; installed 0.70), arm stretch p99 2.017 against 2.0 at
  LOD3 (right arm in Death), and 18 mm at LOD3 for the left arm in Fidget frame 14, the contact pose where the
  installed LOD2 already fails (10.5 mm; reduced LOD2 8.0). 18 rows improve (head penetration in Hit 27 -> 15 mm at
  LOD3), 4 failures are fixed, 16 failing rows got slightly worse (Fidget LOD1 left arm 15.1 -> 16.8 mm, head 21.1 ->
  23.2 mm; the rest are foot-yaw rows of the coarse LODs).
- **LODs** (`lod_check.py`, `work/lod_check_{src,r76}.json`): no face stretches over 20x in any frame of any clip at
  any LOD; lowest points as installed at LOD0/1, LOD2 Death -0.6 mm (installed +0.6), LOD3 Death -9.7 mm mid-fall
  (installed +1.3; Dead +3.7 as installed). Rest height 1.700 / 1.701 / 1.701 / 1.693 m (installed 1.700 / 1.700 /
  1.701 / 1.695). `review/lods/sheet.png`: every LOD standing, Attack and the Running knee frame.
- `check_winding.py`: 0 inverted closed parts. Clips, skeleton, materials, variants and images are those of the
  installed file (`swap_lod0.py` replaces only the geometry).

## Build

`build_export.sh ladder_m.blend Cand_76`: `export_cand.py` (`REA_CAND=Cand_76 REA_NODE=DragonHunter`, 4 influences)
-> `swap_lod0.py` into the installed file (`work/r76_lod0.glb`) -> `blender -b -P build_lods.py`
(tools/build_actor_lods.py, 0.44 / 0.19 / 0.075; the production used 0.46 / 0.21 / 0.075, which gave 0.553 / 0.260
of the smaller LOD0 after the knee rows, over the gates' 0.55 / 0.25 caps) -> `refine_knee_lods.py` (the production
knee rows: one at 0.49 m at LOD0, five / four / three at LOD1-3) -> `carry_variants.py` -> `compact_glb.py`:
`export/mm8_m456.glb`, 8.6 MB (installed 8.9 MB). Shadow LODs use the colour geometry, as installed.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 13,275 | 7,115 | 3,304 | 1,222 |
| reduced (76 %) | 10,151 | 5,525 | 2,456 | 982 |

Viewer: `review/viewer/` (installed vs reduced for the three tiers, ramps baked by `viewer_variants.py`, manifest by
`viewer_manifest.py` with sha256 and `?v=`; the sword is not shown),
<http://127.0.0.1:8912/level_generation/creatures/mm8_m456_reduce_claude/review/viewer/>;
`node level_generation/creatures/claude_shared/check_viewer.mjs <url> 240`: 48 model/clip switches, no console errors.

## Attack v2 (user review)

User: "dragon hunter attack anim - use legs also". The production Attack (SwordAttackL2 on a planted stance, 0.8 s,
impact 0.385417 s) moves only the spine, neck and arms: pelvis, thighs, calves and feet are two constant keys, so the
cut is swung from locked straight legs (the legs stand at 98-99 % of their full reach).

`scripts/attack_legs.py` keeps the arm and sword animation and adds the lower body per 120 Hz key of the clip (the
character faces +z, the left foot leads and the left hand holds the sword):

| time | pelvis (forward / down, hip turn) | lead (left) foot | rear foot |
|---|---|---|---|
| 0-0.18 s | back 5 cm, down 2.5 cm, hips turned 14 degrees into the wind-up | planted | planted |
| 0.20-0.34 s | drive forward and down | lifts 6 cm, steps 24 cm forward, plants before the impact | planted |
| 0.385 s (impact) - 0.50 s | deepest lunge: 16 cm forward, 8.5 cm down, hips turned 14-16 degrees through the cut | planted | planted |
| 0.52-0.70 s | rises and comes back | steps back to its place | planted |
| 0.80 s | Standing pose | | |

The pelvis follows a smooth spline with zero velocity at both ends, so the clip still starts and ends on the Standing
pose. Thighs and calves are solved by two-bone IK in each leg's bending plane, with the rig's bone lengths; both feet
keep their planted orientation. `B_Spine` keeps its world rotation from the source, so chest, arms and sword turn
exactly as authored while the hips counter-rotate under them, and the upper body rides the lunge. Duration and impact
are unchanged, so `actors.yml` needs no change. The edit is made in the GLB itself (no Blender re-export), so the arm,
pauldron and twist channels are byte-identical to v1. The export before this step is `work/mm8_m456_r76_attack_v1.glb`.

Checks (forward kinematics on the GLB at 48 fps and the project checks):
- **Planted feet:** 0.0 cm per frame of slide, the rear foot through the whole clip and the lead foot between steps.
  The ankles return to the guard height when planted, so the lowest point per LOD in Attack is unchanged
  (`work/lod_check_r76a2.json`: 2.2 / 2.3 / 1.8 / 5.2 mm above the floor, no stretched faces at any LOD in any clip).
  Maximum leg reach is 0.993 of full length, and the ankle targets are met exactly.
- **Sword at the impact:** same direction as v1 (blade and edge axes equal to three decimals); its node sits 16 cm
  further forward and 8 cm lower with the lunge. The blade's lowest point over the clip is 35 cm above the floor
  (v1: 43 cm).
- **Shoulders** (`check_shoulders.py`): pass; Attack sleeve-root drift at most 0.1 / 0.14 / 1.9 / 0.76 mm at LOD0-3.
- **Knees** (`check_knees.py`): pass; with the knees now bending in Attack its chord error is 2.7 / 3.9 / 6.8 / 12.0 mm
  (v1 0.8 / 1.2 / 2.0 / 3.6), below each LOD's maximum over the other clips (6.9 / 7.2 / 13.5 / 23.7).

`review/attack_v2/Attack_{side,front,q34}.png` (v1 top, v2 bottom, frames 0-38.4 at 48 fps, impact 18.5, the sword
on its node as in the engine; rendered by `scripts/attack_shots.py`), `review/attack_v2/close.png` (upper body and
legs at frames 10, 17, 18.5 and 26). Viewer: `review/viewer_attack/` (revision `reduce-2-attack`, installed vs reduced
with Attack v2), <http://127.0.0.1:8912/level_generation/creatures/mm8_m456_reduce_claude/review/viewer_attack/>;
`check_viewer.mjs`: 48 switches, no console errors. `review/viewer/` (reduce-1) is superseded.

## Waist (user review 2026-10-19)

User: "dragon hunter's torso cut off in the middle of the animation" (Attack, seen from above). The skin had the
cuirass rigid on `B_Spine2` (joint at 1.27 m) down to 1.04 m and the belt on `B_Pelvis` (0.95 m) below 0.96 m, with only
19 torso vertices between them. In Attack the spine turns about 45 degrees and bends about 55 degrees over the pelvis,
so the cuirass rim swung off the belt and showed the dark underlayer. It was there before the reduction and in Attack v1.

`scripts/waist_weights.py work/mm8_m456_r76_attack_v2.glb export/mm8_m456.glb` re-weights the 1,808 vertices (all
colour and shadow LODs) that are weighted only to the spine chain between 0.96 and 1.12 m: a smoothstep by height along
`B_Pelvis -> B_Spine -> B_Spine1 -> B_Spine2`. Arms, legs, the upper cuirass and the shoulder repair are unchanged.
Checks: winding 0; `check_shoulders.py` and `check_knees.py` pass with the same values; `lod_check.py` as before (no
stretched faces, same lowest points); shared gates against Attack v2 (`work/gates_v2` -> `work/gates_final`, with the
guard-fixed sword): no new or worse row, left arm into the body in Fidget 16.1 -> 5.4 mm at LOD0. Running, Fidget, Hit
and Death look unchanged. Installed 2026-10-19 with the sword guard fix (`../mm8_m456_claude/README.md`); the
regression passes. Rollback: install `work/mm8_m456_r76_attack_v2.glb` with `--name mm8_m456.glb`.

## Status

Installed 2026-10-19 (user: "ok accepted", with Attack v2); winding 0, the regression below passes and the row is in
the ledger. Install (from the repository root): `python3
level_generation/decorations/mm8_3d/animated/scripts/check_winding.py
level_generation/creatures/mm8_m456_reduce_claude/export/mm8_m456.glb`, `python3 tools/install_model.py
level_generation/creatures/mm8_m456_reduce_claude/export/mm8_m456.glb --world mm8`, then
`OPENYAMM_REGRESSION_FILTER=mm8_dragon_hunter_actor_models ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_dragon_hunter_actor_models_keep_native_roles`) and add the row to [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
The sword stays as installed; bindings and scale are unchanged.
Rollback: `python3 tools/install_model.py level_generation/creatures/mm8_m456_reduce_claude/work/mm8_m456_source_pre_reduce.glb --world mm8 --name mm8_m456.glb`.

Attack v2: `attack_legs.py work/mm8_m456_r76_attack_v1.glb export/mm8_m456.glb` -> `compact_glb.py export/mm8_m456.glb`,
then the checks above and `VIEWER_DIR=review/viewer_attack VIEWER_REVISION=reduce-2-attack viewer_variants.py` /
`viewer_manifest.py`.

Reproduce: `REA_GLB=<rollback source> REA_NODE=DragonHunter blender -b -P import_source.py` -> `dump_mesh.py` ->
`dump_faces.py` -> `make_groups.py` -> `patch_keep.py work/keep_base.npy work/keep_b.npy 0.034,-0.105,0.712
0.015,-0.084,0.725 0.055,-0.128,0.723` -> `patch_keep.py work/keep_b.npy work/keep_d.npy 0.21,0.042,1.13
0.21,-0.08,1.165 0.034,-0.107,1.353` -> `REA_HEIGHT_M=1.70 REA_KEEP_FACES=work/keep_d.npy REA_GROUPS=work/groups.npy
REA_GROUP_RATIOS=1:0.75,2:0.5,3:0.7,4:0.5,5:1.0,6:0.75 run_ladder.sh m 0.77,0.76,0.75` -> `texture_drift.py r76`,
`close_ladder.py`, `probe_max.py` -> `build_export.sh ladder_m.blend Cand_76` -> `check_shoulders.py`,
`check_knees.py`, `run_gates.py` + `gate_diff.py`, `REA_NODE=DragonHunter lod_check.py`, `lod_views.py`,
`glb_close.py`, `viewer_variants.py` (installed r100 and export r76), `viewer_manifest.py "MM8 Dragon Hunter" r76 13275
10151`.
