# Shadow's Mask: paint-only view atlas (revision 2)

Inputs (attached):
- `guide_atlas.png`: 1536x1024 transparent sheet, three columns by two rows of 512x512 cells. Row 1: FRONT, BACK, LEFT.
  Row 2: RIGHT, TOP, empty. Each cell is a grey orthographic render of the exact 3D model.
- `7item344.png`: the original game icon, the colour and material reference.

Task: use your built-in image generation tool to paint the guide sheet. Output one 1536x1024 PNG with a transparent
background, the same layout, and each object in exactly the same position, size and outline as its grey guide.
Paint the grey object only; never redraw or redesign it.

- Object: Shadow's Mask, a soft black leather eye mask with a continuous black leather head strap and tied black
  leather ribbons.
- Keep every opening exactly as in the guide: the two round eye holes and every gap between the mask, strap and
  ribbons stay fully transparent. Below and between the eye holes, where the guide shows the strap behind or empty
  background, do not add mask leather.
- Unlit base colour only: near-black leather (about #1c1c1e to #2a2a2c) with subtle grain and fine stitching along
  the mask edge. No lighting, shading, highlights, ambient occlusion, shadows, ground, glow, outlines or text.
- The sixth cell (row 2, column 3) stays empty and transparent.

Save the generated image (copy the file the tool produced) to
`level_generation/props/items_wip_equipment_geometry_finish/codex_tex/equipment_7item344/paint_raw_v2.png`
and report the path of the original generated file.
