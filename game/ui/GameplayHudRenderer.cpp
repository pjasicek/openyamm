#include "game/ui/GameplayHudRenderer.h"

#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/ui/GameplayUiSkin.h"

#include <algorithm>
#include <cmath>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
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

std::optional<GameplayHudTextureHandle> loadContextActionIcon(
    GameplayScreenRuntime &context,
    const GameplayContextAction &action)
{
    if (action.kind == GameplayContextActionKind::DropHeldItem
        && context.heldInventoryItem().active
        && context.itemTable() != nullptr)
    {
        const ItemDefinition *pItemDefinition =
            context.itemTable()->get(context.heldInventoryItem().item.objectDescriptionId);

        if (pItemDefinition != nullptr && !pItemDefinition->iconName.empty())
        {
            const std::optional<GameplayHudTextureHandle> itemIcon =
                context.gameplayUiRuntime().ensureItemIconTextureLoaded(pItemDefinition->iconName);

            if (itemIcon)
            {
                return itemIcon;
            }
        }
    }

    const UiLayoutManager::LayoutElement *pIcon = context.findHudLayoutElement(action.iconId);
    return pIcon != nullptr && !pIcon->primaryAsset.empty()
        ? context.gameplayUiRuntime().ensureHudTextureLoaded(pIcon->primaryAsset) : std::nullopt;
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

void renderContextAction(GameplayScreenRuntime &context, int width, int height)
{
    const GameplayContextActionState &state = context.contextActionStateReadOnly();

    if (!state.visible || state.primaryIndex >= state.actions.size())
    {
        return;
    }

    const GameplayContextAction &action = state.actions[state.primaryIndex];

    if (!context.settingsSnapshot().contextActionPopup
        && action.kind != GameplayContextActionKind::DropHeldItem)
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

    const GameplayHudPointerTarget &pressedTarget = context.interactionState().gameplayHudPressedTarget;
    const bool pressed =
        context.interactionState().gameplayHudClickLatch
        && pressedTarget.type == GameplayHudPointerTargetType::ContextActionButton
        && pressedTarget.index == state.primaryIndex;
    GameplayUiSkin::renderPanel(context, *buttonRect, false, 0.32f);

    const float iconSize = std::min(42.0f * buttonRect->scale, buttonRect->height - 10.0f * buttonRect->scale);
    const float iconX = buttonRect->x + 7.0f * buttonRect->scale;
    const float iconY = buttonRect->y + (buttonRect->height - iconSize) * 0.5f;
    const std::optional<GameplayHudTextureHandle> icon = loadContextActionIcon(context, action);

    if (icon)
    {
        context.submitHudTexturedQuad(*icon, iconX, iconY + (pressed ? buttonRect->scale : 0), iconSize, iconSize);
    }

    UiLayoutManager::LayoutElement labelLayout = {};
    labelLayout.fontName = "Fondamento";
    labelLayout.textColorAbgr = pressed ? GameplayUiSkin::Gold : GameplayUiSkin::Ivory;
    labelLayout.textAlignX = UiLayoutManager::TextAlignX::Center;
    labelLayout.textAlignY = UiLayoutManager::TextAlignY::Middle;
    labelLayout.textScale = 0.4166667f;
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

void renderPassTurnButton(GameplayScreenRuntime &context, int width, int height)
{
    const std::optional<GameplayResolvedHudLayoutElement> buttonRect =
        context.resolveMobilePassTurnButton(width, height);

    if (!buttonRect)
    {
        return;
    }

    const bool pressed =
        context.interactionState().gameplayHudClickLatch
        && context.interactionState().gameplayHudPressedTarget.type == GameplayHudPointerTargetType::PassTurnButton;
    GameplayUiSkin::renderPanel(context, *buttonRect, false, 0.32f);

    UiLayoutManager::LayoutElement labelLayout = {};
    labelLayout.fontName = "Fondamento";
    labelLayout.textColorAbgr = pressed ? GameplayUiSkin::Gold : GameplayUiSkin::Ivory;
    labelLayout.textAlignX = UiLayoutManager::TextAlignX::Center;
    labelLayout.textAlignY = UiLayoutManager::TextAlignY::Middle;
    labelLayout.textScale = 0.4166667f;
    const std::string label =
        context.turnBasedCombatRuntime().stage() == TurnBasedCombatStage::Movement ? "End Movement" : "Pass Turn";
    renderCenteredContextActionLabelLines(context, labelLayout, *buttonRect, {label});
}

} // namespace

void GameplayHudRenderer::renderGameplayHud(GameplayScreenRuntime &context, int width, int height)
{
    const Party *pParty = context.partyReadOnly();
    if (pParty == nullptr || !context.hasHudRenderResources() || width <= 0 || height <= 0)
    {
        return;
    }
    context.prepareHudView(width, height);
    const GameplayHudScreenState state = context.currentHudScreenState();
    const bool fullscreen = isOverlayHudState(state)
        && !activeEventDialogPreservesGameplayHud(context.activeEventDialog());
    std::string status;
    if (context.houseBankState().inputActive())
    {
        status = std::string(context.houseBankState().inputMode
            == GameplayUiController::HouseBankInputMode::Deposit ? "Deposit: " : "Withdraw: ")
            + context.houseBankState().inputText + "_";
    }
    else if (context.statusBarEventRemainingSeconds() > 0 && !context.statusBarEventText().empty())
    {
        status = context.statusBarEventText();
    }
    else
    {
        status = context.statusBarHoverText();
    }
    if (status.empty() && state == GameplayHudScreenState::Dialogue)
    {
        status = context.interactionState().dialogueStatusHint;
    }
    if (!status.empty() && (state == GameplayHudScreenState::Gameplay || state == GameplayHudScreenState::Character
        || state == GameplayHudScreenState::Dialogue || state == GameplayHudScreenState::Chest
        || state == GameplayHudScreenState::Spellbook))
    {
        const std::string id = fullscreen ? "OutdoorStatusBar" : "OutdoorGameplayStatusBar";
        const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(id);
        std::optional<GameplayResolvedHudLayoutElement> rect = context.resolveHudLayoutElement(id, width, height, 0, 0);
        if (pLayout != nullptr && rect)
        {
            if (fullscreen)
            {
                UiLayoutManager::LayoutElement label = *pLayout;
                const float textWidth = context.measureHudTextWidth(label.fontName, status);
                const float availableWidth = rect->width / rect->scale - 2 * std::abs(label.textPadX);
                if (textWidth > availableWidth)
                {
                    label.textScale = std::max(0.75f, availableWidth / textWidth);
                }
                const IGameplayWorldRuntime *pWorld = context.worldRuntime();
                const EventRuntimeState *pEvents = pWorld != nullptr ? pWorld->eventRuntimeState() : nullptr;
                const bool editing = context.houseBankState().inputActive()
                    || (pEvents != nullptr && pEvents->pendingInputPrompt.has_value());
                // Keep the entered suffix and caret visible when the input exceeds the fixed rail.
                while (editing && !status.empty()
                    && context.measureHudTextWidth(label.fontName, status) * label.textScale > availableWidth)
                {
                    size_t next = 1;
                    while (next < status.size() && (static_cast<unsigned char>(status[next]) & 0xc0) == 0x80)
                    {
                        ++next;
                    }
                    status.erase(0, next);
                }
                context.renderLayoutLabel(label, *rect, status);
            }
            else
            {
                const std::optional<GameplayHudFontHandle> font = context.findHudFont(pLayout->fontName);
                if (font)
                {
                    const float bottom = rect->y + rect->height;
                    const float scale = rect->scale * pLayout->textScale;
                    const float maxWidth = 330.666667f * rect->scale;
                    std::vector<std::string> lines = context.wrapHudTextToWidth(*font, status,
                        (maxWidth - 16 * rect->scale) / scale);
                    const size_t maximumLines = 8;
                    if (lines.size() > maximumLines)
                    {
                        lines.resize(maximumLines);
                        lines.back() += "...";
                    }
                    float textWidth = 0;
                    for (const std::string &line : lines)
                    {
                        textWidth = std::max(textWidth, context.measureHudTextWidth(font->fontName, line) * scale);
                    }
                    const float lineHeight = font->fontHeight * scale;
                    rect->width = std::min(maxWidth, textWidth + 16 * rect->scale);
                    rect->x = (width - rect->width) * 0.5f;
                    rect->height = std::min(78.933333f * rect->scale,
                        lineHeight * lines.size() + 12 * rect->scale);
                    rect->y = bottom - rect->height;
                    const std::optional<GameplayResolvedHudLayoutElement> dock =
                        context.resolveHudLayoutElement("ObsidianTurnDock", width, height, 0, 0);
                    if (context.turnBasedCombatRuntime().active() && dock
                        && dock->x + dock->width > rect->x && dock->x < rect->x + rect->width
                        && dock->y < rect->y + rect->height && dock->y + dock->height > rect->y)
                    {
                        rect->y = dock->y - rect->height - 8 * rect->scale;
                    }
                    GameplayUiSkin::renderTexture(context, "obsidian_hud_status_plate", *rect);
                    for (size_t i = 0; i < lines.size(); ++i)
                    {
                        context.renderLayoutLabel(*pLayout, {rect->x + 8 * rect->scale,
                            rect->y + 6 * rect->scale + i * lineHeight,
                            rect->width - 16 * rect->scale, lineHeight, rect->scale}, lines[i]);
                    }
                }
            }
        }
    }
    if (!fullscreen)
    {
        for (bool gold : {true, false})
        {
            const std::string id = gold ? "OutdoorGoldLabel" : "OutdoorFoodLabel";
            const UiLayoutManager::LayoutElement *pLayout = context.findHudLayoutElement(id);
            const std::optional<GameplayResolvedHudLayoutElement> rect =
                context.resolveHudLayoutElement(id, width, height, 0, 0);
            if (pLayout != nullptr && rect)
            {
                context.renderLayoutLabel(*pLayout, *rect, std::to_string(gold ? pParty->gold() : pParty->food()));
            }
        }
    }
    if (context.settingsSnapshot().contextActionPopup && state == GameplayHudScreenState::Gameplay)
    {
        renderContextAction(context, width, height);
    }
    renderPassTurnButton(context, width, height);
}
} // namespace OpenYAMM::Game
