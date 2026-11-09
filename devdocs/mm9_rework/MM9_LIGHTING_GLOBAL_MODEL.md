# MM9 dungeon lighting: one global model (2026-10-31)

This document asks why our rebuilt MM9 dungeons differ in brightness and hue from real MM9 screenshots, and what single
rule fixes that for every map. It is investigation only: nothing was changed in the engine, the shaders, the converter,
the bakes or the review root. The renderer reverse engineering it builds on is in
[MM9 render lighting](MM9_RENDER_LIGHTING_RE.md). The shot-by-shot test data is in
[real-shot measurements](overnight/real_mm9/MEASUREMENTS.md).

## Answer in short

1. **MM9 draws a lightmapped wall as `texture × lightmap / 255`**, per channel, on the 8-bit values (display space).
   There is no multiplier, no gamma and no brightness term. A **controlled capture of real MM9 under Wine** (Boot Camp,
   new game, default settings) matches this to within 5 % on the whole view (61.1 real against 61.4–64.7 predicted,
   depending on the pose) and matches the hue. The ×2 (`Saturate`) path and "lightmap bytes treated as linear light"
   are both ruled out, by about 2× and by about 1.3× (table below).
2. **Our shaders already do the same thing.** The indoor shader multiplies the texture's display bytes by the lighting
   value (no sRGB sampling, no sRGB target, no tonemap). The surface-material path raises both factors to 2.2 and takes
   the 1/2.2 root of the product, which gives back the same product. Our MM9 textures have the same mean as the DTX
   texels (339 textures in five maps, mean difference 0). **So the colour space is not the cause.**
3. **The cause is the bake.** Each map's Cycles bake rebuilds the lightmaps from MM9's light objects, using per-map
   factors (`direct_scale` 0.7–2.6, `bounce_scale` 1–6, `ambient_scale` 0.2–1.19, `max_lighting` 1–1.4) and a bounce
   term that MM9 does not have. Against MM9's own DAT lightmaps, zone by zone, our bake runs at 0.56–1.66×, and its
   hue drifts both ways ("too neutral" ×0.6, "too saturated" ×2.1). No single factor fixes that.
4. **Most of the remaining spread in the YouTube shots comes from the shots themselves, not from MM9's renderer:**
   - **Dungeon of Secrets 4 (3.77×):** the Torch Light spell is on. Its icon shows on the HUD, a hand with a torch left
     of the compass, and it shows in none of the other shots.
   - **Dragon Stadium (2.0×):** a uniform ×2 on floor and wall alike. That fits a capture or `Saturate` gain in that
     player's setup. No added light could fit both surfaces.
   - **Klusos House (1.44–1.66×):** MM9 lights the walls near its wall torches dynamically.
   - **Yanmir's Fort 1 (1.00×):** no light source near the camera, and an exact match.
5. **`PlayerLightOn` is not a global brightener.** It switches a client light of grey (191,191,191) and radius
   **36 LT**. The Torch Light spell reuses the same light at radius = power × 12 LT for its duration.

**Global rule, recommended:** a wall's static light is MM9's own DAT lightmap texel ÷ 255, resampled onto our faces.
Dynamic sources (fires, torches, candles, light FX) add on top at runtime, within `DynamicLightDist` of the camera.
There is no per-map factor. Models keep the model formula in the RE document. A one-time global Cycles recipe covers
only faces that have no DAT polygon.

## 1. The open points, closed or narrowed

### 1.1 `PlayerLightOn`: a tiny grey light, which the Torch Light spell enlarges (proven, except its position)

- **Server** (`object.lto`): `0x100c3cf4` sends `PlayerLightOn` (byte `0x101aa170`) to the client as message `0x19`
  (one byte, through the send helper `0x100d8970`). `0x100c2f85` also copies it into byte `+0x1c` of the player-info
  struct, which it sends as message `0x45` (vtable `0x10183a4c`, position at `+0x10..0x18`).
- **Client** (`cshell.dll`): `0x100999d0` deserialises that struct (vtable `0x100c9530`). It stores the position at
  `+0x1574..0x157c` and calls `light->SetOn(byte +0x1c)` (`0x10096950` → flag bit 0 = `FLAG_VISIBLE`).
- **The light** (class at `0x100967d0`, owned at `+0x40` of the party object, created at `0x10096bab`):
  - an `OT_LIGHT` (`ObjectCreateStruct` type 4) with flags `0x41`;
  - colour `SetLightColor(0.75, 0.75, 0.75)`, which is **(191,191,191)** (`0x1009691f`);
  - radius **36.0** (`0x100969a0`, constant `0x42100000`).
- **Torch Light spell** (`0x10080e30`):
  - `light->Activate(expiry = now + [fx+0x50], radius = byte [fx+0x70] × 12.0)` (`0x100969c0`; constant
    `0x100c5888` = 12.0);
  - the update at `0x100969f0` resets the radius to 36 and switches the light **off** once the game time passes the
    expiry.
  - The HUD shows `TorchLightAnim.pcx` at (642, 25) in 800×600 while the spell is active (`HUDCOORDS.txt`).
- **Still open:** no code in `cshell` was found that moves this light. Searches for its handle feeding
  `SetObjectPos` (`+0x118`) and for its virtual `SetPos` came up empty. It presumably follows the camera, but not
  through a path that could be traced.
- **Effect:**
  - with `PlayerLightOn 1` alone, a 36 LT light at the eye barely reaches a wall (the party stands about 24 LT or more
    from walls), so it is immaterial;
  - Torch Light makes it a grey light of radius 12 × power LT, which explains Dungeon of Secrets 4.
  - Our Torch Light (`GameplayTorchLight.h`: 800 × power native, #606060) is the MM6–MM8 rule and is shared gameplay.
    Leave it alone.

### 1.2 Dynamic lights on the world (partly traced)

- **Selection** (`d3d.ren` `0x10026580`): every light object goes into the frame's visible-light list (`ctx+0x244`,
  count `+0x248`) when `DynamicLight` (`0x100902d0`) is on **and** its distance to the camera is at most
  `DynamicLightDist` (`0x100902d4`; default 1500, worlds 1500–2500).
- **Per light** (`0x100269d0`):
  - if the object's flag `0x20` is clear, the light is added to the model list `0x10094074/78` (at most 40);
  - if flag `0x80` is clear, the world BSP is queried in the light's box (position ± radius `+0x188`), and world
    models (type 2) inside it get the light (`0x100269b0` → `0x10026658`, transformed into model space).
- **World-polygon vertex term** (`0x1004c170`). For each light linked to a polygon (`[poly+0x2c]`), using the colour
  bytes `c` at `+0x94..0x96`:
  - The polygon is skipped unless `|plane distance| < r`.
  - Each vertex with `d < r` gets `w = 1 - d/r`: **linear falloff, no N·L**.
  - The vertex colour byte becomes `old + int(K × w)`, then is clamped to 0..255. The FPU sequence (`0x1004c231`,
    `DE E8+i` = `FSUBP`) decodes as `K = 2c - 255`, so a light colour below 128 darkens. The sum is doubled when
    `Saturate` is 1.
  - **Open:** this is decoded from a single listing. Which polygons go through this vertex path is not proven
    either: the Gouraud (vertex-lit) world polygons certainly do, and the lightmapped ones may not (see 1.3).
- **The `ONE/ONE` world pass** at `0x10041fc0/0x10042043` is **not** the dynamic-light pass, as the RE document
  inferred. It sets `SRCBLEND = DESTBLEND = ONE` and a black fog colour only when the drawn object's flag `0x10` at
  `+0x238` is set, so it is the per-object additive mode (additive world models and sprites).
- **Which MM9 objects make dynamic lights** (the class definitions in `object.lto`):
  - `Fire` (`LightMinRadius`, `LightMaxRadius`, `LightColor1/2`, `FlickerRate`, `LightPolyBack`);
  - `WallTorch`, `Torch` (`LightRadius`, default 200), `CandleProp`, `Brazier`;
  - `LightFX` and its waveforms (`FlickerLight`, `GlowingLight`, `SineWaveLightFX`, ...), with `OnlyLightWorldFlag`,
    `DontLightBackfacingFlag` and `SolidLightFlag`;
  - `PerceptionLight`.
  - Class `Light`, `DirLight` and `ObjectLight` objects are static. They are in the lightmaps (or, for models, in the
    light table and the static lights), not in this list.
- **Evidence that dynamic lights brighten walls:**
  - Klusos House reads 1.44–1.66× its lightmaps, with `WallTorch`/`CandleProp` objects 89–271 LT from the eye.
  - Yanmir 1 has nothing within 840 LT and reads 1.00×.
  - **The size of the effect is not measured.** The user's Wine shot B (`DynamicLight 0`) would give it.
    `DynamicLight` and `DynamicLightDist` are plain cvars.

### 1.3 Vertex diffuse of lightmapped world polygons: white (proven by measurement; code partly)

- The world vertex writer picks its colour function from a table at `0x10090648`, indexed by the draw mode
  `[mode+0x10]`:
  - mode 0: `0x1004c060` writes `0xFFFFFFFF` (**white**);
  - mode 1: `0x1004c080` copies the vertex's stored colour through the identity LUT (Gouraud polygons);
  - mode 2: `0x1004c0d0` scales the vertex's colour by a per-model tint (`+0x7a0..0x7a8`).
- Which mode lightmapped polygons use was not traced to its setter.
- **The Wine capture settles it:** walls, ceiling and the whole view match `texture × lightmap` ×1 within 5 %. Any
  diffuse below white would have darkened them, so on a lightmapped polygon the vertex diffuse is white.

### 1.4 Detail textures and the GOG `ddraw.dll` (closed)

- **Detail textures** add with `ADDSIGNED` (`tex + detail - 0.5`). The 12 detail DTXs average 104–141 (most
  126–141; `DET_04` 129.6), so the mean shift is at most ±0.1 and usually under ±0.05. Clipping at 0 on dark textures
  lifts their mean slightly. Detail textures add contrast, not ×2.
- **The GOG wrapper** (`dxcfg.ini` `gamma=1.0`, which translates D3D7 to a newer D3D) leaves the frame at `T × L`: the
  Wine capture ran through it with default settings and matches ×1.
- **`Brightness`** (`autoexec.cfg` 1.0): `cshell` multiplies the light scale by it, and `d3d.ren` turns that into an
  identity LUT. It has no effect at any value (see the RE document, section 2).

### 1.5 Our colour handling (closed)

- **Indoor faces** (`game/shaders/fs_indoor_textured_lit.sc`):
  - `color = texture.rgb × clamp(static + dynamic, 0, 2)`;
  - with a bake, `static = RGBM4(lightmap)`, the sidecar value as stored;
  - the texture is sampled without `BGFX_TEXTURE_SRGB` (only `ModelRenderer` uses sRGB), and the back buffer is not
    sRGB, so this is a display-space product, the same as MM9's.
  - The surface-material variant computes `pow(T, 2.2) × pow(L, 2.2)` and then takes `pow(…, 1/2.2)`. That is again
    `T × L`, plus small occlusion and specular terms.
  - Cinematic grading is off by default (`GameSettings.cpp:484`), and bloom only spreads emitter glow.
- **The bake** (`tools/lighting/bake_indoor.py`):
  - Cycles is driven with emission colour = authored colour/255 and the window `(1 - d²/r²)²`;
  - its direct term is therefore a linear sum of display-byte colours, which is what MM9's preprocessor sums as well,
    so there is no colour-space mismatch in the direct light;
  - the **bounce** uses the textures' **linear** (sRGB-decoded) mean albedo (`texture_albedo`). It is weak at about
    0.15 albedo, which is why `bounce_scale` reaches 6, and its hue is the texture's in linear terms. MM9's lightmaps
    have no bounce at all.
  - The sidecar is RGBM4, the same units as the shader multiplier.
- **For a texel T and an MM9 lightmap texel L:**
  - MM9 shows `T·L/255`;
  - we show `T × ours`, where `ours` is our bake at that point;
  - when `ours = L/255` the pixels are identical.
  - **The difference is entirely `ours / (L/255)`**: 0.56–1.66 zone by zone, and 1.0–1.5 on screen once our runtime
    extras are counted (the next point).
- **Our runtime extras** add on top of the bake:
  - decoration light emitters and torches in the light grid;
  - props, actors, emitter glow and bloom inside the measured box;
  - the lighting clamp, which is 2 for us; MM9 clips the lightmap at 1, and its dynamic term clamps at 255.
- Yanmir 1 is 1.40× on screen against a zone bake ratio of about 1.16, so about 1.2× comes from these runtime extras.
  To split them per map, capture once with dynamic lights and actors hidden (a debug toggle), which is part of
  change 1 below.

## 2. The global model

```
wall (lightmapped world polygon), per channel, 8-bit display values:
  pixel = clamp( T · (L_DAT / 255)            static: MM9's own lightmap, x1, no gamma
                 + T · Σ_dyn K(c) · (1 - d/r) / 255 ? )   dynamic Fire/Torch/Candle/LightFX within
                                                          DynamicLightDist (form and placement not proven, 1.2)
         )
  + Torch Light spell: one more dynamic light, grey 191, r = 12 × power LT, at the party
  PlayerLightOn: grey 191, r = 36 LT (no visible effect)
  detail texture: ± contrast only; Brightness / LightScale / Gamma: none

models (props, characters): as in MM9_RENDER_LIGHTING_RE.md section 3
  (AmbientLight light table + full-colour lights × (1 - d²/r²) × N·L + ModelAdd 30, clamp 255)
```

### Check against every real shot

The prediction for each YouTube shot is the other agent's `real_context.py` ray cast (DAT texel × DAT lightmap ×1).
Boot Camp is this study's software render of the DAT (scratch script below). Luma is Rec. 709 on 8-bit values.

| Shot | Real luma (RGB) | ×1 prediction | Real / ×1 | Explained by | Our current render / real |
| --- | --- | --- | --- | --- | --- |
| **Boot Camp, Wine, controlled** whole view | 61.1 (59,62,58) | 61.4–64.7 (61,66,64) | 0.94–1.00 | ×1 (the real frame includes an NPC and the HUD) | old ODM import: walls and ceiling 1.3–1.4×, floor 1.03× (outdoor path) |
| Boot Camp floor | 111.9 (123,111,92) | 93.6–104.1 (114,103,87) | 1.08–1.19 | ×1, plus the chandelier `CandleProp` lights near the start, plus the pose | – |
| Boot Camp walls | 63.8–74.4 (57,66,63) | 60.8 (56,62,60) | 1.05–1.2 | ×1 | 78–97 |
| Boot Camp ceiling | 56.5 (48,59,60) | 52.3–62.8 (46,54,54) | 0.9–1.08 | ×1 | 75 |
| Yanmir 1 | 69.0 (38,73,123) | 69.1 (31,75,124) | **1.00** | ×1, hue too | 1.41 (paler) |
| Yanmir 2 | 82.5 (47,85,158) | 64.0 | 1.29 (alt poses 1.15–1.28) | pose; the torches 649–731 LT away are beyond their reach | 1.19 |
| Klusos 1–4 | 36–90 | 22–61 | 1.44–1.66 | `WallTorch`/`CandleProp` dynamic lights 89–271 LT away (size unmeasured); possibly the video's levels | 0.86–0.96 (calibrated to these shots) |
| Verhoffin spawn | 61.1 | 48.4 | 1.26 | not explained: `Fire` 495 LT away (r 80), out of reach; pose or video | 0.89 |
| Dungeon of Secrets 1 | 40.1 (55,36,35) | 24.1 | 1.66; near walls about 3× | **not explained** (no dynamic source, no torch icon) | 0.71 |
| Dungeon of Secrets 2 (purple) | 8.8 (7,6,40) | 15.7 (walls) | 0.56 | darker than ×1: 37 % unlit water, crushed video blacks | 1.84 |
| Dungeon of Secrets 3 | 45.8 | 56.1 | 0.82 | pose (door shut in ours) | 1.55 |
| **Dungeon of Secrets 4** | 41.8 (47,40,46) | 11.1 | **3.77** | **Torch Light on (HUD icon)**: grey, near walls 3× | 0.36 |
| **Dragon Stadium** | 66.9 (70,66,69) | 32.9 | **2.03** | **a uniform ×2 gain**: floor 49 → 98 (real 100.6), wall 11.6 → 23 (real 24.7); `Saturate`/capture setting in that video | 0.55 |

**Hue:**
- Yanmir 1 and Boot Camp match in hue at ×1.
- The "deep cyan" of our Yanmir's Fort and the "deep red" of our Dungeon of Secrets are bake hue drift. In the lightmap
  zones, ours runs from "too neutral" ×0.6 to "too saturated" ×2.1 against MM9's lightmaps (`hue_vs_lightmaps.py`),
  in both directions.
- MM9's own lightmap hue reproduces the real shots wherever the static light dominates.

**What remains unexplained:**
- Dungeon of Secrets 1: the near walls are 3× with no source found.
- Verhoffin: 1.26×.
- Yanmir 2: 1.29×.

These are within the ±15 % plus pose spread of the YouTube data, or need an in-game check (Dungeon of Secrets 1 under
Wine, see the user steps below).

## 3. What to change, once for all MM9 maps (ranked by effect)

| # | Change | Effect | Effort | Risk |
| --- | --- | --- | --- | --- |
| 1 | **Static light from MM9's DAT lightmaps.** A resampler writes the `OYILIT1` sidecar directly from the DAT. For each lightmap texel of our face: native point → LT, then the DAT polygon in the same plane containing it (world model 0 plus the `PhysicsBSP`/door models; skip `VisBSP`, which carries no lightmaps), then the bilinear DAT texel ÷ 255 (`rgb555_to_bgra` bit replication, `lightmap_uvs_for_poly` mapping, LithTech grid `LMGridSize`). Write it with `max_lighting` 1. Retire `direct_scale`, `bounce_scale`, `ambient_scale`, `ambient_colour`, `max_lighting` and the extra, LIGHTDEFS and DirLight bake-only lights for MM9 profiles. Mover faces use their own world model's lightmap. Add a debug capture with dynamic lights and actors off, to measure our runtime extras. | Largest: walls equal MM9's by construction, including hue (Yanmir's cyan and the Dungeon of Secrets red) | Medium: a new step in `bake_indoor.py` or a sibling tool, called from `mm9r_common/dungeon/lighting.py`. The format, the shader and the review root are unchanged | Low for MM6–MM8: data only, and only MM9 sidecars change. Medium for MM9: merged or moved faces and added geometry need the fallback (2), and seams need the chart padding the bake already has |
| 2 | **One global fallback recipe** for faces with no DAT polygon: Cycles direct light only, colour × `BrightScale`, MM9's window and cone, shadows, **no bounce**, floor = WorldInfo `AmbientLight`/255, clip at 1. Calibrate once on the matched faces of all 24 maps (a single `direct_scale`, the same for every map) | Covers new geometry without per-map tuning | Low: the profile keys stay, with defaults pinned for every MM9 profile | Low |
| 3 | **Dynamic sources as runtime lights.** `Fire`, `WallTorch`, `Torch`, `CandleProp`, `Brazier`, `LightFX`, `FlickerLight`, `GlowingLight` become runtime dynamic lights with MM9's radius and colour (flicker from `LightMin/MaxRadius` and `FlickerRate`), never baked (they are not in MM9's lightmaps either), active within the world's `DynamicLightDist` of the camera. MM9 falloff is `1 - d/r` with no N·L. If ours (`(1 - d²/r²)²`) must stay, scale the radius in the converter. An exact match needs an opt-in per-light falloff flag that only MM9 scenes set, so MM6–MM8 stay unchanged | Klusos-type rooms: +40–60 % near torches | Medium (converter, plus a possible opt-in engine flag) | Size unverified. Calibrate with Wine shot B (`DynamicLight 0` vs 1) before tuning |
| 4 | **Player light and Torch Light:** no global light. Optionally scale the Torch Light spell to MM9's (grey 191, r = 12 × power LT ≈ 31 × power native) for MM9 only | Small | Low | The spell is shared gameplay: keep the MM6–MM8 behaviour unless the user asks |
| 5 | **No shader or colour-space change.** Keep display-space `T × L` and non-sRGB textures. Optionally, for MM9 maps only, clamp the static term at 1 (the data already does) | None needed | – | – |
| 6 | (Outdoors, separately) The old ODM import draws `T × lightmap × v_color0 × fxLighting(base u_fxLightParams.y)` and is 1.3–1.4× MM9 on Boot Camp's walls. The Isle of Ashes and later outdoor work should use change 1 there too | Outdoors only | – | – |

## User steps for more real-MM9 evidence

- **Same pose, dynamic lights off:** add `"DynamicLight" "0"` to `autoexec.cfg` (in a copy of the game) and repeat
  Boot Camp shot A. A Klusos House torch corridor is the better target if it can be reached.
- **Start in a given dungeon (untested):** `cshell.dll` reads the console var `runworld` at startup (`0x1009be6c`) and
  switches its start struct when it is set (`0x1009c0a7`). From the game folder, try:
  `wine lithtech.exe +runworld worlds\klusoshouse`. Add `+windowed 1` to run in a window; `windowed` is also read
  there. The party state may be missing without a save.
  - A prepared Wine copy of the game is at `output/mm9_rework/mm9_wine/game` (1.1 GB), with its own prefix at
    `output/mm9_rework/mm9_wine/prefix`. It has not been launched.
  - The console is hidden by `NumConsoleLines 0` and `consolealways 0`. Raising both may let `DynamicLight 0` be typed
    live, which gives an A/B at one pose.

## Evidence files

- Real Wine capture: `overnight/real_mm9/bootcamp_wine_A.png`. It is 468×351, taken from the raw 2000×837 capture;
  the game area is 4:3 and only scaled, so means and ratios hold.
- DAT software render (texture texel, lightmap texel, polygon id and normal per pixel, 90° horizontal FOV, VisBSP
  skipped): a scratch script, not in the repository. It works like `mm9r_common/real_context.py` at full resolution.
  - Boot Camp poses: StartPoint1 (10144, 552, −2624), floor at 504, eye taken at 584.
  - The real view faces south-east (the compass reads SE), i.e. yaw about 2.36 with a slight upward pitch. The room is
    nearly symmetric, so the class statistics (floor, wall, ceiling) do not depend on the exact pose.
- Our old-import capture:
  `./tools/run_game.sh --isolated mm9light_bootcamp2 --world mm9 --map bootcamp.odm --position 25969 -6717 1290`
  `--yaw-radians -0.785 --pitch-degrees 0`, with a tour at pitch 0.2.
