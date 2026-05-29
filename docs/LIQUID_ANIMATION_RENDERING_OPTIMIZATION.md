# Liquid Animation Rendering Optimization

## Context

OpenYAMM currently animates outdoor terrain liquids by updating animated liquid regions inside the terrain texture atlas.
This now works visually, including mip correctness, but it has runtime cost:

- CPU-side terrain atlas mip copies are kept for animated updates.
- On each liquid frame change, affected atlas regions and their mip rectangles are updated.
- `bgfx::updateTexture2D` uploads are issued for animated liquid tiles.
- The cost grows with terrain scale tier and with the number of animated liquid atlas tiles.

This is acceptable as a correctness path, but it is not the ideal long-term renderer shape.

## OpenEnroth Reference Shape

OpenEnroth avoids per-frame terrain atlas mutation for water:

- It uploads `HDWTR###` frames once as layers in a texture array.
- It generates mipmaps once for that texture array.
- It computes the current water frame from time.
- It passes the current frame index as a shader uniform.
- Terrain, outdoor BModel, and indoor BSP shaders sample the animated water layer by frame index.

Runtime cost is therefore mostly a uniform update and shader sampling. There are no per-tick texture uploads and no
per-tick mip regeneration.

## Target Direction

Generalize the OE approach as animated surface materials, not hardcoded water:

- `water_mm6`: `6hdwtr000-013`
- `water_mm7`: `7hdwtr000-013`
- `water_mm8`: `hdwtr000-013`
- `lava`: `hdlav000-013`
- `oil`: `hwoil000-013`

The authoritative material mapping should remain in `assets_dev/engine/rendering/surface_materials.yml`.

## Proposed Renderer Strategy

1. Keep the regular terrain atlas static.
2. Build one texture array per animated liquid material at map/render-resource initialization.
3. Generate mipmaps for each liquid texture array once.
4. Add material ids or liquid animation ids to terrain and face render data.
5. Pass current frame index uniforms per liquid material, or a small uniform vector if frame timing is shared.
6. In shaders:
   - sample the static terrain/BModel texture normally;
   - if the surface is an animated liquid, sample the liquid texture array using the material id and frame index;
   - keep material-specific UV flow/distortion as separate metadata/flags.
7. Remove CPU terrain-atlas liquid mutation after terrain and face paths are migrated.

## Implementation Slices

### Slice 1: Terrain Only

- Upload terrain liquid texture arrays for water/lava/oil.
- Extend terrain vertices with a liquid material id or encode it in existing spare vertex data.
- Update the outdoor terrain shader to sample the liquid array for liquid tiles.
- Disable animated terrain atlas updates for terrain liquids.
- Keep BModel/fountain face animation on the current path.

### Slice 2: Outdoor BModels

- Reuse the same liquid material resolution for BModel faces.
- Add liquid texture-array sampling to the BModel shader path.
- Preserve face flow flags and lava/fluid behavior.
- Remove per-frame BModel texture handle creation for liquid animation frames where possible.

### Slice 3: Indoor Faces

- Apply the same material-array path to indoor BSP/liquid faces.
- Preserve indoor flow flags and disabled-animation flags.
- Verify fountains and special water/lava mechanisms still render correctly.

### Slice 4: Cleanup

- Remove terrain animated atlas update state if no longer used.
- Remove temporary CPU mip maintenance for liquids.
- Keep fallback animated atlas code only if there is a concrete non-liquid material that still needs it.
- Add regression coverage for material resolution and at least one terrain/BModel/indoor liquid case.

## Risks And Checks

- bgfx texture-array support and shader syntax must be validated across the active backends.
- x1/x4 asset selection must stay category-correct through `video_quality.terrain`.
- Mixed frame availability must be explicit: stale `terrain_x4/HDWTR000-006.png` should not silently override only part
  of a 14-frame sequence.
- Terrain transition overlays need a clear policy:
  - either keep transition tiles in the static atlas and sample liquid only for full liquid tiles;
  - or support liquid-array sampling under transition alpha masks.
- Material order and matching must remain deterministic for MM6/MM7/MM8 water aliases.

## Validation Plan

- Unit test material mappings:
  - `6wtrtyl -> 6hdwtr000-013`
  - `7wtrtyl -> 7hdwtr000-013`
  - `wtrtyl -> hdwtr000-013`
  - `lavtyl/lavatyl -> hdlav000-013`
  - `oiltyl/tartyl -> hwoil000-013`
- Headless map-load checks for representative MM6/MM7/MM8 outdoor maps.
- Visual checks:
  - MM8 water close/far movement with x1 and x4 terrain;
  - MM6/MM7 world-specific water color/style;
  - lava and oil/tar animation;
  - fountains/BModel water faces;
  - absence of terrain tile seams with mipmaps/aniso enabled.

