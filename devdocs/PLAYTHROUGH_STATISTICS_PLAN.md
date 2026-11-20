# Playthrough statistics

Reference for the playthrough statistics as built (2026-11-07). The file keeps its original name because code
comments and other records link to it. Mockups and the design study:
[level_generation/ui/playthrough_stats_20261107/](../level_generation/ui/playthrough_stats_20261107/README.md).

A read-only Statistics page shows one playthrough's time played, kills, deaths, experience, damage, travel, gold,
saves and loads. Every counter is kept twice:

- **Timeline:** inside each save. Loading restores it, so a quickload never counts a replayed fight twice.
- **Lifetime:** in a sidecar file per playthrough. It counts everything, including play later undone by loading, and
  never rolls back.

Both copies are sealed: encrypted and authenticated, so they cannot be edited outside the game. The screen flags
playthroughs helped by development options or the debug console.

## Contents

- [What a playthrough is](#what-a-playthrough-is)
- [The two copies](#the-two-copies)
- [Files and writing](#files-and-writing)
- [Code](#code)
- [Where each statistic is counted](#where-each-statistic-is-counted)
- [Time and sessions](#time-and-sessions)
- [The screen](#the-screen)
- [Saves by playthrough](#saves-by-playthrough)
- [Sealed files](#sealed-files)
- [Integrity flags](#integrity-flags)
- [Release key](#release-key)
- [Limits](#limits)
- [Tests](#tests)
- [Not done](#not-done)

## What a playthrough is

A playthrough starts when a new party is created and includes every save made from it, on any branch.

- **Id.** `GameSaveData::playthroughId`: 128 random bits as 32 hex digits.
  - `PlaythroughStatistics::beginNewPlaythrough` makes it. It is called from
    `GameApplication::startNewSessionFromCharacterCreation` and from the debug roster start `startNewSession`.
  - `GameSession::buildSaveData` writes it into every save.
- **Saves from before statistics** have no id. Their id is `legacy-<random root seed in hex>`: `randomRootSeed` is set
  once per party and copied into every later save. All older saves of one party therefore share one record. The id
  is written into the next save.
- **A save with neither an id nor a seed** gets a new random id.

## The two copies

`PlaythroughCounters` holds every counter. `PlaythroughStatistics` keeps two of them, and every `record*` call adds to
both.

| Shown as the main number | Copy |
| --- | --- |
| Kills, damage, largest hit, spells, experience, levels, travel, maps, chests, gold, artifacts, the Party tab | Timeline |
| Real time played, turn-based time, sessions, saves, loads, loads after a wipe | Lifetime (real time spent cannot be undone) |
| Deaths, eradications, party wipes, temple healings, the Party tab's knocked out and deaths | Lifetime (players reload after exactly these, and MM9's early game over reloads the autosave itself) |
| Game time | The current world clock |

- **Breakdowns.** Each timeline statistic's breakdown ends with "Including undone play: N", from the lifetime. The
  losses' breakdowns are built from the lifetime and end with "In this timeline: N" instead.
- **Undone by loading.** The Time breakdown shows lifetime real time minus timeline real time.
- **Rates per hour** divide timeline results by lifetime time played, so reloading lowers the pace.
- **Another branch.** Loading a save of another branch shows exactly that branch's timeline.
- **A save without a timeline** starts its timeline at zero, marked *partial* with the date tracking began. The
  header then reads "Tracked since …".

Each copy also carries a `PlaythroughTrackingInfo`: the date tracking began, *partial*, a write sequence (see
[Integrity flags](#integrity-flags)) and the integrity flags.

## Files and writing

- **Sidecar.** `saves/playthroughs/<id>.<key version>.oystats` under the user data root, for example
  `9f2c….release-1.oystats` or `9f2c….dev.oystats`. Scenarios write theirs under the scenario's save root.
- **Timeline.** `GameSaveData::playthroughTimeline` in the save. Save version 161
  (`SaveVersionPlaythroughStatistics`) adds it, `playthroughId` and `Character::statsMemberId`.
- **Content.** Both hold sealed YAML. The text inside the seal has these sections:
  - `schema`, `tracking_since_utc`, `partial` and `sequence`;
  - `integrity`: `development_build`, `restored_older`, `unverified` and `assists`. The assists are a map from the
    reason to `{first_utc, first_day, sessions, commands}`.
  - `time`, `saves`, `combat`, `spells`, `experience`, `losses`, `services`, `travel`, `exploration`, `gold`,
    `artifacts_found` and `members`.
  - The sidecar adds `playthrough`, `created_utc`, `last_played_utc` and `start: {world, ruleset, difficulty}`.
- **Writing.** The sidecar is written on a worker thread: a `.tmp` file, then a rename over the old one. The main
  thread only builds and seals the text, which takes microseconds. It is written:
  - at a new game;
  - at every load;
  - after every save;
  - on map change and on a party wipe;
  - when an assist is first used in a session;
  - every 60 s of counted play.

  Returning to the main menu or quitting writes it synchronously (`endPlaythrough`). A crash loses at most a minute.
- **Runtime cost.** A few integer additions per event, one map increment per kill, and one clamped time addition per
  frame. A save grows by a few KB.
- **Edge cases.**
  - *Two games on one playthrough:* the last writer wins.
  - *A missing sidecar:* the lifetime restarts from the save's timeline, marked partial.
  - *Deleted saves:* their sidecar stays behind. It does no harm.

## Code

- `game/party/PlaythroughStatistics.h/.cpp`:
  - the counters and the YAML;
  - `PlaythroughStatistics`, with its record functions, sessions, play time and the sidecar writer thread;
  - the free hooks `recordMonsterDeathStatistics` and `recordChestOpenedStatistics`.
- `game/party/PlaythroughStatisticsTypes.h`: `GoldReason`, `ExperienceReason`, `StatKillMethod`,
  `StatDamageTakenKind` and `StatMemberRef`. It is light enough for `Party.h` to include.
- `game/party/PlaythroughSeal.h/.cpp`: sealing and opening (see [Sealed files](#sealed-files)).
- **Ownership.** `GameSession` owns the instance, and `Party::setStatistics` points a party at it.
  - A copy-constructed party (MAW's equipment trial copies) has no binding, so it never records.
  - Copy-assignment keeps the destination's binding.
  - Bound once each: the session party (`GameSession::setPartyState`, `restoreFromSaveData` and the scene captures),
    the outdoor party runtime (`GameApplication::bindPartyDependencies`) and the indoor party runtime
    (`IndoorSceneRuntime`).
- **Lifecycle** (`GameApplication`):
  - `beginNewPlaythrough` at a new game;
  - `attachLoadedSave` in `quickLoadFromPath`;
  - `recordSave` in `quickSaveToPath`;
  - `endPlaythrough` in `openMainMenuScreen` and `shutdownApplication`;
  - `updatePlaythroughStatistics` every frame: the context (clock, map, world, turn-based), new members, the map
    entered, development options and play time.
- **Gold and experience reasons.**
  - `Party::addGold(int amount, GoldReason reason = Other)`. The game's call sites pass `LootCorpse`, `LootChest`,
    `LootGround`, `Event`, `Sold`, `Shop`, `Training`, `Temple`, `Guild`, `Travel`, `Tavern`, `Bank` or `Defeat`.
    Debug and rare sources (stolen gold returned, fines, hireling wages) stay `Other`. The statistics add up to the
    change in party gold.
  - `Party::addExperienceToMember(index, amount, ExperienceReason = Other)` and `grantSharedExperience`. The amount
    is recorded after the Learning bonus. `grantMonsterKillExperience` sets the reason to `Monster` for everything the
    rules grant for a kill, and `EventRuntime`'s experience variable passes `Event`.
- **Members.** `Character::statsMemberId` is a random 64-bit id, saved with the character. Every frame, a member
  without one gets one (`Party::assignStatsMemberIds`). It stays when a member is dismissed and hired back. The
  record keeps each member's last name and class, so former members can still be listed.

## Where each statistic is counted

| Statistic | Where | Notes |
| --- | --- | --- |
| Kills: total, by monster name, strongest, turn-based | `recordMonsterDeathStatistics`, beside `markRuntimeBountyHuntMonsterKilled` in both worlds' death hooks | Only `killedByParty` deaths. |
| Kill credit: member and method | `GameplayCombatController::handlePartyAttackPresentation` (melee) and `handlePendingCombatEvents` (missiles, spells) | Total minus credited kills shows as *Allies and traps*: allies, traps, Armageddon, the debug `actor kill`. MM9 hirelings count for the party, not a member. |
| Damage dealt, school, crits, largest hits | The same controller sites | Party damage that bypasses the controller (Armageddon, traps) is not counted. |
| Damage taken, kind, largest | `Party::applyDamageToMember` | The controller names a monster hit with `Party::setIncomingDamageSource` just before it, for that hit only. A status text ("falling", "chest trap") counts as the environment. |
| Knocked out, death | `applyDamageToMember` and `adjustMemberHealth` (the change of condition) | The cause is the last thing that hurt the member. |
| Death, eradication, stoning by condition | `Party::applyMemberCondition` when newly applied | |
| Party wipe | `GameApplication::processPendingPartyDefeat` | Gold lost is `GoldReason::Defeat`. Also arms *loads after a wipe*, which a load counts and a save clears. |
| Experience by source, largest award | `addExperienceToMember`, `grantSharedExperience`, `EventRuntime` | |
| Levels gained | `Party::trainActiveMember` | |
| Spells cast, mana, scrolls, healing | `PartySpellSystem::castSpell`, its final success | Members only. The two early successes (MAW scroll buffs and auras) are not counted. |
| Town Portal, Lloyd's Beacon | The same place, by spell id | The destination is the utility text: the location's name. |
| Temple heals, donations | `HouseInteraction` `TempleHeal` and `TempleDonate` | |
| Coach and ship | The `HouseInteraction` transport route; MM9 routes in `GameplayDialogController` | Days include the wait. MM9 routes count as coach trips. |
| Maps visited | `updatePlaythroughStatistics`, when the map changes | A set of file names. |
| Chests opened | Both worlds' `attemptOpenChest` (`recordChestOpenedStatistics`) | A set of `map#chest id`: each chest counts once. |
| Artifacts found | `Party::recordEverOwnedItem`, the first time an Artifact or Relic id is owned | Items already held after a restore or a new party's kit do not count. |
| Saves, loads | `quickSaveToPath`, `quickLoadFromPath` | By path: quick, auto or save slot; quickload or Load screen. |
| Turn-based fights, turns | `TurnBasedCombatRuntime::begin`, `enterAttackStage` | |

## Time and sessions

Real time counts in `updatePlaythroughStatistics` only when all of these hold:
- a map is loaded, with no loading overlay and no menu screen (the pause menu is a menu screen);
- the window has keyboard focus and is not minimized;
- there was player input in the last five minutes.

Each frame adds at most 0.25 s of unscaled time. Overlays such as the inventory, dialogue, shops and the Statistics
page itself do count. Turn-based time is the same time while turn-based mode is on.

A **session** starts at a new game, or when a playthrough is loaded while another one or none was active. Reloading
the same playthrough continues the session.

## The screen

Statistics is the second page of the Quick Reference overlay. The overlay's gating, party basebar and Escape apply
unchanged.

- **State:** `QuickReferenceScreenState {active, page, statisticsPartyTab}`, opened by
  `GameplayScreenRuntime::openQuickReferenceOverlay(QuickReferencePage::Statistics)`.
- **Opening it:**
  - The top bar's fifth icon, `OutdoorButtonStatistics` (the tally scroll, `obsidian_statistics`), sits between
    Party and Rest. The bar is 298 units wide instead of 268.
  - The key `statistics` (`KeyboardAction::Statistics`), F1 by default, is in the Settings keyboard list. The Quick
    Ref and Statistics keys each open their page, and the key of the page shown closes the overlay.
- **Files:**
  - `game/ui/GameplayStatisticsScreen.cpp` draws the page and builds the breakdowns.
  - `assets_dev/engine/ui/gameplay/statistics.yml` holds the root and the Overview, Party and Exit buttons.
  - Input is in `GameplayOverlayInputController::handleQuickReferenceOverlayInput`.
- **Overview.** Seven groups:

  | Group | Rows | Held right-click shows |
  | --- | --- | --- |
  | Time | Played, Game time, Turn-based, Sessions | This, longest and average session; time per world; time in this timeline; time undone by loading |
  | Experience | Earned, Per hour, Levels gained | Monsters, quests and events, other; largest award; including undone play; levels per member |
  | Saves | Saves, Loads | Quicksaves, autosaves, save slots; quickloads, Load screen, after a wipe |
  | Combat | Monsters killed, Kills per hour, Damage dealt, Damage taken, Largest hit, Spells cast | By method and most slain; damage by school with bars; top five hits; most-cast spells, healing |
  | Losses | Deaths, Eradications, Party wipes, Temple healings | By member, deadliest causes, latest deaths; latest wipes and gold lost; temple gold |
  | Exploration | Town Portals, Lloyd's Beacons, Coach and ship, Maps visited, Chests opened | Top destinations; recalls and beacons set; trips, days and gold |
  | Wealth | Gold looted, Gold spent, Artifacts found | By source and items sold; by purpose and banked; the artifacts with their day |

- **Party tab.** One column per current member, at most 100 units wide each. Rows: kills, damage dealt, share,
  largest hit, damage taken, spells cast, healing given, knocked out, deaths and experience. The top value in a row is
  gold, and zero is a dash. One line underneath lists former members and *Allies and traps*.
- **Breakdowns.** Hold the right mouse button on a row; release closes it. `buildBreakdown` turns the row's id into
  lines, drawn in the shared inspect frame and sized to the widest line. The popup sits below the row, else above it,
  else beside its column. The page keeps no state for it: it hit-tests the held pointer while drawing.
- **This session.** The basebar's right panel shows this session's time, kills, experience and deaths.
- **Integrity line.** Between the buttons, in place of the breakdown hint (see [Integrity flags](#integrity-flags)).

## Saves by playthrough

The Load and Save screens (`game/ui/screens/LoadGameScreen.cpp`) list the saves under the playthrough each belongs to.
Design mockup and the user's decisions: 2026-11-12 (grouping, renaming, Delete Playthrough, a Quicksave and Autosave
per playthrough). The Load screen keeps its ruleset filter (All, Standard, MAW): a playthrough is listed under it by
its saves of that ruleset.

- **Grouping.** A heading per playthrough id, then its saves. The playthrough being played is first, the others
  follow by their newest save, and saves that name no playthrough come last as "Older saves". The first heading is
  unfolded; a click unfolds a heading, and a click on the selected one folds it.
- **The id of a save.** From save version 175 the summary block at the front of a save holds the playthrough id and
  the timeline's played seconds (`GameSaveSummary::playthrough`), so the list reads them without the game state.
  - Older saves keep the id behind the game state. They are read whole once, and the result is kept in
    `saves/playthroughs/save_index.tsv` by file name, size and time (`scanSaves`). A save written again drops out of
    the index.
  - A save from before statistics is named by its seed (`PlaythroughStatistics::playthroughIdOfSave`).
- **A heading's facts** come from the playthrough's statistics file, read without attaching to it
  (`PlaythroughStatistics::readStoredSummary`): start world, creation and last play, and the lifetime's played time.
  The rules and difficulty are those of its newest save. The playthrough being played shows the game's own time.
- **Names.** The automatic name is start continent, rules and difficulty ("Enroth · MAW Nightmare"). A name the player
  types is kept in `saves/playthroughs/names.yml` (`game/party/PlaythroughNames.h`), apart from the sealed statistics.
  Typing the automatic name, or nothing, removes it.
- **Time played.** A heading shows the lifetime (reloaded stretches included); a save shows the timeline up to it.
  Times under a minute are not shown.
- **Quicksave and Autosave** are files of the playthrough: `saves/quicksave_<id>.oysav` and
  `saves/autosave_<id>.oysav` (`quickSavePath`, `autosavePath` in `game/maps/SaveGame.h`). At start,
  `migrateSharedSaveSlots` renames the shared `quicksave.oysav` and `autosave.oysav` of earlier builds to their
  playthrough's names.
- **Save screen.** It lists the playthrough being played; "All" adds the others, and a ruleset button beside it
  (Standard, MAW) lists every playthrough's saves of that ruleset. A save's name must be free only
  within that playthrough.
- **Delete Playthrough** removes every save of the playthrough (Quicksave and Autosave too), its statistics files and
  its name. It is refused for the playthrough being played.

## Sealed files

`game/party/PlaythroughSeal.cpp` seals the YAML text with XChaCha20-Poly1305 (Monocypher's `crypto_aead_lock`), with a
fresh 24-byte random nonce per seal.

- **Layout.** `OYSEAL01`, the copy (lifetime 1, timeline 2), the key version, the playthrough id, the nonce, the
  16-byte tag, then the ciphertext. Everything before the nonce is authenticated with the text. Editing either, passing
  a timeline off as a lifetime, or using another playthrough's record fails.
- **Keys.** The release key from the private source (see [Release key](#release-key)), and the public development key
  in the code (version `dev`). A build seals with the release key when it has one, else with the development key.
- **Reading the sidecar.** A build reads its own key version's file. A release build that has none reads the `.dev`
  file instead and keeps its *Development build* label. A build writes only its own key version's file, so it never
  overwrites a record it cannot open.
- **Reading a save's timeline.**
  - A seal that opens is used.
  - A seal that fails with a key this build has marks the timeline *changed outside the game* and starts it at zero.
  - A seal from a key this build lacks (a release save in a development build) starts the timeline at zero.
  - Unsealed text from the first development builds of this feature is read and marked *development build*.

## Integrity flags

The flags are sticky. A load merges them both ways between the two copies, so they stay for the rest of the
playthrough.

- **Assisted.** Each reason is recorded with when it was first used, how many sessions used it, and, for the console,
  the commands run with their counts. `PlaythroughStatistics::markAssisted(reason, detail)` is cheap per frame: after
  a reason's first call in a session, only a console command adds anything. The reasons are:
  - `debug console`: any command that succeeds, except the forms that only read or show things.
    - Whole commands marked `readOnly` in their `DebugConsole::CommandDefinition`: `help`, `cls`, `loc`, `map`,
      `memory`, `render`, `portals` and `screenshot`. Also `menu` and `combatlog`, which do what ordinary input does,
      and `exec`, whose file's commands each count on their own.
    - Read-only forms of other commands, through the definition's `readOnlyWith` (`readOnlyConsoleActions` in
      `GameApplication.cpp`): `get`, `dump`, `list`, `show`, `status`, `stats`, `count`, `search` and `forecast`, and
      the bare command where it only shows something (`time`, `gold`, `ruleset`, `sky`, `weather`). For example
      `qbit dump`, `gold get` and `destructible <id> state` do not count; `qbit set` and `time advance` do.
    - The help panel's buttons and menu input tours' console steps run through the same path.
  - `immortal` and `unlimited mana`: while those settings are on during play.
  - `turbo movement`: while turbo is actually used (Ctrl held with the setting on).
  - `movement speed` and `time scale`: while either is not 1.
  - `start flying`: while the `start_flying` debug setting gives the party flight on an outdoor map.
  - `test party`: a MAW game started by `testparty <stage>`. The console marks the playthrough it ran in, and the
    command starts the new game a frame later.
  - `god lich party`: a new game started with the debug God Lich party.
  - `debug start`: the debug quick start (`startNewSession`), which includes agents' test runs.
- **Development build.** A development-key build wrote the record.
- **Changed outside the game.** A copy failed authentication with a key this build has, and the record restarted from
  what could be trusted.
- **Restored from an older copy.** The lifetime's write `sequence` counts up at every write. Each save stores the
  lifetime's count at that moment, inside its sealed timeline. Loading a save whose count is higher than the
  sidecar's means an older sidecar was put back.

The page's bottom line names the flags: in red when anything but *Development build* is set, muted otherwise. Holding
the right mouse button on it lists each assist with its first day, sessions and console commands, and explains the
other flags.

## Release key

Neither the key nor how a build assembles it is in the repository.

- **Interface.** A release build compiles in a private C++ source that defines
  `const char *OpenYAMM::Game::PlaythroughSealRelease::assembleKey(uint8_t *pKey)`. It writes the 32-byte key and
  returns its version label.
- **Where it comes from.** `cmake/PlaythroughStatisticsKey.cmake` takes the source from
  `-DOPENYAMM_STATS_KEY_SOURCE=<file>`, or from the `OPENYAMM_STATS_KEY_SOURCE` environment variable holding its
  text. CI sets that from the repository secret of the same name for every job (`.github/workflows/packages.yml`),
  the Android Gradle build included. Configure logs which key a build uses.
- **Without it.** `OPENYAMM_HAS_RELEASE_STATS_KEY` is 0 in the generated `build/generated/PlaythroughStatisticsKey.h`,
  and the build uses the development key. Forks and contributors' builds work unchanged and say so on the page.
- **Generator.** It is kept outside the repository with the maintainer's other keys. It makes the key file once,
  then a new source on every run with a different random scheme. The scheme splits the key into XOR shares, encodes
  each share differently, scatters the shares through tables of random decoy bytes, and assembles the bytes in a
  permuted order through volatile reads. The executable holds no contiguous copy of the key.
  - Regenerating with the same key changes only the scheme.
  - A new key needs a new version label (`release-2`). Records sealed with the old key then no longer open.
  - `packaging/RELEASE.md` has the commands.
- **Backups.** The maintainer keeps the key file, the generated source and the generator outside the repository, with
  a second copy on another machine. Losing the key file makes sealed release records unreadable.

## Limits

This is a deterrent against casual editing, not a guarantee:
- Anyone who extracts the key from the executable, for example by catching it in a debugger at the decryption call,
  can write records that pass every check.
- Putting back an older sidecar together with only saves older than it passes. The write sequence catches an older
  sidecar next to a newer save, not a coordinated rollback of both.
- Deleting the sidecar is not hidden: the record restarts from the save, marked "Tracked since …".

## Tests

`tests/PlaythroughStatisticsTests.cpp` covers:
- the sealed YAML round trip;
- a quickload restoring the timeline while keeping the lifetime;
- the sidecar between sessions;
- older saves sharing a record through their seed;
- gold and experience by reason, and party copies not recording;
- death causes;
- the save round trip;
- a seal refusing edits, the other copy's kind and another playthrough;
- a changed sidecar;
- an older sidecar put back;
- assists persisting, counted once per session, with commands;
- a changed timeline.

`RulesetTests.cpp`'s legacy save-layout tests strip the new save fields.

## Not done

- The Load screen does not group saves by playthrough.
- No headless scenario covers a quickload end to end; the unit tests do.
- The top bar's touch region on Android (`GameplayScreenRuntime.cpp:814`) is not checked against the buff panel below
  it at the new width.
- A full game build with the real release key has not run yet. Its first CI configure should log "release key from
  the private key source".
