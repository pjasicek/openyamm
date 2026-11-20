# Codex brief: HD reference views for the MM9 Half Orc Recruit (mm9_dookmilitia_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_dookmilitia_claude/references_hd/`. Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and
Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an adult male half-orc militiaman in leather armour, a restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views_a.png`: renders of the ORIGINAL low-poly model with its skin (tier "Half Orc Recruit"), five views left to right: front three-quarter, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, POSE, proportions and colour authority. The faceting, blur and low resolution are NOT the design.
2. `mm9_waist_views_a.png`: close renders of the tunic and its skirt, same five views.
3. `mm9_head_views_a.png`: close renders of head and chest, same five views. Face, helmet, mantle and collar authority.
4. `mm9_skin_x4_a.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
5. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1536x1024 LANDSCAPE so the outstretched arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so all views are
the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then select the better and note any residual fault.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after run 2,
a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Half Orc Recruit" from the supplied renders of its original 3D model,
as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine
detail (stitching, tooled leather, rivets, suede). ONE complete figure from the crown to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-3):
- A broad, heavy-boned adult MALE half-orc about 2.0 m tall, thick neck and wide shoulders, but ordinary human proportions of limbs and head. No bodybuilder.
- HEAD: a coarse half-orc face: heavy brow, deep-set dark eyes, wide flat nose, strong jaw, complete chin, tanned tawny skin, short dark goatee shadow, two short lower tusks showing at a closed mouth. POINTED ears standing out to the sides, as input 3.
- HELMET: a dark reddish-brown leather skull cap with a thick rolled rim over the brow; from it a dark leather coif hangs down over the back of the head and neck to the shoulders, with a thin gold line round the back of the head. Two short black horn spikes stand out from the cap's sides above the ears. On each side, in front of the ear, a vertical dark leather cheek strap with gold edges and two silver studs hangs from the cap to the jaw. Face fully visible.
- MANTLE: a dark brown leather shoulder mantle of long riveted vertical strips with small silver studs at their lower ends, over the chest and upper back and the shoulders, as input 3, in a V from the neck. Below it a soft worn dark-brown leather chest panel. A narrow collar of dark mail at the throat.
- TUNIC: a red-brown leather tunic with big diagonal diamond quilting, a laced centre seam on the belly, to a short skirt that ends at the upper-middle thigh, a closed tube round the hips, split a little at the front centre, with a dark frayed edge. Short red-brown quilted sleeve caps with a jagged lower edge at the shoulder.
- BELT: a dark red leather belt with thin gold lines, silver studs, and an ornate oval buckle.
- SLEEVES: long very dark olive-brown cloth sleeves from the cap to the wrist with a thin gold band above the forearm, then a dark red-brown leather bracer on each forearm, as input 1.
- HANDS: strong bare tan hands with FIVE separate fingers (four fingers and a thumb), relaxed and slightly curled, clear air between the fingers. No gloves. No weapons in them.
- LEGS: red-brown leather trousers tight on the leg, with a patch of tan-olive suede on each knee.
- BOOTS: very dark brown leather boots to below the knee with two rows of silver studs and a strap with a silver buckle over the ankle, thick soles.
- No cape, no hood beyond the coif, no pouches, no sword belt, no scabbard, no weapons, no extra limbs.

Pose (identical in all views, the model's bind pose as in input 1): standing upright, feet apart (about 45 cm between the feet), toes pointing forward; arms straight out to the sides and down at about 27 degrees BELOW horizontal, elbows nearly straight, wrists straight, clear air between arms and body.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add weapons, a cloak or plate armour; change colours; crop any part; copy the blur or faceting; give him a modern look.

Per-image checks (redo at most once): crown to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; helmet with cheek straps and horn spikes; pointed ears; mantle strips with studs; belt; closed tunic skirt; studded boots.
