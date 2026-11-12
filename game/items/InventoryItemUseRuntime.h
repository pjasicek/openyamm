#pragma once

#include "game/party/Party.h"
#include "game/tables/ReadableScrollTable.h"
#include "game/party/SkillData.h"
#include "game/party/SpeechIds.h"
#include "game/audio/SoundIds.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;
struct ItemDefinition;
class MergedPotionSettingTable;
class MergedReagentSettingTable;

enum class InventoryItemUseAction : uint8_t
{
    None = 0,
    Equip,
    CastScroll,
    LearnSpell,
    LearnSkill,
    ConsumePotion,
    ReadMessageScroll,
    UseHorseshoe,
    UseGenieLamp,
    UseDeckOfFate,
    EatFoodItem,
    PlayInstrument,
    UseTempleInABottle,
    UseReagent,
    // An item whose use action is grantTechPoints (Hesper's Engrams): its VarA in tech points to the target.
    GrantTechPoints,
    // An item whose use action is grantSkillPoints (MM9's Clover, one point as in MM9): its VarA in skill points.
    GrantSkillPoints,
    // Personal energy shields (use actions useShieldCell, useShieldBurst; Party::chargePersonalShield and
    // burstPersonalShields).
    UseShieldCell,
    UseShieldBurst,
    // throwEmpGrenade: consumed here; the caller applies it to the world (GameplayItemService).
    ThrowEmpGrenade,
    // useStim: heals VarA % of the target's maximum health (30 without) and cures Weakness.
    UseStim,
    // placeBreachCharge: consumed here; the caller blasts the hostile actors around the party (GameplayItemService),
    // VarA damage (300 without).
    PlaceBreachCharge,
};

struct InventoryItemUseContext
{
    bool underwater = false;
    float gameMinutes = 0.0f;
    // Hostile monsters near the party (the yellow alert): drinking may then cost recovery.
    bool enemiesNear = false;
    // Turn-based combat: only the member whose turn it is (none while monsters act) pays a drink, with its turn.
    bool turnBased = false;
    std::optional<size_t> turnBasedReadyMember;
};

struct InventoryItemUseResult
{
    bool handled = false;
    bool consumed = false;
    InventoryItemUseAction action = InventoryItemUseAction::None;
    bool alreadyKnown = false;
    std::vector<std::string> learnedSkills;
    uint32_t spellId = 0;
    uint32_t spellSkillLevelOverride = 0;
    SkillMastery spellSkillMasteryOverride = SkillMastery::None;
    bool spellBypassRequiredMastery = false;
    std::string statusText;
    std::optional<SpeechId> speechId;
    std::optional<SoundId> soundId;
    std::string readableTitle;
    std::string readableBody;
    // A potion of several drinks that is not used up: the uses its bottle has left (its new charges).
    std::optional<uint32_t> potionUsesLeft;
    // The member who paid the drink's recovery, and how much; in turn-based combat the caller spends its turn.
    std::optional<size_t> recoveryPayer;
    float recoverySeconds = 0.0f;
};

// What drinking a potion would do for a member now, without drinking it (the basebar potion popup's preview).
struct PotionPreview
{
    // False when the item is no potion of potion_effects.yml.
    bool known = false;
    int healthGain = 0;
    int healthBefore = 0;
    int healthMaximum = 0;
    int spellPointGain = 0;
    int spellPointsBefore = 0;
    int spellPointsMaximum = 0;
    // The conditions the member has that it removes.
    std::vector<CharacterCondition> cures;
    // A buff, a permanent or timed effect: something beyond restoring and curing.
    bool otherEffects = false;

    // Restores nothing, cures nothing the member has, and does nothing else.
    bool noEffectNow() const
    {
        return known && healthGain == 0 && spellPointGain == 0 && cures.empty() && !otherEffects;
    }
};

class InventoryItemUseRuntime
{
public:
    static InventoryItemUseAction classifyItemUse(
        const InventoryItem &item,
        const ItemTable &itemTable,
        const MergedPotionSettingTable *pPotionSettingTable = nullptr,
        const MergedReagentSettingTable *pReagentSettingTable = nullptr);

    static InventoryItemUseResult useItemOnMember(
        Party &party,
        size_t targetMemberIndex,
        const InventoryItem &item,
        const ItemTable &itemTable,
        const ReadableScrollTable *pReadableScrollTable,
        const MergedPotionSettingTable *pPotionSettingTable = nullptr,
        const MergedReagentSettingTable *pReagentSettingTable = nullptr,
        const InventoryItemUseContext &context = {});
    // The spell a spell scroll casts (its Mod1 "S<id>"); none for other items.
    static std::optional<uint32_t> scrollSpellId(const ItemDefinition &itemDefinition);
    // The sound an instrument plays when used; none for other items.
    static std::optional<SoundId> instrumentSound(const ItemDefinition &itemDefinition);
    static PotionPreview previewPotion(
        const Party &party,
        size_t memberIndex,
        const InventoryItem &item,
        const MergedPotionSettingTable &potionSettingTable);
    // Whether a drink costs a ready member recovery under the rules' potion effects.
    static bool drinkRecoveryApplies(const MergedPotionSettingTable *pPotionSettingTable);
    // Who pays a drink's recovery: the drinker if ready (unless the active member pays), else the active member, else
    // the first ready one.
    static std::optional<size_t> drinkRecoveryPayer(
        const MergedPotionSettingTable &potionSettingTable,
        const Party &party,
        size_t drinkerIndex);
};
}
