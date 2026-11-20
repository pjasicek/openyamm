#pragma once

#include <filesystem>
#include <string>

namespace OpenYAMM::Game
{
// Where the party stood when the game closed ([debug] exit_pose_path, a launch directive): written on exit so that
// the Map Studio, which started the game with Play here, moves its camera there (devdocs/map_studio/
// S5_BROWSER_EDITOR.md 2.10, D13). The pose is the one the console's `loc` prints, in the same units, with the map
// and its world.
struct ExitPose
{
    std::string worldId;
    std::string mapFileName;
    float x = 0.0f;
    float y = 0.0f;
    float footZ = 0.0f;
    float yawRadians = 0.0f;
    float pitchDegrees = 0.0f;
    int headingYawUnits = 0;
};

// The file's text: format 1, world, map and a `pose` block shaped as a pin's (pins format 1).
std::string serializeExitPose(const ExitPose &pose);

// Writes the file whole under another name first and renames it over the path, so a watcher never reads half of it;
// creates the folder. False with error when it cannot.
bool writeExitPose(const std::filesystem::path &path, const ExitPose &pose, std::string &error);
}
