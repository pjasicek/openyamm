#pragma once

#include "game/maps/MapPresentation.h"
#include "game/ui/GameplayOverlayTypes.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
struct GameplayMinimapPoint
{
    float x = 0.0f;
    float y = 0.0f;
};

inline bool applyMapPresentationToMinimapState(
    const MapPresentation &presentation,
    float partyZ,
    GameplayMinimapState &state)
{
    const MapPresentationVariant *pVariant = resolveMapPresentationVariant(presentation, partyZ);

    if (pVariant == nullptr)
    {
        return false;
    }

    state.textureName = pVariant->textureName;
    state.vectorBackground = false;
    state.zoomWidth = static_cast<float>(pVariant->pixelWidth);
    state.zoomHeight = static_cast<float>(pVariant->pixelHeight);
    state.worldMinX = presentation.worldMinX;
    state.worldMaxX = presentation.worldMaxX;
    state.worldMinY = presentation.worldMinY;
    state.worldMaxY = presentation.worldMaxY;
    state.flipU = presentation.flipU;
    state.flipV = presentation.flipV;
    state.revealEntireMap = presentation.revealEntireMap;
    return true;
}

inline GameplayMinimapPoint gameplayMinimapWorldToUv(
    const GameplayMinimapState &state,
    float worldX,
    float worldY)
{
    const float worldWidth = std::max(state.worldMaxX - state.worldMinX, 0.000001f);
    const float worldHeight = std::max(state.worldMaxY - state.worldMinY, 0.000001f);
    float u = (worldX - state.worldMinX) / worldWidth;
    float v = (worldY - state.worldMinY) / worldHeight;

    if (state.flipU)
    {
        u = 1.0f - u;
    }

    if (state.flipV)
    {
        v = 1.0f - v;
    }

    return {std::clamp(u, 0.0f, 1.0f), std::clamp(v, 0.0f, 1.0f)};
}

// The party heading as it appears on the map image, in the convention of the MAPDIR arrows (+X right, +Y up).
// Mirrors the image flips the position goes through, so a flipped map (MM9 exteriors are drawn rotated 180 degrees)
// shows the arrow pointing where the party walks.
inline float gameplayMinimapDisplayYaw(const GameplayMinimapState &state, float worldYawRadians)
{
    const float screenRight = std::cos(worldYawRadians) * (state.flipU ? -1.0f : 1.0f);
    const float screenUp = std::sin(worldYawRadians) * (state.flipV ? 1.0f : -1.0f);
    return std::atan2(screenUp, screenRight);
}

inline GameplayMinimapPoint gameplayMinimapUvToWorld(
    const GameplayMinimapState &state,
    float u,
    float v)
{
    if (state.flipU)
    {
        u = 1.0f - u;
    }

    if (state.flipV)
    {
        v = 1.0f - v;
    }

    return {
        state.worldMinX + u * (state.worldMaxX - state.worldMinX),
        state.worldMinY + v * (state.worldMaxY - state.worldMinY)
    };
}

inline GameplayMinimapPoint gameplayMinimapUvToOutdoorRevealUv(
    const GameplayMinimapState &state,
    float u,
    float v)
{
    // Saved outdoor exploration always uses the native +/-32768 world extent,
    // independently of the presentation image's crop, aspect ratio or flips.
    const GameplayMinimapPoint world = gameplayMinimapUvToWorld(state, u, v);
    return {
        std::clamp((world.x + 32768.0f) / 65536.0f, 0.0f, 0.999999f),
        std::clamp((32768.0f - world.y) / 65536.0f, 0.0f, 0.999999f)
    };
}
}
