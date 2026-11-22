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
// The world whose kits, roofs, ground tile sets and default textures the studio builds a map of `world` with: MM6,
// MM7, MM8 and MM9 their own; a world that has none of its own (Xeen) the base its world.yml names in terrainTileset
// (mm6, mm7 or mm8), else itself.
std::string studioStyleWorld(const std::filesystem::path &assetRoot, const std::string &world);
// An engine table of the asset root (engine/data_tables/<fileName>) with the rows the world adds to it: its world.yml
// tableContributions of tableName in mode append, as the game composes it. False when the engine table is missing.
bool readWorldTable(
    const std::filesystem::path &assetRoot,
    const std::string &world,
    const std::string &fileName,
    const std::string &tableName,
    std::string &text);

// A named place where the party arrives on a map (D-4: a dungeon with several mouths): a plan entrance of kind
// arrival or both, or `start`; `oymap install` writes the map's into its <stem>.studio.yml (`arrivals`), and a door
// or exit of another map names one (`into: {map, arrival}`, a neighbour's `arrival: entrance:<id>`).
struct MapArrival
{
    std::string name;
    int at[3] = {0, 0, 0};
    // The game's angle units: 2048 a turn, 0 east, 512 north.
    int facing = 0;
};

enum class MapArrivalLookup
{
    Found,
    // The map has no <stem>.studio.yml in the mount or the asset root (not installed yet).
    NotInstalled,
    // It has one, without that name (`known` lists the names it has).
    Unknown
};

// `name` among the arrivals of the installed map `map` (its file name: xeen_xd10.blv) of `world`: the mount's
// <stem>.studio.yml first, then the asset root's.
MapArrivalLookup findMapArrival(
    const std::filesystem::path &assetRoot,
    const std::filesystem::path &mountRoot,
    const std::string &world,
    const std::string &map,
    const std::string &name,
    MapArrival &arrival,
    std::string &known);

// A door's or an exit's arrival by name: true with the arrival when the installed map has it; true with a warning in
// `warning` and the map's start ([0, 0, 0], facing 0) when the map is not installed; false with the error in
// `warning` when the installed map has no arrival of that name.
bool resolveMapArrival(
    const std::filesystem::path &assetRoot,
    const std::filesystem::path &mountRoot,
    const std::string &world,
    const std::string &map,
    const std::string &name,
    MapArrival &arrival,
    std::string &warning);

// The window the game shows before a move to another map (MM6-MM8's entrance window: the map's name, a picture, the
// question or a line, OK and Close): evt.MoveToMap's seventh number, the row of trans.txt whose line replaces "Do you
// wish to enter X?" (0: that question; the shipped scripts call it the house), and its eighth, the picture (1 the
// dungeon entrance's; 0 with text 0: no window). `direct`: no window at all, not even the engine's leave-the-dungeon
// one (`{direct = true}`).
struct MoveScreen
{
    int text = 0;
    int picture = 0;
    bool direct = false;
};

// `screen` under a door's, a thing's or a teleport's `into`, or under a neighbour (feedback F16, 2026-11-22): left
// out, the standard entrance window into a dungeon (`map` a .blv: picture 1) and none to an outdoor map; `none`, a
// direct move; `{text: <trans.txt row>, picture: <n, 1 when left out>}` (`house` is the older name of `text`). False
// with `error` when it is none of these.
bool readMoveScreen(const YAML::Node &screen, const std::string &map, MoveScreen &result, std::string &error);

// The `, {direct = true}` evt.MoveToMap's options take for a direct move, else nothing.
std::string moveScreenOptions(const MoveScreen &screen);
}
