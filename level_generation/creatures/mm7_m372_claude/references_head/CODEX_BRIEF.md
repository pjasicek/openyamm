# Codex brief: head turnaround for the MM7 Peasant Human2 Female (m372)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m372_claude/references_head/`.
No builds, no Meshy, no other files.

Inputs (paths relative to `level_generation/creatures/`):
1. `mm7_m372_claude/references_hd/01_front.png` — selected HD body master, front. IDENTITY AUTHORITY.
2. `mm7_m372_claude/references_hd/00_three_quarter.png` — selected HD primary.
3. `mm7_m372_claude/references_hd/04_right.png` — selected HD right profile.
4. `mm7_m372_claude/references_hd/02_back.png` — selected HD back.

Deliverables: four square 1254 x 1254 images, true transparent background, unresized returns, one bust each:
`00_front.png` (straight front), `01_three_quarter.png` (front three-quarter, face turned toward image right as in
input 2), `02_profile.png` (her RIGHT profile, facing image right, as input 3), `03_back.png` (straight back).
Keep raw returns under `raw/`, record each run in `generation_runs.json` (id, prompt, input sha256, output path,
selected flag, reason) and save each prompt as `<name>_prompt.txt`.

Prompt (adapt the camera per view): Head-and-shoulders modelling texture reference of the EXACT woman in the supplied
HD masters (MM7 female human peasant): same face, light skin, red lips, calm neutral expression, age about 30, short
auburn-brown fringe, thin gold circlet across the forehead, the pale sage-green veil over the head and draped round
the neck and shoulders, its face edge trimmed with small dark-green beads; at the bottom the beaded round neckline of
the forest-green gown. Bust cut just below the neckline. Neutral even flat studio light, no dramatic shadows, no text,
no floor. High detail of skin, eyes, lips, fringe, circlet, veil folds and beads. Same identity in all four views.

Checks per view: correct camera (front / three-quarter / right profile facing image right / back), same face, veil
and circlet as input 1, nothing cropped, square 1254, true alpha. At most ONE targeted corrective regeneration per
view; then select the better and note any residual fault.
