# Goblin images to upload to Meshy

Superseded for Meshy's main/left/back/right slots by [the v2 upload set](../meshy_reference_v2/README.md).
The earlier three-quarter view is not a substitute for the left profile.

Prepared 2026-09-23 using the built-in image-generation tool from our original and restored MM6 goblin.
Four separate 1024×1536 PNG images. No Meshy generation has been submitted.

1. Open **Image to 3D → Multiview** for a single model.
2. Upload these four PNGs; put the front first:
   - `01_front.png`
   - `02_three_quarter.png`
   - `03_profile.png`
   - `04_back.png`
3. Suggested first settings: available **Meshy 7-series / High Detail**, **A-pose**,
   **Image Enhancement off**, **Ultra off**. Check the displayed credit quote before generating.
4. If the interface offers a general instruction field, use `meshy_prompt.txt`.
   Image-to-3D does not require a general geometry prompt. If it only offers a **texture prompt**, use
   `texture_prompt.txt` there instead. Avoid entering body/rigging instructions into a texture-only field.
5. Inspect the generated shape before adding paid processing. After accepting it, texture, prepare topology and rig.

The sword is intentionally absent for clean body reconstruction and rigging. It must be modeled separately and
attached to the right hand in the assembled character. These images prepare the body and costume only.

Use the images individually, not a combined sheet. The ZIP contains only the four upload images and these
instructions/prompts. `prompts/` and `working/` in the source folder are generation provenance, not upload inputs.

Visual review: full silhouettes, empty separated hands, consistent right-side pouch, coherent main costume and
palette. Corrected the invented V-shaped back straps and restored the native rear skull projection; corrected
the profile's extra toe. Small jewelry/rivet details still differ, and the profile shows two visible ear hoops
where the front/oblique views show three. Treat the front as primary for those details. These are AI reconstructions,
not calibrated renders of one existing mesh; the first Meshy result still needs a likeness/deformation review.

Native evidence: `../source_audit/standing_strip.png`.
Restored identity: `../direct_complete/redo_2x/aligned_2x/gobsta0.png` and
`../direct_complete/redo_2x/review/standing_sides_redo_01_detail_contact.png`.
Exact generation/edit prompts are retained in `prompts/`; selected PNG checksums are in `sources.json`.

Settings/background: [pilot research](../../MESHY_CREATURE_PILOT.md),
[Meshy image guide](https://docs.meshy.ai/en/webapp/image-to-3d),
[multi-image API](https://docs.meshy.ai/en/api/multi-image-to-3d).
