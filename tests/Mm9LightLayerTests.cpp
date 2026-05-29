#include "doctest/doctest.h"

#include "game/mm9/Mm9LightLayer.h"

#include <cmath>
#include <optional>
#include <string>
#include <vector>

namespace
{
OpenYAMM::Game::Mm9DatVec3 vec3(float x, float y, float z)
{
    return {x, y, z};
}

void checkColorApprox(
    const OpenYAMM::Game::Mm9LightColor &actual,
    const OpenYAMM::Game::Mm9LightColor &expected)
{
    CHECK(actual.r == doctest::Approx(expected.r));
    CHECK(actual.g == doctest::Approx(expected.g));
    CHECK(actual.b == doctest::Approx(expected.b));
}

OpenYAMM::Game::Mm9LightSourceObject lightObject()
{
    OpenYAMM::Game::Mm9LightSourceObject object = {};
    object.sourceObjectIndex = 41;
    object.sourceClass = "Light";
    object.sourceName = "Light_Red";
    object.properties = {
        OpenYAMM::Game::mm9LightStringProperty("Name", "Light_Red"),
        OpenYAMM::Game::mm9LightVec3Property("Pos", vec3(10.0f, 20.0f, 30.0f)),
        OpenYAMM::Game::mm9LightVec3Property("Rotation", vec3(0.0f, 90.0f, 0.0f)),
        OpenYAMM::Game::mm9LightNumberProperty("LightRadius", 128.0f),
        OpenYAMM::Game::mm9LightVec3Property("LightColor", vec3(100.0f, 64.0f, 32.0f)),
        OpenYAMM::Game::mm9LightVec3Property("InnerColor", vec3(8.0f, 4.0f, 2.0f)),
        OpenYAMM::Game::mm9LightVec3Property("OuterColor", vec3(3.0f, 2.0f, 1.0f)),
        OpenYAMM::Game::mm9LightNumberProperty("BrightScale", 1.5f),
        OpenYAMM::Game::mm9LightNumberProperty("ObjectBrightScale", 0.75f),
        OpenYAMM::Game::mm9LightNumberListProperty("AttCoefs", {1.0f, 2.0f, 19.0f}),
        OpenYAMM::Game::mm9LightNumberListProperty("AttExps", {0.0f, 0.0f, -2.0f}),
        OpenYAMM::Game::mm9LightStringProperty("Attenuation", "Linear"),
        OpenYAMM::Game::mm9LightNumberProperty("Size", 7.0f),
        OpenYAMM::Game::mm9LightStringProperty("AttType", "Custom"),
        OpenYAMM::Game::mm9LightBooleanProperty("LightObjects", true),
        OpenYAMM::Game::mm9LightBooleanProperty("FastLightObjects", false),
        OpenYAMM::Game::mm9LightBooleanProperty("CastShadows", true),
        OpenYAMM::Game::mm9LightBooleanProperty("CastShadowMesh", true),
        OpenYAMM::Game::mm9LightBooleanProperty("ClipLight", true),
        OpenYAMM::Game::mm9LightNumberProperty("ConvertToAmbient", 0.25f),
        OpenYAMM::Game::mm9LightNumberProperty("FOV", 45.0f),
        OpenYAMM::Game::mm9LightNumberProperty("Time", 2.5f),
        OpenYAMM::Game::mm9LightStringProperty("LightGroup", "torches"),
        OpenYAMM::Game::mm9LightStringProperty("MysteryProperty", "preserved"),
    };
    return object;
}

OpenYAMM::Game::Mm9LightSourceObject lightObjectWithFlags(bool lightObjects, bool fastLightObjects)
{
    OpenYAMM::Game::Mm9LightSourceObject object = lightObject();
    for (OpenYAMM::Game::Mm9LightSourceProperty &property : object.properties)
    {
        if (property.name == "LightObjects")
        {
            property = OpenYAMM::Game::mm9LightBooleanProperty("LightObjects", lightObjects);
        }
        else if (property.name == "FastLightObjects")
        {
            property = OpenYAMM::Game::mm9LightBooleanProperty("FastLightObjects", fastLightObjects);
        }
    }
    return object;
}
}

TEST_CASE("MM9 light layer parses world info lighting fields without losing the raw string")
{
    OpenYAMM::Game::Mm9DatWorldInfo worldInfo = {};
    worldInfo.propertyString = "PBlockSize 8096 ; LMGridSize 64; MaxLMSize 128 ; AmbientLight -5 70 300";
    worldInfo.lightMapGridSize = 32.0f;

    const OpenYAMM::Game::Mm9WorldLightingInfo lightingInfo =
        OpenYAMM::Game::parseMm9WorldLightingInfo(worldInfo);

    CHECK(lightingInfo.rawPropertyString == worldInfo.propertyString);
    CHECK(lightingInfo.sourceLightMapGridSize == doctest::Approx(32.0f));
    REQUIRE(lightingInfo.hasAmbientLight);
    checkColorApprox(lightingInfo.ambientLight, {0.0f, 70.0f, 255.0f});
    CHECK(lightingInfo.hasLmGridSize);
    CHECK(lightingInfo.lmGridSize == doctest::Approx(64.0f));
    CHECK(lightingInfo.hasMaxLmSize);
    CHECK(lightingInfo.maxLmSize == doctest::Approx(128.0f));
    CHECK(lightingInfo.hasPBlockSize);
    CHECK(lightingInfo.pBlockSize == doctest::Approx(8096.0f));
    CHECK(lightingInfo.diagnostics.empty());
}

TEST_CASE("MM9 light layer keeps explicit world info defaults and reports invalid values")
{
    OpenYAMM::Game::Mm9DatWorldInfo worldInfo = {};
    worldInfo.propertyString = "AmbientLight bad 70 80 ; LMGridSize nope";

    const OpenYAMM::Game::Mm9WorldLightingInfo lightingInfo =
        OpenYAMM::Game::parseMm9WorldLightingInfo(worldInfo);

    CHECK(!lightingInfo.hasAmbientLight);
    CHECK(!lightingInfo.hasLmGridSize);
    CHECK(!lightingInfo.hasMaxLmSize);
    CHECK(!lightingInfo.hasPBlockSize);
    REQUIRE(lightingInfo.diagnostics.size() == 2);
    CHECK(lightingInfo.diagnostics[0].propertyName == "AmbientLight");
    CHECK(lightingInfo.diagnostics[0].message == "invalid_world_info_value");
}

TEST_CASE("MM9 light layer projects typed light objects and preserves source properties")
{
    OpenYAMM::Game::Mm9DatWorldInfo worldInfo = {};
    worldInfo.propertyString = "AmbientLight 10 20 30";
    const OpenYAMM::Game::Mm9LightLayer layer =
        OpenYAMM::Game::buildMm9LightLayer(worldInfo, {lightObject()});

    REQUIRE(layer.lights.size() == 1);
    const OpenYAMM::Game::Mm9LightObject &light = layer.lights[0];
    CHECK(light.sourceObjectIndex == 41);
    CHECK(light.sourceClass == "Light");
    CHECK(light.sourceName == "Light_Red");
    CHECK(light.hasPosition);
    CHECK(light.positionLt.x == doctest::Approx(10.0f));
    CHECK(light.hasRotation);
    CHECK(light.hasLightRadius);
    CHECK(light.lightRadius == doctest::Approx(128.0f));
    REQUIRE(light.hasLightColor);
    checkColorApprox(light.lightColor, {100.0f, 64.0f, 32.0f});
    REQUIRE(light.hasInnerColor);
    checkColorApprox(light.innerColor, {8.0f, 4.0f, 2.0f});
    REQUIRE(light.hasOuterColor);
    checkColorApprox(light.outerColor, {3.0f, 2.0f, 1.0f});
    CHECK(light.hasBrightScale);
    CHECK(light.brightScale == doctest::Approx(1.5f));
    CHECK(light.hasObjectBrightScale);
    CHECK(light.objectBrightScale == doctest::Approx(0.75f));
    CHECK(light.attCoefs.size() == 3);
    CHECK(light.attExps.size() == 3);
    CHECK(light.hasAttenuation);
    CHECK(light.validAttenuation);
    CHECK(light.attenuation == "Linear");
    CHECK(light.hasSize);
    CHECK(light.size == doctest::Approx(7.0f));
    CHECK(light.hasAttType);
    CHECK(light.attType == "Custom");
    CHECK(light.hasLightObjects);
    CHECK(light.lightObjects);
    CHECK(light.hasFastLightObjects);
    CHECK(!light.fastLightObjects);
    CHECK(light.hasCastShadows);
    CHECK(light.castShadows);
    CHECK(light.hasCastShadowMesh);
    CHECK(light.castShadowMesh);
    CHECK(light.hasClipLight);
    CHECK(light.clipLight);
    CHECK(light.hasConvertToAmbient);
    CHECK(light.convertToAmbient == doctest::Approx(0.25f));
    CHECK(light.hasFov);
    CHECK(light.fov == doctest::Approx(45.0f));
    CHECK(light.hasEffectiveFovCos);
    CHECK(light.effectiveFovCos == doctest::Approx(std::cos(45.0f * 3.14159265358979323846f / 360.0f)));
    CHECK(light.hasTime);
    CHECK(light.time == doctest::Approx(2.5f));
    CHECK(light.hasLightGroup);
    CHECK(light.lightGroup == "torches");
    REQUIRE(light.hasEffectiveColor);
    checkColorApprox(light.effectiveColor, {100.0f, 64.0f, 32.0f});
    REQUIRE(light.hasEffectiveObjectLightColor);
    checkColorApprox(light.effectiveObjectLightColor, {112.5f, 72.0f, 36.0f});
    REQUIRE(light.effectiveAttCoefs.size() == 3);
    CHECK(light.effectiveAttCoefs[0] == doctest::Approx(1.0f));
    CHECK(light.effectiveAttCoefs[1] == doctest::Approx(2.0f));
    CHECK(light.effectiveAttCoefs[2] == doctest::Approx(19.0f / (128.0f * 128.0f)));
    CHECK(light.effectiveLightObjects);
    CHECK(!light.effectiveFastLightObjects);
    CHECK(light.effectiveCastShadows);
    CHECK(light.staticObjectLightEligible);
    CHECK(!light.fastObjectLightingSource);
    CHECK(light.sourceProperties.size() == lightObject().properties.size());
    REQUIRE(light.unsupportedProperties.size() == 1);
    CHECK(light.unsupportedProperties[0] == "MysteryProperty");
    REQUIRE(layer.diagnostics.size() == 1);
    CHECK(layer.diagnostics[0].message == "unsupported_light_property");
}

TEST_CASE("MM9 light layer applies class defaults and effective colors")
{
    OpenYAMM::Game::Mm9LightSourceObject dirLight = lightObject();
    dirLight.sourceObjectIndex = 1;
    dirLight.sourceClass = "DirLight";
    dirLight.properties.clear();
    dirLight.properties.push_back(OpenYAMM::Game::mm9LightStringProperty("Name", "Sun"));
    dirLight.properties.push_back(OpenYAMM::Game::mm9LightVec3Property("Pos", vec3(1.0f, 2.0f, 3.0f)));
    dirLight.properties.push_back(OpenYAMM::Game::mm9LightVec3Property("InnerColor", vec3(16.0f, 32.0f, 64.0f)));

    OpenYAMM::Game::Mm9LightSourceObject defaultLight = lightObject();
    defaultLight.sourceObjectIndex = 3;
    defaultLight.sourceClass = "Light";
    defaultLight.properties.clear();
    defaultLight.properties.push_back(OpenYAMM::Game::mm9LightStringProperty("Name", "DefaultLight"));
    defaultLight.properties.push_back(OpenYAMM::Game::mm9LightVec3Property("Pos", vec3(7.0f, 8.0f, 9.0f)));
    defaultLight.properties.push_back(OpenYAMM::Game::mm9LightNumberProperty("LightRadius", 96.0f));
    defaultLight.properties.push_back(OpenYAMM::Game::mm9LightVec3Property("LightColor", vec3(48.0f, 64.0f, 80.0f)));

    OpenYAMM::Game::Mm9LightSourceObject objectLight = lightObject();
    objectLight.sourceObjectIndex = 2;
    objectLight.sourceClass = "ObjectLight";
    objectLight.properties.clear();
    objectLight.properties.push_back(OpenYAMM::Game::mm9LightStringProperty("Name", "ObjectLight"));
    objectLight.properties.push_back(OpenYAMM::Game::mm9LightVec3Property("Pos", vec3(4.0f, 5.0f, 6.0f)));
    objectLight.properties.push_back(OpenYAMM::Game::mm9LightNumberProperty("LightRadius", 64.0f));
    objectLight.properties.push_back(OpenYAMM::Game::mm9LightVec3Property("LightColor", vec3(100.0f, 64.0f, 32.0f)));

    OpenYAMM::Game::Mm9LightSourceObject nonLight = lightObject();
    nonLight.sourceClass = "Monster";

    OpenYAMM::Game::Mm9DatWorldInfo worldInfo = {};
    const OpenYAMM::Game::Mm9LightLayer layer =
        OpenYAMM::Game::buildMm9LightLayer(worldInfo, {dirLight, defaultLight, objectLight, nonLight});

    REQUIRE(layer.lights.size() == 3);
    CHECK(layer.lights[0].sourceClass == "DirLight");
    CHECK(layer.lights[1].sourceClass == "Light");
    CHECK(layer.lights[2].sourceClass == "ObjectLight");

    const OpenYAMM::Game::Mm9LightObject &sun = layer.lights[0];
    CHECK(sun.lightRadius == doctest::Approx(300.0f));
    CHECK(!sun.hasLightRadius);
    CHECK(sun.lightObjects);
    CHECK(sun.fastLightObjects);
    CHECK(sun.castShadows);
    CHECK(sun.clipLight);
    CHECK(sun.size == doctest::Approx(5.0f));
    CHECK(sun.fov == doctest::Approx(90.0f));
    CHECK(sun.hasEffectiveFovCos);
    CHECK(sun.attenuation == "Quartic");
    REQUIRE(sun.hasEffectiveColor);
    checkColorApprox(sun.effectiveColor, {16.0f, 32.0f, 64.0f});
    CHECK(!sun.staticObjectLightEligible);
    CHECK(sun.fastObjectLightingSource);

    const OpenYAMM::Game::Mm9LightObject &plain = layer.lights[1];
    CHECK(plain.lightObjects);
    CHECK(plain.fastLightObjects);
    CHECK(plain.castShadows);
    CHECK(plain.clipLight);
    CHECK(!plain.staticObjectLightEligible);
    CHECK(plain.fastObjectLightingSource);

    const OpenYAMM::Game::Mm9LightObject &object = layer.lights[2];
    REQUIRE(object.hasEffectiveColor);
    checkColorApprox(object.effectiveColor, {100.0f, 64.0f, 32.0f});
    CHECK(!object.hasObjectBrightScale);
    CHECK(!object.lightObjects);
    CHECK(object.fastLightObjects);
    CHECK(object.castShadows);
    CHECK(!object.clipLight);
    CHECK(!object.staticObjectLightEligible);
    CHECK(layer.diagnostics.empty());
}

TEST_CASE("MM9 light layer diagnoses invalid attenuation strings")
{
    OpenYAMM::Game::Mm9LightSourceObject object = lightObject();
    for (OpenYAMM::Game::Mm9LightSourceProperty &property : object.properties)
    {
        if (property.name == "Attenuation")
        {
            property = OpenYAMM::Game::mm9LightStringProperty("Attenuation", "UnknownCurve");
        }
    }

    OpenYAMM::Game::Mm9DatWorldInfo worldInfo = {};
    const OpenYAMM::Game::Mm9LightLayer layer = OpenYAMM::Game::buildMm9LightLayer(worldInfo, {object});

    REQUIRE(layer.lights.size() == 1);
    CHECK(layer.lights[0].hasAttenuation);
    CHECK(!layer.lights[0].validAttenuation);
    CHECK(layer.lights[0].attenuation == "UnknownCurve");
    bool foundInvalidAttenuation = false;
    for (const OpenYAMM::Game::Mm9LightLayerDiagnostic &diagnostic : layer.diagnostics)
    {
        foundInvalidAttenuation =
            foundInvalidAttenuation || diagnostic.message == "invalid_attenuation_property";
    }
    CHECK(foundInvalidAttenuation);
}

TEST_CASE("MM9 light layer converts eligible static lights to renderer-neutral render lights")
{
    OpenYAMM::Game::Mm9DatWorldInfo worldInfo = {};
    const OpenYAMM::Game::Mm9LightLayer layer =
        OpenYAMM::Game::buildMm9LightLayer(worldInfo, {lightObjectWithFlags(true, false)});

    REQUIRE(layer.lights.size() == 1);
    const std::optional<OpenYAMM::Game::RenderLight> renderLight =
        OpenYAMM::Game::convertMm9LightObjectToRenderLight(layer.lights[0], 2.0f);
    REQUIRE(renderLight.has_value());
    CHECK(renderLight->position.x == doctest::Approx(20.0f));
    CHECK(renderLight->position.y == doctest::Approx(60.0f));
    CHECK(renderLight->position.z == doctest::Approx(40.0f));
    CHECK(renderLight->radius == doctest::Approx(256.0f));
    CHECK(renderLight->colorAbgr == 0xff244871u);
    CHECK(renderLight->intensity == doctest::Approx(1.0f));
    CHECK(renderLight->stableId == 42);
    CHECK(!renderLight->dynamic);
    CHECK(renderLight->important);

    const std::vector<OpenYAMM::Game::RenderLight> renderLights =
        OpenYAMM::Game::buildMm9StaticRenderLights(layer, 2.0f);
    REQUIRE(renderLights.size() == 1);
    CHECK(renderLights[0].stableId == renderLight->stableId);
}

TEST_CASE("MM9 light layer rejects non-static object lighting sources during render-light conversion")
{
    OpenYAMM::Game::Mm9DatWorldInfo worldInfo = {};
    const OpenYAMM::Game::Mm9LightLayer lightObjectsOffLayer =
        OpenYAMM::Game::buildMm9LightLayer(worldInfo, {lightObjectWithFlags(false, false)});
    const OpenYAMM::Game::Mm9LightLayer fastLightObjectsLayer =
        OpenYAMM::Game::buildMm9LightLayer(worldInfo, {lightObjectWithFlags(true, true)});

    REQUIRE(lightObjectsOffLayer.lights.size() == 1);
    REQUIRE(fastLightObjectsLayer.lights.size() == 1);
    CHECK(!lightObjectsOffLayer.lights[0].staticObjectLightEligible);
    CHECK(fastLightObjectsLayer.lights[0].fastObjectLightingSource);
    CHECK(!OpenYAMM::Game::convertMm9LightObjectToRenderLight(lightObjectsOffLayer.lights[0]).has_value());
    CHECK(!OpenYAMM::Game::convertMm9LightObjectToRenderLight(fastLightObjectsLayer.lights[0]).has_value());
    CHECK(OpenYAMM::Game::buildMm9StaticRenderLights(lightObjectsOffLayer).empty());
    CHECK(OpenYAMM::Game::buildMm9StaticRenderLights(fastLightObjectsLayer).empty());
}
