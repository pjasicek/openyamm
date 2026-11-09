# Codex brief: HD modelling references for the MM7 Peasant Dwarf Female (m312)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m312_claude/references_hd/` and
`level_generation/creatures/mm7_m312_claude/references_head/`. Do not edit any other file, do not run builds, do not
call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references_native/standing.png` — ORIGINAL native MM7 standing sprite, five stored views left to right, top row
   then bottom row: front, front three-quarter, her right profile, rear three-quarter, back. Native palette 313 (purple
   dress, blonde hair). The magenta/grey background is not part of the creature. Design, anatomy, proportions and
   colour authority.
2. `references_native/fidget.png` — native fidget frames (front): her hands, apron and the scissors seen from the front.
3. `references_native/tiers.png` — the front sprite in all nine palettes. Only the dress cloth and the hair change
   colour; generate the PURPLE dress / BLONDE hair version (palette 313, first image).
4. `../mm7_m312/aligned_2x/m312sa0.png` — restored 2x frame, SURFACE MATERIAL ONLY. Never sets the design.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Body masters in `references_hd/`, each one creature, full body from the top of the hair bun to the shoe soles, unresized returns,
1024x1536 portrait, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, body turned about 35° (we see her front and one side), camera at chest height slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | her LEFT side: she faces image LEFT, her left shoulder nearest the camera |
| `04_right.png` | her RIGHT side: she faces image RIGHT, her right shoulder nearest the camera |

No prop reference: she carries nothing in her hands.

Head turnaround in `references_head/`, bust only (hair bun, face, curls, earrings, neck and top of the shoulders), 1254x1254 (or the
closest square size), transparent background, same face and hair as the body masters, neutral expression, mouth
closed: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (his right side, face toward image right),
`03_back.png`.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII peasant dwarf woman (a female dwarf villager) from the supplied original sprites, as a 3D modelling reference.
Not a new design. Use case: faithful 3D character modelling reference sheet view. Near-orthographic camera, even soft
neutral studio light (no dramatic lighting, no rim light, no strong shadows: the light is baked into the texture),
semi-realistic game materials, sharp fine detail, a credible fully three-dimensional figure.

Identity (from the native sprite): an adult female dwarf villager, short, broad and sturdy, matronly, wide hips and a
full bust, thick arms, about 4 heads tall. Fair rosy skin, round cheeks, small nose, red lips, small earrings. Pale
golden-blonde hair pulled up into a round bun on top of the head, with a few ringlet curls hanging beside the ears.
A long purple dress reaching the ankles: a purple laced bodice (black criss-cross lacing at the front and at the back),
a square neckline with a white chemise edge showing, puffed long sleeves of white cloth with purple vertical stripes,
gathered at the wrists with a small white ruffle. A white apron from the waist to just above the purple hem, worn and
stained with small purple patches, with a square front pocket; its white waistband ties in a big bow at the back
with hanging tails. A small pair of black scissors hangs at the front of the waistband on her left. Plain brown
shoes peek out under the hem.

Pose (identical in all five body views): A-pose, arms straight down and away from the body about 35° from vertical,
elbows almost straight, hands open with the five fingers separated and slightly spread, palms facing the body, EMPTY
HANDS. Standing straight, feet shoulder-width apart under the dress, the hem just above the ankles so both shoes are
visible, soles flat. Head level, looking forward.

Do NOT: add a hat, shawl, cape, basket, tool or anything in the hands; shorten the dress; change the colours (purple
dress and bodice, white-and-purple striped sleeves, white stained apron, blonde hair, brown shoes); make her tall or
slim; crop the bun, hands or shoes; draw a floor, shadow or background.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins; five fingers per hand, separated; blonde bun with side curls; purple laced
bodice; striped puffed sleeves; white stained apron with pocket and back bow; ankle-length purple dress with both
shoes visible; scissors at the waist on her left; stocky dwarf proportions; empty hands; A-pose; transparent
background; for 01–04 the same woman, pose and proportions as the primary; side views: in `03_left` her face points
to image left, in `04_right` to image right.
Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Same for `references_head/generation_runs.json`. A contact sheet
`references_hd/selected_views_review.png` with the five selected body views side by side.

## Runs

Run 1: `00_three_quarter.png` only, then stop. Run 2 (after the primary is accepted): `01`–`04` and the
four head views, with the selected primary as an extra input.
