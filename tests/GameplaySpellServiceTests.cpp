#include "engine/AssetFileSystem.h"
#include "game/app/GameSession.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayActionController.h"
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
    pAttacker->attackSpellName = pLifedrain->name;
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
}
