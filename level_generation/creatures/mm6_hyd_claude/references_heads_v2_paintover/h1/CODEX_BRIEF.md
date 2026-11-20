# Codex brief: head 1 (OLIVE) texture turnaround for the MM6 Hydra (hyd)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_hyd_claude/references_heads/h1/`.
Do not edit any other file, do not run builds, do not call Meshy.

Purpose: these four views are projected by Meshy onto ONE EXISTING low-poly 3D head (the grey renders `shape_*.png` in
this folder are that exact mesh, from the exact cameras). They are texture references, so every painted view must
have the SAME silhouette, pose, scale and framing as its grey shape guide: paint over the guide's shape, do not
redesign, rotate, re-pose, enlarge or add parts that are not in the guide (anything outside the guide's silhouette
is lost; anything missing leaves the mesh unpainted).

Use your built-in image generation, record format of `../../references_hd/generation_runs.json`. Attached inputs:
1. `shape_front.png`, `shape_left.png`, `shape_back.png`, `shape_right.png` — the geometry authority (grey, transparent).
2. `../crops/h1_hd_front.png` — the accepted HD reference of this head (identity, colours, materials).
3. `../crops/h1_native_front.png` — the ORIGINAL MM6 sprite head (enlarged pixels; palette authority).

## Deliverables (4 images, transparent background, 1024 x 1024 square, unresized returns)
- `00_front.png` from `shape_front.png` (primary; generate first)
- `01_left.png` from `shape_left.png` (the creature's LEFT side)
- `02_back.png` from `shape_back.png`
- `03_right.png` from `shape_right.png` (the creature's RIGHT side)
Generate 01–03 with 00 as an additional input so all four are the SAME head with the same colours and markings.
Also write `generation_runs.json` and a `selected_views_review.png` contact sheet (guide and painted view side by
side). Regenerate a view whose silhouette visibly departs from its guide; record superseded runs.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: fully painted, high-definition TEXTURE REFERENCE of one head of
the Might and Magic VI five-headed Hydra, for projection onto the existing 3D head shown in the grey guide. Paint
exactly over the guide: same outline, same camera, same position and size in the frame, same pose; transparent
background, no floor, no shadow, no text. Even soft neutral studio light (no strong cast shadows, no rim glow), so
the texture is mostly surface colour; sharp fine detail; semi-realistic game material.

Head identity: olive yellow-green head with fine pebbled scales, a short crest of brown-orange spikes on the crown, bright yellow eyes with dark slit pupils, an open mouth with a dark red interior and small ivory fangs, and two thin golden barbels hanging down from the chin. The short piece of neck behind the skull: dark green scales on the back and sides, pale
grey-white horizontal belly rings underneath and in front, matching the rest of the hydra.

Do NOT: change the silhouette, add or move horns, fins, spikes or barbels beyond the guide, add a body or more neck,
glow, blood, effects or text; do not change the colours above.
Checks per image: silhouette matches the guide (overlay), eyes and mouth where the guide's eye sockets and mouth
are, transparent background, same head as the primary and as input 2.
