# Hesper Glassbacks (`hes_glassback`, skins hgb_a/b/c) reduction (2026-10-22)

User: "hesper drone ok, glassback ok - these 2 can go for tris minimize". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: textures (merged body + head atlas
2080x1024), region mask, tier ramps, rig, clips (including the rear-up Attack, impact 1.083 s), `Socket_Beak` and the
14 crest attachments stay as exported. No Meshy credits. **Exported 2026-10-22, not installed** (the Hesper stage's
`monsters.yml` does not list the Glassback yet; nothing in `assets_dev/` or `assets_source/`, `hes_glassback_claude/`
untouched). Scripts copied from `../hes_drone_reduce_claude/` (the guard's ladder chain) and from the source project
(`floor_gate.py`, `shrink_shadow_lods.py`, the crest layout for `crest_check_glb.py`); `lodrep/` = the current
`lod_repair_claude/scripts/` (region mask kept RGBA).

Source: `../hes_glassback_claude/export/hes_glassback.glb`, copied to `work/hes_glassback_source_pre_reduce.glb`
(rollback source); the 14 crest GLBs to `work/hes_glassback_crest_*_source_pre_reduce.glb`. One node `Glassback`,
one material `Glassback_A` (variants B/C; regions R hide, G belly, A rust). The source LOD0 was already cut once in
its own build (`reduce.py`, Blender collapse: body x0.42, head x0.7, 15,862 -> 7,485), so there is little slack.

## Result

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| approved export | 7,485 | 3,741 | 1,345 | 448 |
| **reduced** (`export/hes_glassback.glb`) | **5,987** (-20 %) | 2,992 | 1,494 | 748 |
| crest attachments (full set 1,853 at LOD0) | unchanged | | | |

LOD2/LOD3 from the `lod_repair_claude` route at 25/12 % (first step passing: LOD2 outline 3.2 % / colour 12.6,
LOD3 4.4 % / 9.0); the approved LOD3 put the corpse 4 cm under the floor and stood 1.5 cm up, the new ones are on it.
**The crest is not reduced:** each plate is a 5-7-sided prism (already minimal for a crisp faceted silhouette), and
about two thirds of the crest triangles are the thin glow strips (root bands, cracks, edge seams) that the user asked
to protect (e.g. full spine2: glass 180, glow 414). Any cut there would bend the strips.

## Pieces (`make_groups.py`)

- **Kept exactly** (`work/keep_e.npy`, 3,488 faces): the head texture set (2,026: head, beak, both eyes), the feet
  (Foot_* faces, 1,232: glass toes and soles, which the floor and stride gates measure), a 6 cm spot on the upper left
  flank where the collapse folded a lump through its neighbour (a black window into the body in every config-a step,
  `review/close_a.png`; `spot_lock.py`), two error-lock rounds (posed misses over 15 / 18 mm: hind knees in Running,
  shoulders in Death, 3 cm around each) and one drift-lock round (belly faces whose colour moved, 5 cm).
- **Rest** (torso, legs, neck, tail): about 63 %.

## Ladder (REA_HEIGHT_M 1.2: p99 <= 3.6 mm, max <= 18 mm)

| config | change | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---|---:|---|---|---|---|
| a | head set + feet kept | r90 / r80 | 6,735 / 5,987 | 6.2 / 20.6, 8.9 / 36.7 | 0.997 / 0.995 | 0.994 / 0.986 | black fold on the flank |
| b | + fold spot, error lock | r85 / r80 / r75 | 6,361 / 5,987 / 5,613 | 7.4 / 20.8, 9.0 / 36.7, 11.3 / 36.7 | 0.997-0.994 | 0.991-0.980 | no black pixels |
| c | + second error lock | r80 | 5,987 | 9.5 / 19.6 | 0.995 | 0.986 | |
| **e** | **c + drift lock** | **r80** | **5,987** | **10.1 / 20.6** | **0.995** | **0.984** | **picked** |

No step passes the ladder's p99 limit, not even 90 % (6.2 mm): the mesh is lumpy (overlapping hide plates) and was
already collapsed once, so every further collapse moves the surface a little. The pick is visual: in the close-ups
r80 and r75 look like the source, r75's back lumps a little softer; r80 keeps a margin. Max 20.6 mm (posed, Running,
the hind knee) is 1.1 % of the creature's length. Texture drift (`texture_drift.py r80`): 4 faces over 40 after the
lock (276 cm², belly and flank), nothing visible in the textured close-ups of tiers B and C.

## Gates

| gate | source | reduced |
|---|---|---|
| floor and strides (`floor_gate.py`, `review/floor_gate.json`, three tier scales) | pass; strides 0.875 / 1.4583 m on all six feet | pass; the same strides on all six feet |
| corpse (`floor_fix.py --ground-death`, as the source build) | Dead 0.0 | Dead 0.0 (moved by 0.0) |
| crest clearance (`crest_check_glb.py`, every frame, sinks of 1.3 r; below -1 the open bottom would show) | worst gap -0.25 (Bite), Attack -0.05, swallow 0.97 (Death), tips >= 12.1 cm | worst gap -0.25 (Bite), Attack -0.16, Standing -0.11, swallow 0.94, tips >= 12.1 cm |
| LOD check: stretched faces, bounds, Death/Dead per LOD | 0; corpse 0 / -1.2 / 0.7 / -4.0 cm | 0; corpse 0.0 at every LOD; bounds the same (LOD3 3.5 cm narrower) |
| black clay pixels against the source (`black_check.py`, 12 spots) | | none |
| key times / winding | PASS / 0 | PASS / 0 on all 15 GLBs |

The crest clearance runs on the GLB as imported (the source project's `crest_check.py` reads its master blend); run
on the approved GLB it reproduces the source numbers, so the columns compare (`review/crest_src.json`,
`review/crest_clearance_reduced.json`).

## Review

- Close-ups straight from the viewer GLBs (textured and clay; head, beak, head side, chest, flank, back, tail, front
  foot, belly and legs, walk, Attack rear-up, corpse): [tier B](review/close_r80.png),
  [tier C (rust)](review/close_r80_tierC.png); rejected config a (black fold) `review/close_a.png`, config b steps
  `review/close_b_tex.png`, `review/close_b_clay.png`; [LOD sheet](review/lods/lod_sheet.png) (base colour, no ramps).
- Viewer: `http://127.0.0.1:8912/level_generation/creatures/hes_glassback_reduce_claude/review/viewer/`: approved
  export (r100) and reduction (r80, default B) for A, B and C with their crests; `viewer_swap.py` puts the reduced body
  into the source project's tier viewer GLBs. `run_creature_review.py check`: 54 switches, no console errors;
  [viewer shots](review/viewer_shots.png).

## Doubtful

- The far LODs' own 512/256 px textures blur the black beak into speckles at LOD2/LOD3 (close up in the LOD sheet); at
  the switch sizes (180 / 72 px) the audit's colour score passes, and the approved LODs had worse shapes.
- The ladder's p99 limit is not met at any step (see above); the pick rests on the close-ups and the gates.

## Install (not run)

Same file names, nodes, materials, variants, sockets and attachments, so `integration/actors.yml` (= the source
draft) applies unchanged. When the Hesper stage takes the Glassback: add `export/hes_glassback.glb` and the 14 crest
GLBs to the stage's `monsters.yml` `models:`. Rollback: `work/hes_glassback_source_pre_reduce.glb`.

Reproduce: `import_source.py` (REA_GLB, REA_NODE=Glassback), `dump_mesh.py`, `dump_faces.py`, `dump_weights.py`,
`make_groups.py` (-> keep_a), `spot_lock.py work/keep_a.npy work/keep_b0.npy 0.06 0.30,-0.04,0.97`, `err_lock.py` on
a/Cand_85 (15 mm) -> keep_b, on b/Cand_75 (18 mm) -> keep_c, `REA_WEIGHTS=component REA_HEIGHT_M=1.2
REA_KEEP_FACES=work/keep_c.npy scripts/run_ladder.sh c 0.8`, `texture_drift.py r80`, `REA_LOCK_R=0.05 drift_lock.py
work/keep_c.npy work/keep_e.npy r80`, `run_ladder.sh e 0.8`, `scripts/build_export.sh e Cand_80`, `crest_check_glb.py`,
`lod_check.py` + `lod_views.py` (LOD_VIEWS), `viewer_swap.py`, `viewer_manifest.py`, `glb_close.py` + `pair_sheet.py`,
`black_check.py`, `flip_faces.py`, `region_err_gb.py`.
