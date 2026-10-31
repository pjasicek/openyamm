#include "game/gameplay/StoryTextFormatter.h"

#include "engine/TextCatalogue.h"
#include "game/party/Party.h"

#include <algorithm>
#include <array>
#include <cstdio>

namespace OpenYAMM::Game
{
namespace
{
constexpr int DaysPerMonth = 28;
constexpr int MonthsPerYear = 12;
constexpr int StartingYear = 1168;

std::string memberNameOrFallback(const Party &party, size_t memberIndex)
{
    const Character *pMember = party.member(memberIndex);

    if (pMember == nullptr || pMember->name.empty())
    {
        // Names go into text that is already translated.
        return std::string(Engine::localizeDisplayText("Adventurer"));
    }

    return pMember->name;
}

std::string formatHistoryDate(int32_t unlockedGameMinutes)
{
    const int positiveMinutes = std::max(0, unlockedGameMinutes);
    const int totalDays = positiveMinutes / (24 * 60);
    const int monthIndex = totalDays / DaysPerMonth;
    const int day = (totalDays % DaysPerMonth) + 1;
    const int month = (monthIndex % MonthsPerYear) + 1;
    const int year = StartingYear + monthIndex / MonthsPerYear;

    char buffer[32] = {};
    std::snprintf(buffer, sizeof(buffer), "%02d/%02d/%04d", month, day, year);
    return buffer;
}
}

std::string StoryTextFormatter::format(const std::string &text, const Party &party, int32_t unlockedGameMinutes)
{
    const std::string localizedText(Engine::localizeDisplayText(text));
    std::string result;
    result.reserve(localizedText.size() + 32);

    for (size_t index = 0; index < localizedText.size(); ++index)
    {
        if (localizedText[index] != '%' || index + 2 >= localizedText.size())
        {
            result.push_back(localizedText[index]);
            continue;
        }

        const char first = localizedText[index + 1];
        const char second = localizedText[index + 2];

        if (first < '0' || first > '9' || second < '0' || second > '9')
        {
            result.push_back(localizedText[index]);
            continue;
        }

        const int token = (first - '0') * 10 + (second - '0');
        index += 2;

        if (token == 30)
        {
            result += formatHistoryDate(unlockedGameMinutes);
            continue;
        }

        if (token >= 31 && token <= 34)
        {
            result += memberNameOrFallback(party, static_cast<size_t>(token - 31));
            continue;
        }

        result.push_back('%');
        result.push_back(first);
        result.push_back(second);
    }

    return result;
}
}
