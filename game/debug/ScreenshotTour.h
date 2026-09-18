#pragma once

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct ScreenshotTourShot
{
    std::string name;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float yawRadians = 0.0f;
    float pitchRadians = 0.0f;
    float settleSeconds = -1.0f; // Negative falls back to the tour default.
};

struct ScreenshotTour
{
    std::string outputDirectory = "output/screenshots/tour";
    float defaultSettleSeconds = 1.5f;
    bool exitWhenFinished = false;
    std::vector<ScreenshotTourShot> shots;
};

std::optional<ScreenshotTour> loadScreenshotTour(const std::filesystem::path &tourPath, std::string &error);
}
