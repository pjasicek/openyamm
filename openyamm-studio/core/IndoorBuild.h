#pragma once

#include "core/Project.h"

#include <filesystem>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
class JsonWriter;
struct LoweredIndoorMap;
struct LoweredItem;
struct LoweredLadder;
struct LoweredMonster;
struct LoweringOptions;
struct OutdoorOriginals;
class OutdoorLandCache;
struct OutdoorView;

struct BuildOptions
{
    // Where the map files go. Default: <project>/build.
    std::filesystem::path outputDirectory;
    // An asset root (the folder holding engine/ and worlds/), for the tables a build looks names up in. Optional
    // for a project that names no decoration.
    std::filesystem::path assetRoot;
    // A mount folder read in front of the asset root, as the game's --extra-mount (`oymap validate|build --mount`, S8g):
    // its data tables, sounds and textures count where the asset root's do. Empty: none.
    std::filesystem::path mountRoot;
    // Check everything and compile, but write nothing (not even ids.lock.yml).
    bool dryRun = false;
    // The asset root's tables as the lowering reads them, with their parsed lookups (readLoweringOptions), kept by
    // a service once per asset root (S5_BROWSER_EDITOR.md 2.4.3); without them each lowering reads and parses the
    // tables itself.
    std::shared_ptr<const LoweringOptions> lowering;
    // An outdoor dry build that gets this far fills it with what the view needs (core/View.h); not owned.
    OutdoorView *pOutdoorView = nullptr;
    // The originals' coplanar places a service keeps (not owned); without it each build reads the original.
    OutdoorOriginals *pOriginals = nullptr;
    // The outdoor land kept between a project's lowerings by a service (core/OutdoorLowering.h; not owned).
    OutdoorLandCache *pLand = nullptr;
    // A commit's check of an outdoor dry build (S5_BROWSER_EDITOR.md 2.4.3): without the scene's write and its
    // reader check, which are build checks (install, Play here and playtests run them); the view needs neither.
    bool commitCheck = false;
};

struct BuildResult
{
    std::vector<ProjectIssue> issues;
    std::vector<std::string> warnings;
    // Files written, relative to the output directory.
    std::vector<std::string> files;
    // An overlay project's build: there is no geometry, only handlers.
    bool overlay = false;
    std::string mapFile;
    size_t sectors = 0;
    size_t vertices = 0;
    size_t faces = 0;
    size_t portals = 0;
    size_t doors = 0;
    size_t lights = 0;
    size_t spawns = 0;
    size_t entities = 0;
    size_t events = 0;
    size_t chests = 0;
    bool lockChanged = false;
    // What the build was made from (written into build.json, and by `oymap install` into <stem>.studio.yml): the
    // project's source revision and the hash of the lock the build wrote or used.
    std::string sourceRevision;
    std::string lockHash;
    // The map's named arrivals (build.json `named_arrivals`, then <stem>.studio.yml `arrivals`): `start` and each plan
    // entrance a party can arrive by (D-4).
    std::vector<MapArrival> arrivals;
    // An overlay that changes the base map's scene (S6_PLAN.md item O): the scene overlay's keys and what it adds,
    // changes and removes.
    std::vector<std::string> sceneOverlayKeys;
    size_t sceneAdded = 0;
    size_t sceneChanged = 0;
    size_t sceneRemoved = 0;
    // An overlay that writes cinematics (`<stem>_<project id>.cinematics.yml`, S8a): how many replace the map's own
    // (the same name) and how many are new.
    bool overlayCinematics = false;
    size_t cinematicsAdded = 0;
    size_t cinematicsReplaced = 0;
};

// The scene's records as a new map's scene file holds them and an overlay adds them (S8a): a placed monster as an actor
// (initial_state.actors, authored_content.actors), an item on the floor as a sprite object (sprite_objects), a ladder
// (ladders). An index below 0 leaves the record's own index out (an overlay's are appended where the game puts them).
YAML::Node sceneActorNode(const LoweredMonster &monster, int actorIndex);
YAML::Node sceneSpriteObjectNode(const LoweredItem &item, int index);
YAML::Node sceneLadderNode(const LoweredLadder &ladder);

// build.json's `named_arrivals` (BuildResult::arrivals), which `oymap install` copies into <stem>.studio.yml.
void writeNamedArrivals(JsonWriter &writer, const std::vector<MapArrival> &arrivals);

// The asset root's tables the indoor lowering looks names up in (each empty without an asset root), with their
// parsed lookups (LoweringOptions::tables).
LoweringOptions readLoweringOptions(const std::filesystem::path &assetRoot);

// Schema checks and the cross-file checks that need no compile (PLAN.md section 6, tier 0, as far as S0 goes).
void validateProject(const Project &project, const BuildOptions &options, std::vector<ProjectIssue> &issues);

// What validateProject found file by file, kept by a service so that an edited project is checked again only where
// it changed (S5_BROWSER_EDITOR.md 2.4.3): the schemas of the changed files, and the references of the changed files
// when no file's set of ids (nor the lock's, nor the map card's quest bits and items) changed.
struct ValidationParts
{
    bool valid = false;
    std::map<std::string, std::vector<ProjectIssue>> schemaIssues;
    // Words on the wrong kind (core/Kinds.h), file by file: warnings.
    std::map<std::string, std::vector<ProjectIssue>> kindIssues;
    std::map<std::string, std::set<std::string>> declaredIds;
    std::set<std::string> lockIds;
    std::set<std::string> qbits;
    std::set<std::string> items;
    std::map<std::string, std::vector<ProjectIssue>> referenceIssues;
};

// What the validation lowered, for the view (core/View.h): the indoor lowering when it ran to its end without an
// issue, the outdoor dry build's map when it got that far.
struct ValidationViews
{
    std::shared_ptr<const LoweredIndoorMap> indoor;
    std::shared_ptr<const OutdoorView> outdoor;
    // A view build (S5_BROWSER_EDITOR.md 2.4.2): the lowering refused objects, and `indoor` is the rest, lowered
    // without them and what depends on them. Their ids; the issues hold one note (code `skipped`) for each. Such a
    // view is never installed: a build refuses any error.
    std::vector<std::string> skipped;
    // What the view build found: one note (code `skipped`) per object left out, and the errors its rounds reached
    // that the full lowering had stopped before. Kept apart from the validation's issues, which do not depend on
    // whether a view was asked for.
    std::vector<ProjectIssue> skippedIssues;
};

// validateProject with what is known: `pPrevious` the parts of the project's last validation and `pChanged` the
// files that changed since (both null: everything is checked). Gives the same issues, in the same order, as
// validateProject; fills `parts` and, when given, `pViews`.
void validateProjectParts(
    const Project &project,
    const BuildOptions &options,
    const ValidationParts *pPrevious,
    const std::set<std::string> *pChanged,
    ValidationParts &parts,
    std::vector<ProjectIssue> &issues,
    ValidationViews *pViews);

// What to tell the author of a project whose `world` the asset root does not hold (no worlds/<world> folder): the
// files check and build, but nothing can read the built map. Empty when the world is there, or without an asset
// root.
std::string missingWorldNote(const Project &project, const std::filesystem::path &assetRoot);

// Compiles a project to its map files: <stem>.blv, <stem>.scene.yml, <stem>.lua, the compiler inputs under source/
// and build.json. True when the map was built (and, unless dryRun, written) without issues.
bool buildProject(const Project &project, const BuildOptions &options, BuildResult &result);

// Copies a built map into an asset root (worlds/<world>/maps and events/maps) and adds or replaces its row in the
// root's engine/data_tables/map_stats.txt. For scratch roots: files are replaced by rename, never edited in place.
// Copies a built map into a mount folder (the game's --extra-mount, `oymap ... --mount`): the folder is made if it
// is missing, and for a new map it gets a fresh copy of the asset root's map_stats.txt with the map's row.
bool installBuildIntoMount(
    const Project &project,
    const std::filesystem::path &buildDirectory,
    const std::filesystem::path &mountRoot,
    const std::filesystem::path &assetRoot,
    std::vector<std::string> &installedFiles,
    std::string &errorMessage,
    bool statsOptional = false);

bool installBuild(
    const Project &project,
    const std::filesystem::path &buildDirectory,
    const std::filesystem::path &assetRoot,
    std::vector<std::string> &installedFiles,
    std::string &errorMessage,
    // For reading a build back with oymap only: a project without a map_stats block installs without a row (the
    // game could not enter such a map).
    bool statsOptional = false,
    // The asset root whose world.yml says whether the world owns its maps' rows (idRanges.maps); default
    // `assetRoot`. A mount passes the root it lies over, as the mount has no world.yml.
    const std::filesystem::path *pManifestRoot = nullptr);
}
