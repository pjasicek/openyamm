#include "core/Project.h"

#include "core/CanonicalYaml.h"
#include "core/Pins.h"

#include "engine/update/Sha256.h"

#include <algorithm>
#include <fstream>
#include <sstream>

namespace OpenYAMM::Studio
{
const char *severityName(IssueSeverity severity)
{
    switch (severity)
    {
    case IssueSeverity::Warning:
        return "warning";
    case IssueSeverity::Note:
        return "note";
    case IssueSeverity::Error:
        break;
    }

    return "error";
}

bool hasErrors(const std::vector<ProjectIssue> &issues)
{
    return std::any_of(issues.begin(), issues.end(), [](const ProjectIssue &issue) { return issue.isError(); });
}

bool Project::has(const std::string &name) const
{
    return files.contains(name);
}

YAML::Node Project::document(const std::string &name) const
{
    const std::map<std::string, ProjectFile>::const_iterator iterator = files.find(name);
    return iterator == files.end() ? YAML::Node(YAML::NodeType::Undefined) : iterator->second.document;
}

const std::vector<ProjectFileKind> &projectFileKinds()
{
    static const std::vector<ProjectFileKind> kinds = {
        {"project.yml", "project.schema.json", true, ProjectFileClass::Source},
        {"plan.yml", "plan.schema.json", false, ProjectFileClass::Source},
        {"sketch.yml", "sketch.schema.json", false, ProjectFileClass::Source},
        {"rooms.yml", "rooms.schema.json", false, ProjectFileClass::Source},
        {"objects.yml", "objects.schema.json", false, ProjectFileClass::Source},
        {"wiring.yml", "wiring.schema.json", false, ProjectFileClass::Source},
        {"atmosphere.yml", "atmosphere.schema.json", false, ProjectFileClass::Source},
        {"review/pins.yml", "pins.schema.json", false, ProjectFileClass::Review},
        {"ids.lock.yml", "ids_lock.schema.json", false, ProjectFileClass::Record},
    };
    return kinds;
}

bool isSourceFile(const std::string &name)
{
    for (const ProjectFileKind &kind : projectFileKinds())
    {
        if (name == kind.pName)
        {
            return kind.fileClass == ProjectFileClass::Source;
        }
    }

    return false;
}

std::string contentHash128(const std::string &text)
{
    return Engine::sha256Hex(text.data(), text.size()).substr(0, 32);
}

std::string lockHashOfText(const std::string *pLockText)
{
    return pLockText == nullptr ? std::string("none") : contentHash128(*pLockText);
}

std::string projectLockHash(const std::filesystem::path &projectRoot)
{
    std::string text;
    return readTextFile(projectRoot / "ids.lock.yml", text) ? lockHashOfText(&text) : lockHashOfText(nullptr);
}

bool readTextFile(const std::filesystem::path &path, std::string &text)
{
    std::ifstream stream(path, std::ios::binary);

    if (!stream)
    {
        return false;
    }

    std::ostringstream buffer;
    buffer << stream.rdbuf();
    text = buffer.str();
    return true;
}

namespace
{
template <typename Write>
bool writeAtomically(const std::filesystem::path &path, std::string &errorMessage, Write write)
{
    std::error_code error;

    if (path.has_parent_path())
    {
        std::filesystem::create_directories(path.parent_path(), error);
    }

    std::filesystem::path temporaryPath = path;
    temporaryPath += ".oymap-tmp";

    {
        std::ofstream stream(temporaryPath, std::ios::binary | std::ios::trunc);

        if (!stream)
        {
            errorMessage = "could not write " + temporaryPath.string();
            return false;
        }

        write(stream);

        if (!stream.good())
        {
            errorMessage = "could not write " + temporaryPath.string();
            return false;
        }
    }

    std::filesystem::rename(temporaryPath, path, error);

    if (error)
    {
        errorMessage = "could not replace " + path.string() + ": " + error.message();
        std::filesystem::remove(temporaryPath, error);
        return false;
    }

    return true;
}
}

bool writeTextFileAtomically(const std::filesystem::path &path, const std::string &text, std::string &errorMessage)
{
    return writeAtomically(
        path,
        errorMessage,
        [&text](std::ofstream &stream)
        {
            stream.write(text.data(), static_cast<std::streamsize>(text.size()));
        });
}

bool writeBinaryFileAtomically(
    const std::filesystem::path &path,
    const std::vector<uint8_t> &bytes,
    std::string &errorMessage)
{
    return writeAtomically(
        path,
        errorMessage,
        [&bytes](std::ofstream &stream)
        {
            stream.write(reinterpret_cast<const char *>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
        });
}

bool loadProject(const std::filesystem::path &root, Project &project, std::vector<ProjectIssue> &issues)
{
    project = {};
    project.root = root;
    std::error_code error;

    if (!std::filesystem::is_directory(root, error))
    {
        // No absolute path in the core's messages (the request list's rule): the caller knows what it named.
        issues.push_back({"", "", "not a project folder (no such folder)", "project"});
        return false;
    }

    for (const ProjectFileKind &kind : projectFileKinds())
    {
        const std::filesystem::path path = root / kind.pName;

        if (!std::filesystem::exists(path, error))
        {
            if (kind.required)
            {
                issues.push_back({kind.pName, "", "the project has no " + std::string(kind.pName), "project"});
            }

            continue;
        }

        ProjectFile file;
        file.name = kind.pName;
        file.schema = kind.pSchema;

        if (!readTextFile(path, file.text))
        {
            issues.push_back({kind.pName, "", "could not read the file", "project"});
            continue;
        }

        try
        {
            file.document = YAML::Load(file.text);
        }
        catch (const YAML::Exception &exception)
        {
            issues.push_back({kind.pName, "", std::string("not valid YAML: ") + exception.what(), "yaml"});
            continue;
        }

        project.files[file.name] = file;
    }

    return project.has("project.yml");
}

void validateProjectSchemas(const Project &project, std::vector<ProjectIssue> &issues)
{
    for (const std::pair<const std::string, ProjectFile> &entry : project.files)
    {
        validateFileSchema(entry.second, issues);
    }
}

void validateFileSchema(const ProjectFile &file, std::vector<ProjectIssue> &issues)
{
    // The pins document is read as format 1 (a format 0 one is migrated when it is next written: core/Pins.h).
    const YAML::Node document = file.schema == "pins.schema.json" ? migratePinsDocument(file.document) : file.document;

    for (const SchemaIssue &issue : SchemaSet::builtIn().validate(document, file.schema))
    {
        issues.push_back({file.name, issue.path, issue.message, "schema"});
    }
}

std::string canonicalText(const ProjectFile &file)
{
    return writeCanonicalYaml(file.document, SchemaSet::builtIn(), file.schema);
}
}
