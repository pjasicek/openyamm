# Codex brief: HD reference views for the MM9 Trellborg (mm9_trellborg_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_trellborg_claude/references_hd/`. Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and
Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game monster: a big brutish orc-like tribesman in a leather harness and fur-trimmed shorts, a restoration of an existing 2002 game creature for a game mod.

## Inputs (attached, in order)
1. `mm9_views_a.png`: renders of the ORIGINAL low-poly model with its skin (tier "Trellborg"), five views left to right: front three-quarter from the
   figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, POSE,
   proportions and colour authority. Faceting, blur and low resolution are NOT the design.
2. `mm9_torso_views_a.png`: close renders of the torso and arms, same five views.
3. `mm9_legs_views_a.png`: close renders of the hips, legs and feet, same five views.
4. `mm9_head_views_a.png`: close renders of the head.
5. `mm9_skin_x4_a.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
6. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1536 portrait)
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
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Trellborg" from the supplied renders of its original 3D model,
as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional creature with semi-realistic game materials and sharp fine
detail (skin pores, leather grain, steel rivets, fur). ONE complete figure from the hair to the toes, centred, generous margins, never cropped.

Identity (exactly the layout of inputs 1-5):
- A big, heavily muscled brute about 2.3 m tall: very wide sloping shoulders with huge trapezius, thick neck, deep chest, narrow waist, long thick arms, strong legs, very large feet. Red-brown leathery skin, warm tan to rust, as input 1, clearly modelled muscles, no body hair.
- HEAD (input 4): a broad brutal orc-like face, heavy brow, deep-set amber eyes, a short wide flat nose, a jutting lower jaw with a closed mouth, four tusk-like lower teeth rising over the upper lip, the two outer ones biggest. A short rust-red chin beard. Pointed ears, a small gold ear ring.
- HAIR: thick, chunky dark auburn hair swept back from the brow, ending in several long pointed locks over the ears and at the nape. As input 4. Solid chunky locks, no fine loose strands.
- HARNESS: dark brown leather straps with steel studs and pale edging, two straps over the shoulders crossing to a round steel skull medallion in the middle of the chest, and a strap round the chest at the height of the medallion, and on the back an X of the same straps with a small round stud at the crossing, as inputs 1 and 2. A dark leather band round each upper arm at the top. The bare skin shows between the straps.
- WAIST: a pale fur-trimmed band at the waist, under it a dark leather belt with a smaller steel skull buckle. Below the belt a pale tan pelt apron in front, and dark brown fur short breeches to the upper thigh with a ragged fur hem; at the back a pale pelt seat. As input 3. Tight on the body, not a skirt.
- FOREARMS: wide dark leather wrist guards, a riveted steel plate on the outer side, as input 2.
- LEGS: bare knees and shins, on each lower shin a riveted steel greave plate in front with brown fur and leather straps behind it, as input 3.
- FEET: very large, bare, broad feet with four or five thick short toes and short yellow claws. The toes are short blunt lobes joined close together, not long separate fingers. As input 3.
- HANDS: big, heavy hands closed into loose FISTS, five thick fingers curled into the palm and the thumb across them, as input 1. Each fist hangs clear of the thigh.
- No weapon, no cape, no helmet, no tail. No extra pouches.

Pose (identical in all views, the model's bind pose as in input 1): standing, legs apart (feet about 50 cm apart), feet pointing forward; arms held away from the body and down at about 20 degrees from vertical, elbows very slightly bent, clear air between arms and body, clear air between the legs. Head level, looking straight ahead along the body, chin not lowered.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add a club or any weapon; add a tail; change colours; crop any part; open the hands; copy faceting or the render's dark sheen.

Per-image checks (redo at most once): hair to toes in frame; true alpha; skull medallion on the chest and skull buckle on the belt; steel plates on forearms and shins; closed fists with clear fingers; big bare feet with short toes; complete chin and tusks.

## Correction to run 1 (run 1b)
Input 6 is the first return of `00_three_quarter.png`: keep it exactly (face, hair, harness, medallion, wrist guards, greaves, feet, body, pose, colours, light), and change ONLY the part below the belt:
- There is no skirt. The dark brown fur is a pair of tight short BREECHES: each leg is wrapped separately and tightly round the upper thigh, following the thigh muscle, with a ragged fur hem about a hand above the knee, and a clear inner seam: you see the V of the crotch and the separation between the two thighs, as in input 3 (MM9's model has shorts, not a skirt).
- The pelt apron in front is a flat, tight piece lying on the groin and upper thighs, inside the silhouette of the breeches, no pouch flap sticking out. No claw pendant at the hip.
- The silhouette at the hips stays that of the body: no flare, nothing stands off the thighs by more than a finger.
Also: true transparent background, no glow, no halo, no vignette, no dark backdrop.
Save over `00_three_quarter.png`, add it to `generation_runs.json`, then stop.
