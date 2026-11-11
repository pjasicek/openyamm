# MM9 Dwarf (`mm9_dwarf`) reduction

## Fix pass (2026-11-04 evening): chart-guarded r40, ready for review — current candidate
The r71 candidate below was installed and **rolled back**: 67 of its LOD0 faces (limbs 26: back of the boot shafts; torso 41:
sleeves and upper arms, both sides) had UV triangles leaving the painted charts (`review/uv_audit_e71.json`). MeshLab's
collapse cannot be guarded per collapse, so the fix pass uses the pose-aware half-edge collapse with the chart guard
(`scripts/mpqem.py`, the Giant's copy of the Mummy's: `MP_CHART=1`, every sample of a new face's UV triangle must lie on the
installed charts; texture guard on the three tier base colours baked from the ramps, `tex_extract.py`; 5-D texture weight
`MP_W5=4`; the axe primitive kept whole). Every output corner is an installed vertex, so positions, UVs, normals and weights are
exact. Same keep set as r71 (`work/keep_e.npy` -> `glb_sets.py` e), same group ratios (beard 0.7, helmet 0.75, horns 0.7, pants
0.85, left hand 0.75).

`SETS=e MP_GROUPS=1:0.7,2:0.75,3:0.7,4:0.85,5:0.75 MP_W5=4 scripts/run_mp.sh a 0.5,0.4,0.3`, then `scripts/build_mp.sh mp_a_r40`
(-> `export_mp/mm9_dwarf.glb`):

| step | LOD0 | p99 / max mm | IoU / SSIM | |
|---|---:|---|---|---|
| r50 | 10,611 (-22 %) | 2.18 / 10.7 | 0.998 / 0.994 | pass |
| **r40** | **10,193 (-25.3 %)** | **3.74 / 14.0** | **0.995 / 0.993** | **pass, picked** |
| r30 | 9,927 (guards stop the cut; -27 %) | 7.59 / 28.1 | 0.993 / 0.987 | fail |

LODs 10,193 / 5,094 / 1,830 / 717 (installed 13,643 / 6,817 / 2,452 / 813), every LOD 1.322 m tall, 0 stretched faces, lowest point
over every clip LOD0 -2.9 cm as installed. **UV audit (`review/uv_audit.json`): 0 escaping LOD0 faces in every primitive.** LOD1-3
escapes come from Blender's decimate as in the installed file (LOD1 limbs 121 vs 114, torso 67 vs 26, head 85 vs 56; LOD2/3 at or
below the installed counts). Clips, skin, nodes, materials, images and variants are the installed bytes (`same_clips.py`).

Gates (`review/gates_before/` vs `review/gates_mp40/`): skirt through Death2 2.1 cm both, skirt faces < 50 % max 2 both, arm/hand
3.0 / 1.5 cm both, jitter the same 6 fails (shoulder skin within ±0.07 mm/f2), grip identical, blade identical (2.1 cm Fidget2),
rim helmet 0.7 -> 0.4 cm, face/beard 0.7 both, beard stretch 1.00, wrist gap 0.97 both, bone length 0, orient 4.6 deg both,
collapse sum 81,050 -> 48,665 face-frames, detached 1 (axe head) both, flat shading 0.00/0.02/0.00 both, texture atlas
57.1/55.1/63.8 % as installed, winding 0. Viewer check 102 switches, 0 errors.

Sheets read (installed above, reduced below): `review/sheet_escapes_{a,c}_tex.png` (sleeves/upper arms outer, front, back, both
sides, and the boot shafts from behind: where r71 escaped), `review/sheet_face_b_tex.png`, `review/sheet_body_a_tex.png`,
`review/sheet_viewer_a.png`. Generated, not opened: `sheet_escapes_b_*`, the other face/body/viewer tiers and clay versions.

# Earlier candidate (rolled back): r71, MeshLab ladder


Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 monster,
relaxed keep set), ledger row 21. Lease `mm9reduce:dwarf` (owner dwarf-reduce-20261104). No-retexture branch of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) on the installed r18 (`assets_source/worlds/mm9/models/mm9_dwarf.glb`,
sha256 2bc9e109af9f, copied to `before/`, the rollback source). The creature project `../mm9_dwarf_claude/` was only read.
**Not installed.** No Meshy credits.

| | LOD0 | LOD1 | LOD2 | LOD3 | LOD3 height |
|---|---:|---:|---:|---:|---:|
| installed r18 | 13,643 | 6,817 | 2,452 | 813 | 1.262 m (spike lost) |
| candidate r71 (`export_e/mm9_dwarf.glb`) | **9,683 (-29 %)** | 4,839 | 1,737 | 718 | 1.322 m (= LOD0) |

LOD0 per set: limbs 3,498 -> 2,854, torso 5,888 -> 3,306, head 3,893 -> 3,159, axe 364 (byte-identical primitive).
Clips, images, materials, tier variants, region masks and nodes are byte-identical to the installed file (checked by hash).

## Keep set (measured first: 44.5 % with the full brief set, 37.6 % in the final one)
Per-face labels from the creature's final rest mesh (`scripts/dump_parts_blend.py` on `../mm9_dwarf_claude/work/final_v1.blend`,
matched to the GLB faces exactly; `scripts/make_sets.py`, `scripts/extra_keep.py`):
- **exact:** face skin, eyes, neck tube (head parts 20 non-beard, 22, 24); right hand whole (grip); left glove's graft junction
  (2 cm inside the bracer); skirt (outer, lining, hinge/SkirtLeg gates), boot cuffs with linings, belt, shoulder plates; the
  bracer ends that carry hand weight (wrist-gap gate); soles (6 cm); the axe; small pieces; error locks (`err_lock.py` at r72:
  armpits/side chest) and the second-round spots (chin underside and collar front for `rim_gate` face/beard, forearm faces
  the axe touches in script Fidget2).
- **cut on their own:** beard 0.7, helmet 0.75, horns 0.7, pants 0.85, left hand 0.75 (relaxed prio-1 rules); the rest
  (voxel tunic/sleeves/forearms, boots) in the shared texture-aware collapse with UV weights (`REA_WEIGHTS=component`).

## Ladder (height 1.33 m: p99 <= 3.99 mm, max <= 19.95 mm)
| run | keep | step | LOD0 | p99 / max mm | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| b | brief set, hands kept | r77 | 10,503 | 1.99 / 13.6 | 0.998 / 0.994 | pass |
| b | | r74 | 10,093 | 2.51 / 48.6 (Dead) | | fail |
| d | + err locks, hands/beard cut | r70 | 9,547 | 3.19 / 14.1 | 0.996 / 0.991 | pass (first candidate) |
| d | | r68 | 9,273 | 4.83 / 21.2 | | fail |
| **e** | **+ right hand, rim and axe spots** | **r71** | **9,683** | **3.61 / 16.2** | **0.996 / 0.991** | **pass, picked** |
| e | | r70 | 9,547 | 4.52 / 16.2 | | fail |

r70 of run d regressed three gates (rim face/beard 0.0 -> 2.3 cm in AttackMelee, grip pinky wrap 120-135 -> 90 deg, blade
2.1 -> 2.3 cm); run e keeps those spots and every gate matches the installed model again.

## Export chain (`scripts/build_export.sh`, `EXPORT=export_e REA_KEEP=work/keep_e.npy REA_BLEND=ladder_e.blend ... Cand_71`)
`export_cand.py` (floor = source's lowest point) -> `swap_lod0.py` (`KEEP_PRIMS=DwarfWeapon`: the axe primitive stays as
installed with its hard-edge split vertices) -> `keep_normals.py` (source normals on vertices used only by kept faces; among
coincident split vertices the one with the closest normal) -> `build_lods.py` (tools/build_actor_lods.py ratios, 4 influences,
protected helmet spike, horn tips, soles and the skirt's front/back SkirtLeg hand-over: the default LODs lost 9 cm of spike
on LOD3 and stretched one skirt-side face 20-60x in LOD2/3) -> `shrink_shadow_lods.py` -> `carry_variants.py` -> winding.

## Gates (`scripts/gates.sh`, the creature's own gate scripts copied here; `review/gates_before/` vs `review/gates_e71/`)
| gate | installed | r71 |
|---|---|---|
| skirt through, worst | Death2 2.1 cm | Death2 2.1 cm |
| skirt faces < 50 % | max 2 | max 2 |
| arm/hand (`--outer-only --exact`, also NOCLOTH) | hand 3.0, forearm 1.5 cm (script Fidget2 only) | same |
| jitter vs MM9 clips | 6 fails (shoulder skin, Walking/Running/AttackRanged/Death; this reference build) | same 6, values within ±0.15 mm/f2 |
| grip | inside 0.3 cm, wraps unchanged | identical text |
| blade (axe vs skin) | Fidget2 2.1, AttackMelee3 0.8 cm | 2.1, 0.7 cm |
| rim helmet/horns, face/beard | 0.7 / 0.7 cm | 0.7 / 0.7 cm |
| beard edge stretch | 1.00 | 1.00 |
| wrist gap | worst 0.97 cm | 0.97 cm |
| collapse face-frames / exposed (sum) | 81,050 / 1,058 | 37,573 / 449 (fewer faces) |
| bone length, handedness, orient | 0 stretching; right; head <= 4.6 deg | same |
| LOD heights, stretch over 20x, min z | LOD3 1.262 m; 0; -0.033 m | all 1.322 m; 0; -0.029 m |
| detached parts | 1 (axe head on RHand1, by design) | same; shallow list as before plus two calf/skirt contacts under 5 mm in Running |
| flat shading | limbs 0.00, torso 0.02, head 0.00 | 0.00, 0.01, 0.00 |
| texture quality (atlas, UV stretch p90) | torso 55.1 %, 1.43 | 54.2 %, 1.66 (head unchanged) |
| winding | 0 | 0 |

## Sheets (read)
`review/sheet_face_{a,b,c}_{tex,clay}.png` (front, 3/4, profile, low 3/4, party, back of head; installed above),
`review/sheet_body_{a,b,c}_{tex,clay}.png` (chest, back, boots, both fists, attack, corpse), `review/sheet_viewer_{a,b,c}.png`
(viewer: Standing front/3-4/back, Walking, Running, AttackMelee, Death, hands, arms in the attack), `review/ladder_sheet.png`.
Face skin is unchanged (pixel difference map `work/diff_face_front.png`: only beard, helmet edge and tunic differ).
Viewer: http://127.0.0.1:8912/level_generation/creatures/mm9_dwarf_reduce_claude/review/viewer/index.html (installed and r71
per tier; `check_viewer.mjs` 102 switches, 0 errors).

## Not checked
In game; LODs by eye (numbers only); the binding regression and floor audit (run after install); the viewer's head-focus
shots frame above the helmet for both models (viewer camera, not the mesh), so faces were read from the Blender GLB close-ups.
Blender's clay of the axe shades differently from the installed file although the primitive is byte-identical (import
normals); judge the axe in the viewer.

## MM9 sockets (2026-11-10)

The installed model carries MM9's attach points as `Socket_<name>` nodes for held items (scene `held_items`, MM9's AttachProp), added after this project's install by [`mm9_held_items_claude/scripts/add_sockets.py`](../../props/mm9_held_items_claude/scripts/add_sockets.py) (`Socket_RHand1`). A rebuild installed from here drops them: run that script again and install its export (`tools/install_model.py --world mm9`).
