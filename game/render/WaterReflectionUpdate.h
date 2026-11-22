#pragma once

#include <algorithm>
#include <array>
#include <cstdint>

namespace OpenYAMM::Game
{
// Static reflections can reuse their texture between animation refreshes. Content changes render immediately,
// including while gameplay is paused; uncovered camera changes do too while paused, and otherwise at most 120 times a
// second: above that rate the capture, sampled through its own matrix, stays registered with the world.
class WaterReflectionUpdate
{
public:
    bool prepare(const float *pViewProjection, const std::array<float, 4> &plane, uint16_t size, float seconds,
        uint64_t visualRevision, bool buildings, bool viewCovered = false, bool billboards = false)
    {
        constexpr float AnimationInterval = 1.0f / 30.0f;
        constexpr float CameraInterval = 1.0f / 120.0f;
        const bool cameraMoved = !viewCovered
            && !std::equal(m_viewProjection.begin(), m_viewProjection.end(), pViewProjection);
        const bool update = m_seconds < 0.0f || seconds < m_seconds || seconds - m_seconds >= AnimationInterval
            || m_plane != plane || m_size != size || m_visualRevision != visualRevision || m_buildings != buildings
            || m_billboards != billboards
            || (cameraMoved && (seconds == m_seconds || seconds - m_seconds >= CameraInterval));
        if (update)
        {
            std::copy_n(pViewProjection, m_viewProjection.size(), m_viewProjection.begin());
            m_seconds = seconds;
            m_plane = plane;
            m_size = size;
            m_visualRevision = visualRevision;
            m_buildings = buildings;
            m_billboards = billboards;
        }
        return update;
    }

    // The last capture shows this plane at this size (its own matrix keeps it registered with the world).
    bool holds(const std::array<float, 4> &plane, uint16_t size) const
    {
        return m_seconds >= 0.0f && m_plane == plane && m_size == size;
    }

private:
    std::array<float, 16> m_viewProjection = {};
    float m_seconds = -1.0f;
    std::array<float, 4> m_plane = {};
    uint64_t m_visualRevision = 0;
    uint16_t m_size = 0;
    bool m_buildings = false;
    bool m_billboards = false;
};
}
