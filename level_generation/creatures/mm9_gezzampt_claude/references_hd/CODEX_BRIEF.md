# Codex brief: HD reference views for the MM9 Gezzampt (mm9_gezzampt_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_gezzampt_claude/references_hd/`. Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and
Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game monster: a horned, hoofed, fur-covered beast-man, a restoration of an existing 2002 game creature for a game mod. It has no genitals: the dark fur covers the groin as a smooth shaggy mass.

## Inputs (attached, in order)
1. `mm9_views_a.png`: renders of the ORIGINAL low-poly model with its skin (tier "Gezzamptling"), five views left to right: front three-quarter from the
   figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, POSE,
   proportions and colour authority. Faceting, blur and low resolution are NOT the design.
2. `mm9_head_views_a.png`: close renders of the head: face, teeth, mane, horns and ears authority (front, three-quarter, left side, back).
3. `mm9_hand_views_a.png`: close renders of the right fist.
4. `mm9_hoof_views_a.png`: close renders of the right lower leg and hoof.
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
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Gezzampt" from the supplied renders of its original 3D model,
as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional creature with semi-realistic game materials and sharp fine
detail (individual fur strands, horn rings, hoof grain). ONE complete figure from the crest to the hooves, centred, generous margins, never cropped.

Identity (exactly the layout of inputs 1-5):
- A big, heavily muscled beast-man about 2.5 m tall: very wide shoulders and neck, thick long arms, broad chest, narrow waist, strong thighs. Long arms: the fists hang level with the thighs.
- FUR: the whole body is covered in short dense fur, with the two-tone layout of input 1, no bare human skin.
  Golden tan fur on the chest and belly muscles, the shoulder fronts, the outer upper arms, forearms, fists, and thighs.
  Very dark brown shaggy fur on the shoulder tops, the sides of the chest, the waist, hips and groin, and the lower legs below the knee. The back is dark with a golden patch of back muscles in the middle, as input 1 view 4.
  The chest, stomach and back muscles are clearly modelled under the fur. The dark fur edge is soft and ragged, not a hard line.
- HEAD (input 2): a broad brutal face, tawny golden fur on brow and cheeks. Heavy dark brow ridge, angry deep-set eyes with amber irises. A big broad flat nose. Dark brown beard round the jaw and chin.
  A wide closed snarl with the lips drawn back: a row of small teeth and two pairs of tusks, lower ones rising past the upper lip. A complete chin.
- MANE: a thick, tall crest of dark brown hair starting at the forehead, rising up and BACK to a high point behind the crown (like a stiff swept-back mane), then falling behind the head as a broad mass down to the top of the back. Its silhouette is the pointed shape in input 2's side view, but it is real hair, not a box.
- HORNS: two short curved ram-like horns, pale bone with dark ring bands, one each side of the head above the temple, curving out and forward, as input 2.
- EARS: two large pointed ears standing out level to the sides just below the horns, thin, tawny, as input 2.
- HANDS: tightly closed FISTS, five thick fingers curled into the palm and a thumb across them, big knuckles, each fist the size of a large melon, as input 3. Short pale blunt nails. Do not open the hands. Keep clear air between each fist and the thigh.
- LEGS (input 4): goat-like digitigrade legs. Thick thigh, knee forward, then a short calf running back to a high hock, then a long straight shank running down and forward to the hoof. As the side views of inputs 1 and 4.
- HOOVES: a big split (cloven) hoof on each leg, polished dark horn with a paler centre ridge, wide at the ground, tips pointing forward, as input 4; a band of fur above it. No toes.
- No tail. No wings. No clothes, no belt, no armour, no jewellery, no weapons.

Pose (identical in all views, the model's bind pose as in input 1): standing, legs apart (hooves about 75 cm apart), hooves pointing forward; arms held away from the body and down at about 25-30 degrees from vertical, elbows very slightly bent, fists turned so the knuckles face outward and forward, clear air between arms and body, clear air between the legs. Head level, looking straight ahead along the body.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add clothes or weapons; add a tail; change colours; crop any part; open the hands; give human feet; copy faceting or the render's dark sheen.

Per-image checks (redo at most once): crest to hoof in frame; true alpha; two horns and two ears; closed fists with clear fingers; goat legs with cloven hooves; golden chest on dark fur; complete chin and tusks.
