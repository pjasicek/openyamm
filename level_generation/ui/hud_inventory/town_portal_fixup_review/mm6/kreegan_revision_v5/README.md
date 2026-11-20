# Darker Kreegan stencil

The user approved this darker drawing and requested deployment, then requested a
[muted-color preview](../palette_study_v6/README.md) before deploying. This revision remains the fixed,
unchanged-color source for that study. Acceptance publication and deployment are held pending the palette choice.

The user requested making the Kreegan more black, like the Titan and dragon. This revision darkens its
existing drawing with near-black brown ink and deeper fills. The exact side silhouette, every alpha pixel,
60 × 100 master-pixel size, and position (182, 342) are unchanged.

[Review the map](http://127.0.0.1:8900/level_generation/ui/hud_inventory/town_portal_fixup_review/),
switch to **Lighter Kreegan** to compare, or open [the saved PNG](tpenroth.png).

The built-in imagegen tool produced a darker color reference using the existing stencil, Titan, and dragon.
[prompt.txt](prompt.txt), `tool_args.json`, `inputs/`, and `raw.png` retain that step. Only its tones are transferred:
`grade.json` maps the 10th/90th RGB percentiles of opaque pixels to the original stencil with a uniform affine
color transform. ImageMagick applies the grade to RGB only; the original drawing and alpha remain exact.
The graded layer is composited over the retained crisp terrain and exported once to 1280 × 960.

`prepare.py` reproduces the grade and composition. [manifest.json](manifest.json) and
[validation.json](validation.json) record hashes and verify that changes are confined to the Kreegan.
The terrain, Titan, dragon, destination crops, and all six hover exports are unchanged. All seven accepted
runtime assets still match the earlier gargoyle acceptance; this approved darker Kreegan has not been published.
The earlier Kreegan revision and its original generated layer remain intact under `../kreegan_revision_v4/`.
