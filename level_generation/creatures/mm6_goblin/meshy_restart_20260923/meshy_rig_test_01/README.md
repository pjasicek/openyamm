# Next operation: Meshy humanoid rig test

Upload **mm6_goblin_10577_meshy_upload.glb** from this folder.
It contains the same 10,577 triangles as the reviewed low mesh, consolidated into one mesh,
one material and one UV set. World-space triangle positions match the reviewed GLB to 1e-6.
The existing two 2K normal images were placed without resampling into one 4K atlas;
this packing does not add sculpted detail or alter geometry. Original authoring assets remain separate.
[Visual check](upload_front.png), [structural check](verification.json).

The first 2K re-bake experiment (`after_atlas.png`, `normal.png`) was superseded. The final
upload uses `normal_4096.png` embedded in the GLB and `meshy_upload.blend`.

## User operation

1. Meshy Model → Upload → choose the GLB above.
2. Enable **Keep Original Texture and UV** in the upload dialog.
3. Open the model → Animate / Rig → **Humanoid**. Keep the existing geometry; no further remesh/reduction.
4. Add idle, walk (in place if available), and one one-handed attack as a deformation test.
5. Download → Animation → All Added → Single File, **GLB**. Return the downloaded path.

The model is suitable for attempting a rig, not yet accepted for production deformation.
Inspect head direction, shoulders, elbows, forearm twist/wrists, grip, hips/knees, pouch and skirt.
Diagnose bone placement and skin weights separately from missing joint geometry; fix the demonstrated
problem locally. Lower LODs follow a working animated LOD0. Quads alone are not a deformation guarantee.

Final color/material generation follows this rig test. The existing local normal maps remain authoritative
for sculpted detail and must not be silently discarded by a texturing operation. Generated Meshy maps
and any changed UVs need inspection before merging back into the authoring asset.

## Official documentation checked 2026-09-24

- [Upload a model for animation](https://help.meshy.ai/en/articles/9992032-is-it-possible-to-upload-my-existing-model-for-animation)
- [Humanoid rigging and optional texturing](https://help.meshy.ai/en/articles/16231707-how-to-create-3d-animation-with-auto-rigging)
- [Upload preservation: one material and one UV map](https://www.meshy.ai/tutorials/texture-3d-models-with-ai)
- [Export all added clips in one file](https://help.meshy.ai/en/articles/11725598-how-do-i-export-multiple-animations-into-a-single-file-for-blender)

No Meshy operation has been submitted or credits spent by the agent.
