#include "cli/Commands.h"

#include "core/CanonicalYaml.h"
#include "core/EventFlow.h"
#include "core/Json.h"
#include "core/MapLoad.h"
#include "core/Ops.h"
#include "core/OutdoorBuildings.h"
#include "core/Project.h"

#include "engine/ImageAssetLoader.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <filesystem>
#include <functional>
#include <iostream>
#include <map>
#include <set>
#include <sstream>

namespace OpenYAMM::Studio
{
namespace
{
std::string lowerText(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return text;
}
}

// Reads a project without changing it: its summary, one object by id, or one list.
int runQuery(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    std::string id;
    std::string list;
    takeFlag(arguments, "--json");
    takeOption(arguments, "--id", id);
    takeOption(arguments, "--list", list);

    if (arguments.size() != 1)
    {
        std::cerr << "usage: oymap query <project> [--id <id> | --list <key>]\n";
        return 2;
    }

    Project project;
    std::vector<ProjectIssue> issues;

    if (!loadProject(arguments[0], project, issues))
    {
        std::cerr << "oymap query: " << (issues.empty() ? "not a project" : issues.front().message) << "\n";
        return 1;
    }

    JsonWriter writer(true);
    writer.beginObject();
    writer.field("revision", projectRevision(project));

    if (!id.empty() || !list.empty())
    {
        bool found = false;

        for (const std::pair<const std::string, ProjectFile> &file : project.files)
        {
            const YAML::Node &root = file.second.document;

            // The lock's tables have the names of lists (events, doors); a list is the project's own.
            if (!root.IsMap() || (!list.empty() && file.first == "ids.lock.yml"))
            {
                continue;
            }

            for (YAML::const_iterator iterator = root.begin(); iterator != root.end(); ++iterator)
            {
                if (!list.empty() && iterator->first.Scalar() == list && !found)
                {
                    found = true;
                    writer.field("file", file.first);
                    writer.key(list);
                    writer.node(iterator->second);
                }

                if (id.empty() || !iterator->second.IsSequence())
                {
                    continue;
                }

                const YAML::Node list = iterator->second;

                for (const YAML::Node &item : list)
                {
                    if (item.IsMap() && item["id"] && item["id"].Scalar() == id)
                    {
                        found = true;
                        writer.field("file", file.first);
                        writer.field("list", iterator->first.Scalar());
                        writer.key("object");
                        writer.node(item);

                        // The engine number the build gave the id (the event number map_flow takes, a door's id).
                        if (project.has("ids.lock.yml"))
                        {
                            const YAML::Node lock = project.document("ids.lock.yml");

                            for (YAML::const_iterator table = lock.begin(); table != lock.end(); ++table)
                            {
                                const YAML::Node numbers = table->second;
                                const YAML::Node number = numbers.IsMap() ? numbers[id] : YAML::Node();

                                if (number.IsDefined() && number.IsScalar())
                                {
                                    writer.field("number", number.as<int>());
                                    writer.field("number_of", table->first.Scalar());
                                }
                            }
                        }
                    }
                }
            }
        }

        writer.endObject();

        if (!found)
        {
            std::cerr << "oymap query: nothing in the project is " << (id.empty() ? "a list named " + list : id)
                      << " (oymap query <project> lists every id)\n";
            return 1;
        }

        std::cout << writer.text() << "\n";
        return 0;
    }

    // The summary: the map card and, per file, each list with its ids.
    const YAML::Node card = project.document("project.yml");
    writer.key("card");
    writer.beginObject();

    for (const char *pKey : {"id", "name", "world", "kind", "profile", "base"})
    {
        if (card[pKey])
        {
            writer.field(pKey, card[pKey].Scalar());
        }
    }

    writer.endObject();
    writer.key("files");
    writer.beginObject();

    for (const std::pair<const std::string, ProjectFile> &file : project.files)
    {
        const YAML::Node &root = file.second.document;

        if (!root.IsMap() || file.first == "ids.lock.yml")
        {
            continue;
        }

        writer.key(file.first);
        writer.beginObject();

        for (YAML::const_iterator iterator = root.begin(); iterator != root.end(); ++iterator)
        {
            if (!iterator->second.IsSequence())
            {
                continue;
            }

            writer.key(iterator->first.Scalar());
            writer.beginArray();
            size_t shown = 0;
            const YAML::Node list = iterator->second;

            for (const YAML::Node &item : list)
            {
                if (item.IsMap() && item["id"] && shown++ < 60)
                {
                    writer.value(item["id"].Scalar());
                }
            }

            if (iterator->second.size() > 60)
            {
                writer.value("... " + std::to_string(iterator->second.size() - 60) + " more");
            }

            writer.endArray();
        }

        writer.endObject();
    }

    writer.endObject();
    writer.endObject();
    std::cout << writer.text() << "\n";
    return 0;
}

// The asset catalogue (PLAN.md section 2, `core/assets`), as far as S2 goes: decorations of the engine's table and
// the world's face textures with their sizes, searched by name.
bool writeAssetSearchMembers(
    const std::filesystem::path &assetRoot,
    const std::string &query,
    const std::string &world,
    const std::string &kind,
    size_t limit,
    JsonWriter &writer,
    std::string &errorMessage)
{
    // Every word of the query must be in the name or the hint.
    std::vector<std::string> wantedWords;
    std::istringstream wantedStream(lowerText(query));

    for (std::string word; wantedStream >> word;)
    {
        wantedWords.push_back(word);
    }

    const auto matches = [&wantedWords](const std::string &text)
    {
        const std::string lower = lowerText(text);
        return std::all_of(wantedWords.begin(), wantedWords.end(), [&lower](const std::string &word)
        {
            return lower.find(word) != std::string::npos;
        });
    };
    AssetSession session;

    if (!session.open(assetRoot, world, errorMessage))
    {
        return false;
    }

    size_t total = 0;

    if (kind.empty() || kind == "decoration")
    {
        writer.key("decorations");
        writer.beginArray();
        const std::optional<std::string> table = session.files().readTextFile("engine/data_tables/decoration_data.txt");
        // Which decorations a dungeon draws as a 3D model: the engine's indoor bindings and the world's own, by the
        // decoration's name; a binding with `maps` holds for those maps only, the others for every dungeon.
        std::map<std::string, std::string> indoorModels;

        for (const std::string &bindingFile :
             {std::string("engine/models/indoor_decorations.yml"), "worlds/" + world + "/models/indoor_decorations.yml"})
        {
            const std::optional<std::string> bindingText = session.files().readTextFile(bindingFile);

            if (!bindingText)
            {
                continue;
            }

            try
            {
                const YAML::Node bindings = YAML::Load(*bindingText)["decorations"];

                for (const YAML::Node &binding : bindings)
                {
                    const std::string name = lowerText(binding["name"] ? binding["name"].as<std::string>() : "");
                    std::string where = "every dungeon";

                    if (const YAML::Node maps = binding["maps"]; maps && maps.IsSequence())
                    {
                        where = "only on";

                        for (const YAML::Node &map : maps)
                        {
                            where += (where == "only on" ? " " : ", ") + map.as<std::string>();
                        }
                    }

                    std::string &known = indoorModels[name];
                    known = known.empty() || where == "every dungeon" ? where
                        : known == "every dungeon" ? known : known + "; " + where;
                }
            }
            catch (const YAML::Exception &)
            {
            }
        }

        std::istringstream lines(table.value_or(""));
        std::string line;
        size_t shown = 0;

        while (std::getline(lines, line))
        {
            std::vector<std::string> columns;
            std::istringstream row(line);
            std::string cell;

            while (std::getline(row, cell, '\t'))
            {
                columns.push_back(cell);
            }

            if (columns.size() < 7 || columns[0].empty() || !std::isdigit(static_cast<unsigned char>(columns[0][0]))
                || !matches(columns[1] + " " + columns[2]))
            {
                continue;
            }

            ++total;

            if (shown++ < limit)
            {
                writer.beginObject();
                writer.field("name", columns[1]);
                writer.field("hint", columns[2]);
                writer.field("number", std::stoi(columns[0]));
                writer.field("radius", std::atoi(columns[4].c_str()));
                writer.field("height", std::atoi(columns[5].c_str()));
                writer.field("light_radius", std::atoi(columns[6].c_str()));
                // In a dungeon: a 3D model on every map, on named maps only (a map built here is none of them:
                // the decoration is then drawn as its sprite), or no model at all.
                const std::map<std::string, std::string>::const_iterator model =
                    indoorModels.find(lowerText(columns[1]));
                writer.field("indoor_model", model == indoorModels.end() ? "none (drawn as its sprite)" : model->second);
                writer.endObject();
            }
        }

        writer.endArray();
    }

    if (kind.empty() || kind == "texture")
    {
        writer.key("textures");
        writer.beginArray();
        // The engine's name for the mounted worlds' face textures, cooked or not; one entry per texture name. Only
        // pictures: the folders also hold palettes and sub-folders.
        std::map<std::string, bool> names;
        // The game merges every world's texture folders by name, but a world may be installed without the others:
        // only the world's own textures and the engine's are listed, the ones `oymap build` accepts for it.
        const std::set<std::string> ownTextures = outdoorTextureNames(assetRoot, world);

        for (const std::string &entry : session.files().enumerate("Data/bitmaps"))
        {
            const size_t dot = entry.rfind('.');
            const std::string extension = dot == std::string::npos ? std::string() : lowerText(entry.substr(dot));

            if (extension != ".oytex" && extension != ".png" && extension != ".bmp" && extension != ".pcx")
            {
                continue;
            }

            const std::string name = lowerText(entry.substr(0, dot));

            if (matches(name) && (ownTextures.empty() || ownTextures.contains(name)))
            {
                names[name] = true;
            }
        }

        size_t shown = 0;

        // Liquids (engine/liquids/liquids.yml): a face texture of one of these names has no picture, the liquid
        // shader draws the face (water, lava, tar), so no texture folder holds it. Maps use them all the same.
        const std::optional<std::string> liquidsText = session.files().readTextFile("engine/liquids/liquids.yml");

        if (liquidsText)
        {
            const YAML::Node liquidsRoot = YAML::Load(*liquidsText);
            const YAML::Node liquids = liquidsRoot["liquids"];

            for (const YAML::Node &liquid : liquids)
            {
                const YAML::Node appliesTo = liquid["applies_to"];
                const YAML::Node worlds = liquid["worlds"];
                const YAML::Node match = liquid["match"];
                bool onFaces = false;
                bool inWorld = !worlds.IsDefined();

                for (const YAML::Node &target : appliesTo)
                {
                    onFaces = onFaces || target.Scalar() == "face";
                }

                for (const YAML::Node &liquidWorld : worlds)
                {
                    inWorld = inWorld || liquidWorld.Scalar() == world;
                }

                if (!onFaces || !inWorld || !match.IsMap())
                {
                    continue;
                }

                const YAML::Node textureNames = match["texture_names"];

                for (const YAML::Node &textureName : textureNames)
                {
                    const std::string name = lowerText(textureName.Scalar());

                    if (!matches(name) || names.contains(name))
                    {
                        continue;
                    }

                    ++total;

                    if (shown++ >= limit)
                    {
                        continue;
                    }

                    writer.beginObject();
                    writer.field("name", name);
                    writer.field("liquid", liquid["kind"].Scalar());
                    writer.field("liquid_id", liquid["id"].Scalar());
                    writer.field("note", "drawn by the liquid shader: it has no picture and no size, and a face "
                        "that names it is that liquid");
                    writer.field("usable_on_faces", name.size() <= 10);
                    writer.endObject();
                }
            }
        }

        Engine::DirectoryAssetPathCache directoryCache;
        Engine::AssetPathLookupCache pathCache;

        for (const std::pair<const std::string, bool> &entry : names)
        {
            ++total;

            if (shown++ >= limit)
            {
                continue;
            }

            writer.beginObject();
            writer.field("name", entry.first);
            const std::optional<std::array<int, 2>> size =
                Engine::findSurfaceTextureLogicalSize(session.files(), entry.first, directoryCache, pathCache);

            // In the units a face is drawn in (one texel a unit), whatever the tier of the file read.
            if (size)
            {
                writer.field("width", (*size)[0]);
                writer.field("height", (*size)[1]);
                writer.key("size");
                writer.beginArray();
                writer.value((*size)[0]);
                writer.value((*size)[1]);
                writer.endArray();
            }
            else
            {
                writer.field("note", "the picture's size could not be read from its file");
            }

            // A face texture's name must fit the BLV's ten characters.
            writer.field("usable_on_faces", entry.first.size() <= 10);
            writer.endObject();
        }

        writer.endArray();
    }

    // The rows of an engine table whose number column is a number and whose name matches, with the columns wanted
    // (S5b1: the Library's monsters and items, which the Monster and Item tools place by number).
    const auto tableRows = [&session, &matches](const char *pTable, size_t nameColumn,
        const std::function<void(const std::vector<std::string> &)> &take)
    {
        const std::optional<std::string> text = session.files().readTextFile(std::string("engine/data_tables/") + pTable);
        std::istringstream lines(text.value_or(""));

        for (std::string line; std::getline(lines, line);)
        {
            if (!line.empty() && line.back() == '\r')
            {
                line.pop_back();
            }

            std::vector<std::string> columns;
            std::istringstream row(line);

            for (std::string cell; std::getline(row, cell, '\t');)
            {
                columns.push_back(cell);
            }

            if (columns.size() <= nameColumn || columns[0].empty()
                || !std::all_of(columns[0].begin(), columns[0].end(), [](unsigned char c) { return std::isdigit(c); })
                || columns[0] == "0" || columns[nameColumn].empty() || !matches(columns[nameColumn]))
            {
                continue;
            }

            take(columns);
        }
    };
    const auto number = [](const std::string &text)
    {
        return std::atoi(text.c_str());
    };

    if (kind == "monster")
    {
        writer.key("monsters");
        writer.beginArray();
        size_t shown = 0;
        tableRows("monster_data.txt", 1, [&](const std::vector<std::string> &columns)
        {
            ++total;

            if (shown++ < limit)
            {
                writer.beginObject();
                writer.field("number", number(columns[0]));
                writer.field("name", columns[1]);
                writer.field("picture", columns.size() > 2 ? columns[2] : std::string());
                writer.field("level", columns.size() > 3 ? number(columns[3]) : 0);
                writer.field("hp", columns.size() > 4 ? number(columns[4]) : 0);
                writer.endObject();
            }
        });
        writer.endArray();
    }

    if (kind == "item")
    {
        writer.key("items");
        writer.beginArray();
        size_t shown = 0;
        tableRows("items.txt", 2, [&](const std::vector<std::string> &columns)
        {
            ++total;

            if (shown++ < limit)
            {
                writer.beginObject();
                writer.field("number", number(columns[0]));
                writer.field("name", columns[2]);
                writer.field("picture", columns[1]);
                writer.field("value", columns.size() > 3 ? number(columns[3]) : 0);
                writer.field("kind", columns.size() > 4 ? columns[4] : std::string());
                writer.endObject();
            }
        });
        writer.endArray();
    }

    if (kind == "sound")
    {
        // The world's own sounds: a placed sound names a file of worlds/<world>/audio (the lowering looks for it
        // there, with or without .wav).
        writer.key("sounds");
        writer.beginArray();
        std::vector<std::string> files;
        std::error_code error;

        for (std::filesystem::directory_iterator file(assetRoot / "worlds" / world / "audio", error), end;
             !error && file != end; file.increment(error))
        {
            const std::string name = file->path().filename().string();

            if (file->is_regular_file(error) && lowerText(file->path().extension().string()) == ".wav"
                && matches(name))
            {
                files.push_back(name);
            }
        }

        std::sort(files.begin(), files.end());
        size_t shown = 0;

        for (const std::string &name : files)
        {
            ++total;

            if (shown++ < limit)
            {
                writer.beginObject();
                writer.field("name", name.substr(0, name.size() - 4));
                writer.field("file", "worlds/" + world + "/audio/" + name);
                writer.endObject();
            }
        }

        writer.endArray();
    }

    writer.field("matches", static_cast<uint64_t>(total));
    return true;
}

int runAssets(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    const std::filesystem::path assetRoot = takeAssetRoot(arguments);
    std::string world = "mm6";
    std::string kind;
    std::string limitText;
    takeFlag(arguments, "--json");
    takeOption(arguments, "--world", world);
    takeOption(arguments, "--kind", kind);
    const size_t limit = takeOption(arguments, "--limit", limitText) ? std::stoul(limitText) : 40;

    if (arguments.size() != 1 || assetRoot.empty() || (!kind.empty() && kind != "decoration" && kind != "texture"
        && kind != "monster" && kind != "item" && kind != "sound"))
    {
        std::cerr << "usage: oymap assets <text in the name> --assets <asset root> [--world <world>] "
                     "[--kind decoration|texture|monster|item|sound] [--limit <n>]\n";
        return 2;
    }

    JsonWriter writer(true);
    writer.beginObject();
    std::string errorMessage;

    if (!writeAssetSearchMembers(assetRoot, arguments[0], world, kind, limit, writer, errorMessage))
    {
        std::cerr << "oymap assets: " << errorMessage << "\n";
        return 1;
    }

    writer.endObject();
    std::cout << writer.text() << "\n";
    return 0;
}

std::vector<std::string> eventFunctionNames()
{
    std::istringstream names(EventFunctionNames);
    std::vector<std::string> sorted;

    for (std::string name; names >> name;)
    {
        // Names with an underscore in front are the generated scripts' own plumbing.
        if (name[0] != '_')
        {
            sorted.push_back(name);
        }
    }

    std::sort(sorted.begin(), sorted.end());
    return sorted;
}

int runEventFunctions(const std::vector<std::string> &)
{
    for (const std::string &name : eventFunctionNames())
    {
        std::cout << name << "\n";
    }

    return 0;
}

int runScriptReference(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    std::string world = "mm6";
    takeOption(arguments, "--world", world);
    const std::filesystem::path assetRoot = takeAssetRoot(arguments);

    if (!arguments.empty() || assetRoot.empty())
    {
        std::cerr << "usage: oymap script-reference --assets <asset root> [--world <world>]\n";
        return 2;
    }

    AssetSession session;
    std::string errorMessage;
    std::string text;

    if (!session.open(assetRoot, world, errorMessage)
        || !scriptReference(loadScriptSupport(session), text, errorMessage))
    {
        std::cerr << "oymap script-reference: " << errorMessage << "\n";
        return 1;
    }

    std::cout << text << "\n";
    return 0;
}

const char *const NewProjectNext =
    "First edit: rooms, the openings between them and the start together ({op: set_value, file: objects.yml, path: "
    "start, value: {room: <id>}}), since a map without a start does not validate. Then lights, doors, switches and "
    "chests (objects.yml), then events (wiring.yml).";

const char *const NewOutdoorProjectNext =
    "The land is level spot heights (heights.grid, 16 cells apart): raise and lower them, draw water, roads and "
    "structures in sketch.yml; the party arrives at the point entrance:start in the middle.";

bool createEmptyProject(
    const NewProjectRequest &request, std::vector<std::string> &written, bool &exists, std::string &errorMessage)
{
    const std::filesystem::path &root = request.root;
    std::error_code error;
    exists = std::filesystem::exists(root / "project.yml", error);

    if (exists)
    {
        errorMessage = "the folder already holds a project";
        return false;
    }

    if (request.kind == "outdoor")
    {
        // A new outdoor map: level land of spot heights (a 16-cell grid at 256) the grid editor and the brushes work
        // on, one plan space and its arrival point in the middle. The card's own columns stand in for a reference row.
        const std::string card = "format: 0\nid: " + request.id + "\nname: " + jsonQuote(request.name) + "\nworld: "
            + request.world + "\nkind: outdoor\nprofile: odm\nmap_stats:\n  id: "
            + (request.statsId.empty() ? std::string("9600") : request.statsId)
            + "\n  encounter_chance: 10\n  treasure_level: 1\n  trap_dice: 1\n  perception_difficulty: 1\n"
              "  refill_days: 672\n  music: 19\n  environment: plains\n  lock_difficulty: 0\n"
              "  slots:\n    - {monster: Goblin, tier: 1, per_marker: [2, 4], weight: 100}\n";
        const std::string plan = "format: 0\nspaces:\n  - {id: zone:land, kind: zone}\nentrances:\n"
            "  - {id: entrance:start, kind: arrival, space: zone:land, facing: s}\n";
        std::string grid = "    rows:\n";

        for (int row = 0; row < 8; ++row)
        {
            grid += "      - [4, 4, 4, 4, 4, 4, 4, 4]\n";
        }

        const std::string sketch = "format: 1\ngrid: 512\nmap_cells: 128\nheights:\n  grid:\n    step: 16\n"
            "    unit: 64\n" + grid + "points:\n  - {id: entrance:start, at: [64, 64], facing: s}\n";
        std::filesystem::create_directories(root, error);
        const std::vector<std::pair<std::string, std::string>> files = {{"project.yml", card}, {"plan.yml", plan},
            {"sketch.yml", sketch}, {".gitignore", "build/\n"}};

        for (const std::pair<std::string, std::string> &file : files)
        {
            if (!writeTextFileAtomically(root / file.first, file.second, errorMessage))
            {
                return false;
            }

            written.push_back(file.first);
        }

        return true;
    }

    // Texture names of the reference theme exist in every MM6-MM8 world's merged textures; the theme is a start
    // to be replaced (oymap assets finds textures and their sizes).
    const std::string card =
        "format: 0\nid: " + request.id + "\nname: " + jsonQuote(request.name) + "\nworld: " + request.world
        + "\nkind: indoor\nprofile: dungeon\nmap_stats:\n  id: "
        + (request.statsId.empty() ? std::string("9400") : request.statsId) + "\n  reference: " + request.reference
        + "\n";
    const std::string rooms =
        "format: 0\nthemes:\n  - id: theme:masonry\n    wall: {texture: t1w11a, size: [128, 256]}\n"
        "    floor: {texture: oflr, size: [128, 128]}\n    ceiling: {texture: d2ceil4, size: [256, 256]}\n"
        "    reveal: {texture: t1trima, size: [32, 32], scale: 2}\n"
        "    door: {texture: t1d2, size: [256, 256], fit: true}\n"
        "defaults: {theme: theme:masonry, ambient: 14}\nrooms: []\nopenings: []\n";
    std::filesystem::create_directories(root, error);
    const std::vector<std::pair<std::string, std::string>> files = {{"project.yml", card}, {"rooms.yml", rooms},
        {"objects.yml", "format: 0\n"}, {"wiring.yml", "format: 0\nevents: []\n"}, {".gitignore", "build/\n"}};

    for (const std::pair<std::string, std::string> &file : files)
    {
        if (!writeTextFileAtomically(root / file.first, file.second, errorMessage))
        {
            return false;
        }

        written.push_back(file.first);
    }

    return true;
}

int runNew(const std::vector<std::string> &rawArguments)
{
    std::vector<std::string> arguments = rawArguments;
    NewProjectRequest request;
    takeOption(arguments, "--world", request.world);
    takeOption(arguments, "--reference", request.reference);
    takeOption(arguments, "--stats-id", request.statsId);
    takeOption(arguments, "--kind", request.kind);

    if (!takeOption(arguments, "--id", request.id) || !takeOption(arguments, "--name", request.name)
        || arguments.size() != 1)
    {
        std::cerr << "usage: oymap new <project folder> --id <map stem> --name <name> [--world <world>] "
                     "[--reference <shipped map>] [--stats-id <number>] [--kind indoor|outdoor]\n"
                     "  --id is the map's file stem (studio03 builds studio03.blv). --reference is a shipped map of\n"
                     "  the world whose map_stats row the new map starts from (monsters, music); --stats-id the new\n"
                     "  row's number (default 9400; each map needs its own).\n";
        return 2;
    }

    request.root = arguments[0];
    std::vector<std::string> written;
    bool exists = false;
    std::string errorMessage;

    if (!createEmptyProject(request, written, exists, errorMessage))
    {
        std::cerr << "oymap new: " << (exists ? request.root.string() + " already holds a project" : errorMessage)
                  << "\n";
        return 1;
    }

    std::cout << "created " << request.root.string() << ". "
              << (request.kind == "outdoor" ? NewOutdoorProjectNext : NewProjectNext) << "\n";
    return 0;
}
}
