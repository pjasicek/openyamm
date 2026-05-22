#pragma once

#include "game/indoor/IndoorMovementController.h"
#include "game/party/Party.h"

#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class ItemTable;

class IndoorPartyRuntime
{
public:
    struct Snapshot
    {
        IndoorMoveState movementState = {};
        float movementAccumulatorSeconds = 0.0f;
        bool pendingJumpRequested = false;
        float pendingImpulseVelocityX = 0.0f;
        float pendingImpulseVelocityY = 0.0f;
        float pendingImpulseVelocityZ = 0.0f;
        bool alwaysRunEnabled = true;
    };

    IndoorPartyRuntime(IndoorMovementController movementController, const ItemTable &itemTable);

    void initializeEyePosition(float x, float y, float z, bool resetParty = true);
    void initializePartyPosition(float x, float y, float z, bool resetParty = true);
    void teleportEyePosition(float x, float y, float z);
    void teleportPartyPosition(float x, float y, float z);
    void translatePartyPosition(float deltaX, float deltaY, float deltaZ);
    void update(
        float desiredVelocityX,
        float desiredVelocityY,
        bool jumpRequested,
        bool running,
        float deltaSeconds,
        bool turnBasedMovementStep = false);
    void setActorColliders(const std::vector<IndoorActorCollision> &actorColliders);
    void setDecorationColliders(const std::vector<IndoorCylinderCollision> &decorationColliders);
    void setSpriteObjectColliders(const std::vector<IndoorCylinderCollision> &spriteObjectColliders);
    void applyMechanismGeometryUpdate(const std::vector<uint32_t> &changedDoorIds);
    void invalidateRuntimeGeometryCache();

    const IndoorMoveState &movementState() const;
    const Party &party() const;
    Party &party();
    const std::string &movementStatusText() const;
    float partyX() const;
    float partyY() const;
    float partyFootZ() const;
    void setParty(const Party &party);
    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);
    void setMovementSpeedMultiplier(float multiplier);
    void setAlwaysRunEnabled(bool enabled);
    void setCollisionTraceEnabled(bool enabled, std::string mapName);
    bool alwaysRunEnabled() const;
    void syncSpellMovementStatesFromPartyBuffs();
    void requestJump(std::optional<float> verticalVelocity = std::nullopt, float lift = 1.0f);
    void requestSpecialJump(float velocityX, float velocityY, float velocityZ);

private:
    IndoorMovementController m_movementController;
    Party m_party;
    IndoorMoveState m_movementState = {};
    float m_movementSpeedMultiplier = 1.0f;
    bool m_alwaysRunEnabled = true;
    bool m_collisionTraceEnabled = false;
    std::string m_collisionTraceMapName;
    float m_collisionTraceClockSeconds = 0.0f;
    float m_nextCollisionTraceSeconds = 0.0f;
    float m_movementAccumulatorSeconds = 0.0f;
    bool m_pendingJumpRequested = false;
    float m_pendingImpulseVelocityX = 0.0f;
    float m_pendingImpulseVelocityY = 0.0f;
    float m_pendingImpulseVelocityZ = 0.0f;
    std::optional<float> m_pendingJumpVelocity;
    float m_pendingJumpLift = 1.0f;
    float m_burningDamageTimerSeconds = 0.0f;
    std::string m_movementStatusText;
};
}
