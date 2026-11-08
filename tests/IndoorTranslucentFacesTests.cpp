#include "doctest/doctest.h"

#include "game/indoor/IndoorMapData.h"
#include "game/indoor/IndoorTranslucentFaces.h"
#include "game/maps/IndoorSceneYml.h"

#include <string>
#include <vector>

namespace
{
using OpenYAMM::Game::IndoorFaceTranslucency;
using OpenYAMM::Game::IndoorMapData;
using OpenYAMM::Game::IndoorSceneTranslucentFaces;
using OpenYAMM::Game::IndoorTranslucentDraw;
using OpenYAMM::Game::IndoorTranslucentFace;

std::vector<IndoorSceneTranslucentFaces> parse(const std::string &text, bool expectSuccess = true)
{
    std::vector<IndoorSceneTranslucentFaces> entries;
    std::string error;
    CHECK(OpenYAMM::Game::parseIndoorSceneTranslucentFaces(text, entries, error) == expectSuccess);
    CHECK(error.empty() == expectSuccess);
    return entries;
}
}

TEST_CASE("indoor translucent faces parse from the scene with defaults")
{
    const std::vector<IndoorSceneTranslucentFaces> entries = parse(
        "- {faces: [7, 3], opacity: 0.5, tint: [0.8, 0.9, 1.0], two_sided: true}\n"
        "- {faces: [12]}\n");
    REQUIRE(entries.size() == 2);
    CHECK(entries[0].faceIds == std::vector<uint16_t>{7, 3});
    CHECK(entries[0].translucency.opacity == doctest::Approx(0.5f));
    CHECK(entries[0].translucency.tint[1] == doctest::Approx(0.9f));
    CHECK(entries[0].translucency.twoSided);
    CHECK(entries[1].translucency == IndoorFaceTranslucency{});

    parse("{faces: [1]}", false);
    parse("- {opacity: 0.5}", false);
    parse("- {faces: []}", false);
    parse("- {faces: [1], tint: [1, 1]}", false);
    parse("- {faces: [-1]}", false);
}

TEST_CASE("indoor translucent faces build sorted and validated per map")
{
    std::vector<IndoorTranslucentFace> faces;
    std::string error;
    const std::vector<IndoorSceneTranslucentFaces> entries = parse(
        "- {faces: [9, 2], opacity: 0.25}\n- {faces: [5], tint: [0.5, 0.5, 1]}\n");
    REQUIRE(OpenYAMM::Game::buildIndoorTranslucentFaces(entries, 10, faces, error));
    REQUIRE(faces.size() == 3);
    CHECK(faces[0].faceIndex == 2);
    CHECK(faces[1].faceIndex == 5);
    CHECK(faces[1].translucency.tint[0] == doctest::Approx(0.5f));
    CHECK(faces[2].faceIndex == 9);
    CHECK(faces[2].translucency.opacity == doctest::Approx(0.25f));

    CHECK_FALSE(OpenYAMM::Game::buildIndoorTranslucentFaces(entries, 9, faces, error));
    CHECK(error.find("out of range") != std::string::npos);
    CHECK_FALSE(OpenYAMM::Game::buildIndoorTranslucentFaces(parse("- {faces: [1]}\n- {faces: [1]}\n"), 10, faces,
        error));
    CHECK(error.find("twice") != std::string::npos);
    CHECK_FALSE(OpenYAMM::Game::buildIndoorTranslucentFaces(parse("- {faces: [1], opacity: 1.5}"), 10, faces, error));
    CHECK_FALSE(OpenYAMM::Game::buildIndoorTranslucentFaces(parse("- {faces: [1], tint: [1, -1, 1]}"), 10, faces,
        error));

    // A scene without translucent faces leaves the map without any: the renderer's opaque-only fast path.
    REQUIRE(OpenYAMM::Game::buildIndoorTranslucentFaces({}, 10, faces, error));
    CHECK(faces.empty());
}

TEST_CASE("indoor translucent face lookup")
{
    IndoorMapData map;
    CHECK(OpenYAMM::Game::findIndoorFaceTranslucency(map, 0) == nullptr);
    map.translucentFaces = {{2, {0.5f, {1.0f, 1.0f, 1.0f}, false}}, {40, {0.75f, {0.5f, 0.5f, 1.0f}, true}}};
    CHECK(OpenYAMM::Game::findIndoorFaceTranslucency(map, 1) == nullptr);
    REQUIRE(OpenYAMM::Game::findIndoorFaceTranslucency(map, 2) != nullptr);
    CHECK(OpenYAMM::Game::findIndoorFaceTranslucency(map, 2)->opacity == doctest::Approx(0.5f));
    REQUIRE(OpenYAMM::Game::findIndoorFaceTranslucency(map, 40) != nullptr);
    CHECK(OpenYAMM::Game::findIndoorFaceTranslucency(map, 40)->twoSided);
    CHECK(OpenYAMM::Game::findIndoorFaceTranslucency(map, 41) == nullptr);
    CHECK(OpenYAMM::Game::findIndoorFaceTranslucency(map, 70000) == nullptr);
}

TEST_CASE("indoor opaque face lookup")
{
    IndoorMapData map;
    CHECK_FALSE(OpenYAMM::Game::isIndoorFaceOpaque(map, 0));
    map.opaqueFaces = {3, 17};
    CHECK(OpenYAMM::Game::isIndoorFaceOpaque(map, 3));
    CHECK(OpenYAMM::Game::isIndoorFaceOpaque(map, 17));
    CHECK_FALSE(OpenYAMM::Game::isIndoorFaceOpaque(map, 4));
    CHECK_FALSE(OpenYAMM::Game::isIndoorFaceOpaque(map, 70000));
}

TEST_CASE("indoor translucent faces draw back to front")
{
    std::vector<IndoorTranslucentDraw> draws = {{0, 100.0f}, {1, 900.0f}, {2, 400.0f}, {3, 900.0f}};
    OpenYAMM::Game::sortIndoorTranslucentDrawsBackToFront(draws);
    REQUIRE(draws.size() == 4);
    CHECK(draws[0].batchIndex == 1);
    CHECK(draws[1].batchIndex == 3);
    CHECK(draws[2].batchIndex == 2);
    CHECK(draws[3].batchIndex == 0);
}

TEST_CASE("indoor translucent faces are single-sided unless the data says otherwise")
{
    IndoorFaceTranslucency translucency;
    const std::array<float, 3> normal = {0.0f, 1.0f, 0.0f};
    const std::array<float, 3> point = {10.0f, 20.0f, 30.0f};
    CHECK(OpenYAMM::Game::indoorTranslucentFaceVisibleFrom(translucency, normal, point, {0.0f, 25.0f, 0.0f}));
    CHECK_FALSE(OpenYAMM::Game::indoorTranslucentFaceVisibleFrom(translucency, normal, point, {0.0f, 15.0f, 0.0f}));
    translucency.twoSided = true;
    CHECK(OpenYAMM::Game::indoorTranslucentFaceVisibleFrom(translucency, normal, point, {0.0f, 15.0f, 0.0f}));
}
