# Goblin normal-map feasibility proof

The existing local 30K candidate was copied into an isolated scene. Geometry was not changed.
Its 28,732-triangle main body received temporary smart-projected UVs and a 2K tangent-space normal bake
from the 1,142,748-triangle repaired dense body. Twelve separate back rivets are hidden; two back plates remain.
Visible geometry is 28,800 triangles, no sword. This is a local diagnostic, not a final runtime export.

[Same geometry before/after bake](comparison.jpg). Torso, armor and skirt relief returns without extra geometry.
Black marks and projection artifacts remain around some armor/chest details; cage/ray and UV work is needed.
No colors, rig or animation were added. The source 30K GLB and dense source remain unchanged.
`bake_proof.blend` contains this isolated scene and packed map. `make_probe.py` records the experiment.
Do not mistake this 30K-based proof for proof that a specific 8K model has already passed visual/deformation review.
