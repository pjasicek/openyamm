#include "doctest/doctest.h"

#include "game/mm9/Mm9SkyLayer.h"

#include <optional>
#include <string>
#include <vector>

namespace
{
OpenYAMM::Game::Mm9DatVec3 vec3(float x, float y, float z)
{
    return {x, y, z};
}

void checkVec3Approx(
    const OpenYAMM::Game::Mm9DatVec3 &actual,
    const OpenYAMM::Game::Mm9DatVec3 &expected)
{
    CHECK(actual.x == doctest::Approx(expected.x));
    CHECK(actual.y == doctest::Approx(expected.y));
    CHECK(actual.z == doctest::Approx(expected.z));
}

OpenYAMM::Game::Mm9DatWorld testWorld()
{
    OpenYAMM::Game::Mm9DatWorld world = {};
    world.worldInfo.extentsMinLt = vec3(0.0f, 0.0f, 0.0f);
    world.worldInfo.extentsMaxLt = vec3(1000.0f, 2000.0f, 3000.0f);

    OpenYAMM::Game::Mm9DatWorldModel skyBox = {};
    skyBox.name = "SkyBox0";
    world.worldModels.push_back(skyBox);

    OpenYAMM::Game::Mm9DatWorldModel todSky = {};
    todSky.name = "TOD_Sky0";
    world.worldModels.push_back(todSky);

    OpenYAMM::Game::Mm9DatWorldModel normalModel = {};
    normalModel.name = "NormalModel";
    world.worldModels.push_back(normalModel);

    return world;
}

OpenYAMM::Game::Mm9SkySourceObject demoSkyWorldModel(
    size_t sourceObjectIndex,
    const std::string &name,
    const OpenYAMM::Game::Mm9DatVec3 &skyDimsLt,
    int index = 0)
{
    OpenYAMM::Game::Mm9SkySourceObject object = {};
    object.sourceObjectIndex = sourceObjectIndex;
    object.sourceClass = "DemoSkyWorldModel";
    object.sourceName = name;
    object.properties = {
        OpenYAMM::Game::mm9SkyStringProperty("Name", name),
        OpenYAMM::Game::mm9SkyVec3Property("Pos", vec3(100.0f, 200.0f, 300.0f)),
        OpenYAMM::Game::mm9SkyVec3Property("SkyDims", skyDimsLt),
        OpenYAMM::Game::mm9SkyIntegerProperty("Flags", 1),
        OpenYAMM::Game::mm9SkyIntegerProperty("Index", index),
    };
    return object;
}

OpenYAMM::Game::Mm9SkySourceObject skyPointer(
    size_t sourceObjectIndex,
    const std::string &name,
    const std::string &skyObjectName,
    int index)
{
    OpenYAMM::Game::Mm9SkySourceObject object = {};
    object.sourceObjectIndex = sourceObjectIndex;
    object.sourceClass = "SkyPointer";
    object.sourceName = name;
    object.properties = {
        OpenYAMM::Game::mm9SkyStringProperty("Name", name),
        OpenYAMM::Game::mm9SkyStringProperty("SkyObjectName", skyObjectName),
        OpenYAMM::Game::mm9SkyVec3Property("Pos", vec3(400.0f, 500.0f, 600.0f)),
        OpenYAMM::Game::mm9SkyVec3Property("SkyDims", vec3(0.0f, 0.0f, 0.0f)),
        OpenYAMM::Game::mm9SkyIntegerProperty("Flags", 3),
        OpenYAMM::Game::mm9SkyIntegerProperty("Index", index),
    };
    return object;
}

OpenYAMM::Game::Mm9SkySourceObject todSky(
    size_t sourceObjectIndex,
    const std::string &name,
    int index)
{
    OpenYAMM::Game::Mm9SkySourceObject object = {};
    object.sourceObjectIndex = sourceObjectIndex;
    object.sourceClass = "TOD_Sky";
    object.sourceName = name;
    object.properties = {
        OpenYAMM::Game::mm9SkyStringProperty("Name", name),
        OpenYAMM::Game::mm9SkyIntegerProperty("Index", index),
    };
    return object;
}
}

TEST_CASE("MM9 sky layer definition construction follows LithTech sky dimensions")
{
    const OpenYAMM::Game::Mm9SkyDef skyDef = OpenYAMM::Game::makeMm9SkyDef(
        7,
        "DemoSkyWorldModel",
        "SkyBox0",
        vec3(100.0f, 200.0f, 300.0f),
        vec3(10.0f, 20.0f, 30.0f),
        vec3(0.1f, 0.2f, 0.3f),
        9,
        2);

    CHECK(skyDef.valid);
    CHECK(skyDef.sourceObjectIndex == 7);
    CHECK(skyDef.flags == 9);
    CHECK(skyDef.index == 2);
    checkVec3Approx(skyDef.minLt, vec3(90.0f, 180.0f, 270.0f));
    checkVec3Approx(skyDef.maxLt, vec3(110.0f, 220.0f, 330.0f));
    checkVec3Approx(skyDef.viewMinLt, vec3(99.0f, 196.0f, 291.0f));
    checkVec3Approx(skyDef.viewMaxLt, vec3(101.0f, 204.0f, 309.0f));
}

TEST_CASE("MM9 sky layer definition with zero dimensions is preserved but inactive")
{
    const OpenYAMM::Game::Mm9SkyDef skyDef = OpenYAMM::Game::makeMm9SkyDef(
        1,
        "SkyPointer",
        "SkyPointer0",
        vec3(100.0f, 200.0f, 300.0f),
        vec3(0.0f, 128.0f, 128.0f),
        vec3(0.1f, 0.1f, 0.1f),
        0,
        0);

    CHECK(!skyDef.valid);
    CHECK(skyDef.sourceObjectIndex == 1);
    checkVec3Approx(skyDef.skyDimsLt, vec3(0.0f, 128.0f, 128.0f));
}

TEST_CASE("MM9 sky layer links demo sky models and sky pointers to DAT world models")
{
    const OpenYAMM::Game::Mm9DatWorld world = testWorld();
    const std::vector<OpenYAMM::Game::Mm9SkySourceObject> sourceObjects = {
        demoSkyWorldModel(10, "SkyBox0", vec3(128.0f, 128.0f, 128.0f), 4),
        skyPointer(11, "SkyPointer0", "TOD_Sky0", 1),
        skyPointer(12, "BrokenPointer", "MissingSky", 2),
        todSky(13, "TOD_Sky0", 3),
    };

    OpenYAMM::Game::Mm9DatModelRenderRole role = {};
    role.sourceModelIndex = 1;
    role.sky = true;

    const OpenYAMM::Game::Mm9SkyLayer layer =
        OpenYAMM::Game::buildMm9SkyLayer(world, sourceObjects, {role});

    REQUIRE(layer.objects.size() == 4);
    CHECK(layer.objects[0].sourceName == "SkyPointer0");
    CHECK(layer.objects[0].skyObjectName == "TOD_Sky0");
    CHECK(layer.objects[0].hasSourceModel);
    CHECK(layer.objects[0].sourceModelIndex == 1);
    CHECK(layer.objects[0].flags == 3);
    CHECK(layer.objects[1].sourceName == "BrokenPointer");
    CHECK(layer.objects[1].skyObjectName == "MissingSky");
    CHECK(!layer.objects[1].hasSourceModel);
    CHECK(layer.objects[2].sourceName == "TOD_Sky0");
    CHECK(layer.objects[2].hasSourceModel);
    CHECK(layer.objects[2].sourceModelIndex == 1);
    CHECK(layer.objects[3].sourceName == "SkyBox0");
    CHECK(layer.objects[3].hasSourceModel);
    CHECK(layer.objects[3].sourceModelIndex == 0);
    CHECK(layer.objects[3].flags == 1);

    REQUIRE(layer.skyModelIndices.size() == 2);
    CHECK(layer.skyModelIndices[0] == 0);
    CHECK(layer.skyModelIndices[1] == 1);
    REQUIRE(layer.diagnostics.size() == 1);
    CHECK(layer.diagnostics[0].sourceObjectIndex == 12);
    CHECK(layer.diagnostics[0].message == "unlinked_sky_model");
}

TEST_CASE("MM9 sky layer defaults inner percents and selects active definition deterministically")
{
    const OpenYAMM::Game::Mm9DatWorld world = testWorld();
    std::vector<OpenYAMM::Game::Mm9SkySourceObject> sourceObjects = {
        demoSkyWorldModel(30, "SkyBox0", vec3(100.0f, 200.0f, 300.0f), 5),
        demoSkyWorldModel(20, "TOD_Sky0", vec3(80.0f, 90.0f, 100.0f), 1),
    };
    sourceObjects[1].properties.push_back(OpenYAMM::Game::mm9SkyNumberProperty("InnerPercentX", 0.25f));
    sourceObjects[1].properties.push_back(OpenYAMM::Game::mm9SkyNumberProperty("InnerPercentY", 0.5f));
    sourceObjects[1].properties.push_back(OpenYAMM::Game::mm9SkyNumberProperty("InnerPercentZ", 0.75f));

    const OpenYAMM::Game::Mm9SkyLayer layer = OpenYAMM::Game::buildMm9SkyLayer(world, sourceObjects);
    const std::optional<OpenYAMM::Game::Mm9SkyDef> activeDefinition =
        OpenYAMM::Game::selectActiveMm9SkyDef(layer);

    REQUIRE(activeDefinition.has_value());
    CHECK(activeDefinition->sourceObjectIndex == 20);
    checkVec3Approx(activeDefinition->innerPercentLt, vec3(0.25f, 0.5f, 0.75f));
    checkVec3Approx(activeDefinition->viewMinLt, vec3(80.0f, 155.0f, 225.0f));
    checkVec3Approx(activeDefinition->viewMaxLt, vec3(120.0f, 245.0f, 375.0f));

    REQUIRE(layer.definitions.size() == 2);
    CHECK(layer.definitions[0].sourceObjectIndex == 20);
    CHECK(layer.definitions[1].sourceObjectIndex == 30);
    checkVec3Approx(layer.definitions[1].innerPercentLt, vec3(0.1f, 0.1f, 0.1f));
}

TEST_CASE("MM9 sky layer camera maps DAT world extents into active sky view extents")
{
    const OpenYAMM::Game::Mm9DatWorld world = testWorld();
    const OpenYAMM::Game::Mm9SkyDef skyDef = OpenYAMM::Game::makeMm9SkyDef(
        0,
        "DemoSkyWorldModel",
        "SkyBox0",
        vec3(100.0f, 200.0f, 300.0f),
        vec3(100.0f, 100.0f, 100.0f),
        vec3(0.1f, 0.2f, 0.3f),
        0,
        0);

    const std::optional<OpenYAMM::Game::Mm9DatVec3> atMin =
        OpenYAMM::Game::computeMm9SkyCameraPositionLt(
            world.worldInfo,
            skyDef,
            world.worldInfo.extentsMinLt);
    const std::optional<OpenYAMM::Game::Mm9DatVec3> atMax =
        OpenYAMM::Game::computeMm9SkyCameraPositionLt(
            world.worldInfo,
            skyDef,
            world.worldInfo.extentsMaxLt);
    const std::optional<OpenYAMM::Game::Mm9DatVec3> atCenter =
        OpenYAMM::Game::computeMm9SkyCameraPositionLt(
            world.worldInfo,
            skyDef,
            vec3(500.0f, 1000.0f, 1500.0f));
    const std::optional<OpenYAMM::Game::Mm9DatVec3> outside =
        OpenYAMM::Game::computeMm9SkyCameraPositionLt(
            world.worldInfo,
            skyDef,
            vec3(2000.0f, -100.0f, 1500.0f));
    const std::optional<OpenYAMM::Game::Mm9SkyCameraMap> cameraMap =
        OpenYAMM::Game::buildMm9SkyCameraMap(world.worldInfo, skyDef);

    REQUIRE(atMin.has_value());
    REQUIRE(atMax.has_value());
    REQUIRE(atCenter.has_value());
    REQUIRE(outside.has_value());
    REQUIRE(cameraMap.has_value());
    checkVec3Approx(*atMin, skyDef.viewMinLt);
    checkVec3Approx(*atMax, skyDef.viewMaxLt);
    checkVec3Approx(*atCenter, vec3(100.0f, 200.0f, 300.0f));
    checkVec3Approx(*outside, vec3(130.0f, 178.0f, 300.0f));
    checkVec3Approx(
        OpenYAMM::Game::computeMm9SkyCameraPositionLt(
            *cameraMap,
            vec3(500.0f, 1000.0f, 1500.0f)),
        *atCenter);
}

TEST_CASE("MM9 sky layer camera rejects inactive definitions and degenerate world extents")
{
    OpenYAMM::Game::Mm9DatWorld world = testWorld();
    OpenYAMM::Game::Mm9SkyDef skyDef = OpenYAMM::Game::makeMm9SkyDef(
        0,
        "DemoSkyWorldModel",
        "SkyBox0",
        vec3(100.0f, 200.0f, 300.0f),
        vec3(100.0f, 100.0f, 100.0f),
        vec3(0.1f, 0.1f, 0.1f),
        0,
        0);

    skyDef.valid = false;
    CHECK(!OpenYAMM::Game::buildMm9SkyCameraMap(world.worldInfo, skyDef).has_value());
    CHECK(!OpenYAMM::Game::computeMm9SkyCameraPositionLt(
        world.worldInfo,
        skyDef,
        vec3(500.0f, 1000.0f, 1500.0f)).has_value());

    skyDef.valid = true;
    world.worldInfo.extentsMaxLt.x = world.worldInfo.extentsMinLt.x;
    CHECK(!OpenYAMM::Game::buildMm9SkyCameraMap(world.worldInfo, skyDef).has_value());
    CHECK(!OpenYAMM::Game::computeMm9SkyCameraPositionLt(
        world.worldInfo,
        skyDef,
        vec3(500.0f, 1000.0f, 1500.0f)).has_value());
}
