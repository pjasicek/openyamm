#pragma once

#include <array>
#include <cstdint>
#include <memory>
#include <vector>

namespace OpenYAMM::Engine
{
struct ModelAsset;
}

namespace OpenYAMM::Game
{
// A posed talking prop's model for its talk portrait (an MM9 RUDEProp drawn as a decoration, Sturmford City's
// innkeeper): the model its decoration shows now, its material variant, the yaw that turns its front to +X and the
// scale it is placed at (DecorationModelSet::portraitModel).
struct DecorationPortraitModel
{
    std::shared_ptr<const Engine::ModelAsset> asset;
    uint32_t materialVariant = 0;
    float yawOffset = 0.0f;
    float scale = 1.0f;
};

// The box a talk portrait frames, in the portrait's space (Z up), as eight corners: the head (its points, from the
// neck pivot to the crown), widened to the shoulders and lengthened down the chest, with a little room above the
// crown. headPoints must not be empty.
std::vector<std::array<float, 3>> talkPortraitHeadAndShoulders(const std::vector<std::array<float, 3>> &headPoints,
    float pivotZ);

// The same frame for a figure without head joints (a posed prop's static mesh): its head taken as the top
// TalkPortraitStaticHeadShare of its height, centred on the points there. Empty for no points.
std::vector<std::array<float, 3>> talkPortraitStaticFigureFrame(const std::vector<std::array<float, 3>> &points);

constexpr float TalkPortraitStaticHeadShare = 0.14f;
}
