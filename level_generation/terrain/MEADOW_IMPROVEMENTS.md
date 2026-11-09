# Meadow: follow-up work and tuning

Open items after the first meadow pass ([Meadow](MEADOW.md), 2026-10-15). None of this is scheduled; the user chose
to play with the current version first. Ordered by expected value within each section.

## 1. Low 3D bushes

Done on 2026-10-16 ([Meadow](MEADOW.md#low-bushes)). Open:

- **Colour per world.** The bushes take no rule tint (`ModelStaticPlacement` has no albedo tint), so MM7's olive ground
  and MM8's jungle show the same mid green. A per-placement tint in the static model shader, or a second texture set
  per world, would match them.
- **Sun shadows and water reflections.** Left out to keep the cost down; adding the groups to
  `renderSunShadows`/`renderReflection` needs those calls to take more than one group list.
- **MM8 species.** MM8 uses the temperate shrubs too; its tropical maps would suit low palms and ferns
  (`mm7_deco_bush03` is a fern clump that fits as a fifth model there).
- **Contact darkening.** Bush footprints could be added to the foliage map so the ground darkens under them.

## 2. Tuning (data only)

All in `worlds/<world>/terrain_decorations/families_v2.yml` (library), the map files beside it, and
`worlds/<world>/terrain_materials/world.yml` (then `tools/terrain_materials.py weights` for every map).

| Knob | Now | Raise it to get | Lower it to get |
| --- | --- | --- | --- |
| `tall_grass_chance` (map) | 0.1 (New Sorpigal 0.12) | more and larger uncut patches | a tidier, mown look |
| `verges.distance` / `tall_chance` | 72 / 0.55 (MM7/MM8 108) | wider, fuller verges | cleaner road edges |
| `flowers.coverage` / `chance` | 0.3 / 0.35 | more and denser clusters | rarer accents |
| `flowers.cluster_size` | 700 (MM7/MM8 1050) | larger single-colour fields | small dots |
| `undergrowth.candidates` / radii | 10 / 90-260 | denser fern rings | barer trunks |
| `meadow.density` / `height` | 0.35 / 0.3 | stronger dry-crest vs lush-hollow contrast in the plants | uniform grass |
| terrain `meadow.dry` / `lush` | [1.2, 1.06, 0.64] / [0.78, 0.94, 0.82] | yellower crests, darker hollows | subtler ground |
| family `candidates` (meadow) | 60 | a closer mat (cost grows with it) | more visible ground |
| `minimum_normal_z` (map) | 0.62 | (lower) grass up to steeper slopes | barer hillsides |
| `overhead_fade` `start`/`end` | 260 / 650 | short grass kept to higher flying | earlier fade from above |
| `overhead_fade.ground` | 0.8 | stronger plant colour on the ground from above | plainer ground from above |
| `bushes` `edge_chance` / `lush_chance` / `verge_chance` | 0.45 / 0.3 / 0.3 | more bush groups there | fewer |
| `bushes.max_count` | 600 | (cap) | fewer bushes on large maps |

The per-family variant weights choose between the short mats (cells 0-1) and the older upright tufts (2-3); the
upright tufts read as single potted plants and are kept at 3 % each in meadow families.

## 3. Improvements

### Look

- **Per-world grass colour match.** The rule tints are now matched by hand (see [Meadow](MEADOW.md)): MM7 was
  corrected on 2026-10-16, and MM8 matched already. Maps whose ground differs from the sampled ones can still be off.
  Better: derive each grass instance's tint at load from the terrain's own grass layer colour at that point
  (layer mean colour x world tint x meadow tint), which removes the hand-set rule tints for grass entirely.
- **Tall grass art.** Cells 12-13 are fairly sparse and narrow; a denser uncut-grass sheet (more blades, fewer
  separate stems) would make patches read as masses instead of many stalks up close. The seed heads were darkened
  in processing (`TALL_GRASS_GAIN`); regenerate rather than push that further.
- **Sun-facing slopes.** The meadow field ignores aspect; south-facing slopes drying more would add variety on large
  hills.
- **World flower palettes.** One flower set serves all three worlds. MM7 (Antagarich) and MM8 (Jadame) could have
  their own species in the tropical and swamp families.
- **Wind.** Tall grass and flowers sway with the same strength as short grass; a stronger, slower sway for cells
  10-15 would sell the uncut patches.

### Gameplay and readability

- **Items and small monsters in tall grass.** Ground items and rats can hide in uncut patches. Options: fade grass
  cards within a small radius of ground items (pass item positions as a few uniforms, or a small dynamic mask), or
  keep tall variants out of known item spawn spots.
- **Walking through tall grass.** Cards that fill the screen when the party stands in a patch: shorten or fade tall
  instances within about 150 units of the camera (vertex shader, by distance), like grass bending around the player.
  This also bounds the worst-case overdraw.

### Engine limits

- **16 atlas cells.** `MaxTuftLayers` is bound by the cutout uniform array (64 vec4, 8 outline vertices per cell);
  the atlas is full. More plants need the outlines in a small texture (or per-instance data) instead of uniforms.
- **Undergrowth by name.** Trees are found by substrings of decoration names (`tree`, `snotre`, `stump`). A flag in
  the decoration bindings (`decorations.yml`) would be more robust.
- **Verges use building bounding boxes.** Large or L-shaped buildings get verges along their box, not their walls.
  Using the bmodel faces' footprint would follow walls exactly.

### Platforms

- **Android tier.** Planned with the clumps (2026-10-16): a grass quality setting where `low` draws the short grass as
  single cards (no `clump` layers) and `high` as clumps with fewer cards (3) and about 60 % density, chosen per
  device after measuring a release APK. Phone GPUs pay for alpha-tested overdraw, not triangles.
  No density scale exists yet. Add a setting that scales candidates (and drops tall and flower
  variants beyond the near distance) for the mobile profile, then measure a release APK.
- **Vulkan and GLES.** Not yet checked with the new atlas and shader changes.

## Checks to repeat after changes

- `./build/tests/openyamm_unit_tests --test-case='*eadow*,*errain*,*ildflower*,*erges*,Tall grass*'`
- A screenshot tour of New Sorpigal (ground, ground facing the hills, low and high flying poses) and one map per
  world (`outd3`, `7out01`, `out01`); see `debug.screenshot_tour_path` in AGENTS.md.
- Grass cost at the default pose, grass on and off, alternating runs.
