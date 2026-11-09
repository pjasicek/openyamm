# Effect library research

Research date: 2026-09-22. Scope: reusable art, authoring tools, game references, and compatibility with
OpenYAMM. This is research, not an installation or an approved generation queue. Runtime assets and effects
were not changed during this research. The discarded Spell Reaver restoration remains discarded.

Subsequent authorized implementation: [three authored showcase effects](../../../assets_dev/engine/effects/authored/README.md)
now use selected sources below, with shared runtime loading and HTML previews.

**Recommendation:** build a small library of reusable particle textures and original timed effects using
the existing FX system. Start with CC0 art from Kenney and Unity Labs; use Effekseer or Blender for new
animation sources. Improving silhouette, motion, timing and layering offers more variety than enlarging
already-soft MM9 frames.

## Sources worth using

| Source | Useful material | Reuse status and assessment |
| --- | --- | --- |
| [Kenney Particle Pack](https://kenney.nl/assets/particle-pack) | Neutral sparks, smoke, circles, stars, traces and other masks | CC0. Best starting vocabulary for original effects; tint, scale and animate selectively. Archive inspected. |
| [Unity Labs sequences and flipbooks](https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks) | FireBall01, wispy smoke, disc smoke, candle smoke and flames | This specific collection is CC0, with TGA/EXR assets. FireBall01 archive inspected. Useful naturalistic fire and smoke components. |
| [Effekseer contributed effects](https://effekseer.github.io/en/contribute.html) | Spell bursts, impacts, auras and editable effect compositions | Use the explicitly CC0 sample section. Older samples have a separate, more restrictive license. Individual archives not inspected. |
| [Cethiel: Arcane Magic Effect](https://opengameart.org/content/arcane-magic-effect) | Purple energy knots, wisps and projectile-like shapes | CC0. Small, stylistically plausible fantasy sprites. Archive inspected; animation order and timing are not established. |
| [rubberduck: 25 special effects rendered with Blender](https://opengameart.org/content/25-special-effects-rendered-with-blender) | Fire, explosions, rings and shockwaves at 128×128, plus Blender sources | CC0. Editable sources are particularly useful. Provider describes composited and directly rendered variants; archive not inspected. |
| [Mikodrak: 2D Spell Effects](https://opengameart.org/content/2d-spell-effects) | Ten effects originally made for Nyrthos | CC0 on the creator's page. Secondary candidate; archive not inspected. |
| [JangaFX free VDB animations](https://jangafx.com/software/embergen/download/free-vdb-animations) | Volumetric fire, smoke and explosions | CC0. Render offline to image sequences; large source downloads and extra rendering work make this a later option. |

The licenses above concern those specific collections, not everything on their hosting sites. Retain the
source URL, author, license evidence, archive hash and conversion settings with every accepted asset.

## What was actually inspected

[Candidate preview](preview_candidates.png) contains Cethiel's six folders across the first six rows,
seven selected Kenney textures, and seven sample cells from Unity's FireBall01 sheet. These are research
previews of CC0 artwork from the first, second and fourth sources above, not in-engine screenshots.
[Archive inspection](inspected_archives.json) records file names, dimensions, modes, sizes and SHA-256 hashes.

| Download inspected | Findings | Import consequence |
| --- | --- | --- |
| [Kenney v1.1 ZIP](https://kenney.nl/media/pages/assets/particle-pack/f8fe0f8cb8-1677578741/kenney_particle-pack.zip) | 96 transparent 512×512 PNG files plus matching black-background versions; includes rotated variants. The web page advertises 80, so do not confuse the page count with the inspected archive. Bundled license confirms CC0. | Select a small subset; many will only need 128×128. Decode palette transparency correctly. |
| [Unity FireBall01 ZIP](https://unity3d.com/files/labs/downloads/vfx/assets01/FireBall01/FireBall01-flipbooks.zip) | TGA is 1024×1024 RGB, an 8×8 grid of 128×128 frames, with black background and no alpha. Also contains two EXR files, which were not decoded. | Suitable candidate for additive fire. Split the grid, choose timing explicitly and verify brightness in game. It is not an ordinary alpha-smoke texture. |
| [Cethiel Arcane ZIP](https://opengameart.org/sites/default/files/Arcane_Effect.zip) | 42 RGBA PNGs in six folders of seven. Widths 124–126 and heights 106–108; no timing or anchor metadata supplied. | Establish whether images are intended as frames or variants. Register canvases before animation; filename order alone is insufficient. |

Black-backed fire should not undergo the hard silhouette cleanup used for opaque sprites. Preserve the
soft light contribution and choose blending deliberately. Alpha smoke and additive fire generally need
separate layers.

## Other games and techniques

**NOLF2 / LithTech is the closest structural reference.** Its published
[ClientFX registration source](https://github.com/jsj2008/lithtech/blob/master/NOLF2/ClientFxDLL/clientfx.cpp)
lists sprite systems, sprites, sounds, lights and transform helpers, plus lightning and polygon tubes.
That suggests useful future primitives: sustained lightning, curved trails and independently timed light.
It does not establish compatibility with MM9's FXF files: component sets and fields vary between games.

Public SDK availability also does not establish permission to redistribute a game's textures or copy its
code. The [NOLF2 Modernizer license notes](https://github.com/haekb/nolf2-modernizer#license) explicitly retain
the original SDK EULA. Treat proprietary game artwork as reference unless a separate reuse basis is
established. Recreate an effect's behavior with our own recipes and reusable art.

**Diablo III is a useful technique reference for economical motion.** Nick Seavert's
[Diablo III VFX experiments](https://jangafx.com/insights/diablo-3-vfx-experiments) demonstrate recreations
using scrolling noise and shape masks to get varied motion from a small number of particles. This is a
primary account of the recreation, not a verified description of all Diablo III internals. Its approach
supports prioritizing motion and composition over resolution. Live scrolling-mask materials would need
additional shader support in our named FX path; baking the result offline is an earlier option. The article's
project files were not cleared for reuse merely because JangaFX separately publishes CC0 VDBs.

## Fit with the current engine

The implementation, rather than the older MM9 integration assessment, is the basis for these findings:

- [Effect definitions](../../../game/fx/EffectDefinition.h) already describe timed sprites and emitters,
  several emission shapes, world/local simulation, camera-facing/world-plane sprites, alpha/additive/multiply
  blending, and color, scale and motion curves. Original effects can combine these existing capabilities.
- [Definition loading](../../../game/fx/import/EffectDefinitionLoader.cpp) supports the `predictable`
  compatibility profile. Use that for new recipes; native MM9 timing remains for imported content.
- [Sprite resources](../../../game/fx/import/EffectResourceLibrary.h) carry FPS, logical dimensions and a
  list of frame paths. [Rendering](../../../game/fx/EffectRenderer.cpp) selects full-frame textures;
  the descriptor has no atlas-cell rectangle. Split flipbooks into PNG frames for an initial pilot.
- Named sprite recipes do not currently expose general ribbon/beam endpoints, scrolling-noise materials,
  distortion or volumetric playback. Those are separate renderer features, not simple asset imports.
- [Indoor loading](../../../game/indoor/IndoorRenderer.cpp) and
  [outdoor loading](../../../game/outdoor/OutdoorGameView.cpp) explicitly select
  `engine/effects/mm9/library.yml` and its resource bindings. The
  [world FX loader](../../../game/fx/WorldFxSystem.cpp) replaces its library rather than appending libraries.
  New authored directories are therefore not automatically discovered.

Adding art is practical, but a maintained library needs a small shared content-loading change. Proposed
location: `assets_dev/engine/effects/authored/`, with namespaced IDs such as
`openyamm:fx/fire_impact_small`. Assemble authored and generated libraries with duplicate-ID validation;
do not hand-edit generated MM9 output. Keep world-specific content in its own package scope.

The conversion output would be PNG frames, existing `effectSprite.v2` descriptors, resource bindings and
effect YAML. Effekseer is useful as an offline authoring tool without introducing another runtime:
its [Recorder](https://effekseer.github.io/Help_Tool/en/ToolReference/record.html) exports images and sheets,
including separate blend/additive images. Baking whole 3D effects fixes their viewpoint; preferably bake
components and retain spatial motion in OpenYAMM emitters.

## Suggested first pilot

1. **Healing/buff:** a few Kenney sparks, a soft glow and a world-plane pulse. Test original timing and color
   curves with very little new texture data.
2. **Fire impact:** a short Unity or Blender fire burst with a separately fading alpha-smoke layer.
3. **Arcane hit:** one reviewed Cethiel variant, a short flash and a ring; animate only after confirming
   canvas registration and a coherent sequence.

Aim initially for small sequences, often 8–16 frames at 128×128, and use 256×256 when actual screen coverage
warrants it. This is a starting budget, not a requirement to downsample every source. Sixteen RGBA8 128×128
frames occupy 1 MiB before mipmaps; 32 at 256×256 occupy 8 MiB. Frame texture switches, overlapping particles
and screen coverage also matter. Avoid importing whole packs merely because they are free.

Audition against bright outdoor and dark indoor backgrounds, checking lifetime, scale, anchoring, alpha
fringes and overlap. Use existing named-effect debug spawning before assigning gameplay bindings. Keep
original spell effects available until the new effect has been reviewed in motion. No such runtime audition,
new generation or gameplay replacement was performed in this research.
