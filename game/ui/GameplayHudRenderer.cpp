#include "game/ui/GameplayHudRenderer.h"

#include "game/gameplay/GameplayScreenRuntime.h"

#include <algorithm>
#include <cmath>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr const char *StatusBarFrameAsset = "Ui-FrSp";

enum class ActiveGameplayHudLayout
{
    Overlay,
    Standard,
    Widescreen
};

bool isOverlayHudState(GameplayHudScreenState hudScreenState)
{
    return hudScreenState == GameplayHudScreenState::Dialogue
        || hudScreenState == GameplayHudScreenState::Character
        || hudScreenState == GameplayHudScreenState::Chest
        || hudScreenState == GameplayHudScreenState::Spellbook
        || hudScreenState == GameplayHudScreenState::Rest
        || hudScreenState == GameplayHudScreenState::Menu
        || hudScreenState == GameplayHudScreenState::Controls
        || hudScreenState == GameplayHudScreenState::Keyboard
        || hudScreenState == GameplayHudScreenState::VideoOptions
        || hudScreenState == GameplayHudScreenState::SaveGame
        || hudScreenState == GameplayHudScreenState::LoadGame
        || hudScreenState == GameplayHudScreenState::Journal
        || hudScreenState == GameplayHudScreenState::QuickReference;
}

const char *basebarLayoutIdForHudLayout(ActiveGameplayHudLayout layout)
{
    switch (layout)
    {
    case ActiveGameplayHudLayout::Overlay:
        return "OutdoorBasebar";

    case ActiveGameplayHudLayout::Standard:
        return "OutdoorStandardBasebar";

    case ActiveGameplayHudLayout::Widescreen:
        return "OutdoorGameplayBasebar";
    }

    return "OutdoorGameplayBasebar";
}

const char *partyStripLayoutIdForHudLayout(ActiveGameplayHudLayout layout)
{
    switch (layout)
    {
    case ActiveGameplayHudLayout::Overlay:
        return "OutdoorPartyStrip";

    case ActiveGameplayHudLayout::Standard:
        return "OutdoorStandardPartyStrip";

    case ActiveGameplayHudLayout::Widescreen:
        return "OutdoorGameplayPartyStrip";
    }

    return "OutdoorGameplayPartyStrip";
}

const char *statusBarLayoutIdForHudLayout(ActiveGameplayHudLayout layout)
{
    switch (layout)
    {
    case ActiveGameplayHudLayout::Overlay:
        return "OutdoorStatusBar";

    case ActiveGameplayHudLayout::Standard:
        return "OutdoorStandardStatusBar";

    case ActiveGameplayHudLayout::Widescreen:
        return "OutdoorGameplayStatusBar";
    }

    return "OutdoorGameplayStatusBar";
}

std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolveLayout(
    GameplayScreenRuntime &context,
    const std::string &layoutId,
    float fallbackWidth,
    float fallbackHeight,
    int screenWidth,
    int screenHeight)
{
    return context.resolveHudLayoutElement(layoutId, screenWidth, screenHeight, fallbackWidth, fallbackHeight);
}

uint32_t makeAbgrColor(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha = 255)
{
    return (static_cast<uint32_t>(alpha) << 24)
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

const char *fallbackContextActionIconId(GameplayContextActionKind kind)
{
    switch (kind)
    {
    case GameplayContextActionKind::OpenChest:
    case GameplayContextActionKind::OpenDoor:
    case GameplayContextActionKind::PressButton:
    case GameplayContextActionKind::UseLever:
    case GameplayContextActionKind::GenericEvent:
    case GameplayContextActionKind::EnterHouse:
        return "use";
    case GameplayContextActionKind::Talk:
    case GameplayContextActionKind::PickUpItem:
    case GameplayContextActionKind::LootCorpse:
    case GameplayContextActionKind::None:
        break;
    }

    return "interact";
}

std::optional<GameplayHudTextureHandle> loadContextActionIcon(
    GameplayScreenRuntime &context,
    const GameplayContextAction &action,
    bool pressed)
{
    const char *pSuffix = pressed ? "_pressed" : "_default";
    const std::vector<std::string> candidates = {
        action.iconId + pSuffix,
        std::string(fallbackContextActionIconId(action.kind)) + pSuffix,
        std::string(fallbackContextActionIconId(action.kind)) + "_default",
        "interact_default",
    };

    for (const std::string &candidate : candidates)
    {
        const std::optional<GameplayHudTextureHandle> texture =
            context.gameplayUiRuntime().ensureHudTextureLoaded(candidate);

        if (texture)
        {
            return texture;
        }
    }

    return std::nullopt;
}

std::string fitContextActionLabel(
    GameplayScreenRuntime &context,
    const std::string &fontName,
    const std::string &text,
    float maxWidth,
    float textScale)
{
    if (text.empty() || context.measureHudTextWidth(fontName, text) * textScale <= maxWidth)
    {
        return text;
    }

    std::string fitted = text;

    while (fitted.size() > 4)
    {
        fitted.pop_back();
        const std::string candidate = fitted + "...";

        if (context.measureHudTextWidth(fontName, candidate) * textScale <= maxWidth)
        {
            return candidate;
        }
    }

    return "...";
}

std::string trimContextActionLabelPart(const std::string &text)
{
    const size_t begin = text.find_first_not_of(' ');

    if (begin == std::string::npos)
    {
        return "";
    }

    const size_t end = text.find_last_not_of(' ');
    return text.substr(begin, end - begin + 1);
}

std::vector<std::string> fitContextActionLabelLines(
    GameplayScreenRuntime &context,
    const std::string &fontName,
    const std::string &text,
    float maxWidth,
    float textScale)
{
    if (text.empty())
    {
        return {};
    }

    if (context.measureHudTextWidth(fontName, text) * textScale <= maxWidth)
    {
        return {text};
    }

    size_t bestSplitIndex = std::string::npos;
    float bestScore = std::numeric_limits<float>::max();

    for (size_t index = 1; index + 1 < text.size(); ++index)
    {
        if (text[index] != ' ')
        {
            continue;
        }

        const std::string firstLine = trimContextActionLabelPart(text.substr(0, index));
        const std::string secondLine = trimContextActionLabelPart(text.substr(index + 1));

        if (firstLine.empty() || secondLine.empty())
        {
            continue;
        }

        const float firstWidth = context.measureHudTextWidth(fontName, firstLine) * textScale;
        const float secondWidth = context.measureHudTextWidth(fontName, secondLine) * textScale;

        if (firstWidth <= maxWidth && secondWidth <= maxWidth)
        {
            const float score = std::max(firstWidth, secondWidth) + std::abs(firstWidth - secondWidth) * 0.25f;

            if (score < bestScore)
            {
                bestScore = score;
                bestSplitIndex = index;
            }
        }
    }

    if (bestSplitIndex != std::string::npos)
    {
        return {
            trimContextActionLabelPart(text.substr(0, bestSplitIndex)),
            trimContextActionLabelPart(text.substr(bestSplitIndex + 1))
        };
    }

    std::vector<std::string> lines;
    std::string currentLine;
    size_t wordBegin = 0;

    while (wordBegin < text.size())
    {
        while (wordBegin < text.size() && text[wordBegin] == ' ')
        {
            ++wordBegin;
        }

        if (wordBegin >= text.size())
        {
            break;
        }

        size_t wordEnd = text.find(' ', wordBegin);

        if (wordEnd == std::string::npos)
        {
            wordEnd = text.size();
        }

        const std::string word = text.substr(wordBegin, wordEnd - wordBegin);
        const std::string candidate = currentLine.empty() ? word : currentLine + " " + word;

        if (!currentLine.empty() && context.measureHudTextWidth(fontName, candidate) * textScale > maxWidth)
        {
            lines.push_back(currentLine);
            currentLine = word;

            if (lines.size() == 1)
            {
                break;
            }
        }
        else
        {
            currentLine = candidate;
        }

        wordBegin = wordEnd + 1;
    }

    if (lines.empty())
    {
        lines.push_back(fitContextActionLabel(context, fontName, text, maxWidth, textScale));
    }
    else
    {
        const size_t remainingBegin = wordBegin < text.size() ? wordBegin : text.size();
        const std::string remaining = trimContextActionLabelPart(text.substr(remainingBegin));
        const std::string secondLine = trimContextActionLabelPart(
            currentLine + (remaining.empty() ? std::string() : " " + remaining));
        lines.push_back(fitContextActionLabel(context, fontName, secondLine, maxWidth, textScale));
    }

    return lines;
}

void renderCenteredContextActionLabelLines(
    GameplayScreenRuntime &context,
    const UiLayoutManager::LayoutElement &layout,
    const GameplayResolvedHudLayoutElement &rect,
    const std::vector<std::string> &lines)
{
    if (lines.empty())
    {
        return;
    }

    const float fontScale = std::max(0.5f, layout.textScale * rect.scale);
    const float fontHeight = static_cast<float>(std::max(1, context.hudFontHeight(layout.fontName)));
    const float lineHeight = fontHeight * fontScale;
    const float lineGap = lines.size() > 1 ? std::max(1.0f, 1.0f * rect.scale) : 0.0f;
    const float totalHeight = lineHeight * static_cast<float>(lines.size())
        + lineGap * static_cast<float>(lines.size() - 1);
    float textY = std::round(rect.y + (rect.height - totalHeight) * 0.5f);

    for (const std::string &line : lines)
    {
        const float lineWidth = context.measureHudTextWidth(layout.fontName, line) * fontScale;
        const float textX = std::round(rect.x + (rect.width - lineWidth) * 0.5f);
        context.renderHudTextLine(layout.fontName, layout.textColorAbgr, line, textX, textY, fontScale);
        textY += lineHeight + lineGap;
    }
}

void renderMobileContextAction(GameplayScreenRuntime &context, int width, int height)
{
    if (!context.settingsSnapshot().contextActionPopup)
    {
        return;
    }

    const GameplayContextActionState &state = context.contextActionStateReadOnly();

    if (!state.visible || state.primaryIndex >= state.actions.size())
    {
        return;
    }

    const UiLayoutManager::LayoutElement *pButtonLayout =
        context.findHudLayoutElement("OutdoorMobileContextActionButton");

    if (pButtonLayout == nullptr)
    {
        return;
    }

    const std::optional<GameplayResolvedHudLayoutElement> buttonRect =
        resolveLayout(
            context,
            "OutdoorMobileContextActionButton",
            pButtonLayout->width > 0.0f ? pButtonLayout->width : 260.0f,
            pButtonLayout->height > 0.0f ? pButtonLayout->height : 56.0f,
            width,
            height);

    if (!buttonRect)
    {
        return;
    }

    const GameplayContextAction &action = state.actions[state.primaryIndex];
    const GameplayHudPointerTarget &pressedTarget = context.interactionState().gameplayHudPressedTarget;
    const bool pressed =
        context.interactionState().gameplayHudClickLatch
        && pressedTarget.type == GameplayHudPointerTargetType::ContextActionButton
        && pressedTarget.index == state.primaryIndex;
    const uint32_t panelColor = pressed ? makeAbgrColor(27, 19, 11, 230) : makeAbgrColor(17, 13, 9, 220);
    const uint32_t borderColor = pressed ? makeAbgrColor(255, 159, 47, 255) : makeAbgrColor(246, 211, 106, 245);
    const float border = std::max(2.0f, buttonRect->scale * 2.0f);

    const auto submitSolidQuad =
        [&context](float x, float y, float quadWidth, float quadHeight, uint32_t colorAbgr)
        {
            const std::optional<GameplayHudTextureHandle> texture =
                context.gameplayUiRuntime().ensureSolidHudTextureLoaded(
                    "__mobile_context_action_" + std::to_string(colorAbgr),
                    colorAbgr);

            if (texture)
            {
                context.submitHudTexturedQuad(*texture, x, y, quadWidth, quadHeight);
            }
        };

    submitSolidQuad(buttonRect->x, buttonRect->y, buttonRect->width, buttonRect->height, panelColor);
    submitSolidQuad(buttonRect->x, buttonRect->y, buttonRect->width, border, borderColor);
    submitSolidQuad(
        buttonRect->x,
        buttonRect->y + buttonRect->height - border,
        buttonRect->width,
        border,
        borderColor);
    submitSolidQuad(buttonRect->x, buttonRect->y, border, buttonRect->height, borderColor);
    submitSolidQuad(
        buttonRect->x + buttonRect->width - border,
        buttonRect->y,
        border,
        buttonRect->height,
        borderColor);

    const float iconSize = std::min(42.0f * buttonRect->scale, buttonRect->height - 10.0f * buttonRect->scale);
    const float iconX = buttonRect->x + 7.0f * buttonRect->scale;
    const float iconY = buttonRect->y + (buttonRect->height - iconSize) * 0.5f;
    const std::optional<GameplayHudTextureHandle> icon = loadContextActionIcon(context, action, pressed);

    if (icon)
    {
        context.submitHudTexturedQuad(*icon, iconX, iconY, iconSize, iconSize);
    }

    UiLayoutManager::LayoutElement labelLayout = {};
    labelLayout.fontName = "Create";
    labelLayout.textColorAbgr = makeAbgrColor(246, 211, 106);
    labelLayout.textAlignX = UiLayoutManager::TextAlignX::Center;
    labelLayout.textAlignY = UiLayoutManager::TextAlignY::Middle;
    labelLayout.textScale = 0.92f;
    labelLayout.textPadX = 0.0f;
    labelLayout.textPadY = 0.0f;

    GameplayResolvedHudLayoutElement labelRect = {};
    labelRect.x = iconX + iconSize + 8.0f * buttonRect->scale;
    labelRect.y = buttonRect->y;
    labelRect.width = std::max(1.0f, buttonRect->x + buttonRect->width - labelRect.x - 8.0f * buttonRect->scale);
    labelRect.height = buttonRect->height;
    labelRect.scale = buttonRect->scale;

    if (!action.label.empty())
    {
        const std::vector<std::string> labelLines =
            fitContextActionLabelLines(
                context,
                labelLayout.fontName,
                action.label,
                std::max(1.0f, labelRect.width - 6.0f * labelRect.scale),
                labelLayout.textScale * labelRect.scale);
        renderCenteredContextActionLabelLines(context, labelLayout, labelRect, labelLines);
    }
}

} // namespace

void GameplayHudRenderer::renderGameplayHud(GameplayScreenRuntime &context, int width, int height)
{
    Party *pParty = context.party();

    if (pParty == nullptr || !context.hasHudRenderResources() || width <= 0 || height <= 0)
    {
        return;
    }

    context.prepareHudView(width, height);
    const Party &party = *pParty;
    const GameplayHudScreenState hudScreenState = context.currentHudScreenState();
    const bool isLimitedOverlayHud = isOverlayHudState(hudScreenState);
    const ActiveGameplayHudLayout gameplayHudLayout = isLimitedOverlayHud
        ? ActiveGameplayHudLayout::Overlay
#if defined(__ANDROID__)
        : ActiveGameplayHudLayout::Widescreen;
#else
        : (context.settingsSnapshot().gameplayUiLayout == GameplayUiLayout::Standard
            ? ActiveGameplayHudLayout::Standard
            : ActiveGameplayHudLayout::Widescreen);
#endif
    const bool useGameplayWideHud = gameplayHudLayout == ActiveGameplayHudLayout::Widescreen;
    const bool shouldRenderStatusBar =
        hudScreenState != GameplayHudScreenState::Spellbook
        && hudScreenState != GameplayHudScreenState::Rest
        && hudScreenState != GameplayHudScreenState::Menu
        && hudScreenState != GameplayHudScreenState::Controls
        && hudScreenState != GameplayHudScreenState::Keyboard
        && hudScreenState != GameplayHudScreenState::VideoOptions
        && hudScreenState != GameplayHudScreenState::SaveGame
        && hudScreenState != GameplayHudScreenState::LoadGame
        && hudScreenState != GameplayHudScreenState::Journal
        && hudScreenState != GameplayHudScreenState::QuickReference;

    const auto replaceAll =
        [](std::string text, const std::string &from, const std::string &to) -> std::string
        {
            size_t position = 0;

            while ((position = text.find(from, position)) != std::string::npos)
            {
                text.replace(position, from.size(), to);
                position += to.size();
            }

            return text;
        };
    const auto resolveCounterLabel =
        [&replaceAll](const std::string &labelText, const std::string &value) -> std::string
        {
            if (labelText.empty())
            {
                return value;
            }

            const std::string replacedGold = replaceAll(labelText, "{gold}", value);
            const std::string replacedFood = replaceAll(replacedGold, "{food}", value);
            return replacedFood == labelText ? value : replacedFood;
        };

    std::string statusBarLabel;

    if (context.statusBarEventRemainingSeconds() > 0.0f && !context.statusBarEventText().empty())
    {
        statusBarLabel = context.statusBarEventText();
    }
    else if (!context.statusBarHoverText().empty())
    {
        statusBarLabel = context.statusBarHoverText();
    }

    if (shouldRenderStatusBar)
    {
        const std::string statusBarLayoutId = statusBarLayoutIdForHudLayout(gameplayHudLayout);
        const UiLayoutManager::LayoutElement *pStatusBarLayout = context.findHudLayoutElement(statusBarLayoutId);

        if (pStatusBarLayout != nullptr)
        {
            float logicalStatusBarWidth = pStatusBarLayout->width > 0.0f ? pStatusBarLayout->width : 360.0f;

            if (useGameplayWideHud && !statusBarLabel.empty())
            {
                logicalStatusBarWidth = std::clamp(
                    context.measureHudTextWidth(pStatusBarLayout->fontName, statusBarLabel)
                        * std::max(0.1f, pStatusBarLayout->textScale)
                        + 24.0f,
                    32.0f,
                    483.0f);
            }

            const std::optional<GameplayResolvedHudLayoutElement> resolvedStatusBar =
                resolveLayout(
                    context,
                    statusBarLayoutId,
                    logicalStatusBarWidth,
                    pStatusBarLayout->height > 0.0f ? pStatusBarLayout->height : 18.0f,
                    width,
                    height);

            if (resolvedStatusBar)
            {
                if (useGameplayWideHud && !statusBarLabel.empty() && !pStatusBarLayout->primaryAsset.empty())
                {
                    const std::optional<GameplayHudTextureHandle> statusBarTexture =
                        context.gameplayUiRuntime().ensureHudTextureLoaded(pStatusBarLayout->primaryAsset);

                    if (statusBarTexture)
                    {
                        context.submitHudTexturedQuad(
                            *statusBarTexture,
                            resolvedStatusBar->x,
                            resolvedStatusBar->y,
                            resolvedStatusBar->width,
                            resolvedStatusBar->height);
                    }
                }

                if (useGameplayWideHud && !statusBarLabel.empty())
                {
                    const std::optional<GameplayHudTextureHandle> statusBarFrameTexture =
                        context.gameplayUiRuntime().ensureHudTextureLoaded(StatusBarFrameAsset);

                    if (statusBarFrameTexture)
                    {
                        context.submitHudTexturedQuad(
                            *statusBarFrameTexture,
                            resolvedStatusBar->x,
                            resolvedStatusBar->y,
                            resolvedStatusBar->width,
                            resolvedStatusBar->height);
                    }
                }

                context.renderLayoutLabel(*pStatusBarLayout, *resolvedStatusBar, statusBarLabel);
            }
        }
    }

    if (context.settingsSnapshot().contextActionPopup && hudScreenState == GameplayHudScreenState::Gameplay)
    {
        renderMobileContextAction(context, width, height);
    }

    if (!isLimitedOverlayHud)
    {
        const char *pTopBarLayoutId =
            gameplayHudLayout == ActiveGameplayHudLayout::Standard ? "OutdoorStandardTopBar" : nullptr;

        if (pTopBarLayoutId != nullptr)
        {
            const UiLayoutManager::LayoutElement *pTopBarLayout = context.findHudLayoutElement(pTopBarLayoutId);

            if (pTopBarLayout != nullptr)
            {
                const std::optional<GameplayResolvedHudLayoutElement> topBar =
                    resolveLayout(
                        context,
                        pTopBarLayoutId,
                        pTopBarLayout->width > 0.0f ? pTopBarLayout->width : 640.0f,
                        pTopBarLayout->height > 0.0f ? pTopBarLayout->height : 29.0f,
                        width,
                        height);

                if (topBar && !pTopBarLayout->labelText.empty())
                {
                    const std::string label = replaceAll(
                        replaceAll(pTopBarLayout->labelText, "{gold}", std::to_string(party.gold())),
                        "{food}",
                        std::to_string(party.food()));
                    context.renderLayoutLabel(*pTopBarLayout, *topBar, label);
                }
            }
        }

        const char *pGoldLabelLayoutId = gameplayHudLayout == ActiveGameplayHudLayout::Standard
            ? "OutdoorStandardGoldLabel"
            : "OutdoorGoldLabel";
        const UiLayoutManager::LayoutElement *pGoldLabelLayout = context.findHudLayoutElement(pGoldLabelLayoutId);

        if (pGoldLabelLayout != nullptr)
        {
            const std::optional<GameplayResolvedHudLayoutElement> goldLabel =
                resolveLayout(
                    context,
                    pGoldLabelLayoutId,
                    pGoldLabelLayout->width > 0.0f ? pGoldLabelLayout->width : 28.0f,
                    pGoldLabelLayout->height > 0.0f ? pGoldLabelLayout->height : 14.0f,
                    width,
                    height);

            if (goldLabel)
            {
                context.renderLayoutLabel(
                    *pGoldLabelLayout,
                    *goldLabel,
                    resolveCounterLabel(pGoldLabelLayout->labelText, std::to_string(party.gold())));
            }
        }

        const char *pFoodLabelLayoutId = gameplayHudLayout == ActiveGameplayHudLayout::Standard
            ? "OutdoorStandardFoodLabel"
            : "OutdoorFoodLabel";
        const UiLayoutManager::LayoutElement *pFoodLabelLayout = context.findHudLayoutElement(pFoodLabelLayoutId);

        if (pFoodLabelLayout != nullptr)
        {
            const std::optional<GameplayResolvedHudLayoutElement> foodLabel =
                resolveLayout(
                    context,
                    pFoodLabelLayoutId,
                    pFoodLabelLayout->width > 0.0f ? pFoodLabelLayout->width : 28.0f,
                    pFoodLabelLayout->height > 0.0f ? pFoodLabelLayout->height : 14.0f,
                    width,
                    height);

            if (foodLabel)
            {
                context.renderLayoutLabel(
                    *pFoodLabelLayout,
                    *foodLabel,
                    resolveCounterLabel(pFoodLabelLayout->labelText, std::to_string(party.food())));
            }
        }
    }

    if (isLimitedOverlayHud)
    {
        return;
    }

    const UiLayoutManager::LayoutElement *pBottomLeftButtonsLayout =
        context.findHudLayoutElement("OutdoorBottomLeftButtons");

    if (pBottomLeftButtonsLayout != nullptr)
    {
        const std::optional<GameplayResolvedHudLayoutElement> bottomLeftButtons =
            resolveLayout(context, "OutdoorBottomLeftButtons", 180.0f, 32.0f, width, height);

        if (bottomLeftButtons)
        {
            context.renderLayoutLabel(
                *pBottomLeftButtonsLayout,
                *bottomLeftButtons,
                pBottomLeftButtonsLayout->labelText);
        }
    }

    const std::string skullPanelLayoutId =
        gameplayHudLayout == ActiveGameplayHudLayout::Standard ? "OutdoorStandardBuffSkullPanel" : "OutdoorBuffSkullPanel";
    const UiLayoutManager::LayoutElement *pSkullPanelLayout = context.findHudLayoutElement(skullPanelLayoutId);

    if (pSkullPanelLayout != nullptr)
    {
        const std::optional<GameplayResolvedHudLayoutElement> skullPanel =
            resolveLayout(context, skullPanelLayoutId, 96.0f, 48.0f, width, height);

        if (skullPanel)
        {
            context.renderLayoutLabel(*pSkullPanelLayout, *skullPanel, pSkullPanelLayout->labelText);
        }
    }

    const std::string bodyPanelLayoutId =
        gameplayHudLayout == ActiveGameplayHudLayout::Standard ? "OutdoorStandardBuffBodyPanel" : "OutdoorBuffBodyPanel";
    const UiLayoutManager::LayoutElement *pBodyPanelLayout = context.findHudLayoutElement(bodyPanelLayoutId);

    if (pBodyPanelLayout != nullptr)
    {
        const std::optional<GameplayResolvedHudLayoutElement> bodyPanel =
            resolveLayout(context, bodyPanelLayoutId, 96.0f, 48.0f, width, height);

        if (bodyPanel)
        {
            context.renderLayoutLabel(*pBodyPanelLayout, *bodyPanel, pBodyPanelLayout->labelText);
        }
    }
}
} // namespace OpenYAMM::Game
