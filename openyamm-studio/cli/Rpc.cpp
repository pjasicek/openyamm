#include "cli/Rpc.h"

#include "cli/Commands.h"
#include "core/Authoring.h"
#include "core/CanonicalYaml.h"
#include "core/CoreMath.h"
#include "core/EventFlow.h"
#include "core/History.h"
#include "core/IndoorBuild.h"
#include "core/Json.h"
#include "core/Keys.h"
#include "core/MapLoad.h"
#include "core/Mods.h"
#include "core/Ops.h"
#include "core/OutdoorBuild.h"
#include "core/Pins.h"
#include "core/Project.h"
#include "core/View.h"
#include "core/Preview.h"
#include "core/SceneOverlay.h"
#include "core/Schema.h"
#include "core/Service.h"
#include "core/Walk.h"
#include "core/World.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iterator>
#include <map>
#include <memory>
#include <sstream>
#include <stdexcept>

namespace OpenYAMM::Studio
{
namespace
{
const char *const CoreVersion = "0.1.0";

// A method that did not do what was asked: a typed error (common.rpc.json, $defs/errors). `data` writes the error's
// fields after its kind.
struct RpcRefusal
{
    int code = -32000;
    std::string kind;
    std::string message;
    std::function<void(JsonWriter &)> data;
};

RpcRefusal refusal(const std::string &kind, const std::string &message,
    std::function<void(JsonWriter &)> data = nullptr, int code = -32000)
{
    return RpcRefusal{code, kind, message, std::move(data)};
}

// The project schemas and the catalogue in one set, so the catalogue's references into the project format resolve.
const SchemaSet &rpcSchemas()
{
    static const SchemaSet schemas = []()
    {
        SchemaSet set;
        std::string errorMessage;

        for (size_t index = 0; index < EmbeddedSchemaCount; ++index)
        {
            set.add(EmbeddedSchemas[index].pFileName, EmbeddedSchemas[index].pText, errorMessage);
        }

        for (size_t index = 0; index < EmbeddedRpcSchemaCount; ++index)
        {
            if (!set.add(EmbeddedRpcSchemas[index].pFileName, EmbeddedRpcSchemas[index].pText, errorMessage))
            {
                throw std::runtime_error(errorMessage);
            }
        }

        return set;
    }();
    return schemas;
}

struct MethodEntry
{
    // "edit.rpc.json#/methods/apply".
    std::string reference;
    std::string assets;
};

// The catalogue: every method of every *.rpc.json with an x-group, by full name.
const std::map<std::string, MethodEntry> &catalogue()
{
    static const std::map<std::string, MethodEntry> methods = []()
    {
        std::map<std::string, MethodEntry> table;
        const SchemaSet &schemas = rpcSchemas();

        for (size_t index = 0; index < EmbeddedRpcSchemaCount; ++index)
        {
            const std::string fileName = EmbeddedRpcSchemas[index].pFileName;
            const YAML::Node root = schemas.root(fileName);

            if (!root["x-group"] || !root["methods"])
            {
                continue;
            }

            for (YAML::const_iterator method = root["methods"].begin(); method != root["methods"].end(); ++method)
            {
                // Host methods (game.playtest) are answered by the host: this core neither lists nor serves them.
                if (method->second["lane"] && method->second["lane"].Scalar() == "host")
                {
                    continue;
                }

                MethodEntry entry;
                entry.reference = fileName + "#/methods/" + method->first.Scalar();
                entry.assets = method->second["assets"] ? method->second["assets"].Scalar() : "none";
                table[root["x-group"].Scalar() + "." + method->first.Scalar()] = entry;
            }
        }

        return table;
    }();
    return methods;
}

// The session: its asset root and what it keeps of projects between calls (core/Service.h). One per process (`oymap
// serve`, `oymap call`) and one per WebAssembly instance.
struct Session
{
    std::filesystem::path assetRoot;
    // The folder builds are installed into and read from (`built`); empty: none.
    std::filesystem::path mount;
    StudioService service;
    // Walk mode's one walk (walk.*).
    WalkSession walk;
};

Session &session()
{
    static Session instance;
    return instance;
}

// --- writing ------------------------------------------------------------------------------------------------------

// Each issue carries the severity its check gave it where it was found (S5_BROWSER_EDITOR.md 2.4.2).
// One issue; with `pProject`, the fixes the core offers for it (core/Authoring.h) as operations.
void writeIssue(JsonWriter &writer, const ProjectIssue &issue, const Project *pProject = nullptr)
{
    writer.beginObject();
    writer.field("severity", severityName(issue.severity));
    writer.field("code", issue.code.empty() ? std::string("project") : issue.code);
    writer.field("file", issue.file);
    writer.field("path", issue.path);
    writer.field("message", issue.message);

    if (pProject != nullptr)
    {
        const std::vector<IssueFix> fixes = issueFixes(*pProject, issue);

        if (!fixes.empty())
        {
            writer.key("fixes");
            writer.beginArray();

            for (const IssueFix &fix : fixes)
            {
                writer.beginObject();
                writer.field("label", fix.label);
                writer.key("ops");
                writer.node(fix.ops);
                writer.endObject();
            }

            writer.endArray();
        }
    }

    writer.endObject();
}

void writeIssues(JsonWriter &writer, const std::string &name, const std::vector<ProjectIssue> &issues,
    const Project *pProject = nullptr)
{
    writer.key(name);
    writer.beginArray();

    for (const ProjectIssue &issue : issues)
    {
        writeIssue(writer, issue, pProject);
    }

    writer.endArray();
}

void writeStrings(JsonWriter &writer, const std::string &name, const std::vector<std::string> &values)
{
    writer.key(name);
    writer.beginArray();

    for (const std::string &value : values)
    {
        writer.value(value);
    }

    writer.endArray();
}

// A number rounded to the decimals its result schema states (x-decimals), so native and wasm agree to the digit.
double rounded(double value, int decimals)
{
    const double scale = std::pow(10.0, decimals);
    const double result = std::round(value * scale) / scale;
    return result == 0.0 ? 0.0 : result;
}

void writePoint(JsonWriter &writer, const std::string &name, const std::array<double, 3> &point)
{
    writer.key(name);
    writer.beginArray();

    for (const double value : point)
    {
        writer.value(static_cast<int64_t>(std::llround(value)));
    }

    writer.endArray();
}

// --- reading the params -------------------------------------------------------------------------------------------

std::filesystem::path projectOf(const YAML::Node &params)
{
    return std::filesystem::path(params["project"].Scalar());
}

bool flag(const YAML::Node &params, const char *pName, bool fallback)
{
    return params[pName] ? params[pName].Scalar() == "true" : fallback;
}

// The kept project (core/Service.h), brought up to the files, or the not_a_project refusal.
StudioService::Entry &keptOrRefuse(const std::filesystem::path &root)
{
    std::vector<ProjectIssue> issues;
    StudioService::Entry *pEntry = session().service.project(root, issues);

    if (pEntry == nullptr)
    {
        throw refusal("not_a_project", issues.empty() ? "not a project" : issues.front().message,
            [issues](JsonWriter &writer) { writeIssues(writer, "issues", issues); });
    }

    return *pEntry;
}

// Reads a project or refuses with not_a_project.
void loadOrRefuse(const std::filesystem::path &root, Project &project, std::vector<ProjectIssue> &issues)
{
    if (!loadProject(root, project, issues))
    {
        const std::vector<ProjectIssue> found = issues;
        throw refusal("not_a_project", issues.empty() ? "not a project" : issues.front().message,
            [found](JsonWriter &writer) { writeIssues(writer, "issues", found); });
    }
}

// --- session ------------------------------------------------------------------------------------------------------

void sessionHello(const YAML::Node &, JsonWriter &writer)
{
    writer.field("core_version", CoreVersion);
    const YAML::Node common = rpcSchemas().root("common.rpc.json");
    writer.field("rpc_version", common["x-rpc-version"].as<int>());
#ifdef __EMSCRIPTEN__
    writer.field("backend", "wasm");
#else
    writer.field("backend", "native");
#endif
    writer.field("asset_root", !session().assetRoot.empty());
    writer.key("formats");
    writer.beginObject();

    for (const ProjectFileKind &kind : projectFileKinds())
    {
        const YAML::Node schema = SchemaSet::builtIn().root(kind.pSchema);
        const YAML::Node format = schema["properties"]["format"]["const"];
        writer.field(kind.pName, format ? format.as<int>() : 0);
    }

    writer.endObject();
    writeStrings(writer, "methods", rpcMethodNames());
}

void sessionConfigure(const YAML::Node &params, JsonWriter &writer)
{
    session().mount = params["mount"] ? std::filesystem::path(params["mount"].Scalar()) : std::filesystem::path();

    if (!params["asset_root"])
    {
        session().assetRoot.clear();
        session().service.setAssetRoot({});
        writer.field("asset_root", false);
        writer.field("mount", !session().mount.empty());
        return;
    }

    const std::filesystem::path root = params["asset_root"].Scalar();
    std::error_code error;

    if (!std::filesystem::is_directory(root / "engine", error))
    {
        throw refusal("no_asset_root", "not an asset root (no engine/ folder): " + root.string());
    }

    session().assetRoot = root;
    session().service.setAssetRoot(root);
    writer.field("asset_root", true);
    writer.field("mount", !session().mount.empty());
}

// What the core keeps of a project, dropped (the hosted worker's one map at a time).
void sessionRelease(const YAML::Node &params, JsonWriter &writer)
{
    writer.field("released", session().service.release(std::filesystem::path(params["project"].Scalar())));
}

// --- project ------------------------------------------------------------------------------------------------------

void writeFileTree(JsonWriter &writer, const std::string &name, const YAML::Node &document)
{
    if (!document.IsMap())
    {
        return;
    }

    writer.key(name);
    writer.beginObject();
    writer.key("tree");
    writer.node(document);
    writer.endObject();
}

// The hand-edit mark as the request list gives it (edit.rpc.json hand_mark), when the project has one.
void writeHandMark(JsonWriter &writer, const HandMark &mark)
{
    if (!mark.marked)
    {
        return;
    }

    writer.key("hand_edited");
    writer.beginObject();
    writer.field("since", mark.since);
    writer.field("revision", mark.revision);

    if (mark.setNow)
    {
        writer.field("set_now", true);
    }

    if (!mark.historyKnown)
    {
        writer.field("history_known_from", mark.knownFrom.empty() ? std::string("never") : mark.knownFrom);
    }

    writer.field("message", std::string(HandEditedMessage) + (mark.historyKnown ? std::string()
        : "; the history kept here does not reach back to the mark: objects changed by hand before "
            + (mark.knownFrom.empty() ? std::string("now") : mark.knownFrom) + " are not known"));
    writer.endObject();
}

void projectOpen(const YAML::Node &params, JsonWriter &writer)
{
    StudioService::Entry &entry = keptOrRefuse(projectOf(params));
    const Project &project = entry.memory.project;
    const std::vector<ProjectIssue> issues = session().service.readingIssues(entry);
    writer.field("revision", entry.memory.revision);
    writer.field("lock_hash", entry.memory.lockHash);
    writer.key("files");
    writer.beginObject();

    // Each file's tree is kept as JSON while its bytes stay the same.
    for (const ProjectFileKind &kind : projectFileKinds())
    {
        if (project.has(kind.pName) && project.document(kind.pName).IsMap())
        {
            writer.key(kind.pName);
            writer.beginObject();
            writer.key("tree");
            writer.raw(session().service.treeJson(entry, kind.pName));
            writer.endObject();
        }
    }

    writer.endObject();
    writer.key("ids");
    writer.beginArray();

    for (const ProjectFileKind &kind : projectFileKinds())
    {
        const YAML::Node root = project.document(kind.pName);

        // The lock's tables are maps from ids to numbers, not lists of objects.
        if (!root.IsDefined() || !root.IsMap())
        {
            continue;
        }

        for (YAML::const_iterator list = root.begin(); list != root.end(); ++list)
        {
            if (!list->second.IsSequence())
            {
                continue;
            }

            // A copy of the node: `list->second` lives in a temporary the loop would outlive.
            const YAML::Node items = list->second;

            for (const YAML::Node &item : items)
            {
                if (item.IsMap() && item["id"] && item["id"].IsScalar())
                {
                    writer.beginObject();
                    writer.field("id", item["id"].Scalar());
                    writer.field("file", kind.pName);
                    writer.field("list", list->first.Scalar());
                    writer.endObject();
                }
            }
        }
    }

    writer.endArray();
    writeIssues(writer, "issues", issues);
    writer.key("keys");
    writer.beginArray();

    for (const ProjectFileKind &kind : projectFileKinds())
    {
        if (!project.has(kind.pName) || !fileHasKeyedLists(kind.pSchema))
        {
            continue;
        }

        for (const std::string &address : subObjectAddresses(project.document(kind.pName), kind.pSchema))
        {
            writer.beginObject();
            writer.field("address", address);
            writer.field("file", kind.pName);
            writer.endObject();
        }
    }

    writer.endArray();
    writeHandMark(writer, handMarkOf(entry.root, project));
}

void projectRead(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path root = projectOf(params);
    StudioService::Entry &entry = keptOrRefuse(root);
    const Project &project = entry.memory.project;
    const std::string fileName = params["file"].Scalar();
    std::string text;
    const std::map<std::string, ProjectFile>::const_iterator file = project.files.find(fileName);

    // A file that parses is read from what is kept (the bytes on disk); one that does not, from the disk.
    if (file != project.files.end())
    {
        text = file->second.text;
    }
    else if (!readTextFile(root / fileName, text))
    {
        throw refusal("no_such_file", "the project has no " + fileName,
            [fileName](JsonWriter &data) { data.field("file", fileName); });
    }

    const std::vector<ProjectIssue> issues = session().service.readingIssues(entry);
    writer.field("revision", entry.memory.revision);
    writer.field("file", fileName);
    writer.field("text", text);
    const std::map<std::string, std::string>::const_iterator canonical = entry.memory.canonical.find(fileName);
    writer.field("canonical", file != project.files.end()
        && (canonical != entry.memory.canonical.end() ? canonical->second : canonicalText(file->second)) == text);

    if (file != project.files.end())
    {
        if (file->second.document.IsMap())
        {
            writer.key("tree");
            writer.node(file->second.document);
        }

        return;
    }

    for (const ProjectIssue &issue : issues)
    {
        if (issue.file == fileName)
        {
            writer.field("parse_error", issue.message);
            return;
        }
    }
}

void projectStatusMethod(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path root = projectOf(params);
    std::error_code error;

    if (!std::filesystem::is_regular_file(root / "project.yml", error))
    {
        Project project;
        std::vector<ProjectIssue> issues;
        loadOrRefuse(root, project, issues);
    }

    ProjectStatus status;
    std::string errorMessage;

    if (!projectStatus(root, status, errorMessage))
    {
        if (errorMessage.starts_with("another oymap process"))
        {
            throw refusal("locked", errorMessage);
        }

        throw refusal("failed", errorMessage, nullptr, -32603);
    }

    // The history head is now up to these files: the next edit need not bring it up again.
    std::vector<ProjectIssue> unused;
    std::map<std::string, ProjectIssue> unreadable;

    if (StudioService::Entry *pEntry = session().service.project(root, unused); pEntry != nullptr)
    {
        if (pEntry->memory.revision == status.revision)
        {
            pEntry->memory.headRevision = status.revision;
            pEntry->memory.headLockHash = pEntry->memory.lockHash;
        }

        unreadable = pEntry->loadIssues;
    }

    writer.field("revision", status.revision);
    writer.field("lock_hash", status.lockHash);
    writeStrings(writer, "outside_changes", status.outsideChanges);

    if (status.outsideSequence > 0)
    {
        writer.field("outside_sequence", status.outsideSequence);
    }

    if (!status.outsideNotice.empty())
    {
        writeStrings(writer, "outside_notice", status.outsideNotice);
    }

    writeHandMark(writer, status.mark);

    if (!unreadable.empty())
    {
        writer.key("unreadable");
        writer.beginArray();

        for (const std::pair<const std::string, ProjectIssue> &file : unreadable)
        {
            writer.beginObject();
            writer.field("file", file.first);
            writer.field("message", file.second.message);
            writer.endObject();
        }

        writer.endArray();
    }
}

void projectRecord(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path root = projectOf(params);
    {
        Project project;
        std::vector<ProjectIssue> issues;
        loadOrRefuse(root, project, issues);
    }

    RecordResult result;
    std::string errorMessage;

    if (!recordOutsideEdits(root, params["author"].Scalar(), params["label"] ? params["label"].Scalar() : "", result,
            errorMessage))
    {
        throw refusal(errorMessage.starts_with("another oymap process") ? "locked" : "failed", errorMessage, nullptr,
            errorMessage.starts_with("another oymap process") ? -32000 : -32603);
    }

    writer.field("revision", result.revision);
    writer.key("recorded");
    writer.beginArray();

    for (const HistoryEntry &entry : result.taken)
    {
        writer.beginObject();
        writer.field("sequence", entry.sequence);
        writeStrings(writer, "changes", entry.changes);
        writer.endObject();
    }

    writer.endArray();
}

void projectLockPrune(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path root = projectOf(params);
    {
        Project project;
        std::vector<ProjectIssue> issues;
        loadOrRefuse(root, project, issues);
    }

    LockPruneResult result;
    std::string errorMessage;

    if (!pruneProjectLock(root, flag(params, "dry_run", false), result, errorMessage))
    {
        throw refusal(errorMessage.starts_with("another oymap process") ? "locked" : "failed", errorMessage, nullptr,
            errorMessage.starts_with("another oymap process") ? -32000 : -32603);
    }

    writeStrings(writer, "dropped", result.dropped);
    writer.field("lock_hash_before", result.lockHashBefore);
    writer.field("lock_hash", result.lockHashAfter);

    if (!result.note.empty())
    {
        writer.field("note", result.note);
    }
}

// --- edit ---------------------------------------------------------------------------------------------------------

// The refusals of a transaction or a revert that was not applied.
[[noreturn]] void refuseTransaction(const std::filesystem::path &root, const TransactionResult &result)
{
    const std::string message = result.errors.empty() ? std::string("refused") : result.errors.front();

    switch (result.refusal)
    {
    case TransactionRefusal::NotAProject:
    {
        Project project;
        std::vector<ProjectIssue> issues;
        loadOrRefuse(root, project, issues);
        throw refusal("failed", message, nullptr, -32603);
    }

    case TransactionRefusal::Locked:
        throw refusal("locked", message);

    case TransactionRefusal::StaleRevision:
        // The refusal is written after this function has returned: capture copies.
        throw refusal("stale_revision", message,
            [revision = result.revisionBefore, since = result.outsideChanges, clashes = result.clashes](JsonWriter &data)
            {
                data.field("revision", revision);
                writeStrings(data, "since", since);

                if (!clashes.empty())
                {
                    writeStrings(data, "clashes", clashes);
                }
            });

    case TransactionRefusal::BadOperation:
    {
        // "operation 2: ..." without the place, which data names.
        const size_t colon = message.find(": ");
        const std::string reason = message.starts_with("operation ") && colon != std::string::npos
            ? message.substr(colon + 2) : message;
        throw refusal("bad_operation", message,
            [index = std::max(result.failedOperation, 0), step = result.failedStep, reason](JsonWriter &data)
            {
                data.field("index", index);

                if (step >= 0)
                {
                    data.field("step", step);
                }

                data.field("reason", reason);
            });
    }

    case TransactionRefusal::NewIssues:
        throw refusal("new_errors", message,
            [issues = result.newIssues, revision = result.revisionAfter](JsonWriter &data)
            {
                writeIssues(data, "new_issues", issues);
                data.field("revision_after", revision);
            });

    case TransactionRefusal::NothingToRevert:
        throw refusal("nothing_to_undo", message);

    case TransactionRefusal::None:
    case TransactionRefusal::Failed:
        break;
    }

    throw refusal("failed", message, nullptr, -32603);
}

// `pKept`: the kept project of a written edit, whose changed files' trees, parsed here from their texts, the
// read-back and the next project.open take instead of parsing and writing them again (S8f).
void writeChangedFiles(JsonWriter &writer, const TransactionResult &result, StudioService::Entry *pKept = nullptr)
{
    writer.key("files");
    writer.beginObject();

    // In the order of the project's files: the tree of each changed file as its canonical text reads.
    for (const ProjectFileKind &kind : projectFileKinds())
    {
        const std::map<std::string, std::string>::const_iterator text = result.filesAfter.find(kind.pName);

        if (text == result.filesAfter.end())
        {
            continue;
        }

        const YAML::Node document = YAML::Load(text->second);

        if (pKept == nullptr || !document.IsMap())
        {
            writeFileTree(writer, kind.pName, document);
            continue;
        }

        JsonWriter tree;
        tree.node(document);
        const std::string json = tree.take();
        writer.key(kind.pName);
        writer.beginObject();
        writer.key("tree");
        writer.raw(json);
        writer.endObject();
        session().service.keepReadBack(*pKept, kind.pName, text->second, document, json);
    }

    writer.endObject();
}

void editApply(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path root = projectOf(params);
    TransactionOptions options;
    options.dryRun = flag(params, "dry_run", false);
    options.allowNewIssues = flag(params, "allow_errors", false);
    options.assetRoot = session().assetRoot;
    options.expectRevision = params["expect_revision"] ? params["expect_revision"].Scalar() : std::string();
    options.author = params["author"] ? params["author"].Scalar() : std::string("agent");
    options.label = params["label"] ? params["label"].Scalar() : std::string();
    options.mergeKey = params["merge_key"] ? params["merge_key"].Scalar() : std::string();
    options.rebase = flag(params, "rebase", false);
    TransactionResult result;
    bool applied = false;
    StudioService::Entry *pKept = nullptr;

    {
        // The kept project is brought up to the files under the project's write lock, so no writer comes between
        // reading and writing (S5_BROWSER_EDITOR.md 2.4.3).
        ProjectWriteLock lock(root);
        std::vector<ProjectIssue> issues;
        StudioService::Entry *pEntry = lock.held() ? session().service.project(root, issues) : nullptr;

        if (!lock.held())
        {
            result.refusal = TransactionRefusal::Locked;
            result.errors.push_back(ProjectLockedMessage);
        }
        else if (pEntry == nullptr)
        {
            result.refusal = TransactionRefusal::NotAProject;
            result.errors.push_back(issues.empty() ? std::string("not a project") : issues.front().message);
        }
        else if (pEntry->loadIssues.empty())
        {
            applied = session().service.applyTransaction(*pEntry, params["ops"], options, result);
            pKept = applied && result.applied ? pEntry : nullptr;
        }
    }

    // A file that does not parse: the transaction as it always was, from the files (it takes the lock itself).
    if (result.refusal == TransactionRefusal::None && !applied && result.errors.empty())
    {
        applied = applyTransaction(root, params["ops"], options, result);
    }

    if (!applied)
    {
        refuseTransaction(root, result);
    }

    writer.field("applied", result.applied);
    writer.field("revision_before", result.revisionBefore);
    writer.field("revision_after", result.revisionAfter);
    writeStrings(writer, "changes", result.changes);
    writeStrings(writer, "outside_changes", result.outsideChanges);
    writeIssues(writer, "new_issues", result.newIssues);
    writeIssues(writer, "fixed_issues", result.fixedIssues);
    writeChangedFiles(writer, result, pKept);

    if (!result.idsAllocated.empty())
    {
        writeStrings(writer, "ids_allocated", result.idsAllocated);
    }

    if (!result.keysAllocated.empty())
    {
        writeStrings(writer, "keys_allocated", result.keysAllocated);
    }

    if (!result.notes.empty())
    {
        writeStrings(writer, "notes", result.notes);
    }

    if (result.sequence > 0)
    {
        writer.field("sequence", result.sequence);
    }

    if (result.merged)
    {
        writer.field("merged", true);
    }

    if (!result.rebasedOver.empty())
    {
        writer.key("rebased_over");
        writer.beginArray();

        for (const int sequence : result.rebasedOver)
        {
            writer.value(sequence);
        }

        writer.endArray();
    }

    writeHandMark(writer, result.mark);

    if (!result.handObjects.empty())
    {
        writeStrings(writer, "hand_objects", result.handObjects);
    }

    if (result.outsideSequence > 0)
    {
        writer.field("outside_sequence", result.outsideSequence);
    }

    if (!result.outsideNotice.empty())
    {
        writeStrings(writer, "outside_notice", result.outsideNotice);
    }
}

void editHistory(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path root = projectOf(params);
    {
        Project project;
        std::vector<ProjectIssue> issues;
        loadOrRefuse(root, project, issues);
    }

    ProjectStatus status;
    std::string errorMessage;

    if (!projectStatus(root, status, errorMessage))
    {
        throw refusal(errorMessage.starts_with("another oymap process") ? "locked" : "failed", errorMessage, nullptr,
            errorMessage.starts_with("another oymap process") ? -32000 : -32603);
    }

    const size_t limit = params["limit"] ? params["limit"].as<size_t>() : 50;
    const size_t first = status.history.size() > limit ? status.history.size() - limit : 0;
    writer.field("revision", status.revision);
    writer.field("count", static_cast<uint64_t>(status.history.size()));
    writer.key("entries");
    writer.beginArray();

    for (size_t index = first; index < status.history.size(); ++index)
    {
        const HistoryEntry &entry = status.history[index];
        writer.beginObject();
        writer.field("sequence", entry.sequence);
        writer.field("kind", entry.kind);
        writer.field("author", entry.author);

        if (!entry.label.empty())
        {
            writer.field("label", entry.label);
        }

        if (!entry.time.empty())
        {
            writer.field("time", entry.time);
        }

        writer.field("revision_before", entry.revisionBefore);
        writer.field("revision_after", entry.revisionAfter);
        writeStrings(writer, "changes", entry.changes);
        writer.field("undone", entry.undone);

        if (entry.reverts > 0)
        {
            writer.field("reverts", entry.reverts);
            writer.field("revert_kind", entry.revertKind.empty() ? std::string("revert") : entry.revertKind);
        }

        if (entry.merged > 1)
        {
            writer.field("merged", entry.merged);
        }

        if (!entry.objects.empty())
        {
            writeStrings(writer, "objects", entry.objects);
        }

        if (!entry.notice.empty())
        {
            writeStrings(writer, "notice", entry.notice);
        }

        writer.endObject();
    }

    writer.endArray();
}

// --- check --------------------------------------------------------------------------------------------------------

void checkValidate(const YAML::Node &params, JsonWriter &writer)
{
    StudioService::Entry &entry = keptOrRefuse(projectOf(params));
    const bool withAssets = flag(params, "use_assets", true) && !session().assetRoot.empty();
    // Kept until a file changes; with an asset root an outdoor project is also checked for what the build looks up
    // there (one dry build). Only errors stop a build.
    const std::vector<ProjectIssue> &issues = session().service.validate(entry, withAssets);
    writer.field("ok", !hasErrors(issues));
    writer.field("with_assets", withAssets);
    writeIssues(writer, "issues", issues, &entry.memory.project);
    std::vector<std::string> notes;
    const std::string note =
        missingWorldNote(entry.memory.project, withAssets ? session().assetRoot : std::filesystem::path());

    if (!note.empty())
    {
        notes.push_back(note);
    }

    writeStrings(writer, "notes", notes);
}

void checkThings(const YAML::Node &params, JsonWriter &writer)
{
    if (session().assetRoot.empty())
    {
        throw refusal("no_asset_root", "check.things reads the built map through an asset root: the session has none");
    }

    ThingsReport report;
    TargetFailure failure = TargetFailure::None;
    std::vector<ProjectIssue> buildIssues;
    std::string errorMessage;

    if (!collectThings(projectOf(params), session().assetRoot, report, failure, buildIssues, errorMessage))
    {
        switch (failure)
        {
        case TargetFailure::NotAProject:
        {
            Project project;
            std::vector<ProjectIssue> issues;
            loadOrRefuse(projectOf(params), project, issues);
            break;
        }

        case TargetFailure::DoesNotBuild:
            throw refusal("has_errors", errorMessage,
                [buildIssues](JsonWriter &data) { writeIssues(data, "issues", buildIssues); });

        case TargetFailure::NoAssetRoot:
            throw refusal("no_asset_root", errorMessage);

        case TargetFailure::None:
        case TargetFailure::Failed:
            break;
        }

        throw refusal("failed", errorMessage, nullptr, -32603);
    }

    writer.field("map", report.map);
    writer.field("world", report.world);
    writer.key("things");
    writer.beginArray();

    for (const InteractiveThing &thing : report.things)
    {
        writer.beginObject();
        writer.field("event", thing.eventId);

        if (const auto name = report.names.events.find(thing.eventId); name != report.names.events.end())
        {
            writer.field("id", name->second);
        }

        writer.field("title", thing.title);
        writer.field("kind", thing.kind);
        writer.field("sector", thing.sector);

        if (const auto room = report.names.sectors.find(thing.sector); room != report.names.sectors.end())
        {
            writer.field("room", room->second);
        }

        writer.key("textures");
        writer.beginObject();

        for (const std::pair<const std::string, int> &texture : thing.textures)
        {
            writer.field(texture.first, texture.second);
        }

        writer.endObject();

        for (const std::pair<const char *, const std::vector<uint32_t> *> &list :
             {std::pair<const char *, const std::vector<uint32_t> *>{"faces", &thing.faces},
                 {"own_doors", &thing.ownDoors}})
        {
            writer.key(list.first);
            writer.beginArray();

            for (const uint32_t number : *list.second)
            {
                writer.value(static_cast<uint64_t>(number));
            }

            writer.endArray();
        }

        writePoint(writer, "low", thing.low);
        writePoint(writer, "high", thing.high);
        writePoint(writer, "middle", thing.middle);
        writePoint(writer, "stand", thing.stand);
        writer.field("yaw", rounded(thing.yaw, 4));
        writer.field("pitch", rounded(thing.pitch, 4));
        writer.field("safe_to_use", thing.safeToUse);
        writeStrings(writer, "effects", thing.effects);
        writeStrings(writer, "changes", thing.changes);
        writeStrings(writer, "overlaps", thing.overlaps);
        writer.endObject();
    }

    writer.endArray();
}

// --- build --------------------------------------------------------------------------------------------------------

void buildRun(const YAML::Node &params, JsonWriter &writer)
{
    // A build reads the files again (what it compiles is what is on disk) with the session's kept tables.
    Project project;
    BuildResult result;
    BuildOptions options = session().service.buildOptions(true);
    options.dryRun = flag(params, "dry_run", true);
    loadOrRefuse(projectOf(params), project, result.issues);
    // The land kept by the project's lowerings (an outdoor build gives the same bytes with it as without).
    std::vector<ProjectIssue> unused;
    StudioService::Entry *pEntry = session().service.project(project.root, unused);
    options.pLand = pEntry != nullptr ? pEntry->land.get() : nullptr;

    if (!result.issues.empty() || !buildProject(project, options, result))
    {
        if (result.issues.empty())
        {
            throw refusal("failed", "the build failed", nullptr, -32603);
        }

        const std::vector<ProjectIssue> issues = result.issues;
        size_t errors = 0;

        for (const ProjectIssue &issue : issues)
        {
            errors += issue.isError() ? 1 : 0;
        }

        throw refusal("has_errors", "the project has " + std::to_string(errors) + " error(s) and does not build",
            [issues](JsonWriter &data) { writeIssues(data, "issues", issues); });
    }

    const bool outdoor = result.mapFile.ends_with(".odm");
    writer.field("map", result.mapFile);
    writer.field("kind", result.overlay ? "overlay" : outdoor ? "outdoor" : "indoor");
    writer.key("counts");
    writer.beginObject();

    if (result.overlay)
    {
        writer.field("replaced_events", static_cast<uint64_t>(result.events));
    }
    else if (outdoor)
    {
        writer.field("buildings", static_cast<uint64_t>(result.doors));
        writer.field("faces", static_cast<uint64_t>(result.faces));
        writer.field("vertices", static_cast<uint64_t>(result.vertices));
        writer.field("events", static_cast<uint64_t>(result.events));
        writer.field("entities", static_cast<uint64_t>(result.entities));
        writer.field("spawns", static_cast<uint64_t>(result.spawns));
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
    writeStrings(writer, "files", options.dryRun ? std::vector<std::string>() : result.files);
    writeStrings(writer, "warnings", result.warnings);
    writer.field("ids_lock_changed", result.lockChanged);
}

// --- view ---------------------------------------------------------------------------------------------------------

// The view of the project's current state, or its last that lowered (stale), or the has_errors refusal.
std::shared_ptr<StudioService::View> viewOrRefuse(StudioService::Entry &entry)
{
    std::shared_ptr<StudioService::View> view = session().service.view(entry);

    if (!view)
    {
        const std::vector<ProjectIssue> issues = entry.issues;
        throw refusal("has_errors", "the project does not lower (it has errors) and no earlier view of it is kept",
            [issues](JsonWriter &data) { writeIssues(data, "issues", issues); });
    }

    return view;
}

void writeViewHead(JsonWriter &writer, const StudioService::Entry &entry, const StudioService::View &view)
{
    writer.field("revision", entry.memory.revision);
    writer.field("view_revision", view.revision);
    writer.field("stale", view.revision != entry.memory.revision || view.lockHash != entry.memory.lockHash);

    // A view build: objects the lowering could not lower, left out with what depends on them (2.4.2).
    if (!view.lowered.skipped.empty())
    {
        writeStrings(writer, "skipped", view.lowered.skipped);
        writeIssues(writer, "skipped_issues", view.lowered.skippedIssues);
    }
}

std::string worldOf(const Project &project)
{
    const YAML::Node card = project.document("project.yml");
    return card.IsMap() && card["world"] && card["world"].IsScalar() ? card["world"].Scalar() : std::string();
}

void viewLayout(const YAML::Node &params, JsonWriter &writer)
{
    StudioService::Entry &entry = keptOrRefuse(projectOf(params));
    const std::shared_ptr<StudioService::View> view = viewOrRefuse(entry);
    writeViewHead(writer, entry, *view);
    writer.field("kind", view->lowered.indoor ? "indoor" : "outdoor");
    writer.field("world", worldOf(entry.memory.project));
    writer.rawMembers(session().service.layout(*view));
}

// view.terrain_query (S5_BROWSER_EDITOR.md 3.18): the built land asked by place, as agents read land made by hand.
// From the view's map: the stored samples (steps of 32) at the nodes, weighed by distance between them.
void viewTerrainQuery(const YAML::Node &params, JsonWriter &writer)
{
    StudioService::Entry &entry = keptOrRefuse(projectOf(params));
    const std::shared_ptr<StudioService::View> view = viewOrRefuse(entry);

    if (!view->lowered.outdoor)
    {
        throw refusal("bad_request", "view.terrain_query asks an outdoor project's land: this project is indoor");
    }

    const std::vector<uint8_t> &samples = view->lowered.outdoor->map.heightMap;
    const int side = 128;
    const auto heightAt = [&samples, side](double x, double y)
    {
        const double clampedX = std::clamp(x, 0.0, static_cast<double>(side - 1));
        const double clampedY = std::clamp(y, 0.0, static_cast<double>(side - 1));
        const int x0 = std::min(static_cast<int>(std::floor(clampedX)), side - 2);
        const int y0 = std::min(static_cast<int>(std::floor(clampedY)), side - 2);
        const double shareX = clampedX - x0;
        const double shareY = clampedY - y0;
        const auto at = [&samples, side](int nodeX, int nodeY)
        {
            return samples.size() == static_cast<size_t>(side) * side
                ? samples[static_cast<size_t>(nodeY) * side + nodeX] * 32.0 : 0.0;
        };
        const double north = at(x0, y0) * (1.0 - shareX) + at(x0 + 1, y0) * shareX;
        const double south = at(x0, y0 + 1) * (1.0 - shareX) + at(x0 + 1, y0 + 1) * shareX;
        return north * (1.0 - shareY) + south * shareY;
    };
    const auto pointOf = [](const YAML::Node &node, double &x, double &y)
    {
        if (!node.IsSequence() || node.size() != 2)
        {
            throw refusal("bad_request", "a place is [x, y] in cells");
        }

        x = node[0].as<double>();
        y = node[1].as<double>();
    };
    writeViewHead(writer, entry, *view);
    writer.key("points");
    writer.beginArray();

    for (size_t index = 0; params["points"] && index < params["points"].size(); ++index)
    {
        double x = 0.0;
        double y = 0.0;
        pointOf(params["points"][index], x, y);
        const double dx = (heightAt(x + 0.5, y) - heightAt(x - 0.5, y)) / 512.0;
        const double dy = (heightAt(x, y + 0.5) - heightAt(x, y - 0.5)) / 512.0;
        writer.beginObject();
        writer.key("at");
        writer.beginArray();
        writer.value(rounded(x, 3));
        writer.value(rounded(y, 3));
        writer.endArray();
        writer.field("height", static_cast<int64_t>(std::lround(heightAt(x, y))));
        writer.field("slope", rounded(oy::atan(std::sqrt(dx * dx + dy * dy)) * 180.0 / 3.14159265358979323846, 1));
        writer.endObject();
    }

    writer.endArray();

    if (params["line"])
    {
        double fromX = 0.0;
        double fromY = 0.0;
        double toX = 0.0;
        double toY = 0.0;
        pointOf(params["line"]["from"], fromX, fromY);
        pointOf(params["line"]["to"], toX, toY);
        const double step = params["line"]["step"] ? params["line"]["step"].as<double>() : 1.0;
        const double length = oy::hypot(toX - fromX, toY - fromY);
        const int count = std::max(1, static_cast<int>(std::ceil(length / step)));
        writer.key("profile");
        writer.beginArray();

        for (int index = 0; index <= count; ++index)
        {
            const double share = static_cast<double>(index) / count;
            const double x = fromX + (toX - fromX) * share;
            const double y = fromY + (toY - fromY) * share;
            writer.beginObject();
            writer.key("at");
            writer.beginArray();
            writer.value(rounded(x, 3));
            writer.value(rounded(y, 3));
            writer.endArray();
            writer.field("height", static_cast<int64_t>(std::lround(heightAt(x, y))));
            writer.endObject();
        }

        writer.endArray();
    }
}

// History's "show as it was" (S5_BROWSER_EDITOR.md 3.12): the layout of the project as it stood before (or after) a
// history entry, lowered from the files of then (core/Authoring.h), for the views to draw as a ghost over the current.
// Indoor projects; nothing is kept or written.
void viewLayoutAt(const YAML::Node &params, JsonWriter &writer)
{
    StudioService::Entry &entry = keptOrRefuse(projectOf(params));
    const int sequence = params["sequence"].as<int>();
    const bool before = !params["side"] || params["side"].Scalar() != "after";
    std::map<std::string, std::string> texts;
    std::string errorMessage;

    if (!sourceTextsAtEntry(entry.root, entry.memory.project, sequence, before, texts, errorMessage))
    {
        throw refusal("bad_request", errorMessage);
    }

    Project then;

    if (!projectFromTexts(entry.root, texts, then, errorMessage))
    {
        throw refusal("bad_request", errorMessage.empty() ? "the project had no project.yml then" : errorMessage);
    }

    ValidationParts parts;
    std::vector<ProjectIssue> issues;
    ValidationViews views;
    validateProjectParts(then, session().service.buildOptions(true), nullptr, nullptr, parts, issues, &views);

    // Outdoor projects too (S5b2): the land and the models as they were.
    if (!views.indoor && !views.outdoor)
    {
        throw refusal("has_errors", "the project did not lower " + std::string(before ? "before" : "after") + " entry "
            + std::to_string(sequence), [issues](JsonWriter &data) { writeIssues(data, "issues", issues); });
    }

    writer.field("sequence", static_cast<int64_t>(sequence));
    writer.field("side", before ? "before" : "after");
    writer.field("revision", projectRevision(then));
    writer.field("kind", views.indoor ? "indoor" : "outdoor");
    writer.field("world", worldOf(then));

    if (!views.skipped.empty())
    {
        writeStrings(writer, "skipped", views.skipped);
    }

    JsonWriter layout;
    layout.beginObject();

    if (views.indoor)
    {
        writeIndoorLayout(layout, *views.indoor);
    }
    else
    {
        writeOutdoorLayout(layout, *views.outdoor);
    }

    layout.endObject();
    const std::string text = layout.take();
    writer.rawMembers(text.size() >= 2 ? text.substr(1, text.size() - 2) : std::string());
}

void writeSection(JsonWriter &writer, const char *pName, const ViewMesh::Section &section)
{
    writer.key(pName);
    writer.beginObject();
    writer.field("offset", static_cast<uint64_t>(section.offset));
    writer.field("count", static_cast<uint64_t>(section.count));
    writer.endObject();
}

void writeMeshMembers(JsonWriter &writer, const ViewMesh &mesh);

void viewMesh(const YAML::Node &params, JsonWriter &writer)
{
    StudioService::Entry &entry = keptOrRefuse(projectOf(params));
    const std::shared_ptr<StudioService::View> view = viewOrRefuse(entry);
    std::string errorMessage;

    if (!session().service.makeMesh(entry, *view, errorMessage))
    {
        throw refusal("failed", errorMessage, nullptr, -32603);
    }

    writeViewHead(writer, entry, *view);
    writer.field("lock_hash", view->lockHash);
    writer.field("kind", view->lowered.indoor ? "indoor" : "outdoor");
    writer.field("world", worldOf(entry.memory.project));
    writer.field("file", view->meshFile);
    writeMeshMembers(writer, view->mesh);
}

// A mesh's description after its file (view.mesh and view.original_mesh): bytes, counts, sections, groups, owners,
// bounds.
void writeMeshMembers(JsonWriter &writer, const ViewMesh &mesh)
{
    writer.field("bytes", static_cast<uint64_t>(mesh.bytes.size()));
    writer.key("counts");
    writer.beginObject();
    writer.field("vertices", static_cast<uint64_t>(mesh.vertices));
    writer.field("triangles", static_cast<uint64_t>(mesh.triangles));
    writer.field("faces", static_cast<uint64_t>(mesh.faces));
    writer.endObject();
    writer.key("sections");
    writer.beginObject();
    writeSection(writer, "positions", mesh.positions);
    writeSection(writer, "normals", mesh.normals);
    writeSection(writer, "uvs", mesh.uvs);
    writeSection(writer, "indices", mesh.indices);
    writeSection(writer, "triangle_faces", mesh.triangleFaces);
    writeSection(writer, "face_owners", mesh.faceOwners);
    writer.endObject();
    writer.key("groups");
    writer.beginArray();

    for (const ViewMesh::Group &group : mesh.groups)
    {
        writer.beginObject();
        writer.field("texture", group.texture);
        writer.field("first", static_cast<uint64_t>(group.first));
        writer.field("count", static_cast<uint64_t>(group.count));
        writer.field("uv_unit", group.unitUv ? "unit" : "texel");
        writer.field("kind", group.kind);
        writer.endObject();
    }

    writer.endArray();
    writer.key("owners");
    writer.beginArray();

    for (const ViewMesh::Owner &owner : mesh.owners)
    {
        writer.beginObject();
        writer.field("id", owner.id);

        if (!owner.file.empty())
        {
            writer.field("file", owner.file);
        }

        writer.endObject();
    }

    writer.endArray();
    writer.key("bounds");
    writer.beginObject();
    writer.key("min");
    writer.beginArray();

    for (const int64_t value : mesh.min)
    {
        writer.value(value);
    }

    writer.endArray();
    writer.key("max");
    writer.beginArray();

    for (const int64_t value : mesh.max)
    {
        writer.value(value);
    }

    writer.endArray();
    writer.endObject();
}

// --- pins ---------------------------------------------------------------------------------------------------------

void pinsList(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path root = projectOf(params);
    {
        Project project;
        std::vector<ProjectIssue> issues;
        loadOrRefuse(root, project, issues);
    }

    YAML::Node document;
    std::string errorMessage;

    if (!readPinsDocument(root, document, errorMessage))
    {
        throw refusal("failed", errorMessage, nullptr, -32603);
    }

    writer.field("counter", document["counter"] ? document["counter"].as<int>() : 0);
    writer.key("pins");
    writer.beginArray();

    for (const YAML::Node &pin : pinsWithStatus(document, params["status"] ? params["status"].Scalar() : ""))
    {
        writer.node(pin);
    }

    writer.endArray();
}

// The shots of a screenshot tour at the pins' poses (`oymap pins tour`): the host writes the tour and runs it (its
// pins tour job), so the answer is the shots, never a folder.
void pinsTour(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path root = projectOf(params);
    {
        Project project;
        std::vector<ProjectIssue> issues;
        loadOrRefuse(root, project, issues);
    }

    YAML::Node document;
    std::string errorMessage;

    if (!readPinsDocument(root, document, errorMessage))
    {
        throw refusal("failed", errorMessage, nullptr, -32603);
    }

    std::vector<std::string> ids;
    std::vector<std::string> statuses;

    for (const YAML::Node &id : params["pins"])
    {
        ids.push_back(id.Scalar());
    }

    for (const YAML::Node &status : params["status"])
    {
        statuses.push_back(status.Scalar());
    }

    if (statuses.empty())
    {
        statuses = {"open", "claimed", "resolved"};
    }

    std::vector<std::string> skipped;
    const YAML::Node tour = YAML::Load(pinsTourText(document, ids, statuses, std::filesystem::path(), skipped));
    // The map the pins were made on (the first that names one).
    std::string map;
    std::string world;

    for (const YAML::Node &pin : document["pins"])
    {
        if (map.empty() && pin["map"] && pin["map"].IsScalar() && !pin["map"].Scalar().empty())
        {
            map = pin["map"].Scalar();
            world = pin["world"] && pin["world"].IsScalar() ? pin["world"].Scalar() : std::string();
        }
    }

    writer.field("map", map);
    writer.field("world", world);
    writer.key("shots");
    writer.beginArray();
    // The pins in the tour's order, by their picture's name.
    std::map<std::string, std::string> pinOfStem;

    for (const YAML::Node &pin : document["pins"])
    {
        if (pin["id"] && pin["id"].IsScalar())
        {
            // A shot is named as the pin's pictures are: pin:p7 -> p7.
            const std::string id = pin["id"].Scalar();
            const size_t colon = id.find(':');
            pinOfStem[colon == std::string::npos ? id : id.substr(colon + 1)] = id;
        }
    }

    for (const YAML::Node &shot : tour["shots"])
    {
        writer.beginObject();
        const std::string name = shot["name"].Scalar();
        writer.field("pin", pinOfStem.contains(name) ? pinOfStem[name] : name);
        writer.field("name", name);
        writer.key("position");
        writer.beginArray();

        for (size_t axis = 0; axis < 3; ++axis)
        {
            writer.value(std::round(shot["position"][axis].as<double>() * 1000.0) / 1000.0);
        }

        writer.endArray();
        writer.field("yaw_radians", std::round(shot["yaw"].as<double>() * 10000.0) / 10000.0);
        writer.field("pitch_radians", std::round(shot["pitch"].as<double>() * 1000000.0) / 1000000.0);
        writer.endObject();
    }

    writer.endArray();
    writeStrings(writer, "skipped", skipped);
}

// A pins method's answer: the pin as written and the counter, or the typed refusal.
void pinAnswer(bool ok, const PinResult &result, const std::filesystem::path &root, JsonWriter &writer)
{
    if (!ok)
    {
        switch (result.refusal)
        {
        case PinRefusal::NotAProject:
        {
            Project project;
            std::vector<ProjectIssue> issues;
            loadOrRefuse(root, project, issues);
            break;
        }

        case PinRefusal::Locked:
            throw refusal("locked", result.message);

        case PinRefusal::NoSuchPin:
            throw refusal("no_such_pin", result.message);

        case PinRefusal::WrongState:
        {
            YAML::Node document;
            std::string errorMessage;
            std::string status = "open";

            if (readPinsDocument(root, document, errorMessage))
            {
                for (const YAML::Node &pin : pinsWithStatus(document, ""))
                {
                    if (result.message.starts_with(pin["id"].Scalar() + " "))
                    {
                        status = pin["status"] ? pin["status"].Scalar() : std::string("open");
                    }
                }
            }

            throw refusal("wrong_state", result.message, [status](JsonWriter &data) { data.field("status", status); });
        }

        case PinRefusal::BadRequest:
            throw refusal("bad_request", result.message);

        case PinRefusal::None:
        case PinRefusal::Failed:
            break;
        }

        throw refusal("failed", result.message, nullptr, -32603);
    }

    writer.field("counter", result.counter);
    writer.key("pin");
    writer.node(result.pin);
}

// Standard base64 (RFC 4648, padded) to bytes; false on any other character or a wrong length.
bool decodeBase64(const std::string &text, std::string &bytes)
{
    static const std::array<int8_t, 256> table = []()
    {
        std::array<int8_t, 256> values;
        values.fill(-1);
        const std::string alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

        for (size_t index = 0; index < alphabet.size(); ++index)
        {
            values[static_cast<unsigned char>(alphabet[index])] = static_cast<int8_t>(index);
        }

        return values;
    }();

    if (text.size() % 4 != 0)
    {
        return false;
    }

    bytes.clear();
    bytes.reserve(text.size() / 4 * 3);

    for (size_t index = 0; index < text.size(); index += 4)
    {
        uint32_t group = 0;
        int padding = 0;

        for (size_t offset = 0; offset < 4; ++offset)
        {
            const char character = text[index + offset];

            if (character == '=' && index + 4 == text.size() && offset >= 2)
            {
                ++padding;
                group <<= 6;
                continue;
            }

            const int8_t value = table[static_cast<unsigned char>(character)];

            if (value < 0 || padding > 0)
            {
                return false;
            }

            group = (group << 6) | static_cast<uint32_t>(value);
        }

        bytes.push_back(static_cast<char>((group >> 16) & 0xff));

        if (padding < 2)
        {
            bytes.push_back(static_cast<char>((group >> 8) & 0xff));
        }

        if (padding < 1)
        {
            bytes.push_back(static_cast<char>(group & 0xff));
        }
    }

    return true;
}

// A picture of the request list ({media_type, base64}: pins.rpc.json $defs/picture_in) as the pins take it.
PinPicture pictureOf(const YAML::Node &node)
{
    PinPicture picture;

    if (!decodeBase64(node["base64"].Scalar(), picture.bytes))
    {
        throw refusal("bad_request", "the picture is not base64");
    }

    if (picture.bytes.size() > MaxPinPictureBytes)
    {
        throw refusal("bad_request", "the picture is larger than " + std::to_string(MaxPinPictureBytes / (1024 * 1024))
            + " MB");
    }

    return picture;
}

std::vector<PinPicture> picturesOf(const YAML::Node &params)
{
    std::vector<PinPicture> pictures;

    if (params["pictures"])
    {
        for (const YAML::Node &picture : params["pictures"])
        {
            pictures.push_back(pictureOf(picture));
        }
    }

    return pictures;
}

void pinsAdd(const YAML::Node &params, JsonWriter &writer)
{
    NewPin pin;
    pin.text = params["text"].Scalar();
    pin.on = params["on"] ? params["on"].Scalar() : std::string();
    pin.file = params["file"] ? params["file"].Scalar() : std::string();
    pin.author = params["author"] ? params["author"].Scalar() : std::string("agent");
    pin.source = params["source"] ? params["source"].Scalar() : pin.author == "user" ? std::string("studio")
                                                                                   : std::string("agent");
    pin.world = params["world"] ? params["world"].Scalar() : std::string();
    pin.map = params["map"] ? params["map"].Scalar() : std::string();

    if (params["at"])
    {
        pin.at = std::vector<double>{params["at"][0].as<double>(), params["at"][1].as<double>(),
            params["at"][2].as<double>()};
    }

    if (const YAML::Node pose = params["pose"]; pose)
    {
        pin.position = std::vector<double>{pose["position"][0].as<double>(), pose["position"][1].as<double>(),
            pose["position"][2].as<double>()};

        if (pose["yaw_radians"])
        {
            pin.yawRadians = pose["yaw_radians"].as<double>();
        }

        if (pose["pitch_degrees"])
        {
            pin.pitchDegrees = pose["pitch_degrees"].as<double>();
        }

        if (pose["heading_yaw_units"])
        {
            pin.headingYawUnits = pose["heading_yaw_units"].as<int>();
        }
    }

    if (params["picture"])
    {
        pin.picture = pictureOf(params["picture"]);
    }

    // The request list's pins are made now; `created` is the core's clock.
    PinResult result;
    const std::filesystem::path root = projectOf(params);
    pinAnswer(addPin(root, pin, result), result, root, writer);
}

void pinsClaim(const YAML::Node &params, JsonWriter &writer)
{
    PinResult result;
    const std::filesystem::path root = projectOf(params);
    pinAnswer(claimPin(root, params["pin"].Scalar(), params["by"].Scalar(), flag(params, "force", false), result),
        result, root, writer);
}

void pinsAct(const YAML::Node &params, JsonWriter &writer, PinAction action, const char *pDefaultAuthor)
{
    PinResult result;
    const std::filesystem::path root = projectOf(params);
    const std::string author = params["by"] ? params["by"].Scalar() : std::string(pDefaultAuthor);
    pinAnswer(actOnPin(root, params["pin"].Scalar(), action, author, params["text"] ? params["text"].Scalar() : "",
                  picturesOf(params), result),
        result, root, writer);
}

void pinsReply(const YAML::Node &params, JsonWriter &writer)
{
    pinsAct(params, writer, PinAction::Reply, "");
}

void pinsResolve(const YAML::Node &params, JsonWriter &writer)
{
    pinsAct(params, writer, PinAction::Resolve, "");
}

void pinsAccept(const YAML::Node &params, JsonWriter &writer)
{
    pinsAct(params, writer, PinAction::Accept, "user");
}

void pinsReopen(const YAML::Node &params, JsonWriter &writer)
{
    pinsAct(params, writer, PinAction::Reopen, "user");
}

void pinsDecline(const YAML::Node &params, JsonWriter &writer)
{
    pinsAct(params, writer, PinAction::Decline, "");
}

void pinsKeep(const YAML::Node &params, JsonWriter &writer)
{
    PinResult result;
    const std::filesystem::path root = projectOf(params);
    pinAnswer(keepPinPicture(root, params["pin"].Scalar(), result), result, root, writer);
}

void pinsImportInbox(const YAML::Node &params, JsonWriter &writer)
{
    InboxOptions options;
    options.dryRun = flag(params, "dry_run", false);
    // Only the projects given: the host maps what a client may name onto folders it allows.
    options.trustPinProject = false;

    for (const YAML::Node &project : params["projects"])
    {
        options.projects.push_back(project.Scalar());
    }

    InboxResult result;
    std::string errorMessage;

    if (!importPinInbox(params["inbox"].Scalar(), options, result, errorMessage))
    {
        throw refusal("bad_request", errorMessage.starts_with("no inbox folder") ? "no inbox folder there"
            : errorMessage);
    }

    writer.key("imported");
    writer.beginArray();

    for (const InboxImported &imported : result.imported)
    {
        writer.beginObject();
        writer.field("file", imported.file);
        writer.field("project", imported.project);

        if (!imported.pin.empty())
        {
            writer.field("pin", imported.pin);
        }

        writer.field("matched_by", imported.matchedBy == "map" ? "map" : "studio_file");
        writer.field("picture", imported.picture);
        writer.endObject();
    }

    writer.endArray();
    writer.key("skipped");
    writer.beginArray();

    for (const InboxSkipped &skipped : result.skipped)
    {
        writer.beginObject();
        writer.field("file", skipped.file);
        writer.field("reason", skipped.reason);
        writer.endObject();
    }

    writer.endArray();
}

// --- the methods of the MCP tools that ran command lines (S5a3: map_new, map_query, map_history, map_overview,
// map_flow, map_render, map_assets, map_api, map_build's install) ------------------------------------------------

// A message with a folder's path replaced by its name in words (the request list's messages name no paths).
std::string withoutPath(std::string message, const std::filesystem::path &folder, const std::string &words)
{
    const std::string text = folder.string();

    for (size_t at = text.empty() ? std::string::npos : message.find(text); at != std::string::npos;
         at = message.find(text, at + words.size()))
    {
        message.replace(at, text.size(), words);
    }

    return message;
}

const std::filesystem::path &assetRootOrRefuse(const std::string &method)
{
    if (session().assetRoot.empty())
    {
        throw refusal("no_asset_root", method + " reads the asset root: the session has none");
    }

    return session().assetRoot;
}

// What a reading method's params name (map, world, built), with the session's asset root and mount.
ReadRequest readRequestOf(const YAML::Node &params, const std::string &method)
{
    ReadRequest request;
    request.assetRoot = assetRootOrRefuse(method);
    request.world = params["world"] ? params["world"].Scalar() : std::string();
    request.target = params["map"].Scalar();
    const bool built = flag(params, "built", false);

    if (built && session().mount.empty())
    {
        throw refusal("no_mount", "`built` reads the session's mount of builds: the session has none");
    }

    // Always named, so a request never reads through the mount (or a project's preview mount) of the one before.
    request.mount = built ? session().mount : std::filesystem::path();
    return request;
}

RpcRefusal readRefusal(const ReadFailure &failure)
{
    const std::vector<ProjectIssue> issues = failure.issues;

    switch (failure.failure)
    {
    case TargetFailure::NotAProject:
        return refusal("not_a_project", failure.message,
            [issues](JsonWriter &data) { writeIssues(data, "issues", issues); });

    case TargetFailure::DoesNotBuild:
        return refusal("has_errors", failure.message,
            [issues](JsonWriter &data) { writeIssues(data, "issues", issues); });

    case TargetFailure::NoAssetRoot:
        return refusal("no_asset_root", failure.message);

    case TargetFailure::None:
    case TargetFailure::Failed:
        break;
    }

    if (failure.noSuchMap)
    {
        return refusal("no_such_map", failure.message);
    }

    if (failure.badWorld)
    {
        return refusal("bad_request", failure.message);
    }

    return refusal("failed", failure.message, nullptr, -32603);
}

std::string base64(const std::vector<uint8_t> &bytes)
{
    static const char *const Alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string text;
    text.reserve((bytes.size() + 2) / 3 * 4);

    for (size_t index = 0; index < bytes.size(); index += 3)
    {
        const uint32_t chunk = (uint32_t(bytes[index]) << 16)
            | (index + 1 < bytes.size() ? uint32_t(bytes[index + 1]) << 8 : 0u)
            | (index + 2 < bytes.size() ? uint32_t(bytes[index + 2]) : 0u);
        text += Alphabet[(chunk >> 18) & 63];
        text += Alphabet[(chunk >> 12) & 63];
        text += index + 1 < bytes.size() ? Alphabet[(chunk >> 6) & 63] : '=';
        text += index + 2 < bytes.size() ? Alphabet[chunk & 63] : '=';
    }

    return text;
}

void projectNew(const YAML::Node &params, JsonWriter &writer)
{
    NewProjectRequest request;
    request.root = projectOf(params);
    request.id = params["id"].Scalar();
    request.name = params["name"].Scalar();

    if (params["world"])
    {
        request.world = params["world"].Scalar();
    }

    if (params["reference"])
    {
        request.reference = params["reference"].Scalar();
    }

    if (params["stats_id"])
    {
        request.statsId = std::to_string(params["stats_id"].as<int>());
    }

    if (params["kind"])
    {
        request.kind = params["kind"].Scalar();
    }

    std::vector<std::string> written;
    bool exists = false;
    std::string errorMessage;

    if (!createEmptyProject(request, written, exists, errorMessage))
    {
        if (exists)
        {
            throw refusal("bad_request", "the folder already holds a project: open it, or name another folder");
        }

        throw refusal("failed", withoutPath(errorMessage, request.root, "the project folder"), nullptr, -32603);
    }

    Project project;
    std::vector<ProjectIssue> issues;
    loadProject(request.root, project, issues);
    writeStrings(writer, "files", written);
    writer.field("revision", projectRevision(project));
    writer.field("next", request.kind == "outdoor" ? NewOutdoorProjectNext : NewProjectNext);
}

void projectQuery(const YAML::Node &params, JsonWriter &writer)
{
    StudioService::Entry &entry = keptOrRefuse(projectOf(params));
    const Project &project = entry.memory.project;
    const std::string id = params["id"] ? params["id"].Scalar() : std::string();
    const std::string list = params["list"] ? params["list"].Scalar() : std::string();
    const std::string onlyFile = params["file"] ? params["file"].Scalar() : std::string();

    if (!id.empty() && !list.empty())
    {
        throw refusal("bad_request", "give `id` or `list`, not both");
    }

    writer.field("revision", entry.memory.revision);

    if (id.empty() && list.empty())
    {
        // The summary: the map card's own words and, per file, each list with its ids.
        const YAML::Node card = project.document("project.yml");
        writer.key("card");
        writer.beginObject();

        for (const char *pKey : {"id", "name", "world", "kind", "profile", "base"})
        {
            if (card.IsMap() && card[pKey] && card[pKey].IsScalar())
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

                std::vector<std::string> ids;
                const YAML::Node items = iterator->second;

                for (const YAML::Node &item : items)
                {
                    if (item.IsMap() && item["id"] && item["id"].IsScalar() && ids.size() < 60)
                    {
                        ids.push_back(item["id"].Scalar());
                    }
                }

                if (items.size() > 60)
                {
                    ids.push_back("... " + std::to_string(items.size() - 60) + " more");
                }

                writeStrings(writer, iterator->first.Scalar(), ids);
            }

            writer.endObject();
        }

        writer.endObject();
        return;
    }

    // Every place the id or the list is in (ids are unique per file, not per project).
    struct Place
    {
        std::string file;
        std::string list;
        YAML::Node value;
    };

    std::vector<Place> places;

    for (const std::pair<const std::string, ProjectFile> &file : project.files)
    {
        const YAML::Node &root = file.second.document;

        if (!root.IsMap() || file.first == "ids.lock.yml" || (!onlyFile.empty() && file.first != onlyFile))
        {
            continue;
        }

        for (YAML::const_iterator iterator = root.begin(); iterator != root.end(); ++iterator)
        {
            if (!list.empty())
            {
                if (iterator->first.Scalar() == list && iterator->second.IsSequence())
                {
                    places.push_back({file.first, list, iterator->second});
                }

                continue;
            }

            if (!iterator->second.IsSequence())
            {
                continue;
            }

            const YAML::Node items = iterator->second;

            for (const YAML::Node &item : items)
            {
                if (item.IsMap() && item["id"] && item["id"].IsScalar() && item["id"].Scalar() == id)
                {
                    places.push_back({file.first, iterator->first.Scalar(), item});
                }
            }
        }
    }

    const std::string what = id.empty() ? "a list named " + list : id;

    if (places.empty())
    {
        throw refusal("no_such_object", "nothing in the project" + (onlyFile.empty() ? "" : " (" + onlyFile + ")")
            + " is " + what + " (project.query without id and list lists every id)");
    }

    if (places.size() > 1)
    {
        std::string files;

        for (const Place &place : places)
        {
            files += (files.empty() ? "" : " and ") + place.file;
        }

        throw refusal("bad_request", what + " is in " + files + ": give `file`");
    }

    const Place &place = places.front();
    writer.field("file", place.file);
    writer.field("list", place.list);

    if (!list.empty())
    {
        writer.key("items");
        writer.node(place.value);
        return;
    }

    writer.key("object");
    writer.node(place.value);

    // The engine number the build gave the id (the event number check.flow_event takes, a door's id).
    if (project.has("ids.lock.yml") && project.document("ids.lock.yml").IsMap())
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
                break;
            }
        }
    }
}

void editRevert(const YAML::Node &params, JsonWriter &writer, RevertKind kind)
{
    const std::filesystem::path root = projectOf(params);
    {
        Project project;
        std::vector<ProjectIssue> issues;
        loadOrRefuse(root, project, issues);
    }

    RevertRequest request;
    request.kind = kind;
    request.sequence = params["sequence"] ? params["sequence"].as<int>() : 0;
    request.force = flag(params, "force", false);
    TransactionOptions options;
    options.assetRoot = session().assetRoot;
    options.allowNewIssues = flag(params, "allow_errors", false);
    options.label = params["label"] ? params["label"].Scalar() : std::string();

    // Whose: the author named, or else anybody's latest (as `oymap undo`), the entry then written by `agent`.
    if (params["author"])
    {
        options.author = params["author"].Scalar();
    }
    else
    {
        options.author = "agent";
        request.whose = "*";
    }

    TransactionResult result;
    bool applied = false;

    {
        ProjectWriteLock lock(root);
        std::vector<ProjectIssue> issues;
        StudioService::Entry *pEntry = lock.held() ? session().service.project(root, issues) : nullptr;

        if (!lock.held())
        {
            result.refusal = TransactionRefusal::Locked;
            result.errors.push_back(ProjectLockedMessage);
        }
        else if (pEntry == nullptr)
        {
            result.refusal = TransactionRefusal::NotAProject;
            result.errors.push_back(issues.empty() ? std::string("not a project") : issues.front().message);
        }
        else
        {
            applied = session().service.revert(*pEntry, request, options, result);
        }
    }

    if (!applied)
    {
        refuseTransaction(root, result);
    }

    const char *pWord = kind == RevertKind::Undo ? "undone: " : kind == RevertKind::Redo ? "redone: " : "reverted: ";
    std::vector<std::string> changes;

    for (const std::string &change : result.changes)
    {
        changes.push_back(pWord + change);
    }

    StudioService::Entry &entry = keptOrRefuse(root);
    writer.field("revision", entry.memory.revision);
    int reverts = 0;

    if (result.sequence > 0)
    {
        StoredHistoryEntry written;
        std::string unused;

        if (readHistoryEntry(root, result.sequence, false, written, unused) && written.node["reverts"])
        {
            reverts = written.node["reverts"].as<int>();
        }
    }

    writer.field("reverts", reverts > 0 ? reverts : std::max(request.sequence, 1));

    if (result.sequence > 0)
    {
        writer.field("sequence", result.sequence);
    }

    writeStrings(writer, "changes", changes);
    writeStrings(writer, "conflicts", result.conflicts);

    if (!result.notes.empty())
    {
        writeStrings(writer, "notes", result.notes);
    }

    writeIssues(writer, "new_issues", result.newIssues);
    writeChangedFiles(writer, result);
}

void editUndo(const YAML::Node &params, JsonWriter &writer)
{
    editRevert(params, writer, RevertKind::Undo);
}

void editRedo(const YAML::Node &params, JsonWriter &writer)
{
    editRevert(params, writer, RevertKind::Redo);
}

void editRevertEntry(const YAML::Node &params, JsonWriter &writer)
{
    editRevert(params, writer, RevertKind::Revert);
}

void checkAudit(const YAML::Node &params, JsonWriter &writer)
{
    AuditRequest request;
    request.read = readRequestOf(params, "check.audit");
    request.reach = flag(params, "reach", false);
    request.strict = flag(params, "strict", false);
    request.solve = flag(params, "solve", false);
    request.original = params["original"] ? params["original"].Scalar() : std::string();
    size_t errors = 0;
    ReadFailure failure;

    if (!writeAuditMembers(request, writer, errors, failure))
    {
        throw readRefusal(failure);
    }

    writer.field("errors", static_cast<uint64_t>(errors));
}

void checkSolve(const YAML::Node &params, JsonWriter &writer)
{
    ReadFailure failure;

    if (!writeSolveMembers(readRequestOf(params, "check.solve"), writer, failure))
    {
        throw readRefusal(failure);
    }
}

void checkFlowEvent(const YAML::Node &params, JsonWriter &writer)
{
    const ReadRequest request = readRequestOf(params, "check.flow_event");
    const int64_t event = params["event"].as<int64_t>();
    std::string mapFile;
    std::string flowJson;
    ReadFailure failure;

    if (!readEventFlow(request, mapFile, flowJson, failure))
    {
        throw readRefusal(failure);
    }

    const YAML::Node events = YAML::Load(flowJson);

    for (const YAML::Node &handler : events)
    {
        if (!handler["event"] || handler["event"].as<int64_t>() != event)
        {
            continue;
        }

        writer.field("map", mapFile);
        writer.field("event", event);
        writer.field("title", handler["title"] ? handler["title"].Scalar() : std::string());
        writer.key("paths");
        writer.beginArray();

        for (const YAML::Node &path : handler["paths"])
        {
            writer.beginObject();
            writer.key("tests");
            writer.beginArray();

            for (const YAML::Node &test : path["tests"])
            {
                writer.beginObject();
                writer.field("what", test["what"].Scalar());
                writer.field("taken", test["taken"].Scalar() == "true");
                writer.endObject();
            }

            writer.endArray();
            std::vector<std::string> effects;

            for (const YAML::Node &effect : path["effects"])
            {
                effects.push_back(effect.Scalar());
            }

            writeStrings(writer, "effects", effects);

            if (path["error"])
            {
                writer.field("error", path["error"].Scalar());
            }

            writer.endObject();
        }

        writer.endArray();
        writer.field("truncated", handler["truncated"] && handler["truncated"].Scalar() == "true");
        return;
    }

    throw refusal("no_such_object", "the map has no handler for event " + std::to_string(event));
}

void viewRender(const YAML::Node &params, JsonWriter &writer)
{
    RenderRequest request;
    request.read = readRequestOf(params, "view.render");
    request.isometric = params["view"] && params["view"].Scalar() == "iso";
    request.size = params["size"] ? params["size"].as<int>() : 1024;
    request.labels = flag(params, "labels", true);
    std::vector<uint8_t> png;
    int width = 0;
    int height = 0;
    std::string mapFile;
    ReadFailure failure;

    if (!renderTargetPng(request, png, width, height, mapFile, failure))
    {
        throw readRefusal(failure);
    }

    writer.field("map", mapFile);
    writer.field("width", width);
    writer.field("height", height);
    writer.field("png_base64", base64(png));
}

void assetsSearch(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path &assetRoot = assetRootOrRefuse("assets.search");
    std::string errorMessage;

    if (!writeAssetSearchMembers(assetRoot, params["query"].Scalar(),
            params["world"] ? params["world"].Scalar() : std::string("mm6"),
            params["kind"] ? params["kind"].Scalar() : std::string(),
            params["limit"] ? params["limit"].as<size_t>() : 40, writer, errorMessage))
    {
        throw refusal("bad_request", withoutPath(errorMessage, assetRoot, "the asset root"));
    }
}

void assetsScriptReference(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path &assetRoot = assetRootOrRefuse("assets.script_reference");
    AssetSession assets;
    std::string errorMessage;
    std::string text;

    if (!assets.open(assetRoot, params["world"] ? params["world"].Scalar() : std::string("mm6"), errorMessage))
    {
        throw refusal("bad_request", withoutPath(errorMessage, assetRoot, "the asset root"));
    }

    if (!scriptReference(loadScriptSupport(assets), text, errorMessage))
    {
        throw refusal("failed", withoutPath(errorMessage, assetRoot, "the asset root"), nullptr, -32603);
    }

    writeStrings(writer, "functions", eventFunctionNames());
    writer.field("reference", text);
}

void sessionSchema(const YAML::Node &params, JsonWriter &writer)
{
    const SchemaSet &schemas = SchemaSet::builtIn();

    if (!params["name"])
    {
        writer.key("schemas");
        writer.beginArray();

        for (const std::string &name : schemas.fileNames())
        {
            const YAML::Node root = schemas.root(name);
            writer.beginObject();
            writer.field("name", name);
            writer.field("title", root["title"] ? root["title"].Scalar() : std::string());
            writer.endObject();
        }

        writer.endArray();
        return;
    }

    std::string name = params["name"].Scalar();

    if (!schemas.has(name))
    {
        name += ".schema.json";
    }

    if (!schemas.has(name))
    {
        throw refusal("bad_request", "no schema named " + params["name"].Scalar() + " (session.schema without "
            "`name` lists them)");
    }

    writer.field("name", name);
    writer.key("schema");
    writer.node(schemas.root(name));
}

void buildInstall(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path root = projectOf(params);
    const std::filesystem::path &assetRoot = assetRootOrRefuse("build.install");

    if (session().mount.empty())
    {
        throw refusal("no_mount", "build.install installs into the session's mount of builds: the session has none");
    }

    Project project;
    std::vector<ProjectIssue> issues;
    loadOrRefuse(root, project, issues);

    if (!issues.empty())
    {
        throw refusal("has_errors", "the project's files do not read: nothing is installed",
            [issues](JsonWriter &data) { writeIssues(data, "issues", issues); });
    }

    std::vector<std::string> installed;
    std::string errorMessage;

    if (!installBuildIntoMount(project, project.root / "build", session().mount, assetRoot, installed, errorMessage))
    {
        errorMessage = withoutPath(errorMessage, session().mount, "the mount");
        errorMessage = withoutPath(errorMessage, root, "the project");
        throw refusal("failed", withoutPath(errorMessage, assetRoot, "the asset root"), nullptr, -32603);
    }

    writeStrings(writer, "installed", installed);
}

// --- walk -----------------------------------------------------------------------------------------------------------

std::vector<uint8_t> readWalkFile(const YAML::Node &params, const char *pName)
{
    std::ifstream file(params[pName].Scalar(), std::ios::binary);

    if (!file)
    {
        throw refusal("bad_request", std::string("walk.load cannot read its `") + pName + "` file");
    }

    return std::vector<uint8_t>((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
}

WalkSession &loadedWalk()
{
    if (!session().walk.loaded())
    {
        throw refusal("bad_request", "no walk: walk.load first (or it failed)");
    }

    return session().walk;
}

std::array<float, 3> walkPoint(const YAML::Node &node)
{
    return {node[0].as<float>(), node[1].as<float>(), node[2].as<float>()};
}

void writeWalkPose(JsonWriter &writer, const std::string &name, const WalkPose &pose)
{
    const WalkSession &walk = session().walk;
    writer.key(name);
    writer.beginObject();
    writer.key("position");
    writer.beginArray();

    for (const float value : {pose.x, pose.y, pose.footZ})
    {
        writer.value(rounded(value, 3));
    }

    writer.endArray();
    writer.field("eye_z", rounded(pose.eyeZ, 3));
    writer.field("vertical_velocity", rounded(pose.verticalVelocity, 3));
    writer.field("grounded", pose.grounded);
    writer.field("landed", pose.landed);

    if (walk.outdoor())
    {
        writer.field("on_water", pose.onWater);

        if (pose.model >= 0)
        {
            writer.field("model", pose.model);
            writer.field("face", pose.face);
        }
    }
    else
    {
        writer.field("sector", pose.sector);
        writer.field("eye_sector", pose.eyeSector);

        if (const std::string room = walk.roomOfSector(pose.sector); !room.empty())
        {
            writer.field("room", room);
        }

        if (pose.face >= 0)
        {
            writer.field("face", pose.face);
        }
    }

    writer.field("bits", walkPoseBits(pose));
    writer.endObject();
}

void walkLoad(const YAML::Node &params, JsonWriter &writer)
{
    const std::vector<uint8_t> map = readWalkFile(params, "map");
    const std::vector<uint8_t> state = readWalkFile(params, "state");
    const std::vector<uint8_t> decorations = readWalkFile(params, "decorations");
    const std::vector<uint8_t> terrain = params["terrain"] ? readWalkFile(params, "terrain") : std::vector<uint8_t>();
    std::string errorMessage;

    if (!session().walk.load(map, std::string(state.begin(), state.end()),
            std::string(decorations.begin(), decorations.end()), terrain, errorMessage))
    {
        throw refusal("bad_request", "walk.load: " + errorMessage);
    }

    const WalkSession &walk = session().walk;
    writer.field("kind", walk.outdoor() ? "outdoor" : "indoor");
    writer.field("faces", static_cast<int64_t>(walk.faceCount()));
    writer.field("decoration_colliders", static_cast<int64_t>(walk.decorationColliderCount()));
    writer.key("party");
    writer.beginObject();
    writer.field("radius", rounded(walk.party().radius, 2));
    writer.field("height", rounded(walk.party().height, 2));
    writer.field("eye_height", rounded(walk.party().eyeHeight, 2));
    writer.field("max_step_height", rounded(walk.party().maxStepHeight, 2));
    writer.endObject();
    writer.key("doors");
    writer.beginArray();

    for (const WalkDoor &door : walk.doors())
    {
        writer.beginObject();
        writer.field("id", door.id);
        writer.field("open", door.open);
        writer.endObject();
    }

    writer.endArray();
    writeWalkPose(writer, "pose", walk.pose());
}

void walkPlace(const YAML::Node &params, JsonWriter &writer)
{
    WalkSession &walk = loadedWalk();
    const std::array<float, 3> eye = walkPoint(params["eye"]);
    writeWalkPose(writer, "pose", walk.placeEye(eye[0], eye[1], eye[2]));
}

void walkStep(const YAML::Node &params, JsonWriter &writer)
{
    WalkSession &walk = loadedWalk();
    const float yaw = params["yaw_radians"].as<float>();
    const uint32_t buttons = params["buttons"].as<uint32_t>();
    const float seconds = params["seconds"].as<float>();
    const int frames = params["frames"] ? params["frames"].as<int>() : 1;
    WalkPose pose = walk.pose();

    for (int frame = 0; frame < frames; ++frame)
    {
        pose = walk.step(yaw, buttons, seconds);
    }

    writeWalkPose(writer, "pose", pose);
}

void walkReplay(const YAML::Node &params, JsonWriter &writer)
{
    WalkSession &walk = loadedWalk();
    const std::array<float, 3> eye = walkPoint(params["eye"]);
    walk.placeEye(eye[0], eye[1], eye[2]);
    std::multimap<int64_t, std::string> toggles;

    for (const YAML::Node &toggle : params["toggles"])
    {
        toggles.emplace(toggle["frame"].as<int64_t>(), toggle["door"].Scalar());
    }

    const int64_t traceEvery = params["trace_every"] ? params["trace_every"].as<int64_t>() : 0;
    std::vector<std::string> trace;
    uint64_t hash = 1469598103934665603ull;
    WalkPose pose = walk.pose();
    int64_t frame = 0;

    for (const YAML::Node &input : params["frames"])
    {
        for (auto toggle = toggles.lower_bound(frame); toggle != toggles.upper_bound(frame); ++toggle)
        {
            if (!walk.toggle(toggle->second))
            {
                throw refusal("no_such_object", "the walk has no door " + toggle->second + " to toggle");
            }
        }

        pose = walk.step(input[0].as<float>(), input[1].as<uint32_t>(), input[2].as<float>());
        const std::string bits = walkPoseBits(pose);

        for (const char character : bits)
        {
            hash = (hash ^ static_cast<unsigned char>(character)) * 1099511628211ull;
        }

        if (traceEvery > 0 && frame % traceEvery == 0)
        {
            trace.push_back(bits);
        }

        ++frame;
    }

    char hashText[24] = {};
    std::snprintf(hashText, sizeof(hashText), "%016llx", static_cast<unsigned long long>(hash));
    writer.field("frames", frame);
    writer.field("hash", std::string(hashText));
    writeWalkPose(writer, "pose", pose);

    if (traceEvery > 0)
    {
        writeStrings(writer, "trace", trace);
    }
}

void walkToggle(const YAML::Node &params, JsonWriter &writer)
{
    WalkSession &walk = loadedWalk();
    const std::string door = params["door"].Scalar();

    if (walk.outdoor())
    {
        throw refusal("bad_request",
            "walk.toggle moves indoor doors only: outdoor moving models are not toggled in walk mode");
    }

    const std::optional<bool> open = walk.toggle(door);

    if (!open)
    {
        throw refusal("no_such_object", "the walk has no door, lift or mover " + door);
    }

    writer.field("door", door);
    writer.field("open", *open);
}

// --- compare, the original's mesh and the remaining reading commands (S5a5) ------------------------------------

void compareRun(const YAML::Node &params, JsonWriter &writer)
{
    CompareRequest request;
    request.read = readRequestOf(params, "compare.run");
    request.original = params["original"] ? params["original"].Scalar() : std::string();
    request.originalWorld = params["original_world"] ? params["original_world"].Scalar() : std::string();
    ReadFailure failure;

    if (!writeCompareMembers(request, writer, failure))
    {
        throw readRefusal(failure);
    }
}

// The original's meshes, made once per asset root, world and map (a shipped map does not change under a session).
struct ShippedMesh
{
    ViewMesh mesh;
    std::string kind;
    std::string map;
    std::string name;
};

std::map<std::string, std::shared_ptr<ShippedMesh>> &shippedMeshes()
{
    static std::map<std::string, std::shared_ptr<ShippedMesh>> meshes;
    return meshes;
}

void viewOriginalMesh(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path root = projectOf(params);
    StudioService::Entry &entry = keptOrRefuse(root);
    const YAML::Node card = entry.memory.project.document("project.yml");
    std::string original = params["original"] ? params["original"].Scalar() : std::string();
    const YAML::Node stats = card.IsMap() ? card["map_stats"] : YAML::Node();

    if (original.empty() && stats && stats.IsMap() && stats["reference"] && stats["reference"].IsScalar())
    {
        original = stats["reference"].Scalar();
    }

    if (original.empty() && card.IsMap() && card["base"] && card["base"].IsScalar())
    {
        original = card["base"].Scalar();
    }

    if (original.empty())
    {
        throw refusal("bad_request", "the project has no original: no map_stats.reference (a new map) and no "
                                     "`original` given");
    }

    ReadRequest request;
    request.assetRoot = assetRootOrRefuse("view.original_mesh");
    request.world = worldOf(entry.memory.project);
    request.target = original;
    request.mount = std::filesystem::path();
    const std::string key = request.assetRoot.string() + "\n" + request.world + "\n" + original;
    std::shared_ptr<ShippedMesh> &kept = shippedMeshes()[key];

    if (!kept)
    {
        auto made = std::make_shared<ShippedMesh>();
        ReadFailure failure;

        if (!readShippedViewMesh(request, made->mesh, made->kind, made->map, failure))
        {
            shippedMeshes().erase(key);
            throw readRefusal(failure);
        }

        // Named by the map and by its own bytes, as a project's view meshes are (the host serves them immutable).
        made->name = contentHash128(request.world + "/" + made->map).substr(0, 16) + "-original-"
            + contentHash128(std::string(made->mesh.bytes.begin(), made->mesh.bytes.end())).substr(0, 12) + ".mesh";
        kept = made;
    }

    // Beside the project's own view meshes (a project's later meshes may have pruned it: written again).
    const std::filesystem::path folder = projectStateRoot(root, true) / "view";
    std::error_code error;
    std::filesystem::create_directories(folder, error);
    std::string errorMessage;

    if (std::filesystem::file_size(folder / kept->name, error) != kept->mesh.bytes.size() || error)
    {
        if (!writeBinaryFileAtomically(folder / kept->name, kept->mesh.bytes, errorMessage))
        {
            throw refusal("failed", errorMessage, nullptr, -32603);
        }
    }

    writer.field("original", kept->map);
    writer.field("world", request.world);
    writer.field("kind", kept->kind);
    writer.field("file", ".oymap/view/" + kept->name);
    writeMeshMembers(writer, kept->mesh);
}

// view.overlay (S6_PLAN.md item O): an overlay project's scene things on the base map, for the plan view.
void viewOverlay(const YAML::Node &params, JsonWriter &writer)
{
    StudioService::Entry &entry = keptOrRefuse(projectOf(params));
    const std::filesystem::path &assetRoot = assetRootOrRefuse("view.overlay");
    std::string kind;
    std::string message;

    if (!describeSceneOverlay(entry.memory.project, assetRoot, writer, kind, message))
    {
        throw refusal(kind, message);
    }
}

void checkMetrics(const YAML::Node &params, JsonWriter &writer)
{
    const ReadRequest request = readRequestOf(params, "check.metrics");
    std::string json;
    std::string mapFile;
    std::string world;
    ReadFailure failure;

    if (!readMetricsJson(request, flag(params, "reach", false), json, mapFile, world, failure))
    {
        throw readRefusal(failure);
    }

    writer.field("map", mapFile);
    writer.field("world", world);
    writer.key("metrics");
    writer.raw(json);
}

std::array<float, 3> probePoint(const YAML::Node &node)
{
    return {node[0].as<float>(), node[1].as<float>(), node[2].as<float>()};
}

void checkProbe(const YAML::Node &params, JsonWriter &writer)
{
    const ReadRequest request = readRequestOf(params, "check.probe");
    std::string text;
    std::string mapFile;
    ReadFailure failure;

    if (!readProbeText(request, probePoint(params["from"]), probePoint(params["to"]), flag(params, "doors_open", false),
            text, mapFile, failure))
    {
        throw readRefusal(failure);
    }

    std::vector<std::string> lines;
    std::istringstream stream(text);

    for (std::string line; std::getline(stream, line);)
    {
        if (!line.empty())
        {
            lines.push_back(line);
        }
    }

    writer.field("map", mapFile);
    writeStrings(writer, "lines", lines);
}

void projectImport(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path root = projectOf(params);
    ReadRequest request;
    request.assetRoot = assetRootOrRefuse("project.import");
    request.world = params["world"].Scalar();
    request.target = params["map"].Scalar();
    request.mount = std::filesystem::path();
    std::vector<std::string> written;
    std::string mapFile;
    ReadFailure failure;

    if (!importShippedMap(request, root, written, mapFile, failure))
    {
        failure.message = withoutPath(failure.message, root, "the project folder");
        throw readRefusal(failure);
    }

    std::vector<std::string> names;

    for (const std::string &file : written)
    {
        const std::filesystem::path path = file;
        names.push_back(path.is_absolute() ? path.lexically_relative(root).generic_string() : path.generic_string());
    }

    writer.field("map", mapFile);
    writeStrings(writer, "written", names);
}

void projectFmt(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path root = projectOf(params);
    const bool checkOnly = flag(params, "check", false);
    Project project;
    std::vector<ProjectIssue> issues;
    loadProject(root, project, issues);

    if (!issues.empty())
    {
        throw refusal("has_errors", "a file of the project cannot be read",
            [issues](JsonWriter &data) { writeIssues(data, "issues", issues); });
    }

    std::vector<std::string> changed;

    for (const std::pair<const std::string, ProjectFile> &file : project.files)
    {
        const std::string canonical = canonicalText(file.second);

        if (canonical == file.second.text)
        {
            continue;
        }

        changed.push_back(file.first);
        std::string errorMessage;

        if (!checkOnly && !writeTextFileAtomically(project.root / file.first, canonical, errorMessage))
        {
            throw refusal("failed", withoutPath(errorMessage, root, "the project folder"), nullptr, -32603);
        }
    }

    writer.field("checked_only", checkOnly);
    writeStrings(writer, "not_canonical", changed);
}

void projectProtect(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path root = projectOf(params);
    {
        Project project;
        std::vector<ProjectIssue> issues;
        loadOrRefuse(root, project, issues);
    }

    TransactionResult result;

    if (!protectProject(root, flag(params, "clear", false), result))
    {
        refuseTransaction(root, result);
    }

    StudioService::Entry &entry = keptOrRefuse(root);
    writer.field("revision", entry.memory.revision);
    writer.field("marked", result.mark.marked);
    writeHandMark(writer, result.mark);

    if (result.sequence > 0)
    {
        writer.field("sequence", result.sequence);
    }
}

void projectMigrate(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path root = projectOf(params);
    {
        Project project;
        std::vector<ProjectIssue> issues;
        loadOrRefuse(root, project, issues);
    }

    TransactionResult result;

    if (!migrateProject(root, flag(params, "dry_run", false), result))
    {
        refuseTransaction(root, result);
    }

    StudioService::Entry &entry = keptOrRefuse(root);
    writer.field("revision", entry.memory.revision);
    std::vector<std::string> files;

    for (const std::pair<const std::string, std::string> &file : result.filesAfter)
    {
        files.push_back(file.first);
    }

    writeStrings(writer, "files", files);
    writer.field("keys_written", static_cast<uint64_t>(result.keysAllocated.size()));

    if (result.sequence > 0)
    {
        writer.field("sequence", result.sequence);
    }
}

// The effective values of one object (S5_BROWSER_EDITOR.md 3.8, "defaults are the lowering's"): its written fields,
// what it takes from elsewhere when a field is not written (a room's theme and ambient from rooms.yml `defaults`, its
// surfaces from its theme), and where the view's lowering put it (its resolved geometry, from view.layout).
// The map card's encounter slots (project.resolve's `slots`): written in project.yml or from the reference map's row.
void writeCardSlots(JsonWriter &writer, const MapCard &card)
{
    writer.key("slots");
    writer.beginArray();

    for (const CardSlot &slot : card.slots)
    {
        writer.beginObject();
        writer.field("slot", static_cast<int64_t>(slot.slot));
        writer.field("monster", slot.monster);

        if (!slot.picture.empty() && slot.picture != slot.monster)
        {
            writer.field("picture", slot.picture);
        }

        if (!slot.tier.empty())
        {
            writer.field("tier", slot.tier);
        }

        if (!slot.count.empty())
        {
            writer.field("count", slot.count);
        }

        if (!slot.weight.empty())
        {
            writer.field("weight", slot.weight);
        }

        writer.field("source", slot.source);
        writer.field("from", slot.from);
        writer.endObject();
    }

    writer.endArray();

    if (!card.referenceProblem.empty())
    {
        writer.field("card_note", card.referenceProblem);
    }
}

void projectResolve(const YAML::Node &params, JsonWriter &writer)
{
    StudioService::Entry &entry = keptOrRefuse(projectOf(params));
    const Project &project = entry.memory.project;

    // The map card itself (`card`): project.yml map_stats as the game will read it, the columns it leaves out taken
    // from its reference map's row, and the encounter slots.
    if (!params["id"])
    {
        if (!flag(params, "card", false))
        {
            throw refusal("bad_request", "name the object (`id`), or ask for the map card (`card: true`)");
        }

        const MapCard card = resolveMapCard(project, session().assetRoot);
        writer.field("id", "map_stats");
        writer.field("file", "project.yml");
        writer.field("list", "");
        writer.key("fields");
        writer.beginObject();
        const YAML::Node cardDocument = project.document("project.yml");
        const YAML::Node stats = cardDocument.IsMap() && cardDocument["map_stats"] ? cardDocument["map_stats"]
            : YAML::Node(YAML::NodeType::Map);

        for (YAML::const_iterator field = stats.begin(); field != stats.end(); ++field)
        {
            writer.key(field->first.Scalar());
            writer.beginObject();
            writer.key("value");
            writer.node(field->second);
            writer.field("source", "written");
            writer.endObject();
        }

        for (const CardValue &value : card.fromReference)
        {
            writer.key(value.name);
            writer.beginObject();
            writer.key("value");
            writer.node(YAML::Node(value.value));
            writer.field("source", "reference");
            writer.field("from", value.from);
            writer.endObject();
        }

        writer.endObject();
        writeCardSlots(writer, card);
        return;
    }

    const std::string id = params["id"].Scalar();
    const std::string wanted = params["file"] ? params["file"].Scalar() : std::string();
    std::string fileName;
    YAML::Node object;
    std::string listName;

    for (const std::pair<const std::string, ProjectFile> &file : project.files)
    {
        if (!isSourceFile(file.first) || (!wanted.empty() && file.first != wanted) || !file.second.document.IsMap())
        {
            continue;
        }

        for (YAML::const_iterator list = file.second.document.begin(); list != file.second.document.end(); ++list)
        {
            const YAML::Node items = list->second;

            for (size_t index = 0; items.IsSequence() && index < items.size(); ++index)
            {
                if (items[index].IsMap() && items[index]["id"] && items[index]["id"].Scalar() == id)
                {
                    if (!fileName.empty() && fileName != file.first)
                    {
                        throw refusal("bad_request", "the id " + id + " is in " + fileName + " and " + file.first
                            + ": name the one meant with `file`");
                    }

                    fileName = file.first;
                    object = items[index];
                    listName = list->first.Scalar();
                }
            }
        }
    }

    if (fileName.empty())
    {
        throw refusal("no_such_object", "nothing in the project has the id " + id);
    }

    writer.field("id", id);
    writer.field("file", fileName);
    writer.field("list", listName);
    writer.key("fields");
    writer.beginObject();
    std::set<std::string> written;

    for (YAML::const_iterator field = object.begin(); field != object.end(); ++field)
    {
        written.insert(field->first.Scalar());
        writer.key(field->first.Scalar());
        writer.beginObject();
        writer.key("value");
        writer.node(field->second);
        writer.field("source", "written");
        writer.endObject();
    }

    const auto inherited = [&writer, &written](const std::string &name, const YAML::Node &value, const char *pSource,
        const std::string &from)
    {
        if (written.contains(name) || !value.IsDefined() || value.IsNull())
        {
            return;
        }

        written.insert(name);
        writer.key(name);
        writer.beginObject();
        writer.key("value");
        writer.node(value);
        writer.field("source", pSource);
        writer.field("from", from);
        writer.endObject();
    };

    if (fileName == "rooms.yml" && listName == "rooms")
    {
        const YAML::Node rooms = project.document("rooms.yml");
        const YAML::Node defaults = rooms["defaults"];

        if (defaults.IsMap())
        {
            for (YAML::const_iterator field = defaults.begin(); field != defaults.end(); ++field)
            {
                inherited(field->first.Scalar(), field->second, "default", "rooms.yml defaults");
            }
        }

        const std::string themeId = object["theme"] ? object["theme"].Scalar()
            : defaults.IsMap() && defaults["theme"] ? defaults["theme"].Scalar() : std::string();

        for (const YAML::Node &theme : rooms["themes"])
        {
            if (theme.IsMap() && theme["id"] && theme["id"].Scalar() == themeId)
            {
                for (YAML::const_iterator field = theme.begin(); field != theme.end(); ++field)
                {
                    const std::string name = field->first.Scalar();

                    if (name != "id" && name != "notes")
                    {
                        // The theme's words a room takes: its bands and ends by the same names, its surfaces as
                        // "<word> surface".
                        const bool same = name == "bands" || name == "ends";
                        inherited(same ? name : name + "_surface", field->second, "theme", themeId);
                    }
                }
            }
        }
    }

    writer.endObject();

    // A spawn point draws on the map card's encounter slots: the inspector names the monsters of its slot.
    if (fileName == "objects.yml" && listName == "spawns")
    {
        writeCardSlots(writer, resolveMapCard(project, session().assetRoot));
    }

    // Where the view's lowering put it (the current view, or the last that lowered: `stale`).
    std::vector<ProjectIssue> unused;
    const std::shared_ptr<StudioService::View> view = session().service.view(entry);

    if (view)
    {
        const YAML::Node layout = YAML::Load(std::string("{") + session().service.layout(*view) + "}");

        for (YAML::const_iterator list = layout.begin(); layout.IsMap() && list != layout.end(); ++list)
        {
            const YAML::Node items = list->second;

            for (size_t index = 0; items.IsSequence() && index < items.size(); ++index)
            {
                if (items[index].IsMap() && items[index]["id"] && items[index]["id"].Scalar() == id)
                {
                    writer.key("layout");
                    writer.node(items[index]);
                    writer.field("layout_stale", view->revision != entry.memory.revision);
                    return;
                }
            }
        }
    }
}

void viewRenderSketch(const YAML::Node &params, JsonWriter &writer)
{
    const std::filesystem::path root = projectOf(params);
    SketchPreviewOptions options;
    options.labels = flag(params, "labels", true);

    if (params["size"])
    {
        options.size = std::clamp(params["size"].as<int>(), 256, 4096);
    }

    if (params["region"])
    {
        for (size_t index = 0; index < 4; ++index)
        {
            options.region[index] = params["region"][index].as<double>();
        }
    }

    Project project;
    std::vector<ProjectIssue> issues;
    loadProject(root, project, issues);

    if (!project.has("project.yml"))
    {
        throw refusal("not_a_project", "no project in that folder",
            [issues](JsonWriter &data) { writeIssues(data, "issues", issues); });
    }

    if (!project.has("sketch.yml"))
    {
        throw refusal("bad_request", "the project has no readable sketch.yml (render-sketch draws outdoor projects)");
    }

    const Image image = renderSketch(project, options);
    const std::vector<uint8_t> png = encodePng(image);
    writer.field("width", image.width);
    writer.field("height", image.height);
    writer.field("png_base64", base64(png));
}

// --- mods (devdocs/map_studio/S6_PLAN.md item M) -------------------------------------------------------------------

std::vector<std::filesystem::path> projectsOf(const YAML::Node &params)
{
    std::vector<std::filesystem::path> projects;

    for (const YAML::Node &project : params["projects"])
    {
        projects.push_back(project.Scalar());
    }

    return projects;
}

void modPack(const YAML::Node &params, JsonWriter &writer)
{
    ModPackRequest request;
    request.assetRoot = assetRootOrRefuse("mod.pack");
    request.projects = projectsOf(params);
    request.id = params["id"].Scalar();
    request.out = params["out"].Scalar();
    request.build = flag(params, "build", true);

    for (const char *pField : {"name", "version", "author", "description"})
    {
        if (params[pField])
        {
            std::string &target = std::string(pField) == "name" ? request.name
                : std::string(pField) == "version" ? request.version
                : std::string(pField) == "author" ? request.author : request.description;
            target = params[pField].Scalar();
        }
    }

    if (params["maps"])
    {
        request.mapRange = std::array<int, 2>{params["maps"][0].as<int>(), params["maps"][1].as<int>()};
    }

    ModPackResult result;
    std::string errorMessage;

    if (!packMod(request, result, errorMessage))
    {
        for (const std::filesystem::path &project : request.projects)
        {
            errorMessage = withoutPath(errorMessage, project, "the project");
        }

        errorMessage = withoutPath(withoutPath(errorMessage, request.out, "the mods folder"), request.assetRoot,
            "the asset root");
        const bool notProject = errorMessage.find("does not read as a project") != std::string::npos;

        if (notProject)
        {
            ProjectIssue issue;
            issue.code = "project";
            issue.message = errorMessage;
            const std::vector<ProjectIssue> issues = {issue};
            throw refusal("not_a_project", errorMessage,
                [issues](JsonWriter &data) { writeIssues(data, "issues", issues); });
        }

        const bool asked = errorMessage.find("does not build") != std::string::npos
            || errorMessage.find("has no build") != std::string::npos
            || errorMessage.find("a mod's id") != std::string::npos
            || errorMessage.find("a map range") != std::string::npos
            || errorMessage.find("one project or more") != std::string::npos;
        throw refusal(asked ? "bad_request" : "failed", errorMessage, nullptr, asked ? -32000 : -32603);
    }

    writer.field("id", request.id);
    writeStrings(writer, "files", result.files);
    writer.key("maps");
    writer.beginArray();

    for (const PackedMap &map : result.maps)
    {
        writer.beginObject();
        writer.field("file", map.file);
        writer.field("world", map.world);
        writer.field("kind", map.kind);
        writer.field("project", map.project);

        if (map.number > 0)
        {
            writer.field("map_number", map.number);
        }

        writer.endObject();
    }

    writer.endArray();
    writeStrings(writer, "tables", result.tables);
    writeStrings(writer, "warnings", result.warnings);
}

void modList(const YAML::Node &params, JsonWriter &writer)
{
    writeModList(params["mods"].Scalar(), writer);
}

void modMapNumber(const YAML::Node &params, JsonWriter &writer)
{
    MapNumberRequest request;
    request.assetRoot = assetRootOrRefuse("mod.map_number");
    request.world = params["world"].Scalar();
    request.modsRoot = params["mods"] ? std::filesystem::path(params["mods"].Scalar()) : std::filesystem::path();
    request.mod = params["mod"] ? params["mod"].Scalar() : std::string();
    request.projects = projectsOf(params);

    if (!request.mod.empty() && request.modsRoot.empty())
    {
        throw refusal("bad_request", "a mod is named in its mods folder: give `mods` with `mod`");
    }

    MapNumberProposal proposal;
    std::string errorMessage;

    if (!proposeMapNumber(request, proposal, errorMessage))
    {
        throw refusal("bad_request", withoutPath(errorMessage, request.modsRoot, "the mods folder"));
    }

    writer.field("number", proposal.number);
    writer.key("range");
    writer.beginArray();
    writer.value(proposal.range[0]);
    writer.value(proposal.range[1]);
    writer.endArray();
    writer.field("from", proposal.from);
    writer.field("taken", static_cast<uint64_t>(proposal.taken.size()));
    writeStrings(writer, "warnings", proposal.warnings);
}

// --- the world view (S6_PLAN.md 2.9) --------------------------------------------------------------------------------

void worldView(const YAML::Node &params, JsonWriter &writer)
{
    const WorldGraph graph = readWorldGraph(projectsOf(params), params["world"] ? params["world"].Scalar() : "",
        session().assetRoot);
    writeWorldGraph(graph, writer);
}

using Handler = void (*)(const YAML::Node &params, JsonWriter &writer);

const std::map<std::string, Handler> &handlers()
{
    static const std::map<std::string, Handler> table = {
        {"session.hello", sessionHello},
        {"session.configure", sessionConfigure},
        {"session.release", sessionRelease},
        {"project.open", projectOpen},
        {"project.read", projectRead},
        {"project.status", projectStatusMethod},
        {"project.record", projectRecord},
        {"project.lock_prune", projectLockPrune},
        {"edit.apply", editApply},
        {"edit.history", editHistory},
        {"check.validate", checkValidate},
        {"check.things", checkThings},
        {"build.run", buildRun},
        {"view.layout", viewLayout},
        {"view.mesh", viewMesh},
        {"pins.list", pinsList},
        {"pins.add", pinsAdd},
        {"pins.claim", pinsClaim},
        {"pins.reply", pinsReply},
        {"pins.resolve", pinsResolve},
        {"pins.accept", pinsAccept},
        {"pins.reopen", pinsReopen},
        {"pins.decline", pinsDecline},
        {"pins.keep", pinsKeep},
        {"pins.import_inbox", pinsImportInbox},
        {"project.new", projectNew},
        {"project.query", projectQuery},
        {"edit.undo", editUndo},
        {"edit.redo", editRedo},
        {"check.audit", checkAudit},
        {"check.solve", checkSolve},
        {"check.flow_event", checkFlowEvent},
        {"view.render", viewRender},
        {"assets.search", assetsSearch},
        {"assets.script_reference", assetsScriptReference},
        {"session.schema", sessionSchema},
        {"build.install", buildInstall},
        {"walk.load", walkLoad},
        {"walk.place", walkPlace},
        {"walk.step", walkStep},
        {"walk.replay", walkReplay},
        {"walk.toggle", walkToggle},
        {"compare.run", compareRun},
        {"pins.tour", pinsTour},
        {"view.original_mesh", viewOriginalMesh},
        {"check.metrics", checkMetrics},
        {"check.probe", checkProbe},
        {"project.import", projectImport},
        {"project.fmt", projectFmt},
        {"view.render_sketch", viewRenderSketch},
        {"edit.revert", editRevertEntry},
        {"project.protect", projectProtect},
        {"project.migrate", projectMigrate},
        {"project.resolve", projectResolve},
        {"view.layout_at", viewLayoutAt},
        {"view.terrain_query", viewTerrainQuery},
        {"view.overlay", viewOverlay},
        {"mod.pack", modPack},
        {"mod.list", modList},
        {"mod.map_number", modMapNumber},
        {"world.view", worldView},
    };
    return table;
}

std::string errorText(const RpcRefusal &failure)
{
    JsonWriter writer;
    writer.beginObject();
    writer.key("error");
    writer.beginObject();
    writer.field("code", failure.code);
    writer.field("message", failure.message);
    writer.key("data");
    writer.beginObject();
    writer.field("kind", failure.kind);

    if (failure.data)
    {
        failure.data(writer);
    }

    writer.endObject();
    writer.endObject();
    writer.endObject();
    return writer.take();
}
}

bool isRpcMethod(const std::string &method)
{
    return catalogue().contains(method);
}

void rpcIdle()
{
    session().service.idle();
}

std::vector<std::string> rpcMethodNames()
{
    std::vector<std::string> names;

    for (const std::pair<const std::string, MethodEntry> &method : catalogue())
    {
        names.push_back(method.first);
    }

    return names;
}

std::string callRpcMethod(const std::string &method, const YAML::Node &givenParams)
{
    const std::map<std::string, MethodEntry>::const_iterator entry = catalogue().find(method);

    if (entry == catalogue().end())
    {
        return errorText(refusal("unknown_method", "unknown method '" + method + "'", nullptr, -32601));
    }

    // Absent params are an empty object.
    const YAML::Node params = givenParams.IsDefined() && !givenParams.IsNull() ? givenParams
        : YAML::Node(YAML::NodeType::Map);
    const std::vector<SchemaIssue> invalid = rpcSchemas().validateAt(params, entry->second.reference + "/params");

    if (!invalid.empty())
    {
        return errorText(refusal("invalid_params",
            "the params do not match " + method + ": " + (invalid.front().path.empty() ? "" : invalid.front().path + ": ")
                + invalid.front().message,
            [invalid](JsonWriter &data)
            {
                data.key("issues");
                data.beginArray();

                for (const SchemaIssue &issue : invalid)
                {
                    data.beginObject();
                    data.field("path", issue.path);
                    data.field("message", issue.message);
                    data.endObject();
                }

                data.endArray();
            },
            -32602));
    }

    const std::map<std::string, Handler>::const_iterator handler = handlers().find(method);

    if (handler == handlers().end())
    {
        return errorText(refusal("failed", "the catalogue names " + method + " but this core has no handler for it",
            nullptr, -32603));
    }

    try
    {
        JsonWriter writer;
        writer.beginObject();
        writer.key("result");
        writer.beginObject();
        handler->second(params, writer);
        writer.endObject();
        writer.endObject();
        return writer.take();
    }
    catch (const RpcRefusal &failure)
    {
        return errorText(failure);
    }
    catch (const std::exception &exception)
    {
        return errorText(refusal("failed", exception.what(), nullptr, -32603));
    }
}

std::string callRpcMethod(const std::string &method, const std::string &paramsJson)
{
    YAML::Node params;

    try
    {
        params = paramsJson.empty() ? YAML::Node(YAML::NodeType::Map) : YAML::Load(paramsJson);
    }
    catch (const YAML::Exception &exception)
    {
        return errorText(refusal("invalid_params", std::string("the params are not JSON: ") + exception.what(),
            [](JsonWriter &data)
            {
                data.key("issues");
                data.beginArray();
                data.endArray();
            },
            -32602));
    }

    return callRpcMethod(method, params);
}
}
