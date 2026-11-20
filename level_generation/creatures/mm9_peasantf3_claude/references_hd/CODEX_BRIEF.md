# Codex brief: HD reference views for the MM9 human peasant woman PeasantF1 (mm9_peasantf1_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantf1_claude/references_hd/`. Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an older adult human village woman in plain medieval peasant clothes, a restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views_b.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front three-quarter from the figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, proportions, pose and colour authority. The faceting, blur and low resolution are NOT the design.
2. `mm9_chest_views_b.png`: closer renders of the hood, blouse, bodice, sleeves and arms, same five views.
3. `mm9_head_views_b.png`: close renders of the head in its hood, same five views.
4. `mm9_skirt_views_b.png`: close renders of the apron, the long skirt, the hem and the shoes, same five views.
5. `mm9_skin_x4_b.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY (face, hood, bodice with lacing, blouse, arm, hands, shoes, apron, skirt laid out flat).
6. (run 2 only) the selected three-quarter master (`references_hd/00_three_quarter_clean.png`, its halo removed; keep `00_three_quarter.png` as it is). For 01-04 produce a TRUE transparent background with NO glow or halo around the figure.

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
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX human peasant woman from the supplied renders of its original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine detail (soft wool and linen with a visible weave, leather lacing, worn soft leather shoes). ONE complete figure from the peak of the hood to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-4):
- A sturdy adult human WOMAN about 1.72 m tall, ordinary womanly proportions, natural bust and waist, straight posture. Not a warrior, not glamorous.
- HEAD: a kindly woman of about 55, fair skin with soft wrinkles at the eyes, rosy cheeks, hazel eyes, a broad warm smile with the lips CLOSED (no teeth), red lips. Grey-brown hair with grey at the temples, combed back in soft waves, showing only as a band at the forehead and temples under the hood.
- HOOD: a stiff ochre / honey-brown cloth hood (a folded kerchief) covering the top, sides and back of the head and the ears; at the top it rises to a soft blunt peak; it frames the face closely and falls straight down behind the head and at the sides to the shoulders as a flat curtain, as input 3. It does not cover the face or the front of the neck. No ears visible.
- BLOUSE: a cream / off-white linen blouse with a small standing collar closed at the throat with a short V-slit at the front, visible above the bodice and at the shoulders.
- SLEEVES: SHORT puffed cream linen sleeves ending just above the elbow with a loose ruffled edge. The forearms and hands are BARE skin.
- BODICE: a fitted rust-orange / red-orange wool bodice (a laced vest) from under the bust-line straps over the shoulders to the waist; a scooped neckline front and back, with dark leather LACING criss-crossing down the front centre through small metal eyelets, as inputs 2 and 5.
- HANDS: bare human hands with FIVE separate fingers (four fingers and a thumb), relaxed, slightly curled, open, clear air between the fingers, palms down. Nothing in them.
- WAIST: the apron's narrow cream waistband round the waist under the bodice.
- APRON: a cream / off-white linen apron from the waist band covering the front and the sides of the skirt down to just below the knees, a flat wide panel with soft vertical folds, plain, as input 4.
- SKIRT: a floor-length dark red-brown (maroon) wool skirt, a straight gentle A-line from the waist to a straight hem just above the ankles, soft shallow vertical folds only, closed all round (no slit). Seen from the back it is all skirt; the apron is only at the front and sides.
- SHOES: plain soft brown leather shoes with a rounded toe; only their fronts show under the hem.
- COLOUR: as inputs 1 and 5: rust-orange bodice, honey-brown hood, cream blouse and apron, maroon skirt, brown shoes. Flat even studio light, no baked shadows.
- No jewellery, no belt pouch, no basket, no tools, no weapons, no cloak, no extra limbs, no bare legs.

Pose (identical in all views; EXACTLY the pose of input 1): standing upright and symmetrical, feet about 20 cm apart under the hem, toes forward, the skirt hanging straight; arms straight, out to the sides and sloping down about 30 degrees below horizontal, elbows nearly straight, wrists straight. Head level, looking straight ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: make her young; open the mouth or show teeth; add a veil, braids or visible ears; make the sleeves long; change the colours; make the apron reach the floor; add pleats, patterns or trims beyond the lacing; crop any part; copy the blur or faceting.

Per-image checks (redo at most once): hood peak to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; an older smiling woman with closed lips; short puffed cream sleeves and bare forearms; laced rust-orange bodice; cream apron in front only to below the knees; floor-length maroon skirt; shoes under the hem; the side views show the figure facing the stated image direction.
