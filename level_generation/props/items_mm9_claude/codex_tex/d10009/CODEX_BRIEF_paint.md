# Decorative prop d10009: paint + material mask view atlas

Scope: image generation only. Write ONLY into `level_generation/props/items_mm9_claude/codex_tex/d10009/`. Do not edit any other file, do not run builds.

Inputs (attached):
- `paint_mask_guide.png`: 1536x2048 transparent sheet, three columns by FOUR rows of 512x512 cells. Rows 1-2 and rows
  3-4 hold the same five grey orthographic renders of the exact 3D model: FRONT, BACK, LEFT / RIGHT, TOP, empty.

Task: use your built-in image generation tool to paint the guide sheet. Output ONE PNG with a transparent background
and a 3:4 canvas (1536x2048 or the tool's nearest 3:4 size), the same layout, each object in exactly the same position,
size and outline as its grey guide. Paint the grey objects only; never redraw, enlarge, move or redesign them.

- Rows 1-2 (PAINT): the unlit base colour of the item on each view: Faithfully reconstruct the exact MM9 Imperial flat metal piece from the isolated and mechanically rotated PCX references as an MM6-MM8-style inventory sprite. Repaint the same object; do not redesign it. Preserve its broad pale-steel flat metal piece with gentle asymmetry and swept cutting part, simple thin yellow-gold guard angled across the hilt, very short dark grip, and compact dark-and-gold pommel. Render one complete vertical flat metal piece in restrained late-1990s pre-rendered realism with genuine transparent alpha. No ornate symmetric guard, flat metal piece fuller, jewel pommel, excessive gold, text, glow, shadow, frame, scen CORRECTION (overrides the notes above, which wrongly asked for a very short grip and an angled guard): the thin gold crossguard is PERFECTLY HORIZONTAL, at right angles to the vertical flat metal piece, and symmetric left/right. Below it a dark wrapped grip and the dark-and-gold pommel; from the bottom of the guard to the end of the pommel is about 22-25% of the total length. The paperdoll hand closes over the grip, so the grip must be long enough for a fist plus a visible pommel, like MM6-MM8 flat metal piece (look at the style reference: their hilt below the guard is about a quarter of the length)..
- Rows 3-4 (MATERIAL MASK): the same five silhouettes filled with FLAT pure colours only, no shading, no texture, no
  outlines, no antialiased colour blends inside:
  - pure red #FF0000: every metal part (steel, iron, chain mail, gold, silver, bronze, copper, brass)
  - pure green #00FF00: every leather part (straps, padding, hide, suede) and fur
  - pure blue #0000FF: every cloth part (tabards, quilting, linings, cords, ribbons) and hair
  - pure yellow #FFFF00: every matte non-metal solid (wood, bone, horn, stone, parchment, paper, wax)
  - pure black #000000: every gemstone, crystal, glass, pearl, enamel or liquid seen through glass
  Every pixel of each silhouette gets exactly one of these colours; nothing outside the silhouettes.
- `design_reference.png`: the approved HD painting or master of the item, the material and detail reference.
- `icon_x8.png`: the original game icon (magenta is background), the colour reference.

Object: A harmless static decorative prop for a cosy fantasy game, texture sheet only. Faithfully reconstruct the exact MM9 Imperial flat metal piece from the isolated and mechanically rotated PCX references as an MM6-MM8-style inventory sprite. Repaint the same object; do not redesign it. Preserve its broad pale-steel flat metal piece with gentle asymmetry and swept cutting part, simple thin yellow-gold guard angled across the hilt, very short dark grip, and compact dark-and-gold pommel. Render one complete vertical flat metal piece in restrained late-1990s pre-rendered realism with genuine transparent alpha. No ornate symmetric guard, flat metal piece fuller, jewel pommel, excessive gold, text, glow, shadow, frame, scen CORRECTION (overrides the notes above, which wrongly asked for a very short grip and an angled guard): the thin gold crossguard is PERFECTLY HORIZONTAL, at right angles to the vertical flat metal piece, and symmetric left/right. Below it a dark wrapped grip and the dark-and-gold pommel; from the bottom of the guard to the end of the pommel is about 22-25% of the total length. The paperdoll hand closes over the grip, so the grip must be long enough for a fist plus a visible pommel, like MM6-MM8 flat metal piece (look at the style reference: their hilt below the guard is about a quarter of the length).

- Facets, engravings, scrollwork and inner swirls follow the design reference, scaled to each view.
- Keep every gap and opening exactly as in the guide and fully transparent.
- Unlit base colour only: no lighting, no cast shadows, no ambient occlusion, no hot highlights or reflections, no
  glow halo, sparkles or aura outside the silhouette, no ground, no outlines, no text.
- The empty cells (column 3 of row 2 and row 4) stay empty and transparent.

Save the generated image (copy the file the tool produced) to `level_generation/props/items_mm9_claude/codex_tex/d10009/paint_mask_raw_v1.png` and write
`generation_paint.json` (prompt, inputs with sha256, original output path, output, size). At most one corrective
regeneration, only if the silhouettes or layout are clearly wrong.
