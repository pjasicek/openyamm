#include "core/World.h"

#include "core/Project.h"
#include "core/SketchRead.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <map>
#include <set>
#include <sstream>

namespace OpenYAMM::Studio
{
namespace
{
YAML::Node readYamlFile(const std::filesystem::path &path)
{
    std::string text;

    if (!readTextFile(path, text))
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

std::string lowered(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(),
        [](unsigned char letter) { return static_cast<char>(std::tolower(letter)); });
    return text;
}

// A map's stem, lower case: "oute3.odm" and "OUTE3" are one map; a card's `to` that says more after the file
// ("oute3.odm at -18400, ...", an imported card) names its first word.
std::string stemOf(const std::string &map)
{
    const std::string lower = lowered(map.substr(0, map.find_first_of(" \t")));
    return lower.ends_with(".blv") || lower.ends_with(".odm") ? lower.substr(0, lower.size() - 4) : lower;
}

std::string kindOfFile(const std::string &map)
{
    const std::string lower = lowered(map);
    return lower.ends_with(".odm") ? "outdoor" : lower.ends_with(".blv") ? "indoor" : "unknown";
}

// The shipped maps' names by file (map_stats.txt: number, name, file), lower case.
std::map<std::string, std::string> shippedNames(const std::filesystem::path &assetRoot)
{
    std::map<std::string, std::string> names;
    std::string text;

    if (assetRoot.empty() || !readTextFile(assetRoot / "engine" / "data_tables" / "map_stats.txt", text))
    {
        return names;
    }

    std::istringstream stream(text);
    std::string line;

    while (std::getline(stream, line))
    {
        const size_t first = line.find('\t');
        const size_t second = first == std::string::npos ? std::string::npos : line.find('\t', first + 1);
        const size_t third = second == std::string::npos ? std::string::npos : line.find('\t', second + 1);

        if (third == std::string::npos || line.substr(0, first).find_first_not_of("0123456789") != std::string::npos
            || first == 0)
        {
            continue;
        }

        std::string file = lowered(line.substr(second + 1, third - second - 1));
        names.emplace(file, line.substr(first + 1, second - first - 1));
    }

    return names;
}

// Every object id in `node` whose own words name `id` (an exit's `to: neighbour:x`, a building's way out).
void usersOf(const YAML::Node &node, const std::string &id, const std::string &owner, std::set<std::string> &users)
{
    if (node.IsMap())
    {
        const YAML::Node own = node["id"];
        const std::string here = own && own.IsScalar() && own.Scalar() != id ? own.Scalar() : owner;

        for (YAML::const_iterator entry = node.begin(); entry != node.end(); ++entry)
        {
            const std::string key = entry->first.Scalar();

            if (entry->second.IsScalar())
            {
                if (key != "id" && entry->second.Scalar() == id && !here.empty())
                {
                    users.insert(here);
                }
            }
            else
            {
                usersOf(entry->second, id, here, users);
            }
        }
    }
    else if (node.IsSequence())
    {
        for (const YAML::Node &item : node)
        {
            if (item.IsScalar())
            {
                if (item.Scalar() == id && !owner.empty())
                {
                    users.insert(owner);
                }
            }
            else
            {
                usersOf(item, id, owner, users);
            }
        }
    }
}

// Every (object id, map) whose words name a map by `map:` (an outdoor building's way in, `into: {map: ...}`; a
// wiring effect that moves the party to a map).
void mapsNamed(const YAML::Node &node, const std::string &owner, std::vector<std::pair<std::string, std::string>> &found)
{
    if (node.IsMap())
    {
        const YAML::Node own = node["id"];
        const std::string here = own && own.IsScalar() ? own.Scalar() : owner;

        for (YAML::const_iterator entry = node.begin(); entry != node.end(); ++entry)
        {
            if (entry->second.IsScalar())
            {
                const std::string value = lowered(entry->second.Scalar());

                if (entry->first.Scalar() == "map" && (value.ends_with(".blv") || value.ends_with(".odm"))
                    && !here.empty())
                {
                    found.emplace_back(here, entry->second.Scalar());
                }
            }
            else
            {
                mapsNamed(entry->second, here, found);
            }
        }
    }
    else if (node.IsSequence())
    {
        for (const YAML::Node &item : node)
        {
            mapsNamed(item, owner, found);
        }
    }
}

struct PendingLink
{
    size_t from = 0;
    std::string world;
    YAML::Node neighbour;
    std::vector<std::string> exits;
};
}

WorldGraph readWorldGraph(const std::vector<std::filesystem::path> &projects, const std::string &world,
    const std::filesystem::path &assetRoot)
{
    WorldGraph graph;
    std::vector<PendingLink> pending;

    for (size_t index = 0; index < projects.size(); ++index)
    {
        const YAML::Node card = readYamlFile(projects[index] / "project.yml");

        if (!card.IsDefined() || !card.IsMap() || textOf(card, "id", "").empty())
        {
            graph.skipped.emplace_back(static_cast<int>(index), "its project.yml does not read");
            continue;
        }

        const std::string cardWorld = textOf(card, "world", "");

        if (!world.empty() && cardWorld != world)
        {
            continue;
        }

        WorldMapNode node;
        node.world = cardWorld;
        node.project = static_cast<int>(index);
        node.name = textOf(card, "name", textOf(card, "id", ""));
        const std::string base = textOf(card, "base", "");
        const std::string reference = textOf(childOf(card, "map_stats"), "reference", "");
        const std::string kind = textOf(card, "kind", "indoor");

        if (!base.empty())
        {
            node.map = base;
            node.kind = kindOfFile(base);
            node.role = "overlay";
            node.standsFor = base;
        }
        else
        {
            node.map = textOf(card, "id", "") + (kind == "outdoor" ? ".odm" : ".blv");
            node.kind = kind == "outdoor" ? "outdoor" : "indoor";
            node.role = reference.empty() ? "new" : "rebuild";
            node.standsFor = reference;
        }

        const size_t at = graph.maps.size();
        graph.maps.push_back(node);
        // The files whose objects use the neighbours.
        std::vector<YAML::Node> documents;

        for (const char *pFile : {"objects.yml", "sketch.yml", "wiring.yml", "plan.yml"})
        {
            documents.push_back(readYamlFile(projects[index] / pFile));
        }

        std::vector<std::pair<std::string, std::string>> named;

        for (const YAML::Node &document : documents)
        {
            if (document.IsDefined())
            {
                mapsNamed(document, "", named);
            }
        }

        std::set<std::string> declared;

        for (const YAML::Node &neighbour : childOf(card, "neighbours"))
        {
            PendingLink link;
            link.from = at;
            link.world = cardWorld;
            link.neighbour = neighbour;
            std::set<std::string> users;
            const std::string id = textOf(neighbour, "id", "");
            const std::string stem = stemOf(textOf(neighbour, "to", ""));
            declared.insert(stem);

            for (const YAML::Node &document : documents)
            {
                if (!id.empty() && document.IsDefined())
                {
                    usersOf(document, id, "", users);
                }
            }

            for (const std::pair<std::string, std::string> &way : named)
            {
                if (stemOf(way.second) == stem)
                {
                    users.insert(way.first);
                }
            }

            link.exits.assign(users.begin(), users.end());
            pending.push_back(link);
        }

        // Ways out the card's neighbours do not name: one link per map, kind `undeclared`.
        std::map<std::string, std::pair<std::string, std::set<std::string>>> undeclared;

        for (const std::pair<std::string, std::string> &way : named)
        {
            // (A way to the map itself: a ship or wagon that moves the party about the map.)
            const std::string stem = stemOf(way.second);

            if (!declared.contains(stem) && stem != stemOf(node.map) && stem != stemOf(node.standsFor))
            {
                std::pair<std::string, std::set<std::string>> &entry = undeclared[stemOf(way.second)];
                entry.first = way.second;
                entry.second.insert(way.first);
            }
        }

        for (const std::pair<const std::string, std::pair<std::string, std::set<std::string>>> &way : undeclared)
        {
            PendingLink link;
            link.from = at;
            link.world = cardWorld;
            link.neighbour = YAML::Node(YAML::NodeType::Map);
            link.neighbour["to"] = way.second.first;
            link.neighbour["kind"] = "undeclared";
            link.exits.assign(way.second.second.begin(), way.second.second.end());
            pending.push_back(link);
        }
    }

    const std::map<std::string, std::string> names = shippedNames(assetRoot);

    for (const PendingLink &link : pending)
    {
        const std::string target = textOf(link.neighbour, "to", "");

        if (target.empty())
        {
            continue;
        }

        const std::string stem = stemOf(target);
        // A project's own map, then one that stands for the map named, then a shipped map (one node per name).
        std::optional<size_t> found;
        bool viaOriginal = false;

        for (size_t index = 0; index < graph.maps.size() && !found; ++index)
        {
            const WorldMapNode &node = graph.maps[index];

            if (node.world == link.world && node.project >= 0 && node.role != "overlay" && stemOf(node.map) == stem)
            {
                found = index;
            }
        }

        for (size_t index = 0; index < graph.maps.size() && !found; ++index)
        {
            const WorldMapNode &node = graph.maps[index];

            if (node.world == link.world && node.project >= 0 && !node.standsFor.empty()
                && stemOf(node.standsFor) == stem)
            {
                found = index;
                viaOriginal = true;
            }
        }

        for (size_t index = 0; index < graph.maps.size() && !found; ++index)
        {
            const WorldMapNode &node = graph.maps[index];

            if (node.world == link.world && node.project < 0 && stemOf(node.map) == stem)
            {
                found = index;
            }
        }

        if (!found)
        {
            WorldMapNode shipped;
            shipped.world = link.world;
            shipped.map = target;
            shipped.kind = kindOfFile(target);
            shipped.role = "shipped";
            const std::map<std::string, std::string>::const_iterator name = names.find(lowered(target));
            shipped.name = name != names.end() ? name->second : target;
            found = graph.maps.size();
            graph.maps.push_back(shipped);
        }

        WorldLink made;
        made.from = link.from;
        made.to = *found;
        made.id = textOf(link.neighbour, "id", "");
        made.kind = textOf(link.neighbour, "kind", "");
        made.side = textOf(link.neighbour, "side", "");
        made.target = target;
        made.viaOriginal = viaOriginal;
        made.exits = link.exits;

        if (const YAML::Node days = childOf(link.neighbour, "days"); days.IsDefined() && days.IsScalar())
        {
            try
            {
                made.days = days.as<int>();
            }
            catch (const YAML::Exception &)
            {
            }
        }

        graph.links.push_back(made);
    }

    return graph;
}

void writeWorldGraph(const WorldGraph &graph, JsonWriter &writer)
{
    std::vector<std::string> worlds;

    for (const WorldMapNode &node : graph.maps)
    {
        if (std::find(worlds.begin(), worlds.end(), node.world) == worlds.end())
        {
            worlds.push_back(node.world);
        }
    }

    std::sort(worlds.begin(), worlds.end());
    writer.key("worlds");
    writer.beginArray();

    for (const std::string &world : worlds)
    {
        // Each world's maps are numbered from 0 in its own list.
        std::map<size_t, size_t> local;
        writer.beginObject();
        writer.field("world", world);
        writer.key("maps");
        writer.beginArray();

        for (size_t index = 0; index < graph.maps.size(); ++index)
        {
            const WorldMapNode &node = graph.maps[index];

            if (node.world != world)
            {
                continue;
            }

            const size_t number = local.size();
            local[index] = number;
            writer.beginObject();
            writer.field("map", node.map);
            writer.field("kind", node.kind);
            writer.field("role", node.role);
            writer.field("name", node.name);

            if (node.project >= 0)
            {
                writer.field("project", node.project);
            }

            if (!node.standsFor.empty())
            {
                writer.field("stands_for", node.standsFor);
            }

            writer.endObject();
        }

        writer.endArray();
        writer.key("links");
        writer.beginArray();

        for (const WorldLink &link : graph.links)
        {
            if (!local.contains(link.from) || !local.contains(link.to))
            {
                continue;
            }

            writer.beginObject();
            writer.field("from", static_cast<uint64_t>(local[link.from]));
            writer.field("to", static_cast<uint64_t>(local[link.to]));
            writer.field("id", link.id);
            writer.field("kind", link.kind);

            if (!link.side.empty())
            {
                writer.field("side", link.side);
            }

            if (link.days)
            {
                writer.field("days", *link.days);
            }

            writer.field("target", link.target);
            writer.field("via_original", link.viaOriginal);
            writer.key("exits");
            writer.beginArray();

            for (const std::string &exit : link.exits)
            {
                writer.value(exit);
            }

            writer.endArray();
            writer.endObject();
        }

        writer.endArray();
        writer.endObject();
    }

    writer.endArray();
    writer.key("skipped");
    writer.beginArray();

    for (const std::pair<int, std::string> &skipped : graph.skipped)
    {
        writer.beginObject();
        writer.field("project", skipped.first);
        writer.field("reason", skipped.second);
        writer.endObject();
    }

    writer.endArray();
}
}
