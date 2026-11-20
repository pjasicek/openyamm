# v10 — clean Alvar road connections

Fixes1300/1301: v8 averaged diagonal edge colours into all36 road textures, causing repeating ghost stones and grey dirt protrusions. v9 retained those edges. This revision restores28 non-diagonal road tiles byte-for-byte from v7, and fits eight diagonal variants to those clean connections.

The final pipeline is `build.py`, using retained native substrate inputs, four built-in imagegen endpoint repairs, and a screened harmonic fit to clean v7 boundary pixels. Original approved diagonal masks are retained. Repaired stone artwork remains crisp. `repair_prompt.txt`, `repair_inputs/`, `raw/` and `generation.json` retain generation provenance.

`quilt_endpoints.py`, `finish.py`, `quilted_paths.png` and the earlier captures/temporary candidates are experiments, not the build entry point. Direct colour bands and minimum-error donor strips were rejected because they still produced contour or stone artifacts. Do not run them over the final runtime directory.

Focused review: `straight_comparison.png` shows the repeating Alvar smear removed in both straight directions. `connections.png` compares v9/v10 along the native Dagger entry/exit and opposite diagonal repeats. The Alvar capture uses the clean restored straight-road hashes; the final Dagger capture uses the full final pack. `visual_review.json` binds the reviewed assets and images.

No full gallery or ZIP rebuild: installed assets and complete export are current; broad gallery, ZIP and historical completion audit remain earlier snapshots.
