# MM6 Meshy demon: shoulder and foot rig correction

The supplied Meshy rig stretched its shoulder spikes when the arms moved and curled/rolled its broad clawed feet
with a humanoid walk preset. The corrected package keeps the shoulder spikes attached and gives planted feet a
flatter orientation, with rigid talons and clearance during the lifted part of the stride.

Use [mm6_demon_rig_corrected.glb](mm6_demon_rig_corrected.glb) for the corrected model and animations, or
[mm6_demon_rig_corrected.blend](mm6_demon_rig_corrected.blend) for the standalone Blender review project.
The Blender project opens on the Walking action at 48 fps; choose Running to inspect the other action.
The camera, floor and bone display helper belong to the Blender review only and are excluded from the GLB.

[Walking preview](walking_review.gif) · [Running preview](running_review.gif) · [Foot close view](after_feet.png)
· [Shoulder close view](after_shoulders.png) · [Acceptance record](acceptance.json).

## Changes

- Reparented `Bone_041` and `Bone_036` from the respective forearms to their shoulders, retaining bind-space
  positions. Their source animation channels are static, so the spikes now follow the shoulders correctly.
- Transferred ToeBase/Toe_End skin weights into the corresponding Foot group. The original toe bones remain,
  but their preset curl no longer deforms the talons.
- Removed the preset's sideways foot roll and blended the foot pitch toward a flat planted pose. Swing feet retain
  pitch. Adjusted the fixed-length leg chains for sole contact, preserving the source ankle XY paths and hip XY.
  Root height lowers by at most 0.07030 units in Walking and 0.05469 in Running, on this 1.7-unit-tall model.
- Baked both clips at 48 fps. Names, durations and loop joins are retained; unrelated local bone motion is sampled
  from the source clips. Walking lasts 25/24 seconds and Running lasts 16/24 seconds.
- Preserved all 7,899 mesh vertices, 15,686 triangle indices and 79 bone names. Retained up to seven skin influences.

## Review

All 43 native key poses were rendered and inspected from front and side, with separate shoulder and foot close
views. The complete pose sheets are `walking_front_poses.jpg`, `walking_side_poses.jpg`, `running_front_poses.jpg`
and `running_side_poses.jpg`. GIF timing is rounded to centiseconds; the GLB preserves the exact clip durations.

Both clips were also evaluated at quarter-native-frame intervals: 101 Walking samples and 65 Running samples.
The talons remain rigid to within floating-point error. The smallest sampled foot-surface height is -0.000878
units at a soft seam, within the 0.002-unit review tolerance; the rigid foot contact keys use a 0.006-unit margin.
Soft shoulder attachment transitions still deform, while the torn/stretched spike silhouettes are gone.

An actual GLB reimport preserved triangle indices and matched the reviewed deformed mesh within 0.00000203 units.
Loop endpoint differences remain below 0.0000023 units. The exported file contains only the corrected mesh and rig,
with exactly Walking and Running. `export_file_audit.json`, `export_roundtrip_audit.json` and
`deformation_summary.json` contain the measurements.

Acceptance covers these requested shoulder and foot rig corrections. The supplied “All Animations” file contains
only Walking and Running; there are no idle or attack clips. It has no UV map, material or texture. No texturing or
gameplay installation was performed.

## Source and reproducibility

Source: `/home/pjasicek/Downloads/Meshy_AI_mm6_demon_cleaned_All_Animations.glb`.
Source SHA-256: `f7631fca2e11a01740035028b507584a6f1c4f2fd7251529918495b8bdaa9996`, verified unchanged.

`rig_before_weights.blend` preserves the untouched import. `fix_rig.py` corrects hierarchy/weights;
`correct_foot_placement.py` performs the placement correction and bake; `review_corrected.py` measures and renders
comparisons; `render_cycles_export.py` renders the cycles and exports only the selected rig/mesh;
`check_export_file.py` checks the actual GLB; `verify_export.py` reimports it and saves a standalone review project;
`finalize_review.py` records acceptance. After these library saves, run `normalize_blend.py` in a separate background
Blender process to produce a normal startup project and update the accepted file hash. `validate_startup.py` checks
opening that file directly. `make_review.py` assembles the render-only previews.

Earlier intermediate checkpoints are retained for reproducibility and are superseded by the two corrected files
linked above. Source assets, other Blender scenes, shared tools, global ledgers and runtime assets were preserved.
