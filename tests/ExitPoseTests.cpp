#include "doctest/doctest.h"

#include "game/app/GameSettings.h"
#include "game/debug/ExitPose.h"

#include <yaml-cpp/yaml.h>

#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

using namespace OpenYAMM::Game;

namespace
{
ExitPose exitPoseTestPose()
{
    ExitPose pose;
    pose.worldId = "mm6";
    pose.mapFileName = "cal6d18.blv";
    pose.x = -1234.5f;
    pose.y = 2048.25f;
    pose.footZ = -64.0f;
    pose.yawRadians = 4.712f;
    pose.pitchDegrees = -12.5f;
    pose.headingYawUnits = 1536;
    return pose;
}

std::string readExitPoseFile(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);
    std::ostringstream text;
    text << file.rdbuf();
    return text.str();
}
}

TEST_CASE("the exit pose is the loc pose with its map and world, shaped as a pin's pose")
{
    const YAML::Node root = YAML::Load(serializeExitPose(exitPoseTestPose()));
    CHECK(root["format"].as<int>() == 1);
    CHECK(root["world"].as<std::string>() == "mm6");
    CHECK(root["map"].as<std::string>() == "cal6d18.blv");
    const YAML::Node pose = root["pose"];
    REQUIRE(pose["position"].IsSequence());
    CHECK(pose["position"][0].as<float>() == doctest::Approx(-1234.5f));
    CHECK(pose["position"][1].as<float>() == doctest::Approx(2048.25f));
    CHECK(pose["position"][2].as<float>() == doctest::Approx(-64.0f));
    CHECK(pose["yaw_radians"].as<float>() == doctest::Approx(4.712f));
    CHECK(pose["pitch_degrees"].as<float>() == doctest::Approx(-12.5f));
    CHECK(pose["heading_yaw_units"].as<int>() == 1536);
}

TEST_CASE("the exit pose file is written whole, its folder made, an older file replaced")
{
    const std::filesystem::path folder = std::filesystem::temp_directory_path() / "openyamm-exit-pose-test";
    std::filesystem::remove_all(folder);
    const std::filesystem::path path = folder / "play" / "exit_pose.yml";
    std::string error;
    REQUIRE_MESSAGE(writeExitPose(path, exitPoseTestPose(), error), error);
    CHECK(readExitPoseFile(path) == serializeExitPose(exitPoseTestPose()));
    CHECK_FALSE(std::filesystem::exists(folder / "play" / "exit_pose.yml.partial"));

    ExitPose moved = exitPoseTestPose();
    moved.mapFileName = "oute3.odm";
    REQUIRE_MESSAGE(writeExitPose(path, moved, error), error);
    CHECK(YAML::LoadFile(path.string())["map"].as<std::string>() == "oute3.odm");
    std::filesystem::remove_all(folder);
}

TEST_CASE("the start console file and the exit pose path are read but never persisted")
{
    const std::filesystem::path folder = std::filesystem::temp_directory_path() / "openyamm-exit-pose-settings-test";
    std::filesystem::remove_all(folder);
    std::filesystem::create_directories(folder);
    const std::filesystem::path path = folder / "settings.ini";
    {
        std::ofstream output(path);
        output << "[debug]\nstartup_console_file= /tmp/play/start.console \nexit_pose_path=/tmp/play/exit_pose.yml\n";
    }
    std::string error;
    const std::optional<GameSettings> settings = loadGameSettings(path, error);
    REQUIRE_MESSAGE(settings, error);
    CHECK(settings->startupConsoleFile == "/tmp/play/start.console");
    CHECK(settings->exitPosePath == "/tmp/play/exit_pose.yml");
    REQUIRE(saveGameSettings(path, *settings, error));
    const std::string saved = readExitPoseFile(path);
    CHECK(saved.find("startup_console_file") == std::string::npos);
    CHECK(saved.find("exit_pose_path") == std::string::npos);
    const std::optional<GameSettings> reloaded = loadGameSettings(path, error);
    REQUIRE(reloaded);
    CHECK(reloaded->startupConsoleFile.empty());
    CHECK(reloaded->exitPosePath.empty());
    std::filesystem::remove_all(folder);
}
