# Local repair source for remesh

Selected master 01 as the base after comparing master 02. Master 02 improves the tooth projection but still lacks
native rear-skull shape, invents one V-shaped back plate, duplicates jewelry and has lumpier body surfaces. Its
1,183,918 triangles do not establish better reference fidelity. Actual retry settings were not provided; no causal
claim about Pose/Standard can be made from geometry alone.

## Delivered source

`mm6_goblin_repaired_master.glb`: first body with localized skull and tooth changes plus two upper-back plates.
15 mesh objects and 1,144,016 triangles, unrigged and untextured. Original downloads and archived candidates remain
unchanged. Source and export renders are in `review/`; the parent comparison page is `../candidate_review.html`.

- Added a smoothly blended backward taper to the skull, preserving the existing face and right ear.
- Reduced the excessive forward projection of the teeth while retaining the existing mouth structure.
- Added two separate riveted plates following the measured upper-back surface.
- Original body topology stays intact, with zero boundary edges in the source body.

**Left-ear jewelry remains.** A local trim/replacement experiment damaged the fused ear surface and was rejected.
The delivered file restores the entire original left ear. Remove/refine that decoration on the editable remesh
before texture/rig acceptance. No damaged experimental ear geometry is included in the exported model.

This is a source for the first topology trial, not a final game asset. Meshy's body proportions, hands, armor detail
and face remain interpreted. There are no animation or runtime performance claims. The grip, rigid armor weights,
wrist/twist checks and native attack still belong to later stages.

## Reproduce

Execute `repair_master.py` inside Blender with access to `../master_01/source.glb`. It creates a new scene and
preserves the previous repair as a draft when repeated. `render_review.py` schedules diagnostic views; wait for
completion before `render_details.py`. `export_master.py` exports only meshes in the active repaired scene;
`verify_export.py` reimports the actual file, checks counts and renders the delivered back and quarter views.

See [the next Meshy operation](../MESHY_STEP_02.md).
