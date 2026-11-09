# Codex brief: HD head turnaround for the MM6 Werewolf (wfigt1)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_wfigt1_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation, with the prompt style and record format of
`level_generation/creatures/mm6_ttn1_claude/references_head/generation_runs.json` (the titan's head turnaround;
follow its structure, not its content). Attached inputs:
1. `level_generation/creatures/mm6_wfigt1_claude/references_hd/01_front.png` — the SELECTED HD front body master:
   exact head, face, mane and fur identity authority.
2. `level_generation/creatures/mm6_wfigt1_claude/references_hd/00_three_quarter.png` — the selected HD three-quarter
   master: muzzle length, ear shape, mane and side detail.
3. `level_generation/creatures/mm6_wfigt1_claude/references_hd/02_back.png` — the selected HD back master: back of
   the head and the mane down the nape.
4. `level_generation/creatures/mm6_wfigt1/references/standing.png` — ORIGINAL native five-view sprites (magenta is
   background): supporting native head design only.

## Deliverables (5 images, exactly 1024 x 1024 SQUARE, transparent background, unresized returns)
- `00_front.png` — exact straight-on front (primary; generate first)
- `01_three_quarter.png` — front-right three-quarter
- `02_left.png` — the werewolf's own left side (he faces image LEFT)
- `03_back.png` — straight back
- `04_right.png` — the werewolf's own right side (he faces image RIGHT)
Generate 01–04 with 00 as an additional input so all five show the SAME head. Also write `generation_runs.json` and a
`selected_views_review.png` contact sheet; regenerate a view that breaks the checks; record superseded runs.

## Prompt content (adapt per view)
Use case: identity-preserve. Asset: head texture reference turnaround for the existing MM6 Werewolf, a texture
reference, not a new character design. Generate the EXACT SAME wolf head as the selected body masters, isolated from
the body: ONE HEAD AND NECK ONLY with its shaggy mane, no shoulders, no chest, no necklace. The furry neck ends with a
clean straight HORIZONTAL cut a little below the jaw. Head centred and level; from the ear tips to the neck cut fills
about 80% of the frame height, generous transparent margins on all sides, near-orthographic camera at eye height. Do
not crop the ears, the muzzle or the mane.

Identity (must match the body masters exactly): wolf head with a medium muzzle, black nose, short pointed upright ears
with pinkish-grey inner ears; charcoal-grey fur, lighter ash-grey on the muzzle and cheeks; a shaggy dark mane on the
crown, around the face and down the back of the neck; fierce YELLOW eyes with dark pupils under a heavy frowning brow;
mouth slightly open in a snarl showing white upper and lower fangs and a dark red mouth interior. Sharp fine detail:
fur strands, whiskers pads, teeth, eye highlights.

Even soft neutral studio illumination, no dramatic shadows, no rim light. No floor, cast shadow, glow, background
gradient, checkerboard drawn into the image, scene or text. No shoulders, chest, necklace or clothing. Do not change
colours (charcoal/ash-grey fur, yellow eyes, black nose, white fangs).

Checks per image: 1024 x 1024; true transparency; only head and neck with a straight horizontal cut below the jaw;
ears and mane inside the frame; yellow eyes with pupils; fangs visible in the slightly open mouth; same head as the
primary and the body masters; side views facing the stated direction.
