#include "doctest/doctest.h"

#include "game/mm9/Mm9BarrelRuntime.h"
#include "game/mm9/Mm9PrimaryStats.h"
#include "game/tables/ItemTable.h"

#include <array>

TEST_CASE("MM9 barrel type initialization is stable and covers native range")
{
    std::vector<OpenYAMM::Game::MapDeltaMm9BarrelState> states;
    std::mt19937 firstRng(1234);
    OpenYAMM::Game::MapDeltaMm9BarrelState &first =
        OpenYAMM::Game::ensureMm9BarrelState(states, 42, firstRng);
    const OpenYAMM::Game::Mm9BarrelType type = first.type;
    CHECK(static_cast<uint8_t>(type) >= 1);
    CHECK(static_cast<uint8_t>(type) <= 8);

    std::mt19937 secondRng(9999);
    OpenYAMM::Game::MapDeltaMm9BarrelState &second =
        OpenYAMM::Game::ensureMm9BarrelState(states, 42, secondRng);
    CHECK_EQ(&first, &second);
    CHECK(second.type == type);
}

TEST_CASE("MM9 blue barrel projects Magic to Intellect and is one shot")
{
    OpenYAMM::Game::Party party;
    party.seed(OpenYAMM::Game::Party::createDefaultSeed());
    REQUIRE(party.activeMember() != nullptr);
    party.activeMember()->intellect = 10;
    party.activeMember()->personality = 20;
    OpenYAMM::Game::MapDeltaMm9BarrelState state = {
        7,
        OpenYAMM::Game::Mm9BarrelType::BlueMagic,
        false,
    };
    OpenYAMM::Game::ItemTable itemTable;
    std::mt19937 rng(1);

    const OpenYAMM::Game::Mm9BarrelResult first =
        OpenYAMM::Game::useMm9Barrel(state, party, itemTable, rng);
    CHECK(first.handled);
    CHECK(first.statRaised);
    CHECK(state.used);
    CHECK_EQ(party.activeMember()->intellect, 12u);
    CHECK_EQ(party.activeMember()->personality, 20u);
    CHECK_EQ(first.soundName, "sounds/events/quest.wav");
    CHECK_EQ(OpenYAMM::Game::mm9BarrelLiquidTextureIndex(state), 7u);

    const OpenYAMM::Game::Mm9BarrelResult second =
        OpenYAMM::Game::useMm9Barrel(state, party, itemTable, rng);
    CHECK(second.alreadyUsed);
    CHECK_EQ(party.activeMember()->intellect, 12u);
}

TEST_CASE("MM9 colored barrels raise only the selected member's matching primary stat")
{
    struct StatCase
    {
        OpenYAMM::Game::Mm9BarrelType type;
        OpenYAMM::Game::Mm9PrimaryStat stat;
    };
    const std::array<StatCase, 6> cases = {{
        {OpenYAMM::Game::Mm9BarrelType::RedMight, OpenYAMM::Game::Mm9PrimaryStat::Might},
        {OpenYAMM::Game::Mm9BarrelType::BlueMagic, OpenYAMM::Game::Mm9PrimaryStat::Magic},
        {OpenYAMM::Game::Mm9BarrelType::GreenEndurance, OpenYAMM::Game::Mm9PrimaryStat::Endurance},
        {OpenYAMM::Game::Mm9BarrelType::PurpleSpeed, OpenYAMM::Game::Mm9PrimaryStat::Speed},
        {OpenYAMM::Game::Mm9BarrelType::WhiteLuck, OpenYAMM::Game::Mm9PrimaryStat::Luck},
        {OpenYAMM::Game::Mm9BarrelType::YellowAccuracy, OpenYAMM::Game::Mm9PrimaryStat::Accuracy},
    }};

    for (const StatCase &testCase : cases)
    {
        OpenYAMM::Game::Party party;
        OpenYAMM::Game::PartySeed seed = OpenYAMM::Game::Party::createDefaultSeed();
        seed.members.resize(2, seed.members.front());
        party.seed(seed);
        REQUIRE(party.setActiveMemberIndex(1));
        OpenYAMM::Game::Character *pFirstMember = party.member(0);
        OpenYAMM::Game::Character *pSelectedMember = party.member(1);
        REQUIRE(pFirstMember != nullptr);
        REQUIRE(pSelectedMember != nullptr);
        uint32_t *pFirstStat = OpenYAMM::Game::mm9PrimaryStatStorage(*pFirstMember, testCase.stat);
        uint32_t *pSelectedStat = OpenYAMM::Game::mm9PrimaryStatStorage(*pSelectedMember, testCase.stat);
        REQUIRE(pFirstStat != nullptr);
        REQUIRE(pSelectedStat != nullptr);
        *pFirstStat = 80;
        *pSelectedStat = 100;

        OpenYAMM::Game::MapDeltaMm9BarrelState state = {17, testCase.type, false};
        OpenYAMM::Game::ItemTable itemTable;
        std::mt19937 rng(4);
        const OpenYAMM::Game::Mm9BarrelResult result =
            OpenYAMM::Game::useMm9Barrel(state, party, itemTable, rng);

        CHECK(result.statRaised);
        CHECK_EQ(*pFirstStat, 80u);
        CHECK_EQ(*pSelectedStat, 102u);
    }
}

TEST_CASE("MM9 barrel is consumed when the 500 stat cap rejects its reward")
{
    OpenYAMM::Game::Party party;
    party.seed(OpenYAMM::Game::Party::createDefaultSeed());
    REQUIRE(party.activeMember() != nullptr);
    party.activeMember()->might = 499;
    OpenYAMM::Game::MapDeltaMm9BarrelState state = {
        8,
        OpenYAMM::Game::Mm9BarrelType::RedMight,
        false,
    };
    OpenYAMM::Game::ItemTable itemTable;
    std::mt19937 rng(2);

    const OpenYAMM::Game::Mm9BarrelResult result =
        OpenYAMM::Game::useMm9Barrel(state, party, itemTable, rng);
    CHECK(result.handled);
    CHECK_FALSE(result.statRaised);
    CHECK(state.used);
    CHECK_EQ(party.activeMember()->might, 499u);
}

TEST_CASE("MM9 water barrel drains without reward feedback")
{
    OpenYAMM::Game::Party party;
    party.seed(OpenYAMM::Game::Party::createDefaultSeed());
    OpenYAMM::Game::MapDeltaMm9BarrelState state = {
        9,
        OpenYAMM::Game::Mm9BarrelType::Water,
        false,
    };
    OpenYAMM::Game::ItemTable itemTable;
    std::mt19937 rng(3);

    const OpenYAMM::Game::Mm9BarrelResult result =
        OpenYAMM::Game::useMm9Barrel(state, party, itemTable, rng);
    CHECK(result.handled);
    CHECK(state.used);
    CHECK(result.soundName.empty());
    CHECK(result.statusMessage.empty());
}

TEST_CASE("MM9 barrel rejects a missing selected character without consuming its state")
{
    OpenYAMM::Game::Party party;
    OpenYAMM::Game::MapDeltaMm9BarrelState state = {
        10,
        OpenYAMM::Game::Mm9BarrelType::RedMight,
        false,
    };
    OpenYAMM::Game::ItemTable itemTable;
    std::mt19937 rng(5);

    const OpenYAMM::Game::Mm9BarrelResult result =
        OpenYAMM::Game::useMm9Barrel(state, party, itemTable, rng);
    CHECK(result.handled);
    CHECK(result.invalidCharacter);
    CHECK_FALSE(state.used);
    CHECK_EQ(result.soundName, "sounds/events/error.wav");
}

TEST_CASE("MM9 swamp barrel diseases only the selected member")
{
    OpenYAMM::Game::Party party;
    OpenYAMM::Game::PartySeed seed = OpenYAMM::Game::Party::createDefaultSeed();
    seed.members.resize(3, seed.members.front());
    party.seed(seed);
    REQUIRE(party.setActiveMemberIndex(2));
    REQUIRE(party.member(0) != nullptr);
    REQUIRE(party.member(2) != nullptr);
    OpenYAMM::Game::MapDeltaMm9BarrelState state = {
        11,
        OpenYAMM::Game::Mm9BarrelType::Swamp,
        false,
    };
    OpenYAMM::Game::ItemTable itemTable;
    std::mt19937 rng(6);

    const OpenYAMM::Game::Mm9BarrelResult result =
        OpenYAMM::Game::useMm9Barrel(state, party, itemTable, rng);
    CHECK(result.handled);
    CHECK(result.diseaseApplied);
    CHECK(state.used);
    CHECK_FALSE(party.member(0)->conditions.test(
        static_cast<size_t>(OpenYAMM::Game::CharacterCondition::DiseaseWeak)));
    CHECK(party.member(2)->conditions.test(
        static_cast<size_t>(OpenYAMM::Game::CharacterCondition::DiseaseWeak)));
}

TEST_CASE("MM9 swamp barrel disease is stopped by Protection from Magic")
{
    OpenYAMM::Game::Party party;
    party.seed(OpenYAMM::Game::Party::createDefaultSeed());
    party.applyPartyBuff(OpenYAMM::Game::PartyBuffId::ProtectionFromMagic, 600, 1, 75, 10,
        OpenYAMM::Game::SkillMastery::Master, 0);
    OpenYAMM::Game::MapDeltaMm9BarrelState state = {
        12,
        OpenYAMM::Game::Mm9BarrelType::Swamp,
        false,
    };
    OpenYAMM::Game::ItemTable itemTable;
    std::mt19937 rng(7);

    const OpenYAMM::Game::Mm9BarrelResult result =
        OpenYAMM::Game::useMm9Barrel(state, party, itemTable, rng);
    CHECK(result.handled);
    CHECK_FALSE(result.diseaseApplied);
    CHECK(state.used);
    CHECK_FALSE(party.activeMember()->conditions.test(
        static_cast<size_t>(OpenYAMM::Game::CharacterCondition::DiseaseWeak)));
    CHECK_FALSE(party.hasPartyBuff(OpenYAMM::Game::PartyBuffId::ProtectionFromMagic));
    CHECK(result.statusMessage.find("diseased") == std::string::npos);
}
