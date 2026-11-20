# MM6 demon — Meshy geometry cleanup

Completed 2026-10-04 using the connected Blender MCP add-on, Blender 5.2.2 LTS.

Open [mm6_demon_cleaned.blend](mm6_demon_cleaned.blend) for the editable model, or use
[mm6_demon_cleaned.glb](mm6_demon_cleaned.glb) for a portable mesh. The active Blender scene is
`MM6_Demon_Cleanup`; `Demon_Cleaned` is the result. The original review and unrelated default scene are preserved.
The GLB contains exactly one mesh object in one scene.

![Reviewed cleaned model](preview.png)

## Repairs

The source misplaced 20 independent surface-cap poles at one hip coordinate. Three of those poles belonged to
isolated artifact triangles; those triangles were removed. The other 17 poles and 10 displaced interpolation
helpers were solved against their surrounding local surface vertices. This removed the hand/hip/foot bridges,
including the thin foot spike marked by the user.

Exact duplicate seam coordinates were joined after the misplaced poles were corrected. Open shell backs were
closed with short local triangles; the chest ornament's two rear rims were bridged as an annulus so its opening
remains. Five disconnected face fans were separated at coincident corners. Normals were made consistently outward.
Two small patches at the affected toe base and inner shin were locally faired; the rest of the coordinates remained
fixed during that step. No whole-body remesh, subdivision or smoothing was applied.

The supplied model's A pose, proportions, fingers, claws, shoulder/arm spikes, harness, teeth, eyes and tail were
retained. The original Downloads GLB and the repository's runtime assets were not modified.

## Checks

| Check | Final result |
| --- | --- |
| Vertices | 7,899 |
| Triangles | 15,686; source 15,487 |
| Open boundary edges | 0 |
| Nonmanifold edges / vertices | 0 / 0 |
| Inconsistent winding edges | 0 |
| Loose edges / vertices | 0 / 0 |
| Degenerate faces | 0 |
| Closed surface components | 32, including separate teeth, eyes and chest ornament |
| GLB reimport | One mesh; same counts; coordinate error 0 |
| Source SHA-256 | `fe573922ad435c24c605e1d7f3edad8788606f15204e0447f4a47463b6f70d90`, unchanged |

Six full views and the head/chest, harness back, hands, knees and both sides of the repaired foot were visually
reviewed. Unshadowed lighting was used to distinguish real surface defects from cast shadows.
The reimported GLB and the final MCP viewport were inspected as well. See `acceptance.json`,
`blender_cleanup_audit.json` and `export_verification.json` for recorded results and output hashes.

This deliverable is a cleaned triangle mesh. UV unwrapping, reference textures, rigging, skin weights and animation
deformation checks remain future work. The source was also untextured and unrigged.

## Reproduction

`repair_geometry.py` → `close_seams.py` → `fair_local_artifacts.py` generates the staged geometry using Python/NumPy.
`inspect_repair.py` initializes a separate Blender inspection scene and camera; `export_cleaned.py` applies the final
geometry, checks topology, renders the reviews and exports the selected active scene only.
`verify_export.py` checks an actual reimport; `save_reviewed.py` removes the disposable verification scene and saves
the accepted editable copy. These scripts are asset-specific records and do not edit shared tools or source files.
