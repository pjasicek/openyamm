#include "core/Ops.h"

#include "core/CanonicalYaml.h"
#include "core/History.h"
#include "core/IndoorBuild.h"
#include "core/IndoorLowering.h"
#include "core/Json.h"
#include "core/Keys.h"
#include "core/Pins.h"

#include <algorithm>
#include <cerrno>
#include <chrono>
#include <cstdio>
#include <ctime>
#include <functional>
#include <map>
#include <regex>
#include <set>
#include <thread>

#if defined(__unix__) || defined(__APPLE__)
#include <csignal>
#include <unistd.h>
#endif

namespace OpenYAMM::Studio
{
namespace
{
// A list of objects with ids under a source file's top level: what `add` adds to (S5_BROWSER_EDITOR.md 2.6 item 1:
// every top-level list whose items have an `id`, read from the schemas, so a list is editable the day its schema
// lands).
struct Collection
{
    std::string name;
    std::string singular;
    std::string file;
    // The id prefix of a new object when the list has none to copy (`decorations` -> deco).
    std::string prefix;
};

// Singular names and id prefixes the plain rule (drop the "s") does not give.
const std::map<std::string, std::pair<std::string, std::string>> &collectionWords()
{
    static const std::map<std::string, std::pair<std::string, std::string>> words = {
        {"switches", {"switch", "switch"}},
        {"decorations", {"decoration", "deco"}},
        {"openings", {"opening", "open"}},
        {"events", {"event", "evt"}},
        {"points_of_interest", {"poi", "poi"}},
        {"height_bands", {"height_band", "band"}},
        {"containers", {"container", "box"}},
        {"set_pieces", {"set_piece", "set"}},
        {"sightlines", {"sightline", "sightline"}},
        {"teleport_sets", {"teleport_set", "teleport"}},
        {"lock_groups", {"lock_group", "lock"}},
        {"neighbours", {"neighbour", "exit"}},
        {"scatter", {"scatter", "scatter"}},
        {"structures", {"structure", "thing"}},
        {"areas", {"area", "pop"}},
        {"actors", {"actor", "pop"}},
    };
    return words;
}

const std::vector<Collection> &collections()
{
    static const std::vector<Collection> table = []()
    {
        std::vector<Collection> made;
        const SchemaSet &schemas = SchemaSet::builtIn();

        for (const ProjectFileKind &kind : projectFileKinds())
        {
            if (kind.fileClass != ProjectFileClass::Source || !schemas.has(kind.pSchema))
            {
                continue;
            }

            const YAML::Node properties = schemas.root(kind.pSchema)["properties"];

            for (YAML::const_iterator property = properties.begin(); property != properties.end(); ++property)
            {
                std::string fileName = kind.pSchema;
                const YAML::Node list = schemas.resolve(property->second, fileName);

                if (!list.IsMap() || !list["type"] || list["type"].Scalar() != "array")
                {
                    continue;
                }

                const YAML::Node items = itemsSchema(schemas, list, fileName);

                if (!items.IsDefined() || !items["properties"] || !items["properties"]["id"])
                {
                    continue;
                }

                Collection collection;
                collection.name = property->first.Scalar();
                collection.file = kind.pName;
                const auto word = collectionWords().find(collection.name);

                if (word != collectionWords().end())
                {
                    collection.singular = word->second.first;
                    collection.prefix = word->second.second;
                }
                else
                {
                    collection.singular = collection.name.ends_with("s")
                        ? collection.name.substr(0, collection.name.size() - 1) : collection.name;
                    collection.prefix = collection.singular;
                }

                made.push_back(collection);
            }
        }

        return made;
    }();
    return table;
}

std::string scalarText(const YAML::Node &node, const std::string &key);

// The collection `name` names (plural or singular). Two files may have a list of one name (`events` in wiring.yml
// and sketch.yml): `file`, or else the file the project has, or else the project's kind (sketch.yml is outdoor's),
// decides.
const Collection *findCollection(const std::string &name, const std::string &file, const Project &project)
{
    const bool outdoor = scalarText(project.document("project.yml"), "kind") == "outdoor";
    const auto rank = [&project, outdoor](const Collection &collection)
    {
        return (project.has(collection.file) ? 2 : 0) + ((collection.file == "sketch.yml") == outdoor ? 1 : 0);
    };
    const Collection *pFound = nullptr;

    for (const Collection &collection : collections())
    {
        if ((name == collection.name || name == collection.singular) && (file.empty() || file == collection.file))
        {
            if (pFound == nullptr || rank(collection) > rank(*pFound))
            {
                pFound = &collection;
            }
        }
    }

    return pFound;
}

std::string collectionNames()
{
    std::set<std::string> names;

    for (const Collection &collection : collections())
    {
        names.insert(collection.name);
    }

    std::string text;

    for (const std::string &name : names)
    {
        text += (text.empty() ? "" : ", ") + name;
    }

    return text;
}

YAML::Node childOf(const YAML::Node &node, const std::string &key)
{
    return node.IsDefined() && node.IsMap() ? node[key] : YAML::Node(YAML::NodeType::Undefined);
}

std::string scalarText(const YAML::Node &node, const std::string &key)
{
    const YAML::Node child = childOf(node, key);
    return child.IsDefined() && child.IsScalar() ? child.Scalar() : std::string();
}

// The id objects of a file: every map with an `id`, in lists directly under the root.
std::map<std::string, YAML::Node> idObjects(const YAML::Node &document)
{
    std::map<std::string, YAML::Node> objects;

    if (!document.IsDefined() || !document.IsMap())
    {
        return objects;
    }

    for (YAML::const_iterator iterator = document.begin(); iterator != document.end(); ++iterator)
    {
        if (!iterator->second.IsSequence())
        {
            continue;
        }

        // A copy of the node: `iterator->second` lives in a temporary the loop would outlive.
        const YAML::Node list = iterator->second;

        for (const YAML::Node &item : list)
        {
            const YAML::Node id = childOf(item, "id");

            if (id.IsDefined() && id.IsScalar())
            {
                objects.emplace(id.Scalar(), item);
            }
        }
    }

    return objects;
}

// --- objects as units of change (revert, rebase, the hand-edit mark) ----------------------------------------------

// One object of a source file: an item with an id of a top-level list (`rooms.yml#room:hall`), or a top-level key
// whose value is not such a list (`project.yml#/map_stats`).
struct Unit
{
    // The top-level key the unit is in (its list's, or its own).
    std::string key;
    bool item = false;
    size_t index = 0;
    YAML::Node node;

    Unit(std::string listKey, bool isItem, size_t position, const YAML::Node &value)
        : key(std::move(listKey))
        , item(isItem)
        , index(position)
        , node(value)
    {
    }

    Unit(const Unit &other) = default;
    // Rebinds the handle: assigning a yaml-cpp node that holds one would overwrite the document's own node.
    Unit &operator=(const Unit &other) = delete;
};

bool isIdList(const YAML::Node &value)
{
    if (!value.IsSequence() || value.size() == 0)
    {
        return false;
    }

    for (const YAML::Node &item : value)
    {
        const YAML::Node id = childOf(item, "id");

        if (!id.IsDefined() || !id.IsScalar())
        {
            return false;
        }
    }

    return true;
}

std::map<std::string, Unit> unitsOf(const std::string &file, const YAML::Node &document)
{
    std::map<std::string, Unit> units;

    if (!document.IsDefined() || !document.IsMap())
    {
        return units;
    }

    for (YAML::const_iterator iterator = document.begin(); iterator != document.end(); ++iterator)
    {
        const std::string key = iterator->first.Scalar();
        // A copy of the node: `iterator->second` lives in a temporary the loop would outlive.
        const YAML::Node value = iterator->second;

        if (isIdList(value))
        {
            for (size_t index = 0; index < value.size(); ++index)
            {
                // An id is unique in its file, but a sketch's points and views may share one: the second is named by
                // its list too.
                const std::string id = value[index]["id"].Scalar();

                if (!units.emplace(file + "#" + id, Unit(key, true, index, value[index])).second)
                {
                    units.emplace(file + "#/" + key + "/" + id, Unit(key, true, index, value[index]));
                }
            }
        }
        else
        {
            units.emplace(file + "#/" + key, Unit(key, false, 0, value));
        }
    }

    return units;
}

bool sameUnit(const Unit *pFirst, const Unit *pSecond)
{
    if (pFirst == nullptr || pSecond == nullptr)
    {
        return pFirst == pSecond;
    }

    std::string where;
    return sameYaml(pFirst->node, pSecond->node, where);
}

const Unit *unitIn(const std::map<std::string, Unit> &units, const std::string &name)
{
    const std::map<std::string, Unit>::const_iterator found = units.find(name);
    return found != units.end() ? &found->second : nullptr;
}

// The units of one file that differ between two documents.
std::vector<std::string> changedUnits(const std::string &file, const YAML::Node &before, const YAML::Node &after)
{
    std::vector<std::string> changed;

    if (before.IsDefined() && after.IsDefined() && before.is(after))
    {
        return changed;
    }

    const std::map<std::string, Unit> first = unitsOf(file, before);
    const std::map<std::string, Unit> second = unitsOf(file, after);
    std::set<std::string> names;

    for (const auto &unit : first)
    {
        names.insert(unit.first);
    }

    for (const auto &unit : second)
    {
        names.insert(unit.first);
    }

    for (const std::string &name : names)
    {
        if (!sameUnit(unitIn(first, name), unitIn(second, name)))
        {
            changed.push_back(name);
        }
    }

    return changed;
}

bool issueLess(const ProjectIssue &left, const ProjectIssue &right)
{
    return std::tie(left.file, left.path, left.message) < std::tie(right.file, right.path, right.message);
}

std::vector<ProjectIssue> issuesOnlyIn(std::vector<ProjectIssue> first, std::vector<ProjectIssue> second)
{
    std::sort(first.begin(), first.end(), issueLess);
    std::sort(second.begin(), second.end(), issueLess);
    std::vector<ProjectIssue> only;
    std::set_difference(first.begin(), first.end(), second.begin(), second.end(), std::back_inserter(only), issueLess);
    return only;
}

// --- the .oymap folder --------------------------------------------------------------------------------------------

std::filesystem::path stateRoot(const std::filesystem::path &projectRoot)
{
    return projectRoot / ".oymap";
}

// Appends one line to a log file of the .oymap folder (made when missing).
bool appendLogLine(
    const std::filesystem::path &projectRoot,
    const std::string &name,
    const std::string &line,
    std::string &errorMessage)
{
    const std::filesystem::path path = projectStateRoot(projectRoot, true) / name;
    std::string text;
    readTextFile(path, text);
    return writeTextFileAtomically(path, text + line + "\n", errorMessage);
}

std::string localTimestamp()
{
    const std::time_t now = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
    const std::tm *pLocal = std::localtime(&now);
    char text[32] = {};

    if (pLocal != nullptr)
    {
        std::strftime(text, sizeof(text), "%Y-%m-%dT%H:%M:%S", pLocal);
    }

    return text;
}

// The source files' texts by name; a missing file has no entry.
std::map<std::string, std::string> fileTexts(const std::filesystem::path &folder)
{
    std::map<std::string, std::string> texts;

    for (const ProjectFileKind &kind : projectFileKinds())
    {
        std::string text;

        if (kind.fileClass == ProjectFileClass::Source && readTextFile(folder / kind.pName, text))
        {
            texts[kind.pName] = text;
        }
    }

    return texts;
}

bool writeFileSet(
    const std::filesystem::path &folder,
    const std::map<std::string, std::string> &texts,
    const std::set<std::string> &names,
    std::string &errorMessage)
{
    for (const std::string &name : names)
    {
        const std::map<std::string, std::string>::const_iterator text = texts.find(name);

        if (text != texts.end())
        {
            if (!writeTextFileAtomically(folder / name, text->second, errorMessage))
            {
                return false;
            }
        }
        else
        {
            std::error_code error;
            std::filesystem::remove(folder / name, error);
        }
    }

    return true;
}

std::set<std::string> changedNames(
    const std::map<std::string, std::string> &before,
    const std::map<std::string, std::string> &after)
{
    std::set<std::string> names;

    for (const ProjectFileKind &kind : projectFileKinds())
    {
        if (kind.fileClass != ProjectFileClass::Source)
        {
            continue;
        }

        const std::map<std::string, std::string>::const_iterator first = before.find(kind.pName);
        const std::map<std::string, std::string>::const_iterator second = after.find(kind.pName);
        const bool hadIt = first != before.end();
        const bool hasIt = second != after.end();

        if (hadIt != hasIt || (hadIt && first->second != second->second))
        {
            names.insert(kind.pName);
        }
    }

    return names;
}

// The versions of the named files in a set of texts (none for a file the set lacks).
FileVersions versionsOf(const std::map<std::string, std::string> &texts, const std::set<std::string> &names)
{
    FileVersions versions;

    for (const std::string &name : names)
    {
        const std::map<std::string, std::string>::const_iterator text = texts.find(name);
        versions[name] = text != texts.end() ? std::optional<std::string>(text->second) : std::nullopt;
    }

    return versions;
}

Project projectFromTexts(const std::filesystem::path &root, const std::map<std::string, std::string> &texts)
{
    Project project;
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
        catch (const YAML::Exception &)
        {
            continue;
        }

        project.files[file.name] = file;
    }

    return project;
}

// A head written before the source revision (S5a1) holds a hash of every file, pins and lock included. It is re-keyed
// to the source revision of the files it last saw (last/), so that the next read finds an outside edit only where a
// source file really changed; the step is logged in .oymap/migrations.log. A cursor history (before S5b1) becomes an
// append-only one.
bool migrateHead(const std::filesystem::path &projectRoot, HistoryHead &head, std::string &errorMessage)
{
    if (!head.revision.empty() && head.scheme != RevisionScheme)
    {
        const std::string old = head.revision;
        head.revision = projectRevision(projectFromTexts(projectRoot, fileTexts(stateRoot(projectRoot) / "last")));
        head.scheme = RevisionScheme;

        if (!appendLogLine(projectRoot, "migrations.log", localTimestamp() + " the history head re-keyed from "
                + old + " (a hash of every project file) to the source revision " + head.revision + " ("
                + std::string(RevisionScheme) + "); ids.lock.yml and review/pins.yml left the history; entries that "
                "changed only them are passed over by undo and redo", errorMessage)
            || !writeHistoryHead(projectRoot, head, errorMessage))
        {
            return false;
        }
    }

    if (!head.revision.empty() && head.history != HistoryScheme)
    {
        return migrateCursorHistory(projectRoot, head, errorMessage);
    }

    return true;
}

// ids.lock.yml changed by anything but the core's own writers (a `git checkout`, a hand edit, an older oymap): taken
// as the new record and noted in lock.log, never put into the history.
bool noticeOutsideLockChange(const std::filesystem::path &projectRoot, const std::string &sourceRevision,
    std::string &errorMessage)
{
    const std::filesystem::path seenPath = stateRoot(projectRoot) / "lock_seen";
    std::string seen;
    const std::string current = projectLockHash(projectRoot);

    if (readTextFile(seenPath, seen) && !seen.empty() && seen.back() == '\n')
    {
        seen.pop_back();
    }

    if (seen == current)
    {
        return true;
    }

    if (!seen.empty())
    {
        JsonWriter line;
        line.beginObject();
        line.field("source_revision", sourceRevision);
        line.field("by", "outside");
        line.field("lock_before", seen);
        line.field("lock_after", current);
        line.field("note", "changed outside the tool; taken as the new record");
        line.endObject();

        if (!appendLogLine(projectRoot, "lock.log", line.take(), errorMessage))
        {
            return false;
        }
    }

    return writeTextFileAtomically(seenPath, current + "\n", errorMessage);
}

// --- the hand-edit mark (S5_BROWSER_EDITOR.md 2.8) -----------------------------------------------------------------

// `head` learns where the mark came in when the entries had to be read for it (written back, so that a project
// marked elsewhere, as by a `git pull`, reads its entries for it once).
HandMark markOf(const Project &project, HistoryHead &head, const std::filesystem::path &projectRoot)
{
    HandMark mark;
    const YAML::Node node = childOf(project.document("project.yml"), "edited_by_hand");

    if (!node.IsDefined() || !node.IsMap())
    {
        return mark;
    }

    mark.marked = true;
    mark.since = scalarText(node, "since");
    mark.revision = scalarText(node, "revision");
    // The history knows the hand work when it holds the entry that set the mark (the head says which), or else an
    // entry made at the mark's revision.
    if (!head.markRevision.empty() && head.markRevision == mark.revision)
    {
        mark.historyKnown = head.markSequence >= head.first;

        if (!mark.historyKnown)
        {
            StoredHistoryEntry entry;
            std::string unused;
            readHistoryEntry(projectRoot, head.first, false, entry, unused);
            mark.knownFrom = scalarText(entry.node, "time");
        }

        return mark;
    }

    mark.historyKnown = false;
    int found = -1;

    for (int sequence = head.count; sequence >= head.first && sequence >= 1 && !mark.historyKnown; --sequence)
    {
        StoredHistoryEntry entry;
        std::string unused;

        if (readHistoryEntry(projectRoot, sequence, false, entry, unused))
        {
            mark.historyKnown = scalarText(entry.node, "revision_before") == mark.revision
                || scalarText(entry.node, "revision_after") == mark.revision;
            mark.knownFrom = scalarText(entry.node, "time");
            found = mark.historyKnown ? sequence : found;
        }
    }

    if (mark.historyKnown)
    {
        mark.knownFrom.clear();
    }

    if (!head.revision.empty())
    {
        // -1: not in the kept history.
        head.markSequence = found;
        head.markRevision = mark.revision;
        std::string unused;
        writeHistoryHead(projectRoot, head, unused);
    }

    return mark;
}

// Who changed each object last, as far as the kept history shows (objects it does not show are left out).
std::map<std::string, std::string> lastAuthors(const std::filesystem::path &projectRoot, const HistoryHead &head,
    const std::vector<std::string> &objects)
{
    std::map<std::string, std::string> authors;
    std::set<std::string> wanted(objects.begin(), objects.end());

    for (int sequence = head.count; sequence >= head.first && sequence >= 1 && !wanted.empty(); --sequence)
    {
        StoredHistoryEntry entry;
        std::string unused;

        if (!readHistoryEntry(projectRoot, sequence, false, entry, unused))
        {
            continue;
        }

        const std::string author = scalarText(entry.node, "author");

        for (const YAML::Node &object : childOf(entry.node, "objects"))
        {
            if (wanted.erase(object.Scalar()) > 0)
            {
                authors[object.Scalar()] = author;
            }
        }
    }

    return authors;
}

// The written keys of a project's files (`rooms.yml#room:hall/pillars/big`): what an outside rewrite may drop.
std::set<std::string> writtenKeys(const Project &project)
{
    std::set<std::string> keys;

    for (const std::pair<const std::string, ProjectFile> &file : project.files)
    {
        if (isSourceFile(file.first) && fileHasKeyedLists(file.second.schema))
        {
            for (const std::string &address : writtenKeyAddresses(file.second.document, file.second.schema))
            {
                keys.insert(file.first + "#" + address);
            }
        }
    }

    return keys;
}

struct OutsideRecord
{
    std::vector<std::string> changes;
    int sequence = 0;
    std::vector<std::string> notice;
};

// Brings the tool's record up to the files: an edit of a source file made with anything else becomes a history entry
// of its own (author `outside` until `oymap record` names one), so it shows in the diff and can be undone. In a
// project marked as edited by hand, an outside change that replaces objects a person changed last, or drops keys,
// carries an error notice (S5_BROWSER_EDITOR.md 2.8 item 3).
bool syncOutsideEditsWith(
    const std::filesystem::path &projectRoot,
    const Project &project,
    const std::string &revision,
    const std::map<std::string, std::string> &current,
    HistoryHead &head,
    OutsideRecord &outside,
    std::string &errorMessage)
{
    head = readHistoryHead(projectRoot);

    if (!migrateHead(projectRoot, head, errorMessage) || !noticeOutsideLockChange(projectRoot, revision, errorMessage))
    {
        return false;
    }

    if (head.revision.empty())
    {
        // First sight of the project: nothing to compare with.
        head.revision = revision;
        std::set<std::string> names;

        for (const std::pair<const std::string, std::string> &entry : current)
        {
            names.insert(entry.first);
        }

        return writeFileSet(stateRoot(projectRoot) / "last", current, names, errorMessage)
            && writeHistoryHead(projectRoot, head, errorMessage);
    }

    if (head.revision == revision)
    {
        return true;
    }

    const std::map<std::string, std::string> last = fileTexts(stateRoot(projectRoot) / "last");
    const Project lastProject = projectFromTexts(projectRoot, last);
    outside.changes = semanticDiff(lastProject, project);

    if (outside.changes.empty())
    {
        outside.changes.push_back("files changed in form only (formatting, key order)");
    }

    NewHistoryEntry entry;
    entry.kind = "outside";
    entry.author = "outside";
    entry.revisionBefore = head.revision;
    entry.revisionAfter = revision;
    entry.changes = outside.changes;
    const std::set<std::string> names = changedNames(last, current);
    entry.before = versionsOf(last, names);
    entry.after = versionsOf(current, names);
    entry.objects = changedObjects(lastProject, project);
    const HandMark mark = markOf(project, head, projectRoot);

    if (mark.marked)
    {
        // Objects a person changed last that the change replaced or removed; where the kept history does not reach
        // the mark, an object whose last change it does not show counts as a person's (for this notice only).
        const std::map<std::string, std::string> authors = lastAuthors(projectRoot, head, entry.objects);
        std::vector<std::string> replaced;

        for (const std::string &object : entry.objects)
        {
            const std::map<std::string, std::string>::const_iterator author = authors.find(object);
            const bool person = author != authors.end() ? author->second == "user" : !mark.historyKnown;

            if (person && lastProject.has(object.substr(0, object.find('#'))))
            {
                replaced.push_back(object);
            }
        }

        std::vector<std::string> dropped;
        const std::set<std::string> keysAfter = writtenKeys(project);

        for (const std::string &key : writtenKeys(lastProject))
        {
            if (!keysAfter.contains(key))
            {
                dropped.push_back(key);
            }
        }

        if (!replaced.empty() || !dropped.empty())
        {
            std::string objects;

            for (size_t index = 0; index < replaced.size() && index < 12; ++index)
            {
                objects += (index == 0 ? "" : ", ") + replaced[index];
            }

            if (replaced.size() > 12)
            {
                objects += " and " + std::to_string(replaced.size() - 12) + " more";
            }

            entry.notice.push_back("this project is edited by hand (edited_by_hand since " + mark.since
                + "), and a change made outside the tool (a generator run?) replaced "
                + std::to_string(replaced.size()) + " object(s) a person changed last"
                + (objects.empty() ? std::string() : ": " + objects)
                + (dropped.empty() ? std::string() : "; it dropped " + std::to_string(dropped.size())
                    + " written key(s) (" + dropped.front() + (dropped.size() > 1 ? ", ..." : "") + ")")
                + ". Revert it with edit.revert {sequence: " + std::to_string(head.count + 1) + "} (oymap revert "
                + "<project> " + std::to_string(head.count + 1) + "), and change marked projects by operations, "
                "never by running a generator again");
        }
    }

    if (!appendHistoryEntry(projectRoot, head, entry, errorMessage))
    {
        return false;
    }

    outside.sequence = head.count;
    outside.notice = entry.notice;
    return true;
}

bool syncOutsideEdits(
    const std::filesystem::path &projectRoot,
    const Project &project,
    HistoryHead &head,
    OutsideRecord &outside,
    std::string &errorMessage)
{
    return syncOutsideEditsWith(projectRoot, project, projectRevision(project), fileTexts(projectRoot), head,
        outside, errorMessage);
}

long currentProcessNumber()
{
#if defined(__unix__) || defined(__APPLE__)
    return static_cast<long>(getpid());
#else
    return 0;
#endif
}

// Whether the process that wrote a lock still runs. A lock without a number (from an older build, or on a platform
// without process numbers) counts as dead: locks are held for milliseconds.
bool processRuns(long process)
{
#if defined(__unix__) || defined(__APPLE__)
    return process > 0 && (kill(static_cast<pid_t>(process), 0) == 0 || errno == EPERM);
#else
    (void)process;
    return false;
#endif
}

// --- applying operations ------------------------------------------------------------------------------------------

const std::regex &idPattern()
{
    static const std::regex pattern("^[a-z][a-z0-9_]*:[a-z0-9][a-z0-9_]*$");
    return pattern;
}

const std::regex &keyPattern()
{
    static const std::regex pattern("^[a-z][a-z0-9_]*$");
    return pattern;
}

// A schema node with the file it came from, for walking a document beside its schema.
struct SchemaRef
{
    YAML::Node node;
    std::string file;

    SchemaRef() = default;
    SchemaRef(const SchemaRef &other) = default;

    // Rebinds the handle: assigning a yaml-cpp node that holds one would overwrite the schema's own node.
    SchemaRef &operator=(const SchemaRef &other)
    {
        node.reset(other.node);
        file = other.file;
        return *this;
    }

    SchemaRef property(const std::string &name) const
    {
        SchemaRef child;
        child.file = file;

        if (node.IsDefined())
        {
            child.node = propertySchema(SchemaSet::builtIn(), node, name, child.file);
        }

        return child;
    }

    SchemaRef items() const
    {
        SchemaRef child;
        child.file = file;

        if (node.IsDefined())
        {
            child.node = itemsSchema(SchemaSet::builtIn(), node, child.file);
        }

        return child;
    }

    ListKey listKey() const
    {
        if (!node.IsDefined())
        {
            return ListKey();
        }

        std::string resolvedFile = file;
        return listKeyOf(SchemaSet::builtIn().resolve(node, resolvedFile));
    }
};

class Editor
{
public:
    // `pTouched`: the files the operations change are named there, and each is copied before its first change (a
    // tree's nodes share their data with the trees they were copied from, such as a kept project's).
    explicit Editor(Project &project, std::set<std::string> *pTouched = nullptr)
        : m_project(project)
        , m_pTouched(pTouched)
    {
    }

    // `step` is set to the failing step of a patch (else left alone).
    bool apply(const YAML::Node &operation, std::string &error, int &step)
    {
        if (!operation.IsMap() || !childOf(operation, "op").IsDefined())
        {
            error = "an operation is a map with an `op`: add, set, replace, remove, set_value, patch, rename or "
                    "replace_file";
            return false;
        }

        std::string name = operation["op"].Scalar();
        std::string target;
        const size_t dot = name.find('.');

        // "door.add" is "add" to "doors".
        if (dot != std::string::npos)
        {
            target = name.substr(0, dot);
            name = name.substr(dot + 1);
        }

        if (name == "add")
        {
            return add(operation, target, error);
        }

        if (name == "set")
        {
            return set(operation, error);
        }

        if (name == "replace")
        {
            return replace(operation, error);
        }

        if (name == "remove")
        {
            return remove(operation, error);
        }

        if (name == "set_value")
        {
            return setValue(operation, error);
        }

        if (name == "patch")
        {
            return patch(operation, error, step);
        }

        if (name == "rename")
        {
            return rename(operation, error);
        }

        if (name == "replace_file")
        {
            return replaceFile(operation, error);
        }

        if (name == "name")
        {
            return giveName(operation, error);
        }

        error = "unknown op '" + operation["op"].Scalar() + "': use add, set, replace, remove, set_value, patch, "
                "rename, replace_file or name";
        return false;
    }

    // op name {id, path}: gives a sub-object an id of its own (a room's platform or level, so that a switch, a floor
    // or an event can name it; S5_BROWSER_EDITOR.md 2.6 item 5: ids are the core's to give). The id is
    // `<kind>:<the owner's name>_<n>`, the kind the one its `id` field accepts, n the first number free in the file.
    bool giveName(const YAML::Node &operation, std::string &error)
    {
        const YAML::Node id = childOf(operation, "id");
        const YAML::Node pointer = childOf(operation, "path");
        std::vector<std::string> segments;

        if (!id.IsDefined() || !pointer.IsDefined() || !splitPointer(pointer.Scalar(), segments, error)
            || segments.empty())
        {
            error = error.empty() ? "name needs `id` (the object) and `path` (the sub-object in it, as "
                "/platforms/platform2)" : error;
            return false;
        }

        std::string fileName;
        std::string listKey;
        size_t index = 0;

        if (!find(operation, id.Scalar(), fileName, listKey, index, error))
        {
            return false;
        }

        YAML::Node root;
        root.reset(document(fileName)[listKey][index]);
        const SchemaRef rootSchema = fileSchema(fileName).property(listKey).items();
        YAML::Node current;

        if (!patchGet(root, rootSchema, segments, current, error))
        {
            return false;
        }

        if (!current.IsMap())
        {
            error = pointer.Scalar() + " is not an object";
            return false;
        }

        if (childOf(current, "id").IsDefined())
        {
            error = pointer.Scalar() + " has an id already: " + scalarText(current, "id");
            return false;
        }

        std::vector<Place> chain;
        YAML::Node container;
        SchemaRef containerSchema;

        if (!walk(root, rootSchema, segments, chain, container, containerSchema, error))
        {
            return false;
        }

        const SchemaRef itemSchema = container.IsSequence() ? containerSchema.items()
            : containerSchema.property(segments.back());
        const SchemaRef idSchema = itemSchema.property("id");

        if (!idSchema.node.IsDefined() || !idSchema.node.IsMap())
        {
            error = pointer.Scalar() + " takes no id (its schema has no `id`)";
            return false;
        }

        std::string kind = segments.size() >= 2 ? segments[segments.size() - 2] : std::string();

        if (const YAML::Node kinds = childOf(idSchema.node, "x-id-kinds"); kinds.IsDefined() && kinds.IsSequence() && kinds.size() > 0)
        {
            kind = kinds[0].Scalar();
        }
        else if (kind.ends_with("s"))
        {
            kind.pop_back();
        }

        const std::string owner = id.Scalar();
        const size_t colon = owner.find(':');
        const std::string base = colon == std::string::npos ? owner : owner.substr(colon + 1);
        std::string named;

        for (int number = 1;; ++number)
        {
            named = kind + ":" + base + "_" + std::to_string(number);

            if (!fileHasId(fileName, named))
            {
                break;
            }
        }

        std::vector<std::string> idPath = segments;
        idPath.push_back("id");

        if (!patchAdd(root, rootSchema, idPath, YAML::Node(named), false, error))
        {
            return false;
        }

        m_idsAllocated.push_back(fileName + "#" + named);
        return true;
    }

    // Whether an operation may change the file: only source files (pins have their own methods, the lock is written
    // by builds and `oymap lock prune`).
    static bool changeable(const std::string &fileName, std::string &error)
    {
        if (!isSourceFile(fileName))
        {
            error = fileName + " is not a project file an operation may change"
                + (fileName == "review/pins.yml" ? std::string(" (pins: oymap pins, or the pins methods)")
                    : fileName == "ids.lock.yml" ? std::string(" (the lock is a record: builds write it)")
                    : std::string());
            return false;
        }

        return true;
    }

    // The file's tree for changing (a copy on its first change; made when the project lacks the file).
    YAML::Node &document(const std::string &fileName)
    {
        std::map<std::string, ProjectFile>::iterator file = m_project.files.find(fileName);

        if (m_pTouched != nullptr && file != m_project.files.end() && m_pTouched->insert(fileName).second)
        {
            // A copy of the tree before its first change; the entry is replaced, not assigned to (assigning a
            // yaml-cpp node rebinds the node it shares data with).
            const ProjectFile copy{file->second.name, file->second.schema, file->second.text,
                YAML::Clone(file->second.document)};
            m_project.files.erase(file);
            file = m_project.files.emplace(fileName, copy).first;
        }

        if (file == m_project.files.end())
        {
            if (m_pTouched != nullptr)
            {
                m_pTouched->insert(fileName);
            }

            ProjectFile created;
            created.name = fileName;

            for (const ProjectFileKind &kind : projectFileKinds())
            {
                if (fileName == kind.pName)
                {
                    created.schema = kind.pSchema;
                }
            }

            created.document = YAML::Node(YAML::NodeType::Map);
            created.document["format"] = 0;
            file = m_project.files.emplace(fileName, created).first;
        }

        return file->second.document;
    }

    // The renames made, in order (the history keeps them: a revert runs them backwards).
    const std::vector<HistoryRename> &renames() const
    {
        return m_renames;
    }

    const std::vector<std::string> &idsAllocated() const
    {
        return m_idsAllocated;
    }

    const std::vector<std::string> &notes() const
    {
        return m_notes;
    }

    // Renames an id everywhere (the object's own id and every reference to it in the source files). `from` may be a
    // top-level object's id (with `file` where it is in more than one file) or the id of a sub-object (a platform's
    // or a level's `id`, which events name).
    bool renameId(const std::string &from, const std::string &to, const std::string &file, std::string &error)
    {
        if (!std::regex_match(to, idPattern()))
        {
            error = "the new id '" + to + "' is not an id: <kind>:<name>, lower case letters, digits and underscores";
            return false;
        }

        if (from == to)
        {
            error = "the new id is the old one";
            return false;
        }

        YAML::Node operation(YAML::NodeType::Map);

        if (!file.empty())
        {
            operation["file"] = file;
        }

        std::string fileName;
        std::string listKey;
        size_t index = 0;
        std::string unused;

        if (!find(operation, from, fileName, listKey, index, unused))
        {
            // A sub-object's own id (a platform named by events): unique among the project's ids.
            fileName = fileWithNestedId(from);

            if (fileName.empty())
            {
                error = "nothing in the project has the id " + from;
                return false;
            }
        }

        if (fileHasId(fileName, to))
        {
            error = "the id " + to + " is already used in " + fileName;
            return false;
        }

        // Every source file: the object's own id in its file; in the others every value that names it, except
        // another file's own object of the same id (a plan's space and its room share theirs).
        for (const ProjectFileKind &kind : projectFileKinds())
        {
            if (kind.fileClass != ProjectFileClass::Source || !m_project.has(kind.pName))
            {
                continue;
            }

            if (!mentions(m_project.document(kind.pName), from))
            {
                continue;
            }

            YAML::Node root = document(kind.pName);
            const bool own = kind.pName == fileName;
            replaceIn(root, from, to, own, true, kind.pName);
        }

        m_renames.push_back({from, to});
        return true;
    }

    // Renames a sub-object's key within its list (`room:hall`, `/pillars/pillar2`, to `big`).
    bool renameKey(const YAML::Node &operation, const std::string &owner, const std::string &path,
        const std::string &to, std::string &error)
    {
        if (!std::regex_match(to, keyPattern()))
        {
            error = "the new key '" + to + "' is not a key: lower case letters, digits and underscores, a letter "
                    "first";
            return false;
        }

        std::string fileName;
        std::string listKey;
        size_t index = 0;

        if (!find(operation, owner, fileName, listKey, index, error))
        {
            return false;
        }

        std::vector<std::string> segments;

        if (!splitPointer(path, segments, error))
        {
            return false;
        }

        YAML::Node root = document(fileName)[listKey][index];
        SchemaRef schema = fileSchema(fileName).property(listKey).items();
        std::vector<Place> chain;
        YAML::Node container;
        SchemaRef containerSchema;

        if (!walk(root, schema, segments, chain, container, containerSchema, error))
        {
            return false;
        }

        const ListKey key = containerSchema.listKey();

        if (!container.IsSequence() || !key.keyed() || key.field == "id")
        {
            error = path + " does not name an item of a keyed list (a rename of a key names one, as /pillars/pillar2)";
            return false;
        }

        const long position = findKeyed(container, key, segments.back());

        if (position < 0)
        {
            error = "no item with the key '" + segments.back() + "' in this list";
            return false;
        }

        if (findKeyed(container, key, to) >= 0)
        {
            error = "the key " + to + " is already used in this list";
            return false;
        }

        YAML::Node item = container[static_cast<size_t>(position)];
        item[key.field] = to;
        std::string parent;

        for (size_t segment = 0; segment + 1 < segments.size(); ++segment)
        {
            parent += "/" + segments[segment];
        }

        m_renames.push_back({owner + parent + "/" + segments.back(), owner + parent + "/" + to});
        return true;
    }

private:
    struct Place
    {
        YAML::Node container;
        std::string key;
        size_t index = 0;
    };

    static SchemaRef fileSchema(const std::string &fileName)
    {
        SchemaRef schema;

        for (const ProjectFileKind &kind : projectFileKinds())
        {
            if (fileName == kind.pName)
            {
                schema.file = kind.pSchema;
                schema.node = SchemaSet::builtIn().root(kind.pSchema);
            }
        }

        return schema;
    }

    // Finds the object with the id in one file: its list's key and its position.
    static bool findInFile(const YAML::Node &root, const std::string &id, std::string &listKey, size_t &index)
    {
        if (!root.IsMap())
        {
            return false;
        }

        for (YAML::const_iterator iterator = root.begin(); iterator != root.end(); ++iterator)
        {
            if (!iterator->second.IsSequence())
            {
                continue;
            }

            size_t position = 0;
            // A copy of the node: `iterator->second` lives in a temporary the loop would outlive.
            const YAML::Node list = iterator->second;

            for (const YAML::Node &item : list)
            {
                const YAML::Node itemId = childOf(item, "id");

                if (itemId.IsDefined() && itemId.IsScalar() && itemId.Scalar() == id)
                {
                    listKey = iterator->first.Scalar();
                    index = position;
                    return true;
                }

                ++position;
            }
        }

        return false;
    }

    // Finds the object an operation names by `id`: its file, its list's key and its position. Ids are unique within
    // a file, not across files (a plan's space and the room that realises it share one), so an id in more than one
    // file is refused unless the operation names its `file`.
    bool find(
        const YAML::Node &operation,
        const std::string &id,
        std::string &fileName,
        std::string &listKey,
        size_t &index,
        std::string &error) const
    {
        const YAML::Node wanted = childOf(operation, "file");

        if (wanted.IsDefined())
        {
            const std::map<std::string, ProjectFile>::const_iterator file = m_project.files.find(wanted.Scalar());

            if (file == m_project.files.end() || !findInFile(file->second.document, id, listKey, index))
            {
                error = "nothing in " + wanted.Scalar() + " has the id " + id;
                return false;
            }

            fileName = file->first;
            return true;
        }

        std::vector<std::string> foundIn;

        for (const std::pair<const std::string, ProjectFile> &file : m_project.files)
        {
            std::string key;
            size_t position = 0;

            if (isSourceFile(file.first) && findInFile(file.second.document, id, key, position))
            {
                if (foundIn.empty())
                {
                    fileName = file.first;
                    listKey = key;
                    index = position;
                }

                foundIn.push_back(file.first);
            }
        }

        if (foundIn.empty())
        {
            error = "nothing in the project has the id " + id;
            return false;
        }

        if (foundIn.size() > 1)
        {
            error = "the id " + id + " is in ";

            for (size_t position = 0; position < foundIn.size(); ++position)
            {
                error += (position == 0 ? "" : position + 1 == foundIn.size() ? " and " : ", ") + foundIn[position];
            }

            error += ": name the one meant with `file`, e.g. file: " + foundIn.front();
            return false;
        }

        return true;
    }

    // Whether the value names the id anywhere (a scalar equal to it).
    static bool mentions(const YAML::Node &node, const std::string &id)
    {
        if (node.IsScalar())
        {
            return node.Scalar() == id;
        }

        if (node.IsMap())
        {
            for (YAML::const_iterator iterator = node.begin(); iterator != node.end(); ++iterator)
            {
                if (mentions(iterator->second, id))
                {
                    return true;
                }
            }
        }
        else if (node.IsSequence())
        {
            for (const YAML::Node &item : node)
            {
                if (mentions(item, id))
                {
                    return true;
                }
            }
        }

        return false;
    }

    // Whether a map of the file (at any depth) has this `id`.
    bool fileHasId(const std::string &fileName, const std::string &id) const
    {
        return m_project.has(fileName) && hasNestedId(m_project.document(fileName), id);
    }

    static bool hasNestedId(const YAML::Node &node, const std::string &id)
    {
        if (node.IsMap())
        {
            const YAML::Node own = childOf(node, "id");

            if (own.IsDefined() && own.IsScalar() && own.Scalar() == id)
            {
                return true;
            }

            for (YAML::const_iterator iterator = node.begin(); iterator != node.end(); ++iterator)
            {
                if (hasNestedId(iterator->second, id))
                {
                    return true;
                }
            }
        }
        else if (node.IsSequence())
        {
            for (const YAML::Node &item : node)
            {
                if (hasNestedId(item, id))
                {
                    return true;
                }
            }
        }

        return false;
    }

    std::string fileWithNestedId(const std::string &id) const
    {
        for (const std::pair<const std::string, ProjectFile> &file : m_project.files)
        {
            if (isSourceFile(file.first) && hasNestedId(file.second.document, id))
            {
                return file.first;
            }
        }

        return std::string();
    }

    // Replaces every scalar `from` by `to` under `node`. `own`: the object's own file (its `id` changes too);
    // otherwise an object of the same id there is another object and keeps it. Lua texts are not changed: a note
    // says which name the old id.
    void replaceIn(YAML::Node node, const std::string &from, const std::string &to, bool own, bool topLevel,
        const std::string &fileName)
    {
        if (node.IsMap())
        {
            if (!own && topLevel)
            {
                // Top-level lists of another file: an item whose own id is `from` is that file's own object.
                for (YAML::iterator iterator = node.begin(); iterator != node.end(); ++iterator)
                {
                    YAML::Node value = iterator->second;

                    if (value.IsSequence())
                    {
                        for (YAML::Node item : value)
                        {
                            const bool same = scalarText(item, "id") == from;

                            for (YAML::iterator field = item.begin(); item.IsMap() && field != item.end(); ++field)
                            {
                                if (!(same && field->first.Scalar() == "id"))
                                {
                                    replaceValue(field->second, field->first.Scalar(), from, to, fileName,
                                        scalarText(item, "id"));
                                }
                            }

                            if (!item.IsMap())
                            {
                                replaceValue(item, "", from, to, fileName, "");
                            }
                        }
                    }
                    else
                    {
                        replaceValue(value, iterator->first.Scalar(), from, to, fileName, "");
                    }
                }

                return;
            }

            for (YAML::iterator iterator = node.begin(); iterator != node.end(); ++iterator)
            {
                replaceValue(iterator->second, iterator->first.Scalar(), from, to, fileName, "");
            }
        }
    }

    void replaceValue(YAML::Node node, const std::string &key, const std::string &from, const std::string &to,
        const std::string &fileName, const std::string &owner)
    {
        if (node.IsScalar())
        {
            if (node.Scalar() == from)
            {
                node = to;
            }
            else if (key == "lua" && node.Scalar().find(from) != std::string::npos)
            {
                m_notes.push_back(fileName + (owner.empty() ? std::string() : " " + owner) + ": its `lua` text names "
                    + from + ", which is now " + to + ": change the text by hand");
            }

            return;
        }

        if (node.IsMap())
        {
            const std::string own = scalarText(node, "id");

            for (YAML::iterator iterator = node.begin(); iterator != node.end(); ++iterator)
            {
                replaceValue(iterator->second, iterator->first.Scalar(), from, to, fileName,
                    own.empty() ? owner : own);
            }
        }
        else if (node.IsSequence())
        {
            for (YAML::Node item : node)
            {
                replaceValue(item, key, from, to, fileName, owner);
            }
        }
    }

    // A new id for an object added without one (2.6 item 5): `<prefix>:<base>_<n>`, the prefix as the list's other
    // objects have it (or the collection's), the base the name of the room the object is in (or the collection's
    // singular), n the first number free in the file.
    std::string allocateId(const Collection &collection, const YAML::Node &value)
    {
        std::map<std::string, int> prefixes;

        if (m_project.has(collection.file))
        {
            for (const YAML::Node &item : childOf(m_project.document(collection.file), collection.name))
            {
                const std::string id = scalarText(item, "id");
                const size_t colon = id.find(':');

                if (colon != std::string::npos)
                {
                    ++prefixes[id.substr(0, colon)];
                }
            }
        }

        std::string prefix = collection.prefix;
        int most = 0;

        for (const std::pair<const std::string, int> &count : prefixes)
        {
            if (count.second > most)
            {
                most = count.second;
                prefix = count.first;
            }
        }

        std::string base = collection.singular;

        for (const char *pField : {"room", "space", "in"})
        {
            const std::string where = scalarText(value, pField);
            const size_t colon = where.find(':');

            if (colon != std::string::npos && colon + 1 < where.size())
            {
                base = where.substr(colon + 1);
                break;
            }
        }

        for (int number = 1;; ++number)
        {
            const std::string id = prefix + ":" + base + "_" + std::to_string(number);

            if (!fileHasId(collection.file, id))
            {
                return id;
            }
        }
    }

    bool add(const YAML::Node &operation, const std::string &targetFromName, std::string &error)
    {
        const std::string target = targetFromName.empty() && childOf(operation, "to").IsDefined()
            ? operation["to"].Scalar() : targetFromName;
        const Collection *pCollection = findCollection(target, scalarText(operation, "file"), m_project);
        const YAML::Node value = childOf(operation, "value");

        if (pCollection == nullptr)
        {
            error = "add needs `to`, one of: " + collectionNames();
            return false;
        }

        if (!value.IsDefined() || !value.IsMap())
        {
            error = "add needs a `value` map (without an `id` the core gives one)";
            return false;
        }

        YAML::Node added = YAML::Clone(value);

        if (!childOf(added, "id").IsDefined())
        {
            // The id goes first in the map; the canonical writer orders the keys by the schema anyway.
            const std::string id = allocateId(*pCollection, added);
            YAML::Node withId(YAML::NodeType::Map);
            withId["id"] = id;

            for (YAML::const_iterator field = added.begin(); field != added.end(); ++field)
            {
                withId[field->first.Scalar()] = field->second;
            }

            added = withId;
            m_idsAllocated.push_back(pCollection->file + "#" + id);
        }

        // Ids are unique within a file: only the collection's own file is checked.
        const std::map<std::string, ProjectFile>::const_iterator file = m_project.files.find(pCollection->file);
        std::string listKey;
        size_t index = 0;

        if (file != m_project.files.end() && findInFile(file->second.document, added["id"].Scalar(), listKey, index))
        {
            error = "the id " + added["id"].Scalar() + " is already used in " + file->first
                + "; use op set to change it";
            return false;
        }

        document(pCollection->file)[pCollection->name].push_back(added);
        return true;
    }

    bool set(const YAML::Node &operation, std::string &error)
    {
        const YAML::Node id = childOf(operation, "id");
        const YAML::Node fields = childOf(operation, "fields");
        std::string fileName;
        std::string listKey;
        size_t index = 0;

        if (!id.IsDefined() || !fields.IsDefined() || !fields.IsMap())
        {
            error = "set needs `id` and a `fields` map (a null value removes the field), and `file` when the id is "
                    "in more than one file";
            return false;
        }

        if (!find(operation, id.Scalar(), fileName, listKey, index, error))
        {
            return false;
        }

        YAML::Node object = document(fileName)[listKey][index];

        for (YAML::const_iterator iterator = fields.begin(); iterator != fields.end(); ++iterator)
        {
            const std::string key = iterator->first.Scalar();

            if (key == "id")
            {
                error = "an id is changed with op rename {from, to}, which changes every reference to it too";
                return false;
            }

            if (iterator->second.IsNull())
            {
                object.remove(key);
            }
            else
            {
                object[key] = YAML::Clone(iterator->second);
            }
        }

        return true;
    }

    // The whole object (the Source tab's Apply): every field as `value` says, the id kept.
    bool replace(const YAML::Node &operation, std::string &error)
    {
        const YAML::Node id = childOf(operation, "id");
        const YAML::Node value = childOf(operation, "value");
        std::string fileName;
        std::string listKey;
        size_t index = 0;

        if (!id.IsDefined() || !value.IsDefined() || !value.IsMap())
        {
            error = "replace needs `id` and the whole object as `value` (and `file` when the id is in more than one "
                    "file)";
            return false;
        }

        if (!find(operation, id.Scalar(), fileName, listKey, index, error))
        {
            return false;
        }

        if (childOf(value, "id").IsDefined() && value["id"].Scalar() != id.Scalar())
        {
            error = "replace keeps the object's id: rename it with op rename";
            return false;
        }

        YAML::Node object(YAML::NodeType::Map);
        object["id"] = id.Scalar();

        for (YAML::const_iterator field = value.begin(); field != value.end(); ++field)
        {
            if (field->first.Scalar() != "id")
            {
                object[field->first.Scalar()] = YAML::Clone(field->second);
            }
        }

        YAML::Node root = document(fileName);
        YAML::Node list = root[listKey];
        list[index] = object;
        return true;
    }

    bool remove(const YAML::Node &operation, std::string &error)
    {
        const YAML::Node id = childOf(operation, "id");
        std::string fileName;
        std::string listKey;
        size_t index = 0;

        if (!id.IsDefined())
        {
            error = "remove needs `id` (and `file` when the id is in more than one file)";
            return false;
        }

        if (!find(operation, id.Scalar(), fileName, listKey, index, error))
        {
            return false;
        }

        // The list is rebuilt without the item (yaml-cpp has no dependable erase for a list's item).
        YAML::Node root = document(fileName);
        const YAML::Node list = root[listKey];
        YAML::Node kept(YAML::NodeType::Sequence);
        size_t position = 0;

        for (const YAML::Node &item : list)
        {
            if (position++ != index)
            {
                kept.push_back(item);
            }
        }

        if (kept.size() == 0)
        {
            root.remove(listKey);
        }
        else
        {
            root[listKey] = kept;
        }

        return true;
    }

    bool setValue(const YAML::Node &operation, std::string &error)
    {
        const YAML::Node file = childOf(operation, "file");
        const YAML::Node path = childOf(operation, "path");
        const YAML::Node value = childOf(operation, "value");

        if (!file.IsDefined() || !path.IsDefined() || !childOf(operation, "value").IsDefined())
        {
            error = "set_value needs `file`, `path` (keys joined by dots) and `value` (null removes the key)";
            return false;
        }

        if (!changeable(file.Scalar(), error))
        {
            return false;
        }

        // Walk to the parent of the last key, making maps on the way.
        std::vector<std::string> keys;
        size_t begin = 0;
        const std::string &text = path.Scalar();

        while (begin <= text.size())
        {
            const size_t dot = text.find('.', begin);
            keys.push_back(text.substr(begin, dot == std::string::npos ? dot : dot - begin));

            if (dot == std::string::npos)
            {
                break;
            }

            begin = dot + 1;
        }

        YAML::Node node = document(file.Scalar());

        for (size_t index = 0; index + 1 < keys.size(); ++index)
        {
            YAML::Node next = node[keys[index]];

            if (!next.IsDefined() || !next.IsMap())
            {
                node[keys[index]] = YAML::Node(YAML::NodeType::Map);
                next.reset(node[keys[index]]);
            }

            node.reset(next);
        }

        if (value.IsNull())
        {
            node.remove(keys.back());
        }
        else
        {
            node[keys.back()] = YAML::Clone(value);
        }

        return true;
    }

    // `{op: rename, from, to}` (an id, with `file` where it is in more than one file) or `{op: rename, id, path,
    // to}` (a sub-object's key: path /pillars/pillar2).
    bool rename(const YAML::Node &operation, std::string &error)
    {
        const std::string to = scalarText(operation, "to");

        if (to.empty())
        {
            error = "rename needs `to`, and `from` (an id) or `id` and `path` (a sub-object's key)";
            return false;
        }

        if (childOf(operation, "path").IsDefined())
        {
            const std::string owner = scalarText(operation, "id");

            if (owner.empty())
            {
                error = "a rename of a key needs `id` (its owner) and `path` (/pillars/pillar2)";
                return false;
            }

            return renameKey(operation, owner, operation["path"].Scalar(), to, error);
        }

        const std::string from = scalarText(operation, "from");

        if (from.empty())
        {
            error = "rename needs `from` (an id) and `to`";
            return false;
        }

        return renameId(from, to, scalarText(operation, "file"), error);
    }

    // `{op: replace_file, file, text}`: a whole file as written (the Source tab on a file).
    bool replaceFile(const YAML::Node &operation, std::string &error)
    {
        const std::string file = scalarText(operation, "file");
        const YAML::Node text = childOf(operation, "text");

        if (file.empty() || !text.IsDefined() || !text.IsScalar())
        {
            error = "replace_file needs `file` and `text`";
            return false;
        }

        if (!changeable(file, error))
        {
            return false;
        }

        YAML::Node parsed;

        try
        {
            parsed = YAML::Load(text.Scalar());
        }
        catch (const YAML::Exception &exception)
        {
            error = "the text is not YAML: " + std::string(exception.what());
            return false;
        }

        if (!parsed.IsMap())
        {
            error = "a project file is a map";
            return false;
        }

        YAML::Node &root = document(file);
        root = parsed;
        return true;
    }

    // --- patch: JSON Patch (RFC 6902) on an object or a file ---------------------------------------------------

    static bool splitPointer(const std::string &pointer, std::vector<std::string> &segments, std::string &error)
    {
        segments.clear();

        if (pointer.empty() || pointer[0] != '/')
        {
            error = "a path is a JSON pointer with at least one segment, such as /outline/2";
            return false;
        }

        size_t begin = 1;

        while (true)
        {
            const size_t slash = pointer.find('/', begin);
            const std::string raw = pointer.substr(begin, slash == std::string::npos ? slash : slash - begin);
            std::string segment;

            for (size_t index = 0; index < raw.size(); ++index)
            {
                if (raw[index] == '~' && index + 1 < raw.size() && (raw[index + 1] == '0' || raw[index + 1] == '1'))
                {
                    segment += raw[index + 1] == '0' ? '~' : '/';
                    ++index;
                }
                else if (raw[index] == '~')
                {
                    error = "'~' in a path segment must be ~0 or ~1";
                    return false;
                }
                else
                {
                    segment += raw[index];
                }
            }

            segments.push_back(segment);

            if (slash == std::string::npos)
            {
                return true;
            }

            begin = slash + 1;
        }
    }

    // A list whose items are maps with an id is addressed by id (the key), any other by position.
    static bool isKeyedList(const YAML::Node &list)
    {
        for (const YAML::Node &item : list)
        {
            if (item.IsMap() && childOf(item, "id").IsDefined())
            {
                return true;
            }
        }

        return false;
    }

    // Where `segment` points in `container` (whose schema is `schema`). `forAdd` allows the end of a list ("-" or
    // its size) and a missing map key. `exists` says whether something is there now. A segment into a keyed list
    // (its schema's `x-key`) is the item's key (S5_BROWSER_EDITOR.md 2.6 item 3, a departure from RFC 6901); into a
    // list of objects with ids, an id; into any other list, a position.
    static bool locate(
        const YAML::Node &container,
        const SchemaRef &schema,
        const std::string &segment,
        bool forAdd,
        Place &place,
        bool &exists,
        std::string &error)
    {
        place.container.reset(container);
        place.key = segment;
        place.index = 0;
        exists = false;

        if (container.IsMap())
        {
            exists = childOf(container, segment).IsDefined();

            if (!exists && !forAdd)
            {
                error = "nothing at key '" + segment + "'";
                return false;
            }

            return true;
        }

        if (!container.IsSequence())
        {
            error = "'" + segment + "' points into a value that is neither a map nor a list";
            return false;
        }

        if (segment == "-")
        {
            if (!forAdd)
            {
                error = "'-' (the end of a list) is only for add";
                return false;
            }

            place.index = container.size();
            return true;
        }

        const ListKey key = schema.listKey();

        const bool digits = !segment.empty() && segment.size() < 10
            && std::all_of(segment.begin(), segment.end(), [](char character) { return character >= '0' && character <= '9'; })
            && (segment.size() == 1 || segment[0] != '0');

        // An add may insert into a keyed list at a position (keys begin with a letter, positions are digits).
        if (key.keyed() && key.field != "id" && !(forAdd && digits))
        {
            const long position = findKeyed(container, key, segment);

            if (position < 0)
            {
                std::string known;

                for (const std::string &each : itemKeys(container, key))
                {
                    known += (known.empty() ? "" : ", ") + each;
                }

                error = "no item with the key '" + segment + "' in this list (its items are addressed by key"
                    + (known.empty() ? std::string() : ": " + known) + ")";
                return false;
            }

            place.index = static_cast<size_t>(position);
            exists = true;
            return true;
        }

        // A list of objects with ids whose items may lack one (a building's parts): an item without an id is named
        // by the key the core gives it (`part2`).
        if (key.field == "id" && !key.prefix.empty() && !(forAdd && digits))
        {
            const long position = findKeyed(container, key, segment);

            if (position >= 0)
            {
                place.index = static_cast<size_t>(position);
                exists = true;
                return true;
            }
        }

        if (!(key.keyed() && key.field != "id") && (isKeyedList(container) || key.field == "id"))
        {
            size_t position = 0;

            for (const YAML::Node &item : container)
            {
                const YAML::Node id = childOf(item, "id");

                if (id.IsDefined() && id.IsScalar() && id.Scalar() == segment)
                {
                    place.index = position;
                    exists = true;
                    return true;
                }

                ++position;
            }

            error = "no item with the id '" + segment + "' in this list (its items are addressed by id)";
            return false;
        }

        if (!digits)
        {
            error = "'" + segment + "' is not a position in this list";
            return false;
        }

        place.index = static_cast<size_t>(std::stoul(segment));
        exists = place.index < container.size();

        if (place.index > container.size() || (!exists && !forAdd))
        {
            error = "position " + segment + " is past the end of a list of " + std::to_string(container.size());
            return false;
        }

        return true;
    }

    static YAML::Node valueAt(const Place &place)
    {
        const YAML::Node &container = place.container;
        return container.IsMap() ? container[place.key] : container[place.index];
    }

    static SchemaRef schemaAt(const YAML::Node &container, const SchemaRef &schema, const std::string &segment)
    {
        return container.IsMap() ? schema.property(segment) : schema.items();
    }

    // Puts `value` where `parent` points (the container's own place in its parent). Lists are rebuilt: yaml-cpp has
    // no dependable insert or erase for a list's item.
    static void store(const Place &parent, const YAML::Node &value)
    {
        YAML::Node container = parent.container;

        if (container.IsMap())
        {
            container[parent.key] = value;
        }
        else
        {
            container[parent.index] = value;
        }
    }

    static YAML::Node listWith(const YAML::Node &list, size_t index, const YAML::Node *pInsert, bool dropAtIndex)
    {
        YAML::Node rebuilt(YAML::NodeType::Sequence);
        size_t position = 0;

        for (const YAML::Node &item : list)
        {
            if (position == index && pInsert != nullptr)
            {
                rebuilt.push_back(*pInsert);
            }

            if (!(dropAtIndex && position == index))
            {
                rebuilt.push_back(item);
            }

            ++position;
        }

        if (index >= position && pInsert != nullptr)
        {
            rebuilt.push_back(*pInsert);
        }

        return rebuilt;
    }

    // Walks a pointer to the container of its last segment. `chain` holds each container's place in its parent;
    // `containerSchema` is the container's schema.
    static bool walk(
        const YAML::Node &root,
        const SchemaRef &rootSchema,
        const std::vector<std::string> &segments,
        std::vector<Place> &chain,
        YAML::Node &container,
        SchemaRef &containerSchema,
        std::string &error)
    {
        chain.clear();
        container.reset(root);
        containerSchema = rootSchema;

        for (size_t index = 0; index + 1 < segments.size(); ++index)
        {
            Place place;
            bool exists = false;

            if (!locate(container, containerSchema, segments[index], false, place, exists, error))
            {
                return false;
            }

            chain.push_back(place);
            containerSchema = schemaAt(container, containerSchema, segments[index]);
            container.reset(valueAt(place));
        }

        return true;
    }

    static bool patchAdd(const YAML::Node &root, const SchemaRef &rootSchema, const std::vector<std::string> &segments,
        const YAML::Node &value, bool mustExist, std::string &error)
    {
        std::vector<Place> chain;
        YAML::Node container;
        SchemaRef containerSchema;

        // An append to a list the object does not have yet (`/pillars/-` on a room without pillars) makes the list.
        if (!mustExist && segments.size() >= 2 && (segments.back() == "-" || segments.back() == "0"))
        {
            const std::vector<std::string> parent(segments.begin(), segments.end() - 1);
            std::string unused;

            if (walk(root, rootSchema, parent, chain, container, containerSchema, unused) && container.IsMap()
                && !childOf(container, parent.back()).IsDefined())
            {
                container[parent.back()] = YAML::Node(YAML::NodeType::Sequence);
            }
        }

        if (!walk(root, rootSchema, segments, chain, container, containerSchema, error))
        {
            return false;
        }

        Place place;
        bool exists = false;

        if (!locate(container, containerSchema, segments.back(), !mustExist, place, exists, error))
        {
            return false;
        }

        if (container.IsMap())
        {
            container[place.key] = YAML::Clone(value);
            return true;
        }

        // A new item of a keyed list may bring its key; it must be free (else the core gives one on writing).
        const ListKey key = containerSchema.listKey();

        if (key.keyed() && key.field != "id" && value.IsMap() && childOf(value, key.field).IsDefined())
        {
            const long taken = findKeyed(container, key, value[key.field].Scalar());

            if (taken >= 0 && !(mustExist && static_cast<size_t>(taken) == place.index))
            {
                error = "the key " + value[key.field].Scalar() + " is already used in this list";
                return false;
            }
        }

        // The root is always a map, so a list has a place in its parent.
        const YAML::Node copy = YAML::Clone(value);
        store(chain.back(), listWith(container, place.index, &copy, mustExist));
        return true;
    }

    static bool patchRemove(const YAML::Node &root, const SchemaRef &rootSchema,
        const std::vector<std::string> &segments, std::string &error)
    {
        std::vector<Place> chain;
        YAML::Node container;
        SchemaRef containerSchema;
        Place place;
        bool exists = false;

        if (!walk(root, rootSchema, segments, chain, container, containerSchema, error)
            || !locate(container, containerSchema, segments.back(), false, place, exists, error))
        {
            return false;
        }

        if (container.IsMap())
        {
            container.remove(place.key);
            return true;
        }

        store(chain.back(), listWith(container, place.index, nullptr, true));
        return true;
    }

    static bool patchGet(const YAML::Node &root, const SchemaRef &rootSchema, const std::vector<std::string> &segments,
        YAML::Node &value, std::string &error)
    {
        std::vector<Place> chain;
        YAML::Node container;
        SchemaRef containerSchema;
        Place place;
        bool exists = false;

        if (!walk(root, rootSchema, segments, chain, container, containerSchema, error)
            || !locate(container, containerSchema, segments.back(), false, place, exists, error))
        {
            return false;
        }

        value = YAML::Clone(valueAt(place));
        return true;
    }

    // Whether the pointer ends on the key field of an item of a keyed list.
    static bool pointsAtKey(const YAML::Node &root, const SchemaRef &rootSchema,
        const std::vector<std::string> &segments)
    {
        if (segments.size() < 2)
        {
            return false;
        }

        std::vector<Place> chain;
        YAML::Node container;
        SchemaRef containerSchema;
        std::string unused;
        const std::vector<std::string> parent(segments.begin(), segments.end() - 1);

        if (!walk(root, rootSchema, parent, chain, container, containerSchema, unused) || !container.IsSequence())
        {
            return false;
        }

        const ListKey key = containerSchema.listKey();
        return key.keyed() && key.field != "id" && key.field == segments.back();
    }

    bool patch(const YAML::Node &operation, std::string &error, int &failedStep)
    {
        const YAML::Node id = childOf(operation, "id");
        const YAML::Node file = childOf(operation, "file");
        const YAML::Node steps = childOf(operation, "patch");

        if ((!id.IsDefined() && !file.IsDefined()) || !steps.IsDefined() || !steps.IsSequence() || steps.size() == 0)
        {
            error = "patch needs `id` (an object, with `file` when the id is in more than one file) or `file` alone "
                    "(the file), and a `patch` list of JSON Patch steps";
            return false;
        }

        YAML::Node root;
        SchemaRef rootSchema;

        if (id.IsDefined())
        {
            std::string fileName;
            std::string listKey;
            size_t index = 0;

            if (!find(operation, id.Scalar(), fileName, listKey, index, error))
            {
                return false;
            }

            root.reset(document(fileName)[listKey][index]);
            rootSchema = fileSchema(fileName).property(listKey).items();
        }
        else
        {
            if (!changeable(file.Scalar(), error))
            {
                return false;
            }

            root.reset(document(file.Scalar()));
            rootSchema = fileSchema(file.Scalar());
        }

        int index = 0;

        for (const YAML::Node &step : steps)
        {
            failedStep = index;
            const std::string op = step.IsMap() && childOf(step, "op").IsDefined() ? step["op"].Scalar() : "";
            std::vector<std::string> path;
            std::vector<std::string> from;

            if (!step.IsMap() || !childOf(step, "path").IsDefined()
                || !splitPointer(step["path"].Scalar(), path, error))
            {
                error = error.empty() ? "a step needs `op` and `path`" : error;
                return false;
            }

            const bool needsFrom = op == "move" || op == "copy";

            if (needsFrom && (!childOf(step, "from").IsDefined() || !splitPointer(step["from"].Scalar(), from, error)))
            {
                error = error.empty() ? op + " needs `from`" : error;
                return false;
            }

            if (id.IsDefined() && ((!path.empty() && path[0] == "id") || (!from.empty() && from[0] == "id")))
            {
                error = "an object's id is not changed by a patch: use op rename";
                return false;
            }

            if (op != "test" && (pointsAtKey(root, rootSchema, path) || (!from.empty() && op == "move"
                && pointsAtKey(root, rootSchema, from))))
            {
                error = "a sub-object's key is not changed by a patch: use op rename {id, path, to}";
                return false;
            }

            const YAML::Node value = childOf(step, "value");
            const bool needsValue = op == "add" || op == "replace" || op == "test";

            if (needsValue && !value.IsDefined())
            {
                error = op + " needs `value`";
                return false;
            }

            bool done = false;

            if (op == "add" || op == "replace")
            {
                done = patchAdd(root, rootSchema, path, value, op == "replace", error);
            }
            else if (op == "remove")
            {
                done = patchRemove(root, rootSchema, path, error);
            }
            else if (op == "test")
            {
                YAML::Node current;
                std::string where;
                done = patchGet(root, rootSchema, path, current, error);

                if (done && !sameYaml(current, value, where))
                {
                    error = "test failed: the value at " + step["path"].Scalar() + " is not the one expected";
                    done = false;
                }
            }
            else if (needsFrom)
            {
                YAML::Node moved;
                done = patchGet(root, rootSchema, from, moved, error)
                    && (op == "copy" || patchRemove(root, rootSchema, from, error))
                    && patchAdd(root, rootSchema, path, moved, false, error);
            }
            else
            {
                error = "unknown patch op '" + op + "': add, remove, replace, move, copy or test";
            }

            if (!done)
            {
                return false;
            }

            ++index;
        }

        failedStep = -1;
        return true;
    }

    Project &m_project;
    std::set<std::string> *m_pTouched = nullptr;
    std::vector<HistoryRename> m_renames;
    std::vector<std::string> m_idsAllocated;
    std::vector<std::string> m_notes;
};

// The canonical texts of the project's source files.
std::map<std::string, std::string> canonicalTexts(const Project &project)
{
    std::map<std::string, std::string> texts;

    for (const std::pair<const std::string, ProjectFile> &file : project.files)
    {
        if (isSourceFile(file.first))
        {
            texts[file.first] = canonicalText(file.second);
        }
    }

    return texts;
}

// Whether every operation that touches one of `objects` is a patch with a `test` step (which guards a rebase at the
// value level).
bool guardedByTests(const YAML::Node &operations)
{
    for (const YAML::Node &operation : operations)
    {
        if (scalarText(operation, "op") != "patch")
        {
            return false;
        }

        bool tested = false;

        for (const YAML::Node &step : childOf(operation, "patch"))
        {
            tested = tested || scalarText(step, "op") == "test";
        }

        if (!tested)
        {
            return false;
        }
    }

    return true;
}
}
const char *const RevisionScheme = "source-sha256-128";

std::string projectRevision(const Project &project)
{
    return revisionOfCanonicalTexts(canonicalTexts(project));
}

std::string revisionOfCanonicalTexts(const std::map<std::string, std::string> &canonicalTexts)
{
    // Name and canonical text of each source file, in name order, each ended by a zero byte.
    std::string hashed;

    for (const std::pair<const std::string, std::string> &file : canonicalTexts)
    {
        if (isSourceFile(file.first))
        {
            hashed += file.first;
            hashed.push_back('\0');
            hashed += file.second;
            hashed.push_back('\0');
        }
    }

    return contentHash128(hashed);
}

std::vector<std::string> semanticDiff(const Project &before, const Project &after)
{
    std::vector<std::string> changes;

    for (const ProjectFileKind &kind : projectFileKinds())
    {
        const bool hadIt = before.has(kind.pName);
        const bool hasIt = after.has(kind.pName);

        if ((!hadIt && !hasIt) || kind.fileClass != ProjectFileClass::Source)
        {
            continue;
        }

        if (hadIt != hasIt)
        {
            changes.push_back(std::string(kind.pName) + (hasIt ? ": file added" : ": file removed"));

            for (const std::pair<const std::string, YAML::Node> &object :
                 idObjects((hasIt ? after : before).document(kind.pName)))
            {
                changes.push_back(std::string(kind.pName) + (hasIt ? ": added " : ": removed ") + object.first);
            }

            continue;
        }

        // A file whose tree is the same tree (a kept project's untouched file) has not changed.
        if (before.document(kind.pName).is(after.document(kind.pName)))
        {
            continue;
        }

        const std::map<std::string, YAML::Node> first = idObjects(before.document(kind.pName));
        const std::map<std::string, YAML::Node> second = idObjects(after.document(kind.pName));
        size_t found = 0;

        for (const std::pair<const std::string, YAML::Node> &object : second)
        {
            const std::map<std::string, YAML::Node>::const_iterator old = first.find(object.first);

            if (old == first.end())
            {
                changes.push_back(std::string(kind.pName) + ": added " + object.first);
                ++found;
                continue;
            }

            std::string where;

            if (sameYaml(old->second, object.second, where))
            {
                continue;
            }

            // Which fields differ.
            std::set<std::string> fields;

            for (const YAML::Node *pNode : {&old->second, &object.second})
            {
                const YAML::Node &other = pNode == &old->second ? object.second : old->second;

                for (YAML::const_iterator iterator = pNode->begin(); iterator != pNode->end(); ++iterator)
                {
                    const std::string key = iterator->first.Scalar();
                    const YAML::Node otherValue = childOf(other, key);
                    std::string unused;

                    if (!otherValue.IsDefined() || !sameYaml(iterator->second, otherValue, unused))
                    {
                        fields.insert(key);
                    }
                }
            }

            std::string list;

            for (const std::string &field : fields)
            {
                list += (list.empty() ? "" : ", ") + field;
                // A plain value is shown before and after; a list or map is only named.
                const YAML::Node was = childOf(old->second, field);
                const YAML::Node now = childOf(object.second, field);

                if ((!was.IsDefined() || was.IsScalar()) && (!now.IsDefined() || now.IsScalar()))
                {
                    const auto shown = [](const YAML::Node &value)
                    {
                        std::string text = value.IsDefined() ? value.Scalar() : std::string("none");
                        std::replace(text.begin(), text.end(), '\n', ' ');
                        return text.size() > 40 ? text.substr(0, 37) + "..." : text;
                    };
                    list += " (" + shown(was) + " -> " + shown(now) + ")";
                }
            }

            changes.push_back(std::string(kind.pName) + ": " + object.first + " changed " + list);
            ++found;
        }

        for (const std::pair<const std::string, YAML::Node> &object : first)
        {
            if (!second.contains(object.first))
            {
                changes.push_back(std::string(kind.pName) + ": removed " + object.first);
                ++found;
            }
        }

        // A change outside the id objects (the map card's fields, a start, defaults).
        std::string where;

        if (found == 0 && !sameYaml(before.document(kind.pName), after.document(kind.pName), where))
        {
            changes.push_back(std::string(kind.pName) + ": changed " + (where.empty() ? "its top level" : where));
        }
    }

    return changes;
}


std::vector<std::string> changedObjects(const Project &before, const Project &after)
{
    std::vector<std::string> objects;

    for (const ProjectFileKind &kind : projectFileKinds())
    {
        if (kind.fileClass != ProjectFileClass::Source || (!before.has(kind.pName) && !after.has(kind.pName)))
        {
            continue;
        }

        const std::vector<std::string> changed =
            changedUnits(kind.pName, before.document(kind.pName), after.document(kind.pName));
        objects.insert(objects.end(), changed.begin(), changed.end());
    }

    return objects;
}

const char *const HandEditedMessage =
    "this project is edited by hand (project.yml edited_by_hand): change it through operations (oymap edit, "
    "map_edit, edit.apply), never by running a generator again; a generator run erases the hand edits";

namespace
{
const char *const MarkField = "edited_by_hand";

std::string today()
{
    const std::string stamp = localTimestamp();
    return stamp.substr(0, 10);
}

// What a commit makes and how it is recorded: an edit's operations, a revert, a protect, a migration.
struct CommitWork
{
    std::string kind = "transaction";
    YAML::Node operations;
    int reverts = 0;
    std::string revertKind;
    // Makes the change on `edited` through `editor`; false: refused (result.errors and the refusal set).
    std::function<bool(Project &edited, Editor &editor, TransactionResult &result)> produce;
    // Files written with these bytes when their canonical text is what the change gives (a revert's snapshot).
    std::map<std::string, std::string> exactTexts;
    // Whether a person's change marks the project (a protect or its clearing writes the mark itself).
    bool mayMark = true;
    // A change of form only is written too (a migration writing keys and canonical form).
    bool formOnly = false;
    // A protect: the entry sets the mark (the head remembers which entry did).
    bool setsMark = false;
    // The keys of format 1 are written into the files the change touches; a revert puts files back as they were.
    bool fillKeys = true;
};

// The objects changed by the entries after `revision` (newest first, up to the entry that started from it), and
// those entries; false when the kept history does not reach back to it.
bool objectsChangedSince(const std::filesystem::path &projectRoot, const HistoryHead &head,
    const std::string &revision, std::set<std::string> &objects, std::vector<int> &entries)
{
    for (int sequence = head.count; sequence >= head.first && sequence >= 1; --sequence)
    {
        StoredHistoryEntry entry;
        std::string unused;

        if (!readHistoryEntry(projectRoot, sequence, false, entry, unused))
        {
            return false;
        }

        if (scalarText(entry.node, "revision_after") == revision)
        {
            return true;
        }

        entries.push_back(sequence);
        const YAML::Node listed = childOf(entry.node, "objects");

        if (listed.IsDefined())
        {
            for (const YAML::Node &object : listed)
            {
                objects.insert(object.Scalar());
            }
        }
        else if (readHistoryEntry(projectRoot, sequence, true, entry, unused))
        {
            // An entry written before S5b1: its objects from its files.
            for (const std::pair<const std::string, std::optional<std::string>> &file : entry.after)
            {
                const std::optional<std::string> &before = entry.before[file.first];
                const YAML::Node first = before ? YAML::Load(*before) : YAML::Node();
                const YAML::Node second = file.second ? YAML::Load(*file.second) : YAML::Node();

                for (const std::string &object : changedUnits(file.first, first, second))
                {
                    objects.insert(object);
                }
            }
        }

        if (scalarText(entry.node, "revision_before") == revision)
        {
            return true;
        }
    }

    return false;
}

bool commitInMemory(
    const std::filesystem::path &projectRoot,
    ProjectMemory &memory,
    TransactionChecks &checks,
    const TransactionOptions &options,
    CommitWork &work,
    TransactionResult &result,
    std::set<std::string> &changedFiles)
{
    changedFiles.clear();
    // The source files' bytes as they are on disk (the memory is up to the files).
    std::map<std::string, std::string> textsBefore;

    for (const std::pair<const std::string, ProjectFile> &file : memory.project.files)
    {
        if (isSourceFile(file.first))
        {
            textsBefore[file.first] = file.second.text;
        }
    }

    HistoryHead head;
    std::string errorMessage;

    // The history head is brought up to the files only when they changed since this process last did it.
    if (memory.headRevision != memory.revision || memory.headLockHash != memory.lockHash)
    {
        OutsideRecord outside;

        if (!syncOutsideEditsWith(projectRoot, memory.project, memory.revision, textsBefore, head, outside,
                errorMessage))
        {
            result.refusal = TransactionRefusal::Failed;
            result.errors.push_back(errorMessage);
            return false;
        }

        result.outsideChanges = outside.changes;
        result.outsideSequence = outside.sequence;
        result.outsideNotice = outside.notice;
        memory.headRevision = head.revision;
        memory.headLockHash = memory.lockHash;
    }
    else
    {
        head = readHistoryHead(projectRoot);
    }

    result.revisionBefore = head.revision;
    result.revisionAfter = head.revision;
    result.mark = markOf(memory.project, head, projectRoot);
    const bool stale = !options.expectRevision.empty() && options.expectRevision != head.revision;
    const auto refuseStale = [&](const std::string &why)
    {
        std::string changed;

        for (const std::string &change : result.outsideChanges)
        {
            changed += (changed.empty() ? "" : "; ") + change;
        }

        result.refusal = TransactionRefusal::StaleRevision;
        result.errors.push_back("the project is at revision " + head.revision + ", not " + options.expectRevision
            + (changed.empty() ? "" : " (since then: " + changed + ")") + why
            + ": read it again and send the operations against the new revision");
        return false;
    };

    if (stale && !options.rebase)
    {
        return refuseStale("");
    }

    const std::vector<ProjectIssue> issuesBefore = checks.before();
    // The change is made on copies of the trees it touches.
    Project edited = memory.project;
    std::set<std::string> touched;
    Editor editor(edited, &touched);

    if (!work.produce(edited, editor, result))
    {
        if (result.refusal == TransactionRefusal::None)
        {
            result.refusal = TransactionRefusal::BadOperation;
        }

        return false;
    }

    result.idsAllocated = editor.idsAllocated();
    result.notes.insert(result.notes.end(), editor.notes().begin(), editor.notes().end());
    // What the change touches (before the mark and the keys the core writes with it).
    const std::vector<std::string> objects = changedObjects(memory.project, edited);

    if (stale)
    {
        // A rebase (2.7): on the current revision, when nothing the change touches changed since the revision it was
        // made against, or its `test` steps hold (they were checked as the change was made).
        std::set<std::string> since;

        if (!objectsChangedSince(projectRoot, head, options.expectRevision, since, result.rebasedOver))
        {
            result.rebasedOver.clear();
            return refuseStale(" (the history kept does not reach back to it: no rebase)");
        }

        for (const std::string &object : objects)
        {
            if (since.contains(object))
            {
                result.clashes.push_back(object);
            }
        }

        if (!result.clashes.empty() && !guardedByTests(work.operations))
        {
            std::string clashing;

            for (const std::string &object : result.clashes)
            {
                clashing += (clashing.empty() ? "" : ", ") + object;
            }

            result.rebasedOver.clear();
            return refuseStale(" and the operations touch objects changed since (" + clashing + ")");
        }
    }

    result.changes = semanticDiff(memory.project, edited);
    bool markSetNow = false;

    if (work.mayMark && options.author == "user" && !result.mark.marked && !result.changes.empty())
    {
        // The first source transaction of a person marks the project (2.8); the mark's revision is the state before
        // it, the last one agents alone made.
        YAML::Node &card = editor.document("project.yml");
        YAML::Node mark(YAML::NodeType::Map);
        mark["since"] = today();
        YAML::Node revision(head.revision);
        revision.SetTag("!");
        mark["revision"] = revision;
        card[MarkField] = mark;
        result.changes.push_back("project.yml: marked as edited by hand (edited_by_hand since " + today()
            + "): agents change it by operations from now on");
        result.mark.marked = true;
        result.mark.setNow = true;
        result.mark.since = today();
        result.mark.revision = head.revision;
        result.mark.historyKnown = true;
        markSetNow = true;
    }

    // The keys of format 1, written into every keyed file the change touches (2.6 item 2).
    for (const std::string &name : std::set<std::string>(touched))
    {
        const std::map<std::string, ProjectFile>::iterator file = edited.files.find(name);

        if (!work.fillKeys || file == edited.files.end() || !isSourceFile(name)
            || !fileHasKeyedLists(file->second.schema))
        {
            continue;
        }

        std::vector<std::string> filled;
        const size_t count = fillMissingKeys(file->second.document, file->second.schema, &filled);
        const YAML::Node format = childOf(file->second.document, "format");

        if (!format.IsDefined() || format.Scalar() != "1")
        {
            file->second.document["format"] = 1;
        }

        for (const std::string &key : filled)
        {
            result.keysAllocated.push_back(name + " " + key);
        }

        if (count > 0)
        {
            result.changes.push_back(name + ": keys written for " + std::to_string(count)
                + " sub-object(s) (format 1)");
        }
    }

    // The canonical text of each touched file; the others keep theirs. A file the change removed is gone.
    std::map<std::string, std::string> canonicalAfter = memory.canonical;

    for (const std::string &name : touched)
    {
        if (!isSourceFile(name))
        {
            continue;
        }

        const std::map<std::string, ProjectFile>::iterator file = edited.files.find(name);

        if (file == edited.files.end())
        {
            if (canonicalAfter.erase(name) > 0)
            {
                changedFiles.insert(name);
            }

            continue;
        }

        const std::string text = canonicalText(file->second);
        const std::map<std::string, std::string>::const_iterator old = memory.canonical.find(name);

        if (old == memory.canonical.end() || old->second != text)
        {
            changedFiles.insert(name);
            canonicalAfter[name] = text;
            // What would be written; the tree stands as edited (checked as it is, not read back from the text).
            file->second.text = text;
        }
    }

    const std::vector<ProjectIssue> issuesAfter = checks.after(edited, changedFiles);
    result.newIssues = issuesOnlyIn(issuesAfter, issuesBefore);
    result.fixedIssues = issuesOnlyIn(issuesBefore, issuesAfter);
    result.revisionAfter = revisionOfCanonicalTexts(canonicalAfter);

    for (const std::string &name : changedFiles)
    {
        const std::map<std::string, std::string>::const_iterator text = canonicalAfter.find(name);

        if (text != canonicalAfter.end())
        {
            result.filesAfter[name] = text->second;
        }
    }

    // Agents are told which objects a person changed last (as far as the kept history shows).
    if (result.mark.marked && !markSetNow && options.author != "user")
    {
        for (const std::pair<const std::string, std::string> &author : lastAuthors(projectRoot, head, objects))
        {
            if (author.second == "user")
            {
                result.handObjects.push_back(author.first);
            }
        }
    }

    if (hasErrors(result.newIssues) && !options.allowNewIssues)
    {
        result.refusal = TransactionRefusal::NewIssues;
        result.errors.push_back("the change introduces " + std::to_string(result.newIssues.size())
            + " validation issue(s); nothing was written (fix the operations, or allow new issues)");
        return false;
    }

    if (options.dryRun || (result.changes.empty() && !(work.formOnly && !changedFiles.empty())))
    {
        return true;
    }

    // Files the change did not change keep their bytes; a revert's file comes back byte for byte.
    std::map<std::string, std::string> textsAfter = textsBefore;

    for (const std::string &name : changedFiles)
    {
        const std::map<std::string, std::string>::const_iterator text = canonicalAfter.find(name);

        if (text == canonicalAfter.end())
        {
            textsAfter.erase(name);
            continue;
        }

        textsAfter[name] = text->second;
        const std::map<std::string, std::string>::const_iterator exact = work.exactTexts.find(name);

        if (exact != work.exactTexts.end() && exact->second != text->second)
        {
            try
            {
                const ProjectFile parsed{name, edited.files.at(name).schema, exact->second, YAML::Load(exact->second)};

                if (canonicalText(parsed) == text->second)
                {
                    textsAfter[name] = exact->second;
                    edited.files.at(name).text = exact->second;
                }
            }
            catch (const YAML::Exception &)
            {
            }
        }
    }

    const std::set<std::string> names = changedNames(textsBefore, textsAfter);

    if (!writeFileSet(projectRoot, textsAfter, names, errorMessage))
    {
        result.refusal = TransactionRefusal::Failed;
        result.errors.push_back(errorMessage);
        return false;
    }

    NewHistoryEntry entry;
    entry.kind = work.kind;
    entry.author = options.author.empty() ? std::string("agent") : options.author;
    entry.label = options.label;
    entry.revisionBefore = head.revision;
    entry.revisionAfter = result.revisionAfter;
    entry.changes = result.changes;
    entry.operations = work.operations;
    entry.before = versionsOf(textsBefore, names);
    entry.after = versionsOf(textsAfter, names);
    entry.reverts = work.reverts;
    entry.revertKind = work.revertKind;
    // The entry that marks the project stays an entry of its own.
    entry.mergeKey = work.reverts == 0 && !markSetNow ? options.mergeKey : std::string();
    entry.renames = editor.renames();
    entry.objects = objects;
    bool merged = false;

    if (!entry.mergeKey.empty() && !markSetNow
        && !mergeIntoLatestEntry(projectRoot, head, entry, 5, merged, errorMessage))
    {
        result.refusal = TransactionRefusal::Failed;
        result.errors.push_back(errorMessage);
        return false;
    }

    if (!merged && !appendHistoryEntry(projectRoot, head, entry, errorMessage))
    {
        result.refusal = TransactionRefusal::Failed;
        result.errors.push_back(errorMessage);
        return false;
    }

    result.merged = merged;
    result.sequence = head.count;

    if (markSetNow || work.setsMark)
    {
        head.markSequence = head.count;
        head.markRevision = result.mark.revision;
        writeHistoryHead(projectRoot, head, errorMessage);
    }

    // Renames move the lock's entries (with their numbers) and the pins (2.4.1, 2.6 item 4).
    if (!editor.renames().empty())
    {
        std::vector<std::pair<std::string, std::string>> pairs;

        for (const HistoryRename &rename : editor.renames())
        {
            pairs.emplace_back(rename.from, rename.to);
        }

        const std::map<std::string, ProjectFile>::iterator lock = edited.files.find("ids.lock.yml");

        if (lock != edited.files.end() && lock->second.document.IsMap())
        {
            YAML::Node document = YAML::Clone(lock->second.document);
            const std::vector<std::string> moved = renameLockEntries(document, pairs);

            if (!moved.empty())
            {
                const std::string lockText =
                    writeCanonicalYaml(document, SchemaSet::builtIn(), "ids_lock.schema.json");
                bool changed = false;

                if (!writeLockRecordHeld(projectRoot, lockText, result.revisionAfter, "rename", changed, errorMessage))
                {
                    result.notes.push_back("the lock's entries could not follow the rename: " + errorMessage);
                }
                else
                {
                    const ProjectFile written{lock->second.name, lock->second.schema, lockText, document};
                    edited.files.erase(lock);
                    edited.files.emplace("ids.lock.yml", written);
                    memory.lockHash = lockHashOfText(&lockText);

                    for (const std::string &line : moved)
                    {
                        result.notes.push_back("ids.lock.yml: " + line);
                    }
                }
            }
        }

        std::vector<std::string> renamedPins;

        if (!renamePinAnchors(projectRoot, pairs, renamedPins, errorMessage))
        {
            result.notes.push_back("the pins could not follow the rename: " + errorMessage);
        }

        for (const std::string &line : renamedPins)
        {
            result.notes.push_back("review/pins.yml: " + line);
        }
    }

    memory.project = std::move(edited);
    memory.canonical = std::move(canonicalAfter);
    memory.revision = result.revisionAfter;
    memory.headRevision = result.revisionAfter;
    memory.headLockHash = memory.lockHash;
    result.applied = true;
    return true;
}

// The checks of a transaction read from the files (the command line): the whole validation before and after, the
// edited files through their canonical text and back.
class FileChecks : public TransactionChecks
{
public:
    FileChecks(const Project &project, const std::filesystem::path &assetRoot)
        : m_project(project)
    {
        m_options.assetRoot = assetRoot;
    }

    std::vector<ProjectIssue> before() override
    {
        std::vector<ProjectIssue> issues;
        validateProject(m_project, m_options, issues);
        return issues;
    }

    std::vector<ProjectIssue> after(const Project &edited, const std::set<std::string> &changed) override
    {
        (void)changed;
        std::map<std::string, std::string> texts = canonicalTexts(edited);

        for (const std::pair<const std::string, ProjectFile> &file : edited.files)
        {
            if (!isSourceFile(file.first))
            {
                texts[file.first] = file.second.text;
            }
        }

        std::vector<ProjectIssue> issues;
        validateProject(projectFromTexts(edited.root, texts), m_options, issues);
        return issues;
    }

private:
    const Project &m_project;
    BuildOptions m_options;
};

// A project read from its files into the form the commit keeps.
bool memoryFromFiles(const std::filesystem::path &projectRoot, ProjectMemory &memory, TransactionResult &result)
{
    memory = {};
    std::vector<ProjectIssue> loadIssues;

    if (!loadProject(projectRoot, memory.project, loadIssues))
    {
        result.refusal = TransactionRefusal::NotAProject;

        for (const ProjectIssue &issue : loadIssues)
        {
            result.errors.push_back(issue.file + ": " + issue.message);
        }

        return false;
    }

    memory.canonical = canonicalTexts(memory.project);
    memory.revision = revisionOfCanonicalTexts(memory.canonical);
    memory.lockHash = projectLockHash(projectRoot);
    return true;
}

// Runs a commit on the files, under the project lock.
bool commitOnFiles(const std::filesystem::path &projectRoot, const TransactionOptions &options, CommitWork &work,
    TransactionResult &result)
{
    result = {};
    ProjectWriteLock lock(projectRoot);

    if (!lock.held())
    {
        result.refusal = TransactionRefusal::Locked;
        result.errors.push_back(ProjectLockedMessage);
        return false;
    }

    ProjectMemory memory;

    if (!memoryFromFiles(projectRoot, memory, result))
    {
        return false;
    }

    FileChecks checks(memory.project, options.assetRoot);
    std::set<std::string> changed;
    return commitInMemory(projectRoot, memory, checks, options, work, result, changed);
}

CommitWork operationsWork(const YAML::Node &operations)
{
    CommitWork work;
    work.operations = operations;
    work.produce = [operations](Project &, Editor &editor, TransactionResult &result)
    {
        if (!operations.IsDefined() || !operations.IsSequence())
        {
            result.refusal = TransactionRefusal::BadOperation;
            result.errors.push_back("the operations are a list of maps, each with an `op`");
            return false;
        }

        size_t index = 0;

        for (const YAML::Node &operation : operations)
        {
            std::string error;
            int step = -1;

            if (!editor.apply(operation, error, step))
            {
                if (result.refusal == TransactionRefusal::None)
                {
                    result.refusal = TransactionRefusal::BadOperation;
                    result.failedOperation = static_cast<int>(index);
                    result.failedStep = step;
                }

                result.errors.push_back("operation " + std::to_string(index) + ": " + error);
            }

            ++index;
        }

        return result.errors.empty();
    };
    return work;
}

// --- reverts --------------------------------------------------------------------------------------------------

struct EntryHeader
{
    int sequence = 0;
    YAML::Node node;
    bool reverted = false;
};

// The kept entries, oldest first, with whether each is reverted by a revert entry in effect.
std::vector<EntryHeader> readEntryHeaders(const std::filesystem::path &projectRoot, const HistoryHead &head)
{
    std::vector<EntryHeader> entries;

    for (int sequence = head.first; sequence <= head.count; ++sequence)
    {
        StoredHistoryEntry entry;
        std::string unused;

        if (readHistoryEntry(projectRoot, sequence, false, entry, unused))
        {
            entries.push_back({sequence, entry.node, false});
        }
    }

    // Newest first: a revert in effect reverts its target (a revert entry only names earlier entries).
    std::map<int, size_t> bySequence;

    for (size_t index = 0; index < entries.size(); ++index)
    {
        bySequence[entries[index].sequence] = index;
    }

    for (size_t index = entries.size(); index-- > 0;)
    {
        const YAML::Node reverts = childOf(entries[index].node, "reverts");

        if (!entries[index].reverted && reverts.IsDefined())
        {
            const std::map<int, size_t>::const_iterator target = bySequence.find(reverts.as<int>());

            if (target != bySequence.end())
            {
                entries[target->second].reverted = true;
            }
        }
    }

    return entries;
}

bool changesSourceFiles(const YAML::Node &node)
{
    for (const YAML::Node &name : childOf(node, "files"))
    {
        if (isSourceFile(name.Scalar()))
        {
            return true;
        }
    }

    return false;
}

std::string firstChange(const YAML::Node &node)
{
    const YAML::Node changes = childOf(node, "changes");
    return changes.IsDefined() && changes.IsSequence() && changes.size() > 0 ? changes[0].Scalar() : std::string();
}

// Splits a sub-object's address (`room:x/pillars/big`) into its owner and the pointer to it.
void splitAddress(const std::string &address, std::string &owner, std::string &path)
{
    const size_t slash = address.find('/');
    owner = address.substr(0, slash);
    path = slash == std::string::npos ? std::string() : address.substr(slash);
}

// Runs the opposite of an entry's renames, newest first, through `editor`.
bool renameBack(Editor &editor, const YAML::Node &renames, std::string &error)
{
    std::vector<std::pair<std::string, std::string>> pairs;

    for (const YAML::Node &rename : renames)
    {
        pairs.emplace_back(scalarText(rename, "from"), scalarText(rename, "to"));
    }

    for (size_t index = pairs.size(); index-- > 0;)
    {
        const std::string &from = pairs[index].first;
        const std::string &to = pairs[index].second;

        if (to.find('/') == std::string::npos)
        {
            if (!editor.renameId(to, from, "", error))
            {
                return false;
            }

            continue;
        }

        std::string owner;
        std::string path;
        splitAddress(to, owner, path);
        YAML::Node operation(YAML::NodeType::Map);
        const std::string oldKey = from.substr(from.rfind('/') + 1);

        if (!editor.renameKey(operation, owner, path, oldKey, error))
        {
            return false;
        }
    }

    return true;
}

// Puts the units of one file back as they were before an entry (S5_BROWSER_EDITOR.md 2.7): a unit still as the
// entry left it is put back; one changed since is a conflict, left alone unless `force`. `exact`: the whole file is
// as the entry left it, so it comes back as it was, byte for byte.
void revertFile(const std::string &name, YAML::Node &current, const YAML::Node &before, const YAML::Node &after,
    bool force, std::vector<std::string> &conflicts, bool &exact)
{
    std::string where;
    exact = false;

    if (current.IsDefined() && after.IsDefined() && sameYaml(current, after, where))
    {
        // The hand-edit mark is never reverted (2.8): only a person clears it.
        const bool keepMark = name == "project.yml" && childOf(current, MarkField).IsDefined()
            && !childOf(before, MarkField).IsDefined();
        const YAML::Node mark = keepMark ? YAML::Clone(childOf(current, MarkField)) : YAML::Node();
        current = before.IsDefined() ? YAML::Clone(before) : YAML::Node(YAML::NodeType::Map);
        exact = !keepMark;

        if (keepMark)
        {
            current[MarkField] = mark;
        }

        return;
    }

    const std::map<std::string, Unit> first = unitsOf(name, before);
    const std::map<std::string, Unit> second = unitsOf(name, after);
    std::set<std::string> changed;

    for (const std::string &unit : changedUnits(name, before, after))
    {
        changed.insert(unit);
    }

    for (const std::string &unitName : changed)
    {
        if (unitName == name + "#/" + MarkField)
        {
            continue;
        }

        const std::map<std::string, Unit> now = unitsOf(name, current);
        const Unit *pBefore = unitIn(first, unitName);
        const Unit *pAfter = unitIn(second, unitName);
        const Unit *pNow = unitIn(now, unitName);

        if (!sameUnit(pAfter, pNow) && !force)
        {
            conflicts.push_back(unitName);
            continue;
        }

        const Unit *pAny = pBefore != nullptr ? pBefore : pAfter;

        if (!pAny->item)
        {
            if (pBefore != nullptr)
            {
                current[pAny->key] = YAML::Clone(pBefore->node);
            }
            else
            {
                current.remove(pAny->key);
            }

            continue;
        }

        // An item of a top-level list: replaced, dropped, or put back after the nearest item before it in the old
        // list that is there now.
        const YAML::Node list = childOf(current, pAny->key);
        YAML::Node rebuilt(YAML::NodeType::Sequence);
        size_t insertAt = 0;

        if (pNow == nullptr && pBefore != nullptr)
        {
            const YAML::Node oldList = childOf(before, pBefore->key);

            for (size_t index = pBefore->index; index-- > 0;)
            {
                const std::string previous = name + "#" + scalarText(oldList[index], "id");
                const Unit *pPrevious = unitIn(now, previous);

                if (pPrevious != nullptr && pPrevious->item && pPrevious->key == pBefore->key)
                {
                    insertAt = pPrevious->index + 1;
                    break;
                }
            }
        }

        size_t position = 0;

        if (pNow == nullptr && pBefore != nullptr && insertAt == 0)
        {
            rebuilt.push_back(YAML::Clone(pBefore->node));
        }

        for (size_t index = 0; list.IsDefined() && list.IsSequence() && index < list.size(); ++index)
        {
            if (pNow != nullptr && index == pNow->index)
            {
                if (pBefore != nullptr)
                {
                    rebuilt.push_back(YAML::Clone(pBefore->node));
                }
            }
            else
            {
                rebuilt.push_back(list[index]);
            }

            ++position;

            if (pNow == nullptr && pBefore != nullptr && insertAt != 0 && position == insertAt)
            {
                rebuilt.push_back(YAML::Clone(pBefore->node));
            }
        }

        if (rebuilt.size() == 0)
        {
            current.remove(pAny->key);
        }
        else
        {
            current[pAny->key] = rebuilt;
        }
    }
}
}

const char *const RevertKindNames[] = {"undo", "redo", "revert"};

int revertTarget(const std::filesystem::path &projectRoot, RevertKind kind, const std::string &author,
    std::string &reason)
{
    const HistoryHead head = readHistoryHead(projectRoot);
    const std::vector<EntryHeader> entries = readEntryHeaders(projectRoot, head);
    const auto whose = [&author](const EntryHeader &entry)
    {
        return author == "*" || scalarText(entry.node, "author") == author;
    };

    if (kind == RevertKind::Undo)
    {
        for (size_t index = entries.size(); index-- > 0;)
        {
            const EntryHeader &entry = entries[index];

            if (whose(entry) && !entry.reverted && scalarText(entry.node, "revert_kind") != "undo"
                && changesSourceFiles(entry.node))
            {
                return entry.sequence;
            }
        }

        reason = "nothing to undo" + (author == "*" ? std::string() : " for " + author);
        return 0;
    }

    for (size_t index = entries.size(); index-- > 0;)
    {
        const EntryHeader &entry = entries[index];

        if (!whose(entry))
        {
            continue;
        }

        const std::string revertKind = scalarText(entry.node, "revert_kind");

        if (revertKind == "undo" && !entry.reverted)
        {
            return entry.sequence;
        }

        // A change of the author's own after the undos ends the redo chain, as in every editor.
        if (revertKind != "undo" && revertKind != "redo")
        {
            break;
        }
    }

    reason = "nothing to redo" + (author == "*" ? std::string() : " for " + author);
    return 0;
}

bool revertInMemory(
    const std::filesystem::path &projectRoot,
    ProjectMemory &memory,
    TransactionChecks &checks,
    const RevertRequest &request,
    const TransactionOptions &options,
    TransactionResult &result,
    std::set<std::string> &changedFiles)
{
    result = {};
    changedFiles.clear();
    int target = request.sequence;

    if (request.kind != RevertKind::Revert)
    {
        std::string reason;
        target = revertTarget(projectRoot, request.kind, request.whose.empty() ? options.author : request.whose,
            reason);

        if (target == 0)
        {
            result.refusal = TransactionRefusal::NothingToRevert;
            result.errors.push_back(reason);
            return false;
        }
    }

    StoredHistoryEntry entry;
    std::string errorMessage;

    if (target <= 0 || !readHistoryEntry(projectRoot, target, true, entry, errorMessage))
    {
        result.refusal = TransactionRefusal::NothingToRevert;
        result.errors.push_back(errorMessage.empty() ? "no history entry " + std::to_string(target) : errorMessage);
        return false;
    }

    CommitWork work;
    work.kind = "revert";
    work.reverts = target;
    work.revertKind = RevertKindNames[static_cast<int>(request.kind)];
    work.mayMark = true;
    work.fillKeys = false;
    YAML::Node operation(YAML::NodeType::Map);
    operation["op"] = "revert";
    operation["entry"] = target;
    work.operations.push_back(operation);
    TransactionOptions revertOptions = options;

    if (revertOptions.label.empty())
    {
        const std::string label = scalarText(entry.node, "label");
        revertOptions.label = work.revertKind + ": " + (label.empty() ? firstChange(entry.node) : label);
    }

    revertOptions.mergeKey.clear();
    std::map<std::string, std::string> &exactTexts = work.exactTexts;
    const bool force = request.force;
    work.produce = [&entry, &exactTexts, force](Project &edited, Editor &editor, TransactionResult &result)
    {
        std::string error;
        const YAML::Node renames = childOf(entry.node, "renames");
        // The entry's after texts, with its renames run backwards like the current files', so objects compare by
        // their names before the entry.
        std::map<std::string, YAML::Node> afterDocuments;

        if (renames.IsDefined() && renames.size() > 0)
        {
            Project afterProject = edited;

            for (const std::pair<const std::string, std::optional<std::string>> &file : entry.after)
            {
                const std::map<std::string, ProjectFile>::iterator found = afterProject.files.find(file.first);

                if (file.second && found != afterProject.files.end())
                {
                    // The entry is replaced, not assigned to (assigning a yaml-cpp node rebinds the node it shares
                    // data with: the edited project's).
                    const ProjectFile replaced{found->second.name, found->second.schema, *file.second,
                        YAML::Load(*file.second)};
                    afterProject.files.erase(found);
                    afterProject.files.emplace(file.first, replaced);
                }
            }

            std::set<std::string> scratchTouched;
            Editor scratch(afterProject, &scratchTouched);

            if (!renameBack(scratch, renames, error) || !renameBack(editor, renames, error))
            {
                result.errors.push_back("the opposite rename does not apply: " + error);
                return false;
            }

            for (const std::pair<const std::string, std::optional<std::string>> &file : entry.after)
            {
                if (file.second && afterProject.files.contains(file.first))
                {
                    afterDocuments[file.first] = afterProject.files[file.first].document;
                }
            }
        }

        for (const std::pair<const std::string, std::optional<std::string>> &file : entry.after)
        {
            if (!isSourceFile(file.first))
            {
                continue;
            }

            const std::optional<std::string> &beforeText = entry.before[file.first];
            const YAML::Node before = beforeText ? YAML::Load(*beforeText) : YAML::Node();
            const YAML::Node after = afterDocuments.contains(file.first) ? afterDocuments[file.first]
                : file.second ? YAML::Load(*file.second) : YAML::Node();

            if (!edited.has(file.first) && !before.IsDefined())
            {
                continue;
            }

            YAML::Node &current = editor.document(file.first);
            bool exact = false;
            revertFile(file.first, current, before, after, force, result.conflicts, exact);

            // A file the entry made, still as it left it: removed again.
            if (exact && !beforeText)
            {
                edited.files.erase(file.first);
                continue;
            }

            if (exact && beforeText)
            {
                exactTexts[file.first] = *beforeText;
            }
        }

        return true;
    };

    return commitInMemory(projectRoot, memory, checks, revertOptions, work, result, changedFiles);
}

bool revertProject(
    const std::filesystem::path &projectRoot,
    const RevertRequest &request,
    const TransactionOptions &options,
    TransactionResult &result)
{
    result = {};
    ProjectWriteLock lock(projectRoot);

    if (!lock.held())
    {
        result.refusal = TransactionRefusal::Locked;
        result.errors.push_back(ProjectLockedMessage);
        return false;
    }

    ProjectMemory memory;

    if (!memoryFromFiles(projectRoot, memory, result))
    {
        return false;
    }

    FileChecks checks(memory.project, options.assetRoot);
    std::set<std::string> changed;
    return revertInMemory(projectRoot, memory, checks, request, options, result, changed);
}

namespace
{
bool stepHistory(const std::filesystem::path &projectRoot, bool undo, std::vector<std::string> &changes,
    std::string &errorMessage)
{
    RevertRequest request;
    request.kind = undo ? RevertKind::Undo : RevertKind::Redo;
    request.whose = "*";
    TransactionOptions options;
    options.author = "agent";
    options.allowNewIssues = true;
    TransactionResult result;

    if (!revertProject(projectRoot, request, options, result))
    {
        errorMessage = result.errors.empty() ? std::string("refused") : result.errors.front();
        return false;
    }

    for (const std::string &change : result.changes)
    {
        changes.push_back(std::string(undo ? "undone: " : "redone: ") + change);
    }

    for (const std::string &conflict : result.conflicts)
    {
        changes.push_back("left alone (changed since): " + conflict);
    }

    return true;
}
}

bool undoProject(const std::filesystem::path &projectRoot, std::vector<std::string> &changes, std::string &errorMessage)
{
    return stepHistory(projectRoot, true, changes, errorMessage);
}

bool redoProject(const std::filesystem::path &projectRoot, std::vector<std::string> &changes, std::string &errorMessage)
{
    return stepHistory(projectRoot, false, changes, errorMessage);
}

bool applyTransaction(
    const std::filesystem::path &projectRoot,
    const YAML::Node &operations,
    const TransactionOptions &options,
    TransactionResult &result)
{
    CommitWork work = operationsWork(operations);
    return commitOnFiles(projectRoot, options, work, result);
}

bool applyTransactionInMemory(
    const std::filesystem::path &projectRoot,
    ProjectMemory &memory,
    TransactionChecks &checks,
    const YAML::Node &operations,
    const TransactionOptions &options,
    TransactionResult &result,
    std::set<std::string> &changedFiles)
{
    result = {};
    CommitWork work = operationsWork(operations);
    return commitInMemory(projectRoot, memory, checks, options, work, result, changedFiles);
}

HandMark handMarkOf(const std::filesystem::path &projectRoot, const Project &project)
{
    HistoryHead head = readHistoryHead(projectRoot);
    return markOf(project, head, projectRoot);
}

bool protectProject(const std::filesystem::path &projectRoot, bool clear, TransactionResult &result)
{
    CommitWork work;
    work.mayMark = false;
    work.setsMark = !clear;
    YAML::Node operation(YAML::NodeType::Map);
    operation["op"] = clear ? "unprotect" : "protect";
    work.operations.push_back(operation);
    work.produce = [clear, &projectRoot](Project &edited, Editor &editor, TransactionResult &result)
    {
        const bool marked = childOf(edited.document("project.yml"), MarkField).IsDefined();

        if (marked != clear)
        {
            return true;
        }

        YAML::Node &card = editor.document("project.yml");

        if (clear)
        {
            card.remove(MarkField);
            return true;
        }

        YAML::Node mark(YAML::NodeType::Map);
        mark["since"] = today();
        YAML::Node revision(readHistoryHead(projectRoot).revision);
        revision.SetTag("!");
        mark["revision"] = revision;
        card[MarkField] = mark;
        result.mark.revision = revision.Scalar();
        return true;
    };
    TransactionOptions options;
    options.author = "user";
    options.label = clear ? "clear the hand-edit mark" : "protect this project";
    options.allowNewIssues = true;
    const bool done = commitOnFiles(projectRoot, options, work, result);

    if (done)
    {
        Project project;
        std::vector<ProjectIssue> unused;
        loadProject(projectRoot, project, unused);
        result.mark = handMarkOf(projectRoot, project);
    }

    return done;
}

bool migrateProject(const std::filesystem::path &projectRoot, bool dryRun, TransactionResult &result)
{
    CommitWork work;
    work.kind = "migration";
    work.mayMark = false;
    work.formOnly = true;
    YAML::Node operation(YAML::NodeType::Map);
    operation["op"] = "migrate";
    work.operations.push_back(operation);
    work.produce = [](Project &edited, Editor &editor, TransactionResult &)
    {
        for (const ProjectFileKind &kind : projectFileKinds())
        {
            if (kind.fileClass == ProjectFileClass::Source && edited.has(kind.pName))
            {
                editor.document(kind.pName);
            }
        }

        return true;
    };
    TransactionOptions options;
    options.author = "migration";
    options.label = "format 1: keys written, canonical form";
    options.allowNewIssues = true;
    options.dryRun = dryRun;
    return commitOnFiles(projectRoot, options, work, result);
}

bool projectStatus(const std::filesystem::path &projectRoot, ProjectStatus &status, std::string &errorMessage)
{
    status = {};
    ProjectWriteLock lock(projectRoot);

    if (!lock.held())
    {
        errorMessage = ProjectLockedMessage;
        return false;
    }

    Project project;
    std::vector<ProjectIssue> issues;

    if (!loadProject(projectRoot, project, issues))
    {
        errorMessage = issues.empty() ? "not a project" : issues.front().message;
        return false;
    }

    HistoryHead head;
    // A source file that does not parse (a generator half way, a typo in a text editor) is not an edit to record:
    // read as missing it would enter the history as a removal. The history waits until it parses again
    // (S5_BROWSER_EDITOR.md 2.4.3); the revision reported meanwhile is the last one recorded.
    const bool unparsed = std::any_of(issues.begin(), issues.end(),
        [](const ProjectIssue &issue) { return issue.code == "yaml"; });

    if (unparsed)
    {
        head = readHistoryHead(projectRoot);
    }
    else
    {
        OutsideRecord outside;

        if (!syncOutsideEdits(projectRoot, project, head, outside, errorMessage))
        {
            return false;
        }

        status.outsideChanges = outside.changes;
        status.outsideSequence = outside.sequence;
        status.outsideNotice = outside.notice;
    }

    status.revision = head.revision.empty() ? projectRevision(project) : head.revision;
    status.lockHash = projectLockHash(projectRoot);
    status.mark = markOf(project, head, projectRoot);

    for (const EntryHeader &header : readEntryHeaders(projectRoot, head))
    {
        const YAML::Node &node = header.node;
        HistoryEntry entry;
        entry.sequence = header.sequence;
        entry.kind = scalarText(node, "kind");
        entry.author = childOf(node, "author").IsDefined() ? scalarText(node, "author")
            : entry.kind == "outside" ? std::string("outside") : std::string();
        entry.label = scalarText(node, "label");
        entry.revisionBefore = scalarText(node, "revision_before");
        entry.revisionAfter = scalarText(node, "revision_after");
        entry.undone = header.reverted;
        entry.time = scalarText(node, "time");
        entry.reverts = childOf(node, "reverts").IsDefined() ? node["reverts"].as<int>() : 0;
        entry.revertKind = scalarText(node, "revert_kind");
        entry.mergeKey = scalarText(node, "merge_key");
        entry.merged = childOf(node, "merged").IsDefined() ? node["merged"].as<int>() : 1;

        for (const YAML::Node &change : childOf(node, "changes"))
        {
            entry.changes.push_back(change.Scalar());
        }

        for (const YAML::Node &object : childOf(node, "objects"))
        {
            entry.objects.push_back(object.Scalar());
        }

        for (const YAML::Node &line : childOf(node, "notice"))
        {
            entry.notice.push_back(line.Scalar());
        }

        status.history.push_back(entry);
    }

    return true;
}
const char *const ProjectLockedMessage =
    "another oymap process is writing this project (.oymap/lock exists; remove it if that process died)";

std::filesystem::path projectStateRoot(const std::filesystem::path &projectRoot, bool create)
{
    const std::filesystem::path root = stateRoot(projectRoot);

    if (create)
    {
        std::error_code error;
        std::filesystem::create_directories(root, error);

        if (!std::filesystem::exists(root / ".gitignore", error))
        {
            std::string unused;
            writeTextFileAtomically(root / ".gitignore", "*\n", unused);
        }
    }

    return root;
}

ProjectWriteLock::ProjectWriteLock(const std::filesystem::path &projectRoot, int waitMilliseconds)
    : m_path(stateRoot(projectRoot) / "lock")
{
    std::error_code error;
    std::filesystem::create_directories(m_path.parent_path(), error);
    const std::chrono::steady_clock::time_point until =
        std::chrono::steady_clock::now() + std::chrono::milliseconds(waitMilliseconds);

    // "x": fail when the file exists, so only one writer holds the lock. The file holds the writer's process number:
    // a lock whose writer no longer runs (it crashed or was killed) is taken over instead of blocking the project
    // for good.
    while (true)
    {
        for (int attempt = 0; attempt < 2 && !m_held; ++attempt)
        {
            std::FILE *pFile = std::fopen(m_path.string().c_str(), "wx");

            if (pFile != nullptr)
            {
                std::fprintf(pFile, "%ld\n", currentProcessNumber());
                std::fclose(pFile);
                m_held = true;
                break;
            }

            long holder = 0;
            std::FILE *pExisting = std::fopen(m_path.string().c_str(), "r");

            if (pExisting != nullptr)
            {
                if (std::fscanf(pExisting, "%ld", &holder) != 1)
                {
                    holder = 0;
                }

                std::fclose(pExisting);
            }

            if (processRuns(holder))
            {
                break;
            }

            std::filesystem::remove(m_path, error);
        }

        if (m_held || std::chrono::steady_clock::now() >= until)
        {
            break;
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(20));
    }

    if (m_held)
    {
        projectStateRoot(projectRoot, true);
    }
}

ProjectWriteLock::~ProjectWriteLock()
{
    if (m_held)
    {
        std::error_code error;
        std::filesystem::remove(m_path, error);
    }
}

bool ProjectWriteLock::held() const
{
    return m_held;
}

bool recordOutsideEdits(
    const std::filesystem::path &projectRoot,
    const std::string &author,
    const std::string &label,
    RecordResult &result,
    std::string &errorMessage)
{
    result = {};

    if (author.empty() || author == "outside")
    {
        errorMessage = "record needs an author other than `outside`: user, or agent:<name>";
        return false;
    }

    ProjectWriteLock lock(projectRoot);

    if (!lock.held())
    {
        errorMessage = ProjectLockedMessage;
        return false;
    }

    Project project;
    std::vector<ProjectIssue> issues;

    if (!loadProject(projectRoot, project, issues))
    {
        errorMessage = issues.empty() ? "not a project" : issues.front().message;
        return false;
    }

    HistoryHead head;
    OutsideRecord outside;
    // A project without a history (made by a generator, never built or formatted): its files as they are become the
    // first entry, the author's, instead of a silent baseline that leaves nothing to record.
    const bool firstSight = readHistoryHead(projectRoot).revision.empty();

    if (!syncOutsideEdits(projectRoot, project, head, outside, errorMessage))
    {
        return false;
    }

    if (firstSight)
    {
        const std::map<std::string, std::string> files = fileTexts(projectRoot);
        NewHistoryEntry entry;
        entry.kind = "outside";
        entry.author = "outside";
        entry.revisionBefore = head.revision;
        entry.revisionAfter = head.revision;
        entry.changes.push_back("the project's " + std::to_string(files.size())
            + " files as first recorded: its history starts here");

        if (!appendHistoryEntry(projectRoot, head, entry, errorMessage))
        {
            return false;
        }
    }

    result.revision = head.revision;
    std::vector<StoredHistoryEntry> entries;

    for (int sequence = head.first; sequence <= head.count; ++sequence)
    {
        StoredHistoryEntry entry;

        if (readHistoryEntry(projectRoot, sequence, false, entry, errorMessage))
        {
            entries.push_back(entry);
        }
    }

    errorMessage.clear();
    // Since this author's latest entry.
    size_t first = 0;

    for (size_t index = 0; index < entries.size(); ++index)
    {
        if (scalarText(entries[index].node, "author") == author)
        {
            first = index + 1;
        }
    }

    for (size_t index = first; index < entries.size(); ++index)
    {
        YAML::Node entry = entries[index].node;
        const YAML::Node entryAuthor = childOf(entry, "author");
        const bool unattributed = !entryAuthor.IsDefined() || entryAuthor.Scalar() == "outside";

        if (scalarText(entry, "kind") != "outside" || !unattributed)
        {
            continue;
        }

        entry["author"] = author;

        if (!label.empty())
        {
            YAML::Node labelNode(label);
            labelNode.SetTag("!");
            entry["label"] = labelNode;
        }

        if (!writeTextFileAtomically(historyEntryRoot(projectRoot, entries[index].sequence) / "entry.yml",
                writeCanonicalYaml(entry), errorMessage))
        {
            return false;
        }

        HistoryEntry taken;
        taken.sequence = entries[index].sequence;
        taken.kind = "outside";
        taken.author = author;
        taken.label = label;
        taken.revisionBefore = scalarText(entry, "revision_before");
        taken.revisionAfter = scalarText(entry, "revision_after");

        for (const YAML::Node &change : childOf(entry, "changes"))
        {
            taken.changes.push_back(change.Scalar());
        }

        for (const YAML::Node &line : childOf(entry, "notice"))
        {
            taken.notice.push_back(line.Scalar());
        }

        result.taken.push_back(taken);
    }

    return true;
}

std::vector<std::string> lockDifferences(const std::string &before, const std::string &after)
{
    const auto tables = [](const std::string &text)
    {
        std::map<std::string, std::map<std::string, std::string>> found;

        try
        {
            const YAML::Node document = text.empty() ? YAML::Node() : YAML::Load(text);

            if (document.IsMap())
            {
                for (YAML::const_iterator table = document.begin(); table != document.end(); ++table)
                {
                    if (!table->second.IsMap())
                    {
                        continue;
                    }

                    // A copy of the node: `table->second` lives in a temporary the loop would outlive.
                    const YAML::Node entries = table->second;

                    for (YAML::const_iterator entry = entries.begin(); entry != entries.end(); ++entry)
                    {
                        found[table->first.Scalar()][entry->first.Scalar()] = entry->second.Scalar();
                    }
                }
            }
        }
        catch (const YAML::Exception &)
        {
        }

        return found;
    };
    const std::map<std::string, std::map<std::string, std::string>> first = tables(before);
    const std::map<std::string, std::map<std::string, std::string>> second = tables(after);
    std::set<std::string> names;

    for (const auto &table : first)
    {
        names.insert(table.first);
    }

    for (const auto &table : second)
    {
        names.insert(table.first);
    }

    std::vector<std::string> lines;
    const std::map<std::string, std::string> none;

    for (const std::string &name : names)
    {
        const std::map<std::string, std::string> &was = first.contains(name) ? first.at(name) : none;
        const std::map<std::string, std::string> &now = second.contains(name) ? second.at(name) : none;

        for (const std::pair<const std::string, std::string> &entry : now)
        {
            const std::map<std::string, std::string>::const_iterator old = was.find(entry.first);

            if (old == was.end())
            {
                lines.push_back(name + ": " + entry.first + " " + entry.second + " added");
            }
            else if (old->second != entry.second)
            {
                lines.push_back(name + ": " + entry.first + " " + old->second + " -> " + entry.second);
            }
        }

        for (const std::pair<const std::string, std::string> &entry : was)
        {
            if (!now.contains(entry.first))
            {
                lines.push_back(name + ": " + entry.first + " " + entry.second + " dropped");
            }
        }
    }

    return lines;
}


bool writeLockRecord(
    const std::filesystem::path &projectRoot,
    const std::string &lockText,
    const std::string &sourceRevision,
    const std::string &by,
    bool &changed,
    std::string &errorMessage)
{
    changed = false;
    // A writer holds the lock for milliseconds: a build waits for it rather than fail.
    ProjectWriteLock lock(projectRoot, 5000);

    if (!lock.held())
    {
        errorMessage = ProjectLockedMessage;
        return false;
    }

    return writeLockRecordHeld(projectRoot, lockText, sourceRevision, by, changed, errorMessage);
}

bool writeLockRecordHeld(
    const std::filesystem::path &projectRoot,
    const std::string &lockText,
    const std::string &sourceRevision,
    const std::string &by,
    bool &changed,
    std::string &errorMessage)
{
    changed = false;
    std::string current;
    const bool hadLock = readTextFile(projectRoot / "ids.lock.yml", current);

    if (hadLock && current == lockText)
    {
        return true;
    }

    if (!writeTextFileAtomically(projectRoot / "ids.lock.yml", lockText, errorMessage))
    {
        return false;
    }

    changed = true;
    JsonWriter line;
    line.beginObject();
    line.field("source_revision", sourceRevision);
    line.field("by", by);
    line.field("lock_before", lockHashOfText(hadLock ? &current : nullptr));
    line.field("lock_after", lockHashOfText(&lockText));
    line.key("changes");
    line.beginArray();

    for (const std::string &difference : lockDifferences(hadLock ? current : std::string(), lockText))
    {
        line.value(difference);
    }

    line.endArray();
    line.endObject();
    return appendLogLine(projectRoot, "lock.log", line.take(), errorMessage)
        && writeTextFileAtomically(stateRoot(projectRoot) / "lock_seen", lockHashOfText(&lockText) + "\n",
            errorMessage);
}

std::vector<std::string> renameLockEntries(YAML::Node &lockDocument,
    const std::vector<std::pair<std::string, std::string>> &renames)
{
    std::vector<std::string> moved;

    if (!lockDocument.IsMap())
    {
        return moved;
    }

    // A lock name is an id or built from one with dots (`door:x.leaf2`, `once.evt:x`); ids hold no dots.
    const auto renamed = [&renames](const std::string &name)
    {
        std::vector<std::string> parts;
        size_t begin = 0;

        while (true)
        {
            const size_t dot = name.find('.', begin);
            parts.push_back(name.substr(begin, dot == std::string::npos ? dot : dot - begin));

            if (dot == std::string::npos)
            {
                break;
            }

            begin = dot + 1;
        }

        for (const std::pair<std::string, std::string> &rename : renames)
        {
            for (std::string &part : parts)
            {
                if (part == rename.first)
                {
                    part = rename.second;
                }
            }
        }

        std::string joined;

        for (const std::string &part : parts)
        {
            joined += (joined.empty() ? "" : ".") + part;
        }

        return joined;
    };

    std::vector<std::pair<std::string, YAML::Node>> replaced;

    for (YAML::const_iterator table = lockDocument.begin(); table != lockDocument.end(); ++table)
    {
        // A copy of the node: `table->second` lives in a temporary the loop would outlive.
        const YAML::Node entries = table->second;

        if (!entries.IsMap())
        {
            continue;
        }

        YAML::Node rebuilt(YAML::NodeType::Map);
        bool changed = false;

        for (YAML::const_iterator entry = entries.begin(); entry != entries.end(); ++entry)
        {
            const std::string name = renamed(entry->first.Scalar());

            if (name != entry->first.Scalar())
            {
                changed = true;
                moved.push_back(table->first.Scalar() + ": " + entry->first.Scalar() + " -> " + name + " "
                    + entry->second.Scalar());
            }

            rebuilt[name] = entry->second;
        }

        if (changed)
        {
            replaced.emplace_back(table->first.Scalar(), rebuilt);
        }
    }

    for (const std::pair<std::string, YAML::Node> &table : replaced)
    {
        lockDocument[table.first] = table.second;
    }

    return moved;
}

bool pruneProjectLock(
    const std::filesystem::path &projectRoot,
    bool dryRun,
    LockPruneResult &result,
    std::string &errorMessage)
{
    result = {};
    Project project;
    std::vector<ProjectIssue> issues;

    if (!loadProject(projectRoot, project, issues))
    {
        errorMessage = issues.empty() ? "not a project" : issues.front().message;
        return false;
    }

    result.lockHashBefore = projectLockHash(projectRoot);
    result.lockHashAfter = result.lockHashBefore;

    if (!project.has("ids.lock.yml"))
    {
        result.note = "the project has no ids.lock.yml";
        return true;
    }

    if (project.has("sketch.yml"))
    {
        result.note = "an outdoor project keeps every entry of its lock: there is no rule of what is live outdoors yet";
        return true;
    }

    if (project.document("project.yml")["base"].IsDefined())
    {
        result.note = "an overlay project keeps every entry: its lock holds the base map's own numbers";
        return true;
    }

    IdsLock lock = IdsLock::fromDocument(project.document("ids.lock.yml"));
    result.dropped = retiredLockEntries(project, lock, true);

    if (result.dropped.empty() || dryRun)
    {
        return true;
    }

    const std::string lockText = writeCanonicalYaml(lock.toDocument(), SchemaSet::builtIn(), "ids_lock.schema.json");
    bool changed = false;

    if (!writeLockRecord(projectRoot, lockText, projectRevision(project), "prune", changed, errorMessage))
    {
        return false;
    }

    result.lockHashAfter = lockHashOfText(&lockText);
    return true;
}
}
