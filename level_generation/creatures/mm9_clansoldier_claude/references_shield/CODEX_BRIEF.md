# Codex brief: shield faces for the MM9 Horde Soldier (mm9_clansoldier_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_clansoldier_claude/references_shield/`. No builds, no Meshy. Use your built-in image generation tool.
Flat texture art for a medieval wooden shield of a fantasy video-game character, restored from a 2002 game for a game mod. It is mapped straight onto a 3D plate.

## Inputs (attached, in order)
1. `references_shield/outline.png`: the exact outline of the plate, tip at the bottom, on a transparent canvas. The art fills exactly this shape.
2. `references_shield/mm9_shield_x4_<tier>.png`: the original 256x512 skin enlarged. Design, colour and material authority. Its upper-left panel is the OUTER face, its lower-right panel is the INNER face, the small square bottom-left is a strap. Pale tan is unused background.

## Deliverables (true transparent background outside the outline, 1024x1536, unresized returns, no text)
For tier X: `<x>_outer.png` and `<x>_inner.png`. Seen straight on, perfectly flat, even soft light, no perspective, no cast shadow, no drama. The rim of the art follows the outline exactly and touches it all round. Semi-realistic game-art materials with sharp detail. At most one corrective regeneration per image. Keep raw returns in `raw/`. Write `generation_runs_<x>.json` (id, prompt, inputs with sha256, output path).

## Tier A
OUTER: vertical dark oak planks with grain, framed by a wide band of dark brown leather following the whole outline, black iron rivets along the band, as input 2. INNER: the same planks and band, plainer and darker.

## Tier B
OUTER: vertical oak planks framed by a wide band of dark iron with a raised bevel and small rivets along the whole outline; in the middle a large oval silver boss of Celtic knotwork, as input 2. INNER: the same planks and iron band, no boss.

## Tier C
OUTER: pebbled dark grey-brown leather framed by a wide band of polished steel with rivets along the whole outline; in the middle a red painted dragon emblem, a coiled serpent shape running top to bottom, as input 2. INNER: the same leather and steel band, no emblem.
