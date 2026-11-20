# MM6 Medusa — Claude workflow

Built and installed 2026-10-12. Technical and agent visual review complete; user artistic acceptance is not recorded.

[Interactive viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_med_claude/review/viewer/) ·
[Outdoor comparison](review/ingame/outdoor_comparison.jpg) · [Indoor comparison](review/ingame/indoor_comparison.jpg)

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
Hit fits its native 0.75 s. Running is a faster slither. The native whole-head attack palette flash is interpreted
through crown movement, eye embers and the existing spell-charge socket glow. Hidden snake roots and corpse depth
are inferred from the [native motion study](ANIMATION_STUDY.md), not claimed as exact frame reconstruction.

Meshy: **40 of 100 credits** — body geometry 5, detailed head 5, head texture 10, two body texture passes 20.
`body_retexture_v2` and `head_retexture_v1` are selected. V1 body texture is preserved but superseded: the headless
upload displaced the bodice projection. Body V2 UVs were transferred by exact triangle correspondence; the fitted
rig and animation master were retained. Source prompts, original returns, hashes and corrections remain in
[creature_3d_progress.json](creature_3d_progress.json), `references_hd/`, `references_head/`, `requests/` and `meshy/`.

Checks: ordinary `openyamm` build; **39/39 MM6 actor regressions**; **27/27 viewer tier/clip combinations**;
all nine clips at normal and quarter speed; face, hands, shoulder seams and tail views; isolated Blender reimport
(max surface difference 0.021 mm, socket difference 0.003 mm); native OpenGL/Wayland captures on NVIDIA indoors
(Agar's Laboratory) and outdoors (New Sorpigal), same camera for sprite/model, all tiers and death/remains.
Evidence is in `review/checks/`, `review/export_parity.json`, `review/browser/` and `review/ingame/`.
The initial playback recording predates only the hip palette-mask correction; geometry and animation channels
were unchanged. Final tier closeups and native captures verify the corrected materials.
Vulkan and Android were not tested. No engine feature changes or commits were made for this creature.

To reproduce from the selected local master, claim this family with `tools/creature_workspace.py`, then run guarded
`compose_medusa.py`, Blender `export_medusa.py`, `tools/prepare_actor_glb.py`, Blender `build_lods.py`,
`finish_runtime.py`, `viewer_tiers.py`, and `update_viewer_manifest.py`, in that order. Use the standard
`tools/run_creature_blender.sh --token <token>` for Blender scripts and `creature_workspace.py run` for ordinary
scripts. `pack_editable.py` applies the extracted tier A albedos to the packed editable copy after runtime export.
`export_parity.py` and `validate_delivery.py` verify the deliverables. Retexturing or rig rebuilding is unnecessary
for playback or palette adjustments. Keep `work/textured_master.blend` as the selected rig/UV master.
