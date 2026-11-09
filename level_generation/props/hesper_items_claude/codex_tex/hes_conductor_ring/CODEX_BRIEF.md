# Codex brief: paint the five views of the Hesper item model `hes_conductor_ring` (texture source)

Scope: image generation only. Write ONLY into `level_generation/props/hesper_items_claude/codex_tex/hes_conductor_ring/`. Do not edit any other file, do not run builds.

Use your built-in image generation tool. Inputs in this folder: `design_reference.png` (the approved item art: the
design, colour and material authority) and five guides `guide_front.png`, `guide_back.png`, `guide_left.png`,
`guide_right.png`, `guide_top.png`: plain orthographic renders of the EXACT 3D model from that side, transparent
background. Each guide fixes the silhouette, position, scale and every part's edge. Its parts are lightly tinted by
material only to tell them apart: ceramic (tinted light grey), glow (tinted light tone), gold (tinted mid tone). The tints are not colours to copy.

Item: A ring of colonial conductor wire. Its worth is in its enchantment.

## Deliverables (1024 x 1024, transparent background, unresized returns)
- `paint_front.png`, `paint_back.png`, `paint_left.png`, `paint_right.png`, `paint_top.png`: each painted over its
  guide of the same name (the item seen from the front, back, left, right and from directly above).

Each painting keeps its guide's silhouette EXACTLY: the same outline, size and position in the frame, every part where
the guide has it; nothing added outside the silhouette, nothing cropped. Paint the design reference's surfaces onto
each part: white ceramic with fine wear, brushed gold, black-violet resin, glowing blue-white or orange light, glass
and crystal, leather, cloth or paper as the design shows, with its engraved lines, seams, panel joins and small
markings. Faces the design reference does not show (the back, the underside of a part) continue its materials
plausibly.

LIGHTING: a TEXTURE SOURCE (albedo). Even, flat, shadowless light from the viewer; no cast shadows, no ambient
occlusion darkening, no strong specular highlights or reflections (metal as its base colour with only a faint sheen),
no rim light, no background, no floor. Glowing parts are painted as their bright light colour.

Write `generation_runs.json` (view, prompt, inputs with sha256, output, selected, reason). At most one corrective
regeneration per view. If the tool returns another size, keep it unresized and record it.

Checks per image: silhouette identical to the guide; colours and materials match the design reference; flat even light
with no shadows or hot highlights; transparent background; no text or letters.
