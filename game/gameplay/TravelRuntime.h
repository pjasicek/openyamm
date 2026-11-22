#pragma once

#include <optional>
#include <span>

namespace OpenYAMM::Game
{
class IGameplayWorldRuntime;
class Party;

// What a trip to another map costs: a ride's fare and the wait for its day, the days on the road and the food of the
// road. A game of one party pays it as the trip is chosen. In a world shared with other players the move waits for
// their agreement first (EventRuntimeState::PendingMapMove::unpaidCost), and it is paid when they agree: every party
// its own fare and food, the calendar once.
struct TravelCost
{
    int fareGold = 0;
    // The days waited for a ride's departure and the food eaten meanwhile.
    int waitDays = 0;
    int waitFood = 0;
    // The days on the road and the road's food; a party short of that food arrives weak.
    int travelDays = 0;
    int travelFood = 0;
    // MM9's boats arrive at 6:00 in the morning, the travel days after the day they leave.
    bool arrivesAtSix = false;
    // A coach (false) or a boat (true), for the statistics; none for a walk.
    std::optional<bool> rideByBoat;

    // Whether anything is paid, waited or travelled.
    bool any() const;
    bool operator==(const TravelCost &) const = default;
};

// Pays a trip. `party` and every one of `otherParties` pay their fare and food and rest on the way; the calendar
// moves once. `party` is the one whose timed states this moves along with the calendar (the game's own party); the
// others' follow the calendar by themselves (GameSession's other players). Returns whether there was anything to pay.
bool applyTravelCost(
    Party &party,
    std::span<Party *const> otherParties,
    IGameplayWorldRuntime *pWorldRuntime,
    const TravelCost &cost);

// A walk of `travelDays` that eats `foodRequired`. Returns whether travel time, food or rest were applied to the party.
bool applyTravelDaysSideEffects(
    Party &party,
    IGameplayWorldRuntime *pWorldRuntime,
    int travelDays,
    int foodRequired);
}
