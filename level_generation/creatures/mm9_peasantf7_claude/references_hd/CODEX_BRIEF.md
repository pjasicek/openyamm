# Codex brief: HD reference views for the MM9 elf townswoman PeasantF7 (mm9_peasantf7_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantf7_claude/references_hd/`. Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an adult elf town woman in a plain medieval folk dress, a restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views_a.png`: renders of the ORIGINAL low-poly model with its skin A, five views left to right: front three-quarter from the figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, proportions, pose and colour authority. The faceting, blur and low resolution are NOT the design.
2. `mm9_chest_views_a.png`: closer renders of the hair, braids, neckline, chemise, pinafore bodice, arms and hands, same five views.
3. `mm9_head_views_a.png`: close renders of the head, the long hair and the two braids, same five views.
4. `mm9_skirt_views_a.png`: close renders of the apron, the long skirt, the hem and the shoes, same five views.
5. `mm9_skin_x4_a.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY (face and hair, chemise, arms, hands, braid, shoes, apron and skirt are laid out flat).
6. (run 2 only) the selected three-quarter master (`references_hd/00_three_quarter_clean.png`, halo removed). For 01-04 produce a TRUE transparent background with NO glow or halo around the figure.

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
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX elf town woman from the supplied renders of its original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine detail (soft linen with a visible weave, wool, worn soft leather, hair strands). ONE complete figure from the top of the head to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-4):
- A slim young adult ELF WOMAN of about 25, about 1.76 m tall, natural feminine proportions, a full natural bust and slim waist, straight posture. Not a warrior, not glamorous.
- HEAD: a sweet, calm, warm and friendly face, fair skin with light freckles across the nose and cheeks, green eyes OPEN and clearly visible, a small straight nose, a gentle closed-lip smile. Not fierce, not cold.
- HAIR: long straight copper-orange / ginger hair, parted in the middle, falling smoothly over the ears (the ears are completely covered) and down the back as one smooth sheet to the middle of the back (a pointed tip below the shoulder blades), as inputs 1 and 3. In front, one THIN PLAIT (braid) on each side starts at the temple and hangs down in front of each shoulder onto the chest, as input 3.
- NECKLACE: a thin copper chain necklace in a V at the collarbones.
- CHEMISE: a cream-white linen chemise with a scoop neck and SHORT SLEEVES to just above the elbow, each sleeve ending in a narrow grey-white band, as input 2.
- PINAFORE: a sleeveless yellow-green / olive-green wool dress (pinafore) over the chemise, with wide shoulder straps and a low scoop front that shows the chemise at the neckline, fitted bodice; a thin cream-grey belt at the waist.
- ARMS: BARE forearms below the short sleeves, fair skin, a thin copper-brown bracelet round each wrist.
- HANDS: bare human hands with FIVE separate fingers (four fingers and a thumb), relaxed, slightly curled, open, clear air between the fingers, palms down. No gloves. Nothing in them.
- APRON: a cream / off-white linen apron in front, from the belt to just below the knees, a wide flat panel wrapping a little round the sides, soft vertical folds, plain, as input 4.
- SKIRT: a floor-length yellow-green wool skirt (same colour as the pinafore), a gentle A-line from the waist to a straight hem just above the ankles, soft shallow vertical folds only, closed all round (no slit). Seen from the back it is all skirt and hair; the apron is only at the front.
- SHOES: brown leather shoes with a rounded toe; only their fronts show under the hem.
- COLOUR: as inputs 1 and 5: copper-ginger hair, yellow-green pinafore and skirt, cream chemise and apron, brown shoes. Flat even studio light, no baked shadows.
- No jewellery except the necklace and bracelets, no belt pouch, no basket, no tools, no weapons, no cloak, no hat, no extra limbs, no bare legs.

Pose (identical in all views; EXACTLY the pose of input 1): standing upright and symmetrical, feet about 20 cm apart under the hem, toes forward, the skirt hanging straight; arms straight, out to the sides and sloping down about 30 degrees below horizontal, elbows nearly straight, wrists straight. Head level, looking straight ahead. The long hair hangs straight down the back; the front braids hang in front of the shoulders.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: show her ears; give her long sleeves; make the hair curly or wavy or blow it about; put the braids behind the shoulders; change the colours; make the apron reach the floor; add pleats, patterns or trims beyond those listed; crop any part; copy the blur or faceting; give her a fierce or cold look.

Per-image checks (redo at most once): head top to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; open eyes; calm warm expression; long straight ginger hair covering the ears and down the back; two thin braids in front of the shoulders; cream short-sleeved chemise; green sleeveless pinafore with scoop neck; bare forearms with bracelets; belt; cream apron in front only to below the knees; floor-length green skirt; shoes under the hem; the side views show the figure facing the stated image direction.
