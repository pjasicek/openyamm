#include "cli/Commands.h"

#include "cli/OutdoorCommands.h"
#include "core/Audit.h"
#include "core/compile/EditorDocument.h"
#include "core/compile/LegacyCompileIndoor.h"
#include "core/CanonicalYaml.h"
#include "core/Compare.h"
#include "core/EventFlow.h"
#include "core/Import.h"
#include "core/IndoorBuild.h"
#include "core/Json.h"
#include "core/MapExport.h"
#include "core/Mods.h"
#include "core/Ops.h"
#include "core/OutdoorBuild.h"
#include "core/OutdoorGround.h"
#include "core/OutdoorInteractive.h"
#include "core/OutdoorLowering.h"
#include "core/Preview.h"
#include "core/Metrics.h"
#include "core/Project.h"
#include "core/Reachability.h"
#include "core/Schema.h"
#include "core/SketchRead.h"
#include "core/Things.h"
#include "core/View.h"

#include "engine/ImageAssetLoader.h"
#include "game/maps/TerrainTileData.h"

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <map>
#include <random>
#include <set>
#include <sstream>
#include <iterator>

#include <unistd.h>

namespace OpenYAMM::Studio
{
bool takeFlag(std::vector<std::string> &arguments, const std::string &flag)
{
    for (size_t index = 0; index < arguments.size(); ++index)
    {
        if (arguments[index] == flag)
        {
            arguments.erase(arguments.begin() + static_cast<std::ptrdiff_t>(index));
            return true;
        }
    }

    return false;
}

bool takeOption(std::vector<std::string> &arguments, const std::string &option, std::string &value)
{
    for (size_t index = 0; index + 1 < arguments.size(); ++index)
    {
        if (arguments[index] == option)
        {
            value = arguments[index + 1];
            arguments.erase(
                arguments.begin() + static_cast<std::ptrdiff_t>(index),
                arguments.begin() + static_cast<std::ptrdiff_t>(index) + 2);
            return true;
        }
    }

    return false;
}

namespace
{
std::string worldOfMapPath(const std::filesystem::path &path);

// What one openTarget learnt about what it opened, kept by its caller (no process-wide state: a long-lived core opens
// many targets, and one call must never read another's): why it failed, the issues of a project that did not build,
// the private folder a project was built into, and a project's rooms, doors and events by their numbers.
struct OpenedTarget
{
    TargetFailure failure = TargetFailure::None;
    std::vector<ProjectIssue> buildIssues;
    std::filesystem::path previewFolder;
    std::map<int, std::string> sectorNames;
    CoplanarNames objectNames;
    // A project's decorations (by entity number) that hang: `hangs: true` or on a wall (audit's thing.floating), and
    // its storerooms (sectors of rooms with `store: true`); for an installed map from its <stem>.studio.yml.
    std::set<int> hangingDecorations;
    std::set<int> storerooms;
    // Door numbers of lifts that are trapdoors (objects.yml lifts[].trap), which the ride check leaves out.
    std::set<int> trapDoors;
    // project.yml identity.shape (D-89), for the cave-shape check.
    std::string identityShape;
    // D-91: the project's cave mouths that lead nowhere (DressingFacts::blindMouths).
    std::vector<std::string> blindMouths;
};

bool openTarget(
    AssetSession &session,
    const std::filesystem::path &assetRoot,
    std::string &world,
    std::string &target,
    OpenedTarget &opened,
    std::string &errorMessage);

void writeIssuesJson(JsonWriter &writer, const std::vector<ProjectIssue> &issues)
{
    writer.key("issues");
    writer.beginArray();

    for (const ProjectIssue &issue : issues)
    {
        writer.beginObject();
        writer.field("severity", severityName(issue.severity));
        writer.field("code", issue.code);
        writer.field("file", issue.file);
        writer.field("path", issue.path);
        writer.field("message", issue.message);
        writer.endObject();
    }

    writer.endArray();
}

void printIssues(const std::vector<ProjectIssue> &issues)
{
    for (const ProjectIssue &issue : issues)
    {
        // Errors as they always were; a warning or a note says so (S5_BROWSER_EDITOR.md 2.4.2).
        if (!issue.isError())
        {
            std::cerr << severityName(issue.severity) << ": ";
        }

        std::cerr << (issue.file.empty() ? "project" : issue.file);

        if (!issue.path.empty())
        {
            std::cerr << ": " << issue.path;
        }

        std::cerr << ": " << issue.message << "\n";
    }
}
}

int runExport(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    MapExportOptions options;
    options.summaryOnly = takeFlag(arguments, "--summary");
    const bool pretty = takeFlag(arguments, "--pretty");
    takeFlag(arguments, "--json");
    std::string outputPath;
    takeOption(arguments, "--out", outputPath);
    // With a world and an asset root the map's scene is read too, and the export gains the door records.
    std::string world;
    bool withWorld = takeOption(arguments, "--world", world);
    const std::filesystem::path assetRoot = takeAssetRoot(arguments);

    if (arguments.size() != 1)
    {
        std::cerr << "usage: oymap export <map.odm|map.blv> [--world <world> --assets <root> [--mount <folder>]] "
                     "[--summary] [--pretty] [--out <file>]\n"
                     "       oymap export <project> --assets <root> [--summary] [--pretty] [--out <file>]\n"
                     "  with --world and --assets the export also holds `doors` (the moving parts, from the scene);\n"
                     "  a map that is no file on disk is read by its name from the asset root and, with --mount,\n"
                     "  from a build's mount folder in front of it; a project is built privately and read\n";
        return 2;
    }

    std::filesystem::path path = arguments[0];
    std::vector<uint8_t> bytes;
    std::string errorMessage;
    std::error_code fileError;
    AssetSession session;
    bool sessionOpen = false;

    // A project folder, or a map named as the other commands name it (not a file here): through the asset root.
    if (!std::filesystem::is_regular_file(path, fileError))
    {
        std::string target = arguments[0];
        const bool isProject = std::filesystem::is_regular_file(path / "project.yml", fileError);

        if (assetRoot.empty() || (!isProject && !withWorld && worldOfMapPath(path).empty()))
        {
            std::cerr << "oymap export: " << path.string() << " is no file; a project, or a map by its name, needs "
                         "--assets <root> (and a map --world <world>)\n";
            return 1;
        }

        OpenedTarget opened;

        if (!openTarget(session, assetRoot, world, target, opened, errorMessage))
        {
            std::cerr << "oymap export: " << errorMessage << "\n";
            return 1;
        }

        const std::optional<std::vector<uint8_t>> read = session.files().readBinaryFile("Data/games/" + target);

        if (!read)
        {
            std::cerr << "oymap export: the world " << world << " has no map " << target << "\n";
            return 1;
        }

        bytes = *read;
        path = target;
        sessionOpen = true;
        withWorld = true;
    }
    else if (!readFileBytes(path, bytes, errorMessage))
    {
        std::cerr << "oymap export: " << errorMessage << "\n";
        return 1;
    }

    // An outdoor map's void (U-12) lives in its scene beside it.
    if (mapKindFromPath(path) == MapKind::Outdoor)
    {
        const std::string sceneName = path.stem().string() + ".scene.yml";
        std::string sceneText;

        if (sessionOpen)
        {
            sceneText = session.files().readTextFile("Data/games/" + sceneName).value_or(std::string());
        }
        else
        {
            readTextFile(path.parent_path() / sceneName, sceneText);
        }

        options.voidRects = sceneVoidRectangles(sceneText);
    }

    JsonWriter writer(pretty);
    writer.beginObject();
    writer.field("file", path.filename().string());
    writer.field("size", static_cast<uint64_t>(bytes.size()));
    writer.key("map");

    if (!exportMapJson(mapKindFromPath(path), bytes, options, writer, errorMessage))
    {
        std::cerr << "oymap export: " << path.string() << ": " << errorMessage << "\n";
        return 1;
    }

    if (withWorld && !assetRoot.empty())
    {
        LoadedMap map;

        if ((!sessionOpen && !session.open(assetRoot, world, errorMessage))
            || !loadMap(session, path.filename().string(), map, errorMessage))
        {
            std::cerr << "oymap export: " << errorMessage << "\n";
            return 1;
        }

        writer.key("doors");
        writer.beginArray();

        if (map.state && map.indoor)
        {
            for (const Game::MapDeltaDoor &door : map.state->doors)
            {
                if (door.doorId == 0 && door.vertexIds.empty())
                {
                    continue;
                }

                writer.beginObject();
                writer.field("id", door.doorId);
                writer.field("slot", door.slotIndex);
                writer.field("attributes", door.attributes);
                writer.field("state", door.state);
                writer.key("direction");
                writer.beginArray();
                writer.value(door.directionX);
                writer.value(door.directionY);
                writer.value(door.directionZ);
                writer.endArray();
                writer.field("move_length", door.moveLength);
                writer.field("open_speed", door.openSpeed);
                writer.field("close_speed", door.closeSpeed);
                int minimum[3] = {0, 0, 0};
                int maximum[3] = {0, 0, 0};
                bool any = false;

                for (uint16_t vertexId : door.vertexIds)
                {
                    if (vertexId >= map.indoor->vertices.size())
                    {
                        continue;
                    }

                    const Game::IndoorVertex &vertex = map.indoor->vertices[vertexId];
                    const int point[3] = {vertex.x, vertex.y, vertex.z};

                    for (int axis = 0; axis < 3; ++axis)
                    {
                        minimum[axis] = any ? std::min(minimum[axis], point[axis]) : point[axis];
                        maximum[axis] = any ? std::max(maximum[axis], point[axis]) : point[axis];
                    }

                    any = true;
                }

                // Where the moving vertices stand in the map file (the pose the file stores, not always closed).
                writer.key("bounds_min");
                writer.beginArray();
                writer.value(minimum[0]);
                writer.value(minimum[1]);
                writer.value(minimum[2]);
                writer.endArray();
                writer.key("bounds_max");
                writer.beginArray();
                writer.value(maximum[0]);
                writer.value(maximum[1]);
                writer.value(maximum[2]);
                writer.endArray();
                writer.key("vertices");
                writer.beginArray();

                for (uint16_t vertexId : door.vertexIds)
                {
                    writer.value(static_cast<unsigned>(vertexId));
                }

                writer.endArray();
                writer.key("faces");
                writer.beginArray();

                for (uint16_t faceId : door.faceIds)
                {
                    writer.value(static_cast<unsigned>(faceId));
                }

                writer.endArray();
                writer.key("sectors");
                writer.beginArray();

                for (uint16_t sectorId : door.sectorIds)
                {
                    writer.value(static_cast<unsigned>(sectorId));
                }

                writer.endArray();
                writer.endObject();
            }
        }

        writer.endArray();
    }

    writer.endObject();
    std::string text = writer.take();
    text.push_back('\n');

    if (outputPath.empty())
    {
        std::cout << text;
        return 0;
    }

    if (!writeTextFileAtomically(outputPath, text, errorMessage))
    {
        std::cerr << "oymap export: " << errorMessage << "\n";
        return 1;
    }

    return 0;
}

int runFmt(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const bool checkOnly = takeFlag(arguments, "--check");

    if (arguments.size() != 1)
    {
        std::cerr << "usage: oymap fmt <project> [--check]\n";
        return 2;
    }

    Project project;
    std::vector<ProjectIssue> issues;
    loadProject(arguments[0], project, issues);

    if (!issues.empty())
    {
        printIssues(issues);
        return 1;
    }

    int changed = 0;

    for (const std::pair<const std::string, ProjectFile> &entry : project.files)
    {
        const std::string canonical = canonicalText(entry.second);

        if (canonical == entry.second.text)
        {
            continue;
        }

        ++changed;

        if (checkOnly)
        {
            std::cout << entry.first << ": not in canonical form\n";
            continue;
        }

        std::string errorMessage;

        if (!writeTextFileAtomically(project.root / entry.first, canonical, errorMessage))
        {
            std::cerr << "oymap fmt: " << errorMessage << "\n";
            return 1;
        }

        std::cout << entry.first << ": rewritten\n";
    }

    return checkOnly && changed > 0 ? 1 : 0;
}

// `oymap reads`: the outdoor lowering's read record (S5_BROWSER_EDITOR.md 3.8): a dry build of the project with every
// read of the sketch recorded, then the words written on its objects that the build never read ("word X was never
// read on this object"): a word on a kind that ignores it, or a read under a condition this map does not meet (a
// note, not a fault). With --json every word of every object, read or not, for the kind tables.
int runReads(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const bool json = takeFlag(arguments, "--json");
    // Only the land words, lowered up to the peaks: what the kept land is made of (its key must cover them).
    const bool landOnly = takeFlag(arguments, "--land");
    std::string assets;
    takeOption(arguments, "--assets", assets);

    if (arguments.size() != 1)
    {
        std::cerr << "usage: oymap reads <outdoor project> [--assets <asset root>] [--land] [--json]\n";
        return 2;
    }

    Project project;
    std::vector<ProjectIssue> issues;
    loadProject(arguments[0], project, issues);

    if (!issues.empty() || !project.has("sketch.yml"))
    {
        printIssues(issues);
        std::cerr << (project.has("sketch.yml") ? "" : "oymap reads: the project has no sketch.yml\n");
        return 1;
    }

    BuildOptions options;
    options.assetRoot = assets;
    options.dryRun = true;
    BuildResult result;
    std::vector<SketchWord> words;
    size_t unplaced = 0;

    {
        SketchReadRecord record(project.document("sketch.yml"));

        if (landOnly)
        {
            lowerOutdoorLandOnly(project);
        }
        else
        {
            buildOutdoorProject(project, options, result);
        }

        words = record.words();
        unplaced = record.unplaced();
    }

    size_t unread = 0;

    for (const SketchWord &word : words)
    {
        unread += word.read ? 0 : 1;
    }

    if (json)
    {
        JsonWriter writer(false);
        writer.beginObject();
        writer.field("project", project.root.filename().string());
        writer.field("built", result.issues.empty());
        writer.field("issues", static_cast<uint64_t>(result.issues.size()));
        writer.field("unplaced", static_cast<uint64_t>(unplaced));
        writer.key("words");
        writer.beginArray();

        for (const SketchWord &word : words)
        {
            writer.beginObject();
            writer.field("object", word.object);
            writer.field("place", word.place);
            writer.key("kinds");
            writer.beginObject();

            for (const std::pair<const std::string, std::string> &kind : word.kinds)
            {
                writer.field(kind.first, kind.second);
            }

            writer.endObject();
            writer.field("word", word.word);
            writer.field("read", word.read);
            writer.endObject();
        }

        writer.endArray();
        writer.endObject();
        std::cout << writer.take() << "\n";
        return 0;
    }

    if (!result.issues.empty())
    {
        std::cout << "the build stopped at an issue: words after it count as unread\n";
        printIssues(result.issues);
    }

    for (const SketchWord &word : words)
    {
        if (word.read || word.object.empty())
        {
            continue;
        }

        std::string kind;

        for (const std::pair<const std::string, std::string> &each : word.kinds)
        {
            kind += (kind.empty() ? " (" : ", ") + each.first + " " + each.second;
        }

        std::cout << word.object << (kind.empty() ? "" : kind + ")") << ": the word `" << word.word
                  << "` was never read on this object\n";
    }

    std::cout << words.size() << " words, " << unread << " never read\n";
    return 0;
}

int runSchema(const std::vector<std::string> &arguments)
{
    const SchemaSet &schemas = SchemaSet::builtIn();

    if (arguments.empty())
    {
        for (const std::string &name : schemas.fileNames())
        {
            const YAML::Node root = schemas.root(name);
            std::cout << name << "  " << (root["title"] ? root["title"].Scalar() : std::string()) << "\n";
        }

        return 0;
    }

    std::string name = arguments[0];

    if (!schemas.has(name))
    {
        name += ".schema.json";
    }

    if (!schemas.has(name))
    {
        std::cerr << "oymap schema: no schema named " << arguments[0] << "\n";
        return 1;
    }

    std::cout << schemas.text(name);
    return 0;
}

int runCompileIndoor(const std::vector<std::string> &arguments)
{
    std::vector<std::string> storage = arguments;
    std::vector<char *> argv;
    std::string programName = "oymap compile-indoor";
    argv.push_back(programName.data());

    for (std::string &argument : storage)
    {
        argv.push_back(argument.data());
    }

    // The same function as build/tools/mm9_compile_indoor_source: the same arguments and output.
    return OpenYAMM::Compile::runLegacyCompileIndoor(static_cast<int>(argv.size()), argv.data());
}

// The asset root a command works against: --assets, else OYMAP_ASSETS, else none. With --mount <folder>, a build's
// mount folder is read in front of it (and given in `pMount`).
std::filesystem::path takeAssetRoot(std::vector<std::string> &arguments, std::filesystem::path *pMount)
{
    std::string root;
    std::string mount;
    takeOption(arguments, "--mount", mount);
    AssetSession::setExtraMount(mount);

    if (pMount != nullptr)
    {
        *pMount = mount;
    }

    if (takeOption(arguments, "--assets", root))
    {
        return root;
    }

    const char *pEnvironment = std::getenv("OYMAP_ASSETS");
    return pEnvironment != nullptr ? std::filesystem::path(pEnvironment) : std::filesystem::path();
}

namespace
{
// The world a reading command works in: --world, or none when it is pointed at a project folder (the project
// names its world).
// The world in a map file's path: "assets_dev/worlds/mm7/maps/7d06.blv" names mm7. Empty when the path has no such
// part.
std::string worldOfMapPath(const std::filesystem::path &path)
{
    const std::filesystem::path maps = path.parent_path();
    const std::filesystem::path worldFolder = maps.parent_path();
    return maps.filename() == "maps" && worldFolder.parent_path().filename() == "worlds"
        ? worldFolder.filename().string() : std::string();
}

bool takeWorld(std::vector<std::string> &arguments, std::string &world)
{
    if (takeOption(arguments, "--world", world))
    {
        return true;
    }

    std::error_code error;

    if (arguments.empty())
    {
        return false;
    }

    if (std::filesystem::is_regular_file(std::filesystem::path(arguments[0]) / "project.yml", error))
    {
        return true;
    }

    // A map given by its path in an asset root names its world itself.
    world = worldOfMapPath(arguments[0]);
    return !world.empty();
}

// The folders projects were built into for reading: removed when the command ends.
class PreviewFolders
{
public:
    ~PreviewFolders()
    {
        for (const std::filesystem::path &folder : m_folders)
        {
            std::error_code error;
            std::filesystem::remove_all(folder, error);
        }
    }

    void keep(const std::filesystem::path &folder)
    {
        m_folders.insert(folder);
    }

private:
    std::set<std::filesystem::path> m_folders;
};

PreviewFolders &previewFolders()
{
    static PreviewFolders folders;
    return folders;
}

// Opens what a reading command was pointed at. A map file name is read from the asset root (and its mount). A
// project folder is built into a private folder first and read from there as the game would read it, so a project
// can be audited, solved, rendered and measured without installing it; for an overlay project that is its base
// map with the overlay in front. `target` becomes the map file and `world` the project's world.
bool openTarget(
    AssetSession &session,
    const std::filesystem::path &assetRoot,
    std::string &world,
    std::string &target,
    OpenedTarget &opened,
    std::string &errorMessage)
{
    std::error_code error;
    opened = {};
    opened.failure = TargetFailure::Failed;

    if (!std::filesystem::is_regular_file(std::filesystem::path(target) / "project.yml", error))
    {
        // A map may be given as `export` takes it, by its path: it is read by its name, from the asset root and
        // the mount, like any other.
        const std::filesystem::path path = target;

        if (path.has_parent_path())
        {
            if (world.empty())
            {
                world = worldOfMapPath(path);
            }

            target = path.filename().string();
        }

        // An installed map's <stem>.studio.yml (oymap install) carries what its project said of it.
        const std::filesystem::path studioFile = (path.has_parent_path() ? path.parent_path()
            : assetRoot / "worlds" / world / "maps") / (std::filesystem::path(target).stem().string() + ".studio.yml");

        if (std::filesystem::is_regular_file(studioFile, error))
        {
            try
            {
                const DressingFacts facts = studioFileDressingFacts(YAML::LoadFile(studioFile.string()));
                opened.hangingDecorations = facts.hanging;
                opened.storerooms = facts.storerooms;
                opened.trapDoors = facts.traps;
                opened.identityShape = facts.identityShape;
                opened.blindMouths = facts.blindMouths;
            }
            catch (const YAML::Exception &)
            {
            }
        }

        return session.open(assetRoot, world, errorMessage);
    }

    // Reading must not change what is read: the build writes ids.lock.yml into its project, so a copy is built.
    const std::string key = std::to_string(std::hash<std::string>{}(
        std::filesystem::weakly_canonical(std::filesystem::path(target), error).string()));
    // One folder to each run: two commands on the same project at once must not build into one another's copy.
    // Named by the process and a token drawn once per process: every WebAssembly instance has the same process
    // number, so the number alone would let two instances share a folder.
    static const std::string processToken = []()
    {
        std::random_device random;
        char token[32];
        std::snprintf(token, sizeof(token), "%08x%08x", random(), random());
        return std::to_string(getpid()) + "_" + token;
    }();
    const std::filesystem::path work = std::filesystem::temp_directory_path()
        / ("oymap_preview_" + key + "_" + processToken);
    previewFolders().keep(work);
    opened.previewFolder = work;
    const std::filesystem::path copy = work / "project";
    std::filesystem::remove_all(copy, error);
    std::filesystem::create_directories(copy, error);

    for (std::filesystem::directory_iterator entry(std::filesystem::path(target), error), end; !error && entry != end;
         entry.increment(error))
    {
        std::error_code copyError;

        // The project's own files (its YAML and what they name, such as a diagram), and its review notes; not its
        // build, history or anything else kept beside it.
        if (entry->is_regular_file(copyError))
        {
            std::filesystem::copy_file(entry->path(), copy / entry->path().filename(), copyError);
        }
        else if (entry->is_directory(copyError) && entry->path().filename() == "review")
        {
            std::filesystem::copy(entry->path(), copy / "review", std::filesystem::copy_options::recursive, copyError);
        }
    }

    Project project;
    std::vector<ProjectIssue> issues;

    if (!loadProject(copy, project, issues) || !issues.empty())
    {
        opened.failure = issues.empty() || !project.has("project.yml") ? TargetFailure::NotAProject
            : TargetFailure::DoesNotBuild;
        opened.buildIssues = issues;
        errorMessage = issues.empty() ? "not a project" : issues.front().file + ": " + issues.front().message;
        return false;
    }

    BuildOptions options;
    options.assetRoot = assetRoot;
    options.outputDirectory = work / "build";
    BuildResult result;

    if (!buildProject(project, options, result))
    {
        opened.failure = result.issues.empty() ? TargetFailure::Failed : TargetFailure::DoesNotBuild;
        opened.buildIssues = result.issues;
        errorMessage = "the project does not build";

        for (const ProjectIssue &issue : result.issues)
        {
            errorMessage += "\n  " + issue.file + ": " + issue.path + ": " + issue.message;
        }

        return false;
    }

    std::vector<std::string> installed;

    if (!installBuildIntoMount(
            project, options.outputDirectory, work / "mount", assetRoot, installed, errorMessage, true))
    {
        return false;
    }

    const YAML::Node card = project.document("project.yml");
    world = card["world"].Scalar();
    const bool outdoor = card["kind"].IsDefined() && card["kind"].Scalar() == "outdoor";
    target = card["base"].IsDefined() ? card["base"].Scalar() : card["id"].Scalar() + (outdoor ? ".odm" : ".blv");

    // The rooms behind the built map's sector numbers, for commands that report sectors.
    if (!card["base"].IsDefined())
    {
        Project built;
        std::vector<ProjectIssue> unused;

        if (loadProject(project.root, built, unused) && built.has("ids.lock.yml"))
        {
            const YAML::Node sectors = built.document("ids.lock.yml")["sectors"];

            for (YAML::const_iterator sector = sectors.begin(); sectors.IsMap() && sector != sectors.end(); ++sector)
            {
                opened.sectorNames[sector->second.as<int>()] = sector->first.Scalar();
                opened.objectNames.sectors[sector->second.as<int>()] = sector->first.Scalar();
            }

            for (const std::pair<const char *, std::map<int, std::string> *> &list :
                 {std::pair<const char *, std::map<int, std::string> *>{"doors", &opened.objectNames.doors},
                     std::pair<const char *, std::map<int, std::string> *>{"events", &opened.objectNames.events}})
            {
                const YAML::Node entries = built.document("ids.lock.yml")[list.first];

                for (YAML::const_iterator entry = entries.begin(); entries.IsMap() && entry != entries.end(); ++entry)
                {
                    (*list.second)[entry->second.as<int>()] = entry->first.Scalar();
                }
            }

            const DressingFacts facts = projectDressingFacts(built);
            opened.hangingDecorations = facts.hanging;
            opened.storerooms = facts.storerooms;
            opened.trapDoors = facts.traps;
            opened.identityShape = facts.identityShape;
            opened.blindMouths = facts.blindMouths;
        }
    }

    AssetSession::setExtraMount(work / "mount");

    if (!session.open(assetRoot, world, errorMessage))
    {
        opened.failure = TargetFailure::NoAssetRoot;
        return false;
    }

    opened.failure = TargetFailure::None;
    return true;
}

// "sector 12", with the room's name where the target was a project (`names`: its rooms by sector number).
std::string sectorLabel(const std::map<int, std::string> &names, size_t sector)
{
    const std::map<int, std::string>::const_iterator name = names.find(static_cast<int>(sector));
    return "sector " + std::to_string(sector) + (name == names.end() ? "" : " (" + name->second + ")");
}

void writeWalkStops(JsonWriter &writer, const char *pKey, const std::vector<WalkStop> &stops)
{
    writer.key(pKey);
    writer.beginArray();

    for (const WalkStop &stop : stops)
    {
        writer.beginObject();
        writer.field("from_sector", static_cast<uint64_t>(stop.fromSector));
        writer.field("into_sector", static_cast<uint64_t>(stop.toSector));
        writer.field("face", stop.face);
        writer.key("at");
        writer.beginArray();
        writer.value(std::round(stop.at[0]));
        writer.value(std::round(stop.at[1]));
        writer.value(std::round(stop.at[2]));
        writer.endArray();
        writer.field("why", stop.reason);
        writer.endObject();
    }

    writer.endArray();
}

// Puts a reading request's mount in front for as long as the request runs (when it names one), and nothing after: a
// long-lived core must not read the next request through this one's mount or a project's preview mount.
class ReadMountScope
{
public:
    explicit ReadMountScope(const std::optional<std::filesystem::path> &mount)
        : m_active(mount.has_value())
    {
        if (m_active)
        {
            AssetSession::setExtraMount(*mount);
        }
    }

    ~ReadMountScope()
    {
        if (m_active)
        {
            AssetSession::setExtraMount({});
        }
    }

    ReadMountScope(const ReadMountScope &) = delete;
    ReadMountScope &operator=(const ReadMountScope &) = delete;

private:
    bool m_active = false;
};

// A message with the asset root's path replaced by "the asset root" (the request list's results name no paths).
std::string withoutAssetRoot(std::string message, const std::filesystem::path &assetRoot)
{
    const std::string root = assetRoot.string();

    for (size_t at = root.empty() ? std::string::npos : message.find(root); at != std::string::npos;
         at = message.find(root, at))
    {
        message.replace(at, root.size(), "the asset root");
    }

    return message;
}

// Opens and loads what a reading request names (openTarget, then loadMap), with the failure typed.
bool openRead(
    const ReadRequest &request, AssetSession &session, LoadedMap &map, OpenedTarget &opened, ReadFailure &failure)
{
    std::error_code error;
    const bool project = std::filesystem::is_regular_file(std::filesystem::path(request.target) / "project.yml", error);
    std::string world = request.world;
    std::string target = request.target;
    std::string errorMessage;

    if (!openTarget(session, request.assetRoot, world, target, opened, errorMessage))
    {
        failure.failure = project ? opened.failure : TargetFailure::Failed;
        failure.issues = opened.buildIssues;
        failure.badWorld = !project;
        failure.message = withoutAssetRoot(errorMessage, request.assetRoot);
        return false;
    }

    if (!loadMap(session, target, map, errorMessage))
    {
        failure.failure = TargetFailure::Failed;
        failure.noSuchMap = !project && errorMessage.find(" has no map ") != std::string::npos;
        failure.message = withoutAssetRoot(errorMessage, request.assetRoot);
        return false;
    }

    return true;
}

// What `oymap solve` found, for its text and its JSON (and check.audit's `solve`).
struct SolveOutcome
{
    std::string map;
    SolveResult solved;
    std::map<int, std::string> sectorRooms;
};

void writeSolveOutcome(JsonWriter &writer, const SolveOutcome &outcome);

// What `oymap audit` found, for its text and its JSON.
struct AuditOutcome
{
    std::string map;
    std::string world;
    MapOverview overview;
    CoplanarSummary coplanar;
    ReachabilityResult reach;
    std::vector<std::string> sceneOverlays;
    std::vector<std::string> scripts;
    std::vector<std::string> warnings;
    std::vector<AuditFinding> findings;
    size_t errors = 0;
    // The solve, when asked for (AuditRequest::solve) and the event flow was read: walked once, and the questions'
    // order taken from it.
    std::optional<SolveOutcome> solve;
};

// What the texture checks read of a map: the logical size of every texture its faces (and models' faces) lay, as the
// game resolves it, and the engine's and the world's texture_classes.yml.
TextureFitData textureFitDataOf(
    const AssetSession &session, const std::filesystem::path &assetRoot, const LoadedMap &map)
{
    TextureFitData data;
    Engine::DirectoryAssetPathCache directoryCache;
    Engine::AssetPathLookupCache pathCache;
    const auto add = [&](std::string name)
    {
        std::transform(name.begin(), name.end(), name.begin(),
            [](unsigned char character) { return static_cast<char>(std::tolower(character)); });

        if (name.empty() || data.sizes.contains(name))
        {
            return;
        }

        if (const std::optional<std::array<int, 2>> size =
                Engine::findSurfaceTextureLogicalSize(session.files(), name, directoryCache, pathCache))
        {
            data.sizes[name] = *size;
        }
    };

    if (map.indoor)
    {
        for (const Game::IndoorFace &face : map.indoor->faces)
        {
            add(face.textureName);
        }
    }

    if (map.outdoor)
    {
        for (const Game::OutdoorBModel &model : map.outdoor->bmodels)
        {
            for (const Game::OutdoorBModelFace &face : model.faces)
            {
                add(face.textureName);
            }
        }
    }

    for (const std::filesystem::path &folder : {assetRoot / "engine" / "models",
             assetRoot / "worlds" / map.world / "models"})
    {
        std::string text;

        if (readTextFile(folder / "texture_classes.yml", text))
        {
            data.classTexts.push_back(text);
        }
    }

    return data;
}

bool auditTarget(const AuditRequest &request, AuditOutcome &outcome, ReadFailure &failure)
{
    const ReadMountScope mountScope(request.read.mount);
    const std::filesystem::path &assetRoot = request.read.assetRoot;
    std::string originalName = request.original;
    std::string errorMessage;
    // The original's faces in one plane, read first (one asset root is open at a time).
    std::string originalWorld = request.read.world;
    std::error_code projectError;

    if (originalName.empty()
        && std::filesystem::is_regular_file(std::filesystem::path(request.read.target) / "project.yml", projectError))
    {
        const YAML::Node card = YAML::LoadFile((std::filesystem::path(request.read.target) / "project.yml").string());
        const YAML::Node stats = card["map_stats"];
        originalWorld = card["world"] ? card["world"].Scalar() : request.read.world;

        if (stats && stats.IsMap() && stats["reference"])
        {
            originalName = stats["reference"].Scalar();
        }
        else if (card["base"])
        {
            originalName = card["base"].Scalar();
        }
    }

    std::optional<std::vector<CoplanarPlace>> originalPlaces;

    if (!originalName.empty())
    {
        AssetSession originalSession;
        LoadedMap original;
        ReadRequest originalRequest = request.read;
        originalRequest.world = originalWorld;
        originalRequest.target = originalName;

        OpenedTarget originalOpened;

        if (!openRead(originalRequest, originalSession, original, originalOpened, failure))
        {
            failure.message = "the original " + originalName + ": " + failure.message;
            return false;
        }

        if (original.indoor)
        {
            const Game::MapDeltaData *pState = original.state ? &*original.state : nullptr;
            originalPlaces = coplanarPlaces(*original.indoor, findCoplanarFaces(*original.indoor, pState));
        }
        else if (original.outdoor)
        {
            originalPlaces = outdoorCoplanarPlaces(
                original.outdoor->bmodels, findOutdoorCoplanarFaces(original.outdoor->bmodels));
        }
    }

    AssetSession session;
    LoadedMap map;
    const std::filesystem::path given = request.read.target;
    const bool givenProject = std::filesystem::is_regular_file(given / "project.yml", projectError);

    OpenedTarget opened;

    if (!openRead(request.read, session, map, opened, failure))
    {
        return false;
    }

    // Outdoors, the part of each building face from the build's build.json (the project's preview build, or the
    // one beside a built map given by its path), for the coplanar messages.
    OutdoorFaceParts outdoorParts;

    if (map.outdoor)
    {
        const std::filesystem::path buildJson = givenProject ? opened.previewFolder / "build" / "build.json"
            : given.parent_path() / "build.json";

        if (std::filesystem::is_regular_file(buildJson, projectError))
        {
            const YAML::Node parts = YAML::LoadFile(buildJson.string())["face_parts"];

            for (const Game::OutdoorBModel &model : map.outdoor->bmodels)
            {
                std::vector<std::string> faces;
                const YAML::Node ranges = parts && parts.IsMap() ? parts[model.name] : YAML::Node();

                if (ranges && ranges.IsSequence())
                {
                    faces.assign(model.faces.size(), std::string());

                    for (size_t index = 0; index < ranges.size(); ++index)
                    {
                        const size_t from = ranges[index][0].as<size_t>();
                        const size_t to = index + 1 < ranges.size() ? ranges[index + 1][0].as<size_t>()
                            : model.faces.size();

                        for (size_t face = from; face < std::min(to, model.faces.size()); ++face)
                        {
                            faces[face] = ranges[index][1].as<std::string>();
                        }
                    }
                }

                outdoorParts.push_back(faces);
            }
        }
    }

    outcome.overview = overviewOf(map);
    std::vector<AuditFinding> &findings = outcome.findings;
    findings = auditWiring(map);
    CoplanarSummary &coplanar = outcome.coplanar;
    coplanar.original = originalPlaces ? originalName : std::string();
    const std::vector<AuditFinding> coplanarFindings = auditCoplanarFaces(
        map, originalPlaces ? &*originalPlaces : nullptr, request.strict, coplanar, opened.objectNames, outdoorParts);
    findings.insert(findings.end(), coplanarFindings.begin(), coplanarFindings.end());
    const std::vector<AuditFinding> eyeFindings = auditEyeSectors(map);
    findings.insert(findings.end(), eyeFindings.begin(), eyeFindings.end());
    // The engine's decoration rows and the world's own (its decorations range).
    std::string decorationTable;
    readWorldTable(assetRoot, map.world, "decoration_data.txt", "decorations", decorationTable);
    const std::vector<AuditFinding> lookFindings = auditLooks(map, decorationTable, opened.hangingDecorations);
    findings.insert(findings.end(), lookFindings.begin(), lookFindings.end());
    // The dressing rules hold for the worlds built to them (decision D-7.2: Xeen); other maps on request.
    if (request.dressing || map.world == "xeen")
    {
        // Outdoors, which cells are roads.
        std::vector<uint8_t> cellKinds;

        if (map.outdoor)
        {
            const std::optional<std::vector<Game::TerrainTileDescriptor>> tiles =
                Game::loadTerrainTileDescriptors(session.files(), *map.outdoor);

            if (tiles)
            {
                cellKinds = outdoorCellKinds(*map.outdoor, *tiles);
            }
        }

        const std::vector<AuditFinding> dressingFindings =
            auditDressing(map, decorationTable, opened.hangingDecorations, opened.storerooms, cellKinds);
        findings.insert(findings.end(), dressingFindings.begin(), dressingFindings.end());
    }

    // The light fixtures' mounts, as the dressing: Xeen's maps by default, others on request.
    if (map.indoor && (request.lights || request.lightsMeasure || map.world == "xeen"))
    {
        LightFixtureData lightData;
        lightData.decorationTableText = decorationTable;

        for (const std::filesystem::path &folder : {assetRoot / "engine" / "models",
                 assetRoot / "worlds" / map.world / "models"})
        {
            std::string text;

            if (readTextFile(folder / "indoor_decorations.yml", text))
            {
                lightData.bindingTexts.push_back(text);
            }

            if (readTextFile(folder / "light_fixtures.yml", text))
            {
                lightData.fixtureTexts.push_back(text);
            }
        }

        const std::vector<AuditFinding> lightFindings =
            auditLightFixtures(map, lightData, opened.hangingDecorations, request.lightsMeasure);
        findings.insert(findings.end(), lightFindings.begin(), lightFindings.end());
    }

    // The door leaves' pictures, as the lights.
    if (request.doors || request.doorsMeasure || map.world == "xeen")
    {
        const TextureFitData textureData = textureFitDataOf(session, assetRoot, map);
        const std::vector<AuditFinding> doorFindings = auditDoorTextures(map, textureData, request.doorsMeasure);
        findings.insert(findings.end(), doorFindings.begin(), doorFindings.end());
    }

    // The pictures' fit, as the doors.
    if (request.textures || request.texturesMeasure || map.world == "xeen")
    {
        const TextureFitData textureData = textureFitDataOf(session, assetRoot, map);
        const std::vector<AuditFinding> fitFindings = auditTextureFit(map, textureData, request.texturesMeasure);
        findings.insert(findings.end(), fitFindings.begin(), fitFindings.end());
    }
    ReachabilityResult &reach = outcome.reach;
    std::string flowJson;
    std::string flowError;
    const bool flowRead = exploreEventHandlers(map, flowJson, flowError);
    // The reach check's walks kept for the solve's (much of the map is walked by both).
    WalkSteps walkSteps;

    if (request.reach)
    {
        // With the handlers read, a barrier an event switches off (evt.SetFacetBit) is out of the way like a door.
        reach = checkReachability(map, flowRead ? flowJson : std::string(), &walkSteps);
    }
    else
    {
        reach.skipped = "not asked for (--reach)";
    }

    // The solve itself when asked for (one walk serves it and the questions' order).
    if (request.solve && flowRead && map.indoor && map.state)
    {
        SolveOutcome solved;
        solved.solved = solveMap(map, flowJson, &walkSteps);

        if (solved.solved.ran)
        {
            solved.map = map.fileName;

            if (givenProject)
            {
                solved.sectorRooms = opened.sectorNames;
            }

            outcome.solve = std::move(solved);
            const std::vector<AuditFinding> stranded = strandedFindings(
                outcome.solve->solved, givenProject ? opened.sectorNames : std::map<int, std::string>());
            findings.insert(findings.end(), stranded.begin(), stranded.end());
        }
    }

    // Questions whose answers the player must have met before (by the solve's order).
    const std::vector<AuditFinding> questionFindings = auditQuestions(
        map, flowRead ? flowJson : std::string("[]"), outcome.solve ? &outcome.solve->solved : nullptr);
    findings.insert(findings.end(), questionFindings.begin(), questionFindings.end());
    const std::vector<AuditFinding> silentFindings = auditSilentClicks(map, flowRead ? flowJson : std::string());
    findings.insert(findings.end(), silentFindings.begin(), silentFindings.end());

    // The standard entrance window into a dungeon (F16): the maps built to it (Xeen's), others on request.
    if (request.dressing || map.world == "xeen")
    {
        const std::vector<AuditFinding> entranceFindings = auditEntranceWindows(map);
        findings.insert(findings.end(), entranceFindings.begin(), entranceFindings.end());
        // What props and chests stand on and the chests' looks, as the dressing (they need what the things do).
        const std::vector<AuditFinding> supportFindings = auditPropSupport(
            map, decorationTable, flowRead ? flowJson : std::string(), opened.hangingDecorations);
        findings.insert(findings.end(), supportFindings.begin(), supportFindings.end());
        // How the chests stand and where (D-99).
        const std::vector<AuditFinding> chestFindings = auditChests(map);
        findings.insert(findings.end(), chestFindings.begin(), chestFindings.end());
    }

    // A cave or a mine shaped as one (D-89).
    const std::vector<AuditFinding> caveFindings = auditCaveShape(map, opened.identityShape);
    findings.insert(findings.end(), caveFindings.begin(), caveFindings.end());
    const std::vector<AuditFinding> voidFindings = auditVoid(map);
    findings.insert(findings.end(), voidFindings.begin(), voidFindings.end());
    const std::vector<AuditFinding> mouthFindings = auditBlindMouths(opened.blindMouths);
    findings.insert(findings.end(), mouthFindings.begin(), mouthFindings.end());
    const std::vector<AuditFinding> rideFindings =
        auditRides(map, flowRead ? flowJson : std::string(), opened.objectNames, opened.trapDoors);
    findings.insert(findings.end(), rideFindings.begin(), rideFindings.end());
    const std::vector<AuditFinding> reachFindings = reachabilityFindings(reach);
    findings.insert(findings.end(), reachFindings.begin(), reachFindings.end());

    if (flowRead)
    {
        const std::vector<AuditFinding> flowFindings = auditEventFlow(flowJson);
        findings.insert(findings.end(), flowFindings.begin(), flowFindings.end());
    }
    else
    {
        map.warnings.push_back(flowError);
    }

    for (const AuditFinding &finding : findings)
    {
        outcome.errors += finding.severity == "error" ? 1 : 0;
    }

    outcome.map = map.fileName;
    outcome.world = map.world;
    outcome.sceneOverlays = map.sceneOverlayPaths;
    outcome.scripts = map.scriptPaths;
    outcome.warnings = map.warnings;
    return true;
}

void writeAuditOutcome(JsonWriter &writer, const AuditOutcome &outcome)
{
    const MapOverview &overview = outcome.overview;
    const CoplanarSummary &coplanar = outcome.coplanar;
    const ReachabilityResult &reach = outcome.reach;
    writer.field("map", outcome.map);
    writer.field("world", outcome.world);
    writer.key("overview");
    writer.beginObject();
    writer.field("sectors", static_cast<uint64_t>(overview.sectors));
    writer.field("bmodels", static_cast<uint64_t>(overview.bmodels));
    writer.field("faces", static_cast<uint64_t>(overview.faces));
    writer.field("doors", static_cast<uint64_t>(overview.doors));
    writer.field("actors", static_cast<uint64_t>(overview.actors));
    writer.field("spawns", static_cast<uint64_t>(overview.spawns));
    writer.field("decorations", static_cast<uint64_t>(overview.decorations));
    writer.field("lights", static_cast<uint64_t>(overview.lights));
    writer.field("chests", static_cast<uint64_t>(overview.chests));
    writer.field("loot_containers", static_cast<uint64_t>(overview.containers));
    writer.field("handlers", static_cast<uint64_t>(overview.handlers));
    writer.field("bound_events", static_cast<uint64_t>(overview.boundEvents));
    writer.endObject();
    writer.key("coplanar");
    writer.beginObject();
    writer.field("pairs", static_cast<uint64_t>(coplanar.pairs));
    writer.field("as_original", static_cast<uint64_t>(coplanar.asOriginal));
    writer.field("new", static_cast<uint64_t>(coplanar.pairs - coplanar.asOriginal));
    writer.field("original", coplanar.original);
    writer.endObject();
    writer.key("reachability");
    writer.beginObject();
    writer.field("ran", reach.ran);

    if (reach.ran)
    {
        writer.field("sectors_with_floor", static_cast<uint64_t>(reach.sectorsWithFloor));
        writer.field("reached_at_start", static_cast<uint64_t>(reach.reachedAtStart));
        writer.field("reached_doors_open", static_cast<uint64_t>(reach.reachedDoorsOpen));
        writer.field("spawns", static_cast<uint64_t>(reach.spawnsTotal));
        writer.field("unreachable_spawns", static_cast<uint64_t>(reach.unreachableSpawns.size()));
        writer.key("unreached_sectors");
        writer.beginArray();

        for (const size_t sector : reach.unreachableSectors)
        {
            writer.value(static_cast<uint64_t>(sector));
        }

        writer.endArray();
        writeWalkStops(writer, "stopped_at", reach.stops);
    }
    else
    {
        writer.field("skipped", reach.skipped);
    }

    writer.endObject();

    for (const std::pair<const char *, const std::vector<std::string> *> &list :
         {std::pair<const char *, const std::vector<std::string> *>{"scene_overlays", &outcome.sceneOverlays},
             {"scripts", &outcome.scripts}, {"warnings", &outcome.warnings}})
    {
        writer.key(list.first);
        writer.beginArray();

        for (const std::string &text : *list.second)
        {
            writer.value(text);
        }

        writer.endArray();
    }

    writer.key("findings");
    writer.beginArray();

    for (const AuditFinding &finding : outcome.findings)
    {
        writer.beginObject();
        writer.field("code", finding.code);
        writer.field("severity", finding.severity);
        writer.field("message", finding.message);
        writer.field("hint", finding.hint);
        writer.endObject();
    }

    writer.endArray();

    if (outcome.solve)
    {
        writer.key("solve");
        writer.beginObject();
        writeSolveOutcome(writer, *outcome.solve);
        writer.endObject();
    }
}

// What `oymap solve` found, with the rooms of the sectors when the target was a project.
bool solveTarget(const ReadRequest &request, SolveOutcome &outcome, ReadFailure &failure)
{
    const ReadMountScope mountScope(request.mount);
    AssetSession session;
    LoadedMap map;
    std::string flowJson;
    std::string errorMessage;
    OpenedTarget opened;

    if (!openRead(request, session, map, opened, failure))
    {
        return false;
    }

    if (!exploreEventHandlers(map, flowJson, errorMessage))
    {
        failure.failure = TargetFailure::Failed;
        failure.message = withoutAssetRoot(errorMessage, request.assetRoot);
        return false;
    }

    outcome.solved = solveMap(map, flowJson);

    if (!outcome.solved.ran)
    {
        failure.failure = TargetFailure::Failed;
        failure.message = outcome.solved.skipped;
        return false;
    }

    outcome.map = map.fileName;
    // The rooms of the sectors: only for a project (the names openTarget keeps are the last project's).
    std::error_code error;

    if (std::filesystem::is_regular_file(std::filesystem::path(request.target) / "project.yml", error))
    {
        outcome.sectorRooms = opened.sectorNames;
    }

    return true;
}

void writeSolveOutcome(JsonWriter &writer, const SolveOutcome &outcome)
{
    const SolveResult &solved = outcome.solved;
    writer.field("map", outcome.map);
    writer.field("sectors_with_floor", static_cast<uint64_t>(solved.sectorsWithFloor));

    if (!outcome.sectorRooms.empty())
    {
        writer.key("sector_rooms");
        writer.beginObject();

        for (const std::pair<const int, std::string> &entry : outcome.sectorRooms)
        {
            writer.field(std::to_string(entry.first), entry.second);
        }

        writer.endObject();
    }

    writer.key("waves");
    writer.beginArray();

    for (const SolveWave &wave : solved.waves)
    {
        writer.beginObject();
        writer.key("sectors");
        writer.beginArray();

        for (const size_t sector : wave.sectors)
        {
            writer.value(static_cast<uint64_t>(sector));
        }

        writer.endArray();
        writer.key("opened_by");
        writer.beginArray();

        for (const std::string &cause : wave.causes)
        {
            writer.value(cause);
        }

        writer.endArray();
        writer.key("needs");
        writer.beginArray();

        for (const std::string &need : wave.needs)
        {
            writer.value(need);
        }

        writer.endArray();

        if (!wave.extended.empty())
        {
            writer.key("more_of");
            writer.beginArray();

            for (const std::pair<size_t, size_t> &entry : wave.extended)
            {
                writer.beginObject();
                writer.field("sector", static_cast<uint64_t>(entry.first));
                writer.field("cells", static_cast<uint64_t>(entry.second));
                writer.endObject();
            }

            writer.endArray();
        }

        writer.endObject();
    }

    writer.endArray();
    writer.key("never_reached");
    writer.beginArray();

    for (const size_t sector : solved.neverReached)
    {
        writer.value(static_cast<uint64_t>(sector));
    }

    writer.endArray();
    writer.field("niches_not_reached", static_cast<uint64_t>(solved.nichesNotReached.size()));
    writeWalkStops(writer, "stopped_at", solved.stops);
    writer.key("stranded");
    writer.beginArray();

    for (const SolveResult::Stranded &thing : solved.stranded)
    {
        writer.beginObject();
        writer.field("kind", thing.kind);
        writer.field("index", static_cast<uint64_t>(thing.index));

        if (!thing.name.empty())
        {
            writer.field("name", thing.name);
        }

        writer.key("at");
        writer.beginArray();

        for (const int coordinate : thing.at)
        {
            writer.value(static_cast<int64_t>(coordinate));
        }

        writer.endArray();
        writer.field("sector", static_cast<uint64_t>(thing.sector));
        writer.endObject();
    }

    writer.endArray();

    for (const std::pair<const char *, const std::vector<std::string> *> &list :
         {std::pair<const char *, const std::vector<std::string> *>{"issues", &solved.issues},
             {"waiting", &solved.waiting}, {"notes", &solved.notes}, {"exits", &solved.exits}})
    {
        writer.key(list.first);
        writer.beginArray();

        for (const std::string &text : *list.second)
        {
            writer.value(text);
        }

        writer.endArray();
    }
}

int reportIssues(const char *pCommand, bool asJson, const std::vector<ProjectIssue> &issues)
{
    if (asJson)
    {
        JsonWriter writer(true);
        writer.beginObject();
        writer.field("ok", !hasErrors(issues));
        writeIssuesJson(writer, issues);
        writer.endObject();
        std::cout << writer.text() << "\n";
    }
    else
    {
        printIssues(issues);

        if (issues.empty())
        {
            std::cout << pCommand << ": no issues\n";
        }
        else if (!hasErrors(issues))
        {
            std::cout << pCommand << ": no errors (" << issues.size() << " warnings or notes)\n";
        }
    }

    // Only errors fail: warnings and notes do not stop a build.
    return hasErrors(issues) ? 1 : 0;
}
}

int runValidate(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const bool asJson = takeFlag(arguments, "--json");
    BuildOptions options;
    options.assetRoot = takeAssetRoot(arguments, &options.mountRoot);

    if (arguments.size() != 1)
    {
        std::cerr << "usage: oymap validate <project> [--assets <asset root>] [--mount <folder>] [--json]\n";
        return 2;
    }

    Project project;
    std::vector<ProjectIssue> issues;
    loadProject(arguments[0], project, issues);

    if (issues.empty())
    {
        // With an asset root an outdoor project is also checked for what the build looks up there (one dry build).
        validateProject(project, options, issues);
    }

    // Said here, early: a world the asset root does not hold stops every command that reads the built map.
    if (const std::string note = missingWorldNote(project, options.assetRoot); !note.empty())
    {
        if (asJson)
        {
            JsonWriter writer(true);
            writer.beginObject();
            writer.field("ok", !hasErrors(issues));
            writeIssuesJson(writer, issues);
            writer.key("notes");
            writer.beginArray();
            writer.value(note);
            writer.endArray();
            writer.endObject();
            std::cout << writer.text() << "\n";
            return hasErrors(issues) ? 1 : 0;
        }

        std::cout << "note: " << note << "\n";
    }

    return reportIssues("oymap validate", asJson, issues);
}

int runBuild(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const bool asJson = takeFlag(arguments, "--json");
    BuildOptions options;
    options.dryRun = takeFlag(arguments, "--dry-run");
    options.assetRoot = takeAssetRoot(arguments, &options.mountRoot);
    std::string outputDirectory;

    if (takeOption(arguments, "--out", outputDirectory))
    {
        options.outputDirectory = outputDirectory;
    }

    if (arguments.size() != 1)
    {
        std::cerr << "usage: oymap build <project> [--out <dir>] [--assets <asset root>] [--mount <folder>] [--dry-run] "
                     "[--json]\n";
        return 2;
    }

    Project project;
    BuildResult result;
    loadProject(arguments[0], project, result.issues);
    const bool built = result.issues.empty() && buildProject(project, options, result);

    if (asJson)
    {
        JsonWriter writer(true);
        writer.beginObject();
        writer.field("ok", built);
        writer.field("map", result.mapFile);
        writer.key("counts");
        writer.beginObject();

        if (result.overlay)
        {
            writer.field("replaced_events", static_cast<uint64_t>(result.events));
        }
        else
        {
            writer.field("sectors", static_cast<uint64_t>(result.sectors));
            writer.field("faces", static_cast<uint64_t>(result.faces));
            writer.field("vertices", static_cast<uint64_t>(result.vertices));
            writer.field("portals", static_cast<uint64_t>(result.portals));
            writer.field("doors", static_cast<uint64_t>(result.doors));
            writer.field("lights", static_cast<uint64_t>(result.lights));
            writer.field("spawns", static_cast<uint64_t>(result.spawns));
            writer.field("entities", static_cast<uint64_t>(result.entities));
            writer.field("events", static_cast<uint64_t>(result.events));
            writer.field("chests", static_cast<uint64_t>(result.chests));
        }

        writer.endObject();
        writer.key("files");
        writer.beginArray();

        for (const std::string &file : result.files)
        {
            writer.value(file);
        }

        writer.endArray();
        writer.key("warnings");
        writer.beginArray();

        for (const std::string &warning : result.warnings)
        {
            writer.value(warning);
        }

        writer.endArray();
        writer.field("ids_lock_changed", result.lockChanged);
        writeIssuesJson(writer, result.issues);
        writer.endObject();
        std::cout << writer.text() << "\n";
        return built ? 0 : 1;
    }

    printIssues(result.issues);

    for (const std::string &warning : result.warnings)
    {
        std::cerr << "warning: " << warning << "\n";
    }

    if (!built)
    {
        return 1;
    }

    if (result.mapFile.ends_with(".odm"))
    {
        std::cout << (options.dryRun ? "would build " : "built ") << result.mapFile << ": outdoor terrain, "
                  << result.doors << " buildings (" << result.events << " doors with an event), "
                  << result.entities << " entities, " << result.spawns << " spawn points, "
                  << result.warnings.size() << " warnings\n";
        return 0;
    }

    if (result.sectors == 0)
    {
        std::cout << (options.dryRun ? "would build" : "built") << " an overlay of " << result.mapFile << ": "
                  << result.events << " events replaced";

        // A scene overlay (S6): what it adds, changes and removes of the base scene.
        if (!result.sceneOverlayKeys.empty())
        {
            std::cout << "; the scene: " << result.sceneAdded << " added, " << result.sceneChanged << " changed, "
                      << result.sceneRemoved << " removed";
        }

        // A cinematics overlay (S8a): the map's own replaced by name, and new ones.
        if (result.overlayCinematics)
        {
            std::cout << "; cinematics: " << result.cinematicsAdded << " added, " << result.cinematicsReplaced
                      << " replaced";
        }

        std::cout << "\n";
        return 0;
    }

    std::cout << (options.dryRun ? "would build " : "built ") << result.mapFile << ": " << result.sectors - 1
              << " rooms, " << result.faces << " faces, " << result.portals << " portals, " << result.doors
              << " doors, " << result.lights << " lights, " << result.spawns << " spawns, " << result.events
              << " events, " << result.chests << " chests\n";
    return 0;
}

int runInstall(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    std::string root;
    std::string buildDirectory;
    takeOption(arguments, "--build", buildDirectory);

    std::string mount;
    std::string assets;
    takeOption(arguments, "--mount", mount);
    takeOption(arguments, "--assets", assets);
    const bool hasRoot = takeOption(arguments, "--root", root);

    if (hasRoot == !mount.empty() || (!mount.empty() && assets.empty()) || arguments.size() != 1)
    {
        std::cerr << "usage: oymap install <project> --root <scratch asset root> [--build <dir>]\n"
                     "       oymap install <project> --mount <folder> --assets <asset root> [--build <dir>]\n"
                     "  --mount writes a folder for the game's --extra-mount: only the build's files, and for a new\n"
                     "  map a copy of the asset root's map_stats.txt with the map's row.\n";
        return 2;
    }

    Project project;
    std::vector<ProjectIssue> issues;

    if (!loadProject(arguments[0], project, issues) || !issues.empty())
    {
        printIssues(issues);
        return 1;
    }

    std::vector<std::string> installed;
    std::string errorMessage;

    const std::filesystem::path builtIn =
        buildDirectory.empty() ? project.root / "build" : std::filesystem::path(buildDirectory);

    if (!(mount.empty() ? installBuild(project, builtIn, root, installed, errorMessage)
            : installBuildIntoMount(project, builtIn, mount, assets, installed, errorMessage)))
    {
        std::cerr << "oymap install: " << errorMessage << "\n";
        return 1;
    }

    for (const std::string &file : installed)
    {
        std::cout << "installed " << file << "\n";
    }

    return 0;
}

bool writeAuditMembers(const AuditRequest &request, JsonWriter &writer, size_t &errors, ReadFailure &failure)
{
    AuditOutcome outcome;

    if (!auditTarget(request, outcome, failure))
    {
        return false;
    }

    writeAuditOutcome(writer, outcome);
    errors = outcome.errors;
    return true;
}

int runAudit(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const bool asJson = takeFlag(arguments, "--json");
    AuditRequest request;
    // Experimental (devdocs/map_studio/S1.md): right on maps built by oymap, not yet on every shipped map.
    request.reach = takeFlag(arguments, "--reach");
    // The lock-and-key solve too: monsters and spawn points it never reaches (reach.stranded).
    request.solve = takeFlag(arguments, "--solve");
    // Faces in one plane that the original does not have at the same place fail the audit.
    request.strict = takeFlag(arguments, "--strict");
    // The props' dressing rules on a map of any world (they hold by default for Xeen's).
    request.dressing = takeFlag(arguments, "--dressing");
    // The light fixtures' mounts on a map of any world (they hold by default for Xeen's); --lights-measure also prints
    // each fixture's numbers.
    request.lights = takeFlag(arguments, "--lights");
    request.lightsMeasure = takeFlag(arguments, "--lights-measure");
    // The door leaves' pictures likewise; --doors-measure also prints each leaf's numbers.
    request.doors = takeFlag(arguments, "--doors");
    request.doorsMeasure = takeFlag(arguments, "--doors-measure");
    // The pictures' fit likewise; --textures-measure also prints each surface's numbers and each pair of neighbours.
    request.textures = takeFlag(arguments, "--textures");
    request.texturesMeasure = takeFlag(arguments, "--textures-measure");
    takeOption(arguments, "--original", request.original);
    request.read.assetRoot = takeAssetRoot(arguments);

    if (!takeWorld(arguments, request.read.world) || arguments.size() != 1 || request.read.assetRoot.empty())
    {
        std::cerr << "usage: oymap audit <map file> --world <world> | <project> --assets <root> [--reach] [--solve] "
                     "[--json] [--original <map>] [--strict] [--dressing] [--lights] [--lights-measure] [--doors]\n"
                     "       [--doors-measure] [--textures] [--textures-measure]\n"
                     "  faces in one plane (geometry.coplanar) are matched against the original's at the same place:\n"
                     "  --original names it (a project's map_stats.reference or its base without it); --strict makes\n"
                     "  every pair the original does not have an error, so the audit exits 1; --dressing checks the\n"
                     "  props' dressing rules (devdocs/xeen/formats/DRESSING.md) on a map of any world, not only Xeen's;\n"
                     "  --lights the light fixtures' mounts (devdocs/xeen/formats/LIGHTS.md) likewise, --lights-measure\n"
                     "  with each fixture's numbers; --doors the door leaves' pictures (devdocs/xeen/formats/DOORS.md)\n"
                     "  likewise, --doors-measure with each leaf's numbers; --textures the pictures' fit\n"
                     "  (devdocs/xeen/formats/TEXTURE_FIT.md) likewise, --textures-measure with each surface's numbers\n";
        return 2;
    }

    request.read.target = arguments[0];
    AuditOutcome outcome;
    ReadFailure failure;

    if (!auditTarget(request, outcome, failure))
    {
        std::cerr << "oymap audit: " << failure.message << "\n";
        return 1;
    }

    if (asJson)
    {
        JsonWriter writer(true);
        writer.beginObject();
        writeAuditOutcome(writer, outcome);
        writer.endObject();
        std::cout << writer.text() << "\n";
        return outcome.errors == 0 ? 0 : 1;
    }

    const MapOverview &overview = outcome.overview;
    const CoplanarSummary &coplanar = outcome.coplanar;
    const ReachabilityResult &reach = outcome.reach;
    std::cout << outcome.map << " (" << outcome.world << "): " << overview.sectors << " sectors, " << overview.bmodels
              << " bmodels, " << overview.faces << " faces, " << overview.doors << " doors, " << overview.handlers
              << " handlers, " << overview.boundEvents << " bound events, " << outcome.sceneOverlays.size()
              << " scene overlays, " << outcome.scripts.size() << " scripts\n";
    std::cout << "faces in one plane: " << coplanar.pairs << " pairs, "
              << (coplanar.original.empty() ? std::string("no original to match")
                     : std::to_string(coplanar.asOriginal) + " as the original (" + coplanar.original + ")")
              << ", " << coplanar.pairs - coplanar.asOriginal << " new\n";

    if (reach.ran)
    {
        std::cout << "on foot from the party start: " << reach.reachedAtStart << " of " << reach.sectorsWithFloor
                  << " sectors with the doors as they start, " << reach.reachedDoorsOpen
                  << " with every door out of the way\n";
    }

    for (const std::string &warning : outcome.warnings)
    {
        std::cout << "warning: " << warning << "\n";
    }

    for (const AuditFinding &finding : outcome.findings)
    {
        std::cout << finding.severity << " " << finding.code << ": " << finding.message << "\n";
    }

    return outcome.errors == 0 ? 0 : 1;
}

int runProbe(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const bool doorsOpen = takeFlag(arguments, "--doors-open");
    const std::filesystem::path assetRoot = takeAssetRoot(arguments);
    std::string world;
    std::string fromText;
    std::string toText;
    const auto parsePoint = [](const std::string &text, std::array<float, 3> &point)
    {
        return std::sscanf(text.c_str(), "%f,%f,%f", &point[0], &point[1], &point[2]) == 3;
    };
    std::array<float, 3> from = {};
    std::array<float, 3> to = {};

    if (!takeWorld(arguments, world) || !takeOption(arguments, "--from", fromText)
        || !takeOption(arguments, "--to", toText) || arguments.size() != 1 || assetRoot.empty()
        || !parsePoint(fromText, from) || !parsePoint(toText, to))
    {
        std::cerr << "usage: oymap probe <map file> --world <world> | <project> --assets <root> --from x,y,z "
                     "--to x,y,z "
                     "[--doors-open]\n";
        return 2;
    }

    AssetSession session;
    LoadedMap map;
    std::string errorMessage;

    OpenedTarget opened;

    if (!openTarget(session, assetRoot, world, arguments[0], opened, errorMessage)
        || !loadMap(session, arguments[0], map, errorMessage))
    {
        std::cerr << "oymap probe: " << errorMessage << "\n";
        return 1;
    }

    std::cout << probeWalk(map, from, to, doorsOpen);
    return 0;
}

int runMetrics(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    MetricsOptions options;
    options.withReachability = takeFlag(arguments, "--reach");
    takeFlag(arguments, "--json");
    const std::filesystem::path assetRoot = takeAssetRoot(arguments);
    std::string world;
    std::string outputPath;
    takeOption(arguments, "--out", outputPath);

    if (!takeWorld(arguments, world) || arguments.size() != 1 || assetRoot.empty())
    {
        std::cerr << "usage: oymap metrics <map file> --world <world> | <project> --assets <root> [--reach] "
                     "[--out <file>]\n";
        return 2;
    }

    AssetSession session;
    LoadedMap map;
    std::string errorMessage;

    OpenedTarget opened;

    if (!openTarget(session, assetRoot, world, arguments[0], opened, errorMessage)
        || !loadMap(session, arguments[0], map, errorMessage))
    {
        std::cerr << "oymap metrics: " << errorMessage << "\n";
        return 1;
    }

    // (The decoration table says which decorations carry a light.)
    readTextFile(assetRoot / "engine" / "data_tables" / "decoration_data.txt", options.decorationTableText);
    JsonWriter writer(true);
    writeMetricsJson(map, options, writer);
    std::string text = writer.take();
    text.push_back('\n');

    if (outputPath.empty())
    {
        std::cout << text;
        return 0;
    }

    if (!writeTextFileAtomically(outputPath, text, errorMessage))
    {
        std::cerr << "oymap metrics: " << errorMessage << "\n";
        return 1;
    }

    return 0;
}

// Every interactive thing of an indoor map (core/Things.h): what it is, its textures, what it changes, where a
// player uses it from, and what overlaps it. A project's numbers are said by its ids (its ids.lock.yml).
int runThings(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const bool asJson = takeFlag(arguments, "--json");
    const std::filesystem::path assetRoot = takeAssetRoot(arguments);
    std::string world;

    if (!takeWorld(arguments, world) || arguments.size() != 1 || assetRoot.empty())
    {
        std::cerr << "usage: oymap things <map file> --world <world> | <project> --assets <root> [--json]\n";
        return 2;
    }

    CoplanarNames names;
    std::error_code fileError;
    const std::filesystem::path lockPath = std::filesystem::path(arguments[0]) / "ids.lock.yml";

    if (std::filesystem::is_regular_file(lockPath, fileError))
    {
        try
        {
            const YAML::Node lock = YAML::LoadFile(lockPath.string());

            for (const std::pair<const char *, std::map<int, std::string> *> &table :
                 {std::pair<const char *, std::map<int, std::string> *>{"sectors", &names.sectors},
                     {"doors", &names.doors}, {"events", &names.events}})
            {
                for (YAML::const_iterator entry = lock[table.first].begin(); entry != lock[table.first].end(); ++entry)
                {
                    (*table.second)[entry->second.as<int>()] = entry->first.as<std::string>();
                }
            }
        }
        catch (const YAML::Exception &)
        {
            names = {};
        }
    }

    AssetSession session;
    LoadedMap map;
    std::string errorMessage;

    OpenedTarget opened;

    if (!openTarget(session, assetRoot, world, arguments[0], opened, errorMessage)
        || !loadMap(session, arguments[0], map, errorMessage))
    {
        std::cerr << "oymap things: " << errorMessage << "\n";
        return 1;
    }

    if (!map.indoor && !map.outdoor)
    {
        std::cerr << "oymap things: " << map.fileName << " is neither an indoor nor an outdoor map\n";
        return 1;
    }

    std::string flowJson;
    std::string flowError;

    if (!exploreEventHandlers(map, flowJson, flowError))
    {
        flowJson.clear();
    }

    // Outdoors a thing's "sector" is the model holding most of its faces, named by the model's name.
    const std::vector<InteractiveThing> things = map.indoor ? listInteractiveThings(map, flowJson, names)
        : listOutdoorInteractiveThings(map, flowJson, names.sectors);
    const auto eventName = [&names](int eventId)
    {
        const std::map<int, std::string>::const_iterator name = names.events.find(eventId);
        return name != names.events.end() ? name->second : std::string();
    };

    if (asJson)
    {
        JsonWriter writer(true);
        writer.beginObject();
        writer.field("map", map.fileName);
        writer.field("world", map.world);
        writer.key("things");
        writer.beginArray();

        for (const InteractiveThing &thing : things)
        {
            writer.beginObject();
            writer.field("event", thing.eventId);
            writer.field("id", eventName(thing.eventId));
            writer.field("title", thing.title);
            // What the player reads on pointing at it; a clicked thing without it tells him nothing.
            writer.field("hover", thing.title);
            writer.field("no_hover", thing.title.empty());
            writer.field("kind", thing.kind);
            writer.field("sector", thing.sector);
            writer.field("room", names.sectors.contains(thing.sector) ? names.sectors.at(thing.sector) : std::string());
            writer.key("textures");
            writer.beginObject();

            for (const std::pair<const std::string, int> &texture : thing.textures)
            {
                writer.field(texture.first, texture.second);
            }

            writer.endObject();
            writer.key("faces");
            writer.beginArray();

            for (const uint32_t face : thing.faces)
            {
                writer.value(static_cast<uint64_t>(face));
            }

            writer.endArray();
            writer.key("own_doors");
            writer.beginArray();

            for (const uint32_t door : thing.ownDoors)
            {
                writer.value(static_cast<uint64_t>(door));
            }

            writer.endArray();

            for (const std::pair<const char *, const std::array<double, 3> *> &point :
                 {std::pair<const char *, const std::array<double, 3> *>{"low", &thing.low}, {"high", &thing.high},
                     {"middle", &thing.middle}, {"stand", &thing.stand}})
            {
                writer.key(point.first);
                writer.beginArray();

                for (const double value : *point.second)
                {
                    writer.value(static_cast<int64_t>(std::llround(value)));
                }

                writer.endArray();
            }

            writer.field("yaw", std::round(thing.yaw * 10000.0) / 10000.0);
            writer.field("pitch", std::round(thing.pitch * 10000.0) / 10000.0);
            writer.field("safe_to_use", thing.safeToUse);

            for (const std::pair<const char *, const std::vector<std::string> *> &list :
                 {std::pair<const char *, const std::vector<std::string> *>{"effects", &thing.effects},
                     {"changes", &thing.changes}, {"overlaps", &thing.overlaps}})
            {
                writer.key(list.first);
                writer.beginArray();

                for (const std::string &text : *list.second)
                {
                    writer.value(text);
                }

                writer.endArray();
            }

            writer.endObject();
        }

        writer.endArray();
        writer.endObject();
        std::cout << writer.take() << "\n";
        return 0;
    }

    size_t overlapping = 0;
    size_t unnamed = 0;

    for (const InteractiveThing &thing : things)
    {
        std::string textures;

        for (const std::pair<const std::string, int> &texture : thing.textures)
        {
            textures += (textures.empty() ? "" : ", ") + texture.first + " " + std::to_string(texture.second);
        }

        const std::string name = eventName(thing.eventId);
        std::cout << "event " << thing.eventId << (name.empty() ? "" : " " + name)
                  << " \"" << thing.title << "\" " << thing.kind << " in "
                  << (names.sectors.contains(thing.sector) ? names.sectors.at(thing.sector)
                         : "sector " + std::to_string(thing.sector))
                  << ": " << thing.faces.size() << " faces (" << textures << ") at [" << std::llround(thing.middle[0])
                  << ", " << std::llround(thing.middle[1]) << ", " << std::llround(thing.middle[2]) << "]; used from ["
                  << std::llround(thing.stand[0]) << ", " << std::llround(thing.stand[1]) << ", "
                  << std::llround(thing.stand[2]) << "]\n";

        for (const std::string &change : thing.changes)
        {
            std::cout << "  changes " << change << "\n";
        }

        for (const std::string &overlap : thing.overlaps)
        {
            std::cout << "  OVERLAP " << overlap << "\n";
        }

        if (thing.title.empty())
        {
            std::cout << "  NO HOVER NAME: pointing at it shows nothing\n";
        }

        overlapping += thing.overlaps.empty() ? 0 : 1;
        unnamed += thing.title.empty() ? 1 : 0;
    }

    std::cout << things.size() << " interactive things, " << overlapping << " with overlaps, " << unnamed
              << " without a hover name\n";
    return 0;
}

bool collectThings(
    const std::filesystem::path &projectRoot,
    const std::filesystem::path &assetRoot,
    ThingsReport &report,
    TargetFailure &failure,
    std::vector<ProjectIssue> &buildIssues,
    std::string &errorMessage)
{
    report = {};
    failure = TargetFailure::None;
    std::error_code fileError;

    if (!std::filesystem::is_regular_file(projectRoot / "project.yml", fileError))
    {
        failure = TargetFailure::NotAProject;
        errorMessage = "not a project folder (no project.yml)";
        return false;
    }

    AssetSession session;
    LoadedMap map;
    std::string world;
    std::string target = projectRoot.string();

    OpenedTarget opened;

    if (!openTarget(session, assetRoot, world, target, opened, errorMessage))
    {
        failure = opened.failure;
        buildIssues = opened.buildIssues;
        return false;
    }

    if (!loadMap(session, target, map, errorMessage) || (!map.indoor && !map.outdoor))
    {
        failure = TargetFailure::Failed;
        errorMessage = errorMessage.empty() ? map.fileName + " is neither an indoor nor an outdoor map" : errorMessage;
        return false;
    }

    std::string flowJson;
    std::string flowError;

    if (!exploreEventHandlers(map, flowJson, flowError))
    {
        flowJson.clear();
    }

    // The names of the build just made (its ids.lock.yml), so an id the files gained since the last build is named.
    report.names = opened.objectNames;
    report.map = map.fileName;
    report.world = map.world;
    report.things = map.indoor ? listInteractiveThings(map, flowJson, report.names)
        : listOutdoorInteractiveThings(map, flowJson, report.names.sectors);
    return true;
}

bool readEventFlow(const ReadRequest &request, std::string &mapFile, std::string &flowJson, ReadFailure &failure)
{
    const ReadMountScope mountScope(request.mount);
    AssetSession session;
    LoadedMap map;
    std::string errorMessage;
    OpenedTarget opened;

    if (!openRead(request, session, map, opened, failure))
    {
        return false;
    }

    if (!exploreEventHandlers(map, flowJson, errorMessage))
    {
        failure.failure = TargetFailure::Failed;
        failure.message = withoutAssetRoot(errorMessage, request.assetRoot);
        return false;
    }

    mapFile = map.fileName;
    return true;
}

int runFlow(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    takeFlag(arguments, "--json");
    ReadRequest request;
    request.assetRoot = takeAssetRoot(arguments);
    std::string eventText;
    const bool oneEvent = takeOption(arguments, "--event", eventText);

    if (!takeWorld(arguments, request.world) || arguments.size() != 1 || request.assetRoot.empty())
    {
        std::cerr << "usage: oymap flow <map file> --world <world> | <project> --assets <root> [--event <number>]\n";
        return 2;
    }

    request.target = arguments[0];
    std::string mapFile;
    std::string json;
    ReadFailure failure;

    if (!readEventFlow(request, mapFile, json, failure))
    {
        std::cerr << "oymap flow: " << failure.message << "\n";
        return 1;
    }

    if (!oneEvent)
    {
        std::cout << json << "\n";
        return 0;
    }

    // One event, readably.
    const YAML::Node events = YAML::Load(json);

    for (const YAML::Node &event : events)
    {
        if (event["event"].Scalar() != eventText)
        {
            continue;
        }

        std::cout << "event " << eventText << " \"" << event["title"].Scalar() << "\"\n";

        for (const YAML::Node &path : event["paths"])
        {
            std::cout << "  when";

            if (path["tests"].size() == 0)
            {
                std::cout << " always";
            }

            for (const YAML::Node &test : path["tests"])
            {
                std::cout << " [" << (test["taken"].Scalar() == "true" ? "" : "not ") << test["what"].Scalar() << "]";
            }

            std::cout << ":";

            for (const YAML::Node &effect : path["effects"])
            {
                std::cout << " " << effect.Scalar() << ";";
            }

            if (path["effects"].size() == 0 && !path["error"])
            {
                std::cout << " nothing";
            }

            if (path["error"])
            {
                std::cout << " (stopped: " << path["error"].Scalar() << ")";
            }

            std::cout << "\n";
        }

        return 0;
    }

    std::cerr << "oymap flow: the map has no handler for event " << eventText << "\n";
    return 1;
}

bool writeSolveMembers(const ReadRequest &request, JsonWriter &writer, ReadFailure &failure)
{
    SolveOutcome outcome;

    if (!solveTarget(request, outcome, failure))
    {
        return false;
    }

    writeSolveOutcome(writer, outcome);
    return true;
}

int runSolve(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const bool asJson = takeFlag(arguments, "--json");
    ReadRequest request;
    request.assetRoot = takeAssetRoot(arguments);

    if (!takeWorld(arguments, request.world) || arguments.size() != 1 || request.assetRoot.empty())
    {
        std::cerr << "usage: oymap solve <map file> --world <world> | <project> --assets <root> [--json]\n";
        return 2;
    }

    request.target = arguments[0];
    SolveOutcome outcome;
    ReadFailure failure;

    if (!solveTarget(request, outcome, failure))
    {
        std::cerr << "oymap solve: " << failure.message << "\n";
        return 1;
    }

    const SolveResult &solved = outcome.solved;

    if (asJson)
    {
        JsonWriter writer(true);
        writer.beginObject();
        writeSolveOutcome(writer, outcome);
        writer.endObject();
        std::cout << writer.text() << "\n";
        return 0;
    }

    size_t reached = 0;

    for (size_t index = 0; index < solved.waves.size(); ++index)
    {
        const SolveWave &wave = solved.waves[index];
        reached += wave.sectors.size();
        std::cout << "step " << index << ": " << wave.sectors.size() << " sectors (" << reached << " of "
                  << solved.sectorsWithFloor << ")";

        if (!wave.needs.empty())
        {
            std::cout << ", needs";

            for (const std::string &need : wave.needs)
            {
                std::cout << " [" << need << "]";
            }
        }

        // A gate across one room opens no new sector, only more of one.
        for (size_t extendedIndex = 0; extendedIndex < wave.extended.size(); ++extendedIndex)
        {
            std::cout << (extendedIndex == 0 ? "; more of sector " : ", ") << wave.extended[extendedIndex].first
                      << " (+" << wave.extended[extendedIndex].second << " cells)";
        }

        std::cout << "\n";

        for (size_t causeIndex = 0; causeIndex < wave.causes.size() && causeIndex < 6; ++causeIndex)
        {
            std::cout << "    " << wave.causes[causeIndex] << "\n";
        }

        if (wave.causes.size() > 6)
        {
            std::cout << "    and " << wave.causes.size() - 6 << " more\n";
        }
    }

    std::cout << "never reached: " << solved.neverReached.size() << " sectors";

    for (size_t index = 0; index < solved.neverReached.size() && index < 12; ++index)
    {
        std::cout << (index == 0 ? " (" : ", ") << solved.neverReached[index];
    }

    std::cout << (solved.neverReached.empty() ? "" : solved.neverReached.size() > 12 ? ", ...)" : ")");

    if (!solved.nichesNotReached.empty())
    {
        std::cout << ", and " << solved.nichesNotReached.size() << " niches too small or too low to stand in";
    }

    std::cout << "\n";

    for (size_t index = 0; index < solved.stops.size() && index < 12; ++index)
    {
        const WalkStop &stop = solved.stops[index];
        std::cout << "stopped at the opening from " << sectorLabel(outcome.sectorRooms, stop.fromSector) << " into "
                  << sectorLabel(outcome.sectorRooms, stop.toSector) << " at (" << std::lround(stop.at[0]) << ", "
                  << std::lround(stop.at[1]) << ", " << std::lround(stop.at[2]) << "), face " << stop.face << ": "
                  << stop.reason << "\n";
    }

    if (solved.stops.size() > 12)
    {
        std::cout << "and " << solved.stops.size() - 12 << " more openings (--json lists them)\n";
    }

    for (const std::string &issue : solved.issues)
    {
        std::cout << "issue: " << issue << "\n";
    }

    for (const SolveResult::Stranded &thing : solved.stranded)
    {
        std::cout << "stranded: " << thing.kind << " " << thing.index
                  << (thing.name.empty() ? "" : " (" + thing.name + ")") << " at (" << thing.at[0] << ", "
                  << thing.at[1] << ", " << thing.at[2] << ") in "
                  << sectorLabel(outcome.sectorRooms, thing.sector)
                  << ", never reached: the party cannot get to it, nor it out to the party\n";
    }

    for (size_t index = 0; index < solved.waiting.size() && index < 12; ++index)
    {
        std::cout << "waiting: " << solved.waiting[index] << "\n";
    }

    if (solved.waiting.size() > 12)
    {
        std::cout << "and " << solved.waiting.size() - 12 << " more branches waiting (--json lists them)\n";
    }

    for (const std::string &note : solved.notes)
    {
        std::cout << "note: " << note << "\n";
    }

    std::cout << "exits:";

    for (const std::string &exit : solved.exits)
    {
        std::cout << " " << exit;
    }

    std::cout << "\n";
    return 0;
}

// Reads each scene file, writes it through the core's YAML writer, and requires that the result says the same and
// that the game's scene parser accepts it (overlays are compared only: they parse against their base). The proof
// that the writer loses nothing of a shipped scene (PLAN.md section 11, "Round trips").
int runSceneRoundTrip(const std::vector<std::string> &arguments)
{
    if (arguments.empty())
    {
        std::cerr << "usage: oymap scene-roundtrip <scene.yml> [more files ...]\n";
        return 2;
    }

    size_t failed = 0;

    for (const std::string &argument : arguments)
    {
        std::string text;

        if (!readTextFile(argument, text))
        {
            std::cout << "FAILED " << argument << ": could not read\n";
            ++failed;
            continue;
        }

        try
        {
            const YAML::Node original = YAML::Load(text);
            const std::string written = writeCanonicalYaml(original);
            const YAML::Node reread = YAML::Load(written);
            std::string where;

            if (!sameYaml(original, reread, where))
            {
                std::cout << "FAILED " << argument << ": differs after writing at " << where << "\n";
                ++failed;
                continue;
            }

            if (writeCanonicalYaml(reread) != written)
            {
                std::cout << "FAILED " << argument << ": the written form is not stable\n";
                ++failed;
                continue;
            }

            const YAML::Node kind = reread.IsMap() ? reread["kind"] : YAML::Node(YAML::NodeType::Undefined);
            const std::string kindText = kind.IsDefined() ? kind.Scalar() : std::string();
            std::string sceneError;

            if (kindText == "indoor_scene"
                && (!Game::IndoorSceneYmlLoader().loadFromText(text, sceneError)
                    || !Game::IndoorSceneYmlLoader().loadFromText(written, sceneError)))
            {
                std::cout << "FAILED " << argument << ": the game's parser: " << sceneError << "\n";
                ++failed;
            }
            else if (kindText == "outdoor_scene"
                && (!Game::OutdoorSceneYmlLoader().loadFromText(text, sceneError)
                    || !Game::OutdoorSceneYmlLoader().loadFromText(written, sceneError)))
            {
                std::cout << "FAILED " << argument << ": the game's parser: " << sceneError << "\n";
                ++failed;
            }
        }
        catch (const YAML::Exception &exception)
        {
            std::cout << "FAILED " << argument << ": " << exception.what() << "\n";
            ++failed;
        }
    }

    std::cout << "round trip: " << arguments.size() - failed << " of " << arguments.size() << " scene files\n";
    return failed == 0 ? 0 : 1;
}

int runImport(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const std::filesystem::path assetRoot = takeAssetRoot(arguments);
    std::string world;
    std::string target;

    if (!takeWorld(arguments, world) || !takeOption(arguments, "--to", target) || arguments.size() != 1
        || assetRoot.empty())
    {
        std::cerr << "usage: oymap import <map file> --world <world> --assets <asset root> --to <project folder>\n";
        return 2;
    }

    AssetSession session;
    LoadedMap map;
    std::string errorMessage;
    std::vector<std::string> written;

    OpenedTarget opened;

    if (!openTarget(session, assetRoot, world, arguments[0], opened, errorMessage)
        || !loadMap(session, arguments[0], map, errorMessage)
        || !importMapAsProject(map, target, written, errorMessage))
    {
        std::cerr << "oymap import: " << errorMessage << "\n";
        return 1;
    }

    std::cout << "imported " << map.fileName << " into " << target << " (" << written.size() << " files)\n";
    return 0;
}

bool renderTargetPng(const RenderRequest &request, std::vector<uint8_t> &png, int &width, int &height,
    std::string &mapFile, ReadFailure &failure)
{
    const ReadMountScope mountScope(request.read.mount);
    PreviewOptions options;
    options.labels = request.labels;
    options.view = request.isometric ? PreviewView::Isometric : PreviewView::Plan;
    options.size = std::clamp(request.size, 128, 4096);
    AssetSession session;
    LoadedMap map;

    OpenedTarget opened;

    if (!openRead(request.read, session, map, opened, failure))
    {
        return false;
    }

    // An outdoor map's water, shore and roads are what its tiles say.
    if (map.outdoor)
    {
        const std::optional<std::vector<Game::TerrainTileDescriptor>> tiles =
            Game::loadTerrainTileDescriptors(session.files(), *map.outdoor);

        if (tiles)
        {
            options.cellKinds = outdoorCellKinds(*map.outdoor, *tiles);
        }
    }

    const Image image = renderPreview(map, options);
    png = encodePng(image);
    mapFile = map.fileName;
    width = image.width;
    height = image.height;
    return true;
}

int runRender(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    RenderRequest request;
    request.read.assetRoot = takeAssetRoot(arguments);
    request.labels = !takeFlag(arguments, "--no-labels");
    std::string output;
    std::string view;
    std::string size;

    if (takeOption(arguments, "--view", view))
    {
        request.isometric = view == "iso";
    }

    if (takeOption(arguments, "--size", size))
    {
        request.size = std::atoi(size.c_str());
    }

    if (!takeWorld(arguments, request.read.world) || !takeOption(arguments, "--out", output) || arguments.size() != 1
        || request.read.assetRoot.empty())
    {
        std::cerr << "usage: oymap render <map file> --world <world> | <project> --assets <root> --out <file.png> "
                     "[--view plan|iso] [--size <pixels>] [--no-labels]\n";
        return 2;
    }

    request.read.target = arguments[0];
    std::vector<uint8_t> png;
    int width = 0;
    int height = 0;
    std::string mapFile;
    ReadFailure failure;
    std::string errorMessage;

    if (!renderTargetPng(request, png, width, height, mapFile, failure))
    {
        std::cerr << "oymap render: " << failure.message << "\n";
        return 1;
    }

    if (!writeBinaryFileAtomically(output, png, errorMessage))
    {
        std::cerr << "oymap render: " << errorMessage << "\n";
        return 1;
    }

    std::cout << "wrote " << output << " (" << width << " x " << height << ")\n";
    return 0;
}

// The size of every texture an indoor map's faces name, as drawn (one texel a unit), by lower-case name.
void addTextureSizes(
    const AssetSession &session, const LoadedMap &map, std::map<std::string, std::array<int, 2>> &sizes)
{
    if (!map.indoor)
    {
        return;
    }

    Engine::DirectoryAssetPathCache directoryCache;
    Engine::AssetPathLookupCache pathCache;

    for (const Game::IndoorFace &face : map.indoor->faces)
    {
        std::string name = face.textureName;
        std::transform(name.begin(), name.end(), name.begin(),
            [](unsigned char character) { return static_cast<char>(std::tolower(character)); });

        if (name.empty() || sizes.contains(name))
        {
            continue;
        }

        const std::optional<std::array<int, 2>> size =
            Engine::findSurfaceTextureLogicalSize(session.files(), name, directoryCache, pathCache);

        if (size)
        {
            sizes[name] = *size;
        }
    }
}

// How alike two indoor maps in one coordinate frame are: the original and its rebuild (core/Compare).
int runCompare(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const bool asJson = takeFlag(arguments, "--json");
    const std::filesystem::path assetRoot = takeAssetRoot(arguments);
    std::string world;
    std::string with;
    std::string output;
    std::string stepText;
    CompareOptions options;
    std::string withoutText;
    takeOption(arguments, "--out", output);
    // A picture at another phase counts half in the score only when asked (the lead, eighth merge's follow-up).
    options.ignoreOffsets = !takeFlag(arguments, "--offsets");

    if (takeOption(arguments, "--step", stepText))
    {
        options.step = std::clamp(std::atof(stepText.c_str()), 32.0, 4096.0);
    }

    // Parts of the reading switched back to how it was before 2026-11-13, to see what each did to a score.
    bool knownWithout = true;
    bool outdoorRimByNodes = false;

    if (takeOption(arguments, "--without", withoutText))
    {
        std::istringstream names(withoutText);

        for (std::string name; std::getline(names, name, ',');)
        {
            if (name == "clear-points")
            {
                options.pointsOnGrid = true;
            }
            else if (name == "floor-edges")
            {
                options.exactFloorEdges = true;
            }
            else if (name == "seams")
            {
                options.openSeams = true;
            }
            else if (name == "blocks")
            {
                options.thinBlocksOnly = true;
            }
            else if (name == "load-events")
            {
                options.storedPoses = true;
            }
            else if (name == "offsets")
            {
                options.ignoreOffsets = true;
            }
            else if (name == "rim")
            {
                // Outdoor maps: the rim node by node, as before 2026-11-13 (core/OutdoorCompare).
                outdoorRimByNodes = true;
            }
            else
            {
                knownWithout = false;
            }
        }
    }

    if (!takeOption(arguments, "--with", with) || !takeWorld(arguments, world) || arguments.size() != 1
        || assetRoot.empty() || !knownWithout)
    {
        std::cerr << "usage: oymap compare <original map file> --world <world> --with <project | second map file> "
                     "--assets <root> [--out <folder>] [--step <units>] [--json] [--offsets] [--without <list>]\n"
                     "  --out writes report.json (totals, sectors, the 40 worst points), points.json (every point\n"
                     "  that differs, by sector, with all its differences), geometry.png, textures.png, shots.yml\n"
                     "  Both maps are read with every moving part as the party first sees it: the scene's starting\n"
                     "  state, then what the map's load events do on a first visit.\n"
                     "  --without clear-points,floor-edges,seams,blocks,load-events reads as before 2026-11-13:\n"
                     "  stand points exactly on their grid points; a floor's edge not part of the floor; a ray\n"
                     "  through a seam of two faces meeting nothing; only thin moving blocks kept clear of; moving\n"
                     "  parts as the scene stores them. For telling what each change did to a score, not for\n"
                     "  measuring. A ray on the same texture whose picture lies at another phase counts whole in the\n"
                     "  score; `offset_agreement` reports their share apart and `offsets` say what each rebuilt\n"
                     "  surface needs. --offsets counts such a ray half in the score as well.\n"
                     "  Two outdoor maps: --without rim judges the land beyond the playable square node by node with\n"
                     "  the rest, as before 2026-11-13 (its skyline is then reported with no weight).\n";
        return 2;
    }

    const std::chrono::steady_clock::time_point began = std::chrono::steady_clock::now();
    LoadedMap original;
    LoadedMap rebuilt;
    std::string errorMessage;
    std::string rebuiltWorld = world;

    // One asset root is open at a time: each map is read and its session closed before the next.
    {
        AssetSession session;

        OpenedTarget openedOriginal;

        if (!openTarget(session, assetRoot, world, arguments[0], openedOriginal, errorMessage)
            || !loadMap(session, arguments[0], original, errorMessage))
        {
            std::cerr << "oymap compare: " << errorMessage << "\n";
            return 1;
        }

        addTextureSizes(session, original, options.textureSizes);
    }

    {
        AssetSession session;

        OpenedTarget openedRebuilt;

        if (!openTarget(session, assetRoot, rebuiltWorld, with, openedRebuilt, errorMessage)
            || !loadMap(session, with, rebuilt, errorMessage))
        {
            std::cerr << "oymap compare: " << errorMessage << "\n";
            return 1;
        }

        addTextureSizes(session, rebuilt, options.textureSizes);
    }

    // Two outdoor maps are compared on the terrain's grid, layer by layer (core/OutdoorCompare).
    if (original.outdoor && rebuilt.outdoor)
    {
        return runOutdoorCompare(assetRoot, world, original, rebuilt, output, asJson, outdoorRimByNodes);
    }

    CompareResult result;

    if (!compareMaps(original, rebuilt, options, result, errorMessage))
    {
        std::cerr << "oymap compare: " << errorMessage << "\n";
        return 1;
    }

    JsonWriter writer(true);
    writeCompareJson(result, writer);
    std::string report = writer.take();
    report.push_back('\n');

    if (!output.empty())
    {
        const std::filesystem::path folder = output;
        std::error_code error;
        std::filesystem::create_directories(folder, error);
        // Green where every ray agrees, yellow at 70 %, red at 40 % and under; magenta where the rebuild has no
        // floor, blue where only the rebuild has one.
        const auto ramp = [](double share)
        {
            const double value = std::clamp(share, 0.0, 1.0);
            return std::array<uint8_t, 3>{static_cast<uint8_t>(value < 0.5 ? 230.0 : 230.0 * (1.0 - value) * 2.0),
                static_cast<uint8_t>(value < 0.5 ? 40.0 + 380.0 * value : 230.0 - 40.0 * (value - 0.5)), 40};
        };
        const std::vector<size_t> shots = compareShotPoints(result);
        const int radius = std::clamp(static_cast<int>(result.step / 64.0), 2, 5);

        for (const bool textures : {false, true})
        {
            std::vector<PlanMark> marks;

            for (const std::array<double, 3> &extra : result.extraFloor)
            {
                marks.push_back({extra[0], extra[1], extra[2], {70, 130, 255}, std::max(2, radius - 1), ""});
            }

            for (const ComparePoint &point : result.points)
            {
                marks.push_back({point.x, point.y, point.z,
                    !point.hasFloor ? std::array<uint8_t, 3>{255, 0, 255}
                        : ramp(((textures ? point.textureShare : point.distanceShare) - 0.4) / 0.6),
                    radius, ""});
            }

            // The shots of shots.yml, numbered as there.
            for (size_t index = 0; index < shots.size(); ++index)
            {
                const ComparePoint &point = result.points[shots[index]];
                marks.push_back({point.x, point.y, point.z, {255, 255, 255}, radius + 2, std::to_string(index + 1)});
            }

            const Image image = renderMarkedPlan(original, marks);

            if (!writeBinaryFileAtomically(
                    folder / (textures ? "textures.png" : "geometry.png"), encodePng(image), errorMessage))
            {
                std::cerr << "oymap compare: " << errorMessage << "\n";
                return 1;
            }
        }

        JsonWriter pointsWriter(true);
        writeComparePointsJson(result, pointsWriter);
        std::string points = pointsWriter.take();
        points.push_back('\n');

        if (!writeTextFileAtomically(folder / "report.json", report, errorMessage)
            || !writeTextFileAtomically(folder / "points.json", points, errorMessage)
            || !writeTextFileAtomically(folder / "shots.yml", compareShotsYaml(result), errorMessage))
        {
            std::cerr << "oymap compare: " << errorMessage << "\n";
            return 1;
        }
    }

    const double seconds =
        std::chrono::duration<double>(std::chrono::steady_clock::now() - began).count();

    if (asJson || output.empty())
    {
        std::cout << report;
    }
    else
    {
        std::cout << "compared " << result.originalName << " with " << result.rebuiltName << ": score "
                  << formatNumber(std::round(result.score * 1000.0) / 10.0) << " % over " << result.points.size()
                  << " points (" << result.missingFloor.size() << " without a floor in the rebuild, "
                  << result.extraFloor.size() << " of the rebuild's " << result.rebuiltPoints
                  << " without one in the original); distances agree on "
                  << formatNumber(std::round(result.distanceShare * 1000.0) / 10.0) << " % of " << result.rays
                  << " rays, textures on " << formatNumber(std::round(result.textureShare * 1000.0) / 10.0)
                  << " %\n"
                  << (result.verticalOffset == 0.0 ? std::string() : "the whole rebuild lies "
                      + formatNumber(std::fabs(result.verticalOffset))
                      + (result.verticalOffset > 0.0 ? " higher" : " lower") + " than the original\n")
                  << "wrote report.json, points.json, geometry.png, textures.png and shots.yml in " << output
                  << "\n";

        for (size_t index = 0; index < result.worst.size() && index < 5; ++index)
        {
            const ComparePoint &point = result.points[result.worst[index]];
            std::cout << "  (" << point.x << ", " << point.y << ", " << point.z << ") sector " << point.sector
                      << ", score " << formatNumber(std::round(point.score * 100.0)) << " %: " << point.sentence
                      << "\n";
        }
    }

    // The time goes to the error stream: the report is the same for the same maps.
    std::cerr << "oymap compare: " << formatNumber(std::round(seconds * 10.0) / 10.0) << " s\n";
    return 0;
}

namespace
{
// A share from 0 to 1 as a whole number of thousandths (the heat's scores: integers, the same on every backend).
int64_t permille(double share)
{
    return static_cast<int64_t>(std::llround(std::clamp(share, 0.0, 1.0) * 1000.0));
}

double roundedShare(double value, int decimals)
{
    const double scale = std::pow(10.0, decimals);
    return std::round(value * scale) / scale;
}

void writeAt(JsonWriter &writer, const std::string &name, double x, double y, double z)
{
    writer.key(name);
    writer.beginArray();
    writer.value(static_cast<int64_t>(std::llround(x)));
    writer.value(static_cast<int64_t>(std::llround(y)));
    writer.value(static_cast<int64_t>(std::llround(z)));
    writer.endArray();
}

void writePart(JsonWriter &writer, const std::string &id, const std::string &title, double weight, double score,
    const std::string &what)
{
    writer.beginObject();
    writer.field("id", id);
    writer.field("title", title);
    writer.field("weight", roundedShare(weight, 4));
    writer.field("score", roundedShare(score, 4));
    writer.field("what", what);
    writer.endObject();
}
}

bool writeCompareMembers(const CompareRequest &request, JsonWriter &writer, ReadFailure &failure)
{
    const ReadMountScope mountScope(request.read.mount);
    std::string originalName = request.original;
    std::string originalWorld = request.originalWorld.empty() ? request.read.world : request.originalWorld;
    std::error_code projectError;
    const std::filesystem::path given = request.read.target;
    const bool givenProject = std::filesystem::is_regular_file(given / "project.yml", projectError);

    // A project names its original (map_stats.reference, else the shipped map it overlays) and the world of both.
    if (givenProject)
    {
        const YAML::Node card = YAML::LoadFile((given / "project.yml").string());
        const YAML::Node stats = card["map_stats"];

        if (originalWorld.empty() && card["world"])
        {
            originalWorld = card["world"].Scalar();
        }

        if (originalName.empty() && stats && stats.IsMap() && stats["reference"])
        {
            originalName = stats["reference"].Scalar();
        }
        else if (originalName.empty() && card["base"])
        {
            originalName = card["base"].Scalar();
        }
    }

    if (originalName.empty())
    {
        failure.failure = TargetFailure::Failed;
        failure.badWorld = true;
        failure.message = "no original to compare with: the project has no map_stats.reference (a new map) and no "
                          "`original` was given";
        return false;
    }

    CompareOptions options;
    LoadedMap original;
    LoadedMap rebuilt;

    // One asset root is open at a time: each map is read and its session closed before the next.
    {
        AssetSession session;
        OpenedTarget opened;
        ReadRequest originalRequest = request.read;
        originalRequest.world = originalWorld;
        originalRequest.target = originalName;

        if (!openRead(originalRequest, session, original, opened, failure))
        {
            failure.message = "the original " + originalName + ": " + failure.message;
            return false;
        }

        addTextureSizes(session, original, options.textureSizes);
    }

    {
        AssetSession session;
        OpenedTarget opened;
        ReadRequest rebuiltRequest = request.read;

        if (rebuiltRequest.world.empty())
        {
            rebuiltRequest.world = originalWorld;
        }

        if (!openRead(rebuiltRequest, session, rebuilt, opened, failure))
        {
            return false;
        }

        addTextureSizes(session, rebuilt, options.textureSizes);
    }

    std::string errorMessage;

    if (original.outdoor && rebuilt.outdoor)
    {
        OutdoorCompareResult result;
        std::string warning;

        if (!compareLoadedOutdoorMaps(request.read.assetRoot, originalWorld, original, rebuilt, result, errorMessage,
                warning))
        {
            failure.failure = TargetFailure::Failed;
            failure.message = withoutAssetRoot(errorMessage, request.read.assetRoot);
            return false;
        }

        writer.field("kind", "outdoor");
        writer.field("original", result.originalName);
        writer.field("rebuilt", result.rebuiltName);
        writer.field("world", originalWorld);
        writer.field("score", roundedShare(result.score, 4));
        writer.key("band");
        writer.beginObject();
        writer.field("at_least", 0.9);
        writer.field("within", result.score >= 0.9);
        writer.endObject();
        writer.key("parts");
        writer.beginArray();

        for (const OutdoorComparePart &part : result.parts)
        {
            writePart(writer, part.id, part.title, part.weight, part.score, part.detail);
        }

        writer.endArray();
        writer.field("vertical_offset", static_cast<int64_t>(0));
        constexpr int RegionCells = 16;
        const double tile = Game::OutdoorMapData::TerrainTileSize;
        const int width = Game::OutdoorMapData::TerrainWidth;
        // The middle of a block of 16 x 16 cells, on the original's land.
        const auto middle = [&result, tile, width](const OutdoorCompareRegion &region)
        {
            const int gridX = region.column * RegionCells + RegionCells / 2;
            const int gridY = region.row * RegionCells + RegionCells / 2;
            const size_t node = static_cast<size_t>(gridY * width + gridX);
            const double z = node < result.originalHeights.size() ? result.originalHeights[node] : 0.0;
            return std::array<double, 3>{(gridX - 64) * tile, (64 - gridY) * tile, z};
        };
        writer.key("worst");
        writer.beginArray();

        for (size_t index = 0; index < result.worstRegions.size() && index < 12; ++index)
        {
            const OutdoorCompareRegion &region = result.regions[result.worstRegions[index]];
            const std::array<double, 3> at = middle(region);
            writer.beginObject();
            writer.field("name", region.name);
            writeAt(writer, "at", at[0], at[1], at[2]);
            writer.field("score", roundedShare(region.score, 4));
            writer.field("what", region.sentence);
            writer.endObject();
        }

        writer.endArray();
        writer.key("heat");
        writer.beginObject();
        writer.field("cell", static_cast<int64_t>(RegionCells * Game::OutdoorMapData::TerrainTileSize));
        writer.key("points");
        writer.beginArray();

        for (const OutdoorCompareRegion &region : result.regions)
        {
            const std::array<double, 3> at = middle(region);
            writer.beginArray();
            writer.value(static_cast<int64_t>(std::llround(at[0])));
            writer.value(static_cast<int64_t>(std::llround(at[1])));
            writer.value(permille(region.score));
            writer.endArray();
        }

        writer.endArray();
        writer.endObject();
        writer.key("floor_missing_in_rebuild");
        writer.beginArray();
        writer.endArray();
        writer.key("floor_only_in_rebuild");
        writer.beginArray();
        writer.endArray();
        writer.key("notes");
        writer.beginArray();

        if (!warning.empty())
        {
            writer.value(warning);
        }

        writer.endArray();
        JsonWriter report(false);
        writeOutdoorCompareJson(result, report);
        writer.key("report");
        writer.raw(report.text());
    }
    else if (original.indoor && rebuilt.indoor)
    {
        CompareResult result;

        if (!compareMaps(original, rebuilt, options, result, errorMessage))
        {
            failure.failure = TargetFailure::Failed;
            failure.message = withoutAssetRoot(errorMessage, request.read.assetRoot);
            return false;
        }

        writer.field("kind", "indoor");
        writer.field("original", result.originalName);
        writer.field("rebuilt", result.rebuiltName);
        writer.field("world", originalWorld);
        writer.field("score", roundedShare(result.score, 4));
        writer.key("band");
        writer.beginObject();
        writer.field("at_least", 0.97);
        writer.field("within", result.score >= 0.97);
        writer.endObject();
        writer.key("parts");
        writer.beginArray();
        writePart(writer, "shape", "shape: distances seen from every stand point", 0.7, result.distanceShare,
            "distances agree on " + formatNumber(roundedShare(result.distanceShare * 100.0, 1)) + " % of "
                + std::to_string(result.rays) + " rays");
        writePart(writer, "textures", "textures on the surfaces seen", 0.3, result.textureShare,
            "textures agree on " + formatNumber(roundedShare(result.textureShare * 100.0, 1)) + " % of the rays");
        const double offsetShare = result.sameTextureRays == 0 ? 1.0
            : 1.0 - static_cast<double>(result.offsetRays) / static_cast<double>(result.sameTextureRays);
        writePart(writer, "offsets", "texture offsets (reported, not scored)", 0.0, offsetShare,
            std::to_string(result.offsetRays) + " of " + std::to_string(result.sameTextureRays)
                + " rays on the same texture show it at another phase");
        writer.endArray();
        writer.field("vertical_offset", static_cast<int64_t>(std::llround(result.verticalOffset)));
        writer.key("worst");
        writer.beginArray();

        for (size_t index = 0; index < result.worst.size() && index < 40; ++index)
        {
            const ComparePoint &point = result.points[result.worst[index]];
            writer.beginObject();
            writer.field("name", "sector " + std::to_string(point.sector));
            writeAt(writer, "at", point.x, point.y, point.z);
            writer.field("score", roundedShare(point.score, 4));
            writer.field("what", point.sentence);
            writer.field("yaw_radians", roundedShare(point.worstYaw, 4));
            writer.endObject();
        }

        writer.endArray();
        writer.key("heat");
        writer.beginObject();
        writer.field("cell", static_cast<int64_t>(std::llround(result.step)));
        writer.key("points");
        writer.beginArray();

        for (const ComparePoint &point : result.points)
        {
            writer.beginArray();
            writer.value(static_cast<int64_t>(std::llround(point.x)));
            writer.value(static_cast<int64_t>(std::llround(point.y)));
            writer.value(point.hasFloor ? permille(point.score) : static_cast<int64_t>(-1));
            writer.endArray();
        }

        writer.endArray();
        writer.endObject();
        writer.key("floor_missing_in_rebuild");
        writer.beginArray();

        for (const size_t index : result.missingFloor)
        {
            const ComparePoint &point = result.points[index];
            writer.beginArray();
            writer.value(static_cast<int64_t>(std::llround(point.x)));
            writer.value(static_cast<int64_t>(std::llround(point.y)));
            writer.value(static_cast<int64_t>(std::llround(point.z)));
            writer.endArray();
        }

        writer.endArray();
        writer.key("floor_only_in_rebuild");
        writer.beginArray();

        for (const std::array<double, 3> &extra : result.extraFloor)
        {
            writer.beginArray();

            for (const double value : extra)
            {
                writer.value(static_cast<int64_t>(std::llround(value)));
            }

            writer.endArray();
        }

        writer.endArray();
        writer.key("notes");
        writer.beginArray();
        writer.endArray();
        JsonWriter report(false);
        writeCompareJson(result, report);
        writer.key("report");
        writer.raw(report.text());
    }
    else
    {
        failure.failure = TargetFailure::Failed;
        failure.badWorld = true;
        failure.message = "the original " + original.fileName + " and " + rebuilt.fileName
            + " are not both indoor or both outdoor maps";
        return false;
    }

    return true;
}

bool readShippedViewMesh(
    const ReadRequest &request, ViewMesh &mesh, std::string &kind, std::string &mapFile, ReadFailure &failure)
{
    const ReadMountScope mountScope(request.mount);
    AssetSession session;
    LoadedMap map;
    OpenedTarget opened;

    if (!openRead(request, session, map, opened, failure))
    {
        return false;
    }

    std::string liquidsText;
    readTextFile(request.assetRoot / "engine" / "liquids" / "liquids.yml", liquidsText);
    const LiquidTextures liquids = readLiquidTextures(liquidsText, map.world);
    mapFile = map.fileName;

    if (map.indoor)
    {
        kind = "indoor";
        mesh = shippedIndoorViewMesh(*map.indoor, liquids);
        return true;
    }

    if (!map.outdoor)
    {
        failure.failure = TargetFailure::Failed;
        failure.message = map.fileName + " is neither an indoor nor an outdoor map";
        return false;
    }

    // The land's tiles as the game resolves them, then the same mesh an outdoor project's view is drawn from.
    OutdoorView view;
    view.world = map.world;
    view.map = *map.outdoor;
    const std::optional<std::vector<Game::TerrainTileDescriptor>> tiles =
        Game::loadTerrainTileDescriptors(session.files(), *map.outdoor);

    if (tiles)
    {
        for (size_t tile = 0; tile < tiles->size() && tile < view.tileTextures.size(); ++tile)
        {
            std::string name = (*tiles)[tile].textureName;
            std::transform(name.begin(), name.end(), name.begin(),
                [](unsigned char character) { return static_cast<char>(std::tolower(character)); });
            view.tileTextures[tile] = name;
            view.tileWater[tile] = ((*tiles)[tile].flags & 0x0002u) != 0;
        }
    }

    kind = "outdoor";
    mesh = outdoorViewMesh(view, liquids);
    return true;
}

bool readMetricsJson(const ReadRequest &request, bool reach, std::string &json, std::string &mapFile,
    std::string &world, ReadFailure &failure)
{
    const ReadMountScope mountScope(request.mount);
    AssetSession session;
    LoadedMap map;
    OpenedTarget opened;

    if (!openRead(request, session, map, opened, failure))
    {
        return false;
    }

    MetricsOptions options;
    options.withReachability = reach;
    // (The decoration table says which decorations carry a light.)
    readTextFile(request.assetRoot / "engine" / "data_tables" / "decoration_data.txt", options.decorationTableText);
    JsonWriter writer(false);
    writeMetricsJson(map, options, writer);
    json = writer.take();
    mapFile = map.fileName;
    world = map.world;
    return true;
}

bool readProbeText(const ReadRequest &request, const std::array<float, 3> &from, const std::array<float, 3> &to,
    bool doorsOpen, std::string &text, std::string &mapFile, ReadFailure &failure)
{
    const ReadMountScope mountScope(request.mount);
    AssetSession session;
    LoadedMap map;
    OpenedTarget opened;

    if (!openRead(request, session, map, opened, failure))
    {
        return false;
    }

    if (!map.indoor)
    {
        failure.failure = TargetFailure::Failed;
        failure.badWorld = true;
        failure.message = "the probe walks indoor maps";
        return false;
    }

    text = probeWalk(map, from, to, doorsOpen);
    mapFile = map.fileName;
    return true;
}

bool importShippedMap(const ReadRequest &request, const std::filesystem::path &projectDirectory,
    std::vector<std::string> &written, std::string &mapFile, ReadFailure &failure)
{
    const ReadMountScope mountScope(request.mount);
    AssetSession session;
    LoadedMap map;
    OpenedTarget opened;
    std::error_code error;

    if (std::filesystem::is_regular_file(std::filesystem::path(request.target) / "project.yml", error))
    {
        failure.failure = TargetFailure::Failed;
        failure.badWorld = true;
        failure.message = "import takes a shipped map's file name and its world, not a project";
        return false;
    }

    if (std::filesystem::exists(projectDirectory / "project.yml", error))
    {
        failure.failure = TargetFailure::Failed;
        failure.badWorld = true;
        failure.message = "the folder holds a project already";
        return false;
    }

    if (!openRead(request, session, map, opened, failure))
    {
        return false;
    }

    std::string errorMessage;

    if (!importMapAsProject(map, projectDirectory, written, errorMessage))
    {
        failure.failure = TargetFailure::Failed;
        failure.message = withoutAssetRoot(errorMessage, request.assetRoot);
        return false;
    }

    mapFile = map.fileName;
    return true;
}

// The picture of an outdoor project's sketch.yml. It draws what can be read, so it also works on a sketch that
// `oymap validate` still has issues with.
int runRenderSketch(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    SketchPreviewOptions options;
    options.labels = !takeFlag(arguments, "--no-labels");
    std::string output;
    std::string size;

    if (takeOption(arguments, "--size", size))
    {
        options.size = std::clamp(std::atoi(size.c_str()), 256, 4096);
    }

    std::string region;
    bool regionReadable = true;

    if (takeOption(arguments, "--region", region))
    {
        // x,y,width,depth in cells.
        size_t index = 0;
        size_t position = 0;

        while (index < 4 && position <= region.size())
        {
            const size_t comma = std::min(region.find(',', position), region.size());
            options.region[index] = std::atof(region.substr(position, comma - position).c_str());
            position = comma + 1;
            ++index;
        }

        regionReadable = index == 4 && position > region.size() && options.region[2] > 0.0
            && options.region[3] > 0.0;
    }

    if (!takeOption(arguments, "--out", output) || arguments.size() != 1 || !regionReadable)
    {
        std::cerr << "usage: oymap render-sketch <project> --out <file.png> [--size <pixels>] "
                     "[--region <x,y,width,depth in cells>] [--no-labels]\n";
        return 2;
    }

    Project project;
    std::vector<ProjectIssue> issues;
    loadProject(arguments[0], project, issues);

    if (!project.has("sketch.yml"))
    {
        for (const ProjectIssue &issue : issues)
        {
            std::cerr << "oymap render-sketch: " << issue.file << (issue.file.empty() ? "" : ": ") << issue.message
                      << "\n";
        }

        std::cerr << "oymap render-sketch: " << arguments[0] << " has no readable sketch.yml\n";
        return 1;
    }

    const Image image = renderSketch(project, options);
    std::string errorMessage;

    if (!writeBinaryFileAtomically(output, encodePng(image), errorMessage))
    {
        std::cerr << "oymap render-sketch: " << errorMessage << "\n";
        return 1;
    }

    std::cout << "wrote " << output << " (" << image.width << " x " << image.height << ")\n";
    return 0;
}

// The editor's `--headless-build-map`, through the same EditorDocument compiled in place: load the map package,
// validate it, build it. Same inputs, same files written (the .odm or .blv, the .map.yml, and the map_stats and
// map_navigation rows in the asset root's editor folder).
int runBuildMap(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    std::string assetRoot;
    std::string world = "mm8";
    takeOption(arguments, "--asset-root", assetRoot);
    takeOption(arguments, "--world", world);

    if (arguments.size() != 1)
    {
        std::cerr << "usage: oymap build-map <map.yml-or-scene.yml> [--asset-root <dir>] [--world <id>]\n";
        return 2;
    }

    const std::filesystem::path root = assetRoot.empty()
        ? std::filesystem::path(OPENYAMM_DEV_ASSETS_DIR) : std::filesystem::absolute(assetRoot);
    Engine::AssetScaleProfile profile;
    // The editor builds against the x4 surface textures.
    profile.textures = Engine::AssetScaleTier::X4;
    Engine::AssetFileSystem assetFileSystem;

    if (!assetFileSystem.initialize(root.parent_path(), root, Engine::AssetScaleTier::X1, profile, world))
    {
        std::cerr << "Asset filesystem initialization failed.\n";
        return 1;
    }

    Editor::EditorDocument document;
    std::string errorMessage;

    if (!document.loadMapPhysicalPath(assetFileSystem, std::filesystem::absolute(arguments[0]), errorMessage))
    {
        std::cerr << "Map load failed: " << errorMessage << "\n";
        return 1;
    }

    const std::vector<std::string> issues = document.validate();

    if (!issues.empty())
    {
        for (const std::string &issue : issues)
        {
            std::cerr << "Map validation: " << issue << "\n";
        }

        return 1;
    }

    if (!document.buildRuntime(errorMessage))
    {
        std::cerr << "Map build failed: " << errorMessage << "\n";
        return 1;
    }

    std::cout << "Built native map: " << document.geometryPhysicalPath().string() << "\n";
    return 0;
}

namespace
{
void writeStrings(JsonWriter &writer, std::string_view name, const std::vector<std::string> &values)
{
    writer.key(name);
    writer.beginArray();

    for (const std::string &value : values)
    {
        writer.value(value);
    }

    writer.endArray();
}
}

int runEdit(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const bool asJson = takeFlag(arguments, "--json");
    TransactionOptions options;
    options.dryRun = takeFlag(arguments, "--dry-run");
    options.allowNewIssues = takeFlag(arguments, "--allow-issues");
    options.assetRoot = takeAssetRoot(arguments);
    takeOption(arguments, "--expect", options.expectRevision);
    takeOption(arguments, "--author", options.author);
    takeOption(arguments, "--label", options.label);
    takeOption(arguments, "--merge-key", options.mergeKey);
    options.rebase = takeFlag(arguments, "--rebase");
    std::string opsPath;

    if (!takeOption(arguments, "--ops", opsPath) || arguments.size() != 1)
    {
        std::cerr << "usage: oymap edit <project> --ops <file.json|file.yml|-> [--dry-run] [--expect <revision>] "
                     "[--rebase] [--allow-issues] [--assets <asset root>] [--author <user|agent:name>] "
                     "[--label <text>] [--merge-key <text>] [--json]\n"
                     "The file is a list of operations, applied as one transaction:\n"
                     "  {op: add, to: <collection>, value: {id: <kind>:<name>, ...}}   (or op: <singular>.add; without "
                     "an id the core gives one)\n"
                     "  {op: set, id: <id>, fields: {<key>: <value>, <key>: null}}     (null removes the field)\n"
                     "  {op: replace, id: <id>, value: {...}}                         (the whole object)\n"
                     "  {op: rename, from: <id>, to: <id>}                             (every reference, the lock and the "
                     "pins follow)\n"
                     "  {op: rename, id: <id>, path: /pillars/pillar2, to: <key>}      (a sub-object's key)\n"
                     "  {op: remove, id: <id>}\n"
                     "  set and remove take `file: <name>` too; it is needed when the id is in more than one file\n"
                     "  (ids are unique per file: a plan's space and its room share one in plan.yml and rooms.yml)\n"
                     "  {op: set_value, file: project.yml, path: map_stats.treasure_level, value: 2}\n"
                     "  {op: patch, id: <id>, patch: [{op: replace, path: /outline/2, value: [0, 512]}]}  (JSON Patch;\n"
                     "   a path segment into a keyed list is a key (/pillars/pillar2), into a list of maps with ids an "
                     "id;\n   `file: <name>` instead of `id` patches a file)\n"
                     "Collections: doors lights switches chests spawns decorations exits placeholders (objects.yml), "
                     "events (wiring.yml),\n  rooms openings themes (rooms.yml), spaces links entrances goals keys "
                     "points_of_interest landmarks set_pieces states\n  (plan.yml), neighbours (project.yml). Pins: "
                     "oymap pins. The lock: builds, oymap lock prune.\n";
        return 2;
    }

    std::string opsText;

    if (opsPath == "-")
    {
        opsText.assign(std::istreambuf_iterator<char>(std::cin), std::istreambuf_iterator<char>());
    }
    else if (!readTextFile(opsPath, opsText))
    {
        std::cerr << "oymap edit: could not read " << opsPath << "\n";
        return 1;
    }

    YAML::Node operations;

    try
    {
        operations = YAML::Load(opsText);
    }
    catch (const YAML::Exception &exception)
    {
        std::cerr << "oymap edit: the operations are not valid JSON or YAML: " << exception.what() << "\n";
        return 1;
    }

    // A single operation may be given without the list around it.
    if (operations.IsMap())
    {
        YAML::Node list(YAML::NodeType::Sequence);
        list.push_back(operations);
        operations.reset(list);
    }

    TransactionResult result;
    const bool ok = applyTransaction(arguments[0], operations, options, result);

    if (asJson)
    {
        JsonWriter writer(true);
        writer.beginObject();
        writer.field("ok", ok);
        writer.field("applied", result.applied);
        writer.field("dry_run", options.dryRun);
        writer.field("revision_before", result.revisionBefore);
        // The project's revision now: unchanged by a dry run or a refused change.
        writer.field("revision", result.applied ? result.revisionAfter : result.revisionBefore);

        if (!result.applied && !result.revisionAfter.empty() && result.revisionAfter != result.revisionBefore)
        {
            writer.field("revision_if_applied", result.revisionAfter);
        }

        writeStrings(writer, "changes", result.changes);
        writeStrings(writer, "errors", result.errors);
        writeStrings(writer, "outside_changes", result.outsideChanges);
        writeStrings(writer, "outside_notice", result.outsideNotice);
        writeStrings(writer, "ids_allocated", result.idsAllocated);
        writeStrings(writer, "notes", result.notes);
        writeStrings(writer, "hand_objects", result.handObjects);
        writer.field("hand_edited", result.mark.marked);
        writer.key("new_issues");
        writer.beginArray();

        for (const ProjectIssue &issue : result.newIssues)
        {
            writer.value(issue.file + (issue.path.empty() ? "" : ": " + issue.path) + ": " + issue.message);
        }

        writer.endArray();
        writer.field("fixed_issues", static_cast<uint64_t>(result.fixedIssues.size()));
        writer.endObject();
        std::cout << writer.text() << "\n";
        return ok ? 0 : 1;
    }

    for (const std::string &change : result.outsideChanges)
    {
        std::cout << "changed outside the tool since the last revision: " << change << "\n";
    }

    for (const std::string &line : result.outsideNotice)
    {
        std::cerr << "error: " << line << "\n";
    }

    if (result.mark.marked)
    {
        std::cerr << "note: " << HandEditedMessage << "\n";
    }

    for (const std::string &object : result.handObjects)
    {
        std::cerr << "note: a person changed " << object << " last\n";
    }

    for (const std::string &error : result.errors)
    {
        std::cerr << "error: " << error << "\n";
    }

    for (const std::string &note : result.notes)
    {
        std::cerr << "note: " << note << "\n";
    }

    for (const std::string &id : result.idsAllocated)
    {
        std::cout << "id given: " << id << "\n";
    }

    for (const ProjectIssue &issue : result.newIssues)
    {
        std::cerr << "new issue: " << issue.file << (issue.path.empty() ? "" : ": " + issue.path) << ": "
                  << issue.message << "\n";
    }

    for (const std::string &change : result.changes)
    {
        std::cout << (!ok ? "not changed: " : options.dryRun ? "would change: " : "changed: ") << change << "\n";
    }

    if (ok)
    {
        std::cout << "revision " << result.revisionBefore << " -> " << result.revisionAfter
                  << (result.fixedIssues.empty() ? "" : ", " + std::to_string(result.fixedIssues.size())
                          + " issue(s) fixed")
                  << (options.dryRun ? " (dry run, nothing written)" : "") << "\n";
    }

    return ok ? 0 : 1;
}

int runStatus(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const bool asJson = takeFlag(arguments, "--json");

    if (arguments.size() != 1)
    {
        std::cerr << "usage: oymap status <project> [--json]\n";
        return 2;
    }

    ProjectStatus status;
    std::string errorMessage;

    if (!projectStatus(arguments[0], status, errorMessage))
    {
        std::cerr << "oymap status: " << errorMessage << "\n";
        return 1;
    }

    if (asJson)
    {
        JsonWriter writer(true);
        writer.beginObject();
        writer.field("revision", status.revision);
        writer.field("lock_hash", status.lockHash);
        writeStrings(writer, "outside_changes", status.outsideChanges);
        writer.key("history");
        writer.beginArray();

        for (const HistoryEntry &entry : status.history)
        {
            writer.beginObject();
            writer.field("sequence", entry.sequence);
            writer.field("kind", entry.kind);
            writer.field("author", entry.author);

            if (!entry.label.empty())
            {
                writer.field("label", entry.label);
            }

            writer.field("revision_before", entry.revisionBefore);
            writer.field("revision", entry.revisionAfter);
            writer.field("undone", entry.undone);
            writeStrings(writer, "changes", entry.changes);
            writer.endObject();
        }

        writer.endArray();
        writer.endObject();
        std::cout << writer.text() << "\n";
        return 0;
    }

    std::cout << "revision " << status.revision << " (lock " << status.lockHash << ")\n";

    if (status.mark.marked)
    {
        std::cout << "edited by hand since " << status.mark.since << " (from revision " << status.mark.revision
                  << "): " << HandEditedMessage << "\n";
    }

    for (const std::string &line : status.outsideNotice)
    {
        std::cerr << "error: " << line << "\n";
    }

    for (const std::string &change : status.outsideChanges)
    {
        std::cout << "changed outside the tool since the last revision: " << change << "\n";
    }

    for (const HistoryEntry &entry : status.history)
    {
        std::cout << entry.sequence << (entry.undone ? " (undone) " : " ") << entry.kind
                  << (entry.reverts > 0 ? " (" + entry.revertKind + " of " + std::to_string(entry.reverts) + ")"
                      : std::string())
                  << (entry.author.empty() ? "" : " by " + entry.author)
                  << (entry.label.empty() ? "" : " \"" + entry.label + "\"") << " " << entry.revisionBefore << " -> "
                  << entry.revisionAfter << "\n";

        for (const std::string &change : entry.changes)
        {
            std::cout << "    " << change << "\n";
        }
    }

    return 0;
}

namespace
{
int runUndoRedo(const std::vector<std::string> &arguments, bool undo)
{
    if (arguments.size() != 1)
    {
        std::cerr << "usage: oymap " << (undo ? "undo" : "redo") << " <project>\n";
        return 2;
    }

    std::vector<std::string> changes;
    std::string errorMessage;

    if (!(undo ? undoProject(arguments[0], changes, errorMessage) : redoProject(arguments[0], changes, errorMessage)))
    {
        std::cerr << "oymap " << (undo ? "undo" : "redo") << ": " << errorMessage << "\n";
        return 1;
    }

    for (const std::string &change : changes)
    {
        std::cout << change << "\n";
    }

    return 0;
}
}

int runUndo(const std::vector<std::string> &arguments)
{
    return runUndoRedo(arguments, true);
}

int runRedo(const std::vector<std::string> &arguments)
{
    return runUndoRedo(arguments, false);
}

int runRevert(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    RevertRequest request;
    request.kind = RevertKind::Revert;
    request.force = takeFlag(arguments, "--force");
    TransactionOptions options;
    options.allowNewIssues = takeFlag(arguments, "--allow-issues");
    options.assetRoot = takeAssetRoot(arguments);
    options.author = "agent";
    takeOption(arguments, "--author", options.author);

    if (arguments.size() != 2 || arguments[1].empty()
        || !std::all_of(arguments[1].begin(), arguments[1].end(), [](char letter) { return letter >= '0' && letter <= '9'; }))
    {
        std::cerr << "usage: oymap revert <project> <sequence> [--force] [--allow-issues] [--author <a>]\n"
                     "Reverts one history entry (oymap status lists them) object by object: an object changed since "
                     "is left alone unless --force.\n";
        return 2;
    }

    request.sequence = std::stoi(arguments[1]);
    TransactionResult result;
    const bool ok = revertProject(arguments[0], request, options, result);

    for (const std::string &error : result.errors)
    {
        std::cerr << "oymap revert: " << error << "\n";
    }

    for (const std::string &change : result.changes)
    {
        std::cout << "reverted: " << change << "\n";
    }

    for (const std::string &conflict : result.conflicts)
    {
        std::cout << "left alone (changed since): " << conflict << "\n";
    }

    return ok ? 0 : 1;
}

int runProtect(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const bool clear = takeFlag(arguments, "--clear");

    if (arguments.size() != 1)
    {
        std::cerr << "usage: oymap protect <project> [--clear]\n"
                     "Marks the project as edited by hand (project.yml edited_by_hand), for a person who edits its "
                     "files in a text editor: agents then change it only by operations. --clear removes the mark (a "
                     "generator run then erases hand edits). For a person only: no agent or procedure runs it.\n";
        return 2;
    }

    TransactionResult result;

    if (!protectProject(arguments[0], clear, result))
    {
        std::cerr << "oymap protect: " << (result.errors.empty() ? std::string("refused") : result.errors.front())
                  << "\n";
        return 1;
    }

    std::cout << (result.mark.marked ? "protected: edited by hand since " + result.mark.since + " (from revision "
            + result.mark.revision + ")" : std::string("not protected")) << "\n";
    return 0;
}

int runMigrate(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const bool dryRun = takeFlag(arguments, "--dry-run");

    if (arguments.size() != 1)
    {
        std::cerr << "usage: oymap migrate <project> [--dry-run]\n"
                     "Writes every source file in canonical form with the keys of format 1, as one history entry.\n";
        return 2;
    }

    TransactionResult result;

    if (!migrateProject(arguments[0], dryRun, result))
    {
        std::cerr << "oymap migrate: " << (result.errors.empty() ? std::string("refused") : result.errors.front())
                  << "\n";
        return 1;
    }

    for (const std::pair<const std::string, std::string> &file : result.filesAfter)
    {
        std::cout << (dryRun ? "would write: " : "wrote: ") << file.first << "\n";
    }

    std::cout << result.keysAllocated.size() << " key(s) " << (dryRun ? "to write" : "written") << "\n";
    return 0;
}
}

namespace OpenYAMM::Studio
{
// oymap mod (devdocs/map_studio/S6_PLAN.md item M).
int runMod(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    std::string out;
    std::string assets;
    std::string mods;
    std::string layout = "merged";
    ModPackRequest request;
    takeOption(arguments, "--out", out);
    takeOption(arguments, "--assets", assets);
    takeOption(arguments, "--mods", mods);
    takeOption(arguments, "--layout", layout);
    takeOption(arguments, "--id", request.id);
    takeOption(arguments, "--name", request.name);
    takeOption(arguments, "--version", request.version);
    takeOption(arguments, "--author", request.author);
    takeOption(arguments, "--description", request.description);
    std::string maps;
    std::string world;
    std::string mod;
    takeOption(arguments, "--maps", maps);
    takeOption(arguments, "--world", world);
    takeOption(arguments, "--mod", mod);
    const std::vector<std::string>::iterator buildFlag = std::find(arguments.begin(), arguments.end(), "--build");

    if (buildFlag != arguments.end())
    {
        request.build = true;
        arguments.erase(buildFlag);
    }

    const std::string action = arguments.empty() ? std::string() : arguments.front();
    std::string errorMessage;

    // --maps <first>-<last>: the map numbers the mod declares (mod.yml idRanges.maps).
    if (!maps.empty())
    {
        const size_t dash = maps.find('-');

        try
        {
            request.mapRange = std::array<int, 2>{std::stoi(maps.substr(0, dash)),
                dash == std::string::npos ? 0 : std::stoi(maps.substr(dash + 1))};
        }
        catch (const std::exception &)
        {
            std::cerr << "oymap mod: --maps is <first>-<last>, as 9500-9599\n";
            return 2;
        }
    }

    if (action == "map-number" && !world.empty() && !assets.empty())
    {
        MapNumberRequest numberRequest;
        numberRequest.assetRoot = assets;
        numberRequest.world = world;
        numberRequest.modsRoot = mods;
        numberRequest.mod = mod;

        for (size_t index = 1; index < arguments.size(); ++index)
        {
            numberRequest.projects.push_back(arguments[index]);
        }

        MapNumberProposal proposal;

        if (!proposeMapNumber(numberRequest, proposal, errorMessage))
        {
            std::cerr << "oymap mod map-number: " << errorMessage << "\n";
            return 1;
        }

        std::cout << proposal.number << " (" << proposal.from << ", " << proposal.range[0] << " to "
                  << proposal.range[1] << ", " << proposal.taken.size() << " taken)\n";

        for (const std::string &warning : proposal.warnings)
        {
            std::cout << "warning: " << warning << "\n";
        }

        return 0;
    }

    if (action == "pack" && arguments.size() >= 2 && !out.empty() && !assets.empty())
    {
        request.out = out;
        request.assetRoot = assets;

        for (size_t index = 1; index < arguments.size(); ++index)
        {
            request.projects.push_back(arguments[index]);
        }

        ModPackResult result;

        if (!packMod(request, result, errorMessage))
        {
            std::cerr << "oymap mod pack: " << errorMessage << "\n";
            return 1;
        }

        for (const std::string &file : result.files)
        {
            std::cout << "packed " << file << "\n";
        }

        for (const std::string &warning : result.warnings)
        {
            std::cout << "warning: " << warning << "\n";
        }

        return 0;
    }

    if ((action == "install" || action == "enable" || action == "disable") && arguments.size() == 2 && !mods.empty()
        && (!assets.empty() || layout == "named"))
    {
        ModInstallResult result;
        const bool done = action == "install"
            ? installMod(arguments[1], mods, assets, layout, result, errorMessage)
            : setModEnabled(arguments[1], action == "enable", mods, assets, result, errorMessage);

        if (!done)
        {
            std::cerr << "oymap mod " << action << ": " << errorMessage << "\n";
            return 1;
        }

        for (const std::string &file : result.files)
        {
            std::cout << (action == "disable" ? "removed " : "installed ") << file << "\n";
        }

        for (const std::string &table : result.tables)
        {
            std::cout << "composed " << table << "\n";
        }

        for (const std::string &warning : result.warnings)
        {
            std::cout << "warning: " << warning << "\n";
        }

        return 0;
    }

    if (action == "list" && !mods.empty())
    {
        JsonWriter writer(true);
        writer.beginObject();
        writeModList(mods, writer);
        writer.endObject();
        std::cout << writer.take() << "\n";
        return 0;
    }

    std::cerr << "usage: oymap mod pack <project>... --id <mod> --out <folder> --assets <asset root> [--name <n>] "
                 "[--version <v>] [--author <a>] [--description <d>] [--maps <first>-<last>] [--build]\n"
                 "       oymap mod map-number --world <w> --assets <asset root> [--mods <mods folder>] [--mod <id>] "
                 "[<project>...]\n"
                 "       oymap mod install <mod folder> --mods <mods folder> --assets <asset root> "
                 "[--layout merged|named]\n"
                 "       oymap mod disable|enable <id> --mods <mods folder> --assets <asset root>\n"
                 "       oymap mod list --mods <mods folder>\n";
    return 2;
}
}
