#include "game/gameplay/StoryTextFormatter.h"

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
        return "Adventurer";
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
    std::string result;
    result.reserve(text.size() + 32);

    for (size_t index = 0; index < text.size(); ++index)
    {
        if (text[index] != '%' || index + 2 >= text.size())
        {
            result.push_back(text[index]);
            continue;
        }

        const char first = text[index + 1];
        const char second = text[index + 2];

        if (first < '0' || first > '9' || second < '0' || second > '9')
        {
            result.push_back(text[index]);
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
