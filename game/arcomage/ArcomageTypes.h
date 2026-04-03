#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
enum class ArcomageResourceType : uint8_t
{
    None = 0,
    Bricks = 1,
    Gems = 2,
    Recruits = 3,
};

enum class ArcomageCondition : uint8_t
{
    AlwaysSecondary = 0,
    AlwaysPrimary = 1,
    LesserQuarry = 2,
    LesserMagic = 3,
    LesserDungeon = 4,
    EqualQuarry = 5,
    EqualMagic = 6,
    EqualDungeon = 7,
    GreaterQuarry = 8,
    GreaterMagic = 9,
    GreaterDungeon = 10,
    NoWall = 11,
    HaveWall = 12,
    EnemyHasNoWall = 13,
    EnemyHasWall = 14,
    LesserWall = 15,
    LesserTower = 16,
    EqualWall = 17,
    EqualTower = 18,
    GreaterWall = 19,
    GreaterTower = 20,
    TowerGreaterThanEnemyWall = 21,
};

struct ArcomageEffectBundle
{
    bool playAgain = false;
    int extraDraw = 0;
    int playerQuarry = 0;
    int playerMagic = 0;
    int playerDungeon = 0;
    int playerBricks = 0;
    int playerGems = 0;
    int playerRecruits = 0;
    int playerBuildings = 0;
    int playerWall = 0;
    int playerTower = 0;
    int enemyQuarry = 0;
    int enemyMagic = 0;
    int enemyDungeon = 0;
    int enemyBricks = 0;
    int enemyGems = 0;
    int enemyRecruits = 0;
    int enemyBuildings = 0;
    int enemyWall = 0;
    int enemyTower = 0;
    int bothQuarry = 0;
    int bothMagic = 0;
    int bothDungeon = 0;
    int bothBricks = 0;
    int bothGems = 0;
    int bothRecruits = 0;
    int bothBuildings = 0;
    int bothWall = 0;
    int bothTower = 0;
};

struct ArcomageCardDefinition
{
    uint32_t id = 0;
    std::string name;
    uint32_t slot = 0;
    ArcomageResourceType resourceType = ArcomageResourceType::None;
    int needQuarry = 0;
    int needMagic = 0;
    int needDungeon = 0;
    int needBricks = 0;
    int needGems = 0;
    int needRecruits = 0;
    bool discardable = true;
    ArcomageCondition condition = ArcomageCondition::AlwaysPrimary;
    ArcomageEffectBundle primary = {};
    ArcomageEffectBundle secondary = {};
};

struct ArcomageTavernRule
{
    uint32_t houseId = 0;
    uint32_t victoryTextId = 0;
    uint32_t firstWinAwardId = 0;
    int startTower = 0;
    int startWall = 0;
    int startQuarry = 0;
    int startMagic = 0;
    int startDungeon = 0;
    int startBricks = 0;
    int startGems = 0;
    int startRecruits = 0;
    int winTower = 0;
    int winResources = 0;
    int aiMastery = 0;
};

struct ArcomageLibrary
{
    static constexpr size_t CardCount = 102;

    std::vector<ArcomageCardDefinition> cards;
    std::unordered_map<uint32_t, size_t> cardIndexById;
    std::unordered_map<uint32_t, ArcomageTavernRule> tavernRulesByHouseId;

    const ArcomageCardDefinition *cardById(uint32_t id) const
    {
        const std::unordered_map<uint32_t, size_t>::const_iterator it = cardIndexById.find(id);

        if (it == cardIndexById.end() || it->second >= cards.size())
        {
            return nullptr;
        }

        return &cards[it->second];
    }

    const ArcomageCardDefinition *cardByName(const std::string &name) const
    {
        for (const ArcomageCardDefinition &card : cards)
        {
            if (card.name == name)
            {
                return &card;
            }
        }

        return nullptr;
    }

    const ArcomageTavernRule *ruleForHouse(uint32_t houseId) const
    {
        const std::unordered_map<uint32_t, ArcomageTavernRule>::const_iterator it = tavernRulesByHouseId.find(houseId);
        return it != tavernRulesByHouseId.end() ? &it->second : nullptr;
    }
};

struct ArcomagePlayerState
{
    static constexpr size_t HandSlots = 10;

    std::string name;
    int tower = 0;
    int wall = 0;
    int quarry = 0;
    int magic = 0;
    int dungeon = 0;
    int bricks = 0;
    int gems = 0;
    int recruits = 0;
    std::array<int, HandSlots> hand = {-1, -1, -1, -1, -1, -1, -1, -1, -1, -1};
};

enum class ArcomageVictoryKind : uint8_t
{
    None = 0,
    TowerBuilt,
    TowerDestroyed,
    ResourceVictory,
    Draw,
    TiebreakResource,
    Resigned,
};

struct ArcomageResult
{
    bool finished = false;
    std::optional<size_t> winnerIndex;
    ArcomageVictoryKind victoryKind = ArcomageVictoryKind::None;
};

struct ArcomagePlayedCard
{
    uint32_t cardId = 0;
    size_t playerIndex = 0;
    bool discarded = false;
};

struct ArcomageState
{
    static constexpr size_t PlayerCount = 2;
    static constexpr int MasterDeckSize = static_cast<int>(ArcomageLibrary::CardCount);
    static constexpr int MinimumHandSize = 5;

    uint32_t houseId = 0;
    uint32_t randomSeed = 0;
    int winTower = 0;
    int winResources = 0;
    int aiMastery = 0;
    std::array<ArcomagePlayerState, PlayerCount> players = {};
    std::vector<uint32_t> drawDeck;
    size_t deckIndex = 0;
    size_t currentPlayerIndex = 0;
    bool needsTurnStart = true;
    bool mustDiscard = false;
    bool continueTurnAfterDiscard = false;
    std::optional<ArcomagePlayedCard> lastPlayedCard;
    std::array<std::optional<ArcomagePlayedCard>, 10> shownCards = {};
    std::vector<std::string> messages;
    ArcomageResult result = {};
};
}
