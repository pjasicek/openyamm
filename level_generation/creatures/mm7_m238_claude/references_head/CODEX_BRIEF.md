# Codex brief: head turnaround for the MM7 Genie (m238)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m238_claude/references_head/`.
No builds, no Meshy, no other files.

Inputs (paths relative to `level_generation/creatures/`):
1. `mm7_m238_claude/references_hd/01_front.png` — selected HD body master, front. IDENTITY AUTHORITY.
2. `mm7_m238_claude/references_hd/00_three_quarter.png` — selected HD primary (face toward image LEFT).
3. `mm7_m238_claude/references_hd/04_right.png` — selected HD right profile (faces image right).
4. `mm7_m238_claude/references_hd/02_back.png` — selected HD back.

Deliverables: four square 1254 x 1254 images, true transparent background, unresized returns, one bust each:
`00_front.png` (straight front), `01_three_quarter.png` (front three-quarter, face turned toward image LEFT as in
input 2), `02_profile.png` (her RIGHT profile, facing image right, as input 3), `03_back.png` (straight back).
Keep raw returns under `raw/`, record each run in `generation_runs.json` (id, prompt, input sha256, output path,
selected flag, reason) and save each prompt as `<name>_prompt.txt`.

Prompt (adapt the camera per view): Head-and-neck modelling texture reference of the EXACT genie in the supplied HD
masters (MM7 Genie): same stern beautiful face, cobalt-blue skin, almond eyes, pointed elf ears; navy-blue hair pulled
into a tall high ponytail wrapped by polished gold rings and ending in a gold cone tip; a thin gold circlet with a
small red forehead jewel; long green drop earrings; a green high collar with gold edges around the neck. Bust cut just
below the collar; no top, arms or vortex. The WHOLE ponytail inside the frame. Neutral even flat studio light, no
dramatic shadows, no text, no floor. High detail of skin, eyes, hair and gold. Same identity in all four views.

Checks per view: correct camera (front / three-quarter facing image left / right profile facing image right / back),
same face, hair, ponytail and jewellery as input 1, nothing cropped (the ponytail and its gold tip included), square
1254, true alpha. At most ONE targeted corrective regeneration per view; then select the better and note any residual
fault.
