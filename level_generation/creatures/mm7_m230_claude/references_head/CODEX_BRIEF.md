# Codex brief: helm turnaround for the MM7 Plate Fighter (m230)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m230_claude/references_head/`.
No builds, no Meshy, no other files.

Inputs (paths relative to `level_generation/creatures/`):
1. `mm7_m230_claude/references_hd/01_front.png` — selected HD body master, front. IDENTITY AUTHORITY.
2. `mm7_m230_claude/references_hd/00_three_quarter.png` — selected HD primary.
3. `mm7_m230_claude/references_hd/04_right.png` — selected HD right profile.
4. `mm7_m230_claude/references_hd/02_back.png` — selected HD back.

Deliverables: four square 1254 x 1254 images, true transparent background, unresized returns, one helm each:
`00_front.png` (straight front), `01_three_quarter.png` (front three-quarter, turned toward image right as in input 2),
`02_profile.png` (his RIGHT profile, facing image right, as input 3), `03_back.png` (straight back). Keep raw returns
under `raw/`, record each run in `generation_runs.json` (id, prompt, input sha256, output path, selected flag, reason)
and save each prompt as `<name>_prompt.txt`.

Prompt (adapt the camera per view): Modelling texture reference of the EXACT great helm of the knight in the supplied
HD masters (MM7 Plate Fighter): a cylindrical flat-topped polished steel great helm with a narrow eye slit and vertical
breathing slot forming a T visor, gold rim bands, the small gold eagle crest on top and the long green-and-white
feather plume flowing from the crest down the back. Cut just below the helm's lower edge with a sliver of the gorget;
no shoulders, armour or tabard below. No face visible. Neutral even flat studio light, no dramatic shadows, no text,
no floor. High detail of the steel, gold trim, rivets and feathers. Same helm in all four views.

Checks per view: correct camera (front / three-quarter / right profile facing image right / back), same helm, crest
and plume as input 1, nothing cropped (the plume tip included), square 1254, true alpha. At most ONE targeted
corrective regeneration per view; then select the better and note any residual fault.
