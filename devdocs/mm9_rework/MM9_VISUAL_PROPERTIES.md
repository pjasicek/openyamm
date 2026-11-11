# MM9 visual properties: what MM9 defines, what we render, what we lose

Survey of 2026-10-30 for the [MM9 rework](README.md). Goal (user): "we don't necessarily need to 'lose' anything, only
match and/or gain". Every visual or material property MM9 stores in its data is listed below with its evidence, how
often it is used, the OpenYAMM feature that can carry it today, and what each converter or creature brief should do.

Research only: no game data or engine code was changed.

**Legend.** **V** = verified (read from the files, counted, or seen in decoded images and disassembly). **I** =
inferred (consistent with the data, not confirmed in MM9's renderer). Counts are over all 45 `WORLDS/*.dat`, all 3,503
DTX files (`TEXTURES` 1,787, `SKINS` 895, `SPRITETEXTURES` 821), 843 of the 847 ABC models (4 do not parse with
`convert_abc_model.read_abc`), the 270 rows of `MONSTERS.txt` and the 802 `.scr`/`.inc` scripts.

**Method.** Scratch scripts on the repository's own parsers: `transcode_mm9_dat_to_odm.read_dat_world` (DAT surfaces,
objects, lightmaps), `convert_abc_model.decode_dtx_mips` and `read_abc` (DTX pixels and headers, ABC pieces), plus
`struct` reads of DTX sections and `.spr` files. Semantics come from the LithTech sources in `mm9/lithtech/`
(`runtime/shared/src/dtxmgr.h`, `runtime/world/src/de_world.h`, `tools/utils/mconv8to9/basetypes_de.h`), from MM9's
own preprocessor `mm9/mm9_tools/Lith21tools/Processor.exe` (flag table disassembled with `objdump`) and from MM9's
`game/data/object.lto`. "Visible" surfaces below exclude `Invisible.dtx` and `SURF_INVISIBLE`, and count the main world
(`PhysicsBSP`) and brushes but not the `VisBSP` hull. The scans were one-off scratch scripts; a converter that needs
these counts per map should get them from `tools/mm9_import_discovery/inventory_mm9_rework.py` (not yet extended).
Engine references were read in the working tree of 2026-10-30, including uncommitted changes.

## Five findings that matter most

1. **The green pod lamps and the teal crown are baked texture light, not palette or vertex colour (V/I).** Five DTX
   files carry a `LIGHTDEFS` section, a light that MM9's preprocessor attaches to every surface using the texture (I:
   `Processor.exe` contains the strings `LIGHTDEFS`, `center`, `dirlight`; V: the lightmaps below).
   `YANMIRSOLIDICE1.dtx`, the Lich Lab pod and crown glass, says `center 0 0 640 16 128 128`: a teal light, radius 640.
   The Lich Lab DAT's own lightmaps prove it: `bronze-grid-light` polygons next to the pod glass carry lightmap colour
   (103, 237, 237) with no Light object of that colour in range (only white `DirLight29`); multiplied with the texture's
   lit pixels (128, 100, 66) that is (52, 93, 61), green. The pod-glass polygons themselves bake at (85, 195, 195). Our
   Lich Lab bake has the Light objects, sky faces and window panes, but not this light. Carry-over: emit `LIGHTDEFS` as
   coloured area emitters in the bake profile (converter only; the bake already takes `emitters`).
2. **`DTX_FULLBRITE` uses the texture's alpha as a glow mask (V).** In the 11 textures with the flag, the alpha channel
   is the shape of the lit part: the stained-glass window in `GLASSWINDOW`, the light strip in `XEENPLAINWALLWITHLIGHT`,
   the glowing rune in `XEENTHREEARCHESBRIGHT2` (decoded and inspected). Opaque ones (`STATSTONE`, DXT1) glow everywhere
   (I); in `YANMIRSOLIDICE1` the uniform alpha 191 is also its translucency, so there it reads as about 75 % glow (I).
   This maps one-to-one onto the surface-material "glowing" class and onto glTF emission with the alpha as the grey
   mask. Few maps use it (the Xeen textures are in no DAT), but the Lich Lab and Yanmir's Fort ice does (655 polygons).
3. **MM9 translucency is two numbers multiplied: texture alpha × brush `Alpha` (V for the data, I for the product).**
   Surfaces with `SURF_TRANSLUCENT` (0x8) cover 15,021 visible polygons in 44 maps; 285 brushes (`WorldObject`, `Door`)
   set an object `Alpha` below 1 (0.15–0.95). The Lich Lab glass is `Lichwindow.dtx` (pale blue, alpha mean 119 of 255)
   on brushes with `Alpha` 0.7 and 0.8. (This survey first called that "the misty sky-lit hall". There is no mist: see
   "Correction" below.) The engine-crown glass is `YANMIRSOLIDICE1`
   (blue, alpha 191) on `Engineglass2-4` doors with `Alpha` 0.5. Water is the largest user: animated `water123.spr`
   alone is 10,186 translucent polygons (1000 Terrors, Wizard's Lab, Boot Camp, Training Hall). The engine is closing
   this gap today: uncommitted work of 2026-10-30 adds per-face `translucent_faces: [{faces, opacity, tint, two_sided}]`
   to BLV scene files, drawn after the opaque scene as texture colour × `tint` at texture alpha × `opacity`, sorted back
   to front (`game/maps/IndoorSceneYml.cpp:613`, `game/indoor/IndoorMapData.h` `IndoorFaceTranslucency`,
   `game/indoor/IndoorTranslucentFaces.h`). That is exactly MM9's product, so the converter only has to emit it. Classic
   ODM BModels have no such path; only the old `bmodel_world` ODMs blend (texture alpha only, unsorted).
4. **`Transparent 1` in `MONSTERS.txt` means "draw the skin with its alpha", not "ghost" (V for props, I for
   monsters).** In `object.lto`, `Transparent` sets object `FLAG2` bit 0x400 and `Chromakey` sets bit 0x2
   (`FLAG2_CHROMAKEY` in LithTech 1.x headers). The 257 placed props with `Transparent 1` all have graded-alpha skins
   (lantern glass: `TerrorLight1` 25 % partly transparent texels, `OilLamp`, `Lamppost3`), the 465 with `Chromakey 1`
   have 1-bit cut-out skins (bushes, tree branches). The 30 `Transparent 1` monsters include the Rooster, Fish, Lich,
   Prisoners and the Dragon King, so it is not a ghost flag. Their skins are mostly opaque: Ghost 3 % cut-out texels,
   Banshee 5 %, Dagrell and Venomous Dagrell 3 %; Jellyspore 1/2, Dragonfly 1-3, Spectre Dagrell (`DAGRELL3`) and the
   Prisoner skins have all-zero alpha (the common "no alpha" case: 673 of 895 skins, all on ordinary opaque monsters).
   So MM9 data gives whole-body translucency to no monster. The user's decision (only Banshee, Ghost and Spectre Dagrell
   see-through, PLAN.md) is a gain over MM9, not a loss; what the data does ask for is alpha cut-outs and soft alpha
   edges on these 30 skins.
5. **Animated textures are a real MM9 feature; we can animate them on surfaces and static models, not on creatures.**
   `.spr` files are frame lists with a frame rate (`uint32 frames, fps, 0, 0, 0`, then names). 13,014 visible world
   polygons in 36 maps use one (bit 0x4000 is set on exactly these surfaces: 12,626 of 12,626), mostly water (`water123`
   10 frames at 15 fps, `Ocean4` 19, `slime` 20) plus `Perception`, `twinkle`, `Thjoradtank` and torch flames. The
   Nettle Spore skin is `NettleSpore.spr` (8 frames `JellysporeBani1..8` at 7 fps), the Banshee's five skins are a 6 fps
   `BANSHEE.spr` sequence (B, B, C, C, D, D, E, E, A, A) also listed in `object.lto`'s Banshee class. Water can go to
   our water shader; other surfaces can use the MM6–MM8 texture frame table (looked up by texture name). Static models
   have a flipbook (`extras.openyamm_flipbook`), but skinned creatures do not: their shaders apply only UV scroll, so
   the Nettle Spore and the Banshee need a small engine addition or an emission pulse as a stand-in.

## The property table

Columns: **What** it is; **Evidence**; **Use** (count, examples); **OpenYAMM** (existing equivalent or GAP);
**Carry-over** (converter change C, creature/prop pipeline step P, engine feature E, or none).

### A. DTX texture header and sections

| Property | What | Evidence | Use | OpenYAMM | Carry-over |
| --- | --- | --- | --- | --- | --- |
| Version / layout | `-5`, header 164 bytes, mips then optional sections (`dtxmgr.h`) | V | all 3,503 | decoder `convert_abc_model.decode_dtx_mips` | none |
| `DTX_SECTIONSFIXED` 0x8 | bookkeeping bit | V | all 3,503 | – | none |
| `DTX_FULLBRITE` 0x1 | fullbright; **alpha = glow amount** (finding 2) | V (6 masks inspected) | 11: `GLASSWINDOW`, `XEENWINDOW`, `XEEN*WITHLIGHT`, `XEENTHREEARCHES*`, `SEWERCEILING`, `YANMIRSOLIDICE1/2`, `STATSTONE` (skin), `INVISIBLE`. In DATs: `yanmirsolidice1` 655 polys (Lich Lab, Connecting Tunnels, Yanmir's Fort); `StatStone` props 10 | surface-material class `glowing` (glow `always`, packed in the `_n` map; `tools/cook/surface_materials.yml`, `game/shaders/surface_material.sh:125-130`; desktop High preset only, not on animated textures or movers); model emission (`engine/models/GltfModelLoader.cpp:470-482`, `game/shaders/fs_model.sc:34-37`, bloom) | C: write the alpha as the glow mask of the class map; P: StatStone emissive texture = alpha |
| `DTX_PREFER4444` 0x80 | "keep a graded alpha in 16-bit" = artist marked the alpha as real | V (correlation) | 673 (sprites 409, textures 143, skins 121). Textures with it: 119 graded alpha, 15 cut-out, 9 opaque | – | C/P: use as the "alpha is meant" signal when choosing blend vs opaque |
| `DTX_PREFER5551` 0x100 | 1-bit alpha | V | 19 (skins 10: `DAGRELL1-3`, `SEACREATUREF/M`, `BONEPILE`, `HERB-RACK1`...; textures 9: ladders, doors, `ARENAPEOPLE1/2`) | glTF `MASK` (`GltfModelLoader.cpp:681-692`); faces discard at alpha ≤ 0.001 indoors (`game/shaders/fs_indoor_textured_lit.sc:236`) and ≤ 0.1 on BModels (`game/shaders/outdoor_bmodel_lightmap.sh:241`) | P/C: cut-out, not blend |
| `PREFER16BIT`, `CUBEMAP`, `BUMPMAP`, `LUMBUMPMAP`, `32BITSYSCOPY` | – | V | 0 | – | none |
| User flags (`m_UserFlags`) | surface type for sounds/footsteps (`MATERIALS.txt` hit sounds). Values seen: 0 none/sky boxes, 1 flesh, 2 leather, 3 chain, 4 plate, 6/7 shields, 8 metal hollow, 9 metal solid, 10 wood hollow, 11 wood solid, 12 stone, 13 earth, 14 grass, **15 glass**, **16 liquid**, **17 sky**, 18 web/cloth, 19 carpet/cloth, 20 sound-only, 21 snow, 202 invisible (LithTech internal id) | V (names per value sampled) | 12 stone 1,004; 0 1,147; glass 38 world textures (64 in all), liquid 6 (+ water sprites), sky 52 | surface-material classes (15: brick … glass, cloth, earth, foliage, glowing; `tools/cook/surface_materials.yml:15-139`). Note: class `glass` is opaque (low roughness, reflects, glows at night), not see-through | C: pre-label class maps: 15 glass, 16 liquid, 8/9 iron/bright metal, 10/11 wood, 19 cloth, 13/14/21 earth/foliage; drop 17/20/202 faces |
| `m_Extra[0]` texture group | – | V | 4 blast marks (5) | – | none |
| `m_Extra[1]` mips used | 1–2 = draw only the top mips (keeps fine detail sharp) | V | 21: `BANSHEEA-E`, `GREATERDEMON`, `LESSERDEMON`, `DRAGONEARTH`, tree branches, `MINELANTERN-BRIGHT` | – | none (our textures are regenerated) |
| `m_Extra[3..5]` | non-S3TC offset, UI mip offset, priority | V | all 0 | – | none |
| Detail texture (command string `DetailTex Textures\detailtextures\det_NN.dtx`, scale `m_Extra[6..9]`, angle `[10..11]`) | a second fine texture blended in at close range | V | 606 world textures (13 detail maps `det_02`..`det_12`, 14 spelled `DteailTex`); stored scale 5.0 in 598 (Jupiter's accessor adds 1, I), angle 90° in 16 | x4 textures and surface-material relief cover close-range detail | none (x4 masters replace it); optionally hint `tex.py` with the detail map |
| Section `LIGHTDEFS` | a light attached to the texture: `center x y radius r g b [r2 g2 b2]` and optional `; light x y radius r g b` | V (5 files decoded; `Processor.exe` strings) | `YANMIRSOLIDICE1` teal 16,128,128 r640 (655 polys, 3 maps); `TEMPGLOWICE` cyan 0,255,255 r512 (64 polys, Frosgard, Frosgard City); `LAVAVEINS`/`LAVAVEINS5` orange 255,96,0 r128 + red; `OUTER_WALL_02_LIT` green 0,255,0 (both unused in DATs) | indoor bake `emitters` `{textures, colour, strength, display, outward}`: each emitter face is a flat-coloured Cycles area light (`tools/lighting/bake_indoor.py:51-70,121,344-348`). Outdoor bake: sun and sky only, no emitters (`tools/lighting/bake_outdoor.py:212-214`) | **C (indoor): one emitter per LIGHTDEFS texture with its colour** (finding 1); outdoor (Frosgard `tempglowice`): gap |

### B. DAT world surfaces (per BSP surface)

Bit names: MM9's `Processor.exe` maps brush properties to bits (`or esi,` table at 0x41aca1–0x41b028): Solid 0x1,
Nonexistant 0x2, Invisible 0x4, Translucent 0x8, SkyPortal 0x10, FullyBright 0x20, FlatShade 0x40, LightMap 0x80,
Subdivide (clears 0x100), HullMaker 0x200, AlwaysLightMap 0x400, DirectionalLight 0x800, GouraudShade 0x1000, Portal
0x2000, SkyPan 0x8000, Additive 0x80000, TimeOfDay 0x100000, TerrainOccluder 0x40000, VisBlocker 0x200200, NotAStep
0x400000. Bits 0x4000 and 0x10000 are set elsewhere in the preprocessor.

| Property | What | Evidence | Use (visible polys, maps) | OpenYAMM | Carry-over |
| --- | --- | --- | --- | --- | --- |
| Translucent 0x8 | blend with texture alpha (× brush `Alpha`) | V flag, I blend rule | 15,021 / 44. Water sprites 12,000+; `ChainLink` 405, `web3` 204, `starfield` 204 (night sky), `r_wood_ladder` 156, windows (`window_03`, `thjorwindow2/3/4`, `windowlead1`, `iron_window`, `Lichwindow` 60, `ruinglass`...), `Clouds1`, crowd cards `arenapeople1-3` | BLV: **in progress, uncommitted (2026-10-30)**: scene `translucent_faces` (opacity × texture alpha, tint, two-sided; `IndoorSceneYml.cpp:613-669`, `IndoorRenderer.cpp` `renderTranslucentFaces`); the Lich Lab still uses portals ("Glass is clear"). Old `bmodel_world` ODMs: `.render` flag 0x02 (`transcode_mm9_dat_to_odm.py:88,6124`, read `game/outdoor/OutdoorRenderData.cpp:184`, blended pass `OutdoorRenderer.cpp:5060-5175`, texture alpha only, unsorted). Classic ODM BModels: GAP | C: emit `translucent_faces` from this bit; until it lands, cut-outs for bars/fences/ladders/webs (binary alpha), portals for glass between rooms, water to our water shader. E: classic ODM BModels (gap 1) |
| FullyBright 0x20 | not lit; drawn at texture brightness | V | 2,154 / 40. Sky boxes (`SnowMtns_*`, `SeaSky_*`, `Arslegaard*`, `RedSky_*`...), `starfield` 228, `yanmiricenoise` 1,428 (1000 Terrors, Boot Camp), `anskramfloor`/`anskramdoor*` 104 (Anskram Keep movers), `arenapeople*`, `windowlead1` (Hall of the Gods) | glowing class (always); sky via our sky | C: **not** a blanket glow. Sky boxes: our sky. Movers (Anskram's `ExitStairs`, `RoundDoor*`, no LightMap bit): a workaround for unlit movers, which our bake now lights: ignore. Real glow (`yanmiricenoise`, `windowlead1`): glowing class |
| SkyPortal 0x10 | sky shows through | V | 1,919 / 39 (`skymarker.dtx` 1,654 in 35 maps; `greenscreen` 225 in Guberland City, Thjorgard City) | BLV face attribute `IndoorSky` (projected scrolling sky, `IndoorRenderer.cpp:2213-2249`); outdoor: our sky. Lich Lab draws them with MM9's `Clouds1` (`overrides.yml textures`); the indoor bake does not treat `IndoorSky` faces as emitters unless the profile names them | C: sky faces + bake emitter (current dungeon rule) |
| LightMap 0x80 | lightmapped | V | 277,116 / 45 | baked lighting | none (our bake replaces MM9's) |
| Gouraud 0x1000, FlatShade 0x40, Subdivide/NoSubdiv 0x100 | shading and lightmap subdivision hints | V | 523,400; 168 (Lindisfarne); 298,937 | – | none |
| AlwaysLightMap 0x400 | – | V | 7 visible / 1 (Beethoven water) | – | none |
| SkyPan 0x8000 | panning cloud layer overlaid on the surface (cloud shadows) | V name, I look | 1,006 / 1: Lindisfarne buildings (`thjorwoodpanel`, `thjorsidewalk`, roofs) and its `PerceptionBrush*` | GAP (cloud shadows) | none for now; note for weather/cloud-shadow work |
| TimeOfDay 0x100000 | brightness follows the time of day | V name, I look | 4 / 1: Guberland City `Stainedglass` (`fleur-tall`) | surface-material glow `night` (glass glows after dusk, `SURFACE_MATERIALS_PLAN.md` "night glow") | C: glass class |
| Bit 0x4000 | surface texture is a `.spr` (animated) | V (100 % co-occurrence) | 13,014 / 36 | texture frame table, looked up by texture name for BLV and BModel faces (`game/maps/MapAssetLoader.cpp:1236`, playback `IndoorRenderer.cpp:10758-10790`, `OutdoorRenderer.cpp:5133`); liquids matched by texture name in `engine/liquids/liquids.yml` get the water shader instead (`MapAssetLoader.cpp:1242-1246`) | C: water → `liquids.yml` entry; others (`Perception`, `twinkle`, `Thjoradtank`, torch flames) → frame-table rows for the `.spr` frames (data, I: check the table can take world rows) |
| Bit 0x10000 | unknown; set on `Ocean` world models and Dark Passageway terrain (`darksand`, `darkcanyon`) | V | 619 / 12 | – | none (water is rebuilt) |
| Additive 0x80000, Mirror 0x800000, Portal, DirectionalLight, Nonexistent, HullMaker, VisBlocker, TerrainOccluder | – | V | 0 | – | none |
| NotAStep 0x400000 | movement only | V | 72,560 / 16 | collision | none |
| Surface effect `Pan "u v"` | scrolling texture | V | 103 surfaces, 6 maps: Beethoven/Sturmford City slime `WaterTop*` "2 2", Thjorgard City `BlueWater0-3` "1 1", Dark Passageway water "1000 10"/"250 10", Dungeon of Secrets `Clouds1` "1 3", Verhoffin Ruins "5 5" | face attributes `FlowUp/Down/Left/Right`, one fixed speed of 62.5 px/s (`game/FaceEnums.h`, `IndoorRenderer.cpp:2223-2239`, `OutdoorRenderer.cpp:726-745`); `Fluid`/`Lava` ripple | C: nearest flow direction, or our water shader; exact speeds would need a per-face speed (small E) |
| Surface `texture_flags` | copy of the texture's user flags | V | all | – | as user flags |
| Surface `unknown` (0–9+), `unknown2` (0/1/2) | unknown | V | all | – | none |

### C. DAT objects that change how things look

| Property | What | Evidence | Use | OpenYAMM | Carry-over |
| --- | --- | --- | --- | --- | --- |
| Brush `Alpha` (`WorldObject`, `Door`, `RotatingDoor`, `DestructableBrush`, `InvisibleBrush`, `Lift`...) | whole-brush opacity | V | 285 brushes below 1.0 in 14 maps (1000 Terrors 128, Beethoven 58, Wizard's Lab 40, Ruined Temple 32, Lich Lab 14 incl. `Engineglass2-4` 0.5, `skeletondoora/0` 0.8, `MutateWindow0/1` 0.8); `PerceptionBrush` 289 at 0.3–0.75 | BLV `translucent_faces` `opacity` (in progress, above); classic ODM: GAP | C: `opacity` = brush `Alpha` for the brush's Translucent faces |
| `TOD_Sky` `DayAlpha 0 / NightAlpha 1` | starfield brushes that fade in at night | V | 34 objects, 204 `starfield` polys | outdoor sky stars (`level_generation/lighting/SKY_RENDERING.md`, `stars`) | none (our sky) |
| `DemoSkyWorldModel` / `SkyPointer` | sky box geometry | V | 39 / 35 | our sky presets | none |
| `WorldProperties` fog | `EnableFog`, `FogColor`, `FogNearZ/FarZ`, `SkyFog`, `VFog*` | V | fog on in 8 maps (Afterworld, Anskram Keep, Frosgard City, Guberland, Lindisfarne, Sturmford, Thronheim, Yorwick); colour 127 grey in 42; `VFog` 0 in all | outdoor: `environment.fog` distances, `weather.fog_mode` / `authored_fog` with colour (`game/maps/OutdoorSceneYml.cpp:325-430`). Indoor: GAP (no fog term in the BLV face shader; billboard fog 0, `IndoorRenderer.cpp:7856`) | C outdoor; indoor ones (Anskram Keep) wait for indoor fog (gap 5) |
| `Fog` objects | a **point controller, no brush and no volume** (`FogEnable`, `FogColor`, `FogNearZ/FarZ`, `FarZ`, `SkyFogNearZ/FarZ`, `TransitionTime`, `StartOn`, `BackgroundColor`): what the map's fog becomes when it fires. Wired to `WeatherMan.FogOn/FogOff` (or the `Foggy`/`Clear` objects in Thronheim City) | V | 24 objects in 11 maps: Drangheim, Drangheim City, Frosgard, Frosgard City, Lindisfarne, Lindisfarne Monastery, The Arena, Thjorgard, Thjorgard City, Thronheim City, Training Hall. `StartOn 1` (map-wide from the start) in Drangheim, Drangheim City, The Arena, Thjorgard, Thjorgard City, Training Hall: grey 25–4000/4500. Night and clear states: black or 127 grey, `Fog1` at 8000–15000 | indoor: scene `fog` takes the `StartOn` state ([indoor fog](../INDOOR_FOG.md), `Source.fog`); outdoor: `weather` authored fog. Switching: no carrier yet | C: the `StartOn` state; weather switching belongs to the weather work |
| `WorldProperties` `NightLightScale` | night tint of lighting | V | blue-grey (121,133,180) in 14 maps, (134,143,168) in 7; white elsewhere | day/night cycle and sky presets | C: pick a night preset of that tint |
| `WorldProperties` `EnvironmentMap`, `SoftSky`, `PanSky*`, `LightScale` | env map for chrome objects; cloud texture; panning sky (off everywhere); global light scale (255 everywhere) | V | env map named in all 45, but `Chrome` is 0 on all 7,389 props that have it | – | none |
| Volume surfaces (`BlueWater` 70, `ClearWater` 14, `DirtyWater` 6, `CorrosiveFluid` 1) | `ShowSurface`, `SpriteSurfaceName` (`Water115flowing.spr`, `Ocean4.spr`...), `SurfaceAlpha` (mostly 0.7), `SurfaceColor1/2` (tints such as 0,128,64), `FogEnable`/`FogColor`/`FogFarZ` (underwater fog: 0,128,255; 0,64,0) | V | 59 shown surfaces; underwater fog on 15 | water shader for water/tar/lava indoors and outdoors, shallow water translucent (`game/render/WaterRenderer.cpp:524`, `game/shaders/fs_water.sc:240-270`, `fs_indoor_water.sc`); map-wide underwater fog colour (`game/render/SkyState.cpp:163`) | C: water faces → `liquids.yml`; body tint from `SurfaceColor` where the liquid entry takes a colour (I); underwater fog per body when diving lands |
| `Light` | point light: `LightColor`, `OuterColor`, `LightRadius`, `BrightScale` | V | 4,478 (3,953 not white) | BLV point lights + bake (`dungeon/lights.py`, `lighting.py`) | done |
| `DirLight` | spot light: `InnerColor`, `OuterColor`, `FOV`, radius | V | 1,189 (640 at 241,235,154; teal 0,128,128 in Lich Lab) | runtime lights are point lights only (`game/render/lighting/RenderLight.h`); the dungeon converter skips DirLights ("only fed MM9's lightmap bake"); the bake takes extra point lights (`--extra-lights`) | done (2026-10-30): bake-only spots, opt-in per profile (`dirlights: true`, `dungeon/lighting.py`), aim and cone as MM9's preprocessor (`gr_SetupMatrixEuler`: forward = (cos p sin y, -sin p, cos p cos y); rotation 4.71 points **up**, so the Lich Lab's teal `DirLight4-7` at y 0 light the bridges' undersides, not the pod lamps 1024 LT away) |
| `GlowingLight` | animated light: `Color`, `IntensityMin/Max/Freq/Phase`, `RadiusMin/Max`, waveforms | V | 38 (Wizard's Lab 37 coloured: red, green, blue, yellow, violet, white; Lich Lab `Glow1` orange) | flicker/pulse only for outdoor decoration lights, hard-coded `FireFlicker`/`MagicPulse` (`game/outdoor/OutdoorSpatialFxRuntime.cpp:34-38,80-175`); indoor: GAP | C: steady coloured point light now; E (gap 4) |
| `ObjectLight` | lights only objects | V | 100 | actor light grid | none |
| Fire objects (`Fire` 170, `Brazier` 260, `WallTorch` 246, `Torch` 76) | flame/smoke particle parameters, light colours/radii, flicker rate | V | 752 | decoration flames and lights (MM6–MM8 decorations) | P: map to our 3D decoration flames |
| `CClientFX` placements | placed client effects | V | 9 | MM9 effect library (`assets_dev/engine/effects/mm9/`, 48 FXF recipes, `Mm9Native` timing in `game/fx/EffectDefinition.h:208-225`) | C: bind to the effect library |

### D. Placed models (props)

| Property | What | Evidence | Use (of 10,191 objects with a `Filename`) | OpenYAMM | Carry-over |
| --- | --- | --- | --- | --- | --- |
| `Scale` | uniform scale | V | 2,442 not 1.0 (1.5 ×830, 2.0 ×469, 1.2 ×228, 0.75 ×175, 3.0 ×66...) | `decorations.yml` sizes per binding (`height`, `height_jitter`; `game/maps/DecorationModelSet.cpp:641-683`), not per placement | C: one binding (decoration row) per model and scale used |
| `TintColor` | colour multiply (0,0,0 = none) | V | 42: (45,0,0) ×35 Dungeon of Secrets, (0,0,62) ×6 Wizard's Lab, 1 Dook's Castle | no tint key; colour changes go through `variant` (`DecorationModelSet.cpp:683`) | P: a tinted `KHR_materials_variants` variant |
| `Transparent` | `FLAG2` 0x400: draw skin alpha blended | V (object.lto) | 257: `TerrorLight1` 88, `Lamppost4` 35, shelf items 67, `Lantern_Wall1` 16, `Herb-Rack1/2` 16, `OilLamp` 9, tapestries | glTF `BLEND`, static blended batches drawn back to front (`GltfModelLoader.cpp:681-692`, `engine/render/ModelRenderer.cpp:1597,1761`); `extras.openyamm_additive` for glows | P: lamp glass / tapestry edges as a blended mesh part, emission for the flame |
| `Chromakey` | `FLAG2_CHROMAKEY` 0x2: alpha cut-out | V | 465: bushes, trees, herb racks, chairs, flowers, chandeliers | glTF `MASK` + `alphaCutoff` | P: cut-out leaves etc. |
| `Translucency` (fire props) | flame translucency | V | 27 at 0.9 (hanging braziers) | effects / additive flame cards | none |
| `Shadow` | blob shadow | V | 2,726 | sun shadow maps for models (off by default, `ModelRenderer::renderSunShadows`); outdoor blob shadows for actors and projectiles only (`game/outdoor/OutdoorSpatialFxRuntime.cpp:237-345`) | none |
| `Chrome` | environment map | V | 0 of 7,389 | – | none |
| `AnimationSpeed` | | V | 3 at 4.0 | – | C: carry if animated decorations need it |
| `Skin` lists `a.dtx;b.dtx` | one skin per material index | V | trees (`TreeBark2.dtx;TreeBranch3.dtx`) | multi-material GLB | P |

### E. ABC models, skins and sprites

| Property | What | Evidence | Use | OpenYAMM | Carry-over |
| --- | --- | --- | --- | --- | --- |
| Piece `specular_power` / `specular_scale` | Phong specular | V | 5.0 / 1.0 on every piece (2,046): a default | metallic-roughness, normal maps, `extras.openyamm_specular` (`GltfModelLoader.cpp:471,604,698-706`; GGX in `fs_model.sc:70-127`) | none |
| Command `SpecularEnable` | turn specular on | V | 5: `GOBLET`, `POTION1-3`, `SLEEP` spell | metallic-roughness; environment reflection from the sky cubemap outdoors or a neutral room cubemap indoors (`engine/render/ModelEnvironment.h:26-31`) | P: glossy potions and goblet (low roughness) |
| Command `ShadowEnable` (+ size) | projected blob shadow | V | 20 (`PLAYER`, `GOAT`, `DUCK`, `BRAZIER`, tables, `TREE`, `GARGOYLETREE`) | sun shadow maps / outdoor actor blobs (above) | none |
| Command `FadeRangeMin/Max` | fade out with distance | V | 622 models (1000–5000) | LODs / draw distance | none |
| Command `FadeSpriteTex` + `FadeSpriteSize`, `VisRadius` | impostor billboard for far trees | V | 10 trees (`TREE02-06`, `SNOWTREE1/2`, `DEADTREE3/4`, `TREE01B`) | our LODs | none |
| `DrawIndexedDist`, `NoAnimation` | performance hints | V | 32 / 454 | – | none |
| Material index per piece | piece → skin slot (Skin, SkinName2, SkinName3) | V | 44 models use slots 1–2 (weapons, shields, tree branches, liquids) | multi-material GLB | P (already done for creatures) |
| Animation events `HidePiece`/`ShowPiece` | hide or show a piece during a clip | V | 10 models (`PHANTOM`, `LOBBER`, `DOOKMILITIA`, `FIGHTERBASE`, `CHEST1`, spell models) | not found (no clip- or script-driven node visibility in `game/fx/WorldFxSystem.cpp` or `engine/models`) | P: scale the piece's bone to zero in the clip (no engine work), or E (gap 3) |
| Animation events `DoFX n m`, `EndFX`, `PlayAnimFX` | start/stop the monster's FX0–FX2 effect | V | 12 models (`BANSHEE`, `EVILSORCERER`, `GHOUL`, `LICH`, `LICHKING`, `MONK`, `NOSFERATU`, `SKELETONWARRIOR`, `STAGE1/2DEMON`, `YANMIR`, `ZOMBIE`); `EndFX` 60 keys | `actors.yml` animation events: `effect`/`effects` (named effect, sockets, `start`/`end` clip seconds) on every action role and on any `clips`/`script_clips` clip, following the socket; also played by script and cinematic clips (`game/fx/ActorClipEffects.h`, 2026-11-10). `DoFX n` plays FX*n*, 0-based, 0-2 only (`object.lto` `0x1001af90`, record `+0x1a8`); each dots recipe has one emitter on LHand1 and one on RHand1 (FXF `UpdatePos` 2/3, the library's `body_anchor`), and two sockets share one effect's emitters; `ResurrectFX` plays as a corpse rises (`0x1001acf1`) | done 2026-11-10 for every MM9 binding with FX (creature guidelines §7); Monk, Banshee and Zombie `DoFX 1` name empty columns (nothing, as in MM9) |
| Sockets | `RHand1`/`LHand1` (65/42+), `RangeAttack` 35, `Flame`/`FireNode` (torch flames), `Glownode` 3, `Mouth`, `Head`... | V | 843 models | `actors.yml` `animation.sockets`; effect components can follow a model node (`game/fx/EffectSystem.cpp:417,1699`) | P: keep socket names when rigging |
| `.spr` skin | animated skin | V | `NETTLESPORE.spr` 8 frames 7 fps; `BANSHEE.spr` 10 entries 6 fps (skins B–E decaying face, then A) | `extras.openyamm_flipbook [cols, rows, fps]` works on **static** models only (`game/shaders/model_static.sh:33`); skinned shaders apply only `openyamm_uv_scroll` (`vs_model_skinned_instanced.sc:20`). Emission can pulse or flicker (`extras.openyamm_pulse`/`openyamm_flicker`, `GltfModelLoader.cpp:580-600`). The Nettle Spore uses the frame mean (`mm9_jelly_claude/README.md`) | E (gap 2: flipbook in the skinned shaders), or P now: an emissive "nettle" mask with `openyamm_flicker` |
| Skin alpha | per-texel alpha used when the object is `Transparent`/`Chromakey` | V | skins: 108 graded, 83 cut-out, 673 all-zero, 31 opaque | `MASK`/`BLEND` per material; creature blended draws sorted far to near, triangle order kept (`ModelRenderer.cpp:2736,2767-2772`) | P: cut-out for binary, blend for graded (on its own mesh, modelling guidelines) |
| `SPRITES/*.spr` (133) | effect flipbooks (fps 4–15) | V | spells, fire, smoke, water | effect sprites packed into atlases and played by fps, alpha/additive/multiply blend (`game/fx/EffectRenderer.cpp:31-35,319,736`, `EffectDefinition.h:41-46`) | through the MM9 effect library |

### F. Monster and actor tables, scripts, ClientFX

| Property | What | Evidence | Use | OpenYAMM | Carry-over |
| --- | --- | --- | --- | --- | --- |
| `MONSTERS.txt` `Transparent` | skin alpha on (finding 4) | V column, I semantics | 30 of 270 rows (Prisoners, Dragonflies, Ghosts, Dagrells, Winged Mutants, Banshees, Jellyspores, Sea Monsters, Liches, Dragon King, Fish, Greater Demon, Rooster) | glTF `MASK`/`BLEND` per material; whole-actor see-through only through a `BLEND` variant material (Spectre Dagrell). No whole-actor opacity: `ModelInstanceSystem::setCoverage` is a dither that reaches only stand-ins and attachments (`engine/models/ModelInstance.cpp:364`) | P: check every creature brief: cut-out/soft edges from the skin alpha; whole-body see-through only by user decision |
| `Scale` | size multiplier | V | 33 rows not 1 (0.4–3.0) | tier scale (`CREATURE_POSTPROCESS.md`) | P: already used |
| `SkinName`, `SkinName2`, `SkinName3` | body skin and the weapon/shield slots | V | 46 rows with a 2nd skin, 12 with a 3rd | tier variants and attachments | P: done per creature |
| `FX0`–`FX2` | ClientFX on the actor: `bluedots` 12, `greenyeldots` 13, `redyeldots` 7, `LichKingRes` 1 | V | 27 rows (monks, sorcerers, banshees, ghouls, zombies, vampires, liches) | MM9 effect library has them (2026-11-10: `mm9:redyeldots` and `mm9:LichKingRes` too; hand-anchored emitters fall back to the effect's origin, `body_anchor` names the node); actors have charge sockets with per-event effects and `ambient_effect` (`WorldFxSystem.cpp:642,1061-1105`) | P/C: author an MM6–MM8-style hand effect per colour, or resolve the library's hand anchors to the actor's sockets (small E in the effect binding) |
| `ResurrectFX` | `GreaterDemon` (smoke, skull, green-yellow star sprites) | V | 15 rows | MM9 effect library (`mm9:GreaterDemon`) | P: play on resurrect |
| `HeadTurn` | head tracking | V | 204 rows | – | none (animation) |
| Tint column | none exists | V | – | – | – |
| Scripts: `SetModelFilenames` | model/skin swap | V | 26 calls (Ebora's `Siren1-4` skins, `succubusredgstrng`, `ColloidalWarrior` → `Shockwave`, barrels breaking, gibs) | decorations switch model through event `SetSprite` (a map loads only models its placements or scripts name literally); actor variant switch not found | C per case; actor skin swaps wait for gap 3 or become separate actors |
| Scripts: `DoClientFX` / `CacheClientFX` / `CreateFX` | spawn ClientFX | V | 69 / 70 / 1 | MM9 effect library + Lua effects | C: port per script |
| Scripts: `setflag`/`clearflag` visible | show/hide | V | 513 flag lines, 225 of them on `visible`/`FLAG_VISIBLE` | Lua show/hide | C |
| Banshee skins (`object.lto`) | `skins\BansheeE..A.dtx` listed in the Banshee class; `Banshee.scr` sets `Undead` on melee (`GoUndead`) | V list, I trigger | 3 monster rows | not found: variants are chosen per descriptor (`actors.yml` `skin:`), no runtime switch | E (gap 3), or P: bake the decay into the attack clip as an emission/flicker change |

## How the reported losses come about

| Loss | Cause in the data | Fix |
| --- | --- | --- |
| Lich Lab frosted glass | `Lichwindow.dtx` (pale blue, alpha mean 119) × brush `Alpha` 0.7/0.8 on 60 translucent polygons | done: the panes are BLV `translucent_faces` (`opacity` 0.7/0.8, two-sided) |
| Teal crown | `YANMIRSOLIDICE1` glass (blue, alpha 191; brush `Alpha` 0.5–0.6; fullbright; `LIGHTDEFS` teal) tints the view and its light bakes into the walls | C now: LIGHTDEFS emitter in the bake profile; with `translucent_faces`: the pod and crown glass at `opacity` 0.5/0.6 plus the glowing class |
| Opaque `Transparent 1` monsters | the flag only enables skin alpha; skins are mostly opaque | P: cut-outs and soft edges from the skin alpha; see-through only for the three spectral monsters (user decision) |
| Nettle Spore single frame | `NettleSpore.spr`, 8 frames at 7 fps on a skinned creature | P now: emissive nettle mask with `openyamm_flicker`; E gap 2 for the real frames |
| Green pod lamps | teal `LIGHTDEFS` light of the pod glass in MM9's lightmap on a yellow texture | done: per-polygon texture lights (`texture_lights` in the bake profile); a light at the brush's centre is shut in by the pod. The teal `DirLight4-7` do not reach them: 1024 LT from the engine, radius 700, aimed up |

**Correction (2026-10-30): the "white mist" in the Lich Lab's halls was never MM9's.** It came from how we took the
reference, not from the game's data. The review sheets' "MM9 original" is the old `bmodel_world` import drawn by our
outdoor renderer, with `view_distance_scale: 0.4` (written by `transcode_mm9_dat_to_odm.py` for enclosed maps and
cities): a far clip of 16192 × 0.4 = 6477 native, 2530 LT. `skyFogRatio` fades geometry into the Enhanced sky from 55 %
of that, and past the clip the sky itself shows. MM9's own `FarZ` is 100000 and `LICHLAB` has `EnableFog 0`, `SkyFog 0`,
`VFog 0` and no fog volume. Lifting only the view limit (`--set video.view_distance=unlimited`) removes the mist and
shows the bronze hall: cross hall 99.8 → 33.8, engine hall 80.5 → 33.6 (sheet
`level_generation/projects/mm9r_lichlab/review/mist_probe_farclip_compare.jpg`). Reference runs now always use that
setting (`level_generation/projects/mm9r_common/DUNGEON_PLAYBOOK.md`). It reached Lich Lab views (18 of 40) and some
of Anskram Keep's (12 of 30, by up to 9), not the Temple of Honk's. Any other map whose scene has
`view_distance_scale: 0.4` (17 in all) or whose long views pass 8905 native may show the same fade in an old reference.

## Engine gaps, ranked by visual payoff across the rework

1. **Translucent faces: finish the BLV feature and give classic ODM BModels the same.** 15,021 visible translucent
   polygons in 44 maps: glass in every town and dungeon, indoor water until diving replaces it, webs, chain-link,
   ladders, the night starfield, the Lich Lab. BLV: in progress, uncommitted (2026-10-30: scene `translucent_faces`,
   `opacity` × texture alpha × `tint`, sorted, two-sided option); still to settle there: the bake (does a translucent
   pane pass light and colour it?) and `devdocs/INDOOR_TRANSLUCENT_FACES.md`, which the code cites but does not exist
   yet. Outdoor: remade maps are classic ODMs, whose BModels have no translucent pass; the `bmodel_world` pass exists
   but has no opacity, tint or sorting. Size: **small-medium** for the ODM side (reuse the BLV face record and the
   `bmodel_world` pass), BLV remainder small.
2. **Flipbook textures on skinned creatures: done (2026-11-04).** `extras.openyamm_flipbook` now animates creature
   materials too: `ModelRenderer::bindTextureScroll` picks the frame at the creature clock (every creature of a material
   in step) and `vs_model`/`vs_model_skinned_instanced` map the texture to that cell. For the Nettle Spore's 8 frames
   (and, as a skin sequence, the Banshee): pack the frames as an atlas and set the extra on the material.
3. **Switching a model's variant or hiding a node at run time** (Banshee decay skins B–E, Ebora's `Siren1-4` and other
   `SetModelFilenames` swaps on actors, `HidePiece`/`ShowPiece` animation keys on 10 models). Size: **small-medium**: a
   Lua call and an animation-event action that select a `KHR_materials_variants` variant or toggle a mesh node.
4. **Animated lights indoors: done (2026-11-04)** for MM9's `GlowingLight` (38 objects, 37 of them the Wizard's
   Lab's coloured pulsing lights): scene `pulsing_lights`, sine intensity and radius ([indoor pulsing
   lights](../INDOOR_PULSING_LIGHTS.md)); MM9's other waveforms are drawn as sines.
5. **Indoor fog: done (2026-10-30).** Scene `fog`, [indoor fog](../INDOOR_FOG.md): Anskram Keep's black fade, and the
   `StartOn` state of a `Fog` controller for any other indoor map. Still open: water volumes' fog while diving (the only
   real regions, waiting for diving) and `WeatherMan` switching.
6. **Emitters in the outdoor bake.** `TEMPGLOWICE` (cyan, Frosgard and Frosgard City) and any outdoor `LIGHTDEFS` or
   lamp need the outdoor bake to take area or point lights; it has sun and sky only. Size: **small** (the indoor bake's
   emitter code).
7. **Per-face scroll speed.** MM9 `Pan` speeds range from "1 1" to "1000 10"; native flow attributes have one speed.
   Size: **small**, low payoff (most panning surfaces are water, which our water shader replaces).
8. **Cloud shadows (`SkyPan`)** on Lindisfarne's buildings, 1,006 polygons. Size: medium, low priority; belongs to the
   weather/sky work.

Not gaps (converter work only, below): LIGHTDEFS indoors (bake `emitters` take a flat colour per texture), DirLights
(bake extra lights), fullbright (glowing class, model emission), cut-outs (face and model alpha test), per-placement
scale and tint (one decoration binding or variant per value).

## Converter and pipeline changes that need no engine work

Ready now:

- **LIGHTDEFS → indoor bake emitters** (dungeon `lighting.py` profile): one emitter per `LIGHTDEFS` texture with its
  colour and a strength fitted to its radius. Lich Lab (teal crown, green pod lamps), Yanmir's Fort, Connecting
  Tunnels. Outdoor Frosgard waits for gap 6.
- **`DirLight` → bake-only lights**: done, `dirlights: true` in a map's bake profile (`dungeon/lighting.py`); 1,189
  objects. A map turns it on when it next calibrates.
- **`DTX_FULLBRITE` → glowing class with the alpha as mask** in the surface-material class map, and as an emissive
  texture on the StatStone prop. `SURF_FULLYBRIGHT` → glowing class only where it is not a sky box or an unlit mover:
  `yanmiricenoise` (1000 Terrors, Boot Camp), `windowlead1` (Hall of the Gods), `arenapeople*` (The Arena).
- **User flag → surface-material class pre-label**: 15 glass, 16 liquid, 8/9 iron or bright metal, 10/11 wood, 19
  cloth, 13/14/21 earth, foliage, snow. Saves a class-map review step per texture.
- **Cut-out textures as cut-outs**: binary-alpha world textures (`PREFER5551`, or under 2 % partly transparent texels:
  bars, fences, ladders, grills, `ChainLink`, webs) keep their alpha in the converted bitmap; BLV faces discard at
  alpha ≤ 0.001 and BModels at ≤ 0.1. Check that the dungeon converter's texture path keeps the alpha.
- **Water**: MM9 water textures (`water123`, `Water115`, `water125`, `Ocean*`, `slime`) → `engine/liquids/liquids.yml`
  entries so the water shader draws them; `SurfaceColor1/2` as the body's tint where the entry takes a colour.
- **Other `.spr` surfaces** (`Perception`, `twinkle1-3`, `Thjoradtank`, torch flames): texture frame table rows from
  the `.spr` frame list and fps (I: check the frame table accepts world-package rows; else the first frame, as now).
- **Transparent/Chromakey props and monsters** (creature and decoration pipeline): `Chromakey` and 1-bit skins → glTF
  `MASK`; `Transparent` graded skins → `BLEND` on a separate mesh part (lamp glass, tapestry fringes, feathers, fins,
  wing membranes). Check the 30 `Transparent 1` monster rows in every creature brief.
- **Spectral see-through** (user decision): Banshee and Ghost the Spectre Dagrell way (`mm9_dagrell_claude/README.md`:
  `BLEND` variant material, opaque shadow LODs).
- **Nettle Spore stand-in**: an emissive mask of the white nettle pattern with `extras.openyamm_flicker` (or
  `openyamm_pulse`) until gap 2.
- **Monster FX0–FX2 and ResurrectFX**: per-event charge-socket effects on `LHand1`/`RHand1` (`actors.yml`
  `effects`) for the `bluedots`/`greenyeldots`/`redyeldots` hand sparkles at the `DoFX` keys; `GreaterDemon` on
  resurrect.
- **Props**: `Scale` (2,442 placements) as one decoration binding per model and scale; `TintColor` (42) as a tinted
  variant; `SpecularEnable` potions and goblet glossy.
- **Per-map fog and night tint (outdoor)**: `WorldProperties` fog (outdoor maps among the 8) and `NightLightScale`
  (21 maps) into the map's fog settings and sky preset.

Ready when the in-progress BLV translucency lands (converter only): every Translucent DAT surface → a
`translucent_faces` entry with `opacity` = its brush `Alpha` (1.0 for main-world surfaces), `two_sided` for panes,
`tint` white (the texture carries the colour); the Lich Lab's 44 portal panes and 11 opaque panes become real glass.

Need an engine feature first: translucent BModel faces in classic ODMs, flipbooks on skinned creatures, run-time
variant and node switching, indoor animated lights, outdoor bake emitters.

## Rule for the rework

Carry over MM9's visual properties: match or gain, lose nothing silently. Every converter (dungeon, outdoor, props)
and every creature or decoration brief checks, for its textures, skins and objects: the DTX flags (`FULLBRITE`,
`PREFER4444`/`5551`), the DTX user flag (surface type), `LIGHTDEFS` sections, `.spr` animation, the DAT surface flags
(Translucent, FullyBright, SkyPortal, SkyPan, TimeOfDay, bit 0x4000) and surface `Pan` effects, the brush `Alpha`,
prop `Scale`/`TintColor`/`Transparent`/`Chromakey`, `MONSTERS.txt` `Transparent`/`Scale`/`FX0-2`/`ResurrectFX`, ABC
`SpecularEnable` and `HidePiece`/`DoFX` keys, and the map's `Light`, `DirLight`, `GlowingLight`, fog and volume
objects. Each property is either mapped (table above), deliberately replaced by our own system (sky, water, bake,
LODs; say so in the project README), or recorded as a deviation with the engine gap it waits for. The converter's
summary (`work/*.json` or README) lists counts of each property it met and what it did with them.

## Per-map counts

Visible polygons unless noted. `transl` Translucent surfaces; `alpha<1` brushes with `Alpha` below 1 (not
`PerceptionBrush`); `bright` FullyBright (sky boxes give 12–18 per map); `spr` animated-texture polygons; `pan` surfaces
with a `Pan` effect; `ldefs` polygons with a LIGHTDEFS texture; `glass` polygons with user flag 15; props with
`Transparent`, `Chromakey`, `Scale` not 1, `TintColor` set; `glow` GlowingLights; `dir` DirLights; `fog` WorldProperties
`EnableFog` (not the `Fog` controllers: table C).

| Map | transl | alpha<1 | bright | spr | pan | ldefs | glass | transp. | chroma | scale | tint | glow | dir | fog |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1000TERRORS | 9926 | 128 | 1417 | 9867 | 0 | 0 | 54 | 89 | 0 | 184 | 0 | 0 | 81 | 0 |
| AFTERWORLD | 6 | 0 | 18 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 0 | 0 | 0 | 1 |
| ANSKRAMKEEP | 12 | 0 | 104 | 12 | 0 | 0 | 0 | 0 | 0 | 67 | 0 | 0 | 408 | 1 |
| ARSLEGARDCITY | 119 | 0 | 12 | 4 | 0 | 0 | 25 | 13 | 42 | 137 | 0 | 0 | 0 | 0 |
| BATHHOUSE | 9 | 0 | 13 | 0 | 0 | 0 | 2 | 0 | 0 | 54 | 0 | 0 | 20 | 0 |
| BEETHOVEN | 291 | 58 | 0 | 153 | 16 | 0 | 0 | 0 | 1 | 19 | 0 | 0 | 21 | 0 |
| BOOTCAMP | 383 | 3 | 42 | 195 | 0 | 0 | 127 | 0 | 26 | 60 | 0 | 0 | 50 | 0 |
| CHASMOFTHEDEAD | 53 | 0 | 13 | 27 | 0 | 0 | 0 | 0 | 0 | 80 | 0 | 0 | 0 | 0 |
| CONNECTINGTUNNELS | 0 | 0 | 0 | 0 | 0 | 8 | 8 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| DARKPASSAGEWAY | 88 | 0 | 12 | 72 | 2 | 0 | 0 | 6 | 76 | 87 | 0 | 0 | 11 | 0 |
| DOOKSCASTLE | 4 | 0 | 0 | 0 | 0 | 0 | 15 | 0 | 0 | 39 | 1 | 0 | 7 | 0 |
| DRAGONSTADIUM | 6 | 0 | 13 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| DRANGHEIM | 99 | 0 | 18 | 47 | 0 | 0 | 84 | 1 | 0 | 11 | 0 | 0 | 0 | 0 |
| DRANGHEIMCITY | 181 | 0 | 18 | 85 | 0 | 0 | 37 | 10 | 9 | 44 | 0 | 0 | 1 | 0 |
| DRANGHEIMPRISON | 37 | 0 | 0 | 13 | 0 | 0 | 0 | 0 | 0 | 104 | 0 | 0 | 3 | 0 |
| DUNGEONOFSECRETS | 129 | 0 | 13 | 122 | 1 | 0 | 0 | 0 | 0 | 21 | 35 | 0 | 1 | 0 |
| FROSGARD | 29 | 1 | 18 | 15 | 0 | 32 | 18 | 0 | 29 | 38 | 0 | 0 | 0 | 0 |
| FROSGARDCITY | 71 | 1 | 13 | 40 | 0 | 32 | 151 | 4 | 16 | 54 | 0 | 0 | 0 | 1 |
| GREATGATE | 6 | 0 | 13 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| GUBERLAND | 50 | 0 | 13 | 44 | 0 | 0 | 5 | 0 | 0 | 34 | 0 | 0 | 0 | 1 |
| GUBERLANDCITY | 118 | 1 | 13 | 28 | 0 | 0 | 147 | 12 | 27 | 105 | 0 | 0 | 0 | 0 |
| HALLOFTHEGODS | 27 | 0 | 31 | 2 | 0 | 0 | 15 | 0 | 0 | 53 | 0 | 0 | 31 | 0 |
| INVENTASTORCA | 91 | 0 | 18 | 78 | 0 | 0 | 0 | 0 | 0 | 11 | 0 | 0 | 185 | 0 |
| ISLEOFASHES | 41 | 0 | 18 | 35 | 0 | 0 | 0 | 0 | 0 | 24 | 0 | 0 | 0 | 0 |
| KLUSOSHOUSE | 19 | 0 | 13 | 0 | 0 | 0 | 1 | 0 | 0 | 22 | 0 | 0 | 0 | 0 |
| LICHLAB | 149 | 14 | 13 | 20 | 0 | 37 | 60 | 0 | 14 | 57 | 0 | 1 | 36 | 0 |
| LINDISFARNE | 96 | 1 | 13 | 70 | 0 | 0 | 208 | 11 | 13 | 73 | 0 | 0 | 0 | 1 |
| LINDISFARNEMONASTERY | 78 | 0 | 13 | 29 | 0 | 0 | 300 | 0 | 0 | 8 | 0 | 0 | 264 | 0 |
| MOUNTAINPASS | 6 | 0 | 13 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 27 | 0 |
| RUINEDTEMPLE | 278 | 32 | 13 | 60 | 0 | 0 | 22 | 6 | 0 | 7 | 0 | 0 | 0 | 0 |
| STURMFORD | 67 | 0 | 18 | 52 | 0 | 0 | 0 | 4 | 63 | 21 | 0 | 0 | 0 | 1 |
| STURMFORDCITY | 228 | 0 | 13 | 98 | 7 | 0 | 68 | 49 | 54 | 72 | 0 | 0 | 18 | 0 |
| TASARACADEMY | 71 | 0 | 18 | 6 | 0 | 0 | 12 | 1 | 1 | 36 | 0 | 0 | 4 | 0 |
| TEMPLEOFHONK | 29 | 0 | 18 | 1 | 0 | 0 | 20 | 0 | 1 | 39 | 0 | 0 | 1 | 0 |
| THEARENA | 62 | 0 | 61 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| THJORADMINE | 17 | 0 | 0 | 117 | 0 | 0 | 0 | 5 | 0 | 58 | 0 | 0 | 0 | 0 |
| THJORGARD | 67 | 2 | 13 | 55 | 0 | 0 | 16 | 0 | 18 | 85 | 0 | 0 | 0 | 0 |
| THJORGARDCITY | 344 | 4 | 13 | 102 | 4 | 0 | 141 | 13 | 33 | 244 | 0 | 0 | 0 | 0 |
| THRONHEIM | 47 | 1 | 13 | 40 | 0 | 0 | 1 | 4 | 0 | 23 | 0 | 0 | 0 | 1 |
| THRONHEIMCITY | 155 | 0 | 13 | 35 | 0 | 0 | 31 | 5 | 24 | 122 | 0 | 0 | 0 | 0 |
| TRAININGHALL | 50 | 0 | 13 | 22 | 0 | 0 | 4 | 0 | 0 | 4 | 0 | 0 | 16 | 0 |
| VERHOFFINRUINS | 52 | 5 | 18 | 10 | 1 | 0 | 8 | 3 | 2 | 2 | 0 | 0 | 3 | 0 |
| WIZARDSLAB | 1363 | 40 | 12 | 1400 | 0 | 0 | 0 | 16 | 0 | 137 | 6 | 37 | 1 | 0 |
| YANMIRSFORT | 15 | 0 | 10 | 17 | 0 | 610 | 0 | 0 | 0 | 91 | 0 | 0 | 0 | 0 |
| YORWICK | 52 | 0 | 13 | 41 | 0 | 0 | 39 | 5 | 16 | 58 | 0 | 0 | 0 | 1 |

## Open questions

- **All-zero skin alpha with `Transparent 1`** (Jellyspore, Dragonfly, Spectre Dagrell, Prisoners): the data cannot say
  whether MM9 draws these opaque (alpha treated as absent, as for the 673 opaque monsters with all-zero alpha) or
  applies an object alpha in code. Original-game footage settles it; the user's see-through decision stands either way.
- **What the five Banshee skins do in game**: listed in `object.lto` and in `BANSHEE.spr`; the trigger is not in the
  scripts (inferred: the "undead" phase `Banshee.scr` enters on a melee attack).
- **Bit 0x10000** on ocean and Dark Passageway terrain surfaces, the surface `unknown` fields and `FLAG2` 0x400's
  LithTech name: not needed for the carry-over above.
- **Untranslucent alpha textures**: 41 world textures with graded alpha have no 4444 flag and many alpha textures sit on
  surfaces without the Translucent bit (`yanmiricewall2h256` 1,919 polygons, `stonewindow` 749, half of `ChainLink`).
  Inferred: MM9 draws those opaque (alpha ignored without the bit); worth a look in original footage before giving
  them alpha.
