# MM8 Dark Elf warrior (`m432`, Dark Elf Warrior A/B/C) reduction (2026-10-18)

User: "pick 5 more to do" (MM8 triangle-reduction batch 2, coordinated with sessions openyamm-f9, openyamm-f6 and
openyamm-b4). Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: the
installed textures, three palette variants and region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m432.glb` (byte-identical to
`../mm8_m432_claude/export/mm8_m432.glb`; the runtime copy has the same nine clips, so not stale), copied to
`work/mm8_m432_source_pre_reduce.glb` (rollback source). One merged body + head atlas material (`M432_A`, 2080x1024),
one `M432` node, 58 joints, 4 influences. The sword (`mm8_m432_sword.glb`, 278 triangles) is a separate installed
attachment on `Socket_Sword` and is not touched. Scripts are copied from `../mm8_m624_reduce_claude/scripts/` (fixed
parenting order in `reduce_ladder.py`, `grip_check.py`, per-region groups).

## Where the triangles are

The m432 build already reduced the body once, protecting face, hair and gloves (its README), so the suit is thin.
Weld 6,351 -> 785 open edges; no coincident vertices with other weights; no two-sided sheets (`work/import.log`
equivalent: 10,893 triangles in and out). Pieces (`scripts/m432_regions.py`): body suit 3,200, head skin 2,046, hair
1,649, two gloves 1,514, boots 1,200, pauldrons 500, eyes 384, 37 studs and small pieces 400.

One-region tests (that region cut, everything else kept; limits for the 1.804 m bind height: p99 5.41 mm, max
27.06 mm; `work/selection_{hair,boots,paul,body,head,eyes}.json`):

| region | ratio | tris | p99 / max mm | |
|---|---|---:|---|---|
| hair | 70 / 50 / 35 % | 10,397 / 10,067 / 9,821 | 1.33 / 4.69, 2.81 / 7.15, 5.14 / 14.81 | pass |
| boots | 70 / 50 / 35 % | 10,629 / 10,453 / 10,323 | up to 3.52 / 11.27 | pass |
| pauldrons | 70 / 50 / 30 % | 10,741 / 10,641 / 10,593 | up to 2.18 / 8.43 | pass |
| body suit | 80 / 65 / 50 % | 10,251 / 9,773 / 9,291 | 2.36 / 16.35, 3.43 / 17.68, 4.28 / 28.04 | fail at 50 % |
| head skin | 80 / 65 / 50 % | 10,483 / 10,177 / 9,869 | up to 1.15 / 3.48 | pass |
| eyes | 70 / 40 % | 10,777 / 10,709 | up to 0.21 / 1.3 | pass |

## Picked configuration

Close-ups straight from the GLBs (file normals, `scripts/glb_close.py`, `scripts/glb_sheet.py`; the
`source.blend` normals are scrambled by the weld and are not used):
- **a** (`work/keep_a.npy`): face skin 75 % creased the left cheek and darkened it textured; suit 65 % lost the
  chest and back sculpt in clay (`review/glbclose/sheet_a_head.png`, `sheet_a_body.png`).
- **b**: whole front of the face kept (`M432_KEEP_FACE=1`), face matches (`review/glbclose/sheet_b.png`); hair at
  50 % opened gaps along its lower edge where the suit shows through (`review/glbclose/sheet_b75_all.png`).
- **c**: hair, boots, pauldrons 40 %: 7,867 triangles, p99 5.59 mm, fails.
- **d**: hair 70 %: the gaps close (`review/glbclose/sheet_src_d75.png`).
- **e**: one `drift_lock.py` round on d (texture drift > 40: 10 faces / 34.8 cm2 -> 8 faces / 8.0 cm2).
- **f (pick)**: e plus every face touching a vertex with hand + finger weight > 0.3 kept exactly (the suit's sleeve
  ends): in e, 45 hand-weighted sleeve vertices moved up to 9.8 mm beside the gloves.

`scripts/m432_sets.py` + `drift_lock.py` + the cuff set (`work/keep_f.npy`, 3,602 faces kept exactly): both gloves,
studs and small pieces, boot soles (faces below 6 cm), the front of the face (painted features ringed), the drift
lock and the sleeve ends. Groups: hair 70 %, boots 50 %, pauldrons 50 %, eyes 60 %, rest of the head skin (neck,
ears, scalp under the hair) 55 %; the suit takes the ladder budget (70 %).

| step | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| source | 10,893 | | | | |
| b, suit 90 % | 8,489 | 3.90 / 16.01 | 0.9943 | 0.9958 | pass |
| d, suit 70 % | 8,177 | 3.95 / 16.01 | 0.9923 | 0.9954 | pass |
| **f, suit 70 %** | **8,253** | 4.10 / 16.01 | 0.9915 | 0.9953 | **pick** |
| c, hair/boots/pauldrons 40 % | 7,867 | 5.59 / 15.95 | 0.9908 | 0.9934 | fail (p99) |

The 16 mm maximum is the right pauldron in Death frame 48 (`probe_max.py`), the same at every step.
Texture drift (`texture_drift.py r75`): 8 faces over 40, 8.0 cm2, p99 20.8.

## Build

`export_cand.py` (Cand_75) -> `swap_lod0.py` -> `build_lods.py` (the m432 project's builder settings,
`tools/build_actor_lods.py` 0.5 / 0.18 / 0.06, body only, 4 influences; the installed LOD1-3 carried 8 influence slots)
-> `../mm8_m432_claude/scripts/shrink_shadow_lods.py` (inset shadow LODs, as installed) -> `carry_variants.py`:
`export/mm8_m432.glb`, 6.8 MB (installed 7.5 MB), 9 clips, three palette variants on all 8 colour/shadow meshes;
nodes, materials, images, textures, animations, skin and mesh extras match the installed file. Winding check:
0 inverted closed parts.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 10,893 | 5,444 | 1,955 | 647 |
| reduced | 8,253 | 4,126 | 1,481 | 491 |

- `scripts/grip_check.py ... M432` (`work/grip_check.log`): all 1,262 LOD0 vertices with hand + finger weight > 0.5
  keep their bind positions (max 0.0007 mm) and weights, so the two-handed sword grip is unchanged at LOD0.
- `work/lod_check_{src,r75f}.json`: every LOD keeps the source bounds (LOD3 1.7 mm narrower, 1.8 mm lower top) and
  the same lowest point in every clip (-94 mm in Death at LOD0/1, as installed); no face stretches over 20x in any
  clip at any LOD. `review/lods/sheet.png` compares all LODs.
- No shared gate config exists for m432 (`../claude_shared/gates/`); the project's own penetration gates
  (`../mm8_m432_claude/scripts/gates.py`) run on its assembled `.blend` and were not re-run. Gloves and sleeve ends
  are exact; the suit moves at most 16 mm (p99 4.1 mm).
- Viewer: `review/viewer/` (installed vs reduced, tiers A/B/C, the installed sword added under `Socket_Sword` for
  review only by `scripts/viewer_sword.py`); `tools/run_creature_review.py ... check`: 54 switches, no console errors.
  `review/shots/sheet_sword.png`: the grip in Standing, Attack and Cast matches.

## Attack against the native sprite

`review/attack_native/sheet_native_vs_3d.png` (native `m432Aa`-`Ah` views 0 and 2 against the 3D Attack at eight
even steps): both raise the sword two-handed at the right, cut forward and recover into an upright guard. The native
cut (frames d-f) is level and forward at waist height with an upright torso; the 3D cut leans further forward and
ends lower. No clear mismatch; animations unchanged.

## Attack v2

User review of the reduced model: in the old Attack the arms crossed, the right upper arm entered the pauldron, the
left hand floated beside the hilt and the pose collapsed forward ("could you please find some fitting 2 handed
animation? like check e.g. the lizardman warrior?"). The old clip's own fit record agrees: a 42 mm left-hand grip gap
at 1.08x arm reach (`../mm8_m432_claude/work/two_hand_fit.json`).

The new Attack is the Lizardman Warrior's user-approved two-handed downward slash (Mixamo Great Sword Slash (2), stored
in the animation library; no credits), refitted in the creature project (`../mm8_m432_claude/scripts/attack_v2.py`,
README "Attack v2").

- **Round 1** (`work/attack_v2/`, the first candidate) kept the source's low back-swing at the right. The user found
  rubber-hose arms at 0.604 s: that back-swing turns the hands about 185 degrees against the upper arms, and the
  forearm twist ran 35 -> 240 degrees.
- **Round 2** (current): the grip rises from the guard to the source's top of the wind-up at the right side (the
  native intent), along the shortest turn in the chest frame, and joins the source there. The torso, steps and the
  cut are the source's. Forearm twist now stays within 31-96 degrees (right) and -84 to -31 (left), a 65 / 53 degree
  excursion across the clip. Visible wrist bend is at most 48 / 56 degrees, and the grip turn needed for the wrists
  is 5 degrees. Both hands stay on the handle (gap below 0.001 mm).
- **Impact** is now where the blade passes level, pointing ahead (7 degrees off the facing), on the downswing. It
  is retimed onto the bound 0.917 s (0.9170 s); round 1 used the fastest tip, with the blade still pointing up. The
  clip keeps 55 frames (1.833 s), so `actors.yml` and the regression's durations stay valid.
- **Checks:** hand stretch 2.14x / 1.82x; soles >= -1 mm; peak arm rotation per 1/48 s 20 degrees (old clip 27); g6
  finds no contacts. The upper-arm probe (`../mm8_m432_claude/scripts/attack_v2_contacts.py`) finds one right
  upper-arm vertex against the chest at two half-frames of the follow-through; the old clip had up to 5 vertices at
  32 half-frames.

`scripts/attack_transplant.py` replaced only Attack in `export/mm8_m432.glb` and the three reduced viewer GLBs. Every
mesh, skin, material, variant, node and the other eight clips are byte-identical to the reduction candidate.
`work/attack_v1/` keeps the old-Attack export and viewer GLBs; `work/attack_v2/` keeps round 1. A re-export of the
old clip from the master matched the installed Attack exactly, which validates the path. `lod_check.py`
(`work/lod_check_attack2r2.json`): Attack lowest point -1.3 mm (LOD0/1), +0.4 / +5.7 mm (LOD2/3), no stretched faces
at any LOD.

- `review/attack_v2/sheet_native_new_old.png`: native `m432Aa`-`Ah` (views 0 and 2) against the reduced model with
  Attack v2 and the installed model (old Attack), front and left, eight steps.
- `review/attack_v2/arms_front_f24_34.png`: frames 24-34 at 48 fps from the front (the user's camera).
- `review/attack_v2/hands_grip.png`: both hands on the hilt at the rise, top, impact, follow-through and recovery.
- Viewer (revision attack-v2-r2): opens on Attack, installed (old Attack) beside reduced A/B/C (Attack v2), sword
  shown; `run_creature_review.py check`: 54 switches, no console errors.

## Open issues

- LOD3 (491 triangles) breaks the hair strands over the face a little more than installed LOD3 (`review/lods/sheet.png`).
- The source hair has two small holes at the back of the head; unchanged.

## Status

Installed 2026-10-19 after user review ("dark elf warrior ok", Attack v2 round 2) with
`tools/install_model.py --world mm8 level_generation/creatures/mm8_m432_reduce_claude/export/mm8_m432.glb`.
`OPENYAMM_REGRESSION_FILTER=mm8_dark_elf_warrior_actor_models ./build/game/openyamm --headless-run-regression-suite actors`:
`mm8_dark_elf_warrior_actor_models_keep_native_roles` passes (`review/regression.log`). Recorded in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_m432_source_pre_reduce.glb` with
`tools/install_model.py --world mm8`.

Reproduce: `import_source.py` (REA_NODE=M432, REA_GLB=the rollback source) -> `REA_PROTECT=Head dump_mesh.py`,
`dump_groups.py`, `extract_basecolor.py` -> `REA_SMALL=80 small_pieces.py` -> `m432_regions.py` ->
`M432_KEEP_FACE=1 m432_sets.py b` (copied to d) -> `REA_GROUP_RATIOS=3:0.7,5:0.5,6:0.5,7:0.6,9:0.55` ladder d ->
`texture_drift.py r75`, `drift_lock.py work/keep_d.npy work/keep_e.npy r75` ->
`cuff_keep.py work/keep_e.npy work/keep_f.npy` -> `REA_KEEP_FACES=work/keep_f.npy REA_GROUPS=work/groups_f.npy run_ladder.sh f 0.7579`
(`totals.py` computes the ratio) -> build as above -> `grip_check.py`, `lod_check.py` (REA_NODE=M432),
`lod_views.py`, `glb_close.py`, `viewer_variants.py`, `viewer_sword.py`, `viewer_manifest.py`.

## Floor fix — 2026-10-21

`--ground-death Death Dead`: the falling body went up to 0.097 m (11.7 world units) under the floor between 1.4 and 2.0 s; those keys are raised onto it, and the corpse is lowered 9 mm onto the floor. Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to `export/mm8_m432.glb` (previous export in
`work/floor_fix_base/`) and installed; only animation samplers changed. The editable `.blend` master predates it:
rerun the same operation after any re-export.

## Gait rollout (2026-10-31, package h18)

New in-place locomotion clips appended to the installed source (every existing clip, mesh, skin and material
byte-identical): `Walk2` (Armed-Walk legs, 0.92 s, stride 1.9152) and `Jog` (Unarmed-Run-Forward legs, 0.65 s, stride 2.6637); `Running` becomes the MAW sprint (x1.19-1.25). Arms, hands and props come from this model's own fitted clips. Built, gated and installed in
[../gait_rollout_20261031/h18/](../gait_rollout_20261031/h18/README.md); bindings for the coordinator in its
`bindings.yml`. Rebuild: `level_generation/creatures/gait_rollout_20261031/h18/scripts/rebuild.sh m432`; rollback:
install `../gait_rollout_20261031/h18/work/mm8_m432_pre_gait.glb`. A far-LOD repair, head-bob, floor-fix or reduction
rerun on this model must re-graft these clips (copy the new source over the pre-gait copy and rebuild).
