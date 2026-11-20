#include "doctest/doctest.h"

#include "game/indoor/IndoorFaceDrawGroups.h"

#include <cstdint>
#include <unordered_set>
#include <vector>

namespace
{
using OpenYAMM::Game::IndoorFaceDrawGroupKey;
using OpenYAMM::Game::IndoorFaceDrawGroupKeyHash;
using OpenYAMM::Game::IndoorFaceDrawPlan;
using OpenYAMM::Game::IndoorFaceGroupDraw;
using OpenYAMM::Game::IndoorFaceIndexRange;

// Two triangles (a quad) per batch, local indices.
const std::vector<uint32_t> Quad = {0, 1, 2, 0, 2, 3};

// Group 0: batches 0, 2, 3 (vertex offsets 0, 4, 8); group 1: batch 1; group 2: batch 4 with no faces.
IndoorFaceDrawPlan makePlan()
{
    IndoorFaceDrawPlan plan;
    plan.addBatch(0, 0, Quad, 0);
    plan.addBatch(1, 1, Quad, 0);
    plan.addBatch(0, 2, Quad, 4);
    plan.addBatch(0, 3, Quad, 8);
    plan.addBatch(2, 4, {}, 0);
    return plan;
}
}

TEST_CASE("indoor face draw groups lay out their batches one after another")
{
    const IndoorFaceDrawPlan plan = makePlan();
    REQUIRE(plan.groupCount() == 3);
    CHECK(plan.groupIndices(0) == std::vector<uint32_t>{0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7, 8, 9, 10, 8, 10, 11});
    CHECK(plan.groupIndices(1) == Quad);
    CHECK(plan.groupIndices(2).empty());
    CHECK(plan.batchRange(0) == IndoorFaceIndexRange{0, 6});
    CHECK(plan.batchRange(2) == IndoorFaceIndexRange{6, 6});
    CHECK(plan.batchRange(3) == IndoorFaceIndexRange{12, 6});
    CHECK(plan.batchRange(1) == IndoorFaceIndexRange{0, 6});
    CHECK(plan.batchRange(4) == IndoorFaceIndexRange{0, 0});
    CHECK(plan.batchRange(9) == IndoorFaceIndexRange{});
}

TEST_CASE("indoor face draw groups draw each group's visible batches with one draw")
{
    IndoorFaceDrawPlan plan = makePlan();

    // Everything visible: one draw per group with faces, each its whole list, nothing merged.
    CHECK(plan.update(std::vector<uint8_t>{1, 1, 1, 1, 1}));
    CHECK(plan.draws() == std::vector<IndoorFaceGroupDraw>{{0, false, 0, 18}, {1, false, 0, 6}});
    CHECK(plan.mergedIndices().empty());

    // A contiguous run of a group's batches draws straight from its list.
    CHECK(plan.update(std::vector<uint8_t>{0, 0, 1, 1, 0}));
    CHECK(plan.draws() == std::vector<IndoorFaceGroupDraw>{{0, false, 6, 12}});
    CHECK(plan.mergedIndices().empty());

    // Batches 0 and 3 with 2 hidden between them: one merged draw of both, in group order.
    CHECK(plan.update(std::vector<uint8_t>{1, 1, 0, 1, 1}));
    CHECK(plan.draws() == std::vector<IndoorFaceGroupDraw>{{0, true, 0, 12}, {1, false, 0, 6}});
    CHECK(plan.mergedIndices() == std::vector<uint32_t>{0, 1, 2, 0, 2, 3, 8, 9, 10, 8, 10, 11});

    // Nothing drawn: no draws.
    CHECK(plan.update(std::vector<uint8_t>{0, 0, 0, 0, 0}));
    CHECK(plan.draws().empty());
}

TEST_CASE("indoor face draw groups re-plan only when the drawn batches change")
{
    IndoorFaceDrawPlan plan = makePlan();
    const std::vector<uint8_t> drawn = {1, 0, 0, 1, 0};
    CHECK(plan.update(drawn));
    CHECK_FALSE(plan.update(drawn));
    CHECK(plan.draws() == std::vector<IndoorFaceGroupDraw>{{0, true, 0, 12}});
    CHECK(plan.update(std::vector<uint8_t>{1, 0, 0, 1, 1}));
    CHECK_FALSE(plan.update(std::vector<uint8_t>{1, 0, 0, 1, 1}));

    // A rebuilt layout always plans again, even for the same flags.
    plan.clear();
    plan.addBatch(0, 0, Quad, 0);
    CHECK(plan.update(std::vector<uint8_t>{1}));
    CHECK(plan.draws() == std::vector<IndoorFaceGroupDraw>{{0, false, 0, 6}});
}

TEST_CASE("indoor face draw group keys separate every draw state")
{
    const IndoorFaceDrawGroupKey opaque = {"wall01", -1, 0, -1};
    std::unordered_set<IndoorFaceDrawGroupKey, IndoorFaceDrawGroupKeyHash> keys = {opaque};
    // The sector and the daylight are not part of the key (they are per vertex): the same texture in another sector
    // is the same group.
    CHECK(keys.contains(IndoorFaceDrawGroupKey{"wall01", -1, 0, -1}));
    CHECK_FALSE(keys.contains(IndoorFaceDrawGroupKey{"wall02", -1, 0, -1}));
    CHECK_FALSE(keys.contains(IndoorFaceDrawGroupKey{"wall01", 0, 0, -1}));
    CHECK_FALSE(keys.contains(IndoorFaceDrawGroupKey{"wall01", -1, 0xff804020u, -1}));
    CHECK_FALSE(keys.contains(IndoorFaceDrawGroupKey{"wall01", -1, 0, 12}));
    CHECK(IndoorFaceDrawGroupKey{"glass", -1, 0, 12} != IndoorFaceDrawGroupKey{"glass", -1, 0, 13});
}

TEST_CASE("indoor face draw groups keep the batch order of touching batches")
{
    // Group 0: batches 0 and 2; group 1: batch 1 (drawn between them in batch order).
    const auto make = []
    {
        IndoorFaceDrawPlan plan;
        plan.addBatch(0, 0, Quad, 0);
        plan.addBatch(1, 1, Quad, 0);
        plan.addBatch(0, 2, Quad, 4);
        return plan;
    };
    const std::vector<uint8_t> all = {1, 1, 1};

    // Nothing touches: batch 2 joins batch 0's draw, ahead of batch 1.
    IndoorFaceDrawPlan free = make();
    CHECK(free.update(all));
    CHECK(free.draws() == std::vector<IndoorFaceGroupDraw>{{0, false, 0, 12}, {1, false, 0, 6}});

    // Batch 2 touches batch 1: it must still draw after it, so group 0 draws twice.
    IndoorFaceDrawPlan touching = make();
    CHECK(touching.addConflict(2, 1));
    CHECK_FALSE(touching.addConflict(1, 2));
    CHECK(touching.update(all));
    CHECK(touching.draws()
        == std::vector<IndoorFaceGroupDraw>{{0, false, 0, 6}, {1, false, 0, 6}, {0, false, 6, 6}});

    // Batch 1 touching batch 0 needs nothing more: batch 1 draws after group 0's draw anyway. Touching batches of
    // one group keep their order inside the draw.
    IndoorFaceDrawPlan earlier = make();
    CHECK(earlier.addConflict(1, 0));
    CHECK(earlier.addConflict(0, 2));
    CHECK(earlier.update(all));
    CHECK(earlier.draws() == std::vector<IndoorFaceGroupDraw>{{0, false, 0, 12}, {1, false, 0, 6}});
}

TEST_CASE("indoor face draw groups reorder only batches that do not touch")
{
    // Batch order alternates groups: 0 (group 0), 1 (group 1), 2 (group 0), 3 (group 1), 4 (group 0).
    IndoorFaceDrawPlan plan;
    plan.addBatch(0, 0, Quad, 0);
    plan.addBatch(1, 1, Quad, 0);
    plan.addBatch(0, 2, Quad, 4);
    plan.addBatch(1, 3, Quad, 4);
    plan.addBatch(0, 4, Quad, 8);
    // 3 touches 2, and 4 touches 3: group 0's last batch must follow group 1's.
    CHECK(plan.addConflict(3, 2));
    CHECK(plan.addConflict(4, 3));
    CHECK(plan.update(std::vector<uint8_t>{1, 1, 1, 1, 1}));
    // Group 0 (three ready, then two after batch 2) first: 0 and 2; group 1: 1 and 3; then 4.
    CHECK(plan.draws() == std::vector<IndoorFaceGroupDraw>{{0, false, 0, 12}, {1, false, 0, 12}, {0, false, 12, 6}});

    // With batch 3 hidden nothing holds batch 4 back: one draw per group.
    CHECK(plan.update(std::vector<uint8_t>{1, 1, 1, 0, 1}));
    CHECK(plan.draws() == std::vector<IndoorFaceGroupDraw>{{0, false, 0, 18}, {1, false, 0, 6}});

    // Batches 0 and 4 without 2: one merged draw of both.
    CHECK(plan.update(std::vector<uint8_t>{1, 0, 0, 0, 1}));
    CHECK(plan.draws() == std::vector<IndoorFaceGroupDraw>{{0, true, 0, 12}});
    CHECK(plan.mergedIndices() == std::vector<uint32_t>{0, 1, 2, 0, 2, 3, 8, 9, 10, 8, 10, 11});
}

TEST_CASE("indoor face draw groups plan again when a mover adds a touching pair")
{
    IndoorFaceDrawPlan plan;
    plan.addBatch(0, 0, Quad, 0);
    plan.addBatch(1, 1, Quad, 0);
    plan.addBatch(0, 2, Quad, 4);
    const std::vector<uint8_t> drawn = {1, 1, 1};
    CHECK(plan.update(drawn));
    CHECK_FALSE(plan.update(drawn));
    CHECK(plan.draws().size() == 2);
    CHECK(plan.addConflict(1, 2));
    CHECK(plan.update(drawn));
    CHECK(plan.draws().size() == 3);
    // Batch 1 hidden: the pair no longer matters.
    CHECK(plan.update(std::vector<uint8_t>{1, 0, 1}));
    CHECK(plan.draws() == std::vector<IndoorFaceGroupDraw>{{0, false, 0, 12}});
}

TEST_CASE("indoor faces meet at one depth only over each other's interior")
{
    using OpenYAMM::Game::IndoorFacePoint;
    using OpenYAMM::Game::indoorFaceReachesInterior;
    using OpenYAMM::Game::makeIndoorFaceShape;
    const auto reach = [](const std::vector<IndoorFacePoint> &face, const std::vector<IndoorFacePoint> &other)
    {
        return indoorFaceReachesInterior(makeIndoorFaceShape(face), makeIndoorFaceShape(other), 1.0f, 0.01f);
    };
    // A wall in the plane x = 0, and a floor beside it sharing its bottom edge (a room corner).
    const std::vector<IndoorFacePoint> wall = {{0, 0, 0}, {0, 100, 0}, {0, 100, 100}, {0, 0, 100}};
    const std::vector<IndoorFacePoint> floor = {{0, 0, 0}, {100, 0, 0}, {100, 100, 0}, {0, 100, 0}};
    CHECK_FALSE(reach(wall, floor));
    CHECK_FALSE(reach(floor, wall));
    // The next wall section in the same plane, sharing an edge.
    const std::vector<IndoorFacePoint> nextWall = {{0, 100, 0}, {0, 200, 0}, {0, 200, 100}, {0, 100, 100}};
    CHECK_FALSE(reach(wall, nextWall));
    CHECK_FALSE(reach(nextWall, wall));
    // A cornice's underside, its edge on the wall's interior (a T-junction).
    const std::vector<IndoorFacePoint> cornice = {{0, 20, 50}, {10, 20, 50}, {10, 80, 50}, {0, 80, 50}};
    CHECK(reach(wall, cornice));
    CHECK_FALSE(reach(cornice, wall));
    // A pillar standing in the middle of the floor.
    const std::vector<IndoorFacePoint> pillar = {{40, 40, 0}, {60, 40, 0}, {60, 40, 80}, {40, 40, 80}};
    CHECK(reach(floor, pillar));
    // A panel half a unit off the wall over it (z-fighting far off), and one five units off.
    const std::vector<IndoorFacePoint> plaque = {{0.5f, 30, 30}, {0.5f, 70, 30}, {0.5f, 70, 70}, {0.5f, 30, 70}};
    const std::vector<IndoorFacePoint> distant = {{5, 30, 30}, {5, 70, 30}, {5, 70, 70}, {5, 30, 70}};
    CHECK(reach(wall, plaque));
    CHECK_FALSE(reach(wall, distant));
    // A face crossing the wall.
    const std::vector<IndoorFacePoint> crossing = {{-10, 50, 20}, {10, 50, 20}, {10, 50, 60}, {-10, 50, 60}};
    CHECK(reach(wall, crossing));
    // Either winding of the face.
    const std::vector<IndoorFacePoint> reversed(wall.rbegin(), wall.rend());
    CHECK(reach(reversed, cornice));
    CHECK_FALSE(reach(reversed, floor));
}

TEST_CASE("indoor faces need a draw order only where they overlap nearly parallel")
{
    using OpenYAMM::Game::IndoorFacePoint;
    using OpenYAMM::Game::indoorFacesMeetAtOneDepth;
    using OpenYAMM::Game::makeIndoorFaceShape;
    const auto meet = [](const std::vector<IndoorFacePoint> &first, const std::vector<IndoorFacePoint> &second)
    {
        return indoorFacesMeetAtOneDepth(makeIndoorFaceShape(first), makeIndoorFaceShape(second), 1.0f, 0.01f);
    };
    const std::vector<IndoorFacePoint> wall = {{0, 0, 0}, {0, 100, 0}, {0, 100, 100}, {0, 0, 100}};
    const std::vector<IndoorFacePoint> floor = {{-50, -50, 0}, {100, -50, 0}, {100, 150, 0}, {-50, 150, 0}};
    // A wall standing on a floor and a face crossing the wall tie only along the line where they meet.
    CHECK_FALSE(meet(floor, wall));
    const std::vector<IndoorFacePoint> crossing = {{-10, 50, 20}, {10, 50, 20}, {10, 50, 60}, {-10, 50, 60}};
    CHECK_FALSE(meet(wall, crossing));
    // A panel over the wall, coincident or half a unit off, either order and either winding.
    const std::vector<IndoorFacePoint> plaque = {{0.5f, 30, 30}, {0.5f, 70, 30}, {0.5f, 70, 70}, {0.5f, 30, 70}};
    const std::vector<IndoorFacePoint> backToBack(wall.rbegin(), wall.rend());
    CHECK(meet(wall, plaque));
    CHECK(meet(plaque, wall));
    CHECK(meet(wall, backToBack));
    // A panel leaning 10 degrees off the wall still covers it at one depth near its foot; at 60 degrees only a line.
    const float lean10 = 17.6f;
    const std::vector<IndoorFacePoint> leaning = {{0, 30, 0}, {0, 70, 0}, {lean10, 70, 100}, {lean10, 30, 100}};
    CHECK(meet(wall, leaning));
    const float lean60 = 173.2f;
    const std::vector<IndoorFacePoint> steep = {{0, 30, 0}, {0, 70, 0}, {lean60, 70, 100}, {lean60, 30, 100}};
    CHECK_FALSE(meet(wall, steep));
    // Faces that only share an edge.
    const std::vector<IndoorFacePoint> nextWall = {{0, 100, 0}, {0, 200, 0}, {0, 200, 100}, {0, 100, 100}};
    CHECK_FALSE(meet(wall, nextWall));
}
