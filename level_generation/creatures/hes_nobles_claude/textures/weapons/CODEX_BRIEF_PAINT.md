# Codex brief: paint the Nobles' weapon guides (texture projection views)

Each weapon below has an exact orthographic render of its 3D mesh, seen from the front and from the back
(`review/weapons/<name>_guide_front.png`, `_guide_back.png`: light grey clay with cavity shading on a flat dark grey
background, 1024 x 1024), and its approved HD master (`references_hd/weapons/<name>/00_three_quarter.png`). The painted
views are projected straight onto the mesh, so registration is everything.

For every guide, produce one painted image with your built-in image generation tool, using the guide as the edit
target (image-to-image) and the master as the material reference:
- **Keep the guide's silhouette, framing and every shape exactly**: same outline, same holes, same position and size in
  the canvas, the same 1:1 square canvas. Do not move, rotate, crop, extend, simplify or add any part. Paint only inside
  the clay surface; keep the background the same flat dark grey.
- Paint the clay in the master's materials as seen face-on: gilded chitin and ivory bone-ceramic plates, black-violet
  resin in the recesses and grip wraps, fine gold edges, and the master's orange energy (glowing edges, cells, coil) as
  solid saturated orange. Follow the clay's own forms: a raised plate is one material, a groove is resin.
- Even, flat studio light from the viewer; no cast shadows, no specular hot spots, no glow halo spilling onto the
  background, no text.
- The back view is the same object seen from behind (mirrored): paint it consistently with the front (the same parts
  carry the same materials).

| Name | Master | Notes |
|---|---|---|
| `noble_fang` | `references_hd/weapons/noble_fang/00_three_quarter.png` | blade ivory-gold, its concave edge an orange glowing seam; hilt resin and bone rings |
| `noble_sidearm` | `references_hd/weapons/noble_sidearm/00_three_quarter.png` | barrel shroud ivory with gold ribs, orange cell and muzzle; grip bone-ivory, trigger guard gold |
| `ssekh_fang` | `references_hd/weapons/ssekh_fang/00_three_quarter.png` | crescent ivory-gold, its inner edge bright orange-white; spine resin ribs; grip bone rings |
| `phase_cleaver` | `references_hd/weapons/phase_cleaver/00_three_quarter.png` | blades ivory-gold with resin cut-outs, orange cutting edges and two orange nodes; haft dark resin with gold and bone bands |

Save the eight images as `textures/weapons/<name>_paint_front.png` and `<name>_paint_back.png` (this directory) and record
each in `textures/weapons/generation_runs.json` (asset, view, prompt, inputs, source, output, sha256, size, review notes:
note any silhouette drift honestly). At most one corrective regeneration per image. Then stop.
