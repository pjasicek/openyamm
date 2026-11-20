# Codex brief: HD reference views for the MM9 Bigfoot (mm9_bigfoot_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_bigfoot_claude/references_hd/`. Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and
Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game monster: a huge ape-like Bigfoot, a restoration of an existing 2002 game creature for a game mod. It has no genitals: the long fur covers the groin as a smooth shaggy mass.

## Inputs (attached, in order)
1. `mm9_views_a.png`: renders of the ORIGINAL low-poly model with its skin (tier "Bigfoot"), five views left to right: front three-quarter from the
   figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, POSE,
   proportions and colour authority. Faceting, blur and low resolution are NOT the design.
2. `mm9_head_views_a.png`: close renders of the head: face, crest and ears authority (front, three-quarter, left side, back).
3. `mm9_hand_views_a.png`: close renders of the right hand.
4. `mm9_foot_views_a.png`: close renders of the right foot.
5. `mm9_skin_x4_a.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
6. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1536 portrait)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so all views are
the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then select the better and note any residual fault.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after run 2,
a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Bigfoot" from the supplied renders of its original 3D model,
as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional creature with semi-realistic game materials and sharp fine
detail (individual fur strands, leathery skin, nails). ONE complete figure from the crest to the toes, centred, generous margins, never cropped.

Identity (exactly the layout of inputs 1-5):
- A huge, heavy, upright ape-man about 2.5 m tall: enormous square shoulders and trapezius rising straight into the head with almost no neck, a deep broad chest, thick waist, heavy legs like columns, very long thick arms. The fingertips reach the middle of the thigh when the arms hang.
- FUR: the whole body is covered in dense, slightly shaggy reddish dark-brown fur, like a chestnut orangutan coat but shorter, as input 5. Strands run downward along the limbs, in clumps.
  A paler tan-brown bare-looking chest and belly: broad pectoral muscles and a rounded stomach in dull tan short hair, as input 1. Soft ragged edges, no hard line.
  Slightly paler golden patches on the front of the knees, the shins and the upper buttocks, as input 1. The back is dark reddish brown.
- HEAD (input 2): a gorilla-like head, tall and pointed: a high SAGITTAL CREST rising to a blunt peak on top of the skull, covered in striped golden-tan and dark-brown swept hair that ends in a heavy overhanging fringe straight across the brow. Under it a bare dark grey-brown leathery face: heavy brow ridge, small deep-set amber eyes, a flat ape nose with a pale pinkish-grey muzzle and big nostrils, a long upper lip, a wide CLOSED mouth with thin dark lips, a heavy chin with a short dark beard. Small human-like pale ears set far back at the sides of the head. The back of the head is plain dark reddish fur flowing into the shoulders.
- HANDS (input 3): big, heavy ape hands, RELAXED and slightly curled, NOT fists: four thick separate fingers and a thick separate thumb, brown leathery skin on the fingers with short pale-yellow nails, the fur stops at the knuckles. Fingers slightly apart so each finger reads.
- FEET (input 4): very large flat ape-man feet, long, with FIVE thick separate toes with yellow-brown nails, the big toe largest, soles flat on the ground, fur down to the toes.
- No tail. No clothes, no belt, no armour, no jewellery, no weapons.

Pose (identical in all views, the model's bind pose as in input 1): standing upright, legs straight and apart (feet about 40 cm apart), feet pointing forward; arms held away from the body and down at about 30 degrees from vertical, elbows very slightly bent, palms facing the thigh, clear air between arms and body, clear air between the legs. Head level, looking straight ahead along the body.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add clothes or weapons; add a tail; change colours; crop any part; close the hands into fists; give the face human skin; show teeth; copy faceting or the render's dark sheen.

Per-image checks (redo at most once): crest to toes in frame; true alpha; complete crest, two ears; open hands with four fingers plus thumb; five toes; tan chest on brown fur; closed mouth with a complete chin.
