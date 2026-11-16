#pragma once

#include "core/Schema.h"

#include <yaml-cpp/yaml.h>

#include <filesystem>
#include <map>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// How much an issue matters (S5_BROWSER_EDITOR.md 2.4.2), set where the issue is found: an error means the map
// cannot be built as written (it stops a build and an edit that adds it); a warning means it builds but a rule is
// broken (the outdoor sketch's findings on heights and coverage, which the build takes as drawn); a note is for
// information.
enum class IssueSeverity
{
    Error,
    Warning,
    Note,
};

// "error", "warning", "note".
const char *severityName(IssueSeverity severity);

// One problem found in a project, by the schemas or by a later check. `file` is relative to the project folder.
struct ProjectIssue
{
    std::string file;
    std::string path;
    std::string message;
    // Stable identifier of the kind of problem ("schema", "reference", "geometry" ...), for tools.
    std::string code;
    IssueSeverity severity = IssueSeverity::Error;

    bool isError() const
    {
        return severity == IssueSeverity::Error;
    }
};

// Whether any of the issues is an error (what stops a build).
bool hasErrors(const std::vector<ProjectIssue> &issues);

struct ProjectFile
{
    // Relative to the project folder, with forward slashes ("rooms.yml").
    std::string name;
    std::string schema;
    // The bytes on disk.
    std::string text;
    YAML::Node document;
};

// A map project: a folder of text files (PLAN.md section 4). The files are the truth: this object is only what was
// read from them.
struct Project
{
    std::filesystem::path root;
    // By file name. Only the files that exist.
    std::map<std::string, ProjectFile> files;

    bool has(const std::string &name) const;
    // The file's document, or an undefined node.
    YAML::Node document(const std::string &name) const;
};

// The three classes of project file (S5_BROWSER_EDITOR.md 2.4.1). Only the source files make the source revision,
// the history and undo; the id lock is a record (written by builds, `import` and `oymap lock prune`, never undone);
// the pins document is the review, with its own change counter and log.
enum class ProjectFileClass
{
    Source,
    Record,
    Review,
};

// The project files the format knows and the schema of each.
struct ProjectFileKind
{
    const char *pName;
    const char *pSchema;
    bool required;
    ProjectFileClass fileClass;
};

const std::vector<ProjectFileKind> &projectFileKinds();

// Whether `name` ("rooms.yml") is one of the source files.
bool isSourceFile(const std::string &name);

// A 128-bit content hash as 32 lowercase hex digits: the first half of the text's SHA-256. Every reader, native or
// WebAssembly, gives the same digits.
std::string contentHash128(const std::string &text);

// The id lock's hash (the record's identity beside the source revision: a build is source revision plus lock hash):
// contentHash128 of the file's bytes, or "none" when the project has no lock.
std::string lockHashOfText(const std::string *pLockText);
std::string projectLockHash(const std::filesystem::path &projectRoot);

// Reads every known file of the folder. Unreadable or unparsable files and a missing project.yml are issues;
// false only when nothing of a project could be read.
bool loadProject(const std::filesystem::path &root, Project &project, std::vector<ProjectIssue> &issues);

// Each file against its schema.
void validateProjectSchemas(const Project &project, std::vector<ProjectIssue> &issues);
// One file against its schema.
void validateFileSchema(const ProjectFile &file, std::vector<ProjectIssue> &issues);

// The file's canonical text (CanonicalYaml.h).
std::string canonicalText(const ProjectFile &file);

// Writes through a temporary file and a rename, so a reader never sees half a file and a hard-linked target is
// replaced, not edited.
bool writeTextFileAtomically(const std::filesystem::path &path, const std::string &text, std::string &errorMessage);
bool writeBinaryFileAtomically(
    const std::filesystem::path &path,
    const std::vector<uint8_t> &bytes,
    std::string &errorMessage);
bool readTextFile(const std::filesystem::path &path, std::string &text);
}
