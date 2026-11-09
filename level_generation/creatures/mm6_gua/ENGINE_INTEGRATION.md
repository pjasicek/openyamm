# MM6 guard runtime installation

The isolated [New Sorpigal playtest](../mm6_peasants/PLAYTEST.md) installs the accepted guard art under
`enhanced/assets_dev/engine/sprites_new/mm6_gua/`. Restart enhanced mode and load an existing save:

```sh
./level_generation/creatures/mm6_peasants/play.sh enhanced
```

The installer exports a compact schema-v1 manifest from the accepted art manifest and changes only native guard
texture references to `atlas:mm6_gua/<frame>`. The source art manifest retains its original staging metadata;
this document and the runtime snapshot record the subsequent installation. Descriptors 553–555 retain native actor behavior, palette IDs
748–750, timing, scale, mirror flags and animation groups. `guardang.bmp` is a spell sprite and remains native.
The existing five New Sorpigal guards use descriptor 553; the other appearances are available wherever their
native descriptors occur. Installing art does not add actors or change their combat statistics.

`multi_mask_luminance_rgb_v1` requires exactly four region vectors for each non-base variant. The shared parser,
cache and billboard shader support that contract for both indoor and outdoor rendering. PNG mask RGBA channels
become linear RGBA8 coverage, with no premultiplication or sRGB conversion. The fourth channel is a material
weight, independent of base opacity. The encoded-color operation matches the offline viewer:

```
Y = dot(base.rgb, [0.2126, 0.7152, 0.0722])
result.rgb = clamp(base.rgb * (1 - sum(mask)) + Y * sum(mask[k] * regionVector[k]), 0, 1)
result.a = base.a
```

Palette 748 bypasses recoloring. Lighting, fog, selection outline, picking, crop offsets and native animation
resolution use the existing shared paths. Each package page is cached once across actors and palettes.
Only shipping base/mask pages and compact JSON are installed; review and baked variant images stay offline.
The shared cache now also builds [atlas-safe mipmaps](../SPRITE_ATLAS_MIPMAPS.md). Runtime padding and mip
storage increase guard GPU allocation from 80.80 MiB to approximately 141.97 MiB; source PNG size is unchanged.

The installation preserves both modes' saves and settings, original-mode rendering data and the existing terrain
pack. Future normal `prepare_playtest.py --update` also refreshes terrain and selects x2 as documented by that
helper. Source development sprite tables and native BMPs remain unchanged.

Installation verified: game and GLSL shader build passed; all 12 focused `sprite atlas*` unit cases passed
(100 assertions). All 93 native guard frame bindings resolve across palettes 748–750. The eight installed PNGs
match the accepted exports; 41 save/settings/terrain/original-table files remained byte-for-byte identical.

For future changes, rebuild the game/shaders and run the focused `sprite atlas*` unit cases, including four-vector
validation, the real 59-frame package and RGBA mask decoding with nonzero RGB at zero alpha. The installer checks
every referenced frame/palette and verifies the animation table changes only texture names. In-game appearance
and animation acceptance remain a user playtest; this installation does not run gameplay scenarios.
