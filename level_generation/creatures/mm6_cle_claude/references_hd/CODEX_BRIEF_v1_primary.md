# Codex brief (run 1): HD primary three-quarter view for the MM6 Cleric (cle)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_cle_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. The other four views are a separate later run.

Use your built-in image generation, with the prompt style and record format of
`level_generation/creatures/mm6_thf_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):

1. `mm6_cle/references/standing.png` — ORIGINAL native five-view standing sheet (front, front three-quarter, profile,
   rear three-quarter, back). Magenta is background, not character. Design, proportions and palette authority.
2. `mm6_cle/native/clesta0.png` — ORIGINAL native front frame (transparent background).
3. `mm6_cle/native/clesta1.png` — ORIGINAL native front three-quarter frame.
4. `mm6_cle/native/clesta2.png` — ORIGINAL native profile frame (shows how the cloak covers the side and back).
5. `mm6_cle/aligned_2x/clesta0.png` — restored 2x front view, SURFACE MATERIAL ONLY (cloth, gold, face). It never
   sets the design, pose or proportions.

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, genuine transparent background, unresized native return. Keep raw
returns under `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs).

Accept the first image that passes the checks below. For a failed image do at most ONE targeted corrective
regeneration, then select the better of the two and note any residual fault in its reason. Do not chase minor
differences in fold detail. Stop after that.

## Prompt content

TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI Cleric of Baa from the supplied original sprites, as a 3D modelling reference. Not a new design.
Output: exactly ONE 1024 x 1536 portrait PNG, genuine transparent background. ONE complete figure, full body from the
top of the hair to the boot soles, centred, the figure about 80% of the canvas height with about 140 px of
transparent space above and below, generous side margins. Near-orthographic camera, no floor, no shadow, no scenery,
no text. Even soft neutral studio light (no dramatic or rim light) that still shows form. Credible fully
three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

Identity (from the native sprites):
- An adult fair-skinned human man of normal, slightly slim build (head about one-seventh of body height); a
  clean-shaven, narrow, long face with a straight nose and a calm, plain expression; light brown / dark-blond hair,
  slightly wavy, parted in the middle, falling to the jaw and the nape (no beard, no moustache).
- HIGH COLLAR AND SHOULDER MANTLE: a pale SILVER-GREY stand-up collar close round the neck, joined to a short round
  shoulder mantle (yoke cape) of the same pale grey cloth that covers both shoulders and the tops of the upper arms
  and ends at mid-chest in front in a gently curved lower edge, with a thin dark navy piping along its edge. On the
  front of the mantle, centred on the upper chest, a small DARK NAVY emblem: an ankh-like symbol (a small ring on top
  of two short horizontal bars over a short vertical stem), about the size of a palm, flat appliqué.
- CLOAK: a long PALE GREY cloak hangs from under the mantle at the shoulders down to the ankles. It is OPEN AT THE
  FRONT: its front edges hang straight down behind and outside the arms, about a hand's width outside each hip, and
  it is closed all round the back; seen from the side it covers the side of the body. The outside is pale silver-grey
  smooth wool with soft broad folds; the inside of the cloak is the same grey cloth in shadow. Plain cloth, no
  symbols, no trim, no clasp.
- TUNIC: a medium BLUE (cornflower to royal blue) long-sleeved tunic, fitted at the chest, falling loosely to just
  below the knees with an uneven, slightly asymmetric draped hem (longer at the centre front); the sleeves are long
  and slightly loose down to the wrists.
- BELT: a tan / ochre leather belt at the waist with a golden buckle and a long belt tongue hanging straight down at
  the centre front to about mid-thigh.
- GOLD CUFFS: a broad, plain polished gold band round each wrist at the end of the sleeve.
- Dark NAVY trousers on slim legs (visible below the tunic hem) and soft dark navy-blue boots to mid-calf, simple
  soles, no buckles.
- Hands bare, fair skin.

Pose (the pose for every later view as well): standing upright, relaxed, weight even, legs straight and slightly apart
with a clear gap of air between the legs below the tunic hem and between the boots; feet flat, toes forward. Arms
hang down and away from the body at about 25 degrees from vertical, elbows very slightly bent, the arms IN FRONT of
the open cloak (the mantle covers the shoulders; the cloak hangs behind the arms), with a clear gap of air between
each arm and the torso and between each hand and the thigh. His LEFT hand is CLOSED in a firm fist as if gripping an
invisible upright pole (staff) held vertically at his side: fingers wrapped round, thumb over the index finger, the
grip opening running straight up and down through the fist. His RIGHT hand is loosely CLOSED and relaxed, fingers
curled, thumb along the index finger. Palms toward the thighs, wrists straight. Head level, looking forward.

Do NOT: draw the staff or any held object (the hands are empty); add a hood, a beard, armour, jewellery other than the
two gold wrist cuffs, a necklace, a pendant, embroidery or extra symbols; put a clasp or trim on the cloak; change the
colours (pale grey collar, mantle and cloak; blue tunic; tan belt; gold cuffs; navy trousers and boots; navy emblem);
close the cloak at the front; let the cloak cover the arms or hands; crop the hair, the cloak hem or the boots; add a
floor, shadow or text.

INPUT ROLES (put these in the prompt):
- Input 1: ORIGINAL native five-view standing sheet, design/proportions/palette authority. Magenta is only background.
- Inputs 2–4: ORIGINAL native front, front three-quarter and profile frames, anatomy, costume placement and cloak
  drape authority. Their transparent or cyan background is not part of the character. The staff in them is NOT to
  be drawn.
- Input 5: restored 2x front view, SURFACE MATERIAL ONLY (cloth, gold, face), never design/pose/proportions
  authority. Ignore edge artefacts and the black background.
- Reconstruct the native design in the requested neutral standing pose with empty closed hands, not the original
  outstretched staff arm.

Camera for this PRIMARY view: FRONT-RIGHT THREE-QUARTER, camera 40–45 degrees toward the cleric's anatomical RIGHT
from straight front, at chest height and slightly above, near-orthographic with only a subtle downward view. It shows
the FRONT and his RIGHT flank: his nose and toes point diagonally toward SCREEN-LEFT; his right arm is the nearer arm
(on the image left), his left (fist) arm is farther. Head aligned with the torso, no separate head turn.

## Checks (re-run before selecting)

- camera: front-right three-quarter, nose and toes toward screen-left, right arm nearer;
- whole figure inside the frame (hair, cloak hem, both boots), true transparent alpha, 1024 x 1536;
- clean-shaven narrow face, jaw-length light brown hair, no hood;
- grey stand collar + short round grey mantle with dark piping and the small navy ankh-like emblem on the chest;
- long grey cloak open at the front, behind the arms, reaching the ankles;
- blue knee-length tunic with long sleeves, tan belt with hanging tongue, gold wrist cuffs, navy trousers and boots;
- left hand a firm fist with a vertical grip opening, right hand loosely closed, both empty; arms clear of the body;
- no staff, weapon, hood, beard, extra jewellery or added pattern.
