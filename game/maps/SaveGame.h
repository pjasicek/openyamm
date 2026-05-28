#pragma once

#include "game/scene/IndoorSceneRuntime.h"
#include "game/mm9/Mm9ScriptRuntime.h"
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
struct GameSaveData
{
    SceneKind currentSceneKind = SceneKind::Outdoor;
    std::string mapFileName;
    Party::Snapshot party;
    std::unordered_map<std::string, int32_t> namedGlobalVars;
    Mm9ScriptRuntimeState mm9ScriptState;
    bool hasOutdoorRuntimeState = false;
    OutdoorPartyRuntime::Snapshot outdoorParty;
    OutdoorWorldRuntime::Snapshot outdoorWorld;
    std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> outdoorWorldStates;
    bool hasIndoorSceneState = false;
    IndoorSceneRuntime::Snapshot indoorScene;
    std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> indoorSceneStates;
    float savedGameMinutes = 0.0f;
    float outdoorCameraYawRadians = 0.0f;
    float outdoorCameraPitchRadians = 0.0f;
    std::string saveName;
    std::vector<uint8_t> previewBmp;
};

bool saveGameDataToPath(const std::filesystem::path &path, const GameSaveData &data, std::string &error);
std::optional<GameSaveData> loadGameDataFromPath(const std::filesystem::path &path, std::string &error);
bool compareSavePathsForDisplay(const std::filesystem::path &left, const std::filesystem::path &right);
}
