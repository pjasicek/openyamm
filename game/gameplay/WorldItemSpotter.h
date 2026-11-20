#pragma once

#include <bx/math.h>

#include <cstddef>
#include <functional>
#include <optional>

namespace OpenYAMM::Game
{
// Spots the ground items the party passes near with nothing of the map in between (ItemRules::worldItemSpotting; the
// gather key on a completed map collects them). It never runs per frame: one check every quarter second, distances
// first and at most two line-of-sight rays a check, then rest while the party stays near where its last full pass
// ended and no item came or went. A spotted item keeps SpriteAttrSpotted, which takes it out of the candidates for good.
class WorldItemSpotter
{
public:
    static constexpr float CheckSeconds = 0.25f;
    static constexpr size_t MaxRaysPerCheck = 2;
    // How far the party moves, or how long it waits, before items hidden at the last pass are tried again (a door that
    // opened, an item that landed).
    static constexpr float RetryDistance = 128.0f;
    static constexpr float RetrySeconds = 2.0f;

    // The point an item's ray ends at, or none when the item is no candidate (spotted already, gone, not an item).
    using CandidatePoint = std::function<std::optional<bx::Vec3>(size_t itemIndex)>;
    // Casts the ray to a candidate in range and marks the item spotted when nothing is in between.
    using TrySpot = std::function<void(size_t itemIndex, const bx::Vec3 &eye, const bx::Vec3 &point)>;

    void reset();
    // Returns how many rays the call cast.
    size_t update(
        float deltaSeconds,
        float radius,
        const bx::Vec3 &eye,
        size_t itemCount,
        const CandidatePoint &candidatePoint,
        const TrySpot &trySpot);

private:
    float m_secondsSinceCheck = 0.0f;
    // The next item the pass visits, and how many it has left to visit.
    size_t m_cursor = 0;
    size_t m_passRemaining = 0;
    bool m_resting = false;
    bx::Vec3 m_restEye = {0.0f, 0.0f, 0.0f};
    size_t m_restItemCount = 0;
    float m_restSeconds = 0.0f;
};
}
