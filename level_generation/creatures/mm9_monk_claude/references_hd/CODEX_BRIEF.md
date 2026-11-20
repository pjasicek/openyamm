# Codex brief: HD reference views for the MM9 Monk (mm9_monk_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_monk_claude/references_hd/`. Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an adult male medieval monk in a plain wool habit, a restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views_a.png`: renders of the ORIGINAL low-poly model with its skin (tier "Initiate"), five views left to right: front three-quarter from the figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, proportions, pose and colour authority. The faceting, blur and low resolution are NOT the design.
2. `mm9_chest_views_a.png`: closer renders of the hood, mantle, sleeves and hands, same five views.
3. `mm9_head_views_a.png`: close renders of the head in the hood, same five views.
4. `mm9_waist_views_a.png`: close renders of the rope belt and its two hanging cords, same five views.
5. `mm9_hem_views_a.png`: close renders of the lower robe, the hem and the shoes, same five views.
6. `mm9_skin_x4_a.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
7. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1536 PORTRAIT)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so all views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Monk" from the supplied renders of its original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine detail (coarse woven wool with a visible linen-like weave, twisted hemp rope, soft worn leather). ONE complete figure from the hood's point to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-5):
- A lean, tall adult MALE human about 1.87 m tall including the hood, ordinary proportions, straight narrow body. No bodybuilder, no big belly.
- HOOD: a deep pointed wool cowl, one piece with the mantle. Its point rises at the top of the head, a little behind the crown, a stiff soft peak. The hood's opening is a tight pointed oval round the face with a thick rolled edge; the inside of the hood is dark. The hood is up, always.
- HEAD: a stern man of about 45 with short black hair showing at the forehead under the hood, blue eyes, strong brows, straight nose, closed mouth, a very small goatee on the chin only. Chin complete. The neck shows only as a small V under the chin.
- MANTLE: a short wool cape, one piece with the hood, lies over the shoulders and the upper chest and upper back, and ends in a clear soft straight lower edge across the chest and the back at the height of the armpits, standing about 1.5 cm proud of the robe below it, as inputs 1-2.
- ROBE: one closed floor-length wool tube from the chest to the ankles, no opening, no skirt split, narrow at the waist and widening gently down to a plain straight hem, soft shallow vertical folds only, a wide even A-line, as inputs 1 and 5. There are NO deep pleats.
- SLEEVES: long wide straight wool sleeves, each a stiff open cone COAXIAL WITH THE ARM (the sleeve does NOT hang down below the arm), widening gently from the shoulder to a straight open cuff that ends a hand's length before the wrist bones, the mouth of the sleeve clearly open and dark inside, with clear air between the cuff and the forearm, as input 2.
- FOREARMS AND HANDS: the bare forearm and wrist come out of the cuff. Bare strong human hands with FIVE separate fingers (four fingers and a thumb), relaxed, slightly curled, open, clear air between the fingers, palms down and slightly forward. No gloves. Nothing in them.
- ROPE BELT: a thick twisted hemp rope, tan and honey coloured, wound once round the waist, tied at the centre of the front, with TWO separate thick twisted rope ends hanging straight down the front of the robe side by side, about 8 cm apart, to about mid thigh, each ending in a knot and a short frayed tip, as input 4. The rope is a separate thick object, clearly standing on the robe.
- SHOES: plain soft leather ankle shoes with a rounded toe; only their fronts show under the hem, as input 5.
- COLOUR: warm mid brown wool, as input 6, flat and even; tan hemp rope; warm tan leather shoes.
- No staff, no cross, no book, no beads, no pouch, no sword, no extra limbs, no bare legs.

Pose (identical in all views; EXACTLY the pose of input 1): standing upright and symmetrical, feet about 24 cm apart under the hem, toes forward, the robe hanging straight; arms straight, out to the sides and sloping down about 25 degrees below horizontal, elbows nearly straight, wrists straight. Head level, looking straight ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: lower the hood; add pleats, patterns, trims, embroidery; make the sleeves droop into hanging bags; merge the rope into the robe; change colours; crop any part; copy the blur or faceting.

Per-image checks (redo at most once): hood point to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; open cuffs with a dark inside; bare forearm in each cuff; a rope tied at the front with two hanging ends; mantle edge across chest and back; closed robe; shoes under the hem.
