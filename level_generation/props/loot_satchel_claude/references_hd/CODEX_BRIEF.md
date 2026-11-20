# Codex brief: HD reference views for the four loot satchel tiers (loot_satchel_claude)

Scope: image generation only. Write ONLY into `level_generation/props/loot_satchel_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation (prompt style and record format as in
`level_generation/creatures/mm6_spi1_claude/references_hd/generation_runs.json`). Attached input:
1. `references_hd/native_gold_piles.png` — ORIGINAL native MM6 gold pile sprites (small, medium, large), enlarged
   6x with nearest neighbour. Magenta is background. Authority for the GOLD COIN colour, size relative to each other,
   and the warm, saturated, semi-realistic MM6 prerendered look. The coins are plain thick gold discs.

There is no native satchel sprite: these are new props for the same game (a loot bag that replaces a dead monster's
corpse). They must look like they belong to Might and Magic VI (1998 prerendered fantasy, warm, semi-realistic,
readable at a distance), all four as ONE art family (same leather, same stitching, same coins, same light).

## Deliverables (16 images, transparent background, 1024 x 1024 SQUARE, unresized returns)
One folder per tier, four views each, the prop centred with generous margins (about 15 % on every side):
- `t1/00_three_quarter.png`, `t1/01_front.png`, `t1/02_side.png`, `t1/03_back.png`
- `t2/...`, `t3/...`, `t4/...` the same four names.

Views: `00_three_quarter` = camera about 35 degrees to the right of the front and about 30 degrees above the ground
(the primary image; generate it first per tier — this image alone becomes the 3D mesh, so the whole silhouette,
the flap, the drawstring/buckle and every spilled coin must read clearly and nothing may be hidden or cropped).
`01_front`, `02_side` (pure right-side profile, the prop's right side toward the camera), `03_back` = camera about
20 degrees above the ground. Generate 01–03 with that tier's 00 as an additional input so all four views are the SAME
object, SAME shape, SAME details, SAME coin and gem positions.
Generate the tiers in order t1, t2, t3, t4 and give each later tier the earlier tiers' 00 images as inputs so the
leather, stitching, coins and lighting match across the family.

Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs) and a `selected_views_review.png` contact sheet (4 rows = tiers, 4 columns = views). Regenerate a view if it
breaks the checks below.

## Prompt content (adapt per tier and view)
TASK CONTEXT — MM6 FANTASY-GAME PROP: a 3D modelling reference for a loot bag lying on the ground in Might and Magic
VI. Beautifully detailed, credible, fully three-dimensional object with semi-realistic game materials and sharp fine
detail (leather grain, worn creases, stitching, scuffed edges, metal wear), warm natural colours, even soft neutral
studio light from above, near-orthographic camera, whole object inside the frame with generous margins,
transparent background, NO floor, NO ground plane, NO cast shadow, no text. The object rests on a flat ground plane
that is not drawn: its underside is flat where it touches the ground.

Shared family (all tiers): soft, thick, hand-stitched leather in warm brown tones, rounded and slumped under its own
weight (sagging into a wide base), visible seams with coarse thread, worn and scuffed lighter edges. Coins are
thick plain gold discs exactly like the native gold pile sprites.

- **t1 — small coin pouch** (about 22 cm wide, about 16 cm tall): a small plain worn light-brown leather pouch,
  round-bottomed, gathered at the neck by a leather drawstring cord tied in a simple knot with two short dangling
  ends; the frilled gathered top stands up a little. No metal, no coins visible. Humble and plain.
- **t2 — leather satchel** (about 32 cm wide, about 22 cm tall): a medium leather satchel/bag in mid brown, a rounded
  boxy body with a fold-over flap closed by a leather strap through a single square BRASS buckle on the front; a short
  carry handle or strap stub on top. Closed, no coins visible.
- **t3 — bulging bag** (about 42 cm wide, about 30 cm tall): a larger, overstuffed bulging leather bag in darker
  reddish-brown, the same flap-and-strap design as t2 with a brass buckle, but the flap is PARTLY OPEN (lifted and
  bent back) and a few gold coins show inside the mouth; FOUR or FIVE gold coins spill out on the ground in front and
  to one side of it (a small low scatter, two coins slightly stacked, all touching the ground plane and touching or
  very close to the bag).
- **t4 — rich treasure sack** (about 52 cm wide, about 36 cm tall): a rich, heavy treasure sack of DARK dyed leather
  (deep wine-red or deep oxblood), GOLD trim bands along its seams and around its mouth, a decorative ornate GOLD
  clasp on the front; its mouth is open and overflowing with gold coins; a generous low spill of gold coins on the
  ground in front of it (about ten to fifteen coins in a tight connected heap, not scattered far), and ONE large red
  RUBY and ONE blue SAPPHIRE (faceted, the size of a large coin) lying among the spilled coins at the front.

Do NOT: add straps hanging far away from the body, loose ropes trailing across the ground, a floor, a shadow, a
background, weapons, scrolls, potions or other objects; scatter coins far from the bag (keep every spilled coin
within a few centimetres of the bag so the silhouette stays compact); make it cartoonish or toy-like; change the coin
colour away from the native gold; crop anything.

## Per-image checks (re-run before selecting)
- One object, centred, fully inside the frame with margins; transparent background with clean alpha, no floor or
  shadow.
- Matches its tier description (t1 drawstring and no metal; t2 brass buckle and closed; t3 flap partly open with
  4–5 spilled coins; t4 dark leather, gold trim and clasp, coins and exactly one red and one blue gem).
- The four views of a tier are the same object (shape, flap state, coin and gem positions consistent).
- The four tiers read as one family and grow in size and richness t1 < t2 < t3 < t4.
