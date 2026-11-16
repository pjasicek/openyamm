#pragma once

#include "core/Project.h"

#include <yaml-cpp/yaml.h>

#include <filesystem>
#include <map>
#include <set>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// Documents, revisions, operations and history (PLAN.md section 5; the three classes of file of
// S5_BROWSER_EDITOR.md 2.4.1). The project's files are the truth; everything here reads them, changes them through
// checked operations, and keeps what is needed to say what changed and to go back. The same code serves
// `oymap edit`, `oymap serve` and, later, the hosted page.
//
// Only the source files (project.yml, plan.yml, sketch.yml, rooms.yml, objects.yml, wiring.yml, atmosphere.yml) make
// the revision, the history and undo. ids.lock.yml is a record: builds, `import` and `oymap lock prune` write it,
// nothing undoes it, and each change is a line of .oymap/lock.log. review/pins.yml is the review document, with its
// own counter and log (core/Pins.h).
//
// On disk, in <project>/.oymap/ (git-ignored by its own .gitignore):
//   head.yml            the source revision the tool last saw, its scheme, and the history cursor
//   last/<file>         the source files at that revision (to notice and show edits made outside the tool)
//   history/<seq>/      one entry per change: entry.yml (what, by whom, by which operations), before/ and after/
//                       copies of the source files it changed
//   lock.log            one JSON line per change of ids.lock.yml (by a build, a prune, or found from outside)
//   lock_seen           the lock hash the tool last saw (a different one on disk is a change from outside)
//   migrations.log      what a newer core changed in this folder (the history head re-keyed, ...)
//   pins/               the pins document's log and pictures (core/Pins.h)

// A project's source revision: the first 128 bits of a SHA-256 over the canonical text of its source files (32 hex
// digits). Needs no running process and no counter, so any two readers agree on it. Pins and the id lock do not
// change it.
std::string projectRevision(const Project &project);

// The name of the revision's scheme, written into head.yml; a head of another scheme is re-keyed on first open.
extern const char *const RevisionScheme;

struct TransactionOptions
{
    bool dryRun = false;
    // Apply only when the project is at this revision (empty: at whatever revision it is).
    std::string expectRevision;
    // Apply even when the change introduces validation issues that were not there before.
    bool allowNewIssues = false;
    std::filesystem::path assetRoot;
    // Who makes the change ("user", "agent:<name>") and a short label, kept in the history entry.
    std::string author = "agent";
    std::string label;
    // A repeated edit (`"drag door:gate speed"`): folded into the latest history entry when that one has the same
    // author and merge key, is the latest and is a few seconds old (S5_BROWSER_EDITOR.md 2.6 item 6).
    std::string mergeKey;
    // With `expectRevision` stale: apply on the current revision when nothing the operations touch changed since
    // (or their `test` steps still hold), instead of refusing (2.7).
    bool rebase = false;
};

// The hand-edit mark of a project (S5_BROWSER_EDITOR.md 2.8): project.yml `edited_by_hand: {since, revision}`,
// written by the core at the first source transaction whose author is a person (`user`), or by a person's "protect
// this project" (`oymap protect`). `revision` is the source revision before the marking transaction: a diff from it
// shows all the hand work.
struct HandMark
{
    bool marked = false;
    std::string since;
    std::string revision;
    // Set by this transaction.
    bool setNow = false;
    // Whether the kept history reaches back to the mark (a fresh clone or an unpacked zip has none of it): where it
    // does not, objects changed by hand before then are not known.
    bool historyKnown = true;
    // The oldest time the kept history knows, when it does not reach the mark.
    std::string knownFrom;
};

extern const char *const HandEditedMessage;

// Why a transaction was not applied (the request list's error kinds).
enum class TransactionRefusal
{
    None,
    NotAProject,
    Locked,
    StaleRevision,
    BadOperation,
    NewIssues,
    // An undo or redo with nothing to take, or a revert of an entry that is not there.
    NothingToRevert,
    Failed,
};

struct TransactionResult
{
    bool applied = false;
    std::string revisionBefore;
    std::string revisionAfter;
    // The semantic diff: "objects.yml: added door:gate", "wiring.yml: evt:lever changed opens, text".
    std::vector<std::string> changes;
    // Operations that could not be applied, with the reason and how to fix the call.
    std::vector<std::string> errors;
    // Validation issues the change introduces and removes (the check delta).
    std::vector<ProjectIssue> newIssues;
    std::vector<ProjectIssue> fixedIssues;
    // Set when an edit made outside the tool was found and recorded before this transaction.
    std::vector<std::string> outsideChanges;
    TransactionRefusal refusal = TransactionRefusal::None;
    // For BadOperation: the operation's place in the list, and a patch step's place in its patch (or -1).
    int failedOperation = -1;
    int failedStep = -1;
    // The canonical text of each source file the transaction changes, as it is (or would be) after it.
    std::map<std::string, std::string> filesAfter;
    // Ids the core gave to added objects without one ("objects.yml#door:door_3"), and keys it wrote for sub-objects
    // without one ("room:hall/pillars/pillar3"), in the order made.
    std::vector<std::string> idsAllocated;
    std::vector<std::string> keysAllocated;
    // Things worth knowing that do not stop the transaction (a `lua` text naming a renamed id).
    std::vector<std::string> notes;
    // The history entry written (0: none), and whether it was folded into the latest one (merge_key).
    int sequence = 0;
    bool merged = false;
    // A rebase: the entries since `expectRevision` it applied over. A refused rebase: the objects (file#id) the
    // operations touch that changed since.
    std::vector<int> rebasedOver;
    std::vector<std::string> clashes;
    // A revert: objects changed since the reverted entry, left alone (not `force`).
    std::vector<std::string> conflicts;
    // The project's hand-edit mark, and the objects a person changed last that this transaction changes (told to
    // agents: as far as the kept history shows).
    HandMark mark;
    std::vector<std::string> handObjects;
    // The outside entry recorded before this transaction (0: none), and its notice: in a marked project, the objects
    // a person changed last that the outside change replaced, and keys it dropped.
    int outsideSequence = 0;
    std::vector<std::string> outsideNotice;
};

// Applies a batch of operations as one transaction. `operations` is a list of maps:
//   {op: add, to: doors, value: {id: door:gate, opening: open:a_b}}      (or op: door.add, value: {...}; without
//                                      an `id` the core gives one, `<kind>:<room or kind>_<n>`: ids_allocated)
//   {op: replace, id: door:gate, value: {...}}                           (the whole object, its id kept)
//   {op: rename, from: room:hall, to: room:great_hall}                   (every reference, the lock and the pins
//                                                                         follow; or {op: rename, id: room:hall,
//                                                                         path: /pillars/pillar2, to: big} for a key)
//   {op: replace_file, file: rooms.yml, text: "..."}                     (a whole file)
//   {op: set, id: door:gate, fields: {speed: 64, notes: null}}           (null removes a field)
//   {op: remove, id: door:gate}
//   {op: set, id: room:entry, file: rooms.yml, fields: {...}}            (`file` on set and remove: ids are unique
//                                                                         per file, and an id in more than one file
//                                                                         needs it; add checks only its own file)
//   {op: set_value, file: project.yml, path: map_stats.treasure_level, value: 2}
//   {op: patch, id: room:hall, patch: [{op: replace, path: /outline/2, value: [0, 512]}]}   (JSON Patch, RFC 6902;
//                                      a segment into a keyed list (`x-key`, core/Keys.h) is the item's key, into a
//                                      list of maps with ids an id; `file:` instead of `id:`)
// `to` names a collection (doors, lights, switches, chests, spawns, decorations, exits, events, rooms, openings,
// themes, spaces, links, entrances, goals, keys, points_of_interest, landmarks, set_pieces, states, neighbours).
// Only source files are changed: pins through core/Pins.h, the lock by builds and `oymap lock prune` (and a rename,
// which moves the renamed entries with their numbers). Nothing is written unless every operation applies and (unless
// allowed) no new error appears. The files the transaction changes are written in canonical form, with the keys of
// format 1 (core/Keys.h); a person's first change marks the project as edited by hand (HandMark).
bool applyTransaction(
    const std::filesystem::path &projectRoot,
    const YAML::Node &operations,
    const TransactionOptions &options,
    TransactionResult &result);

// What a long-lived process (core/Service.h) keeps of a project between transactions, so that an edit reads no file
// it already knows (S5_BROWSER_EDITOR.md 2.4.3). The caller brings it up to the files before each transaction.
struct ProjectMemory
{
    // The project as on disk: each file's bytes (`text`) and its parsed tree.
    Project project;
    // The canonical text of each source file of `project`, and the source revision they make.
    std::map<std::string, std::string> canonical;
    std::string revision;
    std::string lockHash;
    // The source revision and lock hash at which this process last brought the history head up to the files
    // (syncOutsideEdits); empty: not yet.
    std::string headRevision;
    std::string headLockHash;
};

// The checks of a transaction for a process that keeps them (core/Service.h): the issues of the project as it is,
// and of the edited project, given the files the edit changed.
class TransactionChecks
{
public:
    virtual ~TransactionChecks() = default;
    virtual std::vector<ProjectIssue> before() = 0;
    virtual std::vector<ProjectIssue> after(const Project &edited, const std::set<std::string> &changed) = 0;
};

// applyTransaction on a project kept in memory: the same refusals, results, files written and history entry, but
// the files are not read again, the operations change copies of the touched trees only, the edited trees are checked
// as they are (their canonical text is written, not read back), and the checks come from `checks`. The caller holds
// the project's write lock and has brought `memory` up to the files; after a written edit `memory` is the project
// after it, with the edited trees standing in it. `changedFiles` names the files whose canonical text changed.
bool applyTransactionInMemory(
    const std::filesystem::path &projectRoot,
    ProjectMemory &memory,
    TransactionChecks &checks,
    const YAML::Node &operations,
    const TransactionOptions &options,
    TransactionResult &result,
    std::set<std::string> &changedFiles);

// The source revision of canonical texts by file name (only source files count), as projectRevision gives it.
std::string revisionOfCanonicalTexts(const std::map<std::string, std::string> &canonicalTexts);

struct HistoryEntry
{
    int sequence = 0;
    // "transaction", "outside" (an edit made with another tool, found on the next read), "revert" (an undo, a redo
    // or a revert of a chosen entry), "migration"; "build" in histories written before the lock left the history.
    std::string kind;
    // "user", "agent:<name>"; "outside" for an edit found on disk that nobody has recorded (`oymap record`).
    std::string author;
    std::string label;
    std::string revisionBefore;
    std::string revisionAfter;
    std::vector<std::string> changes;
    // Reverted by a later revert entry that is itself in effect (an undone entry).
    bool undone = false;
    // When the entry was written (local time); empty in entries written before S5a3.
    std::string time;
    // The entry a revert entry reverts (S5b1, D4), and why: "undo", "redo", "revert"; 0 and empty for others.
    int reverts = 0;
    std::string revertKind;
    std::string mergeKey;
    // How many edits were folded into it (merge_key); 1 for an entry made once.
    int merged = 1;
    // The objects it changed ("rooms.yml#room:hall", "project.yml#/map_stats").
    std::vector<std::string> objects;
    std::vector<std::string> notice;
};

struct ProjectStatus
{
    std::string revision;
    std::string lockHash;
    std::vector<std::string> outsideChanges;
    // The outside entry recorded by this read (0: none) and its notice (a marked project rewritten from outside).
    int outsideSequence = 0;
    std::vector<std::string> outsideNotice;
    HandMark mark;
    std::vector<HistoryEntry> history;
};

// Reads the project, records an edit made outside the tool (if any) as a history entry, and reports.
bool projectStatus(const std::filesystem::path &projectRoot, ProjectStatus &status, std::string &errorMessage);

// Undo, redo and revert (S5_BROWSER_EDITOR.md 2.7): each is a new history entry that reverts one earlier entry,
// object by object, validated like any transaction. An object the reverted entry changed is put back as it was before
// the entry when it is still as the entry left it; one changed since is a conflict, left alone unless `force`. The
// revert of a rename runs as the opposite rename (the lock entry and the pins follow it back); the hand-edit mark is
// never reverted. Undo takes the author's latest entry that is neither an undo nor reverted already; redo reverts
// the author's latest undo not reverted yet, while the author has made no other change since. Positions are read
// from the log; nothing about them is stored.
enum class RevertKind
{
    Undo,
    Redo,
    Revert,
};

struct RevertRequest
{
    RevertKind kind = RevertKind::Undo;
    // RevertKind::Revert: the entry to revert.
    int sequence = 0;
    // Put back conflicting objects too.
    bool force = false;
    // Whose undo or redo (empty: the options' author; "*": anybody's latest, as `oymap undo`).
    std::string whose;
};

// The entry an undo or redo of `author` would revert, or 0 with the reason (`author` "*": anybody's).
int revertTarget(const std::filesystem::path &projectRoot, RevertKind kind, const std::string &author,
    std::string &reason);

// A revert on a project kept in memory (as applyTransactionInMemory). `options.author` is whose undo or redo it is.
bool revertInMemory(
    const std::filesystem::path &projectRoot,
    ProjectMemory &memory,
    TransactionChecks &checks,
    const RevertRequest &request,
    const TransactionOptions &options,
    TransactionResult &result,
    std::set<std::string> &changedFiles);

// The same from the files, under the project lock.
bool revertProject(
    const std::filesystem::path &projectRoot,
    const RevertRequest &request,
    const TransactionOptions &options,
    TransactionResult &result);

// The command line's undo and redo: the latest entry of anybody (`oymap undo`), with errors allowed. `changes` says
// what was put back.
bool undoProject(
    const std::filesystem::path &projectRoot, std::vector<std::string> &changes, std::string &errorMessage);
bool redoProject(
    const std::filesystem::path &projectRoot, std::vector<std::string> &changes, std::string &errorMessage);

// The objects of two readings of a project that differ ("rooms.yml#room:hall", "project.yml#/map_stats"): list
// items with an id under the top level, and every other top-level key as one.
std::vector<std::string> changedObjects(const Project &before, const Project &after);

// The project's hand-edit mark as project.yml says it, with what the kept history knows of it.
HandMark handMarkOf(const std::filesystem::path &projectRoot, const Project &project);

// `oymap protect`: a person sets (or clears) the hand-edit mark by hand, as a transaction of author `user`.
bool protectProject(
    const std::filesystem::path &projectRoot,
    bool clear,
    TransactionResult &result);

// `oymap fmt`/migrate: writes every source file in canonical form, with the keys of format 1 written, as one
// transaction of author `migration` (nothing when every file is so already).
bool migrateProject(const std::filesystem::path &projectRoot, bool dryRun, TransactionResult &result);

// What differs between two readings of a project's source files, object by object.
std::vector<std::string> semanticDiff(const Project &before, const Project &after);

// `oymap record`: puts an author and a label on the edits made outside the tool. The change now on disk is recorded
// first (as an `outside` entry); then every unattributed `outside` entry since that author's latest entry gets the
// author and the label. Nothing else in the entries changes. `taken` lists the entries attributed.
struct RecordResult
{
    std::string revision;
    std::vector<HistoryEntry> taken;
};

bool recordOutsideEdits(
    const std::filesystem::path &projectRoot,
    const std::string &author,
    const std::string &label,
    RecordResult &result,
    std::string &errorMessage);

// The lock as a record (2.4.1): writes ids.lock.yml when `lockText` differs from the file, under the project lock,
// and adds a line to .oymap/lock.log saying who changed it at which source revision and which entries changed.
// `by` is "build", "import" or "prune". `changed` says whether the file was written.
bool writeLockRecord(
    const std::filesystem::path &projectRoot,
    const std::string &lockText,
    const std::string &sourceRevision,
    const std::string &by,
    bool &changed,
    std::string &errorMessage);

// writeLockRecord for a caller that holds the project lock already.
bool writeLockRecordHeld(
    const std::filesystem::path &projectRoot,
    const std::string &lockText,
    const std::string &sourceRevision,
    const std::string &by,
    bool &changed,
    std::string &errorMessage);

// The lock's names after renames (2.4.1): an entry named by `from`, or by a name built on it (`door:x.leaf2`,
// `once.evt:x`), moves to the new name with its number. "doors: door:a -> door:b 7".
std::vector<std::string> renameLockEntries(YAML::Node &lockDocument,
    const std::vector<std::pair<std::string, std::string>> &renames);

// The entries of ids.lock.yml that differ between two lock texts, as lines ("events: evt:x 7 added").
std::vector<std::string> lockDifferences(const std::string &before, const std::string &after);

// `oymap lock prune`: drops the lock entries of ids no source file has (core/IndoorLowering.h retiredLockEntries),
// a deliberate step, never a build's or an undo's. Outdoor projects keep every entry: there is no rule of what is
// live there yet, so nothing is dropped and `note` says so.
struct LockPruneResult
{
    // "events: evt:gone 3".
    std::vector<std::string> dropped;
    std::string lockHashBefore;
    std::string lockHashAfter;
    std::string note;
};

bool pruneProjectLock(
    const std::filesystem::path &projectRoot,
    bool dryRun,
    LockPruneResult &result,
    std::string &errorMessage);

// Holds <project>/.oymap/lock while it lives (a dead holder's lock is taken over). Used by everything that writes a
// project's files.
class ProjectWriteLock
{
public:
    // Waits up to `waitMilliseconds` for another writer to finish.
    explicit ProjectWriteLock(const std::filesystem::path &projectRoot, int waitMilliseconds = 0);
    ~ProjectWriteLock();
    ProjectWriteLock(const ProjectWriteLock &) = delete;
    ProjectWriteLock &operator=(const ProjectWriteLock &) = delete;
    bool held() const;

private:
    std::filesystem::path m_path;
    bool m_held = false;
};

extern const char *const ProjectLockedMessage;

// <project>/.oymap, made with its .gitignore when missing.
std::filesystem::path projectStateRoot(const std::filesystem::path &projectRoot, bool create);
}
