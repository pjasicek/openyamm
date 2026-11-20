# MM9 FX integration assessment

Inspected 2026-09-21. This is an assessment of the current source and extracted FX library,
not an implementation commitment or measured performance result. No runtime code changed.

## Recommendation

Implementing this is technically suitable. The useful abstraction is a timed effect composed
of emitters, sprites, transform nodes, optional animated meshes and sound instances. Its age
does not prevent implementation with bgfx. The difficult work is matching content semantics
and connecting lifetimes, materials and attachments to OpenYAMM.

Start with a shared, named effect-sequence runtime and sprite components. Keep MM9 recipes,
asset lookup and compatibility rules in mounted MM9 content. Preserve the existing MM6–MM8
recipe behavior. Add model-dependent capabilities after a representative sprite effect has
been validated in both indoor and outdoor rendering.

## Actual content scope

The supplied SPELLS.fxf has 48 groups and 176 keys: 109 SpriteSystem, 24 Sprite,
19 PlaySound, 18 Model and 6 Null keys. Only five of the DLL's 15 registered component
classes occur here. This covers that library, not every original-game spell/projectile path.

38 groups contain no Model components. Ten contain Model components: skullcurse,
death's touch, jarjarb setup, eye of the storm, ghost, blobby, armor, firefly, spellfx,
and specks. Some model assets serve as animated attachment paths rather than visible meshes.

Six groups request body-node attachment through UpdatePos: LichKingRes, bluedots,
dragon smoke, greenyeldots, redyeldots and skullcurse. Linked components have a separate
attachment mechanism. Absence of Model keys therefore does not guarantee that a group
needs no skeleton information.

Ghost and Blobby also reference missing assets in the supplied extraction; implementing
the runtime cannot recover those missing inputs.

## Existing code and gaps

Paths below are relative to the OpenYAMM repository root.

| Area | Existing foundation | Required work / difficulty |
| --- | --- | --- |
| Ownership and world hooks | `game/fx/WorldFxSystem.*`; particle submission from both `IndoorRenderer.cpp` and `OutdoorRenderer.cpp` | Named definitions, instance handles, sequence scheduling, parent lifetime, stop/drain, map teardown; moderate |
| Particles | `ParticleSystem.*`, 4096-particle pool and basic movement modes | MM9 emission distributions, cached randomness, distinct clocks, full tracks and native lifetime rules; moderate |
| Materials and sprite animation | `ParticleRenderer.cpp`, `FxSharedTypes.h`, `WorldFxRenderResources.h` | Current six procedural materials and fixed 12 batches cannot express arbitrary SPR frames; add texture/frame resources, orientation and explicit material semantics; moderate |
| Alpha and size | Renderer interpolates two colors/sizes, applies an additional quadratic fade and scales certain round particles | MM9 tracks must control appearance without these unrelated adjustments; moderate |
| Blending and lighting | `game/shaders/fs_particle.sc`, existing alpha/additive states | Current additive shader multiplies RGB by alpha; ordinary particles are unlit. Match MM9 material operations, fog, lighting and transparent ordering explicitly; moderate to hard for fidelity |
| Asset loading | Mounted assets, `engine/ImageAssetLoader.cpp`; independent FXF/SPR/DTX reader in this investigation | Current image path supports PNG/BMP/PCX, with no DTX branch. Add bounded DTX/SPR/FXF decoding and resource caching; moderate, with existing format research |
| Meshes and animation | Converted MM9 GLBs and sidecars; editor glTF import into bmodels | These assets/static imports do not establish runtime skeletal animation. No general skeletal playback path was found in inspected engine/game code; animated nodes, skinning and mesh materials are the largest new capability |
| Actor attachments | MM9 monster replacement policy uses MM6–MM8 sprites (`MM9_MONSTER_LEGACY_SPRITE_MAPPING.md`) | Sprite actors have no original skeleton. Actor-origin effects work; exact moving hand/head attachment requires preserved skeleton data or an explicitly approximate authored attachment policy |
| Sound | `game/audio/GameAudioSystem.h`, `engine/AudioSystem.*`: WAV, positional instances, loops, stop handles | Good starting point. Playback options lack per-instance pitch and inner/outer radii; existing attenuation uses a fixed curve. Basic audition is easy; original behavior needs extension and calibration |

## Timing is a deliberate integration decision

`WorldFxSystem.cpp` currently advances particles in fixed 1/30-second steps. The native MM9
emitter emits at most once per update, and RotateAdd advances per update. Reusing the 30 Hz
clock unconditionally would select a visibly different density/rotation from a 60 Hz original
reference. The viewer's seeded Column test peaks at 56/103/104 particles at 30/60/120 Hz;
these are preview measurements, not original-game capture measurements.

Give MM9 sequence instances an explicit compatibility update policy. A fixed reference rate
can produce stable playback independent of display refresh; document the chosen reference
FPS/detail and compare against original captures at that rate. Preserve separate group,
component, particle and sprite-animation clocks. Do not change the MM6–MM8 particle clock.

Keep the verified quirks explicit in MM9 compatibility behavior: numeric emission selection,
transparency inversion, wind magnitude, detail scaling, early expiry and short-lifetime color
behavior. They should not become implicit defaults for newly authored effects.

## Suggested implementation stages

1. **Moderate: Column of Fire in-engine.** Read the original recipe and frames; implement
   SpriteSystem, Sprite, Null and timed sound support with full tracks. Spawn through a shared
   named-effect API at a world position or actor origin. Add replay/debug inspection and stop
   handles. Column itself needs four SpriteSystem components and one sound, with no mesh or
   body-node attachment. Validate visual state and timing indoors and outdoors.
2. **Moderate: broader sprite-library support.** Validate distinct emission shapes, oriented
   sprites, moving parents, linked transforms, looping and smooth shutdown. Scope MM9 resource
   loading to mounted content and active effects. Wire selected gameplay/map events through
   existing event infrastructure; cosmetic FX support does not require an SCR interpreter or
   implementing MM9 spell mechanics.
3. **Harder: model/path and body-node effects.** Implement sampled node animation and attachment
   evaluation first where path models require no visible skin. Add animated mesh rendering for
   visible models. For sprite actors, decide explicitly whether a retained skeleton animation
   is justified or whether named attachment approximations are acceptable.
4. **Open-ended research: original-game visual parity.** Capture the original at controlled FPS,
   detail, camera and wrapper settings. Finish model tracker, texture-stage, light/fog, sorting,
   loop and attachment traces. Validate audio scheduling and attenuation. The viewer passes
   playback tests but is not evidence of exact original pixels or sound mixing.

The initial implementation is a contained subsystem feature, larger than a texture import and
smaller than replacing the renderer. Completing every library effect faithfully is materially
larger because of models and unresolved native behavior. Calendar estimates would depend on
which fidelity and attachment requirements are selected.

## Architecture and acceptance

Keep one owner of effect instances in shared gameplay FX. Separate definition evaluation from
render submission: evaluated quads carry texture/frame, size, orientation, color and material
state. Reuse bgfx resource/submission infrastructure while avoiding the current renderer's
automatic fades and material-specific tuning for MM9 data. MM9 simulation should not acquire
a second independent particle-age/motion update through the old pool.

Load recipes/resources on mount or demand, not on every startup. Reuse texture handles across
instances; batch compatible draws without invalidating transparency order. Hundreds of simple
particles in an isolated preview give no reason to require GPU simulation, but real scenes
need profiling for simultaneous effects, overdraw, texture switches and the existing pool cap.

Acceptance should cover recovered-rule unit tests, actor removal/map change/pause and stop/drain
scenarios, original reference captures, and affected MM6–MM8 indoor/outdoor regressions. Check
that unmounted MM9 adds no meaningful asset loading, memory or per-frame work. No builds or
runtime tests were needed for this source-only assessment.

## Follow-up: existing OpenMM9 model work and a general GLB runtime

The user narrowed the initial runtime scope to position/orientation-based effects, without
mesh skinning, and prefers modern imported assets reusable outside MM9. Subsequently inspected
the supplied OpenMM9 checkout (paths in this section are relative to that checkout):

- `tools/import/convert_abc_model.py`: existing ABC-to-GLB exporter, including hierarchy,
  translation/rotation animation, mesh geometry, skin data and PNG preview references. It is
  closely related to OpenYAMM's `tools/mm9_import_discovery/convert_abc_model.py`; avoid starting
  a third unrelated converter. Defaults differ: OpenMM9 uses native coordinate scale 1.0.
- `game/render/AnimatedModelAsset.{h,cpp}`: asset structures, retained cgltf loader, clip
  sampling, looping/transitions, node/socket lookup, hierarchy evaluation and skinning data.
- `game/render/AnimatedModelRenderer.*`: bgfx animated-model rendering, including GPU skinning
  and instanced rendering entry points. Existence is established from code, not a new runtime test.
- `game/render/AbcModelAsset.*`: direct native loader. The active project direction is native
  ABC/DTX; `docs/native_abc_no_sidecar_runtime_goal.md` explicitly places converted GLBs outside
  the active game/editor asset path. The retained GLB code is not proof of current integration.

Inspected existing GLB JSON chunks under `artifacts/model_exports/models/spells/`:

| File | Nodes | Meshes | Skins | Animation |
| --- | ---: | ---: | ---: | --- |
| bugpath.glb | 5 | 1 | 1 | bugpath |
| wormpath.glb | 14 | 4 | 1 | wormpath |
| tube.glb | 30 | 1 | 1 | armorcylinder2 |

Bugpath and Wormpath preserve the named moving nodes used by FX links. A dedicated path export
can preserve the node hierarchy and clips while excluding helper meshes and skin declarations.
Tube contains a skinned mesh; conversion to GLB does not turn deformation into rigid animation.
These checks inspect structure only, not glTF conformance or visual equivalence.

Recommended ownership for the user's revised scope:

1. Generic model assets/instances, node animation and rendering belong in reusable engine
   services, shared with the editor. Use asset-relative resource references through the mounted
   filesystem, shared GPU resources, independent instance poses and explicit coordinate/unit
   conversion at the content boundary.
2. Implement a documented GLB subset: static meshes, rigid node animation and invisible animated
   attachment nodes. Use node handles internally; resolve names at binding time. Do not allocate
   skinning state for node-only effects. Reject unsupported visible skinned meshes clearly.
3. Gameplay FX owns emission, particle timelines, effect materials and sound scheduling. It can
   bind to nodes from the general animation service without owning a second animation player.
4. MM9 import tools convert ABC/DTX/SPR/FXF into optional GLB, PNG, effect definitions and WAV
   references. Native-specific flags and behavior stay in imported data/compatibility semantics.
   Preserve source provenance and original files for verification, outside runtime requirements.

Existing OpenMM9 code has assumptions to review before using its design generically: the
inspected pose traversal assumes parents precede children, the node transform reader takes TRS
without handling matrix-authored nodes, and the channel sampler does not retain interpolation
mode. A general loader must handle these valid input cases or reject unsupported ones rather
than silently misinterpret them. Verify texture URI resolution and optional attributes too.

The converter also rewrites some texture alpha for model preview/material policy. That policy
must not be applied indiscriminately to FX sprite textures. Use a pixel-preserving PNG conversion
with explicit effect material state; preserve mip and texture metadata separately where needed.
The earlier DTX runtime recommendation is superseded for this requested imported-asset design.

Initial verification should compare named node trajectories with source ABC evaluation and test
two independent instances, hierarchy ordering, clip boundaries, coordinate conversion and package
lookup. Then validate one ordinary rigid model and one effect path, keeping existing MM6–MM8
rendering unchanged. Future skinning can extend the same asset/instance system when requested.
