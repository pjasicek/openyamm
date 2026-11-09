# Codex brief: HD reference views for the MM9 human peasant woman PeasantF5 (mm9_peasantf5_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantf5_claude/references_hd/`. Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an adult human village woman in a plain folk costume, a restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views_b.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front three-quarter from the figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, proportions, pose and colour authority. The faceting, blur and low resolution are NOT the design.
2. `mm9_chest_views_b.png`: closer renders of the coif, collar, blouse, bodice, arms and hands, same five views.
3. `mm9_head_views_b.png`: close renders of the head in its coif, same five views.
4. `mm9_skirt_views_b.png`: close renders of the apron, the long skirt, the hem and the shoes, same five views.
5. `mm9_skin_x4_b.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY (face, blouse, bodice, apron, skirt, arms, hands, shoes are laid out flat).
6. (run 2 only) the selected three-quarter master (`references_hd/00_three_quarter_clean.png` if it exists, else `00_three_quarter.png`). For 01-04 produce a TRUE transparent background with NO glow or halo around the figure.

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
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX peasant woman from the supplied renders of its original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine detail (soft linen with a visible weave, wool, fine folk embroidery, worn soft leather). ONE complete figure from the peak of the coif to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-4):
- A sturdy adult human WOMAN of about 55-60, about 1.76 m tall, ordinary matronly proportions, natural bust and waist, straight posture. Not a warrior, not glamorous.
- HEAD: a kind older woman with a broad soft face, fair skin with rosy cheeks, blue-grey eyes OPEN and clearly visible, straight nose, a friendly smile with the lips slightly parted. Grey-white hair parted in the middle, showing only at the forehead and temples under the coif. Ears hidden under the coif.
- COIF: a cream / off-white linen hood-like headdress that rises to a TALL POINTED PEAK above the crown (a stiff folded kerchief), frames the face closely at the forehead and cheeks, covers the ears, and falls straight down at the back and sides to the nape and shoulders, as input 3. It does not cover the face or the front of the neck.
- COLLAR: a narrow high standing collar round the neck, dark red and black folk embroidery, as inputs 2 and 3.
- BLOUSE: a cream linen blouse, finely gathered at the chest (the gathered blouse front shows in the open front of the bodice), with SHORT PUFFED SLEEVES ending above the elbow.
- BODICE: a sleeveless dark slate-teal / blue-green wool bodice (pinafore top) with wide shoulder straps and a deep open U front that shows the gathered blouse; its front edges carry a narrow dark red-brown embroidered trim with small round brass ornaments, as input 2. At the waist a dark red-brown embroidered waist band all round.
- ARMS: BARE forearms and the lower upper arms below the puffed sleeves, fair skin, a thin copper-brown bracelet round each wrist.
- HANDS: bare human hands with FIVE separate fingers (four fingers and a thumb), relaxed, slightly curled, open, clear air between the fingers, palms down. No gloves. Nothing in them.
- APRON: a cream / off-white linen apron in front, from the waist band to about two thirds of the way down the skirt (below the knees), a wide flat panel wrapping a little round the sides, soft vertical folds, plain, as input 4.
- SKIRT: a floor-length dark slate-teal wool skirt (same colour as the bodice), a gentle A-line from the waist to a straight hem just above the ankles, soft shallow vertical folds only, closed all round (no slit). Seen from the back it is all skirt; the apron is only at the front.
- SHOES: brown leather shoes with a rounded toe and a little tooled pattern; only their fronts show under the hem.
- COLOUR: as inputs 1 and 5: cream coif, blouse and apron, slate-teal bodice and skirt, dark red-brown embroidery, brown shoes. Flat even studio light, no baked shadows.
- No jewellery except the bracelets and embroidery, no belt pouch, no basket, no tools, no weapons, no cloak, no extra limbs, no bare legs.

Pose (identical in all views; EXACTLY the pose of input 1): standing upright and symmetrical, feet about 20 cm apart under the hem, toes forward, the skirt hanging straight; arms straight, out to the sides and sloping down about 30 degrees below horizontal, elbows nearly straight, wrists straight. Head level, looking straight ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: make her young; give her long sleeves or gloves; show ears or hair beyond the hairline; round off the peak of the coif; change the colours; make the apron reach the floor; add pleats, patterns or trims beyond those listed; crop any part; copy the blur or faceting.

Per-image checks (redo at most once): coif peak to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; open eyes; pointed cream coif; dark embroidered standing collar; short puffed cream sleeves and bare forearms with bracelets; slate-teal bodice with an open front showing the gathered blouse; cream apron in front only to below the knees; floor-length slate-teal skirt; shoes under the hem; the side views show the figure facing the stated image direction.
