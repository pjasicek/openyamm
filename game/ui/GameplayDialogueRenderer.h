#pragma once

#include <bgfx/bgfx.h>

#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayOverlayContext;
struct HouseEntry;

class GameplayDialogueRenderer
{
public:
    static bool shouldRenderInCurrentPass(bool renderAboveHud, int hudZThreshold, int zIndex);
    static bool isDialogueFrameSubtree(GameplayOverlayContext &context, const std::string &layoutId);
    static void renderBlackoutBackdrop(
        GameplayOverlayContext &context,
        int screenWidth,
        int screenHeight,
        float viewportX,
        float viewportWidth);
    static void updateHouseShopHoverTopicText(
        GameplayOverlayContext &context,
        int width,
        int height,
        float dialogMouseX,
        float dialogMouseY,
        std::optional<std::string> &hoveredHouseServiceTopicText);
    static void renderHouseShopOverlay(
        GameplayOverlayContext &context,
        int width,
        int height,
        float dialogMouseX,
        float dialogMouseY,
        std::string &dialogueResponseHintText,
        bool renderAboveHud);
    static void renderDialogueTextureElement(
        GameplayOverlayContext &context,
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
        GameplayOverlayContext &context,
        const std::string &layoutId,
        const std::string &label,
        int width,
        int height,
        bool renderAboveHud);
    static void renderDialogueEventPanel(
        GameplayOverlayContext &context,
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
        GameplayOverlayContext &context,
        int width,
        int height,
        bool renderAboveHud,
        const std::vector<std::string> &dialogueBodyLines);

private:
    static void submitTextureHandleQuad(
        GameplayOverlayContext &context,
        bgfx::TextureHandle textureHandle,
        float x,
        float y,
        float quadWidth,
        float quadHeight);
    static void renderDialogueVideoArea(
        GameplayOverlayContext &context,
        float x,
        float y,
        float quadWidth,
        float quadHeight);
    static void submitTextureHandleQuadUv(
        GameplayOverlayContext &context,
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
