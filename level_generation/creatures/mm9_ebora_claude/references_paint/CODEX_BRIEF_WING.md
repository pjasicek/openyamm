# Codex brief: bat-wing texture for MM9 Ebora (mm9_ebora_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_ebora_claude/references_paint/`. No builds,
no Meshy. Use your built-in image generation tool.

This is a TEXTURE MAP for a 3D bat wing of a demon (a 2002 game restoration for a game mod), not an illustration.

## Inputs (attached, in order)
1. `references_paint/wing_template.png` (1536x1024): the wing's UV layout, the LEFT wing seen flat from the front. GREY
   = the membrane. WHITE lines = the bones (spars): the thick bent line on the left is the arm (it rises from the lower
   left, where the wing meets the back, to the wrist near the top left), the top edge is the long leading finger to the
   wing tip at the right, and two thinner fingers fan out from the wrist to the trailing edge. The short white stub at the
   wrist is a small claw. BLACK = nothing.
2. `references_paint/mm9_wing_views.png`: the ORIGINAL game model's wings (front and back view, top) and its wing skin
   (bottom left): colour and material authority. Ignore the body, the blur and the faceting.

## Deliverable
`wing_paint.png`, 1536x1024 landscape, no text, unresized. Keep raw returns in `raw/`, at most one corrective
regeneration, note it in `generation_runs_wing.json`.

## Paint
- Keep the layout EXACTLY: every grey pixel becomes membrane, every white line becomes bone at exactly the same place and
  width, the outline and the scalloped trailing edges stay where they are. Paint the membrane colour about 20 pixels
  past the outline into the black, then black beyond that.
- MEMBRANE: thin leathery bat-wing skin, saturated deep RED to crimson as input 2, a network of fine darker veins
  branching from the bones towards the trailing edge, faint wrinkles running along the fingers, slightly darker and
  thinner-looking near the scalloped trailing edges, a little darker near the bones. Even, flat lighting: an albedo map,
  no shadows, no highlights, no glow.
- BONES (the white lines): pale bone-grey and dull silver, knobbly, with a row of small dark spines along the top
  leading edge and a dark joint knuckle where the lines meet at the wrist and at the bends, as the spiked silver bones in
  input 2. The claw stub: black.
- Sharp fine detail everywhere, high resolution, no blur.

Do NOT: draw a body, a background scene, a second wing, text, a frame or a perspective view; move or bend the layout.
