#include "doctest/doctest.h"
#include "game/gameplay/MonsterTargetChoice.h"
#include "game/gameplay/WaitingPlayerViews.h"
#include "game/rules/MonsterRules.h"

#include <optional>
#include <vector>

using namespace OpenYAMM::Game;

TEST_CASE("co-op: monsters have the same health whatever the number of players")
{
    CHECK(MonsterRules::playerHealthFactor(0) == doctest::Approx(1.0f));
    CHECK(MonsterRules::playerHealthFactor(1) == doctest::Approx(1.0f));
    // No more health for more players (2026-11-21, as in MAW's own multiplayer).
    CHECK(MonsterRules::playerHealthFactor(2) == doctest::Approx(1.0f));
    CHECK(MonsterRules::playerHealthFactor(4) == doctest::Approx(1.0f));
    CHECK(MonsterRules::healthForPlayers(1, 21) == 21);
    CHECK(MonsterRules::healthForPlayers(2, 20) == 20);
    CHECK(MonsterRules::healthForPlayers(2, 21) == 21);
    CHECK(MonsterRules::healthForPlayers(4, 21) == 21);
}

TEST_CASE("co-op: a monster's health without the players' share is the ruleset's own number")
{
    // What experience and the other rules that weigh a monster's health read, for every count a session allows.
    for (size_t playerCount = 1; playerCount <= 4; ++playerCount)
    {
        for (int maxHp : {1, 2, 3, 7, 20, 21, 199, 1000, 1001, 32767, 250001})
        {
            CAPTURE(playerCount);
            CAPTURE(maxHp);
            CHECK(MonsterRules::healthWithoutPlayers(
                      playerCount, MonsterRules::healthForPlayers(playerCount, maxHp)) == maxHp);
        }
    }
}

TEST_CASE("co-op: each player has their own open chest, and a chest that waits is in use")
{
    WaitingPlayerViews waiting;
    std::optional<GameplayChestViewState> chest = GameplayChestViewState{.chestId = 3};
    std::optional<GameplayCorpseViewState> corpse;

    // Player 1 acts: the local player's chest 3 waits, and player 1 has nothing open.
    waiting.exchange(LocalPlayer, 1, chest, corpse);
    CHECK_FALSE(chest.has_value());
    CHECK(waiting.holdsChest(3));
    CHECK_FALSE(waiting.holdsChest(4));

    // Player 1 opens chest 4 and a corpse, then the local player acts again.
    chest = GameplayChestViewState{.chestId = 4};
    corpse = GameplayCorpseViewState{.fromSummonedMonster = false, .sourceIndex = 9};
    waiting.exchange(1, LocalPlayer, chest, corpse);
    REQUIRE(chest.has_value());
    CHECK(chest->chestId == 3);
    CHECK_FALSE(corpse.has_value());
    CHECK(waiting.holdsChest(4));
    CHECK_FALSE(waiting.holdsChest(3));
    CHECK(waiting.holdsCorpse(GameplayCorpseViewState{.fromSummonedMonster = false, .sourceIndex = 9}));
    CHECK_FALSE(waiting.holdsCorpse(GameplayCorpseViewState{.fromSummonedMonster = true, .sourceIndex = 9}));

    // The same player acting again changes nothing.
    waiting.exchange(LocalPlayer, LocalPlayer, chest, corpse);
    REQUIRE(chest.has_value());
    CHECK(chest->chestId == 3);

    // Player 1 leaves the game: what they had open is free again.
    waiting.keepPlayers(std::vector<GameplayGuestBody>{});
    CHECK_FALSE(waiting.holdsChest(4));

    // A player who stays keeps theirs.
    waiting.exchange(LocalPlayer, 2, chest, corpse);
    chest = GameplayChestViewState{.chestId = 5};
    waiting.exchange(2, LocalPlayer, chest, corpse);
    waiting.keepPlayers(std::vector<GameplayGuestBody>{GameplayGuestBody{.player = 2}});
    CHECK(waiting.holdsChest(5));
    waiting.clear();
    CHECK_FALSE(waiting.holdsChest(5));
}

TEST_CASE("co-op: whom a monster fights among several players' parties")
{
    const PlayerId guest = 1;
    const std::vector<MonsterTargetCandidate> both = {
        MonsterTargetCandidate{LocalPlayer, 1000.0f, 0.0f, 0.0f, true, false},
        MonsterTargetCandidate{guest, 300.0f, 0.0f, 0.0f, true, false},
    };

    // The nearest, whoever it fought before.
    CHECK(chooseMonsterTarget(0.0f, 0.0f, 0.0f, LocalPlayer, std::nullopt, both) == guest);

    // Whoever last hurt it, however far.
    CHECK(chooseMonsterTarget(0.0f, 0.0f, 0.0f, guest, std::optional<PlayerId>(LocalPlayer), both) == LocalPlayer);

    // Two at a like distance do not pass it to and fro: its present target stays until another is a quarter nearer.
    const std::vector<MonsterTargetCandidate> alike = {
        MonsterTargetCandidate{LocalPlayer, 1000.0f, 0.0f, 0.0f, true, false},
        MonsterTargetCandidate{guest, 900.0f, 0.0f, 0.0f, true, false},
    };
    CHECK(chooseMonsterTarget(0.0f, 0.0f, 0.0f, LocalPlayer, std::nullopt, alike) == LocalPlayer);
    CHECK(chooseMonsterTarget(0.0f, 0.0f, 0.0f, guest, std::nullopt, alike) == guest);
    CHECK(chooseMonsterTarget(800.0f, 0.0f, 0.0f, LocalPlayer, std::nullopt, alike) == guest);

    // An invisible party is left alone while a visible one stands, and is found when it is the only one.
    const std::vector<MonsterTargetCandidate> hidden = {
        MonsterTargetCandidate{LocalPlayer, 1000.0f, 0.0f, 0.0f, true, false},
        MonsterTargetCandidate{guest, 100.0f, 0.0f, 0.0f, true, true},
    };
    CHECK(chooseMonsterTarget(0.0f, 0.0f, 0.0f, guest, std::nullopt, hidden) == LocalPlayer);
    CHECK(chooseMonsterTarget(0.0f, 0.0f, 0.0f, guest, std::optional<PlayerId>(guest), hidden) == LocalPlayer);
    const std::vector<MonsterTargetCandidate> allHidden = {
        MonsterTargetCandidate{LocalPlayer, 1000.0f, 0.0f, 0.0f, true, true},
        MonsterTargetCandidate{guest, 100.0f, 0.0f, 0.0f, true, true},
    };
    CHECK(chooseMonsterTarget(0.0f, 0.0f, 0.0f, LocalPlayer, std::nullopt, allHidden) == guest);

    // A party that is down is left alone while another stands; with nobody standing, as in a game of one.
    const std::vector<MonsterTargetCandidate> down = {
        MonsterTargetCandidate{LocalPlayer, 1000.0f, 0.0f, 0.0f, true, false},
        MonsterTargetCandidate{guest, 100.0f, 0.0f, 0.0f, false, false},
    };
    CHECK(chooseMonsterTarget(0.0f, 0.0f, 0.0f, guest, std::optional<PlayerId>(guest), down) == LocalPlayer);
    const std::vector<MonsterTargetCandidate> allDown = {
        MonsterTargetCandidate{LocalPlayer, 1000.0f, 0.0f, 0.0f, false, false},
        MonsterTargetCandidate{guest, 100.0f, 0.0f, 0.0f, false, false},
    };
    CHECK(chooseMonsterTarget(0.0f, 0.0f, 0.0f, guest, std::nullopt, allDown) == LocalPlayer);

    // A player on the floor above is not the nearest for standing over the monster.
    const std::vector<MonsterTargetCandidate> floors = {
        MonsterTargetCandidate{LocalPlayer, 600.0f, 0.0f, 0.0f, true, false},
        MonsterTargetCandidate{guest, 0.0f, 0.0f, 2000.0f, true, false},
    };
    CHECK(chooseMonsterTarget(0.0f, 0.0f, 0.0f, guest, std::nullopt, floors) == LocalPlayer);
}
