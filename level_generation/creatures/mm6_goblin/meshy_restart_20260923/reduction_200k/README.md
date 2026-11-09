> Scope update: the user now targets runtime 3D. This file is retained as an intermediate;
> see `../RUNTIME_3D_PLAN.md`. It is not the selected runtime LOD.

# Higher-detail billboard geometry candidate

`mm6_goblin_billboard_200k.glb` was derived locally from the unchanged repaired master with Blender
collapse decimation. Body: 198,000 triangles; separate back plates and rivets: 1,268;
total **199,268 triangles**, below the 300K limit reported by the user in Meshy.
No Meshy generation or remesh credits were used by the agent.

`build.py` reproduces the export. `verify_export.py` reimports the exported GLB into an isolated scene,
measures it, and renders eight neutral views. Reviewed front and rear-quarter views preserve face,
armor spikes, fingers and both back plates much better than Meshy remesh 01. Comparison sheets are
in the parent folder. This is a billboard authoring candidate, not an accepted runtime LOD or a validated rig.

Still outstanding: left-ear jewelry cleanup, usable body/plate UVs, textures, rig and grip/joint deformation
review. The rivets retain primitive UVs; body and plates have none. Automatic reduction does not create
animation edge loops. Keep the dense source for further edits and high-to-low detail baking.
