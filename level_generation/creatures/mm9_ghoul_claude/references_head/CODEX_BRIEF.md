# Codex brief: HD head turnaround for the MM9 Ghast (mm9_ghoul_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_ghoul_claude/references_head/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool.

Purpose: these images model a HEAD-ONLY high-quality replacement (the three-quarter view is the single-image 3D modelling input) and later
texture it. This is a fantasy video-game undead monster, a restoration of an existing 2002 game character: stylised, no gore.

## Inputs (attached, in order; paths relative to the project)
1. `references_hd/00_three_quarter.png`: the SELECTED HD body master: identity, skin colour and hair colour. Ignore its glowing background.
2. `references_hd/mm9_head_views_a.png`: renders of the ORIGINAL MM9 model's head and shoulders (front, three-quarter, left profile, back): shape authority
   (the low-poly faceting and shine are NOT the design).
3. `references_hd/mm9_skin_x4_a.png`: the original skin enlarged; its top-left corner is the painted face and hair: colour and surface only.
4. (run 2 only) the selected `references_head/00_three_quarter.png`.

## Deliverables (1024x1024 SQUARE, true transparent background with hard edges and NO soft glow or halo, no text, unresized returns)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, faces image right and toward the viewer, camera slightly above eye level; primary. BOTH ears must be visible |
| `01_front.png` | exact straight-on front |
| `02_back.png` | straight from behind |
| `03_left.png` | pure profile, faces IMAGE LEFT (the figure's LEFT side is shown) |
| `04_right.png` | pure profile, faces IMAGE RIGHT (the figure's RIGHT side is shown) |

Run 1: `00_three_quarter.png` only, then stop. Run 2 (separate run): 01-04 with the selected 00 as an additional input, so all five show the SAME head.
At most ONE targeted corrective regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output, selected, reason, superseded runs) and,
after run 2, a `selected_views_review.png` contact sheet; raw returns under `raw/`.

## Prompt content
FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the head of the EXISTING Might and Magic IX ghoul "Ghast", as a modelling reference. A bust only:
head and neck, cut with a clean level edge at the base of the neck. No shoulders, no chest. Centred, generous margins, never cropped. Semi-realistic game materials, sharp fine detail. Even soft studio light, no drama, no cast shadows, no glow, no dark background.

Identity:
- SHAPE: a long lean ghoul head: full rounded cranium, heavy angry brow ridge that meets in a V above the nose, cheekbones standing out above hollow cheeks, a long jaw and a complete, squared CHIN.
- EYES: deep dark sockets with a small amber eye in each, wrinkled lids.
- NOSE: long and narrow with a broad rounded tip and flared nostrils.
- MOUTH: the lips are gone, drawn back in a wide fixed snarl around a dark mouth gap. Long thin sharp ivory teeth, upper and lower rows clenched and interlocked with no gap, individual teeth clearly separated, two longer fangs in the upper row, gums pale and dried. The mouth does not gape.
- EARS: very large pointed ears like a bat or goblin, about 22 cm long, leaf shaped, each with a real inner hollow, standing out from the sides of the head level with the eyes and swept up and back, tip above the crown. Both ears are the same size and shape.
- SKIN: yellow-olive wrinkled hide, darker olive-brown in the hollows. No wounds.
- HAIR: dark brown-black straight hair. A short widow's peak at the top of the forehead, a band over the top of the crown, then falling straight down the back of the skull as one thick flat mass behind the ears, down past the base of the neck, ending in a few ragged clumped locks. The sides of the head and the ears are bare. It reads as a solid sculpted mass with clumped locks. No loose flying strands, no thin wisps standing off.
- NECK: lean with visible cords, same hide.

Do NOT: add a helmet, hood, jewellery, shoulders; open the mouth wide; add blood; add soft alpha halo; change colours.

Per-image checks (redo at most once): whole head, both ears and neck in frame; hard alpha edge; teeth clenched with both rows visible; complete chin; hair behind the ears only.
