# Codex brief: HD reference views for the MM9 Thrall (mm9_thrall_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_thrall_claude/references_hd/`. Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and
Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an adult male enslaved tribesman, a restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views_c.png`: renders of the ORIGINAL low-poly model with its skin (tier "Thrall Master"), five views left to right: front three-quarter from the
   figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, POSE,
   proportions and colour authority. Faceting, blur, the shiny white streaks and low resolution are NOT the design (those streaks are render artefacts).
2. `mm9_waist_views_c.png`: close renders of the waist and the skirt, same five views.
3. `mm9_head_views_c.png`: close renders of head and shoulders: face, hair and rope collar authority.
4. `mm9_skin_x4_c.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
5. (run 2 only) the selected `references_hd/00_three_quarter.png`.

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
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Thrall Master" from the supplied renders of its original 3D model,
as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine
detail (skin pores, individual hair strands, coarse hide, twisted rope). ONE complete figure from the hair to the soles, centred, generous margins, never cropped.

Identity (exactly the layout of inputs 1-3):
- A lean, strong, weathered adult MALE human about 1.85 m tall: broad shoulders, big rangy arms, defined but not bulky chest and stomach muscles, wide hands. No bodybuilder.
- SKIN: warm tanned brown, sun-darkened, as in inputs 1 and 4.
- CHEST: bare. Pectorals and six-pack muscles clearly modelled, a faint scar or two, as input 3.
- NECK: a thick twisted rope COLLAR lying tight round the base of the neck, with one iron ring at the front of the throat, as input 3.
- HEAD: an ordinary human man's head with a strong jaw, dark eyes, short dark beard. A complete chin. Mouth closed.
- HAIR: dark brown shoulder-length hair, parted loosely, close to the skull on top, hanging behind the ears down to the nape as in input 3.
- WAIST: a thin braided rope belt, tied in a loose bow at the front with two rope ends hanging down, as input 2.
- SKIRT: a coarse tan hide kilt from the belt to the middle of the thighs, loose and standing clear of the thighs, a closed tube round the hips. Its hem is torn into long jagged points,
  longest at the two hips and at the front centre, as input 2. Under it, dark brown hide shorts hug the hips and the very top of the thighs (their torn edge shows just below the kilt,
  as in input 2's back view). The legs below it are bare, with air between the kilt and the thigh.
- FOREARMS: a band of dark leather wrapped round each wrist and lower forearm, as input 1.
- HANDS: strong human hands with FIVE separate fingers (four fingers and a thumb), slightly curled and open, clear air between the fingers.
- LOWER LEGS: from below the knee to the ankle, wrapped in strips of dark leather and hide, cross-gartered with a tiger-like stripe rhythm as in input 1. Knees bare.
- FEET: simple leather sandals with a thick sole and a few straps across the instep; five toes visible.
- No weapons, no armour, no extra limbs, no cape, no shirt, no hood.

Pose (identical in all views, the model's bind pose as in input 1): standing, legs apart (feet about 80 cm apart), toes pointing forward; a very slight stoop with the head a little forward,
as input 1's side views; arms held away from the body and down at about 35 degrees from vertical, slightly forward, elbows slightly bent, palms facing inward and down, clear air between arms and body.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add a shirt, armour, weapons; change colours; crop any part; copy the shiny white streaks; give him a modern look.

Per-image checks (redo at most once): hair to soles in frame; true alpha; five fingers on each visible hand; rope collar with one ring; rope belt with bow; torn hem; sandals with toes.
