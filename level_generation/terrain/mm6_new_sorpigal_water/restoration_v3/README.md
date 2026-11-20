# Water seam repair v3

This fixes the local lines reported in `test_img/1278.png`. V2 had discontinuities in the exported
frames that a whole-edge average did not catch. Clamped runtime sampling also left thin lines
between otherwise continuous water tiles.

The [review](review.html) contains enlarged offset comparisons, all fourteen frames, native
low-angle before/after captures and animation. [prompt.txt](prompt.txt) records the built-in
imagegen seam-repair request; its retained output is `seam_repair_raw.png`.

Only the outer 24 pixels of each 256px water frame are repaired. The central 208×208 pixels remain
identical to v2. The original palette, wave scale and fourteen-frame timing remain the reference.
Periodic Poisson insertion transfers connected wave gradients without averaging incompatible
patterns into blurry strips. Motion-aligned filtering stabilizes the repaired strip across the
loop. The 36 land tiles and 12 shared-dirt shoreline overlays remain byte-identical to v2.

The renderer binds its existing terrain array through two samplers: repeat for water, clamp for
land and shore overlays. There is no second texture allocation or new draw call. This engine change
is required alongside the textures; the ZIP alone does not include it.

## Rebuild

```sh
python3 level_generation/terrain/mm6_new_sorpigal_water/restoration_v3/build.py
python3 level_generation/terrain/seam_repair/validate.py --directory level_generation/terrain/mm6_new_sorpigal_water/restoration_v3
cmake --build build --target openyamm -j25
```

After artwork or renderer changes, recapture the flat fixture with the rebuilt executable before
running `review.py`. It validates retained captures and does not launch the game. Capture records
include executable hashes; both sides use the same camera and flat map. The after run includes
the sampler correction, and animation/sky phase can differ between runs.

```sh
python3 level_generation/terrain/mm6_new_sorpigal_water/restoration_v3/review.py
python3 level_generation/creatures/mm6_peasants/prepare_playtest.py --terrain-only
```

`--terrain-only` retains the prepared executable. The default playtest has separately received the
verified rebuilt executable for the sampler correction. Fresh preparation uses the current build.
Prior terrain is backed up under `seed/terrain_before_native_water_v3`.

Checks cover 332 legal map joins across all fourteen frames, local 16-pixel edge windows compared
with interior gradients, animation loop closure, motion-compensated temporal differences and
28 native samples showing water movement with stationary land. Local checks would reject v2.
These screening checks accompany enlarged visual inspection; they do not certify full-frame-rate
shimmer or hardware GPU performance.

Restart `./level_generation/creatures/mm6_peasants/play.sh enhanced` after installation.
