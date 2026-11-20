# Codex brief: head turnaround for the MM7 Goblin (m246)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m246_claude/references_head/`.
No builds, no Meshy, no other files.

Inputs (paths relative to `level_generation/creatures/`):
1. `mm7_m246_claude/references_hd/01_front.png` — selected HD body master, front. IDENTITY AUTHORITY.
2. `mm7_m246_claude/references_hd/00_three_quarter.png` — selected HD primary.
3. `mm7_m246_claude/references_hd/04_right.png` — selected HD right profile.
4. `mm7_m246_claude/references_hd/02_back.png` — selected HD back.

Deliverables: four square 1254 x 1254 images, true transparent background, unresized returns, one bust each:
`00_front.png` (straight front), `01_three_quarter.png` (front three-quarter, face turned toward image right as in
input 2), `02_profile.png` (his RIGHT profile, facing image right, as input 3), `03_back.png` (straight back).
Keep raw returns under `raw/`, record each run in `generation_runs.json` (id, prompt, input sha256, output path,
selected flag, reason) and save each prompt as `<name>_prompt.txt`.

Prompt (adapt the camera per view): Head-and-neck modelling texture reference of the EXACT goblin warrior in the
supplied HD masters (MM7 Goblin): same stern angular green face, olive-green skin with yellow-green highlights, heavy
brow, narrow yellow eyes, broad flat nose, small jutting lower tusks, short dark purple chin tuft, pointed green ears;
the same ornate gold helmet: a crown-like brow band with upward spikes, riveted gold cheek guards hanging beside the
face, and the base of the tall gold crest on top (show only the lower 10 cm of the crest; it is modelled separately);
reddish-brown hair falling from under the back of the helmet onto the neck. Bust cut at the base of the neck, just
above the vest; no vest, shoulders armour, arms or weapon. Neutral even flat studio light, no dramatic shadows, no
text, no floor. High detail of skin, eyes, tusks, the chin tuft and the helmet's gold. Same identity in all four views.

Checks per view: correct camera (front / three-quarter / right profile facing image right / back), same face, ears,
tusks, chin tuft and helmet as input 1, nothing cropped (helmet spikes included), square 1254, true alpha. At most ONE
targeted corrective regeneration per view; then select the better and note any residual fault.
