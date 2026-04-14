#include "engine/ApplicationConfig.h"
#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/TextTable.h"
#include "game/tables/MapStats.h"
#include "tools/EventIr.h"
#include "tools/EventIrLegacyImport.h"
#include "tools/LegacyLuaExport.h"
#include "tools/legacy_events/EvtProgram.h"
#include "tools/legacy_events/StrTable.h"

#include <algorithm>
#include <cstdlib>
#include <cctype>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace
{
using OpenYAMM::Engine::AssetFileSystem;
using OpenYAMM::Engine::ApplicationConfig;
using OpenYAMM::Engine::TextTable;
using OpenYAMM::Game::EventIrProgram;
using OpenYAMM::Game::EvtProgram;
using OpenYAMM::Game::LegacyLuaExportLookups;
using OpenYAMM::Game::LegacyLuaExportScope;
using OpenYAMM::Game::MapStats;
using OpenYAMM::Game::MapStatsEntry;
using OpenYAMM::Game::StrTable;

bool parseArguments(
    int argc,
    char **argv,
    ApplicationConfig &config,
    std::optional<std::string> &mapFilter,
    std::optional<std::filesystem::path> &luaExportConfigPath,
    std::optional<std::string> &legacyEventsDir)
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
    std::string mapStats = "Data/data_tables/map_stats.txt";
    std::string houseData = "Data/data_tables/house_data.txt";
    std::string npcTopicText = "Data/data_tables/npc_topic_text.txt";
    std::string items = "Data/data_tables/items.txt";
    std::string objectList = "Data/data_tables/object_list.txt";
    std::string spells = "Data/data_tables/spells.txt";
    std::string spellsSupplemental = "Data/data_tables/spells_supplemental.txt";
    std::string npc = "Data/data_tables/npc.txt";
    std::string npcGroup = "Data/data_tables/english/npc_group.txt";
    std::string npcNews = "Data/data_tables/npc_news.txt";
    std::string legacyEventsDir = "_legacy/events";
    std::string decompiledScriptsDir;
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

        if (sectionName != "paths")
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
        else if (key == "items")
        {
            tablePaths.items = value;
        }
        else if (key == "object_list")
        {
            tablePaths.objectList = value;
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
        else if (key == "npc_group")
        {
            tablePaths.npcGroup = value;
        }
        else if (key == "npc_news")
        {
            tablePaths.npcNews = value;
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

        if (!parsedId || row[2].empty())
        {
            continue;
        }

        names[*parsedId] = row[2];
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

bool exportLegacyProgram(
    const AssetFileSystem &assetFileSystem,
    const std::filesystem::path &scriptsRoot,
    const std::filesystem::path &dumpsRoot,
    const std::string &legacyEventsDir,
    const std::string &legacyBaseName,
    const std::string &outputStem,
    const LegacyLuaExportLookups &baseLookups,
    const std::unordered_map<std::string, std::unordered_map<uint32_t, std::string>> &decompiledEventTitles,
    bool globalScope)
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
            return iterator != baseLookups.houseNames.end() ? std::optional<std::string>(iterator->second) : std::nullopt;
        };
    const auto resolveNpcText =
        [&baseLookups](uint32_t textId) -> std::optional<std::string>
        {
            const auto iterator = baseLookups.npcTexts.find(textId);
            return iterator != baseLookups.npcTexts.end() ? std::optional<std::string>(iterator->second) : std::nullopt;
        };

    if (!buildEventIrProgramFromLegacySource(eventIrProgram, evtProgram, strTable, resolveHouseName, resolveNpcText))
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
    }

    const auto titleIterator = decompiledEventTitles.find(toLowerCopy(outputStem));

    if (titleIterator != decompiledEventTitles.end())
    {
        lookups.eventTitles = titleIterator->second;
    }

    if (!writeTextFile(luaPath, OpenYAMM::Game::generateLegacyEventLuaChunk(
            evtProgram,
            strTable,
            lookups,
            globalScope ? LegacyLuaExportScope::Global : LegacyLuaExportScope::Map))
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

    if (!parseArguments(argc, argv, config, mapFilter, luaExportConfigPath, legacyEventsDirOverride))
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

    if (!assetFileSystem.initialize(std::filesystem::current_path(), config.assetRoot, config.assetScaleTier))
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
    lookups.npcGroupNames = loadNpcGroupNames(assetFileSystem, tablePaths.npcGroup);
    lookups.npcNewsTexts = loadNpcNewsTexts(assetFileSystem, tablePaths.npcNews);
    lookups.itemNames = loadItemNames(assetFileSystem, tablePaths.items);
    lookups.objectPayloadNames = loadObjectPayloadNames(assetFileSystem, tablePaths.objectList);
    lookups.spellNames = loadSpellNames(assetFileSystem, tablePaths.spells, tablePaths.spellsSupplemental);
    const std::unordered_map<std::string, std::unordered_map<uint32_t, std::string>> decompiledEventTitles =
        loadDecompiledEventTitles(tablePaths.decompiledScriptsDir);
    const std::filesystem::path scriptsRoot = assetFileSystem.getDevelopmentRoot() / "Data" / "scripts";
    const std::filesystem::path dumpsRoot = std::filesystem::current_path() / "script_dumps";

    if (!exportLegacyProgram(
            assetFileSystem,
            scriptsRoot,
            dumpsRoot,
            tablePaths.legacyEventsDir,
            "Global",
            "Global",
            lookups,
            decompiledEventTitles,
            true))
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
                scriptsRoot,
                dumpsRoot,
                tablePaths.legacyEventsDir,
                mapStem,
                lowerMapStem,
                lookups,
                decompiledEventTitles,
                false))
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
    std::cout << "  scripts_root=" << scriptsRoot << '\n';
    std::cout << "  dumps_root=" << dumpsRoot << '\n';
    return 0;
}
