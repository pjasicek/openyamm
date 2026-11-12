# Mist (ground mist and local fog volumes)

A map may carry a coloured mist with depth: up to four **layers**, each lying on a height and thinning upward, and
soft local **volumes**. Both are worked out along the view ray inside the shaders that already fog, so there is no extra render
pass, no depth read and no new render target; it works with every anti-aliasing mode and on Android. It is opt-in per
map through the scene's `mist` block: a map without it packs zeros and its shaders skip the work on one uniform test.

First users (2026-11-12): Shadowspire (`worlds/mm8/maps/out06_mist.scene.yml`, a grey-green layer over the lowlands),
the Necromancers' Guild (`d19_mist.scene.yml`, a green layer over the lower halls), the Troll
Tomb (`d13_mist.scene.yml`, a layer on each of three floors) and Deyja (`worlds/mm7/maps/7out05_mist.scene.yml`, three
layers for land on three heights).

Which other MM6-MM8 maps would suit it, with starting heights: [Mist candidates](MIST_CANDIDATES.md).

This is not volumetric lighting: the mist takes no light from torches or the sun's shadows. See "Limits".

## Data: the scene's `mist`

Top level of an indoor or outdoor `<map>.scene.yml` or of an overlay (`<map>_<name>.scene.yml`; an overlay's `mist`
replaces the base's). The same block and parser for both (`game/maps/MistYml.cpp`); the editor's scene writers keep it.

```yaml
mist:
  layer:
    color_rgb: [142, 160, 150]   # display colour, 0..255
    base_height: 128             # world z at and below which the mist is densest
    falloff_height: 260          # height above the base over which it thins to 37 %
    visibility: 2600             # distance through the densest mist that hides 63 %
    max_opacity: 0.88            # optional (0.9): the most of a pixel it may cover
    noise: 0.45                  # optional (0.35), 0..1: how far drifting patches thin and thicken it
    noise_size: 1800             # optional (1536): world size of a patch
    drift: [16, 7]               # optional ([14, 6]): the patches' drift, world units per second
    follow_daylight: true        # optional (true): the colour darkens with the map's light
  volumes:
    - position: [0, 5750, -720]  # centre
      radius: [380, 380, 190]    # half extents of the ellipsoid, or one number for a sphere
      color_rgb: [150, 92, 205]
      visibility: 420            # as the layer's, at the centre; the density falls to nothing at the surface
      max_opacity: 0.6           # optional (0.9)
      noise: 0.4                 # optional (0.25)
      follow_daylight: true      # optional (true)
```

**Several layers** (`layers`, at most four, instead of `layer`), each with the keys above and an optional `depth`:

```yaml
mist:
  layers:
    - {color_rgb: [150, 156, 150], base_height: -1510, depth: 40, falloff_height: 100, visibility: 700}
    - {color_rgb: [150, 156, 150], base_height: -718, depth: 40, falloff_height: 90, visibility: 800}
```

`depth` is the height below the base over which the layer thins to 37 %. Without it a layer stays at its densest all
the way down, which is right for one outdoor layer and wrong for a dungeon's upper floor: with a small depth (about
40) a floor's mist ends inside its own floor and the floors beneath stay clear. Outdoors a larger depth (150-200) lets
a layer lie on a plateau without filling the valleys under it.

`layer`, `layers` (not both) and `volumes` are each optional. An unknown key or a value out of range fails the scene's load. `color_rgb`,
`base_height`, `falloff_height` and `visibility` are required for a layer; `position`, `radius`, `color_rgb` and
`visibility` for a volume.

**Tuning.** `visibility` is how far you see inside the mist; `falloff_height` how tall it stands (about man height,
100-150, for a floor mist; a few hundred for a valley haze). Outdoors set `base_height` near the low ground: hills rise
out of it. Any colour works; parts of different colours mix by how much each covers.

**Daylight.** Outdoors a part that follows the daylight is scaled by the hour's and weather's ambient light (1 at a
clear noon, about 0.2 at night). Indoors it is scaled only on a map with a scene `daylight` block, by the same measure
a fog with `follow_daylight` takes.

## Player settings

Settings, Video, Environment: **Mist** (`video.mist`, on by default) and its **Density** (`video.mist_strength`, 0-200 %
of each map's authored density, 100 by default). The density scales every layer's and volume's `1 / visibility`
(`packMistUniform`'s `strength`); colours, heights and the most a part may cover stay as authored. The rows come from
`engine/ui/menu/settings_catalog.yml` (`tools/generate_settings_layouts.py` rewrites the layouts).

## Rendering

`game/render/Mist.h` holds the data and packs it per frame (`packMistUniform`); `game/shaders/mist.sh` draws it.

- **Uniform.** The mist rides in the shared `u_skyFog` array after the sky's eight vectors (`SkySurroundings::mist`,
  `packSkyFogUniform`): two for the counts, three per layer and three per volume, 40 in all. Every site that sets the sky fog
  therefore sets the mist, and every shader that includes `sky_common.sh` has it.
- **Layers.** The density falls off exponentially above the base and, with a `depth`, below it (constant below
  without one); its integral from the eye to the pixel has a closed form, split where the view crosses the base
  (`mistLayerDepth`). So looking along the ground hides more than looking down from above,
  and the eye may be inside or over it.
- **Volumes.** An ellipsoid whose density is `1 - r^2` (centre to surface); the integral over the part of the view
  ray inside it is a cubic (`mistVolumeDepth`). The shaders take the six nearest (`MaxMistVolumes`); with more on a map,
  one fades out before it is left out (`selectMistVolumes`).
- **Patches.** Two sizes of value noise drifting apart thin and thicken the mist. Seen from above they lie where the
  view enters the layer, so they hold their place as the eye moves.
- **Where it is applied** (`mistApply`, after each shader's own fog, display space): outdoor terrain, buildings, grass
  and decorations, water, billboards, 3D models, the sky (`mistApplySky`: the view runs on to where the layer has
  thinned out, so the horizon takes the mist); indoor faces, indoor terrain and indoor water. Glows and other additive
  light fade by `mistClear` instead of taking the colour.
- **Indoors** the mist is drawn by the fog variants of the face and water programs. A map with mist and no scene fog
  loads them with a fog too far to show (as a map with only a water volume's fog does).

## Wisps (mist close to the eye)

The shader mist needs distance to show, so the air right around the party reads as clear. `game/fx/MistWisps.cpp`
adds what is missing: about 56 pale streaks in the shared particle system (`FxParticleTag::MapMist`), within 650 units
of the eye, only where the map's mist is (`sampleMist`: the layer's density at their height, or inside a volume).

- World-anchored: a wisp stays where it appeared, drifts with the layer's `drift`, fades in over 2.5 s and out over the
  second half of its 8-13 s. Wisps left more than 1 300 units behind (a teleport) are dropped and a new set appears.
- Shape: low and long (`VelocityStretched` along the drift), about waist height while the eye is in the mist, so the
  quads stay off the floor (they have no soft depth fade and would cut a line into it); at the mist's top when the eye
  is above it. A hill above the layer has none.
- Colour: the mist's, lifted 55 % toward white (in the mist's own colour they cannot be told from it), opacity up to
  0.7 by the local density, with the same daylight scale.
- Both views call `MistWisps::update` just before `ParticleRenderer::renderParticles`; nothing runs on a map without
  mist. The particle renderer's own view fade stops one from covering the screen as the party walks through it.

They are tuned by constants in `MistWisps.cpp` (`WispOpacity`, sizes) and `MistWisps.h` (`TargetCount`,
`SpawnRadius`), not per map. The player's `video.mist_wisps` (INI only) turns them on: they are off by default
(2026-11-12, the mist was judged fine on its own).

**Cost.** Without mist: one uniform comparison per pixel in the shaders above. With a layer: two `exp`, and two noise
reads where it is visible; each volume a square root and a cubic. Not measured on hardware yet.

## Limits

- **No lighting.** Torches, spells and the sun's shadows do not light or shade the mist. Light shafts need either
  authored cards or a ray-marched pass (not built).
- **Particles, weather and effect sprites** are not misted (they are not fogged either).
- **Wisps do not know walls or floors**: one may cut into a wall or a slope with a soft edge.
- **Layers are flat.** Where the ground under one varies by hundreds of units (Deyja's plains), the mist is thin in
  places and thick in others; a terrain-following base is not built. At most four layers.
- **Volumes are ellipsoids**: they do not follow walls, so one larger than its room shows in the next room.
- **No script control** yet (`evt.SetFog` has no mist counterpart).
- The Vulkan (SPIR-V) and Metal shader builds were not compiled on the machine that wrote this; GLSL 1.50 and ESSL
  3.00 were.

## Tests

`./build/tests/openyamm_unit_tests --test-case='*mist*'`: parsing and refusals, the layer's and a volume's cover along
rays (`mistLayerCover`, `mistVolumeCover` mirror the shader terms), the choice and fade of volumes, the uniform's
layout. Captures: `output/mist_test/out06_tour.yml`, `d19_tour.yml` (screenshot tours).
