# Codex brief: HD reference views for the MM9 Wyrde of the Known, Igrid (mm9_wyrdold_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_wyrdold_claude/references_hd/`. Do not edit any other file,
do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the
ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character: Igrid, the eldest of the three Wyrdes (fates) of Might and Magic IX, a very old, kindly seeress in
a long hooded brown robe-cloak over a navy embroidered gown. A restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front three-quarter from the figure's
   RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout,
   proportions, POSTURE, pose and colour authority. The faceting, blur and low resolution are NOT the design.
2. `mm9_chest_views.png`: closer renders of the hood, braids, jewellery, gown front, belt, sleeves and hands, same five views.
3. `mm9_head_views.png`: close renders of the head in its hood, same five views.
4. `mm9_skirt_views.png`: close renders of the gown's lower part, the robe's hem and the feet, same five views.
5. `mm9_skin_x4.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY (face, hood, robe cloth, navy gown with gold
   spirals, jewelled belt, cuff band, hand, grey braid laid out flat). Never the shape.
6. (run 2 only) the selected three-quarter master (`references_hd/00_three_quarter_clean.png`, its halo removed; keep `00_three_quarter.png` as it is). For 01-04 produce a TRUE transparent background with NO glow or halo around the figure.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1536x1024 LANDSCAPE so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front; the figure's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the figure's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: she faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: she faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so
all views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then select the better
and note any residual fault. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected
flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT, FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX Wyrde Igrid from
the supplied renders of its original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully
three-dimensional figure with semi-realistic game materials and sharp fine detail (soft brushed wool with a faint darker damask pattern,
navy velvet, chased gold embroidery and jewellery, soft leather). ONE complete figure from the top of the hood to the soles, centred, both
hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-5):
- A small, very old human WOMAN of about 85, about 1.60 m, gently STOOPED: the upper back rounded and the head and neck carried FORWARD
  in front of the shoulders exactly as in the profile views of input 1. Keep this posture and her proportions. Not a witch, not a monster.
- HEAD: a deeply wrinkled, kind old face, warm ruddy-tan skin, bright pale-blue eyes with crow's feet, thin soft white brows, a long
  straight nose, a broad warm closed-lips smile with natural old lips (input 3). Thin white-grey hair framing the face inside the hood, and
  two long thin GREY BRAIDS hanging down from inside the hood at both sides of the face to the upper chest (input 2, input 5 bottom).
- CIRCLET: a thin gold circlet with a small dark-red stone across the forehead, just inside the hood's front edge (input 3 front).
- HOOD AND ROBE: ONE long, deep DARK-BROWN (cocoa / umber) wool robe-cloak. A deep hood covers the top, sides and back of the head, rising
  to a soft point on top, its front edge framing the face closely; it drapes in soft folds round the neck. The robe has long full sleeves
  of the same brown cloth covering the arms to the wrists, each ending in a plain brown cuff. The robe is OPEN DOWN THE FRONT from the
  neck to the floor, its two straight front edges framing the navy gown; it hangs to the floor all round (to the ankles at the front, a
  little longer at the back), wide at the hem like a long cone (inputs 1 and 4).
- NECK JEWELLERY: a choker of small pearls with gold beads, and below it a long gold pendant with an amber stone hanging to a gold
  filigree ornament with green and red gems at the top of the gown (input 2).
- GOWN (visible in the robe's front opening): a dark NAVY-BLUE velvet gown to the floor. On the bodice TWO gold spiral embroideries side by
  side; at the waist a broad gold jewelled belt with a red stone in the centre; below it thin gold braided cords hang down the front; near
  the knees a broad gold-and-red embroidered band across the gown; the lowest part a darker navy with a thin teal hem trim (inputs 2, 4, 5).
- HANDS: bony, knuckly old hands with long thin fingers, warm ruddy skin, FIVE separate fingers (four fingers and a thumb), relaxed and
  slightly curled, open, clear air between the fingers, palms down; a small gold ring may show on one finger. Nothing in them.
- FEET: hidden under the hem except the toes of plain dark shoes.
- COLOUR: as inputs 1 and 5: dark brown robe and hood, navy gown, gold jewellery and embroidery, grey braids, ruddy skin. Flat even studio
  light, no baked shadows (the image is baked into a texture).
- No staff, no weapon, no book, no crown, no veil, no wings, no extra limbs.

Pose (identical in all views; EXACTLY the pose of input 1): standing, gently stooped as above, feet about 20 cm apart under the hem; arms
out to the sides sloping down about 30 degrees below horizontal, the full sleeves hanging from them, elbows nearly straight, wrists
straight, clear air between the sleeves and the robe. Head forward as in input 1, looking ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: straighten her back or lift her head upright; make her young, stern, fierce, cold, sinister or witch-like; open the mouth or show
teeth; close the robe over the gown; make the robe black or the gown purple; let the hood hide the face; show ears; add a staff or
anything held; change the colours; crop any part; copy the blur or faceting.

Per-image checks (redo at most once): hood top to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; a
kind very old woman with closed lips and a warm smile; the stoop and forward head; brown hood and open brown robe to the floor; navy gown
with two gold spirals, gold belt and knee band; two grey braids; the side views show the figure facing the stated image direction.
