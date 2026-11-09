# MM9 PeasantF1 (`mm9_peasantf1`, the older townswoman in a hood) reduction: candidate e50 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk: the
relaxed keep set, face exact), ledger row 14 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantf1`
(owner peasantf1-reduce-20261104); the creature's own `mm9:peasantf1` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantf1.glb` (sha256 e07f87e9b75c, identical to `../mm9_peasantf1_claude/export/`), copied
to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantf1_claude/` was only read.

| | LOD0 | head prim (face/neck/eyes/teeth 3,612 + hood 1,150) | dress | skirt | lining | legs | arms + hands | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| installed | 14,474 | 4,762 | 2,598 | 1,358 | 1,426 | 760 | 3,570 | 7,105 | 2,556 | 885 |
| **e50 (`export/mm9_peasantf1.glb` = `export/mm9_peasantf1_e50.glb`, sha256 6c13a1e4d869)** | **10,818 (-25.3 %)** | 4,762 (exact) | 1,898 | 746 | 814 (746 + rim 68) | 608 | 1,990 | 5,257 | 1,891 | 846 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). The head primitive keeps every installed vertex and triangle (same set, only the triangle order differs), so face
and hood render pixel-identical in both tiers. Clips (11), skin, nodes, materials, region ramps/mask, `KHR_materials_variants`, all
8 images: byte-identical (`same_clips.py`).

## Measured first: protected share
Part labels from the creature's last pre-GLB mesh (`../mm9_peasantf1_claude/work/uv_tex2.npz`, `scripts/glb_parts.py`: matched by
UV + position centroid, every face at distance 0). Keep set c (`scripts/make_sets_pf1.py`, `HOODHEM=0.02`): head part 3,612, hood
edge (8 mm of the face) 234 + hood hem (2 cm of its open boundary) 202, collar 134, both short sleeves (|x| > 15 cm, PeasantF3's
lesson) 840, soles 256, small pieces (lacing) 226, lining rim 68 = 5,572 (38.5 %). Ladder e then keeps the whole hood (group 2 at
1.0), so 41 % of the installed faces are exact. The cut comes from the MPFB arms/hands, the skirt (with its lining), the bodice and
the hidden legs.

**Skirt lining re-emitted, not kept.** F1's lining (`assemble_pf1.lining`) is the skirt's exact twin: lining face k = skirt face k
reversed, every vertex 4 mm in along the skirt's vertex normal (1,358 of 1,358 skirt faces matched corner by corner, offset 3.99-4.00
mm), plus a 68-face hem rim. The lining has UV seams of its own (84 positions where the skirt has none), so `scripts/mpqem.py` (this
project's copy) carries each skirt face's twin per lining UV island (7 islands): a collapse is refused when a moved face's new corner
has no twin in that island or when the twin UV triangle flips or leaves the charts; the lining is re-emitted from the surviving skirt
faces (0 twin-key clashes), the rim kept exactly. Lining 1,426 -> 814 with every lining gate number equal to the installed model's.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, from PeasantF3's)
Texture guard over each tier's baked body colour, each tier's head image and the region mask (`scripts/tex_extract.py`); chart guard
(`MP_CHART=1`, sampled at 12); texture weight 4 (`MP_W5`); seam slides on the hands (`MP_SEAM_GROUPS=1`). Scored over every clip at
10 Hz plus a position+UV rest quadric. Groups: hands + fingers 0.6 (every finger kept), arm skin 0.45, skirt 0.55 (lining follows),
shoes 0.6, hidden calves 0.85, hood 1.0 (e), bodice at the ladder ratio.

## Ladders (limits for 1.792 m: p99 <= 5.38 mm, max <= 26.9 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | change | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---|---:|---|---|---|
| a | set a, hood/skirt/shoes 0.7 | r50 / r45 | 10,980 / 10,910 | 2.67 / 15.0 (Hit), 3.38 / 25.6 (Conv3) | .998 / .996 | pass; a50 built, every gate equal or better |
| b | a, skirt 0.55, hood 0.65, shoes 0.6 | r50 | 10,496 | 2.97 / 15.0 | .997 / .996 | pass; gates = a50; **sheets: hood hem shaded as a dark band** (profile and from behind) |
| c | b + hood open-boundary hem kept (2 cm) | r50 | 10,568 | 2.94 / 15.0 | .997 / .996 | pass; dark band unchanged: the hem is mostly a closed rolled fold (underside faces + inner layer), cut faces next to it interpolated its down-turned normals; keeping the fold alone would hold 70-77 % of the hood |
| **e** | **c, hood kept whole** | **r50** | **10,818** | **2.91 / 15.0 (Hit:18)** | **.997 / .996** | **PASS, picked**: head primitive exact, sheets show no change |

UV audit (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_e50.json`): **0 LOD0 faces leave the charts** in both primitives.
LOD1-3 (tool-built): body 127 / 110 / 14, head 73 / 92 / 21 escaping (installed LODs: 90 / 129 / 110 and 75 / 84 / 22).

## Gates, installed -> e50 (F1's own scripts via `scripts/gates.sh`; `review/gates_before/`, `review/gates_e50/`)
- Collapse face-frames lower in every clip (Standing 1,612 -> 1,212, Hit 5,356 -> 4,647, Death 2,506 -> 2,039, Cower 3,564 -> 2,511).
- Robe (legs through the skirt): 0 in every clip, both. Sleeve poke (`sleeve_poke_pf1.py`): 0 mm in every clip, both (the cut arm
  stub leaves 70/69 candidate vertices instead of 114).
- Arm/hand (`--outer-only --exact`): 0 frames > 1 cm in every clip, both; hand depth 0.2 cm both; finger-stretch maxima equal
  (Fidget R 3.3), minima up 0.02-0.1.
- Skirt lining through the skirt (`scripts/lining_gate.py`): every clip's largest outward distance and frame count identical
  (installed max Running 28.0 mm at the hem rim); Death most vertices out 8 -> 7.
- Jitter vs the creature's `ref_half.glb`: 2 fails both (Death shoulder skin 45.21 -> 45.14 mm/f2, the installed model's own).
- Detached parts: 13 components, the same 2 (the legs, by design), same worst distances. Flat shading 0.00/0.01. Winding 0.
  Bone lengths 14 checked, 0 stretching. Texture quality unchanged (body stretch p90 1.05 -> 1.06, head 1.34).
- See-through (`scripts/see_through.sh`, PeasantF3's `see_through_gate.py`, every clip, 16 views; `scripts/see_summary.py`; hole max
  px, level / 20 deg): torso 1559/122 -> 1533/122, sleeve L 2001/24 -> 1910/21, sleeve R 24/14 -> 22/14, head 71/37 -> 71/43,
  collar 896/23 -> 977/23, boots 0 both. The large ones are the installed construction (Death/Dead seen from the feet at ground level,
  up the open skirt into the hollow dress; `review/see_collar_dead_death_e50.png`: same opening, small changes at its edge). Rises:
  collar Death 896 -> 977 and Dead 100 -> 153 px (that ground-level view only, same frames), elsewhere 1-4 px in single views
  (Conv3 sleeve L 25 -> 29, Talk sleeve R 18 -> 21).
- LODs (`scripts/lod_check.py`, every frame of every clip; `scripts/lod_summary.py`, `work/lod_check_{installed,e50}.json`), built by
  `scripts/build_lods.py` (tool defaults 0.5/0.18/0.06, 4 influences; soles, crown and corpse contact protected, each point snapped to
  the imported vertex): height 1.788 m at every LOD (installed LOD3 1.784); every clip's lowest point at LOD1-3 equal to LOD0
  (installed LOD3 floated +0.4-0.9 cm, Hit +0.94, Walking +0.82); stretched faces fewer at every LOD (LOD0 29 -> 23, LOD1-3 13 -> 10).

## Review
Viewer (installed and reduced, both tiers, all 11 clips; `run_creature_review.py check`: 44 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf1_reduce_claude/review/viewer/ (revision r3-e50-20261104)
Sheets read: `review/sheet_face_e50.png` (front close-up, 3/4, true profile, low 3/4, party; both tiers), `review/sheet_face_diff_e50.png`
(face and hood black in all views; only bodice/shoulder shading below the collar), `review/sheet_body_e50_{a,b}.png` (Standing
front/3-4/back, Walking, Talk, Death), `review/close_e50_{a,b}_hands.png`, `review/close_e50_{a,b}_1.png` (arms, skirt front/back,
Running skirt), `review/close_e50_{a,b}_2.png` (feet, Talk, hood and shoulders from behind, Hit, hood top), `review/crop_bodice_party_e50.png`
(bodice, embroidery and lacing at full size), `review/crop_hood_profile_{b50,c50}_b.png` (the rejected hood cuts), `review/ladder_sheet_{a,b}.png`.
Look at: the fingertips (hands 0.6: very slightly more angular tips), bodice shading at the sides of the chest (same paint), the
skirt hem in Running and Death.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantf1_reduce_claude/before/mm9_peasantf1.glb REA_NODE=PeasantF1 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py
HOODHEM=0.02 $G scripts/make_sets_pf1.py c
MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=c MP_GROUPS=1:0.6,2:1.0,3:0.55,4:0.6,5:0.45,7:0.85 scripts/run_mp.sh e 0.5
scripts/build_mp.sh mp_e_r50 export/mm9_peasantf1_e50.glb   # swap_mp -> build_lods (protected, snapped) -> shrink_shadow_lods -> carry_variants -> fix_winding
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantf1_e50.glb before/mm9_peasantf1.glb --json review/uv_audit_e50.json
scripts/gates.sh export/mm9_peasantf1_e50.glb e50; $G scripts/lining_gate.py export/mm9_peasantf1_e50.glb review/gates_e50/lining.json
scripts/see_through.sh export/mm9_peasantf1_e50.glb e50; REA_NODE=PeasantF1 $BL -P scripts/lod_check.py -- $PWD/export/mm9_peasantf1_e50.glb e50
$G scripts/face_exact.py export/mm9_peasantf1_e50.glb c
$G scripts/viewer_tiers.py export/mm9_peasantf1_e50.glb rede50   # installed: viewer_tiers.py before/mm9_peasantf1.glb inst
$G scripts/make_viewer_manifest.py <rev> inst_b=..=work/viewer_inst_th_b.glb red_b=..=work/viewer_rede50_th_b.glb inst_a=.. red_a=..
scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py e50; $G scripts/face_diff_sheet.py e50
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantf1.glb` (0), `tools/install_model.py export/mm9_peasantf1.glb
--world mm9`, the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_peasantf1_claude/README.md`: "LOD0 reduced
post-install on <date> by `mm9_peasantf1_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback:
`before/mm9_peasantf1.glb`. Fre (built on F1/F4 parts) was not touched.

Other builds in `export/` (a50, b50, c50) are the rejected ladder steps, kept for reference.

## Not checked
In game (not installed; binding regression skipped per the orchestrator: unrelated failure, it runs it after install; floor audit
after install); motion at normal speed by eye (frames, gates and viewer stills only); LOD1-3 and shadow meshes by eye (numbers only).
