#pragma once

#include <bgfx/bgfx.h>

#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
struct HouseEntry;

class GameplayDialogueRenderer
{
public:
    static void renderDialogueOverlay(
        GameplayScreenRuntime &context,
        int width,
        int height,
        bool renderAboveHud);
    static bool shouldRenderInCurrentPass(bool renderAboveHud, int hudZThreshold, int zIndex);
    static bool isDialogueFrameSubtree(GameplayScreenRuntime &context, const std::string &layoutId);
    static void renderBlackoutBackdrop(
        GameplayScreenRuntime &context,
        int screenWidth,
        int screenHeight,
        float viewportX,
        float viewportWidth);
    static void updateHouseShopHoverTopicText(
        GameplayScreenRuntime &context,
        int width,
        int height,
        float dialogMouseX,
        float dialogMouseY,
        std::optional<std::string> &hoveredHouseServiceTopicText);
    static void renderHouseShopOverlay(
        GameplayScreenRuntime &context,
        int width,
        int height,
        float dialogMouseX,
        float dialogMouseY,
        std::string &dialogueResponseHintText,
        bool renderAboveHud);
    static void renderDialogueTextureElement(
        GameplayScreenRuntime &context,
        const std::string &layoutId,
        int width,
        int height,
        float dialogMouseX,
        float dialogMouseY,
        bool showDialogueTextFrame,
        bool showDialogueVideoArea,
        bool showEventDialogPanel,
        bool renderAboveHud);
    static void renderDialogueLabelById(
        GameplayScreenRuntime &context,
        const std::string &layoutId,
        const std::string &label,
        int width,
        int height,
        bool renderAboveHud);
    static void renderDialogueEventPanel(
        GameplayScreenRuntime &context,
        int width,
        int height,
        float dialogMouseX,
        float dialogMouseY,
        bool renderAboveHud,
        bool showEventDialogPanel,
        bool isResidentSelectionMode,
        const HouseEntry *pHostHouseEntry,
        const std::optional<std::string> &hoveredHouseServiceTopicText,
        bool suppressServiceTopicsForShopOverlay);
    static void renderDialogueBodyText(
        GameplayScreenRuntime &context,
        int width,
        int height,
        bool renderAboveHud,
        const std::vector<std::string> &dialogueBodyLines);

private:
    static void submitTextureHandleQuad(
        GameplayScreenRuntime &context,
        bgfx::TextureHandle textureHandle,
        float x,
        float y,
        float quadWidth,
        float quadHeight);
    static void renderDialogueVideoArea(
        GameplayScreenRuntime &context,
        float x,
        float y,
        float quadWidth,
        float quadHeight);
    static void submitTextureHandleQuadUv(
        GameplayScreenRuntime &context,
        bgfx::TextureHandle textureHandle,
        float x,
        float y,
        float quadWidth,
        float quadHeight,
        float u0,
        float v0,
        float u1,
        float v1);
};
} // namespace OpenYAMM::Game
