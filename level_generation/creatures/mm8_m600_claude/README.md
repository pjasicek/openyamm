# Nightmare — MM8 m600

> **Installed model reduced (2026-10-18):** the installed runtime is now the triangle reduction from [`../mm8_m600_reduce_claude/`](../mm8_m600_reduce_claude/README.md) (LOD0 15,986 -> 8,792). This project's own exports and master remain the unreduced production; the rollback source is `../mm8_m600_reduce_claude/work/mm8_m600_source_pre_reduce.glb`.


Rigged slime/stalk creature for Nightmare A/B/C: **Fear, Terror and Nightmare**, merged descriptors **151–153**.
Technical production is complete. The user approved the subtle attack revision on 2026-10-18.

[Interactive review](http://127.0.0.1:8776/level_generation/creatures/mm8_m600_claude/review/viewer/) ·
[Portable GLB](export/mm8_m600.glb) · [Packed Blender master](export/nightmare.blend) ·
[Runtime checks](review/runtime_checks.json) · [Canonical progress](creature_3d_progress.json)

The viewer has all three palettes, seven clips, slow motion and native source images. It uses the existing repository
review server on port 8776. The original sprites and gameplay tables are unchanged.

## Anatomy and motion

Two tall mouth stalks, a third front mouth, five slender eye stalks, three embedded eyes and a low elongated slime
body. A local 58-bone rig uses anatomical branch ownership, distributed bend weights, rigid eyes/teeth and jaw controls.
There are at most four influences per vertex. Snake informed the segmented bend and reduction method; Ooze was a
provisional reference for floor-anchored slime controls, not a user-approved baseline. No humanoid animation or paid
rigging service was used.

| Clip | Seconds | Native basis |
|---|---:|---|
| Standing | 3.000 | Held native frame; subtle breathing is authored |
| Walking | 1.000 | Eight native 125 ms frames |
| Attack | 1.000 | Eight frames; mouth brace, gape, subtle irregular eye-stalk motion and recovery |
| Hit | 0.625 | Five frames of recoil |
| Death | 0.750 | Six frames; outward collapse and pooling |
| Dead | 1.000 held | Native corpse; identical to Death endpoint |
| Fidget | 0.625 | Five frames; mouth/eye motion |

Stalk retraction uses joint translations and unit-scale tips so Blender and glTF preserve the same pod shapes.
Slime pooling uses floor-anchored body controls. Keys are linear at 120 Hz, exactly 15 samples per native hold.
The user requested no baked effects and more erratic eye movement during Attack. Five eye chains now make
small, slower staggered twitches with a smooth fade at both endpoints. Combat remains physical melee, with native timing
and no added missile, spell, event marker or equipment. The user will add effects separately.
See [motion study](MOTION.md) for observations and inferred anatomy.

All tiers use scale **280.073043099**: native standing silhouette **187 pixels × 1.5**, divided by the fitted
standing model height **1.00152445 m**. Width follows **146/187**. The base crawl cycle covers **0.714099426 m**,
calibrated to the native speed 200 world units and one-second walk cycle; pursuit uses normal runtime gait advancement.
Equal native tier scales are recorded explicitly, avoiding a dependency on preloaded sprite frames in other worlds.

## Materials and detail levels

One shared 2048-square base colour, 1024-square normal/specular/roughness maps and 1024-square region mask.
This 2K body budget retains detail across the eight eyes and three mouths on one UV layout. Native palette
601/602/603 ramps provide olive/red irises, violet/yellow irises and red/blue irises. Socket skin follows the body tier;
sclera, teeth and mouth interiors retain their own material colours. Runtime ORM is **R specular, G roughness, B zero**.
The Meshy normal was converted once to glTF +Y-up. No full tier textures are installed in the game.

Colour and shadow triangle counts are **15986 / 8792 / 5427 / 3472**.
Reduction is evaluated with bent stalks before restoring rest coordinates. Eyes are protected from reduction to retain
their iris UVs. The 55%/34%/22% budgets deliberately exceed simple half-per-level reduction: 12.5% distorted irises.
Shadow LODs have small inward offsets to limit detached shadow fringes. No LOD adds another skeleton or animation set.

The editable Blender delivery packs the final A appearance, corrected normal and seven actions, without effect meshes or bones.
Its A preview texture is baked for Blender; the runtime GLB uses the shared maps and native region ramps.
`work/nightmare_final.blend` remains the shared-texture export source. The preview conversion changes materials only.

## Validation

- [Export parity](work/export_parity.json): maximum Blender/glTF surface difference **0.01002 mm**, including fractional frames.
- [Export gates](review/export_gates.json): all seven clips, four colour and four shadow LODs; finite normalized skin,
  at most four influences, floor contact, strain, loop closure, held corpse and absence of baked effects.
- [UV/LOD audit](review/uv_lod_audit.json): zero degenerate UV triangles, finite unit normals on every colour LOD.
- Baseline agent review of all clips at normal and half speed, mouth close-ups, three tiers, side/back and reduced meshes.
  Recordings are in [playback](review/playback/); LOD shape inspection uses the unmodified base material, without
  engine-only palette ramps. Its diagnostic viewer is separate from the three-tier review viewer.
- Prior no-FX revision: **41 binding assertions**, one all-binding asset-load smoke check, browser tier/clip switches
  and indoor/outdoor checks passed. This amplitude-only follow-up rechecked animation/export invariants and playback.
  The baseline MM8 actor suite passed **50 cases**; full game tests were not rerun for this follow-up.
- Native/model comparisons use New Sorpigal `oute3.odm` and Agar's Laboratory `6d19.blv`, with all three tiers.
  The native fixture mounts unchanged m601/m602/m603 sprite definitions for cross-world spawning.
  Death is triggered with an Incinerate test cast: the normal physical debug kill is ineffective against native immunity.
- Native source hashes are checked at delivery. Desktop OpenGL on the NVIDIA GPU is the visual target; Android,
  Vulkan and performance benchmarking were not run.

## Attack revision — 2026-10-18

Removed both mouth effect meshes/materials and their four control bones from the runtime, viewer and editable master.
The initial extra movement was rejected as excessive. Added eye-stalk bends and tip motion now use **20%** of that
amplitude, with roughly half the reversal frequency. The one-second duration, mouth
motion and endpoints are preserved. The embedded eyes retain their socket attachment.

[Revision invariants](review/attack_subtle/invariants.json) compare the retained previous delivery at 120 Hz:
body topology, normals, UVs, weights, all colour/shadow LODs, six other clips and non-eye Attack transforms are unchanged.
[Attack playback](review/attack_subtle/playback/) and [runtime evidence](review/runtime_checks.json) belong to this
revision. The prior revision’s indoor/outdoor checks remain recorded in `work/attack_revision_strong/runtime_checks.json`;
they were not rerun for this amplitude-only adjustment. Earlier full-production captures remain under `review/playback/` and `review/ingame/`.

## Provenance and reproduction

Five generated HD references follow the native anatomy; [generation records](references_hd/generation_runs.json)
retain prompts, inputs and hashes. Only generated HD references were uploaded to Meshy.
Meshy spend: **15 / 100 credits** — Smart Topology 5, texture generation 10. Task receipts and downloads are in the
canonical progress record and `meshy/`. No paid animation job was needed.

Retain the geometry and downloaded texture jobs. With an active creature lease, run the scripts using
`tools/run_creature_blender.sh` for Blender and `tools/creature_workspace.py run` for ordinary Python mutations:

1. `export_checked.py` rebuilds the fitted rig/actions, transfers the downloaded UVs, exports and checks pose parity.
2. `compose.py` updates shared maps and native ramps when texture inputs change; re-export to embed changed maps.
3. `prepare_runtime.py` converts normal convention and restores the ORM specular channel.
4. Blender `build_lods.py`, then `finalize.py`, `validate.py` and Blender `editable_delivery.py`.
5. `tools/install_model.py export/mm8_m600.glb --world mm8` installs source and cooked desktop assets.
6. Refresh the browser and native visual evidence after an affected change.

Installed source: `assets_source/worlds/mm8/models/mm8_m600.glb`.
Runtime: `assets_dev/worlds/mm8/models/mm8_m600.glb`; bindings: `assets_dev/worlds/mm8/models/actors.yml`.
Front lip and eye-socket skin follow their rigid anatomical owners during body motion.
No renderer or gameplay implementation change is required.
