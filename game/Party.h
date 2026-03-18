#pragma once

#include "game/ClassSkillTable.h"
#include "game/OutdoorMovementDriver.h"
#include "game/RosterTable.h"

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;
struct EventRuntimeState;

struct InventoryItem
{
    uint32_t objectDescriptionId = 0;
    uint32_t quantity = 1;
    uint8_t width = 1;
    uint8_t height = 1;
    uint8_t gridX = 0;
    uint8_t gridY = 0;
};

struct Character
{
    static constexpr int InventoryWidth = 14;
    static constexpr int InventoryHeight = 9;

    std::string name;
    std::string role;
    std::string className;
    std::string portraitTextureName;
    uint32_t rosterId = 0;
    uint32_t level = 1;
    uint32_t skillPoints = 0;
    uint32_t might = 0;
    uint32_t intellect = 0;
    uint32_t personality = 0;
    uint32_t endurance = 0;
    uint32_t speed = 0;
    uint32_t accuracy = 0;
    uint32_t luck = 0;
    int maxHealth = 100;
    int health = 100;
    int maxSpellPoints = 0;
    int spellPoints = 0;
    std::unordered_map<std::string, CharacterSkill> skills;
    std::unordered_set<uint32_t> awards;

    bool addInventoryItem(const InventoryItem &item);
    bool removeInventoryItem(uint32_t objectDescriptionId, uint32_t quantity = 1);
    size_t inventoryItemCount() const;
    size_t usedInventoryCells() const;
    size_t inventoryCapacity() const;
    bool hasSkill(const std::string &skillName) const;
    const CharacterSkill *findSkill(const std::string &skillName) const;
    CharacterSkill *findSkill(const std::string &skillName);
    bool setSkillMastery(const std::string &skillName, SkillMastery mastery);

    std::vector<InventoryItem> inventory;
};

struct PartySeed
{
    std::vector<Character> members;
    std::vector<InventoryItem> inventory;
    int gold = 0;
    int food = 0;
};

class Party
{
public:
    static PartySeed createDefaultSeed();

    void setItemTable(const ItemTable *pItemTable);
    void setClassSkillTable(const ClassSkillTable *pClassSkillTable);
    void reset();
    void seed(const PartySeed &seed);
    void applyMovementEffects(const OutdoorMovementEffects &effects);
    void applyEventRuntimeState(const EventRuntimeState &runtimeState);
    bool applyDamageToActiveMember(int damage, const std::string &status);
    void addGold(int amount);
    void addFood(int amount);
    bool tryGrantItem(uint32_t objectDescriptionId, uint32_t quantity = 1);
    void grantItem(uint32_t objectDescriptionId, uint32_t quantity = 1);
    bool removeItem(uint32_t objectDescriptionId, uint32_t quantity = 1);
    bool needsHealing() const;
    bool activeMemberNeedsHealing() const;
    void restoreAll();
    void restoreActiveMember();
    bool trainLeader(uint32_t maxLevel, uint32_t &newLevel, uint32_t &skillPointsEarned);
    bool trainActiveMember(uint32_t maxLevel, uint32_t &newLevel, uint32_t &skillPointsEarned);
    bool canActiveMemberLearnSkill(const std::string &skillName) const;
    bool learnActiveMemberSkill(const std::string &skillName);
    int depositAllGoldToBank();
    int withdrawAllBankGold();
    bool isFull() const;
    bool recruitRosterMember(const RosterEntry &rosterEntry);
    bool hasRosterMember(uint32_t rosterId) const;
    bool hasAward(uint32_t awardId) const;
    bool hasAward(size_t memberIndex, uint32_t awardId) const;
    void addAward(uint32_t awardId);
    void addAward(size_t memberIndex, uint32_t awardId);
    void removeAward(uint32_t awardId);
    void removeAward(size_t memberIndex, uint32_t awardId);
    int inventoryItemCount(uint32_t objectDescriptionId, std::optional<size_t> memberIndex = std::nullopt) const;
    bool grantItemToMember(size_t memberIndex, uint32_t objectDescriptionId, uint32_t quantity = 1);
    bool removeItemFromMember(size_t memberIndex, uint32_t objectDescriptionId, uint32_t quantity = 1);
    bool setMemberClassName(size_t memberIndex, const std::string &className);
    const Character *member(size_t memberIndex) const;
    Character *member(size_t memberIndex);
    bool setActiveMemberIndex(size_t memberIndex);

    const std::vector<Character> &members() const;
    const Character *activeMember() const;
    Character *activeMember();
    size_t activeMemberIndex() const;
    int totalHealth() const;
    int totalMaxHealth() const;
    int gold() const;
    int bankGold() const;
    int food() const;
    size_t inventoryItemCount() const;
    size_t usedInventoryCells() const;
    size_t inventoryCapacity() const;
    uint32_t waterDamageTicks() const;
    uint32_t burningDamageTicks() const;
    uint32_t splashCount() const;
    uint32_t landingSoundCount() const;
    uint32_t hardLandingSoundCount() const;
    float lastFallDamageDistance() const;
    const std::string &lastStatus() const;

private:
    static constexpr size_t MaxMembers = 5;

    uint8_t resolveInventoryWidth(uint32_t objectDescriptionId) const;
    uint8_t resolveInventoryHeight(uint32_t objectDescriptionId) const;
    void applyDefaultStartingSkills(Character &member) const;

    const ItemTable *m_pItemTable = nullptr;
    const ClassSkillTable *m_pClassSkillTable = nullptr;
    std::vector<Character> m_members;
    size_t m_activeMemberIndex = 0;
    int m_gold = 0;
    int m_bankGold = 0;
    int m_food = 0;
    uint32_t m_waterDamageTicks = 0;
    uint32_t m_burningDamageTicks = 0;
    uint32_t m_splashCount = 0;
    uint32_t m_landingSoundCount = 0;
    uint32_t m_hardLandingSoundCount = 0;
    float m_lastFallDamageDistance = 0.0f;
    std::string m_lastStatus;
};
}
