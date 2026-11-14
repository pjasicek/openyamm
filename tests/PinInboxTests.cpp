#include "doctest/doctest.h"

#include "game/app/GameSettings.h"
#include "game/debug/PinInbox.h"

#include <yaml-cpp/yaml.h>

#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

using namespace OpenYAMM::Game;

namespace
{
std::tm pinTestTime()
{
    std::tm time = {};
    time.tm_year = 2026 - 1900;
    time.tm_mon = 10;
    time.tm_mday = 20;
    time.tm_hour = 10;
    time.tm_min = 12;
    time.tm_sec = 5;
    return time;
}

GamePin pinTestPin()
{
    GamePin pin;
    pin.text = "the gate leaf: \"flickers\" # at C:\\jamb";
    pin.worldId = "mm6";
    pin.mapFileName = "6d01.blv";
    pin.x = 2816.0f;
    pin.y = 2048.5f;
    pin.z = -380.0f;
    pin.yawRadians = 1.571f;
    pin.pitchDegrees = -3.0f;
    pin.headingYawUnits = 512;
    pin.created = pinTimestamp(pinTestTime());
    return pin;
}

std::string readWholeFile(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);
    std::ostringstream text;
    text << file.rdbuf();
    return text.str();
}
}

TEST_CASE("pin names and timestamps follow the inbox convention")
{
    CHECK(pinTimestamp(pinTestTime()) == "2026-11-20T10:12:05");
    CHECK(pinFileStem(pinTestTime(), "6d01.blv") == "20261120-101205-6d01");
    CHECK(pinFileStem(pinTestTime(), "") == "20261120-101205");
}

TEST_CASE("pin file is pins format 1 and reads back as written")
{
    GamePin pin = pinTestPin();
    pin.picture = "20261120-101205-6d01.png";
    pin.studio = StudioMapInfo{"/home/user/briefs/mm6_6d01/L4", "7c1e0a", ""};

    const YAML::Node root = YAML::Load(serializeGamePin(pin));
    CHECK(root["format"].as<int>() == 1);
    CHECK(root["source"].as<std::string>() == "game");
    CHECK(root["author"].as<std::string>() == "user");
    CHECK(root["created"].as<std::string>() == "2026-11-20T10:12:05");
    CHECK(root["text"].as<std::string>() == pin.text);
    CHECK(root["world"].as<std::string>() == "mm6");
    CHECK(root["map"].as<std::string>() == "6d01.blv");
    REQUIRE(root["pose"]["position"].size() == 3);
    CHECK(root["pose"]["position"][1].as<float>() == doctest::Approx(2048.5f));
    CHECK(root["pose"]["yaw_radians"].as<float>() == doctest::Approx(1.571f));
    CHECK(root["pose"]["pitch_degrees"].as<float>() == doctest::Approx(-3.0f));
    CHECK(root["pose"]["heading_yaw_units"].as<int>() == 512);
    CHECK(root["picture"].as<std::string>() == "20261120-101205-6d01.png");
    CHECK(root["project"].as<std::string>() == "/home/user/briefs/mm6_6d01/L4");
    CHECK(root["revision"].as<std::string>() == "7c1e0a");
    CHECK_FALSE(root["lock_hash"]);

    // Text that YAML would read as another type stays a string; control characters are escaped.
    pin.text = "42";
    pin.studio.reset();
    YAML::Node plain = YAML::Load(serializeGamePin(pin));
    CHECK(plain["text"].Tag() == "!");
    CHECK(plain["text"].as<std::string>() == "42");
    CHECK_FALSE(plain["project"]);
    pin.text = "line\tone\x01";
    CHECK(YAML::Load(serializeGamePin(pin))["text"].as<std::string>() == "line\tone\x01");
}

TEST_CASE("pin writer creates the inbox and never overwrites a pin")
{
    const std::filesystem::path inbox = std::filesystem::temp_directory_path() / "openyamm-pin-inbox-test";
    std::filesystem::remove_all(inbox);

    std::string error;
    const std::optional<std::filesystem::path> first =
        writeGamePin(inbox, "20261120-101205-6d01", pinTestPin(), error);
    REQUIRE(first);
    CHECK(*first == inbox / "20261120-101205-6d01.yml");
    CHECK(YAML::Load(readWholeFile(*first))["picture"].as<std::string>() == "20261120-101205-6d01.png");

    const std::optional<std::filesystem::path> second =
        writeGamePin(inbox, "20261120-101205-6d01", pinTestPin(), error);
    REQUIRE(second);
    CHECK(*second == inbox / "20261120-101205-6d01-2.yml");
    CHECK(YAML::Load(readWholeFile(*second))["picture"].as<std::string>() == "20261120-101205-6d01-2.png");
    CHECK_FALSE(std::filesystem::exists(inbox / "20261120-101205-6d01.yml.partial"));

    // A picture already there (a pin file removed by hand) also takes the name.
    std::ofstream(inbox / "20261120-101206-6d01.png") << "png";
    const std::optional<std::filesystem::path> third =
        writeGamePin(inbox, "20261120-101206-6d01", pinTestPin(), error);
    REQUIRE(third);
    CHECK(*third == inbox / "20261120-101206-6d01-2.yml");

    std::filesystem::remove_all(inbox);
}

TEST_CASE("studio map file gives the project, revision and lock hash")
{
    std::string error;
    const std::optional<StudioMapInfo> info = parseStudioMapFile(
        "project: /home/user/briefs/mm6_6d01/L4\nrevision: 7c1e0a\nlock_hash: 99ab\n", error);
    REQUIRE(info);
    CHECK(info->project == "/home/user/briefs/mm6_6d01/L4");
    CHECK(info->revision == "7c1e0a");
    CHECK(info->lockHash == "99ab");

    CHECK_FALSE(parseStudioMapFile("revision: 7c1e0a\n", error));
    CHECK(error == "no project");
    CHECK_FALSE(parseStudioMapFile("- a list\n", error));
    CHECK_FALSE(parseStudioMapFile("project: [unclosed\n", error));
}

TEST_CASE("pin inbox setting defaults to pins_inbox and persists")
{
    CHECK(GameSettings{}.pinInboxPath == "pins_inbox");

    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-pin-inbox-settings-test.ini";
    {
        std::ofstream output(path);
        output << "[debug]\npin_inbox_path=/data/pins\n";
    }

    std::string error;
    const std::optional<GameSettings> settings = loadGameSettings(path, error);
    REQUIRE(settings);
    CHECK(settings->pinInboxPath == "/data/pins");
    REQUIRE(saveGameSettings(path, *settings, error));
    const std::optional<GameSettings> reloaded = loadGameSettings(path, error);
    REQUIRE(reloaded);
    CHECK(reloaded->pinInboxPath == "/data/pins");
    std::filesystem::remove(path);
}
