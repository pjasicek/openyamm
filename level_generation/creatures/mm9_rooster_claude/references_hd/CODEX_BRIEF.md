# Codex brief: HD reference views for the MM9 Rooster (mm9_rooster_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_rooster_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_crow_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model (its skin alpha is applied: the serrated comb and the separated tail feathers are
alpha cut-outs in the original).

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly rooster with its original skin, five
   views left to right: front three-quarter from the rooster's RIGHT (head toward image right), front, the
   rooster's LEFT side (head faces IMAGE LEFT), back, the rooster's RIGHT side (head faces IMAGE RIGHT). Flat grey
   is background, not creature. This is the design, anatomy, POSE, proportions and colour authority. Its faceting,
   blur and low resolution are NOT the design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original 128x128 skin enlarged 4x, MATERIAL AND COLOUR ONLY (white
   hackle and sickle feathers, red comb and wattles, white earlobe, pale yellow beak, yellow-orange scaly legs).
   Magenta is transparent, not colour. Never the design or shape.
3. `references_hd/mm9_side_close.png` — a larger render of input 1's left side view: comb shape, wattles, earlobe
   and the arched sickle tail with separated feather tips.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the rooster's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front (head toward the camera) | 1536x1024 |
| `02_back.png` | back (tail toward the camera) | 1536x1024 |
| `03_left.png` | the rooster's LEFT side: head faces IMAGE LEFT (as input 3) | 1536x1024 |
| `04_right.png` | the rooster's RIGHT side: head faces IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME rooster, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic
IX "Rooster" (a white farmyard cockerel, like a white Leghorn) from the supplied renders of its original 3D model, as
a 3D modelling/texturing reference. Not a new design. A beautifully detailed, credible, fully three-dimensional white
rooster with semi-realistic game materials and sharp fine feather detail, as if a high-quality sculpt of the original.

Identity: a proud upright white rooster standing.
- Plumage: clean white with soft light-grey shading between feathers: long pointed hackle feathers on the neck
  falling over the shoulders, smooth breast, the folded wing lying flat and tight against each side of the body.
  No other colours in the plumage.
- Tail: a large high arched tail of long white sickle feathers rising behind the back and curving over and down
  (as inputs 1 and 3), the individual sickle feathers clearly separated near their tips; the tail is a fairly thin,
  vertical fan seen from the side, narrow seen from the front and back.
- Head: rooster head; a SHORT, DEEP, stout conical pale-yellow beak, closed, pointing FORWARD and only slightly down
  exactly as in input 3 (no long or thin beak, no hook); a LARGE upright bright-red SERRATED single comb with five to
  six pointed spikes running from the beak base back over the crown (as input 3), a fleshy blade, thin side to side;
  two red wattles hanging under the beak, compact and close together; a white oval earlobe below and behind the eye;
  red bare skin around a small round amber-orange eye with a black pupil.
- Neck: upright, covered by the hackle feathers; the throat is a smooth feathered line behind the wattles.
- Legs: two yellow-orange scaly legs, straight, vertical and clearly SEPARATED with a gap of air between them (as
  input 1 front view), each with a small backward-pointing spur on the inner back of the shank, feathered thighs.
- Feet: flat on an invisible ground plane, each with THREE front toes spread FORWARD and slightly outward and ONE
  short hind toe pointing straight BACK, small pale claws. Soles down.

Pose (exactly as input 1, the model's bind pose): standing upright and square, chest out, head high on the upright
neck looking forward, both legs straight and apart, wings folded, tail raised. Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. The whole rooster inside the frame with generous margins (never crop the tail, comb or toes), genuine
transparent background, no floor, no ground shadow, no straw, no text.

Do NOT: add a second animal, straw, a fence or a perch; do not spread or raise the wings; do not open the beak (not
crowing); no long or hooked beak; no brown, black, green or golden plumage; no extra toes, legs or combs; do not crop.

## Per-image checks (re-run before selecting)
One white rooster; short deep closed pale-yellow beak pointing forward; large serrated red comb; two red wattles;
white earlobe; amber eye; wings folded flat on the sides; high arched white sickle tail with separated tips; two
separated straight legs with three forward toes, one hind toe and a spur each, soles down; the correct side faces the
correct image side (03: head to image LEFT; 04: head to image RIGHT); true transparent background; 1536x1024;
nothing cropped.
