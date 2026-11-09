# MM6 Fire Lizard (`drag`) — fast UV-preserving reduction pilot (2026-10-13)

Staged only; nothing installed. Purpose: a fast, low-babysitting triangle cut for the MM6 3D batch that keeps each
creature's existing UVs, textures, tier masks, burn maps, rig and clips (no retexture, no Meshy credits).

- `scripts/reduce_ladder.py` (Blender, about 1 minute): quadric collapse at 70/60/55/50/45 %, X-symmetric, Head/Jaw
  protected (Decimate's vertex group selects what decimates, so it is inverted), 4 influences. Per step: triangles,
  open edges, two-way surface error over every 3rd frame of every clip, 6 silhouette + 6 textured renders.
- `scripts/compare_ladder.py`: silhouette IoU and textured SSIM per view; picks the lowest passing step
  (p99 <= 3 mm, max <= 15 mm, open edges not above the source, IoU >= 0.98, SSIM >= 0.93); `review/ladder_sheet.png`.

| step | triangles | p99 / max mm | IoU min | SSIM | |
|---|---:|---|---|---|---|
| source | 13,789 | | | | |
| 70 % | 9,651 | 1.1 / 11.4 | 0.993 | 0.997 | pass |
| 60 % | 8,273 | 1.9 / 11.1 | 0.989 | 0.992 | pass |
| **55 %** | **7,583** | 2.5 / 13.6 | 0.986 | 0.989 | **picked** |
| 50 % | 6,894 | 4.3 / 25.2 | 0.974 | 0.982 | fail |
| 45 % | 6,205 | 18.3 / 90.1 | 0.912 | 0.960 | fail (tail facets) |

## Round 2: texture-aware decimation (after the user's review)

Blender's collapse slid the belly plates apart where it merged vertices across the belly's UV split. Locking UV seams
froze 62 % of this Meshy mesh's vertices (no reduction). MeshLab's texture-aware quadric decimation
(`scripts/dump_mesh.py` -> `scripts/decimate_tex.py`, run in a venv with pymeshlab and scipy; OBJ in/out because
MeshLab needs a textured material per face) collapses seams consistently on both sides; skin weights come back by
data transfer from the source (`reduce_ladder.py`, `REA_METHOD=texture`). MeshLab's "selected only" mode does not
decimate with textures, and cutting the head out moved the cut edge (cracks), so this route has no head protection;
the texture term keeps the face detailed anyway.

| step | triangles | p99 / max mm | IoU min | SSIM | |
|---|---:|---|---|---|---|
| 70 % | 9,651 | 1.2 / 5.4 | 0.996 | 0.9995 | pass |
| 55 % | 7,583 | 1.7 / 7.6 | 0.991 | 0.998 | pass |
| 40 % | 5,515 | 2.4 / 9.7 | 0.985 | 0.995 | pass |
| **35 %** | **4,825** | 2.8 / 9.7 | 0.980 | 0.993 | **picked** |
| 30 % | 4,135 | 3.2 / 9.7 | 0.978 | 0.991 | fail |

Belly close-ups (`review/close/`): plates continuous at 55 % and 35 %. Viewer (`review/viewer/`): every tier at 100 /
55 / 40 / 35 %.

Next for a batch: per creature, run the ladder, show one sheet, then (on acceptance) export the picked mesh through the
creature's existing runtime chain (prepare -> LODs -> burn maps if any -> region variants -> install) and its actor
regression. Below about 50 % the protected head eats the budget and the body collapses; a lower protection factor or
per-part protection (fins, claws) would go further at more review cost.

## Round 3: 35 % + new teeth + Meshy retexture (timed test, 2026-10-13, not installed)

User request: take the 35 % step, fix the teeth by hand, retexture head and body with Meshy, apply, time it.

- `scripts/build_r35.py`: `part` labels per connected piece (majority of nearest source vertices; per-vertex labels
  painted the skin beside spines and teeth ivory), the 20 lumpy Meshy teeth (143 tris after reduction) replaced by
  6-sided cones (200 tris) on the bone each tooth had (upper hang from the top of their blob, lower rise from the
  bottom, root sunk 35 % into the gum), fresh smart-project UVs per texture set, Meshy uploads. 4,882 triangles.
- Meshy: `requests/{body,head}_texture_r35.json` (the accepted v2 requests and references), 20 credits, both back in
  about 2 minutes. UV parity exact (0 unmatched corners).
- `scripts/r35_texture_chain.sh`: UV parity, raster, AO, compose, export, prepare, LODs (4,882 / 2,428 / 844 / 254),
  shadow LODs, region variants, head merge, viewer tiers: 67 s.
- Review: `review/teeth/sheet_final_tex.png` (open mouth, accepted vs new), `review/r35/`; viewer models `*_r35t`.

| Phase (wall clock) | Time |
|---|---:|
| teeth fix incl. three rule iterations and close renders | ~5 min |
| Meshy body + head retexture | ~2 min |
| texture/runtime chain (one run 67 s; run twice after a labelling fix) | ~3 min |
| review renders + viewer check | ~2 min |
| **total, 21:50 -> 22:03** | **~12 min** |

Repeat runs on another creature reuse every script; the teeth rule is lizard-specific (teeth as separate pieces).
