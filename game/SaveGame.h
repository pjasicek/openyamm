#pragma once

#include "game/OutdoorPartyRuntime.h"
#include "game/OutdoorWorldRuntime.h"
#include "game/Party.h"

#include <filesystem>
#include <optional>
#include <string>
#include <unordered_map>

namespace OpenYAMM::Game
{
struct GameSaveData
{
    std::string mapFileName;
    Party::Snapshot party;
    OutdoorPartyRuntime::Snapshot outdoorParty;
    OutdoorWorldRuntime::Snapshot outdoorWorld;
    std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> outdoorWorldStates;
    float outdoorCameraYawRadians = 0.0f;
    float outdoorCameraPitchRadians = 0.0f;
};

bool saveGameDataToPath(const std::filesystem::path &path, const GameSaveData &data, std::string &error);
std::optional<GameSaveData> loadGameDataFromPath(const std::filesystem::path &path, std::string &error);
}
