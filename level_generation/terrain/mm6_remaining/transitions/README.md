# Complete MM6 terrain x2

134 runtime PNGs: all 120 static terrain names used by the 15 MM6 outdoor maps, plus 14 water animation frames.

- Five 256px masters, with the corrected tropical v3 artwork; other four masters unchanged from v2.
- Sixty material-to-dirt transitions: sand, snow, cracked, tropical and swamp, twelve directional variants each.
- Six additional cobble roads, joined to the existing roads' accepted coverage and shading profiles.
- All 63 accepted New Sorpigal terrain/water files preserved byte-for-byte.

Coverage and contact shading are recovered from the original tile artwork and transferred onto the accepted restored materials. Snow keeps its broad soft mixing; vegetation keeps irregular edges; sand and cracked ground retain their original boundary treatment. Original low-resolution colour grain is not overlaid onto the masters. Authoring masks and scalar shading fields are retained under `masks/`, `shading/` and `fields/`. Shading PNG neutral value is 200; NPZ stores the actual floating-point multiplier.

[Review gallery](index.html) · [Validation](reports/validation.json) · [Combined runtime ZIP](mm6_complete_terrain_x2.zip) · [Master review](../masters/v3/index.html)

## Validation and limits

All five master wrap checks pass. All 1,526 compatible tile joins pass the local 16px boundary-window tests against neighbouring/interior gradients, including new-to-existing road joins. Closed islands and inward corners show all 60 material transitions. The unchanged older pack retains its 332-join, full 14-frame water-cycle validation; its files are hash-checked here.

The shipped map layouts also contain 184 distinct incompatible neighbour pairs. These are recorded with map/cell locations in `reports/native_layout_mismatches.csv`, with original-versus-restored examples. The pack does not repair those map placements. Passing compatible asset joins is not a claim that every shipped map layout is seamless.

## Iteration policy

1. Edit the authoritative master or native coverage/shading extraction; preserve material phase and accepted file hashes.
2. Rebuild with `python3 level_generation/terrain/mm6_remaining/transitions/build.py`.
3. Run `check.py`. Any compatible-join failure blocks acceptance. Never weaken thresholds to hide a bad join.
4. Visually inspect master repeat/offset previews, every family island and dirt-hole fixture, road originals/composites, native contexts, and worst boundary windows. Numerical checks alone do not detect all internal artistic artifacts.
5. Rebuild the isolated fixtures with `prepare_review.py` and capture with the existing gameplay capture tool. Review engine filtering and oblique views; bind capture metadata to the current map, executable and texture hashes.
6. Run `review.py` to verify and package. Preserve source evidence and previous accepted versions. Native layout mismatches remain explicit map work, not texture exceptions.

## Runtime use

The ZIP contains `worlds/mm6/terrain_x2/*.png` and `manifest.json`. Overlay the `worlds` directory into the desired staged `assets_dev` and set `[video_quality] terrain = x2`. Existing filenames replace terrain only. No engine code, sprites, decorations, bmodel textures, or map placements are included. The current peasants-enhanced playtest was preserved; native captures use a separate `/tmp/openyamm-mm6-complete-terrain-review` copy.

`prepare_review.py` currently uses the existing local editor build, peasants playtest and `/tmp/sorpigal-transition-capture-save` helper. Flat map sources and built ODM fixtures are preserved in `fixture/`; those external local prerequisites are needed only to recreate engine captures, not to use the ZIP.

## Main playtest installation

The complete pack is now installed into `play.sh enhanced`: 71 new textures added, all 63 previously installed textures unchanged, and 4,002 other file hashes/symlink targets preserved. See [installation audit](reports/integration.json). Restart the game after installing. Future `prepare_playtest.py --terrain-only` runs use the complete pack.
