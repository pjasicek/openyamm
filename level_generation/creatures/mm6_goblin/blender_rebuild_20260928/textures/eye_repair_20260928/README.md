# Local eye-paint repair, 2026-09-28

The duplicate eyes painted above the modeled eye openings have been removed. The original Meshy GLB and extracted
JPEGs in `../meshy_20260928/` are preserved. Updated delivery files are `../../delivery/mm6_goblin_textured.blend`
and `../../delivery/mm6_goblin_textured_rigged.glb`.

## Selected repair

- Mode: **built-in imagegen**, precise-object-edit; one generated result.
- [Exact prompt](prompt.txt).
- [Input patch](face_patch_input.png): 320×320 crop at atlas pixel `(585,1245)`, rotated 90° counterclockwise and
  enlarged three times for inspection and editing.
- [Selected generated patch](generated_face_patch.png), copied into the repository from the built-in tool's result.
- [Atlas repair mask](repair_mask.png): two feathered regions around the erroneous skin-painted eyes. Its support is
  5,730 pixels, 0.137% of the 2048² atlas. The AI output is used only inside this mask; it cannot alter other islands.
- [Base color](base_color.png), [tangent normals](normal.png), [metallic/roughness](metallic_roughness.png).

`../../authoring/composite_eye_repair.sh` performs deterministic resizing, rotation and masked atlas placement using
ImageMagick. The normal patch is neutral tangent space; the packed PBR patch is nonmetal skin with roughness 0.6.
Both remove the false iris imprint under the same local mask. The original decoded pixels outside the mask are
bit-identical in all three final PNG maps. Base color changes 5,020 pixels; normal changes 4,419; packed PBR changes
4,544. No UVs or topology changed.

`../../authoring/eye_repair.py` packs those maps into the existing material regions and restores the actual modeled
eyeball, iris and pupil materials. The aligned surfaces use olive sclera, amber irises and dark pupils; erroneous
skin paint and normal relief no longer cover those separate surfaces.

See the historical [eye and foot comparison](../../review/eyes_feet_correction/index.html) and its preserved
[export/pixel validation](../../review/body_motion_correction/before/textured_validation.json). That pass also
corrected the walking feet, leaving the other six clips and the walk's upper-body channels unchanged at that stage.
The subsequent [whole-body walk correction](../../review/body_motion_correction/index.html) revises the torso,
stride and support timing while retaining this eye repair and all material maps byte-for-byte.

The later [eye visibility correction](../../review/eye_readability/index.html), screenshot 2120, keeps these repaired
maps and refines the actual iris/pupil surfaces and eye material values so the eyes read at full-body scale.
