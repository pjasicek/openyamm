#include "tests/RegressionGameData.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/TextTable.h"
#include "game/arcomage/ArcomageLoader.h"
#include "game/tables/MapStats.h"
#include "game/tables/MergedBaseTables.h"

#include <filesystem>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Tests
{
namespace
{
struct RegressionGameDataState
{
    bool loaded = false;
    RegressionGameData data = {};
    std::string failure;
};

std::string engineDataTablePath(std::string_view fileName)
{
    return "engine/data_tables/" + std::string(fileName);
}

std::string engineEnglishDataTablePath(std::string_view fileName)
{
    return "engine/data_tables/english/" + std::string(fileName);
}

std::string prependLuaSupport(
    const std::optional<std::string> &supportSource,
    const std::optional<std::string> &scriptSource)
{
    if (!scriptSource.has_value())
    {
        return {};
    }

    if (!supportSource.has_value() || supportSource->empty())
    {
        return *scriptSource;
    }

    return *supportSource + "\n\n" + *scriptSource;
}

bool loadTextTableRows(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &virtualPath,
    std::vector<std::vector<std::string>> &rows,
    std::string &failure)
{
    const std::optional<std::string> contents = assetFileSystem.readTextFile(virtualPath);

    if (!contents)
    {
        failure = "could not read test data table " + virtualPath;
        return false;
    }

    const std::optional<Engine::TextTable> table = Engine::TextTable::parseTabSeparated(*contents);

    if (!table)
    {
        failure = "could not parse test data table " + virtualPath;
        return false;
    }

    rows.clear();
    rows.reserve(table->getRowCount());

    for (size_t rowIndex = 0; rowIndex < table->getRowCount(); ++rowIndex)
    {
        rows.push_back(table->getRow(rowIndex));
    }

    return true;
}

bool loadRegressionGameData(RegressionGameData &data, std::string &failure)
{
    Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::filesystem::path assetsRoot = sourceRoot / "assets_dev";

    if (!assetFileSystem.initialize(sourceRoot, assetsRoot, Engine::AssetScaleTier::X1))
    {
        failure = "could not initialize asset file system for regression test tables";
        return false;
    }

    const std::optional<std::string> supportScriptText =
        assetFileSystem.readTextFile("Data/scripts/common/event_support.lua");
    const std::optional<std::string> globalScriptText = assetFileSystem.readTextFile("Data/scripts/Global.lua");
    const std::optional<std::string> out01ScriptText = assetFileSystem.readTextFile("Data/scripts/maps/out01.lua");

    if (!globalScriptText.has_value())
    {
        failure = "could not read global event script for regression tests";
        return false;
    }

    std::string globalScriptError;
    data.globalEventProgram = Game::ScriptedEventProgram::loadFromLuaText(
        prependLuaSupport(supportScriptText, globalScriptText),
        "@Global.lua",
        Game::ScriptedEventScope::Global,
        globalScriptError);

    if (!data.globalEventProgram.has_value())
    {
        failure = "could not load global event script for regression tests: " + globalScriptError;
        return false;
    }

    if (!out01ScriptText.has_value())
    {
        failure = "could not read out01 local event script for regression tests";
        return false;
    }

    std::string out01ScriptError;
    data.out01LocalEventProgram = Game::ScriptedEventProgram::loadFromLuaText(
        prependLuaSupport(supportScriptText, out01ScriptText),
        "@Data/scripts/maps/out01.lua",
        Game::ScriptedEventScope::Map,
        out01ScriptError);

    if (!data.out01LocalEventProgram.has_value())
    {
        failure = "could not load out01 local event script for regression tests: " + out01ScriptError;
        return false;
    }

    std::vector<std::vector<std::string>> itemRows;

    std::vector<std::vector<std::string>> arcomageCardRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("arcomage_cards.txt"), arcomageCardRows, failure))
    {
        return false;
    }

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("items.txt"), itemRows, failure))
    {
        return false;
    }

    std::vector<std::vector<std::string>> randomItemRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("random_items.txt"), randomItemRows, failure))
    {
        return false;
    }

    if (!data.itemTable.load(assetFileSystem, itemRows, randomItemRows))
    {
        failure = "could not load item table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> potionRows;

    if (!loadTextTableRows(assetFileSystem, engineEnglishDataTablePath("potion.txt"), potionRows, failure))
    {
        return false;
    }

    if (!data.potionMixingTable.loadFromRows(potionRows))
    {
        failure = "could not load potion mixing table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> potionNoteRows;

    if (!loadTextTableRows(assetFileSystem, engineEnglishDataTablePath("potnotes.txt"), potionNoteRows, failure))
    {
        return false;
    }

    if (!data.potionNoteTable.loadFromRows(potionNoteRows))
    {
        failure = "could not load potion note table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> potionSettingRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("potion_settings.txt"), potionSettingRows, failure))
    {
        return false;
    }

    if (!data.mergedPotionSettingTable.loadFromRows(potionSettingRows))
    {
        failure = "could not load merged potion setting table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> reagentSettingRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("reagent_settings.txt"), reagentSettingRows, failure))
    {
        return false;
    }

    if (!data.mergedReagentSettingTable.loadFromRows(reagentSettingRows))
    {
        failure = "could not load merged reagent setting table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> teacherTopicRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("teacher_topics.txt"), teacherTopicRows, failure))
    {
        return false;
    }

    if (!data.mergedTeacherTopicTable.loadFromRows(teacherTopicRows))
    {
        failure = "could not load merged teacher topic table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> teacherAutonoteRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("teacher_autonotes.txt"), teacherAutonoteRows, failure))
    {
        return false;
    }

    if (!data.mergedTeacherAutonoteTable.loadFromRows(teacherAutonoteRows))
    {
        failure = "could not load merged teacher autonote table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> npcProfessionRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("npc_professions.txt"), npcProfessionRows, failure))
    {
        return false;
    }

    if (!data.mergedNpcProfessionTable.loadFromRows(npcProfessionRows))
    {
        failure = "could not load merged NPC profession table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> npcNameRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("npc_names.txt"), npcNameRows, failure))
    {
        return false;
    }

    if (!data.mergedNpcNameTable.loadFromRows(npcNameRows))
    {
        failure = "could not load merged NPC name table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> npcBtbRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("npc_btb.txt"), npcBtbRows, failure))
    {
        return false;
    }

    if (!data.mergedNpcBtbTable.loadFromRows(npcBtbRows))
    {
        failure = "could not load merged NPC BTB table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> newsProfessionTopicRows;

    if (!loadTextTableRows(
            assetFileSystem,
            engineDataTablePath("news_topics_profession.txt"),
            newsProfessionTopicRows,
            failure))
    {
        return false;
    }

    if (!data.mergedNewsProfessionTopicTable.loadFromRows(newsProfessionTopicRows))
    {
        failure = "could not load merged profession news topic table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> bolsterMapRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("bolster_maps.txt"), bolsterMapRows, failure))
    {
        return false;
    }

    if (!data.mergedBolsterMapTable.loadFromRows(bolsterMapRows))
    {
        failure = "could not load merged bolster map table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> bolsterMonsterRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("bolster_monsters.txt"), bolsterMonsterRows, failure))
    {
        return false;
    }

    if (!data.mergedBolsterMonsterTable.loadFromRows(bolsterMonsterRows))
    {
        failure = "could not load merged bolster monster table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> characterVoiceRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("character_voices.txt"), characterVoiceRows, failure))
    {
        return false;
    }

    if (!data.mergedCharacterVoiceTable.loadFromRows(characterVoiceRows))
    {
        failure = "could not load merged character voice table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> monsterPortraitRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("monster_portraits.txt"), monsterPortraitRows, failure))
    {
        return false;
    }

    if (!data.mergedMonsterPortraitTable.loadFromRows(monsterPortraitRows))
    {
        failure = "could not load merged monster portrait table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> continentSettingRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("continent_settings.txt"), continentSettingRows, failure))
    {
        return false;
    }

    if (!data.mergedContinentSettingTable.loadFromRows(continentSettingRows))
    {
        failure = "could not load merged continent setting table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> standardEnchantRows;

    if (!loadTextTableRows(
            assetFileSystem,
            engineDataTablePath("standard_item_enchants.txt"),
            standardEnchantRows,
            failure))
    {
        return false;
    }

    if (!data.standardItemEnchantTable.load(standardEnchantRows))
    {
        failure = "could not load standard item enchant table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> specialEnchantRows;

    if (!loadTextTableRows(
            assetFileSystem,
            engineDataTablePath("special_item_enchants.txt"),
            specialEnchantRows,
            failure))
    {
        return false;
    }

    if (!data.specialItemEnchantTable.load(specialEnchantRows))
    {
        failure = "could not load special item enchant table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> readableScrollRows;

    if (!loadTextTableRows(assetFileSystem, engineEnglishDataTablePath("scroll.txt"), readableScrollRows, failure))
    {
        return false;
    }

    if (!data.readableScrollTable.loadFromRows(readableScrollRows))
    {
        failure = "could not load readable scroll table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> transitionRows;

    if (!loadTextTableRows(assetFileSystem, engineEnglishDataTablePath("trans.txt"), transitionRows, failure))
    {
        return false;
    }

    if (!data.transitionTable.loadFromRows(transitionRows))
    {
        failure = "could not load transition table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> monsterRelationRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("hostile.txt"), monsterRelationRows, failure))
    {
        return false;
    }

    if (!data.monsterTable.loadRelationsFromRows(monsterRelationRows))
    {
        failure = "could not load monster relation table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> spellRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("spells.txt"), spellRows, failure))
    {
        return false;
    }

    if (!data.spellTable.loadFromRows(spellRows))
    {
        failure = "could not load spell table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> characterRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("character_data.txt"), characterRows, failure))
    {
        return false;
    }

    if (!data.characterDollTable.loadCharacterRows(characterRows))
    {
        failure = "could not load character doll rows for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> dollTypeRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("doll_types.txt"), dollTypeRows, failure))
    {
        return false;
    }

    if (!data.characterDollTable.loadDollTypeRows(dollTypeRows))
    {
        failure = "could not load doll type rows for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> classMultiplierRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("class_multipliers.txt"), classMultiplierRows, failure))
    {
        return false;
    }

    if (!data.classMultiplierTable.loadFromRows(classMultiplierRows))
    {
        failure = "could not load class multipliers for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> classExtraRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("class_extra.txt"), classExtraRows, failure))
    {
        return false;
    }

    if (!data.classMultiplierTable.applyClassExtraRows(classExtraRows))
    {
        failure = "could not apply class metadata for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> classSkillRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("class_skills.txt"), classSkillRows, failure))
    {
        return false;
    }

    if (!data.classSkillTable.loadCapsFromRows(classSkillRows))
    {
        failure = "could not load class skill caps for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> startingSkillRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("class_starting_skills.txt"), startingSkillRows, failure))
    {
        return false;
    }

    if (!data.classSkillTable.loadStartingSkillsFromRows(startingSkillRows))
    {
        failure = "could not load class starting skills for regression tests";
        return false;
    }

    if (!data.classSkillTable.loadClassMetadataFromRows(classExtraRows))
    {
        failure = "could not load class metadata for regression tests";
        return false;
    }

    if (!data.classSkillTable.loadClassSpellPointMetadataFromRows(classMultiplierRows))
    {
        failure = "could not load class spell point metadata for regression tests";
        return false;
    }

    const std::optional<std::string> raceSkillYaml =
        assetFileSystem.readTextFile(engineDataTablePath("race_skills.yml"));

    if (!raceSkillYaml)
    {
        failure = "could not read race skill yaml for regression tests";
        return false;
    }

    Game::MergedRaceSkillTable raceSkillTable = {};
    std::string raceSkillErrorMessage;

    if (!raceSkillTable.loadFromYaml(*raceSkillYaml, raceSkillErrorMessage))
    {
        failure = "could not load race skill yaml for regression tests: " + raceSkillErrorMessage;
        return false;
    }

    if (!data.classSkillTable.applyRaceSkillOverrides(raceSkillTable))
    {
        failure = "could not apply race skill rules for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> houseRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("house_data.txt"), houseRows, failure))
    {
        return false;
    }

    if (!data.houseTable.loadFromRows(houseRows))
    {
        failure = "could not load house table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> houseAnimationRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("house_animations.txt"), houseAnimationRows, failure))
    {
        return false;
    }

    std::vector<std::vector<std::string>> houseMovieRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("house_movies.txt"), houseMovieRows, failure))
    {
        return false;
    }

    if (!data.houseTable.loadAnimationRows(houseAnimationRows, houseMovieRows))
    {
        failure = "could not load house animation rows for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> mapStatsRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("map_stats.txt"), mapStatsRows, failure))
    {
        return false;
    }

    Game::MapStats mapStats = {};

    if (!mapStats.loadFromRows(mapStatsRows))
    {
        failure = "could not load map stats for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> houseRuleRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("house_rules.txt"), houseRuleRows, failure))
    {
        return false;
    }

    Game::MergedHouseRuleTable houseRules = {};

    if (!houseRules.loadFromRows(houseRuleRows))
    {
        failure = "could not load merged house rules for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> transportLocationRows;

    if (!loadTextTableRows(
            assetFileSystem,
            engineDataTablePath("transport_locations.txt"),
            transportLocationRows,
            failure))
    {
        return false;
    }

    Game::MergedTransportLocationTable transportLocations = {};

    if (!transportLocations.loadFromRows(transportLocationRows))
    {
        failure = "could not load merged transport locations for regression tests";
        return false;
    }

    if (!data.houseTable.applyHouseRules(houseRules, transportLocations, mapStats))
    {
        failure = "could not apply merged house rules for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> houseExitRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("house_exits.txt"), houseExitRows, failure))
    {
        return false;
    }

    Game::MergedHouseExitTable houseExits = {};

    if (!houseExits.loadFromRows(houseExitRows))
    {
        failure = "could not load merged house exits for regression tests";
        return false;
    }

    if (!data.houseTable.applyHouseExits(houseExits, mapStats))
    {
        failure = "could not apply merged house exits for regression tests";
        return false;
    }

    Game::ArcomageLoader arcomageLoader;

    if (!arcomageLoader.loadFromHouseRules(houseRules, data.houseTable, arcomageCardRows))
    {
        failure = "could not load Arcomage library for regression tests";
        return false;
    }

    data.arcomageLibrary = arcomageLoader.library();

    std::vector<std::vector<std::string>> rosterRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("roster.txt"), rosterRows, failure))
    {
        return false;
    }

    if (!data.rosterTable.loadFromRows(rosterRows, &data.classSkillTable))
    {
        failure = "could not load roster table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> greetingRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("npc_greet.txt"), greetingRows, failure))
    {
        return false;
    }

    std::vector<std::vector<std::string>> textRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("npc_topic_text.txt"), textRows, failure))
    {
        return false;
    }

    std::vector<std::vector<std::string>> topicRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("npc_topic.txt"), topicRows, failure))
    {
        return false;
    }

    std::vector<std::vector<std::string>> npcRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("npc.txt"), npcRows, failure))
    {
        return false;
    }

    std::vector<std::vector<std::string>> newsRows;

    if (!loadTextTableRows(assetFileSystem, engineDataTablePath("npc_news.txt"), newsRows, failure))
    {
        return false;
    }

    std::vector<std::vector<std::string>> groupRows;

    if (!loadTextTableRows(assetFileSystem, engineEnglishDataTablePath("npc_group.txt"), groupRows, failure))
    {
        return false;
    }

    if (!data.npcDialogTable.loadGreetingsFromRows(greetingRows)
        || !data.npcDialogTable.loadNewsFromRows(newsRows)
        || !data.npcDialogTable.loadGroupNewsFromRows(groupRows)
        || !data.npcDialogTable.loadTextsFromRows(textRows)
        || !data.npcDialogTable.loadTopicsFromRows(topicRows)
        || !data.npcDialogTable.loadNpcRows(npcRows))
    {
        failure = "could not load NPC dialog tables for regression tests";
        return false;
    }

    data.npcDialogTable.resolveSpecialTopics(data.rosterTable);

    return true;
}

const RegressionGameDataState &regressionGameDataState()
{
    static const RegressionGameDataState state = []()
    {
        RegressionGameDataState state = {};
        state.loaded = loadRegressionGameData(state.data, state.failure);
        return state;
    }();

    return state;
}
}

bool regressionGameDataLoaded()
{
    return regressionGameDataState().loaded;
}

const std::string &regressionGameDataFailure()
{
    return regressionGameDataState().failure;
}

const RegressionGameData &regressionGameData()
{
    return regressionGameDataState().data;
}
}
