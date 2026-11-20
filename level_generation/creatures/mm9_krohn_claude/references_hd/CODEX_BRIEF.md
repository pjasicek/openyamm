# Codex brief: HD reference views for MM9 Krohn (skin KROHN) (mm9_krohn_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_krohn_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_k.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter (he faces image right and toward the viewer), front, side facing
   IMAGE LEFT, back, side facing IMAGE RIGHT. Flat grey is background. This is the design, costume, POSE, proportions
   and colour authority. Its faceting, blur and low resolution are NOT the design. (The model's spear and sword were
   hidden for these renders on purpose: the character is drawn WITHOUT any weapon.)
2. `references_hd/mm9_head_views_k.png` — close renders of the same model's head (front, profile facing left,
   three-quarter, profile facing right, back): the face, crown, hair and beard authority.
3. `references_hd/mm9_skin_x4_k.png` — the original 256x256 skin texture enlarged, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, beard, hair, crown, chain mail, scale skirt, fur, belt with the ram buckle, baldric strap, skin).
   Never the design or shape.
4. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1536x1024 landscape so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter as input 1 view 1 (he faces image right and toward the viewer), camera at chest height slightly above |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree side profile facing IMAGE LEFT (as input 1 view 3) |
| `04_right.png` | pure 90-degree side profile facing IMAGE RIGHT (as input 1 view 5) |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME character, SAME pose, SAME proportions and colours. At most ONE
corrective regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`.
Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs)
and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and
Magic IX character from the supplied renders of its original 3D model, as a 3D modelling and texturing reference.
Not a new design. A credible, fully three-dimensional character with semi-realistic game materials and sharp fine
detail (skin pores and muscle definition, face, beard and hair strands, fur, chain-mail rings, overlapping scales,
leather grain, embossed gold), as if a high-quality sculpt of the original model. ONE complete figure from the top of
the crown to the soles, centred, generous margins, never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing upright; the arms held out to the sides
as in input 1 (straight, about 35 degrees below horizontal), clear air between the arms and the body; hands open
and flat, palms facing DOWN, the four fingers straight and close together with small gaps, the thumb separated; legs
straight and slightly apart with a clear gap between them, feet flat. Head level, looking forward. The long hair
falls down the back, NOT over the shoulders or chest.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; the pose above (arms out,
open flat hands with five fingers each, legs apart); the correct side faces the correct image side (03: faces IMAGE
LEFT; 04: faces IMAGE RIGHT); NO weapon anywhere; whole figure inside the frame with margins; true transparent
background; 1536x1024.

## Identity
Krohn, an old Norse warrior god-king: a huge, powerfully built man of about sixty with heavy shoulders, thick muscular
bare arms and strong legs; upright, dignified and calm.
- Face and head (inputs 2, 3): weathered, tanned fair skin with warm ruddy cheeks, a strong straight nose, deep-set
  clear pale BLUE eyes, BOTH fully open with visible irises; thick grey-brown brows, relaxed (not knitted, not angry);
  a calm, warm, kindly expression with a gentle closed-mouth hint of a smile; faint lines at the eyes and on the
  forehead. A FULL long beard and moustache, brown streaked with grey and white, reaching to the upper chest, the
  mouth visible. Long straight dark-brown hair from a centre parting, falling behind the ears and down the back to the
  shoulder blades. On his head a GOLD CROWN: a band of embossed gold set with small jewels, with three tall pointed gold
  spikes (one at the front centre, one at each temple) and smaller points between.
- Costume:
  - a short-sleeveless chest piece of BLUE-GREY steel CHAIN MAIL down the chest and belly, continuing below the belt
    as a long pointed mail tabard panel hanging to the knees at the front, edged with narrow gold-olive trim;
  - over the shoulders a short brown FUR mantle (shoulder caps and collar), the shoulder caps on the outside of each
    upper arm marked with a gold chevron trim; at the back a broad brown fur cape/pelt hanging from the shoulders to
    the hips, tapering to a point;
  - a dark leather BALDRIC strap with gold studs and a gold buckle running diagonally across the chest, from a round
    gold Celtic-knot medallion on the character's LEFT shoulder (image right in the front view) down to the belt;
  - a wide dark-red leather BELT with gold edges and round gold studs, its large GOLD RAM-HEAD buckle at the front
    centre (curled horns, small blue-glinting eyes);
  - below the belt at the sides and back a short skirt of olive-gold overlapping SCALES/mail to mid-thigh with a gold
    lower edge, over a ragged brown FUR under-skirt; a brown fur loincloth flap at the back tapering to a point;
  - BARE arms: a narrow gold-and-brown band round each upper arm, and on each forearm an ornate embossed gold-and-brown
    leather BRACER from mid-forearm to the wrist; bare hands;
  - bare muscular thighs and knees above ornate embossed GOLD GREAVES that cover the knees and shins (a lion/beast
    face embossed at each knee), the back of the calf wrapped in striped brown fur;
  - plain dark-brown leather boots with soft rounded toes and flat soles.

## Do NOT
- add ANY weapon, shield, scabbard or sword hilt, spear or staff; add a helmet, cloak hood, gloves, sleeves or
  trousers; drop the crown, beard, chain mail, ram buckle, baldric, fur mantle, fur cape, scale skirt, bracers or
  greaves; change colours (blue-grey mail, olive-gold scales, brown fur, gold crown and greaves, brown hair, grey-streaked
  beard); make him young, thin or cartoonish; angry, fierce, squinting or closed eyes; bring the hair forward over
  the chest; change the pose; crop.
