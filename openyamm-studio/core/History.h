#pragma once

#include <yaml-cpp/yaml.h>

#include <filesystem>
#include <map>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Studio
{
// The storage of a project's source history (S5_BROWSER_EDITOR.md 2.7): append-only entries in
// <project>/.oymap/history/<sequence>/entry.yml, and each version of a file once, by its hash, compressed with zstd in
// .oymap/history/blobs/<hash>.zst. An entry names the blobs of the files it changed, before and after. Entries are
// never marked undone or cut off: an undo is a new entry that reverts an earlier one (core/Ops.h). The one exception
// is merging (`merge_key`): a repeated edit is folded into the latest entry. The last 1 000 entries are kept; blobs
// no kept entry names are dropped when entries are.
//
// Entries written before S5b1 keep whole copies in before/ and after/ beside entry.yml and are read as they are.

// The versions of the changed source files: a file's text, or none when it did not exist.
using FileVersions = std::map<std::string, std::optional<std::string>>;

struct HistoryHead
{
    // The source revision the tool last saw.
    std::string revision;
    std::string scheme;
    // The newest entry's sequence (0: none), and the oldest one kept.
    int count = 0;
    int first = 1;
    // "append-only-1"; empty in a head of the cursor history (before S5b1).
    std::string history;
    // The cursor of a cursor history (entries above it were undone).
    int cursor = 0;
    // The entry that set the hand-edit mark in this history (-1: not in the kept history), and the mark's revision
    // (core/Ops.h HandMark): whether the kept history reaches back to the mark is known without reading the entries.
    int markSequence = 0;
    std::string markRevision;
};

HistoryHead readHistoryHead(const std::filesystem::path &projectRoot);
bool writeHistoryHead(const std::filesystem::path &projectRoot, const HistoryHead &head, std::string &errorMessage);

extern const char *const HistoryScheme;

// The entries kept at most; older ones are dropped with the blobs only they named.
constexpr int HistoryEntriesKept = 1000;

struct HistoryRename
{
    // An id (`room:hall` to `room:great_hall`), or a sub-object's address (`room:hall/pillars/pillar2` to
    // `room:hall/pillars/big`).
    std::string from;
    std::string to;
};

struct NewHistoryEntry
{
    // "transaction", "outside", "revert", "migration".
    std::string kind;
    std::string author;
    std::string label;
    std::string revisionBefore;
    std::string revisionAfter;
    std::vector<std::string> changes;
    YAML::Node operations;
    FileVersions before;
    FileVersions after;
    // A revert entry: the entry it reverts and why ("undo", "redo", "revert").
    int reverts = 0;
    std::string revertKind;
    std::string mergeKey;
    // The renames the entry made, in order (a revert runs them backwards).
    std::vector<HistoryRename> renames;
    // An error notice (a marked project rewritten from outside: objects a person changed last that it replaced).
    std::vector<std::string> notice;
    // Objects (file#id) the entry changed, for the hand-edit mark's notices and the rebase.
    std::vector<std::string> objects;
};

// Appends an entry with the next sequence, writes its blobs, and brings `last/` and the head up to it.
bool appendHistoryEntry(
    const std::filesystem::path &projectRoot,
    HistoryHead &head,
    const NewHistoryEntry &entry,
    std::string &errorMessage);

// Folds `entry` into the latest entry when that one has the same author and merge key, is a transaction, is not
// reverted, and was written less than `windowSeconds` ago: its before stays, its after, revision, changes and
// operations become the merged ones and `merged` counts the folds. `merged` says whether it did.
bool mergeIntoLatestEntry(
    const std::filesystem::path &projectRoot,
    HistoryHead &head,
    const NewHistoryEntry &entry,
    int windowSeconds,
    bool &merged,
    std::string &errorMessage);

struct StoredHistoryEntry
{
    int sequence = 0;
    YAML::Node node;
    // Only when read with texts.
    FileVersions before;
    FileVersions after;
};

bool readHistoryEntry(
    const std::filesystem::path &projectRoot,
    int sequence,
    bool withTexts,
    StoredHistoryEntry &entry,
    std::string &errorMessage);

// The entry folder of a sequence (`.oymap/history/0012`).
std::filesystem::path historyEntryRoot(const std::filesystem::path &projectRoot, int sequence);

// A blob's text by its hash.
bool readHistoryBlob(const std::filesystem::path &projectRoot, const std::string &hash, std::string &text);

// The files the tool last saw (`.oymap/last/`).
std::map<std::string, std::string> lastSeenTexts(const std::filesystem::path &projectRoot);

// Turns a cursor history into an append-only one: entries above the cursor (undone, waiting for a redo) are dropped,
// since an append-only history has no such state, and the step is logged in migrations.log.
bool migrateCursorHistory(const std::filesystem::path &projectRoot, HistoryHead &head, std::string &errorMessage);

// zstd at the level the history uses.
std::string compressText(const std::string &text);
bool decompressText(const std::string &compressed, std::string &text);
}
