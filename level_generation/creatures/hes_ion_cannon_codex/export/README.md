# Finished ion-cannon states — 2026-10-23

Accepted in the viewer; corrected POSITION bounds are ready for Crown-builder binding. All are static, unskinned GLBs with four body LODs
(7,916 / 3,939 / 3,148 / 1,955 triangles), shadow meshes, shared texture bytes and seven glow materials.

| File | State |
|---|---|
| hes_great_cannon.glb | Rest: dim violet |
| hes_great_cannon_c1.glb | Core |
| hes_great_cannon_c2.glb | Core + pods |
| hes_great_cannon_c3.glb | Core + pods + first two rings |
| hes_great_cannon_c4.glb | Core + pods + four rings |
| hes_great_cannon_c5.glb | Full charge; white-hot muzzle and three arcs |
| hes_great_cannon_dark.glb | Emission zero |

C5 alone draws the arcs, adding 180 / 108 / 84 / 60 triangles. All files have identical binary/image payloads.
Scale 100; bottom mount origin. **Update the Crown shot origin:** Blender/map-local at scale 100 is
(4.9, -3188.9, 1150.5), before decoration rotation/translation; the old (0, -3800, 1200) does not align.
See [project README](../README.md), [actual-file checks](../review/final_checks.json),
[LOD checks](../review/lod_checks.json) and [state sheet](../review/charging_states.png).
The integrator accepted all seven viewer states; native staging remains with the Crown builder. Meshy is complete (15/40 credits); no jobs remain.

2026-10-23 bounds fix: all 40 POSITION accessors per GLB have measured min/max. Geometry/texture bytes are unchanged;
viewer copies/hashes are refreshed. The stage extent/model-rule checks and complete local artifact checks pass.
