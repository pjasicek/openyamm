# Projectile FX OpenEnroth Parity Plan

This document tracks a focused plan for making OpenYAMM projectile particles structurally match OpenEnroth behavior.
OpenEnroth is a reference for behavior and structure only; do not copy its code.

Primary references:

- `reference/OpenEnroth-git/src/Engine/SpellFxRenderer.cpp`
- `reference/OpenEnroth-git/src/Library/Color/ColorTable.h`
- Current OpenYAMM implementation:
  - `game/fx/WorldFxSystem.cpp`
  - `game/fx/ParticleRecipes.cpp`
  - `game/fx/ParticleRecipes.h`

## Status Checklist

- [x] Document OE projectile FX structure and color mapping.
- [x] Add OE projectile recipe metadata for covered projectile families.
- [x] Add segment-aware projectile trail state.
- [x] Implement OE-style hanging trail particles for monster bolts and mapped spell trails.
- [x] Implement OE-style single and radial impact particle bursts.
- [x] Suppress normal projectile billboards for OE particle-only projectile recipes.
- [x] Render OE segment projectiles for Lightning Bolt and Sunray.
- [x] Add/align remaining special impact primitives: fireball sphere, implosion sphere, mind blast after-effect, stun.
- [x] Add visual verification captures for representative projectile families.
- [x] Close out focused unit tests for mapped primitive types.
- [x] Add focused runtime coverage for projectile presentation/impact state.
- [x] Add focused headless map coverage for FX-only projectile presentation/impact state.

## Problem

Some projectile trails currently look like separated particle beads instead of continuous spell trails. A visible example is
`test_img/1014.png`, where a fire-like projectile trail has circular particles with gaps between them.

The likely cause is structural: OpenYAMM currently emits generic trail bursts from the current projectile position, while
OpenEnroth often emits particles using previous and current projectile positions. OE continuity comes from placing particles
along the projectile segment and keeping them alive long enough, not from globally increasing density.

## OpenEnroth Model

OE's projectile FX path is centered around `SpellFxRenderer::RenderAsSprite`. It maps sprite ids to a small set of reusable
FX primitives:

- Hanging trail particles: `_4A73AA_hanging_trace_particles___like_fire_strike_ice_blast_etc`
- Single collision burst: `_4A75CC_single_spell_collision_particle`
- Fireball collision burst plus sphere: `_4A7688_fireball_collision_particle`
- Implosion sphere: `_4A77FD_implosion_particle_d3d`
- Mind blast after-effect: `_4A7948_mind_blast_after_effect`
- Radial spark/lightning burst: `_4A7A66_miltiple_spell_collision_partifles___like_after_sparks_or_lightning`
- Stun FX: `_4A7C07_stun_spell_fx`
- Segment projectile rendering: `AddProjectile` / `DoAddProjectile`

### Hanging Trail Behavior

OE hanging trails:

- Spawn every `_ticksPerParticle`, defaulting to `2_ticks`.
- Store previous projectile position in `field_54`/`array_4`.
- Once initialized, emit particles at:
  - midpoint between previous and current position
  - current position
  - small `+/- 4` lateral X offsets
- Use `ParticleType_Bitmap | ParticleType_Rotating | ParticleType_Ascending`.
- Use `effpar01`, except specific light/sunray paths that use `effpar02` or `effpar03`.
- Use `particle_size = 1.0`.
- Use long lifetime:
  - first emission: `1-2s`
  - subsequent emissions: `750-1250ms`

This is the key behavior missing from the current monster-bolt/generic-particle path.

## OE Color Mapping

Use OE `ColorTable` RGB values as the authoritative projectile FX color mapping.

| Use case | OE color | RGB hex |
| --- | --- | --- |
| Fire bolt, fireball, fire spike, meteor, inferno, incinerate | `OrangeyRed` | `#FF3C1E` |
| Monster air bolt, monster spirit bolt | `Azure` | `#0AAAFF` |
| Monster earth bolt, rock blast impact | `CarnabyTan` | `#5C310E` |
| Monster water bolt | `ScienceBlue` | `#0062D0` |
| Poison spray, acid burst, monster body bolt | `GreenTeal` | `#0AB450` |
| Monster mind bolt | `DirtyYellow` | `#C8C805` |
| Light bolt, sunray, destroy undead | `White` | `#FFFFFF` |
| Monster dark bolt, implosion, death blossom, sharpmetal | `MediumGrey` | `#7E7E7E` |
| Sparks, lightning bolt impact, starburst | `MustardYellow` | `#C8C814` |
| Ice bolt impact, ice blast impact/fallout | `CarolinaBlue` | `#9EB9F1` |
| Harm impact, flying fist impact | `BloodRed` | `#F00000` |
| Harm mobile light | `GreenishBrown` | `#64640F` |
| Blaster impact | `Red` | `#FF0000` |

Current OpenYAMM colors in `projectileRecipeColorAbgr` are close in some cases but should be replaced with this explicit
OE mapping where OE defines a projectile effect color.

## OE Projectile Mapping

### Monster Elemental Bolts

OE maps these to hanging trail particles and does not render a normal projectile sprite:

| Sprite family | Trail color | Texture | Impact |
| --- | --- | --- | --- |
| Air bolt | `Azure` | `effpar01` | single collision burst, `Azure`, `effpar01` |
| Spirit bolt | `Azure` | `effpar01` | single collision burst, `Azure`, `effpar01` |
| Earth bolt | `CarnabyTan` | `effpar01` | single collision burst, `CarnabyTan`, `effpar01` |
| Fire bolt | `OrangeyRed` | `effpar01` | single collision burst, `OrangeyRed`, `effpar01` |
| Water bolt | `ScienceBlue` | `effpar01` | single collision burst, `ScienceBlue`, `effpar01` |
| Body bolt | `GreenTeal` | `effpar01` | single collision burst, `GreenTeal`, `effpar01` |
| Mind bolt | `DirtyYellow` | `effpar01` | single collision burst, `DirtyYellow`, `effpar01` |
| Light bolt | `White` | `effpar01` | single collision burst, `White`, `effpar01` |
| Dark bolt | `MediumGrey` | `effpar01` | single collision burst, `MediumGrey`, `effpar01` |

### Spell Projectiles

| Projectile family | OE behavior |
| --- | --- |
| Arrow, flaming arrow, blaster, trap projectiles, ice bolt, deadly swarm, rock blast, blades, mind projectiles, flying fist, paralyze, toxic cloud, shrinking ray, sharpmetal, dragon breath | Render sprite normally unless a specific impact path is listed |
| Fire bolt | Hanging trail, `OrangeyRed`, `effpar01`, mobile light 256 |
| Fire bolt impact | Single collision burst, `OrangeyRed`, `effpar01`, mobile light 256 |
| Fireball | Hanging trail, `OrangeyRed`, `effpar01`, mobile light 256 |
| Fireball impact | Mobile light 256, fireball burst plus sphere, sprite/sphere retained |
| Fire spike impact | Radial spark burst, `OrangeyRed`, `effpar01`, radius 250, mobile light 256 |
| Immolation | Single collision burst, `OrangeyRed`, `effpar01` |
| Meteor shower fallout | Three radial bursts, `OrangeyRed`, `effpar01`, radii 300/250/200, mobile light 256 |
| Inferno | Radial burst, `OrangeyRed`, `effpar01`, radius 250 |
| Incinerate impact | Two single collision bursts, `OrangeyRed`, `effpar01`, mobile light 256 |
| Sparks pop | Radial burst, `MustardYellow`, `effpar02`, radius 200 |
| Lightning bolt | Segment projectile from previous to current position using random `sp18h1` to `sp18h6` texture |
| Lightning bolt impact | Radial burst, `MustardYellow`, `effpar02`, radius 200, mobile light 256 |
| Implosion | Implosion sphere, `MediumGrey` |
| Starburst fallout | Radial burst, `MustardYellow`, `effpar01`, radius 200, mobile light 256 |
| Poison spray | Hanging trail, `GreenTeal`, `effpar01`, mobile light 256 |
| Poison spray impact | Single collision burst, `GreenTeal`, `effpar01`, mobile light 256 |
| Acid burst | Hanging trail, `GreenTeal`, `effpar01`, mobile light 256 |
| Acid burst impact | Render sprite normally |
| Ice bolt impact | Single collision burst, `CarolinaBlue`, `effpar01`, mobile light 256 |
| Ice blast impact | Single collision burst, `CarolinaBlue`, `effpar01`, mobile light 256 |
| Ice blast fallout | Hanging trail, `CarolinaBlue`, `effpar01` |
| Stun | Stun particle primitive |
| Rock blast impact | Single collision burst, `CarnabyTan`, `effpar01` |
| Blades impact | Mind blast after-effect |
| Death blossom | Hanging trail, `MediumGrey`, `effpar01`, plus normal sprite |
| Death blossom impact | Radial burst, `MediumGrey`, `effpar01`, radius 200 |
| Death blossom fallout | Hanging trail, `MediumGrey`, `effpar01` |
| Mind blast impact | Mind blast after-effect |
| Harm | Normal sprite plus mobile light `GreenishBrown`, radius 128 |
| Harm impact | Single collision burst, `BloodRed`, `effpar01` |
| Flying fist impact | Single collision burst, `BloodRed`, `effpar01`, mobile light 256 |
| Light bolt | Hanging trail, `White`, `effpar03`, mobile light 128 |
| Light bolt impact | Single collision burst, `White`, `effpar02`, mobile light 256 |
| Destroy undead | Mobile light `White`, radius 64 |
| Sunray | Segment projectile from previous to current position, no texture, mobile light 128 |
| Sunray impact | Single collision burst, `White`, `effpar03` |
| Sharpmetal impact | Single collision burst, `MediumGrey`, `effpar01` |

## Implementation Plan

### 1. Add OE FX Recipe Metadata

Add a small OE-parity recipe layer in `ParticleRecipes` that maps `ProjectileRecipe` to:

- OE primitive kind
- OE color
- OE material/texture equivalent
- impact primitive
- mobile light color/radius
- whether the normal projectile billboard/sprite should render

This should replace ad hoc per-branch color choices for OE-covered projectile families.

Suggested enum:

```cpp
enum class OeProjectileFxPrimitive
{
    None,
    RenderSprite,
    HangingTrail,
    SegmentProjectile,
    SingleCollisionBurst,
    RadialCollisionBurst,
    FireballSphereBurst,
    ImplosionSphere,
    MindBlastAfterEffect,
    Stun,
};
```

### 2. Add Segment-Aware Trail State

In `WorldFxSystem`, replace the current cooldown-only projectile trail state with a state object:

```cpp
struct ProjectileFxTrailState
{
    bool hasPreviousPosition = false;
    float previousX = 0.0f;
    float previousY = 0.0f;
    float previousZ = 0.0f;
    float cooldownSeconds = 0.0f;
};
```

Use `projectileId` as the key. Clean up entries for projectiles no longer present in the current presentation state.

### 3. Implement Hanging Trail Emission

Add a recipe entry point that receives both previous and current positions:

```cpp
void spawnOeHangingTrailParticles(
    ParticleSystem &particleSystem,
    const ProjectileSegmentSpawnContext &context,
    const OeProjectileFxRecipe &recipe);
```

Behavior:

- On first emission, spawn two particles at current position with `+/- 4` lateral offsets and `1-2s` lifetime.
- On subsequent emissions, spawn four particles:
  - midpoint `+4`
  - midpoint `-4`
  - current `+4`
  - current `-4`
- Use `effpar01` equivalent by default.
- Use OE color table values.
- Use `particle_size = 1.0` equivalent.
- Use `750-1250ms` lifetime after initialization.
- Use low/no inherited velocity and no large random offset.

This should replace the current generic trail branch for monster elemental bolts and OE-covered hanging spell trails.

### 4. Implement Segment Projectile Rendering

OE renders Lightning Bolt and Sunray as a segment between previous and current positions:

- `Lightning Bolt`: segment projectile using random `sp18h1` to `sp18h6`.
- `Sunray`: segment projectile with null texture in OE.

OpenYAMM should expose a lightweight world FX segment primitive rather than approximating these as particles.

### 5. Implement Impact Primitives

Implement or align these OE primitives:

- Single collision burst:
  - 10 particles
  - current projectile position
  - random `shiftX/Y/Z` in `[-255, 256)`
  - `1-2s` lifetime
  - configured OE color and `effpar` material
- Radial spark/lightning burst:
  - fixed radial directions
  - `z + 32`
  - configured radius value, usually 200/250/300
  - `1-2s` lifetime
- Fireball sphere/burst:
  - 10 `OrangeyRed` particles
  - plus expanding sphere based on projectile lifetime fraction
- Implosion sphere:
  - collapsing sphere, `MediumGrey`
- Mind blast after-effect:
  - 10 sprite particles using the projectile frame texture, `MediumGrey`
- Stun:
  - midpoint/current sprite particles using previous/current state

### 6. Preserve Current Non-OE Behavior Until Mapped

If OE does not define a particle effect for a projectile family, keep current rendering unless there is a known regression.
Do not broaden the rewrite to every projectile at once.

### 7. Tests

Add focused tests for:

- `ProjectileRecipe` classification for monster bolt object ids and spell projectiles.
- OE color mapping returns the exact expected ABGR values.
- Hanging trail first emission and subsequent emission particle counts.
- Hanging trail lifetime ranges.
- Trail state cleanup when projectile ids disappear.
- Segment projectile creation for Lightning Bolt and Sunray.
- Impact primitive particle counts for single burst and radial burst.

### 8. Visual Verification

Capture before/after screenshots for:

- Monster fire/air/water/body/mind/dark bolts.
- Fire Bolt.
- Fireball and Fireball impact.
- Lightning Bolt and Lightning impact.
- Poison Spray and Acid Burst.
- Ice Bolt/Ice Blast impacts.
- Light Bolt and Sunray.
- Sharpmetal impact.

The `test_img/1014.png` case should specifically be rechecked for continuous trail appearance.

## Performance Notes

This should be performance-neutral or better for the visible trail problem.

The current generic path can try to solve gaps by increasing particle density, particle size, or lifetime. OE's structure is
more efficient: place a small number of particles at meaningful points along the projectile's traveled segment, and let their
lifetimes overlap. Longer lifetimes increase live particle count, but the spawn count can be lower and more stable than a
dense generic burst.

The implementation should avoid global density increases. Tune only OE-covered projectile families.

## Verification Notes

Current focused verification:

- `cmake --build build --target openyamm -j25` passes.
- `./build/tests/openyamm_unit_tests --test-case="*projectile*"` passes: 28 test cases, 296 assertions.
- `./build/tests/openyamm_unit_tests --test-case="*OE*"` passes: 56 test cases, 790 assertions.
- `build/game/openyamm --headless-run-regression-suite projectiles` includes and passes
  `lightning_projectile_uses_fx_only_presentation_and_impact`.
- `build/game/openyamm --headless-capture-projectile-fx /tmp/openyamm_projectile_fx_oe_captures` generates
  renderer-independent PNG captures and a manifest for representative projectile trail, segment, and impact families.
- `/tmp/openyamm_projectile_fx_oe_captures/spell_hanging_trails.png` was inspected against the sparse bead pattern in
  `test_img/1014.png`; the generated OE-covered hanging trail rows overlap continuously.

The full projectile headless suite is not yet a clean completion gate because two neighboring projectile regressions fail
outside the new OE FX parity case:

- `local_event_457_cannonball_uses_gravity_but_fireball_does_not`
- `mixed_actor_53_arrow_ignores_friendly_lizardman_blocker`

Generated visual captures cover:

- `monster_bolt_trails.png`: fire, air, water, body, mind, and dark monster bolt hanging trails.
- `spell_hanging_trails.png`: Fire Bolt, Fireball, Poison Spray, Acid Burst, Light Bolt, and Ice Blast fallout trails.
- `segment_projectiles_and_light_impacts.png`: Lightning Bolt, Sunray, and Lightning/Light/Sunray impacts.
- `impact_bursts.png`: Fireball, Meteor, Ice Bolt, Sharpmetal, Harm, and Flying Fist impacts.

## Open Questions

- Whether OpenYAMM should add explicit `effpar01`, `effpar02`, and `effpar03` particle materials, or map them onto existing
  `SoftBlob`/`HardBlob`/`Mist` generated textures.
- Whether segment projectiles should be rendered by the FX renderer or by the existing projectile billboard renderer.
- Whether save/load should persist projectile FX trail history. It is probably not necessary because OE trail history is
  transient render state and can be reinitialized after load.
