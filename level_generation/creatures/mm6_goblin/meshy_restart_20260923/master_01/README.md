# Source master 01 — inspection, 2026-09-23

Source download: `/home/pjasicek/Downloads/Meshy_AI_Ironhide_Goblin_Warlo_0923175641_generate.glb`.
Archived unchanged as `source.glb`; its SHA-256 is in the parent run record. Imported into the isolated Blender
scene `MM6 Goblin Restart - Master 01`, preserving earlier scenes. No paid processing or mesh edits performed.

## Inventory

- 570,800 vertices; 1,142,748 triangle faces; one mesh and one plain material.
- No UV layers, image textures, skeleton or animation clips.
- Imported dimensions: about 1.205 × 0.415 × 1.902 Blender units; unscaled, center-origin source.
- Meshy version and generation controls cannot be recovered from this export; generator metadata is `xpostprocessing`.

## Visual findings

[Review page](review.html) includes rendered evidence and reference comparisons.

The general lean biped, shoulder/forearm/shin armor, belt/skirt, right-side pouch and separated legs are present.
Close views show separated fingers and thumbs. Neither automatic skinning nor a weapon grip has been tested.

Material geometry discrepancies requiring resolution before acceptance:

1. Both small upper-back plates are missing, leaving the upper back bare.
2. The pointed rear skull required by the native profile and both input profiles is absent; the skull is round.
3. Thin teeth/tusks extend too far forward from the mouth, conspicuous in both profiles.
4. Jewelry appears on the left ear as well as the intended right ear.
5. Hands face inward more than in the front input. This is a rest-pose difference to correct/verify before rigging.

Small chest-plate, belt, skirt and rivet details also drifted. Dense polygon count did not ensure reconstruction
fidelity. Clay renders intentionally assess geometry; there are no textures to assess yet.

## Generation inputs — resolved from screenshot 2029.png

After Reuse prompt: Meshy 7.1 Flagship, all four views present, Multi-view ON, Ultra 2K, Pose ON / A-Pose,
Image Enhancement OFF, Texture OFF, Split OFF. This is observed restored UI state, not a server metadata export.
The missing uploads hypothesis is unsupported.

Current next operation: [one revised source candidate](../MESHY_STEP_01B.md).

## Earlier request — verify generation inputs (resolved)

Supply a screenshot of this Meshy job's input images and settings, specifically all four Multi-View slots and
Pose/A-Pose state, plus the model/version and geometry resolution if shown. The missing rear/profile features
suggest checking view use, but the export alone cannot establish whether Multi-View was disabled or the model
ignored supplied views. Do not assert either cause without evidence.

Do not spend on remesh, texture or rig yet. Remesh preserves/reduces existing geometry; it cannot add the missing
reference design. After checking settings: correct an input/configuration problem if found, or evaluate local
skull/teeth/earring/back-plate repair if the correct four-view setup was already used. Keep the usable body and
untouched master. Do not blindly repeat identical paid generation jobs.

Reference: [Meshy Remesh](https://docs.meshy.ai/en/webapp/guides/3d-model/remesh), checked 2026-09-23,
places remesh after shape acceptance and before UV/texturing/rigging. Target count is deferred until shape acceptance.

Inspection scripts: `inspect_master.py` (imports a new isolated scene and renders views), `inspect_details.py`
(renders face/hand close-ups in that scene). `inspection.json` records measured Blender inventory and bounds.
