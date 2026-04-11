#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct SurfaceAnimationFrame
{
    std::string textureName;
    uint32_t frameLengthTicks = 0;
};

struct SurfaceAnimationSequence
{
    std::vector<SurfaceAnimationFrame> frames;
    uint32_t animationLengthTicks = 0;

    bool empty() const
    {
        return frames.empty();
    }

    size_t frameIndexAtTicks(uint32_t elapsedTicks) const
    {
        if (frames.empty())
        {
            return 0;
        }

        if (frames.size() == 1 || animationLengthTicks == 0)
        {
            return 0;
        }

        uint32_t localTicks = elapsedTicks % animationLengthTicks;

        for (size_t frameIndex = 0; frameIndex < frames.size(); ++frameIndex)
        {
            const uint32_t frameLengthTicks = frames[frameIndex].frameLengthTicks;

            if (frameLengthTicks == 0 || localTicks < frameLengthTicks)
            {
                return frameIndex;
            }

            localTicks -= frameLengthTicks;
        }

        return frames.size() - 1;
    }
};
} // namespace OpenYAMM::Game
