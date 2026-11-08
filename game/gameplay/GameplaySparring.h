#pragma once

#include <cstddef>
#include <cstdint>
#include <string>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
class IGameplayWorldRuntime;

// A match belongs to the live map. Its script resolves an interrupted match on reload.
struct GameplaySparringState
{
    size_t actorIndex = 0;
    uint32_t actorId = 0;
    std::string opponentName;
    int partyGoal = 0;
    int opponentGoal = 0;
    uint16_t winEvent = 0;
    uint16_t lossEvent = 0;
    int partyScore = 0;
    int opponentScore = 0;
    bool active = true;
};

bool isSparringOpponent(const IGameplayWorldRuntime *pWorld, size_t actorIndex);
bool isSparringSource(const IGameplayWorldRuntime *pWorld, uint32_t actorId);
void scoreSparringHit(IGameplayWorldRuntime &world, GameplayScreenRuntime *pRuntime, bool byParty, int damage);
}
