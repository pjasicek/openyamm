# Solo action mode: held weapons plan

What the first-person arms hold for every weapon a character can wield, which animation set and attack paths each
uses, where the models come from, and in what order to build it. Written 2026-11-13 for the user's questions: "how to
handle 2h stuff like 2h weapons, halberds, spears, staffs ... also are the weapon models from Oblivion?", plus "the
staff attack isn't that good" and "the sword should also have a vertical slash". Research and plan only; the engine
work it references (swings fitted to MM's recovery, chop variants in the combo, staves on the two-handed set, the
whoosh at swing start) is being built separately.

**No shield on screen (user, 2026-11-14):** the arms never show a shield, whatever the off hand holds: a character
with a weapon and a shield is drawn with the weapon alone, and a guard (Shield Wall) plays the weapon set's own
`blockidle`. `Kit` has no shield fields since; the shield passages below are the earlier design. The steel shield
template and its skins (`s_steelshield*.glb`) are no longer drawn.

## Where the models come from today

All held models in the prototype are **Oblivion's** (private, `reference/oblivion_poc/`, never shipped): the steel
longsword, shortsword, claymore, dagger, mace, war axe, battle axe, warhammer, steel bow, a test staff and the steel
shield. They are stand-ins chosen by skill group (`FirstPersonViewModel::kitFor`), so every MM sword looks like the
same steel longsword. **Oblivion has no spears, halberds, tridents, crossbows, blasters or wands**, and its
`staffattack*` clips are a spell-casting gesture, not a blow.

**What can ship:** our own item models. Every MM6–MM8/MMerge weapon icon already has a 3D ground model
(`assets_source/engine/world_items/models/item_<icon>.glb`, bound in `engine/world_items/items.yml`, 911 icons).
Measured against Oblivion's (2026-11-13):

| | Triangles | Textures | Note |
|---|---|---|---|
| Oblivion steel longsword / claymore / mace | 1,270 / 1,390 / 1,450 | 512² (diffuse, normal) | The 2006 standard the arms were made for |
| Ours: Iron Longsword `item001` | 1,822 | 1024² (base colour, normal, ORM) | PBR |
| Ours: Two-Handed Axe `item036`, Sturdy Mace `item066` | 1,986 / 3,484 | 1024² | |
| Ours: Steel Spear `item042`, Halberd `halberd1`, staff `item079` | 1,340 / 2,140 / 1,150 | 512×1024 | Long weapons: half the density |

So our models already match or beat Oblivion's budget for one-handed weapons; long polearms are the weak spot (512
px across a 2 m shaft, and alpha-cut heads show stair-stepped edges up close: the halberd head in
`reference/oblivion_poc/preview/weapons_ours/sheet.jpg`). They were built for the ground at a distance, so a held
pass is needed (below), not new models.

## Wield rules (our code)

- **Standard** (`ItemRules::wield`, `GameMechanics` equip plan): `Weapon2` items are two-handed; `Weapon1or2`
  (spears, tridents, halberds) need **both hands below Spear Master** and take a shield or off-hand weapon from
  Master on; a spear with an empty off hand gains +1 damage. Off-hand weapons (dual wielding): **Dagger Expert**,
  **Sword Master** (one-handed swords and daggers only). Clubs need no skill. Wands (`WeaponW`) are main-hand.
  Bows and crossbows are `Missile` in their own slot.
- **MAW** (`MawItemRules::wield`): Seraphim hold any sword one-handed and never off-hand; **Dwarves and Minotaurs**
  hold axes in the off hand from Axe Expert; **Minotaurs** hold two-handed axes and halberds one-handed, off-hand
  from Axe Master. Halberds (`mawIsHalberd`) train with the better of Spear and Axe.
- **MM9** (`worlds/mm9/data_tables/items.txt`, its own items): two-handed spears and halberds (`Weapon2` Spear: 9),
  a two-handed mace (Thjorad), and **throwing weapons** (`Missile` Throwing: throwing dagger and axe).

The view model must follow `wield().twoHanded` and what is actually in the off hand, never the item's table type
alone (a Minotaur's halberd is one-handed).

## Weapon kinds → animation set → attack paths

Oblivion's first-person clips per set (`arms_full.textkeys.json`): `attackright`, `attackleft` (a right–left combo
chained at `a:L`/`a:R`), `attackright_chop`, `attackleft_chop` (the same swings turned towards vertical), `attackpower`
(standing overhead), `attack{forward,back,left,right}power`, four perk power attacks `skill1`–`skill4`, plus the
hand-to-hand `jab` and `hook` variants. Checked in Blender (`reference/oblivion_poc/preview/weapons_ours/sheet_b.jpg`):
**`onehandattackforwardpower` at its Hit is a straight forward thrust**: the only real thrust Oblivion has, and it
reads as a spear thrust with a long shaft. `twohandattackforwardpower` is an overhead downward chop, not a thrust.

| Kind (skill, table type) | Hand rule | Set | Attack path (repeat presses) | Model now → shippable |
|---|---|---|---|---|
| Sword (Sword, `Weapon`) | 1H; off-hand at Master | onehand | right → left → right_chop → left_chop (the vertical slash the user asked for); moving forward: forwardpower thrust as the 3rd blow | Oblivion longsword → our item models |
| Dagger (Dagger, `Weapon`) | 1H; off-hand at Expert | onehand at 1.25× pace | right → left → forwardpower (stab) | Oblivion dagger → ours |
| Two-handed sword (Sword, `Weapon2`) | 2H (Seraphim 1H) | twohand | right → left → right_chop → attackpower (overhead) | Oblivion claymore → ours |
| Axe (Axe, `Weapon`) | 1H; MAW off-hand | onehand | right_chop → left_chop → right (axes chop) | Oblivion war axe → ours |
| Two-handed axe (Axe, `Weapon2`) | 2H (MAW Minotaur 1H) | twohand | right_chop → left_chop → attackpower | Oblivion battle axe → ours |
| Poleaxe (Axe, `Weapon2`; held.yml kind `poleaxe`) | 2H (MAW Minotaur 1H) | **pole** (since 2026-11-14) | jab → jab → sweep → chop → power (lunge standing) | our halberd template |
| Mace, club (Mace / Club, `Weapon`) | 1H | onehand | right → left → attackpower (overhead smash) | Oblivion mace → ours |
| Two-handed hammer/mace (MM9 Thjorad) | 2H | twohand | right → left → attackpower | Oblivion warhammer → ours |
| Staff (Staff, `Weapon2`) | 2H | **twohand** (not `staff*`) | right → left → attackpower; gripped at mid-shaft, so it swings as a quarterstaff | Oblivion test staff → ours |
| Spear, trident (Spear, `Weapon1or2`) | 2H below Master, 1H with a shield from Master | **pole** (since 2026-11-14; before: twohand) | jab → jab → sweep → chop → power (lunge standing) | our spear and trident templates |
| Halberd, voulge, MM9 bills (Spear `Weapon1or2`/`Weapon2`; kind `polearm`) | 2H; MAW Minotaur 1H | **pole** (since 2026-11-14; before: twohand) | jab → jab → sweep → chop → power (lunge standing) | our halberd template |
| Fists (no weapon) | — | handtohand | right → left → right_jab → left_hook (Oblivion's own jab/hook) | arms only |
| Bow, crossbow (`Missile` Bow) | own slot | bow; crossbow (built, see "Crossbow set") | draw, hold, release; crossbow: raise, release, recoil, span | Oblivion bow → ours; our crossbow template |
| Throwing (MM9 `Missile` Throwing) | own slot | onehand | `attackright` released at Hit with the item flying | ours |
| Wand (`WeaponW`) | 1H main | onehand | `onehandcasttarget` (point and release) with the wand in hand | ours |
| Blaster, rifle (Blaster, `Weapon`) | 1H | onehand | `onehandcasttarget` hold plus a code recoil kick; no swing | ours |

Attack paths are data, not code: a small table per kind (clip list, chain order, the movement-direction overrides),
so changing the sword's third blow is one line. Power and perk clips (`attackpower`, `skill1`–`4`) are the natural
look for special skills on the action bar (Cleave, Shield Bash's partner blow, a mastery finisher), not for the
normal chain, so the normal chain stays fast.

**Spears and polearms in two hands.** Oblivion has no two-handed thrust. Interim: the onehand forward-power thrust
for every spear (the off hand hangs, acceptable for a thrust), the two-handed chops for halberds. Shippable: one own
clip pair, a two-handed thrust and a two-handed sweep, keyed with the same text keys (`Hit`, `a:L`/`a:R`, `Blend`),
made in Blender on the arms rig; this is the only animation the plan needs that Oblivion lacks. Built (keyframed in a
script rather than in Blender, with the whole combo): see "Pole set (2026-11-14)" below.

**Dual wielding** (Dagger Expert, Sword Master, MAW axes). Oblivion has no off-hand attacks. Interim: the off-hand
weapon hangs on the left hand and the right arm attacks as usual (MM resolves both weapons in one attack anyway).
Shippable: mirror `attackright`/`attackleft` onto the left arm in Blender and alternate main and off hand (right,
off-left, right, ...), the same blow per press as MM's single attack roll. Built: see "Dual wielding (2026-11-14)" below.

**A two-handed weapon with a shield** (MAW Minotaur halberds, Spear Master): use the onehand set with the shield on
the left forearm, as Oblivion does for any one-handed weapon; the long shaft simply extends past the hand.

## Grip alignment: making a ground model a held weapon

The arms expect each weapon in the weapon node's space: the **palm at the origin, the head along +Y, the edge's
width along X, the flat along Z**, in Oblivion units (≈1.43 cm). Oblivion's own grips, measured: swords palm just
below the guard (longsword 15 % of the length from the pommel, claymore 21 %), one-handed axes and maces 30 %, the
staff 71 % (a casting staff).

The probe `level_generation/solo_action_weapons_20261113/scripts/align_held.py` does it automatically from a ground
model: longest axis → +Y, widest → X; the **widest slice** decides the ends (a sword's or dagger's guard marks its
butt end, any other weapon's head is its widest part); the grip sits 6 % of the length below a sword's guard, else at
a fraction of the length from the butt by kind (axe and mace 0.30, staff 0.5, spear and polearm 0.35); the length is
set by kind (dagger 32, sword 79, greatsword 96, axe 50, two-handed axe 64, mace 53, hammer 62, staff 120, spear
140, polearm 150). Renders of seven ground models in the arms:
`reference/oblivion_poc/preview/weapons_ours/sheet.jpg` and `sheet_b.jpg` (private: the arms are Oblivion's).

What the probe showed:

- Swords, axes, maces and the halberd land in the hand the right way round with the automatic rule.
- **The spear came out upside down**: its butt cap is wider than its point, so the widest-slice rule picked the
  wrong end. Some models will always need a hand correction.
- So the shippable route is **automatic plus an override table**: `engine/world_items/held.yml` (or a `held` block
  on each `items.yml` entry): kind, flip, grip fraction, roll, length. Generated once by the script for all weapon
  icons, then checked on a contact sheet (each weapon in the idle pose and at a swing's Hit) and corrected by hand
  where wrong; expect 10–20 % to need a flip or grip nudge.
- The blade tip (already computed from the model's bounds for the blow direction and the coming trail) comes from
  the same table: the +Y end.
- Scale is per kind, not from the ground model (ground lengths follow the icon size, e.g. a 2.5 m spear and a 1.35 m
  longsword at ground scale).

## Held weapons in the game (built 2026-11-14)

A solo run's arms now hold **our own ground item models** instead of Oblivion's templates: the active member's main
hand, shield and bow. A model without a grip falls back to the template; `viewmodel weapons oblivion|ours` switches
for comparison, and `viewmodel held <icon>` holds any icon's model (contact sheets).

- **The table:** `assets_dev/engine/world_items/held.yml` (schema `openyamm.heldWeapons.v1`), a separate file beside
  `items.yml`, written by `level_generation/solo_action_weapons_20261113/scripts/make_held_table.py`. It is separate
  because it serves only the solo run's presentation, and is generated from geometry with hand corrections kept in
  the script's `OVERRIDES` (regenerating keeps them). It holds 334 models: 51 swords, 31 daggers, 17 greatswords,
  21 axes, 11 two-handed axes, 6 poleaxes, 21 maces, 14 hammers, 8 clubs, 15 staves, 20 spears, 14 tridents,
  11 polearms, 15 wands, 5 blasters, 24 bows, 12 crossbows and 38 shields. Every weapon, shield and bow icon with a
  ground model has a row.
- **Per row:**
  - `long`: the shaft axis.
  - `head`: which end is the head.
  - `edge`: the side the edge, an axe's blade, a bow's riser or a gun's handle faces.
  - `grip`: the palm, as a fraction from the butt.
  - `length`: by kind, ±15 % by the model's ground length.
  - `across`: the shaft's place across the model.
  - `girth`: a shaft thinned to a hand's grip.
  - `roll`.
- **The matrix** is built at load from the model's bounds (`game/render/HeldWeapons.cpp`, `heldWeaponMatrix`). It is a
  rotation without mirroring, a scale and a translation, carried by a new optional `localMatrix` on
  `Engine::ModelAttachment`, applied in `ModelRenderer` and the picking bounds. Mounts:
  - Hand: the Weapon node.
  - Gun: the Weapon node, muzzle along +X (out of the knuckles), the handle down through the fist. Until
    2026-11-14 the muzzle went to −X, which points it at the eye ("Blaster, wand and crossbow after the review").
  - Shield: the left forearm, face −Y, top −Z (measured from Oblivion's steel shield).
  - Bow and Crossbow: the left hand's `Torch` node. A crossbow is carried on the Weapon node at the place the
    crossbow set's clips keep that frame ("Crossbow set" below).
- **How the head is found:**
  - Blades: the guard is the widest slice, and the tip is the far end.
  - Axes, maces, poleaxes and shields: the head is the widest slice.
  - Spears, tridents, halberds and staves: flatness (a blade or prongs are flat, a butt cap is round), else the
    end-quarter width.
  - Blasters: the narrow muzzle.
- **Hand corrections:** `7item003` (a sword) and `item242` (Spiritslayer).
- **Checks:**
  - Blender renders of all 334 at idle and at a swing's Hit, placed as the engine places them
    (`reference/oblivion_poc/tools/render_held.py`): `reference/oblivion_poc/preview/held/sheet_<kind>.jpg`.
  - In game: 19 representative models in idle and at the Hit (`held/ingame_idle.jpg`, `ingame_hit.jpg`), and the
    swap (`held/swap_v1.jpg`).
  - Re-run: `held/run_captures.sh`.
  - Unit tests: `tests/HeldWeaponTests.cpp`.

| Kind | Verdict | Remaining gap |
|---|---|---|
| Swords, daggers, greatswords | Right way up, palm below the guard | Translucent blade textures read pale in Blender; single-edged blades' edge side unchecked |
| Axes, two-handed axes, poleaxes | Head up, blade side from the head's offset | — |
| Maces, hammers, clubs | Head up | Flails' heads are rigid balls (no chain) |
| Spears, tridents, halberds | Heads at the far end after the flatness rule | Long shafts thinned only to 0.7 (bladed heads share the cross axes); polearm textures 512×1024 over a 2 m shaft |
| Staves | Ornament up | Thinned up to 0.45, which also slims ornaments (serpent, bone) |
| Wands | Head up | — |
| Blasters | Held as pistols, muzzle forward | No aim or recoil clip: swings use the one-handed set |
| Bows | Riser in the left hand, string toward the archer | Static: no string draw, no arrow (Oblivion's bow animates both) |
| Crossbows | Stock forward, the foregrip in the left fist, carried by the right hand in the crossbow set | Our ground models' prods are wide and their stocks short: they read less well than the template |
| Shields | Face out, emblem upright, top up | Kite shields sit low in the block pose, as Oblivion's does |

## Bow swap (built 2026-11-14)

In a solo run the player can swap the arms and the attack between the melee weapon and the bow:
- **Keys:** `KeyboardAction::NextWeapon` and `PreviousWeapon`, by default the mouse wheel down and up, rebindable in
  Controls (`next_weapon` and `previous_weapon`, group Combat). Of two weapons the next and the previous are the same
  one, so either swaps. One turn of the wheel is several steps: a change within 250 ms of the last is ignored, and so
  is one with the right button held, where the wheel scrolls the inspected item's text.
- **Action bar:** a weapon slot with id `ActionBarWeaponSwapId` (1). The bar's prefill adds it when a bow is equipped,
  and it shows the weapon it swaps to.
- **With the bow drawn:** the arms play the equip clips and hold the bow, and **Attack shoots even at melee range**.
  `GameMechanics::soloBowShotMode` is used through `PartyAttackConfig::preferBow`, the only rule difference of a solo
  run. A party member at melee range strikes with the bow's melee fallback; a blaster or wand in the hand would shoot
  first in a party.
- **Archers:** a member with a bow and nothing (or only a broken weapon) in the main hand holds the bow without a
  swap and shoots at any range too.
- **No break the repair would undo** (user, 2026-11-16): a monster's break attack leaves a solo run's held weapon
  (main hand, off hand, bow) whole when the rules' auto-repair would mend it anyway (MAW: the party's best Repair
  skill x mastery reaches the item's repair difficulty, mended on the 5-minute regeneration tick;
  `CombatRules::autoRepairs`). Breaking it would only swap the arms to the other weapon until the tick. Armour and
  carried items still break; a party run breaks everything as before (`GameplayRuleRegressionTests`, "a solo run's
  weapon that auto-repair would mend").
- **The choice:** transient (`ViewModelLink::bowSelected`). A loaded game starts with the melee weapon. It clears when
  no bow is equipped.
- **Verified in game:** combat trace `had_melee_target=true mode=bow`, the arrow killed the target.

## Tier skins (2026-11-14)

The arms hold **Oblivion's templates by default** again, re-skinned per item tier; our own ground models only for the
kinds Oblivion lacks. Record, route, credits and verdicts:
[oblivion_weapon_skins_20261114](../../level_generation/props/items_claude/oblivion_weapon_skins_20261114/README.md)
(private: the meshes are Oblivion's and are never committed).

- **Which model:** `engine/world_items/held_tiers.yml` (schema `openyamm.heldTiers.v1`) lists the held.yml kinds the
  templates draw (`template_kinds`: swords, daggers, greatswords, axes, two-handed axes, maces, hammers, staves, bows,
  shields; since "New templates (2026-11-14)" below also spears, tridents, polearms, poleaxes, clubs, crossbows,
  wands and blasters, with templates of their own). An item without a held.yml row keeps its template. `viewmodel weapons ours` holds our model for every gripped kind,
  `viewmodel weapons oblivion` (the default) goes back.
- **Tiers:** four (approved 2026-11-14): low, mid, high and legendary. The item's base value times its equip stat's
  scale (`Weapon2` 0.5) below 150 is low, 150-599 mid, 600-4,999 high, 5,000 and up legendary; artifacts, relics and
  specials are legendary; an enchanted copy is one tier higher but at most high (legendary stays for the uniques and
  the most valuable bases). All in `held_tiers.yml` (`tiers: 4`, `value_bands`, `value_scale`, `unique_tier`,
  `enchanted_bonus`, `enchanted_max_tier`); the code is `heldSkinTier` in `game/render/HeldWeapons.cpp`, tested in
  `tests/HeldWeaponTests.cpp`. Checked in game with `viewmodel equip`: Iron Longsword low, Dark Elven Longsword mid,
  Templar's Sword high, Elsenrail legendary. Under MAW the halberds are `Weapon2`, so their value counts half like
  every two-handed weapon's (Common Halberd 250 -> 125: low), as intended.
- **Loot rarity (2026-11-14):** an item rolled with a loot rarity (`ItemRulesetFields::lootRarity`, MAW) shows at
  least its rarity's tier (`loot_rarity_tiers`: Common low, Uncommon and Rare mid, Epic high, Ancient, Primordial,
  Legendary and Celestial legendary); the base value can still raise it, never lower it. The user found a Legendary
  Archangel Broadsword (value 29,000 by MAW's own pricing, a broadsword at base price) held as a plain blade. Checked
  with `testparty apply early|mid|endgame` in a MAW solo run: rare and epic gear high (the base value), legendary gear
  legendary.
- **Short swords (2026-11-14):** one-handed swords named cutlass, scimitar, sabre/saber or falchion are held.yml kind
  `shortsword` (`make_held_table.py` `classify`), drawn with `w_shortsword.glb` through `kind_templates`; every other
  one-handed sword keeps the longsword. Checked in game: Cutlass beside an Iron Longsword.
- **Files:** a template `w_<name>.glb` has its skins beside it as `w_<name>_t<tier>.glb`; the view model takes the skin
  when it exists, else the template (`FirstPersonViewModel::skinAttachment`). `Kit::weaponTier` (and `offTier` when dual
  wielding) carry the tier, set by `GameApplication::renderFirstPersonViewModel` from the main hand (or bow).
- **Console:** `viewmodel tier <0-9|auto>` draws every template in one tier (0: the plain template).
- **Made:** every template in tiers 1-4: `w_longsword`, `w_shortsword`, `w_claymore`, `w_dagger`, `w_mace`,
  `w_waraxe`, `w_battleaxe`, `w_warhammer`, `w_staff` (and `w_staff_grip`, the same paint), `w_bow`,
  `s_steelshield` (44 skins; 47 Meshy jobs, 470 credits with the pilot): new PartUV/sparrow layouts on the unchanged
  meshes, Codex masters per tier, Meshy 4K paint downsampled to 2K, a metal and blade pass (weave filter, metal
  albedo, gold's saturation, honed edges, grinding grain), MR with baked occlusion. Node names, transforms, the bow's
  string morph, arrow and clips are the template's. The low bow and low staff are repainted from their mid paint
  (Meshy drew their plain wood as noise).
- **Legendary:** the only glowing tier, and it must read as clearly more magical than high in a thumbnail (tier rule,
  2026-11-14 review; high never glows). Starmetal longsword, voidstone mace, moonsilver short sword, bloodsteel dagger
  and frost-steel battle axe keep their own looks; the bow, claymore, war axe, warhammer, staff and shield (v2, which
  failed the rule as v1) share one: dark star-metal (the staff: star-wood) with a blue-violet sheen, platinum
  fittings, glowing cyan-to-violet rune channels and glowing violet-cyan crystals. Rune inlays carry a glTF
  `emissiveTexture`; the v2 legendaries also `KHR_materials_emissive_strength` 2.5 (the engine accepts up to 16), so
  they glow in daylight and in the dungeon. Where Meshy dropped a channel (the staff) or the masters had none on a part
  that fills the idle frame (the war axe's and warhammer's twisted shafts), post.py draws it procedurally from the
  texels' 3D positions. Long thin templates (bow, claymore, staff) are painted from pieced uploads. Details: the
  project README's "Legendary v2".
- **Bow v2 (2026-11-14 review):** the high bow read blurred and the legendary (bone and gold) plain. The layout was
  never the limit (2.0-3.5 texels per screen pixel at idle, one 4K -> 2K downsample): the v1 masters showed the bow in
  profile, so the limb's belly, the face the camera sees at idle and through the draw, was edge-on for Codex and Meshy
  and came back smeared. The v2 upload stands the bow's pieces side by side with the belly facing the masters (50 px
  per unit face-on, was 25 edge-on): high is now crisp gold filigree on black lacquer with a crimson grip, legendary a
  blue-black star-metal limb with glowing cyan-violet rune channels (`KHR_materials_emissive_strength` 2.5, which the
  engine accepts up to 16), platinum and glowing crystals. Same layout, so low and mid were kept; 20 credits. Details:
  the project README's "Bow v2".
- **Winding:** Oblivion's templates wound every triangle against its normal and the engine culls by winding, so it
  drew their far sides (guards, pommels and grips near black). Fixed 2026-11-14 in the templates themselves
  (`scripts/fix_winding.py`, the skins' index flip; `view_model/` and `reference/oblivion_poc/glb/` share the files as
  hard links; originals backed up in the project's `work/templates_backup_20261114/`).
- **New templates:** a template with skins needs only `w_<name>_t<tier>.glb` beside it; the project README's route and
  scripts take a new template through entries in `codex_masters.py` (`VIEWS`, `WEAPON`, `PARTS`, `LEGENDARY`),
  `post.py` (`BLADED`, `LEGENDARY_LUM`, `RUNES`, `TEMPLATE_CFG`) and `run_ingame.sh`.

## Dual wielding (2026-11-14)

A melee weapon in each hand shows both: the off hand's weapon in the left hand, and every MM attack swung with the two
blades. Record, bake, gates and captures:
[dual_wield_20261114](../../level_generation/props/items_claude/dual_wield_20261114/README.md) (private: the clips
are baked into Oblivion's arms, never committed).

- **Clips:** the engine plays one clip on the whole skeleton (no per-arm layering), so 22 `dual*` clips are baked into
  the arms (`engine/view_model/arms.glb` and the race arms in `reference/oblivion_poc/glb/`) by
  `scripts/bake_dual_clips.py` from the one-handed set, the right arm's clips mirrored onto the left across the body's
  sagittal plane with left and right bones swapped. Each arm keeps its source's place relative to the eye (the attack
  clips twist the spine, the engine's eye only follows Camera01's position), so a waiting arm stays raised in view:
  `dualidle`, the walks and runs, `dualequip`/`dualunequip` (the left hand draws a quarter second after the right),
  `dualblockidle`/`dualblockhit` (a crossed guard), `dualattackright[_chop]` (the right hand cuts and settles back into
  its guard after the blow, the left waits) and `dualattackleft[_chop]` (the mirror), the sideways, lunge and step-back
  power attacks led by one hand, and `dualattackpower`, the cross slash of both blades (the left a tenth of a second
  behind). Text keys come from the source clips (Hit, chain keys; the left cuts' chain keys swapped); the existing 147
  clips are untouched. The arms also get an `OffHandWeapon` node under `Bip01 L Hand`: the `Weapon` node mirrored with
  its flat side turned over, so the off-hand weapon is a rotated, never reflected, copy of a right-hand placement.
- **Kit:** `FirstPersonViewModel::kitForHands` (`game/render/FirstPersonViewModelKit.cpp`) gives `WeaponSet::Dual`
  when the main hand (not wielded two-handed) and the off hand both hold a sword, dagger, axe, mace or club; a shield,
  an empty off hand or anything else keeps the main hand's kit. A two-handed item held in one hand (a MAW Minotaur's
  axes, `Weapon2`) keeps its larger template and makes the kit `heavy`: its swings may play down to 0.7 of Oblivion's
  pace when the recovery is long. Arms without the dual clips or the node show a Dual kit as one-handed.
- **Off hand:** `Kit::offWeapon`, `offHeldModel`/`offHeldIcon` and `offTier`, set by
  `GameApplication::renderFirstPersonViewModel` with the same template-or-ours choice and `heldSkinTier` as the main
  hand. Each blade leaves its own trail (`FirstPersonViewModelFx` keeps one per blade), and the blow's screen direction
  (impact effects) follows whichever blade travelled further since the swing began, as for bare fists.
- **Combo:** the existing round of five (`comboAction`): right, left, right chop, left chop, then the power blow by
  movement, standing the cross slash. The chain keys alternate the leading hand. One MM attack is one blow, released at
  the clip's Hit and fitted to the recovery as before.
- **Console:** `viewmodel equip <main item id|0> <off-hand item id|0>` puts items straight into the active member's
  hands (an assisted command); `viewmodel kit dual <weapon> <off-hand weapon>` forces the kit; `viewmodel path` also
  writes the off-hand blade's tip (`offTip`).
- **Open:** a halberd (a Spear item, which a MAW Minotaur may hold in the off hand) keeps the main hand's kit; the
  crossed block guard and the equip let the blades touch for a frame or two; casting while dual wielding uses the
  one-handed cast clips, whose left hand casts with its weapon in it.

## New templates (2026-11-14)

The kinds Oblivion's templates lack now have **our own templates** (committable art), each in the four tiers: spear,
halberd (also every poleaxe and other polearm), trident, crossbow, wand and blaster; and a wooden **club** in two tiers
(low and mid: every club is valued below the mid band, so `max_tier: 2`; clubs drew the mace template's low tier
before). Record, route, measures and credits (370 Meshy credits):
[view_model_weapons_20261114](../../level_generation/props/items_claude/view_model_weapons_20261114/README.md).

- **Which model:** `held_tiers.yml` `kind_templates` maps a held.yml kind to its own template (`file`, optional
  `max_tier`), drawn instead of the skill group's (`FirstPersonViewModel::kindTemplate`, used by `holdWeapon` and the
  bow branch); the kinds are also in `template_kinds`. Files: `engine/view_model/w_{spear,halberd,trident,crossbow,
  wand,blaster}.glb` (the mid skin) and their `_t1`-`_t4` skins; `w_club.glb` (its mid skin) with `_t1` and `_t2`.
  `viewmodel weapons ours` still holds our ground models through held.yml. Unit test: "kinds with a template of their
  own" in `tests/HeldWeaponTests.cpp` (parsing, and every template and its skins up to its `max_tier` installed).
- **Models:** built in Blender from parts to the Codex design masters drawn from the MM6-MM8 icons (fluted leaf point
  with lugs; crescent axe, hooked beak, studded langets; three barbed prongs on a cross-piece with a set stone; a
  crystal in claws; an Ancients' ray pistol; a crossbow with a steel prod, cord, bolt and stirrup; a knotted club with
  an egg-shaped knob, riveted iron bands, pyramid studs and a rawhide wrap): 1.5-2.9k
  triangles, shafts 2.5 units across at the hands (the fist closes on radius 1.38), PartUV/sparrow layouts at 68-82 %,
  Meshy 4K paint over Codex tier masters, the Oblivion skins' post with regions from the build.
- **How each is held:**
  - Spear, trident, halberd: on the Weapon node, the right fist on the leather wrap, butt 22-30 units behind the
    palm, 1.7 m long. Until 2026-11-14 they played the two-handed set, which holds a pole upright at idle, so its head
    was off-screen at any grip and small in the swings; since then the pole set ("Pole set" below) carries them low
    with the head in view.
  - Wand: the one-handed set, held like a short sword (Oblivion casts with the left hand, so the cast clips leave the
    wand at rest).
  - Club: the one-handed set like the mace, 55 units (79 cm), moved 4.5 units down the hand (butt 15 below the palm,
    as the mace's 16) so the knob's neck shows at the top of the idle frame; the right swing shows the whole knob.
  - Blaster: the one-handed set, built as a pistol with the muzzle along -X; the runtime copy is turned half a turn
    (the muzzle forward), lifted 2.3 units up the fist and its muzzle raised 10° so the fist closes around the grip
    ("Blaster, wand and crossbow after the review" below). Idle holds it low on the right; the block pose reads as
    aiming.
  - Crossbow: built in the left hand's Torch frame at the bow's full draw (+X aim, +Y up, +Z right), on a short
    vertical foregrip in the left fist; held since 2026-11-14 by its own set ("Crossbow set" below): the runtime copies
    are placed rigidly in the right hand's Weapon node (the stock's wrist in the fist). Until then it hung on the left
    fist and played the bow's clips, so drawing the bow read as winding the crossbow.
- **Verdict at full size** (`ingame/` captures, outdoors and in 6d05): the four tiers read as four different weapons on
  every kind (crude iron and ash; satin steel, yew and brass; gilding, ebony and crimson; dark star-metal and glowing
  cyan runes), the legendary runes and stones glow indoors. Weakest: the halberd's low tier (a recolour of the mid
  paint, its masters refused four times). The crossbow's first skins (a plain box stock, masters rendered because the
  image tool refused every crossbow brief) were replaced after the user's review ("Blaster, wand and crossbow after the
  review"). The club's two tiers read as two different clubs
  (weathered ash, rawhide and dark iron; dark oiled walnut, steel bands with brass rivets and dark leather); a faint
  colour step rings its shaft at the upload cut, visible at idle on close look.
- **Legendary poles (redone 2026-11-14):** at idle only a pole's shaft shows, and the first legendary's bone-white
  wood read plain. Spear, halberd and trident now have violet-black ebony shafts with two broad glowing rune channels
  (saturated cyan, violet at the rim; `KHR_materials_emissive_strength` 2.5 like the legendary bow) spiralling up them
  between platinum lips, diamond runes along them and small glowing cabochons round the
  collars, drawn from the 3D position at the map's full resolution (the project's `shaft_runes.py`, "Legendary poles"
  and "Shaft sharpness": one texel covers about one screen pixel at idle, so the softness was the paint, not the map
  size); star-metal heads and fittings from new masters (30 credits). High (black and gold, crimson wrap) does not
  glow; legendary is the only tier that does. A legendary pole's textures take 72.7 MB at runtime (raw RGBA with
  mips).
- **Open:** the blaster and wand have no aim or recoil clip (a blaster shot plays the right swing, which swings the
  pistol sideways).

### Blaster, wand and crossbow after the review (2026-11-14)

Record: the project README's "Blaster", "Wand glow" and "Crossbow tiller and skins". Captures `ingame/review3`.

- **Blaster ("not held properly"):** the fist closed below the gun body: the body's underside sat level with the
  index finger, so the index and middle fingers were inside it and only the little and ring fingers held the grip.
  The runtime copies are lifted 2.3 units up the fist and the muzzle raised 10° about the palm (rigid, kinds.py
  `shift` and `aim`): the whole grip in the fist, the index finger behind the trigger guard, the pommel below the
  little finger, the barrel up the frame toward the crosshair.
- **Gun mount:** `heldWeaponMatrix` now puts a ground blaster's muzzle along +X (out of the knuckles); with −X it
  pointed at the eye. A blaster bolt still leaves the party's ranged source (the party's position at
  `PartyAttackProjectileSourceHeight`, as arrows do), not the muzzle; only spells start at the hand on screen.
- **Wand:** the crystal glows on every tier, faint on low to clear on legendary, in its own saturated hue, brighter
  toward the tip and on the lighter facets (post.py `WAND_GLOW`).
- **Crossbow ("doesn't look that different between the versions"):** the ribbing was the colour map (Meshy's paint
  over rendered masters whose wood was a regular wave texture), not the mesh or the normal map. The stock is now a
  shaped tiller (cheek piece, narrow wrist, tapered butt deepening below a straight comb, lock plates with set stones;
  2,260 triangles, the wrist and foregrip unchanged so the crossbow set's clips stand), laid out again, and its four
  skins are painted procedurally per texel (`bake_crossbow.py`; Codex refused two further wordings, Meshy not used):
  weathered grey-brown wood and rusty iron; polished walnut and steel; black ebony with framed gold scrollwork, steel,
  gold, crimson and rubies (no glow); blackened violet wood, star-metal, platinum, glowing cyan-violet rune channels
  along the stock and the prod and glowing stones.

## Crossbow set (2026-11-14)

A crossbow is held with both hands and has its own clips: carried at the right hip, raised to the cheek, loosed with a
short sharp recoil and spanned again. Record, bake, gates and captures:
[crossbow_set_20261114](../../level_generation/props/items_claude/crossbow_set_20261114/README.md) (private: the clips
are baked into Oblivion's arms, never committed; the crossbow template is ours).

- **Kit:** `FirstPersonViewModel::kitForBow(heldKind)` (`FirstPersonViewModelKit.cpp`): the drawn bow whose held.yml
  kind is `crossbow` (every crossbow icon) gets `WeaponSet::Crossbow` and `w_crossbow.glb`; any other bow, or an icon
  without a held.yml row, keeps the bow set. `GameApplication::renderFirstPersonViewModel` asks
  `FirstPersonViewModel::heldKind(icon)` for the bow slot's item. Unit test: "crossbows: the drawn bow's held kind picks
  the crossbow set" in `tests/HeldWeaponTests.cpp` (also checks the engine's held.yml crossbow rows).
- **Hold:** the right hand holds it: the template hangs on the Weapon node (the stock's wrist in the fist, the hand
  cradling it from below), placed there rigidly by the weapons project's `kinds.py` `mount`, which the clip bake reads
  too. The left fist closes on the foregrip under the fore-end, where the crossbow was built in the Torch frame; it
  leaves it to span the cord and to cast. Our ground crossbows (`viewmodel weapons ours`), gripped by held.yml's
  Crossbow mount in the Torch frame, ride on the Weapon node at the Torch frame's place in `crossbowidle`
  (`m_crossbowGrip`, measured once when the arms load), so they follow the right hand too.
- **Clips** (17, baked into the arms of every race by `scripts/bake_crossbow_clips.py`, the arms solved onto the
  crossbow's keyframed place relative to the eye): `crossbowidle` (3 s, breathing), the eight walks and runs (the bow's
  durations and motion), `crossbowequip` (Attach 0.1 s) and `crossbowunequip`, `crossbowattack` (1.55 s: raise 0.25 s,
  Release 0.4 s, a 0.06 s kick, then the span; a:R at 1.433 s), `crossbowblockidle` and `crossbowblockhit` (raised
  across the face) and `crossbowcastself` / `crossbowcasttarget` (the left hand casts as in Oblivion's one-handed casts,
  the right holds the crossbow low; `castClip` picks them, `castHands` casts from the left palm).
- **Shot timing:** the Crossbow set shoots like the Bow set (`shoots()` in `FirstPersonViewModel.cpp`: the attack clip,
  `setClip("attack")`, looses the missile at its Release; no weapon trail; the Shot action, Volley and the queued shot
  take it). A queued shot waits for the running shot's chain key when it has one, else its Release: the crossbow's a:R
  sits at 1.433 s, the bow's Release, so with the swing rate fitted to the recovery by that same span both keep one
  cadence at any recovery (at most 3.5 times Oblivion's pace, a shot every 0.41 s). The bolt leaves 0.4 s into the clip
  (0.11 s at the fastest), the span finishes before the next shot may start.
- **Console:** `viewmodel kit crossbow w_crossbow.glb 0` forces the set; `viewmodel equip <main> <off> <bow>` also
  fills the bow slot (`viewmodel equip 0 0 63`: empty hands and the Hunting Crossbow, so the member draws it);
  `viewmodel held <crossbow icon>` holds our ground model in the crossbow set.
- **Arms without the clips** (a `[debug] view_model_path` arms file without them) show a Crossbow kit with the bare
  hands' clips; the engine's arms and every race's carry them.
- **Open:** the span is a gesture (the cord and bolt are static on the model: a drawn cord and a nocked bolt at all
  times); the spanning reads at the bottom right, partly under the right forearm, because the eye cannot look down at a
  crossbow tipped toward the floor; the right fingers sink a little into the stock's thick wrist (3.4 by 3.9 units
  against the fist's 2.5).

## Pole set (2026-11-14)

Spears, tridents, halberds and poleaxes are held with both hands with their own clips: low at the right hip with the
head up and right of the crosshair, jabbed along the view, swept across it and chopped down through it. Record, bake,
gates and captures: [pole_set_20261114](../../level_generation/props/items_claude/pole_set_20261114/README.md)
(private: the clips are baked into Oblivion's arms; the pole templates are ours). Before, poles played the two-handed
(claymore) clips, which hold a pole upright: the head above the frame at idle and small in the swings, so the tier
skins' heads were never seen.

- **Kit:** `FirstPersonViewModel::kitForHeldKind(kit, mainHeldKind)` (`FirstPersonViewModelKit.cpp`) turns
  `kitForHands`' kit into `WeaponSet::Pole` when the main-hand item's held.yml kind is `spear`, `trident`, `polearm`
  or `poleaxe` (`poleKind`): both hands on the shaft, no shield (also a Spear Master's spear with a shield, as the
  two-handed kit dropped it), our model, icon and tier kept; `held_tiers.yml` `kind_templates` draws the kind's
  template (`w_spear`, `w_trident`, `w_halberd`; `w_spear.glb` is the kit's fallback). Staves (`staff`) keep the
  two-handed set and the staff grip, an icon without a held.yml row keeps the skill group's kit, and a Dual kit (a MAW
  Minotaur's poleaxe with an axe) stays dual. `GameApplication::renderFirstPersonViewModel` asks
  `FirstPersonViewModel::heldKind(icon)` for the main hand's item; `viewmodel held <icon>` does the same. Unit test:
  "pole weapons: spears, tridents, polearms and poleaxes get the pole set" in `tests/HeldWeaponTests.cpp` (also every
  pole and staff row of the engine's held.yml).
- **Hold:** the right fist on the Weapon node (the templates are built there: palm at the origin, head +Y), behind and
  low, below the frame at idle; the left fist 22 units up the shaft, at the bottom right. The shaft points forward, up
  and a little in, so the head is about 25 degrees off the view ray: held along the view (12 degrees) the halberd's blade
  was seen edge on. The head is turned so its flat half faces the eye (the halberd's axe blade up and right); the
  sweeps and chops turn its edge forward, the shaft turning in the left fist.
- **Clips** (24, baked into every race's arms by `scripts/bake_pole_clips.py` after the dual and crossbow bakes:
  `crossbow_set_20261114/scripts/rebake_arms.sh` runs all three from the pristine arms): `poleidle` (3 s, breathing),
  the eight walks and runs (the two-handed durations and keys, the pole carried by their motion at 60 %), `poleequip`
  (Attach 0.1 s, swung up from below the view) and `poleunequip`; the combo `poleattackright` (a jab: the point onto
  the crosshair at the Hit), `poleattackleft` (a higher jab), `poleattackright_chop` (a sweep right to left, the edge
  leading), `poleattackleft_chop` (an overhead chop, the halberd's axe blade leading); the power attacks
  `poleattackpower` and `poleattackforwardpower` (a lunge thrust), `poleattackbackpower` (a big chop),
  `poleattackleftpower` and `poleattackrightpower` (big sweeps); `poleblockidle` and `poleblockhit` (the shaft raised
  across the face); `polecastself` and `polecasttarget` (the left hand casts as in Oblivion's one-handed casts, the
  right holds the pole lower; `castClip` picks them). The attacks are baked at 60 frames a second, the rest at 30.
- **Timing:** every attack carries the Hit and chain keys (a:L, a:R) of the two-handed clip of the same name, so the
  swing is fitted to the recovery by the same span and the blow lands at the Hit as before: the same cadence, the Hit
  at the contact frame (the point on the crosshair, or the head crossing it). The combo plays jab, jab, sweep, chop and
  a power attack by the movement (the lunge standing or moving forward, the big chop moving back, the big sweeps moving
  sideways); Cleave and Whirlwind play the big sweeps and Charge the forward lunge. Checked live: ten presses gave two
  full rounds, each blow within a frame of its Hit.
- **Console:** `viewmodel kit pole w_halberd.glb 0` forces the set; `viewmodel equip 42 0` (Steel Spear), `1643`
  (Titanic Trident), `1630` (Light Poleaxe) or `1638` (Common Halberd) puts a real item in the hand.
- **Arms without the clips** (a `[debug] view_model_path` arms file without them) play the two-handed clips for a Pole
  kit (`setClip`'s fallback), as before the set existed.
- **Open:** the spear's narrow head is the smallest at idle; the chop's Hit shows the halberd's blade edge on; the
  right hand is never on screen at idle; one set for every pole kind (a spear also chops, a halberd also jabs).

## Quality bar for shippable held weapons

A held weapon fills a third of the screen, so the ground models need a **held pass**, not a remake:

1. **Texture density**: at least 2048 px along a blade or head at 1080p (one-handed weapons: today's 1024² is
   enough for the grip and borderline for the blade; polearms: the head re-baked to its own 1024² or 2048×1024
   atlas, the shaft can stay at today's density). Normal maps on blades and heads.
2. **Alpha-cut detail** (halberd and trident heads, axe beards) becomes real geometry or gets anti-aliased cut
   edges (alpha-to-coverage); stair-stepped cutouts are the most visible defect up close.
3. **Triangles**: 2–5 k for one-handed weapons, up to 8 k for polearms; the held view is one model, so this is cheap.
4. **Materials** as the ground models (metal/roughness from the ORM map), lit like the arms (the new scene-matched
   view model lighting).
5. **Checks**: grip sheet (idle and Hit, every kind), no back faces visible, blade tip correct, a capture in the
   game at 1080p with the HUD off.

Wands, blasters, throwing weapons and crossbows reuse their ground models the same way; crossbows have their own set
since 2026-11-14 (Oblivion's base game has none).

## Work order

1. **Now, prototype (no art):** kind → set and attack-path table in the view model, staves on twohand, spears
   on the onehand thrust, the combo variety above. *(Partly in progress in the engine work.)*
2. **Held table and loader:** run `align_held.py` over every weapon icon, write the override table, load the held
   model by the equipped item's icon instead of Oblivion's stand-ins, and the contact-sheet check. About 1–2 days;
   no paid generation.
3. **Held pass on the art**: polearm heads and blades re-baked at higher density, alpha cut-outs to geometry, by
   family (the items pipeline in `level_generation/props/items_claude/`). Roughly the cost of a ground-items family
   pass per weapon family; mostly local work, small Meshy retexture spend only where a paint must be redone.
4. **Two own clips**: two-handed thrust and sweep for spears and halberds (Blender, on the arms rig), then mirrored
   off-hand swings for dual wielding. *(Done 2026-11-14: "Pole set" and "Dual wielding".)*
5. **Own arms** replace Oblivion's (separate plan in README.md), after which nothing Oblivion-derived remains.

## Open decisions for the user

- Spears: always the thrust, or thrust and sweep alternating? And two-handed below Master with the off hand
  hanging (interim) until the own clip exists — acceptable?
- Power and perk clips: reserve them for special skills on the action bar (recommended), or mix them into the
  normal chain at Master/Grandmaster?
- Held art: go straight to the held pass on our item models (recommended), or keep Oblivion's stand-ins for the
  prototype longer?
- Override table: a separate `held.yml`, or a `held` block on each `items.yml` entry?
