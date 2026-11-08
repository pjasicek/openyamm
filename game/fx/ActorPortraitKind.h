#pragma once

#include <cstddef>
#include <cstdint>

namespace OpenYAMM::Game
{
// What an actor portrait (WorldFxSystem::syncInspectPortrait, ActorModelPreview) shows: the inspect popup's whole
// creature demonstrating its fidget and attack, or the head and shoulders of a speaking MM9 actor (the talk ring, a
// venue's sidebar), standing and fidgeting.
enum class ActorPortraitKind : uint8_t
{
    Inspect = 0,
    Talk,
};

constexpr size_t ActorPortraitKindCount = 2;
}
