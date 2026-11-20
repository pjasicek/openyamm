# Revised sky and elemental minimap concepts

The earlier sky/plane sheets were stitched source-grid schematics. They did not meet the requested visual target:
**top-down terrain concepts comparable to the surface minimap study**. The atlas now shows textured concepts first;
the source schematics remain available as a separate evidence view.

Open the [updated all-outdoor atlas](other_outdoors.html), [Skyroad minimap](sky_map.png) or
[elemental minimaps](elemental_planes.png).

## Native visual references selected by the user

**MM8 Plane of Air and MM7 Celeste** establish the floating-world visual direction: exposed stone platforms and paths,
sky/clouds visible beyond and below their edges, and compact architecture. The
[native material/geometry audit](native_sky_references/README.md) records the inspected maps and texture names.

MM8 Air's scene explicitly disables normal terrain. Celeste uses BLV geometry with sky-textured surfaces. These are
more useful references than painting an ordinary terrain plane blue. In the minimap, platform edges, cloud depth and
separated silhouettes communicate altitude; the later native scene must also work when looking up, down and across
the landscape from player height.

## Skyroad concept

- Preserve the source perimeter skyway, its branch pattern, isolated cloud/platform areas and large open gaps.
- Use textured stone paths and built platforms with thickness and edge shading, above a blue/cloud atmosphere.
- Keep Olympus, the tower/castle upper entries, the isolated pyramid summit, the eastern sky lake and the four corner
  elemental gateways in their source-relative parts of the world.
- Use Celeste-inspired compact architecture for Olympus and the native Air material vocabulary for paths/platforms.
- Remove diagnostic dots from the rendered concept. A source event/transport trail is not a physical bridge, road
  or line of stepping stones. The exact directed transitions stay in the source manifest.

The six-region division is an editable atlas overlay, not a grid baked into the artwork. The generated architectural
footprints and cloud contours are proposed. This is a visual review of coarse topology, not a pixel-exact conversion
or a new collision/navigation proof. Original coordinate aliases remain authoritative for subsequent layout work.

## Elemental concepts

The original planes have nearly uniform surface types. Their new landforms therefore require explicit authorship:

| Plane | Proposed minimap treatment | Original anchor roles retained in the brief |
| --- | --- | --- |
| Fire | Braided lava basins, charred basalt shelves, cooled-flow ridges and small elemental sites | Arrival, Fire Sleeper, test, instruction statue, exit |
| Air | Cloud-supported stone shelves/platforms with visible air gaps and native Air/Celeste material direction | Arrival, Air Sleeper, test, instruction statue, exit |
| Earth | Continuous rocky ground, uneven ridges, gullies, mineral outcrops and sparse built landmarks | Arrival, Earth Sleeper, test, instruction statue, exit |
| Water | Deep water, submerged shelves, reef/mineral ridges and small exposed landmark platforms | Arrival, Water Sleeper, test, instruction statue, exit |

Sleeper and instruction sites exist in the supplied MM5 maps; this does not add the excluded WoX bonus-map finale to
the current scope. The prompts preserve their coarse relative arrangement. Exact anchor placement must be authored
and checked in the future map plan; a rendered shrine is not an event binding.

Basalt shelves and emergent water platforms are new design proposals. They must not silently remove the original
hazards or traversal requirements. Likewise, Air's gaps must not become an accidental sequence of mandatory jumps or
unplanned Fly gates. No runtime movement/balance decision has been made by these pictures.

## Artifacts and generation method

The raster concepts were made with the **built-in image-generation tool**, using the source diagrams, the previous
surface study, the user's MM6 minimap reference and the actual native Air/Celeste material sheet. No API/CLI fallback
was used. The images are authored concept illustrations, not engine screenshots or literal composites of native tiles.

- Final [Skyroad artwork](concepts/sky_minimap_v2.png); the initial v1 is retained for comparison.
- [Four-plane artwork](concepts/elemental_minimaps_v1.png): Fire / Air on the upper row, Earth / Water below.
- [Sky prompt](SKY_MINIMAP_PROMPT.txt) and [marker-cleanup refinement](SKY_MINIMAP_REFINEMENT.txt).
- [Elemental prompt](PLANE_MINIMAPS_PROMPT.txt).

`concept_sheets.py` adds editable atlas framing and creates SVG viewports with PNG exports for individual region/panel
previews. It does not repaint the generated raster art. `build_other_outdoors.py` rebuilds the atlas and source schematics; it requires
the reviewed concept images and does not silently substitute source diagrams when the images are missing.

Rebuild the atlas with:

```sh
python3 level_generation/projects/mm5_world_feasibility/world_layout/build_other_outdoors.py
```

The manifest still covers all 52 original outdoor logical maps exactly once in 16 proposed groups. No native ODM,
BLV, runtime material registry, sky renderer or gameplay behavior was changed by this visual revision.
