# MAW audit 2026-10-24: verification and plan

Verification of [AUDIT_20261024.md](AUDIT_20261024.md) against the working tree (MAW source: /home/pjasicek/github/Maw-Mod-MMMerge at `ef23ee17`; `reference/Maw-Mod-MMMerge` is an older clone without `Modules/MawCore` and with different formulas, so do not audit against it), done later the same evening after
the combat log and bag work had landed. Every P1 and P2 finding was traced again on both sides (MAW `ef23ee17` and our
code); P3 rows were not re-checked. Nothing in the code was changed by this check.

## Verification results

### P1 (all confirmed)

| Id | Result | Current evidence |
|---|---|---|
| DAT-1 | confirmed, the only gap | `GameDataLoader::loadMapStats` (`GameDataLoader.cpp:2413`) reads `map_stats.txt` directly. Every other table `ruleset.yml` patches goes through `loadTextTableRows` / `loadFirstTextTableRows`, which apply the ruleset |
| ITM-1 | confirmed | `writeIndoorHeldItemPayload` (`IndoorWorldRuntime.cpp:3490`) keeps the 0x24-byte MM record; outdoors keeps the whole `InventoryItem` |
| CNT-1 | confirmed | `Global_maw.lua:451/503` register 65310/65311; `Global_mmmerge_crystals.lua:4-5` owns them; `registerGlobalHook` calls `replaceGlobalEvent` silently |
| SPL-1 | confirmed | `GameplayActorService::resolveDirectSpellImpact` recomputes `currentHp × (0.25 + 0.02 × skill)` for Mass Distortion and ignores the `baseDamage` MAW computed |
| CLS-1 | confirmed | MAW: `SPStats = 2` for every caster (`zzMaw-Items.lua:4427-4433`) plus `addMana` adds the Personality effect again (`:3131-3145`); ours `MawClassRules::baseMaxSpellPoints` adds the class stat plus Personality. DEVIATIONS 25 is wrong |
| MON-3 | confirmed | `MawGameState::completedMaps` is only ever inserted into (`MawExperienceRules.cpp:200`); it gates the HUD, the Nightmare save cost and `mapResetOffer` |

### P2

Confirmed, no decision needed: MON-2, MON-4, MON-5, CNT-2, CMB-1 (wider than reported: also the Elemental and Undead
Slaying special enchants; narrower for bows: indoor arrows always pass 1), CMB-2, CMB-4, ITM-L2, ITM-2, ITM-A1, FITM-2-1,
FITM-2-2, FCOR-2-1, FCOR-2-81, CLS-2, CLS-3, SKL-1 + FSPS-2-2, SKL-2, SPL-3 (fix must keep the power out of the
resistance bonus), SPL-4, SPL-5, SPL-6, SPL-7 (now proven, not "plausible": the engine heal keys on object spell 111,
which MAW swaps to 200), SPL-8, CHM-1, ALC-4, STD3-2, FSPS-2-1 (MAW also skips the hour check indoors), STD3-1, STD2-3,
STD2-4, STD3-4, STD4-2-1, STD4-2-2, ROB-2-1, ROB-2-5.

Partly, or needs a decision: MON-1, MON-6 (FMON-2-5), OVR2-2-1, FMON-2-1, SPL-9, DAT-3, STD3-3, STD1-1, STD3-6, STD2-2,
STD2-1, STD2-M2, STD4-2-4, STD4-2-5. See the decision list below.

Closed: STD2-M1 (GAPS H.3 records the user's decision: the docked log on by default with a setting to turn it off).

### Where the audit was wrong or is stale

- FMON-2-1 overstates the effect: under MAW's default M&M6 Projectiles the elemental missiles never reach the engine
  roll, so only Arrow (545) and Body/Mind/Spirit (520-530) take two rolls.
- MON-1: Nightmare/Doom risen monsters give full experience by accident (a reload recomputes `facts.experience`), which
  is what MAW effectively does too; only the Road to Insanity / Beyond Madness zero is broken.
- STD3-6: HEAD already found the MM6 face by index; the real changes are lost swaps in saves from HEAD and the MM7/MM8
  stray-face fix.
- SKL-1 and SKL-2 are Standard bugs too: OpenEnroth keeps negative HP on heal and counts permanent stat bonuses in max
  HP, so the fix belongs in the shared code.
- SPL-8: our flat five-wisp cap is probably a Standard deviation as well (OpenEnroth caps 1/3/5 by mastery); check
  the MM8 executable before changing Standard.
- Docs marked done but broken: GAPS N8.3 (d22), L4.1 (Legendary 11), L6.3 (Assassin Mass Distortion), L5.6 (staff
  resistance base), A2.4 (artifact 507), L5.5 (Immolation, see SPL-9), H.8 (lists done work as open). DEVIATIONS 9, 25,
  31 and 48 describe behaviour we do not have.

## Decisions for the user

Approved as recommended by the user on 2026-10-24 (D15: move the rulesets into the engine package).

| # | Question | Recommendation |
|---|---|---|
| D1 | MON-1: risen monsters' experience in Nightmare/Doom | Keep full (matches MAW in practice), record a row; give none in Road to Insanity / Beyond Madness |
| D2 | OVR2-2-1 + FMON-2-1: MAW's "M&M6 Projectiles" (elemental monster missiles: no special attack, no Pain Reflection, random conscious target; arrows and Body/Mind/Spirit roll Speed twice) | Copy MAW: it is on by default and its balance model assumes it |
| D3 | SPL-9: Immolation burns with the full dice (ours, MAW's tooltip) or the flat part only (MAW in practice, a bug) | Keep the full dice, add a DEVIATIONS row |
| D4 | DAT-3: Standard's raised spellbook weights carried into MAW | Force MAW's values in the MAW ruleset |
| D5 | MON-6: affix 12 resistance for unnamed monsters only, as MAW | Copy MAW |
| D6 | ROB-2-1: training stops at level 1063 (32-bit experience) | Widen experience to 64 bits with a save migration |
| D7 | SKL-1, SKL-2: heals from negative HP and black-potion stats in max HP/SP, shared code (changes Standard) | Fix in the shared code: original and OpenEnroth behaviour |
| D8 | CMB-1 side issue: Standard indoor arrows ignore the ×2 against a monster kind | Fix in Standard (outdoor already doubles) |
| D9 | STD1-1: MM9 Dragon King spawns with full HP indoors | Accept as a fix (outdoors already did) |
| D10 | STD3-6: MM6 `SetTexture` | Accept, and add the save migration for MM6 saves from HEAD |
| D11 | STD3-3: refused projectile hits report 0 damage | Accept as a fix |
| D12 | STD2-2: Enter / Shift+Enter / Delete on the Standard Alchemy bench | Keep, note it in L7.4 |
| D13 | STD2-1: once-per-character potion text | Restore HEAD's text in Standard |
| D14 | STD2-M2: All / Standard / MAW filter on Load/Save | Show it only when saves of two rulesets exist; cache the definitions |
| D15 | STD4-2-1: v1.8-v1.10 cannot self-update to a release with the `rulesets` pack. Their manifest parser rejects any pack outside `/engine` and `/worlds/<package>`, and their app install checks that every pack the new `index.json` names was downloaded and has a valid mount (`v1.10:engine/update/AppUpdater.cpp:698-704`). So a pack hidden from old clients under a new manifest key would still fail at the index check, and a bridge release strands every client that has not taken it before MAW ships | Move the rulesets into the engine package: `assets_dev/engine/rulesets/<id>/`, packed as `engine` packs mounted at `/engine/rulesets/<id>`, which every released updater accepts. Code: the `rulesets/` root in `RulesetDefinition`, `AssetFileSystem`, `AssetPackIndex` and the packaging tools; the saves' required-package key `rulesets/<id>` stays as a name. About half a day, plus an old-parser test in `test_publish_release.py`. The alternative, a new "optional packs" key in both the manifest and `index.json` that new clients fetch on start, keeps rulesets a top-level package for future mods but changes the update protocol |
| D16 | STD4-2-4: combat log over the Android touch controls | Default off on Android; place the toggle clear of the flight panel |
| D17 | STD4-2-5: "Item rarity glow" in Standard games | Hide the row in Standard games, keep it in the main menu |

## P3 questions

The P3 rows that ask the user something; all approved as recommended by the user on 2026-10-24:

| # | Id | Question | Recommendation |
|---|---|---|---|
| Q1 | SPL-16 | Town Portal near enemies in Nightmare/Doom: MAW means to block it, but a typo leaves only Lloyd's Beacon blocked | Keep our block (MAW's intent), row |
| Q2 | FSPS-2-9 | Solo Knight Charge: in MAW it never comes off its 25 s cooldown (dead ability) | Keep our working 25 s cooldown, correct DEVIATIONS 48 |
| Q3 | FITM-2-6 | Poison duration: MAW re-registers its handler on every map load, so poisonings soon last 50 s | Keep the written 25 s, +5 per repeat, cap 50; row |
| Q4 | CMB-20 | Cover against a monster's second spell needs only Expert in MAW (Master for the first) | Keep Master for both; row |
| Q5 | FCOR-2-3 | Boss on-hit affixes (poison, summon, swap, pull) still fire on a dodged hit in MAW | Keep: a dodged hit carries nothing; row |
| Q6 | FCOR-2-61 | Dimension maps in Road to Insanity / Beyond Madness: MAW never refills the target, so it stays empty | Keep our refill; row |
| Q7 | OVR1-2-2 | MAW lost MMMerge's off-hand dagger fix: Dagger 64+ dual-wields at Normal | Keep Expert required; row |
| Q8 | OVR2-2-5 | Road to Insanity: MAW withholds a finished bounty while another town's is open | Keep paying at once; row |
| Q9 | FMON-2-11 | Goblin King / Lieutenant fall on MAW's boss and risen id boundaries (random boss, counts as slain) | Keep plain named monsters; row |
| Q10 | CHM-3 | Road to Insanity held-back food: MAW keeps only the last dungeon's excess | Keep adding up; row |
| Q11 | CMB-12 | Weak dragons' bite halved, dragon bite SP no longer lowers SP above the cap (MAW bugs we fixed) | Keep the fixes; row |
| Q12 | CLS (quirk) | Death Knight quick-cast toggles store the wrong value in MAW | Keep the fix; row |
| Q13 | ITM-A5 | Medusa's Mirror gives no stone immunity in either ruleset (MAW and MMMerge both give it) | Add the immunity in both rulesets (changes Standard) |
| Q14 | ITM-L7 | Legendary 30: MAW's code takes max(HP, SP) × efficiency, its text says only SP is multiplied | Follow MAW's code (how it plays), fix the text |
| Q15 | ITM-L8 | Legendary 28: the text says armour AC "doubled", the code gives ×1.5 | Keep ×1.5 (how it plays), fix the text |
| Q16 | MON-17 | 7d24/7d37 item scripts: MAW's level includes resets, Madness and dimension power | Include those three terms; leave out MAW's horizontal-progression side effect; row |
| Q17 | CNT-10 | Road to Insanity trade-goods list ports MAW's typo (Tularean Wood keeps selling) | Fix the typo; row |
| Q18 | FMON-2-12 | MAW's safety nets for monsters pushed out of the map or into walls | Check in play; clamp pushes and swaps only if they can strand a monster |
| Q19 | CHM note | DEVIATIONS 1 (Normal plays bolster 70) also makes real-time poison ×0.7 instead of MAW's ×0.5 | Say so in DEVIATIONS 1 |

The other P3 rows are fixes without a question; each stream takes its area's P3 fixes after its P1 and P2 rows.

## Plan

Three streams, split by the files they touch so sessions do not collide. Within a stream, P1 first, then the P2 rows,
each with a unit test or a scenario assertion, then the doc rows it corrects.

### Stream 1: data, engine, saves and release

1. DAT-1: apply the ruleset in `loadMapStats`, and add a loader test that loads each table `ruleset.yml` names and
   checks one patched cell, so a contribution no loader reads fails.
2. CNT-1: move the two MAW hooks to a free MAW event range, and make `replaceGlobalEvent` refuse (log an error) to
   overwrite an event another file registered, unless it is an explicit override.
3. ITM-1: keep an `InventoryItem` beside each indoor sprite object that carries an item, save it, and fall back to
   the raw record only for map-authored items. Covers wand charges too. (L)
4. STD3-1: validate packages and schemas before tearing the session down; after a failure that follows the teardown,
   return to the main menu.
5. STD4-2-2: add `SceneOverlayOperations.cpp` to the editor sources.
6. STD4-2-1 (after D15), ROB-2-1 (after D6), STD3-6 migration (D10).
7. Standard UI: STD2-3 (clear hover text when the utility overlay closes), STD2-4 (cures skip Dead, Eradicated, Stoned),
   STD2-1 (D13), STD2-M2 (D14), STD4-2-4 (D16), STD4-2-5 (D17).

### Stream 2: combat and spells (MawCombatRules, MawSpellRules, PartySpellSystem, Party)

1. SPL-1: the actor service uses the damage it is given; Standard's formula moves into `CombatRules::spellDamageOnTarget`.
2. CLS-1: Personality twice, no Intellect; re-run `MawBalanceModelTests` and the golden data; fix TXT-2 Personality
   text and DEVIATIONS 25.
3. CMB-1 (kind multiplier through a rules hook; D8), CMB-2, CMB-4, ITM-L2 (stage order), FCOR-2-1, CLS-2, CLS-3, SPL-7,
   STD3-4.
4. SPL-3 (fix DEVIATIONS 31), SPL-4, SPL-5, SPL-6, SPL-8, SPL-9 (D3), FSPS-2-1, SKL-1 + FSPS-2-2 and SKL-2 (D7), STD3-2.
5. OVR2-2-1 + FMON-2-1 (D2).

### Stream 3: monsters, items and content (MawMonsterRules, MawExperienceRules, MawItemRules, MAW Lua)

1. MON-3: a per-visit "cleared since the last refill" flag (a map variable a refill wipes) for the HUD, the save cost
   and the reset offer; `completedMaps` keeps the one-time reward and the dimension pool.
2. MON-1 (D1), MON-2, MON-4, MON-5, MON-6 (D5), FITM-2-1, FCOR-2-81, CNT-2, CHM-1, ALC-4, DAT-3 (D4).
3. ITM-2, ITM-A1, FITM-2-2.
4. ROB-2-5: profile first, then one shared actor pass per frame and auras on the 0.5 s tick.

### Then

- Correct the docs listed above (GAPS N8.3, L4.1, L6.3, L5.6, A2.4, L5.5, H.8; DEVIATIONS 9, 25, 31, 48).
- Full unit suite and all ruleset scenarios, plus the Standard-versus-HEAD scenario comparison the audit used.
- P3: re-check and triage in a second pass by area (many are one-line fixes; the questions among them go to the user
  in one list).

Sizes: stream 1 is about a day (ITM-1 is most of it), streams 2 and 3 about a day each.

## Progress (stream 1, 2026-10-25)

Done, each with a test: the ruleset move (D15: `engine/rulesets/<id>`, `/engine/rulesets` mount, publish-time check
for old updaters), DAT-1 (`loadMapStats` applies the ruleset; a loader test checks every contribution is applied),
CNT-1 (MAW hooks on 65400/65401; global hooks and on-load events refuse an id another event holds), STD4-2-2 (editor
links), ROB-2-8 (fixed scenario root seed), ROB-2-1 (64-bit experience, save 115; Standard cap 4 billion, MAW 10^18),
D10 (MM6 SetTexture keys migrated for saves before 115), STD3-1 (package schemas checked before a ruleset switch;
a failure after it opens the main menu; no automated test), STD2-3 (utility overlay clears its hover text), D13
(`PotionRules::noBenefitText`), D14 (Load/Save filters from the saves' rulesets), D16 (combat log off on Android,
Android positions in `touch_controls.yml`; not captured on a device), D17 (`game_ruleset: maw` hides the rarity
glow row in other games' pause menus), ITM-1 (indoor floor items keep the whole `InventoryItem`, save 116), Q19 and
the N8.6 record of the approved Standard changes. STD2-4 moved to stream 2.

P3 (stream 1): DAT-4 (MAW's collision shrink as `content/monster_descriptors_patch.txt`, following its comment for the
MM6 minotaurs; DEVIATIONS 142), DAT-5 (unidentified names of 67 and 804), DAT-6 (`appendTableColumns` refuses cells
past the header), DAT-7 (MAW texts reset with the other MAW data), STD2-U1 (skill popup title from the rules' name,
not the row label with its mastery), STD2-U2 (no "Power: 0" on Standard potions), STD2-M3 (Standard creation popups
back to their old height). Open for the user: STD2-U3, U4, U5 / STD1-4 (Standard layout changes made for MAW's long
names and effects).

## Progress (stream 2 P3, 2026-10-25)

Done, each with a test in `tests/MawAuditCombatSpellTests.cpp` unless noted:

- Spells: SPL-10 (Turn/Control Undead on the living record no diminishing returns), SPL-11, SPL-12, SPL-13 (Spirit
  Lash 384 at Master), SPL-15 (Raise Dead lifts Eradication at Grandmaster only), SPL-17 (weak potion auras show
  skill 0), SPL-18 (MAW's quick-cast crowd control takes the visible hostile within 4800 whose debuff ends soonest,
  `PartySpellSystem::quickCastActorTarget`; no-target case DEVIATIONS 155), FSPS-2-3 (heal scrolls heal the engine's
  amount, Shared Life MAW's table at the scroll's skill), FSPS-2-4 (Invisibility, Fly and Shrinking Ray texts),
  FSPS-2-5 (crowd-control and Elementalist costs cap at 65000), FSPS-2-7 (a released Preservation aura ends for
  members without the potion), FSPS-2-8 / TXT-2-1 (Armsmaster lines), FSPS-2-10 (monster missile homing re-acquires;
  Meteor Shower, Sparks, Starburst, Poison Spray, Ice Blast and Shrapmetal never home). SPL-14 and FSPS-2-11 were
  done in stream 3 (7d11 Wall of Mist, `prepareRosterCharacter`).
- Combat: CMB-6 (affix 26 inside `mawCharacterAttackDelay`), CMB-8 (flat class cut by the party's model), CMB-11
  (breath: mean of two rolls, Legendary 14's crit), CMB-13 (Seraph heal and leech floor read the sheet's Speed and
  Personality), CMB-14 (hazards take Legendary 18/22 and affix 2), CMB-15 (affix 32 spares the leech floor), CMB-16
  (Weak and Carnage scale only the shot's own roll; `CombatRules::callerHalvesWeakMissile`), CMB-18 / ITM-A6
  (artifact on-hit at the hands' pace), CMB-19 (Subtlety in every reader of the attack delay), CMB-21 (Shield does not
  halve MAW arrows; `monsterShieldHalvesPartyMissile`), CMB-22 (Souldrinker's tenth for vampires only), ITM-A7
  (artifact on-hit in its own "artifact-on-hit" stage, by kind; Earth, Mind and Spirit artifacts no longer dropped),
  ITM-A8 (Ethric's Staff spares the Lich class only), ITM-A9 (Horn of Ros and Ghost Ring buffs refreshed each tick at
  Master). Recorded instead: CMB-9's Thorn/Reflecting amount (DEVIATIONS 174), CMB-17 (DEVIATIONS 44). CMB-12, CMB-20
  and CMB-23 were done before (DEVIATIONS 148, 146; P2).
- Class and core: FCOR-2-5 (Elementalists learn from any element spell on a hostile monster; DEVIATIONS 177 for
  zero-damage hits), FCOR-2-6 (a Regenerating boss's party hits saved with the actor, SaveVersion 119), FCOR-2-20 (the
  Elementalist idle window from the last offensive cast; `baseRecoveryTicks` has no side effect), FCOR-2-21
  (Assassins pay and build only on hostile targets), FCOR-2-60 (regeneration specials' 1 % per 5-minute tick).
  Recorded instead: FCOR-2-2 (DEVIATIONS 175), FCOR-2-41 (DEVIATIONS 176). FCOR-2-40 and FCOR-2-82 were done in
  stream 3.
- Skills, texts, robustness: SKL-3 (Supreme Armsmaster damage from the effective level), SKL-4 (mercenary gear plain),
  SKL-5 (scenario-only, GAPS L5.2), SKL-7 (broken weapons and armour ignored by the delay and impairment), TXT-2-2,
  2-3, 2-5, 2-6, 2-7, 2-9, 2-10, 2-11 (popups: GM Bow and Unarmed lines, per-use Ascension rows, Meditation after the
  reservation and Legendary 20, the held weapon's paralyse chance, bolster levels, the SP regeneration wording, the
  class schools' live numbers and Grandmaster Dodging's chance; tests here and in `MawSkillTests`), TXT-2-8 (with
  CLS-1), TXT-2-12 (with CLS-2: both read the trained level), ROB-2-6 (the balance model caches whole levels only),
  ROB-2-10 (a malformed text placeholder stays as written). The staff party resistance reads MAW's skillResistance
  row, whose numbers equal the StaffArmor row: no change.
- For stream 3 in the shared files: ITM-A3 (rings and amulets in the armour breakdown), CHM-2 (the madness ledger marks
  every hit that lands), ROB-2-3, FITM-2-7.

## State at the end of the audit work (2026-10-25)

All three streams are done. Every P1, P2 and assigned P3 row is fixed with a test, recorded in DEVIATIONS.md or left
open below. Check on the combined tree: unit suite 2193/2199 (the six known asset failures: darkmoor previews, flour
sack, mm8 slime/Ogre/Vampire bindings, demon LOD); scenarios 44/58, all ruleset scenarios passing, the 14 failures
being the MM6 story scenarios that fail at HEAD too; packaging tests pass; the editor links. Saves are at version 119.

Waiting for the user:
- STD2-U3, U4, U5 / STD1-4: Standard layout changes made for MAW's long names and effect lists.
- The Standard Summon Wisp cap (flat 5 against the original's per-mastery limit), once stream 2's MM8 check is in.
- Judgment rows to confirm: DEVIATIONS 151, 154, 156, 157, 159, 160, 164, 170 (stream 3) and 155, 174-177
  (stream 2).

Open:
- GAPS H.10: MAW's crafting bag (Shift+B pickup routing).
- GAPS H.11: bounty presentation (map note on the target, the boss's name in the bounty texts).
- No scenario covers FMON-2-2 (scenarios cannot make an actor a party ally) or STD3-1 (a failed cross-ruleset load);
  D16's Android placement is not captured on a device.

## User decisions of 2026-10-25

All recommendations accepted: STD2-U3 and U5 kept, U4 shrinks to fit at 145; the judgment rows kept; Standard's
Summon Wisp follows MM8 (1/3/5 per caster by mastery, refused at the limit without spending SP; stream 2). New work:
the MAW inventory shows all four bags at once at half size with dividers, 1-4 zoom one bag (stream 2); MAW bounty
presentation (H.11, stream 3); a scenario step for party allies (FMON-2-2, stream 3); `save_game` /
`load_game: expect_failure` for STD3-1 (`cross_ruleset_load_failure.yml`, done); no combat log on Android (done:
setting hidden, never read from the ini, Android layout overrides removed); a review of MAW's interface changes
(spellbook, quick-cast slots and the rest) against ours.
