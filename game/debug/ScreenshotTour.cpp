#include "game/debug/ScreenshotTour.h"

#include <yaml-cpp/yaml.h>

#include <cmath>
#include <exception>

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

    if (!std::isfinite(parsed))
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

    if (const YAML::Node outputNode = root["output_dir"]; outputNode && outputNode.IsScalar())
    {
        const std::string outputDirectory = outputNode.as<std::string>();

        if (outputDirectory.empty() || outputDirectory.front() == '-')
        {
            error = "screenshot tour 'output_dir' must be a non-empty directory path";
            return std::nullopt;
        }

        tour.outputDirectory = outputDirectory;
    }

    if (const YAML::Node exitNode = root["exit"]; exitNode && exitNode.IsScalar())
    {
        tour.exitWhenFinished = exitNode.as<bool>(false);
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
            if (!isFiniteFloat(pitchNode, shot.pitchRadians) || shot.pitchRadians < -1.553f || shot.pitchRadians > 1.553f)
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

        tour.shots.push_back(std::move(shot));
    }

    return tour;
}
}
