#pragma once

#include "core/Json.h"
#include "core/Project.h"
#include "core/Things.h"

#include <array>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// core/View.h
struct ViewMesh;

// Each command takes the arguments after its name and returns the process exit code:
// 0 done, 1 failed (or, for checks, issues found), 2 wrong usage.
int runEdit(const std::vector<std::string> &arguments);
int runStatus(const std::vector<std::string> &arguments);
int runUndo(const std::vector<std::string> &arguments);
int runRedo(const std::vector<std::string> &arguments);
int runRevert(const std::vector<std::string> &arguments);
int runProtect(const std::vector<std::string> &arguments);
int runMigrate(const std::vector<std::string> &arguments);
int runMod(const std::vector<std::string> &arguments);
int runExport(const std::vector<std::string> &arguments);
int runFmt(const std::vector<std::string> &arguments);
int runReads(const std::vector<std::string> &arguments);
int runValidate(const std::vector<std::string> &arguments);
int runBuild(const std::vector<std::string> &arguments);
int runBuildMap(const std::vector<std::string> &arguments);
int runAudit(const std::vector<std::string> &arguments);
int runFlow(const std::vector<std::string> &arguments);
int runThings(const std::vector<std::string> &arguments);
int runMetrics(const std::vector<std::string> &arguments);
int runSceneRoundTrip(const std::vector<std::string> &arguments);
int runRender(const std::vector<std::string> &arguments);
int runRenderSketch(const std::vector<std::string> &arguments);
int runSolve(const std::vector<std::string> &arguments);
int runProbe(const std::vector<std::string> &arguments);
int runImport(const std::vector<std::string> &arguments);
int runInstall(const std::vector<std::string> &arguments);
int runCompileIndoor(const std::vector<std::string> &arguments);
int runSchema(const std::vector<std::string> &arguments);
int runQuery(const std::vector<std::string> &arguments);
int runAssets(const std::vector<std::string> &arguments);
int runEventFunctions(const std::vector<std::string> &arguments);
int runScriptReference(const std::vector<std::string> &arguments);
int runNew(const std::vector<std::string> &arguments);
int runCompare(const std::vector<std::string> &arguments);
// cli/PinsCommands.cpp
int runPins(const std::vector<std::string> &arguments);
int runRecord(const std::vector<std::string> &arguments);
int runLock(const std::vector<std::string> &arguments);

// Why opening a project's map for reading failed (oymap things and the request list's check.things).
enum class TargetFailure
{
    None,
    NotAProject,
    DoesNotBuild,
    NoAssetRoot,
    Failed,
};

// Every interactive thing of a project's map, built from its current files into a private folder, with the names the
// build gave its numbers.
struct ThingsReport
{
    std::string map;
    std::string world;
    std::vector<InteractiveThing> things;
    CoplanarNames names;
};

bool collectThings(
    const std::filesystem::path &projectRoot,
    const std::filesystem::path &assetRoot,
    ThingsReport &report,
    TargetFailure &failure,
    std::vector<ProjectIssue> &buildIssues,
    std::string &errorMessage);

// --- the reading commands' work, shared by the command line and the request list (cli/Rpc.cpp) -------------------

// What a reading request names: a shipped map's file name (6d01.blv) with its world, or a project folder (built
// into a private folder and read as the game would read it).
struct ReadRequest
{
    std::filesystem::path assetRoot;
    std::string world;
    std::string target;
    // The builds' mount read in front of the asset root: when set, it is put in front for this request only (the
    // request list's `built`, with the session's mount, or none); when unset, whatever the command line set stays.
    std::optional<std::filesystem::path> mount;
};

// Why a reading request failed. `failure` NotAProject, DoesNotBuild (with `issues`) and NoAssetRoot as for
// collectThings; `noSuchMap` when the asset root has no map of that name; Failed otherwise (`badWorld` when the
// world could not be opened). Messages name the asset root as "the asset root", never by its path.
struct ReadFailure
{
    TargetFailure failure = TargetFailure::None;
    bool noSuchMap = false;
    bool badWorld = false;
    std::string message;
    std::vector<ProjectIssue> issues;
};

struct AuditRequest
{
    ReadRequest read;
    bool reach = false;
    bool strict = false;
    // The map whose faces in one plane are the original's; empty: a project's map_stats.reference or its base.
    std::string original;
    // Also the lock-and-key solve of an indoor map, as `oymap solve --json` gives it (check.audit's `solve`): one
    // walk serves the solve and the questions' order, where an audit and a solve each walk the map.
    bool solve = false;
};

// `oymap audit --json`'s members (map, world, overview, coplanar, reachability, scene_overlays, scripts, warnings,
// findings) into the open object; `errors` counts the findings of severity error.
bool writeAuditMembers(const AuditRequest &request, JsonWriter &writer, size_t &errors, ReadFailure &failure);

// compare.run (`oymap compare` on a project and its original): `read.target` is the rebuild (a project folder, or a
// second map file with `read.world`); `original` its original (default: a project's map_stats.reference, else its
// base), in `originalWorld` (default: the project's world, else read.world).
struct CompareRequest
{
    ReadRequest read;
    std::string original;
    std::string originalWorld;
};

// compare.run's members into the open object: kind, original, rebuilt, world, score, band, parts, vertical_offset,
// worst, heat, floor_missing_in_rebuild, floor_only_in_rebuild, notes and the full report as `oymap compare --json`
// prints it.
bool writeCompareMembers(const CompareRequest &request, JsonWriter &writer, ReadFailure &failure);

// A shipped (or installed) map's view mesh as the core's views draw it (view.original_mesh: the original beside its
// rebuild): indoor every visible face as stored, owned by its sector; outdoor the land by its tiles and the models.
bool readShippedViewMesh(
    const ReadRequest &request, ViewMesh &mesh, std::string &kind, std::string &mapFile, ReadFailure &failure);

// check.metrics: `oymap metrics`'s JSON (compact) of a shipped map or a project, with the map read and its world.
bool readMetricsJson(const ReadRequest &request, bool reach, std::string &json, std::string &mapFile,
    std::string &world, ReadFailure &failure);

// check.probe: `oymap probe`'s account of why the party can or cannot walk between two points of an indoor map.
bool readProbeText(const ReadRequest &request, const std::array<float, 3> &from, const std::array<float, 3> &to,
    bool doorsOpen, std::string &text, std::string &mapFile, ReadFailure &failure);

// project.import: a shipped map (`request.target` a map file, with its world) as an overlay project in
// `projectDirectory`, which must hold no project yet; `written` names the files made.
bool importShippedMap(const ReadRequest &request, const std::filesystem::path &projectDirectory,
    std::vector<std::string> &written, std::string &mapFile, ReadFailure &failure);

// `oymap solve --json`'s members into the open object.
bool writeSolveMembers(const ReadRequest &request, JsonWriter &writer, ReadFailure &failure);

// The map's event handlers as `oymap flow` prints them (a JSON array of {event, title, paths, truncated}).
bool readEventFlow(const ReadRequest &request, std::string &mapFile, std::string &flowJson, ReadFailure &failure);

// The labelled picture of `oymap render` as PNG bytes.
struct RenderRequest
{
    ReadRequest read;
    bool isometric = false;
    int size = 1024;
    bool labels = true;
};

// `mapFile` is the map drawn (a project's built map).
bool renderTargetPng(const RenderRequest &request, std::vector<uint8_t> &png, int &width, int &height,
    std::string &mapFile, ReadFailure &failure);

// `oymap assets --json`'s members (decorations, textures, matches) into the open object. False with a message when
// the world cannot be opened.
bool writeAssetSearchMembers(
    const std::filesystem::path &assetRoot,
    const std::string &query,
    const std::string &world,
    const std::string &kind,
    size_t limit,
    JsonWriter &writer,
    std::string &errorMessage);

// The function names the game gives event scripts (evt.<name>), sorted, without the scripts' own plumbing.
std::vector<std::string> eventFunctionNames();

// `oymap new`: an empty indoor or outdoor project. False with a message when the folder already holds a project (`exists`) or
// a file cannot be written; `written` names the files made.
struct NewProjectRequest
{
    std::filesystem::path root;
    std::string id;
    std::string name;
    std::string world = "mm6";
    std::string reference = "6d01.blv";
    std::string statsId;
    // indoor (rooms, objects, wiring) or outdoor (a plan, a sketch with flat land of spot heights and the arrival
    // point: S5b2's hand author starts there; no `reference`, since a new map rebuilds nothing).
    std::string kind = "indoor";
};

bool createEmptyProject(
    const NewProjectRequest &request, std::vector<std::string> &written, bool &exists, std::string &errorMessage);

// The text `oymap new` prints after making a project: what to do first.
extern const char *const NewProjectNext;
extern const char *const NewOutdoorProjectNext;

// Argument helpers shared by the command files: each removes what it finds from `arguments`.
bool takeFlag(std::vector<std::string> &arguments, const std::string &flag);
bool takeOption(std::vector<std::string> &arguments, const std::string &option, std::string &value);
// The asset root a command works against: --assets, else OYMAP_ASSETS, else none.
std::filesystem::path takeAssetRoot(std::vector<std::string> &arguments, std::filesystem::path *pMount = nullptr);
}
