#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>

namespace OpenYAMM::Game
{
// Lives with the held item, so replacing or consuming that item also cancels the gesture.
class InventoryItemDoubleClick
{
public:
    void arm(size_t memberIndex, uint64_t ticks, float x, float y, float tolerance)
    {
        m_memberIndex = memberIndex;
        m_ticks = ticks;
        m_x = x;
        m_y = y;
        m_tolerance = tolerance;
    }

    void cancel()
    {
        m_memberIndex.reset();
    }

    void update(size_t memberIndex, uint64_t ticks, float x, float y)
    {
        const float dx = x - m_x;
        const float dy = y - m_y;

        if (m_memberIndex != memberIndex || ticks < m_ticks || ticks - m_ticks > 500
            || dx * dx + dy * dy > m_tolerance * m_tolerance)
        {
            cancel();
        }
    }

    bool pending() const
    {
        return m_memberIndex.has_value();
    }

private:
    std::optional<size_t> m_memberIndex;
    uint64_t m_ticks = 0;
    float m_x = 0.0f;
    float m_y = 0.0f;
    float m_tolerance = 0.0f;
};
} // namespace OpenYAMM::Game
