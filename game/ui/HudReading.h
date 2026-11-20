#pragma once

#include <cstdint>
#include <optional>
#include <utility>

namespace OpenYAMM::Game
{
// A fact the HUD shows that is costly to work out (it walks the map's actors or the party's bags) and harmless to
// show a moment late: worked out again when its subject changes or when the reading is older than its age limit,
// not on every frame (devdocs/HUD_RENDERING.md, "Facts that are costly to work out").
//
// The age limit bounds how old a shown value can be by construction. Nothing has to tell the HUD that the fact
// changed, so no writer anywhere in the game can forget to.
template <typename Value, typename Subject>
class HudReading
{
public:
    // The fact about `subject` at `nowMilliseconds`, from `compute()` when the stored one cannot be used.
    template <typename Compute>
    const Value &get(const Subject &subject, uint64_t nowMilliseconds, uint64_t maxAgeMilliseconds, Compute &&compute)
    {
        if (!m_reading || !(m_reading->subject == subject) || nowMilliseconds < m_reading->milliseconds
            || nowMilliseconds - m_reading->milliseconds >= maxAgeMilliseconds)
        {
            m_reading = Reading{subject, nowMilliseconds, std::forward<Compute>(compute)()};
        }

        return m_reading->value;
    }

    // Forgets the reading: the next get works it out.
    void reset()
    {
        m_reading.reset();
    }

private:
    struct Reading
    {
        Subject subject;
        uint64_t milliseconds = 0;
        Value value;
    };

    std::optional<Reading> m_reading;
};
}
