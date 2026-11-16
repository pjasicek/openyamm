#include "game/content/NamedMods.h"

#include "engine/TextTable.h"
#include "game/content/ContentTableComposer.h"
#include "game/content/RulesetDefinition.h"
#include "game/tables/MapStats.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <exception>
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
#include <system_error>

namespace OpenYAMM::Game
{
namespace
{
constexpr const char *EngineDataTableRoot = "engine/data_tables/";
constexpr const char *MapsDomain = "maps";

std::string pathText(const std::filesystem::path &path)
{
    const std::u8string text = path.generic_u8string();
    return std::string(text.begin(), text.end());
}

std::optional<std::string> readFileText(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);

    if (!file)
    {
        return std::nullopt;
    }

    std::ostringstream text;
    text << file.rdbuf();
    return text.str();
}

// A path inside the mod's folder: relative, forward slashes, no `..` and no drive.
bool isContainedRelativePath(const std::string &path)
{
    if (path.empty() || path.front() == '/' || path.find('\\') != std::string::npos
        || path.find(':') != std::string::npos)
    {
        return false;
    }

    std::istringstream parts(path);
    std::string part;

    while (std::getline(parts, part, '/'))
    {
        if (part.empty() || part == "." || part == "..")
        {
            return false;
        }
    }

    return true;
}

bool scalarText(const YAML::Node &node, const char *pKey, std::string &value, std::string &errorMessage)
{
    const YAML::Node child = node[pKey];

    if (!child)
    {
        return true;
    }

    if (!child.IsScalar())
    {
        errorMessage = std::string("'") + pKey + "' must be text";
        return false;
    }

    value = child.Scalar();
    return true;
}

const ContentIdRangeDefinition *findRange(const std::vector<ContentIdRangeDefinition> &ranges, const char *pDomain)
{
    for (const ContentIdRangeDefinition &range : ranges)
    {
        if (range.domain == pDomain)
        {
            return &range;
        }
    }

    return nullptr;
}

bool inRange(const ContentIdRangeDefinition *pRange, uint32_t value)
{
    return pRange != nullptr && pRange->begin <= value && value <= pRange->end;
}

std::string rangeText(const ContentIdRangeDefinition &range)
{
    return std::to_string(range.begin) + "-" + std::to_string(range.end);
}

std::optional<std::vector<std::vector<std::string>>> tableRows(const std::string &text)
{
    const std::optional<Engine::TextTable> table = Engine::TextTable::parseTabSeparated(text);

    if (!table)
    {
        return std::nullopt;
    }

    std::vector<std::vector<std::string>> rows;

    for (size_t rowIndex = 0; rowIndex < table->getRowCount(); ++rowIndex)
    {
        const std::vector<std::string> &row = table->getRow(rowIndex);
        const bool blank = std::all_of(row.begin(), row.end(),
            [](const std::string &cell)
            {
                return cell.find_first_not_of(" \t\r\n") == std::string::npos;
            });

        if (!blank)
        {
            rows.push_back(row);
        }
    }

    return rows;
}

// The reason `mod` cannot be on beside the owners and the mods already on, or empty.
std::string clashReason(
    const NamedModManifest &mod,
    const std::vector<NamedModRangeOwner> &owners,
    const std::vector<const NamedModManifest *> &earlier)
{
    const ContentIdRangeDefinition *pOwnMaps = findRange(mod.idRanges, MapsDomain);

    for (uint32_t number : mod.mapNumbers)
    {
        if (pOwnMaps != nullptr && !inRange(pOwnMaps, number))
        {
            return "map number " + std::to_string(number) + " is outside its own maps range " + rangeText(*pOwnMaps);
        }
    }

    for (const NamedModRangeOwner &owner : owners)
    {
        if (const std::optional<std::string> domain = overlappingContentIdRange(mod.idRanges, owner.ranges))
        {
            return "its " + *domain + " ids overlap those of " + owner.name;
        }

        for (uint32_t number : mod.mapNumbers)
        {
            if (inRange(findRange(owner.ranges, MapsDomain), number))
            {
                return "map number " + std::to_string(number) + " lies in the maps range of " + owner.name;
            }
        }
    }

    for (const NamedModManifest *pOther : earlier)
    {
        if (const std::optional<std::string> domain = overlappingContentIdRange(mod.idRanges, pOther->idRanges))
        {
            return "its " + *domain + " ids overlap those of mod " + pOther->id;
        }

        const ContentIdRangeDefinition *pOtherMaps = findRange(pOther->idRanges, MapsDomain);

        for (uint32_t number : mod.mapNumbers)
        {
            if (inRange(pOtherMaps, number)
                || std::find(pOther->mapNumbers.begin(), pOther->mapNumbers.end(), number) != pOther->mapNumbers.end())
            {
                return "map number " + std::to_string(number) + " belongs to mod " + pOther->id;
            }
        }

        for (uint32_t number : pOther->mapNumbers)
        {
            if (inRange(pOwnMaps, number))
            {
                return "its maps range " + rangeText(*pOwnMaps) + " holds map number " + std::to_string(number)
                    + " of mod " + pOther->id;
            }
        }

        for (const NamedModMap &map : mod.maps)
        {
            for (const NamedModMap &otherMap : pOther->maps)
            {
                if (map.kind == "new" && otherMap.kind == "new" && map.world == otherMap.world
                    && map.file == otherMap.file)
                {
                    return "its new map " + map.file + " is a new map of mod " + pOther->id + " too";
                }
            }
        }
    }

    return {};
}

NamedModEntry *findMutable(NamedModCatalog &catalog, const std::string &id)
{
    for (NamedModEntry &entry : catalog.mods)
    {
        if (entry.id == id)
        {
            return &entry;
        }
    }

    return nullptr;
}

bool writeTextAtomically(const std::filesystem::path &path, const std::string &text, std::string &errorMessage)
{
    std::filesystem::path temporary = path;
    temporary += ".tmp";

    {
        std::ofstream file(temporary, std::ios::binary | std::ios::trunc);

        if (!file || !(file << text) || !file.flush())
        {
            errorMessage = "could not write " + pathText(temporary);
            return false;
        }
    }

    std::error_code error;
    std::filesystem::rename(temporary, path, error);

    if (error)
    {
        errorMessage = "could not replace " + pathText(path) + ": " + error.message();
        std::filesystem::remove(temporary, error);
        return false;
    }

    return true;
}

// The ranges every mounted world and every available ruleset declare.
bool collectRangeOwners(
    const Engine::AssetFileSystem &assetFileSystem,
    std::vector<NamedModRangeOwner> &owners,
    std::string &errorMessage)
{
    std::vector<WorldManifest> worlds;

    if (!loadMountedWorldManifests(assetFileSystem, worlds, errorMessage))
    {
        return false;
    }

    for (const WorldManifest &world : worlds)
    {
        owners.push_back({"world " + world.id, world.idRanges});
    }

    std::vector<RulesetDefinition> rulesets;

    if (!loadAvailableRulesets(assetFileSystem, rulesets, errorMessage))
    {
        return false;
    }

    for (const RulesetDefinition &ruleset : rulesets)
    {
        if (!ruleset.idRanges.empty())
        {
            owners.push_back({"ruleset " + ruleset.id, ruleset.idRanges});
        }
    }

    return true;
}

// The first mod On whose rows do not apply to the tables as mounted (each table read, then every mod's rows in order;
// map_stats.txt is parsed as the game parses it), with the reason; nullopt when all apply.
std::optional<std::pair<std::string, std::string>> firstModWithFailingRows(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<NamedModManifest> &mods)
{
    std::set<std::string> tables;

    for (const NamedModManifest &mod : mods)
    {
        for (const NamedModTable &table : mod.tables)
        {
            tables.insert(table.table);
        }
    }

    for (const std::string &table : tables)
    {
        const std::string virtualPath = EngineDataTableRoot + table;
        const std::optional<std::string> text = assetFileSystem.readTextFile(virtualPath);
        const std::optional<Engine::TextTable> parsed = text ? Engine::TextTable::parseTabSeparated(*text)
                                                             : std::nullopt;
        // The table as the game reads it, blank rows included.
        std::vector<std::vector<std::string>> rows;

        for (size_t rowIndex = 0; parsed && rowIndex < parsed->getRowCount(); ++rowIndex)
        {
            rows.push_back(parsed->getRow(rowIndex));
        }

        for (const NamedModManifest &mod : mods)
        {
            bool changed = false;

            for (const NamedModTable &modTable : mod.tables)
            {
                if (modTable.table != table)
                {
                    continue;
                }

                if (!parsed)
                {
                    return std::make_pair(mod.id, table + ": the game has no table " + virtualPath);
                }

                std::string error;

                if (!applyNamedModTable(rows, modTable, error))
                {
                    return std::make_pair(mod.id, table + ": " + error);
                }

                changed = true;
            }

            MapStats mapStats;

            if (changed && table == "map_stats.txt" && !mapStats.loadFromRows(rows))
            {
                return std::make_pair(mod.id, table + ": the table does not load with them (the line above says why)");
            }
        }
    }

    return std::nullopt;
}
}

bool isValidNamedModId(const std::string &id)
{
    return !id.empty() && id != "engine" && id != "worlds"
        && std::all_of(id.begin(), id.end(),
            [](char character)
            {
                return (character >= 'a' && character <= 'z') || (character >= '0' && character <= '9')
                    || character == '_';
            });
}

std::optional<NamedModManifest> parseNamedModManifest(
    const std::string &yamlText,
    const std::string &folderName,
    std::string &errorMessage)
{
    errorMessage.clear();
    NamedModManifest manifest;

    try
    {
        const YAML::Node root = YAML::Load(yamlText);

        if (!root || !root.IsMap())
        {
            errorMessage = "mod.yml must be a map";
            return std::nullopt;
        }

        static const std::set<std::string> KnownKeys = {"format", "id", "name", "version", "author", "description",
            "worlds", "maps", "tables", "map_numbers", "idRanges"};

        for (YAML::const_iterator iterator = root.begin(); iterator != root.end(); ++iterator)
        {
            if (!iterator->first.IsScalar() || !KnownKeys.contains(iterator->first.Scalar()))
            {
                errorMessage = "mod.yml has an unknown key '" + iterator->first.as<std::string>("") + "'";
                return std::nullopt;
            }
        }

        if (!root["format"] || !root["format"].IsScalar() || root["format"].as<int>(0) != NamedModManifestFormat)
        {
            errorMessage = "mod.yml needs format: " + std::to_string(NamedModManifestFormat);
            return std::nullopt;
        }

        if (!scalarText(root, "id", manifest.id, errorMessage) || !scalarText(root, "name", manifest.name, errorMessage)
            || !scalarText(root, "version", manifest.version, errorMessage)
            || !scalarText(root, "author", manifest.author, errorMessage)
            || !scalarText(root, "description", manifest.description, errorMessage))
        {
            return std::nullopt;
        }

        if (!isValidNamedModId(manifest.id) || manifest.id != folderName)
        {
            errorMessage = "id '" + manifest.id + "' must be lower case letters, digits and underscores, not engine "
                "or worlds, and the name of its folder '" + folderName + "'";
            return std::nullopt;
        }

        if (manifest.name.empty() || manifest.version.empty())
        {
            errorMessage = "mod.yml needs a name and a version";
            return std::nullopt;
        }

        if (const YAML::Node worlds = root["worlds"])
        {
            if (!worlds.IsSequence())
            {
                errorMessage = "'worlds' must be a list";
                return std::nullopt;
            }

            for (const YAML::Node &world : worlds)
            {
                if (!world.IsScalar() || world.Scalar().empty())
                {
                    errorMessage = "'worlds' must list world ids";
                    return std::nullopt;
                }

                manifest.worlds.push_back(world.Scalar());
            }
        }

        if (const YAML::Node maps = root["maps"])
        {
            if (!maps.IsSequence())
            {
                errorMessage = "'maps' must be a list";
                return std::nullopt;
            }

            for (const YAML::Node &mapNode : maps)
            {
                NamedModMap map;

                if (!mapNode.IsMap() || !scalarText(mapNode, "file", map.file, errorMessage)
                    || !scalarText(mapNode, "world", map.world, errorMessage)
                    || !scalarText(mapNode, "kind", map.kind, errorMessage))
                {
                    errorMessage = "each of 'maps' needs a file, a world and a kind";
                    return std::nullopt;
                }

                if (map.file.empty() || map.world.empty() || (map.kind != "new" && map.kind != "overlay"))
                {
                    errorMessage = "each of 'maps' needs a file, a world and a kind new or overlay";
                    return std::nullopt;
                }

                std::transform(map.file.begin(), map.file.end(), map.file.begin(),
                    [](unsigned char character) { return static_cast<char>(std::tolower(character)); });
                manifest.maps.push_back(std::move(map));
            }
        }

        if (const YAML::Node tables = root["tables"])
        {
            if (!tables.IsSequence())
            {
                errorMessage = "'tables' must be a list";
                return std::nullopt;
            }

            for (const YAML::Node &tableNode : tables)
            {
                NamedModTable table;

                if (!tableNode.IsMap() || !scalarText(tableNode, "table", table.table, errorMessage)
                    || !scalarText(tableNode, "override", table.overridePath, errorMessage)
                    || !scalarText(tableNode, "append", table.appendPath, errorMessage))
                {
                    errorMessage = "each of 'tables' needs a table and its override or append file";
                    return std::nullopt;
                }

                if (!isContainedRelativePath(table.table) || (table.overridePath.empty() && table.appendPath.empty())
                    || (!table.overridePath.empty() && !isContainedRelativePath(table.overridePath))
                    || (!table.appendPath.empty() && !isContainedRelativePath(table.appendPath)))
                {
                    errorMessage = "table '" + table.table + "' needs an override or append file inside the mod";
                    return std::nullopt;
                }

                manifest.tables.push_back(std::move(table));
            }
        }

        if (const YAML::Node numbers = root["map_numbers"])
        {
            if (!numbers.IsSequence())
            {
                errorMessage = "'map_numbers' must be a list";
                return std::nullopt;
            }

            for (const YAML::Node &numberNode : numbers)
            {
                const int number = numberNode.IsScalar() ? numberNode.as<int>(0) : 0;

                if (number < 1 || std::find(manifest.mapNumbers.begin(), manifest.mapNumbers.end(),
                                      static_cast<uint32_t>(number)) != manifest.mapNumbers.end())
                {
                    errorMessage = "'map_numbers' must list different numbers from 1";
                    return std::nullopt;
                }

                manifest.mapNumbers.push_back(static_cast<uint32_t>(number));
            }
        }

        if (!parseContentIdRanges(root["idRanges"], "mod.yml", manifest.idRanges, errorMessage))
        {
            return std::nullopt;
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("mod.yml: ") + exception.what();
        return std::nullopt;
    }

    return manifest;
}

std::optional<std::vector<std::string>> parseEnabledModList(const std::string &yamlText, std::string &errorMessage)
{
    errorMessage.clear();
    std::vector<std::string> ids;

    try
    {
        const YAML::Node root = YAML::Load(yamlText);

        // An empty file enables nothing.
        if (!root || root.IsNull())
        {
            return ids;
        }

        if (!root.IsMap() || !root["format"] || root["format"].as<int>(0) != 1)
        {
            errorMessage = "enabled.yml needs format: 1";
            return std::nullopt;
        }

        const YAML::Node enabled = root["enabled"];

        if (enabled && !enabled.IsSequence() && !enabled.IsNull())
        {
            errorMessage = "enabled.yml's 'enabled' must be a list of mod ids";
            return std::nullopt;
        }

        for (const YAML::Node &idNode : enabled)
        {
            if (!idNode.IsScalar() || !isValidNamedModId(idNode.Scalar()))
            {
                errorMessage = "enabled.yml lists '" + (idNode.IsScalar() ? idNode.Scalar() : std::string("?"))
                    + "', which is no mod id";
                return std::nullopt;
            }

            if (std::find(ids.begin(), ids.end(), idNode.Scalar()) == ids.end())
            {
                ids.push_back(idNode.Scalar());
            }
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("enabled.yml: ") + exception.what();
        return std::nullopt;
    }

    return ids;
}

std::string formatEnabledModList(const std::vector<std::string> &ids)
{
    std::string text = "# The named mods that are on, in the order they mount: a later one in front "
                       "(devdocs/NAMED_MODS.md).\nformat: 1\nenabled: [";

    for (size_t index = 0; index < ids.size(); ++index)
    {
        text += (index == 0 ? "" : ", ") + ids[index];
    }

    return text + "]\n";
}

const NamedModEntry *NamedModCatalog::find(const std::string &id) const
{
    for (const NamedModEntry &entry : mods)
    {
        if (entry.id == id)
        {
            return &entry;
        }
    }

    return nullptr;
}

std::vector<NamedModManifest> NamedModCatalog::mountedManifests() const
{
    std::vector<NamedModManifest> manifests;

    for (const std::string &id : mountOrder)
    {
        const NamedModEntry *pEntry = find(id);

        if (pEntry != nullptr && pEntry->manifest)
        {
            manifests.push_back(*pEntry->manifest);
        }
    }

    return manifests;
}

NamedModCatalog readNamedModCatalog(const std::filesystem::path &modsRoot)
{
    NamedModCatalog catalog;
    catalog.modsRoot = modsRoot;
    std::error_code error;

    if (modsRoot.empty() || !std::filesystem::is_directory(modsRoot, error))
    {
        return catalog;
    }

    for (std::filesystem::directory_iterator entry(modsRoot, error), end; !error && entry != end;
         entry.increment(error))
    {
        std::error_code typeError;
        const std::filesystem::path manifestPath = entry->path() / NamedModManifestFileName;

        if (!entry->is_directory(typeError) || !std::filesystem::is_regular_file(manifestPath, typeError))
        {
            continue;
        }

        NamedModEntry mod;
        mod.id = pathText(entry->path().filename());
        const std::optional<std::string> text = readFileText(manifestPath);
        std::string manifestError = "mod.yml cannot be read";

        if (text)
        {
            mod.manifest = parseNamedModManifest(*text, mod.id, manifestError);
        }

        for (size_t index = 0; mod.manifest && index < mod.manifest->tables.size(); ++index)
        {
            NamedModTable &table = mod.manifest->tables[index];

            for (const auto &[pPath, pText] : {std::pair{&table.overridePath, &table.overrideText},
                     std::pair{&table.appendPath, &table.appendText}})
            {
                if (pPath->empty())
                {
                    continue;
                }

                const std::optional<std::string> rowsText = readFileText(entry->path() / *pPath);

                if (!rowsText)
                {
                    manifestError = "its table file " + *pPath + " cannot be read";
                    mod.manifest.reset();
                    break;
                }

                *pText = *rowsText;
            }
        }

        if (!mod.manifest)
        {
            mod.reason = manifestError;
        }

        catalog.mods.push_back(std::move(mod));
    }

    std::sort(catalog.mods.begin(), catalog.mods.end(),
        [](const NamedModEntry &left, const NamedModEntry &right) { return left.id < right.id; });

    const std::filesystem::path enabledPath = modsRoot / EnabledModListFileName;

    if (std::filesystem::is_regular_file(enabledPath, error))
    {
        const std::optional<std::string> text = readFileText(enabledPath);
        std::optional<std::vector<std::string>> ids = text ? parseEnabledModList(*text, catalog.enabledListError)
                                                           : std::nullopt;

        if (!text)
        {
            catalog.enabledListError = "enabled.yml cannot be read";
        }

        if (ids)
        {
            catalog.enabledIds = std::move(*ids);
        }
    }

    return catalog;
}

void resolveNamedMods(NamedModCatalog &catalog, const std::vector<NamedModRangeOwner> &owners)
{
    catalog.missingIds.clear();
    catalog.mountOrder.clear();
    std::vector<const NamedModManifest *> accepted;

    for (NamedModEntry &entry : catalog.mods)
    {
        entry.state = NamedModState::Off;

        if (entry.manifest)
        {
            entry.reason.clear();
        }
    }

    for (const std::string &id : catalog.enabledIds)
    {
        NamedModEntry *pEntry = findMutable(catalog, id);

        if (pEntry == nullptr)
        {
            catalog.missingIds.push_back(id);
            continue;
        }

        pEntry->state = NamedModState::Refused;

        if (!pEntry->manifest)
        {
            continue;
        }

        pEntry->reason = clashReason(*pEntry->manifest, owners, accepted);

        if (pEntry->reason.empty())
        {
            pEntry->state = NamedModState::On;
            catalog.mountOrder.push_back(id);
            accepted.push_back(&*pEntry->manifest);
        }
    }
}

void refuseNamedMod(NamedModCatalog &catalog, const std::string &id, const std::string &reason)
{
    if (NamedModEntry *pEntry = findMutable(catalog, id))
    {
        pEntry->state = NamedModState::Refused;
        pEntry->reason = reason;
    }

    std::erase(catalog.mountOrder, id);
}

bool applyNamedModTable(
    std::vector<std::vector<std::string>> &rows,
    const NamedModTable &table,
    std::string &errorMessage)
{
    std::vector<std::vector<std::string>> composed = rows;

    if (!table.overrideText.empty())
    {
        const std::optional<std::vector<std::vector<std::string>>> patchRows = tableRows(table.overrideText);

        if (!patchRows || !applyTableCellOverrides(composed, *patchRows, 0, 0, errorMessage))
        {
            errorMessage = table.overridePath + ": " + (patchRows ? errorMessage : "not a tab-separated table");
            return false;
        }
    }

    if (!table.appendText.empty())
    {
        const std::optional<std::vector<std::vector<std::string>>> appendRows = tableRows(table.appendText);

        if (!appendRows || !appendTableRows(composed, *appendRows, 0, 0, errorMessage))
        {
            errorMessage = table.appendPath + ": " + (appendRows ? errorMessage : "not a tab-separated table");
            return false;
        }
    }

    rows = std::move(composed);
    return true;
}

void applyNamedModTables(
    std::vector<std::vector<std::string>> &rows,
    const std::vector<NamedModManifest> &mods,
    const std::string &tableVirtualPath,
    std::vector<std::string> &errors)
{
    if (!tableVirtualPath.starts_with(EngineDataTableRoot))
    {
        return;
    }

    const std::string table = tableVirtualPath.substr(std::string(EngineDataTableRoot).size());

    for (const NamedModManifest &mod : mods)
    {
        for (const NamedModTable &modTable : mod.tables)
        {
            std::string error;

            if (modTable.table == table && !applyNamedModTable(rows, modTable, error))
            {
                errors.push_back(mod.id + ": " + error);
            }
        }
    }
}

bool mountNamedMods(Engine::AssetFileSystem &assetFileSystem, NamedModCatalog &catalog)
{
    catalog = readNamedModCatalog(assetFileSystem.installedContentOptions().modsRoot);

    if (!catalog.enabledListError.empty())
    {
        std::cerr << "Mods: " << pathText(catalog.modsRoot / EnabledModListFileName) << " is ignored, no named mod "
                  << "is on: " << catalog.enabledListError << '\n';
    }

    std::vector<NamedModRangeOwner> owners;

    if (!catalog.enabledIds.empty())
    {
        std::string error;

        if (!collectRangeOwners(assetFileSystem, owners, error))
        {
            // Without the worlds' ranges no mod can be checked: none mounts.
            std::cerr << "Mods: no named mod is on, the worlds' and rulesets' id ranges cannot be read: " << error
                      << '\n';
            catalog.enabledIds.clear();
        }
    }

    resolveNamedMods(catalog, owners);

    for (const std::string &id : catalog.missingIds)
    {
        std::cerr << "Mods: enabled.yml lists " << id << ", which is not installed\n";
    }

    for (const NamedModEntry &entry : catalog.mods)
    {
        if (entry.state == NamedModState::Refused)
        {
            std::cerr << "Mods: " << entry.id << " is refused: " << entry.reason << '\n';
        }
        else if (entry.state == NamedModState::Off)
        {
            std::cout << "Mods: " << entry.id << " is installed and off (not in enabled.yml)\n";
        }
    }

    // A refused mod's rows leave the tables and its files the mounts, so the others are checked again without it.
    while (true)
    {
        if (!assetFileSystem.setNamedMods(catalog.mountOrder))
        {
            std::cerr << "Mods: the named mods could not be mounted\n";
            return false;
        }

        const std::optional<std::pair<std::string, std::string>> failing =
            firstModWithFailingRows(assetFileSystem, catalog.mountedManifests());

        if (!failing)
        {
            break;
        }

        std::cerr << "Mods: " << failing->first << " is refused: its rows of " << failing->second << '\n';
        refuseNamedMod(catalog, failing->first, "its rows of " + failing->second);
    }

    for (const std::string &id : catalog.mountOrder)
    {
        const NamedModEntry *pEntry = catalog.find(id);
        std::cout << "Mods: " << id << " " << pEntry->manifest->version << " is on (" << pEntry->manifest->name
                  << ")\n";
    }

    return true;
}

bool setNamedModEnabled(
    const std::filesystem::path &modsRoot,
    const std::string &id,
    bool enabled,
    std::string &errorMessage)
{
    errorMessage.clear();
    const std::filesystem::path enabledPath = modsRoot / EnabledModListFileName;
    std::vector<std::string> ids;
    std::error_code error;

    if (std::filesystem::exists(enabledPath, error))
    {
        const std::optional<std::string> text = readFileText(enabledPath);
        std::optional<std::vector<std::string>> listed = text ? parseEnabledModList(*text, errorMessage)
                                                              : std::nullopt;

        if (!listed)
        {
            errorMessage = pathText(enabledPath) + " is not changed: "
                + (text ? errorMessage : std::string("it cannot be read"));
            return false;
        }

        ids = std::move(*listed);
    }

    const bool listed = std::find(ids.begin(), ids.end(), id) != ids.end();

    if (enabled)
    {
        if (!isValidNamedModId(id) || !std::filesystem::is_regular_file(modsRoot / id / NamedModManifestFileName, error))
        {
            errorMessage = "no mod " + id + " is installed in " + pathText(modsRoot);
            return false;
        }

        if (listed)
        {
            return true;
        }

        ids.push_back(id);
    }
    else
    {
        if (!listed)
        {
            return true;
        }

        std::erase(ids, id);
    }

    std::filesystem::create_directories(modsRoot, error);
    return writeTextAtomically(enabledPath, formatEnabledModList(ids), errorMessage);
}
}
