#include "doctest/doctest.h"

#include "game/app/GameSettings.h"
#include "game/debug/ScreenshotTour.h"

#include <filesystem>
#include <fstream>
#include <string>

using namespace OpenYAMM::Game;

TEST_CASE("screenshot tour loads ordered poses and relative output with per-shot delays")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-screenshot-tour-test.yml";
    {
        std::ofstream output(path);
        output << "output_dir: screenshots\nsettle_seconds: 2\nexit: true\nshots:\n"
                  "  - name: coast\n    position: [1370.718, -8612.107, 974.502]\n"
                  "    yaw: 0.322\n    pitch: -0.371493\n"
                  "  - name: sea\n    position: [1400, -8600, 975]\n    settle_seconds: 0\n"
                  "    time: \"20:45\"\n    commands: [\"sky weather 5\", \"sky rain heavy\"]\n";
    }
    std::string error = "previous error";
    const std::optional<ScreenshotTour> tour = loadScreenshotTour(path, error);
    REQUIRE(tour);
    CHECK(error.empty());
    REQUIRE(tour->shots.size() == 2);
    CHECK(tour->exitWhenFinished);
    CHECK(tour->defaultSettleSeconds == 2.0f);
    CHECK(std::filesystem::path(tour->outputDirectory) == path.parent_path() / "screenshots");
    CHECK(tour->shots[0].name == "coast");
    CHECK(tour->shots[0].z == doctest::Approx(974.502f));
    CHECK(tour->shots[0].pitchRadians == doctest::Approx(-0.371493f));
    CHECK(tour->shots[0].settleSeconds == -1.0f);
    CHECK(tour->shots[1].name == "sea");
    CHECK(tour->shots[1].settleSeconds == 0.0f);
    CHECK_FALSE(tour->shots[0].clockMinutes);
    REQUIRE(tour->shots[1].clockMinutes);
    CHECK(*tour->shots[1].clockMinutes == 20 * 60 + 45);
    REQUIRE(tour->shots[1].commands.size() == 2);
    CHECK(tour->shots[1].commands[1] == "sky rain heavy");
    std::filesystem::remove(path);
}

TEST_CASE("screenshot tour rejects malformed poses paths and non-finite values")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-screenshot-invalid-test.yml";
    for (const char *pYaml : {
        "shots: []",
        "shots: [{name: ../escape, position: [0, 0, 0]}]",
        "shots: [{name: coast, position: [0, 0]}]",
        "shots: [{name: coast, position: [0, 0, .nan]}]",
        "shots: [{name: coast, position: [0, 0, 1e100]}]",
        "shots: [{name: coast, position: [0, 0, 0], yaw: .inf}]",
        "shots: [{name: coast, position: [0, 0, 0], pitch: 2}]",
        "shots: [{name: coast, position: [0, 0, 0], settle_seconds: -1}]",
        "shots: [{name: coast, position: [0, 0, 0], time: \"24:00\"}]",
        "shots: [{name: coast, position: [0, 0, 0], time: \"9:5\"}]",
        "shots: [{name: coast, position: [0, 0, 0], commands: \"sky clear\"}]",
        "shots: [{name: coast, position: [0, 0, 0], commands: [\"\"]}]",
        "settle_seconds: 601\nshots: [{name: coast, position: [0, 0, 0]}]",
        "exit: perhaps\nshots: [{name: coast, position: [0, 0, 0]}]",
        "output_dir: []\nshots: [{name: coast, position: [0, 0, 0]}]"})
    {
        CAPTURE(pYaml);
        {
            std::ofstream output(path);
            output << pYaml;
        }
        std::string error;
        CHECK_FALSE(loadScreenshotTour(path, error));
        CHECK_FALSE(error.empty());
    }
    std::filesystem::remove(path);
}

TEST_CASE("screenshot launch directives are read but never persisted")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-screenshot-settings-test.ini";
    {
        std::ofstream output(path);
        output << "[debug]\nmenu_input_tour_path=menu.yml\nscreenshot_path=shot.png\nscreenshot_delay_seconds=4\n"
            << "screenshot_tour_path=tour.yml\neffect_spawn_id=mm9:firefly\n"
            << "effect_spawn_x=1\neffect_spawn_y=2\neffect_spawn_z=3\n"
            << "effect_spawn_scale=2\neffect_spawn_yaw_radians=1.5\n"
            << "effect_spawn_count=32\neffect_stats_delay_seconds=0.75\n"
            << "actor_models=true\nactor_spawn_id=502\nactor_spawn_count=3\n"
            << "actor_models_manifest=worlds/mm6/models/sorpigal_demon_crowd.yml\n"
            << "actor_spawn_x=10\nactor_spawn_y=20\nactor_spawn_z=30\n"
            << "model_spawn_path=engine/models/fixtures/shared_model_fixture.glb\n"
            << "model_spawn_clip=bob_spin\n"
            << "model_spawn_x=4\nmodel_spawn_y=5\nmodel_spawn_z=6\n"
            << "model_spawn_scale=128\nmodel_spawn_yaw_radians=0.25\nmodel_spawn_markers=true\n";
    }
    std::string error;
    const std::optional<GameSettings> settings = loadGameSettings(path, error);
    REQUIRE(settings);
    CHECK(settings->screenshotPath == "shot.png");
    CHECK(settings->screenshotDelaySeconds == 4.0f);
    CHECK(settings->screenshotTourPath == "tour.yml");
    CHECK(settings->menuInputTourPath == "menu.yml");
    CHECK(settings->effectSpawnId == "mm9:firefly");
    const std::array<float, 3> expectedEffectPosition = {1.0f, 2.0f, 3.0f};
    CHECK(settings->effectSpawnPosition == expectedEffectPosition);
    CHECK(settings->effectSpawnScale == 2.0f);
    CHECK(settings->effectSpawnYawRadians == 1.5f);
    CHECK_EQ(settings->effectSpawnCount, 32u);
    CHECK_EQ(settings->effectStatsDelaySeconds, doctest::Approx(0.75f));
    CHECK(settings->actorModels);
    CHECK(settings->actorModelsManifest == "worlds/mm6/models/sorpigal_demon_crowd.yml");
    CHECK_EQ(settings->actorSpawnId, 502);
    CHECK_EQ(settings->actorSpawnCount, 3u);
    const std::array<float, 3> expectedActorPosition = {10, 20, 30};
    CHECK(settings->actorSpawnPosition == expectedActorPosition);
    CHECK(settings->modelSpawnPath == "engine/models/fixtures/shared_model_fixture.glb");
    CHECK(settings->modelSpawnClip == "bob_spin");
    const std::array<float, 3> expectedModelPosition = {4.0f, 5.0f, 6.0f};
    CHECK(settings->modelSpawnPosition == expectedModelPosition);
    CHECK(settings->modelSpawnScale == 128.0f);
    CHECK(settings->modelSpawnYawRadians == 0.25f);
    CHECK(settings->modelSpawnMarkers);
    REQUIRE(saveGameSettings(path, *settings, error));
    const std::optional<GameSettings> reloaded = loadGameSettings(path, error);
    REQUIRE(reloaded);
    CHECK(reloaded->screenshotPath.empty());
    CHECK(reloaded->screenshotTourPath.empty());
    CHECK(reloaded->menuInputTourPath.empty());
    CHECK(reloaded->screenshotDelaySeconds == 0.0f);
    CHECK(reloaded->effectSpawnId.empty());
    CHECK_EQ(reloaded->effectSpawnCount, 1u);
    CHECK_EQ(reloaded->effectStatsDelaySeconds, doctest::Approx(-1.0f));
    CHECK(reloaded->actorModels);    // a persisted toggle, unlike the launch directives
    CHECK(reloaded->actorModelsManifest.empty());
    CHECK_EQ(reloaded->actorSpawnId, 0);
    CHECK(reloaded->modelSpawnPath.empty());
    CHECK(reloaded->modelSpawnClip.empty());
    CHECK_FALSE(reloaded->modelSpawnMarkers);
    for (const char *pInvalid : {"-1", "nan", "inf", "601", "not-a-number"})
    {
        CAPTURE(pInvalid);
        {
            std::ofstream output(path);
            output << "[debug]\nscreenshot_delay_seconds=" << pInvalid << '\n';
        }
        CHECK_FALSE(loadGameSettings(path, error));
        CHECK(error.find("screenshot_delay_seconds") != std::string::npos);
    }
    std::filesystem::remove(path);
}

TEST_CASE("melee hit blood effects setting is opt-in and persists")
{
    CHECK_FALSE(GameSettings{}.meleeHitBloodEffects);

    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / "openyamm-melee-hit-blood-settings-test.ini";
    {
        std::ofstream output(path);
        output << "[gameplay]\nmelee_hit_blood_effects=true\n";
    }

    std::string error;
    const std::optional<GameSettings> settings = loadGameSettings(path, error);
    REQUIRE(settings);
    CHECK(settings->meleeHitBloodEffects);
    REQUIRE(saveGameSettings(path, *settings, error));

    const std::optional<GameSettings> reloaded = loadGameSettings(path, error);
    REQUIRE(reloaded);
    CHECK(reloaded->meleeHitBloodEffects);

    std::filesystem::remove(path);
}
