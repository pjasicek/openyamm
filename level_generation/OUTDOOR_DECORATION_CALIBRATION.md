# Outdoor decoration vocabulary, placement and deliberate open space

Use this when choosing scenery for a new outdoor region. It extends
[population and composition](POPULATION_AND_COMPOSITION.md),
[wilderness calibration](WILDERNESS_CALIBRATION.md) and
[landscape detail](LANDSCAPE_DETAIL_CALIBRATION.md) with **all 42 mounted MM6–MM8 ODMs**:
15 MM6, 13 MM7 and 14 MM8, including special environments and the tutorial.

The [interactive catalogue](catalogues/outdoor_decorations/index.html) contains every resolved decoration type,
its native first-frame artwork, maps/counts, source entity coordinates, event fields, collision dimensions,
light data, terrain under the anchor and proximity to BModel envelopes, road cells and water cells.
The [map summary](catalogues/outdoor_decorations/map_summary.csv) and
[decoration-by-map index](catalogues/outdoor_decorations/decoration_usage.csv) are machine-readable.
Read the [measurement definitions and limits](catalogues/outdoor_decorations/README.md) before comparing rates.

## Evidence and interpretation

The inventory resolves **18,158 entity records**, **338 descriptor identities** and **17,929 initially visible
sprite instances**. Hidden/marker records and emitter-only effects are retained separately. This is the complete
placed-decoration record inventory, not an inventory of every visible object: buildings, modeled fountains/wells,
bridges, chest meshes, terrain detail, monsters and loose items are different content layers.

Inputs are this checkout's imported ODM/scene files and merged decoration/frame tables. Placement is checked against
the corresponding local MMerge reference ODMs; this is not independent proof of unchanged retail event behavior.
Current map scripts can replace/hide decorations after load. The per-map JSON records visual-change calls as
references; the survey does not execute those scripts or seasonal/quest states.

**Observed:** counts, artwork, positions, native event fields, terrain material, sampled grade and spatial clustering.
**Inferred design reading:** a group frames a route, supplies a camp, expresses a local culture or makes a space feel
tended/abandoned. These are interpretations of the shipped arrangement, not quotations from historical design notes.
**New-map prescription:** the recipes and review rules below. They are not recovered original authoring algorithms.

## First choose the local place, then the palette

“Grass”, “sand” or “necro” establishes a broad material language. It does not determine every decoration on the map.
Choose a **local subregion and use**: town garden, rough rear plot, orchard, open pasture, woodland edge, wet bank,
snow shelf, cemetery approach, exposed dune or defended camp. Match that context to a reference patch, rather than
applying the entire reference map's palette uniformly.

Two particularly useful measured examples:

- **Tatalia is not a uniform swamp.** Its 248 `tree33`/`tree36` snow-tree sprites have median anchor Z=3,072;
  245 stand over `7snow`, with three over snow transitions. Its 139 `tree60`/`7tree63`/`tree65` sprites have median
  Z=16 and occupy dirt/swamp terrain. Preserve the high-country/low-country contrast when borrowing the palette.
  [Tatalia records](catalogues/outdoor_decorations/maps/mm7_7out13.json).
- **Frozen Highlands is not all snow trees.** It contains 235 `snotre01`/`snotre03` sprites, while its 234
  `6tree17`/`6tree04`/`6tree18` sprites mostly stand over dirt: 222 of those 234 anchors use `6dirttyl`.
  The artwork supports distinct ground/vegetation patches inside one named snowy region.
  [Frozen Highlands records](catalogues/outdoor_decorations/maps/mm6_outc1.json).

Descriptor hints are insufficient: `tree41`/`tree42` say “tree” but visibly show bare branches;
`tree33`/`tree36` show snowy trees; some MM7 `plant*` entries are **plants in containers**, including withered versions.
The catalogue records explicit visual tags for these cases. Do not scatter potted plants into wilderness because
their descriptor says “plant”. Fitted thumbnails also hide physical size: check frame scale and collision dimensions.

Likewise, the cactus-labelled `cac*`/`bush*` families include palm-like and branching canopy silhouettes. The
catalogue's `dry_plants` category is an indexing convenience, not a botanical classification. Inspect the painted
ground contact as well: `searka01`/`searkb01` rocks include wave/foam bases, which can look misplaced on dry ground.

## Practical palettes above the terrain material

The counts here are whole-map, initially visible sprite counts unless a subset is explicitly named.
Names are the canonical keys in this checkout; use the catalogue's world/descriptor resolution when importing.

| Local feel / reference | Observed vocabulary | Use in a new region |
| --- | --- | --- |
| Temperate settlement — Ravenshore, Alvar, Erathia | Ravenshore: 269 flowers/low plants; 231 are within 1,024 units of a BModel envelope. Alvar: 278 flower sprites. Erathia: 268 flowers. | Bounded beds, verges, court edges and selected rear gardens. Pair low colour/detail with occasional canopy silhouettes. Reserve usable square/door space; do not add the same garden at every house. |
| Temperate countryside — Ravenshore | 268 tree sprites, three stumps and 205 ordinary rocks; only 32 of the trees are within 1,024 units of BModels. | Separate open meadow, wooded shoulder, rocky edge and settlement planting. A few nearby accents can connect town to countryside without turning the whole region into forest. |
| Woodland — Murmurwoods, Tularean Forest | Murmurwoods: 1,480 trees, 141 stumps and 207 rocks. Tularean Forest: 102 `bush03` shrubs alongside its trees, flowers and town/container plants. | Compose groves, varied crowns, understory pockets, stumps and occasional rock groups. Leave readable clearings and travel corridors; forest character need not come from flowers. |
| Open grass/dirt forts — Garrote Gorge | 263 visible sprites total: 131 trees, 53 flowers/low plants, 77 rocks, one working prop and one fire. | Use architecture, terrain shelves and opposing camp identities as major interest. Add selected verges and hillside groups; preserve military yards and long approaches. Do not import Murmurwoods density. |
| Dry grass/dirt — Ravage Roaming | 72 `tree62c` and 63 `tree63b` trees have warm autumnal crowns; 31 `tree28` bare trees; 85 rocks and five campfires. | Retain the warm crown/earth palette, mixed live/bare silhouettes and exposed rocky ground. A dirt region does not automatically need cacti or an entirely dead forest. |
| Desert — Dragonsand, Bracada, Ironsand | Dragonsand: 290 dry-plant-family sprites, 86 fan-palm-like `6tree21` trees and 69 rocks. Bracada: 204 dry-plant-family sprites and 53 rocks; no tree-category records, but some plants have branching canopies. Ironsand: 126 dry plants, 225 rocks and 137 remains. | Pick the intended desert language first. Use species/rock groups and deliberate bare expanses; put bones/ruin accents where the local story warrants them. Palms in one reference do not mandate an oasis or palms in every desert. |
| Necropolis / cursed land — Shadowspire, Deyja | Shadowspire: 225 rune posts (`dec13`–`dec17`), 95 skeletons, 84 bare `tree28`, 159 rocks and 28 low plants. Deyja: 172 dry-plant-family sprites, 98 bare `tree41`/`tree42` and nine rocks. | These are distinct palettes. Build repeated ritual structures and remains into Shadowspire-like settings, or use Deyja's exposed dry/bare vegetation language. Avoid mixing every spooky prop into every patch. |
| Wetland / low coast — Tatalia, Mire of the Damned | Tatalia's lowland trees contrast with its snowy uplands. Mire uses swamp-tree families, ordinary trees, rocks and food trees. | Place credible wet/dry pockets and tree groups on shelves/margins. Do not carpet all water with aquatic sprites; lily pads and submerged plants are separate, selectively used assets. |
| Tropical settlement/coast — Dagger Wound, Regna, Bootleg Bay | Dagger Wound: 367 palms, 281 low plants/flowers, 43 corn sprites, four lily pads and 68 emitter-only smoke records. Regna: 339 palm/tree sprites and 61 low plants/flowers. | Compose inhabited islands with cultivated plots, dense tropical pockets, exposed shore and docking/approach space. Crops communicate occupation; smoke contributes activity beyond the static sprite layer. |
| Snow / high country — Frozen Highlands, Nighon | Nighon: 129 snow-tree sprites and 102 rocks; large areas lie far from decoration anchors. Frozen Highlands mixes snow and dirt-side vegetation. | Use snowy crowns and rock groups on plausible shelves, with open snow/rock faces and a few deliberate landmarks. Preserve local material changes; snow is not a reason to scatter the same tree over every slope. |
| Air / water / fire planes | Plane of Air: 428 instances of **one** `dec57` path-marker descriptor. Plane of Water: 100 coral and 48 seaweed sprites. Plane of Fire: zero visible decoration sprites. | The dominant layer can be route legibility, underwater structure or terrain/architecture. Do not apply a terrestrial foliage target to a plane. Zero sprites does not establish a visually empty level. |

Read exact map palettes and coordinate plots before selecting variants. The categories are analytical groups, not
botanical taxonomy, biome eligibility flags or declarations that the original designers followed strict ecology.

## Use multiple kinds of interest, with a purpose for each group

| Layer | Useful function | Placement test |
| --- | --- | --- |
| Large silhouettes | Grove edge, isolated tree, boulder group, skyline framing or screening a reveal | Does it clarify the approach or create a recognisable place? Inspect crowns, not only trunk origins. |
| Close ground detail | Low plants, small rocks, stumps and sparse compatible terrain-detail tiles | Does it give the walked-through foreground texture without producing uniform noise? Use local groups and changes in coverage. |
| Human use | Barrels, refuse, fire/cauldron, crops, wood and container plants | What activity explains this object here? Working/rear plots differ from civic forecourts, gardens and wilderness. |
| Narrative / cultural identity | Rune posts, remains, statues, unusual stones and ruined structures | Is there a readable setting or repeated local motif? Preserve the visual distinction between an ordinary verge and a significant site. |
| Navigation / interaction | Path markers, buoys, pedestals, food trees, wells/fountains and chest settings | Can the player recognise and reach it? Does it help a junction, approach, return route or optional excursion? |
| Activity / atmosphere | Smoke, fire, sound emitters and lighting | Review in the game when needed. Static sprite counts and first-frame previews do not represent these effects fully. |

A **small composition** is usually more useful than unrelated additions: a tree at a court corner with a low bed;
a rock shoulder with a few fitting plants; a cooking fire with a usable clearing and supplies; a rune-post group with
bare branches and a clear approach. These are proposed composition patterns, not mandatory three-object recipes.
Use a few related variants within a group and different densities between groups. Avoid decorative rings around
every tree, identical borders around every plot, regular lone trees at fixed intervals or constant roadside flowers.

There is also a legitimate broad-scatter vocabulary. Dragonsand's cactus/palm/rock population has at most four
central-land sprites in one aligned 2,048-unit square, while Alvar reaches 47. The former is not simply an unfinished
version of the latter. Combine sparse background distribution with a few designed settings when that fits the biome.

## Density: compare coverage and local concentrations, not just totals

The central analytical window is ±24,576 on both axes: 96×96 cells at 512 units. Nonwater cells include shores and
steep ground. This window matches the earlier landscape measurement, **not** actual map travel bounds or confirmed
walkability. Density counts only initially visible anchors in those nonwater cells. A 4,096-square area is 8×8 cells.

| Reference | All-map visible sprites | Central nonwater sprites / 4,096-square area | Central nonwater area farther than 2,048 from any visible anchor |
| --- | ---: | ---: | ---: |
| Garrote Gorge | 263 | 1.55 | 60.8% |
| Ravage Roaming | 266 | 1.64 | 30.3% |
| Bracada Desert | 260 | 1.77 | 28.6% |
| Dragonsand | 446 | 2.97 | 7.2% |
| Shadowspire | 604 | 4.18 | 15.3% |
| Alvar | 1,038 | 6.68 | 27.9% |
| Ravenshore | 807 | 7.07 | 26.4% |
| Murmurwoods | 1,847 | 10.08 | 10.6% |
| Dagger Wound | 731 | 11.83 | 19.4% |

These are reference observations, **not target bands**. Coastlines alter the denominator; dense town planting can
raise average density while leaving substantial open countryside. Small flowers and enormous crowns each count as
one anchor. Terrain and BModels can make a “far from sprites” area visually rich. The JSON also reports the same
distance measure on gentle terrain (maximum triangle grade ≤0.5) to expose mountain-area effects; this is still not
a collision/traversability or screen-coverage measure. Underwater/air maps and the tutorial are marked separately.

For a generated map, compare the intended **district** to a comparable reference district. Keep tree, low-plant,
rock, special-prop and effects counts distinct. Review local density maps with a common physical scale; do not stretch
each map to appear equally full. The existing [land-normalized district heatmaps](LANDSCAPE_DETAIL_CALIBRATION.md#compare-local-coverage-inside-and-outside-the-settlement)
remain the more specific town/town-edge/wilderness comparison.

## Deliberate empty space versus missed composition

For every sizeable open patch on the sketch, write a short purpose: pasture, dune, exposed snow, water view,
combat room, gateway approach, town square, clearing or a view toward a landmark. Then inspect it from the likely
walking route. It may need **no extra objects** if terrain, architecture, a distant silhouette or the view supplies
the intended interest. Calm/no encounter does not mean visually featureless.

If a walked-through area lacks a role and visual structure, change the composition locally:

1. Identify the missing layer: silhouette, ground detail, inhabited-use clue, navigation cue or focal setting.
2. Choose a suitable group from one or two reference patches and record their map/entity indices.
3. Reserve its extent, standing/approach space and clear sightline; keep the main movement corridor open.
4. Place the principal forms first, then selected smaller accents. Use seeded variation inside authored extents.
5. Check the **accepted placements in that group**, not whether the entire map reached a total. A rejected/empty
   garden should trigger a local layout decision, not reduced clearance everywhere or more trees in a remote wood.

The 2,048-unit “far” measure is an inspection aid, not a trigger to fill every four-cell gap. Review a few deliberate
routes and transitions: arrival → first destination, town → country, country → special site, return approach.
Avoid making every stop a quest/reward/encounter. A framed view, distinctive tree or quiet rock shelf can provide pace.

## Props can carry behavior: retain their meaning

- MM8 `dec03` is a barrel despite the unhelpful hint; the shared
  [interactive-decoration rules](../game/gameplay/InteractiveDecorationRules.cpp) recognise it.
- MM8 `dec40`–`dec43` are stat-challenge appearances despite the “beacon fire” hints. `dec44`–`dec55` are buff
  pedestal appearances. Follow [the existing effect/state calibration](LANDSCAPE_DETAIL_CALIBRATION.md#buff-pedestals-and-stat-challenges-are-optional-landmarks),
  not the hint text. Repeated native challenges may share completion state.
- MM6 food trees and MM7 fruit trees are activity/interaction cues, not simply additional green crowns. The original
  [Tularean script](../reference/mmext-scripts/Decompiled_Scripts/mm7orig/txt/OUT04.txt) changes harvested fruit-tree
  appearances; the [imported map script](../assets_dev/worlds/mm7/events/maps/7out04.lua) exposes the corresponding
  event references. Seasonal/quest changes need their own context review.
- An event field of zero is **not proof of inertness**. Native decoration rules, descriptor flags and lifecycle code
  can provide behavior. A flag/light/emitter also has runtime implications beyond its thumbnail.

For custom worlds, choose visual identity separately from event/state ownership. Reserve interactions/placeholders
as required by the project brief; do not accidentally import a native reward, shared completion bit or encounter
simply by selecting a familiar decoration. Keep authored overrides out of generated Lua exports.

## What to record and review in future generation

Add to the brief: subregion material/feel, reference map and patch, a restricted native palette, each group's role,
extent, large/low/special layers, deliberate open patches, route views, expected versus accepted counts and exclusion
reasons. Use the existing `decoration_groups`, `soil_patches`, `ground_detail_variants` and `scenery_heatmaps` fields;
the new reference/open-space fields make the choices explicit.

Ground sprites on the final quantized native triangles or the intended BModel surface. Reserve the full collision
and visual envelope around doors, roads, bridges, travel arrivals, water crossings, interactions and combat space.
Check root/rock contact from low views and crowns from approach directions. Do not hide construction defects with
dense foliage or globally disable collision to make scatter pass.

Reuse this survey; do not regenerate all 42 maps during routine level work. The normal completion gate remains a
small set of representative player-height views plus one static native/semantic readback. Recheck source evidence
when a chosen reference changes, or investigate a specific new behavior/defect. No exhaustive gameplay suite is
required for choosing existing decoration artwork and placing it in an already supported way.
