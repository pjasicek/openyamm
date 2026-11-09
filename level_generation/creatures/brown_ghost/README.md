# Brown ghost — rigged 3D character

Revision 3: an original Blender mesh based on the silhouette and motions in `assets_dev/engine/sprites/m242*.bmp`:
aged skeletal face, exposed ribs and hands, floating legless body, hood, and ragged brown cloth.
Authored and visually reviewed through Blender MCP. The source asset is a **3D character** with a rig and animations.
Its [directional sprite export](spritesheets/README.md) includes transparent animation sheets, indexed BMP frames,
playback previews and a packaged ZIP, rendered from this model.

For the reusable agent procedure, read [Sprite-to-3D workflow](../SPRITE_TO_3D_WORKFLOW.md). It combines the accepted
restoration, modeling, material and animation findings; this file contains the `m242`-specific asset and build details.

## Open and animate

Open `brown_ghost.blend`. The isolated character scene includes the mesh, **32-bone armature**, brown materials,
packed color texture, lights, camera, and animation. No external texture download is needed.
`brown_ghost.glb` is the portable version with skin weights, skeletal animation, cloth morphs and a color atlas.
Mesh counts and export checks are recorded in `review/validation.json` and `review/glb_validation.json`.
Earlier models are preserved in `revisions/v1/` and `revisions/v2/`. See `ART_CALIBRATION.md` and
[the AI restoration references](reference_restoration/README.md) for the visual calibration and exact prompt set.

Select **Ghost RIG**, enter Pose Mode, and pose the named bones. Controls include root, body, head,
upper arms, forearms, hands, two bones per finger, and three cloak controls.
Every mesh vertex is weighted. Mesh shape keys provide cloth and pose corrections in addition to bone animation.
For a new custom pose, mute the rig's and mesh shape keys' NLA tracks together, clear the active bone transforms,
and zero the corrective shape keys; then pose the armature. Cloth is animated with deterministic corrections,
not a cloth simulation requiring a cache.

The timeline plays the seven clips sequentially. Markers show their starts:

| Clip | Timeline frames | Reference behavior |
| --- | --- | --- |
| Standing | 1–49 | Two-second idle: bobbing, hands and delayed cloth movement |
| Attack | 50–80 | Anticipation, raised grasp, quick reaching stroke, recovery |
| Float | 81–117 | 1.5-second floating loop; body and cloth move with phase offsets |
| Hit | 118–136 | Quick recoil followed by recovery |
| Death | 137–179 | Recoil, loss of height and collapse into cloth and bones |
| Corpse | 180–181 | Collapsed held pose |
| Fidget | 182–218 | Hand/body gesture with return to the initial pose |

Each clip has matching **bones** and **cloth correctives** actions and NLA tracks.
Keep both components together when moving, trimming, or exporting a clip.
`animations.json` records clip ranges and source pose samples. The studio runs at **24 fps**, with 218 timeline
samples derived from 69 authored rig/geometry anchors. Bone transforms and cloth corrections are evaluated at
intermediate times; these are not duplicate sprite frames. Clip endpoints close loops or hold the corpse as appropriate.
Animation timing and final game-world scale can be adjusted during integration.

## Reference audit

The `m242` texture family is used by **Ghost A/B/C** descriptor rows and sprite groups **m243/m244/m245**;
there is no corresponding `m242.yml` frame group. These groups differ in palette/tint selection.
See `assets_dev/engine/data_tables/monster_descriptors.txt` and
`assets_dev/engine/rendering/sprite_frames/monsters/m243.yml`, `m244.yml`, `m245.yml`.

The 124 original images comprise standing 1×5, attack 8×5, movement 8×5, hit 6×5,
four additional death frames, one corpse frame, and four fidget frames.
Directions 0–4 run front through side to rear; runtime mirrors directions 5–7.
Death and fidget use single-image frames. Both melee and ranged attack slots reuse the same attack group.
The six-frame death animation starts with `m242na0` and `m242nb0`, then `m242da0`–`m242dd0`.
The new model is fully three-dimensional and can be viewed from any direction.

The reference's saturated violet cloth is replaced by weathered umber/brown cloth and aged ivory bones.
Its silhouette and animation staging guide this model; it is not an exact reconstruction. Revision 2 replaces the
rounded hood/face, narrow robe and weak hands with a pointed hood, recessed angular sockets, denser ribs, layered
cloth tears and hooked fingers. The death clip uses the original recoil-before-collapse ordering with new poses. Revision 3 replaces the facial
outlines with a connected skull sculpt guided by AI-restored native views. The forehead, cheeks and maxilla surround
real carved cavities; the teeth are separate anatomical teeth. Frontal restoration color is projected onto the skull
and baked with the other character materials. The body follows the same restored views: a narrower continuous shroud
with long folds and torn hems, a small V-shaped chest opening, curved flattened ribs, tapered limb bones and long
jointed fingers that hang across the robe. Brown woven fabric is generated from the restored robe's surface character.
Bones and tooth enamel share aged ivory shading; teeth are explicitly excluded from the dark mouth-cavity material.
Their pigment is sampled from the same restored skull reference, with a shared fine-relief/satin treatment to avoid
chalky limbs beside the face. The hood is fitted more closely around the unchanged skull; see the `1252.png` follow-up
in `ART_CALIBRATION.md`.
`revisions/v3_skull_draft/` preserves the accepted skull with the older body for comparison.
Original game sprites, descriptors and map content are untouched. This asset is not installed into the game yet.

## Files and reproduction

- `brown_ghost.blend`: editable model, rig, animation and material source.
- `brown_ghost.glb`: portable rigged model with named animation clips.
- `textures/brown_ghost_albedo.png`: 4096×4096 baked color atlas, also embedded in both model formats.
- `review/`: directional views, pose renders, animation preview and validation results.
- `sculpt_skull_blender.py`: creates the connected skull sculpture and mesh cache.
- `skull_projection_material.py`: projects restoration color onto the carved face while keeping side/rear bone neutral.
- `author_blender.py`: embeds that sculpt and creates geometry, weights, bone animation and cloth corrections.
- `finish_blender.py`: makes the named clips, packs reference images and renders review views.
- `export_blender.py`: bakes the portable atlas and exports GLB.
- `normalize_blend.py`: turns the isolated library save into a normal project and verifies the rig.
- `review_asset.py`: assembles previews and checks the GLB skeleton, animations and texture.
- `review_body.py`: compares the native sprite, restored view, older body and final body at a useful display scale.
- `render_sprites_blender.py`: samples the finished clips in five directions with a common camera and ground pivot.
- `pack_sprites.py`: creates directional sheets, mirrored PNG frames, shared-palette BMPs and the sprite ZIP.

The selected AI references are already saved in `reference_restoration/`. Read that folder's README before revising
them; it documents the built-in image-generation prompts and corrected pose drift.

For fast visual iteration, execute `author_blender.py` as an imported module in Blender and call
`build(preview_only=True, preview_pose=('s', 0))`. Use `('a', .6)` for the raised attack and `('x', 0)` for the corpse.
This builds a temporary single-pose scene without replacing the saved model or `poses.json`. Review its renders,
adjust geometry/materials, then run the full build once the shape is ready. Do not export the temporary preview scene
as the finished animated asset.

Run `sculpt_skull_blender.py`, `author_blender.py`, `finish_blender.py`, then `export_blender.py` inside Blender using
MCP `execute_blender_code`. The sculpt step is needed when rebuilding or changing the skull cache.
They target only the named ghost scene; they do not delete other project scenes or restart the MCP service.
For long work, schedule execution with a Blender timer and write completion/error status to disk.
After the MCP authoring/export steps finish, normalize the isolated library save into a normal project:

```sh
blender -b level_generation/creatures/brown_ghost/brown_ghost.blend --python level_generation/creatures/brown_ghost/normalize_blend.py
python3 level_generation/creatures/brown_ghost/review_asset.py
python3 level_generation/creatures/brown_ghost/review_body.py
```

This separate background process does not stop the GUI Blender MCP connection.
Paths currently point to this repository checkout; update `ROOT` when moving the authoring scripts.

Review front, profile, rear and three-quarter views, then attack extremes, floating extremes, hit and collapsed
poses. Check hand clearance, continuity of the hood/shoulders, cloth silhouette and ground contact.
Use the quick structural export checks and visual previews; no map scenario runner is needed for this asset.
