# MM8 animated and light-emitting decorations in 3D (batch `animated`, 2026-10-15)

Batch of the MM8 decorations project (`../BRIEF.md`, `../README.md`). The native animated sprites become animated
3D models using only the engine's cheap material extras: shared flipbook flames, emission with `openyamm_pulse`,
`openyamm_uv_scroll`, `openyamm_wind`, `openyamm_flutter`, camera-facing BLEND glow cards and `swing` bindings.
All geometry is procedural Blender modelling traced from the restored native frames (x2 pixels at 0.5 map units).
No paid generation.

## Models

All are engine content in `assets_source/engine/models/`, cooked into `assets_dev/engine/models/` by
`tools/install_model.py --engine` (all ten installed 2026-10-15). Sizes: source GLB / cooked runtime GLB (textures cook separately).

| Model | Decoration (placements) | LOD triangles | Size | Animation |
|---|---|---|---|---|
| `mm8_deco_bell_buoy.glb` | dec30 (17: out01, out02, out13) | 3420 / 1432 / 528 | 1.66 MB / 193 KB | wind 0.09 on all materials, bell and clapper 0.2 |
| `mm8_deco_air_orb.glb` | dec57 (428, elema) | 194 / 82 / 38 | 0.43 MB / 18 KB | uv scroll [0.025, 0], sine pulse [0.3, 3.2] on orb and additive halo |
| `mm8_deco_seaweed.glb` | dec58 (48, elemw) | 264 / 96 / 30 | 0.87 MB / 24 KB | wind 0.25, flutter 0.03 |
| `mm8_deco_coral.glb` | dec59 (100, elemw) | 360 / 132 / 48 | 0.96 MB / 35 KB | coral wind 0.04; strands wind 0.15, flutter 0.05 |
| `mm8_deco_lantern.glb` | dec07 (54: d24, d06) | 2242 / 872 / 324 | 1.24 MB / 136 KB | Flame03 flipbook, flickering underside/wick, additive flickering halo, swing |
| `mm8_deco_chandelier1.glb` | dec08 (15: d40, d27) | 3552 / 1476 / 680 | 1.19 MB / 242 KB | 7 additive candle-glow flames (6 card billboards), flicker, swing |
| `mm8_deco_chandelier2.glb` | dec27 (9: d09, d06) | 3126 / 1552 / 689 | 2.38 MB / 274 KB | 8 additive candle-glow card billboards, flicker, swing |
| `mm8_deco_candlestick.glb` | dec02 (1, d06) | 1722 / 688 / 398 | 1.01 MB / 115 KB | 3 additive candle-glow flames (2 card billboards), flicker |
| `mm8_deco_standing_torch.glb` | dec06 (8, out02) | 1270 / 650 / 138 | 2.85 MB / 101 KB | 2 Flame02 cards + additive blaze, additive sparks and halo, flicker |
| `mm8_deco_campfire.glb` | dec24 (9, outdoor) | 366 / 158 / 100 | 2.92 MB / 50 KB | 3 Flame02 tongues + additive blaze, additive sparks and halo, flicker |

Review sheets: `review/<prop>/sheet.png` (props: buoy, orb, seaweed, coral, lantern, chandelier1, chandelier2,
candlestick, torch, campfire). Each shows the native frame(s), LOD0 front, three-quarter and side, every LOD, and for
moving models a motion strip at six times (the engine's wind and flutter evaluated on the CPU, or the swing). Native
frame strips: `review/native_frames/<name>.png` (x2) and `<name>_native.png` (8-bit, x3).

## Suggested bindings

Heights are the inventory heights. Each model's bounds height equals its inventory height, except the orb (below).
For hanging fixtures the bounds top is the chain top, which is the `swing` pivot. `swing` animates only indoors:
`DecorationModelSet::animate` is driven by `IndoorRenderer` alone.

```yaml
# outdoor: decorations.yml
- {name: dec30, model: engine/models/mm8_deco_bell_buoy.glb, height: 234}
- {name: dec57, model: engine/models/mm8_deco_air_orb.glb, height: 79, z_offset: -9}   # 61-unit sphere + halo card
- {name: dec58, model: engine/models/mm8_deco_seaweed.glb, height: 251}
- {name: dec59, model: engine/models/mm8_deco_coral.glb, height: 243}
- {name: dec06, model: engine/models/mm8_deco_standing_torch.glb, height: 119}
- {name: dec24, model: engine/models/mm8_deco_campfire.glb, height: 51}
# indoor: indoor_decorations.yml
- {name: dec07, model: engine/models/mm8_deco_lantern.glb, height: 128, swing: [1.2, 2.2]}
- {name: dec08, model: engine/models/mm8_deco_chandelier1.glb, height: 127, swing: [1.0, 2.6]}
- {name: dec27, model: engine/models/mm8_deco_chandelier2.glb, height: 127, swing: [1.0, 2.6]}
- {name: dec02, model: engine/models/mm8_deco_candlestick.glb, height: 123}
```

- No binding needs `still`, `mount`, `free_model` or `lod_pixels`. Yaw is random everywhere (all models read from
  every side), and `height_jitter` is 0.
- **Orb:** the halo card is 1.3 times the sphere radius and sets the bounds. A height of 79 therefore gives the
  native 61-unit sphere, and `z_offset: -9` puts the sphere's bottom where the sprite's bottom was.
- **Swing periods:** the native frames do not move these fixtures (only the flames change). The periods come from
  the pendulum length: the lantern is about 1.1 m to its centre of mass, the chandeliers are heavier. The angles are
  kept small so the swing reads as a creak.
- **Motion measured on the native frames:**
  - seaweed: frond tips about ±20 units in 1.25 s;
  - coral: about ±2.5 units, while its green strands wave;
  - buoy: rocks with its top about ±5 units, and the bell swings about ±15° in 1 s.

## Construction notes

- **Orb dec57:** a 16 × 7 UV sphere with the procedural `orb` texture: silver clouds on the native ball's luminance
  ramp, seamless around the sphere.
  - Glossy and lit, with `openyamm_edge_darkening` 0.3 for the native ball's dark rim and a faint grey emission that
    breathes.
  - The clouds drift round the ball (one turn in 40 s).
  - A camera-facing BLEND halo card (`orbhalo`: half opaque at the silhouette, gone at the card edge) pulses with it.
    The sphere hides the inside of the card.
- **Seaweed dec58:** eleven pinnate fronds on a painted atlas (`seaweed`: four variants, 1024 × 256 rows, base at
  u = 0).
  - Each frond is a curved, twisted strip that leans out in a V from a tight clump. Its width follows the painted
    frond (`textures/seaweed_profile.json`), and it stops at the painted tip.
  - COLOR_0 alpha, the flutter weight, rises from the base, so the shader's flutter wave travels up the fronds.
- **Coral dec59:** a red branching spire built from three crossed fans and two lower side fans (painted recursive
  coral, `coral` atlas rows 0-511), kept stiff. Fourteen wavy green strands round it sway and ripple.
- **Lantern dec07:** chain of five links, neck, smooth-iron hood with a flat brim, three thin rods (two seen in
  front at ±18) and an oil bowl with a finial point.
  - The flame is a narrow camera-facing Flame03 card. The hood underside and bowl inside (`Underside`) carry a warm
    emission that flickers (pulse 0.37 s), the wick glows, and a soft halo pulses.
  - No glass: the native lamp is open.
- **Chandelier dec08:** silvery wrought iron:
  - a chain, a crown with four thorn horns, and four heart scrolls framing the tall centre candle;
  - two long arms to the outer candles and four short arms to inner candles (front pair lower, back pair higher, as
    in the sprite);
  - a bulbous spindle, three inner curls and six scroll legs curling down to finial points.
- **Chandelier dec27:** dark iron on four red-brown wooden posts:
  - a twisted chain, a crown, and four scalloped straps with curls down to the posts, which carry two iron bands each;
  - eight radial arms with an octagonal ring, ending in cups with thick white candles;
  - pendant finials under the posts and four of the arms, and a central pendant.
- **Candlestick dec02:** a copper three-branch candelabrum with a domed foot, a crossbar and U-shaped arms to two
  side cups. Its three candles are uneven, as in the sprite.
- **Standing torch dec06:** a club-like stick with four carved dark diamonds, a wound head (a lathe roughened into
  lumps and wraps, plus five tilted flat strips), an ember crown, two coplanar mirrored Flame02 cards a third of the
  loop apart, and a halo.
- **Campfire dec24:** four cut logs as in the sprite, with no stone ring (unlike the MM6 campfire):
  - two lying side by side in front, one resting across them behind, and a short one at the back right;
  - the bark is reddened where it faces the fire, and the cut ends use procedural rings;
  - a small glowing ember bed with coals, two Flame02 cards and a halo.
- **Bell buoy dec30:** a tapering barrel of staves (one plank of the scan per stave) with two dark studded bands, a
  copper cage of four flat bars and two flat rings, a brass bell with its hook and clapper hanging from a crossbar,
  and a brass dome.

## Shared techniques

- **Flames:** the shared CC0 Unity Labs flipbooks (`../../mm6_dungeons_3d/textures/FLAMES.md`): Flame02 for the
  torch and campfire, Flame03 for candles and the lantern. They are BLEND, double-sided, unlit, and played with
  `openyamm_flipbook: [16, 4, 30]`.
  - Flames on the model axis are camera-facing (`openyamm_billboard`).
  - Off-axis candle flames are two crossed fixed cards (one at LOD2), because a camera-facing card keeps only its
    offset across the model.
  - Each flame's texture coordinates are shifted by whole frames (the sampler repeats), so neighbouring candles do
    not flicker in step (`anim_lib.flame_card(frame_offset=...)`).
- **Draw order:** blended and additive slots are moved to the end of each primitive list (`anim_lib.order_materials`,
  by name prefix: halo, flames, blaze, sparks), so they draw after the opaque parts.
- **Colour:** COLOR_0 is vertex occlusion times a per-material tint. The tint is linear(native sRGB) / linear(texture
  mean) (`textures/means.json`), with targets measured on the frames (`scripts/measure.py`). For the painted plant
  atlases it is a plain shading factor (`anim_lib.scaled`).

## Pretty lights pass (2026-10-16)

The engine gained three static decoration extras (user-approved "pretty lights"): `openyamm_billboard: "card"`
(each primitive turns about the vertical axis through its own centre), `openyamm_additive` (a BLEND material adds
colour x alpha, faded by fog, casting no shadow) and `openyamm_flicker: [amplitude, changes per second]` (smooth
random emission flicker instead of the sine pulse).

- **Candles** (chandeliers dec08/dec27, candlestick dec02): every flame is `candleglow`, a new flipbook made by
  `make_textures.py`. It is the shared CC0 Flame03 re-centred in square frames, with a soft warm halo blurred from
  each frame's own alpha, so the halo breathes with its flame. Every candle flame is additive and flickers
  `[0.3, 8]`, with its own flipbook frame offset.
  - Every off-axis flame is a card billboard on its own material copy (`Candle0`, `Candle1`, ...), because the
    pivot is per primitive. That is one extra draw per candle at LOD0/LOD1 (dec08: 6, dec27: 8, dec02: 2).
  - Centre flames turn about the model axis.
  - LOD2 shares one material of crossed fixed additive cards.
  - The old separate halo cards are gone, because each flame carries its halo.
- **Standing torch dec06:**
  - fifteen ragged burning tatters splay off the head's rim (seven at LOD1);
  - the two Flame02 tongues are joined by an additive Flame02 blaze over the lower half (the sprite's bright, pale
    burning head) and rising additive `sparks` (a new procedural 8 x 4 flipbook at 12 fps);
  - a wider additive halo with a softer falloff;
  - the head, the ember crown and the halo flicker.
- **Campfire dec24:**
  - a broad blaze of three Flame02 tongues side by side (one at LOD2) under an additive blaze across the pile;
  - rising sparks;
  - an additive halo;
  - flickering embers, bark and halo.
- **Lantern dec07:** the halo is additive and flickers `[0.35, 8]`; the hood interior and the wick flicker instead
  of pulsing.
- **Orb dec57:** the halo is additive (a fainter silver: colour 176/182/200, emission 40/42/48) and keeps the slow
  sine pulse with the ball.
- **Bell buoy dec30:** unchanged. It has no light (light 0) and no glow cards.
- **Review:**
  - `review.py` draws additive materials as display-space colour x alpha added to the scene, turns card billboards
    about their own centres, and renders LOD0 over a near-black background (`dark_*.png`, a row of each sheet).
  - `review/dark_glow.png` collects the seven lit models.
  - Sheets read the native frames from `assets_legacy/decorations_x2_mm8_20261016/`; `dec24x`, which was not
    archived, comes from the native bitmap.

## Fix 2026-10-16: faces seen from below and inside-out parts

The coordinator found the lantern's hood see-through from underneath in d24. The engine culls the back faces of
single-sided materials, but the Blender review renders did not, so inverted surfaces never showed in the sheets.

- `pl.lathe` faces point to the right of the profile's direction: outward for a profile that climbs, downward for
  one that runs outward and down.
- **Lantern:** both hood profiles ran the wrong way. The dome now runs from the brim in and up. Its inside is a real
  interior shell 1.8 units under the dome (`Underside`), soot-black at the top and warmer toward the brim, with the
  flickering warm emission. Looking up into the hood now shows a deep dark dome instead of the ceiling.
- **Inside-out closed parts**, found by the new check:
  - the orb sphere (every orb showed its inside);
  - the chain links of the lantern and both chandeliers (`anim_lib.link`);
  - the buoy's bell (profile reversed);
  - the campfire's logs, bark and cut ends.
- **Open surfaces:** the campfire's ember bed faced downward (profile reversed). The buoy's dome gained a bottom cap,
  and the torch's ember crown now meets the head's rim.
- **Checked and closed from below:** the chandelier cups (closed lathes from the arm ends), the candlestick foot and
  cups, and the buoy's barrel bottom.
- **Pipeline:**
  - `scripts/check_winding.py` merges each mesh's single-sided primitives, splits them into connected parts and
    requires every closed part to have a positive signed volume. `finish.py` refuses a model that fails.
  - `review.py` culls back faces as the engine does (material settings from `scripts/finish_table.py`) and renders
    LOD0 from 60° below (`lod0_d_below.png`, the fifth tile of each sheet).
  - `review/below_views.png` collects all ten below views.
- All ten models were reinstalled over the same names. Bindings are unchanged.

## Build

`scripts/build.sh [--install] [--textures] [prop ...]` runs, for each prop:

1. the Blender build (`build_orb.py`, `build_weed.py -- seaweed|coral`, `build_lantern.py`,
   `build_chandelier.py -- chandelier1|chandelier2`, `build_candlestick.py`, `build_torch.py`, `build_campfire.py`,
   `build_buoy.py`; shared helpers in `anim_lib.py`);
2. `review.py` and `sheet.py`;
3. `finish.py`: material modes, `tools/link_static_model_lods.py`, validation, and with `--install` it runs
   `tools/install_model.py <work/output> --engine --name <output>`.

Textures come from `scripts/fetch_textures.py` (Poly Haven sources) and `scripts/make_textures.py` (every set plus
`means.json`).

## Sources and licences

- **Poly Haven** (CC0 1.0, https://polyhaven.com/license), 1k PNG in `source/polyhaven/`:
  - rusty_metal_04, rusty_metal_02, blue_metal_plate, leather_white, bark_brown_02 and marble_rock_01, copied from
    the MM6 fire batch's downloads;
  - rough_wood and hessian_380, copied from the MM6 torch textures' downloads;
  - brown_planks_03, downloaded here.
  - Derived sets in `textures/`: iron_dark, iron_smooth, iron_grey, copper, brass, wax, wood, rag, bark, staves and
    ember.
- **Procedural** (this folder): orb clouds, halo, orb halo, rope, log ends, and the seaweed and coral atlases.
- **Flames:** the shared CC0 Unity Labs flipbooks, read only from `../../mm6_dungeons_3d/textures/`.

## Compromises

- **Buoy:** rocks with `openyamm_wind`, which bends the buoy from its base (the top moves most). The native frames
  tilt the whole body, so its waterline also moves; the wind's bend cannot do that. The bell swings harder through
  its own larger wind amplitude, but it sways rather than pivoting on its hook. The barrel bands' studs are small.
- **Chandeliers:** the native look is a front view. The heart scrolls and horns of dec08 sit on the diagonals, so
  from the front and the side they read as one pair.
- **Candle card billboards:** they cost one draw per candle per batch at LOD0/LOD1. LOD2 uses crossed fixed cards in
  one draw.
- **Lantern:** the hood reads a little lighter and greyer than the sprite's black iron.
- **Torch:** its fire is the shared tongue flame plus an additive blaze; the sprite's single tall smoky flame column
  is not reproduced exactly.
- **Campfire:** the blaze is three shared tongues side by side; seen from the side, the camera-facing plane shows
  them as one wide fire.
- **Plants:** fronds and strands are single strips (double-sided), so a frond seen edge-on reads as a thin line. The
  painted atlases are simplified versions of the sprites' fronds and coral.
- **Orb:** the 16-sided silhouette is visible up close (the triangle budget is 200).
- **Flames and flicker:** all of one placement's flames share the per-placement phase and flicker noise; the frame
  offsets only shift frames.

## Engine support that would look better (not implemented here)

Done in the engine since: card billboards, additive blending and random flicker (pretty lights pass above).
Still open:

- **An emissive texture** (or emission scaled by the base texture): glowing embers and orb clouds could keep their
  detail while glowing. Today emission is one flat colour per material.
- **Per-primitive flicker phase:** every flame of one chandelier flickers in step; a phase offset per primitive (or
  per card) would let each candle flicker on its own.
- **Rigid sway about a pivot** (a `rock` extra: rotation about the base or a point, per material): the buoy could
  tilt as a body, and the bell could swing on its hook.
- **`swing` in outdoor maps:** today only `IndoorRenderer` drives `DecorationModelSet::animate`.

## Notes for the MM6 and MM7 fixture projects (to pass on; their files are not edited here)

- **Off-axis flames:** wall sconces with more than one flame, the MM6 chandelier `chndlir0` (twelve crossed candle
  cards) and the cauldron's ring cards could use `openyamm_billboard: "card"`, one material copy per card. Keep it
  to the cards that show; each adds a draw per batch.
- **Glow cards:** the `candleglow` recipe (`scripts/make_textures.py`: Flame03 re-centred with a halo blurred from
  each frame) gives a candle flame and halo in one additive card. Halo cards (`textures/halo`) read best additive
  with a softer falloff (alpha (1 - r)^1.4).
- **Flicker:** fire-lit surfaces, embers, ember beds and halos look better with `openyamm_flicker` around
  `[0.3-0.45, 6-10]` than with the sine pulse. Keep `openyamm_pulse` for slow magical glows (crystals, runes,
  orbs).
- **Sparks:** `textures/sparks` (an 8 x 4 additive flipbook at 12 fps, procedural) on one camera-facing card
  suits campfires, braziers and burning rocks.
- **Winding:** the engine culls back faces of single-sided materials and Blender reviews do not. Check closed parts
  with `scripts/check_winding.py` (merge each mesh's single-sided primitives), and render one view from below.
  `pl.lathe` faces point to the right of the profile's direction.
