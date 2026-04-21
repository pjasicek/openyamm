#pragma once

#include "game/gameplay/GameMechanics.h"
#include "game/party/Party.h"
#include "game/tables/PortraitEnums.h"

#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
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

    struct ActorCombatInfo
    {
        uint32_t actorId = 0;
        int16_t monsterId = 0;
        int maxHp = 0;
        uint32_t attackPreferences = 0;
        std::string displayName;
    };

    struct PresentationCallbacks
    {
        std::function<void(size_t, FaceAnimationId)> triggerPortraitFaceAnimation;
        std::function<void(FaceAnimationId)> triggerPortraitFaceAnimationForAllLivingMembers;
        std::function<void(size_t, SpeechId, bool)> playSpeechReaction;
        std::function<void(const std::string &)> showCombatStatus;
        std::function<uint32_t()> animationTicks;
    };

    struct PendingCombatEventContext
    {
        Party &party;
        std::function<std::optional<ActorCombatInfo>(uint32_t)> resolveActorById;
        PresentationCallbacks presentation;
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
        const PresentationCallbacks &presentation,
        const PartyAttackPresentation &attack);

    static void handlePendingCombatEvents(
        PendingCombatEventContext &context,
        const std::vector<CombatEvent> &events);
};
} // namespace OpenYAMM::Game
