#include "game/maps/DecorationModelPlacement.h"

#include <doctest/doctest.h>

#include <cmath>

using namespace OpenYAMM;

TEST_CASE("decoration flame cards are picked facing the viewer")
{
    // Asset x is across the card, asset y up; the placement scales by 2 and stands at (100, 200, 10).
    const Engine::ModelMatrix placement =
        Engine::composeModelTransform(Engine::gltfModelPlacement({100.0f, 200.0f, 10.0f}, 0.7f, 2.0f));
    const std::array<float, 3> corner = {1.0f, 3.0f, 0.0f};
    const std::array<std::array<float, 3>, 3> viewers = {{{100.0f, -300.0f, 50.0f}, {600.0f, 200.0f, 0.0f},
        {-100.0f, 400.0f, 90.0f}}};
    for (const std::array<float, 3> &viewer : viewers)
    {
        const std::array<float, 3> world = Game::facingCardCorner(placement, corner, viewer);
        const float offsetX = world[0] - 100.0f;
        const float offsetY = world[1] - 200.0f;
        // Height and the offset across the card are kept; the card is square to the view direction.
        CHECK(world[2] == doctest::Approx(16.0f));
        CHECK(std::sqrt(offsetX * offsetX + offsetY * offsetY) == doctest::Approx(2.0f));
        CHECK(offsetX * (viewer[0] - 100.0f) + offsetY * (viewer[1] - 200.0f) == doctest::Approx(0.0f).epsilon(1e-4));
    }
    // Viewed from the south (-y) the card's +x edge lies east, from the east it lies north.
    const std::array<float, 3> south = Game::facingCardCorner(placement, corner, {100.0f, -300.0f, 0.0f});
    CHECK(south[0] == doctest::Approx(102.0f));
    const std::array<float, 3> east = Game::facingCardCorner(placement, corner, {600.0f, 200.0f, 0.0f});
    CHECK(east[1] == doctest::Approx(202.0f));
}

TEST_CASE("wall-mounted decorations face away from their wall with their back on it")
{
    // A wall along x through y = 50, the decoration on its +y side; the model's back is 0.5 asset units deep.
    const Game::DecorationWallContact wall = {{120.0f, 50.0f}, {0.0f, 1.0f}};
    const Engine::ModelMatrix placement = Game::wallMountedPlacement(wall, -0.5f, 30.0f, 40.0f);
    // The asset front (+z) points along the wall normal; the asset back plane lies on the wall.
    CHECK(placement[8] == doctest::Approx(0.0f).epsilon(1e-4));
    CHECK(placement[9] == doctest::Approx(40.0f));
    CHECK(placement[12] == doctest::Approx(120.0f));
    CHECK(placement[13] == doctest::Approx(70.0f));
    CHECK(placement[14] == doctest::Approx(30.0f));
    // Asset up stays map up.
    CHECK(placement[6] == doctest::Approx(40.0f));
    const Engine::ModelMatrix east = Game::wallMountedPlacement({{0.0f, 0.0f}, {1.0f, 0.0f}}, -0.5f, 0.0f, 1.0f);
    CHECK(east[8] == doctest::Approx(1.0f));
    CHECK(east[9] == doctest::Approx(0.0f).epsilon(1e-4));
}

TEST_CASE("swinging decorations turn about their top pivot")
{
    const Engine::ModelMatrix identity = Engine::identityModelMatrix();
    const std::array<float, 3> pivot = {0.0f, 2.0f, 0.0f};
    const Engine::ModelMatrix swung = Game::swungPlacement(identity, pivot, 0.3f);
    // The pivot stays; a point below it moves along z by sin(angle) of its distance.
    const auto apply = [&](const std::array<float, 3> &p)
    {
        return std::array<float, 3>{swung[0] * p[0] + swung[4] * p[1] + swung[8] * p[2] + swung[12],
            swung[1] * p[0] + swung[5] * p[1] + swung[9] * p[2] + swung[13],
            swung[2] * p[0] + swung[6] * p[1] + swung[10] * p[2] + swung[14]};
    };
    const std::array<float, 3> top = apply(pivot);
    CHECK(top[1] == doctest::Approx(2.0f));
    CHECK(top[2] == doctest::Approx(0.0f).epsilon(1e-5));
    const std::array<float, 3> bottom = apply({0.0f, 0.0f, 0.0f});
    CHECK(bottom[1] == doctest::Approx(2.0f - 2.0f * std::cos(0.3f)));
    CHECK(std::abs(bottom[2]) == doctest::Approx(2.0f * std::sin(0.3f)));
    CHECK(Game::swungPlacement(identity, pivot, 0.0f) == identity);
}
