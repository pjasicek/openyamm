# MM8 Will-o’-Wisp — m528

Floating smoke-ring body, gold energy core, short-lived engine stars and six animations, installed for
Dancing Light, Wisp and Will O’ Wisp (monster IDs 97–99). The three native tiers share palette 528;
their only appearance difference is scale: 1 / 1.299988 / 1.699997.

Selected source export: `export/mm8_m528.glb`. Editable, packed animation master:
`export/m528_master.blend`. Selection, hashes and verification are recorded in
`creature_3d_progress.json` and `review/delivery.json`; user artistic acceptance is tracked separately.

## Native appearance and route

`source/native_inventory.json` verifies all 56 original BMP hashes and records the 33 referenced frames,
timings, palette and tier data. `review/native_actions.png` compares the native action sequences.
The existing restoration in `../mm8_m528/` is preserved. Its restored branching sparks, orange-white
attack flash and brown death-smoke fragments supply the effect atlas; crops and source hashes are in
`textures/provenance.json`. The ring uses a seamless authored turbulent field coloured from the native
grey smoke. Core and halo falloff are analytic. No external artwork or raw animation clips were added.

This follows the playbook’s local effect-bodied route: no HD generation, Meshy model, rigging job or
texture job was necessary. Meshy spend: **0 credits**. Reactor and Air Elemental informed the existing
unlit-glow and scrolling-transparent-surface methods; the wisp geometry, rig and motion are new.
All eight native views point to one stored direction, so depth and orbital paths are authored inference.

## Model and motion

The actual toroidal surface forms a flattened smoky body. Three tilted particle-emission rings surround it.
White stars appear, grow, drift and fade over 0.45 seconds; they are camera-facing engine particles, not bones
or crossed mesh cards. Death bursts the core and disperses small native smoke fragments while the last stars
fade, then removes the body entirely. There is no corpse.

| Clip | Duration | Runtime role |
| --- | ---: | --- |
| Standing | 2.5 s | Four native idle cycles; looping hover and pulse |
| Walking | 1.25 s | Two native movement cycles; travelling lean and orbit; also run |
| Attack | 1 s | Continuous charge, native release at 0.75 s, 0.25 s follow-through |
| Hit | 0.375 s | Compressing disturbance; also the native fidget sequence |
| Death | 0.5625 s | Native-duration flash and dispersion |
| Dead | 1 s | Both mesh nodes hidden |

`Socket_Core` supplies the ranged release point. Attack also fills the unused cast role; native wisps
have a light missile and no spells. Native gameplay clocks and dynamic glow values are unchanged.
The source frames carry Center flags, but the current actor renderer uses the bottom of their
128-pixel logical canvas. Geometry is authored around the ring centre, so bindings lift it by
64 / 83.199232 / 108.799808 world units for A / B / C. This matches the actual native actor
presentation. One Blender metre represents 100 source pixels and the actor binding uses scale 100.

There are 16 bones and one skin influence per vertex. Two mesh/material draws per LOD use authored
triangle counts **2388 / 1100 / 548 / 252**. LODs reduce the torus and death fragments while preserving
the core. The remaining surfaces use explicit opposite-facing triangles for two-sided alpha.
The stars add at most 24 camera-facing quads (48 triangles) per creature in the main pass, making LOD0
**at most 2436 triangles including stars**. All creatures share the existing additive glint texture batch;
bloom can submit the same star quads once more. Pixel coverage still matters for transparency cost.
Death fragments use one small vertical plane each to avoid intersecting oversized smoke cards.

Both materials are alpha-blended, unlit, nonmetallic, with specular and edge darkening disabled.
The ring uses the existing `[0.18, 0]` UV scroll and a 0.45 alpha factor to keep the core visible
through overlapping smoke surfaces in the native renderer. These effects intentionally use no lit PBR/AO/normal
detail or physical opaque shadows. Maps are `m528_smoke.png` (512×256) and `m528_fx.png` (1024²).
The material-class map marks effect pixels as class 11. Cooked BC7/ASTC textures are installed through
the normal model installer. Engine stars reuse the existing particle renderer; actor-lifetime binding and
portrait submission are shared engine changes.

## Review and reproduction

Open the shared review viewer at
<http://127.0.0.1:8912/level_generation/creatures/mm8_m528_claude/review/viewer/>.
It includes the body’s six clips, native frame anchors and the three tier sizes. It does not simulate the
engine particle system. Use `review/ingame/particles_staged/`, `particles_in/` and `particles_portrait_final/`
for the complete current creature. The v2 recordings in `review/playback/` are historical mesh-spark footage.

The pose audit samples all six exported clips, checks finite transforms, quaternion continuity,
loop closure and the empty corpse, then compares Blender and GLB posed surfaces. Maximum exported
surface discrepancy is below 0.0005 mm; loop closure error is below 0.000001 m.
See `work/motion_audit.json`. This is geometry/motion verification, not user artistic approval.

Native indoor/outdoor captures, same-camera sprite comparisons, all four LODs and selected motion
phases are in `review/ingame/`. The indoor fixture adds distant actors only to preload the native
sprite families. It does not change the production map. Exact launcher settings, logs and fixture
details are retained with the captures. See the delivery receipt for actual results and limitations.

Reproduce under a fresh project lease with the normal workspace guard:

1. `scripts/prepare.py` verifies native inputs and prepares effect maps (also initializes progress).
2. `tools/run_creature_blender.sh --token TOKEN level_generation/creatures/mm8_m528_claude/scripts/build_model.py --full`
3. Guarded `python3 level_generation/creatures/mm8_m528_claude/scripts/finish_runtime.py` wires LODs,
   collapsed-mesh visibility and the shared viewer. It preserves existing viewer feedback.
4. Run `scripts/audit_motion.py` through the Blender wrapper.
5. Guarded `python3 tools/install_model.py level_generation/creatures/mm8_m528_claude/export/mm8_m528.glb --world mm8`.
6. Run `tools/run_creature_review.py` for checks, shots and playback, then the retained native tours.

Runtime bindings are in `assets_dev/worlds/mm8/models/actors.yml`. The focused engine regression is
`mm8_wisp_actor_models_keep_sizes_effects_and_empty_corpse` in the actors suite. No Android or Vulkan
run was performed. Transparent fragment planes are an intentional bounded-cost approximation;
they are not a volumetric particle simulation.

Historical v1/v2 review used browser playback recordings, extracted temporal frames, native captures and numeric
motion checks. Full videos were recorded but were not watched as continuous video by the agent.
The current Wisp regression passes against the production manifest, including the engine-particle lifecycle checks.
The initial production broader MM8 suite had **43 passes / 2 failures**: Phoenix presentation and
Plane Guardian height/impact/socket assertions. Those concurrently authored creatures were not
changed here. Earlier Air Elemental and Naga errors were corrected by their owners and both
now pass. That historical result is `review/checks/mm8-final.log`.

## White spark density follow-up

The user accepted the existing look and requested more white sparkling material. Historical revision `m528-v2`
increases the orbiting clusters from 28 to 48 and enlarges each by 10%; LOD counts are 48/36/24/16.
All six clip timings, smoke/core materials, scale and release timing are retained. Previous files are
in `work/before_spark_density/`; previous playback is in `review/playback_before_spark_density/`.
That export passed the all-clip pose/export audit, 18 viewer switches and the focused native
Wisp regression. Fresh normal/half-speed recordings are in `review/playback/`; fresh native LOD
captures are in `review/ingame/dense_out_model/` and `dense_in_model/`. No engine rebuild or broader
suite rerun was needed for this scoped art revision. See `review/delivery.json` for current hashes.

## Engine stars follow-up — m528-v3

The user requested revisiting the approach: retain the disc and make the white material short-lived engine FX.
The 48 crossed-card clusters and their 48 bones are removed. The shared named-effect system now owns the
white stars through `ambient_effect` in the three actor bindings. Its authored definition is
`assets_dev/worlds/mm8/effects/wisp.yml`, importing the existing `openyamm:effect-sprite/glint` resource.
Each of three tilted rings emits one star every 0.06 seconds, with a 0.45-second lifetime and a peak size
of 19.2 world units at tier A (previous mesh cards were 15.4 × 18.7). The core, smoke, attack flash, death
fragments and six clip timings are retained. The previous selected files are in `work/before_engine_sparks/`.

The native creature regression now checks bounded emission across a full eight-second cycle, pause,
hidden/death drainage and the independently animated inspect portrait. Existing Demon eye/charge effects
are checked separately. The export audit and 18 body-viewer switches passed. Native OpenGL captures
cover indoor/outdoor LODs, temporal star frames and the independently animated inspect portrait. See `review/delivery.json` for current artifact hashes
and the exact verification record. No controlled GPU timing or Android/Vulkan performance measurement
was made; this revision reduces skinned geometry/bones and bounds particles, not a claimed FPS gain.
