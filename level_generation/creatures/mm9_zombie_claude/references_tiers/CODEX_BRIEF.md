# Codex brief: tier masters for the MM9 zombie (mm9_zombie_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_zombie_claude/references_tiers/`. Do not edit any other file, do not run builds, do not call Meshy.
Use your built-in image generation tool. Fantasy video-game undead, a restoration of an existing 2002 game character: stylised dry decay, no fresh gore.

MM9 uses ONE body for three monsters and paints different clothes on it. The selected Rotter masters show the shared figure. These masters repaint that SAME figure in the SAME pose, camera and proportions
in the other two designs. They will be projected onto one 3D model, so silhouette, pose and scale must match the input master exactly, pixel for pixel as far as you can: only the surface paint changes, no thicker clothes, no new silhouette.

## Inputs, in order (paths relative to the project)
Run b:  1 `references_tiers/input_a_views.png` (selected Rotter masters: front, back, left side, right side, left to right): figure, pose, scale. 2 `references_hd/mm9_views_b.png`: renders of the ORIGINAL model with the Dripper skin: design authority (front three-quarter, front, left, back, right). 3 `references_hd/mm9_skin_x4_b.png`: the original skin enlarged, colour and material only.
Run c:  the same with `mm9_views_c.png` and `mm9_skin_x4_c.png`.

## Deliverables (each a 1024x1536 portrait, true transparent background, hard alpha, NO soft halo or glow, no text; one figure per image)
Run b: `b_01_front.png`, `b_02_back.png`, `b_03_left.png`, `b_04_right.png`. Run c: `c_01_front.png`, `c_02_back.png`, `c_03_left.png`, `c_04_right.png`.
Same views as the input: `_front` the figure's RIGHT arm on IMAGE LEFT, `_back` the figure's RIGHT arm on IMAGE RIGHT, `_left` faces IMAGE LEFT, `_right` faces IMAGE RIGHT. Generate one image per file, each with the matching single master crop from input 1 in mind. At most one corrective regeneration per view. Keep raw returns in `raw/`; write `generation_runs_<run>.json` (prompt, input sha256, output, selected, reason).

## Design b, "Dripper"
From the neck to the belt he wears a sleeveless torn dark-tan LEATHER VEST, open in a narrow V at the chest and laced across with a thin pale thong; the pale linen undershirt is torn open under the lacing; a torn hole on the lower left of the vest shows olive-green rot, and on the back of the vest three torn holes show pale skin, as in input 2. Shoulders covered by the vest edge, the arms below it bare with pale yellow and green mottled rotting skin. A brown leather BELT with a plain oval iron buckle at the waist. Below the belt, short torn tan cloth tatters tight on the hips. Same trousers, knees, shin bone, feet as the input but mid-brown, with pale torn patches at the knees. Hair white-grey.

## Design c, "Zombie"
From the neck to the belt he wears a sleeveless hauberk of fine dark steel-grey CHAIN MAIL (regular tiny interlocking rings, clearly mail, rusty dark red-brown where it is torn), open in a V at the throat showing olive skin; a torn hole in the chest and lower belly shows dark dried wounds; on the back two torn slits show dark red flesh. The mail covers the shoulder caps and ends in a short mail sleeve at the top of the arm. Arms below it bare, olive and yellow mottled. A black leather BELT with small studs and a round bronze boss buckle. Below the belt, a short torn hem of the same mail with dull blue-grey cloth tatters, tight on the hips. Trousers very dark brown, nearly black. Hair black.

Common: same head shape and face as the input, same five-finger hands, same bare feet with cloth bands, same pale bare shin bone on the figure's RIGHT leg. Even soft studio light, no shadows on the figure. Do NOT change the pose, add armour plates, a cape, weapons or sleeves past the shoulder; do not thicken the body.

Per-image checks: same pose and silhouette as the matching input view; hard alpha edge; the shin bone on the figure's RIGHT leg; hands and feet in frame.
