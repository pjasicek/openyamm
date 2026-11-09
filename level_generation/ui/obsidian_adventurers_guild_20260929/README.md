# Adventurer's Guild — Carved Obsidian

Native replacement requested on 2026-09-29 for `test_img/2143.png`. The mounted screen is
`assets_dev/engine/ui/gameplay/adventurers_inn.yml`; the shared character renderer draws its live roster.

The new backdrop uses generated rough green-black stone with compact worn-brass corners. The reading inset uses
the existing quiet Obsidian material, soft ivory SMALLNUM text, and a fine divider before the biography.
Eight recessed slots retain the original 62 × 72 logical-pixel portrait rectangles and 3-pixel gaps. Selection
uses a thin gold frame. Hire and Exit use the shared Fondamento buttons; the new arrows have normal, hover,
pressed and disabled states. The original paging, selection, double-click inspection and hiring code is retained.
The top resource icons are visible again. The paperdoll, bottom party frame and status/input rail remain native.

## Artwork and export

- Mode: **built-in imagegen**.
- Exact prompt: [art/prompt.txt](art/prompt.txt).
- Unmodified generated master: [art/guild-panel-master.png](art/guild-panel-master.png), 1448 × 1086 RGB.
- Runtime backdrop: [obsidian_guild_panel.png](../../../assets_dev/engine/icons_x2/obsidian_guild_panel.png),
  920 × 688 RGBA, drawn at 460 × 344 logical pixels.
- [export_runtime.py](export_runtime.py) fits the frame by nine-slicing, reducing the corners to 28 logical pixels
  so they clear the original controls. It also exports eight vector arrow states at 2× resolution. SVG sources
  are preserved in `art/`; the direct vector rasterizer avoids this host's broken ImageMagick SVG stroke delegate.
- [native/export.json](native/export.json) records dimensions, paths, hashes and source provenance.

Run `python3 level_generation/ui/obsidian_adventurers_guild_20260929/export_runtime.py` to regenerate installed art.
All new filenames are lowercase, in the engine-owned `icons_x2` tier, with 0644 permissions.
No original portrait art or typography was generated.

## Native review

[Native screenshot gallery](native/index.html). The scripted desktop runs use private fixtures with two and twelve
real roster entries loaded through the mounted item/class/doll/roster tables. `native/prepare_fixture.py` rebuilds
those fixtures from the existing isolated one-member save; it does not write to ordinary saves.

The ordinary OpenGL development build, focused tests, input tours, native captures and run receipts are retained
under `native/`. This shared screen also supplies Android's current desktop layout; no separate Android layout
or APK validation is part of this replacement.

Validation completed: the development build passed; 24 focused Obsidian/guild tests passed (2,516 assertions).
Three isolated native OpenGL runs exited successfully at 1600 × 900 and 1200 × 900. Captures verify sparse and paged
rosters, both paging directions/bounds, selection, hiring, a full party's disabled Hire button, double-click inventory
inspection and return, Exit/Escape, and the clear status rail. See [native/validation.json](native/validation.json).
