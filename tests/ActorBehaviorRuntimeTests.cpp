#include "doctest/doctest.h"

#include "game/gameplay/ActorBehaviorCatalog.h"
#include "game/gameplay/ActorBehaviorRuntime.h"
#include "game/gameplay/GameplayActorAiSystem.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/maps/SaveGame.h"
#include "game/tables/SpellTable.h"

#include "engine/AssetFileSystem.h"
#include "engine/TextTable.h"

#include <algorithm>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

using OpenYAMM::Game::ActorAiAnimationState;
using OpenYAMM::Game::ActorAiFacts;
using OpenYAMM::Game::ActorAiFrameFacts;
using OpenYAMM::Game::ActorAiFrameResult;
using OpenYAMM::Game::ActorAiMovementAction;
using OpenYAMM::Game::ActorAiMotionState;
using OpenYAMM::Game::ActorAiTargetKind;
using OpenYAMM::Game::ActorBehaviorActorFacts;
using OpenYAMM::Game::ActorBehaviorCatalog;
using OpenYAMM::Game::ActorBehaviorFrameFacts;
using OpenYAMM::Game::ActorBehaviorFrameResult;
using OpenYAMM::Game::ActorBehaviorRuntime;
using OpenYAMM::Game::ActorProjectileRequest;
using OpenYAMM::Game::GameplayActorAiSystem;
using OpenYAMM::Game::GameplayActorAiType;
using OpenYAMM::Game::GameplayActorAttackAbility;
using OpenYAMM::Game::GameplayProjectileService;
using OpenYAMM::Game::GameplayRuntimeActorState;
using OpenYAMM::Game::SkillMastery;

namespace
{
constexpr float Step = 1.0f / 128.0f;

std::string readSourceFile(const std::string &relativePath)
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / relativePath);
    std::ostringstream contents;
    contents << input.rdbuf();
    return contents.str();
}

OpenYAMM::Game::SpellTable loadSpellTable()
{
    const std::optional<OpenYAMM::Engine::TextTable> table =
        OpenYAMM::Engine::TextTable::parseTabSeparated(readSourceFile("assets_dev/engine/data_tables/spells.txt"));
    std::vector<std::vector<std::string>> rows;

    for (size_t rowIndex = 0; table && rowIndex < table->getRowCount(); ++rowIndex)
    {
        rows.push_back(table->getRow(rowIndex));
    }

    OpenYAMM::Game::SpellTable spellTable;
    spellTable.loadFromRows(rows);
    return spellTable;
}

ActorBehaviorCatalog makeCatalog(const std::string &behaviorSource, int16_t monsterId = 307)
{
    ActorBehaviorCatalog catalog;
    catalog.setLibrary("engine/behaviors/behavior.lua", readSourceFile("assets_dev/engine/behaviors/behavior.lua"));
    catalog.addBehavior("test/boss", "test/boss.lua", behaviorSource);
    catalog.setMonsterDefault(monsterId, "test/boss");
    return catalog;
}

ActorBehaviorActorFacts makeActor(int hp, int maxHp = 100)
{
    ActorBehaviorActorFacts actor = {};
    actor.actorIndex = 0;
    actor.actorId = 41;
    actor.monsterId = 307;
    actor.currentHp = hp;
    actor.maxHp = maxHp;
    actor.hostileToParty = true;
    actor.position = {1000.0f, 0.0f, 0.0f};
    actor.height = 200.0f;
    return actor;
}

ActorBehaviorFrameFacts makeFrame(const ActorBehaviorActorFacts &actor, float deltaSeconds = Step)
{
    ActorBehaviorFrameFacts facts = {};
    facts.deltaSeconds = deltaSeconds;
    facts.actorCount = 1;
    facts.actors.push_back(actor);
    return facts;
}

ActorAiFacts makeAiActor()
{
    ActorAiFacts actor = {};
    actor.actorIndex = 0;
    actor.actorId = 41;
    actor.identity.actorId = 41;
    actor.stats.currentHp = 100;
    actor.stats.maxHp = 100;
    actor.stats.radius = 32;
    actor.stats.height = 128;
    actor.runtime.motionState = ActorAiMotionState::Standing;
    actor.runtime.animationState = ActorAiAnimationState::Standing;
    actor.movement.position = {100.0f, 0.0f, 0.0f};
    return actor;
}

bool hasMessage(const ActorBehaviorFrameResult &result, const std::string &message)
{
    return std::find(result.statusMessages.begin(), result.statusMessages.end(), message)
        != result.statusMessages.end();
}

GameplayProjectileService::ProjectileWardFacts makeWard(float radius)
{
    GameplayProjectileService::ProjectileWardFacts ward = {};
    ward.ownerActorIndex = 0;
    ward.ownerActorId = 41;
    ward.center = {0.0f, 0.0f, 0.0f};
    ward.radius = radius;
    ward.wardId = "shadow";
    return ward;
}
}

TEST_CASE("actor behaviour attaches by monster id and runs onStart once")
{
    const ActorBehaviorCatalog catalog = makeCatalog(R"(
        return Behavior.define{
            onStart = function(self, s)
                s.starts = (s.starts or 0) + 1
                self:say("start " .. s.starts .. " hp " .. self:hp())
            end,
        }
    )");
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);

    const ActorBehaviorFrameResult first = runtime.update(makeFrame(makeActor(100)));
    CHECK(hasMessage(first, "start 1 hp 100"));
    REQUIRE(runtime.instance(0) != nullptr);
    CHECK(runtime.instance(0)->behaviorId == "test/boss");

    const ActorBehaviorFrameResult second = runtime.update(makeFrame(makeActor(100)));
    CHECK(second.statusMessages.empty());
}

TEST_CASE("actor behaviour ignores monsters without a default behaviour")
{
    const ActorBehaviorCatalog catalog = makeCatalog("return Behavior.define{}", 308);
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);
    runtime.update(makeFrame(makeActor(100)));
    CHECK(runtime.instance(0) == nullptr);
}

TEST_CASE("actor behaviour fires health thresholds once, highest first")
{
    const ActorBehaviorCatalog catalog = makeCatalog(R"(
        return Behavior.define{
            onDamaged = function(self, s, amount)
                self:say("damaged " .. amount)
            end,
            onHealthBelow = {
                [0.6] = function(self, s) s.order = (s.order or "") .. "60;" self:say(s.order) end,
                [0.3] = function(self, s) s.order = (s.order or "") .. "30;" self:say(s.order) end,
            },
        }
    )");
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);
    runtime.update(makeFrame(makeActor(100)));

    const ActorBehaviorFrameResult hit = runtime.update(makeFrame(makeActor(20)));
    CHECK(hasMessage(hit, "damaged 80"));
    CHECK(hasMessage(hit, "60;"));
    CHECK(hasMessage(hit, "60;30;"));

    const ActorBehaviorFrameResult again = runtime.update(makeFrame(makeActor(10)));
    CHECK(hasMessage(again, "damaged 10"));
    CHECK(again.statusMessages.size() == 1);
}

TEST_CASE("actor behaviour perform holds the native AI with its fallback animation")
{
    const ActorBehaviorCatalog catalog = makeCatalog(R"(
        return Behavior.define{
            onStart = function(self, s)
                self:perform{clip = "cast_ward", seconds = 0.5, fallback = "attack_ranged", sound = "17shield03"}
            end,
            onPerformDone = function(self, s, clip) self:say("done " .. clip) end,
        }
    )");
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);

    ActorBehaviorActorFacts busy = makeActor(100);
    busy.animationState = ActorAiAnimationState::AttackMelee;
    const ActorBehaviorFrameResult started = runtime.update(makeFrame(busy));
    REQUIRE(started.sounds.size() == 1);
    CHECK(started.sounds[0].soundName == "17shield03");
    REQUIRE(runtime.instance(0)->perform.has_value());
    CHECK_FALSE(runtime.instance(0)->perform->started);

    runtime.update(makeFrame(makeActor(100)));
    CHECK(runtime.instance(0)->perform->started);

    ActorAiFrameFacts aiFacts = {};
    aiFacts.deltaSeconds = Step;
    aiFacts.fixedStepSeconds = Step;
    aiFacts.activeActors.push_back(makeAiActor());
    runtime.applyAiFacts(aiFacts);
    CHECK(aiFacts.activeActors[0].behavior.holdActive);
    CHECK(aiFacts.activeActors[0].behavior.holdRestartAnimation);
    CHECK(aiFacts.activeActors[0].behavior.holdAnimation == ActorAiAnimationState::AttackRanged);

    GameplayRuntimeActorState presentation = {};
    presentation.actorId = 41;
    runtime.applyPresentation(0, presentation);
    CHECK(presentation.scriptedClip == "cast_ward");

    const ActorBehaviorFrameResult finished = runtime.update(makeFrame(makeActor(100), 0.6f));
    CHECK(hasMessage(finished, "done cast_ward"));
    CHECK_FALSE(runtime.instance(0)->perform.has_value());
}

TEST_CASE("actor AI holds still for a scripted action")
{
    ActorAiFrameFacts frame = {};
    frame.deltaSeconds = Step;
    frame.fixedStepSeconds = Step;
    ActorAiFacts actor = makeAiActor();
    actor.world.active = true;
    actor.status.hostileToParty = true;
    actor.target.currentKind = ActorAiTargetKind::Party;
    actor.target.currentCanSense = true;
    actor.target.currentPosition = {100.0f, 500.0f, 0.0f};
    actor.behavior.holdActive = true;
    actor.behavior.holdRestartAnimation = true;
    actor.behavior.holdAnimation = ActorAiAnimationState::AttackRanged;
    frame.activeActors.push_back(actor);

    const GameplayActorAiSystem aiSystem = {};
    const ActorAiFrameResult result = aiSystem.updateActors(frame);
    REQUIRE(result.actorUpdates.size() == 1);
    const OpenYAMM::Game::ActorAiUpdate &update = result.actorUpdates[0];
    CHECK(update.state.motionState == ActorAiMotionState::Standing);
    CHECK(update.animation.animationState == ActorAiAnimationState::AttackRanged);
    CHECK(update.animation.animationTimeTicks == doctest::Approx(0.0f));
    CHECK(update.movementIntent.action == ActorAiMovementAction::Stand);
    CHECK_FALSE(update.attackRequest.has_value());
    CHECK(update.movementIntent.updateYaw);
}

TEST_CASE("actor behaviour wards feed projectile facts and report blocks")
{
    const ActorBehaviorCatalog catalog = makeCatalog(R"(
        return Behavior.define{
            onStart = function(self, s)
                self:addWard{id = "shadow", radius = 400, seconds = 1, effect = "openyamm:fx/shadow_ward",
                    effectInterval = 0.25}
            end,
            onWardBlocked = function(self, s, id) self:say("blocked " .. id) end,
            onWardExpired = function(self, s, id) self:say("expired " .. id) end,
        }
    )");
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);
    const ActorBehaviorFrameResult started = runtime.update(makeFrame(makeActor(100)));
    CHECK(started.effects.size() == 1);
    REQUIRE(runtime.projectileWards().size() == 1);
    CHECK(runtime.projectileWards()[0].radius == doctest::Approx(400.0f));
    CHECK(runtime.projectileWards()[0].center.z == doctest::Approx(100.0f));

    GameplayProjectileService::ProjectileWardBlock block = {};
    block.ownerActorIndex = 0;
    block.ownerActorId = 41;
    block.wardId = "shadow";
    runtime.recordWardBlock(block);
    CHECK(hasMessage(runtime.update(makeFrame(makeActor(100))), "blocked shadow"));

    const ActorBehaviorFrameResult expired = runtime.update(makeFrame(makeActor(100), 1.0f));
    CHECK(hasMessage(expired, "expired shadow"));
    CHECK(runtime.projectileWards().empty());
}

TEST_CASE("projectile wards stop projectiles entering from outside only")
{
    std::vector<GameplayProjectileService::ProjectileWardFacts> wards = {makeWard(400.0f)};
    GameplayProjectileService::ProjectileState projectile = {};
    projectile.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Party;

    GameplayProjectileService::ProjectileMotionSegment inbound = {};
    inbound.startX = -600.0f;
    inbound.endX = -200.0f;
    const auto block = GameplayProjectileService::findProjectileWardBlock(projectile, inbound, wards, 1.0f);
    REQUIRE(block.has_value());
    CHECK(block->point.x == doctest::Approx(-400.0f));
    CHECK(block->wardId == "shadow");

    // A collision with something outside the ward comes first.
    CHECK_FALSE(GameplayProjectileService::findProjectileWardBlock(projectile, inbound, wards, 0.25f).has_value());

    GameplayProjectileService::ProjectileMotionSegment inside = {};
    inside.startX = -100.0f;
    inside.endX = -900.0f;
    CHECK_FALSE(GameplayProjectileService::findProjectileWardBlock(projectile, inside, wards, 1.0f).has_value());

    GameplayProjectileService::ProjectileMotionSegment miss = {};
    miss.startX = -600.0f;
    miss.startY = 500.0f;
    miss.endX = 600.0f;
    miss.endY = 500.0f;
    CHECK_FALSE(GameplayProjectileService::findProjectileWardBlock(projectile, miss, wards, 1.0f).has_value());

    projectile.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Actor;
    projectile.sourceId = 41;
    CHECK_FALSE(GameplayProjectileService::findProjectileWardBlock(projectile, inbound, wards, 1.0f).has_value());
}

TEST_CASE("actor behaviour spells, AI type and flee overrides adjust AI facts")
{
    const ActorBehaviorCatalog catalog = makeCatalog(R"(
        return Behavior.define{
            onStart = function(self, s)
                self:setSpell{spell = 15, skill = 8, mastery = "master", chance = 40}
                self:castNext{spell = 90, skill = 10, mastery = "grandmaster"}
                self:setAiType("aggressive")
                self:setNoFlee(true)
            end,
        }
    )");
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);
    runtime.update(makeFrame(makeActor(100)));

    ActorAiFrameFacts aiFacts = {};
    aiFacts.activeActors.push_back(makeAiActor());
    runtime.applyAiFacts(aiFacts);
    const ActorAiFacts &forced = aiFacts.activeActors[0];
    CHECK(forced.stats.hasSpell1);
    CHECK(forced.stats.spell1Id == 90);
    CHECK(forced.stats.spell1SkillLevel == 10);
    CHECK(forced.stats.spell1SkillMastery == SkillMastery::Grandmaster);
    CHECK(forced.stats.spell1UseChance == 100);
    CHECK(forced.stats.aiType == GameplayActorAiType::Aggressive);
    CHECK(forced.status.suppressLowHealthFlee);

    ActorAiFrameResult aiResult = {};
    ActorProjectileRequest request = {};
    request.sourceActorIndex = 0;
    request.ability = GameplayActorAttackAbility::Spell1;
    aiResult.projectileRequests.push_back(request);
    runtime.observeAiResult(aiResult);

    ActorAiFrameFacts nextFacts = {};
    nextFacts.activeActors.push_back(makeAiActor());
    runtime.applyAiFacts(nextFacts);
    CHECK(nextFacts.activeActors[0].stats.spell1Id == 15);
    CHECK(nextFacts.activeActors[0].stats.spell1UseChance == 40);
    CHECK(nextFacts.activeActors[0].stats.spell1SkillMastery == SkillMastery::Master);
}

TEST_CASE("actor behaviour state, timers and thresholds survive a snapshot")
{
    const ActorBehaviorCatalog catalog = makeCatalog(R"(
        return Behavior.define{
            onStart = function(self, s)
                s.phase = 1
                s.nested = {list = {3, 2, 1}, name = "mage", ratio = 0.5, flag = true}
                self:startTimer("again", 2)
            end,
            onHealthBelow = {[0.5] = function(self, s) s.phase = 2 end},
            onLoad = function(self, s)
                self:say("load " .. s.phase .. " " .. s.nested.name .. " " .. s.nested.list[1] .. " "
                    .. tostring(s.nested.flag) .. " " .. s.nested.ratio)
            end,
            onTimer = {again = function(self, s) self:say("timer " .. s.phase) end},
        }
    )");
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);
    runtime.update(makeFrame(makeActor(100)));
    runtime.update(makeFrame(makeActor(40)));
    const ActorBehaviorRuntime::Snapshot snapshot = runtime.snapshot();
    REQUIRE(snapshot.instances.size() == 1);
    CHECK(snapshot.instances[0].timers.size() == 1);
    CHECK(snapshot.instances[0].firedHealthThresholds.size() == 1);

    ActorBehaviorRuntime restored;
    restored.bind(&catalog, nullptr);
    restored.restoreSnapshot(snapshot);
    const ActorBehaviorFrameResult loaded = restored.update(makeFrame(makeActor(40)));
    CHECK(hasMessage(loaded, "load 2 mage 3 true 0.5"));

    // The fired 0.5 threshold does not fire again, and the saved timer still runs.
    const ActorBehaviorFrameResult timer = restored.update(makeFrame(makeActor(30), 2.0f));
    CHECK(hasMessage(timer, "timer 2"));
}

TEST_CASE("actor behaviour death clears directives and runs onDeath once")
{
    const ActorBehaviorCatalog catalog = makeCatalog(R"(
        return Behavior.define{
            onStart = function(self, s) self:addWard{id = "w", radius = 100} end,
            onDeath = function(self, s) self:say("dead") end,
        }
    )");
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);
    runtime.update(makeFrame(makeActor(100)));
    CHECK(runtime.projectileWards().size() == 1);

    ActorBehaviorActorFacts dead = makeActor(0);
    dead.dead = true;
    CHECK(hasMessage(runtime.update(makeFrame(dead)), "dead"));
    CHECK(runtime.projectileWards().empty());
    CHECK(runtime.update(makeFrame(dead)).statusMessages.empty());
}

TEST_CASE("actor behaviour sandbox and script errors stop only that script")
{
    const ActorBehaviorCatalog catalog = makeCatalog(R"(
        return Behavior.define{
            onStart = function(self, s)
                self:say("random " .. tostring(math.random) .. " load " .. tostring(load) .. " io " .. tostring(io))
                local value = self:random(1, 6)
                self:say(value >= 1 and value <= 6 and "dice ok" or "dice bad")
                s.fn = function() end
            end,
            onThink = function(self, s) self:say("think") end,
        }
    )");
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);
    const ActorBehaviorFrameResult result = runtime.update(makeFrame(makeActor(100)));
    CHECK(hasMessage(result, "random nil load nil io nil"));
    CHECK(hasMessage(result, "dice ok"));
    // Storing a function in the saved state is an error: the behaviour stops, the actor keeps its native AI.
    CHECK(runtime.update(makeFrame(makeActor(100), 1.0f)).statusMessages.empty());
}

TEST_CASE("Behavior.define rejects misspelt handlers")
{
    const ActorBehaviorCatalog catalog = makeCatalog(R"(
        return Behavior.define{onStrat = function(self, s) self:say("never") end}
    )");
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);
    CHECK(runtime.update(makeFrame(makeActor(100))).statusMessages.empty());
}

TEST_CASE("boss mage behaviour raises its ward at 60 percent health")
{
    ActorBehaviorCatalog catalog;
    catalog.setLibrary("engine/behaviors/behavior.lua", readSourceFile("assets_dev/engine/behaviors/behavior.lua"));
    catalog.addBehavior("bosses/necro_mage", "engine/behaviors/bosses/necro_mage.lua",
        readSourceFile("assets_dev/engine/behaviors/bosses/necro_mage.lua"));
    catalog.setMonsterDefault(307, "bosses/necro_mage");
    const OpenYAMM::Game::SpellTable spellTable = loadSpellTable();
    REQUIRE(spellTable.findByName("Shrapmetal") != nullptr);
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, &spellTable);

    runtime.update(makeFrame(makeActor(137, 137)));
    REQUIRE(runtime.instance(0) != nullptr);
    CHECK(runtime.instance(0)->suppressFlee);
    CHECK(runtime.projectileWards().empty());

    const ActorBehaviorFrameResult phase2 = runtime.update(makeFrame(makeActor(80, 137)));
    CHECK(runtime.projectileWards().size() == 1);
    CHECK(runtime.instance(0)->perform.has_value());
    CHECK(runtime.instance(0)->spellOverride.has_value());
    CHECK_FALSE(phase2.statusMessages.empty());

    const ActorBehaviorFrameResult phase3 = runtime.update(makeFrame(makeActor(30, 137)));
    CHECK(phase3.summons.size() == 2);
    CHECK(runtime.instance(0)->nextCast.has_value());
}

TEST_CASE("actor behaviour snapshots round-trip through save files")
{
    OpenYAMM::Game::ActorBehaviorInstanceState instance = {};
    instance.actorIndex = 12;
    instance.actorId = 77;
    instance.behaviorId = "bosses/necro_mage";
    instance.started = true;
    instance.lastHp = 80;
    instance.ageSeconds = 14.5f;
    instance.randomState = 123456789u;
    instance.scriptState = {6, 0, 0, 0, 0};
    instance.firedHealthThresholds = {0.6f};
    instance.timers.push_back({"ward_return", 3.5f});
    OpenYAMM::Game::ActorBehaviorWard ward = {};
    ward.id = "shadow";
    ward.radius = 400.0f;
    ward.remainingSeconds = 12.0f;
    ward.effectId = "openyamm:fx/shadow_ward";
    instance.wards.push_back(ward);
    instance.perform = OpenYAMM::Game::ActorBehaviorPerform{"cast_ward", ActorAiAnimationState::AttackRanged, 1.6f,
        0.4f, true};
    instance.spellOverride = OpenYAMM::Game::ActorBehaviorSpell{15, 8, SkillMastery::Master, 40};
    instance.aiTypeOverride = GameplayActorAiType::Aggressive;
    instance.suppressFlee = true;

    OpenYAMM::Game::GameSaveData save;
    save.mapFileName = "oute3.odm";
    save.hasOutdoorRuntimeState = true;
    save.outdoorWorld.actorBehaviors.instances.push_back(instance);
    save.outdoorWorld.actorBehaviors.scannedActorCount = 13;
    save.outdoorWorldStates[save.mapFileName] = save.outdoorWorld;
    save.indoorSceneStates["6d19.blv"].worldRuntime.actorBehaviors.instances.push_back(instance);

    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm_actor_behaviour.oysav";
    std::string error;
    REQUIRE_MESSAGE(OpenYAMM::Game::saveGameDataToPath(path, save, error), error.c_str());
    const std::optional<OpenYAMM::Game::GameSaveData> restored = OpenYAMM::Game::loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(restored.has_value(), error.c_str());

    const ActorBehaviorRuntime::Snapshot &outdoor = restored->outdoorWorldStates.at("oute3.odm").actorBehaviors;
    CHECK(outdoor.scannedActorCount == 13);
    REQUIRE(outdoor.instances.size() == 1);
    const OpenYAMM::Game::ActorBehaviorInstanceState &loaded = outdoor.instances[0];
    CHECK(loaded.actorIndex == 12);
    CHECK(loaded.actorId == 77);
    CHECK(loaded.behaviorId == "bosses/necro_mage");
    CHECK(loaded.started);
    CHECK(loaded.randomState == 123456789u);
    CHECK(loaded.scriptState == instance.scriptState);
    CHECK(loaded.firedHealthThresholds == instance.firedHealthThresholds);
    REQUIRE(loaded.timers.size() == 1);
    CHECK(loaded.timers[0].name == "ward_return");
    REQUIRE(loaded.wards.size() == 1);
    CHECK(loaded.wards[0].effectId == "openyamm:fx/shadow_ward");
    REQUIRE(loaded.perform.has_value());
    CHECK(loaded.perform->clip == "cast_ward");
    CHECK(loaded.perform->started);
    REQUIRE(loaded.spellOverride.has_value());
    CHECK(loaded.spellOverride->skillMastery == SkillMastery::Master);
    CHECK(loaded.aiTypeOverride == GameplayActorAiType::Aggressive);
    CHECK(loaded.suppressFlee);
    CHECK(restored->indoorSceneStates.at("6d19.blv").worldRuntime.actorBehaviors.instances.size() == 1);
}

TEST_CASE("actor behaviour wards publish dome displays with their visual and recent hits")
{
    const ActorBehaviorCatalog catalog = makeCatalog(R"(
        return Behavior.define{
            onStart = function(self, s)
                self:addWard{id = "shadow", radius = 300,
                    visual = {color = {255, 170, 60}, intensity = 1.5, rim = 4, noise = 0.2}}
                self:addWard{id = "hidden", radius = 100, visual = false}
            end,
        }
    )");
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);
    runtime.update(makeFrame(makeActor(100)));
    CHECK(runtime.projectileWards().size() == 2);
    REQUIRE(runtime.wardDisplays().size() == 1);
    const OpenYAMM::Game::ActorBehaviorWardDisplay &display = runtime.wardDisplays()[0];
    CHECK(display.wardId == "shadow");
    CHECK(display.radius == doctest::Approx(300.0f));
    CHECK(display.groundZ == doctest::Approx(0.0f));
    CHECK(display.center.z == doctest::Approx(100.0f));
    CHECK(display.visual.color[0] == 255);
    CHECK(display.visual.color[1] == 170);
    CHECK(display.visual.intensity == doctest::Approx(1.5f));
    CHECK(display.visual.rimPower == doctest::Approx(4.0f));
    CHECK(display.impacts.empty());

    GameplayProjectileService::ProjectileWardBlock block = {};
    block.ownerActorIndex = 0;
    block.ownerActorId = 41;
    block.wardId = "shadow";
    block.point = {1300.0f, 0.0f, 100.0f};
    runtime.recordWardBlock(block);
    runtime.update(makeFrame(makeActor(100)));
    REQUIRE(runtime.wardDisplays()[0].impacts.size() == 1);
    CHECK(runtime.wardDisplays()[0].impacts[0].direction.x == doctest::Approx(1.0f));
    CHECK(runtime.wardDisplays()[0].ageSeconds > 0.0f);

    // Ripples last under a second.
    runtime.update(makeFrame(makeActor(100), 1.0f));
    CHECK(runtime.wardDisplays()[0].impacts.empty());
}

namespace
{
std::filesystem::path writeTacticsAssetRoot(const std::string &worldBehaviors)
{
    const std::filesystem::path root =
        std::filesystem::temp_directory_path() / ("openyamm_tactics_" + std::to_string(std::rand()));
    std::filesystem::create_directories(root / "assets_dev/engine/behaviors");
    std::filesystem::create_directories(root / "assets_dev/worlds/testworld");
    std::ofstream(root / "assets_dev/engine/behaviors/behaviors.yml")
        << "schema: openyamm.actorBehaviors.v1\nlibrary: engine/behaviors/behavior.lua\n";
    std::ofstream(root / "assets_dev/engine/behaviors/behavior.lua") << "return {}\n";
    std::ofstream(root / "assets_dev/worlds/testworld/behaviors.yml") << worldBehaviors;
    return root;
}

bool loadTacticsCatalog(const std::string &worldBehaviors, ActorBehaviorCatalog &catalog, std::string &error)
{
    const std::filesystem::path root = writeTacticsAssetRoot(worldBehaviors);
    OpenYAMM::Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "testworld"));
    const bool loaded = catalog.load(assets, "testworld", error);
    assets.shutdown();
    std::filesystem::remove_all(root);
    return loaded;
}
}

TEST_CASE("actor behaviour catalogue reads declarative tactics per monster")
{
    ActorBehaviorCatalog catalog;
    std::string error;
    REQUIRE_MESSAGE(loadTacticsCatalog(
        "schema: openyamm.actorBehaviors.v1\n"
        "tactics:\n"
        "  10065: {traverse_degrees_per_second: 90, fire_within_degrees: 4, post: {}}\n"
        "  10067: {ranged_band: [768, 2304], post: {leash: 1536}}\n",
        catalog, error), error);

    REQUIRE(catalog.hasTactics());
    const OpenYAMM::Game::ActorTacticsFacts *pTurret = catalog.tacticsForMonster(10065);
    REQUIRE(pTurret != nullptr);
    CHECK(pTurret->traverseRadiansPerSecond == doctest::Approx(3.14159265f / 2.0f));
    CHECK(pTurret->fireToleranceRadians == doctest::Approx(4.0f * 3.14159265f / 180.0f));
    CHECK(pTurret->holdPost);
    CHECK(pTurret->postLeashRadius == 0.0f);
    CHECK_FALSE(pTurret->keepsRangedBand());
    const OpenYAMM::Game::ActorTacticsFacts *pGuard = catalog.tacticsForMonster(10067);
    REQUIRE(pGuard != nullptr);
    CHECK(pGuard->rangedMinDistance == 768.0f);
    CHECK(pGuard->rangedMaxDistance == 2304.0f);
    CHECK(pGuard->postLeashRadius == 1536.0f);
    CHECK(pGuard->traverseRadiansPerSecond == 0.0f);
    CHECK(catalog.tacticsForMonster(10068) == nullptr);

    ActorBehaviorCatalog plain;
    REQUIRE(loadTacticsCatalog("schema: openyamm.actorBehaviors.v1\n", plain, error));
    CHECK_FALSE(plain.hasTactics());
}

TEST_CASE("actor behaviour catalogue rejects malformed tactics")
{
    for (const char *pTactics : {"{travers_degrees_per_second: 90}", "{ranged_band: [900, 800]}",
             "{fire_within_degrees: 4}", "{post: {radius: 10}}", "{traverse_degrees_per_second: 0}"})
    {
        ActorBehaviorCatalog catalog;
        std::string error;
        CHECK_FALSE(loadTacticsCatalog(
            std::string("schema: openyamm.actorBehaviors.v1\ntactics:\n  10065: ") + pTactics + "\n", catalog, error));
        CHECK(error.find("tactic") != std::string::npos);
    }
}

TEST_CASE("actor behaviour catalogue reads the shield_break tactic and rejects unknown reactions")
{
    ActorBehaviorCatalog catalog;
    std::string error;
    REQUIRE_MESSAGE(loadTacticsCatalog(
        "schema: openyamm.actorBehaviors.v1\n"
        "tactics:\n"
        "  10010: {shield_break: {react: fall_back, max_seconds: 5}}\n"
        "  10072: {shield_break: {react: fall_back}, ranged_band: [768, 2304]}\n",
        catalog, error), error);
    const OpenYAMM::Game::ActorTacticsFacts *pTrooper = catalog.tacticsForMonster(10010);
    REQUIRE(pTrooper != nullptr);
    CHECK(pTrooper->shieldBreakReaction == OpenYAMM::Game::ActorShieldBreakReaction::FallBack);
    CHECK(pTrooper->shieldBreakSeconds == doctest::Approx(5.0f));
    CHECK(catalog.tacticsForMonster(10072)->shieldBreakSeconds == doctest::Approx(8.0f));

    for (const char *pTactics : {"{shield_break: {react: teleport}}", "{shield_break: fall_back}",
             "{shield_break: {react: fall_back, max_seconds: 0}}", "{shield_break: {react: fall_back, seconds: 3}}"})
    {
        ActorBehaviorCatalog bad;
        CHECK_FALSE(loadTacticsCatalog(
            std::string("schema: openyamm.actorBehaviors.v1\ntactics:\n  10010: ") + pTactics + "\n", bad, error));
        CHECK(error.find("shield_break") != std::string::npos);
    }
}

TEST_CASE("actor behaviour runtime applies tactics only to their monster and posts only to immobile placements")
{
    ActorBehaviorCatalog catalog;
    OpenYAMM::Game::ActorTacticsFacts tactics = {};
    tactics.rangedMinDistance = 768.0f;
    tactics.rangedMaxDistance = 2304.0f;
    tactics.holdPost = true;
    tactics.postLeashRadius = 1536.0f;
    catalog.setMonsterTactics(10067, tactics);
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);

    const auto makeFacts = [](size_t index, int16_t monsterId, bool placedImmobile)
    {
        ActorAiFacts facts = {};
        facts.actorIndex = index;
        facts.actorId = uint32_t(100 + index);
        facts.identity.monsterId = monsterId;
        facts.movement.placedImmobile = placedImmobile;
        facts.movement.wanderRadius = 2560.0f;
        facts.movement.movementAllowed = !placedImmobile;
        return facts;
    };
    ActorAiFrameFacts frame = {};
    frame.activeActors.push_back(makeFacts(0, 10067, true));      // a gate post
    frame.activeActors.push_back(makeFacts(1, 10067, false));     // the patrol
    frame.activeActors.push_back(makeFacts(2, 194, true));        // another monster
    frame.activeActors[0].target.currentKind = ActorAiTargetKind::Party;
    frame.activeActors[0].target.currentCanSense = true;
    frame.activeActors[0].target.currentPosition = {10.0f, 20.0f, 30.0f};
    runtime.applyAiFacts(frame);

    CHECK(frame.activeActors[0].tactics.holdPost);
    CHECK(frame.activeActors[0].tactics.keepsRangedBand());
    CHECK(frame.activeActors[0].movement.movementAllowed);
    CHECK_FALSE(frame.activeActors[1].tactics.holdPost);
    CHECK(frame.activeActors[1].tactics.postLeashRadius == 0.0f);
    CHECK(frame.activeActors[1].tactics.keepsRangedBand());
    CHECK_FALSE(frame.activeActors[2].tactics.keepsRangedBand());
    CHECK_FALSE(frame.activeActors[2].movement.movementAllowed);

    GameplayRuntimeActorState aimed = {};
    aimed.actorId = 100;
    runtime.applyPresentation(0, aimed);
    CHECK(aimed.hasAimTarget);
    CHECK(aimed.aimTargetZ == 30.0f);
    GameplayRuntimeActorState idle = {};
    idle.actorId = 101;
    runtime.applyPresentation(1, idle);
    CHECK_FALSE(idle.hasAimTarget);
}

namespace
{
constexpr float ScanDegrees = 3.14159265358979323846f / 180.0f;

OpenYAMM::Game::TurretScanSettings makeScanSettings()
{
    OpenYAMM::Game::TurretScanSettings scan = {};
    scan.halfWidthRadians = 50.0f * ScanDegrees;
    scan.radiansPerSecond = 15.0f * ScanDegrees;
    scan.pauseMinSeconds = 0.8f;
    scan.pauseMaxSeconds = 2.4f;
    scan.pitchRadians = 4.0f * ScanDegrees;
    scan.holdSeconds = 3.0f;
    return scan;
}

// A Landfall-style wall turret: tactics with a traverse rate, an idle scan and a lead, placed `immobile` facing +y.
ActorBehaviorCatalog makeTurretCatalog()
{
    ActorBehaviorCatalog catalog;
    OpenYAMM::Game::ActorTacticsFacts tactics = {};
    tactics.traverseRadiansPerSecond = 120.0f * ScanDegrees;
    tactics.fireToleranceRadians = 5.0f * ScanDegrees;
    tactics.holdPost = true;
    tactics.scan = makeScanSettings();
    tactics.leadSeconds = 0.25f;
    catalog.setMonsterTactics(10065, tactics);
    return catalog;
}

ActorAiFacts makeTurretFacts(size_t index, uint32_t actorId)
{
    ActorAiFacts facts = {};
    facts.actorIndex = index;
    facts.actorId = actorId;
    facts.identity.monsterId = 10065;
    facts.movement.placedImmobile = true;
    facts.movement.hasHomeYaw = true;
    facts.movement.homeYawRadians = 1.5f;
    facts.runtime.yawRadians = 1.5f;
    return facts;
}

// One AI step of the runtime over these actors; the actors keep the facing the runtime asked for (a perfect AI).
void stepTurrets(ActorBehaviorRuntime &runtime, std::vector<ActorAiFacts> &actors, bool followIdleAim = true)
{
    ActorAiFrameFacts frame = {};
    frame.fixedStepSeconds = 1.0f / 128.0f;
    frame.activeActors = actors;

    for (ActorAiFacts &actor : frame.activeActors)
    {
        actor.tactics = {};
    }

    runtime.applyAiFacts(frame);

    for (size_t index = 0; index < actors.size(); ++index)
    {
        actors[index].tactics = frame.activeActors[index].tactics;

        if (followIdleAim && actors[index].tactics.idleAimActive)
        {
            actors[index].runtime.yawRadians = actors[index].tactics.idleAimYawRadians;
        }
    }
}
}

TEST_CASE("actor behaviour catalogue reads a turret's idle scan and lead")
{
    ActorBehaviorCatalog catalog;
    std::string error;
    REQUIRE_MESSAGE(loadTacticsCatalog(
        "schema: openyamm.actorBehaviors.v1\n"
        "tactics:\n"
        "  10065: {traverse_degrees_per_second: 120, post: {}, lead_seconds: 0.2,\n"
        "          scan: {half_width_degrees: 50, degrees_per_second: 15, pause_seconds: [0.5, 2],\n"
        "                 pitch_degrees: 4, hold_seconds: 3.5}}\n"
        "  10066: {traverse_degrees_per_second: 75, scan: {half_width_degrees: 30, degrees_per_second: 10}}\n",
        catalog, error), error);

    const OpenYAMM::Game::ActorTacticsFacts *pWard = catalog.tacticsForMonster(10065);
    REQUIRE(pWard != nullptr);
    CHECK(pWard->scan.enabled());
    CHECK(pWard->scan.halfWidthRadians == doctest::Approx(50.0f * ScanDegrees));
    CHECK(pWard->scan.radiansPerSecond == doctest::Approx(15.0f * ScanDegrees));
    CHECK(pWard->scan.pauseMinSeconds == 0.5f);
    CHECK(pWard->scan.pauseMaxSeconds == 2.0f);
    CHECK(pWard->scan.pitchRadians == doctest::Approx(4.0f * ScanDegrees));
    CHECK(pWard->scan.holdSeconds == 3.5f);
    CHECK(pWard->leadSeconds == doctest::Approx(0.2f));
    const OpenYAMM::Game::ActorTacticsFacts *pBastion = catalog.tacticsForMonster(10066);
    REQUIRE(pBastion != nullptr);
    CHECK(pBastion->scan.pauseMaxSeconds > pBastion->scan.pauseMinSeconds);
    CHECK(pBastion->scan.holdSeconds > 0.0f);
    CHECK(pBastion->leadSeconds == 0.0f);

    for (const char *pTactics : {"{scan: {half_width_degrees: 50, degrees_per_second: 15}}", "{lead_seconds: 0.2}",
             "{traverse_degrees_per_second: 90, scan: {half_width_degrees: 50}}",
             "{traverse_degrees_per_second: 90, scan: {half_width_degrees: 50, degrees_per_second: 15, speed: 1}}",
             "{traverse_degrees_per_second: 90, scan: {half_width_degrees: 50, degrees_per_second: 15, "
             "pause_seconds: [3, 1]}}",
             "{traverse_degrees_per_second: 90, lead_seconds: 5}"})
    {
        ActorBehaviorCatalog rejected;
        CHECK_FALSE(loadTacticsCatalog(
            std::string("schema: openyamm.actorBehaviors.v1\ntactics:\n  10065: ") + pTactics + "\n", rejected, error));
        CHECK(error.find("tactic") != std::string::npos);
    }
}

TEST_CASE("turret scan sweeps both ways within its width, eases every turnaround and pauses")
{
    const OpenYAMM::Game::TurretScanSettings settings = makeScanSettings();
    OpenYAMM::Game::TurretScanState state;
    OpenYAMM::Game::startTurretScan(state, 4242u, 0.0f, 0.0f, 0.0f, 1.0f);
    constexpr float Step = 1.0f / 128.0f;
    float previous = OpenYAMM::Game::turretScanPose(state).yawOffsetRadians;
    float previousVelocity = 0.0f;
    float lowest = 0.0f;
    float highest = 0.0f;
    float stillSeconds = 0.0f;
    float longestStill = 0.0f;
    int reversals = 0;
    float largestReversalVelocity = 0.0f;
    float lowestPitch = 0.0f;
    float highestPitch = 0.0f;

    for (int step = 0; step < 128 * 120; ++step)
    {
        const OpenYAMM::Game::TurretScanPose pose = OpenYAMM::Game::advanceTurretScan(state, settings, Step);
        const float velocity = (pose.yawOffsetRadians - previous) / Step;
        // Never faster than its peak rate, so never a snap.
        CHECK(std::abs(velocity) <= settings.radiansPerSecond * 1.02f);
        CHECK(std::abs(pose.yawOffsetRadians) <= settings.halfWidthRadians + 1.0e-4f);
        CHECK(std::abs(pose.pitchRadians) <= settings.pitchRadians + 1.0e-5f);
        lowest = std::min(lowest, pose.yawOffsetRadians);
        highest = std::max(highest, pose.yawOffsetRadians);
        lowestPitch = std::min(lowestPitch, pose.pitchRadians);
        highestPitch = std::max(highestPitch, pose.pitchRadians);

        if (std::abs(velocity) < 1.0e-6f)
        {
            stillSeconds += Step;
            longestStill = std::max(longestStill, stillSeconds);
        }
        else
        {
            if (previousVelocity != 0.0f && (velocity > 0.0f) != (previousVelocity > 0.0f))
            {
                ++reversals;
                largestReversalVelocity = std::max(largestReversalVelocity, std::abs(velocity));
            }

            previousVelocity = velocity;
            stillSeconds = 0.0f;
        }

        previous = pose.yawOffsetRadians;
    }

    // Ping-pong across most of the width, with eased turnarounds (they start from rest) and pauses in the range.
    CHECK(lowest < -0.5f * settings.halfWidthRadians);
    CHECK(highest > 0.5f * settings.halfWidthRadians);
    CHECK(reversals >= 6);
    CHECK(largestReversalVelocity < 0.05f * settings.radiansPerSecond);
    CHECK(longestStill >= settings.pauseMinSeconds);
    CHECK(longestStill <= settings.pauseMaxSeconds + 0.05f);
    CHECK(highestPitch - lowestPitch > settings.pitchRadians);
}

TEST_CASE("turret scan differs per seed and returns from outside its width at the return rate")
{
    const OpenYAMM::Game::TurretScanSettings settings = makeScanSettings();
    OpenYAMM::Game::TurretScanState first;
    OpenYAMM::Game::TurretScanState second;
    OpenYAMM::Game::startTurretScan(first, 1u, 0.0f, 0.0f, 0.0f, 0.0f);
    OpenYAMM::Game::startTurretScan(second, 2u, 0.0f, 0.0f, 0.0f, 0.0f);
    float difference = 0.0f;

    for (int step = 0; step < 128 * 30; ++step)
    {
        difference = std::max(difference, std::abs(
            OpenYAMM::Game::advanceTurretScan(first, settings, 1.0f / 128.0f).yawOffsetRadians
            - OpenYAMM::Game::advanceTurretScan(second, settings, 1.0f / 128.0f).yawOffsetRadians));
    }

    CHECK(difference > 0.3f);

    // Back from a fight 2.5 rad round: a beat's delay, then an eased return into the sweep at the return rate.
    OpenYAMM::Game::TurretScanState back;
    const float returnRate = 60.0f * ScanDegrees;
    OpenYAMM::Game::startTurretScan(back, 3u, 2.5f, 0.0f, 0.4f, returnRate);
    CHECK(OpenYAMM::Game::advanceTurretScan(back, settings, 0.3f).yawOffsetRadians == 2.5f);
    float previous = 2.5f;
    float fastest = 0.0f;
    float seconds = 0.3f;

    while (previous > settings.halfWidthRadians && seconds < 20.0f)
    {
        const float yaw = OpenYAMM::Game::advanceTurretScan(back, settings, 1.0f / 128.0f).yawOffsetRadians;
        fastest = std::max(fastest, (previous - yaw) * 128.0f);
        CHECK(yaw <= previous + 1.0e-6f);
        previous = yaw;
        seconds += 1.0f / 128.0f;
    }

    CHECK(previous <= settings.halfWidthRadians);
    CHECK(fastest > 0.9f * returnRate);
    CHECK(fastest <= returnRate * 1.02f);
    CHECK(seconds < 0.4f + 1.5f * 2.5f / returnRate + 0.1f);
}

TEST_CASE("actor behaviour runtime scans an idle turret, holds a lost target's aim, then eases back into the scan")
{
    const ActorBehaviorCatalog catalog = makeTurretCatalog();
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);
    CHECK(runtime.turnsAtTraverseRate(10065));
    CHECK_FALSE(runtime.turnsAtTraverseRate(194));
    std::vector<ActorAiFacts> actors = {makeTurretFacts(0, 500), makeTurretFacts(1, 501)};

    // Idle: a scan around the placement facing, each turret on its own phase.
    float spread = 0.0f;
    float farthest = 0.0f;

    for (int step = 0; step < 128 * 20; ++step)
    {
        stepTurrets(runtime, actors);
        REQUIRE(actors[0].tactics.idleAimActive);
        farthest = std::max(farthest, std::abs(actors[0].runtime.yawRadians - 1.5f));
        spread = std::max(spread, std::abs(actors[0].runtime.yawRadians - actors[1].runtime.yawRadians));
    }

    CHECK(farthest > 0.4f);
    CHECK(farthest <= 50.0f * ScanDegrees + 1.0e-3f);
    CHECK(spread > 0.2f);
    GameplayRuntimeActorState scanning = {};
    scanning.actorId = 500;
    runtime.applyPresentation(0, scanning);
    CHECK(scanning.aimScanning);
    CHECK_FALSE(scanning.hasAimTarget);

    // Engaged: no idle aim (the AI tracks the target); the aim leads a target moving at 400 units/s along x.
    actors[0].target.currentKind = ActorAiTargetKind::Actor;
    actors[0].target.currentActorIndex = 7;
    actors[0].target.currentCanSense = true;
    actors[0].target.currentPosition = {0.0f, 2000.0f, 300.0f};

    for (int step = 0; step < 128 * 2; ++step)
    {
        actors[0].target.currentPosition.x += 400.0f / 128.0f;
        stepTurrets(runtime, actors);
        CHECK_FALSE(actors[0].tactics.idleAimActive);
    }

    CHECK(actors[0].tactics.aimLead.x == doctest::Approx(400.0f * 0.25f).epsilon(0.05));
    CHECK(std::abs(actors[0].tactics.aimLead.y) < 1.0f);
    GameplayRuntimeActorState engaged = {};
    engaged.actorId = 500;
    runtime.applyPresentation(0, engaged);
    REQUIRE(engaged.hasAimTarget);
    CHECK_FALSE(engaged.aimScanning);
    CHECK(engaged.aimTargetX == doctest::Approx(actors[0].target.currentPosition.x + actors[0].tactics.aimLead.x));

    // The target dies: the facing and the barrel hold the last aim for the hold time.
    const float heldYaw = 0.7f;
    actors[0].runtime.yawRadians = heldYaw;
    const float lastAimX = engaged.aimTargetX;
    actors[0].target = {};

    for (int step = 0; step < int(128 * 2.9f); ++step)
    {
        stepTurrets(runtime, actors);
        REQUIRE(actors[0].tactics.idleAimActive);
        CHECK(actors[0].tactics.idleAimYawRadians == heldYaw);
        CHECK(actors[0].tactics.aimLead.x == 0.0f);
    }

    GameplayRuntimeActorState holding = {};
    holding.actorId = 500;
    runtime.applyPresentation(0, holding);
    REQUIRE(holding.hasAimTarget);
    CHECK(holding.aimTargetX == doctest::Approx(lastAimX));

    // Then the scan resumes from where it points, after a beat, and eases back towards its centre without a jump.
    float previous = actors[0].runtime.yawRadians;
    float fastest = 0.0f;

    for (int step = 0; step < 128 * 8; ++step)
    {
        stepTurrets(runtime, actors);
        fastest = std::max(fastest, std::abs(actors[0].runtime.yawRadians - previous) * 128.0f);
        previous = actors[0].runtime.yawRadians;
    }

    CHECK(std::abs(actors[0].runtime.yawRadians - 1.5f) <= 50.0f * ScanDegrees + 1.0e-3f);
    CHECK(fastest <= 60.0f * ScanDegrees * 1.05f);
    GameplayRuntimeActorState resumed = {};
    resumed.actorId = 500;
    runtime.applyPresentation(0, resumed);
    CHECK(resumed.aimScanning);
    CHECK_FALSE(resumed.hasAimTarget);
}

TEST_CASE("actor behaviour runtime leaves actors without a turret scan untouched")
{
    ActorBehaviorCatalog catalog;
    OpenYAMM::Game::ActorTacticsFacts tactics = {};
    tactics.traverseRadiansPerSecond = 1.0f;
    tactics.holdPost = true;
    catalog.setMonsterTactics(10065, tactics);
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);
    std::vector<ActorAiFacts> actors = {makeTurretFacts(0, 500)};

    for (int step = 0; step < 128; ++step)
    {
        stepTurrets(runtime, actors);
        CHECK_FALSE(actors[0].tactics.idleAimActive);
        CHECK(actors[0].runtime.yawRadians == 1.5f);
    }

    GameplayRuntimeActorState state = {};
    state.actorId = 500;
    runtime.applyPresentation(0, state);
    CHECK_FALSE(state.aimScanning);
    CHECK_FALSE(state.hasAimTarget);
}

TEST_CASE("actor behaviour commands: blink, shield, leave, speed, invulnerability and QBit queries")
{
    const ActorBehaviorCatalog catalog = makeCatalog(R"(
        return Behavior.define{
            onStart = function(self, s)
                self:blink()
                self:suspendShield(4)
                self:restoreShield()
                self:leave("openyamm:fx/arcane_pulse")
                self:setSpeed(1.5)
                self:setInvulnerable(true)
                self:summonAt(308, 10, 20, 30, 2, 0)
                self:say(self:qbit(5) and "qbit" or "no qbit")
            end,
        }
    )");
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);

    const ActorBehaviorFrameResult result = runtime.update(makeFrame(makeActor(100)));
    using Kind = OpenYAMM::Game::ActorBehaviorActorCommand::Kind;
    REQUIRE_EQ(result.actorCommands.size(), 4u);
    CHECK(result.actorCommands[0].kind == Kind::Blink);
    CHECK(result.actorCommands[1].kind == Kind::SuspendShield);
    CHECK_EQ(result.actorCommands[1].seconds, doctest::Approx(4.0f));
    CHECK(result.actorCommands[2].kind == Kind::RestoreShield);
    CHECK(result.actorCommands[3].kind == Kind::Leave);
    CHECK_EQ(result.actorCommands[3].effectId, "openyamm:fx/arcane_pulse");
    REQUIRE_EQ(result.summons.size(), 2u);
    CHECK_EQ(result.summons[0].position.x, doctest::Approx(10.0f));
    CHECK_EQ(result.summons[1].position.z, doctest::Approx(30.0f));
    CHECK(hasMessage(result, "no qbit"));
    CHECK_EQ(runtime.speedMultiplier(0, 41), doctest::Approx(1.5f));
    CHECK(runtime.invulnerable(0, OpenYAMM::Game::ShieldAttackTier::Spell));

    ActorAiFrameFacts facts = {};
    ActorAiFacts actor = makeAiActor();
    actor.movement.effectiveMoveSpeed = 100.0f;
    facts.activeActors.push_back(actor);
    runtime.applyAiFacts(facts);
    CHECK_EQ(facts.activeActors.front().movement.effectiveMoveSpeed, doctest::Approx(150.0f));
    CHECK_EQ(facts.activeActors.front().behavior.attackRateMultiplier, doctest::Approx(1.5f));
}

TEST_CASE("actor behaviour tactics per actor: leash, ranged band, move-to point, map events, bearing and front armour")
{
    const ActorBehaviorCatalog catalog = makeCatalog(R"(
        return Behavior.define{
            onStart = function(self, s)
                self:setLeash(600)
                self:setRangedBand(300, 900)
                self:moveTo(50, 60, 0)
                self:runEvent(41)
                self:setArmoredFront(60, 0.25)
                self:say(string.format("bearing %.0f", self:bearingToParty()))
            end,
        }
    )");
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);

    ActorBehaviorFrameFacts frame = makeFrame(makeActor(100));
    // The actor at (1000, 0) faces north (90 degrees); the party is due west of it: 90 degrees to its left.
    frame.actors.front().yawRadians = 1.5707964f;
    frame.partyPosition = {0.0f, 0.0f, 0.0f};
    const ActorBehaviorFrameResult result = runtime.update(frame);
    CHECK(hasMessage(result, "bearing 90"));
    REQUIRE_EQ(result.mapEvents.size(), 1u);
    CHECK_EQ(result.mapEvents.front(), 41);

    ActorAiFrameFacts facts = {};
    facts.activeActors.push_back(makeAiActor());
    ActorAiFacts placed = makeAiActor();
    placed.actorIndex = 1;
    placed.actorId = 42;
    placed.movement.placedLeashRadius = 400.0f;
    facts.activeActors.push_back(placed);
    runtime.applyAiFacts(facts);
    const ActorAiFacts &scripted = facts.activeActors[0];
    CHECK(scripted.tactics.holdPost);
    CHECK_EQ(scripted.tactics.postLeashRadius, doctest::Approx(600.0f));
    CHECK_EQ(scripted.tactics.rangedMinDistance, doctest::Approx(300.0f));
    CHECK_EQ(scripted.tactics.rangedMaxDistance, doctest::Approx(900.0f));
    CHECK_EQ(scripted.movement.homePosition.x, doctest::Approx(50.0f));
    CHECK(facts.activeActors[1].tactics.holdPost);
    CHECK_EQ(facts.activeActors[1].tactics.postLeashRadius, doctest::Approx(400.0f));

    // A hit from ahead (north of it) loses three quarters; one from behind does not.
    const OpenYAMM::Game::GameplayWorldPoint actorPosition = {1000.0f, 0.0f, 0.0f};
    CHECK_EQ(runtime.incomingDamageMultiplier(0, actorPosition, 1.5707964f, {1000.0f, 500.0f, 0.0f}),
        doctest::Approx(0.25f));
    CHECK_EQ(runtime.incomingDamageMultiplier(0, actorPosition, 1.5707964f, {1000.0f, -500.0f, 0.0f}),
        doctest::Approx(1.0f));
}

TEST_CASE("a resting (dormant) actor holds still without turning to its target")
{
    ActorBehaviorRuntime runtime;
    ActorAiFrameFacts facts = {};
    ActorAiFacts actor = makeAiActor();
    actor.movement.dormant = true;
    facts.activeActors.push_back(actor);
    runtime.applyAiFacts(facts);
    CHECK(facts.activeActors.front().behavior.holdActive);
    CHECK(facts.activeActors.front().behavior.holdKeepsFacing);
    CHECK(facts.activeActors.front().behavior.holdAnimation == ActorAiAnimationState::Standing);
}

TEST_CASE("a patrolling actor walks its waypoints in turn as a post walks home")
{
    const std::vector<std::array<int32_t, 3>> points = {{0, 0, 0}, {1000, 0, 0}, {1000, 1000, 0}};
    size_t index = 0;
    // Far from the first waypoint it heads there; once within reach of one it heads for the next, round and round.
    CHECK_EQ(OpenYAMM::Game::nextPatrolWaypoint(points, index, 500.0f, 500.0f).x, doctest::Approx(0.0f));
    CHECK_EQ(OpenYAMM::Game::nextPatrolWaypoint(points, index, 20.0f, 0.0f).x, doctest::Approx(1000.0f));
    CHECK_EQ(index, 1u);
    CHECK_EQ(OpenYAMM::Game::nextPatrolWaypoint(points, index, 1000.0f, 50.0f).y, doctest::Approx(1000.0f));
    CHECK_EQ(OpenYAMM::Game::nextPatrolWaypoint(points, index, 1000.0f, 1000.0f).x, doctest::Approx(0.0f));
    CHECK_EQ(index, 0u);

    ActorBehaviorRuntime runtime;
    ActorAiFrameFacts facts = {};
    ActorAiFacts actor = makeAiActor();
    actor.movement.patrolTarget = OpenYAMM::Game::GameplayWorldPoint{1000.0f, 0.0f, 0.0f};
    facts.activeActors.push_back(actor);
    actor.movement.dormant = true;
    facts.activeActors.push_back(actor);
    runtime.applyAiFacts(facts);
    CHECK(facts.activeActors[0].tactics.holdPost);
    CHECK(facts.activeActors[0].movement.movementAllowed);
    CHECK_FALSE(facts.activeActors[0].movement.hasHomeYaw);
    CHECK_EQ(facts.activeActors[0].movement.homePosition.x, doctest::Approx(1000.0f));
    // A resting one stays put.
    CHECK_FALSE(facts.activeActors[1].tactics.holdPost);
}

TEST_CASE("shield-break climb lifts a falling-back flyer above its target")
{
    ActorBehaviorCatalog catalog;
    std::string error;
    REQUIRE_MESSAGE(loadTacticsCatalog(
        "schema: openyamm.actorBehaviors.v1\ntactics:\n  10030: {shield_break: {react: climb, max_seconds: 5}}\n",
        catalog, error), error);
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);
    ActorAiFacts facts = makeAiActor();
    facts.identity.monsterId = 10030;
    facts.status.hostileToParty = true;
    facts.status.shieldDownSinceBreakSeconds = 1.0f;
    facts.target.currentKind = ActorAiTargetKind::Party;
    ActorAiFrameFacts frame = {};
    frame.activeActors.push_back(facts);
    facts.status.shieldDownSinceBreakSeconds = 6.0f;
    frame.activeActors.push_back(facts);
    runtime.applyAiFacts(frame);
    CHECK(frame.activeActors[0].status.forceFleeFromParty);
    CHECK(frame.activeActors[0].status.climbAboveTarget > 0.0f);
    // Past its seconds it fights on at its own height.
    CHECK_FALSE(frame.activeActors[1].status.forceFleeFromParty);
    CHECK(frame.activeActors[1].status.climbAboveTarget == 0.0f);
}

TEST_CASE("an MM9 boss script drives its loop: directives, one-shots, the loop's events and physical immunity")
{
    const ActorBehaviorCatalog catalog = makeCatalog(R"(
        return Behavior.define{
            onStart = function(self, s)
                self:setMm9{drives_attacks = true, ignores_calls = true, chase_limit = 0, turn_degrees = 180,
                    immune = "physical"}
                self:setTarget("party")
                self:attack("spell1")
                self:trace("start")
            end,
            onTargetChanged = function(self, s, target)
                self:say("target " .. (target and target.kind or "none"))
            end,
            onHit = function(self, s, attacker)
                self:say("hit by " .. attacker.kind .. " " .. attacker.index)
            end,
            onAttackDone = function(self, s)
                local target = self:target()
                self:say("done " .. target.kind .. " " .. math.floor(target.distance))
            end,
            onTrigger = function(self, s, message)
                self:say("trigger " .. message)
            end,
        }
    )");
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);
    runtime.update(makeFrame(makeActor(100)));

    ActorAiFrameFacts facts = {};
    facts.party.position = {100.0f, 1000.0f, 0.0f};
    facts.party.collisionRadius = 37.0f;
    facts.party.collisionHeight = 128.0f;
    facts.activeActors.push_back(makeAiActor());
    runtime.applyAiFacts(facts);

    const OpenYAMM::Game::ActorMm9ScriptFacts &directives = facts.activeActors[0].behavior.mm9Script;
    CHECK(directives.active);
    CHECK(directives.drivesAttacks);
    CHECK(directives.ignoresCalls);
    CHECK_EQ(directives.chaseLimitSeconds, doctest::Approx(0.0f));
    CHECK_EQ(directives.turnRadiansPerSecond, doctest::Approx(3.14159265f));
    CHECK(directives.setTarget);
    CHECK(directives.targetKind == ActorAiTargetKind::Party);
    REQUIRE(directives.attack.has_value());
    CHECK(*directives.attack == GameplayActorAttackAbility::Spell1);
    REQUIRE_EQ(directives.traceLines.size(), 1u);
    CHECK_EQ(directives.traceLines[0], "start");
    CHECK(runtime.invulnerable(0, OpenYAMM::Game::ShieldAttackTier::Physical));
    CHECK_FALSE(runtime.invulnerable(0, OpenYAMM::Game::ShieldAttackTier::Spell));

    // One-shots last one AI step.
    ActorAiFrameFacts next = facts;
    next.activeActors[0].behavior = {};
    runtime.applyAiFacts(next);
    CHECK_FALSE(next.activeActors[0].behavior.mm9Script.setTarget);
    CHECK_FALSE(next.activeActors[0].behavior.mm9Script.attack.has_value());
    CHECK(next.activeActors[0].behavior.mm9Script.drivesAttacks);

    // The loop took the party and attacks; then it is hit by actor 3, the attack ends, a trigger comes.
    ActorAiFrameFacts attacking = facts;
    attacking.activeActors[0].behavior = {};
    attacking.activeActors[0].runtime.mm9.targetKind = ActorAiTargetKind::Party;
    attacking.activeActors[0].runtime.motionState = ActorAiMotionState::Attacking;
    attacking.activeActors[0].mm9World.damageSerial = 1;
    attacking.activeActors[0].mm9World.attackerKind = ActorAiTargetKind::Actor;
    attacking.activeActors[0].mm9World.attackerActorIndex = 3;
    runtime.applyAiFacts(attacking);
    CHECK(runtime.trigger(0, "startup"));
    const ActorBehaviorFrameResult events = runtime.update(makeFrame(makeActor(100)));
    CHECK(hasMessage(events, "target party"));
    CHECK(hasMessage(events, "hit by actor 3"));
    CHECK(hasMessage(events, "trigger startup"));

    ActorAiFrameFacts done = attacking;
    done.activeActors[0].runtime.motionState = ActorAiMotionState::Standing;
    runtime.applyAiFacts(done);
    const ActorBehaviorFrameResult finished = runtime.update(makeFrame(makeActor(100)));
    // Centre to centre (1 000 apart; the same heights) less both radii.
    CHECK(hasMessage(finished, "done party 931"));
}
