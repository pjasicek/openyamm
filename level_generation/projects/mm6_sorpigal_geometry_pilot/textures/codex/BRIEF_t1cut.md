# Texture brief: t1cut

Make ONE seamless, tileable game texture, square, 1024x1024 pixels, saved as
level_generation/projects/mm6_sorpigal_geometry_pilot/textures/codex/t1cut.png

Use: sills, plinths and coping on the pink-veined marble temple and town hall, in New Sorpigal, a town of Might and Magic VI (OpenYAMM). It sits directly on the texture in input 1
(t1wl5lea.png) and must look like part of the same building: the same pale pink marble with red-brown veins as the blocks in input 1, joints the dark grey of input 1, mean brightness like input 1.

Content:
- Dressed ashlar: rectangular cut stone blocks in running bond, 4 courses over the tile height, blocks 1.5 to 2.5
  times as long as they are high, thin mortar joints (2-4 % of the tile), slightly chamfered block edges.
- No moss, no colour cast beyond input 1's own, no carving, no decoration.

Rules:
- Seamless on both axes: the left edge continues into the right edge and the top into the bottom with no visible
  seam; courses or boards must line up across the top/bottom edge.
- Straight-on orthographic view, even flat lighting, no cast shadows, no perspective, no vignette, no text.
- Painterly-realistic texture matching the 1990s-remastered style of input 1; detail readable at 512x512.

Generate it with your built-in image generation tool, check the seams yourself (offset the image by half in both
axes with a quick script) and compare its mean colour with input 1's; regenerate once if a seam, a perspective or a
clear colour mismatch is visible. Save only the PNG.
