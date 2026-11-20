# Codex brief (v2): bare-head turnaround for the MM7 Angel (m150); the helmet is a separate model

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m150_claude/references_head/v2/`.
No builds, no Meshy, no other files.

Inputs (paths relative to `level_generation/creatures/`):
1. `mm7_m150_claude/references_hd/v2/00_three_quarter.png` — selected v2 HD primary (bare head). IDENTITY AUTHORITY.
2. `mm7_m150_claude/references_head/00_front.png` — v1 head front: the SAME FACE (ignore its helmet).
3. `mm7_m150_claude/references_head/02_profile.png` — v1 right profile: the same face in profile (ignore the helmet).
4. `mm7_m150_claude/references_head/03_back.png` — v1 back: hair length at the back (ignore the helmet).

Deliverables: four square 1254 x 1254 images, true transparent background, unresized returns, one bust each:
`v2/00_front.png` (straight front), `v2/01_three_quarter.png` (front three-quarter, face turned toward image LEFT as in
input 2), `v2/02_profile.png` (his RIGHT profile, facing image right, as input 3), `v2/03_back.png` (straight back).
Keep raw returns under `v2/raw/`, record each run in `generation_runs.json` (id, prompt, input sha256, output path,
selected flag, reason) and save each prompt as `<name>_prompt.txt`.

Prompt (adapt the camera per view): Head-and-neck modelling texture reference of the EXACT winged warrior in the
supplied HD masters (MM7 Angel): same stern clean-shaven face, tan skin, strong jaw, straight nose, dark eyes, age about
30; BARE HEAD with NO helmet, no headband and no ornaments: dark brown wavy hair combed back close to the skull on top
(a helmet will sit over it) and falling to the nape at the back, ears visible, as input 1. Bust cut at the base of the neck just above the breastplate collar; no breastplate, arms,
wings or weapon. Neutral even flat studio light, no dramatic shadows, no text, no floor. High detail of skin, eyes,
hair and the brass. Same identity in all four views.

Checks per view: correct camera (front / three-quarter facing image left / right profile facing image right / back),
same face and hair as inputs 1-2, no helmet, nothing cropped, square 1254, true alpha. At most ONE targeted
corrective regeneration per view; then select the better and note any residual fault.
