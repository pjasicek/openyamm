# Projectile visual effects: investigation

Status: investigation, recommendation and an in-game test of two bolts (2026-10-10). See section 7 for what was built.
The fire family design proposal (2026-10-11) is in [PROJECTILE_VFX_FIRE_PROPOSAL.md](PROJECTILE_VFX_FIRE_PROPOSAL.md).
Every other projectile, the asset sources and the first implementation: [PROJECTILE_VFX_ALL_PROPOSAL.md](../PROJECTILE_VFX_ALL_PROPOSAL.md).

**Question:** spell and monster projectiles (fire, air, water, dark bolts and the rest) are drawn as trails of particles.
What is the current best way to draw them that suits OpenYAMM's enhanced retro look?

**Short answer:** build each projectile in layers, the way current action RPGs do:

- a bright **head** sitting exactly on the collision point;
- a continuous textured **ribbon trail**;
- a few **shed particles**;
- the existing **light**;
- a proper **impact**.

All of this should be authored as named effects in the existing effect library, which needs two new features: a
`ribbon` component and velocity-aligned sprites. Each projectile type is bound to its effect through data. Keep the
current recipes as the classic style.

## 1. What we draw now

Projectile presentation lives in `game/fx/ParticleRecipes.cpp` (`projectileFxRecipe`, about 40 recipes) and
`WorldFxSystem::syncProjectileTrails` (`game/fx/WorldFxSystem.cpp`). It reproduces the MM7/MM8 trails:

- **Hanging trail** (fire bolt, fireball, poison, every monster elemental bolt):
  - The projectile's own sprite is hidden (`renderProjectileBillboard = false`).
  - Every 2/128 s the trail drops four stationary, camera-facing `effpar01` blobs: two at the segment midpoint and two
    at the current position, ±4 units apart.
  - Each blob lives 0.75–1.25 s and fades over its last 30%.
  - The result is about 256 particles per second per bolt, and about 250 alive per bolt at any moment. The CPU pool
    holds 4096, so roughly 16 bolts in flight fill it.
- **Render sprite** (fire spike, ice bolt, meteor, incinerate): the native object sprite only, with an impact burst.
- **Segment projectile** (lightning-style bolts): a beam drawn between successive positions. The segment code is
  duplicated in `OutdoorBillboardRenderer.cpp` and `IndoorRenderer.cpp`.
- **Light:** a projectile point light (`projectileRecipeGlowRadius`), and impact lights.
- **Impacts:** native burst recipes. `effect impact-rebind` can swap an impact for a named effect, but only through the
  console.

Separately, the named effect system (`EffectSystem`, `EffectRenderer`, `library.yml`) already supports:

- moving, world-space emitters (`creature_fire_hand`, `creature_air_staff` on actor hand sockets);
- flipbooks (`fireball`, 16 frames);
- additive, alpha and multiply blending;
- model components and sounds;
- `setTransform`, `stop(drain)`, and a browser viewer.

It does not have ribbons, velocity-aligned sprites, gradient-mapped colour, soft particles or bloom.

### What it looks like

Captured in New Sorpigal with the authorised isolated desktop runs and the engine screenshot tour: hostile Regnan mages
(air, water, fire bolts) and Necromancer 307 against friendly archers, viewed from the side. The captures are kept
locally in `output/projectile_vfx/` (`current_side_view.png`, `current_mixed.png`, `current_sheet.jpg`,
`capture_tour.yml`).

- **A string of beads.** Each bolt reads as a dotted line of evenly spaced round dots with gaps between them. There is
  no continuous body, so it looks low-tech at HD resolutions.
- **No head.** The front of the bolt is just another dot, so the dangerous end is not obvious. Riot's VFX guidance calls
  this the "hot point": the end players dodge, which must sit exactly on the collision volume and be the clearest part.
- **The trail hangs too long.** One-second blobs leave a path across the whole battlefield, which reads as a dotted
  arc rather than motion.
- **Elements look alike.** Fire, air, water, dark and mind differ only in tint. The blob, size, motion and timing are
  the same.
- **Fireballs near the camera fill the screen** with large soft orange discs (`current_mixed.png`), with no soft or depth
  fade.

This is faithful to the 1998–2000 look, and it is the right classic mode. It doesn't match the enhanced sky, the 3D
creatures and the shield dome now in the game.

## 2. How current games build a projectile

Modern projectiles, from ARPGs (Diablo IV, Path of Exile, Last Epoch, Grim Dawn) and MOBAs (League of Legends) to Unity
and Unreal VFX packs and tutorials, use the same small kit of layers. Each layer has a separate job.

| Layer | Job | Typical technique |
| --- | --- | --- |
| Hot core | Marks the collision point; the brightest value in the effect | Small additive billboard, nearly white, sometimes stretched along travel |
| Halo or body | Gives the element's colour and size | Larger soft additive billboard or flipbook (fire), slow spin; sometimes a tiny mesh with a fresnel shader |
| Streak | Gives a sense of speed | Billboard stretched along the velocity (axial), its length scaled by speed |
| Ribbon trail | Shows direction and the path just travelled | A camera-facing strip through recent positions; UVs along world distance; scrolling noise × gradient mask; width tapers to the tail; alpha fades with age; a dissolve threshold breaks up the tail |
| Sheds | Character and texture: embers, frost motes, wisps, drips | Few particles that keep part of the projectile's velocity, with drag and gravity per element |
| Light | Lights the ground and walls along the path | A dynamic point light, sometimes flickering |
| Cast flash and impact | Readable start and end | Flash, shockwave ring, sparks, light pulse; for big spells a scorch decal and camera shake |

The guidance behind these layers:

- **Value structure.** Each effect has a white core, a saturated middle and a dark or transparent edge. Many studios
  paint textures in greyscale and colour them through a gradient ramp per element, so one texture set serves every
  element.
- **The trail carries the feel.** A breakdown of a stylised magic missile puts most of the feel in the textured trail,
  with sparkles added on top. A commercial Niagara projectile pack is built from the same parts: cast (muzzle), travel
  and impact effects, with core, trail, spark, smoke and glow layers.
- **Readability before decoration.** The element should read at a glance, with little clutter, and pure white kept for
  what matters most.
- **Trails are sampled by distance, not time,** so slow and fast bolts keep the same texture density. When the
  projectile dies, the ribbon detaches and fades out in about 0.2–0.4 s instead of vanishing.

Sources:

- [Constructing VFX worthy of League of Legends (80.lv)](https://80.lv/articles/constructing-vfx-worthy-of-league-of-legends/)
  — the hot point and the trail's direction cue.
- [League VFX style guide (Riot)](https://nexus.leagueoflegends.com/en-us/2017/10/dev-leagues-vfx-style-guide/)
  and the [VFX Apprentice summary](https://www.vfxapprentice.com/blog/10-league-of-legends-vfx-design-tips) — clarity,
  low clutter, value, colour, shape and timing.
- [Anatomy of a League missile, part 2 (RealtimeVFX)](https://realtimevfx.com/t/anatomy-of-a-league-of-legends-missile-part-2-what-are-we-communicating-with-our-vfx/13062).
- [Robin's Sketchbook (RealtimeVFX)](https://realtimevfx.com/t/robins-sketchbook/9020) — the magic missile built from a
  core and shell, a trail renderer with scrolling painted textures, and sparkles.
- [Niagara magic projectile pack (Fab)](https://www.fab.com/listings/526c5afc-ee43-4d70-a4a7-483b32f2ed36) — the
  muzzle, travel and impact split.

## 3. Options

| Option | What it is | Verdict |
| --- | --- | --- |
| A. Tune the recipes | More, smaller, shorter-lived blobs; add a head blob | Cheap, but still beads. The cost grows with smoothness (the particle pool is already the limit), and every element stays a tint. Not enough on its own |
| **B. Layered named effects with ribbons** | Head + streak + ribbon + sheds + light, authored per element in `library.yml` and bound per projectile type | **Recommended.** It matches modern practice, reuses the effect library, loader, viewer and moving emitters, needs fewer particles than today, and is pure presentation |
| C. 3D mesh projectiles | Modelled arrows, rock chunks, ice shards, a small fresnel orb | Add per case on top of B: `EffectModelDefinition` already exists. Right for physical projectiles (arrows, rock blast, ice shards, blades), wrong as the base for energy bolts |
| D. HD flipbook sprites only | Restore the native projectile sprites at higher resolution and show them | Keeps the original identity, but a sprite with no trail looks static at modern frame rates. Useful as the body layer of B for spells with distinctive native art |

## 4. Recommendation

Use B as the enhanced style, and add C where a physical object flies:

1. **One projectile effect per element and spell family,** authored in the effect library, using:
   - a hot core;
   - a halo, or a flipbook body for fire;
   - an optional velocity streak;
   - a ribbon;
   - sparse sheds.

   The head's centre is the collision centre (`projectileRecipeAnchorOffset` already gives it).
2. **Gradient-mapped greyscale textures:** a few shared trail-noise, core and wisp textures, coloured by a per-element
   ramp (white → element colour → dark or transparent). This follows the colour-tier rule used for the 3D creatures:
   shared textures plus palette ramps, not a baked copy for each colour.
3. **Restrained density.** Keep the MM element colours and the readable silhouette, but use no screen-filling clutter.
   Players fight many casters at once, so the head must stay readable inside a crowd: pure white goes only on the
   core.
4. **Bound through data:** `engine/effects/projectiles.yml` maps each recipe name (`projectileRecipeFromName` already
   exists) to its flight and impact effects. This replaces the console-only impact rebind with authoritative data.
5. **A user setting,** `video.projectile_fx = classic | enhanced`, like `video.sky_style`. Classic keeps the current
   recipes unchanged. With enhanced, a projectile bound to an effect skips the native trail; an unbound one keeps its
   recipe, so the work can be done one element at a time.

### Per-element look

| Element / family | Head | Ribbon | Sheds and extras |
| --- | --- | --- | --- |
| Fire bolt, fireball, monster fire | Fire flipbook body with a hot yellow-white core | Short, wide, noisy, eroding orange-to-red tail | Embers with gravity; 1–2 alpha smoke puffs; flickering light |
| Air, sparks, lightning | Small white core with a blue halo | Thin, jittering electric ribbon (lateral offsets re-randomised every few frames) | Short-lived spark crackle; light flicker; could replace the duplicated segment beam |
| Water, ice bolt | Sharp pale core; an ice-shard mesh (C) for ice bolt | Smooth, glassy, pale-blue ribbon, little noise | Frost motes falling slowly with gravity |
| Earth, rock blast | Tumbling rock mesh or sprite, no glow | None, or a faint dust ribbon (alpha) | Dust puffs and grit; no light |
| Body, poison, toxic cloud | Wobbling green blob | Thick ribbon with slow bubbling noise | Dripping droplets; low toxic mist |
| Mind | Pulsing yellow core | Thin ribbon with a slow sine sway | Two orbiting motes |
| Spirit | Soft gold-white core | Wispy, wide, low-alpha ribbon | Rising wisps |
| Light, sunray | Very bright white core with a long streak | Long, straight, thin ribbon | Short rays; strong light |
| Dark | Dark core (alpha blend) with an additive violet rim | Smoky ribbon: dark alpha body with a violet additive edge | Black wisps that sink slightly |
| Arrows, bolts, cannonball | Mesh (C) | Faint air streak only | None |

## 5. Engine work

All of this is shared FX code; the only indoor and outdoor hooks are the existing calls into the transparent view.

| Item | Where | Notes |
| --- | --- | --- |
| Flight binding | `WorldFxSystem::syncProjectileTrails` | For a bound recipe: spawn the effect at first sight of the projectile, call `setTransform` with position and travel direction each frame, and `stop(drain)` when it expires. Skip the native trail. Keep the light |
| Binding data | `engine/effects/projectiles.yml` (new) | Recipe name → `{flight, impact}`. Validate effect ids at load, like the actor events' `effects` |
| `ribbon` component | `EffectDefinition.h`, `EffectDefinitionLoader`, `EffectSystem` | Parameters: width (with a taper curve), lifetime, sample distance, texture, gradient, UV scroll, erosion. Store a per-instance ring of samples taken by distance; after a stop, the samples age out |
| Ribbon drawing | `EffectRenderer` plus a new `fs_effect_ribbon` shader | A camera-facing strip (expanded along cross(tangent, to-camera)) with u = world distance. One transient vertex buffer for all ribbons: at 24 samples, 48 vertices per ribbon |
| Velocity alignment | `EffectSpriteAlignment::Velocity` | The particle renderer already has `VelocityStretched`; bring the same logic to effect sprites and emitters, driven by the instance's travel direction |
| Gradient colour | Effect shader, plus a `gradient:` key | Sample greyscale × ramp (a small 256×N ramp texture); keeps one texture set for all elements |
| Viewer support | `re_mm8/mm9_vfx/viewer` | Ribbon and velocity alignment in the JavaScript preview, so the effects can be authored there |
| Later (optional) | `CinematicGrading`, transparent pass | Soft particles: depth is only readable with AO on, so this needs a detached-depth pass. A small half-resolution bloom would lift every effect and the shield dome. Neither is needed for the first version |

There are no gameplay, save or multiplayer changes: everything derives from `GameplayProjectilePresentationState`.
The cost is lower than today: one ribbon (48 vertices) plus about 10–30 shed particles per bolt, instead of about
250 live blobs.

### Example authoring shape (proposed, not final)

```yaml
# engine/effects/projectiles.yml
schema: openyamm.projectileEffects.v1
projectiles:
  FireBolt:        {flight: openyamm:fx/projectile/fire_bolt, impact: openyamm:fx/ember_impact}
  MonsterFireBolt: {flight: openyamm:fx/projectile/fire_bolt, impact: openyamm:fx/ember_impact}
  MonsterAirBolt:  {flight: openyamm:fx/projectile/air_bolt}
```

```yaml
# authored/library.yml
- id: openyamm:fx/projectile/fire_bolt
  duration_seconds: 30
  components:
  - {id: 1, type: sprite, sprite_resource: openyamm:effect-sprite/glow, blend: additive,
     scale_keys: [{time: 0, value: 0.3}], color_keys: [{time: 0, rgb: [255, 240, 205], transparency: 0}]}
  - {id: 2, type: sprite, sprite_resource: openyamm:effect-sprite/fireball, blend: additive,
     alignment: velocity, stretch_u: 1.6, scale_keys: [{time: 0, value: 0.9}]}
  - id: 3
    type: ribbon
    texture: openyamm:effect-texture/trail_noise
    gradient: openyamm:effect-gradient/fire
    blend: additive
    width_keys: [{time: 0, value: 30}, {time: 1, value: 4}]   # head to tail
    lifetime_seconds: 0.25
    sample_distance: 16
    scroll: [-1.8, 0.0]
    erosion_keys: [{time: 0, value: 0.0}, {time: 1, value: 0.8}]
  - {id: 4, type: sprite_system, sprite_resource: openyamm:effect-sprite/spark, particle_space: world,
     blend: additive, sprites_per_emission: 1, emission_interval_seconds: 0.04,
     particle_lifetime_seconds: 0.45, emission_shape: sphere, radius: 6, velocity: 30}
```

## 6. Suggested next step

Run one in-engine spike before committing to the whole table:

1. Add the ribbon component, velocity alignment and the flight binding.
2. Author **fire bolt** (body, ribbon, embers) and **monster air bolt** (thin electric ribbon).
3. Capture them beside classic with the same tour used for the captures above (`output/projectile_vfx/capture_tour.yml`):
   - New Sorpigal;
   - Regnan mages against friendly archers;
   - `debug.immortal=true`.

Judge readability in a crowd and at distance, the frame cost, and whether the look sits well with the HD terrain and
3D creatures. Only then author the remaining elements. Physical meshes (arrows, ice shards, rock) and bloom are separate
follow-ups.

## 7. The in-game test (implemented)

Fire bolt (party and monster) and the monster air bolt now fly as layered effects in the enhanced style. Every other
projectile keeps its classic trail.

| Piece | Where |
| --- | --- |
| `ribbon` effect component | `EffectDefinition.h`, `EffectDefinitionLoader.cpp`, `EffectSystem.cpp` (`updateRibbons`) |
| Ribbon drawing | `EffectRenderer::renderRibbons`, `vs_effect_ribbon.sc`, `fs_effect_ribbon.sc` |
| `alignment: velocity` sprites | `EffectSystem` (travel direction from `setTransform`), `EffectRenderer` `writeQuad` |
| Flight binding | `engine/effects/projectiles.yml`, `ProjectileFlightBindings.cpp`, `WorldFxSystem::syncProjectileFlightEffect` |
| Setting | `video.projectile_style = enhanced \| classic` (Settings, Video, World detail, Projectiles) |
| Effects | `openyamm:fx/projectile/fire_bolt` and `openyamm:fx/projectile/air_bolt` in `effects/authored/library.yml` |
| Textures | `glow`, `trail_noise`, `trail_electric`: original procedural art from `tools/fx/generate_projectile_textures.py` |

### Ribbon parameters

| Parameter | Meaning |
| --- | --- |
| `lifetime_seconds` | How long a sample lives |
| `max_length` | Cap on the trail's length. Fast bolts need it: lifetime alone gave trails across the whole battlefield |
| `sample_distance` | Distance between samples |
| `width` with `width_keys` | Strip width, shaped from head (0) to tail (1) |
| `color_keys` | Colour and transparency from head to tail |
| `texture_length` | World units per texture repeat |
| `scroll_speed` | Texture repeats per second, flowing towards the tail |
| `fill` | Solid body under the noise: about 0.15–0.35 for flame, 0 for pure arcs |
| `erosion` | How much the noise dissolves the tail |
| `core` | A white-hot line along the centre |
| `jitter` and `jitter_rate` | Sideways lightning displacement and how often it changes; the head stays put |

### How flights and trails behave

- **Spawn and follow.** A projectile's effect spawns the first time the projectile is seen, and follows it every
  frame.
- **When the projectile ends.** The effect drains: the head disappears at once, and the ribbon and sheds fade out.
- **What stays from the recipe.** The recipe's light and impact are unchanged.
- **Previews.** The browser viewer skips ribbons.

### Results

The comparison is in `output/projectile_vfx/comparison.png` (local captures, same tour as section 1, both styles).

- **Fire bolt.** It reads as a fireball head on the collision point, with a short flame tail that erodes into embers.
- **Air bolt.** It reads as a small white core with a thin crackling arc.
- **Classic trails alongside.** The bead trails that remain in the enhanced frames are unbound recipes: the Regnan
  Archmage's Fireball spell, the Sorcerer's flat yellow Lightning Bolt beam and Poison Spray.
- **Next candidates.** Those unbound recipes are the obvious next bindings.

Verification:

- normal build;
- full unit suite;
- isolated desktop captures in New Sorpigal for both styles.

No GPU performance measurement was made. Each bolt costs:

- one ribbon draw call for the fire bolt, two for the air bolt;
- a few dozen particles, instead of about 250.

### Open points

- **Tuning.** All values are first-pass, judged at about 900 units' distance.
- **Close range.** A close-up review still needs doing.
- **Lightning beam.** The air ribbon could replace the native segment beam of Lightning Bolt.
- **Impacts.** They are still the recipe bursts; `projectiles.yml` has no `impact` key yet.
- **Bloom and soft particles.** These would lift the heads further, but are not needed.
