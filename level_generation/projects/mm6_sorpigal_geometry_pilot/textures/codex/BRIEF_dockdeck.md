# Texture brief: dockdeck

Make ONE seamless, tileable game texture, square, 1024x1024 pixels, saved as
level_generation/projects/mm6_sorpigal_geometry_pilot/textures/codex/dockdeck.png

Use: the deck of a wooden pier, with the planks laid across the pier, and the thick edge boards and piles of the same pier, in New Sorpigal, a town of Might and Magic VI (OpenYAMM). It sits directly on the texture in input 1
(cedvwal1.png) and must look like part of the same building: clean golden-brown seasoned timber like input 1 but less orange and with fewer knots, fine grain, slight wear, mean brightness like input 1.

Content:
- Deck planks running VERTICALLY in the image (top to bottom), 4 broad planks across the tile width, each
  plank one piece over the tile height or with one staggered butt joint, thin dark gaps between planks, a pair of
  nail heads where each plank crosses a joist (2 rows of nails over the tile height, at 25 % and 75 %).
- No moss, no colour cast beyond input 1's own, no carving, no decoration.

Rules:
- Seamless on both axes: the left edge continues into the right edge and the top into the bottom with no visible
  seam; courses or boards must line up across the top/bottom edge.
- Straight-on orthographic view, even flat lighting, no cast shadows, no perspective, no vignette, no text.
- Painterly-realistic texture matching the 1990s-remastered style of input 1; detail readable at 512x512.

Generate it with your built-in image generation tool, check the seams yourself (offset the image by half in both
axes with a quick script) and compare its mean colour with input 1's; regenerate once if a seam, a perspective or a
clear colour mismatch is visible. Save only the PNG.
