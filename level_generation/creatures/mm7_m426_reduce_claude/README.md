# MM7 Warlock (`m426`, Fire / Water / Air Warlock) reduction (2026-10-20, round 3)

User: "OK good, now reduce tris of the 5" (batch B). Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)
for an unbroken model: texture-aware ladder, no retexture, no Meshy credits. Scripts start from
`../mm8_m460_reduce_claude/` (the MM8 Cleric), plus `uv_weights.py` / `dump_weights.py` / component weights from
`../mm8_m600_reduce_claude/`. **Not installed; awaiting user review** (batch B: nothing under `assets_dev/` or
`assets_source/`).

Round 3 is on the source of the user's review revision 2026-10-20b (`../mm7_m426_claude/README.md`): gown inside,
covered inner layers and hidden leg shafts dropped at export, inner-leg weights off, Cast replaces Attack, Death is
Relax Lay Down, new base colour. Rounds 1-2 (earlier sources, 11,910 -> 9,452 and 11,740 -> 9,406) are superseded.

Source: `../mm7_m426_claude/export/mm7_m426.glb` (sha256 d1fd31f7fb541ed928decf6ae94b10d049c4e9719c8a2723ce589bce05a0450d;
LOD0 **10,732** triangles in the GLB) and `mm7_m426_wand.glb` (62ac27be..., unchanged), copied to
`work/mm7_m426_source_pre_reduce.glb` and `work/mm7_m426_wand_source_pre_reduce.glb` (rollback sources). Body: one node
`M426`, one merged material `M426_A` (body + head atlas 2080x1024, gown region mask, tiers `m426_a/b/c`), 116 joints,
8 influences, seven clips (Standing, Walking, Cast, Hit, Death, Dead, Fidget).

## Regions (`make_groups.py`, `vis_faces.py`)

Weld 7,638 -> 1,062 open edges, 2 coincident vertices with other weights kept apart. Labels from the source project's
runtime maps at each face's UV (material classes, gown mask, base colour) and the dominant bone; hidden = no ray
escapes the rest mesh (`vis_faces.py`, 8,568 of 10,732 visible). `review/labels_groups*.png` (round 1 renders).

| label | region | free faces | ratio |
|---|---|---:|---|
| 1 | face skin (head set) | 535 | 75 % |
| 2 | hair (head set + copper hair on the body set) | 3,335 | 60 % |
| 3 | right hand (open) | 198 | 70 % |
| 5 | gown | 857 | **kept** (round 3) |
| 6 | cape | 1,070 | 85 % |
| 7 | body skin (chest, shoulders, arms) | 689 | 80 % |
| 8 | hidden in the rest pose (linings) | 599 | 85 % |
| 9 | leg-weighted surface (now only the shins below 18 cm) | 75 | 65 % |
| 0 | rest | 86 | 80 % |

Kept exactly (`work/keep_g.npy`, 4,451 faces): pieces of up to 250 faces (eyes, earrings, neck ring, arm and wrist
bands), the bare feet (foot/toe-weighted faces and anything below 12 cm outside gown and cape), the left hand (wand
fist), gold texels (bodice cords, waist band, hem band; hair highlights classed gold excluded), the lavender cape edge
strip, the lips (2.5 cm around the mouth), the bust, one drift-lock round (`texture_drift.py` + `dark_slivers.py`,
visible faces only, 3 cm), spot locks for five light flecks (`REA_LIGHT=1 dark_slivers.py`; a white dash on the gown
front at the left hip in every pose), and the whole gown.

Why the gown is kept: the user's dark skirt patches were the source's inner layers (now removed); with the gown cut at
85 % its front read slightly more faceted in Walking (`review/glbclose/r79_skirt_walk12_tex.png`), for 128 triangles.
Kept, the skirt front renders like the source.

## Checks (round 3)

- **See-through** (`backface_check.py`, new): per pose and view (front, front-left, front-right, back; below 1 m;
  5 mm rays), back-facing hits are skipped as the engine culls them, and a pixel counts when the first front-facing
  surface lies over 1 cm behind the first surface. Source and r80 match within a few pixels everywhere on the skirt
  front (Standing 0/24, Walking 0/6/12, Cast 10/20, Hit 6); `BF_WHERE=1` lists the pixels only in the candidate:
  Walking 12 front 0, Standing 24 front 2 (at the cape edge). Cast 20 adds 22-51 pixels at the right cape edge and
  slit (the source has the same jagged gap there; `review/close/*_cast20_rside_tex.png`). The source itself counts
  about 1,200 such pixels from the front: the cape's inner side and the slit edges are single-sided.
- **Close-ups** with back-face culling (`CULL=1 close_human.py`, `review/close/`, source / r80): skirt front in
  Standing 24, Walking 6/12, Cast 20, hem, feet, face, hair front/back/side, bodice, hands, cape side, walk back, Cast,
  Death 8/16 and Dead match. Shading from the GLBs (`glb_close.py`, `review/glbclose/`, culled) matches.
- **Errors** (`group_error.py`, every 4th frame of every clip): face p99 2.1 mm, hair 7.6, cape 8.4, body skin 4.1,
  hidden 9.8 (max 85 in Death: an inner sheet between two robe chains), gown 0. Overall p99 5.4 mm, IoU 0.996, SSIM 0.995.
- **Flecks:** visible dark slivers 0; visible light flecks below 1.4 m 0 (the rest are sub-cm2 faces at the eyes).

## Ladder (round 3)

| config | triangles | overall p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| d: gown 75, cape 70 (lock source) | 8,484 | 7.5 / 110 | 0.993 | 0.992 | drift lock round |
| g: gown 85, cape 85, hidden 60 | 8,716 | 6.1 / 110 | 0.994 | 0.994 | hidden inner sheet 110 mm in Dead |
| i/j: hidden 85, + fleck spots | 8,748 / 8,760 | 5.7 / 85 | 0.994 | 0.995 | gown front facets in Walking |
| **k: gown kept** | **8,846** | **5.4 / 85** | **0.996** | **0.995** | **picked** |

## Build

`export_cand.py` (REA_CAND=Cand_80 of `work/ladder_k.blend`, 8 influences) -> `swap_lod0.py ... M426` ->
`build_lods.py` (`tools/build_actor_lods.py` with the source chain's ratios 0.5 / 0.18 / 0.06, 8 influences; crown
locked; no Death floor lock (the flat corpse froze LOD3) and no sole lock (LOD3's arms collapsed)) ->
`shrink_shadow_lods.py` (the source chain's) -> `carry_variants.py` -> `export/mm7_m426.glb` (sha256
10c48d1bb46df966deb60239049cce7259949700cee0af18223f67151962b882). `check_winding.py`: 0 inverted closed parts.
The wand is unchanged (`export/mm7_m426_wand.glb`, byte-identical).

| body | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source | 10,732 | 5,363 | 1,930 | 643 |
| reduced | 8,846 | 4,422 | 1,591 | 529 |

`lod_check.py` (REA_NODE=M426, every frame of the GLB clips): every LOD keeps the 1.70 m height and 0.96 m width.
Lowest point per LOD 0/1/2/3: Dead -1.0 / -1.0 / -0.1 / -0.1 cm (source the same), Death -9.7 / -5.5 / -4.7 / -4.5 cm
(source -9.7 / -9.7 / -4.7 / -4.5), Standing -0.5 cm. Stretched faces over 20x: at most as many as the source per clip.

Source faults found in rounds 1-2 and fixed in the source: the left cape hem's calf weights, the under-eye crescent
shells, the front-left gown hem 22 cm under the floor in Dead.

## Review

Viewer `review/viewer/` (source vs reduced per tier, wand included; tier ramps baked by `viewer_variants.py`, the wand
primitive copied from the source viewer files by `viewer_wand.py`):
http://127.0.0.1:8912/level_generation/creatures/mm7_m426_reduce_claude/review/viewer/.
`tools/run_creature_review.py ... check`: 42 clip switches, no console errors.

## Status

Not installed; awaiting user review. To adopt: install `export/mm7_m426.glb` and `export/mm7_m426_wand.glb` with
`tools/install_model.py --world mm7` (binding: `../mm7_m426_claude/export/actors_binding.yml`).
Rollback: `work/mm7_m426_source_pre_reduce.glb` (= `../mm7_m426_claude/export/mm7_m426.glb`, sha256 d1fd31f7...450d).

Reproduce: `REA_NODE=M426 REA_GLB=<rollback source> import_source.py` -> `dump_mesh.py` -> `dump_faces.py` ->
`vis_faces.py` -> `make_groups.py` -> `dump_weights.py` -> base colour from the GLB to `work/basecolor.png` ->
`spot_lock.py work/keep_base.npy work/keep_c.npy 0.025 0,-0.115,1.487` -> bust (front torso gown/skin faces,
y < -0.09, z 1.10-1.34, |x| < 0.17) -> `keep_d.npy` -> ladder d (`REA_GROUP_RATIOS=0:0.8,1:0.75,2:0.6,3:0.7,5:0.75,
6:0.7,7:0.8,8:0.6,9:0.65`) -> drift lock on r74 (`texture_drift.py`, `REA_DARK_L=80 REA_DARK_N=4 dark_slivers.py`,
`visible_only.py` each, combined, `drift_lock.py keep_d keep_e r74`) -> `spot_lock.py keep_e keep_f 0.03
-0.024,0.216,1.004 -0.102,0.184,1.046 -0.113,-0.073,1.11 0.078,-0.129,0.836 0.313,-0.022,0.452` -> keep_g = keep_f +
gown -> `REA_KEEP_FACES=work/keep_g.npy REA_GROUPS=work/groups.npy REA_WEIGHTS=component REA_HEIGHT_M=1.705
REA_GROUP_RATIOS=0:0.8,1:0.75,2:0.6,3:0.7,6:0.85,7:0.8,8:0.85,9:0.65 run_ladder.sh k 0.80` -> checks
(`group_error.py`, `backface_check.py`, `dark_slivers.py` dark and light + `visible_only.py`, `CULL=1 close_human.py`,
`close_sheet.py`) -> build as above -> `lod_check.py`, `glb_close.py` -> `viewer_variants.py` (source r100, export
r80) -> `viewer_wand.py r100 r80`. The MeshLab venv is `REA_VENV` in `run_ladder.sh` (pymeshlab, numpy, scipy).

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -8.9.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m426.glb export/mm7_m426.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m426.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [h11](../gait_rollout_20261031/h11/README.md) appended `Jog` (chase; wand kept upright, gown hem kept above the floor) to the installed
`assets_source/worlds/mm7/models/mm7_m426.glb` (library-loop legs, this model's own `Walking` arms, robe/cape chains
re-simulated on the new motion); existing clips are unchanged and the bindings are in
`../gait_rollout_20261031/h11/bindings.yml`. Rebuild: `level_generation/creatures/gait_rollout_20261031/h11/scripts/rebuild.sh m426`
(from `h11/work/mm7_m426_pre_gait.glb`). A far-LOD repair, head-bob, floor-fix or reduction rerun, or any re-export
of this model, must re-graft these clips (copy the new source over the pre-gait copy and rerun that rebuild, or graft
them with `claude_shared/graft_clips.py`).
