#pragma once

#include "game/events/EventRuntime.h"
#include "game/outdoor/OutdoorMovementDriver.h"
#include "game/party/Party.h"

#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class ItemTable;
struct GameplayWorldMovementFrameDiagnostics;

class OutdoorPartyRuntime
{
public:
    struct Snapshot
    {
        OutdoorMoveState movementState = {};
        OutdoorPartyMovementState partyMovementState = {};
    };

    OutdoorPartyRuntime(OutdoorMovementDriver movementDriver, const ItemTable &itemTable);

    void initialize(float x, float y, float footZHint, bool resetParty = true);
    // keepHeight: the party is placed at footZHint in the air and falls from there (a fall from the sky).
    void teleportTo(float x, float y, float footZHint, bool keepHeight = false);
    void update(
        const OutdoorMovementInput &input,
        float deltaSeconds,
        GameplayWorldMovementFrameDiagnostics *pPerformanceDiagnostics = nullptr);
    void setActorColliders(const std::vector<OutdoorActorCollision> &actorColliders);
    void setHiddenDecorationEntities(const std::vector<bool> &hiddenEntities);
    void setFaceAttributes(size_t bModelIndex, size_t faceIndex, uint32_t attributes);
    void updateFaceGeometries(const std::vector<OutdoorFaceGeometryData> &geometries);
    bool translateWithSupportedBModel(size_t bModelIndex, float deltaX, float deltaY, float deltaZ);
    void lift(float height);
    // Adds this horizontal velocity to every movement step for `seconds`, with the world's collision (a charge).
    void requestDash(float velocityX, float velocityY, float seconds);
    void applyEventRuntimeState(const EventRuntimeState &runtimeState, bool grantItemsToInventory = true);

    const OutdoorMoveState &movementState() const;
    const OutdoorMovementEvents &movementEvents() const;
    const OutdoorMovementConsequences &movementConsequences() const;
    const OutdoorPartyMovementState &partyMovementState() const;
    const Party &party() const;
    Party &party();
    const std::string &movementStatusText() const;
    float partyX() const;
    float partyY() const;
    float partyFootZ() const;
    float partyEyeZ() const;
    void setParty(const Party &party);
    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);

    void toggleRunning();
    void toggleFlying();
    void requestLanding();
    void toggleWaterWalk();
    void toggleFeatherFall();
    void setRunning(bool active);
    void setDebugFlyingOverride(bool active);
    // Underwater (MM7's Shoals: OY-350) the party swims: it moves up and down freely, without gravity or falls.
    void setUnderwater(bool active);
    void setMovementSpeedMultiplier(float multiplier);
    void setBodyDimensions(float radius, float height, float maxStepHeight = 128.0f);
    // Camera height over the feet (world.yml partyMovement.eyeHeight; the MM6-MM8 default otherwise).
    void setEyeHeight(float eyeHeight);
    void setCollisionTraceEnabled(bool enabled, const std::string &mapName);
    void syncSpellMovementStatesFromPartyBuffs();
    void requestJump(std::optional<float> verticalVelocity = std::nullopt, float lift = 1.0f);
    void requestSpecialJump(float velocityX, float velocityY, float velocityZ);

private:
    OutdoorMovementDriver m_movementDriver;
    float m_eyeHeight = 176.0f;
    Party m_party;
    std::string m_movementStatusText;
    bool m_debugFlyingOverride = false;
    bool m_underwater = false;
};
}
