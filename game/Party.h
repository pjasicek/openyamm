#pragma once

#include "game/OutdoorMovementDriver.h"

#include <cstdint>
#include <string>
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
    std::string portraitTextureName;
    uint32_t level = 1;
    int maxHealth = 100;
    int health = 100;
    int maxSpellPoints = 0;
    int spellPoints = 0;

    bool addInventoryItem(const InventoryItem &item);
    bool removeInventoryItem(uint32_t objectDescriptionId, uint32_t quantity = 1);
    size_t inventoryItemCount() const;
    size_t usedInventoryCells() const;
    size_t inventoryCapacity() const;

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
    void reset();
    void seed(const PartySeed &seed);
    void applyMovementEffects(const OutdoorMovementEffects &effects);
    void applyEventRuntimeState(const EventRuntimeState &runtimeState);
    void addGold(int amount);
    void addFood(int amount);
    void grantItem(uint32_t objectDescriptionId, uint32_t quantity = 1);
    bool removeItem(uint32_t objectDescriptionId, uint32_t quantity = 1);

    const std::vector<Character> &members() const;
    int totalHealth() const;
    int totalMaxHealth() const;
    int gold() const;
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
    uint8_t resolveInventoryWidth(uint32_t objectDescriptionId) const;
    uint8_t resolveInventoryHeight(uint32_t objectDescriptionId) const;

    const ItemTable *m_pItemTable = nullptr;
    std::vector<Character> m_members;
    int m_gold = 0;
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
