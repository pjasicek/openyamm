#pragma once

#include "core/IndoorLowering.h"
#include "core/Json.h"
#include "core/MapLoad.h"
#include "core/Project.h"

#include "game/indoor/IndoorMapData.h"
#include "game/maps/IndoorSceneYml.h"

#include <yaml-cpp/yaml.h>

#include <filesystem>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// Overlay projects that change a shipped map's scene (devdocs/map_studio/S6_PLAN.md, item O): objects.yml `scene`
// (new pulsing lights, ambient sounds, spawn points, destructibles, water volumes and ladders; changes to and removals
// of the base map's own; since S8a also new monsters and floor items, which the game appends after the base map's)
// and atmosphere.yml's scene blocks (`open_sky`, `scene_fog`, `daylight`, `terrain`, `mist`), written
// as the indoor scene overlay `<stem>_<project id>.scene.yml` the game applies after the base scene. A list key in an
// overlay replaces the base scene's list, so each list the project touches is written whole: the base map's entries
// with the changes and removals, then the additions.

// The base map's scene things under stable ids, for `oymap import` to put into ids.lock.yml: pulsing lights by key
// (`light:k<key>` in `lights`), ambient sounds by key (`sound:a<key>` in `sounds`), destructibles by id
// (`destructible:k<id>`), water volumes by their place in the list (`water:<name>`), spawn points by index
// (`spawn:s<index>`), ladders by their place in the list (`ladder:<id>`).
void lockBaseSceneThings(const Game::IndoorSceneData &scene, YAML::Node &lock);

// The base map's cinematics (the text of its `<stem>.cinematics.yml`, read by the game's parser) by their place in the
// file (`cinematic:<name>` in `cinematics`): a wiring cinematic of that id replaces the shipped one (S8a).
void lockBaseCinematics(const std::string &cinematicsText, YAML::Node &lock);

// The names of the base map's own cinematics (its `<stem>.cinematics.yml` in the session's asset root), in order.
std::vector<std::string> baseCinematicNames(const AssetSession &session, const std::string &stem);

// The world's own rows of the tables an overlay's monsters and items are named in (its world.yml `tableContributions`
// that append to monster_data, monster_descriptors and items), added to `options` after the engine's as the game
// composes them, so that an overlay of an MM9 map places MM9's monsters (S8a). Read from the asset root's folders.
void addWorldTableRows(const std::filesystem::path &assetRoot, const std::string &world, LoweringOptions &options);

// What an overlay project's lowering needs of its base map (LoweringOptions overlayFirstActor, overlayBaseGroups):
// the base scene's own actors (`baseSceneText`, without overlays) and those of the world's scene overlays the game
// applies before the project's own (`<stem>_<project id>.scene.yml`, by name), and the groups of those actors and
// spawn points.
void readOverlayBase(
    const Project &project,
    const AssetSession &session,
    const LoadedMap &map,
    const std::string &baseSceneText,
    LoweringOptions &options);

// The profile a shipped BLV is of: `region` (open to the sky, with terrain: MM9's wilderness), `city` (open to the sky
// without terrain), else `dungeon`.
std::string indoorSceneProfile(const Game::IndoorSceneData &scene);

// Whether the project says anything the scene overlay holds.
bool projectChangesScene(const Project &project);

// What can be checked without the base map: the words only an overlay may use, the words of a change that fit the kind
// of the thing it names, a thing changed and removed at once, a removal that names no base thing.
void checkSceneOverlayWords(const Project &project, std::vector<ProjectIssue> &issues);

struct SceneOverlayText
{
    std::string text;
    // The overlay's top-level keys, in order (pulsing_lights, ambient_sounds ...).
    std::vector<std::string> keys;
    size_t added = 0;
    size_t changed = 0;
    size_t removed = 0;
};

// Writes the overlay from the base scene's own text (without other overlays) and the base map's geometry (the faces of
// a destructible's cog, its centre; the sectors of added monsters and items). New things get their numbers in `lock`
// (lights from 49001, sounds and destructibles from 60001). `lowered` (lowerOverlayProject) holds the monsters, items
// and ladders the overlay adds.
bool buildSceneOverlayText(
    const Project &project,
    const std::string &baseSceneText,
    const Game::IndoorMapData &baseMap,
    const LoweredIndoorMap &lowered,
    IdsLock &lock,
    SceneOverlayText &result,
    std::vector<ProjectIssue> &issues,
    std::vector<std::string> &warnings);

// view.overlay (S6_PLAN.md item O): an overlay project's scene things for the plan view: the base map's pulsing
// lights, ambient sounds, destructibles, water volumes and spawn points with what the project does to each (kept,
// changed, removed), and the project's own additions, each with its id and place (whole map units), and the base map's
// bounds and profile. Fails with `errorKind` bad_request (not an overlay of a BLV), no_such_map or failed.
bool describeSceneOverlay(
    const Project &project,
    const std::filesystem::path &assetRoot,
    JsonWriter &writer,
    std::string &errorKind,
    std::string &errorMessage);
}
