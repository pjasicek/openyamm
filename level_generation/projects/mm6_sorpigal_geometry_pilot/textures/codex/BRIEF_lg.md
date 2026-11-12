# Texture brief: lgashlar (light grey dressed stone trim)

Make ONE seamless, tileable game texture, square, 1024x1024 pixels, saved as
level_generation/projects/mm6_sorpigal_geometry_pilot/textures/codex/lgashlar.png

Use: coping stones on a rubble bridge parapet, the stones of the bridge arch and a plinth course under a
half-timbered house in a bright town of Might and Magic VI (OpenYAMM). It sits next to the grey cobble rubble in
input 1 (rblbw.png), so it must belong to the same town: the same light-to-mid grey granite, but cut and dressed.

Content:
- Dressed ashlar: rectangular cut stone blocks in running bond, 4 courses over the tile height, blocks 1.5 to 2.5
  times as long as they are high, thin mortar joints a little darker than the stone (2-4 % of the tile), slightly
  chamfered block edges.
- Colour: light-to-mid warm grey granite, about as bright as the lightest stones in input 1, smooth faces with fine
  speckle and faint weathering, no moss, no colour cast.
- Input 2 (concept_bridge.png) shows the intended look: lighter dressed coping blocks on the darker rubble parapets.

Rules:
- Seamless on both axes: the left edge continues into the right edge and the top into the bottom with no visible
  seam; courses must line up across the top/bottom edge.
- Straight-on orthographic view, even flat lighting, no cast shadows, no perspective, no vignette, no text.
- Painterly-realistic texture matching the 1990s-remastered style of the inputs; detail readable at 512x512.

Generate it with your built-in image generation tool, check the seams yourself (offset the image by half in both
axes mentally / with a quick script) and regenerate once if a seam or a perspective is visible. Save only the PNG.
