#include "doctest/doctest.h"

#include "engine/TextTable.h"
#include "game/StringUtils.h"
#include "game/gameplay/GameplayActorAiSystem.h"
#include "game/gameplay/ActorVocalizationRules.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/MonsterSpellSupport.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/SpellTable.h"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <optional>
#include <set>
#include <sstream>
#include <string>
#include <vector>

using OpenYAMM::Game::ActorAiAnimationState;
using OpenYAMM::Game::ActorAiFacts;
using OpenYAMM::Game::ActorAiFrameFacts;
using OpenYAMM::Game::ActorAiFxRequestKind;
using OpenYAMM::Game::ActorAiMovementAction;
using OpenYAMM::Game::ActorAiMotionState;
using OpenYAMM::Game::ActorAiTargetKind;
using OpenYAMM::Game::GameplayActorAttackAbility;
using OpenYAMM::Game::GameplayActorAiType;
using OpenYAMM::Game::GameplayActorControlMode;
using OpenYAMM::Game::GameplayActorAiSystem;
using OpenYAMM::Game::GameplayActorService;
using OpenYAMM::Game::MonsterTable;

namespace
{
ActorAiFacts makeActor(size_t actorIndex, uint32_t actorId)
{
    ActorAiFacts actor = {};
    actor.actorIndex = actorIndex;
    actor.actorId = actorId;
    actor.identity.actorId = actorId;
    actor.stats.currentHp = 10;
    actor.stats.maxHp = 10;
    actor.stats.radius = 32;
    actor.stats.height = 128;
    actor.runtime.motionState = ActorAiMotionState::Standing;
    actor.runtime.animationState = ActorAiAnimationState::Standing;
    actor.movement.position = {100.0f, 200.0f, 0.0f};
    return actor;
}

ActorAiFrameFacts makeFrame()
{
    ActorAiFrameFacts frame = {};
    frame.deltaSeconds = 1.0f / 128.0f;
    frame.fixedStepSeconds = 1.0f / 128.0f;
    frame.party.position = {0.0f, 0.0f, 0.0f};
    frame.party.collisionRadius = 32.0f;
    frame.party.collisionHeight = 128.0f;
    return frame;
}

std::vector<std::string> makeActorServiceMonsterStatsRow(int id)
{
    std::vector<std::string> row(38);
    row[0] = std::to_string(id);
    row[1] = "Monster " + std::to_string(id);
    row[2] = "MonsterPic" + std::to_string(id);
    row[3] = "1";
    row[4] = "10";
    row[5] = "0";
    row[6] = "10";
    row[10] = "short";
    row[11] = "normal";
    row[13] = "100";
    row[14] = "30";
    row[17] = "Physical";
    row[18] = "1d4";
    return row;
}

std::string trimCopy(const std::string &value)
{
    const size_t first = value.find_first_not_of(" \t\r\n");

    if (first == std::string::npos)
    {
        return {};
    }

    const size_t last = value.find_last_not_of(" \t\r\n");
    return value.substr(first, last - first + 1);
}

std::optional<std::vector<std::vector<std::string>>> loadAssetTextTableRows(const std::string &relativePath)
{
    const std::filesystem::path path = std::filesystem::path(OPENYAMM_SOURCE_DIR) / relativePath;
    std::ifstream input(path);

    if (!input)
    {
        return std::nullopt;
    }

    std::ostringstream contents;
    contents << input.rdbuf();
    const std::optional<OpenYAMM::Engine::TextTable> table =
        OpenYAMM::Engine::TextTable::parseTabSeparated(contents.str());

    if (!table)
    {
        return std::nullopt;
    }

    std::vector<std::vector<std::string>> rows;
    rows.reserve(table->getRowCount());

    for (size_t rowIndex = 0; rowIndex < table->getRowCount(); ++rowIndex)
    {
        rows.push_back(table->getRow(rowIndex));
    }

    return rows;
}

std::string monsterSpellNameFromDescriptor(const std::string &descriptor)
{
    if (descriptor.empty() || descriptor == "0")
    {
        return {};
    }

    const size_t comma = descriptor.find(',');
    return OpenYAMM::Game::toLowerCopy(trimCopy(descriptor.substr(0, comma)));
}
}

TEST_CASE("shared actor AI marks newly killed active actors dead without outdoor runtime")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(3, 100);
    actor.stats.currentHp = 0;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    CHECK_EQ(update.actorIndex, 3u);
    REQUIRE(update.state.dead.has_value());
    CHECK(*update.state.dead);
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Dead);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Dead);
    REQUIRE_EQ(update.fxRequests.size(), 1u);
    CHECK(update.fxRequests.front().kind == ActorAiFxRequestKind::Death);
}

TEST_CASE("shared actor AI keeps already dead active actors on the dead frame")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(4, 101);
    actor.status.dead = true;
    actor.runtime.motionState = ActorAiMotionState::Dead;
    actor.runtime.animationState = ActorAiAnimationState::Dead;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Dead);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Dead);
    CHECK(update.fxRequests.empty());
}

TEST_CASE("shared actor AI keeps immobile actors standing instead of walking in place")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(5, 102);
    actor.world.active = true;
    actor.runtime.motionState = ActorAiMotionState::Wandering;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.runtime.actionSeconds = 1.0f;
    actor.movement.movementAllowed = false;
    actor.movement.allowIdleWander = true;
    actor.movement.wanderRadius = 2048.0f;
    actor.movement.moveDirectionX = 1.0f;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Standing);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Standing);
    CHECK(update.movementIntent.action == ActorAiMovementAction::Stand);
    CHECK_FALSE(update.movementIntent.applyMovement);
}

TEST_CASE("shared actor AI lets party controlled friendly actors wander near the party")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(1, 1);
    actor.world.active = true;
    actor.identity.hostilityType = 0;
    actor.identity.targetPolicy.controlMode = GameplayActorControlMode::Reanimated;
    actor.status.hostileToParty = false;
    actor.movement.homePosition = actor.movement.position;
    actor.movement.wanderRadius = 1024.0f;
    actor.movement.effectiveMoveSpeed = 200.0f;
    actor.movement.allowIdleWander = true;
    actor.movement.movementAllowed = true;
    actor.movement.distanceToParty = 0.0f;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Wandering);
    CHECK(update.movementIntent.action == ActorAiMovementAction::Wander);
    CHECK(update.movementIntent.applyMovement);
}

TEST_CASE("shared actor AI marks first party detection without playing a monster alert sound")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(2, 100);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = false;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {0.0f, 0.0f, 64.0f};
    actor.target.currentDistance = 4096.0f;
    actor.target.currentEdgeDistance = 4096.0f;
    actor.target.currentCanSense = true;
    actor.target.currentHasAttackLineOfSight = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.hasDetectedParty.has_value());
    CHECK(*update.state.hasDetectedParty);
    CHECK(update.audioRequests.empty());
    CHECK(result.audioRequests.empty());
}

TEST_CASE("shared actor AI drops an invisible party target")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    frame.party.invisible = true;
    ActorAiFacts actor = makeActor(2, 100);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {0.0f, 0.0f, 64.0f};
    actor.target.currentDistance = 128.0f;
    actor.target.currentEdgeDistance = 64.0f;
    actor.target.currentCanSense = true;
    actor.target.currentHasAttackLineOfSight = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.hasDetectedParty.has_value());
    CHECK_FALSE(*update.state.hasDetectedParty);
    CHECK_FALSE(update.attackRequest.has_value());
}

TEST_CASE("shared actor service lets hostile actors target party controlled actors in the same group")
{
    MonsterTable monsterTable = {};
    REQUIRE(monsterTable.loadStatsFromRows({makeActorServiceMonsterStatsRow(1), makeActorServiceMonsterStatsRow(2)}));

    GameplayActorService service = {};
    service.bindTables(&monsterTable, nullptr);

    OpenYAMM::Game::GameplayActorTargetPolicyState hostileActor = {};
    hostileActor.monsterId = 1;
    hostileActor.group = 7;
    hostileActor.hostileToParty = true;
    hostileActor.height = 128;

    OpenYAMM::Game::GameplayActorTargetPolicyState reanimatedActor = {};
    reanimatedActor.monsterId = 2;
    reanimatedActor.group = 7;
    reanimatedActor.hostileToParty = false;
    reanimatedActor.controlMode = GameplayActorControlMode::Reanimated;
    reanimatedActor.height = 128;

    const OpenYAMM::Game::GameplayActorTargetPolicyResult result =
        service.resolveActorTargetPolicy(hostileActor, reanimatedActor);

    CHECK(result.canTarget);
    CHECK_EQ(result.relationToTarget, 4);
    CHECK(result.engagementRange > 0.0f);
}

TEST_CASE("shared actor service lets party controlled actors target party hostiles")
{
    MonsterTable monsterTable = {};
    REQUIRE(monsterTable.loadStatsFromRows({makeActorServiceMonsterStatsRow(1), makeActorServiceMonsterStatsRow(2)}));

    GameplayActorService service = {};
    service.bindTables(&monsterTable, nullptr);

    OpenYAMM::Game::GameplayActorTargetPolicyState summonedActor = {};
    summonedActor.monsterId = 1;
    summonedActor.group = 999;
    summonedActor.hostileToParty = false;
    summonedActor.controlMode = GameplayActorControlMode::Enslaved;
    summonedActor.height = 128;

    OpenYAMM::Game::GameplayActorTargetPolicyState hostileActor = {};
    hostileActor.monsterId = 2;
    hostileActor.group = 999;
    hostileActor.hostileToParty = true;
    hostileActor.height = 128;

    const OpenYAMM::Game::GameplayActorTargetPolicyResult hostileResult =
        service.resolveActorTargetPolicy(summonedActor, hostileActor);

    CHECK(hostileResult.canTarget);
    CHECK_EQ(hostileResult.relationToTarget, 4);
    CHECK(hostileResult.engagementRange > 0.0f);

    hostileActor.hostileToParty = false;

    const OpenYAMM::Game::GameplayActorTargetPolicyResult friendlyResult =
        service.resolveActorTargetPolicy(summonedActor, hostileActor);

    CHECK_FALSE(friendlyResult.canTarget);
}

TEST_CASE("shared actor service respects runtime party hostility overrides")
{
    MonsterTable monsterTable = {};
    REQUIRE(monsterTable.loadStatsFromRows({makeActorServiceMonsterStatsRow(1)}));
    REQUIRE(monsterTable.loadRelationsFromRows({
        {"", "Party", "Monster 1"},
        {"Party", "0", "3"},
        {"Monster 1", "0", "0"},
    }));

    GameplayActorService service = {};
    service.bindTables(&monsterTable, nullptr);

    OpenYAMM::Game::GameplayActorTargetPolicyState actor = {};
    actor.monsterId = 1;
    actor.relationMonsterId = 1;
    actor.hostileToParty = false;

    CHECK_EQ(service.partyEngagementRange(actor), 0.0f);

    actor.hostileToParty = true;

    CHECK_EQ(
        service.partyEngagementRange(actor),
        OpenYAMM::Game::GameplayActorService::MaximumPartyEngagementRange);

    service.setPartyEngagementRange(4096.0f);
    CHECK_EQ(service.configuredPartyEngagementRange(), 4096.0f);
    CHECK_EQ(service.partyEngagementRange(actor), 4096.0f);
}

TEST_CASE("shared actor AI exposes a melee recovery window after the attack animation")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(11, 108);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.aiType = GameplayActorAiType::Normal;
    actor.stats.moveSpeed = 200;
    actor.stats.attack1Damage.diceRolls = 1;
    actor.stats.attack1Damage.diceSides = 4;
    actor.runtime.recoverySeconds = 0.8f;
    actor.runtime.meleeAttackAnimationSeconds = 1.0f;
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 200.0f;
    actor.movement.distanceToParty = 96.0f;
    actor.movement.edgeDistanceToParty = 0.0f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {132.0f, 200.0f, 64.0f};
    actor.target.currentDistance = 96.0f;
    actor.target.currentEdgeDistance = 0.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult attackResult = system.updateActors(frame);

    REQUIRE_EQ(attackResult.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &attackUpdate = attackResult.actorUpdates.front();
    REQUIRE(attackUpdate.state.motionState.has_value());
    CHECK(*attackUpdate.state.motionState == ActorAiMotionState::Attacking);
    REQUIRE(attackUpdate.state.actionSeconds.has_value());
    CHECK(*attackUpdate.state.actionSeconds == doctest::Approx(1.0f));
    REQUIRE(attackUpdate.state.attackCooldownSeconds.has_value());
    CHECK(*attackUpdate.state.attackCooldownSeconds == doctest::Approx(1.25f));

    actor.runtime.motionState = ActorAiMotionState::Attacking;
    actor.runtime.animationState = ActorAiAnimationState::AttackMelee;
    actor.runtime.actionSeconds = 1.0f / 256.0f;
    actor.runtime.attackCooldownSeconds = 0.25f;
    actor.runtime.queuedAttackAbility = OpenYAMM::Game::GameplayActorAttackAbility::Attack1;
    actor.runtime.attackImpactTriggered = true;
    frame.activeActors.clear();
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult recoveryResult = system.updateActors(frame);

    REQUIRE_EQ(recoveryResult.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &recoveryUpdate = recoveryResult.actorUpdates.front();
    REQUIRE(recoveryUpdate.state.motionState.has_value());
    CHECK(*recoveryUpdate.state.motionState == ActorAiMotionState::Standing);
    REQUIRE(recoveryUpdate.state.attackCooldownSeconds.has_value());
    CHECK(*recoveryUpdate.state.attackCooldownSeconds > 0.0f);
}

TEST_CASE("shared actor AI preserves ranged presentation and tracks the target during windup")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(12, 109);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.runtime.motionState = ActorAiMotionState::Attacking;
    actor.runtime.animationState = ActorAiAnimationState::AttackMelee;
    actor.runtime.queuedAttackAbility = GameplayActorAttackAbility::Attack1;
    actor.runtime.actionSeconds = 0.5f;
    actor.runtime.attackImpactTriggered = false;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {132.0f, 200.0f, 64.0f};
    actor.target.currentDistance = 512.0f;
    actor.target.currentEdgeDistance = 400.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::AttackRanged);
    REQUIRE(update.movementIntent.updateYaw);
    CHECK(update.movementIntent.yawRadians == doctest::Approx(0));

    frame.activeActors[0].target.currentPosition = {100, 300, 64};
    const OpenYAMM::Game::ActorAiFrameResult moved = system.updateActors(frame);
    REQUIRE_EQ(moved.actorUpdates.size(), 1u);
    CHECK(moved.actorUpdates[0].movementIntent.updateYaw);
    CHECK(moved.actorUpdates[0].movementIntent.yawRadians == doctest::Approx(std::atan2(100.0f, 0.0f)));
    CHECK_FALSE(moved.actorUpdates[0].attackRequest.has_value());
    CHECK(moved.projectileRequests.empty());

    frame.activeActors[0].target.currentKind = ActorAiTargetKind::Actor;
    frame.activeActors[0].target.currentActorIndex = 6;
    frame.activeActors[0].target.currentPosition = {0, 200, 64};
    const OpenYAMM::Game::ActorAiFrameResult infighting = system.updateActors(frame);
    REQUIRE_EQ(infighting.actorUpdates.size(), 1u);
    CHECK(infighting.actorUpdates[0].movementIntent.updateYaw);
    CHECK(infighting.actorUpdates[0].movementIntent.yawRadians == doctest::Approx(std::atan2(0.0f, -100.0f)));
}

TEST_CASE("shared actor AI uses a missile attack outside melee range when the melee attack chance is certain")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(12, 109);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.attack2Chance = 100;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.runtime.rangedAttackAnimationSeconds = 0.5f;
    actor.movement.movementAllowed = false;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {1024.0f, 200.0f, 64.0f};
    actor.target.currentDistance = 1024.0f;
    actor.target.currentEdgeDistance = 900.0f;
    actor.target.currentCanSense = true;
    actor.target.currentHasAttackLineOfSight = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Attacking);
    REQUIRE(update.state.queuedAttackAbility.has_value());
    CHECK(*update.state.queuedAttackAbility == GameplayActorAttackAbility::Attack1);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::AttackRanged);
}

TEST_CASE("shared actor AI returns to standing presentation when attack impact resolves")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(12, 109);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.aiType = GameplayActorAiType::Normal;
    actor.stats.attack1Damage.diceRolls = 1;
    actor.stats.attack1Damage.diceSides = 4;
    actor.runtime.motionState = ActorAiMotionState::Attacking;
    actor.runtime.animationState = ActorAiAnimationState::AttackMelee;
    actor.runtime.animationTimeTicks = 128.0f;
    actor.runtime.actionSeconds = 1.0f / 256.0f;
    actor.runtime.attackCooldownSeconds = 0.5f;
    actor.runtime.queuedAttackAbility = GameplayActorAttackAbility::Attack1;
    actor.runtime.attackImpactTriggered = false;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {132.0f, 200.0f, 64.0f};
    actor.target.currentDistance = 96.0f;
    actor.target.currentEdgeDistance = 0.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.attackRequest.has_value());
    REQUIRE(update.state.attackImpactTriggered.has_value());
    CHECK(*update.state.attackImpactTriggered);
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Standing);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Standing);
    REQUIRE(update.animation.animationTimeTicks.has_value());
    CHECK(*update.animation.animationTimeTicks == doctest::Approx(0.0f));
    REQUIRE(update.state.attackCooldownSeconds.has_value());
    CHECK(*update.state.attackCooldownSeconds > 0.0f);
}

TEST_CASE("shared actor AI doubles attack recovery while slowed")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(11, 108);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.status.spellEffects.slowRemainingSeconds = 10.0f;
    actor.stats.aiType = GameplayActorAiType::Normal;
    actor.stats.moveSpeed = 200;
    actor.stats.attack1Damage.diceRolls = 1;
    actor.stats.attack1Damage.diceSides = 4;
    actor.runtime.recoverySeconds = 0.8f;
    actor.runtime.meleeAttackAnimationSeconds = 1.0f;
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 200.0f;
    actor.movement.distanceToParty = 96.0f;
    actor.movement.edgeDistanceToParty = 0.0f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {132.0f, 200.0f, 64.0f};
    actor.target.currentDistance = 96.0f;
    actor.target.currentEdgeDistance = 0.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult attackResult = system.updateActors(frame);

    REQUIRE_EQ(attackResult.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &attackUpdate = attackResult.actorUpdates.front();
    REQUIRE(attackUpdate.state.attackCooldownSeconds.has_value());
    CHECK(*attackUpdate.state.attackCooldownSeconds > 1.25f);
}

TEST_CASE("shared actor AI pursues a remembered party target without attack line of sight")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(21, 121);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.aiType = GameplayActorAiType::Normal;
    actor.stats.moveSpeed = 200;
    actor.stats.attack1Damage.diceRolls = 1;
    actor.stats.attack1Damage.diceSides = 4;
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 200.0f;
    actor.movement.inMeleeRange = true;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {132.0f, 200.0f, 64.0f};
    actor.target.currentDistance = 96.0f;
    actor.target.currentEdgeDistance = 0.0f;
    actor.target.currentCanSense = true;
    actor.target.currentHasAttackLineOfSight = false;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Pursuing);
    CHECK(update.movementIntent.action == ActorAiMovementAction::Pursue);
    CHECK(update.movementIntent.applyMovement);
    CHECK(update.movementIntent.moveSpeed == doctest::Approx(300.0f));
    CHECK_FALSE(update.movementIntent.inMeleeRange);
    CHECK_FALSE(update.attackRequest.has_value());
}

TEST_CASE("shared actor AI scales pursuit speed and caps it")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(24, 124);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.aiType = GameplayActorAiType::Normal;
    actor.stats.moveSpeed = 700;
    actor.stats.attack1Damage.diceRolls = 1;
    actor.stats.attack1Damage.diceSides = 4;
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 700.0f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {600.0f, 200.0f, 64.0f};
    actor.target.currentDistance = 500.0f;
    actor.target.currentEdgeDistance = 500.0f;
    actor.target.currentCanSense = true;
    actor.target.currentHasAttackLineOfSight = false;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Pursuing);
    CHECK(update.movementIntent.applyMovement);
    CHECK(update.movementIntent.moveSpeed == doctest::Approx(1000.0f));
}

TEST_CASE("shared actor AI emits vertical movement for flying actors pursuing above or below")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(22, 122);
    actor.world.active = true;
    actor.world.targetZ = 96.0f;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.aiType = GameplayActorAiType::Normal;
    actor.stats.canFly = true;
    actor.stats.moveSpeed = 200;
    actor.stats.attack1Damage.diceRolls = 1;
    actor.stats.attack1Damage.diceSides = 4;
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 200.0f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {100.0f, 200.0f, 400.0f};
    actor.target.currentDistance = 1024.0f;
    actor.target.currentEdgeDistance = 1024.0f;
    actor.target.currentCanSense = true;
    actor.target.currentHasAttackLineOfSight = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Pursuing);
    CHECK(update.movementIntent.action == ActorAiMovementAction::Pursue);
    CHECK(update.movementIntent.applyMovement);
    CHECK(update.movementIntent.desiredMoveZ > 0.99f);
    CHECK_FALSE(update.attackRequest.has_value());
}

TEST_CASE("shared actor AI uses movement target height for flying pursuit")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(24, 124);
    actor.world.active = true;
    actor.world.targetZ = 96.0f;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.aiType = GameplayActorAiType::Normal;
    actor.stats.canFly = true;
    actor.stats.moveSpeed = 200;
    actor.stats.attack1Damage.diceRolls = 1;
    actor.stats.attack1Damage.diceSides = 4;
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 200.0f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {100.0f, 200.0f, 96.0f};
    actor.target.currentMovementPosition = {100.0f, 200.0f, 400.0f};
    actor.target.hasCurrentMovementPosition = true;
    actor.target.currentDistance = 1024.0f;
    actor.target.currentEdgeDistance = 1024.0f;
    actor.target.currentCanSense = true;
    actor.target.currentHasAttackLineOfSight = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    CHECK(update.movementIntent.applyMovement);
    CHECK(update.movementIntent.targetPosition.z == doctest::Approx(400.0f));
    CHECK(update.movementIntent.desiredMoveZ > 0.99f);
    CHECK_FALSE(update.attackRequest.has_value());
}

TEST_CASE("shared actor AI lets flying pursuit use party body height instead of attack point")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(25, 125);
    actor.world.active = true;
    actor.world.targetZ = 375.0f;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.aiType = GameplayActorAiType::Normal;
    actor.stats.canFly = true;
    actor.stats.moveSpeed = 200;
    actor.stats.attack1Damage.diceRolls = 1;
    actor.stats.attack1Damage.diceSides = 4;
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 200.0f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {1024.0f, 200.0f, 96.0f};
    actor.target.currentMovementPosition = {1024.0f, 200.0f, 192.0f};
    actor.target.hasCurrentMovementPosition = true;
    actor.target.currentDistance = 2048.0f;
    actor.target.currentEdgeDistance = 2048.0f;
    actor.target.currentCanSense = true;
    actor.target.currentHasAttackLineOfSight = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    CHECK(update.movementIntent.applyMovement);
    CHECK(update.movementIntent.targetPosition.z == doctest::Approx(192.0f));
    CHECK(update.movementIntent.desiredMoveZ < 0.0f);
    CHECK(update.movementIntent.desiredMoveZ > -0.5f);
    CHECK_FALSE(update.attackRequest.has_value());
}

TEST_CASE("shared actor AI pursues instead of firing blocked ranged attacks")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(23, 123);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.aiType = GameplayActorAiType::Normal;
    actor.stats.moveSpeed = 200;
    actor.stats.attack1Damage.diceRolls = 1;
    actor.stats.attack1Damage.diceSides = 4;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.stats.attackConstraints.rangedCommitAllowed = false;
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 200.0f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {400.0f, 200.0f, 64.0f};
    actor.target.currentDistance = 300.0f;
    actor.target.currentEdgeDistance = 300.0f;
    actor.target.currentCanSense = true;
    actor.target.currentHasAttackLineOfSight = false;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Pursuing);
    CHECK(update.movementIntent.action == ActorAiMovementAction::Pursue);
    CHECK(update.movementIntent.applyMovement);
    CHECK_FALSE(update.movementIntent.targetHasAttackLineOfSight);
    CHECK_FALSE(update.attackRequest.has_value());
}

TEST_CASE("shared actor AI skips monster power cure at full health")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(12, 109);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.currentHp = 10;
    actor.stats.maxHp = 10;
    actor.stats.hasSpell1 = true;
    actor.stats.spell1Name = "power cure";
    actor.stats.spell1UseChance = 100;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.runtime.rangedAttackAnimationSeconds = 0.5f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {0.0f, 0.0f, 64.0f};
    actor.target.currentDistance = 512.0f;
    actor.target.currentEdgeDistance = 512.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.queuedAttackAbility.has_value());
    CHECK(*update.state.queuedAttackAbility == GameplayActorAttackAbility::Attack1);
}

TEST_CASE("shared actor AI skips monster heal at full health")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(17, 114);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.currentHp = 10;
    actor.stats.maxHp = 10;
    actor.stats.hasSpell1 = true;
    actor.stats.spell1Name = "heal";
    actor.stats.spell1UseChance = 100;
    actor.stats.spell1CastSupported = true;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.runtime.rangedAttackAnimationSeconds = 0.5f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {0.0f, 0.0f, 64.0f};
    actor.target.currentDistance = 512.0f;
    actor.target.currentEdgeDistance = 512.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.queuedAttackAbility.has_value());
    CHECK(*update.state.queuedAttackAbility == GameplayActorAttackAbility::Attack1);
}

TEST_CASE("shared actor AI allows monster power cure when wounded")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(13, 110);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.currentHp = 5;
    actor.stats.maxHp = 10;
    actor.stats.hasSpell1 = true;
    actor.stats.spell1Name = "power cure";
    actor.stats.spell1UseChance = 100;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.runtime.rangedAttackAnimationSeconds = 0.5f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {0.0f, 0.0f, 64.0f};
    actor.target.currentDistance = 512.0f;
    actor.target.currentEdgeDistance = 512.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.queuedAttackAbility.has_value());
    CHECK(*update.state.queuedAttackAbility == GameplayActorAttackAbility::Spell1);
}

TEST_CASE("monster spell support includes implemented monster-data spells")
{
    const std::vector<std::string> projectileSpellNames = {
        "Acid Burst",
        "Blades",
        "Dark Grasp",
        "Fire Bolt",
        "Fireball",
        "Harm",
        "Ice Blast",
        "Ice Bolt",
        "Implosion",
        "Incinerate",
        "Light Bolt",
        "Lightning Bolt",
        "Mass Distortion",
        "Mind Blast",
        "Poison Spray",
        "Rock Blast",
        "Sparks",
        "Spirit Lash",
        "Toxic Cloud",
    };

    for (const std::string &spellName : projectileSpellNames)
    {
        CHECK(OpenYAMM::Game::isMonsterProjectileSpellName(spellName));
    }

    const std::vector<std::string> selfActionSpellNames = {
        "Bless",
        "Haste",
        "Heal",
        "Heroism",
        "Pain Reflection",
        "Shield",
    };

    for (const std::string &spellName : selfActionSpellNames)
    {
        CHECK(OpenYAMM::Game::isMonsterSelfActionSpellName(spellName));
    }
}

TEST_CASE("monster data spell names resolve and unsupported mechanics stay explicit")
{
    const std::optional<std::vector<std::vector<std::string>>> monsterRows =
        loadAssetTextTableRows("assets_dev/engine/data_tables/monster_data.txt");
    const std::optional<std::vector<std::vector<std::string>>> spellRows =
        loadAssetTextTableRows("assets_dev/engine/data_tables/spells.txt");
    REQUIRE(monsterRows.has_value());
    REQUIRE(spellRows.has_value());

    OpenYAMM::Game::SpellTable spellTable = {};
    REQUIRE(spellTable.loadFromRows(*spellRows));

    std::set<std::string> unsupportedSpellNames;
    std::set<std::string> unresolvedSpellNames;

    for (const std::vector<std::string> &row : *monsterRows)
    {
        if (row.size() <= 27 || row[0].empty() || row[0].find_first_not_of("0123456789") != std::string::npos)
        {
            continue;
        }

        for (size_t column : {25u, 27u})
        {
            const std::string spellName = monsterSpellNameFromDescriptor(row[column]);

            if (spellName.empty())
            {
                continue;
            }

            if (spellTable.findByName(spellName) == nullptr)
            {
                if (!OpenYAMM::Game::isKnownUnsupportedMonsterSpellName(spellName))
                {
                    unresolvedSpellNames.insert(spellName);
                }
            }

            if (!OpenYAMM::Game::isMonsterProjectileSpellName(spellName)
                && !OpenYAMM::Game::isMonsterSelfActionSpellName(spellName)
                && !OpenYAMM::Game::isKnownUnsupportedMonsterSpellName(spellName))
            {
                unsupportedSpellNames.insert(spellName);
            }
        }
    }

    CHECK(unresolvedSpellNames.empty());
    CHECK(unsupportedSpellNames.empty());
}

TEST_CASE("shared actor AI skips spell attacks that the world cannot resolve")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(16, 113);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.hasSpell1 = true;
    actor.stats.spell1Name = "spirit lash";
    actor.stats.spell1UseChance = 100;
    actor.stats.spell1CastSupported = false;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.runtime.rangedAttackAnimationSeconds = 0.5f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {0.0f, 0.0f, 64.0f};
    actor.target.currentDistance = 512.0f;
    actor.target.currentEdgeDistance = 512.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.queuedAttackAbility.has_value());
    CHECK(*update.state.queuedAttackAbility == GameplayActorAttackAbility::Attack1);
}

TEST_CASE("shared actor AI skips monster self buff while already active")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(14, 111);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.status.spellEffects.heroismRemainingSeconds = 60.0f;
    actor.stats.hasSpell1 = true;
    actor.stats.spell1Name = "heroism";
    actor.stats.spell1UseChance = 100;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.runtime.rangedAttackAnimationSeconds = 0.5f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {0.0f, 0.0f, 64.0f};
    actor.target.currentDistance = 512.0f;
    actor.target.currentEdgeDistance = 512.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.queuedAttackAbility.has_value());
    CHECK(*update.state.queuedAttackAbility == GameplayActorAttackAbility::Attack1);
}

TEST_CASE("shared actor AI applies monster self buff when spell attack completes")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(15, 112);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.hasSpell1 = true;
    actor.stats.spell1Id = 51;
    actor.stats.spell1Name = "heroism";
    actor.stats.spell1SkillLevel = 4;
    actor.stats.spell1SkillMastery = OpenYAMM::Game::SkillMastery::Master;
    actor.stats.spell1UseChance = 100;
    actor.runtime.motionState = ActorAiMotionState::Attacking;
    actor.runtime.animationState = ActorAiAnimationState::AttackRanged;
    actor.runtime.queuedAttackAbility = GameplayActorAttackAbility::Spell1;
    actor.runtime.actionSeconds = 0.0f;
    actor.runtime.attackImpactTriggered = false;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {0.0f, 0.0f, 64.0f};
    actor.target.currentDistance = 512.0f;
    actor.target.currentEdgeDistance = 512.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.spellEffects.has_value());
    CHECK(update.state.spellEffects->heroismRemainingSeconds > 0.0f);
    CHECK_EQ(update.state.spellEffects->heroismPower, 9);
    REQUIRE(update.state.attackImpactTriggered.has_value());
    CHECK(*update.state.attackImpactTriggered);
    CHECK(!update.state.queuedAttackAbility.has_value());
    REQUIRE_EQ(update.fxRequests.size(), 1u);
    CHECK(update.fxRequests.front().kind == ActorAiFxRequestKind::Buff);
    CHECK(update.fxRequests.front().spellId == 51u);
    CHECK(result.projectileRequests.empty());
    CHECK(result.audioRequests.empty());
}

TEST_CASE("shared actor AI applies monster heal when spell attack completes")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(18, 115);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.currentHp = 5;
    actor.stats.maxHp = 20;
    actor.stats.hasSpell1 = true;
    actor.stats.spell1Id = 68;
    actor.stats.spell1Name = "heal";
    actor.stats.spell1SkillLevel = 5;
    actor.stats.spell1SkillMastery = OpenYAMM::Game::SkillMastery::Expert;
    actor.stats.spell1UseChance = 100;
    actor.runtime.motionState = ActorAiMotionState::Attacking;
    actor.runtime.animationState = ActorAiAnimationState::AttackRanged;
    actor.runtime.queuedAttackAbility = GameplayActorAttackAbility::Spell1;
    actor.runtime.actionSeconds = 0.0f;
    actor.runtime.attackImpactTriggered = false;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {0.0f, 0.0f, 64.0f};
    actor.target.currentDistance = 512.0f;
    actor.target.currentEdgeDistance = 512.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.currentHp.has_value());
    CHECK_EQ(*update.state.currentHp, 20);
    REQUIRE(update.state.attackImpactTriggered.has_value());
    CHECK(*update.state.attackImpactTriggered);
    CHECK(!update.state.queuedAttackAbility.has_value());
    REQUIRE_EQ(update.fxRequests.size(), 1u);
    CHECK(update.fxRequests.front().kind == ActorAiFxRequestKind::Buff);
    CHECK(update.fxRequests.front().spellId == 68u);
    CHECK(result.projectileRequests.empty());
    CHECK(result.audioRequests.empty());
}

TEST_CASE("shared actor service applies monster buff combat modifiers")
{
    GameplayActorService service = {};
    OpenYAMM::Game::GameplayActorSpellEffectState state = {};
    state.stoneskinRemainingSeconds = 60.0f;
    state.stoneskinPower = 8;
    state.hourOfPowerRemainingSeconds = 60.0f;
    state.hourOfPowerPower = 10;
    state.heroismRemainingSeconds = 60.0f;
    state.heroismPower = 7;
    state.hammerhandsRemainingSeconds = 60.0f;
    state.hammerhandsPower = 3;
    state.blessRemainingSeconds = 60.0f;
    state.blessPower = 5;
    state.fateRemainingSeconds = 60.0f;
    state.fatePower = 20;
    state.hasteRemainingSeconds = 60.0f;
    state.shieldRemainingSeconds = 60.0f;
    state.painReflectionRemainingSeconds = 60.0f;

    CHECK_EQ(service.effectiveArmorClass(12, state), 22);
    CHECK_EQ(service.effectiveAttackDamageBonus(GameplayActorAttackAbility::Attack1, state), 13);
    CHECK_EQ(service.effectiveAttackDamageBonus(GameplayActorAttackAbility::Attack2, state), 0);
    CHECK_EQ(service.effectiveAttackHitBonus(state), 30);
    CHECK(service.effectiveRecoveryProgressMultiplier(state) > 1.0f);
    CHECK(service.halveIncomingMissileDamage(state));
    CHECK(service.hasPainReflection(state));
}

TEST_CASE("shared actor service clears status locks before reanimated control is applied")
{
    GameplayActorService service = {};
    OpenYAMM::Game::GameplayActorSpellEffectState state = {};
    state.stunRemainingSeconds = 5.0f;
    state.paralyzeRemainingSeconds = 10.0f;
    state.fearRemainingSeconds = 20.0f;
    state.blindRemainingSeconds = 30.0f;
    state.slowRemainingSeconds = 40.0f;
    state.slowMoveMultiplier = 0.5f;
    state.slowRecoveryMultiplier = 2.0f;
    state.stoneskinRemainingSeconds = 50.0f;
    state.stoneskinPower = 7;
    state.hostileToParty = true;
    state.hasDetectedParty = true;

    CHECK(service.clearSpellEffects(state, false));

    state.controlMode = GameplayActorControlMode::Reanimated;
    state.controlRemainingSeconds = 24.0f * 60.0f * 60.0f;

    CHECK_EQ(state.stunRemainingSeconds, 0.0f);
    CHECK_EQ(state.paralyzeRemainingSeconds, 0.0f);
    CHECK_EQ(state.fearRemainingSeconds, 0.0f);
    CHECK_EQ(state.blindRemainingSeconds, 0.0f);
    CHECK_EQ(state.slowRemainingSeconds, 0.0f);
    CHECK_EQ(state.slowMoveMultiplier, 1.0f);
    CHECK_EQ(state.slowRecoveryMultiplier, 1.0f);
    CHECK_EQ(state.stoneskinRemainingSeconds, 0.0f);
    CHECK_EQ(state.stoneskinPower, 0);
    CHECK_FALSE(state.hostileToParty);
    CHECK_FALSE(state.hasDetectedParty);
    CHECK_EQ(state.controlMode, GameplayActorControlMode::Reanimated);
    CHECK(state.controlRemainingSeconds > 0.0f);
}

TEST_CASE("shared actor service breaks fear and control when damaged by the party")
{
    GameplayActorService service = {};
    OpenYAMM::Game::GameplayActorSpellEffectState state = {};
    state.fearRemainingSeconds = 20.0f;
    state.controlRemainingSeconds = 60.0f;
    state.controlMode = GameplayActorControlMode::Enslaved;
    state.hostileToParty = false;
    state.hasDetectedParty = false;

    CHECK(service.breakFearAndControlOnPartyDamage(state));

    CHECK_EQ(state.fearRemainingSeconds, 0.0f);
    CHECK_EQ(state.controlRemainingSeconds, 0.0f);
    CHECK(state.controlMode == GameplayActorControlMode::None);
    CHECK(state.hostileToParty);
    CHECK(state.hasDetectedParty);
}

TEST_CASE("shared actor AI suppresses repeat low health fleeing for non-wimps")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(18, 115);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.status.suppressLowHealthFlee = true;
    actor.stats.aiType = GameplayActorAiType::Normal;
    actor.stats.currentHp = 1;
    actor.stats.maxHp = 20;
    actor.stats.moveSpeed = 200;
    actor.stats.attack1Damage.diceRolls = 1;
    actor.stats.attack1Damage.diceSides = 4;
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 200.0f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {132.0f, 200.0f, 64.0f};
    actor.target.currentDistance = 96.0f;
    actor.target.currentEdgeDistance = 0.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Attacking);
}

TEST_CASE("shared actor AI applies monster melee buff damage and hit bonuses")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(17, 114);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.monsterLevel = 12;
    actor.stats.attack1Damage.diceRolls = 2;
    actor.stats.attack1Damage.diceSides = 4;
    actor.stats.attack1Damage.bonus = 1;
    actor.status.spellEffects.heroismRemainingSeconds = 60.0f;
    actor.status.spellEffects.heroismPower = 7;
    actor.status.spellEffects.hammerhandsRemainingSeconds = 60.0f;
    actor.status.spellEffects.hammerhandsPower = 3;
    actor.status.spellEffects.blessRemainingSeconds = 60.0f;
    actor.status.spellEffects.blessPower = 5;
    actor.status.spellEffects.fateRemainingSeconds = 60.0f;
    actor.status.spellEffects.fatePower = 20;
    actor.runtime.motionState = ActorAiMotionState::Attacking;
    actor.runtime.animationState = ActorAiAnimationState::AttackMelee;
    actor.runtime.queuedAttackAbility = GameplayActorAttackAbility::Attack1;
    actor.runtime.actionSeconds = 0.0f;
    actor.runtime.attackImpactTriggered = false;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {0.0f, 0.0f, 64.0f};
    actor.target.currentDistance = 96.0f;
    actor.target.currentEdgeDistance = 0.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.attackRequest.has_value());
    CHECK_GE(update.attackRequest->damage, 13);
    CHECK_LE(update.attackRequest->damage, 19);
    CHECK_EQ(update.attackRequest->attackBonus, 25);
    REQUIRE(update.state.spellEffects.has_value());
    CHECK_EQ(update.state.spellEffects->fateRemainingSeconds, doctest::Approx(0.0f));
    CHECK_EQ(update.state.spellEffects->fatePower, 0);
}

TEST_CASE("shared actor AI orbits during ranged recovery instead of closing to melee")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(16, 113);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.aiType = GameplayActorAiType::Normal;
    actor.stats.moveSpeed = 160;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.runtime.attackCooldownSeconds = 0.5f;
    actor.runtime.recoverySeconds = 0.5f;
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 160.0f;
    actor.movement.position = {1000.0f, 0.0f, 0.0f};
    actor.movement.distanceToParty = 1000.0f;
    actor.movement.edgeDistanceToParty = 936.0f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {0.0f, 0.0f, 64.0f};
    actor.target.currentDistance = 1000.0f;
    actor.target.currentEdgeDistance = 936.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Pursuing);
    CHECK(update.movementIntent.applyMovement);
    CHECK(update.movementIntent.action == ActorAiMovementAction::Pursue);
    CHECK_FALSE(update.movementIntent.meleePursuitActive);
    CHECK(update.movementIntent.targetHasAttackLineOfSight);
    CHECK(std::abs(update.movementIntent.desiredMoveY) > 0.9f);
    CHECK(update.movementIntent.desiredMoveX < 0.0f);
    CHECK(std::abs(update.movementIntent.desiredMoveX) < 0.25f);
}

TEST_CASE("shared actor AI may change ranged orbit side on a fresh pursuit decision")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(16, 113);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.aiType = GameplayActorAiType::Normal;
    actor.stats.moveSpeed = 160;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.runtime.attackCooldownSeconds = 0.5f;
    actor.runtime.recoverySeconds = 0.5f;
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 160.0f;
    actor.movement.position = {1000.0f, 0.0f, 0.0f};
    actor.movement.distanceToParty = 1000.0f;
    actor.movement.edgeDistanceToParty = 936.0f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {0.0f, 0.0f, 64.0f};
    actor.target.currentDistance = 1000.0f;
    actor.target.currentEdgeDistance = 936.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult firstResult = system.updateActors(frame);
    REQUIRE_EQ(firstResult.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &firstUpdate = firstResult.actorUpdates.front();
    REQUIRE(firstUpdate.state.pursueDecisionCount.has_value());
    CHECK(firstUpdate.movementIntent.action == ActorAiMovementAction::Pursue);
    CHECK(std::abs(firstUpdate.movementIntent.desiredMoveY) > 0.9f);

    frame.activeActors.clear();
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.runtime.actionSeconds = 0.0f;
    actor.runtime.pursueDecisionCount = *firstUpdate.state.pursueDecisionCount;
    actor.movement.moveDirectionX = firstUpdate.movementIntent.moveDirectionX;
    actor.movement.moveDirectionY = firstUpdate.movementIntent.moveDirectionY;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult secondResult = system.updateActors(frame);
    REQUIRE_EQ(secondResult.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &secondUpdate = secondResult.actorUpdates.front();
    CHECK(secondUpdate.movementIntent.action == ActorAiMovementAction::Pursue);
    CHECK(secondUpdate.movementIntent.desiredMoveY * firstUpdate.movementIntent.desiredMoveY < 0.0f);
    CHECK(secondUpdate.movementIntent.moveDirectionY * firstUpdate.movementIntent.moveDirectionY < 0.0f);
}

TEST_CASE("shared actor AI preserves move direction while continuing pursuit")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(17, 114);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.aiType = GameplayActorAiType::Normal;
    actor.stats.moveSpeed = 160;
    actor.stats.attack1Damage.diceRolls = 1;
    actor.stats.attack1Damage.diceSides = 4;
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.runtime.actionSeconds = 0.5f;
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 160.0f;
    actor.movement.moveDirectionX = 0.6f;
    actor.movement.moveDirectionY = -0.8f;
    actor.movement.position = {1000.0f, 0.0f, 0.0f};
    actor.movement.distanceToParty = 1000.0f;
    actor.movement.edgeDistanceToParty = 936.0f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {0.0f, 0.0f, 64.0f};
    actor.target.currentDistance = 1000.0f;
    actor.target.currentEdgeDistance = 936.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    CHECK(update.movementIntent.action == ActorAiMovementAction::Pursue);
    CHECK(update.movementIntent.moveDirectionX == doctest::Approx(0.6f));
    CHECK(update.movementIntent.moveDirectionY == doctest::Approx(-0.8f));
    CHECK(update.movementIntent.desiredMoveX == doctest::Approx(0.6f));
    CHECK(update.movementIntent.desiredMoveY == doctest::Approx(-0.8f));
}

TEST_CASE("shared actor AI stands briefly when actor movement is crowded after collision")
{
    GameplayActorAiSystem system;
    ActorAiFacts actor = makeActor(6, 103);
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.movement.contactedActorCount = 2;
    actor.movement.meleePursuitActive = true;
    actor.movement.movementBlocked = true;

    const OpenYAMM::Game::ActorAiUpdate update = system.updateActorAfterWorldMovement(actor);

    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Standing);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Standing);
    REQUIRE(update.state.crowdStandRemainingSeconds.has_value());
    CHECK(*update.state.crowdStandRemainingSeconds > 0.0f);
    CHECK(update.movementIntent.clearVelocity);
}

TEST_CASE("shared actor AI crowd steers after blocked movement without an actor contact")
{
    GameplayActorAiSystem system;
    ActorAiFacts actor = makeActor(30, 130);
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.actionSeconds = 5.0f;
    actor.movement.position = {0.0f, 0.0f, 0.0f};
    actor.movement.allowCrowdSteering = true;
    actor.movement.meleePursuitActive = true;
    actor.movement.movementBlocked = true;
    actor.target.currentPosition = {400.0f, 0.0f, 0.0f};
    actor.target.currentEdgeDistance = 400.0f;

    SUBCASE("direct approach")
    {
        const OpenYAMM::Game::ActorAiUpdate update = system.updateActorAfterWorldMovement(actor);
        CHECK(update.movementIntent.crowdSteeringActive);
        CHECK(update.movementIntent.desiredMoveX > 0.5f);
        CHECK(std::abs(update.movementIntent.desiredMoveY) > 0.5f);
        REQUIRE(update.state.actionSeconds.has_value());
        CHECK(*update.state.actionSeconds < 0.3f);
    }

    SUBCASE("navigation supplies the approach direction around a wall")
    {
        actor.target.hasCurrentMovementPosition = true;
        actor.target.currentMovementPosition = {0.0f, 200.0f, 0.0f};
        const OpenYAMM::Game::ActorAiUpdate update = system.updateActorAfterWorldMovement(actor);
        CHECK(update.movementIntent.crowdSteeringActive);
        CHECK(update.movementIntent.desiredMoveY > 0.5f);
        CHECK(std::abs(update.movementIntent.desiredMoveX) > 0.5f);
    }

    SUBCASE("an unobstructed approach does not start crowd steering")
    {
        actor.movement.movementBlocked = false;
        CHECK_FALSE(system.updateActorAfterWorldMovement(actor).movementIntent.crowdSteeringActive);
    }

    SUBCASE("a monster already within melee range does not sidestep")
    {
        actor.movement.inMeleeRange = true;
        CHECK_FALSE(system.updateActorAfterWorldMovement(actor).movementIntent.crowdSteeringActive);
    }
}

TEST_CASE("shared actor AI keeps a crowd detour until its lock expires and attacks when in reach")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(31, 131);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.moveSpeed = 160;
    actor.stats.attack1Damage.diceRolls = 1;
    actor.stats.attack1Damage.diceSides = 4;
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.runtime.actionSeconds = 0.2f;
    actor.runtime.crowdSideLockRemainingSeconds = 0.2f;
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 160.0f;
    actor.movement.moveDirectionX = -0.6f;
    actor.movement.moveDirectionY = 0.8f;
    actor.movement.position = {400.0f, 0.0f, 0.0f};
    actor.movement.distanceToParty = 400.0f;
    actor.movement.edgeDistanceToParty = 336.0f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {0.0f, 0.0f, 64.0f};
    actor.target.currentDistance = 400.0f;
    actor.target.currentEdgeDistance = 336.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    bool expectDetour = true;
    bool expectAttack = false;

    SUBCASE("active sidestep") {}
    SUBCASE("expired sidestep yields to navigation")
    {
        actor.runtime.crowdSideLockRemainingSeconds = 0.0f;
        expectDetour = false;
    }
    SUBCASE("melee range ends the detour and the crowd wait")
    {
        actor.runtime.crowdStandRemainingSeconds = 1.0f;
        actor.movement.position.x = 300.0f;
        actor.movement.distanceToParty = 300.0f;
        actor.movement.edgeDistanceToParty = 236.0f;
        actor.movement.inMeleeRange = true;
        actor.target.currentDistance = 300.0f;
        actor.target.currentEdgeDistance = 236.0f;
        expectDetour = false;
        expectAttack = true;
    }
    frame.activeActors.push_back(actor);
    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);
    REQUIRE(result.actorUpdates.size() == 1);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    CHECK(update.movementIntent.crowdSteeringActive == expectDetour);
    if (expectAttack)
    {
        REQUIRE(update.state.motionState.has_value());
        CHECK(*update.state.motionState == ActorAiMotionState::Attacking);
    }
    else
    {
        CHECK(update.movementIntent.desiredMoveX == doctest::Approx(-0.6f));
        CHECK(update.movementIntent.desiredMoveY == doctest::Approx(0.8f));
    }
}

TEST_CASE("shared actor AI stands when pursuing movement is suppressed by navigation")
{
    GameplayActorAiSystem system;
    ActorAiFacts actor = makeActor(27, 127);
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.runtime.actionSeconds = 1.0f;
    actor.movement.meleePursuitActive = true;
    actor.movement.movementSuppressedByNavigation = true;
    actor.movement.allowCrowdSteering = true;
    actor.movement.movementBlocked = true;
    actor.target.currentPosition = {300.0f, 200.0f, 0.0f};
    actor.target.currentEdgeDistance = 400.0f;

    const OpenYAMM::Game::ActorAiUpdate update = system.updateActorAfterWorldMovement(actor);

    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Standing);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Standing);
    CHECK(update.movementIntent.action == ActorAiMovementAction::Stand);
    CHECK(update.movementIntent.moveDirectionX == doctest::Approx(0.0f));
    CHECK(update.movementIntent.moveDirectionY == doctest::Approx(0.0f));
    CHECK(update.movementIntent.clearVelocity);
    REQUIRE(update.state.actionSeconds.has_value());
    CHECK(*update.state.actionSeconds == doctest::Approx(0.25f));
}

TEST_CASE("shared actor AI flees briefly after a single hostile actor contact")
{
    GameplayActorAiSystem system;
    ActorAiFacts actor = makeActor(7, 104);
    actor.identity.hostilityType = 4;
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.movement.contactedActorCount = 1;
    actor.movement.hasContactedActor = true;
    actor.movement.contactedActorHostilityType = 4;
    actor.movement.contactedActorPosition = {50.0f, 200.0f, 0.0f};

    const OpenYAMM::Game::ActorAiUpdate update = system.updateActorAfterWorldMovement(actor);

    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Fleeing);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Walking);
    CHECK(update.movementIntent.action == ActorAiMovementAction::Flee);
    CHECK(update.movementIntent.moveDirectionX > 0.99f);
    CHECK(std::abs(update.movementIntent.moveDirectionY) < 0.01f);
    CHECK(update.movementIntent.clearVelocity);
    REQUIRE(update.state.actionSeconds.has_value());
    CHECK(*update.state.actionSeconds > 0.0f);
}

TEST_CASE("shared actor AI lets flying actors react to actor contact")
{
    GameplayActorAiSystem system;
    ActorAiFacts actor = makeActor(8, 105);
    actor.identity.hostilityType = 4;
    actor.stats.canFly = true;
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.movement.contactedActorCount = 1;
    actor.movement.hasContactedActor = true;
    actor.movement.contactedActorHostilityType = 4;
    actor.movement.contactedActorPosition = {50.0f, 200.0f, 0.0f};

    const OpenYAMM::Game::ActorAiUpdate update = system.updateActorAfterWorldMovement(actor);

    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Fleeing);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Walking);
    CHECK(update.movementIntent.action == ActorAiMovementAction::Flee);
    CHECK(update.movementIntent.moveDirectionX > 0.99f);
    CHECK(std::abs(update.movementIntent.moveDirectionY) < 0.01f);
    CHECK(update.movementIntent.clearVelocity);
}

TEST_CASE("shared actor AI crowd steers while flying")
{
    GameplayActorAiSystem system;
    ActorAiFacts actor = makeActor(26, 126);
    actor.identity.hostilityType = 4;
    actor.stats.canFly = true;
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.movement.contactedActorCount = 1;
    actor.movement.hasContactedActor = true;
    actor.movement.contactedActorHostilityType = 4;
    actor.movement.contactedActorPosition = {50.0f, 200.0f, 0.0f};
    actor.movement.meleePursuitActive = true;
    actor.movement.allowCrowdSteering = true;
    actor.movement.effectiveMoveSpeed = 200.0f;
    actor.target.currentPosition = {300.0f, 200.0f, 0.0f};
    actor.target.currentEdgeDistance = 400.0f;

    const OpenYAMM::Game::ActorAiUpdate update = system.updateActorAfterWorldMovement(actor);

    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Pursuing);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Walking);
    CHECK(update.movementIntent.action == ActorAiMovementAction::Pursue);
    const bool hasDesiredMovement =
        update.movementIntent.desiredMoveX != 0.0f || update.movementIntent.desiredMoveY != 0.0f;
    CHECK(hasDesiredMovement);
    CHECK_FALSE(update.movementIntent.clearVelocity);
    REQUIRE(update.state.crowdSideSign.has_value());
    CHECK(*update.state.crowdSideSign != 0);
}

TEST_CASE("shared actor AI continues fleeing with base speed")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(25, 125);
    actor.world.active = true;
    actor.runtime.motionState = ActorAiMotionState::Fleeing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.runtime.actionSeconds = 1.0f;
    actor.movement.movementAllowed = true;
    actor.movement.moveDirectionX = 1.0f;
    actor.movement.effectiveMoveSpeed = 180.0f;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Fleeing);
    CHECK(update.movementIntent.action == ActorAiMovementAction::Flee);
    CHECK(update.movementIntent.applyMovement);
    CHECK(update.movementIntent.moveSpeed == doctest::Approx(180.0f));
}

TEST_CASE("shared actor AI preserves crowd steering instead of overwriting it with contact flee")
{
    GameplayActorAiSystem system;
    ActorAiFacts actor = makeActor(10, 107);
    actor.identity.hostilityType = 4;
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.movement.contactedActorCount = 1;
    actor.movement.hasContactedActor = true;
    actor.movement.contactedActorHostilityType = 4;
    actor.movement.contactedActorPosition = {50.0f, 200.0f, 0.0f};
    actor.movement.meleePursuitActive = true;
    actor.movement.allowCrowdSteering = true;
    actor.movement.effectiveMoveSpeed = 200.0f;
    actor.target.currentPosition = {300.0f, 200.0f, 0.0f};
    actor.target.currentEdgeDistance = 400.0f;

    const OpenYAMM::Game::ActorAiUpdate update = system.updateActorAfterWorldMovement(actor);

    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Pursuing);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Walking);
    CHECK(update.movementIntent.action == ActorAiMovementAction::Pursue);
    const bool hasDesiredMovement =
        update.movementIntent.desiredMoveX != 0.0f || update.movementIntent.desiredMoveY != 0.0f;
    CHECK(hasDesiredMovement);
    CHECK_FALSE(update.movementIntent.clearVelocity);
    REQUIRE(update.state.crowdSideSign.has_value());
    CHECK(*update.state.crowdSideSign != 0);
}

TEST_CASE("shared actor AI scales single hostile contact flee duration by actor move speed")
{
    GameplayActorAiSystem system;
    ActorAiFacts actor = makeActor(9, 106);
    actor.identity.hostilityType = 4;
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.movement.effectiveMoveSpeed = 200.0f;
    actor.movement.contactedActorCount = 1;
    actor.movement.hasContactedActor = true;
    actor.movement.contactedActorHostilityType = 4;
    actor.movement.contactedActorPosition = {-200.0f, 200.0f, 0.0f};

    const OpenYAMM::Game::ActorAiUpdate update = system.updateActorAfterWorldMovement(actor);

    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Fleeing);
    REQUIRE(update.state.actionSeconds.has_value());
    CHECK(*update.state.actionSeconds > 1.4f);
    CHECK(*update.state.actionSeconds < 1.6f);
}

TEST_CASE("shared actor AI faces a single friendly actor contact")
{
    GameplayActorAiSystem system;
    ActorAiFacts actor = makeActor(8, 105);
    actor.identity.hostilityType = 0;
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.movement.contactedActorCount = 1;
    actor.movement.hasContactedActor = true;
    actor.movement.contactedActorHostilityType = 0;
    actor.movement.contactedActorPosition = {100.0f, 300.0f, 0.0f};

    const OpenYAMM::Game::ActorAiUpdate update = system.updateActorAfterWorldMovement(actor);

    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Standing);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Standing);
    CHECK(update.movementIntent.action == ActorAiMovementAction::Stand);
    CHECK(update.movementIntent.updateYaw);
    CHECK(update.movementIntent.clearVelocity);
    REQUIRE(update.state.actionSeconds.has_value());
    CHECK(*update.state.actionSeconds > 0.0f);
}

TEST_CASE("shared actor AI advances dying actors until the final dead frame")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(5, 102);
    actor.stats.currentHp = 0;
    actor.runtime.motionState = ActorAiMotionState::Dying;
    actor.runtime.animationState = ActorAiAnimationState::Dying;
    actor.runtime.actionSeconds = 1.0f / 256.0f;
    actor.runtime.animationTimeTicks = 10.0f;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
    REQUIRE(update.state.dead.has_value());
    CHECK(*update.state.dead);
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Dead);
    REQUIRE(update.animation.animationState.has_value());
    CHECK(*update.animation.animationState == ActorAiAnimationState::Dead);
}

TEST_CASE("shared actor hit reaction gate blocks terminal and active attack states")
{
    GameplayActorService service = {};

    CHECK(service.canActorEnterHitReaction(false, false, false, false, false, false, false));
    CHECK_FALSE(service.canActorEnterHitReaction(true, false, false, false, false, false, false));
    CHECK_FALSE(service.canActorEnterHitReaction(false, true, false, false, false, false, false));
    CHECK_FALSE(service.canActorEnterHitReaction(false, false, true, false, false, false, false));
    CHECK_FALSE(service.canActorEnterHitReaction(false, false, false, true, false, false, false));
    CHECK_FALSE(service.canActorEnterHitReaction(false, false, false, false, true, false, false));
    CHECK_FALSE(service.canActorEnterHitReaction(false, false, false, false, false, true, false));
    CHECK_FALSE(service.canActorEnterHitReaction(false, false, false, false, false, false, true));
}

TEST_CASE("shared actor AI leaves victim audio to resolved melee combat")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(0, 100);
    actor.world.active = true;
    actor.runtime.motionState = ActorAiMotionState::Attacking;
    actor.runtime.animationState = ActorAiAnimationState::AttackMelee;
    actor.runtime.actionSeconds = 0.001f;
    actor.runtime.attackCooldownSeconds = 1.0f;
    actor.stats.attack1Damage.bonus = 100;
    actor.target.currentKind = ActorAiTargetKind::Actor;
    actor.target.currentActorIndex = 1;
    actor.target.currentHp = 1;
    actor.target.currentPosition = {132, 200, 64};
    actor.target.currentDistance = 32;
    actor.target.currentEdgeDistance = 0;
    actor.target.currentCanSense = true;
    frame.activeActors = {actor};
    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);
    REQUIRE(result.actorUpdates.front().attackRequest);
    CHECK(result.actorUpdates.front().attackRequest->kind == OpenYAMM::Game::ActorAiAttackRequestKind::ActorMelee);
    CHECK(result.audioRequests.empty());
}

TEST_CASE("shared actor AI fidgets and vocalizes on decisions in active and background paths")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(0, 100);
    actor.runtime.yawRadians = std::atan2(-200.0f, -100.0f);
    actor.runtime.boredAnimationSeconds = 0.75f;
    uint32_t decision = 0;
    for (; decision < 10000; ++decision)
    {
        if (OpenYAMM::Game::actorChoosesBored(actor.actorId, decision)
            && OpenYAMM::Game::actorBoredSoundRoll(actor.actorId, decision))
        {
            break;
        }
    }
    REQUIRE(decision < 10000);
    actor.runtime.idleDecisionCount = decision;

    for (const bool active : {false, true})
    {
        actor.world.active = active;
        frame.activeActors = active ? std::vector<ActorAiFacts>{actor} : std::vector<ActorAiFacts>{};
        frame.backgroundActors = active ? std::vector<ActorAiFacts>{} : std::vector<ActorAiFacts>{actor};
        const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);
        REQUIRE_EQ(result.actorUpdates.size(), 1);
        CHECK(result.actorUpdates[0].animation.animationState == ActorAiAnimationState::Bored);
        CHECK(result.actorUpdates[0].state.actionSeconds == 0.75f);
        REQUIRE_EQ(result.audioRequests.size(), 1);
        CHECK(result.audioRequests[0].kind == OpenYAMM::Game::ActorAiAudioRequestKind::Bored);
        CHECK_EQ(result.audioRequests[0].position.z, actor.movement.position.z);

        ActorAiFacts continued = actor;
        continued.runtime.animationState = ActorAiAnimationState::Bored;
        continued.runtime.actionSeconds = 0.75f;
        continued.runtime.idleDecisionCount = decision + 1;
        if (active)
        {
            frame.activeActors = {continued};
        }
        else
        {
            frame.backgroundActors = {continued};
        }
        const OpenYAMM::Game::ActorAiFrameResult next = system.updateActors(frame);
        CHECK(next.audioRequests.empty());
        CHECK_FALSE(next.actorUpdates[0].state.idleDecisionCount);
        CHECK(next.actorUpdates[0].animation.animationState == ActorAiAnimationState::Bored);
    }

    actor.runtime.yawRadians += 3.14159265f;
    frame.activeActors.clear();
    frame.backgroundActors = {actor};
    const OpenYAMM::Game::ActorAiFrameResult backgroundTurn = system.updateActors(frame);
    REQUIRE_EQ(backgroundTurn.audioRequests.size(), 1);
    CHECK(backgroundTurn.actorUpdates[0].movementIntent.updateYaw);

    actor.world.active = true;
    actor.movement.distanceToParty = 1000;
    actor.movement.edgeDistanceToParty = 1000;
    frame.activeActors = {actor};
    frame.backgroundActors.clear();
    const OpenYAMM::Game::ActorAiFrameResult away = system.updateActors(frame);
    CHECK(away.audioRequests.empty());
    CHECK(away.actorUpdates[0].animation.animationState == ActorAiAnimationState::Standing);

    actor.status.spellEffects.paralyzeRemainingSeconds = 10.0f;
    frame.activeActors.clear();
    frame.backgroundActors = {actor};
    CHECK(system.updateActors(frame).audioRequests.empty());

    actor.status.spellEffects.paralyzeRemainingSeconds = 0.0f;
    actor.status.invisible = true;
    frame.backgroundActors = {actor};
    const OpenYAMM::Game::ActorAiFrameResult removed = system.updateActors(frame);
    CHECK(removed.audioRequests.empty());
    CHECK_FALSE(removed.actorUpdates[0].state.idleDecisionCount);
}

TEST_CASE("shared actor AI wander sound is independent and only rolls for new walks")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(0, 77);
    actor.world.active = true;
    actor.movement.distanceToParty = 1000;
    actor.movement.edgeDistanceToParty = 1000;
    actor.movement.movementAllowed = true;
    actor.movement.allowIdleWander = true;
    actor.movement.wanderRadius = 1024;
    actor.movement.homePosition = actor.movement.position;
    actor.movement.effectiveMoveSpeed = 200;
    bool found = false;
    for (uint32_t decision = 0; decision < 10000; ++decision)
    {
        actor.runtime.idleDecisionCount = decision;
        frame.activeActors = {actor};
        const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);
        if (result.actorUpdates[0].movementIntent.action != ActorAiMovementAction::Wander
            || result.audioRequests.empty())
        {
            continue;
        }
        found = true;
        CHECK(result.audioRequests[0].kind == OpenYAMM::Game::ActorAiAudioRequestKind::Bored);
        actor.runtime.motionState = ActorAiMotionState::Wandering;
        actor.runtime.animationState = ActorAiAnimationState::Walking;
        actor.runtime.actionSeconds = 1;
        actor.movement.moveDirectionX = result.actorUpdates[0].movementIntent.moveDirectionX;
        actor.movement.moveDirectionY = result.actorUpdates[0].movementIntent.moveDirectionY;
        frame.activeActors = {actor};
        CHECK(system.updateActors(frame).audioRequests.empty());
        break;
    }
    CHECK(found);
}

TEST_CASE("shared actor service permits forced hit reactions without reviving dead actors")
{
    GameplayActorService service;
    CHECK(service.canActorEnterHitReaction(false, false, false, false, false, false, true, true));
    CHECK(service.canActorEnterHitReaction(false, false, false, false, false, true, false, true));
    CHECK_FALSE(service.canActorEnterHitReaction(false, true, true, true, true, false, false, true));
}

TEST_CASE("actor fidget facing uses the requested yaw and a front octant")
{
    using OpenYAMM::Game::actorFidgetFacesListener;
    constexpr float pi = 3.14159265f;
    CHECK(actorFidgetFacesListener(0, 100, 0));
    CHECK(actorFidgetFacesListener(pi, -100, 0));
    CHECK_FALSE(actorFidgetFacesListener(0, -100, 0));
    CHECK(actorFidgetFacesListener(pi / 8 - 0.001f, 100, 0));
    CHECK_FALSE(actorFidgetFacesListener(pi / 8 + 0.001f, 100, 0));
    CHECK(actorFidgetFacesListener(-pi / 8 + 0.001f, 100, 0));
    CHECK_FALSE(actorFidgetFacesListener(-pi / 8 - 0.001f, 100, 0));
    CHECK(actorFidgetFacesListener(2 * pi, 100, 0));
}

TEST_CASE("shared actor AI special pursuit alone can vocalize on entry")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(0, 100);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 200;
    actor.movement.distanceToParty = 2048;
    actor.movement.edgeDistanceToParty = 2048;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {2148, 200, 0};
    actor.target.currentDistance = 2048;
    actor.target.currentEdgeDistance = 2048;
    actor.target.currentCanSense = true;
    actor.target.currentHasAttackLineOfSight = true;
    actor.target.partyCanSenseActor = true;
    uint32_t decision = 0;
    for (; decision < 10000; ++decision)
    {
        if (OpenYAMM::Game::actorVocalizationRoll(actor.actorId, decision, 0x281da370u) < 2u)
        {
            break;
        }
    }
    REQUIRE(decision < 10000);
    actor.runtime.pursueDecisionCount = decision;
    frame.activeActors = {actor};
    const OpenYAMM::Game::ActorAiFrameResult started = system.updateActors(frame);
    REQUIRE_EQ(started.audioRequests.size(), 1);
    CHECK(started.audioRequests.front().kind == OpenYAMM::Game::ActorAiAudioRequestKind::Hit);

    ActorAiFacts continuing = actor;
    continuing.runtime.motionState = ActorAiMotionState::Pursuing;
    continuing.runtime.actionSeconds = 1;
    continuing.movement.moveDirectionX = 1;
    frame.activeActors = {continuing};
    CHECK(system.updateActors(frame).audioRequests.empty());

    actor.movement.distanceToParty = 512;
    actor.movement.edgeDistanceToParty = 512;
    actor.target.currentDistance = 512;
    actor.target.currentEdgeDistance = 512;
    actor.target.currentPosition = {612, 200, 0};
    frame.activeActors = {actor};
    const OpenYAMM::Game::ActorAiFrameResult direct = system.updateActors(frame);
    CHECK(direct.actorUpdates.front().movementIntent.action == ActorAiMovementAction::Pursue);
    CHECK(direct.audioRequests.empty());
}
