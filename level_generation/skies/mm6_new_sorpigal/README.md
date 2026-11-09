# New Sorpigal sky — imagegen ×2

Open [the before/after review](review/index.html). This pass restores the fair-weather `plansky1` cloud texture
used by the saved New Sorpigal review state (`oute3.odm`). The export is **512×512 opaque RGB PNG**, twice the
256×256 runtime source in each dimension.

Installed asset: `assets_dev/worlds/mm6/textures_x2/plansky1.png`. The identical authoring export is
[runtime/plansky1.png](runtime/plansky1.png). Main `settings.ini` was not changed. The review profile uses
`[video_quality] sky=x2`; the remaining quality categories use x1, allowing the sky change to be judged separately.
This is a single-texture restoration, not a complete sky/weather tier. Do not treat this partial tier as a
replacement for all weather assets: sky lookup uses the selected tier's directory and this pass does not provide
the other weather textures. No source BMP or map/weather table was overwritten.

The [peasants enhanced playtest](../../creatures/mm6_peasants/PLAYTEST.md) installs this texture and six explicit
native x2 weather exports into its private asset tree, enables sky x2, and refreshes its executable.
Its default snapshot is ready for `./level_generation/creatures/mm6_peasants/play.sh enhanced`.
Run `python3 level_generation/creatures/mm6_peasants/prepare_playtest.py --sky-only` to refresh an existing snapshot;
normal preparation and `--update` also include the sky. The main development asset tier remains partial.

## Source and generation

The mounted `plansky1` source is `assets_dev/worlds/mm8/textures/PLANSKY1.bmp`; it is byte-identical to
`assets_dev/worlds/mmmerge/textures/plansky1.bmp`. Both are 256×256. The 512×512 native MM6 `6plansky1.bmp`
contains the same cloud pattern with a darker palette and was supplied only as supporting detail/layout reference.
It is not the 1× size of the runtime texture restored here. The decoded source copies are in `source/`.

The built-in `image_gen` tool edited the runtime source using [prompt.txt](prompt.txt). The prompt requests
faithful cloud placement, restrained wispy detail, the muted blue/cream palette, and repeating edges on both axes.
The saved tool output is `generated/plansky1_v1.png`; its actual dimensions are recorded in `manifest.json`.
ImageMagick Lanczos reduction produces the exact runtime size, without sharpening, palette correction, or seam
painting:

```sh
convert level_generation/skies/mm6_new_sorpigal/generated/plansky1_v1.png \
  -filter Lanczos -resize 512x512 -alpha off \
  PNG24:level_generation/skies/mm6_new_sorpigal/runtime/plansky1.png
```

## Runtime correction

`game/outdoor/OutdoorRenderer.cpp`, in `renderOutdoorSky`, now passes the existing logical sky width/height to
all four projection vertices. Previously it passed physical dimensions, making an x2 image enlarge the cloud
pattern and slow its normalized drift. GPU texture upload still uses physical dimensions. At x1 the logical and
physical dimensions are identical, so the projection is unchanged. No rendering architecture or weather behavior
was added for this asset.

## Visual review and checks

- `review/sky_original.png`: original x1 sky at the requested position.
- `review/sky_ai_x2.png`: imagegen x2 sky at the same saved position and weather/time state.
- `review/sky_ai_x2_pose.png`: console verification of position (-9954.209, -9427.790, 161.000), heading units 475,
  yaw 83.552°, pitch 25.955°. The 0.002° difference from the supplied degree value is immaterial.
- `review/sky_ai_x2_horizon.png`: same position, yaw 173.552°, pitch 5°, with rooftops and distant terrain.
- `review/tiled_v1.png`: 2×2 repeated export, inspected for hard cuts and edge discontinuities.

The restored cloud wisps are more distinct while the original diagonal bands, blue openings, apparent scale,
and subdued game lighting remain recognizable. No conspicuous hard tile seams were seen in these views or the
2×2 sheet. The edges are not mathematically identical: average RGB wrap differences are 2.48/255 left-right and
4.57/255 top-bottom; retain visual review when extending this to other skies. Ordinary repeating cloud structure
and perspective compression near the horizon remain part of the native presentation.

These are real OpenGL game captures under isolated Xvfb displays, not texture mockups. Both runs use the same
save; wall-clock cloud animation and ordinary actors can differ slightly between captures. The horizon capture
also retains warm/final frames three seconds apart; it is not a comprehensive animation or GPU benchmark.
The original capture precedes the logical-dimension correction; both x2 captures use the rebuilt binary. Binary
hashes, settings hashes, and map hashes are retained in their capture JSON files.

Validation passed:

- `cmake --build build --target openyamm -j25`
- `cmake --build build --target openyamm_unit_tests -j25`
- `./build/tests/openyamm_unit_tests --test-case='*sky*,*Sky*,*scalePhysicalPixelsToLogical*'`
  (1 matching test, 8 assertions; sky asset lookup coverage, not a projection unit test).
- Exact 512×512 RGB export, matching installed SHA-256, and renderer diff whitespace check.

The capture save files and x1/x2 settings are retained in `review/`. Re-run from the repository root using the
existing capture helper (adjust the absolute asset root in the settings if relocating the checkout):

```sh
xvfb-run -a -s '-screen 0 1600x1200x24' \
  python3 level_generation/projects/brackenford_greywatch/capture_gameplay.py sky_repeat \
  --world mm6 --map oute3.odm \
  --stage /tmp/openyamm-sorpigal-sky/x2 \
  --review-directory level_generation/skies/mm6_new_sorpigal/review \
  --start-save level_generation/skies/mm6_new_sorpigal/review/view.oysav \
  --actions level_generation/terrain/mm6_new_sorpigal_master_study/references/capture_actions.json \
  --warmup 1 --seconds 0
```

For a fresh session, create the stage directory and copy `review/settings_x2.ini` there as `settings.ini` first.
Use `review/horizon.oysav` to reproduce the lower-angle review.
