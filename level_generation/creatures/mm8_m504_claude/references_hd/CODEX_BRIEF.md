# Codex brief: HD modelling references for the Earth Elemental (MM7 m198 / MM8 m504)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm8_m504_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references_hd/native_views.png` — ORIGINAL native sprite standing views, enlarged 3x with nearest neighbour, left
   to right: front, front three-quarter, its right profile (facing image right), rear three-quarter, back. Magenta is
   background, not creature. Design, anatomy, proportions and colour authority.
2. `references_hd/native_palettes.png` — the front view in the three tier palettes (brown, blue-slate, red). Generate
   the LEFT, BROWN version.
3. `references_hd/native_actions.png` — native attack frames (front) and walk/fidget frames: arms, fists and legs in
   motion. Anatomy evidence only.
4. `level_generation/creatures/mm7_m198/aligned_2x/m198sa1.png` — restored 2x three-quarter frame, SURFACE MATERIAL
   ONLY (the cracked stone). Never sets the design.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five images in `references_hd/`, one creature each, full body from the top of the head to the soles, unresized
returns, 1024x1536 PORTRAIT, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, body turned about 35° (we see its front and its right side), camera at chest height slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | its LEFT side: it faces image LEFT, its left shoulder nearest the camera |
| `04_right.png` | its RIGHT side: it faces image RIGHT, its right shoulder nearest the camera |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (a separate invocation): generate 01–04 with the selected 00 as an input so all five show the same creature,
pose and proportions. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT — MM7/MM8 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING
Might and Magic Earth Elemental from the supplied original sprites, as a 3D modelling reference. Not a new design.
Use case: faithful 3D character modelling reference sheet view. Near-orthographic camera, even soft neutral studio
light (no dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), semi-realistic
game materials, sharp fine detail, a credible fully three-dimensional figure.

Identity (from the native sprite): a huge, heavy humanoid made entirely of living ROCK. Its whole surface is built of
irregular interlocking flat stone plates and pebbles of warm BROWN / umber earth stone with lighter tan edges,
separated by dark deep cracks, like dry cracked earth or a dry-stone wall; no skin, no clothing, no moss, no glow.
Proportions: a small blocky HEAD with a FLAT TOP that sits low and forward between massive shoulders (almost no
neck), a heavy brow ridge, deep-set dark eye hollows and a rough craggy face without a visible mouth opening; very
broad, rounded boulder-like SHOULDERS and a deep barrel CHEST, a narrower waist; long thick ARMS ending in oversized
heavy stone FISTS (each fist about the size of the head); thick column-like LEGS that widen toward the bottom and end
in broad, flat, rounded stone FEET like boulders. Stocky and heavy, about 5 heads tall.

Pose (identical in all five views, a neutral rigging pose): A-pose, arms straight down and away from the body about
35° from vertical so there is clear air between the arms and the torso, elbows almost straight; hands are big
CLOSED FISTS (four thick fingers curled and a thumb), knuckles pointing down and slightly forward. Legs straight,
feet apart with a clear gap between the thighs and between the feet, soles flat. Head level, looking forward.

Do NOT: add armour, weapons, crystals, glowing eyes, lava, moss, grass, extra limbs, a tail or horns; change the
colour (no grey granite, no blue, no red); make it slim or human-like with skin; open the hands; crop the head, fists
or feet; draw a floor, shadow or background.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins; brown cracked-stone surface of interlocking plates everywhere; small
flat-topped head low between huge shoulders; two big closed fists; thick legs with broad flat boulder feet; A-pose
with air between arms and body and between the legs; transparent background; for 01–04 the same figure, pose and
proportions as the primary; side views: in `03_left` its face points to image LEFT, in `04_right` to image RIGHT.
Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). After run 2, a contact sheet `references_hd/selected_views_review.png`
with the five selected views side by side.

## Run 2 addition: head turnaround (in `references_head/`)

Also in run 2, after 01–04: a bust-only head turnaround in `level_generation/creatures/mm8_m504_claude/references_head/`
(write there too), generated from the selected body masters (00 as input), 1254x1254 (or the closest square size),
transparent background, the same head as the body masters: the head, the stub of neck and the top of the massive
shoulders only, cut below the shoulders. Files: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (its right
side, face toward image right), `03_back.png`. Same brown cracked-stone plates, heavy brow ridge, deep dark eye hollows,
craggy face without an open mouth, flat-topped skull. Record them in `references_head/generation_runs.json` and a
`references_head/selected_views_review.png` contact sheet.
