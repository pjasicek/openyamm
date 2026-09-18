#include "doctest/doctest.h"

#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorMapData.h"

#include <cmath>

namespace
{
OpenYAMM::Game::OutdoorBModel quadBModel()
{
    OpenYAMM::Game::OutdoorBModel bmodel = {};
    bmodel.vertices = {
        {0, 0, 0},
        {512, 0, 0},
        {512, 512, 0},
        {0, 512, 0},
    };

    OpenYAMM::Game::OutdoorBModelFace face = {};
    face.vertexIndices = {0, 1, 2, 3};
    face.textureName = "quad";
    bmodel.faces.push_back(face);
    return bmodel;
}
}

TEST_CASE("outdoor face geometry produces a flat unit quad normal")
{
    OpenYAMM::Game::OutdoorBModel bmodel = quadBModel();
    OpenYAMM::Game::OutdoorFaceGeometryData geometry = {};

    REQUIRE(OpenYAMM::Game::buildOutdoorFaceGeometry(bmodel, 0, bmodel.faces.front(), 0, geometry, true));
    REQUIRE(geometry.hasPlane);

    // Vertices wind counter-clockwise in the XY plane; the cross product faces +Z.
    CHECK(geometry.normal.x == doctest::Approx(0.0f).epsilon(0.001f));
    CHECK(geometry.normal.y == doctest::Approx(0.0f).epsilon(0.001f));
    CHECK(geometry.normal.z == doctest::Approx(1.0f).epsilon(0.001f));
}

TEST_CASE("outdoor face geometry keeps degenerate faces plane-less instead of normalizing zero")
{
    OpenYAMM::Game::OutdoorBModel bmodel = quadBModel();
    bmodel.vertices[1] = {1024, 0, 0};
    bmodel.vertices[2] = {2048, 0, 0};

    OpenYAMM::Game::OutdoorFaceGeometryData geometry = {};

    // The first three vertices are collinear, so no plane exists.
    REQUIRE(OpenYAMM::Game::buildOutdoorFaceGeometry(bmodel, 0, bmodel.faces.front(), 0, geometry, true));
    CHECK(!geometry.hasPlane);
}

TEST_CASE("outdoor face geometry rejects faces with out-of-range vertices")
{
    OpenYAMM::Game::OutdoorBModel bmodel = quadBModel();
    bmodel.faces.front().vertexIndices = {0, 1, 4096};

    OpenYAMM::Game::OutdoorFaceGeometryData geometry = {};
    CHECK(!OpenYAMM::Game::buildOutdoorFaceGeometry(bmodel, 0, bmodel.faces.front(), 0, geometry, true));
}

TEST_CASE("bmodel direction transform rotates normals without translation or pivot")
{
    OpenYAMM::Game::OutdoorBModelTransform transform = {};
    transform.pivotX = 100.0f;
    transform.pivotY = -50.0f;
    transform.pivotZ = 25.0f;
    transform.translationX = 512.0f;
    transform.translationY = -512.0f;
    transform.translationZ = 256.0f;
    transform.rotationDegreesZ = 90.0f;

    const bx::Vec3 rotated = OpenYAMM::Game::transformOutdoorBModelDirection(
        {1.0f, 0.0f, 0.0f}, transform, 1.0f);

    CHECK(rotated.x == doctest::Approx(0.0f).epsilon(0.001f));
    CHECK(rotated.y == doctest::Approx(1.0f).epsilon(0.001f));
    CHECK(rotated.z == doctest::Approx(0.0f).epsilon(0.001f));

    const bx::Vec3 rotatedX = OpenYAMM::Game::transformOutdoorBModelDirection(
        {0.0f, 0.0f, 1.0f},
        []() { OpenYAMM::Game::OutdoorBModelTransform t = {}; t.rotationDegreesX = 90.0f; return t; }(),
        1.0f);
    CHECK(rotatedX.x == doctest::Approx(0.0f).epsilon(0.001f));
    CHECK(rotatedX.y == doctest::Approx(-1.0f).epsilon(0.001f));
    CHECK(rotatedX.z == doctest::Approx(0.0f).epsilon(0.001f));

    const bx::Vec3 rotatedY = OpenYAMM::Game::transformOutdoorBModelDirection(
        {1.0f, 0.0f, 0.0f},
        []() { OpenYAMM::Game::OutdoorBModelTransform t = {}; t.rotationDegreesY = 90.0f; return t; }(),
        1.0f);
    CHECK(rotatedY.x == doctest::Approx(0.0f).epsilon(0.001f));
    CHECK(rotatedY.y == doctest::Approx(0.0f).epsilon(0.001f));
    CHECK(rotatedY.z == doctest::Approx(-1.0f).epsilon(0.001f));
}

TEST_CASE("bmodel direction transform applies the mechanism fraction and renormalizes")
{
    OpenYAMM::Game::OutdoorBModelTransform transform = {};
    transform.rotationDegreesZ = 90.0f;

    const bx::Vec3 halfRotated = OpenYAMM::Game::transformOutdoorBModelDirection(
        {1.0f, 0.0f, 0.0f}, transform, 0.5f);
    CHECK(halfRotated.x == doctest::Approx(std::cos(static_cast<float>(M_PI) * 0.25f)).epsilon(0.001f));
    CHECK(halfRotated.y == doctest::Approx(std::sin(static_cast<float>(M_PI) * 0.25f)).epsilon(0.001f));

    // Renormalization keeps a scaled input unit-length.
    const bx::Vec3 scaled = OpenYAMM::Game::transformOutdoorBModelDirection(
        {10.0f, 0.0f, 0.0f},
        []() { OpenYAMM::Game::OutdoorBModelTransform t = {}; return t; }(),
        1.0f);
    CHECK(scaled.x == doctest::Approx(1.0f));
    CHECK(scaled.y == doctest::Approx(0.0f));
    CHECK(scaled.z == doctest::Approx(0.0f));
}

TEST_CASE("bmodel direction transform keeps zero normals zero")
{
    OpenYAMM::Game::OutdoorBModelTransform transform = {};
    transform.rotationDegreesX = 90.0f;
    transform.rotationDegreesY = 90.0f;
    transform.rotationDegreesZ = 90.0f;

    const bx::Vec3 rotated = OpenYAMM::Game::transformOutdoorBModelDirection(
        {0.0f, 0.0f, 0.0f}, transform, 1.0f);
    CHECK(rotated.x == 0.0f);
    CHECK(rotated.y == 0.0f);
    CHECK(rotated.z == 0.0f);
}
