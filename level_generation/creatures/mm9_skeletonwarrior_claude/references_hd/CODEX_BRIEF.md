# Codex brief: HD reference views for the MM9 Skeleton Master (mm9_skeletonwarrior_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_skeletonwarrior_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no
native sprites for MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders made
from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views.png` — renders of the ORIGINAL MM9 low-poly model with its original skin, five views left to
   right: front three-quarter from the figure's RIGHT (it faces image right and toward the viewer), front, figure's LEFT
   side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Flat grey is background. This is the design,
   armour layout, POSE, proportions and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_head_views.png` — close renders of the same model's head and shoulders (front, three-quarter,
   left profile, back): the skull and helmet authority.
3. `references_hd/mm9_skin_x4.png` — the original 256x256 skin enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY (red
   lacquered lamellar plates, blue lacing, dark chain mail, ivory-olive bone, black iron). Never the design or shape.
4. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1024x1536 portrait)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front; the figure's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the figure's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as an
additional input so all views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`. Write
`generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after
run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic
IX "Skeleton Master" monster from the supplied renders of its original 3D model, as a 3D modelling and texturing
reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp
fine detail (aged bone with cracks and pits, riveted black iron, individually laced lamellar plates, chain-mail rings),
as if a high-quality sculpt of the original model. ONE complete figure from the helmet spikes to the soles, centred,
generous margins, never cropped. It is a real SKELETON: no skin, no muscle, no cloth body under the armour; where the
armour stops you see separate bones with clear air between them.

Identity (exactly the layout of inputs 1 and 2):
- Tall and thin, about two metres, a gaunt skeleton in samurai-like dark armour.
- HELMET: a tall pointed black-iron war hood, open at the face, whose sides fall as two long cheek-and-neck guards to
  below the jaw and whose back falls to a point at the nape. The lower guards are covered with RED lacquered lamellar
  plates laced with BLUE cord. THREE curved pale horn spikes stand on the crown (one tall in the centre, one on each
  side curving up and out) on little gold-beaded collars. A small red-and-gold insignia sits on the brow edge above the
  face opening.
- SKULL: a human skull of aged ivory-olive bone, with deep eye sockets holding glowing RED eyes, a nasal hole, cheekbones,
  and an OPEN mouth with a full upper and lower row of teeth (a separate lower jaw, the mouth open about 3 cm).
- NECK: bare neck vertebrae between helmet and collar.
- CUIRASS: a short sleeveless cuirass from the neck to the lower ribs only. Dark chain mail at the collar and upper chest,
  RED lamellar plates with BLUE lacing across the lower chest and the whole back, a black stepped collar with standing
  shoulder points.
- SHOULDERS: short cap pauldrons of red lamellar and chain over the top of each upper arm.
- WAIST: NO armour between the cuirass and the belt: a bare bone spine with a few vertebrae, the lowest ribs just
  visible below the cuirass, clear air on both sides of the spine.
- SKIRT: a black belt with a gold-rimmed round buckle at the hips, then a knee-length skirt of stiff armoured panels: a
  wide pointed front panel, a wide pointed back panel and two narrow pointed side strips each side, red lamellar with blue
  lacing framed in dark chain.
- ARMS: bare bone upper arms (a single humerus each) from under the pauldrons; black iron tubular BRACERS covering the
  whole forearm, with a gauntlet at the end.
- HANDS: black iron articulated GAUNTLETS with five separate fingers, each finger plated in several segments.
- LEGS: bare bone thighs (a single femur each) under the skirt, a knobbly bone knee, then tall black-iron GREAVE BOOTS
  from just under the knee to the foot, with engraved plates and iron toe caps. Bone toes are NOT shown: the boots are
  closed, except for a little bone showing at the toe-cap as in input 1.

Pose (identical in all views, the model's bind pose as in input 1): standing upright, arms hanging out to the sides
about 25-30 degrees away from the body with a little bend at the elbow and clear air between the arms and the body;
the gauntlet hands open with the five fingers separated and slightly curved (NOT fists), palms facing the thighs; legs
straight and wide apart as in input 1 with a clear gap between them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light (brighter than input 1, which is dark), no dramatic
light, no strong cast shadows on the figure; genuine transparent background, no floor, no shadow, no text.

Do NOT: add a weapon, shield, cape, cloth, flesh, skin, muscle or extra armour; do not add ribs in front of the cuirass;
do not close the mouth; do not fill the waist gap; do not change the colours; do not make the armour shiny silver;
no fire and no glow except the red eyes; do not crop the helmet spikes or the feet.

## Per-image checks (re-run before selecting)
Three horn spikes on the helmet; open-faced helmet with long lamellar side guards; ivory skull with red eyes and an open
toothed mouth; short cuirass with red lamellar and blue lacing; bare spine at the waist with air beside it; pointed
armoured skirt; bare bone humerus and femur; black bracers, gauntlets with FIVE separated fingers on each hand, greave
boots; no weapon; the pose above; the correct side faces the correct image side (03: faces IMAGE LEFT; 04: faces IMAGE
RIGHT); whole figure inside the frame with margins; true transparent background; 1024x1536.
