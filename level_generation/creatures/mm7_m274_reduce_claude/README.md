# MM7 Mage (`m274`, Sorcerer / Wizard / Archmage) reduction (2026-10-20)

User: "OK good, now reduce tris of the 5" (MM7 batch B casters). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) for an unbroken model ("No part to rebuild: skip the retexture"),
scripts from [`../mm8_m460_reduce_claude/`](../mm8_m460_reduce_claude/README.md) (the MM8 Cleric, robe + staff).
No retexture, no Meshy credits. **Not installed; awaiting user review** (batch B: nothing is installed).

Sources: the production exports `../mm7_m274_claude/export/mm7_m274.glb` (after the 2026-10-20 review revisions:
face_forward, flatten_feet, then the Cast retime and Attack/Cast trunk smoothing; sha256 e1ca396117ddc87c...) and `mm7_m274_staff.glb` (a3afbbc5a0f038cc...), copied to `work/mm7_m274_source_pre_reduce.glb` and
`work/mm7_m274_staff_source_pre_reduce.glb` (rollback sources). Body: one node `M274`, variants `M274_A/B/C`, merged
head/body 2080x1024 atlas with the region mask (R robe, G cape and collar, B beard), 8 influences, eight clips.
The staff is a static attachment on the `Staff` joint (left fist), `Socket_Staff_Head` at the gem.

## Regions (`make_groups.py`)

Weld (`import_source.py`, identical weights only) 7,244 -> 232 open edges, no coincident vertices with other weights.
Pieces from the production master (`rig_v6.blend` 'piece' attribute, mapped by rest position, max 0.001 mm):

| label | region | faces | ratio |
|---|---|---:|---|
| 1 | face (head piece outside the beard mask) | 862 | 70 % |
| 2 | beard (head piece, region mask B) | 1,789 | 50 % |
| 3 | right hand (open) | 489 | 50 % |
| 5 | robe lower | 1,118 | kept (100 %) |
| 6 | robe top + sleeves | 1,600 | 88 % |
| 7 | collar + yoke | 1,100 | 75 % |
| 8 | star cape | 1,068 | kept (100 %) |
| 9 | legs (inside the robe) | 389 | 70 % |

Kept exactly (`work/keep_f.npy`, 1,970 faces): pieces up to 250 faces (braids, belt medallion, mouth, eyes), the left
fist (fitted staff grip), shoes (below 15 cm), the hem bands of robe and cape (below 12 cm), one error lock
(`err_lock.py`, 12 mm, 2 cm: 32 vertices, mostly hidden inner robe surfaces in Death and the armpits) and one spot lock
(a visible dark sliver on the left front yoke).

## Ladder (limits for 1.70 m: p99 5.1 mm, max 25.5 mm)

| config | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| a: face 60, beard 50, hand 50, robe/cape 85, collar 80, legs 60 | 7,754 | 6.44 / 36.7 | 0.995 | 0.993 | fail: robe lower 9.8 / 33 mm and cape in Death/Cast |
| b: robe 92-95, cape 93, collar 85 | 8,286 | 4.58 / 30.5 | 0.998 | 0.995 | fail (max): hidden inner robe in Death |
| c: + error lock, robe/cape 90 | 8,176 | 4.93 / 28.6 | 0.997 | 0.995 | fail: robe lower 33 mm in Death |
| d: robe lower and cape kept, face 55, beard 45 | 8,008 | 4.91 / 22.5 | 0.998 | 0.995 | pass; face soft (eye sockets) |
| e: face 70, beard 50 | 8,226 | 4.76 / 22.5 | 0.998 | 0.995 | pass; one visible dark sliver (yoke) |
| **f: + spot lock** | **8,228** | **4.78 / 22.5** | **0.998** | **0.995** | **picked** |
| g: hand 40, collar 70, top 85, legs 60 | 8,042 | 5.42 / 38.7 | 0.997 | 0.995 | fail |

- **Pick 81 %:** the production chain already reduced the robe parts to its own per-garment budgets
  (`reduce_rigged.py`), and the robe and cape are simulated chains that lie flat in Death: even a 5 % cut moved
  hidden inner surfaces by 29-33 mm. The savings come from the head (beard 50 %, face 70 %), the right hand, collar,
  robe top and hidden legs.
- **Close-ups** (`review/close/sheet_f.png`, `sheet_d.png`, `sheet_e_head.png`; source / reduced, textured and clay):
  face, beard and braids, collar front and back, both hands, torso and medallion, cape back, hem, Death, Attack and
  Cast match. The beard is a little smoother in clay; the pale band across the upper face is in the source too.
- **Flecks:** `dark_slivers.py` (`REA_DARK_L=80 REA_DARK_N=4`) 0 faces at the pick; `texture_drift.py` 1 face over 40
  (0.0 cm2), p99 11.3.

## Build

`export_cand.py` (Cand_80 of `work/ladder_f.blend`, REA_NODE=M274, 8 influences) -> `swap_lod0.py ... M274` ->
`build_lods.py` (the creature's own LOD settings, `tools/build_actor_lods.py` ratios 0.5 / 0.18 / 0.06, 8 influences;
protected: LOD0 vertices within 1 cm of the floor in any Death/Dead frame and the top 5 mm of the collar, 122 points)
-> `MESH=M274 shrink_shadow_lods.py` (the creature's own) -> `carry_variants.py`: `export/mm7_m274.glb`, 7.2 MB
(production 7.5 MB). Textures, variants, region ramps, clips, sockets and node structure are the production ones.
`check_winding.py`: 0 inverted closed parts (body and staff).

| body | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| production | 10,188 | 5,091 | 1,833 | 609 |
| reduced | 8,228 | 4,113 | 1,480 | 489 |

`lod_check.py` (`work/lod_check_{src,r80}.json`): every LOD keeps the 1.70 m height (the collar top); the lowest
point per clip equals LOD0's at every LOD (Standing -0.7 cm, Attack -1.2, Cast -1.2, Walking -1.3, Death -5.3, as the
source; the production LOD3 rose up to 5 mm); 0-2 faces stretch over 20x in Death/Dead, as in the production model.

**Rebuilt 2026-10-20 (reduce-2)** on the new production source (`flatten_feet.py`: the shoes had sat 7-10 cm under the
floor; mesh, UVs, textures and staff unchanged): same pick (Cand_80 of `work/ladder_f.blend`), export_cand ->
swap_lod0 -> build_lods (108 protected points) -> shrink_shadow_lods -> carry_variants; the rollback copies in `work/`
are the new source. No ladder rerun (the mesh did not change).

**Rebuilt again (reduce-3)** on the next production source (Cast retimed with `retime_speed.py`, trunk and head
smoothed in Attack and Cast with `smooth_bones.py`, cast release 0.667 s; mesh, UVs, textures and staff unchanged;
body sha256 e1ca396117ddc87c..., staff unchanged a3afbbc5a0f038cc...): same pick and build (126 protected points),
LODs 8,228 / 4,113 / 1,480 / 489.

## Staff: unchanged

664 triangles (lathe shaft with gold bands, ring torus, gem). As for the MM8 Cleric, the ring and bands would go
star-shaped under a cut; `export/mm7_m274_staff.glb` is the production attachment byte for byte.

## Review

Viewer `review/viewer/` (production vs reduced per tier, staff included; tier ramps baked by `viewer_variants.py`,
the staff primitive copied from the production viewer files by `viewer_staff.py`):
http://127.0.0.1:8912/level_generation/creatures/mm7_m274_reduce_claude/review/viewer/.
`tools/run_creature_review.py ... check`: 48 clip switches, no console errors. `review/shots/pair_b.png`: tier B
production / reduced (standing, head, Dead).

## Status

Not installed; awaiting user review. To adopt it, install `export/mm7_m274.glb` and the unchanged
`export/mm7_m274_staff.glb` in place of the production exports (the README of `../mm7_m274_claude/` lists the command
and binding; nothing else changes). Rollback: `work/mm7_m274_source_pre_reduce.glb`.

Reproduce: `REA_NODE=M274 REA_GLB=<rollback source> import_source.py` -> `dump_mesh.py` -> `dump_faces.py` ->
face pieces (`work/face_piece.npy`, from `../mm7_m274_claude/work/rig_v6.blend`) -> `make_groups.py` -> ladder b ->
`REA_CAND=Cand_81 REA_ERR_MM=12 REA_LOCK_R=0.02 err_lock.py -- work/keep_base.npy work/keep_e.npy` ->
`spot_lock.py work/keep_e.npy work/keep_f.npy 0.02 0.132,-0.123,1.28` -> `REA_KEEP_FACES=work/keep_f.npy
REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.7,2:0.5,3:0.5,5:1.0,6:0.88,7:0.75,8:1.0,9:0.7 REA_HEIGHT_M=1.699
run_ladder.sh f 0.80` -> checks (`group_error.py`, `dark_slivers.py`, `visible_only.py`, `texture_drift.py`,
`close_human.py`, `close_sheet.py`) -> build as above -> `lod_check.py` -> `viewer_variants.py export/mm7_m274.glb r80`
-> `viewer_staff.py`.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -5.7.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m274.glb export/mm7_m274.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m274.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [h11](../gait_rollout_20261031/h11/README.md) appended `Jog` (chase; staff kept upright and off the floor) to the installed
`assets_source/worlds/mm7/models/mm7_m274.glb` (library-loop legs, this model's own `Walking` arms, robe/cape chains
re-simulated on the new motion); existing clips are unchanged and the bindings are in
`../gait_rollout_20261031/h11/bindings.yml`. Rebuild: `level_generation/creatures/gait_rollout_20261031/h11/scripts/rebuild.sh m274`
(from `h11/work/mm7_m274_pre_gait.glb`). A far-LOD repair, head-bob, floor-fix or reduction rerun, or any re-export
of this model, must re-graft these clips (copy the new source over the pre-gait copy and rerun that rebuild, or graft
them with `claude_shared/graft_clips.py`).
