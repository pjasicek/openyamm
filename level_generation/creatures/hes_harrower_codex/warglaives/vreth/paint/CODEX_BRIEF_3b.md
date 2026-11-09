# Codex brief: texture-source painting of a decorative prop, right edge view (retry)

Scope: image generation only. Write ONLY into `level_generation/creatures/hes_harrower_codex/warglaives/vreth/paint/`.
Do not edit any other file, do not run builds.

This is a texture source for a fantasy game's decorative prop: a long, slender, curved ornamental bow-shaped object
of carved bone-white ceramic with gold trim and a dark plum lacquered core. Inputs in this folder:
`design_reference.png` and `design_front.png` (the approved design: colour and material authority),
`paint_left.png` (the already painted opposite narrow side, for consistency) and `guide_right.png` (a plain grey
orthographic render of the EXACT 3D model seen from its right narrow side, transparent background).

## Deliverable (1024 x 1024 or the tool's size, transparent background, unresized return)

- `paint_right.png` over `guide_right.png`.

Keep the guide's silhouette EXACTLY (outline, size, position; nothing added, nothing cropped). Paint the materials onto
it: bone-white ceramic plates, gold bands and trim, dark plum lacquer between them; along this side's narrow face
runs a flat, bright warm orange-white inlay stripe (painted colour, not light). Even, flat, shadowless light, no
highlights, no background. Append the run to `generation_runs_3.json` (view, prompt, inputs with sha256, output,
selected, reason). At most one corrective regeneration.
