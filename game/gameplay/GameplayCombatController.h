#pragma once

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/PlayerId.h"
#include "game/party/Party.h"
#include "game/tables/PortraitEnums.h"

#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class CombatRules;
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
        // The player whose party the event is about: the one a monster hit, or the one whose member hit a monster.
        PlayerId player = LocalPlayer;
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
        // A party missile's or spell's damage was a critical hit.
        bool critical = false;
        // A solo run's ordinary bow attack's shared credit (ProjectileState::hitCredit).
        std::shared_ptr<bool> hitCredit;
        // A monster's missile at the party: how far it stood when it loosed it (ProjectileState::firedDistance);
        // negative when unknown.
        float firedDistance = -1.0f;
        // A monster's death blast (MM8's Special "explode"), not a detonate modifier's charge: MAW cuts it.
        bool deathBlast = false;
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
        std::optional<int> appliedDamage;
        bool actionPerformed = false;
        bool attacked = false;
        bool hadMeleeTarget = false;
        bool killed = false;
        bool targetStrongEnemy = false;
    };

    // A party hit that deals no damage after resistances counts as a miss unless it stuns the target.
    static bool partyHitLands(int appliedDamage, bool stunsTarget);
    static std::string formatPartyAttackStatusText(
        const std::string &attackerName,
        const std::string &targetName,
        const CharacterAttackResult &attack,
        bool killed,
        std::optional<int> appliedDamage = std::nullopt,
        const CombatRules *pRules = nullptr);

    // With rules, an area spell's `monstersHit` and `totalDamage` sum what its explosion did this frame.
    static std::string formatPartyProjectileActorImpactStatusText(
        const std::string &sourceName,
        const std::string &targetName,
        const CombatEvent &event,
        const CombatRules *pRules = nullptr,
        int monstersHit = 1,
        int totalDamage = 0);

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
    void recordPartyProjectileImpact(
        uint32_t sourceId,
        int damage,
        int attackBonus,
        int spellId,
        bool affectsAllParty,
        CombatDamageType damageType,
        GameplayActorAttackAbility ability,
        float firedDistance = -1.0f);
    // A monster's blast reaching the whole party, as its Attack 1: its death blast (deathBlast) or a detonate
    // modifier's.
    void recordMonsterBlastImpact(uint32_t sourceId, int damage, CombatDamageType damageType, bool deathBlast);
    void recordPartyProjectileActorImpact(
        uint32_t sourceId,
        uint32_t sourcePartyMemberIndex,
        uint32_t targetActorId,
        int damage,
        CombatDamageType damageType,
        int spellId,
        bool hit,
        bool killed,
        bool critical = false,
        std::shared_ptr<bool> hitCredit = nullptr);
    const std::vector<CombatEvent> &pendingCombatEvents() const;
    void clearPendingCombatEvents();
    void handleAndClearPendingCombatEvents(PendingCombatEventContext &context);
    // The same for a game of several players' parties: each player's events are handled with that player's party
    // (partyOf; a player it does not know has its events dropped), in the order the players first appear. Only the
    // local player's are shown on this game's screen (pLocalRuntime).
    void handleAndClearPendingCombatEvents(
        const std::function<Party *(PlayerId)> &partyOf,
        IGameplayWorldRuntime *pWorldRuntime,
        GameplayScreenRuntime *pLocalRuntime);
    // The player the events recorded from now on are about (CombatEvent::player); the recorder sets it back to
    // LocalPlayer when it is done.
    void setRecordingPlayer(PlayerId player);

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
        CombatDamageType damageType,
        GameplayActorAttackAbility ability);
    static CombatEvent buildPartyProjectileActorImpactEvent(
        uint32_t sourceId,
        uint32_t sourcePartyMemberIndex,
        uint32_t targetActorId,
        int damage,
        CombatDamageType damageType,
        int spellId,
        bool hit,
        bool killed,
        bool critical = false,
        std::shared_ptr<bool> hitCredit = nullptr);
    static void handlePendingCombatEvents(
        PendingCombatEventContext &context,
        const std::vector<CombatEvent> &events);

    void queueCombatEvent(CombatEvent event);

    PlayerId m_recordingPlayer = LocalPlayer;
    std::vector<CombatEvent> m_pendingCombatEvents;
};
} // namespace OpenYAMM::Game
