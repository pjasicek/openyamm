#include "engine/AssetFileSystem.h"
#include "tests/ContentPackTestSupport.h"
#include "engine/AssetScaleTier.h"
#include "engine/ImageMipmaps.h"
#include "engine/models/GltfModelLoader.h"
#include "engine/models/ModelInstance.h"
#include "game/gameplay/ActorModelPresentation.h"
#include "game/gameplay/GameplayActorAiTypes.h"

#include <doctest/doctest.h>

#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <memory>
#include <numbers>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

TEST_CASE("ModelAnimation mm8 Ogre peasant keeps civilian motion and a grounded corpse")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", AssetScaleTier::X1));
    const ModelLoadResult loaded = GltfModelLoader().load(assets, "worlds/mm8/models/mm8_m436.glb");
    REQUIRE_MESSAGE(loaded, loaded.error);
    const ModelAsset &asset = *loaded.asset;
    CHECK_EQ(asset.materialVariants, std::vector<std::string>{"m436_a", "m436_b", "m436_c"});
    for (const char *pClip : {"Standing", "Walking", "Running", "Hit", "Death", "Dead", "Fidget"})
    {
        REQUIRE_MESSAGE(asset.findClip(pClip).has_value(), pClip);
    }
    CHECK_FALSE(asset.findClip("Attack").has_value());
    CHECK_FALSE(asset.findClip("Cast").has_value());
    for (const char *pSocket : {"Socket_Palm_Left", "Socket_Palm_Right", "Socket_Eye_Left", "Socket_Eye_Right"})
    {
        REQUIRE_MESSAGE(asset.findNode(pSocket).has_value(), pSocket);
    }
    ModelInstanceSystem instances;
    const ModelInstanceHandle handle = instances.create(loaded.asset);
    const uint32_t death = *asset.findClip("Death");
    REQUIRE(instances.sample(handle, death, asset.clips[death].durationSeconds, {}));
    const ModelMatrix fallen = *instances.nodeMatrix(handle, "B_Pelvis");
    for (const float time : {0.0f, 0.5f, 1.0f})
    {
        REQUIRE(instances.sample(handle, *asset.findClip("Dead"), time, {}));
        const ModelMatrix held = *instances.nodeMatrix(handle, "B_Pelvis");
        for (size_t component = 0; component < 16; ++component)
        {
            CHECK(held[component] == doctest::Approx(fallen[component]).epsilon(1.0e-4));
        }
    }
}

TEST_CASE("ModelAnimation mm8 Ogre keeps club motion and recovery in the cooked asset")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", AssetScaleTier::X1));
    const ModelLoadResult body = GltfModelLoader().load(assets, "worlds/mm8/models/mm8_m440.glb");
    const ModelLoadResult club = GltfModelLoader().load(assets, "worlds/mm8/models/mm8_m440_club.glb");
    REQUIRE_MESSAGE(body, body.error);
    REQUIRE_MESSAGE(club, club.error);
    const ModelAsset &asset = *body.asset;
    CHECK_EQ(asset.materialVariants, std::vector<std::string>{"m440_a", "m440_b", "m440_c"});
    for (const char *pClip : {"Standing", "Walking", "Running", "Attack", "Hit", "Death", "Dead", "Fidget"})
    {
        CHECK_MESSAGE(asset.findClip(pClip).has_value(), pClip);
    }
    const std::optional<uint32_t> attachment = asset.findNode("Club");
    const std::optional<uint32_t> attack = asset.findClip("Attack");
    const std::optional<uint32_t> death = asset.findClip("Death");
    const std::optional<uint32_t> dead = asset.findClip("Dead");
    REQUIRE(attachment);
    REQUIRE(attack);
    REQUIRE(death);
    REQUIRE(dead);
    // The fastest tier has 0.5 s left after the native one-second attack wind-up.
    constexpr float Impact = 26.0f / 30.0f;
    CHECK(asset.clips[*attack].durationSeconds - Impact == doctest::Approx(0.5f));
    ModelInstanceSystem instances;
    const ModelInstanceHandle handle = instances.create(body.asset);
    REQUIRE(instances.sample(handle, *attack, 0, {}));
    const ModelMatrix initial = *instances.nodeMatrix(handle, "Club");
    REQUIRE(instances.sample(handle, *attack, Impact, {}));
    const ModelMatrix impact = *instances.nodeMatrix(handle, "Club");
    float distanceSquared = 0;
    for (size_t axis = 12; axis < 15; ++axis)
    {
        distanceSquared += (impact[axis] - initial[axis]) * (impact[axis] - initial[axis]);
    }
    CHECK_GT(distanceSquared, 0.16f);
    REQUIRE(instances.sample(handle, *death, asset.clips[*death].durationSeconds, {}));
    const ModelMatrix fallen = *instances.nodeMatrix(handle, "Club");
    REQUIRE(instances.sample(handle, *dead, 0, {}));
    const ModelMatrix held = *instances.nodeMatrix(handle, "Club");
    for (size_t component = 0; component < 16; ++component)
    {
        CHECK(held[component] == doctest::Approx(fallen[component]).epsilon(1.0e-4));
    }
}

TEST_CASE("ModelAnimation mm8 Vampire keeps claw, jaw, palm sockets and a held corpse")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", AssetScaleTier::X1));
    const ModelLoadResult loaded = GltfModelLoader().load(assets, "worlds/mm8/models/mm8_m468.glb");
    REQUIRE_MESSAGE(loaded, loaded.error);
    const ModelAsset &asset = *loaded.asset;
    CHECK_EQ(asset.materialVariants, std::vector<std::string>{"m468_a", "m468_b", "m468_c"});
    for (const char *pClip : {"Standing", "Walking", "Running", "Attack", "Cast", "Hit", "Death", "Dead", "Fidget"})
    {
        REQUIRE_MESSAGE(asset.findClip(pClip).has_value(), pClip);
    }
    for (const char *pNode : {"B_Jaw", "Socket_Palm_Left", "Socket_Palm_Right", "Socket_Eye_Left", "Socket_Eye_Right"})
    {
        REQUIRE_MESSAGE(asset.findNode(pNode).has_value(), pNode);
    }
    ModelInstanceSystem instances;
    const ModelInstanceHandle handle = instances.create(loaded.asset);
    const uint32_t attack = *asset.findClip("Attack");
    constexpr float Impact = 77.0f / 60.0f;
    CHECK(asset.clips[attack].durationSeconds - Impact == doctest::Approx(43.0f / 60.0f));
    REQUIRE(instances.sample(handle, attack, 0, {}));
    const ModelMatrix initial = *instances.nodeMatrix(handle, "Socket_Palm_Right");
    REQUIRE(instances.sample(handle, attack, Impact, {}));
    const ModelMatrix impact = *instances.nodeMatrix(handle, "Socket_Palm_Right");
    float distanceSquared = 0;
    for (size_t axis = 12; axis < 15; ++axis)
    {
        distanceSquared += (impact[axis] - initial[axis]) * (impact[axis] - initial[axis]);
    }
    CHECK_GT(distanceSquared, 0.16f);
    REQUIRE(instances.sample(handle, *asset.findClip("Cast"), 35.0f / 30.0f, {}));
    const ModelMatrix left = *instances.nodeMatrix(handle, "Socket_Palm_Left");
    const ModelMatrix right = *instances.nodeMatrix(handle, "Socket_Palm_Right");
    CHECK_GT(std::abs(left[12] - right[12]), 0.3f);
    CHECK_LT(std::abs(left[13] - right[13]), 0.1f);
    const uint32_t cast = *asset.findClip("Cast");
    REQUIRE(instances.sample(handle, cast, 13.0f / 48.0f, {}));
    ModelMatrix previousPalm = *instances.nodeMatrix(handle, "Socket_Palm_Left");
    for (int frame = 14; frame <= 44; ++frame)
    {
        REQUIRE(instances.sample(handle, cast, frame / 48.0f, {}));
        const ModelMatrix palm = *instances.nodeMatrix(handle, "Socket_Palm_Left");
        float stepSquared = 0;
        for (size_t axis = 12; axis < 15; ++axis)
        {
            stepSquared += (palm[axis] - previousPalm[axis]) * (palm[axis] - previousPalm[axis]);
        }
        CHECK_GT(stepSquared, 1.0e-8f);
        previousPalm = palm;
    }
    const uint32_t death = *asset.findClip("Death");
    REQUIRE(instances.sample(handle, death, asset.clips[death].durationSeconds, {}));
    const ModelMatrix fallen = *instances.nodeMatrix(handle, "B_Pelvis");
    for (const float time : {0.0f, 0.5f, 1.0f})
    {
        REQUIRE(instances.sample(handle, *asset.findClip("Dead"), time, {}));
        const ModelMatrix held = *instances.nodeMatrix(handle, "B_Pelvis");
        for (size_t component = 0; component < 16; ++component)
        {
            CHECK(held[component] == doctest::Approx(fallen[component]).epsilon(1.0e-4));
        }
    }
}

namespace
{
std::shared_ptr<OpenYAMM::Engine::ModelAsset> makeAnimatedAsset()
{
    using namespace OpenYAMM::Engine;
    std::shared_ptr<ModelAsset> asset = std::make_shared<ModelAsset>();
    asset->nodes.resize(2);
    asset->nodes[0].name = "child";
    asset->nodes[0].parentIndex = 1;
    asset->nodes[0].transform.translation = {1.0f, 0.0f, 0.0f};
    asset->nodes[0].matrix = composeModelTransform(asset->nodes[0].transform);
    asset->nodes[1].name = "root";
    asset->nodes[1].childIndices = {0};
    asset->nodes[1].matrix = identityModelMatrix();
    asset->hierarchyOrder = {1, 0};
    asset->nodeIndicesByName = {{"child", 0}, {"root", 1}};

    ModelAnimationChannel translation;
    translation.nodeIndex = 0;
    translation.target = ModelAnimationTarget::Translation;
    translation.interpolation = ModelAnimationInterpolation::Linear;
    translation.times = {0.0f, 1.0f};
    translation.values = {{0.0f, 0.0f, 0.0f, 0.0f}, {2.0f, 0.0f, 0.0f, 0.0f}};

    ModelAnimationChannel rotation;
    rotation.nodeIndex = 0;
    rotation.target = ModelAnimationTarget::Rotation;
    rotation.interpolation = ModelAnimationInterpolation::Linear;
    rotation.times = {0.0f, 1.0f};
    rotation.values = {{0.0f, 0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 0.0f}};

    ModelAnimationClip clip;
    clip.name = "move";
    clip.durationSeconds = 1.0f;
    clip.channels = {translation, rotation};
    asset->clips.push_back(std::move(clip));
    asset->clipIndicesByName.emplace("move", 0);
    return asset;
}

TEST_CASE("ModelAnimation blends local poses, interrupts transitions and masks actions without eager deformation")
{
    using namespace OpenYAMM::Engine;
    std::shared_ptr<ModelAsset> asset = makeAnimatedAsset();
    asset->clips.push_back(asset->clips[0]);
    asset->clips[1].name = "hold";
    asset->clips[1].channels[0].values = {{4, 0, 0, 0}, {4, 0, 0, 0}};
    asset->clips[1].channels[1].values = {{0, 0, 0, -1}, {0, 0, 0, -1}};
    ModelInstanceSystem instances;
    const ModelInstanceHandle handle = instances.create(asset);
    REQUIRE(instances.sample(handle, 0, 0, {}));
    const ModelPose *pPose = instances.pose(handle, false);
    REQUIRE(pPose != nullptr);
    const uint64_t revision = pPose->matrixRevision;
    REQUIRE(instances.sampleBlended(handle, 1, 0, {}, .05f, .1f));
    CHECK(pPose->matrixRevision == revision);
    pPose = instances.pose(handle, false);
    CHECK(pPose->localTransforms[0].translation[0] == doctest::Approx(2));
    CHECK(std::abs(pPose->localTransforms[0].rotation[3]) == doctest::Approx(1));
    CHECK(std::all_of(pPose->deformedVertices.begin(), pPose->deformedVertices.end(),
        [](const auto &node) { return node.empty(); }));
    // Interrupt halfway through: the visible intermediate pose is the new source, so there is no pop.
    REQUIRE(instances.sampleBlended(handle, 0, 0, {}, 0, .1f));
    CHECK(instances.pose(handle, false)->localTransforms[0].translation[0] == doctest::Approx(2));
    // Eased: a quarter of the way the pose has moved 0.15625 of the distance (smoothstep), half way exactly half.
    REQUIRE(instances.sampleBlended(handle, 0, 0, {}, .025f, .1f));
    CHECK(instances.pose(handle, false)->localTransforms[0].translation[0] == doctest::Approx(1.6875));
    REQUIRE(instances.sampleBlended(handle, 0, 0, {}, .025f, .1f));
    CHECK(instances.pose(handle, false)->localTransforms[0].translation[0] == doctest::Approx(1));
    REQUIRE(instances.sampleBlended(handle, 0, 0, {}, .05f, .1f));
    CHECK(instances.pose(handle, false)->localTransforms[0].translation[0] == doctest::Approx(0));
    const std::shared_ptr<const std::vector<float>> mask = std::make_shared<std::vector<float>>(
        std::initializer_list<float>{1.0f, 0.0f});
    const ModelAnimationLayer action{1, 0, .5f, mask};
    REQUIRE(instances.sampleBlended(handle, 0, .5f, {}, 0, 0, action));
    pPose = instances.pose(handle, false);
    CHECK(pPose->localTransforms[0].translation[0] == doctest::Approx(2.5));
    CHECK(pPose->localTransforms[1].translation[0] == doctest::Approx(0));
    CHECK((*instances.nodeMatrix(handle, "child"))[12] == doctest::Approx(2.5));
    CHECK_FALSE(instances.sampleBlended(handle, 0, 0, {}, .1f, .1f, {1, 0, 1, {}}));
    CHECK_FALSE(instances.sampleBlended(handle, 0, 0, {}, -1, .1f));
    REQUIRE(instances.destroy(handle));
    const ModelInstanceHandle recycled = instances.create(asset);
    REQUIRE(instances.sample(recycled, 0, 0, {}));
    CHECK(instances.pose(recycled, false)->localTransforms[0].translation[0] == doctest::Approx(0));
}

TEST_CASE("Actor model yaw wraps smoothly and gait follows travelled distance")
{
    using namespace OpenYAMM::Game;
    constexpr float Degrees = std::numbers::pi_v<float> / 180.0f;
    CHECK(advanceActorModelYaw(350 * Degrees, 10 * Degrees, .1f, 100 * Degrees)
        == doctest::Approx(360 * Degrees));
    CHECK(advanceActorModelYaw(0, 180 * Degrees, .1f, 540 * Degrees) == doctest::Approx(54 * Degrees));
    CHECK(advanceActorModelYaw(1, 2, 0, 540 * Degrees) == 1);
    CHECK(advanceActorModelGait(.9f, 30, 100) == doctest::Approx(.2f));
    CHECK(advanceActorModelGait(.4f, 0, 100) == doctest::Approx(.4f));
}

TEST_CASE("Attack legs follow the motion at the attack's start and change only after a held change")
{
    using namespace OpenYAMM::Game;
    // As MM9's SetState: an attacker that moves plays its gait under the upper-body layer, one that stands the whole
    // attack.
    ActorModelAttackLegs legs;
    advanceActorModelAttackLegs(legs, true, true, 1.0f / 60);
    CHECK(legs.moving);
    // The AI stops and runs it again from one step to the next: a stop shorter than the hold keeps the gait.
    for (int frame = 0; frame < 10; ++frame)
    {
        advanceActorModelAttackLegs(legs, false, frame % 3 != 0, 1.0f / 60);
    }
    CHECK(legs.moving);
    // A stop that lasts the hold puts the legs into the attack pose.
    for (int frame = 0; frame < 16; ++frame)
    {
        advanceActorModelAttackLegs(legs, false, false, 1.0f / 60);
    }
    CHECK_FALSE(legs.moving);
    CHECK(legs.disagreeSeconds == 0.0f);
    // A new attack takes the body's motion at once.
    advanceActorModelAttackLegs(legs, true, true, 1.0f / 60);
    CHECK(legs.moving);
    advanceActorModelAttackLegs(legs, true, false, 1.0f / 60);
    CHECK_FALSE(legs.moving);
}

TEST_CASE("Gait changes only after the new choice has held")
{
    using namespace OpenYAMM::Game;
    float held = 0.0f;
    // A fleeing Bandit near the walk/run boundary: single frames choosing the walk keep the run.
    CHECK(holdActorModelGait(ActorModelGait::Run, ActorModelGait::Walk, held, .1f) == ActorModelGait::Run);
    CHECK(holdActorModelGait(ActorModelGait::Run, ActorModelGait::Run, held, .1f) == ActorModelGait::Run);
    CHECK(held == 0.0f);
    CHECK(holdActorModelGait(ActorModelGait::Run, ActorModelGait::Walk, held, .2f) == ActorModelGait::Run);
    CHECK(holdActorModelGait(ActorModelGait::Run, ActorModelGait::Walk, held, .15f) == ActorModelGait::Walk);
    CHECK(held == 0.0f);
}

TEST_CASE("Gait advances smoothly between AI steps and covers the distance travelled")
{
    using namespace OpenYAMM::Game;
    // A body at 256 units a second stepping 2 units 128 times a second, drawn at 300 frames a second: most frames see
    // no step, some a whole one.
    float lead = 0.0f;
    float travelled = 0.0f;
    float advanced = 0.0f;
    float smallest = 1.0e9f;
    float largest = 0.0f;
    const float frameSeconds = 1.0f / 300.0f;
    float stepClock = 0.0f;

    for (int frame = 0; frame < 300; ++frame)
    {
        stepClock += frameSeconds;
        float distance = 0.0f;

        while (stepClock >= 1.0f / 128.0f)
        {
            stepClock -= 1.0f / 128.0f;
            distance += 2.0f;
        }

        travelled += distance;
        const float advance = smoothActorModelGaitDistance(lead, distance, 256.0f, frameSeconds);
        advanced += advance;

        if (frame > 10)
        {
            smallest = std::min(smallest, advance);
            largest = std::max(largest, advance);
        }
    }

    // Every frame advances by about the speed's share (not 0 or a whole step), and the gait stays within the
    // smoothing band of the distance travelled.
    CHECK(smallest == doctest::Approx(256.0f * frameSeconds).epsilon(0.01));
    CHECK(largest == doctest::Approx(256.0f * frameSeconds).epsilon(0.01));
    CHECK(std::abs(travelled - advanced) <= 256.0f * ActorModelGaitSmoothingSeconds + 1e-3f);
    // Stopping advances what is left of the last step, and nothing more.
    const float rest = smoothActorModelGaitDistance(lead, 0.0f, 0.0f, frameSeconds);
    CHECK(std::abs(advanced + rest - travelled) <= 256.0f * ActorModelGaitSmoothingSeconds + 1e-3f);
    CHECK(lead == 0.0f);
    // A body pushing against a wall (speed, no travel) does not run its gait ahead of it.
    float blockedLead = 0.0f;
    float blockedAdvance = 0.0f;

    for (int frame = 0; frame < 60; ++frame)
    {
        blockedAdvance += smoothActorModelGaitDistance(blockedLead, 0.0f, 256.0f, 1.0f / 60.0f);
    }

    CHECK(blockedAdvance <= 256.0f * ActorModelGaitSmoothingSeconds + 1e-3f);
}

TEST_CASE("MM9 skirmisher footwork backpedals only while it backs off or in the first half of an evade")
{
    using namespace OpenYAMM::Game;
    CHECK(skirmishBackpedals(ActorSkirmishPhase::BackOff, .2f, 2));
    CHECK(skirmishBackpedals(ActorSkirmishPhase::Evade, 1.5f, 2));
    CHECK_FALSE(skirmishBackpedals(ActorSkirmishPhase::Evade, .9f, 2));
    CHECK_FALSE(skirmishBackpedals(ActorSkirmishPhase::Circle, 1, 2));
    CHECK_FALSE(skirmishBackpedals(ActorSkirmishPhase::StrafeAttack, 1, 2));
    CHECK_FALSE(skirmishBackpedals(ActorSkirmishPhase::BackOff, 0, 2));
}

TEST_CASE("Actor model locomotion prefers walking to wander and running or sprinting to chase, within each clip's authored speed")
{
    using namespace OpenYAMM::Game;
    constexpr ActorModelGait Walk = ActorModelGait::Walk;
    constexpr ActorModelGait Run = ActorModelGait::Run;
    constexpr ActorModelGait Sprint = ActorModelGait::Sprint;
    // MM8 Necromancer: walk 0.93 m/s, run 1.16 m/s authored; it wanders at 1.77 and chases at 3.54.
    CHECK(actorModelGait(1.77f, {.93f, 1.16f, 0}, false, Walk) == Walk);
    CHECK(actorModelGait(3.54f, {.93f, 1.16f, 0}, true, Walk) == Run);
    // Pirate Mage chasing at 1.01 m/s: its 5.44 m/s run would crawl at a fifth of its rate, so it walks.
    CHECK(actorModelGait(1.01f, {1.77f, 5.44f, 0}, true, Walk) == Walk);
    // Pirate Warrior chasing at 3.15 m/s: a 1.59 m/s walk at 2x beats a 5.29 m/s sprint in slow motion at 0.6x.
    CHECK(actorModelGait(3.15f, {1.59f, 5.29f, 0}, true, Walk) == Walk);
    CHECK(actorModelGait(3.15f, {1.59f, 3.5f, 0}, true, Walk) == Run);
    // Dire Wolf wandering at 1.16 m/s: its 0.34 m/s walk would scurry at 3.4x, so it trots its 0.77 m/s run.
    CHECK(actorModelGait(1.16f, {.34f, .77f, 0}, false, Walk) == Run);
    // Near the boundary (1.357 m/s for these clips, wandering) the clip playing now holds; without speeds the hurry
    // decides.
    CHECK(actorModelGait(1.36f, {.5f, 2.0f, 0}, false, Run) == Run);
    CHECK(actorModelGait(1.36f, {.5f, 2.0f, 0}, false, Walk) == Walk);
    CHECK(actorModelGait(0, {1, 2, 0}, true, Walk) == Run);
    // A chaser at twice its run's speed (MAW's fast melee monsters) sprints when it has a sprint twice as long; at
    // 1.3x of the run it keeps running, and the sprint holds its margin near the boundary (run x1.59).
    CHECK(actorModelGait(4.0f, {1, 2, 4}, true, Run) == Sprint);
    CHECK(actorModelGait(2.6f, {1, 2, 4}, true, Run) == Run);
    CHECK(actorModelGait(3.12f, {1, 2, 4}, true, Sprint) == Sprint);
    CHECK(actorModelGait(3.12f, {1, 2, 4}, true, Run) == Run);
    // MM9's gait (`gait: intent`) follows the AI. Sturmford's boy wanders at 1.28 m/s: walk 0.71, run 1.34 authored;
    // the speed chooser jogs its run at 0.95x, MM9 walks it (x1.8).
    CHECK(actorModelGait(1.28f, {.71f, 1.34f, 0}, false, Walk) == Run);
    CHECK(actorModelIntendedGait(1.28f, {.71f, 1.34f, 0}, false, Walk, 2) == Walk);
    CHECK(actorModelIntendedGait(3.2f, {.71f, 1.34f, 0}, true, Walk, 2) == Run);
    // A walk past the window gives way to a run inside it (the Grey Wolf trots); with nothing inside it the AI's clip
    // plays when it is only too fast (a dwarf, walk x5, run x2.9), never a run in slow motion (Giant: walk x1.89, run
    // x0.59; Phantom Fighter: walk x2.56, run x0.47); the clip playing now keeps its margin at the edge; uncapped:
    // always the AI's.
    CHECK(actorModelIntendedGait(3.84f, {2.03f, 6.5f, 0}, true, Run, 2) == Walk);
    CHECK(actorModelIntendedGait(3.84f, {1.5f, 8.25f, 0}, true, Run, 2) == Walk);
    CHECK(actorModelIntendedGait(3.58f, {.87f, 4.18f, 0}, false, Walk, 2) == Run);
    CHECK(actorModelIntendedGait(1.92f, {.39f, .66f, 0}, false, Walk, 2) == Walk);
    CHECK(actorModelIntendedGait(2.1f, {1, 2.5f, 0}, false, Walk, 2) == Walk);
    CHECK(actorModelIntendedGait(2.1f, {1, 2.5f, 0}, false, Run, 2) == Run);
    CHECK(actorModelIntendedGait(1.95f, {1, 2.5f, 0}, false, Run, 2) == Walk);
    CHECK(actorModelIntendedGait(5, {1, 4, 0}, false, Walk, 0) == Walk);
    // Hurrying, the run or sprint that suits the speed better: both are the AI's run (the MM9 wolf chases on its
    // Running at 1.47x, not its Trot at 1.85x).
    CHECK(actorModelIntendedGait(5, {1, 2, 4}, true, Run, 2) == Sprint);
    CHECK(actorModelIntendedGait(2.2f, {1, 2, 4}, true, Run, 2) == Run);
    // By default the gait advances by the distance travelled, however fast, so the feet do not slide.
    CHECK(actorModelGaitDistance(5, 50, .1f, 1) == doctest::Approx(5));
    CHECK(actorModelGaitDistance(100, 50, .1f, 1) == doctest::Approx(100));
    // A flier drifting slowly keeps beating at its minimum rate and glides past its maximum.
    CHECK(actorModelGaitDistance(1, 50, .1f, 1, .8f, 1.5f) == doctest::Approx(4));
    CHECK(actorModelGaitDistance(100, 50, .1f, 1, .8f, 1.5f) == doctest::Approx(7.5f));
    // The default ceiling: a walker at 5x its clip pedals at 2x and slides the rest.
    CHECK(actorModelGaitDistance(25, 50, .1f, 1, 0, ActorModelDefaultMaxGaitRate) == doctest::Approx(10));
}

TEST_CASE("Actor model gait keeps pace and turns along a wall that slows its body")
{
    using namespace OpenYAMM::Game;
    constexpr float Degrees = std::numbers::pi_v<float> / 180.0f;
    // Unhindered, or hindered a little, the gait follows the body; pushing nearly head-on it keeps 60 % of its pace.
    CHECK(actorModelGaitSpeed(200, 200) == doctest::Approx(200));
    CHECK(actorModelGaitSpeed(150, 200) == doctest::Approx(150));
    CHECK(actorModelGaitSpeed(30, 200) == doctest::Approx(120));
    CHECK(actorModelGaitSpeed(0, 200) == doctest::Approx(120));
    // Knocked back or drifting without trying to move, it follows the body alone.
    CHECK(actorModelGaitSpeed(50, 0) == doctest::Approx(50));
    // Sliding sideways along a wall it faces the slide; backing away it keeps the AI's yaw, with a margin.
    CHECK(actorModelFacesMovement(0, std::cos(90 * Degrees), std::sin(90 * Degrees), false));
    CHECK(actorModelFacesMovement(0, std::cos(95 * Degrees), std::sin(95 * Degrees), false));
    CHECK_FALSE(actorModelFacesMovement(0, std::cos(100 * Degrees), std::sin(100 * Degrees), false));
    CHECK(actorModelFacesMovement(0, std::cos(105 * Degrees), std::sin(105 * Degrees), true));
    CHECK_FALSE(actorModelFacesMovement(0, std::cos(115 * Degrees), std::sin(115 * Degrees), true));
    CHECK_FALSE(actorModelFacesMovement(0, -1, 0, true));
    CHECK_FALSE(actorModelFacesMovement(0, 0, 0, true));
}

TEST_CASE("Loot satchel tiers follow the corpse's loot value, and the satchel appears as the body dissolves")
{
    using namespace OpenYAMM::Game;
    CHECK(corpseSatchelTier(0) == 0);
    CHECK(corpseSatchelTier(1) == 1);
    CHECK(corpseSatchelTier(99) == 1);
    CHECK(corpseSatchelTier(100) == 2);
    CHECK(corpseSatchelTier(749) == 2);
    CHECK(corpseSatchelTier(750) == 3);
    CHECK(corpseSatchelTier(2999) == 3);
    CHECK(corpseSatchelTier(3000) == 4);
    CHECK(corpseSatchelTier(7999) == 4);
    CHECK(corpseSatchelTier(8000) == 5);
    CHECK(corpseSatchelTier(14999) == 5);
    CHECK(corpseSatchelTier(15000) == 6);
    CHECK(corpseSatchelTier(1000000) == 6);

    const CorpseSinkPresentation resting = corpseSinkPresentation(CorpseRestSeconds * 0.5f);
    CHECK(resting.depthFraction == 0.0f);
    CHECK(resting.coverage == 1.0f);
    CHECK(resting.satchelCoverage == 0.0f);
    CHECK_FALSE(resting.gone);
    // Body and satchel cross over: the satchel is fully shown while the body is still dissolving.
    const CorpseSinkPresentation shown = corpseSinkPresentation(CorpseRestSeconds + CorpseSatchelAppearSeconds);
    CHECK(shown.satchelCoverage == 1.0f);
    CHECK(shown.satchelScale == doctest::Approx(1.0f));
    CHECK(shown.coverage > 0.0f);
    CHECK(shown.coverage < 1.0f);
    CHECK_FALSE(shown.gone);
    CHECK(corpseSinkPresentation(CorpseRestSeconds + CorpseSatchelAppearSeconds * 0.75f).satchelScale > 1.0f);
    const CorpseSinkPresentation sunk = corpseSinkPresentation(CorpseRestSeconds + CorpseSinkSeconds);
    CHECK(sunk.gone);
    CHECK(sunk.coverage == 0.0f);
    CHECK(sunk.depthFraction == 1.0f);
    CHECK(sunk.satchelCoverage == 1.0f);
    CHECK(CorpseRestSeconds + CorpseSinkSeconds <= 1.0f);
}

std::filesystem::path makeTemporaryRoot()
{
    const uint64_t ticks = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_model_" + std::to_string(ticks));
}

void appendFloat(std::vector<uint8_t> &bytes, float value)
{
    const size_t offset = bytes.size();
    bytes.resize(offset + sizeof(value));
    std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

void appendUInt16(std::vector<uint8_t> &bytes, uint16_t value)
{
    bytes.push_back(static_cast<uint8_t>(value & 0xff));
    bytes.push_back(static_cast<uint8_t>((value >> 8) & 0xff));
}

void appendUInt32(std::vector<uint8_t> &bytes, uint32_t value)
{
    bytes.push_back(static_cast<uint8_t>(value & 0xff));
    bytes.push_back(static_cast<uint8_t>((value >> 8) & 0xff));
    bytes.push_back(static_cast<uint8_t>((value >> 16) & 0xff));
    bytes.push_back(static_cast<uint8_t>((value >> 24) & 0xff));
}

void writeUInt16(std::ofstream &stream, uint16_t value)
{
    stream.put(static_cast<char>(value & 0xff));
    stream.put(static_cast<char>((value >> 8) & 0xff));
}

void writeUInt32(std::ofstream &stream, uint32_t value)
{
    stream.put(static_cast<char>(value & 0xff));
    stream.put(static_cast<char>((value >> 8) & 0xff));
    stream.put(static_cast<char>((value >> 16) & 0xff));
    stream.put(static_cast<char>((value >> 24) & 0xff));
}

uint32_t crc32(const std::vector<uint8_t> &bytes)
{
    uint32_t crc = 0xffffffffu;
    for (uint8_t byte : bytes)
    {
        crc ^= byte;
        for (int bit = 0; bit < 8; ++bit)
        {
            crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
        }
    }
    return crc ^ 0xffffffffu;
}

void writeFile(const std::filesystem::path &path, const std::string &text)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream stream(path, std::ios::binary);
    stream << text;
}

void writeFile(const std::filesystem::path &path, const std::vector<uint8_t> &bytes)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream stream(path, std::ios::binary);
    stream.write(reinterpret_cast<const char *>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
}

std::vector<uint8_t> fixtureBuffer()
{
    std::vector<uint8_t> bytes;
    for (float value : std::initializer_list<float>{0, 0, 0, 1, 0, 0, 0, 1, 0})
    {
        appendFloat(bytes, value);
    }
    for (int vertex = 0; vertex < 3; ++vertex)
    {
        appendFloat(bytes, 0.0f);
        appendFloat(bytes, 0.0f);
        appendFloat(bytes, 1.0f);
    }
    for (float value : std::initializer_list<float>{0, 0, 1, 0, 0, 1})
    {
        appendFloat(bytes, value);
    }
    appendUInt16(bytes, 0);
    appendUInt16(bytes, 1);
    appendUInt16(bytes, 2);
    appendUInt16(bytes, 0);
    appendUInt16(bytes, 2);
    appendUInt16(bytes, 1);
    appendFloat(bytes, 0.0f);
    appendFloat(bytes, 1.0f);
    for (float value : std::initializer_list<float>{0, 0, 0, 2, 0, 0})
    {
        appendFloat(bytes, value);
    }
    for (float value : std::initializer_list<float>{1, 1, 1, 2, 2, 2})
    {
        appendFloat(bytes, value);
    }
    return bytes;
}

std::string fixtureGltf(const std::string &interpolation = "LINEAR")
{
    return R"({
  "asset": {"version": "2.0"},
  "scene": 0,
  "scenes": [{"nodes": [1]}],
  "nodes": [
    {"name": "attachment", "mesh": 0, "translation": [1, 0, 0]},
    {"name": "root", "children": [0], "translation": [10, 0, 0]}
  ],
  "meshes": [{"name": "triangle", "primitives": [{
    "attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, "indices": 3, "material": 0
  }]}],
  "materials": [{"name": "opaque", "pbrMetallicRoughness": {"baseColorFactor": [1, 0.5, 0.25, 1]}}],
  "animations": [
    {"name": "move", "samplers": [{"input": 4, "output": 5, "interpolation": ")" + interpolation + R"("}],
     "channels": [{"sampler": 0, "target": {"node": 0, "path": "translation"}}]},
    {"name": "grow", "samplers": [{"input": 4, "output": 6, "interpolation": "STEP"}],
     "channels": [{"sampler": 0, "target": {"node": 0, "path": "scale"}}]}
  ],
  "buffers": [{"uri": "fixture.bin", "byteLength": 164}],
  "bufferViews": [
    {"buffer": 0, "byteOffset": 0, "byteLength": 36},
    {"buffer": 0, "byteOffset": 36, "byteLength": 36},
    {"buffer": 0, "byteOffset": 72, "byteLength": 24},
    {"buffer": 0, "byteOffset": 96, "byteLength": 12},
    {"buffer": 0, "byteOffset": 108, "byteLength": 8},
    {"buffer": 0, "byteOffset": 116, "byteLength": 24},
    {"buffer": 0, "byteOffset": 140, "byteLength": 24}
  ],
  "accessors": [
    {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3"},
    {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
    {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC2"},
    {"bufferView": 3, "componentType": 5123, "count": 6, "type": "SCALAR"},
    {"bufferView": 4, "componentType": 5126, "count": 2, "type": "SCALAR"},
    {"bufferView": 5, "componentType": 5126, "count": 2, "type": "VEC3"},
    {"bufferView": 6, "componentType": 5126, "count": 2, "type": "VEC3"}
  ]
})";
}

std::vector<uint8_t> fixtureGlb()
{
    std::string json = fixtureGltf();
    const std::string externalUri = "\"uri\": \"fixture.bin\", ";
    const size_t uriOffset = json.find(externalUri);
    if (uriOffset == std::string::npos)
    {
        throw std::runtime_error("fixture glTF has no external buffer URI");
    }
    json.erase(uriOffset, externalUri.size());
    while (json.size() % 4 != 0)
    {
        json.push_back(' ');
    }
    std::vector<uint8_t> binary = fixtureBuffer();
    while (binary.size() % 4 != 0)
    {
        binary.push_back(0);
    }

    std::vector<uint8_t> glb;
    appendUInt32(glb, 0x46546c67u);
    appendUInt32(glb, 2);
    appendUInt32(glb, static_cast<uint32_t>(12 + 8 + json.size() + 8 + binary.size()));
    appendUInt32(glb, static_cast<uint32_t>(json.size()));
    appendUInt32(glb, 0x4e4f534au);
    glb.insert(glb.end(), json.begin(), json.end());
    appendUInt32(glb, static_cast<uint32_t>(binary.size()));
    appendUInt32(glb, 0x004e4942u);
    glb.insert(glb.end(), binary.begin(), binary.end());
    return glb;
}

void writeZipFile(
    const std::filesystem::path &path,
    const std::vector<std::pair<std::string, std::vector<uint8_t>>> &files)
{
    struct Entry
    {
        std::string name;
        uint32_t checksum = 0;
        uint32_t size = 0;
        uint32_t offset = 0;
    };

    std::filesystem::create_directories(path.parent_path());
    std::ofstream stream(path, std::ios::binary);
    std::vector<Entry> entries;
    for (const auto &[name, bytes] : files)
    {
        const Entry entry = {
            .name = name,
            .checksum = crc32(bytes),
            .size = static_cast<uint32_t>(bytes.size()),
            .offset = static_cast<uint32_t>(stream.tellp()),
        };
        entries.push_back(entry);
        writeUInt32(stream, 0x04034b50u);
        writeUInt16(stream, 20);
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt32(stream, entry.checksum);
        writeUInt32(stream, entry.size);
        writeUInt32(stream, entry.size);
        writeUInt16(stream, static_cast<uint16_t>(name.size()));
        writeUInt16(stream, 0);
        stream.write(name.data(), static_cast<std::streamsize>(name.size()));
        stream.write(reinterpret_cast<const char *>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    }
    const uint32_t directoryOffset = static_cast<uint32_t>(stream.tellp());
    for (const Entry &entry : entries)
    {
        writeUInt32(stream, 0x02014b50u);
        writeUInt16(stream, 20);
        writeUInt16(stream, 20);
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt32(stream, entry.checksum);
        writeUInt32(stream, entry.size);
        writeUInt32(stream, entry.size);
        writeUInt16(stream, static_cast<uint16_t>(entry.name.size()));
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt16(stream, 0);
        writeUInt32(stream, 0);
        writeUInt32(stream, entry.offset);
        stream.write(entry.name.data(), static_cast<std::streamsize>(entry.name.size()));
    }
    const uint32_t directorySize = static_cast<uint32_t>(stream.tellp()) - directoryOffset;
    writeUInt32(stream, 0x06054b50u);
    writeUInt16(stream, 0);
    writeUInt16(stream, 0);
    writeUInt16(stream, static_cast<uint16_t>(entries.size()));
    writeUInt16(stream, static_cast<uint16_t>(entries.size()));
    writeUInt32(stream, directorySize);
    writeUInt32(stream, directoryOffset);
    writeUInt16(stream, 0);
}
}

TEST_CASE("ModelAnimation evaluates out-of-order hierarchies and quaternion shortest paths")
{
    using namespace OpenYAMM::Engine;
    const std::shared_ptr<ModelAsset> asset = makeAnimatedAsset();
    ModelPose pose;
    evaluateModelClip(*asset, 0, 0.5f, pose);
    evaluateModelHierarchy(*asset, identityModelMatrix(), pose);

    CHECK(pose.globalMatrices[0][12] == doctest::Approx(1.0f));
    CHECK(pose.globalMatrices[0][0] == doctest::Approx(0.0f).epsilon(0.0001));
    CHECK(pose.globalMatrices[0][1] == doctest::Approx(1.0f).epsilon(0.0001));
}

TEST_CASE("ModelAnimation glTF placement maps Y-up into OpenYAMM Z-up")
{
    using namespace OpenYAMM::Engine;
    const ModelMatrix placement = composeModelTransform(gltfModelPlacement({10.0f, 20.0f, 30.0f}));

    CHECK(placement[4] + placement[12] == doctest::Approx(10.0f));
    CHECK(placement[5] + placement[13] == doctest::Approx(20.0f));
    CHECK(placement[6] + placement[14] == doctest::Approx(31.0f));
    CHECK(placement[8] + placement[12] == doctest::Approx(10.0f));
    CHECK(placement[9] + placement[13] == doctest::Approx(21.0f));
    CHECK(placement[10] + placement[14] == doctest::Approx(30.0f));
    constexpr float HalfPi = 1.5707963267948966192f;
    // Proper rotation, not a mirror: glTF +X (a forward-facing character's left) maps to OpenYAMM -X.
    CHECK(placement[0] + placement[12] == doctest::Approx(9.0f));
    CHECK(determinant3x3(placement) > 0.0f);
    const ModelMatrix yawed = composeModelTransform(gltfModelPlacement({}, HalfPi, 2.0f));
    CHECK(yawed[0] == doctest::Approx(0.0f).epsilon(0.0001));
    CHECK(yawed[1] == doctest::Approx(-2.0f).epsilon(0.0001));
    CHECK(yawed[6] == doctest::Approx(2.0f).epsilon(0.0001));
    CHECK(yawed[8] == doctest::Approx(-2.0f).epsilon(0.0001));
}

TEST_CASE("ModelAnimation instances have independent clocks and generation-checked handles")
{
    using namespace OpenYAMM::Engine;
    const std::shared_ptr<ModelAsset> asset = makeAnimatedAsset();
    ModelInstanceSystem instances;
    const ModelInstanceHandle first = instances.create(asset);
    const ModelInstanceHandle second = instances.create(asset);
    CHECK_FALSE(instances.areNodeMarkersVisible(first));
    CHECK(instances.setNodeMarkersVisible(first, true));
    CHECK(instances.areNodeMarkersVisible(first));
    CHECK_FALSE(instances.areNodeMarkersVisible(second));
    REQUIRE(instances.play(first, "move", ModelPlaybackMode::Loop));
    REQUIRE(instances.play(second, "move", ModelPlaybackMode::Once));
    REQUIRE(instances.setTime(second, 0.5f));

    instances.update(0.25f);
    CHECK(instances.playbackTime(first) == doctest::Approx(0.25f));
    CHECK(instances.playbackTime(second) == doctest::Approx(0.75f));
    REQUIRE(instances.nodeMatrix(first, "child") != nullptr);
    REQUIRE(instances.nodeMatrix(second, "child") != nullptr);
    CHECK((*instances.nodeMatrix(first, "child"))[12] == doctest::Approx(0.5f));
    CHECK((*instances.nodeMatrix(second, "child"))[12] == doctest::Approx(1.5f));

    instances.update(0.5f);
    CHECK_FALSE(instances.isPlaying(second));
    CHECK((*instances.nodeMatrix(second, "child"))[12] == doctest::Approx(2.0f));
    REQUIRE(instances.destroy(first));
    CHECK_FALSE(instances.contains(first));
    const ModelInstanceHandle replacement = instances.create(asset);
    CHECK_EQ(replacement.index, first.index);
    CHECK_NE(replacement.generation, first.generation);
}

TEST_CASE("ModelAnimation recycled instances drop the previous model's node rotations")
{
    using namespace OpenYAMM::Engine;
    const std::shared_ptr<ModelAsset> asset = makeAnimatedAsset();
    ModelInstanceSystem instances;
    const ModelInstanceHandle looking = instances.create(asset);
    const float half = std::numbers::sqrt2_v<float> * 0.5f;
    REQUIRE(instances.setNodeRotations(looking, {{1, {0.0f, 0.0f, half, half}}}));
    REQUIRE(instances.nodeMatrix(looking, "child") != nullptr);
    CHECK((*instances.nodeMatrix(looking, "child"))[13] == doctest::Approx(1.0f));
    REQUIRE(instances.destroy(looking));

    // The look-at of a destroyed actor must not carry over to the model that reuses its slot.
    const ModelInstanceHandle replacement = instances.create(asset);
    REQUIRE_EQ(replacement.index, looking.index);
    REQUIRE(instances.nodeMatrix(replacement, "child") != nullptr);
    CHECK((*instances.nodeMatrix(replacement, "child"))[12] == doctest::Approx(1.0f));
    CHECK((*instances.nodeMatrix(replacement, "child"))[13] == doctest::Approx(0.0f));
}

TEST_CASE("ModelAnimation stand-in minimum size changes the stand-in revision and resets with the slot")
{
    using namespace OpenYAMM::Engine;
    const std::shared_ptr<ModelAsset> asset = makeAnimatedAsset();
    ModelInstanceSystem instances;
    const ModelInstanceHandle item = instances.create(asset);
    REQUIRE(instances.setStaticStandIn(item, asset, 8.0f));
    CHECK(instances.staticStandInMinimumPixels(item) == doctest::Approx(8.0f));

    // Renderers keep their stand-in groups while the revision holds, so a new minimum must change it.
    const uint64_t revision = instances.standInRevision();
    REQUIRE(instances.setStaticStandIn(item, asset, 8.0f));
    CHECK_EQ(instances.standInRevision(), revision);
    REQUIRE(instances.setStaticStandIn(item, asset, 4.0f));
    CHECK_NE(instances.standInRevision(), revision);
    CHECK(instances.staticStandInMinimumPixels(item) == doctest::Approx(4.0f));

    REQUIRE(instances.destroy(item));
    const ModelInstanceHandle corpse = instances.create(asset);
    REQUIRE_EQ(corpse.index, item.index);
    REQUIRE(instances.setStaticStandIn(corpse, asset));
    CHECK(instances.staticStandInMinimumPixels(corpse) == doctest::Approx(0.0f));
}

TEST_CASE("ModelAnimation loader reads external glTF buffers through AssetFileSystem")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    writeFile(assetRoot / "engine" / "models" / "fixture.gltf", fixtureGltf());
    writeFile(assetRoot / "engine" / "models" / "fixture.bin", fixtureBuffer());

    {
        AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1));
        ModelAssetCache cache;
        const ModelLoadResult loaded = cache.load(assetFileSystem, "engine/models/fixture.gltf");
        REQUIRE_MESSAGE(loaded, loaded.error.c_str());
        REQUIRE_EQ(loaded.asset->hierarchyOrder.size(), 2);
        CHECK_EQ(loaded.asset->hierarchyOrder[0], 1);
        CHECK_EQ(loaded.asset->hierarchyOrder[1], 0);
        CHECK_EQ(loaded.asset->clips.size(), 2);
        CHECK_EQ(loaded.asset->meshes[0].primitives[0].indices.size(), 6);
        CHECK(loaded.asset->staticBounds.min[0] == doctest::Approx(11.0f));
        CHECK(loaded.asset->staticBounds.max[0] == doctest::Approx(12.0f));

        ModelInstanceSystem instances;
        const ModelInstanceHandle handle = instances.create(loaded.asset);
        REQUIRE(instances.play(handle, "move", ModelPlaybackMode::Once));
        REQUIRE(instances.setTime(handle, 1.0f));
        REQUIRE(instances.bounds(handle) != nullptr);
        CHECK(instances.bounds(handle)->min[0] == doctest::Approx(12.0f));
        CHECK(instances.bounds(handle)->max[0] == doctest::Approx(13.0f));

        const ModelLoadResult cached = cache.load(assetFileSystem, "engine/models/fixture.gltf");
        REQUIRE(cached);
        CHECK_EQ(cached.asset.get(), loaded.asset.get());
        CHECK_EQ(cache.size(), 1);
        cache.clear();
        CHECK_EQ(cache.size(), 0);
    }
    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("ModelAnimation clip lengths read from a model file's JSON match the loaded model's")
{
    using namespace OpenYAMM::Engine;
    // A cooked binary model (only its JSON chunk is read) and a text glTF.
    {
        const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
        AssetFileSystem assets;
        REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", AssetScaleTier::X1));
        const ModelLoadResult loaded = GltfModelLoader().load(assets, "worlds/mm9/models/mm9_skeleton.glb");
        REQUIRE_MESSAGE(loaded, loaded.error);
        const std::optional<GltfModelSummary> summary =
            readGltfModelSummary(assets, "worlds/mm9/models/mm9_skeleton.glb");
        REQUIRE(summary);
        const std::unordered_map<std::string, float> &durations = summary->clipDurations;
        REQUIRE_EQ(durations.size(), loaded.asset->clips.size());
        for (const ModelAnimationClip &clip : loaded.asset->clips)
        {
            REQUIRE_MESSAGE(durations.contains(clip.name), clip.name);
            CHECK_MESSAGE(durations.at(clip.name) == doctest::Approx(clip.durationSeconds), clip.name);
        }
        CHECK(durations.at("AttackMelee") == doctest::Approx(0.8f).epsilon(0.01));
        CHECK_FALSE(readGltfModelSummary(assets, "worlds/mm9/models/missing.glb"));
    }

    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    writeFile(assetRoot / "engine" / "models" / "fixture.gltf", fixtureGltf());
    {
        AssetFileSystem fixtureAssets;
        REQUIRE(fixtureAssets.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1));
        const std::optional<GltfModelSummary> fixtureSummary =
            readGltfModelSummary(fixtureAssets, "engine/models/fixture.gltf");
        REQUIRE(fixtureSummary);
        const std::unordered_map<std::string, float> &fixture = fixtureSummary->clipDurations;
        CHECK_EQ(fixture.size(), 2);
        CHECK(fixture.contains("move"));
    }
    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("ModelAnimation bind pose height read from a model file's JSON matches the loaded model's")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", AssetScaleTier::X1));
    // MM8's Bone Dragon (its origin at its feet) and an MM9 townswoman (centred mesh lifted by its skeleton's bind
    // matrices, which a header-only read would put half below the ground).
    for (const char *pPath : {"worlds/mm8/models/mm8_m616.glb", "worlds/mm9/models/mm9_peasantf8.glb"})
    {
        const ModelLoadResult loaded = GltfModelLoader().load(assets, pPath);
        REQUIRE_MESSAGE(loaded, loaded.error);
        REQUIRE(loaded.asset->staticBounds.valid);
        const std::optional<GltfModelSummary> summary = readGltfModelSummary(assets, pPath);
        REQUIRE_MESSAGE(summary, pPath);
        REQUIRE_MESSAGE(summary->bindPoseHeightRange, pPath);
        const std::optional<std::array<float, 2>> &range = summary->bindPoseHeightRange;
        const float height = loaded.asset->staticBounds.max[1] - loaded.asset->staticBounds.min[1];
        CHECK_MESSAGE(std::abs((*range)[0] - loaded.asset->staticBounds.min[1]) <= 0.03f * height, pPath);
        CHECK_MESSAGE(std::abs((*range)[1] - loaded.asset->staticBounds.max[1]) <= 0.03f * height, pPath);
    }
}

TEST_CASE("ModelAnimation loader rejects unsupported interpolation explicitly")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path assetRoot = temporaryRoot / "assets_dev";
    writeFile(assetRoot / "engine" / "models" / "fixture.gltf", fixtureGltf("CUBICSPLINE"));
    writeFile(assetRoot / "engine" / "models" / "fixture.bin", fixtureBuffer());

    {
        AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(temporaryRoot, assetRoot, AssetScaleTier::X1));
        GltfModelLoader loader;
        const ModelLoadResult loaded = loader.load(assetFileSystem, "engine/models/fixture.gltf");
        CHECK_FALSE(loaded);
        CHECK(loaded.error.find("CUBICSPLINE") != std::string::npos);
    }
    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("ModelAnimation material factors retain defaults and reject invalid roughness")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path root = makeTemporaryRoot();
    std::string json = fixtureGltf();
    writeFile(root / "assets_dev/engine/models/fixture.bin", fixtureBuffer());
    AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", AssetScaleTier::X1));
    writeFile(root / "assets_dev/engine/models/fixture.gltf", json);
    const ModelLoadResult defaults = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    REQUIRE_MESSAGE(defaults, defaults.error);
    CHECK_EQ(defaults.asset->materials[0].metallic, 1.0f);
    CHECK_EQ(defaults.asset->materials[0].roughness, 1.0f);
    const size_t offset = json.find("\"baseColorFactor\"");
    REQUIRE_NE(offset, std::string::npos);
    json.insert(offset, "\"roughnessFactor\": -0.1, ");
    writeFile(root / "assets_dev/engine/models/fixture.gltf", json);
    const ModelLoadResult invalid = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    CHECK_FALSE(invalid);
    CHECK(invalid.error.find("invalid colour or surface factors") != std::string::npos);
    assets.shutdown();
    std::filesystem::remove_all(root);
}

TEST_CASE("ModelAnimation material variants share geometry and validate mappings and recycled instances")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path root = makeTemporaryRoot();
    std::string json = fixtureGltf();
    json.insert(1, R"("extensionsRequired":["KHR_materials_variants"],
        "extensions":{"KHR_materials_variants":{"variants":[{"name":"green"},{"name":"red"}]}},)");
    json.insert(json.find("\"attributes\""), R"("extensions":{"KHR_materials_variants":{
        "mappings":[{"material":1,"variants":[0]},{"material":2,"variants":[1]}]}},)");
    const size_t materialEnd = json.find("],\n  \"animations\"");
    REQUIRE_NE(materialEnd, std::string::npos);
    json.insert(materialEnd, R"(,{"name":"green","pbrMetallicRoughness":{"baseColorFactor":[0,1,0,1]}},
        {"name":"red","pbrMetallicRoughness":{"baseColorFactor":[1,0,0,1]}})");
    writeFile(root / "assets_dev/engine/models/fixture.bin", fixtureBuffer());
    writeFile(root / "assets_dev/engine/models/fixture.gltf", json);
    AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", AssetScaleTier::X1));
    ModelAssetCache cache;
    const ModelLoadResult loaded = cache.load(assets, "engine/models/fixture.gltf");
    REQUIRE_MESSAGE(loaded, loaded.error);
    REQUIRE_EQ(loaded.asset->meshes[0].primitives[0].materialIndices, std::vector<int>{0, 1, 2});
    CHECK_FALSE(loaded.asset->findMaterialVariant("missing"));
    ModelInstanceSystem instances;
    const ModelInstanceHandle first = instances.create(loaded.asset);
    const ModelInstanceHandle second = instances.create(cache.load(assets, "engine/models/fixture.gltf").asset);
    REQUIRE(instances.setMaterialVariant(first, *loaded.asset->findMaterialVariant("green")));
    REQUIRE(instances.setMaterialVariant(second, *loaded.asset->findMaterialVariant("red")));
    CHECK(instances.asset(first) == instances.asset(second));
    CHECK_EQ(instances.materialVariant(first), 1);
    CHECK_EQ(instances.materialVariant(second), 2);
    CHECK_FALSE(instances.setMaterialVariant(first, 3));
    REQUIRE(instances.destroy(first));
    CHECK_FALSE(instances.setMaterialVariant(first, 0));
    CHECK_EQ(instances.materialVariant(instances.create(loaded.asset)), 0);
    for (const std::pair<std::string, std::string> replacement : {
        std::pair{std::string("\"name\":\"red\""), std::string("\"name\":\"green\"")},
        std::pair{std::string("\"variants\":[1]"), std::string("\"variants\":[0]")},
        std::pair{std::string("\"variants\":[1]"), std::string("\"variants\":[7]")}})
    {
        std::string invalid = json;
        invalid.replace(invalid.find(replacement.first), replacement.first.size(), replacement.second);
        writeFile(root / "assets_dev/engine/models/fixture.gltf", invalid);
        CHECK_FALSE(GltfModelLoader().load(assets, "engine/models/fixture.gltf"));
    }
    assets.shutdown();
    std::filesystem::remove_all(root);
}

TEST_CASE("ModelAnimation loader reads GLB and packaged external buffers")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path temporaryRoot = makeTemporaryRoot();
    const std::filesystem::path developmentAssets = temporaryRoot / "assets_dev";
    writeFile(developmentAssets / "engine" / "models" / "fixture.glb", fixtureGlb());
    {
        AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(temporaryRoot, developmentAssets, AssetScaleTier::X1));
        const ModelLoadResult loaded = GltfModelLoader().load(assetFileSystem, "engine/models/fixture.glb");
        REQUIRE_MESSAGE(loaded, loaded.error.c_str());
        CHECK_EQ(loaded.asset->clips.size(), 2);
        CHECK_EQ(loaded.asset->meshes.size(), 1);
    }

    const std::filesystem::path packagedAssets = temporaryRoot / "assets";
    const std::string gltf = fixtureGltf();
    writeZipFile(
        packagedAssets / "packs/engine.core.zip",
        {
            {"models/fixture.gltf", std::vector<uint8_t>(gltf.begin(), gltf.end())},
            {"models/fixture.bin", fixtureBuffer()},
        });
    writeCorePackIndex(packagedAssets, {"engine"});
    {
        AssetFileSystem assetFileSystem;
        REQUIRE(assetFileSystem.initialize(temporaryRoot, packagedAssets, AssetScaleTier::X1));
        const ModelLoadResult loaded = GltfModelLoader().load(assetFileSystem, "engine/models/fixture.gltf");
        INFO(loaded.error);
        REQUIRE(loaded);
        CHECK_EQ(loaded.asset->hierarchyOrder.size(), 2);
        CHECK_EQ(loaded.asset->clips.size(), 2);
        CHECK_FALSE(assetFileSystem.resolvePhysicalPath("engine/models/fixture.bin").has_value());
    }
    std::filesystem::remove_all(temporaryRoot);
}

TEST_CASE("ModelAnimation checked-in fixture covers rendering and animation contract")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", AssetScaleTier::X1));

    const ModelLoadResult loaded = GltfModelLoader().load(
        assetFileSystem,
        "engine/models/fixtures/shared_model_fixture.glb");
    INFO(loaded.error);
    REQUIRE(loaded);
    REQUIRE_EQ(loaded.asset->nodes.size(), 3);
    REQUIRE_EQ(loaded.asset->hierarchyOrder.size(), 3);
    CHECK_EQ(loaded.asset->hierarchyOrder[0], 2);
    CHECK_EQ(loaded.asset->hierarchyOrder[1], 0);
    CHECK_EQ(loaded.asset->hierarchyOrder[2], 1);
    CHECK_EQ(loaded.asset->nodes[2].matrix[12], doctest::Approx(0.25f));
    REQUIRE_EQ(loaded.asset->meshes.size(), 1);
    CHECK_EQ(loaded.asset->meshes[0].primitives.size(), 2);
    REQUIRE_EQ(loaded.asset->materials.size(), 2);
    CHECK_EQ(loaded.asset->materials[0].alphaMode, ModelAlphaMode::Opaque);
    CHECK_EQ(loaded.asset->materials[1].alphaMode, ModelAlphaMode::Blend);
    CHECK(loaded.asset->materials[1].doubleSided);
    CHECK(loaded.asset->materials[1].unlit);
    CHECK_EQ(loaded.asset->materials[0].edgeDarkening, 0.0f);   // unskinned: no creature edge darkening
    REQUIRE_EQ(loaded.asset->images.size(), 1);
    CHECK_EQ(loaded.asset->clips.size(), 2);
    CHECK(loaded.asset->findNode("animated_attachment").has_value());

    ModelInstanceSystem instances;
    const ModelInstanceHandle handle = instances.create(loaded.asset);
    REQUIRE(instances.play(handle, "bob_spin", ModelPlaybackMode::Loop));
    const ModelMatrix *pInitial = instances.nodeMatrix(handle, "animated_attachment");
    REQUIRE(pInitial != nullptr);
    const float initialY = (*pInitial)[13];
    instances.update(1.0f);
    const ModelMatrix *pAnimated = instances.nodeMatrix(handle, "animated_attachment");
    REQUIRE(pAnimated != nullptr);
    CHECK((*pAnimated)[13] > initialY);

    const ModelLoadResult masked = GltfModelLoader().load(
        assetFileSystem, "engine/models/fixtures/masked_emissive_fixture.glb");
    INFO(masked.error);
    REQUIRE(masked);
    REQUIRE_EQ(masked.asset->materials.size(), 2);
    CHECK_EQ(masked.asset->materials[0].alphaMode, ModelAlphaMode::Mask);
    CHECK_EQ(masked.asset->materials[0].alphaCutoff, 0.75f);
    CHECK_EQ(masked.asset->materials[0].emissive[0], 0.2f);
    CHECK_EQ(masked.asset->materials[0].metallic, 0.0f);
    CHECK_EQ(masked.asset->materials[0].roughness, 0.25f);
    CHECK(masked.asset->materials[1].unlit);
}

TEST_CASE("ModelAnimation burnt corpse picking follows visible attachments and invalidates cached bounds")
{
    using namespace OpenYAMM::Engine;
    std::shared_ptr<ModelAsset> asset = makeAnimatedAsset();
    asset->nodes[1].meshIndex = 0;
    ModelPrimitive primitive;
    primitive.vertices = {{{-10, -10, -10}}, {{10, 10, 10}}};
    ModelMesh mesh;
    mesh.primitives.push_back(primitive);
    asset->meshes.push_back(mesh);
    ModelAnimationChannel visibility;
    visibility.nodeIndex = 0;
    visibility.target = ModelAnimationTarget::Scale;
    visibility.interpolation = ModelAnimationInterpolation::Step;
    visibility.times = {0, 1};
    visibility.values = {{1, 1, 1, 0}, {0, 0, 0, 0}};
    asset->clips[0].channels.push_back(visibility);
    std::shared_ptr<ModelAsset> remains = std::make_shared<ModelAsset>();
    remains->staticBounds = {{-1, -2, 0}, {1, 2, 1}, true};

    ModelInstanceSystem instances;
    const ModelInstanceHandle handle = instances.create(asset);
    ModelTransform placement;
    placement.translation = {10, 20, 30};
    REQUIRE(instances.sample(handle, 0, .5f, placement));
    REQUIRE(instances.pickingBounds(handle)->valid);
    CHECK(instances.pickingBounds(handle)->min[0] == doctest::Approx(0));
    ModelBurn burn;
    burn.front = 5;
    REQUIRE(instances.setBurn(handle, &burn));
    CHECK_FALSE(instances.pickingBounds(handle)->valid);
    REQUIRE(instances.setAttachments(handle, {{remains, 0, 0}}));
    const ModelBounds *pBounds = instances.pickingBounds(handle);
    REQUIRE(pBounds->valid);
    CHECK(pBounds->min[0] == doctest::Approx(9));
    CHECK(pBounds->max[0] == doctest::Approx(13));
    CHECK(pBounds->min[1] == doctest::Approx(19));
    CHECK(pBounds->max[1] == doctest::Approx(21));
    CHECK(pBounds->min[2] == doctest::Approx(30));
    CHECK(pBounds->max[2] == doctest::Approx(31));
    REQUIRE(instances.setAttachments(handle, {}));
    CHECK_FALSE(instances.pickingBounds(handle)->valid);
    REQUIRE(instances.setAttachments(handle, {{remains, 0, 0}}));
    REQUIRE(instances.pickingBounds(handle)->valid);
    REQUIRE(instances.sample(handle, 0, 1, placement));
    CHECK_FALSE(instances.pickingBounds(handle)->valid);
    REQUIRE(instances.setBurn(handle, nullptr));
    REQUIRE(instances.pickingBounds(handle)->valid);
    CHECK(instances.pickingBounds(handle)->min[0] == doctest::Approx(0));
    CHECK(instances.pickingBounds(handle)->max[2] == doctest::Approx(40));
}

TEST_CASE("ModelAnimation picking rays meet the coarsest LOD triangles, not their bounds")
{
    using namespace OpenYAMM::Engine;
    std::shared_ptr<ModelAsset> asset = makeAnimatedAsset();
    asset->nodes[1].meshIndex = 0;
    // Full detail: one quad across the gap. Coarsest LOD: two quads (x = 0 plane) with a gap at y = 0.
    ModelPrimitive full;
    full.vertices = {{{0, -10, -10}}, {{0, 10, -10}}, {{0, 10, 10}}, {{0, -10, 10}}};
    full.indices = {0, 1, 2, 0, 2, 3};
    ModelPrimitive coarse;
    coarse.vertices = {
        {{0, -10, -10}}, {{0, -5, -10}}, {{0, -5, 10}}, {{0, -10, 10}},
        {{0, 5, -10}}, {{0, 10, -10}}, {{0, 10, 10}}, {{0, 5, 10}}};
    coarse.indices = {0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7};
    ModelMesh fullMesh;
    fullMesh.primitives.push_back(full);
    fullMesh.lodMeshes = {1};
    ModelMesh coarseMesh;
    coarseMesh.primitives.push_back(coarse);
    asset->meshes = {fullMesh, coarseMesh};

    ModelInstanceSystem instances;
    const ModelInstanceHandle handle = instances.create(asset);
    ModelTransform placement;
    placement.translation = {100, 0, 0};
    REQUIRE(instances.sample(handle, 0, 0, placement));
    const ModelBounds *pBounds = instances.pickingBounds(handle);
    REQUIRE(pBounds->valid);
    CHECK(pBounds->min[1] == doctest::Approx(-10));
    CHECK(pBounds->max[1] == doctest::Approx(10));

    // Inside the bounds but through the gap: a miss.
    CHECK_FALSE(instances.pickRay(handle, {0, 0, 0}, {1, 0, 0}));
    const std::optional<float> front = instances.pickRay(handle, {0, -7.5f, 0}, {1, 0, 0});
    REQUIRE(front);
    CHECK(*front == doctest::Approx(100));
    // Either face: a thin wing is picked from behind too.
    const std::optional<float> back = instances.pickRay(handle, {250, 7.5f, 0}, {-1, 0, 0});
    REQUIRE(back);
    CHECK(*back == doctest::Approx(150));
    CHECK_FALSE(instances.pickRay(handle, {0, -7.5f, 0}, {-1, 0, 0}));
}

TEST_CASE("ModelAnimation skinning applies inverse bind, all influences, morphs and root placement")
{
    using namespace OpenYAMM::Engine;
    std::shared_ptr<ModelAsset> asset = makeAnimatedAsset();
    asset->nodes[0].meshIndex = 0;
    asset->nodes[0].skinIndex = 0;
    asset->nodes[0].weights = {0};
    ModelSkin skin;
    skin.joints = {1, 0};
    skin.inverseBindMatrices = {identityModelMatrix(), identityModelMatrix()};
    skin.inverseBindMatrices[1][12] = -1;
    asset->skins.push_back(skin);
    ModelPrimitive primitive;
    primitive.vertices = {{{1, 0, 0}, {0, 1, 0}, {0, 0}}};
    ModelVertexInfluences influences;
    influences.joints = {0, 0, 0, 0, 1, 1, 1, 1};
    influences.weights = {0.125f, 0.125f, 0.125f, 0.125f, 0.125f, 0.125f, 0.125f, 0.125f};
    primitive.influences.push_back(influences);
    primitive.morphTargets.push_back({{{2, 0, 0}}, {}});
    ModelMesh mesh;
    mesh.primitives.push_back(primitive);
    asset->meshes.push_back(mesh);
    ModelAnimationChannel weights;
    weights.nodeIndex = 0;
    weights.target = ModelAnimationTarget::Weights;
    weights.times = {0, 1};
    weights.weightValues = {{0}, {1}};
    // Move the joint, keeping its rotation fixed so the weighted translation is independently measurable.
    asset->clips[0].channels = {asset->clips[0].channels[0], weights};
    ModelInstanceSystem instances;
    const ModelInstanceHandle handle = instances.create(asset);
    ModelTransform transform;
    transform.translation = {10, 20, 30};
    REQUIRE(instances.sample(handle, 0, 0.5f, transform));
    CHECK(instances.bounds(handle)->min[0] == doctest::Approx(12));
    const ModelVertex &vertex = instances.pose(handle)->deformedVertices[0][0][0];
    CHECK(vertex.position[0] == doctest::Approx(12));
    CHECK(vertex.position[1] == doctest::Approx(20));
    CHECK(vertex.normal[1] == doctest::Approx(1));
    CHECK(instances.bounds(handle)->min[0] == doctest::Approx(12));
    REQUIRE(instances.sample(handle, 0, 1, transform));
    CHECK(instances.pose(handle)->deformedVertices[0][0][0].position[0] == doctest::Approx(13.5));
    weights.interpolation = ModelAnimationInterpolation::Step;
    asset->clips[0].channels[1] = weights;
    REQUIRE(instances.sample(handle, 0, 1, transform));
    CHECK(instances.pose(handle)->morphWeights[0][0] == doctest::Approx(1));
    asset->clips[0].channels[1].weightValues = {{-2}, {1}};
    REQUIRE(instances.sample(handle, 0, 0, transform));
    const ModelBounds conservative = *instances.cullingBounds(handle);
    const ModelBounds exact = *instances.bounds(handle);
    CHECK(conservative.min[0] <= exact.min[0]);
    CHECK(conservative.max[0] >= exact.max[0]);
}

TEST_CASE("ModelAnimation MM6 demon loads all native clips and keeps its body for the death burn")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", AssetScaleTier::X1));
    const ModelLoadResult loaded = GltfModelLoader().load(assets, "worlds/mm6/models/mm6_demon.glb");
    REQUIRE_MESSAGE(loaded, loaded.error);
    REQUIRE_EQ(loaded.asset->skins.size(), 1);
    CHECK_EQ(loaded.asset->skins[0].joints.size(), 85);
    // Ten native clips plus the 2026-10-31 gait rollout's Walk2, Jog and Sprint.
    CHECK_EQ(loaded.asset->clips.size(), 13);
    CHECK(loaded.asset->findClip("Sprint"));
    for (const ModelMaterial &material : loaded.asset->materials)
    {
        if (material.name == "Demon_Meshy_Body")
        {
            CHECK_EQ(material.metallic, 0.0f);
            CHECK_EQ(material.metallicRoughnessImageIndex, 2);
            CHECK_EQ(material.baseSampler.minFilter, 9987);
            CHECK_EQ(material.baseSampler.wrapS, 10497);
        }
        else if (material.name == "Demon_Iris")
        {
            CHECK_EQ(material.metallic, 0.0f);
            CHECK(material.roughness == doctest::Approx(0.22f));
        }
    }
    ModelInstanceSystem instances;
    const ModelInstanceHandle handle = instances.create(loaded.asset);
    REQUIRE(loaded.asset->findNode("Demon_Native_Mesh"));
    REQUIRE(loaded.asset->findNode("Demon_Death_Plume"));
    const uint32_t body = *loaded.asset->findNode("Demon_Native_Mesh");
    const uint32_t plume = *loaded.asset->findNode("Demon_Death_Plume");
    REQUIRE_EQ(loaded.asset->materialVariants, std::vector<std::string>{"demon_a", "demon_b", "demon_c"});
    const std::array<std::array<uint8_t, 3>, 3> eyeColors = {{{231, 156, 156}, {250, 102, 102}, {250, 176, 62}}};
    const uint32_t bodyMesh = loaded.asset->nodes[body].meshIndex;
    std::vector<uint32_t> colorMeshes = loaded.asset->meshes[bodyMesh].lodMeshes;
    colorMeshes.push_back(bodyMesh);
    for (uint32_t mesh : colorMeshes)
    {
        REQUIRE(loaded.asset->meshes[mesh].primitives.size() >= 3);
        const ModelPrimitive &iris = loaded.asset->meshes[mesh].primitives[1];
        const ModelPrimitive &pupil = loaded.asset->meshes[mesh].primitives[2];
        REQUIRE_EQ(iris.materialIndices.size(), 4);
        for (size_t variant = 0; variant < eyeColors.size(); ++variant)
        {
            const ModelMaterial &material = loaded.asset->materials[iris.materialIndices[variant + 1]];
            CHECK_EQ(material.name, loaded.asset->materialVariants[variant] + "_Iris");
            for (size_t channel = 0; channel < 3; ++channel)
            {
                CHECK(material.baseColor[channel]
                    == doctest::Approx(srgbToLinear(eyeColors[variant][channel] / 255.0f)));
                CHECK(loaded.asset->materials[pupil.materialIndices[variant + 1]].baseColor[channel] < 0.005f);
            }
        }
    }
    // The portable authoring effect is replaced by batched runtime particles.
    CHECK_EQ(loaded.asset->nodes[plume].meshIndex, -1);
    CHECK(loaded.asset->nodes[plume].weights.empty());
    for (const ModelMesh &mesh : loaded.asset->meshes)
    {
        for (const ModelPrimitive &primitive : mesh.primitives)
        {
            CHECK(primitive.morphTargets.empty());
        }
    }
    // The death is 25 % slower than the native one (level_generation/creatures/mm6_demon_reduce_claude).
    const std::array<std::pair<const char *, float>, 8> nativeClips = {{{"Standing", .125f}, {"Walk_Native", 1.125f},
        {"Attack", .75f}, {"Hit", .75f}, {"Fidget", .625f}, {"Death", 1.5625f}, {"Dead", 1.0f},
        {"Cast_FireBolt", 1.0f}}};
    for (const auto &[name, duration] : nativeClips)
    {
        REQUIRE_MESSAGE(loaded.asset->findClip(name), name);
        const uint32_t clip = *loaded.asset->findClip(name);
        CHECK(loaded.asset->clips[clip].durationSeconds == doctest::Approx(duration));
        REQUIRE(instances.sample(handle, clip, duration * .5f, gltfModelPlacement({1, 2, 3}, 0, 100)));
        // The engine burn (actors.yml death_effect) consumes the body, so no clip hides it.
        CHECK(instances.bounds(handle)->valid);
        for (const auto &node : instances.pose(handle)->deformedVertices)
        {
            for (const auto &primitive : node)
            {
                for (const ModelVertex &vertex : primitive)
                {
                    if (!std::isfinite(vertex.position[0]) || !std::isfinite(vertex.position[1])
                        || !std::isfinite(vertex.position[2]))
                    {
                        FAIL("Non-finite deformed vertex");
                    }
                }
            }
        }
    }
    // Only the death clips scale the plume marker on; leaving them restores it to zero.
    for (const char *name : {"Death", "Dead"})
    {
        REQUIRE(instances.sample(handle, *loaded.asset->findClip(name), 0, {}));
        REQUIRE(instances.nodeMatrix(handle, plume) != nullptr);
        CHECK(modelMatrixVisible(*instances.nodeMatrix(handle, body)));
        CHECK(modelMatrixVisible(*instances.nodeMatrix(handle, plume)));
    }
    REQUIRE(instances.sample(handle, *loaded.asset->findClip("Standing"), 0, {}));
    CHECK(modelMatrixVisible(*instances.nodeMatrix(handle, body)));
    CHECK_FALSE(modelMatrixVisible(*instances.nodeMatrix(handle, plume)));
    for (float weight : instances.pose(handle)->morphWeights[plume])
    {
        CHECK(weight == 0.0f);
    }
    CHECK(instances.bounds(handle)->max[1] == doctest::Approx(1.707f).epsilon(.01));
    REQUIRE(instances.sample(handle, *loaded.asset->findClip("Cast_FireBolt"), .65f, {}));
    CHECK(modelMatrixVisible(*instances.nodeMatrix(handle, body)));
    CHECK_FALSE(modelMatrixVisible(*instances.nodeMatrix(handle, plume)));
    for (const char *socket : {"Socket_Eye_Left", "Socket_Eye_Right", "Socket_Palm_Left", "Socket_Palm_Right"})
    {
        CHECK(instances.nodeMatrix(handle, socket) != nullptr);
    }
}

TEST_CASE("ModelAnimation defers crowd deformation and bounds contain every demon animation")
{
    using namespace OpenYAMM::Engine;
    AssetFileSystem assets;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", AssetScaleTier::X1));
    const ModelLoadResult loaded = GltfModelLoader().load(assets, "worlds/mm6/models/mm6_demon.glb");
    REQUIRE_MESSAGE(loaded, loaded.error);
    ModelInstanceSystem instances;
    const ModelInstanceHandle first = instances.create(loaded.asset);
    const ModelInstanceHandle second = instances.create(loaded.asset);
    const ModelPose *pPose = instances.pose(first, false);
    const uint32_t body = *loaded.asset->findNode("Demon_Native_Mesh");
    for (const std::vector<ModelVertex> &primitive : pPose->deformedVertices[body])
    {
        CHECK(primitive.empty());
    }
    uint64_t revision = pPose->deformationRevision;
    for (uint32_t clip = 0; clip < loaded.asset->clips.size(); ++clip)
    {
        for (float fraction : {0.0f, 0.2f, 0.5f, 0.8f, 1.0f})
        {
            ModelTransform placement = gltfModelPlacement({-9728, -11319, 161}, fraction * 6.0f, 104.8623316f);
            placement.scale[0] *= 0.7f;
            placement.scale[2] *= 1.3f;
            const float time = loaded.asset->clips[clip].durationSeconds * fraction;
            REQUIRE(instances.sample(first, clip, time, placement));
            const ModelBounds conservative = *instances.cullingBounds(first);
            const ModelBounds envelope = *instances.motionBounds(first);
            CHECK(pPose->deformationRevision == revision);
            REQUIRE(instances.nodeMatrix(first, 0) != nullptr);
            CHECK(pPose->deformationRevision == revision);
            const ModelBounds exact = *instances.bounds(first);
            CHECK(pPose->deformationRevision == revision);
            CHECK(conservative.valid == exact.valid);
            if (exact.valid)
            {
                for (size_t axis = 0; axis < 3; ++axis)
                {
                    CHECK(conservative.min[axis] <= exact.min[axis] + 0.01f);
                    CHECK(conservative.max[axis] >= exact.max[axis] - 0.01f);
                    CHECK(envelope.min[axis] <= exact.min[axis] + 0.01f);
                    CHECK(envelope.max[axis] >= exact.max[axis] - 0.01f);
                }
            }
            REQUIRE(instances.sample(first, clip, time, placement));
            CHECK(instances.bounds(first)->min == exact.min);
            CHECK(instances.pose(first)->deformationRevision == revision + 1);
            revision = pPose->deformationRevision;
            const ModelBounds cpuVertices = *instances.bounds(first);
            CHECK(cpuVertices.valid == exact.valid);
            for (size_t axis = 0; axis < 3; ++axis)
            {
                CHECK(cpuVertices.min[axis] == doctest::Approx(exact.min[axis]));
                CHECK(cpuVertices.max[axis] == doctest::Approx(exact.max[axis]));
            }
        }
    }
    // A second instance has its own pose and does not inherit the first actor's deformation.
    CHECK(instances.pose(second)->deformationRevision == 1);
    REQUIRE(instances.destroy(first));
    const ModelInstanceHandle reused = instances.create(loaded.asset);
    CHECK(reused.index == first.index);
    CHECK(reused.generation != first.generation);
    CHECK(instances.pose(reused)->deformationRevision == 1);
}

TEST_CASE("ModelAnimation demon LOD meshes share the rig and retain posed bounds across all clips")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path root = OPENYAMM_SOURCE_DIR;
    AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", AssetScaleTier::X1));
    const ModelLoadResult loaded = GltfModelLoader().load(assets, "worlds/mm6/models/mm6_demon.glb");
    REQUIRE_MESSAGE(loaded, loaded.error);
    const ModelAsset &asset = *loaded.asset;
    const uint32_t nodeIndex = *asset.findNode("Demon_Native_Mesh");
    const ModelMesh &mesh = asset.meshes[asset.nodes[nodeIndex].meshIndex];
    REQUIRE(mesh.lodMeshes.size() == 3);
    REQUIRE(mesh.shadowMeshes.size() == 4);
    // The installed 55 % reduction (level_generation/creatures/mm6_demon_reduce_claude); levels 2 and 3 from the
    // monster LOD rebuild of 2026-10-22 (tools/build_actor_lods.py).
    const std::array<size_t, 4> triangles = {9060, 4512, 2716, 1455};
    for (size_t level = 0; level < 4; ++level)
    {
        const uint32_t meshIndex = level == 0 ? uint32_t(asset.nodes[nodeIndex].meshIndex) : mesh.lodMeshes[level - 1];
        size_t indices = 0;
        for (const ModelPrimitive &primitive : asset.meshes[meshIndex].primitives)
        {
            indices += primitive.indices.size();
            CHECK(primitive.influences.size() == primitive.vertices.size());
        }
        // The shadow mesh keeps the authored triangles; the colour mesh may add reversed copies of the triangles whose
        // back can be seen (tools/model_backface_split.py, at most a quarter of a primitive).
        const ModelMesh &shadow = asset.meshes[mesh.shadowMeshes[level]];
        REQUIRE(shadow.primitives.size() == 1);
        CHECK(shadow.primitives[0].indices.size() / 3 == triangles[level]);
        CHECK(indices / 3 >= triangles[level]);
        CHECK(indices / 3 <= triangles[level] + triangles[level] / 4);
        ModelAsset lower = asset;
        lower.nodes[nodeIndex].meshIndex = int(meshIndex);
        for (uint32_t clip = 0; clip < asset.clips.size(); ++clip)
        {
            for (int sample = 0; sample < 5; ++sample)
            {
                ModelPose pose;
                evaluateModelClip(asset, clip, asset.clips[clip].durationSeconds * sample / 4.0f, pose);
                evaluateModelHierarchy(asset, identityModelMatrix(), pose);
                const ModelBounds reference = modelExactPoseBounds(asset, pose);
                const ModelBounds actual = modelExactPoseBounds(lower, pose);
                CHECK(actual.valid == reference.valid);
                if (actual.valid)
                {
                    for (size_t axis = 0; axis < 3; ++axis)
                    {
                        // Detect changed bind spaces, bad joint remapping and exploded decimated weights.
                        CHECK(std::abs(reference.min[axis] - actual.min[axis]) < 0.15f);
                        CHECK(std::abs(reference.max[axis] - actual.max[axis]) < 0.15f);
                    }
                }
            }
        }
    }
}

TEST_CASE("ModelAnimation loader rejects self-referencing LOD metadata")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path root = makeTemporaryRoot();
    std::string json = fixtureGltf();
    const size_t position = json.find("\"primitives\"");
    REQUIRE(position != std::string::npos);
    json.insert(position, "\"extras\":{\"openyamm_lods\":[0]},");
    writeFile(root / "assets_dev/engine/models/fixture.bin", fixtureBuffer());
    writeFile(root / "assets_dev/engine/models/fixture.gltf", json);
    AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", AssetScaleTier::X1));
    const ModelLoadResult loaded = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    CHECK_FALSE(loaded);
    CHECK(loaded.error.find("LOD reference") != std::string::npos);
    assets.shutdown();
    std::filesystem::remove_all(root);
}

TEST_CASE("ModelAnimation loader reads colour region masks and ramps and rejects incomplete ones")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path root = makeTemporaryRoot();
    const std::string baseJson = fixtureGltf();
    const auto withRegions = [&](const std::string &extras)
    {
        std::string json = baseJson;
        const size_t animations = json.find("\"animations\"");
        REQUIRE(animations != std::string::npos);
        json.insert(animations, "\"images\": [{\"uri\": \"mask.png\"}], \"textures\": [{\"source\": 0}], ");
        const size_t material = json.find("\"pbrMetallicRoughness\"");
        REQUIRE(material != std::string::npos);
        json.insert(material, "\"extras\": {" + extras + "}, ");
        return json;
    };
    const auto ramp = [](size_t stops)
    {
        std::string colors;
        for (size_t stop = 0; stop < stops; ++stop)
        {
            const float position = float(stop) / 15.0f;
            colors += (stop == 0 ? "[" : ", [") + std::to_string(position) + ", 0, " + std::to_string(1 - position)
                + "]";
        }
        return "{\"range\": [0.1, 0.6], \"colors\": [" + colors + "]}";
    };
    const std::string mask = "\"openyamm_region_mask\": {\"index\": 0}";
    writeFile(root / "assets_dev/engine/models/fixture.bin", fixtureBuffer());
    // Only the PNG signature is checked at load; decoding happens when the renderer uploads the image.
    writeFile(root / "assets_dev/engine/models/mask.png", std::string("\x89PNG\r\n\x1a\n", 8));
    AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", AssetScaleTier::X1));

    writeFile(root / "assets_dev/engine/models/fixture.gltf",
        withRegions(mask + ", \"openyamm_region_ramps\": [" + ramp(16) + ", " + ramp(16) + "]"));
    const ModelLoadResult loaded = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    REQUIRE_MESSAGE(loaded, loaded.error);
    const ModelMaterial &material = loaded.asset->materials[0];
    CHECK_EQ(material.regionMaskImageIndex, 0);
    REQUIRE_EQ(material.regionRamps.size(), 2);
    CHECK_EQ(material.regionRamps[1].luminanceRange[0], doctest::Approx(0.1f));
    CHECK_EQ(material.regionRamps[1].luminanceRange[1], doctest::Approx(0.6f));
    CHECK_EQ(material.regionRamps[0].colors[0][2], doctest::Approx(1.0f));
    CHECK_EQ(material.regionRamps[0].colors[15][0], doctest::Approx(1.0f));

    CHECK_FALSE(material.specularMask);

    // A specular mask reads the metallic-roughness red channel, so it needs that texture.
    std::string masked = withRegions("\"openyamm_specular_mask\": true");
    writeFile(root / "assets_dev/engine/models/fixture.gltf", masked);
    const ModelLoadResult unmasked = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    CHECK_FALSE(unmasked);
    CHECK_MESSAGE(unmasked.error.find("specular mask needs") != std::string::npos, unmasked.error);
    const size_t factor = masked.find("\"baseColorFactor\"");
    REQUIRE(factor != std::string::npos);
    masked.insert(factor, "\"metallicRoughnessTexture\": {\"index\": 0}, ");
    writeFile(root / "assets_dev/engine/models/fixture.gltf", masked);
    const ModelLoadResult specularMasked = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    REQUIRE_MESSAGE(specularMasked, specularMasked.error);
    CHECK(specularMasked.asset->materials[0].specularMask);

    const std::array<std::pair<std::string, std::string>, 3> invalid = {{
        {mask, "region mask and one to four ramps"},
        {mask + ", \"openyamm_region_ramps\": [" + ramp(15) + "]", "16 colours"},
        {"\"openyamm_region_mask\": {\"index\": 3}, \"openyamm_region_ramps\": [" + ramp(16) + "]", "no texture"},
    }};
    for (const auto &[extras, message] : invalid)
    {
        writeFile(root / "assets_dev/engine/models/fixture.gltf", withRegions(extras));
        const ModelLoadResult rejected = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
        CHECK_FALSE(rejected);
        CHECK_MESSAGE(rejected.error.find(message) != std::string::npos, rejected.error);
    }
    assets.shutdown();
    std::filesystem::remove_all(root);
}

TEST_CASE("ModelAnimation loader reads emissive textures, strength and creature bloom per material variant")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path root = makeTemporaryRoot();
    std::string json = fixtureGltf();
    // Three tiers share one emissive mask and glow in their own colours (KHR_materials_variants), as creature tiers do.
    json.insert(1, R"("extensionsRequired":["KHR_materials_variants"],
        "extensions":{"KHR_materials_variants":{"variants":[{"name":"a"},{"name":"b"},{"name":"c"}]}},)");
    json.insert(json.find("\"attributes\""), R"("extensions":{"KHR_materials_variants":{"mappings":[
        {"material":0,"variants":[0]},{"material":1,"variants":[1]},{"material":2,"variants":[2]}]}},)");
    const std::string material = R"({"name": "opaque", "pbrMetallicRoughness": {"baseColorFactor": [1, 0.5, 0.25, 1]}})";
    const size_t materialAt = json.find(material);
    REQUIRE_NE(materialAt, std::string::npos);
    json.replace(materialAt, material.size(), R"(
        {"name":"a","emissiveFactor":[0.5,0.8,0.1],"emissiveTexture":{"index":0}},
        {"name":"b","emissiveFactor":[0.9,0.8,0.05],"emissiveTexture":{"index":0},
         "extensions":{"KHR_materials_emissive_strength":{"emissiveStrength":2.5}}},
        {"name":"c","emissiveFactor":[0.6,0.9,0.1],"emissiveTexture":{"index":0},"extras":{"openyamm_bloom":false}},
        {"name":"lens","emissiveFactor":[0.3,0.7,1],"extras":{"openyamm_bloom":true,"openyamm_pulse":[0.25,2]}},
        {"name":"plain","emissiveFactor":[0.95,0.72,0.18]})");
    json.insert(json.find("\"animations\""), R"("images": [{"uri": "glow.png"}], "textures": [{"source": 0}], )");
    writeFile(root / "assets_dev/engine/models/fixture.bin", fixtureBuffer());
    writeFile(root / "assets_dev/engine/models/glow.png", std::string("\x89PNG\r\n\x1a\n", 8));
    writeFile(root / "assets_dev/engine/models/fixture.gltf", json);
    AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", AssetScaleTier::X1));
    const ModelLoadResult loaded = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    REQUIRE_MESSAGE(loaded, loaded.error);
    const std::vector<ModelMaterial> &materials = loaded.asset->materials;
    REQUIRE_EQ(materials.size(), 5);
    REQUIRE_EQ(loaded.asset->meshes[0].primitives[0].materialIndices, std::vector<int>{0, 0, 1, 2});
    for (size_t index = 0; index < 3; ++index)
    {
        CHECK_EQ(materials[index].emissiveImageIndex, 0);
    }
    CHECK_EQ(materials[0].emissive[1], doctest::Approx(0.8f));
    CHECK_EQ(materials[1].emissive[0], doctest::Approx(2.25f));   // 0.9 x strength 2.5
    CHECK(materials[0].bloom);                                      // an emissive texture blooms
    CHECK(materials[1].bloom);
    CHECK_FALSE(materials[2].bloom);                                // unless the material opts out
    CHECK_EQ(materials[3].emissiveImageIndex, -1);
    CHECK(materials[3].bloom);                                      // a factor-only emitter opts in
    CHECK_FALSE(materials[4].bloom);                                // and otherwise emits without bloom

    // A creature pulse is 1 without "openyamm_pulse", and swings by its amplitude over its period.
    CHECK_EQ(modelCreaturePulse(materials[4], 3.7f), 1.0f);
    CHECK_EQ(modelCreaturePulse(materials[3], 0.0f), doctest::Approx(1.0f));
    CHECK_EQ(modelCreaturePulse(materials[3], 0.5f), doctest::Approx(1.25f));
    CHECK_EQ(modelCreaturePulse(materials[3], 1.5f), doctest::Approx(0.75f));
    ModelMaterial flicker;
    flicker.pulse = {0.3f, -0.25f};
    for (float seconds = 0.0f; seconds < 10.0f; seconds += 0.37f)
    {
        const float scale = modelCreaturePulse(flicker, seconds);
        CHECK(scale >= 0.7f - 1.0e-5f);
        CHECK(scale <= 1.3f + 1.0e-5f);
    }

    const std::array<std::pair<std::string, std::string>, 2> invalid = {{
        {R"("emissiveTexture":{"index":0},"extras":{"openyamm_bloom":false})",
            R"("emissiveTexture":{"index":0,"texCoord":1},"extras":{"openyamm_bloom":false})"},
        {R"("emissiveStrength":2.5)", R"("emissiveStrength":-1)"},
    }};
    for (const auto &[from, to] : invalid)
    {
        std::string rejected = json;
        REQUIRE_NE(rejected.find(from), std::string::npos);
        rejected.replace(rejected.find(from), from.size(), to);
        writeFile(root / "assets_dev/engine/models/fixture.gltf", rejected);
        CHECK_FALSE(GltfModelLoader().load(assets, "engine/models/fixture.gltf"));
    }
    assets.shutdown();
    std::filesystem::remove_all(root);
}

TEST_CASE("ModelAnimation installed creatures keep their emission out of the creature bloom")
{
    using namespace OpenYAMM::Engine;
    // The MM6 robot's eye is the only emitting creature material of MM6-MM8 (2026-10-22): it keeps its unbloomed glow.
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", AssetScaleTier::X1));
    const ModelLoadResult loaded = GltfModelLoader().load(assetFileSystem, "worlds/mm6/models/mm6_rob1.glb");
    REQUIRE_MESSAGE(loaded, loaded.error);
    REQUIRE_FALSE(loaded.asset->skins.empty());
    size_t emitters = 0;
    for (const ModelMaterial &material : loaded.asset->materials)
    {
        CHECK_EQ(material.emissiveImageIndex, -1);
        CHECK_FALSE(material.bloom);
        CHECK_EQ(modelCreaturePulse(material, 1.0f), 1.0f);
        emitters += material.emissive[0] > 0.0f ? 1 : 0;
    }
    CHECK(emitters > 0);
}

TEST_CASE("ModelAnimation loader reads the cooked burn order per vertex")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path root = makeTemporaryRoot();
    std::string json = fixtureGltf();
    // A float view over the texture coordinates (0, 0, 1) stands in for the cook's normalized byte stream.
    const size_t attributes = json.find("\"TEXCOORD_0\": 2");
    REQUIRE(attributes != std::string::npos);
    json.insert(attributes, "\"_BURN_ORDER\": 7, ");
    const std::string lastAccessor = "{\"bufferView\": 6, \"componentType\": 5126, \"count\": 2, \"type\": \"VEC3\"}";
    const size_t accessors = json.find(lastAccessor);
    REQUIRE(accessors != std::string::npos);
    const std::string burnOrder =
        ",\n    {\"bufferView\": 2, \"componentType\": 5126, \"count\": COUNT, \"type\": \"SCALAR\"}";
    std::string valid = json;
    valid.insert(accessors + lastAccessor.size(), std::string(burnOrder).replace(burnOrder.find("COUNT"), 5, "3"));
    writeFile(root / "assets_dev/engine/models/fixture.bin", fixtureBuffer());
    writeFile(root / "assets_dev/engine/models/fixture.gltf", valid);
    AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", AssetScaleTier::X1));
    const ModelLoadResult loaded = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    REQUIRE_MESSAGE(loaded, loaded.error);
    const ModelPrimitive &primitive = loaded.asset->meshes[0].primitives[0];
    REQUIRE_EQ(primitive.burnOrder.size(), primitive.vertices.size());
    CHECK_EQ(primitive.burnOrder[0], doctest::Approx(0.0f));
    CHECK_EQ(primitive.burnOrder[1], doctest::Approx(0.0f));
    CHECK_EQ(primitive.burnOrder[2], doctest::Approx(1.0f));

    // One scalar per vertex, or the model is rejected (here the VEC2 texture coordinates).
    std::string mismatched = json;
    mismatched.replace(mismatched.find("\"_BURN_ORDER\": 7"), 16, "\"_BURN_ORDER\": 2");
    writeFile(root / "assets_dev/engine/models/fixture.gltf", mismatched);
    const ModelLoadResult rejected = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    CHECK_FALSE(rejected);
    CHECK_MESSAGE(rejected.error.find("_BURN_ORDER") != std::string::npos, rejected.error);
    assets.shutdown();
    std::filesystem::remove_all(root);
}

TEST_CASE("ModelAnimation loader reads vertex colours and static decoration material extras")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path root = makeTemporaryRoot();
    std::string json = fixtureGltf();
    // The normal accessor doubles as a VEC3 colour stream.
    const size_t attributes = json.find("\"TEXCOORD_0\": 2");
    REQUIRE(attributes != std::string::npos);
    json.insert(attributes, "\"COLOR_0\": 1, ");
    const size_t material = json.find("\"pbrMetallicRoughness\"");
    REQUIRE(material != std::string::npos);
    json.insert(material,
        "\"extras\": {\"openyamm_wind\": 0.12, \"openyamm_translucency\": 0.35, \"openyamm_billboard\": true, "
        "\"openyamm_specular\": 0.1, \"openyamm_uv_scroll\": [0.25, -1.5], \"openyamm_flipbook\": [4, 2, 12], "
        "\"openyamm_flutter\": 0.1, \"openyamm_edge_darkening\": 0.25}, ");
    writeFile(root / "assets_dev/engine/models/fixture.bin", fixtureBuffer());
    writeFile(root / "assets_dev/engine/models/fixture.gltf", json);
    AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", AssetScaleTier::X1));
    const ModelLoadResult loaded = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    REQUIRE_MESSAGE(loaded, loaded.error);
    const ModelPrimitive &primitive = loaded.asset->meshes[0].primitives[0];
    REQUIRE_EQ(primitive.colors.size(), primitive.vertices.size());
    for (size_t index = 0; index < primitive.vertices.size(); ++index)
    {
        for (size_t channel = 0; channel < 3; ++channel)
        {
            const float expected = std::clamp(primitive.vertices[index].normal[channel], 0.0f, 1.0f) * 255.0f;
            CHECK_EQ(int(primitive.colors[index][channel]), int(std::lround(expected)));
        }
        CHECK_EQ(int(primitive.colors[index][3]), 255);
    }
    const ModelMaterial &extras = loaded.asset->materials[0];
    CHECK_EQ(extras.wind, doctest::Approx(0.12f));
    CHECK_EQ(extras.translucency, doctest::Approx(0.35f));
    CHECK_EQ(extras.specular, doctest::Approx(0.1f));
    CHECK_EQ(extras.uvScroll[0], doctest::Approx(0.25f));
    CHECK_EQ(extras.uvScroll[1], doctest::Approx(-1.5f));
    CHECK_EQ(extras.flipbook[0], doctest::Approx(4.0f));
    CHECK_EQ(extras.flipbook[1], doctest::Approx(2.0f));
    CHECK_EQ(extras.flipbook[2], doctest::Approx(12.0f));
    CHECK_EQ(extras.flutter, doctest::Approx(0.1f));
    CHECK_EQ(extras.edgeDarkening, doctest::Approx(0.25f));
    CHECK_EQ(loaded.asset->materials[0].specular, doctest::Approx(0.1f));
    CHECK(extras.billboard);

    const size_t translucency = json.find("0.35");
    REQUIRE(translucency != std::string::npos);
    json.replace(translucency, 4, "1.50");
    writeFile(root / "assets_dev/engine/models/fixture.gltf", json);
    const ModelLoadResult invalid = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    CHECK_FALSE(invalid);
    CHECK(invalid.error.find("translucency") != std::string::npos);
    json.replace(json.find("1.50"), 4, "0.35");
    json.replace(json.find("[4, 2, 12]"), 10, "[2.5, 2, 1]");
    writeFile(root / "assets_dev/engine/models/fixture.gltf", json);
    const ModelLoadResult fractionalFlipbook = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    CHECK_FALSE(fractionalFlipbook);
    CHECK(fractionalFlipbook.error.find("flipbook") != std::string::npos);
    json.replace(json.find("[2.5, 2, 1]"), 11, "[4, 2, 12]");
    // Flame cards: a card billboard, additive blending and a random flicker (a pulse with a negative period).
    json.replace(json.find("\"openyamm_billboard\": true"), 26,
        "\"openyamm_billboard\": \"card\", \"openyamm_additive\": true, \"openyamm_flicker\": [0.3, 8]");
    writeFile(root / "assets_dev/engine/models/fixture.gltf", json);
    const ModelLoadResult flame = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    REQUIRE_MESSAGE(flame, flame.error);
    const ModelMaterial &card = flame.asset->materials[0];
    CHECK(card.billboard);
    CHECK(card.billboardCard);
    CHECK(card.additive);
    CHECK_EQ(card.pulse[0], doctest::Approx(0.3f));
    CHECK_EQ(card.pulse[1], doctest::Approx(-0.125f));
    json.replace(json.find("[0.3, 8]"), 8, "[0.3, 90]");
    writeFile(root / "assets_dev/engine/models/fixture.gltf", json);
    const ModelLoadResult fastFlicker = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    CHECK_FALSE(fastFlicker);
    CHECK(fastFlicker.error.find("flicker") != std::string::npos);
    json.replace(json.find("[0.3, 90]"), 9, "[0.3, 8], \"openyamm_pulse\": [0.2, 2]");
    writeFile(root / "assets_dev/engine/models/fixture.gltf", json);
    const ModelLoadResult flickerAndPulse = GltfModelLoader().load(assets, "engine/models/fixture.gltf");
    CHECK_FALSE(flickerAndPulse);
    CHECK(flickerAndPulse.error.find("flicker") != std::string::npos);
    assets.shutdown();
    std::filesystem::remove_all(root);
}

TEST_CASE("ModelAnimation bakes a frozen skinned pose into a static asset that matches CPU skinning")
{
    using namespace OpenYAMM::Engine;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", AssetScaleTier::X1));
    const ModelLoadResult loaded = GltfModelLoader().load(assets, "worlds/mm6/models/mm6_ckt.glb");
    REQUIRE_MESSAGE(loaded, loaded.error);
    const ModelAsset &asset = *loaded.asset;
    const std::optional<uint32_t> dead = asset.findClip("Dead");
    REQUIRE(dead);
    ModelPose pose;
    resetModelPose(asset, pose);
    evaluateModelClip(asset, *dead, asset.clips[*dead].durationSeconds, pose);
    evaluateModelHierarchy(asset, identityModelMatrix(), pose);
    const std::shared_ptr<ModelAsset> baked = bakeStaticModelPose(asset, pose);
    deformModelPose(asset, pose);
    REQUIRE(baked->skins.empty());
    REQUIRE(baked->clips.empty());
    // Creature materials default to edge darkening, and the corpse stand-in keeps it.
    CHECK(std::any_of(asset.materials.begin(), asset.materials.end(), [](const ModelMaterial &material)
    {
        return material.edgeDarkening == DefaultCreatureEdgeDarkening;
    }));
    for (size_t index = 0; index < asset.materials.size(); ++index)
    {
        CHECK_EQ(baked->materials[index].edgeDarkening, asset.materials[index].edgeDarkening);
    }
    CHECK(baked->staticBounds.valid);
    CHECK_EQ(baked->materialVariants, asset.materialVariants);
    size_t compared = 0;
    for (size_t nodeIndex = 0; nodeIndex < asset.nodes.size(); ++nodeIndex)
    {
        const ModelNode &node = asset.nodes[nodeIndex];
        if (node.meshIndex < 0 || node.skinIndex < 0)
        {
            continue;
        }
        const ModelNode &bakedNode = baked->nodes.at(baked->nodeIndicesByName.at(node.name));
        CHECK_EQ(bakedNode.skinIndex, -1);
        CHECK_EQ(bakedNode.matrix, identityModelMatrix());
        const ModelMesh &bakedMesh = baked->meshes.at(size_t(bakedNode.meshIndex));
        CHECK_EQ(bakedMesh.lodMeshes.size(), asset.meshes[size_t(node.meshIndex)].lodMeshes.size());
        for (size_t primitive = 0; primitive < bakedMesh.primitives.size(); ++primitive)
        {
            const std::vector<ModelVertex> &expected = pose.deformedVertices[nodeIndex][primitive];
            const std::vector<ModelVertex> &actual = bakedMesh.primitives[primitive].vertices;
            REQUIRE_EQ(actual.size(), expected.size());
            for (size_t vertex = 0; vertex < actual.size(); ++vertex)
            {
                for (size_t axis = 0; axis < 3; ++axis)
                {
                    REQUIRE(std::abs(actual[vertex].position[axis] - expected[vertex].position[axis]) < 1.0e-4f);
                }
            }
            compared += actual.size();
            CHECK(bakedMesh.primitives[primitive].influences.empty());
        }
    }
    CHECK_GT(compared, 1000u);
    for (size_t meshIndex = 0; meshIndex < baked->meshes.size(); ++meshIndex)
    {
        for (const ModelPrimitive &primitive : baked->meshes[meshIndex].primitives)
        {
            for (const uint32_t index : primitive.indices)
            {
                REQUIRE_LT(index, primitive.vertices.size());
            }
            for (const int material : primitive.materialIndices)
            {
                REQUIRE((material >= -1 && material < int(baked->materials.size())));
            }
            for (const ModelVertex &vertex : primitive.vertices)
            {
                const float length = std::sqrt(vertex.normal[0] * vertex.normal[0] + vertex.normal[1] * vertex.normal[1]
                    + vertex.normal[2] * vertex.normal[2]);
                REQUIRE_MESSAGE(std::abs(length - 1.0f) < 1.0e-3f, "mesh " << meshIndex << " normal length " << length);
                for (size_t axis = 0; axis < 3; ++axis)
                {
                    REQUIRE(std::isfinite(vertex.position[axis]));
                }
            }
        }
    }
}
