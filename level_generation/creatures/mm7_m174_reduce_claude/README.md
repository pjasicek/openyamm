# MM7 Cleric of the Sun (`m174`, Acolyte / Cleric / Priest of the Sun) reduction (2026-10-20)

User: "OK good, now reduce tris of the 5" (the MM7 batch B casters). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) for an unbroken model ("No part to rebuild: skip the retexture"),
scripts copied from the MM8 Cleric reduction [`../mm8_m460_reduce_claude/`](../mm8_m460_reduce_claude/README.md).
No retexture, no Meshy credits. **Not installed; awaiting user review** (batch B keeps everything in the project).

Source: `../mm7_m174_claude/export/mm7_m174.glb` (revision 2026-10-20, faced-front Attack/Cast), copied to
`work/mm7_m174_source_pre_reduce.glb` (rollback). One node `M174`, three material variants (`M174_A/B/C`, tiers
`m174_a/b/c`), merged head/body 2080x1024 atlas with the stole region mask (R) and ramps, eight clips.

## Regions (`make_groups.py`)

`import_source.py` (REA_NODE=M174): weld 5,601 -> 157 open edges, no coincident vertices with other weights; height
1.68 m (limits p99 5.04 mm, max 25.2 mm). After the weld: the main piece (masked face on the head atlas, arms, open
hands, robe top and sleeves, 4,199), the gold sun mantle (1,500), the robe skirt (1,100) and 16 small pieces.

| label | region | faces | ratio |
|---|---|---:|---|
| 0 | robe top, sleeves, arms (rest of the main piece) | 1,316 | free (54 % at the pick) |
| 1 | face (head-atlas part of the main piece) | 1,505 | 55 % |
| 3 / 4 | left / right hand (B_*_Hand dominated) | 658 / 668 | 45 % |
| 6 | gold sun mantle | 1,487 | 70 % |
| 5 | robe skirt | 718 | kept |

Kept exactly (`work/keep_i.npy`, 3,127 faces):
- pieces of up to 250 faces: the nine crown rays (thin spikes), the neck/collar band, the teal stole (tier region,
  painted squares), eyes, belt medallion, both wrist bands;
- the robe skirt: at 90 % it missed the source by 28-40 mm in Death (robe chains, the lying robe); keeping it costs
  ~70 triangles;
- one error lock (`err_lock.py`, 16 mm, Cand_74 of ladder a): mostly skirt and chest points in Death/Cast;
- spot locks (`spot_lock.py`, 3 cm): the back of the neck (7 visible dark slivers, `dark_slivers.py` +
  `visible_only.py`), two chest faces on the red centre strip and one under the left mantle edge
  (`texture_drift.py` over 40).

## Ladder

| config | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| a: face 60, hands 50, skirt 90, mantle 80 (80-74 %) | 7,005 ... 6,481 | 3.29 / 40.1 ... 4.16 / 40.1 | 0.997 | 0.995 | fail: skirt in Death |
| d: + error lock, skirt kept | 7,005 ... 6,479 | 2.81 / 15.9 ... 4.22 / 17.7 | 0.998 | 0.996 | pass |
| e: face 55, hands 45, mantle 70 (74-68 %) | 6,483 ... 5,957 | 3.54 / 14.8 ... 5.88 / 24.8 | 0.998 | 0.994 | pass to 70 %, 68 % fails (Fidget) |
| h/i: e at 72 % + spot locks | 6,305 | 4.04 / 18.2 | 0.998 | 0.994 | **picked** |

- **Pick 72 %:** close-ups of 74 / 72 / 70 % (`review/close_e_{a,b}.png`, source left; textured and clay): face,
  crown rays, both hands and the Cast hand, wrist bands, mantle pattern front and back, stole, robe stripes and hem,
  Death, Attack and Cast match at 72 %; at 70 % the shoulder line under the collar gets coarser and Fidget fails the
  max. Earlier ladders: `review/close_d_{a,b}.png`.
- **Flecks:** at the pick `dark_slivers.py` (`REA_DARK_L=80 REA_DARK_N=4`) 0, `texture_drift.py` 0 faces over 40.

## Normals

Plain smooth, as the source. Rendered straight from the GLBs (`glb_close.py`, `review/glbclose_sheet.png`: columns
source tex / reduced tex / source clay / reduced clay): face, crown, mantle, neck, hand, back and robe shade the same.
The neckline's red pleats read slightly softer.

## Build

`export_cand.py` (Cand_72 of `work/ladder_i.blend`, REA_NODE=M174, 8 influences) -> `swap_lod0.py ... M174` ->
`build_lods.py` (the creature's `build_actor_lods` ratios 0.5 / 0.18, LOD3 0.08 instead of 0.06 to keep about the
source's LOD3 count; protected: LOD0 vertices within 1 cm of the floor in any Death/Dead frame, the top 5 mm, the tip
of every crown ray, and the x/y bounding extremes; at 0.06 without the extremes LOD3 lost 11 cm of hand width) ->
`../mm7_m174_claude/scripts/shrink_shadow_lods.py` (MESH=M174, as the creature's runtime chain) ->
`carry_variants.py`: `export/mm7_m174.glb`, 6.9 MB (source 7.4 MB). `check_winding.py`: 0 inverted closed parts.

| body | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source | 8,761 | 4,379 | 1,576 | 514 |
| reduced | 6,305 | 3,152 | 1,134 | 492 |

Shadow meshes match the colour LODs, as the source. `lod_check.py` (REA_NODE=M174): every LOD keeps the 1.700 m
height and the 1.09 x 0.79 m extent (the source LOD3 lost 3.5 cm of depth); lowest points equal LOD0's in every clip
(Death -5.9 cm, the source's own). One face at LOD2 and two at LOD3 stretch over 20x for a moment in Death (source:
0); far LODs only.

## Review

Viewer `review/viewer/` (source vs reduced per tier; tier ramps baked by `viewer_variants.py`, source files copied
from `../mm7_m174_claude/review/viewer/`):
http://127.0.0.1:8912/level_generation/creatures/mm7_m174_reduce_claude/review/viewer/.
`tools/run_creature_review.py ... check`: 48 clip switches, no console errors. `review/shots/std_b_pair.png`: tier B
source / reduced.

## Status

Not installed; awaiting user review. To adopt: install `export/mm7_m174.glb` in place of the source project's export
(the install line in `../mm7_m174_claude/README.md`, same binding). Rollback: `work/mm7_m174_source_pre_reduce.glb`
(byte-identical to `../mm7_m174_claude/export/mm7_m174.glb`).

Reproduce: `import_source.py` (REA_NODE=M174, REA_GLB=the rollback source) -> `dump_mesh.py` -> `dump_faces.py` ->
`make_groups.py` -> ladder a (`REA_KEEP_FACES=work/keep_base.npy REA_GROUPS=work/groups.npy
REA_GROUP_RATIOS=1:0.6,3:0.5,4:0.5,5:0.9,6:0.8 REA_HEIGHT_M=1.68 run_ladder.sh a 0.80,0.78,0.76,0.74`) ->
`REA_CAND=Cand_74 REA_ERR_MM=16 REA_LOCK_R=0.02 err_lock.py -- work/keep_base.npy work/keep_e.npy` -> keep_g = keep_e +
group 5 -> `spot_lock.py work/keep_g.npy work/keep_h.npy 0.03 -0.011,0.037,1.35 -0.027,-0.149,1.135
-0.002,-0.156,1.084` -> `spot_lock.py work/keep_h.npy work/keep_i.npy 0.03 0.108,-0.022,1.03` ->
`REA_KEEP_FACES=work/keep_i.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.55,3:0.45,4:0.45,6:0.7
REA_HEIGHT_M=1.68 run_ladder.sh i 0.72` -> checks (`dark_slivers.py r72`, `visible_only.py`, `texture_drift.py r72`,
`close_human.py`, `close_sheet.py`) -> build as above -> `lod_check.py`, `glb_close.py` -> `viewer_variants.py
export/mm7_m174.glb r72`. `rest_of.py` (new) prints a candidate vertex's rest position from a posed probe point.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: Cast sinks to -2.6; corpse at -7.5; dying sinks to -8.6.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m174.glb export/mm7_m174.glb --lift-joints Cast Dead Death --lift-only 'B_Skirt*,Robe_*,…' --raise Cast --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m174.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [h11](../gait_rollout_20261031/h11/README.md) appended `Walk2` (slower walk, wandering) and `Jog` (chase of tiers B/C; tier A keeps walk-as-run on `Walking`) to the installed
`assets_source/worlds/mm7/models/mm7_m174.glb` (library-loop legs, this model's own `Walking` arms, robe/cape chains
re-simulated on the new motion); existing clips are unchanged and the bindings are in
`../gait_rollout_20261031/h11/bindings.yml`. Rebuild: `level_generation/creatures/gait_rollout_20261031/h11/scripts/rebuild.sh m174`
(from `h11/work/mm7_m174_pre_gait.glb`). A far-LOD repair, head-bob, floor-fix or reduction rerun, or any re-export
of this model, must re-graft these clips (copy the new source over the pre-gait copy and rerun that rebuild, or graft
them with `claude_shared/graft_clips.py`).
