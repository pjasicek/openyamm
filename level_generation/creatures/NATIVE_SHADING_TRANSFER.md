# Native shading transfer (Claude, 3D creature textures)

Carry a sprite's prerendered shading and palette colours onto a 3D creature's texture. Tool:
[`claude_shared/native_shading.py`](claude_shared/native_shading.py). It is an optional step between the Meshy
retexture and the tier ramps of [creature textures](CLAUDE_CREATURE_TEXTURES.md). Use the decision guide below
before applying it.

## Origin

MM6 Patrol Unit (`mm6_rob1_claude/`), 2026-10-08. Next to its sprites the model read flat and washed out, with no
sense of its 3D structure (`mm6_rob1_claude/review/look/compare_native_2158.png`). Two rounds of global brightness
gains (darker, then lighter) did not fix it. The sprite's 3D look comes from **where** light and dark sit, not from
overall brightness, and Meshy paints evenly lit, pastel textures. After the transfer the user's verdict was "MUCH
better" (`review/look/look_v5.png`: left 3D, top right sprites, bottom right the state before).

## What the sprites have that Meshy textures lack

Measured on the robot. Compare the same regions on any creature before deciding:

1. **Lighting from above, built in.** The top cap and upper ring are bright (sRGB luminance 0.4–0.53); the belt,
   lower ring and lower cap are dark (about 0.2). That vertical contrast is most of the 3D read.
2. **Dark materials whose shine is in highlights.** The chrome rings are dark warm grey with white glints, not a
   light mid tone.
3. **Saturated palette colours.** They are not the pastel of an evenly lit texture.
4. **A 1-px dark outline.** In every view the outermost silhouette pixel is about 25 % darker than its neighbours
   (prerendered against black), with a slightly brighter band two pixels inside. A texture cannot carry this; it needs
   a shader or outline pass (not done yet).

## How it works

1. **Measure** (`native_shading.py measure <config.json>`). Native frames in every tier palette are read. Pixels in
   the central band of each view are kept; the silhouette rim is skipped because its shading is a rim effect. Each
   pixel gets a body coordinate and a region. Outputs, written to the config's `out` folder:
   - `profile.json`: the reference palette's median luminance per coordinate bin, overall and per region;
   - `pixels.npz`: the same pixels in every palette, aligned, with coordinate and region;
   - `profile.png`: a preview strip.
2. **Shade** (in the project's compose script, after the Meshy base is loaded and cleaned):
   `NS.shade(base, coord, region, profile, scale, detail_strength, detail)`. Inside a region, the base becomes the
   native brightness at each texel's coordinate, as grey, times the base's own local detail (a high-pass ratio from
   `NS.detail_of`). `amount` < 1 blends with the original. The texel coordinate comes from the rest-pose 3D position
   (`NS.texel_coordinate`, from the `uv3d.npz` rasterisation every compose script already makes).
3. **Ramps** (in the project's `tier_ramps.py`):
   `NS.transfer_ramps(base, weights, pixels, region_for, variants, reference, gain, chroma)`. For each ramp stop,
   the reference-palette pixels nearest in luminance are read in each tier's palette. That transfers the palette swap
   exactly, with no hand-tuned gains per tier, which matches how MM6–MM8 tiers work. The output goes straight into
   `region_variants.py`.

Then grade lightly (`grade_basecolor.py --local 0.4 --contrast 1.05 --saturation 1.0`, because the contrast is
already in the base) and build as usual.

Robot example: config `mm6_rob1_claude/native_shading.json`, use in `scripts/compose_rob1.py` and
`scripts/tier_ramps.py`.

## Configuration choices

- **Coordinate.**
  - `elevation`: degrees on a sphere around the body centre. Use it for round, upright bodies (robot, floating eye,
    slimes, beholder-like heads). The texel side needs the centre.
  - `height`: 0 at the lowest opaque row, 1 at the highest. Use it for any upright body seen from the side (a
    creature's torso, a totem). The texel side needs the rest-pose z range of the same part.
  - Other mappings (distance from the head along a quadruped's spine, height on the body only) can be added to
    `_sample_view` and `texel_coordinate` together.
- **Views.** Use views without front-only features: the robot's front views pass through its V notch and eye, which
  read as bright "cap" pixels at band heights. Side, rear three-quarter and back were used.
- **Regions.** Use coordinate bands that follow the 3D model's parts (the robot: belt |e| < 6.5°, rings
  6.5–30°, caps beyond). The restored mask channels (`masks_2x`) did **not** follow the robot's parts (the
  "shell" channel reached into the caps), so check them before trusting them.
- **Camera elevation** (elevation mode). The sprites are rendered from above (8–9° on the robot), so the equator
  projects below the silhouette centre. Measure it per view from a band at a known elevation with
  `camera_reference` (the robot: the red belt, `channel: 0`, `ratio: 2`), or give a number.
- **Per-region scale.** The median per bin averages the highlights into the mid tone. Dark shiny materials need a
  lower scale (robot rings ×0.62), so their shine comes from glints (specular, an edge highlight) and not a light
  mid tone.
- **Detail strength.** 1.0 keeps Meshy's surface detail (etching, scales, fur strands); 0.3–0.5 for smooth parts.
  Meshy's colour variation inside a region is replaced; only its luminance detail survives.

## When to use it

Use it when **all** of these hold:
- the model reads flat, washed out or pastel next to its sprite in the same place (capture both, same camera), and a
  region-by-region comparison shows the sprite's shading is in different **places**, not just brighter or darker;
- the creature mostly stays upright and turns about its vertical axis (walkers, hoverers, floaters), so lighting
  from above stays on top;
- the body has a clear coordinate (round or upright) and the regions follow it;
- the tiers are palette swaps of one sprite (they are in MM6–MM8).

Use it **partially** (`amount` 0.3–0.7, or on the body regions only) when:
- the creature lies down, rolls or banks in some clips (quadruped deaths, flyers): the baked top light then sits on
  a side. A partial bake keeps some contrast with less error;
- limbs, wings or tails have no clean coordinate: shade the torso and head only, and leave limbs to the normal
  texture and AO;
- the creature has a separate head texture set (faces): do not shade faces from a body profile.

Do **not** use it when:
- the Meshy texture already reads like the sprite (check before adding work);
- the views disagree in lighting (very different light per view) or have heavy front-only details that cannot be
  excluded;
- the art direction wants dynamic lighting to dominate (for example a creature meant to be lit by its own fire).

## Trade-offs

| Gain | Cost |
|---|---|
| Matches the sprite's look and contrast in every tier | Lighting is fixed in the texture: a light from below does not brighten the underside, and the engine shades again on top (double shading). Hand-painted games accept the same. |
| Tier colours transfer exactly from the palettes, with no per-tier gain tuning | Meshy's colour variation inside a region is lost (only its luminance detail is kept) |
| No Meshy credits; it reruns in seconds | Parameters per creature: coordinate, regions, views, camera elevation, region scales |
| Works with the shared-skin and ramp contract | The profile is a median per bin, so view-dependent effects (chrome glints at the sides, the silhouette outline) are not carried; they need shader work |
| Same mesh, rig and clips; only textures change | It holds while the pose keeps the body upright; tilted poses show the baked light on the wrong side |

## Pitfalls found on the robot

- Global gains do not fix flatness; first find where the sprite's light and dark sit.
- A partly metallic "chrome" material turned chalky and uneven indoors: a metallic texel loses its diffuse colour
  and depends on the sky reflection. The fix was glossy, not metallic.
- Bake AO without moving parts. The eye lens slides along the belt, and its rest-pose occlusion left a dark patch
  (`mm6_rob1_claude/scripts/bake_ao_no_eye.py`).
- A glowing part (eye) works as its own material with an emissive factor per tier
  (`mm6_rob1_claude/scripts/eye_emissive.py`). The renderer adds the material's emissive colour after lighting.
- Dark lip and crevice faces, plus a bright line on rounded outer edges, recover part of the sprite's outlined look.

## Applied so far

| Creature | Coordinate | Regions | Amount | Result |
|---|---|---|---|---|
| Patrol Unit (`mm6_rob1_claude`) | elevation | bands by geometry | 1.0 | user: "MUCH better" |
| Flying Eye (`mm6_bh_claude`) | height | restored masks | skin 0.5, face 0.7, horns/teeth excluded | modest step; the old texture was already close |
| Mage (`mm6_pmn2_claude`) | height | restored robe mask | 0.65, robe only | cleaner tier colours, closer to the sprites |
| Cockatrice (`mm6_ckt_claude`) | height (feet to neck top), front and back views | body feathers (body, tail, neck; brown native pixels of the central column) | 0.85 + body ramp by palette transfer | body and tail darker and browner; a small step in game |
| Hydra (`mm6_hyd_claude`) | none (necks bend in every clip) | necks and body: ramps by palette transfer only | — | necks take some per-neck tint; barely visible in game |
| Spider (`mm6_spi1_claude`) | height (all standing views) | chitin (existing quantile ramps kept) | 0.7, detail 0.5 | softer, browner leg bands, closer to the sprite; detail 0.35 lost too much striping |
| Bat (`mm6_bat_claude`) | none (banks and flaps) | membrane: transfer_ramps; body: ramps by luminance rank | — | golden/blue/red wings with the sprites' light-to-dark range; body darker, warmer mauve |
| Cleric (`mm6_cle_claude`) | height checked: medians matched within 0.05, not used | cloak, tunic | — | contrast transfer instead: inner cloak ×0.5, broad shading stretched (cloak ×1.8, tunic ×1.6); dark inner cloak like the sprites |
| Titan (`mm6_ttn1_claude`) | height (all standing views) | armour (not trim, skin or head set) | 0.7, detail 1.0 | darker greaves and waist, light chest; B/C armour ramps by rank for the teal sheen, A by luminance |

Lessons from the flying eye and the mage:
- `transfer_ramps` matches by absolute luminance: when the 3D region is brighter than every native pixel (the bat's
  body) it only reads the sprite's highlights. Match by luminance rank instead (`mm6_bat_claude/scripts/native_tiers.py`).
- A full transfer on a region that is very dark in the sprites (the eye's back skin) loses the sculpt. Blend it.
- Check the height profile against the 3D texture before shading: on the cleric the medians already matched, and the
  gap was the spread (a near-black cloak interior, wider cloth contrast). Darkening an inner cloth shell shows every
  place it crosses the outer one, so keep the shells apart first (`mm6_cle_claude/scripts/shell_weights.py`), and
  pad the islands so the ramps never see Meshy's light gutter fill (`mm6_cle_claude/scripts/prepare_textures.py`).
  It also shows every face whose island is on the wrong side: shade the faces that are physically inside
  (`mm6_cle_claude/scripts/cloak_sides.py`), not the inner UV islands; per-face normal labels mix the sides near
  hems and edges.
- One profile per region must cover parts that the sprite shades alike. The eye's horns are lighter than its face,
  and a humanoid's skin, leather and boots share heights, so leave such parts out or give them their own region.
- On humanoids, the palette transfer (ramps) does most of the work; the shading part is secondary.
- Check tier previews offline with `claude_shared/tier_textures.py` (bakes the shader's ramp maths) and
  `claude_shared/render_tier_views.py` (Blender front and three-quarter renders per texture).

## Industry context

These techniques are established, not workarounds. Painted or baked lighting in the albedo is the hand-painted style
(World of Warcraft, Dota 2, League of Legends, most pre-2010 games); recolouring by luminance through a ramp is
gradient mapping; dark crevices and lit edges are the curvature and cavity passes of every texturing tool. Taking the
values from the original art is ordinary reference matching. It becomes a workaround only where the engine lacks a
feature (environment reflections or an outline shader for creatures). If those are added, the bake can be made more
neutral (`amount` < 1).
