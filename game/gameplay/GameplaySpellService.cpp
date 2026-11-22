#include "game/gameplay/GameplaySpellService.h"

#include "engine/Localization.h"

#include "game/app/GameSession.h"
#include "game/audio/GameAudioSystem.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayHeldItemController.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/PlayerCommands.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/party/LloydsBeaconRuntime.h"
#include "game/party/SpellIds.h"
#include "game/rules/GameRules.h"
#include "game/rules/SpellRules.h"

namespace OpenYAMM::Game
{
namespace
{
bool isUtilitySelectionRequest(const PartySpellCastRequest &request)
{
    return request.utilityAction != PartySpellUtilityActionKind::None
        || request.targetInventoryGridX.has_value()
        || request.targetEquipmentSlot.has_value();
}

bool isFollowupSpellUiActive(
    const GameplayScreenState &screenState,
    const GameplayScreenRuntime &runtime)
{
    return screenState.pendingSpellTarget().active || runtime.utilitySpellOverlayReadOnly().active;
}

SkillMastery dragonAbilityMasteryForCaster(const GameplayScreenRuntime &runtime, size_t casterMemberIndex)
{
    const Party *pParty = runtime.partyReadOnly();
    const Character *pCaster = pParty != nullptr ? pParty->member(casterMemberIndex) : nullptr;
    const CharacterSkill *pDragonAbility = pCaster != nullptr ? pCaster->findSkill("DragonAbility") : nullptr;
    return pDragonAbility != nullptr ? pDragonAbility->mastery : SkillMastery::None;
}
}

GameplaySpellService::GameplaySpellService(GameSession &session)
    : m_session(session)
{
}

GameplaySpellService::QuickSpellStartResolution GameplaySpellService::tryStartQuickSpellCast(
    GameplayScreenRuntime &runtime,
    const TargetQueries &targetQueries,
    std::optional<size_t> extraSlot,
    const std::string &barSpellName)
{
    QuickSpellStartResolution resolution = {};

    if (m_session.gameplayScreenState().pendingSpellTarget().active)
    {
        showPendingTargetSelectionPrompt(runtime);
        return resolution;
    }

    IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();
    const bool hasActiveLootView =
        pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr || pWorldRuntime->activeCorpseView() != nullptr);

    if (runtime.heldInventoryItem().active
        || runtime.characterScreenReadOnly().open
        || runtime.spellbookReadOnly().active
        || runtime.controlsScreenState().active
        || runtime.keyboardScreenState().active
        || runtime.menuScreenState().active
        || runtime.saveGameScreenState().active
        || runtime.loadGameScreenState().active
        || runtime.activeEventDialog().isActive
        || hasActiveLootView)
    {
        runtime.setStatusBarEvent(Engine::tr("Finish current action"));
        return resolution;
    }

    Party *pParty = runtime.party();

    if (pParty == nullptr)
    {
        return resolution;
    }

    const Character *pCaster = pParty->activeMember();

    if (pCaster == nullptr || !GameMechanics::canTakeGameplayAction(*pCaster))
    {
        return resolution;
    }

    const std::string &quickSpellName = !barSpellName.empty() ? barSpellName
        : extraSlot && *extraSlot < ExtraQuickSpellSlotCount ? pCaster->extraQuickSpellNames[*extraSlot]
        : pCaster->quickSpellName;

    if (quickSpellName.empty())
    {
        resolution.disposition = QuickSpellStartDisposition::AttackFallback;
        return resolution;
    }

    const SpellTable *pSpellTable = runtime.spellTable();

    if (pSpellTable == nullptr)
    {
        return resolution;
    }

    const SpellEntry *pSpellEntry = pSpellTable->findByName(quickSpellName, spellKnownBy(*pCaster));

    if (pSpellEntry == nullptr)
    {
        runtime.setStatusBarEvent(Engine::tr("Unknown quick spell"));
        return resolution;
    }

    const size_t casterMemberIndex = pParty->activeMemberIndex();
    const uint32_t spellId = uint32_t(pSpellEntry->id);

    if (!pCaster->knowsSpell(spellId))
    {
        runtime.setStatusBarEvent(Engine::tr("Spell not learned"));
        return resolution;
    }

    // A caster without the mana, the rules' other means (an Assassin's combo points) or a target for the quick spell
    // attacks instead, so the character is never stuck; attacking is how an Assassin builds combo points.
    const std::optional<uint32_t> manaCost = PartySpellSystem::manaCost(*pParty, *pCaster, *pSpellTable, spellId);

    if ((manaCost && !pParty->canSpendSpellPoints(casterMemberIndex, int(*manaCost)))
        || pParty->rules().spells.castRefusal(*pParty, casterMemberIndex, spellId))
    {
        resolution.disposition = QuickSpellStartDisposition::AttackFallback;
        return resolution;
    }

    PartySpellCastRequest request = {};
    request.casterMemberIndex = casterMemberIndex;
    request.spellId = spellId;

    if (!tryPrepareQuickCastRequest(runtime, request, pSpellEntry->name, targetQueries))
    {
        resolution.disposition = QuickSpellStartDisposition::AttackFallback;
        return resolution;
    }

    if (runtime.tryCastSpellRequest(request, pSpellEntry->name))
    {
        resolution.disposition = QuickSpellStartDisposition::CastStarted;
    }

    return resolution;
}

GameplaySpellService::MemberSpellCastResolution GameplaySpellService::castSpellFromMember(
    GameplayScreenRuntime &runtime,
    size_t casterMemberIndex,
    uint32_t spellId,
    const std::string &spellName,
    bool quickCast,
    const TargetQueries *pTargetQueries)
{
    MemberSpellCastResolution resolution = {};
    Party *pParty = runtime.party();

    if (pParty != nullptr)
    {
        const Character *pCaster = pParty->member(casterMemberIndex);

        if (pCaster == nullptr || !pCaster->knowsSpell(spellId))
        {
            runtime.setStatusBarEvent(Engine::tr("Spell not learned"));
            return resolution;
        }
    }

    PartySpellCastRequest request = {};
    request.casterMemberIndex = casterMemberIndex;
    request.spellId = spellId;

    if (quickCast
        && pTargetQueries != nullptr
        && !tryPrepareQuickCastRequest(runtime, request, spellName, *pTargetQueries))
    {
        resolution.noTarget = true;
        return resolution;
    }

    resolution.castStarted = runtime.tryCastSpellRequest(request, spellName);
    resolution.followupUiActive =
        resolution.castStarted && isFollowupSpellUiActive(m_session.gameplayScreenState(), runtime);
    return resolution;
}

bool GameplaySpellService::tryCastSpellFromMember(
    GameplayScreenRuntime &runtime,
    size_t casterMemberIndex,
    uint32_t spellId,
    const std::string &spellName,
    bool quickCast,
    const TargetQueries *pTargetQueries)
{
    return castSpellFromMember(
        runtime,
        casterMemberIndex,
        spellId,
        spellName,
        quickCast,
        pTargetQueries).castStarted;
}

bool GameplaySpellService::tryPrepareQuickCastRequest(
    GameplayScreenRuntime &runtime,
    PartySpellCastRequest &request,
    const std::string &spellName,
    const TargetQueries &targetQueries) const
{
    // A spell the rules hold as an aura (MAW's Meditation on Telepathy's id, Bless) toggles without a target.
    const Party *pParty = runtime.partyReadOnly();

    if (pParty != nullptr && pParty->rules().spells.castsAsAura(*pParty, request.casterMemberIndex, request.spellId))
    {
        return true;
    }

    if (targetQueries.characterTargetIndex)
    {
        request.quickCast = true;
        request.targetCharacterIndex = targetQueries.characterTargetIndex;
        request.targetPlayer = targetQueries.characterTargetPlayer;
        return true;
    }

    if (spellIdFromValue(request.spellId) == SpellId::Fear)
    {
        request.quickCast = true;

        if (dragonAbilityMasteryForCaster(runtime, request.casterMemberIndex) >= SkillMastery::Grandmaster)
        {
            return true;
        }

        const PartySpellDescriptor fearTargetDescriptor = {
            request.spellId,
            PartySpellCastTargetKind::Actor,
            PartySpellCastEffectKind::ActorEffect
        };

        return tryResolveQuickCastRequest(runtime, request, fearTargetDescriptor, targetQueries);
    }

    const std::optional<PartySpellDescriptor> descriptor = PartySpellSystem::describeSpell(request.spellId);

    if (!descriptor || !isQuickCastable(*descriptor))
    {
        return true;
    }

    request.quickCast = true;

    // In a co-op session a heal, cure or raising goes to whoever near needs it most, another player's character
    // too.
    if (descriptor->targetKind == PartySpellCastTargetKind::Character && !targetQueries.characterTargetIndex)
    {
        if (const std::optional<CoopCharacterTarget> target =
                coopCharacterTarget(runtime, request.casterMemberIndex, request.spellId, false))
        {
            request.targetCharacterIndex = target->memberIndex;
            request.targetPlayer = target->player;
            return true;
        }
    }

    return tryResolveQuickCastRequest(runtime, request, *descriptor, targetQueries);
}

namespace
{
// Whether what this game knows of another player's character says the spell would help it.
bool otherPlayerNeedsSpell(uint32_t spellId, const CoopAidPlayer::Member &other)
{
    using enum CharacterCondition;
    const std::optional<CharacterCondition> condition = other.conditionCode != 0
        ? std::optional<CharacterCondition>(CharacterCondition(other.conditionCode - 1)) : std::nullopt;
    const auto ails = [&condition](std::initializer_list<CharacterCondition> conditions)
    {
        return condition && std::find(conditions.begin(), conditions.end(), *condition) != conditions.end();
    };

    switch (spellIdFromValue(spellId))
    {
        case SpellId::RaiseDead: return ails({Dead});
        case SpellId::Resurrection: return ails({Dead, Eradicated});
        case SpellId::StoneToFlesh: return ails({Petrified});
        case SpellId::RemoveCurse: return ails({Cursed});
        case SpellId::RemoveFear: return ails({Fear});
        case SpellId::CureParalysis: return ails({Paralyzed});
        case SpellId::CureInsanity: return ails({Insane});
        case SpellId::CureWeakness: return ails({Weak});
        case SpellId::CurePoison: return ails({PoisonWeak, PoisonMedium, PoisonSevere});
        case SpellId::CureDisease: return ails({DiseaseWeak, DiseaseMedium, DiseaseSevere});
        default: break;
    }

    // A heal: the wounded, the unconscious too; not those a heal cannot reach.
    return other.health < other.maxHealth && !ails({Dead, Eradicated, Petrified});
}

float healthShare(int32_t health, int32_t maximum)
{
    return maximum > 0 ? float(health) / float(maximum) : 1.0f;
}
}

std::optional<GameplaySpellService::CoopCharacterTarget> GameplaySpellService::coopCharacterTarget(
    GameplayScreenRuntime &runtime,
    size_t casterMemberIndex,
    uint32_t spellId,
    bool explicitCast) const
{
    const Party *pParty = runtime.partyReadOnly();
    const IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    const std::vector<CoopAidPlayer> &others = m_session.coopAidPlayers();

    if (!m_session.coopSession() || others.empty() || pParty == nullptr || pWorldRuntime == nullptr)
    {
        return std::nullopt;
    }

    // A player with one character has nobody else of its own to choose; one with a party chooses among its members
    // as ever, unless it points at another player.
    const bool oneCharacter = pParty->combatantCount() == 1;

    const float x = pWorldRuntime->partyX();
    const float y = pWorldRuntime->partyY();
    const float footZ = pWorldRuntime->partyFootZ();
    // Within the reach of a party's spells, with nothing of the map in between (as the host will ask).
    const float reach = m_session.aidReach();
    const float eyeHeight = m_session.partyEyeHeight();
    const auto withinReach = [&](const CoopAidPlayer &other)
    {
        const float deltaX = other.x - x;
        const float deltaY = other.y - y;
        const float deltaZ = other.footZ - footZ;
        return deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ <= reach * reach
            && pWorldRuntime->hasClearLineBetween({x, y, footZ + eyeHeight},
                {other.x, other.y, other.footZ + eyeHeight});
    };

    // The player the view is pointed at: the nearest body the line of sight passes through.
    if (explicitCast)
    {
        const float yaw = pWorldRuntime->gameplayCameraYawRadians();
        const float pitch = pWorldRuntime->gameplayCameraPitchRadians();
        const bx::Vec3 direction = {std::cos(pitch) * std::cos(yaw), std::cos(pitch) * std::sin(yaw), std::sin(pitch)};
        const bx::Vec3 eye = {x, y, pWorldRuntime->partyEyeZ()};
        std::optional<PlayerId> aimed;
        float aimedDistance = 0.0f;

        for (const CoopAidPlayer &other : others)
        {
            if (!withinReach(other))
            {
                continue;
            }

            // Standing it is tall and narrow; down it lies low and wide.
            const float height = other.down ? 60.0f : 176.0f;
            const float radius = other.down ? 110.0f : 64.0f;

            for (int step = 0; step <= 6; ++step)
            {
                const bx::Vec3 offset = {other.x - eye.x, other.y - eye.y,
                    other.footZ + height * float(step) / 6.0f - eye.z};
                const float along = bx::dot(offset, direction);
                const bx::Vec3 nearest = bx::mul(direction, along);
                const float away = bx::length(bx::sub(offset, nearest));

                if (along > 0.0f && away <= radius && (!aimed || along < aimedDistance))
                {
                    aimed = other.player;
                    aimedDistance = along;
                }
            }
        }

        // Of the party pointed at: the member the spell would help most, else its first.
        if (aimed)
        {
            size_t member = 0;
            std::optional<float> lowest;

            for (const CoopAidPlayer &other : others)
            {
                for (size_t index = 0; other.player == *aimed && index < other.members.size(); ++index)
                {
                    const float share = healthShare(other.members[index].health, other.members[index].maxHealth);

                    if (PartySpellSystem::hasQuickCastCharacterTarget(spellId)
                        && otherPlayerNeedsSpell(spellId, other.members[index]) && (!lowest || share < *lowest))
                    {
                        member = index;
                        lowest = share;
                    }
                }
            }

            return CoopCharacterTarget{member, aimed};
        }

        if (!oneCharacter)
        {
            return std::nullopt;
        }
    }

    // Whoever needs it most: the lowest share of hit points among those the spell would help.
    std::optional<CoopCharacterTarget> best;
    float bestShare = 0.0f;

    if (const std::optional<size_t> own = PartySpellSystem::quickCastCharacterTarget(
            *pParty, casterMemberIndex, spellId, runtime.spellTable()))
    {
        const Character *pOwn = pParty->combatant(*own);
        best = CoopCharacterTarget{*own, std::nullopt};
        bestShare = pOwn != nullptr ? healthShare(pOwn->health, pParty->reachableMaximumHealth(*own)) : 1.0f;
    }

    if (PartySpellSystem::hasQuickCastCharacterTarget(spellId))
    {
        for (const CoopAidPlayer &other : others)
        {
            for (size_t index = 0; withinReach(other) && index < other.members.size(); ++index)
            {
                const float share = healthShare(other.members[index].health, other.members[index].maxHealth);

                if (otherPlayerNeedsSpell(spellId, other.members[index]) && (!best || share < bestShare))
                {
                    best = CoopCharacterTarget{index, other.player};
                    bestShare = share;
                }
            }
        }
    }

    if (!best && explicitCast)
    {
        return CoopCharacterTarget{casterMemberIndex, std::nullopt};
    }

    return best;
}

float GameplaySpellService::coopLowestOtherHealthShare() const
{
    const IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    float lowest = 1.0f;

    if (!m_session.coopSession() || pWorldRuntime == nullptr)
    {
        return lowest;
    }

    for (const CoopAidPlayer &other : m_session.coopAidPlayers())
    {
        const float deltaX = other.x - pWorldRuntime->partyX();
        const float deltaY = other.y - pWorldRuntime->partyY();
        const float deltaZ = other.footZ - pWorldRuntime->partyFootZ();
        const float reach = m_session.aidReach();
        const float eyeHeight = m_session.partyEyeHeight();

        // Those a heal could reach: within the spells' reach and in sight.
        if (deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ > reach * reach
            || !pWorldRuntime->hasClearLineBetween(
                {pWorldRuntime->partyX(), pWorldRuntime->partyY(), pWorldRuntime->partyFootZ() + eyeHeight},
                {other.x, other.y, other.footZ + eyeHeight}))
        {
            continue;
        }

        for (const CoopAidPlayer::Member &member : other.members)
        {
            const bool beyond = member.conditionCode == uint8_t(CharacterCondition::Dead) + 1
                || member.conditionCode == uint8_t(CharacterCondition::Eradicated) + 1
                || member.conditionCode == uint8_t(CharacterCondition::Petrified) + 1;

            if (!beyond && member.maxHealth > 0)
            {
                lowest = std::min(lowest, std::max(0.0f, healthShare(member.health, member.maxHealth)));
            }
        }
    }

    return lowest;
}

bool GameplaySpellService::tryResolveQuickCastRequest(
    GameplayScreenRuntime &runtime,
    PartySpellCastRequest &request,
    const PartySpellDescriptor &descriptor,
    const TargetQueries &targetQueries)
{
    IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();

    if (descriptor.targetKind == PartySpellCastTargetKind::None)
    {
        return true;
    }

    if (descriptor.targetKind == PartySpellCastTargetKind::Character)
    {
        const Party *pParty = runtime.partyReadOnly();
        if (pParty == nullptr)
        {
            return false;
        }

        request.targetCharacterIndex = PartySpellSystem::quickCastCharacterTarget(
            *pParty, request.casterMemberIndex, request.spellId, runtime.spellTable());
        return request.targetCharacterIndex.has_value();
    }

    if (descriptor.targetKind == PartySpellCastTargetKind::Actor)
    {
        if (pWorldRuntime != nullptr)
        {
            // The attack's own target, else the hovered actor, else the game's pick; every one a living hostile
            // within spell reach, whether or not it has noticed the party.
            const auto usable = [pWorldRuntime](const std::optional<size_t> &actorIndex)
            {
                return actorIndex && PartySpellSystem::isUsableSpellActorTarget(*pWorldRuntime, *actorIndex, true);
            };
            request.targetActorIndex = targetQueries.preferredActorIndex;

            if (!usable(request.targetActorIndex))
            {
                request.targetActorIndex = pWorldRuntime->spellActionHoveredActorIndex();
            }

            // A missile spell with no actor under the crosshair flies at a standing destructible there rather than
            // at the game's pick (devdocs/INDOOR_DESTRUCTIBLES.md "Aiming").
            if (!usable(request.targetActorIndex) && descriptor.effectKind == PartySpellCastEffectKind::Projectile)
            {
                if (const std::optional<bx::Vec3> point = resolveCursorDestructiblePoint(targetQueries, *pWorldRuntime))
                {
                    request.targetActorIndex.reset();
                    request.hasTargetPoint = true;
                    request.targetX = point->x;
                    request.targetY = point->y;
                    request.targetZ = point->z;
                    return true;
                }
            }

            if (!usable(request.targetActorIndex))
            {
                const Party *pParty = runtime.partyReadOnly();
                const SpellRules &spellRules = pParty != nullptr ? pParty->rules().spells : standardSpellRules();
                request.targetActorIndex =
                    PartySpellSystem::quickCastActorTarget(*pWorldRuntime, spellRules, request.spellId);
            }
        }

        if (request.targetActorIndex)
        {
            return true;
        }

        if (descriptor.effectKind == PartySpellCastEffectKind::Projectile)
        {
            const std::optional<bx::Vec3> groundTargetPoint =
                resolveCursorTargetPoint(targetQueries, pWorldRuntime);

            if (!groundTargetPoint)
            {
                return false;
            }

            request.hasTargetPoint = true;
            request.targetX = groundTargetPoint->x;
            request.targetY = groundTargetPoint->y;
            request.targetZ = groundTargetPoint->z;
            return true;
        }

        return false;
    }

    if (descriptor.targetKind == PartySpellCastTargetKind::GroundPoint)
    {
        std::optional<bx::Vec3> targetPoint;

        if (pWorldRuntime != nullptr)
        {
            const std::optional<size_t> hoveredActorIndex = pWorldRuntime->spellActionHoveredActorIndex();

            if (hoveredActorIndex)
            {
                targetPoint = pWorldRuntime->spellActionActorTargetPoint(*hoveredActorIndex);
            }
        }

        if (!targetPoint)
        {
            targetPoint = resolveCursorTargetPoint(targetQueries, pWorldRuntime);
        }

        if (!targetPoint)
        {
            return false;
        }

        request.hasTargetPoint = true;
        request.targetX = targetPoint->x;
        request.targetY = targetPoint->y;
        request.targetZ = targetPoint->z;
        return true;
    }

    return false;
}

std::optional<bx::Vec3> GameplaySpellService::resolveCursorTargetPoint(
    const TargetQueries &targetQueries,
    const IGameplayWorldRuntime *pWorldRuntime)
{
    if (pWorldRuntime == nullptr)
    {
        return std::nullopt;
    }

    if (targetQueries.useCrosshairTarget && targetQueries.screenWidth > 0.0f && targetQueries.screenHeight > 0.0f)
    {
        return pWorldRuntime->spellActionGroundTargetPoint(
            targetQueries.screenWidth * 0.5f,
            targetQueries.screenHeight * 0.5f);
    }

    return pWorldRuntime->spellActionGroundTargetPoint(targetQueries.cursorX, targetQueries.cursorY);
}

std::optional<bx::Vec3> GameplaySpellService::resolveCursorDestructiblePoint(
    const TargetQueries &targetQueries,
    IGameplayWorldRuntime &worldRuntime)
{
    if (targetQueries.screenWidth <= 0.0f || targetQueries.screenHeight <= 0.0f)
    {
        return std::nullopt;
    }

    const GameplayWorldPickRequest pickRequest = worldRuntime.buildWorldPickRequest(
        GameplayWorldPickRequestInput{
            .screenX = targetQueries.useCrosshairTarget ? targetQueries.screenWidth * 0.5f : targetQueries.cursorX,
            .screenY = targetQueries.useCrosshairTarget ? targetQueries.screenHeight * 0.5f : targetQueries.cursorY,
            .screenWidth = int(targetQueries.screenWidth),
            .screenHeight = int(targetQueries.screenHeight),
            .includeRay = true,
        });
    return standingDestructibleHitPoint(worldRuntime, worldRuntime.pickPartyAttackTarget(pickRequest));
}

GameplaySpellService::SpellRequestResolution GameplaySpellService::resolveSpellRequest(
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &initialRequest,
    const std::string &spellName)
{
    PartySpellCastRequest request = initialRequest;
    const GameplayUiController::UtilitySpellOverlayState &selection = runtime.utilitySpellOverlayReadOnly();

    if (isUtilitySelectionRequest(request) && selection.active
        && selection.mode != GameplayUiController::UtilitySpellOverlayMode::DimensionDoor
        && selection.spellId == request.spellId && selection.casterMemberIndex == request.casterMemberIndex)
    {
        request.skillLevelOverride = selection.skillLevelOverride;
        request.skillMasteryOverride = selection.skillMasteryOverride;
        request.bypassRequiredMastery = selection.bypassRequiredMastery;
        request.bypassGameplayCasterValidation = selection.bypassGameplayCasterValidation;
        request.spendMana = selection.spendMana;
        request.applyRecovery = selection.applyRecovery;
    }

    SpellRequestResolution resolution = {};

    if (!request.bypassGameplayCasterValidation
        && !tryValidateCasterForGameplayCast(runtime, request.casterMemberIndex))
    {
        return resolution;
    }

    resolution.castResult = m_session.playerCommands().castSpell(LocalPlayer, runtime, request);

    // A solo run has one character: a heal, cure or buff that wants a character goes to the hero without asking.
    // MM9 hirelings, which come along but never act, are not picked this way.
    if (resolution.castResult.status == PartySpellCastStatus::NeedCharacterTarget)
    {
        const Party *pParty = runtime.partyReadOnly();

        // With other players about (a co-op session): the one the view is pointed at; for a player with one
        // character, else whoever near needs it, else that character.
        const std::optional<CoopCharacterTarget> other = pParty != nullptr
            ? coopCharacterTarget(runtime, request.casterMemberIndex, request.spellId, true) : std::nullopt;

        if (pParty != nullptr && (other || pParty->soloRun()) && pParty->member(request.casterMemberIndex) != nullptr)
        {
            request.targetCharacterIndex = other ? other->memberIndex : request.casterMemberIndex;
            request.targetPlayer = other ? other->player : std::nullopt;
            resolution.castResult = m_session.playerCommands().castSpell(LocalPlayer, runtime, request);
        }
    }

    if (resolution.castResult.succeeded())
    {
        applySuccessFeedback(runtime, request, spellName, resolution.castResult);
        resolution.disposition = SpellRequestDisposition::CastSucceeded;
        return resolution;
    }

    if (tryOpenSelectionUi(runtime, request, spellName, resolution.castResult))
    {
        GameplayUiController::UtilitySpellOverlayState &overlay = runtime.utilitySpellOverlay();

        if (overlay.active && overlay.spellId == request.spellId
            && overlay.casterMemberIndex == request.casterMemberIndex)
        {
            overlay.skillLevelOverride = request.skillLevelOverride;
            overlay.skillMasteryOverride = request.skillMasteryOverride;
            overlay.bypassRequiredMastery = request.bypassRequiredMastery;
            overlay.bypassGameplayCasterValidation = request.bypassGameplayCasterValidation;
            overlay.spendMana = request.spendMana;
            overlay.applyRecovery = request.applyRecovery;
        }

        Party *pParty = runtime.party();

        if (pParty != nullptr)
        {
            pParty->setActiveMemberIndex(request.casterMemberIndex);
        }

        resolution.disposition = SpellRequestDisposition::OpenedSelectionUi;
        return resolution;
    }

    if (requiresTargetSelection(resolution.castResult))
    {
        if (isSpellId(request.spellId, SpellId::Telekinesis)
            && !GameplayHeldItemController::tryDisplaceHeldInventoryItem(runtime))
        {
            runtime.setStatusBarEvent(Engine::tr("Finish current action"));
            return resolution;
        }

        resolution.disposition = SpellRequestDisposition::NeedsTargetSelection;
        return resolution;
    }

    applyFailureFeedback(runtime, request, resolution.castResult);
    return resolution;
}

void GameplaySpellService::armPendingTargetSelection(
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &request,
    PartySpellCastTargetKind targetKind,
    const std::string &spellName) const
{
    GameplayScreenState::PendingSpellTargetState &pendingTargetState =
        m_session.gameplayScreenState().pendingSpellTarget();
    pendingTargetState.clear();
    pendingTargetState.active = true;
    pendingTargetState.casterMemberIndex = request.casterMemberIndex;
    pendingTargetState.spellId = request.spellId;
    pendingTargetState.skillLevelOverride = request.skillLevelOverride;
    pendingTargetState.skillMasteryOverride = request.skillMasteryOverride;
    pendingTargetState.bypassRequiredMastery = request.bypassRequiredMastery;
    pendingTargetState.spendMana = request.spendMana;
    pendingTargetState.applyRecovery = request.applyRecovery;
    pendingTargetState.targetKind = targetKind;
    pendingTargetState.spellName = spellName;
    showPendingTargetSelectionPrompt(runtime);
}

void GameplaySpellService::clearPendingTargetSelection(
    GameplayScreenRuntime &runtime,
    const std::string &statusText) const
{
    m_session.gameplayScreenState().pendingSpellTarget().clear();

    if (!statusText.empty())
    {
        runtime.setStatusBarEvent(statusText);
    }
}

PartySpellCastRequest GameplaySpellService::makePendingTargetSelectionRequest() const
{
    const GameplayScreenState::PendingSpellTargetState &pendingTargetState =
        m_session.gameplayScreenState().pendingSpellTarget();

    PartySpellCastRequest request = {};
    request.casterMemberIndex = pendingTargetState.casterMemberIndex;
    request.spellId = pendingTargetState.spellId;
    request.skillLevelOverride = pendingTargetState.skillLevelOverride;
    request.skillMasteryOverride = pendingTargetState.skillMasteryOverride;
    request.bypassRequiredMastery = pendingTargetState.bypassRequiredMastery;
    request.spendMana = pendingTargetState.spendMana;
    request.applyRecovery = pendingTargetState.applyRecovery;
    return request;
}

std::string GameplaySpellService::pendingTargetSelectionPromptText(bool includeControls) const
{
    const GameplayScreenState::PendingSpellTargetState &pendingTargetState =
        m_session.gameplayScreenState().pendingSpellTarget();

    const std::string spellName = Engine::localizeKnown(pendingTargetState.spellName, "spell");
    std::string prompt =
        pendingTargetState.targetKind == PartySpellCastTargetKind::Actor
            ? Engine::tr("Select actor for {spell}", {{"spell", spellName}})
            : pendingTargetState.targetKind == PartySpellCastTargetKind::Character
            ? Engine::tr("Select character for {spell}", {{"spell", spellName}})
            : pendingTargetState.targetKind == PartySpellCastTargetKind::GroundPoint
            ? Engine::tr("Select ground point for {spell}", {{"spell", spellName}})
            : Engine::tr("Select target for {spell}", {{"spell", spellName}});

    if (includeControls)
    {
#if defined(__ANDROID__) || defined(OPENYAMM_IOS)
        const bool mobileGroundTargetConfirmSpell =
            isSpellId(pendingTargetState.spellId, SpellId::MeteorShower)
            || isSpellId(pendingTargetState.spellId, SpellId::Starburst);

        if (mobileGroundTargetConfirmSpell)
        {
            prompt += Engine::tr("  Drag target  Spell button cast  Pause cancel");
        }
        else if (pendingTargetState.targetKind == PartySpellCastTargetKind::Character)
        {
            prompt += Engine::tr("  Tap portrait  Pause cancel");
        }
        else if (pendingTargetState.targetKind == PartySpellCastTargetKind::CharacterOrWorldTarget)
        {
            prompt += Engine::tr("  Tap target  Pause cancel");
        }
        else if (pendingTargetState.targetKind == PartySpellCastTargetKind::Actor
            || pendingTargetState.targetKind == PartySpellCastTargetKind::ActorOrCharacter)
        {
            prompt += Engine::tr("  Tap target  Pause cancel");
        }
        else
        {
            prompt += Engine::tr("  Tap target  Pause cancel");
        }
#else
        prompt += Engine::tr("  LMB cast  Esc cancel");
#endif
    }

    return prompt;
}

void GameplaySpellService::showPendingTargetSelectionPrompt(
    GameplayScreenRuntime &runtime,
    bool includeControls,
    float durationSeconds) const
{
    const GameplayScreenState::PendingSpellTargetState &pendingTargetState =
        m_session.gameplayScreenState().pendingSpellTarget();

    if (!pendingTargetState.active)
    {
        return;
    }

    runtime.setStatusBarEvent(pendingTargetSelectionPromptText(includeControls), durationSeconds);
}

bool GameplaySpellService::validatePendingTargetSelectionRequest(
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &request) const
{
    const GameplayScreenState::PendingSpellTargetState &pendingTargetState =
        m_session.gameplayScreenState().pendingSpellTarget();

    bool targetResolved = true;

    switch (pendingTargetState.targetKind)
    {
        case PartySpellCastTargetKind::Actor:
            targetResolved = request.targetActorIndex.has_value();
            break;

        case PartySpellCastTargetKind::Character:
            targetResolved = request.targetCharacterIndex.has_value();
            break;

        case PartySpellCastTargetKind::CharacterOrWorldTarget:
            targetResolved = request.targetCharacterIndex.has_value() || request.targetWorldHit.has_value();
            break;

        case PartySpellCastTargetKind::ActorOrCharacter:
            targetResolved = request.targetActorIndex.has_value() || request.targetCharacterIndex.has_value();
            break;

        case PartySpellCastTargetKind::GroundPoint:
            targetResolved = request.hasTargetPoint;
            break;

        case PartySpellCastTargetKind::TelekinesisTarget:
            targetResolved = request.telekinesisTarget.has_value();
            break;

        default:
            break;
    }

    if (targetResolved)
    {
        return true;
    }

    showPendingTargetSelectionPrompt(runtime);
    return false;
}

GameplaySpellService::PendingTargetResolution GameplaySpellService::resolvePendingTargetSelectionCast(
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &request) const
{
    PendingTargetResolution resolution = {};
    resolution.castResult = m_session.playerCommands().castSpell(LocalPlayer, runtime, request);

    if (resolution.castResult.succeeded())
    {
        const std::string spellName = m_session.gameplayScreenState().pendingSpellTarget().spellName;
        applySuccessFeedback(runtime, request, spellName, resolution.castResult);
        resolution.disposition = PendingTargetResolutionDisposition::CastSucceeded;
        return resolution;
    }

    if (requiresTargetSelection(resolution.castResult))
    {
        showPendingTargetSelectionPrompt(runtime);
        resolution.disposition = PendingTargetResolutionDisposition::NeedsTargetSelection;
        return resolution;
    }

    applyFailureFeedback(runtime, request, resolution.castResult);
    clearPendingTargetSelection(runtime);
    return resolution;
}

bool GameplaySpellService::tryValidateCasterForGameplayCast(GameplayScreenRuntime &runtime, size_t casterMemberIndex)
{
    Party *pParty = runtime.party();

    if (pParty == nullptr)
    {
        return false;
    }

    const Character *pCaster = pParty->member(casterMemberIndex);

    if (pCaster == nullptr || !GameMechanics::canTakeGameplayAction(*pCaster))
    {
        return false;
    }

    return true;
}

PartySpellCastResult GameplaySpellService::castSpell(
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &request) const
{
    Party *pParty = runtime.party();
    IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();
    const SpellTable *pSpellTable = runtime.spellTable();

    if (pParty == nullptr || pWorldRuntime == nullptr || pSpellTable == nullptr)
    {
        return {};
    }

    PartySpellCastRequest effectiveRequest = request;
    TurnBasedCombatRuntime &turnBasedCombatRuntime = runtime.turnBasedCombatRuntime();
    const bool turnBasedRecovery =
        turnBasedCombatRuntime.active()
        && request.applyRecovery
        && turnBasedCombatRuntime.stage() == TurnBasedCombatStage::Attack;

    if (turnBasedRecovery)
    {
        effectiveRequest.applyRecovery = false;
        effectiveRequest.turnBasedPendingAction = true;
    }

    PartySpellCastResult result = PartySpellSystem::castSpell(*pParty, *pWorldRuntime, *pSpellTable, effectiveRequest);

    if (turnBasedRecovery
        && (result.recoverySeconds > 0.0f || result.status == PartySpellCastStatus::NotEnoughSpellPoints))
    {
        turnBasedCombatRuntime.storeMemberTurnRecovery(request.casterMemberIndex, result.recoverySeconds);

        turnBasedCombatRuntime.applyPlayerAction(*pParty, request.casterMemberIndex, result.recoverySeconds);
    }

    return result;
}

bool GameplaySpellService::isQuickCastable(const PartySpellDescriptor &descriptor)
{
    if (spellIdFromValue(descriptor.spellId) == SpellId::MeteorShower
        || spellIdFromValue(descriptor.spellId) == SpellId::Starburst)
    {
        return false;
    }

    if (descriptor.targetKind == PartySpellCastTargetKind::None)
    {
        return true;
    }

    if (descriptor.targetKind == PartySpellCastTargetKind::Character)
    {
        return PartySpellSystem::hasQuickCastCharacterTarget(descriptor.spellId);
    }

    if (descriptor.targetKind == PartySpellCastTargetKind::Actor)
    {
        return descriptor.effectKind == PartySpellCastEffectKind::Projectile
            || descriptor.effectKind == PartySpellCastEffectKind::ActorEffect;
    }

    if (descriptor.targetKind == PartySpellCastTargetKind::GroundPoint)
    {
        return descriptor.effectKind == PartySpellCastEffectKind::Projectile
            || descriptor.effectKind == PartySpellCastEffectKind::MultiProjectile
            || descriptor.effectKind == PartySpellCastEffectKind::AreaEffect;
    }

    return false;
}

bool GameplaySpellService::requiresTargetSelection(const PartySpellCastResult &result)
{
    return result.status == PartySpellCastStatus::NeedActorTarget
        || result.status == PartySpellCastStatus::NeedCharacterTarget
        || result.status == PartySpellCastStatus::NeedCharacterOrWorldTarget
        || result.status == PartySpellCastStatus::NeedActorOrCharacterTarget
        || result.status == PartySpellCastStatus::NeedGroundPoint
        || result.status == PartySpellCastStatus::NeedTelekinesisTarget;
}

bool GameplaySpellService::tryOpenSelectionUi(
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &request,
    const std::string &spellName,
    const PartySpellCastResult &result)
{
    if (result.status == PartySpellCastStatus::NeedInventoryItemTarget)
    {
        runtime.closeSpellbookOverlay();
        runtime.characterScreen().open = true;
        runtime.characterScreen().dollJewelryOverlayOpen = false;
        runtime.characterScreen().adventurersInnRosterOverlayOpen = false;
        runtime.characterScreen().source = GameplayUiController::CharacterScreenSource::Party;
        runtime.characterScreen().sourceIndex = request.casterMemberIndex;
        runtime.characterScreen().page = GameplayUiController::CharacterPage::Inventory;
        runtime.openUtilitySpellOverlay(
            GameplayUiController::UtilitySpellOverlayMode::InventoryTarget,
            request.spellId,
            request.casterMemberIndex);
        runtime.setStatusBarEvent(
            Engine::tr("Select item for {spell}", {{"spell", Engine::localizeKnown(spellName, "spell")}}), 4.0f);
        return true;
    }

    if (result.status != PartySpellCastStatus::NeedUtilityUi)
    {
        return false;
    }

    runtime.closeSpellbookOverlay();

    if (isSpellId(request.spellId, SpellId::TownPortal))
    {
        if (!runtime.ensureTownPortalDestinationsLoaded())
        {
            runtime.setStatusBarEvent(Engine::tr("Town Portal data missing"));
            return true;
        }

        runtime.openUtilitySpellOverlay(
            GameplayUiController::UtilitySpellOverlayMode::TownPortal,
            request.spellId,
            request.casterMemberIndex);
        runtime.resetUtilitySpellOverlayInteractionState();
        runtime.setStatusBarEvent(Engine::tr("Choose Town Portal destination"), 4.0f);
        return true;
    }

    if (isSpellId(request.spellId, SpellId::LloydsBeacon))
    {
        const Party *pParty = runtime.partyReadOnly();
        const Character *pCaster = pParty != nullptr ? pParty->member(request.casterMemberIndex) : nullptr;

        runtime.openUtilitySpellOverlay(
            GameplayUiController::UtilitySpellOverlayMode::LloydsBeacon,
            request.spellId,
            request.casterMemberIndex,
            lloydsBeaconHasRecallableBeacon(pCaster));
        runtime.resetUtilitySpellOverlayInteractionState();
        runtime.setStatusBarEvent(Engine::tr("Set or recall beacon"), 4.0f);
        return true;
    }

    return false;
}

void GameplaySpellService::applySuccessFeedback(
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &request,
    const std::string &spellName,
    const PartySpellCastResult &result) const
{
    if (isUtilitySelectionRequest(request))
    {
        runtime.closeUtilitySpellOverlayAfterSpellResolution(request.spellId);
    }

    runtime.triggerPortraitFaceAnimation(request.casterMemberIndex, FaceAnimationId::CastSpell);
    runtime.playSpeechReaction(request.casterMemberIndex, SpeechId::CastSpell, false);
    runtime.noteSpellCast();

    if (isSpellId(request.spellId, SpellId::Awaken) && !result.affectedCharacterIndices.empty())
    {
        runtime.playSpeechReaction(result.affectedCharacterIndices.front(), SpeechId::Awaken, true);
    }

    m_session.gameplayFxService().triggerPortraitSpellFx(result);
    if (result.screenOverlayRequest.has_value())
    {
        m_session.gameplayFxService().triggerGameplayScreenOverlay(*result.screenOverlayRequest);
    }

    if (runtime.audioSystem() != nullptr && runtime.spellTable() != nullptr)
    {
        const SpellEntry *pSpellEntry = runtime.spellTable()->findById(request.spellId);

        if (result.effectKind == PartySpellCastEffectKind::CharacterRestore
            || result.effectKind == PartySpellCastEffectKind::PartyRestore)
        {
            runtime.audioSystem()->playCommonSound(SoundId::Heal, GameAudioSystem::PlaybackGroup::Ui);
        }
        else if (pSpellEntry != nullptr
            && pSpellEntry->effectSoundId > 0
            && result.effectKind != PartySpellCastEffectKind::Projectile
            && result.effectKind != PartySpellCastEffectKind::MultiProjectile)
        {
            runtime.audioSystem()->playSound(
                pSpellEntry->effectSoundId,
                GameAudioSystem::PlaybackGroup::Ui);
        }
    }

    const std::string statusText = successStatusText(spellName, result);

    if (!statusText.empty())
    {
        runtime.setStatusBarEvent(statusText);
    }
}

std::string GameplaySpellService::successStatusText(const std::string &spellName, const PartySpellCastResult &result)
{
    if (!result.statusText.empty())
    {
        return result.statusText;
    }

    if (spellName.empty() || result.effectKind == PartySpellCastEffectKind::Telekinesis)
    {
        return {};
    }

    return Engine::tr("Cast {spell}", {{"spell", Engine::localizeKnown(spellName, "spell")}});
}

void GameplaySpellService::applyFailureFeedback(
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &request,
    const PartySpellCastResult &result) const
{
    if (isUtilitySelectionRequest(request))
    {
        runtime.closeUtilitySpellOverlayAfterSpellResolution(request.spellId);
    }

    runtime.triggerSpellFailureFeedback(request.casterMemberIndex, result.statusText);
}
}
