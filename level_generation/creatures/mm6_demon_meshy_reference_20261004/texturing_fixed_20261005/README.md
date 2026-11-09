# MM6 demon — local material corrections

Open [index.html](index.html) for the native face reference, matched Meshy/corrected
material comparisons and representative poses from all nine exported clips.

## Files

- `mm6_demon_textured.blend`: editable animated master with packed textures. Active scene:
  `MM6_Demon_Textured_Animations`, Standing at frame zero, 48 fps.
- `mm6_demon_textured.glb`: animated portable model, nine clips, 85 joints, 16474 body triangles.
- `textures/`: the unchanged Meshy maps and the locally baked white-claw colour map.
- `material_regions.json`: reviewed polygon mask and input/texture hashes.
- `validation.json`: preservation, export and representative-pose checks.

The source is `Meshy_AI_mm6_demon_meshy_uploa_1005094724_texture.glb`. Its geometry
and UV coordinates match our static UV upload. The animated source remains
`../texturing_upload_20261005/mm6_demon_uv_master.blend`.

The body and harness use the original generated material. The two iris surfaces use
salmon-red sRGB (0.86, 0.38, 0.36); the pupil caps use near-black (0.015, 0.012, 0.012).
Eyes have no generated bump or metallic map. Hand and foot talons, including the rear
foot spurs, use a neutral white colour map, zero metallic and the existing roughness
and tangent-normal detail. The colour bake brightens and desaturates the ivory pigment
while retaining dark skin at the roots. The mask uses hand-tip/lower-foot anatomy and ivory
pigment, with one adjacent polygon ring for dark baked patches. It does not recolour
the ivory shoulder spikes or teeth.

The Blender master keeps four body material slots: body, iris, pupil and white talons.
No topology, UV, normal, weight, bind or animation changes were made. The extra talon
material adds one material primitive; triangle count is unchanged. The original UV
master, Meshy download and previous revisions remain unchanged.

The actual GLB was reimported, its material colours and maps checked, and representative
deformed vertices compared across all nine clips, including fractional Running timing.
Comparison renders use the actual GLB with matching pose, camera and lighting. These
checks do not constitute final artistic acceptance or engine installation.

## Reproduction

Run `python3 prepare_return.py` from this directory to extract maps and the mask.
Through Blender MCP, import `author_materials.py` and call `apply()` in a session without
the new textured scene. This appends the UV master from the preserved source checkpoint.
Then, from the repository root:

```sh
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/texturing_fixed_20261005/export_and_review.py
python3 level_generation/creatures/mm6_demon_meshy_reference_20261004/texturing_fixed_20261005/build_review.py
```

To inspect an animation in Blender, mute all rig/object/shape-key NLA tracks, assign
the matching strip Action and its Action Slot, then set frames according to the clip.
Alternatively, use the existing `SELECT_ANIMATION.py` text in the project to enable
one clip's NLA tracks. Nine clips: Standing, Walk_Native, Attack, Hit, Fidget, Death,
Ash_Remains, Walking and Running.

The 3D renderer material pass subsequently set the body metallic factor to zero: skin, leather, and bone are
dielectrics, including pixels that Meshy marked metallic. Iris and pupil roughness are now 0.22 and 0.18.
`tune_pbr_materials.py` updates these factors in the existing GLB and both editable Blender masters. Geometry,
animation bytes, base colour, and normal images are preserved. The original files and tuning hashes are retained
under `output/creature_3d_rendering_review/material_tuning/`; earlier gallery images predate this response tuning.

The 2026-10-06 performance correction adds explicit object visibility for the standalone death plume:
zero scale outside Death and unit scale during Death. `effects.py` and `normalize_export.py` reproduce that
visibility; the selected editable master and portable GLB retain the original plume motion and materials.
`fix_plume_visibility.py` records the applied correction without rebuilding other animation or geometry.
The game export omits this mesh with `tools/prepare_actor_glb.py --omit-mesh-node Demon_Death_Plume`;
the model binding instead selects `death_effect: disintegration`, a bounded shared particle burst.
Validation and native performance evidence are in
[`output/performance/demon_cpu_fix_20261006/REPORT.md`](../../../../output/performance/demon_cpu_fix_20261006/REPORT.md).
