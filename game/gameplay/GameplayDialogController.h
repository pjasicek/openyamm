#pragma once

#include "game/events/EventDialogContent.h"
#include "game/events/EventRuntime.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/arcomage/ArcomageTypes.h"
#include "game/audio/SoundIds.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/party/SpeechIds.h"
#include "game/ui/GameplayUiController.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
class ClassSkillTable;
class HouseTable;
struct MapStatsEntry;
class NpcDialogTable;
class Party;
class RosterTable;
struct HouseEntry;
class GameplayScreenRuntime;

class GameplayDialogController
{
public:
    struct Context
    {
        GameplayUiController &uiController;
        EventRuntimeState &eventRuntimeState;
        EventDialogContent &activeEventDialog;
        size_t &selectionIndex;
        GameplayScreenRuntime *pScreenRuntime = nullptr;
        Party *pParty = nullptr;
        IGameplayWorldRuntime *pWorldRuntime = nullptr;
        const std::optional<ScriptedEventProgram> *pGlobalEventProgram = nullptr;
        const HouseTable *pHouseTable = nullptr;
        const ClassSkillTable *pClassSkillTable = nullptr;
        const NpcDialogTable *pNpcDialogTable = nullptr;
        const MapStatsEntry *pCurrentMap = nullptr;
        const std::vector<MapStatsEntry> *pMapEntries = nullptr;
        const RosterTable *pRosterTable = nullptr;
        const ArcomageLibrary *pArcomageLibrary = nullptr;
        bool dialogueHudActive = false;
    };

    struct Result
    {
        size_t previousMessageCount = 0;
        bool shouldOpenPendingEventDialog = false;
        bool allowNpcFallbackContent = true;
        bool shouldCloseActiveDialog = false;
        std::optional<InnRestRequest> pendingInnRest;
    };

    struct PresentPendingDialogResult
    {
        bool dialogOpened = false;
        bool wasDialogAlreadyActive = false;
        EventRuntimeState::PendingDialogueContext resolvedContext = {};
    };

    struct CloseDialogRequestResult
    {
        size_t previousMessageCount = 0;
        bool shouldOpenPendingEventDialog = false;
        bool allowNpcFallbackContent = true;
        bool shouldCloseActiveDialog = false;
    };

    Result executeActiveDialogAction(Context &context) const;
    PresentPendingDialogResult presentPendingEventDialog(
        Context &context,
        size_t previousMessageCount,
        bool allowNpcFallbackContent,
        bool showBankInputCursor) const;
    Result openNpcDialogue(Context &context, uint32_t npcId, uint32_t hostHouseId = 0) const;
    Result openNpcNews(
        Context &context,
        uint32_t npcId,
        uint32_t newsId,
        const std::string &titleOverride,
        const std::string &newsText) const;
    CloseDialogRequestResult handleDialogueCloseRequest(Context &context) const;
    bool refreshHouseBankInputDialog(Context &context, bool showCursor) const;
    Result returnToHouseBankMainDialog(Context &context) const;
    Result confirmHouseBankInput(Context &context) const;
    bool rejectClosedHouseInteraction(Context &context, const HouseEntry &houseEntry) const;
};
}
