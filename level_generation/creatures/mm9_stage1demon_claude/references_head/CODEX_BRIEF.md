# Codex brief: HD head turnaround for the MM9 Lesser Demon (mm9_stage1demon_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_stage1demon_claude/references_head/`. Do not edit any
other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

Purpose: these images model a HEAD-ONLY high-quality replacement (the three-quarter view is the single-image 3D modelling input)
and later texture it. This is a fantasy video-game demon monster, a restoration of an existing 2002 game character: stylised, no gore.

## Inputs (attached, in order; paths relative to the project)
1. `references_hd/00_three_quarter.png`: the SELECTED HD body master: identity, skin, horn and steel colours.
2. `references_hd/mm9_head_views.png`: renders of the ORIGINAL MM9 model's head and shoulders (front, three-quarter, left profile,
   back): shape authority (the low-poly faceting and shine are NOT the design).
3. `references_hd/mm9_skin_x4.png`: the original skin enlarged: colour and surface only.
4. (run 2 only) the selected `references_head/00_three_quarter.png`.

## Deliverables (1024x1024 SQUARE, true transparent background with hard edges and NO soft glow or halo, no text, unresized returns)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, faces image right and toward the viewer, camera slightly above eye level; primary. BOTH ram horns visible |
| `01_front.png` | exact straight-on front |
| `02_back.png` | straight from behind |
| `03_left.png` | pure profile, faces IMAGE LEFT (the figure's LEFT side is shown) |
| `04_right.png` | pure profile, faces IMAGE RIGHT (the figure's RIGHT side is shown) |

Run 1: `00_three_quarter.png` only, then stop. Run 2 (separate run): 01-04 with the selected 00 as an additional input, so all five
show the SAME head. At most ONE targeted corrective regeneration per view. Write `generation_runs.json` (id, prompt, inputs with
sha256, output, selected, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet; raw returns under `raw/`.

## Prompt content
FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the head of the EXISTING Might and Magic IX "Lesser Demon",
as a modelling reference. A HEAD ONLY with a short neck stump, cut with a clean level edge at the base of the neck. No shoulders, no
chest, no armour collar, no nape crest. Centred, generous margins, never cropped. Semi-realistic game materials, sharp fine detail.
Even soft studio light, no drama, no cast shadows, no glow, no dark background.

Identity:
- SHAPE: a long reptilian, dragon-like head: a broad flat-topped skull, a heavy angry brow ridge in a V, a long tapering snout with
  two nostrils at the tip, strong cheekbones, a long lower jaw with a complete squared chin.
- EYES: two narrow slanted glowing yellow-orange eyes with a dark slit pupil, set close under the brow ridge, facing forward.
- MOUTH: OPEN about 35 degrees: the lower jaw hangs down. Inside: a red-pink gum line, a dark red palate, a red tongue lying in
  the lower jaw, a dark throat at the back. Rows of sharp ivory fangs along the upper and lower jaws, individual teeth clearly
  separated, two longer fangs at the front of each jaw.
- HORNS: two thick pale bone-grey ram horns with ridged rings, rooted on the sides of the skull behind and above the eyes, curving
  out sideways and forward in a wide C, the tips pointing forward and up at brow height, about 45 cm across each curl. Both the
  same size and shape. A short sharp spur on each horn.
- SKIN: deep crimson and maroon reptilian hide with fine pebbled scales, larger plate scales on the snout and brow, darker
  brown-black in the hollows. No wounds.
- NECK: thick and scaly, same hide.

Do NOT: add a helmet, crest, hair, jewellery, shoulders, armour; close the mouth; add blood; add a soft alpha halo; change colours.

Per-image checks (redo at most once): whole head, both horns and the neck stump in frame; hard alpha edge; mouth open with both rows
of fangs and the tongue visible; complete chin; two eyes.
