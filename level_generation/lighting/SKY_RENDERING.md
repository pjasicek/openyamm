# Enhanced outdoor sky

The Enhanced sky replaces the original projected cloud quad with a procedural sky, and makes all outdoor fog take its
colour from that sky. It is the only outdoor sky: the classic renderer and its `video.sky_style` setting were removed
on 2026-10-11. Where a preset draws no sky (underwater), the sky view's clear colour, the flat fog, is the background. Implementation history and acceptance results: [`SKY_RENDERING_GOAL.md`](../../SKY_RENDERING_GOAL.md).

## How it fits together

| Piece | Location |
| --- | --- |
| Presets, aliases, weather ladder | `assets_dev/engine/rendering/sky/sky.yml` |
| Texture sources | `assets_source/engine/rendering/sky/*.png` and `legacy/*.png` (cloud layers, horizon ring, night sky, moon, original skies) |
| Runtime textures | `assets_dev/engine/rendering/sky/**/*.oytex` (BC7) and `assets_cooked/android/...` (ASTC), from `tools/cook_sky_textures.py` |
| Preset loader and keyframe tracks | `game/render/SkyPresets.{h,cpp}` |
| Per-frame state (selection, transitions, sun/moon/stars) | `game/render/SkyState.{h,cpp}` |
| GPU side (sky pass, textures, uniforms, model environment source) | `game/render/SkyRenderer.{h,cpp}` |
| Sky pass shaders | `game/shaders/vs_sky.sc`, `fs_sky.sc` |
| Shared sky colour and fog helpers | `game/shaders/sky_common.sh` |
| Frame hook | `OutdoorRenderer::updateEnhancedSky`, `applySkyFogUniform` |

- Every outdoor fog blend (terrain, bmodels, decorations, water, billboards, outlines, spell preview, 3D models)
  calls `skyFogDisplayColor()`, so distant geometry fades into the sky colour in its own direction.
- `skyFogRatio()` adds Enhanced-only distance haze and a fade at the terrain square's edge. Fog distances and
  visibility rules are unchanged.
  - Through the middle distance the haze is a gentle depth cue: at most 35% of the preset's `aerial_haze`, between
    30% and 90% of the view distance. Towns a few thousand units away stay clear.
  - From 55% of the view distance, a steep fade reaches the sky completely at the view distance.
  - The world fog's own clear-weather fade covers only its last eighth. From the air, where the end of the terrain is
    seen edge-on, that showed as a hard cut.
- Open sea continues past the map edge to the horizon. At map load, `measureOutdoorDistantSea`
  (`game/outdoor/OutdoorDistantSea.cpp`) measures each side of the terrain border (west, east, south, north): its
  water share, the sea level and the water tiles' colour.
  - Below the horizon, the sky pass draws that sea wherever a view ray leaves the map through a sea side, blending
    across corners. It uses the water shader's base colour, the sky's Fresnel reflection, and haze along the ray's
    distance.
  - Fogged geometry below the horizon fades into the same sea, so distant water, coast and ships vanish into it
    instead of into a band of horizon fog.
  - Water facing a sea side (`skyWaterFogRatio`) fades into that sea over the whole far distance, from 40% to 97%
    of the view distance. Otherwise its own dark colour would end in a visible curve where the water stops at the
    view distance. Land, coast and buildings keep the gentle haze.
  - Land sides keep the horizon haze. Fog weather hides the sea with the rest of the view.
- `u_skyFog[1].w` (sky share) is 0 indoors and underwater, which returns the flat fog colour exactly.
- `u_skyFog` has eight vectors: sky colours and sun (0–3), map edge and aerial haze (4), and the distant sea (5–7:
  lit colour and visibility; camera height, haze distance and camera x/y; per-side weights).
- The sky pass reconstructs view rays from the same view/projection as the world (main view and water reflections).
- The main sky is drawn in the main view after the opaque surfaces (buildings, terrain), before any translucent
  draw, as a full-screen triangle at the far plane with the depth test (`SkyRenderer::render`, `behindScene`): only
  the pixels the scene left uncovered are shaded. The sky view (0) only clears to the flat fog colour. In New
  Sorpigal this cut the sky from about 60 µs per frame to the visible share of it (NS_PROF_1: 63 → 19 µs).
- `video.sky_resolution_scale` (0.25-1, ini only) renders the main sky into an offscreen target in view
  `SkyImageView` (238) and upscales it (`fs_sky_upscale`, also behind the scene). Desktop uses 1; the Android
  profile uses 0.5, which is visually indistinguishable. The reduced image is shaded over the whole frame, so with
  the depth-tested full-resolution sky it only pays off when more than about a quarter of the frame is sky: on
  desktop 0.5 measured 0 to +8 µs worse. Android has not been re-measured since.
- 3D-model reflections use a neutral cumulus pattern (`SkyRenderer::environmentSource`), coloured per frame by
  `skyEnvironmentTint`, so time of day costs no environment rebuild. Water glint and sky-fill colours come from the
  preset `water_sun` / `water_sky` values.

## Original skies

Each sky texture the data can select (a continent's weather ladder entry, a custom map sky such as Dagger Wound's
`sunsetclouds`, or an event override) has its own `legacy_<name>` preset, generated from the original painting by
`tools/sky/derive_legacy_skies.py`:

- `assets_source/engine/rendering/sky/legacy/<name>.png` is the original painting as a colour cloud layer (`mode: color`). For open
  skies the background is keyed to transparent, so the Enhanced gradient, sun, moon and stars show through the gaps.
  Fully painted skies (`sunsetclouds`, `stormclds`, `6sky19`, `sky19`, `sky04`, `sky01`, `skycity01`) stay opaque.
- The layer keeps the original sky-plane size (`scale = 64 / logical width`) and drift, with the curved projection
  and horizon haze of the Enhanced sky.
- Each layer is built from a Codex HD repaint of the original when one is approved
  ([`sky_art/hd_masters/`](sky_art/hd_masters/README.md)): same composition and palette, real painted detail, 1024²
  after resampling and edge matching. Without a master the generator falls back to the original at twice its width,
  with the 8-bit dither softened.
- Open skies key out the bluest sizeable colour cluster with its neighbouring shades (a grey cloud-edge tone must not
  win over a sky split into several blues). Alpha comes from a smoothed colour distance, and edge texels take the
  colour of nearby cloud, so the layer has no blue fringe. All filters wrap because the layer tiles.
- Clouds continue down to about one degree above the horizon, crowding together in perspective and fading into
  the horizon haze.
- When more than four cloud layers are loaded, the renderer releases those the current frame does not draw.
- Daytime zenith, horizon and fog colours come from the painting's own sky colour; dawn, dusk and night blend into the
  shared base ramps. `cloud_lit` tints the painting by time of day.
- Fixed skies (`sunsetclouds`) keep their colours at every hour and only dim at night.
- Fog weather washes a painting toward the hazed horizon; rain or snow over a painting adds haze instead of switching
  to the generic rain preset. That haze takes the rain or snow preset's fog colour, so snow reads near-white.
- Untinted fog weather mixes 65% of the original renderer's neutral grey fog (bright by day, dark at night) into the
  preset fog colour. Fog over a brown painting therefore stays grey, as it was in the original.
- At night, cloud colours follow the moon: the moon's height, phase and visibility. Under a new moon clouds drop to
  30% and read as dark shapes over the stars; a bright full moon keeps the preset's night cloud colours.

Re-run the generator after changing the source textures or the base ramps. It rewrites the generated alias and preset
blocks in `sky.yml`, the layer PNGs and `legacy_skies.json`.

## Cooked textures

The renderer loads only cooked `.oytex` files. `tools/cook_sky_textures.py` cooks every source PNG for both profiles
(the desktop build also runs it incrementally, target `openyamm_cook_sky_textures`); run it after any of the sky
generators. Cloud layers keep their mip chain. Every texture `sky.yml` names under `horizon_ring` or `stars`, and the
moon, has one level because those panoramas wrap at the atan2 seam. BC7 measured 46 to 56 dB against the sources.

The horizon ring, night sky and moon are loaded only while the frame draws them, at the same weights `fs_sky.sc`
skips them at, and released when they are hidden. The 8 MB night sky is therefore resident from dusk to dawn only.
Cloud layers stay loaded while drawn, plus up to four recently used ones.

## Map themes

A map's character survives every weather: `themes` in `sky.yml` recolour whichever preset the weather or sky name
selected. `maps` assigns a theme by map file name. Themes come from each map's name, role, terrain tiles and original
sky or fog:

| Theme | Maps | Look |
| --- | --- | --- |
| `scorched` | Ironsand Desert | Hot orange haze and warm fog, matching the original fog tint (230, 184, 136) |
| `volcanic` | Dagger Wound, Hermit's Isle | Light ash haze over the red sky |
| `necrotic` | Shadowspire, Deyja | Dark, desaturated grey-green sky with a sickly sun |
| `mire` | Mire of the Damned | Murky olive haze |
| `swamp` | Tatalia | Humid green-grey haze |
| `haunted` | Evenmorn Island | Cold blue-grey mist ("perm. fog" in the designer notes) |
| `misty` | Misty Islands | Bright sea mist |
| `arid` | Bracada Desert, Dragonsand | Bleached zenith, warm horizon |
| `barren` | Ravage Roaming, Land of the Giants, Sweet Water | Dusty khaki air |
| `ashen` | Mount Nighon, Kriegspire | Grey-red ash over snow and volcanic rock |
| `frozen` | Frozen Highlands | Cold, pale and clean |
| `gloomy` | Blackshire, Barrow Downs | Overcast gloom |
| `tropical` | Regna, Emerald Island | Deeper turquoise |
| `lush` | Murmurwoods, Avlee, Tularean Forest | Slightly richer colour |
| `otherworldly` | Plane Between Planes | Violet sky, fire-coloured sun |

Theme fields:

- `sky_tint` multiplies the zenith, horizon, fog and water sky colours.
- `sun_tint` multiplies the sun glow, sun disc and water glint colours.
- `cloud_tint` multiplies the clouds and painted skies.
- `saturation` (0 = grey) applies to the sky, fog, sun glow and cloud colours.
- `haze` is the minimum wash toward the themed fog colour.
- `stars` scales star brightness.
- `preset` pins a preset regardless of weather.

Plane of Fire, Plane of Air, Plane of Water, the underwater tutorial and Shoals keep their special-flag presets.
`sky theme <name|none|auto>` overrides the theme at runtime. `sky_review.py capture <label> --targets maps` captures
every themed map as Classic, Enhanced without a theme, and themed, at 09:00, 13:00, 19:40 and 23:30.

## Choosing a preset

`selectSkyPreset` resolves, in order:

1. underwater → `special.underwater` (no sky drawn, flat fog);
2. a debug `sky preset` override;
3. `red_fog` → `special.red_fog`, `always_light` → `special.always_light`, `always_dark` → `special.always_dark`;
   then a map theme's pinned `preset`;
4. the resolved weather sky texture name through `aliases` (merged weather ladder entry, custom sky, Dagger Wound
   rule, `SetOutdoorSky`);
5. the MMerge weather ladder position (`weather_ladder`, clear → storm) for names without a preset;
6. `fallback`;
7. rain or snow switch a generic non-stormy result to `special.rain` / `special.snow` (painted skies stay).

Changes cross-fade over `transition_seconds`. Map loads, clock jumps over 30 game minutes and `sky` console commands
snap. Foggy weather hazes the sky toward the preset `fog` colour according to the fog strong distance. A map-authored
fog colour or tint (`out04_1`, MM9 maps) stays authoritative: the world fog uses it, mixed with the sky by
`fog_tint_sky_mix`.

## Preset schema

```yaml
presets:
  my_preset:
    inherits: base            # every value not keyed here comes from the parent
    keys:                     # game time HH:MM, wraps at midnight; colours are linear RGB
      - {time: "12:00", zenith: [0.1, 0.25, 0.62], horizon: [0.55, 0.68, 0.85]}
      - {time: "20:35", horizon: [0.8, 0.36, 0.18]}
    sun_disc_degrees: 1.6
    moon_disc_degrees: 3.4
    moon_texture: moon        # the moon disc's texture; its alpha shapes the disc (a broken moon)
    moon_phase_offset: 0.0    # added to the calendar's phase (0 new, 0.5 full): where the world's moon starts
    below_horizon: fog        # fog | sky (open sky below, Plane of Air) | flat
    fog_tint_sky_mix: 0.25
    horizon_ring: {texture: horizon_ring, opacity: 0.8, height: 0.16}
    stars: {texture: night_sky, density: 0.6, brightness: 1.0, pole_elevation_deg: 55}
    orbit_ring:               # optional; off (opacity 0, no lights) in every shipped MM preset
      opacity: 0.2            # brightness at full star visibility; fades with the stars (a ghost by day)
      width_deg: 10
      color: [0.86, 0.8, 0.9]
      fragments: 2.5          # extra density of the debris trailing behind the moon
      lights: {count: 5, size_deg: 0.12, orbit_minutes: [60, 180], color: [1, 0.82, 0.6], brightness: 3}
    clouds:                   # at most two layers; a list replaces the parent's list
      - {texture: clouds_cumulus, scale: 0.126, speed: 0.0021, direction_deg: 35, coverage: 0.32,
         softness: 0.33, opacity: 1.0, curvature: 0.13}
    storm: true               # keeps its own look in rain; lightning itself comes from the weather
    draw_sky: true
```

Keyed values:

- colours: `zenith`, `horizon`, `sun_glow`, `fog`, `sun_disc`, `cloud_lit`, `cloud_shadow`, `ambient_tint`,
  `water_sun`, `water_sky`;
- scalars: `horizon_exponent`, `sun_glow_exponent`, `sun_glow_strength`, `sun_disc_visibility`, `stars`,
  `moon_visibility`, `aerial_haze`.

`orbit_ring` (2026-10-22, for Hesper's debris ring) draws a procedural planetary ring along the moon's path, a
circle of constant height round the sky, so the moon always hangs in it: banded across its width, clumped along it,
densest just behind the moon. Its `lights` (at most 8) are small points that orbit in the ring, each with its own
lane, start and period between the two `orbit_minutes` (game minutes per turn; the game clock runs at half a
game minute per second), from the light's index and the game time alone, so they are deterministic and need no
save state. Ring and lights scale with the `stars` value and fade near the horizon; the lights pass in front of the
moon. `fs_sky.sc` skips both while `opacity` is 0 and `count` is 0, so presets without the block draw as before.

The loader rejects unknown keys, bad times and out-of-range values, so a broken file disables Enhanced with one
`[AssetLoadWarning] kind=sky_presets` line instead of drawing garbage.

To add a sky:

1. Add a preset that inherits `base`, or an existing weather preset.
2. Map its legacy texture name in `aliases`.
3. Run `openyamm_unit_tests --test-case='*sky*'`. The alias-coverage test reads `continent_settings.txt` and
   `bolster_maps.txt`.

The renderer reads `engine/rendering/sky/` only, so a world cannot replace a sky file by mounting its own; a world's
preset names its own textures instead (`stars.texture`, `horizon_ring.texture`, cloud layers, `moon_texture`).
Hesper's are cooked into its stage (`level_generation/projects/hesper_stage`).

## Assets and provenance

- Cloud layers: `tools/sky/generate_cloud_layers.py`, seamless by construction (spectral fBm and toroidal Worley).
  - R = histogram-equalised density, so `coverage` is the covered fraction of the sky.
  - G = thickness.
  - Seeds and hashes are in `cloud_layers.json`.
- Horizon ring, night sky and moon: Codex image generation from
  [`sky_art/codex/CODEX_BRIEF.md`](sky_art/codex/CODEX_BRIEF.md).
  - Sources, attempts and prompts are in `sky_art/codex/`, outside the runtime package.
  - Runtime files are made by `tools/sky/prepare_sky_art.py` (ring wrap blend and alpha, night-sky pole fade, moon
    crop). Hashes are in `sky_art.json`.

## Checking changes

- Console:
  - `time set HH:MM`;
  - `sky` (status);
  - `sky weather <n|auto>`, `sky name <texture|auto>`, `sky fog <weak> <strong>|auto`;
  - rain, snow, wind and lightning: `weather ...` (see [Outdoor weather](WEATHER_PLAN.md#debug-console));
  - `sky preset <name|auto>`, `sky theme <name|none|auto>`, `sky clear`.

  All overrides are runtime-only.
- Screenshot tours accept per-shot `time: "HH:MM"` and `commands: ["sky weather 5", ...]`.
- `tools/sky/sky_review.py capture <label> --targets mm6,mm7,mm8,specials --style enhanced` captures the review
  matrix into `output/sky_review/<label>/` with contact sheets.
  - `compare <a> <b> <out>` writes side-by-side sheets and mean differences.

## Known limits

- No HDR. The sun disc is the brightest display value, and bloom or glare would need an HDR pass.
- Rain, snow, lightning and thunder belong to the [outdoor weather](WEATHER_PLAN.md); the sky only reacts to them.
- Indoor sky faces (`FaceAttribute::IndoorSky`) still use the original scrolling texture.
- `ambient_tint` is keyed but not yet applied to world lighting. Baked lighting colours are unchanged.
