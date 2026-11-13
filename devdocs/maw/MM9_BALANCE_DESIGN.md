# MAW in MM9: balance design

Design of 2026-11-09; the user's answers are in section 7, what is built in section 9. It covers what MAW needs to play well on Chedian:
map levels and a route, quest experience and gold, monster density, MM9's equipment, its hirelings, and one file
that holds every MM9 number MAW uses so that testers' reports can be turned into changes in one place. What is
already built is in [MM9_SUPPORT.md](MM9_SUPPORT.md). Drafts: [mm9_drafts/](mm9_drafts/).

## 1. One source of truth

Every MM9 number MAW uses lives in one hand-edited file, `assets_dev/engine/rulesets/maw/worlds/mm9/balance.yml`
(the engine package ships it; without MM9 it is never read). Nothing else is edited by hand for MM9 under MAW.

```yaml
version: 1                  # testers quote it (to show on the Rules panel and the Progress tab: not yet)
changelog:
  - {version: 1, date: 2026-11-xx, note: first balance}
maps:                       # every MM9 map, checked by the tool
  isleofashes.blv:
    stage: act1             # route position (section 2)
    band: [3, 3, 4]         # MAW's low/mid/high B levels
    horizontal_starter: true
    madness_level: 4
    density: 1.0            # this map's share of MM9's grown scene (section 4)
    treasure_level: 2       # map_stats column 12 under MAW
    note: start island, out01's role
monsters:                   # rows or families (by picture stem), only where MAW's model needs help
  "MM9 212 Dragon King": {level: 300}
density:                    # factor per difficulty and challenge mode (section 4)
  easy: 0.8
  maw: 1.0
  hard: 1.25
  nightmare: 1.5
items:
  rung_by_quality: [1, 2.25, 3.5, 4.75, 6]
  overrides: {}             # per item id, where the rule is wrong
hirelings: {scale: true, refuse_from: doom, none_in: [beyond_madness]}
quests: {gold_bonus: true}
```

- The engine reads it directly where MAW already reads YAML: map bands, starters and madness levels (beside
  `data/map_levels.yml`), item bases (beside `data/items.yml`), density factors, hireling and quest switches.
- `tools/maw/mm9_balance.py` checks it against MM9's tables and scenes (every map with monsters has a band, ids and
  pictures exist, rungs and bands are in range) and writes what must be a table: the `world: mm9` patches of
  `monster_data` and `map_stats` (MM9_SUPPORT.md "Ruleset patches for a world's tables").
- The same tool writes a review page for testers: per map its stage, band, the monster levels it gives (free and
  horizontal, no banks and typical banks), monster counts per difficulty, and HP and damage against the expected
  party of its stage; and the item table. A report names the version and the map; the fix is an edit of
  `balance.yml`, a run of the tool and a changelog line.

## 2. Map levels and the route

MAW's MM6-MM8 route (`data/map_levels.yml`): starters at B 3-7, the first quarter of each continent at 6-24, the
middle at 20-50 (Antagarich's castles up to 64), the last quarter at 55-100. Horizontal progression puts a map's
monsters at about 2.5 x its band; Beyond Madness gives each map a fixed level from its route position
(500 x (position / N)^1.2).

MM9's acts go on the MAW bands of the MM7 stage its Standard balance equates them with (party level 6 / 17 / 33 / 51 /
64 against MM7's 6 / 21 / 37 / 54 / 68). Draft for all 44 maps, with each map's natives and the levels they give:
[mm9_drafts/map_levels_draft.yml](mm9_drafts/map_levels_draft.yml).

| Stage | Maps and bands |
|---|---|
| Act 1 | Bootcamp [1,1,2], Isle of Ashes [3,3,4], Sturmford [4,6,9], Beet Hoven [5,7,10], Anskram Keep [7,9,12] |
| Early clans | Drangheim [9,12,15], Prison [12,14,17], Guberland [10,13,16], Thjorad Mine [12,15,18], Thjorgard [14,17,21], Ta'Sar Academy [16,18,22] |
| Clans | Lindisfarne [20,25,32], Monastery [24,28,32], Chasm [20,24,30], Frosgard [24,28,32], Thronheim [24,28,34], Mountain Pass [24,30,36], Yanmir's Fort [28,32,38], Inventa Storca [28,33,40], Dook's Castle [30,34,40], Ruined Temple [32,36,42] |
| Late side dungeons | Kluso's House [40,44,48], Training Hall [40,46,54], Verhoffin Ruins [44,50,56], Lich Lab [46,52,58] |
| War | Connecting Tunnels [48,52,58], Yorwick [50,54,60], Wizard's Lab [52,57,62], Dark Passageway [56,62,68], Bathhouse [60,65,70] |
| Finale | Temple of Honk [70,75,80], Afterworld [75,80,85], Thousand Terrors [80,88,96], Dragon's Lair [90,95,100] |

Cities take their region's band (it sets only loot and scripted spawns). Horizontal starters: Bootcamp, Isle of Ashes,
Beet Hoven, Anskram Keep. Beyond Madness starts on Bootcamp and Isle of Ashes.

**The peaceful route is an option, not a requirement.** MM9's talk and delivery quests before the war council pay
about 124,000 experience and 35,000 gold per member, about level 16 on MAW's curve, the early clans' band. They let a
new party buy gear and train before it fights, and nothing on the route needs them:

| Quest | Where | Experience | Gold |
|---|---|---|---|
| Ivan the Smart's trivia, then the certificate to Markel | Guberland, Guberland City | 5,000 + 16,500 | 3,000 |
| Nicolai's trapeze job for Thorir | Drangheim City, Guberland | 16,500 | 5,000 |
| Love letter to Kira, her answer to Bjarni | Sturmford City, Thronheim City | 12,000 + 12,500 | 2,000 |
| Three Honk missionaries, then Kira's reward | Thronheim City | 8,000 + 12,500 | 7,000 |
| Orb of Linking in the six city banks | six cities | 12,500 | 15,000 |
| Keg to the Guberland tavern and back | Frosgard City, Guberland City | 5,000 + 12,500 | 500 |
| Plow, herbs and dolly returned | Drangheim | 6,000 | 1,500 |
| Randver, the saboteur, gossip | Sturmford City | 4,800 | 1,000 |
| Dagfari's news to the temple | Thronheim City | 5,000 | 5,000 |

Later ones (the Thing's games and Bikki's stuffed dragon, the six gathering prizes) pay 10,000-18,500 each.

**Horizontal progression on Chedian needs MAW's continent teleporter** in its starting town (MAW README §2.1), as the
other continents have.

## 3. Quest experience, quest gold and bolster

- **MAW scales quest experience** by the levels banked on the other continents only: value x (1 + L/100) + 500 L,
  L = `levelOutside(continent)` (all four banks in Beyond Madness), five times per member over the party size
  (`MawExperienceRules.cpp:70-89`). It ignores party level and difficulty. MM9's experience (`MM9.giveExperience`)
  already goes through it, and its continent is now Chedian's.
- **Keep MM9's chapter caps under MAW** (1.33M experience per member over the story instead of MM9's 4.3M). MAW's
  curve matches the vanilla one up to level 101, so the uncapped total would take a fresh Chedian party to level
  93-98 on quests alone, and in free progression Chedian's own levels never raise Chedian's monsters: the party would
  outgrow every band. The capped total is close to the 1.7M of MM7's quests MAW keeps for Antagarich. Kill experience
  grows by itself with MAW's levels. If tests find the late chapters stingy, `balance.yml` can raise their caps.
- **Apply MAW's quest gold bonus to MM9's rewards.** MAW adds gold x L/100 + 250 L to a quest that pays gold and
  experience, but only in MM6-MM8's NPC topic events (`GameplayDialogController.cpp:1509-1528`); MM9's RUDE reward
  hooks never reach it. A party starting on Chedian (L = 0) sees no difference; one arriving with banks is paid like
  on the other continents. The change is in shared dialogue code around the RUDE hook.
- **MM9's bolster rows stay**: MAW turns the engine's bolster off, so under MAW they only carry the continent.

## 4. Monster density

**What MAW does elsewhere.** Group sizes per spawn point by difficulty: 1-3 up to MAW, 1-4 Hard and Hell, 2-4
Nightmare, 2-5 Doom, 3-5 Road to Insanity, 3-6 Beyond Madness (means 2, 2.5, 3, 3.5, 4, 4.5); measured over whole
MM7 and MM8 maps that is x1.2 at Hard and x1.4 at Nightmare (placed actors stay). MM9 has no spawn points: every
monster is a scene actor, and its converters grew MM9's packs at conversion toward the Standard targets (1,476
monsters to 2,723). Its packs average 2.8-4.6 monsters, against MAW's 2, but MAW sizes each monster by its model, not
by MM9's weaker stats, so the grown scene is the fair MAW baseline.

**Design: a pack reserve written by the converter, applied deterministically by a generic engine hook.**

- `density.py` already places copies of a pack's members beside them with every safety rule (doors, movers, event
  faces, ladders, water, path reach, scripted and Lua-named actors). It keeps growing past the Standard target up to
  the largest factor (2.25, within the map's room) and writes the extra copies to a scene section `pack_reserve`:
  whole actor records with `copy_of`, `pack` and `from_factor`, the smallest factor that includes them. A harder
  difficulty only adds copies; the same factor always gives the same monsters. The copies it places today get a
  `density_level`, so a factor below 1 can leave them out.
- The rules give a factor: `MonsterRules::packDensityFactor(map)` (Standard 1; MAW the difficulty's group mean / 2,
  the same ratio its experience multiplier already uses, times the map's `density` from `balance.yml`).
- At a map's first fill and on each refill, `IndoorWorldRuntime` appends the reserve entries up to the factor after the
  scene's actors (map Lua's actor indices stay), before hostility, event spawns, AI states and `placeMapMonsters`, so
  the copies get MAW levels, can be bosses and count for map completion.
- Saves keep the appended actors. The layout identity hashes the reserve, so a reconversion resets a map and a
  difficulty change does not; the next refill uses the new difficulty.
- Maps whose Lua counts placed actors (Yanmir's Fort) keep no reserve. Past the room limit the copies move a tier up
  (A to B, B to C), as MAW raises the encounter tier from Nightmare.
- ~~Fix first: the Tomb of a Thousand Terrors was never grown~~: done 2026-11-09 in its converter, at 2x since that
  evening (186 monsters; section 9).

Rejected: copying monsters at load in the engine (it would duplicate `density.py`'s placement and scripting rules and
risk monsters in doors, on plates and in water) and MAW scene overlays per difficulty (six files a map, overlays do not
know the difficulty, and a difficulty change would reset saved maps).

## 5. MM9's equipment

MAW gives every MM6-MM8 weapon and armour a base, `[rung, dice, two_handed, AC, reference AC]` (`data/items.yml`),
and everything MAW does with an item starts from it: enchantments and rarity, damage, armour, level requirement,
value, crafting. Item power comes from the drop level; the rung adds flat damage (up to +16 two-handed, +8
one-handed) and up to 15 levels of requirement. MAW ranks a family's items on rungs 1, 2.25, 3.5, 4.75 and 6.

**Rule for MM9's 133 pieces** (draft: [mm9_drafts/item_bases_draft.tsv](mm9_drafts/item_bases_draft.tsv), each row
with its nearest MM6-MM8 base to compare):

- Rung by MM9's quality, which the MM9 balance already set equal to MM6-MM8 tiers 1-4 and 6: 1, 2.25, 3.5, 4.75, 6
  (22 / 25 / 29 / 29 / 28 items).
- Dice: the item's own dice count, as MAW reads MM6-MM8's. Two-handed: MM9's two-handed weapons (halberds, staves);
  spears stay one-handed as MAW has them.
- Armour: MAW's average AC of the slot at that rung, scaled by the item's MM9 armour against its slot and quality
  (Imperial Scale stays above Scaled Leather); reference AC the slot's top. Belts take MAW's belt ladder, rings and
  amulets none.
- They match their MM6-MM8 neighbours closely: Laga Couta and Labyrinth Grapple are both `[6, 3, 1, 0, 0]`, Dark
  Plate 59/59 against Noble Plate 58/58.
- Throwing daggers and axes go on the dagger and axe ladders (MAW has no Throwing skill); the Coif reads as a hat, as
  MM8's Horned Helm does; MM9's chain and plate start at rung 3.5 (it has none below quality 3).

This also fixes MM6-MM8 MAW games with MM9 installed, where MM9's gear drops plain today.

**Artifacts and relics**: they keep MM9's fixed effects; quest-placed ones stay where they are. MM9's black chests'
level-7 slots already roll as MAW's boss drops under MAW (the user: fine; no guaranteed artifacts). Set pieces and
Bootcamp's gear get no base, as MM6-MM8's unique items.

Also needed: `mawShownRarity` finds rarity by MM6-MM8 id ranges (`MawItemRules.cpp:77`) and must use the base
instead; `adjustShopStock` knows shops by MM6-MM8 house types, so MM9's spellbook shops get crafting gems and its
apothecaries not (`:2454`).

## 6. MM9's hirelings

MAW never scales MMerge's followers or mercenaries by level: mercenaries are made at the party's level and level up
as members, followers do not fight, and from Doom up followers refuse to join (story ones excepted). MM9's 15
hirelings fight with their row's fixed dice and level, outside `party.members()`, so MAW neither counts nor scales
them: at party level 35 Hrolf does about a fifth of an expected member's damage, Forad at 50 a twelfth, and both die
in two or three hits.

Proposal:

- **Scale each hireling to MAW's expected character at the party's average level, keeping its share**: damage by
  the model's power ratio, HP by its health ratio (keeping the current fraction), armour and hit level up with the
  party, spell skill and mastery by the model. Hrolf stays a fifth of a member and does not fall behind; no hireling
  becomes a sixth member that MAW's party-size sizing ignores. Nothing new is saved. One rules hook
  (`ClassRules::hirelingScaling`, Standard: unchanged) applied where the hireling is hired, levels and attacks.
- **Refusals as MAW's followers**: paid hirelings refuse from Doom up, none in Beyond Madness; story companions
  (Forad, Tamur) always join.
- Wages stay MM9's unless the user wants them scaled too.

## 7. Decided (the user, 2026-11-09)

- Four continents; Chedian is MM9; MM9 starts at Bootcamp.
- The single source of truth (`balance.yml`) and the draft bands.
- **The Arena** as MMMerge's arenas: MM9's picks its fighters by the party's mean level as they do, so it gets MAW's
  arena rules (no bolster, nothing in Beyond Madness) and their band [1, 1, 1] and madness level 1.
- **The Battle of Frosgard** sized from MM9's own story: it comes after the Afterworld's six fires (playthrough
  segment 59, Standard party level about 64), where MM9's Horde (A 34, B 44, C 54) is about 0.7 x the party. Frosgard
  City keeps its region's band until MM9 key 104 (QBit 90104), then [66, 72, 78]: the Horde at 45 / 55 / 65, the same
  ratio to a MAW party of the stage. Its chests keep the act-2 band before that.
- **Density factors from MAW's own maps**: MAW's group sizes raise whole MM7 and MM8 maps by x1.2 at Hard and x1.4 at
  Nightmare, 80 % of the groups' growth; the same rule for the rest: Easy, Normal, MAW 1.0; Hard, Hell 1.2; Nightmare
  1.4; Doom 1.6; Road to Insanity 1.8; Beyond Madness 2.0.
- **MM9 gear is not a copy** of MM6-MM8's: it takes MAW's rungs and armour, and some pieces are 10-15 % ahead, an
  incentive to wear something new: the strongest MM9 piece of each kind and quality by its own numbers does 1.10
  times its peers' damage or armour, 1.15 at the top quality (35 of 133). Comparing MM9's numbers with the nearest
  MM6-MM8 item found too few (4): the MM9 import had already put its items on MM6-MM8's tier medians.
- **Map completion**: MM9's sea monsters and Jellyspores never count (they guard the water: Isle of Ashes, Sturmford,
  Guberland), and any map can leave out more monsters by row, name, picture or family (`completion_exclude`).
- Hireling wages stay MM9's.
- No guaranteed artifacts from black chests under MAW; quest-placed items stay.
- Density grows deterministically, not by rolled duplicates (section 4).
- Drowning stays MM9's 1/6 of maximum HP a tick; falls follow the generic rules.

- **Natives**: the map table's encounter pictures do not always match what MM9's scenes place (Inventa Storca lists
  Zombies and has none, its liches unlisted), so `balance.yml` names a map's natives where they differ (six maps), and
  the tool lists every such mismatch. Inventa Storca's liches are its top natives (band [28, 33, 48]: Liches 38, Lich
  Kings about 56).
- An Emerald upgrade may turn an MM6-MM8 item into an MM9 one: OpenYAMM serves MM6-MM9 together.
- The Dragon King's level stays as the bands give it (about 300) for now.
- Horizontal progression's continent teleporter is Sturmford City's dimensional pedestal (event 250), already there.
- Story companions (Forad Darre, Tamur Leng) always join, whatever the challenge mode; they scale as the others.
- **Chedian's Seer is Hjordisa the Hag** (Guberland): MAW's skill reset and Dimensional Maps. **The Jarls give
  bounties for their regions**, the target placed on the party's next visit; Arslegard has none (MM9_SUPPORT.md).
- **A game may skip Chedian and play as before**: MM6-MM8 maps drop only MM6-MM8 items unless the Gameplay setting
  "MM9 loot in MM6-MM8" is on (off by default, any ruleset; [LOOT_POOL.md](../LOOT_POOL.md)); Chedian drops a mix of
  every world's. Everything else MM9 adds to MAW waits in Chedian: its level bank, its Beyond Madness ladder, its
  promotions (the promotion factor still counts three worlds at most), its hirelings and its gear.

## 8. Ideas noted (the user, 2026-11-09), not planned yet

- **Families far apart on one map.** MM6-MM8 keep a map's families close in level; MM9 mixes very weak and very strong
  ones. MAW's bands already pull them together (natives pinned to low, mid and high, the rest halfway), but a map may
  still want a family swapped, as MAW put Dark Knights in Darkmoor Castle instead of ogres: a `swaps` entry
  (family -> family) in `balance.yml`, applied when the map's monsters are placed.
- **The route by need.** The story's maps and the first and second promotions' maps are known: tag each map with its
  role (story, promotion 1, promotion 2, side) in `balance.yml`. Second promotions may well be hard; side-quest
  dungeons (Inventa Storca) can sit later than their region as optional later-level dungeons.

## 9. Built and next

Built (2026-11-09):
- `rulesets/maw/worlds/mm9/balance.yml` (version 1): all 44 maps with stage, band, starters, madness levels, the
  Frosgard City story band, the Arena, the completion exclusions and the item rule. MAW loads a mounted world's
  `balance.yml` after `data/map_levels.yml` (`MawMapLevels::loadWorldBalance`); story bands follow the party's quest
  bits (`MawRules::updateStoryBands`, four times a second with the promotions).
- `tools/maw/mm9_balance.py`: checks the file (every MM9 map listed, bands in order, story bands on MM9 quest bits,
  exclusions naming MM9 monsters), writes `item_bases.yml` (133 bases, `MawItemData::loadWorldBases`, the sixth value
  the strength, applied to weapon damage and armour) and `--review <file>`, the testers' page (each map's stage, band,
  counted and placed monsters and families; each item's base, peer and own-to-peer ratio). `--check` fails when
  `item_bases.yml` is stale.
- `MonsterRules::countsForMapCompletion` (the world runtimes' kill progress; MAW asks the balance file).
- **MAW's whole map table, computed by the game**: `ruleset maplevels <file.tsv> [banked]` (debug console;
  `MawRules::mapLevelTable`) writes every installed world's listed maps with their level as the Progress tab counts it,
  free with no banks and with 50, horizontal and Beyond Madness, whatever the game's own options.
  `tools/maw/maw_map_levels.scenario.yml` runs it headless; `mm9_balance.py --review <file> --levels` adds the table to
  the review page: the four continents side by side, MM9's stages in story order with a check that no story stage's map
  sits below the stage before it, and every map sorted by horizontal level. First run (version 1): free 4-88 and
  horizontal 4-211 on Chedian against 1-100 and 4-241 on the other three; MM9's stages climb (act 1 4-10, clans 53-83,
  finale 179-211 horizontal); no route warnings.
- Tests: `MawMonsterLevelTests` (world balance, story bands, exclusions), `MawCraftingTests` (world bases).

Built (2026-11-09, second step):
- **Rarity of unrolled MM9 gear**: `mawShownRarity` counts MM9's based items as MAW's MM6-MM8 equipment (name colour,
  loot filter); the MM6-MM8 id ranges stay as they were (the Blasters there have no base).
- **MM9's shops under MAW**: MM9's vendors sell fixed stock (vendor_stock), which never reached MAW's shop rules, so
  its gear sold at item power 0. `ItemRules::rollsFixedShopStock` (Standard no, MAW yes): the vendor keeps its items,
  MAW rolls their power, rarity and enchantments as shop stock at the vendor's tiers, at each restock
  (`ensureHouseStockGenerated`). Crafting gems: MM9's apothecaries take the alchemist's place; MM9's "Magic" vendors
  sell spellbooks, so neither the gem swap nor the reroll offer applies to them (`sellsCraftingMaterials`, `magicShop`
  in `MawItemRules.cpp`). Test: `MawMm9ShopRuntimeTests.cpp` (runtime tests; needs the MM9 package).
- **Quest gold bonus for MM9's quests**: MM9 pays its quests in a talk's exit handler (the map Lua's
  `reward(key, experience, gold)`); `executeMm9RudeExitCallback` now measures it as MM6-MM8's topic events are measured
  (gold and the first member's experience before and after, `payQuestGoldBonus`), so MAW adds its bonus. Standard's
  bonus is 0. The measure now keeps experience 64-bit (it was cut to 32 bits).
- **The Level popup** names the fourth bank: `levels_mm9` and `bolster_mm9` (`MawSkillRules.cpp`, `data/texts.yml`
  Level). The language packs' translation of that sentence is stale until the release pass.

Built (2026-11-09, third step: MAW plays in MM9):
- **Density, deterministic**: `tools/maw/mm9_pack_reserve.py` runs the converter's own pack placement
  (`mm9r_common/dungeon/density.py` `grow`, every rule of it) on each installed map, beside its actors, for up to
  2 x its monsters, and writes the copies as MAW's overlay `rulesets/maw/maps/<stem>_zz_maw.scene.yml`
  (`initial_state.pack_reserve`). The copies of all packs are interleaved by each pack's share and numbered map-wide, the
  k-th joining at factor 1 + k / N. The scene overlay carries `scene_actors` and `scene_check`; a map rebuilt since
  uses no reserve and says so, and `mm9_balance.py --check` fails until the tool runs again. The engine:
  `MapDeltaData::packReserve` (from the assets, never saved), `MonsterRules::packDensityFactor` (Standard 1; MAW
  `balance.yml` `density`: Easy, Normal, MAW 1.0, Hard, Hell 1.2, Nightmare 1.4, Doom 1.6, Road to Insanity 1.8,
  Beyond Madness 2.0, times a map's own `density`), appended right after the scene's actors at a first fill and each
  refill (`IndoorWorldRuntime::materializeInitialMonsterSpawns`), the load-time MM9 profile refresh following them,
  the layout identity counting a reserve (maps without one keep theirs). The reserve leaves out what
  `completion_exclude` leaves out (the sea's guards). It lives with MAW, not in the converters' scenes: the converters
  belong to the MM9 rework, which other sessions were changing (density.py, 1000 Terrors) during this work.
  29 maps have one, most reaching x1.7-2.0; short: Drangheim Prison (x1.12), the Bathhouse (x1.28), Dook's Castle
  (x1.45), Ta'Sar Academy, Kluso's House, the Temple of Honk (packs the converter takes for scripted) and
  Yanmir's Fort (its Lua counts the placed actors). Scenario: `tests/scenarios/mm9/maw_density.yml`.
- **The Tomb of a Thousand Terrors**, never grown before (114 monsters of a target of 465), is grown since 2026-11-09
  late in its converter, for Standard and MAW alike: 319 copies, 412 monsters (the map Lua's `KIND` table and two loops
  over every actor by a variable `index` had made the converter take every member for scripted; only the fly-past
  critters are messaged, and they stay uncopied; `level_generation/projects/mm9r_1000terrors/README.md`, "Pack
  growth"). Its 5x piled about ten times the monsters into its open halls, so the user set it to 2x the same evening
  (`MAP_FACTOR` in `tools/mm9_import_discovery/mm9_density_targets.py`): 93 copies, 186 monsters; MAW's reserve adds
  up to x2 on that (none at MAW, 260 at Nightmare).
- **Hirelings**: `MawClassRules::scaleHirelings` (four times a second): each MM9 hireling at the party's mean level when
  that is above its row's keeps its share of MAW's expected character: health (its share of the current kept), armour,
  hit level, damage (`Mm9PartyHireling::rulesDamageScale`) and spell skill (`rulesSkillScale`), neither saved.
  `ClassRules::paidHirelingRefusal` (MAW: Doom and up, as its followers): paid retainers decline with MAW's line
  (`Mm9HireOutcome::Declines`), story companions join. Wages stay MM9's. Test: `Mm9HirelingServicesTests`.
- **Used barrels**: `MonsterRules::keepsUsedBarrelsThroughRefill` (MAW): a refill keeps MM9's used barrels used (their
  state is already saved with the map; no save change). MAW's rule is for barrels that raised a stat; MM9's barrel
  states do not record what they gave, so every used one stays empty.
- **The gate**: `ruleset.yml` `worlds: [mm6, mm7, mm8, mm9]`.
- **Comparisons**: `ruleset mapmonsters <file.tsv>` (`MawRules::mapMonsterTable`): every listed map's native families,
  A to C, as the game makes them (level, HP, armour, attack damage). `mm9_balance.py --review <file> --levels` adds
  "Comparable encounters": each MM9 story map beside the two MM6-MM8 maps nearest its level (free progression,
  nothing banked), with monsters at MAW and Nightmare and the B families' numbers. First reading: MM9's dungeons hold
  about what MM6-MM8's do (Beethoven 156 against the Abandoned Temple's 219, Thjorad Mine 77 against Barrow II's 60),
  but its regions a third to a quarter of MM6-MM8's outdoor maps (Drangheim 32 against Harmondale's 150, Guberland 40
  against the Barrow Downs' 130, Lindisfarne 57 against Alvar's 122). A map's `density` in `balance.yml` can raise
  them; the reserve reaches 2 x today, so a region at 3-4 x needs a larger reserve (MAX_FACTOR) first.

- **Thjorad Mine x3** (the user, 2026-11-09: its rooms hold one to three Troglodytes; a lot more): its `density` 3.0 in
  `balance.yml`, so 77 monsters become 231 at MAW, 323 at Nightmare. Later that day the rebuild itself grew the mine
  for every game, at 1.4x as the rest of its act (108 monsters; a few hours at 1.8x first), and its MAW `density`
  became 2.1 on top (balance.yml version 2: about 227 at MAW, 318 at Nightmare). A map's reserve is now made for its highest factor
  (its `density` times the file's highest, at most 8; the mine's to 6 x), and each pack has room for twice its own
  copies, so the copies of scripted packs land with the others (Drangheim and Guberland now reach 2 x, Dook's Castle
  1.71 x, the Training Hall 1.84 x).

Built (2026-11-09, fourth step, the user's answers on density, scripted maps and promotions):
- **Regions** at about 90 monsters at MAW (MM6-MM8's outdoor maps of their level hold 120-220): `density` Drangheim
  2.8, Guberland 2.5, Thjorgard 2.0, Frosgard 1.8, Thronheim and Lindisfarne 1.6 (Drangheim 89, Guberland 95,
  Thjorgard 97 at MAW, a third more at Nightmare). Ta'Sar Academy 1.5.
- **No crowds** (the user: never ten monsters in a few steps): `mm9_pack_reserve.py`'s crowd rule refuses a copy where
  6 monsters stand within 400 units of the spot or of a monster near it; checked over the densest maps at MAW and
  Nightmare: at most 6 others within 400 of any monster (7 where MM9's own scene had them so).
- **Arrival leeway** (the user: not swarmed where a teleport puts the party): no copy within 1500 of a map's start
  points, of map_transitions arrivals, of other maps' `evt.MoveToMap` spots into it, or of `balance.yml` `arrivals`
  (Chasm of the Dead's revolving wall and rim); the converter's `density_arrivals` (Dark Passageway, Wizard's Lab) keep
  their quotas.
- **Packs from the scene**: hostile monsters no target pack holds form packs of their own (within 700, one sector), so
  maps the targets cover thinly take copies too (Ta'Sar Academy).
- **Scripted groups**: `reserve_lua_groups` (the Temple of Honk's Honks, group 1, which HonkHostility.inc turns as a
  whole): their members take copies, which turn with them; the Temple reaches 2 x.
- **Drangheim Prison**: `rulesets/maw/events/maps/drangheimprison_maw.lua`: the alarm (key 5006) calls the garrison,
  guards of all three ranks at the four of six posts farthest from the party (never within 1500), three each (Hell
  and Nightmare four, Doom and up five). Scenario `tests/scenarios/mm9/maw_prison_garrison.yml`.
- **Bathhouse** left as it is (five copies; small rooms and scripted or boss members); **Kluso's House** as it is
  (the user). The **Training Hall** gets almost none under the crowd rule: its rooms are full already.
- **The Tomb** grown in its converter (the user, 2026-11-09, the rework's session gone): a Standard fix, then MAW's
  reserve on top (devdocs/mm9_rework/FINAL_REBUILD_GAPS.md section 7).
- **Spawn tiers of a world's rows**: `gameplaySpawnMonsterId` drew a summon's tier by id triples, wrong for MM9's rows
  (MM9 Guard 9111 drew 9109-9111); a world's row now goes by its picture's tier letter (Standard's summons in MM9 too).
- **Promotions** (the user: Chedian's as MM6-MM8's, the closest MM9 quest): `promotions.yml` `mm9` per class kind,
  the done key of MM9's second-tier quest of the line's theme (Gladiator 221: knights, monks, minotaurs, trolls,
  dragons, Death Knights; Assassin 227: thieves, vampires; Paladin 237; Ranger 249: rangers, archers; Priest 261:
  clerics, Seraphim; Druid 280: druids, dark elves, Shamans; Mage 294 and Lich 299: sorcerers, necromancers,
  Elementalists Mage only), and MAW's own lines' first steps from MM9's first tier (Healer 213: Seraphim, Shaman;
  Mercenary 127: Death Knight; Scholar 205: Elementalist). Chedian counts as a fourth world: Elder and Ultimate
  at two and three worlds, and since 2026-11-09 (the user) Supreme at all four, x1.75 (DEVIATIONS 183). Test: `MawClassTests` "Chedian".
- **Beyond Madness and horizontal levels**: MAW's continents are parallel ladders, each from level 1 to 500 in Beyond
  Madness (Jadame 57 maps, Antagarich 75, Enroth 53) and to about 220-240 in horizontal progression; Chedian is a
  fourth ladder (to 500 and 211), as MAW makes its continents, not a longer one.

Next: tester builds; the ideas of section 8.
