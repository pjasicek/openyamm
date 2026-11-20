#include "doctest/doctest.h"

#include "game/indoor/IndoorDaylight.h"
#include "game/indoor/IndoorMapData.h"
#include "game/indoor/IndoorOpenSky.h"
#include "game/indoor/IndoorTerrainSurface.h"
#include "game/maps/IndoorSceneYml.h"
#include "game/render/TerrainMaterialConfig.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

using namespace OpenYAMM::Game;

namespace
{
std::string readOpenSkySceneText(const char *pRelativePath)
{
    std::ifstream stream(std::filesystem::path(OPENYAMM_SOURCE_DIR) / pRelativePath);
    REQUIRE(stream.good());
    std::ostringstream text;
    text << stream.rdbuf();
    return text.str();
}
}

TEST_CASE("indoor open sky: off by default, only sky faces of an open map give way to the sky")
{
    const IndoorOpenSky closed = {};
    CHECK_FALSE(closed.enabled);
    const uint32_t sky = static_cast<uint32_t>(FaceAttribute::IndoorSky);
    CHECK_FALSE(indoorFaceShowsOpenSky(closed, sky));

    IndoorOpenSky open = {};
    open.enabled = true;
    CHECK(indoorFaceShowsOpenSky(open, sky));
    CHECK(indoorFaceShowsOpenSky(open, sky | static_cast<uint32_t>(FaceAttribute::Invisible)));
    CHECK_FALSE(indoorFaceShowsOpenSky(open, 0));
    CHECK_FALSE(indoorFaceShowsOpenSky(open, static_cast<uint32_t>(FaceAttribute::Invisible)));
}

TEST_CASE("indoor open sky: block parsing and refusals")
{
    IndoorOpenSky sky = {};
    std::string error;
    REQUIRE_MESSAGE(parseIndoorSceneOpenSky("{mode: open}", sky, error), error);
    CHECK(sky.enabled);
    CHECK(sky.skyTexture.empty());
    CHECK(sky.preset.empty());

    CHECK_FALSE(sky.outdoorView);
    CHECK(sky.viewDistanceScale == 1.0f);

    REQUIRE_MESSAGE(parseIndoorSceneOpenSky("{mode: open, sky_texture: plansky3, preset: clear}", sky, error), error);
    CHECK(sky.skyTexture == "plansky3");
    CHECK(sky.preset == "clear");
    CHECK_FALSE(sky.outdoorView);

    // The outdoor view (a city's view distance and haze as an outdoor map's).
    REQUIRE_MESSAGE(parseIndoorSceneOpenSky("{mode: open, preset: cloudy, view: outdoor, view_distance_scale: 1.5}", sky,
        error), error);
    CHECK(sky.outdoorView);
    CHECK(sky.viewDistanceScale == 1.5f);
    // The weather over the open sky (devdocs/INDOOR_OPEN_SKY.md "Weather"): off unless asked for.
    CHECK_FALSE(sky.weatherRain);
    CHECK_FALSE(sky.weatherSnow);
    REQUIRE_MESSAGE(parseIndoorSceneOpenSky("{mode: open, weather: rain}", sky, error), error);
    CHECK(sky.weatherRain);
    CHECK_FALSE(sky.weatherSnow);
    REQUIRE_MESSAGE(parseIndoorSceneOpenSky("{mode: open, weather: snow}", sky, error), error);
    CHECK_FALSE(sky.weatherRain);
    CHECK(sky.weatherSnow);
    REQUIRE_MESSAGE(parseIndoorSceneOpenSky("{mode: open, weather: rain_and_snow}", sky, error), error);
    CHECK(sky.weatherRain);
    CHECK(sky.weatherSnow);
    REQUIRE_MESSAGE(parseIndoorSceneOpenSky("{mode: open, view: scene}", sky, error), error);
    CHECK_FALSE(sky.outdoorView);

    IndoorOpenSky untouched = {};
    CHECK_FALSE(parseIndoorSceneOpenSky("{mode: projected}", untouched, error));
    CHECK_FALSE(untouched.enabled);
    CHECK_FALSE(parseIndoorSceneOpenSky("{sky_texture: plansky3}", untouched, error));
    CHECK_FALSE(parseIndoorSceneOpenSky("{mode: open, weather: hail}", untouched, error));
    CHECK_FALSE(parseIndoorSceneOpenSky("open", untouched, error));
    CHECK_FALSE(parseIndoorSceneOpenSky("{mode: open, view: far}", untouched, error));
    CHECK_FALSE(parseIndoorSceneOpenSky("{mode: open, view: outdoor, view_distance_scale: 0}", untouched, error));
    CHECK_FALSE(untouched.enabled);
}

TEST_CASE("indoor open sky: a scene without the block keeps its sky faces")
{
    const std::string sceneText = readOpenSkySceneText("assets_dev/worlds/mm6/maps/6d02.scene.yml");
    std::string error;
    const std::optional<IndoorSceneData> scene = IndoorSceneYmlLoader{}.loadFromText(sceneText, error);
    REQUIRE_MESSAGE(scene, error);
    CHECK_FALSE(scene->openSky.enabled);

    const std::optional<IndoorSceneData> openScene =
        IndoorSceneYmlLoader{}.loadFromText(sceneText + "\nsky: {mode: open, sky_texture: plansky3}\n", error);
    REQUIRE_MESSAGE(openScene, error);
    CHECK(openScene->openSky.enabled);
    CHECK(openScene->openSky.skyTexture == "plansky3");

    // An overlay's block replaces the base scene's; an overlay without one keeps it.
    IndoorSceneData overlaid = *scene;
    REQUIRE_MESSAGE(IndoorSceneYmlLoader{}.applyOverlayFromText(
        overlaid, "format_version: 1\nkind: indoor_scene_overlay\nsky: {mode: open}\n", error), error);
    CHECK(overlaid.openSky.enabled);
    IndoorSceneData kept = *openScene;
    REQUIRE_MESSAGE(IndoorSceneYmlLoader{}.applyOverlayFromText(
        kept, "format_version: 1\nkind: indoor_scene_overlay\n", error), error);
    CHECK(kept.openSky.enabled);
    CHECK_FALSE(IndoorSceneYmlLoader{}.loadFromText(sceneText + "\nsky: {mode: closed}\n", error));
}

TEST_CASE("indoor daylight: block parsing and refusals")
{
    IndoorDaylight daylight = {};
    std::string error;
    REQUIRE_MESSAGE(parseIndoorSceneDaylight("{ambient_rgb: [80, 80, 80], sun_rgb: [255, 255, 255], "
        "night_scale_rgb: [134, 143, 168]}", daylight, error), error);
    CHECK(daylight.enabled);
    CHECK(daylight.ambient[0] == doctest::Approx(80.0f / 255.0f));
    CHECK(daylight.sun[2] == 1.0f);
    CHECK(daylight.dayScale == std::array<float, 3>{1.0f, 1.0f, 1.0f});
    CHECK(daylight.nightScale[2] == doctest::Approx(168.0f / 255.0f));

    CHECK_FALSE(daylight.sunDirection.has_value());
    CHECK(daylight.sunGain == 1.0f);
    REQUIRE_MESSAGE(parseIndoorSceneDaylight("{ambient_rgb: [80, 80, 80], sun_rgb: [255, 255, 255], "
        "sun_direction: [0, -3, 4], sun_gain: 4}", daylight, error), error);
    REQUIRE(daylight.sunDirection.has_value());
    CHECK((*daylight.sunDirection)[1] == doctest::Approx(-0.6f));
    CHECK((*daylight.sunDirection)[2] == doctest::Approx(0.8f));
    CHECK(daylight.sunGain == 4.0f);
    CHECK(evaluateIndoorDaylight(daylight, 600.0f).sunDirection[2] == doctest::Approx(0.8f));
    CHECK(evaluateIndoorDaylight(daylight, 600.0f).sunGain == 4.0f);

    IndoorDaylight untouched = {};
    CHECK_FALSE(parseIndoorSceneDaylight("{ambient_rgb: [80, 80, 80], sun_rgb: [1, 1, 1], sun_direction: [0, 0, 0]}",
        untouched, error));
    CHECK_FALSE(parseIndoorSceneDaylight("{ambient_rgb: [80, 80, 80], sun_rgb: [1, 1, 1], sun_gain: 0}", untouched,
        error));
    CHECK_FALSE(parseIndoorSceneDaylight("{ambient_rgb: [80, 80, 80]}", untouched, error));
    CHECK_FALSE(parseIndoorSceneDaylight("{ambient_rgb: [80, 80], sun_rgb: [1, 1, 1]}", untouched, error));
    CHECK_FALSE(parseIndoorSceneDaylight("{ambient_rgb: [80, 80, 300], sun_rgb: [1, 1, 1]}", untouched, error));
    CHECK_FALSE(parseIndoorSceneDaylight("{ambient_rgb: [80, 80, 80], sun_rgb: [1, 1, 1], scale: 2}", untouched,
        error));
    CHECK_FALSE(untouched.enabled);
}

TEST_CASE("indoor daylight: MM9's light by day, its night scale at night, no sun after sunset")
{
    IndoorDaylight daylight = {};
    CHECK(evaluateIndoorDaylight(daylight, 720.0f).ambient == std::array<float, 3>{0.0f, 0.0f, 0.0f});
    CHECK_FALSE(indoorDaylightSector(daylight, 0));

    daylight.enabled = true;
    daylight.ambient = {0.3f, 0.3f, 0.3f};
    daylight.sun = {1.0f, 1.0f, 1.0f};
    daylight.nightScale = {0.5f, 0.5f, 0.75f};

    CHECK(indoorDaylightWeight(720.0f) == doctest::Approx(1.0f));
    CHECK(indoorDaylightWeight(0.0f) == doctest::Approx(0.0f));
    CHECK(indoorDaylightWeight(360.0f) == doctest::Approx(0.5f));
    CHECK(indoorDaylightWeight(720.0f + 1440.0f) == doctest::Approx(1.0f));

    const IndoorDaylightLight noon = evaluateIndoorDaylight(daylight, 720.0f);
    CHECK(noon.ambient[0] == doctest::Approx(0.3f));
    CHECK(noon.sun[0] == doctest::Approx(1.0f));
    // The sky's sun: rises at +X at 05:00, high at 13:00.
    CHECK(noon.sunDirection[2] > 0.9f);

    const IndoorDaylightLight midnight = evaluateIndoorDaylight(daylight, 0.0f);
    CHECK(midnight.ambient[0] == doctest::Approx(0.15f));
    CHECK(midnight.ambient[2] == doctest::Approx(0.225f));
    CHECK(midnight.sun == std::array<float, 3>{0.0f, 0.0f, 0.0f});

    // Twilight after the 21:00 sunset: some sky light, no sun.
    const IndoorDaylightLight late = evaluateIndoorDaylight(daylight, 21.0f * 60.0f + 45.0f);
    CHECK(late.sun[0] == doctest::Approx(0.0f));
    CHECK(late.ambient[0] > midnight.ambient[0]);

    CHECK(indoorDaylightRoomLight(noon) == doctest::Approx(0.8f));
    CHECK(indoorDaylightRoomLight(midnight) <= 0.25f);
    // Models taking the sun by direction keep only the ambient share: the room light less half the sun.
    CHECK(indoorDaylightModelAmbient(noon) == doctest::Approx(0.3f));
    CHECK(indoorDaylightModelAmbient(noon) + 0.5f * noon.sun[0] == doctest::Approx(indoorDaylightRoomLight(noon)));
}

TEST_CASE("indoor daylight: the fog colour's scale follows the open air's light, 1 at noon")
{
    IndoorDaylight daylight = {};
    CHECK(indoorDaylightFogScale(daylight, 0.0f) == std::array<float, 3>{1.0f, 1.0f, 1.0f});

    daylight.enabled = true;
    daylight.ambient = {0.3f, 0.3f, 0.3f};
    daylight.sun = {1.0f, 1.0f, 1.0f};
    daylight.nightScale = {0.5f, 0.5f, 0.75f};

    const std::array<float, 3> noon = indoorDaylightFogScale(daylight, 720.0f);
    CHECK(noon[0] == doctest::Approx(1.0f));
    CHECK(noon[2] == doctest::Approx(1.0f));
    CHECK(indoorDaylightFogScale(daylight, 720.0f + 3.0f * 1440.0f)[1] == doctest::Approx(1.0f));
    // Midnight: the night's ambient (0.15, 0.15, 0.225) over noon's ambient and half sun (0.8).
    const std::array<float, 3> midnight = indoorDaylightFogScale(daylight, 0.0f);
    CHECK(midnight[0] == doctest::Approx(0.15f / 0.8f));
    CHECK(midnight[2] == doctest::Approx(0.225f / 0.8f));
    const std::array<float, 3> evening = indoorDaylightFogScale(daylight, 19.0f * 60.0f);
    CHECK(evening[0] > midnight[0]);
    CHECK(evening[0] < 1.0f);
}

TEST_CASE("indoor daylight: a lightmap's daylight page draws as baked at noon and darkens by night")
{
    IndoorDaylight daylight = {};
    const IndoorBakedDaylightScale none = indoorBakedDaylightScale(daylight, {}, 0.18f);
    CHECK(indoorBakedDaylightTexel(none, {0.4f, 0.5f, 0.6f})[1] == doctest::Approx(0.5f));

    daylight.enabled = true;
    daylight.ambient = {0.3f, 0.3f, 0.3f};
    daylight.sun = {1.0f, 1.0f, 1.0f};
    daylight.nightScale = {0.5f, 0.5f, 0.75f};
    constexpr float Floor = 0.18f;

    // Noon: as baked, a shaded texel (the ambient alone) and a sunlit one alike.
    const IndoorBakedDaylightScale noon = indoorBakedDaylightScale(daylight, evaluateIndoorDaylight(daylight, 720.0f),
        Floor);
    CHECK(indoorBakedDaylightTexel(noon, {0.3f, 0.3f, 0.3f})[0] == doctest::Approx(0.3f));
    CHECK(indoorBakedDaylightTexel(noon, {1.0f, 1.0f, 1.0f})[2] == doctest::Approx(1.0f));

    // Midnight, with the renderer's floor under the ambient: both read as the night's ambient (no sun), so a sunlit
    // facade and a shaded one are equally dark, as on the vertex-lit faces open to the sky.
    IndoorDaylightLight midnight = evaluateIndoorDaylight(daylight, 0.0f);
    for (float &channel : midnight.ambient)
    {
        channel = std::max(channel, Floor);
    }
    const IndoorBakedDaylightScale night = indoorBakedDaylightScale(daylight, midnight, Floor);
    CHECK(indoorBakedDaylightTexel(night, {0.3f, 0.3f, 0.3f})[0] == doctest::Approx(0.18f));
    CHECK(indoorBakedDaylightTexel(night, {1.0f, 1.0f, 1.0f})[0] == doctest::Approx(0.18f));
    CHECK(indoorBakedDaylightTexel(night, {1.0f, 1.0f, 1.0f})[2] == doctest::Approx(0.225f));
    // A texel darker than the ambient (a fallback texel) is all sky light.
    CHECK(indoorBakedDaylightTexel(night, {0.15f, 0.15f, 0.15f})[0] == doctest::Approx(0.09f));

    // An ambient under the floor never darkens; a map whose bake has no sun (no StaticSunLight) has only ambient.
    daylight.ambient = {0.1f, 0.1f, 0.1f};
    daylight.sun = {0.0f, 0.0f, 0.0f};
    const IndoorBakedDaylightScale dim = indoorBakedDaylightScale(daylight, midnight, Floor);
    CHECK(dim.ambientScale[0] == doctest::Approx(1.0f));
    CHECK(dim.sunScale[0] == doctest::Approx(dim.ambientScale[0]));
}

TEST_CASE("indoor daylight: the open air's lights are the wide ones of a daylight map and follow the sun")
{
    IndoorMapData map = {};
    map.lights.resize(3);
    map.lights[0].radius = 512;    // a lamp
    map.lights[1].radius = 1792;   // MM9's widest lamp (Sturmford City)
    map.lights[2].radius = 5120;   // a region's light over the land (Ravensford)
    CHECK(indoorOpenAirLights(map) == std::vector<uint8_t>{0, 0, 0});
    CHECK_FALSE(indoorOpenAirLight(map.daylight, 2));

    map.daylight.enabled = true;
    map.daylight.ambient = {0.3f, 0.3f, 0.3f};
    map.daylight.sun = {1.0f, 1.0f, 1.0f};
    map.daylight.openAirLights = indoorOpenAirLights(map);
    CHECK(map.daylight.openAirLights == std::vector<uint8_t>{0, 0, 1});
    CHECK(indoorOpenAirLight(map.daylight, 2));
    CHECK_FALSE(indoorOpenAirLight(map.daylight, 0));
    CHECK_FALSE(indoorOpenAirLight(map.daylight, 7));

    // Full at noon, none at 03:00 (Ravensford's white night scale changes nothing: the sun has set), half at 06:00.
    CHECK(indoorOpenAirLightScale(IndoorDaylight{}, {}) == doctest::Approx(1.0f));
    CHECK(indoorOpenAirLightScale(map.daylight, evaluateIndoorDaylight(map.daylight, 720.0f)) == doctest::Approx(1.0f));
    CHECK(indoorOpenAirLightScale(map.daylight, evaluateIndoorDaylight(map.daylight, 180.0f)) == doctest::Approx(0.0f));
    CHECK(indoorOpenAirLightScale(map.daylight, evaluateIndoorDaylight(map.daylight, 360.0f))
        == doctest::Approx(0.5f));

    // A scene without a sun: the ambient's ratio.
    map.daylight.sun = {0.0f, 0.0f, 0.0f};
    map.daylight.nightScale = {0.5f, 0.5f, 0.5f};
    CHECK(indoorOpenAirLightScale(map.daylight, evaluateIndoorDaylight(map.daylight, 0.0f)) == doctest::Approx(0.5f));
}

TEST_CASE("indoor daylight: the sectors open to the sky")
{
    // Sector 1: the air over the roofs with a sky face; sector 2: a street under it, joined by a horizontal portal;
    // sector 3: a house off the street through a doorway (vertical portal); sector 4: a cellar under the house's
    // trapdoor (horizontal, but under a closed room).
    IndoorMapData map = {};
    map.sectors.resize(5);
    map.vertices = {{0, 0, 100}, {100, 0, 100}, {100, 100, 100}, {0, 100, 100},
        {0, 0, 0}, {0, 100, 0}, {0, 100, 50}, {0, 0, 50}};
    const auto face = [](std::vector<uint16_t> vertices, uint16_t room, uint16_t behind, bool portal,
        uint32_t attributes)
    {
        IndoorFace result = {};
        result.vertexIndices = std::move(vertices);
        result.roomNumber = room;
        result.roomBehindNumber = behind;
        result.isPortal = portal;
        result.attributes = attributes;
        return result;
    };
    const uint32_t sky = static_cast<uint32_t>(FaceAttribute::IndoorSky);
    // Counter-clockwise from above: the normal points up, into room 1 above.
    map.faces.push_back(face({0, 1, 2, 3}, 1, 2, true, 0));
    map.faces.push_back(face({0, 1, 2, 3}, 1, 1, false, sky));
    map.faces.push_back(face({4, 5, 6, 7}, 2, 3, true, 0));
    // The cellar's trapdoor: the normal points up into the house.
    map.faces.push_back(face({0, 1, 2, 3}, 3, 4, true, 0));

    std::vector<uint8_t> open = indoorOpenSkySectors(map);
    REQUIRE(open.size() == 5);
    CHECK(open == std::vector<uint8_t>{0, 1, 1, 0, 0});

    // A skylight (a sky face over a tenth of the house's floor) leaves the house closed; a sky over a quarter opens it.
    map.vertices.insert(map.vertices.end(), {{0, 0, 10}, {100, 0, 10}, {100, 100, 10}, {0, 100, 10},
        {0, 0, 90}, {10, 0, 90}, {10, 100, 90}, {0, 100, 90}, {0, 0, 80}, {30, 0, 80}, {30, 100, 80}, {0, 100, 80}});
    map.faces.push_back(face({8, 9, 10, 11}, 3, 3, false, 0));
    map.faces.push_back(face({15, 14, 13, 12}, 3, 3, false, sky));
    CHECK(indoorOpenSkySectors(map)[3] == 0);
    map.faces.push_back(face({19, 18, 17, 16}, 3, 3, false, sky));
    CHECK(indoorOpenSkySectors(map)[3] == 1);
    map.faces.resize(4);

    // The same portal wound the other way (normal down, into the street) still lets the light down.
    map.faces[0] = face({3, 2, 1, 0}, 2, 1, true, 0);
    open = indoorOpenSkySectors(map);
    CHECK(open == std::vector<uint8_t>{0, 1, 1, 0, 0});
}

TEST_CASE("indoor daylight: a scene without the block has none, the block marks the open sectors")
{
    const std::string sceneText = readOpenSkySceneText("assets_dev/worlds/mm6/maps/6d02.scene.yml");
    std::string error;
    const std::optional<IndoorSceneData> scene = IndoorSceneYmlLoader{}.loadFromText(sceneText, error);
    REQUIRE_MESSAGE(scene, error);
    CHECK_FALSE(scene->daylight.enabled);

    const std::optional<IndoorSceneData> daylit = IndoorSceneYmlLoader{}.loadFromText(
        sceneText + "\ndaylight: {ambient_rgb: [80, 80, 80], sun_rgb: [255, 255, 255]}\n", error);
    REQUIRE_MESSAGE(daylit, error);
    CHECK(daylit->daylight.enabled);
}

TEST_CASE("indoor footstep sounds: block parsing, refusals and the floor's texture")
{
    std::vector<IndoorFootstepSound> sounds;
    std::string error;
    REQUIRE(parseIndoorSceneFootstepSounds(
        "[{texture_names: [ASHC08T3G2, ashro4zhnj], walk_sound_id: 93, run_sound_id: 54},"
        " {texture_names: [ashw5wt0xi], walk_sound_id: 103, run_sound_id: 64}]", sounds, error));
    REQUIRE_EQ(sounds.size(), 2u);
    CHECK_EQ(sounds[0].textureNames[0], "ashc08t3g2");
    CHECK_EQ(sounds[0].walkSoundId, 93u);
    CHECK_EQ(sounds[0].runSoundId, 54u);

    std::vector<IndoorFootstepSound> refused;
    CHECK_FALSE(parseIndoorSceneFootstepSounds("{texture_names: [a], walk_sound_id: 1, run_sound_id: 2}", refused,
        error));
    CHECK_FALSE(parseIndoorSceneFootstepSounds("[{texture_names: [], walk_sound_id: 1, run_sound_id: 2}]", refused,
        error));
    CHECK_FALSE(parseIndoorSceneFootstepSounds("[{texture_names: [a], walk_sound_id: 1}]", refused, error));
    CHECK_FALSE(parseIndoorSceneFootstepSounds("[{texture_names: [a], walk_sound_id: 1, run_sound_id: 2, x: 3}]",
        refused, error));

    IndoorMapData map;
    map.faces.resize(3);
    map.faces[0].textureName = "ASHRO4ZHNJ";
    map.faces[1].textureName = "ASHW5WT0XI";
    map.faces[2].textureName = "ASHRUIN000";
    CHECK(findIndoorFootstepSound(map, 0) == nullptr);       // no table: every floor keeps the stone hall sound
    map.footstepSounds = sounds;
    REQUIRE(findIndoorFootstepSound(map, 0) != nullptr);
    CHECK_EQ(findIndoorFootstepSound(map, 0)->walkSoundId, 93u);
    CHECK_EQ(findIndoorFootstepSound(map, 1)->runSoundId, 64u);
    CHECK(findIndoorFootstepSound(map, 2) == nullptr);
    CHECK(findIndoorFootstepSound(map, static_cast<size_t>(-1)) == nullptr);
}

TEST_CASE("indoor party movement: steep slopes climb by default, block by the scene")
{
    IndoorSceneYmlLoader loader;
    std::string error;
    const std::string base = readOpenSkySceneText("assets_dev/worlds/mm6/maps/6d02.scene.yml") + "\n";
    const std::optional<IndoorSceneData> plain = loader.loadFromText(base, error);
    REQUIRE_MESSAGE(plain.has_value(), error);
    CHECK_FALSE(plain->partySteepSlopesBlock);
    const std::optional<IndoorSceneData> blocking =
        loader.loadFromText(base + "party_movement: {steep_slopes: block}\n", error);
    REQUIRE_MESSAGE(blocking.has_value(), error);
    CHECK(blocking->partySteepSlopesBlock);
    CHECK_FALSE(loader.loadFromText(base + "party_movement: {steep_slopes: fly}\n", error).has_value());
    CHECK_FALSE(loader.loadFromText(base + "party_movement: {jump: 3}\n", error).has_value());
}

TEST_CASE("indoor actor movement: drops guarded by default, followed by the scene")
{
    IndoorSceneYmlLoader loader;
    std::string error;
    const std::string base = readOpenSkySceneText("assets_dev/worlds/mm6/maps/6d02.scene.yml") + "\n";
    const std::optional<IndoorSceneData> plain = loader.loadFromText(base, error);
    REQUIRE_MESSAGE(plain.has_value(), error);
    CHECK_FALSE(plain->actorDropsFollow);
    const std::optional<IndoorSceneData> follow = loader.loadFromText(base + "actor_movement: {drops: follow}\n", error);
    REQUIRE_MESSAGE(follow.has_value(), error);
    CHECK(follow->actorDropsFollow);
    CHECK_FALSE(loader.loadFromText(base + "actor_movement: {drops: jump}\n", error).has_value());
    CHECK_FALSE(loader.loadFromText(base + "actor_movement: {climb: true}\n", error).has_value());
}

TEST_CASE("indoor actor detection: neighbour wakes by default, none by the scene")
{
    IndoorSceneYmlLoader loader;
    std::string error;
    const std::string base = readOpenSkySceneText("assets_dev/worlds/mm6/maps/6d02.scene.yml") + "\n";
    const std::optional<IndoorSceneData> plain = loader.loadFromText(base, error);
    REQUIRE_MESSAGE(plain.has_value(), error);
    CHECK(plain->actorNeighbourWakes);
    const std::optional<IndoorSceneData> none = loader.loadFromText(base + "actor_detection: {wakes: none}\n", error);
    REQUIRE_MESSAGE(none.has_value(), error);
    CHECK_FALSE(none->actorNeighbourWakes);
    const std::optional<IndoorSceneData> wakes =
        loader.loadFromText(base + "actor_detection: {wakes: neighbours}\n", error);
    REQUIRE_MESSAGE(wakes.has_value(), error);
    CHECK(wakes->actorNeighbourWakes);
    CHECK_FALSE(loader.loadFromText(base + "actor_detection: {wakes: all}\n", error).has_value());
    CHECK_FALSE(loader.loadFromText(base + "actor_detection: {hearing: true}\n", error).has_value());
    // The provoke radius: the world's without the key, the scene's with it.
    CHECK_FALSE(plain->actorProvokeRadius.has_value());
    const std::optional<IndoorSceneData> radius =
        loader.loadFromText(base + "actor_detection: {wakes: none, provoke_radius: 192}\n", error);
    REQUIRE_MESSAGE(radius.has_value(), error);
    CHECK_FALSE(radius->actorNeighbourWakes);
    REQUIRE(radius->actorProvokeRadius.has_value());
    CHECK(*radius->actorProvokeRadius == doctest::Approx(192.0f));
    CHECK_FALSE(loader.loadFromText(base + "actor_detection: {provoke_radius: -1}\n", error).has_value());
}

TEST_CASE("indoor static lights: both sides by default, the front only by the scene")
{
    IndoorSceneYmlLoader loader;
    std::string error;
    const std::string base = readOpenSkySceneText("assets_dev/worlds/mm6/maps/6d02.scene.yml") + "\n";
    const std::optional<IndoorSceneData> plain = loader.loadFromText(base, error);
    REQUIRE_MESSAGE(plain.has_value(), error);
    CHECK_FALSE(plain->staticLightsFrontOnly);
    const std::optional<IndoorSceneData> both = loader.loadFromText(base + "static_lights: {sides: both}\n", error);
    REQUIRE_MESSAGE(both.has_value(), error);
    CHECK_FALSE(both->staticLightsFrontOnly);
    const std::optional<IndoorSceneData> front = loader.loadFromText(base + "static_lights: {sides: front}\n", error);
    REQUIRE_MESSAGE(front.has_value(), error);
    CHECK(front->staticLightsFrontOnly);
    CHECK_FALSE(loader.loadFromText(base + "static_lights: {sides: back}\n", error).has_value());
    CHECK_FALSE(loader.loadFromText(base + "static_lights: {shadows: true}\n", error).has_value());
}

TEST_CASE("indoor actor barriers: none by default, the scene's faces when listed")
{
    IndoorSceneYmlLoader loader;
    std::string error;
    const std::string base = readOpenSkySceneText("assets_dev/worlds/mm6/maps/6d02.scene.yml") + "\n";
    const std::optional<IndoorSceneData> plain = loader.loadFromText(base, error);
    REQUIRE_MESSAGE(plain.has_value(), error);
    CHECK(plain->actorBarrierFaceIds.empty());
    const std::optional<IndoorSceneData> barriers = loader.loadFromText(base + "actor_barriers: {faces: [4, 7]}\n", error);
    REQUIRE_MESSAGE(barriers.has_value(), error);
    CHECK(barriers->actorBarrierFaceIds == std::vector<uint16_t>{4, 7});
    CHECK_FALSE(loader.loadFromText(base + "actor_barriers: [4, 7]\n", error).has_value());
    CHECK_FALSE(loader.loadFromText(base + "actor_barriers: {walls: [4]}\n", error).has_value());
}

TEST_CASE("indoor terrain: block parsing and refusals")
{
    IndoorSceneYmlLoader loader;
    std::string error;
    const std::string base = readOpenSkySceneText("assets_dev/worlds/mm6/maps/6d02.scene.yml") + "\n";
    const std::optional<IndoorSceneData> plain = loader.loadFromText(base, error);
    REQUIRE_MESSAGE(plain.has_value(), error);
    CHECK_FALSE(plain->terrain.has_value());
    const std::optional<IndoorSceneData> terrain = loader.loadFromText(
        base + "terrain: {materials: isle_blv.yml, textures: [ASHC08T3G2, ashro4zhnj, ashc08t3g2]}\n", error);
    REQUIRE_MESSAGE(terrain.has_value(), error);
    REQUIRE(terrain->terrain.has_value());
    CHECK_EQ(terrain->terrain->materials, "isle_blv.yml");
    REQUIRE_EQ(terrain->terrain->textureNames.size(), 2u);
    CHECK_EQ(terrain->terrain->textureNames[0], "ashc08t3g2");
    CHECK_EQ(terrain->terrain->textureNames[1], "ashro4zhnj");
    CHECK(terrain->terrain->excludedFaces.empty());
    const std::optional<IndoorSceneData> excluded = loader.loadFromText(
        base + "terrain: {materials: a.yml, textures: [a], exclude_faces: [2387, 2386, 2387]}\n", error);
    REQUIRE_MESSAGE(excluded.has_value(), error);
    CHECK_EQ(excluded->terrain->excludedFaces, std::vector<uint32_t>{2386, 2387});
    CHECK_FALSE(loader.loadFromText(base + "terrain: {materials: a.yml, textures: [a], exclude_faces: 3}\n", error)
        .has_value());
    CHECK_FALSE(loader.loadFromText(base + "terrain: {materials: a.yml, textures: []}\n", error).has_value());
    CHECK_FALSE(loader.loadFromText(base + "terrain: {textures: [a]}\n", error).has_value());
    CHECK_FALSE(loader.loadFromText(base + "terrain: {materials: ../a.yml, textures: [a]}\n", error).has_value());
    CHECK_FALSE(loader.loadFromText(base + "terrain: {materials: a.yml, textures: [a], grass: 1}\n", error)
        .has_value());
}

TEST_CASE("indoor terrain: the smooth normal runs on across an edge and keeps a sharp crease")
{
    // Two quads hinged at x = 0: flat ground (x < 0) and a 30-degree rise (x > 0), plus a wall at x = 400.
    IndoorMapData map;
    std::vector<IndoorVertex> vertices = {
        {-400, 0, 0}, {0, 0, 0}, {0, 400, 0}, {-400, 400, 0},
        {0, 0, 0}, {346, 0, 200}, {346, 400, 200}, {0, 400, 0},
        {346, 0, 200}, {346, 0, 600}, {346, 400, 600}, {346, 400, 200}};
    map.faces.resize(3);
    for (size_t face = 0; face < 3; ++face)
    {
        for (uint16_t corner = 0; corner < 4; ++corner)
        {
            map.faces[face].vertexIndices.push_back(uint16_t(face * 4 + corner));
        }
    }
    IndoorTerrainSurface surface;
    surface.build(map, vertices, {1, 1, 1});
    const bx::Vec3 ground = surface.faceNormal(0);
    const bx::Vec3 slope = surface.faceNormal(1);
    CHECK(ground.z > 0.99f);
    CHECK(slope.z == doctest::Approx(std::cos(3.14159265f / 6.0f)).epsilon(0.01));
    // On the hinge both faces see the same normal, halfway between them.
    const bx::Vec3 fromGround = surface.normalAt({0.0f, 200.0f, 0.0f}, ground);
    const bx::Vec3 fromSlope = surface.normalAt({0.0f, 200.0f, 0.0f}, slope);
    CHECK(fromGround.x == doctest::Approx(fromSlope.x).epsilon(0.001));
    CHECK(fromGround.z == doctest::Approx(fromSlope.z).epsilon(0.001));
    CHECK(fromGround.z < ground.z);
    CHECK(fromGround.z > slope.z);
    // Far from any edge a face keeps its own slope.
    const bx::Vec3 middle = surface.normalAt({-250.0f, 200.0f, 0.0f}, ground);
    CHECK(middle.z == doctest::Approx(1.0f));
    // The wall meets the slope at 60 degrees from it but 90 from the ground: the slope's normal at their edge leans
    // toward the wall, the ground never takes the wall's.
    const bx::Vec3 wall = surface.faceNormal(2);
    CHECK(std::abs(wall.z) < 0.01f);
    CHECK(surface.steepnessAt({-300.0f, 200.0f, 0.0f}) < 0.05f);
}

TEST_CASE("terrain material config: the outdoor format, refusals named by the file")
{
    std::string error;
    const std::string text = "version: 1\ntexels_per_cell: 16\nweights: [isle_weights0.png]\nweighted_layers: 2\n"
        "layers:\n- {name: grass, library: grass_meadow, tint: [1, 1, 1]}\n"
        "- {name: cliff, library: rock_layered, tint: [0.8, 0.7, 0.6], repeat: 640}\n"
        "slope: {layer: 1, start: 0.36, end: 0.56}\n";
    const std::optional<OutdoorTerrainMaterialConfig> config =
        parseTerrainMaterialConfig(text, "worlds/mm9/terrain_materials/", "isle.yml", error);
    REQUIRE_MESSAGE(config.has_value(), error);
    CHECK_EQ(config->directory, "worlds/mm9/terrain_materials/");
    CHECK_EQ(config->weightedLayers, 2);
    REQUIRE_EQ(config->layers.size(), 2u);
    CHECK_EQ(config->layers[1].repeat, doctest::Approx(640.0f));
    CHECK_EQ(config->slopeLayer, 1);
    CHECK_FALSE(parseTerrainMaterialConfig("version: 2\n", "d/", "bad.yml", error).has_value());
    CHECK(error.find("bad.yml") != std::string::npos);
}
