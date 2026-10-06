#include "doctest/doctest.h"

#include "game/app/GameSettings.h"
#include "game/render/WaterMath.h"
#include "game/fx/WaterRippleRuntime.h"
#include "game/render/WaterAppearance.h"
#include "game/render/WaterGeometry.h"
#include "game/indoor/IndoorPortalVisibility.h"
#include "game/render/WaterCoverage.h"
#include "game/render/WaterReflectionUpdate.h"
#include "game/render/WaterBillboardReflection.h"
#include "game/ui/MenuSettingsModel.h"

#include <algorithm>
#include <chrono>
#include <filesystem>

using namespace OpenYAMM::Game;

TEST_CASE("indoor water visibility respects both sectors and keeps unassigned geometry visible")
{
    const std::array<uint8_t, 4> sectors = {0, 1, 0, 0};
    CHECK(indoorGeometrySectorsVisible(sectors, 1, -1));
    CHECK(indoorGeometrySectorsVisible(sectors, 2, 1));
    CHECK_FALSE(indoorGeometrySectorsVisible(sectors, 2, -1));
    CHECK_FALSE(indoorGeometrySectorsVisible(sectors, 2, 3));
    CHECK(indoorGeometrySectorsVisible(sectors, -1, -1));
    CHECK(indoorGeometrySectorsVisible({}, 2, 3));
}

TEST_CASE("indoor water classification excludes lava and sky even when marked fluid")
{
    const uint32_t fluid = faceAttributeBit(FaceAttribute::Fluid);
    CHECK(isWaterSurface(fluid, SurfaceMaterialSemantic::GenericAnimated));
    CHECK(isWaterSurface(0, SurfaceMaterialSemantic::Water));
    CHECK_FALSE(isWaterSurface(0, SurfaceMaterialSemantic::GenericAnimated));
    CHECK_FALSE(isWaterSurface(fluid, SurfaceMaterialSemantic::Lava));
    CHECK_FALSE(isWaterSurface(fluid | faceAttributeBit(FaceAttribute::Lava), SurfaceMaterialSemantic::Water));
    CHECK_FALSE(isWaterSurface(fluid | faceAttributeBit(FaceAttribute::IndoorSky),
        SurfaceMaterialSemantic::Water));
}

TEST_CASE("indoor water separates pool elevations and keeps waterfalls out of planar reflections")
{
    const auto vertex = [](float x, float y, float z)
    { return WaterVertex{x, y, z, 0.0f, 0.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0xff4a4429u}; };
    const std::vector<WaterVertex> triangles = {
        vertex(0, 0, 10), vertex(100, 0, 10), vertex(0, 100, 10),
        vertex(100, 0, 10), vertex(100, 100, 10), vertex(0, 100, 10),
        vertex(0, 0, 20), vertex(100, 0, 20), vertex(0, 100, 20),
        vertex(0, 0, 10), vertex(100, 0, 10), vertex(0, 0, 20),
        vertex(0, 0, 10), vertex(0, 0, 10), vertex(0, 0, 10)
    };
    const std::vector<WaterSurfaceGeometry> geometry = buildWaterFaceGeometry(triangles, 12, -1);
    REQUIRE(geometry.size() == 3);
    CHECK(geometry[0].planar);
    CHECK(geometry[0].height == 10);
    CHECK(geometry[0].vertices.size() == 6);
    CHECK(geometry[1].planar);
    CHECK(geometry[1].height == 20);
    CHECK_FALSE(geometry[2].planar);
    CHECK(geometry[0].patches.front()[1].x == 100);
    CHECK(geometry[0].patches.front()[1].y == 100);
    for (const WaterSurfaceGeometry &surface : geometry)
    {
        CHECK(surface.sectorId == 12);
        CHECK(surface.backSectorId == -1);
        CHECK(surface.vertices.front().colorAbgr == 0xff4a4429u);
    }
    const std::array<WaterVertex, 3> underside = {vertex(0, 0, 10), vertex(0, 100, 10), vertex(100, 0, 10)};
    const std::vector<WaterSurfaceGeometry> below = buildWaterFaceGeometry(underside, -1, -1);
    REQUIRE(below.size() == 1);
    CHECK_FALSE(below.front().planar);
    CHECK(below.front().vertices.front().normalZ == -1.0f);
    CHECK(buildWaterFaceGeometry({}, 1, -1).empty());
}

TEST_CASE("water face directional flow follows native UV orientation on horizontal and vertical faces")
{
    const std::array<std::array<float, 2>, 3> uvs = {{{0, 0}, {1, 0}, {0, 1}}};
    const std::array<bx::Vec3, 3> flat = {bx::Vec3{0, 0, 0}, bx::Vec3{128, 0, 0}, bx::Vec3{0, -128, 0}};
    const std::array<bx::Vec3, 3> wall = {bx::Vec3{0, 0, 0}, bx::Vec3{128, 0, 0}, bx::Vec3{0, 0, -128}};
    const std::array<float, 2> flatFlow = waterFaceFlow(flat, uvs, 0.0f, -0.5f);
    const std::array<float, 2> wallFlow = waterFaceFlow(wall, uvs, 0.0f, -0.5f);
    CHECK(flatFlow[0] == 0);
    CHECK(flatFlow[1] == doctest::Approx(-64.0 / 768.0));
    CHECK(wallFlow[0] == 0);
    CHECK(wallFlow[1] == doctest::Approx(64.0 / 768.0));
    const std::array<float, 2> reverse = waterFaceFlow(wall, uvs, 0.0f, 0.5f);
    CHECK(reverse[1] == -wallFlow[1]);
    const std::array<bx::Vec3, 3> collapsed = {bx::Vec3{0, 0, 0}, bx::Vec3{0, 0, 0}, bx::Vec3{0, 0, 0}};
    CHECK(waterFaceFlow(collapsed, uvs, 1, 1) == std::array<float, 2>{0, 0});
}

TEST_CASE("sprite fountain water stays inside authored streams and follows billboard mirroring")
{
    const std::string yaml = R"(textures:
  fountain1:
    - [[0.2, 0.3, 0.4], [0.25, 0.35, 0.9]]
)";
    const auto materials = parseSpriteWaterStrips(yaml);
    const BillboardQuad quad = billboardQuad({10, 20, 30}, {1, 0, 0}, {0, 0, 1}, 100, 200);
    const auto &strips = materials.at("fountain1");
    REQUIRE(strips.size() == 1);
    const std::vector<WaterVertex> ordinary = buildSpriteWaterGeometry(quad, strips, false);
    const std::vector<WaterVertex> mirrored = buildSpriteWaterGeometry(quad, strips, true);
    REQUIRE(ordinary.size() == 6);
    REQUIRE(mirrored.size() == ordinary.size());
    for (size_t index = 0; index < ordinary.size(); ++index)
    {
        CHECK(ordinary[index].x + mirrored[index].x == doctest::Approx(quad.center.x * 2));
        CHECK(ordinary[index].z >= -50);
        CHECK(ordinary[index].z <= 50);
        CHECK(ordinary[index].layer == -2);
        CHECK(ordinary[index].v == mirrored[index].v);
    }
    CHECK_FALSE(materials.contains("stone"));
    std::string invalid = yaml;
    invalid.replace(invalid.find("0.9"), 3, "1.9");
    CHECK_THROWS_AS(parseSpriteWaterStrips(invalid), std::invalid_argument);
    invalid = yaml;
    invalid.replace(invalid.find("0.9"), 3, "0.1");
    CHECK_THROWS_AS(parseSpriteWaterStrips(invalid), std::invalid_argument);
    invalid = yaml;
    invalid.replace(invalid.find("0.9"), 3, "bad");
    CHECK_THROWS_AS(parseSpriteWaterStrips(invalid), std::invalid_argument);
}

TEST_CASE("water body tint keeps regional colour without the source wave pattern or resolution")
{
    const std::vector<uint8_t> black = {0, 0, 0, 255};
    const std::vector<uint8_t> white = {255, 255, 255, 255};
    const std::vector<uint8_t> blue = {255, 0, 0, 255};
    const std::vector<uint8_t> green = {0, 255, 0, 255};
    CHECK(waterBodyColorFromBgra(black) == 0xff322b11u);
    CHECK(waterBodyColorFromBgra(white) == 0xff635c42u);
    CHECK(waterBodyColorFromBgra(blue) == 0xff632b11u);
    CHECK(waterBodyColorFromBgra(green) == 0xff325c11u);
    std::vector<uint8_t> alternating = {0, 0, 0, 255, 255, 255, 255, 255};
    CHECK(waterBodyColorFromBgra(alternating) == 0xff4a4429u);
    for (int repeat = 0; repeat < 12; ++repeat)
    {
        alternating.insert(alternating.end(), {255, 255, 255, 255, 0, 0, 0, 255});
        CHECK(waterBodyColorFromBgra(alternating) == 0xff4a4429u);
    }
    CHECK_THROWS_AS(waterBodyColorFromBgra({}), std::invalid_argument);
    CHECK_THROWS_AS(waterBodyColorFromBgra(std::vector<uint8_t>{0, 0, 0}), std::invalid_argument);
}

TEST_CASE("water reflection reuse refreshes animation and immediately invalidates camera, content and quality changes")
{
    WaterReflectionUpdate state;
    float matrix[16];
    bx::mtxIdentity(matrix);
    const auto prepare = [&](float seconds, float height = 0.0f, uint16_t size = 512,
        uint64_t revision = 7, bool buildings = true)
    {
        return state.prepare(matrix, height, size, seconds, revision, buildings);
    };
    CHECK(prepare(10.0f));
    for (int frame = 1; frame < 100; ++frame)
    {
        CHECK_FALSE(prepare(10.0f + frame * 0.0003f));
    }
    CHECK(prepare(10.034f));
    CHECK_FALSE(prepare(10.034f)); // Paused time retains the rendered texture.
    matrix[12] = 1.0f;
    CHECK(prepare(10.034f)); // Translation while paused.
    matrix[0] = 0.5f;
    CHECK(prepare(10.034f)); // Rotation/projection while paused.
    CHECK(prepare(10.034f, 180.0f));
    CHECK(prepare(10.034f, 180.0f, 2048));
    CHECK(prepare(10.034f, 180.0f, 2048, 8));
    CHECK(prepare(10.034f, 180.0f, 2048, 8, false));
    CHECK_FALSE(prepare(10.034f, 180.0f, 2048, 8, false));
    CHECK(prepare(0.0f, 180.0f, 2048, 8, false)); // Time reset/load.
    state = {};
    CHECK(prepare(0.0f, 180.0f, 2048, 8, false)); // GPU resources recreated at the same pose.
}

TEST_CASE("water covered rotations still refresh animation, content and capture quality")
{
    WaterReflectionUpdate state;
    float matrix[16];
    bx::mtxIdentity(matrix);
    CHECK(state.prepare(matrix, 100.0f, 576, 1.0f, 7, true, true));
    matrix[0] = 0.99f;
    CHECK_FALSE(state.prepare(matrix, 100.0f, 576, 1.001f, 7, true, true));
    CHECK_FALSE(state.prepare(matrix, 100.0f, 576, 1.001f, 7, true, true)); // Paused rotation.
    CHECK(state.prepare(matrix, 100.0f, 576, 1.001f, 8, true, true)); // Door/light changes.
    CHECK(state.prepare(matrix, 100.0f, 1152, 1.001f, 8, true, true));
    CHECK(state.prepare(matrix, 110.0f, 1152, 1.001f, 8, true, true));
    CHECK(state.prepare(matrix, 110.0f, 1152, 1.001f, 8, false, true));
    CHECK(state.prepare(matrix, 110.0f, 1152, 1.04f, 8, false, true));
    CHECK(state.prepare(matrix, 110.0f, 1152, 0.0f, 8, false, true)); // Reload/time reset.
    matrix[0] = 0.97f;
    CHECK_FALSE(state.prepare(matrix, 110.0f, 1152, 0.0f, 8, false, true));
    CHECK(state.prepare(matrix, 110.0f, 1152, 0.0f, 8, false)); // Beyond the capture margin.
}

TEST_CASE("water billboard setting refreshes cached reflections even while paused")
{
    WaterReflectionUpdate state;
    float matrix[16];
    bx::mtxIdentity(matrix);
    CHECK(state.prepare(matrix, 0.0f, 512, 1.0f, 1, true, true, false));
    CHECK_FALSE(state.prepare(matrix, 0.0f, 512, 1.0f, 1, true, true, false));
    CHECK(state.prepare(matrix, 0.0f, 512, 1.0f, 1, true, true, true));
    CHECK_FALSE(state.prepare(matrix, 0.0f, 512, 1.0f, 1, true, true, true));
    CHECK(state.prepare(matrix, 0.0f, 512, 1.0f, 1, true, true, false));
}

TEST_CASE("water billboard budget keeps nearby objects and fades before the distance cutoff")
{
    CHECK(waterBillboardFade(0.0f) == 1.0f);
    CHECK(waterBillboardFade(WaterBillboardFadeDistance * WaterBillboardFadeDistance) == 1.0f);
    CHECK(waterBillboardFade(WaterBillboardDistance * WaterBillboardDistance) == 0.0f);
    CHECK(waterBillboardFade(WaterBillboardDistance * WaterBillboardDistance + 1.0f) == 0.0f);
    const float middle = (WaterBillboardDistance * WaterBillboardDistance
        + WaterBillboardFadeDistance * WaterBillboardFadeDistance) * 0.5f;
    CHECK(waterBillboardFade(middle) == doctest::Approx(0.5f));
    CHECK(waterBillboardColor(0x80402010u, middle) == 0x40402010u);
    CHECK(waterBillboardColor(0xff402010u, 0.0f) == 0xff402010u);
    struct Item
    {
        float distanceSquared;
    };
    std::vector<Item> items;
    for (size_t index = MaxWaterBillboards + 16; index > 0; --index)
    {
        items.push_back({float(index)});
    }
    limitWaterBillboards(items, MaxWaterBillboards);
    REQUIRE(items.size() == MaxWaterBillboards);
    for (const Item &item : items)
    {
        CHECK(item.distanceSquared <= float(MaxWaterBillboards));
    }
    limitWaterBillboards(items, 0);
    CHECK(items.empty());
}

TEST_CASE("water billboards use reflection visibility without inverting their world anchor")
{
    const bx::Vec3 eye = {0.0f, -200.0f, 100.0f};
    float view[16];
    float reflected[16];
    float recovered[16];
    bx::mtxLookAt(view, eye, {0.0f, 0.0f, -100.0f}, {0.0f, 0.0f, 1.0f}, bx::Handedness::Right);
    waterReflectionView(reflected, view, 0.0f);
    waterReflectionView(recovered, reflected, 0.0f);
    for (size_t index = 0; index < 16; ++index)
    {
        CHECK(recovered[index] == doctest::Approx(view[index]));
    }
    const bx::Vec3 right = {recovered[0], recovered[4], recovered[8]};
    const bx::Vec3 up = {recovered[1], recovered[5], recovered[9]};
    CHECK(up.z > 0.0f);
    const BillboardQuad above = billboardQuad({0.0f, 0.0f, 160.0f}, right, up, 40.0f, 40.0f);
    const BillboardQuad below = billboardQuad({0.0f, 0.0f, -160.0f}, right, up, 40.0f, 40.0f);
    for (bool homogeneousDepth : {false, true})
    {
        float projection[16];
        bx::mtxProj(projection, 60.0f, 1.0f, 1.0f, 10000.0f, homogeneousDepth, bx::Handedness::Right);
        const ViewFrustum mainFrustum(view, projection, homogeneousDepth);
        const ViewFrustum reflectionFrustum(reflected, projection, homogeneousDepth);
        CHECK_FALSE(mainFrustum.intersectsQuad(above.center, above.right, above.up));
        CHECK(waterBillboardVisible(above, reflectionFrustum, 0.0f));
        CHECK_FALSE(waterBillboardVisible(below, reflectionFrustum, 0.0f));
    }
}

TEST_CASE("water guarded captures cover nearby rotations and reject uncaptured view edges")
{
    constexpr uint16_t captureSize = uint16_t(512 * IndoorWaterReflectionGuardBand);
    for (bool homogeneousDepth : {false, true})
    {
        for (float aspect : {4.0f / 3.0f, 16.0f / 9.0f})
        {
            float projection[16];
            float captureProjection[16];
            bx::mtxProj(projection, 60.0f, aspect, 0.1f, 50000.0f,
                homogeneousDepth, bx::Handedness::Right);
            waterReflectionCaptureProjection(captureProjection, projection, IndoorWaterReflectionGuardBand,
                homogeneousDepth);
            CHECK(captureProjection[0] * captureSize == doctest::Approx(projection[0] * 512));
            CHECK(captureProjection[5] * captureSize == doctest::Approx(projection[5] * 512));
            for (float yaw : {0.0f, 1.0f, 3.0f})
            {
                for (float pitch : {-1.4f, -0.28f, 0.0f, 1.4f})
                {
                    const bx::Vec3 eye = {25000.0f, -21000.0f, 300.0f};
                    const auto reflectedView = [&](float angle, float elevation, float *pResult)
                    {
                        const bx::Vec3 forward = {std::cos(angle) * std::cos(elevation),
                            std::sin(angle) * std::cos(elevation), std::sin(elevation)};
                        float view[16];
                        bx::mtxLookAt(view, eye, bx::add(eye, forward), {0.0f, 0.0f, 1.0f}, bx::Handedness::Right);
                        waterReflectionView(pResult, view, 0.0f);
                    };
                    float capture[16];
                    float current[16];
                    reflectedView(yaw, pitch, capture);
                    for (float angle : {-0.01f, 0.0f, 0.01f})
                    {
                        INFO("depth=" << homogeneousDepth << " aspect=" << aspect << " yaw=" << yaw
                            << " pitch=" << pitch << " rotation=" << angle);
                        reflectedView(yaw + angle, pitch + angle, current);
                        CHECK(waterReflectionViewCovered(capture, captureProjection, current, projection,
                            captureSize, homogeneousDepth));
                    }
                    reflectedView(yaw + 0.3f, pitch, current);
                    CHECK_FALSE(waterReflectionViewCovered(capture, captureProjection, current, projection,
                        captureSize, homogeneousDepth));
                    reflectedView(yaw, pitch + 0.2f, current);
                    CHECK_FALSE(waterReflectionViewCovered(capture, captureProjection, current, projection,
                        captureSize, homogeneousDepth));
                    reflectedView(yaw + 3.14159265f, -pitch, current);
                    CHECK_FALSE(waterReflectionViewCovered(capture, captureProjection, current, projection,
                        captureSize, homogeneousDepth));
                }
            }
        }
    }
}

TEST_CASE("water guarded capture size respects hardware limits without reducing requested detail")
{
    CHECK(waterReflectionCaptureSize(128, 8192) == 144);
    CHECK(waterReflectionCaptureSize(512, 8192) == 576);
    CHECK(waterReflectionCaptureSize(2048, 8192) == 2304);
    CHECK(waterReflectionCaptureSize(2048, 2048) == 2048);
    CHECK(waterReflectionCaptureSize(1024, 1100) == 1100);
}

TEST_CASE("water shoreline coverage preserves opaque land, open water and partial shore alpha")
{
    const std::vector<uint8_t> overlay = {
        10, 20, 30, 255, 10, 20, 30, 0,
        10, 20, 30, 128, 10, 20, 30, 64
    };
    CHECK(waterCoverageFromOverlay(overlay, 2, 2, 2) == std::vector<uint8_t>{0, 255, 127, 191});
    CHECK(waterCoverageFromOverlay(overlay, 2, 2, 1) == std::vector<uint8_t>{143});
    CHECK(waterCoverageFromOverlay(overlay, 2, 2, 4) == std::vector<uint8_t>{
        0, 0, 255, 255, 0, 0, 255, 255, 127, 127, 191, 191, 127, 127, 191, 191});
    CHECK_THROWS_AS(waterCoverageFromOverlay(overlay, 0, 2), std::invalid_argument);
    CHECK_THROWS_AS(waterCoverageFromOverlay(overlay, 2, 2, 0), std::invalid_argument);
    CHECK_THROWS_AS(waterCoverageFromOverlay(overlay, 3, 2), std::invalid_argument);
}

TEST_CASE("menu water controls accept supported quality values and reject invalid edits")
{
    GameSettings settings = GameSettings::createDefault();
    CHECK(menuSettingValue(settings, "water_shader") == "true");
    REQUIRE(setMenuSettingValue(settings, "water_shader", "false"));
    CHECK_FALSE(settings.waterShader);
    REQUIRE(setMenuSettingValue(settings, "water_reflections", "false"));
    CHECK_FALSE(settings.waterReflections);
    CHECK(menuSettingValue(settings, "water_reflections") == "false");
    CHECK(menuSettingValue(settings, "water_sprite_reflections") == "false");
    REQUIRE(setMenuSettingValue(settings, "water_sprite_reflections", "true"));
    CHECK(settings.waterSpriteReflections);
    CHECK(menuSettingValue(settings, "water_sprite_reflections") == "true");
    CHECK_FALSE(setMenuSettingValue(settings, "water_sprite_reflections", "bad"));
    REQUIRE(setMenuSettingValue(settings, "water_reflection_size", "1024"));
    CHECK(menuSettingValue(settings, "water_reflection_size") == "1024");
    CHECK_FALSE(setMenuSettingValue(settings, "water_reflection_size", "1024bad"));
    CHECK_FALSE(setMenuSettingValue(settings, "water_reflection_size", "700"));
    CHECK_FALSE(setMenuSettingValue(settings, "water_reflection_size", "0"));
    CHECK_FALSE(setMenuSettingValue(settings, "water_shader", "bad"));
    CHECK(settings.waterReflectionSize == 1024);
}

TEST_CASE("water reflection preserves surface projection and mirrors geometry across the actual elevation")
{
    for (float height : {-180.0f, 0.0f, 512.0f})
    {
        const bx::Vec3 eye = {2300.0f, -4700.0f, height + 350.0f};
        const bx::Vec3 at = {1000.0f, -2000.0f, height};
        float view[16];
        float reflected[16];
        bx::mtxLookAt(view, eye, at, {0.0f, 0.0f, 1.0f}, bx::Handedness::Right);
        waterReflectionView(reflected, view, height);
        for (const bx::Vec3 &point : {bx::Vec3{1000.0f, -2000.0f, height},
            bx::Vec3{1300.0f, -1600.0f, height + 240.0f}, bx::Vec3{-100.0f, 500.0f, height - 90.0f}})
        {
            // Independently transform the reflected world point through the ordinary camera.
            const bx::Vec3 expected = bx::mul(reflectWaterPoint(point, height), view);
            const bx::Vec3 actual = bx::mul(point, reflected);
            CHECK(actual.x == doctest::Approx(expected.x).epsilon(0.0001).scale(1.0));
            CHECK(actual.y == doctest::Approx(expected.y).epsilon(0.0001).scale(1.0));
            CHECK(actual.z == doctest::Approx(expected.z).epsilon(0.0001).scale(1.0));
            if (point.z == height)
            {
                const bx::Vec3 ordinary = bx::mul(point, view);
                CHECK(actual.x == doctest::Approx(ordinary.x).epsilon(0.0001).scale(1.0));
                CHECK(actual.y == doctest::Approx(ordinary.y).epsilon(0.0001).scale(1.0));
                CHECK(actual.z == doctest::Approx(ordinary.z).epsilon(0.0001).scale(1.0));
            }
        }
        const bx::Vec3 mirrorEye = reflectWaterPoint(eye, height);
        CHECK(mirrorEye.z == doctest::Approx(height - 350.0f));
        const bx::Vec3 cameraOrigin = bx::mul(mirrorEye, reflected);
        CHECK(cameraOrigin.x == doctest::Approx(0.0f).epsilon(0.001).scale(1.0));
        CHECK(cameraOrigin.y == doctest::Approx(0.0f).epsilon(0.001).scale(1.0));
        CHECK(cameraOrigin.z == doctest::Approx(0.0f).epsilon(0.001).scale(1.0));
    }
}

TEST_CASE("water reflection scissor covers visible water and distorted samples across cameras and depth conventions")
{
    constexpr uint16_t size = 512;
    size_t samples = 0;
    for (bool homogeneousDepth : {false, true})
    {
        for (float height : {-180.0f, 512.0f})
        {
            for (float pitch : {-1.5f, -0.5f, 0.0f, 0.5f, 1.5f})
            {
                for (float yaw : {0.0f, 1.0f, 3.0f})
                {
                    const bx::Vec3 eye = {25000.0f, -21000.0f, height + 300.0f};
                    const bx::Vec3 forward = {std::cos(yaw) * std::cos(pitch),
                        std::sin(yaw) * std::cos(pitch), std::sin(pitch)};
                    float view[16];
                    float projection[16];
                    float reflected[16];
                    float viewProjection[16];
                    bx::mtxLookAt(view, eye, bx::add(eye, forward), {0.0f, 0.0f, 1.0f}, bx::Handedness::Right);
                    bx::mtxProj(projection, 60.0f, 16.0f / 9.0f, 16.0f, 32768.0f,
                        homogeneousDepth, bx::Handedness::Right);
                    waterReflectionView(reflected, view, height);
                    bx::mtxMul(viewProjection, reflected, projection);
                    const WaterReflectionScissor scissor =
                        waterReflectionScissor(viewProjection, reflectWaterPoint(eye, height), size);
                    CHECK(scissor.x + scissor.width <= size);
                    CHECK(scissor.y + scissor.height <= size);
                    if (pitch == 0.0f)
                    {
                        CHECK(scissor.y >= size / 2 - 12);
                        CHECK(scissor.y <= size / 2);
                        CHECK(scissor.height < size * 3 / 4);
                    }
                    if (pitch < -1.0f)
                    {
                        CHECK(scissor.width == size);
                        CHECK(scissor.height == size);
                    }
                    if (pitch > 1.0f)
                    {
                        CHECK(scissor.width == 0);
                        CHECK(scissor.height == 0);
                    }
                    for (int x = -16; x <= 16; ++x)
                    {
                        for (int y = -16; y <= 16; ++y)
                        {
                            const float point[] = {eye.x + x * 1000.0f, eye.y + y * 1000.0f, height, 1.0f};
                            float clip[4];
                            bx::vec4MulMtx(clip, point, viewProjection);
                            if (clip[3] < 16.0f || std::abs(clip[0]) > clip[3] || std::abs(clip[1]) > clip[3])
                            {
                                continue;
                            }
                            ++samples;
                            for (float distortion : {-WaterReflectionDistortion, WaterReflectionDistortion})
                            {
                                const float u = std::clamp(clip[0] / clip[3] * 0.5f + 0.5f + distortion, 0.0f, 1.0f);
                                const float v = std::clamp(0.5f - clip[1] / clip[3] * 0.5f + distortion, 0.0f, 1.0f);
                                CHECK(u * size >= scissor.x);
                                CHECK(u * size <= scissor.x + scissor.width);
                                CHECK(v * size >= scissor.y);
                                CHECK(v * size <= scissor.y + scissor.height);
                            }
                        }
                    }
                }
            }
        }
    }
    CHECK(samples > 1000);
}

TEST_CASE("sunlight shadows precede water reflections and world rendering without duplicate views")
{
    for (bool grading : {false, true})
    {
        const std::array<uint16_t, WorldGradingView + 1> order = worldRenderViewOrder(grading);
        const auto position = [&](uint16_t view) { return std::find(order.begin(), order.end(), view); };
        CHECK(position(0) < position(1));
        CHECK(position(1) < position(2));
        for (uint16_t view = FirstSunShadowView; view < FirstSunShadowView + SunShadowViews; ++view)
        {
            CHECK(position(view) < position(FirstWaterReflectionView));
        }
        for (uint16_t view = FirstWaterReflectionView;
            view < FirstWaterReflectionView + MaxWaterReflections * 2; ++view)
        {
            CHECK(position(view) < position(0));
        }
        if (grading)
        {
            CHECK(position(1) < position(WorldGradingView));
            CHECK(position(WorldGradingView) < position(2));
        }
        std::array<uint16_t, WorldGradingView + 1> sorted = order;
        std::sort(sorted.begin(), sorted.end());
        for (uint16_t view = 0; view <= WorldGradingView; ++view)
        {
            CHECK(sorted[view] == view);
        }
    }
}

TEST_CASE("water quality settings survive save load and clamp reflection allocation size")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path()
        / ("openyamm-water-settings-" + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())
            + ".ini");
    struct Cleanup
    {
        std::filesystem::path path;
        ~Cleanup() { std::filesystem::remove(path); }
    } cleanup{path};
    GameSettings settings = GameSettings::createDefault();
    settings.waterShader = false;
    settings.waterReflections = false;
    settings.waterSpriteReflections = true;
    settings.waterMovementRipples = false;
    settings.waterReflectionSize = 1024;
    std::string error;
    REQUIRE(saveGameSettings(path, settings, error));
    const std::optional<GameSettings> loaded = loadGameSettings(path, error);
    REQUIRE_MESSAGE(loaded.has_value(), error);
    CHECK_FALSE(loaded->waterShader);
    CHECK_FALSE(loaded->waterReflections);
    CHECK(loaded->waterSpriteReflections);
    CHECK_FALSE(loaded->waterMovementRipples);
    CHECK(loaded->waterReflectionSize == 1024);
    settings.waterReflectionSize = 65535;
    REQUIRE(saveGameSettings(path, settings, error));
    const std::optional<GameSettings> bounded = loadGameSettings(path, error);
    REQUIRE(bounded.has_value());
    CHECK(bounded->waterReflectionSize == 2048);
}

TEST_CASE("water movement ripple setting is enabled by default and rejects invalid toggle values")
{
    GameSettings settings = GameSettings::createDefault();
    CHECK(settings.waterMovementRipples);
    CHECK(menuSettingValue(settings, "water_movement_ripples") == "true");
    REQUIRE(setMenuSettingValue(settings, "water_movement_ripples", "false"));
    CHECK_FALSE(settings.waterMovementRipples);
    CHECK_FALSE(setMenuSettingValue(settings, "water_movement_ripples", "bad"));
    CHECK_FALSE(settings.waterMovementRipples);
}

TEST_CASE("water movement ripples require travel on water and obey a minimum emission interval")
{
    WaterRippleRuntime state;
    state.setEnabled(true);
    state.observe(0, {0, 0, 5}, true, 37);
    state.advance(0.1f, false);
    state.observe(0, {80, 0, 5}, true, 37);
    CHECK(state.ripples().empty());
    state.advance(0.2f, false);
    state.observe(0, {100, 0, 5}, true, 37);
    REQUIRE(state.ripples().size() == 1);
    CHECK(state.ripples()[0].position.x == 100);
    for (int step = 0; step < 10; ++step)
    {
        state.advance(0.05f, false);
        state.observe(0, {100, 0, 5}, true, 37);
    }
    CHECK(state.ripples().size() == 1);
    state.observe(0, {200, 0, 5}, false, 37); // Land, bridge or airborne.
    state.observe(0, {300, 0, 5}, false, 37);
    CHECK(state.ripples().size() == 1);
    state.observe(0, {400, 0, 5}, true, 37); // Re-entry establishes a fresh baseline.
    CHECK(state.ripples().size() == 1);
}

TEST_CASE("water movement ripples ignore teleport and height discontinuities")
{
    WaterRippleRuntime state;
    state.setEnabled(true);
    state.observe(1, {0, 0, 5}, true, 32);
    state.advance(0.3f, false);
    state.observe(1, {1000, 0, 5}, true, 32);
    CHECK(state.ripples().empty());
    state.advance(0.3f, false);
    state.observe(1, {1100, 0, 50}, true, 32);
    CHECK(state.ripples().empty());
    state.advance(0.3f, false);
    state.observe(1, {1200, 0, 50}, true, 32);
    CHECK(state.ripples().size() == 1);
}

TEST_CASE("water movement ripple storage and per surface shading stay bounded in crowds")
{
    WaterRippleRuntime state;
    CHECK(sizeof(state) < 8192);
    state.setEnabled(true);
    for (uint32_t source = 0; source < MaxWaterRipples; ++source)
    {
        state.observe(source, {float(source * 100), 0, 5}, true, 32);
    }
    state.advance(0.3f, false);
    for (uint32_t source = 0; source < MaxWaterRipples; ++source)
    {
        state.observe(source, {float(source * 100 + 80), 0, 5}, true, 32);
    }
    REQUIRE(state.ripples().size() == MaxWaterRipples);
    state.advance(0.3f, false);
    for (uint32_t source = 0; source < MaxWaterRipples; ++source)
    {
        state.observe(source, {float(source * 100 + 160), 0, 5}, true, 32);
    }
    CHECK(state.ripples().size() == MaxWaterRipples);
    const std::array<std::array<bx::Vec3, 2>, 1> patches = {{{bx::Vec3{-10, -10, 5}, bx::Vec3{10000, 10, 5}}}};
    const WaterRippleDrawSet draw = state.select({160, 0, 200}, 5, patches);
    CHECK(draw.count == MaxDrawWaterRipples);
    for (const std::array<float, 4> &ring : draw.rings)
    {
        CHECK(ring[0] >= 160);
        CHECK(ring[0] <= 460);
    }
}

TEST_CASE("water movement ripple storage caps each emitter without replacing another creature trail")
{
    WaterRippleRuntime state;
    state.setEnabled(true);
    state.observe(0, {0, 0, 5}, true, 37);
    state.observe(1, {500, 0, 5}, true, 32);
    state.advance(0.25f, false);
    state.observe(1, {580, 0, 5}, true, 32);
    for (uint32_t step = 1; step <= 5; ++step)
    {
        state.advance(0.25f, false);
        state.observe(0, {float(step * 80), 0, 5}, true, 37);
    }
    CHECK(std::count_if(state.ripples().begin(), state.ripples().end(),
        [](const WaterRipple &ripple) { return ripple.sourceId == 0; }) == MaxWaterRipplesPerEmitter);
    CHECK(std::count_if(state.ripples().begin(), state.ripples().end(),
        [](const WaterRipple &ripple) { return ripple.sourceId == 1 && ripple.position.x == 580; }) == 1);
    CHECK(std::none_of(state.ripples().begin(), state.ripples().end(),
        [](const WaterRipple &ripple) { return ripple.sourceId == 0 && ripple.position.x == 80; }));
}

TEST_CASE("water movement ripple selection shares the draw budget between nearby creatures")
{
    WaterRippleRuntime state;
    state.setEnabled(true);
    state.observe(0, {0, 0, 5}, true, 37);
    for (uint32_t source = 1; source <= 3; ++source)
    {
        state.observe(source, {float(400 + source * 200), 0, 5}, true, 32);
    }
    state.advance(0.26f, false);
    for (uint32_t source = 1; source <= 3; ++source)
    {
        state.observe(source, {float(480 + source * 200), 0, 5}, true, 32);
    }
    for (uint32_t step = 1; step <= 4; ++step)
    {
        state.advance(0.26f, false);
        state.observe(0, {float(step * 80), 0, 5}, true, 37);
    }
    const std::array<std::array<bx::Vec3, 2>, 1> patches = {{{bx::Vec3{0, -10, 5}, bx::Vec3{1600, 10, 5}}}};
    const WaterRippleDrawSet draw = state.select({0, 0, 200}, 5, patches);
    REQUIRE(draw.count == MaxDrawWaterRipples);
    CHECK(std::count_if(draw.rings.begin(), draw.rings.end(),
        [](const std::array<float, 4> &ring) { return ring[0] <= 320; }) == 1);
    for (uint32_t source = 1; source <= 3; ++source)
    {
        CHECK(std::any_of(draw.rings.begin(), draw.rings.end(), [source](const std::array<float, 4> &ring)
        { return ring[0] == float(480 + source * 200); }));
    }
}

TEST_CASE("water movement ripple selection allows at most two rings per creature")
{
    WaterRippleRuntime state;
    state.setEnabled(true);
    state.observe(0, {0, 0, 5}, true, 37);
    state.observe(1, {500, 0, 5}, true, 32);
    for (uint32_t step = 1; step <= 4; ++step)
    {
        state.advance(0.26f, false);
        state.observe(0, {float(step * 80), 0, 5}, true, 37);
        state.observe(1, {float(500 + step * 80), 0, 5}, true, 32);
    }
    const std::array<std::array<bx::Vec3, 2>, 1> patches = {{{bx::Vec3{0, -10, 5}, bx::Vec3{1600, 10, 5}}}};
    const WaterRippleDrawSet draw = state.select({0, 0, 200}, 5, patches);
    REQUIRE(draw.count == MaxDrawWaterRipples);
    CHECK(std::count_if(draw.rings.begin(), draw.rings.end(),
        [](const std::array<float, 4> &ring) { return ring[0] < 500; }) == MaxDrawWaterRipplesPerEmitter);
    CHECK(std::count_if(draw.rings.begin(), draw.rings.end(),
        [](const std::array<float, 4> &ring) { return ring[0] > 500; }) == MaxDrawWaterRipplesPerEmitter);
    state.observe(1, {900, 0, 5}, false, 32);
    state.advance(1.4f, false);
    state.observe(0, {320, 0, 5}, true, 37);
    state.advance(0.26f, false);
    state.observe(0, {400, 0, 5}, true, 37);
    state.advance(0.26f, false);
    state.observe(0, {480, 0, 5}, true, 37);
    CHECK(state.select({0, 0, 200}, 5, patches).count == MaxDrawWaterRipplesPerEmitter);
}

TEST_CASE("water movement ripples filter different pools and distant or disjoint surfaces")
{
    WaterRippleRuntime state;
    state.setEnabled(true);
    state.observe(1, {0, 0, 5}, true, 32, 2);
    state.advance(0.3f, false);
    state.observe(1, {80, 0, 5}, true, 32, 2);
    const std::array<std::array<bx::Vec3, 2>, 1> patches = {{{bx::Vec3{0, -10, 5}, bx::Vec3{200, 10, 5}}}};
    CHECK(state.select({0, 0, 200}, 5, patches, 2).count == 1);
    CHECK(state.select({0, 0, 200}, 5, patches, 3, 2).count == 1);
    CHECK(state.select({0, 0, 200}, 5, patches, 3).count == 0);
    CHECK(state.select({0, 0, 200}, 50, patches, 2).count == 0);
    CHECK(state.select({5000, 0, 200}, 5, patches, 2).count == 0);
    CHECK(state.select({0, 0, 200}, 5, {}).count == 0);
    const std::array<std::array<bx::Vec3, 2>, 1> remote = {{{bx::Vec3{500, 0, 5}, bx::Vec3{700, 10, 5}}}};
    CHECK(state.select({0, 0, 200}, 5, remote).count == 0);
}

TEST_CASE("water movement ripple timing keeps advancing during long high frame rate sessions")
{
    WaterRippleRuntime state;
    state.setEnabled(true);
    state.advance(86400, false);
    state.observe(0, {0, 0, 0}, true, 37);
    const double startSeconds = state.seconds();
    for (int frame = 0; frame < 1200; ++frame)
    {
        state.advance(0.00025f, false);
    }
    CHECK(state.seconds() - startSeconds == doctest::Approx(0.3));
    state.observe(0, {80, 0, 0}, true, 37);
    REQUIRE(state.ripples().size() == 1);
    state.advance(WaterRippleLifetime, false);
    CHECK(state.ripples().empty());
}

TEST_CASE("water movement ripples pause expire and clear immediately when disabled")
{
    WaterRippleRuntime state;
    state.observe(0, {0, 0, 0}, true, 37);
    state.advance(1, false);
    CHECK(state.seconds() == 0);
    CHECK(state.ripples().empty());
    state.setEnabled(true);
    state.observe(0, {0, 0, 0}, true, 37);
    state.advance(0.3f, false);
    state.observe(0, {80, 0, 0}, true, 37);
    REQUIRE(state.ripples().size() == 1);
    state.advance(10, true);
    CHECK(state.ripples().size() == 1);
    CHECK(state.seconds() == doctest::Approx(0.3f));
    state.advance(WaterRippleLifetime, false);
    CHECK(state.ripples().empty());
    state.setEnabled(false);
    state.observe(0, {160, 0, 0}, true, 37);
    CHECK(state.ripples().empty());
    state.setEnabled(true);
    state.observe(0, {160, 0, 0}, true, 37);
    CHECK(state.ripples().empty());
}
