# MM7 Peasant Goblin Female (`m442`, descriptors 430-438) reduction (2026-10-20)

User: "do tris reduction on all 5" (the five MM7 batch-K peasants; this project is m442 only). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that keeps the
UVs, so the textures, the nine palette looks (`KHR_materials_variants`) and the two region ramps stay valid. No Meshy
credits. Scripts from batch J's goblin, [`../mm7_7m452_reduce_claude/`](../mm7_7m452_reduce_claude/README.md) (paths,
node `M442`, shells and keep sets adapted). **Not installed** (batch K: the user installs later).

[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m442_reduce_claude/review/viewer/) (source r100 vs
reduced r83, nine looks, six clips, the sickle added under the `Sword` joint for review) · close-ups
[head](review/glbclose/sheet_f82_head.png), [body](review/glbclose/sheet_f82_body.png),
[hands, boots, death](review/glbclose/sheet_f82_legs.png), [neck front](review/glbclose/sheet_neck.png),
[back](review/glbclose/sheet_g83_back.png) · [viewer shots](review/shots_sheet.png)

## Source

`../mm7_m442_claude/export/mm7_m442.glb` and `mm7_m442_sickle.glb` (after the 2026-10-20 walk fix), copied byte for
byte to `work/mm7_m442_source_pre_reduce.glb` (sha256 df54d5b4902856d7…) and `work/mm7_m442_sickle_source_pre_reduce.glb`
(76f745555e236067…; rollback sources). One merged body + head atlas material per look (`M442_AA`…`M442_CC`, 2080x1024,
head half u > 0.51, region mask R purple cloth / G hair), node `M442`, 57 joints (incl. `Sword`), shadow LODs, clips
Standing, Walking, Hit, Death, Dead, Fidget. Bind height 1.700 m (ladder limits p99 5.1 mm, max 25.5 mm). Weld
(identical weights only): 6,110 -> 437 open edges, no coincident vertices with other weights, 9,534 triangles in and out.
Piece labels from the production master's `piece` attribute (`master_pieces.py`, `m442_pieces.py`: nearest rest vertex,
max distance 0.0006 mm).

## Where the triangles are (`scripts/m442_pieces.py`)

| part | faces | |
|---|---:|---|
| fused body shell (P00): head set part (face, ears, scalp, top knot, ponytail) | 3,604 | 1,658 head-set faces are hair (region G) |
| fused body shell (P00): body (vest, blouse with the wide sleeves, sash, trousers, boots) | 2,933 | already thinned in the build |
| hands (P01/P02) | 1,662 | the sickle grip is solved per finger: kept with every finger-weighted face (1,901) |
| fringe, ribbon bow and tails | 529 | |
| eyes | 306 | kept |
| 37 eyelets and toggles | 500 | kept (small pieces taper to points at any cut) |

The production build had already reduced the body (15.1k -> 9.5k with head and hands protected), so the cut sits in the
head set outside the face, the hair, the fringe and ribbons, and gently on cloth, sleeves and boots.

## Keep set and groups (`scripts/m442_sets.py`, pick = set `g`, `M442_FRONT_Y=0.0`)

Kept exactly (`work/keep_g.npy`, 4,334 faces): both hands (every face touching a vertex with hand + finger weight > 0.3),
the eyes, the 37 eyelets and toggles, the boot soles (body faces below 6 cm), the visible face and neck front (head-set
skin seen in some view, `visibility.py 1.30 1.71`, in front of y = 0).

| group | faces | ratio |
|---|---:|---|
| 1 visible head skin sides and back (ears, nape) | 500 | 60 % |
| 2 hidden head-set faces | 502 | 50 % |
| 3 visible hair (scalp, top knot, ponytail) | 1,175 | 50 % |
| 4 fringe and ribbon (pieces 3, 6-8, 45) | 529 | 65 % |
| 5 purple cloth on the body (region mask R) | 827 | 85 % |
| 6 wide sleeves (arm share > 0.5) | 428 | 85 % |
| 7 boots (below 0.45 m outside the cloth) | 500 | 70 % |
| 0 blouse front, sash, the rest | 739 | kept (free ratio 1.0) |

## Ladder (limits for 1.70 m: p99 5.1 mm, max 25.5 mm; IoU >= 0.98, SSIM >= 0.93)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 9,534 | | | | |
| a: hair/head 50-60 %, cloth 70 %, free 70-50 % | r78 / r77 | 7,528 / 7,484 | 7.43 / 35.97, 8.32 / 37.39 | 0.990-0.988 | 0.992-0.991 | fail (free region: chest V, sash front 25 mm) |
| b: body groups 85 %, free 95-75 % | r85 / r84 | 8,158 / 8,010 | 3.36 / 24.55, 4.75 / 24.71 | 0.995-0.994 | 0.997-0.995 | pass |
| c: head/hair 50-60 %, free 90-80 % | r81 / r80 | 7,806 / 7,734 | 4.02, 4.89 / 24.55 | 0.995-0.993 | 0.997-0.995 | pass; V neckline smeared, dark notch on the sash back (drift 86) |
| d: harder head/hair (40-50 %) | r77 / r76 | 7,496 / 7,424 | 5.13 / 25.16, 5.75 | | | fail (p99) |
| e: c + 4 cm patches at the max spots (chest V, sash front/back, hips) | r81 / r80 | 7,800 / 7,758 | 4.67, 5.08 / 24.71 | | | pass; the cut moved: a facet fan on the sash back, 20 drifted faces |
| f: c's groups, free region kept | r82 | 7,858 | 3.85 / 24.55 | 0.995 | 0.997 | pass; a faint vertical line down the neck front |
| **g: f + neck front kept** | **r83** | **7,978** | **4.27 / 24.55** | **0.994** | **0.997** | **pick** |

The pick is the lowest configuration that passes the ladder and looks like the source in the textured and clay
close-ups: the free region (blouse front between the vest panels, sash) is already lean and broke first (configs a, c,
e), so it is kept whole and the cut comes from the head set, hair, fringe/ribbons and gently from cloth, sleeves and boots.
The 24.55 mm maximum is in Death frame 9 (the same in every passing step).
Texture drift (`texture_drift.py` + `drift_visible.py g83`, visible faces): 9 faces over 40 (15.4 cm²); the largest
(drift 87, 8.7 cm²) is at the back of the neck under the ponytail; none shows in the close-ups.

## Build

`REA_KEPT_NORMALS=1 cand_glb.sh g Cand_83 kn` -> `work/g83_lod0.glb` -> `REA_CAP_Z=1.64 cap_points.py` (10 top-knot and
ribbon points, top 1.70 m) and `REA_NODE=M442 REA_FLOOR_MM=30 floor_points.py` (24 Death/Dead floor contacts) ->
`REA_LOD_RATIOS=0.5,0.21,0.068 build_lods.py` (`tools/build_actor_lods.py`, 34 protected points) ->
`shrink_shadow_lods.py` (the source project's) -> `carry_variants.py` (7 primitives) -> `check_winding.py` (0 inverted
closed parts): `export/mm7_m442.glb`, 6.33 MB (source 6.53 MB).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source body | 9,534 | 4,758 | 1,690 | 545 |
| reduced body | **7,978** | **3,987** | **1,649** | **515** |
| sickle (`export/mm7_m442_sickle.glb`, byte-identical copy, as the template's billhook) | 776 | 388 | 138 | 46 |

Checks:
- `scripts/compare_glb.py`: node names and transforms, skin and inverse binds, materials and extras, images, textures,
  samplers, all six clips, mesh names and the variants extension identical to the source; `KHR_materials_variants`
  (nine looks) on all 8 colour/shadow primitives. `DIFFERENCES none`.
- `scripts/grip_check.py` (`work/grip_check.log`): all 1,139 LOD0 vertices with hand + finger weight > 0.5 keep their
  bind positions (max 0.0003 mm) and weights exactly, so the sickle grip is unchanged.
- `lod_check.py` (source vs reduced): every LOD keeps the 1.70 m top; the lowest point per clip equals the source's at
  LOD0/LOD1 and is within 0-1 cm at LOD2/LOD3 (LOD3 Death −1.8 cm vs the source's −0.8 cm, Walking −1.5 vs −0.0); no
  face stretches over 20x in any frame of any clip at any LOD.
- Close-ups straight from the GLBs, source vs candidates, textured and clay (`glb_close.py`, `glb_sheet.py`): head,
  ears, hair, ponytail, V neckline, vest, sash front and back, wide sleeves, both hands, boots, death (links above).
- Viewer: `review/viewer/` (source r100 vs r83, nine looks with the ramps baked by `viewer_variants.py`, the sickle
  added under `Sword` by `viewer_sickle.py`); `python3 tools/run_creature_review.py --project
  level_generation/creatures/mm7_m442_reduce_claude check`: 108 switches, no console errors; shots in
  `review/shots_sheet.png`.

## Open points for review

- The cut is −16 % (9,534 -> 7,978): hands with the solved fist (1,901), face and neck front, 37 eyelets and the already
  lean body shell hold most of the mesh; harder steps flattened the V neckline and the sash.
- The viewer's `head` focus frames empty space for this model; use `body` or orbit.
- LOD3 lies up to 1 cm lower than the source's LOD3 in Death and Walking (distance LOD).

## Install (not run; user decision)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m442_reduce_claude/export/mm7_m442.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m442_reduce_claude/export/mm7_m442_sickle.glb --world mm7
```

then the binding from `../mm7_m442_claude/integration/actors.yml` (unchanged by this reduction) and a
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) row. Rollback: install `work/mm7_m442_source_pre_reduce.glb` (+
`work/mm7_m442_sickle_source_pre_reduce.glb`) the same way.

## Reproduce

`REA_GLB=<abs path of work/mm7_m442_source_pre_reduce.glb> REA_NODE=M442 import_source.py` -> `dump_mesh.py`,
`dump_groups.py`, `extract_basecolor.py work/mm7_m442_source_pre_reduce.glb` -> `master_pieces.py` (Blender) ->
`m442_pieces.py` -> `REA_MIN_PIX=6 visibility.py 1.30 1.71` (copy to `work/visible_head.npy`) ->
`M442_FRONT_Y=0.0 m442_sets.py g` -> `REA_HEIGHT_M=1.70 TOKEN=<lease> run_ladder.sh g g
"1:0.6,2:0.5,3:0.5,4:0.65,5:0.85,6:0.85,7:0.7" 1.0,0.97` -> `texture_drift.py g83`, `drift_visible.py g83` ->
`REA_KEPT_NORMALS=1 cand_glb.sh g Cand_83 kn` (copy `work/glb_g_83kn.glb` to `work/g83_lod0.glb`) -> build as above ->
`compare_glb.py`, `grip_check.py ... M442`, `lod_check.py` (REA_NODE=M442), `glb_close.py`, `viewer_variants.py`
(r100, r83), `viewer_sickle.py`, `viewer_manifest.py "MM7 Peasant Goblin Female" r83 9534 7978`. Blender scripts run
through `scripts/bl.sh` (lease wrapper, `TOKEN`). Ladder venv: `run_ladder.sh` uses the pymeshlab venv path recorded
in it (another session's scratchpad); recreate it if missing.

## Clips transplanted (2026-10-20, sickle grip fix)

The production project's corrected grip and palm-in carry (see `../mm7_m442_claude/README.md`, "Sickle grip fix") were
made after this reduction; the solved fist moved the `Sword` joint. The reduced mesh is unchanged:
`REBIND=Sword scripts/transplant_clips.py` copies the new clips and the Sword joint's transform and inverse bind into
`export/mm7_m442.glb` (every other joint must match; `compare_glb.py` against the new production export: DIFFERENCES
none); `export/mm7_m442_sickle.glb` is the new production attachment. Grip check: 1,139 hand vertices, max 0.0003 mm,
weights equal. Viewer rebuilt (r100 = new production export, r83 = reduced): 108 switches, no console errors.
Previous reduced export: `work/mm7_m442_reduced_precarry.glb`.

## Installed 2026-10-20

`tools/install_model.py export/mm7_m442.glb --world mm7` and `export/mm7_m442_sickle.glb` (winding check 0 inverted closed parts first); the
nine bindings from `../mm7_m442_claude/integration/actors.yml` appended to `assets_dev/worlds/mm7/models/actors.yml`
(explicit scale, no `scale_reference`); ledger row in `../REDUCTION_LEDGER.md`. Boot check on Harmondale with two looks
spawned: no load errors, no missing models (`output/batchK_boot/`). Rollback: reinstall
`work/mm7_m442_source_pre_reduce.glb` (the batch export) the same way.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -2.7.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m442.glb export/mm7_m442.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m442.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

The installed `mm7_m442.glb` carries a new `Jog` (Mixamo Running (5), 0.70 s, stride 1.5766) appended by
[gait rollout package h15](../gait_rollout_20261031/h15/README.md) for the peasants' flight (2.36 u/s; Walking played
x1.75); binding `run: Jog`, `run_stride_length: 1.5766` on all nine descriptors. Rebuild:
`gait_rollout_20261031/h15/scripts/rebuild.sh mm7_m442`. A far-LOD repair rerun or any re-export here must re-graft
that clip (copy the new source over `h15/work/mm7_m442_pre_gait.glb` and rebuild).
