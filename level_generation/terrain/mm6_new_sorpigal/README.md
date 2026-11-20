# New Sorpigal terrain catalogue

Open **index.html** for the searchable, offline visual catalogue. All paths in JSON are relative to this catalogue unless explicitly identified as source paths in the repository.

49 unique native 128×128 terrain textures, 12 exact shoreline alpha masks and 14 additional water animation frames. Sources are copied unchanged as indexed BMP and also decoded to PNG. No generation has been run and no runtime assets have been changed.

| Group | Used tiles | Related materials |
|---|---:|---|
| Base tiles | 4 | grass, dirt, rock, water |
| Grass / dirt transitions | 12 | grass, dirt |
| Rock / dirt transitions | 12 | rock, dirt |
| Shore overlays / water openings | 12 | dirt, water |
| Roads on dirt | 9 | road, dirt |

## Files

- `original_bmp/`: byte-identical native tile sources, including palettes.
- `source_rgb/`: unmodified colours; shoreline keys remain cyan.
- `rgba/`: ready-to-reference tiles; shoreline keys converted to exact transparency.
- `alpha/shore_visible/`: white = visible shore; black = water opening.
- `alpha/water_opening/`: white = water opening; black = shore.
- `composited/`: water uses animation frame 0; shore alpha is composited over that frame.
- `contexts/`: one real 3×3 map neighbourhood per tile, target in the centre; no labels in image.
- `sheets/`: labelled family, context, water-frame, alpha and composition reference sheets.
- `map/`: flat source-art overview and family map (colours in catalogue.json).
- `water_animation/`: 14 existing 256px BMP/PNG frame pairs plus runtime-equivalent 128px copies.
- `imagegen_briefs/`: five material-master prompts, input references and transition instructions.
- `catalogue.json`, `tiles.csv`: grouping, descriptors, usage counts, source provenance and paths.
- `map_cells.csv`, `adjacency.json`: all rendered cells and observed east/south neighbour pairs.
- `checksums.json`: SHA-256 of every other catalogue file.

## Interpretation

The four bases are 6grastyl (grass), 6dirttyl (dirt), 6voltyl (rock) and 6wtrtyl (static water fallback). The rock/dirt family uses voldrt*, not a grass/rock blend. Roads also contain dirt and have no standalone native master tile here.

Edge/corner/X-corner classifications retain native filename suffixes. The suffix alone does not define which side is material A; the source image and real-map context are authoritative. No rotations or mirrors are introduced.

Only shoreline masks are exact material-separation data. Grass/dirt, rock/dirt and road tiles are opaque painted images: they do not carry a material alpha channel. Do not use colour-distance estimates as authoritative masks without review. Black rock and palette index 0 in opaque road/rock tiles must remain visible.

The map stores 128×128 tile entries; the renderer draws 127×127 cells. Counts distinguish these. Contexts and overview use rendered cells, north up. World coordinates in map_cells.csv describe the north-west tile corner. These are flat texture assemblies, not game screenshots.

The legacy BMP sources encode shoreline openings as cyan RGB (0,252,252), palette index 0. Exported shore alpha follows runtime key rules. 6wtrtyl is only the static fallback: water_mm6 supplies 14 existing 256px animated frames, each with 15 native ticks in the surface table. Runtime x1 composites use the engine's floor-based nearest resize to 128px. The catalogue does not equate native ticks to milliseconds.

## Next generation order

1. Review and restore shared grass, dirt, rock and road masters; establish a water style reference.
2. Derive/review opaque transition masks together, constraining neighbour edges and material phase.
3. Rebuild transitions from approved masters; retain exact shoreline coverage.
4. Review full families, actual map contexts and reduced-resolution versions before runtime use.

Generation prompts are drafts ready for later tool calls. They do not guarantee seamless output. Individual inputs are unlabelled; reference sheets include labels that must not appear in generated art.

Rebuild from the repository root: `python3 level_generation/terrain/build_new_sorpigal_catalogue.py`.

Original artwork remains MM6 game artwork; this catalogue does not grant a new asset licence.
