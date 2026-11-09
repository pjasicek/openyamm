# MM8 School of Fish — m636

> **Installed model reduced (2026-10-19):** the installed model is now the reduction from [`../mm8_m636_reduce_claude/`](../mm8_m636_reduce_claude/README.md) (LOD0 7,800 -> 5,280). This project's exports and master remain the unreduced production; the rollback source is in `../mm8_m636_reduce_claude/work/`.

Twelve fish swim as one coordinated school. Installed for **School of Fish (non-combatant) A/B/C**, merged
monster IDs **178–180**, with native purple, green and orange palettes. Native noncombatant AI and gameplay
remain unchanged. Fish have individually phased tails and fins, small formation movements, and an authored
roll-and-settle death. No flocking AI or new renderer feature is required.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m636_claude/review/viewer/)
includes all three colours, native frame anchors, frame stepping and feedback links.
Selected portable model: `export/mm8_m636.glb`; editable packed master: `export/m636_master.blend`.
`creature_3d_progress.json` and `review/delivery.json` record selection, hashes and checks.
The user accepted revision `m636-v1` on 2026-10-18: “ok accepted”.

## Source and production route

`source/native_inventory.json` preserves the verified 130 native BMPs, palette hashes and three descriptor
bindings. The existing 2D restoration in `../mm8_m636/` is unchanged. Native front/profile sequences establish
the mixed fish sizes, loose vertical formation, spiny dorsal fins, pale tails and mottled coloured bodies.
Depth spacing, continuous tail beats and coordinated body motion are authored interpretations of those sprites.

No approved reusable swimming creature or fish animation was available. Five new HD views in `references_hd/`
were generated from the native fish identity. Their actual prompts, source/output hashes and selected images
are in `generation_runs.json`. One Meshy Smart Topology fish was generated, locally fitted and simplified to
650 triangles, UV-unwrapped and retextured using the selected HD views. Geometry cost 5 credits and the 2K
retexture cost 10 credits: **15 credits total** against the 100-credit creature budget. Original service returns
and receipts remain in `meshy/` and the progress record.

The returned texture model has the same surface/UV correspondence as the upload (normalised correspondence
error below 0.000001). Returned maps were applied to the retained animated master; its mesh was not replaced
with the service's rescaled static return. The measured DirectX normal map was converted to glTF +Y-up.

## Geometry, materials and motion

| LOD | Triangles for the complete 12-fish school |
| --- | ---: |
| 0 | 7,800 |
| 1 | 3,888 |
| 2 | 1,908 |
| 3 | 924 |

One skin, one visible mesh and one material draw per colour LOD. The rig has 61 bones: a shared root and
Body/Tail1/Tail2/FinL/FinR for each fish. There are at most three nonzero skin influences per exported vertex
(the simplifier blends the neighbouring tail weights). Lower LODs preserve all twelve fish. Duplicate faces
introduced by the two coarsest reductions were removed before saving/exporting. The lower meshes also supply
the shadow chain. These are geometry costs, not measured frame-time or FPS claims.

All fish share the same UV islands intentionally, one 2K base colour, and 1K normal/ORM/region-mask maps.
Purple, green and orange use each native palette's pigment chroma/luminance, fitted to the existing 16-stop
region-ramp shader. Pale fins and markings remain largely neutral. Runtime tiers share the four images;
only browser previews bake separate tier colours for Three.js. Fish skin and fin membranes use nonmetallic
rough materials, with restrained per-texel specular and small eye highlights. Opaque fin geometry avoids
transparent overdraw. Tiny fish heads share the atlas instead of adding a separate head material/set.

| Clip | Duration | Native roles |
| --- | ---: | --- |
| Swim | 1.875 s | Standing, walking, fidget, hit and unused attack/cast/run aliases |
| Death | 1.25 s | Dying; fish roll independently and settle slightly lower |
| Dead | 1 s, held | Retained dead fish poses |

The living and death durations match 15 and 10 native 125-ms frames. Swim has three tail oscillations per
cycle, different phases per fish, gentle banking and bounded drift. One actor controls the school; the fish
are not twelve independently simulated actors. All tiers use scale 100 and a 22-unit upward anchor offset,
matching the native 256-pixel bottom-anchored canvas. Their native scales are equal, so no runtime reference
to another tier's potentially unloaded sprite is needed. Movement stride is 2.625 model units, corresponding
to the native 140-unit movement speed over the 1.875-second swim cycle. No new attacks or damage events exist. After the held death pose, the existing engine corpse system
dissolves the empty fish school; no permanent corpse or new loot is introduced.

## Verification and known limits

The dense motion audit checks every clip at 96 Hz for finite transforms, continuous rotation and minimum
height; fish-to-fish triangle contacts are sampled at 24 Hz. It found no inter-fish contacts. Swim closes
exactly, Dead stays held, and Death ends exactly at Dead. Reimported GLB surfaces match the master within
0.001 mm at nine poses per clip. See `work/motion_audit.json`.

Neutral viewer inspection covers front/side/rear views, the three palettes, swimming poses and the death
endpoint. All nine tier/clip combinations load and switch without browser errors. Normal and half-speed
WebM recordings plus sampled temporal frames are in `review/playback/`. The agent inspected the sampled
frames; it did not watch the recordings as continuous video.

The ordinary OpenGL game build and focused fish regression pass. The broader MM8 actor run has **52 passes
and one failure**: `mm8_vampire_female_peasant_actor_models_keep_native_roles` cannot resolve the standing sprite
for Vampire Female Peasant B. That separate creature binding was not changed here; see `review/checks/mm8_actors.log`. The regression checks shared model loading,
all three palette names, the twelve-fish rig, swim movement, lower LODs, every native animation role, and
unchanged actor HP, position and animation clocks. Native GPU checks use the actual Plane of Water habitat
(`elemw.odm`). `review/ingame/fixture.json` describes a review-only map overlay containing three immobile fish
schools for palette/LOD/sprite comparisons. Its production map and gameplay tables are untouched. Native inspect-portrait and death/removal captures
are in `review/ingame/inspect/` and `inspect_death/`. Early canyon-
wall captures and unsuccessful launcher attempts are not acceptance evidence; the delivery receipt identifies
selected captures and retained run logs.

Android, Vulkan and controlled performance benchmarks were not run. Underwater OpenGL is the relevant habitat
check; this is not a claim of correct fish placement on arbitrary dry indoor floors. Palette differences are
subdued by the native underwater lighting. Formation movement is authored rather than reactive avoidance.

## Reproduction

Acquire a fresh creature workspace lease and use its token for project writes.

1. `scripts/inspect_geometry.py` imports the retained raw geometry through `tools/run_creature_blender.sh`.
2. `scripts/prepare_fish.py` fits the fish rig, simplifies it and creates the static UV upload.
3. `scripts/compose_textures.py` verifies the retained retexture, composes maps and native palette ramps.
4. Run `scripts/build_school.py` through the Blender wrapper to build the school, animations and four LODs.
5. `scripts/finish_runtime.py` links LODs/material ramps and prepares the shared viewer, preserving feedback.
6. Run `scripts/audit_motion.py` through the Blender wrapper, then `scripts/validate_delivery.py`.
7. `tools/install_model.py export/mm8_m636.glb --world mm8` installs the source and cooks the runtime model.
8. Run the shared creature viewer checks/playback, the focused `mm8_fish_school` actor regression, and the
   retained native tours. `scripts/prepare_runtime_fixture.py` recreates the isolated comparison overlay.

Do not rerun paid jobs to reproduce the retained asset. Do not edit the original downloads, overwrite the
2D restoration, or copy a cooked runtime GLB back over the editable/source export.
