# OpenYAMM material rendering implementation blueprint

## Status and scope

Reviewed on 2026-09-18 against the **working tree**, including staged and unstaged changes, with HEAD
`7a1d58034`. HEAD alone does not reproduce this baseline. This is a source audit and future implementation
plan; the review did not implement materials, run a new build, or establish new GPU measurements.

The target is a small material layer in the existing bgfx forward renderer: geometric-normal sheen,
roughness/specular, optional Fresnel and emissive, global wetness, terrain material data, and authored puddles.
Preserve the current diffuse lighting, lightmaps, animation, event behavior, visibility and batching.

**None of the new material shading, wetness, puddle or material-mask features below is implemented yet.**
Existing surface animation, geometry normals on some paths, weather, light selection and lightmaps provide
integration points, not completed material features. All schema additions and new symbols below are targets.

## 1. Verified baseline and changes required

| Area | Current implementation | Required change |
| --- | --- | --- |
| Material metadata | `SurfaceMaterialDefinition` has string ID, water/lava/generic-animation semantics, scope, texture/attribute matching, animation and terrain transition behavior. No shading properties or compact render ID. | Extend the same table and carry resolved shading through map presentation data. |
| Material loading | `MapAssetLoader` reads `Data/rendering/surface_materials.yml`, resolved through the asset filesystem to the mounted rendering data. The base file is `assets_dev/engine/rendering/surface_materials.yml`. It caches the table and resolves animation at load time. | Preserve mounted lookup, shared-cache lifetime and existing animation precedence. Renderers currently do not receive a shading table. |
| Matching | `findMatch` lowercases names and returns the first matching row, checking terrain/face scope, required attributes, exact names and prefixes. | Keep this ordering. A catch-all inserted before water/lava would change existing behavior. |
| Terrain geometry | `TexturedTerrainVertex` already stores a Float3 normal. `buildTexturedTerrainVertices` assigns a flat normal per native triangle. | Forward the existing normal to fragments; keep the native diagonal and geometry. |
| BModel geometry | Textured BModel vertices get a normal only on classic ODM without applied lightmaps. `LightmappedBModelVertex` has no normal. BModelWorld currently does not get these normals. | Compute geometric normals independently of diffuse-lighting mode and carry them through both layouts and runtime transforms. |
| Indoor geometry | `IndoorRenderer::TexturedVertex` carries UV/flow/secret data and `bakedLightAbgr`, but no normal. CPU face geometry already computes normals. | Add flat normals through triangulation, light subdivision and moving-face updates. |
| Shader interface | World position already reaches outdoor, lightmapped and indoor fragments. No `v_worldNormal` exists. Indoor world shading has no camera-position uniform. | Add the missing normal varying and indoor camera input; do not duplicate world position. |
| Terrain textures | CPU structures still say `Atlas`, but the renderer uploads a mipmapped **256-layer texture array**. `v_flowInfo.x` carries the raw tile ID/layer. Water animation updates layers in place. | Index the material LUT by that existing layer, not animation-frame number or a new per-material terrain batch. |
| Outdoor lighting | Eight selected FX lights per draw, with clustering and bounds ranking. Nonbaked diffuse uses `u_outdoorSunlight`. Paired baked lighting uses separate sun/sky RGBM4 pages. | Add bounded specular without modifying diffuse selection or adding sunlight twice. |
| Indoor lighting | CPU-baked vertex lighting plus up to twelve selected live lights. Textured-batch selection passes `includeStaticLights=false`. There is no indoor texture-lightmap path equivalent to outdoor RGBM. | Preserve baked static lighting. Start local specular from an already selected live light. |
| Outdoor lightmap format | Runtime accepts only `.lighting` version 3. Paired MM6–MM8 bakes and combined imported MM9 maps share this version, distinguished by flags. | Keep the format and both shading meanings. No v1/v2 compatibility path. |
| Weather | `AtmosphereState` already contains rain intensity, night/underwater state and sun direction. There is no persistent surface-wetness state. | Add explicit render controls first; do not implement another weather system. |
| Resources/postprocessing | Existing image decoding, texture upload/filtering and runtime shader loading are available. Optional `CinematicGrading` already adds a fullscreen pass. | Reuse resources and preserve grading. The restriction is **no additional pass for materials**, not removal of an existing pass. |

Primary source map for implementation:

- [SurfaceMaterialTable.h](game/tables/SurfaceMaterialTable.h) and
  [SurfaceMaterialTable.cpp](game/tables/SurfaceMaterialTable.cpp): schema, parser and first-match rules.
- [MapAssetLoader.h](game/maps/MapAssetLoader.h) and [MapAssetLoader.cpp](game/maps/MapAssetLoader.cpp):
  `loadSurfaceMaterialTable`, `resolveSurfaceAnimation`, `findTerrainSurfaceMaterialForDescriptor`,
  `buildOutdoorBModelTextureSet`, `buildIndoorTextureSet` and presentation-load options.
- [OutdoorGameView.h](game/outdoor/OutdoorGameView.h),
  [OutdoorGameView.cpp](game/outdoor/OutdoorGameView.cpp) and
  [OutdoorRenderer.cpp](game/outdoor/OutdoorRenderer.cpp): vertex layouts, terrain setup, classic draw groups,
  BModelWorld chunks, dynamic mechanisms, resource creation/submission/destruction.
- [IndoorRenderer.h](game/indoor/IndoorRenderer.h) and [IndoorRenderer.cpp](game/indoor/IndoorRenderer.cpp):
  `buildFaceTexturedVertices`, `rebuildAllTexturedBatches`, moving-face updates and `drawLightSetForBatch`.
- [OutdoorLightingRuntime](game/outdoor/OutdoorLightingRuntime.cpp),
  [IndoorLightingRuntime](game/indoor/IndoorLightingRuntime.cpp) and
  [OutdoorSunlight.h](game/outdoor/OutdoorSunlight.h): existing light selection and day/night weights.
- [varying.def.sc](game/shaders/varying.def.sc),
  [outdoor_textured_fog.sh](game/shaders/outdoor_textured_fog.sh),
  [outdoor_bmodel_lightmap.sh](game/shaders/outdoor_bmodel_lightmap.sh),
  [outdoor_baked_lighting.sh](game/shaders/outdoor_baked_lighting.sh),
  [fs_indoor_textured_lit.sc](game/shaders/fs_indoor_textured_lit.sc): actual shading paths.
- [ImageAssetLoader](engine/ImageAssetLoader.h), [TextureFiltering](game/render/TextureFiltering.h),
  [RuntimeShader](game/render/RuntimeShader.cpp) and [BgfxRuntime.cmake](cmake/BgfxRuntime.cmake): resource and
  shader build conventions.
- [OutdoorSceneYml](game/maps/OutdoorSceneYml.h), [GameSettings](game/app/GameSettings.h),
  [GameApplication](game/app/GameApplication.cpp): map rendering metadata, INI and console integration.
- [Lighting format](level_generation/lighting/baked_outdoors/FORMAT.md) and
  [bake_outdoor.py](tools/lighting/bake_outdoor.py): bake encoding, recipe and dependency contract.

The [MM8 rendering comparison](re_mm8/OPENYAMM_RENDERING_COMPARISON.md) explains why existing persistent groups,
texture arrays and bounded light selection should be retained. Its historical measurements are not material
benchmarks. The [original rendering investigation](re_mm8/OUTDOOR_RENDERING.md) is a behavioral reference,
not code to copy.

## 2. Boundaries

Do not add deferred rendering, a G-buffer, SSR, planar reflections, reflection probes, cubemaps/IBL,
tangent-space normal maps, parallax, bloom, material graphs, runtime shader generation, an automatic puddle
simulation, terrain depression analysis, or another texture manager. No metallic workflow or authoring UI.
No new full-scene/world pass for material effects.

Target opaque terrain, opaque BModel faces and opaque indoor faces first. Leave billboards, instanced ground
cover, particles, decals, spell previews, HUD, sky and translucent surfaces on their existing behavior.
A window painted into an opaque facade can use a mask; transparent/refractive glass is outside this target.
Retain fluid animation and flow semantics; liquids do not automatically opt into puddles or new sheen.

Build shader changes through bgfx for GLSL 120, GLES 300 and D3D11 `s_5_0`. Preserve the existing optional
SPIR-V path and runtime shader lookup. Android currently selects GLES; Windows defaults to D3D11; other
normal desktop builds use OpenGL. Vulkan is an explicit build option and must not be built for this work
unless separately requested. Use bgfx helpers such as `vec3_splat` for scalar vector constructors; the earlier
D3D shader failure demonstrates why GLSL-only constructor syntax is insufficient.

Material properties and shader math belong in shared gameplay/render code. Keep BLV/ODM-specific geometry,
visibility and resource submission in their existing renderers. Add at most a small shared CPU material record
and a shader include; do not introduce a general renderer framework.

## 3. Material data contract

Extend `SurfaceMaterialDefinition` with optional `shading` data. Keep `SurfaceMaterialTable` as the single
authoring source. Add a `generic` semantic for static shading rows; retain `generic_animated`, `water` and
`lava` unchanged. `animation` remains optional. Do not reinterpret a shading row as an animation override.

Use standard existing types (`float`, `bool`, `std::array<float, 3>`, `std::string`), not a new math layer.
The following names are the proposed YAML contract:

| Property | Default | Validation/meaning |
| --- | --- | --- |
| `roughness` | `0.90` | Finite `[0.05, 1]`; controls sheen width. |
| `specular` | `0.0` | Finite `[0, 1]`; explicit opt-in, so old content has no new highlight. |
| `receives_wetness` | `false` | Enables the wetness response. |
| `wetness_response` | `0.0` | Finite `[0, 1]`; multiplied by global wetness. |
| `wet_roughness` | `0.12` | Finite `[0.05, 1]`. |
| `wet_darkening` | `0.08` | Finite `[0, 1]`; keep authored values subtle. |
| `receives_puddles` | `false` | Terrain only initially; requires wetness opt-in. |
| `fresnel_strength` | `0.0` | Finite `[0, 1]`; strengthens light-driven specular, not ambient glow. |
| `emissive_strength` | `0.0` | Finite `[0, 4]`; self-lit contribution in the path's working color domain. |
| `emissive_color` | `[1, 1, 1]` | Three finite components in `[0, 1]`. |
| `material_mask_texture` | empty | Optional mounted image path, introduced only in the mask phase. |

A missing `shading` block resolves to the neutral defaults. The original suggested global `specular=0.03`
would add a highlight to every old material; use zero for compatibility and author `0.03` explicitly where
wanted. Roughness alone does not enable shine. Wet materials need a nonzero specular value to show sheen.

Example target schema (illustrative texture name; choose an existing texture when authoring a fixture):

```yaml
materials:
  - id: castle_stone
    semantic: generic
    applies_to: [face]
    match:
      texture_names: [castle01]
    shading:
      roughness: 0.82
      specular: 0.04
      receives_wetness: true
      wetness_response: 0.8
      wet_roughness: 0.12
      wet_darkening: 0.08
```

Preserve first-match precedence and existing liquid rows. Require unique normalized IDs and validate new
shading keys/types/ranges; catch YAML conversion failures and identify the material/property in the error.
Do not silently skip an explicitly authored invalid shading block or substitute neutral data. Existing valid
animation YAML must continue to load. The current loader treats table failure as optional; propagate explicit
invalid shading failures through the presentation load instead of silently losing the requested effect.

Keep common definitions in the mounted base `rendering/surface_materials.yml`. Use precise texture matches
and namespaced content IDs where needed; a generic prefix must not affect unrelated worlds. Do not introduce
an unimplemented world-file merging scheme. Shared cache invalidation must follow existing world/remount
lifetime rules so matching never uses another mounted package's stale definitions.

## 4. Resolution, ownership and batching

Resolve shading during presentation loading/building. Add a compact `uint16_t` material ID with ID 0 reserved
for neutral shading; validate capacity instead of wrapping. IDs are runtime-only and must not enter saves,
native ODM/BLV geometry or `.lighting` files.

Carry a map-owned immutable set of resolved CPU materials and face/tile bindings with the map presentation
payload. Renderer batches reference IDs into that set. Table-definition pointers must not outlive the loader's
optional/copy of `SurfaceMaterialTable`. Keep bgfx handles in renderer-owned resources; do not put GPU handles
in the YAML table or headless map data, or duplicate all shading values into a second independently owned table.

Matching inputs include the effective texture name, relevant face attributes, and terrain/face scope. A cache
key containing only texture name is insufficient because `required_face_attributes` can distinguish surfaces.
Use logical source texture identity, not its current animation frame or selected asset scale tier.

Bind one material per compatible draw group using uniforms. Extend existing keys, preserving their other fields:

| Path | Existing grouping | Material integration |
| --- | --- | --- |
| Classic static ODM | `rebuildResolvedBModelDrawGroups`: resolved animation index + lightmap page; mechanisms are excluded. | Add material ID and retain lightmapped/nonlightmapped layout separation. |
| BModelWorld | Spatial chunks; animation + translucency, plus lightmap page for static-lit groups. | Add material ID within each chunk; preserve visibility and opaque/translucent ordering. |
| Dynamic BModels | Separate event/mechanism path with transformed vertices and effective attributes. | Reuse resolved material IDs and normals without adding submissions per triangle. |
| Indoor | `rebuildAllTexturedBatches`: texture + front sector + back sector; dynamic buffer ranges retain face identity. | Add material ID to keys, buffer reuse checks and stable selection-cache identity. Preserve sector boundaries. |
| Terrain | Whole terrain or existing local-light chunks using the same 256-layer array. | One per-layer LUT; zero new material-based terrain splits. |

Event texture replacement and relevant attribute changes must re-resolve materials through existing visual
revision/rebuild paths. Handle BModelWorld refresh and indoor partial rebuilds as well as initial loading.
Cache each new effective binding once; no per-frame string matching. Animation frame advance, camera movement,
wetness changes and scalar setting changes must not rebuild static geometry.

Create/destroy material uniforms, LUTs and mask textures with the renderer's ordinary map-resource lifetime,
including failed initialization and world switching. Bind complete neutral material state on every eligible
neutral draw; bgfx uniform state must not leak from a shiny surface into another draw.

## 5. Normals and shader interfaces

Forward `v_worldPosition` as already supplied. Add `v_worldNormal` to the actual vertex/fragment interfaces and
`varying.def.sc`. Audit active varying slots and the instanced decoration inputs before assigning a semantic;
existing flow/layer, lightmap, barycentric and sunlight fields already have meanings.

- Terrain: keep the current flat triangle normals and native diagonal. No smoothing or extra geometry.
- BModels: use `buildOutdoorFaceGeometry` to obtain a valid flat face normal regardless of lightmaps or scene
  profile. Preserve handling of collinear prefixes and degenerate faces. Copy it into lightmapped vertices.
- Runtime BModel transforms: rotate normals as vectors, without translation, and renormalize. Update copies
  into both vertex layouts in static rebuild, chunk refresh and dynamic mechanism submission.
- Indoors: derive a flat normal from the same transformed face geometry used for rendering. Keep it through
  triangulation/subdivision and moving-door partial buffer updates. Do not reorient UVs to add lighting.
- Guard zero-length normals and degenerate view/half vectors before normalization. Excluded geometry has no
  material contribution. Preserve existing culling; test both visible sides of currently two-sided faces.

The existing outdoor layout uses Float3 normals; there is no compact normal implementation in the inspected
paths. Reuse it initially. A standard bgfx normalized packed format is acceptable only if encoding, CPU stride,
shader decoding and all backends are verified together; custom normal compression is not a prerequisite.
Record the additional vertex bytes for lightmapped/indoor layouts.

Normals for specular must not accidentally re-enable legacy diffuse sunlight on BModelWorld, baked surfaces,
sky or overlays. Keep material lighting enablement distinct from the zero-normal convention used by
`outdoor_sunlight.sh`.

Shader coverage:

| Vertex shader | Fragment path(s) requiring integration |
| --- | --- |
| `vs_outdoor_textured_fog.sc` | `fs_outdoor_textured_fog.sc`, `fs_outdoor_terrain_fog.sc`, `fs_outdoor_terrain_baked.sc` |
| `vs_outdoor_bmodel_lightmap.sc` | `fs_outdoor_bmodel_lightmap.sc`, `fs_outdoor_bmodel_baked.sc` |
| `vs_indoor_textured_lit.sc` | `fs_indoor_textured_lit.sc` |

`outdoor_textured_fog.sh` is also included by terrain-decoration shaders. Gate material code explicitly so
those variants retain their current interface and behavior. Add only small math in a proposed
`game/shaders/material_lighting.sh`. Keep the existing finite set of explicit shader entry points.
Update CMake shader include dependencies; editing the new include must rebuild its consumers.

## 6. Lighting and color composition

### Preserve the three existing color paths

The renderer is not uniformly linear/HDR:

1. Paired baked outdoor paths decode RGBM4 to linear illumination, convert display-encoded albedo using power
   2.2, apply lighting, then encode with power 1/2.2 in `bakedSurfaceColor`.
2. Combined imported lightmaps use texture RGB times vertex RGB and existing FX lighting in the legacy domain.
3. Nonbaked outdoor and indoor paths multiply display-encoded textures by their existing lighting values.

For paired bakes, apply wet darkening to albedo and add specular/emissive **inside the existing linear expression
before its one display encode**. For the other paths, preserve their current diffuse equation and add the
bounded artistic specular/emissive term in that existing working domain. Do not globally enable sRGB textures,
linearize the whole renderer, reinterpret combined MM9 lightmaps as RGBM, or multiply specular by albedo/lightmaps
again. Exact visual equivalence at zero material contribution is a requirement.

Keep alpha tests, UV flow, perception discard, secret tint, fog and draw blend/depth state. Add material terms
before the existing secret tint and outdoor fog so emissive does not bypass those effects. Preserve the current
prelighting fog tint. Leave cinematic grading after world shading; test with it both off and on. No bloom or
light emission into gameplay/other surfaces.

### Light-driven sheen and Fresnel

Use one inexpensive Blinn-Phong style helper, with normalized world-space N, V, L:

```text
H = safeNormalize(L + V)
NoL = max(dot(N, L), 0)
exponent = mix(4, 192, 1 - roughness)
f = 1 - clamp(dot(N, V), 0, 1)
F = f * f * f * f * f
S = lightColor * attenuation * NoL * pow(max(dot(N, H), 0), exponent)
    * specular * (1 + fresnelStrength * F)
```

Constants are tuning values, not a PBR contract. Fresnel only boosts an actual light response; it must not
create an unlit outline. A disabled light, zero specular or invalid normal gives zero sheen. Keep highlights
bounded for the SDR target and avoid unstable infinitely sharp lobes.

### Directional source: do not reuse disabled diffuse state

`buildOutdoorSunlight` deliberately returns zero direct light when `mapData.lightingData` is present, including
when the lightmap application switch is off. Therefore `u_outdoorSunlight.xyz` is not a usable universal
specular direction. Add separate material sun direction/color inputs without changing that diffuse policy.

- Nonbaked classic exterior: use the atmosphere's normalized sun direction and existing daylight gating.
- Paired baked exterior with lightmaps applied: use the **fixed bake direction** and the already sampled sun
  source, weighted by `outdoorBakedLightingColors`. This attenuates sheen where the sun source is dark. The baked
  source includes diffuse incidence/bounce; this is an artistic energy proxy, not a binary shadow mask.
- Paired assets with `lightmaps=false`: use atmosphere direction/daylight for material sheen. Preserve the
  current diffuse result; any separate correction to lightmap-off diffuse behavior is outside this plan.
- Indoor, underwater, enclosed ODM and combined imported lightmaps: default directional material light to zero.
  Never invent an indoor sun or normalize a zero light direction. Local sheen and emissive still work.

The fixed bake direction currently exists in `.bake.json` (`profile.azimuth`/`profile.elevation`), not in
`OutdoorLightingData`; the atmosphere's time-varying X/Z direction is different. For material-enabled paired
bakes, resolve and parse the matching **already hash-validated recipe once at map load**, using existing YAML
support for its JSON syntax. Derive the direction with the producer's convention:
`(cos(e)*cos(a), cos(e)*sin(a), sin(e))`, with angles converted from degrees. Store it in map presentation data.
Do not hardcode one map's angle or add a per-frame recipe read. Missing/invalid required recipe metadata must
produce an actionable material-load error. This needs no lightmap format revision or compatibility reader.

### Local lights

Keep all existing diffuse iterations: eight outdoor, twelve indoor. Initially evaluate material specular for
**one existing selected live light per draw**. Outdoors the bounded list is ranked; indoors it reflects
Torchlight/FX budgets and selection history, not a globally sorted nearest list. Use its first eligible entry
and retain that established selection stability. Use the same position, radius, intensity, color and squared
attenuation as the diffuse path, without adding its diffuse contribution again.

Indoor static lights are already baked into vertex colors and omitted from these draw selections. Initial
material sheen therefore follows selected live lights such as Torchlight/FX; it does not reconstruct static
light directions from baked RGB. A separate static-specular selector is outside the initial target.

Do not extend the specular calculation to the whole existing loop. A second selected local light is optional
only after a recorded visual/performance comparison; two is the ceiling for this blueprint. Indoor sheen
validation requires this local-light stage; a directional-only phase cannot demonstrate it.

## 7. Global wetness and controls

Proposed shared settings under `[video]`:

```ini
surface_materials=true
material_wetness=0
```

`surface_materials=false` suppresses all new contributions and optional material texture work while retaining
existing diffuse/lightmap/animation behavior. `material_wetness` must be finite in `[0,1]`; add console get/set
support for reproducible `0`, `0.5` and `1` checks. Mirror the new keys/defaults in `settings.ini`,
`settings_release.ini` and `android/settings.ini`; preserve unrelated platform values. Settings changes should
update uniforms/program choices through current settings propagation, not rebuild geometry every frame.

Build one small material environment value per view/frame and upload it for each affected submission. It is
shared render state, not process-global mutable weather state. Initially only explicit configured wetness
changes the effect. The existing `AtmosphereState.rainIntensity` can feed a future policy; rain-to-wetness
accumulation/drying and save persistence are not part of this implementation.

Apply global wetness only to exterior world surfaces, and only if their material opts in. Indoors and enclosed
or underwater ODM scenes receive zero wetness; do not carry an outdoor value accidentally across a map switch.
Emissive and dry local specular are independent of wetness.

```text
W = clamp(globalWetness * effectiveWetnessResponse, 0, 1)
upward = smoothstep(0.25, 0.90, max(N.z, 0))
W *= mix(0.5, 1.0, upward)       # vertical exterior walls can still be partially wet
roughness = mix(dryRoughness, wetRoughness, W)
albedo *= 1 - W * wetDarkening
```

Bake `receives_wetness=false` into `effectiveWetnessResponse=0` in the resolved record. Apply an authored
wetness mask before roughness/darkening. This models exposure approximately: overhangs/roofs do not shelter
surfaces automatically. No new ray tests or rain occlusion.

## 8. Terrain lookup and binding budget

Keep the 256 existing layer identities, including invalid/default slots, descriptor fallbacks, animated water
and composited shore transitions. Store resolved shading next to tile presentation data while the table and
terrain descriptors are available. Do not re-match an animated upload each frame.

The original proposed 256x1 RGBA LUT cannot encode per-material wet roughness, darkening, Fresnel and emissive
in addition to its four suggested channels. Use one small **256x3 RGBA8 non-sRGB data texture** for the complete
scalar contract, with these logical channels:

| Row | R | G | B | A |
| --- | --- | --- | --- | --- |
| 0 | roughness | specular | effective wetness response | wet roughness |
| 1 | wet darkening | Fresnel strength | puddles allowed (0/1) | emissive strength / 4 |
| 2 | emissive R | emissive G | emissive B | reserved zero |

This is 3 KiB before driver overhead, independent of lightmap resolution. Use point filtering, clamp and no
mipmaps. Sample texel centers: X=`(layer+0.5)/256`, Y=`(row+0.5)/3`. Keep each triangle's layer constant.
Apply the BGRA/RGBA channel conventions of the existing upload helpers explicitly; masks are numerical data.
No color keying, gamma transforms or alpha-coverage processing of LUT values.

Budget **two LUT reads per material-enabled terrain fragment**, plus the third only when a map-level uniform
indicates terrain emissive is present. Skip the whole material branch when all terrain entries are neutral.
This corrects the earlier one-lookup cost estimate; measure it on Android as well as desktop. Do not claim
full per-layer properties while silently using shared wetness constants.

Composited shore layers contain more than one visual material. A scalar LUT cannot distinguish their land/water
pixels. Keep those mixed layers neutral for new wetness/puddles initially; preserve existing animation/compositing.
Per-pixel terrain classification is deferred rather than treating a shoreline as uniformly glossy water.

Proposed sampler allocation for these **world surface shaders** (other programs may reuse the same slots):

| Slot | Terrain | BModel | Indoor |
| --- | --- | --- | --- |
| 0 | Existing color array | Existing diffuse | Existing diffuse |
| 1 | Existing repeat-sampled water array | Existing sun/combined lightmap | Unused |
| 2 | Existing terrain sun page | Unused | Unused |
| 3 | Existing sky page | Existing sky page | Unused |
| 4 | New material LUT | Unused | Unused |
| 5 | New puddle mask | Unused initially | Unused |
| 6 | Unused initially | Optional packed material mask | Optional packed material mask |

Check sampler/varying limits for supported backends before implementation. Add an explicit fixed data-sampling
policy in the existing texture helpers, or direct bgfx binding with fixed flags. LUT point sampling and puddle
mask linear sampling must not change when the user toggles ordinary texture filtering. Own no duplicate manager.

## 9. Authored puddle mask

First support puddles on native terrain only, with one optional world-space grayscale mask per map. BModel
roofs, streets made of model faces, and stacked surfaces are excluded initially: one XY mask cannot distinguish
heights. Dry/wet BModel sheen remains supported through material wetness.

Extend the existing outdoor scene `rendering` schema, not the lightmap format. Proposed example:

```yaml
rendering:
  puddles:
    mask: worlds/mm6/rendering/puddles/oute3.png
    origin: [-32768, 32768]
    extent: [65024, -65024]
```

Use explicit mounted paths and validate finite origin, nonzero signed extent, dimensions and image decoding.
Absence means no puddles; an explicitly configured missing/corrupt image is an error, not a black fallback.
Prefer 256x256 or 512x512 authored images, RGBA/BGRA8 upload with the grayscale red channel sampled linearly,
clamped and without mipmaps. No alpha-derived visibility and no sRGB decode.

Define the first decoded image row as the row at `origin.y`; row order and signed extent must be tested with an
asymmetric fixture. Origin and origin+extent identify the first/last texel centers. Compute a mask-specific
half-texel transform from its own dimensions, analogous to the baked terrain transform, and return zero outside
the authored world rectangle. Clamping alone would smear an edge puddle beyond the rectangle.

Do not reuse `u_bakedTerrainBounds` or require lightmaps to be enabled: its half-texel adjustment depends on the
lightmap dimensions. Supply independent puddle bounds so the same mask works with `lightmaps=true` and `false`.

```text
P = maskRed * W * puddlesAllowed * upward
roughness = mix(roughness, 0.05, P)
albedo *= mix(1, 0.88, P)
```

The upward factor restricts puddles on steep slopes. Reuse W's material/mask eligibility; do not bypass
`receives_wetness`. Optionally bias only the specular normal toward world up, renormalizing safely. Leave diffuse
normals, terrain geometry, collision and alpha unchanged. No water plane, reflection, gameplay water flag,
new draw or pass. Bind a neutral black texel when necessary for valid sampler state, and skip sampling if no map
mask is authored.

`parseOptionalRendering` currently returns early if `view_distance_scale` is absent. Refactor that control flow
so a puddles-only block is parsed. Thread the data through base/overlay parsing, merge/apply and presentation
loading; retain explicit absence versus replacement when merging optional map overrides.

Current bakes hash `.scene.yml` dependencies. Adding puddle metadata to such a scene changes its hash even if
geometry is unchanged. Rebuild/reinstall the affected bake and recipe together, or implement an explicit reviewed
metadata migration that verifies unchanged bake inputs. Never suppress stale-dependency errors or merely rewrite
hashes to make a stale file load. Authoring/remounting new assets must work in both loose and packaged worlds.

## 10. Optional packed facade mask

Implement only with a real authored facade fixture after the core features pass. Use
`shading.material_mask_texture` as an explicit mounted image path; share the existing image loader and per-view
texture cache. First support opaque BModel/indoor materials only, not a second 256-layer terrain mask array.

| Channel | Meaning |
| --- | --- |
| R | Shine/smoothness selector: mix roughness toward `min(roughness, 0.10)`. |
| G | Multiplier of material wetness response. |
| B | Multiplier of material emissive contribution. |
| A | Reserved; does not affect opacity. |

An unmasked material has neutral mask **(0,1,1,1)**, not white or black. Bypass the sample for unmasked draws.
Use the same normalized base-material UV/flow as diffuse, never lightmap UV. A static mask must be valid for
every frame of its diffuse animation; per-frame mask animation is outside scope. A mask may be lower resolution
but must have matching orientation/aspect and repeat/clamp behavior. Decode as linear channel data without
color-key transparency. Give numerical masks deliberate filtering/mip rules instead of sprite alpha treatment.

Do not add mask texture IDs to every face or split facade geometry into window polygons. The resolved material
owns the mask binding; material ID already distinguishes compatible draw groups. Missing explicitly authored
masks must report their path. Validate x1/x2 asset selection alignment and packaged lookup.

## 11. Implementation phases and completion gates

Each phase must build independently. Preserve a neutral/default path throughout. Use phase status and evidence
here when implementation begins. **Phases A, B and C are implemented**; phases D–H are **pending**.

| Phase | Deliverable | Gate before proceeding |
| --- | --- | --- |
| A — data and ownership — **done** | Optional shading parser, generic semantic, neutral ID, map-owned CPU bindings, revision-aware resolution and material batch keys. | Existing liquid/animation fixtures pass; invalid data is diagnosed; no visual change, per-frame lookup or new terrain draw. |
| B — normals — **done** | Flat normals through all eligible layouts, transforms, subdivision and shader interfaces; indoor camera input. | Geometry/stride tests and all relevant shader variants pass; material terms still zero. |
| C — face response — **done** | Shared math, separate sun inputs, baked recipe direction, roughness/specular/Fresnel/emissive and one selected local specular light. | Baked/nonbaked outdoor and indoor fixtures respond to camera/light direction; zero/default matches baseline; nighttime has no sun highlight. |
| D — wetness | Shared controls, defaults in all three INIs, exterior eligibility, subtle darkening and wet roughness. | 0/0.5/1 captures; indoor/underwater/neutral exclusions; map transitions clear old state. |
| E — terrain LUT | Per-layer material data, fixed data sampling, existing array and chunk integration. | Two adjacent materials differ in one existing draw; animation/layer IDs stay correct; shore exclusions hold; LUT cost measured. |
| F — puddles | Optional scene metadata, image load, independent bounds, slope/eligibility gates and terrain-only response. | Asymmetric mask/corners tested, no out-of-bounds smear, lightmaps on/off alignment, missing authored asset error, valid bake dependencies. |
| G — packed mask (optional) | Opaque facade mask and exact neutral behavior. | Real facade fixture works without geometric splitting; unmasked path avoids sampling. |
| H — second local highlight (optional) | At most two existing selected lights. | Recorded visual benefit and acceptable CPU/GPU cost. Otherwise remain at one. |

Phase A evidence (2026-09-18):

- `SurfaceMaterialTable` parses the optional `shading` block with the section 3 contract (generic semantic,
  per-property defaults, range/finite/type checks, unknown-key rejection, duplicate-id rejection,
  puddles-requires-wetness and terrain-only validation). Errors name the material and property. A missing
  `shading` block stays absent at the authoring level; neutral defaults materialize in the resolved record.
  `MapAssetLoader` now fails the map load on an explicitly invalid table instead of silently dropping it;
  an absent file or empty table keeps the historical optional behavior.
- `SurfaceMaterialRuntimeSet` ([SurfaceMaterialRuntime.h](game/render/SurfaceMaterialRuntime.h)) is the
  map-owned immutable resolved set: neutral record at ID 0, capacity-validated `uint16_t` IDs, first-match
  resolution identical to table order, and a `(texture, face attributes, scope)` binding cache so rebuild
  paths never string-scan per frame. `receives_wetness=false` bakes to `effectiveWetnessResponse=0`.
- Ownership: the set rides `OutdoorMapData`/`IndoorMapData` (runtime-only; not in saves, native geometry or
  `.lighting`). Terrain keeps per-layer IDs in `OutdoorTerrainTextureAtlas.tileMaterialIds` with the existing
  liquid-base fallback order. Classic ODM draw groups key on `(animation, lightmap page, material)`;
  BModelWorld chunk groups on `(animation, translucency, material[, lightmap page])`; indoor batch keys,
  buffer-reuse checks and `stableId` (lighting selection-cache identity) include the material ID resolved from
  the effective texture and delta face attributes. Event texture/attribute changes re-resolve through the
  existing revision-gated rebuilds. Dynamic mechanism batches keep their base material ID and cache the
  effective ID by animation frame and effective face attributes, so unchanged submission does no string
  normalization or binding lookup while visual revisions resolve once.
- No shader, uniform, normal or geometry changes; resolved shading is inert CPU data. With the current
  shipped `surface_materials.yml` (5 rows, no shading blocks, no attribute constraints), material IDs are a
  pure function of texture name, so all batch keys degenerate to the previous grouping and draw order.
- Verification: 9 new doctest cases in [SurfaceMaterialTests.cpp](tests/SurfaceMaterialTests.cpp) (authored
  values/defaults, neutral records, wetness baking, first-match and scope precedence, attribute-sensitive
  binding with cache consistency, duplicate IDs, ten invalid-value cases, NaN/infinity, set independence and
  empty-set neutrality, generic rows beside liquid animation rows). `cmake --build build --target openyamm
  -j25` and the unit-test target build clean; full suite shows the same three pre-existing failures with and
  without this change (caused by unrelated uncommitted working-tree asset edits, confirmed by stash A/B);
  the mm6 probe headless scenario fails at the same pre-existing step with and without this change.

Phase B evidence (2026-09-18):

- Normals: `buildTexturedBModelFaceVertices` now computes the flat `buildOutdoorFaceGeometry` normal for
  every profile and lightmap mode (degenerate faces keep a zero normal; the classic non-lightmapped path
  keeps its historical face rejection on geometry failure, other profiles keep rendering with a zero
  normal). `LightmappedBModelVertex` gained a Float3 normal slot (stride 52 → 64 bytes, static_assert) and
  receives the normal in `buildLightmappedBModelFaceVertices` and the resolved-group copy. Indoor
  `TexturedVertex` gained a Float3 normal (stride 60 → 72 bytes, static_assert), set once per face from the
  same transformed geometry (`computeFaceNormal` + guarded normalization) in `buildFaceTexturedVertices`,
  carried through triangulation, baked-light subdivision (`interpolateTexturedVertex` lerps and
  renormalizes with a zero guard) and moving-door partial rebuilds (they reuse the same builder).
  `TexturedTerrainVertex` is unchanged (already carried flat triangle normals).
- Runtime transforms: new `transformOutdoorBModelDirection` in
  [OutdoorGeometryUtils.cpp](game/outdoor/OutdoorGeometryUtils.cpp) applies the mechanism rotation without
  pivot/translation and renormalizes (zero stays zero). The static resolved-group rebuild, and the dynamic
  mechanism submission for both layouts, rotate the face normal through the runtime transform. The
  BModelWorld chunk path builds world-space normals directly from map geometry (mechanisms are excluded
  from chunks).
- Shader interfaces: `v_worldNormal` added to [varying.def.sc](game/shaders/varying.def.sc) on TEXCOORD7
  (shares the semantic with the instanced `i_data0`, which never coexists in one program — same pattern as
  `v_sunlight`/`i_data1` on TEXCOORD6). `vs_outdoor_textured_fog`, `vs_outdoor_bmodel_lightmap` and
  `vs_indoor_textured_lit` forward it; the six fragment shaders in the section 5 coverage table declare it
  as input. Decoration shaders keep their exact interface. Indoor camera input: `u_cameraPosition`
  declared in `fs_indoor_textured_lit.sc`, created/bound per frame from the tracked indoor camera position
  in `IndoorRenderer` (the outdoor convention), unused until Phase C. No fragment shader reads the normal
  yet — material terms remain zero.
- Sunlight convention preserved by construction: `buildOutdoorSunlight` returns the neutral
  `{0, 0, 0, 1}` (ambient 1) for every path that newly gains normals (BModelWorld, any map with
  `lightingData`, non-exterior, underwater), where `outdoorSunlight()` evaluates to exactly 1.0
  regardless of the normal; the only normal-sensitive path (classic exterior without baked lighting)
  already had real normals.
- Verification: 6 new doctest cases in [SurfaceNormalGeometryTests.cpp](tests/SurfaceNormalGeometryTests.cpp)
  (flat quad normal, collinear degenerate face stays plane-less, out-of-range rejection, direction
  rotation per axis, mechanism fraction and renormalization, zero-normal pass-through). GLSL 120 rebuilt
  through `openyamm_runtime_shaders`; GLES 300 cross-compiled for all nine touched shaders with the local
  `openyamm_shaderc`; the local shaderc is built without the HLSL backend, so the D3D11 `s_5_0` check
  remains due from CI/Windows per section 12. Real-GPU isolated runs on `oute3.odm` and `6d01.blv`
  (Renderer: OpenGL 3.3) completed with no shader/program failures, confirming varying linkage. Full unit
  suite and the mm6 probe scenario show the same three pre-existing failures as the Phase A baseline.

Phase C evidence (2026-09-18) and open issue:

- Implemented: shared Blinn-Phong math, uniform set (`u_materialShading`, `u_materialEmissiveColor`,
  `u_materialSunDirection`, `u_materialSunColor`) and per-path response functions in
  [material_lighting.sh](game/shaders/material_lighting.sh), integrated in all four face paths with the
  section 6 color-domain placement: paired-baked adds sheen/emissive inside the linear expression before its
  one display encode (`bakedSurfaceColorWithEmission` in
  [outdoor_baked_lighting.sh](game/shaders/outdoor_baked_lighting.sh)); combined lightmaps and nonbaked
  outdoor add the bounded term in their existing domain; indoor adds it before the secret tint. Terrain and
  decoration variants compile the material code out, preserving their interface. The include was added to
  the shader-compile dependencies. Separate material sun inputs live in
  [OutdoorSunlight.h](game/outdoor/OutdoorSunlight.h) (`buildOutdoorMaterialSunInputs`,
  `surfaceMaterialBakeSunDirection`): baked exteriors use the fixed recipe direction parsed once at map load
  from the sibling `.bake.json` (`profile.azimuth`/`elevation`). On paired baked BModels the directional term
  is multiplied by the decoded per-fragment baked-sun sample, so baked shadows suppress sun sheen; local
  specular and emissive remain independent. Nonbaked and lightmaps-off exteriors use the atmosphere direction
  and daylight gating; BModelWorld/underwater/enclosed carry no directional sheen. Directional-material content with a
  paired bake but missing/invalid recipe fails the map load with an actionable error. Local sheen uses the
  first entry of each draw's existing ranked light selection with the exact diffuse attenuation. Material
  uniforms are bound per BModel draw (classic groups, BModelWorld chunks, dynamic mechanisms) and per indoor
  textured batch; translucent BModel groups, partial-alpha dynamic faces and indoor sky faces bind neutral
  state and retain their existing behavior.
- Unit: 2 new test cases (34 assertions) in [OutdoorSunlightTests.cpp](tests/OutdoorSunlightTests.cpp)
  covering the bake-direction math and every material-sun selection branch including night attenuation.
  GLSL 120 rebuilt; GLES 300 cross-compiled for all eight touched fragment shaders including decorations.
  Full suite: same three pre-existing failures as the Phase A/B baseline.
- Zero-contribution exactness: an explicitly authored `specular: 0` fixture over five town wall textures is
  pixel-identical to the neutral-table baseline within the capture-to-capture animation noise floor
  (0.007–0.024% vs 0.009–0.015% neutral-vs-neutral), on a real-GPU OpenGL 3.3 run of `oute3.odm`.
- Uniform delivery: per-draw `setUniform` for every BModel group (~19k writes/frame) proved unreliable on the
  GL renderer's frame uniform command stream — instrumented bgfx commit diagnostics showed only neutral values
  reaching the replay while later fixture writes vanished. The renderer already replays bound uniform values
  for every draw of a program, so material uniforms now enter the stream once per value change (a per-view
  last-material guard in `applyBModelMaterialUniforms` and the indoor batch loop — the same idiom as the
  existing once-per-frame light/fog uniform helpers). Each renderer invalidates its guard at frame start and
  at initialization/shutdown, so shared uniform names and map-local IDs cannot retain another view's values.
  Verified end-to-end on real GPU: an
  `u_materialEmissiveColor`-gated color probe renders on 27.6% of the frame (all BModel pixels), and a
  `u_materialSunDirection.w`-gated probe confirms the material sun reaches the shader. Material uniforms are
  also created before the first world-surface program in `initializeWorldRenderResources`, matching the GL
  renderer's resolve-at-program-creation behavior.
- Direction response (gate): a sheen fixture (`roughness: 0.85`, `specular: 0.85`, `fresnel_strength: 0.8`
  over the same five wall textures) measured against the neutral baseline across four camera yaws at the same
  position changes 0.00%/0.80%/0.41%/0.11% of the frame respectively — the response is present only at
  view/sun-aligned geometry, as expected for a half-vector lobe. A tight-lobe fixture (`roughness: 0.12`,
  exponent ≈169) legitimately shows no visible change at these angles. Nighttime has no sun highlight by the
  unit-tested attenuation (atmosphere daylight gating and baked-sun weights both reach exactly zero at night).
  Indoor response uses the identical deduped binding mechanism and compiled shader path; it was verified at
  mechanism level (bindings, resolution, uniform flow) rather than with a dedicated indoor fixture capture.
- **Open issue (end-to-end response)**: ~~with the fixture authored…~~ resolved by the uniform-stream fix
  above; this paragraph is retained as the investigation record. The failure was isolated through: table-load
  verification (set size), group resolution with valid unit normals on both layouts, ~19k/frame `setUniform`
  calls before the correct submits, shader-binary disassembly and a rename test proving the loaded binary,
  unconditional shader edits proving execution, and routing values through a long-standing uniform handle at
  the same call site (which worked). The custom bgfx GL uniform-cache patch and the GTX 3060 Ti driver were
  ruled out (the issue reproduced identically with the shadow cache fully bypassed); the defect was in our
  per-draw write pattern, not the GPU, the driver, or the cache.
- Session incident: a parallel session committed (`ab6babc86` "Fix shader compilation issue on windows") and
  added untracked bgfx EGL/cmake work while this phase was being verified; the shared `build/` tree and
  CMake cache changed underneath repeated runs (screenshot-tour behavior and camera poses also changed
  across identical invocations). Two bgfx patch-state repairs (`git checkout` of the patched files plus
  reconfigure) were needed and left the dependency tree consistent with the pinned patches. (Addendum: the
  repository owner confirmed this was their own interleaved activity, not another automated session.)

No full-repository rebake or bulk material authoring is required for early phases. Use a few explicit fixtures
first. Required acceptance covers A–F; G/H may remain deferred with the reason recorded. Do not mark deferred
features implemented or require broad renderer refactoring to finish them.

## 12. Verification and performance budget

### Automated checks

Prefer focused unit coverage for meaningful contracts:

- Existing material YAML and water/lava/oil animation continue to match; new static shading rows work.
  Test first-match precedence, attribute-sensitive binding, duplicate IDs, invalid/NaN/infinite data and defaults.
- Neutral ID, map ownership and world switches; same diffuse texture with different relevant attributes resolves
  correctly. Event texture/attribute replacements update only affected bindings; animation ticks preserve IDs.
- Normal direction/length through native terrain triangles, flat/collinear BModel faces, lightmapped copies,
  rotated mechanisms, indoor triangulation/subdivision and doors. Neutral geometry does not normalize zero.
- Uniform packing and LUT channels/ranges/centers, including BGRA/RGBA upload conventions, invalid tile IDs,
  animated water and mixed shore exclusions. Materials-off and zero wetness disable their intended terms.
- Puddle mapping, signed Y extent, image row order, out-of-bounds zero, absent versus broken assets, optional
  scene overlay behavior and independence from lightmap resolution/application.
- Retain [OutdoorLightingDataTests](tests/OutdoorLightingDataTests.cpp),
  [OutdoorSunlightTests](tests/OutdoorSunlightTests.cpp),
  [OutdoorLightingRuntimeTests](tests/OutdoorLightingRuntimeTests.cpp),
  [IndoorLightingRuntimeTests](tests/IndoorLightingRuntimeTests.cpp) and surface animation regressions in
  [GameplayRuleRegressionTests](tests/GameplayRuleRegressionTests.cpp). New material tests can be a focused file
  registered in `tests/CMakeLists.txt`.

Build with `cmake --build build --target openyamm -j25` and, for logic tests,
`cmake --build build --target openyamm_unit_tests -j25`; run only relevant test filters. Compile the modified
shader variants for GLSL, GLES and Windows/D3D11 via the appropriate configured builds/CI. A successful Linux
build alone is not a D3D11 or Android shader check. Do not launch a Vulkan build without current authorization.

### Runtime/visual matrix

Use existing isolated desktop/capture workflows and record the actual renderer, GPU, settings, camera and clock.
Headless scenarios validate map loading and state, not shader appearance. Test:

- MM6 `oute3.odm`, MM7 `7out01.odm`, MM8 `out02.odm`: default/neutral versus configured materials, lightmaps on/off,
  daylight/dusk/night, dry/half-wet/wet, flat/sloped terrain, facade and Torchlight/FX.
- An indoor BLV containing ordinary static faces, a moving door, secret surfaces, animated liquids and a sky face:
  normals and local sheen work while the excluded surfaces and static light toggles retain existing behavior.
- A mounted MM9 BModelWorld map such as `sturmfordcity.odm`: combined lightmaps, chunks, dynamic/translucent geometry
  and authored lighting remain valid. Do not add MM9-only work/cost when that content is not mounted.
- Terrain decorations on/off and grading on/off to catch shared-include/interface and color-order regressions.
- An Android **release** APK on representative hardware, plus a Windows D3D11 run/CI shader build. Preserve GLES
  budgets and platform settings. Desktop screenshots or emulator timing alone are insufficient mobile evidence.
- Loose `assets_dev` and regenerated ZIP/APK package loading for the authored masks/metadata. An already installed
  Android writable INI is not necessarily replaced by changing the bundled first-launch template.

### Measured limits

Hold camera, map, clock, resolution, asset tiers, view distance, grading, decoration density and light workload
constant. Measure GPU milliseconds and CPU submission/selection time rather than treating FPS as GPU time.
Record before/after draw counts, submitted vertex bytes, extra texture memory and map-load time. Include a
GPU-bound outdoor view and an indoor view with several local lights; record Android separately.

Targets, **not measured results**:

- Zero additional passes; zero terrain draws attributable to material IDs.
- Opaque-world draw-call growth ideally 0%, normally below 10%; investigate any representative case above 20%.
- Full opted-in effects within roughly 10–15% GPU time growth; investigate over 20% before acceptance.
- Neutral/materials-off CPU, GPU and loading cost should stay near baseline; measure vertex-bandwidth cost too.

If cost is too high: retain one local specular light; skip inactive mask/puddle/emissive reads; fix accidental
batch splitting; profile shader arithmetic and resource churn. Keep the existing spatial/light caches. Normal
packing is a measured follow-up, not a reason to introduce infrastructure or redesign the renderer.

The accepted result must preserve v3 lighting/dependency validation, animated surfaces, event-driven texture
changes, portal/sector visibility, day/night behavior and shared MM6–MM8 gameplay while exposing a small,
explicitly authored material response. Update this document with phase results and remaining limits as work lands.
