# Codex brief: HD modelling references for the MM7 Blaster Guy (m475: Tolberti, Robert the Wise)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m475_claude/references_hd/` and
`level_generation/creatures/mm7_m475_claude/references_head/`. Do not edit any other file, do not run builds, do not
call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references_hd/native_views.png` — ORIGINAL native MM7 sprite standing views, enlarged 3x with nearest neighbour,
   left to right: front, front three-quarter, his right profile (facing image right), rear three-quarter, back.
   Magenta is background, not character. Design, anatomy, proportions and colour authority (one palette, 527).
2. `references_hd/native_actions.png` — native attack (he aims the blaster pistol forward and fires), hit and fidget
   frames: the pistol's shape, the cape in motion. Anatomy and prop evidence only.
3. `level_generation/creatures/mm7_m475/aligned_2x/m475sa1.png` — restored 2x three-quarter frame, SURFACE MATERIAL
   ONLY. Never sets the design.
4. (second and third runs only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Body masters in `references_hd/`, one man each, full body from the collar tips to the boot soles, unresized returns,
1024x1536 PORTRAIT, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, body turned about 35° (we see his front and his right side), camera at chest height slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | his LEFT side: he faces image LEFT, his left shoulder nearest the camera |
| `04_right.png` | his RIGHT side: he faces image RIGHT, his right shoulder nearest the camera |

Prop reference in `references_hd/`: `blaster.png`, 1536x1024 LANDSCAPE, transparent background: the blaster pistol
ALONE, seen exactly from its side (muzzle to image RIGHT, grip down), the whole gun inside the frame with margins, no
hand, no muzzle flash.

Head turnaround in `references_head/`, bust only (head, hair, beard, the stand-up collar, neck and top of the
shoulders), 1254x1254 (or the closest square size), transparent background, the same face as the body masters,
neutral expression, mouth closed: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (his right side, face
toward image right), `03_back.png`.

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): 01–04 and `blaster.png` with the selected 00 as an input. Run 3: the head turnaround.
At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII "blaster guy" character (the NPCs Tolberti and Robert the Wise) from the supplied original sprites, as a 3D
modelling reference. Not a new design. Use case: faithful 3D character modelling reference sheet view.
Near-orthographic camera, even soft neutral studio light (no dramatic lighting, no rim light, no strong shadows: the
light is baked into the texture), semi-realistic game materials, sharp fine detail, a credible fully
three-dimensional figure.

Identity (from the native sprite): a stern man in his forties, average athletic build, shoulder-length wavy BROWN hair
parted in the middle, a short full brown BEARD and moustache, heavy brows. A long BLACK CAPE hangs from his shoulders
to just above the ankles, open at the front, with a very TALL STIFF STAND-UP COLLAR rising behind his head in two
pointed wings (like a vampire collar), black outside. Clothing: a black shirt with full, PUFFED, gathered black
sleeves ending in tight cuffs at the wrists; over it a sleeveless deep PURPLE / violet vest reaching the hips, with two
broad WHITE bands running from padded white shoulder rolls down to a V at the belly (white padded epaulettes on both
shoulders); a broad black leather BELT with rows of small gold studs and round rivets; slightly baggy black trousers
tucked into tall black leather riding BOOTS reaching the knees, with a thin silver band below the knee and at the
ankle; black shoes with a silver buckle.

Pose (identical in all five body views): A-pose, arms straight down and away from the body about 40° from vertical so
there is clear air between the hands and the cape, elbows almost straight. His RIGHT hand is a loose FIST with the
fingers curled around an EMPTY space as if holding a pistol grip, knuckles pointing forward-down; his LEFT hand open
and relaxed with the fingers together. EMPTY HANDS: the pistol is a separate prop, do not draw it. Legs straight,
feet shoulder-width apart, soles flat. The cape hangs straight down behind him and to his sides, not wrapped around
the arms. Head level, looking forward.

Blaster (`blaster.png` only): a fantasy-sci-fi energy pistol from the native frames: a long dark steel-grey barrel
with ribbed bands and a flared muzzle, a rounded body with brass/silver fittings, a curved wooden-brown or dark grip,
a trigger guard; about 30 cm long at this man's scale.

Do NOT: add a hat, a sword, armour plates, a second weapon or the pistol in his hand; change the colours (black cape,
shirt, trousers and boots; purple vest with white bands; brown hair and beard); make the collar small or soft; crop
the collar tips, hands or boots; draw a floor, shadow or background.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins; tall two-pointed stand-up collar behind the head; black cape to the
ankles; purple vest with white V-bands and white padded shoulders; studded belt; puffed black sleeves; knee boots with
silver bands; brown hair and beard; right hand an empty loose fist, left hand open; arms out about 40° with air
between hands and cape; transparent background; for 01–04 the same man, pose and proportions as the primary; side
views: in `03_left` his face points to image LEFT, in `04_right` to image RIGHT. Stop after one corrective
regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json` and `references_head/generation_runs.json`: one entry per generation (id, view,
prompt, input paths with sha256, output path, selected flag, reason, superseded runs). Contact sheets
`references_hd/selected_views_review.png` (five body views and the blaster) and
`references_head/selected_views_review.png`.
