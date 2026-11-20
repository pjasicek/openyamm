#pragma once

#include "engine/Localization.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <string>

namespace OpenYAMM::Game
{
// The HUD's clock ("9:03 am"); the other screens use formatClockTime's capitals.
inline std::string formatGameplayClock(float gameMinutes)
{
    const int totalMinutes = std::max(0, static_cast<int>(std::floor(gameMinutes + 0.5f)));
    const int minuteOfDay = totalMinutes % 1440;
    const int hour24 = minuteOfDay / 60;
    const int minute = minuteOfDay % 60;
    const int hour12 = hour24 == 0 ? 12 : hour24 > 12 ? hour24 - 12 : hour24;
    char minutes[8] = {};
    std::snprintf(minutes, sizeof(minutes), "%02d", minute);
    return hour24 >= 12 ? Engine::tr("{hour}:{minute} pm", {{"hour", hour12}, {"minute", minutes}})
                        : Engine::tr("{hour}:{minute} am", {{"hour", hour12}, {"minute", minutes}});
}
}
