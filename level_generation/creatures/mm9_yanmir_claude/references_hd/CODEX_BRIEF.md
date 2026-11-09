# Codex brief: HD reference views for MM9 Yanmir (mm9_yanmir_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_yanmir_claude/references_hd/`. Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and
Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character: "Yanmir", a frost giant king, the boss of an ice fortress. A restoration of an existing 2002 game creature for a
game mod.

## Inputs (attached, in order)
1. `mm9_views.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front three-quarter from the figure's RIGHT,
   front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, proportions
   and colour authority. Faceting, blur and low resolution are NOT the design. (His staff is left out on purpose.)
2. `mm9_torso_views.png`: close renders of the torso (front, left side, back, three-quarter).
3. `mm9_leg_views.png`: close renders of the legs (front, left side, back, three-quarter).
4. `mm9_head_views.png`: close renders of the head (front, three-quarter, left side, back).
5. `mm9_skin_x4.png`: the original 512x512 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
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
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Yanmir" from the supplied renders of its original 3D model,
as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine
detail (frosted skin, fur tufts, leather grain, engraved silver knotwork, ice). ONE complete figure from the tips of the crown to the soles, centred,
generous margins, never cropped.

Identity (exactly the layout of inputs 1-5):
- A huge, heavily muscled frost giant man with heroic proportions: broad shoulders, deep chest, defined pectorals and abdominal muscles, thick arms and
  legs. His SKIN is pale icy blue (cold light blue with white frost highlights and slightly darker blue shadows), smooth like frozen skin. Normal human
  proportions otherwise (head about 1/8 of the height).
- HEAD (input 4): a CROWN of tall clear ice spikes (a dozen icicle points, the tallest at the front centre and the temples) rising from a wide band of
  engraved silver knotwork with a pointed V-shaped centre plate on the forehead. Long straight frosted white-and-pale-blue hair hanging behind the ears
  to the shoulders and the nape, and a long frosted white-blue beard and moustache to the upper chest. Pale icy blue face, heavy brows, a straight
  nose, pale eyes, a broad grim smile with the mouth CLOSED. Ordinary human ears.
- SHOULDERS and COLLAR (input 2): a thick mantle of shaggy white frosted fur over both shoulders and the upper chest and upper back, ending in a jagged
  icicle-like fur fringe across the upper back; a dark-brown leather band around each upper arm just below the fur, like short sleeves. A row of round
  dark silver knotwork disks on the fur across the collarbones and a silver knotwork plate in the centre of the upper chest.
- TORSO: BARE muscular pale-blue chest and stomach between the fur and the belt; the upper back below the fur is bare blue skin too.
- BELT: a wide belt of dark-brown leather with two silver rails and silver round studs and knotwork disks, a big round engraved silver boss at the front centre.
- HIPS: under the belt a short loincloth of white frosted fur with dark-brown leather edges, all round the hips, ending high on the thigh, with a
  shield-shaped engraved silver plate hanging over the groin at the front and a matching smaller one at the back. Tight to the body, NOT a flaring skirt.
  A thin dark leather strap round each upper thigh.
- LEGS (input 3): BARE muscular pale-blue thighs; tall boots from the knee down: an engraved silver knee plate and silver shin greave with knotwork,
  dark-brown leather straps with silver studs round the calf, white fur at the top of the boot, engraved silver shoes.
- ARMS: bare muscular pale-blue arms with an engraved silver bracer on each forearm. Big strong human hands, RELAXED and slightly open, NOT fists,
  four separate fingers and a separate thumb, fingers slightly apart so each one reads.
- No weapon, no staff, no cape, no shield. The hands hold nothing.

Pose (identical in all views): standing upright, legs straight and apart (feet about 35 cm apart), feet pointing forward; arms hanging down and OUT to
the sides at about 35 degrees away from the body, elbows very slightly bent, palms facing the thighs and slightly back, clear air between the arms and
the body and between the legs. Head level, looking straight ahead along the body.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add a weapon or staff, clothes on the chest or thighs, a cape; change the skin to human tones; crop any part (the crown tips included); close
the hands into fists; show teeth; copy faceting or the render's dark sheen; turn the loincloth into a long kilt.

Per-image checks (redo at most once): crown tips to soles in frame; true alpha; both hands open with four fingers plus thumb; bare blue chest and bare
blue thighs; white fur mantle with brown arm bands; wide belt with the round silver boss; silver groin plate; closed mouth with a complete beard.
