# Codex brief: paint the views of Huntmaster Vreth's warglaive 3D model (texture source), part 3

Scope: image generation only. Write ONLY into `level_generation/creatures/hes_harrower_codex/warglaives/vreth/paint/`. Do not edit any other file, do not run builds.

Use your built-in image generation tool. Inputs in this folder: `design_reference.png` (the approved HD design,
three-quarter: design, colour and material authority), `design_front.png` (the same design square on) and one
`guide_<view>.png` per deliverable: a plain grey orthographic render of the EXACT 3D model from that side,
transparent background. The guide fixes the silhouette, position, scale and every shape edge. If a guide shows the
weapon mirrored relative to the references, follow the guide and mirror the design's details onto it.

## Deliverables (1024 x 1024, transparent background, unresized returns)
- `paint_left.png` over `guide_left.png` (one edge, edge-on)
- `paint_right.png` over `guide_right.png` (the other edge, edge-on)

Each painting must keep the guide's silhouette EXACTLY: the same outline, size and position in the frame, every edge,
spur, ring, guard and opening where the guide has them; nothing added outside the silhouette, nothing cropped. Paint
the design's materials onto that shape: bone-white chitin-ceramic (pale, cool ivory) over a dark plum resin core with fine gold filigree lines; gold bands and gold trim at the grip, the guards and the spurs' roots; the grip dark resin wound with cord; the small hanging bone trophy on a gold chain; the ENERGY EDGES along the concave edge of the long blades and of the inner blades: a flat, bright ORANGE-WHITE seam (about RGB 255, 215, 150, white-hot at its centre) in a dark channel, with NO glow or halo outside it.

LIGHTING: this is a TEXTURE SOURCE (albedo). Even, flat, shadowless light from the viewer; no cast shadows, no
ambient-occlusion darkening, no strong specular highlights or reflections (gold as its base colour with only a faint
sheen), no rim light, no background, no floor. The energy seam is painted as flat bright colour, not as light: no bloom.

Write `generation_runs_3.json` (view, prompt, inputs with sha256, output, selected, reason). At most one
corrective regeneration per view. If the tool returns another size, keep it unresized and record it.

Checks per image: silhouette identical to the guide; materials and colours match the design; flat even light with no
shadows, hot highlights or glow halos; transparent background.
