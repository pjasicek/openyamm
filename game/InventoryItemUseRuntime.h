#pragma once

#include "game/Party.h"
#include "game/ReadableScrollTable.h"
#include "game/SkillData.h"
#include "game/SpeechIds.h"

#include <cstdint>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class ItemTable;

enum class InventoryItemUseAction : uint8_t
{
    None = 0,
    Equip,
    CastScroll,
    LearnSpell,
    ConsumePotion,
    ReadMessageScroll,
    UseHorseshoe,
};

struct InventoryItemUseResult
{
    bool handled = false;
    bool consumed = false;
    InventoryItemUseAction action = InventoryItemUseAction::None;
    bool alreadyKnown = false;
    uint32_t spellId = 0;
    uint32_t spellSkillLevelOverride = 0;
    SkillMastery spellSkillMasteryOverride = SkillMastery::None;
    std::string statusText;
    std::optional<SpeechId> speechId;
    std::string readableTitle;
    std::string readableBody;
};

class InventoryItemUseRuntime
{
public:
    static InventoryItemUseAction classifyItemUse(const InventoryItem &item, const ItemTable &itemTable);

    static InventoryItemUseResult useItemOnMember(
        Party &party,
        size_t targetMemberIndex,
        const InventoryItem &item,
        const ItemTable &itemTable,
        const ReadableScrollTable *pReadableScrollTable);
};
}
