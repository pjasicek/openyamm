# Surface materials

Status (2026-10-30): implemented for outdoor BModel faces of baked maps and for BLV faces. MM6 New Sorpigal
(`oute3.odm`, 143 textures) has every map and was reviewed by day and night; the rest is produced per map through
[`level_generation/surface_materials/`](../level_generation/surface_materials/README.md) (local, like
`textures_x4`). Remaining work is listed in section 8.

Goal: render BLV faces and outdoor BModel faces (walls, floors, ceilings, doors, facades) as the materials they
depict. Brick is rough with recessed mortar, iron is metal, glass reflects the sky and glows at night, and carved
relief catches a low sun or a passing torch. Before this every face was one colour texture shaded like matte paper,
which is why facades read as flat paintings even with the 4× masters
([surface texture playbook](../level_generation/textures_x4/PLAYBOOK.md)).

Reference captures of the problem: [brick facade](surface_materials/reference_brick_facade.png) (MM6 town hall:
`thlgdr`, `thle`, `thre`, `thctr*`, `thuniq*`, `thsmdr`) and [porch](surface_materials/reference_porch.png) (MM6
tavern: `tavlgdr`, `tav*`), both in New Sorpigal (`oute3.odm`).

Out of scope: terrain (its own material layers, `game/shaders/outdoor_terrain_materials.sh`), 3D models (glTF PBR,
[model rendering](../engine/render/MODEL_RENDERING.md)), liquids, sky, sprites, and the lightmap bakes.

## 1. Before

| Surface | Inputs | Shading |
|---|---|---|
| Outdoor BModel faces (`outdoor_bmodel_lightmap.sh`) | One colour texture | Colour × baked sun and sky pages, grid point lights, wetness, fog. |
| Indoor faces (`fs_indoor_textured_lit.sc`) | One colour texture | Colour × (static light + grid point lights with the flat face normal). |
| Terrain | Colour+height, normal, AO+roughness per layer | Detail normals, cavity, GGX highlight, baked direct sun relit for the detail normal. |
| Models | glTF maps | PBR with a sky cubemap. |

Textures without maps still draw exactly this way (section 4.1).

## 2. Data

### 2.1 Authored per texture (by `mat.py`, never by hand)

In `assets_source/worlds/<w>/surface_materials/`, the same size as the 4× master:

| File | Content |
|---|---|
| `<stem>_h.png` | 16-bit height, white raised, black recessed; relative (depth in 2.3). |
| `<stem>_m.png` | Material classes as exact key colours of `tools/cook/surface_materials.yml`. |
| `textures.yml` | Per texture: `wrap` (from the texture inventory), optional `depth` and `painted_shading`. |

Exact duplicate textures receive copies of their canonical texture's maps. Where two masters of a wall family share
exact pixels, the later one copies the earlier one's maps there and eases its own height into them, so joints match.

### 2.2 Material classes

[`tools/cook/surface_materials.yml`](../tools/cook/surface_materials.yml): brick, mortar, stone, polished stone,
plaster, wood, iron (and lead), bright metal, patina, glass, painted/enamel, cloth, earth, foliage, glowing. Each has
a key colour, a prompt description, a roughness range, whether brighter detail is smoother (`gloss`, metals), metal,
relief and occlusion strengths, a typical relief depth and a glow (none, night, always).

### 2.3 Cooked (tools/surface_materials.py)

`assets_dev/worlds/<w>/surface_materials_x4/<stem>_n.oytex` and `<stem>_d.oytex`, both BC7 with linear channels, at
half the colour texture's size on each axis with the full mip chain below it (`MAP_REDUCTION`; computed at the
master's size, the cooker drops the top level):

| Map | r | g | b | a |
|---|---|---|---|---|
| `_n` normal | tangent x (+u) | tangent y (up the image) | glow: 0 none, (0, 0.45] at night, [0.55, 1] always (the gap survives BC7) | 1 |
| `_d` detail | ambient occlusion | roughness | metal | height (1 at the face plane, 8 world units at 0) |

- Height is normalised to its 0.5–99.5 percentiles and scaled by the texture's depth: `depth` in `textures.yml`, or
  the texel-weighted depth of its classes. One native texel is one world unit; the master texel is a quarter.
- Normals from the height in world units, scaled by the class relief strength and `1 - 0.6 × painted_shading`;
  gradients and blurs wrap on the axes the texture repeats on its faces.
- Occlusion from four scales of height (0.5–10 world units), class strength, `1 - 0.8 × painted_shading`.
- Roughness inside the class range by the master's fine brightness detail; metal per class; glow per class, brighter
  glass glowing more. Class properties are softened across class edges.
- On axes a texture does not tile, the relief flattens to the face plane over the outer 8 texels (2 world units).
  Faces sample with repeat even there, so filtering and parallax rays at a face edge reach the opposite edge; a
  column's side at one edge drew a dark line along the neighbouring face (town hall, 2026-10-30).
- The desktop cook (`tools/cook_surface_textures.py`, build target `openyamm_cook_surface_textures`) runs it after
  the colour textures; receipts recognise unchanged inputs by size and time. `--verify` and packaging check it.
- Packaging: `surface_materials_x4` ships on desktop only (`tools/packaging/packs.yml` domains; Android drops the
  folder). At full size the two maps took 1.7 times the colour textures on disk (about 4 GB more for MM6–MM8) and
  164 MB of video memory in New Sorpigal; at half size they take 32 MB on disk for New Sorpigal's 148 textures
  (their colour textures: 75 MB) and about 50 MB of video memory, and captures by day, dusk, night and up close
  showed no difference worth the rest.

## 3. Runtime

### 3.1 Loading

With `video.surface_materials` on, `loadFaceTextures` (`game/maps/MapAssetLoader.cpp`) reads both maps beside every
cooked colour texture: from `<world>/surface_materials<tier>/` next to its `textures<tier>/` folder
(`MapCompanionLoadOptions::surfaceMaterials`, set by `GameDataLoader::setSurfaceMaterials`). Off, nothing of them is
read, kept or uploaded. A map of another size or mip count, or only one of the two, is an error naming the cook. `OutdoorBitmapTexture::materialNormal` and `materialDetail` hold them
until upload.

### 3.2 Outdoor

- Lightmapped single-frame textures live in colour arrays per size; each array gets two material arrays of the
  layers that have maps (a lone layer is repeated: bgfx turns one-layer arrays into 2D textures). A vertex carries its
  material layer (`LightmappedBModelVertex::materialLayer`, -1 for none) and its face's texture gradients.
  Single-frame 2D textures get 2D maps.
- `OutdoorRenderer::bindSurfaceMaterial` picks the material programs (`fs_outdoor_bmodel_baked{,_array}{,_shadow}
  _materials`) for a group whose textures have maps while `video.surface_materials` is on, and binds the maps at
  stages 7 and 8 and the direct-sun page at 5. Animated textures, runtime-moved mechanisms and the BModel-world path
  (MM9, Hesper) draw without maps.

### 3.3 Indoor

`IndoorRenderer` creates 2D maps with each face texture and draws a batch whose single-frame texture has them with
`fs_indoor_textured_lit_materials` (or `fs_indoor_textured_baked_materials` on maps with indoor baked lighting,
maintained by that work).

### 3.4 Tangent frame

Each face starts its texture coordinates at its own edges, so screen-space derivatives of u and v break where two
faces meet (a dark seam on every wall). The CPU computes each triangle's world-space gradients of u and v
(`game/render/SurfaceTextureGradients.h`) into two vertex attributes (`a_tangent`, `a_bitangent`, varyings
`v_gradientU`, `v_gradientV`); only the flat normal comes from screen derivatives.

## 4. Shading (`game/shaders/surface_material.sh`)

### 4.1 Common

- A face without maps (layer -1 in an array group) takes today's path in the same shader.
- Normal map: +x along the u gradient, +y against the v gradient (up the image).
- Specular anti-aliasing widens roughness by the normal's variation across the pixel.
- Painted metal keeps half its diffuse colour (`SURFACE_METAL_DIFFUSE_LOSS`): the art already shows how the metal
  looks, and a fully specular metal goes black without a detailed environment.
- Only smooth and metal surfaces reflect the sky or room; the painted colours already hold rough surfaces' faint
  sheen (full reflection on brick greyed whole facades in the first capture).
- Glow: `surfaceGlowColor(albedo)` × strength × 0.8, added to the light: the texel's hue with the darkness of its
  paint compressed (`0.35 + 0.65 √peak`), as backlit stained glass shows its colours even where they are dark.
  Glowing at the paint's own brightness left dark cells black, which read as holes in the windows. The glow mask is
  the class alone; night glow follows `u_surfaceMaterial.y`.

### 4.2 Outdoor

Linear lighting from the bake for the flat face, as the terrain does:

- sun: indirect part × occlusion, direct part × relight (`max(n·L, 0) / max(nf·L, 0.15)`, the bake's sun direction
  `u_surfaceSun`) × moving-actor sun shadows;
- sky × occlusion × `(0.55 + 0.45 n.z) / (0.55 + 0.45 nf.z)`;
- grid point lights relit for the normal, with GGX highlights; the sun's GGX highlight from the direct page (shadowed
  where the bake is) at its strength at normal incidence;
- sky reflection: the Enhanced sky's gradient (`skyGradientLinear`) in the reflected direction, dim ground below the
  horizon, scaled to the bake's sky light at the point (recesses reflect less), split-sum response (Karis's fit);
- rain: wet surfaces darken and smooth (walls less), and on level faces the recesses fill first: puddles in mortar
  joints with a flat normal and roughness 0.03;
- night glow: 0 while the sun is above 0.05, 1 once it is 0.15 below the horizon (`OutdoorGameView::
  m_surfaceNightGlow`, from the game clock).

### 4.3 Indoor

Static light (vertex bake or lightmap) × occlusion; dynamic lights through the light grid (or the draw's own list)
relit for the normal with their flat-face response and GGX highlights; the room's own light as a dim environment
for smooth and metal surfaces; glass glows at any hour (lit from outside).

### 4.4 Parallax

Ten fixed steps with a linear crossing, within 1600 world units (fading from 65 %), in the main view only
(`video.surface_parallax`). Depth fades out toward grazing views and the offset per unit of depth is capped: at
grazing angles the ray crossed whole stones per step and smeared the recesses into blotches. No branches or explicit
mip levels: bgfx's desktop GL 3 path has no `texture2DArrayLod` (only `texture2DLod` is mapped to `textureLod`), and
implicit derivatives need uniform control flow.

### 4.5 Screen-space reflections

Smooth and metal surfaces (marble, glass, metal, puddles; roughness under 0.6) trace their reflected ray against the
previous frame's finished world instead of reflecting only the sky or room, as HDRP's SSR traces the previous
frame's colour pyramid. The renderer is forward with no G-buffer, so the trace runs in the material shaders.

- History (`CinematicGrading`, views `ReflectionHistoryColorView` and `ReflectionHistoryPositionView`, ordered
  before the presentation pass): the world colour at half resolution (RGBA8) and every pixel's world position
  relative to its camera (RGBA16F, rebuilt from the depth like ambient occlusion; a = 0 for the sky), with that
  frame's view-projection and camera. They must run before the presentation: bgfx's OpenGL screenshot reads whatever
  framebuffer was bound last, and history passes after the HUD made every capture (and save preview) black or white.
- Trace (`surfaceScreenReflection`): 24 steps from 12 world units growing by 1.3 (about 12,000 units), a hit where the
  ray passes behind what the history saw within twice the step, four bisection steps, the colour at the crossing.
  It fades at the screen edges, beyond 7,200 units, for rough surfaces (0.3–0.6) and for rays turning back toward
  the camera, whose targets no frame has seen. A miss keeps the sky or room radiance.
- Off (`video.surface_reflections`, or materials off): no history targets or passes; the shaders skip the trace on a
  uniform (`u_surfaceReflection`) and sample 1x1 placeholders (`SurfaceReflectionBinding`). Main view only; water
  reflections and portraits never trace.
- Measured (same desktop and window as section 7, switched with `render surface_reflections` inside one run): +0.11 ms
  at the town hall street, +0.25 ms on the tavern porch in heavy rain with the wet floor filling the view.
- Limits, as for any screen-space reflection: only what is on screen reflects, so a window seen straight on (it
  would reflect what is behind the camera) or along a street (to the side) shows the sky as before; floors and
  puddles reflecting what lies ahead benefit most.

### 4.6 Settings

`video.surface_materials`, `video.surface_parallax` and `video.surface_reflections` (Settings → Video → Experimental,
the last group of the tab) are off by default and outside the graphics presets, which neither set nor read them. The materials setting takes effect on the next map load: off,
the maps are not loaded at all (New Sorpigal: 649 MB of textures in video memory instead of 699 MB). The `render
surface_materials` and `render surface_parallax` console switches change the shading of the current map for profiling.

## 5. Production

[`level_generation/surface_materials/`](../level_generation/surface_materials/README.md): two Codex image calls per
texture on its master (a height map prompted as a renderer's depth pass, a class map in the key colours), aligned,
snapped to the master's edges, family-matched, checked and installed; `mat.py auto` runs job after job and leaves
flagged textures for review. Measured on the pilot (18 MM6 town hall and tavern textures): returns align within
2 texels at 1024 (phase correlation of edges); Codex keeps the reference's aspect exactly up to 2:1; one height in
18 tripped the colour-correlation check (planks, whose gaps are both dark and deep: accepted by hand); four class
maps needed one retry with a note (terracotta columns read as wood, stone door frames as polished stone). In the
first production job 8 of 24 heights correlated with the master's brightness above 0.8; six were right (gravel,
cobbles, roughcast, marble blocks, wood grain: dark is deep there too), two had traced mottled colour into bumps, so
the check flags above 0.9. Inventory entries with `exclude` (liquids, renderer materials) are never claimed.

Class map lessons from New Sorpigal (the prompt states the first two since):

- Stained-glass pictures came back as the materials they depict (a castle as stone, a knight as iron), so only their
  sky glowed. Everything light shines through is glass.
- Amber leaded glass came back as the glowing class, which glows by day. Tinted glass of any colour is glass; yellow
  is only for things that give light. `mat.py relabel mm6/pxstrlew glowing glass` fixed installed maps.
- The image generator's safety filter refused the height map of a nude sandstone relief (`tavldyle`); describing it as
  an architectural bas-relief carving passed.
- The height-against-brightness check is only a hint: gravel, cobbles and wood grain are dark where deep. Thin trims
  and flat slabs fail the alignment check because they have no edges to correlate; they were fine.

## 6. Lighting bakes

Unchanged: Cycles bakes flat faces and the shader adds the detail. The maps are not bake dependencies.

## 7. Cost

- Shader: two more samples per face pixel, ten more within the parallax range. Measured on New Sorpigal with the
  town hall facade filling the view (-10169.5, -8379.4, 161, yaw 3.145; visible 1600×900 window, vsync off, RTX
  3060 Ti), switching with the `render` command inside one run: GPU frame p50 1.45 ms off, 1.59 ms with materials,
  1.73 ms with parallax too (+0.14 ms each). The GPU timings of this desktop jump between two levels (about 0.7 and
  1.45 ms) with other programs on the GPU; in the lower level the step was about 0.38 ms. Expect up to 0.3–0.5 ms
  at 1600×900 and about 2.5 times that at 2560×1440 for a screen full of buildings.
- After the parallax loop got its uniform off switch (it used to run its ten steps at zero depth when parallax was
  off), the same camera measured 0.705 ms with materials off, 0.707 ms with materials on and parallax off, and
  1.00 ms with parallax on: the materials cost almost nothing, parallax about 0.3 ms with a facade filling the view.
- With every surface setting off, what remains is the vertex format: building and dungeon face vertices carry their
  material layer and texture gradients (56 to 84 bytes outdoors), and the original vertex shaders pass the two
  gradient varyings, because bgfx links only matching varyings.
- Memory and disk: see 2.3 (half-size maps).
- Memory: both maps are BC7 at one byte per texel each, so a texture with maps takes three times the VRAM of its
  colour texture alone.

## 8. Remaining

1. Production for every other MM6–MM8 map (`mat.py auto` per world), with review of the flagged textures and a
   check of every texture with glass or the glowing class.
2. Directional static light indoors: the vertex bake has no direction, so normal maps respond only to dynamic
   lights and occlusion there. The indoor baked lighting work replaces the vertex bake with lightmaps; a dominant
   light direction belongs in that bake, not in the vertex bake.
3. Runtime-moved mechanisms (doors, lifts) and animated textures draw without maps.
4. Android: no maps; a reduced set is possible later.
