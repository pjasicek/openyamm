#pragma once

#include "game/events/EventRuntime.h"
#include "game/mm9/Mm9MapTransition.h"

#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9PositionedTransitionActivation
{
    const Mm9MapTransition *pTransition = nullptr;
    EventRuntimeState::PendingMapMove move;
};

class Mm9PositionedTransitionRuntime
{
public:
    void configure(const std::vector<const Mm9MapTransition *> &transitions);
    void resetOverlapState();
    void clear();
    bool empty() const;
    // partyZ is the feet; with a body (radius, height) an exit fires when the party's box touches the volume, as
    // MM9's TouchNotify does (an exit volume floating over a floor still catches a walking party); none: the point.
    std::optional<Mm9PositionedTransitionActivation> update(
        float partyX,
        float partyY,
        float partyZ,
        EventRuntimeState &eventRuntimeState,
        float bodyRadius = 0.0f,
        float bodyHeight = 0.0f);

private:
    struct Gate
    {
        const Mm9MapTransition *pTransition = nullptr;
        bool inside = false;
    };

    std::vector<Gate> m_gates;
    bool m_initialized = false;
};
}
