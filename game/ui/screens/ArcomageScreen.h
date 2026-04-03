#pragma once

#include "game/arcomage/ArcomageAi.h"
#include "game/arcomage/ArcomageRules.h"
#include "game/audio/SoundIds.h"
#include "game/ui/MenuScreenBase.h"

namespace OpenYAMM::Game
{
class GameAudioSystem;

class ArcomageScreen : public MenuScreenBase
{
public:
    ArcomageScreen(
        const Engine::AssetFileSystem &assetFileSystem,
        GameAudioSystem *pGameAudioSystem,
        const ArcomageLibrary &library,
        uint32_t houseId,
        const std::string &playerName,
        const std::string &opponentName,
        int winGoldReward,
        uint32_t randomSeed);

    AppMode mode() const override;

    bool shouldClose() const;
    const ArcomageState &state() const;

private:
    enum class CardAnimationKind : uint8_t
    {
        None = 0,
        PlayCard,
        DiscardCard,
    };

    struct LogicalLayout
    {
        float rootX = 0.0f;
        float rootY = 0.0f;
        float scale = 1.0f;
    };

    struct HandCardPlacement
    {
        size_t handIndex = 0;
        Rect logicalRect = {};
    };

    struct CardAnimation
    {
        CardAnimationKind kind = CardAnimationKind::None;
        size_t playerIndex = 0;
        size_t handIndex = 0;
        size_t shownCardIndex = 0;
        uint32_t cardId = 0;
        std::optional<size_t> concealedHandIndex;
        Rect originRect = {};
        float elapsedSeconds = 0.0f;
    };

    void drawScreen(float deltaSeconds) override;
    Rect scaleLogicalRect(const LogicalLayout &layout, const Rect &logicalRect) const;
    MenuScreenBase::SourceRect cardSourceRect(const ArcomageCardDefinition &card) const;
    Rect shownCardLogicalRect(size_t index) const;
    Rect handCardLogicalRect(
        const ArcomagePlayerState &player,
        size_t handIndex,
        std::optional<size_t> hoveredHandIndex) const;
    void drawBuildings(const LogicalLayout &layout);
    void drawPanels(const LogicalLayout &layout);
    void drawShownCards(const LogicalLayout &layout);
    void drawAnimatedCard(const LogicalLayout &layout);
    std::vector<HandCardPlacement> drawCurrentHand(const LogicalLayout &layout);
    void drawScreenText(
        const LogicalLayout &layout,
        const std::string &fontName,
        const std::string &text,
        float logicalX,
        float logicalY,
        bool centered,
        uint32_t colorAbgr = 0xffffffffu,
        float scale = 1.0f);
    void updateHumanInput(const LogicalLayout &layout, const std::vector<HandCardPlacement> &handPlacements);
    void updateAiTurn(float deltaSeconds);
    void updateResultDelay(float deltaSeconds);
    void updateCardAnimation(float deltaSeconds);
    void updateFinishInput();
    bool hasCardAnimation() const;
    bool startCardAnimation(CardAnimationKind kind, size_t handIndex, const Rect &originRect);
    bool startTurnIfNeeded();
    void playArcomageSound(SoundId soundId) const;
    void playRepeatedArcomageSound(SoundId soundId, int count) const;
    void playResultSound(const ArcomageResult &previousResult, const ArcomageResult &currentResult);
    void playTurnStartSounds(const ArcomageState &previousState, const ArcomageState &currentState);
    void playActionSounds(
        CardAnimationKind kind,
        const ArcomageCardDefinition &card,
        const ArcomageState &previousState,
        const ArcomageState &currentState);
    void playDeltaSounds(const ArcomageState &previousState, const ArcomageState &currentState) const;
    std::string resultText() const;
    std::string hoveredCardText() const;
    int currentHandCount() const;

    GameAudioSystem *m_pGameAudioSystem = nullptr;
    const ArcomageLibrary *m_pLibrary = nullptr;
    ArcomageRules m_rules;
    ArcomageAi m_ai;
    ArcomageState m_state = {};
    mutable std::optional<size_t> m_hoveredHandIndex;
    bool m_escapeLatch = false;
    bool m_shouldClose = false;
    std::optional<CardAnimation> m_cardAnimation;
    float m_aiDecisionDelaySeconds = 0.0f;
    float m_resultDelaySeconds = 0.0f;
    int m_winGoldReward = 0;
};
}
