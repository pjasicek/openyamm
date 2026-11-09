# v9 stone material — GOOD

Addresses1299: keep the approved v8 outline, replace blurry native stone pixels with full generated artwork matched to the accepted straight-road material. Eight dirt/grey-dirt diagonal tiles changed;231 terrain textures unchanged. The masks and every tile boundary pixel are byte-identical to v8. Existing dirt and outside contact shading are preserved.

Built-in imagegen: four calls. Inputs, exact prompt and raw outputs are retained in `inputs/`, `prompts/material.txt`, `raw/`; hashes are in `generation.json`. Rebuild with `build.py`; then run `../v2/check.py --version v9`.

Focused visual review: `connections.png` shows v8 / v9 / v7, with native straight-road entry/exit above and repeated opposite diagonals below. `captures/mm8_diagonal_v9_material_b.png` is the final candidate in-game at the supplied pose. Stones are clearly defined, consistent with the accepted material, and the reviewed joins have no visible line/gap. `visual_review.json` records GOOD.

All724 road contacts checked. Complete validation rechecks contacts touching changed textures and retains previous checks only for hash-identical assets, via `validate_update.py`. No broad gallery or ZIP rebuild was requested: those remain v8 snapshots; the installed assets and export manifest are v9.
