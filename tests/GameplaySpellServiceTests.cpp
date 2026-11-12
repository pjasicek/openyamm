#include "engine/AssetFileSystem.h"
#include "game/app/GameSession.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayActionController.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/party/SpellIds.h"
#include "game/rules/GameRules.h"
#include "game/rules/SpellRules.h"
#include "game/ui/GameplayOverlayAdapters.h"
#include "tests/PartySpellTestHarness.h"

#include <doctest/doctest.h>

#include <algorithm>
#include <algorithm>
#include <filesystem>

TEST_CASE("quick Heal goes to the member most in danger, else to the one it helps most (GAPS A7.2)")
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
    pCaster->maxHealth = 100;
    pCaster->health = 30;
    party.member(1)->maxHealth = 200;
    party.member(1)->health = 7;
    party.member(2)->maxHealth = 40;
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
    // At or below a third of their maximum: the caster 30 %, member 1 3.5 %, member 2 10 %; member 3 is whole.
    size_t expectedTarget = 1;

    SUBCASE("the lowest share of HP goes first, not the fewest HP")
    {
        CHECK_GT(party.member(1)->health, party.member(2)->health);
    }
    SUBCASE("dead members are skipped")
    {
        party.member(1)->conditions.set(static_cast<size_t>(Game::CharacterCondition::Dead));
        expectedTarget = 2;
    }
    SUBCASE("petrified members are skipped")
    {
        party.member(1)->conditions.set(static_cast<size_t>(Game::CharacterCondition::Petrified));
        expectedTarget = 2;
    }
    SUBCASE("eradicated members are skipped")
    {
        party.member(1)->conditions.set(static_cast<size_t>(Game::CharacterCondition::Eradicated));
        expectedTarget = 2;
    }
    SUBCASE("unconscious members can be healed")
    {
        party.member(2)->health = 0;
        party.member(2)->conditions.set(static_cast<size_t>(Game::CharacterCondition::Unconscious));
        expectedTarget = 2;
    }
    SUBCASE("nobody in danger: the member the heal gives the most HP")
    {
        pCaster->health = 90;
        party.member(1)->health = 150;
        party.member(2)->health = 30;
    }
    SUBCASE("the caster can be the one most in danger")
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

namespace
{
// Rules that refuse every cast, as MAW does an Assassin's spell without combo points.
class RefusingSpellRules : public OpenYAMM::Game::SpellRules
{
public:
    std::optional<std::string> castRefusal(const OpenYAMM::Game::Party &, size_t, uint32_t) const override
    {
        return "Not enough combo points";
    }
};

// The scene's part of a quick cast, which a test session has no scene for: it starts every cast it is given.
class StartingSceneAdapter : public OpenYAMM::Game::IGameplayOverlaySceneAdapter
{
public:
    float gameplayCameraYawRadians() const override
    {
        return 0.0f;
    }

    void executeActiveDialogAction() override
    {
    }

    bool tryCastSpellRequest(const OpenYAMM::Game::PartySpellCastRequest &, const std::string &) override
    {
        ++casts;
        return true;
    }

    bool trySaveToSelectedGameSlot() override
    {
        return false;
    }

    int casts = 0;
};
}

TEST_CASE("quick cast attacks instead when the quick spell lacks mana or a target")
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
    party.member(1)->health = 1;
    Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    Game::GameSession session;
    session.bindDataRepository(&data);
    session.bindActiveWorldRuntime(&world);
    Game::GameplayScreenRuntime &runtime = session.gameplayScreenRuntime();
    StartingSceneAdapter scene;
    runtime.bindSceneAdapter(&scene);
    Game::GameplaySpellService &spells = session.gameplaySpellService();
    REQUIRE_EQ(party.activeMemberIndex(), 0);
    Game::GameplaySpellService::QuickSpellStartDisposition expected =
        Game::GameplaySpellService::QuickSpellStartDisposition::AttackFallback;

    SUBCASE("an injured member is healed")
    {
        expected = Game::GameplaySpellService::QuickSpellStartDisposition::CastStarted;
    }
    SUBCASE("without enough mana")
    {
        pCaster->spellPoints = 0;
    }
    SUBCASE("without a target")
    {
        party.member(1)->health = Game::Party::effectiveMaximumHealth(*party.member(1));
    }
    const RefusingSpellRules refusing;
    const Game::GameRules &standard = Game::standardGameRules();
    const Game::GameRules refusingRules = {standard.experience, standard.combat, standard.monsters, standard.items,
        standard.skills, refusing, standard.classes, standard.potions, standard.crafting};
    SUBCASE("when the rules refuse the spell")
    {
        party.setRules(&refusingRules);
    }

    const int spellPoints = pCaster->spellPoints;
    const Game::GameplaySpellService::QuickSpellStartResolution resolution = spells.tryStartQuickSpellCast(runtime, {});
    CHECK(resolution.disposition == expected);

    if (expected == Game::GameplaySpellService::QuickSpellStartDisposition::AttackFallback)
    {
        CHECK_EQ(pCaster->spellPoints, spellPoints);
        CHECK_EQ(pCaster->recoverySecondsRemaining, 0.0f);
    }
}

TEST_CASE("an extra quick spell slot casts its own spell; an empty slot attacks")
{
    // MMMerge's four extra quick spells (ExtraQuickSpells.lua), cast by Quick Spell 1-4.
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
    // The quick spell is empty, so only the slot can cast Heal.
    pCaster->quickSpellName.clear();
    pCaster->extraQuickSpellNames[2] = "Heal";
    party.member(1)->health = 1;
    Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    Game::GameSession session;
    session.bindDataRepository(&data);
    session.bindActiveWorldRuntime(&world);
    Game::GameplayScreenRuntime &runtime = session.gameplayScreenRuntime();
    Game::GameplaySpellService &spells = session.gameplaySpellService();

    // An empty slot, like an empty quick spell, attacks.
    CHECK(spells.tryStartQuickSpellCast(runtime, {}, 1).disposition
        == Game::GameplaySpellService::QuickSpellStartDisposition::AttackFallback);
    CHECK(spells.tryStartQuickSpellCast(runtime, {}).disposition
        == Game::GameplaySpellService::QuickSpellStartDisposition::AttackFallback);
    // The slot's own spell is the one checked: out of mana it attacks; a name no spell has is refused.
    pCaster->spellPoints = 0;
    CHECK(spells.tryStartQuickSpellCast(runtime, {}, 2).disposition
        == Game::GameplaySpellService::QuickSpellStartDisposition::AttackFallback);
    pCaster->extraQuickSpellNames[3] = "No Such Spell";
    CHECK(spells.tryStartQuickSpellCast(runtime, {}, 3).disposition
        == Game::GameplaySpellService::QuickSpellStartDisposition::Failed);
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

TEST_CASE("a game session leaves no class table behind when it and its data go")
{
    using namespace OpenYAMM;
    Game::Party party;
    party.seed(Tests::createSpellRegressionPartySeed());
    const Game::Character member = *party.member(0);
    const int withoutTable = std::max(1, 40 + std::max(10, int(member.endurance)) * 2 + int(member.level) * 5);
    {
        const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
        Engine::AssetFileSystem assets;
        REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
        Game::GameDataLoader loader;
        REQUIRE(loader.loadForHeadlessGameplay(assets));
        Game::GameDataRepository data;
        data.bind(loader);
        Game::GameSession session;
        session.bindDataRepository(&data);
        REQUIRE_NE(Game::GameMechanics::calculateBaseCharacterMaxHealth(member, nullptr), withoutTable);
    }

    // The session bound its repository's table for the formulas; a later party must not read the freed one.
    CHECK_EQ(Game::GameMechanics::calculateBaseCharacterMaxHealth(member, nullptr), withoutTable);
}

TEST_CASE("a game session leaves no class table behind when it and its data go")
{
    using namespace OpenYAMM;
    Game::Party party;
    party.seed(Tests::createSpellRegressionPartySeed());
    const Game::Character member = *party.member(0);
    const int withoutTable = std::max(1, 40 + std::max(10, int(member.endurance)) * 2 + int(member.level) * 5);
    {
        const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
        Engine::AssetFileSystem assets;
        REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
        Game::GameDataLoader loader;
        REQUIRE(loader.loadForHeadlessGameplay(assets));
        Game::GameDataRepository data;
        data.bind(loader);
        Game::GameSession session;
        session.bindDataRepository(&data);
        REQUIRE_NE(Game::GameMechanics::calculateBaseCharacterMaxHealth(member, nullptr), withoutTable);
    }

    // The session bound its repository's table for the formulas; a later party must not read the freed one.
    CHECK_EQ(Game::GameMechanics::calculateBaseCharacterMaxHealth(member, nullptr), withoutTable);
}

namespace
{
OpenYAMM::Game::GameplayRuntimeActorState spellTargetActor(float x, bool hostile)
{
    OpenYAMM::Game::GameplayRuntimeActorState actor;
    actor.preciseX = x;
    actor.hostileToParty = hostile;
    actor.currentHp = actor.maxHp = 50;
    return actor;
}
}

TEST_CASE("spell actor targets are living hostiles within spell reach, whether or not they noticed the party")
{
    using namespace OpenYAMM;
    Tests::PartySpellTestWorldRuntime world;
    world.setPartyPosition(0.0f, 0.0f, 0.0f);
    // Neither has detected the party: the quick-target lists no longer ask.
    const size_t near = world.addActor(spellTargetActor(3000.0f, true));
    const size_t far = world.addActor(spellTargetActor(6000.0f, true));
    const size_t friendly = world.addActor(spellTargetActor(1000.0f, false));
    const Game::SpellRules &standard = Game::standardSpellRules();
    const uint32_t lifedrain = Game::spellIdValue(Game::SpellId::Lifedrain);

    CHECK(Game::PartySpellSystem::isUsableSpellActorTarget(world, near, true));
    CHECK_FALSE(Game::PartySpellSystem::isUsableSpellActorTarget(world, far, true));
    CHECK_FALSE(Game::PartySpellSystem::isUsableSpellActorTarget(world, friendly, true));
    CHECK(Game::PartySpellSystem::isUsableSpellActorTarget(world, friendly, false));
    CHECK_EQ(Game::PartySpellSystem::quickCastActorTarget(world, standard, lifedrain), std::optional<size_t>(near));

    // A corpse is no living target, but a click may still reach it (Reanimate).
    world.actor(near).isDead = true;
    CHECK_FALSE(Game::PartySpellSystem::isUsableSpellActorTarget(world, near, false));
    CHECK(Game::PartySpellSystem::isActorWithinSpellTargetRange(world, near));
    CHECK_FALSE(Game::PartySpellSystem::isActorWithinSpellTargetRange(world, far));
    // With only the far hostile left, the quick cast has no target, under MAW's spread rule as well.
    CHECK_FALSE(Game::PartySpellSystem::quickCastActorTarget(world, standard, lifedrain).has_value());
    CHECK_FALSE(Game::PartySpellSystem::quickCastActorTarget(
        world, standard, Game::spellIdValue(Game::SpellId::Slow)).has_value());
}

TEST_CASE("a quick Lifedrain takes a hostile within reach; beyond reach it attacks instead")
{
    using namespace OpenYAMM;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::GameDataLoader loader;
    REQUIRE(loader.loadForHeadlessGameplay(assets));
    Game::GameDataRepository data;
    data.bind(loader);
    const Game::SpellEntry *pLifedrain =
        loader.getSpellTable().findById(int(Game::spellIdValue(Game::SpellId::Lifedrain)));
    REQUIRE(pLifedrain != nullptr);
    Game::Party party;
    party.seed(Tests::createSpellRegressionPartySeed());
    Game::Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);
    // The vampires' racial spell.
    pCaster->skills["VampireAbility"] = {"VampireAbility", 5, Game::SkillMastery::Normal};
    pCaster->learnSpell(Game::spellIdValue(Game::SpellId::Lifedrain));
    pCaster->quickSpellName = pLifedrain->name;
    pCaster->spellPoints = 100;
    Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    world.setPartyPosition(0.0f, 0.0f, 0.0f);
    Game::GameSession session;
    session.bindDataRepository(&data);
    session.bindActiveWorldRuntime(&world);
    Game::GameplayScreenRuntime &runtime = session.gameplayScreenRuntime();
    StartingSceneAdapter scene;
    runtime.bindSceneAdapter(&scene);
    Game::GameplaySpellService &spells = session.gameplaySpellService();
    Game::PartySpellCastRequest request;
    request.spellId = Game::spellIdValue(Game::SpellId::Lifedrain);

    SUBCASE("the hovered far hostile and a hovered friend give way to the near hostile")
    {
        const size_t far = world.addActor(spellTargetActor(7000.0f, true));
        const size_t near = world.addActor(spellTargetActor(4000.0f, true));
        const size_t friendly = world.addActor(spellTargetActor(500.0f, false));
        world.setHoveredActorIndex(far);
        REQUIRE(spells.tryPrepareQuickCastRequest(runtime, request, pLifedrain->name, {}));
        CHECK_EQ(request.targetActorIndex, std::optional<size_t>(near));
        world.setHoveredActorIndex(friendly);
        REQUIRE(spells.tryPrepareQuickCastRequest(runtime, request, pLifedrain->name, {}));
        CHECK_EQ(request.targetActorIndex, std::optional<size_t>(near));
        CHECK(spells.tryStartQuickSpellCast(runtime, {}).disposition
            == Game::GameplaySpellService::QuickSpellStartDisposition::CastStarted);
        CHECK_EQ(scene.casts, 1);
    }
    SUBCASE("a hostile only beyond reach: the quick cast attacks")
    {
        world.setHoveredActorIndex(world.addActor(spellTargetActor(7000.0f, true)));
        CHECK_FALSE(spells.tryPrepareQuickCastRequest(runtime, request, pLifedrain->name, {}));
        CHECK(spells.tryStartQuickSpellCast(runtime, {}).disposition
            == Game::GameplaySpellService::QuickSpellStartDisposition::AttackFallback);
        CHECK_EQ(scene.casts, 0);
        CHECK_EQ(pCaster->spellPoints, 100);
    }
}

TEST_CASE("an attack spell without a target swings the weapon instead")
{
    using namespace OpenYAMM;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::GameDataLoader loader;
    REQUIRE(loader.loadForHeadlessGameplay(assets));
    Game::GameDataRepository data;
    data.bind(loader);
    const Game::SpellEntry *pLifedrain =
        loader.getSpellTable().findById(int(Game::spellIdValue(Game::SpellId::Lifedrain)));
    REQUIRE(pLifedrain != nullptr);
    Game::Party party;
    party.seed(Tests::createSpellRegressionPartySeed());
    Game::Character *pAttacker = party.member(0);
    REQUIRE(pAttacker != nullptr);
    pAttacker->skills["VampireAbility"] = {"VampireAbility", 5, Game::SkillMastery::Normal};
    pAttacker->learnSpell(Game::spellIdValue(Game::SpellId::Lifedrain));
    Game::BattleOrder lifedrain;
    lifedrain.spellName = pLifedrain->name;
    pAttacker->battleOrders = {lifedrain};
    pAttacker->spellPoints = 100;
    Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    world.setPartyPosition(0.0f, 0.0f, 0.0f);
    Game::GameSession session;
    session.bindDataRepository(&data);
    session.bindActiveWorldRuntime(&world);
    Game::GameplayScreenRuntime &runtime = session.gameplayScreenRuntime();
    // The weapon path reads the attack tuning from the settings.
    Game::GameSettings settings = Game::GameSettings::createDefault();
    runtime.bindSettings(&settings);
    StartingSceneAdapter scene;
    runtime.bindSceneAdapter(&scene);
    REQUIRE_EQ(party.activeMemberIndex(), 0);
    Game::GameplayActionController::PartyAttackConfig config = {
        .pRuntime = &runtime,
        .pSpellService = &session.gameplaySpellService(),
        .pWorldRuntime = &world,
        .pParty = &party,
        .pItemTable = &loader.getItemTable(),
        .pSpellTable = &loader.getSpellTable(),
        .pMonsterTable = &loader.getMonsterTable(),
        .pSpecialItemEnchantTable = &loader.getSpecialItemEnchantTable(),
    };

    SUBCASE("nothing to aim at: the weapon swings and no mana is spent")
    {
        const Game::GameplayActionController::PartyAttackExecutionResult result =
            Game::GameplayActionController::executePartyAttack(config);
        CHECK(result.attempted);
        CHECK(result.actionPerformed);
        CHECK_EQ(scene.casts, 0);
        CHECK_EQ(pAttacker->spellPoints, 100);
    }
    SUBCASE("the attack's own target, unnoticed by it, takes the spell")
    {
        config.directTargetActorIndex = world.addActor(spellTargetActor(300.0f, true));
        const Game::GameplayActionController::PartyAttackExecutionResult result =
            Game::GameplayActionController::executePartyAttack(config);
        CHECK(result.attempted);
        CHECK_FALSE(result.actionPerformed);
        CHECK_EQ(scene.casts, 1);
    }
}

TEST_CASE("battle orders: a spell with no target passes to the next order, and a holder hands the press on")
{
    using namespace OpenYAMM;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::GameDataLoader loader;
    REQUIRE(loader.loadForHeadlessGameplay(assets));
    Game::GameDataRepository data;
    data.bind(loader);
    const Game::SpellEntry *pLifedrain =
        loader.getSpellTable().findById(int(Game::spellIdValue(Game::SpellId::Lifedrain)));
    const Game::SpellEntry *pHeal = loader.getSpellTable().findById(int(Game::spellIdValue(Game::SpellId::Heal)));
    REQUIRE(pLifedrain != nullptr);
    REQUIRE(pHeal != nullptr);
    Game::Party party;
    party.seed(Tests::createSpellRegressionPartySeed());

    // Nobody is hurt: a Heal finds no target.
    for (size_t index = 0; index < party.members().size(); ++index)
    {
        party.member(index)->health = party.reachableMaximumHealth(index);
    }

    Game::Character *pHealer = party.member(0);
    REQUIRE(pHealer != nullptr);
    pHealer->skills["VampireAbility"] = {"VampireAbility", 5, Game::SkillMastery::Normal};
    pHealer->skills["BodyMagic"] = {"BodyMagic", 5, Game::SkillMastery::Normal};
    pHealer->learnSpell(Game::spellIdValue(Game::SpellId::Lifedrain));
    pHealer->learnSpell(Game::spellIdValue(Game::SpellId::Heal));
    pHealer->spellPoints = 100;
    Game::BattleOrder heal;
    heal.spellName = pHeal->name;
    Game::BattleOrder lifedrain;
    lifedrain.spellName = pLifedrain->name;
    Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    world.setPartyPosition(0.0f, 0.0f, 0.0f);
    Game::GameSession session;
    session.bindDataRepository(&data);
    session.bindActiveWorldRuntime(&world);
    Game::GameplayScreenRuntime &runtime = session.gameplayScreenRuntime();
    Game::GameSettings settings = Game::GameSettings::createDefault();
    runtime.bindSettings(&settings);
    StartingSceneAdapter scene;
    runtime.bindSceneAdapter(&scene);
    REQUIRE_EQ(party.activeMemberIndex(), 0);
    Game::GameplayActionController::PartyAttackConfig config = {
        .pRuntime = &runtime,
        .pSpellService = &session.gameplaySpellService(),
        .pWorldRuntime = &world,
        .pParty = &party,
        .pItemTable = &loader.getItemTable(),
        .pSpellTable = &loader.getSpellTable(),
        .pMonsterTable = &loader.getMonsterTable(),
        .pSpecialItemEnchantTable = &loader.getSpecialItemEnchantTable(),
    };

    SUBCASE("a Heal with nobody hurt passes to Lifedrain at the target")
    {
        pHealer->battleOrders = {heal, lifedrain};
        config.directTargetActorIndex = world.addActor(spellTargetActor(300.0f, true));
        const Game::GameplayActionController::PartyAttackExecutionResult result =
            Game::GameplayActionController::executePartyAttack(config);
        CHECK(result.attempted);
        CHECK_FALSE(result.held);
        CHECK_EQ(result.actingMemberIndex, 0);
        CHECK_EQ(scene.casts, 1);
    }
    SUBCASE("an order that is off is skipped")
    {
        lifedrain.enabled = false;
        pHealer->battleOrders = {lifedrain};
        config.directTargetActorIndex = world.addActor(spellTargetActor(300.0f, true));
        const Game::GameplayActionController::PartyAttackExecutionResult result =
            Game::GameplayActionController::executePartyAttack(config);
        CHECK(result.actionPerformed);
        CHECK_EQ(scene.casts, 0);
    }
    SUBCASE("nothing to do and otherwise hold: the next ready member takes the press")
    {
        pHealer->battleOrders = {heal};
        pHealer->battleOrderFallback = Game::BattleOrderFallback::Hold;
        const Game::GameplayActionController::PartyAttackExecutionResult result =
            Game::GameplayActionController::executePartyAttack(config);
        CHECK_FALSE(result.held);
        CHECK(result.actionPerformed);
        CHECK_EQ(result.actingMemberIndex, 1);
        CHECK_EQ(scene.casts, 0);
        // The holder spent nothing and is still ready.
        CHECK_EQ(pHealer->recoverySecondsRemaining, doctest::Approx(0.0f));
    }
    SUBCASE("a member without orders blows again as soon as the recovery is over")
    {
        pHealer->battleOrders.clear();
        const Game::GameplayActionController::PartyAttackExecutionResult first =
            Game::GameplayActionController::executePartyAttack(config);
        REQUIRE(first.actionPerformed);
        CHECK_EQ(first.actingMemberIndex, 0);
        CHECK_GT(pHealer->recoverySecondsRemaining, 0.0f);
        pHealer->recoverySecondsRemaining = 0.0f;
        REQUIRE(party.setActiveMemberIndex(0));
        const Game::GameplayActionController::PartyAttackExecutionResult second =
            Game::GameplayActionController::executePartyAttack(config);
        CHECK(second.actionPerformed);
        CHECK_EQ(second.actingMemberIndex, 0);
    }
    SUBCASE("everyone ready holds: nothing happens and the first holder stays selected")
    {
        for (size_t index = 0; index < party.members().size(); ++index)
        {
            party.member(index)->battleOrders.clear();
            party.member(index)->battleOrderFallback = Game::BattleOrderFallback::Hold;
        }

        const Game::GameplayActionController::PartyAttackExecutionResult result =
            Game::GameplayActionController::executePartyAttack(config);
        CHECK(result.held);
        CHECK_FALSE(result.attempted);
        CHECK_FALSE(result.actionPerformed);
        CHECK_EQ(party.activeMemberIndex(), 0);
        CHECK_EQ(scene.casts, 0);
    }
}

namespace
{
// A scene that carries the party's casts out, so their buffs and heals land, and keeps the requests.
class CastingSceneAdapter : public StartingSceneAdapter
{
public:
    CastingSceneAdapter(OpenYAMM::Game::Party &party, OpenYAMM::Game::IGameplayWorldRuntime &world,
        const OpenYAMM::Game::SpellTable &spellTable)
        : m_party(party)
        , m_world(world)
        , m_spellTable(spellTable)
    {
    }

    bool tryCastSpellRequest(const OpenYAMM::Game::PartySpellCastRequest &request, const std::string &) override
    {
        ++casts;
        requests.push_back(request);
        return OpenYAMM::Game::PartySpellSystem::castSpell(m_party, m_world, m_spellTable, request).succeeded();
    }

    std::vector<OpenYAMM::Game::PartySpellCastRequest> requests;

private:
    OpenYAMM::Game::Party &m_party;
    OpenYAMM::Game::IGameplayWorldRuntime &m_world;
    const OpenYAMM::Game::SpellTable &m_spellTable;
};
}

TEST_CASE("upkeep: a press casts the first due spell of a ready member's list")
{
    using namespace OpenYAMM;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::GameDataLoader loader;
    REQUIRE(loader.loadForHeadlessGameplay(assets));
    Game::GameDataRepository data;
    data.bind(loader);
    const Game::SpellTable &spellTable = loader.getSpellTable();
    const auto order = [&spellTable](Game::SpellId spell)
    {
        const Game::SpellEntry *pSpell = spellTable.findById(int(Game::spellIdValue(spell)));
        REQUIRE(pSpell != nullptr);
        Game::BattleOrder upkeep;
        upkeep.spellName = pSpell->name;
        return upkeep;
    };
    Game::Party party;
    party.seed(Tests::createSpellRegressionPartySeed());

    for (size_t index = 0; index < party.members().size(); ++index)
    {
        party.member(index)->health = party.reachableMaximumHealth(index);
        party.member(index)->recoverySecondsRemaining = 0.0f;
    }

    Game::Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);
    pCaster->skills["FireMagic"] = {"FireMagic", 5, Game::SkillMastery::Normal};
    pCaster->skills["BodyMagic"] = {"BodyMagic", 10, Game::SkillMastery::Master};

    for (const Game::SpellId spell : {Game::SpellId::TorchLight, Game::SpellId::Heal, Game::SpellId::Regeneration})
    {
        pCaster->learnSpell(Game::spellIdValue(spell));
    }

    pCaster->spellPoints = 200;
    Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    world.setPartyPosition(0.0f, 0.0f, 0.0f);
    Game::GameSession session;
    session.bindDataRepository(&data);
    session.bindActiveWorldRuntime(&world);
    Game::GameplayScreenRuntime &runtime = session.gameplayScreenRuntime();
    Game::GameSettings settings = Game::GameSettings::createDefault();
    runtime.bindSettings(&settings);
    CastingSceneAdapter scene(party, world, spellTable);
    runtime.bindSceneAdapter(&scene);
    REQUIRE_EQ(party.activeMemberIndex(), 0);
    const Game::GameplayActionController::PartyUpkeepConfig config = {
        .pRuntime = &runtime,
        .pSpellService = &session.gameplaySpellService(),
        .pWorldRuntime = &world,
        .pParty = &party,
        .pSpellTable = &spellTable,
        .pressedThisFrame = true,
    };
    const auto press = [&config]()
    {
        return Game::GameplayActionController::executePartyUpkeep(config);
    };

    SUBCASE("a missing party buff is cast once, and not again while it lasts")
    {
        pCaster->upkeepOrders = {order(Game::SpellId::TorchLight)};
        const Game::GameplayActionController::PartyUpkeepResult first = press();
        CHECK(first.castStarted);
        CHECK_EQ(first.actingMemberIndex, 0);
        CHECK(party.hasPartyBuff(Game::PartyBuffId::TorchLight));
        CHECK_LT(pCaster->spellPoints, 200);
        pCaster->recoverySecondsRemaining = 0.0f;
        const int spellPoints = pCaster->spellPoints;
        CHECK_FALSE(press().attempted);
        CHECK_EQ(scene.casts, 1);
        CHECK_EQ(pCaster->spellPoints, spellPoints);
    }
    SUBCASE("a buff under its renew time is cast again; one with more left is not")
    {
        Game::BattleOrder torch = order(Game::SpellId::TorchLight);
        torch.renewBelowMinutes = 30;
        pCaster->upkeepOrders = {torch};
        party.applyPartyBuff(Game::PartyBuffId::TorchLight, 31 * 60.0f, 3, 0, 5, Game::SkillMastery::Normal, 0);
        CHECK_FALSE(press().attempted);
        party.clearPartyBuff(Game::PartyBuffId::TorchLight);
        party.applyPartyBuff(Game::PartyBuffId::TorchLight, 29 * 60.0f, 3, 0, 5, Game::SkillMastery::Normal, 0);
        CHECK(press().castStarted);
        REQUIRE(party.partyBuff(Game::PartyBuffId::TorchLight) != nullptr);
        CHECK_GT(party.partyBuff(Game::PartyBuffId::TorchLight)->remainingSeconds, 3600.0f);
    }
    SUBCASE("a spell that is off, or for another place, is passed over")
    {
        Game::BattleOrder off = order(Game::SpellId::TorchLight);
        off.enabled = false;
        pCaster->upkeepOrders = {off};
        CHECK_FALSE(press().attempted);
        // The test world is outdoors.
        Game::BattleOrder indoors = order(Game::SpellId::TorchLight);
        indoors.place = Game::BattleOrderPlace::Indoors;
        pCaster->upkeepOrders = {indoors};
        CHECK_FALSE(press().attempted);
        world.setIndoorMap(true);
        CHECK(press().castStarted);
    }
    SUBCASE("a buff on one member goes to a living member without it, each in turn")
    {
        pCaster->upkeepOrders = {order(Game::SpellId::Regeneration)};
        party.member(1)->conditions.set(size_t(Game::CharacterCondition::Dead));
        std::vector<size_t> targets;

        for (size_t cast = 0; cast < party.members().size(); ++cast)
        {
            pCaster->recoverySecondsRemaining = 0.0f;
            REQUIRE(party.setActiveMemberIndex(0));

            if (press().castStarted)
            {
                REQUIRE(scene.requests.back().targetCharacterIndex.has_value());
                targets.push_back(*scene.requests.back().targetCharacterIndex);
            }
        }

        // Everyone but the dead member, once each.
        CHECK_EQ(targets.size(), party.members().size() - 1);
        CHECK(std::find(targets.begin(), targets.end(), size_t(1)) == targets.end());

        for (size_t index = 0; index < party.members().size(); ++index)
        {
            CHECK_EQ(party.hasCharacterBuff(index, Game::CharacterBuffId::Regeneration), index != 1);
        }
    }
    SUBCASE("a heal waits for a wound, then goes to the wounded member")
    {
        pCaster->upkeepOrders = {order(Game::SpellId::Heal), order(Game::SpellId::TorchLight)};
        // Nobody is hurt: the list goes on to the torch.
        REQUIRE(press().castStarted);
        CHECK(party.hasPartyBuff(Game::PartyBuffId::TorchLight));
        party.member(2)->health = 1;
        pCaster->recoverySecondsRemaining = 0.0f;
        REQUIRE(party.setActiveMemberIndex(0));
        REQUIRE(press().castStarted);
        CHECK_EQ(scene.requests.back().targetCharacterIndex, std::optional<size_t>(2));
        CHECK_GT(party.member(2)->health, 1);
    }
    SUBCASE("a member in recovery leaves the press to the next ready member")
    {
        Game::Character *pSecond = party.member(1);
        pSecond->skills["FireMagic"] = {"FireMagic", 5, Game::SkillMastery::Normal};
        pSecond->learnSpell(Game::spellIdValue(Game::SpellId::TorchLight));
        pSecond->spellPoints = 50;
        pSecond->upkeepOrders = {order(Game::SpellId::TorchLight)};
        pCaster->upkeepOrders = {order(Game::SpellId::TorchLight)};
        pCaster->recoverySecondsRemaining = 5.0f;
        const Game::GameplayActionController::PartyUpkeepResult result = press();
        CHECK(result.castStarted);
        CHECK_EQ(result.actingMemberIndex, 1);
        REQUIRE_EQ(scene.requests.size(), 1);
        CHECK_EQ(scene.requests.back().casterMemberIndex, 1);
    }
    SUBCASE("members without a list, or with nothing due, are passed over while the key is held")
    {
        // Only the third member keeps anything up; the selected first member and the second have no list.
        Game::Character *pThird = party.member(2);
        pThird->skills["FireMagic"] = {"FireMagic", 5, Game::SkillMastery::Normal};
        pThird->learnSpell(Game::spellIdValue(Game::SpellId::TorchLight));
        pThird->spellPoints = 50;
        pThird->upkeepOrders = {order(Game::SpellId::TorchLight)};
        REQUIRE_EQ(party.activeMemberIndex(), 0);
        const Game::GameplayActionController::PartyUpkeepResult first = press();
        CHECK(first.castStarted);
        CHECK_EQ(first.actingMemberIndex, 2);
        // The repeats of a held key find nothing more, and leave the selection alone.
        pThird->recoverySecondsRemaining = 0.0f;
        const size_t selected = party.activeMemberIndex();
        CHECK_FALSE(press().attempted);
        CHECK_FALSE(press().attempted);
        CHECK_EQ(party.activeMemberIndex(), selected);
        CHECK_EQ(scene.casts, 1);
    }
    SUBCASE("a due spell the caster cannot pay for is not cast")
    {
        pCaster->upkeepOrders = {order(Game::SpellId::TorchLight)};
        pCaster->spellPoints = 0;
        CHECK_FALSE(press().attempted);
        CHECK_EQ(scene.casts, 0);
        CHECK_FALSE(party.hasPartyBuff(Game::PartyBuffId::TorchLight));
    }
}

namespace
{
// A world with a fallback hostile and a destructible face 7 the crosshair can be on; it records the party's shots.
class DestructibleAimWorld : public OpenYAMM::Tests::PartySpellTestWorldRuntime
{
public:
    std::vector<OpenYAMM::Game::GameplayPartyAttackActorFacts> fallbackActors;
    bool faceStanding = true;
    std::vector<OpenYAMM::Game::GameplayPartyAttackProjectileRequest> shots;

    std::vector<OpenYAMM::Game::GameplayPartyAttackActorFacts> collectPartyAttackFallbackActors(
        const OpenYAMM::Game::GameplayPartyAttackFallbackQuery &query) const override
    {
        (void)query;
        return fallbackActors;
    }

    bool isPartyAttackMeleeBModelTarget(size_t faceIndex) const override
    {
        return faceStanding && faceIndex == 7;
    }

    bool spawnPartyAttackProjectile(const OpenYAMM::Game::GameplayPartyAttackProjectileRequest &request) override
    {
        shots.push_back(request);
        return true;
    }
};

OpenYAMM::Game::GameplayPartyAttackActorFacts fallbackHostile(size_t actorIndex, float x)
{
    OpenYAMM::Game::GameplayPartyAttackActorFacts actor;
    actor.actorIndex = actorIndex;
    actor.position = {x, 0.0f, 0.0f};
    actor.radius = 40;
    actor.height = 120;
    actor.currentHp = 50;
    actor.maxHp = 50;
    actor.hostileToParty = true;
    actor.visibleForFallback = true;
    return actor;
}
}

TEST_CASE("a crosshair destructible wins over a fallback hostile out of blow reach")
{
    using GameplayActionController = OpenYAMM::Game::GameplayActionController;
    CHECK(GameplayActionController::crosshairDestructibleOverridesFallback(true, 3000.0f));
    CHECK_FALSE(GameplayActionController::crosshairDestructibleOverridesFallback(true, 200.0f));
    CHECK_FALSE(GameplayActionController::crosshairDestructibleOverridesFallback(false, 3000.0f));
}

TEST_CASE("a bow shot with no actor under the crosshair flies at a standing destructible there")
{
    using namespace OpenYAMM;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", Engine::AssetScaleTier::X1));
    Game::GameDataLoader loader;
    REQUIRE(loader.loadForHeadlessGameplay(assets));
    Game::Party party;
    party.seed(Tests::createSpellRegressionPartySeed());
    Game::Character *pArcher = party.member(0);
    REQUIRE(pArcher != nullptr);
    pArcher->equipment.bow = 61;
    pArcher->skills["Bow"] = {"Bow", 5, Game::SkillMastery::Normal};
    DestructibleAimWorld world;
    world.bindParty(&party);
    world.setPartyPosition(0.0f, 0.0f, 0.0f);
    REQUIRE_EQ(party.activeMemberIndex(), 0);
    Game::GameplayActionController::PartyAttackConfig config = {
        .pWorldRuntime = &world,
        .pParty = &party,
        .pItemTable = &loader.getItemTable(),
        .pSpellTable = &loader.getSpellTable(),
        .pMonsterTable = &loader.getMonsterTable(),
        .pSpecialItemEnchantTable = &loader.getSpecialItemEnchantTable(),
        .directTargetBModelIndex = 7,
        .directWorldTargetDistance = 1800.0f,
        .rayRangedTarget = {1500.0f, 900.0f, 400.0f},
        .hasRayRangedTarget = true,
        .randomSeed = 5,
    };

    SUBCASE("the chain under the crosshair takes the arrow, not the hostile across the yard")
    {
        world.fallbackActors = {fallbackHostile(3, 2500.0f)};
        const Game::GameplayActionController::PartyAttackExecutionResult result =
            Game::GameplayActionController::executePartyAttack(config);
        CHECK(result.attempted);
        CHECK_FALSE(result.targetActorIndex.has_value());
        REQUIRE_FALSE(world.shots.empty());
        CHECK_FALSE(world.shots.front().targetActorIndex.has_value());
        CHECK_EQ(world.shots.front().target.x, doctest::Approx(1500.0f));
        CHECK_EQ(world.shots.front().target.y, doctest::Approx(900.0f));
    }
    SUBCASE("a broken chain gives the shot back to the nearest hostile")
    {
        world.faceStanding = false;
        world.fallbackActors = {fallbackHostile(3, 2500.0f)};
        const Game::GameplayActionController::PartyAttackExecutionResult result =
            Game::GameplayActionController::executePartyAttack(config);
        CHECK_EQ(result.targetActorIndex, std::optional<size_t>(3));
        REQUIRE_FALSE(world.shots.empty());
        CHECK_EQ(world.shots.front().targetActorIndex, std::optional<size_t>(3));
        CHECK_EQ(world.shots.front().target.x, doctest::Approx(2500.0f));
    }
    SUBCASE("a hostile within blow reach is still struck")
    {
        world.fallbackActors = {fallbackHostile(4, 200.0f)};
        const Game::GameplayActionController::PartyAttackExecutionResult result =
            Game::GameplayActionController::executePartyAttack(config);
        CHECK_EQ(result.targetActorIndex, std::optional<size_t>(4));
        CHECK(world.shots.empty());
    }
    SUBCASE("a Carnage bow shoots an exploding fire arrow that carries its damage range")
    {
        Game::ItemEnchantRuntime::applySpecialEnchantBonus(*pArcher, Game::SpecialItemEnchantKind::Carnage);
        world.faceStanding = false;
        world.fallbackActors = {fallbackHostile(3, 2500.0f)};
        const Game::GameplayActionController::PartyAttackExecutionResult result =
            Game::GameplayActionController::executePartyAttack(config);
        CHECK(result.attack.explosiveArrow);
        REQUIRE_FALSE(world.shots.empty());
        const Game::GameplayPartyAttackProjectileRequest &shot = world.shots.front();
        CHECK_EQ(shot.damageType, Game::CombatDamageType::Fire);
        CHECK_FALSE(shot.useActorHitChance);
        CHECK_EQ(shot.explosionRadius, doctest::Approx(512.0f));
        CHECK(shot.blastMinimumDamage > 0);
        CHECK(shot.blastMinimumDamage <= shot.damage);
        CHECK(shot.damage <= shot.blastMaximumDamage);
    }
    SUBCASE("a destructible within blow reach takes a blow, not an arrow")
    {
        config.directWorldTargetDistance = 100.0f;
        const Game::GameplayActionController::PartyAttackExecutionResult result =
            Game::GameplayActionController::executePartyAttack(config);
        CHECK(result.attempted);
        CHECK_EQ(result.attack.mode, Game::CharacterAttackMode::Melee);
        CHECK(world.shots.empty());
    }
}
