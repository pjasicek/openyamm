# Texture brief: gwashlar (Goblinwatch dressed stone trim)

Make ONE seamless, tileable game texture, square, 1024x1024 pixels, saved as
level_generation/projects/mm6_sorpigal_geometry_pilot/textures/codex/gwashlar.png

Use: the trim stones of a dark goblin castle in Might and Magic VI (OpenYAMM): quoins (corner stones), a cornice,
plinth courses, window sills, coping stones and battlements. It sits on walls made of the black rubble stone in
input 1 (tews.png), so it must belong to the same castle: the same dark basalt-like stone, but cut and dressed.

Content:
- Dressed ashlar: rectangular cut stone blocks in running bond, 4 courses over the tile height, blocks 1.5 to 2.5
  times as long as they are high, thin dark mortar joints (2-4 % of the tile), slightly chamfered block edges.
- Colour: dark charcoal grey basalt, a little lighter and smoother than the rubble in input 1 (mean brightness
  about 1.4x that of input 1), cool neutral grey, faint weathering and small chips, no moss, no colour cast.
- Input 3 (concept_crop.png) shows the intended look of the trim on the castle: lighter dressed edges against the
  dark rubble walls. Input 2 (rblst.png) is the castle's lighter wall-top cobble: do not copy it; it is too busy.

Rules:
- Seamless on both axes: the left edge continues into the right edge and the top into the bottom with no visible
  seam; courses must line up across the top/bottom edge.
- Straight-on orthographic view, even flat lighting, no cast shadows, no perspective, no vignette, no text.
- Painterly-realistic texture matching the 1990s-remastered style of the inputs; detail readable at 512x512.

Generate it with your built-in image generation tool, check the seams yourself (offset the image by half in both
axes mentally / with a quick script) and regenerate once if a seam or a perspective is visible. Save only the PNG.
