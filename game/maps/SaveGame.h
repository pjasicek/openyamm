#pragma once

#include "game/scene/IndoorSceneRuntime.h"
#include "game/scene/SceneKind.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/party/Party.h"

#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;
class HouseTable;

struct GameSaveData
{
    SceneKind currentSceneKind = SceneKind::Outdoor;
    std::string mapFileName;
    Party::Snapshot party;
    std::unordered_map<std::string, int32_t> namedGlobalVars;
    bool hasOutdoorRuntimeState = false;
    OutdoorPartyRuntime::Snapshot outdoorParty;
    OutdoorWorldRuntime::Snapshot outdoorWorld;
    std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> outdoorWorldStates;
    bool hasIndoorSceneState = false;
    IndoorSceneRuntime::Snapshot indoorScene;
    std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> indoorSceneStates;
    float savedGameMinutes = 0.0f;
    // Camera angles of the current scene (outdoor or indoor). Saves older than SaveVersionIndoorCamera stored only the
    // outdoor camera, so for them the angles are valid only when the save was made outdoors.
    float cameraYawRadians = 0.0f;
    float cameraPitchRadians = 0.0f;
    bool cameraAnglesValid = false;
    bool heldInventoryItemActive = false;
    InventoryItem heldInventoryItem = {};
    uint8_t heldInventoryItemGrabCellOffsetX = 0;
    uint8_t heldInventoryItemGrabCellOffsetY = 0;
    float heldInventoryItemGrabOffsetX = 0.0f;
    float heldInventoryItemGrabOffsetY = 0.0f;
    std::unordered_map<std::string, uint32_t> requiredContentPackages;
    std::string saveName;
    std::vector<uint8_t> previewBmp;
};

void migrateLegacyConsumedCorpseMarkers(GameSaveData &data, uint32_t sourceSaveVersion);
bool saveGameDataToPath(const std::filesystem::path &path, const GameSaveData &data, std::string &error);
std::optional<GameSaveData> loadGameDataFromPath(const std::filesystem::path &path, std::string &error);
std::unordered_map<std::string, uint32_t> collectRequiredContentPackages(
    const GameSaveData &data,
    const ItemTable &itemTable,
    const HouseTable &houseTable,
    const std::unordered_map<std::string, uint32_t> &loadedPackageSchemas);
bool validateRequiredContentPackages(
    const GameSaveData &data,
    const ItemTable &itemTable,
    const HouseTable &houseTable,
    const std::unordered_map<std::string, uint32_t> &loadedPackageSchemas,
    std::string &error);
bool compareSavePathsForDisplay(const std::filesystem::path &left, const std::filesystem::path &right);
}
