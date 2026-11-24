# MX: MAW in Xeen

Started 2026-11-21 by the fourth Xeen orchestrator (session openyamm-65) at the user's word: "work on MAW scaling for
the world of xeen now. including the "conjoined" promotions for the classes - e.g. check the MM9 what it does for the
classes. and document it I guess in the MAW html page we have and then "refresh" the MAW html we have on the server."

## Owns

- `devdocs/maw/XEEN_SUPPORT.md` (the design, its questions D-1..D-8, what is built).
- `assets_dev/engine/rulesets/maw/worlds/xeen/` (`balance.yml` by hand; `item_bases.yml`, `new_game_continents.yml`
  written by the tool).
- The `xeen` columns and Xeen `mid` bits of `rulesets/maw/data/promotions.yml`; `xeen` in `ruleset.yml` `worlds` and
  its `world: xeen` card entry; the Xeen line of `data/texts.yml` Level.
- `tools/maw/xeen_*` (`xeen_balance.py`, `xeen_pack_reserve.py`) and the shared reserve core `tools/maw/pack_reserve.py`
  (`mm9_pack_reserve.py` runs on it; MM9's output must stay byte-identical).
- MAW's Xeen overlays: `rulesets/maw/maps/xeen_*_zz_maw.scene.yml` (the pack reserves; Vertigo's pedestal is the world's own since 2026-11-21),
  `rulesets/maw/events/maps/xeen_*_maw.lua`, `rulesets/maw/worlds/xeen/npc_seers_patch.txt`.
- `tools/maw_site/` changes for Xeen (the MAW guide's Xeen continent and section).
- The engine code for MAW's fifth world (see XEEN_SUPPORT.md section 10) and its tests
  (`tests/scenarios/xeen/maw_new_game.yml`, the Xeen cases in MawClassTests, MawMonsterLevelTests, RulesetTests).

Never touches: Xeen's world files (`world.yml`, `source/`, generated `data_tables/`, quest files), `tools/xeen/`,
`tools/mm9_site/`, `tools/xeen_site/`.

## Read first

`devdocs/maw/XEEN_SUPPORT.md`, `devdocs/maw/MM9_SUPPORT.md`, `devdocs/maw/MM9_BALANCE_DESIGN.md` §7-9,
`tools/maw_site/README.md`, `devdocs/xeen/QUESTS.md` §3, `devdocs/xeen/DECISIONS.md` (D-44, D-80, U-1).

## State

Session 1 (2026-11-21): design, the fifth bank (SaveVersion 200), Xeen's promotions as a fifth world, `balance.yml`
v1, gem gear, MAW's Xeen card, the Progress tab's Xeen card, the Level popup (merge point 37, released 18:35:58); MAW
guide's Xeen continent and section.

Session 2 (2026-11-21, after D-84 and U-4): all of D-84 built, no engine change (no merge point). `balance.yml`
version 2 (one-native bands, X7's natives, `density`); gem gear on Xeen's tiers; `xeen_balance.py --review` route
check and D-G list, `--check` of the reserves; the reserve tool generalised (`pack_reserve.py`; MM9's 28 reserves
byte-identical) and 48 Xeen reserves (15 Cloudside dungeons on spawn points use MAW's group sizes instead); Vertigo's
MAW-only pedestal; the Seers Zephyra (X4) and Madame Oorla (D1); three new scenarios; XEEN_SUPPORT.md (sections 2, 3,
4, 6, 7, 9, 11, "Decided by the user"); the guide's Xeen section, deployed.

## Next

- After any rebuild of an indoor Xeen map: `python3 tools/maw/xeen_pack_reserve.py <stem>` and
  `xeen_balance.py --check` (map lanes do it; MX checks at phase 7).
- At the next engine build (A1 or MX): the stale-reserve log line in `game/maps/IndoorSceneYml.cpp` names
  `mm9_pack_reserve.py`; make it name the world's tool (the file has another session's uncommitted diff: not touched).
- Xeen's promotion playthrough and an act of the main chain under MAW; tester feedback on bands v2 and the reserves.

## Log

- 2026-11-21 session 1: XEEN_SUPPORT.md; `xeen_balance.py`; `balance.yml` v1; promotions.yml `xeen`; engine (MawGameState
  five banks, SaveVersionMawXeenBank 200, MawPromotionKind::xeen, MawProgress Xeen card, Level popup, `ruleset banks`
  fifth value, scenario `ruleset_banks.xeen`, test parties' fifth bank, shopRerollCost for Xeen houses, the Warzone in
  `mawArenaMap`, a ruleset's replace of a world's `new_game_continents`); unit tests (15 focused cases, 72 in the four
  files) pass; scenario `tests/scenarios/xeen/maw_new_game.yml` passes; `ruleset maplevels`: Xeen 82 maps, free 4-85,
  horizontal 4-204 (MM6-MM9: 88-100 and 211-241); isolated X4 run under MAW Nightmare: 164 counted monsters
  (`output/xeen_mx/s1/maw_x4_small.png`). MAW on MM6-MM9 unchanged: `maw_test_parties`, `maw_classes`,
  `mm9/maw_density`, `mm9/maw_jarl_bounty_and_hag` pass; `mm9_balance.py --check` passes.
- 2026-11-21 session 2: D-84 MX-8 (`balance.yml` v2: 34 bands moved, X7 natives; `ruleset maplevels` before/after:
  Castle Xeen 44 -> 53, DD-14 34 -> 41, DD-17 51 -> 62, FD-01 61 -> 74, Dragon Cave 67 -> 80; MM6-MM9's 237 rows
  identical), MX-6 (gem gear rungs 4.75/5.375/5.375/6 at 1.1/1.1/1.1/1.15), MX-3 (`--review` D-G list, 40 rows),
  route check (3 maps flagged). MX-4: `pack_reserve.py`, `mm9_pack_reserve.py` on it (28 MM9 overlays identical to
  the original tool's and to the installed ones), `xeen_pack_reserve.py`, Xeen `density`, 48 reserves; scenario
  `xeen/maw_density.yml`; capture `output/xeen_mx/s2/tour_dd02_grid.jpg`. Vertigo pedestal (overlay + event 1777),
  scenario `xeen/maw_vertigo_teleporter.yml`, capture `tour_x1.jpg`. MX-7: Seers patch + `Global_maw.lua` slots
  guarded by `evt.GetNPCTopic`; scenario `xeen/maw_seers_and_bounties.yml`. Guide rebuilt and deployed (live checked).
  Scenarios passing on build-xeen (mp37): the three new ones, `xeen/maw_new_game`, `rulesets/maw_dimension_maps`,
  `rulesets/maw_bounty`, `dimensional_travel_pedestals`, `mm9/maw_jarl_bounty_and_hag`, `mm9/maw_density`, `rulesets/maw_dimension_map_repeat`, `mm9/maw_hag_repeats_dimension_map`;
  `mm9_balance.py --check` and `xeen_balance.py --check` pass.
- 2026-11-21 (A5's Vertigo pedestal session): MX-6's MAW-only pedestal moved to the world, every ruleset (`worlds/xeen/maps/xeen_x1_dimensional_travel.scene.yml`, `worlds/xeen/events/maps/xeen_x1_dimensional_travel.lua`); `rulesets/maw/maps/xeen_x1_zz_maw.scene.yml` and `rulesets/maw/events/maps/xeen_x1_maw.lua` deleted; `xeen/maw_vertigo_teleporter.yml` replaced by `xeen/dimensional_travel_vertigo.yml` (Standard + MAW); XEEN_SUPPORT.md section 7 and the MAW guide's Xeen page updated, guide rebuilt and deployed.
- 2026-11-23 (agent:xeen-mx-ranged; Discord, gryz.mahlay and Tyrkys; OY-657 is the same cause): MAW Hell's ranged
  melee monsters. (1) **Starting maps in every world**: the list of maps where Hell's melee monsters gain no ranged
  attack is data, not code: `rulesets/maw/data/map_levels.yml` `ranged_free_maps` (MAW's six: out01, out02, 7out01,
  7out02, oute3, outd3) and a world balance file's `ranged_free: true` (Xeen `balance.yml` v3: X1 Vertigo, the
  player's "maybe Vertigo might be enough"; MM9 `balance.yml` v3: Bootcamp and the Isle of Ashes, MM9's start and
  its start island, both already `madness_start`); `MawMapLevels::isRangedFreeMap`, `gainsHellRangedAttack` without
  its hard-coded array. (2) **Mixed, not archers** (shared AI, every world): `chooseCombatAbility` turned a rolled
  blow into the missile attack 2 whenever the target was out of reach, so a melee monster with a missile attack 2
  (MAW's Hell arrow, MM6's goblins, the Inferno Bat) shot at nearly every decision; and the roll was made again every
  128th of a second, so a monster walking in stopped to shoot as soon as its recovery ended. Now the blow stays a blow
  (attack 2 by its chance, as the original's ability roll; a missile attack 1 still replaces a blow out of reach), and
  a pursuit under way keeps the roll it began with (`AI_AttackOrPursue`: the count before the stored one; the original
  decides when an action ends). Ranged-only monsters unchanged (their every roll is a missile); melee monsters with
  spells now cast only when a decision rolls the spell, not at each recovery while closing in. Scenarios (new):
  `xeen/maw_hell_mixed_monsters.yml` (X2 street, MAW Hell, Giant/Swamp Toad, Skeleton, Skeleton Lord from 2,800: all
  strike by 5.5 s; before: the Giant Toad at 13 s, the Skeleton Lord not within 15 s), `mm6/goblins_mixed_close_in.yml`
  (Standard, MM6's three goblins from 1,500 strike by 8.4 s and the Goblin Lord still shoots; before: two not within
  12 s), `mm8/skeleton_archers_keep_range.yml` (ranged only: shoot and circle, never melee; unchanged). Unit tests:
  `MawGapTests` (the six, X1, Bootcamp, Isle of Ashes exempt; out05/X2 not; indoors not), two
  `GameplayActorAiSystemTests` cases. Built and tested in `build-mx` (not build/build-xeen).

- 2026-11-24, P3 feedback agent `xeen-fb3-engine` (F56, XD-21 p2 "no boss in MAW"): no change. MAW names bosses only
  on maps with more than 30 monsters (`ceil((n - 30) / 150)`, C-tier); Xeen's authored boss rows never become MAW
  bosses (§3). A decider kept MAW's rule (option a); if more players ask, option b (Xeen's unscripted authored bosses
  as MAW bosses) is this lane's.
