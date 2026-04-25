#pragma once

#include "game/events/EventDialogContent.h"
#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayDialogContextBuilder.h"
#include "game/gameplay/GameplayDialogController.h"
#include "game/ui/GameplayUiController.h"

#include "tests/PartySpellTestHarness.h"
#include "tests/RegressionGameData.h"

#include <cstdint>
#include <optional>
#include <string>

namespace OpenYAMM::Tests
{
class HouseDialogueTestHarness
{
public:
    explicit HouseDialogueTestHarness(const RegressionGameData &gameData)
        : m_gameData(gameData),
          m_party(makeSpellRegressionParty(gameData))
    {
        m_worldRuntime.bindParty(&m_party);
        m_worldRuntime.bindEventRuntimeState(&m_eventRuntimeState);
        m_worldRuntime.bindGlobalEventProgram(&m_gameData.globalEventProgram);
        m_worldRuntime.advanceGameMinutes(12.0f * 60.0f);
    }

    Game::Party &party()
    {
        return m_party;
    }

    const Game::Party &party() const
    {
        return m_party;
    }

    Game::EventRuntimeState &eventRuntimeState()
    {
        return m_eventRuntimeState;
    }

    const Game::EventRuntimeState &eventRuntimeState() const
    {
        return m_eventRuntimeState;
    }

    Game::GameplayUiController &uiController()
    {
        return m_uiController;
    }

    const Game::GameplayUiController &uiController() const
    {
        return m_uiController;
    }

    PartySpellTestWorldRuntime &worldRuntime()
    {
        return m_worldRuntime;
    }

    const PartySpellTestWorldRuntime &worldRuntime() const
    {
        return m_worldRuntime;
    }

    const Game::EventDialogContent &activeDialog() const
    {
        return m_uiController.eventDialog().content;
    }

    bool executeOut01LocalEvent(uint16_t eventId)
    {
        return executeEvent(m_gameData.out01LocalEventProgram, m_gameData.globalEventProgram, eventId);
    }

    bool executeGlobalEvent(uint16_t eventId)
    {
        return executeEvent(std::nullopt, m_gameData.globalEventProgram, eventId);
    }

    const Game::EventDialogContent &openHouseDialog(uint32_t houseId)
    {
        Game::EventRuntimeState::PendingDialogueContext pendingContext = {};
        pendingContext.kind = Game::DialogueContextKind::HouseService;
        pendingContext.sourceId = houseId;
        pendingContext.hostHouseId = houseId;
        m_eventRuntimeState.pendingDialogueContext = pendingContext;
        return presentPendingDialog(0, true);
    }

    const Game::EventDialogContent &openNpcDialogue(uint32_t npcId, uint32_t hostHouseId = 0)
    {
        Game::GameplayDialogController::Context context = buildContext();
        const Game::GameplayDialogController::Result result =
            m_controller.openNpcDialogue(context, npcId, hostHouseId);
        return presentPendingDialog(result.previousMessageCount, result.allowNpcFallbackContent);
    }

    const Game::EventDialogContent &openNpcNews(
        uint32_t npcId,
        uint32_t newsId,
        const std::string &titleOverride,
        const std::string &newsText)
    {
        Game::GameplayDialogController::Context context = buildContext();
        const Game::GameplayDialogController::Result result =
            m_controller.openNpcNews(context, npcId, newsId, titleOverride, newsText);
        return presentPendingDialog(result.previousMessageCount, result.allowNpcFallbackContent);
    }

    const Game::EventDialogContent &presentPendingDialog(
        size_t previousMessageCount,
        bool allowNpcFallbackContent,
        bool showBankInputCursor = false)
    {
        Game::GameplayDialogController::Context context = buildContext();
        m_controller.presentPendingEventDialog(
            context,
            previousMessageCount,
            allowNpcFallbackContent,
            showBankInputCursor);
        return m_uiController.eventDialog().content;
    }

    Game::GameplayDialogController::Result executeActiveDialogAction(size_t actionIndex)
    {
        m_uiController.eventDialog().selectionIndex = actionIndex;
        Game::GameplayDialogController::Context context = buildContext();
        return m_controller.executeActiveDialogAction(context);
    }

    const Game::EventDialogContent &executeAndPresent(size_t actionIndex)
    {
        const Game::GameplayDialogController::Result result = executeActiveDialogAction(actionIndex);

        if (result.shouldOpenPendingEventDialog)
        {
            return presentPendingDialog(result.previousMessageCount, result.allowNpcFallbackContent);
        }

        if (result.shouldCloseActiveDialog)
        {
            m_uiController.clearEventDialog();
        }

        return m_uiController.eventDialog().content;
    }

    const Game::EventDialogContent &refreshCurrentHouseDialog()
    {
        const uint32_t houseId = m_eventRuntimeState.dialogueState.hostHouseId;

        if (houseId == 0)
        {
            return m_uiController.eventDialog().content;
        }

        Game::EventRuntimeState::PendingDialogueContext pendingContext = {};
        pendingContext.kind = Game::DialogueContextKind::HouseService;
        pendingContext.sourceId = houseId;
        pendingContext.hostHouseId = houseId;
        m_eventRuntimeState.pendingDialogueContext = pendingContext;
        return presentPendingDialog(0, true);
    }

    const Game::EventDialogContent &refreshCurrentNpcDialog()
    {
        uint32_t npcId = m_uiController.eventDialog().content.sourceId;

        if (m_eventRuntimeState.dialogueState.currentOffer.has_value()
            && m_eventRuntimeState.dialogueState.currentOffer->npcId != 0)
        {
            npcId = m_eventRuntimeState.dialogueState.currentOffer->npcId;
        }

        if (npcId == 0)
        {
            return m_uiController.eventDialog().content;
        }

        Game::EventRuntimeState::PendingDialogueContext pendingContext = {};
        pendingContext.kind = Game::DialogueContextKind::NpcTalk;
        pendingContext.sourceId = npcId;
        pendingContext.hostHouseId = m_eventRuntimeState.dialogueState.hostHouseId;
        m_eventRuntimeState.pendingDialogueContext = pendingContext;
        return presentPendingDialog(0, true);
    }

    const Game::EventDialogContent &openMasteryTeacherOffer(
        uint32_t npcId,
        const std::string &topicLabel,
        uint32_t hostHouseId = 0)
    {
        const Game::EventDialogContent &dialog = openNpcDialogue(npcId, hostHouseId);

        for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
        {
            if (dialog.actions[actionIndex].label == topicLabel)
            {
                return executeAndPresent(actionIndex);
            }
        }

        return m_uiController.eventDialog().content;
    }

    const Game::EventDialogContent &confirmHouseBankInput(const std::string &inputText)
    {
        m_uiController.houseBankState().inputText = inputText;

        Game::GameplayDialogController::Context context = buildContext();
        const Game::GameplayDialogController::Result result = m_controller.confirmHouseBankInput(context);

        if (result.shouldOpenPendingEventDialog)
        {
            return presentPendingDialog(result.previousMessageCount, result.allowNpcFallbackContent);
        }

        if (result.shouldCloseActiveDialog)
        {
            m_uiController.clearEventDialog();
        }

        return m_uiController.eventDialog().content;
    }

    Game::EventDialogContent buildPendingDialogContent(
        size_t previousMessageCount,
        bool allowNpcFallbackContent)
    {
        return Game::buildEventDialogContent(
            m_eventRuntimeState,
            previousMessageCount,
            allowNpcFallbackContent,
            &m_gameData.globalEventProgram,
            &m_gameData.houseTable,
            &m_gameData.classSkillTable,
            &m_gameData.npcDialogTable,
            &m_gameData.transitionTable,
            nullptr,
            nullptr,
            &m_party,
            &m_worldRuntime,
            m_worldRuntime.gameMinutes());
    }

private:
    bool executeEvent(
        const std::optional<Game::ScriptedEventProgram> &localEventProgram,
        const std::optional<Game::ScriptedEventProgram> &globalEventProgram,
        uint16_t eventId)
    {
        Game::EventRuntime eventRuntime = {};
        const bool executed = eventRuntime.executeEventById(
            localEventProgram,
            globalEventProgram,
            eventId,
            m_eventRuntimeState,
            &m_party);

        if (executed)
        {
            m_party.applyEventRuntimeState(m_eventRuntimeState);
        }

        return executed;
    }

    Game::GameplayDialogController::Context buildContext()
    {
        return Game::buildGameplayDialogContext(
            m_uiController,
            m_eventRuntimeState,
            m_uiController.eventDialog().content,
            m_uiController.eventDialog().selectionIndex,
            &m_party,
            &m_worldRuntime,
            &m_gameData.globalEventProgram,
            &m_gameData.houseTable,
            &m_gameData.classSkillTable,
            &m_gameData.npcDialogTable,
            &m_gameData.transitionTable,
            nullptr,
            nullptr,
            &m_gameData.rosterTable,
            &m_gameData.arcomageLibrary,
            true,
            nullptr);
    }

    const RegressionGameData &m_gameData;
    Game::Party m_party = {};
    PartySpellTestWorldRuntime m_worldRuntime = {};
    Game::GameplayUiController m_uiController = {};
    Game::GameplayDialogController m_controller = {};
    Game::EventRuntimeState m_eventRuntimeState = {};
};
}
