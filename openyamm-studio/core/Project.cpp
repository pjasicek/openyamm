#include "core/Project.h"

#include "core/CanonicalYaml.h"
#include "core/Pins.h"

#include "engine/update/Sha256.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <fstream>
#include <sstream>

namespace OpenYAMM::Studio
{
const char *severityName(IssueSeverity severity)
{
    switch (severity)
    {
    case IssueSeverity::Warning:
        return "warning";
    case IssueSeverity::Note:
        return "note";
    case IssueSeverity::Error:
        break;
    }

    return "error";
}

bool hasErrors(const std::vector<ProjectIssue> &issues)
{
    return std::any_of(issues.begin(), issues.end(), [](const ProjectIssue &issue) { return issue.isError(); });
}

bool Project::has(const std::string &name) const
{
    return files.contains(name);
}

YAML::Node Project::document(const std::string &name) const
{
    const std::map<std::string, ProjectFile>::const_iterator iterator = files.find(name);
    return iterator == files.end() ? YAML::Node(YAML::NodeType::Undefined) : iterator->second.document;
}

const std::vector<ProjectFileKind> &projectFileKinds()
{
    static const std::vector<ProjectFileKind> kinds = {
        {"project.yml", "project.schema.json", true, ProjectFileClass::Source},
        {"plan.yml", "plan.schema.json", false, ProjectFileClass::Source},
        {"sketch.yml", "sketch.schema.json", false, ProjectFileClass::Source},
        {"rooms.yml", "rooms.schema.json", false, ProjectFileClass::Source},
        {"objects.yml", "objects.schema.json", false, ProjectFileClass::Source},
        {"wiring.yml", "wiring.schema.json", false, ProjectFileClass::Source},
        {"atmosphere.yml", "atmosphere.schema.json", false, ProjectFileClass::Source},
        {"review/pins.yml", "pins.schema.json", false, ProjectFileClass::Review},
        {"ids.lock.yml", "ids_lock.schema.json", false, ProjectFileClass::Record},
    };
    return kinds;
}

bool isSourceFile(const std::string &name)
{
    for (const ProjectFileKind &kind : projectFileKinds())
    {
        if (name == kind.pName)
        {
            return kind.fileClass == ProjectFileClass::Source;
        }
    }

    return false;
}

std::string contentHash128(const std::string &text)
{
    return Engine::sha256Hex(text.data(), text.size()).substr(0, 32);
}

std::string lockHashOfText(const std::string *pLockText)
{
    return pLockText == nullptr ? std::string("none") : contentHash128(*pLockText);
}

std::string projectLockHash(const std::filesystem::path &projectRoot)
{
    std::string text;
    return readTextFile(projectRoot / "ids.lock.yml", text) ? lockHashOfText(&text) : lockHashOfText(nullptr);
}

bool readTextFile(const std::filesystem::path &path, std::string &text)
{
    std::ifstream stream(path, std::ios::binary);

    if (!stream)
    {
        return false;
    }

    std::ostringstream buffer;
    buffer << stream.rdbuf();
    text = buffer.str();
    return true;
}

std::string studioStyleWorld(const std::filesystem::path &assetRoot, const std::string &world)
{
    const auto shipped = [](const std::string &name)
    {
        return name == "mm6" || name == "mm7" || name == "mm8" || name == "mm9";
    };
    std::string manifest;

    if (shipped(world) || assetRoot.empty() || world.empty()
        || !readTextFile(assetRoot / "worlds" / world / "world.yml", manifest))
    {
        return world;
    }

    try
    {
        const YAML::Node tileset = YAML::Load(manifest)["terrainTileset"];
        const std::string base = tileset.IsScalar() ? tileset.Scalar() : std::string();
        return base == "mm6" || base == "mm7" || base == "mm8" ? base : world;
    }
    catch (const YAML::Exception &)
    {
        return world;
    }
}

bool readWorldTable(
    const std::filesystem::path &assetRoot,
    const std::string &world,
    const std::string &fileName,
    const std::string &tableName,
    std::string &text)
{
    if (assetRoot.empty() || !readTextFile(assetRoot / "engine" / "data_tables" / fileName, text))
    {
        return false;
    }

    std::string manifest;

    if (world.empty() || !readTextFile(assetRoot / "worlds" / world / "world.yml", manifest))
    {
        return true;
    }

    try
    {
        const YAML::Node contributions = YAML::Load(manifest)["tableContributions"];

        for (const YAML::Node &contribution : contributions.IsSequence() ? contributions : YAML::Node())
        {
            std::string rows;

            if (contribution.IsMap() && contribution["table"].as<std::string>("") == tableName
                && contribution["mode"].as<std::string>("") == "append"
                && readTextFile(assetRoot / "worlds" / world / contribution["path"].as<std::string>(""), rows))
            {
                text += "\n" + rows;
            }
        }
    }
    catch (const YAML::Exception &)
    {
        // A manifest that does not parse adds nothing (the game refuses the world).
    }

    return true;
}

namespace
{
template <typename Write>
bool writeAtomically(const std::filesystem::path &path, std::string &errorMessage, Write write)
{
    std::error_code error;

    if (path.has_parent_path())
    {
        std::filesystem::create_directories(path.parent_path(), error);
    }

    std::filesystem::path temporaryPath = path;
    temporaryPath += ".oymap-tmp";

    {
        std::ofstream stream(temporaryPath, std::ios::binary | std::ios::trunc);

        if (!stream)
        {
            errorMessage = "could not write " + temporaryPath.string();
            return false;
        }

        write(stream);

        if (!stream.good())
        {
            errorMessage = "could not write " + temporaryPath.string();
            return false;
        }
    }

    std::filesystem::rename(temporaryPath, path, error);

    if (error)
    {
        errorMessage = "could not replace " + path.string() + ": " + error.message();
        std::filesystem::remove(temporaryPath, error);
        return false;
    }

    return true;
}
}

bool writeTextFileAtomically(const std::filesystem::path &path, const std::string &text, std::string &errorMessage)
{
    return writeAtomically(
        path,
        errorMessage,
        [&text](std::ofstream &stream)
        {
            stream.write(text.data(), static_cast<std::streamsize>(text.size()));
        });
}

bool writeBinaryFileAtomically(
    const std::filesystem::path &path,
    const std::vector<uint8_t> &bytes,
    std::string &errorMessage)
{
    return writeAtomically(
        path,
        errorMessage,
        [&bytes](std::ofstream &stream)
        {
            stream.write(reinterpret_cast<const char *>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
        });
}

bool loadProject(const std::filesystem::path &root, Project &project, std::vector<ProjectIssue> &issues)
{
    project = {};
    project.root = root;
    std::error_code error;

    if (!std::filesystem::is_directory(root, error))
    {
        // No absolute path in the core's messages (the request list's rule): the caller knows what it named.
        issues.push_back({"", "", "not a project folder (no such folder)", "project"});
        return false;
    }

    for (const ProjectFileKind &kind : projectFileKinds())
    {
        const std::filesystem::path path = root / kind.pName;

        if (!std::filesystem::exists(path, error))
        {
            if (kind.required)
            {
                issues.push_back({kind.pName, "", "the project has no " + std::string(kind.pName), "project"});
            }

            continue;
        }

        ProjectFile file;
        file.name = kind.pName;
        file.schema = kind.pSchema;

        if (!readTextFile(path, file.text))
        {
            issues.push_back({kind.pName, "", "could not read the file", "project"});
            continue;
        }

        try
        {
            file.document = YAML::Load(file.text);
        }
        catch (const YAML::Exception &exception)
        {
            issues.push_back({kind.pName, "", std::string("not valid YAML: ") + exception.what(), "yaml"});
            continue;
        }

        project.files[file.name] = file;
    }

    return project.has("project.yml");
}

void validateProjectSchemas(const Project &project, std::vector<ProjectIssue> &issues)
{
    for (const std::pair<const std::string, ProjectFile> &entry : project.files)
    {
        validateFileSchema(entry.second, issues);
    }
}

void validateFileSchema(const ProjectFile &file, std::vector<ProjectIssue> &issues)
{
    // The pins document is read as format 1 (a format 0 one is migrated when it is next written: core/Pins.h).
    const YAML::Node document = file.schema == "pins.schema.json" ? migratePinsDocument(file.document) : file.document;

    for (const SchemaIssue &issue : SchemaSet::builtIn().validate(document, file.schema))
    {
        issues.push_back({file.name, issue.path, issue.message, "schema"});
    }
}

std::string canonicalText(const ProjectFile &file)
{
    return writeCanonicalYaml(file.document, SchemaSet::builtIn(), file.schema);
}

MapArrivalLookup findMapArrival(
    const std::filesystem::path &assetRoot,
    const std::filesystem::path &mountRoot,
    const std::string &world,
    const std::string &map,
    const std::string &name,
    MapArrival &arrival,
    std::string &known)
{
    const std::string studioName = std::filesystem::path(map).stem().string() + ".studio.yml";
    known.clear();

    for (const std::filesystem::path &root : {mountRoot, assetRoot})
    {
        std::string text;

        if (root.empty() || !readTextFile(root / "worlds" / world / "maps" / studioName, text))
        {
            continue;
        }

        try
        {
            const YAML::Node arrivals = YAML::Load(text)["arrivals"];

            for (const YAML::Node &entry : arrivals && arrivals.IsSequence() ? arrivals : YAML::Node())
            {
                const std::string entryName = entry["name"] ? entry["name"].as<std::string>("") : std::string();
                const YAML::Node at = entry["at"];

                if (entryName.empty() || !at || !at.IsSequence() || at.size() != 3)
                {
                    continue;
                }

                if (entryName == name)
                {
                    arrival.name = entryName;

                    for (size_t axis = 0; axis < 3; ++axis)
                    {
                        arrival.at[axis] = at[axis].as<int>(0);
                    }

                    arrival.facing = entry["facing"] ? entry["facing"].as<int>(0) : 0;
                    return MapArrivalLookup::Found;
                }

                known += (known.empty() ? "" : ", ") + entryName;
            }
        }
        catch (const YAML::Exception &)
        {
        }

        return MapArrivalLookup::Unknown;
    }

    return MapArrivalLookup::NotInstalled;
}

bool resolveMapArrival(
    const std::filesystem::path &assetRoot,
    const std::filesystem::path &mountRoot,
    const std::string &world,
    const std::string &map,
    const std::string &name,
    MapArrival &arrival,
    std::string &warning)
{
    std::string known;
    warning.clear();
    arrival = MapArrival();

    switch (findMapArrival(assetRoot, mountRoot, world, map, name, arrival, known))
    {
    case MapArrivalLookup::Found:
        return true;
    case MapArrivalLookup::NotInstalled:
        warning = "the arrival " + name + " of " + map + " is not known: " + map + " is not installed in worlds/"
            + world + " of the asset root" + (mountRoot.empty() ? "" : " or the mount") + " (its <stem>.studio.yml "
            "lists its arrivals); the party arrives at its start until it is installed and this map is built again";
        arrival = MapArrival();
        return true;
    case MapArrivalLookup::Unknown:
        break;
    }

    warning = map + " has no arrival " + name + " (it has: " + (known.empty() ? std::string("none") : known)
        + "); an arrival is `start` or a plan.yml entrance of kind arrival or both, which `oymap install` lists";
    return false;
}

bool readMoveScreen(const YAML::Node &screen, const std::string &map, MoveScreen &result, std::string &error)
{
    result = {};
    std::string lowerMap = map;
    std::transform(lowerMap.begin(), lowerMap.end(), lowerMap.begin(),
        [](unsigned char character) { return static_cast<char>(std::tolower(character)); });

    if (!screen.IsDefined() || screen.IsNull())
    {
        result.picture = lowerMap.ends_with(".blv") ? 1 : 0;
        return true;
    }

    if (screen.IsScalar() && screen.Scalar() == "none")
    {
        result.direct = true;
        return true;
    }

    const auto wholeNumber = [&](const char *pKey, int fallback, int &value)
    {
        const YAML::Node node = screen[pKey];

        if (!node)
        {
            value = fallback;
            return true;
        }

        try
        {
            const double number = node.as<double>();

            if (number < 0.0 || number != std::floor(number) || number > 65535.0)
            {
                return false;
            }

            value = static_cast<int>(number);
            return true;
        }
        catch (const YAML::Exception &)
        {
            return false;
        }
    };

    if (!screen.IsMap() || (screen["text"] && screen["house"]) || !wholeNumber("text", 0, result.text)
        || (!screen["text"] && !wholeNumber("house", 0, result.text)) || !wholeNumber("picture", 1, result.picture))
    {
        error = "screen is `none` (a direct move) or {text: <the trans.txt row whose line the entrance window shows, "
                "0 for \"Do you wish to enter ...?\">, picture: <its picture, 1 when left out>}, whole numbers; "
                "left out, a move into a dungeon shows the standard window (picture 1)";
        return false;
    }

    for (const auto &entry : screen)
    {
        const std::string key = entry.first.as<std::string>();

        if (key != "text" && key != "house" && key != "picture")
        {
            error = "screen takes `text` and `picture`, not `" + key + "`";
            return false;
        }
    }

    return true;
}

std::string moveScreenOptions(const MoveScreen &screen)
{
    return screen.direct ? ", {direct = true}" : std::string();
}
}
