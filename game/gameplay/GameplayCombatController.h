#pragma once

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
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
        int attackBonus = 0;
        int spellId = 0;
        CombatDamageType damageType = CombatDamageType::Physical;
        GameplayActorAttackAbility ability = GameplayActorAttackAbility::Attack1;
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
    void recordMonsterMeleeImpact(uint32_t sourceId, int damage, int attackBonus);
    void recordMonsterMeleeImpact(
        uint32_t sourceId,
        int damage,
        int attackBonus,
        CombatDamageType damageType,
        GameplayActorAttackAbility ability);
    void recordMonsterRangedRelease(uint32_t sourceId, int damage);
    void recordMonsterRangedRelease(uint32_t sourceId, int damage, CombatDamageType damageType);
    void recordPartyProjectileImpact(
        uint32_t sourceId,
        int damage,
        int spellId,
        bool affectsAllParty);
    void recordPartyProjectileImpact(
        uint32_t sourceId,
        int damage,
        int spellId,
        bool affectsAllParty,
        CombatDamageType damageType);
    void recordPartyProjectileImpact(
        uint32_t sourceId,
        int damage,
        int attackBonus,
        int spellId,
        bool affectsAllParty,
        CombatDamageType damageType);
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
    static CombatEvent buildMonsterMeleeImpactEvent(
        uint32_t sourceId,
        int damage,
        int attackBonus,
        CombatDamageType damageType,
        GameplayActorAttackAbility ability);
    static CombatEvent buildMonsterRangedReleaseEvent(
        uint32_t sourceId,
        int damage,
        CombatDamageType damageType);
    static CombatEvent buildPartyProjectileImpactEvent(
        uint32_t sourceId,
        int damage,
        int attackBonus,
        int spellId,
        bool affectsAllParty,
        CombatDamageType damageType);
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
