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
#include <functional>
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
class SpellTable;
class TransitionTable;
class MergedNpcProfessionTable;
class MergedNewsProfessionTopicTable;
class MergedNpcBtbTable;
class MergedBolsterMapTable;
class MergedContinentSettingTable;
class MergedTeacherAutonoteTable;
class MergedTeacherTopicTable;
class Mm9RudeDialogueTable;
class Mm9MapTransitionTable;
class Mm9SkillTrainerTable;
class Mm9TransportRouteTable;
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
        const Mm9RudeDialogueTable *pMm9RudeDialogueTable = nullptr;
        const Mm9MapTransitionTable *pMm9MapTransitionTable = nullptr;
        const Mm9SkillTrainerTable *pMm9SkillTrainerTable = nullptr;
        const Mm9TransportRouteTable *pMm9TransportRouteTable = nullptr;
        const TransitionTable *pTransitionTable = nullptr;
        const MapStatsEntry *pCurrentMap = nullptr;
        const std::vector<MapStatsEntry> *pMapEntries = nullptr;
        const RosterTable *pRosterTable = nullptr;
        const ArcomageLibrary *pArcomageLibrary = nullptr;
        const MergedNpcProfessionTable *pNpcProfessionTable = nullptr;
        const MergedNewsProfessionTopicTable *pNewsProfessionTopicTable = nullptr;
        const MergedNpcBtbTable *pNpcBtbTable = nullptr;
        const MergedBolsterMapTable *pBolsterMapTable = nullptr;
        const MergedContinentSettingTable *pContinentSettingTable = nullptr;
        const MergedTeacherTopicTable *pTeacherTopicTable = nullptr;
        const MergedTeacherAutonoteTable *pTeacherAutonoteTable = nullptr;
        bool dialogueHudActive = false;
        const SpellTable *pSpellTable = nullptr;
        // Executed instead of the selected topic: an action offered by a popup over the dialogue (a trip chosen in
        // a stable's schedule).
        std::optional<EventDialogAction> actionOverride;
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
    Result openNpcDialogue(
        Context &context,
        uint32_t npcId,
        uint32_t hostHouseId = 0,
        std::optional<uint32_t> sourceActorIndex = std::nullopt) const;
    Result openMm9RudeDialogue(
        Context &context,
        uint32_t rudeId,
        std::optional<uint32_t> sourceActorIndex = std::nullopt) const;
    // What a click on an MM9 dialogue actor (MapDeltaActor::mm9RudeId > 0) knows, indoors and outdoors.
    struct Mm9ActorDialogueActivation
    {
        uint32_t rudeId = 0;
        uint32_t actorIndex = 0;
        std::optional<uint32_t> sourceObjectIndex;
        const std::optional<ScriptedEventProgram> *pLocalEventProgram = nullptr;
    };

    // Runs the actor's compiled SCR Use routine when the map has one (it opens the dialogue itself), else opens its
    // RUDE dialogue, with the actor as the dialogue's source so OnRudeExit runs. presentPendingDialog(previous message
    // count) presents what the SCR routine left pending, presentActiveDialog the opened RUDE dialogue. Sets
    // lastActivationResult; returns whether the actor was activated.
    bool activateMm9ActorDialogue(
        Context &context,
        const Mm9ActorDialogueActivation &activation,
        const std::function<void(size_t)> &presentPendingDialog,
        const std::function<void()> &presentActiveDialog) const;
    Result openNpcNews(
        Context &context,
        uint32_t npcId,
        uint32_t newsId,
        const std::string &titleOverride,
        const std::string &newsText,
        uint32_t participantPictureId = 0,
        std::optional<uint32_t> sourceActorIndex = std::nullopt) const;
    CloseDialogRequestResult handleDialogueCloseRequest(Context &context) const;
    bool refreshHouseBankInputDialog(Context &context, bool showCursor) const;
    Result returnToHouseBankMainDialog(Context &context) const;
    // A message in the open dialog of the house (an Arcomage match's result in its tavern).
    Result showHouseServiceMessage(Context &context, uint32_t houseId, const std::string &message) const;
    Result confirmHouseBankInput(Context &context) const;
    bool rejectClosedHouseInteraction(Context &context, const HouseEntry &houseEntry) const;
};
}
