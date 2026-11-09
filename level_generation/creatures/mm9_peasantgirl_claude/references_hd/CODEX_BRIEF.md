# Codex brief: HD reference views for the MM9 human peasant girl PeasantGirl2 (mm9_peasantgirl_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantgirl_claude/references_hd/`. Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, a human village girl of about nine in a plain folk costume, a restoration of an existing 2002 game character for a game mod. She is a friendly, ordinary village child.

## Inputs (attached, in order)
1. `mm9_views_g2.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front three-quarter, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, proportions and colour authority. The faceting, blur, low resolution and the stiff T-pose are NOT the design.
2. `mm9_chest_views_g2.png`: closer renders of the head, bodice, sleeves and hands, same five views.
3. `mm9_head_views_g2.png`: close renders of the head and hair, same five views.
4. `mm9_skirt_views_g2.png`: close renders of the apron, the long skirt, the hem and the shoes, same five views.
5. `mm9_skin_x4_g2.png`: the original 128x128 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY (face, hair, bodice, sleeves, arms, hands, apron, skirt, shoes laid out flat).
6. (run 2 only) the selected three-quarter master `references_hd/00_three_quarter.png`.

## Deliverables (TRUE transparent background with no glow or halo, no floor, no shadow, no text, unresized returns, 1536x1024 LANDSCAPE so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, the figure turned about 35 degrees to IMAGE LEFT (we see more of her right side), camera at chest height slightly above |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: she faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: she faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so all views are the SAME girl, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX peasant girl from the supplied renders of its original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine detail (soft wool with a visible weave, linen, fine gold folk embroidery, worn soft leather). ONE complete figure from the top of the head to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-4):
- A human GIRL of about nine years old, about 1.30 m tall, child proportions (a relatively large head, slim limbs, narrow shoulders, no bust, no waist curves). Straight posture. Not an adult, not a doll, not a cartoon.
- HEAD: a sweet round child's face, fair skin with light freckles and rosy cheeks, blue eyes OPEN and clearly visible, small straight nose, a calm warm closed-lip smile, soft natural brows. Calm and warm, never fierce or cold.
- HAIR: long straight auburn / chestnut-brown hair parted in the middle, falling smoothly over the ears and down the back as one long mass to the middle of the back (input 3, back view); a thin braid runs from each temple back along the side of the head. Ears hidden under the hair.
- DRESS: a rust-brown / red-brown wool dress: a fitted upper body, sleeves to just below the elbow ending in a narrow dark trim with gold embroidery, and a floor-length gathered skirt.
- UNDERSLEEVES: from the dress sleeve to the wrist a cream linen undersleeve that flares a little at the wrist, as input 2.
- BODICE: over the front of the dress a black sleeveless bodice / vest with rich GOLD folk embroidery (scrolls and leaves) along its edges and front, a deep U neckline, laced up the centre front with red-brown lacing, as input 2. A narrow dark waist band at the bottom of the bodice with two small hanging tabs.
- ARMS AND HANDS: bare hands only below the undersleeves; bare child hands with FIVE separate fingers (four fingers and a thumb), relaxed, slightly curled, open, clear air between the fingers, palms down. No gloves. Nothing in them.
- APRON: a cream / off-white linen apron in front, from the waist band to about two thirds of the way down the skirt (below the knees), a flat panel wrapping a little round the sides, soft vertical folds, plain, as input 4.
- SKIRT: the dress's floor-length rust-brown skirt, a gentle A-line from the waist to a straight hem at the ankles, soft shallow vertical folds only, closed all round (no slit). Seen from the back it is all skirt and hair; the apron is only at the front.
- SHOES: soft brown leather shoes with a rounded toe; only their fronts show under the hem.
- COLOUR: as inputs 1 and 5: auburn hair, rust-brown dress, black bodice with gold embroidery, cream undersleeves and apron, brown shoes. Flat even studio light, no baked shadows.
- No jewellery, no belt pouch, no basket, no doll, no tools, no cloak, no headwear, no extra limbs, no bare legs.

Pose (identical in all views): standing upright and symmetrical, feet about 15 cm apart under the hem, toes forward, the skirt hanging straight; arms straight, out to the sides and sloping down about 30 degrees below horizontal, elbows nearly straight, wrists straight, clear air between the arms and the body. Head level, looking straight ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: make her a teenager or an adult; make her chibi or big-eyed; show the ears; give her short sleeves or bare forearms; add a hat, headscarf or ribbons; change the colours; make the apron reach the floor; add patterns or trims beyond those listed; crop any part; copy the blur or faceting.

Per-image checks (redo at most once): head top to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; open eyes; child proportions; long auburn hair down the back with the temple braids; black gold-embroidered laced bodice; rust-brown elbow sleeves with cream undersleeves to the wrist; cream apron in front only to below the knees; floor-length rust-brown skirt; shoes under the hem; the side views show the figure facing the stated image direction.
