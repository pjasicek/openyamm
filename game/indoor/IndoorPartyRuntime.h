#pragma once

#include "game/indoor/IndoorMovementController.h"
#include "game/indoor/IndoorWater.h"
#include "game/party/Party.h"

#include <array>
#include <optional>
#include <string>
#include <vector>

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
        // Whether the party has been under water and is in a surface jump (saved, so a load in the water swims on as
        // before it); none: guessed on restore, as a placement in the water is.
        std::optional<IndoorSwimMemory> swimMemory;
    };

    IndoorPartyRuntime(IndoorMovementController movementController, const ItemTable &itemTable);

    void initializeEyePosition(float x, float y, float z, bool resetParty = true);
    void initializePartyPosition(float x, float y, float z, bool resetParty = true);
    void teleportEyePosition(float x, float y, float z);
    void teleportPartyPosition(float x, float y, float z);
    // Whether the party's body fits at a foot position: inside the map's rooms and clear of every face.
    bool partyFitsAt(float x, float y, float footZ) const;
    void translatePartyPosition(float deltaX, float deltaY, float deltaZ);
    // A moving face pushes the party (a rotating mover's push rule): moved, no longer supported, falling from there.
    void pushPartyPosition(float deltaX, float deltaY, float deltaZ);
    // Raises the party in place; it falls back from there (MAW's unstuck key).
    void lift(float height);
    void update(
        float desiredVelocityX,
        float desiredVelocityY,
        bool jumpRequested,
        bool runningMovement,
        float deltaSeconds,
        bool turnBasedMovementStep = false,
        bool turnBasedPhysicsStep = false);
    void setActorColliders(const std::vector<IndoorActorCollision> &actorColliders);
    void setDecorationColliders(const std::vector<IndoorCylinderCollision> &decorationColliders);
    void setSpriteObjectColliders(const std::vector<IndoorCylinderCollision> &spriteObjectColliders);
    void applyMechanismGeometryUpdate(const std::vector<uint32_t> &changedDoorIds);
    void invalidateRuntimeGeometryCache();

    const IndoorMoveState &movementState() const;
    // Fly Up/Fly Down while on a ladder: +1, -1 or 0 (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md, "Ladders").
    void setLadderVerticalInput(int verticalInput);
    bool climbingLadder() const;
    // Swimming (scene `water_volumes`, devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md): the look direction and the
    // movement keys for the next update; ignored on a map without water volumes.
    void setSwimInput(const IndoorSwimInput &input);
    IndoorSwimState swimState() const
    {
        return m_swimState;
    }
    // In deep water, on the bed or at the surface: Fly Up and Fly Down swim (the flight arrows show).
    bool swimming() const;
    // The volume the eye point is in after the last update, or null.
    const IndoorWaterVolume *eyeWaterVolume() const;
    bool eyeUnderWater() const
    {
        return m_eyeUnderWater;
    }
    // The breath left (1 full) while the eye is under water; none out of it.
    std::optional<float> breathFraction() const;
    // Drowning ticks taken since the map was entered.
    uint32_t drowningTicks() const
    {
        return m_drowningTicks;
    }
    // Moves out the water sounds (splash, out of the water, drowning) since the last call, by name.
    void takeWaterSounds(std::vector<std::string> &sounds);
    // Moves out the floor faces stood on during movement steps since the last call, in order, so pressure plates
    // see every face crossed instead of only the frame's final one.
    void takeSteppedFloorFaces(std::vector<size_t> &faces);
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
    // Per face: the speed share while the party stands on it (shallow liquids it wades through); empty: none.
    void setFaceWadeSpeeds(std::vector<float> speeds);
    // The map lies open to the sky (world.yml openAirMaps): its falls and other movement damage count as outdoors.
    void setOpenAir(bool openAir);
    void setAlwaysRunEnabled(bool enabled);
    void setCollisionTraceEnabled(bool enabled, std::string mapName);
    bool alwaysRunEnabled() const;
    // Whether the last update moved the party running (footstep sounds).
    bool runningMovement() const
    {
        return m_runningMovement;
    }
    void syncSpellMovementStatesFromPartyBuffs();
    void requestJump(std::optional<float> verticalVelocity = std::nullopt, float lift = 0.0f);
    void requestSpecialJump(float velocityX, float velocityY, float velocityZ);
    // Adds this horizontal velocity to every movement step for `seconds`, with the world's collision (a charge).
    void requestDash(float velocityX, float velocityY, float seconds);

private:
    // One movement step on a ladder (grabbing it first when the party walks into one); false: walk normally.
    bool stepOnLadder(
        float desiredVelocityX,
        float desiredVelocityY,
        bool runningMovement,
        const IndoorBodyDimensions &body,
        std::vector<size_t> &contactedActorIndices);
    // Starts the short glide onto a ladder taken at its top or off its top onto the exit, and steps it.
    void startLadderGlide(float toX, float toY, float toFootZ, std::optional<size_t> ontoLadderIndex);
    void stepLadderGlide(const IndoorBodyDimensions &body);
    // One movement step swimming, at the surface or jumping out of it; false: the party walks or falls as on land
    // (dry, wading, walking on the bed, falling in before the eye goes under).
    bool stepInWater(
        float speedMultiplier,
        const IndoorBodyDimensions &body,
        std::vector<size_t> &contactedActorIndices);
    // The breath, drowning and the crossing sounds after an update's steps.
    void updateWaterBreath(float deltaSeconds);
    void resetWaterState(bool refillBreath);
    void keepPlacementInWater(float requestedFootZ, const IndoorBodyDimensions &body);
    bool waterActive() const;
    std::optional<IndoorWaterSample> bodyWaterSample(
        const IndoorMoveState &state,
        const IndoorBodyDimensions &body) const;

    IndoorMovementController m_movementController;
    // Runtime only: a save made on a ladder restores the party falling from where it was.
    std::optional<size_t> m_ladderIndex;
    int m_ladderVerticalInput = 0;
    // Runtime only: the party glides between the floor and a ladder's top instead of jumping there. Its path rises
    // or falls at the higher end, so it never cuts through the edge of the floor.
    struct LadderGlide
    {
        std::array<float, 3> from = {};
        std::array<float, 3> corner = {};
        std::array<float, 3> to = {};
        float seconds = 0.0f;
        float duration = 0.0f;
        // The ladder the party holds at the end; none: it stands on the top exit.
        std::optional<size_t> ontoLadderIndex;
    };
    std::optional<LadderGlide> m_ladderGlide;
    Party m_party;
    IndoorMoveState m_movementState = {};
    float m_movementSpeedMultiplier = 1.0f;
    std::vector<float> m_faceWadeSpeeds;
    bool m_openAir = false;
    bool m_alwaysRunEnabled = true;
    bool m_runningMovement = false;
    bool m_collisionTraceEnabled = false;
    std::string m_collisionTraceMapName;
    float m_collisionTraceClockSeconds = 0.0f;
    float m_nextCollisionTraceSeconds = 0.0f;
    float m_movementAccumulatorSeconds = 0.0f;
    bool m_pendingJumpRequested = false;
    float m_pendingImpulseVelocityX = 0.0f;
    float m_pendingImpulseVelocityY = 0.0f;
    float m_pendingImpulseVelocityZ = 0.0f;
    // A special jump's horizontal speed, kept until the party is back on the ground.
    float m_jumpCarryVelocityX = 0.0f;
    float m_jumpCarryVelocityY = 0.0f;
    float m_dashVelocityX = 0.0f;
    float m_dashVelocityY = 0.0f;
    float m_dashSeconds = 0.0f;
    std::optional<float> m_pendingJumpVelocity;
    float m_pendingJumpLift = 0.0f;
    float m_burningDamageTimerSeconds = 0.0f;
    std::string m_movementStatusText;
    std::vector<size_t> m_steppedFloorFaces;
    // Water (runtime only: a save under water loads with full breath, the state derived again from the position).
    IndoorSwimInput m_swimInput = {};
    IndoorSwimMemory m_swimMemory = {};
    IndoorSwimState m_swimState = IndoorSwimState::Dry;
    IndoorBreathState m_breath = {};
    std::vector<float> m_waterTopOffsets;
    bool m_eyeUnderWater = false;
    bool m_eyeUnderWaterKnown = false;
    std::optional<size_t> m_eyeWaterVolumeIndex;
    uint32_t m_drowningTicks = 0;
    std::vector<std::string> m_waterSounds;
};
}
