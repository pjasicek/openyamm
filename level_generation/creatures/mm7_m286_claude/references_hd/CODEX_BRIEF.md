# Codex brief v2: HD modelling references for the MM7 Minotaur (m286), native proportions

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m286_claude/references_hd/` and
`level_generation/creatures/mm7_m286_claude/references_head/`. Do not edit any other file, do not run builds, do not
call Meshy. Use your built-in image generation tool. Do not read or reuse `references_hd_v1/` or `references_head_v1/`:
those masters were REJECTED because their body proportions drifted from the original (a lean, long-legged bodybuilder).

## Why this run exists

The user rejected the first model: "too narrow torso, too big legs, not anatomically according to the original". The
original MM7 Minotaur is a HULKING BRUTE, not a lean athlete: enormous shoulders and chest (shoulder width about TWICE
the waist), massive arms, the bull head sitting LOW between the shoulders on huge trapezius muscles with almost no
visible neck, a big barrel torso, and comparatively SHORT legs. The proportions below were measured on the original
sprite and are the main acceptance criterion of this run.

## Inputs (attached in this order)

1. `references_hd/guide_front.png` — PROPORTION AUTHORITY, front. The restored native front standing frame scaled onto
   the 1024x1536 master canvas (hoof soles at y=1450, skull top at y=350), with the measured landmark rows (yellow) and
   widths (cyan bars) drawn over it. Magenta lines are the A-pose arm axes the masters must use. The grey background,
   lines and text are annotations, not part of the creature.
2. `references_hd/guide_side.png` — PROPORTION AUTHORITY, profile (his right side, facing image right), same scale.
3. `references_native/standing_287_sheet.png` — ORIGINAL native MM7 standing sprite, five stored views left to right:
   front, front three-quarter, his right profile, rear three-quarter, back. Magenta is background. Design, anatomy and
   colour authority.
4. `references_native/tiers.png` — the front sprite in the three tier palettes. Only the loincloth and wrist bands
   recolour; generate the OLIVE-GREEN version.
5. `../mm7_m286/aligned_2x/m286sa0.png` — restored 2x front standing frame: proportions and surface material.
6. `../mm7_m286/aligned_2x/m286sa2.png` — restored 2x profile standing frame: proportions and surface material.
7. (run 2 only) the selected `references_hd/01_front.png` and `references_hd/00_three_quarter.png`.

## Measured native proportions (H = hoof sole to skull top between the horn roots, horns excluded)

Heights above the hoof soles: horn tips 1.19 H; skull top 1.00 H; eyes 0.92 H; chin 0.82 H; shoulder line (top of the
deltoids) 0.78 H; armpit 0.68 H; waist 0.58 H; belt 0.54 H; kilt hem 0.35 H; legs visibly separate below the kilt at
0.31 H; goat knee (most forward, profile) 0.25 H; hock (most backward, profile) 0.15 H.

Widths (front view): shoulders across the deltoids 0.43 H; chest at the armpits 0.27 H; waist 0.22 H; belt 0.20 H;
fur kilt at the hips 0.28 H; both thighs together 0.33 H; one thigh 0.15 H; one shin 0.08 H; one hoof 0.11 H; one
upper arm 0.11 H; forearm with the wrist band 0.10 H; head without the ears 0.16 H; ear tip to ear tip 0.29 H; horn
span 0.39 H. Profile: chest depth (sternum to the back skin under the mane) 0.22 H; head length (back of the skull to
the snout tip) 0.23 H.

So: head (skull top to chin) 0.18 H, the chin only 0.04 H above the shoulder line (no neck; the trapezius rises
straight from the shoulders to the jaw and the back of the skull), the torso from the shoulder line to the crotch
0.47 H, the legs only about 0.31–0.35 H to the crotch.

In pixels on the 1024x1536 canvas of `01_front.png` (place him exactly like guide_front.png): hoof soles y=1450, skull
top y=350, horn tips y≈142, chin y≈549, shoulder line y≈588, armpits y≈700, waist y≈814, kilt hem y≈1070, legs separate
y≈1109; shoulders ≈475 px wide, chest ≈295, waist ≈241, kilt ≈310, both thighs ≈368, one thigh ≈163, one shin ≈84,
upper arm ≈121 px thick, forearm with band ≈112, head without ears ≈175.

## Deliverables

Body masters in `references_hd/`, each one creature, full body from the horn tips to the hooves, unresized returns,
1024x1536 portrait, true transparent background, no floor, no shadow, no text, no guide lines:

| File | View | Run |
|---|---|---|
| `01_front.png` | front, placed and proportioned exactly like guide_front.png | 1 (generate FIRST) |
| `00_three_quarter.png` | front three-quarter, body turned about 35° (we see his front and his LEFT side, which is on image right), camera at chest height slightly above, same proportions and pose as 01_front | 1 (with 01_front as an extra input) |
| `02_back.png` | back | 2 |
| `03_left.png` | his LEFT side: he faces image LEFT, his left shoulder nearest the camera | 2 |
| `04_right.png` | his RIGHT side: he faces image RIGHT, his right shoulder nearest the camera; must match guide_side.png's heights | 2 |

Head turnaround in `references_head/` (run 2), bust only (horns, head, mane, the top of the huge trapezius and
shoulders), 1254x1254 (or the closest square size), transparent background, the same head, horns, nose ring and mane
as the body masters, mouth closed: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (his right side, face
toward image right), `03_back.png`.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII Minotaur from the supplied original sprites, as a 3D modelling reference. Not a new design. Use case:
faithful 3D character modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), semi-realistic game
materials, sharp fine detail, a credible fully three-dimensional figure.

BODY PROPORTIONS — the first priority. A hulking, top-heavy brute built like the original sprite and the guide images:
enormously broad rounded shoulders and deltoids (0.43 H across, about twice the 0.22 H waist), a deep barrel chest
and big pectorals, a V-shaped torso tapering hard to a comparatively narrow waist and belt, very thick upper arms and
forearms, massive trapezius muscles that rise from the shoulders up to the jaw so the bull head sits LOW and forward
between the shoulders with no visible neck (the chin is barely above the shoulder line). The legs are comparatively
SHORT and sturdy: the fur kilt ends at 0.35 H, the crotch is about a third of the height, the shaggy fur thighs are
thick but NOT wider than the kilt, the legs nearly straight and parallel in the front view with the hooves under the
hips (no bow legs, no wide stance), the shins slimmer. Upper body big, legs short: if in doubt, make the torso and
arms bigger and the legs shorter, never the reverse.

Identity (from the native sprite): bull-headed humanoid with short grey-brown skin/hide on the torso and arms
(defined pecs and abdominal muscles, not furry on the chest). Bull head: dark brown short-haired bovine head with a
broad muzzle, a black nose with a GOLD nose ring, glowing RED eyes, small bovine ears sticking out sideways, and
exactly TWO very large smooth pale ivory-grey horns that sweep sideways from the top of the skull and curve UPWARD,
ending in dark RED tips (horn tips at 1.19 H, horn span 0.39 H). A shaggy dark-brown mane runs from the back of the head
down the neck and the upper back (it lies on the body; it is not a cape). Hands are human, large, with four fingers
and a thumb, dark grey-brown, short dark nails. Goat (satyr) legs: from the hips down long shaggy dark-brown fur;
in the profile the knee bends slightly forward at 0.25 H and a backward-bent hock sits at 0.15 H (a moderate zig-zag
as in guide_side.png, not a long stilt-like lower leg); a black cloven HOOF on each foot; NO human feet, NO boots. A
short kilt of shaggy OLIVE-GREEN fur with a ragged hem around the hips, held by a narrow gold belt with small blue
and gold square beads. On each forearm a wide OLIVE-GREEN padded wrist band with gold rims and three or four short
pointed silver spikes. No other clothing, no harness, no armour, no tail.

Pose (identical in all five body views): A-pose, arms straight and away from the body about 33° from vertical along
the magenta axes of guide_front.png, elbows almost straight, hands open with the five fingers separated and slightly
spread, palms facing the thighs, the whole hand clear of the body and the kilt, EMPTY HANDS (no axe). Legs straight
and parallel with their natural goat-leg knee and hock, hooves flat on an imaginary floor under the hips, a clear gap
between the legs below the kilt. Head level, looking forward. Horns fully inside the frame.

Do NOT: make him lean, slim-waisted with long legs, or a bodybuilder on stilts; give him a visible long neck; make
the legs longer, wider or bulkier than in the guides; spread or bow the legs; add a cape, armour, a harness, a
weapon, a tail, human feet or boots; change the colours (grey-brown skin, dark-brown fur legs and mane, olive-green
fur kilt and wrist bands, gold belt with blue beads, gold nose ring, ivory horns with red tips, red eyes, black
hooves); crop the horns, hands or hooves; draw a floor, shadow, background, guide lines or text.

## Per-image checks (re-run before you select a view)

Overlay the front (and the right profile) on its guide at the canvas positions above: the skull top, chin, shoulder
line, armpits, waist, kilt hem and soles within about ±25 px of the guide rows, and the shoulder, chest, waist, kilt
and thigh widths within about ±10 % of the cyan bars. Five fingers per hand, separated, clear of the body; exactly two
horns with red tips; gold nose ring; red eyes; mane on the neck and back; goat legs with black cloven hooves; olive-green
fur kilt; gold beaded belt; green spiked wrist bands on BOTH forearms; empty hands; A-pose; true transparent
background; side views: in `03_left` his face points to image left, in `04_right` to image right; for 00 and 02–04 the
same minotaur, pose and proportions as 01_front. Stop after one corrective regeneration per view and record what
remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Same for `references_head/generation_runs.json`. A contact sheet
`references_hd/selected_views_review.png` with the selected body views side by side (run 2).

## Runs

Run 1: `01_front.png` first (from inputs 1–6), then `00_three_quarter.png` (inputs 1–6 plus your selected
01_front.png), then stop. Run 2 (after both are accepted): `02_back.png`, `03_left.png`, `04_right.png` and the four
head views, with the selected 01_front and 00_three_quarter as extra inputs.
