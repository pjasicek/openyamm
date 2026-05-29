# Particle Renderer Implementation Plan

## Goal

Implement a real particle renderer for OpenYAMM that:

- replaces the current temporary quad-based trail/impact path
- supports outdoor now
- is shared by indoor later
- stays performant on the current renderer/backend
- is extensible for future richer FX without rewriting the system

This plan is for the renderer/runtime architecture, not for reproducing every MM8 effect in one step.

## Current State

### What exists now

- Outdoor transient FX state lives in:
  - [OutdoorFxRuntime.h](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorFxRuntime.h)
  - [OutdoorFxRuntime.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorFxRuntime.cpp)
- Outdoor billboard rendering lives in:
  - [OutdoorBillboardRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorBillboardRenderer.cpp)
- Outdoor dynamic light application lives in:
  - [OutdoorRenderer.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorRenderer.cpp)
  - [fs_outdoor_textured_fog.sc](/home/pjasicek/github/OpenYAMM/game/shaders/fs_outdoor_textured_fog.sc)

### What is temporary / wrong

- particles are still rendered through the billboard path, not a dedicated particle renderer
- travel and impact recipes are mixed into `OutdoorFxRuntime`
- particle rendering is currently constrained by billboard assumptions
- outdoor-only ownership is wrong for a system that must be reused indoors

## Target Architecture

Create a shared FX subsystem under `game/fx/`.

### New modules

- `game/fx/ParticleSystem.h`
- `game/fx/ParticleSystem.cpp`
- `game/fx/ParticleRenderer.h`
- `game/fx/ParticleRenderer.cpp`
- `game/fx/ParticleRecipes.h`
- `game/fx/ParticleRecipes.cpp`
- `game/fx/FxSharedTypes.h`

Optional later:

- `game/fx/FxLightSystem.h`
- `game/fx/FxLightSystem.cpp`

### Ownership split

#### `ParticleSystem`

Responsible for:

- owning active particles
- CPU-side particle simulation
- spawn/despawn
- particle limits
- recipe-driven spawn helpers

Not responsible for:

- scene-specific lighting
- terrain/bmodel shading
- gameplay event decisions

#### `ParticleRenderer`

Responsible for:

- batching particle vertices
- particle texture selection
- blend-mode separation
- bgfx submission

Not responsible for:

- deciding which spell spawns what
- particle simulation
- scene light emitter selection

#### `ParticleRecipes`

Responsible for:

- effect family definitions
- travel trail layers
- impact burst layers
- decoration fire emitter layers
- later buff sparkle layers

Not responsible for:

- draw submission
- global runtime ownership

#### Scene runtimes

Outdoor and indoor runtimes should:

- trigger recipe spawns
- provide frame delta
- provide camera/render context
- optionally provide scene-specific light emitters separately

But they should not own the particle engine implementation.

## Particle Data Model

### Particle instance

The shared particle instance should include:

- position
- velocity
- acceleration or motion mode
- age
- lifetime
- start size
- end size
- start color
- end color
- rotation
- angular velocity
- drag
- blend mode
- texture id / sprite id
- alignment mode
- sort bias / layer

Suggested enums:

- `ParticleBlendMode`
  - `Alpha`
  - `Additive`
- `ParticleAlignment`
  - `CameraFacing`
  - `VelocityStretched`
  - `GroundAligned`
- `ParticleMotionMode`
  - `Ballistic`
  - `VelocityTrail`
  - `Drift`
  - `Rise`
  - `StaticFade`

### Recipe layer

Each recipe layer should describe:

- texture
- blend mode
- count
- spawn interval or burst count
- base color / color variance
- size range
- lifetime range
- inherited velocity factor
- local random spread
- drag
- acceleration / rise
- alignment mode

This keeps recipe tuning out of the render code.

## Rendering Design

### Render path

Use a dedicated particle render path, separate from billboard sprites.

It should:

- use its own vertex type
- use its own shader program
- batch all particles by:
  - blend mode
  - texture
  - alignment mode if needed

### Suggested vertex format

- position
- uv
- color
- size or already-expanded quad vertices

Two valid approaches:

1. CPU-expanded quads
- simpler
- good enough for this project
- likely the right first implementation

2. point/instance expansion in shader
- more modern
- more complexity
- not needed first

Recommendation:

- start with CPU-expanded quads

### Shaders

Add a dedicated particle shader pair:

- `vs_particle.sc`
- `fs_particle.sc`

Minimum fragment behavior:

- sample particle texture
- multiply by vertex color
- respect vertex alpha
- no terrain/bmodel lighting coupling

Optional later:

- soft depth fade near geometry
- emissive multiplier
- distortion for selected materials

### Textures

Start with a very small set:

- soft round blob
- spark streak
- smoke puff
- mist cloud
- ember mote

These can be:

- generated procedurally first
- replaced by authored textures later

Do not start with dozens of textures.

## Runtime Integration

### Phase 1 scene integration

Keep current outdoor effect triggering, but redirect spawns into shared `ParticleSystem`.

Replace current outdoor-only direct particle ownership:

- move `ParticleState` out of `OutdoorFxRuntime`
- let `OutdoorFxRuntime` call spawn helpers on `ParticleSystem`

Outdoor still owns:

- projectile light emitters
- decoration light emitters
- contact shadows

But not the particle store itself.

### Phase 2 indoor integration

Indoor runtime should later use the same particle system for:

- spell trails
- impacts
- torches / braziers / fire emitters
- buff sparkles
- ambient dust / mist if wanted

## Recipes To Implement First

These are the first concrete parity targets.

### Travel recipes

- Fire Bolt
- Fireball
- Lightning Bolt
- Ice Bolt
- Light Bolt
- Poison Spray
- Acid Burst
- Toxic Cloud
- Dragon Breath
- DarkFire Bolt

### Impact recipes

- fire impact burst
- lightning spark impact
- ice burst + cold mist
- poison/acid splash haze
- generic light impact
- generic dark/fire impact

### Decoration/environment recipes

- fire pedestal / brazier / torch flame
- campfire
- beacon flame

### Later

- buff sparkles
- status effect loops
- monster cast windup effects

## Immediate Migration Plan

### Step 1

Create shared `ParticleSystem` with current `ParticleState` moved out of `OutdoorFxRuntime`.

Deliverable:

- compile-only refactor
- behavior unchanged

### Step 2

Create `ParticleRenderer` with a dedicated particle shader and CPU-expanded quads.

Deliverable:

- outdoor can render particles through the new renderer
- remove particle rendering from `OutdoorBillboardRenderer::renderFxParticles(...)`

### Step 3

Move current trail/impact spawn logic into `ParticleRecipes`.

Deliverable:

- `OutdoorFxRuntime` triggers shared recipes instead of constructing particles directly

### Step 4

Implement layered travel recipes:

- core trail layer
- secondary haze/smoke layer where appropriate

Deliverable:

- visible improvement on:
  - Fire Bolt
  - Lightning Bolt
  - Ice Bolt
  - Toxic Cloud

### Step 5

Implement layered impact recipes.

Deliverable:

- replace current generic-ish impact bursts with family-specific bursts

### Step 6

Move decoration fire emitters to shared recipes.

Deliverable:

- fire decorations use the same particle engine as spells

### Step 7

Integrate the same system into indoor rendering/runtime.

Deliverable:

- identical particle architecture outdoors and indoors

## Performance Constraints

### This should stay cheap

For this project, a CPU-updated particle renderer is acceptable if:

- active particles are capped
- textures are few
- batching is good
- overdraw is controlled

### Hard limits to enforce

Suggested initial caps:

- global active particles: `4096`
- per-spawn cap for single effect: small, recipe-dependent
- max particle textures in first pass: `5`
- draw batches per frame: keep low by batching by texture + blend mode

### Expensive things to avoid

- huge full-screen alpha quads
- too many smoke particles
- too many unique particle textures
- per-particle heap allocation
- scene-lighting calculations in the particle shader

### Expected cheap path

- CPU simulation
- transient vertex buffer submission
- one alpha batch group
- one additive batch group
- texture bucketing inside each group

That is a reasonable cost for OpenYAMM.

## Relationship To Lights And Billboards

Keep these systems separate.

### Particle renderer

Handles:

- visual transient FX only

### Light emitters

Handled separately by outdoor/indoor renderers.

Particles may optionally spawn companion light emitters, but the light system should stay separate.

### Sprite / object billboards

Handled separately.

Do not treat particles as a special case of sprite billboards long-term.

## Acceptance Criteria

The particle renderer is in acceptable first-release shape when:

- projectile trails no longer rely on billboard hacks
- impacts no longer rely on billboard hacks
- outdoor uses the shared particle renderer
- at least the first spell families look coherent:
  - Fire Bolt
  - Lightning Bolt
  - Ice Bolt
  - Toxic Cloud
- performance remains near current outdoor baseline
- architecture is scene-agnostic enough to reuse indoors

## Recommended Order Of Work

1. Shared `ParticleSystem`
2. Dedicated `ParticleRenderer`
3. Dedicated particle shaders
4. Recipe migration
5. Travel recipe polish
6. Impact recipe polish
7. Decoration fire migration
8. Indoor integration

## Notes

- Keep current outdoor light emitter work. It is orthogonal and should remain separate.
- Keep current contact shadow work. It is orthogonal and should remain separate.
- Do not try to solve bloom/post-processing in the same pass.
- Do not try to make this GPU-simulated. That is unnecessary here.
- Do not overfit to OE structure. Match behavior, not code shape.
