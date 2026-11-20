# Plan A: inn rest, tavern food, rest-screen weekday

Line references are against `main` at 2476b1e90 (re-read 2026-10-25). Nothing has been edited.

## A1. Indoor inn rest takes gold but never rests (Stone City, Celeste, The Pit)

**Root cause.** `performHouseAction` / `TavernRentRoom` (`game/gameplay/HouseInteraction.cpp:1781-1800`) takes the
gold and returns `pendingInnRest`. `GameplayDialogController` copies it into its `Result` and sets
`shouldCloseActiveDialog` (`GameplayDialogController.cpp:2972-2976`). Only the outdoor `afterCloseContinuation`
(`OutdoorInteractionController.cpp:1388-1394`) calls `startInnRest`. The indoor view passes `{}` in that slot
(`IndoorGameView.cpp:1769-1791`, the third argument).

The duration lives in the outdoor-only `OutdoorGameView::innRestDurationMinutes` (`OutdoorGameView.cpp:4476-4507`,
constants at 209-213). Its +12 h case uses raw MM7 ids 111/114/116, which are alchemists in the merged
`house_data.txt`. The merged tavern ids are 243 The Snobbish Goblin (Deyja), 246 The Vampyre Lounge (The Pit,
indoor) and 248 Fortune's Folly (Mount Nighon). Original: dawn plus 1 h, plus 12 h for those three
(OpenEnroth `src/Application/Game.cpp:1050-1062`, `HouseEnums.h:124-129`).

**Placement.** Taverns and rest are shared gameplay (AGENTS.md architecture). The fix goes in shared code, not in
`IndoorGameView`/`OutdoorGameView`.

**Changes.**

1. `game/gameplay/HouseInteraction.h/.cpp`: add a pure free function next to `isHouseOpenAtGameMinute`. Move the
   constants from `OutdoorGameView.cpp` with the merged ids (the `MinutesPerDay` constant already exists in
   `HouseInteraction.cpp:28`):
   ```cpp
   // HouseInteraction.h
   float innRestDurationMinutes(uint32_t houseId, float currentGameMinutes);

   // HouseInteraction.cpp, anonymous namespace
   constexpr int InnRestDawnHour = 5;
   constexpr uint32_t DeyjaTavernHouseId = 243;        // The Snobbish Goblin
   constexpr uint32_t PitTavernHouseId = 246;          // The Vampyre Lounge
   constexpr uint32_t MountNighonTavernHouseId = 248;  // Fortune's Folly

   float innRestDurationMinutes(uint32_t houseId, float currentGameMinutes)
   {
       int currentMinuteOfDay = static_cast<int>(std::floor(currentGameMinutes)) % MinutesPerDay;
       if (currentMinuteOfDay < 0)
       {
           currentMinuteOfDay += MinutesPerDay;
       }
       int minutesUntilDawn = InnRestDawnHour * 60 - currentMinuteOfDay;
       if (minutesUntilDawn <= 0)
       {
           minutesUntilDawn += MinutesPerDay;
       }
       float durationMinutes = static_cast<float>(minutesUntilDawn) + 60.0f;
       if (houseId == DeyjaTavernHouseId || houseId == PitTavernHouseId || houseId == MountNighonTavernHouseId)
       {
           durationMinutes += 12.0f * 60.0f;
       }
       return durationMinutes;
   }
   ```
   This keeps the existing outdoor formula unchanged except for the ids.
2. `game/gameplay/GameplayScreenRuntime.h:221` / `.cpp:1599-1603`: change to `void startInnRest(uint32_t houseId)`.
   It calls `openRestOverlay(false)` and then
   `beginRestAction(Heal, innRestDurationMinutes(houseId, worldRuntime()->gameMinutes()), false, true)`, returning
   early when `worldRuntime() == nullptr`.
3. `GameplayScreenRuntime::executeActiveDialogAction(...)` (`GameplayScreenRuntime.cpp:2363-2415`): start the rest
   in the `!mapMovePending` branch, after `closeActiveDialogActionResult(...)` (2402) and before
   `afterCloseContinuation`:
   ```cpp
   else
   {
       closeActiveDialogActionResult(result, closeActiveDialog);
       if (result.pendingInnRest.has_value())
       {
           startInnRest(result.pendingInnRest->houseId);
       }
   }
   ```
   Both views then get the rest from one place.
4. Remove the outdoor duplicate: delete the `pendingInnRest` lambda at `OutdoorInteractionController.cpp:1388-1394`
   (pass `{}` as indoor does). Also delete `OutdoorGameView::innRestDurationMinutes` (`OutdoorGameView.h:686`,
   `.cpp:4476-4507`) and its constants at `OutdoorGameView.cpp:209-211,213`. Keep `MinutesPerDay` if other code in
   that file uses it.
5. `game/outdoor/HeadlessOutdoorDiagnostics.cpp:34490` only formats a price, so it needs no change. Grep for any
   other `startInnRest(` caller after the signature change.

**Edge cases.**
- Gold is still taken before the rest. Once the rest always starts, that matches the original. Add no refund path.
- `beginRestAction` refuses a second action ("You are already resting.", `GameplayScreenRuntime.cpp:1517-1521`).
  It cannot run here, because the inn closes the dialog first.
- Inn rest passes `consumeFood=false`, so it skips camping restrictions such as MAW's "enemies near" and food.
  That is intentional and matches the original. Do not add the camping checks.
- After the rest, `applyMapReentryReset()` runs for an inn rest (`GameplayScreenRuntime.cpp:1916-1919`). It must
  now work on `IndoorWorldRuntime`, since indoors never reached it before. Check that it doesn't respawn Stone City
  guards hostile or reset doors oddly.
- The Pit's tavern (246) is indoor, so its +12 h case only starts working with this fix.

**Verification.**
- Unit test, extending `tests/HouseDialogueRegressionTests.cpp` next to `"tavern rent room defers recovery until
  rest screen"` (line 6865):
  `TEST_CASE("inn rest lasts until an hour after dawn, twelve hours longer in Deyja, the Pit and Mount Nighon")`.
  Call `innRestDurationMinutes` for 228 at 22:00, giving 7 h + 1 h = 480. Call it for 246 at the same time, giving
  480 + 720. At 05:00 the 228 rest wraps to 24 h + 1 h. Also check that 252 Grogg's Grog gets no bonus.
- Headless scenario, new `tests/scenarios/mm7/stone_city_inn_rest.yml`, modelled on `tests/scenarios/mm8_party_slopes.yml`
  (`load_map` of a `.blv`) and `tests/scenarios/rulesets/maw_bounty.yml` (`select_topic` / `advance_runtime` /
  `assert: {gold}`). Steps: `load_map: {map: 7d24.blv}`, then `execute_event: {id: 429}` (opens house 252,
  `assets_dev/worlds/mm7/events/maps/7d24.lua:320-321`). Next, `select_topic` with `match_label: "Rent room for 40
  gold"`; take the action id from the dialog snapshot. Finish with `advance_runtime: {seconds: 3}` and an assert.
  The runner has no game-time assert (the loader's `AssertKeys`, `ScenarioYamlLoader.cpp:40-45`). Either add
  `assert: {game_minutes_min: N}`, registered in the loader lists in the same change per `tests/scenarios/README.md`,
  or rely on the unit test above plus `assert: {gold: <start-40>}` and a party-health check.
- Manual: in an MM7 game, enter Stone City, rent a room and check that the clock jumps to 06:00 and the party heals.

**Size.** Small: about 40 lines moved and roughly 10 changed.

## A2. Tavern "fill packs" is always 14 days

**Root cause.** `game/gameplay/HouseInteraction.cpp:27` has `constexpr int TavernFoodTarget = 14;`. It is used for
the label (1261), the menu's disabled check (1270), the full check (1805), the fill (1826) and the message (1827). The
price uses the house's `Val` value (`PriceCalculator.cpp:325-334`, loaded as `HouseEntry::priceMultiplier` from
row[12] in `HouseTable.cpp:734`). Original sets food to `Val`: OpenEnroth `src/GUI/UI/Houses/Tavern.cpp:32,114,124`.
MMerge doesn't override it. MAW's `content/house_data_patch.txt` only changes `Open` hours, so the fix applies to
every ruleset.

**Placement.** Shared, `HouseInteraction.cpp` only.

**Changes.**
```cpp
// remove: constexpr int TavernFoodTarget = 14;
// anonymous namespace:
int tavernFoodTarget(const HouseEntry &houseEntry)
{
    return static_cast<int>(houseEntry.priceMultiplier);
}
```
- Replace all five uses with `const int foodTarget = tavernFoodTarget(houseEntry);`, in the menu builder at
  ~1244 and the `TavernBuyFood` case at 1803.
- Use truncation, as OpenEnroth's `int foodNum = fPriceMultiplier` does. Every tavern `Val` is an integer
  (6 to 60), so rounding never matters.

**Edge cases.**
- Don't keep 14 as a fallback when `Val` is 0 (AGENTS.md: no masking fallbacks). No tavern row has 0.
- MAW Insanity food cap (`MawMonsterRules::capInsanityFood`, `MawMonsterRules.cpp:1734-1760`): a 60-day fill can
  exceed the cap until the next map change, when the cap trims it. Check whether MAW expects the cap to apply on
  purchase. If so, add an explicit ruleset hook rather than changing the target.
- The cook/chef follower cap (`GameplayDialogController.cpp:64`, `MaxFoodForCookFollower = 14`) is a separate
  MMerge rule (`NPCFollowersSkills.lua:324`). Do not touch it.
- The existing test `"house actions expose mmmerge speech reactions..."` (`HouseDialogueRegressionTests.cpp:6918`) uses
  `addFood(100)` on house 228 (`Val` 6). That is still "full", so the test is unaffected.

**Verification.** Add `TEST_CASE("tavern fill packs uses the house food value")` to
`tests/HouseDialogueRegressionTests.cpp`, copying the `performHouseAction` call shape at 6928-6940.
- With 0 food at house 228 (`DaggerWoundTavernHouseId`, line 59), check that food becomes 6. A second buy is
  refused with `SpeechId::TavernPacksFull`.
- With 0 food at house 252 Grogg's Grog, food becomes 20.
- Check that the menu label from the house-action-option builder reads "Fill packs to 20 days for ...".

Build and run with `cmake --build build --target openyamm_unit_tests -j25 && ./build/tests/openyamm_unit_tests
--test-case='*tavern*'`.

**Size.** Trivial.

## A3 (optional). Weekday on the rest screen

The original rest screen shows time, Day, Month and Year with no weekday (OpenEnroth `src/GUI/UI/UIRest.cpp:149-153`),
and OpenYAMM already matches it (`assets_dev/engine/ui/gameplay/rest.yml:154-245`). This is a feature request.

**Changes.**
- `game/ui/GameplayPartyOverlayRenderer.cpp`: add `int weekday` to `RestDateText` (`1403-1408`) and set
  `result.weekday = totalDays % 7` in `formatRestDateText` (`1410-1416`). Add a full-name table identical to
  `LoadGameScreen.cpp:76-81`, then `label = replaceAllText(label, "{weekday}", ...)` beside the other placeholders
  (3121-3125).
- `assets_dev/engine/ui/gameplay/rest.yml`: either change `RestTimeText` to `'{weekday} {time}'`, the smallest
  layout change, or add a `RestWeekdayText` row in the date block. Check the Obsidian rest layout spacing first
  (`level_generation/ui/obsidian_rest_hourglass_20260929/native/README.md`: wider date block, fine divider).
- Better but larger: the calendar maths is duplicated four times (`GameplayPartyOverlayRenderer.cpp:1410`,
  `LoadGameScreen.cpp:52`, `GameplaySaveLoadUiSupport.cpp:~55`, `GameApplication.cpp:1761-1778`), plus
  `StoryTextFormatter.cpp:15`. One shared `game/gameplay/GameCalendar.h` with `civilTimeFromGameMinutes` and the name
  tables would remove that. Only do this if the user wants the cleanup now.

**Edge cases.** Day 1 of the game is Monday, matching save slots (`GameplaySaveLoadUiSupport.cpp:28,62`). Use the same
`totalDays % 7` so the two screens agree. Android uses the same `rest.yml`, so check the label width at 4:3.

**Verification.** If the shared helper is extracted, extend `tests/GameplaySaveLoadUiSupportTests.cpp` with a
weekday/month/day case (for example minute 0 is Monday 1/1/1168, and minute 7*1440 is Monday again). Without the
helper, take a native capture of the rest screen per AGENTS.md (`./tools/run_game.sh --isolated rest_weekday ...
--set debug.screenshot_path=/abs/rest.png`) after opening rest from the debug console or a save.

**Size.** Trivial (placeholder only); small (shared calendar helper).

## Not in this plan
Sleep portraits during rest were fixed in ddcf6696d (`GameplayScreenRuntime.cpp:1551-1573`). The fix is not in v1.11
and only needs a release. A1 makes indoor inns reach that same code.
