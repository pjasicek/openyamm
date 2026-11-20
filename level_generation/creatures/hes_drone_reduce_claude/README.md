# Hesper Drones (`hes_drone`, skins hdr_a/b/c) reduction (2026-10-22)

User: "hesper drone ok, glassback ok - these 2 can go for tris minimize". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: textures, region mask, tier ramps, rig, clips,
sockets, the thrust node and the four gear attachments stay as exported. No Meshy credits. **Exported 2026-10-22, not
installed** (Hesper is integrated by the Hesper stage, whose `monsters.yml` does not list the drone yet; nothing in
`assets_dev/` or `assets_source/`, `hes_drone_claude/` untouched). Scripts copied from `hes_guard_reduce_claude/`
(ladder, LODs, LOD check, close-ups); `lodrep/` = the current `lod_repair_claude/scripts/` (region mask kept RGBA)
with the guard's `repair_glb.py`; `floor_check.py`, `shrink_shadow_lods.py` from the source project / turrets.

Source: `../hes_drone_claude/export/hes_drone.glb` (sha256 `24f65766…`), copied to
`work/hes_drone_source_pre_reduce.glb` (rollback source); the four gear GLBs to `work/*_source_pre_reduce.glb`.
Mesh node `HDR` with `Casing_*` (4,140) and unlit `Glow_*` (256) primitives, node `HDR_Thrust` (48).

## Result

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| approved export | 4,396 | 2,250 | 776 | 248 |
| **reduced** (`export/hes_drone.glb`) | **3,846** (-12.5 %) | 1,923 | 1,129 | 589 |
| thrust cone, attachments (emitter 336 + 48, ring 384 + 20) | unchanged | | | |

The gain is small and that is the honest number: the body was hand-built at 4.4k with its triangles already on the
silhouette (32-side lathes after the user's smoothing review, 6-sided tubes and cables, curved ribs). Every piece that
carries the look is kept; what went is the casing's and tail's profile rings where the profile is nearly straight,
the tail cap's 32-spoke pole fan (a high-valence fan the guidelines advise against) and a little of the plates.
LOD2/LOD3 come from the `lod_repair_claude` route (own UVs, 512/256 px far textures; LOD2/3 at 30/16 % of LOD0, the
first step passing: LOD2 outline 5.6 % / colour 12.5, LOD3 5.9 % / 13.3); they are larger than the approved ones
(776/248), whose LOD3 had a hexagonal lens and black shards ([LOD sheet](review/lods/lod_sheet.png)).
The attachments are lathed rings and a barrel (their sides are the silhouette, own LODs already): left unchanged.

## Pieces (`make_groups.py` from the master's face labels, `work/master_labels.npz`)

- **Kept exactly** (`work/keep_e.npy`, 2,964 faces): the Glow material (lens dome, vent nozzle and slots), the whole
  front collar (gold rings and the dark segmented band: at 79-86 % the dark band merged into the gold, `review/close_rejected_b79_c80.png`), the seven bone ribs and two hooks, the seven resin tubes (at
  70 % they broke: p99 7.3 mm, max 12.7), the three cables and gold plugs, the three chitin masses (85 % moved them
  5.5 mm for 33 triangles) and the vent drum.
- **Plates** 85 %; **casing and tail shell**: the rest (about 51 %).

## Ladder (REA_HEIGHT_M 0.525: p99 <= 1.6 mm, max <= 7.9 mm)

| config | change | step | triangles | p99 / max mm | IoU | |
|---|---|---|---:|---|---|---|
| a | tubes kept, plates 75, chitin 70, drum 80 % | r84 | 3,690 | 3.14 / 8.0 | 0.996 | chitin and drum too far |
| b | + drum kept, plates / chitin 85 % | r79 / r86 | 3,480 / 3,804 | 3.0 / 5.5 | 0.997 | collar band merged into the gold rings |
| c | b, tubes 70 % | r80 | 3,514 | 6.4 / 11.5 | 0.986 | tubes broke |
| d | + collar kept | r86 | 3,796 | 2.6 / 5.5 | 0.998 | chitin still 5.5 mm |
| **f** | **+ chitin kept, plates 85 %, custom normals** | **r87** | **3,846** | **2.18 / 2.9** | **0.998** | **picked** |

The p99 stays above the height-scaled limit at every step, even at 92 %: it is the sagitta of the lathed casing where
profile rings go (casing p99 about 2 mm on a 20 cm radius); the max (2.9 mm) is far inside its limit and the
close-ups show no change. Scaled by the drone's length (0.79 m) instead of its height the step passes.

**Normals.** `import_source.py`'s weld merges the source's hard-edge vertex splits (collar lips, plate borders, vent
rims), so a plain smooth export would round every hard edge. `reduce_ladder.py` gained `REA_SHARP=2`: every candidate
corner on a source vertex position takes the normal of the source corner there whose face matches best
(`work/src_normals.npz` from `src_normals.py`, the unwelded GLB), other corners smooth with the source's hard edges
marked sharp. `normal_check.py`: all 2,686 reduced vertices on source positions match a source normal (max 0.0°).

## Gates

| gate | source | reduced |
|---|---|---|
| floor rule, flier with hover (`floor_check.py`, `review/floor_check.json`) | living min 0.0 cm (thrust tip), Death/Dead 0.0 | identical, every clip |
| lowest body point (casing, vents) per clip (`lod_check.py`, LOD0) | Standing 7.02 cm, all living >= 7.0 | the same at LOD0/LOD1, >= 7.07 at LOD2/LOD3 |
| corpse per LOD (Death/Dead) | 0.0 / 0.0 / -0.25 / 0.05 cm | 0.0 / 0.0 / 0.04 / 0.04 cm |
| stretched faces in any clip, bounds | 0, 0.43 x 0.79 x 0.53 m | 0, the same (LOD3 1 cm shorter at the lens) |
| error over every 3rd frame of every clip | | max 2.9 mm |
| texture drift (`texture_drift.py r87`) | | 4 faces over 40 (51 cm², resin skin on the right flank), nothing visible |
| key times (`check_key_times.py`) | PASS | PASS on all five GLBs |
| winding (`check_winding.py`) | 0 | 0 on all five GLBs |

## Review

- Close-ups straight from the viewer GLBs (textured, clay, clay + wireframe; lens, three-quarter, ribs, right flank,
  tail, belly, left flank): [tier A](review/close_r87.png), [tier C with the ring](review/close_r87_tierC.png);
  the rejected configs `review/close_e87.png` (sharp edges only, before the custom normals), ladder
  `review/ladder_sheet.png` (last config).
- Viewer: `http://127.0.0.1:8912/level_generation/creatures/hes_drone_reduce_claude/review/viewer/`: approved export
  (r100) and reduction (r87, default) for A, B (twin emitter) and C (shield ring); `viewer_swap.py` puts the reduced
  body into the source project's tier viewer GLBs. `run_creature_review.py check`: 48 switches, no console errors;
  [viewer shots](review/viewer_shots.png).

## Install (not run)

Same file names, nodes, materials, variants, sockets and attachments, so `integration/actors.yml` (= the source
draft) applies unchanged. When the Hesper stage takes the drone: add the five `export/` GLBs to the stage's
`monsters.yml` `models:` (after `check_winding.py`). Rollback: `work/hes_drone_source_pre_reduce.glb`.

Reproduce: `import_source.py` (REA_GLB, REA_NODE=HDR), `dump_mesh.py`, `dump_faces.py`, `dump_weights.py`,
`src_normals.py work/hes_drone_source_pre_reduce.glb HDR`, the master labels (face centres matched to
`../hes_drone_claude/work/uv3d.npz`, `work/master_labels.npz`, `work/piece.npy`), `make_groups.py`, keep masks
(`keep_e.npy` = glow, bone, cables, tubes, drum, collar, chitin), `REA_SHARP=2 REA_HEIGHT_M=0.525
REA_KEEP_FACES=work/keep_e.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=2:0.85 scripts/run_ladder.sh f 0.875`,
`region_err.py`, `scripts/build_export.sh f Cand_87`, `lod_check.py` + `lod_views.py` (LOD_VIEWS), `viewer_swap.py`,
`viewer_manifest.py`, `close_drone.py` + `pair_sheet.py`, `normal_check.py`.
