#include "game/ui/screens/ArcomageScreen.h"

#include "game/audio/GameAudioSystem.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr float LogicalWidth = 640.0f;
constexpr float LogicalHeight = 480.0f;
constexpr float CardWidth = 96.0f;
constexpr float CardHeight = 128.0f;
constexpr float HandY = 327.0f;
constexpr float TableCardWidth = 76.0f;
constexpr float TableCardHeight = 102.0f;
constexpr float AnimationTickSeconds = 1.0f / 30.0f;
constexpr float PlayCardMoveToCenterSeconds = 7.0f * AnimationTickSeconds;
constexpr float PlayCardHoldSeconds = 12.0f * AnimationTickSeconds;
constexpr float PlayCardMoveToTableSeconds = 7.0f * AnimationTickSeconds;
constexpr float DiscardCardAnimationSeconds = 14.0f * AnimationTickSeconds;
constexpr float AiTurnDelaySeconds = 0.75f;
constexpr float ResultAutoCloseSeconds = 1.0f;
constexpr uint32_t GrayTintColorAbgr = 0xff9c9c9cu;
constexpr uint32_t OeTextColorAbgr = 0xffffffffu;
constexpr char ComicFontName[] = "comic";
constexpr char ArrusFontName[] = "arrus";
const MenuScreenBase::SourceRect CardBackSourceRect = {192.0f, 0.0f, CardWidth, CardHeight};
const MenuScreenBase::SourceRect DiscardedOverlaySourceRect = {843.0f, 200.0f, 73.0f, 16.0f};

MenuScreenBase::Rect deckCardLogicalRect()
{
    return {120.0f, 18.0f, CardWidth, CardHeight};
}

int handCount(const ArcomagePlayerState &player)
{
    int result = 0;

    for (int cardId : player.hand)
    {
        if (cardId >= 0)
        {
            ++result;
        }
    }

    return result;
}

std::string resourceTypeName(ArcomageResourceType resourceType)
{
    switch (resourceType)
    {
        case ArcomageResourceType::Bricks:
            return "Bricks";

        case ArcomageResourceType::Gems:
            return "Gems";

        case ArcomageResourceType::Recruits:
            return "Recruits";

        case ArcomageResourceType::None:
            break;
    }

    return "Free";
}

float clamp01(float value)
{
    return std::clamp(value, 0.0f, 1.0f);
}

MenuScreenBase::Rect lerpRect(const MenuScreenBase::Rect &from, const MenuScreenBase::Rect &to, float progress)
{
    const float t = clamp01(progress);
    return {
        from.x + (to.x - from.x) * t,
        from.y + (to.y - from.y) * t,
        from.width + (to.width - from.width) * t,
        from.height + (to.height - from.height) * t
    };
}

int cardsDrawnBetweenStates(const ArcomageState &previousState, const ArcomageState &currentState)
{
    if (previousState.drawDeck.empty() || currentState.drawDeck.empty())
    {
        return 0;
    }

    if (currentState.deckIndex >= previousState.deckIndex)
    {
        return static_cast<int>(currentState.deckIndex - previousState.deckIndex);
    }

    return static_cast<int>(previousState.drawDeck.size() - previousState.deckIndex + currentState.deckIndex);
}

bool didDeckWrap(const ArcomageState &previousState, const ArcomageState &currentState)
{
    if (previousState.drawDeck.empty() || currentState.drawDeck.empty())
    {
        return false;
    }

    return currentState.deckIndex < previousState.deckIndex;
}
}

ArcomageScreen::ArcomageScreen(
    const Engine::AssetFileSystem &assetFileSystem,
    GameAudioSystem *pGameAudioSystem,
    const ArcomageLibrary &library,
    uint32_t houseId,
    const std::string &playerName,
    const std::string &opponentName,
    int winGoldReward,
    uint32_t randomSeed)
    : MenuScreenBase(assetFileSystem)
    , m_pGameAudioSystem(pGameAudioSystem)
    , m_pLibrary(&library)
    , m_winGoldReward(winGoldReward)
{
    if (!m_rules.initializeMatch(library, houseId, playerName, opponentName, randomSeed, m_state))
    {
        m_shouldClose = true;
        return;
    }
}

AppMode ArcomageScreen::mode() const
{
    return AppMode::Arcomage;
}

bool ArcomageScreen::shouldClose() const
{
    return m_shouldClose;
}

const ArcomageState &ArcomageScreen::state() const
{
    return m_state;
}

void ArcomageScreen::drawScreen(float deltaSeconds)
{
    const LogicalLayout layout = {
        (static_cast<float>(frameWidth()) - LogicalWidth * std::min(
            static_cast<float>(frameWidth()) / LogicalWidth,
            static_cast<float>(frameHeight()) / LogicalHeight)) * 0.5f,
        (static_cast<float>(frameHeight()) - LogicalHeight * std::min(
            static_cast<float>(frameWidth()) / LogicalWidth,
            static_cast<float>(frameHeight()) / LogicalHeight)) * 0.5f,
        std::min(
            static_cast<float>(frameWidth()) / LogicalWidth,
            static_cast<float>(frameHeight()) / LogicalHeight)
    };

    startTurnIfNeeded();

    drawTexture("Layout", Rect{layout.rootX, layout.rootY, LogicalWidth * layout.scale, LogicalHeight * layout.scale});
    drawBuildings(layout);
    drawPanels(layout);
    drawShownCards(layout);
    const std::vector<HandCardPlacement> handPlacements = drawCurrentHand(layout);
    drawAnimatedCard(layout);

    if (hasCardAnimation())
    {
        updateCardAnimation(deltaSeconds);
    }
    else if (m_state.result.finished && m_resultDelaySeconds > 0.0f)
    {
        updateResultDelay(deltaSeconds);
    }
    else if (m_state.result.finished)
    {
        updateFinishInput();
    }
    else if (m_state.currentPlayerIndex == 0)
    {
        updateHumanInput(layout, handPlacements);
    }
    else
    {
        updateAiTurn(deltaSeconds);
    }

    const std::string hoverText = hasCardAnimation() ? std::string {} : hoveredCardText();

    if (!hoverText.empty())
    {
        drawScreenText(layout, ArrusFontName, hoverText, LogicalWidth * 0.5f, 458.0f, true);
    }

    if (m_state.mustDiscard)
    {
        drawScreenText(layout, ArrusFontName, "Right-click a card to discard.", LogicalWidth * 0.5f, 306.0f, true);
    }

}

MenuScreenBase::Rect ArcomageScreen::scaleLogicalRect(const LogicalLayout &layout, const Rect &logicalRect) const
{
    return {
        layout.rootX + logicalRect.x * layout.scale,
        layout.rootY + logicalRect.y * layout.scale,
        logicalRect.width * layout.scale,
        logicalRect.height * layout.scale
    };
}

MenuScreenBase::SourceRect ArcomageScreen::cardSourceRect(const ArcomageCardDefinition &card) const
{
    const uint32_t slot = card.slot;
    return {
        static_cast<float>(96 * (slot % 10)),
        static_cast<float>(220 + 128 * (slot / 10)),
        CardWidth,
        CardHeight
    };
}

MenuScreenBase::Rect ArcomageScreen::shownCardLogicalRect(size_t index) const
{
    const float xSlot = static_cast<float>((index + 1) % 4);
    const float ySlot = static_cast<float>((index + 1) / 4);
    return {
        100.0f * xSlot + 120.0f,
        138.0f * ySlot + 18.0f,
        TableCardWidth,
        TableCardHeight
    };
}

MenuScreenBase::Rect ArcomageScreen::handCardLogicalRect(
    const ArcomagePlayerState &player,
    size_t handIndex,
    std::optional<size_t> hoveredHandIndex) const
{
    const int cardCount = handCount(player);

    if (cardCount <= 0)
    {
        return {};
    }

    const float spacing = (LogicalWidth - CardWidth * static_cast<float>(cardCount)) / static_cast<float>(cardCount + 1);
    float x = spacing;

    for (size_t slotIndex = 0; slotIndex < player.hand.size(); ++slotIndex)
    {
        if (player.hand[slotIndex] < 0)
        {
            continue;
        }

        const bool isHovered = hoveredHandIndex.has_value() && *hoveredHandIndex == slotIndex;
        const Rect logicalRect = {x, HandY - (isHovered ? 10.0f : 0.0f), CardWidth, CardHeight};

        if (slotIndex == handIndex)
        {
            return logicalRect;
        }

        x += spacing + CardWidth;
    }

    return {};
}

void ArcomageScreen::drawBuildings(const LogicalLayout &layout)
{
    const int maxTowerHeight = std::max(1, m_state.winTower);

    for (size_t playerIndex = 0; playerIndex < m_state.players.size(); ++playerIndex)
    {
        const bool left = playerIndex == 0;
        const ArcomagePlayerState &player = m_state.players[playerIndex];
        const int towerHeight = std::clamp(player.tower, 0, maxTowerHeight);
        const int wallHeight = std::clamp(player.wall, 0, 100);
        const float towerPixels = 200.0f * static_cast<float>(towerHeight) / static_cast<float>(maxTowerHeight);
        const float wallPixels = 200.0f * static_cast<float>(wallHeight) / 100.0f;

        if (towerPixels > 0.0f)
        {
            drawTextureRegion(
                "Sprites",
                SourceRect{892.0f, 0.0f, 45.0f, towerPixels},
                scaleLogicalRect(layout, Rect{left ? 102.0f : 494.0f, 297.0f - towerPixels, 45.0f, towerPixels})
            );
        }

        drawTextureRegion(
            "Sprites",
            SourceRect{384.0f, left ? 0.0f : 94.0f, 68.0f, 94.0f},
            scaleLogicalRect(layout, Rect{left ? 91.0f : 483.0f, 203.0f - towerPixels, 68.0f, 94.0f})
        );

        if (wallPixels > 0.0f)
        {
            drawTextureRegion(
                "Sprites",
                SourceRect{843.0f, 0.0f, 24.0f, wallPixels},
                scaleLogicalRect(layout, Rect{left ? 177.0f : 439.0f, 297.0f - wallPixels, 24.0f, wallPixels})
            );
        }
    }
}

void ArcomageScreen::drawPanels(const LogicalLayout &layout)
{
    drawTextureRegion(
        "Sprites",
        SourceRect{283.0f, 166.0f, 78.0f, 24.0f},
        scaleLogicalRect(layout, Rect{8.0f, 13.0f, 78.0f, 24.0f})
    );
    drawTextureRegion(
        "Sprites",
        SourceRect{283.0f, 166.0f, 78.0f, 24.0f},
        scaleLogicalRect(layout, Rect{555.0f, 13.0f, 78.0f, 24.0f})
    );
    drawTextureRegion(
        "Sprites",
        SourceRect{765.0f, 0.0f, 78.0f, 216.0f},
        scaleLogicalRect(layout, Rect{8.0f, 56.0f, 78.0f, 216.0f})
    );
    drawTextureRegion(
        "Sprites",
        SourceRect{765.0f, 0.0f, 78.0f, 216.0f},
        scaleLogicalRect(layout, Rect{555.0f, 56.0f, 78.0f, 216.0f})
    );
    drawTextureRegion(
        "Sprites",
        SourceRect{234.0f, 166.0f, 49.0f, 24.0f},
        scaleLogicalRect(layout, Rect{100.0f, 296.0f, 49.0f, 24.0f})
    );
    drawTextureRegion(
        "Sprites",
        SourceRect{234.0f, 166.0f, 49.0f, 24.0f},
        scaleLogicalRect(layout, Rect{492.0f, 296.0f, 49.0f, 24.0f})
    );
    drawTextureRegion(
        "Sprites",
        SourceRect{192.0f, 166.0f, 42.0f, 24.0f},
        scaleLogicalRect(layout, Rect{168.0f, 296.0f, 42.0f, 24.0f})
    );
    drawTextureRegion(
        "Sprites",
        SourceRect{192.0f, 166.0f, 42.0f, 24.0f},
        scaleLogicalRect(layout, Rect{430.0f, 296.0f, 42.0f, 24.0f})
    );

    if (m_state.players.size() >= 2)
    {
        const size_t displayedTurnPlayerIndex =
            hasCardAnimation() ? m_cardAnimation->playerIndex : m_state.currentPlayerIndex;
        std::string playerName = m_state.players[0].name;
        std::string opponentName = m_state.players[1].name;

        if (displayedTurnPlayerIndex == 0)
        {
            playerName += "***";
        }
        else if (displayedTurnPlayerIndex == 1)
        {
            opponentName += "***";
        }

        drawScreenText(layout, ComicFontName, playerName, 47.0f, 18.0f, true, OeTextColorAbgr);
        drawScreenText(layout, ComicFontName, opponentName, 595.0f, 18.0f, true, OeTextColorAbgr);
        drawScreenText(layout, ComicFontName, std::to_string(m_state.players[0].tower), 123.0f, 305.0f, true, OeTextColorAbgr);
        drawScreenText(layout, ComicFontName, std::to_string(m_state.players[1].tower), 515.0f, 305.0f, true, OeTextColorAbgr);
        drawScreenText(layout, ComicFontName, std::to_string(m_state.players[0].wall), 188.0f, 305.0f, true, OeTextColorAbgr);
        drawScreenText(layout, ComicFontName, std::to_string(m_state.players[1].wall), 451.0f, 305.0f, true, OeTextColorAbgr);

        const ArcomagePlayerState &player = m_state.players[0];
        const ArcomagePlayerState &enemy = m_state.players[1];

        drawScreenText(layout, ComicFontName, std::to_string(player.quarry), 14.0f, 89.0f, false, OeTextColorAbgr);
        drawScreenText(layout, ComicFontName, std::to_string(enemy.quarry), 561.0f, 89.0f, false, OeTextColorAbgr);
        drawScreenText(layout, ComicFontName, std::to_string(player.magic), 14.0f, 161.0f, false, OeTextColorAbgr);
        drawScreenText(layout, ComicFontName, std::to_string(enemy.magic), 561.0f, 161.0f, false, OeTextColorAbgr);
        drawScreenText(layout, ComicFontName, std::to_string(player.dungeon), 14.0f, 233.0f, false, OeTextColorAbgr);
        drawScreenText(layout, ComicFontName, std::to_string(enemy.dungeon), 561.0f, 233.0f, false, OeTextColorAbgr);
        drawScreenText(layout, ComicFontName, std::to_string(player.bricks), 10.0f, 109.0f, false, OeTextColorAbgr);
        drawScreenText(layout, ComicFontName, std::to_string(enemy.bricks), 557.0f, 109.0f, false, OeTextColorAbgr);
        drawScreenText(layout, ComicFontName, std::to_string(player.gems), 10.0f, 181.0f, false, OeTextColorAbgr);
        drawScreenText(layout, ComicFontName, std::to_string(enemy.gems), 557.0f, 181.0f, false, OeTextColorAbgr);
        drawScreenText(layout, ComicFontName, std::to_string(player.recruits), 10.0f, 253.0f, false, OeTextColorAbgr);
        drawScreenText(layout, ComicFontName, std::to_string(enemy.recruits), 557.0f, 253.0f, false, OeTextColorAbgr);
    }
}

void ArcomageScreen::drawShownCards(const LogicalLayout &layout)
{
    for (size_t index = 0; index < m_state.shownCards.size(); ++index)
    {
        if (hasCardAnimation() && index == m_cardAnimation->shownCardIndex)
        {
            continue;
        }

        if (!m_state.shownCards[index].has_value())
        {
            continue;
        }

        const ArcomagePlayedCard &shownCard = *m_state.shownCards[index];
        const ArcomageCardDefinition *pCard =
            m_pLibrary != nullptr ? m_pLibrary->cardById(shownCard.cardId) : nullptr;

        if (pCard == nullptr)
        {
            continue;
        }

        const Rect targetRect = shownCardLogicalRect(index);
        drawTextureRegionColor(
            "Sprites",
            cardSourceRect(*pCard),
            scaleLogicalRect(layout, targetRect),
            GrayTintColorAbgr
        );

        if (shownCard.discarded)
        {
            drawTextureRegion(
                "Sprites",
                DiscardedOverlaySourceRect,
                scaleLogicalRect(layout, Rect{targetRect.x + 2.0f, targetRect.y + 40.0f, 73.0f, 16.0f})
            );
        }
    }
}

void ArcomageScreen::drawAnimatedCard(const LogicalLayout &layout)
{
    if (!hasCardAnimation() || m_pLibrary == nullptr)
    {
        return;
    }

    const ArcomageCardDefinition *pCard = m_pLibrary->cardById(m_cardAnimation->cardId);

    if (pCard == nullptr)
    {
        return;
    }

    Rect targetRect = shownCardLogicalRect(m_cardAnimation->shownCardIndex);
    uint32_t tintColor = GrayTintColorAbgr;

    if (m_cardAnimation->kind == CardAnimationKind::PlayCard)
    {
        const Rect centerRect = {272.0f, 173.0f, CardWidth, CardHeight};

        if (m_cardAnimation->elapsedSeconds < PlayCardMoveToCenterSeconds)
        {
            targetRect = lerpRect(
                m_cardAnimation->originRect,
                centerRect,
                m_cardAnimation->elapsedSeconds / PlayCardMoveToCenterSeconds
            );
            tintColor = 0xffffffffu;
        }
        else if (m_cardAnimation->elapsedSeconds < PlayCardMoveToCenterSeconds + PlayCardHoldSeconds)
        {
            targetRect = centerRect;
            tintColor = 0xffffffffu;
        }
        else
        {
            targetRect = lerpRect(
                centerRect,
                shownCardLogicalRect(m_cardAnimation->shownCardIndex),
                (m_cardAnimation->elapsedSeconds - PlayCardMoveToCenterSeconds - PlayCardHoldSeconds)
                    / PlayCardMoveToTableSeconds
            );
        }
    }
    else
    {
        targetRect = lerpRect(
            m_cardAnimation->originRect,
            shownCardLogicalRect(m_cardAnimation->shownCardIndex),
            m_cardAnimation->elapsedSeconds / DiscardCardAnimationSeconds
        );
    }

    drawTextureRegionColor(
        "Sprites",
        cardSourceRect(*pCard),
        scaleLogicalRect(layout, targetRect),
        tintColor
    );

    if (m_cardAnimation->kind != CardAnimationKind::PlayCard || !m_cardAnimation->concealedHandIndex.has_value())
    {
        return;
    }

    const float drawStartSeconds = PlayCardMoveToCenterSeconds + PlayCardHoldSeconds;

    if (m_cardAnimation->elapsedSeconds < drawStartSeconds)
    {
        return;
    }

    if (m_cardAnimation->playerIndex >= m_state.players.size())
    {
        return;
    }

    const ArcomagePlayerState &player = m_state.players[m_cardAnimation->playerIndex];

    if (*m_cardAnimation->concealedHandIndex >= player.hand.size()
        || player.hand[*m_cardAnimation->concealedHandIndex] < 0)
    {
        return;
    }

    const Rect replacementTargetRect = handCardLogicalRect(
        player,
        *m_cardAnimation->concealedHandIndex,
        std::nullopt
    );
    const float drawProgress =
        clamp01((m_cardAnimation->elapsedSeconds - drawStartSeconds) / PlayCardMoveToTableSeconds);
    const Rect replacementRect = lerpRect(deckCardLogicalRect(), replacementTargetRect, drawProgress);
    drawTextureRegion(
        "Sprites",
        CardBackSourceRect,
        scaleLogicalRect(layout, replacementRect)
    );
}

std::vector<ArcomageScreen::HandCardPlacement> ArcomageScreen::drawCurrentHand(const LogicalLayout &layout)
{
    std::vector<HandCardPlacement> placements;

    size_t displayedPlayerIndex = m_state.currentPlayerIndex;

    if (hasCardAnimation())
    {
        displayedPlayerIndex = m_cardAnimation->playerIndex;
    }

    if (displayedPlayerIndex >= m_state.players.size())
    {
        return placements;
    }

    const ArcomagePlayerState &player = m_state.players[displayedPlayerIndex];
    const int cardCount = handCount(player);

    if (cardCount <= 0)
    {
        return placements;
    }

    const bool showFronts = displayedPlayerIndex == 0;

    for (size_t handIndex = 0; handIndex < player.hand.size(); ++handIndex)
    {
        if (player.hand[handIndex] < 0)
        {
            continue;
        }

        const Rect logicalRect = handCardLogicalRect(player, handIndex, m_hoveredHandIndex);
        placements.push_back({handIndex, logicalRect});

        if (showFronts)
        {
            const bool concealCardBack = hasCardAnimation()
                && m_cardAnimation->playerIndex == displayedPlayerIndex
                && m_cardAnimation->concealedHandIndex.has_value()
                && *m_cardAnimation->concealedHandIndex == handIndex;

            if (concealCardBack)
            {
                const float revealStartSeconds = PlayCardMoveToCenterSeconds + PlayCardHoldSeconds
                    + PlayCardMoveToTableSeconds;

                if (m_cardAnimation->elapsedSeconds >= revealStartSeconds)
                {
                    const ArcomageCardDefinition *pRevealedCard =
                        m_pLibrary != nullptr
                            ? m_pLibrary->cardById(static_cast<uint32_t>(player.hand[handIndex]))
                            : nullptr;

                    if (pRevealedCard != nullptr)
                    {
                        drawTextureRegion(
                            "Sprites",
                            cardSourceRect(*pRevealedCard),
                            scaleLogicalRect(layout, logicalRect)
                        );
                    }
                }

                continue;
            }

            const ArcomageCardDefinition *pCard =
                m_pLibrary != nullptr ? m_pLibrary->cardById(static_cast<uint32_t>(player.hand[handIndex])) : nullptr;

            if (pCard != nullptr)
            {
                const bool shouldGray = !m_state.mustDiscard
                    && (m_pLibrary == nullptr
                        || !m_rules.canPlayCard(*m_pLibrary, m_state, displayedPlayerIndex, handIndex));
                drawTextureRegionColor(
                    "Sprites",
                    cardSourceRect(*pCard),
                    scaleLogicalRect(layout, logicalRect),
                    shouldGray ? GrayTintColorAbgr : 0xffffffffu
                );
            }
        }
        else
        {
            drawTextureRegion(
                "Sprites",
                SourceRect{192.0f, 0.0f, CardWidth, CardHeight},
                scaleLogicalRect(layout, logicalRect)
            );
        }
    }

    return placements;
}

void ArcomageScreen::drawScreenText(
    const LogicalLayout &layout,
    const std::string &fontName,
    const std::string &text,
    float logicalX,
    float logicalY,
    bool centered,
    uint32_t colorAbgr,
    float scale)
{
    const float finalScale = layout.scale * scale;
    float pixelX = layout.rootX + logicalX * layout.scale;

    if (centered)
    {
        pixelX -= measureTextWidth(fontName, text, finalScale) * 0.5f;
    }

    drawText(
        fontName,
        text,
        pixelX,
        layout.rootY + logicalY * layout.scale,
        colorAbgr,
        finalScale,
        true
    );
}

void ArcomageScreen::updateHumanInput(
    const LogicalLayout &layout,
    const std::vector<HandCardPlacement> &handPlacements)
{
    if (hasCardAnimation())
    {
        m_hoveredHandIndex.reset();
        return;
    }

    m_hoveredHandIndex.reset();

    const float logicalMouseX = (mouseX() - layout.rootX) / layout.scale;
    const float logicalMouseY = (mouseY() - layout.rootY) / layout.scale;

    for (const HandCardPlacement &placement : handPlacements)
    {
        if (logicalMouseX >= placement.logicalRect.x
            && logicalMouseX <= placement.logicalRect.x + placement.logicalRect.width
            && logicalMouseY >= placement.logicalRect.y
            && logicalMouseY <= placement.logicalRect.y + placement.logicalRect.height)
        {
            m_hoveredHandIndex = placement.handIndex;
            break;
        }
    }

    const bool *pKeyboardState = SDL_GetKeyboardState(nullptr);
    const bool escapeDown = pKeyboardState != nullptr && pKeyboardState[SDL_SCANCODE_ESCAPE];

    if (escapeDown && !m_escapeLatch)
    {
        m_rules.resign(0, m_state);
    }

    m_escapeLatch = escapeDown;

    if (!m_hoveredHandIndex.has_value() || m_pLibrary == nullptr)
    {
        return;
    }

    if (leftMouseJustPressed())
    {
        for (const HandCardPlacement &placement : handPlacements)
        {
            if (placement.handIndex == *m_hoveredHandIndex)
            {
                startCardAnimation(
                    m_state.mustDiscard ? CardAnimationKind::DiscardCard : CardAnimationKind::PlayCard,
                    placement.handIndex,
                    placement.logicalRect
                );
                break;
            }
        }
    }

    if (rightMouseJustPressed())
    {
        for (const HandCardPlacement &placement : handPlacements)
        {
            if (placement.handIndex == *m_hoveredHandIndex)
            {
                startCardAnimation(CardAnimationKind::DiscardCard, placement.handIndex, placement.logicalRect);
                break;
            }
        }
    }
}

void ArcomageScreen::updateAiTurn(float deltaSeconds)
{
    m_hoveredHandIndex.reset();
    m_escapeLatch = false;

    if (m_state.result.finished || m_pLibrary == nullptr)
    {
        return;
    }

    if (hasCardAnimation())
    {
        return;
    }

    if (m_aiDecisionDelaySeconds > 0.0f)
    {
        m_aiDecisionDelaySeconds -= deltaSeconds;
        return;
    }

    const ArcomageAi::Action action = m_ai.chooseAction(*m_pLibrary, m_state);
    const Rect originRect = handCardLogicalRect(m_state.players[m_state.currentPlayerIndex], action.handIndex, std::nullopt);

    switch (action.kind)
    {
        case ArcomageAi::ActionKind::PlayCard:
            if (!startCardAnimation(CardAnimationKind::PlayCard, action.handIndex, originRect))
            {
                m_rules.resign(1, m_state);
            }
            break;

        case ArcomageAi::ActionKind::DiscardCard:
            if (!startCardAnimation(CardAnimationKind::DiscardCard, action.handIndex, originRect))
            {
                m_rules.resign(1, m_state);
            }
            break;

        case ArcomageAi::ActionKind::None:
            m_rules.resign(1, m_state);
            break;
    }
}

void ArcomageScreen::updateResultDelay(float deltaSeconds)
{
    if (m_resultDelaySeconds <= 0.0f)
    {
        return;
    }

    m_hoveredHandIndex.reset();
    m_escapeLatch = false;
    m_resultDelaySeconds = std::max(0.0f, m_resultDelaySeconds - deltaSeconds);

    if (m_resultDelaySeconds <= 0.0f && m_state.result.winnerIndex.has_value())
    {
        m_shouldClose = true;
    }
}

void ArcomageScreen::updateCardAnimation(float deltaSeconds)
{
    if (!hasCardAnimation())
    {
        return;
    }

    m_cardAnimation->elapsedSeconds += deltaSeconds;
    const float animationDuration = m_cardAnimation->kind == CardAnimationKind::PlayCard
        ? PlayCardMoveToCenterSeconds + PlayCardHoldSeconds + PlayCardMoveToTableSeconds
        : DiscardCardAnimationSeconds;

    if (m_cardAnimation->elapsedSeconds < animationDuration)
    {
        return;
    }

    m_cardAnimation.reset();
    m_hoveredHandIndex.reset();
    m_aiDecisionDelaySeconds = (m_state.currentPlayerIndex == 1 && !m_state.result.finished) ? AiTurnDelaySeconds : 0.0f;
}

void ArcomageScreen::updateFinishInput()
{
    m_hoveredHandIndex.reset();
    const bool *pKeyboardState = SDL_GetKeyboardState(nullptr);
    const bool escapeDown = pKeyboardState != nullptr && pKeyboardState[SDL_SCANCODE_ESCAPE];

    if ((escapeDown && !m_escapeLatch) || leftMouseJustPressed() || rightMouseJustPressed())
    {
        m_shouldClose = true;
    }

    m_escapeLatch = escapeDown;
}

bool ArcomageScreen::hasCardAnimation() const
{
    return m_cardAnimation.has_value();
}

bool ArcomageScreen::startCardAnimation(CardAnimationKind kind, size_t handIndex, const Rect &originRect)
{
    if (hasCardAnimation()
        || m_pLibrary == nullptr
        || m_state.currentPlayerIndex >= m_state.players.size()
        || handIndex >= m_state.players[m_state.currentPlayerIndex].hand.size())
    {
        return false;
    }

    const size_t playerIndex = m_state.currentPlayerIndex;
    const int cardId = m_state.players[playerIndex].hand[handIndex];

    if (cardId < 0)
    {
        return false;
    }

    const ArcomageCardDefinition *pCard = m_pLibrary->cardById(static_cast<uint32_t>(cardId));

    if (pCard == nullptr)
    {
        return false;
    }

    const ArcomageState previousState = m_state;
    bool actionResult = false;

    switch (kind)
    {
        case CardAnimationKind::PlayCard:
            actionResult = m_rules.playCard(*m_pLibrary, handIndex, m_state);
            break;

        case CardAnimationKind::DiscardCard:
            actionResult = m_rules.discardCard(*m_pLibrary, handIndex, m_state);
            break;

        case CardAnimationKind::None:
            break;
    }

    if (!actionResult)
    {
        return false;
    }

    playActionSounds(kind, *pCard, previousState, m_state);

    size_t shownCardIndex = m_state.shownCards.size();

    for (size_t index = m_state.shownCards.size(); index > 0; --index)
    {
        const std::optional<ArcomagePlayedCard> &shownCard = m_state.shownCards[index - 1];

        if (!shownCard.has_value())
        {
            continue;
        }

        if (shownCard->cardId == static_cast<uint32_t>(cardId)
            && shownCard->playerIndex == playerIndex
            && shownCard->discarded == (kind == CardAnimationKind::DiscardCard))
        {
            shownCardIndex = index - 1;
            break;
        }
    }

    if (shownCardIndex >= m_state.shownCards.size())
    {
        return false;
    }

    std::optional<size_t> concealedHandIndex;

    if (kind == CardAnimationKind::PlayCard)
    {
        const ArcomagePlayerState &previousPlayer = previousState.players[playerIndex];
        const ArcomagePlayerState &currentPlayer = m_state.players[playerIndex];

        if (handIndex < currentPlayer.hand.size()
            && currentPlayer.hand[handIndex] >= 0
            && currentPlayer.hand[handIndex] != previousPlayer.hand[handIndex])
        {
            concealedHandIndex = handIndex;
        }
        else
        {
            for (size_t slotIndex = 0; slotIndex < currentPlayer.hand.size(); ++slotIndex)
            {
                if (currentPlayer.hand[slotIndex] >= 0
                    && previousPlayer.hand[slotIndex] != currentPlayer.hand[slotIndex])
                {
                    concealedHandIndex = slotIndex;
                    break;
                }
            }
        }
    }

    m_cardAnimation = CardAnimation {
        kind,
        playerIndex,
        handIndex,
        shownCardIndex,
        static_cast<uint32_t>(cardId),
        concealedHandIndex,
        originRect,
        0.0f
    };
    m_aiDecisionDelaySeconds = 0.0f;
    return true;
}

bool ArcomageScreen::startTurnIfNeeded()
{
    if (m_pLibrary == nullptr || hasCardAnimation() || m_state.result.finished)
    {
        return false;
    }

    const ArcomageState previousState = m_state;

    if (!m_rules.startTurn(*m_pLibrary, m_state))
    {
        return false;
    }

    playTurnStartSounds(previousState, m_state);
    playResultSound(previousState.result, m_state.result);
    return true;
}

void ArcomageScreen::playArcomageSound(SoundId soundId) const
{
    if (m_pGameAudioSystem == nullptr)
    {
        return;
    }

    m_pGameAudioSystem->playCommonSound(soundId, GameAudioSystem::PlaybackGroup::Ui);
}

void ArcomageScreen::playRepeatedArcomageSound(SoundId soundId, int count) const
{
    for (int index = 0; index < count; ++index)
    {
        playArcomageSound(soundId);
    }
}

void ArcomageScreen::playResultSound(const ArcomageResult &previousResult, const ArcomageResult &currentResult)
{
    if (!currentResult.finished || previousResult.finished)
    {
        return;
    }

    if (currentResult.winnerIndex == 0)
    {
        playArcomageSound(SoundId::ArcomageVictory);
        m_resultDelaySeconds = ResultAutoCloseSeconds;
    }
    else if (currentResult.winnerIndex.has_value())
    {
        playArcomageSound(SoundId::ArcomageDefeat);
        m_resultDelaySeconds = ResultAutoCloseSeconds;
    }
}

void ArcomageScreen::playTurnStartSounds(const ArcomageState &previousState, const ArcomageState &currentState)
{
    if (didDeckWrap(previousState, currentState))
    {
        playArcomageSound(SoundId::ArcomageShuffle);
    }

    playRepeatedArcomageSound(SoundId::ArcomageDeal, cardsDrawnBetweenStates(previousState, currentState));
}

void ArcomageScreen::playActionSounds(
    CardAnimationKind kind,
    const ArcomageCardDefinition &card,
    const ArcomageState &previousState,
    const ArcomageState &currentState)
{
    if (kind == CardAnimationKind::PlayCard || kind == CardAnimationKind::DiscardCard)
    {
        playArcomageSound(SoundId::ArcomageDeal);
    }

    if (didDeckWrap(previousState, currentState))
    {
        playArcomageSound(SoundId::ArcomageShuffle);
    }

    if (kind == CardAnimationKind::PlayCard)
    {
        const ArcomagePlayerState &previousPlayer = previousState.players[previousState.currentPlayerIndex];
        const ArcomagePlayerState &currentPlayer = currentState.players[previousState.currentPlayerIndex];
        const int previousHandCount = handCount(previousPlayer);
        const int currentHandCount = handCount(currentPlayer);
        const int extraDrawCount = std::max(0, currentHandCount - previousHandCount + 1);
        playRepeatedArcomageSound(SoundId::ArcomageDeal, extraDrawCount);
    }

    ArcomageState adjustedPreviousState = previousState;

    if (kind == CardAnimationKind::PlayCard && previousState.currentPlayerIndex < adjustedPreviousState.players.size())
    {
        ArcomagePlayerState &actingPlayer = adjustedPreviousState.players[previousState.currentPlayerIndex];
        actingPlayer.bricks = std::max(0, actingPlayer.bricks - card.needBricks);
        actingPlayer.gems = std::max(0, actingPlayer.gems - card.needGems);
        actingPlayer.recruits = std::max(0, actingPlayer.recruits - card.needRecruits);
    }

    playDeltaSounds(adjustedPreviousState, currentState);
    playResultSound(previousState.result, currentState.result);
}

void ArcomageScreen::playDeltaSounds(const ArcomageState &previousState, const ArcomageState &currentState) const
{
    const ArcomagePlayerState &previousPlayer = previousState.players[0];
    const ArcomagePlayerState &previousEnemy = previousState.players[1];
    const ArcomagePlayerState &currentPlayer = currentState.players[0];
    const ArcomagePlayerState &currentEnemy = currentState.players[1];

    const int quarryDelta =
        (currentPlayer.quarry - previousPlayer.quarry) + (currentEnemy.quarry - previousEnemy.quarry);
    const int magicDelta =
        (currentPlayer.magic - previousPlayer.magic) + (currentEnemy.magic - previousEnemy.magic);
    const int dungeonDelta =
        (currentPlayer.dungeon - previousPlayer.dungeon) + (currentEnemy.dungeon - previousEnemy.dungeon);
    const int bricksDelta =
        (currentPlayer.bricks - previousPlayer.bricks) + (currentEnemy.bricks - previousEnemy.bricks);
    const int gemsDelta =
        (currentPlayer.gems - previousPlayer.gems) + (currentEnemy.gems - previousEnemy.gems);
    const int recruitsDelta =
        (currentPlayer.recruits - previousPlayer.recruits) + (currentEnemy.recruits - previousEnemy.recruits);
    const int wallDelta =
        (currentPlayer.wall - previousPlayer.wall) + (currentEnemy.wall - previousEnemy.wall);
    const int towerDelta =
        (currentPlayer.tower - previousPlayer.tower) + (currentEnemy.tower - previousEnemy.tower);

    if (quarryDelta > 0)
    {
        playArcomageSound(SoundId::ArcomageQuarryDown);
    }
    if (quarryDelta < 0)
    {
        playArcomageSound(SoundId::ArcomageQuarryUp);
    }
    if (magicDelta > 0)
    {
        playArcomageSound(SoundId::ArcomageQuarryDown);
    }
    if (magicDelta < 0)
    {
        playArcomageSound(SoundId::ArcomageQuarryUp);
    }
    if (dungeonDelta > 0)
    {
        playArcomageSound(SoundId::ArcomageQuarryDown);
    }
    if (dungeonDelta < 0)
    {
        playArcomageSound(SoundId::ArcomageQuarryUp);
    }
    if (bricksDelta > 0)
    {
        playArcomageSound(SoundId::ArcomageBricksUp);
    }
    if (bricksDelta < 0)
    {
        playArcomageSound(SoundId::ArcomageBricksDown);
    }
    if (gemsDelta > 0)
    {
        playArcomageSound(SoundId::ArcomageBricksUp);
    }
    if (gemsDelta < 0)
    {
        playArcomageSound(SoundId::ArcomageBricksDown);
    }
    if (recruitsDelta > 0)
    {
        playArcomageSound(SoundId::ArcomageBricksUp);
    }
    if (recruitsDelta < 0)
    {
        playArcomageSound(SoundId::ArcomageBricksDown);
    }
    if (wallDelta > 0)
    {
        playArcomageSound(SoundId::ArcomageWallUp);
    }
    if (wallDelta < 0)
    {
        playArcomageSound(SoundId::ArcomageDamage);
    }
    if (towerDelta > 0)
    {
        playArcomageSound(SoundId::ArcomageTowerUp);
    }
    if (towerDelta < 0)
    {
        playArcomageSound(SoundId::ArcomageDamage);
    }
}

std::string ArcomageScreen::resultText() const
{
    if (!m_state.result.finished)
    {
        return {};
    }

    if (!m_state.result.winnerIndex.has_value())
    {
        return "Arcomage ended in a draw.";
    }

    if (*m_state.result.winnerIndex == 0)
    {
        return "You have won " + std::to_string(m_winGoldReward) + " gold!";
    }

    return "You lost the Arcomage match.";
}

std::string ArcomageScreen::hoveredCardText() const
{
    if (!m_hoveredHandIndex.has_value()
        || m_state.currentPlayerIndex >= m_state.players.size()
        || m_pLibrary == nullptr)
    {
        return {};
    }

    const ArcomagePlayerState &player = m_state.players[m_state.currentPlayerIndex];
    const int cardId = player.hand[*m_hoveredHandIndex];

    if (cardId < 0)
    {
        return {};
    }

    const ArcomageCardDefinition *pCard = m_pLibrary->cardById(static_cast<uint32_t>(cardId));

    if (pCard == nullptr)
    {
        return {};
    }

    int cost = 0;

    switch (pCard->resourceType)
    {
        case ArcomageResourceType::Bricks:
            cost = pCard->needBricks;
            break;

        case ArcomageResourceType::Gems:
            cost = pCard->needGems;
            break;

        case ArcomageResourceType::Recruits:
            cost = pCard->needRecruits;
            break;

        case ArcomageResourceType::None:
            break;
    }

    return pCard->name + "  " + std::to_string(cost) + " " + resourceTypeName(pCard->resourceType);
}

int ArcomageScreen::currentHandCount() const
{
    if (m_state.currentPlayerIndex >= m_state.players.size())
    {
        return 0;
    }

    return handCount(m_state.players[m_state.currentPlayerIndex]);
}
}
