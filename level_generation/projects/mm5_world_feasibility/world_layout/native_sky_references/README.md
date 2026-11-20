# Native sky references: MM8 Plane of Air and MM7 Celeste

These are the user's selected visual/structural references for the MM5 Skyroads and Air plane. The material sheet
contains actual local textures. `sources.json` records source map/texture hashes and measured texture usage.

## MM8 Plane of Air

Source: `assets_dev/worlds/mm8/maps/elema.odm` and `elema.scene.yml`.

- The scene explicitly sets **`no_terrain: true`** and **`always_light: true`** (`map_extra_bits_raw: 40`).
- The ODM contains **39 BModels / 2,301 model faces**. Its ordinary tile array is almost entirely `rktyl`, but this is
  not the visible air-world design: the normal terrain is disabled.
- Model textures include `CDB` masonry, `GWSPHLWL`, `GWSPHLFL`, `GWSPEDG`, and two `PLANSKY1` faces. The texture names
  are material keys, not enough on their own to determine collision or visibility semantics.
- Those two `PLANSKY1` model faces are small vertical 256 × 256 surfaces, not a pair of world-sized sky planes;
  `sky_faces.json` records their bounds. Do not infer the full environment rendering from their count.
- Use exposed built platforms and architecture with sky beyond/below them as the design reference. Copying its hidden
  rock tile array would miss the effect the user asked for.

## MM7 Celeste

Source: `assets_dev/worlds/mm7/maps/7d25.blv`, identified as Celeste in the active map registry.

- Celeste is a **BLV**, despite its open-air cloud-city presentation.
- Its **3,973 faces** include 578 with `SKY19`, 213 with `7plansky1`, and 505 with `CWB`, along with residential walls,
  floors, roof panels and water. These are counts, not surface-area proportions.
- `CWB` is masonry, not a cloud bitmap. `SKY19` provides cloud imagery; `7plansky1` is blue sky with clouds.
- The sky/cloud textures occur on faces at different orientations and heights. A floating city is achieved with
  geometry and surrounding sky presentation, not solely by choosing a blue terrain texture.

## What this means for the MM5 plan

Use blue sky/cloud layers visible through gaps and below exposed edges, believable platform thickness, and compact
stone architecture. Olympus should borrow Celeste's cloud-city vocabulary; the broad Skyroad routes can use MM8 Air's
platform/stone/sky treatment. Keep perspective strictly top-down for the minimap concepts; validate the floating feeling
later from player-height views as well.

OpenYAMM already handles `noTerrain` in `game/outdoor/OutdoorRenderer.cpp` and excludes that terrain from the standard
terrain navigation path in `OutdoorPathfindingBuilder.cpp`. This supplies a relevant existing implementation path,
but it is not proof that a new MM5 scene's collision, actors, gaps, falling, and travel are correct. The proposed sky
fixture remains required before production. Do not change MM8/Celeste assets or global behavior for this study.

The [material reference sheet](material_reference.png) is used as a visual input to the revised concepts. It is evidence
of available art; it does not copy complete game geometry into a new MM5 map.
