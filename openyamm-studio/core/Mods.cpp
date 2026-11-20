#include "core/Mods.h"

#include "core/CanonicalYaml.h"
#include "core/IndoorBuild.h"
#include "core/Project.h"
#include "core/Schema.h"
#include "core/SketchRead.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <optional>
#include <map>
#include <set>
#include <sstream>

namespace OpenYAMM::Studio
{
namespace
{
const char *RegistryName = "studio_mods.yml";
const char *CopiesName = "studio_mods";

struct TableText
{
    std::vector<std::string> lines;
    std::string newline = "\n";
    bool finalNewline = true;
};

TableText splitTable(const std::string &text)
{
    TableText table;
    table.newline = text.find("\r\n") != std::string::npos ? "\r\n" : "\n";
    table.finalNewline = !text.empty() && text.back() == '\n';
    std::string line;
    std::istringstream stream(text);

    while (std::getline(stream, line))
    {
        if (!line.empty() && line.back() == '\r')
        {
            line.pop_back();
        }

        table.lines.push_back(line);
    }

    return table;
}

std::string joinTable(const TableText &table)
{
    std::string text;

    for (size_t index = 0; index < table.lines.size(); ++index)
    {
        text += table.lines[index];

        if (index + 1 < table.lines.size() || table.finalNewline)
        {
            text += table.newline;
        }
    }

    return text;
}

std::vector<std::string> cellsOf(const std::string &line)
{
    std::vector<std::string> cells;
    size_t begin = 0;

    while (true)
    {
        const size_t tab = line.find('\t', begin);
        cells.push_back(line.substr(begin, tab == std::string::npos ? std::string::npos : tab - begin));

        if (tab == std::string::npos)
        {
            return cells;
        }

        begin = tab + 1;
    }
}

std::string keyOf(const std::string &line)
{
    std::string key = cellsOf(line).front();
    const size_t first = key.find_first_not_of(" \"");
    const size_t last = key.find_last_not_of(" \"");
    return first == std::string::npos ? std::string() : key.substr(first, last - first + 1);
}

std::string joinCells(const std::vector<std::string> &cells)
{
    std::string line;

    for (size_t index = 0; index < cells.size(); ++index)
    {
        line += (index == 0 ? "" : "\t") + cells[index];
    }

    return line;
}

bool readText(const std::filesystem::path &path, std::string &text)
{
    return readTextFile(path, text);
}

bool copyTree(const std::filesystem::path &from, const std::filesystem::path &to, std::vector<std::string> &files,
    const std::filesystem::path &relativeTo, std::string &errorMessage)
{
    std::error_code error;

    if (!std::filesystem::is_directory(from, error))
    {
        return true;
    }

    std::vector<std::filesystem::path> sources;

    for (std::filesystem::recursive_directory_iterator entry(from, error), end; !error && entry != end;
         entry.increment(error))
    {
        if (entry->is_regular_file())
        {
            sources.push_back(entry->path());
        }
    }

    std::sort(sources.begin(), sources.end());

    for (const std::filesystem::path &source : sources)
    {
        const std::filesystem::path target = to / source.lexically_relative(from);
        std::filesystem::create_directories(target.parent_path(), error);
        std::filesystem::copy_file(source, target, std::filesystem::copy_options::overwrite_existing, error);

        if (error)
        {
            errorMessage = "could not copy " + source.generic_string() + ": " + error.message();
            return false;
        }

        files.push_back(target.lexically_relative(relativeTo).generic_string());
    }

    return true;
}

YAML::Node readYaml(const std::filesystem::path &path)
{
    std::string text;

    if (!readText(path, text))
    {
        return YAML::Node();
    }

    try
    {
        return YAML::Load(text);
    }
    catch (const std::exception &)
    {
        return YAML::Node();
    }
}

bool writeYaml(const std::filesystem::path &path, const YAML::Node &node, const char *pSchema,
    std::string &errorMessage)
{
    const std::string text = pSchema != nullptr ? writeCanonicalYaml(node, SchemaSet::builtIn(), pSchema)
                                                : writeCanonicalYaml(node);
    return writeTextFileAtomically(path, text, errorMessage);
}

// The registry of merged installs: the mods in installation order, each with its files and whether it is on.
struct Registry
{
    YAML::Node document;

    static Registry load(const std::filesystem::path &modsRoot)
    {
        Registry registry;
        registry.document = readYaml(modsRoot / RegistryName);

        if (!registry.document.IsDefined() || !registry.document.IsMap())
        {
            registry.document = YAML::Node(YAML::NodeType::Map);
            registry.document["format"] = 1;
            registry.document["mods"] = YAML::Node(YAML::NodeType::Sequence);
        }

        return registry;
    }
};

// Composes every table the enabled merged mods change, from the asset root's own and each mod's rows in order.
bool composeTables(const std::filesystem::path &modsRoot, const std::filesystem::path &assetRoot,
    const std::set<std::string> &tables, const Registry &registry, ModInstallResult &result,
    std::string &errorMessage)
{
    for (const std::string &table : tables)
    {
        std::string text;

        // A development root's table (a player's install keeps it in its packages, which the native core does not
        // open yet: S6_PLAN.md, what remains).
        if (!readText(assetRoot / "engine" / "data_tables" / table, text))
        {
            errorMessage = "the asset root has no engine/data_tables/" + table + " (a development root is needed)";
            return false;
        }

        bool changed = false;

        for (const YAML::Node &mod : registry.document["mods"])
        {
            if (mod["enabled"] && mod["enabled"].Scalar() == "false")
            {
                continue;
            }

            const std::filesystem::path copy = modsRoot / CopiesName / mod["id"].Scalar();
            const YAML::Node manifest = readYaml(copy / "mod.yml");

            for (const YAML::Node &entry : childOf(manifest, "tables"))
            {
                if (textOf(entry, "table", "") != table)
                {
                    continue;
                }

                std::string overrideText;
                std::string appendText;

                if (entry["override"])
                {
                    readText(copy / entry["override"].Scalar(), overrideText);
                }

                if (entry["append"])
                {
                    readText(copy / entry["append"].Scalar(), appendText);
                }

                text = applyTableRows(text, overrideText, appendText);
                changed = true;
            }
        }

        const std::filesystem::path target = modsRoot / "engine" / "data_tables" / table;
        std::error_code error;

        if (changed)
        {
            std::filesystem::create_directories(target.parent_path(), error);

            if (!writeTextFileAtomically(target, text, errorMessage))
            {
                return false;
            }

            result.tables.push_back("engine/data_tables/" + table);
        }
        else
        {
            std::filesystem::remove(target, error);
        }
    }

    return true;
}

std::set<std::string> tablesOfMods(const std::filesystem::path &modsRoot, const Registry &registry)
{
    std::set<std::string> tables;

    for (const YAML::Node &mod : registry.document["mods"])
    {
        for (const YAML::Node &entry : childOf(readYaml(modsRoot / CopiesName / mod["id"].Scalar() / "mod.yml"),
                 "tables"))
        {
            tables.insert(textOf(entry, "table", ""));
        }
    }

    return tables;
}
}

namespace
{
// A manifest's `idRanges.maps` (world.yml and mod.yml share the form: {begin, end}).
std::optional<std::array<int, 2>> mapRangeOf(const YAML::Node &manifest)
{
    const YAML::Node maps = childOf(childOf(manifest, "idRanges"), "maps");

    if (!maps.IsDefined() || !childOf(maps, "begin").IsDefined() || !childOf(maps, "end").IsDefined())
    {
        return std::nullopt;
    }

    try
    {
        return std::array<int, 2>{maps["begin"].as<int>(), maps["end"].as<int>()};
    }
    catch (const YAML::Exception &)
    {
        return std::nullopt;
    }
}

// The mod's numbers and range as members of its list entry.
void writeModNumbers(JsonWriter &writer, const YAML::Node &manifest)
{
    writer.key("map_numbers");
    writer.beginArray();

    for (const YAML::Node &number : childOf(manifest, "map_numbers"))
    {
        writer.value(number.as<int>());
    }

    writer.endArray();

    if (const std::optional<std::array<int, 2>> range = mapRangeOf(manifest))
    {
        writer.key("map_range");
        writer.beginArray();
        writer.value((*range)[0]);
        writer.value((*range)[1]);
        writer.endArray();
    }
}

// Every mod manifest a mods folder holds: its merged installs' copies, its named installs and packed mods.
std::vector<YAML::Node> manifestsIn(const std::filesystem::path &modsRoot)
{
    std::vector<YAML::Node> manifests;
    std::error_code error;

    if (modsRoot.empty() || !std::filesystem::is_directory(modsRoot, error))
    {
        return manifests;
    }

    for (const std::filesystem::path &folder : {modsRoot, modsRoot / CopiesName})
    {
        std::vector<std::filesystem::path> found;

        for (std::filesystem::directory_iterator entry(folder, error), end; !error && entry != end;
             entry.increment(error))
        {
            if (entry->is_directory() && std::filesystem::exists(entry->path() / "mod.yml"))
            {
                found.push_back(entry->path());
            }
        }

        std::sort(found.begin(), found.end());

        for (const std::filesystem::path &path : found)
        {
            const YAML::Node manifest = readYaml(path / "mod.yml");

            if (manifest.IsDefined() && manifest.IsMap())
            {
                manifests.push_back(manifest);
            }
        }
    }

    return manifests;
}

// The map numbers of a map_stats table's rows (the first cell of each row that is a number).
void tableNumbers(const std::string &text, std::set<int> &numbers)
{
    for (const std::string &line : splitTable(text).lines)
    {
        const std::string key = keyOf(line);

        if (!key.empty() && key.size() < 9 && key.find_first_not_of("0123456789") == std::string::npos)
        {
            numbers.insert(std::stoi(key));
        }
    }
}
}

bool proposeMapNumber(const MapNumberRequest &request, MapNumberProposal &proposal, std::string &errorMessage)
{
    const std::vector<YAML::Node> manifests = manifestsIn(request.modsRoot);
    const YAML::Node world = request.world.empty() ? YAML::Node()
        : readYaml(request.assetRoot / "worlds" / request.world / "world.yml");
    const std::optional<std::array<int, 2>> worldRange = mapRangeOf(world);

    if (!request.mod.empty())
    {
        const std::vector<YAML::Node>::const_iterator mod = std::find_if(manifests.begin(), manifests.end(),
            [&request](const YAML::Node &manifest) { return textOf(manifest, "id", "") == request.mod; });

        if (mod == manifests.end())
        {
            errorMessage = "no mod " + request.mod + " in the mods folder";
            return false;
        }

        const std::optional<std::array<int, 2>> range = mapRangeOf(*mod);

        if (!range)
        {
            errorMessage = "the mod " + request.mod + " declares no map numbers (mod.yml idRanges.maps; oymap mod pack "
                "--maps <first>-<last>)";
            return false;
        }

        proposal.range = *range;
        proposal.from = "mod:" + request.mod;
    }
    else if (worldRange)
    {
        proposal.range = *worldRange;
        proposal.from = "world:" + request.world;
    }
    else
    {
        proposal.range = StudioMapNumbers;
        proposal.from = "studio";
    }

    // Declared ranges that overlap: two mods, or a mod and the world (the game's rule for world and ruleset ranges).
    std::vector<std::pair<std::string, std::array<int, 2>>> declared;

    if (worldRange)
    {
        declared.emplace_back("the world " + request.world, *worldRange);
    }

    std::set<std::string> seen;

    for (const YAML::Node &manifest : manifests)
    {
        const std::string id = textOf(manifest, "id", "");

        if (const std::optional<std::array<int, 2>> range = mapRangeOf(manifest); range && seen.insert(id).second)
        {
            declared.emplace_back("the mod " + id, *range);
        }
    }

    for (size_t first = 0; first < declared.size(); ++first)
    {
        for (size_t second = first + 1; second < declared.size(); ++second)
        {
            if (declared[first].second[0] <= declared[second].second[1]
                && declared[second].second[0] <= declared[first].second[1])
            {
                proposal.warnings.push_back(declared[first].first + "'s map numbers (" + std::to_string(
                    declared[first].second[0]) + " to " + std::to_string(declared[first].second[1]) + ") overlap "
                    + declared[second].first + "'s (" + std::to_string(declared[second].second[0]) + " to "
                    + std::to_string(declared[second].second[1]) + ")");
            }
        }
    }

    std::set<int> taken;
    std::string text;

    if (readText(request.assetRoot / "engine" / "data_tables" / "map_stats.txt", text))
    {
        tableNumbers(text, taken);
    }

    if (!request.modsRoot.empty() && readText(request.modsRoot / "engine" / "data_tables" / "map_stats.txt", text))
    {
        tableNumbers(text, taken);
    }

    for (const YAML::Node &manifest : manifests)
    {
        for (const YAML::Node &number : childOf(manifest, "map_numbers"))
        {
            taken.insert(number.as<int>());
        }
    }

    for (const std::filesystem::path &root : request.projects)
    {
        const YAML::Node card = readYaml(root / "project.yml");
        const YAML::Node id = childOf(childOf(card, "map_stats"), "id");

        if (id.IsDefined() && id.IsScalar() && textOf(card, "base", "").empty())
        {
            try
            {
                taken.insert(id.as<int>());
            }
            catch (const YAML::Exception &)
            {
            }
        }
    }

    for (const int number : taken)
    {
        if (number >= proposal.range[0] && number <= proposal.range[1])
        {
            proposal.taken.push_back(number);
        }
    }

    for (int number = proposal.range[0]; number <= proposal.range[1]; ++number)
    {
        if (!taken.contains(number))
        {
            proposal.number = number;
            return true;
        }
    }

    errorMessage = "every map number from " + std::to_string(proposal.range[0]) + " to "
        + std::to_string(proposal.range[1]) + " (" + proposal.from + ") is taken";
    return false;
}

std::string applyTableRows(const std::string &baseText, const std::string &overrideText, const std::string &appendText)
{
    TableText table = splitTable(baseText);

    for (const std::string &line : splitTable(overrideText).lines)
    {
        const std::vector<std::string> cells = cellsOf(line);

        if (cells.size() < 3 || cells[0] == "key" || cells[1].empty() || cells[1][0] != '#')
        {
            continue;
        }

        const size_t column = static_cast<size_t>(std::stoul(cells[1].substr(1)));

        for (std::string &row : table.lines)
        {
            if (keyOf(row) == cells[0])
            {
                std::vector<std::string> rowCells = cellsOf(row);
                rowCells.resize(std::max(rowCells.size(), column + 1));
                rowCells[column] = cells[2];
                row = joinCells(rowCells);
                break;
            }
        }
    }

    for (const std::string &line : splitTable(appendText).lines)
    {
        if (line.empty())
        {
            continue;
        }

        // A row whose key the table has already (a mod installed twice) replaces it.
        const std::string key = keyOf(line);
        const std::vector<std::string>::iterator known = std::find_if(table.lines.begin(), table.lines.end(),
            [&key](const std::string &row) { return !key.empty() && keyOf(row) == key; });

        if (known != table.lines.end())
        {
            *known = line;
        }
        else
        {
            // After the last row with content (tables may end in blank lines).
            size_t at = table.lines.size();

            while (at > 0 && table.lines[at - 1].find_first_not_of(" \t") == std::string::npos)
            {
                --at;
            }

            table.lines.insert(table.lines.begin() + static_cast<std::ptrdiff_t>(at), line);
        }
    }

    return joinTable(table);
}

void diffTableRows(const std::string &baseText, const std::string &changedText, std::string &overrideText,
    std::string &appendText)
{
    const TableText base = splitTable(baseText);
    std::map<std::string, std::string> baseRows;

    for (const std::string &line : base.lines)
    {
        baseRows.emplace(keyOf(line), line);
    }

    overrideText.clear();
    appendText.clear();

    for (const std::string &line : splitTable(changedText).lines)
    {
        const std::string key = keyOf(line);
        const std::map<std::string, std::string>::const_iterator known = baseRows.find(key);

        if (known == baseRows.end())
        {
            appendText += line + "\n";
            continue;
        }

        if (known->second == line || key.empty())
        {
            continue;
        }

        const std::vector<std::string> before = cellsOf(known->second);
        const std::vector<std::string> after = cellsOf(line);

        for (size_t column = 1; column < after.size(); ++column)
        {
            if (column >= before.size() || before[column] != after[column])
            {
                overrideText += (overrideText.empty() ? "key\tcolumn\tvalue\n" : "") + key + "\t#"
                    + std::to_string(column) + "\t" + after[column] + "\n";
            }
        }
    }
}

bool packMod(const ModPackRequest &request, ModPackResult &result, std::string &errorMessage)
{
    if (request.id.empty() || request.id.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_") != std::string::npos)
    {
        errorMessage = "a mod's id is lower case letters, digits and underscores";
        return false;
    }

    if (request.projects.empty())
    {
        errorMessage = "a mod packs one project or more";
        return false;
    }

    if (request.mapRange && ((*request.mapRange)[0] < 1 || (*request.mapRange)[1] < (*request.mapRange)[0]))
    {
        errorMessage = "a map range is [first, last] with 1 <= first <= last";
        return false;
    }

    result.folder = request.out / request.id;
    const std::filesystem::path stage = request.out / (".stage_" + request.id);
    std::error_code error;
    std::filesystem::remove_all(stage, error);
    std::filesystem::remove_all(result.folder, error);
    std::filesystem::create_directories(result.folder, error);
    YAML::Node manifest(YAML::NodeType::Map);
    manifest["format"] = 1;
    manifest["id"] = request.id;
    manifest["name"] = request.name.empty() ? request.id : request.name;
    manifest["version"] = request.version;

    if (!request.author.empty())
    {
        manifest["author"] = request.author;
    }

    if (!request.description.empty())
    {
        manifest["description"] = request.description;
    }

    std::set<std::string> worlds;
    std::set<std::string> tables;
    YAML::Node maps(YAML::NodeType::Sequence);
    YAML::Node mapNumbers(YAML::NodeType::Sequence);

    for (const std::filesystem::path &projectRoot : request.projects)
    {
        Project project;
        std::vector<ProjectIssue> issues;

        if (!loadProject(projectRoot, project, issues) || hasErrors(issues))
        {
            errorMessage = projectRoot.generic_string() + " does not read as a project";
            return false;
        }

        const YAML::Node card = project.document("project.yml");
        const std::string world = textOf(card, "world", "");
        const std::filesystem::path build = project.root / "build";
        std::string buildJson;

        if (request.build)
        {
            BuildOptions options;
            options.outputDirectory = build;
            options.assetRoot = request.assetRoot;
            BuildResult built;

            if (!buildProject(project, options, built))
            {
                size_t errors = 0;
                std::string first;

                for (const ProjectIssue &issue : built.issues)
                {
                    errors += issue.isError() ? 1 : 0;
                    first = first.empty() && issue.isError() ? issue.file + " " + issue.path + ": " + issue.message
                                                             : first;
                }

                errorMessage = textOf(card, "id", "") + " does not build (" + std::to_string(errors) + " error(s)"
                    + (first.empty() ? std::string() : ", the first: " + first) + ")";
                return false;
            }
        }

        if (!readText(build / "build.json", buildJson))
        {
            errorMessage = textOf(card, "id", "") + " has no build: oymap build it first";
            return false;
        }

        const std::filesystem::path projectStage = stage / textOf(card, "id", "map");
        std::vector<std::string> installed;

        if (!installBuildIntoMount(project, build, projectStage, request.assetRoot, installed, errorMessage))
        {
            return false;
        }

        // The worlds' files, without the studio's own link to the project (<stem>.studio.yml).
        std::vector<std::string> files;
        const std::filesystem::path worldsFrom = projectStage / "worlds";

        for (std::filesystem::recursive_directory_iterator entry(worldsFrom, error), end; !error && entry != end;
             entry.increment(error))
        {
            if (entry->is_regular_file() && entry->path().filename().string().find(".studio.yml") == std::string::npos)
            {
                const std::filesystem::path relative = entry->path().lexically_relative(projectStage);
                const std::filesystem::path target = result.folder / relative;
                std::filesystem::create_directories(target.parent_path(), error);
                std::filesystem::copy_file(entry->path(), target, std::filesystem::copy_options::overwrite_existing,
                    error);
                files.push_back(relative.generic_string());
            }
        }

        std::sort(files.begin(), files.end());

        // The engine tables the install changed: their rows only.
        for (const char *pTable : {"map_stats.txt", "outdoor_travels.txt", "bolster_maps.txt"})
        {
            std::string staged;
            std::string base;

            if (!readText(projectStage / "engine" / "data_tables" / pTable, staged)
                || !readText(request.assetRoot / "engine" / "data_tables" / pTable, base))
            {
                continue;
            }

            std::string overrideText;
            std::string appendText;
            diffTableRows(base, staged, overrideText, appendText);

            if (overrideText.empty() && appendText.empty())
            {
                continue;
            }

            // Several projects of one mod: their rows together.
            std::string oldOverride;
            std::string oldAppend;
            readText(result.folder / "tables" / (std::string(pTable) + ".override.txt"), oldOverride);
            readText(result.folder / "tables" / (std::string(pTable) + ".append.txt"), oldAppend);

            if (!overrideText.empty())
            {
                overrideText = oldOverride.empty() ? overrideText : oldOverride + overrideText.substr(
                    overrideText.find('\n') + 1);
                writeTextFileAtomically(result.folder / "tables" / (std::string(pTable) + ".override.txt"),
                    overrideText, errorMessage);
            }

            if (!appendText.empty())
            {
                writeTextFileAtomically(result.folder / "tables" / (std::string(pTable) + ".append.txt"),
                    oldAppend + appendText, errorMessage);
            }

            tables.insert(pTable);
        }

        if (std::filesystem::exists(projectStage / "engine" / "rendering" / "sky" / "sky.yml", error))
        {
            result.warnings.push_back(textOf(card, "id", "") + ": its sky theme (engine/rendering/sky/sky.yml) is "
                "not packed: a mod cannot add a row to it yet");
        }

        YAML::Node map(YAML::NodeType::Map);
        const std::string base = textOf(card, "base", "");
        map["file"] = base.empty() ? textOf(card, "id", "") + (textOf(card, "kind", "") == "outdoor" ? ".odm" : ".blv")
                                   : base;
        map["world"] = world;
        map["kind"] = base.empty() ? "new" : "overlay";
        map["project"] = textOf(card, "id", "");
        const YAML::Node built = YAML::Load(buildJson);

        if (built["source_revision"])
        {
            map["source_revision"] = built["source_revision"].Scalar();
        }

        for (const std::string &file : files)
        {
            map["files"].push_back(file);
        }

        maps.push_back(map);
        worlds.insert(world);
        PackedMap packed;
        packed.file = map["file"].Scalar();
        packed.world = world;
        packed.kind = map["kind"].Scalar();
        packed.project = map["project"].Scalar();

        if (base.empty() && childOf(childOf(card, "map_stats"), "id").IsDefined())
        {
            const int number = childOf(childOf(card, "map_stats"), "id").as<int>();
            mapNumbers.push_back(number);
            packed.number = number;

            if (request.mapRange && (number < (*request.mapRange)[0] || number > (*request.mapRange)[1]))
            {
                result.warnings.push_back(textOf(card, "id", "") + ": its map number " + std::to_string(number)
                    + " lies outside the mod's range " + std::to_string((*request.mapRange)[0]) + " to "
                    + std::to_string((*request.mapRange)[1]) + " (project.yml map_stats.id)");
            }
        }

        result.files.insert(result.files.end(), files.begin(), files.end());
        result.maps.push_back(packed);
    }

    result.tables.assign(tables.begin(), tables.end());

    for (const std::string &world : worlds)
    {
        manifest["worlds"].push_back(world);
    }

    manifest["maps"] = maps;

    for (const std::string &table : tables)
    {
        YAML::Node entry(YAML::NodeType::Map);
        entry["table"] = table;
        std::error_code exists;

        if (std::filesystem::exists(result.folder / "tables" / (table + ".override.txt"), exists))
        {
            entry["override"] = "tables/" + table + ".override.txt";
            result.files.push_back("tables/" + table + ".override.txt");
        }

        if (std::filesystem::exists(result.folder / "tables" / (table + ".append.txt"), exists))
        {
            entry["append"] = "tables/" + table + ".append.txt";
            result.files.push_back("tables/" + table + ".append.txt");
        }

        manifest["tables"].push_back(entry);
    }

    if (mapNumbers.size() > 0)
    {
        manifest["map_numbers"] = mapNumbers;
    }

    if (request.mapRange)
    {
        manifest["idRanges"]["maps"]["begin"] = (*request.mapRange)[0];
        manifest["idRanges"]["maps"]["end"] = (*request.mapRange)[1];
    }

    std::filesystem::remove_all(stage, error);

    if (!writeYaml(result.folder / "mod.yml", manifest, "mod.schema.json", errorMessage))
    {
        return false;
    }

    result.files.insert(result.files.begin(), "mod.yml");
    return true;
}

bool installMod(const std::filesystem::path &modFolder, const std::filesystem::path &modsRoot,
    const std::filesystem::path &assetRoot, const std::string &layout, ModInstallResult &result,
    std::string &errorMessage)
{
    const YAML::Node manifest = readYaml(modFolder / "mod.yml");
    const std::string id = textOf(manifest, "id", "");

    if (id.empty())
    {
        errorMessage = modFolder.generic_string() + " has no mod.yml with an id";
        return false;
    }

    std::error_code error;
    std::filesystem::create_directories(modsRoot, error);

    if (layout == "named")
    {
        // The game's named mods (devdocs/NAMED_MODS.md): the folder as it is, and the enabled list.
        std::filesystem::remove_all(modsRoot / id, error);

        if (!copyTree(modFolder, modsRoot / id, result.files, modsRoot, errorMessage))
        {
            return false;
        }

        YAML::Node enabled = readYaml(modsRoot / "enabled.yml");

        if (!enabled.IsDefined() || !enabled.IsMap())
        {
            enabled = YAML::Node(YAML::NodeType::Map);
            enabled["format"] = 1;
            enabled["enabled"] = YAML::Node(YAML::NodeType::Sequence);
        }

        bool listed = false;

        for (const YAML::Node &name : enabled["enabled"])
        {
            listed = listed || name.Scalar() == id;
        }

        if (!listed)
        {
            enabled["enabled"].push_back(id);
        }

        // The game reads the mods folder once, at its start (devdocs/NAMED_MODS.md).
        result.warnings.push_back("mods/" + id + "/ is on in enabled.yml: a running game mounts it at its next start");
        return writeYaml(modsRoot / "enabled.yml", enabled, nullptr, errorMessage);
    }

    if (layout != "merged")
    {
        errorMessage = "a layout is merged or named";
        return false;
    }

    // A copy of the mod beside the record, so it can be switched off and on again.
    const std::filesystem::path copy = modsRoot / CopiesName / id;
    std::vector<std::string> copied;
    std::filesystem::remove_all(copy, error);

    if (!copyTree(modFolder, copy, copied, modsRoot, errorMessage))
    {
        return false;
    }

    Registry registry = Registry::load(modsRoot);
    YAML::Node mods(YAML::NodeType::Sequence);

    for (const YAML::Node &mod : registry.document["mods"])
    {
        if (mod["id"].Scalar() != id)
        {
            mods.push_back(mod);
        }
    }

    // Files another installed mod brings too: the later install wins, as in one merged folder.
    std::set<std::string> others;

    for (const YAML::Node &mod : mods)
    {
        for (const YAML::Node &file : mod["files"])
        {
            others.insert(file.Scalar());
        }
    }

    YAML::Node entry(YAML::NodeType::Map);
    entry["id"] = id;
    entry["version"] = textOf(manifest, "version", "");
    entry["enabled"] = true;

    for (const char *pTree : {"engine", "worlds"})
    {
        std::vector<std::string> files;

        if (!copyTree(modFolder / pTree, modsRoot / pTree, files, modsRoot, errorMessage))
        {
            return false;
        }

        for (const std::string &file : files)
        {
            entry["files"].push_back(file);
            result.files.push_back(file);

            if (others.contains(file))
            {
                result.warnings.push_back(file + " is brought by another installed mod too: " + id + "'s replaces it");
            }
        }
    }

    // A table file in the merged folder that no studio mod composed (copied in by hand, or another tool's) would be
    // overwritten: said, not silently.
    for (const YAML::Node &table : childOf(manifest, "tables"))
    {
        const std::string name = textOf(table, "table", "");
        const std::filesystem::path target = modsRoot / "engine" / "data_tables" / name;
        const std::set<std::string> known = tablesOfMods(modsRoot, registry);

        if (std::filesystem::exists(target, error) && !known.contains(name))
        {
            result.warnings.push_back("mods/engine/data_tables/" + name + " was not composed by the studio: it is "
                "replaced by the asset root's table with the installed mods' rows");
        }
    }

    mods.push_back(entry);
    registry.document["mods"] = mods;

    if (!writeYaml(modsRoot / RegistryName, registry.document, nullptr, errorMessage))
    {
        return false;
    }

    return composeTables(modsRoot, assetRoot, tablesOfMods(modsRoot, registry), registry, result, errorMessage);
}

bool setModEnabled(const std::string &id, bool enabled, const std::filesystem::path &modsRoot,
    const std::filesystem::path &assetRoot, ModInstallResult &result, std::string &errorMessage)
{
    Registry registry = Registry::load(modsRoot);
    bool found = false;
    std::error_code error;

    for (YAML::Node mod : registry.document["mods"])
    {
        if (mod["id"].Scalar() != id)
        {
            continue;
        }

        found = true;
        mod["enabled"] = enabled;
        const std::filesystem::path copy = modsRoot / CopiesName / id;

        if (enabled)
        {
            YAML::Node files(YAML::NodeType::Sequence);

            for (const char *pTree : {"engine", "worlds"})
            {
                std::vector<std::string> copied;

                if (!copyTree(copy / pTree, modsRoot / pTree, copied, modsRoot, errorMessage))
                {
                    return false;
                }

                for (const std::string &file : copied)
                {
                    files.push_back(file);
                    result.files.push_back(file);
                }
            }

            mod["files"] = files;
        }
        else
        {
            for (const YAML::Node &file : mod["files"])
            {
                std::filesystem::remove(modsRoot / file.Scalar(), error);
                result.files.push_back(file.Scalar());
            }
        }
    }

    if (!found)
    {
        errorMessage = "no mod " + id + " is installed in " + modsRoot.filename().generic_string()
            + " (merged installs only)";
        return false;
    }

    if (!writeYaml(modsRoot / RegistryName, registry.document, nullptr, errorMessage))
    {
        return false;
    }

    return composeTables(modsRoot, assetRoot, tablesOfMods(modsRoot, registry), registry, result, errorMessage);
}

void writeModList(const std::filesystem::path &modsRoot, JsonWriter &writer)
{
    const Registry registry = Registry::load(modsRoot);
    writer.key("merged");
    writer.beginArray();

    for (const YAML::Node &mod : registry.document["mods"])
    {
        const YAML::Node manifest = readYaml(modsRoot / CopiesName / mod["id"].Scalar() / "mod.yml");
        writer.beginObject();
        writer.field("id", mod["id"].Scalar());
        writer.field("name", textOf(manifest, "name", mod["id"].Scalar()));
        writer.field("version", textOf(manifest, "version", ""));
        writer.field("enabled", !(mod["enabled"] && mod["enabled"].Scalar() == "false"));
        writer.field("files", static_cast<uint64_t>(mod["files"] ? mod["files"].size() : 0));
        writeModNumbers(writer, manifest);
        writer.endObject();
    }

    writer.endArray();
    const YAML::Node enabled = readYaml(modsRoot / "enabled.yml");
    std::set<std::string> enabledIds;

    for (const YAML::Node &name : childOf(enabled, "enabled"))
    {
        enabledIds.insert(name.Scalar());
    }

    std::vector<std::string> named;
    std::error_code error;

    for (std::filesystem::directory_iterator entry(modsRoot, error), end; !error && entry != end;
         entry.increment(error))
    {
        if (entry->is_directory() && std::filesystem::exists(entry->path() / "mod.yml"))
        {
            named.push_back(entry->path().filename().string());
        }
    }

    std::sort(named.begin(), named.end());
    writer.key("named");
    writer.beginArray();

    for (const std::string &id : named)
    {
        const YAML::Node manifest = readYaml(modsRoot / id / "mod.yml");
        writer.beginObject();
        writer.field("id", id);
        writer.field("name", textOf(manifest, "name", id));
        writer.field("version", textOf(manifest, "version", ""));
        writer.field("enabled", enabledIds.contains(id));
        writer.field("maps", static_cast<uint64_t>(childOf(manifest, "maps").IsDefined() ? manifest["maps"].size() : 0));
        writeModNumbers(writer, manifest);
        writer.endObject();
    }

    writer.endArray();
}
}
