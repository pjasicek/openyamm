#include "game/ui/GameplayUiSkin.h"
#include "game/ui/GameplayDialogueRenderer.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/HouseShopLayout.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"

#include "game/gameplay/HouseServiceRuntime.h"
#include "game/gameplay/ReputationRuntime.h"
#include "game/tables/ItemTable.h"
#include "game/StringUtils.h"

#include <bx/math.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdio>
#include <limits>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
int effectiveReputationForView(const GameplayScreenRuntime &view)
{
    const IGameplayWorldRuntime *pWorldRuntime = view.worldRuntime();
    return pWorldRuntime != nullptr
        ? effectivePartyReputation(pWorldRuntime->currentLocationReputation(), pWorldRuntime->eventRuntimeState())
        : 0;
}

std::optional<std::string> pendingInputPromptHint(const GameplayScreenRuntime &view)
{
    if (!view.activeEventDialog().isActive)
    {
        return std::nullopt;
    }

    const IGameplayWorldRuntime *pWorldRuntime = view.worldRuntime();
    const EventRuntimeState *pRuntimeState = pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;

    if (pRuntimeState == nullptr
        || !pRuntimeState->pendingInputPrompt
        || pRuntimeState->pendingInputPrompt->kind != EventRuntimeState::PendingInputPrompt::Kind::InputString)
    {
        return std::nullopt;
    }

    return std::string("Answer: _");
}

constexpr uint16_t HudViewId = 2;
constexpr uint32_t HoveredDialogueTopicTextColorAbgr = 0xff23cde1u;
constexpr uint32_t FreeHavenHighCouncilHouseId = 209;
constexpr uint32_t PrestonSteelNpcId = 1084;
constexpr uint32_t ToriGoldmanNpcId = 1085;
constexpr uint32_t IsaacRockwellNpcId = 1086;
constexpr uint32_t OlafHeimdallNpcId = 1087;
constexpr uint32_t EuclidKeplerNpcId = 1088;
constexpr uint32_t SlickerSilvertongueNpcId = 1089;
constexpr float EventNpcFrameNativeWidth = 71.0f;
constexpr float EventNpcFrameNativeHeight = 81.0f;
constexpr float EventNpcPortraitNativeX = 4.0f;
constexpr float EventNpcPortraitNativeY = 4.0f;
constexpr float EventNpcPortraitNativeWidth = 63.0f;
constexpr float EventNpcPortraitNativeHeight = 73.0f;
constexpr float EventNpcPortraitUvCropX = 2.0f;
constexpr float EventNpcPortraitUvCropY = 2.0f;
constexpr float DialogueTextTopInset = 2.0f;
constexpr float DialogueTextBottomInset = 5.0f;
constexpr float DialogueTextRightInset = 6.0f;
constexpr float DialogueTextPrimaryFontMaxHeight = 310.0f;
constexpr const char *DialogueTextSmallFontName = "Create";
constexpr float Mm9RudeCanvasWidth = 800.0f;
constexpr float Mm9RudeCanvasHeight = 600.0f;
constexpr float Mm9RudeBackgroundX = 139.0f;
constexpr float Mm9RudeBackgroundY = 408.0f;
constexpr float Mm9RudeBackgroundWidth = 540.0f;
constexpr float Mm9RudeBackgroundHeight = 192.0f;
constexpr float Mm9RudeTextX = 160.0f;
constexpr float Mm9RudeTitleY = 428.0f;
constexpr float Mm9RudeBodyY = 444.0f;
constexpr float Mm9RudeTopicsX = 184.0f;
constexpr float Mm9RudeTopicsY = 492.0f;
constexpr float Mm9RudeTopicAdvance = 16.0f;
constexpr const char *Mm9RudeBackgroundTexture = "ui/dialogue/RUDEBG_OPENYAMM_LIGHT_ORNATE_SLIM.png";
constexpr const char *Mm9RudeFontName = "RUDEBLACK";
constexpr const char *Mm9RudeHoveredFontName = "RUDERED";

std::optional<float> fullWidthStandaloneDialogueFrameWidth(
    const GameplayScreenRuntime::HudLayoutElement *pDialogueRootLayout,
    const GameplayScreenRuntime::HudLayoutElement *pDialogueFrameLayout)
{
    if (pDialogueRootLayout == nullptr || pDialogueFrameLayout == nullptr)
    {
        return std::nullopt;
    }

    const float frameWidth = pDialogueRootLayout->width - std::max(0.0f, pDialogueFrameLayout->gapX);

    if (frameWidth <= pDialogueFrameLayout->width)
    {
        return std::nullopt;
    }

    return frameWidth;
}

std::optional<float> fullWidthStandaloneDialogueTextWidth(
    float frameWidth,
    const GameplayScreenRuntime::HudLayoutElement *pDialogueFrameLayout,
    const GameplayScreenRuntime::HudLayoutElement *pDialogueTextLayout)
{
    if (pDialogueFrameLayout == nullptr || pDialogueTextLayout == nullptr)
    {
        return std::nullopt;
    }

    const float originalRightInset = std::max(
        0.0f,
        pDialogueFrameLayout->width - pDialogueTextLayout->gapX - pDialogueTextLayout->width);
    const float textWidth = frameWidth - pDialogueTextLayout->gapX - originalRightInset;

    if (textWidth <= pDialogueTextLayout->width)
    {
        return std::nullopt;
    }

    return textWidth;
}

float dialogueTextLineAdvance(const GameplayScreenRuntime::HudFontHandle &font)
{
    return static_cast<float>(std::max(1, font.fontHeight - 3));
}

void renderMm9RudeText(
    GameplayScreenRuntime &view,
    const GameplayScreenRuntime::HudFontHandle &font,
    bgfx::TextureHandle texture,
    const std::string &text,
    float x,
    float y,
    float scale)
{
    view.renderHudFontLayer(font, texture, text, std::round(x), std::round(y), scale);
}

void renderMm9RudeDialogueOverlay(
    GameplayScreenRuntime &view,
    int width,
    int height,
    bool renderAboveHud,
    float mouseX,
    float mouseY)
{
    if (!renderAboveHud)
    {
        return;
    }

    const GameplayUiViewportRect viewport = GameplayHudCommon::computeUiViewportRect(width, height);
    const float scale = std::min(viewport.width / Mm9RudeCanvasWidth, viewport.height / Mm9RudeCanvasHeight);
    const float canvasX = viewport.x + (viewport.width - Mm9RudeCanvasWidth * scale) * 0.5f;
    const float canvasY = viewport.y + (viewport.height - Mm9RudeCanvasHeight * scale) * 0.5f;
    const float backgroundX = canvasX + Mm9RudeBackgroundX * scale;
    const float backgroundY = canvasY + Mm9RudeBackgroundY * scale;
    const std::optional<GameplayScreenRuntime::HudTextureHandle> background =
        view.gameplayUiRuntime().ensureHudTextureLoaded(Mm9RudeBackgroundTexture);
    if (background)
    {
        view.submitHudTexturedQuad(
            *background,
            backgroundX,
            backgroundY,
            Mm9RudeBackgroundWidth * scale,
            Mm9RudeBackgroundHeight * scale);
    }

    const std::optional<GameplayScreenRuntime::HudFontHandle> font = view.findHudFont(Mm9RudeFontName);
    const std::optional<GameplayScreenRuntime::HudFontHandle> hoveredFont =
        view.findHudFont(Mm9RudeHoveredFontName);
    if (!font || !hoveredFont)
    {
        return;
    }
    const bgfx::TextureHandle normalFontTexture = font->mainTextureHandle;

    renderMm9RudeText(
        view,
        *font,
        normalFontTexture,
        view.activeEventDialog().title,
        canvasX + Mm9RudeTextX * scale,
        canvasY + Mm9RudeTitleY * scale,
        scale);

    float bodyY = canvasY + Mm9RudeBodyY * scale;
    for (const std::string &line : view.activeEventDialog().lines)
    {
        const std::vector<std::string> wrapped = view.wrapHudTextToWidth(*font, line, 480.0f);
        for (const std::string &wrappedLine : wrapped)
        {
            if (bodyY >= canvasY + (Mm9RudeTopicsY - 4.0f) * scale)
            {
                break;
            }
            renderMm9RudeText(
                view,
                *font,
                normalFontTexture,
                wrappedLine,
                canvasX + Mm9RudeTextX * scale,
                bodyY,
                scale);
            bodyY += 12.0f * scale;
        }
    }

    const float topicX = canvasX + Mm9RudeTopicsX * scale;
    float topicY = canvasY + Mm9RudeTopicsY * scale;
    const size_t visibleTopicCount = std::min<size_t>(view.activeEventDialog().actions.size(), 6);
    for (size_t actionIndex = 0; actionIndex < visibleTopicCount; ++actionIndex)
    {
        const bool hovered = mouseX >= topicX
            && mouseX < backgroundX + Mm9RudeBackgroundWidth * scale - 20.0f * scale
            && mouseY >= topicY - 2.0f * scale
            && mouseY < topicY + Mm9RudeTopicAdvance * scale;
        renderMm9RudeText(
            view,
            hovered ? *hoveredFont : *font,
            hovered ? hoveredFont->mainTextureHandle : normalFontTexture,
            view.activeEventDialog().actions[actionIndex].label,
            topicX,
            topicY,
            scale);
        topicY += Mm9RudeTopicAdvance * scale;
    }
}

struct PointerRenderInput
{
    float mouseX = 0.0f;
    float mouseY = 0.0f;
    bool isLeftMousePressed = false;
};

struct DialogueBodyTextMetrics
{
    GameplayScreenRuntime::HudFontHandle font = {};
    float textHeight = 0.0f;
    float fontScale = 1.0f;
};

float snappedHudFontScale(float scale);

float dialogueTitleLineAdvance(const GameplayScreenRuntime::HudFontHandle &font, float fontScale)
{
    return static_cast<float>(std::max(1, font.fontHeight - 3)) * fontScale;
}

float renderWrappedCenteredDialogueTitle(
    GameplayScreenRuntime &view,
    const GameplayScreenRuntime::HudLayoutElement &layout,
    const GameplayScreenRuntime::ResolvedHudLayoutElement &resolved,
    const std::string &label)
{
    if (label.empty())
    {
        return 0.0f;
    }

    const std::optional<GameplayScreenRuntime::HudFontHandle> font = view.findHudFont(layout.fontName);

    if (!font)
    {
        view.renderLayoutLabel(layout, resolved, label);
        return resolved.height;
    }

    const float fontScale = snappedHudFontScale(resolved.scale * std::max(0.1f, layout.textScale));
    const float textWidthScaled =
        std::max(0.0f, resolved.width - std::abs(layout.textPadX * resolved.scale) * 2.0f);
    const float textWrapWidth = textWidthScaled / std::max(1.0f, fontScale);
    std::vector<std::string> wrappedLines = view.wrapHudTextToWidth(*font, label, textWrapWidth);

    if (wrappedLines.empty())
    {
        wrappedLines.push_back(label);
    }

    const float lineHeight = static_cast<float>(font->fontHeight) * fontScale;
    const float lineAdvance = dialogueTitleLineAdvance(*font, fontScale);
    const float textHeight = lineHeight + static_cast<float>(wrappedLines.size() - 1) * lineAdvance;
    const float startY = resolved.y + std::max(0.0f, (resolved.height - textHeight) * 0.5f);
    GameplayScreenRuntime::HudLayoutElement lineLayout = layout;
    lineLayout.textAlignX = UiLayoutManager::TextAlignX::Center;
    lineLayout.textAlignY = UiLayoutManager::TextAlignY::Middle;

    for (size_t lineIndex = 0; lineIndex < wrappedLines.size(); ++lineIndex)
    {
        GameplayScreenRuntime::ResolvedHudLayoutElement resolvedLine = resolved;
        resolvedLine.y = startY + static_cast<float>(lineIndex) * lineAdvance;
        resolvedLine.height = lineHeight;
        view.renderLayoutLabel(lineLayout, resolvedLine, wrappedLines[lineIndex]);
    }

    return textHeight;
}

PointerRenderInput pointerRenderInput(const GameplayScreenRuntime &view)
{
    PointerRenderInput input = {};
    const GameplayInputFrame *pInputFrame = view.currentGameplayInputFrame();

    if (pInputFrame == nullptr)
    {
        return input;
    }

    input.mouseX = pInputFrame->pointerX;
    input.mouseY = pInputFrame->pointerY;
    input.isLeftMousePressed = pInputFrame->leftMouseButton.held;
    return input;
}

std::optional<uint32_t> freeHavenCouncilStatusPictureId(uint32_t houseId, uint32_t npcId, const Party *pParty)
{
    if (houseId != FreeHavenHighCouncilHouseId || npcId < PrestonSteelNpcId || npcId > SlickerSilvertongueNpcId)
    {
        return std::nullopt;
    }

    const uint32_t pictureBaseId = (SlickerSilvertongueNpcId - npcId) * 3 + 1;

    if (npcId == SlickerSilvertongueNpcId)
    {
        return pictureBaseId + 1;
    }

    uint32_t approvalAwardId = 0;

    switch (npcId)
    {
        case PrestonSteelNpcId:
            approvalAwardId = 59;
            break;
        case ToriGoldmanNpcId:
            approvalAwardId = 61;
            break;
        case IsaacRockwellNpcId:
            approvalAwardId = 60;
            break;
        case OlafHeimdallNpcId:
            approvalAwardId = 62;
            break;
        case EuclidKeplerNpcId:
            approvalAwardId = 58;
            break;
        default:
            break;
    }

    const bool approved = pParty != nullptr && approvalAwardId != 0 && pParty->hasAward(approvalAwardId);
    return pictureBaseId + (approved ? 0 : 1);
}

std::optional<float> freeHavenCouncilBenchCenterX(uint32_t npcId)
{
    switch (npcId)
    {
        case PrestonSteelNpcId:
            return 0.098f;
        case ToriGoldmanNpcId:
            return 0.265f;
        case IsaacRockwellNpcId:
            return 0.415f;
        case OlafHeimdallNpcId:
            return 0.565f;
        case EuclidKeplerNpcId:
            return 0.735f;
        case SlickerSilvertongueNpcId:
            return 0.9f;
        default:
            return std::nullopt;
    }
}

float freeHavenCouncilBenchOffsetY(uint32_t npcId)
{
    switch (npcId)
    {
        case PrestonSteelNpcId:
            return 55.0f;
        case ToriGoldmanNpcId:
            return 6.0f;
        case IsaacRockwellNpcId:
            return 0.0f;
        case OlafHeimdallNpcId:
            return 0.0f;
        case EuclidKeplerNpcId:
            return 4.0f;
        case SlickerSilvertongueNpcId:
            return 53.0f;
        default:
            return 0.0f;
    }
}

void renderFreeHavenCouncilBenchParticipants(
    GameplayScreenRuntime &view,
    const HouseEntry *pHostHouseEntry,
    const Party *pParty,
    float x,
    float y,
    float quadWidth,
    float quadHeight)
{
    if (pHostHouseEntry == nullptr || pHostHouseEntry->id != FreeHavenHighCouncilHouseId)
    {
        return;
    }

    const float imageScale = quadWidth / 460.0f;
    const float bottomY = y + quadHeight * 0.665f;

    const EventRuntimeState *pEventRuntimeState =
        view.worldRuntime() != nullptr ? view.worldRuntime()->eventRuntimeState() : nullptr;

    for (uint32_t npcId : pHostHouseEntry->residentNpcIds)
    {
        if (pEventRuntimeState != nullptr)
        {
            const auto overrideIterator = pEventRuntimeState->npcHouseOverrides.find(npcId);

            if (overrideIterator != pEventRuntimeState->npcHouseOverrides.end()
                && overrideIterator->second != FreeHavenHighCouncilHouseId)
            {
                continue;
            }

            if (pEventRuntimeState->unavailableNpcIds.contains(npcId))
            {
                continue;
            }
        }

        const std::optional<uint32_t> pictureId =
            freeHavenCouncilStatusPictureId(FreeHavenHighCouncilHouseId, npcId, pParty);
        const std::optional<float> centerX = freeHavenCouncilBenchCenterX(npcId);

        if (!pictureId.has_value() || !centerX.has_value())
        {
            continue;
        }

        char textureName[16] = {};
        std::snprintf(textureName, sizeof(textureName), "npc%04u", *pictureId);
        const std::optional<GameplayScreenRuntime::HudTextureHandle> texture =
            view.gameplayUiRuntime().ensureHudTextureLoaded(textureName);

        if (!texture.has_value())
        {
            continue;
        }

        const float drawWidth = static_cast<float>(texture->width) * imageScale;
        const float drawHeight = static_cast<float>(texture->height) * imageScale;
        const float drawX = std::round(x + quadWidth * *centerX - drawWidth * 0.5f);
        const float drawY =
            std::round(bottomY - drawHeight + freeHavenCouncilBenchOffsetY(npcId) * imageScale);
        view.submitHudTexturedQuad(*texture, drawX, drawY, drawWidth, drawHeight);
    }
}

uint32_t currentDialogueHostHouseId(const EventRuntimeState *pEventRuntimeState)
{
    return pEventRuntimeState != nullptr ? pEventRuntimeState->dialogueState.hostHouseId : 0;
}

bool isHouseOccupantSelectionMode(const EventDialogContent &dialog)
{
    return !dialog.actions.empty()
        && std::all_of(
            dialog.actions.begin(),
            dialog.actions.end(),
            [](const EventDialogAction &action)
            {
                return action.kind == EventDialogActionKind::HouseProprietor
                    || action.kind == EventDialogActionKind::HouseExtraExit
                    || action.kind == EventDialogActionKind::HouseResident;
            });
}

bool isEmptyHouseDialog(const EventDialogContent &dialog)
{
    return dialog.isHouseDialog && dialog.lines.empty() && dialog.actions.empty();
}

struct InventoryGridMetrics
{
    float x = 0.0f;
    float y = 0.0f;
    float cellWidth = 0.0f;
    float cellHeight = 0.0f;
};

InventoryGridMetrics computeInventoryGridMetrics(
    float x,
    float y,
    float width,
    float height,
    int columns,
    int rows)
{
    InventoryGridMetrics metrics = {};
    metrics.x = x;
    metrics.y = y;
    metrics.cellWidth = width / static_cast<float>(std::max(1, columns));
    metrics.cellHeight = height / static_cast<float>(std::max(1, rows));
    return metrics;
}

float snappedHudFontScale(float scale)
{
    if (scale < 1.0f)
    {
        return std::max(0.5f, scale);
    }

    const float roundedScale = std::round(scale);

    if (std::abs(scale - roundedScale) <= 0.1f)
    {
        return roundedScale;
    }

    return scale;
}

std::optional<DialogueBodyTextMetrics> calculateDialogueBodyTextMetrics(
    GameplayScreenRuntime &view,
    const GameplayScreenRuntime::HudLayoutElement &layout,
    const std::vector<std::string> &dialogueBodyLines)
{
    const auto calculateForFont = [&](const GameplayScreenRuntime::HudFontHandle &font, float targetHeight)
    {
        DialogueBodyTextMetrics metrics;
        metrics.font = font;
        metrics.fontScale = targetHeight / std::max(1, font.fontHeight);
        const float wrapWidth = (layout.width - 2 * std::abs(layout.textPadX) - DialogueTextRightInset)
            / metrics.fontScale;
        size_t lines = 0;
        for (const std::string &line : dialogueBodyLines)
        {
            lines += std::max(size_t{1}, view.wrapHudTextToWidth(font, line, wrapWidth).size());
        }
        metrics.textHeight = lines * dialogueTextLineAdvance(font) * metrics.fontScale
            + 2 * std::abs(layout.textPadY) + DialogueTextTopInset + DialogueTextBottomInset;
        return metrics;
    };
    DialogueBodyTextMetrics metrics;
    for (const auto &[fontName, targetHeight] : std::array<std::pair<const char *, float>, 4>{{
        {"Arrus", 19}, {"Arrus", 18}, {"Create", 18}, {"Create", 17}}})
    {
        const std::optional<GameplayHudFontHandle> font = view.findHudFont(fontName);
        if (!font)
        {
            return std::nullopt;
        }
        metrics = calculateForFont(*font, targetHeight);
        if (metrics.textHeight <= DialogueTextPrimaryFontMaxHeight)
        {
            return metrics;
        }
    }
    return metrics;
}
} // namespace

void GameplayDialogueRenderer::renderDialogueOverlay(
    GameplayScreenRuntime &view,
    int width,
    int height,
    bool renderAboveHud)
{
    if (view.currentHudScreenState() != GameplayHudScreenState::Dialogue
        || !view.activeEventDialog().isActive
        || !view.hasHudRenderResources()
        || width <= 0
        || height <= 0)
    {
        return;
    }

    view.clearHudLayoutRuntimeHeightOverrides();
    const PointerRenderInput pointerInput = pointerRenderInput(view);
    const float dialogMouseX = pointerInput.mouseX;
    const float dialogMouseY = pointerInput.mouseY;

    if (view.activeEventDialog().presentation == EventDialogPresentation::Mm9Rude)
    {
        renderMm9RudeDialogueOverlay(
            view,
            width,
            height,
            renderAboveHud,
            dialogMouseX,
            dialogMouseY);
        return;
    }

    const GameplayUiViewportRect uiViewport = GameplayHudCommon::computeUiViewportRect(width, height);

    if (!renderAboveHud && uiViewport.x > 0.5f)
    {
        renderBlackoutBackdrop(view, width, height, uiViewport.x, uiViewport.width);
    }

    const bool residentSelectionMode = isHouseOccupantSelectionMode(view.activeEventDialog());
    const EventRuntimeState *pEventRuntimeState =
        view.worldRuntime() != nullptr ? view.worldRuntime()->eventRuntimeState() : nullptr;
    const uint32_t dialogueHostHouseId = currentDialogueHostHouseId(pEventRuntimeState);
    const HouseEntry *pHostHouseEntry =
        (dialogueHostHouseId != 0 && view.houseTable() != nullptr)
        ? view.houseTable()->get(dialogueHostHouseId)
        : nullptr;
    const bool showDialogueVideoArea = activeEventDialogShowsVideoArea(
        view.activeEventDialog(),
        pHostHouseEntry != nullptr);
    const bool hasDialogueParticipantIdentity =
        !view.activeEventDialog().title.empty()
        || view.activeEventDialog().participantPictureId != 0
        || view.activeEventDialog().sourceId != 0;
    const bool emptyHouseDialog = isEmptyHouseDialog(view.activeEventDialog());
    const bool showEventDialogPanel =
        emptyHouseDialog
        || (residentSelectionMode
            || !view.activeEventDialog().actions.empty()
            || pHostHouseEntry != nullptr
            || hasDialogueParticipantIdentity);
    const std::vector<std::string> &dialogueBodyLines = view.activeEventDialog().lines;
    const bool isTransitionDialog =
        view.activeEventDialog().presentation == EventDialogPresentation::Transition;
    const bool showDialogueTextFrame = !isTransitionDialog && !dialogueBodyLines.empty();
    std::optional<std::string> hoveredHouseServiceTopicText;
    const bool suppressServiceTopicsForShopOverlay =
        (view.houseShopOverlay().active
         && (view.houseShopOverlay().mode == GameplayUiController::HouseShopMode::BuyStandard
             || view.houseShopOverlay().mode == GameplayUiController::HouseShopMode::BuySpecial
             || view.houseShopOverlay().mode == GameplayUiController::HouseShopMode::BuySpellbooks))
        || (view.inventoryNestedOverlay().active
            && (view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell
                || view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify
                || view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopRepair));
    const Party *pParty = view.partyReadOnly();

    updateHouseShopHoverTopicText(
        view,
        width,
        height,
        dialogMouseX,
        dialogMouseY,
        hoveredHouseServiceTopicText);

    const GameplayScreenRuntime::HudLayoutElement *pDialogueFrameLayout = view.findHudLayoutElement("DialogueFrame");
    const GameplayScreenRuntime::HudLayoutElement *pDialogueRootLayout = view.findHudLayoutElement("DialogueRoot");
    const GameplayScreenRuntime::HudLayoutElement *pDialogueTextLayout = view.findHudLayoutElement("DialogueText");
    const GameplayScreenRuntime::HudLayoutElement *pBasebarLayout = view.findHudLayoutElement("OutdoorBasebar");
    const bool useFullWidthDialogueTextFrame = showDialogueTextFrame && !showEventDialogPanel;
    std::optional<float> fullWidthDialogueFrameWidth;
    std::optional<float> fullWidthDialogueTextWidth;

    if (useFullWidthDialogueTextFrame)
    {
        fullWidthDialogueFrameWidth =
            fullWidthStandaloneDialogueFrameWidth(pDialogueRootLayout, pDialogueFrameLayout);

        if (fullWidthDialogueFrameWidth)
        {
            fullWidthDialogueTextWidth =
                fullWidthStandaloneDialogueTextWidth(*fullWidthDialogueFrameWidth, pDialogueFrameLayout, pDialogueTextLayout);
            view.setHudLayoutRuntimeWidthOverride("DialogueFrame", *fullWidthDialogueFrameWidth);
            view.setHudLayoutRuntimeWidthOverride("DialogueFrameEndCap", *fullWidthDialogueFrameWidth);

            if (fullWidthDialogueTextWidth)
            {
                view.setHudLayoutRuntimeWidthOverride("DialogueText", *fullWidthDialogueTextWidth);
            }
        }
    }

    if (showDialogueTextFrame
        && pDialogueFrameLayout != nullptr
        && pDialogueTextLayout != nullptr
        && pBasebarLayout != nullptr
        && toLowerCopy(pDialogueFrameLayout->screen) == "dialogue"
        && toLowerCopy(pDialogueTextLayout->screen) == "dialogue")
    {
        GameplayScreenRuntime::HudLayoutElement effectiveDialogueTextLayout = *pDialogueTextLayout;

        if (fullWidthDialogueTextWidth)
        {
            effectiveDialogueTextLayout.width = *fullWidthDialogueTextWidth;
        }

        const std::optional<DialogueBodyTextMetrics> textMetrics =
            calculateDialogueBodyTextMetrics(view, effectiveDialogueTextLayout, dialogueBodyLines);

        if (textMetrics)
        {
            const float bodyHeight = std::min(DialogueTextPrimaryFontMaxHeight, textMetrics->textHeight);
            const float authoritativeFrameHeight = pBasebarLayout->height + bodyHeight + 15.0f;
            view.setHudLayoutRuntimeHeightOverride("DialogueFrame", authoritativeFrameHeight);
            view.setHudLayoutRuntimeHeightOverride("DialogueText", bodyHeight);
        }
    }

    std::string dialogueResponseHintText;

    if (view.houseBankState().inputActive())
    {
        dialogueResponseHintText = "Type amount  Enter accept  E/Esc cancel";
    }

    if (view.statusBarEventRemainingSeconds() > 0.0f && !view.statusBarEventText().empty())
    {
        dialogueResponseHintText = view.statusBarEventText();
    }
    else if (const std::optional<std::string> promptHint = pendingInputPromptHint(view))
    {
        dialogueResponseHintText = *promptHint;
    }

    if (view.inventoryNestedOverlay().active
        && (view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell
            || view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify
            || view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopRepair))
    {
        if (view.statusBarEventRemainingSeconds() <= 0.0f || view.statusBarEventText().empty())
        {
            if (view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell)
            {
                dialogueResponseHintText = "Select the Item to Sell";
            }
            else if (view.inventoryNestedOverlay().mode
                == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify)
            {
                dialogueResponseHintText = "Select the Item to Identify";
            }
            else if (view.inventoryNestedOverlay().mode
                == GameplayUiController::InventoryNestedOverlayMode::ShopRepair)
            {
                dialogueResponseHintText = "Select the Item to Repair";
            }
        }

        if (pHostHouseEntry != nullptr && view.party() != nullptr && view.itemTable() != nullptr)
        {
            const Character *pActiveCharacter = view.party()->activeMember();
            const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedInventoryGrid =
                view.resolveInventoryNestedOverlayGridArea(width, height);

            if (pActiveCharacter != nullptr && resolvedInventoryGrid)
            {
                const InventoryGridMetrics gridMetrics = computeInventoryGridMetrics(
                    resolvedInventoryGrid->x,
                    resolvedInventoryGrid->y,
                    resolvedInventoryGrid->width,
                    resolvedInventoryGrid->height,
                    Character::InventoryWidth,
                    Character::InventoryHeight);

                if (dialogMouseX >= resolvedInventoryGrid->x
                    && dialogMouseX < resolvedInventoryGrid->x + resolvedInventoryGrid->width
                    && dialogMouseY >= resolvedInventoryGrid->y
                    && dialogMouseY < resolvedInventoryGrid->y + resolvedInventoryGrid->height)
                {
                    const uint8_t gridX = static_cast<uint8_t>(std::clamp(
                        static_cast<int>((dialogMouseX - resolvedInventoryGrid->x) / gridMetrics.cellWidth),
                        0,
                        Character::InventoryWidth - 1));
                    const uint8_t gridY = static_cast<uint8_t>(std::clamp(
                        static_cast<int>((dialogMouseY - resolvedInventoryGrid->y) / gridMetrics.cellHeight),
                        0,
                        Character::InventoryHeight - 1));
                    const InventoryItem *pItem = pActiveCharacter->inventoryItemAt(gridX, gridY);

                    if (pItem != nullptr)
                    {
                        if (view.inventoryNestedOverlay().mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell)
                        {
                            hoveredHouseServiceTopicText = HouseServiceRuntime::buildSellHoverText(
                                *view.party(),
                                *view.itemTable(),
                                *view.standardItemEnchantTable(),
                                *view.specialItemEnchantTable(),
                                *pHostHouseEntry,
                                *pItem,
                                effectiveReputationForView(view));
                        }
                        else if (view.inventoryNestedOverlay().mode
                            == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify)
                        {
                            hoveredHouseServiceTopicText = HouseServiceRuntime::buildIdentifyHoverText(
                                *view.party(),
                                *view.itemTable(),
                                *view.standardItemEnchantTable(),
                                *view.specialItemEnchantTable(),
                                *pHostHouseEntry,
                                *pItem,
                                effectiveReputationForView(view));
                        }
                        else if (view.inventoryNestedOverlay().mode
                            == GameplayUiController::InventoryNestedOverlayMode::ShopRepair)
                        {
                            const std::string hoverText = HouseServiceRuntime::buildRepairHoverText(
                                *view.party(),
                                *view.itemTable(),
                                *view.standardItemEnchantTable(),
                                *view.specialItemEnchantTable(),
                                *pHostHouseEntry,
                                *pItem,
                                effectiveReputationForView(view));

                            if (!hoverText.empty())
                            {
                                hoveredHouseServiceTopicText = hoverText;
                            }
                        }
                    }
                }
            }
        }
    }

    const std::vector<std::string> orderedDialogueLayoutIds = view.sortedHudLayoutIdsForScreen("Dialogue");

    for (const std::string &layoutId : orderedDialogueLayoutIds)
    {
        const GameplayScreenRuntime::HudLayoutElement *pLayout = view.findHudLayoutElement(layoutId);

        if (pLayout == nullptr || toLowerCopy(pLayout->screen) != "dialogue")
        {
            continue;
        }

        renderDialogueTextureElement(
            view,
            layoutId,
            width,
            height,
            dialogMouseX,
            dialogMouseY,
            showDialogueTextFrame,
            showDialogueVideoArea,
            showEventDialogPanel,
            pHostHouseEntry,
            pParty,
            renderAboveHud);
    }

    renderHouseShopOverlay(
        view,
        width,
        height,
        dialogMouseX,
        dialogMouseY,
        dialogueResponseHintText,
        renderAboveHud);
    view.interactionState().dialogueStatusHint = dialogueResponseHintText;

    if (view.activeEventDialog().presentation == EventDialogPresentation::Transition
        && !view.activeEventDialog().actions.empty())
    {
        renderDialogueLabelById(
            view,
            "DialogueOkButton",
            view.activeEventDialog().actions[0].label,
            width,
            height,
            renderAboveHud);
    }

    renderDialogueLabelById(
        view,
        "DialogueGoldLabel",
        pParty != nullptr ? std::to_string(pParty->gold()) : "",
        width,
        height,
        renderAboveHud);
    renderDialogueLabelById(
        view,
        "DialogueFoodLabel",
        pParty != nullptr ? std::to_string(pParty->food()) : "",
        width,
        height,
        renderAboveHud);
    renderDialogueEventPanel(
        view,
        width,
        height,
        dialogMouseX,
        dialogMouseY,
        renderAboveHud,
        showEventDialogPanel,
        residentSelectionMode,
        pHostHouseEntry,
        hoveredHouseServiceTopicText,
        suppressServiceTopicsForShopOverlay);
    if (!isTransitionDialog)
    {
        renderDialogueBodyText(
            view,
            width,
            height,
            renderAboveHud,
            dialogueBodyLines);
    }

    view.clearHudLayoutRuntimeHeightOverrides();
}

bool GameplayDialogueRenderer::shouldRenderInCurrentPass(bool renderAboveHud, int hudZThreshold, int zIndex)
{
    return renderAboveHud ? zIndex >= hudZThreshold : zIndex < hudZThreshold;
}

bool GameplayDialogueRenderer::isDialogueFrameSubtree(GameplayScreenRuntime &view, const std::string &layoutId)
{
    std::string currentLayoutId = layoutId;

    while (!currentLayoutId.empty())
    {
        if (toLowerCopy(currentLayoutId) == "dialogueframe")
        {
            return true;
        }

        const GameplayScreenRuntime::HudLayoutElement *pCurrentLayout = view.findHudLayoutElement(currentLayoutId);

        if (pCurrentLayout == nullptr || pCurrentLayout->parentId.empty())
        {
            break;
        }

        currentLayoutId = pCurrentLayout->parentId;
    }

    return false;
}

void GameplayDialogueRenderer::renderBlackoutBackdrop(
    GameplayScreenRuntime &view,
    int screenWidth,
    int screenHeight,
    float viewportX,
    float viewportWidth)
{
    (void)viewportX;
    (void)viewportWidth;
    view.renderViewportSidePanels(screenWidth, screenHeight, "obsidian_reading_surface");
}

void GameplayDialogueRenderer::updateHouseShopHoverTopicText(
    GameplayScreenRuntime &view,
    int width,
    int height,
    float dialogMouseX,
    float dialogMouseY,
    std::optional<std::string> &hoveredHouseServiceTopicText)
{
    if (!view.houseShopOverlay().active
        || view.party() == nullptr
        || view.worldRuntime() == nullptr
        || view.itemTable() == nullptr
        || view.houseTable() == nullptr)
    {
        return;
    }

    const HouseEntry *pHouseEntry = view.houseTable()->get(view.houseShopOverlay().houseId);

    if (pHouseEntry == nullptr)
    {
        return;
    }

    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedFrame =
        view.resolveHouseShopOverlayFrame(width, height);

    if (!resolvedFrame)
    {
        return;
    }

    std::optional<HouseStockMode> stockMode;

    switch (view.houseShopOverlay().mode)
    {
        case GameplayUiController::HouseShopMode::BuyStandard:
            stockMode = HouseStockMode::ShopStandard;
            break;

        case GameplayUiController::HouseShopMode::BuySpecial:
            stockMode = HouseStockMode::ShopSpecial;
            break;

        case GameplayUiController::HouseShopMode::BuySpellbooks:
            stockMode = HouseStockMode::GuildSpellbooks;
            break;

        case GameplayUiController::HouseShopMode::None:
        default:
            return;
    }

    Party &party = *view.party();
    const std::vector<InventoryItem> &stock = HouseServiceRuntime::ensureStock(
        party,
        *view.itemTable(),
        *view.standardItemEnchantTable(),
        *view.specialItemEnchantTable(),
        *pHouseEntry,
        view.worldRuntime()->gameMinutes(),
        *stockMode);
    const size_t slotCount = HouseServiceRuntime::slotCountForStockMode(*pHouseEntry, *stockMode);
    const HouseShopVisualLayout overlayLayout =
        buildHouseShopVisualLayout(
            *pHouseEntry,
            view.houseShopOverlay().mode == GameplayUiController::HouseShopMode::BuySpellbooks);

    for (size_t slotIndex = 0;
         slotIndex < slotCount && slotIndex < stock.size() && slotIndex < overlayLayout.slots.size();
         ++slotIndex)
    {
        const InventoryItem &item = stock[slotIndex];

        if (item.objectDescriptionId == 0)
        {
            continue;
        }

        const ItemDefinition *pItemDefinition = view.itemTable()->get(item.objectDescriptionId);

        if (pItemDefinition == nullptr || pItemDefinition->iconName.empty())
        {
            continue;
        }

        const std::optional<GameplayScreenRuntime::HudTextureHandle> itemTexture =
            view.gameplayUiRuntime().ensureItemIconTextureLoaded(pItemDefinition->iconName);

        if (!itemTexture)
        {
            continue;
        }

        int opaqueTextureWidth = itemTexture->width;
        int opaqueTextureHeight = itemTexture->height;
        int opaqueMinX = 0;
        int opaqueMinY = 0;
        int opaqueMaxX = itemTexture->width - 1;
        int opaqueMaxY = itemTexture->height - 1;
        view.gameplayUiRuntime().tryGetOpaqueHudTextureBounds(
            pItemDefinition->iconName,
            opaqueTextureWidth,
            opaqueTextureHeight,
            opaqueMinX,
            opaqueMinY,
            opaqueMaxX,
            opaqueMaxY);
        const HouseShopItemDrawRect drawRect = resolveHouseShopItemDrawRect(
            resolvedFrame->x,
            resolvedFrame->y,
            static_cast<float>(resolvedFrame->width),
            static_cast<float>(resolvedFrame->height),
            resolvedFrame->scale,
            overlayLayout.slots[slotIndex],
            slotIndex,
            itemTexture->width,
            itemTexture->height,
            opaqueMinY,
            opaqueMaxY);

        if (dialogMouseX >= drawRect.x
            && dialogMouseX < drawRect.x + drawRect.width
            && dialogMouseY >= drawRect.y
            && dialogMouseY < drawRect.y + drawRect.height)
        {
            hoveredHouseServiceTopicText =
                HouseServiceRuntime::buildBuyHoverText(
                    party,
                    *view.itemTable(),
                    *view.standardItemEnchantTable(),
                    *view.specialItemEnchantTable(),
                    *pHouseEntry,
                    item,
                    effectiveReputationForView(view));
            return;
        }
    }
}

void GameplayDialogueRenderer::renderHouseShopOverlay(
    GameplayScreenRuntime &view,
    int width,
    int height,
    float dialogMouseX,
    float dialogMouseY,
    std::string &dialogueResponseHintText,
    bool renderAboveHud)
{
    if (!view.houseShopOverlay().active
        || view.party() == nullptr
        || view.worldRuntime() == nullptr
        || view.itemTable() == nullptr
        || view.houseTable() == nullptr)
    {
        return;
    }

    const HouseEntry *pHouseEntry = view.houseTable()->get(view.houseShopOverlay().houseId);

    if (pHouseEntry == nullptr)
    {
        return;
    }

    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedFrame =
        view.resolveHouseShopOverlayFrame(width, height);

    if (!resolvedFrame)
    {
        return;
    }

    const GameplayScreenRuntime::HudLayoutElement *pFrameLayout = view.findHudLayoutElement("DialogueShopOverlayFrame");
    const int hudZThreshold = view.defaultHudLayoutZIndexForScreen("OutdoorHud");

    if (pFrameLayout != nullptr && shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pFrameLayout->zIndex))
    {
        const HouseShopVisualLayout overlayLayout =
            buildHouseShopVisualLayout(
                *pHouseEntry,
                view.houseShopOverlay().mode == GameplayUiController::HouseShopMode::BuySpellbooks);
        const std::string &backgroundAsset = overlayLayout.backgroundAsset;

        if (!backgroundAsset.empty())
        {
            const std::optional<GameplayScreenRuntime::HudTextureHandle> frameTexture =
                view.gameplayUiRuntime().ensureHudTextureLoaded(backgroundAsset);

            if (frameTexture)
            {
                view.submitHudTexturedQuad(
                    *frameTexture,
                    resolvedFrame->x,
                    resolvedFrame->y,
                    resolvedFrame->width,
                    resolvedFrame->height);
            }
        }
    }

    std::optional<HouseStockMode> stockMode;

    switch (view.houseShopOverlay().mode)
    {
        case GameplayUiController::HouseShopMode::BuyStandard:
            stockMode = HouseStockMode::ShopStandard;
            break;

        case GameplayUiController::HouseShopMode::BuySpecial:
            stockMode = HouseStockMode::ShopSpecial;
            break;

        case GameplayUiController::HouseShopMode::BuySpellbooks:
            stockMode = HouseStockMode::GuildSpellbooks;
            break;

        case GameplayUiController::HouseShopMode::None:
        default:
            return;
    }

    Party &party = *view.party();
    const std::vector<InventoryItem> &stock = HouseServiceRuntime::ensureStock(
        party,
        *view.itemTable(),
        *view.standardItemEnchantTable(),
        *view.specialItemEnchantTable(),
        *pHouseEntry,
        view.worldRuntime()->gameMinutes(),
        *stockMode);
    const size_t slotCount = HouseServiceRuntime::slotCountForStockMode(*pHouseEntry, *stockMode);
    const HouseShopVisualLayout overlayLayout =
        buildHouseShopVisualLayout(
            *pHouseEntry,
            view.houseShopOverlay().mode == GameplayUiController::HouseShopMode::BuySpellbooks);
    bool hoveredItem = false;

    for (size_t slotIndex = 0;
         slotIndex < slotCount && slotIndex < stock.size() && slotIndex < overlayLayout.slots.size();
         ++slotIndex)
    {
        const InventoryItem &item = stock[slotIndex];

        if (item.objectDescriptionId == 0)
        {
            continue;
        }

        const ItemDefinition *pItemDefinition = view.itemTable()->get(item.objectDescriptionId);

        if (pItemDefinition == nullptr || pItemDefinition->iconName.empty())
        {
            continue;
        }

        const std::optional<GameplayScreenRuntime::HudTextureHandle> itemTexture =
            view.gameplayUiRuntime().ensureItemIconTextureLoaded(pItemDefinition->iconName);

        if (!itemTexture)
        {
            continue;
        }

        int opaqueTextureWidth = itemTexture->width;
        int opaqueTextureHeight = itemTexture->height;
        int opaqueMinX = 0;
        int opaqueMinY = 0;
        int opaqueMaxX = itemTexture->width - 1;
        int opaqueMaxY = itemTexture->height - 1;
        view.gameplayUiRuntime().tryGetOpaqueHudTextureBounds(
            pItemDefinition->iconName,
            opaqueTextureWidth,
            opaqueTextureHeight,
            opaqueMinX,
            opaqueMinY,
            opaqueMaxX,
            opaqueMaxY);
        const HouseShopItemDrawRect drawRect = resolveHouseShopItemDrawRect(
            resolvedFrame->x,
            resolvedFrame->y,
            static_cast<float>(resolvedFrame->width),
            static_cast<float>(resolvedFrame->height),
            resolvedFrame->scale,
            overlayLayout.slots[slotIndex],
            slotIndex,
            itemTexture->width,
            itemTexture->height,
            opaqueMinY,
            opaqueMaxY);
        view.submitHudTexturedQuad(*itemTexture, drawRect.x, drawRect.y, drawRect.width, drawRect.height);

        GameplayRenderedInspectableHudItem inspectableItem = {};
        inspectableItem.objectDescriptionId = item.objectDescriptionId;
        inspectableItem.hasItemState = true;
        inspectableItem.itemState = item;
        inspectableItem.textureName = pItemDefinition->iconName;
        inspectableItem.textureUsesItemIconTransparency = true;
        inspectableItem.x = drawRect.x;
        inspectableItem.y = drawRect.y;
        inspectableItem.width = drawRect.width;
        inspectableItem.height = drawRect.height;
        view.addRenderedInspectableHudItem(inspectableItem);

        if (dialogMouseX >= drawRect.x
            && dialogMouseX < drawRect.x + drawRect.width
            && dialogMouseY >= drawRect.y
            && dialogMouseY < drawRect.y + drawRect.height)
        {
            hoveredItem = true;
        }
    }

    if (!hoveredItem && (view.statusBarEventRemainingSeconds() <= 0.0f || view.statusBarEventText().empty()))
    {
        dialogueResponseHintText = "LMB buy  RMB inspect  Esc close";
    }
}

void GameplayDialogueRenderer::renderDialogueTextureElement(
    GameplayScreenRuntime &view,
    const std::string &layoutId,
    int width,
    int height,
    float dialogMouseX,
    float dialogMouseY,
    bool showDialogueTextFrame,
    bool showDialogueVideoArea,
    bool showEventDialogPanel,
    const HouseEntry *pHostHouseEntry,
    const Party *pParty,
    bool renderAboveHud)
{
    const GameplayScreenRuntime::HudLayoutElement *pLayout = view.findHudLayoutElement(layoutId);

    if (pLayout == nullptr || !pLayout->visible || toLowerCopy(pLayout->screen) != "dialogue")
    {
        return;
    }

    const std::string normalizedLayoutId = toLowerCopy(layoutId);

    if (normalizedLayoutId == "dialoguenpcportrait"
        || normalizedLayoutId == "dialoguetext"
        || normalizedLayoutId == "dialogueshopoverlayframe")
    {
        return;
    }

    if (!showDialogueTextFrame && isDialogueFrameSubtree(view, layoutId))
    {
        return;
    }

    if (normalizedLayoutId == "dialoguevideoarea" && !showDialogueVideoArea)
    {
        return;
    }

    if (normalizedLayoutId == "dialogueokbutton"
        && view.activeEventDialog().presentation != EventDialogPresentation::Transition)
    {
        return;
    }

    if (normalizedLayoutId == "dialogueeventdialog" && !showEventDialogPanel)
    {
        return;
    }

    const int hudZThreshold = view.defaultHudLayoutZIndexForScreen("OutdoorHud");

    if (!shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pLayout->zIndex))
    {
        return;
    }

    std::optional<GameplayScreenRuntime::HudTextureHandle> baseTexture;

    if ((pLayout->width <= 0.0f || pLayout->height <= 0.0f) && !pLayout->primaryAsset.empty())
    {
        baseTexture = view.gameplayUiRuntime().ensureHudTextureLoaded(pLayout->primaryAsset);
    }

    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved = view.resolveHudLayoutElement(
        layoutId,
        width,
        height,
        pLayout->width > 0.0f
            ? pLayout->width
            : (baseTexture ? static_cast<float>(baseTexture->width) : 0.0f),
        pLayout->height > 0.0f
            ? pLayout->height
            : (baseTexture ? static_cast<float>(baseTexture->height) : 0.0f));

    if (!resolved)
    {
        return;
    }

    if (normalizedLayoutId == "dialogueframe")
    {
        GameplayResolvedHudLayoutElement panel = *resolved;
        panel.height -= 114 * panel.scale;
        GameplayUiSkin::renderPanel(view, panel, true);
        return;
    }
    if (pLayout->primaryAsset.starts_with("obsidian_frame_"))
    {
        return;
    }
    if (normalizedLayoutId == "dialoguevideoarea")
    {
        renderDialogueVideoArea(
            view,
            pHostHouseEntry,
            pParty,
            resolved->x,
            resolved->y,
            resolved->width,
            resolved->height);
        return;
    }

    if (pLayout->interactive && !pLayout->labelText.empty()
        && pLayout->labelText.find('{') == std::string::npos)
    {
        GameplayUiSkin::renderButton(view, layoutId, width, height);
        return;
    }
    const PointerRenderInput pointerInput = pointerRenderInput(view);
    const std::string *pAssetName =
        view.resolveInteractiveAssetName(
            *pLayout,
            *resolved,
            dialogMouseX,
            dialogMouseY,
            pointerInput.isLeftMousePressed);

    if (pAssetName->empty())
    {
        return;
    }

    const std::optional<GameplayScreenRuntime::HudTextureHandle> texture = view.gameplayUiRuntime().ensureHudTextureLoaded(*pAssetName);

    if (!texture)
    {
        return;
    }

    submitTextureHandleQuad(view, texture->textureHandle, resolved->x, resolved->y, resolved->width, resolved->height);
}

void GameplayDialogueRenderer::renderDialogueLabelById(
    GameplayScreenRuntime &view,
    const std::string &layoutId,
    const std::string &label,
    int width,
    int height,
    bool renderAboveHud)
{
    const GameplayScreenRuntime::HudLayoutElement *pLayout = view.findHudLayoutElement(layoutId);

    if (pLayout == nullptr || !pLayout->visible || toLowerCopy(pLayout->screen) != "dialogue")
    {
        return;
    }

    const int hudZThreshold = view.defaultHudLayoutZIndexForScreen("OutdoorHud");

    if (!shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pLayout->zIndex))
    {
        return;
    }

    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved = view.resolveHudLayoutElement(
        layoutId,
        width,
        height,
        pLayout->width,
        pLayout->height);

    if (!resolved)
    {
        return;
    }

    view.renderLayoutLabel(*pLayout, *resolved, label);
}

void GameplayDialogueRenderer::renderDialogueEventPanel(
    GameplayScreenRuntime &view,
    int width,
    int height,
    float dialogMouseX,
    float dialogMouseY,
    bool renderAboveHud,
    bool showEventDialogPanel,
    bool isResidentSelectionMode,
    const HouseEntry *pHostHouseEntry,
    const std::optional<std::string> &hoveredHouseServiceTopicText,
    bool suppressServiceTopicsForShopOverlay)
{
    if (!showEventDialogPanel)
    {
        return;
    }

    const GameplayScreenRuntime::HudLayoutElement *pEventDialogLayout = view.findHudLayoutElement("DialogueEventDialog");
    const GameplayScreenRuntime::HudLayoutElement *pNpcPortraitLayout = view.findHudLayoutElement("DialogueNpcPortrait");
    const GameplayScreenRuntime::HudLayoutElement *pHouseTitleLayout = view.findHudLayoutElement("DialogueHouseTitle");
    const GameplayScreenRuntime::HudLayoutElement *pNpcNameLayout = view.findHudLayoutElement("DialogueNpcName");
    const GameplayScreenRuntime::HudLayoutElement *pTopicRowLayout = view.findHudLayoutElement("DialogueTopicRow_1");

    if (pEventDialogLayout == nullptr)
    {
        return;
    }

    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedEventDialog = view.resolveHudLayoutElement(
        "DialogueEventDialog",
        width,
        height,
        pEventDialogLayout->width,
        pEventDialogLayout->height);
    const int hudZThreshold = view.defaultHudLayoutZIndexForScreen("OutdoorHud");

    if (!resolvedEventDialog
        || !shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pEventDialogLayout->zIndex))
    {
        return;
    }

    const float panelScale = resolvedEventDialog->scale;
    const float panelPaddingX = 10.0f * panelScale;
    const float panelPaddingY = 10.0f * panelScale;
    const float titleBoundsInset = 4.0f * panelScale;
    const float panelInnerX = resolvedEventDialog->x + panelPaddingX;
    const float panelInnerY = resolvedEventDialog->y + panelPaddingY;
    const float panelInnerWidth = resolvedEventDialog->width - panelPaddingX * 2.0f;
    const float titleBoundsX = std::round(resolvedEventDialog->x + titleBoundsInset);
    const float titleBoundsWidth = std::max(1.0f, resolvedEventDialog->width - titleBoundsInset * 2.0f);
    const float sectionGap = 8.0f * panelScale;
    const float houseTitleToPortraitGap = 2.0f * panelScale;
    float contentY = panelInnerY;
    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedPortraitTemplate =
        pNpcPortraitLayout != nullptr
        ? view.resolveHudLayoutElement(
            "DialogueNpcPortrait",
            width,
            height,
            pNpcPortraitLayout->width,
            pNpcPortraitLayout->height)
        : std::nullopt;
    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedNpcNameTemplate =
        pNpcNameLayout != nullptr
        ? view.resolveHudLayoutElement(
            "DialogueNpcName",
            width,
            height,
            pNpcNameLayout->width,
            pNpcNameLayout->height)
        : std::nullopt;
    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedTopicRowTemplate =
        pTopicRowLayout != nullptr
        ? view.resolveHudLayoutElement(
            "DialogueTopicRow_1",
            width,
            height,
            pTopicRowLayout->width,
            pTopicRowLayout->height)
        : std::nullopt;
    const GameplayScreenRuntime::HudLayoutElement *pEffectiveHouseTitleLayout =
        pHouseTitleLayout != nullptr ? pHouseTitleLayout : pNpcNameLayout;
    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedHouseTitleTemplate =
        pEffectiveHouseTitleLayout != nullptr
        ? view.resolveHudLayoutElement(
            pEffectiveHouseTitleLayout->id,
            width,
            height,
            pEffectiveHouseTitleLayout->width,
            pEffectiveHouseTitleLayout->height)
        : std::nullopt;
    const float portraitAreaWidth = resolvedPortraitTemplate ? resolvedPortraitTemplate->width : 80.0f * panelScale;
    const float portraitAreaHeight = resolvedPortraitTemplate ? resolvedPortraitTemplate->height : 80.0f * panelScale;
    const float portraitBorderWidth = portraitAreaWidth;
    const float portraitBorderHeight = portraitAreaHeight;
    const float portraitAreaX = resolvedPortraitTemplate
        ? resolvedPortraitTemplate->x
        : std::round(panelInnerX + (panelInnerWidth - portraitAreaWidth) * 0.5f);
    const float portraitBaseY = resolvedPortraitTemplate ? resolvedPortraitTemplate->y : panelInnerY;
    const float nameWidth = titleBoundsWidth;
    const float nameHeight = resolvedNpcNameTemplate ? resolvedNpcNameTemplate->height : 20.0f * panelScale;
    const float nameX = titleBoundsX;
    const float nameScale = resolvedNpcNameTemplate ? resolvedNpcNameTemplate->scale : panelScale;
    const float nameOffsetY = resolvedNpcNameTemplate && resolvedPortraitTemplate
        ? (resolvedNpcNameTemplate->y - resolvedPortraitTemplate->y)
        : portraitAreaHeight + 2.0f * panelScale;

    const bool isTransitionDialog =
        view.activeEventDialog().presentation == EventDialogPresentation::Transition;

    if ((pHostHouseEntry != nullptr || isTransitionDialog) && pEffectiveHouseTitleLayout != nullptr)
    {
        GameplayScreenRuntime::ResolvedHudLayoutElement resolvedHouseTitle = {};
        resolvedHouseTitle.x = titleBoundsX;
        resolvedHouseTitle.y = resolvedHouseTitleTemplate ? resolvedHouseTitleTemplate->y : contentY;
        resolvedHouseTitle.width = titleBoundsWidth;
        resolvedHouseTitle.height = resolvedHouseTitleTemplate ? resolvedHouseTitleTemplate->height : 20.0f * panelScale;
        resolvedHouseTitle.scale = resolvedHouseTitleTemplate ? resolvedHouseTitleTemplate->scale : panelScale;

        if (shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pEffectiveHouseTitleLayout->zIndex))
        {
            const std::string houseTitle =
                isTransitionDialog
                    ? view.activeEventDialog().title
                    : (!view.activeEventDialog().houseTitle.empty()
                        ? view.activeEventDialog().houseTitle
                        : pHostHouseEntry->name);
            const float renderedTitleHeight =
                renderWrappedCenteredDialogueTitle(
                    view,
                    *pEffectiveHouseTitleLayout,
                    resolvedHouseTitle,
                    houseTitle);
            resolvedHouseTitle.height = std::max(resolvedHouseTitle.height, renderedTitleHeight);
        }

        contentY += resolvedHouseTitle.height + houseTitleToPortraitGap;
    }

    if (isEmptyHouseDialog(view.activeEventDialog()))
    {
        return;
    }

    contentY = std::max(contentY, portraitBaseY);

    const auto drawEventNpcCard =
        [&view,
         pNpcNameLayout,
         nameHeight,
         nameOffsetY,
         nameScale,
         panelScale,
         portraitAreaHeight,
         portraitAreaWidth,
         portraitBorderHeight,
         portraitBorderWidth,
         renderAboveHud,
         hudZThreshold](
            float startY,
            float cardPortraitAreaX,
            float cardNameX,
            float cardNameWidth,
            const std::string &name,
            uint32_t pictureId,
            EventDialogParticipantVisual participantVisual) -> float
        {
            const float portraitY = std::round(startY);
            const float portraitX =
                std::round(cardPortraitAreaX + (portraitAreaWidth - portraitBorderWidth) * 0.5f);
            const float portraitBorderY = std::round(portraitY + (portraitAreaHeight - portraitBorderHeight) * 0.5f);
            float nextY = portraitY + portraitAreaHeight;
            std::optional<GameplayScreenRuntime::HudTextureHandle> transitionIcon;
            const bool isMapIcon = participantVisual == EventDialogParticipantVisual::MapIcon;

            if (isMapIcon && !view.activeEventDialog().participantTextureName.empty())
            {
                transitionIcon =
                    view.gameplayUiRuntime().ensureHudTextureLoaded(view.activeEventDialog().participantTextureName);
            }

            if (!isMapIcon && pictureId > 0)
            {
                // Keep the native portrait aperture; scale the shared carved frame to its four-unit rim.
                GameplayUiSkin::renderPanel(view,
                    {portraitX, portraitBorderY, portraitBorderWidth, portraitBorderHeight, panelScale}, false, 0.35f);
            }

            if (isMapIcon)
            {
                if (transitionIcon)
                {
                    const float imageWidth = static_cast<float>(transitionIcon->width) * panelScale;
                    const float imageHeight = static_cast<float>(transitionIcon->height) * panelScale;
                    const float iconX = std::round(cardPortraitAreaX + (portraitAreaWidth - imageWidth) * 0.5f);
                    const float iconY = std::round(portraitY);

                    submitTextureHandleQuadUv(
                        view,
                        transitionIcon->textureHandle,
                        iconX,
                        iconY,
                        imageWidth,
                        imageHeight,
                        0.0f,
                        0.0f,
                        1.0f,
                        1.0f);
                    nextY = iconY + imageHeight;
                }
            }
            else if (pictureId > 0)
            {
                char textureName[16] = {};
                std::snprintf(textureName, sizeof(textureName), "npc%04u", pictureId);
                const std::optional<GameplayScreenRuntime::HudTextureHandle> portraitTexture =
                    view.gameplayUiRuntime().ensureHudTextureLoaded(textureName);

                if (portraitTexture)
                {
                    const float portraitScaleX = portraitBorderWidth / EventNpcFrameNativeWidth;
                    const float portraitScaleY = portraitBorderHeight / EventNpcFrameNativeHeight;
                    const float innerX = std::round(portraitX + EventNpcPortraitNativeX * portraitScaleX);
                    const float innerY = std::round(portraitBorderY + EventNpcPortraitNativeY * portraitScaleY);
                    const float drawWidth = std::round(EventNpcPortraitNativeWidth * portraitScaleX);
                    const float drawHeight = std::round(EventNpcPortraitNativeHeight * portraitScaleY);
                    float u0 = 0.0f;
                    float v0 = 0.0f;
                    float u1 = 1.0f;
                    float v1 = 1.0f;

                    if (portraitTexture->width == static_cast<int>(EventNpcPortraitNativeWidth)
                        && portraitTexture->height == static_cast<int>(EventNpcPortraitNativeHeight))
                    {
                        u0 = EventNpcPortraitUvCropX / EventNpcPortraitNativeWidth;
                        v0 = EventNpcPortraitUvCropY / EventNpcPortraitNativeHeight;
                        u1 = (EventNpcPortraitNativeWidth - EventNpcPortraitUvCropX) / EventNpcPortraitNativeWidth;
                        v1 = (EventNpcPortraitNativeHeight - EventNpcPortraitUvCropY) / EventNpcPortraitNativeHeight;
                    }

                    submitTextureHandleQuadUv(
                        view,
                        portraitTexture->textureHandle,
                        innerX,
                        innerY,
                        drawWidth,
                        drawHeight,
                        u0,
                        v0,
                        u1,
                        v1);
                }
            }

            if (pNpcNameLayout != nullptr
                && !name.empty()
                && shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pNpcNameLayout->zIndex))
            {
                GameplayScreenRuntime::ResolvedHudLayoutElement resolvedName = {};
                resolvedName.x = cardNameX;
                resolvedName.y = portraitY + nameOffsetY;
                resolvedName.width = cardNameWidth;
                resolvedName.height = nameHeight;
                resolvedName.scale = nameScale;
                const float renderedNameHeight =
                    renderWrappedCenteredDialogueTitle(view, *pNpcNameLayout, resolvedName, name);
                nextY = resolvedName.y + std::max(resolvedName.height, renderedNameHeight);
            }

            return nextY;
        };

    if (isResidentSelectionMode)
    {
        const size_t residentCount = view.activeEventDialog().actions.size();
        const bool useTwoColumns = residentCount > 3;
        const size_t columnCount = useTwoColumns ? 2u : 1u;
        const float columnWidth = useTwoColumns ? panelInnerWidth / 2.0f : panelInnerWidth;
        const float rowStep = portraitAreaHeight + (useTwoColumns ? 0.0f : nameHeight) + sectionGap;
        float maxContentY = contentY;

        for (size_t actionIndex = 0; actionIndex < residentCount; ++actionIndex)
        {
            const EventDialogAction &action = view.activeEventDialog().actions[actionIndex];
            const NpcEntry *pNpc = action.kind == EventDialogActionKind::HouseResident && view.npcDialogTable()
                ? view.npcDialogTable()->getNpc(action.id)
                : nullptr;
            const uint32_t pictureId = action.participantPictureId != 0
                ? action.participantPictureId
                : (pNpc != nullptr ? pNpc->pictureId : 0);
            const size_t column = useTwoColumns ? actionIndex % columnCount : 0u;
            const size_t row = useTwoColumns ? actionIndex / columnCount : actionIndex;
            const float cardNameX = useTwoColumns ? panelInnerX + static_cast<float>(column) * columnWidth : nameX;
            const float cardNameWidth = useTwoColumns ? columnWidth : nameWidth;
            const float cardPortraitAreaX = useTwoColumns
                ? cardNameX + (columnWidth - portraitAreaWidth) * 0.5f
                : portraitAreaX;
            const float cardY = useTwoColumns ? contentY + static_cast<float>(row) * rowStep : contentY;
            const float nextY = drawEventNpcCard(
                cardY,
                cardPortraitAreaX,
                cardNameX,
                cardNameWidth,
                useTwoColumns ? std::string() : action.label,
                pictureId,
                action.participantVisual);

            if (useTwoColumns)
            {
                maxContentY = std::max(maxContentY, nextY);
            }
            else
            {
                contentY = nextY + sectionGap;
            }
        }

        if (useTwoColumns)
        {
            contentY = maxContentY + sectionGap;
        }
    }
    else
    {
        uint32_t pictureId = view.activeEventDialog().participantPictureId;

        if (pictureId == 0 && view.activeEventDialog().participantVisual == EventDialogParticipantVisual::Portrait)
        {
            const NpcEntry *pNpc =
                view.npcDialogTable() ? view.npcDialogTable()->getNpc(view.activeEventDialog().sourceId) : nullptr;
            pictureId = pNpc != nullptr
                ? pNpc->pictureId
                : (pHostHouseEntry != nullptr ? pHostHouseEntry->proprietorPictureId : 0);
        }

        contentY = drawEventNpcCard(
            contentY,
            portraitAreaX,
            nameX,
            nameWidth,
            isTransitionDialog ? std::string() : view.activeEventDialog().title,
            pictureId,
            view.activeEventDialog().participantVisual);
        contentY += isTransitionDialog ? 15.0f * panelScale : sectionGap;

        if (isTransitionDialog)
        {
            const GameplayScreenRuntime::HudLayoutElement *pTransitionTextLayout =
                pEffectiveHouseTitleLayout != nullptr ? pEffectiveHouseTitleLayout : pTopicRowLayout;

            if (pTransitionTextLayout == nullptr || view.activeEventDialog().lines.empty())
            {
                return;
            }

            const std::optional<GameplayScreenRuntime::HudFontHandle> topicFont =
                view.findHudFont(pTransitionTextLayout->fontName);

            if (!topicFont || !shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pTransitionTextLayout->zIndex))
            {
                return;
            }

            const float topicFontScale = snappedHudFontScale(
                resolvedHouseTitleTemplate ? resolvedHouseTitleTemplate->scale : panelScale);
            const float topicLineHeight = static_cast<float>(topicFont->fontHeight) * topicFontScale;
            const float textWidth = std::max(0.0f, panelInnerWidth - 5.0f * panelScale);
            const float textWrapWidth = std::max(0.0f, textWidth / std::max(1.0f, topicFontScale));
            std::vector<std::string> wrappedLines;

            for (const std::string &sourceLine : view.activeEventDialog().lines)
            {
                std::vector<std::string> lineParts = view.wrapHudTextToWidth(*topicFont, sourceLine, textWrapWidth);

                if (lineParts.empty())
                {
                    lineParts.push_back(sourceLine);
                }

                wrappedLines.insert(wrappedLines.end(), lineParts.begin(), lineParts.end());
            }

            const float availableBottom = resolvedEventDialog->y + resolvedEventDialog->height - panelPaddingY;
            float lineY = contentY;
            GameplayScreenRuntime::HudLayoutElement transitionTextLayout = *pTransitionTextLayout;
            transitionTextLayout.textAlignY = UiLayoutManager::TextAlignY::Top;

            for (const std::string &line : wrappedLines)
            {
                if (lineY + topicLineHeight > availableBottom)
                {
                    break;
                }

                GameplayScreenRuntime::ResolvedHudLayoutElement resolvedLine = {};
                resolvedLine.x = std::round(panelInnerX + (panelInnerWidth - textWidth) * 0.5f);
                resolvedLine.y = std::round(lineY);
                resolvedLine.width = textWidth;
                resolvedLine.height = topicLineHeight;
                resolvedLine.scale = topicFontScale;
                view.renderLayoutLabel(transitionTextLayout, resolvedLine, line);
                lineY += topicLineHeight;
            }

            return;
        }

        if (pTopicRowLayout != nullptr
            && ((!suppressServiceTopicsForShopOverlay && !view.activeEventDialog().actions.empty())
                || hoveredHouseServiceTopicText.has_value()))
        {
            const std::optional<GameplayScreenRuntime::HudFontHandle> topicFont =
                view.findHudFont(pTopicRowLayout->fontName);
            const float topicFontScale = (resolvedTopicRowTemplate ? resolvedTopicRowTemplate->scale : panelScale)
                * pTopicRowLayout->textScale;
            const float topicLineHeight = topicFont
                ? static_cast<float>(topicFont->fontHeight) * topicFontScale
                : 20.0f * panelScale;
            const float topicWrapWidth = 140.0f * (resolvedTopicRowTemplate ? resolvedTopicRowTemplate->scale : panelScale);
            const float topicTextWidthScaled = std::max(
                0.0f,
                std::min(
                    resolvedTopicRowTemplate ? resolvedTopicRowTemplate->width : panelInnerWidth,
                    topicWrapWidth)
                        - std::abs(pTopicRowLayout->textPadX * topicFontScale) * 2.0f
                        - 4.0f * topicFontScale);
            const float topicTextWidth = std::max(0.0f, topicTextWidthScaled / std::max(0.01f, topicFontScale));
            const float rowGap = 4.0f * panelScale;
            const bool showHoveredShopTopic = hoveredHouseServiceTopicText.has_value();
            const size_t visibleActionCount =
                showHoveredShopTopic
                ? 1
                : (suppressServiceTopicsForShopOverlay ? 0 : std::min<size_t>(view.activeEventDialog().actions.size(), 5));
            const float availableTop = contentY;
            const float availableHeight =
                resolvedEventDialog->y + resolvedEventDialog->height - panelPaddingY - availableTop;
            std::vector<std::vector<std::string>> wrappedActionLabels;
            std::vector<float> actionRowHeights;
            std::vector<float> actionPressHeights;
            wrappedActionLabels.reserve(visibleActionCount);
            actionRowHeights.reserve(visibleActionCount);
            actionPressHeights.reserve(visibleActionCount);

            for (size_t actionIndex = 0; actionIndex < visibleActionCount; ++actionIndex)
            {
                const std::string &label = showHoveredShopTopic
                    ? *hoveredHouseServiceTopicText
                    : view.activeEventDialog().actions[actionIndex].label;
                std::vector<std::string> wrappedLines = topicFont
                    ? view.wrapHudTextToWidth(*topicFont, label, topicTextWidth)
                    : std::vector<std::string>{label};

                if (wrappedLines.empty())
                {
                    wrappedLines.push_back(label);
                }

                const float minimumRowHeight = resolvedTopicRowTemplate
                    ? resolvedTopicRowTemplate->height
                    : pTopicRowLayout->height * panelScale;
                const float wrappedRowHeight = static_cast<float>(wrappedLines.size()) * topicLineHeight;
                wrappedActionLabels.push_back(std::move(wrappedLines));
                actionRowHeights.push_back(std::max(minimumRowHeight, wrappedRowHeight));
                actionPressHeights.push_back(wrappedRowHeight);
            }

            float totalHeight = 0.0f;

            for (size_t actionIndex = 0; actionIndex < actionRowHeights.size(); ++actionIndex)
            {
                totalHeight += actionRowHeights[actionIndex];

                if (actionIndex + 1 < actionRowHeights.size())
                {
                    totalHeight += rowGap;
                }
            }

            const float topicListCenterOffsetY = 8.0f * panelScale;
            float rowY = availableTop + std::max(0.0f, (availableHeight - totalHeight) * 0.5f) - topicListCenterOffsetY;

            for (size_t actionIndex = 0; actionIndex < visibleActionCount; ++actionIndex)
            {
                GameplayScreenRuntime::ResolvedHudLayoutElement resolvedRow = {};
                resolvedRow.x = resolvedTopicRowTemplate ? resolvedTopicRowTemplate->x : panelInnerX;
                resolvedRow.y = rowY;
                resolvedRow.width = resolvedTopicRowTemplate ? resolvedTopicRowTemplate->width : panelInnerWidth;
                resolvedRow.height = actionRowHeights[actionIndex];
                resolvedRow.scale = resolvedTopicRowTemplate ? resolvedTopicRowTemplate->scale : panelScale;

                if (shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pTopicRowLayout->zIndex))
                {
                    const float pressAreaInsetY = 2.0f * panelScale;
                    const float pressAreaHeight =
                        std::min(
                            resolvedRow.height,
                            std::max(topicLineHeight, actionPressHeights[actionIndex]) + pressAreaInsetY * 2.0f);
                    const float pressAreaY = resolvedRow.y + (resolvedRow.height - pressAreaHeight) * 0.5f;
                    const bool isHovered = !showHoveredShopTopic
                        && dialogMouseX >= resolvedRow.x
                        && dialogMouseX < resolvedRow.x + resolvedRow.width
                        && dialogMouseY >= pressAreaY
                        && dialogMouseY < pressAreaY + pressAreaHeight;

                    if (topicFont)
                    {
                        float lineY = pressAreaY;
                        GameplayScreenRuntime::HudLayoutElement hoveredTopicRowLayout = *pTopicRowLayout;

                        if (isHovered)
                        {
                            hoveredTopicRowLayout.textColorAbgr = HoveredDialogueTopicTextColorAbgr;
                        }

                        for (const std::string &wrappedLine : wrappedActionLabels[actionIndex])
                        {
                            GameplayScreenRuntime::ResolvedHudLayoutElement resolvedLine = resolvedRow;
                            resolvedLine.y = lineY;
                            resolvedLine.height = topicLineHeight;
                            view.renderLayoutLabel(
                                isHovered ? hoveredTopicRowLayout : *pTopicRowLayout,
                                resolvedLine,
                                wrappedLine);
                            lineY += topicLineHeight;
                        }
                    }
                    else
                    {
                        GameplayScreenRuntime::HudLayoutElement hoveredTopicRowLayout = *pTopicRowLayout;

                        if (isHovered)
                        {
                            hoveredTopicRowLayout.textColorAbgr = HoveredDialogueTopicTextColorAbgr;
                        }

                        view.renderLayoutLabel(
                            isHovered ? hoveredTopicRowLayout : *pTopicRowLayout,
                            resolvedRow,
                            showHoveredShopTopic
                                ? *hoveredHouseServiceTopicText
                                : view.activeEventDialog().actions[actionIndex].label);
                    }
                }

                rowY += actionRowHeights[actionIndex] + rowGap;
            }
        }
    }
}

void GameplayDialogueRenderer::renderDialogueBodyText(
    GameplayScreenRuntime &view,
    int width,
    int height,
    bool renderAboveHud,
    const std::vector<std::string> &dialogueBodyLines)
{
    if (dialogueBodyLines.empty())
    {
        return;
    }

    const GameplayScreenRuntime::HudLayoutElement *pDialogueTextLayout = view.findHudLayoutElement("DialogueText");

    if (pDialogueTextLayout == nullptr || toLowerCopy(pDialogueTextLayout->screen) != "dialogue")
    {
        return;
    }

    const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolvedText = view.resolveHudLayoutElement(
        "DialogueText",
        width,
        height,
        pDialogueTextLayout->width,
        pDialogueTextLayout->height);
    const int hudZThreshold = view.defaultHudLayoutZIndexForScreen("OutdoorHud");

    if (!resolvedText
        || !shouldRenderInCurrentPass(renderAboveHud, hudZThreshold, pDialogueTextLayout->zIndex))
    {
        return;
    }

    const std::optional<DialogueBodyTextMetrics> textMetrics =
        [&view, pDialogueTextLayout, &dialogueBodyLines, &resolvedText]() -> std::optional<DialogueBodyTextMetrics>
        {
            GameplayScreenRuntime::HudLayoutElement effectiveDialogueTextLayout = *pDialogueTextLayout;
            effectiveDialogueTextLayout.width = resolvedText->width / std::max(1.0f, resolvedText->scale);
            effectiveDialogueTextLayout.height = resolvedText->height / std::max(1.0f, resolvedText->scale);
            return calculateDialogueBodyTextMetrics(view, effectiveDialogueTextLayout, dialogueBodyLines);
        }();

    if (!textMetrics)
    {
        return;
    }

    const GameplayScreenRuntime::HudFontHandle &font = textMetrics->font;
    const float fontScale = resolvedText->scale * textMetrics->fontScale;
    const float lineHeight = dialogueTextLineAdvance(font) * fontScale;
    const float wrapWidth = (resolvedText->width - 2 * pDialogueTextLayout->textPadX * resolvedText->scale
        - DialogueTextRightInset * resolvedText->scale) / fontScale;
    std::vector<std::string> lines;
    std::string content;
    for (const std::string &source : dialogueBodyLines)
    {
        content += source + "\n";
        const std::vector<std::string> wrapped = view.wrapHudTextToWidth(font, source, wrapWidth);
        lines.insert(lines.end(), wrapped.begin(), wrapped.end());
    }
    GameplayOverlayInteractionState &interaction = view.interactionState();
    if (interaction.dialogueBodyText != content)
    {
        interaction.dialogueBodyText = std::move(content);
        interaction.dialogueBodyScrollLines = 0;
    }
    const GameplayInputFrame *pInput = view.currentGameplayInputFrame();
    if (pInput != nullptr && GameplayHudCommon::isPointerInsideResolvedElement(
        *resolvedText, pInput->pointerX, pInput->pointerY))
    {
        interaction.dialogueBodyScrollLines -= static_cast<int>(pInput->mouseWheelDelta * 3);
    }
    const int visible = std::max(1, static_cast<int>(resolvedText->height / lineHeight));
    interaction.dialogueBodyScrollLines = std::clamp(interaction.dialogueBodyScrollLines,
        0, std::max(0, static_cast<int>(lines.size()) - visible));
    const bgfx::TextureHandle main = view.ensureHudFontMainTextureColor(font, pDialogueTextLayout->textColorAbgr);
    const float x = resolvedText->x + pDialogueTextLayout->textPadX * resolvedText->scale;
    for (int i = 0; i < visible && i + interaction.dialogueBodyScrollLines < lines.size(); ++i)
    {
        const float y = resolvedText->y + i * lineHeight;
        const std::string &line = lines[i + interaction.dialogueBodyScrollLines];
        view.renderHudFontLayer(font, font.shadowTextureHandle, line, x, y, fontScale, &*resolvedText);
        view.renderHudFontLayer(font, main, line, x, y, fontScale, &*resolvedText);
    }

}

void GameplayDialogueRenderer::submitTextureHandleQuad(
    GameplayScreenRuntime &view,
    bgfx::TextureHandle textureHandle,
    float x,
    float y,
    float quadWidth,
    float quadHeight)
{
    view.submitWorldTextureQuad(textureHandle, x, y, quadWidth, quadHeight, 0.0f, 0.0f, 1.0f, 1.0f);
}

void GameplayDialogueRenderer::submitTextureHandleQuadUv(
    GameplayScreenRuntime &view,
    bgfx::TextureHandle textureHandle,
    float x,
    float y,
    float quadWidth,
    float quadHeight,
    float u0,
    float v0,
    float u1,
    float v1)
{
    view.submitWorldTextureQuad(textureHandle, x, y, quadWidth, quadHeight, u0, v0, u1, v1);
}

void GameplayDialogueRenderer::renderDialogueVideoArea(
    GameplayScreenRuntime &view,
    const HouseEntry *pHostHouseEntry,
    const Party *pParty,
    float x,
    float y,
    float quadWidth,
    float quadHeight)
{
    if (!view.renderHouseVideoFrame(x, y, quadWidth, quadHeight))
    {
        const std::optional<GameplayScreenRuntime::HudTextureHandle> videoFillTexture =
            view.gameplayUiRuntime().ensureSolidHudTextureLoaded("__dialogue_video_area_fill__", 0xa0181818u);
        const std::optional<GameplayScreenRuntime::HudTextureHandle> videoBorderTexture =
            view.gameplayUiRuntime().ensureSolidHudTextureLoaded("__dialogue_video_area_border__", 0xff505050u);

        if (videoFillTexture)
        {
            view.submitHudTexturedQuad(
                *videoFillTexture,
                x,
                y,
                quadWidth,
                quadHeight);
        }

        if (videoBorderTexture)
        {
            static constexpr float BorderThickness = 2.0f;
            view.submitHudTexturedQuad(
                *videoBorderTexture,
                x,
                y,
                quadWidth,
                BorderThickness);
            view.submitHudTexturedQuad(
                *videoBorderTexture,
                x,
                y + quadHeight - BorderThickness,
                quadWidth,
                BorderThickness);
            view.submitHudTexturedQuad(
                *videoBorderTexture,
                x,
                y,
                BorderThickness,
                quadHeight);
            view.submitHudTexturedQuad(
                *videoBorderTexture,
                x + quadWidth - BorderThickness,
                y,
                BorderThickness,
                quadHeight);
        }
    }

    renderFreeHavenCouncilBenchParticipants(view, pHostHouseEntry, pParty, x, y, quadWidth, quadHeight);
}
} // namespace OpenYAMM::Game
