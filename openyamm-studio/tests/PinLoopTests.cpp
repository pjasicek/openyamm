// S5a3, the pin loop in the browser (S5_BROWSER_EDITOR.md 6.4), the core's side: pins with pictures sent as bytes
// (the studio's screenshot) and replies with pictures, pins.keep, edit.history with times and undone entries,
// project.status naming a file that does not parse without recording it as an edit, provenance on every face of an
// indoor view (objects as well as rooms), mesh files named by their bytes, and two reads in one process that keep
// their own names (openTarget's state per call).
#include "doctest/doctest.h"

#include "cli/Rpc.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <random>
#include <set>
#include <string>

using namespace OpenYAMM::Studio;

namespace
{
const std::filesystem::path StudioRoot = std::filesystem::path(__FILE__).parent_path().parent_path();

std::filesystem::path copyExample(const std::string &example)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path()
        / ("oymap_s5a3_pins_" + example + "_" + std::to_string(std::random_device{}()));
    std::filesystem::create_directories(root);

    for (const std::filesystem::directory_entry &entry :
         std::filesystem::directory_iterator(StudioRoot / "examples" / example))
    {
        if (entry.is_regular_file())
        {
            std::filesystem::copy_file(entry.path(), root / entry.path().filename());
        }
    }

    return root;
}

YAML::Node call(const std::string &method, const std::string &params)
{
    return YAML::Load(callRpcMethod(method, params));
}

std::string quoted(const std::filesystem::path &path)
{
    return "\"" + path.string() + "\"";
}

std::string kindOf(const YAML::Node &answer)
{
    return answer["error"] ? answer["error"]["data"]["kind"].Scalar() : std::string("result");
}

std::string readBytes(const std::filesystem::path &path)
{
    std::ifstream stream(path, std::ios::binary);
    return std::string(std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>());
}

std::string base64(const std::string &bytes)
{
    static const char *pAlphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string text;

    for (size_t index = 0; index < bytes.size(); index += 3)
    {
        uint32_t group = static_cast<uint32_t>(static_cast<unsigned char>(bytes[index])) << 16;
        const size_t left = bytes.size() - index;

        if (left > 1)
        {
            group |= static_cast<uint32_t>(static_cast<unsigned char>(bytes[index + 1])) << 8;
        }

        if (left > 2)
        {
            group |= static_cast<uint32_t>(static_cast<unsigned char>(bytes[index + 2]));
        }

        text += pAlphabet[(group >> 18) & 63];
        text += pAlphabet[(group >> 12) & 63];
        text += left > 1 ? pAlphabet[(group >> 6) & 63] : '=';
        text += left > 2 ? pAlphabet[group & 63] : '=';
    }

    return text;
}

// The smallest picture each kind checks: the PNG signature with a few bytes after it, a JPEG's start.
const std::string PngBytes = std::string("\x89PNG\r\n\x1a\n", 8) + std::string("\0\0\0\rIHDR", 8) + "rest";
const std::string JpegBytes = std::string("\xff\xd8\xff\xe0", 4) + "JFIF";

std::string pictureParam(const std::string &mediaType, const std::string &bytes)
{
    return "{\"media_type\":\"" + mediaType + "\",\"base64\":\"" + base64(bytes) + "\"}";
}

void configureAssets()
{
    const std::filesystem::path assets = StudioRoot.parent_path() / "assets_dev";

    if (std::filesystem::is_directory(assets / "engine"))
    {
        callRpcMethod("session.configure", "{\"asset_root\":" + quoted(assets) + "}");
    }
}
}

TEST_CASE("S5a3: a pin from the studio carries its picture as bytes; replies carry theirs; pins.keep keeps one")
{
    const std::filesystem::path project = copyExample("gatehouse_cellars");
    const YAML::Node added = call("pins.add", "{\"project\":" + quoted(project) + ",\"text\":\"Too dark.\",\"on\":"
        "\"room:hall\",\"file\":\"rooms.yml\",\"at\":[100,200,0],\"author\":\"user\",\"source\":\"studio\","
        "\"pose\":{\"position\":[1,2,3],\"yaw_radians\":1.5708,\"pitch_degrees\":-10},\"picture\":"
        + pictureParam("image/jpeg", JpegBytes) + "}");
    REQUIRE(kindOf(added) == "result");
    const YAML::Node pin = added["result"]["pin"];
    CHECK(pin["picture"].Scalar() == ".oymap/pins/pictures/p1.jpg");
    CHECK(readBytes(project / ".oymap/pins/pictures/p1.jpg") == JpegBytes);
    CHECK(pin["source"].Scalar() == "studio");
    // The id is in rooms.yml only (plan.yml has no room:hall here): the file is not written beside it.
    CHECK(pin["on"].Scalar() == "room:hall");
    CHECK(pin["pose"]["yaw_radians"].as<double>() == doctest::Approx(1.5708));

    const YAML::Node replied = call("pins.resolve", "{\"project\":" + quoted(project) + ",\"pin\":\"pin:p1\",\"by\":"
        "\"agent:test\",\"text\":\"Brighter.\",\"pictures\":[" + pictureParam("image/png", PngBytes) + ","
        + pictureParam("image/png", PngBytes) + "]}");
    REQUIRE(kindOf(replied) == "result");
    const YAML::Node reply = replied["result"]["pin"]["replies"][0];
    CHECK(reply["pictures"][0].Scalar() == ".oymap/pins/pictures/p1-r1.png");
    CHECK(reply["pictures"][1].Scalar() == ".oymap/pins/pictures/p1-r1-2.png");
    CHECK(readBytes(project / ".oymap/pins/pictures/p1-r1-2.png") == PngBytes);
    CHECK(replied["result"]["pin"]["status"].Scalar() == "resolved");

    // Not a picture, not base64: refused, and nothing is written.
    const int counter = replied["result"]["counter"].as<int>();
    CHECK(kindOf(call("pins.add", "{\"project\":" + quoted(project) + ",\"text\":\"x\",\"picture\":"
        + pictureParam("image/png", "GIF89a....") + "}")) == "bad_request");
    CHECK(kindOf(call("pins.add", "{\"project\":" + quoted(project)
        + ",\"text\":\"x\",\"picture\":{\"media_type\":\"image/png\",\"base64\":\"%%%%\"}}")) == "bad_request");
    CHECK(kindOf(call("pins.add", "{\"project\":" + quoted(project)
        + ",\"text\":\"x\",\"picture\":{\"media_type\":\"image/gif\",\"base64\":\"AAAA\"}}")) == "invalid_params");
    CHECK(call("pins.list", "{\"project\":" + quoted(project) + "}")["result"]["counter"].as<int>() == counter);

    const YAML::Node kept = call("pins.keep", "{\"project\":" + quoted(project) + ",\"pin\":\"pin:p1\"}");
    REQUIRE(kindOf(kept) == "result");
    CHECK(kept["result"]["pin"]["picture"].Scalar() == "review/pictures/p1.jpg");
    CHECK(kept["result"]["pin"]["keep"].as<bool>());
    CHECK(readBytes(project / "review/pictures/p1.jpg") == JpegBytes);
    CHECK(kindOf(call("pins.keep", "{\"project\":" + quoted(project) + ",\"pin\":\"pin:p9\"}")) == "no_such_pin");
    std::filesystem::remove_all(project);
}

TEST_CASE("S5a3: edit.history lists entries with author, label, time and undone; a file that does not parse is not "
          "recorded as an edit")
{
    configureAssets();
    const std::filesystem::path project = copyExample("gatehouse_cellars");
    const std::string at = "{\"project\":" + quoted(project) + "}";
    REQUIRE(kindOf(call("project.status", at)) == "result");
    const YAML::Node edited = call("edit.apply", "{\"project\":" + quoted(project) + ",\"ops\":[{\"op\":\"set\",\"id\":"
        "\"light:entry\",\"fields\":{\"radius\":950}}],\"author\":\"agent:test\",\"label\":\"brighter entry\"}");
    REQUIRE(kindOf(edited) == "result");

    YAML::Node history = call("edit.history", at);
    REQUIRE(kindOf(history) == "result");
    YAML::Node last = history["result"]["entries"][history["result"]["entries"].size() - 1];
    CHECK(last["author"].Scalar() == "agent:test");
    CHECK(last["label"].Scalar() == "brighter entry");
    CHECK(last["kind"].Scalar() == "transaction");
    CHECK(last["time"].Scalar().size() == 19);
    CHECK_FALSE(last["undone"].as<bool>());
    CHECK(last["changes"][0].Scalar().find("light:entry") != std::string::npos);
    const int count = history["result"]["count"].as<int>();

    // The undo is an entry of its own that reverts the edit (S5b1): the edit shows as undone.
    const int editSequence = last["sequence"].as<int>();
    REQUIRE(kindOf(call("edit.undo", at)) == "result");
    history = call("edit.history", at);
    last = history["result"]["entries"][history["result"]["entries"].size() - 1];
    const YAML::Node undoneEdit = history["result"]["entries"][history["result"]["entries"].size() - 2];
    CHECK_FALSE(last["undone"].as<bool>());
    CHECK(last["reverts"].as<int>() == editSequence);
    CHECK(undoneEdit["sequence"].as<int>() == editSequence);
    CHECK(undoneEdit["undone"].as<bool>());
    CHECK(call("edit.history", "{\"project\":" + quoted(project) + ",\"limit\":1}")["result"]["entries"].size() == 1);

    // A half-written file: reported, the revision kept, no entry; once it parses again, nothing was recorded.
    const std::string revision = call("project.status", at)["result"]["revision"].Scalar();
    const std::string wiring = readBytes(project / "wiring.yml");
    std::ofstream(project / "wiring.yml", std::ios::binary) << wiring << "\n  - [unclosed\n";
    const YAML::Node broken = call("project.status", at);
    REQUIRE(kindOf(broken) == "result");
    CHECK(broken["result"]["unreadable"][0]["file"].Scalar() == "wiring.yml");
    CHECK(broken["result"]["revision"].Scalar() == revision);
    CHECK(broken["result"]["outside_changes"].size() == 0);
    std::ofstream(project / "wiring.yml", std::ios::binary) << wiring;
    const YAML::Node mended = call("project.status", at);
    CHECK_FALSE(mended["result"]["unreadable"]);
    CHECK(mended["result"]["revision"].Scalar() == revision);
    CHECK(call("edit.history", at)["result"]["count"].as<int>() == count + 1);
    std::filesystem::remove_all(project);
}

TEST_CASE("S5a3: every face of an indoor view has its owner: rooms, walls, doors, and the objects of objects.yml")
{
    configureAssets();
    const std::filesystem::path project = copyExample("gatehouse_cellars");
    const YAML::Node mesh = call("view.mesh", "{\"project\":" + quoted(project) + "}");
    REQUIRE(kindOf(mesh) == "result");
    const YAML::Node result = mesh["result"];
    const std::string bytes = readBytes(project / result["file"].Scalar());
    REQUIRE(bytes.size() == result["bytes"].as<size_t>());
    // Named by its bytes too: <revision>-<lock>-<12 digits of the bytes' hash>.mesh.
    const std::string name = std::filesystem::path(result["file"].Scalar()).filename().string();
    CHECK(std::count(name.begin(), name.end(), '-') == 2);

    const size_t offset = result["sections"]["face_owners"]["offset"].as<size_t>();
    const size_t faces = result["sections"]["face_owners"]["count"].as<size_t>();
    REQUIRE(faces > 0);
    std::set<std::string> kinds;
    size_t owned = 0;

    for (size_t face = 0; face < faces; ++face)
    {
        uint32_t owner = 0;
        std::memcpy(&owner, bytes.data() + offset + face * 4, 4);
        const std::string id = result["owners"][owner]["id"].Scalar();
        owned += id.empty() ? 0 : 1;

        if (!id.empty())
        {
            kinds.insert(id.substr(0, id.find(':')));
            const std::string file = result["owners"][owner]["file"] ? result["owners"][owner]["file"].Scalar() : "";
            CHECK(file == (id.rfind("room:", 0) == 0 || id.rfind("open:", 0) == 0 ? "rooms.yml" : "objects.yml"));
        }
    }

    CHECK(owned == faces);
    CHECK(kinds.contains("room"));
    CHECK(kinds.contains("door"));
    CHECK(kinds.contains("chest"));
    CHECK(kinds.contains("switch"));
    std::filesystem::remove_all(project);
}

TEST_CASE("S5a3: two reads in one process keep their own names (openTarget's state is the call's)")
{
    configureAssets();
    const std::filesystem::path first = copyExample("gatehouse_cellars");
    const std::filesystem::path second = copyExample("goblinwatch_vault");
    const YAML::Node solvedFirst = call("check.solve", "{\"map\":" + quoted(first) + "}");
    const YAML::Node solvedSecond = call("check.solve", "{\"map\":" + quoted(second) + "}");
    REQUIRE(kindOf(solvedFirst) == "result");
    REQUIRE(kindOf(solvedSecond) == "result");
    const YAML::Node again = call("check.solve", "{\"map\":" + quoted(first) + "}");
    REQUIRE(kindOf(again) == "result");
    CHECK(YAML::Dump(again["result"]["sector_rooms"]) == YAML::Dump(solvedFirst["result"]["sector_rooms"]));
    CHECK(YAML::Dump(solvedSecond["result"]["sector_rooms"]) != YAML::Dump(solvedFirst["result"]["sector_rooms"]));
    std::filesystem::remove_all(first);
    std::filesystem::remove_all(second);
}
