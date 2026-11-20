# Codex brief: HD reference views for the MM9 Horde Soldier (mm9_clansoldier_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_clansoldier_claude/references_hd/`. Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and
Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an adult male medieval foot soldier in leather and mail, a restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views_a.png`: renders of the ORIGINAL low-poly model with its skin (tier "Horde Grunt"), five views left to right: front three-quarter from the
   figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, POSE,
   proportions and colour authority. The faceting, blur and low resolution are NOT the design.
2. `mm9_waist_views_a.png`: close renders of the coat and its skirt, same five views.
3. `mm9_head_views_a.png`: close renders of head and chest, same five views. Face, helmet, hair and mantle authority.
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
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Horde Grunt" from the supplied renders of its original 3D model,
as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine
detail (mail rings, stitching, studs, fur, worn leather). ONE complete figure from the crown to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-3):
- A broad-shouldered, fit adult MALE human about 2 m tall, ordinary proportions. No bodybuilder.
- HEAD: an ordinary rugged man about 35, tanned, straight nose, a thin moustache and a small dark goatee, mouth closed. A round conical open-faced HELMET: a steel-grey and bronze dome with a raised central ridge, a band of mottled dark brown fur round its lower half, and a narrow straight steel NASAL bar in front of the nose. Long straight black hair falls from under the helmet behind the ears and down the back of the neck to the mail mantle, a solid mass as wide as the neck and ears, as in input 3.
- MANTLE: a short heavy chain-mail capelet over the shoulders, chest top and upper back, with a low V neck edged in olive-gold cloth showing a bare V of skin at the throat. It lies close on the shoulders.
- SHOULDERS: brown fur caps at the very top of the arm, just below the mantle.
- COAT: a red-brown quilted leather coat with diagonal diamond quilting and rows of small round brass studs, closed all round the torso, a laced seam at the centre of the chest, as in inputs 1 and 3.
- SASH: a wide dark brown leather and cloth sash wrapped round the waist, with a knotted fold hanging in front, as in input 2.
- SKIRT: below the sash the coat continues as a short skirt to the upper-middle thigh, slightly flared and standing clear of the thighs, a closed tube round the hips except for a small slit at the centre front and centre back. Its upper part carries panels of grey metal scales bordered with brass beads, its lower part bands of red-brown leather, and the hem a narrow tan woven band, as in input 2.
- SLEEVES: as input 1: upper arm red-brown leather with bands of brass-edged laminated strips on the outside, forearm dark teal-blue cloth, then a wide dark leather bracer with brass trim at the wrist.
- HANDS: strong hands in plain dark brown leather gloves with FIVE separate fingers (four fingers and a thumb), relaxed and slightly curled, clear air between the fingers. No weapons in them.
- LEGS: slim very dark brown leather trousers, tight on the leg, ending inside the boots.
- BOOTS: brown leather boots to below the knee, wide cuffs lined with tan fur at the upper shin as in input 1, thick soles, rounded toes.
- No cape, no hood, no pouches, no sword belt, no scabbard, no shield, no weapons, no extra limbs.

Pose (identical in all views, the model's bind pose as in input 1): standing upright, feet apart (about 35 cm between the feet), toes pointing forward; arms straight out to the sides and down at about 30 degrees BELOW horizontal, elbows nearly straight, wrists straight, clear air between arms and body.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add weapons, a shield, a cloak or extra armour; change colours; crop any part; copy the blur or faceting; give him a modern look.

Per-image checks (redo at most once): crown to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; helmet with nasal bar; mail mantle with V; coat with studs; sash; closed skirt; fur-cuffed boots.
