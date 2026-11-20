#include "game/debug/PinInbox.h"

#include <yaml-cpp/yaml.h>

#include <cstdio>
#include <exception>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <system_error>

namespace OpenYAMM::Game
{
namespace
{
// A YAML double-quoted scalar: always a string, whatever the text looks like (a number, "yes", a colon, a '#').
std::string quoted(const std::string &text)
{
    std::string result = "\"";

    for (const char character : text)
    {
        const unsigned char byte = static_cast<unsigned char>(character);

        if (character == '"' || character == '\\')
        {
            result.push_back('\\');
            result.push_back(character);
        }
        else if (character == '\n')
        {
            result += "\\n";
        }
        else if (character == '\t')
        {
            result += "\\t";
        }
        else if (byte < 0x20 || byte == 0x7f)
        {
            char escaped[8] = {};
            std::snprintf(escaped, sizeof(escaped), "\\x%02X", byte);
            result += escaped;
        }
        else
        {
            result.push_back(character);
        }
    }

    result.push_back('"');
    return result;
}

std::string scalarOrEmpty(const YAML::Node &node)
{
    return node && node.IsScalar() ? node.Scalar() : std::string();
}
}

std::optional<StudioMapInfo> parseStudioMapFile(const std::string &yamlText, std::string &error)
{
    YAML::Node root;

    try
    {
        root = YAML::Load(yamlText);
    }
    catch (const std::exception &exception)
    {
        error = std::string("not YAML: ") + exception.what();
        return std::nullopt;
    }

    if (!root.IsMap())
    {
        error = "not a mapping";
        return std::nullopt;
    }

    StudioMapInfo info;
    info.project = scalarOrEmpty(root["project"]);
    info.revision = scalarOrEmpty(root["revision"]);
    info.lockHash = scalarOrEmpty(root["lock_hash"]);

    if (info.project.empty())
    {
        error = "no project";
        return std::nullopt;
    }

    return info;
}

std::string pinTimestamp(const std::tm &localTime)
{
    char text[32] = {};
    std::strftime(text, sizeof(text), "%Y-%m-%dT%H:%M:%S", &localTime);
    return text;
}

std::string pinFileStem(const std::tm &localTime, const std::string &mapFileName)
{
    char text[32] = {};
    std::strftime(text, sizeof(text), "%Y%m%d-%H%M%S", &localTime);
    const std::string mapStem = std::filesystem::path(mapFileName).stem().string();
    return mapStem.empty() ? std::string(text) : std::string(text) + "-" + mapStem;
}

std::string serializeGamePin(const GamePin &pin)
{
    std::ostringstream out;
    out << std::fixed << std::setprecision(3);
    out << "# A pin from the game's console (`pin <text>`); `oymap pins import <inbox>` files it into its project.\n"
        << "format: 1\n"
        << "source: game\n"
        << "author: user\n"
        << "created: " << quoted(pin.created) << '\n'
        << "text: " << quoted(pin.text) << '\n'
        << "world: " << quoted(pin.worldId) << '\n'
        << "map: " << quoted(pin.mapFileName) << '\n'
        << "pose:\n"
        << "  position: [" << pin.x << ", " << pin.y << ", " << pin.z << "]\n"
        << "  yaw_radians: " << pin.yawRadians << '\n'
        << "  pitch_degrees: " << pin.pitchDegrees << '\n'
        << "  heading_yaw_units: " << pin.headingYawUnits << '\n'
        << "picture: " << quoted(pin.picture) << '\n';

    if (pin.studio)
    {
        out << "project: " << quoted(pin.studio->project) << '\n';

        if (!pin.studio->revision.empty())
        {
            out << "revision: " << quoted(pin.studio->revision) << '\n';
        }

        if (!pin.studio->lockHash.empty())
        {
            out << "lock_hash: " << quoted(pin.studio->lockHash) << '\n';
        }
    }

    return out.str();
}

std::optional<std::filesystem::path> writeGamePin(
    const std::filesystem::path &inbox,
    const std::string &stem,
    GamePin pin,
    std::string &error)
{
    std::error_code fileError;
    std::filesystem::create_directories(inbox, fileError);

    if (fileError)
    {
        error = "cannot create " + inbox.string() + ": " + fileError.message();
        return std::nullopt;
    }

    std::string usedStem = stem;

    for (int suffix = 2; std::filesystem::exists(inbox / (usedStem + ".yml"))
         || std::filesystem::exists(inbox / (usedStem + ".png")); ++suffix)
    {
        if (suffix > 999)
        {
            error = "no free name for " + stem + " in " + inbox.string();
            return std::nullopt;
        }

        usedStem = stem + "-" + std::to_string(suffix);
    }

    pin.picture = usedStem + ".png";
    const std::filesystem::path path = inbox / (usedStem + ".yml");
    // Written whole under another name first, so an importer never reads half a pin.
    const std::filesystem::path partialPath = inbox / (usedStem + ".yml.partial");

    {
        std::ofstream file(partialPath, std::ios::binary);
        file << serializeGamePin(pin);

        if (!file)
        {
            error = "cannot write " + partialPath.string();
            return std::nullopt;
        }
    }

    std::filesystem::rename(partialPath, path, fileError);

    if (fileError)
    {
        error = "cannot write " + path.string() + ": " + fileError.message();
        return std::nullopt;
    }

    return path;
}
}
