#include "engine/AssetFileSystem.h"
#include "game/app/GameSession.h"
#include "game/data/GameDataLoader.h"
#include "game/party/SpellIds.h"
#include "tests/PartySpellTestHarness.h"

#include <doctest/doctest.h>

#include <filesystem>

TEST_CASE("quick Heal selects the injured living member with lowest current HP")
{
    using namespace OpenYAMM;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::GameDataLoader loader;
    REQUIRE(loader.loadForHeadlessGameplay(assets));
    Game::GameDataRepository data;
    data.bind(loader);
    Game::Party party;
    party.seed(Tests::createSpellRegressionPartySeed());
    Game::Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);
    pCaster->skills["BodyMagic"] = {"BodyMagic", 5, Game::SkillMastery::Normal};
    pCaster->learnSpell(Game::spellIdValue(Game::SpellId::Heal));
    pCaster->quickSpellName = "Heal";
    pCaster->health = 30;
    party.member(1)->maxHealth = 200;
    party.member(1)->health = 7;
    party.member(2)->health = 4;
    party.member(3)->maxHealth = 1;
    party.member(3)->health = 1;
    Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    Game::GameSession session;
    session.bindDataRepository(&data);
    session.bindActiveWorldRuntime(&world);
    Game::GameplayScreenRuntime &runtime = session.gameplayScreenRuntime();
    Game::GameplaySpellService &spells = session.gameplaySpellService();
    Game::PartySpellCastRequest quickRequest;
    quickRequest.spellId = Game::spellIdValue(Game::SpellId::Heal);
    size_t expectedTarget = 2;

    SUBCASE("absolute HP takes priority over percentage remaining")
    {
        CHECK_LT(party.member(1)->health / float(party.member(1)->maxHealth),
            party.member(2)->health / float(party.member(2)->maxHealth));
    }
    SUBCASE("dead members are skipped")
    {
        party.member(2)->conditions.set(static_cast<size_t>(Game::CharacterCondition::Dead));
        expectedTarget = 1;
    }
    SUBCASE("petrified members are skipped")
    {
        party.member(2)->conditions.set(static_cast<size_t>(Game::CharacterCondition::Petrified));
        expectedTarget = 1;
    }
    SUBCASE("eradicated members are skipped")
    {
        party.member(2)->conditions.set(static_cast<size_t>(Game::CharacterCondition::Eradicated));
        expectedTarget = 1;
    }
    SUBCASE("unconscious members can be healed")
    {
        party.member(2)->health = 0;
        party.member(2)->conditions.set(static_cast<size_t>(Game::CharacterCondition::Unconscious));
    }
    SUBCASE("equal HP chooses the first injured member")
    {
        party.member(1)->health = 4;
        expectedTarget = 1;
    }
    SUBCASE("the caster can be the lowest HP target")
    {
        pCaster->health = 1;
        expectedTarget = 0;
    }
    SUBCASE("a healthy party does not waste mana or recovery")
    {
        for (size_t index = 0; index < party.members().size(); ++index)
        {
            Game::Character &member = *party.member(index);
            member.health = Game::Party::effectiveMaximumHealth(member);
        }
        CHECK_FALSE(spells.tryPrepareQuickCastRequest(runtime, quickRequest, "Heal", {}));
        CHECK_EQ(pCaster->spellPoints, 20);
        CHECK_EQ(pCaster->recoverySecondsRemaining, 0.0f);
        CHECK_FALSE(session.gameplayScreenState().pendingSpellTarget().active);
        return;
    }
    SUBCASE("manual healing retains explicit target selection")
    {
        Game::PartySpellCastRequest request;
        request.spellId = Game::spellIdValue(Game::SpellId::Heal);
        CHECK(spells.castSpell(runtime, request).status == Game::PartySpellCastStatus::NeedCharacterTarget);
        request.targetCharacterIndex = 1;
        CHECK(spells.castSpell(runtime, request).status == Game::PartySpellCastStatus::Succeeded);
        CHECK_EQ(party.member(1)->health, 22);
        CHECK_EQ(party.member(2)->health, 4);
        return;
    }
    SUBCASE("condition cures retain manual target selection")
    {
        quickRequest.spellId = Game::spellIdValue(Game::SpellId::CurePoison);
        REQUIRE(spells.tryPrepareQuickCastRequest(runtime, quickRequest, "Cure Poison", {}));
        CHECK_FALSE(quickRequest.quickCast);
        CHECK_FALSE(quickRequest.targetCharacterIndex.has_value());
        return;
    }
    SUBCASE("turn mode uses the same automatic target")
    {
        Game::TurnBasedCombatRuntime &turns = session.turnBasedCombatRuntime();
        REQUIRE(turns.begin(party, nullptr));
        turns.update(&party, nullptr, 0.6f);
        REQUIRE(turns.canBeginPlayerAction(party));
        REQUIRE_EQ(party.activeMemberIndex(), 0);
    }

    const int previousHealth = party.member(expectedTarget)->health;
    REQUIRE(spells.tryPrepareQuickCastRequest(runtime, quickRequest, "Heal", {}));
    CHECK(quickRequest.quickCast);
    REQUIRE(quickRequest.targetCharacterIndex == expectedTarget);
    CHECK(spells.castSpell(runtime, quickRequest).status == Game::PartySpellCastStatus::Succeeded);
    CHECK_EQ(party.member(expectedTarget)->health, previousHealth + 15);
    CHECK_FALSE(party.member(expectedTarget)->conditions.test(
        static_cast<size_t>(Game::CharacterCondition::Unconscious)));
    CHECK_EQ(pCaster->spellPoints, 18);
    CHECK_FALSE(session.gameplayScreenState().pendingSpellTarget().active);
}

TEST_CASE("out of mana spells yield the character turn without blocking combat")
{
    using namespace OpenYAMM;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::GameDataLoader loader;
    REQUIRE(loader.loadForHeadlessGameplay(assets));
    Game::GameDataRepository data;
    data.bind(loader);
    Game::PartySeed seed;
    seed.members.push_back(Tests::makeSpellRegressionPartyMember("Mage", "Sorcerer", "PC07-01", 7));
    seed.members.push_back(Tests::makeSpellRegressionPartyMember("Knight", "Knight", "PC01-01", 1));
    Game::Party party;
    party.seed(seed);
    Game::Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);
    pCaster->skills["FireMagic"] = {"FireMagic", 5, Game::SkillMastery::Normal};
    pCaster->spellPoints = 0;
    Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    Game::GameSession session;
    session.bindDataRepository(&data);
    session.bindActiveWorldRuntime(&world);
    Game::GameplayScreenRuntime &runtime = session.gameplayScreenRuntime();
    Game::GameplaySpellService &spells = session.gameplaySpellService();
    Game::TurnBasedCombatRuntime &turns = session.turnBasedCombatRuntime();
    Game::PartySpellCastRequest request;
    request.spellId = Game::spellIdValue(Game::SpellId::TorchLight);

    SUBCASE("turn mode advances through the party and remains usable next round")
    {
        REQUIRE(turns.begin(party, nullptr));
        turns.update(&party, nullptr, 0.6f);
        REQUIRE(turns.canBeginPlayerAction(party));
        for (int round = 0; round < 2; ++round)
        {
            for (int action = 0; action < 8 && turns.stage() == Game::TurnBasedCombatStage::Attack; ++action)
            {
                REQUIRE_EQ(party.activeMemberIndex(), 0);
                request.quickCast = round == 0;
                const Game::PartySpellCastResult result = spells.castSpell(runtime, request);
                CHECK(result.status == Game::PartySpellCastStatus::NotEnoughSpellPoints);
                CHECK_EQ(pCaster->spellPoints, 0);
                CHECK_EQ(pCaster->recoverySecondsRemaining, 0.0f);
                CHECK(world.projectileRequests().empty());
                REQUIRE_EQ(party.activeMemberIndex(), 1);
                REQUIRE(turns.canBeginPlayerAction(party));
                REQUIRE(turns.applyPlayerAction(party, 1, 0.0f));
            }
            REQUIRE(turns.stage() == Game::TurnBasedCombatStage::Movement);
            CHECK_EQ(turns.movementActionPoints(), 130);
            REQUIRE(turns.finishMovementPhase());
            turns.update(&party, nullptr, 0.016f);
            turns.update(&party, nullptr, 0.6f);
            REQUIRE(turns.canBeginPlayerAction(party));
        }
    }

    SUBCASE("real time keeps an unsuccessful cast free of recovery")
    {
        const Game::PartySpellCastResult result = spells.castSpell(runtime, request);
        CHECK(result.status == Game::PartySpellCastStatus::NotEnoughSpellPoints);
        CHECK_EQ(party.activeMemberIndex(), 0);
        CHECK_EQ(pCaster->recoverySecondsRemaining, 0.0f);
    }

    SUBCASE("casts explicitly excluding recovery do not consume a turn")
    {
        REQUIRE(turns.begin(party, nullptr));
        turns.update(&party, nullptr, 0.6f);
        request.applyRecovery = false;
        const Game::PartySpellCastResult result = spells.castSpell(runtime, request);
        CHECK(result.status == Game::PartySpellCastStatus::NotEnoughSpellPoints);
        CHECK_EQ(party.activeMemberIndex(), 0);
        CHECK(turns.canBeginPlayerAction(party));
    }

    SUBCASE("choosing a spell target does not consume a turn")
    {
        REQUIRE(turns.begin(party, nullptr));
        turns.update(&party, nullptr, 0.6f);
        pCaster->spellPoints = 20;
        request.spellId = Game::spellIdValue(Game::SpellId::FireBolt);
        const Game::PartySpellCastResult result = spells.castSpell(runtime, request);
        CHECK(result.status == Game::PartySpellCastStatus::NeedActorTarget);
        CHECK_EQ(party.activeMemberIndex(), 0);
        CHECK(turns.canBeginPlayerAction(party));
        CHECK_EQ(pCaster->spellPoints, 20);
    }
}
