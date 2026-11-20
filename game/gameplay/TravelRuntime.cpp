#include "game/gameplay/TravelRuntime.h"

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/party/Party.h"

#include <algorithm>

namespace OpenYAMM::Game
{
bool applyTravelDaysSideEffects(
    Party &party,
    IGameplayWorldRuntime *pWorldRuntime,
    int travelDays,
    int foodRequired)
{
    travelDays = std::max(0, travelDays);
    foodRequired = std::max(0, foodRequired);
    constexpr float MinutesPerDay = 24.0f * 60.0f;
    if (travelDays == 0 && foodRequired == 0)
    {
        return false;
    }

    // The party rests while travelling, so heal first: the days on the road are not days without rest.
    party.restAndHealAll();
    if (travelDays > 0 && pWorldRuntime != nullptr)
    {
        const float travelMinutes = static_cast<float>(travelDays) * MinutesPerDay;
        pWorldRuntime->advanceGameMinutes(travelMinutes);
        party.advanceTimedStates(travelMinutes * 60.0f);
    }
    const int availableFood = party.food();
    if (availableFood > 0)
    {
        party.addFood(-foodRequired);
    }
    if (availableFood >= foodRequired)
    {
        return true;
    }

    const float gameMinutes = pWorldRuntime != nullptr ? pWorldRuntime->gameMinutes() : 0.0f;
    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        const Character *pMember = party.member(memberIndex);
        if (pMember != nullptr && pMember->health > 0)
        {
            party.applyMemberCondition(memberIndex, CharacterCondition::Weak, gameMinutes);
        }
    }
    party.addDayWithoutRest();

    return true;
}
}
