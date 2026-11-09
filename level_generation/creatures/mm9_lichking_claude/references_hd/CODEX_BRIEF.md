# Codex brief: HD reference views for the MM9 Lich King (mm9_lichking_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_lichking_claude/references_hd/`. Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and
Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an undead skeleton king in ornate dark armour, a restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front three-quarter from the
   figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout,
   proportions and colour authority. The faceting, blur and low resolution are NOT the design. The pose of the input is NOT the pose wanted.
   (The original holds a staff; it is removed here and must NOT be drawn.)
2. `mm9_waist.png`: close renders of the belt, the front panel, the coat and the legs, same five views.
3. `mm9_chest.png`: close renders of the chest plate, shoulder plates and arms, same five views.
4. `mm9_head.png`: close renders of the skull, crown and its hanging bands, same five views.
5. `mm9_skin_x4.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
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
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Lich King" from the supplied renders of its original 3D model,
as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine
detail (engraved blackened steel, polished silver knotwork, cold bone, heavy dark navy wool). ONE complete figure from the top of the crown to the soles,
centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-4):
- A tall, lean undead king about 2.1 m tall including the crown, ordinary human proportions under the armour, narrow waist. No bodybuilder.
- HEAD: a bare human SKULL, pale cold bone with a faint blue-grey tint, glowing red-orange eye lights deep in the sockets, the jaw slightly open showing teeth with a faint green glow inside the mouth. Only the face of the skull is bare.
- CROWN-HELM: a tall stiff crown of blackened steel with silver knotwork, five tall triangular points (a tall centre point over the forehead), a band of red and turquoise gems round the brow, as input 4. The crown continues down the back of the skull as a closed rigid helm plate of silver-grey knotwork that covers the top, sides and back of the skull to the nape, so only the face shows. From the sides of the crown two narrow stiff silver bands hang straight down beside the jaw to just above the shoulder plates, standing clear of the face.
- SHOULDERS: two big separate rigid shoulder plates of engraved silver and blackened steel, flaring out wide past the arms and ending in a sharp point at the outer tip, each with a sharp upright point rising beside the neck, as input 3. They sit on the shoulders, clear of the upper arm.
- CHEST: a rigid breastplate of blackened steel with silver knotwork, a big round silver medallion with a skull relief in the centre of the upper chest and two smaller round skull medallions to either side, a dark blue-black engraved plate below it, as input 3.
- ARMS: tight armoured sleeves of black ribbed lacquered plates on the upper arm and forearm; on each forearm a long rigid silver knotwork bracer from the wrist to near the elbow, as input 3.
- HANDS: black armoured gauntlets with FIVE separate articulated fingers (four fingers and a thumb), relaxed, slightly curled, clear air between the fingers. Nothing in them.
- BELT: a black belt with a large oval silver buckle at the front carrying a skull relief and a turquoise gem above the skull, as input 2.
- FRONT PANEL: from under the belt, one long stiff silver knotwork panel (a tabard), about 26 cm wide, hanging straight down at the front to the middle of the shin, with a skull-shaped top and a shallow pointed end, standing clear of the legs, as input 2.
- COAT: a long heavy dark navy-black wool coat starting at the shoulders under the shoulder plates and covering the whole back, down to just above the ankles at the back, OPEN at the front: at the front only its two side edges show beside the hips, ending at about knee height in front and getting longer towards the back, as inputs 1 and 2. Air between the coat and the legs. A dark lining inside.
- LEGS: two separate slim legs in black ribbed lacquered armour plates, a clear gap between the legs. At each knee a black winged knee plate with a round silver skull medallion on it, and a smaller skull medallion on the shin, as input 2.
- BOOTS: black armoured boots with silver knotwork trim, slightly pointed toes, ordinary size.
- No staff, no weapons, no cape over the shoulders, no pouches, no extra limbs, no hair, no flesh.

Pose (identical in all views; NOT the pose of input 1): standing upright and symmetrical, facing the camera direction of the view, feet apart (about 40 cm between the feet), toes pointing forward, legs straight; arms straight, out to the sides and down at about 40 degrees from vertical, palms facing the thighs, slightly forward, elbows nearly straight, wrists straight, clear air between the arms and the body, clear air between the hands and the coat. Head level, looking straight ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add a staff or weapons; close the coat at the front; change colours (dark navy, black, silver, pale bone, red and turquoise gems); crop any part; copy the blur or faceting; merge the coat or the front panel into the legs.

Per-image checks (redo at most once): crown to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; skull face with red eye lights; crown with five points covering the back of the skull; two hanging side bands; two wide pointed shoulder plates; skull medallion on the chest; skull buckle; one long front panel clear of the legs; open coat with the back covered to the ankles; two separate legs with skull knee plates.
