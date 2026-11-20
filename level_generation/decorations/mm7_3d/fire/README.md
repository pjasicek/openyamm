# MM7 fire batch: beacon fires, magic pedestals, bell buoy, lantern, burned-out fire (2026-10-15)

Batch `fire/` of the MM7 3D decorations project (brief: `../BRIEF.md`). Procedural Blender models traced row by row
from the restored native frames (`assets_dev/engine/decorations_x2/`), surfaced with graded CC0 Poly Haven scans and
procedural textures of our own. No paid generation. MM8 binds the beacon fires and pedestals too, so those keep their
decoration names (`mm7_deco_dec60` to `mm7_deco_dec75`). Every model is named after the decoration it serves.

| Installed GLB (`engine/models/`) | Decorations | LOD triangles | File | Animation |
|---|---|---|---|---|
| `mm7_deco_dec60.glb` | dec60 (blue beacon fire, stone) | 1902 / 652 / 262 | 2.3 MB | blue flame flipbook: a centre card and 3 / 2 / 1 off-axis `card` billboards per LOD; additive halo; ember bed `openyamm_flicker [0.35, 6]` |
| `mm7_deco_dec62.glb` | dec62 (orange beacon fire, stone) | 1902 / 652 / 262 | 2.4 MB | as dec60, orange flame recoloured deeper by COLOR_0 |
| `mm7_deco_dec63.glb` | dec63 (white beacon fire, stone) | 1902 / 652 / 262 | 2.3 MB | as dec60, white flame |
| `mm7_deco_dec61.glb` | dec61 (golden brazier on clawed feet) | 3018 / 1712 / 766 / 330 | 2.0 MB | as dec60 (one off-axis card at LOD2/LOD3), orange flame recoloured paler |
| `mm7_deco_dec64.glb` ... `mm7_deco_dec75.glb` | dec64 ... dec75 (magic pedestals, one per orb colour) | 2394 / 1002 / 274 | 1.1 MB each | orb `openyamm_pulse [0.3, 2.0]` + `openyamm_uv_scroll [0.02, 0]`; faint additive halo in the orb colour |
| `mm7_deco_7dec33.glb` | 7dec33 (bell buoy) | 2546 / 1226 / 414 | 1.8 MB | every material `openyamm_wind 0.1` |
| `mm7_deco_torch02.glb` / `_free` | torch02 (iron lantern, dungeons) | 1366 / 638 / 298 (free 1282 / 562 / 268) | 1.1 MB | glowing chimney `openyamm_flicker [0.25, 6]`; faint additive halo |
| `mm7_deco_dec24x.glb` | dec24x (burned-out fire, logs) | 460 / 120 / 80 | 1.4 MB | none (native single frame) |
| `mm7_deco_v77dec24.glb` | v77dec24 (lit signal fire, 7dec24a-g) | 528 / 168 / 114 | 2.6 MB | flame02: a centre card and 2 off-axis `card` billboards (LOD0/LOD1), recoloured deeper orange; additive halo; ember bed `openyamm_flicker [0.4, 7]` |

Pedestal orb colours (dec64-dec75): pearl, amber, white, green, blue, crimson, orange, pink, purple, red, silver,
yellow. Each variant is the same GLB except for the `Orb` material's `baseColorFactor` (the orb's deep colour, the
10th luminance percentile of all eight native frames) and `emissiveFactor` (the median colour x 0.22): `ORBS` in
`scripts/finish.py`. The cooker stores identical images once, so the twelve share their textures on disk.

## Suggested bindings

Heights are the model bounds heights, so every model draws at the scale it was traced at (the native art's height,
except where noted).

Outdoor (`assets_dev/worlds/mm7/models/decorations.yml`, and MM8's for the beacons and pedestals):

```yaml
  # Beacon fires and magic pedestals (mm7_3d/fire/).
  - name: dec60
    model: engine/models/mm7_deco_dec60.glb
    height: 190
  - name: dec61
    model: engine/models/mm7_deco_dec61.glb
    height: 198
  - name: dec62
    model: engine/models/mm7_deco_dec62.glb
    height: 190
  - name: dec63
    model: engine/models/mm7_deco_dec63.glb
    height: 190
  - name: dec64
    model: engine/models/mm7_deco_dec64.glb
    height: 201
  # ... dec65 to dec75 the same: model engine/models/mm7_deco_dec<NN>.glb, height 201
  - name: 7dec33
    model: engine/models/mm7_deco_7dec33.glb
    height: 235
  - name: dec24x
    model: engine/models/mm7_deco_dec24x.glb
    height: 25
    still: true
  - name: v77dec24
    model: engine/models/mm7_deco_v77dec24.glb
    height: 51.6
```

Indoor (`indoor_decorations.yml`):

```yaml
  - name: torch02
    model: engine/models/mm7_deco_torch02.glb
    free_model: engine/models/mm7_deco_torch02_free.glb
    height: 130
    mount: wall
```

- No `still` is needed except for dec24x, whose native sprite has one frame. Every animated sprite has a flipbook,
  pulse, uv scroll or wind.
- `height_jitter`, `yaw`, `swing` and `z_offset` are not needed. Yaw can be the placement's or random (all models are
  round, except torch02, which the wall mount orients).
- `lod_pixels`: the engine defaults suffice (low placement counts).
- dec61's sprite art is 201 tall, but its top rows are sparse flame wisps. The model's flame card stops at 198.
- dec24x: the native art is 28 units tall, but its height includes the elevated view's depth. The model is 25 tall
  at the native width (64), so bind it at 25.
- 7dec33: the native art starts 2 units above the placement (`art_bottom`). The model's barrel bottom is on the
  placement point; `z_offset: 2` would match the sprite exactly.

## Quality pass (2026-10-16): fuller fires, halos, flicker

This pass uses the engine's new static extras (`engine/models/ModelAsset.h`).
- **Fires** (dec60-dec63, v77dec24). The single flame card read thinner and less ragged than the native fire, so
  each fire now has:
  - a centre card on the model axis;
  - off-axis flame cards (`openyamm_billboard: "card"`, one material and primitive each: `FlameA`, `FlameB`,
    `FlameC`). They sit at different x and y offsets in the bowl and turn about their own centres, so the fire keeps
    depth from every side;
  - a soft additive halo card (`Halo`: BLEND, unlit, `openyamm_additive`, the procedural `halo` texture, its colour
    and strength from COLOR_0). It stays inside the flame's height, so the bounds and binding heights are unchanged.

  Each card's texture u is offset by whole frames (`flame_card(shift=...)`: 5, 9, 13 columns; the sampler repeats),
  so a placement's cards do not flicker in step. The ember beds use `openyamm_flicker` instead of the sine pulse.
- **Lantern** (torch02). The chimney flickers (`[0.25, 6]`, as the four native frames do) and has a faint warm
  additive halo (72 x 58 units round the cage).
- **Orbs** (dec64-dec75). Each has a faint additive halo in the orb colour (`ORB_HALO` 0.45 x the median colour,
  per variant through `baseColorFactor`). It is 84 x 66 units, centred a little below the orb so its top stays at the
  orb's top: the orb's light on the cup. The orb keeps its breathing pulse.
- **Review.** `review.py` renders additive materials as transparent plus emission, turns "card" billboards about
  their own centres, and adds a night view (`night.png`, the last tile of the LOD row), where the halos show.
  `review_variants.py` adds a night row to the pedestal sheet.
- Every model was reinstalled under its name after `check_winding.py` reported 0 inverted closed parts. v77dec24's
  bounds are unchanged (binding height 51.6).

## Models

- **Stone beacon (dec60, dec62, dec63).** This is one lathe traced from dec60a:
  - a stepped round plinth (29 units radius);
  - a slightly swelling column with a collar ring and a neck;
  - a shallow flared bowl with a rolled lip (45 radius, rim at 128).

  A domed ember bed of the flame's colour sits just under the lip. It is lit, with emission and pulse, and is visible
  from above. The fire is three camera-facing cards: a centre card (base 123, tip 190, 92 wide) and two lower,
  narrower side cards (one mirrored), for the sprite's broad, bushy fire. Flames:
  - dec62: `mm6_dungeons_3d/textures/flame02`, with COLOR_0 (0.85, 0.27, 0.2) turning the torch yellow into the
    sprite's deep orange-red (native linear ratio 1 : 0.16 : 0.01);
  - dec60: `shared_flames/flame02_blue`;
  - dec63: `shared_flames/flame02_white`.

  Edges sharper than 30 degrees are split, so the plinth steps stay crisp. Stone: COLOR_0 follows the native colour
  by height (dark plinth, lighter column, dark bowl underside, lit rim), warmed slightly against the review sky.
- **Golden brazier (dec61).** Built from:
  - a wide bowl with a rolled lip on a narrow neck, and an urn-like collar;
  - a cage of eight curved ribs round a core, under a ring;
  - a waist ring and a base dish;
  - five clawed legs ending in ball feet gripped by three talons.

  LOD3 replaces the cage with a flared drum and the legs with single bars. The flame02 card is recoloured paler by
  COLOR_0 (0.8, 0.55, 1.2), toward the sprite's soft orange.
- **Magic pedestal (dec64-dec75).** Built from:
  - a flared skirt ringed with twelve curled claws, and a plinth with a notched band (14 blocks);
  - a plain shaft;
  - a capital with twelve hanging tabs and a wide plate;
  - a notched cup holding a glass orb (radius 24.5, top at 201).

  The orb material is glossy (roughness 0.1) with the procedural `orb` texture: pale clouded glass with curling
  swirls, which scroll slowly round it, standing in for the native swirls that change from frame to frame. Its
  emission breathes (pulse 0.3 over 2 s).
- **Bell buoy (7dec33).** The sprite is a bell buoy: it has no lantern and no light (light radius 0). The model has:
  - a barrel of wooden staves with two dark corroded bands and an open top;
  - six brass straps (two in front, as on the sprite) rising to two flat hoops;
  - a copper dome;
  - a broad brass bell hanging from a crossbar, with its clapper rod and ball below.

  All materials sway with `openyamm_wind 0.1` (about +-6 units at the top), as the native frames rock the whole buoy.
  The bell sways with the rest; the engine's wind grows with height, so a separate pendulum swing is not possible.
  No glow was added: the sprite has none.
- **Lantern (torch02).** Built from:
  - a domed foot and a rolled collar;
  - a flaring cage (an alpha-tested `grid` cut-out on a cone, double-sided) round a glowing glass chimney (lit
    material with emission (225, 132, 70) and a pulse; the four native frames flicker the light inside);
  - a wide lid band with a knob;
  - a squarish wire bail on pivots.

  **Mounting: wall-mounted.** 48 of the 56 placements (d03) stand 9-12 units from a wall, 176 units above the floor,
  under a ceiling 208 above them. That is how torches are placed (yaw 0), so torch02 binds with `mount: wall`. The
  `torch02` model adds a wall plate (back face at Blender +y = 31 units, just behind the foot) and an iron arm reaching
  over the cap, whose hook holds the bail's top. `torch02_free` is the lantern alone, for the 8 placements with no
  wall in reach (7d17, and two on d03 floors). Its bounds are 127.5 tall against 130, so under the shared binding
  height it draws about 2 % larger. Colours are the sprite's fire-lit rust oranges by height, through COLOR_0 (not
  brightened).
- **Burned-out fire (dec24x).** Five slightly irregular logs, stacked as on the sprite:
  - two lying across;
  - a shorter one in front;
  - one behind on the right;
  - one on top whose near end shows the cut end grain.

  The bark is `bark_brown_02`, graded to the sprite's dark brown (undersides darker); the ends are the procedural
  `endgrain` (red-orange growth rings, cracks, charred rim). There is no ash or ember, as on the sprite.

- **Lit signal fire (v77dec24).** The three Signal Fire Pits of 7out02 (events 237-239) switch dec24x to
  v77dec24 when the party lights them. `build_burnedfire.py -- lit` keeps dec24x's logs: the same geometry and
  COLOR_0 (the unlit build was checked to rebuild byte-identical). It adds:
  - a small glowing ember bed between the logs (`ember_orange`, emission (170, 72, 22), pulse [0.3, 0.6]);
  - two camera-facing flame02 cards centred on the native flame (x -4): a 50-wide card with its base at 10.5 and its
    tip at 51 (the native flame's top), and a narrower mirrored card reaching 40.

  COLOR_0 (0.95, 0.6, 0.55) deepens the torch flame toward the sprite's orange. Engine scale is binding height / LOD0
  bounds height, so the binding height keeps the logs the same size across the switch:
  25 x 0.632636 m / 0.306501 m = 51.6. The model bounds are 51.69 units against dec24x's 25.04.
  Review: `review/litfire/sheet.png`.

## Textures, sources and licences

`scripts/fetch_textures.py` downloads 1k PNG sets (diffuse, OpenGL normal, roughness, and each asset's `files.json`)
into `source/polyhaven/`. All Poly Haven assets are CC0 (https://polyhaven.com/license).
`scripts/make_textures.py` grades them into `textures/<name>_{basecolor,normal,mr}.png`, using
`../../mm6_dungeons_3d/fire/scripts/pbr.py`, imported read only. The base colour keeps the scan's luminance detail,
with contrast applied as a power, times the target colour's chroma. `textures/means.json` holds the linear means used
for the COLOR_0 tints.

| Set | Source | Used for |
|---|---|---|
| `stone` | Poly Haven `rock_face_03` (CC0) | stone beacons |
| `gold` | Poly Haven `european_walnut_veneer_05` (CC0; its fine linear streaks as brushed metal, recoloured gold, metal 0.55) | golden brazier, pedestals, buoy straps, hoops and bell |
| `copper` | the same veneer scan, recoloured copper | buoy dome |
| `staves` | Poly Haven `wood_planks` (CC0), turned 90 degrees (seams along v = vertical staves) | buoy barrel |
| `bandiron` | Poly Haven `rusty_metal_04` (CC0) | buoy bands |
| `rust` | Poly Haven `rusty_metal_05` (CC0) | lantern iron and chimney |
| `bark` | Poly Haven `bark_brown_02` (CC0), moss desaturated | dec24x logs |
| `ember_orange` / `_blue` / `_white` | `rock_face_03` through a fire ramp (its cracks glow) | beacon ember beds |
| `endgrain`, `orb`, `grid` | procedural, this batch (own work, FFT noise; `grid` takes its colour from `rust`) | log ends, pedestal orbs, lantern cage |

Flames:
- `../../mm6_dungeons_3d/textures/flame02_basecolor.png`: the CC0 Unity Labs Flame02 flipbook recoloured to the MM
  torch flame; licence in `../../mm6_dungeons_3d/source/unity_labs_vfx/`;
- `../../shared_flames/flame02_blue_basecolor.png` and `flame02_white_basecolor.png`: the same flipbook in other
  colours.

All three are `openyamm_flipbook [16, 4, 30]`, unlit, blended, double-sided and camera-facing.

## Scripts and rebuild

- `./build.sh [--install]` rebuilds everything (about 10 minutes): textures, builds, reviews, finish, and the
  pedestal variant sheet. Run `scripts/fetch_textures.py` once first.
- `scripts/run.sh <build script> <variant|-> <prop> <outdoor|dungeon> <yaw> <native texture>` builds, reviews and
  sheets one model.
- `python3 scripts/finish.py <prop> [--install]` links the LODs, sets material modes and orb factors, validates
  (budgets, COLOR_0, base on the ground) and installs through `tools/install_model.py --engine`.

Files:
- `scripts/firelib.py`: the shared helpers. It imports the MM6 `props_lib` read only and adds materials, glow
  materials, flame cards, tints, lathes and tori, and the LOD loop with sharp edges.
- Builders: `build_beacon.py -- stone_blue|stone_orange|stone_white|gold`, `build_pedestal.py`, `build_buoy.py`,
  `build_lantern.py -- lantern|lantern_free`, `build_burnedfire.py`.
- Review:
  - `review.py`: Blender renders under outdoor sky and sun, or the dungeon's flat light. Specular is scaled by
    `openyamm_specular` as in the engine.
  - `sheet.py`: the review sheets. It prints native and model band means.
  - `review_variants.py` and `sheet_variants.py`: the pedestal colour sheet.
  - `profile.py`: per-row silhouette and colour of a sprite.
  - `sprite_sheets.py`: every native frame (`review/sprites/`).

## Review

- `review/<prop>/sheet.png`: native first frame | LOD0 front | three-quarter | side, with all LODs below. Props:
  `beacon_stone_blue`, `beacon_stone_orange`, `beacon_stone_white`, `beacon_gold`, `pedestal`, `buoy`, `lantern`,
  `lantern_free`, `burnedfire`.
- `review/pedestal_variants/sheet_variants.png`: all twelve orbs under their sprites.
- `review/textures.png`: the texture sets.
- `review/sprites/`: all native frames and zooms.

Measured band means (LOD0 front against the native sprite, 6 bands top to bottom) are within about 10 sRGB levels on
the stone, gold, wood and log bodies.

## Compromises

- Flames are the shared Flame02 flipbook on 4 cards (beacons) or 3 (signal fire). It is fuller since the quality
  pass, but still softer and less pixel-ragged than the native fire.
- The engine's emission is one constant colour per material: ember beds, orbs and the lantern chimney glow evenly
  and pulse or flicker as a whole.
- The pedestal orb's swirls are a procedural texture scrolling round the orb, not the native carved pattern.
- The buoy's bell rocks with the buoy (wind); it does not swing on its own as in the native frames.
- torch02's wall bracket is an addition the sprite does not show. The free variant is 2 % shorter than the wall
  variant.
- The golden brazier's legs read thinner than the sprite's heavy claw feet from a distance. Its LOD3 is a coarse
  6-sided impostor.
- The pedestal LOD0 (2392 triangles) is spent mostly on the claws and notched bands. The twelve variants share it.
- Each GLB embeds its own copy of its flame atlas (about 0.8 MB of each beacon's size). The cooker deduplicates
  identical images.
- Outdoor models were reviewed in Blender only (no game run, per the brief). The outdoor maps that place them need a
  re-bake once they are bound: MM7 7out01-06, 7out13, 7out15 and out09-out14, as listed in `../inventory.json`.
