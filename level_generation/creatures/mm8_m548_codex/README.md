# MM8 Crystal Dragon — m548

> **Installed model reduced (2026-10-19):** the installed model is now the reduction from [`../mm8_m548_reduce_claude/`](../mm8_m548_reduce_claude/README.md) (LOD0 7,570 -> 6,132). This project's exports remain the unreduced production; the rollback source is in `../mm8_m548_reduce_claude/work/`.

Wingless, solid rose-crystal quadruped with a tall neck, wedge head, amber eyes, radiating crown, dorsal ridge and short spiked tail. Produced from native MM8 sprite evidence and five Codex HD reference views on 2026-10-18. User artistic acceptance is not recorded.

[Interactive viewer](http://127.0.0.1:8912/level_generation/creatures/mm8_m548_codex/review/viewer/) · [Standing](review/shots/standing.png) · [Attack](review/shots/lunge.png) · [Corpse](review/shots/corpse.png)

Production and scoped technical review are complete.

## Delivered files

- `export/mm8_m548.blend`: editable rig, eight actions and packed textures.
- `export/mm8_m548_lod0.glb`: portable full-detail animated model.
- `export/mm8_m548.glb`: engine-ready model, colour/shadow LODs and mouth socket.
- `assets_source/worlds/mm8/models/mm8_m548.glb`: authoritative installed source; `tools/install_model.py` cooks the runtime copy into `assets_dev/worlds/mm8/models/`.
- `assets_dev/worlds/mm8/models/actors.yml`: Crystal Dragon A/B/C bindings (monster IDs 112/113/114).
- `creature_3d_progress.json`: canonical provenance, paid job receipts, correction ledger and completion evidence.

## Geometry, materials and native sizes

One opaque, single-sided material and shared texture set; 23 deform bones, at most four influences per vertex. Colour LODs contain 7,570 / 3,785 / 1,891 / 945 triangles. Coarse shadow meshes receive bounded inward correction. Head and crown density was protected during body reduction.

The base colour is 2K, the normal and ORM maps 1K. Crystal is nonmetallic, roughness 0.392; amber eyes use 0.188. Normal-map green was corrected using the measured convention. A protected head region in the shared atlas is sufficient for the simple crystal facets; there is no separate portrait-like skin material. The source is solid crystal, with no transmission or glass shell.

All three native tiers use the same pink palette 548 despite their Emerald/Sapphire/Ruby names. They therefore share the exact same geometry and skin, with no artificial recolours or redundant region ramps.

| Descriptor | Name | Native height | Model scale |
| --- | --- | ---: | ---: |
| Crystal Dragon A | Emerald Dragon | 229.500 | 286.581789966 |
| Crystal Dragon B | Sapphire Dragon | 275.398 | 343.895855305 |
| Crystal Dragon C | Ruby Dragon | 336.600 | 420.319385454 |

## Animation

| Clip | Seconds | Endpoint |
| --- | ---: | --- |
| Standing | 2.000 | Loop |
| Walking | 1.000 | Loop; stride 0.32 |
| Running | 0.750 | Loop; stride 0.43 |
| Attack | 1.000 | Recover to standing |
| Hit | 0.625 | Recover to standing |
| Fidget | 0.625 | Recover to standing |
| Death | 1.000 | Grounded collapse |
| Dead | 1.000 | Hold death endpoint |

Motion is authored for this rig from native action evidence, not described as an exact reconstruction of every sprite landmark. Walking, attack, hit, fidget and death retain native action lengths; idle and run are smooth production cycles. Native death starts with three hit frames before the five collapse frames. Attack serves both native energy attacks; its release is at 0.375 seconds from `Socket_Mouth`. Both attacks share the same native source frames. The cast alias is present for the model contract; these monsters have no native spell entry.

Automatic heat weighting failed on the angular shell. Region-constrained four-influence skinning with local smoothing replaced it. Rigid head/crown weights, fixed-length limb IK, the shortened tail, attack head counterrotation and low spread corpse were checked before texturing. Linear baked keys fix Blender/glTF between-key disagreement without altering the sampled poses.

## Validation and review

Outdoor: [model](review/ingame/out_models/front.png), [native sprites](review/ingame/out_sprites/front.png), [ranged attack at LOD2](review/ingame/out_models/lod2.png). Indoor: [model](review/ingame/in_far_models/front.png), [native sprites](review/ingame/in_far_sprites/front.png). Live [damage/hit](review/ingame/out_death/hit.png) and [collapse](review/ingame/out_death/death_08.png).

- Ordinary `openyamm` development build passed.
- The new `mm8_crystal_dragon_actor_models_keep_native_sizes_and_roles` regression passed. It checks all native sizes, shared asset ownership, role clips, mouth socket and unchanged simulation state.
- Export reimport passed all eight clips: 392 half-frame samples, closed loops, at most four influences, minimum surface height above -0.001 m, maximum master/export surface discrepancy below 0.000027 m.
- No inverted closed parts; no zero-area UV triangles; UVs stay inside the atlas. Retexture retained all 22,710 UV corners exactly.
- Viewer check passed all 24 tier/clip combinations with no console errors. `review/playback/` contains actual advancing browser recordings at 1x and 0.5x, timestamped captured frames and the playback report. Recorded playback was reviewed through consecutive timestamped frames alongside static detail views.
- Native desktop comparisons use OpenGL 3.3 on NVIDIA (`vendor=0x10de`, Wayland), fixed cameras in New Sorpigal and Agar’s Laboratory, and isolated saves/settings. These captures are visual checks, not a GPU performance benchmark.

The wider MM8 actor suite returned 12 passes and 14 failures in other creature cases: Cyclops and Unicorn presentation checks, and twelve cases reporting a missing `59c9d94dd6c219187543a17204ca4888.oytex` image. The Crystal Dragon test passed in that run. Full output is in `review/regression_mm8.log`; no unrelated creature or engine fixes were made.

The first desktop launch was blocked by an unrelated ground-item manifest `bounds` field rejected by the current parser. Capture runs use the isolated setting `rendering.item_models=false`; production settings and item assets are unchanged. The first long combat tour let the hostile actor walk off-camera; the selected hit/death tour applies damage immediately and uses time scale 0.15. The ranged beam is visible in the earlier three-tier outdoor LOD capture.

A hardlinked asset fixture declares the MM8 family in the two MM6 review scenes so the original sprites preload. Fixture scene files are detached before editing and original hashes are verified. No production map edits are part of this creature.

Android and Vulkan were not tested. User visual acceptance remains separate from these technical checks.

## Rebuild and review

Claim the existing project with `tools/creature_workspace.py` before modifying it. Use the returned token with the guarded Blender, Meshy and viewer wrappers. `scripts/build.py` rebuilds the selected animated master and LOD export; `scripts/audit.py` validates the final export. Earlier geometry, rig, motion, texture composition and review scripts preserve the production steps and selected intermediate masters.

From the repository root, run `python3 tools/install_model.py level_generation/creatures/mm8_m548_codex/export/mm8_m548.glb --world mm8` after a new selected export, then recheck affected clips and native sizes. Never overwrite the source with a cooked runtime GLB. Native review fixture preparation is in `scripts/prepare_reviews.py`.

Meshy used 15 credits: 5 for Smart Topology and 10 for the retained-UV retexture. Original downloads, request fingerprints, hashes and exact image-generation inputs are retained.
