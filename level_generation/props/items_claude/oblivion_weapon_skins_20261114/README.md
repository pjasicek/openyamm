# Oblivion weapon tier skins (2026-11-14)

New high-resolution textures ("skins") for the Oblivion first-person weapon templates of the solo run
(`assets_dev/engine/view_model/`, devdocs/solo_action/WEAPONS.md "Tier skins (2026-11-14)"), one per item tier, picked
in game by the item's tier. The pilot made the one-handed sword (`w_longsword`), the two-handed sword (`w_claymore`),
the mace (`w_mace`) and the bow (`w_bow`) in three tiers; the rollout (approved by the user the same day) added a
fourth, **legendary** tier and every other template: `w_shortsword`, `w_dagger`, `w_waraxe`, `w_battleaxe`,
`w_warhammer`, `w_staff` (with `w_staff_grip`, the same mesh and paint) and `s_steelshield`, tiers 1-4. 44 skins
(45 files with the staff's grip twin), and the templates' winding fixed.

The Oblivion meshes are private (reference/oblivion_poc/README.md): nothing here or in `view_model/` is committed. This
folder's GLBs, images and Meshy returns are git-ignored by the level_generation rules (`work/`, `meshy/`, `review/`,
`ingame/` and every non-text file); only this README, the scripts and the request JSONs are tracked.

## Tiers and the mapping rule

| Tier | Look (the Codex masters' brief, `scripts/codex_masters.py` TIERS) |
|---|---|
| 1 low | crude: dark forged iron with hammer marks, grinding streaks and a few rust spots; blackened iron fittings; rawhide and cord grip; bow of weathered ash |
| 2 mid | clean craftsman's steel: satin flats with lengthwise grain, honed bright edge bevels; steel fittings with small brass accents; dark leather with steel wire; bow of polished yew |
| 3 high | masterwork: mirror-polished steel, an etched vine band in the fuller, gilded and engraved fittings with a red gem, crimson leather with gold wire; bow of black lacquer with gold inlay |
| 4 legendary | one look per weapon (`LEGENDARY`): longsword starmetal (blue-black, pale-blue rune line, sapphires), claymore star-metal (v2: blue-black blade, glowing cyan rune channel, crystals in guard and pommel; v1 dragonforged dropped), mace voidstone (near-black, violet runes, amethysts), bow star-metal (v2: blue-black limbs with glowing cyan-violet rune channels, platinum, glowing crystals; v1 bone and gold dropped), shortsword elven moonsilver (pale green, glowing leaf vein, emerald), dagger bloodsteel (crimson-black, red runes, garnet), war axe star-metal (v2; v1 dwarven runebronze dropped), battle axe frost steel (icy damascus, ice-blue runes), warhammer star-metal (v2; v1 stormforged dropped), staff star-wood (v2: a clean glowing double-helix channel; v1 archmage's dropped), shield star-metal (v2: glowing channels along the lames, cyan crystal studs; v1 dawn relic dropped) |

Families per template (`PARTS`): blade, metal fittings, grip (swords, dagger), axe head or hammer head, metal and haft
(axes, hammer), wood and metal (bow), staff wood and cloth wrap (staff), plates and strap (shield). Per weapon and tier
corrections go in `OVERRIDES` (the low bow).

Rule (data: `assets_dev/engine/world_items/held_tiers.yml`, `tiers: 4`; code: `heldSkinTier` in
`game/render/HeldWeapons.cpp`, tests in `tests/HeldWeaponTests.cpp`): the item's base value (items.txt Value) times its
equip stat's scale (`Weapon2` 0.5: two-handed weapons cost about twice their one-handed peers) below 150 is low,
150-599 mid, 600-4,999 high, 5,000 and up legendary; artifacts, relics and specials (items.txt material column, or the
copy's own rarity) are legendary (`unique_tier: 4`); a copy with a standard or special enchantment is one tier higher
(`enchanted_bonus: 1`) but at most high (`enchanted_max_tier: 3`). Examples: Iron Longsword 20 low, Dark Elven
Longsword 450 mid, Templar's Sword 600 high, Elsenrail (artifact) legendary, Iron Two-Handed Sword 200 low, Dragonning
Blade 1500 high (checked in game with `viewmodel equip`, `ingame/autotier/`). Helper C's new templates (spear, halberd,
trident, crossbow, wand, blaster) follow the same rule and files.

## Winding fix (approved 2026-11-14)

Oblivion's templates as exported wind every triangle against its vertex normals, and the engine culls by winding, so
it drew their far sides: guards, pommels and grips lit from behind and near black, a blade's back. `scripts/fix_winding.py
<glb>...` reverses the corner order of each primitive that mostly disagrees with its normals (the `[0, 2, 1]` flip;
`--check` only reports, a fixed file is left alone) and permutes a layout made on the old order
(`uv_template.npy`, `maps/uv_tris.npz`). It rewrote all 12 templates in place (`w_*.glb`, `w_staff_grip.glb`,
`s_steelshield.glb`); `assets_dev/engine/view_model/` and `reference/oblivion_poc/glb/` share them as hard links, so
both are fixed. Pre-fix originals: `work/templates_backup_20261114/` (0 % of triangles with their normals; now 100 %, the
bow 99.6 %: string slivers). In game the plain templates' guards, pommels and grips now read lit outdoors (the dungeon
is dim for every skin and template alike).

## Route (reusable for any template: helper C's new weapons use the same scripts)

1. `scripts/prep.py <template> 4` (Blender): the template's mesh in world space (its node's transform applied: the
   staff's node turns it 76 degrees) welded (the bow by position and string-morph delta, since its string stacks faces
   the morph pulls apart), `uv_atlas.unwrap()` defaults (PartUV, seam pass, sparrow), islands longer than 4x their
   width cut and repacked, the template's split normals back; `layout.blend` (locked), `layout_measure.glb`,
   `upload.glb`, the guides, and `uv_template.npy` (the new UV per template corner, matched to the Blender faces by
   corner positions within 1e-3 after the node transform; `scripts/template_uvs.py` recovers it for layouts made before
   the bow). Upright frame per template in `ORIENT` (the shield faces glTF -Y). 10-20 min CPU per template (two sparrow
   packs); `scripts/run_prep.sh <template>...` runs several.
2. `scripts/render_template.py`: the template textured in the guide framing (the design reference for Codex).
   `scripts/codex_masters.py brief|run|mirror <template> <tier>` (`MASTERS_JOBS=n scripts/run_masters.sh
   template:tier ...`): Codex HD masters over the guides; the views per template in `VIEWS`, its description in
   `WEAPON`, its material families in `PARTS`, the tier texts in `TIERS` (families blade, metal, grip, wood, axe, head,
   haft, staffwood, wrap, plate, strap), tier 4 per weapon in `LEGENDARY`. The image tool refuses weapon words as
   violence at random (mace, bow, dagger, axes, hammer, short sword, each once or twice): the briefs name regalia,
   ceremonial and armour-display props and tell Codex to retry a refused view once in neutral words and finish the
   others; a refused run's logs are moved to `masters_t<n>_refused/` and the run repeated. `mirror` writes the back as
   the mirrored front where the back is refused (the bow: its back guide is the mirrored front, IoU 0.997).
   `scripts/master_check.py`: IoU 0.71-0.99 (bows and the staff lowest: thin parts).
3. `scripts/meshy_request.py <template> <tier> [version]`: `requests/<template>_t<tier>_<version>.json` (`meshy-7`,
   original UVs, PBR, 4K, the masters as multiview; no text prompt). Submitted with `tools/run_creature_meshy.sh submit
   --kind retexture --credits 10` under the workspace claim (`engine:oblivion-weapon-skins`, budget 520 after the
   rollout), ledger `creature_3d_progress.json`; `scripts/poll_jobs.sh <token> <job>...` polls and downloads. Jobs
   return in 2-5 minutes; 14 at once were fine.
4. `scripts/bake_ao.py` (Cycles AO) and `scripts/post.py transfer <template>` (the template's specular mask, colour,
   positions, normals and the island coverage carried onto the new UVs), once per template; `post.py coverage` writes
   the coverage cache for older layouts.
5. `scripts/post.py skin <template> <tier> <job>` (`scripts/run_posts.sh template:tier:job ...`, `PARALLEL` at a time,
   about a minute each): 4K -> 2K once, Meshy's normal flipped to glTF, gentle grade, metal from Oblivion's specular
   mask (the bow's glossy wood taken out by colour; the staff's metal from the paint's gold and silver,
   `METAL_BY_COLOUR`), metal mask blurred within the islands only, Meshy's weave filtered on metal, metal albedo lifted
   to the tier's median (0.36 / 0.52 / 0.62 linear; legendary per weapon in `LEGENDARY_LUM`, lifted at most 3x),
   metal saturation capped at gold's (`METAL_SAT_MAX`), tier-1 rust non-metal; blades (`BLADED`: longsword, claymore,
   short sword, dagger) get the honed edge, grinding grain and polish variation; roughness by tier; per template
   adjustments in `TEMPLATE_CFG` (the shield). Legendary rune inlays (`RUNES`: hue, tolerance, saturation, value) become
   non-metal enamel with an `emissive.png` of their own colour. MR padded from the islands before its 1K downsample,
   then the nearest-texel gutter fill on every map (`gutter_fill.py`'s functions, coverage cached), then
   `scripts/write_skin.py`. A job of another tier repaints that paint (`RECOLOUR`: the low bow and the low staff).
6. `scripts/write_skin.py`: the skin GLB from the template's own JSON: nodes, names, transforms, the bow's animations,
   morph and arrow kept; the weapon primitive rebuilt and its material's three images replaced, an `emissiveTexture`
   (factor 1) added when `emissive.png` exists. Checked per skin: the same triangles by position. `w_staff_grip` takes
   the staff's layout and paint (`UV_FROM`; `post.py` writes it beside the staff's, `SAME_PAINT`). Installed by copying
   `work/<template>/t<tier>/*_t<tier>.glb` into `assets_dev/engine/view_model/`.

Fixes in the rollout:
- **Seam lines** (the claymore's quillons): the metal mask was blurred against the empty gutter, so island borders fell
  to about 65 % metallic and their lifted albedo drew as thin white diffuse lines. Now a normalised blur within the
  islands and the MR map padded before its downsample; the 12 pilot skins were rebuilt.
- **Low bow:** Meshy painted it as noise three times (v1 grey ash: zebra; v2 the same masters with both views: snakeskin;
  v3 plain dark elm: leopard spots; 30 credits). The low bow is now repainted from the mid bow's clean yew: its grain
  under a dark weathered elm brown with slow grime and worn patches from the 3D position, blackened iron fittings. The
  low staff (its Meshy draw a zebra too) is repainted the same way from the mid staff: grey-brown weathered wood and a
  hemp wrap. Rejected paints in `work/<template>/t1_rejected_v*/`.
- **Busy high mace:** redrawn (v2) from masters asking for a plain mirror-polished head with one gold band; v1's damask
  head is gone.
- **Gold read olive-green:** Meshy's gold came back near linear (1, 0.66, 0.05); capped at gold's saturation.
- **Shield:** its paint has no weave and its broad mirror plates reflected the dark ground (black-olive): more paint
  detail kept, darker plates and roughness raised by 0.32 (`TEMPLATE_CFG`).

Skins are 5-12 MB each (uncooked PNG; the view model folder is loaded raw).

## Bow v2: pieced upload (review 2026-11-14)

The user's review of the bow (idle, outdoors, 1600 x 900): "high blurred? legendary doesn't look legendary?". Fixed
for the high and legendary tiers; low and mid kept.

**Cause of the blur: the paint, not the layout or the resampling.**
- Layout (measured in game with a UV probe skin, a 16-texel checker per island, `viewmodel kit bow
  w_bowprobe.glb 0`, removed afterwards): the near limb at idle draws 2.0-3.5 texels of the 2K map per screen pixel
  (the cells square, no anisotropy), so the engine samples mip 1 there. The layout was never the limit.
- Resampling: Meshy's 4K map is downsampled to 2K once (post.py step 1); the view model folder is loaded raw. No
  second downsample.
- The visible face: the probe showed the camera looks along the bow's plane at the limb's belly (the face toward the
  string) at idle and through the whole draw. The v1 guides showed the bow in profile (the only views Codex and Meshy
  got, front and back), so that face was edge-on in both: Meshy smeared it into lengthwise streaks and blobs. The whole
  bow was also small in the guides: 24.6 px per unit, a limb 40 px wide.
- The post: Oblivion's specular mask marks the limb tips and the riser as metal, and post.py kept only 10 % of the
  detail finer than 4.5 texels on metal (the weave filter meant for blades): the high bow's gold filigree there went
  soft (island 9: -16 % of the sigma-2 detail).

**Fix (no layout change, so the low and mid skins stay valid):**
- `scripts/prep_pieced.py` (Blender, on the locked `layout.blend`): the bow cut at its material breaks (tips at
  |y| 37, riser at |y| 6), each piece stood upright by its chord and turned so the belly faces Meshy's front, the five
  pieces side by side (the lower limb and tip, never on screen at idle, at half scale), the string (a 48-triangle
  part) left out: `work/w_bow/pieced/` (upload, guides, `reference_*` with Oblivion's colour, `previous_t<n>_*` with
  each tier's v1 paint). The guides now carry **50.3 px per unit** of the visible face, face-on (was 24.6, edge-on).
- `scripts/codex_masters_pieced.py brief|run|mirror w_bow <tier> v2`: the masters over the pieced guides (the tier
  rule below; the front of tier 4 was refused once as violence and went through on the neutral retry; IoU 0.93-0.95).
- `scripts/meshy_request.py w_bow <tier> v2 --pieced`; post.py: the bow keeps 85 % of the fine detail on metal
  (`TEMPLATE_CFG`), its high and legendary metal from the paint's gold and platinum (`METAL_BY_COLOUR`), the string's
  texels from the tier's v1 skin (`PIECED`, the legendary's recoloured pale silver: `STRING_COLOUR`), legendary runes
  and gems by hue (`RUNES`: cyan 185 and violet 275) with `KHR_materials_emissive_strength` 2.5
  (`EMISSIVE_STRENGTH`, written by write_skin.py from `t<tier>/emissive.json`).
- Measured: fine detail (sigma 2 texels) in the islands seen at idle, high bow 0.04-0.08 -> 0.14-0.17 (2-4x),
  legendary 0.04-0.05 -> 0.08-0.16 (one plain dark face 0.05 -> 0.03). Texture memory unchanged per skin: colour and normal 2K, MR 1K (and the
  legendary's emissive 1K), about 48 MB as RGBA8 with mips (53 MB with the emissive); the GLBs are 12.2 and 12.7 MB
  (sharper paint compresses less; v1 8.5 and 8.9).

**Tier rule (shared by the skin helpers, 2026-11-14):** high is polished ebony with gold filigree, crimson leather and
gold fittings and does not glow; legendary is the only tier that glows: dark star-metal with a blue-violet sheen,
platinum fittings, luminous cyan-violet rune channels along the limbs (emissive) and glowing crystals at the grip and
the tips. Verdict (`ingame/bowv2/`, outdoors and in 6d05): the high limb shows crisp gold vine filigree on black with a
crimson, gold-wired grip (v1: soft gold blobs); the legendary reads at a glance as magical: a blue-black limb with a
bright cyan-to-violet rune channel, platinum tip and wire, glowing in the dungeon too (v1: plain bone-white). The
grip crystal is mostly under the hand; the tip crystals are off screen at idle. Low and mid were re-checked: their
plain lengthwise grain hides the same edge-on paint, so they were kept (no credits). v1 maps: `work/w_bow/t3_v1/`,
`t4_v1/`. Credits: 2 jobs, 20 (ledger total 490).

## Legendary v2 (2026-11-14)

The bow's review led to one rule for every legendary (see "Bow v2"); five of the v1 legendaries failed it: the claymore
(its runes came out dark), the war axe, the warhammer and the shield (no emissive at all; they read close to their high
tier) and the staff (a patchy speckled glow, no channel). All five were redone in the shared look: dark star-metal
(the staff: star-wood) with a blue-violet sheen, platinum fittings, glowing cyan-to-violet rune channels on the parts
seen at idle and in the swings, glowing violet-cyan crystals. Low, mid and high are unchanged (same layouts); the v1
legendary maps are in `work/<template>/t4_v1/`.

- **Uploads:** the claymore and the staff were small in their full-length guides (blade about 40 px wide, 14 px per
  unit; staff shaft about 35 px, 11.4 px per unit): `prep_pieced.py` cuts them into side-by-side pieces (claymore:
  upper blade, lower blade, hilt; staff: head, two shaft pieces, the butt at half scale), 28.5 px per unit for both.
  Their blade and shaft are a few sliver triangles longer than a piece, so the upload's triangles are bisected at each
  cut first (UVs are affine on a triangle: the parts cover exactly the same texels). The war axe's and warhammer's
  heads and the shield already filled their guides face-on: they keep their uploads with new masters.
- **Masters:** `codex_masters_pieced.py brief|run <template> 4 v2` (`LAYOUTS`, `LEGENDARY_V2`; one Codex session at a
  time, IoU 0.87-0.99; one refusal on the warhammer, through on the retry). `meshy_request.py` takes
  `masters_t<tier>_<version>/` when it exists.
- **Post:** `RUNES` `STAR_RUNES` (cyan 185, violet 275) and `EMISSIVE_STRENGTH` 2.5 for all five. Meshy kept the
  masters' channels on the claymore, war axe head, warhammer head and shield, but dropped the staff's channel and
  crystal (dark blue noise), and the twisted platinum shafts of the war axe and the warhammer, which fill the idle
  frame, have none in the masters. Those get **procedural channels** (`CHANNELS`, `procedural_channels`): drawn from
  each texel's template position, so continuous across UV seams; the staff a double helix (one turn per 28 units,
  0.34 units wide, diamond nodes every 3.2) with a faceted crystal on each side of the claw's knot, the two shafts three
  straight channels each (y 6.5-20.8 and 6.3-18.3).
- **Verdict** (`ingame/legv2/`, t3 against t4, idle and swings, oute3 and 6d05): every one reads clearly more magical
  than its high tier at thumbnail size, the glow carrying in the dungeon. Claymore: blue-black blade with a bright cyan
  rune channel, crystals in the guard and the pommel. War axe: star-metal head with glowing trims and a violet-cyan
  medallion crystal, a glowing channel on the shaft, a cyan crystal end cap; Meshy's head paint is streaky. Warhammer:
  glowing panel sigils, cyan-edged spike, a glowing channel down the shaft at idle. Staff: one clean continuous
  glowing helix (no speckle); the claw crystal is small and the wrap is Meshy's bright blue weave. Shield (seen in the
  block poses only): near-black lames with glowing cyan and violet channels, a platinum rim with cyan crystal studs.
- **Credits:** 5 jobs, 50 (ledger total 540). Skins 9.4-11.5 MB; texture memory as before per skin (about 53 MB with
  the 1K emissive as RGBA8 with mips).

## Credits and measures

Pilot: 12 jobs, 120 credits. Rollout: **35 jobs, 350 credits** of its 400 (ledger total 470): tier 4 of the pilot
weapons (4), tiers 1-4 of the seven new templates (28), the low bow v2 and v3 (2, both rejected) and the high mace v2
(1). Every job succeeded on Meshy's side; task ids in `creature_3d_progress.json`.

Layouts (`texture_quality.py` on `layout_measure.glb`, 2048; density in texels per model length; about 70 units per
metre):

| Template | Atlas | Equivalent px | Density p10/p50/p90 | Per metre (p50) | Spread | Stretch p90 |
|---|---|---|---|---|---|---|
| w_longsword (79 units, 1.13 m) | 40.9 % | 1,310 | 3,471 / 3,871 / 4,244 | ~3,400 | 1.22 | 1.66 |
| w_claymore (96 units, 1.38 m) | 56.2 % | 1,535 | 4,778 / 4,972 / 5,145 | ~3,600 | 1.08 | 1.62 |
| w_shortsword (53 units, 0.75 m) | 48.0 % | 1,419 | 3,715 / 3,806 / 3,978 | ~5,100 | 1.07 | 1.19 |
| w_dagger (32 units, 0.45 m) | 78.0 % | 1,809 | 3,762 / 3,910 / 4,182 | ~8,600 | 1.11 | 1.17 |
| w_mace (53 units, 0.76 m) | 77.5 % | 1,803 | 3,384 / 3,614 / 3,789 | ~4,800 | 1.12 | 1.22 |
| w_waraxe (48 units, 0.69 m) | 81.7 % | 1,851 | 3,041 / 3,204 / 3,364 | ~4,700 | 1.11 | 1.20 |
| w_battleaxe (61 units, 0.87 m) | 76.2 % | 1,787 | 2,926 / 3,108 / 3,263 | ~3,600 | 1.12 | 1.21 |
| w_warhammer (60 units, 0.86 m) | 72.1 % | 1,739 | 2,941 / 3,163 / 3,411 | ~3,700 | 1.16 | 1.27 |
| w_staff (119 units, 1.70 m) | 69.3 % | 1,705 | 5,053 / 5,283 / 5,484 | ~3,100 | 1.09 | 1.32 |
| w_bow (55 units, 0.79 m) | 76.2 % | 1,788 | 6,123 / 6,582 / 6,930 | ~8,300 | 1.13 | 1.17 |
| s_steelshield (47 units, 0.67 m) | 73.0 % | 1,750 | 1,475 / 1,535 / 1,601 | ~2,300 | 1.09 | 1.14 |

The swords miss the 65 % atlas target: their blades are a few single triangles 25-57 times longer than wide, which no
cut can split without new geometry (kept: the mesh is the template's). Their density is still about 3x what the
screen shows (a held blade covers about 1,100 px per metre at 1600 x 900).

## In-game checks

`scripts/run_ingame.sh <template> outdoor|indoor <tag> ["tiers"]` (`scripts/run_captures.sh <tag> template:place ...`,
`PARALLEL` runs at a time): 1600 x 900, `--ruleset maw:solo`, MM6 New Sorpigal (oute3) at 9 am and Corlagon's dungeon
(6d05), `viewmodel kit <set> <file> <shield>`, then for `viewmodel tier 0` (the plain template) to 4 and our ground
model (`viewmodel weapons ours` + `viewmodel held <icon>`): idle and two swing moments (`swing`, `swing2`): swords the
left and right cuts, maces, axes and hammers the right-hand backswing and blow (`ingame/posetest/`), the bow drawing
and at full draw, the shield held alone (`kit onehand none 1`) raised (`blockidle`) and taking a hit (`blockhit`); the
staff is held as `w_staff_grip`. `scripts/make_sheets.py <tag> [template...] [--cell W]`: `review/<template>_tiers.jpg`.
`scripts/to_viewer.py <tag> <dir>`: 1280 x 720 JPEGs named `<template>_<place>_<tier>_<pose>.jpg`. Final captures:
`ingame/v6/` (all 11 templates, 396 images); `ingame/autotier/`: the automatic tier from equipped items.

Verdict at full size (v6):
- **Longsword, claymore, short sword:** low dark grimy iron, mid clean steel with honed edges, high bright steel with
  the etched band and gilded guard, legendary clearly apart (starmetal with a glowing pale-blue rune line and sapphires;
  dark damascus with gold dragon scales and rubies, its runes dark rather than orange as Meshy painted them; moonsilver
  with a glowing green leaf vein). The claymore's quillon seam lines are gone.
- **Dagger:** small on screen; low and mid differ in finish more than colour, high gilded guard, legendary crimson-black
  with a glowing red rune line.
- **Mace:** low rusty iron, mid polished steel, high (v2) calm silver head with gold bands, legendary voidstone with
  glowing violet runes.
- **War axe, battle axe, warhammer:** low rough grey iron, mid polished steel, high gold-engraved, legendary runebronze
  (war axe), frost steel with glowing ice-blue runes (battle axe), gunmetal with gold and blue enamel (warhammer). Low
  and mid read close on the hammer (pale rough iron against polished steel).
- **Bow:** low dark weathered elm (repaint), mid orange yew, high black lacquer and gold, legendary bone and gold
  (superseded by "Bow v2" below: high sharp, legendary star-metal);
  string morph and nocked arrow as on the template.
- **Staff:** low grey weathered wood with a hemp wrap (repaint), mid walnut with a blue wrap (the wrap's weave a little
  noisy), high dark wood with a crimson wrap and gold, legendary violet with silver stars (speckled, busier than the
  others).
- **Shield:** the player sees its inner face; low dark pitted iron, mid satin steel, high warm engraved plates with gold
  borders and a crimson strap, legendary dark blued steel with the gold sun lines and gems. Glossy plates mirrored
  the dark ground (high read black-olive), so the shield's metal is rougher than the other templates'. Idle shows no
  shield (Oblivion's idle holds it off screen).
- **Dungeon:** every skin readable but dim; dark legendary metals rely on their runes there.
- **Automatic tier** (`viewmodel equip`): Iron Longsword low, Dark Elven Longsword mid, Templar's Sword high, Elsenrail
  legendary, Iron Two-Handed Sword low, Dragonning Blade high.
