# Codex brief: head turnaround for the MM7 Harpy (m262)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m262_claude/references_head/`.
No builds, no Meshy, no other files.

Inputs (paths relative to `level_generation/creatures/`):
1. `mm7_m262_claude/references_hd/01_front.png` — selected HD body master, front. IDENTITY AUTHORITY.
2. `mm7_m262_claude/references_hd/00_three_quarter.png` — selected HD primary (face toward image LEFT).
3. `mm7_m262_claude/references_hd/04_right.png` — selected HD right profile (faces image right).
4. `mm7_m262_claude/references_hd/02_back.png` — selected HD back.

Deliverables: four square 1254 x 1254 images, true transparent background, unresized returns, one bust each:
`00_front.png` (straight front), `01_three_quarter.png` (front three-quarter, face turned toward image LEFT as in
input 2), `02_profile.png` (her RIGHT profile, facing image right, as input 3), `03_back.png` (straight back).
Keep raw returns under `raw/`, record each run in `generation_runs.json` (id, prompt, input sha256, output path,
selected flag, reason) and save each prompt as `<name>_prompt.txt`.

Prompt (adapt the camera per view): Head-and-neck modelling texture reference of the EXACT harpy woman in the
supplied HD masters (MM7 Harpy): the same gaunt stern middle-aged face, sharp nose, high cheekbones, tan-olive skin,
dark eyes; long silver-white hair swept straight back from the forehead into a crest down the back of the head and
the nape, a few strands falling forward over the shoulders. Bust cut at the base of the neck above the bodice; no
bodice, wings, arms or weapon. Neutral even flat studio light, no dramatic shadows, no text, no floor. High detail of
skin, eyes and hair. Same identity in all four views.

Checks per view: correct camera (front / three-quarter facing image left / right profile facing image right / back),
same face and hair as input 1, nothing cropped (hair included), square 1254, true alpha. At most ONE targeted
corrective regeneration per view; then select the better and note any residual fault.
