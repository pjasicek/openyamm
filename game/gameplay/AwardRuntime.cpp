#include "game/gameplay/AwardRuntime.h"

#include "game/events/EvtEnums.h"
#include "game/party/Party.h"
#include "game/tables/AwardTable.h"

#include "engine/Localization.h"

#include <algorithm>
#include <cstdint>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
bool isAwardVisible(const AwardDisplayEntry &entry,
                    const Character &character,
                    const Party &party,
                    const AwardAutonoteLookup &isAutonoteUnlocked)
{
    switch (entry.stateKind)
    {
    case AwardStateKind::CharacterAward:
        return character.awards.contains(entry.stateId);

    case AwardStateKind::PartyQBit:
        return party.hasQuestBit(entry.stateId);

    case AwardStateKind::PartyAutonote:
        return isAutonoteUnlocked && isAutonoteUnlocked(entry.stateId);

    case AwardStateKind::PartyArcomageWin:
        return party.hasArcomageWinAt(entry.stateId);
    }

    return false;
}

std::string replaceFirstPrintfUnsigned(std::string text, uint32_t value)
{
    size_t position = text.find("%lu");
    size_t markerLength = 3;

    if (position == std::string::npos)
    {
        position = text.find("%u");
        markerLength = 2;
    }

    if (position != std::string::npos)
    {
        text.replace(position, markerLength, std::to_string(value));
    }

    return text;
}

uint32_t awardCounterValue(uint32_t awardId, const Party &party)
{
    switch (awardId)
    {
    case 36:
        return party.arcomageWinCount();
    case 37:
        return party.arcomageLossCount();
    case 43:
        return static_cast<uint32_t>(
            std::max<int32_t>(0, party.eventVariableValue(static_cast<uint16_t>(EvtVariable::NumDeaths))));
    case 44:
        return static_cast<uint32_t>(
            std::max<int32_t>(0, party.eventVariableValue(static_cast<uint16_t>(EvtVariable::NumBounties))));
    case 45:
        return static_cast<uint32_t>(
            std::max<int32_t>(0, party.eventVariableValue(static_cast<uint16_t>(EvtVariable::PrisonTerms))));
    case 46:
        return static_cast<uint32_t>(
            std::max<int32_t>(0, party.eventVariableValue(static_cast<uint16_t>(EvtVariable::ArenaWinsPage))));
    case 47:
        return static_cast<uint32_t>(
            std::max<int32_t>(0, party.eventVariableValue(static_cast<uint16_t>(EvtVariable::ArenaWinsSquire))));
    case 48:
        return static_cast<uint32_t>(
            std::max<int32_t>(0, party.eventVariableValue(static_cast<uint16_t>(EvtVariable::ArenaWinsKnight))));
    case 49:
        return static_cast<uint32_t>(
            std::max<int32_t>(0, party.eventVariableValue(static_cast<uint16_t>(EvtVariable::ArenaWinsLord))));
    default:
        return 0;
    }
}
} // namespace

std::vector<VisibleAward> buildVisibleAwards(const AwardTable &awardTable,
                                             const Character &character,
                                             const Party &party,
                                             const AwardAutonoteLookup &isAutonoteUnlocked)
{
    std::vector<VisibleAward> awards;

    for (const AwardDisplayEntry &entry : awardTable.entries())
    {
        if (!isAwardVisible(entry, character, party, isAutonoteUnlocked))
        {
            continue;
        }

        VisibleAward award = {};
        award.key = entry.key;
        // A counted award puts its count into the translated text; the screen translates a whole text itself.
        award.text = entry.stateKind == AwardStateKind::CharacterAward && entry.text.find('%') != std::string::npos
                         ? replaceFirstPrintfUnsigned(
                               Engine::localize(entry.text), awardCounterValue(entry.stateId, party))
                         : entry.text;
        award.priority = entry.priority;
        awards.push_back(std::move(award));
    }

    std::stable_sort(awards.begin(), awards.end(), [](const VisibleAward &left, const VisibleAward &right) {
        return left.priority < right.priority;
    });

    return awards;
}

size_t visibleAwardCount(const AwardTable &awardTable,
                         const Character &character,
                         const Party &party,
                         const AwardAutonoteLookup &isAutonoteUnlocked)
{
    return buildVisibleAwards(awardTable, character, party, isAutonoteUnlocked).size();
}
} // namespace OpenYAMM::Game
