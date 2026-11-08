#pragma once

#include "game/events/EventRuntime.h"

#include <cstddef>
#include <cstdint>
#include <optional>

namespace OpenYAMM::Game
{
class IGameplayWorldRuntime;
struct EventDialogContent;
struct HouseEntry;

// Who speaks in an MM9 dialogue: an actor, or a posed talking prop (an MM9 RUDEProp placed as a decoration whose click
// opens the talk), by its decoration's sprite override key. Neither for a speaker that is no actor or prop.
struct Mm9DialogueSpeaker
{
    std::optional<size_t> actorIndex;
    std::optional<uint32_t> decorationKey;

    explicit operator bool() const
    {
        return actorIndex.has_value() || decorationKey.has_value();
    }
};

// The talking prop speaking in an MM9 dialogue: the decoration whose click opened the talk
// (DialogueRuntimeState::mm9RudeSourceDecorationKey), also in the house dialogue of a venue its talk opened (the talk
// waits in suspendedMm9RudeDialogue). None when an actor opened it.
std::optional<uint32_t> findMm9DialogueSpeakerDecoration(const EventDialogContent &dialog,
    const EventRuntimeState::DialogueRuntimeState &dialogueState);

// The speaker of an MM9 dialogue: the actor the talk was opened on, else the prop whose click opened it
// (findMm9DialogueSpeakerDecoration), else the nearest living actor with the talk's RUDE id (a talk opened by an
// event) or, in the house dialogue of an MM9 shop or service venue, with the venue's (its source id is the RUDE id that
// opens it). None for a speaker that is neither (Bjarni on his throne).
Mm9DialogueSpeaker findMm9DialogueSpeaker(const IGameplayWorldRuntime &world, const EventDialogContent &dialog,
    const HouseEntry *pHouse);
}
