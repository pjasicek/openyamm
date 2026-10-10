#pragma once

#include <charconv>
#include <optional>
#include <string_view>

namespace OpenYAMM::Game
{
constexpr int SkyMinutesPerDay = 24 * 60;

// Parses a game-clock "HH:MM" (00:00-23:59) into minutes after midnight.
inline std::optional<int> parseClockMinutes(std::string_view text)
{
    const size_t colon = text.find(':');

    if (colon == std::string_view::npos || colon == 0 || colon + 3 != text.size())
    {
        return std::nullopt;
    }

    int hours = 0;
    int minutes = 0;
    const std::string_view hoursText = text.substr(0, colon);
    const std::string_view minutesText = text.substr(colon + 1);
    const std::from_chars_result hoursResult =
        std::from_chars(hoursText.data(), hoursText.data() + hoursText.size(), hours);
    const std::from_chars_result minutesResult =
        std::from_chars(minutesText.data(), minutesText.data() + minutesText.size(), minutes);

    if (hoursResult.ec != std::errc() || hoursResult.ptr != hoursText.data() + hoursText.size()
        || minutesResult.ec != std::errc() || minutesResult.ptr != minutesText.data() + minutesText.size()
        || hours < 0 || hours > 23 || minutes < 0 || minutes > 59)
    {
        return std::nullopt;
    }

    return hours * 60 + minutes;
}
}
