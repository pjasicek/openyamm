#include "game/gameplay/WorldItemSpotter.h"

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
float distanceSquared(const bx::Vec3 &a, const bx::Vec3 &b)
{
    const float dx = a.x - b.x;
    const float dy = a.y - b.y;
    const float dz = a.z - b.z;
    return dx * dx + dy * dy + dz * dz;
}
}

void WorldItemSpotter::reset()
{
    *this = WorldItemSpotter{};
}

size_t WorldItemSpotter::update(
    float deltaSeconds,
    float radius,
    const bx::Vec3 &eye,
    size_t itemCount,
    const CandidatePoint &candidatePoint,
    const TrySpot &trySpot)
{
    m_secondsSinceCheck += std::max(0.0f, deltaSeconds);

    if (m_secondsSinceCheck < CheckSeconds || radius <= 0.0f)
    {
        return 0;
    }

    const float elapsed = m_secondsSinceCheck;
    m_secondsSinceCheck = 0.0f;

    if (m_resting)
    {
        m_restSeconds += elapsed;

        if (itemCount == m_restItemCount && m_restSeconds < RetrySeconds
            && distanceSquared(eye, m_restEye) < RetryDistance * RetryDistance)
        {
            return 0;
        }

        m_resting = false;
    }

    if (itemCount == 0)
    {
        m_passRemaining = 0;
    }

    // A new pass visits every item once, from wherever the last one stopped; items taken or added meanwhile only
    // shorten it.
    if (m_passRemaining == 0)
    {
        m_passRemaining = itemCount;
    }

    m_passRemaining = std::min(m_passRemaining, itemCount);

    if (m_cursor >= itemCount)
    {
        m_cursor = 0;
    }

    const float radiusSquared = radius * radius;
    size_t rays = 0;

    while (m_passRemaining > 0)
    {
        const std::optional<bx::Vec3> point = candidatePoint(m_cursor);

        if (point && distanceSquared(eye, *point) <= radiusSquared)
        {
            // The budget is spent: the next check starts with this item.
            if (rays == MaxRaysPerCheck)
            {
                return rays;
            }

            ++rays;
            trySpot(m_cursor, eye, *point);
        }

        m_cursor = (m_cursor + 1) % itemCount;
        --m_passRemaining;
    }

    m_resting = true;
    m_restEye = eye;
    m_restItemCount = itemCount;
    m_restSeconds = 0.0f;
    return rays;
}
}
