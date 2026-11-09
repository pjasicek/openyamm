# MM6 Medusa — Claude workflow

Revision 4 built and installed 2026-10-12. Technical and agent visual review complete for Medusa. User accepted revision 4 on 2026-10-12.

[Interactive viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_med_claude/review/viewer/) ·
[Current outdoor capture](review/ingame/v4/outdoor/outdoor_models_02.png) · [Prior indoor capture (v2)](review/ingame/v2/indoor/indoor_models_02.png)

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
Hit fits its native 0.75 s. Revision 2 gives Walk and Running a stronger travelling wave in the rear tail and a smaller torso sway. Revision 4 Attack uses a larger backward/forward and sideways coil with shoulder turn.
Hands draw up and back with bent elbows during preparation, then sweep forward/outward and open during the gaze
release, with slightly staggered left/right timing and wrist motion. The head remains directed toward the target
at release. The body and hands follow through and settle together. Cast uses the exact same motion, holding the last pose to its original 1.5 s duration. The native whole-head attack palette flash is interpreted
through crown movement, eye embers and the existing spell-charge socket glow. Hidden snake roots and corpse depth
are inferred from the [native motion study](ANIMATION_STUDY.md), not claimed as exact frame reconstruction.

Meshy: **40 of 100 credits** — body geometry 5, detailed head 5, head texture 10, two body texture passes 20.
`body_retexture_v2` and `head_retexture_v1` are selected. V1 body texture is preserved but superseded: the headless
upload displaced the bodice projection. Body V2 UVs were transferred by exact triangle correspondence; the fitted
rig and animation master were retained. Source prompts, original returns, hashes and corrections remain in
[creature_3d_progress.json](creature_3d_progress.json), `references_hd/`, `references_head/`, `requests/` and `meshy/`.

Revision 4 checks: **27/27 viewer tier/clip combinations**, full Attack/Cast playback at normal and quarter speed
from front and three-quarter views, side poses and hands/arms close-ups; all-clip deformation/ground gates and
Blender export reimport parity. Only Attack/Cast animation samples changed; the other seven clips and all
geometry/UVs/weights match v3 exactly. Attack/Cast channels match exactly through release and recovery.
The focused Medusa regression passes **1/1**. Native outdoor checks used all tiers on NVIDIA OpenGL/Wayland.
Evidence: `review/checks/*v4*`, `review/browser_v4/`, `review/ingame/v4/` and `review/export_parity.json`.
Full-suite and indoor evidence from earlier revisions remains historical; no full-suite, indoor, Vulkan or Android
rerun was performed for this scoped motion edit. No Meshy credits, engine changes, rebuilds or commits were needed.
Previous selected masters and review records are under `revisions/v1/`, `revisions/v2/` and `revisions/v3/`.

Triangle reduction was evaluated at 9,983, 11,919, 12,260 and 13,856 triangles. The lower trials distorted textures
or shoulders; even the conservative tail-only trial visibly flattened the belly/tail curve. The selected full-detail
mesh stays at **14,900 triangles**, with the existing distance LOD savings. See
[reduction decision](review/reduction_decision.json). Earlier masters/exports are retained under `revisions/`.
No additional Meshy credits were spent.

To reproduce from the selected local master, claim this family with `tools/creature_workspace.py`, then run guarded
Blender `export_medusa.py`, `tools/prepare_actor_glb.py`, Blender `build_lods.py`,
`finish_runtime.py`, `viewer_tiers.py`, and `update_viewer_manifest.py`, in that order. Use the standard
`tools/run_creature_blender.sh --token <token>` for Blender scripts and `creature_workspace.py run` for ordinary
scripts. `pack_editable.py` applies the extracted tier A albedos to the packed editable copy after runtime export.
`export_parity.py` and `validate_delivery.py` verify the deliverables. Retexturing or rig rebuilding is unnecessary
for playback or palette adjustments. Keep `work/textured_master.blend` as the selected rig/UV master.

To rebake revision 4 motion from the retained v1 fitted master, run guarded Blender `animate_reduced.py`; it writes `work/motion_v4.blend` and `work/animation_audit_v4.json`. After review, copy that blend to `work/textured_master.blend`, then follow the export steps above. Materials are already composed and need no regeneration.
