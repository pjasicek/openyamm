# Player stand-in bodies: plan (2026-11-20)

**Set aside on 2026-11-21 (the user's decision). Do not start it.** Players are drawn with installed MM6–MM9
models chosen by race, sex and kind of class (`game/coop/CoopBodies.cpp`), in one gold colour that no monster tier
has, with a glow by the tier of their gear. The body does not change with the worn armour and holds the model's own
weapon. What is built and what is open: the architecture's "Another player's body" and
`devdocs/plans/MULTIPLAYER_OPEN_ITEMS.md`. The rest of this file is the plan as it was written, kept for its
measurements.

This folder holds the plan for our own 3D bodies of co-op players. Nothing here has been generated, rigged or
installed. Every body below has the status `planned`. The machine-readable parts are `roster_manifest.yml`, `weapons_manifest.yml` and
`armour_looks_manifest.yml` beside this file.

Numbers marked "measured" were read from the files in this checkout on 2026-11-20. Numbers marked "estimate" are my
judgement and must be checked when the work starts.

## 1. What exists today

- Another player is drawn as an existing monster model. `game/coop/CoopBodies.cpp` (`coopBodyDescriptor`) picks it:
  the race's monster first, then a woman's model for a human woman, then a model by class, then any fighter.
- The body shows no worn gear. The weapon in its hand is the monster's own.
- `WorldFxSystem::syncPlayerBodies` plays standing, a gait, the melee attack, the ranged attack, the cast and the death
  clip of that monster's binding.
- The open items list calls gear on bodies CO-61, "not planned" (`devdocs/plans/MULTIPLAYER_OPEN_ITEMS.md`).

## 2. Recommendation in short

1. **Rig family: the humanoid set layout (`B_*` bones) of the MM6–MM8 humanoid playbook**, not the MM9 skeletons.
   One bone layout and one clip list for every player body. MM9's own clips are kept as a second source for the
   social clips they are good at (taunt, bow, applause, cower), retargeted onto the same rig.
2. **Six body builds, as the original games already have them.** The paperdoll table `doll_types.txt` has six doll
   types: male, female, minotaur, troll, dwarf and dragon. Every race in the game is drawn on one of them. We make
   skinned bodies for male, female, dwarf, minotaur and troll. The dragon keeps its monster model.
3. **Races are heads and skin colours on those bodies.** An elf, a goblin, a half-orc, a vampire, a dark elf or a
   lich is the male or female body with that race's head (a small separate model on the head bone) and that race's
   skin colour. This turns 31 race, sex and doll combinations into 5 bodies and 11 heads.
4. **Armour: four looks by armour type, with the gear tier shown as trim.** The look (cloth, leather, chain, plate)
   comes from the worn body armour's skill column. The tier (low, mid, high, legendary) recolours the trim and metal,
   and the legendary tier glows. Both of the owner's ideas are used: type picks the look, tier picks the trim.
5. **Weapons: reuse the first-person weapon rules unchanged.** The game already decides which model and which tier
   skin the first-person arms hold (`game/render/HeldWeapons.h`, `engine/world_items/held.yml`,
   `engine/world_items/held_tiers.yml`). The body gets mount nodes with the same names and axes as the arms, so the
   same files and the same placement code serve both views.
6. **Per-player tint: one "livery" region on every look**, recoloured per player from a palette of eight colours.

## 3. Why this rig family (measured)

I parsed every creature GLB under `assets_source/worlds/<world>/models/` (the scripts and their output are in the
scratch folder named at the end of this file).

| Fact | MM9 bodies | MM6–MM8 humanoid bodies |
|---|---|---|
| Skeleton | Original MM9 skeletons, 3ds Max Biped names (`Bip01 ...`) | Humanoid set layout (`B_Pelvis`, `B_L_Thigh` ...) |
| Bodies on it | 72 | 101 (24 in MM6, 45 in MM7, 32 in MM8) |
| Different joint name sets among them | 47 | 73 (the extras are cloak, skirt and weapon bones) |
| Largest group with identical joints | 16 (the male townsfolk, 75 joints) | 15 (`mm6_bar1`, 13 MM7 bodies, `mm8_m444`; 57 joints) |
| Finger bones | MM9 had one finger chain; 15 per hand are grafted on (`MM9_HUMANOID_BRIEF.md`) | 30 on 91 of the 101 bodies |
| Where the clips come from | Each model's own MM9 clips | One library: the humanoid set (1,157 clips) and Mixamo |
| Clips per body | 9 to 49, median 16 | 5 to 13, median 10 |
| LOD0 triangles, median | 9,782 | 7,939 |
| Source GLB size, median | 24.3 MB | 9.8 MB |

What decides it is the clips, not the bones:

- **A player body must hold every weapon kind.** An MM9 body's combat clips are made for what that model carries:
  the guard's attacks are halberd attacks (its README), and the clan soldier's skeleton has one sword bone and one
  shield bone. Of the 72 MM9 bodies, 46 have one melee attack clip, 17 have two and 7 have three; 40 have no ranged
  attack; 4 have a clip named `Cast`; 3 have a block. The clips are named by role (`AttackMelee`, `AttackMelee2`),
  not by weapon, and I found no body with separate sets for different weapons, so none can show a sword today and a
  bow tomorrow. (Read from clip and bone names; I did not watch the clips.) MM9 never drew the party, so it has no
  player set.
- **The animation library has a set per weapon kind.** Counted from `anim_library/index.json` (clips rated `core`):
  the humanoid set has standing, walking, run, attack, hit and death clips for each of these sets (1Hand is
  attacks only): Unarmed (11 attacks, 28 casts), Armed (12 attacks, 25 casts), Armed-Shield (3 attacks), 1Hand (41
  attacks: sword, mace, dagger, spear), 2Hand Sword (16), 2Hand Axe (12), 2Hand Spear (16), 2Hand Staff (11 attacks,
  10 casts), 2Hand Bow (2 shots) and 2Hand Crossbow (2 shots). Mixamo adds 548 more `core` clips.
- **The route is proven and has numeric gates.** The source-frame rig of
  [the humanoid playbook](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md) got "very good results" (barbarian) and "very good"
  (spearman) from the user after one review round each. Its gates G1–G7 measure joints, weights, grip, contacts, feet
  and jerk before anyone looks at a picture.
- **The MM9 route costs more per body.** The guard's source skeleton was mirrored (its `R Hand` was the anatomical
  left) and the MM9 brief asks for that check on every body; MM9 hands need grafted fingers; and the guard's fist
  round a shaft took two passes (`../mm9_guard_claude/README.md`).
- **What MM9 does better is kept.** MM9 clips are rich in social motion: of 72 bodies, 37 have `Cower`, 32 `Talk`, 31
  `Taunt`, 27 `Backpedal`, and the townsfolk have `Bow`, `Applause`, `Sit`, `Pray` and `Bless`. MM9's bones, the
  humanoid set's bones and the first-person arms all use the same Biped naming (pelvis, three spine bones, neck,
  head, clavicle, upper arm, forearm, hand, thigh, calf, foot, toe), so an MM9 clip can be copied onto the player rig
  by the playbook's world-rotation retarget. **This has not been done in this repository yet**; the first slice tests
  it on one clip before the plan relies on it.

The owner leaned towards the MM9 rigs because their animations are rich. The recommendation keeps that richness where
MM9 has it (social clips) and uses the library where MM9 has nothing (weapon sets).

## 4. Roster

### 4.1 Skinned bodies (rig, clips, four armour looks each)

| Id | Doll type | Used by | Notes |
|---|---|---|---|
| `pb_male` | 0 | Men of: human, elf, dark elf, vampire, goblin, half-orc, lich, zombie | First slice |
| `pb_female` | 1 | Women of the same races | Second |
| `pb_dwarf_male` | 4 | Dwarf men, lich and zombie dwarves | Short, broad; own proportions |
| `pb_minotaur` | 2 | Minotaur (men only in the data), lich and zombie minotaur | No helm, no boots (`doll_types.txt`) |
| `pb_troll` | 3 | Troll (men only in the data), lich and zombie troll | Every slot |
| `pb_dwarf_female` | 4 | Dwarf women | **Optional.** Until decided: `pb_dwarf_male` with the dwarf woman's head |

### 4.2 Heads (static models on the head bone, one 1K texture set each)

| Id | Used by | How it is made |
|---|---|---|
| `ph_human_male`, `ph_human_female` | Human, vampire (pale skin colour), zombie (zombie skin colour) | Cut from the body's own generated mesh |
| `ph_elf_male`, `ph_elf_female` | Elf, dark elf (dark skin and white hair by colour) | The human head with pointed ears (estimate: an edit, else a head-only model) |
| `ph_goblin_male`, `ph_goblin_female` | MM7 goblins | Head-only model |
| `ph_halforc_male`, `ph_halforc_female` | MM9 half-orcs (same race id 8 as goblins; told apart by the portrait row's world) | Head-only model |
| `ph_lich` | Lich, both sexes, on the male, female and dwarf bodies | Head-only model (a skull) |
| `ph_dwarf_male`, `ph_dwarf_female` | Dwarves | Male: cut from the body's mesh. Female: head-only model |

The minotaur and troll heads are part of their bodies. Their lich and zombie forms are skin colours only.

### 4.3 Races that keep a monster model

| Race | Model kept | Why |
|---|---|---|
| Dragon (race 5, and its lich and ghost forms) | `Wimpy Dragon A`, then `Dragon A`, `ADragon A`, `DragonLand A`, as today | Doll type 5 equips nothing, so there is no gear to show. The body is not humanoid. The first-person view already has its own dragon forelegs. Permanent. |
| Minotaur (race 3) | `Minotaur A`, `BMinotaur A`, `AMinotaur A`, `Minotaur Pesant A`, as today | Only until `pb_minotaur` is built (last wave). |
| Troll (race 4) | `Troll A`, `ATroll A`, `Troll Pesant A`, as today | Only until `pb_troll` is built (last wave). |
| Every race | Today's table in `CoopBodies.cpp` | Stays as the fallback whenever a planned body or head is not installed. |

### 4.4 Every combination the data allows

`character_data.txt` has 97 portrait rows. Their race, sex and doll type give 29 combinations; goblins and half-orcs
share race id 8, so counting them apart gives 31. `roster_manifest.yml` lists all of them under `appearances` with the body,
head and skin colour each one uses. In short:

- Human, vampire, dark elf, elf, goblin, half-orc: man and woman each (12 combinations).
- Dwarf: man and woman (2). Minotaur: man (1). Troll: man (1). Dragon (1).
- Lich: man, woman, dwarf man, dwarf woman, minotaur, troll, dragon (7).
- Zombie (a condition's portrait): man, woman, dwarf man, dwarf woman, minotaur, troll, dragon ghost (7).
- The three rows without a race (portraits 29, 30 and the wetsuit row 31) are not player bodies and are not counted.

Which worlds offer what (from `character_selection.yml`): Jadame offers races 0, 1, 2, 3, 4, 5, 7, 8, 9; Antagarich
0, 3, 7, 8, 9; Enroth 0, 3, 7, 9; Chedian (MM9) 0, 1, 2, 3, 4, 5, 7, 8, 9. Liches come from promotion and zombies from
a condition. The class does not change the body: the worn gear already shows what a character is.

## 5. The shared rig

- **Bones:** the 56 body joints of `mm6_bar1` (measured: pelvis, 3 spine, neck, head, 2 × clavicle, upper arm,
  forearm, hand, 2 × thigh, calf, foot, toe, 30 finger bones, 2 forearm twist, 2 upper-arm twist). Same names and
  hierarchy on every player body. Each body's joints are fitted to its own mesh (gate G3), so a dwarf and a troll
  share the layout, not the proportions.
- **Clips are baked per body** by the playbook's `rebuild.sh` from one clip list, as every MM6–MM8 humanoid does. The
  engine reads clips from each model's own file, so nothing new is needed to play them.
- **Mount nodes** (plain nodes under the bones, with the first-person arms' names and axes, so
  `heldWeaponMatrix` and the `w_*.glb` templates work unchanged; the templates are in Oblivion units, about 1.43 cm,
  so each mount node carries that scale):

| Node | Parent bone | Holds |
|---|---|---|
| `Weapon` | `B_R_Hand` | Main-hand weapon; a crossbow's stock. Palm at the origin, head along +Y, edge along +X |
| `OffHandWeapon` | `B_L_Hand` | Second weapon when dual wielding |
| `Torch` | `B_L_Hand` | Bow in use. Limbs along Y, riser at the origin |
| `Shield` | `B_L_Forearm` | Shield. Face toward −Y, top along −Z (the arms use `Bip01 L ForearmTwist`) |
| `BackWeapon` | `B_Spine2` | Stowed bow while a melee weapon is in the hand |
| `Quiver` | `B_Spine2` | Reserved (not used in the first release) |
| `Helm` | `B_Head` | The worn helm's ground item model |
| `B_Head` itself | — | The race head |

- **Sockets for effects** (`animation.sockets` in the binding): `palm_left`, `palm_right` (spell charge and release),
  `arrow` (arrow release on the bow hand), `weapon_tip` (a node plus an offset on `Weapon`), `head_top` (name label).

## 6. The shared clip set

Clip names are `<Set><Action>`. The set names follow the first-person `WeaponSet` enum so the game sends one value.
"Library" means the git-ignored `anim_library/` (see its README); clips are chosen and previewed at gate G1, and the
committed GLBs carry only our role names. "MM9" means retargeted from an MM9 model's clips. "Authored" means built with
`mm6_natm_claude/scripts/author_attack.py` or `author_carry.py` because the playbook found no library clip that works.

| Set | Used when | Standing, Walking, Running | Attack clips | Source |
|---|---|---|---|---|
| `Unarmed` | Nothing in the hands | 3 | `UnarmedAttack`, `UnarmedAttack2` | Library: Unarmed set; upright idle and walks from Mixamo |
| `Onehand` | One-handed weapon, free off hand; wand; blaster | 3 | `OnehandAttack`, `OnehandAttack2` | Library: 1Hand attacks; upright carry authored (the set's own one-handed idle is a low guard) |
| `Shield` | One-handed weapon and a shield | 3 | `ShieldAttack` | Library: Armed-Shield set and Mixamo sword-and-shield |
| `Dual` | A weapon in each hand | 3 | `DualAttack`, `DualAttack2` | To be made: the one-handed attacks mirrored onto the left arm (as the first-person dual set was made) |
| `Twohand` | Two-handed sword, axe, hammer | 3 | `TwohandAttack`, `TwohandAttack2` | Library: 2Hand Sword and 2Hand Axe sets |
| `Pole` | Spear, trident, halberd, poleaxe in two hands | 3 | `PoleAttack`, `PoleAttack2` | Library: 2Hand Spear locomotion; the thrust authored (underhand, per the playbook's spear finding) |
| `Staff` | Staff | 3 | `StaffAttack`, `StaffCast` | Library: 2Hand Staff set (11 attacks, 10 casts) |
| `Bow` | Bow in the hands | 3 | `BowAttack` (draw and release) | Library: 2Hand Bow set, Mixamo bow clips |
| `Crossbow` | Crossbow in the hands | 3 | `CrossbowAttack` | Library: 2Hand Crossbow set |

Shared by every set: `Cast` (left open hand, release forward), `Cast2` (raise, for spells on oneself), `Hit`, `Death`,
`Dead`, `Fidget`. Source: library (Unarmed and Armed casts; hits and deaths of the Unarmed set).

That is 27 locomotion clips, 15 attack and staff-cast clips and 6 shared clips: **48 clips**. Estimate from measured data (0.034 to
0.076 MB per clip-second on 56-joint bodies; about 70 clip-seconds): 2.4 to 5.3 MB of animation per body file.

A later optional wave adds emotes from MM9 (`Taunt`, `Bow`, `Applause`, `Cower`, `Sit`): the engine has no player
emote command yet, so they are not in the first 48.

The engine already plays an attack on the upper body over a gait (`upper_body_root` in the binding), so no "attack
while running" clips are needed.

## 7. Weapons in the hands

Full table: `weapons_manifest.yml`. The rule is the one the first-person arms use; nothing is invented.

- **Kind:** an item's `Equip Stat` and `Skill Group` columns in `items.txt` give the base (for example `Weapon` +
  `Sword`). Its inventory icon's row in `engine/world_items/held.yml` refines it (`sword`, `shortsword`, `greatsword`,
  `axe`, `greataxe`, `poleaxe`, `mace`, `hammer`, `club`, `dagger`, `staff`, `spear`, `trident`, `polearm`, `bow`,
  `crossbow`, `wand`, `blaster`, `shield`). Measured: 334 rows; every weapon, bow and shield icon of the engine item
  table has one, except one shield.
- **Model:** the template in `assets_dev/engine/view_model/` (`w_longsword.glb`, `w_claymore.glb`, `w_waraxe.glb`,
  `w_battleaxe.glb`, `w_mace.glb`, `w_warhammer.glb`, `w_club.glb`, `w_dagger.glb`, `w_shortsword.glb`,
  `w_staff.glb`, `w_spear.glb`, `w_trident.glb`, `w_halberd.glb`, `w_bow.glb`, `w_crossbow.glb`, `w_wand.glb`,
  `w_blaster.glb`, `s_steelshield.glb`). The same console switch as in first person can draw the item's own ground
  model instead (941 ground models exist; `engine/world_items/items.yml`).
- **Tier skin:** `w_<name>_t1.glb` to `_t4.glb`, chosen by `heldSkinTier` from `held_tiers.yml` (base value bands 150,
  600 and 5,000; two-handed values count half; artifacts and relics are tier 4; an enchantment raises one tier up to
  3; a MAW loot rarity sets a floor). The owner approved these tiers on 2026-11-14.
- **Hands:** follow `ItemRules::wield` (a Minotaur's halberd is one-handed under MAW), never the table type alone.
- **Bow:** in the hands (`Torch`) while the player has the bow selected or has no melee weapon; otherwise stowed on
  `BackWeapon`.
- **No model yet:** MM9's throwing weapons (4 items, `Missile` + `Throwing`); MM9's 93 weapons, bows and shields have
  no `held.yml` rows, so they fall back to their skill group's template, and MM9 spears and halberds (14 items) would
  be drawn as a staff until they get rows. These gaps exist in first person today as well.

## 8. Armour looks

Full table: `armour_looks_manifest.yml`.

**The look comes from the armour type.** The body armour slot's item has `Skill Group` `Leather`, `Chain` or `Plate`
(measured: 19, 20 and 15 items in the engine table; 13, 12 and 10 in MM9's). No body armour means `cloth`.

| Look | When | What is painted |
|---|---|---|
| `cloth` | No body armour | Tunic, trousers, boots, belt; bare hands |
| `leather` | Body armour with skill `Leather` | Leather jerkin, bracers, leather boots |
| `chain` | Skill `Chain` | Mail shirt over a gambeson, surcoat, leather gloves |
| `plate` | Skill `Plate` | Breastplate, plated arms and legs, gauntlets, tabard |

**The tier is the trim.** Four tiers, the same as the weapon skins: 1 low (rough cloth, dull iron), 2 mid (clean
steel, plain dye), 3 high (polished, gilded trim), 4 legendary (dark exotic metal, glowing inlay). The tier comes from
the same body armour item through the same rule as weapons, with value bands per look because plate costs more than
leather (my proposal from the listed item values: leather 300 and 800, chain 500 and 1,300, plate 1,300 and 2,500;
artifacts, relics and specials are tier 4).

**Why type and not tier for the look:**

- The type is a column in the item table; the look can never disagree with the inventory.
- It is what other players read first: a robed caster, a leather-clad archer, a knight in plate.
- A tier is a scale, and colour and glow show a scale well. Four tier looks alone would make a mage in a legendary
  robe look like a knight.
- Body and weapon then use one tier rule, already approved for the weapons.

**How a look is built:** one mesh per body, four texture sets painted on it, selected by material variant (the
mechanism creature tiers use). The MM9 guard is the precedent: quilted leather, chain and plate are three paints on
one mesh, and the user called it "good". The base mesh is a neutral, fitted garment (an arming doublet with boots,
gloves and a belt) so that it reads as cloth when painted as cloth and as armour when painted as metal.

**What else is shown:** the helm (the item's own ground model on the `Helm` node; 40 engine helm models exist) and
the shield. **Not shown:** cloak (needs simulated cloth), boots, gauntlets and belt (part of the look's paint), rings
and amulets (too small).

## 9. Colours: skin, livery, trim, hair

Every look has one region mask with the same four channels, and the head uses the same channels:

| Channel | Region | Chosen by |
|---|---|---|
| R | Skin | Race (and lich or zombie form) |
| G | Livery: the main cloth piece of the look (tunic, surcoat, tabard) | The player's colour |
| B | Trim and metal | Gear tier |
| A | Hair (on heads); unused on bodies | Race default; later the portrait |

The **per-player tint** is the livery channel. Eight colours: crimson, royal blue, forest green, gold, purple, teal,
orange, ivory. By default a player gets the colour of their slot in the session (four players at most today:
`MaxGuests = 3`). The same colour can mark the name above the head.

The creature renderer stores ramps per material. Three independent choices (skin, livery, trim) on one body need
ramps per drawn instance; that is the main renderer change (section 10).

## 10. What the game sends and what the engine needs

**Per player, sent when it changes** (about 16 bytes; race, sex and portrait are already sent):

| Field | Size | Meaning |
|---|---|---|
| `weaponSet` | 1 byte | Which clip set and whether the bow is in the hands |
| `mainItem`, `mainTier` | 2 + 1 bytes | Main-hand item id and its skin tier (computed by the owner's game) |
| `offItem`, `offTier` | 2 + 1 bytes | Shield or second weapon |
| `bowItem`, `bowTier` | 2 + 1 bytes | Bow slot |
| `armourLook`, `armourTier` | 1 + 1 bytes | Look 0–3 and tier 1–4 |
| `helmItem` | 2 bytes | Worn helm, 0 for none |
| `colour` | 1 byte | Livery colour 0–7 |
| `form` | 1 byte | Normal, lich or zombie |

The sender computes the set and tiers because they depend on its character's skills and on each item copy's
enchantment and rarity, which the other games do not hold.

**Engine changes, one line each:**

1. `CoopProtocol` / `CoopSession`: add the appearance record above to a player's state.
2. `CoopBodies.cpp`: choose body, head and skin from a table (`engine/models/player_bodies.yml`) by race, sex, doll
   type and portrait world; keep today's monster table as the fallback.
3. Model manifest: load `engine/models/player_bodies.yml` in every world (the `actors.yml` schema plus a clip table
   per weapon set).
4. `WorldFxSystem::syncPlayerBodies`: take standing, gait and attack clips from the current weapon set.
5. Held weapons: build the body's attachments with the existing `HeldWeapons` functions; move the kit choice
   (`kitForHands`, `kitForBow`, `kitForHeldKind`) where both views can call it.
6. Head and helm: two more rigid attachments; a small `worn.yml` placement table for helm models (like `held.yml`).
7. `ModelInstanceSystem`: region ramps per instance (`setRegionRamps`), also applied to that instance's attachments.
8. Legendary glow: the existing `setEmissionMultiplier` per instance.
9. Stowed bow: attach the bow to `BackWeapon` when it is equipped but not in the hands.
10. Cooking and packaging: add the player body files to the model cook and to the engine package.
11. Tests: a unit test for "appearance record → body, look, tier, attachments" and a two-player headless scenario.
12. Optional: upload only the textures of the material variants in use (today all four looks of a body upload at
    once; the MM9 guard measured +40.8 MB of GPU memory for three texture sets).

**Already supported, no change:** attachments per drawn instance with a placement matrix (`ModelAttachment`), the
material variant per instance, upper-body attack over a gait, shadows, outlines, picking and the name label.

## 11. Recipe per body

Each step names the section it follows. `<P>` is `level_generation/creatures/player_bodies/<id>`.

| # | Step | Follows |
|---|---|---|
| 0 | Claim the workspace with a credit budget (`tools/creature_workspace.py claim`). | Humanoid playbook, "Quick start" 2 |
| 1 | **Clip list (once, for `pb_male`).** Choose the 48 clips with `build_anim_index.py find`, preview each on the set's own mannequin with a stand-in of our weapon's real length, measure tip height and direction. Later bodies reuse the list. | Humanoid playbook, gate G1 and "Weapon attacks and held props" |
| 2 | **HD masters.** Five views of the body in the base garment, A-pose, from the native paperdoll body and worn armour art; then front, left, back and right of each other look on the same body and pose. | [HD masters](../CLAUDE_HD_MASTER_REFERENCES.md): "Deliverables", "Inputs to Codex", "Gate before Meshy" |
| 3 | **Mesh.** Meshy Smart Topology at 15,000 triangles from the three-quarter master. | [Creature textures](../CLAUDE_CREATURE_TEXTURES.md), "Geometry: Smart Topology at 15k" |
| 4 | **Clean and rig.** Proportions (G2), joints from Meshy's auto-rig plus ring fits (G3), cloned source frames (`build_rig.py`), then the mount nodes of section 5. | Humanoid playbook, gates G2–G3 |
| 5 | **Retarget and repair.** World-rotation retarget; toes, foot pitch, floor and run fixes; carry pose per set; authored blows where no clip fits. | Humanoid playbook, "Feet and locomotion after any retarget", "Weapon attacks and held props" |
| 6 | **Weights, fingers, grip.** Garment labels and weights (G4), finger weights, then the fist solved once round a standard handle and checked with the thinnest and thickest template handles (G5). | Humanoid playbook, gates G4–G5 |
| 7 | **Contacts, feet, motion.** Every clip with the longest prop of its set (claymore, halberd, staff, bow) and the widest shield; soles and jerk probes. | Humanoid playbook, gate G6 |
| 8 | **Reduce** after weighting, head and hands protected. Target: about 7,000–8,000 triangles for the body. | Humanoid playbook, "Budgets"; [modelling guidelines](../../GAME_ASSET_MODELLING_GUIDELINES.md) §1, §7 |
| 9 | **Split the head** at the collar into its own static model on a standard neck ring, plus a copy without the hair volume for use under a helm. | Creature textures, "Head detail" (`head_texture_split.py`) |
| 10 | **UVs and paint.** `uv_atlas.py`, then four body paints at 4K (one per look) on the same UVs and one head paint; downsample once; gentle grade; gutter fill last. | Creature textures, "Sharp textures"; [texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md) §0, §2 |
| 11 | **Masks and ramps.** One region mask per look (skin, livery, trim), ramps for skin per race, livery per colour and trim per tier, an emission mask for the legendary inlay. | Creature textures, "Region mask and ramps", "Building masks and ramps", "Emission" |
| 12 | **Runtime build.** `build_runtime.sh`: prepare, LODs, shadow LODs, far LOD maps for each look. | `engine/render/MODEL_RENDERING.md` §2; [LOD playbook](../LOD_PLAYBOOK.md) |
| 13 | **Gates.** Arm and hand gate on every clip, `texture_quality.py`, `check_winding.py`, `floor_audit.py`, the review viewer. | Humanoid playbook, "Arm and hand gate", gate G7 |
| 14 | **Install and bind.** `tools/install_model.py --engine`, the binding in `player_bodies.yml`, then two game runs in one session at the playbook's test locations. | Humanoid playbook, "Quick start" 6, "In-game test locations" |

**An extra race head:** head turnaround from the portraits (Codex), a head-only Meshy model, fitted to the standard
neck ring, 1K head paint, mask (skin, hair), static model plus the copy without hair. Follows Creature textures, "Head
detail" and "Problem heads".

This deviates from the HD master document in one way: the bodies are our own design guided by paperdoll art, not a
reconstruction of a sprite. The brief must say so.

## 12. Cost (estimates)

Meshy prices are the ones the playbooks record: Smart Topology 5 credits, auto-rig 5, a body or head paint 10 at any
resolution, a head-only model about 30. Codex image generation costs no credits.

| Item | Credits each | Count | Credits |
|---|---|---|---|
| Skinned body: mesh 5, rig 5, four look paints 40, one repaint in reserve 10 | 60 | 5 | 300 |
| Head paint for a head cut from the body's mesh (human man and woman, dwarf man, minotaur, troll) | 10 | 5 | 50 |
| Elf heads as edited human heads (paint only) | 10 | 2 | 20 |
| Head-only models with paint (goblin man and woman, half-orc man and woman, lich, dwarf woman) | 40 | 6 | 240 |
| **Subtotal** | | | **610** |
| Reserve, 20 % | | | 120 |
| **Total** | | | **about 730** |

- Optional `pb_dwarf_female` as its own body: about 30 more (60 for the body, and its head then costs 10 instead of 40).
- Weapons, shields, helms, tier trims and player colours: 0 credits. The models exist; trims and colours are numbers.
- For scale: the 44 weapon tier skins cost 470 credits.

Agent effort, in sessions of about half a working day (estimates):

| Work | Sessions |
|---|---|
| `pb_male`, including the clip list for nine sets | 4 |
| Each further body (female, dwarf, minotaur, troll) | 2 each, 8 |
| Eight extra heads | 4 |
| Helm placement table and a check of 56 helms | 1 |
| Engine changes 1–11 | 3–4 |
| **Total** | **about 20** |

Size on disk (estimate): one file per body with mesh and 48 clips, about 6–8 MB, plus four looks of cooked textures;
heads about 1 MB of mesh each plus a 1K texture set.

## 13. Order

1. **First slice, to prove the approach (about 60–90 credits, 5–6 sessions).** `pb_male` with the `cloth` and
   `plate` looks, the sets `Unarmed`, `Onehand`, `Shield` and `Bow`, the human head and the elf head, weapon templates
   in the hands, engine changes 1–5 and 7. It answers the risky questions: does the head on the head bone hide its
   seam, does one fist hold every handle, do ramps per instance work, does an MM9 clip retarget cleanly (one `Taunt`).
   The owner looks at two players side by side before anything else is paid for.
2. **Finish the male body:** `leather` and `chain`, the other five sets, tier trims, livery colours, the stowed bow.
3. **`pb_female`.**
4. **Race heads and helms:** goblin, half-orc, lich; dark elf, vampire and zombie colours; the helm table.
5. **`pb_dwarf_male`, `pb_minotaur`, `pb_troll`.** The monster models stand in until then.
6. **Optional:** MM9 emotes, `pb_dwarf_female`, cloaks, textures uploaded per used variant.

## 14. Risks

- **Head seam.** A rigid head over a bending neck can show a gap. Mitigation: every look has a collar and the head
  includes the upper neck. Fallback: weld head and body at build time into one file per race (no paid job, more disk).
- **One fist for every handle.** The playbook solves the fist round one weapon. A dagger and a staff differ in
  thickness. Mitigation: solve for the template handle and gate the two extremes.
- **Painted armour has no bulk.** Plate on a shared mesh has no pauldrons. The guard was accepted this way; if it is
  not enough, add rigid shoulder pieces as attachments.
- **No robe.** The `cloth` look is tunic and trousers. A real robe needs skirt geometry and its bones.
- **Clip quality per set.** The humanoid set's one-handed idle is a low guard that users read as crouching; upright
  sources and authored carries are needed (playbook, "Upright vs guard clips").
- **MM9 clip retarget is untested** (section 3).
- **Hair under a helm.** Solved by the second head copy without hair; a tall helm on a goblin's ears needs a check.
- **Memory.** All four looks of a body upload together today. With 2K colour that is about 40 MB of GPU memory per
  body in view (estimate from the guard's measurement); change 12 removes it.
- **Far LOD maps** must be built for each look; four times the usual work of that step per body.
- **MM9 weapons** show a generic template until they get `held.yml` rows.
- **Image tool refusals.** Codex refused a halberd brief once ("violence" flag). Body and head masters carry no weapons.

## 15. Decisions for the owner

| # | Decision | Recommendation |
|---|---|---|
| 1 | Rig family | The humanoid set layout with library clips; MM9 clips retargeted for emotes only |
| 2 | Armour looks | Four looks by armour type; tier as trim colour and a legendary glow |
| 3 | Races | Heads and skin colours on shared bodies, not a full body per race |
| 4 | Dwarf women | The dwarf man's body with a woman's head first; an own body only if it looks wrong |
| 5 | Minotaur and troll | Own bodies in the last wave; monster models until then |
| 6 | Dragon | Keeps its monster model for good |
| 7 | Helms | Show the worn helm's own model, from the fourth step |
| 8 | Caster robe | Not now; the `cloth` look serves every unarmoured class |
| 9 | Weapon models | The first-person templates and tier skins by default, the same switch to our ground models |
| 10 | Player colour | By session slot at first; a setting to choose it later |
| 11 | Where they live | Engine content (`assets_source/engine/models/`), since every world uses them |
| 12 | Oblivion's third-person clips | The local extraction has 453 of them, named like the first-person sets. Not needed by this plan; I would use them only for a set where the library fails gate G1. Owner's call. |
| 13 | Budget | Approve about 90 credits for the first slice (mesh 5, rig 5, two looks 20, one repaint 10, human head 10, elf head 10 to 40); the rest after its review |
| 14 | Portrait likeness | One head per race and sex now; hair and skin colour per portrait later (colour data only) |

## 16. Not verified

- That an MM9 clip retargets cleanly onto the `B_*` rig.
- That a head-only Meshy model costs 30 credits today (the number is from the texture document), and that elf ears
  can be made by editing the human head.
- The size estimates for animation and files.
- Whether the item marked as the one shield without a `held.yml` row matters in play.
- MM9's helm, weapon and shield ground models (`worlds/mm9/world_items/items.yml`) were not counted by kind.
- The armour value bands in `armour_looks_manifest.yml` are my proposal; MM9 armour values were not read.
- The three `.yml` files in this folder are ignored by `level_generation/.gitignore` (rule
  `/creatures/*/**/*.yml`). Only this README is tracked unless the rule gets an exception or the files are renamed
  to `*_manifest.yml`.

Scratch scripts and their JSON output (not kept beyond this session):
`/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/b981ca9f-2817-4abd-b052-a52790407614/scratchpad/player_bodies/`.
