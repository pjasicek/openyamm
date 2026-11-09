# Cloth Hat: paint-only view atlas (revision 3, rebuilt feather)

Inputs (attached):
- `guide_atlas.png`: 1536x1024 transparent sheet, three columns by two rows of 512x512 cells. Row 1: FRONT, BACK, LEFT.
  Row 2: RIGHT, TOP, empty. Each cell is a grey orthographic render of the exact 3D model.
- `6hat1.png`: the original game icon, the colour reference.
- `equipment_6hat1.png`: the approved HD master of the same hat, the material and detail reference.

Task: use your built-in image generation tool to paint the guide sheet. Output one 1536x1024 PNG with a transparent
background, the same layout, and each object in exactly the same position, size and outline as its grey guide.
Paint the grey object only; never redraw, enlarge or redesign it.

- Object: a soft, low green felt Robin Hood cap: pointed crown with a curled tip, a turned-up cuff/brim around it,
  and one broad brown feather tucked into the cuff.
- Paint every grey surface that belongs to the cap in mid green felt like the master (about #2f7a3c to #3f8f48,
  slightly darker inside the cuff), with subtle felt texture and a faint seam along the crown.
- Paint the feather (the thin curved blade rising from the cuff) as a natural brown feather: light tan quill along its
  middle, striped brown vane like the master.
- Keep every gap and opening exactly as in the guide and fully transparent.
- Unlit base colour only: no lighting, shading, highlights, ambient occlusion, shadows, ground, glow, outlines or
  text.
- The sixth cell (row 2, column 3) stays empty and transparent.

Save the generated image (copy the file the tool produced) to
`level_generation/props/items_wip_equipment_geometry_finish/codex_tex/equipment_6hat1/paint_raw_v3.png`
and report the path of the original generated file.
