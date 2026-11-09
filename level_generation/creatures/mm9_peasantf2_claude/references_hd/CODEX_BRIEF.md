# Codex brief: HD reference views for the MM9 human townswoman PeasantF2 (mm9_peasantf2_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantf2_claude/references_hd/`. Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an adult human town woman in a plain medieval folk dress, a restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views_a.png`: renders of the ORIGINAL low-poly model with its skin A, five views left to right: front three-quarter from the figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, proportions, pose and colour authority. The faceting, blur and low resolution are NOT the design.
2. `mm9_chest_views_a.png`: closer renders of the hair, neckline, chemise, bodice, sleeves and hands, same five views.
3. `mm9_head_views_a.png`: close renders of the head, hair and braid, same five views.
4. `mm9_skirt_views_a.png`: close renders of the apron, the long skirt, the hem and the shoes, same five views.
5. `mm9_skin_x4_a.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY (face and hair, chemise, cuffs, hands, ear, shoes, apron and skirt are laid out flat).
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
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX town woman from the supplied renders of its original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine detail (soft linen with a visible weave, wool, gold brocade, worn soft leather). ONE complete figure from the top of the head to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-4):
- A slim adult human WOMAN of about 30, about 1.76 m tall, ordinary natural proportions, natural bust and waist, straight posture. Not a warrior, not glamorous.
- HEAD: a pretty, calm, warm and friendly face, fair skin with light freckles on the nose and cheeks, green-grey eyes OPEN and clearly visible, straight nose, a gentle closed-lip smile. Not fierce, not cold.
- HAIR: golden-blonde to strawberry-blond hair, parted in the middle, combed smoothly and closely over the skull and pulled back so it covers the ears completely, gathered at the nape into ONE thick plait (braid) that hangs down the middle of her back to about the shoulder blades, as input 3. The hair is close to the head (a neat smooth rounded cap of hair), not big, not loose.
- NECKLACE: a short necklace of small round copper-amber beads with a small pendant at the throat.
- NECKLINE: a wide scoop / V neckline edged with a broad band of GOLD-OCHRE brocade embroidery, showing a cream-white linen chemise with fine vertical gathers and a little embroidery in the front opening, as input 2.
- DRESS: a rust-orange / burnt-orange wool dress with a fitted bodice, LONG SLEEVES, fitted on the upper arm and widening into FLARED BELL CUFFS of gold-ochre brocade from about the middle of the forearm, open at the wrist so the hands come out of them, as inputs 1 and 2. At the waist a narrow gold-and-ochre embroidered belt with a small buckle plate all round.
- HANDS: bare human hands with FIVE separate fingers (four fingers and a thumb), relaxed, slightly curled, open, clear air between the fingers, palms down. No gloves. Nothing in them.
- APRON: a cream / light beige linen apron in front, from the belt to just below the knees, a wide flat panel wrapping a little round the sides, soft vertical folds, plain, as input 4.
- SKIRT: a floor-length rust-orange wool skirt (same colour as the bodice), a gentle A-line from the waist to a straight hem just above the ankles, soft shallow vertical folds only, closed all round (no slit). Seen from the back it is all skirt; the apron is only at the front.
- SHOES: brown-red leather shoes with a rounded toe and a little tooled pattern; only their fronts show under the hem.
- COLOUR: as inputs 1 and 5: golden-blonde hair, rust-orange dress, gold-ochre cuffs and neckline band, cream chemise and apron, brown shoes. Flat even studio light, no baked shadows.
- No jewellery except the necklace, no belt pouch, no basket, no tools, no weapons, no cloak, no hat, no extra limbs, no bare legs.

Pose (identical in all views; EXACTLY the pose of input 1): standing upright and symmetrical, feet about 20 cm apart under the hem, toes forward, the skirt hanging straight; arms straight, out to the sides and sloping down about 35 degrees below horizontal, elbows nearly straight, wrists straight; the bell cuffs hang open round the forearms without touching the body. Head level, looking straight ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: give her short sleeves or bare forearms; make the cuffs tight; show her ears; make the hair loose, big or a bun on top; add a second braid; change the colours; make the apron reach the floor; add pleats, patterns or trims beyond those listed; crop any part; copy the blur or faceting; give her a fierce or cold look.

Per-image checks (redo at most once): head top to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; open eyes; calm warm expression; smooth close blonde hair over the ears; one braid down the back; gold brocade neckline band with the cream gathered chemise; long rust sleeves with gold flared bell cuffs from mid-forearm; belt; cream apron in front only to below the knees; floor-length rust skirt; shoes under the hem; the side views show the figure facing the stated image direction.
