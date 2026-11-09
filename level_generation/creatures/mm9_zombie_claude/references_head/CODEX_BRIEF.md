# Codex brief: HD head turnaround for the MM9 Rotter (mm9_zombie_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_zombie_claude/references_head/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool.

Purpose: the body model came back with a smooth bald human head. These images model a HEAD-ONLY replacement (the three-quarter view is the
single-image 3D modelling input) and later texture it. This is a fantasy video-game undead monster, a restoration of an existing 2002
game character: stylised dry decay, no fresh gore.

## Inputs (attached, in order; paths relative to the project)
1. `references_hd/00_three_quarter.png`: the SELECTED HD body master: identity, skin colour and hair colour.
2. `references_hd/mm9_head_views_a.png`: renders of the ORIGINAL MM9 model's head and shoulders (front, three-quarter, left profile, back): shape authority
   (the low-poly faceting and white shine are NOT the design).
3. `references_hd/mm9_skin_x4_a.png`: the original skin enlarged; its top-left corner is the painted face and hair: colour and surface only.
4. (run 2 only) the selected `references_head/00_three_quarter.png`.

## Deliverables (1024x1024 SQUARE, true transparent background with hard edges and NO soft glow or halo, no text, unresized returns)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, faces image right and toward the viewer, camera slightly above eye level; primary |
| `01_front.png` | exact straight-on front |
| `02_back.png` | straight from behind |
| `03_left.png` | pure profile, faces IMAGE LEFT (the figure's LEFT side is shown) |
| `04_right.png` | pure profile, faces IMAGE RIGHT (the figure's RIGHT side is shown) |

Run 1: `00_three_quarter.png` only, then stop. Run 2 (separate run): 01-04 with the selected 00 as an additional input, so all five show the SAME head.
At most ONE targeted corrective regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output, selected, reason, superseded runs) and,
after run 2, a `selected_views_review.png` contact sheet; raw returns under `raw/`.

## Prompt content
FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the head of the EXISTING Might and Magic IX zombie "Rotter", as a modelling reference. A bust only:
head and neck, cut with a clean level edge at the base of the neck. No shoulders, no chest. Centred, generous margins, never cropped. Semi-realistic game materials, sharp fine detail. Even soft studio light, no drama, no cast shadows, no glow.

Identity:
- SHAPE: an adult male corpse's head with a real human skull shape: a full rounded cranium, a strong brow, cheekbones standing out above hollow cheeks, a long lean jaw and a complete, squared human CHIN. The face is shrunken onto the bone, the head is not smaller than a living man's. Not an alien, not a bare skull.
- EYES: deep dark sunken sockets with a small dull amber eye in each, wrinkled lids.
- NOSE: a shrunken nose with the nostrils pulled open, cartilage partly gone.
- MOUTH: lips rotted and drawn far back in a wide fixed rictus GRIN. Large long yellow-ivory teeth, upper and lower rows, clenched together, a clear individual row of teeth, gums dark and dried. The mouth does not gape.
- HIS RIGHT CHEEK (the cheek visible in the selected 00 image; IMAGE LEFT in the front view, and shown in the 04_right profile): a torn hole from the corner of the mouth toward the ear, showing the back teeth, dark dried red inside. His left cheek is whole.
- SKIN: dry yellow-olive leathery skin, wrinkled, darker in the hollows, a few dark-brown scabs.
- HAIR: thick matted lank brown hair as a solid mass, in heavy clumps close to the skull, covering the whole cranium, parted roughly over the forehead, falling straight past the ears and down over the nape to the base of the neck, ending in a few ragged locks. No loose flying strands, no thin wisps standing off: it reads as a thick cap with clumped locks, as a 3D modeller would sculpt it. Ears hidden.
- NECK: gaunt with visible cords, same dry skin.

Do NOT: add a helmet, hood, jewellery, shoulders; open the mouth; show a bald crown; add fresh blood or splatter; soft alpha halo; change colours.

Per-image checks (redo at most once): whole head and neck in frame; hard alpha edge; teeth clenched with both rows visible; tear on his RIGHT cheek; hair covering the crown and nape; complete chin.
