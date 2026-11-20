# MM7 Leather Fighter (`m226`, Robber / Raider / Bandit) reduction (2026-10-20)

User request for the MM7 batch A humanoids: "reduce tris on all 5". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that keeps UVs,
so the textures, region mask, tier ramps (`m226_a/b/c`) and clips stay as exported. No Meshy credits. **Nothing
installed**; nothing written under `assets_dev/` or `assets_source/`; `../mm7_m226_claude/` untouched.

Source: `../mm7_m226_claude/export/mm7_m226.glb` (body + merged head atlas `M226_A`, 2080x1024, node `M226`, 57
joints incl. `Sword`, 4 influences, 8 clips, shadow LODs) and `mm7_m226_sword.glb`, copied to
`work/mm7_m226_source_pre_reduce.glb` and `work/mm7_m226_sword_source_pre_reduce.glb` (rollback sources). Scripts are
copied from `../mm8_m432_reduce_claude/scripts/` (fixed parenting order in `reduce_ladder.py`, per-region groups, keep
sets, `grip_check.py`, `glb_close.py`), `kept_normals.py` / `region_error.py` from `../mm8_m656_reduce_claude/`,
`build_lods.py` from `../mm7_m162_reduce_claude/` (protected floor-contact and extreme points) and
`shrink_shadow_lods.py` from the source project. `scripts/bl.sh` runs Blender under this project's lease.

## Where the triangles are

Weld 6,315 -> 805 open edges, 5,780 vertices, no coincident vertices with other weights, no two-sided sheets (10,455 in
and out). Pieces (`scripts/m226_regions.py`):

| region | faces | treatment |
|---|---:|---|
| skin (body, arms, boots) | 2,883 | ladder budget (soles below 6 cm and sleeve ends kept) |
| head skin | 1,333 | front of the face kept (778), rest 70 % |
| hands (two shells, fingers) | 1,684 | kept exactly (fitted falchion grip) |
| small pieces (<= 80 faces: studs, spikes, boot straps, buckles, eyes, face strands, chest placket) | 1,680 | kept exactly |
| hair cap | 605 | 65 % |
| ponytail + loose strand | 362 | 60 % |
| shoulder yoke | 479 | 70 % |
| dagger + sheath | 604 | 30 % |
| back scabbard | 306 | 30 % |
| belt / buckle | 243 / 142 | belt 60 %, buckle kept |
| thigh strap | 134 | 80 % |

Kept exactly (`work/keep_f.npy`, 4,860 faces): both hands, small pieces, boot soles (321), front of the face (778),
sleeve ends (229 skin faces touching a vertex with hand + finger weight > 0.3), the belt buckle (142) and the skin
within 3 cm of the chest placket strip (26).

## Ladder

Limits for the 1.70 m bind height: p99 5.1 mm, max 25.5 mm.

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 10,455 | | | | |
| a: head rest 60, hair 70, ponytail 70, yoke 60, dagger/scabbard 50, belt 70, strap 80 % | r80 / r78 | 8,447 / 8,215 | 4.29 / 20.9, 4.79 / 22.5 | 0.993 / 0.992 | 0.993 / 0.991 | pass |
| a | r76 / r74 | 7,981 / 7,749 | 5.81 / 24.4, 6.93 / 27.8 | | | fail |
| b: head rest 50, hair 60, ponytail 55, yoke 75, dagger/scabbard 35, belt 60 % | r77 / r76 | 8,057 / 7,941 | 4.78 / 22.0, 5.10 / 22.5 | 0.992 / 0.991 | 0.992 / 0.991 | pass (r76 at the limit) |
| c: head rest 60, hair 65, ponytail 60, yoke 70, dagger/scabbard 35, belt 60 % | r76 | 8,021 | 4.94 / 22.5 | 0.991 | 0.991 | pass, but see below |
| d: c + one drift lock round (2 cm, 223 faces) | r77 / r76 | 8,059 / 7,989 | 5.67, 5.97 | | | fail |
| e: c + buckle, placket skin, both ears kept | | 8,171 / 8,101 / 8,033 | 5.19, 5.42, 5.79 | | | fail |
| **f: c + buckle, placket skin; head rest 70 %, dagger/scabbard 30 %; skin 62 %** | **r78** | **8,233** | **4.94 / 22.0** | **0.991** | **0.993** | **pick** |
| f, skin 58 % | r77 | 8,049 | 5.43 / 22.5 | 0.990 | 0.991 | fail |

- `region_error.py` (a r76): the skin causes 83 % of the over-limit error; `hotspots.py` (f r77) finds it spread over
  the whole suit (366 vertices, no cluster), so no spot patch helps. With 45 % of the mesh kept exactly, about 8.2k is
  the floor for this model at the playbook thresholds.
- **c r76 (8,021) was rejected on the close-ups:** the belt buckle's relief knot broke at 60 % and the suit skin poked
  through the lower edge of the chest placket strip (a green notch in the black strip). Both are kept in f.
- The 22 mm maximum is the same at every step (Running frame 15 / Death frame 12), not caused by the cut.
- Texture drift (`texture_drift.py r78`): 7 faces over 40 (44 cm2, p99 16.1; c had 14 / 88 cm2), the largest at the
  back of the right boot shaft; not visible in the close-ups. A drift-lock round (d) failed the geometry limits.

Close-ups straight from the GLBs (`scripts/glb_close.py`, file normals; viewer GLBs with the falchion in the socket):
`review/glbclose/sheet_a_head.png` (face front, three-quarter, side, back, yoke), `sheet_a_body.png` (torso, back, belt,
boots front and back), `sheet_a_hands.png` (both hands, the grip in the Attack, whole Attack and Death), `sheet_bc_tex.png`
(tiers B and C). Face, hands, grip, buckle, placket, laced thigh panel, boots and boot straps match the source; the
ears are a little softer in clay (70 %), the same textured.

## Build

`scripts/build_export.sh Cand_78 r78`: `kept_normals.py` (source corner normals on the 17,070 corners of unchanged
source faces, source vertex normals on 2,976 more; the source shades smooth, only 4 split positions have differing
normals) -> `export_cand.py` -> `swap_lod0.py` (into the rollback source) -> `build_lods.py` (0.5 / 0.2 / 0.075 of
LOD0, 4 influences; protected: the bounding extremes and every LOD0 vertex within 4 mm of the floor in Death/Dead) ->
`shrink_shadow_lods.py` (as the source project) -> `carry_variants.py` (variants on all 8 colour and shadow
primitives). `export/mm7_m226.glb`, 7.1 MB (source 7.7 MB).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source body | 10,455 | 5,210 | 1,825 | 570 |
| reduced body | **8,233** | 4,096 | 1,591 | 558 |
| falchion (unchanged) | 730 | 364 | 130 | 42 |

LOD3 ratio 0.075: 0.07 (503) and 0.08 (599) looked the same at LOD3 (`review/lods/lod3_trials.png`);
0.075 keeps every level at or under the source's.

Checks:
- Nodes, skins, inverse binds, materials, textures, images (bytes), clips (bytes), `KHR_materials_variants` (3 tiers)
  identical to the source; the `Sword` joint is unchanged.
- `grip_check.py` (`work/grip_check.log`): all 1,475 LOD0 vertices with hand + finger weight > 0.5 keep their bind
  positions (max 0.0004 mm) and weights, so the fitted falchion grip is unchanged at LOD0.
- `lod_check.py` (`work/lod_check_{src,r78}.json`): every LOD keeps the LOD0 bounds (0.97 x 0.52 x 1.700 m) and the
  same lowest point in every clip (Walking -16.4 mm, Attack -15.9, Standing -15.3, Death -13.7 as the source; Dead
  +2.9 mm, source +0.7); no face stretches over 20x at any LOD (the source LOD2 had one in Death and Running).
  `review/lods/sheet.png`: all LODs, standing, attack and head.
- Winding (`check_winding.py`): 0 inverted closed parts.
- Viewer: `http://127.0.0.1:8912/level_generation/creatures/mm7_m226_reduce_claude/review/viewer/index.html`, source
  export (r100) vs reduced (r78) for tiers A/B/C (`viewer_variants.py` bakes the tier ramps; `viewer_sword.py` adds the
  falchion under `Sword` for review only); `run_creature_review.py ... check`: 48 switches, no console errors.

## Weapon

`export/mm7_m226_sword.glb` is byte-identical to the source. The falchion is a clean procedural loft (`make_falchion.py`:
lens blade with a notched spine, guard bar, octagonal 1.2 cm grip, pommel) at 730 triangles; a cut would save about
250 triangles and bend the notched spine and the curved outline, so it is not clearly worthwhile.

## For the user to review

- 8,233 triangles is 3 % over the ~8,000 target; every lower step failed the p99 limit (the suit carries the cut).
- The ears at 70 % (side view, clay) and LOD3 (as coarse as the source's).

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m226_reduce_claude/export/mm7_m226.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m226_reduce_claude/export/mm7_m226_sword.glb --world mm7
```

then the binding from `../mm7_m226_claude/integration/actors.yml` as the source README says (same nodes, clips,
`Sword` socket and materials). Rollback: `work/mm7_m226_source_pre_reduce.glb` (+ `_sword`).

Reproduce (from this directory, `TOKEN=<lease>`):
1. `REA_GLB=level_generation/creatures/mm7_m226_reduce_claude/work/mm7_m226_source_pre_reduce.glb REA_NODE=M226 scripts/bl.sh scripts/import_source.py`;
   `REA_PROTECT=Head scripts/bl.sh scripts/dump_mesh.py`; `scripts/bl.sh scripts/dump_groups.py`;
   `python3 scripts/extract_basecolor.py work/mm7_m226_source_pre_reduce.glb`; `python3 scripts/small_pieces.py`;
2. `python3 scripts/m226_regions.py`; `python3 scripts/m226_sets.py f`;
3. `REA_KEEP_FACES=work/keep_f.npy REA_GROUPS=work/groups_f.npy REA_GROUP_RATIOS=2:0.7,3:0.65,5:0.6,6:0.7,7:0.3,8:0.3,9:0.6,10:0.8 scripts/run_ladder.sh f 0.7881`
   (`totals.py f 0.62` gives the ratio); `texture_drift.py r78`;
4. `scripts/build_export.sh Cand_78 r78`; `grip_check.py`, `REA_NODE=M226 lod_check.py`, `lod_views.py`;
5. `viewer_variants.py` (r100 from the rollback source, r78 from the export), `viewer_sword.py <glb> a|b|c`,
   `viewer_manifest.py "MM7 Leather Fighter" r78 10455 8233`, `glb_close.py`, `glb_sheet.py`.

## Clips updated (2026-10-20)

The source project's walk/run ankle twitch was fixed after this reduction (`../mm7_m226_claude/scripts/foot_level.py`). `scripts/transplant_clips.py` copied the re-exported clips into `export/mm7_m226.glb` and every `review/viewer/*.glb` (geometry, LODs, materials and variants unchanged), and `work/mm7_m226_source_pre_reduce.glb` is now that re-export. After any later re-export of the source, run `python3 scripts/transplant_clips.py ../mm7_m226_claude/export/mm7_m226.glb export/mm7_m226.glb export/mm7_m226.glb`.
The walk bob fix (`walk_bob.py`, same day) was carried over the same way.

**Accepted 2026-10-20**; installed 2026-10-20 from `../mm7_batches/BATCH_A_stage/` (listed in REDUCTION_LEDGER.md).
So was the Hit/Death foot-roll fix (flatness-weighted, smoothed roll; same day); the stage was rebuilt.

## Gait rollout (2026-10-31)

Package [`gait_rollout_20261031/h07`](../gait_rollout_20261031/h07/README.md) appended Jog (humanoid set Unarmed-Run-Forward, 0.74 s) and Sprint (Unarmed-Sprint, 0.56 s); Walking unchanged to the installed
`assets_source/worlds/mm7/models/mm7_m226.glb` and installed it (existing clips, meshes, skins and materials
byte-identical). The sword arm is lifted (eased, up to 25 deg) in the half of the run loop where the right knee comes
through, so the blade clears the thigh. Bindings for the coordinator (`h07/bindings.yml`): run: Jog, run_stride_length 3.129, sprint: Sprint, sprint_stride_length 4.1051. `Running` is kept in
the GLB but no longer bound for locomotion. Rebuild: `level_generation/creatures/gait_rollout_20261031/h07/scripts/rebuild.sh m226`
(from `h07/work/mm7_m226_pre_gait.glb`, the rollback source). A far-LOD repair rerun, a floor fix or any re-export of this
model must re-graft these clips: copy the new source over `h07/work/mm7_m226_pre_gait.glb` and rerun the rebuild, then
install with `tools/install_model.py`.
