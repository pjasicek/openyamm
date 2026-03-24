#pragma once

#include "game/Party.h"

#include <optional>
#include <string>

namespace OpenYAMM::Game
{
class ItemTable;
struct ItemDefinition;
struct CharacterDollTypeEntry;

struct CharacterSheetValue
{
    int base = 0;
    int actual = 0;
    bool infinite = false;
};

struct CharacterResourceSummary
{
    int current = 0;
    int maximum = 0;
    int baseMaximum = 0;
};

struct CharacterCombatSummary
{
    int attack = 0;
    std::optional<int> shoot;
    std::string meleeDamageText;
    std::string rangedDamageText;
};

struct CharacterSheetSummary
{
    CharacterSheetValue might = {};
    CharacterSheetValue intellect = {};
    CharacterSheetValue personality = {};
    CharacterSheetValue endurance = {};
    CharacterSheetValue accuracy = {};
    CharacterSheetValue speed = {};
    CharacterSheetValue luck = {};
    CharacterResourceSummary health = {};
    CharacterResourceSummary spellPoints = {};
    CharacterSheetValue armorClass = {};
    CharacterSheetValue level = {};
    CharacterSheetValue fireResistance = {};
    CharacterSheetValue airResistance = {};
    CharacterSheetValue waterResistance = {};
    CharacterSheetValue earthResistance = {};
    CharacterSheetValue mindResistance = {};
    CharacterSheetValue bodyResistance = {};
    std::string ageText;
    std::string experienceText;
    std::string conditionText;
    std::string quickSpellText;
    CharacterCombatSummary combat = {};
};

struct CharacterEquipPlan
{
    EquipmentSlot targetSlot = EquipmentSlot::MainHand;
    std::optional<EquipmentSlot> displacedSlot;
    bool autoStoreDisplacedItem = false;
};

class GameMechanics
{
public:
    static CharacterSheetSummary buildCharacterSheetSummary(const Character &character, const ItemTable *pItemTable);
    static bool canAct(const Character &character);
    static bool canSelectInGameplay(const Character &character);
    static bool canCharacterEquipItem(
        const Character &character,
        const ItemDefinition &itemDefinition,
        const CharacterDollTypeEntry *pCharacterDollType);
    static std::optional<CharacterEquipPlan> resolveCharacterEquipPlan(
        const Character &character,
        const ItemDefinition &itemDefinition,
        const ItemTable *pItemTable,
        const CharacterDollTypeEntry *pCharacterDollType,
        std::optional<EquipmentSlot> explicitSlot,
        bool preferOffHand);
};
}
