#pragma once

#include "game/events/EventRuntime.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct GameplayChestItemState
{
    InventoryItem item = {};
    uint32_t itemId = 0;
    uint32_t quantity = 0;
    uint32_t goldAmount = 0;
    uint32_t goldRollCount = 0;
    bool isGold = false;
    uint8_t width = 1;
    uint8_t height = 1;
    uint8_t gridX = 0;
    uint8_t gridY = 0;
};

struct GameplayChestViewState
{
    uint32_t chestId = 0;
    uint16_t chestTypeId = 0;
    uint16_t flags = 0;
    uint8_t gridWidth = 0;
    uint8_t gridHeight = 0;
    std::vector<GameplayChestItemState> items;
};

struct GameplayCorpseViewState
{
    bool fromSummonedMonster = false;
    uint32_t sourceIndex = 0;
    std::string title;
    std::vector<GameplayChestItemState> items;
};

struct GameplayRuntimeActorState
{
    float preciseX = 0.0f;
    float preciseY = 0.0f;
    float preciseZ = 0.0f;
    uint16_t radius = 0;
    uint16_t height = 0;
    bool isDead = false;
    bool isInvisible = false;
    bool hostileToParty = false;
    bool hasDetectedParty = false;
};

struct GameplayPartySpellProjectileRequest
{
    uint32_t casterMemberIndex = 0;
    uint32_t spellId = 0;
    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;
    int damage = 0;
    float sourceX = 0.0f;
    float sourceY = 0.0f;
    float sourceZ = 0.0f;
    float targetX = 0.0f;
    float targetY = 0.0f;
    float targetZ = 0.0f;
};

class IGameplayWorldRuntime
{
public:
    virtual ~IGameplayWorldRuntime() = default;

    virtual const std::string &mapName() const = 0;
    virtual float gameMinutes() const = 0;
    virtual int currentHour() const = 0;
    virtual void advanceGameMinutes(float minutes) = 0;
    virtual int currentLocationReputation() const = 0;
    virtual void setCurrentLocationReputation(int reputation) = 0;
    virtual Party *party() = 0;
    virtual const Party *party() const = 0;
    virtual float partyX() const = 0;
    virtual float partyY() const = 0;
    virtual float partyFootZ() const = 0;
    virtual void syncSpellMovementStatesFromPartyBuffs() = 0;
    virtual void requestPartyJump() = 0;
    virtual EventRuntimeState *eventRuntimeState() = 0;
    virtual const EventRuntimeState *eventRuntimeState() const = 0;
    virtual bool castEventSpell(
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        int32_t fromX,
        int32_t fromY,
        int32_t fromZ,
        int32_t toX,
        int32_t toY,
        int32_t toZ) = 0;
    virtual size_t mapActorCount() const = 0;
    virtual bool actorRuntimeState(size_t actorIndex, GameplayRuntimeActorState &state) const = 0;
    virtual bool castPartySpellProjectile(const GameplayPartySpellProjectileRequest &request) = 0;
    virtual bool applyPartySpellToActor(
        size_t actorIndex,
        uint32_t spellId,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        int damage,
        float partyX,
        float partyY,
        float partyZ,
        uint32_t sourcePartyMemberIndex) = 0;
    virtual std::vector<size_t> collectMapActorIndicesWithinRadius(
        float centerX,
        float centerY,
        float centerZ,
        float radius,
        bool requireLineOfSight,
        float sourceX,
        float sourceY,
        float sourceZ) const = 0;
    virtual bool spawnPartyFireSpikeTrap(
        uint32_t casterMemberIndex,
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        float x,
        float y,
        float z) = 0;
    virtual bool summonFriendlyMonsterById(
        int16_t monsterId,
        uint32_t count,
        float durationSeconds,
        float x,
        float y,
        float z) = 0;
    virtual void triggerGameplayScreenOverlay(
        uint32_t colorAbgr,
        float durationSeconds,
        float peakAlpha) = 0;
    virtual bool tryStartArmageddon(
        size_t casterMemberIndex,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        std::string &failureText) = 0;
    virtual const GameplayChestViewState *activeChestView() const = 0;
    virtual bool takeActiveChestItem(size_t itemIndex, GameplayChestItemState &item) = 0;
    virtual bool takeActiveChestItemAt(uint8_t gridX, uint8_t gridY, GameplayChestItemState &item) = 0;
    virtual bool tryPlaceActiveChestItemAt(const GameplayChestItemState &item, uint8_t gridX, uint8_t gridY) = 0;
    virtual void closeActiveChestView() = 0;
    virtual const GameplayCorpseViewState *activeCorpseView() const = 0;
    virtual bool takeActiveCorpseItem(size_t itemIndex, GameplayChestItemState &item) = 0;
    virtual void closeActiveCorpseView() = 0;
};
}
