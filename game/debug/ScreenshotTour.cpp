#include "game/debug/ScreenshotTour.h"

#include "game/render/SkyClock.h"

#include <yaml-cpp/yaml.h>

#include <cmath>
#include <exception>
#include <limits>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
bool isFiniteFloat(const YAML::Node &node, float &value)
{
    if (!node || !node.IsScalar())
    {
        return false;
    }

    double parsed = 0.0;

    try
    {
        parsed = node.as<double>();
    }
    catch (const std::exception &)
    {
        return false;
    }

    if (!std::isfinite(parsed) || std::abs(parsed) > std::numeric_limits<float>::max())
    {
        return false;
    }

    value = static_cast<float>(parsed);
    return true;
}

bool isSafeShotName(const std::string &name)
{
    if (name.empty() || name.size() > 64)
    {
        return false;
    }

    for (const char character : name)
    {
        const bool allowed = (character >= 'a' && character <= 'z')
            || (character >= 'A' && character <= 'Z')
            || (character >= '0' && character <= '9')
            || character == '_'
            || character == '-';

        if (!allowed)
        {
            return false;
        }
    }

    return true;
}
}

std::optional<ScreenshotTour> loadScreenshotTour(const std::filesystem::path &tourPath, std::string &error)
{
    error.clear();
    YAML::Node root;

    try
    {
        root = YAML::LoadFile(tourPath.string());
    }
    catch (const std::exception &exception)
    {
        error = "failed to load screenshot tour: " + std::string(exception.what());
        return std::nullopt;
    }

    if (!root || !root.IsMap())
    {
        error = "screenshot tour must be a YAML map";
        return std::nullopt;
    }

    const YAML::Node shotsNode = root["shots"];

    if (!shotsNode || !shotsNode.IsSequence() || shotsNode.size() == 0)
    {
        error = "screenshot tour requires a non-empty 'shots' sequence";
        return std::nullopt;
    }

    ScreenshotTour tour = {};

    if (const YAML::Node outputNode = root["output_dir"]; outputNode)
    {
        if (!outputNode.IsScalar())
        {
            error = "screenshot tour 'output_dir' must be a directory path";
            return std::nullopt;
        }
        const std::string outputDirectory = outputNode.as<std::string>();

        if (outputDirectory.empty() || outputDirectory.front() == '-')
        {
            error = "screenshot tour 'output_dir' must be a non-empty directory path";
            return std::nullopt;
        }

        tour.outputDirectory = outputDirectory;
    }

    if (const YAML::Node exitNode = root["exit"]; exitNode)
    {
        try
        {
            tour.exitWhenFinished = exitNode.as<bool>();
        }
        catch (const std::exception &)
        {
            error = "screenshot tour 'exit' must be a boolean";
            return std::nullopt;
        }
    }

    if (const YAML::Node settleNode = root["settle_seconds"]; settleNode)
    {
        float settleSeconds = 0.0f;

        if (!isFiniteFloat(settleNode, settleSeconds) || settleSeconds < 0.0f || settleSeconds > 600.0f)
        {
            error = "screenshot tour 'settle_seconds' must be a finite value in [0, 600]";
            return std::nullopt;
        }

        tour.defaultSettleSeconds = settleSeconds;
    }

    size_t shotIndex = 0;

    for (const YAML::Node &shotNode : shotsNode)
    {
        ++shotIndex;

        if (!shotNode || !shotNode.IsMap())
        {
            error = "screenshot tour shot #" + std::to_string(shotIndex) + " must be a map";
            return std::nullopt;
        }

        ScreenshotTourShot shot = {};

        if (const YAML::Node nameNode = shotNode["name"]; nameNode && nameNode.IsScalar())
        {
            shot.name = nameNode.as<std::string>();
        }

        if (!isSafeShotName(shot.name))
        {
            error = "screenshot tour shot #" + std::to_string(shotIndex)
                + " requires a name of letters, digits, '_' or '-'";
            return std::nullopt;
        }

        const YAML::Node coordinatesNode = shotNode["position"];

        if (!coordinatesNode || !coordinatesNode.IsSequence() || coordinatesNode.size() != 3)
        {
            error = "screenshot tour shot '" + shot.name + "' requires position: [x, y, z]";
            return std::nullopt;
        }

        if (!isFiniteFloat(coordinatesNode[0], shot.x)
            || !isFiniteFloat(coordinatesNode[1], shot.y)
            || !isFiniteFloat(coordinatesNode[2], shot.z))
        {
            error = "screenshot tour shot '" + shot.name + "' has non-finite position coordinates";
            return std::nullopt;
        }

        if (const YAML::Node yawNode = shotNode["yaw"]; yawNode)
        {
            if (!isFiniteFloat(yawNode, shot.yawRadians))
            {
                error = "screenshot tour shot '" + shot.name + "' has a non-finite yaw";
                return std::nullopt;
            }
        }

        if (const YAML::Node pitchNode = shotNode["pitch"]; pitchNode)
        {
            if (!isFiniteFloat(pitchNode, shot.pitchRadians)
                || shot.pitchRadians < -1.553f || shot.pitchRadians > 1.553f)
            {
                error = "screenshot tour shot '" + shot.name + "' pitch must be finite within +-89 degrees";
                return std::nullopt;
            }
        }

        if (const YAML::Node settleNode = shotNode["settle_seconds"]; settleNode)
        {
            if (!isFiniteFloat(settleNode, shot.settleSeconds)
                || shot.settleSeconds < 0.0f
                || shot.settleSeconds > 600.0f)
            {
                error = "screenshot tour shot '" + shot.name + "' settle_seconds must be finite in [0, 600]";
                return std::nullopt;
            }
        }

        if (const YAML::Node timeNode = shotNode["time"]; timeNode)
        {
            shot.clockMinutes = timeNode.IsScalar() ? parseClockMinutes(timeNode.as<std::string>()) : std::nullopt;

            if (!shot.clockMinutes)
            {
                error = "screenshot tour shot '" + shot.name + "' time must be \"HH:MM\"";
                return std::nullopt;
            }
        }

        if (const YAML::Node commandsNode = shotNode["commands"]; commandsNode)
        {
            if (!commandsNode.IsSequence())
            {
                error = "screenshot tour shot '" + shot.name + "' commands must be a list of console lines";
                return std::nullopt;
            }

            for (const YAML::Node &commandNode : commandsNode)
            {
                if (!commandNode.IsScalar() || commandNode.as<std::string>().empty())
                {
                    error = "screenshot tour shot '" + shot.name + "' has an empty or non-text command";
                    return std::nullopt;
                }

                shot.commands.push_back(commandNode.as<std::string>());
            }
        }

        tour.shots.push_back(std::move(shot));
    }

    if (std::filesystem::path(tour.outputDirectory).is_relative())
    {
        tour.outputDirectory = (std::filesystem::absolute(tourPath).parent_path()
            / tour.outputDirectory).lexically_normal().string();
    }
    return tour;
}
}
