# Codex brief: HD reference views for the MM9 Guard (mm9_guard_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_guard_claude/references_hd/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the
authority is the ORIGINAL Might and Magic IX 3D model with its skins, shown in renders made from that model.

The same low-poly body has three skins: Guard (leather, tier A), Sergeant (tier B) and Captain (chain and steel, tier C).
All tiers must be the SAME body, same pose, same proportions, same silhouette: only the surface differs.

## Inputs (attached, in order)
Run 1 and 2 (tier A):
1. `mm9_views_a.png`: renders of the ORIGINAL low-poly model, five views left to right: front three-quarter from the figure's
   RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design,
   POSE, proportions and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `mm9_head_views_a.png`: close renders of head and shoulders.
3. `mm9_skin_a_x4.png`: the original skin enlarged 4x: SURFACE MATERIAL AND COLOUR ONLY, never shape.
4. (run 2) the selected `00_three_quarter.png`.
Run 3 (tier C): 1. `mm9_views_c.png`, 2. `mm9_head_views_c.png`, 3. `mm9_skin_c_x4.png`, 4. selected `00_three_quarter.png`,
5. selected `01_front.png`: inputs 4 and 5 fix the body, pose and silhouette.

## Deliverables (true transparent background, unresized returns, 1024x1536 portrait)
| File | View |
|---|---|
| `00_three_quarter.png` | tier A, front three-quarter from the figure's RIGHT, camera at chest height slightly above |
| `01_front.png` | tier A, straight front; the figure's RIGHT arm on IMAGE LEFT |
| `02_back.png` | tier A, straight back; the figure's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | tier A, pure 90-degree profile of the figure's LEFT side: faces IMAGE LEFT |
| `04_right.png` | tier A, pure 90-degree profile of the figure's RIGHT side: faces IMAGE RIGHT |
| `c_01_front.png`, `c_02_back.png`, `c_03_left.png`, `c_04_right.png` | tier C, same four views |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2: 01-04 with the selected 00 as input. Run 3: the c_ views. At most
ONE corrective regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`. Write
`generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs); after runs 2 and 3
`selected_views_review.png` / `selected_views_review_c.png` contact sheets.

## Common prompt content (adapt per view)
TASK CONTEXT, FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Guard"
character from the supplied renders of its original 3D model, as a 3D modelling and texturing reference. Not a new design. A
credible, fully three-dimensional adult man with semi-realistic game materials and sharp fine detail, as if a high-quality sculpt of
the original model. ONE complete figure from the helmet to the soles, centred, generous margins, never cropped.

Body and silhouette (exactly as input 1, tiers A and C alike):
- A fit man about 1.88 m tall, normal human proportions, broad shoulders, slim waist, long straight legs.
- HELMET: a tall rounded war cap whose sides fall as two long solid cheek-and-neck guards to the jaw line and whose back closes the
  whole nape, with a slight brim ridge above the brow and a band round the head at temple height. The face is open from brow to
  chin. A real human face in the opening: clean jaw, short reddish-blond stubble beard, firm mouth (closed), blue eyes.
- NECK: short bare neck in a V-opening.
- SHOULDERS: a stiff collar-mantle over the shoulders with two raised triangular shoulder points that stand up and outwards beside
  the neck (the tall pointed wings of input 2), closing into a V on the chest with two round brooches, one each side of the V.
- BODY: a long-sleeved fitted tunic down to the upper thigh, its hem a simple closed ring that hangs just below the crotch line, with
  a clear hem trim. A flat belt at the hips with an ornate round buckle.
- ARMS: slim sleeves, a small ridged flanged cuff (a few short raised points) at the elbow, as on input 1, and short flared
  gauntlet cuffs at the wrist.
- HANDS: gloves with FIVE clearly separated fingers each.
- LEGS: slim fitted legs, two clearly separate legs with a real gap between them from the crotch down. Knee-high boots with cuffs,
  strapped and studded, buckle at the ankle, a slightly pointed toe, flat soles.

Tier A surface (input 1 and 3): helmet of dark brown riveted leather with steel studs in rows and a small gold lion-face badge on
the brow; tunic of warm red-brown quilted leather in a diamond stitch, lacing at the centre of the chest; deep teal-blue cloth V-panel
at the collar and teal cloth sleeves, tan braided trim along the V, the collar, the hem and the cuffs; dark brown leather mantle
points; gold round brooches and buckle; dark red-brown belt with steel studs and gold edges; dark brown leather gloves; dark brown
leather trousers; tan-brown studded leather boots.

Tier C surface (run 3; input 1 and 3, shapes from inputs 4 and 5): helmet of grey polished steel with rivets and a banded brow, with
a steel nasal bar and an eye-mask ring round both eyes; the same face, the same stubble; steel chevron plates and steel shoulder
plates on the mantle with bronze round brooches; hauberk and leggings of dark grey riveted chain mail; steel gauntlets with
articulated fingers and steel forearm bracers; bright steel greaves with a ridged shin and knee cops over the same boots, steel
sabatons; same belt and buckle.

Pose (identical in all views, the model's bind pose as in input 1): standing upright facing forward, arms held out to the sides and
down, about 35-40 degrees below horizontal, elbows very slightly bent, wide clear air between arms and body; hands open, the five
fingers separated and slightly curved, palms facing down and in; legs straight, feet about shoulder width apart, a clear gap between
the legs from crotch to feet, feet flat. Head level, looking forward. NO weapon.

Camera and light: near-orthographic, even soft neutral studio light (brighter than input 1, which is dark), no dramatic light, no
strong cast shadows on the figure; genuine transparent background, no floor, no shadow, no text.

Do NOT: add a weapon, shield, cape, cloak, tabard flaps, skirt panels, pouches, scabbard or extra armour; do not change the colours;
do not open a slit in the tunic hem; do not fuse the legs; do not crop the helmet or the feet; do not make a fists or claws.

## Per-image checks (re-run before selecting)
Open-faced cheek-guard helmet with a real human face; raised triangular shoulder points; V-collar with two brooches; closed
tunic hem at the upper thigh, belt with round buckle; elbow cuffs; gloves with FIVE separated fingers on each hand; two separate legs with
a visible gap; boots to the knee; no weapon; the pose above; the correct side faces the correct image side (03: faces IMAGE LEFT;
04: faces IMAGE RIGHT); whole figure inside the frame with margins; true transparent background; 1024x1536.
