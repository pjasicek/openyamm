# Plan B: shops, guilds, house audio, MM6 light/dark path

Read-only analysis. Line numbers checked against the working tree on 2026-10-25. Nothing in the repo was edited.
Everything below is shared gameplay code or shared Standard data, so it applies to both Standard and MAW.

---

## 1. House entry audio in shared code (fixes "Stone City shops have no greeting")

**Today.** The house entry audio is outdoor-only, in `OutdoorGameView::updateHouseVideoPlayback`
(`game/outdoor/OutdoorGameView.cpp:4186-4264`). It does four things:
- tracks the house through `m_activeHouseAudioHostId` (`OutdoorGameView.h:944`, reset at `OutdoorGameView.cpp:3978`);
- on entry, pauses the music and plays `SoundId::Enter` (HouseDoor group) plus the `GeneralGreeting` line
  (HouseSpeech group);
- on exit, plays `SoundId::WoodDoorClosing` and resumes the music;
- skips the greeting when the dialog carries its own video (`activeDialog.videoName`).

`IndoorGameView::updateDialogueVideoPlayback` (`game/indoor/IndoorGameView.cpp:1695-1736`) only plays the video. That
leaves every indoor shop silent: Stone City 7d24, Celeste 7d25, The Pit 7d26, MM6 d24 and so on.

**Change (shared: `game/gameplay/GameplayScreenRuntime.{h,cpp}`).** This class already owns `m_pAudioSystem`,
`playHouseSound` (`:2938`), `party()`, `worldRuntime()` and the house video helpers (`:3419-3441`).
- Add the member `uint32_t m_activeHouseAudioHostId = 0;`.
- Add `void updateHouseEntryAudio(const HouseEntry *pHostHouseEntry, bool houseDialogueActive);` and
  `void resetHouseEntryAudio();`. `resetHouseEntryAudio` clears the host id without playing anything; use it on map
  unload.

```cpp
void GameplayScreenRuntime::updateHouseEntryAudio(const HouseEntry *pHostHouseEntry, bool houseDialogueActive)
{
    const uint32_t hostId = houseDialogueActive && pHostHouseEntry != nullptr ? pHostHouseEntry->id : 0;

    if (hostId == m_activeHouseAudioHostId)
    {
        return;
    }

    if (m_activeHouseAudioHostId != 0 && m_pAudioSystem != nullptr)
    {
        m_pAudioSystem->playCommonSound(SoundId::WoodDoorClosing, GameAudioSystem::PlaybackGroup::HouseDoor);
        m_pAudioSystem->resumeBackgroundMusic();
    }

    m_activeHouseAudioHostId = hostId;

    if (hostId == 0 || m_pAudioSystem == nullptr)
    {
        return;
    }

    m_pAudioSystem->pauseBackgroundMusic();
    m_pAudioSystem->playCommonSound(SoundId::Enter, GameAudioSystem::PlaybackGroup::HouseDoor);
    const HouseSoundType greeting = houseEntrySoundType(*pHostHouseEntry, party());   // see fix 3
    const std::optional<uint32_t> soundId = deriveHouseSoundId(*pHostHouseEntry, greeting);

    if (soundId)
    {
        playHouseSound(*soundId);
    }
}
```

**Outdoor caller.** Replace the audio blocks in `OutdoorGameView::updateHouseVideoPlayback` (4205-4258) with calls to
`updateHouseEntryAudio(...)`. Keep the outdoor semantics exactly:
- Dialog with its own `videoName`: call `updateHouseEntryAudio(nullptr, false)`. Today that path resumes the music
  without the door sound, so either add a `bool playDoor` parameter or accept the door sound there. Pick one
  explicitly.
- Otherwise call `updateHouseEntryAudio(pHostHouseEntry, true)`, but only when `pHostHouseEntry->videoName` is
  non-empty. Today houses without a video get no audio; keep that.

Then delete `m_activeHouseAudioHostId` from `OutdoorGameView` (`.h:944`, the initialiser at `:2633`, and `:3978` which
becomes `resetHouseEntryAudio()`).

**Indoor caller.** In `IndoorGameView::updateDialogueVideoPlayback` (1695-1736), make the same calls in the same
branches. Call `resetHouseEntryAudio()` in the unbind path next to `bindAudioSystem(nullptr)` (`:1399`).

**Optional dedupe.** `activeEventDialogAllowsHouseVideoPlayback` (`game/ui/GameplayOverlayTypes.h:74`) plus the
`currentDialogueHostHouseId` copies (`IndoorGameView.cpp:902`, `GameplayDialogueRenderer.cpp:480`,
`GameplayDialogController.cpp:560`) could fold the whole update into one shared
`GameplayScreenRuntime::updateHouseDialoguePresentation(deltaSeconds)`. Only do this if both views are already
identical; otherwise keep the change minimal.

**Edge cases.**
- Switching between two houses without leaving: the first house plays the close sound, the second the enter sound.
  That matches the outdoor behaviour today.
- Map change while inside a house: reset without the door sound.
- Houses with no sound base (residences): `deriveHouseSoundId` returns nullopt, so no greeting. The door sound and
  music pause still happen, as outdoors.
- Side note: the Stone City weapon shop (house 17) has sound base 31110, so its greeting is 31111
  (`elf magic shop 01` in `sounds.txt`), but it is a dwarven shop. This is probably a separate data error in
  `house_animations.txt`. I didn't verify it against MM7, so check before touching it.

**Verification.**
- The audio system has no playback log, so unit-test the decision function instead. In
  `tests/HouseDialogueRegressionTests.cpp`, next to `"merged house movie sound bases drive mm8 house speech"` (`:6535`),
  add `TEST_CASE("stone city house entry resolves a greeting sound")`. For houses 17, 57, 124, 252 and 321 it should
  check that `houseEntrySoundType(...) == GeneralGreeting` and that `deriveHouseSoundId` returns base+1.
- Manual check: `OPENYAMM_AUDIO_TRACE=1 ./tools/run_game.sh --isolated stonecity --world mm7 --map 7d24.blv ...`.
  Enter a shop; the log should show HouseDoor and HouseSpeech plays (`GameAudioSystem.cpp:28-130`).

**Size:** small.

---

## 2. Alchemist stock: empty bottles and recipe scrolls

**Today.** `generateShopStandardStock` and `generateShopSpecialStock` (`game/gameplay/HouseServiceRuntime.cpp:562-650`
and `:652-…`) fill all 12 alchemist slots at random from Reagent, Herb and Bottle items (`isShopItemFamilyAllowed`,
`:163-169`; "Bottle" also covers every potion). Item 220 "Potion Bottle" only has weight in tier 1.

**Original.** OpenEnroth `GUIWindow_AlchemyShop::generateShopItems` (`src/GUI/UI/Houses/Shops.cpp:674-693`):
- Standard: slots 0-5 are `ITEM_POTION_BOTTLE`, slots 6-11 are random `RANDOM_ITEM_REAGENT` at the shop's tier.
- Special: slots 0-5 are a random recipe scroll, slots 6-11 are random `RANDOM_ITEM_POTION`.

The layout has 12 slots and the top row is indices 0-5 (`game/ui/HouseShopLayout.cpp:101-130`).

**Recipe items.** `AlchemyBenchRuntime::recipeScrollPotionItemId` (`game/items/AlchemyBenchRuntime.cpp:342-370`)
defines a recipe scroll as equipStat `Mscroll` with a name ending in `" Recipe"` (case-sensitive) that resolves to a
potion. That matches two blocks of 32: 700-731 and 1542-1573 (the MM8 and MM7 copies, same names).
- 751-769 ("Divine Boost recipe", lowercase) do **not** match. They are other MMerge scrolls; leave them out unless the
  bench learns to read them.
- Don't hard-code id ranges. Build the candidate list from the item table with the bench's predicate:
  `AlchemyBenchRuntime::recipeScrollPotionItemId(id, tables).has_value()`. Then remove duplicate names, keeping the
  lowest id, so both blocks don't double the odds.
- Open question: which block should MM7 shops sell? Both teach the same potion, so it only matters for item identity.
  If identity matters, choose by `houseEntry.worldId` ("mm7" → 1542-1573, otherwise 700-731).

**Change (shared, `HouseServiceRuntime.cpp`).** Add one helper and call it before the generic branch in both stock
functions:

```cpp
constexpr uint32_t PotionBottleItemId = 220;
constexpr size_t AlchemistTopRowSlots = 6;

// Native alchemist rows: standard = 6 empty bottles over reagents, special = 6 recipes over potions.
std::vector<InventoryItem> generateAlchemistStock(..., bool special)
{
    std::vector<InventoryItem> results(count);
    const size_t topRowCount = std::min(AlchemistTopRowSlots, count);

    for (size_t index = 0; index < topRowCount; ++index)
    {
        const uint32_t itemId = special ? pickRecipeScroll(itemTable, rng) : PotionBottleItemId;   // 0 if none
        if (itemId != 0)
        {
            results[index] = ItemGenerator::makeInventoryItem(itemId, itemTable, ItemGenerationMode::Shop);
        }
    }

    const std::vector<InventoryItem> bottomRow = generateStockItems(..., count - topRowCount,
        [special](const ItemDefinition &entry)
        {
            return special ? isPotionStockItem(entry) : isReagentStockItem(entry);  // Reagent/Herb vs Bottle minus 220
        },
        weightFunc, true);
    // copy bottomRow into results[topRowCount + i]
    return results;
}
```

- `pickRecipeScroll` needs `AlchemyBenchTables` (item table plus potion settings). If the stock path can't reach
  `potionSettingTable`, use the cheaper rule `equipStat == "Mscroll" && name.ends_with(" Recipe")`, the same rule as
  `tests/AlchemyBenchRegressionTests.cpp:315-335`.
- Keep the bottom row's existing tier rule (`rule.itemTypes` from `house_rules.txt` "Alchem shops Standart/Special").
  Exclude item 220 from the bottom-row potion pool.
- The standard top row ignores the tier. The special top row uses a uniform pick, as the original does.

**Edge cases.**
- MAW's `MawItemRules::adjustShopStock` (`game/rules/maw/MawItemRules.cpp:2165-2235`) may replace non-enchantable
  stock with gems at `shopReplaceChance`, including bottles. That is MAW-specific; leave it unless MAW's design says
  bottles are exempt. Flag it to the MAW owner.
- MM6 "Alchemist"-type houses (1213 Traveler's Supply, 1229, 1274, 1289) are MM6 general stores. They also get
  bottles plus reagents, which matches MMerge running on the MM8 engine. I didn't verify the MM8 engine's alchemist
  routine; a quick Rizin check of MM8-Rel.exe is worth doing before shipping.
- Houses with `deterministicStandardStockPages` return early (`:866-875`), so they are unaffected.
- Old saves keep their current stock until the next refresh. No migration needed.

**Verification.**
- In `tests/HouseDialogueRegressionTests.cpp`, next to `"house service guild spellbook stock generates and buys"`
  (`:3135`), add `TEST_CASE("alchemist standard stock puts empty bottles in the top row")`. Use house 124 (Stone City),
  `HouseServiceRuntime::ensureStock(..., HouseStockMode::ShopStandard)`, and check slots 0-5 are id 220 and slots 6-11
  are Reagent/Herb.
- Add `TEST_CASE("alchemist special stock offers recipe scrolls")`: slots 0-5 resolve through
  `recipeScrollPotionItemId`, slots 6-11 are Bottle-type potions other than 220.

**Size:** small.

---

## 3. Magic guild membership gating (MMerge `StdQuestsFunctions.lua:279-329`)

**MMerge rules.**
- Gated guild types are 5-15: Fire 5, Air 6, Water 7, Earth 8, Spirit 9, Mind 10, Body 11, Light 12, Dark 13,
  Elemental 14, Self 15. These match the `guildType` values in `buildGuildMembershipOffer`,
  `game/tables/NpcDialogTable.cpp:179-207`.
- Gated continents are Antagarich (MM7) and Enroth (MM6) only.
- On Antagarich, Light 12 and Dark 13 are **exempt**; there the light/dark path gates them. MM6 Light/Dark stay gated
  (1000 gold, topics 1709/1710).
- Jadame (MM8) is never gated, including its "Elemental Guild"-type houses such as 182 "Cures and Curses" on out01 and
  "Spell Shop".
- A non-member gets no spell shop topic and only "Learn", which answers NPC text 122 ("You must be a member of this
  guild to study here."). Membership is party-wide (`vars.GuildMembership[type]`).

**Today.** `skillGuildMembershipType` (`game/gameplay/HouseInteraction.cpp:326-359`) only knows the six skill guilds,
by house name. `hasSkillGuildMembership` is at `:366-391`; the call sites are the info lines at `:1016-1022` and the
action options at `:1392-1426`. `HouseSoundType::MagicGuildMembersOnly = 3` (`HouseInteraction.h:71`) is never used.

**Change (shared, `HouseInteraction.cpp/.h`).**

```cpp
std::optional<uint32_t> magicGuildMembershipType(const HouseEntry &houseEntry)
{
    struct Mapping { const char *pType; uint32_t guildType; };
    constexpr std::array<Mapping, 11> mappings = {{
        {"Fire Guild", 5}, {"Air Guild", 6}, {"Water Guild", 7}, {"Earth Guild", 8}, {"Spirit Guild", 9},
        {"Mind Guild", 10}, {"Body Guild", 11}, {"Light Guild", 12}, {"Dark Guild", 13},
        {"Elemental Guild", 14}, {"Self Guild", 15},
    }};
    const bool antagarich = houseEntry.worldId == "mm7";
    const bool enroth = houseEntry.worldId == "mm6";
    // find mapping; return nullopt if !antagarich && !enroth, or antagarich && guildType is 12 or 13
}

std::optional<uint32_t> requiredGuildMembershipType(const HouseEntry &houseEntry)
{
    const std::optional<uint32_t> skillGuild = skillGuildMembershipType(houseEntry);
    return skillGuild ? skillGuild : magicGuildMembershipType(houseEntry);
}
```

- Rename `isSkillGuildHouse` / `hasSkillGuildMembership` to `requiresGuildMembership` / `hasGuildMembership` and base
  them on `requiredGuildMembershipType`. The membership storage is unchanged: party var `0x8000 | type` or runtime var
  `0x80000000 | type`, written by `grantGuildMembership` (`GameplayDialogController.cpp:1868-1891`).
- In `buildHouseActionOptions` (`:1392-1426`), the non-member branch already shows a disabled "Learn Skills" and no
  "Buy Spellbooks". Generalising the predicate gives the MMerge behaviour.
- At `:1412`, keep `!isSkillGuildHouse(houseEntry)` as the "has spellbooks" test (skill guilds sell none). Don't swap
  it for the new predicate.
- Also export `HouseSoundType houseEntrySoundType(const HouseEntry &, const Party *)`: return `MagicGuildMembersOnly`
  when `magicGuildMembershipType` is set and the party isn't a member, otherwise `GeneralGreeting`. This is what fix 1
  calls. OpenEnroth plays members-only only for magic guilds (`UIHouses.cpp:370-379`), so skill guilds keep the
  general greeting.
- The `worldId` comes from the map table (`game/tables/HouseTable.cpp:1401`). Check that the "mm6"/"mm7" strings
  match `MapStats` world ids.

**Edge cases.**
- MM7 Light/Dark guilds stay open, as in MMerge. In the original MM7 they need the path award. Not in scope.
- Existing tests that use MM6/MM7 magic guild actions without membership will break. `ensureStock` isn't gated, so the
  stock tests at `:3135` and `:3179` are safe, but grep for `GuildBuySpellbooks` and "Learn Skills" in tests using MM6
  or MM7 guild houses and set membership in them.
- The headless playthroughs `tests/scenarios/mm6/*` may buy spells without joining. Check `probe_4.yml` and
  `main_story_draft.yml`; they already contain `guild_membership_offer` steps at `:3325`.
- Fix 4 from the triage ("join doesn't take gold") becomes testable once the gate exists. The join code and its test
  (`:5438-5467`) already take the gold.

**Verification.**
- Extend `tests/HouseDialogueRegressionTests.cpp` in the style of
  `"mm6 skill guilds require membership and expose their original skills"` (`:4226-4307`). Add
  `TEST_CASE("mm6 and mm7 magic guilds require membership; mm8 and mm7 light/dark do not")`:
  - MM6 Elemental guild 1214 (Initiate Guild of the Elements, New Sorpigal): Learn disabled and no Buy Spellbooks;
    after `setEventVariableValue(0x800E, 1)`, both are enabled.
  - An MM7 Fire guild (house 128 from `:3182`) is gated.
  - MM8 182 is not gated.
  - An MM7 Light guild is not gated.
  - `houseEntrySoundType` returns `MagicGuildMembersOnly` for a non-member MM6 guild.

**Size:** small to medium.

---

## 4. MM6 Path of Light / Path of Dark topics (port of `reference/mmmerge/Scripts/Global/Quest_EnrothDarkArts.lua`)

**Reference content.**
- Dark topic, slot 4 (event E): NPC 1040 Su Lang Manchu (Paradise Valley) and 1030 Rebecca Calaway (Blackshire).
- Light topic, slot 4: NPC 1057 Ki Lo Nee (Eel-Infested Waters), 1031 Virginia Standridge (Silver Cove) and 795 Marton
  Ferris (Blackshire).
- The player mentions Frozen Highlands, so Rodril's newer build may use other NPCs; confirm with the developer.
- Class ids are MMerge `const.Class` (`reference/mmmerge/Scripts/General/MiscTweaks.lua:303-353`), the same ids
  `GetPlayerClass` returns (used as 47 in `assets_dev/worlds/mm7/events/Global_mm7_mmmerge.lua:834-841`):
  - Dark: 51 MasterWizard→47, 50 HighPriest→7, 46 ArchMage→47, 28 Hero→29, 15 ArchDruid→14, 6→7, 2 MasterArcher→3.
  - Light: 51→46, 50→6, 47→46, 29→28, 14→15, 7→6, 3→2.
- On "yes", the skill being kept becomes max(Light, Dark) and the other skill becomes 0. The other school's spells are
  removed: going dark removes 78-88 (Light Bolt … Divine Intervention); going light removes 89-99 (Reanimate …
  Souldrinker). Those ids match `spells.txt`. Then the class is set and a face animation plays: 71 on success, 67 when
  declined.
- Texts are NPC text 2102-2109, already in `assets_dev/engine/data_tables/npc_topic_text.txt`.

**Placement (per AGENTS.md).**
- Don't touch the generated `engine/events/Global.lua`.
- Add the events to the hand-written MM6 overlay `assets_dev/worlds/mm6/events/Global_mm6_mmmerge.lua`.
- Put the topic labels in `assets_dev/engine/data_tables/npc_topic.txt` as custom ids 10001 "Path of Light" and
  10002 "Path of Dark". The precedent is id 10000 "Dimensional travel" in the same file plus
  `RegisterGlobalEvent(10000, …)` in `engine/events/common/cross_continents_common.lua:418`. Custom ids start at
  10000+.
- Attach the topics with the existing pattern at `Global_mm6_mmmerge.lua:53-75`: `RegisterGlobalOnLoadEvent` plus
  `RegisterGlobalNpcEnterHook`, calling `evt.SetNPCTopic(npc, 4, 10001/10002)`. Slot 4 is free on all five NPCs; the
  GM-teacher overlay uses slot 3 on 1057 and 1040.

**Lua API.** `game/events/EventRuntime.cpp` registers these at `~8630-8760`:
- Already available:
  - `GetPlayerClass`, `SetPlayerClass(playerIndex, classIdOrName)` → `Party::setMemberClassName` (`:7246-7286`,
    wrappers at `event_support.lua:1317-1325`).
  - `GetCurrentPlayerIndex`.
  - `AskQuestionWithAnswerSteps(eventId, fallbackStep, text, {{Answer=…, Step=…}})` (`:7510-7580`); it resumes the
    event with `continueStep`.
  - `FaceAnimation` (`:6860`, active member only), `NPCText`, `SetMessage`, `PartyMemberKnowsSpell`.
- **Missing; add these three:**
  - `GetPlayerSkill(playerIndex, skillName) -> level, mastery` reads `Character::skills`
    (`std::unordered_map<std::string, CharacterSkill>`, `game/party/Party.h:134`) through `findSkill`. Mastery is the
    `SkillMastery` integer.
  - `SetPlayerSkill(playerIndex, skillName, level, mastery)`: level 0 erases the entry; otherwise insert or update and
    use `setSkillMastery`. Use the canonical names `"LightMagic"` and `"DarkMagic"` (`EventRuntime.cpp:1192-1193`).
  - `ForgetPlayerSpell(playerIndex, spellId)` → `Character::forgetSpell` (`game/party/Party.cpp:2105-2113`).
  - Write them in the style of `luaSetPlayerClass`: `writableParty(pLuaState)`, `luaMemberIndexArgument`, return a
    boolean. Add thin wrappers in `assets_dev/engine/scripts/common/event_support.lua` next to `:1317-1325`.
- `evt.Set{"LightSkill", …}` only writes the packed MM skill value and can't read it back, so it isn't enough for the
  max() merge.

**Overlay sketch** (in `Global_mm6_mmmerge.lua`):

```lua
local darkPath = {[51] = 47, [50] = 7, [46] = 47, [28] = 29, [15] = 14, [6] = 7, [2] = 3}
local lightPath = {[51] = 46, [50] = 6, [47] = 46, [29] = 28, [14] = 15, [7] = 6, [3] = 2}

local function swapPath(eventId, table, keepSkill, dropSkill, firstDropSpell, warningText, advertText, continueStep)
    local player = GetCurrentPlayerIndex()
    local target = table[GetPlayerClass(player)]
    if target == nil then evt.SetMessage(NPCText(2109)) return end
    if continueStep == nil then
        evt.SetMessage(advertText)
        AskQuestionWithAnswerSteps(eventId, 2, warningText, {{Answer = NPCText(2108), Step = 1}})
        return
    end
    if continueStep ~= 1 then FaceAnimation(67) return end
    -- keep = max(level/mastery of the two skills), set keepSkill, SetPlayerSkill(player, dropSkill, 0, 0)
    for spell = firstDropSpell, firstDropSpell + 10 do ForgetPlayerSpell(player, spell) end
    SetPlayerClass(player, target)
    FaceAnimation(71)
end

RegisterGlobalEvent(10001, "Path of Light", function(step)
    swapPath(10001, lightPath, "LightMagic", "DarkMagic", 89, NPCText(2104), NPCText(2106), step)
end)
RegisterGlobalEvent(10002, "Path of Dark", function(step)
    swapPath(10002, darkPath, "DarkMagic", "LightMagic", 78, NPCText(2105), NPCText(2107), step)
end)
```

**Edge cases.**
- MMerge needs two clicks within 2 s before it asks. The plan uses the question prompt as the confirmation instead (a
  deliberate simplification; note it in the overlay comment).
- The active member at resume time must be the one who asked. Store the index in a local or runtime variable when
  asking, and reuse it on resume.
- Compare "max" by mastery first, then level. That matches MMerge comparing packed values, where the mastery bits sit
  above the level.
- The target class may be below the skill's current mastery cap. MMerge doesn't clamp; don't clamp either.
- Classes 46 and 47 also feed the Lich jar promotion (`Global_mm7_mmmerge.lua:841` uses 47); behaviour is unchanged.
- Naming: `game/party/SkillData.cpp:264` displays class 47 as "Dark ArchMage", while `class.txt` says "Master
  Necromancer". Decide with the developer; it is out of scope for this fix.
- `SetPlayerClass` recomputes HP and SP (`Party.cpp:5982`). MMerge's `Add{"Experience",0}` only refreshes the UI, so
  there is no extra step.

**Verification.** `tests/ScriptedMapRegressionTests.cpp` already loads the MM6 overlay
(`"seer lost item topic recovers ever owned active quest items"`, `:1947-2000`: `support` + `mm6_common` +
`Global_mm6_mmmerge`, then `executeEventById`). Add
`TEST_CASE("mm6 path of dark converts master wizard and drops light spells")`:
- Party member class 51 with LightMagic Master 10 and DarkMagic Expert 4, knowing spells 78 and 90.
- Run event 10002: expect a pending prompt.
- Run again with `continueStep = 1`: expect class 47, DarkMagic Master 10, no LightMagic, spell 78 forgotten, spell 90
  kept.
- Mirror it for 10001 with class 50 → 6.
- Check that an ineligible class shows text 2109.
- Add a C++ unit test for the three new Lua functions in the same file.

**Size:** medium. That is three small engine Lua functions plus the overlay, two `npc_topic.txt` rows and tests.

---

## 5. Dismiss sound: no change recommended

Neither dismissal path plays a sound: `GameplayDialogController.cpp:3676-3708` (followers) and
`GameplayPartyOverlayInputController.cpp:3414-3426` (party member to the inn). OpenEnroth plays nothing when a MM7
follower is dismissed (`NPCTopics.cpp:790-806`), so followers already match the original. For MM8 party members, check
MM8-Rel.exe's dismiss routine in Rizin first. If it plays a speech or sound, adding it is one line after
`dismissMemberToAdventurersInn` succeeds (`pParty->requestSpeech(...)` or `playCommonUiSound`). Until then, no change.
