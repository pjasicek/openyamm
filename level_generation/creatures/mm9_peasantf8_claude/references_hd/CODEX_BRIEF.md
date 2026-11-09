# Codex brief: HD reference views for the MM9 elf peasant woman PeasantF8 (mm9_peasantf8_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantf8_claude/references_hd/`. Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an adult female elf villager in plain medieval peasant clothes, a restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views_b.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front three-quarter from the figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, proportions, pose and colour authority. The faceting, blur and low resolution are NOT the design.
2. `mm9_chest_views_b.png`: closer renders of the headscarf, bodice, sleeves and hands, same five views.
3. `mm9_head_views_b.png`: close renders of the head in its headscarf, same five views.
4. `mm9_skirt_views_b.png`: close renders of the apron, the long skirt, the hem and the shoes, same five views.
5. `mm9_skin_x4_b.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY (face, bodice, scarf, apron, skirt, hands, shoes, ears are laid out flat).
6. (run 2 only) the selected three-quarter master (`references_hd/00_three_quarter_clean.png`, the halo removed; keep `00_three_quarter.png` as it is). For 01-04 produce a TRUE transparent background with NO glow or halo around the figure.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1536x1024 LANDSCAPE so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: she faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: she faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so all views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX elf peasant woman from the supplied renders of its original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine detail (soft wool and linen with a visible weave, a fine embroidered neckline band, worn soft leather). ONE complete figure from the top of the headscarf to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-4):
- A slim adult FEMALE elf about 1.76 m tall, ordinary womanly proportions, natural bust and waist, straight posture. Not a warrior, not glamorous.
- HEAD: a young woman of about 25, fair skin, soft round face, green-grey eyes, straight nose, small closed mouth with natural pink lips. Blonde hair parted in the middle and swept to both sides under the scarf, showing only at the forehead and temples. LONG POINTED ELF EARS, about 9 cm long, sticking out sideways and slightly up and back through the sides of the headscarf, both clearly visible, skin coloured.
- HEADSCARF: a soft ochre / honey-brown cloth kerchief covering the top and back of the head; it frames the face with a rolled front edge above the forehead and falls straight down behind the head to the shoulders and upper back as a simple soft curtain, as input 3. It does not cover the face, the neck front or the ears.
- BODICE: a fitted deep red wool bodice from the neck to the waist with a round neckline; along the neckline a narrow embroidered band (red, gold and dark brown pattern) with a small embroidered V at the front centre, as inputs 2 and 3. The neck and throat are bare above it.
- SLEEVES: long sleeves of ochre / honey-brown cloth, the same cloth as the scarf, fitted at the shoulder and widening gently to an open cuff at the wrist, coaxial with the arm (not hanging bags). The cuff ends at the wrist.
- HANDS: bare human hands with FIVE separate fingers (four fingers and a thumb), relaxed, slightly curled, open, clear air between the fingers, palms down. No gloves. Nothing in them.
- WAIST: a narrow pale linen waistband round the waist.
- APRON: a cream / off-white linen apron tied at the waist band, covering the front of the skirt from the waist to just below the knees, a flat wide panel with soft vertical folds, plain, as input 4.
- SKIRT: a floor-length red-brown wool skirt, a wide gentle A-line from the waist to a straight hem just above the ankles, soft shallow vertical folds only, closed all round (no slit). Seen from the back it is all skirt; the apron is only at the front.
- SHOES: plain soft brown leather shoes with a rounded toe; only their fronts show under the hem.
- COLOUR: as inputs 1 and 5: deep red bodice, honey-brown scarf and sleeves, cream apron, red-brown skirt, brown shoes. Flat even studio light, no baked shadows.
- No jewellery except the embroidered neckline, no belt pouch, no basket, no tools, no weapons, no cloak, no extra limbs, no bare legs.

Pose (identical in all views; EXACTLY the pose of input 1): standing upright and symmetrical, feet about 20 cm apart under the hem, toes forward, the skirt hanging straight; arms straight, out to the sides and sloping down about 30 degrees below horizontal, elbows nearly straight, wrists straight. Head level, looking straight ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add a hood point, a veil over the face, or braids; hide the ears; change the colours; make the sleeves droop into hanging bags; make the apron reach the floor; add pleats, patterns or trims beyond the embroidered neckline; crop any part; copy the blur or faceting.

Per-image checks (redo at most once): scarf top to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; two pointed elf ears; bare neck above the embroidered round neckline; red bodice; cream apron in front only to below the knees; floor-length red-brown skirt; shoes under the hem; the side views show the figure facing the stated image direction.
