# NE2 road edge repair — v12

Installed `drsrne2.png` and `gdrdne2.png` only. All 34 other cobble-road textures, including every straight, remain byte-identical to v11. The other 237 terrain textures and 64,077 nonterrain asset entries were preserved.

[Exact-pose comparison](exact_pose_comparison.png) and [final capture](captures/mm8_1303_registered.png) show the supplied Dagger Wound pose: position `(7766.500,3508.695,545)`, yaw `1.782` radians, pitch `-26.385` degrees. The upper bank now curves into the straight road without vertically sliced stones; the lower ghost fragment is removed and grout contours connect. Colours were reviewed in this capture. Grey-dirt uses the same geometry over its own master and was checked offline.

Two built-in imagegen calls are retained in `raw/`, with exact prompts in [prompts.json](prompts.json). The first full-context contour repair still left a clipped junction and was rejected as a final candidate. The second used a full two-tile pair and explicitly required rounding the diagonal inward above the straight road. Only its diagonal half is used.

`build.py` extracts fresh coverage instead of applying the obsolete native mask, composites over accepted dirt with contact shadow, and locally registers lower grout rows to the immutable straight neighbour. The last 48 diagonal pixels receive a smooth vertical registration; no straight donor strip is grafted. The east boundary is matched to the actual straight tile. Auxiliary silhouette masks are closed, filled, and single-component.

Lessons: preserving defective boundary pixels can perpetuate clipping despite new AI interiors; show the complete adjoining tile and explicitly describe the concave road turn. Generated boundary grout needs registration to the immutable neighbour before compositing. Seam metrics alone do not detect sliced stones. Review the actual pose before installation.

Validation: 724 compatible road joins pass; all 36 auxiliary masks are single-component and hole-free. Recomputed all 448 complete-pack contacts involving these two tiles, zero failures; 23,980 unchanged checks reused with hash verification. Final capture stage matches all 239 exported file hashes. Installed-pack verification passes. Broad gallery, ZIP and historical audit were not rebuilt.

Run from the repository root: `./level_generation/terrain/mm8/play.sh enhanced`.
