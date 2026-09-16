#pragma once

namespace OpenYAMM::Game
{
void setGameplayProfilingEnabled(bool enabled);

class GprofProfilingScope
{
public:
    GprofProfilingScope();
    ~GprofProfilingScope();

    GprofProfilingScope(const GprofProfilingScope &) = delete;
    GprofProfilingScope &operator=(const GprofProfilingScope &) = delete;
};
}
