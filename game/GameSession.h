#pragma once

#include "game/EventRuntime.h"
#include "game/SaveGame.h"
#include "game/scene/SceneKind.h"

#include <filesystem>
#include <optional>
#include <string>
#include <unordered_map>

namespace OpenYAMM::Game
{
class ClassSkillTable;
class ItemTable;
class SpecialItemEnchantTable;
class StandardItemEnchantTable;

class GameSession
{
public:
    void clear();

    const std::optional<Party> &partyState() const;
    std::optional<Party> &partyState();
    void setPartyState(const Party &party);
    void setPartyState(Party &&party);

    SceneKind currentSceneKind() const;
    void setCurrentSceneKind(SceneKind sceneKind);

    bool hasCurrentMapFileName() const;
    const std::string &currentMapFileName() const;
    void setCurrentMapFileName(const std::string &mapFileName);
    void setCurrentMapFileName(std::string &&mapFileName);

    const std::optional<OutdoorPartyRuntime::Snapshot> &outdoorPartyState() const;
    void setOutdoorPartyState(const OutdoorPartyRuntime::Snapshot &snapshot);
    void setOutdoorPartyState(OutdoorPartyRuntime::Snapshot &&snapshot);

    const std::optional<OutdoorWorldRuntime::Snapshot> &currentOutdoorWorldState() const;
    void setCurrentOutdoorWorldState(const OutdoorWorldRuntime::Snapshot &snapshot);
    void setCurrentOutdoorWorldState(OutdoorWorldRuntime::Snapshot &&snapshot);

    const std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> &outdoorWorldStates() const;
    std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> &outdoorWorldStates();
    void storeOutdoorWorldState(const std::string &mapFileName, const OutdoorWorldRuntime::Snapshot &snapshot);

    const std::optional<IndoorSceneRuntime::Snapshot> &currentIndoorSceneState() const;
    void setCurrentIndoorSceneState(const IndoorSceneRuntime::Snapshot &snapshot);
    void setCurrentIndoorSceneState(IndoorSceneRuntime::Snapshot &&snapshot);

    const std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> &indoorSceneStates() const;
    std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> &indoorSceneStates();
    void storeIndoorSceneState(const std::string &mapFileName, const IndoorSceneRuntime::Snapshot &snapshot);

    void setOutdoorCameraAngles(float yawRadians, float pitchRadians);
    float outdoorCameraYawRadians() const;
    float outdoorCameraPitchRadians() const;

    const std::optional<std::filesystem::path> &currentSavePath() const;
    void setCurrentSavePath(const std::filesystem::path &path);
    void clearCurrentSavePath();

    const std::optional<EventRuntimeState::PendingMapMove> &pendingMapMove() const;
    void setPendingMapMove(const EventRuntimeState::PendingMapMove &pendingMapMove);
    void setPendingMapMove(EventRuntimeState::PendingMapMove &&pendingMapMove);
    std::optional<EventRuntimeState::PendingMapMove> consumePendingMapMove();
    void clearPendingMapMove();

    void captureOutdoorRuntimeState(
        const std::string &mapFileName,
        const Party &party,
        const OutdoorPartyRuntime::Snapshot &partySnapshot,
        const OutdoorWorldRuntime::Snapshot &worldSnapshot,
        float yawRadians,
        float pitchRadians
    );

    void captureIndoorRuntimeState(
        const std::string &mapFileName,
        const Party &party,
        const IndoorSceneRuntime::Snapshot &snapshot
    );

    std::optional<GameSaveData> buildSaveData() const;
    void restoreFromSaveData(
        const GameSaveData &saveData,
        const ItemTable &itemTable,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const ClassSkillTable &classSkillTable
    );

private:
    std::optional<Party> m_partyState;
    SceneKind m_currentSceneKind = SceneKind::Outdoor;
    std::string m_currentMapFileName;
    std::optional<OutdoorPartyRuntime::Snapshot> m_outdoorPartyState;
    std::optional<OutdoorWorldRuntime::Snapshot> m_currentOutdoorWorldState;
    std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> m_outdoorWorldStates;
    std::optional<IndoorSceneRuntime::Snapshot> m_currentIndoorSceneState;
    std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> m_indoorSceneStates;
    float m_outdoorCameraYawRadians = 0.0f;
    float m_outdoorCameraPitchRadians = 0.0f;
    std::optional<std::filesystem::path> m_currentSavePath;
    std::optional<EventRuntimeState::PendingMapMove> m_pendingMapMove;
};
}
