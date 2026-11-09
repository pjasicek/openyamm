# Codex brief: HD reference views for the MM9 Evil Sorcerer (mm9_evilsorcerer_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_evilsorcerer_claude/references_hd/`. Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and
Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an adult male court sorcerer in ceremonial robes, a restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views_b.png`: renders of the ORIGINAL low-poly model with its skin (tier "Evil Sorcerer"), five views left to right: front three-quarter from the
   figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout,
   proportions and colour authority. The faceting, blur and low resolution are NOT the design. The pose of the input is NOT the pose wanted.
2. `mm9_waist_views_b.png`: close renders of the belt, the hanging panels and the legs, same five views.
3. `mm9_chest_views_b.png`: close renders of the chest, yoke, shoulder plates and arms, same five views.
4. `mm9_head_views_b.png`: close renders of head, crown and neck, same five views.
5. `mm9_skin_x4_b.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
6. (run 2 only) the selected `references_hd/00_three_quarter.png`.

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
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Evil Sorcerer" from the supplied renders of its original 3D model,
as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine
detail (woven wool, embossed brass, damask silk, individual hairs). ONE complete figure from the top of the crown to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-4):
- A lean, tall adult MALE human about 1.95 m tall including the crown, ordinary proportions, narrow waist. No bodybuilder.
- HEAD: a cruel, sharp-browed man of about 45, strong nose, dark brown eyes, black swept moustache joined to a black goatee, trimmed black sideburns, closed mouth, chin complete. Bare ears show below the crown.
- CROWN: a stiff tall crown of embossed brass and red enamel, a tall centre point over the forehead with a small red gem, four more upright points round the head, open at the top with a dark inner cap, as input 4. A rigid brass band round the brow.
- NAPE FLAP: from the crown's rim at the back and the sides, a stiff padded panel hangs behind the ears and neck to the top of the shoulders, red and gold brocade, with a thin brass edge, standing clear of the neck, as input 4. The face and the front of the neck stay clear.
- YOKE: a rigid embossed brass-and-red-enamel yoke sits on the upper chest and the upper back, ending in a low pointed V on the chest and on the back. At the centre of the chest a small brass demon face. It carries a tall stiff brass COLLAR: two wing points rising beside the neck, as input 3. Inside the collar, a dark grey wool undershirt at the throat.
- PAULDRONS: on each shoulder one big separate rounded plate of embossed brass and red enamel, with a brass rim, a pointed peak standing up at the inner edge, sitting on the shoulder and clear of the upper arm, as input 3.
- BODY: a tight dark charcoal padded wool tunic from the yoke to the belt, soft shallow folds.
- SLEEVES: dark grey wool sleeves, tight on the arm, to the mid forearm, then a stiff brass BRACER with a zigzag upper edge and two small red gems, as input 3.
- BELT: a wide belt of plaited brass knotwork all round the waist, with a large brass demon-face buckle hanging a little below it at the front, as input 2.
- HANGING PANELS: from under the belt, flat stiff separate panels of red silk damask with gold scrollwork and a thin brass edge: one long FRONT panel, about 26 cm wide, hanging straight down to the middle of the shin with a shallow pointed end; one long BACK panel, the same; and two SHORT FLAPS at the front of the hips, ending in points at mid thigh, as input 2. The panels hang straight and free in front of and behind the legs, NOT stuck to them, with clear air visible between the legs and the panels. There is NO closed skirt and NO robe tube: between the panels you see the trousers at the sides of the hips.
- LEGS: separate slim charcoal wool trousers, tight on the thighs and calves, with a clear gap between the legs, tucked into low boots, a brass ring band below the knee at the upper calf.
- GREAVES: on each shin a stiff red-and-gold plate, narrow, pointed at the top just below the knee, strapped to the shin, as input 2.
- BOOTS: low soft black shoes with brass trim and a slightly pointed toe, ordinary size.
- HANDS: strong bare human hands with FIVE separate fingers (four fingers and a thumb), relaxed, slightly curled, clear air between the fingers. No gloves. Nothing in them.
- No cape, no staff, no weapons, no pouches, no extra limbs.

Pose (identical in all views; NOT the pose of input 1): standing upright and symmetrical, facing the camera direction of the view, feet apart (about 40 cm between the feet), toes pointing forward, legs straight; arms straight, out to the sides and down at about 40 degrees from vertical, palms facing the thighs, slightly forward, elbows nearly straight, wrists straight, clear air between the arms and the body, clear air between the hands and the panels. Head level, looking straight ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add weapons, a staff, a cloak or a closed skirt; change colours; crop any part; copy the blur or faceting; give him a modern look; merge the panels into the legs.

Per-image checks (redo at most once): crown to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; crown with five points; nape flap; yoke with demon face; two collar wings; two pauldrons clear of the arm; belt with demon buckle; one long front panel and two short flaps standing clear of the legs; back panel; two separate trouser legs; greaves.
