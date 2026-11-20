# Codex brief: HD reference views for the MM9 Bembridge Scholar (mm9_scholar_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_scholar_claude/references_hd/`. Do not edit any other file,
do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the
ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character: a Bembridge Scholar of Might and Magic IX, a learned man in a long scholar's robe with a soft cap.
A restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views_1.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front three-quarter from the figure's
   RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout,
   proportions, pose and colour authority. The faceting, blur and low resolution are NOT the design.
2. `mm9_chest_views_1.png`: closer renders of the beard, the stole collar with its gold chain and medallion, the belt, sleeves and hands.
3. `mm9_head_views_1.png`: close renders of the head, cap, hair and beard, same five views.
4. `mm9_skirt_views_1.png`: close renders of the robe's lower part, its hem and the shoes, same five views.
5. `mm9_skin_x4_1.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY (face, beard, cap, stole with the gold chain,
   robe cloth, cuff band, hand, belt, shoes laid out flat). Never the shape.
6. (run 2 only) the selected three-quarter master (`references_hd/00_three_quarter_clean.png`, its halo removed; keep `00_three_quarter.png` as it is). For 01-04 produce a TRUE transparent background with NO glow or halo around the figure.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1536x1024 LANDSCAPE so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front; the figure's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the figure's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: he faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: he faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so
all views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then select the better
and note any residual fault. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected
flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT, FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX Bembridge Scholar
from the supplied renders of its original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully
three-dimensional figure with semi-realistic game materials and sharp fine detail (fine wool with a visible weave, soft felt cap, satin
stole, chased gold chain and medallion, leather belt and shoes, individual hair and beard strands). ONE complete figure from the top of the
cap to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-5):
- A slender adult human MAN of about 40, about 1.78 m, upright calm posture, a learned man, not a warrior.
- HEAD: a lean, kind face with fair skin, blue-grey eyes, straight brows, a straight nose, a calm warm closed-lips expression. A full
  COPPER-GINGER BEARD with a moustache, the beard long and full, reaching the upper chest in a rounded point (inputs 2, 3). Long thick
  copper-ginger hair falling straight from under the cap to the shoulders at the sides and down the back to the shoulder blades (input 3
  back view).
- CAP: a soft, floppy, very dark navy felt scholar's cap (a beret-like bonnet) sitting on top of the head and tilted back, its brim
  rolled, a little wider than the head (input 3).
- ROBE: a long, ankle-length DARK NAVY-BLUE wool scholar's robe, straight and simple, with long wide sleeves to the wrists, each ending in a
  slate-grey cuff band; the sleeves are open and slightly wide at the wrist. A plain brown leather belt with a small gold buckle at the
  waist; the robe falls straight and wide below it to just above the ankles with a slate-grey hem band.
- STOLE: a broad dark charcoal-grey satin shawl collar lying over the shoulders and coming down the chest in a deep V to the breastbone
  (input 2), with a wide rolled collar at the back of the neck (input 1 back view). Along both front edges runs a chain of small gold
  beads and amber medallions meeting at a round gold medallion at the point of the V.
- HANDS: bare human hands with FIVE separate fingers (four fingers and a thumb), relaxed and slightly curled, open, clear air between the
  fingers, palms down. Nothing in them.
- SHOES: plain dark brown leather shoes with rounded toes under the hem.
- COLOUR: as inputs 1 and 5: dark navy robe and cap, charcoal stole, gold chain, copper-ginger hair and beard, brown belt and shoes. Flat
  even studio light, no baked shadows (the image is baked into a texture).
- No staff, no book, no scroll, no weapon, no cloak, no hood, no wings, no extra limbs.

Pose (identical in all views; EXACTLY the pose of input 1): standing upright and symmetrical, feet about 20 cm apart under the hem, toes
forward; arms straight, out to the sides sloping down about 20-25 degrees below horizontal, elbows nearly straight, wrists straight, clear
air between the sleeves and the body. Head level, looking straight ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: make him stern, fierce, cold or sinister; open the mouth or show teeth; make him a wizard with a pointed hat; add a hood or cloak;
change the colours; shorten the beard or hair; crop any part; copy the blur or faceting.

Per-image checks (redo at most once): cap top to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; a calm
man of about 40 with closed lips; long ginger beard and shoulder-length ginger hair; navy cap and robe with grey cuffs and hem; charcoal V
stole with the gold chain and round medallion; brown belt; the side views show the figure facing the stated image direction.
