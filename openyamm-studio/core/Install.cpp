#include "core/IndoorBuild.h"
#include "core/Audit.h"
#include "core/GroundTerrain.h"
#include "core/Json.h"
#include "core/Ops.h"
#include "core/OutdoorBuild.h"

#include <algorithm>
#include <charconv>
#include <optional>
#include <set>
#include <sstream>

namespace OpenYAMM::Studio
{
namespace
{
YAML::Node childOf(const YAML::Node &node, const char *pKey)
{
    return node.IsDefined() && node.IsMap() ? node[pKey] : YAML::Node(YAML::NodeType::Undefined);
}

// A world that declares its own map ids (world.yml idRanges.maps, as Xeen does) owns its maps' table rows: its own
// generator writes them, and the game reads them through world.yml tableContributions (devdocs/xeen/lanes/TABLES.md).
bool worldOwnsMapRows(const std::filesystem::path &assetRoot, const std::string &world)
{
    std::string manifest;

    if (!readTextFile(assetRoot / "worlds" / world / "world.yml", manifest))
    {
        return false;
    }

    try
    {
        return childOf(childOf(YAML::Load(manifest), "idRanges"), "maps").IsMap();
    }
    catch (const YAML::Exception &)
    {
        return false;
    }
}

std::string lower(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return text;
}

// The file of a project's map: an ODM for an outdoor project, a BLV for an indoor one.
std::string mapExtension(const YAML::Node &card)
{
    const YAML::Node kind = childOf(card, "kind");
    return kind.IsDefined() && kind.IsScalar() && kind.Scalar() == "outdoor" ? ".odm" : ".blv";
}

std::vector<std::string> splitTabs(const std::string &line)
{
    std::vector<std::string> columns;
    size_t begin = 0;

    while (true)
    {
        const size_t tab = line.find('\t', begin);
        columns.push_back(line.substr(begin, tab == std::string::npos ? tab : tab - begin));

        if (tab == std::string::npos)
        {
            break;
        }

        begin = tab + 1;
    }

    return columns;
}

std::string joinTabs(const std::vector<std::string> &columns)
{
    std::string line;

    for (size_t index = 0; index < columns.size(); ++index)
    {
        line += index == 0 ? "" : "\t";
        line += columns[index];
    }

    return line;
}

// map_stats.txt columns (game/tables/MapStats.cpp).
constexpr size_t ColumnId = 0;
constexpr size_t ColumnName = 1;
constexpr size_t ColumnFile = 2;
constexpr size_t ColumnPerception = 5;
constexpr size_t ColumnRefillDays = 6;
constexpr size_t ColumnDisarm = 9;
constexpr size_t ColumnTrapDice = 10;
constexpr size_t ColumnTreasure = 11;
constexpr size_t ColumnEncounterChance = 12;
constexpr size_t ColumnDesigner = 30;
constexpr size_t ColumnWorld = 34;
constexpr size_t ColumnCount = 35;

bool upsertMapStatsRow(
    const Project &project,
    const std::filesystem::path &tablePath,
    std::string &errorMessage)
{
    const YAML::Node card = project.document("project.yml");
    const YAML::Node stats = childOf(card, "map_stats");
    const YAML::Node idNode = childOf(stats, "id");
    const YAML::Node referenceNode = childOf(stats, "reference");

    const YAML::Node slotsNode = childOf(stats, "slots");

    if (!idNode.IsDefined() || (!referenceNode.IsDefined() && !slotsNode.IsDefined()))
    {
        errorMessage = "project.yml map_stats needs `id`, and either `reference` (a shipped map whose row is the "
            "template) or `slots` (the encounter slots in full), to install the map";
        return false;
    }

    std::string text;

    if (!readTextFile(tablePath, text))
    {
        errorMessage = "could not read " + tablePath.string();
        return false;
    }

    const std::string lineEnding = text.find("\r\n") != std::string::npos ? "\r\n" : "\n";
    std::vector<std::string> lines;
    size_t begin = 0;

    while (begin <= text.size())
    {
        const size_t end = text.find('\n', begin);
        std::string line = text.substr(begin, end == std::string::npos ? end : end - begin);

        if (!line.empty() && line.back() == '\r')
        {
            line.pop_back();
        }

        lines.push_back(line);

        if (end == std::string::npos)
        {
            break;
        }

        begin = end + 1;
    }

    const bool endsWithNewline = !lines.empty() && lines.back().empty();

    if (endsWithNewline)
    {
        lines.pop_back();
    }

    const std::string mapFile = lower(card["id"].Scalar()) + mapExtension(card);
    const std::string id = idNode.Scalar();
    const std::string reference = referenceNode.IsDefined() ? lower(referenceNode.Scalar()) : std::string();
    std::vector<std::string> row;
    std::optional<size_t> existing;

    for (size_t index = 0; index < lines.size(); ++index)
    {
        const std::vector<std::string> columns = splitTabs(lines[index]);

        if (columns.size() <= ColumnFile)
        {
            continue;
        }

        // Without a reference nothing is the template: an empty name would otherwise match the table's heading
        // rows, whose file column is empty, and copy their words ("Steal") into the map's numbers.
        if (!reference.empty() && lower(columns[ColumnFile]) == reference)
        {
            row = columns;
        }

        if (lower(columns[ColumnFile]) == mapFile)
        {
            existing = index;
        }
        else if (columns[ColumnId] == id)
        {
            errorMessage = "map_stats id " + id + " already belongs to " + columns[ColumnFile];
            return false;
        }
    }

    if (row.empty() && referenceNode.IsDefined())
    {
        errorMessage = "map_stats.txt has no row for the reference map " + referenceNode.Scalar();
        return false;
    }

    if (row.empty())
    {
        // No reference: a plain row, every number zero, refilled every 672 days, one trap die.
        row.assign(ColumnCount, "0");
        row[ColumnRefillDays] = "672";
        row[ColumnTrapDice] = "1";
        row[33] = "-";
    }

    row.resize(std::max(row.size(), ColumnCount));
    row[ColumnId] = id;
    row[ColumnName] = childOf(card, "name").IsDefined() ? card["name"].Scalar() : card["id"].Scalar();
    row[ColumnFile] = mapFile;
    row[ColumnDesigner] = "map_studio";
    row[ColumnWorld] = card["world"].Scalar();
    const auto overrideColumn = [&stats, &row](const char *pKey, size_t column)
    {
        const YAML::Node value = childOf(stats, pKey);

        if (value.IsDefined() && value.IsScalar())
        {
            row[column] = value.Scalar();
        }
    };
    overrideColumn("perception_difficulty", ColumnPerception);
    overrideColumn("refill_days", ColumnRefillDays);
    overrideColumn("disarm_difficulty", ColumnDisarm);
    overrideColumn("trap_dice", ColumnTrapDice);
    overrideColumn("treasure_level", ColumnTreasure);
    overrideColumn("lock_difficulty", ColumnDisarm);
    overrideColumn("encounter_chance", ColumnEncounterChance);
    overrideColumn("steal_fine", 8);
    overrideColumn("music", 28);
    overrideColumn("environment", 29);

    // Encounter slots in full: chance (columns 13 to 15), then picture, name, difficulty and count per slot.
    if (slotsNode.IsDefined() && slotsNode.IsSequence())
    {
        size_t slot = 0;

        for (const YAML::Node &slotNode : slotsNode)
        {
            if (slot >= 3)
            {
                break;
            }

            const size_t base = 16 + slot * 4;
            const YAML::Node monster = childOf(slotNode, "monster");
            const YAML::Node tier = childOf(slotNode, "tier");
            const YAML::Node perMarker = childOf(slotNode, "per_marker");
            const YAML::Node weight = childOf(slotNode, "weight");

            if (monster.IsDefined())
            {
                row[base] = monster.Scalar();
                row[base + 1] = monster.Scalar();
            }

            if (tier.IsDefined())
            {
                row[base + 2] = tier.Scalar();
            }

            if (perMarker.IsDefined() && perMarker.IsSequence() && perMarker.size() == 2)
            {
                // The table writes counts as " low-high".
                row[base + 3] = " " + perMarker[0].Scalar() + "-" + perMarker[1].Scalar();
            }

            if (weight.IsDefined())
            {
                row[13 + slot] = weight.Scalar();
            }

            ++slot;
        }
    }

    if (existing)
    {
        lines[*existing] = joinTabs(row);
    }
    else
    {
        lines.push_back(joinTabs(row));
    }

    std::string updated;

    for (size_t index = 0; index < lines.size(); ++index)
    {
        updated += lines[index];

        if (index + 1 < lines.size() || endsWithNewline)
        {
            updated += lineEnding;
        }
    }

    return writeTextFileAtomically(tablePath, updated, errorMessage);
}

bool copyFileAtomically(
    const std::filesystem::path &source,
    const std::filesystem::path &target,
    std::string &errorMessage)
{
    std::string bytes;

    if (!readTextFile(source, bytes))
    {
        errorMessage = "could not read " + source.string() + " (build the project first)";
        return false;
    }

    return writeTextFileAtomically(target, bytes, errorMessage);
}

// <stem>.studio.yml beside an installed map (S5_BROWSER_EDITOR.md 2.10): the project the map was built from, its
// source revision and lock hash, as the build recorded them in build.json (from the project as it is now for a
// build made before builds recorded them). The game's `pin` copies the three into every pin made on the map, and
// `oymap pins import` files the pin into that project.
bool writeStudioMapFile(
    const Project &project,
    const std::filesystem::path &buildDirectory,
    const std::filesystem::path &target,
    std::string &errorMessage)
{
    std::string revision;
    std::string lockHash;
    std::string buildJson;
    // The map's named arrivals (D-4), which doors and exits of other maps name.
    std::string arrivals;

    if (readTextFile(buildDirectory / "build.json", buildJson))
    {
        try
        {
            const YAML::Node built = YAML::Load(buildJson);
            revision = built["source_revision"] ? built["source_revision"].Scalar() : std::string();
            lockHash = built["lock_hash"] ? built["lock_hash"].Scalar() : std::string();
            const YAML::Node named = built["named_arrivals"];

            for (const YAML::Node &arrival : named && named.IsSequence() ? named : YAML::Node())
            {
                const YAML::Node at = arrival["at"];

                if (arrival["name"] && at && at.IsSequence() && at.size() == 3)
                {
                    arrivals += "  - {name: " + jsonQuote(arrival["name"].Scalar()) + ", at: ["
                        + std::to_string(at[0].as<int>(0)) + ", " + std::to_string(at[1].as<int>(0)) + ", "
                        + std::to_string(at[2].as<int>(0)) + "], facing: "
                        + std::to_string(arrival["facing"] ? arrival["facing"].as<int>(0) : 0) + "}\n";
                }
            }
        }
        catch (const YAML::Exception &)
        {
        }
    }

    if (revision.empty())
    {
        revision = projectRevision(project);
        lockHash = projectLockHash(project.root);
    }

    std::error_code error;
    std::filesystem::path projectPath = std::filesystem::weakly_canonical(std::filesystem::absolute(project.root), error);

    if (error)
    {
        projectPath = std::filesystem::absolute(project.root);
    }

    std::string text = "# Written by oymap install: the Map Studio project this map was built from. The game's `pin`"
        " copies it into\n# every pin made on the map; `oymap pins import` files the pin into that project.\n"
        "project: " + jsonQuote(projectPath.generic_string()) + "\n"
        "revision: " + jsonQuote(revision) + "\n"
        "lock_hash: " + jsonQuote(lockHash) + "\n";

    if (!arrivals.empty())
    {
        text += "# Where a party arrives (`into: {map, arrival}` and a neighbour's `arrival: <name>` of other maps).\n"
            "arrivals:\n" + arrivals;
    }

    // What the project says of the map that the map cannot (the audit of the installed map reads it back): the
    // decorations that hang, the storerooms and the trapdoors, by the numbers of the lock the build wrote.
    Project built;
    std::vector<ProjectIssue> unused;

    if (loadProject(project.root, built, unused))
    {
        const DressingFacts facts = projectDressingFacts(built);

        // What the map is (D-89), for the audit's cave-shape check of the installed map.
        if (!facts.identityShape.empty())
        {
            text += "identity: {shape: " + jsonQuote(facts.identityShape) + "}\n";
        }

        // D-91: the cave mouths that lead nowhere, for the audit's `caves.blind_mouth`.
        if (!facts.blindMouths.empty())
        {
            text += "blind_mouths: [";

            for (const std::string &id : facts.blindMouths)
            {
                text += (text.back() == '[' ? "" : ", ") + jsonQuote(id);
            }

            text += "]\n";
        }

        for (const std::pair<const char *, const std::set<int> *> list :
            {std::pair<const char *, const std::set<int> *>{"hanging_decorations", &facts.hanging},
                std::pair<const char *, const std::set<int> *>{"storerooms", &facts.storerooms},
                std::pair<const char *, const std::set<int> *>{"trap_doors", &facts.traps}})
        {
            if (!list.second->empty())
            {
                text += std::string(list.first) + ": [";

                for (const int number : *list.second)
                {
                    text += (text.back() == '[' ? "" : ", ") + std::to_string(number);
                }

                text += "]\n";
            }
        }
    }

    return writeTextFileAtomically(target, text, errorMessage);
}
}

bool installBuild(
    const Project &project,
    const std::filesystem::path &buildDirectory,
    const std::filesystem::path &assetRoot,
    std::vector<std::string> &installedFiles,
    std::string &errorMessage,
    bool statsOptional,
    const std::filesystem::path *pManifestRoot)
{
    const YAML::Node card = project.document("project.yml");
    const std::string stem = card["id"].Scalar();
    const std::string world = card["world"].Scalar();
    std::error_code error;

    if (!std::filesystem::is_directory(assetRoot / "engine" / "data_tables", error)
        || !std::filesystem::is_directory(assetRoot / "worlds" / world, error))
    {
        errorMessage = assetRoot.string() + " is not an asset root with engine/data_tables and worlds/" + world;
        return false;
    }

    // A world that owns its maps' table rows takes only the map's files, all in its own folder, so its maps install
    // into the development root too; they write no table row, sky theme or travel row (the world's generator does).
    const bool ownRows = worldOwnsMapRows(pManifestRoot != nullptr ? *pManifestRoot : assetRoot, world);

    // S0 installs into scratch roots only (a hard-link copy of assets_dev, as the MM9 scratch builds use); the
    // development assets get new maps once the game can mount a build folder (PLAN.md section 10b).
    if (!ownRows && std::filesystem::weakly_canonical(assetRoot, error).filename() == "assets_dev")
    {
        errorMessage = "refusing to install into assets_dev: install into a scratch asset root (cp -al assets_dev "
            "output/<name>_root)";
        return false;
    }

    const std::filesystem::path baseMap(childOf(card, "base").IsDefined() ? card["base"].Scalar() : std::string());

    // An overlay project installs its overlays beside the base map (its script, scene and cinematics overlays).
    if (!baseMap.empty())
    {
        const std::string overlayName = baseMap.stem().string() + "_" + stem + ".lua";

        const std::string sceneName = baseMap.stem().string() + "_" + stem + ".scene.yml";
        const std::string cinematicsName = baseMap.stem().string() + "_" + stem + ".cinematics.yml";
        const std::string studioName = baseMap.stem().string() + ".studio.yml";
        std::error_code missing;
        installedFiles.clear();

        // The script, the scene overlay and the cinematics overlay the build made (S6, S8a: an overlay may change
        // only the scene, only handlers or only cinematics); one the build no longer makes leaves the root, so an old
        // overlay does not stay applied.
        for (const std::pair<std::string, std::filesystem::path> &file : {
                 std::pair<std::string, std::filesystem::path>{overlayName,
                     assetRoot / "worlds" / world / "events" / "maps" / overlayName},
                 {sceneName, assetRoot / "worlds" / world / "maps" / sceneName},
                 {cinematicsName, assetRoot / "worlds" / world / "maps" / cinematicsName}})
        {
            if (std::filesystem::exists(buildDirectory / file.first, missing))
            {
                if (!copyFileAtomically(buildDirectory / file.first, file.second, errorMessage))
                {
                    return false;
                }

                installedFiles.push_back(file.second.lexically_relative(assetRoot).generic_string());
            }
            else
            {
                std::filesystem::remove(file.second, missing);
            }
        }

        if (installedFiles.empty())
        {
            errorMessage = "the build folder holds no overlay of " + baseMap.string() + ": build the project first";
            return false;
        }

        if (!writeStudioMapFile(project, buildDirectory, assetRoot / "worlds" / world / "maps" / studioName,
                errorMessage))
        {
            return false;
        }

        installedFiles.push_back("worlds/" + world + "/maps/" + studioName);
        return true;
    }

    const std::filesystem::path maps = assetRoot / "worlds" / world / "maps";
    const std::filesystem::path events = assetRoot / "worlds" / world / "events" / "maps";

    const std::string mapFile = stem + mapExtension(card);
    // A card without `map_stats` at all is as good as one without its `id` (asking a missing node for a key throws).
    const YAML::Node stats = childOf(card, "map_stats");
    const bool hasStatsId = stats.IsDefined() && stats.IsMap() && stats["id"].IsDefined();

    if (!copyFileAtomically(buildDirectory / mapFile, maps / mapFile, errorMessage)
        || !copyFileAtomically(buildDirectory / (stem + ".scene.yml"), maps / (stem + ".scene.yml"), errorMessage)
        || !copyFileAtomically(buildDirectory / (stem + ".lua"), events / (stem + ".lua"), errorMessage)
        || !writeStudioMapFile(project, buildDirectory, maps / (stem + ".studio.yml"), errorMessage)
        || (!ownRows && !(statsOptional && !hasStatsId)
            && !upsertMapStatsRow(project, assetRoot / "engine" / "data_tables" / "map_stats.txt", errorMessage)))
    {
        return false;
    }

    // The map's cinematics, when the build made them; an old file goes when the project has none any more.
    std::error_code cinematicsError;

    if (std::filesystem::exists(buildDirectory / (stem + ".cinematics.yml"), cinematicsError))
    {
        if (!copyFileAtomically(buildDirectory / (stem + ".cinematics.yml"), maps / (stem + ".cinematics.yml"),
                errorMessage))
        {
            return false;
        }
    }
    else
    {
        std::filesystem::remove(maps / (stem + ".cinematics.yml"), cinematicsError);
    }

    installedFiles = {
        "worlds/" + world + "/maps/" + mapFile,
        "worlds/" + world + "/maps/" + stem + ".scene.yml",
        "worlds/" + world + "/events/maps/" + stem + ".lua",
        "worlds/" + world + "/maps/" + stem + ".studio.yml"};

    // An open-air map's ground (atmosphere.yml `ground`): its material file and weights (core/GroundTerrain.h).
    if (!installGroundFiles(buildDirectory, assetRoot, world, stem, installedFiles, errorMessage))
    {
        return false;
    }

    if (ownRows)
    {
        return true;
    }

    installedFiles.push_back("engine/data_tables/map_stats.txt");

    // An outdoor map's ways to its neighbours across its sides: its row of the travel table (core/OutdoorInstall).
    const std::filesystem::path travels = assetRoot / "engine" / "data_tables" / "outdoor_travels.txt";
    std::vector<std::string> travelChanges;

    if (!outdoorTravelEdges(project).empty() && std::filesystem::exists(travels))
    {
        if (!upsertOutdoorTravelRows(project, travels, travelChanges, errorMessage))
        {
            return false;
        }

        installedFiles.push_back("engine/data_tables/outdoor_travels.txt");
    }

    // An outdoor map's continent (its skies and colours) and weather, and a map's bolster kind (an indoor map's row
    // only when map_stats.bolster asks for it): its row of bolster_maps.txt (core/OutdoorInstall).
    const std::filesystem::path tables = assetRoot / "engine" / "data_tables";
    std::vector<std::string> weatherChanges;

    if (outdoorWeatherRow(project).written && std::filesystem::exists(tables / "bolster_maps.txt"))
    {
        if (!upsertOutdoorWeatherRow(project, tables, weatherChanges, errorMessage))
        {
            return false;
        }

        installedFiles.push_back("engine/data_tables/bolster_maps.txt");
    }

    // An outdoor map's sky theme: its row of the enhanced sky's `maps` (core/OutdoorInstall).
    const std::filesystem::path skyFile = assetRoot / "engine" / "rendering" / "sky" / "sky.yml";
    std::vector<std::string> skyChanges;

    if (!outdoorSkyTheme(project).empty())
    {
        if (!upsertOutdoorSkyTheme(project, skyFile, skyChanges, errorMessage))
        {
            return false;
        }

        installedFiles.push_back("engine/rendering/sky/sky.yml");
    }

    return true;
}

namespace
{
// The key of a table row: its first column, lower case; empty for the heading rows (no first column, or "#").
std::string tableRowKey(const std::string &line)
{
    const size_t tab = line.find('\t');
    std::string key = lower(line.substr(0, tab));

    while (!key.empty() && (key.back() == '\r' || key.back() == ' '))
    {
        key.pop_back();
    }

    return key.empty() || key[0] == '#' ? std::string() : key;
}

// A mount's copy of one of the root's tables (map_stats.txt, outdoor_travels.txt, bolster_maps.txt) before an install
// writes its rows into it (S8g). A mount without the table gets the root's. A mount that has it keeps it, with the
// rows earlier installs into the mount wrote (X1's travel row stays when X2 is installed after it), and gains the
// root's rows it lacks (a map installed into the root since). A row the root changed since the mount took its copy
// is not taken: remove the mount's table to start afresh.
bool prepareMountTable(
    const std::filesystem::path &rootTable,
    const std::filesystem::path &mountTable,
    std::string &errorMessage)
{
    std::error_code error;

    if (!std::filesystem::exists(mountTable, error))
    {
        std::filesystem::copy_file(rootTable, mountTable, std::filesystem::copy_options::overwrite_existing, error);

        if (error)
        {
            errorMessage = "could not copy " + rootTable.string() + " to " + mountTable.string() + ": "
                + error.message();
            return false;
        }

        return true;
    }

    std::string mountText;
    std::string rootText;

    if (!readTextFile(mountTable, mountText) || !readTextFile(rootTable, rootText))
    {
        errorMessage = "could not read " + mountTable.string() + " or " + rootTable.string();
        return false;
    }

    const auto linesOf = [](const std::string &text)
    {
        std::vector<std::string> lines;
        size_t begin = 0;

        while (begin < text.size())
        {
            const size_t end = text.find('\n', begin);
            lines.push_back(text.substr(begin, end == std::string::npos ? end : end - begin));

            if (end == std::string::npos)
            {
                break;
            }

            begin = end + 1;
        }

        return lines;
    };

    std::vector<std::string> lines = linesOf(mountText);
    std::set<std::string> keys;

    for (const std::string &line : lines)
    {
        keys.insert(tableRowKey(line));
    }

    std::vector<std::string> added;

    for (const std::string &line : linesOf(rootText))
    {
        const std::string key = tableRowKey(line);

        if (!key.empty() && keys.insert(key).second)
        {
            added.push_back(line);
        }
    }

    if (added.empty())
    {
        return true;
    }

    // The rows go after the last row with something in it, before the table's blank tail.
    size_t at = lines.size();

    while (at > 0 && (lines[at - 1].empty() || lines[at - 1] == "\r"
            || lines[at - 1].find_first_not_of("\t\r") == std::string::npos))
    {
        --at;
    }

    const std::string lineEnding = mountText.find("\r\n") != std::string::npos ? "\r" : "";

    for (std::string &line : added)
    {
        if (!line.empty() && line.back() == '\r')
        {
            line.pop_back();
        }

        line += lineEnding;
    }

    lines.insert(lines.begin() + static_cast<std::ptrdiff_t>(at), added.begin(), added.end());
    std::string written;

    for (size_t index = 0; index < lines.size(); ++index)
    {
        written += lines[index];

        if (index + 1 < lines.size() || (!mountText.empty() && mountText.back() == '\n'))
        {
            written += "\n";
        }
    }

    return writeTextFileAtomically(mountTable, written, errorMessage);
}

// The same for the enhanced sky's file: the root's sky.yml with the map themes the mount's copy holds.
bool prepareMountSkyFile(
    const std::filesystem::path &rootFile,
    const std::filesystem::path &mountFile,
    std::string &errorMessage)
{
    std::string rootText;
    std::string mountText;

    if (!readTextFile(rootFile, rootText))
    {
        errorMessage = "could not read " + rootFile.string();
        return false;
    }

    std::error_code error;

    if (std::filesystem::exists(mountFile, error) && readTextFile(mountFile, mountText))
    {
        std::istringstream lines(mountText);
        std::string line;
        bool inside = false;

        while (std::getline(lines, line))
        {
            if (!line.empty() && line[0] != ' ' && line[0] != '#')
            {
                inside = line.rfind("maps:", 0) == 0;
                continue;
            }

            const size_t colon = line.find(':');

            if (inside && line.rfind("  ", 0) == 0 && line.size() > 2 && line[2] != ' ' && line[2] != '#'
                && colon != std::string::npos && rootText.find(line + "\n") == std::string::npos)
            {
                std::string theme = line.substr(colon + 1);
                theme.erase(0, theme.find_first_not_of(' '));
                rootText = withSkyTheme(rootText, line.substr(2, colon - 2), theme);
            }
        }
    }

    return writeTextFileAtomically(mountFile, rootText, errorMessage);
}
}

bool installBuildIntoMount(
    const Project &project,
    const std::filesystem::path &buildDirectory,
    const std::filesystem::path &mountRoot,
    const std::filesystem::path &assetRoot,
    std::vector<std::string> &installedFiles,
    std::string &errorMessage,
    bool statsOptional)
{
    // A mount's tables start from its own copy when it has one (prepareMountTable): several maps installed into one
    // mount keep each other's rows.
    const YAML::Node card = project.document("project.yml");
    const std::string world = card["world"].Scalar();
    const std::filesystem::path tables = mountRoot / "engine" / "data_tables";
    const std::filesystem::path rootTables = assetRoot / "engine" / "data_tables";
    std::error_code error;
    std::filesystem::create_directories(tables, error);
    std::filesystem::create_directories(mountRoot / "worlds" / world / "maps", error);
    std::filesystem::create_directories(mountRoot / "worlds" / world / "events" / "maps", error);

    if (error)
    {
        errorMessage = "could not prepare " + mountRoot.string() + ": " + error.message();
        return false;
    }

    // A world that owns its maps' rows (Xeen) gets none in the mount: the root's world tables have them, and an engine
    // copy would collide with them.
    const bool ownRows = worldOwnsMapRows(assetRoot, world);

    if (!ownRows && !card["base"].IsDefined()
        && !prepareMountTable(rootTables / "map_stats.txt", tables / "map_stats.txt", errorMessage))
    {
        return false;
    }

    // The same for the travel table of an outdoor map that leads to neighbours across its sides.
    if (!ownRows && !outdoorTravelEdges(project).empty()
        && !prepareMountTable(rootTables / "outdoor_travels.txt", tables / "outdoor_travels.txt", errorMessage))
    {
        return false;
    }

    // And for the table with a map's continent, weather and bolster kind.
    if (!ownRows && outdoorWeatherRow(project).written
        && std::filesystem::exists(rootTables / "bolster_maps.txt", error)
        && !prepareMountTable(rootTables / "bolster_maps.txt", tables / "bolster_maps.txt", errorMessage))
    {
        return false;
    }

    // And for the enhanced sky's file, where an outdoor map's sky theme is keyed by its name.
    if (!card["base"].IsDefined() && !outdoorSkyTheme(project).empty())
    {
        std::filesystem::create_directories(mountRoot / "engine" / "rendering" / "sky", error);

        if (!prepareMountSkyFile(assetRoot / "engine" / "rendering" / "sky" / "sky.yml",
                mountRoot / "engine" / "rendering" / "sky" / "sky.yml", errorMessage))
        {
            return false;
        }
    }

    return installBuild(project, buildDirectory, mountRoot, installedFiles, errorMessage, statsOptional, &assetRoot);
}
}
