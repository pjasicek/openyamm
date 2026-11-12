# Texture brief: rblcut

Make ONE seamless, tileable game texture, square, 1024x1024 pixels, saved as
level_generation/projects/mm6_sorpigal_geometry_pilot/textures/codex/rblcut.png

Use: coping stones on the town walls, cap stones on the gate pillars and wall piers, rims of planters and wells, plinth courses, in New Sorpigal, a town of Might and Magic VI (OpenYAMM). It sits directly on the texture in input 1
(rblbw.png) and must look like part of the same building: the same grey river stone as the stones in input 1: the same mid grey with lighter and darker speckle, mean brightness about 1.1x that of input 1, faces hewn flat but keeping the stone grain.

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
