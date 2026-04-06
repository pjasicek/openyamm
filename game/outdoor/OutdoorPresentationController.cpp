#include "game/outdoor/OutdoorPresentationController.h"

#include "game/audio/GameAudioSystem.h"
#include "game/gameplay/GameMechanics.h"
#include "game/outdoor/OutdoorGameView.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/tables/PortraitEnums.h"
#include "game/StringUtils.h"
#include "game/ui/HudUiService.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t SpeechReactionCooldownMs = 900;
constexpr uint32_t CombatSpeechReactionCooldownMs = 2500;
constexpr float WalkingSoundMovementSpeedThreshold = 20.0f;
constexpr float WalkingMotionHoldSeconds = 0.125f;

uint32_t currentAnimationTicks()
{
    return static_cast<uint32_t>((static_cast<uint64_t>(SDL_GetTicks()) * 128ULL) / 1000ULL);
}

uint32_t mixPortraitSequenceValue(uint32_t value)
{
    value ^= value >> 16;
    value *= 0x7feb352du;
    value ^= value >> 15;
    value *= 0x846ca68bu;
    value ^= value >> 16;
    return value;
}

PortraitId pickIdlePortrait(uint32_t sequenceValue)
{
    const uint32_t randomValue = sequenceValue % 100u;

    if (randomValue < 25u)
    {
        return PortraitId::Blink;
    }

    if (randomValue < 31u)
    {
        return PortraitId::Wink;
    }

    if (randomValue < 37u)
    {
        return PortraitId::MouthOpenRandom;
    }

    if (randomValue < 43u)
    {
        return PortraitId::PurseLipsRandom;
    }

    if (randomValue < 46u)
    {
        return PortraitId::LookUp;
    }

    if (randomValue < 52u)
    {
        return PortraitId::LookRight;
    }

    if (randomValue < 58u)
    {
        return PortraitId::LookLeft;
    }

    if (randomValue < 64u)
    {
        return PortraitId::LookDown;
    }

    if (randomValue < 70u)
    {
        return PortraitId::Portrait54;
    }

    if (randomValue < 76u)
    {
        return PortraitId::Portrait55;
    }

    if (randomValue < 82u)
    {
        return PortraitId::Portrait56;
    }

    if (randomValue < 88u)
    {
        return PortraitId::Portrait57;
    }

    if (randomValue < 94u)
    {
        return PortraitId::PurseLips1;
    }

    return PortraitId::PurseLips2;
}

uint32_t pickNormalPortraitDurationTicks(uint32_t sequenceValue)
{
    return 32u + (sequenceValue % 257u);
}

bool portraitExpressionAllowedForCondition(
    const std::optional<CharacterCondition> &displayedCondition,
    PortraitId newPortrait)
{
    if (!displayedCondition)
    {
        return true;
    }

    const std::optional<PortraitId> currentPortrait = portraitIdForCondition(*displayedCondition);

    if (!currentPortrait)
    {
        return true;
    }

    if (*currentPortrait == PortraitId::Dead || *currentPortrait == PortraitId::Eradicated)
    {
        return false;
    }

    if (*currentPortrait == PortraitId::Petrified)
    {
        return newPortrait == PortraitId::WakeUp;
    }

    if (*currentPortrait == PortraitId::Sleep && newPortrait == PortraitId::WakeUp)
    {
        return true;
    }

    if ((*currentPortrait >= PortraitId::Cursed && *currentPortrait <= PortraitId::Unconscious)
        && *currentPortrait != PortraitId::Poisoned)
    {
        return isDamagePortrait(newPortrait);
    }

    return true;
}

bool bypassSpeechCooldown(SpeechId speechId)
{
    switch (speechId)
    {
    case SpeechId::IdentifyWeakItem:
    case SpeechId::IdentifyGreatItem:
    case SpeechId::IdentifyFailItem:
    case SpeechId::RepairSuccess:
    case SpeechId::RepairFail:
    case SpeechId::CantLearnSpell:
    case SpeechId::LearnSpell:
        return true;

    default:
        return false;
    }
}

} // namespace

void OutdoorPresentationController::updatePartyPortraitAnimations(OutdoorGameView &view, float deltaSeconds)
{
    if (view.m_pOutdoorPartyRuntime == nullptr)
    {
        return;
    }

    (void)deltaSeconds;
    const uint32_t nowTicks = currentAnimationTicks();

    if (view.m_lastPortraitAnimationUpdateTicks == 0)
    {
        view.m_lastPortraitAnimationUpdateTicks = nowTicks;
    }

    const uint32_t deltaTicks = nowTicks - view.m_lastPortraitAnimationUpdateTicks;
    view.m_lastPortraitAnimationUpdateTicks = nowTicks;

    if (deltaTicks == 0)
    {
        return;
    }

    Party &party = view.m_pOutdoorPartyRuntime->party();

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        Character *pMember = party.member(memberIndex);

        if (pMember == nullptr)
        {
            continue;
        }

        view.updatePortraitAnimation(*pMember, memberIndex, deltaTicks);
    }
}

void OutdoorPresentationController::updatePortraitAnimation(
    OutdoorGameView &view,
    Character &member,
    size_t memberIndex,
    uint32_t deltaTicks)
{
    member.portraitElapsedTicks += deltaTicks;
    const std::optional<CharacterCondition> displayedCondition = GameMechanics::displayedCondition(member);

    if (displayedCondition)
    {
        const std::optional<PortraitId> conditionPortrait = portraitIdForCondition(*displayedCondition);

        if (conditionPortrait)
        {
            if (isDamagePortrait(member.portraitState)
                && member.portraitDurationTicks > 0
                && member.portraitElapsedTicks < member.portraitDurationTicks)
            {
                return;
            }

            if (member.portraitState != *conditionPortrait || member.portraitDurationTicks != 0)
            {
                member.portraitState = *conditionPortrait;
                member.portraitElapsedTicks = 0;
                member.portraitDurationTicks = 0;
            }

            return;
        }
    }

    if (member.portraitDurationTicks > 0 && member.portraitElapsedTicks < member.portraitDurationTicks)
    {
        return;
    }

    member.portraitElapsedTicks = 0;
    const uint32_t sequenceValue = mixPortraitSequenceValue(
        static_cast<uint32_t>(memberIndex + 1u) * 2654435761u + member.portraitSequenceCounter++);

    if (member.portraitState != PortraitId::Normal || (sequenceValue % 5u) != 0u)
    {
        member.portraitState = PortraitId::Normal;
        member.portraitDurationTicks = pickNormalPortraitDurationTicks(sequenceValue);
        return;
    }

    member.portraitState = pickIdlePortrait(sequenceValue);
    member.portraitDurationTicks = view.defaultPortraitAnimationLengthTicks(member.portraitState);
}

void OutdoorPresentationController::playPortraitExpression(
    OutdoorGameView &view,
    size_t memberIndex,
    PortraitId portraitId,
    std::optional<uint32_t> durationTicks)
{
    if (view.m_pOutdoorPartyRuntime == nullptr)
    {
        return;
    }

    Character *pMember = view.m_pOutdoorPartyRuntime->party().member(memberIndex);

    if (pMember == nullptr)
    {
        return;
    }

    const std::optional<CharacterCondition> displayedCondition = GameMechanics::displayedCondition(*pMember);

    if (!portraitExpressionAllowedForCondition(displayedCondition, portraitId))
    {
        return;
    }

    pMember->portraitState = portraitId;
    pMember->portraitElapsedTicks = 0;
    pMember->portraitDurationTicks = durationTicks.value_or(view.defaultPortraitAnimationLengthTicks(portraitId));
    pMember->portraitSequenceCounter += 1;
}

void OutdoorPresentationController::triggerPortraitFaceAnimation(
    OutdoorGameView &view,
    size_t memberIndex,
    FaceAnimationId animationId)
{
    const FaceAnimationEntry *pEntry = view.m_faceAnimationTable.find(animationId);

    if (pEntry == nullptr || pEntry->portraitIds.empty())
    {
        return;
    }

    const uint32_t sequenceValue = mixPortraitSequenceValue(
        currentAnimationTicks() ^ static_cast<uint32_t>(memberIndex + 1u) ^ static_cast<uint32_t>(pEntry->portraitIds.size()));
    const size_t choiceIndex = static_cast<size_t>(sequenceValue % pEntry->portraitIds.size());

    view.playPortraitExpression(memberIndex, pEntry->portraitIds[choiceIndex]);
}

void OutdoorPresentationController::triggerPortraitFaceAnimationForAllLivingMembers(
    OutdoorGameView &view,
    FaceAnimationId animationId)
{
    if (view.m_pOutdoorPartyRuntime == nullptr)
    {
        return;
    }

    const std::vector<Character> &members = view.m_pOutdoorPartyRuntime->party().members();

    for (size_t memberIndex = 0; memberIndex < members.size(); ++memberIndex)
    {
        if (members[memberIndex].health <= 0)
        {
            continue;
        }

        view.triggerPortraitFaceAnimation(memberIndex, animationId);
    }
}

bool OutdoorPresentationController::triggerPortraitFxAnimation(
    OutdoorGameView &view,
    const std::string &animationName,
    const std::vector<size_t> &memberIndices)
{
    if (memberIndices.empty())
    {
        return false;
    }

    const std::optional<size_t> animationId = view.m_iconFrameTable.findAnimationIdByName(animationName);

    if (!animationId)
    {
        return false;
    }

    const uint32_t startedTicks = currentAnimationTicks();
    bool triggered = false;

    for (size_t memberIndex : memberIndices)
    {
        if (memberIndex >= view.m_portraitSpellFxStates.size())
        {
            continue;
        }

        OutdoorGameView::PortraitFxState &state = view.m_portraitSpellFxStates[memberIndex];
        state.active = true;
        state.animationId = *animationId;
        state.startedTicks = startedTicks;
        triggered = true;
    }

    return triggered;
}

void OutdoorPresentationController::triggerPortraitSpellFx(OutdoorGameView &view, const PartySpellCastResult &result)
{
    const SpellFxEntry *pSpellFxEntry = view.m_spellFxTable.findBySpellId(result.spellId);

    if (pSpellFxEntry == nullptr)
    {
        return;
    }

    triggerPortraitFxAnimation(view, pSpellFxEntry->animationName, result.affectedCharacterIndices);
}

void OutdoorPresentationController::triggerPortraitEventFx(
    OutdoorGameView &view,
    const EventRuntimeState::PortraitFxRequest &request)
{
    const PortraitFxEventEntry *pEntry = view.m_portraitFxEventTable.findByKind(request.kind);

    if (pEntry == nullptr)
    {
        return;
    }

    triggerPortraitFxAnimation(view, pEntry->animationName, request.memberIndices);

    if (!pEntry->faceAnimationId)
    {
        return;
    }

    for (size_t memberIndex : request.memberIndices)
    {
        view.triggerPortraitFaceAnimation(memberIndex, *pEntry->faceAnimationId);
    }

    if (view.m_pGameAudioSystem == nullptr || request.memberIndices.empty())
    {
        return;
    }

    switch (request.kind)
    {
    case PortraitFxEventKind::AutoNote:
        view.m_pGameAudioSystem->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
        break;

    case PortraitFxEventKind::AwardGain:
        view.m_pGameAudioSystem->playCommonSound(SoundId::Chimes, GameAudioSystem::PlaybackGroup::Ui);
        view.playSpeechReaction(request.memberIndices.front(), SpeechId::AwardGot, false);
        break;

    case PortraitFxEventKind::QuestComplete:
        view.m_pGameAudioSystem->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
        view.playSpeechReaction(request.memberIndices.front(), SpeechId::QuestGot, false);
        break;

    case PortraitFxEventKind::StatIncrease:
        view.m_pGameAudioSystem->playCommonSound(SoundId::Quest, GameAudioSystem::PlaybackGroup::Ui);
        break;

    case PortraitFxEventKind::StatDecrease:
        view.playSpeechReaction(request.memberIndices.front(), SpeechId::Indignant, false);
        break;

    case PortraitFxEventKind::Disease:
        view.playSpeechReaction(request.memberIndices.front(), SpeechId::Poisoned, false);
        break;

    case PortraitFxEventKind::None:
        break;
    }
}

void OutdoorPresentationController::consumePendingPortraitEventFxRequests(OutdoorGameView &view)
{
    if (view.m_pOutdoorWorldRuntime == nullptr)
    {
        return;
    }

    EventRuntimeState *pEventRuntimeState = view.m_pOutdoorWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        return;
    }

    if (pEventRuntimeState->portraitFxRequests.empty() && pEventRuntimeState->spellFxRequests.empty())
    {
        return;
    }

    for (const EventRuntimeState::PortraitFxRequest &request : pEventRuntimeState->portraitFxRequests)
    {
        view.triggerPortraitEventFx(request);
    }

    if (!pEventRuntimeState->portraitFxRequests.empty())
    {
        pEventRuntimeState->portraitFxRequests.clear();
    }

    if (!pEventRuntimeState->spellFxRequests.empty())
    {
        for (const EventRuntimeState::SpellFxRequest &request : pEventRuntimeState->spellFxRequests)
        {
            const SpellFxEntry *pSpellFxEntry = view.m_spellFxTable.findBySpellId(request.spellId);

            if (pSpellFxEntry != nullptr)
            {
                view.triggerPortraitFxAnimation(pSpellFxEntry->animationName, request.memberIndices);
            }

            if (view.m_pGameAudioSystem == nullptr || view.m_pSpellTable == nullptr)
            {
                continue;
            }

            const SpellEntry *pSpellEntry = view.m_pSpellTable->findById(static_cast<int>(request.spellId));

            if (pSpellEntry != nullptr && pSpellEntry->effectSoundId > 0)
            {
                view.m_pGameAudioSystem->playSound(
                    static_cast<uint32_t>(pSpellEntry->effectSoundId),
                    GameAudioSystem::PlaybackGroup::Ui);
            }
        }

        pEventRuntimeState->spellFxRequests.clear();
    }
}

bool OutdoorPresentationController::canPlaySpeechReaction(
    OutdoorGameView &view,
    size_t memberIndex,
    SpeechId speechId,
    uint32_t nowTicks)
{
    if (memberIndex >= view.m_memberSpeechCooldownUntilTicks.size())
    {
        return true;
    }

    if (bypassSpeechCooldown(speechId))
    {
        return true;
    }

    if (nowTicks < view.m_memberSpeechCooldownUntilTicks[memberIndex])
    {
        return false;
    }

    switch (speechId)
    {
    case SpeechId::KillWeakEnemy:
    case SpeechId::KillStrongEnemy:
        return true;

    case SpeechId::DamageMinor:
    case SpeechId::DamageMajor:
    case SpeechId::AttackHit:
    case SpeechId::AttackMiss:
    case SpeechId::Shoot:
    case SpeechId::CastSpell:
    case SpeechId::DamagedParty:
        return nowTicks >= view.m_memberCombatSpeechCooldownUntilTicks[memberIndex];

    default:
        return true;
    }
}

void OutdoorPresentationController::playSpeechReaction(
    OutdoorGameView &view,
    size_t memberIndex,
    SpeechId speechId,
    bool triggerFaceAnimation)
{
    if (view.m_pOutdoorPartyRuntime == nullptr)
    {
        return;
    }

    const Character *pMember = view.m_pOutdoorPartyRuntime->party().member(memberIndex);

    if (pMember == nullptr)
    {
        return;
    }

    const uint32_t nowTicks = currentAnimationTicks();

    if (!canPlaySpeechReaction(view, memberIndex, speechId, nowTicks))
    {
        return;
    }

    const SpeechReactionEntry *pReaction =
        view.m_pGameAudioSystem != nullptr ? view.m_pGameAudioSystem->findSpeechReaction(speechId) : nullptr;
    bool speechPlayed = false;

    if (view.m_pGameAudioSystem != nullptr)
    {
        speechPlayed = view.m_pGameAudioSystem->playSpeech(
            *pMember,
            speechId,
            nowTicks ^ static_cast<uint32_t>(memberIndex),
            static_cast<uint32_t>(memberIndex + 1));
    }

    if (speechPlayed)
    {
        if (memberIndex >= view.m_memberSpeechCooldownUntilTicks.size())
        {
            view.m_memberSpeechCooldownUntilTicks.resize(memberIndex + 1, 0);
            view.m_memberCombatSpeechCooldownUntilTicks.resize(memberIndex + 1, 0);
        }

        if (!bypassSpeechCooldown(speechId))
        {
            view.m_memberSpeechCooldownUntilTicks[memberIndex] = nowTicks + SpeechReactionCooldownMs;
        }

        switch (speechId)
        {
        case SpeechId::DamageMinor:
        case SpeechId::DamageMajor:
        case SpeechId::AttackHit:
        case SpeechId::AttackMiss:
        case SpeechId::Shoot:
        case SpeechId::CastSpell:
        case SpeechId::DamagedParty:
        case SpeechId::KillWeakEnemy:
        case SpeechId::KillStrongEnemy:
            view.m_memberCombatSpeechCooldownUntilTicks[memberIndex] = nowTicks + CombatSpeechReactionCooldownMs;
            break;

        default:
            break;
        }
    }

    if (!triggerFaceAnimation)
    {
        return;
    }

    if (pReaction != nullptr && pReaction->faceAnimationId)
    {
        view.triggerPortraitFaceAnimation(memberIndex, *pReaction->faceAnimationId);
    }
}

void OutdoorPresentationController::consumePendingPartyAudioRequests(OutdoorGameView &view)
{
    if (view.m_pGameAudioSystem == nullptr || view.m_pOutdoorPartyRuntime == nullptr)
    {
        return;
    }

    Party &party = view.m_pOutdoorPartyRuntime->party();
    const std::vector<Party::PendingAudioRequest> requests = party.pendingAudioRequests();

    if (requests.empty())
    {
        return;
    }

    std::optional<GameAudioSystem::WorldPosition> listenerPosition = std::nullopt;
    const OutdoorMoveState &moveState = view.m_pOutdoorPartyRuntime->movementState();
    listenerPosition = GameAudioSystem::WorldPosition{
        moveState.x,
        moveState.y,
        moveState.footZ + view.m_cameraEyeHeight
    };

    for (const Party::PendingAudioRequest &request : requests)
    {
        if (request.kind == Party::PendingAudioRequest::Kind::Speech)
        {
            view.playSpeechReaction(request.memberIndex, request.speechId, true);
            continue;
        }

        GameAudioSystem::PlaybackGroup group = GameAudioSystem::PlaybackGroup::Ui;
        std::optional<GameAudioSystem::WorldPosition> position = std::nullopt;

        if (request.soundId == SoundId::Splash)
        {
            group = GameAudioSystem::PlaybackGroup::World;
            position = listenerPosition;
        }

        view.m_pGameAudioSystem->playCommonSound(request.soundId, group, position);
    }

    party.clearPendingAudioRequests();
}

void OutdoorPresentationController::consumePendingWorldAudioEvents(OutdoorGameView &view)
{
    if (view.m_pGameAudioSystem == nullptr || view.m_pOutdoorWorldRuntime == nullptr)
    {
        return;
    }

    const std::vector<OutdoorWorldRuntime::AudioEvent> &events = view.m_pOutdoorWorldRuntime->pendingAudioEvents();

    if (events.empty())
    {
        return;
    }

    for (const OutdoorWorldRuntime::AudioEvent &event : events)
    {
        std::optional<GameAudioSystem::WorldPosition> position = std::nullopt;

        if (event.positional)
        {
            position = GameAudioSystem::WorldPosition{event.x, event.y, event.z};
        }

        view.m_pGameAudioSystem->playSound(event.soundId, GameAudioSystem::PlaybackGroup::World, position);
    }

    view.m_pOutdoorWorldRuntime->clearPendingAudioEvents();
}

void OutdoorPresentationController::updateFootstepAudio(OutdoorGameView &view, float deltaSeconds)
{
    if (deltaSeconds <= 0.0f || view.m_pGameAudioSystem == nullptr || view.m_pOutdoorPartyRuntime == nullptr || !view.m_outdoorMapData)
    {
        return;
    }

    if (view.currentHudScreenState() != OutdoorGameView::HudScreenState::Gameplay)
    {
        view.m_pGameAudioSystem->stopGroup(GameAudioSystem::PlaybackGroup::Walking);
        view.m_walkingMotionHoldSeconds = 0.0f;
        view.m_activeWalkingSoundId = std::nullopt;
        return;
    }

    const OutdoorMoveState &moveState = view.m_pOutdoorPartyRuntime->movementState();

    if (!view.m_hasLastFootstepPosition)
    {
        view.m_lastFootstepX = moveState.x;
        view.m_lastFootstepY = moveState.y;
        view.m_hasLastFootstepPosition = true;
        return;
    }

    const float deltaX = moveState.x - view.m_lastFootstepX;
    const float deltaY = moveState.y - view.m_lastFootstepY;
    view.m_lastFootstepX = moveState.x;
    view.m_lastFootstepY = moveState.y;
    const float movedDistance = std::sqrt(deltaX * deltaX + deltaY * deltaY);
    const float movementSpeed = movedDistance / std::max(deltaSeconds, 0.0001f);

    if (movementSpeed >= WalkingSoundMovementSpeedThreshold)
    {
        view.m_walkingMotionHoldSeconds = WalkingMotionHoldSeconds;
    }
    else
    {
        view.m_walkingMotionHoldSeconds = std::max(0.0f, view.m_walkingMotionHoldSeconds - deltaSeconds);
    }

    if (moveState.airborne || view.m_walkingMotionHoldSeconds <= 0.0f)
    {
        view.m_pGameAudioSystem->stopGroup(GameAudioSystem::PlaybackGroup::Walking);
        view.m_activeWalkingSoundId = std::nullopt;
        return;
    }

    const OutdoorPartyMovementState &partyMovementState = view.m_pOutdoorPartyRuntime->partyMovementState();
    const bool running = partyMovementState.running;

    const auto chooseBModelFootstepSound =
        [&view, running, &moveState]() -> SoundId
        {
            if (!view.m_outdoorMapData
                || moveState.supportKind != OutdoorSupportKind::BModelFace
                || moveState.supportBModelIndex >= view.m_outdoorMapData->bmodels.size())
            {
                return running ? SoundId::RunStone : SoundId::WalkStone;
            }

            const OutdoorBModel &bmodel = view.m_outdoorMapData->bmodels[moveState.supportBModelIndex];

            if (moveState.supportFaceIndex >= bmodel.faces.size())
            {
                return running ? SoundId::RunStone : SoundId::WalkStone;
            }

            const std::string textureName = toLowerCopy(bmodel.faces[moveState.supportFaceIndex].textureName);

            if (textureName.find("wood") != std::string::npos || textureName.find("plank") != std::string::npos)
            {
                return running ? SoundId::RunWood : SoundId::WalkWood;
            }

            if (textureName.find("carpet") != std::string::npos || textureName.find("rug") != std::string::npos)
            {
                return running ? SoundId::RunCarpet : SoundId::WalkCarpet;
            }

            if (textureName.find("road") != std::string::npos)
            {
                return running ? SoundId::RunRoad : SoundId::WalkRoad;
            }

            if (textureName.find("dirt") != std::string::npos || textureName.find("earth") != std::string::npos)
            {
                return running ? SoundId::RunDirt : SoundId::WalkDirt;
            }

            return running ? SoundId::RunStone : SoundId::WalkStone;
        };

    const auto chooseTerrainFootstepSound =
        [&view, running]() -> SoundId
        {
            if (!view.m_outdoorMapData)
            {
                return running ? SoundId::RunGround : SoundId::WalkGround;
            }

            const std::string tileset = toLowerCopy(view.m_outdoorMapData->groundTilesetName);

            if (tileset.find("grass") != std::string::npos)
            {
                return running ? SoundId::RunGrass : SoundId::WalkGrass;
            }

            if (tileset.find("desert") != std::string::npos || tileset.find("sand") != std::string::npos)
            {
                return running ? SoundId::RunDesert : SoundId::WalkDesert;
            }

            if (tileset.find("snow") != std::string::npos || tileset.find("ice") != std::string::npos)
            {
                return running ? SoundId::RunSnow : SoundId::WalkSnow;
            }

            if (tileset.find("swamp") != std::string::npos)
            {
                return running ? SoundId::RunSwamp : SoundId::WalkSwamp;
            }

            if (tileset.find("badland") != std::string::npos)
            {
                return running ? SoundId::RunBadlands : SoundId::WalkBadlands;
            }

            if (tileset.find("road") != std::string::npos)
            {
                return running ? SoundId::RunRoad : SoundId::WalkRoad;
            }

            return running ? SoundId::RunGround : SoundId::WalkGround;
        };

    SoundId soundId = SoundId::None;

    if (moveState.supportOnWater)
    {
        soundId = running ? SoundId::RunWater : SoundId::WalkWater;
    }
    else if (moveState.supportKind == OutdoorSupportKind::BModelFace)
    {
        soundId = chooseBModelFootstepSound();
    }
    else
    {
        soundId = chooseTerrainFootstepSound();
    }

    if (soundId == SoundId::None)
    {
        view.m_pGameAudioSystem->stopGroup(GameAudioSystem::PlaybackGroup::Walking);
        view.m_activeWalkingSoundId = std::nullopt;
        return;
    }

    if (view.m_activeWalkingSoundId && *view.m_activeWalkingSoundId == soundId)
    {
        return;
    }

    if (view.m_pGameAudioSystem->playLoopingSound(
            static_cast<uint32_t>(soundId),
            GameAudioSystem::PlaybackGroup::Walking))
    {
        view.m_activeWalkingSoundId = soundId;
    }
}

void OutdoorPresentationController::renderPortraitFx(
    const OutdoorGameView &view,
    size_t memberIndex,
    float portraitX,
    float portraitY,
    float portraitWidth,
    float portraitHeight)
{
    if (memberIndex >= view.m_portraitSpellFxStates.size())
    {
        return;
    }

    const OutdoorGameView::PortraitFxState &state = view.m_portraitSpellFxStates[memberIndex];

    if (!state.active)
    {
        return;
    }

    const int32_t animationLengthTicks = view.m_iconFrameTable.animationLengthTicks(state.animationId);
    const uint32_t nowTicks = currentAnimationTicks();
    const uint32_t elapsedTicks = nowTicks - state.startedTicks;

    if (animationLengthTicks <= 0 || elapsedTicks >= static_cast<uint32_t>(animationLengthTicks))
    {
        return;
    }

    const IconFrameEntry *pFrame = view.m_iconFrameTable.getFrame(state.animationId, elapsedTicks);

    if (pFrame == nullptr || pFrame->textureName.empty())
    {
        return;
    }

    const OutdoorGameView::HudTextureHandle *pTexture =
        HudUiService::ensureHudTextureLoaded(const_cast<OutdoorGameView &>(view), pFrame->textureName);

    if (pTexture == nullptr || pTexture->width <= 0 || pTexture->height <= 0)
    {
        return;
    }

    const float textureAspectRatio = static_cast<float>(pTexture->width) / static_cast<float>(pTexture->height);
    const float renderHeight = portraitHeight;
    const float renderWidth = renderHeight * textureAspectRatio;
    const float renderX = portraitX + (portraitWidth - renderWidth) * 0.5f;
    const float renderY = portraitY;
    view.submitHudTexturedQuad(*pTexture, renderX, renderY, renderWidth, renderHeight);
}
} // namespace OpenYAMM::Game
