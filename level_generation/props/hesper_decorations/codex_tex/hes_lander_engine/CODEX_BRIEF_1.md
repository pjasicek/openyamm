# Codex brief: paint the views of the The lander's torn-off engine nacelle 3D model (texture source), part 1

Scope: image generation only. Write ONLY into `level_generation/props/hesper_decorations/codex_tex/hes_lander_engine/`. Do not edit any other file, do not run builds.

Use your built-in image generation tool. Inputs in this folder: `design_reference.png` (the approved HD design,
three-quarter view: the design, colour and material authority), one
`guide_<view>.png` per deliverable: a plain grey orthographic render of the EXACT 3D model from that side,
transparent background. The guide fixes the silhouette, position, scale and every shape edge.

## Deliverables (1024 x 1024, transparent background, unresized returns)
- `paint_front.png` over `guide_front.png` (the decoration seen from the front)
- `paint_top.png` over `guide_top.png` (the decoration seen from the top)

Each painting must keep the guide's silhouette EXACTLY: the same outline, size and position in the frame, every edge,
opening and detail where the guide has them; nothing added outside the silhouette, nothing cropped. Paint the surface
materials of the design reference onto that shape: chipped white ceramic plates with broad gold rings, a dark steel exhaust nozzle with a gold turbine ring, black soot and scorch, black cables.

LIGHTING: this is a TEXTURE SOURCE (albedo). Even, flat, shadowless light from the viewer; no cast shadows, no
ambient-occlusion darkening, no strong specular highlights or reflections, no rim light, no background, no floor.
Glowing parts (orange sacs, seams) are painted at their glowing colour, not as light cast on their surroundings.

Write `generation_runs_1.json` (view, prompt, inputs with sha256, output, selected, reason). At most one
corrective regeneration per view.

Checks per image: silhouette identical to the guide; materials and colours match the design reference; flat even
light; transparent background.
