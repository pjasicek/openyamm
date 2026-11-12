# Texture brief: snowcap

Make ONE seamless, tileable game texture, square, 1024x1024 pixels, saved as
level_generation/projects/mm6_sorpigal_geometry_pilot/textures/codex/snowcap.png

Use: ridge and hip caps and fascia boards on the snow-laden plank roofs of input 1, in New Sorpigal, a town of Might and Magic VI (OpenYAMM). It sits directly on the texture in input 1
(sgstrrf.png) and must look like part of the same building: the same red-brown planks as input 1 with a thin crust of the same snow along the upper edge of each board, a little darker than input 1.

Content:
- Wooden boards running horizontally across the tile: 4 boards over the tile height, butt joints staggered,
  thin dark gaps between boards, visible grain and a few nail heads.
- No moss, no colour cast beyond input 1's own, no carving, no decoration.

Rules:
- Seamless on both axes: the left edge continues into the right edge and the top into the bottom with no visible
  seam; courses or boards must line up across the top/bottom edge.
- Straight-on orthographic view, even flat lighting, no cast shadows, no perspective, no vignette, no text.
- Painterly-realistic texture matching the 1990s-remastered style of input 1; detail readable at 512x512.

Generate it with your built-in image generation tool, check the seams yourself (offset the image by half in both
axes with a quick script) and compare its mean colour with input 1's; regenerate once if a seam, a perspective or a
clear colour mismatch is visible. Save only the PNG.
