# MM6 goblin: rigged model and directional sprites

**2026-09-28 planning follow-up:** [New Blender rebuild at roughly 10K triangles](blender_rebuild_20260928/README.md),
with a [3D-attempt audit](blender_rebuild_20260928/ATTEMPT_AUDIT.md) and
[visual reference board](blender_rebuild_20260928/references.html). That study covers this original Blender asset
and the later Meshy branches. The files and delivery description below document the historical September 8 model.

An original 3D reconstruction of the MM6 `gob` sprite family, built against native frames and reviewed AI restorations.
The final character uses continuous head/neck geometry, olive skin, worn iron and brass, leather strips, and a
right-hand scimitar. It has an editable 88-bone rig and seven animated clips. Original game assets are unchanged.

## Open and inspect

```sh
blender level_generation/creatures/mm6_goblin/mm6_goblin.blend
```

- [Editable packed Blender project](mm6_goblin.blend) and [portable GLB](mm6_goblin.glb).
- [Native → restored → model comparison](review/native_restored_model.png): front, oblique, profile and rear.
- [Actual GLB close-up renders](review/export_glb/), including [head](review/export_glb/head.png),
  [hand](review/export_glb/hand.png), [feet](review/export_glb/feet.png) and [oblique](review/export_glb/oblique.png).
- [Actual GLB animation playback](review/motion_playback_final_glb/README.md),
  [walking](review/motion_playback_final_glb/walk.gif) and [attack](review/motion_playback_final_glb/attack.gif).
- [Directional sprite instructions](spritesheets/README.md) and [sprite ZIP](spritesheets/mm6_goblin_mm_sprites.zip).
- [Completion evidence](DELIVERY_AUDIT.md), [progress](PROGRESS.md) and [calibration history](ART_CALIBRATION.md).

Select **MM6 Goblin Rig**, open the Action Editor, choose a clip and set the timeline range below. If assigning an
Action in Python, also assign `rig.animation_data.action_slot = action.slots[0]`; a missing slot silently prevents
animation. The saved project starts in Standing. The GLB's clip timestamps start at zero.

| Clip | Editable Blender frames, 24 fps | Duration | Behavior |
| --- | --- | --- | --- |
| Standing | 1–49 | 2 s | Breathing loop; extends native static pose |
| Walk | 1–19 | 0.75 s | In-place loop |
| Attack | 1–19 | 0.75 s | Anticipation, diagonal slash, recovery |
| Hit | 1–19 | 0.75 s | Free arm shields face during recoil |
| Death | 1–16, fractional keys | 0.625 s | Collapse to prone endpoint |
| Corpse | 1–4 | 0.125 s, held | Identical to Death endpoint |
| Fidget | 1–19 | 0.75 s | Restrained idle variation |

Walk travels toward **-Y** at **0.853333 m/s**, using a 0.64 m full-cycle stride. Units are meters and Blender is Z-up;
GLB uses the standard Y-up export conversion. Apply matching actor translation when inspecting planted feet.
Preserve Death's fractional-frame keys during export; rounding them to ordinary 24-fps samples reintroduced floor
intersections in an earlier revision.

For manual posing, unlink the active Action, disable any NLA playback you add, enter Pose Mode, select all bones and
reset location/rotation/scale. This is an editable FK rig: `root` moves the character, named limbs/digits pose the body,
`weapon.R` controls the scimitar and `skirt.00`–`skirt.21` control leather strips. There are no runtime corrective
drivers to disable; clothing corrections are baked into bone keys. Use Armature → Rest Position to edit the neutral
mesh, then restore Pose Position. Save edits as a new revision rather than overwriting the source of delivered sprites.

## Asset size and consumer limits

The game mesh has **206,722 triangles**, 103,921 Blender vertices and 140,185 GLB vertices after UV/material splitting.
One skin uses 88 bones with at most four normalized influences per vertex. Fourteen material regions share three
4096² textures: base color, tangent normal and ORM (R=1, G=roughness, B=metallic). All GLB primitives include tangents.
Detailed source geometry is retained in the authoring checkpoints; face vertices were protected during reduction.

The three textures cost about **192 MiB uncompressed RGBA8**, or **256 MiB with mipmaps**, before consumer-specific
compression or channel formats. The optional region mask adds 64 MiB / approximately 85.3 MiB respectively if loaded
as RGBA8. It identifies skin (red), leather (green), iron/steel (blue), brass (yellow), teeth/claws (magenta), eyes
(cyan), and cavities (black). No three-variant palette set or LOD chain is supplied. See
[asset statistics](export_work/asset_stats.json) for current sizes and hashes.

Actual exported appearance and all seven clips were checked through Blender 5.2.1's glTF importer and rendered
playback. The export uses `KHR_materials_specular`; a consumer without that extension can differ in highlights.
Blender's small skin subsurface contribution is not represented in this GLB. The reimport was visually reviewed,
but another engine's lighting/renderer may differ. This is a detailed stylized reconstruction, not proof that lost
original high-resolution art was recovered, and the chosen stylized finish remains open to artistic feedback.

The character and sprites are staged here. Actor installation, live registry IDs, runtime scale/anchor integration,
collision dimensions and engine LOD/performance tuning are outside this goal. No gameplay tables were changed.

## References and reproduction

[Source manifest](source_manifest.json) inventories 59 native BMPs, hashes, palettes, timing and anchors.
[Source contact sheets](source_audit/) and [AI reference index](reference_restoration/README.md) record the original
views, exact generation prompts, selected references and rejected interpretations. Read
[the generic workflow](../SPRITE_TO_3D_WORKFLOW.md) and [case calibration](ART_CALIBRATION.md) before authoring changes.

The authoritative detailed source is `animations/animation_library.blend`, scene
`MM6 Goblin final motion studio` (neck 3, surface/detail 2, motion 10).
`animations/manifest.json` records action names and timing. Older `review/mm6_goblin_working.blend` and numbered
review/revision folders are historical checkpoints; the top-level model files are the delivery.

Authoring scripts form a staged workflow: `sculpt_head.py` / `build_body.py` → `rig_character.py` →
`finish_surfaces.py` / `refine_details.py` / `refine_neck.py` → `animate_character.py`.
`body_landmarks.json`, the source libraries and reviewed AI inputs preserve the measured construction. These scripts
were iterated through Blender MCP; they intentionally refuse to overwrite an existing owned authoring scene.
Inspect the scene and preserve a checkpoint before rerunning a stage. Do not run every historical revision in sequence.

From the current accepted animation checkpoint, the delivery pipeline is:

```sh
blender -b level_generation/creatures/mm6_goblin/animations/animation_library.blend --python level_generation/creatures/mm6_goblin/prepare_export_mesh.py
blender -b level_generation/creatures/mm6_goblin/export_work/game_mesh_library.blend --python level_generation/creatures/mm6_goblin/bake_materials.py
blender -b level_generation/creatures/mm6_goblin/export_work/baked_library.blend --python level_generation/creatures/mm6_goblin/export_character.py
blender -b level_generation/creatures/mm6_goblin/mm6_goblin.blend --python level_generation/creatures/mm6_goblin/review_glb.py
blender -b level_generation/creatures/mm6_goblin/mm6_goblin.blend --python level_generation/creatures/mm6_goblin/render_sprites.py
python3 level_generation/creatures/mm6_goblin/pack_sprites.py
```

Archive existing delivery artifacts before rebuilding. Sprite rendering verifies its saved model hash and refuses
to mix revisions: archive the old sprite output directory before rendering a changed model. Review matched export
views and actual imported playback before committing to another full sprite batch. `make_comparison.py` generates
the four-view comparison. `review_motion.py` can render playback with the imported manifest override; its invocation
and sample mapping are recorded in the playback README. ZIP creation is separate from packing so output can first
be visually reviewed. Focused geometry, timing, image and source-integrity checks are sufficient here; no engine build
or map scenario suite was needed.
