#include "core/Authoring.h"

#include "core/CoreMath.h"
#include "core/History.h"
#include "core/Keys.h"
#include "core/Polygon.h"
#include "core/Schema.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <optional>
#include <set>
#include <sstream>

namespace OpenYAMM::Studio
{
namespace
{
// The child, or an undefined node (never yaml-cpp's invalid node of a missing key, which throws when asked its type).
YAML::Node childOf(const YAML::Node &node, const std::string &key)
{
    if (!node.IsDefined() || !node.IsMap())
    {
        return YAML::Node(YAML::NodeType::Undefined);
    }

    const YAML::Node child = node[key];
    return child.IsDefined() ? child : YAML::Node(YAML::NodeType::Undefined);
}

std::string textOf(const YAML::Node &node, const std::string &key)
{
    const YAML::Node child = childOf(node, key);
    return child.IsDefined() && child.IsScalar() ? child.Scalar() : std::string();
}

std::string lower(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return text;
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

std::string trimmed(const std::string &text)
{
    const size_t first = text.find_first_not_of(" \r");
    const size_t last = text.find_last_not_of(" \r");
    return first == std::string::npos ? std::string() : text.substr(first, last - first + 1);
}

// The reference map's row of map_stats.txt (its columns), or none with the reason.
std::optional<std::vector<std::string>> referenceRow(const std::string &reference,
    const std::filesystem::path &assetRoot, std::string &problem)
{
    if (assetRoot.empty())
    {
        problem = "no asset root: the reference map's row is not read";
        return std::nullopt;
    }

    std::string text;

    if (!readTextFile(assetRoot / "engine" / "data_tables" / "map_stats.txt", text))
    {
        problem = "the asset root has no engine/data_tables/map_stats.txt";
        return std::nullopt;
    }

    std::istringstream lines(text);
    const std::string wanted = lower(reference);

    for (std::string line; std::getline(lines, line);)
    {
        const std::vector<std::string> columns = splitTabs(line);

        if (columns.size() > 2 && lower(trimmed(columns[2])) == wanted)
        {
            return columns;
        }
    }

    problem = "map_stats.txt has no row for the reference map " + reference;
    return std::nullopt;
}

// A part of an issue's path: a property name or a position.
struct PathPart
{
    std::string name;
    long index = -1;
};

// "events[3].opens[1]" -> events, 3, opens, 1.
std::vector<PathPart> splitIssuePath(const std::string &path)
{
    std::vector<PathPart> parts;
    std::string name;

    for (size_t at = 0; at < path.size(); ++at)
    {
        const char character = path[at];

        if (character == '.' || character == '[')
        {
            if (!name.empty())
            {
                parts.push_back({name, -1});
                name.clear();
            }

            if (character == '[')
            {
                const size_t close = path.find(']', at);

                if (close == std::string::npos)
                {
                    return {};
                }

                const std::string digits = path.substr(at + 1, close - at - 1);

                if (digits.empty() || !std::all_of(digits.begin(), digits.end(), [](unsigned char c) { return std::isdigit(c); }))
                {
                    return {};
                }

                parts.push_back({"", std::stol(digits)});
                at = close;
            }
        }
        else
        {
            name += character;
        }
    }

    if (!name.empty())
    {
        parts.push_back({name, -1});
    }

    return parts;
}

std::string escapeSegment(const std::string &segment)
{
    std::string out;

    for (char character : segment)
    {
        out += character == '~' ? std::string("~0") : character == '/' ? std::string("~1") : std::string(1, character);
    }

    return out;
}

// Where an issue's path points in its file, as the patch op names it (keyed lists by key, lists of objects with ids
// by id, other lists by position), with the node there, its parent and the parent's schema.
struct Located
{
    bool found = false;
    std::string pointer;
    YAML::Node node;
    // The parent node and, when the last part is a property, its name.
    YAML::Node parent;
    std::string parentPointer;
    std::string property;
    long position = -1;
    YAML::Node parentSchema;
    // The top-level object the path is in (its id and list), when it has one.
    std::string objectId;
    std::string objectList;
    bool objectRequiresIt = false;
};

Located locateIssue(const Project &project, const std::string &fileName, const std::string &path)
{
    Located located;
    const std::map<std::string, ProjectFile>::const_iterator file = project.files.find(fileName);

    if (file == project.files.end())
    {
        return located;
    }

    const std::vector<PathPart> parts = splitIssuePath(path);

    if (parts.empty())
    {
        return located;
    }

    const SchemaSet &schemas = SchemaSet::builtIn();
    std::string schemaFile = file->second.schema;
    YAML::Node schema = schemas.root(schemaFile);
    YAML::Node node = file->second.document;
    std::string pointer;
    std::string lastName;
    size_t depth = 0;

    for (const PathPart &part : parts)
    {
        located.parent.reset(node);
        located.parentPointer = pointer;
        located.parentSchema.reset(schema);

        if (part.index < 0)
        {
            if (!node.IsMap())
            {
                return located;
            }

            // reset, never assign: assigning a yaml-cpp node writes into the schema node it holds.
            schema.reset(propertySchema(schemas, schema, part.name, schemaFile));
            node.reset(childOf(node, part.name));
            pointer += "/" + escapeSegment(part.name);
            located.property = part.name;
            located.position = -1;
            lastName = part.name;
        }
        else
        {
            if (!node.IsSequence() || static_cast<size_t>(part.index) >= node.size())
            {
                return located;
            }

            const ListKey key = listKeyOf(schema);
            const YAML::Node item = node[static_cast<size_t>(part.index)];
            std::string segment = std::to_string(part.index);

            if (key.keyed() && key.field == "id" && item.IsMap() && childOf(item, "id").IsDefined())
            {
                segment = item["id"].Scalar();

                if (depth == 1)
                {
                    located.objectId = segment;
                    located.objectList = lastName;
                }
            }
            else if (key.keyed() && key.field != "id")
            {
                segment = itemKeys(node, key)[static_cast<size_t>(part.index)];
            }

            schema.reset(itemsSchema(schemas, schema, schemaFile));
            node.reset(item);
            pointer += "/" + escapeSegment(segment);
            located.property.clear();
            located.position = part.index;
        }

        if (!node.IsDefined())
        {
            return located;
        }

        ++depth;
    }

    located.found = true;
    located.node.reset(node);
    located.pointer = pointer;
    const YAML::Node required = childOf(located.parentSchema, "required");

    if (!located.property.empty() && required.IsSequence())
    {
        for (const YAML::Node &name : required)
        {
            located.objectRequiresIt = located.objectRequiresIt || name.Scalar() == located.property;
        }
    }

    return located;
}

YAML::Node patchOp(const std::string &fileName, std::initializer_list<YAML::Node> steps)
{
    YAML::Node op(YAML::NodeType::Map);
    op["op"] = "patch";
    op["file"] = fileName;
    YAML::Node list(YAML::NodeType::Sequence);

    for (const YAML::Node &step : steps)
    {
        list.push_back(step);
    }

    op["patch"] = list;
    return op;
}

YAML::Node step(const std::string &kind, const std::string &path, const YAML::Node *pValue = nullptr)
{
    YAML::Node made(YAML::NodeType::Map);
    made["op"] = kind;
    made["path"] = path;

    if (pValue != nullptr)
    {
        made["value"] = YAML::Clone(*pValue);
    }

    return made;
}

YAML::Node oneOp(const YAML::Node &op)
{
    YAML::Node list(YAML::NodeType::Sequence);
    list.push_back(op);
    return list;
}

std::vector<IssueFix> referenceFixes(const Project &project, const ProjectIssue &issue, const std::string &missing)
{
    std::vector<IssueFix> fixes;
    const Located at = locateIssue(project, issue.file, issue.path);

    if (!at.found)
    {
        return fixes;
    }

    if (at.position >= 0 && at.parent.IsSequence())
    {
        // An entry of a list of ids: taken out, or the list dropped when it was the only one (a list of none is
        // refused by most schemas).
        if (at.parent.size() > 1)
        {
            fixes.push_back({"take " + missing + " out of the list",
                oneOp(patchOp(issue.file, {step("test", at.pointer, &at.node), step("remove", at.pointer)}))});
        }
        else
        {
            fixes.push_back({"drop the list (" + missing + " was its only entry)",
                oneOp(patchOp(issue.file, {step("test", at.parentPointer, &at.parent),
                    step("remove", at.parentPointer)}))});
        }
    }
    else if (!at.property.empty() && !at.objectRequiresIt)
    {
        fixes.push_back({"drop `" + at.property + "` (" + missing + ")",
            oneOp(patchOp(issue.file, {step("test", at.pointer, &at.node), step("remove", at.pointer)}))});
    }

    if (!at.objectId.empty() && at.parentPointer.find('/', 1) == at.parentPointer.rfind('/'))
    {
        // A word of the object itself: the object may not stand without what it names (an event's source, a door's
        // opening, a thing's room).
        YAML::Node remove(YAML::NodeType::Map);
        remove["op"] = "remove";
        remove["id"] = at.objectId;
        remove["file"] = issue.file;
        fixes.push_back({"remove " + at.objectId + " (it names " + missing + ")", oneOp(remove)});
    }

    return fixes;
}

// --- fixes of S5b2 (geometry where the fix is unambiguous, a missing id with one obvious target, a thing outside its
// room) -------------------------------------------------------------------------------------------------------------

// Every id the project's source files give (a map's `id`, at any depth), by file.
void collectIds(const YAML::Node &node, std::set<std::string> &ids, int depth)
{
    if (depth > 8)
    {
        return;
    }

    if (node.IsMap())
    {
        const YAML::Node id = childOf(node, "id");

        if (id.IsDefined() && id.IsScalar() && !id.Scalar().empty())
        {
            ids.insert(id.Scalar());
        }

        for (YAML::const_iterator field = node.begin(); field != node.end(); ++field)
        {
            if (field->second.IsMap() || field->second.IsSequence())
            {
                collectIds(field->second, ids, depth + 1);
            }
        }
    }
    else if (node.IsSequence())
    {
        for (const YAML::Node &item : node)
        {
            if (item.IsMap() || item.IsSequence())
            {
                collectIds(item, ids, depth + 1);
            }
        }
    }
}

size_t editDistance(const std::string &first, const std::string &second)
{
    std::vector<size_t> row(second.size() + 1);

    for (size_t column = 0; column <= second.size(); ++column)
    {
        row[column] = column;
    }

    for (size_t line = 1; line <= first.size(); ++line)
    {
        size_t diagonal = row[0];
        row[0] = line;

        for (size_t column = 1; column <= second.size(); ++column)
        {
            const size_t above = row[column];
            row[column] = std::min({row[column] + 1, row[column - 1] + 1,
                diagonal + (first[line - 1] == second[column - 1] ? 0 : 1)});
            diagonal = above;
        }
    }

    return row[second.size()];
}

// A reference to an id the project lacks, where one id is the obvious one meant: of the ids of the same kind (the part
// before `:`), the one nearer in spelling than every other (within two letters), else the only id of that kind at all.
// Its fix names that id instead.
std::vector<IssueFix> obviousTargetFixes(const Project &project, const ProjectIssue &issue, const std::string &missing)
{
    const size_t colon = missing.find(':');
    const Located at = locateIssue(project, issue.file, issue.path);

    if (colon == std::string::npos || !at.found || !at.node.IsScalar() || at.node.Scalar() != missing)
    {
        return {};
    }

    std::set<std::string> ids;

    for (const std::pair<const std::string, ProjectFile> &file : project.files)
    {
        if (isSourceFile(file.first))
        {
            collectIds(file.second.document, ids, 0);
        }
    }

    // An entry of a list of ids: an id the list names already is not what was meant.
    std::set<std::string> named;

    if (at.position >= 0 && at.parent.IsSequence())
    {
        for (const YAML::Node &entry : at.parent)
        {
            if (entry.IsScalar())
            {
                named.insert(entry.Scalar());
            }
        }
    }

    const std::string kind = missing.substr(0, colon + 1);
    std::vector<std::string> sameKind;
    // The nearest spellings (within two letters): obvious only when one is nearer than every other.
    std::vector<std::string> near;
    size_t nearest = 3;

    for (const std::string &id : ids)
    {
        if (id.rfind(kind, 0) == 0 && id != missing && !named.contains(id))
        {
            sameKind.push_back(id);
            const size_t distance = editDistance(id, missing);

            if (distance < nearest)
            {
                nearest = distance;
                near = {id};
            }
            else if (distance == nearest && nearest <= 2)
            {
                near.push_back(id);
            }
        }
    }

    std::string target;
    std::string why;

    if (near.size() == 1)
    {
        target = near[0];
        why = "a near spelling";
    }
    else if (near.empty() && sameKind.size() == 1)
    {
        target = sameKind[0];
        why = "the only " + kind.substr(0, kind.size() - 1) + " of the project";
    }

    if (target.empty())
    {
        return {};
    }

    const YAML::Node value(target);
    return {{"name " + target + " instead (" + why + ")",
        oneOp(patchOp(issue.file, {step("test", at.pointer, &at.node), step("replace", at.pointer, &value)}))}};
}

// The points of a list of [x, y] (or [x, y, z]) points; false when an item is not such a point.
bool pointList(const YAML::Node &node, std::vector<Point2> &points)
{
    points.clear();

    if (!node.IsSequence())
    {
        return false;
    }

    for (const YAML::Node &item : node)
    {
        if (!item.IsSequence() || item.size() < 2 || !item[0].IsScalar() || !item[1].IsScalar())
        {
            return false;
        }

        try
        {
            points.push_back({item[0].as<double>(), item[1].as<double>()});
        }
        catch (const YAML::Exception &)
        {
            return false;
        }
    }

    return true;
}

// The list of points an issue is about: the located node, or its `outline` (a level's issue names the level).
struct LocatedPoints
{
    YAML::Node node;
    std::string pointer;
    std::vector<Point2> points;
};

std::optional<LocatedPoints> issuePoints(const Located &at)
{
    LocatedPoints found;

    if (at.node.IsSequence())
    {
        found.node.reset(at.node);
        found.pointer = at.pointer;
    }
    else if (at.node.IsMap() && childOf(at.node, "outline").IsSequence())
    {
        found.node.reset(childOf(at.node, "outline"));
        found.pointer = at.pointer + "/outline";
    }
    else
    {
        return std::nullopt;
    }

    if (!pointList(found.node, found.points))
    {
        return std::nullopt;
    }

    return found;
}

// An outline that does not stand as given, where one change makes it stand: repeated points dropped (a corner given
// twice in a row, or the first given again at the end), and in rooms.yml (whose outlines run counter-clockwise) the
// points reversed when they run clockwise. Offered only when the result is a simple outline the check accepts and the
// given one is not.
std::vector<IssueFix> outlineFixes(const Project &project, const ProjectIssue &issue)
{
    const Located at = locateIssue(project, issue.file, issue.path);

    if (!at.found)
    {
        return {};
    }

    const std::optional<LocatedPoints> outline = issuePoints(at);

    if (!outline || outline->points.size() < 3)
    {
        return {};
    }

    const bool counterClockwise = issue.file == "rooms.yml";
    const std::vector<Point2> &given = outline->points;
    const auto stands = [counterClockwise](const std::vector<Point2> &points)
    {
        return points.size() >= 3 && polygonIsSimple(points)
            && (counterClockwise ? polygonDoubleArea(points) > 0.0 : std::abs(polygonDoubleArea(points)) > 0.0);
    };

    if (stands(given))
    {
        return {};
    }

    // Repeats dropped: each point that lies on the one before it (the first counts as after the last).
    std::vector<size_t> kept;

    for (size_t index = 0; index < given.size(); ++index)
    {
        const Point2 &previous = kept.empty() ? given[index] : given[kept.back()];

        if (kept.empty() || oy::hypot(previous[0] - given[index][0], previous[1] - given[index][1]) >= 1.0)
        {
            kept.push_back(index);
        }
    }

    while (kept.size() > 1
        && oy::hypot(given[kept.back()][0] - given[kept[0]][0], given[kept.back()][1] - given[kept[0]][1]) < 1.0)
    {
        kept.pop_back();
    }

    const bool dropped = kept.size() != given.size();
    std::vector<Point2> points;

    for (const size_t index : kept)
    {
        points.push_back(given[index]);
    }

    bool reversed = false;

    if (counterClockwise && points.size() >= 3 && polygonDoubleArea(points) < 0.0)
    {
        // The first point stays first; the rest run the other way round.
        std::reverse(kept.begin() + 1, kept.end());
        std::reverse(points.begin() + 1, points.end());
        reversed = true;
    }

    if ((!dropped && !reversed) || !stands(points))
    {
        return {};
    }

    YAML::Node value(YAML::NodeType::Sequence);

    for (const size_t index : kept)
    {
        value.push_back(YAML::Clone(outline->node[index]));
    }

    const size_t repeats = given.size() - kept.size();
    const std::string drop = repeats == 1 ? "drop the repeated point" : "drop the " + std::to_string(repeats)
        + " repeated points";
    const std::string label = dropped && reversed ? drop + " and reverse the outline (it ran clockwise)"
        : dropped ? drop + " of the outline" : "reverse the outline's points (it ran clockwise)";
    return {{label, oneOp(patchOp(issue.file, {step("test", outline->pointer, &outline->node),
        step("replace", outline->pointer, &value)}))}};
}

// A path (a corridor's centre line) with a point given twice in a row: the repeat dropped.
std::vector<IssueFix> pathFixes(const Project &project, const ProjectIssue &issue)
{
    const Located at = locateIssue(project, issue.file, issue.path);

    if (!at.found || at.property != "path" || !at.node.IsSequence())
    {
        return {};
    }

    std::vector<Point2> given;

    if (!pointList(at.node, given) || given.size() < 2)
    {
        return {};
    }

    YAML::Node value(YAML::NodeType::Sequence);
    size_t kept = 0;

    for (size_t index = 0; index < given.size(); ++index)
    {
        if (index > 0 && oy::hypot(given[index][0] - given[index - 1][0], given[index][1] - given[index - 1][1]) < 1.0)
        {
            continue;
        }

        value.push_back(YAML::Clone(at.node[index]));
        ++kept;
    }

    if (kept == given.size() || kept < 2)
    {
        return {};
    }

    const size_t repeats = given.size() - kept;
    return {{repeats == 1 ? "drop the repeated point of the path"
                          : "drop the " + std::to_string(repeats) + " repeated points of the path",
        oneOp(patchOp(issue.file, {step("test", at.pointer, &at.node), step("replace", at.pointer, &value)}))}};
}

// A number after `after` in a message ("... share only 448 units ..."), or none.
std::optional<double> numberAfter(const std::string &message, const std::string &after)
{
    const size_t at = message.find(after);

    if (at == std::string::npos)
    {
        return std::nullopt;
    }

    const size_t begin = at + after.size();
    size_t end = begin;

    while (end < message.size() && (std::isdigit(static_cast<unsigned char>(message[end])) || message[end] == '.'
        || (end == begin && message[end] == '-')))
    {
        ++end;
    }

    if (end == begin)
    {
        return std::nullopt;
    }

    try
    {
        return std::stod(message.substr(begin, end - begin));
    }
    catch (const std::exception &)
    {
        return std::nullopt;
    }
}

// An opening wider than the wall its two rooms share: narrowed to the shared wall less its margins, or made `full`.
std::vector<IssueFix> openingWidthFixes(const Project &project, const ProjectIssue &issue)
{
    const std::optional<double> shared = numberAfter(issue.message, "share only ");
    const Located at = locateIssue(project, issue.file, issue.path);

    if (!shared || !at.found || at.property != "width")
    {
        return {};
    }

    std::vector<IssueFix> fixes;
    const double margin = 16.0;
    const int narrower = static_cast<int>(std::floor((*shared - 2.0 * margin) / 8.0)) * 8;

    if (narrower >= 32)
    {
        const YAML::Node value(narrower);
        fixes.push_back({"narrow it to " + std::to_string(narrower) + " (the shared wall less 16 at each side)",
            oneOp(patchOp(issue.file, {step("test", at.pointer, &at.node), step("replace", at.pointer, &value)}))});
    }

    if (*shared >= 32.0)
    {
        const YAML::Node value("full");
        fixes.push_back({"make it `width: full` (the whole shared stretch)",
            oneOp(patchOp(issue.file, {step("test", at.pointer, &at.node), step("replace", at.pointer, &value)}))});
    }

    return fixes;
}

// A thing whose place is not inside its room: given the room it stands in (when exactly one room's outline holds the
// place), or brought inside its own room (to the nearest place 32 inside its wall).
std::vector<IssueFix> outsideRoomFixes(const Project &project, const ProjectIssue &issue)
{
    const std::string prefix = "the position [";
    const size_t close = issue.message.find("] is not inside room ");
    const Located at = locateIssue(project, issue.file, issue.path);

    if (issue.message.rfind(prefix, 0) != 0 || close == std::string::npos || !at.found || !at.node.IsMap())
    {
        return {};
    }

    const std::string roomId = issue.message.substr(close + std::string("] is not inside room ").size());
    const std::string place = issue.message.substr(prefix.size(), close - prefix.size());
    const size_t comma = place.find(',');
    Point2 point = {};

    try
    {
        point = {std::stod(place.substr(0, comma)), std::stod(place.substr(comma + 1))};
    }
    catch (const std::exception &)
    {
        return {};
    }

    const std::string what = at.objectId.empty() ? issue.path : at.objectId;
    std::vector<IssueFix> fixes;
    std::vector<Point2> own;
    std::vector<std::string> holding;

    for (const YAML::Node &room : childOf(project.document("rooms.yml"), "rooms"))
    {
        std::vector<Point2> outline;

        if (!pointList(childOf(room, "outline"), outline) || outline.size() < 3)
        {
            continue;
        }

        if (textOf(room, "id") == roomId)
        {
            own = outline;
        }
        else if (pointInPolygon(outline, point, 1.0))
        {
            holding.push_back(textOf(room, "id"));
        }
    }

    const YAML::Node room = childOf(at.node, "room");

    if (holding.size() == 1 && room.IsDefined() && room.IsScalar())
    {
        const YAML::Node value(holding[0]);
        fixes.push_back({"give " + what + " the room it stands in (" + holding[0] + ")",
            oneOp(patchOp(issue.file, {step("test", at.pointer + "/room", &room),
                step("replace", at.pointer + "/room", &value)}))});
    }

    if (own.size() >= 3 && polygonDoubleArea(own) > 0.0)
    {
        // The nearest point of the walls, and from it 32 into the room (left of a counter-clockwise wall).
        double best = -1.0;
        Point2 inside = {};

        for (size_t index = 0; index < own.size(); ++index)
        {
            const Point2 &a = own[index];
            const Point2 &b = own[(index + 1) % own.size()];
            const double dx = b[0] - a[0];
            const double dy = b[1] - a[1];
            const double length = oy::hypot(dx, dy);

            if (length < 1.0)
            {
                continue;
            }

            const double share = std::clamp(((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / (length * length),
                0.0, 1.0);
            const Point2 near = {a[0] + dx * share, a[1] + dy * share};
            const double distance = oy::hypot(point[0] - near[0], point[1] - near[1]);
            const Point2 candidate = {std::round(near[0] - dy / length * 32.0),
                std::round(near[1] + dx / length * 32.0)};

            if ((best < 0.0 || distance < best) && pointInPolygon(own, candidate, 8.0))
            {
                best = distance;
                inside = candidate;
            }
        }

        const std::string moveLabel = "move " + what + " inside " + roomId + ", to ["
            + std::to_string(static_cast<int64_t>(inside[0])) + ", "
            + std::to_string(static_cast<int64_t>(inside[1])) + "]";
        YAML::Node value(YAML::NodeType::Sequence);
        value.SetStyle(YAML::EmitterStyle::Flow);
        value.push_back(static_cast<int64_t>(inside[0]));
        value.push_back(static_cast<int64_t>(inside[1]));
        const YAML::Node given = childOf(at.node, "at");
        const YAML::Node offset = childOf(at.node, "offset");

        if (best >= 0.0 && given.IsDefined())
        {
            if (given.IsSequence() && given.size() > 2)
            {
                value.push_back(YAML::Clone(given[2]));
            }

            fixes.push_back({moveLabel,
                oneOp(patchOp(issue.file, {step("test", at.pointer + "/at", &given),
                    step("replace", at.pointer + "/at", &value)}))});
        }
        else if (best >= 0.0 && offset.IsDefined())
        {
            fixes.push_back({moveLabel,
                oneOp(patchOp(issue.file, {step("test", at.pointer + "/offset", &offset),
                    step("remove", at.pointer + "/offset"), step("add", at.pointer + "/at", &value)}))});
        }
    }

    return fixes;
}

// A list's entry that repeats one before it (`floor_points` with a point twice): the entry dropped.
std::vector<IssueFix> repeatedEntryFixes(const Project &project, const ProjectIssue &issue)
{
    const Located at = locateIssue(project, issue.file, issue.path);

    if (!at.found || at.position < 0 || !at.parent.IsSequence() || at.parent.size() < 2)
    {
        return {};
    }

    return {{"drop the repeated point",
        oneOp(patchOp(issue.file, {step("test", at.pointer, &at.node), step("remove", at.pointer)}))}};
}
}

MapCard resolveMapCard(const Project &project, const std::filesystem::path &assetRoot)
{
    MapCard card;
    const YAML::Node stats = childOf(project.document("project.yml"), "map_stats");
    const YAML::Node slots = childOf(stats, "slots");
    const std::string reference = textOf(stats, "reference");
    std::optional<std::vector<std::string>> row;

    if (!reference.empty())
    {
        row = referenceRow(reference, assetRoot, card.referenceProblem);
    }

    const std::string rowName = "map_stats.txt row of " + reference;

    for (int slot = 1; slot <= 3; ++slot)
    {
        CardSlot made;
        made.slot = slot;
        const YAML::Node written = slots.IsSequence() && slots.size() >= static_cast<size_t>(slot)
            ? slots[static_cast<size_t>(slot - 1)] : YAML::Node(YAML::NodeType::Undefined);

        if (written.IsDefined() && written.IsMap())
        {
            made.monster = textOf(written, "monster");
            made.picture = made.monster;
            made.tier = textOf(written, "tier");
            const YAML::Node perMarker = childOf(written, "per_marker");

            if (perMarker.IsSequence() && perMarker.size() == 2)
            {
                made.count = perMarker[0].Scalar() + "-" + perMarker[1].Scalar();
            }

            made.weight = textOf(written, "weight");
            made.source = "written";
            made.from = "project.yml map_stats.slots";
        }
        else if (row)
        {
            const size_t base = 16 + static_cast<size_t>(slot - 1) * 4;

            if (row->size() > base + 3)
            {
                made.picture = trimmed((*row)[base]);
                made.monster = trimmed((*row)[base + 1]);
                made.tier = trimmed((*row)[base + 2]);
                made.count = trimmed((*row)[base + 3]);
                made.weight = row->size() > 12 + static_cast<size_t>(slot) ? trimmed((*row)[12 + static_cast<size_t>(slot)])
                    : std::string();
            }

            made.source = "reference";
            made.from = rowName;
        }
        else
        {
            continue;
        }

        if (!made.monster.empty() && made.monster != "0")
        {
            card.slots.push_back(made);
        }
    }

    if (row)
    {
        // The columns a card may write (core/Install.cpp upsertMapStatsRow), taken from the reference when it does
        // not.
        const std::vector<std::pair<const char *, size_t>> columns = {
            {"perception_difficulty", 5}, {"refill_days", 6}, {"steal_fine", 8}, {"lock_difficulty", 9},
            {"trap_dice", 10}, {"treasure_level", 11}, {"encounter_chance", 12}, {"music", 28}, {"environment", 29}};

        for (const std::pair<const char *, size_t> &column : columns)
        {
            const bool written = childOf(stats, column.first).IsDefined()
                || (std::string(column.first) == "lock_difficulty" && childOf(stats, "disarm_difficulty").IsDefined());

            if (!written && row->size() > column.second)
            {
                card.fromReference.push_back({column.first, trimmed((*row)[column.second]), rowName});
            }
        }
    }

    return card;
}

std::vector<IssueFix> issueFixes(const Project &project, const ProjectIssue &issue)
{
    const std::string &message = issue.message;
    const std::string nothing = "nothing in the project has the id ";

    if (issue.code == "reference" && message.rfind(nothing, 0) == 0)
    {
        // The obvious target first (S5b2), then taking the reference out.
        const std::string missing = message.substr(nothing.size());
        std::vector<IssueFix> fixes = obviousTargetFixes(project, issue, missing);
        std::vector<IssueFix> others = referenceFixes(project, issue, missing);
        fixes.insert(fixes.end(), others.begin(), others.end());
        return fixes;
    }

    // Geometry (S5b2): only where one change makes it stand.
    if (issue.code == "geometry")
    {
        if (message.find("wide but the two rooms share only ") != std::string::npos)
        {
            return openingWidthFixes(project, issue);
        }

        if (message.rfind("the position [", 0) == 0 && message.find("] is not inside room ") != std::string::npos)
        {
            return outsideRoomFixes(project, issue);
        }

        if (message.find("_points` has the point ") != std::string::npos && message.ends_with(" twice"))
        {
            return repeatedEntryFixes(project, issue);
        }

        if (message == "the path repeats a point")
        {
            return pathFixes(project, issue);
        }

        if (message.find("outline") != std::string::npos)
        {
            return outlineFixes(project, issue);
        }
    }

    // A word on the wrong kind (core/Kinds.h): dropped.
    if (issue.code == "kind")
    {
        const Located at = locateIssue(project, issue.file, issue.path);

        if (at.found && !at.property.empty() && !at.objectRequiresIt)
        {
            return {{"drop `" + at.property + "`",
                oneOp(patchOp(issue.file, {step("test", at.pointer, &at.node), step("remove", at.pointer)}))}};
        }

        return {};
    }

    // A map variable named but not declared: declared.
    const std::string variable = "the variable ";
    const std::string undeclared = " is not declared in wiring.yml variables";

    if (issue.code == "reference" && message.rfind(variable, 0) == 0 && message.ends_with(undeclared))
    {
        const std::string name = message.substr(variable.size(), message.size() - variable.size() - undeclared.size());
        const YAML::Node value(name);
        const bool hasList = childOf(project.document("wiring.yml"), "variables").IsSequence();
        YAML::Node list(YAML::NodeType::Sequence);
        list.push_back(name);
        return {{"declare " + name + " in wiring.yml variables",
            oneOp(hasList ? patchOp("wiring.yml", {step("add", "/variables/-", &value)})
                          : patchOp("wiring.yml", {step("add", "/variables", &list)}))}};
    }

    // A room that realises no plan space: it realises one the plan has no room for, or the plan gains its space.
    const std::string realises = "the room realises no space of plan.yml (";

    if (issue.file == "rooms.yml" && message.rfind(realises, 0) == 0)
    {
        const size_t close = message.find(" is not there)");
        const Located at = locateIssue(project, "rooms.yml", issue.path);
        const std::string roomId = at.found ? textOf(at.node, "id") : std::string();

        if (close == std::string::npos || roomId.empty())
        {
            return {};
        }

        const std::string wanted = message.substr(realises.size(), close - realises.size());
        std::set<std::string> realised;

        for (const YAML::Node &room : childOf(project.document("rooms.yml"), "rooms"))
        {
            realised.insert(textOf(room, "space").empty() ? textOf(room, "id") : textOf(room, "space"));
        }

        std::vector<IssueFix> fixes;

        for (const YAML::Node &space : childOf(project.document("plan.yml"), "spaces"))
        {
            const std::string spaceId = textOf(space, "id");

            if (!spaceId.empty() && !realised.contains(spaceId) && fixes.size() < 3)
            {
                YAML::Node op(YAML::NodeType::Map);
                op["op"] = "set";
                op["id"] = roomId;
                op["file"] = "rooms.yml";
                op["fields"]["space"] = spaceId;
                fixes.push_back({"make " + roomId + " the room of " + spaceId
                    + (textOf(space, "name").empty() ? std::string() : " (" + textOf(space, "name") + ")"), oneOp(op)});
            }
        }

        YAML::Node add(YAML::NodeType::Map);
        add["op"] = "add";
        add["to"] = "spaces";
        add["file"] = "plan.yml";
        add["value"]["id"] = wanted;
        add["value"]["kind"] = "room";

        if (!textOf(at.node, "name").empty())
        {
            add["value"]["name"] = textOf(at.node, "name");
        }

        fixes.push_back({"add " + wanted + " to the plan as a space", oneOp(add)});
        return fixes;
    }

    // No party start: the first room.
    if (issue.file == "objects.yml" && issue.path == "start" && message.rfind("the map needs a party start", 0) == 0)
    {
        const YAML::Node rooms = childOf(project.document("rooms.yml"), "rooms");

        if (rooms.IsSequence() && rooms.size() > 0 && !textOf(rooms[0], "id").empty())
        {
            YAML::Node op(YAML::NodeType::Map);
            op["op"] = "set_value";
            op["file"] = "objects.yml";
            op["path"] = "start";
            YAML::Node start(YAML::NodeType::Map);
            start["room"] = rooms[0]["id"].Scalar();
            op["value"] = start;
            return {{"start the party in " + rooms[0]["id"].Scalar(), oneOp(op)}};
        }
    }

    return {};
}

bool sourceTextsAtEntry(
    const std::filesystem::path &projectRoot,
    const Project &current,
    int sequence,
    bool before,
    std::map<std::string, std::string> &texts,
    std::string &errorMessage)
{
    const HistoryHead head = readHistoryHead(projectRoot);

    if (sequence < head.first || sequence > head.count)
    {
        errorMessage = "the history has no entry " + std::to_string(sequence) + " (it keeps " + std::to_string(head.first)
            + " to " + std::to_string(head.count) + ")";
        return false;
    }

    // Each file as the earliest entry after the wanted state found it (its `before`); the current text when no later
    // entry changed it.
    std::map<std::string, std::optional<std::string>> taken;

    for (int later = before ? sequence : sequence + 1; later <= head.count; ++later)
    {
        StoredHistoryEntry entry;

        if (!readHistoryEntry(projectRoot, later, true, entry, errorMessage))
        {
            return false;
        }

        for (const std::pair<const std::string, std::optional<std::string>> &file : entry.before)
        {
            taken.emplace(file.first, file.second);
        }
    }

    texts.clear();

    for (const std::pair<const std::string, ProjectFile> &file : current.files)
    {
        if (isSourceFile(file.first) && !taken.contains(file.first))
        {
            texts[file.first] = file.second.text;
        }
    }

    for (const std::pair<const std::string, std::optional<std::string>> &file : taken)
    {
        if (file.second)
        {
            texts[file.first] = *file.second;
        }
    }

    // The record and the review are not part of the history: the current ones stand beside the old sources.
    for (const std::pair<const std::string, ProjectFile> &file : current.files)
    {
        if (!isSourceFile(file.first))
        {
            texts[file.first] = file.second.text;
        }
    }

    return true;
}

bool projectFromTexts(
    const std::filesystem::path &root,
    const std::map<std::string, std::string> &texts,
    Project &project,
    std::string &errorMessage)
{
    project = {};
    project.root = root;

    for (const ProjectFileKind &kind : projectFileKinds())
    {
        const std::map<std::string, std::string>::const_iterator text = texts.find(kind.pName);

        if (text == texts.end())
        {
            continue;
        }

        ProjectFile file;
        file.name = kind.pName;
        file.schema = kind.pSchema;
        file.text = text->second;

        try
        {
            file.document = YAML::Load(file.text);
        }
        catch (const YAML::Exception &exception)
        {
            errorMessage = std::string(kind.pName) + " is not valid YAML: " + exception.what();
            return false;
        }

        project.files[file.name] = file;
    }

    return project.has("project.yml");
}
}
