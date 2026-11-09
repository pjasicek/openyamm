# Codex brief (run 2): four HD side/front/back views for the MM6 Thief (thf)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_thf_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `thf_three_quarter_v1` in
`generation_runs.json`; earlier run brief: `CODEX_BRIEF_v1_primary.md`). Do not regenerate or re-judge it. Append the
new runs to the existing `generation_runs.json` (same record format), and at the end write
`selected_views_review.png` (all five selected views side by side).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm6_thf_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same man, face, hood, mantle, cloak, clothes, colours, pose, proportions, light and render style.
2. `mm6_thf/references/standing.png` — ORIGINAL native five-view sheet (front, front three-quarter, profile, rear
   three-quarter, back); magenta is background. Use it for what each view shows (how the cloak covers the side and
   the back).
3. `mm6_thf/native/thfstaa2.png` — ORIGINAL native profile frame.

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (the thief faces the viewer in `01_front`; "his left" means the thief's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of him | pouch on IMAGE LEFT (his right hip), sheathed dagger on IMAGE RIGHT (his left hip) |
| `02_back.png` | straight behind him | the closed cloak back and hood back; any visible hand/boot on his right is on IMAGE RIGHT |
| `03_left.png` | at his LEFT side, pure 90-degree profile | he faces IMAGE LEFT; his LEFT hip (sheath side) is nearest the camera |
| `04_right.png` | at his RIGHT side, pure 90-degree profile | he faces IMAGE RIGHT; his RIGHT hip (pouch side) is nearest the camera |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason. Do not chase minor differences in fold detail.

## Prompt content (adapt per view)

TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same character as input 1
(a faithful HD reconstruction of the existing Might and Magic VI Thief), as a 3D modelling reference. Not a new
design. ONE complete figure, hood tip to boot soles, centred, generous margins, near-orthographic camera at chest
height, transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio light, same render
style and materials as input 1. Plain wool weave with irregular dark worn blotches, NO woven or embossed patterns.

Identity (from the native sprites): a slim, narrow-shouldered adult human man of normal height (head about
one-seventh of body height), long thin face, pale skin, straight nose, narrow eyes, a thin drooping brown moustache
and short stubble on the chin, straight brown hair falling to the jaw at both sides of the face inside the hood.
- HOOD: a deep, soft, loose cloth hood in muted dark GREY-GREEN wool, up over the head and coming to a soft point at
  the back; the face is fully visible in the hood opening (forehead, eyes, nose, mouth, chin), hair framing it.
- SHOULDER MANTLE: the hood joins a short shoulder cape of the same green cloth that drapes over both shoulders and
  the upper arms and hangs to about mid-chest in front, with a soft irregular lower edge.
- CLOAK: a long, heavy, worn grey-green wool cloak hangs from the shoulders under the mantle to just above the ankles.
  It is OPEN AT THE FRONT (the front edges hang straight down at the outer sides of the body, about a hand's width
  outside each hip), wide like a bell at the bottom, and closed all round the back. Seen from the side it wraps
  round and covers the side of the body and the arm. The cloth has irregular dark worn/stained blotches (dark green,
  star-like smudges, as in the native back view), a frayed slightly ragged hem, plain weave; NO symbols, no trim,
  no embroidery, no clasp jewellery.
- UNDERSHIRT: a pale sea-green / jade long-sleeved shirt; the sleeves are visible below the mantle down to the wrists,
  and its hem shows below the jerkin at the hips.
- JERKIN: a fitted sleeveless BROWN leather jerkin from chest to hip, made of rectangular leather panels with many
  small round SILVER studs in rows and a lighter edge trim, slightly open down the centre front.
- A thin brown leather strap diagonally across the chest from the thief's LEFT shoulder down to the pouch at his RIGHT hip; a brown
  leather belt with a small brass buckle; a squarish brown leather POUCH hanging at the front of his RIGHT hip; a
  small sheathed dagger with a brass-capped hilt worn vertically at the front of his LEFT hip (sheathed, hilt up).
- Brown leather wrist bracers on both forearms (from the wrist about a third of the way to the elbow).
- Tight, slightly glossy BLACK / very dark navy trousers (leggings) on slim legs.
- Brown leather BOOTS to mid-calf with a turned-down cuff and a strap with small studs at the top, simple soles.
- Hands bare, pale skin.

Pose (identical in all five views): standing upright, relaxed, weight even, legs straight and slightly apart with a
clear gap of air between the legs from the crotch down and between the boots; feet flat, toes forward. Arms hang down
away from the body at about 20 degrees from vertical, elbows very slightly bent, the arms INSIDE the cloak (the cloak
falls OUTSIDE the arms, over the shoulders and down past the elbows), forearms and hands visible in front of the
open cloak, with a clear gap of air between each arm and the torso and between each hand and the thigh. BOTH HANDS
loosely CLOSED into a relaxed grip, as if each held a thin invisible dagger handle running front-to-back: fingers
curled, thumb resting along the index finger, palms facing the thighs, knuckles outward, wrists straight. Head level,
looking forward, hood up.

Do NOT: draw a dagger in the hands (no held weapon of any kind), a bow, a sword, a quiver or a backpack; add armour
plates, metal pauldrons, a mask or a scarf over the face; add a clasp, brooch, trim, embroidery or symbols to the
cloak; change colours (grey-green hood, mantle and cloak; jade undershirt; brown studded leather; black trousers;
brown boots); close the cloak at the front; let the cloak cover the hands; crop the hood, the cloak hem or the boots;
add a floor, shadow or text.

Checks per view:
- the camera matches the table (side and facing direction); same pose and proportions as input 1;
- whole figure inside the frame (hood tip, cloak hem, both boots), true transparent background, 1024 x 1536;
- same hood, short mantle, long cloak (open at the front, closed at the back, covering the sides in profile), plain
  wool with dark blotches, no clasp, trim or pattern;
- same jade sleeves, studded brown jerkin, strap, pouch at his RIGHT hip, sheath at his LEFT hip, bracers, black
  trousers, brown cuffed boots wherever the view can see them;
- both hands loosely closed and empty; no added weapon or equipment.
