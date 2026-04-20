#pragma once

#include "game/audio/GameAudioSystem.h"
#include "game/app/GameSettings.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/ItemEquipPosTable.h"
#include "game/party/SpeechIds.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/CharacterInspectTable.h"
#include "game/tables/ChestTable.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/HouseTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/JournalAutonoteTable.h"
#include "game/tables/JournalHistoryTable.h"
#include "game/tables/JournalQuestTable.h"
#include "game/tables/NpcDialogTable.h"
#include "game/tables/ReadableScrollTable.h"
#include "game/tables/RosterTable.h"
#include "game/tables/SpellTable.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/GameplayUiController.h"
#include "game/ui/UiLayoutManager.h"

#include <SDL3/SDL.h>
#include <bgfx/bgfx.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class IGameplayWorldRuntime;
struct HouseEntry;

class IGameplayOverlaySceneAdapter
{
public:
    virtual ~IGameplayOverlaySceneAdapter() = default;

    virtual float gameplayCameraYawRadians() const = 0;

    virtual void executeActiveDialogAction() = 0;
    virtual bool tryUseHeldItemOnPartyMember(size_t memberIndex, bool keepCharacterScreenOpen) = 0;
    virtual bool tryCastSpellFromMember(
        size_t casterMemberIndex,
        uint32_t spellId,
        const std::string &spellName) = 0;
    virtual bool tryCastSpellRequest(
        const PartySpellCastRequest &request,
        const std::string &spellName) = 0;
    virtual bool trySaveToSelectedGameSlot() = 0;
};
}
