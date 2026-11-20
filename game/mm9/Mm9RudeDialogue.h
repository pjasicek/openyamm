#pragma once

#include "game/party/SkillData.h"

#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
class Party;
struct EventRuntimeState;

constexpr uint32_t Mm9QuestKeyQBitBegin = 90000;
constexpr uint32_t Mm9QuestKeyQBitEnd = 99999;
constexpr int32_t Mm9QuestKeyRawIdMaximum = 9999;
constexpr uint32_t Mm9RudeExitEventIdBegin = 50000;
constexpr uint32_t Mm9RudeExitEventIdEnd = 52999;
constexpr uint32_t Mm9RudeUseEventIdBegin = 53000;
constexpr uint32_t Mm9RudeUseEventIdEnd = 55999;
constexpr uint32_t Mm9RudeFoundPlayerEventIdBegin = 56000;
constexpr uint32_t Mm9RudeFoundPlayerEventIdEnd = 58999;
// The promoters' standing topic (dialogue/promotions.yml): the shared MM9 Lua event (mm9_common.lua) that promotes the
// eligible members, with the promotion's name in the hook context.
constexpr uint16_t Mm9PromotionServiceEventId = 49990;

std::optional<uint32_t> mm9QBitForRawQuestKey(int32_t rawKeyId);
std::optional<int32_t> mm9RawQuestKeyForQBit(uint32_t qbitId);
std::optional<uint16_t> mm9RudeExitEventIdForSourceObject(uint32_t sourceObjectIndex);
std::optional<uint16_t> mm9RudeUseEventIdForSourceObject(uint32_t sourceObjectIndex);
std::optional<uint16_t> mm9RudeFoundPlayerEventIdForSourceObject(uint32_t sourceObjectIndex);

enum class Mm9RudeSelectionKind
{
    GotoNode,
    Close,
    Service,
    Unresolved,
};

struct Mm9RudeRow
{
    size_t rowIndex = 0;
    size_t sourceLine = 0;
    int32_t rudeId = 0;
    int32_t nodeId = 0;
    int32_t choiceSlot = 0;
    std::string prompt;
    std::string response;
    int32_t next = 0;
    std::vector<int32_t> requiredRawKeys;
    std::vector<int32_t> grantedRawKeys;
    std::vector<int32_t> forbiddenRawKeys;
    std::vector<int32_t> removedRawKeys;
    std::vector<std::string> rawColumns;
};

struct Mm9RudeSelection
{
    Mm9RudeSelectionKind kind = Mm9RudeSelectionKind::Unresolved;
    int32_t next = 0;
    int32_t serviceOpcode = 0;
    std::string response;
};

struct Mm9RudeSkillTrainerTopic
{
    int32_t rawTrainerId = 0;
    std::string displayName;
    SkillMastery targetMastery = SkillMastery::None;
    std::vector<std::string> skillNames;
    uint32_t requiredSkillRank = 0;
    uint32_t requiredGold = 0;
};

// An MM9 promotion quest's standing topic (devdocs/mm9/MM9_RUDE_SCR_INTEGRATION.md "Promotions And Classes"): once the
// party holds the quest's done key, the promoter's first page offers to promote the members eligible now, without the
// quest's experience or gold.
struct Mm9PromotionService
{
    std::string promotion;
    uint32_t rudeId = 0;
    int32_t doneRawKey = 0;
};

// An item a lost-item keeper gives back (dialogue/lost_items.yml): its raw MM9 id (the hand-in's named global
// MM9.HandedIn.<raw>) and its engine item.
struct Mm9LostItem
{
    int32_t rawItemId = 0;
    uint32_t itemId = 0;
};

// A row a ruleset adds to an MM9 person's first page (rulesets/<id>/worlds/mm9/dialogue.yml): a global event (MAW's
// skill reset and Dimensional Maps on Hjordisa the Hag), or the bounty office of a map (MAW's Jarls, each for his
// region: the hunt is posted in the city and its target placed when the party next enters the region).
struct Mm9RulesetRow
{
    uint32_t rudeId = 0;
    uint16_t eventId = 0;
    std::string bountyMapFileName;
    std::string label;
};

// A racial trainer (dialogue/racial_trainers.yml): an NPC whose first page offers each member the racial ability they
// know at the next mastery, up to this one.
struct Mm9RacialTrainer
{
    uint32_t rudeId = 0;
    SkillMastery maxMastery = SkillMastery::None;
};

class Mm9RudeDialogueTable
{
public:
    // packageRoot is empty for the active world's own files, or "worlds/mm9/" to read MM9's package while another
    // world is active.
    bool load(const Engine::AssetFileSystem &assetFileSystem, const std::string &packageRoot = {});
    bool loadDialogueText(const std::string &sourceName, const std::string &text);
    bool loadNpcNamesText(const std::string &sourceName, const std::string &text);
    bool loadTopBlurbsText(const std::string &sourceName, const std::string &text);
    // dialogue/promotions.yml, after the dialogue rows: the promoters' standing topics, rows MM9's dialogue lacks
    // (added_rows) and the required keys waived so that every promotion quest is offered without the one before it.
    bool loadPromotionsText(const std::string &sourceName, const std::string &text);
    // dialogue/lost_items.yml (devdocs/mm9_rework/PLACED_ITEMS_PLAN.md section 4): the keepers whose first page offers
    // to give back a lost item (Hjordisa the Hag) and the items they give back.
    bool loadLostItemsText(const std::string &sourceName, const std::string &text);
    // dialogue/racial_trainers.yml: the racial abilities and the NPCs that teach them (MM9 has no such trainers).
    bool loadRacialTrainersText(const std::string &sourceName, const std::string &text);
    // The active ruleset's rows (Mm9RulesetRow); empty text, or none for a ruleset without the file, clears them.
    bool loadRulesetRowsText(const std::string &sourceName, const std::string &text);
    void clearRulesetRows();
    void clear();

    bool empty() const;
    bool hasDialogue(uint32_t rudeId) const;
    std::string npcName(uint32_t rudeId) const;
    std::string topBlurb(uint32_t rudeId) const;
    std::vector<const Mm9RudeRow *> visibleRows(uint32_t rudeId, int32_t nodeId, const Party &party) const;
    const std::vector<Mm9RudeRow> &rows(uint32_t rudeId) const;
    const Mm9RudeRow *rowByIndex(uint32_t rudeId, size_t rowIndex) const;
    const Mm9PromotionService *promotionService(uint32_t rudeId) const;
    bool isLostItemKeeper(uint32_t rudeId) const;
    const std::vector<Mm9LostItem> &lostItems() const;
    std::vector<const Mm9RulesetRow *> rulesetRows(uint32_t rudeId) const;
    const Mm9RacialTrainer *racialTrainer(uint32_t rudeId) const;
    const std::vector<std::string> &racialAbilitySkills() const;
    const std::vector<std::string> &errors() const;

private:
    void addError(const std::string &sourceName, size_t sourceLine, const std::string &message);

    std::unordered_map<uint32_t, std::vector<Mm9RudeRow>> m_rowsByRudeId;
    std::unordered_map<uint32_t, Mm9PromotionService> m_promotionServices;
    std::vector<uint32_t> m_lostItemKeepers;
    std::vector<Mm9LostItem> m_lostItems;
    std::vector<Mm9RulesetRow> m_rulesetRows;
    std::unordered_map<uint32_t, Mm9RacialTrainer> m_racialTrainers;
    std::vector<std::string> m_racialAbilitySkills;
    std::unordered_map<uint32_t, std::string> m_npcNames;
    std::unordered_map<uint32_t, std::string> m_topBlurbs;
    std::vector<std::string> m_errors;
};

Mm9RudeSelection selectMm9RudeRow(const Mm9RudeRow &row);
bool mm9RudeRowPassesQuestKeys(
    const Mm9RudeRow &row,
    const std::function<bool(uint32_t)> &hasQBit);
// Whether the row's c16-c20 and c26-c30 are quest keys it grants and removes: ordinary rows, and the hire and dismiss
// services, whose tails keep the key meaning (Forad's hire grants 29 and 371, a dismissal removes its hire key); the
// other services reuse those columns as parameters.
bool mm9RudeRowAppliesQuestKeys(const Mm9RudeRow &row);
void applyMm9RudeRowActions(
    const Mm9RudeRow &row,
    Party &party,
    EventRuntimeState *pEventRuntimeState = nullptr);
std::string mm9RudeServiceName(int32_t opcode);
}
