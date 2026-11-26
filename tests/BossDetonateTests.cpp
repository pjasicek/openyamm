#include <doctest/doctest.h>

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayActorModifiers.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/party/SpellIds.h"
#include "game/rules/ActorRulesetFacts.h"
#include "game/rules/CrowdControlDiminishing.h"
#include "game/rules/GameRules.h"
#include "game/rules/MonsterRules.h"
#include "game/rules/SpellRules.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/MonsterModifiers.h"

#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace OpenYAMM::Game;

// The boss and detonate modifiers (devdocs/MONSTER_MODIFIERS.md): parsing, the detonation's timing in real time and
// turn-based play, and the Standard rules' diminishing returns on bosses.

namespace
{
MonsterModifierTable modifierTable(const std::string &modifiers)
{
    MonsterModifierTable table;
    std::string error;
    REQUIRE_MESSAGE(table.loadWorldYaml("schema: openyamm.monsterModifiers.v1\nmonsters:\n  10179: [" + modifiers
            + "]\n", "hesper", 10000, 10999, error), error);
    return table;
}

std::string modifierError(const std::string &modifiers)
{
    MonsterModifierTable table;
    std::string error;
    CHECK_FALSE(table.loadWorldYaml("schema: openyamm.monsterModifiers.v1\nmonsters:\n  10179: [" + modifiers + "]\n",
        "hesper", 10000, 10999, error));
    return error;
}

// One detonating actor at x = 0, the party at partyEdgeDistance in sight.
struct DetonateTestActor
{
    bool canAct = true;
    bool alive = true;
    bool engagesParty = true;
    float partyEdgeDistance = 100.0f;
    std::vector<GameplayActorModifiers::DetonateEventKind> events;

    GameplayActorModifiers::ChargeActorFacts facts() const
    {
        GameplayActorModifiers::ChargeActorFacts actorFacts = {};
        actorFacts.monsterId = 10179;
        actorFacts.actorId = 7;
        actorFacts.canAct = canAct;
        actorFacts.alive = alive;
        actorFacts.incapacitated = !canAct && alive;
        actorFacts.engagesParty = engagesParty;
        actorFacts.hostileToParty = true;
        actorFacts.partyEdgeDistance = partyEdgeDistance;
        return actorFacts;
    }

    GameplayActorModifiers::ChargeWorld world()
    {
        GameplayActorModifiers::ChargeWorld chargeWorld = {};
        chargeWorld.hasLineOfSightToParty = [](size_t) { return true; };
        chargeWorld.detonated = [this](const GameplayActorModifiers::DetonateEvent &event)
        {
            events.push_back(event.kind);
        };
        return chargeWorld;
    }
};

constexpr float Step = 1.0f / 30.0f;

void stepDetonate(GameplayActorModifiers &modifiers, DetonateTestActor &actor, float seconds,
    const std::vector<size_t> *pGrants = nullptr)
{
    const GameplayActorModifiers::ChargeWorld world = actor.world();
    for (float elapsed = 0.0f; elapsed < seconds - 0.0001f; elapsed += Step)
    {
        modifiers.updateDetonations(Step, 1, [&](size_t) { return actor.facts(); }, world, pGrants);
    }
}

bool held(const GameplayActorModifiers &modifiers)
{
    ActorAiFrameFacts frame = {};
    ActorAiFacts actorFacts = {};
    actorFacts.actorIndex = 0;
    actorFacts.actorId = 7;
    frame.activeActors.push_back(actorFacts);
    modifiers.applyDetonationHolds(frame);
    return frame.activeActors[0].behavior.holdActive;
}
}

TEST_CASE("boss and detonate modifiers load their parameters, defaults and errors")
{
    const MonsterModifierTable table = modifierTable("boss, detonate");
    const MonsterModifierSet &set = *table.find(10179);
    CHECK(set.boss);
    CHECK(table.hasBoss());
    CHECK(table.hasDetonate());
    REQUIRE(set.detonate);
    const DetonateModifier &detonate = *set.detonate;
    CHECK(detonate.windupSeconds == doctest::Approx(3.0f));
    CHECK(detonate.cooldownSeconds == doctest::Approx(20.0f));
    CHECK(detonate.radius == doctest::Approx(768.0f));
    CHECK(detonate.triggerDistance == 0.0f);
    CHECK(detonate.damage == 0.0f);
    CHECK(detonate.meleeMultiplier == doctest::Approx(1.5f));
    CHECK(detonate.damageType == "melee");
    CHECK_FALSE(detonate.hitsMonsters);
    CHECK(detonate.sound == "monster_detonate_charge");
    CHECK(detonate.explodeSound == "monster_detonate_blast");
    // Turn-based: 20 s are four of its turns; cooldown_turns overrides.
    CHECK(detonate.cooldownTurns == 0);
    CHECK(detonateCooldownTurns(detonate) == 4);
    CHECK(findMonsterModifierInfo("boss") != nullptr);
    CHECK(findMonsterModifierInfo("detonate") != nullptr);

    const MonsterModifierTable custom = modifierTable(
        "{detonate: {windup_seconds: 2, cooldown_seconds: 30, radius: 512, damage: 600, damage_type: fire, "
        "hits_monsters: true, sound: hh_detonate_charge}}");
    const DetonateModifier &given = *custom.find(10179)->detonate;
    CHECK_FALSE(custom.find(10179)->boss);
    CHECK_FALSE(custom.hasBoss());
    CHECK(given.windupSeconds == doctest::Approx(2.0f));
    CHECK(given.radius == doctest::Approx(512.0f));
    CHECK(given.damage == doctest::Approx(600.0f));
    CHECK(given.damageType == "fire");
    CHECK(given.hitsMonsters);
    CHECK(given.sound == "hh_detonate_charge");
    CHECK(detonateCooldownTurns(given) == 6);
    CHECK(detonateCooldownTurns(*modifierTable("{detonate: {cooldown_seconds: 21}}").find(10179)->detonate) == 5);
    CHECK(detonateCooldownTurns(*modifierTable("{detonate: {cooldown_seconds: 0}}").find(10179)->detonate) == 0);
    CHECK(detonateCooldownTurns(
              *modifierTable("{detonate: {cooldown_seconds: 30, cooldown_turns: 2}}").find(10179)->detonate)
        == 2);

    CHECK(modifierError("{detonate: {windup_seconds: 30}}").find("modifiers.yml:3: detonate.windup_seconds must be")
        != std::string::npos);
    CHECK(modifierError("{detonate: {damage_type: plasma}}").find("damage_type must be one of") != std::string::npos);
    CHECK(modifierError("{detonate: {damage: 400, melee_multiplier: 2}}").find("not both") != std::string::npos);
    CHECK(modifierError("{detonate: {damage: 0}}").find("must be above 0") != std::string::npos);
    CHECK(modifierError("{boss: {hp: 3}}").find("boss has no parameter 'hp' (it takes none)") != std::string::npos);
}

TEST_CASE("detonate charges in melee reach, holds and glows, explodes after its wind-up and cools down")
{
    const MonsterModifierTable table =
        modifierTable("{detonate: {windup_seconds: 3, cooldown_seconds: 20, glow_multiplier: 3}}");
    GameplayActorModifiers modifiers;
    modifiers.bind(&table);
    DetonateTestActor actor;

    // Beyond its melee reach nothing happens.
    actor.partyEdgeDistance = GameplayActorModifiers::DetonateMeleeReach + 50.0f;
    stepDetonate(modifiers, actor, 2.0f);
    CHECK(modifiers.detonationCount() == 0);
    CHECK_FALSE(held(modifiers));

    // In reach: the charge starts, holds it and its glow rises.
    actor.partyEdgeDistance = 120.0f;
    stepDetonate(modifiers, actor, Step);
    CHECK(modifiers.detonationCount() == 1);
    REQUIRE(actor.events.size() == 1);
    CHECK(actor.events[0] == GameplayActorModifiers::DetonateEventKind::ChargeStarted);
    CHECK(modifiers.detonatePhase(0, 7) == GameplayActorModifiers::DetonatePhase::Charging);
    CHECK(held(modifiers));
    const char *pRole = nullptr;
    float clipSeconds = -1.0f;
    REQUIRE(modifiers.scriptedClip(0, 7, pRole, clipSeconds));
    CHECK(std::string(pRole) == "detonate");
    stepDetonate(modifiers, actor, 1.5f);
    CHECK(modifiers.detonateChargeShare(0, 7) == doctest::Approx(0.5f).epsilon(0.03));
    CHECK(modifiers.emissionMultiplier(0, 7) == doctest::Approx(2.0f).epsilon(0.03));

    // Hits do not flinch it while it charges.
    CHECK_FALSE(modifiers.allowsStagger(0, 10179, 7, 1000));

    // The party stepping away does not stop the blast: it goes off where the monster stands after 3 s.
    actor.partyEdgeDistance = 900.0f;
    stepDetonate(modifiers, actor, 1.4f);
    CHECK(modifiers.detonationBlastCount() == 0);
    stepDetonate(modifiers, actor, 0.2f);
    CHECK(modifiers.detonationBlastCount() == 1);
    CHECK(actor.events.back() == GameplayActorModifiers::DetonateEventKind::Exploded);
    CHECK(modifiers.detonatePhase(0, 7) == GameplayActorModifiers::DetonatePhase::Blasted);
    CHECK(held(modifiers));
    CHECK(modifiers.emissionMultiplier(0, 7) == doctest::Approx(1.0f));

    // The cooldown: back in reach, no second charge within 20 s of the blast's hold.
    actor.partyEdgeDistance = 100.0f;
    stepDetonate(modifiers, actor, 19.0f);
    CHECK(modifiers.detonationCount() == 1);
    CHECK_FALSE(held(modifiers));
    CHECK(modifiers.allowsStagger(0, 10179, 7, 1000));
    stepDetonate(modifiers, actor, 2.0f);
    CHECK(modifiers.detonationCount() == 2);
}

TEST_CASE("a stun or paralysis in a detonation's charge cancels it; death too; only fighting monsters charge")
{
    const MonsterModifierTable table = modifierTable("{detonate: {cooldown_seconds: 5}}");
    {
        GameplayActorModifiers modifiers;
        modifiers.bind(&table);
        DetonateTestActor actor;
        actor.engagesParty = false;
        stepDetonate(modifiers, actor, 1.0f);
        CHECK(modifiers.detonationCount() == 0);
        actor.engagesParty = true;
        stepDetonate(modifiers, actor, 1.0f);
        REQUIRE(modifiers.detonationCount() == 1);
        actor.canAct = false;
        stepDetonate(modifiers, actor, Step);
        CHECK(modifiers.detonationCancelCount() == 1);
        CHECK(actor.events.back() == GameplayActorModifiers::DetonateEventKind::Cancelled);
        CHECK(modifiers.detonatePhase(0, 7) == GameplayActorModifiers::DetonatePhase::Ready);
        actor.canAct = true;
        stepDetonate(modifiers, actor, 4.5f);
        CHECK(modifiers.detonationCount() == 1);
        CHECK(modifiers.detonationBlastCount() == 0);
        stepDetonate(modifiers, actor, 1.0f);
        CHECK(modifiers.detonationCount() == 2);
    }
    {
        GameplayActorModifiers modifiers;
        modifiers.bind(&table);
        DetonateTestActor actor;
        REQUIRE(modifiers.startDetonation(0, 10179, 7, actor.world()));
        CHECK_FALSE(modifiers.startDetonation(0, 10179, 7, actor.world()));
        CHECK_FALSE(modifiers.startCharge(0, 10179, 7, {}, {}, actor.world()));
        actor.alive = false;
        actor.canAct = false;
        stepDetonate(modifiers, actor, Step);
        CHECK(modifiers.detonationBlastCount() == 0);
        CHECK(modifiers.detonationCancelCount() == 1);
    }
}

TEST_CASE("turn-based: a detonation charges on the monster's turn and explodes at the start of its next")
{
    const MonsterModifierTable table = modifierTable("{detonate: {windup_seconds: 3}}");
    GameplayActorModifiers modifiers;
    modifiers.bind(&table);
    DetonateTestActor actor;
    const std::vector<size_t> none;
    const std::vector<size_t> granted = {0};

    // Not its turn: it waits in reach.
    stepDetonate(modifiers, actor, 1.0f, &none);
    CHECK(modifiers.detonationCount() == 0);
    // Its turn: the charge is its action.
    stepDetonate(modifiers, actor, Step, &granted);
    CHECK(modifiers.detonationCount() == 1);
    CHECK(held(modifiers));
    // The party's turns and the wait stages pass, far past the wind-up: no blast until its next turn.
    stepDetonate(modifiers, actor, 8.0f, &none);
    CHECK(modifiers.detonationBlastCount() == 0);
    CHECK(modifiers.detonateChargeShare(0, 7) == doctest::Approx(1.0f));
    stepDetonate(modifiers, actor, Step, &granted);
    CHECK(modifiers.detonationBlastCount() == 1);
    // The blast was that turn's action: it holds through the step.
    CHECK(held(modifiers));
}

TEST_CASE("turn-based: a detonation's cooldown counts the monster's own turns, not seconds")
{
    // 20 s: four turns (ceil(20 / 5)); cooldown_turns: 2 overrides it.
    for (const auto &[modifiers, turns] : std::vector<std::pair<std::string, int>>{
             {"{detonate: {cooldown_seconds: 20}}", 4}, {"{detonate: {cooldown_seconds: 20, cooldown_turns: 2}}", 2}})
    {
        CAPTURE(modifiers);
        const MonsterModifierTable table = modifierTable(modifiers);
        GameplayActorModifiers actorModifiers;
        actorModifiers.bind(&table);
        DetonateTestActor actor;
        const std::vector<size_t> none;
        const std::vector<size_t> granted = {0};

        stepDetonate(actorModifiers, actor, Step, &granted);
        stepDetonate(actorModifiers, actor, Step, &granted);
        REQUIRE(actorModifiers.detonationBlastCount() == 1);
        // The blast's hold ends between its turns.
        stepDetonate(actorModifiers, actor, 1.0f, &none);
        CHECK_FALSE(held(actorModifiers));

        // Far past 20 s of actor time between turns: still cooling down, for exactly `turns` of its turns.
        for (int turn = 0; turn < turns; ++turn)
        {
            stepDetonate(actorModifiers, actor, 30.0f, &none);
            stepDetonate(actorModifiers, actor, Step, &granted);
            CHECK(actorModifiers.detonationCount() == 1);
        }

        stepDetonate(actorModifiers, actor, Step, &granted);
        CHECK(actorModifiers.detonationCount() == 2);
    }

    // A cancel starts the same count; a cooldown spent in real time leaves none for a later turn-based fight.
    const MonsterModifierTable table = modifierTable("{detonate: {cooldown_seconds: 10}}");
    GameplayActorModifiers actorModifiers;
    actorModifiers.bind(&table);
    DetonateTestActor actor;
    const std::vector<size_t> none;
    const std::vector<size_t> granted = {0};
    stepDetonate(actorModifiers, actor, Step, &granted);
    actor.canAct = false;
    stepDetonate(actorModifiers, actor, Step, &none);
    REQUIRE(actorModifiers.detonationCancelCount() == 1);
    actor.canAct = true;
    stepDetonate(actorModifiers, actor, Step, &granted);
    CHECK(actorModifiers.detonationCount() == 1);
    // One of its two turns waited; the fight goes real-time with the party away until the 10 s have run.
    actor.partyEdgeDistance = 2000.0f;
    stepDetonate(actorModifiers, actor, 11.0f);
    CHECK(actorModifiers.detonationCount() == 1);
    actor.partyEdgeDistance = 100.0f;
    stepDetonate(actorModifiers, actor, Step, &granted);
    CHECK(actorModifiers.detonationCount() == 2);
}

TEST_CASE("a co-op guest mirrors a detonation's charge and blast from its host's poses")
{
    const MonsterModifierTable table = modifierTable("{detonate: {windup_seconds: 2, glow_multiplier: 5}}");
    GameplayActorModifiers modifiers;
    modifiers.bind(&table);
    CHECK(GameplayActorModifiers::replicaPoseFlags(GameplayActorModifiers::DetonatePhase::Ready) == 0);
    CHECK(GameplayActorModifiers::replicaPoseFlags(GameplayActorModifiers::DetonatePhase::Charging)
        == ReplicaActorPose::DetonateCharging);

    GameplayActorModifiers::ReplicaDetonateEdges edges = modifiers.applyReplicaDetonation(0, 10179, 7, true, false);
    CHECK(edges.chargeStarted);
    modifiers.tickReplicaDetonations(1.0f);
    CHECK(modifiers.emissionMultiplier(0, 7) == doctest::Approx(3.0f));
    edges = modifiers.applyReplicaDetonation(0, 10179, 7, true, false);
    CHECK_FALSE(edges.chargeStarted);
    edges = modifiers.applyReplicaDetonation(0, 10179, 7, false, true);
    CHECK(edges.exploded);
    edges = modifiers.applyReplicaDetonation(0, 10179, 7, false, false);
    CHECK_FALSE(edges.cancelled);
    modifiers.applyReplicaDetonation(0, 10179, 7, true, false);
    edges = modifiers.applyReplicaDetonation(0, 10179, 7, false, false);
    CHECK(edges.cancelled);
}

TEST_CASE("Standard rules hold a boss by MAW's durations and diminishing returns; other monsters keep Standard's")
{
    const MonsterModifierTable table = modifierTable("boss");
    GameplayActorModifiers modifiers;
    modifiers.bind(&table);
    CHECK(modifiers.bossCrowdControl(10178) == nullptr);
    CrowdControlDiminishingReturns *pHistory = modifiers.bossCrowdControl(10179);
    REQUIRE(pHistory != nullptr);

    // Paralyze at Grandmaster on a boss with 70 light resistance: 3 game minutes / 1.7 = 3.53 s, a boss holds half
    // (the history counts the whole); recast as each one ends: 18 % of the window spent paralysed cuts the next to
    // three quarters, 31 % to a half.
    CrowdControlCast cast;
    cast.spellId = spellIdValue(SpellId::Paralyze);
    cast.mastery = SkillMastery::Grandmaster;
    cast.skillLevel = 20;
    cast.resistance = 70;
    cast.targetKey = 11;
    cast.partySize = 4;
    cast.pBossHistory = pHistory;
    const SpellRules &standard = standardSpellRules();
    const std::optional<float> first = standard.crowdControlSeconds(cast);
    REQUIRE(first);
    CHECK(*first == doctest::Approx(6.0f / 1.7f * 0.5f).epsilon(0.001));
    cast.nowSeconds = *first * 2.0;
    const std::optional<float> second = standard.crowdControlSeconds(cast);
    CHECK(*second == doctest::Approx(*first * 0.75f).epsilon(0.001));
    cast.nowSeconds += *second * 2.0;
    const std::optional<float> third = standard.crowdControlSeconds(cast);
    CHECK(*third == doctest::Approx(*first * 0.5f).epsilon(0.001));

    // Immune stays immune; slow keeps Standard's own roll and length; a monster without the modifier too.
    cast.resistance = 200;
    CHECK(standard.crowdControlSeconds(cast) == std::optional<float>(0.0f));
    cast.resistance = 70;
    cast.spellId = spellIdValue(SpellId::Slow);
    CHECK_FALSE(standard.crowdControlSeconds(cast));
    cast.spellId = spellIdValue(SpellId::Paralyze);
    cast.pBossHistory = nullptr;
    CHECK_FALSE(standard.crowdControlSeconds(cast));

    // A Grandmaster mace's paralysis on a boss: MAW's 4 s held as a boss, then less; a Master mace's stun becomes
    // MAW's 2 s paralysis. MAW's own blows (their seconds set) pass unchanged.
    CharacterAttackResult blow;
    blow.paralyzeTarget = true;
    modifiers.applyBossBlowCrowdControl(blow, 10179, 12, 0.0);
    CHECK(blow.paralyzeSeconds == std::optional<float>(2.0f));
    blow = {};
    blow.paralyzeTarget = true;
    modifiers.applyBossBlowCrowdControl(blow, 10179, 12, 4.0);
    CHECK(blow.paralyzeSeconds == std::optional<float>(1.5f));
    blow = {};
    blow.stunTarget = true;
    modifiers.applyBossBlowCrowdControl(blow, 10179, 13, 0.0);
    CHECK_FALSE(blow.stunTarget);
    CHECK(blow.paralyzeTarget);
    CHECK(blow.paralyzeSeconds == std::optional<float>(1.0f));
    blow = {};
    blow.stunTarget = true;
    blow.stunSeconds = StaggerStunSeconds;
    modifiers.applyBossBlowCrowdControl(blow, 10179, 14, 0.0);
    CHECK(blow.stunTarget);
    CHECK_FALSE(blow.paralyzeTarget);
    blow = {};
    blow.paralyzeTarget = true;
    modifiers.applyBossBlowCrowdControl(blow, 10178, 15, 0.0);
    CHECK_FALSE(blow.paralyzeSeconds);

    // A blow's fear (FearOnHit10) and berserk (EnrageOnHit5Grandmaster): MAW's Fear (4 game minutes) and Berserk
    // (4.5) at the blow's mastery, two real seconds a minute, held half as a boss, then less through the control
    // group's diminishing returns; another monster keeps the world's own duration.
    blow = {};
    blow.fearTarget = true;
    blow.skillMastery = uint32_t(SkillMastery::Grandmaster);
    GameplayActorModifiers::BossBlowControl control = modifiers.applyBossBlowCrowdControl(blow, 10179, 16, 0.0);
    CHECK(blow.fearTarget);
    CHECK(control.fearSeconds == std::optional<float>(4.0f));
    CHECK_FALSE(control.berserkSeconds);
    blow = {};
    blow.enrageTarget = true;
    blow.skillMastery = uint32_t(SkillMastery::Expert);
    control = modifiers.applyBossBlowCrowdControl(blow, 10179, 17, 0.0);
    CHECK(blow.enrageTarget);
    REQUIRE(control.berserkSeconds);
    CHECK(*control.berserkSeconds == doctest::Approx(4.5f * 0.65f));
    // Feared again 8 s later: the history counts the whole 8 s (40 % of the last 20 s), which halves the next.
    blow = {};
    blow.fearTarget = true;
    blow.skillMastery = uint32_t(SkillMastery::Grandmaster);
    control = modifiers.applyBossBlowCrowdControl(blow, 10179, 16, 8.0);
    REQUIRE(control.fearSeconds);
    CHECK(*control.fearSeconds == doctest::Approx(2.0f));
    blow = {};
    blow.fearTarget = true;
    blow.enrageTarget = true;
    control = modifiers.applyBossBlowCrowdControl(blow, 10178, 18, 0.0);
    CHECK_FALSE(control.fearSeconds);
    CHECK_FALSE(control.berserkSeconds);
    CHECK(blow.fearTarget);
    CHECK(blow.enrageTarget);
}

TEST_CASE("MAW's diminishing returns are the shared history's")
{
    CrowdControlDiminishingReturns history;
    CHECK(history.apply(7, 3, 0, 4, false) == doctest::Approx(4));
    CHECK(history.apply(7, 3, 4, 4, false) == doctest::Approx(3));
    CHECK(history.apply(7, 1, 4, 4, false) == doctest::Approx(4));
    CHECK(history.apply(8, 3, 0, 4, true) == doctest::Approx(2));
    // Immune from 60 % of the window.
    CrowdControlDiminishingReturns immune;
    immune.apply(9, 2, 0, 12, false);
    CHECK(immune.apply(9, 2, 12, 5, false) == 0.0);
}

TEST_CASE("a boss-modifier monster shows the boss skull under Standard and MAW; MAW's own bosses keep their badges")
{
    const MonsterRules &standard = standardGameRules().monsters;
    ActorRulesetFacts facts;
    CHECK(healthBarBadges(standard, facts, false).empty());
    CHECK(healthBarBadges(standard, facts, true) == std::vector<std::string>{"maw_boss_skull"});

    MawRules maw(RulesetOptions{}, MawMapLevels{});
    const MonsterRules &mawMonsters = maw.gameRules().monsters;
    CHECK(healthBarBadges(mawMonsters, facts, false).empty());
    CHECK(healthBarBadges(mawMonsters, facts, true) == std::vector<std::string>{"maw_boss_skull"});
    facts.bossAffix = 1;
    const std::vector<std::string> own = mawMonsters.actorBadges(facts);
    REQUIRE_FALSE(own.empty());
    CHECK(healthBarBadges(mawMonsters, facts, true) == own);
    CHECK(healthBarBadges(mawMonsters, facts, false) == own);
}
