#pragma once

#include "game/indoor/IndoorMovementController.h"
#include "game/party/Party.h"

namespace OpenYAMM::Game
{
class ItemTable;

class IndoorPartyRuntime
{
public:
    struct Snapshot
    {
        IndoorMoveState movementState = {};
    };

    IndoorPartyRuntime(IndoorMovementController movementController, const ItemTable &itemTable);

    void initializeEyePosition(float x, float y, float z, bool resetParty = true);
    void initializePartyPosition(float x, float y, float z, bool resetParty = true);
    void teleportEyePosition(float x, float y, float z);
    void teleportPartyPosition(float x, float y, float z);
    void update(float desiredVelocityX, float desiredVelocityY, bool jumpRequested, float deltaSeconds);

    const IndoorMoveState &movementState() const;
    const Party &party() const;
    Party &party();
    void setParty(const Party &party);
    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);
    void setMovementSpeedMultiplier(float multiplier);

private:
    IndoorMovementController m_movementController;
    Party m_party;
    IndoorMoveState m_movementState = {};
    float m_movementSpeedMultiplier = 1.0f;
};
}
