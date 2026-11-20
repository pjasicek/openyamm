# Codex brief: HD reference views for the Imp (MM9 monster) (mm9_imp_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_imp_claude/references_hd/`. Do not edit any
other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites
for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the creature's RIGHT (faces image right and toward the viewer),
   front, creature's LEFT side (faces IMAGE LEFT), back, creature's RIGHT side (faces IMAGE RIGHT). Flat grey is
   background. This is the design, POSE, proportions and colour authority. Its faceting, blur, dark shading and low
   resolution are NOT the design.
2. `references_hd/mm9_head_views.png` — close renders of the same model's head (front, left profile, three-quarter):
   the face, horn, ear and mouth authority.
3. `references_hd/mm9_skin_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (the painted face, wrinkled hide, studded leather). Never the design or shape.
4. (run 2 only) the selected `references_hd/00_three_quarter.png`.
5. (run 2 only, trident view only) `references_hd/mm9_trident_view.png` and `references_hd/mm9_trident_skin_x8.png`.

## Deliverables (true transparent background, unresized returns, 1536x1024 landscape so the spread arms and tail fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the creature's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front; the creature's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the creature's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the creature's LEFT side: faces IMAGE LEFT, tail on IMAGE RIGHT |
| `04_right.png` | pure 90-degree profile of the creature's RIGHT side: faces IMAGE RIGHT, tail on IMAGE LEFT |
| `05_trident.png` | (run 2) the trident alone, lying horizontal, pure side view with all three prongs fanned in the image plane, prongs on IMAGE LEFT, red butt spike on IMAGE RIGHT, filling the width |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–05 with the selected 00 as an
additional input so all views are the SAME creature, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`. Write
`generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after
run 2, a `selected_views_review.png` contact sheet of the selected views.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and Magic IX
monster from the supplied renders of its original 3D model, as a 3D modelling and texturing reference. Not a new
design. A credible, fully three-dimensional creature with semi-realistic game materials and sharp fine detail (wrinkled
hide, skin folds, leather, studs, claws), as if a high-quality sculpt of the original model. ONE complete figure from
the horn tips to the soles and the tail tip, centred, generous margins, never cropped.

Pose (identical in all views, the model's bind pose as in input 1): a stooped goblinoid stance: the back rounded, the
shoulders high, the neck thrust FORWARD and the big head hanging forward and low, face level, as in input 1's side
views. Arms held out to the sides and down, about 40 degrees below horizontal, slightly bent, with clear air between
the arms and the body. Hands open and EMPTY with the claws slightly curled, every digit clearly separate. Legs slightly
apart with a clear gap between them, the knees very slightly bent, the left foot a little ahead of the right as in
input 1's side view, feet flat. The tail comes out of the base of the spine, runs down and back in a gentle S curve
clear of the legs.

Camera and light: near-orthographic, even soft neutral studio light (brighter than input 1, which is dark), no dramatic
light, no strong cast shadows on the body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity and colours as inputs 1–3; the pose above (stoop, arms out,
empty open hands, gap between the legs); digit counts (below); the correct side faces the correct image side (03: faces
IMAGE LEFT; 04: faces IMAGE RIGHT); whole figure and tail inside the frame with margins; true transparent background;
1536x1024.

## Identity
The Imp: a small, bald, pot-bellied devil-goblin, about 1.2 m tall with a big head, narrow bony shoulders, long skinny
arms, a round belly and thin legs with long flat feet.
- Hide: mustard-yellow to olive-gold wrinkled hide with darker ochre-brown mottling in the folds, and a paler tan
  blaze down the middle of the forehead, nose and chest. Colours from inputs 1 and 3.
- Head (input 2): large, bald, heavy brow ridge with deep wrinkles, a long hooked pointed nose, wide flat cheeks, a
  jaw narrowing to a pointed chin; the mouth is a wide snarl showing a double row of long jagged pale fangs on dark
  gums, with a short black tuft under the lower lip. Two short black conical horns on top of the skull, pointing
  up and slightly out. Two pointed bat-like ears standing out sideways and back from the head.
- Eyes: glowing emerald-green, almond-shaped, slanted, with no pupil, set deep under black-shadowed brows.
- Hands: FOUR digits per hand: one thumb and THREE long bony fingers, each ending in a long dark claw.
- Feet: long flat feet with THREE toes each, each toe ending in a curved dark claw with a green tip.
- Tail: thin, whip-like, same hide, ending in a black arrowhead spade.
- Wear: nothing but a wide black leather belt round the hips with silver round studs and a round skull-like buckle at
  the front, a square black studded leather flap hanging from it over the groin at the front, and a narrow black
  leather band with three silver studs on each wrist. Bare buttocks and a bare back: the flap is at the front only.

## Trident (`05_trident.png` only)
A long thin straight wooden shaft, orange-brown with a diagonal wrapped grain, about 75 times as long as it is thick; a
small brass-gold collar at the head; three flat steel blades: a long straight centre spike and two side tines that
leave the collar outward, then bend forward parallel to the centre spike, pale blue-grey steel with bright edges and
darker fuller; at the other end a small gold ferrule with a red faceted spike. No hands, no background, no shadow.

## Do NOT
- add armour, clothing, jewellery, wings, hair, a weapon in the hands (the trident is a separate image), or extra
  fingers or toes; give the eyes pupils; close the mouth; make the creature muscular, tall or human-proportioned;
  straighten the stoop; change colours; change the pose; crop.
