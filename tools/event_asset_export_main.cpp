#include "engine/ApplicationConfig.h"
#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/TextTable.h"
#include "game/events/EvtEnums.h"
#include "game/indoor/IndoorMapData.h"
#include "game/tables/MapStats.h"
#include "tools/EventIr.h"
#include "tools/EventIrLegacyImport.h"
#include "tools/LegacyLuaExport.h"
#include "tools/legacy_events/EvtProgram.h"
#include "tools/legacy_events/StrTable.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cstdlib>
#include <cctype>
#include <cstdint>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <optional>
#include <set>
#include <sstream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace
{
using OpenYAMM::Engine::AssetFileSystem;
using OpenYAMM::Engine::ApplicationConfig;
using OpenYAMM::Engine::TextTable;
using OpenYAMM::Game::EventIrProgram;
using OpenYAMM::Game::EvtEvent;
using OpenYAMM::Game::EvtInstruction;
using OpenYAMM::Game::EvtOpcode;
using OpenYAMM::Game::EvtVariable;
using OpenYAMM::Game::EvtProgram;
using OpenYAMM::Game::IndoorMapData;
using OpenYAMM::Game::IndoorMapDataLoader;
using OpenYAMM::Game::IndoorSpawn;
using OpenYAMM::Game::LegacyEventVersion;
using OpenYAMM::Game::LegacyLuaExportLookups;
using OpenYAMM::Game::LegacyLuaExportScope;
using OpenYAMM::Game::MapEncounterInfo;
using OpenYAMM::Game::MapStats;
using OpenYAMM::Game::MapStatsEntry;
using OpenYAMM::Game::StrTable;

constexpr uint32_t CustomWorldQBitBegin = 10000;

std::optional<LegacyEventVersion> parseLegacyEventVersion(std::string_view value)
{
    if (value == "6" || value == "mm6" || value == "MM6")
    {
        return LegacyEventVersion::Mm6;
    }

    if (value == "7" || value == "mm7" || value == "MM7")
    {
        return LegacyEventVersion::Mm7;
    }

    if (value == "8" || value == "mm8" || value == "MM8")
    {
        return LegacyEventVersion::Mm8;
    }

    return std::nullopt;
}

bool parseArguments(
    int argc,
    char **argv,
    ApplicationConfig &config,
    std::optional<std::string> &mapFilter,
    std::optional<std::filesystem::path> &luaExportConfigPath,
    std::optional<std::string> &legacyEventsDir,
    std::optional<LegacyEventVersion> &legacyEventVersion)
{
    bool hasAssetScaleArgument = false;

    for (int argumentIndex = 1; argumentIndex < argc; ++argumentIndex)
    {
        const std::string argument = argv[argumentIndex];

        if (argument == "--asset-scale")
        {
            if (hasAssetScaleArgument || argumentIndex + 1 >= argc)
            {
                std::cerr << "Usage: --asset-scale <1|2|4|x1|x2|x4>\n";
                return false;
            }

            const std::optional<OpenYAMM::Engine::AssetScaleTier> assetScaleTier =
                OpenYAMM::Engine::parseAssetScaleTier(argv[argumentIndex + 1]);

            if (!assetScaleTier)
            {
                std::cerr << "Invalid asset scale: " << argv[argumentIndex + 1] << '\n';
                return false;
            }

            config.assetScaleTier = *assetScaleTier;
            hasAssetScaleArgument = true;
            ++argumentIndex;
            continue;
        }

        if (argument == "--map")
        {
            if (mapFilter.has_value() || argumentIndex + 1 >= argc)
            {
                std::cerr << "Usage: --map <map_stem>\n";
                return false;
            }

            mapFilter = argv[argumentIndex + 1];
            ++argumentIndex;
            continue;
        }

        if (argument == "--lua-export-config")
        {
            if (luaExportConfigPath.has_value() || argumentIndex + 1 >= argc)
            {
                std::cerr << "Usage: --lua-export-config <path>\n";
                return false;
            }

            luaExportConfigPath = std::filesystem::path(argv[argumentIndex + 1]);
            ++argumentIndex;
            continue;
        }

        if (argument == "--legacy-events-dir")
        {
            if (legacyEventsDir.has_value() || argumentIndex + 1 >= argc)
            {
                std::cerr << "Usage: --legacy-events-dir <virtual_path>\n";
                return false;
            }

            legacyEventsDir = argv[argumentIndex + 1];
            ++argumentIndex;
            continue;
        }

        if (argument == "--legacy-event-version")
        {
            if (legacyEventVersion.has_value() || argumentIndex + 1 >= argc)
            {
                std::cerr << "Usage: --legacy-event-version <6|7|8>\n";
                return false;
            }

            const std::string value = argv[argumentIndex + 1];
            const std::optional<LegacyEventVersion> parsedVersion = parseLegacyEventVersion(value);

            if (!parsedVersion)
            {
                std::cerr << "Invalid legacy event version: " << value << '\n';
                return false;
            }

            legacyEventVersion = *parsedVersion;
            ++argumentIndex;
            continue;
        }

        if (argument == "--world")
        {
            if (argumentIndex + 1 >= argc)
            {
                std::cerr << "Usage: --world <world_id>\n";
                return false;
            }

            config.activeWorldId = argv[argumentIndex + 1];
            ++argumentIndex;
            continue;
        }

        std::cerr << "Unknown argument: " << argument << '\n';
        return false;
    }

    return true;
}

std::string trimCopy(const std::string &value)
{
    size_t begin = 0;

    while (begin < value.size() && std::isspace(static_cast<unsigned char>(value[begin])))
    {
        ++begin;
    }

    size_t end = value.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])))
    {
        --end;
    }

    return value.substr(begin, end - begin);
}

std::string toLowerCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return result;
}

std::string toUpperCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::toupper(static_cast<unsigned char>(character)));
    }

    return result;
}

struct LuaExportTablePaths
{
    std::string mapStats = "engine/data_tables/map_stats.txt";
    std::string houseData = "engine/data_tables/house_data.txt";
    std::string npcTopicText = "engine/data_tables/npc_topic_text.txt";
    std::string npcTopic = "engine/data_tables/npc_topic.txt";
    std::string npcGreeting = "engine/data_tables/npc_greet.txt";
    std::string items = "engine/data_tables/items.txt";
    std::string objectList = "engine/data_tables/object_list.txt";
    std::string monsterData = "engine/data_tables/monster_data.txt";
    std::string placeMon = "engine/data_tables/english/place_mon.txt";
    std::string spells = "engine/data_tables/spells.txt";
    std::string spellsSupplemental = "engine/data_tables/spells_supplemental.txt";
    std::string npc = "engine/data_tables/npc.txt";
    std::string roster = "engine/data_tables/roster.txt";
    std::string npcGroup = "engine/data_tables/english/npc_group.txt";
    std::string npcNews = "engine/data_tables/npc_news.txt";
    std::string quests = "engine/data_tables/english/quests.txt";
    std::string autonote = "engine/data_tables/english/autonote.txt";
    std::string awards = "engine/data_tables/english/awards.txt";
    std::string legacyEventsDir = "_legacy/events";
    std::string decompiledScriptsDir;
    LegacyEventVersion legacyEventVersion = LegacyEventVersion::Mm8;
};

bool loadLuaExportConfig(const std::filesystem::path &path, LuaExportTablePaths &tablePaths)
{
    std::ifstream inputStream(path);

    if (!inputStream)
    {
        return false;
    }

    std::string sectionName;
    std::string line;

    while (std::getline(inputStream, line))
    {
        const std::string trimmed = trimCopy(line);

        if (trimmed.empty() || trimmed[0] == '#' || trimmed[0] == ';')
        {
            continue;
        }

        if (trimmed.front() == '[' && trimmed.back() == ']')
        {
            sectionName = toLowerCopy(trimCopy(trimmed.substr(1, trimmed.size() - 2)));
            continue;
        }

        if (sectionName != "paths" && sectionName != "legacy_events")
        {
            continue;
        }

        const size_t equalsIndex = trimmed.find('=');

        if (equalsIndex == std::string::npos)
        {
            continue;
        }

        const std::string key = toLowerCopy(trimCopy(trimmed.substr(0, equalsIndex)));
        const std::string value = trimCopy(trimmed.substr(equalsIndex + 1));

        if (sectionName == "legacy_events")
        {
            if (key == "version")
            {
                const std::optional<LegacyEventVersion> parsedVersion = parseLegacyEventVersion(value);

                if (parsedVersion)
                {
                    tablePaths.legacyEventVersion = *parsedVersion;
                }
            }

            continue;
        }

        if (key == "map_stats")
        {
            tablePaths.mapStats = value;
        }
        else if (key == "house_data")
        {
            tablePaths.houseData = value;
        }
        else if (key == "npc_topic_text")
        {
            tablePaths.npcTopicText = value;
        }
        else if (key == "npc_topic")
        {
            tablePaths.npcTopic = value;
        }
        else if (key == "npc_greeting")
        {
            tablePaths.npcGreeting = value;
        }
        else if (key == "items")
        {
            tablePaths.items = value;
        }
        else if (key == "object_list")
        {
            tablePaths.objectList = value;
        }
        else if (key == "monster_data")
        {
            tablePaths.monsterData = value;
        }
        else if (key == "place_mon")
        {
            tablePaths.placeMon = value;
        }
        else if (key == "spells")
        {
            tablePaths.spells = value;
        }
        else if (key == "spells_supplemental")
        {
            tablePaths.spellsSupplemental = value;
        }
        else if (key == "npc")
        {
            tablePaths.npc = value;
        }
        else if (key == "roster")
        {
            tablePaths.roster = value;
        }
        else if (key == "npc_group")
        {
            tablePaths.npcGroup = value;
        }
        else if (key == "npc_news")
        {
            tablePaths.npcNews = value;
        }
        else if (key == "quests")
        {
            tablePaths.quests = value;
        }
        else if (key == "autonote")
        {
            tablePaths.autonote = value;
        }
        else if (key == "awards")
        {
            tablePaths.awards = value;
        }
        else if (key == "legacy_events_dir")
        {
            tablePaths.legacyEventsDir = value;
        }
        else if (key == "decompiled_scripts_dir")
        {
            tablePaths.decompiledScriptsDir = value;
        }
    }

    return true;
}

bool writeTextFile(const std::filesystem::path &path, const std::string &text)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream outputStream(path);

    if (!outputStream)
    {
        return false;
    }

    outputStream << text;
    return outputStream.good();
}

std::vector<std::string> buildLegacyScriptPathCandidates(
    const std::string &legacyEventsDir,
    const std::string &baseName,
    const std::string &extension)
{
    const std::string normalizedLegacyEventsDir = trimCopy(legacyEventsDir);
    std::vector<std::string> candidates = {
        normalizedLegacyEventsDir + "/" + baseName + extension,
        normalizedLegacyEventsDir + "/" + toUpperCopy(baseName) + extension,
        normalizedLegacyEventsDir + "/" + baseName + toUpperCopy(extension),
        normalizedLegacyEventsDir + "/" + toUpperCopy(baseName) + toUpperCopy(extension),
    };

    if (toLowerCopy(normalizedLegacyEventsDir) != "data/englisht")
    {
        candidates.push_back("Data/EnglishT/" + baseName + extension);
        candidates.push_back("Data/EnglishT/" + toUpperCopy(baseName) + extension);
        candidates.push_back("Data/EnglishT/" + baseName + toUpperCopy(extension));
        candidates.push_back("Data/EnglishT/" + toUpperCopy(baseName) + toUpperCopy(extension));
    }

    return candidates;
}

std::optional<std::vector<uint8_t>> readFirstExistingBinary(
    const AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &candidates,
    std::string &resolvedPath)
{
    for (const std::string &candidate : candidates)
    {
        const std::optional<std::vector<uint8_t>> bytes = assetFileSystem.readBinaryFile(candidate);

        if (bytes)
        {
            resolvedPath = candidate;
            return bytes;
        }
    }

    for (const std::string &candidate : candidates)
    {
        const std::filesystem::path candidatePath(candidate);
        const std::string parentPath = candidatePath.parent_path().generic_string();
        const std::string fileName = toLowerCopy(candidatePath.filename().string());

        if (parentPath.empty() || fileName.empty())
        {
            continue;
        }

        for (const std::string &entryName : assetFileSystem.enumerate(parentPath))
        {
            if (toLowerCopy(entryName) != fileName)
            {
                continue;
            }

            const std::string matchedPath = parentPath + "/" + entryName;
            const std::optional<std::vector<uint8_t>> bytes = assetFileSystem.readBinaryFile(matchedPath);

            if (bytes)
            {
                resolvedPath = matchedPath;
                return bytes;
            }
        }
    }

    return std::nullopt;
}

bool loadTextTableRows(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath,
    std::vector<std::vector<std::string>> &rows)
{
    rows.clear();
    const std::optional<std::string> fileContents = assetFileSystem.readTextFile(virtualPath);

    if (!fileContents)
    {
        return false;
    }

    const std::optional<TextTable> parsedTable = TextTable::parseTabSeparated(*fileContents);

    if (!parsedTable)
    {
        return false;
    }

    for (size_t rowIndex = 0; rowIndex < parsedTable->getRowCount(); ++rowIndex)
    {
        rows.push_back(parsedTable->getRow(rowIndex));
    }

    return true;
}

std::optional<uint32_t> parseUint32Field(const std::string &value)
{
    if (value.empty() || value[0] == '#')
    {
        return std::nullopt;
    }

    char *pEnd = nullptr;
    const unsigned long parsedId = std::strtoul(value.c_str(), &pEnd, 10);

    if (pEnd == value.c_str() || *pEnd != '\0')
    {
        return std::nullopt;
    }

    if (parsedId > std::numeric_limits<uint32_t>::max())
    {
        return std::nullopt;
    }

    return static_cast<uint32_t>(parsedId);
}

bool loadMapStats(const AssetFileSystem &assetFileSystem, const std::string &virtualPath, MapStats &mapStats)
{
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        return false;
    }

    return mapStats.loadFromRows(rows);
}

std::unordered_map<std::string, std::string> buildMapNameLookup(const MapStats &mapStats)
{
    std::unordered_map<std::string, std::string> names;

    for (const MapStatsEntry &entry : mapStats.getEntries())
    {
        if (entry.name.empty())
        {
            continue;
        }

        if (!entry.fileName.empty())
        {
            const std::string loweredFileName = toLowerCopy(entry.fileName);
            names[loweredFileName] = entry.name;
            names[toLowerCopy(std::filesystem::path(entry.fileName).stem().string())] = entry.name;
        }
    }

    return names;
}

std::unordered_map<uint32_t, std::string> loadHouseNames(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath)
{
    std::unordered_map<uint32_t, std::string> names;
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        return names;
    }

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 5)
        {
            continue;
        }

        const std::optional<uint32_t> parsedId = parseUint32Field(row[0]);

        if (!parsedId)
        {
            continue;
        }

        if (!row[5].empty())
        {
            names[*parsedId] = row[5];
        }
    }

    return names;
}

std::unordered_map<uint32_t, std::string> loadNpcTexts(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath)
{
    std::unordered_map<uint32_t, std::string> texts;
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        return texts;
    }

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 1)
        {
            continue;
        }

        const std::optional<uint32_t> parsedId = parseUint32Field(row[0]);

        if (!parsedId)
        {
            continue;
        }

        texts[*parsedId] = row[1];
    }

    return texts;
}

std::unordered_map<uint32_t, std::string> loadItemNames(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath)
{
    std::unordered_map<uint32_t, std::string> names;
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        return names;
    }

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 2)
        {
            continue;
        }

        const std::optional<uint32_t> parsedId = parseUint32Field(row[0]);

        if (!parsedId || row[2].empty())
        {
            continue;
        }

        names[*parsedId] = row[2];
    }

    return names;
}

std::unordered_map<uint32_t, std::string> loadObjectPayloadNames(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath)
{
    std::unordered_map<uint32_t, std::string> names;
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        return names;
    }

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 2)
        {
            continue;
        }

        const std::optional<uint32_t> parsedId = parseUint32Field(row[2]);

        if (!parsedId || row[0].empty() || row[0] == "null" || row[0].starts_with("//"))
        {
            continue;
        }

        names[*parsedId] = row[0];
    }

    return names;
}

std::unordered_map<uint32_t, std::string> loadMonsterNames(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath)
{
    std::unordered_map<uint32_t, std::string> names;
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        return names;
    }

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 1)
        {
            continue;
        }

        const std::optional<uint32_t> parsedId = parseUint32Field(row[0]);

        if (!parsedId || row[1].empty())
        {
            continue;
        }

        names[*parsedId] = row[1];
    }

    return names;
}

void appendSpellNamesFromPath(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath,
    std::unordered_map<uint32_t, std::string> &names)
{
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        return;
    }

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 2)
        {
            continue;
        }

        const std::optional<uint32_t> parsedId = parseUint32Field(row[0]);

        if (!parsedId || row[2].empty())
        {
            continue;
        }

        names[*parsedId] = row[2];
    }
}

std::unordered_map<uint32_t, std::string> loadSpellNames(
    const AssetFileSystem &assetFileSystem,
    const std::string &spellsPath,
    const std::string &supplementalPath)
{
    std::unordered_map<uint32_t, std::string> names;
    appendSpellNamesFromPath(assetFileSystem, spellsPath, names);

    if (assetFileSystem.exists(supplementalPath))
    {
        appendSpellNamesFromPath(assetFileSystem, supplementalPath, names);
    }

    return names;
}

std::unordered_map<uint32_t, std::string> loadNpcNames(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath)
{
    std::unordered_map<uint32_t, std::string> names;
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        return names;
    }

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 1)
        {
            continue;
        }

        const std::optional<uint32_t> parsedId = parseUint32Field(row[0]);

        if (!parsedId || row[1].empty())
        {
            continue;
        }

        names[*parsedId] = row[1];
    }

    return names;
}

std::unordered_map<uint32_t, std::string> loadRosterNames(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath)
{
    std::unordered_map<uint32_t, std::string> names;
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        return names;
    }

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 1)
        {
            continue;
        }

        const std::optional<uint32_t> parsedId = parseUint32Field(row[0]);

        if (!parsedId || row[1].empty())
        {
            continue;
        }

        names[*parsedId] = row[1];
    }

    return names;
}

std::unordered_map<uint32_t, std::string> loadPlacedMonsterNames(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath)
{
    std::unordered_map<uint32_t, std::string> names;
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        return names;
    }

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 1)
        {
            continue;
        }

        const std::optional<uint32_t> parsedId = parseUint32Field(row[0]);

        if (!parsedId || row[1].empty())
        {
            continue;
        }

        names[*parsedId] = row[1];
    }

    return names;
}

std::unordered_map<uint32_t, std::string> loadNpcGroupNames(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath)
{
    std::unordered_map<uint32_t, std::string> names;
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        return names;
    }

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 2)
        {
            continue;
        }

        const std::optional<uint32_t> parsedId = parseUint32Field(row[0]);

        if (!parsedId)
        {
            continue;
        }

        for (size_t columnIndex = 2; columnIndex < row.size(); ++columnIndex)
        {
            const std::string groupName = trimCopy(row[columnIndex]);

            if (!groupName.empty())
            {
                names[*parsedId] = groupName;
                break;
            }
        }
    }

    return names;
}

std::unordered_map<uint32_t, std::string> loadNpcNewsTexts(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath)
{
    std::unordered_map<uint32_t, std::string> texts;
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        return texts;
    }

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 1)
        {
            continue;
        }

        const std::optional<uint32_t> parsedId = parseUint32Field(row[0]);

        if (!parsedId || row[1].empty())
        {
            continue;
        }

        texts[*parsedId] = row[1];
    }

    return texts;
}

std::string normalizeWhitespace(const std::string &value);

std::unordered_map<uint32_t, std::string> loadNpcTopicNames(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath)
{
    std::unordered_map<uint32_t, std::string> names;
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        return names;
    }

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 1)
        {
            continue;
        }

        const std::optional<uint32_t> parsedId = parseUint32Field(row[0]);
        const std::string topicName = normalizeWhitespace(row[1]);

        if (parsedId && !topicName.empty() && topicName != "0")
        {
            names[*parsedId] = topicName;
        }
    }

    return names;
}

std::unordered_map<uint32_t, std::string> loadNpcGreetingTexts(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath)
{
    std::unordered_map<uint32_t, std::string> texts;
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        return texts;
    }

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 2)
        {
            continue;
        }

        const std::optional<uint32_t> parsedId = parseUint32Field(row[0]);
        std::string greetingText = normalizeWhitespace(row[1]);

        if (greetingText.empty() || greetingText == "0")
        {
            greetingText = normalizeWhitespace(row[2]);
        }

        if (parsedId && !greetingText.empty() && greetingText != "0")
        {
            texts[*parsedId] = greetingText;
        }
    }

    return texts;
}

bool isMeaningfulQuestField(const std::string &value)
{
    const std::string trimmed = trimCopy(value);
    return !trimmed.empty() && trimmed != "0";
}

std::unordered_map<uint32_t, std::string> loadQuestNotes(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath,
    std::string &errorMessage)
{
    std::unordered_map<uint32_t, std::string> notes;
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        errorMessage = "failed to read " + virtualPath;
        return notes;
    }

    std::set<uint32_t> seenQBitIds;

    for (size_t rowIndex = 0; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];

        if (row.size() <= 2)
        {
            continue;
        }

        const std::optional<uint32_t> parsedId = parseUint32Field(row[0]);

        if (!parsedId)
        {
            if (!row[0].empty() && row[0][0] != '#' && row[0] != "Q Bit")
            {
                errorMessage = "invalid quests.txt QBit id at row "
                    + std::to_string(rowIndex + 1) + ": " + row[0];
                return {};
            }

            continue;
        }

        if (!seenQBitIds.insert(*parsedId).second)
        {
            errorMessage = "duplicate quests.txt QBit id at row "
                + std::to_string(rowIndex + 1) + ": " + std::to_string(*parsedId);
            return {};
        }

        const std::string questText = normalizeWhitespace(row[1]);
        const std::string noteText = normalizeWhitespace(row[2]);
        std::string comment;

        if (isMeaningfulQuestField(questText))
        {
            comment = questText;
        }

        if (isMeaningfulQuestField(noteText))
        {
            if (!comment.empty())
            {
                comment += " - ";
            }

            comment += noteText;
        }

        if (!comment.empty())
        {
            notes[*parsedId] = comment;
        }
    }

    return notes;
}

std::unordered_map<uint32_t, std::string> loadAutonoteTexts(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath)
{
    std::unordered_map<uint32_t, std::string> texts;
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        return texts;
    }

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 1)
        {
            continue;
        }

        const std::optional<uint32_t> parsedId = parseUint32Field(row[0]);

        if (!parsedId)
        {
            continue;
        }

        const std::string autonoteText = normalizeWhitespace(row[1]);

        if (!autonoteText.empty() && autonoteText != "0")
        {
            texts[*parsedId] = autonoteText;
        }
    }

    return texts;
}

bool legacyOpcodeUsesVariableValue(EvtOpcode opcode)
{
    switch (opcode)
    {
        case EvtOpcode::Compare:
        case EvtOpcode::Add:
        case EvtOpcode::Subtract:
        case EvtOpcode::Set:
        case EvtOpcode::OnCanShowDialogItemCmp:
            return true;

        default:
            return false;
    }
}

std::optional<uint32_t> legacyQBitIdFromVariableValue(uint32_t rawValue)
{
    const uint32_t rawVariableId = rawValue & 0xFFFFu;
    const uint32_t index = rawValue >> 16;

    if (rawVariableId != static_cast<uint32_t>(EvtVariable::QBits))
    {
        return std::nullopt;
    }

    return index;
}

bool validateLegacyQBitReferences(
    const EvtProgram &evtProgram,
    const LegacyLuaExportLookups &lookups,
    const std::string &sourceName)
{
    std::set<uint32_t> customQBitsMissingQuestRows;

    for (const EvtEvent &event : evtProgram.getEvents())
    {
        for (const EvtInstruction &instruction : event.instructions)
        {
            if (!legacyOpcodeUsesVariableValue(instruction.opcode) || !instruction.value1)
            {
                continue;
            }

            const std::optional<uint32_t> qbitId = legacyQBitIdFromVariableValue(*instruction.value1);

            if (!qbitId)
            {
                continue;
            }

            if (*qbitId == 0)
            {
                std::cerr << "Invalid QBit(0) reference in " << sourceName
                          << " event " << event.eventId
                          << " step " << static_cast<unsigned>(instruction.step) << '\n';
                return false;
            }

            if (*qbitId >= CustomWorldQBitBegin && lookups.questNotes.find(*qbitId) == lookups.questNotes.end())
            {
                customQBitsMissingQuestRows.insert(*qbitId);
            }
        }
    }

    for (uint32_t qbitId : customQBitsMissingQuestRows)
    {
        std::cerr << "Warning: " << sourceName << " references custom-range QBit(" << qbitId
                  << ") without a visible row in quests.txt\n";
    }

    return true;
}

std::unordered_map<uint32_t, std::string> loadAwardTexts(
    const AssetFileSystem &assetFileSystem,
    const std::string &virtualPath)
{
    std::unordered_map<uint32_t, std::string> texts;
    std::vector<std::vector<std::string>> rows;

    if (!loadTextTableRows(assetFileSystem, virtualPath, rows))
    {
        return texts;
    }

    for (const std::vector<std::string> &row : rows)
    {
        if (row.size() <= 1)
        {
            continue;
        }

        const std::optional<uint32_t> parsedId = parseUint32Field(row[0]);
        const std::string awardText = normalizeWhitespace(row[1]);

        if (parsedId && !awardText.empty() && awardText != "0")
        {
            texts[*parsedId] = awardText;
        }
    }

    return texts;
}

std::unordered_map<uint32_t, std::string> loadLegacyInputStringAnswerTexts(
    const AssetFileSystem &assetFileSystem,
    const std::string &legacyEventsDir)
{
    std::unordered_map<uint32_t, std::string> texts;

    for (const std::string &entryName : assetFileSystem.enumerate(legacyEventsDir))
    {
        if (toLowerCopy(std::filesystem::path(entryName).extension().string()) != ".str")
        {
            continue;
        }

        const std::optional<std::vector<uint8_t>> bytes =
            assetFileSystem.readBinaryFile(legacyEventsDir + "/" + entryName);

        if (!bytes)
        {
            continue;
        }

        StrTable strTable = {};

        if (!strTable.loadFromBytes(*bytes))
        {
            continue;
        }

        const std::vector<std::string> &entries = strTable.getEntries();

        for (size_t index = 0; index < entries.size(); ++index)
        {
            const uint32_t textId = static_cast<uint32_t>(index);

            if (!entries[index].empty() && !texts.contains(textId))
            {
                texts.emplace(textId, entries[index]);
            }
        }
    }

    return texts;
}

std::string normalizeWhitespace(const std::string &value)
{
    std::string result;
    result.reserve(value.size());

    bool previousWasSpace = false;

    for (char character : value)
    {
        if (std::isspace(static_cast<unsigned char>(character)))
        {
            if (!previousWasSpace)
            {
                result.push_back(' ');
                previousWasSpace = true;
            }

            continue;
        }

        result.push_back(character);
        previousWasSpace = false;
    }

    return trimCopy(result);
}

std::unordered_map<uint32_t, std::string> loadDecompiledEventTitlesForScript(
    const std::filesystem::path &decompiledScriptPath)
{
    std::unordered_map<uint32_t, std::string> titles;
    std::ifstream inputStream(decompiledScriptPath);

    if (!inputStream)
    {
        return titles;
    }

    std::vector<std::string> lines;
    std::string line;

    while (std::getline(inputStream, line))
    {
        lines.push_back(line);
    }

    for (size_t lineIndex = 0; lineIndex < lines.size(); ++lineIndex)
    {
        const std::string &currentLine = lines[lineIndex];
        const size_t titleMarkerIndex = currentLine.find("-- \"");

        if (titleMarkerIndex == std::string::npos || !currentLine.starts_with("event "))
        {
            continue;
        }

        const std::optional<uint32_t> eventId =
            parseUint32Field(trimCopy(currentLine.substr(6, titleMarkerIndex - 6)));

        if (!eventId)
        {
            continue;
        }

        std::string title = currentLine.substr(titleMarkerIndex + 4);

        while (!title.empty() && title.back() != '"' && lineIndex + 1 < lines.size())
        {
            ++lineIndex;
            title += ' ';
            title += trimCopy(lines[lineIndex]);
        }

        if (!title.empty() && title.back() == '"')
        {
            title.pop_back();
        }

        title = normalizeWhitespace(title);

        if (!title.empty())
        {
            titles[*eventId] = title;
        }
    }

    return titles;
}

std::unordered_map<std::string, std::unordered_map<uint32_t, std::string>> loadDecompiledEventTitles(
    const std::filesystem::path &decompiledScriptsDir)
{
    std::unordered_map<std::string, std::unordered_map<uint32_t, std::string>> titlesByScriptStem;

    if (decompiledScriptsDir.empty() || !std::filesystem::is_directory(decompiledScriptsDir))
    {
        return titlesByScriptStem;
    }

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(decompiledScriptsDir))
    {
        if (!entry.is_regular_file() || toLowerCopy(entry.path().extension().string()) != ".txt")
        {
            continue;
        }

        std::unordered_map<uint32_t, std::string> titles = loadDecompiledEventTitlesForScript(entry.path());

        if (!titles.empty())
        {
            titlesByScriptStem[toLowerCopy(entry.path().stem().string())] = std::move(titles);
        }
    }

    return titlesByScriptStem;
}

uint32_t eventStepKey(uint32_t eventId, uint32_t step)
{
    return (eventId << 8) | step;
}

std::unordered_map<uint32_t, uint32_t> loadDecompiledSummonObjectTypesForScript(
    const std::filesystem::path &decompiledScriptPath)
{
    std::unordered_map<uint32_t, uint32_t> typesByEventStep;
    std::ifstream inputStream(decompiledScriptPath);

    if (!inputStream)
    {
        return typesByEventStep;
    }

    uint32_t currentEventId = 0;
    bool hasCurrentEvent = false;
    std::string line;

    while (std::getline(inputStream, line))
    {
        const std::string trimmed = trimCopy(line);

        if (trimmed.starts_with("event "))
        {
            const size_t idEnd = trimmed.find_first_not_of("0123456789", 6);
            const std::optional<uint32_t> parsedEventId =
                parseUint32Field(trimmed.substr(6, idEnd == std::string::npos ? std::string::npos : idEnd - 6));

            currentEventId = parsedEventId.value_or(0);
            hasCurrentEvent = parsedEventId.has_value();
            continue;
        }

        if (!hasCurrentEvent)
        {
            continue;
        }

        const size_t colonIndex = trimmed.find(':');
        const size_t summonIndex = trimmed.find("SummonObject");
        const size_t typeIndex = trimmed.find("Type = ");

        if (colonIndex == std::string::npos
            || summonIndex == std::string::npos
            || typeIndex == std::string::npos
            || summonIndex < colonIndex)
        {
            continue;
        }

        const std::optional<uint32_t> parsedStep = parseUint32Field(trimmed.substr(0, colonIndex));

        if (!parsedStep)
        {
            continue;
        }

        const size_t valueBegin = typeIndex + std::string_view("Type = ").size();
        const size_t valueEnd = trimmed.find_first_not_of("0123456789", valueBegin);
        const std::optional<uint32_t> parsedType =
            parseUint32Field(trimmed.substr(valueBegin, valueEnd - valueBegin));

        if (parsedType)
        {
            typesByEventStep[eventStepKey(currentEventId, *parsedStep)] = *parsedType;
        }
    }

    return typesByEventStep;
}

std::unordered_map<uint32_t, uint32_t> loadDecompiledSummonObjectTypes(
    const std::unordered_map<std::string, std::unordered_map<uint32_t, uint32_t>> &typesByScriptStem,
    const std::string &outputStem)
{
    const std::string lowerOutputStem = toLowerCopy(outputStem);
    auto iterator = typesByScriptStem.find(lowerOutputStem);

    if (iterator == typesByScriptStem.end()
        && lowerOutputStem.size() > 2
        && lowerOutputStem[0] == '6'
        && (lowerOutputStem[1] == 'd' || lowerOutputStem[1] == 't'))
    {
        iterator = typesByScriptStem.find(lowerOutputStem.substr(1));
    }

    if (iterator == typesByScriptStem.end())
    {
        return {};
    }

    return iterator->second;
}

std::unordered_map<std::string, std::unordered_map<uint32_t, uint32_t>> loadDecompiledSummonObjectTypes(
    const std::filesystem::path &decompiledScriptsDir)
{
    std::unordered_map<std::string, std::unordered_map<uint32_t, uint32_t>> typesByScriptStem;

    if (decompiledScriptsDir.empty() || !std::filesystem::is_directory(decompiledScriptsDir))
    {
        return typesByScriptStem;
    }

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(decompiledScriptsDir))
    {
        if (!entry.is_regular_file() || toLowerCopy(entry.path().extension().string()) != ".txt")
        {
            continue;
        }

        std::unordered_map<uint32_t, uint32_t> types = loadDecompiledSummonObjectTypesForScript(entry.path());

        if (!types.empty())
        {
            typesByScriptStem[toLowerCopy(entry.path().stem().string())] = std::move(types);
        }
    }

    return typesByScriptStem;
}

std::optional<uint32_t> readYamlUint32(const YAML::Node &node, const char *key)
{
    const YAML::Node childNode = node[key];

    if (!childNode || !childNode.IsScalar())
    {
        return std::nullopt;
    }

    try
    {
        return childNode.as<uint32_t>();
    }
    catch (const std::exception &)
    {
        return std::nullopt;
    }
}

std::string lookupMonsterName(
    const std::unordered_map<uint32_t, std::string> &monsterNames,
    uint32_t monsterInfoId)
{
    const auto iterator = monsterNames.find(monsterInfoId);

    if (iterator != monsterNames.end() && !iterator->second.empty())
    {
        return iterator->second;
    }

    return "monster info " + std::to_string(monsterInfoId);
}

void addActorGroupLabel(
    std::unordered_map<uint32_t, std::vector<std::string>> &labelsByGroup,
    uint32_t groupId,
    const std::string &label)
{
    if (label.empty())
    {
        return;
    }

    std::vector<std::string> &labels = labelsByGroup[groupId];

    if (std::find(labels.begin(), labels.end(), label) == labels.end())
    {
        labels.push_back(label);
    }
}

void collectActorGroupLabelFromActor(
    std::unordered_map<uint32_t, std::vector<std::string>> &labelsByGroup,
    const std::unordered_map<uint32_t, std::string> &monsterNames,
    const YAML::Node &actorNode)
{
    const std::optional<uint32_t> groupId = readYamlUint32(actorNode, "group");

    if (!groupId || *groupId == 0)
    {
        return;
    }

    const std::optional<uint32_t> monsterInfoId = readYamlUint32(actorNode, "monster_info_id");

    if (monsterInfoId && *monsterInfoId != 0)
    {
        addActorGroupLabel(labelsByGroup, *groupId, lookupMonsterName(monsterNames, *monsterInfoId));
    }
}

void collectActorGroupLabelsFromActors(
    std::unordered_map<uint32_t, std::vector<std::string>> &labelsByGroup,
    const std::unordered_map<uint32_t, std::string> &monsterNames,
    const YAML::Node &actorsNode)
{
    if (!actorsNode || !actorsNode.IsSequence())
    {
        return;
    }

    for (const YAML::Node &actorNode : actorsNode)
    {
        if (actorNode.IsMap())
        {
            collectActorGroupLabelFromActor(labelsByGroup, monsterNames, actorNode);
        }
    }
}

std::string formatSpawnLabel(const MapStatsEntry &mapEntry, uint16_t typeId, uint16_t index);

void collectActorGroupLabelsFromSpawns(
    std::unordered_map<uint32_t, std::vector<std::string>> &labelsByGroup,
    const YAML::Node &spawnsNode,
    const MapStatsEntry *pMapEntry)
{
    if (!spawnsNode || !spawnsNode.IsSequence())
    {
        return;
    }

    for (const YAML::Node &spawnNode : spawnsNode)
    {
        if (!spawnNode.IsMap())
        {
            continue;
        }

        const std::optional<uint32_t> groupId = readYamlUint32(spawnNode, "group");
        const std::optional<uint32_t> typeId = readYamlUint32(spawnNode, "type_id");
        const std::optional<uint32_t> index = readYamlUint32(spawnNode, "index");

        if (groupId && *groupId != 0 && typeId)
        {
            if (pMapEntry != nullptr && index)
            {
                addActorGroupLabel(
                    labelsByGroup,
                    *groupId,
                    formatSpawnLabel(*pMapEntry, static_cast<uint16_t>(*typeId), static_cast<uint16_t>(*index)));
            }
            else
            {
                addActorGroupLabel(labelsByGroup, *groupId, "outdoor spawn type " + std::to_string(*typeId));
            }
        }
    }
}

const MapEncounterInfo *encounterForSpawnIndex(const MapStatsEntry &mapEntry, uint16_t index)
{
    if (index == 1)
    {
        return &mapEntry.encounter1;
    }

    if (index == 2)
    {
        return &mapEntry.encounter2;
    }

    if (index == 3)
    {
        return &mapEntry.encounter3;
    }

    if (index >= 4 && index <= 12)
    {
        const uint16_t encounterSlot = static_cast<uint16_t>(((index - 4) % 3) + 1);
        return encounterForSpawnIndex(mapEntry, encounterSlot);
    }

    return nullptr;
}

std::optional<std::string> resolveSpawnMonsterLabel(const MapStatsEntry &mapEntry, uint16_t typeId, uint16_t index)
{
    if (typeId != 3)
    {
        return std::nullopt;
    }

    const MapEncounterInfo *pEncounter = encounterForSpawnIndex(mapEntry, index);

    if (pEncounter == nullptr || pEncounter->monsterName.empty())
    {
        return std::nullopt;
    }

    char tierSuffix = 'A';

    if (index >= 4 && index <= 12)
    {
        tierSuffix = static_cast<char>('A' + ((index - 4) / 3));
    }

    return pEncounter->monsterName + " " + std::string(1, tierSuffix);
}

std::string formatSpawnLabel(const MapStatsEntry &mapEntry, uint16_t typeId, uint16_t index)
{
    const std::optional<std::string> monsterLabel = resolveSpawnMonsterLabel(mapEntry, typeId, index);

    if (monsterLabel)
    {
        return "spawn " + *monsterLabel;
    }

    return "spawn type " + std::to_string(typeId) + " index " + std::to_string(index);
}

void collectActorGroupLabelsFromIndoorBlvSpawns(
    std::unordered_map<uint32_t, std::vector<std::string>> &labelsByGroup,
    const AssetFileSystem &assetFileSystem,
    const std::string &outputStem,
    const MapStatsEntry &mapEntry)
{
    const std::string fileName = mapEntry.fileName.empty() ? (outputStem + ".blv") : mapEntry.fileName;
    const std::string lowerFileName = toLowerCopy(fileName);
    const std::vector<std::string> candidates = {
        "Data/games/" + fileName,
        "Data/games/" + lowerFileName,
        "Data/games/" + outputStem + ".blv",
        "Data/games/" + toLowerCopy(outputStem) + ".blv",
    };
    std::string resolvedPath;
    const std::optional<std::vector<uint8_t>> bytes =
        readFirstExistingBinary(assetFileSystem, candidates, resolvedPath);

    if (!bytes)
    {
        return;
    }

    const IndoorMapDataLoader loader;
    const std::optional<IndoorMapData> indoorMapData = loader.loadFromBytes(*bytes);

    if (!indoorMapData)
    {
        return;
    }

    for (const IndoorSpawn &spawn : indoorMapData->spawns)
    {
        if (spawn.group == 0)
        {
            continue;
        }

        addActorGroupLabel(
            labelsByGroup,
            spawn.group,
            formatSpawnLabel(mapEntry, spawn.typeId, spawn.index));
    }
}

std::string formatActorGroupLabels(std::vector<std::string> labels)
{
    std::sort(labels.begin(), labels.end());

    constexpr size_t MaxLabelsToShow = 4;
    std::ostringstream stream;

    for (size_t index = 0; index < labels.size() && index < MaxLabelsToShow; ++index)
    {
        if (index != 0)
        {
            stream << ", ";
        }

        stream << labels[index];
    }

    if (labels.size() > MaxLabelsToShow)
    {
        stream << ", +" << (labels.size() - MaxLabelsToShow) << " more";
    }

    return stream.str();
}

std::unordered_map<uint32_t, std::string> buildActorGroupNameLookup(
    const AssetFileSystem &assetFileSystem,
    const std::string &outputStem,
    const std::unordered_map<uint32_t, std::string> &monsterNames,
    const MapStatsEntry *pMapEntry)
{
    std::unordered_map<uint32_t, std::string> groupNames;
    const std::string scenePath = "Data/games/" + toLowerCopy(outputStem) + ".scene.yml";
    const std::optional<std::string> sceneText = assetFileSystem.readTextFile(scenePath);

    if (!sceneText)
    {
        return groupNames;
    }

    YAML::Node sceneNode;

    try
    {
        sceneNode = YAML::Load(*sceneText);
    }
    catch (const std::exception &)
    {
        return groupNames;
    }

    std::unordered_map<uint32_t, std::vector<std::string>> labelsByGroup;
    collectActorGroupLabelsFromActors(labelsByGroup, monsterNames, sceneNode["initial_state"]["actors"]);
    collectActorGroupLabelsFromSpawns(labelsByGroup, sceneNode["spawns"], pMapEntry);

    if (pMapEntry != nullptr && toLowerCopy(std::filesystem::path(pMapEntry->fileName).extension().string()) == ".blv")
    {
        collectActorGroupLabelsFromIndoorBlvSpawns(labelsByGroup, assetFileSystem, outputStem, *pMapEntry);
    }

    for (const auto &entry : labelsByGroup)
    {
        groupNames[entry.first] = formatActorGroupLabels(entry.second);
    }

    return groupNames;
}

std::string encounterDisplayName(const MapEncounterInfo &encounter)
{
    if (!encounter.monsterName.empty())
    {
        return encounter.monsterName;
    }

    return encounter.pictureName;
}

void populateMapEncounterNames(LegacyLuaExportLookups &lookups, const MapStatsEntry *pMapEntry)
{
    lookups.mapEncounterNames.clear();

    if (pMapEntry == nullptr)
    {
        return;
    }

    const MapEncounterInfo *encounters[] = {
        &pMapEntry->encounter1,
        &pMapEntry->encounter2,
        &pMapEntry->encounter3,
    };

    constexpr size_t EncounterCount = sizeof(encounters) / sizeof(encounters[0]);

    for (size_t index = 0; index < EncounterCount; ++index)
    {
        const std::string name = encounterDisplayName(*encounters[index]);

        if (name.empty())
        {
            continue;
        }

        lookups.mapEncounterNames[static_cast<uint32_t>(index + 1)] = name;
    }
}

bool exportLegacyProgram(
    const AssetFileSystem &assetFileSystem,
    const std::filesystem::path &scriptsRoot,
    const std::filesystem::path &dumpsRoot,
    const std::string &legacyEventsDir,
    const std::string &legacyBaseName,
    const std::string &outputStem,
    const LegacyLuaExportLookups &baseLookups,
    const std::unordered_map<std::string, std::unordered_map<uint32_t, std::string>> &decompiledEventTitles,
    const std::unordered_map<std::string, std::unordered_map<uint32_t, uint32_t>> &decompiledSummonObjectTypes,
    const MapStatsEntry *pMapEntry,
    bool globalScope,
    LegacyEventVersion version)
{
    std::string resolvedEvtPath;
    const std::optional<std::vector<uint8_t>> evtBytes = readFirstExistingBinary(
        assetFileSystem,
        buildLegacyScriptPathCandidates(legacyEventsDir, legacyBaseName, ".evt"),
        resolvedEvtPath
    );

    if (!evtBytes)
    {
        return true;
    }

    EvtProgram evtProgram = {};

    if (!evtProgram.loadFromBytes(*evtBytes))
    {
        std::cerr << "Failed to parse legacy event program: " << resolvedEvtPath << '\n';
        return false;
    }

    std::string resolvedStrPath;
    const std::optional<std::vector<uint8_t>> strBytes = readFirstExistingBinary(
        assetFileSystem,
        buildLegacyScriptPathCandidates(legacyEventsDir, legacyBaseName, ".str"),
        resolvedStrPath
    );
    StrTable strTable = {};

    if (strBytes && !strTable.loadFromBytes(*strBytes))
    {
        std::cerr << "Failed to parse legacy string table: " << resolvedStrPath << '\n';
        return false;
    }

    EventIrProgram eventIrProgram = {};
    const auto resolveHouseName =
        [&baseLookups](uint32_t houseId) -> std::optional<std::string>
        {
            const auto iterator = baseLookups.houseNames.find(houseId);

            if (iterator != baseLookups.houseNames.end())
            {
                return iterator->second;
            }

            return std::nullopt;
        };
    const auto resolveNpcText =
        [&baseLookups](uint32_t textId) -> std::optional<std::string>
        {
            const auto iterator = baseLookups.npcTexts.find(textId);
            return iterator != baseLookups.npcTexts.end() ? std::optional<std::string>(iterator->second) : std::nullopt;
        };

    if (!buildEventIrProgramFromLegacySource(
            eventIrProgram,
            evtProgram,
            strTable,
            resolveHouseName,
            resolveNpcText,
            static_cast<int>(version)))
    {
        std::cerr << "Failed to convert legacy event program to IR: " << legacyBaseName << '\n';
        return false;
    }

    const std::filesystem::path luaPath = globalScope
        ? (scriptsRoot / "Global.lua")
        : (scriptsRoot / "maps" / (outputStem + ".lua"));
    const std::filesystem::path evtDumpPath = dumpsRoot / (globalScope ? "Global.evt.txt" : (outputStem + ".evt.txt"));
    const std::filesystem::path irDumpPath = dumpsRoot / (globalScope ? "Global.ir.txt" : (outputStem + ".ir.txt"));
    LegacyLuaExportLookups lookups = baseLookups;

    if (!globalScope)
    {
        const auto iterator = lookups.mapNamesByFile.find(toLowerCopy(outputStem));

        if (iterator != lookups.mapNamesByFile.end())
        {
            lookups.mapName = iterator->second;
        }

        lookups.actorGroupNames = buildActorGroupNameLookup(
            assetFileSystem,
            outputStem,
            lookups.monsterNames,
            pMapEntry);
        populateMapEncounterNames(lookups, pMapEntry);
        lookups.summonObjectTypesByEventStep =
            loadDecompiledSummonObjectTypes(decompiledSummonObjectTypes, outputStem);
    }

    const auto titleIterator = decompiledEventTitles.find(toLowerCopy(outputStem));

    if (titleIterator != decompiledEventTitles.end())
    {
        lookups.eventTitles = titleIterator->second;
    }

    if (!validateLegacyQBitReferences(evtProgram, lookups, legacyBaseName))
    {
        return false;
    }

    if (!writeTextFile(luaPath, OpenYAMM::Game::generateLegacyEventLuaChunk(
            evtProgram,
            strTable,
            lookups,
            globalScope ? LegacyLuaExportScope::Global : LegacyLuaExportScope::Map,
            version))
        || !writeTextFile(evtDumpPath, evtProgram.dump(strTable))
        || !writeTextFile(irDumpPath, eventIrProgram.dump()))
    {
        std::cerr << "Failed to write generated event assets for " << legacyBaseName << '\n';
        return false;
    }

    return true;
}
}

int main(int argc, char **argv)
{
    ApplicationConfig config = ApplicationConfig::createDefault();
    std::optional<std::string> mapFilter;
    std::optional<std::filesystem::path> luaExportConfigPath;
    std::optional<std::string> legacyEventsDirOverride;
    std::optional<LegacyEventVersion> legacyEventVersionOverride;

    if (!parseArguments(
            argc,
            argv,
            config,
            mapFilter,
            luaExportConfigPath,
            legacyEventsDirOverride,
            legacyEventVersionOverride))
    {
        return 2;
    }

    LuaExportTablePaths tablePaths = {};

    if (luaExportConfigPath && !loadLuaExportConfig(*luaExportConfigPath, tablePaths))
    {
        std::cerr << "Failed to load Lua export config: " << luaExportConfigPath->string() << '\n';
        return 1;
    }

    if (legacyEventsDirOverride)
    {
        tablePaths.legacyEventsDir = *legacyEventsDirOverride;
    }

    if (legacyEventVersionOverride)
    {
        tablePaths.legacyEventVersion = *legacyEventVersionOverride;
    }

    if (tablePaths.decompiledScriptsDir.empty())
    {
        const std::filesystem::path siblingDecompiledScriptsDir =
            std::filesystem::current_path().parent_path() / "OpenMM8_Data" / "DecompiledScripts";

        if (std::filesystem::is_directory(siblingDecompiledScriptsDir))
        {
            tablePaths.decompiledScriptsDir = siblingDecompiledScriptsDir.string();
        }
    }

    AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(
            std::filesystem::current_path(),
            config.assetRoot,
            config.assetScaleTier,
            config.activeWorldId))
    {
        std::cerr << "Failed to initialize asset file system\n";
        return 1;
    }

    MapStats mapStats = {};

    if (!loadMapStats(assetFileSystem, tablePaths.mapStats, mapStats))
    {
        std::cerr << "Failed to load map stats\n";
        return 1;
    }

    LegacyLuaExportLookups lookups = {};
    lookups.mapNamesByFile = buildMapNameLookup(mapStats);
    lookups.houseNames = loadHouseNames(assetFileSystem, tablePaths.houseData);
    lookups.npcTexts = loadNpcTexts(assetFileSystem, tablePaths.npcTopicText);
    lookups.npcNames = loadNpcNames(assetFileSystem, tablePaths.npc);
    lookups.rosterNames = loadRosterNames(assetFileSystem, tablePaths.roster);
    lookups.npcTopicNames = loadNpcTopicNames(assetFileSystem, tablePaths.npcTopic);
    lookups.npcGreetingTexts = loadNpcGreetingTexts(assetFileSystem, tablePaths.npcGreeting);
    lookups.npcGroupNames = loadNpcGroupNames(assetFileSystem, tablePaths.npcGroup);
    lookups.npcNewsTexts = loadNpcNewsTexts(assetFileSystem, tablePaths.npcNews);
    lookups.itemNames = loadItemNames(assetFileSystem, tablePaths.items);
    lookups.objectPayloadNames = loadObjectPayloadNames(assetFileSystem, tablePaths.objectList);
    lookups.monsterNames = loadMonsterNames(assetFileSystem, tablePaths.monsterData);
    lookups.placedMonsterNames = loadPlacedMonsterNames(assetFileSystem, tablePaths.placeMon);
    lookups.spellNames = loadSpellNames(assetFileSystem, tablePaths.spells, tablePaths.spellsSupplemental);
    std::string questNotesError;
    lookups.questNotes = loadQuestNotes(assetFileSystem, tablePaths.quests, questNotesError);

    if (!questNotesError.empty())
    {
        std::cerr << "Failed to validate quest note table: " << questNotesError << '\n';
        return 1;
    }

    lookups.autonoteTexts = loadAutonoteTexts(assetFileSystem, tablePaths.autonote);
    lookups.awardTexts = loadAwardTexts(assetFileSystem, tablePaths.awards);
    lookups.inputStringAnswerTexts =
        loadLegacyInputStringAnswerTexts(assetFileSystem, tablePaths.legacyEventsDir);
    const std::unordered_map<std::string, std::unordered_map<uint32_t, std::string>> decompiledEventTitles =
        loadDecompiledEventTitles(tablePaths.decompiledScriptsDir);
    const std::unordered_map<std::string, std::unordered_map<uint32_t, uint32_t>> decompiledSummonObjectTypes =
        loadDecompiledSummonObjectTypes(tablePaths.decompiledScriptsDir);
    const std::filesystem::path globalScriptsRoot =
        assetFileSystem.getDevelopmentRoot() / "engine" / "events";
    const std::filesystem::path worldScriptsRoot =
        assetFileSystem.getDevelopmentRoot() / "worlds" / config.activeWorldId / "events";
    const std::filesystem::path dumpsRoot = std::filesystem::current_path() / "script_dumps";

    if (!exportLegacyProgram(
            assetFileSystem,
            globalScriptsRoot,
            dumpsRoot,
            tablePaths.legacyEventsDir,
            "Global",
            "Global",
            lookups,
            decompiledEventTitles,
            decompiledSummonObjectTypes,
            nullptr,
            true,
            tablePaths.legacyEventVersion))
    {
        return 1;
    }

    size_t exportedMapCount = 0;

    for (const MapStatsEntry &entry : mapStats.getEntries())
    {
        if (entry.fileName.empty())
        {
            continue;
        }

        const std::string mapStem = std::filesystem::path(entry.fileName).stem().string();
        const std::string lowerMapStem = toLowerCopy(mapStem);

        if (mapFilter && *mapFilter != lowerMapStem && *mapFilter != mapStem)
        {
            continue;
        }

        if (!exportLegacyProgram(
                assetFileSystem,
                worldScriptsRoot,
                dumpsRoot,
                tablePaths.legacyEventsDir,
                mapStem,
                lowerMapStem,
                lookups,
                decompiledEventTitles,
                decompiledSummonObjectTypes,
                &entry,
                false,
                tablePaths.legacyEventVersion))
        {
            return 1;
        }

        const std::string extension = toLowerCopy(std::filesystem::path(entry.fileName).extension().string());

        if (extension == ".odm" || extension == ".blv")
        {
            std::string resolvedEvtPath;
            if (readFirstExistingBinary(
                    assetFileSystem,
                    buildLegacyScriptPathCandidates(tablePaths.legacyEventsDir, mapStem, ".evt"),
                    resolvedEvtPath))
            {
                ++exportedMapCount;
            }
        }
    }

    std::cout << "Exported legacy event assets:\n";
    std::cout << "  global=yes\n";
    std::cout << "  map_count=" << exportedMapCount << '\n';
    std::cout << "  legacy_event_version=" << static_cast<int>(tablePaths.legacyEventVersion) << '\n';
    std::cout << "  global_scripts_root=" << globalScriptsRoot << '\n';
    std::cout << "  world_scripts_root=" << worldScriptsRoot << '\n';
    std::cout << "  dumps_root=" << dumpsRoot << '\n';
    return 0;
}
