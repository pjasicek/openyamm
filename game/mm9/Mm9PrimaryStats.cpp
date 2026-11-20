#include "game/mm9/Mm9PrimaryStats.h"

#include "engine/Localization.h"
#include "game/party/Party.h"

namespace OpenYAMM::Game
{
uint32_t *mm9PrimaryStatStorage(Character &character, Mm9PrimaryStat stat)
{
    switch (stat)
    {
        case Mm9PrimaryStat::Might: return &character.might;
        case Mm9PrimaryStat::Magic: return &character.intellect;
        case Mm9PrimaryStat::Endurance: return &character.endurance;
        case Mm9PrimaryStat::Accuracy: return &character.accuracy;
        case Mm9PrimaryStat::Speed: return &character.speed;
        case Mm9PrimaryStat::Luck: return &character.luck;
    }
    return nullptr;
}

std::string_view mm9PrimaryStatName(Mm9PrimaryStat stat)
{
    switch (stat)
    {
        case Mm9PrimaryStat::Might: return Engine::trNoop("Might");
        case Mm9PrimaryStat::Magic: return Engine::trNoop("Magic");
        case Mm9PrimaryStat::Endurance: return Engine::trNoop("Endurance");
        case Mm9PrimaryStat::Accuracy: return Engine::trNoop("Accuracy");
        case Mm9PrimaryStat::Speed: return Engine::trNoop("Speed");
        case Mm9PrimaryStat::Luck: return Engine::trNoop("Luck");
    }
    return {};
}

bool addMm9PermanentPrimaryStat(Character &character, Mm9PrimaryStat stat, uint32_t amount, uint32_t maximum)
{
    uint32_t *pValue = mm9PrimaryStatStorage(character, stat);
    if (pValue == nullptr || *pValue > maximum || amount > maximum - *pValue)
    {
        return false;
    }
    *pValue += amount;
    return true;
}
}
