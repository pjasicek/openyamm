# MM6 Ogre 3D — revision 03

Running A (weighted run), Attack A (standing downward chop) and Fidget A (neck stretching) are installed for all three tiers. The user selected these from the Mixamo comparison viewer on 2026-10-11. Current Hit is retained: the focused game regression verifies its 60 ms entry and 120 ms exit from/to Standing, Running, Attack and Fidget, including unchanged transition-start poses and halfway samples. The recoil's crouch remains intentional.

The approved revision 02 head, body, sword, textures, LODs and five other animation streams are unchanged. New motion, checks and native captures are under `revision_03/`; prior production files are preserved under `revision_03/previous/`. The comparison viewer remains a historical A/B/previous-set comparison.

## Review

- [Interactive viewer](http://127.0.0.1:8903/level_generation/creatures/mm6_ogr_claude/review/viewer/): three tiers, eight clips, native references and slow playback.
- [Head close-up](revision_02/review/head.png), [quarter view](revision_02/review/head_quarter.png), [upright run](revision_02/review/run.png), [outdoors](revision_02/runtime/outdoor/tiers.png), [indoors](revision_02/runtime/indoor/tiers.png), [held corpse](revision_02/runtime/motion/dead_held.png).
- [Packed editable Blender master](export/mm6_ogr.blend), [runtime body](export/mm6_ogr.glb), [separate sword](export/mm6_ogr_sword.glb).
- [Animation sources and fitting](ANIMATION_STUDY.md), [asset hashes/validation](export/validation.json), [dense clearance](revision_02/motion/dense_clearance.json), [UV validation](work/uv_gate.json), [focused regression](revision_02/checks/ogre_regression.log).

`creature_3d_progress.json` is the canonical state. Earlier artwork, motions and evidence describe revision 01; its export/viewer are preserved under `revision_02/previous/`. Restart the shared viewer from the repository root with `python3 -m http.server 8903 --bind 127.0.0.1` if needed.

## Native identity and runtime contract

Original evidence is `../mm6_ogr/inventory.json`, its BMP-derived frames and `revision_02/native_head.png`. IDs 592/593/594 use Ogre A/B/C and palettes 783/784/785. Only the spikes change colour between tiers. The retained body has three long fingers plus a thumb, three clawed toes, paired spiked armour, crossed harness/skull medallion, belt, loin panels and shin wraps.

The native 248-pixel standing silhouette at sprite scale 0.799988 measures 198.397 world units. The replacement library standing pose measures 1.721017 m, giving binding scale **115.279**. Yaw remains -1.570796327, stride 1.25 m and melee impact 0.866666667 s (source frame 26). The sword is a static attachment at the animated Sword node. Cast/ranged slots retain the Attack alias; no gameplay capability or monster table changed.

| Asset | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| Body | 12,166 | 6,097 | 2,197 | 725 |
| Sword | 236 | 102 | 32 | 9 |

The body has one material draw per LOD, at most eight influences, fitted shadow meshes and a merged 2080 × 1024 atlas. The runtime keeps MR.R as its specular mask, MR.G as roughness and MR.B as metallic, with `openyamm_specular_mask: true`. The export preparation restores MR.R after Blender packing. Skin is matte; palette variants use the retained region ramps.

## Head production and receipts

`revision_02/references_head/` retains five generated views, original returns, prompts, hashes and review. The original mouth/eye topology did not support an acceptable projection, so the new Meshy 7.1 head replaces it with a welded neckline. The head retains its generated UVs and has 3,728 triangles including the join. The rest of the body keeps its existing UVs and textures. The seam uses skin colour/detail transfer through the joined neck; head normals were baked from the detailed source.

The new head job cost **30 Meshy credits**. Total project spend is **60 of the 100-credit limit**, including the original topology, rig and textures. No paid animations were used. Requests, receipts and untouched downloads are retained under `requests/` and `meshy/head_model_v2/`.

## Revision 03 verification

- Build and focused Ogre regression passed; all three skins, clips, LODs and attachments load, and the real WorldFxSystem path passes Hit transition checks for all four neighbouring states.
- Existing interrupted-pose blending unit test: 22 assertions passed. Viewer: 24 tier/clip switches and all 16 normal/quarter-speed playback combinations passed.
- Dense 60 Hz selected-motion checks: finite unit-scale bones, maximum hand-edge stretch 3.594, no detected sword/body penetration, closed Running seam. The source's 0.51-degree seam difference was closed only across its final three frames.
- Exact preservation checks cover existing mesh/material/skin/node documents, binary geometry/texture buffers and the five retained animation streams. Package validation passes.
- Native OpenGL/Wayland NVIDIA checks cover outdoor combat/damage recovery and all three tiers indoors. Native screenshots after damage are appearance evidence; precise 60/120 ms transitions are verified by the game regression, since screenshot-tour latency is coarser.
- No Android/Vulkan run or broad regression rerun. The historical broad-suite limitation below still applies.

## Revision 02 verification (retained evidence)

The revision 02 master is `work/rig_v15.blend`. Revision 03 uses `revision_03/selected_motion.blend` (also copied to `export/mm6_ogr.blend`). The selected source-frame library clips are listed with file hashes in `revision_02/motion/selection.json`. Fitting preserves their body choreography and timing; it adds grip, twist, cloth, floor and replacement-head clearance adjustments.

- UV checks: no collapsed visible triangles; body overlap 0%; head overlap 0.0177%; all regions exceed 1 pixel/cm at 1K.
- Arm sweep: maximum p99 edge stretch 1.95. Dense 48 Hz checks: maximum head/shoulder depth 6.56 mm, cloth depth 0.40 mm. The approximate head gate excludes the connected neck itself. The older skin-side cloth heuristic misclassifies exposed free-edge skin; the direct cloth-to-skin test and visual review are the applicable evidence.
- Exported curved sword sweep: no detected body penetration. Source-relative rotation traces: zero flags. All eight clips completed normal and quarter-speed playback; 24 tier/clip switches had no browser errors.
- Package validation: finite accessors, valid indices, normalized weights, eight clips, three variants, four LODs, static attachment, closed loop endpoints and exact preservation of animation samples through post-processing.
- Normal `openyamm` build passed. The focused `mm6_ogr_actor_models_bind_all_tiers` regression passes on the installed package. The broad actor suite passed 37 cases, including Ogre, then crashed in the following Hive demon test during `MapDeltaData` copying. Logs/backtrace are retained in `revision_02/checks/`; that broader suite is **not** reported as passing.
- Engine-native NVIDIA/Wayland captures cover all tiers and LODs indoors (`6d19.blv`) and outdoors (`oute3.odm`), movement, damage, library death and held corpse. Records include launch settings and binary hashes. Native sprite comparisons from revision 01 remain under `review/indoor_sprite/` and `review/outdoor_sprite/`; camera positions are retained. These are appearance checks, not performance benchmarks.

Final geometry/animation playback preceded the last neck colour adjustment; the final texture was checked again in the viewer and native captures. The sampled tests do not prove every runtime blend or head-look combination. Android and Vulkan were not checked.

## Re-export

With a fresh creature lease, run `tools/run_creature_blender.sh --token <token> level_generation/creatures/mm6_ogr_claude/scripts/build_final.py`. It uses the gated body master plus the three selected actions from `revision_03/selected_motion.blend` and final textures, builds LODs/shadows/variants, splits the sword, merges materials, refreshes the shared viewer, validates and installs both GLBs. Earlier revision scripts and experiments are historical fitting steps, not an alternative production entry point. No commit was made.
