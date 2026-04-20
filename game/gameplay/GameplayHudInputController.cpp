#include "game/gameplay/GameplayHudInputController.h"

#include "game/gameplay/GameplayScreenRuntime.h"

#include <SDL3/SDL.h>

#include <optional>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint64_t PartyPortraitDoubleClickWindowMs = 500;

struct HudPointerState
{
    float x = 0.0f;
    float y = 0.0f;
    bool leftButtonPressed = false;
};

template <typename Target, typename ResolveTargetFn, typename ActivateTargetFn>
void handlePointerClickRelease(
    const HudPointerState &pointerState,
    bool &clickLatch,
    Target &pressedTarget,
    const Target &noneTarget,
    ResolveTargetFn resolveTargetFn,
    ActivateTargetFn activateTargetFn)
{
    if (pointerState.leftButtonPressed)
    {
        if (!clickLatch)
        {
            pressedTarget = resolveTargetFn(pointerState.x, pointerState.y);
            clickLatch = true;
        }
    }
    else if (clickLatch)
    {
        const Target currentTarget = resolveTargetFn(pointerState.x, pointerState.y);

        if (currentTarget == pressedTarget)
        {
            activateTargetFn(currentTarget);
        }

        clickLatch = false;
        pressedTarget = noneTarget;
    }
    else
    {
        pressedTarget = noneTarget;
    }
}

const char *activeGameplayButtonLayoutId(
    const GameplayScreenRuntime &context,
    const char *pWideId,
    const char *pStandardId)
{
    return context.settingsSnapshot().gameplayUiLayout == GameplayUiLayout::Standard ? pStandardId : pWideId;
}
}

void GameplayHudInputController::handlePartyPortraitInput(
    GameplayScreenRuntime &context,
    const GameplayPartyPortraitInputConfig &config)
{
    if (!config.allowInput || config.screenWidth <= 0 || config.screenHeight <= 0)
    {
        context.partyPortraitClickLatch() = false;
        context.partyPortraitPressedIndex() = std::nullopt;
        return;
    }

    const HudPointerState pointerState = {
        config.pointerX,
        config.pointerY,
        config.leftButtonPressed
    };

    handlePointerClickRelease(
        pointerState,
        context.partyPortraitClickLatch(),
        context.partyPortraitPressedIndex(),
        std::optional<size_t>{},
        [&context, &config](float x, float y) -> std::optional<size_t>
        {
            return context.resolvePartyPortraitIndexAtPoint(config.screenWidth, config.screenHeight, x, y);
        },
        [&context, &config](const std::optional<size_t> &memberIndex)
        {
            if (!memberIndex)
            {
                return;
            }

            if (config.onPortraitActivated && config.onPortraitActivated(*memberIndex))
            {
                return;
            }

            if (context.heldInventoryItem().active)
            {
                const bool switchCharacterOnFailedPlacement =
                    context.characterScreenReadOnly().open
                    && context.characterScreenReadOnly().page == GameplayUiController::CharacterPage::Inventory;

                if (context.tryAutoPlaceHeldInventoryItemOnPartyMember(*memberIndex, !switchCharacterOnFailedPlacement))
                {
                    context.lastPartyPortraitClickedIndex() = std::nullopt;
                }
                else if (switchCharacterOnFailedPlacement)
                {
                    context.trySelectPartyMember(*memberIndex, config.requireGameplayReady);
                }

                return;
            }

            const uint64_t nowTicks = SDL_GetTicks();
            const bool isGameplayInventoryDoubleClick =
                config.requireGameplayReady
                && context.lastPartyPortraitClickedIndex().has_value()
                && *context.lastPartyPortraitClickedIndex() == *memberIndex
                && nowTicks >= context.lastPartyPortraitClickTicks()
                && nowTicks - context.lastPartyPortraitClickTicks() <= PartyPortraitDoubleClickWindowMs;
            const bool isChestInventoryDoubleClick =
                config.hasActiveLootView
                && context.lastPartyPortraitClickedIndex().has_value()
                && *context.lastPartyPortraitClickedIndex() == *memberIndex
                && nowTicks >= context.lastPartyPortraitClickTicks()
                && nowTicks - context.lastPartyPortraitClickTicks() <= PartyPortraitDoubleClickWindowMs;

            if (!context.trySelectPartyMember(*memberIndex, config.requireGameplayReady))
            {
                return;
            }

            if (isGameplayInventoryDoubleClick)
            {
                GameplayUiController::CharacterScreenState &characterScreen = context.characterScreen();
                characterScreen = {};
                characterScreen.open = true;
                characterScreen.page = GameplayUiController::CharacterPage::Inventory;
                characterScreen.source = GameplayUiController::CharacterScreenSource::Party;
                characterScreen.sourceIndex = 0;
            }
            else if (isChestInventoryDoubleClick)
            {
                context.openChestTransferInventoryOverlay();
            }

            context.lastPartyPortraitClickTicks() = nowTicks;
            context.lastPartyPortraitClickedIndex() = *memberIndex;
        });
}

void GameplayHudInputController::handleGameplayHudButtonInput(
    GameplayScreenRuntime &context,
    const GameplayHudButtonInputConfig &config)
{
    if (!config.allowInput || config.screenWidth <= 0 || config.screenHeight <= 0)
    {
        context.gameplayHudClickLatch() = false;
        context.gameplayHudPressedTarget() = {};
        return;
    }

    const HudPointerState pointerState = {
        config.pointerX,
        config.pointerY,
        config.leftButtonPressed
    };

    handlePointerClickRelease(
        pointerState,
        context.gameplayHudClickLatch(),
        context.gameplayHudPressedTarget(),
        GameplayHudPointerTarget{},
        [&context, &config](float pointerX, float pointerY) -> GameplayHudPointerTarget
        {
            const std::pair<const char *, GameplayHudPointerTargetType> targets[] = {
                {
                    activeGameplayButtonLayoutId(
                        context,
                        "OutdoorButtonOptions",
                        "OutdoorStandardButtonOptions"),
                    GameplayHudPointerTargetType::MenuButton
                },
                {
                    activeGameplayButtonLayoutId(
                        context,
                        "OutdoorButtonRest",
                        "OutdoorStandardButtonRest"),
                    GameplayHudPointerTargetType::RestButton
                },
                {
                    activeGameplayButtonLayoutId(
                        context,
                        "OutdoorButtonBooks",
                        "OutdoorStandardButtonBooks"),
                    GameplayHudPointerTargetType::BooksButton
                }
            };

            for (const auto &[pLayoutId, targetType] : targets)
            {
                const GameplayScreenRuntime::HudLayoutElement *pLayout = context.findHudLayoutElement(pLayoutId);

                if (pLayout == nullptr)
                {
                    continue;
                }

                const std::optional<GameplayScreenRuntime::ResolvedHudLayoutElement> resolved =
                    context.resolveHudLayoutElement(
                        pLayoutId,
                        config.screenWidth,
                        config.screenHeight,
                        pLayout->width,
                        pLayout->height);

                if (resolved && context.isPointerInsideResolvedElement(*resolved, pointerX, pointerY))
                {
                    return {targetType};
                }
            }

            return {};
        },
        [&context](const GameplayHudPointerTarget &target)
        {
            switch (target.type)
            {
            case GameplayHudPointerTargetType::MenuButton:
                context.openMenuOverlay();
                break;
            case GameplayHudPointerTargetType::RestButton:
                context.openRestOverlay();
                break;
            case GameplayHudPointerTargetType::BooksButton:
                context.openJournalOverlay();
                break;
            case GameplayHudPointerTargetType::None:
                break;
            }
        });
}
} // namespace OpenYAMM::Game
