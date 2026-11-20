# Codex brief: HD reference views for the MM9 Lizard-Orc (mm9_lizardorc_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_lizardorc_claude/references_hd/` (run 3: `level_generation/creatures/mm9_lizardorc_claude/references_head/`). Do not edit any other file, do not run builds,
do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a non-human fantasy reptile warrior in plate armour from a 2002 video game, restored for a game mod.

## Inputs (attached, in order)
1. `mm9_views.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front three-quarter from the figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT),
   back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, POSE, proportions and colour authority. Faceting, blur, mirrored-texture seams and low resolution are NOT the design. It holds no weapon here.
2. `mm9_head_views.png`: close renders of the head, neck and shoulders, same five views.
3. `mm9_skin_x4.png`: the original 256x256 skin enlarged: SURFACE MATERIAL AND COLOUR ONLY.
4. (runs 2, 3) the selected `00_three_quarter.png`.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns)
| Run | File | Canvas | View |
|---|---|---|---|
| 1 | `00_three_quarter.png` | 1024x1536 | front three-quarter from the figure's RIGHT, camera at chest height, slightly above (as input 1 view 1) |
| 2 | `01_front.png` | 1024x1536 | straight front |
| 2 | `02_back.png` | 1024x1536 | straight back |
| 2 | `03_left.png` | 1024x1536 | pure 90-degree profile of the figure's LEFT side: it faces IMAGE LEFT |
| 2 | `04_right.png` | 1024x1536 | pure 90-degree profile of the figure's RIGHT side: it faces IMAGE RIGHT |
| 3 | `../references_head/00_q34.png`, `01_front.png`, `02_left.png`, `03_back.png`, `04_right.png` | 1254x1254 | head only, mouth open, see run 3 below |

Run 1: generate `00_three_quarter.png` only, then stop. Later runs (separate runs): use the selected 00 as an additional input so all views are the SAME figure, SAME pose, SAME proportions and colours.
At most ONE corrective regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Lizard-Orc" from the supplied renders of its original 3D model, as a 3D modelling and texturing reference. Not a new design.
A credible, fully three-dimensional creature with semi-realistic game materials and sharp fine detail. ONE complete figure from the crest to the toes and the tail tip, centred, generous margins, never cropped.

Identity (exactly the layout of inputs 1-3):
- A tall, broad-shouldered upright reptile warrior, about 1.9 m, narrow waist, long legs, a long tail. NOT a human.
- HEAD: a long heavy crocodile-tyrannosaur head thrust FORWARD and level on a long neck; the neck rises from the chest and curves forward. The UPPER half of the head (skull and snout) is entirely covered by a grey steel HELM forged like a beast's skull: long snout plates,
  a brow ridge over each eye, two swept-back blade crests at the rear that give the head a wide "W" outline from the front, and a row of small sharp steel teeth along the helm's lower edge. Inside each eye opening: green scaly lid skin and a small glowing orange-red slit reptile eye.
- JAW: the LOWER jaw is bare hide, long and heavy: green on the sides, pale yellow-olive under the chin. Two curved ivory fangs stand up at its tip and a row of small teeth along it. The mouth stands OPEN about 25 degrees as in input 2; inside blood red and dark red, with a long thick red forked tongue lying on the jaw.
- NECK: bare, thick, scaly: vivid green at the back and sides, pale yellow-olive on the throat, wrinkled.
- CHEST: a dark grey steel BREASTPLATE fanned from a central lighter vertical plate with bright raised edges and small rivets. It has a V neckline with a thin red-brown leather edge. CHAINMAIL (fine grey rings) wraps the ribs on both sides. The BACKPLATE is steel with a symmetric embossed demon-mask pattern over chainmail.
- PAULDRONS: one huge round steel dome on each shoulder, wider than the head, with a bright rolled rim and three or four short conical spikes.
- WAIST: a narrow band of bare hide above the belt. BELT: red-brown leather with round steel studs and a small horned-skull buckle at the front.
- HIPS: laminated steel tassets over the hips and upper thighs, with chainmail bands. Front: a long pointed steel flap embossed with a horned skull hanging between the legs. Back: the same lames over the top of the tail.
- ARMS: bare muscular upper arms, olive to yellow-green with fine scales, held away from the body and down about 45 degrees from horizontal, as in input 1. FOREARMS: wide flared polished-steel bracers that cover the whole forearm, each with a red-brown leather strap with oval steel studs at the wrist end and elbow end.
- HANDS: scaly olive reptile hands: EXACTLY three long thick fingers plus one thumb, open and spread with air between them, each ending in a long dark brown claw, as in input 1. The hands are EMPTY.
- THIGHS: bare scaly hide, deep green at the outside and back, pale yellow-olive at the front, with one red-brown leather band with round steel studs around each thigh at mid height. KNEES bare.
- SHINS: shield-shaped polished steel greaves, orange-brown leather top edge, chainmail on the back of the calf and around the ankle.
- FEET: big scaly reptile feet, flat on the floor, olive with yellow highlights, three thick forward toes with short blunt ivory claws and a short rear spur, slightly splayed outward.
- TAIL: one long tapering tail growing from under the back of the hips, hanging down and back in a straight line to a sharp point about shin height, as in the side views of input 1. Vivid green with a chevron scale pattern.
- MATERIALS: worn dark steel, soft highlights, no gold. Fine reptile scales on all bare hide; no bright speculars.

Pose (identical in all views, the model's bind pose as in input 1): standing straight, weight on both feet, feet shoulder-width apart, gap between the legs; arms held out and down, about 45 degrees from horizontal, with clear air between arms and body; fingers spread; the neck forward; the tail straight down and back.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT (runs 1, 2): add a weapon, shield, cape, hair, ears, extra limbs; add gold; change colours; crop any part; copy the blur or the mirrored seams of the low-poly skin; give it a human face.

Run 3 only, the head study: the HEAD ONLY with about 25 cm of neck, severed cleanly with a simple flat cut (hide colour, no shoulders, no armour below the head), floating on transparency, neck axis as in input 2. The mouth is open WIDER than in the body views, about 40 degrees, hinged at the mouth corners far back on the head, so the whole inside can be seen:
- PALATE: the underside of the helm's snout is a concave blood-red fleshy roof with ridges; a row of small sharp ivory-steel teeth along its rim; a dark throat opening at the back.
- LOWER JAW: a deep trough of the same width as the upper jaw, outside bare green hide and pale yellow-olive underneath, inside dark red; a row of small teeth along its rim; two big curved ivory fangs standing up at its tip.
- NO TONGUE in this study: the floor of the mouth is a smooth dark-red surface (the tongue is built separately).
- Thick dark-red and green lip folds at the mouth corners join upper and lower jaw: a real closed hinge, no long membrane.
- Eyes, helm and crest as in 00.
Views: `00_q34` from the front 3/4 on the head's right, `01_front` straight at the mouth, `02_left` pure profile facing IMAGE LEFT, `03_back` from behind, `04_right` pure profile facing IMAGE RIGHT. All five the same head, same gape.

Per-image checks (redo at most once): crest to toes and tail tip in frame; true alpha; three fingers plus thumb on each visible hand with air between them; no weapon; pauldrons symmetric; tail present; helm on the upper head, bare jaw below.
