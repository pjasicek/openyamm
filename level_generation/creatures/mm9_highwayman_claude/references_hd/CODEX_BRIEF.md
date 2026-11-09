# Codex brief: HD reference views for the MM9 Highwayman (mm9_highwayman_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_highwayman_claude/references_hd/`. Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and
Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an adult male travelling rogue in leather and cloth clothes, a restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views_a.png`: renders of the ORIGINAL low-poly model with its skin (tier "Cutpurse"), five views left to right: front three-quarter from the
   figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, POSE,
   proportions and colour authority. The faceting, blur and low resolution are NOT the design.
2. `mm9_waist_views_a.png`: close renders of the tunic and its skirt, same five views.
3. `mm9_head_views_a.png`: close renders of head and chest: front, three-quarter, left, back, right. Face, hair, headband, collar and brooch authority.
4. `mm9_skin_x4_a.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
5. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1536x1024 LANDSCAPE so the outstretched arms fit)
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
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Cutpurse" from the supplied renders of its original 3D model,
as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine
detail (stitching, pebbled leather, woven wool, individual hair strands). ONE complete figure from the crown to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-3):
- A lean, athletic adult MALE human about 1.86 m tall, ordinary proportions, medium shoulders. No bodybuilder.
- HEAD: an ordinary handsome rugged man, straight nose, blue eyes, short ginger-blond beard and moustache, chin complete, mouth closed. Long thick dark-blond hair, parted at the centre, hanging straight down over the ears to the jaw line and at the back to the nape, as in input 3. Across the forehead a black leather HEADBAND with a dark metal central clasp.
- YOKE: over chest, upper back and top of the shoulders a dark olive-green woollen yoke with a V neck, edged all round with a wide band of tan-brown pebbled leather, ending in a low pointed V on the chest and on the back, its squared shoulder corners standing a little proud, as in input 3. A bare V of skin at the throat. On the chest below the V an ornate silver filigree brooch with a short chain.
- TUNIC: under the yoke, a red-brown leather tunic with diagonal diamond quilting, from the yoke to a short skirt that ends at the upper-middle thigh, slightly flared and standing clear of the thighs, a closed tube round the hips, with a narrow pebbled leather hem. A thin laced slit below the V on the chest. Slits at the hip are NOT present.
- BELT: a dark red-brown leather belt with two thin gold lines, small silver studs, and an ornate square silver buckle at the front.
- SLEEVES: short red-brown quilted leather sleeve caps at the shoulder, then long olive-green wool sleeves to the elbow and below, then on each forearm a stiff embroidered gold-and-brown cuff, a thin gold band at its upper edge, as in input 1.
- HANDS: strong bare human hands with FIVE separate fingers (four fingers and a thumb), relaxed and slightly curled, clear air between the fingers. No gloves. No weapons in them.
- LEGS: slim very dark brown leather trousers, tight on the leg, ending inside the boots.
- BOOTS: brown leather boots to below the knee, wide stiff flared tops turned down with two rows of straps and small silver studs at the upper shin as in input 1, a strap with a silver buckle over the ankle, thick soles.
- No cape, no hood, no armour plates, no pouches, no sword belt, no scabbard, no weapons, no extra limbs.

Pose (identical in all views, the model's bind pose as in input 1): standing upright, feet apart (about 45 cm between the feet), toes pointing forward; arms straight out to the sides and down at about 20 degrees BELOW horizontal, slightly forward, elbows nearly straight, wrists straight, clear air between arms and body.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add weapons, a cloak or armour; change colours; crop any part; copy the blur or faceting; give him a modern look.

Per-image checks (redo at most once): crown to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; headband with clasp; yoke with V; brooch; belt with buckle; closed tunic skirt; flared boots with straps.
