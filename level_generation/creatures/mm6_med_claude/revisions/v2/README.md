# MM6 Medusa — Claude workflow

Revision 2 built and installed 2026-10-12. Technical and agent visual review complete for Medusa; user artistic acceptance of this revision is not recorded.

[Interactive viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_med_claude/review/viewer/) ·
[Current outdoor capture](review/ingame/v2/outdoor/outdoor_models_02.png) · [Current indoor capture](review/ingame/v2/indoor/indoor_models_02.png)

| Monster | Descriptor | Skin | Palette |
| --- | --- | --- | --- |
| 574 Medusa | BMedusa A | med_a | 769 |
| 575 Medusa Enchantress | BMedusa B | med_b | 250 |
| 576 Gorgon | BMedusa C | med_c | 251 |

Editable packed master: [export/mm6_med.blend](export/mm6_med.blend), with tier A colours.
Portable animated GLBs: [A](export/mm6_med_portable_a.glb), [B](export/mm6_med_portable_b.glb),
[C](export/mm6_med_portable_c.glb). These have baked tier colours for ordinary glTF viewers.
[Runtime GLB](export/mm6_med.glb) is installed as `assets_dev/worlds/mm6/models/mm6_med.glb`; the three bindings
are in that folder's `actors.yml`. It shares palette ramps and merged body/head materials.

14,900 / 7,449 / 2,672 / 883 triangles across four colour LODs, plus shadow LODs; 107 bones, eleven articulated
snake chains and five fitted digits on each hand. Full detail has four weights per vertex; reduced LODs use up to
eight, supported by the current engine. Body and head retain separate 1K texel density inside 2080×1024 runtime
atlases. [Native region ramps](textures/med_ramps.json) drive armour, belly and green skin. Gold, eyes and tongues
retain their authored colours. Normal maps use glTF +Y-up; packed material channels are specular mask / roughness /
metallic, as required by the engine.

Nine clips: Standing, Walk, Running, Fidget, Attack, Cast, Hit, Death and Dead. See [clip durations](export/clips.json)
and [effects/sockets](export/effects.json). Attack and Cast release at 0.75 s without changing native gameplay timing;
Hit fits its native 0.75 s. Revision 2 gives Walk and Running a stronger travelling wave in the rear tail and a smaller torso sway. Attack leans the head and torso back during preparation (peak 0.36 s), then forward for the gaze release (0.75 s) before recovery. Cast uses the exact same motion, holding the last pose to its original 1.5 s duration. The native whole-head attack palette flash is interpreted
through crown movement, eye embers and the existing spell-charge socket glow. Hidden snake roots and corpse depth
are inferred from the [native motion study](ANIMATION_STUDY.md), not claimed as exact frame reconstruction.

Meshy: **40 of 100 credits** — body geometry 5, detailed head 5, head texture 10, two body texture passes 20.
`body_retexture_v2` and `head_retexture_v1` are selected. V1 body texture is preserved but superseded: the headless
upload displaced the bodice projection. Body V2 UVs were transferred by exact triangle correspondence; the fitted
rig and animation master were retained. Source prompts, original returns, hashes and corrections remain in
[creature_3d_progress.json](creature_3d_progress.json), `references_hd/`, `references_head/`, `requests/` and `meshy/`.

Revision 2 checks: **27/27 viewer tier/clip combinations**, all nine clips at normal and quarter speed;
loop/deformation gates; exact unchanged geometry, UVs, normals and skin weights relative to v1; exact Attack/Cast
channel agreement; isolated Blender reimport (max surface difference 0.021 mm, socket difference 0.004 mm);
native OpenGL/Wayland NVIDIA checks indoors and outdoors, all tiers plus collapse/remains.
The MM6 actor suite passed **41/42**, including Medusa. The sole failure is the separate concurrent Lizard Archer
integration (`lizard tier 0 has no posed model`). Its earlier invalid cast binding blocked the entire manifest;
its owner removed the bindings before the final runs. This task changed no Lizard assets or shared bindings.
See `review/checks/*v2*`, `review/export_parity.json`, `review/browser_v2/`, and `review/ingame/v2/`.
The ordinary build and original sprite/model comparisons from v1 remain valid baseline evidence; no engine code
changed or rebuild was needed here. Vulkan and Android were not tested. No commits were made.

Triangle reduction was evaluated at 9,983, 11,919, 12,260 and 13,856 triangles. The lower trials distorted textures
or shoulders; even the conservative tail-only trial visibly flattened the belly/tail curve. The selected full-detail
mesh stays at **14,900 triangles**, with the existing distance LOD savings. See
[reduction decision](review/reduction_decision.json). Revision 1 masters/exports are retained in `revisions/v1/`.
No additional Meshy credits were spent.

To reproduce from the selected local master, claim this family with `tools/creature_workspace.py`, then run guarded
Blender `export_medusa.py`, `tools/prepare_actor_glb.py`, Blender `build_lods.py`,
`finish_runtime.py`, `viewer_tiers.py`, and `update_viewer_manifest.py`, in that order. Use the standard
`tools/run_creature_blender.sh --token <token>` for Blender scripts and `creature_workspace.py run` for ordinary
scripts. `pack_editable.py` applies the extracted tier A albedos to the packed editable copy after runtime export.
`export_parity.py` and `validate_delivery.py` verify the deliverables. Retexturing or rig rebuilding is unnecessary
for playback or palette adjustments. Keep `work/textured_master.blend` as the selected rig/UV master.

To rebake revision 2 motion from the retained v1 fitted master, run guarded Blender `animate_reduced.py`; it writes `work/motion_v2.blend` and `work/animation_audit_v2.json`. After review, copy that blend to `work/textured_master.blend`, then follow the export steps above. Materials are already composed and need no regeneration.
