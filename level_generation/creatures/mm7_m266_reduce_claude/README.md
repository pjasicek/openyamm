# MM7 Hydra (`m266`, Fire / Air / Chaos Hydra) reduction (2026-10-20)

The user asked for triangle reduction on the five batch I creatures ("do the tri reduction on all 5"). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: no part needed rebuilding, so the batch I
textures (both texture sets), region masks, tier ramps, clips and `Socket_Mouth` stay valid. **No Meshy credits.**
Scripts are copied from `mm7_m278_reduce_claude/` (ladder, UV weights, error/spot locks, LOD build, checks), with
`drift_lock.py` from `mm7_m402_reduce_claude/` and `shrink_shadow_lods.py` from `../mm7_m266_claude/`. Every
project, node and material name is adapted (node `M266`; materials `Hydra_A` body and `HydraHeads_A` heads). The
scripts that read textures read both sets: `texture_drift.py`, `dark_slivers.py` and `viewer_tiers.py` pick the
image by the wedge-u material offset. New for the hydra: `make_groups.py`, `rest_error.py`, `rest_misses.py`,
`ratio_for.py`, `contact_lock.py`, `check_heads_glb.py`, `gate_cand.sh`, `close_hydra.py`, `lod_split.py` and
`b.sh` (every Blender step goes through `tools/run_creature_blender.sh` under this project's lease). Batch I rules:
nothing installed, nothing written to `assets_dev/` or `assets_source/`. `../mm7_m266_claude/` is read only; its README
got only the "Reduced version" note.

Source: the batch I export `../mm7_m266_claude/export/mm7_m266.glb`, copied to `work/mm7_m266_source_pre_reduce.glb`
(the rollback source). Two materials with three `KHR_materials_variants` tiers each, one `M266` node, 71 bones +
`Socket_Mouth`, 8 clips. Weld: 19,886 -> 680 open edges, 9,512 vertices, 3 coincident vertices with other weights kept
apart. The open-edge count stays 680 at every step. The source shades smooth (21,770 vertices), and so does the reduced export. Smooth or flat
shading is not a question for this model.

Pieces (182): the body with heads 2-5 (9,816 faces), head 1 (1,007), the neck 1 shell (384) and 179 small pieces:
teeth (20-26 faces, 3-7 cm), eyes, tongues, horns, head 1's fin ribs, head 3's crest spikes (40 pieces of 20-34 faces),
head 5's frill, and the dorsal and tail spikes.

## Budgets per region (`make_groups.py`, final configuration)

| region | source faces | treatment |
|---|---:|---|
| small pieces (up to 40 faces or shorter than 9 cm: teeth, eyes, crest, dorsal and tail spikes) | 3,719 | kept exactly |
| head-to-neck lofts (body faces with any Head<k> weight) | 975 | kept exactly |
| near-contact zones of the heads (`contact_lock.py`, 2.5 cm, every half frame of every clip) | ~990 | kept exactly |
| spots: head 2's long mane spike, 9 rest misses over 15 mm (head 5 frill and horn tips, head 2 mane, head 1 fin), one thigh vertex, the five heads' nostrils, head 4's lower lip | ~260 | kept exactly |
| head surfaces (HydraHeads faces of the large pieces) | 6,548 | head 1 60 %, head 2 70 % (mane spikes), head 3 40 %, head 4 50 %, head 5 50 % |
| head pieces of 41-300 faces (horns, fin ribs, tongues, frill) | 2,940 | head 1 55 %, head 2 55 %, head 3 55 %, head 4 40 %, head 5 65 % |
| body (body, legs, tail, necks) | ~3,670 unkept | 90 % |

Result per material: heads (HydraHeads) 12,315 -> 8,555 (-31 %), body (Hydra) 5,551 -> 5,375 (-3 %). The heads take
94 % of the cut.

## Head 5: horns where the eyes belong (user review 2026-10-20)

The user found that head 5 (the rust horned head) had two short curved ivory horns exactly where its eyes should be, and
a stray horn jutting down beside the upper fang. The head 5 HD master (`../mm7_m266_claude/references_heads/h5/`) has
orange eyes there and no horn by the mouth. The fix is in this project's build only (`build_reduced.sh`):
- **`head5_fix.py`** removes the three separate horn pieces from the picked candidate: 112 triangles, pieces rigid on
  Head5 whose centres lie within 3 cm of (0.690, -1.187, 1.435), (0.905, -1.205, 1.436) and (0.877, -1.327, 1.370);
  the script asserts it found exactly these three. With `REA_EYES=1` it adds the eyes.
- **No eye is painted under the horns** (a shadowed socket with ivory paint where the horns met the skin), so
  **`head5_eyes.py`** builds two low-poly ellipsoid lenses: 8 segments x 5 rings, 64 triangles each, 4.8 x 3.2 cm,
  sunk 4 mm into the skin, rigid on Head5. Their axes point sideways, a little forward and up, in head 5's own frame.
  The right eye sits at its horn's root; the left horn's root lay in a pocket behind a skin flap, so the left eye
  mirrors the right one across the head. The UVs project flat into a 192 px cell of the head atlas's free sixth tile,
  which no other face uses.
- **`head5_eye_paint.py`** paints the cell in the GLB's embedded head images, after the master: an orange iris (yellow
  centre to red-orange), a dark rim, an upright slit pupil and a small glint. The region mask is 0 there, so the tiers
  never recolour the eyes; roughness is 70 and the normal map flat. It also repaints Meshy's ivory spill on the skin
  under the three removed horns (473 texels in head 5's own tile, each copied from the nearest skin texel; the teeth
  are excluded).
- **Unchanged:** the other heads, the body primitive (byte-identical to the pre-fix LOD0), every body image, materials,
  variants, nodes, skin and clips. Head image texels changed only in the free tile and in those 439-473 spill texels
  of tile 5. The LODs were rebuilt from the new LOD0.
- **Gates after the fix:** all identical to before. Head intersections are 0 in every clip except Attack frame 13
  (6 pairs, as batch I); the floor per clip and edge stretch match batch I; winding 0; viewer check 48 switches, no
  errors.
- Before/after close-ups straight from the GLBs: `review/glbclose/head5_fix_tex.png` (front, both three-quarters,
  both eyes, the stray horn's site).
- **The batch I export `../mm7_m266_claude/export/mm7_m266.glb` keeps the fault** (eye horns, stray horn, no eyes).
  As asked, it was not changed. Install this project's export.

## Ladder

Limits scaled to the 2.14 m rest height (`REA_HEIGHT_M=2.14`): p99 6.42 mm, max 32.1 mm, IoU >= 0.98, SSIM >= 0.93.

| step | change | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| g1 | small pieces + lofts kept, heads 50 %, head pieces 60 % | 12,144 | 9.95 / 66.3 | 0.987 | 0.988 | fail |
| a1 | heads 45 %, pieces 50 %, body 95 % | 12,252 | 9.67 / 66.3 | 0.990 | 0.990 | fail: the heads carry the error |
| v1 | per-head ratios from a rest-pose sweep | 13,768 / 12,448 / 11,126 | 5.47 / 27.4, 8.03 / 65.0, 12.8 / 66.3 | 0.996-0.983 | 0.992-0.986 | pass / fail / fail |
| m | v1 ratios a little deeper, 10 spot locks | 13,322 | 6.19 / 27.4 | 0.994 | 0.992 | pass, but heads 1 and 2 intersect in every frame |
| c1 | + contact lock (1.5 cm, every 2nd frame) | 13,446 | 6.13 / 27.4 | 0.996 | 0.992 | pass; head 3 nostril and head 4 lip in close-ups |
| s3 | + nostril, lip and thigh spots | 13,482 | 6.17 / 27.4 | 0.996 | 0.992 | pass; head 4 touches head 5 in Fidget |
| c3 | contact lock 2.5 cm at every half frame | 13,678 | 6.53 / 22.8 | 0.996 | 0.992 | fail (narrowly); head gate clean |
| f1 | heads 1, 2 and 4 a little gentler | 13,680 | 6.38 / 24.7 | 0.995 | 0.992 | pass; head 3's left nostril hit a wrong spot |
| **n1** | **+ the five heads' nostrils (2 cm)** | **13,930 (78 %)** | **6.23 / 22.8** | **0.996** | **0.992** | **picked** (`Cand_78`, lowest passing step) |

What was tried and dropped:
- **A deep uniform head cut:** heads at 35-45 % (v1 r62, 11,126) still look the same in textured close-ups, but they miss
  by up to 66 mm (head 2's long mane spike), p99 is twice the limit, and the heads interpenetrate without the contact
  lock.
- **Rest-pose error locks inside the head groups** (211 vertices, 2 cm): these broke the groups into islands with
  preserved borders, and the error rose (p99 8.5 -> 16 mm). An error lock in poses on the body only (`err_lock.py` with
  `REA_LOCK_LABELS=0`) worked. A full drift lock (753 faces, d1) fragmented the head groups the same way (p99 8.0). It
  was replaced by small spot locks at the visible spots.
- **Detail and smooth subgroups per head:** a uniform cut at 40 % misses by over 5 mm almost everywhere on heads 1, 2, 4
  and 5. The Meshy heads have no smooth parts that could take a deeper cut.
- **Cutting the spikes** (crest, dorsal, tail; 2,451 faces) at 50-70 %: the error is 13-40 mm at the tips. They stay
  exact.
- **The body:** it was already reduced to 80 % in batch I (`reduce_body.py`), and with a quarter of its edges on UV seams
  any cut past 90 % fails in the leg and thigh poses (`rest_error.py`: 0.97 -> 2 points over 6 mm, 0.9 -> 51,
  0.85 -> 136).

Close-ups (`close_hydra.py` on `work/ladder_n1.blend`, source | r78; the welded source's custom normals are cleared, so
judge shading from `review/glbclose/`):
- `review/close/sheet_heads_tex.png` and `_clay.png`: every head front, outer side, three-quarter and mouth.
- `review/close/sheet_body_tex.png` and `_clay.png`: the five loft joints, heads from above, back, both flanks, belly,
  paws, tail, necks from behind, Attack, Death, Running.
- `review/close/sheet_spots_tex.png` and `_clay.png`: the drift and sliver clusters and the nostrils.

Teeth, horns, crest spikes, head 1's fins, head 2's mane, head 5's frill and the loft joints match the source.
Straight from the GLBs (`glb_close.py`, `review/glbclose/sheet_tex.png`, `sheet_clay.png`: batch I | reduced), the
shading is the same.

## Gates (export/mm7_m266.glb)

- **Head intersections** (`check_heads_glb.py`: `check_hydra.py` rebuilt from the GLB, with heads by material and
  dominant Head<k> bone and the chain owner by dominant Neck<k>/Head<k> bone; 30 fps, every frame). On the batch I GLB it
  reproduces the batch I result exactly. **Reduced: identical to batch I.** 0 overlaps in Standing, Walking,
  Running, Hit, Death, Dead and Fidget. Attack frame 13 has 6 triangle pairs (head 4's horn tip grazing head 5, as in
  batch I).
- **Floor:** the lowest vertex per clip is identical to batch I: -1.2 cm Attack, -0.7 Dead, -3.9 Death (the hind paw
  mid-fall, as in batch I), 0.0 Fidget and Standing, -1.1 Hit, -0.8 Running, -0.7 Walking.
- **LODs** (`lod_check.py`, every frame): bounds and height (2.145 m) kept at every LOD. Every LOD's lowest point equals
  LOD0's (Dead at LOD3 -1.5 cm). Batch I's LOD3 sank 5.9 cm in Death and floated 2.2 cm when standing. No face
  stretches over 20x except the 3 LOD0 faces that batch I has too.
- **Edge stretch** (`glb_stretch.py`): identical to batch I in every clip (max 11.4x in Attack, batch I's neck 1 inner
  edge).
- **Winding** (`check_winding.py`): 0 inverted closed parts.
- **Texture drift** (`texture_drift.py`, both base colours): 24 faces over 40 (199 cm² in all; 8 on head 4's noisy
  grey skin, 5 on head 1). At 97 % the same check gives 0, so the cut causes these faces. **Dark slivers**
  (`dark_slivers.py`, `REA_DARK_L=80 REA_DARK_N=4`): 47 faces, each under 35 cm², mostly on heads 4, 1 and 3 at
  texture-island edges. These counts are higher than the manticore's (2 faces): the Meshy head atlases are noisy at a
  high frequency. Two spots were visible in close-ups and are fixed: head 3's nostrils had become a dark square, and
  head 4's lower lip had a red streak. The other clusters show no change (`sheet_spots_tex.png`).
- **Viewer:** `run_creature_review.py check`: 48 switches (6 models x 8 clips), no console errors.

## Build

`scripts/build_reduced.sh export/mm7_m266.glb` runs `head5_eyes.py` and `head5_fix.py` (`REA_EYES=1`) on `Cand_78` of
`work/ladder_n1.blend`, then `export_cand.py`. Then `swap_lod0.py` puts it onto the rollback source; materials, variants, images, clips, nodes, skin and `Socket_Mouth` are
checked identical. Then `build_lods.py`: default ratios 0.5 / 0.18 / 0.06, the body material at 0.5 / 0.22 / 0.1
(`REA_MAT_RATIOS`), protected bounding extremes within 5 mm, and LOD0 vertices within 6 mm of the floor in any
Death/Dead frame. Then `shrink_shadow_lods.py` and `carry_variants.py`, which carries the tier mapping to all 10 LOD and
shadow primitives, and last `head5_eye_paint.py`.

The body material ratios for LOD3 have a reason. The body material carries about 60 separate spikes and the claws, each
keeping a few triangles, so at the default 6 % its LOD3 surface broke into shards and the dorsal spikes floated
(`review/lods/sheet_lods.png` shows the fixed build).

| | LOD0 | LOD1 | LOD2 | LOD3 | file |
|---|---:|---:|---:|---:|---:|
| batch I | 17,866 | 8,925 | 3,110 | 913 | 13.8 MB |
| reduced (picked step, before the head 5 fix) | 13,930 | 6,945 | 2,598 | 1,094 | 12.6 MB |
| **reduced + head 5 fix (export)** | **13,946** | 6,953 | 2,600 | 1,093 | 12.6 MB |

The file shrinks less than the triangle count because both texture sets are unchanged.

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/mm7_m266_reduce_claude/review/viewer/index.html`: batch I and reduced
for tiers A, B and C (models `*_r78h5`: the export's LOD0 with the head 5 fix; ramps baked by
`scripts/viewer_tiers.py r78h5` from the batch I ramps and this project's patched head atlas and mask in `textures/`). The batch I models
are copies of the batch I viewer's GLBs. The viewer opens on reduced tier A; clips, provenance and native reference
frames come from the batch I manifest. Shots: `review/viewer_shots.png` (Standing and Attack, batch I | reduced).

## For the user to review

- **Head 5's new eyes** (`review/glbclose/head5_fix_tex.png`): their size, placement and painted iris are my reading of
  the master. The left eye mirrors the right one because its horn root lay in a skin pocket.
- **The cut is modest: 17,866 -> 13,946 (78 %), 13,930 before the head 5 fix.** About a third of the model is kept exactly: teeth, eyes, spikes, the
  loft joints, and the zones where the heads pass within 2.5 cm of each other. Cutting those breaks teeth and spike tips
  or lets the heads interpenetrate. The heads' Meshy detail fails the error limit below about 50-70 % per head, and the
  body was already reduced in batch I. Deeper steps (12.4k, 11.1k in `work/ladder_v1.blend`) look the same in textured
  close-ups but fail p99 by 25-100 %, lose head 2's longest mane spike, and would need the contact lock re-added. Ask
  if you want one built anyway, as was done for the MM6 hydra at 45 %.
- LOD3 is 1,094 triangles (batch I 913), so its spikes and claws stay attached.
- Head 4's grey snout shows slightly larger facets in extreme close-up (`sheet_spots_tex.png`, `h4n_nose`).

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m266_reduce_claude/export/mm7_m266.glb --world mm7
```

The `actors.yml` binding in `../mm7_m266_claude/README.md` is unchanged (same file name, node, clips, socket).
Rollback: `work/mm7_m266_source_pre_reduce.glb`. Add a ledger row in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) when
installing.

Reproduce (from the repository root, Blender scripts through
`tools/run_creature_blender.sh --token <lease> level_generation/creatures/mm7_m266_reduce_claude/scripts/<x>.py`, or
`REA_TOKEN=<lease> scripts/b.sh <x>.py` from the project; the MeshLab venv path is `REA_VENV` in `run_ladder.sh`):
1. `REA_NODE=M266 REA_GLB=level_generation/creatures/mm7_m266_reduce_claude/work/mm7_m266_source_pre_reduce.glb import_source.py`.
2. `dump_mesh.py`, `dump_faces.py`, `dump_weights.py`, then `python3 scripts/make_groups.py` (40 faces, 9 cm).
3. Keep chain (each step adds to the previous mask; points are rest-pose metres):
   - `spot_lock.py work/keep_base.npy work/keep_s1.npy 0.02` with the 9 misses over 15 mm printed by `rest_misses.py`
     plus head 2's mane spike tip `-0.549,-0.545,1.910`;
   - `contact_lock.py <abs>/work/keep_s1.npy work/keep_c1.npy 0.015`;
   - `spot_lock.py work/keep_c1.npy work/keep_s2.npy 0.015 0.05,-0.84,1.745 -0.045,-0.84,1.745 0.254,-1.076,1.307
     0.296,-1.078,1.312 0.239,-1.066,1.316 0.275,-1.079,1.313` (head 3 nostril, head 4 lower lip);
   - `spot_lock.py work/keep_s2.npy work/keep_s3.npy 0.03 -0.4132,-0.0822,0.3783` (thigh);
   - `contact_lock.py <abs>/work/keep_s3.npy work/keep_c3.npy 0.025` (every half frame);
   - `spot_lock.py work/keep_c3.npy work/keep_n1.npy 0.02 -0.953,-0.883,1.372 -0.901,-0.897,1.374 -0.006,-0.85,1.744
     0.05,-0.834,1.742 0.22,-1.156,1.446 0.811,-1.38,1.346` (the dark nostril clusters of heads 1, 3, 4, 5).
4. The body-only pose error lock (`REA_LOCK_LABELS=0 err_lock.py`, `work/keep_e2.npy`) and the drift lock
   (`drift_lock.py`, `work/keep_d1.npy`) are tried steps, not part of this chain.
5. `REA_WEIGHTS=component REA_HEIGHT_M=2.14 REA_KEEP_FACES=work/keep_n1.npy REA_GROUPS=work/groups.npy
   REA_GROUP_RATIOS=1:0.6,2:0.7,3:0.4,4:0.5,5:0.5,11:0.55,12:0.55,13:0.55,14:0.4,15:0.65 run_ladder.sh n1
   $(ratio_for.py work/keep_n1.npy work/groups.npy <ratios> 0.95,0.9)`.
6. `gate_cand.sh n1 Cand_78`, `close_hydra.py -- ladder_n1.blend Cand_78`, `pair_sheet.py`, `texture_drift.py r78`,
   `dark_slivers.py r78`.
7. `build_reduced.sh export/mm7_m266.glb`, then `check_heads_glb.py`, `lod_check.py` (`REA_NODE=M266`),
   `glb_stretch.py`, `check_winding.py`, `lod_split.py` + `lod_views.py`, `glb_close.py`, `viewer_tiers.py r78h5`,
   `update_viewer_manifest.py r78h5 13946` (after `cp work/pick_lod0.glb work/pick_lod0_eyes.glb` and
   `head5_eye_paint.py work/pick_lod0_eyes.glb`), `run_creature_review.py check`.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -6.6; dying sinks to -9.1; dying sinks to -9.9.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m266.glb export/mm7_m266.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m266.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [`gait_rollout_20261031/q3`](../gait_rollout_20261031/q3/README.md) added **Run2**, a slower trot for
Standard's chase:
- 0.75 s, stride 1.62, authored speed 2.16;
- hind L + front R at 0, as Walking. Running is half a loop off.

Hydra B and C chased on Walking ×1.57; Run2 plays ×0.94-1.19. Run2 was grafted onto the installed GLB; everything else
is byte for byte. Binding: `run: Run2`, `run_stride_length: 1.62`.

Rebuild: `blender -b --factory-startup -P scripts/quad_gait.py -- m266 work/m266_clips.glb`, then `graft_clips.py`
(see the q3 README). A far-LOD repair rerun or any re-export must re-graft Run2. Viewer revision `hydra-run2-1`.
