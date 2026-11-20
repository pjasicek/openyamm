#include "game/gameplay/WorldItemSpotter.h"

#include <doctest/doctest.h>

#include <vector>

using OpenYAMM::Game::WorldItemSpotter;

namespace
{
// Items on a line along x; the ones in `hidden` have something of the map in front of them.
struct SpotterWorld
{
    std::vector<float> itemX;
    std::vector<bool> spotted;
    std::vector<bool> hidden;
    size_t rays = 0;

    explicit SpotterWorld(std::vector<float> x)
        : itemX(std::move(x))
        , spotted(itemX.size(), false)
        , hidden(itemX.size(), false)
    {
    }

    size_t update(WorldItemSpotter &spotter, float seconds, float eyeX, float radius = 1000.0f)
    {
        const size_t cast = spotter.update(
            seconds,
            radius,
            bx::Vec3{eyeX, 0.0f, 0.0f},
            itemX.size(),
            [this](size_t index) -> std::optional<bx::Vec3>
            {
                if (spotted[index])
                {
                    return std::nullopt;
                }

                return bx::Vec3{itemX[index], 0.0f, 0.0f};
            },
            [this](size_t index, const bx::Vec3 &, const bx::Vec3 &)
            {
                ++rays;

                if (!hidden[index])
                {
                    spotted[index] = true;
                }
            });
        return cast;
    }
};
}

TEST_CASE("World item spotter checks a quarter second apart and only within its radius")
{
    WorldItemSpotter spotter;
    SpotterWorld world({100.0f, 5000.0f});
    CHECK(world.update(spotter, 0.1f, 0.0f) == 0);
    CHECK(world.update(spotter, 0.1f, 0.0f) == 0);
    CHECK(world.update(spotter, 0.1f, 0.0f) == 1);
    CHECK(world.spotted[0]);
    CHECK_FALSE(world.spotted[1]);
}

TEST_CASE("World item spotter casts at most two rays a check and carries on where it stopped")
{
    WorldItemSpotter spotter;
    SpotterWorld world({10.0f, 20.0f, 30.0f, 40.0f, 50.0f});
    CHECK(world.update(spotter, 0.25f, 0.0f) == 2);
    CHECK(world.update(spotter, 0.25f, 0.0f) == 2);
    CHECK(world.update(spotter, 0.25f, 0.0f) == 1);
    CHECK(world.rays == 5);

    for (bool spotted : world.spotted)
    {
        CHECK(spotted);
    }

    // Everything is spotted: nothing is a candidate any more.
    CHECK(world.update(spotter, 5.0f, 600.0f) == 0);
}

TEST_CASE("World item spotter rests while the party stays put and tries hidden items again once it moves or waits")
{
    WorldItemSpotter spotter;
    SpotterWorld world({10.0f, 20.0f, 30.0f});
    world.hidden = {true, true, true};
    CHECK(world.update(spotter, 0.25f, 0.0f) == 2);
    CHECK(world.update(spotter, 0.25f, 0.0f) == 1);
    // The pass is over and the party stands still: no rays.
    CHECK(world.update(spotter, 0.25f, 0.0f) == 0);
    CHECK(world.update(spotter, 0.25f, 50.0f) == 0);
    // Moving far enough tries them again.
    CHECK(world.update(spotter, 0.25f, 200.0f) == 2);
    CHECK(world.update(spotter, 0.25f, 200.0f) == 1);
    CHECK(world.update(spotter, 0.25f, 200.0f) == 0);
    // So does waiting (a door opened meanwhile).
    world.hidden[1] = false;

    for (int check = 0; check < 6; ++check)
    {
        CHECK(world.update(spotter, 0.25f, 200.0f) == 0);
    }

    world.update(spotter, 0.25f, 200.0f);
    world.update(spotter, 0.25f, 200.0f);
    CHECK(world.spotted[1]);
}

TEST_CASE("World item spotter wakes when an item comes or goes")
{
    WorldItemSpotter spotter;
    SpotterWorld world({10.0f});
    world.hidden = {true};
    CHECK(world.update(spotter, 0.25f, 0.0f) == 1);
    CHECK(world.update(spotter, 0.25f, 0.0f) == 0);
    world.itemX.push_back(20.0f);
    world.spotted.push_back(false);
    world.hidden.push_back(false);
    CHECK(world.update(spotter, 0.25f, 0.0f) == 2);
    CHECK(world.spotted[1]);
}
