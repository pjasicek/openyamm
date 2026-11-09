# Codex brief: HD reference views for the MM6 Thief (thf)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_thf_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation, with the prompt style and record format of
`level_generation/creatures/mm6_ttn1_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):

1. `mm6_thf/references/standing.png` — ORIGINAL native five-view standing sheet (front, front three-quarter, profile,
   rear three-quarter, back). Magenta is background, not character. Design, proportions and palette authority.
2. `mm6_thf/native/thfstaa0.png` — ORIGINAL native front frame (transparent background).
3. `mm6_thf/native/thfstaa1.png` — ORIGINAL native front three-quarter frame.
4. `mm6_thf/native/thfstaa2.png` — ORIGINAL native profile frame (shows how far the cloak wraps round the sides).
5. `mm6_thf/aligned_2x/thfstaa0.png` — restored 2x front view, for SURFACE MATERIAL ONLY (cloth weave, stud and
   leather detail, face). It never sets the design, pose or proportions.

## Deliverables (5 images, transparent background, 1024 x 1536 portrait, unresized returns)

| File | View |
|---|---|
| `00_three_quarter.png` | front-right three-quarter (camera 40–45° toward the thief's right), camera at chest height, slightly above; primary, generate first |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | the thief's own LEFT side (pure profile) |
| `04_right.png` | the thief's own RIGHT side (pure profile) |

Generate 01–04 with 00 as an additional input so all five are the SAME man, SAME cloak, SAME pose, SAME proportions.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs) and a `selected_views_review.png` contact sheet. Keep raw returns under `raw/`. Regenerate a view that fails
the checks below with one targeted correction (using 00 as input) and record the superseded run.

## Prompt content (adapt per view)

TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI Thief from the supplied original sprites, as a 3D modelling reference. Not a new design.
Use case: faithful 3D modelling reference. ONE complete figure, full body from the hood tip to the boot soles,
centred, generous margins, near-orthographic camera, transparent background, no floor, no shadow, no scenery, no
text. Even soft neutral studio light (no dramatic lighting, no rim light) that still shows form. Credible fully
three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

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

Checks per image (re-run before selecting a view):
- whole figure inside the frame: hood tip, cloak hem, both boots; true transparent background; 1024 x 1536;
- face visible in the hood with brown hair at both sides and the thin moustache;
- short mantle over the shoulders AND the long cloak to above the ankles, open at the front, closed at the back,
  covering the sides; dark blotches on the cloth; no clasp or trim;
- jade sleeves to the wrist and jade hem below the jerkin; brown studded jerkin; diagonal strap; pouch at his RIGHT
  hip; sheathed dagger at his LEFT hip; brown wrist bracers; black trousers; brown cuffed boots;
- both hands loosely closed, empty, with air between hand and thigh; gap between the legs;
- the same pose and proportions as the primary; in the side views the pouch is on the right side and the sheath on
  the left side, matching the front and back.
