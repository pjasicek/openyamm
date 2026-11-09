# Codex brief: paint MM9 Yanmir's head (mm9_yanmir_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_yanmir_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game frost giant king restored from a 2002 game for a game mod. The result is projected onto a 3D head, so **every painted view must keep the
exact outline and feature positions of its clay input**, pixel for pixel: eyes, nose, mouth, ears, brow, beard, hair edge, chin. Only surface paint is added.
Do not change the shape, do not turn or tilt the head, do not add hair volume beyond the clay's outline, do not add a crown (his crown is a separate part).

## Inputs (attached, in order)
1-5. `clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`, `clay_05_top.png`: the clay head, geometry authority.
6. `references_hd/mm9_head_views.png`: the original Yanmir head (front, three-quarter, left, back): identity, hair and beard layout, colour.
7. `references_hd/mm9_skin_x4.png`: the original skin (his face is top left): colour and material.
8. `references_head/in_body_head.png`: the high-definition master's head: the target look (ignore its crown).

## Deliverables (true transparent background, same size as the clay, unresized returns, no floor, no shadow, no text)
`a_01_front.png`, `a_03_left.png`, `a_02_back.png`, `a_04_right.png`, `a_05_top.png`.
Generate the front first, then use it as an extra input for the other views. One corrective regeneration at most per view. Keep raw returns in `raw/`.
Write `generation_runs_a.json` (id, prompt, inputs with sha256, output path).
Even soft studio light, no cast shadows, no rim light: the paint is a colour map. Semi-realistic game-art materials with sharp detail: fine frosted hair
strands, pores and fine wrinkles on the face.

## Paint
- SKIN (face, ears, neck): pale icy blue, like frozen skin: light cold blue with white frost highlights on the forehead, nose bridge and cheekbones,
  slightly deeper blue in the creases and around the eyes. NOT human pink or tan.
- EYES: pale ice-blue irises with small dark pupils, white sclera with a blue tint, dark blue-grey upper lid lines. Paint them exactly on the clay's
  eye openings, one pair only.
- BROWS: heavy frosted white-blue brows on the clay's brow ridge.
- LIPS: slightly darker blue-grey, closed, a thin dark line between them on the clay's mouth line; no teeth.
- HAIR (crown, back, sides behind the ears): long straight frosted hair in streaks of white, pale blue and mid blue, as input 6; fine vertical strands
  following the clay's grooves; the parting runs from the forehead back.
- BEARD and MOUSTACHE: frosted white-blue, the same streaked strands as the hair, flowing down to the beard's blunt tip; slightly icy (a few clear
  icicle-like strand ends at the tip).
- TOP view: the hair from above, parted at the centre.
