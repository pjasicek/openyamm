# Codex brief: HD reference views for the MM9 Wyrde of the Unknown, Morgan (mm9_wyrde_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_wyrde_claude/references_hd/`. Do not edit any other file, do
not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the
ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character: one of the three Wyrdes (fates) of Might and Magic IX, a serene young noblewoman-seeress in a long
hooded mantle over a rich embroidered gown. A restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views_y.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front three-quarter from the figure's
   RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout,
   proportions, pose and colour authority. The faceting, blur and low resolution are NOT the design.
2. `mm9_chest_views_y.png`: closer renders of the hood, jewellery, bodice, belt, sleeves and hands, same five views.
3. `mm9_head_views_y.png`: close renders of the head in its hood, same five views.
4. `mm9_skirt_views_y.png`: close renders of the front panel, its gold border, the underskirt, the hem and the shoes, same five views.
5. `mm9_skin_x4_y.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY (face, hood/mantle, gown, spirals, gold trims,
   cuffs, hands, shoes, underskirt laid out flat).
6. (run 2 only) the selected three-quarter master (`references_hd/00_three_quarter_clean.png`, its halo removed; keep `00_three_quarter.png`
   as it is). For 01-04 produce a TRUE transparent background with NO glow or halo around the figure.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1536x1024 LANDSCAPE so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: she faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: she faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so
all views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then select the better
and note any residual fault. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected
flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX Wyrde (fate) woman from the supplied renders of
its original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with
semi-realistic game materials and sharp fine detail (soft wool and velvet with a visible weave, chased gold embroidery and jewellery, soft
leather shoes). ONE complete figure from the top of the hood to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-5):
- A slender adult human WOMAN about 1.75 m tall, graceful womanly proportions, straight calm posture. Not a warrior.
- HEAD: a young woman of about 25, fair skin, calm kind expression with a gentle warm closed-lips smile, blue-grey eyes, soft natural brows,
  rose lips. Long straight GOLDEN-BLONDE hair parted in the middle, falling at both sides of the face over the front of the shoulders down
  to the upper chest, inside the hood.
- CIRCLET: a gold filigree diadem worn over the hood's front edge on the forehead, with a red cabochon gem in the centre and a small pearl drop
  under it, as input 3.
- HOOD AND MANTLE: a deep royal-blue wool mantle with a hood. The hood covers the top, sides and back of the head and frames the face, its
  front edge soft and folded; it drapes in soft folds round the neck and over both shoulders, then falls down the BACK as one long flat
  mantle to mid-calf, ending in a shallow point at the back centre (input 1 view 4). Seen from the front, the mantle shows only as narrow
  blue edges hanging behind the arms at both sides; the gown is fully visible in front. It does not cover the arms.
- NECK JEWELLERY: a choker of pearls and small gold beads, and below it a gold filigree pectoral (a broad ornament at the base of the
  throat) with an amber oval stone and a small green gem, as input 2.
- GOWN: a plum / deep wine-purple velvet gown with long fitted sleeves. The bodice carries TWO gold spiral embroideries on the chest (one
  under each breast, as input 2), a broad gold jewelled belt at the high waist with a red stone in the centre.
- SLEEVES: long fitted plum sleeves to the wrist, each ending in a broad GOLD embroidered cuff band (about 8 cm) with a dark green inner
  edge, as input 2. Hands bare below the cuffs.
- FRONT PANEL: below the belt the plum gown hangs as a straight overskirt to just below the knees, with a gold embroidered border along its
  hem and thin gold edging up its sides, and a small gold tassel ornament at each side (input 4).
- UNDERSKIRT: below it a floor-length dark olive / khaki-brown underskirt in soft vertical pleats with a gold and red border at the hem.
- SHOES: plain soft brown leather shoes with rounded toes; only their fronts show under the hem.
- HANDS: bare human hands with FIVE separate fingers (four fingers and a thumb), relaxed, slightly curled, open, clear air between the
  fingers, palms down. Nothing in them.
- COLOUR: as inputs 1 and 5: royal-blue mantle and hood, plum gown, gold trims and jewellery, olive-brown underskirt, brown shoes, golden
  blonde hair. Flat even studio light, no baked shadows.
- No staff, no weapon, no book, no crown other than the circlet, no wings, no extra limbs, no bare legs.

Pose (identical in all views; EXACTLY the pose of input 1): standing upright and symmetrical, feet about 20 cm apart under the hem, toes
forward, the skirts hanging straight; arms straight, out to the sides and sloping down about 30 degrees below horizontal, elbows nearly
straight, wrists straight. Head level, looking straight ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: make her older; make her stern, fierce or cold; open the mouth or show teeth; let the mantle cover the arms or the front of the gown;
add a veil, braids or visible ears; make the sleeves short or bell-shaped; change the colours; crop any part; copy the blur or faceting.

Per-image checks (redo at most once): hood top to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; a calm
young blonde woman with closed lips and a gentle smile; blue hood and mantle reaching mid-calf at the back; gold circlet on the forehead;
plum gown with two chest spirals, gold belt and gold cuffs; front panel to below the knees with a gold border; olive underskirt to the floor;
shoes under the hem; the side views show the figure facing the stated image direction.
