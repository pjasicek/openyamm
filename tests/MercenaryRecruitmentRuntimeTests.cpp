#include "doctest/doctest.h"

#include "game/gameplay/MercenaryRecruitmentRuntime.h"
#include "game/maps/SaveGame.h"
#include "game/party/SpellSchool.h"

#include "tests/HouseDialogueTestHarness.h"
#include "tests/RegressionGameData.h"

#include <algorithm>
#include <filesystem>
#include <set>
#include <string>
#include <tuple>

namespace
{
OpenYAMM::Game::MapStatsEntry makeRavenshoreMap()
{
    OpenYAMM::Game::MapStatsEntry map = {};
    map.id = 2;
    map.worldId = "mm8";
    map.name = "Ravenshore";
    map.fileName = "out02.odm";
    map.treasureLevel = 2;
    map.mergedContinentId = 3;
    map.isTopLevelArea = true;
    return map;
}

OpenYAMM::Game::MercenaryRecruitmentTables makeRecruitmentTables(
    const OpenYAMM::Tests::RegressionGameData &gameData)
{
    return OpenYAMM::Game::MercenaryRecruitmentTables{
        .pHouseTable = &gameData.houseTable,
        .pNpcNameTable = &gameData.mergedNpcNameTable,
        .pCharacterDollTable = &gameData.characterDollTable,
        .pClassSkillTable = &gameData.classSkillTable,
        .pClassMultiplierTable = &gameData.classMultiplierTable,
        .pRaceStartingStatsTable = nullptr,
        .pItemTable = &gameData.itemTable,
        .pStandardItemEnchantTable = &gameData.standardItemEnchantTable,
        .pSpecialItemEnchantTable = &gameData.specialItemEnchantTable,
        .pSpellTable = &gameData.spellTable,
    };
}

size_t findActionByLabel(const OpenYAMM::Game::EventDialogContent &dialog, const std::string &label)
{
    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        if (dialog.actions[actionIndex].label == label)
        {
            return actionIndex;
        }
    }

    return static_cast<size_t>(-1);
}

bool hasAnyEquippedItem(const OpenYAMM::Game::Character &character)
{
    return character.equipment.offHand != 0
        || character.equipment.mainHand != 0
        || character.equipment.bow != 0
        || character.equipment.armor != 0
        || character.equipment.helm != 0
        || character.equipment.belt != 0
        || character.equipment.cloak != 0
        || character.equipment.gauntlets != 0
        || character.equipment.boots != 0
        || character.equipment.amulet != 0
        || character.equipment.ring1 != 0
        || character.equipment.ring2 != 0
        || character.equipment.ring3 != 0
        || character.equipment.ring4 != 0
        || character.equipment.ring5 != 0
        || character.equipment.ring6 != 0;
}

bool hasAnySpellSkill(const OpenYAMM::Game::Character &character)
{
    for (const auto &[skillName, skill] : character.skills)
    {
        if (skill.level > 0
            && skill.mastery != OpenYAMM::Game::SkillMastery::None
            && OpenYAMM::Game::spellIdRangeForMagicSkill(skillName).has_value())
        {
            return true;
        }
    }

    return false;
}

bool dialogContainsText(const OpenYAMM::Game::EventDialogContent &dialog, const std::string &text)
{
    for (const std::string &line : dialog.lines)
    {
        if (line.find(text) != std::string::npos)
        {
            return true;
        }
    }

    return false;
}
}

TEST_CASE("Mercenary recruitment house detection uses actual house type not raw type index")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    const OpenYAMM::Game::MapStatsEntry map = makeRavenshoreMap();

    const std::optional<uint32_t> houseId =
        OpenYAMM::Game::findMercenaryRecruitmentHouseId(map, gameData.houseTable);

    REQUIRE(houseId.has_value());
    CHECK(*houseId == 229);
}

TEST_CASE("MMerge-style mercenary recruits are generated into current-map recruitment houses")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    OpenYAMM::Game::MapStatsEntry map = makeRavenshoreMap();

    const bool placed = OpenYAMM::Game::refreshMercenaryRecruitmentForCurrentMap(
        map,
        harness.party(),
        harness.eventRuntimeState(),
        540.0f,
        makeRecruitmentTables(gameData));

    REQUIRE(placed);
    REQUIRE(harness.eventRuntimeState().generatedMercenaryRecruitsByNpcId.size() == 1);

    const auto recruitIt = harness.eventRuntimeState().generatedMercenaryRecruitsByNpcId.begin();
    const uint32_t npcId = recruitIt->first;
    CHECK(OpenYAMM::Game::isGeneratedMercenaryNpcId(npcId));
    CHECK(recruitIt->second.rosterId == OpenYAMM::Game::generatedMercenaryRosterIdForNpcId(npcId));
    CHECK(recruitIt->second.houseId != 0);
    CHECK(recruitIt->second.character.rosterId == recruitIt->second.rosterId);
    CHECK_FALSE(recruitIt->second.character.name.empty());
    CHECK_FALSE(recruitIt->second.character.className.empty());
    CHECK(recruitIt->second.character.level >= 1);
    CHECK(recruitIt->second.character.maxHealth > 0);
    CHECK(recruitIt->second.character.characterDataId == recruitIt->second.character.portraitPictureId + 1);
    CHECK_FALSE(recruitIt->second.character.portraitTextureName.empty());
    CHECK(recruitIt->second.character.portraitTextureName.ends_with("01"));
    CHECK_FALSE(recruitIt->second.character.skills.empty());
    CHECK(hasAnyEquippedItem(recruitIt->second.character));
    CHECK(hasAnySpellSkill(recruitIt->second.character) == !recruitIt->second.character.knownSpellIds.empty());
    CHECK(harness.eventRuntimeState().npcHouseOverrides.at(npcId) == recruitIt->second.houseId);
    CHECK(harness.eventRuntimeState().npcNameOverrides.at(npcId) == recruitIt->second.character.name);
    CHECK(harness.eventRuntimeState().npcPictureOverrides.at(npcId) == recruitIt->second.npcPictureId);
}

TEST_CASE("Generated mercenaries vary between games and refresh once per calendar month")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    const OpenYAMM::Game::MapStatsEntry map = makeRavenshoreMap();
    const OpenYAMM::Game::MercenaryRecruitmentTables tables = makeRecruitmentTables(gameData);
    std::set<std::tuple<std::string, std::string, uint32_t>> identities;
    for (int game = 0; game < 8; ++game)
    {
        OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
        OpenYAMM::Game::EventRuntimeState &state = harness.eventRuntimeState();
        REQUIRE(OpenYAMM::Game::refreshMercenaryRecruitmentForCurrentMap(
            map, harness.party(), state, 540.0f, tables));
        const OpenYAMM::Game::EventRuntimeState::GeneratedMercenaryRecruit first =
            state.generatedMercenaryRecruitsByNpcId.begin()->second;
        identities.emplace(first.character.name, first.character.className, first.npcPictureId);
        REQUIRE(OpenYAMM::Game::refreshMercenaryRecruitmentForCurrentMap(
            map, harness.party(), state, 28 * 24 * 60 - 1.0f, tables));
        CHECK_EQ(state.generatedMercenaryRecruitsByNpcId.at(first.npcId).character.name, first.character.name);
        CHECK_EQ(state.generatedMercenaryRecruitsByNpcId.at(first.npcId).character.className,
            first.character.className);
        CHECK_EQ(state.generatedMercenaryRecruitsByNpcId.at(first.npcId).npcPictureId, first.npcPictureId);
        REQUIRE(OpenYAMM::Game::refreshMercenaryRecruitmentForCurrentMap(
            map, harness.party(), state, 28 * 24 * 60.0f, tables));
        CHECK_EQ(state.namedMapVars.at("MMerge.Mercenaries.RefillMonth"), 1);
        REQUIRE_EQ(state.generatedMercenaryRecruitsByNpcId.size(), 1u);
        const OpenYAMM::Game::EventRuntimeState::GeneratedMercenaryRecruit refreshed =
            state.generatedMercenaryRecruitsByNpcId.at(first.npcId);
        REQUIRE(OpenYAMM::Game::refreshMercenaryRecruitmentForCurrentMap(
            map, harness.party(), state, 28 * 24 * 60 + 1.0f, tables));
        CHECK_EQ(state.generatedMercenaryRecruitsByNpcId.at(first.npcId).character.name, refreshed.character.name);

        REQUIRE(harness.party().addAdventurersInnMember(refreshed.character, refreshed.portraitPictureId));
        state.generatedMercenaryRecruitsByNpcId.erase(first.npcId);
        state.unavailableNpcIds.insert(first.npcId);
        CHECK_FALSE(OpenYAMM::Game::refreshMercenaryRecruitmentForCurrentMap(
            map, harness.party(), state, 28 * 24 * 60 + 2.0f, tables));
        REQUIRE(OpenYAMM::Game::refreshMercenaryRecruitmentForCurrentMap(
            map, harness.party(), state, 2 * 28 * 24 * 60.0f, tables));
        CHECK_FALSE(state.generatedMercenaryRecruitsByNpcId.contains(first.npcId));
        REQUIRE_EQ(harness.party().adventurersInnMembers().size(), 1u);
        CHECK_EQ(harness.party().adventurersInnMembers().front().character.name, refreshed.character.name);
    }
    CHECK_GT(identities.size(), 1u);
}

TEST_CASE("Generated mercenary residents can join the party through shared house dialogue")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    OpenYAMM::Game::MapStatsEntry map = makeRavenshoreMap();
    harness.setCurrentMap(map);

    REQUIRE(OpenYAMM::Game::refreshMercenaryRecruitmentForCurrentMap(
        map,
        harness.party(),
        harness.eventRuntimeState(),
        540.0f,
        makeRecruitmentTables(gameData)));

    const OpenYAMM::Game::EventRuntimeState::GeneratedMercenaryRecruit recruit =
        harness.eventRuntimeState().generatedMercenaryRecruitsByNpcId.begin()->second;
    const size_t initialPartySize = harness.party().members().size();

    const OpenYAMM::Game::EventDialogContent &houseDialog = harness.openHouseDialog(recruit.houseId);
    const size_t residentAction = findActionByLabel(houseDialog, recruit.character.name);
    REQUIRE(residentAction != static_cast<size_t>(-1));

    const OpenYAMM::Game::EventDialogContent &npcDialog = harness.executeAndPresent(residentAction);
    const size_t joinAction = findActionByLabel(npcDialog, "Join");
    REQUIRE(joinAction != static_cast<size_t>(-1));

    const OpenYAMM::Game::EventDialogContent &offerDialog = harness.executeAndPresent(joinAction);
    CHECK(dialogContainsText(offerDialog, "Good tidings. I am " + recruit.character.name));
    CHECK(dialogContainsText(offerDialog, OpenYAMM::Game::displayClassName(recruit.character.className)));
    const size_t yesAction = findActionByLabel(offerDialog, "Yes");
    REQUIRE(yesAction != static_cast<size_t>(-1));

    harness.executeAndPresent(yesAction);

    REQUIRE(harness.party().members().size() == initialPartySize + 1);
    const OpenYAMM::Game::Character &joined = harness.party().members().back();
    CHECK(joined.rosterId == recruit.rosterId);
    CHECK(joined.name == recruit.character.name);
    CHECK(harness.eventRuntimeState().generatedMercenaryRecruitsByNpcId.count(recruit.npcId) == 0);
    CHECK(harness.eventRuntimeState().unavailableNpcIds.contains(recruit.npcId));
    CHECK(harness.eventRuntimeState().npcHouseOverrides.count(recruit.npcId) == 0);
}

TEST_CASE("Generated mercenary recruits persist in event runtime saves")
{
    OpenYAMM::Game::EventRuntimeState state = {};
    OpenYAMM::Game::EventRuntimeState::GeneratedMercenaryRecruit recruit = {};
    recruit.npcId = 303;
    recruit.rosterId = 42;
    recruit.houseId = 756;
    recruit.portraitPictureId = 23;
    recruit.npcPictureId = 1200;
    recruit.character.name = "Persisted Mercenary";
    recruit.character.className = "Knight";
    recruit.character.rosterId = recruit.rosterId;
    recruit.character.level = 12;
    recruit.character.portraitPictureId = recruit.portraitPictureId;
    recruit.character.portraitTextureName = "PC24-01";
    state.generatedMercenaryRecruitsByNpcId[recruit.npcId] = recruit;
    state.npcHouseOverrides[recruit.npcId] = recruit.houseId;
    state.npcNameOverrides[recruit.npcId] = recruit.character.name;
    state.npcPictureOverrides[recruit.npcId] = recruit.npcPictureId;
    state.namedMapVars["MMerge.Mercenaries.RefillMonth"] = 0;

    OpenYAMM::Game::GameSaveData saveData = {};
    saveData.hasOutdoorRuntimeState = true;
    saveData.outdoorWorld.eventRuntimeState = state;

    const std::filesystem::path savePath =
        std::filesystem::temp_directory_path() / "openyamm_generated_mercenary_save_test.oys";
    std::string error;
    REQUIRE(OpenYAMM::Game::saveGameDataToPath(savePath, saveData, error));

    const std::optional<OpenYAMM::Game::GameSaveData> loaded =
        OpenYAMM::Game::loadGameDataFromPath(savePath, error);
    std::filesystem::remove(savePath);

    REQUIRE(loaded.has_value());
    REQUIRE(loaded->outdoorWorld.eventRuntimeState.has_value());
    const OpenYAMM::Game::EventRuntimeState &loadedState = *loaded->outdoorWorld.eventRuntimeState;
    REQUIRE(loadedState.generatedMercenaryRecruitsByNpcId.count(recruit.npcId) == 1);
    const OpenYAMM::Game::EventRuntimeState::GeneratedMercenaryRecruit &loadedRecruit =
        loadedState.generatedMercenaryRecruitsByNpcId.at(recruit.npcId);
    CHECK(loadedRecruit.character.name == recruit.character.name);
    CHECK(loadedRecruit.character.level == recruit.character.level);
    CHECK(loadedRecruit.houseId == recruit.houseId);
    CHECK(loadedRecruit.portraitPictureId == recruit.portraitPictureId);
    CHECK(loadedRecruit.npcPictureId == recruit.npcPictureId);
    CHECK(loadedState.npcHouseOverrides.at(recruit.npcId) == recruit.houseId);
    CHECK_EQ(loadedState.namedMapVars.at("MMerge.Mercenaries.RefillMonth"), 0);

    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    OpenYAMM::Game::EventRuntimeState restoredState = loadedState;
    REQUIRE(OpenYAMM::Game::refreshMercenaryRecruitmentForCurrentMap(
        makeRavenshoreMap(), harness.party(), restoredState, 540.0f, makeRecruitmentTables(gameData)));
    CHECK_EQ(restoredState.generatedMercenaryRecruitsByNpcId.at(recruit.npcId).character.name, recruit.character.name);

    saveData.outdoorWorld.eventRuntimeState->namedMapVars.erase("MMerge.Mercenaries.RefillMonth");
    saveData.savedGameMinutes = 90000.0f;
    OpenYAMM::Game::migrateLegacyNpcRosters(saveData);
    REQUIRE(OpenYAMM::Game::refreshMercenaryRecruitmentForCurrentMap(
        makeRavenshoreMap(), harness.party(), *saveData.outdoorWorld.eventRuntimeState,
        saveData.savedGameMinutes, makeRecruitmentTables(gameData)));
    CHECK_EQ(saveData.outdoorWorld.eventRuntimeState->generatedMercenaryRecruitsByNpcId.at(recruit.npcId)
        .character.name, recruit.character.name);
}
