# Codex brief: paint the views of the Great hive spire 3D model (texture source), part 3

Scope: image generation only. Write ONLY into `level_generation/props/hesper_decorations/codex_tex/hes_spire_great/`. Do not edit any other file, do not run builds.

Use your built-in image generation tool. Inputs in this folder: `design_reference.png` (the approved HD design,
three-quarter view: the design, colour and material authority), `concept_crop.png` (the original concept) and one
`guide_<view>.png` per deliverable: a plain grey orthographic render of the EXACT 3D model from that side,
transparent background. The guide fixes the silhouette, position, scale and every shape edge.

## Deliverables (1024 x 1024, transparent background, unresized returns)
- `paint_left.png` over `guide_left.png` (the decoration seen from the left)
- `paint_right.png` over `guide_right.png` (the decoration seen from the right)

Each painting must keep the guide's silhouette EXACTLY: the same outline, size and position in the frame, every edge,
opening and detail where the guide has them; nothing added outside the silhouette, nothing cropped. Paint the surface
materials of the design reference onto that shape: glossy wet black-violet resin and chitin with a faint violet sheen, hot glowing orange slit windows and veins, ivory bone spikes with pale tips.

LIGHTING: this is a TEXTURE SOURCE (albedo). Even, flat, shadowless light from the viewer; no cast shadows, no
ambient-occlusion darkening, no strong specular highlights or reflections, no rim light, no background, no floor.
Glowing parts (orange sacs, seams) are painted at their glowing colour, not as light cast on their surroundings.

Write `generation_runs_3.json` (view, prompt, inputs with sha256, output, selected, reason). At most one
corrective regeneration per view.

Checks per image: silhouette identical to the guide; materials and colours match the design reference; flat even
light; transparent background.
