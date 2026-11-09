# Meadow: ground moisture, plant layers and wildflowers

How the outdoor grass reads as a layered meadow rather than evenly spaced tufts: the ground's colour and the plants
follow the terrain's shape, uncut grass grows in patches and along verges, flowers grow in single-species clusters
and ferns ground the trees. The art direction target was a paintover of New Sorpigal (2026-10-15). The distance level
of detail and the terrain's far grass colour are in [Grass level of detail](GRASS_LOD.md); the paintovers are in
[`meadow/concept/`](meadow/concept/).

## Ground moisture (`game/outdoor/OutdoorMeadow.*`)

`buildOutdoorMeadowField` derives a value per terrain grid corner from the native heights and water tiles, -1 lush to
+1 dry: crests (relief against a 3-cell and a 10-cell Gaussian) and steep slopes are dry, the land within a few cells
of water lush, open flat ground neutral. It is computed at load and costs nothing per frame.

- **Terrain:** the materials mesh carries the value per vertex (`v_texcoord0.y`). Each layer's `meadow` strength
  (`u_terrainLayerTint.w`) tints it towards the map's `meadow: {dry, lush}` colours; macro noise frays the borders.
  Configure in `worlds/<world>/terrain_materials/world.yml` (top-level `meadow`, per-material `meadow`) and run
  `tools/terrain_materials.py weights` for every map.
- **Grass:** the plants sample the same field: `meadow.dry_tint`/`lush_tint` tint them, and `density` and `height`
  thin and shorten them on dry ground (and the opposite on lush ground).

## Plant layers (`worlds/<world>/terrain_decorations/families_v2.yml`)

The atlas `plants_v4.png` (4 x 4 cells of 256 x 192) is built by
[`meadow/process_art.py`](meadow/process_art.py) from Codex-generated magenta sheets (`meadow/art/raw`, brief in
`meadow/art/BRIEF.md`), the earlier `plants_v2` cells and, for cells 0-1, cards rendered from Poly Haven's CC0
`grass_medium_01` ([`meadow/clump_cards/`](meadow/clump_cards/README.md)):

| Cells | Plants |
| --- | --- |
| 0, 1 | Short meadow grass, one card of a clump each, colour-matched to the grass ground (the base layer) |
| 2, 3 | Mid and dry grass tufts |
| 4-9 | Reeds, tropical low plants, dead tufts |
| 10, 11 | Purple flower spikes, fern |
| 12, 13 | Tall seed-head grass |
| 14, 15 | Buttercups, daisies and yarrow |

Library blocks (a map file may replace any of them):

| Key | Meaning |
| --- | --- |
| `meadow` | Plant tint, density and height by ground moisture. |
| `flowers` | `coverage` of the ground in clusters of `cluster_size`, `chance` that grass there is a flower; the species follows a coarser noise, so clusters are single-coloured. Families opt in with `flowers: true`. |
| `verges` | Within `distance` of buildings and walls or of the grass edge (roads, rock, water), `tall_chance` of uncut grass. |
| `undergrowth` | `candidates` plants in a ring (`inner_radius`-`outer_radius`) around map decorations whose names contain one of `decorations` (trees): mostly ferns. |

A family's `tall_variants` are its uncut grass. With them, the map's `tall_grass_chance` is about the share of the
ground in uncut patches: the highest values of the density patch noise, a little more on lush ground; inside a patch
most grass is tall. Plants grow on slopes down to `minimum_normal_z` (0.62, just before the terrain turns to cliff
rock) and thin out over the last 0.1 of the normal.

Each plant is one card turned about its vertical axis to face the camera, within a fixed per-plant offset of up to
30 degrees, and mirrored for half the plants (`vs_terrain_decoration.sc`). Two crossed cards, used until 2026-10-16,
read as X shapes stamped on the ground from raised and flying views.

The short mats must match the colour of the grass ground under them, or they read as dashes. A map file's rule
`tint` overrides the family's tint, so a world-wide change means editing every map's rules. To measure, capture one
pose with `video.terrain_decorations` on and off, and compare the changed pixels. MM7's rules use
[0.93, 0.89, 0.69], which is within about 10 % of Harmondale's and Erathia's ground (the earlier
[0.72, 0.86, 0.62] was 25-45 % too dark in red). MM8 matched already. MM6's mats are 15-25 % greener than New
Sorpigal's ground; that is the approved look and is kept.

## Short grass clumps

Cells 0-1, the base layer, are drawn as clumps (the library's `clump` block, `TerrainDecorationClump`): `cards`
(5) cards in a star about the tuft's own yaw, each turned, sized and mirrored by its own seed, leaning outward by
`lean` (25 degrees) from a base a little off the centre, at `card_scale` (0.75) of the tuft's size. Clump
instances get their own rank quadtree and draw with their own mesh (8 fans; `u_terrainDecorationClump`); the other
plants stay single camera-facing cards. Past `distance` (1500) only the first card remains: the others thin out over
the last quarter and the first grows by half to keep the coverage. This is the usual construction of game grass
clumps: from the side, a raised angle and above they read as tufts, where a single card (two crossed cards before
that) read as a sliver, strip or X stamped on the ground.

Cost (RTX 3060 Ti, 1600 x 900, New Sorpigal's start): about 45-60 us of GPU time more than single cards; the
distance level of detail took it from about 95 us. It is near-field overdraw, so a lower `distance` barely changes it.

## Shading that sets the grass off the ground

The short grass matches the grass ground in colour, so its shading has to set it apart: the vertex shader darkens
every grass card at its roots and lightens it towards the tips (0.72 to 1.28), and a third of the tufts on average
get drier, yellower tips (`TerrainDecorationShade`; the foliage map averages the same factors, so the far colour
still matches). The library's `ground_shade` (0.2) darkens the ground under dense grass while the grass is drawn, so
the gaps between the tufts read as shade. The field's mean brightness stays within about 5 % of the unshaded one.

## Seen from above

Grass cards cannot carry a meadow seen from flying height: a short mat seen from above is a sliver, and thousands of
them hatch the ground. Three parts take over as the camera rises (all from 2026-10-16):

- **Short grass fades out.** The library's `overhead_fade` lists the atlas cells that fade (`layers: [0, 1]`, the
  short grass) between `start` and `end` (600 and 1400; 260 and 650 before the clumps) of the camera's height above
  the ground under it, so walking on slopes never fades plants downhill. The vertex shader thins them like distance
  thinning (`u_terrainDecorationLod.yz`, set by `TerrainDecorationRenderer::setCameraAltitude`). The clumps read from
  above too; the fade saves their cost when flying high, and the ground under them has their colour.
- **The ground takes the plants' colour.** The foliage map is 1024 x 1024 (64 units per texel, RGBA8 with mips,
  `encodeTerrainFoliageMap`). Over the same camera heights the terrain blends towards its colour by
  `1 - exp(-2 x depth)` times `overhead_fade.ground` (0.8), so uncut patches, flower clusters and dense grass read as
  areas and the open ground is mottled. Far away the existing far-colour blend still applies (GRASS_LOD.md).
- **Banks keep their texture.** Ground layers on slopes too gentle for the cliff layer (geometric normal z 0.92 down to
  0.72) blend to the two vertical projections, so grass banks no longer show streaks down the slope
  (`sampleTerrainLayer` in `outdoor_terrain_materials.sh`; only bank pixels pay for the four extra samples per layer).

## Low bushes

Four shrub models (`engine/models/meadow_bush01-04.glb`, built in
[`decorations/meadow_bushes/`](../decorations/meadow_bushes/README.md)) fill the layer between the grass and the trees.
The library's `bushes` block places them with the grass at load (`placeBushes` in `TerrainDecorationData.cpp`):

- groups of one to `group_max` at tree lines: `edge_chance` per undergrowth decoration (trees), `edge_radius` away;
- on a jittered grid of `spacing`: along buildings and walls (`verge_chance` within `verge_distance`), in lush hollows
  (`lush_chance` below `lush_below`) and rarely on open grass (`meadow_chance`);
- only where grass grows all around `radius`, clear of buildings and decorations by `clearance`, on slopes with a
  normal z of at least `minimum_normal_z`, `radius x 1.6` apart, at most `max_count`.

`TerrainBushSet` draws them as static model groups with the decoration models' baked light probes. They are scenery:
no collision, picking, events, sun shadows or water reflections. They dissolve out over `fade_distance` (5000-6500)
and follow the grass setting. Harmondale gets 315.

## Open-air BLVs (MM9's regions)

The remade MM9 regions are BLVs open to the sky; their terrain faces grow this meadow with New Sorpigal's settings
(2026-11-06): the same families, density, tall patches, flowers, verges, undergrowth, clumps, bushes, LOD, meadow
field and far colour, through `scatterTerrainDecorationsOnSurface` and a per-region file whose only change is the
short grass's tint, matched to the region's grass ground as above. Rock, snow, sand and dirt grow none. See
[devdocs/INDOOR_OPEN_SKY.md](../../devdocs/INDOOR_OPEN_SKY.md) "Terrain".

## Cost

New Sorpigal: 116,185 instances (7.4 MB) against 65,554 before; the grass costs about 40 us of GPU time at the default
pose (RTX 3060 Ti, 1600 x 900), the same share of the frame as the previous tufts. Unit tests:
`tests/OutdoorMeadowTests.cpp`.

## Next

[Meadow: follow-up work and tuning](MEADOW_IMPROVEMENTS.md): low 3D bushes (the mid-height layer the aerial views
still lack), a tuning table of every knob, and the known look, gameplay, engine and platform improvements.
