#pragma once

// Walk mode (S5_BROWSER_EDITOR.md 2.10, 3.6; D7): the game's own movement controllers (IndoorMovementController,
// OutdoorMovementController, compiled in place) moving a party of the game's size over a built map, fed from bytes
// so that the browser's WebAssembly worker runs it without a file system of its own. Collision is the game's; events,
// monsters and traps do not run, doors move only when toggled.
//
// What a walk reads, all written by the build beside the map (`oymap build`):
//   <stem>.blv|.odm          the built map
//   <stem>.walk.yml          the movement state: the scene as the game reads it without what movement never reads
//                            (actors, sprite objects, chests, spawns, lights, sounds), after a block of the studio's
//                            own (`studio_walk`: the party's size, the doors by project id, the rooms by sector, an
//                            outdoor map's bounds)
//   <stem>.walk.terrain      outdoors: the terrain pack (the tile attributes and the land mask the game derives from
//                            the asset root's tile tables)
// and the asset root's engine/data_tables/decoration_data.txt (the decorations' sizes).
//
// The walk's input turns the yaw into a direction with the core's own sin and cos (core/CoreMath.h), so a recorded
// walk gives the same poses, bit for bit, in the native and the WebAssembly core (S5-0 spike 3: C-library sinf and
// cosf differ between glibc and musl and drift a walk for a few dozen frames).

#include "game/outdoor/OutdoorMapData.h"

#include <yaml-cpp/yaml.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Studio
{
// The keys held, as the game's movement keys.
enum WalkButton : uint32_t
{
    WalkForward = 1,
    WalkBackward = 2,
    WalkLeft = 4,
    WalkRight = 8,
    WalkRun = 16,
    WalkJump = 32,
};

struct WalkPose
{
    float x = 0.0f;
    float y = 0.0f;
    float footZ = 0.0f;
    float eyeZ = 0.0f;
    float verticalVelocity = 0.0f;
    bool grounded = false;
    // Landed during the last step.
    bool landed = false;
    // Indoors: the sector of the feet and of the eye; -1 outdoors or nowhere.
    int32_t sector = -1;
    int32_t eyeSector = -1;
    // The face under the feet: indoors the map's face, outdoors the model's face (model >= 0) or -1 on the terrain or
    // in the air.
    int32_t model = -1;
    int32_t face = -1;
    // Outdoors: standing on water (deep water on the terrain, or a fluid face).
    bool onWater = false;
};

// A door, lift or mover of the project: its id and the map's mechanisms (door numbers) it moves.
struct WalkDoor
{
    std::string id;
    std::vector<uint32_t> mechanisms;
    bool open = false;
};

struct WalkParty
{
    float radius = 37.0f;
    float height = 160.0f;
    float eyeHeight = 160.0f;
    float maxStepHeight = 128.0f;
};

class WalkSession
{
public:
    WalkSession();
    ~WalkSession();

    // mapBytes: the built BLV or ODM; stateText: <stem>.walk.yml; decorationTableText: decoration_data.txt;
    // terrainPack: <stem>.walk.terrain (outdoors only).
    bool load(const std::vector<uint8_t> &mapBytes, const std::string &stateText,
        const std::string &decorationTableText, const std::vector<uint8_t> &terrainPack, std::string &errorMessage);

    bool loaded() const;
    bool outdoor() const;
    const WalkParty &party() const;
    const std::vector<WalkDoor> &doors() const;
    size_t faceCount() const;
    size_t decorationColliderCount() const;
    // Indoors: the room a sector belongs to ("" for none).
    std::string roomOfSector(int32_t sector) const;

    // Puts the party where an eye at (x, y, eyeZ) would be; the next steps let it settle as the game does.
    WalkPose placeEye(float x, float y, float eyeZ);
    // One frame of the given length: the game's accumulator and 1/128 s movement steps.
    WalkPose step(float yawRadians, uint32_t buttons, float frameSeconds);
    WalkPose pose() const;
    // Opens a shut door (or lift, or mover) at once, or shuts an open one: its end state, as an event would leave it.
    // nullopt when the map has no such door, or outdoors (moving models are not toggled in walk mode).
    std::optional<bool> toggle(const std::string &doorId);

private:
    struct Impl;
    std::unique_ptr<Impl> m_pImpl;
};

// The pose's floats as their bits (x, y, foot, vertical velocity), eight hex digits each: what a replay compares.
std::string walkPoseBits(const WalkPose &pose);

// --- written by the build -------------------------------------------------------------------------------------------

struct WalkStateHeader
{
    std::string kind;
    std::string world;
    std::string map;
    WalkParty party;
    std::vector<WalkDoor> doors;
    // Indoors: sector number and room id.
    std::vector<std::pair<int, std::string>> rooms;
    // Outdoors: min x, max x, min y, max y of the map's travel bounds, when it has them.
    std::optional<std::array<int, 4>> bounds;
    // Outdoors: the faces whose attributes the scene changes from the map's (model, face, attributes). Movement reads
    // nothing else of the scene's face entries, so these stand in for them (Harmondale: 520 KB of 760).
    std::optional<std::vector<std::array<uint32_t, 3>>> faceAttributes;
};

// <stem>.walk.yml: the header, then the scene without the parts movement never reads. `scene` is not changed.
std::string writeWalkStateText(const WalkStateHeader &header, const YAML::Node &scene);

// The game's party sizes for a world: outdoors world.yml's partyMovement when it declares one, else the MM6-MM8
// defaults; indoors the indoor body.
WalkParty walkPartyOfWorld(const std::filesystem::path &assetRoot, const std::string &world, bool outdoor);

// <stem>.walk.terrain: "OYWT", the attribute map's size and bytes (after the tile table's flags), the land mask's size
// and bytes (1 for land, 0 for water), sizes as little-endian uint32. Empty when the tile tables do not load.
std::vector<uint8_t> writeWalkTerrainPack(const Engine::AssetFileSystem &files, Game::OutdoorMapData map);

// The faces of `scened` (the map with its scene applied) whose attributes differ from `plain` (the map's bytes alone).
std::vector<std::array<uint32_t, 3>> walkFaceAttributeChanges(const Game::OutdoorMapData &plain,
    const Game::OutdoorMapData &scened);
}
