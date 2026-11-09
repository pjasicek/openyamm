# Codex brief: HD reference views for MM9's Njam the Meddler (mm9_njam_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_njam_claude/references_hd/`. Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and
Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an adult male courtier (a trickster god in human form) in a rich medieval costume, a restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front three-quarter from the
   figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout,
   proportions and colour authority. The faceting, blur, low resolution and the T-pose arms are NOT the design.
2. `mm9_waist_views.png`: close renders of the coat, tunic, belt and sleeves, same five views.
3. `mm9_head_views.png`: close renders of head and chest, same five views. Face, hair, collar, fur yoke and jewellery authority.
4. `mm9_skin_x4.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
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
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Njam the Meddler" from the supplied renders of its original 3D model,
as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine
detail (gold thread embroidery, green scale-pattern brocade, long fur, wool, individual hair strands). ONE complete figure from the crown to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-3):
- A tall, lean adult MALE human about 1.80 m tall, ordinary proportions, narrow shoulders, long legs. No bodybuilder.
- HEAD: a lean man about 35 with a long narrow face, high cheekbones, a long straight nose, pale green-blue eyes, a sly knowing half-smile with the mouth CLOSED, light stubble on the jaw, no full beard, no moustache, complete chin. Thick medium-brown hair in a pageboy bob: a straight fringe across the forehead above the eyebrows, hanging over the ears to the jaw line at the sides and to the nape at the back, a clean even lower edge, as in input 3.
- COLLAR: a cream-white linen shirt collar open in a V at the throat, edged with a thin gold braid.
- FUR YOKE: a short golden-brown fur yoke over both shoulders, the upper chest and the upper back (to the shoulder blades), the coat's front edges trimmed with the same fur down to the hem, as in inputs 2 and 3.
- JEWELLERY: a gold filigree pendant with an oval GREEN gem at the base of the V collar, and two round gold filigree brooches on the chest left and right of it.
- COAT: a long fitted open-front coat of deep bottle-green brocade with a small raised scale pattern, sleeveless at the front opening, its skirt reaching mid-thigh, fur-trimmed front edges; at the back a band of fur across the hem.
- TUNIC under the coat: deep red-burgundy, with a narrow gold embroidered band down the centre front from the pendant to the belt; below the belt a short flared tunic skirt to mid-thigh with a brown fur-brocade panel, a red band and a gold embroidered hem. Coat and tunic skirts together form a closed flared tube round the hips, standing clear of the thighs.
- BELT: a black leather belt with small silver studs and a square gold filigree buckle at the front.
- SLEEVES: green brocade from the shoulder to the elbow, a gold band at the elbow, then from the elbow to the wrist a panelled red-and-gold brocade forearm with gold bands, as in input 2. A short cream linen cuff shows at each wrist.
- HANDS: bare human hands with FIVE separate fingers (four fingers and a thumb), relaxed and slightly curled, clear air between the fingers. No gloves. No rings. Nothing held.
- LEGS: fitted dark bottle-green hose, smooth, slim.
- BOOTS: knee-high dark brown leather boots with a turned-down tawny fur-and-gold cuff below the knee, a thin gold band round the ankle, soft rounded toes, low heels.
- No cape, no hood, no hat or crown, no armour plates, no pouches, no sword belt, no scabbard, no weapons, no staff, no extra limbs.

Pose (identical in all views, the model's bind pose made symmetric): standing upright, feet apart about 30 cm, toes pointing forward and slightly out; arms hanging down and away from the body about 30 degrees from vertical, elbows nearly straight, wrists straight, palms facing the thighs, clear air between arms and coat. Exactly the same left and right.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add weapons, a cloak or armour; change colours (green coat and hose, red tunic, brown boots and hair, golden fur); crop any part; copy the blur or faceting; give him a modern look; add a beard, a hat or a crown.

Per-image checks (redo at most once): crown to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; V collar; fur yoke; green pendant and two brooches; belt with buckle; closed flared skirt; two-part sleeves; boots with fur cuffs.
