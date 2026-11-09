# Codex brief: HD reference views for MM9's PeasantM2 townsman (mm9_peasantm2_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm2_claude/references_hd/`. Do not edit any other file,
do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the
ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an elderly male townsman (a commoner) in simple medieval clothes, a restoration of an existing 2002
game character for a game mod.

## Inputs (attached, in order)
1. `mm9_full_views_a_half.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front three-quarter from the
   figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design,
   layout, proportions and colour authority. The faceting, blur, low resolution and the T-pose arms are NOT the design.
2. `mm9_waist_views_a_half.png`: close renders of the tunic, belt, sleeves and trousers, same five views.
3. `mm9_head_views_a_half.png`: close renders of head and chest, same five views. Face, hair, collar authority.
4. `mm9_skin_x4_a.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
5. (run 2 only) the selected `references_hd/00_three_quarter_clean.png` (the selected 00 with its halo removed).

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1536 PORTRAIT)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so all
views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then select the better and
note any residual fault. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX commoner from the supplied renders of its original 3D
model, as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game
materials and sharp fine detail (coarse woven wool, embroidered braid, worn leather, rope lacing, individual hair strands). ONE complete figure
from the crown to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-3):
- An elderly MALE human about 1.78 m tall, ordinary lean build, slightly narrow shoulders. No bodybuilder, no paunch.
- HEAD: a friendly weathered man about 60, tanned ruddy skin, crow's feet, blue eyes, a long straight nose, a broad warm smile with the LIPS
  CLOSED (no teeth showing), a short neat WHITE beard and moustache along the jaw and chin, complete chin. Thick wavy WHITE-GREY hair, long:
  swept back from the forehead (no fringe), covering the ears, falling to the shoulders at the sides and to between the shoulder blades at the
  back, as in input 3.
- TUNIC: a long-sleeved olive-green wool tunic reaching the upper thigh, loose, with a V neck opening at the throat closed by criss-cross
  lacing, the V edged with a band of gold-brown embroidered braid (geometric key pattern) that runs round the neckline, as in input 3.
- SLEEVES: the same olive wool, wide bell sleeves widening from the elbow, ending just past the wrist with a gold-brown embroidered braid
  band at the cuff, the opening loose round the wrist.
- BELT: a dark brown leather belt at the waist with a plain brass buckle at the front and a short strap end hanging down from the buckle.
- Below the belt the tunic skirt flares slightly, a closed tube round the hips standing clear of the thighs, plain hem.
- TROUSERS: dark brown-black woven wool trousers with a small checked weave, fitted, tucked into the boots.
- BOOTS: mid-calf soft brown leather boots with criss-cross rope lacing up the front, a turned-over cream fleece cuff at the top and a cream
  fleece trim at the ankle, rounded toes, flat soles.
- HANDS: bare human hands with FIVE separate fingers (four fingers and a thumb), relaxed and slightly curled, clear air between the fingers.
  No gloves, no rings. Nothing held.
- No cape, no hood, no hat, no armour, no pouches, no weapons, no staff, no pendant, no extra limbs.

Pose (identical in all views, made symmetric): standing upright, feet apart about 30 cm, toes pointing forward and slightly out; arms hanging
down and away from the body about 30 degrees from vertical, elbows nearly straight, wrists straight, palms facing the thighs, clear air between
the arms, the wide sleeves and the tunic. Exactly the same left and right.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add weapons, a cloak, a hat or armour; change colours (olive-green tunic, gold-brown braid, brown belt, dark checked trousers, brown
boots with cream fleece, white hair and beard); show teeth; crop any part; copy the blur or faceting; give him a modern look.

Per-image checks (redo at most once): crown to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; laced V neck
with braid; bell sleeves with braid cuffs; belt with buckle and hanging strap end; closed flared tunic skirt; checked trousers; laced boots with
fleece cuffs; white beard; long white hair to the shoulders; lips closed.
