# Codex brief: HD reference views for the MM6 Hydra (hyd)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_hyd_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation, with the prompt style and record format of
`level_generation/creatures/mm6_seas_claude/references_hd/generation_runs.json`. Attached inputs:
1. `level_generation/creatures/mm6_hyd/references/standing.png` — ORIGINAL native five-view sheet (magenta is
   background). Design/anatomy/palette authority.
2. `level_generation/creatures/mm6_hyd/references/attack.png` — ORIGINAL attack views (open mouths, teeth).
3. `level_generation/creatures/mm6_hyd/aligned_2x/hydstaa0.png` — restored 2x front view, surface material only.

## Deliverables (5 images, transparent background, 1536 x 1024 landscape, unresized returns)
- `00_three_quarter.png` — front-right three-quarter (primary; generate first)
- `01_front.png`, `02_back.png`, `03_left.png` (creature's left side), `04_right.png`
Generate 01–04 with 00 as an additional input so all five are the SAME creature, SAME pose, SAME proportions.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason) and a
`selected_views_review.png` contact sheet. Regenerate a view if it breaks the checks below; record superseded runs.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI Hydra from the supplied original sprites, as a 3D modelling reference. Not a new design.
Use case: faithful 3D modelling reference. ONE complete creature, centred, generous margins, near-orthographic
camera at mid height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio
light that still shows form. Credible fully three-dimensional sculpt, semi-realistic game materials, sharp detail.

Identity (from the native sprites): a five-headed serpent hydra. ONE thick serpent body: back and sides dark green
scales with a row of orange-brown diamond patches along the back, underside pale grey-white glossy horizontal belly
rings; the body tapers into a long tail ending in a ringed, banded tip. FIVE long necks, each the thickness of the
body's front part, pale ringed belly on their front, green scaly back; each ends in a DIFFERENT dragon-serpent head:
(1) purple head with two long ivory horns sweeping up and a third short horn on the snout; (2) dark green rounded
head; (3) dark red head with a tall spiky fin crest and frills; (4) dark blue head with short spiky crest; (5) olive
head, smaller, with a short crest. All heads: yellow or orange eyes, mouths slightly open showing small ivory fangs
and a dark red mouth.

Pose (identical in all five views): the body lies on the ground in ONE simple flat curve: a low U shape whose front
part is the base of the necks and whose tail extends straight back and slightly to the side, tail tip on the ground.
The FIVE necks rise from the front of the body like the fingers of an open hand: fanned out in a wide arc with CLEAR
GAPS between every neck at every height (necks never touch or cross), outer necks leaning outward, middle neck
tallest; the necks curve forward at the top so all five heads face forward and slightly down, at different heights
(middle highest, outer lowest). No coils over the necks, nothing hidden behind another part in the front view.

Do NOT: add legs, wings, arms, extra heads, a sixth neck, water, splashes, glowing effects or blood; do not let necks
touch, cross, twist round each other or merge; do not change colours (green body with orange diamonds, pale belly
rings, the five head colours above, ivory horns and fangs).

Checks per image: exactly five heads and five separate necks with visible gaps; each head's distinct colour and
crest; whole tail with ringed tip inside the frame; pale belly rings on the neck fronts; transparent background; same
pose and proportions as the primary.
