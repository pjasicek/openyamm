# Codex brief: head turnaround for the MM9 Guard (mm9_guard_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_guard_claude/references_head/`. No builds, no Meshy.
Use your built-in image generation tool.

## Inputs (attached, in order)
1. `in_00_three_quarter.png`, 2. `in_01_front.png`: crops of the accepted full-body masters: the face, helmet shape, proportions authority.
3. `mm9_head_views_a.png`: the ORIGINAL low-poly model, tier A. 4. `mm9_head_views_c.png`: tier C. 5. `mm9_skin_c_x4.png`: tier C skin, surface only.

## Deliverables: 1254x1254 if available, else 1024x1024, true transparent background, bust only cut below the jaw at the top of the collar
Two helmets on the SAME head, the same face, same stubble, same scale and framing in every image:
| File | View | Helmet |
|---|---|---|
| `a_01_front.png`, `a_03_left.png`, `a_02_back.png`, `a_04_right.png` | straight front; profile facing IMAGE LEFT; straight back; profile facing IMAGE RIGHT | tier A: dark brown riveted leather war cap with steel studs and a small gold lion badge on the brow, as inputs 1 and 2 |
| `c_01_front.png`, `c_03_left.png`, `c_02_back.png`, `c_04_right.png` | same four | tier C: the SAME helmet shape in grey polished steel, a banded riveted brow, a steel nasal bar and an eye-mask ring round both eyes as inputs 4 and 5, no badge |

Keep the helmet's silhouette identical in A and C: rounded skull, brim ridge above the brow, long solid cheek guards down to the jaw line, a closed nape. A real adult man's face in the opening: clean jaw, firm closed mouth, blue eyes, short reddish-blond stubble. The neck is bare below the jaw, cut flat at the bottom edge of the image.

Camera: orthographic, even soft neutral studio light, no cast shadows, head level, centred, the head filling about 80 % of the height, nothing cropped except the neck. No text, no floor, no armour below the neck.

Generate a_01_front first; use it as an input for all others. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs.json` and a contact sheet `selected_views_review.png`.

Checks: identical framing, profile views are true 90-degree profiles (only one eye visible), the correct side faces the correct image side, true transparency.
