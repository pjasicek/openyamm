# Codex brief: HD reference views for the MM9 Nobleman (mm9_nobleman_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_nobleman_claude/references_hd/`. Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and
Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an adult male nobleman in a rich medieval court costume, a restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views_a.png`: renders of the ORIGINAL low-poly model with its skin (tier "Baron"), five views left to right: front three-quarter from the
   figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout,
   proportions and colour authority. The faceting, blur and low resolution are NOT the design.
2. `mm9_waist_views_a.png`: close renders of the doublet, its skirt and the sleeves, same five views.
3. `mm9_head_views_a.png`: close renders of head and chest, same five views. Face, hair, collar, fur mantle and jewellery authority.
4. `mm9_skin_x4_a.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
5. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1536 PORTRAIT)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so all views are
the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then select the better and note any residual fault.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after run 2,
a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Baron" from the supplied renders of its original 3D model,
as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine
detail (gold thread embroidery, brocade weave, long fur, woven wool, individual hair strands). ONE complete figure from the crown to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-3):
- A tall, lean adult MALE human about 1.84 m tall, ordinary proportions, medium shoulders. No bodybuilder.
- HEAD: a handsome man about 35, straight nose, blue eyes, short golden-brown beard and moustache, chin complete, mouth closed. Thick golden blond hair in a straight bob, parted at the centre, hanging over the ears to the jaw line at the sides and to the nape at the back, a clean even lower edge, as in input 3.
- COLLAR: a tall stiff cream-white linen standing collar round the neck, open in a V at the throat, a gold chain necklace with an oval red gem pendant on the cream chest panel.
- FUR MANTLE: a thick short shoulder cape of golden-brown fur over both shoulders, upper chest and upper back, its ragged lower edge above the bust, standing proud of the shoulders with squared corners, as in input 3. Two round gold filigree brooches on the chest.
- DOUBLET: a deep burgundy-red brocade doublet with a small raised gold-black scale pattern, from the mantle to a short flared skirt that ends at the upper thigh, standing clear of the thighs, a closed tube round the hips with a wide embroidered gold hem. A wide gold embroidered band runs down the centre front from the brooches to the hem.
- BELT: a narrow brown leather belt with gold filigree plates at the sides and a square gold filigree buckle at the front.
- SLEEVES: long fitted sleeves to the wrist in panelled dark gold-and-burgundy brocade: long vertical burgundy slashes framed by dark gold bands, a gold band at the elbow, as in input 2. A short ruffled cream linen cuff shows at each wrist.
- HANDS: bare human hands with FIVE separate fingers (four fingers and a thumb), relaxed and slightly curled, clear air between the fingers. A gold ring on one finger is fine. No gloves. No weapons in them.
- LEGS: full dark maroon-black breeches, soft loose cloth, tapering to the shin, with a thin dark seam braid down the outside of each leg.
- BELOW THE KNEE: two narrow bands at the lower shin, burgundy and gold embroidered, as in input 1.
- SHOES: soft pointed dark red-brown leather shoes without heels.
- No cape to the ground, no hood, no armour plates, no pouches, no sword belt, no scabbard, no weapons, no extra limbs.

Pose (identical in all views, the model's bind pose made symmetric): standing upright, feet apart about 35 cm, toes pointing forward and slightly out; arms hanging down and away from the body about 20 degrees from vertical, elbows nearly straight, wrists straight, palms facing the thighs, clear air between arms and body. Exactly the same left and right.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add weapons, a long cloak or armour; change colours; crop any part; copy the blur or faceting; give him a modern look; make a crown or hat.

Per-image checks (redo at most once): crown to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; standing collar; fur mantle; pendant; belt with buckle; closed doublet skirt; panelled sleeves.
