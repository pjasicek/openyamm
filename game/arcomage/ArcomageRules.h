#pragma once

#include "game/arcomage/ArcomageTypes.h"

#include <string>

namespace OpenYAMM::Game
{
class ArcomageRules
{
public:
    // Changes the MM8 cards coded by name (Shift, Flood Water) make beyond their effect fields.
    struct SpecialCardEffect
    {
        int playerWall = 0;
        int playerTower = 0;
        int playerDungeon = 0;
        int enemyWall = 0;
        int enemyTower = 0;
        int enemyDungeon = 0;
    };

    bool initializeMatch(
        const ArcomageLibrary &library,
        uint32_t houseId,
        const std::string &playerName,
        const std::string &opponentName,
        uint32_t randomSeed,
        ArcomageState &state
    ) const;

    bool canPlayCard(
        const ArcomageLibrary &library,
        const ArcomageState &state,
        size_t playerIndex,
        size_t handIndex
    ) const;

    bool canDiscardCard(
        const ArcomageLibrary &library,
        const ArcomageState &state,
        size_t playerIndex,
        size_t handIndex
    ) const;

    bool startTurn(const ArcomageLibrary &library, ArcomageState &state) const;
    bool playCard(const ArcomageLibrary &library, size_t handIndex, ArcomageState &state) const;
    bool discardCard(const ArcomageLibrary &library, size_t handIndex, ArcomageState &state) const;
    bool resign(size_t playerIndex, ArcomageState &state) const;

    // True when the card's primary effects apply, false for the secondary ones.
    static bool evaluateCondition(
        ArcomageCondition condition,
        const ArcomagePlayerState &player,
        const ArcomagePlayerState &enemy);
    static SpecialCardEffect specialCardEffect(
        const ArcomageCardDefinition &card,
        const ArcomagePlayerState &player,
        const ArcomagePlayerState &enemy);

private:
    static std::vector<uint32_t> buildMasterDeck();
    static int handCount(const ArcomagePlayerState &player);
    static int firstEmptyHandSlot(const ArcomagePlayerState &player);
    static bool drawCard(const ArcomageLibrary &library, size_t playerIndex, ArcomageState &state);
    static void refillAndShuffleDeck(ArcomageState &state);
    static int applyScalarChange(int &target, int otherValue, int delta);
    // applyScalarChange for a production level (quarry, magic, dungeon), which stays at 1 or more.
    static int applyLevelChange(int &target, int otherValue, int delta);
    static int applyBuildingDamage(ArcomagePlayerState &player, int delta);
    static void applyEffectBundle(const ArcomageEffectBundle &bundle, ArcomagePlayerState &player, ArcomagePlayerState &enemy);
    static void consumeCardCost(const ArcomageCardDefinition &card, ArcomagePlayerState &player);
    static ArcomageResult resolveResult(const ArcomageState &state);
    static int highestResource(const ArcomagePlayerState &player);
};
}
