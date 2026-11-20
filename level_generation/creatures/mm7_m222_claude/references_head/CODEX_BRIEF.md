# Codex brief: head turnaround for the MM7 Chain Fighter (m222)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m222_claude/references_head/`.
No builds, no Meshy, no other files.

Inputs (paths relative to `level_generation/creatures/`):
1. `mm7_m222_claude/references_hd/01_front.png` — selected HD body master, front. IDENTITY AUTHORITY.
2. `mm7_m222_claude/references_hd/00_three_quarter.png` — selected HD primary.
3. `mm7_m222_claude/references_hd/04_right.png` — selected HD right profile.
4. `mm7_m222_claude/references_hd/02_back.png` — selected HD back.

Deliverables: four square 1254 x 1254 images, true transparent background, unresized returns, one bust each:
`00_front.png` (straight front), `01_three_quarter.png` (front three-quarter, face turned toward image right as in
input 2), `02_profile.png` (her RIGHT profile, facing image right, as input 3), `03_back.png` (straight back).
Keep raw returns under `raw/`, record each run in `generation_runs.json` (id, prompt, input sha256, output path,
selected flag, reason) and save each prompt as `<name>_prompt.txt`.

Prompt (adapt the camera per view): Head-and-shoulders modelling texture reference of the EXACT woman in the supplied
HD masters (MM7 Chain Fighter soldier): same face, fair skin, calm stern expression, blue-grey eyes, age about 25-30,
long straight light-brown hair hanging behind the shoulders, the same rounded steel kettle helmet with a narrow brim,
gold rim and short gold crest ridge on top. Bust cut at the base of the neck, just above the chain-mail collar; no
armour, shoulders, weapon or scabbard below the cut. Neutral even flat studio light, no dramatic shadows, no text,
no floor. High detail of skin, eyes, lips, hair strands and the helmet's metal. Same identity in all four views.

Checks per view: correct camera (front / three-quarter / right profile facing image right / back), same face and
helmet as input 1, the hair falls behind the neck, nothing cropped, square 1254, true alpha. At most ONE targeted
corrective regeneration per view; then select the better and note any residual fault.
