# Indoor model lighting (scene `model_lighting`)

An opt-in, per-map lighting mode for indoor (BLV) maps that lights decorations (3D decoration models and decoration
sprites), actors and the other world models the way MM9 lit its `.abc` models. A map without the scene block (every
MM6–MM8 dungeon, Hesper's, every MM9 map that has not opted in) renders exactly as before: the block is the only
switch, and the old path runs unchanged when it is absent.

Why: the MM9 dungeons are rebuilt as native BLVs with baked lightmaps ([baked lighting](INDOOR_BAKED_LIGHTING.md)).
Under the bake, decorations took the room's actor ambient plus the BLV lights at their centre, minus the frame ambient
(`IndoorRenderer::billboardLightingUniform`), and came out much darker than the walls (Ruined Temple banners at 0.35
of the wall, Klusos House chairs at 0.37, Inventa Storca's tables black). In MM9 itself props read as bright as the
walls or brighter: MM9's lightmaps were baked with BrightScale and shadows, its models get the same lights at full
colour, unshadowed, plus the world ambient and a flat ModelAdd ([MM9 render lighting](mm9_rework/MM9_RENDER_LIGHTING_RE.md),
"Models").

## Scene block

```yaml
model_lighting:
  mode: mm9               # the only mode
  ambient: [60, 60, 60]   # 0..255: MM9's WorldInfo AmbientLight (required)
  add: [30, 30, 30]       # 0..255: MM9's ModelAdd (autoexec.cfg; this default when omitted)
  light_scale: 1          # >= 0: multiplies every point light for models (default 1; see "Light colours")
```

Parsed by `parseModelLightingNode` (`game/maps/IndoorSceneYml.cpp`) into `IndoorSceneData::modelLighting`, copied to
`IndoorMapData::modelLighting`; an overlay's block replaces the base scene's. A bad block (another mode, a missing or
out-of-range colour, a negative scale) fails the scene load.

## Formula

Per point, in 0..1 (MM9's 0..255 / 255), `game/indoor/IndoorModelLighting.h`:

```
light = min(1, ambient + add + Σ colour × lightScale × (1 − d²/r²) × max(0, N·L))      per channel
pixel = display texel × light
```

- **3D models** (`fs_model.sc`, `u_modelLighting[1].w = 2`, `ModelRenderLighting::fixedFunctionLighting`): the
  placement or instance light is the base (`ambient + add`); every light of the view's light grid over the fragment
  adds per pixel with MM9's falloff and N·L on the mesh normal, with no room test (MM9 lights per vertex with mesh
  normals, so normal maps are not used). The result multiplies the display (sRGB) texel, as MM9's stage-0 MODULATE does.
  No key light, specular, environment reflection, sun, edge darkening or SDR shoulder. Emission, fog, hover outlines and
  the hit flash apply as before.
- **Sprites** (`billboardLightingUniform`: decoration, actor and object sprites): a sprite faces the camera, so its
  lights arrive without N·L (`IndoorLightingRuntime::sampleModelLightRgb`: every light of the frame).
- A self-lit sprite frame (`Lit`, flames) stays at 1, as MM9's `ModelFullbrite` models draw at 255.
- No frame-ambient subtraction, no room or bake actor ambient, no shadows and **no occlusion**: MM9 has no
  visibility test for model lights, so a light reaches a model through floors and walls. The frame therefore takes a
  static light when its sphere reaches the view of any visible room (`IndoorLightingFrameInput::lightsIgnoreReach`),
  not only through the rooms it reaches by portals, and models skip the grid's room test. This matters: Klusos
  House's master-bedroom dresser and tall cabinet get their whole MM9 light from `Light18` (255, 255, 159, radius
  1024), which hangs in the room below them. Faces are unaffected: they take only the grid's dynamic lights, by room.
- **Actors** use it too, behind the same block: MM9 lit characters with the same loop, and creatures share the model
  path, so the cost is one branch.
- Reflections in water: the decoration placements' base only (a reflection pass has no light grid).

Not reproduced: MM9's light table for `FastLightObjects=1` lights (linear `1 − d/r` into the base; our BLV lights do
not carry the flag, and almost every Klusos light is `FastLightObjects=0`, a per-vertex light), the five-light cap
(`MaxModelLights`), dynamic `Fire` flicker lights and the unknown `PlayerLightOn` light. Lights MM9 had that the
converter left out of the BLV (over the four-per-floor-point cap; bake-only extra lights) do not reach models.

## Light colours

The frame carries a map light as its colour × alpha 224/255 × `IndoorLightScale` 1.35
(`IndoorLightingRuntime::mapLightStrength`, 1.186); the mode divides that out (`fixedPointScale`, and the same in
`sampleModelLightRgb`), so a BLV light lights models at the colour written in the BLV. Decoration lights (alpha 208),
the party torch and spell lights keep their strength relative to a map light.

What our data holds (2026-10-30):

- The shared converter (`level_generation/projects/mm9r_common/dungeon/lights.py`) writes MM9's `LightColor` raw (no
  BrightScale) and radius × 2.56: the mode then gives MM9's model colour exactly, `light_scale: 1`. Klusos House,
  the Lich Lab, Anskram Keep and the other maps on the shared `build_lights` are like this.
- Some per-map converters pre-multiply BrightScale into the BLV colour (Ruined Temple `blv_colour`, Training Hall,
  Tasar Academy, Bathhouse, Beethoven), and the shared converter does with `map: {bright_scale_lights: true}` (the
  converted cities, 2026-10-31: MM9's lightmaps carry colour × BrightScale). Their models would get MM9's light ×
  BrightScale; such a map sets `light_scale` to about 1 / its typical BrightScale when it opts in.

## Converter opt-in

`overrides.yml` `map: {model_lighting: true}` (or a map `{light_scale: x, add: [r, g, b]}`) makes the shared converter
write the block (`Source.model_lighting`, `build.py` `scene_file`): `ambient` from the DAT's WorldInfo string
`AmbientLight r g b` (any case; 0 0 0 when absent, as MM9's light table), `add` 30 30 30. Off by default: maps that do
not opt in get a byte-identical scene. The block changes only the scene, not the BLV, so no rebake is needed.

## Klusos House trial (2026-10-31): not adopted

Klusos House was rebuilt with the block (scene only; BLV and bake unchanged) and its four real-shot views
(`level_generation/projects/mm9r_klusoshouse/make_real_tour.py`, `real_compare.py`) compared with the real MM9
screenshots, then switched back off (`overrides.yml` `model_lighting: false`). Central-crop luma against real MM9:

| Shot | Old path (real09) | Model lighting (real11) |
| --- | --- | --- |
| 1 west bedroom | ×1.02 | ×0.92 |
| 2 doorway | ×1.01 | ×1.01 |
| 3 master bedroom props | ×0.96 | ×0.77 |
| 4 great hall | ×0.89 | ×0.88 |

By eye (`review/model_lighting_props01.jpg`: real MM9 | old | model lighting) MM9's dresser, cabinets and chair are
warm and bright, the old path is close to them, and the model lighting draws them darker and browner. Measured with
two probe renders (ambient 255 and no lights for the bare texel; lights only at scale 1), the master-bedroom dresser
gets 0.40 of its texel from the lights, about 0.75 with the base, against MM9's ~0.9. The textures themselves match
MM9's skins in brightness. What is missing:

- **The capped fill lights.** MM9's models take every light; the converter leaves a light out of the BLV once a floor
  point is under four (it becomes a bake-only extra light). In Klusos `Light19` alone gives the west-bedroom and
  great-hall cabinets 0.57 and 0.49 of its colour in MM9; ours never see it. A map's models would need those lights
  too (for instance a `model_lighting` light list the frame adds for models only) before the mode can match MM9.
- **Coarse MM9 meshes.** The ported `.abc` props are low-poly boxes (cabinet04ns: 50 vertices, 20 triangles). The
  panel diagonals seen at the time were mostly scrambled normals, not the mesh: until 2026-11-06 the props builds
  exported the glTF import's custom normals garbled by their bmesh round trip, so each triangle of a flat panel had
  unrelated normals (on both lighting paths). Fixed in `blib.import_raw` and in the installed models
  (`level_generation/props/mm9_isleofashes_claude/scripts/renormal.py`); see that project's README.

The old path stays the default; a map that tries the mode compares its real-shot views first.

## Code

| Piece | Where |
| --- | --- |
| Block, falloff and clamp | `game/indoor/IndoorModelLighting.h` |
| Parsing | `game/maps/IndoorSceneYml.cpp` (`parseModelLightingNode`, `parseIndoorSceneModelLighting`) |
| Sprite lights | `IndoorLightingRuntime::sampleModelLightRgb`, `IndoorRenderer::billboardLightingUniform` |
| Model setup | `IndoorRenderer::render` (creatures, decorations), `updateDecorationModels`, `renderWaterReflections` |
| Shader | `game/shaders/fs_model.sc` (fixed-function branch, `modelFixedPointLight`) |
| Uniform packing | `engine/render/ModelRenderer.cpp` (`modelLightingModeUniform`, `modelSunOrPointScaleUniform`) |

Checks (2026-10-31): MM8 `d06.blv` renders unchanged with the mode compiled in (outside the hanging lantern, whose
animated flame differs between any two runs, the before and after shots are pixel-identical); the Lich Lab
converter output is byte-identical with the opt-in off; the indoor regression suite passes.

Tests: `./build/tests/openyamm_unit_tests --test-case='*indoor model lighting*'` (falloff and clamp, sprite light
sampling, block parsing and refusals, a scene without the block, overlays).
