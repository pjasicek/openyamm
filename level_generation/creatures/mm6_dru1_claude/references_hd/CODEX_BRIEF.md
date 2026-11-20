# Codex brief (run 3): four HD front/back/side views for the MM6 Druidess (dru1)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_dru1_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED (run `dru1_three_quarter_v3_alphaclean` in
`generation_runs.json`). Do not regenerate or re-judge it. Append the new runs to `generation_runs.json` (same record
format), keep raw returns under `raw/` (`dru1_front_v1.png`, ...), and at the end write `selected_views_review.png`
(all five selected views side by side).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm6_dru1_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same woman, face, hair, hood, cloak, studded bodysuit, belt and medallion, choker, armbands, bracers, boots,
   colours, pose, proportions, light and render style.
2. `mm6_dru1/references/standing.png` — ORIGINAL native five-view sheet (magenta background). Use it for what each
   view shows (the closed back of the cloak and the hood from behind).
3. `mm6_dru1/native/dru1sta2.png` — ORIGINAL native profile frame (how the cloak hangs at the side).

## Deliverables (1024 x 1536 portrait, true transparent background with no translucent haze, unresized returns)

Camera conventions (she faces the viewer in `01_front`; "her left" means her own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of her | face in the hood, bodysuit, belt; her RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight behind her | the back of the hood and the closed back of the cloak down to above the ankles, boots below; her RIGHT arm on IMAGE RIGHT, both arms and hands visible out at the sides |
| `03_left.png` | at her LEFT side, pure 90-degree profile | she faces IMAGE LEFT; her LEFT arm and leg nearest the camera |
| `04_right.png` | at her RIGHT side, pure 90-degree profile | she faces IMAGE RIGHT; her RIGHT arm and leg nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks; for a failed
view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual fault.

## Prompt content (adapt per view)

TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VI Druidess), as a 3D modelling reference. Not a new
design. ONE complete figure, hood top to boot soles, centred, generous margins, near-orthographic camera at chest
height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio light, same render
style and materials as input 1.

Identity (as in input 1): a slim athletic adult woman, pale skin, long wavy dark brown hair falling inside the hood
over the front of the shoulders; a deep forest-green hood (up) joined to a full-length forest-green cloak hanging from
the shoulders to just above the ankles, open at the front, hanging BEHIND the arms, closed all round the back; a
sleeveless dark brown studded-scale leather bodysuit with a V neckline and high-cut legs; a wide reddish-brown belt
with gold edging, a large round gold spiral medallion at the centre front and a smaller gold disc at each side; a thin
gold choker; an engraved gold armband on each upper arm; reddish-brown leather bracers with gold rims on the
forearms; reddish-brown knee boots with turned-down cuffs edged in small gold studs. Neutral, modest documentation-style
turnaround presentation.

If the image tool refuses a view, retry that view ONCE with the neckline described as "a V neckline filled with a thin
dark brown leather underlayer", and note the deviation in the run's reason.

Pose (identical in all views, as in input 1): neutral A-pose, standing upright, legs straight and slightly apart with
a clear gap between the legs and boots, feet flat. Arms hang down and out to the sides at about 40 degrees from
vertical, elbows very slightly bent, both hands relaxed and open with five fingers, palms facing inward, with clear
background between each arm and the torso and between each hand and the cloak. Head level, looking forward, hood up.

Do NOT: add a held object, staff, weapon or spell effect; add a clasp, trim, embroidery or lining colour to the cloak;
close the cloak at the front or let it cover the arms or hands; change any colour; change the pose; crop the hood, the
cloak hem or the boots; add a floor, shadow or text.

Checks per view:
- the camera matches the table (side and facing direction); pure front/back/profile, not three-quarter;
- same character, proportions, pose and colours as input 1;
- whole figure inside the frame with margins, true transparent background with no haze, 1024 x 1536;
- empty open hands with five fingers wherever visible;
- in profile, the arm nearest the camera hangs clear of the torso, the cloak hangs behind it.
