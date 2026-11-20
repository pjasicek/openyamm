# Codex brief: head turnaround for the MM7 Behemoth (mm7_m162_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m162_claude/references_head/`.
No builds, no Meshy, no other files.

Inputs, in order: 1. `references_hd/00_three_quarter.png` (selected primary body master, identity authority);
2. `references_hd/01_front.png` (selected front master); 3. `references_hd/03_left.png` (selected left-side master).

Deliverables: four square 1254 x 1254 PNGs, true transparent background, unresized returns, head-only bust of the EXACT
Behemoth in the inputs, cut just below the jaw and beard (include the green beard and the mane on the head and nape,
not the shoulders or arms). Same face, tusks, teeth, orange eyes, small pointed ears, brow, nose, grey-beige stony
hide, green mane and beard colours as the masters. Mouth open as in the masters (upper and lower ivory tusks visible).
Neutral even flat studio light, no shadow, no text, no background, one head per image, generous margins.
- `00_front.png` — straight front, looking at the camera.
- `01_three_quarter.png` — front three-quarter, face turned toward image left.
- `02_profile.png` — exact side profile facing image LEFT (only one eye and one ear visible).
- `03_back.png` — straight back of the head (mane), no face visible.
Generate 00 first and use it as an extra input for 01–03 so all four show the same head. At most one corrective
regeneration per view. Record `generation_runs.json` (id, prompt, inputs with sha256, output, selected, reason).
Do NOT: add horns, change colours, close the mouth, add a neck or shoulders, crop the mane.
