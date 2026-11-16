#include "core/Service.h"

#include "core/CanonicalYaml.h"
#include "core/Json.h"

#include <algorithm>
#include <system_error>

namespace OpenYAMM::Studio
{
namespace
{
// Whether two trees are the same with their maps' keys in the same order (scalars by kind and value, as sameYaml):
// an edited tree and the same file read back from its canonical text lower alike only then.
bool sameInOrder(const YAML::Node &left, const YAML::Node &right)
{
    if (left.Type() != right.Type())
    {
        return false;
    }

    if (left.IsMap())
    {
        if (left.size() != right.size())
        {
            return false;
        }

        YAML::const_iterator other = right.begin();

        for (YAML::const_iterator iterator = left.begin(); iterator != left.end(); ++iterator, ++other)
        {
            if (iterator->first.Scalar() != other->first.Scalar() || !sameInOrder(iterator->second, other->second))
            {
                return false;
            }
        }

        return true;
    }

    if (left.IsSequence())
    {
        if (left.size() != right.size())
        {
            return false;
        }

        for (size_t index = 0; index < left.size(); ++index)
        {
            if (!sameInOrder(left[index], right[index]))
            {
                return false;
            }
        }

        return true;
    }

    std::string where;
    return sameYaml(left, right, where);
}

// Puts a file into a project, replacing the entry (never assigning to a tree another project may share).
void putFile(Project &project, ProjectFile file)
{
    project.files.erase(file.name);
    const std::string name = file.name;
    project.files.emplace(name, std::move(file));
}

std::string worldOf(const Project &project)
{
    const YAML::Node card = project.document("project.yml");
    return card.IsMap() && card["world"] && card["world"].IsScalar() ? card["world"].Scalar() : std::string();
}

// The checks of an edit on a kept project: the current state's validation, and the edited project's from it.
class KeptChecks : public TransactionChecks
{
public:
    KeptChecks(StudioService &service, StudioService::Entry &entry, bool withAssets)
        : m_service(service)
        , m_entry(entry)
        , m_withAssets(withAssets)
    {
    }

    std::vector<ProjectIssue> before() override
    {
        return m_service.validate(m_entry, m_withAssets);
    }

    std::vector<ProjectIssue> after(const Project &edited, const std::set<std::string> &changed) override
    {
        std::set<std::string> since = m_entry.changedSinceParts;
        since.insert(changed.begin(), changed.end());
        BuildOptions options = m_service.buildOptions(m_withAssets);
        // A commit: the land kept up to the peaks, the scene's write and reader check left to the build (2.4.3).
        options.pLand = m_entry.land.get();
        options.commitCheck = true;
        validateProjectParts(edited, options, m_entry.parts.valid ? &m_entry.parts : nullptr, &since, parts, issues,
            &views);
        return issues;
    }

    ValidationParts parts;
    std::vector<ProjectIssue> issues;
    ValidationViews views;

private:
    StudioService &m_service;
    StudioService::Entry &m_entry;
    bool m_withAssets = false;
};
}

void StudioService::setAssetRoot(const std::filesystem::path &assetRoot)
{
    if (assetRoot == m_assetRoot)
    {
        return;
    }

    m_assetRoot = assetRoot;

    // Validations with assets were made against the other root.
    for (std::pair<const std::filesystem::path, Entry> &project : m_projects)
    {
        project.second.validated = false;
        project.second.parts = {};
    }
}

const std::filesystem::path &StudioService::assetRoot() const
{
    return m_assetRoot;
}

std::shared_ptr<const LoweringOptions> StudioService::loweringOptions()
{
    std::shared_ptr<const LoweringOptions> &kept = m_lowering[m_assetRoot];

    if (!kept)
    {
        kept = std::make_shared<const LoweringOptions>(readLoweringOptions(m_assetRoot));
    }

    return kept;
}

BuildOptions StudioService::buildOptions(bool withAssets)
{
    BuildOptions options;

    if (withAssets && !m_assetRoot.empty())
    {
        options.assetRoot = m_assetRoot;
        options.lowering = loweringOptions();
        options.pOriginals = &m_originals;
    }
    else
    {
        static const std::shared_ptr<const LoweringOptions> none =
            std::make_shared<const LoweringOptions>(readLoweringOptions({}));
        options.lowering = none;
    }

    return options;
}

bool StudioService::release(const std::filesystem::path &root)
{
    return m_projects.erase(root) > 0;
}

StudioService::Entry *StudioService::project(const std::filesystem::path &root, std::vector<ProjectIssue> &issues)
{
    std::error_code error;

    if (!std::filesystem::is_directory(root, error))
    {
        m_projects.erase(root);
        issues.push_back({"", "", "not a project folder (no such folder)", "project"});
        return nullptr;
    }

    Entry &entry = m_projects[root];
    entry.root = root;
    entry.memory.project.root = root;

    if (!refresh(entry, issues))
    {
        m_projects.erase(root);
        return nullptr;
    }

    return &entry;
}

bool StudioService::refresh(Entry &entry, std::vector<ProjectIssue> &issues)
{
    settle(entry);
    bool sourceChanged = false;

    for (const ProjectFileKind &kind : projectFileKinds())
    {
        const std::string name = kind.pName;
        const std::filesystem::path path = entry.root / name;
        std::error_code error;
        FileStamp now;
        now.exists = std::filesystem::is_regular_file(path, error);

        if (now.exists)
        {
            now.size = std::filesystem::file_size(path, error);
            now.time = std::filesystem::last_write_time(path, error);
        }

        FileStamp &old = entry.stamps[name];

        if (now.exists == old.exists && (!now.exists || (now.size == old.size && now.time == old.time)))
        {
            continue;
        }

        std::string text;
        const bool read = now.exists && readTextFile(path, text);

        if (read)
        {
            now.hash = contentHash128(text);

            if (old.exists && old.hash == now.hash)
            {
                old = now;
                continue;
            }
        }

        // A change: the file is read again.
        old = now;
        entry.memory.project.files.erase(name);
        entry.memory.canonical.erase(name);
        entry.loadIssues.erase(name);
        entry.unsettled.erase(name);
        entry.readBack.erase(name);
        entry.changedSinceParts.insert(name);
        entry.validated = false;
        sourceChanged = sourceChanged || isSourceFile(name);

        if (!now.exists)
        {
            if (kind.required)
            {
                entry.loadIssues[name] = {name, "", "the project has no " + name, "project"};
            }
        }
        else if (!read)
        {
            entry.loadIssues[name] = {name, "", "could not read the file", "project"};
        }
        else
        {
            ProjectFile file;
            file.name = name;
            file.schema = kind.pSchema;
            file.text = text;

            try
            {
                file.document = YAML::Load(file.text);
            }
            catch (const YAML::Exception &exception)
            {
                entry.loadIssues[name] = {name, "", std::string("not valid YAML: ") + exception.what(), "yaml"};
                continue;
            }

            if (isSourceFile(name))
            {
                entry.memory.canonical[name] = canonicalText(file);
            }

            putFile(entry.memory.project, std::move(file));
        }

        if (kind.fileClass == ProjectFileClass::Record)
        {
            entry.memory.lockHash = read ? lockHashOfText(&text) : lockHashOfText(nullptr);
        }
        else if (kind.fileClass == ProjectFileClass::Review)
        {
            entry.pinsHash = read ? now.hash : std::string("none");
        }
    }

    if (sourceChanged)
    {
        entry.memory.revision = revisionOfCanonicalTexts(entry.memory.canonical);
    }

    if (entry.memory.lockHash.empty())
    {
        entry.memory.lockHash = lockHashOfText(nullptr);
    }

    if (!entry.memory.project.has("project.yml"))
    {
        for (const std::pair<const std::string, ProjectIssue> &issue : entry.loadIssues)
        {
            issues.push_back(issue.second);
        }

        if (issues.empty())
        {
            issues.push_back({"project.yml", "", "the project has no project.yml", "project"});
        }

        return false;
    }

    return true;
}

void StudioService::settle(Entry &entry)
{
    for (const std::string &name : entry.unsettled)
    {
        const std::map<std::string, ProjectFile>::const_iterator file = entry.memory.project.files.find(name);

        if (file == entry.memory.project.files.end())
        {
            continue;
        }

        ProjectFile readBack{file->second.name, file->second.schema, file->second.text, YAML::Node()};
        const std::map<std::string, std::pair<std::string, YAML::Node>>::const_iterator parsed =
            entry.readBack.find(name);

        if (parsed != entry.readBack.end() && parsed->second.first == readBack.text)
        {
            readBack.document = parsed->second.second;
        }
        else
        {
            try
            {
                readBack.document = YAML::Load(readBack.text);
            }
            catch (const YAML::Exception &)
            {
                continue;
            }
        }

        // The tree the edit left says what its text says, in the same order: the validation made of it holds.
        if (!sameInOrder(file->second.document, readBack.document))
        {
            entry.validated = false;
            entry.changedSinceParts.insert(name);
        }

        putFile(entry.memory.project, std::move(readBack));
    }

    entry.unsettled.clear();
    entry.readBack.clear();
}

void StudioService::keepReadBack(Entry &entry, const std::string &fileName, const std::string &text,
    const YAML::Node &document, const std::string &json)
{
    const std::map<std::string, ProjectFile>::const_iterator file = entry.memory.project.files.find(fileName);

    if (!entry.unsettled.contains(fileName) || file == entry.memory.project.files.end() || file->second.text != text)
    {
        return;
    }

    entry.readBack[fileName] = {text, document};
    // The JSON stands for the tree read back: project.open takes it once the file is settled.
    entry.treeJson[fileName] = {contentHash128(text), json};
}

void StudioService::idle()
{
    for (std::pair<const std::filesystem::path, Entry> &project : m_projects)
    {
        settle(project.second);
    }
}

std::vector<ProjectIssue> StudioService::readingIssues(Entry &entry)
{
    std::vector<ProjectIssue> issues;

    // In the order of the project's files, as loadProject and validateProjectSchemas give them.
    for (const ProjectFileKind &kind : projectFileKinds())
    {
        const std::map<std::string, ProjectIssue>::const_iterator problem = entry.loadIssues.find(kind.pName);

        if (problem != entry.loadIssues.end())
        {
            issues.push_back(problem->second);
        }
    }

    for (const std::pair<const std::string, ProjectFile> &file : entry.memory.project.files)
    {
        const std::string hash = contentHash128(file.second.text);
        std::pair<std::string, std::vector<ProjectIssue>> &kept = entry.schemaIssues[file.first];

        if (kept.first != hash)
        {
            kept.first = hash;
            kept.second.clear();
            validateFileSchema(file.second, kept.second);
        }

        issues.insert(issues.end(), kept.second.begin(), kept.second.end());
    }

    return issues;
}

void StudioService::adoptValidation(Entry &entry, bool withAssets, ValidationParts parts,
    std::vector<ProjectIssue> issues, const ValidationViews &views)
{
    entry.validated = true;
    entry.validatedWithAssets = withAssets;
    entry.issues = std::move(issues);
    entry.parts = std::move(parts);
    entry.changedSinceParts.clear();

    // A state that lowered is the view from now on; one that did not leaves the last view (stale).
    if (views.indoor || views.outdoor)
    {
        std::shared_ptr<View> view = std::make_shared<View>();
        view->revision = entry.memory.revision;
        view->lockHash = entry.memory.lockHash;
        view->lowered = views;
        entry.view = view;
    }
}

const std::vector<ProjectIssue> &StudioService::validate(Entry &entry, bool withAssets)
{
    const bool assets = withAssets && !m_assetRoot.empty();

    if (entry.validated && entry.validatedWithAssets == assets)
    {
        return entry.issues;
    }

    // Problems reading a file come first and stop the checks, as loadProject's issues stop `oymap validate`.
    std::vector<ProjectIssue> issues;

    for (const std::pair<const std::string, ProjectIssue> &problem : entry.loadIssues)
    {
        issues.push_back(problem.second);
    }

    ValidationParts parts;
    ValidationViews views;

    if (issues.empty())
    {
        const bool incremental = entry.parts.valid && entry.validatedWithAssets == assets;
        BuildOptions options = buildOptions(assets);
        options.pLand = entry.land.get();
        validateProjectParts(entry.memory.project, options, incremental ? &entry.parts : nullptr,
            &entry.changedSinceParts, parts, issues, &views);
    }

    adoptValidation(entry, assets, std::move(parts), std::move(issues), views);
    return entry.issues;
}

bool StudioService::applyTransaction(
    Entry &entry,
    const YAML::Node &operations,
    const TransactionOptions &options,
    TransactionResult &result)
{
    const bool withAssets = !options.assetRoot.empty();
    KeptChecks checks(*this, entry, withAssets);
    std::set<std::string> changed;

    if (!entry.loadIssues.empty())
    {
        // A file that does not parse: the transaction as it always was, from the files.
        return OpenYAMM::Studio::applyTransaction(entry.root, operations, options, result);
    }

    if (!applyTransactionInMemory(entry.root, entry.memory, checks, operations, options, result, changed))
    {
        return false;
    }

    adoptCommit(entry, result, changed, std::move(checks.parts), std::move(checks.issues), checks.views, withAssets);
    return true;
}

bool StudioService::revert(
    Entry &entry,
    const RevertRequest &request,
    const TransactionOptions &options,
    TransactionResult &result)
{
    const bool withAssets = !options.assetRoot.empty();
    KeptChecks checks(*this, entry, withAssets);
    std::set<std::string> changed;

    if (!entry.loadIssues.empty())
    {
        return revertProject(entry.root, request, options, result);
    }

    if (!revertInMemory(entry.root, entry.memory, checks, request, options, result, changed))
    {
        return false;
    }

    adoptCommit(entry, result, changed, std::move(checks.parts), std::move(checks.issues), checks.views, withAssets);
    return true;
}

void StudioService::adoptCommit(Entry &entry, const TransactionResult &result, const std::set<std::string> &changed,
    ValidationParts parts, std::vector<ProjectIssue> issues, const ValidationViews &views, bool withAssets)
{
    if (!result.applied)
    {
        return;
    }

    // The files written: their stamps now, so the next call does not read them again (a file the change removed
    // is gone; a revert may write a file's own bytes back, not its canonical text).
    std::set<std::string> written = changed;

    if (!result.notes.empty())
    {
        // A rename moved the lock's entries.
        written.insert("ids.lock.yml");
    }

    for (const std::string &name : written)
    {
        const std::filesystem::path path = entry.root / name;
        std::error_code error;
        FileStamp &stamp = entry.stamps[name];
        stamp.exists = std::filesystem::exists(path, error);
        const std::map<std::string, ProjectFile>::const_iterator file = entry.memory.project.files.find(name);

        if (!stamp.exists || file == entry.memory.project.files.end())
        {
            stamp = FileStamp();
            entry.treeJson.erase(name);
            continue;
        }

        stamp.size = std::filesystem::file_size(path, error);
        stamp.time = std::filesystem::last_write_time(path, error);
        stamp.hash = contentHash128(file->second.text);

        if (isSourceFile(name))
        {
            entry.unsettled.insert(name);
        }

        entry.treeJson.erase(name);
    }

    adoptValidation(entry, withAssets && !m_assetRoot.empty(), std::move(parts), std::move(issues), views);
}

std::shared_ptr<StudioService::View> StudioService::view(Entry &entry)
{
    validate(entry, true);
    return entry.view;
}

bool StudioService::makeMesh(Entry &entry, View &view, std::string &errorMessage)
{
    if (view.meshMade)
    {
        return true;
    }

    std::string liquidsText;

    if (!m_assetRoot.empty())
    {
        readTextFile(m_assetRoot / "engine" / "liquids" / "liquids.yml", liquidsText);
    }

    const LiquidTextures liquids = readLiquidTextures(liquidsText, worldOf(entry.memory.project));
    view.mesh = view.lowered.indoor ? indoorViewMesh(*view.lowered.indoor, liquids)
        : outdoorViewMesh(*view.lowered.outdoor, liquids);
    // Named by what it was made from and by its own bytes (another core makes other bytes of the same revision: a
    // name must never stand for two contents, since the host serves meshes as immutable).
    const std::string name = view.revision + "-" + view.lockHash.substr(0, 8) + "-"
        + contentHash128(std::string(view.mesh.bytes.begin(), view.mesh.bytes.end())).substr(0, 12) + ".mesh";
    const std::filesystem::path folder = projectStateRoot(entry.root, true) / "view";
    std::error_code error;
    std::filesystem::create_directories(folder, error);

    // A mesh is named by what it was made from: the same name is the same bytes.
    if (std::filesystem::file_size(folder / name, error) != view.mesh.bytes.size() || error)
    {
        if (!writeBinaryFileAtomically(folder / name, view.mesh.bytes, errorMessage))
        {
            return false;
        }
    }

    // Keep the newest few: older revisions' meshes go.
    std::vector<std::pair<std::filesystem::file_time_type, std::filesystem::path>> meshes;

    for (std::filesystem::directory_iterator file(folder, error), end; !error && file != end; file.increment(error))
    {
        if (file->path().extension() == ".mesh")
        {
            std::error_code timeError;
            meshes.push_back({std::filesystem::last_write_time(file->path(), timeError), file->path()});
        }
    }

    std::sort(meshes.begin(), meshes.end());

    for (size_t index = 0; index + 8 < meshes.size(); ++index)
    {
        if (meshes[index].second.filename() != name)
        {
            std::filesystem::remove(meshes[index].second, error);
        }
    }

    view.meshFile = ".oymap/view/" + name;
    view.meshMade = true;
    return true;
}

const std::string &StudioService::layout(View &view)
{
    if (view.layoutJson.empty())
    {
        JsonWriter writer;
        writer.beginObject();

        if (view.lowered.indoor)
        {
            writeIndoorLayout(writer, *view.lowered.indoor);
        }
        else
        {
            writeOutdoorLayout(writer, *view.lowered.outdoor);
        }

        writer.endObject();
        // The members alone: the answer puts them after its own.
        const std::string text = writer.take();
        view.layoutJson = text.size() >= 2 ? text.substr(1, text.size() - 2) : std::string();
    }

    return view.layoutJson;
}

const std::string &StudioService::treeJson(Entry &entry, const std::string &fileName)
{
    const ProjectFile &file = entry.memory.project.files.at(fileName);
    const std::string hash = entry.unsettled.contains(fileName) ? std::string() : contentHash128(file.text);
    std::pair<std::string, std::string> &kept = entry.treeJson[fileName];

    if (hash.empty() || kept.first != hash)
    {
        JsonWriter writer;
        writer.node(file.document);
        kept.first = hash;
        kept.second = writer.take();
    }

    return kept.second;
}
}
