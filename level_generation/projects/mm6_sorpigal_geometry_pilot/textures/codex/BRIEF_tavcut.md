# Texture brief: tavcut

Make ONE seamless, tileable game texture, square, 1024x1024 pixels, saved as
level_generation/projects/mm6_sorpigal_geometry_pilot/textures/codex/tavcut.png

Use: sills, string courses, plinths and coping on a tawny sandstone tower and tavern, in New Sorpigal, a town of Might and Magic VI (OpenYAMM). It sits directly on the texture in input 1
(tav128wl.png) and must look like part of the same building: the same tawny ochre sandstone as input 1, a little lighter and finer grained (dressed faces), mean brightness about 1.1x that of input 1.

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
