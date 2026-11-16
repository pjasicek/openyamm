#pragma once

#include "core/Coplanar.h"
#include "core/IndoorBuild.h"
#include "core/IndoorLowering.h"
#include "core/Ops.h"
#include "core/OutdoorLowering.h"
#include "core/View.h"

#include <filesystem>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// What a long-lived core (`oymap serve`, the WebAssembly core's oymap_call) keeps between calls (S5_BROWSER_EDITOR.md
// 2.4.3): per project folder, the files as last read (parsed, with their canonical texts and the source revision),
// the validation of that state with what it lowered (the view), and per asset root the tables the lowering reads,
// parsed with their lookups. The files stay the truth: every call first compares each file's size and modification
// time with what was read, then a hash of its bytes, and parses again only a file that really changed (an edit
// made with another tool, recorded in the history by the next transaction as before).
class StudioService
{
public:
    // The asset root of the session (session.configure, `serve --assets`); empty: none.
    void setAssetRoot(const std::filesystem::path &assetRoot);
    const std::filesystem::path &assetRoot() const;

    struct FileStamp
    {
        bool exists = false;
        uintmax_t size = 0;
        std::filesystem::file_time_type time = {};
        // contentHash128 of the bytes.
        std::string hash;
    };

    // The view of one state of a project (a revision with a lock): what its validation lowered, and the mesh and the
    // layout made from it when asked.
    struct View
    {
        std::string revision;
        std::string lockHash;
        ValidationViews lowered;
        bool meshMade = false;
        ViewMesh mesh;
        std::string meshFile;
        std::string layoutJson;
    };

    struct Entry
    {
        std::filesystem::path root;
        ProjectMemory memory;
        std::map<std::string, FileStamp> stamps;
        // Problems reading a file (unreadable, not YAML, project.yml missing), by file name.
        std::map<std::string, ProjectIssue> loadIssues;
        std::string pinsHash;
        // Schema issues of each file, with the hash of the bytes they were found in.
        std::map<std::string, std::pair<std::string, std::vector<ProjectIssue>>> schemaIssues;
        // Each file's tree as JSON text, with the hash of the bytes it was made from.
        std::map<std::string, std::pair<std::string, std::string>> treeJson;

        // The validation of the current state (with or without the asset root), its parts for the next one, and the
        // files changed since those parts were made.
        bool validated = false;
        bool validatedWithAssets = false;
        std::vector<ProjectIssue> issues;
        ValidationParts parts;
        std::set<std::string> changedSinceParts;
        // The latest view of the project that lowered (the current state's, or an older one: stale).
        std::shared_ptr<View> view;
        // Files whose tree stands as an edit left it (canonical text written, not read back): read back when the
        // core is idle, and the validation dropped if the tree read back says something else.
        std::set<std::string> unsettled;
        // An unsettled file's text already parsed (edit.apply's answer parses each changed file's text): its tree,
        // by the text it was read from, used by the read-back instead of parsing that text again (S8f).
        std::map<std::string, std::pair<std::string, YAML::Node>> readBack;
        // An outdoor project's land up to its peaks, kept between its lowerings (core/OutdoorLowering.h).
        std::shared_ptr<OutdoorLandCache> land = std::make_shared<OutdoorLandCache>();
    };

    // The project in `root` as on disk now, read or brought up to the files. Null when nothing of a project can be
    // read (no folder, no project.yml); `issues` says why.
    Entry *project(const std::filesystem::path &root, std::vector<ProjectIssue> &issues);

    // Drops what is kept of the project in `root` (session.release: the hosted worker keeps one map at a time);
    // whether anything was kept.
    bool release(const std::filesystem::path &root);

    // The issues the files' schemas find, and the files that could not be read (project.open's issues).
    std::vector<ProjectIssue> readingIssues(Entry &entry);

    // The full checks of the current state (check.validate), kept until a file changes. Without the asset root
    // when `withAssets` is false or the session has none.
    const std::vector<ProjectIssue> &validate(Entry &entry, bool withAssets);

    // edit.apply on the kept project: the caller holds the project's write lock and has just called project().
    bool applyTransaction(
        Entry &entry,
        const YAML::Node &operations,
        const TransactionOptions &options,
        TransactionResult &result);

    // edit.undo, edit.redo, edit.revert on the kept project (core/Ops.h revertInMemory), as applyTransaction.
    bool revert(
        Entry &entry,
        const RevertRequest &request,
        const TransactionOptions &options,
        TransactionResult &result);

    // The view of the current state, or the last one that lowered (stale); null when the project never lowered.
    // Validates first when needed.
    std::shared_ptr<View> view(Entry &entry);
    // Makes the view's mesh and writes it under <project>/.oymap/view/ (once per view); false with a message when
    // it cannot be written.
    bool makeMesh(Entry &entry, View &view, std::string &errorMessage);
    const std::string &layout(View &view);

    // A file's tree as JSON text (kept while the file's bytes are the same).
    const std::string &treeJson(Entry &entry, const std::string &fileName);

    // Work left for when nothing waits: the edited trees read back from their canonical texts.
    void idle();
    // A written edit's answer parsed `text`, an unsettled file's canonical text, into `document` and wrote it as
    // `json`: the read-back takes that tree, and project.open that JSON, instead of doing the same work again.
    void keepReadBack(Entry &entry, const std::string &fileName, const std::string &text, const YAML::Node &document,
        const std::string &json);

    // The lowering's tables of the session's asset root (read once per asset root).
    std::shared_ptr<const LoweringOptions> loweringOptions();
    BuildOptions buildOptions(bool withAssets);

private:
    bool refresh(Entry &entry, std::vector<ProjectIssue> &issues);
    void settle(Entry &entry);
    void adoptValidation(Entry &entry, bool withAssets, ValidationParts parts, std::vector<ProjectIssue> issues,
        const ValidationViews &views);
    // After a written edit or revert: the stamps of the files written and the edit's validation kept.
    void adoptCommit(Entry &entry, const TransactionResult &result, const std::set<std::string> &changed,
        ValidationParts parts, std::vector<ProjectIssue> issues, const ValidationViews &views, bool withAssets);

    std::filesystem::path m_assetRoot;
    std::map<std::filesystem::path, std::shared_ptr<const LoweringOptions>> m_lowering;
    OutdoorOriginals m_originals;
    std::map<std::filesystem::path, Entry> m_projects;
};
}
