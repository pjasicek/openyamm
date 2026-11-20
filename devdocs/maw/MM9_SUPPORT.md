# MAW in MM9 (Chedian)

MAW plays on four continents: Jadame (MM8), Antagarich (MM7), Enroth (MM6) and Chedian (MM9) (the user, 2026-11-09);
`ruleset.yml` lists mm9 since 2026-11-09. This file records what is built for it; the balance (map levels, density,
items, hirelings) is in [MM9_BALANCE_DESIGN.md](MM9_BALANCE_DESIGN.md).

## Built (2026-11-09)

- **Chedian is continent 5 for every MM9 map** (`engine/data_tables/bolster_maps.txt` rows 9001-9080; they said 0,
  which the map table reads as Jadame, and Bootcamp, 9080, had no row: it has one now, without bolster). In Standard games this only moves MM9's journal history entries and Arcomage
  taverns from Jadame's group to Chedian's and names Chedian on the load screen: MM9's own `partyDeath` decides
  defeats, its sky does not come from the continent row (BLV maps), and neither row turns on continent reputation.
- **Four level banks**: `MawGameState::continentLevels` is Jadame, Antagarich, Enroth, Chedian (continents 1, 2, 3,
  5); MMMerge's fourth "other" bank was always empty, so the save format is unchanged. MAW's "every bank but the
  other one" (`getPartyLevel(4)`, `levelOutside(0)`) is `totalLevel()`, and horizontal progression counts all four
  banks. The console's `ruleset banks <mm8> <mm7> <mm6> <mm9>`, the scenario step `ruleset_banks {..., mm9}` and the
  test parties' `banks` name the fourth bank mm9.
- **MAW's new-game continents** include Chedian (`content/character_selection.yml`: the engine's Chedian classes and
  the four new class lines).
- **Vendor stock under a ruleset**: MM9's fixed stock is rolled against the Standard enchantment table; MAW stops
  rolling Elemental and Undead Slaying, Assassins' and Barbarians' on weapons, of the Storm and the Ocean on armour and
  of Shielding on jewellery (ITEMS_DATA.md), and the vendor check took weight 0 for "not applicable", so MAW failed to
  load with MM9 active. Under a ruleset other than Standard such stock is now sold without that enchantment
  (`HouseTable::removeSpecialEnchantsTheRulesetDoesNotRoll`, 49 of MM9's 287 enchanted stock items); Standard keeps
  the strict check.
- **Ruleset patches for a world's tables**: a `tables` entry with `world: mm9` and `table: data_tables/<file>` (the
  path world.yml contributes) patches that world's rows (monsters 9000+, items 10000+, vendor stock, trainers,
  hirelings) as they are read, with the same override, append and replace modes. It does nothing when the world is
  not installed. MAW has no such entry yet.
- **Monster families of a world's rows** (`mawMonsterFamily`): MAW's rows below 1000 keep MAW's id % 3 triples (every
  one with a tier suffix agrees); a world's rows go by their picture suffix ("MM9 Dragonfly A"), the A, B and C rows
  found by picture wherever they lie (MM9's Skeleton and Honk families are not contiguous), and one without a suffix
  (townsfolk, named uniques) is a family of its own at tier B. Boss levels, Broodling and Omnipotent spawns,
  the Summoner's family members and HP ratios all read it.
- **MAW levels for a world's monsters**: `resolveMawMonsterLevels` covers MAW's rows 1-651 and every row from 1000
  (MMMerge's 652-906 keep their table levels, as in MAW), so MM9 monsters get the party bolster, map bands,
  horizontal x2.5, resets and Beyond Madness levels, and MM9 encounter pictures ("MM9 Thrall") count as native
  families.
- **Bosses**: scripted actors (a Lua behaviour: Dragon King, Njam, Yanmir, Ebora, the Concubine, the Power Lich)
  never become bosses; a world's monster must also be hostile. MAW's own rows keep MAW's rule, which does not ask.
- **Open-air BLVs count as outdoors** for MAW (`MawRules::outdoorMap`, `isOpenAirMap`, `MapKillProgress::indoor`):
  no Nightmare revival, outdoor save food cost, no Road to Insanity food cap, Hell's ranged melee monsters, vampires
  by the hour, falls and drowning keeping their own damage, map resets for dungeons only, Doom's reveal-on-hit
  indoors only, fixed auras ending on outdoor maps.
- **Arena**: MAW's arenas are named by file (d42, 7d05, zarena) and include MM9's `thearena.blv`, which picks its
  fighters by the party's level as MMMerge's arenas do: no bolster, no rewards in Beyond Madness (the user's call).
- **Spellbooks**: a world's books (item ids from 10000, `mod1` S<spell>) are sealed when found and cost what MAW asks
  for its own (MM8) book of the same spell (`pricedBook`: MAW's repriced values in `content/items_patch.txt`, so
  Chedian's Meteor Shower costs 40000, not MM9's 2000), with Road to Insanity's multiplier by the spell's school and
  place on top. MM9's other items already follow MAW's prices: ordinary weapons and armour through `item_bases.yml`,
  scrolls at the MM6-MM8 scrolls' values, artifacts at their table values as MAW's own are (checked 2026-11-11).
- **No flying in Chedian** (the user, 2026-11-09): the Dragon's Flight casts MM9's Fleet Foot as Air Magic's Fly does
  (`castsFleetFoot`), and any other Fly there (a scroll, a potion, an event's buff) becomes Fleet Foot in
  `Party::applyPartyBuff`: MM9's speed (125/150/175 %) and, from a skill, MM9's duration. Across worlds: a Fly brought
  into MM9 becomes Fleet Foot for its remaining time, and a Fleet Foot ends on leaving MM9
  (`Party::setFleetFootWorld`). Tests: SpellRegressionTests "MM9 Fleet Foot replaces every Fly",
  `tests/scenarios/mm9/fleet_foot_across_worlds.yml`.
- **Fleet Foot**: names go through `partySpellName`, which gives Fleet Foot for Fly's slot in MM9 before any class's
  name (the Assassin's "Fly"); the buff HUD's aura lines now use it too.
- **Njam** vanishes below a share of his maximum HP (`worlds/mm9/behaviors/njam.lua`: MM9's 1500-4500 of 6600).
- **MAW's people in Chedian** (`rulesets/maw/worlds/mm9/dialogue.yml`, read for MAW games into
  `Mm9RudeDialogueTable::rulesetRows`; the rows stand on the person's first page): Hjordisa the Hag (RUDE 132,
  Guberland) is Chedian's Oracle, Judge Grey and Seer, with MAW's skill reset (global events 10010, 10011) and
  Dimensional Maps (10040) (`Mm9RudeRulesetEvent`). The six Jarls keep their region's bounty office
  (`Mm9RudeBountyOffice`): Bjarni (Sturmford), Tryygva (Frosgard), Markel (Guberland), Sigmund (Drangheim), Sven
  (Thjorgard) and Kira (Thronheim); Arslegard has no region and no bounty (the user, 2026-11-09). MM9's cities are
  maps of their own, so the hunt is posted in the city under the region's name (`MMerge.BountyHunt.<region>`,
  `BountyHuntRemoteMap`), its target chosen by the hunt's seed (`MonsterRules::bountyTargetMonster`) and placed when
  the party next enters the region (`spawnPendingBountyHunt`, `.Pending`); MAW opens it only once the region is
  cleared (`bountyRefusalForMap`). Kills and the reward work as a town's own. Standard games offer neither.
  Tests: `Mm9RudeDialogueTests` (the rows), `MawMonsterItemAuditTests` (the region's bounty),
  `tests/scenarios/mm9/maw_jarl_bounty_and_hag.yml` (in game).
- **MM9's start** is Bootcamp everywhere (`world.yml start`, and the continent row's position for a world launch).
- The journal's **Progress tab** has a Chedian card (MM9) once Chedian has maps with MAW levels; the cards share the
  row.

## Decided by the user

- Four continents; Chedian is MM9.
- MM9 starts at Bootcamp.
- Falls follow the generic rules. Drowning stays MM9's own: 1/6 of maximum HP a tick
  (`indoorDrowningDamage`), which no ruleset changes.
- 2026-11-09: loot from other worlds is a per-game choice (MAW and Standard); Chedian's Seer is Hjordisa the Hag; the
  six Jarls give their regions' bounties, Arslegard none; a final class promoted on all four worlds is Supreme (x1.75,
  DEVIATIONS 183); no flying in Chedian (every Fly is Fleet Foot there); the rebuild grows the Tomb 2x and Thjorad
  Mine 1.4x for every game.

## Open

Done on 2026-11-09 (MM9_BALANCE_DESIGN.md sections 7 and 9): the 44 maps' bands, starters and Beyond Madness levels
(`worlds/mm9/balance.yml`, which also lists every map, so the `{1, 1, 1}` fallback no longer applies), MM9 gear's
bases and strength, MM9's shops and barrels, quest gold, density (pack reserves, the Drangheim Prison garrison),
hirelings scaled to MAW, the Arena, artifacts (none guaranteed), promotions for MAW's classes, and the per-game "Loot
from other worlds" ([LOOT_POOL.md](../LOOT_POOL.md)): off, a game that never goes to Chedian plays as before MM9.

Still open:
- **Play under MAW**: the MM9 story playthrough (`tests/playthrough/mm9/`) has not been run under MAW; tester builds
  (MM9 stays out of releases).
- ~~The Tomb of a Thousand Terrors' density~~: done 2026-11-09, 2x in the rebuild (186 monsters) and MAW's reserve on
  top (`devdocs/mm9_rework/FINAL_REBUILD_GAPS.md` section 7).
- **Fleet Foot leaving MM9** ends (a Fly entering MM9 becomes Fleet Foot). Turning it into Fly for its remaining time
  instead is the user's call (asked 2026-11-09; the recommendation is to keep it ending).
- **A map's first-completion reward is lost when every pack is full** (any MAW world, not only Chedian): the Crafting
  Cube and two gems go through `Party::tryGrantInventoryItem`; MAW's `evt.Add` put them in hand. Asked 2026-11-09.
- **Dimension maps open only MM6-MM8 dungeons**: `data/dimension_maps.yml` `dungeons` lists map ids 1-186, so the
  Hag's maps, like the Oracle's, open completed MM6-MM8 dungeons. MM9 dungeons in the pool would need MM9 families for
  the opened maps (MAW's lists are MM6-MM8 rows, whose art MM9's world may not carry) and a check of the travel
  between worlds. Not done.
- Map resets need no NPC: the dungeon entry dialog offers MAW's reset, and MM9's entrances use it (not tried in play).
  MM9's refills (600, 300 and 150 days) match MM6-MM8's (672, 336, 168); MAW reads both alike.
- **Ideas** (MM9_BALANCE_DESIGN.md section 8): family swaps per map, maps tagged by role (story, promotions, side).

## Tools for testers

- Debug console `actor remaining`: the living monsters the map's progress still counts, nearest first, with where
  they stand and their HP ("hidden" for the invisible ones counted apart). `player sheet`: each member's level, Might,
  Fangs and Dragon Ability, and the sheet's attack and damage rows.
- `tools/maw/mm9_balance.py --review <file> --levels`: the testers' page of MAW's MM9 numbers; `--check` before a
  commit. `tools/maw/mm9_pack_reserve.py <stem>` after an MM9 map is reconverted.
