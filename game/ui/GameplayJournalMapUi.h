#pragma once

#include "game/gameplay/GameplaySaveLoadUiSupport.h"
#include "game/ui/GameplayMinimapTransform.h"
#include "game/ui/GameplayUiController.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <filesystem>
#include <string>

namespace OpenYAMM::Game
{
constexpr int GameplayJournalMapBaseZoom = 384;
constexpr float GameplayJournalMapPinLogicalSize = 10.0f;

struct GameplayJournalMapPoint
{
    float x = 0.0f;
    float y = 0.0f;
};

struct GameplayJournalMapTransform
{
    float uOrigin = 0.0f;
    float vOrigin = 0.0f;
    float uSpan = 1.0f;
    float vSpan = 1.0f;
};

inline int clampedGameplayJournalMapZoomValue(int zoomStep)
{
    const int clampedStep = std::clamp(zoomStep, 0, static_cast<int>(GameplayJournalMapZoomLevels.size()) - 1);
    return GameplayJournalMapZoomLevels[clampedStep];
}

// A journal map's view: its zoom step and the world point at its centre (the Map view's, or the trainer finder's map
// of another map).
struct GameplayJournalMapView
{
    int zoomStep = 0;
    float centerX = 0.0f;
    float centerY = 0.0f;
};

inline GameplayJournalMapView gameplayJournalMapView(const GameplayUiController::JournalScreenState &journalScreen)
{
    return {journalScreen.mapZoomStep, journalScreen.mapCenterX, journalScreen.mapCenterY};
}

inline GameplayJournalMapTransform gameplayJournalMapTransform(
    const GameplayJournalMapView &view,
    const GameplayMinimapState *pMinimapState = nullptr,
    float viewportWidth = 1.0f,
    float viewportHeight = 1.0f)
{
    const int zoom = clampedGameplayJournalMapZoomValue(view.zoomStep);
    const float zoomFactor = static_cast<float>(zoom) / static_cast<float>(GameplayJournalMapBaseZoom);
    const GameplayMinimapPoint center = pMinimapState != nullptr
        ? gameplayMinimapWorldToUv(*pMinimapState, view.centerX, view.centerY)
        : GameplayMinimapPoint {
            (view.centerX + GameplayJournalMapWorldHalfExtent)
                / (GameplayJournalMapWorldHalfExtent * 2.0f),
            (GameplayJournalMapWorldHalfExtent - view.centerY)
                / (GameplayJournalMapWorldHalfExtent * 2.0f)};
    float uSpan = 1.0f / std::max(zoomFactor, 0.000001f);
    float vSpan = 1.0f / std::max(zoomFactor, 0.000001f);

    if (pMinimapState != nullptr
        && pMinimapState->zoomWidth > 0.0f
        && pMinimapState->zoomHeight > 0.0f)
    {
        const float imageAspect = pMinimapState->zoomWidth / pMinimapState->zoomHeight;
        const float viewportAspect = std::max(viewportWidth, 1.0f) / std::max(viewportHeight, 1.0f);

        if (imageAspect > viewportAspect)
        {
            vSpan *= imageAspect / viewportAspect;
        }
        else
        {
            uSpan *= viewportAspect / imageAspect;
        }
    }

    return {
        center.x - uSpan * 0.5f,
        center.y - vSpan * 0.5f,
        uSpan,
        vSpan
    };
}

inline GameplayJournalMapTransform gameplayJournalMapTransform(
    const GameplayUiController::JournalScreenState &journalScreen,
    const GameplayMinimapState *pMinimapState = nullptr,
    float viewportWidth = 1.0f,
    float viewportHeight = 1.0f)
{
    return gameplayJournalMapTransform(
        gameplayJournalMapView(journalScreen), pMinimapState, viewportWidth, viewportHeight);
}

// Keeps the view's zoom step among the levels and its centre where the view stays on the map image.
inline void clampGameplayJournalMapView(GameplayJournalMapView &view, const GameplayMinimapState &minimapState)
{
    view.zoomStep = std::clamp(view.zoomStep, 0, static_cast<int>(GameplayJournalMapZoomLevels.size()) - 1);
    const GameplayJournalMapTransform transform = gameplayJournalMapTransform(view, &minimapState);
    const float visibleHalfWidth = (minimapState.worldMaxX - minimapState.worldMinX) * transform.uSpan * 0.5f;
    const float visibleHalfHeight = (minimapState.worldMaxY - minimapState.worldMinY) * transform.vSpan * 0.5f;
    const float minimumCenterX = minimapState.worldMinX + visibleHalfWidth;
    const float maximumCenterX = minimapState.worldMaxX - visibleHalfWidth;
    const float minimumCenterY = minimapState.worldMinY + visibleHalfHeight;
    const float maximumCenterY = minimapState.worldMaxY - visibleHalfHeight;
    view.centerX = minimumCenterX <= maximumCenterX
        ? std::clamp(view.centerX, minimumCenterX, maximumCenterX)
        : (minimapState.worldMinX + minimapState.worldMaxX) * 0.5f;
    view.centerY = minimumCenterY <= maximumCenterY
        ? std::clamp(view.centerY, minimumCenterY, maximumCenterY)
        : (minimapState.worldMinY + minimapState.worldMaxY) * 0.5f;
}

inline void clampGameplayJournalMapState(
    GameplayUiController::JournalScreenState &journalScreen,
    const GameplayMinimapState *pMinimapState)
{
    if (pMinimapState == nullptr)
    {
        clampJournalMapState(journalScreen);
        return;
    }

    journalScreen.mapZoomStep = std::clamp(
        journalScreen.mapZoomStep,
        0,
        static_cast<int>(GameplayJournalMapZoomLevels.size()) - 1);
    const GameplayJournalMapTransform transform = gameplayJournalMapTransform(journalScreen, pMinimapState);
    const float visibleHalfWidth =
        (pMinimapState->worldMaxX - pMinimapState->worldMinX) * transform.uSpan * 0.5f;
    const float visibleHalfHeight =
        (pMinimapState->worldMaxY - pMinimapState->worldMinY) * transform.vSpan * 0.5f;
    const float minimumCenterX = pMinimapState->worldMinX + visibleHalfWidth;
    const float maximumCenterX = pMinimapState->worldMaxX - visibleHalfWidth;
    const float minimumCenterY = pMinimapState->worldMinY + visibleHalfHeight;
    const float maximumCenterY = pMinimapState->worldMaxY - visibleHalfHeight;

    journalScreen.mapCenterX = minimumCenterX <= maximumCenterX
        ? std::clamp(journalScreen.mapCenterX, minimumCenterX, maximumCenterX)
        : (pMinimapState->worldMinX + pMinimapState->worldMaxX) * 0.5f;
    journalScreen.mapCenterY = minimumCenterY <= maximumCenterY
        ? std::clamp(journalScreen.mapCenterY, minimumCenterY, maximumCenterY)
        : (pMinimapState->worldMinY + pMinimapState->worldMaxY) * 0.5f;
}

inline GameplayJournalMapPoint gameplayJournalWorldToScreen(
    float worldX,
    float worldY,
    float viewportX,
    float viewportY,
    float viewportWidth,
    float viewportHeight,
    const GameplayJournalMapView &view,
    const GameplayMinimapState *pMinimapState = nullptr)
{
    const GameplayJournalMapTransform transform = gameplayJournalMapTransform(
        view,
        pMinimapState,
        viewportWidth,
        viewportHeight);
    const GameplayMinimapPoint point = pMinimapState != nullptr
        ? gameplayMinimapWorldToUv(*pMinimapState, worldX, worldY)
        : GameplayMinimapPoint {
            (worldX + GameplayJournalMapWorldHalfExtent) / (GameplayJournalMapWorldHalfExtent * 2.0f),
            (GameplayJournalMapWorldHalfExtent - worldY) / (GameplayJournalMapWorldHalfExtent * 2.0f)};

    return {
        viewportX + ((point.x - transform.uOrigin) / std::max(transform.uSpan, 0.000001f)) * viewportWidth,
        viewportY + ((point.y - transform.vOrigin) / std::max(transform.vSpan, 0.000001f)) * viewportHeight
    };
}

inline GameplayJournalMapPoint gameplayJournalWorldToScreen(
    float worldX,
    float worldY,
    float viewportX,
    float viewportY,
    float viewportWidth,
    float viewportHeight,
    const GameplayUiController::JournalScreenState &journalScreen,
    const GameplayMinimapState *pMinimapState = nullptr)
{
    return gameplayJournalWorldToScreen(worldX, worldY, viewportX, viewportY, viewportWidth, viewportHeight,
        gameplayJournalMapView(journalScreen), pMinimapState);
}

inline GameplayJournalMapPoint gameplayJournalScreenToWorld(
    float screenX,
    float screenY,
    float viewportX,
    float viewportY,
    float viewportWidth,
    float viewportHeight,
    const GameplayUiController::JournalScreenState &journalScreen,
    const GameplayMinimapState *pMinimapState = nullptr)
{
    const GameplayJournalMapTransform transform = gameplayJournalMapTransform(
        journalScreen,
        pMinimapState,
        viewportWidth,
        viewportHeight);
    const float u =
        transform.uOrigin + ((screenX - viewportX) / std::max(viewportWidth, 1.0f)) * transform.uSpan;
    const float v =
        transform.vOrigin + ((screenY - viewportY) / std::max(viewportHeight, 1.0f)) * transform.vSpan;

    if (pMinimapState != nullptr)
    {
        const GameplayMinimapPoint worldPoint = gameplayMinimapUvToWorld(*pMinimapState, u, v);
        return {worldPoint.x, worldPoint.y};
    }

    return {
        u * (GameplayJournalMapWorldHalfExtent * 2.0f) - GameplayJournalMapWorldHalfExtent,
        GameplayJournalMapWorldHalfExtent - v * (GameplayJournalMapWorldHalfExtent * 2.0f)};
}

inline std::string gameplayJournalNormalizeMapFileName(const std::string &mapFileName)
{
    std::string normalized = std::filesystem::path(mapFileName).filename().string();

    std::transform(
        normalized.begin(),
        normalized.end(),
        normalized.begin(),
        [](unsigned char ch)
        {
            return static_cast<char>(std::tolower(ch));
        });

    return normalized;
}
} // namespace OpenYAMM::Game
