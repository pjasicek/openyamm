#pragma once

#include "core/MapExport.h"

#include "engine/AssetFileSystem.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/IndoorSceneYml.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/outdoor/OutdoorMapData.h"

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// A shipped or installed map as the game reads it: geometry, the scene file with its overlays applied, the state
// built from them, and the map's event script with its overlays. Read through the engine's asset file system and the
// game's own parsers, so what an audit sees is what the game runs.
struct LoadedMap
{
    std::string world;
    std::string fileName;
    std::string stem;
    MapKind kind = MapKind::Unknown;
    std::optional<Game::IndoorMapData> indoor;
    std::optional<Game::OutdoorMapData> outdoor;
    std::optional<Game::IndoorSceneData> indoorScene;
    std::optional<Game::OutdoorSceneData> outdoorScene;
    // Doors, actors, chests and variables as the map starts.
    std::optional<Game::MapDeltaData> state;
    std::string scenePath;
    std::vector<std::string> sceneOverlayPaths;
    // The map's own <stem>.cinematics.yml (without its cinematics overlays), when it has one.
    std::optional<std::string> cinematicsText;
    // The map's own script and its overlays, joined as the game joins them, without the support scripts.
    std::string scriptText;
    std::vector<std::string> scriptPaths;
    // What the game runs: the support script, the world's common scripts and scriptText.
    std::string fullScriptSource;
    std::optional<Game::ScriptedEventProgram> events;
    // Problems that did not stop the load (a map without a scene or a script, a script that does not run).
    std::vector<std::string> warnings;
};

// One asset root opened for one world, as the game mounts it. PhysicsFS is one per process: open one at a time.
class AssetSession
{
public:
    bool open(const std::filesystem::path &assetRoot, const std::string &world, std::string &errorMessage);
    // A build's mount folder (`oymap install --mount`) read in front of every asset root opened after this call, as
    // the game's --extra-mount does. Empty: none.
    static void setExtraMount(const std::filesystem::path &mountRoot);
    const Engine::AssetFileSystem &files() const;
    const std::string &world() const;

private:
    Engine::AssetFileSystem m_files;
    std::string m_world;
};

// The support script and the world's common scripts, as they stand in front of every map script of the session's
// world. Empty when the asset root has none.
std::string loadScriptSupport(const AssetSession &session);

// Loads `<file>` (an .odm or .blv name) of the session's world under Standard rules.
bool loadMap(const AssetSession &session, const std::string &fileName, LoadedMap &map, std::string &errorMessage);
}
