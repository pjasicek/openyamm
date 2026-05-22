#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/TextTable.h"
#include "game/audio/SoundCatalog.h"
#include "game/party/SpeechIds.h"
#include "game/tables/CharacterInspectTable.h"
#include "game/tables/FaceAnimationTable.h"
#include "game/tables/PortraitEnums.h"
#include "game/tables/PortraitFrameTable.h"
#include "game/tables/SpeechReactionTable.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/RaceStartingStatsTable.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <optional>
#include <sstream>
#include <string>
#include <unordered_set>
#include <vector>

namespace
{
std::string readSourceTextFile(const std::filesystem::path &path)
{
    std::ifstream stream(path);
    REQUIRE(stream.is_open());

    std::ostringstream buffer;
    buffer << stream.rdbuf();
    return buffer.str();
}

std::vector<std::vector<std::string>> loadRows(const char *pFileName)
{
    const std::string text =
        readSourceTextFile(
            std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/data_tables" / pFileName);

    const std::optional<OpenYAMM::Engine::TextTable> table =
        OpenYAMM::Engine::TextTable::parseTabSeparated(text);

    REQUIRE(table.has_value());

    std::vector<std::vector<std::string>> rows;

    for (size_t index = 0; index < table->getRowCount(); ++index)
    {
        rows.push_back(table->getRow(index));
    }

    return rows;
}

std::string loadDataTableText(const char *pFileName)
{
    return readSourceTextFile(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/data_tables" / pFileName);
}

bool assetTextureExists(const OpenYAMM::Engine::AssetFileSystem &assetFileSystem, const std::string &assetName)
{
    return assetFileSystem.exists("icons/" + assetName + ".bmp")
        || assetFileSystem.exists("icons/" + assetName + ".png");
}

std::string portraitFrameTextureName(const std::string &baseTextureName, uint32_t frameIndex)
{
    if (baseTextureName.size() < 2
        || !std::isdigit(static_cast<unsigned char>(baseTextureName[baseTextureName.size() - 2]))
        || !std::isdigit(static_cast<unsigned char>(baseTextureName[baseTextureName.size() - 1])))
    {
        return baseTextureName;
    }

    char suffix[8] = {};
    std::snprintf(suffix, sizeof(suffix), "%02u", frameIndex);

    std::string textureName = baseTextureName;
    textureName.replace(textureName.size() - 2, 2, suffix);
    return textureName;
}

bool voiceSpeechResolves(
    const OpenYAMM::Game::MergedCharacterVoiceTable &voiceTable,
    const OpenYAMM::Game::SpeechReactionTable &speechReactionTable,
    const OpenYAMM::Game::SoundCatalog &soundCatalog,
    const OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    uint32_t voiceId,
    OpenYAMM::Game::SpeechId speechId)
{
    const OpenYAMM::Game::SpeechReactionEntry *pReaction = speechReactionTable.find(speechId);

    if (pReaction == nullptr)
    {
        return false;
    }

    const std::vector<uint32_t> soundIds = voiceTable.soundIdsForTypes(voiceId, pReaction->soundTypes);

    for (uint32_t soundId : soundIds)
    {
        const std::optional<std::string> virtualPath = soundCatalog.buildVirtualPath(soundId);

        if (virtualPath && assetFileSystem.exists(*virtualPath))
        {
            return true;
        }
    }

    return false;
}

OpenYAMM::Game::ClassSkillTable loadClassSkillTableWithRaceRules()
{
    OpenYAMM::Game::ClassSkillTable classSkillTable;

    REQUIRE(classSkillTable.loadCapsFromRows(loadRows("class_skills.txt")));
    REQUIRE(classSkillTable.loadStartingSkillsFromRows(loadRows("class_starting_skills.txt")));
    REQUIRE(classSkillTable.loadClassMetadataFromRows(loadRows("class_extra.txt")));
    REQUIRE(classSkillTable.loadClassSpellPointMetadataFromRows(loadRows("class_multipliers.txt")));

    OpenYAMM::Game::MergedRaceSkillTable raceSkillTable;
    std::string raceSkillErrorMessage;
    REQUIRE(raceSkillTable.loadFromYaml(loadDataTableText("race_skills.yml"), raceSkillErrorMessage));
    REQUIRE(classSkillTable.applyRaceSkillOverrides(raceSkillTable));

    return classSkillTable;
}
}

TEST_CASE("merged base engine tables load without changing active MM8 runtime tables")
{
    OpenYAMM::Game::MergedClassExtraTable classExtraTable;
    OpenYAMM::Game::MergedCharacterSelectionTable characterSelectionTable;
    OpenYAMM::Game::MergedRaceSkillTable raceSkillTable;
    OpenYAMM::Game::MergedTeacherTopicTable teacherTopicTable;
    OpenYAMM::Game::MergedTeacherAutonoteTable teacherAutonoteTable;
    OpenYAMM::Game::MergedNpcProfessionTable npcProfessionTable;
    OpenYAMM::Game::MergedNpcNameTable npcNameTable;
    OpenYAMM::Game::MergedNpcBtbTable npcBtbTable;
    OpenYAMM::Game::MergedNewsTopicTable newsAreaTopicTable;
    OpenYAMM::Game::MergedNewsTopicTable newsContinentTopicTable;
    OpenYAMM::Game::MergedNewsProfessionTopicTable newsProfessionTopicTable;
    OpenYAMM::Game::MergedMonsterPortraitTable monsterPortraitTable;
    OpenYAMM::Game::MergedPotionSettingTable potionSettingTable;
    OpenYAMM::Game::MergedReagentSettingTable reagentSettingTable;
    OpenYAMM::Game::MergedAdditionalUiTable additionalUiTable;
    OpenYAMM::Game::MergedBolsterFormulaTable bolsterFormulaTable;
    OpenYAMM::Game::MergedBolsterMapTable bolsterMapTable;
    OpenYAMM::Game::MergedBolsterMonsterTable bolsterMonsterTable;
    OpenYAMM::Game::MergedCharacterVoiceTable characterVoiceTable;
    OpenYAMM::Game::MergedClassStartingStatTable classStartingStatTable;
    OpenYAMM::Game::RaceStartingStatsTable raceStartingStatsTable;
    OpenYAMM::Game::MergedComplexItemPictureOffsetTable complexItemPictureOffsetTable;
    OpenYAMM::Game::MergedComplexItemPictureTable complexItemPictureTable;
    OpenYAMM::Game::MergedContinentSettingTable continentSettingTable;
    OpenYAMM::Game::MergedHardwareWaterTextureTable hardwareWaterTextureTable;
    OpenYAMM::Game::MergedHouseExitTable houseExitTable;
    OpenYAMM::Game::MergedHouseRuleTable houseRuleTable;
    OpenYAMM::Game::MergedHistoryTable mm7HistoryTable;
    OpenYAMM::Game::MergedOutdoorTravelTable outdoorTravelTable;
    OpenYAMM::Game::MergedOverlayTable overlayTable;
    OpenYAMM::Game::MergedTownPortalSwitchTable townPortalSwitchTable;
    OpenYAMM::Game::MergedTransportIndexTable transportIndexTable;
    OpenYAMM::Game::MergedTransportLocationTable transportLocationTable;

    REQUIRE(classExtraTable.loadFromRows(loadRows("class_extra.txt")));
    std::string characterSelectionErrorMessage;
    REQUIRE(characterSelectionTable.loadFromYaml(
        loadDataTableText("character_selection.yml"),
        characterSelectionErrorMessage));
    constexpr uint32_t PeasantClassId = 48;
    for (uint32_t raceId = 0; raceId <= 10; ++raceId)
    {
        const std::vector<std::string> *pAllowedClasses = characterSelectionTable.allowedClassesForRaceId(raceId);
        if (pAllowedClasses == nullptr)
        {
            continue;
        }

        CHECK(std::find(pAllowedClasses->begin(), pAllowedClasses->end(), "Peasant") == pAllowedClasses->end());
    }

    for (const OpenYAMM::Game::MergedCharacterSelectionContinent &continent : characterSelectionTable.continents())
    {
        CHECK(
            std::find(
                continent.availableClassIds.begin(),
                continent.availableClassIds.end(),
                PeasantClassId) == continent.availableClassIds.end());
    }

    std::string raceSkillErrorMessage;
    REQUIRE(raceSkillTable.loadFromYaml(loadDataTableText("race_skills.yml"), raceSkillErrorMessage));
    REQUIRE(teacherTopicTable.loadFromRows(loadRows("teacher_topics.txt")));
    REQUIRE(teacherAutonoteTable.loadFromRows(loadRows("teacher_autonotes.txt")));
    REQUIRE(npcProfessionTable.loadFromRows(loadRows("npc_professions.txt")));
    REQUIRE(npcNameTable.loadFromRows(loadRows("npc_names.txt")));
    REQUIRE(npcBtbTable.loadFromRows(loadRows("npc_btb.txt")));
    REQUIRE(newsAreaTopicTable.loadFromRows(loadRows("news_topics_area.txt")));
    REQUIRE(newsContinentTopicTable.loadFromRows(loadRows("news_topics_continent.txt")));
    REQUIRE(newsProfessionTopicTable.loadFromRows(loadRows("news_topics_profession.txt")));
    REQUIRE(monsterPortraitTable.loadFromRows(loadRows("monster_portraits.txt")));
    REQUIRE(potionSettingTable.loadFromRows(loadRows("potion_settings.txt")));
    REQUIRE(reagentSettingTable.loadFromRows(loadRows("reagent_settings.txt")));
    REQUIRE(additionalUiTable.loadFromRows(loadRows("additional_ui.txt")));
    REQUIRE(bolsterFormulaTable.loadFromRows(loadRows("bolster_formulas.txt")));
    REQUIRE(bolsterMapTable.loadFromRows(loadRows("bolster_maps.txt")));
    REQUIRE(bolsterMonsterTable.loadFromRows(loadRows("bolster_monsters.txt")));
    REQUIRE(characterVoiceTable.loadFromRows(loadRows("character_voices.txt")));
    REQUIRE(classStartingStatTable.loadFromRows(loadRows("class_starting_stats.txt")));
    REQUIRE(raceStartingStatsTable.loadFromRows(loadRows("class_starting_stats.txt")));
    const OpenYAMM::Game::RaceStartingStatsTable::Entry *pHumanStartingStats =
        raceStartingStatsTable.get("Human");
    const OpenYAMM::Game::RaceStartingStatsTable::Entry *pDragonStartingStats =
        raceStartingStatsTable.get("Dragon");
    REQUIRE(pHumanStartingStats != nullptr);
    REQUIRE(pDragonStartingStats != nullptr);
    CHECK_EQ(pHumanStartingStats->stats[0], 11);
    CHECK_EQ(pHumanStartingStats->maximumStats[0], 25);
    CHECK_EQ(pHumanStartingStats->addSteps[0], 1);
    CHECK_EQ(pDragonStartingStats->maximumStats[0], 30);
    CHECK_EQ(pDragonStartingStats->maximumStats[6], 30);
    REQUIRE(complexItemPictureOffsetTable.loadFromRows(loadRows("complex_item_picture_offsets.txt")));
    REQUIRE(complexItemPictureTable.loadFromRows(loadRows("complex_item_pictures.txt")));
    REQUIRE(continentSettingTable.loadFromRows(loadRows("continent_settings.txt")));
    REQUIRE(hardwareWaterTextureTable.loadFromRows(loadRows("hw_water_textures.txt")));
    REQUIRE(houseExitTable.loadFromRows(loadRows("house_exits.txt")));
    REQUIRE(houseRuleTable.loadFromRows(loadRows("house_rules.txt")));
    REQUIRE(mm7HistoryTable.loadFromRows(loadRows("english/mm7_history.txt")));
    REQUIRE(outdoorTravelTable.loadFromRows(loadRows("outdoor_travels.txt")));
    REQUIRE(overlayTable.loadFromRows(loadRows("overlay.txt")));
    REQUIRE(townPortalSwitchTable.loadFromRows(loadRows("town_portal_switch.txt")));
    REQUIRE(transportIndexTable.loadFromRows(loadRows("transport_index.txt")));
    REQUIRE(transportLocationTable.loadFromRows(loadRows("transport_locations.txt")));

    REQUIRE_GT(classExtraTable.entries().size(), 50u);
    CHECK_EQ(classExtraTable.entries()[10].note, "Dragon");
    CHECK_EQ(classExtraTable.entries()[10].kind, 4u);

    CHECK_EQ(characterSelectionTable.raceCount(), 11u);
    REQUIRE_EQ(characterSelectionTable.continents().size(), 4u);
    CHECK_EQ(characterSelectionTable.continents()[0].name, "Jadam");

    REQUIRE_EQ(raceSkillTable.overrideCount(), 18u);
    CHECK_EQ(raceSkillTable.overrides()[0].race, "Human");
    CHECK_EQ(raceSkillTable.overrides()[0].skillName, "Learning");
    CHECK_EQ(raceSkillTable.overrides()[0].add, 1);

    REQUIRE_GT(teacherTopicTable.entries().size(), 70u);
    CHECK_EQ(teacherTopicTable.entries()[21].topicId, 971u);
    CHECK_EQ(teacherTopicTable.entries()[21].requiredGold, 2000u);
    REQUIRE(teacherTopicTable.get(971u) != nullptr);
    CHECK_EQ(teacherTopicTable.get(971u)->skillId, 7u);

    CHECK_GT(teacherAutonoteTable.mappingCount(), 100u);
    CHECK_EQ(teacherAutonoteTable.autonoteIdForTopicAndNpc(300u, 440u), 307u);

    REQUIRE_GT(npcProfessionTable.entries().size(), 70u);
    CHECK_EQ(npcProfessionTable.entries()[41].profession, "Gate Master");
    CHECK_EQ(npcProfessionTable.entries()[41].actionTopicId, 1718u);

    CHECK_GT(npcNameTable.maleNameCount(), 100u);
    CHECK_GT(npcNameTable.femaleNameCount(), 100u);
    CHECK_EQ(npcNameTable.maleNames().front(), "Aaron");
    CHECK_EQ(npcNameTable.femaleNames().front(), "Alice");
    CHECK_EQ(npcBtbTable.personalityCount(), 13u);
    const OpenYAMM::Game::MergedNpcBtbEntry *pMerchantBtb = npcBtbTable.get("Merchant");
    REQUIRE(pMerchantBtb != nullptr);
    CHECK_FALSE(pMerchantBtb->acceptBeg);
    CHECK(pMerchantBtb->acceptBribe);
    CHECK(pMerchantBtb->acceptThreat);
    CHECK_EQ(pMerchantBtb->bribeSuccessTextId, 2469u);

    CHECK_GT(newsAreaTopicTable.entries().size(), 200u);
    CHECK_GT(newsContinentTopicTable.entries().size(), 10u);
    CHECK_GT(newsProfessionTopicTable.topicCount(), 400u);

    CHECK_GT(monsterPortraitTable.groupCount(), 50u);
    REQUIRE(monsterPortraitTable.firstPortraitForName("Peasant").has_value());
    REQUIRE(monsterPortraitTable.portraitForName("Peasant", 0).has_value());
    REQUIRE(monsterPortraitTable.portraitForName("Peasant", 1).has_value());
    CHECK_NE(
        *monsterPortraitTable.portraitForName("Peasant", 0),
        *monsterPortraitTable.portraitForName("Peasant", 1));

    REQUIRE_GT(potionSettingTable.entries().size(), 50u);
    CHECK_EQ(potionSettingTable.entries()[1].itemId, 221u);
    CHECK(potionSettingTable.entries()[1].drinkable);
    CHECK_EQ(potionSettingTable.emptyBottleItemId(), 220u);
    CHECK_EQ(potionSettingTable.catalystPotionItemId(), 221u);
    REQUIRE(potionSettingTable.getByItemId(233u) != nullptr);
    CHECK(potionSettingTable.getByItemId(233u)->usable);

    REQUIRE_GT(reagentSettingTable.entries().size(), 40u);
    CHECK_EQ(reagentSettingTable.entries()[0].resultItemId, 222u);
    CHECK_EQ(reagentSettingTable.resultItemIdForReagent(1002u), 222u);

    REQUIRE_EQ(additionalUiTable.entries().size(), 3u);
    CHECK_EQ(additionalUiTable.entries()[0].lodName, "default");

    CHECK_GT(bolsterFormulaTable.entries().size(), 10u);
    CHECK_EQ(bolsterFormulaTable.entries()[0].stat, "HP");

    CHECK_GT(bolsterMapTable.entries().size(), 20u);
    CHECK_EQ(bolsterMapTable.entries()[1].note, "Dagger Wound Island");
    const OpenYAMM::Game::MergedBolsterMapEntry *pHarmondale = bolsterMapTable.findById(63u);
    REQUIRE(pHarmondale != nullptr);
    CHECK(pHarmondale->rain);
    CHECK(pHarmondale->snow);
    const OpenYAMM::Game::MergedBolsterMapEntry *pTulareanForest = bolsterMapTable.findById(65u);
    REQUIRE(pTulareanForest != nullptr);
    CHECK(pTulareanForest->rain);
    CHECK_FALSE(pTulareanForest->snow);
    const OpenYAMM::Game::MergedBolsterMapEntry *pBracadaDesert = bolsterMapTable.findById(67u);
    REQUIRE(pBracadaDesert != nullptr);
    CHECK_FALSE(pBracadaDesert->rain);
    CHECK_FALSE(pBracadaDesert->snow);

    CHECK_GT(bolsterMonsterTable.entries().size(), 100u);
    CHECK_EQ(bolsterMonsterTable.entries()[1].type, "Lizardman");

    CHECK_GT(characterVoiceTable.entries().size(), 40u);
    CHECK_EQ(characterVoiceTable.entries()[0].soundIdsByVoiceSetId[0], 5000u);

    CHECK_GT(classStartingStatTable.entries().size(), 100u);
    CHECK_EQ(classStartingStatTable.entries()[0].raceName, "Human");
    CHECK_EQ(classStartingStatTable.entries()[0].maxValue, 25u);

    REQUIRE_EQ(complexItemPictureOffsetTable.entries().size(), 1u);
    CHECK_EQ(complexItemPictureOffsetTable.entries()[0].portraitId, 26u);

    CHECK_GT(complexItemPictureTable.entries().size(), 10u);
    CHECK_EQ(complexItemPictureTable.entries()[0].itemId, 84u);
    const OpenYAMM::Game::MergedComplexItemPictureEntry *pLeatherJerkin = complexItemPictureTable.get(84u);
    REQUIRE(pLeatherJerkin != nullptr);
    REQUIRE_GE(pLeatherJerkin->points.size(), 5u);
    CHECK_EQ(pLeatherJerkin->points[0].x, 47);
    CHECK_EQ(pLeatherJerkin->points[0].y, 78);
    CHECK_EQ(pLeatherJerkin->points[4].x, -2);
    CHECK_EQ(pLeatherJerkin->points[4].y, 0);
    const OpenYAMM::Game::MergedComplexItemPictureEntry *pWetsuit = complexItemPictureTable.get(1406u);
    REQUIRE(pWetsuit != nullptr);
    REQUIRE_GE(pWetsuit->points.size(), 5u);
    CHECK_EQ(pWetsuit->points[0].x, 0);
    CHECK_EQ(pWetsuit->points[0].y, -1);
    CHECK_EQ(pWetsuit->points[2].x, 9);
    CHECK_EQ(pWetsuit->points[2].y, 23);
    const OpenYAMM::Game::MergedComplexItemPictureEntry *pTravelersCloak = complexItemPictureTable.get(122u);
    REQUIRE(pTravelersCloak != nullptr);
    REQUIRE_EQ(pTravelersCloak->points.size(), 6u);
    CHECK_EQ(pTravelersCloak->points[4].x, 43);
    CHECK_EQ(pTravelersCloak->points[4].y, 117);
    CHECK_EQ(pTravelersCloak->points[5].x, 0);
    CHECK_EQ(pTravelersCloak->points[5].y, 0);
    CHECK(complexItemPictureTable.get(999999u) == nullptr);

    REQUIRE_EQ(continentSettingTable.entries().size(), 4u);
    CHECK_EQ(continentSettingTable.entries()[0].note, "Jadam");
    const OpenYAMM::Game::MergedContinentSettingEntry *pAntagarichContinent =
        continentSettingTable.findById(2u);
    REQUIRE(pAntagarichContinent != nullptr);
    CHECK_EQ(pAntagarichContinent->note, "Antagarich");
    CHECK_EQ(pAntagarichContinent->deathMovie, "7losegame");
    CHECK_EQ(pAntagarichContinent->deathMap1, "7out01.odm");
    CHECK_EQ(pAntagarichContinent->deathMap1X, 12552);
    CHECK_EQ(pAntagarichContinent->deathMap1Y, 800);
    CHECK_EQ(pAntagarichContinent->deathMap1Z, 193);
    CHECK_EQ(pAntagarichContinent->deathMap1Direction, 512);
    CHECK_EQ(pAntagarichContinent->deathMap2, "7out02.odm");
    CHECK_EQ(pAntagarichContinent->deathMap2X, -16832);
    CHECK_EQ(pAntagarichContinent->deathMap2Y, 12512);
    CHECK_EQ(pAntagarichContinent->deathMap2Z, 372);
    CHECK_EQ(pAntagarichContinent->deathMap2Direction, 0);

    REQUIRE_EQ(hardwareWaterTextureTable.entries().size(), 6u);
    CHECK_EQ(hardwareWaterTextureTable.entries()[0].hardwareTexturePrefix, "7hdwtr");

    REQUIRE_GT(houseExitTable.data().npcPictureIds.size(), 6u);
    CHECK_EQ(houseExitTable.data().exits[0].mapName, "sewer.blv");

    CHECK_GT(houseRuleTable.sections().size(), 5u);
    CHECK_EQ(houseRuleTable.sections()[0].name, "Weapon shops Standart");

    CHECK_GT(mm7HistoryTable.entries().size(), 20u);
    CHECK_EQ(mm7HistoryTable.entries()[0].pageTitle, "Author's Forward");

    CHECK_GT(outdoorTravelTable.entries().size(), 20u);
    CHECK_EQ(outdoorTravelTable.entries()[0].keyMap, "7out02.odm");

    CHECK_GT(overlayTable.entries().size(), 10u);
    CHECK_EQ(overlayTable.entries()[0].id, 1020u);

    CHECK_GT(townPortalSwitchTable.groups().size(), 2u);
    CHECK_EQ(townPortalSwitchTable.groups()[0].topicId, 300u);
    const auto antagarichTownPortalGroup = std::find_if(
        townPortalSwitchTable.groups().begin(),
        townPortalSwitchTable.groups().end(),
        [](const OpenYAMM::Game::MergedTownPortalSwitchGroup &group)
        {
            return group.name == "Antagrich";
        });
    REQUIRE(antagarichTownPortalGroup != townPortalSwitchTable.groups().end());
    CHECK_EQ(antagarichTownPortalGroup->topicId, 307u);
    REQUIRE_EQ(antagarichTownPortalGroup->destinations.size(), 6u);
    CHECK_EQ(antagarichTownPortalGroup->destinations[0].description, "Castle Harmondale");
    CHECK_EQ(antagarichTownPortalGroup->destinations[0].qbitIndex, 718u);
    CHECK_EQ(antagarichTownPortalGroup->destinations[1].description, "Tularean Forest");
    CHECK_EQ(antagarichTownPortalGroup->destinations[1].qbitIndex, 719u);
    CHECK_EQ(antagarichTownPortalGroup->destinations[2].description, "City of Steadwick");
    CHECK_EQ(antagarichTownPortalGroup->destinations[2].qbitIndex, 720u);
    CHECK_EQ(antagarichTownPortalGroup->destinations[3].description, "Nighon");
    CHECK_EQ(antagarichTownPortalGroup->destinations[3].qbitIndex, 721u);
    CHECK_EQ(antagarichTownPortalGroup->destinations[4].description, "Celeste");
    CHECK_EQ(antagarichTownPortalGroup->destinations[4].qbitIndex, 722u);
    CHECK_EQ(antagarichTownPortalGroup->destinations[5].description, "The Pit");
    CHECK_EQ(antagarichTownPortalGroup->destinations[5].qbitIndex, 723u);

    const auto jadameTownPortalGroup = std::find_if(
        townPortalSwitchTable.groups().begin(),
        townPortalSwitchTable.groups().end(),
        [](const OpenYAMM::Game::MergedTownPortalSwitchGroup &group)
        {
            return group.name == "townport";
        });
    REQUIRE(jadameTownPortalGroup != townPortalSwitchTable.groups().end());
    CHECK_EQ(jadameTownPortalGroup->topicId, 300u);
    REQUIRE_EQ(jadameTownPortalGroup->destinations.size(), 6u);
    CHECK_EQ(jadameTownPortalGroup->destinations[0].description, "Alvar");
    CHECK_EQ(jadameTownPortalGroup->destinations[0].qbitIndex, 301u);
    CHECK_EQ(jadameTownPortalGroup->destinations[1].description, "Ravenshore");
    CHECK_EQ(jadameTownPortalGroup->destinations[1].qbitIndex, 302u);
    CHECK_EQ(jadameTownPortalGroup->destinations[5].description, "Daggerwound islands");
    CHECK_EQ(jadameTownPortalGroup->destinations[5].qbitIndex, 306u);

    const auto dimensionDoorGroup = std::find_if(
        townPortalSwitchTable.groups().begin(),
        townPortalSwitchTable.groups().end(),
        [](const OpenYAMM::Game::MergedTownPortalSwitchGroup &group)
        {
            return group.name == "TPGlobal";
        });
    REQUIRE(dimensionDoorGroup != townPortalSwitchTable.groups().end());
    CHECK_EQ(dimensionDoorGroup->topicId, 309u);
    REQUIRE_EQ(dimensionDoorGroup->destinations.size(), 6u);
    CHECK_EQ(dimensionDoorGroup->destinations[0].description, "Jadame");
    CHECK_EQ(dimensionDoorGroup->destinations[0].iconName, "TPJadam1");
    CHECK_EQ(dimensionDoorGroup->destinations[2].description, "Antagarich");
    CHECK_EQ(dimensionDoorGroup->destinations[2].iconName, "TPAntag1");
    CHECK_EQ(dimensionDoorGroup->destinations[4].description, "Enroth");
    CHECK_EQ(dimensionDoorGroup->destinations[4].iconName, "TPEnroth1");

    CHECK_GE(transportIndexTable.entries().size(), 20u);
    CHECK_EQ(transportIndexTable.entries()[0].houseEventId, 54u);

    CHECK_GT(transportLocationTable.entries().size(), 20u);
    CHECK_EQ(transportLocationTable.entries()[0].mapName, "Out03.odm");
}

TEST_CASE("race skill rules apply additive effective caps without changing class caps")
{
    const OpenYAMM::Game::ClassSkillTable classSkillTable = loadClassSkillTableWithRaceRules();

    CHECK_EQ(classSkillTable.getClassCap("Archer", "Learning"), OpenYAMM::Game::SkillMastery::Master);
    CHECK_EQ(
        classSkillTable.getEffectiveCap("Archer", 0, "Learning"),
        OpenYAMM::Game::SkillMastery::Grandmaster);
    CHECK_EQ(
        classSkillTable.getEffectiveCap("Archer", 4, "Learning"),
        OpenYAMM::Game::SkillMastery::Master);

    CHECK_EQ(classSkillTable.getClassCap("Troll", "Regeneration"), OpenYAMM::Game::SkillMastery::Master);
    CHECK_EQ(
        classSkillTable.getEffectiveCap("Troll", 4, "Regeneration"),
        OpenYAMM::Game::SkillMastery::Grandmaster);
    CHECK_EQ(
        classSkillTable.getEffectiveCap("Peasant", 4, "Regeneration"),
        OpenYAMM::Game::SkillMastery::None);
}

TEST_CASE("character inspect table loads class descriptions")
{
    OpenYAMM::Game::CharacterInspectTable inspectTable;

    REQUIRE(inspectTable.loadClassRows(loadRows("english/class.txt")));

    const OpenYAMM::Game::ClassInspectEntry *pKnight = inspectTable.getClass("Knight");
    REQUIRE(pKnight != nullptr);
    CHECK_EQ(pKnight->name, "Knight");
    CHECK(pKnight->description.find("martial skills") != std::string::npos);

    const OpenYAMM::Game::ClassInspectEntry *pWarriorMage = inspectTable.getClass("Warrior Mage");
    REQUIRE(pWarriorMage != nullptr);
    CHECK_EQ(pWarriorMage->name, "Warrior Mage");
    CHECK(pWarriorMage->description.find("first Archer promotion") != std::string::npos);
}

TEST_CASE("race skill rules grant minimum caps and honor class-kind exceptions")
{
    const OpenYAMM::Game::ClassSkillTable classSkillTable = loadClassSkillTableWithRaceRules();

    CHECK_EQ(classSkillTable.getClassCap("Knight", "VampireAbility"), OpenYAMM::Game::SkillMastery::None);
    CHECK_EQ(
        classSkillTable.getEffectiveCap("Knight", 1, "VampireAbility"),
        OpenYAMM::Game::SkillMastery::Expert);

    CHECK_EQ(classSkillTable.getClassCap("Knight", "Axe"), OpenYAMM::Game::SkillMastery::Expert);
    CHECK_EQ(
        classSkillTable.getEffectiveCap("Knight", 3, "Axe"),
        OpenYAMM::Game::SkillMastery::Master);

    CHECK_EQ(classSkillTable.getClassCap("Cleric", "Axe"), OpenYAMM::Game::SkillMastery::None);
    CHECK_EQ(
        classSkillTable.getEffectiveCap("Cleric", 3, "Axe"),
        OpenYAMM::Game::SkillMastery::None);
}

TEST_CASE("race skill warrior exception uses class spell point metadata")
{
    const OpenYAMM::Game::ClassSkillTable classSkillTable = loadClassSkillTableWithRaceRules();

    CHECK_EQ(classSkillTable.getClassCap("Knight", "Meditation"), OpenYAMM::Game::SkillMastery::None);
    CHECK_EQ(
        classSkillTable.getEffectiveCap("Knight", 1, "Meditation"),
        OpenYAMM::Game::SkillMastery::Expert);

    CHECK_EQ(classSkillTable.getClassCap("Thief", "Meditation"), OpenYAMM::Game::SkillMastery::None);
    CHECK_EQ(
        classSkillTable.getEffectiveCap("Thief", 1, "Meditation"),
        OpenYAMM::Game::SkillMastery::Expert);

    CHECK_EQ(classSkillTable.getClassCap("Rogue", "Meditation"), OpenYAMM::Game::SkillMastery::None);
    CHECK_EQ(
        classSkillTable.getEffectiveCap("Rogue", 1, "Meditation"),
        OpenYAMM::Game::SkillMastery::None);
}

TEST_CASE("race granted skills become creation choices but not default skills")
{
    const OpenYAMM::Game::ClassSkillTable classSkillTable = loadClassSkillTableWithRaceRules();

    CHECK_EQ(
        classSkillTable.getStartingSkillAvailability("Knight", "VampireAbility"),
        OpenYAMM::Game::StartingSkillAvailability::None);
    CHECK_EQ(
        classSkillTable.getEffectiveStartingSkillAvailability("Knight", 1, "VampireAbility"),
        OpenYAMM::Game::StartingSkillAvailability::CanLearn);

    const std::vector<OpenYAMM::Game::CharacterSkill> defaultSkills =
        classSkillTable.getDefaultSkillsForCharacter("Knight", 1);
    CHECK_EQ(
        std::find_if(
            defaultSkills.begin(),
            defaultSkills.end(),
            [](const OpenYAMM::Game::CharacterSkill &skill)
            {
                return skill.name == "VampireAbility";
            }),
        defaultSkills.end());
}

TEST_CASE("Antagarich continent skies referenced by merged tables are available")
{
    OpenYAMM::Game::MergedContinentSettingTable continentSettingTable;
    REQUIRE(continentSettingTable.loadFromRows(loadRows("continent_settings.txt")));

    const OpenYAMM::Game::MergedContinentSettingEntry *pAntagarichContinent =
        continentSettingTable.findById(2u);
    REQUIRE(pAntagarichContinent != nullptr);
    REQUIRE_FALSE(pAntagarichContinent->skies.empty());

    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::filesystem::path assetsRoot = sourceRoot / "assets_dev";
    REQUIRE(assetFileSystem.initialize(sourceRoot, assetsRoot, OpenYAMM::Engine::AssetScaleTier::X1));
    REQUIRE(assetFileSystem.switchActiveWorld("mm7"));

    for (const std::string &skyTextureName : pAntagarichContinent->skies)
    {
        const bool hasBmpSkyTexture = assetFileSystem.exists("sky_textures/" + skyTextureName + ".bmp");
        const bool hasPngSkyTexture = assetFileSystem.exists("sky_textures/" + skyTextureName + ".png");
        const bool hasSkyTexture = hasBmpSkyTexture || hasPngSkyTexture;

        CHECK_MESSAGE(hasSkyTexture, skyTextureName.c_str());
    }
}

TEST_CASE("merged character portrait prefixes resolve all standard expression frames")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::filesystem::path assetsRoot = sourceRoot / "assets_dev";
    REQUIRE(assetFileSystem.initialize(sourceRoot, assetsRoot, OpenYAMM::Engine::AssetScaleTier::X1));

    std::unordered_set<uint32_t> portraitFrameIndices;

    for (const std::vector<std::string> &row : loadRows("portrait_frame_data.txt"))
    {
        if (row.size() < 2 || row[0].empty() || !std::isdigit(static_cast<unsigned char>(row[0][0])))
        {
            continue;
        }

        portraitFrameIndices.insert(static_cast<uint32_t>(std::stoul(row[1])));
    }

    REQUIRE_GT(portraitFrameIndices.size(), 50u);

    size_t checkedPortraits = 0;

    for (const std::vector<std::string> &row : loadRows("character_data.txt"))
    {
        if (row.size() < 20 || row[0].empty() || !std::isdigit(static_cast<unsigned char>(row[0][0]))
            || row[2] == "-1")
        {
            continue;
        }

        const std::string facePrefix = row[19];

        if (facePrefix.empty() || facePrefix == "none")
        {
            continue;
        }

        ++checkedPortraits;
        const std::string baseTextureName = facePrefix + "01";
        CAPTURE(row[0]);
        CAPTURE(baseTextureName);
        CHECK_MESSAGE(assetTextureExists(assetFileSystem, baseTextureName), baseTextureName.c_str());

        for (uint32_t frameIndex : portraitFrameIndices)
        {
            const std::string frameTextureName = portraitFrameTextureName(baseTextureName, frameIndex);
            CHECK_MESSAGE(assetTextureExists(assetFileSystem, frameTextureName), frameTextureName.c_str());
        }
    }

    CHECK_GT(checkedPortraits, 70u);
}

TEST_CASE("merged character speech face animations have concrete expression mappings")
{
    OpenYAMM::Game::FaceAnimationTable faceAnimationTable;
    REQUIRE(faceAnimationTable.loadFromRows(loadRows("face_animations.txt")));

    size_t checkedAnimations = 0;

    for (const std::vector<std::string> &row : loadRows("character_speech_events.txt"))
    {
        if (row.size() < 4 || row[0] == "Id" || row[3].empty())
        {
            continue;
        }

        const std::optional<OpenYAMM::Game::FaceAnimationId> faceAnimationId =
            OpenYAMM::Game::faceAnimationIdFromName(row[3]);
        CAPTURE(row[0]);
        CAPTURE(row[3]);
        REQUIRE(faceAnimationId.has_value());
        CHECK(faceAnimationTable.find(*faceAnimationId) != nullptr);
        ++checkedAnimations;
    }

    CHECK_GT(checkedAnimations, 40u);
}

TEST_CASE("merged startable character voices resolve core speech sounds")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::filesystem::path assetsRoot = sourceRoot / "assets_dev";
    REQUIRE(assetFileSystem.initialize(sourceRoot, assetsRoot, OpenYAMM::Engine::AssetScaleTier::X1));

    OpenYAMM::Game::SoundCatalog soundCatalog;
    std::string soundCatalogError;
    REQUIRE(soundCatalog.loadFromScopedRows(loadRows("sounds.txt"), {}, soundCatalogError));
    soundCatalog.initializeVirtualPathIndex(assetFileSystem);

    OpenYAMM::Game::MergedCharacterVoiceTable voiceTable;
    REQUIRE(voiceTable.loadFromRows(loadRows("character_voices.txt")));

    OpenYAMM::Game::SpeechReactionTable speechReactionTable;
    REQUIRE(speechReactionTable.loadFromRows(loadRows("character_speech_events.txt")));

    const std::array<OpenYAMM::Game::SpeechId, 10> checkedSpeechIds = {{
        OpenYAMM::Game::SpeechId::SelectCharacter,
        OpenYAMM::Game::SpeechId::DamageMinor,
        OpenYAMM::Game::SpeechId::DamageMajor,
        OpenYAMM::Game::SpeechId::DoorLocked,
        OpenYAMM::Game::SpeechId::CantLearnSpell,
        OpenYAMM::Game::SpeechId::LearnSpell,
        OpenYAMM::Game::SpeechId::KillWeakEnemy,
        OpenYAMM::Game::SpeechId::CantEquip,
        OpenYAMM::Game::SpeechId::StoreClosed,
        OpenYAMM::Game::SpeechId::NotEnoughGold,
    }};
    std::unordered_set<uint32_t> checkedVoiceIds;

    for (const std::vector<std::string> &row : loadRows("character_data.txt"))
    {
        if (row.size() < 6 || row[0].empty() || !std::isdigit(static_cast<unsigned char>(row[0][0]))
            || row[2] == "-1" || row[5] != "x")
        {
            continue;
        }

        const uint32_t voiceId = static_cast<uint32_t>(std::stoul(row[3]));

        if (!checkedVoiceIds.insert(voiceId).second)
        {
            continue;
        }

        for (OpenYAMM::Game::SpeechId speechId : checkedSpeechIds)
        {
            CAPTURE(voiceId);
            CHECK(voiceSpeechResolves(voiceTable, speechReactionTable, soundCatalog, assetFileSystem, voiceId, speechId));
        }
    }

    CHECK_GT(checkedVoiceIds.size(), 50u);
}

TEST_CASE("merged character presentation-only reactions have no speech sounds")
{
    OpenYAMM::Game::SpeechReactionTable speechReactionTable;
    REQUIRE(speechReactionTable.loadFromRows(loadRows("character_speech_events.txt")));

    const std::array<OpenYAMM::Game::SpeechId, 8> portraitOnlySpeechIds = {{
        OpenYAMM::Game::SpeechId::Shoot,
        OpenYAMM::Game::SpeechId::AttackHit,
        OpenYAMM::Game::SpeechId::AttackMiss,
        OpenYAMM::Game::SpeechId::FoundItem,
        OpenYAMM::Game::SpeechId::StatBonusIncreased,
        OpenYAMM::Game::SpeechId::StatBaseIncreased,
        OpenYAMM::Game::SpeechId::QuestGot,
        OpenYAMM::Game::SpeechId::AwardGot,
    }};

    for (OpenYAMM::Game::SpeechId speechId : portraitOnlySpeechIds)
    {
        const OpenYAMM::Game::SpeechReactionEntry *pReaction = speechReactionTable.find(speechId);
        REQUIRE(pReaction != nullptr);
        CHECK(pReaction->soundTypes.empty());
        CHECK(pReaction->faceAnimationId.has_value());
    }
}
