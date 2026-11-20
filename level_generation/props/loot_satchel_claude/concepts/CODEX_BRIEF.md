# Codex brief: loot satchel tier concept sheets (loot_satchel_claude/concepts)

Scope: image generation only. Write ONLY into `level_generation/props/loot_satchel_claude/concepts/`.
Do not edit any other file, do not run builds, do not call Meshy.

## Context
OpenYAMM replaces a slain monster's body in Might and Magic VI (1998, prerendered, warm, semi-realistic fantasy) with
a loot bag lying on the ground. Six tiers by loot value:
1. 1-99 gold (a few coins), 2. 100-749, 3. 750-2,999, 4. 3,000-7,999, 5. 8,000-14,999 (a rich hoard or an artifact),
6. 15,000+ (an artifact or relic).
The player sees the bag from a first-person camera 2-15 m away, often in grass. The tier MUST be obvious at a glance,
at a distance, from colour and size before any detail.

Attached inputs, in order:
1. `concepts/mm9_bags.png` - Might and Magic IX's five treasure bags: one crude low-poly sack, the tier shown only by
   its fabric (burlap, green wool, leather, floral brocade, red velvet with a gold band). They are ugly; do NOT copy
   their look. They are here because the tier was obvious at a glance: that readability is the goal.
2. `concepts/current_tiers.png` - our current six 3D tiers. Problem: they are all similar browns and reds and the
   spilled coins dominate, so the tier does not read. Do not draw spilled coins in any concept.
3. `../references_hd/native_gold_piles.png` - original MM6 gold pile sprites (magenta background), the authority for
   the game's warm, saturated, prerendered look.

## Deliverables
Five concept sheets, landscape 1536 x 1024, each one design direction, plus `generation_runs.json` (id, prompt,
inputs with sha256, output path, selected flag, reason) and `concepts_review.png` (the five sheets stacked, scaled to
fit 1536 wide). Regenerate a sheet if it breaks the checks below.

Every sheet: a top row with the six tiers left to right (1 to 6), each on the same plain mid-grey-green ground, the
same three-quarter camera about 30 degrees above the ground, the same soft light from above, a small tier number
under each; below it a second row "distance test" with the same six drawn about one sixth of the size, side by side
on a patch of short green grass, so readability at a distance can be judged. Sizes grow gently with the tier
(tier 6 about twice the width of tier 1). Semi-realistic MM6 prop rendering: fully three-dimensional, real materials
(cloth weave, leather grain, metal wear), warm natural colours, NO spilled coins, no text other than the tier
numbers and the sheet title. Simple, strong silhouettes: these become low-poly game props (400-1,800 triangles).

Sheets:
- `A_material_ladder.png` - title "A: material ladder". One drawstring-sack silhouette for all six; the material
  tells the tier: coarse undyed burlap, then patched green wool, then tanned brown leather, then deep blue dyed leather
  with brass fittings, then rich embroidered brocade, then royal velvet with gold embroidery and a gold cord. Each
  step must contrast clearly with its neighbours in hue and value.
- `B_rarity_colours.png` - title "B: rarity colours". The same plain brown leather sack for all six; the tier is a
  broad coloured cloth band around the neck plus a matching wax seal or tassel, in classic RPG rarity colours: grey,
  green, blue, purple, orange, gold. Tiers 5-6 add metal corner fittings. The band colour must read from far away.
- `C_container_ladder.png` - title "C: container ladder". The silhouette itself tells the tier: small coin purse,
  belt pouch, shoulder satchel, large bulging sack, small iron-banded coffer, ornate gilded reliquary chest.
- `D_fittings_and_fullness.png` - title "D: fittings and fullness". One material family (dark leather), the sack
  grows fuller and taller and gains fittings: plain cord tie, leather strap, brass buckle, brass clasp with studs,
  silver filigree straps, gold filigree straps with a large gem clasp.
- `E_material_plus_glow.png` - title "E: material plus glow". Like A for tiers 1-4 (burlap, wool, leather, dyed
  leather); tiers 5-6 are deep jewel-toned velvet (5 emerald green, 6 royal purple) with gold embroidery and a soft
  magical glow from a rune or gem on the clasp (5 faint, 6 stronger), so artifact tiers stand out at night and in
  dungeons.

## Checks before selecting a sheet
- six distinct objects in the top row and six in the distance row, in tier order, none cropped;
- at the distance-row size, every tier is distinguishable from its neighbours by colour and/or silhouette alone;
- no spilled coins, no floor shadows that hide the base, no extra text;
- the same camera and light for all six on a sheet.
