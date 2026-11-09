#include "doctest/doctest.h"

#include "engine/TextTable.h"
#include "game/StringUtils.h"
#include "game/gameplay/GameplayActorAiSystem.h"
#include "game/gameplay/ActorVocalizationRules.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/MonsterSpellSupport.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/SpellTable.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <optional>
#include <set>
#include <sstream>
#include <string>
#include <unordered_map>
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

TEST_CASE("shared actor service makes a berserk monster and every other monster enemies")
{
    MonsterTable monsterTable = {};
    REQUIRE(monsterTable.loadStatsFromRows({makeActorServiceMonsterStatsRow(1), makeActorServiceMonsterStatsRow(2)}));

    GameplayActorService service = {};
    service.bindTables(&monsterTable, nullptr);

    OpenYAMM::Game::GameplayActorTargetPolicyState berserkActor = {};
    berserkActor.monsterId = 1;
    berserkActor.hostileToParty = true;
    berserkActor.controlMode = GameplayActorControlMode::Berserk;
    berserkActor.height = 128;

    OpenYAMM::Game::GameplayActorTargetPolicyState otherActor = {};
    otherActor.monsterId = 1;
    otherActor.hostileToParty = true;
    otherActor.height = 128;

    // Same kind, no faction feud: only the berserk spell makes them fight, both ways.
    const OpenYAMM::Game::GameplayActorTargetPolicyResult attack =
        service.resolveActorTargetPolicy(berserkActor, otherActor);
    CHECK(attack.canTarget);
    CHECK_EQ(attack.relationToTarget, 4);
    CHECK(attack.engagementRange > 0.0f);
    CHECK(service.resolveActorTargetPolicy(otherActor, berserkActor).canTarget);
    CHECK(service.partyEngagementRange(berserkActor) > 0.0f);

    // Without the spell they stay friends.
    berserkActor.controlMode = GameplayActorControlMode::None;
    CHECK_FALSE(service.resolveActorTargetPolicy(berserkActor, otherActor).canTarget);
}

TEST_CASE("shared actor service makes a monster fight back the monster that last hit it")
{
    MonsterTable monsterTable = {};
    REQUIRE(monsterTable.loadStatsFromRows({makeActorServiceMonsterStatsRow(1), makeActorServiceMonsterStatsRow(2)}));

    GameplayActorService service = {};
    service.bindTables(&monsterTable, nullptr);

    OpenYAMM::Game::GameplayActorTargetPolicyState victim = {};
    victim.monsterId = 1;
    victim.actorId = 0;
    victim.hostileToParty = true;
    victim.height = 128;

    OpenYAMM::Game::GameplayActorTargetPolicyState attacker = {};
    attacker.monsterId = 2;
    attacker.actorId = 7;
    attacker.hostileToParty = true;
    attacker.height = 128;

    // No faction feud: they ignore each other until one is hit.
    CHECK_FALSE(service.resolveActorTargetPolicy(victim, attacker).canTarget);

    victim.lastActorAttackerId = 7;
    const OpenYAMM::Game::GameplayActorTargetPolicyResult strikeBack =
        service.resolveActorTargetPolicy(victim, attacker);
    CHECK(strikeBack.canTarget);
    CHECK_EQ(strikeBack.relationToTarget, 4);

    // Only that attacker, and never one of its own group.
    OpenYAMM::Game::GameplayActorTargetPolicyState bystander = attacker;
    bystander.actorId = 8;
    CHECK_FALSE(service.resolveActorTargetPolicy(victim, bystander).canTarget);

    victim.group = 3;
    attacker.group = 3;
    CHECK_FALSE(service.resolveActorTargetPolicy(victim, attacker).canTarget);
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

TEST_CASE("shared actor AI closes in on a far party with only a missile")
{
    // A Great Wyrm: one missile attack, no blow to fall back on. Beyond the 5120 missile reach it used to shoot; the
    // party's hits reach no farther, so a hit never lets it shoot from beyond. A world's shorter party reach (MM9's
    // 4096) shortens its reach at the party too.
    const auto updateAt = [](float edgeDistance, float partyHitReach = 5120.0f)
    {
        GameplayActorAiSystem system;
        ActorAiFrameFacts frame = makeFrame();
        frame.partyHitReach = partyHitReach;
        ActorAiFacts actor = makeActor(12, 109);
        actor.world.active = true;
        actor.identity.hostilityType = 4;
        actor.status.hostileToParty = true;
        actor.status.hasDetectedParty = true;
        actor.stats.attackConstraints.attack1IsRanged = true;
        actor.runtime.rangedAttackAnimationSeconds = 0.5f;
        actor.movement.movementAllowed = true;
        actor.movement.effectiveMoveSpeed = 140.0f;
        actor.target.currentKind = ActorAiTargetKind::Party;
        actor.target.currentPosition = {edgeDistance + 132.0f, 200.0f, 64.0f};
        actor.target.currentDistance = edgeDistance + 32.0f;
        actor.target.currentEdgeDistance = edgeDistance;
        actor.target.currentCanSense = true;
        actor.target.currentHasAttackLineOfSight = true;
        actor.target.partyCanSenseActor = true;
        frame.activeActors.push_back(actor);
        const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);
        REQUIRE_EQ(result.actorUpdates.size(), 1u);
        REQUIRE(result.actorUpdates.front().state.motionState.has_value());
        return *result.actorUpdates.front().state.motionState;
    };

    CHECK(updateAt(7000.0f) == ActorAiMotionState::Pursuing);
    CHECK(updateAt(5200.0f) == ActorAiMotionState::Pursuing);
    CHECK(updateAt(4000.0f) == ActorAiMotionState::Attacking);
    CHECK(updateAt(4500.0f, 4096.0f) == ActorAiMotionState::Pursuing);
    CHECK(updateAt(4000.0f, 4096.0f) == ActorAiMotionState::Attacking);
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

TEST_CASE("shared actor AI applies an attack at its sprite contact frame and attacks until the action ends")
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
    actor.runtime.meleeAttackAnimationSeconds = 0.75f;
    actor.runtime.meleeAttackImpactSeconds = 0.5f;
    actor.runtime.attackCooldownSeconds = 0.5f;
    actor.runtime.queuedAttackAbility = GameplayActorAttackAbility::Attack1;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {132.0f, 200.0f, 64.0f};
    actor.target.currentDistance = 96.0f;
    actor.target.currentEdgeDistance = 0.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    const auto step = [&](float actionSeconds, bool impactTriggered)
    {
        frame.activeActors = {actor};
        frame.activeActors[0].runtime.actionSeconds = actionSeconds;
        frame.activeActors[0].runtime.attackImpactTriggered = impactTriggered;
        const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);
        REQUIRE_EQ(result.actorUpdates.size(), 1u);
        return result.actorUpdates.front();
    };

    // Before the contact frame (0.5 s into the 0.75 s action) nothing applies.
    const OpenYAMM::Game::ActorAiUpdate windup = step(0.3f, false);
    CHECK_FALSE(windup.attackRequest.has_value());
    CHECK_FALSE(windup.state.attackImpactTriggered.value_or(false));

    // At the contact frame the blow applies and the actor keeps attacking.
    const OpenYAMM::Game::ActorAiUpdate contact = step(0.25f + 1.0f / 256.0f, false);
    CHECK(contact.attackRequest.has_value());
    CHECK(contact.state.attackImpactTriggered.value_or(false));
    REQUIRE(contact.state.motionState.has_value());
    CHECK(*contact.state.motionState == ActorAiMotionState::Attacking);

    const OpenYAMM::Game::ActorAiUpdate afterContact = step(0.1f, true);
    CHECK_FALSE(afterContact.attackRequest.has_value());
    REQUIRE(afterContact.state.motionState.has_value());
    CHECK(*afterContact.state.motionState == ActorAiMotionState::Attacking);

    // The native action ends standing, without a second blow.
    const OpenYAMM::Game::ActorAiUpdate end = step(1.0f / 256.0f, true);
    CHECK_FALSE(end.attackRequest.has_value());
    REQUIRE(end.state.motionState.has_value());
    CHECK(*end.state.motionState == ActorAiMotionState::Standing);
}

TEST_CASE("attack timing: a sprite contact frame wins, else the clip's key; clip-timed models last their clip")
{
    using OpenYAMM::Game::ActorAttackTiming;
    using OpenYAMM::Game::resolveActorAttackTiming;
    // An MM6-MM8 sprite with an authored contact frame keeps it, whatever the model's key.
    ActorAttackTiming timing = resolveActorAttackTiming(0.75f, 0.5f, 0.8f, 0.4f, false);
    CHECK(timing.actionSeconds == doctest::Approx(0.75f));
    CHECK(timing.impactSeconds == doctest::Approx(0.5f));
    // Without one, the model's key applies the attack within the sprite's action (any world).
    timing = resolveActorAttackTiming(0.75f, 0.0f, 0.8f, 0.4f, false);
    CHECK(timing.actionSeconds == doctest::Approx(0.75f));
    CHECK(timing.impactSeconds == doctest::Approx(0.4f));
    // Neither: at the action's end, as MM8 does.
    timing = resolveActorAttackTiming(0.75f, 0.0f, 0.0f, -1.0f, false);
    CHECK(timing.actionSeconds == doctest::Approx(0.75f));
    CHECK(timing.impactSeconds == 0.0f);
    // A model whose clips time its attacks (MM9): the action is the clip and the key applies it, over a stand-in
    // sprite's contact frame; a key outside the clip applies it at the clip's end; an unknown clip length keeps the
    // sprite.
    timing = resolveActorAttackTiming(0.75f, 0.5f, 0.8f, 0.4f, true);
    CHECK(timing.actionSeconds == doctest::Approx(0.8f));
    CHECK(timing.impactSeconds == doctest::Approx(0.4f));
    timing = resolveActorAttackTiming(0.75f, 0.5f, 0.8f, 0.9f, true);
    CHECK(timing.actionSeconds == doctest::Approx(0.8f));
    CHECK(timing.impactSeconds == 0.0f);
    timing = resolveActorAttackTiming(0.75f, 0.5f, 0.0f, 0.4f, true);
    CHECK(timing.actionSeconds == doctest::Approx(0.75f));
    CHECK(timing.impactSeconds == doctest::Approx(0.5f));
}

TEST_CASE("shared actor AI casts a spell at its own clip's key where the world times spells apart")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(12, 109);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.aiType = GameplayActorAiType::Normal;
    actor.runtime.motionState = ActorAiMotionState::Attacking;
    actor.runtime.animationState = ActorAiAnimationState::AttackRanged;
    actor.runtime.rangedAttackAnimationSeconds = 0.5f;
    actor.runtime.spellAttackAnimationSeconds = 1.2f;
    actor.runtime.spellAttackImpactSeconds = 0.9f;
    actor.runtime.attackCooldownSeconds = 0.5f;
    actor.runtime.queuedAttackAbility = GameplayActorAttackAbility::Spell1;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {600.0f, 200.0f, 64.0f};
    actor.target.currentDistance = 500.0f;
    actor.target.currentEdgeDistance = 400.0f;
    actor.target.currentCanSense = true;
    actor.target.currentHasAttackLineOfSight = true;
    actor.target.partyCanSenseActor = true;
    const auto step = [&](float actionSeconds)
    {
        frame.activeActors = {actor};
        frame.activeActors[0].runtime.actionSeconds = actionSeconds;
        const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);
        REQUIRE_EQ(result.actorUpdates.size(), 1u);
        return result.actorUpdates.front();
    };

    // 0.4 s into the 1.2 s cast clip: the ranged attack's 0.5 s action would long be over, the cast key (0.9 s) is
    // not yet due.
    CHECK_FALSE(step(0.8f).state.attackImpactTriggered.value_or(false));
    // At the key it casts.
    CHECK(step(0.3f - 1.0f / 256.0f).state.attackImpactTriggered.value_or(false));
}

TEST_CASE("shared actor AI plays a delayed attack sound once the action clock passes the delay")
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
    actor.runtime.meleeAttackAnimationSeconds = 0.75f;
    actor.runtime.meleeAttackSoundDelaySeconds = 0.2f;
    actor.movement.movementAllowed = true;
    actor.movement.distanceToParty = 96.0f;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {132.0f, 200.0f, 64.0f};
    actor.target.currentDistance = 96.0f;
    actor.target.currentEdgeDistance = 0.0f;
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    const auto attackSounds = [](const OpenYAMM::Game::ActorAiFrameResult &result)
    {
        return std::count_if(result.audioRequests.begin(), result.audioRequests.end(), [](const auto &request)
        {
            return request.kind == OpenYAMM::Game::ActorAiAudioRequestKind::Attack;
        });
    };

    // Starting the attack does not play the delayed sound.
    frame.activeActors = {actor};
    const OpenYAMM::Game::ActorAiFrameResult start = system.updateActors(frame);
    REQUIRE_EQ(start.actorUpdates.size(), 1u);
    REQUIRE(start.actorUpdates[0].state.motionState.has_value());
    REQUIRE(*start.actorUpdates[0].state.motionState == ActorAiMotionState::Attacking);
    CHECK_EQ(attackSounds(start), 0);

    actor.runtime.motionState = ActorAiMotionState::Attacking;
    actor.runtime.animationState = ActorAiAnimationState::AttackMelee;
    actor.runtime.queuedAttackAbility = GameplayActorAttackAbility::Attack1;
    actor.runtime.attackCooldownSeconds = 1.0f;
    const auto step = [&](float actionSeconds)
    {
        frame.activeActors = {actor};
        frame.activeActors[0].runtime.actionSeconds = actionSeconds;
        return attackSounds(system.updateActors(frame));
    };
    // 0.2 s into the 0.75 s action the action clock reads 0.55 s.
    CHECK_EQ(step(0.6f), 0);
    CHECK_EQ(step(0.55f + 1.0f / 256.0f), 1);
    CHECK_EQ(step(0.5f), 0);
}

TEST_CASE("shared actor AI ages attack recovery at half speed while slowed")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(11, 108);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.status.spellEffects.slowRemainingSeconds = 10.0f;
    actor.status.spellEffects.slowRecoveryMultiplier = 2.0f;
    actor.stats.aiType = GameplayActorAiType::Normal;
    actor.stats.moveSpeed = 200;
    actor.stats.attack1Damage.diceRolls = 1;
    actor.stats.attack1Damage.diceSides = 4;
    actor.runtime.recoverySeconds = 2.0f;
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
    const float startCooldownSeconds = *attackUpdate.state.attackCooldownSeconds;

    // Slow is applied once, while the cooldown ages, not again when the attack starts.
    CHECK_GE(startCooldownSeconds, 2.0f * 0.9f);
    CHECK_LE(startCooldownSeconds, 2.0f * 1.2f);

    actor.runtime.motionState = OpenYAMM::Game::ActorAiMotionState::Attacking;
    actor.runtime.attackCooldownSeconds = startCooldownSeconds;
    actor.runtime.actionSeconds = attackUpdate.state.actionSeconds.value_or(1.0f);
    frame.activeActors = {actor};

    const OpenYAMM::Game::ActorAiFrameResult agingResult = system.updateActors(frame);

    REQUIRE_EQ(agingResult.actorUpdates.size(), 1u);
    REQUIRE(agingResult.actorUpdates.front().state.attackCooldownSeconds.has_value());
    CHECK_EQ(
        *agingResult.actorUpdates.front().state.attackCooldownSeconds,
        doctest::Approx(startCooldownSeconds - frame.fixedStepSeconds * 0.5f));
}


ActorAiFacts makeEngagedMeleeActor(float edgeDistanceToParty)
{
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

TEST_CASE("shared actor AI attacks in turn-based hold mode only with an action grant")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    frame.turnBased.mode = OpenYAMM::Game::ActorTurnBasedMode::Hold;
    frame.activeActors.push_back(makeEngagedMeleeActor(0.0f));

    const OpenYAMM::Game::ActorAiFrameResult heldResult = system.updateActors(frame);
    REQUIRE_EQ(heldResult.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &heldUpdate = heldResult.actorUpdates.front();
    CHECK_FALSE(heldUpdate.attackRequest.has_value());
    CHECK(heldUpdate.state.motionState.value_or(ActorAiMotionState::Standing) != ActorAiMotionState::Attacking);
    CHECK_FALSE(heldUpdate.movementIntent.applyMovement);

    frame.turnBased.actionGrantActorIndices = {11};
    const OpenYAMM::Game::ActorAiFrameResult grantedResult = system.updateActors(frame);
    REQUIRE_EQ(grantedResult.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &grantedUpdate = grantedResult.actorUpdates.front();
    REQUIRE(grantedUpdate.state.motionState.has_value());
    CHECK(*grantedUpdate.state.motionState == ActorAiMotionState::Attacking);
}

TEST_CASE("shared actor AI moves but never attacks in turn-based move-only mode")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    frame.turnBased.mode = OpenYAMM::Game::ActorTurnBasedMode::MoveOnly;
    frame.turnBased.actionGrantActorIndices = {};
    frame.activeActors.push_back(makeEngagedMeleeActor(0.0f));

    const OpenYAMM::Game::ActorAiFrameResult meleeResult = system.updateActors(frame);
    REQUIRE_EQ(meleeResult.actorUpdates.size(), 1u);
    CHECK(
        meleeResult.actorUpdates.front().state.motionState.value_or(ActorAiMotionState::Standing)
        != ActorAiMotionState::Attacking);

    frame.activeActors = {makeEngagedMeleeActor(600.0f)};
    const OpenYAMM::Game::ActorAiFrameResult pursuitResult = system.updateActors(frame);
    REQUIRE_EQ(pursuitResult.actorUpdates.size(), 1u);
    CHECK(pursuitResult.actorUpdates.front().movementIntent.applyMovement);

    frame.turnBased.mode = OpenYAMM::Game::ActorTurnBasedMode::Hold;
    const OpenYAMM::Game::ActorAiFrameResult heldResult = system.updateActors(frame);
    REQUIRE_EQ(heldResult.actorUpdates.size(), 1u);
    CHECK_FALSE(heldResult.actorUpdates.front().movementIntent.applyMovement);
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
    CHECK(update.movementIntent.moveSpeed == doctest::Approx(400.0f));
    CHECK_FALSE(update.movementIntent.inMeleeRange);
    CHECK_FALSE(update.attackRequest.has_value());
}

TEST_CASE("shared actor AI uses the pursuit speed multiplier and cap")
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

TEST_CASE("turn-based wait stage multiplies movement speed by 5/3 before the cap")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    frame.turnBased.mode = OpenYAMM::Game::ActorTurnBasedMode::MoveOnly;
    frame.turnBased.actionGrantActorIndices = {};
    ActorAiFacts actor = makeActor(25, 125);
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
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {600.0f, 200.0f, 64.0f};
    actor.target.currentDistance = 500.0f;
    actor.target.currentEdgeDistance = 500.0f;
    actor.target.currentCanSense = true;
    actor.target.currentHasAttackLineOfSight = false;
    actor.target.partyCanSenseActor = true;
    frame.activeActors.push_back(actor);

    const OpenYAMM::Game::ActorAiFrameResult waitResult = system.updateActors(frame);
    REQUIRE_EQ(waitResult.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &waitUpdate = waitResult.actorUpdates.front();
    REQUIRE(waitUpdate.state.motionState.has_value());
    CHECK(*waitUpdate.state.motionState == ActorAiMotionState::Pursuing);
    CHECK(waitUpdate.movementIntent.applyMovement);
    CHECK(waitUpdate.movementIntent.moveSpeed == doctest::Approx(200.0f * 2.0f * 5.0f / 3.0f));

    frame.turnBased.mode = OpenYAMM::Game::ActorTurnBasedMode::RealTime;
    const OpenYAMM::Game::ActorAiFrameResult realTimeResult = system.updateActors(frame);
    REQUIRE_EQ(realTimeResult.actorUpdates.size(), 1u);
    CHECK(realTimeResult.actorUpdates.front().movementIntent.moveSpeed == doctest::Approx(400.0f));

    frame.turnBased.mode = OpenYAMM::Game::ActorTurnBasedMode::MoveOnly;
    frame.activeActors.front().stats.moveSpeed = 700;
    frame.activeActors.front().movement.effectiveMoveSpeed = 700.0f;
    const OpenYAMM::Game::ActorAiFrameResult cappedResult = system.updateActors(frame);
    REQUIRE_EQ(cappedResult.actorUpdates.size(), 1u);
    CHECK(cappedResult.actorUpdates.front().movementIntent.moveSpeed == doctest::Approx(1000.0f));

    frame.turnBased.mode = OpenYAMM::Game::ActorTurnBasedMode::Hold;
    const OpenYAMM::Game::ActorAiFrameResult heldResult = system.updateActors(frame);
    REQUIRE_EQ(heldResult.actorUpdates.size(), 1u);
    CHECK_FALSE(heldResult.actorUpdates.front().movementIntent.applyMovement);
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

TEST_CASE("shared actor AI gives a monster's Stone Skin its armour power")
{
    // The table's "Stone Skin" arrives lowercased with its space (parseMonsterSpellName); it gave +0 AC before.
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    ActorAiFacts actor = makeActor(15, 112);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.hasSpell1 = true;
    actor.stats.spell1Id = 38;
    actor.stats.spell1Name = "stone skin";
    actor.stats.spell1SkillLevel = 5;
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
    CHECK(update.state.spellEffects->stoneskinRemainingSeconds > 0.0f);
    CHECK_EQ(update.state.spellEffects->stoneskinPower, 10);
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
    CHECK(std::abs(update.movementIntent.desiredMoveX) < 0.05f);
}

TEST_CASE("shared actor AI keeps its ranged orbit side on a fresh pursuit decision")
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
    CHECK(secondUpdate.movementIntent.desiredMoveY * firstUpdate.movementIntent.desiredMoveY > 0.0f);
    CHECK(secondUpdate.movementIntent.moveDirectionY * firstUpdate.movementIntent.moveDirectionY > 0.0f);
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

TEST_CASE("shared actor AI continues fleeing with the original flee speed multiplier")
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
    CHECK(update.movementIntent.moveSpeed == doctest::Approx(360.0f));
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

TEST_CASE("shared actor AI holds the animation clock during a hit's hitstop")
{
    GameplayActorAiSystem system;

    for (const bool hitstopActive : {false, true})
    {
        CAPTURE(hitstopActive);
        ActorAiFrameFacts frame = makeFrame();
        ActorAiFacts actor = makeActor(5, 102);
        actor.stats.currentHp = 0;
        actor.runtime.motionState = ActorAiMotionState::Dying;
        actor.runtime.animationState = ActorAiAnimationState::Dying;
        actor.runtime.actionSeconds = 1.0f;
        actor.runtime.animationTimeTicks = 10.0f;
        actor.runtime.hitstopActive = hitstopActive;
        frame.activeActors.push_back(actor);

        const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);

        REQUIRE_EQ(result.actorUpdates.size(), 1u);
        const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates.front();
        REQUIRE(update.animation.animationTimeTicks.has_value());
        REQUIRE(update.state.actionSeconds.has_value());
        CHECK(*update.state.actionSeconds < 1.0f);

        if (hitstopActive)
        {
            CHECK(*update.animation.animationTimeTicks == doctest::Approx(10.0f));
        }
        else
        {
            CHECK(*update.animation.animationTimeTicks > 10.0f);
        }
    }
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

namespace
{
using OpenYAMM::Game::ActorTacticsFacts;

constexpr float TacticDegrees = 3.14159265358979323846f / 180.0f;

// A hostile ranged actor at the origin engaging the party, for the tactics tests (ActorTacticsFacts).
ActorAiFacts makeTacticRangedActor(float targetX, float targetY, float edgeDistance)
{
    ActorAiFacts actor = makeActor(20, 120);
    actor.world.active = true;
    actor.identity.hostilityType = 4;
    actor.status.hostileToParty = true;
    actor.status.hasDetectedParty = true;
    actor.stats.aiType = GameplayActorAiType::Normal;
    actor.stats.attackConstraints.attack1IsRanged = true;
    actor.stats.attackConstraints.rangedCommitAllowed = true;
    actor.runtime.rangedAttackAnimationSeconds = 0.5f;
    actor.runtime.meleeAttackAnimationSeconds = 0.5f;
    actor.runtime.recoverySeconds = 1.0f;
    actor.movement.position = {0.0f, 0.0f, 0.0f};
    actor.movement.homePosition = actor.movement.position;
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 250.0f;
    actor.movement.wanderRadius = 2560.0f;
    actor.movement.allowIdleWander = true;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {targetX, targetY, 64.0f};
    actor.target.currentDistance = std::hypot(targetX, targetY);
    actor.target.currentEdgeDistance = edgeDistance;
    actor.target.currentCanSense = true;
    actor.target.currentHasAttackLineOfSight = true;
    actor.target.partyCanSenseActor = true;
    return actor;
}

ActorAiFacts makeTacticTurret(float targetX, float targetY)
{
    ActorAiFacts actor = makeTacticRangedActor(targetX, targetY, std::hypot(targetX, targetY) - 60.0f);
    actor.movement.movementAllowed = false;
    actor.movement.effectiveMoveSpeed = 0.0f;
    actor.movement.wanderRadius = 0.0f;
    actor.tactics.traverseRadiansPerSecond = 90.0f * TacticDegrees;
    actor.tactics.fireToleranceRadians = 5.0f * TacticDegrees;
    return actor;
}

OpenYAMM::Game::ActorAiUpdate updateOne(const ActorAiFacts &actor)
{
    ActorAiFrameFacts frame = makeFrame();
    frame.activeActors.push_back(actor);
    const OpenYAMM::Game::ActorAiFrameResult result = GameplayActorAiSystem().updateActors(frame);
    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    return result.actorUpdates.front();
}
}

TEST_CASE("actor tactics leave a stationary ranged actor's native snap-and-fire unchanged by default")
{
    ActorAiFacts actor = makeTacticTurret(0.0f, 1500.0f);
    actor.tactics = {};
    const OpenYAMM::Game::ActorAiUpdate update = updateOne(actor);

    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Attacking);
    REQUIRE(update.movementIntent.updateYaw);
    CHECK(update.movementIntent.yawRadians == doctest::Approx(std::atan2(1500.0f, 0.0f)));
}

TEST_CASE("actor tactics turn a turret at its traverse rate and fire only once it is on target")
{
    ActorAiFacts actor = makeTacticTurret(0.0f, 1500.0f);
    const OpenYAMM::Game::ActorAiUpdate turning = updateOne(actor);

    CHECK_FALSE(turning.attackRequest.has_value());
    REQUIRE(turning.state.motionState.has_value());
    CHECK(*turning.state.motionState == ActorAiMotionState::Standing);
    REQUIRE(turning.movementIntent.updateYaw);
    CHECK(turning.movementIntent.yawRadians == doctest::Approx(90.0f * TacticDegrees / 128.0f));
    CHECK_FALSE(turning.movementIntent.applyMovement);

    actor.runtime.yawRadians = 87.0f * TacticDegrees;
    const OpenYAMM::Game::ActorAiUpdate firing = updateOne(actor);
    REQUIRE(firing.state.motionState.has_value());
    CHECK(*firing.state.motionState == ActorAiMotionState::Attacking);
    REQUIRE(firing.animation.animationState.has_value());
    CHECK(*firing.animation.animationState == ActorAiAnimationState::AttackRanged);
}

TEST_CASE("actor tactics keep a turret tracking its target between shots and through the windup")
{
    ActorAiFacts actor = makeTacticTurret(-1500.0f, 0.0f);
    actor.runtime.attackCooldownSeconds = 1.0f;
    actor.runtime.yawRadians = 2.5f;
    const OpenYAMM::Game::ActorAiUpdate waiting = updateOne(actor);

    REQUIRE(waiting.state.motionState.has_value());
    CHECK(*waiting.state.motionState == ActorAiMotionState::Standing);
    REQUIRE(waiting.movementIntent.updateYaw);
    CHECK(waiting.movementIntent.yawRadians == doctest::Approx(2.5f + 90.0f * TacticDegrees / 128.0f));

    actor.runtime.motionState = ActorAiMotionState::Attacking;
    actor.runtime.animationState = ActorAiAnimationState::AttackRanged;
    actor.runtime.actionSeconds = 0.4f;
    actor.runtime.yawRadians = 3.1f;
    const OpenYAMM::Game::ActorAiUpdate windup = updateOne(actor);
    REQUIRE(windup.movementIntent.updateYaw);
    CHECK(windup.movementIntent.yawRadians > 3.1f);
    CHECK(windup.movementIntent.yawRadians < 3.1f + 0.02f);
}

TEST_CASE("actor tactics hold a post: walk home, face the placement, never wander")
{
    ActorAiFacts actor = makeTacticRangedActor(0.0f, 0.0f, 0.0f);
    actor.target = {};
    actor.status.hostileToParty = false;
    actor.status.hasDetectedParty = false;
    actor.tactics.holdPost = true;
    actor.movement.hasHomeYaw = true;
    actor.movement.homeYawRadians = 1.0f;
    actor.movement.homePosition = {600.0f, 0.0f, 0.0f};
    actor.movement.distanceToParty = 5000.0f;
    const OpenYAMM::Game::ActorAiUpdate returning = updateOne(actor);

    REQUIRE(returning.state.motionState.has_value());
    CHECK(*returning.state.motionState == ActorAiMotionState::Wandering);
    CHECK(returning.movementIntent.applyMovement);
    CHECK(returning.movementIntent.desiredMoveX == doctest::Approx(1.0f));
    CHECK(returning.movementIntent.yawRadians == doctest::Approx(0.0f));

    actor.movement.position = actor.movement.homePosition;
    actor.runtime.motionState = ActorAiMotionState::Wandering;
    const OpenYAMM::Game::ActorAiUpdate facing = updateOne(actor);
    REQUIRE(facing.state.motionState.has_value());
    CHECK(*facing.state.motionState == ActorAiMotionState::Standing);
    REQUIRE(facing.movementIntent.updateYaw);
    CHECK(facing.movementIntent.yawRadians == doctest::Approx(1.0f));
    CHECK_FALSE(facing.movementIntent.applyMovement);

    // At its post and facing the right way, every idle decision stands (the native AI would wander 75 % of them).
    actor.runtime.motionState = ActorAiMotionState::Standing;
    actor.runtime.yawRadians = 1.0f;
    for (uint32_t decision = 0; decision < 16; ++decision)
    {
        actor.runtime.idleDecisionCount = decision;
        const OpenYAMM::Game::ActorAiUpdate idle = updateOne(actor);
        REQUIRE(idle.state.motionState.has_value());
        CHECK(*idle.state.motionState == ActorAiMotionState::Standing);
        CHECK_FALSE(idle.movementIntent.applyMovement);
    }
}

TEST_CASE("actor tactics keep a distant post facing its placement instead of the party")
{
    ActorAiFacts actor = makeTacticRangedActor(0.0f, 0.0f, 0.0f);
    actor.target = {};
    actor.world.active = false;
    actor.world.listenerPosition = {0.0f, 3000.0f, 0.0f};
    actor.movement.hasHomeYaw = true;
    actor.movement.homeYawRadians = -2.0f;
    ActorAiFrameFacts frame = makeFrame();
    frame.backgroundActors.push_back(actor);
    const OpenYAMM::Game::ActorAiFrameResult native = GameplayActorAiSystem().updateActors(frame);
    REQUIRE_EQ(native.actorUpdates.size(), 1u);
    CHECK(native.actorUpdates[0].movementIntent.yawRadians == doctest::Approx(std::atan2(3000.0f, 0.0f)));

    frame.backgroundActors[0].tactics.holdPost = true;
    const OpenYAMM::Game::ActorAiFrameResult post = GameplayActorAiSystem().updateActors(frame);
    REQUIRE_EQ(post.actorUpdates.size(), 1u);
    CHECK(post.actorUpdates[0].movementIntent.yawRadians == doctest::Approx(-2.0f));
}

TEST_CASE("actor tactics ranged band always shoots a non-adjacent target instead of closing to melee")
{
    // 400 units: the native roll mostly walks in to melee here.
    size_t nativeRanged = 0;
    for (uint32_t decision = 0; decision < 32; ++decision)
    {
        ActorAiFacts actor = makeTacticRangedActor(460.0f, 0.0f, 400.0f);
        actor.stats.attack2Chance = 25;
        actor.runtime.attackDecisionCount = decision;
        const OpenYAMM::Game::ActorAiUpdate native = updateOne(actor);
        nativeRanged += native.animation.animationState == ActorAiAnimationState::AttackRanged ? 1 : 0;

        actor.tactics.rangedMinDistance = 768.0f;
        actor.tactics.rangedMaxDistance = 2304.0f;
        const OpenYAMM::Game::ActorAiUpdate band = updateOne(actor);
        REQUIRE(band.state.motionState.has_value());
        CHECK(*band.state.motionState == ActorAiMotionState::Attacking);
        REQUIRE(band.animation.animationState.has_value());
        CHECK(*band.animation.animationState == ActorAiAnimationState::AttackRanged);
    }
    CHECK(nativeRanged < 32);
}

TEST_CASE("actor tactics ranged band uses melee only against an adjacent target on its melee roll")
{
    ActorAiFacts actor = makeTacticRangedActor(150.0f, 0.0f, 90.0f);
    actor.tactics.rangedMinDistance = 768.0f;
    actor.tactics.rangedMaxDistance = 2304.0f;
    actor.stats.attack2Chance = 100;
    const OpenYAMM::Game::ActorAiUpdate melee = updateOne(actor);
    REQUIRE(melee.animation.animationState.has_value());
    CHECK(*melee.animation.animationState == ActorAiAnimationState::AttackMelee);

    actor.stats.attack2Chance = 0;
    const OpenYAMM::Game::ActorAiUpdate shot = updateOne(actor);
    REQUIRE(shot.animation.animationState.has_value());
    CHECK(*shot.animation.animationState == ActorAiAnimationState::AttackRanged);
}

TEST_CASE("actor tactics ranged band backs off, closes in and circles between shots")
{
    ActorAiFacts actor = makeTacticRangedActor(500.0f, 0.0f, 440.0f);
    actor.tactics.rangedMinDistance = 768.0f;
    actor.tactics.rangedMaxDistance = 2304.0f;
    actor.runtime.attackCooldownSeconds = 1.0f;
    const OpenYAMM::Game::ActorAiUpdate backOff = updateOne(actor);
    REQUIRE(backOff.state.motionState.has_value());
    CHECK(*backOff.state.motionState == ActorAiMotionState::Pursuing);
    CHECK(backOff.movementIntent.moveSpeed == doctest::Approx(250.0f));
    CHECK(backOff.movementIntent.applyMovement);
    CHECK(backOff.movementIntent.desiredMoveX == doctest::Approx(-1.0f));
    REQUIRE(backOff.movementIntent.updateYaw);
    CHECK(backOff.movementIntent.yawRadians == doctest::Approx(0.0f));
    CHECK(backOff.movementIntent.keepYawWhileMoving);

    actor = makeTacticRangedActor(3000.0f, 0.0f, 2940.0f);
    actor.tactics.rangedMinDistance = 768.0f;
    actor.tactics.rangedMaxDistance = 2304.0f;
    actor.runtime.attackCooldownSeconds = 1.0f;
    const OpenYAMM::Game::ActorAiUpdate closeIn = updateOne(actor);
    REQUIRE(closeIn.state.motionState.has_value());
    CHECK(*closeIn.state.motionState == ActorAiMotionState::Pursuing);
    CHECK(closeIn.movementIntent.desiredMoveX == doctest::Approx(1.0f));

    actor = makeTacticRangedActor(1500.0f, 0.0f, 1440.0f);
    actor.tactics.rangedMinDistance = 768.0f;
    actor.tactics.rangedMaxDistance = 2304.0f;
    actor.runtime.attackCooldownSeconds = 1.0f;
    const OpenYAMM::Game::ActorAiUpdate circle = updateOne(actor);
    REQUIRE(circle.state.motionState.has_value());
    CHECK(*circle.state.motionState == ActorAiMotionState::Pursuing);
    CHECK(std::abs(circle.movementIntent.desiredMoveY) > 0.9f);
}

TEST_CASE("actor tactics leash a post: it stops moving away from home but keeps facing the target")
{
    ActorAiFacts actor = makeTacticRangedActor(4000.0f, 0.0f, 3940.0f);
    actor.tactics.rangedMinDistance = 768.0f;
    actor.tactics.rangedMaxDistance = 2304.0f;
    actor.tactics.holdPost = true;
    actor.tactics.postLeashRadius = 500.0f;
    actor.movement.homePosition = {-600.0f, 0.0f, 0.0f};
    actor.runtime.attackCooldownSeconds = 1.0f;
    const OpenYAMM::Game::ActorAiUpdate held = updateOne(actor);

    REQUIRE(held.state.motionState.has_value());
    CHECK(*held.state.motionState == ActorAiMotionState::Standing);
    CHECK_FALSE(held.movementIntent.applyMovement);
    REQUIRE(held.movementIntent.updateYaw);
    CHECK(held.movementIntent.yawRadians == doctest::Approx(0.0f));

    // Within the leash it closes in as usual.
    actor.movement.homePosition = {-100.0f, 0.0f, 0.0f};
    const OpenYAMM::Game::ActorAiUpdate free = updateOne(actor);
    REQUIRE(free.state.motionState.has_value());
    CHECK(*free.state.motionState == ActorAiMotionState::Pursuing);
    CHECK(free.movementIntent.applyMovement);
}

TEST_CASE("actor tactics ease a traverse onto its target instead of stopping dead")
{
    ActorAiFacts actor = makeTacticTurret(0.0f, 1500.0f);
    actor.runtime.attackCooldownSeconds = 1.0f;
    actor.runtime.yawRadians = std::atan2(1500.0f, 0.0f) - 2.0f * TacticDegrees;
    const OpenYAMM::Game::ActorAiUpdate settling = updateOne(actor);

    REQUIRE(settling.movementIntent.updateYaw);
    const float step = settling.movementIntent.yawRadians - actor.runtime.yawRadians;
    CHECK(step > 0.0f);
    CHECK(step < 0.5f * 90.0f * TacticDegrees / 128.0f);
}

TEST_CASE("actor tactics aim a turret ahead of its target by the lead, shot included")
{
    // Without the lead the turret is 5.7 degrees off its target and turns; with it, it is on the led point and fires.
    ActorAiFacts actor = makeTacticTurret(0.0f, 1500.0f);
    actor.runtime.yawRadians = std::atan2(1500.0f, 150.0f);
    const OpenYAMM::Game::ActorAiUpdate unled = updateOne(actor);
    REQUIRE(unled.state.motionState.has_value());
    CHECK(*unled.state.motionState == ActorAiMotionState::Standing);

    actor.tactics.aimLead = {150.0f, 0.0f, 10.0f};
    const OpenYAMM::Game::ActorAiUpdate led = updateOne(actor);
    REQUIRE(led.state.motionState.has_value());
    CHECK(*led.state.motionState == ActorAiMotionState::Attacking);

    // The release aims at the led point too.
    actor.runtime.motionState = ActorAiMotionState::Attacking;
    actor.runtime.animationState = ActorAiAnimationState::AttackRanged;
    actor.runtime.queuedAttackAbility = GameplayActorAttackAbility::Attack1;
    actor.runtime.actionSeconds = 0.001f;
    actor.runtime.attackCooldownSeconds = 1.0f;
    const OpenYAMM::Game::ActorAiUpdate release = updateOne(actor);
    REQUIRE(release.attackRequest.has_value());
    CHECK(release.attackRequest->target.x == doctest::Approx(150.0f));
    CHECK(release.attackRequest->target.y == doctest::Approx(1500.0f));
    CHECK(release.attackRequest->target.z == doctest::Approx(74.0f));
}

TEST_CASE("actor tactics turn an idle post turret to its scan facing, standing without fidgets")
{
    ActorAiFacts actor = makeTacticTurret(0.0f, 0.0f);
    actor.target = {};
    actor.status.hostileToParty = false;
    actor.status.hasDetectedParty = false;
    actor.tactics.holdPost = true;
    actor.movement.hasHomeYaw = true;
    actor.movement.homeYawRadians = 1.0f;
    actor.movement.distanceToParty = 5000.0f;
    actor.runtime.yawRadians = 1.0f;
    actor.tactics.idleAimActive = true;
    actor.tactics.idleAimYawRadians = 1.3f;

    for (uint32_t decision = 0; decision < 16; ++decision)
    {
        actor.runtime.idleDecisionCount = decision;
        const OpenYAMM::Game::ActorAiUpdate idle = updateOne(actor);
        REQUIRE(idle.state.motionState.has_value());
        CHECK(*idle.state.motionState == ActorAiMotionState::Standing);
        REQUIRE(idle.animation.animationState.has_value());
        CHECK(*idle.animation.animationState == ActorAiAnimationState::Standing);
        CHECK_FALSE(idle.movementIntent.applyMovement);
        REQUIRE(idle.movementIntent.updateYaw);
        CHECK(idle.movementIntent.yawRadians > 1.0f);
        CHECK(idle.movementIntent.yawRadians <= 1.0f + 90.0f * TacticDegrees / 128.0f + 1.0e-5f);
    }

    // A background turret scans too, instead of facing its placement.
    actor.world.active = false;
    actor.world.listenerPosition = {0.0f, 3000.0f, 0.0f};
    ActorAiFrameFacts frame = makeFrame();
    frame.backgroundActors.push_back(actor);
    const OpenYAMM::Game::ActorAiFrameResult background = GameplayActorAiSystem().updateActors(frame);
    REQUIRE_EQ(background.actorUpdates.size(), 1u);
    REQUIRE(background.actorUpdates[0].movementIntent.updateYaw);
    CHECK(background.actorUpdates[0].movementIntent.yawRadians > 1.0f);

    // Without the scan the post keeps its native stand at the placement facing.
    actor.world.active = true;
    actor.tactics.idleAimActive = false;
    const OpenYAMM::Game::ActorAiUpdate native = updateOne(actor);
    CHECK((!native.movementIntent.updateYaw || native.movementIntent.yawRadians == doctest::Approx(1.0f)));
}

TEST_CASE("actor tactics keep a friendly scanning turret tracking a target it senses but does not fight yet")
{
    // A friendly turret (hostility type 0) senses a hostile actor beyond its promotion range: no fight yet, but its
    // facing follows the target at the traverse rate instead of its scan.
    ActorAiFacts actor = makeTacticTurret(0.0f, 0.0f);
    actor.status.hostileToParty = false;
    actor.status.hasDetectedParty = false;
    actor.identity.hostilityType = 0;
    actor.tactics.holdPost = true;
    actor.tactics.scan.radiansPerSecond = 0.2f;
    actor.tactics.scan.halfWidthRadians = 0.8f;
    actor.tactics.idleAimActive = false;
    actor.movement.hasHomeYaw = true;
    actor.movement.homeYawRadians = 0.0f;
    actor.movement.distanceToParty = 5000.0f;
    actor.runtime.yawRadians = 0.0f;
    actor.target.currentKind = ActorAiTargetKind::Actor;
    actor.target.currentActorIndex = 4;
    actor.target.currentPosition = {0.0f, 2400.0f, 300.0f};
    actor.target.currentDistance = 2400.0f;
    actor.target.currentEdgeDistance = 2300.0f;
    actor.target.currentRelationToTarget = 2;     // promoted only within the close range (1 024)
    actor.target.partyCanSenseActor = false;
    const OpenYAMM::Game::ActorAiUpdate update = updateOne(actor);

    CHECK_FALSE(update.attackRequest.has_value());
    REQUIRE(update.state.motionState.has_value());
    CHECK(*update.state.motionState == ActorAiMotionState::Standing);
    REQUIRE(update.movementIntent.updateYaw);
    CHECK(update.movementIntent.yawRadians == doctest::Approx(90.0f * TacticDegrees / 128.0f));

    // Without the scan the same post does not engage and keeps its placement facing (the native result).
    actor.tactics.scan = {};
    const OpenYAMM::Game::ActorAiUpdate native = updateOne(actor);
    CHECK((!native.movementIntent.updateYaw || native.movementIntent.yawRadians == doctest::Approx(0.0f)));
}

TEST_CASE("relation overrides replace the faction relation, and a turned actor fights its own faction")
{
    OpenYAMM::Game::GameplayActorService service;
    OpenYAMM::Game::GameplayActorTargetPolicyState kreegan = {};
    kreegan.monsterId = 10010;
    kreegan.hostileToParty = true;
    OpenYAMM::Game::GameplayActorTargetPolicyState turret = kreegan;
    turret.monsterId = 10102;

    CHECK_FALSE(service.resolveActorTargetPolicy(kreegan, turret).canTarget);

    std::unordered_map<uint32_t, int32_t> overrides;
    overrides[OpenYAMM::Game::GameplayActorService::relationOverrideKey(10010, 10102)] = 3;
    const OpenYAMM::Game::GameplayActorTargetPolicyResult overridden =
        service.resolveActorTargetPolicy(kreegan, turret, &overrides);
    CHECK(overridden.canTarget);
    CHECK_EQ(overridden.relationToTarget, 3);
    CHECK(overridden.engagementRange > 0.0f);

    // A turned turret (evt.TurnActor: enslaved for good) targets the Kreegan.
    turret.controlMode = OpenYAMM::Game::GameplayActorControlMode::Enslaved;
    turret.hostileToParty = false;
    CHECK(service.resolveActorTargetPolicy(turret, kreegan).canTarget);
}

TEST_CASE("a relation row may name an actor group, which wins over its monsters' rows")
{
    using OpenYAMM::Game::GameplayActorService;
    GameplayActorService service;
    OpenYAMM::Game::GameplayActorTargetPolicyState barracksGuard = {};
    barracksGuard.monsterId = 9111;
    barracksGuard.group = 4;
    OpenYAMM::Game::GameplayActorTargetPolicyState kitchenGuard = barracksGuard;
    kitchenGuard.group = 3;
    OpenYAMM::Game::GameplayActorTargetPolicyState nagate = {};
    nagate.monsterId = 9081;
    nagate.hostileToParty = true;

    // Drangheim Prison: only group 4 (GuardToNegate.scr's AddEnemy Nagate) and the Nagate are enemies; the guards'
    // own monster rows say peace.
    std::unordered_map<uint32_t, int32_t> overrides;
    overrides[GameplayActorService::relationOverrideKey(9111, 9081)] = 0;
    overrides[GameplayActorService::relationOverrideKey(9081, 9111)] = 0;
    overrides[GameplayActorService::relationOverrideKey(GameplayActorService::relationGroupSide(4), 9081)] = 2;
    overrides[GameplayActorService::relationOverrideKey(9081, GameplayActorService::relationGroupSide(4))] = 2;

    CHECK(service.resolveActorTargetPolicy(barracksGuard, nagate, &overrides).canTarget);
    CHECK(service.resolveActorTargetPolicy(nagate, barracksGuard, &overrides).canTarget);
    CHECK_FALSE(service.resolveActorTargetPolicy(kitchenGuard, nagate, &overrides).canTarget);
    CHECK_FALSE(service.resolveActorTargetPolicy(nagate, kitchenGuard, &overrides).canTarget);
}

namespace
{
// A hostile melee skirmisher (ActorTacticsFacts::skirmish) fighting the party, which stands targetDistance away along
// +x (edge distance targetDistance - 64).
ActorAiFacts makeSkirmisher(float targetDistance)
{
    ActorAiFacts actor = makeActor(21, 131);
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
    actor.runtime.queuedAttackAbility = GameplayActorAttackAbility::Attack1;
    actor.movement.movementAllowed = true;
    actor.movement.effectiveMoveSpeed = 200.0f;
    actor.movement.distanceToParty = targetDistance;
    actor.movement.edgeDistanceToParty = std::max(0.0f, targetDistance - 64.0f);
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentPosition = {100.0f + targetDistance, 200.0f, 64.0f};
    actor.target.currentDistance = targetDistance;
    actor.target.currentEdgeDistance = std::max(0.0f, targetDistance - 64.0f);
    actor.target.currentCanSense = true;
    actor.target.partyCanSenseActor = true;
    actor.tactics.skirmish = true;
    actor.tactics.strafeAttackChance = 0.0f;
    actor.tactics.evadeChance = 0.0f;
    return actor;
}

OpenYAMM::Game::ActorAiUpdate updateSkirmisher(const ActorAiFacts &actor, ActorAiFrameFacts frame = makeFrame())
{
    GameplayActorAiSystem system;
    frame.activeActors = {actor};
    const OpenYAMM::Game::ActorAiFrameResult result = system.updateActors(frame);
    REQUIRE_EQ(result.actorUpdates.size(), 1u);
    return result.actorUpdates.front();
}
}

TEST_CASE("a skirmisher follows a target that steps away while it strikes; a native actor stands")
{
    ActorAiFacts actor = makeSkirmisher(344.0f);
    actor.runtime.motionState = ActorAiMotionState::Attacking;
    actor.runtime.animationState = ActorAiAnimationState::AttackMelee;
    actor.runtime.actionSeconds = 0.5f;
    actor.runtime.attackCooldownSeconds = 1.0f;

    // Beyond 0.9 of its reach before the blow lands, it lunges 1.25x faster than it runs.
    const OpenYAMM::Game::ActorAiUpdate chase = updateSkirmisher(actor);
    REQUIRE(chase.state.motionState.has_value());
    CHECK(*chase.state.motionState == ActorAiMotionState::Attacking);
    CHECK(chase.movementIntent.applyMovement);
    CHECK(chase.movementIntent.desiredMoveX == doctest::Approx(1.0f));
    CHECK(chase.movementIntent.moveSpeed == doctest::Approx(500.0f));
    CHECK(chase.movementIntent.keepYawWhileMoving);
    CHECK_FALSE(chase.attackRequest.has_value());

    // Within half its melee range it stands and swings at a standing target.
    ActorAiFacts close = makeSkirmisher(96.0f);
    close.runtime = actor.runtime;
    close.movement.moveDirectionX = 1.0f;
    CHECK_FALSE(updateSkirmisher(close).movementIntent.applyMovement);

    // A moving target it runs after until within a quarter of its reach, keeping 0.95x the pace of one moving away.
    ActorAiFacts following = makeSkirmisher(184.0f);
    following.runtime = actor.runtime;
    ActorAiFrameFacts fleeing = makeFrame();
    fleeing.party.velocityX = 300.0f;
    const OpenYAMM::Game::ActorAiUpdate pace = updateSkirmisher(following, fleeing);
    CHECK(pace.movementIntent.applyMovement);
    CHECK(pace.movementIntent.moveSpeed == doctest::Approx(285.0f));
    CHECK_FALSE(updateSkirmisher(following).movementIntent.applyMovement);

    ActorAiFacts native = actor;
    native.tactics.skirmish = false;
    CHECK_FALSE(updateSkirmisher(native).movementIntent.applyMovement);

    // Turn-based combat keeps the native stance.
    ActorAiFrameFacts turnBased = makeFrame();
    turnBased.turnBased.mode = OpenYAMM::Game::ActorTurnBasedMode::MoveOnly;
    CHECK_FALSE(updateSkirmisher(actor, turnBased).movementIntent.applyMovement);
}

TEST_CASE("a skirmisher arriving at a still target may run a strafe attack past it")
{
    ActorAiFacts actor = makeSkirmisher(96.0f);
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.animationState = ActorAiAnimationState::Walking;
    actor.runtime.actionSeconds = 0.2f;
    actor.movement.moveDirectionX = 1.0f;
    actor.tactics.strafeAttackChance = 1.0f;

    const OpenYAMM::Game::ActorAiUpdate start = updateSkirmisher(actor);
    REQUIRE(start.state.motionState.has_value());
    CHECK(*start.state.motionState == ActorAiMotionState::Attacking);
    REQUIRE(start.state.skirmishPhase.has_value());
    CHECK(*start.state.skirmishPhase == OpenYAMM::Game::ActorSkirmishPhase::StrafeAttack);
    CHECK(start.movementIntent.applyMovement);
    // 45 degrees off the line to the target, at half its running speed until the blow lands.
    CHECK(start.movementIntent.desiredMoveX == doctest::Approx(std::sqrt(0.5f)));
    CHECK(std::abs(start.movementIntent.desiredMoveY) == doctest::Approx(std::sqrt(0.5f)));
    CHECK(start.movementIntent.moveSpeed == doctest::Approx(200.0f));
    CHECK(start.movementIntent.yawRadians == doctest::Approx(0.0f));

    // A moving target gets a plain strike.
    ActorAiFrameFacts moving = makeFrame();
    moving.party.velocityY = 200.0f;
    const OpenYAMM::Game::ActorAiUpdate plain = updateSkirmisher(actor, moving);
    CHECK(*plain.state.motionState == ActorAiMotionState::Attacking);
    CHECK(plain.state.skirmishPhase.value_or(OpenYAMM::Game::ActorSkirmishPhase::None)
        == OpenYAMM::Game::ActorSkirmishPhase::None);

    // Standing when the attack began, it strikes from where it stands.
    ActorAiFacts standing = actor;
    standing.runtime.motionState = ActorAiMotionState::Standing;
    standing.movement.moveDirectionX = 0.0f;
    const OpenYAMM::Game::ActorAiUpdate still = updateSkirmisher(standing);
    CHECK(*still.state.motionState == ActorAiMotionState::Attacking);
    CHECK_FALSE(still.movementIntent.applyMovement);
}

TEST_CASE("a skirmisher evades after a strike and does not strike again while evading")
{
    ActorAiFacts actor = makeSkirmisher(96.0f);
    actor.runtime.motionState = ActorAiMotionState::Attacking;
    actor.runtime.animationState = ActorAiAnimationState::AttackMelee;
    actor.runtime.actionSeconds = 1.0f / 256.0f;
    actor.runtime.attackCooldownSeconds = 0.5f;
    actor.runtime.attackImpactTriggered = true;
    actor.tactics.evadeChance = 1.0f;

    const OpenYAMM::Game::ActorAiUpdate done = updateSkirmisher(actor);
    REQUIRE(done.state.motionState.has_value());
    CHECK(*done.state.motionState == ActorAiMotionState::Pursuing);
    REQUIRE(done.state.skirmishPhase.has_value());
    CHECK(*done.state.skirmishPhase == OpenYAMM::Game::ActorSkirmishPhase::Evade);
    CHECK(done.state.skirmishSeconds.value_or(0.0f) == doctest::Approx(2.0f));
    // It backpedals away from the target (5-35 degrees off straight back) while facing it.
    CHECK(done.movementIntent.applyMovement);
    CHECK(done.movementIntent.desiredMoveX < -0.8f);
    CHECK(done.movementIntent.yawRadians == doctest::Approx(0.0f));
    CHECK(done.movementIntent.keepYawWhileMoving);
    CHECK(done.movementIntent.moveSpeed == doctest::Approx(200.0f));

    // In melee range with its attack ready it keeps evading instead of striking.
    ActorAiFacts evading = actor;
    evading.runtime.motionState = ActorAiMotionState::Pursuing;
    evading.runtime.animationState = ActorAiAnimationState::Walking;
    evading.runtime.attackCooldownSeconds = 0.0f;
    evading.runtime.attackImpactTriggered = false;
    evading.runtime.actionSeconds = 0.5f;
    evading.runtime.skirmishPhase = OpenYAMM::Game::ActorSkirmishPhase::Evade;
    evading.runtime.skirmishSeconds = 1.5f;
    evading.movement.moveDirectionX = done.movementIntent.desiredMoveX;
    evading.movement.moveDirectionY = done.movementIntent.desiredMoveY;
    const OpenYAMM::Game::ActorAiUpdate step = updateSkirmisher(evading);
    CHECK(*step.state.motionState == ActorAiMotionState::Pursuing);
    CHECK(step.movementIntent.applyMovement);
    CHECK(step.movementIntent.desiredMoveX == doctest::Approx(evading.movement.moveDirectionX));

    // The step past the backpedal half turns it to circle the target, 65 degrees off the line to it.
    evading.runtime.skirmishSeconds = 1.0f + 1.0f / 256.0f;
    const OpenYAMM::Game::ActorAiUpdate circle = updateSkirmisher(evading);
    CHECK(circle.movementIntent.desiredMoveX == doctest::Approx(std::cos(65.0f * 3.14159265f / 180.0f)).epsilon(0.01));

    // Once over, it fights as usual: in range with the attack ready, it strikes.
    evading.runtime.skirmishSeconds = 0.0f;
    const OpenYAMM::Game::ActorAiUpdate over = updateSkirmisher(evading);
    CHECK(*over.state.motionState == ActorAiMotionState::Attacking);

    // Without the evade roll a plain strike ends standing.
    ActorAiFacts plain = actor;
    plain.tactics.evadeChance = 0.0f;
    CHECK(*updateSkirmisher(plain).state.motionState == ActorAiMotionState::Standing);

    // From a target moving away it only circles, 65 degrees off the line to it.
    ActorAiFrameFacts away = makeFrame();
    away.party.velocityX = 300.0f;
    const OpenYAMM::Game::ActorAiUpdate circling = updateSkirmisher(actor, away);
    CHECK(*circling.state.skirmishPhase == OpenYAMM::Game::ActorSkirmishPhase::Circle);
    CHECK(circling.movementIntent.desiredMoveX
        == doctest::Approx(std::cos(65.0f * 3.14159265f / 180.0f)).epsilon(0.01));
}

TEST_CASE("a skirmisher holds off its chase until its attack will be ready as it arrives")
{
    ActorAiFacts actor = makeSkirmisher(864.0f);

    // It arrives within its 307 reach: the 493 units beyond it take 1.2 s at 400 a second. With 1.5 s of recovery
    // left it waits; with 1 s it runs.
    actor.runtime.attackCooldownSeconds = 1.5f;
    const OpenYAMM::Game::ActorAiUpdate hold = updateSkirmisher(actor);
    CHECK(*hold.state.motionState == ActorAiMotionState::Standing);
    CHECK_FALSE(hold.movementIntent.applyMovement);

    actor.runtime.attackCooldownSeconds = 1.0f;
    const OpenYAMM::Game::ActorAiUpdate go = updateSkirmisher(actor);
    CHECK(*go.state.motionState == ActorAiMotionState::Pursuing);
    CHECK(go.movementIntent.applyMovement);
}

TEST_CASE("a skirmisher taunts when it first notices the party and after a back-off, holding still meanwhile")
{
    ActorAiFacts actor = makeSkirmisher(96.0f);
    actor.status.hasDetectedParty = false;
    actor.tactics.tauntChance = 1.0f;
    actor.tactics.tauntSeconds = 1.4f;

    const OpenYAMM::Game::ActorAiUpdate aware = updateSkirmisher(actor);
    REQUIRE(aware.state.skirmishPhase.has_value());
    CHECK(*aware.state.skirmishPhase == OpenYAMM::Game::ActorSkirmishPhase::Taunt);
    CHECK(aware.state.skirmishSeconds.value_or(0.0f) == doctest::Approx(1.4f));
    CHECK(*aware.state.motionState == ActorAiMotionState::Standing);

    // A taunt under way holds even with the target in reach and the attack ready.
    actor.status.hasDetectedParty = true;
    actor.runtime.skirmishPhase = OpenYAMM::Game::ActorSkirmishPhase::Taunt;
    actor.runtime.skirmishSeconds = 0.7f;
    const OpenYAMM::Game::ActorAiUpdate holding = updateSkirmisher(actor);
    CHECK(*holding.state.motionState == ActorAiMotionState::Standing);
    CHECK_FALSE(holding.movementIntent.applyMovement);

    // Over, it strikes.
    actor.runtime.skirmishSeconds = 0.0f;
    CHECK(*updateSkirmisher(actor).state.motionState == ActorAiMotionState::Attacking);

    // A back-off that runs out ends in a taunt.
    actor.runtime.motionState = ActorAiMotionState::Pursuing;
    actor.runtime.skirmishPhase = OpenYAMM::Game::ActorSkirmishPhase::BackOff;
    actor.runtime.skirmishSeconds = 1.0f / 256.0f;
    actor.movement.moveDirectionX = -1.0f;
    const OpenYAMM::Game::ActorAiUpdate afterBackOff = updateSkirmisher(actor);
    CHECK(*afterBackOff.state.skirmishPhase == OpenYAMM::Game::ActorSkirmishPhase::Taunt);
    CHECK(*afterBackOff.state.motionState == ActorAiMotionState::Standing);

    // A model without a taunt never taunts.
    actor.tactics.tauntSeconds = 0.0f;
    actor.status.hasDetectedParty = false;
    actor.runtime = makeSkirmisher(96.0f).runtime;
    CHECK(*updateSkirmisher(actor).state.motionState == ActorAiMotionState::Attacking);
}

TEST_CASE("an evt.MoveActorTo walk takes an actor to its point instead of its own fight, also from a post")
{
    GameplayActorAiSystem system;
    ActorAiFrameFacts frame = makeFrame();
    // Adjacent to the party, hostile: by itself it attacks.
    ActorAiFacts actor = makeEngagedMeleeActor(0.0f);
    frame.activeActors = {actor};
    const OpenYAMM::Game::ActorAiFrameResult fighting = system.updateActors(frame);
    REQUIRE_EQ(fighting.actorUpdates.size(), 1u);
    CHECK(fighting.actorUpdates.front().state.motionState.value_or(ActorAiMotionState::Standing)
        == ActorAiMotionState::Attacking);

    // The walk: no attack, the path planner's pursuit of the point at its walking speed, even placed immobile.
    actor.movement.movementAllowed = false;
    actor.movement.scriptedMoveTarget = OpenYAMM::Game::GameplayWorldPoint{900.0f, 200.0f, 0.0f};
    frame.activeActors = {actor};
    const OpenYAMM::Game::ActorAiFrameResult walking = system.updateActors(frame);
    REQUIRE_EQ(walking.actorUpdates.size(), 1u);
    const OpenYAMM::Game::ActorAiUpdate &walk = walking.actorUpdates.front();
    CHECK_FALSE(walk.attackRequest.has_value());
    CHECK(walk.state.motionState == ActorAiMotionState::Wandering);
    CHECK(walk.movementIntent.action == ActorAiMovementAction::Pursue);
    CHECK(walk.movementIntent.applyMovement);
    CHECK(walk.movementIntent.meleePursuitActive);
    CHECK_EQ(walk.movementIntent.targetPosition.x, doctest::Approx(900.0f));
    CHECK_EQ(walk.movementIntent.moveSpeed, doctest::Approx(200.0f));
    CHECK_EQ(walk.movementIntent.moveDirectionX, doctest::Approx(1.0f));
    REQUIRE(walk.state.decision.has_value());
    CHECK(walk.state.decision->kind == OpenYAMM::Game::ActorAiDecisionKind::Patrol);

    // A run goes at its pursuit speed.
    actor.movement.scriptedMoveRun = true;
    frame.activeActors = {actor};
    const OpenYAMM::Game::ActorAiUpdate run = system.updateActors(frame).actorUpdates.front();
    CHECK(run.state.motionState == ActorAiMotionState::Pursuing);
    CHECK(run.movementIntent.moveSpeed > walk.movementIntent.moveSpeed);

    // Turn-based play holding every actor holds the walker too.
    frame.turnBased.mode = OpenYAMM::Game::ActorTurnBasedMode::Hold;
    frame.activeActors = {actor};
    CHECK_FALSE(system.updateActors(frame).actorUpdates.front().movementIntent.applyMovement);
}
