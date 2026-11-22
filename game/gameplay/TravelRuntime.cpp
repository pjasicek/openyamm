#include "game/gameplay/TravelRuntime.h"

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/party/Party.h"
#include "game/party/PlaythroughStatistics.h"

#include <algorithm>
#include <cmath>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr float MinutesPerDay = 24.0f * 60.0f;
}

bool TravelCost::any() const
{
    return fareGold > 0 || waitDays > 0 || waitFood > 0 || travelDays > 0 || travelFood > 0 || rideByBoat.has_value();
}

bool applyTravelCost(
    Party &party,
    std::span<Party *const> otherParties,
    IGameplayWorldRuntime *pWorldRuntime,
    const TravelCost &cost)
{
    if (!cost.any())
    {
        return false;
    }

    std::vector<Party *> parties = {&party};
    parties.insert(parties.end(), otherParties.begin(), otherParties.end());
    const int waitDays = std::max(0, cost.waitDays);
    const int travelDays = std::max(0, cost.travelDays);
    const int travelFood = std::max(0, cost.travelFood);

    // The calendar moves once for everyone; the game's own party's timed states move with it here.
    const auto passMinutes = [&party, pWorldRuntime](float minutes)
    {
        if (minutes > 0.0f && pWorldRuntime != nullptr)
        {
            pWorldRuntime->advanceGameMinutes(minutes);
            party.advanceTimedStates(minutes * 60.0f);
        }
    };

    for (Party *pParty : parties)
    {
        if (cost.fareGold > 0)
        {
            pParty->addGold(-std::min(cost.fareGold, pParty->gold()), GoldReason::Travel);
        }

        // The party eats while it waits for the departure.
        if (waitDays > 0)
        {
            pParty->addFood(-std::min(std::max(0, cost.waitFood), pParty->food()));
        }
    }

    passMinutes(float(waitDays) * MinutesPerDay);

    // The party rests while travelling, so heal first: the days on the road are not days without rest.
    for (Party *pParty : parties)
    {
        pParty->restAndHealAll();

        if (PlaythroughStatistics *pStatistics = cost.rideByBoat ? pParty->statistics() : nullptr)
        {
            pStatistics->recordTravel(*cost.rideByBoat, double(waitDays + travelDays));
        }
    }

    if (cost.arrivesAtSix && pWorldRuntime != nullptr)
    {
        constexpr double ArrivalMinuteOfDay = 6.0 * 60.0;
        const double departure = pWorldRuntime->gameMinutes();
        const double arrival =
            (std::floor(departure / double(MinutesPerDay)) + double(travelDays)) * double(MinutesPerDay)
            + ArrivalMinuteOfDay;
        passMinutes(float(std::max(0.0, arrival - departure)));
    }
    else
    {
        passMinutes(float(travelDays) * MinutesPerDay);
    }

    const float gameMinutes = pWorldRuntime != nullptr ? pWorldRuntime->gameMinutes() : 0.0f;

    for (Party *pParty : parties)
    {
        const int availableFood = pParty->food();

        if (availableFood > 0)
        {
            pParty->addFood(-travelFood);
        }

        if (availableFood >= travelFood)
        {
            continue;
        }

        // Short of the road's food: everyone alive arrives weak, and the days were no rest.
        for (size_t memberIndex = 0; memberIndex < pParty->members().size(); ++memberIndex)
        {
            const Character *pMember = pParty->member(memberIndex);

            if (pMember != nullptr && pMember->health > 0)
            {
                pParty->applyMemberCondition(memberIndex, CharacterCondition::Weak, gameMinutes);
            }
        }

        pParty->addDayWithoutRest();
    }

    return true;
}

bool applyTravelDaysSideEffects(
    Party &party,
    IGameplayWorldRuntime *pWorldRuntime,
    int travelDays,
    int foodRequired)
{
    TravelCost cost;
    cost.travelDays = std::max(0, travelDays);
    cost.travelFood = std::max(0, foodRequired);
    return applyTravelCost(party, {}, pWorldRuntime, cost);
}
}
