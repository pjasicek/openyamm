#pragma once

namespace OpenYAMM::Game
{
class IGameplayWorldRuntime;
class Party;

// Returns whether travel time, food or rest were applied to the party.
bool applyTravelDaysSideEffects(
    Party &party,
    IGameplayWorldRuntime *pWorldRuntime,
    int travelDays,
    int foodRequired);
}
