# MM6–MM8 decoration rollout proposal

Inspected on 2026-09-13. All **42 inventoried outdoor maps** have proposed settings: 15 MM6, 13 MM7,
14 MM8. All **489 installed accepted terrain PNGs** were checked against their export manifests.
MM8 uses the effective scene inventory, including Shadowspire's grey-dirt override and the accepted v13 roads.

The recommendation is to reuse the existing grass and stone implementation for most materials, add a small
amount of new plant artwork, and leave genuinely barren or special environments mostly clear. This is a
staged design and content audit. No runtime configurations, artwork, settings or renderer code were changed.
Only New Sorpigal is currently enabled by installed decoration content.

- [Every map and its proposed settings](MAPS.md)
- [Editable map choices and rationale](map_design.yml)
- [Decoration families and dimensions](families.yml)
- [Expanded machine-readable catalogue](catalogue.yml)
- [Every installed texture, material family, hash and map usage](tiles.json)
- Master contact sheets: [MM6](mm6_materials.png), [MM7](mm7_materials.png), [MM8](mm8_materials.png),
  [swamp variants and MM8 red-dirt/sand](special_materials.png)

## What the actual tiles suggest

The contact sheets were visually inspected along with the accepted four-variant grass atlas. This is a
material/art-direction review, not an in-game review of the proposed placements.

| Material | Proposed cover | Why |
| --- | --- | --- |
| Grass | Existing broad/fine/wispy/dry mix, weighted by map | Existing art already supplies four usable silhouettes. MM7/MM8 are more olive than MM6; calibrate palette in native lighting. |
| Sand | Very occasional short dry tufts | MM6 and MM8 have visible dunes. Dense vegetation would hide their form; MM7 sand is flatter ochre. |
| Snow | Mostly bare, with rare cool-gray exposed stones near margins | White grass would read as misplaced plants. No new snow artwork is needed for the first pass. |
| Swamp | Low sedges/reeds rooted on solid green/brown areas | The blue channels are baked into opaque artwork, including the base tiles and MM7 variants. Alpha alone cannot protect them. |
| Tropical | Low broadleaf clumps mixed with existing grass | MM6's yellow-green segmented ground calls for broader leaves. Dagger Wound uses ordinary MM8 grass textures but can select a tropical mix by map. |
| Cracked/waste/dead ground | Rare broken dead stalks | Keep large cracks and the barren tonal weight visible. |
| Dirt/rock/volcanic ground | Sparse existing stone mesh with local color and scale | Texture detail already does much of the work; no need for AI-generated pebble sprites. |
| Water/lava/tar/roads | No new scattered cover | Preserve readability and the accepted road/shore appearance. |

MM8's `plains` material in Ironsand is orange cracked ground, not green meadow. Its `plains_sand` is orange
dunes. MM8 `rdtyl` is a dependency-only master absent from the installed pack; the actually used `rdnw`
red-dirt transition was inspected instead. No extra terrain tile needs installation for that dependency.

## Proposed densities and map controls

The map table gives explicit material/family density multipliers. For example, New Sorpigal retains
50 grass candidates per eligible cell. Erathia uses 0.25 of that baseline (12.5 before exclusions),
while Emerald Island uses 0.9 (45) over a much smaller grassy area. These values are intended to retain
open ground and avoid multiplying instance counts across large grass maps.

Use a 4096-unit foliage range initially, 0.88 minimum normal Z, 0.8 density variation, 768-unit patch size,
and modest occasional taller clumps. Keep New Sorpigal's exact accepted settings and its 6144-unit range.
These distances are proposed starting values, not measured performance limits. The existing shorter stone
range stays in effect. Use map-local density masks for towns, courtyards, beaches and important sightlines;
building/entity checks alone do not identify every open plaza or scripted staging area.

The material counts in MAPS.md count an entire transition cell under its named foreground family. They
are not fractional ground coverage or predicted instance totals. During export, a transition may need two
rules, using the foreground mask and its complement for exposed dirt. Do not scatter over the whole
transition based on these counts. Do not infer world art palettes from material names alone.

Shoals, Plane of Water, Plane of Air and Tutorial are deliberately disabled in the proposal. Shoals needs
an aquatic art/placement pass; the elemental and tutorial geometry needs review before scatter. Plane
of Fire and Plane Between Planes have conservative mineral-only proposals that also require geometry checks.
Indoor and geometry-only areas outside the 42-map terrain inventory are outside this rollout.

## Small implementation extension

The current loader reads one world-local `<map>.yml`, one grass atlas with map-wide variant weights,
and grass/stone rules. Density, dimensions, tint, slope limits, material masks and map density masks exist.

1. Add world-local reusable family definitions and let each material rule choose a family/variant subset.
   Compile the selected families into the existing texture array and store the chosen layer in the existing
   instance field. Keep one authoritative runtime configuration path; migrate New Sorpigal explicitly while
   preserving its seed, weights and placements. Do not duplicate family definitions into every map file.
2. Add an explicit full-footprint clearance choice for reeds/broadleaf plants. Existing short grass checks
   roots, while only stones and selected tall clumps use stricter clearance. New marsh plants must not depend
   on the random tall-clump branch to avoid water channels. Wind strength can be family-specific using the
   current instance wind field; the existing billboard mesh is sufficient for the proposed low plants.
3. Reuse accepted transition coverage fields and masks, choosing their actual final revisions. Author an
   additional dry-root mask for each swamp base/variant and combine it with transition coverage. Do not use
   shadow/bevel darkness as a placement mask, or inverted land coverage as permission to plant in water.
4. Export small per-map YAML configurations and family assets under each world's `terrain_decorations/`.
   No gameplay actors, collision objects, new simulation or separate world renderer is needed.

An artist-facing biome preset may fill defaults, but each map's material choices remain explicit. Tatalia
has snow and swamp; Ironfist has meadow and swamp; a single map-wide plant family cannot express these.

## Artwork recommendation

Start with **six new source sprites**, two silhouettes each for:

- Low marsh reed/sedge clumps.
- Low tropical broadleaf clumps.
- Broken dead stalks.

Reuse the accepted dry/wispy grass for sand and all existing stone geometry. New snow, volcanic, desert
rock or large plant assets are unnecessary for the first pass. Aquatic vegetation is a separate deferred
task, not a terrestrial family recolored blue.

When generation starts, follow the imagegen skill and the direct sprite transparency/placement workflow.
Supply the accepted terrain master and grass atlas as palette/style references. Generate family artwork
once, retain prompts and raw outputs, then derive palette variants deterministically. Keep real alpha,
grounded silhouettes, restrained contrast and no painted ground patch. Inspect light/dark alpha edges and
premultiplied resizing. Use the existing 256×192 per-variant runtime cell as a starting budget; allocate larger
cells only if the actual small in-game silhouette demonstrates a need. Authoring sheet resolution is separate.

## Verification before installation

Keep progress per map as proposed, prepared, visually reviewed and installed; accepted source art is a
separate state. The current catalogue is entirely proposed except for preserved New Sorpigal.

- Loader/export checks: each rule references a tile actually used by that map, a valid family and correctly
  oriented mask; every installed file matches its selected source. Retain all 42 explicit decisions, including
  deliberate disabled maps. Proposals here have inventory/hash checks, not runtime-loader validation.
- Unit checks for new logic: per-rule variant selection, deterministic placements, strict marsh footprint
  masks and unchanged New Sorpigal output. Preserve the no-allocation behavior when disabled/unconfigured.
- Visual checks: native camera pairs with decorations off/on; inspect grass/dirt, every road shape, shores,
  swamp channel interiors, snow margins and buildings. Walk through transitions and observe wind and fading.
- Representative first maps: New Sorpigal (regression), Bootleg Bay (tropical), Mire of the Damned (swamp),
  Frozen Highlands (snow), Dragonsand (sand), Sweet Water (dead); Harmondale, Tatalia and Shoals; Dagger Wound,
  Ironsand and Shadowspire. Then inspect every remaining enabled map, including dense wilderness and towns.
- Measure real-GPU dense views and Android release behavior, including visible/total instances, draw calls,
  frame time and memory. Tune actual map density/range from these results, not candidate counts alone.

Rebuild this audit without changing active game assets:

```sh
python3 level_generation/terrain/decoration_rollout/build_catalogue.py
```

The script checks current ODM/table hashes and MM8 effective scene hashes, installed texture hashes/dimensions,
map-set coverage and referenced families, and regenerates catalogue.yml, tiles.json and MAPS.md. Original
MM6/MM7 scene environment lookups were inspected against their ODM values during this review; they agree.
Re-audit effective scene overrides before a future runtime export if those scenes or overlays change.
