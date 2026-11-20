# MM6 New Sorpigal decorations

[Open the comparison and animation viewer](review.html) · [All enhanced/native comparisons](review/comparison_dark.png)
· [Light-background comparison](review/comparison_light.png) · [Exact source inventory](inventory.json)

**Installed in the isolated enhanced New Sorpigal playtest.** Run
`./level_generation/creatures/mm6_peasants/play.sh enhanced` and load a New Sorpigal save; restart an already running
game. Only `mm6/oute3.odm` selects these decoration images. Other maps and original mode keep native decorations.
No original BMPs, maps, events, sprite tables, saves or settings were modified by decoration installation.

The map contains **479 decoration placements**, using **22 descriptor names**: 20 visible-art types and two start
markers. The map script also selects `swrdstx`, making **23 types/states** in this inventory. The complete source
set is **54 unique BMP images**. Names and actual filenames differ (`6rock01` → `rok1`, `sta1a` → `fount1` etc.).
Scene entity overrides and map-script `SetSprite` targets are included; filtering filenames by a `6` prefix is insufficient.

**13 built-in imagegen calls produced 19 enhanced images**, covering 15 static descriptor types/states and the
five stored ship directions. These correspond to 465 initial placements. Six animated types (12 placements,
35 unique images) retain their native artwork and timing. The remaining two placements are start markers.

## Complete decoration list

“Frames” is the number of native timeline entries, not necessarily the number of different images.

| Map decoration/state | Native hint | Placements | Frames | Actual image stems | This pass |
| --- | --- | ---: | ---: | --- | --- |
| `6flower02` | flowers | 16 | 1 | `6flower02` | AI enhanced, 2x |
| `6flower07` | flowers | 16 | 1 | `6flower07` | AI enhanced, 2x |
| `6rock01` | rock | 41 | 1 | `rok1` | AI enhanced, 2x |
| `6tree01` | tree | 213 | 1 | `6tree01` | AI enhanced, 2x |
| `6tree02` | tree | 103 | 1 | `6tree02` | AI enhanced, 2x |
| `6tree03` | tree | 13 | 1 | `6tree03` | AI enhanced, 2x |
| `6tree04` | tree | 8 | 1 | `6tree04` | AI enhanced, 2x |
| `6tree05` | tree | 16 | 1 | `6tree05` | AI enhanced, 2x |
| `6tree06` | Food Tree | 6 | 1 | `6tree06` | AI enhanced, 2x |
| `6tree19` | tree | 18 | 1 | `6tree19` | AI enhanced, 2x |
| `bigbarel` | barrel | 4 | 1 | `bigbarel` | AI enhanced, 2x |
| `bouy0` | buoy | 1 | 10 | `bouy0`, `bouy1`, `bouy2`, `bouy3`, `bouy4`, `bouy5` | Native animation retained |
| `ckfyr00` | fire | 5 | 6 | `ckfyr00`, `ckfyr01`, `ckfyr02`, `ckfyr03`, `ckfyr04`, `ckfyr05` | Native animation retained |
| `fla3__01` | flag | 1 | 8 | `fla3__01`, `fla3__02`, `fla3__03`, `fla3__04`, `fla3__05`, `fla3__06`, `fla3__07`, `fla3__08` | Native animation retained |
| `party start` | null | 1 | 0 | — | Marker; no image |
| `searka01` | rock | 1 | 6 | `searka01`, `searka02`, `searka03`, `searka04`, `searka05`, `searka06` | Native animation retained |
| `searkb01` | rock | 1 | 6 | `searkb01`, `searkb02`, `searkb03`, `searkb04`, `searkb05`, `searkb06` | Native animation retained |
| `shp` | Ship | 1 | 1 | `shp0`, `shp1`, `shp2`, `shp3`, `shp4` | AI enhanced, 2x |
| `sta1a` | Statue | 3 | 3 | `fount1`, `fount2`, `fount3` | Native animation retained |
| `swrdstn` | A Sword in a Stone | 1 | 1 | `swrdstn` | AI enhanced, 2x |
| `swrdstx` | rock | 0 | 1 | `swrdstx` | AI enhanced, 2x |
| `tree06a` | Empty Food Tree | 9 | 1 | `tree06a` | AI enhanced, 2x |
| `west start` | null | 1 | 0 | — | Marker; no image |

`tree06a` is called “Empty Food Tree” in the merged descriptor table but its actual correctly paletted native image
shows fruit; `6tree06` shows no visible fruit. This pass follows the source artwork and existing event references,
without silently swapping their names or changing gameplay. Both appearances share exactly the same restored
foliage/trunk/alpha; only fruit changes. Likewise, `swrdstn` and `swrdstx` share the same boulder pixels at native
bottom alignment. `swrdstx` has zero initial placements but is selected after the sword interaction.

## Animated billboards

The cooking cauldron exists: **`ckfyr00`** is a suspended kettle/tripod above animated fire (six frames, five placements).
The other native animations are the buoy (ten timeline entries reusing six images in a forward/back loop), red flag
(eight frames), two rocks with moving surf (six each), and the fountain (three frames).

For this first scenery test, retain those animations completely. Freezing a cauldron/flame or fountain to one enhanced
frame would lose motion. Independently redrawing every frame risks flickering rigid geometry. A later animation pass
should restore one complete short native sequence in a sheet, lock the rigid kettle/stand/pole/rock/fountain body,
and vary only fire/water/cloth. The current viewer plays the exact native sequences so this decision is reviewable.
There are no new intermediate frames or altered light/event/collision properties.

The ship is **not a timeline animation**: it has five stored directions plus native mirrored views. Its five views
were enhanced together to maintain hull, spars and rigging identity. It keeps the source's mostly furled sails and
native scale 9.0, with per-view canvases and native bottom alignment retained.

## Export and review

- `native/`: correct native palette and index-zero transparency, for every referenced image.
- `references/`: original edit targets, catalogue and complete native animation sheets.
- `prompts/`: exact prompts submitted through built-in imagegen; no paid API fallback was used.
- `raw/`, `cleaned/`: generated sheets and full-detail matte extraction masters.
- `enhanced/`: the 19 shipping RGBA PNGs; each canvas is exactly twice its native width/height.
- `sheets/`: transparent static/state/view sheets for review and reuse; individual shipping PNGs remain authoritative.
- `manifest.json`, `registration.json`, `generation.json`: intended map scope, native descriptors/frames, pixel
  scale, palettes already baked into RGB, source/target bounds, tonal correction and selected output hashes.
- `validation.json`, `review/edge_closeups.png`: final size/alpha/spill checks and final contours on light/dark backgrounds.

Magenta matting is used except for the pink blossom tree and purple flowers, which use cyan to protect their actual
colors. Matte contribution is removed before premultiplied-alpha resizing, with a second contour correction after
resampling. All final images pass the 16/255 contour spill threshold for their own matte hue. This is an estimated
alpha reconstruction; thin leaf edges, stems and rigging remain interpretations of the low-resolution source.

A restrained deterministic tonal correction matches each source's luminance. Green tree foliage also receives a
selective red/blue ratio correction from its native palette, to avoid the generator's yellow/olive shift; bark and
pink/red foliage are protected. No AI pass is spent on those color corrections. State locking reuses common pixels
rather than accepting small model-induced changes across interactions. Details are still newly interpreted artwork,
not recovered original high-resolution renders. Leaves, bark grain, rivets and ship rigging differ in fine detail.

Shipping PNGs: **4.10 MiB**; decoded RGBA: **12.73 MiB**.
The matching 19 native BMPs occupy 0.82 MiB on disk and
3.18 MiB as decoded RGBA. Doubling both dimensions means 4× decoded
pixels. This is shared artwork, not multiplied by 465 placements. Runtime mipmaps/padding would add separate cost.

## Reproduce / installation

```sh
python3 level_generation/decorations/mm6_new_sorpigal/prepare.py
python3 level_generation/decorations/mm6_new_sorpigal/process.py
python3 level_generation/decorations/mm6_new_sorpigal/build_review.py
```

These commands use accepted AI outputs and do not make new image-generation requests. The saved reference inputs,
exact prompts and raw outputs retain the generation provenance. `prepare.py` inventories the current authoritative
map/table data; review changes before regenerating from a different native baseline.

After building the current executable, install or refresh only this package with:

```sh
python3 level_generation/creatures/mm6_peasants/prepare_decorations.py
```

Use `--directory /absolute/playtest/path` for another prepared snapshot. Normal playtest preparation and `--update`
also include decorations. The installer verifies source hashes/dimensions, preserves saves/settings, and refreshes
the executable. It writes a private `worlds/mm6/rendering/decoration_overrides/oute3.odm/manifest.yml` alongside 19 PNGs.

The shared map loader reads `worlds/<world>/rendering/decoration_overrides/<map-file>/manifest.yml` only for the
selected map. Schema version 1 lists `textures` entries with native `name`, `palette_id` (cache identity only),
PNG `file` in the same directory, `logical_size: [width, height]`, and integer `pixel_scale`. Missing manifests keep
native artwork; malformed manifests, missing declared images or incorrect dimensions fail loading explicitly.
Script-only appearances are preloaded too. Selected native textures are skipped instead of loaded a second time.

Native retained animations remain 1x: **do not divide every decoration's dimensions by two globally**. Decode
replacement PNGs as RGBA without applying the indexed BMP palette again. Preserve descriptor IDs, animation timing,
mirror flags, frame scale, events, light radius and collision dimensions. Full native canvas sizes preserve the
existing bottom-center anchor. This uses the existing decoration billboard filtering and opacity picking path;
it does not use the actor atlas/mask shader or its atlas mipmaps.

Focused loader tests cover exact world/map isolation, native logical dimensions, unkeyed RGBA and alpha preservation,
invalid metadata, duplicate entries and missing/wrong-sized images. A native game smoke capture is in `review/runtime/`;
full artistic acceptance remains an in-game review.
