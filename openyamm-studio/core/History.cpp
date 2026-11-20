#include "core/History.h"

#include "core/CanonicalYaml.h"
#include "core/Ops.h"
#include "core/Project.h"

#include <zstd.h>

#include <chrono>
#include <cstdio>
#include <ctime>
#include <set>

namespace OpenYAMM::Studio
{
namespace
{
YAML::Node childOf(const YAML::Node &node, const std::string &key)
{
    return node.IsDefined() && node.IsMap() ? node[key] : YAML::Node(YAML::NodeType::Undefined);
}

std::string textOf(const YAML::Node &node, const std::string &key)
{
    const YAML::Node child = childOf(node, key);
    return child.IsDefined() && child.IsScalar() ? child.Scalar() : std::string();
}

YAML::Node quoted(const std::string &text)
{
    YAML::Node node(text);
    node.SetTag("!");
    return node;
}

std::filesystem::path historyRoot(const std::filesystem::path &projectRoot)
{
    return projectRoot / ".oymap" / "history";
}

std::filesystem::path blobPath(const std::filesystem::path &projectRoot, const std::string &hash)
{
    return historyRoot(projectRoot) / "blobs" / (hash + ".zst");
}

constexpr const char *NoFile = "none";

std::string localTimestamp(long long &epochSeconds)
{
    const std::chrono::system_clock::time_point now = std::chrono::system_clock::now();
    epochSeconds = std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch()).count();
    const std::time_t time = std::chrono::system_clock::to_time_t(now);
    const std::tm *pLocal = std::localtime(&time);
    char text[32] = {};

    if (pLocal != nullptr)
    {
        std::strftime(text, sizeof(text), "%Y-%m-%dT%H:%M:%S", pLocal);
    }

    return text;
}

// Writes a file version as a blob (once: a blob that exists already holds the same text), returning its hash.
bool storeBlob(const std::filesystem::path &projectRoot, const std::optional<std::string> &text, std::string &hash,
    std::string &errorMessage)
{
    if (!text)
    {
        hash = NoFile;
        return true;
    }

    hash = contentHash128(*text);
    const std::filesystem::path path = blobPath(projectRoot, hash);
    std::error_code error;

    if (std::filesystem::exists(path, error))
    {
        return true;
    }

    std::filesystem::create_directories(path.parent_path(), error);
    const std::string compressed = compressText(*text);
    return writeBinaryFileAtomically(path, std::vector<uint8_t>(compressed.begin(), compressed.end()), errorMessage);
}

bool writeFileSet(const std::filesystem::path &folder, const FileVersions &versions, std::string &errorMessage)
{
    for (const std::pair<const std::string, std::optional<std::string>> &file : versions)
    {
        if (file.second)
        {
            if (!writeTextFileAtomically(folder / file.first, *file.second, errorMessage))
            {
                return false;
            }
        }
        else
        {
            std::error_code error;
            std::filesystem::remove(folder / file.first, error);
        }
    }

    return true;
}

// The names of the files an entry changed (before and after differ).
std::set<std::string> changedNames(const FileVersions &before, const FileVersions &after)
{
    std::set<std::string> names;

    for (const FileVersions *pVersions : {&before, &after})
    {
        for (const std::pair<const std::string, std::optional<std::string>> &file : *pVersions)
        {
            const FileVersions &other = pVersions == &before ? after : before;
            const FileVersions::const_iterator found = other.find(file.first);
            const std::optional<std::string> otherText = found != other.end() ? found->second : std::nullopt;

            if (file.second != otherText)
            {
                names.insert(file.first);
            }
        }
    }

    return names;
}

YAML::Node entryNode(const NewHistoryEntry &entry, int sequence, const std::map<std::string,
    std::pair<std::string, std::string>> &blobs, const std::string &time, long long epoch)
{
    YAML::Node node(YAML::NodeType::Map);
    node["sequence"] = sequence;
    node["kind"] = entry.kind;
    node["author"] = entry.author;

    if (!entry.label.empty())
    {
        node["label"] = quoted(entry.label);
    }

    node["revision_before"] = quoted(entry.revisionBefore);
    node["revision_after"] = quoted(entry.revisionAfter);
    node["time"] = quoted(time);
    node["epoch"] = epoch;

    for (const std::string &change : entry.changes)
    {
        node["changes"].push_back(quoted(change));
    }

    for (const std::pair<const std::string, std::pair<std::string, std::string>> &blob : blobs)
    {
        node["files"].push_back(blob.first);
        YAML::Node pair(YAML::NodeType::Map);
        pair["before"] = quoted(blob.second.first);
        pair["after"] = quoted(blob.second.second);
        node["blobs"][blob.first] = pair;
    }

    if (entry.operations.IsDefined() && entry.operations.IsSequence())
    {
        node["operations"] = YAML::Clone(entry.operations);
    }

    if (entry.reverts > 0)
    {
        node["reverts"] = entry.reverts;
        node["revert_kind"] = entry.revertKind.empty() ? std::string("revert") : entry.revertKind;
    }

    if (!entry.mergeKey.empty())
    {
        node["merge_key"] = quoted(entry.mergeKey);
    }

    for (const HistoryRename &rename : entry.renames)
    {
        YAML::Node pair(YAML::NodeType::Map);
        pair["from"] = quoted(rename.from);
        pair["to"] = quoted(rename.to);
        node["renames"].push_back(pair);
    }

    for (const std::string &line : entry.notice)
    {
        node["notice"].push_back(quoted(line));
    }

    for (const std::string &object : entry.objects)
    {
        node["objects"].push_back(quoted(object));
    }

    return node;
}

// Drops the oldest entries past the kept number, and the blobs no kept entry names.
bool pruneHistory(const std::filesystem::path &projectRoot, HistoryHead &head, std::string &errorMessage)
{
    // Pruned in batches, so that most appends read nothing.
    if (head.count - head.first + 1 <= HistoryEntriesKept + HistoryEntriesKept / 10)
    {
        return true;
    }

    const int newFirst = head.count - HistoryEntriesKept + 1;
    std::error_code error;

    for (int sequence = head.first; sequence < newFirst; ++sequence)
    {
        std::filesystem::remove_all(historyEntryRoot(projectRoot, sequence), error);
    }

    head.first = newFirst;
    std::set<std::string> named;

    for (int sequence = head.first; sequence <= head.count; ++sequence)
    {
        std::string text;

        if (!readTextFile(historyEntryRoot(projectRoot, sequence) / "entry.yml", text))
        {
            continue;
        }

        const YAML::Node blobs = childOf(YAML::Load(text), "blobs");

        for (YAML::const_iterator file = blobs.begin(); file != blobs.end(); ++file)
        {
            named.insert(textOf(file->second, "before"));
            named.insert(textOf(file->second, "after"));
        }
    }

    for (std::filesystem::directory_iterator blob(historyRoot(projectRoot) / "blobs", error), end;
         !error && blob != end; blob.increment(error))
    {
        if (!named.contains(blob->path().stem().string()))
        {
            std::filesystem::remove(blob->path(), error);
            error.clear();
        }
    }

    return writeHistoryHead(projectRoot, head, errorMessage);
}
}

const char *const HistoryScheme = "append-only-1";

std::string compressText(const std::string &text)
{
    std::string compressed(ZSTD_compressBound(text.size()), '\0');
    const size_t size = ZSTD_compress(compressed.data(), compressed.size(), text.data(), text.size(), 3);

    if (ZSTD_isError(size))
    {
        return std::string();
    }

    compressed.resize(size);
    return compressed;
}

bool decompressText(const std::string &compressed, std::string &text)
{
    const unsigned long long size = ZSTD_getFrameContentSize(compressed.data(), compressed.size());

    if (size == ZSTD_CONTENTSIZE_ERROR || size == ZSTD_CONTENTSIZE_UNKNOWN)
    {
        return false;
    }

    text.assign(static_cast<size_t>(size), '\0');
    const size_t written = ZSTD_decompress(text.data(), text.size(), compressed.data(), compressed.size());
    return !ZSTD_isError(written) && written == size;
}

std::filesystem::path historyEntryRoot(const std::filesystem::path &projectRoot, int sequence)
{
    char name[16];
    std::snprintf(name, sizeof(name), "%04d", sequence);
    return historyRoot(projectRoot) / name;
}

HistoryHead readHistoryHead(const std::filesystem::path &projectRoot)
{
    HistoryHead head;
    std::string text;

    if (readTextFile(projectRoot / ".oymap" / "head.yml", text))
    {
        try
        {
            const YAML::Node node = YAML::Load(text);
            head.revision = textOf(node, "revision");
            head.scheme = textOf(node, "scheme");
            head.history = textOf(node, "history");
            head.count = childOf(node, "count").IsDefined() ? node["count"].as<int>() : 0;
            head.cursor = childOf(node, "cursor").IsDefined() ? node["cursor"].as<int>() : head.count;
            head.first = childOf(node, "first").IsDefined() ? node["first"].as<int>() : 1;
            head.markSequence = childOf(node, "mark_sequence").IsDefined() ? node["mark_sequence"].as<int>() : 0;
            head.markRevision = textOf(node, "mark_revision");
        }
        catch (const YAML::Exception &)
        {
        }
    }

    return head;
}

bool writeHistoryHead(const std::filesystem::path &projectRoot, const HistoryHead &head, std::string &errorMessage)
{
    YAML::Node node(YAML::NodeType::Map);
    node["revision"] = quoted(head.revision);
    node["scheme"] = head.scheme.empty() ? std::string(RevisionScheme) : head.scheme;
    node["history"] = HistoryScheme;
    node["count"] = head.count;
    node["first"] = head.first;

    if (!head.markRevision.empty())
    {
        node["mark_sequence"] = head.markSequence;
        node["mark_revision"] = quoted(head.markRevision);
    }

    std::error_code error;
    std::filesystem::create_directories(projectRoot / ".oymap", error);
    return writeTextFileAtomically(projectRoot / ".oymap" / "head.yml", writeCanonicalYaml(node), errorMessage);
}

bool migrateCursorHistory(const std::filesystem::path &projectRoot, HistoryHead &head, std::string &errorMessage)
{
    if (head.history == HistoryScheme)
    {
        return true;
    }

    std::error_code error;
    const int dropped = head.count - head.cursor;

    for (int sequence = head.cursor + 1; sequence <= head.count; ++sequence)
    {
        std::filesystem::remove_all(historyEntryRoot(projectRoot, sequence), error);
    }

    head.count = head.cursor;
    head.history = HistoryScheme;
    long long epoch = 0;
    std::string log;
    readTextFile(projectRoot / ".oymap" / "migrations.log", log);
    log += localTimestamp(epoch) + " the history became append-only (" + std::string(HistoryScheme)
        + "): undo and redo are entries that revert entries; " + std::to_string(dropped)
        + " entr" + (dropped == 1 ? "y" : "ies") + " undone in the old history (waiting for a redo) dropped\n";
    return writeTextFileAtomically(projectRoot / ".oymap" / "migrations.log", log, errorMessage)
        && writeHistoryHead(projectRoot, head, errorMessage);
}

bool appendHistoryEntry(
    const std::filesystem::path &projectRoot,
    HistoryHead &head,
    const NewHistoryEntry &entry,
    std::string &errorMessage)
{
    const int sequence = head.count + 1;
    const std::set<std::string> names = changedNames(entry.before, entry.after);
    std::map<std::string, std::pair<std::string, std::string>> blobs;
    FileVersions after;

    for (const std::string &name : names)
    {
        const FileVersions::const_iterator before = entry.before.find(name);
        const FileVersions::const_iterator now = entry.after.find(name);
        std::pair<std::string, std::string> &pair = blobs[name];

        if (!storeBlob(projectRoot, before != entry.before.end() ? before->second : std::nullopt, pair.first,
                errorMessage)
            || !storeBlob(projectRoot, now != entry.after.end() ? now->second : std::nullopt, pair.second,
                errorMessage))
        {
            return false;
        }

        after[name] = now != entry.after.end() ? now->second : std::nullopt;
    }

    long long epoch = 0;
    const std::string time = localTimestamp(epoch);
    const YAML::Node node = entryNode(entry, sequence, blobs, time, epoch);
    std::error_code error;
    std::filesystem::remove_all(historyEntryRoot(projectRoot, sequence), error);

    if (!writeTextFileAtomically(historyEntryRoot(projectRoot, sequence) / "entry.yml", writeCanonicalYaml(node),
            errorMessage))
    {
        return false;
    }

    head.count = sequence;
    head.cursor = sequence;
    head.revision = entry.revisionAfter;
    head.history = HistoryScheme;
    return writeFileSet(projectRoot / ".oymap" / "last", after, errorMessage)
        && writeHistoryHead(projectRoot, head, errorMessage) && pruneHistory(projectRoot, head, errorMessage);
}

bool mergeIntoLatestEntry(
    const std::filesystem::path &projectRoot,
    HistoryHead &head,
    const NewHistoryEntry &entry,
    int windowSeconds,
    bool &merged,
    std::string &errorMessage)
{
    merged = false;

    if (entry.mergeKey.empty() || head.count < head.first || !entry.renames.empty())
    {
        return true;
    }

    StoredHistoryEntry latest;

    if (!readHistoryEntry(projectRoot, head.count, true, latest, errorMessage))
    {
        errorMessage.clear();
        return true;
    }

    long long now = 0;
    localTimestamp(now);
    const long long then = childOf(latest.node, "epoch").IsDefined() ? latest.node["epoch"].as<long long>() : 0;

    if (textOf(latest.node, "merge_key") != entry.mergeKey || textOf(latest.node, "author") != entry.author
        || textOf(latest.node, "kind") != "transaction" || now - then > windowSeconds || now < then
        || textOf(latest.node, "revision_after") != entry.revisionBefore || childOf(latest.node, "renames").IsDefined())
    {
        return true;
    }

    // The merged entry: the latest one's before (files it did not change are taken from this entry's before), this
    // entry's after.
    NewHistoryEntry folded = entry;
    folded.revisionBefore = textOf(latest.node, "revision_before");
    folded.label = textOf(latest.node, "label").empty() ? entry.label : textOf(latest.node, "label");
    folded.before = latest.before;

    for (const std::pair<const std::string, std::optional<std::string>> &file : entry.before)
    {
        folded.before.emplace(file.first, file.second);
    }

    folded.after = latest.after;

    for (const std::pair<const std::string, std::optional<std::string>> &file : entry.after)
    {
        folded.after[file.first] = file.second;
    }

    YAML::Node operations(YAML::NodeType::Sequence);
    const YAML::Node earlier = childOf(latest.node, "operations");

    for (const YAML::Node *pList : {&earlier, &entry.operations})
    {
        if (pList->IsDefined() && pList->IsSequence())
        {
            for (const YAML::Node &operation : *pList)
            {
                operations.push_back(YAML::Clone(operation));
            }
        }
    }

    // Rebound, not assigned: the folded entry's node shares its data with the caller's operations.
    folded.operations.reset(operations);
    std::set<std::string> objects(folded.objects.begin(), folded.objects.end());

    for (const YAML::Node &object : childOf(latest.node, "objects"))
    {
        objects.insert(object.Scalar());
    }

    folded.objects.assign(objects.begin(), objects.end());
    std::set<std::string> names = changedNames(folded.before, folded.after);
    std::map<std::string, std::pair<std::string, std::string>> blobs;
    FileVersions after;

    for (const std::string &name : names)
    {
        std::pair<std::string, std::string> &pair = blobs[name];

        if (!storeBlob(projectRoot, folded.before[name], pair.first, errorMessage)
            || !storeBlob(projectRoot, folded.after[name], pair.second, errorMessage))
        {
            return false;
        }

        after[name] = folded.after[name];
    }

    long long epoch = 0;
    const std::string time = localTimestamp(epoch);
    YAML::Node node = entryNode(folded, head.count, blobs, time, epoch);
    node["merged"] = (childOf(latest.node, "merged").IsDefined() ? latest.node["merged"].as<int>() : 1) + 1;

    if (!writeTextFileAtomically(historyEntryRoot(projectRoot, head.count) / "entry.yml", writeCanonicalYaml(node),
            errorMessage))
    {
        return false;
    }

    head.revision = entry.revisionAfter;
    merged = true;
    return writeFileSet(projectRoot / ".oymap" / "last", after, errorMessage)
        && writeHistoryHead(projectRoot, head, errorMessage);
}

bool readHistoryBlob(const std::filesystem::path &projectRoot, const std::string &hash, std::string &text)
{
    std::string compressed;
    return readTextFile(blobPath(projectRoot, hash), compressed) && decompressText(compressed, text);
}

bool readHistoryEntry(
    const std::filesystem::path &projectRoot,
    int sequence,
    bool withTexts,
    StoredHistoryEntry &entry,
    std::string &errorMessage)
{
    entry = {};
    entry.sequence = sequence;
    const std::filesystem::path root = historyEntryRoot(projectRoot, sequence);
    std::string text;

    if (!readTextFile(root / "entry.yml", text))
    {
        errorMessage = "history entry " + std::to_string(sequence) + " is missing";
        return false;
    }

    try
    {
        entry.node = YAML::Load(text);
    }
    catch (const YAML::Exception &)
    {
        errorMessage = "history entry " + std::to_string(sequence) + " does not parse";
        return false;
    }

    if (!withTexts)
    {
        return true;
    }

    const YAML::Node blobs = childOf(entry.node, "blobs");

    if (blobs.IsDefined() && blobs.IsMap())
    {
        for (YAML::const_iterator file = blobs.begin(); file != blobs.end(); ++file)
        {
            for (const bool before : {true, false})
            {
                const std::string hash = textOf(file->second, before ? "before" : "after");
                std::optional<std::string> version;

                if (hash != NoFile)
                {
                    std::string blob;

                    if (!readHistoryBlob(projectRoot, hash, blob))
                    {
                        errorMessage = "history entry " + std::to_string(sequence) + ": the blob " + hash
                            + " is missing";
                        return false;
                    }

                    version = blob;
                }

                (before ? entry.before : entry.after)[file->first.Scalar()] = version;
            }
        }

        return true;
    }

    // An entry written before S5b1: whole copies beside it.
    for (const YAML::Node &name : childOf(entry.node, "files"))
    {
        for (const bool before : {true, false})
        {
            std::string version;
            const bool exists = readTextFile(root / (before ? "before" : "after") / name.Scalar(), version);
            (before ? entry.before : entry.after)[name.Scalar()] =
                exists ? std::optional<std::string>(version) : std::nullopt;
        }
    }

    return true;
}

std::map<std::string, std::string> lastSeenTexts(const std::filesystem::path &projectRoot)
{
    std::map<std::string, std::string> texts;

    for (const ProjectFileKind &kind : projectFileKinds())
    {
        std::string text;

        if (kind.fileClass == ProjectFileClass::Source
            && readTextFile(projectRoot / ".oymap" / "last" / kind.pName, text))
        {
            texts[kind.pName] = text;
        }
    }

    return texts;
}
}
