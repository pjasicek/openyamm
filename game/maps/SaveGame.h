#pragma once

#include "game/scene/IndoorSceneRuntime.h"
#include "game/scene/SceneKind.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/party/Party.h"

#include <filesystem>
#include <optional>
#include <string>
#include <unordered_map>

namespace OpenYAMM::Game
{
struct GameSaveData
{
    SceneKind currentSceneKind = SceneKind::Outdoor;
    std::string mapFileName;
    Party::Snapshot party;
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
};

bool saveGameDataToPath(const std::filesystem::path &path, const GameSaveData &data, std::string &error);
std::optional<GameSaveData> loadGameDataFromPath(const std::filesystem::path &path, std::string &error);
}
