# MM8 Salamander (`m568`, Fire Newt / Fire Lizard / Salamander) reduction (2026-10-19)

User: "OK go ahead" (MM8 triangle-reduction batch of openyamm-f6: m536, m616, m568, m628, m412). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: the installed textures, three palette
variants and region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m568.glb`, byte-identical to
`../mm8_m568_claude/export/mm8_m568.glb` (the `assets_dev` runtime copy was cooked from it at the same time, 11:02 on
2026-10-18), copied to `work/mm8_m568_source_pre_reduce.glb` (rollback source). One merged body + head atlas material
per tier, one `Body` node, 74 bones, 4 influences, 9 clips. The polearm (`mm8_m568_polearm.glb`, 268) is a separate
installed attachment and is not touched. Scripts come from `../mm8_m624_reduce_claude/scripts/` (parent-before-matrix
fix, normal-aware weights for a serpent body).

## Where the triangles are

The m568 build already reduced the body once with face, hands, crest and UV boundaries protected, so the lower body is
sparse (20-40 faces per 5 cm band below the waist). Of 12,490 triangles: head and neck 5,392 (the crest membrane
1,832 and about 1,500 in 22 separate crest ribs of it), hands with fingers 3,013, tail 1,952, arms 1,321, torso 812.
Weld 7,946 -> 252 open edges, no coincident vertices with other weights (no split seam), no two-sided sheets.

## Keep sets and groups (`scripts/m568_sets.py`, `scripts/m568_sets_i.py`)

- Kept exactly: both hands and fingers (fitted polearm grips, `grip_check.py`), small pieces up to 150 faces
  (`REA_SMALL=150 small_pieces.py`: ten claws, 22 crest ribs, the 140-face snout piece), the painted yellow eyes with
  two rings, and the torso (B_Pelvis/B_Spine* faces, 620): every cut of the back smeared the painted spots and the
  dorsal stripe at the waist (`review/glbclose/sheet_try_h.png`, `sheet_try_i.png`).
- Group 1, head and neck skin (2,093): 70 %. Group 2, crest membrane (1,832): 45 %. Group 3, the front of the serpent
  bend (270 faces, z 0.15-0.65 m): 85 %; every uniform step had its maximum (34-49 mm, `Dead:0`) there.
  Group 4, arms (1,277): 75 %. Group 0, the tail, takes the rest.
- `REA_NORMAL_WEIGHTS=1` (new vertices take weights from the nearest source surface with an agreeing normal).

## Ladder

Limits for the 2.4 m height: p99 7.2 mm, max 36 mm.

| config | step | triangles | p99 / max mm | IoU | |
|---|---|---:|---|---|---|
| source | | 12,490 | | | |
| a: uniform body, head 80 %, crest 60 % | 80 % | 9,990 | 3.76 / 34.30 | 0.995 | pass (bend point) |
| a | 75 % | 9,364 | 4.70 / 36.23 | 0.991 | fail (max) |
| c: + bend 85 %, head 65 %, crest 50 % | 70 % | 8,740 | 5.35 / 20.27 | 0.990 | pass; 38 drifted faces, 754 cm² |
| e: head 55 %, crest 45 % | 70 % | 8,742 | 4.83 / 20.27 | 0.993 | pass; back spots smeared |
| d / f: one drift-lock round on c / e | 70 % | 8,740 | 9.05 / 8.64 p99 | 0.986 | fail (lock moved the cut) |
| g: head 80 %, crest 45 % | 74 % | 9,240 | 4.77 / 20.27 | 0.992 | pass; lower back smeared |
| h: g + waist band kept | 74 % | 9,240 | 5.65 / 24.78 | 0.991 | pass; spots angular higher up |
| i: torso kept, head 70 %, arms 75 % | 78 % | 9,740 | 4.10 / 20.27 | 0.995 | pass |
| **i** | **76 %** | **9,490** | 5.05 / 24.78 | 0.993 | **pick** |
| i | 74 % | 9,240 | 7.04 / 24.41 | 0.988 | pass; 2,270 cm² drift on the tail |

Texture drift at the pick: 19 faces over 40 (269 cm², p99 23.2), no drift lock (one lock round raised the error in
both tries). Close-ups straight from the GLBs (file normals, `glb_close.py`): `review/glbclose/sheet_i76_head_tex.png`,
`sheet_i76_head_clay.png` (head, crest, hand, tail tip) and `sheet_try_i.png` (back, torso, arm, tail, Dead). The light
forehead wedge in `review/close/` (renders of the welded `source.blend`) is the weld's normal artifact and does not
appear in the GLB renders.

## Build

`export_cand.py` (Cand_76) -> `swap_lod0.py` -> `build_lods.py` (as the m568 project: 0.5 / 0.25 / 0.125, 4
influences, body only) -> `../mm8_m568_claude/scripts/shrink_shadow_lods.py` (inset shadow LODs, as installed) ->
`carry_variants.py` (variants on all 7 LOD/shadow primitives) -> `fix_lod_winding.py` -> `check_winding.py` (0 inverted
closed parts): `export/mm8_m568.glb`, 7.4 MB (installed 7.8 MB), 9 clips.
The LOD builder collapsed three crest ribs to inverted 4-triangle tetrahedra at LOD3 (colour and shadow);
`fix_lod_winding.py` reverses those six closed parts.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 12,490 | 6,243 | 3,122 | 1,549 |
| reduced | 9,490 | 4,744 | 2,371 | 1,171 |

- `scripts/grip_check.py`: all 2,276 LOD0 hand vertices keep their bind positions (max 0.0009 mm) and weights.
- `work/lod_check_{src,r76}.json`: every LOD keeps the 2.40 m height (LOD3 2.398 m, installed 2.399 m); lowest point
  over every clip -0.4 mm (installed -0.4 mm); no face stretches over 20x in any clip (installed LOD0: 2).
  `review/lods/sheet.png`: installed / reduced, LOD0-3, standing three-quarter, head and Attack.
- Viewer: `review/viewer/` (installed vs 76 %, three palettes, polearm not shown);
  `python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m568_reduce_claude check`:
  54 switches, no console errors.

## Spear handling after the Raven Man (round 2, 2026-10-19)

User review: "please check the raven man how he holds his spear and maybe do the same limb movement / weapon
placement as he has + show me also the weapon in the viewer". Built on the staged reduced body: geometry, skin,
LODs and textures of round 1 are unchanged; only the clips (and the LOD1-3 rebuild noted below) are new.

**Raven Man (m584), read with `scripts/spear/read_spear.py` from the installed GLB (`work/raven_spear.json`):** the
glaive is a separate attachment on a `Polearm` joint parented to `B_R_Hand`; `actors.yml` binds
`mm8_m584_polearm.glb` at node `Polearm`, as the Salamander's. In chest space he carries it in a low two-hand guard:
right hand at the hip just right of the centre, left hand 24 cm lower on the shaft at the belly, blade up and out
to his right (shaft axis -0.80, -0.10, 0.60), elbows close. Standing, Walking and Hit keep that grip with only the
chest moving; Attack (26/30 s impact) lifts the spear near vertical beside the right shoulder (0.5-0.7 s, shoulders
protracted), then drives it forward and down and recovers; Death holds it until 0.33 s and slides it out of the fists.

**What was copied (`scripts/spear/animate_spear.py`):** per frame, the polearm axis and blade plane, the midpoint of
the two hand contacts, both elbow directions, both shoulder positions (clavicle swing, at most 30 degrees) and where
each wrist sits around the shaft, all in the Raven Man's chest space, scaled by the arm-length ratio (1.261) onto the
Salamander's shoulders and carried by the Salamander's own chest. Clip times: Standing 2 s -> 3 s, Walk/Running =
his first 1 s of Walking, Attack piecewise (his impact 26/30 s on our 1.0 s, his end 35/30 s on our 4/3 s), Hit
0.733 -> 0.625 s, Death holds his guard until our 0.24 s release; small end-to-start drifts of his clips are spread
linearly so loops close. Unchanged from `../mm8_m568_claude/scripts/animate_salamander.py`: the serpent body, tail,
spine, head, finger grips (`grip_pose.json`), the Fidget left-fist lift, the Death release and the polearm settling
beside the corpse, durations and the 1.0 s contact events.

**Salamander adaptations:**
- Grip on the shaft: right hand at -0.15 m, left at -0.45 m from the polearm centre (his 24 cm spacing scaled, held
  in the lower half like his, the right hand on the lower green wrap). A centre grip pushed the butt through the
  torso in the forward drive; a lower grip swept the long fork through the crest on recovery.
- The Salamander's hand is longer (grip centre 19 cm from the wrist): each grip is rolled about the shaft to his
  wrist placement and then searched +-60 degrees for the least wrist bend within a forearm-twist budget of 86
  degrees; where a contact is beyond reach (the left hand across to the raised shaft), the spear moves towards that
  shoulder by the shortfall; both fists stay 23 cm in front of the torso (it is deeper than his).
- Cast (no Raven Man clip): rises into his attack lift (his 0.15 s pose) for the 1.0 s release and settles back. The
  Fire Bolt socket (`Polearm` [0, 0.58, 0]) is at 2.20 m at 1.0 s, inside the engine's launch bounds
  (`WorldFxSystem::actorLaunchPoint`: 1.5 x height 160 / 106.7 = 2.25 m); a cap keeps it at or below 2.22 m.
- Fidget: the lifted left fist keeps its wrist angle to the forearm (the original rest-orientation slerp gave the
  re-rolled grip a 50-degree twist jump).
- Death: a wider release arc (the shaft now starts lower; the original arc clipped the falling body).
- LOD1-3 rebuilt with the 25 LOD0 vertices around both armpits kept (`scripts/spear/build_lods_spear.py`): with the
  new shoulder swing one long LOD2 chest-to-arm face stretched 22x in Fidget and Hit. LOD tris 9,490 / 4,744 /
  2,371 / 1,170.

**Pipeline:** `animate_spear.py` (opens `../mm8_m568_claude/export/mm8_m568.blend` read only, writes
`work/spear_final.blend`) -> `export_anim.py final` (rig and actions only, the project's exporter settings) ->
`transplant_anim.py` (clips replaced by node name; every animated node's rest TRS must match: 0.0) into the reduced
LOD0 -> `build_lods_spear.py` -> `../mm8_m568_claude/scripts/shrink_shadow_lods.py` -> `carry_variants.py` ->
`fix_lod_winding.py`. `SPEAR_MODE=original` reproduces the installed clips through the same export and transplant
with 0.000 mm joint and tip difference (pipeline check).

**Checks** (`review/spear/arm_gate.json`, `animation_audit.json`; installed motion for comparison in
`arm_gate_installed_motion.json`; every second 48 Hz frame of every clip):

| | installed motion | new |
|---|---|---|
| polearm inside the body (outside the grip zones) | 0 | 0, Death 2.8 mm at one release frame (shaft brushing the falling body) |
| hands inside the torso | 0 | 0 |
| wrist bend change from rest, held clips | 144 degrees | 53-59 degrees |
| wrist bend, Attack / Cast / Death | 144 | 75 (left, 0.875 s, drive start) / 52 / 92 (release, fingers opening) |
| forearm twist (twist bone vs forearm) / full twist before split | 40 / 85 | 72 / 88; largest frame step 25 degrees (Attack drive) |
| hand target out of reach | 0 | 0 (Death 0.3 mm) |
| loops (Standing, Walk, Running, Fidget) | closed | closed |
| serpent, spine, head joints vs installed clips | | 0 mm (Death 4.8 mm: floor lift) |
| LOD heights, floor, stretch (`work/lod_check_spear.json`) | | 2.40 m every LOD, lowest -0.4 mm, no face over 20x |
| winding / LOD0 hand vertices | | 0 inverted / 2,276 unchanged (0.0009 mm) |

Over budget: the left wrist at the start of the forward drive (75 > 60 degrees) and during the Death release (as
installed). Renders: `review/spear/sheet_final.png` (key poses, three views) and `review/spear/side_by_side.png`
(installed vs new with the polearm, quarter and front).

**Polearm and binding:** `mm8_m568_polearm.glb` is unchanged (same `Polearm` joint frame and rest; only its
animation changed), so no polearm file is staged. `actors.yml` needs no change: attachment node `Polearm`,
`polearm_charge` socket offset, 1.0 s impacts and `upper_body_root: B_Pelvis` all stay valid.

**Viewer:** `review/viewer/` now shows installed (unreduced, old motion) and new (76 % + spear handling), both with
the polearm attached under the `Polearm` joint (`viewer_variants.py <glb> <tag> <polearm.glb>:Polearm`), three
palettes; manifest revision `reduce-2-spear` with fresh sha256 and `?v=`. `run_creature_review.py ... check`:
54 switches, no console errors.

## Status

Round 2 (spear handling) installed 2026-10-19 after user review ("ok accepted") with `tools/install_model.py --world mm8`; actor regression `mm8_salamander_actor_models_keep_native_tiers_and_polearm` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).

Install: `python3 tools/install_model.py --world mm8 level_generation/creatures/mm8_m568_reduce_claude/export/mm8_m568.glb`
(the polearm stays as installed),
then `OPENYAMM_REGRESSION_FILTER=mm8_salamander ./build/game/openyamm --world mm8 --headless-run-regression-suite actors`
(it checks the Cast release at 1.0 s against the launch bounds) and a ledger row. Round 1 (old motion, same
geometry) is kept as `work/mm8_m568_r76_old_motion.glb`.
Rollback: `python3 tools/install_model.py --world mm8 level_generation/creatures/mm8_m568_reduce_claude/work/mm8_m568_source_pre_reduce.glb`.

Reproduce: `import_source.py` (REA_NODE=Body, REA_GLB=the rollback source) -> `REA_PROTECT=B_Head,B_Neck dump_mesh.py`,
`dump_groups.py` -> `REA_SMALL=150 small_pieces.py` -> `m568_sets.py` -> `m568_sets_i.py` -> `REA_NORMAL_WEIGHTS=1 REA_KEEP_FACES=work/keep_i.npy
REA_GROUPS=work/groups_i.npy REA_GROUP_RATIOS=1:0.7,2:0.45,3:0.85,4:0.75 run_ladder.sh i 0.78,0.76,0.74` ->
`close_ladder.py`, `texture_drift.py r76`, `glb_close.py` -> build as above -> `grip_check.py`, `lod_check.py`,
`lod_views.py`, `viewer_variants.py`, `viewer_manifest.py`.
