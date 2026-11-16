#include "core/OutdoorEvents.h"

#include "core/Json.h"
#include "core/SketchRead.h"

#include "game/FaceEnums.h"

#include <algorithm>
#include <charconv>
#include <cmath>
#include <sstream>

// What the handlers of the shipped outdoor maps test and do beside entering a house, leaving for a map and opening
// a chest (measured with `oymap flow` on Ravenshore and Harmondale; output/studio_s4d/orig):
//
//   a lock in front of a door: all 33 house doors of Harmondale enter only while quest bit 695 is clear and
//   otherwise say "This Door is Locked"; 59 doors of Ravenshore are shut while the pirates are in the town (57);
//   the council's terrace door leads in once bit 59 is set and speaks to an NPC before; the crystal's door needs
//   item 610; the Vault of Time opens its chest with the key or once it has been opened (item 661, a map
//   variable); a chest opens for those who hold an award;
//   a click that changes a decoration: a picked fruit tree goes bare, a signal fire is lit
//   (`evt.SetSprite(<the decoration's number>, 1, "<picture>")`; the number is the entity's `event_id_primary`);
//   events that show and hide models and change their textures: Castle Harmondale's towers are models whose faces
//   start invisible and untouchable and carry one number (`cog_number` 20), shown by
//   `evt.SetFacetBit(20, FacetBits.Invisible, 0)` and `... Untouchable, 0`; its walls carry a number per texture
//   and are repainted by `evt.SetTexture(<number>, "<texture>")`;
//   events nobody clicks: on entering the map (`onLoad`), by the clock (`timers`, counted in half minutes of game
//   time), and faces walked onto (the face bit PressurePlate with the event on it: the hill fort's trap);
//   actors shown by an event: `evt.SetMonGroupBit(<group>, MonsterBits.Invisible, 0)`.
//
// So the words here are the indoor wiring's (condition, locked_text, else_effects, effects, once, lua), with the
// outdoor effects show, hide, set_sprite, set_texture, show_actors and hide_actors. A handler's order is: `once`,
// the condition (when it fails: else_effects, locked_text, stop), the house, map or chest of the thing, effects,
// lua.

namespace OpenYAMM::Studio
{
namespace
{
const char *SketchFile = "sketch.yml";
// Decorations take their numbers from here up, clear of the numbers the game falls back to for a decoration
// without one (its place in the map's list).
constexpr int FirstDecorationNumber = 30000;



bool numberOfNode(const YAML::Node &value, double &number)
{
    if (!value.IsDefined() || !value.IsScalar())
    {
        return false;
    }

    const std::string &text = value.Scalar();
    const std::from_chars_result result = std::from_chars(text.data(), text.data() + text.size(), number);
    return result.ec == std::errc() && result.ptr == text.data() + text.size() && std::isfinite(number);
}

double numberOr(const YAML::Node &node, const char *pKey, double fallback)
{
    double number = fallback;
    return numberOfNode(childOf(node, pKey), number) ? number : fallback;
}

std::string lowerCase(const std::string &text)
{
    std::string result = text;
    std::transform(result.begin(), result.end(), result.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return result;
}

std::string luaQuote(const std::string &text)
{
    std::string result = "\"";

    for (const char character : text)
    {
        if (character == '"' || character == '\\')
        {
            result.push_back('\\');
        }

        result.push_back(character == '\n' ? ' ' : character);
    }

    return result + "\"";
}

// A line in the status bar held long enough to read, as indoors (IndoorLowering statusLine): a text over 30
// characters 2 seconds and one more for each 15 characters, at most 6; a shorter one the game's default 2.
std::string statusLine(const std::string &text)
{
    const int seconds = std::clamp(2 + static_cast<int>(text.size() / 15), 2, 6);
    return "evt.StatusText(" + luaQuote(text) + (text.size() > 30 ? ", " + std::to_string(seconds) : std::string())
        + ")";
}

std::string wholeText(double number)
{
    return std::to_string(static_cast<long long>(number));
}

// A point [x, y, z] of an effect as three Lua arguments on whole units; empty when it is not one.
std::string pointArguments(const YAML::Node &effect, const char *pKey)
{
    const YAML::Node point = childOf(effect, pKey);
    std::string arguments;

    if (!point.IsDefined() || !point.IsSequence() || point.size() != 3)
    {
        return arguments;
    }

    for (size_t axis = 0; axis < 3; ++axis)
    {
        double coordinate = 0.0;

        if (!numberOfNode(point[axis], coordinate))
        {
            return {};
        }

        arguments += (arguments.empty() ? "" : ", ") + std::to_string(std::lround(coordinate));
    }

    return arguments;
}
}

YAML::Node sketchNodeAt(const YAML::Node &root, const std::string &path)
{
    YAML::Node node = root;
    size_t at = 0;

    while (at < path.size() && node.IsDefined())
    {
        if (path[at] == '.')
        {
            ++at;
            continue;
        }

        if (path[at] == '[')
        {
            const size_t close = path.find(']', at);
            size_t index = 0;

            if (close == std::string::npos
                || std::from_chars(path.data() + at + 1, path.data() + close, index).ec != std::errc()
                || !node.IsSequence() || index >= node.size())
            {
                return YAML::Node(YAML::NodeType::Undefined);
            }

            // A fresh handle each step: assigning to a node would rewrite the tree it stands in.
            const YAML::Node next = node[index];
            node.reset(next);
            at = close + 1;
            continue;
        }

        const size_t end = path.find_first_of(".[", at);
        const std::string key = path.substr(at, end == std::string::npos ? end : end - at);
        const YAML::Node next = childOf(node, key.c_str());
        node.reset(next);
        at = end == std::string::npos ? path.size() : end;
    }

    return node;
}

OutdoorEventWords::OutdoorEventWords(
    const Project &project,
    const std::filesystem::path &assetRoot,
    IdsLock &ids,
    std::vector<ProjectIssue> &issues)
    : m_project(project)
    , m_assetRoot(assetRoot)
    , m_ids(ids)
    , m_issues(issues)
{
    const YAML::Node sketch = project.document(SketchFile);
    const YAML::Node structures = childOf(sketch, "structures");

    for (size_t index = 0; structures.IsDefined() && structures.IsSequence() && index < structures.size(); ++index)
    {
        const YAML::Node node = structures[index];
        const std::string id = textOf(node, "id");

        if (id.empty())
        {
            continue;
        }

        OutdoorEventTarget target;
        target.decoration = textOf(node, "kind") == "decoration";
        target.hidden = textOf(node, "hidden") == "true";
        target.follows = textOf(node, "switch");
        target.path = "structures[" + std::to_string(index) + "]";
        m_targets.emplace(id, target);
    }

    const YAML::Node districts = childOf(sketch, "districts");

    for (size_t district = 0; districts.IsDefined() && districts.IsSequence() && district < districts.size();
         ++district)
    {
        const YAML::Node plots = childOf(districts[district], "plots");

        for (size_t index = 0; plots.IsDefined() && plots.IsSequence() && index < plots.size(); ++index)
        {
            const YAML::Node plot = plots[index];
            OutdoorEventTarget target;
            target.hidden = textOf(plot, "hidden") == "true";
            target.path = "districts[" + std::to_string(district) + "].plots[" + std::to_string(index) + "]";
            m_targets.emplace(textOf(plot, "building")
                + (childOf(plot, "index").IsDefined() ? "#" + textOf(plot, "index") : std::string()), target);
        }
    }

    // Scattered decorations with an `id`: all the decorations of the entries of one id are one target (a
    // forest whose pictures change with the season, as Harmondale's load event 250 changes ids 5, 6 and 7).
    const YAML::Node scatter = childOf(sketch, "scatter");

    for (size_t index = 0; scatter.IsDefined() && scatter.IsSequence() && index < scatter.size(); ++index)
    {
        const std::string path = "scatter[" + std::to_string(index) + "]";
        const YAML::Node groupNode = childOf(scatter[index], "group");
        int group = 0;

        if (groupNode.IsDefined())
        {
            group = groupNode.as<int>(0);

            if (group < 1 || group >= FirstDecorationNumber || groupNode.Scalar() != std::to_string(group))
            {
                add(path + ".group", "`group` is the number the entry's decorations carry, 1 to "
                    + std::to_string(FirstDecorationNumber - 1) + " (the shipped maps' season groups are 5, 6, 7 "
                    "and 10)");
                continue;
            }
        }

        // An entry with a group and no id is named by its group: group:5.
        const std::string id = !textOf(scatter[index], "id").empty() ? textOf(scatter[index], "id")
            : group != 0 ? "group:" + std::to_string(group) : std::string();
        const std::map<std::string, OutdoorEventTarget>::iterator known = m_targets.find(id);

        if (id.empty())
        {
            continue;
        }

        if (known != m_targets.end() && known->second.path.rfind("scatter[", 0) != 0)
        {
            add(path + ".id", "`" + id + "` is already the id of "
                + known->second.path + ": a scatter entry's id names its decorations alone (entries may share one)");
            continue;
        }

        if (known != m_targets.end())
        {
            if (known->second.group != group)
            {
                add(path + ".group", "the entries of one id are one group: " + known->second.path + " has `group: "
                    + std::to_string(known->second.group) + "`, this one " + std::to_string(group));
            }

            continue;
        }

        for (const std::pair<const std::string, OutdoorEventTarget> &other : m_targets)
        {
            if (group != 0 && other.second.group == group)
            {
                add(path + ".group", "group " + std::to_string(group) + " is already the group of `" + other.first
                    + "` (" + other.second.path + "): give entries of one group one id");
            }
        }

        OutdoorEventTarget target;
        target.decoration = true;
        target.group = group;
        target.path = path;
        m_targets.emplace(id, target);
    }

    // `switch`: a structure that is shown and hidden with another (a gangway with its ship) names a model that
    // events can change, not itself, and starts as that one starts.
    for (const std::pair<const std::string, OutdoorEventTarget> &entry : m_targets)
    {
        const std::string &other = entry.second.follows;

        if (other.empty())
        {
            continue;
        }

        const std::map<std::string, OutdoorEventTarget>::const_iterator leader = m_targets.find(other);

        if (entry.second.decoration || other == entry.first || leader == m_targets.end()
            || leader->second.decoration || !leader->second.follows.empty() || entry.second.hidden)
        {
            add(entry.second.path + ".switch", "`switch` names the structure or building whose show and hide this "
                "model follows (a gangway with its ship): another model of the sketch that follows none itself; "
                "the follower starts as that one starts (no `hidden` of its own), and a decoration has no faces",
                "reference");
        }
    }

    // The textures any handler changes on a model, before a handler is written: an effect that shows or hides
    // the model must name the faces of those textures too, whichever comes first in the sketch.
    collectSwaps(sketch);
    const YAML::Node actors = childOf(sketch, "actors");

    for (size_t index = 0; actors.IsDefined() && actors.IsSequence() && index < actors.size(); ++index)
    {
        const int group = static_cast<int>(numberOr(actors[index], "group", 0.0));

        if (group > 0)
        {
            m_actorGroups.insert(group);
        }

        if (textOf(actors[index], "hidden") == "true")
        {
            if (group <= 0)
            {
                add("actors[" + std::to_string(index) + "].hidden", "actors that start hidden are shown by their "
                    "group ({show_actors: <group>}): give the entry a `group` number of its own");
            }
            else
            {
                m_hiddenGroups.insert(group);
            }
        }
    }
}

void OutdoorEventWords::collectSwaps(const YAML::Node &node)
{
    if (node.IsSequence())
    {
        for (size_t index = 0; index < node.size(); ++index)
        {
            collectSwaps(node[index]);
        }

        return;
    }

    if (!node.IsMap())
    {
        return;
    }

    // A search for one word through everything: only what it finds counts as read (core/SketchRead.h).
    for (YAML::const_iterator entry = node.begin(); entry != node.end(); ++entry)
    {
        if (entry->first.IsScalar() && entry->first.Scalar() == "set_texture" && entry->second.IsMap())
        {
            noteRead(entry->second);
            const std::map<std::string, OutdoorEventTarget>::iterator found =
                m_targets.find(textOf(entry->second, "of"));

            if (found != m_targets.end() && !found->second.decoration && !textOf(entry->second, "from").empty())
            {
                found->second.swapped.insert(lowerCase(textOf(entry->second, "from")));
            }
        }
        else
        {
            collectSwaps(entry->second);
        }
    }
}

void OutdoorEventWords::add(const std::string &path, const std::string &message, const char *pCode)
{
    m_issues.push_back({SketchFile, path, message, pCode});
}

bool OutdoorEventWords::hasActions(const YAML::Node &node)
{
    return childOf(node, "effects").IsDefined() || childOf(node, "lua").IsDefined();
}

const std::map<std::string, OutdoorEventTarget> &OutdoorEventWords::targets() const
{
    return m_targets;
}

const std::map<std::string, std::string> &OutdoorEventWords::namedTextures() const
{
    return m_namedTextures;
}

const std::set<int> &OutdoorEventWords::shownGroups() const
{
    return m_shownGroups;
}

// A number, or a name declared in a table of project.yml (qbits, items, awards).
int OutdoorEventWords::namedNumber(const YAML::Node &value, const char *pTable, const std::string &path)
{
    double number = 0.0;

    if (numberOfNode(value, number) && number == std::floor(number))
    {
        return static_cast<int>(number);
    }

    const YAML::Node table = childOf(m_project.document("project.yml"), pTable);
    const std::string name = value.IsDefined() && value.IsScalar() ? value.Scalar() : std::string();

    if (!name.empty() && numberOfNode(childOf(table, name.c_str()), number))
    {
        return static_cast<int>(number);
    }

    add(path, "`" + name + "` is no number and is not declared in project.yml `" + pTable + "`: write the number, "
        "or add `" + (name.empty() ? std::string("<name>") : name) + ": <number>` there", "reference");
    return 0;
}

// A map variable: its number, or a name that gets a number of its own (ids.lock.yml `map_vars`).
int OutdoorEventWords::mapVariable(const YAML::Node &value, const std::string &path)
{
    double number = 0.0;

    if (numberOfNode(value, number) && number == std::floor(number) && number >= 0.0 && number <= 74.0)
    {
        return static_cast<int>(number);
    }

    const std::string name = value.IsDefined() && value.IsScalar() ? value.Scalar() : std::string();
    const bool plain = !name.empty() && std::isalpha(static_cast<unsigned char>(name[0])) != 0
        && std::all_of(name.begin(), name.end(), [](unsigned char character)
        {
            return std::isalnum(character) != 0 || character == '_';
        });

    if (!plain)
    {
        add(path, "a map variable is a number from 0 to 74 or a name of letters, digits and _ (the build gives a "
            "name a number of its own and keeps it in ids.lock.yml)", "reference");
        return 0;
    }

    const int index = IdsLock::number(m_ids.mapVars, name, 0);

    if (index > 74)
    {
        add(path, "the map has more than 75 variables", "limit");
    }

    return index;
}

// The name of a variable of the game's scripts (Gold, HP, MightBonus ...; `oymap script-reference` lists them),
// or a map variable as {map_var: n}.
std::string OutdoorEventWords::selector(const YAML::Node &node, const std::string &path)
{
    if (node.IsDefined() && node.IsMap() && childOf(node, "map_var").IsDefined())
    {
        return "MapVar(" + std::to_string(mapVariable(childOf(node, "map_var"), path + ".map_var")) + ")";
    }

    const std::string name = node.IsDefined() && node.IsScalar() ? node.Scalar() : std::string();
    const bool plain = !name.empty() && std::all_of(name.begin(), name.end(), [](unsigned char character)
    {
        return std::isalnum(character) != 0 || character == '(' || character == ')' || character == '_';
    });
    return plain ? name : std::string();
}

std::string OutdoorEventWords::condition(const YAML::Node &condition, const std::string &path)
{
    std::vector<std::string> terms;

    if (!condition.IsDefined() || !condition.IsMap())
    {
        add(path, "a condition is a map of what must hold: {qbit: 59}, {item: 610}, {not: {qbit: 695}}, "
            "{any: [{item: 661}, {map_var: vault_open}]}");
        return "true";
    }

    for (YAML::const_iterator entry = condition.begin(); entry != condition.end(); ++entry)
    {
        const std::string key = entry->first.Scalar();
        const YAML::Node value = entry->second;
        noteRead(value);

        if (key == "item")
        {
            // One item, or every item of a list.
            std::vector<YAML::Node> items;

            if (value.IsSequence())
            {
                for (const YAML::Node &item : value)
                {
                    items.push_back(item);
                }
            }
            else
            {
                items.push_back(value);
            }

            for (const YAML::Node &item : items)
            {
                terms.push_back("HasItem(" + std::to_string(namedNumber(item, "items", path + ".item")) + ")");
            }
        }
        else if (key == "qbit")
        {
            terms.push_back("IsQBitSet(QBit(" + std::to_string(namedNumber(value, "qbits", path + ".qbit")) + "))");
        }
        else if (key == "map_var")
        {
            terms.push_back("IsAtLeast(MapVar(" + std::to_string(mapVariable(value, path + ".map_var")) + "), 1)");
        }
        else if (key == "not")
        {
            terms.push_back("not (" + this->condition(value, path + ".not") + ")");
        }
        else if (key == "any" || key == "all")
        {
            std::string joined;

            for (size_t index = 0; value.IsSequence() && index < value.size(); ++index)
            {
                joined += joined.empty() ? "" : (key == "any" ? " or " : " and ");
                joined += "(" + this->condition(value[index], path + "." + key + "[" + std::to_string(index) + "]")
                    + ")";
            }

            terms.push_back("(" + (joined.empty() ? std::string(key == "any" ? "false" : "true") : joined) + ")");
        }
        else if (key == "consume" || key == "item_count")
        {
            double count = 1.0;

            if (key == "item_count" && (!numberOfNode(value, count) || count != 1.0))
            {
                add(path + ".item_count", "item counts above 1 are not built: say the test with the condition's "
                    "`lua` key ({lua: \"evt.CheckItemsCount(221, 271, 1)\"})", "unsupported");
            }
        }
        else if (key == "gold")
        {
            double amount = 0.0;

            if (numberOfNode(childOf(value, "at_least"), amount))
            {
                terms.push_back("IsAtLeast(Gold, " + formatNumber(amount) + ")");
            }

            if (numberOfNode(childOf(value, "below"), amount))
            {
                terms.push_back("not IsAtLeast(Gold, " + formatNumber(amount) + ")");
            }
        }
        else if (key == "stat")
        {
            const std::string name = selector(childOf(value, "name"), path + ".stat.name");

            if (name.empty())
            {
                add(path + ".stat", "stat is {name: <a selector of the game's scripts: BaseLuck, MightBonus, "
                    "DisarmTrapSkill ...; `oymap script-reference` lists them>, at_least: <number>}");
                continue;
            }

            terms.push_back("IsAtLeast(" + name + ", " + formatNumber(numberOr(value, "at_least", 1.0)) + ")");
        }
        else if (key == "award")
        {
            terms.push_back("HasAward(" + std::to_string(namedNumber(value, "awards", path + ".award")) + ")");
        }
        else if (key == "autonote")
        {
            terms.push_back("IsAutonoteSet(" + std::to_string(namedNumber(value, "autonotes", path + ".autonote"))
                + ")");
        }
        else if (key == "season")
        {
            static const std::pair<const char *, const char *> Seasons[] = {{"spring", "Spring"},
                {"summer", "Summer"}, {"autumn", "Autumn"}, {"winter", "Winter"}};
            const std::string name = value.IsScalar() ? value.Scalar() : std::string();
            std::string season;

            for (const std::pair<const char *, const char *> &known : Seasons)
            {
                season = name == known.first ? known.second : season;
            }

            if (season.empty())
            {
                add(path + ".season", "season is spring, summer, autumn or winter");
                continue;
            }

            terms.push_back("evt.CheckSeason(Season." + season + ")");
        }
        else if (key == "kills")
        {
            // All of a group dead ({group: 2}), so many of it ({group: 2, at_least: 3}), every monster of the map
            // ({all: true}) or so many of any ({at_least: 5}): the game's own test, in which 0 means all.
            double group = 0.0;
            double atLeast = 0.0;
            const bool grouped = numberOfNode(childOf(value, "group"), group);
            const bool counted = numberOfNode(childOf(value, "at_least"), atLeast);

            if (!value.IsMap() || childOf(value, "monster").IsDefined() || (counted && atLeast < 1.0)
                || (counted && textOf(value, "all") == "true")
                || (childOf(value, "group").IsDefined() && !grouped))
            {
                add(path + ".kills", "kills is {group: <the `group` number of `actors`>} (all of the group dead), "
                    "{group: 2, at_least: 3} (so many of it), {all: true} (every monster of the map) or "
                    "{at_least: 5} (so many of any)");
                continue;
            }

            if (grouped && !m_actorGroups.contains(static_cast<int>(group)))
            {
                add(path + ".kills.group", "no entry of `actors` has `group: " + wholeText(group) + "`, so \"all "
                    "of that group dead\" would hold from the start: give the actors that are meant that `group`",
                    "reference");
                continue;
            }

            terms.push_back("evt.CheckMonstersKilled(" + (grouped ? "ActorKillCheck.Group, " + wholeText(group)
                : std::string("ActorKillCheck.Any, 0")) + ", " + wholeText(atLeast) + ", false)");
        }
        else if (key == "lua")
        {
            const std::string expression = value.IsScalar() ? value.Scalar() : std::string();

            if (expression.empty() || expression.find('\n') != std::string::npos
                || expression.rfind("return", 0) == 0)
            {
                add(path + ".lua", "a condition's `lua` is one Lua expression on one line that must be true, "
                    "without `return`: {lua: \"IsAtLeast(MapVar(3), 2)\"}");
                continue;
            }

            terms.push_back("(" + expression + ")");
        }
        else
        {
            add(path + "." + key, "the build has no test for a `" + key + "` condition (it has item, qbit, "
                "map_var, gold, stat, award, autonote, season, kills, lua, not, any, all): say the test as a Lua "
                "expression with the condition's `lua` key", "unsupported");
        }
    }

    std::string expression;

    for (const std::string &term : terms)
    {
        expression += (expression.empty() ? "" : " and ") + term;
    }

    return expression.empty() ? "true" : expression;
}

std::vector<std::string> OutdoorEventWords::targetIds(const YAML::Node &value) const
{
    std::vector<std::string> ids;

    if (value.IsDefined() && value.IsScalar())
    {
        ids.push_back(value.Scalar());
    }

    for (size_t index = 0; value.IsDefined() && value.IsSequence() && index < value.size(); ++index)
    {
        ids.push_back(value[index].IsScalar() ? value[index].Scalar() : std::string());
    }

    return ids;
}

OutdoorEventTarget *OutdoorEventWords::target(const YAML::Node &value, const std::string &path,
    const std::string &effect)
{
    const std::string id = value.IsDefined() && value.IsScalar() ? value.Scalar() : std::string();
    const std::map<std::string, OutdoorEventTarget>::iterator found = m_targets.find(id);

    if (found == m_targets.end())
    {
        add(path, effect + " names `" + id + "`, which the sketch does not draw: name a structure by its `id` "
            "(thing:signal_fire) or a plot's building (building:castle, building:houses#2)", "reference");
        return nullptr;
    }

    return &found->second;
}

int OutdoorEventWords::decorationNumber(const std::string &id)
{
    const std::map<std::string, OutdoorEventTarget>::const_iterator found = m_targets.find(id);

    if (found != m_targets.end() && found->second.decoration && found->second.group != 0)
    {
        // A group carries its number whether or not an event of this map names it (the shipped forests do).
        return found->second.group;
    }

    if (found == m_targets.end() || !found->second.decoration || (!found->second.toggled && !found->second.hidden
        && found->second.swapped.empty()))
    {
        return 0;
    }

    return IdsLock::number(m_ids.cogs, "cog:" + id, FirstDecorationNumber);
}

bool OutdoorEventWords::knownDecoration(const std::string &name)
{
    if (!m_decorationsLoaded)
    {
        m_decorationsLoaded = true;
        std::string text;

        if (!m_assetRoot.empty()
            && readTextFile(m_assetRoot / "engine" / "data_tables" / "decoration_data.txt", text))
        {
            std::istringstream lines(text);
            std::string line;

            while (std::getline(lines, line))
            {
                if (!line.empty() && line.back() == '\r')
                {
                    line.pop_back();
                }

                // The internal name is the table's second column.
                const size_t first = line.find('\t');
                const size_t second = first == std::string::npos ? first : line.find('\t', first + 1);
                const std::string name = first == std::string::npos ? std::string()
                    : line.substr(first + 1, second == std::string::npos ? second : second - first - 1);

                if (!name.empty())
                {
                    m_decorationNames.insert(lowerCase(name));
                }
            }
        }
    }

    return m_decorationNames.empty() || m_decorationNames.contains(lowerCase(name));
}

// show and hide: a decoration by its picture, a model by its faces' bits.
void OutdoorEventWords::visibility(const YAML::Node &value, const std::string &path, const std::string &key,
    bool show, const std::string &indent, std::vector<std::string> &body)
{
    const std::vector<std::string> ids = targetIds(value);

    if (ids.empty())
    {
        add(path, key + " is a structure or a plot's building, or a list of them: {" + key
            + ": thing:signal_fire}, {" + key + ": [building:tower_a, building:tower_b]}");
        return;
    }

    for (const std::string &id : ids)
    {
        OutdoorEventTarget *pTarget = target(YAML::Node(id), path, key);

        if (pTarget == nullptr)
        {
            continue;
        }

        pTarget->toggled = true;

        if (pTarget->decoration)
        {
            body.push_back(indent + "evt.SetSprite(" + std::to_string(decorationNumber(id)) + ", "
                + (show ? "1" : "0") + ")");
            continue;
        }

        // The model's own number, and one for each texture an event changes on it.
        std::vector<int> numbers = {IdsLock::number(m_ids.cogs, "cog:" + id, 1)};

        for (const std::string &texture : pTarget->swapped)
        {
            numbers.push_back(IdsLock::number(m_ids.cogs, "cog:" + id + ":" + texture, 1));
        }

        for (const int number : numbers)
        {
            body.push_back(indent + "evt.SetFacetBit(" + std::to_string(number) + ", FacetBits.Invisible, "
                + (show ? "0" : "1") + ")");
            body.push_back(indent + "evt.SetFacetBit(" + std::to_string(number) + ", FacetBits.Untouchable, "
                + (show ? "0" : "1") + ")");
        }
    }
}

void OutdoorEventWords::effects(const YAML::Node &effects, const std::string &path, const std::string &indent,
    std::vector<std::string> &body)
{
    if (!effects.IsDefined())
    {
        return;
    }

    if (!effects.IsSequence())
    {
        add(path, "effects is a list of steps, each one key: [{text: \"...\"}, {gold: 100}]");
        return;
    }

    for (size_t index = 0; index < effects.size(); ++index)
    {
        const YAML::Node effect = effects[index];
        const std::string at = path + "[" + std::to_string(index) + "]";

        if (!effect.IsMap() || effect.size() != 1)
        {
            add(at, "an effect is one key: {text: \"...\"}, {gold: 100}, {add: {var: MightBonus, value: 25}}, "
                "{subtract: {...}}, {set: {...}}, {autonote: n}, {qbit: n}, {clear_qbit: n}, {give_item: n}, "
                "{teleport: {to: [x, y, z], direction: 90}} or {lua: \"...\"}");
            continue;
        }

        const std::string key = effect.begin()->first.Scalar();
        const YAML::Node value = effect.begin()->second;
        noteRead(value);
        double number = 0.0;
        const bool isNumber = numberOfNode(value, number);
        const std::string whole = wholeText(number);

        if (key == "text" && value.IsScalar())
        {
            body.push_back(indent + statusLine(value.Scalar()));
        }
        else if (key == "gold" && isNumber)
        {
            body.push_back(indent + (number >= 0.0 ? "AddValue(Gold, " + whole + ")"
                : "SubtractValue(Gold, " + wholeText(-number) + ")"));
        }
        else if ((key == "add" || key == "subtract" || key == "set") && value.IsMap())
        {
            const std::string name = selector(childOf(value, "var"), at + "." + key + ".var");
            double amount = 0.0;

            if (name.empty() || !numberOfNode(childOf(value, "value"), amount))
            {
                add(at, key + " is {var: <a selector of the game's scripts, such as Gold, MightBonus or "
                    "{map_var: n}>, value: <number>}; `oymap script-reference` lists the selectors");
                continue;
            }

            body.push_back(indent + std::string(key == "add" ? "AddValue(" : (key == "subtract" ? "SubtractValue("
                : "SetValue(")) + name + ", " + wholeText(amount) + ")");
        }
        else if (key == "autonote" && isNumber)
        {
            body.push_back(indent + "SetAutonote(" + whole + ")");
        }
        else if (key == "qbit" || key == "clear_qbit")
        {
            body.push_back(indent + (key == "qbit" ? "SetQBit(QBit(" : "ClearQBit(QBit(")
                + std::to_string(namedNumber(value, "qbits", at + "." + key)) + "))");
        }
        else if (key == "give_item")
        {
            body.push_back(indent + "evt.GiveItem(1, 0, " + std::to_string(namedNumber(value, "items",
                at + ".give_item")) + ")");
        }
        else if (key == "take_item")
        {
            body.push_back(indent + "RemoveItem(" + std::to_string(namedNumber(value, "items", at + ".take_item"))
                + ")");
        }
        else if (key == "teleport" && value.IsMap())
        {
            const YAML::Node to = childOf(value, "to");

            if (!to.IsDefined() || !to.IsSequence() || to.size() != 3)
            {
                add(at, "teleport is {to: [x, y, z], direction: <degrees, 0 east, 90 north>} in map units, or with "
                    "`map: <file>` to another map");
                continue;
            }

            const int direction = static_cast<int>(std::lround(numberOr(value, "direction", 0.0) * 2048.0 / 360.0));
            const std::string map = textOf(value, "map");
            body.push_back(indent + "evt.MoveToMap(" + std::to_string(to[0].as<int>(0)) + ", "
                + std::to_string(to[1].as<int>(0)) + ", " + std::to_string(to[2].as<int>(0)) + ", "
                + std::to_string(direction) + ", 0, 0, 0, 0" + (map.empty() ? std::string() : ", " + luaQuote(map))
                + ")");
        }
        else if (key == "lua" && value.IsScalar())
        {
            body.push_back(indent + value.Scalar());
        }
        else if (key == "damage")
        {
            // {damage: 25} or {damage: {amount: 25, kind: fire, who: all}}.
            static const std::set<std::string> Kinds = {"air", "body", "cold", "dark", "earth", "electric", "energy",
                "fire", "light", "magic", "mind", "physical", "poison", "spirit", "water"};
            const double amount = isNumber ? number : numberOr(value, "amount", 0.0);
            std::string kind = isNumber ? "physical" : textOf(value, "kind", "physical");
            const std::string who = isNumber ? "all" : textOf(value, "who", "all");

            if ((!isNumber && !value.IsMap()) || amount < 1.0 || !Kinds.contains(kind)
                || (who != "all" && who != "current"))
            {
                add(at + ".damage", "damage is {amount: <1 or more>, kind: <air, body, cold, dark, earth, electric, "
                    "energy, fire, light, magic, mind, physical (default), poison, spirit or water>, who: <all "
                    "(default) or current>}, or the amount alone");
                continue;
            }

            kind[0] = static_cast<char>(std::toupper(static_cast<unsigned char>(kind[0])));
            body.push_back(indent + "evt.DamagePlayer(Players." + (who == "all" ? "All" : "Current")
                + ", const.Damage." + kind + ", " + std::to_string(std::lround(amount)) + ")");
        }
        else if (key == "cast")
        {
            static const std::map<std::string, int> Masteries = {{"normal", 1}, {"expert", 2}, {"master", 3},
                {"grandmaster", 4}};
            const std::string from = pointArguments(value, "from");
            const std::string to = pointArguments(value, "to");
            const std::map<std::string, int>::const_iterator mastery =
                Masteries.find(textOf(value, "mastery", "normal"));
            const double spell = numberOr(value, "spell", 0.0);
            const double level = numberOr(value, "level", 1.0);

            if (from.empty() || to.empty() || mastery == Masteries.end() || spell < 1.0 || level < 1.0)
            {
                add(at + ".cast", "cast is {spell: <the spell's number>, from: [x, y, z], to: [x, y, z], mastery: "
                    "<normal (default), expert, master or grandmaster>, level: <skill level, default 1>}: the spell "
                    "flies from the first point toward the second, in map units");
                continue;
            }

            body.push_back(indent + "evt.CastSpell(" + std::to_string(std::lround(spell)) + ", "
                + std::to_string(std::lround(level)) + ", " + std::to_string(mastery->second) + ", " + from + ", "
                + to + ")");
        }
        else if (key == "summon")
        {
            static const std::map<std::string, int> Tiers = {{"a", 1}, {"b", 2}, {"c", 3}};
            const std::string place = pointArguments(value, "at");
            const std::map<std::string, int>::const_iterator tier = Tiers.find(textOf(value, "tier", "a"));
            const double slot = numberOr(value, "slot", 0.0);
            const double count = numberOr(value, "count", 1.0);

            if (place.empty() || tier == Tiers.end() || slot < 1.0 || slot > 3.0 || count < 1.0)
            {
                add(at + ".summon", "summon is {slot: <1 to 3, the map card's encounter slot>, at: [x, y, z], "
                    "count: <default 1>, tier: <a (default), b or c>, group: <default 0>}, in map units");
                continue;
            }

            body.push_back(indent + "evt.SummonMonsters(" + std::to_string(std::lround(slot)) + ", "
                + std::to_string(tier->second) + ", " + std::to_string(std::lround(count)) + ", " + place + ", "
                + std::to_string(std::lround(numberOr(value, "group", 0.0))) + ", 0)");
        }
        else if (key == "show" || key == "hide")
        {
            visibility(value, at + "." + key, key, key == "show", indent, body);
        }
        else if (key == "set_sprite")
        {
            // A decoration's picture: {set_sprite: {of: thing:fruit_tree, to: tree37}}.
            OutdoorEventTarget *pTarget = value.IsMap() ? target(childOf(value, "of"), at + ".set_sprite.of",
                "set_sprite") : nullptr;
            const std::string picture = textOf(value, "to");

            if (!value.IsMap() || picture.empty() || (pTarget != nullptr && !pTarget->decoration))
            {
                add(at + ".set_sprite", "set_sprite is {of: <a structure of kind decoration>, to: <the "
                    "decoration whose picture it takes: an internal name of engine/data_tables/decoration_data.txt, "
                    "as tree37>}; a model is changed with show, hide and set_texture");
                continue;
            }

            if (pTarget == nullptr)
            {
                continue;
            }

            if (!knownDecoration(picture))
            {
                add(at + ".set_sprite.to", "there is no decoration named " + picture + " in engine/data_tables/"
                    "decoration_data.txt; `oymap assets <text> --kind decoration` lists them", "reference");
                continue;
            }

            pTarget->toggled = true;
            body.push_back(indent + "evt.SetSprite(" + std::to_string(decorationNumber(textOf(value, "of")))
                + ", 1, " + luaQuote(picture) + ")");
        }
        else if (key == "set_texture")
        {
            // A model's faces of one texture get another: {set_texture: {of: building:castle, from: chb1, to:
            // chb1dl}}.
            OutdoorEventTarget *pTarget = value.IsMap() ? target(childOf(value, "of"), at + ".set_texture.of",
                "set_texture") : nullptr;
            const std::string from = lowerCase(textOf(value, "from"));
            const std::string to = textOf(value, "to");

            if (!value.IsMap() || from.empty() || to.empty() || (pTarget != nullptr && pTarget->decoration))
            {
                add(at + ".set_texture", "set_texture is {of: <a structure that is a model, or a plot's "
                    "building>, from: <the texture its faces have now>, to: <the texture they get>}; a "
                    "decoration's picture is changed with set_sprite");
                continue;
            }

            if (pTarget == nullptr)
            {
                continue;
            }

            pTarget->swapped.insert(from);
            m_namedTextures.emplace(to, at + ".set_texture.to");
            body.push_back(indent + "evt.SetTexture(" + std::to_string(IdsLock::number(m_ids.cogs,
                "cog:" + textOf(value, "of") + ":" + from, 1)) + ", " + luaQuote(to) + ")");
        }
        else if (key == "show_actors" || key == "hide_actors")
        {
            const int group = isNumber ? static_cast<int>(number) : 0;

            if (group <= 0 || !m_actorGroups.contains(group))
            {
                add(at + "." + key, key + " is the `group` number of entries of `actors`; no entry has group "
                    + (isNumber ? whole : std::string("(nothing)")), "reference");
                continue;
            }

            if (key == "show_actors")
            {
                m_shownGroups.insert(group);
            }

            body.push_back(indent + "evt.SetMonGroupBit(" + std::to_string(group) + ", MonsterBits.Invisible, "
                + (key == "show_actors" ? "0" : "1") + ")");
        }
        else
        {
            add(at, "the effect `" + key + "` is not one an outdoor structure has: text, gold, add, subtract, "
                "set, autonote, qbit, clear_qbit, give_item, take_item, teleport, damage, cast, summon, show, hide, "
                "set_sprite, set_texture, show_actors, hide_actors or lua");
        }
    }
}

void OutdoorEventWords::lock(const YAML::Node &node, const std::string &path, const std::string &onceId,
    std::vector<std::string> &body)
{
    const bool once = textOf(node, "once") == "true";
    int onceVariable = 0;

    if (once)
    {
        // A map variable of its own remembers that it was used.
        onceVariable = IdsLock::number(m_ids.mapVars, onceId, 0);
        body.push_back("if IsAtLeast(MapVar(" + std::to_string(onceVariable) + "), 1) then return end");
    }

    const YAML::Node lockNode = childOf(node, "condition");

    if (lockNode.IsDefined())
    {
        body.push_back("if not (" + condition(lockNode, path + ".condition") + ") then");
        effects(childOf(node, "else_effects"), path + ".else_effects", "    ", body);

        if (childOf(node, "locked_text").IsDefined())
        {
            body.push_back("    " + statusLine(textOf(node, "locked_text")));
        }

        body.push_back("    return");
        body.push_back("end");

        if (textOf(lockNode, "consume") == "true")
        {
            const YAML::Node item = childOf(lockNode, "item");

            if (!item.IsDefined() || !item.IsScalar())
            {
                add(path + ".condition.consume", "`consume: true` takes the one `item` the condition names: name "
                    "one item beside it");
            }
            else
            {
                body.push_back("RemoveItem(" + std::to_string(namedNumber(item, "items", path + ".condition.item"))
                    + ")");
            }
        }
    }
    else if (childOf(node, "else_effects").IsDefined() || childOf(node, "locked_text").IsDefined())
    {
        add(path, "`else_effects` and `locked_text` say what happens when the `condition` does not hold: give the "
            "condition, or leave them out");
    }

    if (once)
    {
        body.push_back("SetValue(MapVar(" + std::to_string(onceVariable) + "), 1)");
    }

    // `lua_before`: steps that run once the lock is passed and before the house, the map or the chest (the
    // Hostel's film and the Hearts it takes before it opens).
    const std::string before = textOf(node, "lua_before");

    if (!before.empty())
    {
        std::istringstream lines(before);
        std::string line;

        while (std::getline(lines, line))
        {
            body.push_back(line);
        }
    }
}

void OutdoorEventWords::actions(const YAML::Node &node, const std::string &path, std::vector<std::string> &body)
{
    effects(childOf(node, "effects"), path + ".effects", "", body);
    const std::string lua = textOf(node, "lua");

    if (!lua.empty())
    {
        std::istringstream lines(lua);
        std::string line;

        while (std::getline(lines, line))
        {
            body.push_back(line);
        }
    }
}

void OutdoorEventWords::applyToModel(const std::string &id, Game::OutdoorBModel &model)
{
    const std::map<std::string, OutdoorEventTarget>::const_iterator found = m_targets.find(id);

    if (found == m_targets.end() || found->second.decoration)
    {
        return;
    }

    if (!found->second.follows.empty())
    {
        // A follower's faces carry the leader's number and start as the leader starts.
        const std::map<std::string, OutdoorEventTarget>::const_iterator leader = m_targets.find(found->second.follows);

        if (leader != m_targets.end() && !leader->second.decoration)
        {
            for (Game::OutdoorBModelFace &face : model.faces)
            {
                if (leader->second.toggled || leader->second.hidden)
                {
                    face.cogNumber = static_cast<uint16_t>(IdsLock::number(m_ids.cogs, "cog:" + leader->first, 1));
                }

                if (leader->second.hidden)
                {
                    face.attributes |= Game::faceAttributeBit(Game::FaceAttribute::Invisible)
                        | Game::faceAttributeBit(Game::FaceAttribute::Untouchable);
                }
            }
        }

        return;
    }

    const OutdoorEventTarget &target = found->second;
    std::set<std::string> present;

    for (Game::OutdoorBModelFace &face : model.faces)
    {
        const std::string texture = lowerCase(face.textureName);
        present.insert(texture);

        if (target.swapped.contains(texture))
        {
            face.cogNumber = static_cast<uint16_t>(IdsLock::number(m_ids.cogs, "cog:" + id + ":" + texture, 1));
        }
        else if (target.toggled || target.hidden)
        {
            face.cogNumber = static_cast<uint16_t>(IdsLock::number(m_ids.cogs, "cog:" + id, 1));
        }

        if (target.hidden)
        {
            face.attributes |= Game::faceAttributeBit(Game::FaceAttribute::Invisible)
                | Game::faceAttributeBit(Game::FaceAttribute::Untouchable);
        }
    }

    for (const std::string &texture : target.swapped)
    {
        if (!present.contains(texture))
        {
            std::string listed;

            for (const std::string &name : present)
            {
                listed += (listed.empty() ? "" : ", ") + name;
            }

            add(target.path, "an effect changes the texture " + texture + " of " + id + ", which has no face of "
                "that texture; its textures are " + listed, "reference");
        }
    }
}

void OutdoorEventWords::finish(std::vector<std::string> &warnings) const
{
    for (const std::pair<const std::string, OutdoorEventTarget> &entry : m_targets)
    {
        if (entry.second.hidden && !entry.second.toggled)
        {
            warnings.push_back("events: " + entry.first + " starts hidden and no event shows it: add the effect "
                "{show: " + entry.first + "} to what reveals it, or leave `hidden` out");
        }
    }

    for (const int group : m_hiddenGroups)
    {
        if (!m_shownGroups.contains(group))
        {
            warnings.push_back("events: the actors of group " + std::to_string(group) + " start hidden and no "
                "event shows them: add the effect {show_actors: " + std::to_string(group) + "} to what reveals "
                "them, or leave `hidden` out");
        }
    }
}
}
