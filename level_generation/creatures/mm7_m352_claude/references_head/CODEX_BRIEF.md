# Codex brief: head turnaround for the MM7 Peasant Human1 Male (m352)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m352_claude/references_head/`.
No builds, no Meshy, no other files.

Inputs (paths relative to `level_generation/creatures/`):
1. `mm7_m352_claude/references_hd/01_front.png` — selected HD body master, front. IDENTITY AUTHORITY.
2. `mm7_m352_claude/references_hd/00_three_quarter.png` — selected HD primary.
3. `mm7_m352_claude/references_hd/04_right.png` — selected HD right profile.
4. `mm7_m352_claude/references_hd/02_back.png` — selected HD back.

Deliverables: four square 1254 x 1254 images, true transparent background, unresized returns, one bust each:
`00_front.png` (straight front), `01_three_quarter.png` (front three-quarter, face turned toward image right as in
input 2), `02_profile.png` (his RIGHT profile, facing image right, as input 3), `03_back.png` (straight back).
Keep raw returns under `raw/`, record each run in `generation_runs.json` (id, prompt, input sha256, output path,
selected flag, reason) and save each prompt as `<name>_prompt.txt`.

Prompt (adapt the camera per view): Head-and-shoulders modelling texture reference of the EXACT man in the supplied
HD masters (MM7 male human peasant): same face, light tan skin, calm neutral expression, dark brown eyes, age about
30-35, long straight black hair parted in the middle falling past the shoulders, black moustache and short full
beard, no hat or headwear, the green wool tunic's round neckline with its row of small brass studs. Bust cut at the
base of the neck, just below the studded neckline. Neutral even flat studio light, no dramatic shadows, no text, no
floor. High detail of skin, eyes, lips, beard, hair strands. Same identity in all four views.

Checks per view: correct camera (front / three-quarter / right profile facing image right / back), same face, hair
and beard as input 1, nothing cropped, square 1254, true alpha. At most ONE targeted corrective regeneration per view;
then select the better and note any residual fault.
