# Particles, Lights, And Shadows Implementation Plan

## Purpose

This document defines the concrete implementation plan for the FX subsystem
needed to match original MM8 behavior while leaving the engine in a cleaner and
more extensible state than OpenEnroth.

The target is:

- preserve MM8-visible behavior
- avoid cloning OpenEnroth architecture directly
- separate particles, dynamic lights, shadows, and trigger logic cleanly
- keep the implementation suitable for a likely successor engine reusing this
  codebase

This document is intentionally detailed and implementation-oriented.

## Scope

This plan covers:

- world particles
- projectile trail and impact FX
- monster buff-cast sparkles
- decoration and sprite fire/trail emitters
- dynamic lights from spells, projectiles, decorations, and glow metadata
- billboard contact shadows
- static baked outdoor lighting inputs
- data ownership for FX behavior
- performance constraints and rollout order

This plan does not cover:

- full shadow maps
- global physically based lighting
- indoor baked lighting implementation details
- advanced post-processing beyond existing fog and UI overlays

## Reference Sources

Behavioral reference comes from the local OpenEnroth checkout only.

Main OE references:

- [ParticleEngine.h](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Graphics/ParticleEngine.h)
- [ParticleEngine.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Graphics/ParticleEngine.cpp)
- [SpellFxRenderer.h](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/SpellFxRenderer.h)
- [SpellFxRenderer.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/SpellFxRenderer.cpp)
- [SpriteObject.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Objects/SpriteObject.cpp)
- [BaseRenderer.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Graphics/Renderer/BaseRenderer.cpp)
- [Outdoor.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Graphics/Outdoor.cpp)
- [Indoor.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Graphics/Indoor.cpp)
- [Spells.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Spells/Spells.cpp)
- [ObjectList.h](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Objects/ObjectList.h)
- [Sprites.h](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Graphics/Sprites.h)

Current OpenYAMM integration points:

- [OutdoorWorldRuntime.h](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorWorldRuntime.h)
- [OutdoorWorldRuntime.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorWorldRuntime.cpp)
- [OutdoorBillboardRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorBillboardRenderer.cpp)
- [OutdoorRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorRenderer.cpp)
- [OutdoorPresentationController.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorPresentationController.cpp)
- [ObjectTable.h](/home/pjasicek/github/OpenYAMM/game/tables/ObjectTable.h)
- [ObjectTable.cpp](/home/pjasicek/github/OpenYAMM/game/tables/ObjectTable.cpp)
- [SpriteTables.h](/home/pjasicek/github/OpenYAMM/game/tables/SpriteTables.h)
- [SpellFxTable.h](/home/pjasicek/github/OpenYAMM/game/tables/SpellFxTable.h)
- [MapAssetLoader.cpp](/home/pjasicek/github/OpenYAMM/game/maps/MapAssetLoader.cpp)

## What OpenEnroth Actually Does

OpenEnroth does not have one unified authored FX system.

It is split into several distinct layers:

1. Generic particle engine
- particle pool
- particle update
- particle draw submission
- basic flags like dropping, rotating, ascending, bitmap, line, sprite

2. Separate trail particle generator
- small dedicated trail-dot system
- not the same as the main particle pool

3. Hardcoded spell FX renderer
- projectile trail recipes
- projectile impact recipes
- buff cast sparkles
- sphere and ring effects
- mobile light spawning for some spell sprites

4. Object/decor emitter behavior
- object flags such as trail fire, trail line, trail particle
- decoration flags like emits fire

5. Dynamic lights from sprite-frame glow
- actor, object, and decoration sprite frames can carry glow radius
- render path turns glow radius into dynamic lights

6. Portrait spell FX
- separate from world particles
- spell id mapped to portrait icon animation

The important point is:

- OE behavior is compatible and useful
- OE architecture is not the design target

## OE Data And Behavior Mapping

OpenEnroth uses several separate mapping sources.

### Spell Id To Spell Sprite

OE maps spell id to sprite id in code:

- [Spells.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Spells/Spells.cpp#L35)

This is the identity of the world spell projectile or world spell effect sprite.

### Sprite/Object Entry Metadata

OE object metadata carries:

- object id
- radius
- height
- flags
- sprite id
- lifetime
- particle trail color
- speed

Defined in:

- [ObjectList.h](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Objects/ObjectList.h#L34)

Important FX-relevant flags:

- `OBJECT_DESC_TRAIL_PARTICLE`
- `OBJECT_DESC_TRAIL_FIRE`
- `OBJECT_DESC_TRAIL_LINE`

These drive generic sprite trail behavior in:

- [SpriteObject.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Objects/SpriteObject.cpp#L115)

### Sprite Frame Metadata

OE sprite frame entries carry:

- `textureName`
- `scale`
- `flags`
- `glowRadius`
- `paletteId`

Defined in:

- [Sprites.h](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Graphics/Sprites.h#L29)

OE loads this from `dsft.bin`:

- [Engine.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Engine.cpp#L648)

Glow radius then drives dynamic lights in:

- [BaseRenderer.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Graphics/Renderer/BaseRenderer.cpp#L123)
- [Outdoor.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Graphics/Outdoor.cpp#L768)

### Spell Sprite To Effect Recipe

This is the least data-driven part of OE.

`SpellFxRenderer.cpp` contains a large switch on spell sprite ids:

- [SpellFxRenderer.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/SpellFxRenderer.cpp#L720)

It chooses:

- trail particle recipe
- impact particle recipe
- special effect recipe
- optional mobile light color/radius
- whether sprite rendering should remain visible

### Portrait Buff And UI Spell FX

OE also hardcodes spell id to portrait animation mapping:

- [SpellFxRenderer.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/SpellFxRenderer.cpp#L991)

This is not world particles, but it belongs in the broader FX plan.

### Where OE Colors Come From

Colors come from several places:

- hardcoded spell colors in `SpellFxRenderer.cpp`
- object trail colors from object list entries
- decoration colored lights from decoration descriptors
- random colors in a few generic fallback emitters

There is no single color table.

## Current OpenYAMM State

Current OpenYAMM already has the following useful pieces:

### Runtime Projectiles And Impacts

Projectile state and impact state already exist:

- [OutdoorWorldRuntime.h](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorWorldRuntime.h#L238)

Those are currently billboard-driven and render in:

- [OutdoorBillboardRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorBillboardRenderer.cpp#L1754)

### Object FX Metadata

OpenYAMM object table already carries:

- `particleTrailColor`
- `particleTrailRed`
- `particleTrailGreen`
- `particleTrailBlue`

in:

- [ObjectTable.h](/home/pjasicek/github/OpenYAMM/game/tables/ObjectTable.h#L11)

### Glow Metadata

OpenYAMM sprite frame entries already carry:

- `glowRadius`

in:

- [SpriteTables.h](/home/pjasicek/github/OpenYAMM/game/tables/SpriteTables.h)

### Portrait Spell FX

Portrait spell fx routing already exists:

- [OutdoorPresentationController.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorPresentationController.cpp#L531)
- [SpellFxTable.h](/home/pjasicek/github/OpenYAMM/game/tables/SpellFxTable.h)

### Map-Side Glow Multipliers

Outdoor sprite objects already retain:

- `glowRadiusMultiplier`

via:

- [MapDeltaData.h](/home/pjasicek/github/OpenYAMM/game/maps/MapDeltaData.h)
- [MapAssetLoader.cpp](/home/pjasicek/github/OpenYAMM/game/maps/MapAssetLoader.cpp#L1507)

### What Is Missing

The main missing parts are:

- a real world particle system
- a real dynamic light runtime for spell/object FX
- world-space emitter recipes
- billboard contact shadows
- static outdoor lighting bake products
- clean trigger routing for all OE-like FX cases

## Design Goals

The FX implementation should satisfy these goals:

1. MM8 parity
- projectile trails
- impact bursts
- monster buff sparkles
- fire emitters
- glow lights
- portrait spell animations

2. Clean separation
- particles
- lights
- shadows
- effect recipes
- trigger routing

3. Data where useful
- do not hardcode what is already stable in data
- do not force everything into data if the effect is inherently procedural

4. Low-risk runtime path
- bounded memory use
- bounded light count
- clear fallback behavior

5. Forward extensibility
- successor project can add richer recipes and rendering without rewriting the
  gameplay trigger layer

## Proposed Subsystems

Create a new `game/fx/` subsystem with the following modules.

### 1. `ParticleSystem`

Responsibilities:

- own runtime particle instances
- update lifetime and motion
- apply fade and optional size over lifetime
- render billboard and line particles
- expose a simple spawn API

Required particle kinds:

- bitmap billboard particle
- sprite particle
- line particle

Required motion flags:

- ascending
- dropping
- rotating
- velocity-driven
- random jitter optional

Recommended shape:

- fixed-capacity particle pool
- no heap allocation during normal frame updates
- stable IDs only if needed for debugging
- compact SoA or cache-friendly AoS is acceptable

Suggested first API:

```cpp
struct ParticleSpawnRequest;

class ParticleSystem
{
public:
    void reset();
    void update(float deltaSeconds);
    void submitRender(const FxViewContext &view) const;
    bool spawn(const ParticleSpawnRequest &request);
};
```

### 2. `DynamicLightSystem`

Responsibilities:

- collect transient and persistent FX lights
- cull them to the camera
- provide a bounded set of active lights to render passes

Inputs:

- projectile glow
- impact bursts
- actor/glowing sprite frames
- decoration emitters
- spell recipe-driven flashes or pulses

Do not fold this into the particle system.

Lights and particles are related, but not the same thing.

Suggested first API:

```cpp
struct FxLightRequest;

class DynamicLightSystem
{
public:
    void reset();
    void beginFrame();
    void addLight(const FxLightRequest &request);
    Span<const ActiveFxLight> visibleLights() const;
};
```

### 3. `ShadowSystem`

Responsibilities:

- render billboard contact shadows
- query ground/bmodel receivers
- fade shadow by height and context

First implementation should support:

- actors
- sprite objects
- projectiles
- optionally world items

Do not start with real shadow maps.

First implementation should be:

- contact/blob shadows only
- soft ellipse or soft quad
- projected onto terrain or bmodel collision hit point

Suggested first API:

```cpp
struct ShadowCasterRequest;

class BillboardShadowSystem
{
public:
    void beginFrame();
    void addCaster(const ShadowCasterRequest &request);
    void submitRender(const FxViewContext &view) const;
};
```

### 4. `FxRecipeLibrary`

Responsibilities:

- own reusable effect recipes
- translate high-level effect triggers into particle and light spawn requests

Initial built-in recipes:

- `ProjectileTrailFire`
- `ProjectileTrailParticle`
- `ProjectileTrailLine`
- `SingleCollisionBurst`
- `FireballCollisionBurst`
- `LightningCollisionBurst`
- `BuffSparkles`
- `DecorationFireEmitter`
- `StunRing`
- `SpherePulse`
- `ImplosionPulse`

This is the layer that should absorb OE behavior while staying cleaner than OE.

### 5. `FxTriggerLayer`

Responsibilities:

- connect gameplay/runtime events to recipes
- avoid polluting gameplay systems with rendering details

Trigger sources:

- projectile spawn
- projectile update
- projectile impact
- monster cast
- monster buff/self-buff application
- event spell cast
- decoration/object emitters
- portrait spell requests

This layer should know:

- what happened
- which recipe to trigger

This layer should not know:

- low-level rendering details
- billboard mesh building
- bgfx resource management

## Data Ownership Plan

Use existing tables where possible.

### Keep Existing Data Sources

Use:

- [object_list.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/data_tables/object_list.txt)
  for:
  - object trail flags
  - object trail colors
  - lifetime
  - speed

- sprite frame YAML data for:
  - `glowRadius`
  - sprite visuals

- current spell/projectile identity mappings already represented in runtime data

- [portrait_fx_events.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/data_tables/portrait_fx_events.txt)
  and spell FX tables for portrait/UI-side effects

### Add New Data Where Useful

Recommended new files:

- `assets_dev/Data/data_tables/fx_recipe_table.yml`
- `assets_dev/Data/data_tables/spell_world_fx_bindings.txt`
- `assets_dev/Data/data_tables/object_fx_bindings.txt`
- `assets_dev/Data/data_tables/decoration_fx_bindings.txt`

Suggested contents:

`fx_recipe_table.yml`
- recipe id
- particle texture or sprite
- particle count
- lifetime range
- spawn spread
- velocity range
- color mode
- light radius
- light color
- contact shadow behavior if relevant

`spell_world_fx_bindings.txt`
- spell id
- spell sprite id or sprite name
- trail recipe id
- impact recipe id
- cast recipe id
- light policy id

`object_fx_bindings.txt`
- object id
- trail recipe override
- impact recipe override
- emitter recipe override

`decoration_fx_bindings.txt`
- decoration id
- emitter recipe id
- static light override

Do not try to move every OE spell switch case into data in phase 1.

Phase 1 should keep:

- small code-side recipe helpers
- data-side binding/tuning

## Concrete MM8 Parity Requirements

Initial parity should include at least:

### Projectile Trails

- fire bolt
- fireball
- poison spray
- acid burst
- ice blast fallout
- death blossom fallout
- lightning bolt visual strip equivalent
- light bolt trail

### Projectile Impacts

- generic single collision burst
- fireball burst + sphere pulse
- sparks/lightning burst
- harm/flying fist blood-red impacts
- sunray/light bolt/light impacts
- dark sharpmetal impact

### Buff Cast FX

- monster self-buff sparkles
- monster target-buff sparkles
- party portrait buff animations already present

### Emitters

- decoration fire emitters
- object trail fire
- object trail particle
- object trail line

### Lights

- glow radius on sprite frames
- spell projectile mobile lights
- impact light pulses where OE used them
- decoration colored lights

### Shadows

- billboard contact shadows for:
  - actors
  - moving projectiles
  - important sprite objects

## Lighting Strategy

Split lighting into:

- baked static lighting
- dynamic transient lights

### Dynamic Lights

Use for:

- projectiles
- impacts
- glowing spell sprites
- decorations with fire
- actor frame glow where it matters

Keep dynamic light budgets small.

Recommended starting limits:

- max active dynamic lights visible in outdoor world: `32`
- high-priority near-camera lights sorted first
- per draw region or per shader batch: nearest `4` or `8`

Performance notes:

- projectile and impact lights are short-lived
- actor frame glow lights are potentially numerous and need culling
- decoration lights can be split into:
  - baked if static and common
  - dynamic only if blinking/flickering/temporary

### Baked Outdoor Lighting

Bake at outdoor bake time:

- terrain directional lighting
- terrain ambient occlusion
- terrain static shadowing from large bmodels
- bmodel directional lighting
- bmodel ambient occlusion

Optional later:

- low-resolution light probe grid

Do not bake:

- spell/projectile effects
- actor shadows
- temporary fire/projectile lights
- gameplay-driven stateful effects

### Suggested Outdoor Bake Product

Recommended artifact:

- `assets_dev/Data/games/outXX.lighting.yml`
  or
- compact binary cache if size becomes a problem later

Suggested contents:

- terrain lighting samples or per-vertex color
- terrain AO values
- bmodel baked vertex colors or lightmap references
- optional local probe grid
- optional receiver metadata for shadow projection quality

Phase 1 can use simple baked vertex color or tile-cell lighting.

No need to jump to full lightmaps immediately.

## Shadow Strategy

### Phase 1: Billboard Contact Shadows

Implement:

- soft ellipse or soft quad shadow
- projected onto ground/bmodel receiver
- alpha faded by caster height
- scale based on actor/projectile size

Receiver query:

- terrain height if unobstructed
- otherwise nearest bmodel floor hit

Good enough for:

- actors
- projectiles
- some hovering objects

This is cheap and gives major visual grounding.

### Phase 2: Better Receiver Fit

Improve with:

- local receiver normal
- better deformation on slopes
- partial occlusion if caster is very high

### Avoid Initially

Do not start with:

- cascaded shadow maps
- global dynamic bmodel shadows
- fully dynamic scene-wide soft shadows

Those are too expensive and not the best value for this visual style.

## Rendering Integration

### New Runtime Flow

Per frame:

1. gameplay/runtime produces trigger events
2. `FxTriggerLayer` converts them to recipes
3. `FxRecipeLibrary` spawns particles and lights
4. `ParticleSystem` updates and culls particles
5. `DynamicLightSystem` gathers and culls lights
6. `ShadowSystem` gathers billboard casters
7. render order:
   - terrain + bmodels with baked lighting and limited dynamic lights
   - billboard shadows
   - world billboards
   - particles
   - UI / portraits / HUD

### Outdoor Renderer Changes

Expected touchpoints:

- [OutdoorRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorRenderer.cpp)
- [OutdoorBillboardRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorBillboardRenderer.cpp)
- [OutdoorGameView.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameView.cpp)

Expected shader work:

- extend outdoor terrain and bmodel shaders to accept a small capped set of
  dynamic lights
- add a simple billboard shadow render program
- add particle billboard render path

Recommended first implementation:

- keep particles forward-rendered and additive/alpha blended
- keep billboard shadows simple alpha-blended dark quads
- keep dynamic light application simple and capped

## Performance Budget Guidance

These are initial engineering targets, not final hard rules.

### Particle Budget

Outdoor:

- visible active particles target: `<= 2000`
- hard cap: `4096`

Indoor:

- visible active particles target: `<= 3000`
- hard cap: `4096`

Reason:

- OE used `5000`
- our renderer should stay comfortably under that first
- particle overdraw matters more than raw count

### Light Budget

- active visible dynamic lights target: `<= 32`
- lights affecting a single terrain/bmodel pass: `<= 8`
- lights affecting a single billboard shading path: `<= 4`

### Shadow Budget

- billboard contact shadows target: `<= 128` casters visible
- skip tiny and far-away projectiles
- fade out or disable contact shadows at long range

### Bake Budget

Outdoor bake can be slower and more expensive.

Acceptable:

- several seconds per map during tooling

Not acceptable:

- expensive per-frame recomputation of static lighting

## Implementation Phases

### Phase 1. FX Core

Implement:

- `ParticleSystem`
- `DynamicLightSystem`
- `BillboardShadowSystem`
- basic render submission hooks

Do not yet add full authored data tables.

### Phase 2. OE-Parity Recipe Set

Implement core recipes:

- projectile trails
- projectile impacts
- buff sparkles
- decoration fire emitter
- stun ring
- sphere pulse

Bind them in code first using a small library.

### Phase 3. Runtime Trigger Wiring

Hook:

- [OutdoorWorldRuntime.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorWorldRuntime.cpp)
- projectile spawn/update/impact
- monster spell/buff paths
- event spell requests
- decoration/object runtime emitters

### Phase 4. Data-Driven Bindings

Add:

- recipe table
- spell binding table
- object/decor binding tables

Move only stable tunables into data.

### Phase 5. Baked Outdoor Lighting

Add bake tool and runtime loader:

- static terrain lighting
- terrain AO
- bmodel baked lighting
- optional probe grid later

### Phase 6. Successor-Oriented Extensions

Later optional improvements:

- richer particles
- light flicker curves
- emissive animation curves
- optional indoor bake path
- editor-side live preview of emitters and light probes

## Acceptance Criteria

Phase 1 and 2 are done when:

- projectile trails are visible for OE-equivalent projectile/object flags
- projectile impacts spawn the right burst families
- monster buff casts spawn visible sparkles
- decoration fire emitters render correctly
- sprite glow lights appear where OE-equivalent data says they should
- billboard contact shadows visibly ground actors and projectiles

Phase 5 is done when:

- outdoor maps render with baked static lighting
- dynamic lights layer on top without replacing baked lighting
- lighting bake artifacts are deterministic and reloadable from authored assets

## Recommended First Deliverable

The first concrete implementation slice should be:

- particle runtime
- dynamic lights
- billboard contact shadows
- projectile trail and impact recipes
- buff sparkle recipe
- fire emitter recipe
- trigger integration from `OutdoorWorldRuntime`

This is the highest value parity slice.

It improves:

- projectile combat readability
- spell feedback
- world grounding
- overall scene life

without waiting for the full outdoor lighting bake pipeline.

## Open Questions

These do not block phase 1.

1. Should outdoor dynamic lights affect terrain and bmodels immediately, or only
   billboards first?
Recommended:
- billboards first
- terrain/bmodels in the next pass

2. Should OE’s portrait spell FX stay separate from world FX?
Recommended:
- yes
- share binding vocabulary if useful, but keep runtime systems distinct

3. Should some static decoration lights be baked instead of dynamic?
Recommended:
- yes, where fully static and common
- dynamic only for flicker or gameplay relevance

4. Should the editor preview FX emitters and contact shadows?
Recommended:
- yes eventually
- not required for first runtime parity milestone

## Final Recommendation

Implement the subsystem in this order:

1. `ParticleSystem`
2. `DynamicLightSystem`
3. `BillboardShadowSystem`
4. parity recipe library
5. runtime trigger integration
6. data-driven binding tables
7. baked outdoor lighting

This gives:

- MM8-compatible visible behavior
- cleaner code than OE
- low-risk runtime costs
- a clear growth path for the successor
