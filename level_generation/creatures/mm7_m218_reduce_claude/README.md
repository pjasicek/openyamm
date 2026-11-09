# MM7 Elf Spearman (`m218`, Elven Warrior / Defender / Lancer) reduction (2026-10-20)

User: "do the tris reduction playbook on these 5" (the five MM7 batch-C humanoids; this project is m218 only).
Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab
ladder that keeps the UVs, so the textures, the three tier variants (`KHR_materials_variants`) and the region ramps
stay valid. No Meshy credits. **Not installed.**

[Review viewer](review/viewer/index.html) (source vs reduced, tiers A/B/C, all eight clips, spear in its socket)

## Source

`../mm7_m218_claude/export/mm7_m218.glb` and `mm7_m218_spear.glb` (accepted 2026-10-20), copied to
`work/mm7_m218_source_pre_reduce.glb` and `work/mm7_m218_spear_source_pre_reduce.glb` (rollback sources). One merged
body + head atlas material per tier (`Elf_A/B/C`, 2080x1024, head half u > 0.51), node `Elf`, 57 joints, 4 influences
at LOD0 (8 slots at LOD1-3), shadow LODs, clips Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget. Bind
height 1.803 m (crown leaves). Weld: 6,930 -> 1,420 open edges (crown-leaf cards, loincloth panels and other open
pieces), 9 coincident vertices with other weights (kept apart), 9,586 triangles in and out (no two-sided sheets).
Scripts start from `../mm7_m406_reduce_claude/scripts/` (same pipeline, batch A).

## Where the triangles are (`scripts/m218_pieces.py`, `review/labels/pieces.png`)

| piece | faces | |
|---|---:|---|
| head skin (face, ears, hair shell; head texture set) | 2,701 | 1,994 visible, 707 never visible (inner hair shell, sockets) |
| hands (fingers; both fists are solved on the spear) | 2,054 | kept exactly |
| crown leaves (~75 thin leaf cards) | 1,090 | kept exactly |
| body skin (neck down, one shell with the head) | 1,045 | already coarse: 4-7 cm edges |
| eyes and mouth pieces | 708 | 513 faces never visible (eyeball backs, mouth inside) |
| bracers (3 pieces) | 449 | |
| belt (2 pieces) | 400 | kept exactly |
| other small pieces (loincloth tabs, necklace, pouch flap) | 325 | kept exactly |
| back shaft (slung second shaft, rigid B_Spine2) | 300 | |
| loincloth panels with their tabs | 282 | kept exactly |
| hip pouch | 136 | |
| ponytail | 96 | kept exactly |

The source build already reduced everything except head, hands and crown leaves (14.5k Smart Topology -> 9.6k), so the
body skin has no room left: cutting it to 90 % (88 triangles) put 20-26 mm errors on knees, calves, back and armpit
in Running, Death and Attack (`probe_max.py`, ladders a/b/g). Hands, crown leaves, eyes, belt, loincloth and the small
pieces were to be kept by the brief, which leaves about 3,000 faces to cut from: the head skin, bracers, back shaft,
pouch and the hidden eye/mouth faces.

## Keep set and groups (`scripts/m218_sets.py` + `scripts/head_keep.py`, pick = set `h`)

Kept exactly (`work/keep_h.npy`, 6,038 faces): hands; every face touching a vertex with hand + finger weight > 0.3
(bracer ends); the visible eye and mouth faces; crown leaves; belt; loincloth panels; ponytail; all other small
pieces; soles (body faces below 6 cm); head skin within 2 cm of the eye/mouth pieces (sockets, lips); 2.2 cm patches
around eyes, nose and mouth; both ears (3.5 cm around each ear's outermost point) and the hairline plus the painted face
lines (head-skin faces within 1.2 cm of both a dark and a light base-colour face) (`head_keep.py`; the first pass at
50 % flattened an ear and notched the temple hairline, `review/glbclose/sheet_c87.png`). The visibility split is
`scripts/visibility.py` (face-id z-buffers from 42 sphere directions, those more than 15 degrees below the horizon
dropped).

| group | faces | ratio |
|---|---:|---|
| 1 face front (visible head skin in front of y = -0.03 m, below 1.64 m) | 224 | 80 % |
| 2 visible rest of the head skin (hair, jaw sides, neck) | 748 | 60 % (45 % flattened the back of the hair 13-19 mm) |
| 3 hidden head skin (inner hair shell) | 304 | free part, 100 % (at 65 % it poked a lump through the hair above the ear, `sheet_h89_head.png` f88 column) |
| 4 bracers | 449 | 85 % (60 % slid the woven texture) |
| 5 back shaft | 300 | 40 % |
| 6 hip pouch | 136 | 50 % |
| 7 never-visible eye/mouth faces | 513 | 40 % (every visible face of the pieces kept) |
| 0 body skin | 1,045 | free part, 100 % (unchanged; 1,037 of its faces are identical, 8 at the neck border were re-split) |

## Ladder (limits for the 1.803 m height: p99 5.41 mm, max 27.04 mm; IoU >= 0.98, SSIM >= 0.93)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 9,586 | | | | |
| a: hair 55 %, hidden 45 %, bracers 55 %, shaft 35 %, body 90-70 % | r86 / r85 | 8,316 / 8,228 | 4.89 / 20.53, 5.75 / 25.93 | 0.989 / 0.984 | | pass / fail; body and hidden scalp dominate |
| b: hair 60 %, hidden 60 %, bracers 70 %, shaft 50 %, body 100 / 90 % | r90 / r89 | 8,636 / 8,550 | 2.85 / 6.78, 3.22 / 20.53 | 0.996 / 0.994 | 0.997 | pass |
| c: hair 50 %, hidden 50 %, bracers 60 %, shaft 40 %, body 100 % | r87 | 8,402 | 4.05 / 10.83 | 0.9904 | 0.9961 | pass; ear flattened, hairline notched, bracer weave slid |
| d: c + ears/hairline kept, face 80 %, hidden 65 %, bracers 85 % | r91 | 8,744 | 3.47 / 11.71 | 0.9927 | 0.9971 | pass |
| e: d + hidden eye/mouth faces 40 %, hair 45 % | r87 | 8,398 | 4.01 / 19.69 | 0.9906 | 0.9965 | pass; back of the hair flattened |
| f: e with hair 60 % | r88 | 8,510 | 2.82 / 7.61 | 0.9929 | 0.9973 | pass; inner hair shell poked a lump above the ear |
| g: f with body 90 / 80 % | r87 / r86 | 8,422 / 8,334 | 3.27 / 20.53, 3.89 / 25.93 | 0.992 / 0.987 | | pass, body errors 20-26 mm (no gain worth it) |
| **h: f with the hidden head skin kept** | **r89** | **8,616** | **2.74 / 7.61** | **0.9929** | **0.9973** | **pick** |

The pick is the lowest step that also looks right in the close-ups: e and f were lower but showed the flattened hair
back and the lump above the ear. Texture drift (`texture_drift.py h_r89`): no face over 40, p99 8.3; the largest (15-29)
are on the bracers at 85 %, invisible in the close-ups, so no lock round. The cut is small (-10.1 %) because
hands, crown leaves, eyes, belt, loincloth and the small pieces (5,500 faces, 57 % of the mesh) are kept by the brief
and the body skin is already at its floor.

## Build

`REA_KEPT_NORMALS=1 cand_glb.sh h Cand_89 kn` (`kept_normals.py`: source GLB normals on the 23,436 corners of unchanged
source faces and on 1,118 kept smooth vertices, computed smooth normals on 1,294 corners) -> `export_cand.py` ->
`swap_lod0.py` (`work/h89_lod0.glb`) -> `crown_points.py` (8 crown-leaf top/spread points) and `floor_points.py` (24
Dead/Death floor contacts) -> `build_lods.py` (`tools/build_actor_lods.py`, 8 influence slots as the source, ratios
0.5 / 0.196 / 0.0625, 32 protected points) -> `shrink_shadow_lods.py` (source project's script: shadow LODs inset as in
the source export) -> `carry_variants.py` -> `check_winding.py` (0 inverted closed parts): `export/mm7_m218.glb`,
6.00 MB (source 6.10 MB).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source body | 9,586 | 4,775 | 1,692 | 541 |
| reduced body | 8,616 | 4,285 | 1,654 | 504 |
| spear (`export/mm7_m218_spear.glb`, byte-identical copy) | 486 | 242 | 86 | 27 |

LOD ratios: 0.196 / 0.0625 keep LOD2/LOD3 just below the source's counts (the default 0.18 / 0.06 on the smaller LOD0
would have cut them to ~1,550 / 517). 48 floor points instead of 24 made LOD3 Dead worse (-17 mm), so 24 stay.

Checks:
- `scripts/compare_glb.py`: node names and transforms, skin and inverse binds, materials and extras, images, textures,
  samplers, all eight clips (sampler data), mesh names/extras and the variants extension are identical to the source;
  `KHR_materials_variants` (m218_a/b/c) on all 8 colour/shadow primitives. One difference the check does not cover:
  the shadow meshes now carry the atlas UVs of LOD0 (the source's shadow UVs stayed in the body half, u <= 0.49);
  the material is opaque, so shadows do not sample them.
- `scripts/grip_check.py` (`work/grip_check.log`): all 1,486 LOD0 vertices with hand + finger weight > 0.5 keep their
  bind positions (max 0.0003 mm) and weights exactly, so both solved spear fists are unchanged.
- `scripts/arm_torso_probe.py` (the source project's probe, copied; reads GLBs; `work/arm_torso.log`), all clips of
  source and reduced export: Attack right upper arm 0.6 cm at worst (both), Death left forearm 0.5 / 0.4 cm at frame 24
  (the known lying frame), everything else 0.0; nothing over 1.5 cm. The copy adds a tie rule (a nearest point on a
  shared vertex/edge uses the mean normal of all faces there): without it the probe reported 9.1 cm at Death frame 19
  on the reduced file only, from the BVH picking another face of the same unchanged corner (both faces exist in both
  meshes; the body skin there is identical).
- `work/lod_check_{src,h89}.json`: every LOD keeps the 1.800 m top and the source's bounds; lowest point per clip equals
  the source's at LOD0/1 in every clip (within 0.6 mm) and is within 0.2-3.5 mm of the source's LOD2 (Dead -0.7 vs -4.2 mm); LOD3 Dead lies 8.6 mm under
  the floor (source 3.4 mm above), LOD3 Hit -13.8 mm (= LOD0; source LOD3 -6.8). No face stretches over 20x in any
  frame of any clip at any LOD. The Death minimum of -0.257 m is the same in source and reduced file at every LOD
  (a pre-existing low point of the source while lying; not touched).
- Close-ups straight from the GLBs, source vs pick, textured and clay (`scripts/glb_close.py`, `glb_sheet.py`):
  `review/glbclose/sheet_h89_head.png` (face, three-quarter, side with the ear, back of the head, crown leaves),
  `sheet_h89_body.png` (vines on chest and back, shoulder, bracer, loincloth front/back, hip side),
  `sheet_h89_limbs.png` (both fists, legs, feet, Attack front and side, Death),
  `sheet_h89_tiers_spear.png` (viewer GLBs with the spear in the fists: tier A source vs A/B/C reduced),
  `sheet_c87.png` (the rejected 50 % head cut). Label renders in `review/labels/`, ladder sheets
  `review/ladder_sheet_<config>.png`, LOD renders `review/lods/sheet.png`.
- Viewer: `review/viewer/` (source vs 89 % pick, tiers A/B/C, spear added under the `Spear` joint for review only by
  `viewer_spear.py`); `python3 tools/run_creature_review.py --project
  level_generation/creatures/mm7_m218_reduce_claude --token <lease> check`: 48 switches, no console errors.

## Open points for review

- The cut is modest (9,586 -> 8,616, -10 %). More would need cutting the crown leaves (1,090), the hands (2,054) or the
  already-coarse body skin, which the brief keeps or which fails the error limits.
- In clay, a faint crease runs down the jaw behind the cheek (face 80 % / sides 60 %); textured it does not show.
- LOD3 (504) is as crude as the source LOD3 (541): head blocky, crown sprigs thin; it lies 8.6 mm into the floor in Dead.
- The spear was left byte-identical (486 triangles; a clean procedural mesh both fists grip).

## Install (not run; user decision)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m218_reduce_claude/export/mm7_m218.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m218_reduce_claude/export/mm7_m218_spear.glb --world mm7
```

then the binding from `../mm7_m218_claude/README.md` (unchanged by this reduction) and a
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) row. Rollback: install `work/mm7_m218_source_pre_reduce.glb` (+
`work/mm7_m218_spear_source_pre_reduce.glb`) the same way. After any later re-export of the source clips:
`python3 scripts/transplant_clips.py ../mm7_m218_claude/export/mm7_m218.glb export/mm7_m218.glb export/mm7_m218.glb`.

## Reproduce

`REA_GLB=level_generation/creatures/mm7_m218_reduce_claude/work/mm7_m218_source_pre_reduce.glb REA_NODE=Elf
import_source.py` -> `dump_mesh.py`, `dump_groups.py`, `extract_basecolor.py work/mm7_m218_source_pre_reduce.glb` ->
`m218_pieces.py` -> `REA_MIN_PIX=6 visibility.py 1.40 1.81` (copy to `work/visible_head.npy`) and
`visibility.py -0.01 1.81` (`work/visible_all.npy`) -> `head_keep.py work/head_keep.npy` ->
`M218_EYE_HIDDEN=1 M218_EXTRA_KEEP=work/head_keep.npy m218_sets.py e` (copy `keep_e`/`groups_e` to `keep_h`/`groups_h`)
-> `TOKEN=<lease> run_ladder.sh h h "1:0.8,2:0.6,4:0.85,5:0.4,6:0.5,7:0.4" 1.0` -> `texture_drift.py h_r89`,
`region_error.py`, `probe_max.py` -> `REA_KEPT_NORMALS=1 cand_glb.sh h Cand_89 kn` (copy `work/glb_h_89kn.glb` to
`work/h89_lod0.glb`) -> `crown_points.py`, `REA_NODE=Elf floor_points.py` -> build as above -> `compare_glb.py`,
`grip_check.py ... Elf`, `arm_torso_probe.py <glb> Attack Death ...`, `lod_check.py` (REA_NODE=Elf), `lod_views.py`,
`glb_close.py`, `viewer_variants.py`, `viewer_spear.py`, `viewer_manifest.py "MM7 Elf Spearman" r89 9586 8616`.
Blender scripts run through `scripts/bl.sh` (lease wrapper, `TOKEN`).

**Installed 2026-10-20** (user acceptance) with `../mm7_batches/BATCH_C_stage/install.sh`; bindings in `../mm7_m218_claude/integration/actors.yml`.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -26.5.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m218.glb export/mm7_m218.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m218.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [`gait_rollout_20261031/h12`](../gait_rollout_20261031/h12/README.md) appended Walk2 (humanoid set 2Hand-Bow-Walk legs,
0.80 s), Jog (Unarmed-Run-Forward, 0.72 s) and Sprint (Unarmed-Sprint, 0.56 s) to the installed
`assets_source/worlds/mm7/models/mm7_m218.glb` and installed it (existing clips, meshes, skins and materials
byte-identical). The pelvis-child `Spear` bone is keyed in the left fist with the accepted grip (`hand_props`); the spear
arm is raised 8 deg (Jog) / 20 deg (Sprint) so the tip stays 15 / 22 cm above the floor. Bindings (`h12/bindings.yml`):
walking: Walk2, stride_length 1.9505, run: Jog, run_stride_length 3.4574, sprint: Sprint, sprint_stride_length 4.4418.
Rebuild: `level_generation/creatures/gait_rollout_20261031/h12/scripts/rebuild.sh m218` (from `h12/work/mm7_m218_pre_gait.glb`, the
rollback source). A far-LOD repair rerun, a floor fix or any re-export of this model must re-graft these clips: copy the
new source over `h12/work/mm7_m218_pre_gait.glb` and rerun the rebuild, then install with `tools/install_model.py`.
