#include "doctest/doctest.h"

#include "engine/DisplayModes.h"

#include <vector>

using namespace OpenYAMM::Engine;

namespace
{
// Part of what a 16-inch MacBook Pro (3456x2234 panel) lists with its desktop at 1496x967 points.
const std::vector<DisplayModeSize> MacModes = {
    {3456, 2234, 1.0f, 120.0f},
    {3456, 2234, 1.0f, 60.0f},
    {2992, 1934, 1.0f, 120.0f},
    {1920, 1200, 1.0f, 120.0f},
    {2056, 1329, 2.0f, 120.0f},
    {1728, 1117, 2.0f, 120.0f},
    {1728, 1117, 2.0f, 60.0f},
    {1496, 967, 2.0f, 120.0f},
    {960, 600, 2.0f, 120.0f},
};
const DisplayModeSize MacDesktop = {1496, 967, 2.0f, 120.0f};
}

TEST_CASE("a display mode renders its pixels only in a high pixel density window")
{
    CHECK(displayModeRenderSize({1728, 1117, 2.0f, 120.0f}, true) == RenderSize{3456, 2234});
    CHECK(displayModeRenderSize({1728, 1117, 2.0f, 120.0f}, false) == RenderSize{1728, 1117});
    CHECK(displayModeRenderSize({1920, 1080, 1.0f, 60.0f}, true) == RenderSize{1920, 1080});
}

TEST_CASE("a Retina fullscreen size picks the mode nearest the desktop's size in points")
{
    // The panel's pixels: 1728x1117 at 2x, whose cursor looks and moves as on the desktop, not 3456x2234 at 1x.
    CHECK(findDisplayModeForRenderSize(MacModes, {3456, 2234}, MacDesktop, true) == 5);
    // The desktop's own pixels pick the desktop mode.
    CHECK(findDisplayModeForRenderSize(MacModes, {2992, 1934}, MacDesktop, true) == 7);
    // 1920x1200 points at 1x is nearer the desktop than 960x600 at 2x.
    CHECK(findDisplayModeForRenderSize(MacModes, {1920, 1200}, MacDesktop, true) == 3);
    CHECK(findDisplayModeForRenderSize(MacModes, {4112, 2658}, MacDesktop, true) == 4);
    // No mode renders a size in points of a 2x mode.
    CHECK_FALSE(findDisplayModeForRenderSize(MacModes, {1728, 1117}, MacDesktop, true));
}

TEST_CASE("a fullscreen size picks the refresh rate nearest the desktop's")
{
    const DisplayModeSize desktopAt60 = {1496, 967, 2.0f, 60.0f};
    CHECK(findDisplayModeForRenderSize(MacModes, {3456, 2234}, desktopAt60, true) == 6);
    CHECK(findDisplayModeForRenderSize(MacModes, {3456, 2234}, MacDesktop, false) == 0);
    CHECK(findDisplayModeForRenderSize(MacModes, {3456, 2234}, desktopAt60, false) == 1);
}

TEST_CASE("without high pixel density a fullscreen size is a mode's listed size")
{
    CHECK(findDisplayModeForRenderSize(MacModes, {1728, 1117}, MacDesktop, false) == 5);
    CHECK_FALSE(findDisplayModeForRenderSize(MacModes, {2560, 1440}, MacDesktop, false));
}
