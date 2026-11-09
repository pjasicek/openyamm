# New Sorpigal — original / enhanced residents, terrain and sky

Enhanced mode includes **19 AI-enhanced decoration images at 2x**, scoped specifically to `mm6/oute3.odm`.
Trees, flowers, static rocks/props, both fruit-tree and sword/stone appearances, and five ship views use the new art.
Cauldron/fire, fountains, flag, buoy and surf-rock animations keep their native frames/timing. World sizes,
collision, interactions and ground anchors remain native. Other maps and original mode keep original decorations.
[Inventory and visual comparisons](../../decorations/mm6_new_sorpigal/README.md).

Restart the game and launch `./level_generation/creatures/mm6_peasants/play.sh enhanced` as usual.
Normal preparation and `--update` include decorations. To refresh only decoration art and the executable:

```sh
python3 level_generation/creatures/mm6_peasants/prepare_decorations.py
```

This preserves saves, settings, and all other enhanced art. The private override lives under
`enhanced/assets_dev/worlds/mm6/rendering/decoration_overrides/oute3.odm/`.


Enhanced mode now includes the reviewed **imagegen x2 sky** (`plansky1`, 512×512), with
`video_quality.sky=x2`. The default snapshot is updated: launch `play.sh enhanced` as usual and restart
an already running game. The other six Enroth weather textures are explicit nearest-neighbor x2 exports
of the native artwork, preserving their original colors and weather choices; they are not AI restorations.
The current executable includes the projection correction that keeps x2 clouds at their original apparent size.

Normal preparation and `--update` include the sky. To refresh only the sky and executable in an existing snapshot:

```sh
python3 level_generation/creatures/mm6_peasants/prepare_playtest.py --sky-only
```

This preserves saves, other enhanced art, other quality preferences, and original-mode settings/assets.
Use `--directory /absolute/path/to/playtest` for another snapshot. The two modes share the refreshed executable.
[Sky before/after review](../../skies/mm6_new_sorpigal/review/index.html) and combined playtest screenshots under
`review/combined_sky_x2/` document the result. Sky staging additionally requires ImageMagick's `convert` and Pillow.

The default enhanced playtest also includes **1,530 ESRGAN x2 surface textures** for bmodels and indoor
geometry, with `video_quality.texture=x2`. Launch it using the same command below. Terrain remains x2
and all installed restored creature families remain available.

To add these textures to a newly prepared snapshot, or refresh only the building-texture pack:

```sh
python3 level_generation/creatures/mm6_peasants/prepare_model_textures.py
```

Use `--directory /absolute/path/to/playtest` for a custom snapshot. The installer checks source hashes,
copies only the manifest-listed PNGs into the enhanced world's private `textures_x2/` directory, and
changes only the texture-quality setting. Saves, terrain, sprites, executable and original mode are
preserved. The default snapshot has already been updated. Restart the game to load changed assets.
Native smoke-capture evidence is under `review/combined_models_x2/`.

From the repository root:

```sh
./level_generation/creatures/mm6_peasants/play.sh enhanced
./level_generation/creatures/mm6_peasants/play.sh original
```

Run one at a time. Choose **Load Game** and the supplied starting save (the only save initially).
Both modes receive identical copies of the existing New Sorpigal town-road save, including party, time,
camera and world state. This save contains a five-member test party and 50,000 gold.
Settings initially copy your current repository settings; each mode then saves its own preferences.
Enhanced mode uses the **complete MM6 pack: 134 terrain PNGs at 256×256**, covering all 15 outdoor maps.
The 71 additions comprise sand, snow, cracked, tropical and swamp masters, their 60 dirt transitions, and six extra road variants.
The earlier 63-texture set is preserved byte-for-byte:
36 land tiles, 12 shore overlays, a water fallback and 14 animation frames. The 36 accepted fuller-dirt land tiles and 15 water tiles are preserved exactly;
twelve shoreline overlays use that same repeating dirt with retained coverage and a broader shaded, granular bank (shorelines v2). Water v3 repairs the seams in the restored original fourteen animation frames with imagegen,
retaining their dark navy palette, warm highlights and ripple scale. The default snapshot also has the rebuilt
renderer with repeat sampling for water; land and shore sampling remains clamped. Shore earth uses the same accepted dirt material.
[Before/after and animation review](../../terrain/mm6_new_sorpigal_dirt_fidelity/transitions/shorelines/review.html).

Normal preparation, `--update` and `--terrain-only` install this combined pack and the reviewed
12-cell terrain map correction. The default snapshot has been updated. Previous tiles are retained
under `seed/terrain_before_mm6_complete_v1`; saves and other enhanced assets are preserved.

```sh
python3 level_generation/creatures/mm6_peasants/prepare_playtest.py --terrain-only
```

The enhanced mode replaces `pfem`, `pman`, `pmn2` (mages), `gob` and `gua` (guards) appearances through their native animation groups. The source
map has 21 female peasants (variants 10/2/9), 17 male peasants (1/9/7), and five guards (descriptor 553).
Native actor/monster IDs, NPC links, animation IDs, timing, flags, mirrors, scale and palette IDs remain intact.
Base and mask pages are shared by the three appearances in each family. No extra monsters are added.
Mages include Apprentice/Journeyman/Mage, and goblins include Goblin/Shaman/King, with their native scale and
animation differences retained. Goblins use an RG8 mask to recolor skin and equipment independently; mages and
the two town-peasant families use R8 masks. Guards use four RGBA8 material weights for sleeves, trousers,
mail highlights and the remaining materials, with palettes 748/749/750 sharing all 59 restored images.
Mask alpha is a material weight; sprite opacity comes from base alpha. No baked variant texture copies are installed. Enhanced sprites also use [atlas-safe mipmaps](../SPRITE_ATLAS_MIPMAPS.md)
for distance filtering; the shared GPU pages require additional padding/mip memory.
The other five restored peasant families are not installed by this test.

These are texture-reference replacements in the isolated runtime, not map-scoped overrides: visiting another
map in that runtime also enhances any actors using these five families. Original development assets and the
separate `pmn2` custom-monster installation are untouched.

## Saves and isolation

The prepared runtime lives at `/tmp/openyamm-sorpigal-peasants-playtest/`:

- `original/` and `enhanced/`: separate settings, saves, data tables and rendering tables.
- `enhanced/assets_dev/engine/sprites_new/mm6_pfem/`, `mm6_pman/`, `mm6_pmn2/`, `mm6_gob/`, `mm6_gua/`: shipping base/mask PNGs and compact JSON.
- `enhanced/assets_dev/worlds/mm6/terrain_x2/`: private copies of all 134 MM6 terrain textures.
- `seed/New_Sorpigal_Start.oysav`: preserved starting save.
- `playtest_snapshot.json`: source/save/binary hashes and texture binding counts.

Normal launches preserve saves. To restore only the supplied start in either mode:

```sh
./level_generation/creatures/mm6_peasants/play.sh enhanced --reset-start
```

This overwrites that mode's `New_Sorpigal_Start.oysav`; other save slots remain intact.
Load the supplied start in each mode for an A/B comparison, rather than differently progressed saves.

The executable and editable data are copied. Large original art directories, maps and events are mounted from
the repository, and the development executable uses `build/runtime/shaders`. Keep the checkout/build available;
this is an isolated playtest, not a portable frozen distribution. `/tmp` may be cleared on reboot.
Preparation does not launch the game. A combined native smoke capture is retained under
`review/combined_terrain/`; artistic acceptance remains yours.

## Prepare again

```sh
python3 level_generation/creatures/mm6_peasants/prepare_playtest.py
```

Preparation requires the existing `build/game/openyamm`, Python PyYAML, and the completed restoration packages.
The executable must include `masked_regions_luminance_rgb_v1` support for goblins and
`multi_mask_luminance_rgb_v1` support for guards. Build engine changes with
`cmake --build build --target openyamm -j25` before preparing or updating the playtest.
It refuses an existing destination to protect personal saves. For another snapshot:

```sh
python3 level_generation/creatures/mm6_peasants/prepare_playtest.py --directory /tmp/sorpigal-peasants-v2
OPENYAMM_SORPIGAL_PEASANTS_DEMO=/tmp/sorpigal-peasants-v2 ./level_generation/creatures/mm6_peasants/play.sh
```

`--source-save /absolute/path/to/save.oysav` selects another existing New Sorpigal start for both modes.
No AI generation, engine rebuild or global monster registration is part of preparation.

To update a prepared installation's enhanced assets and executable while preserving both modes' saves
and preferences (terrain and sky quality are set to x2):

```sh
python3 level_generation/creatures/mm6_peasants/prepare_playtest.py --update
```

Restart the playtest after an update; already loaded sprites are cached. Existing saves work without restarting
the campaign. Updating uses the snapshot's original animation table as its baseline and changes only texture names.
The goblin's offline art schema v2 is exported explicitly into the compact runtime schema v1; its two-region
operation remains `masked_regions_luminance_rgb_v1`. The accepted source manifests are not rewritten.

To add or refresh only the terrain while retaining the prepared executable and restored sprite packages:

```sh
python3 level_generation/creatures/mm6_peasants/prepare_playtest.py --terrain-only
```

This has already been applied to the default playtest. Normal `play.sh enhanced` launches both sprites and
terrain together. Restart after changing assets. `original` remains available for comparison.
Terrain source: [complete pack and review](../../terrain/mm6_remaining/transitions/index.html).
[Installation preservation audit](../../terrain/mm6_remaining/transitions/reports/integration.json).
