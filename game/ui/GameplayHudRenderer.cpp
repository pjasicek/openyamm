#include "game/ui/GameplayHudRenderer.h"

#include "game/gameplay/GameplayScreenRuntime.h"

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
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
        || hudScreenState == GameplayHudScreenState::Journal;
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
        : (context.settingsSnapshot().gameplayUiLayout == GameplayUiLayout::Standard
            ? ActiveGameplayHudLayout::Standard
            : ActiveGameplayHudLayout::Widescreen);
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
        && hudScreenState != GameplayHudScreenState::Journal;

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
                        + 16.0f,
                    24.0f,
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

                context.renderLayoutLabel(*pStatusBarLayout, *resolvedStatusBar, statusBarLabel);
            }
        }
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
