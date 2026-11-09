# Codex brief: HD reference views for the MM9 mummies (mm9_mummy_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_mummy_claude/references_hd/` (and `references_head/` for
run 4). Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skins, shown in renders made from that model.
The monsters are three grades of one body: Canopic Mummy (tier A), Embalmed Mummy (tier B), Petrified Mummy (tier C).

## Inputs
Attached per run (see Runs). In each `mm9_views_t<N>.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right:
front three-quarter, front, side facing image RIGHT, back, side facing image LEFT. Flat grey is background. Those renders are the
design, pattern layout, POSE, proportions and colour authority. Their faceting, blur and low resolution are NOT the design.
`mm9_skin_x4_t<N>.png`: the original 256x256 skin enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent background, unresized returns, 1024x1536 portrait; if the arms need it, the figure may be smaller in the frame, never cropped)
| File | View |
|---|---|
| `00_three_quarter.png` | tier A, front three-quarter, camera at chest height slightly above, as input view 1 |
| `01_front.png` | tier A, straight front |
| `02_back.png` | tier A, straight back |
| `03_left.png` | tier A, pure 90-degree profile facing IMAGE RIGHT (as input view 3) |
| `04_right.png` | tier A, pure 90-degree profile facing IMAGE LEFT (as input view 5) |
| `tierB/01_front.png` ... `tierB/04_right.png` | same four views, tier B |
| `tierC/01_front.png` ... `tierC/04_right.png` | same four views, tier C |

## Runs
- Run 1: `00_three_quarter.png` only, then stop. Inputs: `mm9_views_t1.png`, `mm9_skin_x4_t1.png`, `mm9_head_t1.png` (from references_head/).
- Run 2: 01-04, tier A, with the selected 00 as an extra input so all views show the SAME figure, SAME pose, SAME proportions.
- Run 3: `tierB/` and `tierC/`, with `mm9_views_t2.png`, `mm9_skin_x4_t2.png`, `mm9_views_t3.png`, `mm9_skin_x4_t3.png`, and the selected tier A 01-04 as inputs.
  Same figure, pose and silhouette as tier A: only the surface changes.
At most ONE corrective regeneration per view, then select the better and note any residual fault. Keep raw returns in `raw/`. Write
`generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after each run, a
`selected_views_review.png` contact sheet of the selected views so far.

## Common prompt content (adapt per view)
TASK CONTEXT - FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX mummy monster
from the supplied renders of its original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully
three-dimensional figure, semi-realistic game materials, sharp fine detail, as if a high-quality sculpt of the original model. ONE
complete figure from the crown to the soles, centred, generous margins, never cropped.

Identity (exactly the layout of the input renders): a tall, lean adult man, about 1.85 m, gaunt but with a human torso and limbs, narrow
waist, long legs. The body is one tight continuous wrapped form, like the input.

Tier A surface (Canopic Mummy): the WHOLE body is bound in overlapping linen bandages, each band 3 to 5 cm wide, tea-stained ochre and
dirty straw with coarse woven weave and frayed edges, separated by thin deep DARK uneven gaps. Bands run horizontally round chest, waist
and limbs (as in the input: wavy dark lines round the torso, arms and shins), in V-shaped chevrons down the front and back of the
thighs, and in overlapping criss-crossed bands on the feet, hands and the back of the head. The bands stand in real low relief: an
overlapping edge you can see and model, a real recess in each gap. The HEAD is a tight bandaged hood wrapping crown, cheeks and neck; the
FACE is open: a gaunt, dead, sunken human man's face with a short beard, dull eyes half open, mouth closed or barely parted, with one
strip crossing the face diagonally over one eye as in the input. Feet: bandaged, the shape of a real foot with toes just readable under
the wraps. Dark grime in the recesses, no blood.

Tier B surface (Embalmed Mummy, pattern as in `mm9_views_t2.png`): the same figure, but the bandages have rotted open. Exposed dried flesh on
the chest and belly, the whole back (ribs and spine showing through dark red-brown leathery skin, gashes, stitched tears), the upper arms,
and the thighs and knees: dark mahogany, cracked, leathery. Remaining bandages: a thick torn band round the hips like a ragged loincloth,
tatters hanging on the thighs in painted pieces, X-shaped straps across the back and shoulders, wraps at the elbows, forearms and hands, and wrapped shins and feet.
The head is still hooded by bandages, but the face is a yellowed SKULL with a few shreds of dried skin, cracked cheekbone, long bare teeth and pale blue dead eyes.

Tier C surface (Petrified Mummy, pattern as in `mm9_views_t3.png`): the same figure, more bandaged than tier B: criss-crossed strips over the
chest, belly, legs and arms over near-BLACK and charcoal-brown stone-hard dried flesh, with black voids at the belly and pale cracked
bone-coloured strips standing out. The face is a darker rotted skull with one reddish eye, with bandage strips across it.

Pose (identical in all views, the model's bind pose as in the input): standing upright, arms out to the sides close to horizontal, about 10 degrees below horizontal with a
slight bend at the elbow, palms facing DOWN, legs straight and apart at about 25 degrees from vertical, feet flat, toes forward, head level looking straight ahead.

Hands: BOTH hands alike, open and relaxed, five clearly separated long thin bandaged fingers with air between them, thumb apart. (The renders show a mitten: ignore that.)

Do NOT add: any loose strips, hanging ends, swags, tatters or fringes standing away from the body, even though the renders have them: the band hanging between the wrist and the hip, and
the spikes under the arm, by the hip and at the thigh must all be LEFT OUT. All bandages lie flat on the body. No armour, jewels, weapons, cloth other than bandages,
no extra limbs, no scarab or amulet, no crop, no cast shadow, no floor, no text, no background. Even soft studio light, no dramatic light, nothing baked that looks like a directional shadow.
Near-orthographic.

## Checks per image
True alpha; no floor; complete figure; five fingers on each hand with air between them; no loose strips; arms near horizontal; legs apart; side views show one clean profile with the arms foreshortened;
a face as described; bands readable as separate raised strips with dark gaps (not a blurry stripe paint).
