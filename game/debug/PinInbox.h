#pragma once

#include <ctime>
#include <filesystem>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
// Pins from the game's debug console (`pin <text>`): one YAML file per pin in pins format 1, with the game's own
// screenshot of the same name beside it, written into an inbox folder that the Map Studio imports
// (devdocs/map_studio/S5_BROWSER_EDITOR.md 2.10 and 3.13).

// What the Map Studio's install writes beside a map it installed (`<stem>.studio.yml`): the project the map was built
// from, the source revision and the id lock's hash. The game copies them into each pin made on that map.
struct StudioMapInfo
{
    std::string project;
    std::string revision;
    std::string lockHash;
};

// A pin as the game makes it. The pose is the one `loc` prints, in the same units.
struct GamePin
{
    std::string text;
    std::string worldId;
    std::string mapFileName;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float yawRadians = 0.0f;
    float pitchDegrees = 0.0f;
    int headingYawUnits = 0;
    // Local time, 2026-11-20T10:12:05.
    std::string created;
    // The screenshot's file name, beside the pin file.
    std::string picture;
    std::optional<StudioMapInfo> studio;
};

// Reads a `<stem>.studio.yml`; nullopt with error when it is not a mapping with a non-empty `project`.
std::optional<StudioMapInfo> parseStudioMapFile(const std::string &yamlText, std::string &error);

// 2026-11-20T10:12:05
std::string pinTimestamp(const std::tm &localTime);

// <date>-<time>-<map stem>: 20261120-101205-6d01
std::string pinFileStem(const std::tm &localTime, const std::string &mapFileName);

// The pin file's text, pins format 1.
std::string serializeGamePin(const GamePin &pin);

// Writes <inbox>/<stem>.yml, creating the inbox; a stem already taken gets -2, -3 ... The pin's picture is set to the
// stem actually used plus .png. Returns the pin file's path, or nullopt with error.
std::optional<std::filesystem::path> writeGamePin(
    const std::filesystem::path &inbox,
    const std::string &stem,
    GamePin pin,
    std::string &error);
}
