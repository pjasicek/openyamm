# Amber Droplet: paint-only view atlas

Scope: image generation only. Write ONLY into `level_generation/props/items_wip_maw/codex_tex/maw_gem04/`. Do not edit any other file, do not run builds.

Inputs (attached):
- `guide_atlas.png`: 1536x1024 transparent sheet, three columns by two rows of 512x512 cells. Row 1: FRONT, BACK,
  LEFT. Row 2: RIGHT, TOP, empty. Each cell is a grey orthographic render of the exact 3D model.

Task: use your built-in image generation tool to paint the guide sheet. Output ONE 1536x1024 PNG with a transparent
background, the same layout, each object in exactly the same position, size and outline as its grey guide. Paint the
grey objects only; never redraw, enlarge, move or redesign them.

- Paint the unlit base colour of the item on each view: polished translucent honey-orange amber, deeper orange at the rim, a small brown leaf inclusion.
- `design_reference.png`: the approved HD master of the item (three-quarter view), the material and detail reference.
- `icon_x8.png`: the original game icon (magenta is background), the colour reference.

Object: a polished teardrop-shaped amber cabochon: smooth domed top, pointed tip at one end, flat underside; translucent honey-orange with a small dark leaf inclusion inside. It lies on the ground.

- Facets, engravings, scrollwork and inner swirls follow the design reference, scaled to each view.
- Keep every gap and opening exactly as in the guide and fully transparent.
- Unlit base colour only: no lighting, no cast shadows, no ambient occlusion, no hot highlights or reflections, no
  glow halo, sparkles or aura outside the silhouette, no ground, no outlines, no text.
- The empty cell (column 3 of row 2) stays empty and transparent.

Save the generated image (copy the file the tool produced) to `level_generation/props/items_wip_maw/codex_tex/maw_gem04/paint_raw_v1.png` and write
`generation_paint.json` (prompt, inputs with sha256, original output path, output, size). At most one corrective
regeneration, only if the silhouettes or layout are clearly wrong.
