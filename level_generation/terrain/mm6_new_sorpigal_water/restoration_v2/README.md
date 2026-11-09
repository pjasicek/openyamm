# Faithful native water restoration v2

This replaces the brighter, finer-patterned water candidate with a conservative restoration of
the original fourteen MM6 frames. Runtime files remain 256×256. The 36 land tiles and 12 shared-dirt
shore overlays are byte-identical to `../../seam_repair`; only fourteen water frames and the static
fallback change. The earlier candidate remains available there for comparison and rollback.

[Visual review](review.html) includes an in-game original/restored slider at the user's reference
pose, animated repeats, all shoreline contexts and native animation samples. The
[combined runtime ZIP](new_sorpigal_terrain_x2.zip) contains 63 PNGs and their manifest.

The built-in imagegen tool restored the native frame atlas using [this prompt](prompt.txt).
The generated atlas is retained as `restored_atlas_raw.png`. Optical flow registers its fine detail
to each original frame; the export removes broad generated colour changes and bounds the added
detail. A periodic smooth-component correction removes boundary discontinuities from that residual,
without averaging texture strips. The original frame order and 15/128-second frame durations remain.

## Rebuild

```sh
python3 level_generation/terrain/mm6_new_sorpigal_water/restoration_v2/build.py
python3 level_generation/terrain/seam_repair/validate.py --directory level_generation/terrain/mm6_new_sorpigal_water/restoration_v2
python3 level_generation/terrain/mm6_new_sorpigal_water/restoration_v2/review.py
python3 level_generation/creatures/mm6_peasants/prepare_playtest.py --terrain-only
```

Python dependencies: Pillow, NumPy, SciPy, OpenCV. No new AI call is needed to rebuild from the
retained atlas. After changing artwork, recapture both native comparison runs and the restored
animation before running `review.py`; it checks retained captures and does not launch the game.
Capture provenance JSON and the pose save are under `captures/`.

Validation covers all 332 map joins across 14 frames, palette/broad-form correlation, loop closure,
and native-motion-compensated frame differences. The 28 native screenshots verify moving water
and stable land; they do not certify full-frame-rate shimmer or hardware GPU performance.
The comparison baseline uses original 128px runtime frames, while source art and restored exports
are 256px. Land, shoreline, camera and executable match between the two capture stages.

The enhanced playtest installer backs up the prior tiles under `seed/terrain_before_native_water_v2`
and preserves saves, other enhanced artwork and the executable. Restart the playtest after installing:

```sh
./level_generation/creatures/mm6_peasants/play.sh enhanced
```
