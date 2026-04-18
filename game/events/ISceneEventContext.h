#pragma once

#include <cstdint>

namespace OpenYAMM::Game
{
struct MapDeltaData;

class ISceneEventContext
{
public:
    virtual ~ISceneEventContext() = default;

    virtual float currentGameMinutes() const = 0;
    virtual const MapDeltaData *mapDeltaData() const = 0;

    virtual bool castEventSpell(
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        int32_t fromX,
        int32_t fromY,
        int32_t fromZ,
        int32_t toX,
        int32_t toY,
        int32_t toZ
    ) = 0;

    virtual bool summonMonsters(
        uint32_t typeIndexInMapStats,
        uint32_t level,
        uint32_t count,
        int32_t x,
        int32_t y,
        int32_t z,
        uint32_t group,
        uint32_t uniqueNameId
    ) = 0;

    virtual bool summonEventItem(
        uint32_t itemId,
        int32_t x,
        int32_t y,
        int32_t z,
        int32_t speed,
        uint32_t count,
        bool randomRotate
    ) = 0;

    virtual bool checkMonstersKilled(
        uint32_t checkType,
        uint32_t id,
        uint32_t count,
        bool invisibleAsDead
    ) const = 0;
};
}
