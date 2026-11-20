# Codex brief: head turnaround for the MM7 Ghost (m242)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m242_claude/references_head/`.
No builds, no Meshy, no other files.

Inputs (paths relative to `level_generation/creatures/`):
1. `mm7_m242_claude/references_hd/01_front.png` — selected HD body master, front. IDENTITY AUTHORITY.
2. `mm7_m242_claude/references_hd/00_three_quarter.png` — selected HD primary (skull toward image LEFT).
3. `mm7_m242_claude/references_hd/04_right.png` — selected HD right profile (faces image right).
4. `mm7_m242_claude/references_hd/02_back.png` — selected HD back.

Deliverables: four square 1254 x 1254 images, true transparent background, unresized returns, one bust each:
`00_front.png` (straight front), `01_three_quarter.png` (front three-quarter, skull turned toward image LEFT as in
input 2), `02_profile.png` (its RIGHT profile, facing image right, as input 3), `03_back.png` (straight back).
Keep raw returns under `raw/`, record each run in `generation_runs.json` (id, prompt, input sha256, output path,
selected flag, reason) and save each prompt as `<name>_prompt.txt`.

Prompt (adapt the camera per view): Head-and-hood modelling texture reference of the EXACT ghost in the supplied HD
masters (MM7 Ghost): the same yellowed ivory human SKULL with large black hollow eye sockets, black nasal opening, a
full row of worn teeth and a closed jaw; the cervical vertebrae under it; inside the same deep pointed dark umber-brown
coarse woollen HOOD, worn and moth-eaten, its pointed peak at the back of the head; the hood frames the skull. Bust cut
at the shoulders just below the hood's lower edge; no ribcage, arms or robe body. Neutral even flat studio light, no
dramatic shadows, no glow, no text, no floor. High detail of the bone and the cloth weave. Same identity in all views.

Checks per view: correct camera (front / three-quarter toward image left / right profile facing image right / back),
same skull and hood as input 1, nothing cropped (hood peak included), square 1254, true alpha. At most ONE targeted
corrective regeneration per view; then select the better and note any residual fault.
