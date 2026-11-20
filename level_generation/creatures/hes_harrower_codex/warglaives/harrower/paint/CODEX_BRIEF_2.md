# Codex brief: paint the views of the standard Harrower warglaive 3D model (texture source), part 2

Scope: image generation only. Write ONLY into `level_generation/creatures/hes_harrower_codex/warglaives/harrower/paint/`. Do not edit any other file, do not run builds.

Use your built-in image generation tool. Inputs in this folder: `design_reference.png` (the approved HD design,
three-quarter: design, colour and material authority), `design_front.png` (the same design square on) and one
`guide_<view>.png` per deliverable: a plain grey orthographic render of the EXACT 3D model from that side,
transparent background. The guide fixes the silhouette, position, scale and every shape edge. If a guide shows the
weapon mirrored relative to the references, follow the guide and mirror the design's details onto it.

## Deliverables (1024 x 1024, transparent background, unresized returns)
- `paint_back.png` over `guide_back.png` (the back face, square on)

Each painting must keep the guide's silhouette EXACTLY: the same outline, size and position in the frame, every edge,
spur, ring, guard and opening where the guide has them; nothing added outside the silhouette, nothing cropped. Paint
the design's materials onto that shape: ivory chitin-ceramic plates (warm off-white, fine chitin cells and veins) over a black-violet resin core (twisted, scaled, dark); the grip black resin wound with ivory bone rings; the crescent guards ivory with a fine gold band; the ENERGY EDGE along the concave (inner, right-hand in the front guide) edge of both blades: a flat, bright, saturated ORANGE seam (about RGB 255, 140, 40) inside a dark resin channel, with NO glow or halo outside it.

LIGHTING: this is a TEXTURE SOURCE (albedo). Even, flat, shadowless light from the viewer; no cast shadows, no
ambient-occlusion darkening, no strong specular highlights or reflections (gold as its base colour with only a faint
sheen), no rim light, no background, no floor. The energy seam is painted as flat bright colour, not as light: no bloom.

Write `generation_runs_2.json` (view, prompt, inputs with sha256, output, selected, reason). At most one
corrective regeneration per view. If the tool returns another size, keep it unresized and record it.

Checks per image: silhouette identical to the guide; materials and colours match the design; flat even light with no
shadows, hot highlights or glow halos; transparent background.
