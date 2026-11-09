#include <doctest/doctest.h>

#include "engine/AssetFileSystem.h"
#include "game/StringUtils.h"
#include "game/data/GameDataLoader.h"
#include "game/items/WorldItemShape.h"
#include "game/party/Party.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <numbers>

using namespace OpenYAMM::Game;

namespace
{
ItemModelBinding boxBinding(std::array<float, 3> low, std::array<float, 3> high)
{
    ItemModelBinding binding;
    binding.model = "test.glb";
    binding.length = std::max(high[0] - low[0], high[1] - low[1]);
    binding.boundsMin = low;
    binding.boundsMax = high;
    return binding;
}
}

TEST_CASE("ground item yaw keeps the hashed per-key orientation")
{
    for (uint32_t key : {0u, 1u, 17u, 4000000000u})
    {
        const float halfYaw = float((key * 2654435761u) >> 8) / float(1u << 24) * std::numbers::pi_v<float>;
        CHECK(worldItemYawRadians(key) == doctest::Approx(2.0f * halfYaw));
        CHECK(worldItemYawRadians(key) >= 0.0f);
        CHECK(worldItemYawRadians(key) < 2.0f * std::numbers::pi_v<float>);
    }
}

TEST_CASE("ground item sphere chains follow the long side and rest on the underside")
{
    const ItemModelBinding sword = boxBinding({-10.0f, -80.0f, 0.0f}, {10.0f, 80.0f, 12.0f});
    const WorldItemSphereChain flat = worldItemSphereChain(sword, 0.0f);
    CHECK(flat.radius == doctest::Approx(10.0f));
    REQUIRE(flat.count == WorldItemSphereChain::MaxSpheres);
    CHECK(flat.offsets[0][1] == doctest::Approx(-70.0f));
    CHECK(flat.offsets[flat.count - 1][1] == doctest::Approx(70.0f));
    CHECK(flat.offsets[2][1] == doctest::Approx(0.0f).epsilon(0.001));
    CHECK(flat.offsets[0][2] == doctest::Approx(10.0f));

    // Turned a quarter: the blade lies along x.
    const WorldItemSphereChain turned = worldItemSphereChain(sword, std::numbers::pi_v<float> * 0.5f);
    CHECK(turned.offsets[turned.count - 1][0] == doctest::Approx(-70.0f));
    CHECK(std::abs(turned.offsets[turned.count - 1][1]) < 0.001f);

    const ItemModelBinding gem = boxBinding({-10.0f, -11.0f, 0.0f}, {10.0f, 11.0f, 19.0f});
    const WorldItemSphereChain compact = worldItemSphereChain(gem, 1.0f);
    CHECK(compact.count == 1);
    CHECK(compact.radius == doctest::Approx(10.0f));
}

TEST_CASE("resting ground items fit the slope under their footprint and never sink into it")
{
    const ItemModelBinding sword = boxBinding({-10.0f, -80.0f, 0.0f}, {10.0f, 80.0f, 12.0f});
    const WorldItemFootprint footprint = worldItemFootprintOffsets(sword, 0.0f);
    const auto heightsOf = [&footprint](auto ground)
    {
        std::array<std::optional<float>, WorldItemFootprintSampleCount> heights;
        for (size_t index = 0; index < WorldItemFootprintSampleCount; ++index)
        {
            heights[index] = ground(footprint[index][0], footprint[index][1]);
        }
        return heights;
    };
    const auto supported = [&](const WorldItemRestingPose &pose, const auto &heights)
    {
        const float slopeX = -pose.normal[0] / pose.normal[2];
        const float slopeY = -pose.normal[1] / pose.normal[2];
        for (size_t index = 0; index < WorldItemFootprintSampleCount; ++index)
        {
            if (heights[index])
            {
                const float underside = pose.z + slopeX * footprint[index][0] + slopeY * footprint[index][1];
                CHECK(underside >= *heights[index] - 0.01f);
            }
        }
    };

    const auto flat = heightsOf([](float, float) { return std::optional<float>(5.0f); });
    const WorldItemRestingPose level = fitWorldItemRestingPose(sword, 0.0f, flat, 0.0f);
    CHECK(level.z == doctest::Approx(5.0f));
    CHECK(level.normal[2] == doctest::Approx(1.0f));

    const auto ramp = heightsOf([](float, float y) { return std::optional<float>(0.1f * y); });
    const WorldItemRestingPose sloped = fitWorldItemRestingPose(sword, 0.0f, ramp, 0.0f);
    CHECK(sloped.z == doctest::Approx(0.0f).epsilon(0.001));
    CHECK(-sloped.normal[1] / sloped.normal[2] == doctest::Approx(0.1f));
    supported(sloped, ramp);

    // A stair edge under one end: tilted at most a little, then propped up on the step.
    const auto step = heightsOf([](float, float y) { return std::optional<float>(y > 0.0f ? 64.0f : 0.0f); });
    const WorldItemRestingPose propped = fitWorldItemRestingPose(sword, 0.0f, step, 0.0f);
    CHECK(-propped.normal[1] / propped.normal[2] <= 0.37f);
    supported(propped, step);

    const std::array<std::optional<float>, WorldItemFootprintSampleCount> nothing = {};
    const WorldItemRestingPose unsupported = fitWorldItemRestingPose(sword, 0.0f, nothing, 42.0f);
    CHECK(unsupported.z == doctest::Approx(42.0f));
    CHECK(unsupported.normal[2] == doctest::Approx(1.0f));
}

TEST_CASE("ground item pick boxes keep small items clickable and long items clickable along their length")
{
    const ItemModelBinding gem = boxBinding({-5.0f, -6.0f, 0.0f}, {5.0f, 6.0f, 9.0f});
    const std::array<float, 3> origin = {100.0f, 200.0f, 50.0f};
    const std::optional<float> gemHit = intersectWorldItemPickBox(gem, 0.0f, origin, {100.0f, 100.0f, 60.0f},
        {0.0f, 1.0f, 0.0f});
    REQUIRE(gemHit);
    CHECK(*gemHit == doctest::Approx(80.0f));
    CHECK_FALSE(intersectWorldItemPickBox(gem, 0.0f, origin, {125.0f, 100.0f, 60.0f}, {0.0f, 1.0f, 0.0f}));

    // A sword turned a quarter lies along x: its far end is clickable, beside it is not.
    const ItemModelBinding sword = boxBinding({-10.0f, -80.0f, 0.0f}, {10.0f, 80.0f, 12.0f});
    const float quarter = std::numbers::pi_v<float> * 0.5f;
    CHECK(intersectWorldItemPickBox(sword, quarter, origin, {170.0f, 100.0f, 55.0f}, {0.0f, 1.0f, 0.0f}));
    CHECK_FALSE(intersectWorldItemPickBox(sword, quarter, origin, {190.0f, 100.0f, 55.0f}, {0.0f, 1.0f, 0.0f}));
    CHECK_FALSE(intersectWorldItemPickBox(sword, 0.0f, origin, {170.0f, 100.0f, 55.0f}, {0.0f, 1.0f, 0.0f}));

    // Its corners (for on-screen targets) span the same turned box: 160 along x, the minimum 40 along y, 24 high.
    const WorldItemPickBoxCorners corners = worldItemPickBoxCorners(sword, quarter, origin);
    std::array<float, 3> low = corners[0];
    std::array<float, 3> high = corners[0];
    for (const std::array<float, 3> &corner : corners)
    {
        for (size_t axis = 0; axis < 3; ++axis)
        {
            low[axis] = std::min(low[axis], corner[axis]);
            high[axis] = std::max(high[axis], corner[axis]);
        }
    }
    CHECK(low[0] == doctest::Approx(20.0f));
    CHECK(high[0] == doctest::Approx(180.0f));
    CHECK(low[1] == doctest::Approx(180.0f));
    CHECK(high[1] == doctest::Approx(220.0f));
    CHECK(low[2] == doctest::Approx(50.0f));
    CHECK(high[2] == doctest::Approx(74.0f));
}

TEST_CASE("ground items bounce off walls with the native object reflection")
{
    const std::array<float, 3> head = reflectWorldItemVelocity({100.0f, 0.0f, 0.0f}, {-1.0f, 0.0f, 0.0f});
    CHECK(head[0] == doctest::Approx(-100.0f));
    CHECK(head[1] == doctest::Approx(0.0f));
    // Grazing: at least an eighth of the speed is turned away from the wall.
    const std::array<float, 3> graze = reflectWorldItemVelocity({0.0f, 80.0f, 0.0f}, {-1.0f, 0.0f, 0.0f});
    CHECK(graze[0] == doctest::Approx(-20.0f));
    CHECK(graze[1] == doctest::Approx(80.0f));
}

TEST_CASE("ground items sparkle by their value in gold")
{
    ItemDefinition sword;
    sword.value = 300;
    InventoryItem item;
    CHECK(worldItemSparkle(item, sword, 300) == WorldItemSparkle::None);
    CHECK(worldItemSparkle(item, sword, 999) == WorldItemSparkle::None);
    CHECK(worldItemSparkle(item, sword, 1000) == WorldItemSparkle::Valuable);
    CHECK(worldItemSparkle(item, sword, 2500) == WorldItemSparkle::Precious);
    item.artifactId = 1;
    CHECK(worldItemSparkle(item, sword, 300) == WorldItemSparkle::Artifact);

    // Artifacts, relics and named uniques by their definition, even the ones worth nothing.
    InventoryItem unique;
    ItemDefinition ebonest;
    ebonest.rarity = ItemRarity::Special;
    CHECK(worldItemSparkle(unique, ebonest, 0) == WorldItemSparkle::Artifact);
    ItemDefinition key;
    CHECK(worldItemSparkle(unique, key, 0) == WorldItemSparkle::Quest);
    ItemDefinition coins;
    coins.equipStat = "Gold";
    CHECK(worldItemSparkle(unique, coins, 0) == WorldItemSparkle::Coins);
}

TEST_CASE("every MM6-MM8 item has a ground model of its own")
{
    // An item without one draws the missing-model placeholder on the ground (GROUND_ITEMS_3D_BEHAVIOUR.md): a bug.
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    OpenYAMM::Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm6"));
    GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assets));
    const ItemTable &items = data.getItemTable();
    size_t realItems = 0;
    for (const ItemDefinition &item : items.entries())
    {
        const std::string icon = toLowerCopy(item.iconName);
        if (item.itemId == 0 || icon.empty() || icon == "null" || item.packageId == "mm9")
        {
            continue;
        }
        ++realItems;
        INFO("item " << item.itemId << " " << item.name << " (icon " << icon << ")");
        CHECK(items.hasGroundModel(item.itemId));
    }
    CHECK(realItems > 1800);
}

TEST_CASE("a posed world item rests on its lowest point and is picked as it stands")
{
    OpenYAMM::Game::ItemModelBinding binding = {};
    binding.boundsMin = {-10.0f, -20.0f, 0.0f};
    binding.boundsMax = {10.0f, 20.0f, 4.0f};
    // Pitched up a quarter turn: the item stands on its -y end, 40 units tall.
    const OpenYAMM::Game::WorldItemPose pose = {0.0f, std::numbers::pi_v<float> / 2.0f, 0.0f};
    const std::array<float, 3> origin = OpenYAMM::Game::worldItemPosedOrigin(binding, pose, {100.0f, 50.0f, 7.0f});
    CHECK(origin[2] == doctest::Approx(27.0f));
    // A horizontal ray along y at mid-height meets the standing box; one above its top does not.
    CHECK(OpenYAMM::Game::intersectPosedWorldItemPickBox(binding, pose, {100.0f, 50.0f, 7.0f},
        {100.0f, -100.0f, 27.0f}, {0.0f, 1.0f, 0.0f}).has_value());
    CHECK_FALSE(OpenYAMM::Game::intersectPosedWorldItemPickBox(binding, pose, {100.0f, 50.0f, 7.0f},
        {100.0f, -100.0f, 60.0f}, {0.0f, 1.0f, 0.0f}).has_value());
    // The quaternion of a pure yaw is the yaw about z.
    const std::array<float, 4> q = OpenYAMM::Game::worldItemPoseRotation({std::numbers::pi_v<float> / 2.0f, 0.0f, 0.0f});
    CHECK(q[2] == doctest::Approx(std::sqrt(0.5f)));
    CHECK(q[3] == doctest::Approx(std::sqrt(0.5f)));
}
