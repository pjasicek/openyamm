# MM9 render lighting (reverse engineering)

How the original Might and Magic IX (LithTech Talon, 2002) puts dungeon lighting on screen. This comes from the
shipped binaries, so that our native BLV rebuilds and their bakes can be calibrated against it. Research date
2026-10-30, using Rizin 0.10.0 (`third_party/rizin/build/binrz/`) and `objdump -M intel` for full linear listings.

| Binary (`mm9/game/`) | SHA-256 | Role |
| --- | --- | --- |
| `d3d.ren` | `f4c708f5…1c113805` | D3D renderer DLL, built 2002-01-29, uses `IDirect3DDevice7` |
| `lithtech.exe` | `4e9ddd2b…dd39e56d8` | Engine: console, world load, lights, light table, scene description |
| `data/cshell.dll` | `678700ff…f82f7ae` | MM9 client game code (Brightness, light-scale manager) |
| `data/object.lto` | `b1271f37…7bc37f162` | MM9 server game code (WorldProperties, Light/Fire classes) |
| `mm9.exe` | — | Launcher only. Its only lighting-related string is `LightMap`, and it holds no lighting cvars |

`IDirect3DDevice7` vtable offsets used below: `+0x50` SetRenderState, `+0x54` GetRenderState, `+0x8c` SetTexture,
`+0x90` GetTextureStageState, `+0x94` SetTextureStageState, `+0x98` ValidateDevice. The device pointer is at
`[0x10095cf8]`. Arguments are passed by `mov [esp+N]` (`[esp]`=this, `+4`=stage/state, `+8`, `+0xc`).

## Summary of the formulas

**World polygons (proven):**

```
pass 1:  C = texture * vertexDiffuse            (stage 0 MODULATE, TEXTURE x DIFFUSE)
pass 2:  C = C * lightmap                        (alpha blend SRC=ZERO, DST=SRCCOLOR)  -- default
         C = C * lightmap * 2                    (SRC=DESTCOLOR, DST=SRCCOLOR)          -- only if cvar Saturate=1
```

- The multiplier is **×1**. MM9 never sets `Saturate` (default 0, not in any cfg and not in any game binary), and no
  `MODULATE2X` or `MODULATE4X` (5 or 6) appears in any `SetTextureStageState` call.
- Lightmaps are RGB555 in memory. Expanding them by bit replication (`(v<<3)|(v>>2)`), as our tools already do,
  matches how the hardware reads them.
- There is no gamma ramp: the only ramp source is an optional `lithtech.gam` file, and no such file ships. The `Gamma`
  cvar (default 100) is registered but never read. There is no brightness term either: the global light scale that
  `Brightness` and WorldProperties `LightScale` drive reaches the renderer, but `d3d.ren` turns it into an
  **identity** lookup table, so it has no visible effect.
- Fog is off in the dungeons studied (`EnableFog 0`). The additive `ONE/ONE` passes are per-object additive objects
  and the camera light-add poly. Dynamic lights reach the world through a vertex term (see the open points at the end,
  2026-10-31).

**Models (`.abc` props, characters; proven unless marked):**

```
per vertex, 0..255 units:
  base  = lightTable(modelCentre)                       // AmbientLight + FastLightObjects lights, see below
          (+ sun term outdoors only: lerp(base, sunColour, N.sunDir * sunVisibility))
  sum   = base + Σ_{lights touching model, ≤ MaxModelLights}  colour * (1 - d²/r²) * max(0, N · L̂)
  out   = min(255, sum * objectColour/255 + ModelAdd)          // ModelAdd = 30,30,30 from autoexec.cfg
  pixel = texture * out/255                                     // stage 0 MODULATE
```

- `colour` is the authored `LightColor`/`InnerColor` (0–255) **without BrightScale**: the engine never reads
  BrightScale.
- `d` is the distance from the vertex to the light. `L̂` is the direction from the model origin to the light, in model
  space (inferred from the setup code).
- There is no shadow or line-of-sight test.
- The light table is built at load time: every cell starts at the WorldInfo `AmbientLight`, and each light with
  `FastLightObjects=1` adds `colour * (1 - d/r)`, clamped to 255, again without BrightScale and without occlusion.
  Cell size is `LightTableRes` from WorldInfo, 250 units if absent.
- Lights with `LightObjects=1, FastLightObjects=0` (almost every light in Klusos House) become runtime static lights
  that light models per vertex as above.
- `ModelFullbrite` models are drawn at 255.

**Why props look brighter and warmer than walls:** lightmaps were baked by the preprocessor with BrightScale (0.6 for
most Klusos lights, 0.3–0.8 in Verhoffin) and with shadows. Models get the same lights at full colour, without
shadows, plus ambient 60 (Klusos) or 50 (Verhoffin), plus the flat ModelAdd of 30. At the scale of a room, a dresser
near a (231,157,90) r=300 light receives ~200,140,80 + 90 of light, which saturates warm.

## 1. Lightmap blending

### Two-pass is the default

`Force1Pass` defaults to 0 (cvar table, `0x1000673f`; not overridden in `autoexec.cfg`). In the device-init path
(`0x1001937e`):

```
1001937e  mov ecx,[0x10094f2c]        ; Force1Pass
10019390  test ecx,ecx
1001939d  je 0x100193e6               ; -> "Using 2 pass lightmapping."  (0x100b1060)
1001939f  call 0x1006c570             ; 1-pass stage setup, then ValidateDevice (+0x98)
```

### Lightmap pass blend states (`0x10063790`, duplicated at `0x10064b4b`)

```
100637a4..ed  SetTextureStageState(1, COLORARG1, TEXTURE), (1, COLORARG2, CURRENT)
1006382a      GetRenderState(ALPHABLENDENABLE)          ; saved
1006384a      SetRenderState(ALPHABLENDENABLE, 1)
1006384d      mov eax,[0x10094f9c]                      ; Saturate (default 0)
10063854      je 0x10063878
10063873      SetRenderState(SRCBLEND, 9 = DESTCOLOR)   ; Saturate=1 -> dst*src + src*dst = 2x
10063895      SetRenderState(SRCBLEND, 1 = ZERO)        ; default
100638b5      SetRenderState(DESTBLEND, 3 = SRCCOLOR)   ; result = dst * lightmap
```

The blend is skipped when `[0x10099ec0]` (a setter-controlled mode flag) or `LMFullBright` (`0x10099f10`, default 0)
is set.

### One-pass path, only with `Force1Pass` (`0x1006c570`)

```
stage 0: COLOROP=MODULATE(4), COLORARG1=TEXTURE(2), COLORARG2=DIFFUSE(0)
stage 1: COLOROP = LightmapsOnly ? SELECTARG1(2) : MODULATE(4); COLORARG1=TEXTURE, COLORARG2=CURRENT
```

This path is also ×1.

### Base stage (`0x10009970`, used when `UseDX6Commands=1`, the default)

Stage 0 is set to COLOROP MODULATE, TEXTURE × DIFFUSE, with alpha MODULATE, and `TEXTUREMAPBLEND` is MODULATE. The
world vertex diffuse for lightmapped polygons is presumably white (inferred: anything darker would darken twice).
This rendering was not traced to the vertex writer.

### Texture-op census

Of all 122 `SetTextureStageState` sites, the only immediate COLOROP values are 2 (SELECTARG1), 4 (MODULATE),
7 (ADD, a stage-1 clamp-add helper at `0x100295e4`), 8 (ADDSIGNED, for detail textures) and 18
(MODULATEALPHA_ADDCOLOR, detail/env mode 2 at `0x1006365c`). MODULATE2X/4X never appear. Some sites pass registers, so
this census is not exhaustive, but every lightmap path read here is ×1.

### Lightmap data format

The dynamic-light-into-lightmap code (`0x1005e770`, used only for flagged lights or `FastLight`/`LMDynamic`) reads
and writes 16-bit texels with masks `0x7c00`/`0x3e0`. The pages are therefore RGB555 in system memory (proven). Their
upload format on the GPU is presumably 16-bit as well (inferred).

### `LightSaturate` table (`0x1005ff60`, default 1.0)

This 64-entry 16.16 table, `min(i/63 · LightSaturate, 1)`, is used only to weight lightmap animation frames (LMAnim)
and dynamic lightmap blends. At the default it is an identity clamp.

### Detail textures

`DetailTextures` and `DetailTextureAdd` both default to 1, so a detail stage is ADDSIGNED: `tex + detail - 0.5`. This
averages out to no brightness change and only adds contrast, on surfaces that have a detail texture.

## 2. Gamma and brightness

### Gamma

The `Gamma` float (`0x100902a0`, default 100.0) is referenced **only** in its registration (`0x10006498`).

`IDirectDrawGammaControl` (IID at `0x1008e198`) is used in only one place, the loader at `0x10018874`. That loader
reads 0x600 bytes (a `DDGAMMARAMP`) from a file and calls `SetGammaRamp` (`+0x10`). It runs at startup with
`lithtech.gam` (`0x10019405`, string `0x100b1080`) and from the `LOADGAMMA <file>` console command. MM9 ships no
`lithtech.gam`, so no ramp is ever set.

The GOG wrapper's `dxcfg.ini` has `gamma=1.0`.

### Brightness

`cshell.dll` registers `Brightness` with default 1.0 (`0x100a0424`); `autoexec.cfg` also sets 1.0. The light-scale
manager (`lightscalemgr.cpp`, `0x10072c30`) multiplies the active light scale by Brightness and calls
`SetGlobalLightScale` (client vtable `+0x254`).

The active scale is WorldProperties `LightScale`/`NightLightScale`, divided by 255 (`0x100a6607`, constant
`0x100c5d94`). Klusos uses 255,255,255, so the scale is 1.

`lithtech.exe` clamps the global light scale to **[0, 2]** (`0x40924c`, constant `0x482bd8` = 2.0) and initialises it
to 1 (`0x40e9d9`). It reaches the renderer as SceneDesc `+0x50` (`0x40f377`, from clientmgr `+0x7b4`). `d3d.ren`
copies it to `0x10094170..78` (`0x10002550`) and derives packed values that are never read. Its only consumer is a
change check (`0x10013725`) that rebuilds the 3×256 colour LUT at `0x100955b0`, and that rebuild writes an
**identity** ramp:

```
1001374d  mov ebx,0x100955b0 ; xor ecx,ecx ; mov edx,0x100
10013760  mov eax,ecx ; shr eax,16 ; add ecx,0x10000 ; mov [ebx],al ; inc ebx ; dec edx ; jnz   (bytes 81 c1 00 00 01 00)
```

So in this renderer, Brightness and LightScale have no on-screen effect (proven for `d3d.ren`). The LUT is applied to
vertex colours (for example `0x1004c097`), so it would be the place where a scale took effect.

## 3. Model lighting

### ModelAdd and ModelDirAdd chain (proven)

1. `autoexec.cfg`: `ModelAdd 30 30 30`, `ModelDirAdd 0 0 0`.
2. Console handler in `lithtech.exe`, from the command table at file offset `0x89d18`: ModelAdd → `0x418b95`, which
   parses three floats into `0x49cc10..18` and clamps each to [0, 250]. ModelDirAdd → `0x418c5a`, stored at
   `0x49cc00..08`.
3. Scene description fill at `0x40f395`: ModelAdd goes to SceneDesc `+0x1c`, ModelDirAdd to `+0x28`.
4. `d3d.ren` `0x100796c9`: `[0x100941a0]+0x1c..0x24` is copied to the model state at `+0x624..0x62c`.

### Per-vertex loop (`0x1003d884`; copies at `0x1003dd6b` and `0x1007b330`)

```
d     = dot(N, sunDirModel[+0x648]) * sunVis[+0x654]
base  = amb[+0x658] + (sunColour[+0x63c] - amb) * d      ; amb = light-table sample, sun only if present
for each light (count +0x308, 0x2c-byte entries at +0x48):
    if dot(N, Lhat[+0x54]) > 0 and dist2(v, Lpos[+0x48]) < r2[+0x60]:
        base += colour[+0x68] * (1 - dist2 * invR2[+0x64]) * dot(N, Lhat)
out   = base * objColour[+0x630] + ModelAdd[+0x624]       ; 1003d9af..dc
out   = min(out, 255)                                      ; constants 0x100b28d4..e4 = 255
diffuse bytes -> vertex +0x10..0x12, alpha +0x13
```

### Inputs to that loop

- **Object colour** (`0x10079677`): the object's colour bytes `+0x94..0x96`, multiplied by 1/255 (`0x100b4e34`), so
  they are 1.0 for an untinted prop. Only when `Saturate=1` is it further multiplied by **ModelSaturation** (default
  2.0, `0x1007b71a`).
- **Light entry setup** (`0x100789f1`): the light position is transformed into model space. `Lhat` is that position
  normalised (the model origin's direction to the light), `r2 = radius²` and `invR2 = 1/r²`. The colour is the light's
  `+0x78` colour (0–255), lerped towards `OuterColor` (`+0x94`) by the cone factor for spotlights (FOV cos in
  (−1, 1)).
- **Light count**: `MaxModelLights` defaults to 4 in `d3d.ren`, and MM9's `autoexec.cfg` sets 5.
- **Ambient** (`0x100799b3..0x1007a4b2`): the light table at `[0x1009419c]` is sampled at the model position: the
  position minus the table origin, times the inverse cell size, converted from bytes to 0–255 floats. The 8-way code
  paths suggest trilinear interpolation (inferred). With no table, ambient is 0 (`0x1007a916`). For `ModelFullbrite`
  objects (flag `0x200` in `+0x88`, cvar `ModelFullbrite` default 1) ambient is 255 and the sun is zeroed
  (`0x1007a92f`).
- **Dynamic lights** (OT_LIGHT objects such as Fire flicker lights) are added from the list at
  `0x10094074/0x10094078`, with colour bytes `+0x94..96` (`0x1007a4f0`).

### Light table and static lights (`lithtech.exe` `de_mainworld.cpp`)

- `0x44c34d` parses `AmbientLight r g b` from the WorldInfo string and clamps it to [0, 255]. `0x44c43c` parses
  `LightTableRes`, falling back to 250.0.
- `0x420fb5` allocates the table and fills every cell with AmbientLight.
- `0x421037` scans the object data for `Light`, `DirLight` and `ObjectLight` and reads `LightRadius`,
  `LightColor`/`InnerColor`, `OuterColor`, `Pos`, `LightObjects`, `FastLightObjects`, `Rotation` and `FOV`. It does
  **not** read `BrightScale`: that string is absent from `lithtech.exe`, `d3d.ren` and `cshell.dll`, and present only
  in `object.lto` (class definitions) and the editor-side `Processor.exe`.
  - `LightObjects` defaults to 1. `FastLightObjects` is initialised to 1 once, before the loop (`0x421050`), so a
    missing value is inherited from the previous light (the "sticky" behaviour).
  - `FastLightObjects=1`: `0x4214e1` adds `colour * (1 - dist/radius)` to each cell in range and clamps to 255
    (`0x482430` = 1.0, clamp `0x482bc4` = 255). There is no visibility test.
  - `FastLightObjects=0`: a 0xa0-byte static light is created (`0x4213b8`) with position `+0x68`, radius `+0x74`,
    colour `+0x78`, direction `+0x84`, FOV `+0x90` and outer colour `+0x94`. It is linked into the world and reaches
    the per-vertex loop above.

### WorldModels and `.abc` models

WorldModel geometry (doors, BSP brushes) is world geometry: it is lightmapped or Gouraud-lit with the world passes and
does not use the model loop or ModelAdd (inferred from LithTech structure; WorldModel drawing was not traced). Every
Klusos dresser, chair, table and candle is a `Prop` or `CandleProp` `.abc` model, so the model formula applies to them.

## 4. World-wide terms

- **WorldInfo strings.** Klusos: `AmbientLight 60 60 60`. Verhoffin Ruins: `PBlockSize 1024 ; AmbientLight 50 50 50`.
  Neither sets `LightTableRes`. AmbientLight affects **models only** (through the light table). The lightmaps already
  contain whatever ambient the preprocessor baked.
- **WorldProperties** (Klusos): `LightScale` and `NightLightScale` are 255,255,255, which has no effect (see above).
  `EnableFog 0`, `VFog 0`, `SkyFog 0`, `DynamicLightDist 2500`, `PlayerLightOn 1`.
- **Fog.** The renderer's `FogEnable` defaults to 0; `autoexec.cfg` `fogenable 1` only allows it, and the world turns
  it off.
- **Dynamic lights.** `DynamicLight` defaults to 1, with `DynamicLightDist` 1500 (2500 in the world). The `ONE/ONE` pass
  with black fog colour (`0x10041fc0`/`0x10042043`) is the per-object additive mode, not dynamic lights (2026-10-31).
  Dynamic lights reach the world through the vertex term described in the open points at the end.
  - Klusos has 3 `Fire` objects with flickering lights (radius 55–80, colours (255,190,130) to (255,220,190)) and
    22 `CandleProp` wall candles. `CandleProp`, `WallTorch`, `Torch`, `Brazier` and the `LightFX` family are
    light-making classes in `object.lto`'s class definitions.
- **Player light.** `PlayerLightOn` (WorldProperties, default 1, `object.lto` `0x100da552` → byte `0x101aa170`) is sent
  to the client in a player message (`0x100c2f85`, `0x100c3cf4`). The client turns it into a grey (191,191,191) light
  of radius 36 LT, which the Torch Light spell enlarges to 12 × power. See the open points at the end and the
  [global model](MM9_LIGHTING_GLOBAL_MODEL.md).
- **LightAddPoly** (default 1) enables the full-screen additive poly for the camera light add (SceneDesc `+0x5c`, from
  camera `+0x1a4`). It is zero unless game code flashes the screen.
- **Saturation.** `Saturate` (0) and `ModelSaturation` (2.0, effective only with Saturate) were covered above. No
  colour-saturation post effect exists.

## 5. What this means for our bake

1. **World:** draw `albedo × lightmap555` (bit-replicated) with **no multiplier, no gamma, no brightness**. Matching
   the stored texels is the right target for the static lightmap contribution. **Do not** apply ×2.
2. The 1.3–1.7× brighter, warmer Klusos screenshots are therefore **not** explained by the lightmap formula. Remaining
   suspects, in order:
   - **Dynamic lights near the camera**, added `ONE/ONE`: the Fire flicker lights, possibly CandleProp lights, and the
     `PlayerLightOn` light. Klusos has many candle and fire sources in small rooms; Verhoffin is large with fewer
     sources, which fits the 1.1× there.
   - **Detail textures** add contrast.
   - **Screenshot pipeline differences**: the GOG ddraw wrapper and our own tonemap or sRGB handling.

   A capture with `DynamicLight 0` (`autoexec.cfg`) in real MM9 would settle this. Update 2026-10-31: a controlled Wine
   capture (Boot Camp) confirms ×1. The wrapper and our shaders were ruled out. The YouTube excesses come from
   dynamic sources, the Torch Light spell and per-video gain; see [the global model](MM9_LIGHTING_GLOBAL_MODEL.md).
3. **Props and models:** stop lighting them from the baked lightmap or irradiance alone. Match MM9 instead:
   - ambient = WorldInfo `AmbientLight`, plus `FastLightObjects` lights with linear `1 - d/r`;
   - plus each `LightObjects` light at its **full** `LightColor` (ignore BrightScale), times `(1 - d²/r²)`, times
     `max(0, N · L̂)`, with no shadows and at most 5 lights;
   - plus a flat **+30/255** (ModelAdd);
   - clamped to 1.0 and multiplied by the texture.

   This is what makes MM9 props read brighter and warmer than the walls next to them.
4. If our bake applies BrightScale to wall light (as the preprocessor did), keep that for walls only. Models must use
   unscaled light colours.

## Proven, inferred and open

- **Proven from code:** two-pass default; the ×1 lightmap blend and its Saturate ×2 alternative; no MODULATE2X/4X; no
  gamma ramp without `lithtech.gam`; the unused Gamma cvar; the identity light-scale LUT and the [0, 2] clamp; the
  ModelAdd chain and clamp; the per-vertex model formula and its 255 clamp; light-table construction, its linear
  falloff and the AmbientLight seed; BrightScale absent from runtime binaries; the cvar defaults listed above.
- **Inferred:** trilinear light-table sampling; `L̂` being the direction from the model origin to the light; WorldModels
  not using the model path; GPU lightmap format 16-bit.
- **Closed on 2026-10-31** ([global model](MM9_LIGHTING_GLOBAL_MODEL.md)):
  - **The ×1 formula holds on screen.** A controlled real-MM9 capture under Wine (Boot Camp, default settings, through
    the GOG `ddraw.dll`) matches `texture × lightmap / 255` within 5 % in brightness and in hue. That also proves the
    vertex diffuse of lightmapped polygons is white. The world vertex writer's table at `0x10090648` holds that white
    setter, `0x1004c060`.
  - **The GOG wrapper and `Brightness` change nothing.**
  - **`PlayerLightOn`** reaches the client in the player-info struct (`0x100999d0`) and switches a grey (191,191,191)
    `OT_LIGHT` of **radius 36 LT** (`cshell` `0x100967d0`, `0x100969a0`). The Torch Light spell reuses that light at
    radius 12 × power for its duration (`0x10080e30`, `0x100969c0`). The light has no visible effect without Torch
    Light. Its position update was not found.
  - **The `ONE/ONE` pass at `0x10041fc0`** is the per-object additive mode (object flag `0x10` at `+0x238`), not
    dynamic lights.
  - **Dynamic lights** are selected within `DynamicLightDist` (`0x10026580`). They reach models (list `0x10094074`)
    and world models (`0x100269d0`). The world-polygon vertex term (`0x1004c170`) is `old + (2c - 255)·(1 - d/r)` per
    channel, linear, with no N·L, ×2 under `Saturate`, clamped to 0..255.
- **Open:** which world polygons take that vertex term (lightmapped or only Gouraud ones), and how much dynamic light
  real MM9 adds next to a torch. Real-MM9 shot B (`DynamicLight 0`) would measure it. The light moving with the party
  is also open.

## Cvar defaults (from `d3d.ren` registration, `0x10006040..0x1000708f`, `0x100667d0`, `0x1007b5c4`)

Format is cvar = default, followed by the `autoexec.cfg` value where one is set:

- **World lighting:** LightMap = 1 (cfg 1); LightmapsOnly = 0; LMFullBright = 0; Saturate = 0; LightSaturate = 1.0;
  Gamma = 100 (unused); Force1Pass = 0 (cfg 0); Force2Pass = 0; LightAddPoly = 1.
- **Dynamic and model lighting:** DynamicLight = 1; DynamicLightDist = 1500; FastLight = 0 (cfg `LMDynamic 0`);
  LightModels = 1; ModelFullbrite = 1; MaxModelLights = 4 (cfg 5); MaxModelShadows = 1 (cfg 1); TintModels = 1;
  ModelApplySun = 1; ModelSunVariance = 0.05; ModelSaturation = 2.0; LightModelSprites = 0.
- **Detail textures:** DetailTextures = 1 (cfg 1); DetailTextureAdd = 1.
- **Fog and environment:** FogEnable = 0 (cfg `fogenable 1`); FogR/G/B = 255; FogFarZ = 2000; EnvMapEnable = 0
  (cfg 1); EnvMapWorld = 1.

Scratch listings (`d3d.objdump`, `lt.objdump`, `cshell.objdump`, `object.objdump`, cvar extractor `cvars.py`) were
kept outside the repository and can be regenerated with `objdump -d -M intel --no-show-raw-insn <binary>`.
