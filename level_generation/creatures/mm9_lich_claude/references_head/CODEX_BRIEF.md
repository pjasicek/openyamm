# Codex brief: HD skull turnaround for the MM9 Lich (mm9_lich_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_lich_claude/references_head/`. Do not edit
any other file, do not run builds, do not call Meshy.

Purpose: the body model came back with an old man's face instead of a skull. These images model a SKULL-ONLY
replacement (the three-quarter view is the single-image 3D modelling input) and later texture it.

## Inputs (attached, in order; paths relative to `level_generation/creatures/mm9_lich_claude/`)
1. `references_hd/01_front.png`: the SELECTED HD front body master: skull identity, bone colour, ember eyes.
2. `references_hd/00_three_quarter.png`: the selected three-quarter body master.
3. `references_hd/03_left.png`: the selected profile body master (skull profile, jaw, teeth).
4. `references_hd/mm9_head_views.png`: renders of the ORIGINAL MM9 model's head: the jaw hangs open.
5. `references_hd/mm9_skin_x4.png`: the original skin enlarged, top-left corner: the skull painting and the wet red-green
   rot inside the mouth. Surface and colour only.
6. (run 2 only) the selected `references_head/00_three_quarter.png`.

## Deliverables (1024x1024 SQUARE, true transparent background, unresized returns)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, faces image right and toward the viewer, camera slightly above eye level; primary |
| `01_front.png` | exact straight-on front |
| `02_back.png` | straight from behind |
| `03_left.png` | pure profile, faces IMAGE LEFT |
| `04_right.png` | pure profile, faces IMAGE RIGHT |

Run 1: `00_three_quarter.png` only, then stop. Run 2 (separate run): 01-04 with the selected 00 as an additional input, so
all five show the SAME skull. At most ONE targeted corrective regeneration per view. Write `generation_runs.json` (id,
prompt, inputs with sha256, output, selected, reason, superseded runs) and, after run 2, a `selected_views_review.png`
contact sheet; raw returns under `raw/`.

## Prompt content (adapt per view)
Use case: identity-preserve. An isolated HD SKULL for the existing MM9 Lich monster, a 3D modelling and texture reference,
not a new design. The EXACT SAME skull as the selected body masters, shown alone: ONE COMPLETE anatomically correct adult
human SKULL with its lower jaw attached. NO hood, no cloth, no neck vertebrae, no spine, nothing else. The skull is centred
and level and fills about 75 % of the frame height, generous transparent margins, near-orthographic camera, even soft
neutral studio light, no cast shadows, no floor, no text.

Identity: smooth rounded cranium with a clear brow ridge, deep round eye sockets, a pear-shaped nose cavity, prominent
cheekbones, a complete row of worn teeth above and below. The LOWER JAW hangs open by about two finger-widths, as in input
4, so the upper and lower teeth are clearly apart and the mouth is a dark hollow; a small dark red-green rot clings inside
the mouth, as in input 5. Aged ivory bone with slightly yellowed cracks and shallow stains, as in input 1. Each eye socket
holds a small burning red-orange ember deep inside, the same as input 1; the rest of the socket is dark.

Per-image checks: one skull; lower jaw open and clearly attached at the hinges; no neck, no hood; real skull proportions,
not a cartoon; correct side faces the correct image side; true transparent background; 1024x1024.

## Do NOT
add flesh, skin, lips, eyelids, a hood, a crown, horns, a spine or neck bones; close the jaw; crop.
