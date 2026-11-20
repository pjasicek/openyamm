# Codex brief: HD reference views for loot satchel tiers 5 and 6 (loot_satchel_claude)

Scope: image generation only. Write ONLY into `level_generation/props/loot_satchel_claude/references_hd/t5/`,
`references_hd/t6/`, `references_hd/generation_runs_t56.json` and `references_hd/selected_views_review_t56.png`.
Another Codex run may be writing tiers 1–4 in the same folder at the same time: do NOT touch `t1/`–`t4/`,
`generation_runs.json` or `selected_views_review.png`. Do not edit any other file, do not run builds, do not call Meshy.

Read `references_hd/CODEX_BRIEF.md` first: tiers 5 and 6 extend that four-tier family and follow ALL of its rules
(views, canvas, transparency, camera, prompt context, "Do NOT" list, per-image checks, record format), except where
this brief says otherwise. Use your built-in image generation.

Attached inputs, in order:
1. `references_hd/native_gold_piles.png` — native MM6 gold pile sprites: coin colour authority.
2. `references_hd/t3/00_three_quarter.png` and 3. `references_hd/t4/00_three_quarter.png` — the approved tier 3 and
   tier 4 primaries: family authority for leather, stitching, coins, gems, light and rendering style.

## Deliverables (8 images, transparent background, 1024 x 1024 SQUARE, unresized returns)
- `t5/00_three_quarter.png`, `t5/01_front.png`, `t5/02_side.png`, `t5/03_back.png`
- `t6/00_three_quarter.png`, `t6/01_front.png`, `t6/02_side.png`, `t6/03_back.png`
Same view definitions as CODEX_BRIEF.md (`02_side` shows the same side as the tier 1–4 side views). Generate each
tier's 00 first, then 01–03 with that 00 as an additional input. Give t6 the t5 00 as an extra input.

## Tiers
- **t5 — ornate treasure sack** (about 62 cm wide, about 40 cm tall): an open, ornate treasure sack of rich dark
  leather with gold-embroidered bands and gold corner fittings, its mouth wide open and overflowing; a generous low
  heap of gold coins spilling out in front (tight, connected, touching the bag), several faceted gems (red, blue,
  green) among the coins, and ONE clearly visible fine item lying on top of the spill at the front: a jewelled golden
  goblet lying on its side (or a gemmed golden circlet). Richer and bigger than t4, same family.
- **t6 — regal relic bundle** (about 72 cm wide, about 45 cm tall): the richest tier: a regal sack of deep royal-blue
  (or deep crimson) velvet-like heavy cloth and leather with dense gold embroidery and a gold drawstring cord with
  tassels, slumped open; a large, connected heap of gold coins and many gems spilling around its front; and on top
  of the heap an ornate golden RELIC that reads clearly at a distance — a gemmed golden crown with large glowing
  ruby and sapphire stones (the stones look softly luminous, lit from within, but with no light rays, bloom, sparkles
  or halo painted into the image). The crown must sit on the coins, fully visible, not floating.

Extra "Do NOT" for t5/t6: no chest or wooden box, no weapons, no scrolls, no candles, no glow halo or light rays, no
coins scattered far from the heap (keep the whole silhouette compact and grounded), nothing hanging off the frame.
