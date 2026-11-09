# Codex brief: HD head turnaround for the MM6 Titan (ttn1)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_ttn1_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation, with the prompt style and record format of
`level_generation/creatures/mm6_gua_claude/references_head/generation_runs.json` (that is the guard's head
turnaround; follow its structure, not its content). Attached inputs:
1. `level_generation/creatures/mm6_ttn1_claude/references_hd/01_front.png` — the SELECTED HD front body master:
   exact head, helmet, crest and face identity authority.
2. `level_generation/creatures/mm6_ttn1_claude/references_hd/00_three_quarter.png` — the selected HD three-quarter
   master: helmet construction, crest shape and side detail.
3. `level_generation/creatures/mm6_ttn1_claude/references_hd/02_back.png` — the selected HD back master: back of the
   helmet and crest.
4. `level_generation/creatures/mm6_ttn1/references/standing.png` — ORIGINAL native five-view sprites (magenta is
   background): supporting native helmet design only.

## Deliverables (5 images, exactly 1024 x 1024 SQUARE, transparent background, unresized returns)
- `00_front.png` — exact straight-on front (primary; generate first)
- `01_three_quarter.png` — front-right three-quarter
- `02_left.png` — the titan's own left side (he faces image LEFT)
- `03_back.png` — straight back
- `04_right.png` — the titan's own right side (he faces image RIGHT)
Generate 01–04 with 00 as an additional input so all five show the SAME head. Also write `generation_runs.json` and a
`selected_views_review.png` contact sheet; regenerate a view that breaks the checks; record superseded runs.

## Prompt content (adapt per view)
Use case: identity-preserve. Asset: head texture reference turnaround for the existing MM6 Titan, a texture reference,
not a new character design. Generate the EXACT SAME helmeted head as the selected body masters, isolated from the
body: ONE HEAD AND NECK ONLY, no shoulders, no armour collar, no chest. The bare grey neck ends with a clean straight
HORIZONTAL cut a little below the chin and jaw. Head centred and level; from the top of the red crest to the neck cut
fills about 80% of the frame height, generous transparent margins on all sides, near-orthographic camera at eye
height. Do not crop the crest.

Identity (must match the body masters exactly): cool pale stone-grey skin with darker grey shading, stern classical
face, strong jaw, straight nose, closed mouth, clean-shaven; eyes pale and blank (white, no visible pupils).
Lavender-blue / periwinkle Corinthian-style open-face helmet with a hammered, slightly mottled metal surface; gold
brow band rising to a pointed gold triangular ornament over the forehead; gold rims down the cheek guards that frame
the face (face fully visible); small round boss on each side of the helmet over the ears; tall RED horsehair crest
running front to back over the top of the helmet, with fine strands. Sharp fine detail: hammered metal, gold edges,
crest strands, skin pores and brow.

Even soft neutral studio illumination, no dramatic shadows, no rim light. No floor, cast shadow, glow, background
gradient, checkerboard drawn into the image, scene or text. No shoulders, pauldrons, cuirass, collar or chest. Do not
change colours (grey skin, lavender-blue helmet, gold trim, red crest) and do not cover the face.

Checks per image: 1024 x 1024; true transparency; only head and neck with a straight horizontal cut below the jaw;
whole crest inside the frame; gold brow ornament and cheek-guard rims; white blank eyes; same head as the primary and
the body masters; side views facing the stated direction.
