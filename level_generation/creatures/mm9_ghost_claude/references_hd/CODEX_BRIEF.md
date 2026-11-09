# Codex brief: HD reference views for the Ghost (MM9 monster, rows Shadow, Apparition, Specter) (mm9_ghost_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_ghost_claude/references_hd/`. Do not edit
any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_t2.png`: flat-lit renders of the ORIGINAL Might and Magic IX low-poly model with its original
   skin, five views left to right: front three-quarter (figure faces image right and toward the viewer), front, side
   facing IMAGE LEFT, back, side facing IMAGE RIGHT. Flat grey is background. This is the design, costume, POSE,
   proportions and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_head_views_t2.png`: close renders of the head and collar: head, ruff, necklace authority.
3. `references_hd/mm9_skin_x4_t2.png`: the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (robe weave, ribs, belt, trim, ruff, hair). Never the design or shape.
4. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1024x1536 portrait)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter as input 1 view 1 (faces image right and toward the viewer), camera at chest height, slightly above |
| `01_front.png` | straight front, as input 1 view 2 |
| `02_back.png` | straight back, as input 1 view 4 |
| `03_left.png` | pure 90-degree profile, faces IMAGE LEFT, as input 1 view 3 |
| `04_right.png` | pure 90-degree profile, faces IMAGE RIGHT, as input 1 view 5 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an
additional input so all views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`. Write
`generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after
run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT, FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and Magic IX
undead character from the supplied renders of its original 3D model, as a 3D modelling and texturing reference. Not a new
design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine detail (woven cloth,
braided trim, tooled belt, soft ruff), as if a high-quality sculpt of the original model. ONE complete figure from the crown
of the head to the tips of the robe, centred, generous margins, never cropped. Render it SOLID and OPAQUE: it is a modelling
reference, so no transparency, no glow, no mist, no smoke, no aura.

Pose (identical in all views, the model's bind pose as in input 1; do not tidy it): a legless floating figure, upright torso, head
level, a thin neck rising from the ruff. Both arms straight out and down from the shoulders about 35 degrees below horizontal,
well clear of the body, with slim full-length sleeves. Hands open, relaxed, fingers together and pointing along the arm. The robe
below the belt is one long closed tapered skirt with NO legs and NO feet inside it: it sweeps down and BACKWARD at about 30 degrees
from vertical, as in the side views of input 1, wider toward the hem, and ends in about seven long sharp pointed tatters.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no cast shadows on the body;
genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1-3; the pose above; no legs; robe
sweeping back; both arms clear of the body; correct side faces the correct image side (03 IMAGE LEFT, 04 IMAGE RIGHT); whole figure
inside the frame with margins; true transparent background; 1024x1536.

## Identity
The spirit of a gaunt old nobleman. From top to bottom:
- Head: a long, gaunt, hollow-cheeked old man's face, pale grey-green skin, deep brow, sunken green eyes, mouth open in a dark grin
  with worn teeth, as input 2. White hair brushed straight back, lying close to the skull as ONE smooth solid mass (no loose strands),
  so the head keeps the tall egg silhouette of input 2.
- Neck: thin, inside a soft white fur ruff collar that opens in a V down the upper chest, a thin pale chain with a small oval clasp in the V.
- Torso: a slim fitted coat of dark green-brown patterned brocade with a tiny dotted weave, a narrow braided tan trim along the front
  opening, a pale green-white ribcage showing through the cloth on the chest sides and on the back, as in input 1 view 4 and input 3.
- Belt: a flat grey-green tooled belt with two oval knotwork bosses, at the waist.
- Sleeves: slim, same brocade fading to pale sea-green toward the wrist, ending in a soft white lace cuff.
- Hands: pale grey-green, long thin bony fingers, five fingers, slightly curled nails.
- Robe: sea-green cloth with long vertical folds from the belt, pale at the top, dripping into near-black torn tatters in the lower third, as
  in input 1: the pale cloth ends in ragged downward drips over the dark. Long sharp points at the hem, the same front and back.

## Do NOT
- add legs, feet, a hood, a staff, weapon, crown, armour, wings, chains or extra limbs; change colours; add glow or see-through effects;
  straighten the robe to hang vertically; put hands against the body; crop.
