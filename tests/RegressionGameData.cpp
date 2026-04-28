#include "tests/RegressionGameData.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/TextTable.h"
#include "game/arcomage/ArcomageLoader.h"

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

std::string dataTablePath(std::string_view fileName)
{
    return "Data/data_tables/" + std::string(fileName);
}

std::string englishDataTablePath(std::string_view fileName)
{
    return dataTablePath(std::string("english/") + std::string(fileName));
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

bool loadFirstTextTableRows(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &virtualPaths,
    std::vector<std::vector<std::string>> &rows,
    std::string &failure)
{
    for (const std::string &virtualPath : virtualPaths)
    {
        if (loadTextTableRows(assetFileSystem, virtualPath, rows, failure))
        {
            return true;
        }
    }

    return false;
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

    std::vector<std::vector<std::string>> arcomageRuleRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("arcomage_rules.txt"), arcomageRuleRows, failure))
    {
        return false;
    }

    std::vector<std::vector<std::string>> arcomageCardRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("arcomage_cards.txt"), arcomageCardRows, failure))
    {
        return false;
    }

    Game::ArcomageLoader arcomageLoader;

    if (!arcomageLoader.load(arcomageRuleRows, arcomageCardRows))
    {
        failure = "could not load Arcomage library for regression tests";
        return false;
    }

    data.arcomageLibrary = arcomageLoader.library();

    if (!loadTextTableRows(assetFileSystem, dataTablePath("items.txt"), itemRows, failure))
    {
        return false;
    }

    std::vector<std::vector<std::string>> randomItemRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("random_items.txt"), randomItemRows, failure))
    {
        return false;
    }

    if (!data.itemTable.load(assetFileSystem, itemRows, randomItemRows))
    {
        failure = "could not load item table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> potionRows;

    if (!loadTextTableRows(assetFileSystem, englishDataTablePath("potion.txt"), potionRows, failure))
    {
        return false;
    }

    if (!data.potionMixingTable.loadFromRows(potionRows))
    {
        failure = "could not load potion mixing table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> standardEnchantRows;

    if (!loadTextTableRows(
            assetFileSystem,
            dataTablePath("standard_item_enchants.txt"),
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
            dataTablePath("special_item_enchants.txt"),
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

    if (!loadTextTableRows(assetFileSystem, englishDataTablePath("scroll.txt"), readableScrollRows, failure))
    {
        return false;
    }

    if (!data.readableScrollTable.loadFromRows(readableScrollRows))
    {
        failure = "could not load readable scroll table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> transitionRows;

    if (!loadTextTableRows(assetFileSystem, englishDataTablePath("trans.txt"), transitionRows, failure))
    {
        return false;
    }

    if (!data.transitionTable.loadFromRows(transitionRows))
    {
        failure = "could not load transition table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> monsterRelationRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("monster_relation_data.txt"), monsterRelationRows, failure))
    {
        return false;
    }

    if (!data.monsterTable.loadRelationsFromRows(monsterRelationRows))
    {
        failure = "could not load monster relation table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> spellRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("spells.txt"), spellRows, failure))
    {
        return false;
    }

    std::vector<std::vector<std::string>> supplementalSpellRows;

    const std::string supplementalSpellsPath = dataTablePath("spells_supplemental.txt");

    if (assetFileSystem.exists(supplementalSpellsPath)
        && !loadTextTableRows(assetFileSystem, supplementalSpellsPath, supplementalSpellRows, failure))
    {
        return false;
    }

    if (!supplementalSpellRows.empty())
    {
        spellRows.insert(spellRows.end(), supplementalSpellRows.begin(), supplementalSpellRows.end());
    }

    if (!data.spellTable.loadFromRows(spellRows))
    {
        failure = "could not load spell table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> characterRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("character_data.txt"), characterRows, failure))
    {
        return false;
    }

    if (!data.characterDollTable.loadCharacterRows(characterRows))
    {
        failure = "could not load character doll rows for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> dollTypeRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("doll_types.txt"), dollTypeRows, failure))
    {
        return false;
    }

    if (!data.characterDollTable.loadDollTypeRows(dollTypeRows))
    {
        failure = "could not load doll type rows for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> classMultiplierRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("class_multipliers.txt"), classMultiplierRows, failure))
    {
        return false;
    }

    if (!data.classMultiplierTable.loadFromRows(classMultiplierRows))
    {
        failure = "could not load class multipliers for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> classSkillRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("class_skills.txt"), classSkillRows, failure))
    {
        return false;
    }

    if (!data.classSkillTable.loadCapsFromRows(classSkillRows))
    {
        failure = "could not load class skill caps for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> startingSkillRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("class_starting_skills.txt"), startingSkillRows, failure))
    {
        return false;
    }

    if (!data.classSkillTable.loadStartingSkillsFromRows(startingSkillRows))
    {
        failure = "could not load class starting skills for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> houseRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("house_data.txt"), houseRows, failure))
    {
        return false;
    }

    if (!data.houseTable.loadFromRows(houseRows))
    {
        failure = "could not load house table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> houseAnimationRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("house_animations.txt"), houseAnimationRows, failure))
    {
        return false;
    }

    if (!data.houseTable.loadAnimationRows(houseAnimationRows))
    {
        failure = "could not load house animation rows for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> transportRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("transport_schedules.txt"), transportRows, failure))
    {
        return false;
    }

    if (!data.houseTable.loadTransportScheduleRows(transportRows))
    {
        failure = "could not load transport schedules for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> rosterRows;

    if (!loadTextTableRows(assetFileSystem, dataTablePath("roster.txt"), rosterRows, failure))
    {
        return false;
    }

    if (!data.rosterTable.loadFromRows(rosterRows))
    {
        failure = "could not load roster table for regression tests";
        return false;
    }

    std::vector<std::vector<std::string>> greetingRows;

    if (!loadFirstTextTableRows(assetFileSystem, {dataTablePath("npc_greet.txt")}, greetingRows, failure))
    {
        return false;
    }

    std::vector<std::vector<std::string>> textRows;

    if (!loadFirstTextTableRows(assetFileSystem, {dataTablePath("npc_topic_text.txt")}, textRows, failure))
    {
        return false;
    }

    std::vector<std::vector<std::string>> topicRows;

    if (!loadFirstTextTableRows(assetFileSystem, {dataTablePath("npc_topic.txt")}, topicRows, failure))
    {
        return false;
    }

    std::vector<std::vector<std::string>> npcRows;

    if (!loadFirstTextTableRows(assetFileSystem, {dataTablePath("npc.txt")}, npcRows, failure))
    {
        return false;
    }

    std::vector<std::vector<std::string>> newsRows;

    if (!loadFirstTextTableRows(assetFileSystem, {dataTablePath("npc_news.txt")}, newsRows, failure))
    {
        return false;
    }

    std::vector<std::vector<std::string>> groupRows;

    if (!loadFirstTextTableRows(assetFileSystem, {englishDataTablePath("npc_group.txt")}, groupRows, failure))
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
