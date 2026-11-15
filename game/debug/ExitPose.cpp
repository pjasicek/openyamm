#include "game/debug/ExitPose.h"

#include <fstream>
#include <iomanip>
#include <sstream>
#include <system_error>

namespace OpenYAMM::Game
{
namespace
{
// A YAML double-quoted scalar of a map or world name.
std::string quoted(const std::string &text)
{
    std::string result = "\"";

    for (const char character : text)
    {
        if (character == '"' || character == '\\')
        {
            result.push_back('\\');
        }

        result.push_back(character);
    }

    result.push_back('"');
    return result;
}
}

std::string serializeExitPose(const ExitPose &pose)
{
    std::ostringstream out;
    out << std::fixed << std::setprecision(3);
    out << "# Where the party stood when the game closed ([debug] exit_pose_path); the pose as `loc` prints it.\n"
        << "format: 1\n"
        << "world: " << quoted(pose.worldId) << '\n'
        << "map: " << quoted(pose.mapFileName) << '\n'
        << "pose:\n"
        << "  position: [" << pose.x << ", " << pose.y << ", " << pose.footZ << "]\n"
        << "  yaw_radians: " << pose.yawRadians << '\n'
        << "  pitch_degrees: " << pose.pitchDegrees << '\n'
        << "  heading_yaw_units: " << pose.headingYawUnits << '\n';
    return out.str();
}

bool writeExitPose(const std::filesystem::path &path, const ExitPose &pose, std::string &error)
{
    std::error_code fileError;

    if (path.has_parent_path())
    {
        std::filesystem::create_directories(path.parent_path(), fileError);

        if (fileError)
        {
            error = "cannot create " + path.parent_path().string() + ": " + fileError.message();
            return false;
        }
    }

    std::filesystem::path partialPath = path;
    partialPath += ".partial";

    {
        std::ofstream file(partialPath, std::ios::binary);
        file << serializeExitPose(pose);

        if (!file)
        {
            error = "cannot write " + partialPath.string();
            return false;
        }
    }

    std::filesystem::rename(partialPath, path, fileError);

    if (fileError)
    {
        error = "cannot write " + path.string() + ": " + fileError.message();
        return false;
    }

    return true;
}
}
