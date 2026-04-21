#pragma once

#include "game/gameplay/GameMechanics.h"
#include "game/party/Party.h"
#include "game/tables/PortraitEnums.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
class IGameplayWorldRuntime;

class GameplayCombatController
{
public:
    enum class CombatEventType
    {
        MonsterMeleeImpact,
        MonsterRangedRelease,
        PartyProjectileImpact,
        PartyProjectileActorImpact,
    };

    struct CombatEvent
    {
        CombatEventType type = CombatEventType::MonsterMeleeImpact;
        uint32_t sourceId = 0;
        uint32_t sourcePartyMemberIndex = 0;
        uint32_t targetActorId = 0;
        int damage = 0;
        int spellId = 0;
        bool affectsAllParty = false;
        bool hit = false;
        bool killed = false;
    };

    struct PendingCombatEventContext
    {
        Party &party;
        IGameplayWorldRuntime *pWorldRuntime = nullptr;
        GameplayScreenRuntime *pRuntime = nullptr;
    };

    struct PartyAttackPresentation
    {
        size_t memberIndex = 0;
        std::string attackerName;
        std::string targetName;
        CharacterAttackResult attack = {};
        bool actionPerformed = false;
        bool attacked = false;
        bool hadMeleeTarget = false;
        bool killed = false;
        bool targetStrongEnemy = false;
    };

    static std::string formatPartyAttackStatusText(
        const std::string &attackerName,
        const std::string &targetName,
        const CharacterAttackResult &attack,
        bool killed);

    static void handlePartyAttackPresentation(
        GameplayScreenRuntime *pRuntime,
        const PartyAttackPresentation &attack);

    void clear();
    void recordMonsterMeleeImpact(uint32_t sourceId, int damage);
    void recordMonsterRangedRelease(uint32_t sourceId, int damage);
    void recordPartyProjectileImpact(
        uint32_t sourceId,
        int damage,
        int spellId,
        bool affectsAllParty);
    void recordPartyProjectileActorImpact(
        uint32_t sourceId,
        uint32_t sourcePartyMemberIndex,
        uint32_t targetActorId,
        int damage,
        int spellId,
        bool hit,
        bool killed);
    const std::vector<CombatEvent> &pendingCombatEvents() const;
    void clearPendingCombatEvents();
    void handleAndClearPendingCombatEvents(PendingCombatEventContext &context);

private:
    static CombatEvent buildMonsterMeleeImpactEvent(uint32_t sourceId, int damage);
    static CombatEvent buildMonsterRangedReleaseEvent(uint32_t sourceId, int damage);
    static CombatEvent buildPartyProjectileImpactEvent(
        uint32_t sourceId,
        int damage,
        int spellId,
        bool affectsAllParty);
    static CombatEvent buildPartyProjectileActorImpactEvent(
        uint32_t sourceId,
        uint32_t sourcePartyMemberIndex,
        uint32_t targetActorId,
        int damage,
        int spellId,
        bool hit,
        bool killed);
    static void handlePendingCombatEvents(
        PendingCombatEventContext &context,
        const std::vector<CombatEvent> &events);

    std::vector<CombatEvent> m_pendingCombatEvents;
};
} // namespace OpenYAMM::Game
