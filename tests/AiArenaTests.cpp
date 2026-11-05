#include "doctest/doctest.h"

#include "game/debug/AiArena.h"
#include "game/gameplay/ActorAiTrace.h"
#include "game/gameplay/GameplayActorAiSystem.h"

#include <cmath>
#include <optional>
#include <string>

using namespace OpenYAMM::Game;

namespace
{
ActorAiFacts makeArenaMeleeActor(size_t actorIndex, float edgeDistanceToParty)
{
    ActorAiFacts actor = {};
    actor.actorIndex = actorIndex;
    actor.actorId = 500 + uint32_t(actorIndex);
    actor.identity.actorId = actor.actorId;
    actor.identity.monsterId = 9183;
    actor.identity.displayName = "Skeletoid";
    actor.identity.hostilityType = 4;
    actor.stats.currentHp = 11;
    actor.stats.maxHp = 11;
    actor.stats.radius = 32;
    actor.stats.height = 128;
    actor.stats.aiType = GameplayActorAiType::Aggressive;
    actor.stats.moveSpeed = 200;
    actor.stats.attack1Damage.diceRolls = 1;
    actor.stats.attack1Damage.diceSides = 4;
    actor.runtime.recoverySeconds = 0.8f;
    actor.runtime.meleeAttackAnimationSeconds = 1.0f;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.world.active = true;
    actor.movement.position = {100.0f, 200.0f, 0.0f};
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 200.0f;
    actor.movement.distanceToParty = edgeDistanceToParty + 96.0f;
    actor.movement.edgeDistanceToParty = edgeDistanceToParty;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {132.0f, 200.0f + edgeDistanceToParty, 64.0f};
    actor.target.currentDistance = edgeDistanceToParty + 96.0f;
    actor.target.currentEdgeDistance = edgeDistanceToParty;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    return actor;
}

ActorAiFrameFacts makeArenaFrame(const ActorAiFacts &actor)
{
    ActorAiFrameFacts frame = {};
    frame.deltaSeconds = 1.0f / 128.0f;
    frame.fixedStepSeconds = 1.0f / 128.0f;
    frame.party.collisionRadius = 32.0f;
    frame.party.collisionHeight = 128.0f;
    frame.activeActors.push_back(actor);
    return frame;
}

ActorAiFrameResult resultWithDecision(size_t actorIndex, ActorAiDecisionKind kind)
{
    ActorAiFrameResult result = {};
    ActorAiUpdate update = {};
    update.actorIndex = actorIndex;
    ActorAiDecision decision = {};
    decision.kind = kind;
    decision.targetKind = ActorAiTargetKind::Party;
    update.state.decision = decision;
    result.actorUpdates.push_back(update);
    return result;
}

size_t countEntries(const ActorAiTrace &trace, const std::string &name)
{
    size_t count = 0;

    for (const ActorAiTraceEntry &entry : trace.entries())
    {
        count += entry.name == name ? 1 : 0;
    }

    return count;
}
}

TEST_CASE("AI arena parses the party, monsters and their overrides")
{
    const std::string text = R"(
name: skirmisher
world: mm9
map: thearena.blv
asset_root: output/mm9_rework/assets_dev
party: {position: [0, -2000, 1], yaw_degrees: 90, pitch_degrees: -5, members: 2}
trace: true
monsters:
  - monster_id: 9183
    position: [0, 0, 1]
    yaw_degrees: 270
    overrides: {strafe_attack_chance: 1, evade_chance: 0.5, skirmish: true, ai_type: suicide}
  - {monster_id: 9185, position: [400, 0, 1], hostile: false, group: 3}
)";
    std::string error;
    const std::optional<AiArena> arena = parseAiArenaText(text, "skirmisher.arena.yml", error);
    REQUIRE_MESSAGE(arena, error);
    CHECK(arena->name == "skirmisher");
    CHECK(arena->map == "thearena.blv");
    CHECK(arena->clearActors);
    CHECK(arena->party.invulnerable);
    CHECK(arena->party.y == -2000.0f);
    CHECK(std::abs(arena->party.yawRadians - 1.5707963f) < 1e-5f);
    REQUIRE(arena->party.members);
    CHECK(*arena->party.members == 2);
    REQUIRE(arena->monsters.size() == 2);
    REQUIRE(arena->monsters[0].yawRadians);
    CHECK(std::abs(*arena->monsters[0].yawRadians - 4.712389f) < 1e-5f);
    CHECK_FALSE(arena->monsters[1].hostile);
    CHECK(arena->monsters[1].group == 3);
    CHECK(arena->monsters[1].overrides.empty());

    ActorAiFacts facts = {};
    facts.tactics.strafeAttackChance = 0.2f;
    facts.tactics.evadeSeconds = 2.0f;
    arena->monsters[0].overrides.apply(facts);
    CHECK(facts.tactics.strafeAttackChance == 1.0f);
    CHECK(facts.tactics.evadeChance == 0.5f);
    CHECK(facts.tactics.skirmish);
    CHECK(facts.tactics.evadeSeconds == 2.0f);
    CHECK(facts.stats.aiType == GameplayActorAiType::Suicide);
}

TEST_CASE("AI arena rejects unknown keys and overrides")
{
    std::string error;
    CHECK_FALSE(parseAiArenaText("map: a.blv\nparty: {position: [0, 0, 0]}\nmonstres: []\n", "a.yml", error));
    CHECK(error.find("monstres") != std::string::npos);
    error.clear();
    CHECK_FALSE(parseAiArenaText("map: a.blv\nparty: {position: [0, 0, 0]}\n"
        "monsters: [{monster_id: 1, position: [0, 0, 0], overrides: {strafe: 1}}]\n", "a.yml", error));
    CHECK(error.find("unknown override 'strafe'") != std::string::npos);
    error.clear();
    CHECK_FALSE(parseAiArenaText("party: {position: [0, 0, 0]}\n", "a.yml", error));
    CHECK(error.find("map") != std::string::npos);
}

TEST_CASE("AI trace lines carry the time, actor, decision, target and detail")
{
    ActorAiTraceEntry entry = {};
    entry.timeSeconds = 12.3f;
    entry.actorIndex = 3;
    entry.monsterId = 9183;
    entry.actorName = "Skeletoid";
    entry.decision = true;
    entry.name = "strafe_attack";
    entry.target = "party";
    entry.detail = "chance 0.80 roll 0.13";
    CHECK(formatActorAiTraceLine(entry)
        == "[ai] t=12.300 actor=3 monster=9183 \"Skeletoid\" decision=strafe_attack target=party "
           "detail=\"chance 0.80 roll 0.13\"");
    entry.decision = false;
    entry.name = "died";
    entry.target.clear();
    entry.detail.clear();
    CHECK(formatActorAiTraceLine(entry) == "[ai] t=12.300 actor=3 monster=9183 \"Skeletoid\" event=died");

    ActorAiDecision decision = {};
    decision.kind = ActorAiDecisionKind::AttackMelee;
    decision.hasAbility = true;
    decision.ability = GameplayActorAttackAbility::Attack2;
    decision.chance = 0.8f;
    decision.roll = 0.13f;
    CHECK(actorAiDecisionDetail(decision) == "ability attack2 chance 0.80 roll 0.13");
    CHECK(actorAiDecisionFromName("back_off") == ActorAiDecisionKind::BackOff);
    CHECK(actorAiDecisionFromName("swoop") == ActorAiDecisionKind::Swoop);
    CHECK_FALSE(actorAiDecisionFromName("teleport"));
}

TEST_CASE("AI trace records a lasting decision once and every attack, damage and death")
{
    ActorAiTrace trace;
    ActorAiFrameFacts frame = makeArenaFrame(makeArenaMeleeActor(4, 600.0f));
    trace.traceActor(4);

    for (int step = 0; step < 3; ++step)
    {
        trace.observe(frame, resultWithDecision(4, ActorAiDecisionKind::Pursue));
    }

    trace.observe(frame, resultWithDecision(4, ActorAiDecisionKind::AttackMelee));
    trace.observe(frame, resultWithDecision(4, ActorAiDecisionKind::AttackMelee));
    frame.activeActors[0].stats.currentHp = 5;
    trace.observe(frame, ActorAiFrameResult{});
    frame.activeActors[0].status.dead = true;
    trace.observe(frame, ActorAiFrameResult{});

    CHECK(countEntries(trace, "spawn") == 1);
    CHECK(countEntries(trace, "target") == 1);
    CHECK(countEntries(trace, "pursue") == 1);
    CHECK(countEntries(trace, "attack_melee") == 2);
    CHECK(countEntries(trace, "damaged") == 1);
    CHECK(countEntries(trace, "died") == 1);
    CHECK(std::abs(trace.timeSeconds() - 7.0f / 128.0f) < 1e-6f);

    const std::vector<ActorAiTrace::OverlayItem> items = trace.overlayItems();
    REQUIRE(items.size() == 1);
    CHECK(items[0].actorIndex == 4);
    REQUIRE(items[0].lines.size() == 4);
    CHECK(items[0].lines[0] == "dead");
    CHECK(items[0].lines[1].find("attack_melee") != std::string::npos);

    // Untraced actors are ignored once the arena names its own (the map's, before them); what spawns after the
    // arena's monsters (a pod, a death spawn) is traced.
    ActorAiFrameFacts other = makeArenaFrame(makeArenaMeleeActor(2, 600.0f));
    const size_t before = trace.entries().size();
    trace.observe(other, resultWithDecision(2, ActorAiDecisionKind::Pursue));
    CHECK(trace.entries().size() == before);
    ActorAiFrameFacts spawned = makeArenaFrame(makeArenaMeleeActor(9, 600.0f));
    trace.observe(spawned, resultWithDecision(9, ActorAiDecisionKind::Pursue));
    CHECK(trace.entries().size() > before);
}

TEST_CASE("shared actor AI reports its decisions for the trace")
{
    const GameplayActorAiSystem system;
    const ActorAiFrameResult attack = system.updateActors(makeArenaFrame(makeArenaMeleeActor(1, 0.0f)));
    REQUIRE(attack.actorUpdates.size() == 1);
    REQUIRE(attack.actorUpdates[0].state.decision);
    CHECK(attack.actorUpdates[0].state.decision->kind == ActorAiDecisionKind::AttackMelee);
    CHECK(attack.actorUpdates[0].state.decision->targetKind == ActorAiTargetKind::Party);
    CHECK(attack.actorUpdates[0].state.decision->hasAbility);

    const ActorAiFrameResult pursue = system.updateActors(makeArenaFrame(makeArenaMeleeActor(1, 800.0f)));
    REQUIRE(pursue.actorUpdates.size() == 1);
    REQUIRE(pursue.actorUpdates[0].state.decision);
    CHECK(pursue.actorUpdates[0].state.decision->kind == ActorAiDecisionKind::Pursue);
}

TEST_CASE("AI arena overrides apply to the named actors only")
{
    ActorAiTrace trace;
    ActorAiFactsOverride actorOverride;
    std::string error;
    REQUIRE(actorOverride.setField("evade_chance", "1", error));
    REQUIRE_FALSE(actorOverride.setField("evade_chance", "often", error));
    CHECK(error.find("not a number") != std::string::npos);
    trace.setOverride(2, actorOverride);

    ActorAiFrameFacts frame = makeArenaFrame(makeArenaMeleeActor(2, 0.0f));
    frame.backgroundActors.push_back(makeArenaMeleeActor(3, 0.0f));
    trace.applyOverrides(frame);
    CHECK(frame.activeActors[0].tactics.evadeChance == 1.0f);
    CHECK(frame.backgroundActors[0].tactics.evadeChance == 0.0f);
}

TEST_CASE("AI trace records the moment an attack applies and the playback rate of the attack layer")
{
    ActorAiTrace trace;
    trace.setAnimationRecording(true);
    ActorAiFrameFacts frame = makeArenaFrame(makeArenaMeleeActor(4, 0.0f));
    trace.traceActor(4);
    frame.activeActors[0].runtime.motionState = ActorAiMotionState::Attacking;
    frame.activeActors[0].runtime.animationTimeTicks = 0.4f * 128.0f;
    trace.observe(frame, ActorAiFrameResult{});
    ActorAiFrameResult impact = {};
    ActorAiUpdate update = {};
    update.actorIndex = 4;
    update.state.attackImpactTriggered = true;
    impact.actorUpdates.push_back(update);
    trace.observe(frame, impact);
    // Once: the next step already carries the applied attack.
    frame.activeActors[0].runtime.attackImpactTriggered = true;
    trace.observe(frame, impact);
    REQUIRE(countEntries(trace, "impact") == 1);

    for (const ActorAiTraceEntry &entry : trace.entries())
    {
        if (entry.name == "impact")
        {
            CHECK(entry.detail == "attack1 at 0.400");
        }
    }

    // A swing over the run: the legs at 1.5, the layer at 1.0, measured over AnimationRateWindowSeconds.
    ActorAnimationTraceSample sample;
    sample.clip = "Running";
    sample.layerClip = "AttackMelee";
    sample.durationSeconds = 1.0f;
    sample.layerDurationSeconds = 0.8f;
    sample.deltaSeconds = 1.0f / 30.0f;
    sample.speed = 384.0f;

    for (int frameIndex = 0; frameIndex < 8; ++frameIndex)
    {
        sample.timeSeconds = 1.5f * sample.deltaSeconds * float(frameIndex);
        sample.layerTimeSeconds = sample.deltaSeconds * float(frameIndex);
        sample.blendSeconds = frameIndex == 0 ? 0.12f : -1.0f;
        trace.observe(frame, ActorAiFrameResult{});
        trace.observeAnimation(4, sample);
    }

    // The layer slows to half its speed: a line of its own, carrying both rates.
    for (int frameIndex = 8; frameIndex < 16; ++frameIndex)
    {
        sample.timeSeconds = 1.5f * sample.deltaSeconds * float(frameIndex);
        sample.layerTimeSeconds = sample.deltaSeconds * (8.0f + 0.5f * float(frameIndex - 8));
        trace.observeAnimation(4, sample);
    }

    std::vector<std::string> anim;

    for (const ActorAiTraceEntry &entry : trace.entries())
    {
        if (entry.name == "anim")
        {
            anim.push_back(entry.detail);
        }
    }

    REQUIRE(anim.size() == 2);
    CHECK(anim[0] == "main=Running layer=AttackMelee speed=384 blend=0.12");
    CHECK(anim[1] == "main=Running layer=AttackMelee rate=1.50 layer_rate=0.50 speed=384");
}
