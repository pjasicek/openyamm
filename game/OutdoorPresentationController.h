#pragma once

#include "game/EventRuntime.h"
#include "game/PartySpellSystem.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class Character;
class OutdoorGameView;

class OutdoorPresentationController
{
public:
    static void updatePartyPortraitAnimations(OutdoorGameView &view, float deltaSeconds);
    static void updatePortraitAnimation(OutdoorGameView &view, Character &member, size_t memberIndex, uint32_t deltaTicks);
    static void playPortraitExpression(
        OutdoorGameView &view,
        size_t memberIndex,
        PortraitId portraitId,
        std::optional<uint32_t> durationTicks = std::nullopt);
    static void triggerPortraitFaceAnimation(OutdoorGameView &view, size_t memberIndex, FaceAnimationId animationId);
    static void triggerPortraitFaceAnimationForAllLivingMembers(OutdoorGameView &view, FaceAnimationId animationId);
    static bool triggerPortraitFxAnimation(
        OutdoorGameView &view,
        const std::string &animationName,
        const std::vector<size_t> &memberIndices);
    static void triggerPortraitSpellFx(OutdoorGameView &view, const PartySpellCastResult &result);
    static void triggerPortraitEventFx(OutdoorGameView &view, const EventRuntimeState::PortraitFxRequest &request);
    static void consumePendingPortraitEventFxRequests(OutdoorGameView &view);
    static bool canPlaySpeechReaction(OutdoorGameView &view, size_t memberIndex, SpeechId speechId, uint32_t nowTicks);
    static void playSpeechReaction(
        OutdoorGameView &view,
        size_t memberIndex,
        SpeechId speechId,
        bool triggerFaceAnimation);
    static void consumePendingPartyAudioRequests(OutdoorGameView &view);
    static void consumePendingWorldAudioEvents(OutdoorGameView &view);
    static void updateFootstepAudio(OutdoorGameView &view, float deltaSeconds);
    static void renderPortraitFx(
        const OutdoorGameView &view,
        size_t memberIndex,
        float portraitX,
        float portraitY,
        float portraitWidth,
        float portraitHeight);
};
} // namespace OpenYAMM::Game
