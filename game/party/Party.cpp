#include "game/party/Party.h"
#include "engine/Localization.h"

#include "game/events/EventRuntime.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/party/PlaythroughStatistics.h"
#include "game/gameplay/ReputationRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/InventoryBags.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/mm9/Mm9HirelingServices.h"
#include "game/mm9/Mm9HirelingTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/JournalQuestTable.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/RosterTable.h"
#include "game/tables/SpellTable.h"
#include "game/party/SpellSchool.h"
#include "game/rules/GameRules.h"
#include "game/party/SpellIds.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <optional>
#include <random>
#include <string_view>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
// An implant's family (no two of a family add up): its set id `family:<name>`, else its canonical id's name without the
// tier (dermal_2 -> dermal).
std::string implantFamily(const ItemDefinition &item)
{
    if (item.setId.rfind("family:", 0) == 0)
    {
        return item.setId.substr(7);
    }
    std::string name = item.canonicalId.substr(item.canonicalId.rfind('/') + 1);
    const size_t separator = name.rfind('_');
    if (separator != std::string::npos && separator + 1 < name.size()
        && std::all_of(name.begin() + separator + 1, name.end(), [](char c) { return c >= '0' && c <= '9'; }))
    {
        name.resize(separator);
    }
    return name;
}

// A numbered flag (Coupler30) with its number scaled; other flags unchanged.
std::string scaledImplantFlag(const std::string &flag, float scale)
{
    for (const char *pPrefix : {"Coupler", "Resonator"})
    {
        const std::string prefix = pPrefix;
        if (flag.size() > prefix.size() && flag.rfind(prefix, 0) == 0)
        {
            return prefix + std::to_string(int(std::lround(float(std::stoi(flag.substr(prefix.size()))) * scale)));
        }
    }
    return flag;
}

// The installed implants' effects, the better of each family only, each bonus +5 % per Cybernetics rank.
void applyImplants(Character &member, const ItemTable &itemTable)
{
    std::unordered_map<std::string, const ItemDefinition *> bestOfFamily;
    for (uint32_t itemId : member.implants)
    {
        const ItemDefinition *pItem = itemId != 0 ? itemTable.get(itemId) : nullptr;
        if (pItem == nullptr)
        {
            continue;
        }
        const ItemDefinition *&pBest = bestOfFamily[implantFamily(*pItem)];
        if (pBest == nullptr || pItem->itemId > pBest->itemId)
        {
            pBest = pItem;
        }
    }
    const CharacterSkill *pCybernetics = member.findSkill("Cybernetics");
    const float scale = 1.0f + 0.05f * float(pCybernetics != nullptr ? pCybernetics->level : 0);
    const auto scaled = [scale](int value)
    {
        return int(std::lround(float(value) * scale));
    };
    for (const auto &[family, pItem] : bestOfFamily)
    {
        ItemContentEffect effect = pItem->contentEffect;
        for (int *pValue : {&effect.might, &effect.intellect, &effect.personality, &effect.endurance, &effect.speed,
                 &effect.accuracy, &effect.luck, &effect.maxHealth, &effect.maxSpellPoints, &effect.armorClass,
                 &effect.meleeAttack, &effect.rangedAttack, &effect.meleeDamage, &effect.rangedDamage,
                 &effect.allResistances, &effect.fireResistance, &effect.airResistance, &effect.waterResistance,
                 &effect.earthResistance, &effect.mindResistance, &effect.bodyResistance, &effect.spiritResistance,
                 &effect.weaponDamage, &effect.recoveryReductionTicks, &effect.energyResistance,
                 &effect.personalShield, &effect.humPoints, &effect.rangedDamagePercent, &effect.meleeDamagePercent,
                 &effect.spellDamagePercent, &effect.energyDamageTakenPercent, &effect.gunRecoveryReductionTicks,
                 &effect.meleeRecoveryReductionTicks})
        {
            *pValue = scaled(*pValue);
        }
        effect.shieldRegenDelaySeconds *= scale;
        effect.healthRegenPerSecond *= scale;
        effect.spellRegenPerSecond *= scale;
        ItemEnchantRuntime::applyContentEffect(effect, member);
        member.armorShieldPoints += effect.personalShield;
        for (const std::string &flag : pItem->contentFlags)
        {
            member.equippedItemEffectFlags.insert(scaledImplantFlag(flag, scale));
        }
    }
}

constexpr std::array<CharacterBuffId, 24> DispellableCharacterBuffs = {
    CharacterBuffId::Bless,
    CharacterBuffId::Fate,
    CharacterBuffId::Preservation,
    CharacterBuffId::Regeneration,
    CharacterBuffId::Hammerhands,
    CharacterBuffId::PainReflection,
    CharacterBuffId::Haste,
    CharacterBuffId::Heroism,
    CharacterBuffId::Shield,
    CharacterBuffId::Stoneskin,
    CharacterBuffId::WaterBreathing,
    CharacterBuffId::TempMight,
    CharacterBuffId::TempIntellect,
    CharacterBuffId::TempPersonality,
    CharacterBuffId::TempEndurance,
    CharacterBuffId::TempSpeed,
    CharacterBuffId::TempAccuracy,
    CharacterBuffId::TempLuck,
    CharacterBuffId::FireResistance,
    CharacterBuffId::AirResistance,
    CharacterBuffId::WaterResistance,
    CharacterBuffId::EarthResistance,
    CharacterBuffId::MindResistance,
    CharacterBuffId::BodyResistance,
};

constexpr uint32_t ArcomageChampionAwardId = 41;
constexpr uint32_t Mm8ArcomageChampionQBit = 174;
constexpr uint32_t FirstMm8ArcomageHouseId = 228;
constexpr uint32_t LastMm8ArcomageHouseId = 238;
constexpr uint32_t Mm7ArcomageChampionQBit = 750;
constexpr uint32_t FirstMm7ArcomageHouseId = 240;
constexpr uint32_t LastMm7ArcomageHouseId = 252;
constexpr uint32_t RosterNpcPortraitBaseId = 2901;
constexpr float OeFiveGameMinuteTickGameSeconds = 5.0f * 60.0f;
constexpr uint32_t FirstRegularItemId = 1;
constexpr uint32_t LastRegularItemId = 134;
constexpr int GrandmasterUtilitySkillScore = std::numeric_limits<int>::max() / 4;

int utilitySkillMasteryMultiplier(SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Normal:
            return 1;
        case SkillMastery::Expert:
            return 2;
        case SkillMastery::Master:
            return 3;
        case SkillMastery::Grandmaster:
            return 5;
        case SkillMastery::None:
        default:
            return 0;
    }
}

std::string canonicalPartyWideUtilitySkillName(std::string_view skillName)
{
    const std::string canonical = canonicalSkillName(std::string(skillName));

    if (canonical == "Repair")
    {
        return "RepairItem";
    }

    if (canonical == "DisarmTrap")
    {
        return "DisarmTraps";
    }

    return canonical;
}

int genericUtilitySkillScore(const Character &member, const std::string &skillName)
{
    const CharacterSkill *pSkill = member.findSkill(skillName);
    const int itemBonus = member.skillBonus(skillName);

    if ((pSkill == nullptr || pSkill->level == 0 || pSkill->mastery == SkillMastery::None) && itemBonus == 0)
    {
        return 0;
    }

    if (pSkill != nullptr && pSkill->mastery == SkillMastery::Grandmaster)
    {
        return GrandmasterUtilitySkillScore + static_cast<int>(pSkill->level) + std::max(0, itemBonus);
    }

    const int level = (pSkill != nullptr ? static_cast<int>(pSkill->level) : 0) + itemBonus;
    const SkillMastery mastery = pSkill != nullptr ? pSkill->mastery : SkillMastery::Normal;
    return std::max(0, level) * utilitySkillMasteryMultiplier(mastery);
}

int partyWideUtilitySkillScore(const Character &member, const std::string &skillName)
{
    if (skillName == "Perception")
    {
        return GameMechanics::resolveCharacterPerceptionValue(member);
    }

    if (skillName == "DisarmTraps")
    {
        return GameMechanics::resolveCharacterDisarmTrapValue(member);
    }

    if (skillName == "Merchant")
    {
        const int merchantScore = genericUtilitySkillScore(member, skillName);
        return merchantScore > 0
            ? merchantScore + std::max(0, member.merchantBonus)
            : std::max(0, member.merchantBonus);
    }

    return genericUtilitySkillScore(member, skillName);
}

bool hasWonAllMm7ArcomageTaverns(const std::unordered_set<uint32_t> &wonHouseIds)
{
    for (uint32_t houseId = FirstMm7ArcomageHouseId; houseId <= LastMm7ArcomageHouseId; ++houseId)
    {
        if (!wonHouseIds.contains(houseId))
        {
            return false;
        }
    }

    return true;
}

bool hasWonAllMm8ArcomageTaverns(const std::unordered_set<uint32_t> &wonHouseIds)
{
    for (uint32_t houseId = FirstMm8ArcomageHouseId; houseId <= LastMm8ArcomageHouseId; ++houseId)
    {
        if (!wonHouseIds.contains(houseId))
        {
            return false;
        }
    }

    return true;
}

uint32_t resolveAdventurersInnPortraitPictureId(
    const Character &character,
    uint32_t portraitPictureId,
    const CharacterDollTable *pCharacterDollTable)
{
    if (pCharacterDollTable != nullptr && character.characterDataId != 0)
    {
        const CharacterDollEntry *pDollEntry = pCharacterDollTable->getCharacter(character.characterDataId);

        if (pDollEntry != nullptr && pDollEntry->npcPictureId != 0)
        {
            return pDollEntry->npcPictureId;
        }
    }

    if (character.rosterId != 0 && portraitPictureId < RosterNpcPortraitBaseId && character.portraitPictureId != 0)
    {
        return RosterNpcPortraitBaseId + character.portraitPictureId;
    }

    return portraitPictureId;
}

uint32_t remapCasterMemberIndexAfterDismiss(uint32_t casterMemberIndex, size_t dismissedMemberIndex)
{
    if (casterMemberIndex > dismissedMemberIndex)
    {
        return casterMemberIndex - 1;
    }

    return casterMemberIndex == dismissedMemberIndex ? 0 : casterMemberIndex;
}

bool characterNeedsTempleHealing(const Character &member)
{
    if (member.health < Party::effectiveMaximumHealth(member)
        || member.spellPoints < Party::effectiveMaximumSpellPoints(member))
    {
        return true;
    }

    for (size_t conditionIndex = 0; conditionIndex < CharacterConditionCount; ++conditionIndex)
    {
        if (member.conditions.test(conditionIndex))
        {
            return true;
        }
    }

    return false;
}

void clearTemporaryEventBonuses(Character &member)
{
    member.temporaryEventBonuses = {};
    member.armorClassModifier = 0;
    member.levelModifier = 0;
    member.ageModifier = 0;
}

uint32_t primaryStatWithMagicalBonus(uint32_t baseValue, int magicalBonus)
{
    const int64_t adjustedValue = static_cast<int64_t>(baseValue) + magicalBonus;
    return static_cast<uint32_t>(std::clamp<int64_t>(adjustedValue, 0, std::numeric_limits<int>::max()));
}

int currentMaximumHealth(const Character &member)
{
    return Party::effectiveMaximumHealth(member);
}

int currentMaximumSpellPoints(const Character &member)
{
    return Party::effectiveMaximumSpellPoints(member);
}

void applyMagicalPrimaryStatResourceBonuses(
    Character &member,
    const ClassMultiplierTable *pClassMultiplierTable)
{
    // The stats HP and SP grow with count permanent bonuses (black potions) as well as magical ones (SKL-2).
    Character adjustedMember = member;
    adjustedMember.intellect = primaryStatWithMagicalBonus(
        member.intellect, member.magicalBonuses.intellect + member.permanentBonuses.intellect);
    adjustedMember.personality = primaryStatWithMagicalBonus(
        member.personality, member.magicalBonuses.personality + member.permanentBonuses.personality);
    adjustedMember.endurance = primaryStatWithMagicalBonus(
        member.endurance, member.magicalBonuses.endurance + member.permanentBonuses.endurance);
    // Worn levels ("of Power") count as levels for HP and SP, as the original's level attribute does.
    adjustedMember.level = uint32_t(std::max<int64_t>(1, int64_t(member.level) + member.equippedLevelBonus));

    const int baseMaxHealth = GameMechanics::calculateBaseCharacterMaxHealth(member, pClassMultiplierTable);
    const int adjustedMaxHealth = GameMechanics::calculateBaseCharacterMaxHealth(adjustedMember, pClassMultiplierTable);
    member.magicalBonuses.maxHealth += adjustedMaxHealth - baseMaxHealth;

    const int baseMaxSpellPoints = GameMechanics::calculateBaseCharacterMaxSpellPoints(member, pClassMultiplierTable);
    const int adjustedMaxSpellPoints =
        GameMechanics::calculateBaseCharacterMaxSpellPoints(adjustedMember, pClassMultiplierTable);
    member.magicalBonuses.maxSpellPoints += adjustedMaxSpellPoints - baseMaxSpellPoints;
}

// Negative HP stays: an unconscious member wakes only when healed above 0 (SKL-1).
void clampCurrentResourcesToMaximum(Character &member)
{
    member.health = std::min(member.health, currentMaximumHealth(member));
    member.spellPoints = std::clamp(member.spellPoints, 0, currentMaximumSpellPoints(member));
}

void grantSeedSkill(Character &character, const std::string &skillName, uint32_t level = 1)
{
    CharacterSkill skill = {};
    skill.name = canonicalSkillName(skillName);
    skill.level = level;
    skill.mastery = SkillMastery::Normal;
    character.skills[skill.name] = skill;
}

void grantSeedSkill(Character &character, const std::string &skillName, uint32_t level, SkillMastery mastery)
{
    CharacterSkill skill = {};
    skill.name = canonicalSkillName(skillName);
    skill.level = level;
    skill.mastery = mastery;
    character.skills[skill.name] = skill;
}

const std::array<const char *, 12> &seedSpellSkillNames()
{
    static const std::array<const char *, 12> skillNames = {
        "FireMagic",
        "AirMagic",
        "WaterMagic",
        "EarthMagic",
        "SpiritMagic",
        "MindMagic",
        "BodyMagic",
        "LightMagic",
        "DarkMagic",
        "DarkElfAbility",
        "VampireAbility",
        "DragonAbility"
    };

    return skillNames;
}

void grantAllMagicSchools(Character &character, uint32_t level, SkillMastery mastery)
{
    for (const char *pSkillName : seedSpellSkillNames())
    {
        grantSeedSkill(character, pSkillName, level, mastery);
    }
}

void grantAllSkills(Character &character, uint32_t level, SkillMastery mastery)
{
    const std::vector<std::string> skillNames = allCanonicalSkillNames();

    for (const std::string &skillName : skillNames)
    {
        // The home-world test party keeps the classic skills; `skill set` grants technology and ruleset skills.
        if (!isTechnologySkill(skillName) && !isRulesetSkill(skillName))
        {
            grantSeedSkill(character, skillName, level, mastery);
        }
    }
}

void grantAllSpellsForMagicSkill(Character &character, const std::string &skillName)
{
    const std::optional<std::pair<uint32_t, uint32_t>> spellRange = spellIdRangeForMagicSkill(skillName);

    if (!spellRange)
    {
        return;
    }

    for (uint32_t spellId = spellRange->first; spellId <= spellRange->second; ++spellId)
    {
        character.learnSpell(spellId);
    }
}

void grantAllSpells(Character &character)
{
    for (const char *pSkillName : seedSpellSkillNames())
    {
        grantAllSpellsForMagicSkill(character, pSkillName);
    }
}

void forgetAllSpellsForMagicSkill(Character &character, const std::string &skillName)
{
    const std::optional<std::pair<uint32_t, uint32_t>> spellRange = spellIdRangeForMagicSkill(skillName);

    if (!spellRange)
    {
        return;
    }

    for (uint32_t spellId = spellRange->first; spellId <= spellRange->second; ++spellId)
    {
        character.forgetSpell(spellId);
    }
}

void applyRosterSpellKnowledge(Character &character, const RosterEntry &rosterEntry)
{
    for (const auto &[skillName, knownSpellCount] : rosterEntry.knownSpellCounts)
    {
        const std::optional<std::pair<uint32_t, uint32_t>> spellRange = spellIdRangeForMagicSkill(skillName);

        if (!spellRange || knownSpellCount == 0)
        {
            continue;
        }

        const uint32_t firstSpellId = spellRange->first;
        const uint32_t lastSpellId = spellRange->second;
        const uint32_t spellCountInSchool = lastSpellId - firstSpellId + 1;
        const uint32_t learnedSpellCount = std::min(knownSpellCount, spellCountInSchool);

        for (uint32_t spellOffset = 0; spellOffset < learnedSpellCount; ++spellOffset)
        {
            character.learnSpell(firstSpellId + spellOffset);
        }
    }
}

void grantDefaultEquipmentSkills(Character &character)
{
    static const std::array<const char *, 12> skillNames = {
        "LeatherArmor",
        "ChainArmor",
        "PlateArmor",
        "Spear",
        "Sword",
        "Bow",
        "Throwing",
        "Dagger",
        "Mace",
        "Axe",
        "Staff",
        "Shield"
    };

    for (const char *pSkillName : skillNames)
    {
        grantSeedSkill(character, pSkillName);
    }
}

void grantSeedInventoryItem(
    Character &character,
    uint32_t itemId,
    bool identified,
    bool broken)
{
    InventoryItem item = {};
    item.objectDescriptionId = itemId;
    item.quantity = 1;
    item.width = 0;
    item.height = 0;
    item.identified = identified;
    item.broken = broken;
    character.inventory.push_back(item);
}

std::string normalizeRoleName(const std::string &className)
{
    const std::string canonicalName = canonicalClassName(className);

    if (canonicalName.empty())
    {
        return "Adventurer";
    }

    return displayClassName(canonicalName);
}

std::string normalizePartyClassName(const std::string &className, const ClassSkillTable *pClassSkillTable)
{
    const std::string canonicalName = canonicalClassName(className);

    if (canonicalName.empty() || pClassSkillTable == nullptr)
    {
        return canonicalName;
    }

    for (char character : canonicalName)
    {
        if (std::isdigit(static_cast<unsigned char>(character)) == 0)
        {
            return canonicalName;
        }
    }

    char *pEnd = nullptr;
    const unsigned long classId = std::strtoul(canonicalName.c_str(), &pEnd, 10);

    if (pEnd == canonicalName.c_str() || *pEnd != '\0')
    {
        return canonicalName;
    }

    const std::optional<std::string> resolvedClassName =
        pClassSkillTable->classNameForId(static_cast<uint32_t>(classId));

    return resolvedClassName ? canonicalClassName(*resolvedClassName) : canonicalName;
}

uint32_t generateHouseStockSeed()
{
    std::random_device randomDevice;
    const uint32_t first = static_cast<uint32_t>(randomDevice());
    const uint32_t second = static_cast<uint32_t>(randomDevice());
    const uint32_t mixed = first ^ (second * 1664525u) ^ 0x9e3779b9u;
    return mixed != 0 ? mixed : 1u;
}

template <size_t N>
SoundId pickRandomSoundId(const std::array<SoundId, N> &soundIds)
{
    static thread_local std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<size_t> distribution(0, N - 1);
    return soundIds[distribution(rng)];
}

bool isPotionExplosionBreakCandidate(const InventoryItem &item)
{
    return item.objectDescriptionId >= FirstRegularItemId
        && item.objectDescriptionId <= LastRegularItemId;
}

void breakPotionExplosionItems(Character &member, uint8_t count)
{
    std::vector<InventoryItem *> candidates;

    for (InventoryItem &item : member.inventory)
    {
        if (isPotionExplosionBreakCandidate(item))
        {
            candidates.push_back(&item);
        }
    }

    if (candidates.empty())
    {
        return;
    }

    // Eradication breaks everything, hardened or not.
    if (count == 0)
    {
        for (InventoryItem *pItem : candidates)
        {
            pItem->broken = true;
        }

        return;
    }

    static thread_local std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<size_t> distribution(0, candidates.size() - 1);

    for (uint8_t index = 0; index < count; ++index)
    {
        InventoryItem *pItem = candidates[distribution(rng)];

        if (!pItem->hardened)
        {
            pItem->broken = true;
        }
    }
}

int potionExplosionDamage(uint8_t damageLevel)
{
    static thread_local std::mt19937 rng(std::random_device{}());

    switch (damageLevel)
    {
        case 1:
            return std::uniform_int_distribution<int>(10, 20)(rng);

        case 2:
            return std::uniform_int_distribution<int>(30, 100)(rng);

        case 3:
            return std::uniform_int_distribution<int>(50, 250)(rng);

        default:
            return 0;
    }
}

std::string portraitTextureNameFromPictureId(uint32_t pictureId)
{
    char buffer[16] = {};
    std::snprintf(buffer, sizeof(buffer), "PC%02u-01", pictureId + 1);
    return buffer;
}

std::string portraitTextureNameFromCharacterDollEntry(const CharacterDollEntry &entry)
{
    if (!entry.facePicturesPrefix.empty())
    {
        return entry.facePicturesPrefix + "01";
    }

    return entry.id > 0 ? portraitTextureNameFromPictureId(entry.id - 1) : std::string();
}

std::optional<uint32_t> tryParsePictureIdFromPortraitTextureName(const std::string &portraitTextureName)
{
    if (portraitTextureName.size() < 6)
    {
        return std::nullopt;
    }

    const std::string normalized = toLowerCopy(portraitTextureName);

    if (normalized[0] != 'p' || normalized[1] != 'c'
        || !std::isdigit(static_cast<unsigned char>(normalized[2]))
        || !std::isdigit(static_cast<unsigned char>(normalized[3])))
    {
        return std::nullopt;
    }

    const uint32_t faceNumber = static_cast<uint32_t>((normalized[2] - '0') * 10 + (normalized[3] - '0'));

    if (faceNumber == 0)
    {
        return std::nullopt;
    }

    return faceNumber - 1;
}

Character buildCharacterFromRosterEntry(
    const RosterEntry &rosterEntry,
    const ClassMultiplierTable *pClassMultiplierTable)
{
    Character member = {};
    member.name = rosterEntry.name;
    member.className = canonicalClassName(rosterEntry.className);
    member.role = normalizeRoleName(member.className);
    member.portraitTextureName = portraitTextureNameFromPictureId(rosterEntry.pictureId);
    member.portraitPictureId = rosterEntry.pictureId;
    member.characterDataId = rosterEntry.pictureId + 1;
    member.voiceId = rosterEntry.voiceId;
    member.rosterId = rosterEntry.id;
    member.birthYear = rosterEntry.birthYear;
    member.experience = rosterEntry.experience;
    member.level = std::max<uint32_t>(1, rosterEntry.level);
    member.skillPoints = rosterEntry.skillPoints;
    member.might = rosterEntry.might;
    member.intellect = rosterEntry.intellect;
    member.personality = rosterEntry.personality;
    member.endurance = rosterEntry.endurance;
    member.speed = rosterEntry.speed;
    member.accuracy = rosterEntry.accuracy;
    member.luck = rosterEntry.luck;
    member.baseResistances = rosterEntry.baseResistances;
    member.skills = rosterEntry.skills;
    applyRosterSpellKnowledge(member, rosterEntry);
    member.synchronizeInnateAbilitySpells();

    GameMechanics::refreshCharacterBaseResources(member, true, pClassMultiplierTable);
    return member;
}

void initializePortraitRuntimeState(Character &member)
{
    const std::optional<uint32_t> parsedPictureId = tryParsePictureIdFromPortraitTextureName(member.portraitTextureName);

    if (parsedPictureId)
    {
        member.portraitPictureId = *parsedPictureId;
    }
    else if (member.portraitTextureName.empty())
    {
        member.portraitTextureName = portraitTextureNameFromPictureId(member.portraitPictureId);
    }

    member.portraitState = PortraitId::Normal;
    member.portraitElapsedTicks = 0;
    member.portraitDurationTicks = 0;
    member.portraitSequenceCounter = 0;
    member.portraitImageIndex = 0;
}

std::optional<std::pair<uint8_t, uint8_t>> findFirstFreeInventorySlot(
    const std::vector<InventoryItem> &inventory,
    uint8_t width,
    uint8_t height)
{
    if (width == 0 || height == 0 || width > Character::InventoryWidth || height > Character::InventoryHeight)
    {
        return std::nullopt;
    }

    std::array<bool, Character::InventoryWidth * Character::InventoryHeight> occupied = {};

    for (const InventoryItem &item : inventory)
    {
        for (uint8_t y = 0; y < item.height; ++y)
        {
            for (uint8_t x = 0; x < item.width; ++x)
            {
                const uint8_t cellX = item.gridX + x;
                const uint8_t cellY = item.gridY + y;

                if (cellX >= Character::InventoryWidth || cellY >= Character::InventoryHeight)
                {
                    continue;
                }

                occupied[static_cast<size_t>(cellY) * Character::InventoryWidth + cellX] = true;
            }
        }
    }

    for (int x = 0; x <= Character::InventoryWidth - width; ++x)
    {
        for (int y = 0; y <= Character::InventoryHeight - height; ++y)
        {
            bool canPlace = true;

            for (uint8_t offsetY = 0; offsetY < height && canPlace; ++offsetY)
            {
                for (uint8_t offsetX = 0; offsetX < width; ++offsetX)
                {
                    const size_t index =
                        static_cast<size_t>(y + offsetY) * Character::InventoryWidth + static_cast<size_t>(x + offsetX);

                    if (occupied[index])
                    {
                        canPlace = false;
                        break;
                    }
                }
            }

            if (canPlace)
            {
                return std::pair<uint8_t, uint8_t>(static_cast<uint8_t>(x), static_cast<uint8_t>(y));
            }
        }
    }

    return std::nullopt;
}

// Sort group of an item: weapons, armour pieces, jewelry, then consumables and the rest.
int inventorySortGroup(const ItemDefinition *pItemDefinition)
{
    static const std::array<std::string_view, 21> EquipStatOrder = {
        "Weapon", "Weapon1or2", "Weapon2", "Bow", "Missile", "WeaponW",
        "Armor", "Shield", "Helm", "Cloak", "Belt", "Gauntlets", "Boots", "Amulet", "Ring",
        "Bottle", "Reagent", "Herb", "Gem", "Sscroll", "Mscroll"};

    if (pItemDefinition == nullptr)
    {
        return static_cast<int>(EquipStatOrder.size()) + 1;
    }

    for (size_t index = 0; index < EquipStatOrder.size(); ++index)
    {
        if (pItemDefinition->equipStat == EquipStatOrder[index])
        {
            return static_cast<int>(index);
        }
    }

    return static_cast<int>(EquipStatOrder.size());
}

// Repacks items column by column in the given order; fails when any item no longer fits.
std::optional<std::vector<InventoryItem>> packInventoryItems(const std::vector<InventoryItem> &orderedItems)
{
    std::vector<InventoryItem> packed;
    packed.reserve(orderedItems.size());

    for (const InventoryItem &item : orderedItems)
    {
        const std::optional<std::pair<uint8_t, uint8_t>> placement =
            findFirstFreeInventorySlot(packed, item.width, item.height);

        if (!placement)
        {
            return std::nullopt;
        }

        InventoryItem placedItem = item;
        placedItem.gridX = placement->first;
        placedItem.gridY = placement->second;
        packed.push_back(placedItem);
    }

    return packed;
}

bool inventoryItemContainsCell(const InventoryItem &item, uint8_t gridX, uint8_t gridY)
{
    return gridX >= item.gridX
        && gridX < item.gridX + item.width
        && gridY >= item.gridY
        && gridY < item.gridY + item.height;
}

const char *equipmentSlotName(EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::MainHand:
            return "MainHand";
        case EquipmentSlot::OffHand:
            return "OffHand";
        case EquipmentSlot::Bow:
            return "Bow";
        case EquipmentSlot::Armor:
            return "Armor";
        case EquipmentSlot::Helm:
            return "Helm";
        case EquipmentSlot::Belt:
            return "Belt";
        case EquipmentSlot::Cloak:
            return "Cloak";
        case EquipmentSlot::Gauntlets:
            return "Gauntlets";
        case EquipmentSlot::Boots:
            return "Boots";
        case EquipmentSlot::Amulet:
            return "Amulet";
        case EquipmentSlot::Ring1:
            return "Ring1";
        case EquipmentSlot::Ring2:
            return "Ring2";
        case EquipmentSlot::Ring3:
            return "Ring3";
        case EquipmentSlot::Ring4:
            return "Ring4";
        case EquipmentSlot::Ring5:
            return "Ring5";
        case EquipmentSlot::Ring6:
            return "Ring6";
    }

    return "Unknown";
}

void logItemInteractionResult(
    const char *pAction,
    const Character *pInspector,
    const Character *pOwner,
    const ItemDefinition *pItemDefinition,
    const std::string &location,
    bool success,
    const std::string &statusText)
{
    std::cout << "Item " << pAction
              << ": inspector=\"" << (pInspector != nullptr ? pInspector->name : "")
              << "\" owner=\"" << (pOwner != nullptr ? pOwner->name : "")
              << "\" item=\"" << (pItemDefinition != nullptr ? pItemDefinition->name : "")
              << "\" location=" << location
              << " result=" << (success ? "success" : "failed");

    if (!statusText.empty())
    {
        std::cout << " status=\"" << statusText << "\"";
    }

    std::cout << '\n';
}

constexpr uint32_t CharacterSexMale = 0;
constexpr uint32_t CharacterSexFemale = 1;
constexpr uint32_t CharacterRaceHuman = 0;
constexpr uint32_t CharacterRaceMinotaur = 3;
constexpr uint32_t CharacterRaceTroll = 4;
constexpr uint32_t CharacterRaceDragon = 5;
constexpr uint32_t CharacterRaceUndead = 6;
constexpr uint32_t CharacterRaceDarkElf = 2;
constexpr uint32_t CharacterRaceElf = 7;
constexpr uint32_t CharacterRaceGoblin = 8;
constexpr uint32_t CharacterRaceDwarf = 9;
constexpr uint32_t MaleLichCharacterDataId = 27;
constexpr uint32_t FemaleLichCharacterDataId = 28;
constexpr uint32_t MaleDwarfLichCharacterDataId = 66;
constexpr uint32_t FemaleDwarfLichCharacterDataId = 67;
constexpr uint32_t DragonLichCharacterDataId = 68;
constexpr uint32_t MinotaurLichCharacterDataId = 70;
constexpr uint32_t TrollLichCharacterDataId = 76;

void applyCharacterIdentityFromDollTable(Character &member, const CharacterDollTable *pCharacterDollTable)
{
    if (member.characterDataId == 0
        && (member.rosterId != 0 || !member.portraitTextureName.empty() || member.portraitPictureId != 0))
    {
        member.characterDataId = member.portraitPictureId + 1;
    }

    if (pCharacterDollTable == nullptr || member.characterDataId == 0)
    {
        return;
    }

    const CharacterDollEntry *pEntry = pCharacterDollTable->getCharacter(member.characterDataId);

    if (pEntry == nullptr)
    {
        return;
    }

    if (member.voiceId < 0)
    {
        member.voiceId = static_cast<int32_t>(pEntry->defaultVoiceId);
    }

    member.sexId = pEntry->defaultSex;

    if (pEntry->raceId >= 0)
    {
        member.raceId = static_cast<uint32_t>(pEntry->raceId);
    }
}

void applyCharacterDollIdentity(Character &member, const CharacterDollTable *pCharacterDollTable, bool forceVoice)
{
    if (pCharacterDollTable == nullptr || member.characterDataId == 0)
    {
        return;
    }

    const CharacterDollEntry *pEntry = pCharacterDollTable->getCharacter(member.characterDataId);

    if (pEntry == nullptr)
    {
        return;
    }

    if (forceVoice || member.voiceId < 0)
    {
        member.voiceId = static_cast<int32_t>(pEntry->defaultVoiceId);
    }

    member.sexId = pEntry->defaultSex;

    if (pEntry->raceId >= 0)
    {
        member.raceId = static_cast<uint32_t>(pEntry->raceId);
    }
}

void applyLichIdentity(Character &member, const CharacterDollTable *pCharacterDollTable)
{
    if (member.raceId == CharacterRaceUndead)
    {
        return;
    }

    const bool female = member.sexId == CharacterSexFemale;

    switch (member.raceId)
    {
        case CharacterRaceDragon:
            member.characterDataId = DragonLichCharacterDataId;
            break;
        case CharacterRaceMinotaur:
            member.characterDataId = MinotaurLichCharacterDataId;
            break;
        case CharacterRaceTroll:
            member.characterDataId = TrollLichCharacterDataId;
            break;
        case CharacterRaceDwarf:
            member.characterDataId = female ? FemaleDwarfLichCharacterDataId : MaleDwarfLichCharacterDataId;
            break;
        default:
            member.characterDataId = female ? FemaleLichCharacterDataId : MaleLichCharacterDataId;
            break;
    }

    const CharacterDollEntry *pLichEntry = pCharacterDollTable != nullptr
        ? pCharacterDollTable->getCharacter(member.characterDataId)
        : nullptr;
    member.portraitPictureId = member.characterDataId - 1;
    member.portraitTextureName = pLichEntry != nullptr
        ? portraitTextureNameFromCharacterDollEntry(*pLichEntry)
        : portraitTextureNameFromPictureId(member.portraitPictureId);
    member.portraitState = PortraitId::Normal;
    member.portraitElapsedTicks = 0;
    member.portraitDurationTicks = 0;
    member.portraitImageIndex = 0;
    applyCharacterDollIdentity(member, pCharacterDollTable, true);
}

void refundAndClearSkill(Character &member, const std::string &skillName)
{
    const std::unordered_map<std::string, CharacterSkill>::iterator skillIt = member.skills.find(skillName);

    if (skillIt == member.skills.end())
    {
        return;
    }

    const uint32_t level = skillIt->second.level;

    if (level > 0)
    {
        const uint32_t spentSkillPoints = level * (level + 1) / 2;
        member.skillPoints += spentSkillPoints > 0 ? spentSkillPoints - 1 : 0;
    }

    member.skills.erase(skillIt);
}

void applyLichState(Character &member)
{
    member.baseResistances.fire = std::max(member.baseResistances.fire, 20);
    member.baseResistances.air = std::max(member.baseResistances.air, 20);
    member.baseResistances.water = std::max(member.baseResistances.water, 20);
    member.baseResistances.earth = std::max(member.baseResistances.earth, 20);
    refundAndClearSkill(member, "ChainArmor");
    refundAndClearSkill(member, "RepairItem");
}

bool isValidMonsterAttackTarget(const Character &member)
{
    return member.health > 0
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Paralyzed))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Unconscious))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Dead))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Eradicated));
}

bool matchesMonsterAttackPreference(const Character &member, uint32_t preferenceFlag)
{
    const std::string className = canonicalClassName(member.className.empty() ? member.role : member.className);
    const bool hasCharacterIdentity = member.characterDataId != 0;
    const std::string normalizedRole = toLowerCopy(member.role);
    const std::string normalizedClassName = toLowerCopy(className);

    switch (preferenceFlag)
    {
        case MonsterAttackPreferenceKnight:
            return className == "Knight";

        case MonsterAttackPreferencePaladin:
            return className == "Paladin";

        case MonsterAttackPreferenceArcher:
            return className == "Archer";

        case MonsterAttackPreferenceDruid:
            return className == "Druid";

        case MonsterAttackPreferenceCleric:
            return className == "Cleric";

        case MonsterAttackPreferenceSorcerer:
            return className == "Sorcerer";

        case MonsterAttackPreferenceRanger:
            return className == "Ranger";

        case MonsterAttackPreferenceThief:
            return className == "Thief";

        case MonsterAttackPreferenceMonk:
            return className == "Monk";

        case MonsterAttackPreferenceMale:
            return hasCharacterIdentity ? member.sexId == CharacterSexMale : false;

        case MonsterAttackPreferenceFemale:
            return hasCharacterIdentity ? member.sexId == CharacterSexFemale : false;

        case MonsterAttackPreferenceHuman:
            return hasCharacterIdentity
                ? member.raceId == CharacterRaceHuman
                : className == "Knight"
                || className == "Paladin"
                || className == "Archer"
                || className == "Druid"
                || className == "Cleric"
                || className == "Sorcerer"
                || className == "Ranger"
                || className == "Thief"
                || className == "Monk";

        case MonsterAttackPreferenceElf:
            return hasCharacterIdentity
                ? member.raceId == CharacterRaceDarkElf || member.raceId == CharacterRaceElf
                : className == "DarkElf";

        case MonsterAttackPreferenceDwarf:
            return hasCharacterIdentity
                ? member.raceId == CharacterRaceDwarf
                : normalizedClassName.find("dwarf") != std::string::npos
                    || normalizedRole.find("dwarf") != std::string::npos;

        case MonsterAttackPreferenceGoblin:
            return hasCharacterIdentity
                ? member.raceId == CharacterRaceGoblin
                : className == "Goblin";

        default:
            return false;
    }
}

bool hasConditionImmunity(const Character &member, CharacterCondition condition)
{
    const size_t conditionIndex = static_cast<size_t>(condition);
    const bool ameliorationBlocksCondition =
        member.equippedItemEffectFlags.contains("Amelioration")
        && (condition == CharacterCondition::Weak
            || condition == CharacterCondition::Drunk
            || condition == CharacterCondition::PoisonWeak
            || condition == CharacterCondition::DiseaseWeak);

    return conditionIndex < CharacterConditionCount
        && (ameliorationBlocksCondition
            || member.permanentConditionImmunities.test(conditionIndex)
            || member.magicalConditionImmunities.test(conditionIndex)
            || member.rulesetState.potionEffect(TimedPotionEffect::Kind::Immunity, uint32_t(conditionIndex)) > 0);
}

bool conditionAffectedByProtectionFromMagic(CharacterCondition condition)
{
    switch (condition)
    {
        case CharacterCondition::Weak:
        case CharacterCondition::PoisonWeak:
        case CharacterCondition::DiseaseWeak:
        case CharacterCondition::PoisonMedium:
        case CharacterCondition::DiseaseMedium:
        case CharacterCondition::PoisonSevere:
        case CharacterCondition::DiseaseSevere:
        case CharacterCondition::Paralyzed:
        case CharacterCondition::Dead:
        case CharacterCondition::Petrified:
        case CharacterCondition::Eradicated:
            return true;

        default:
            return false;
    }
}

bool conditionRequiresGrandmasterProtectionFromMagic(CharacterCondition condition)
{
    return condition == CharacterCondition::Dead || condition == CharacterCondition::Eradicated;
}

// MM8 multiplies only the trained level by mastery; item and follower bonuses add once, and any nonzero total
// (even from bonuses alone) earns the flat 9 percent.
int learningPercentForExperienceGain(const Character &member)
{
    const CharacterSkill *pSkill = member.findSkill("Learning");
    const bool trained = pSkill != nullptr && pSkill->level > 0 && pSkill->mastery != SkillMastery::None;
    const int baseLevel = trained ? static_cast<int>(pSkill->level) : 0;
    const int bonusLevel = member.skillBonus("Learning");

    if (baseLevel + bonusLevel <= 0)
    {
        return 0;
    }

    const int multiplier = trained ? utilitySkillMasteryMultiplier(pSkill->mastery) : 1;
    return std::max(0, 9 + multiplier * baseLevel + bonusLevel);
}

bool canReceiveSharedExperience(const Character &member)
{
    return !member.conditions.test(static_cast<size_t>(CharacterCondition::Unconscious))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Dead))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Eradicated));
}

bool canReceiveUnconsciousAoeDamage(const Character &member)
{
    return member.conditions.test(static_cast<size_t>(CharacterCondition::Unconscious))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Dead))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Eradicated));
}

size_t countActingMembers(const std::vector<Character> &members)
{
    size_t count = 0;

    for (const Character &member : members)
    {
        if (GameMechanics::canAct(member))
        {
            ++count;
        }
    }

    return count;
}

std::optional<size_t> firstActingMemberIndex(const std::vector<Character> &members)
{
    for (size_t memberIndex = 0; memberIndex < members.size(); ++memberIndex)
    {
        if (GameMechanics::canAct(members[memberIndex]))
        {
            return memberIndex;
        }
    }

    return std::nullopt;
}

// Only a revival (Raise Dead, Resurrection) brings the dead back: a heal leaves them as they are (OE Character::Heal).
bool isDeadOrEradicated(const Character &member)
{
    return member.conditions.test(static_cast<size_t>(CharacterCondition::Dead))
        || member.conditions.test(static_cast<size_t>(CharacterCondition::Eradicated));
}

// Clears what the buffs, items and followers give, before rebuildMagicalBonusesFromBuffs applies them again.
void resetMagicalState(Character &member)
{
    member.magicalBonuses = member.temporaryEventBonuses;
    member.magicalImmunities = {};
    member.magicalConditionImmunities = {};
    member.merchantBonus = 0;
    member.glamourPower = 0;
    member.glamourMastery = SkillMastery::None;
    member.meleeWeaponDamageBonus = 0;
    member.rangedWeaponDamageBonus = 0;
    member.vampiricHealFraction = 0.0f;
    member.physicalAttackDisabled = false;
    member.physicalDamageImmune = false;
    member.halfMissileDamage = false;
    member.meleeArmorClassBonus = 0;
    member.missileArmorClassBonus = 0;
    member.magicArmorClassBonus = 0;
    member.physicalDamageTakenMultiplier = 1.0f;
    member.itemResistanceEnchants = {};
    member.mistFormPhysicalShare = 1.0f;
    member.manaDrainImmune = false;
    member.agingImmune = false;
    member.experienceGainMultiplier = 1.0f;
    member.randomEncounterChanceMultiplier = 1.0f;
    member.waterWalking = false;
    member.featherFalling = false;
    member.healthRegenPerSecond = 0.0f;
    member.spellRegenPerSecond = 0.0f;
    member.armorShieldPoints = 0;
    member.emitterShieldPoints = 0;
    member.energyResistance = 0;
    member.meleeWeaponEnchant = {};
    member.rangedWeaponEnchant = {};
    member.shieldRegenDelaySeconds = 0.0f;
    member.humPoints = 0;
    member.rangedDamagePercent = 0;
    member.meleeDamagePercent = 0;
    member.spellDamagePercent = 0;
    member.energyDamageTakenPercent = 0;
    member.gunRecoveryReductionTicks = 0;
    member.meleeRecoveryReductionTicks = 0;
    member.healthRegenAccumulator = 0.0f;
    member.spellRegenAccumulator = 0.0f;
    member.attackRecoveryReductionTicks = 0;
    member.recoveryProgressMultiplier = 1.0f;
    member.itemSkillBonuses.clear();
    member.equippedItemEffectFlags.clear();
    member.equippedLevelBonus = 0;
}

void updateMemberIncapacitatedCondition(Character &member, bool preservationActive, float gameMinutes)
{
    // HP never lifts Dead or Eradicated; only a revival or an explicit cure does.
    if (isDeadOrEradicated(member))
    {
        return;
    }

    if (member.health > 0)
    {
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Unconscious));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Unconscious)] = 0.0f;
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Dead));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Dead)] = 0.0f;
        return;
    }

    if (member.health + static_cast<int>(member.endurance) >= 1 || preservationActive)
    {
        const size_t unconsciousIndex = static_cast<size_t>(CharacterCondition::Unconscious);
        if (!member.conditions.test(unconsciousIndex))
        {
            member.conditionStartGameMinutes[unconsciousIndex] = std::max(0.0f, gameMinutes);
        }
        member.conditions.set(unconsciousIndex);
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Dead));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Dead)] = 0.0f;
    }
    else
    {
        const size_t deadIndex = static_cast<size_t>(CharacterCondition::Dead);
        if (!member.conditions.test(deadIndex))
        {
            member.conditionStartGameMinutes[deadIndex] = std::max(0.0f, gameMinutes);
        }
        member.conditions.set(deadIndex);
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Unconscious));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Unconscious)] = 0.0f;
    }
}

bool inventoryItemFitsAt(const InventoryItem &item, uint8_t gridX, uint8_t gridY)
{
    return item.width > 0
        && item.height > 0
        && gridX + item.width <= Character::InventoryWidth
        && gridY + item.height <= Character::InventoryHeight;
}

bool inventoryItemsOverlap(const InventoryItem &left, const InventoryItem &right)
{
    return left.gridX < right.gridX + right.width
        && left.gridX + left.width > right.gridX
        && left.gridY < right.gridY + right.height
        && left.gridY + left.height > right.gridY;
}

uint32_t &equippedItemId(CharacterEquipment &equipment, EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return equipment.offHand;

        case EquipmentSlot::MainHand:
            return equipment.mainHand;

        case EquipmentSlot::Bow:
            return equipment.bow;

        case EquipmentSlot::Armor:
            return equipment.armor;

        case EquipmentSlot::Helm:
            return equipment.helm;

        case EquipmentSlot::Belt:
            return equipment.belt;

        case EquipmentSlot::Cloak:
            return equipment.cloak;

        case EquipmentSlot::Gauntlets:
            return equipment.gauntlets;

        case EquipmentSlot::Boots:
            return equipment.boots;

        case EquipmentSlot::Amulet:
            return equipment.amulet;

        case EquipmentSlot::Ring1:
            return equipment.ring1;

        case EquipmentSlot::Ring2:
            return equipment.ring2;

        case EquipmentSlot::Ring3:
            return equipment.ring3;

        case EquipmentSlot::Ring4:
            return equipment.ring4;

        case EquipmentSlot::Ring5:
            return equipment.ring5;

        case EquipmentSlot::Ring6:
            return equipment.ring6;
    }

    return equipment.mainHand;
}

uint32_t equippedItemId(const CharacterEquipment &equipment, EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return equipment.offHand;

        case EquipmentSlot::MainHand:
            return equipment.mainHand;

        case EquipmentSlot::Bow:
            return equipment.bow;

        case EquipmentSlot::Armor:
            return equipment.armor;

        case EquipmentSlot::Helm:
            return equipment.helm;

        case EquipmentSlot::Belt:
            return equipment.belt;

        case EquipmentSlot::Cloak:
            return equipment.cloak;

        case EquipmentSlot::Gauntlets:
            return equipment.gauntlets;

        case EquipmentSlot::Boots:
            return equipment.boots;

        case EquipmentSlot::Amulet:
            return equipment.amulet;

        case EquipmentSlot::Ring1:
            return equipment.ring1;

        case EquipmentSlot::Ring2:
            return equipment.ring2;

        case EquipmentSlot::Ring3:
            return equipment.ring3;

        case EquipmentSlot::Ring4:
            return equipment.ring4;

        case EquipmentSlot::Ring5:
            return equipment.ring5;

        case EquipmentSlot::Ring6:
            return equipment.ring6;
    }

    return 0;
}

EquippedItemRuntimeState &equippedItemRuntimeState(CharacterEquipmentRuntimeState &equipmentRuntime, EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return equipmentRuntime.offHand;

        case EquipmentSlot::MainHand:
            return equipmentRuntime.mainHand;

        case EquipmentSlot::Bow:
            return equipmentRuntime.bow;

        case EquipmentSlot::Armor:
            return equipmentRuntime.armor;

        case EquipmentSlot::Helm:
            return equipmentRuntime.helm;

        case EquipmentSlot::Belt:
            return equipmentRuntime.belt;

        case EquipmentSlot::Cloak:
            return equipmentRuntime.cloak;

        case EquipmentSlot::Gauntlets:
            return equipmentRuntime.gauntlets;

        case EquipmentSlot::Boots:
            return equipmentRuntime.boots;

        case EquipmentSlot::Amulet:
            return equipmentRuntime.amulet;

        case EquipmentSlot::Ring1:
            return equipmentRuntime.ring1;

        case EquipmentSlot::Ring2:
            return equipmentRuntime.ring2;

        case EquipmentSlot::Ring3:
            return equipmentRuntime.ring3;

        case EquipmentSlot::Ring4:
            return equipmentRuntime.ring4;

        case EquipmentSlot::Ring5:
            return equipmentRuntime.ring5;

        case EquipmentSlot::Ring6:
            return equipmentRuntime.ring6;
    }

    return equipmentRuntime.mainHand;
}

const EquippedItemRuntimeState &equippedItemRuntimeState(
    const CharacterEquipmentRuntimeState &equipmentRuntime,
    EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return equipmentRuntime.offHand;

        case EquipmentSlot::MainHand:
            return equipmentRuntime.mainHand;

        case EquipmentSlot::Bow:
            return equipmentRuntime.bow;

        case EquipmentSlot::Armor:
            return equipmentRuntime.armor;

        case EquipmentSlot::Helm:
            return equipmentRuntime.helm;

        case EquipmentSlot::Belt:
            return equipmentRuntime.belt;

        case EquipmentSlot::Cloak:
            return equipmentRuntime.cloak;

        case EquipmentSlot::Gauntlets:
            return equipmentRuntime.gauntlets;

        case EquipmentSlot::Boots:
            return equipmentRuntime.boots;

        case EquipmentSlot::Amulet:
            return equipmentRuntime.amulet;

        case EquipmentSlot::Ring1:
            return equipmentRuntime.ring1;

        case EquipmentSlot::Ring2:
            return equipmentRuntime.ring2;

        case EquipmentSlot::Ring3:
            return equipmentRuntime.ring3;

        case EquipmentSlot::Ring4:
            return equipmentRuntime.ring4;

        case EquipmentSlot::Ring5:
            return equipmentRuntime.ring5;

        case EquipmentSlot::Ring6:
            return equipmentRuntime.ring6;
    }

    return equipmentRuntime.mainHand;
}

InventoryItem makeInventoryItem(
    const ItemTable *pItemTable,
    uint32_t objectDescriptionId,
    ItemGenerationMode mode = ItemGenerationMode::Generic)
{
    if (pItemTable == nullptr)
    {
        InventoryItem item = {};
        item.objectDescriptionId = objectDescriptionId;
        item.quantity = 1;
        return item;
    }

    return ItemGenerator::makeInventoryItem(objectDescriptionId, *pItemTable, mode);
}

InventoryItem makeInventoryItem(
    const ItemTable *pItemTable,
    uint32_t objectDescriptionId,
    const EquippedItemRuntimeState &runtimeState)
{
    InventoryItem item = makeInventoryItem(pItemTable, objectDescriptionId, ItemGenerationMode::Generic);
    item.identified = runtimeState.identified;
    item.broken = runtimeState.broken;
    item.stolen = runtimeState.stolen;
    item.hardened = runtimeState.hardened;
    item.standardEnchantId = runtimeState.standardEnchantId;
    item.standardEnchantPower = runtimeState.standardEnchantPower;
    item.specialEnchantId = runtimeState.specialEnchantId;
    item.artifactId = runtimeState.artifactId;
    item.rarity = runtimeState.rarity;
    item.currentCharges = runtimeState.currentCharges;
    item.maxCharges = runtimeState.maxCharges;
    item.temporaryBonusRemainingSeconds = runtimeState.temporaryBonusRemainingSeconds;
    item.rulesetFields = runtimeState.rulesetFields;
    item.workshopModId = runtimeState.workshopModId;

    if (pItemTable != nullptr)
    {
        const ItemDefinition *pItemDefinition = pItemTable->get(objectDescriptionId);

        if (pItemDefinition != nullptr)
        {
            if (item.rarity == ItemRarity::Common)
            {
                item.rarity = pItemDefinition->rarity;
            }

            if (item.artifactId == 0 && ItemRuntime::isRareItem(*pItemDefinition))
            {
                item.artifactId = static_cast<uint16_t>(std::min<uint32_t>(pItemDefinition->itemId, 0xFFFFu));
            }
        }
    }

    return item;
}

uint32_t rosterItemSeed(const RosterEntry &rosterEntry, const RosterEntry::StartingItem &rosterItem, size_t itemIndex)
{
    uint32_t seed = 0x9e3779b9u;
    seed ^= rosterEntry.id + 0x85ebca6bu + (seed << 6) + (seed >> 2);
    seed ^= rosterItem.rawValue + 0xc2b2ae35u + (seed << 6) + (seed >> 2);
    seed ^= static_cast<uint32_t>(itemIndex) + 0x27d4eb2fu + (seed << 6) + (seed >> 2);
    return seed;
}

InventoryItem makeRosterInventoryItem(
    const RosterEntry &rosterEntry,
    const RosterEntry::StartingItem &rosterItem,
    size_t itemIndex,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardEnchantTable,
    const SpecialItemEnchantTable *pSpecialEnchantTable)
{
    InventoryItem item = makeInventoryItem(pItemTable, rosterItem.itemId);
    item.identified = true;

    if (pItemTable == nullptr
        || pStandardEnchantTable == nullptr
        || pSpecialEnchantTable == nullptr
        || rosterItem.enchantmentLevel == 0)
    {
        return item;
    }

    const ItemDefinition *pItemDefinition = pItemTable->get(rosterItem.itemId);

    if (pItemDefinition == nullptr
        || ItemRuntime::isRareItem(*pItemDefinition)
        || !ItemEnchantRuntime::isEnchantable(*pItemDefinition))
    {
        return item;
    }

    const int treasureLevel = std::clamp(static_cast<int>(rosterItem.enchantmentLevel), 1, 6);
    const bool canHaveStandardEnchant = ItemEnchantRuntime::canHaveStandardEnchant(*pItemDefinition);
    const bool canHaveSpecialEnchant = ItemEnchantRuntime::canHaveSpecialEnchant(*pItemDefinition);
    const int standardChance =
        canHaveStandardEnchant ? ItemEnchantRuntime::standardEnchantChance(treasureLevel) : 0;
    const int specialChance =
        canHaveSpecialEnchant ? ItemEnchantRuntime::specialEnchantChance(*pItemDefinition, treasureLevel) : 0;

    if (standardChance <= 0 && specialChance <= 0)
    {
        return item;
    }

    std::mt19937 rng(rosterItemSeed(rosterEntry, rosterItem, itemIndex));
    const int roll = std::uniform_int_distribution<int>(0, 99)(rng);

    if (roll < standardChance)
    {
        const std::optional<uint16_t> standardEnchantId =
            ItemEnchantRuntime::chooseStandardEnchantId(*pItemDefinition, *pStandardEnchantTable, rng);

        if (standardEnchantId)
        {
            item.standardEnchantId = *standardEnchantId;

            const StandardItemEnchantEntry *pEntry = pStandardEnchantTable->get(*standardEnchantId);

            if (pEntry != nullptr)
            {
                item.standardEnchantPower =
                    static_cast<uint16_t>(ItemEnchantRuntime::generateStandardEnchantPower(
                        pEntry->kind,
                        treasureLevel,
                        rng));
            }
        }

        return item;
    }

    if (roll < standardChance + specialChance)
    {
        const std::optional<uint16_t> specialEnchantId =
            ItemEnchantRuntime::chooseSpecialEnchantId(*pItemDefinition, *pSpecialEnchantTable, treasureLevel, rng);

        if (specialEnchantId)
        {
            item.specialEnchantId = *specialEnchantId;
        }
    }

    return item;
}

void copyItemToEquippedRuntimeState(const InventoryItem &item, EquippedItemRuntimeState &runtimeState)
{
    runtimeState.identified = item.identified;
    runtimeState.broken = item.broken;
    runtimeState.stolen = item.stolen;
    runtimeState.hardened = item.hardened;
    runtimeState.standardEnchantId = item.standardEnchantId;
    runtimeState.standardEnchantPower = item.standardEnchantPower;
    runtimeState.specialEnchantId = item.specialEnchantId;
    runtimeState.artifactId = item.artifactId;
    runtimeState.rarity = item.rarity;
    runtimeState.currentCharges = item.currentCharges;
    runtimeState.maxCharges = item.maxCharges;
    runtimeState.temporaryBonusRemainingSeconds = item.temporaryBonusRemainingSeconds;
    runtimeState.rulesetFields = item.rulesetFields;
    runtimeState.workshopModId = item.workshopModId;
}

void grantRosterInventoryToCharacter(
    Character &character,
    const RosterEntry &rosterEntry,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardEnchantTable,
    const SpecialItemEnchantTable *pSpecialEnchantTable)
{
    const auto tryEquipRosterItem =
        [pItemTable](Character &targetCharacter, const InventoryItem &item) -> bool
        {
            if (pItemTable == nullptr)
            {
                return false;
            }

            const ItemDefinition *pItemDefinition = pItemTable->get(item.objectDescriptionId);

            if (pItemDefinition == nullptr || pItemDefinition->equipStat.empty() || pItemDefinition->equipStat == "0")
            {
                return false;
            }

            const std::optional<CharacterEquipPlan> equipPlan = GameMechanics::resolveCharacterEquipPlan(
                targetCharacter,
                *pItemDefinition,
                pItemTable,
                nullptr,
                std::nullopt,
                false);

            if (!equipPlan || equipPlan->displacedSlot.has_value())
            {
                return false;
            }

            equippedItemId(targetCharacter.equipment, equipPlan->targetSlot) = item.objectDescriptionId;
            EquippedItemRuntimeState &runtimeState =
                equippedItemRuntimeState(targetCharacter.equipmentRuntime, equipPlan->targetSlot);
            copyItemToEquippedRuntimeState(item, runtimeState);
            return true;
        };

    for (size_t itemIndex = 0; itemIndex < rosterEntry.startingItems.size(); ++itemIndex)
    {
        const InventoryItem item = makeRosterInventoryItem(
            rosterEntry,
            rosterEntry.startingItems[itemIndex],
            itemIndex,
            pItemTable,
            pStandardEnchantTable,
            pSpecialEnchantTable);

        if (tryEquipRosterItem(character, item))
        {
            continue;
        }

        character.addInventoryItem(item);
    }
}

InventoryItem *inventoryItemAtMutable(Character &character, uint8_t gridX, uint8_t gridY)
{
    for (InventoryItem &item : character.inventory)
    {
        if (inventoryItemContainsCell(item, gridX, gridY))
        {
            return &item;
        }
    }

    return nullptr;
}

bool identifyInventoryItemInstance(InventoryItem &item, const ItemDefinition &itemDefinition, std::string &statusText)
{
    if (item.identified || !ItemRuntime::requiresIdentification(itemDefinition))
    {
        statusText = Engine::tr("Already identified.");
        return false;
    }

    item.identified = true;
    statusText = Engine::tr("Identified {item}.", {{"item", ItemRuntime::displayName(item, itemDefinition)}});
    return true;
}

bool repairInventoryItemInstance(InventoryItem &item, const ItemDefinition &itemDefinition, std::string &statusText)
{
    if (!item.broken)
    {
        statusText = Engine::tr("Nothing to repair.");
        return false;
    }

    item.broken = false;
    item.identified = true;
    statusText = Engine::tr("Repaired {item}.", {{"item", ItemRuntime::displayName(item, itemDefinition)}});
    return true;
}

bool identifyEquippedItemInstance(EquippedItemRuntimeState &runtimeState, const ItemDefinition &itemDefinition, std::string &statusText)
{
    if (runtimeState.identified || !ItemRuntime::requiresIdentification(itemDefinition))
    {
        statusText = Engine::tr("Already identified.");
        return false;
    }

    runtimeState.identified = true;
    InventoryItem displayItem = {};
    displayItem.identified = runtimeState.identified;
    displayItem.broken = runtimeState.broken;
    displayItem.stolen = runtimeState.stolen;
    displayItem.standardEnchantId = runtimeState.standardEnchantId;
    displayItem.standardEnchantPower = runtimeState.standardEnchantPower;
    displayItem.specialEnchantId = runtimeState.specialEnchantId;
    displayItem.artifactId = runtimeState.artifactId;
    displayItem.rarity = runtimeState.rarity;
    statusText = Engine::tr("Identified {item}.", {{"item", ItemRuntime::displayName(displayItem, itemDefinition)}});
    return true;
}

bool repairEquippedItemInstance(EquippedItemRuntimeState &runtimeState, const ItemDefinition &itemDefinition, std::string &statusText)
{
    if (!runtimeState.broken)
    {
        statusText = Engine::tr("Nothing to repair.");
        return false;
    }

    runtimeState.broken = false;
    runtimeState.identified = true;
    InventoryItem displayItem = {};
    displayItem.identified = runtimeState.identified;
    displayItem.broken = runtimeState.broken;
    displayItem.stolen = runtimeState.stolen;
    displayItem.standardEnchantId = runtimeState.standardEnchantId;
    displayItem.standardEnchantPower = runtimeState.standardEnchantPower;
    displayItem.specialEnchantId = runtimeState.specialEnchantId;
    displayItem.artifactId = runtimeState.artifactId;
    displayItem.rarity = runtimeState.rarity;
    statusText = Engine::tr("Repaired {item}.", {{"item", ItemRuntime::displayName(displayItem, itemDefinition)}});
    return true;
}
}

bool Party::fitImplant(size_t memberIndex, size_t socket, const InventoryItem &item,
    std::optional<InventoryItem> &heldReplacement)
{
    Character *pMember = member(memberIndex);
    const ItemDefinition *pItem = m_pItemTable != nullptr ? m_pItemTable->get(item.objectDescriptionId) : nullptr;

    if (pMember == nullptr || pItem == nullptr || pItem->equipStat != "Implant"
        || socket >= pMember->implantSocketCount())
    {
        return false;
    }

    heldReplacement.reset();

    if (pMember->implants[socket] != 0)
    {
        heldReplacement =
            ItemGenerator::makeInventoryItem(pMember->implants[socket], *m_pItemTable, ItemGenerationMode::Generic);
    }

    pMember->implants[socket] = item.objectDescriptionId;
    rebuildMagicalBonusesFromBuffs();
    return true;
}

bool Party::takeImplant(size_t memberIndex, size_t socket, InventoryItem &item)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || socket >= pMember->implants.size() || pMember->implants[socket] == 0)
    {
        return false;
    }

    if (m_pItemTable == nullptr)
    {
        return false;
    }

    item = ItemGenerator::makeInventoryItem(pMember->implants[socket], *m_pItemTable, ItemGenerationMode::Generic);
    pMember->implants[socket] = 0;
    rebuildMagicalBonusesFromBuffs();
    return true;
}

bool Character::showsImplantSockets() const
{
    return findSkill("Cybernetics") != nullptr
        || std::any_of(implants.begin(), implants.end(), [](uint32_t itemId) { return itemId != 0; });
}

size_t Character::implantSocketCount() const
{
    const CharacterSkill *pCybernetics = findSkill("Cybernetics");
    if (pCybernetics == nullptr || pCybernetics->level == 0)
    {
        return 0;
    }
    return std::min<size_t>(implants.size(), size_t(std::max<int>(1, int(pCybernetics->mastery))));
}

bool Character::addInventoryItem(const InventoryItem &item)
{
    InventoryItem placedItem = item;
    placedItem.width = std::max<uint8_t>(1, item.width);
    placedItem.height = std::max<uint8_t>(1, item.height);

    const std::optional<std::pair<uint8_t, uint8_t>> placement =
        findFirstFreeInventorySlot(inventory, placedItem.width, placedItem.height);

    if (!placement)
    {
        return false;
    }

    return addInventoryItemAt(placedItem, placement->first, placement->second);
}

bool Character::addInventoryItemAt(const InventoryItem &item, uint8_t gridX, uint8_t gridY)
{
    InventoryItem placedItem = item;
    placedItem.width = std::max<uint8_t>(1, item.width);
    placedItem.height = std::max<uint8_t>(1, item.height);
    placedItem.gridX = gridX;
    placedItem.gridY = gridY;

    if (!inventoryItemFitsAt(placedItem, placedItem.gridX, placedItem.gridY))
    {
        return false;
    }

    for (const InventoryItem &existingItem : inventory)
    {
        if (inventoryItemsOverlap(existingItem, placedItem))
        {
            return false;
        }
    }

    inventory.push_back(placedItem);
    return true;
}

bool Character::removeInventoryItem(uint32_t objectDescriptionId, uint32_t quantity)
{
    if (objectDescriptionId == 0 || quantity == 0)
    {
        return false;
    }

    for (size_t itemIndex = 0; itemIndex < inventory.size(); ++itemIndex)
    {
        InventoryItem &item = inventory[itemIndex];

        if (item.objectDescriptionId != objectDescriptionId)
        {
            continue;
        }

        if (item.quantity < quantity)
        {
            return false;
        }

        item.quantity -= quantity;

        if (item.quantity == 0)
        {
            inventory.erase(inventory.begin() + itemIndex);
        }

        return true;
    }

    return false;
}

const InventoryItem *Character::inventoryItemAt(uint8_t gridX, uint8_t gridY) const
{
    for (const InventoryItem &item : inventory)
    {
        if (inventoryItemContainsCell(item, gridX, gridY))
        {
            return &item;
        }
    }

    return nullptr;
}

bool Character::takeInventoryItemAt(uint8_t gridX, uint8_t gridY, InventoryItem &item)
{
    for (size_t itemIndex = 0; itemIndex < inventory.size(); ++itemIndex)
    {
        if (!inventoryItemContainsCell(inventory[itemIndex], gridX, gridY))
        {
            continue;
        }

        item = inventory[itemIndex];
        inventory.erase(inventory.begin() + itemIndex);
        return true;
    }

    return false;
}

bool Character::tryPlaceInventoryItemAt(
    const InventoryItem &item,
    uint8_t gridX,
    uint8_t gridY,
    std::optional<InventoryItem> &replacedItem)
{
    replacedItem.reset();

    InventoryItem placedItem = item;
    placedItem.width = std::max<uint8_t>(1, item.width);
    placedItem.height = std::max<uint8_t>(1, item.height);
    placedItem.gridX = gridX;
    placedItem.gridY = gridY;

    if (!inventoryItemFitsAt(placedItem, gridX, gridY))
    {
        return false;
    }

    std::optional<size_t> targetItemIndex;

    for (size_t itemIndex = 0; itemIndex < inventory.size(); ++itemIndex)
    {
        if (inventoryItemContainsCell(inventory[itemIndex], gridX, gridY))
        {
            targetItemIndex = itemIndex;
            break;
        }
    }

    if (!targetItemIndex)
    {
        return addInventoryItemAt(placedItem, gridX, gridY);
    }

    replacedItem = inventory[*targetItemIndex];
    inventory.erase(inventory.begin() + *targetItemIndex);

    const bool placedAtReplacedItemOrigin =
        addInventoryItemAt(placedItem, replacedItem->gridX, replacedItem->gridY);
    const bool placedInFirstFreeSlot =
        !placedAtReplacedItemOrigin && addInventoryItem(placedItem);

    if (!placedAtReplacedItemOrigin && !placedInFirstFreeSlot)
    {
        inventory.push_back(*replacedItem);
        replacedItem.reset();
        return false;
    }

    return true;
}

bool Character::hasSkill(const std::string &skillName) const
{
    const std::string canonicalName = canonicalSkillName(skillName);
    return hasCanonicalSkill(canonicalName);
}

bool Character::hasCanonicalSkill(const std::string &canonicalSkillName) const
{
    return !canonicalSkillName.empty() && skills.contains(canonicalSkillName);
}

int Character::skillBonus(const std::string &skillName) const
{
    // Item bonuses are kept under canonical skill names.
    const std::string canonicalName = canonicalSkillName(skillName);
    const auto itemBonus = itemSkillBonuses.find(canonicalName);
    const auto followerBonus = hiredNpcSkillBonuses.find(canonicalName);
    return (itemBonus != itemSkillBonuses.end() ? itemBonus->second : 0)
        + (followerBonus != hiredNpcSkillBonuses.end() ? followerBonus->second : 0);
}

uint32_t Character::pointsForRaisingSkill(const std::string &skillName) const
{
    return isTechnologySkill(skillName) ? techPoints : skillPoints;
}

bool Character::hasTechnologySkill() const
{
    for (const std::string &skillName : skillSheetGroupSkillNames(SkillSheetGroup::Technology))
    {
        if (findSkillByCanonicalName(skillName) != nullptr)
        {
            return true;
        }
    }

    return false;
}

const CharacterSkill *Character::findSkill(const std::string &skillName) const
{
    const std::string canonicalName = canonicalSkillName(skillName);

    if (canonicalName.empty())
    {
        return nullptr;
    }

    return findSkillByCanonicalName(canonicalName);
}

const CharacterSkill *Character::findSkillByCanonicalName(const std::string &canonicalSkillName) const
{
    if (canonicalSkillName.empty())
    {
        return nullptr;
    }

    const std::unordered_map<std::string, CharacterSkill>::const_iterator it = skills.find(canonicalSkillName);
    return it != skills.end() ? &it->second : nullptr;
}

CharacterSkill *Character::findSkill(const std::string &skillName)
{
    const std::string canonicalName = canonicalSkillName(skillName);

    if (canonicalName.empty())
    {
        return nullptr;
    }

    return findSkillByCanonicalName(canonicalName);
}

CharacterSkill *Character::findSkillByCanonicalName(const std::string &canonicalSkillName)
{
    if (canonicalSkillName.empty())
    {
        return nullptr;
    }

    const std::unordered_map<std::string, CharacterSkill>::iterator it = skills.find(canonicalSkillName);
    return it != skills.end() ? &it->second : nullptr;
}

bool Character::setSkillMastery(const std::string &skillName, SkillMastery mastery)
{
    CharacterSkill *pSkill = findSkill(skillName);

    if (pSkill == nullptr)
    {
        return false;
    }

    pSkill->mastery = mastery;
    synchronizeInnateAbilitySpells();

    GameMechanics::refreshCharacterBaseResources(*this);
    return true;
}

void Character::synchronizeInnateAbilitySpells()
{
    static constexpr std::array<const char *, 3> InnateAbilitySkillNames = {
        "DarkElfAbility",
        "VampireAbility",
        "DragonAbility",
    };

    for (const char *pSkillName : InnateAbilitySkillNames)
    {
        const CharacterSkill *pSkill = findSkillByCanonicalName(pSkillName);

        if (pSkill == nullptr || pSkill->level == 0 || pSkill->mastery == SkillMastery::None)
        {
            continue;
        }

        const std::optional<std::pair<uint32_t, uint32_t>> spellRange = spellIdRangeForMagicSkill(pSkillName);

        if (!spellRange)
        {
            continue;
        }

        const uint32_t spellCount = spellRange->second - spellRange->first + 1;
        const uint32_t grantedSpellCount = std::min<uint32_t>(
            spellCount,
            static_cast<uint32_t>(pSkill->mastery));

        for (uint32_t spellOffset = 0; spellOffset < grantedSpellCount; ++spellOffset)
        {
            learnSpell(spellRange->first + spellOffset);
        }
    }
}

const std::string &Party::lastOutdoorMapFileName() const
{
    return m_lastOutdoorMapFileName;
}

void Party::setLastOutdoorMapFileName(const std::string &mapFileName)
{
    m_lastOutdoorMapFileName = mapFileName;
}

std::function<bool(const SpellEntry &)> spellKnownBy(const Character &character)
{
    return [&character](const SpellEntry &entry)
    {
        return character.knowsSpell(uint32_t(entry.id));
    };
}

bool Character::knowsSpell(uint32_t spellId) const
{
    return spellId != 0 && knownSpellIds.contains(spellId);
}

bool Character::learnSpell(uint32_t spellId)
{
    if (spellId == 0)
    {
        return false;
    }

    return knownSpellIds.insert(spellId).second;
}

bool Character::forgetSpell(uint32_t spellId)
{
    if (spellId == 0)
    {
        return false;
    }

    return knownSpellIds.erase(spellId) > 0;
}

size_t Character::inventoryItemCount() const
{
    return inventory.size();
}

size_t Character::usedInventoryCells() const
{
    size_t usedCells = 0;

    for (const InventoryItem &item : inventory)
    {
        usedCells += static_cast<size_t>(item.width) * item.height;
    }

    return usedCells;
}

size_t Character::inventoryCapacity() const
{
    return static_cast<size_t>(InventoryWidth) * InventoryHeight;
}

PartySeed Party::createDefaultSeed()
{
    PartySeed seed = {};
    seed.gold = 10000;
    seed.food = 7;

    auto grantSeedEquippedItem = [](
        Character &character,
        EquipmentSlot slot,
        uint32_t itemId,
        uint16_t standardEnchantId = 0,
        uint16_t standardEnchantPower = 0,
        uint16_t specialEnchantId = 0)
    {
        ::OpenYAMM::Game::equippedItemId(character.equipment, slot) = itemId;
        EquippedItemRuntimeState &runtimeState = equippedItemRuntimeState(character.equipmentRuntime, slot);
        runtimeState = {};
        runtimeState.identified = true;
        runtimeState.standardEnchantId = standardEnchantId;
        runtimeState.standardEnchantPower = standardEnchantPower;
        runtimeState.specialEnchantId = specialEnchantId;
    };

    auto grantSeedSpellAccess = [](Character &character)
    {
        grantAllMagicSchools(character, 10, SkillMastery::Grandmaster);
        grantAllSpells(character);
    };

    Character cleric = {};
    cleric.name = "Ariel";
    cleric.className = "Cleric";
    cleric.role = "Cleric";
    cleric.portraitTextureName = "PC03-01";
    cleric.portraitPictureId = 2;
    cleric.characterDataId = 3;
    cleric.birthYear = 1148;
    cleric.experience = 10000;
    cleric.level = 5;
    cleric.skillPoints = 30;
    cleric.might = 12;
    cleric.intellect = 20;
    cleric.personality = 20;
    cleric.endurance = 15;
    cleric.speed = 12;
    cleric.accuracy = 12;
    cleric.luck = 14;
    cleric.maxHealth = 100;
    cleric.health = 100;
    cleric.maxSpellPoints = 120;
    cleric.spellPoints = 120;
    grantDefaultEquipmentSkills(cleric);
    grantSeedSkill(cleric, "IdentifyItem", 10, SkillMastery::Grandmaster);
    grantSeedSkill(cleric, "RepairItem", 10, SkillMastery::Grandmaster);
    grantSeedEquippedItem(cleric, EquipmentSlot::MainHand, 79, 0, 0, 16);
    grantSeedEquippedItem(cleric, EquipmentSlot::Armor, 90, 0, 0, 1);
    grantSeedEquippedItem(cleric, EquipmentSlot::Helm, 111, 2, 8);
    grantSeedEquippedItem(cleric, EquipmentSlot::Boots, 135, 0, 0, 72);
    grantSeedEquippedItem(cleric, EquipmentSlot::Amulet, 151, 0, 0, 26);
    grantSeedEquippedItem(cleric, EquipmentSlot::Ring1, 145, 0, 0, 17);
    grantSeedEquippedItem(cleric, EquipmentSlot::Ring2, 146, 9, 12);
    grantSeedInventoryItem(cleric, 137, false, false);
    grantSeedInventoryItem(cleric, 137, true, true);
    grantSeedInventoryItem(cleric, 138, false, false);
    grantSeedInventoryItem(cleric, 138, true, true);
    grantSeedInventoryItem(cleric, 145, false, false);
    grantSeedInventoryItem(cleric, 145, true, true);
    grantSeedInventoryItem(cleric, 401, true, false);
    grantSeedInventoryItem(cleric, 410, true, false);
    grantSeedInventoryItem(cleric, 411, true, false);
    grantSeedInventoryItem(cleric, 400, true, false);
    grantSeedInventoryItem(cleric, 741, true, false);
    grantSeedInventoryItem(cleric, 222, true, false);
    grantSeedInventoryItem(cleric, 223, true, false);
    grantSeedInventoryItem(cleric, 266, true, false);
    grantSeedInventoryItem(cleric, 253, true, false);
    grantSeedInventoryItem(cleric, 656, true, false);
    grantSeedInventoryItem(cleric, 2106, true, false);
    grantSeedInventoryItem(cleric, 2125, true, false);
    grantSeedSpellAccess(cleric);
    grantAllSkills(cleric, 200, SkillMastery::Grandmaster);
    seed.members.push_back(cleric);

    return seed;
}

void Party::reset()
{
    seed(createDefaultSeed());
}

void Party::setItemTable(const ItemTable *pItemTable)
{
    m_pItemTable = pItemTable;
}

void Party::setJournalQuestTable(const JournalQuestTable *pJournalQuestTable)
{
    m_pJournalQuestTable = pJournalQuestTable;
}

void Party::setCharacterDollTable(const CharacterDollTable *pCharacterDollTable)
{
    m_pCharacterDollTable = pCharacterDollTable;

    for (Character &member : m_members)
    {
        applyCharacterIdentityFromDollTable(member, m_pCharacterDollTable);
    }

    for (AdventurersInnMember &member : m_adventurersInnMembers)
    {
        applyCharacterIdentityFromDollTable(member.character, m_pCharacterDollTable);
        member.portraitPictureId = resolveAdventurersInnPortraitPictureId(
            member.character,
            member.portraitPictureId,
            m_pCharacterDollTable);
    }
}

void Party::setItemEnchantTables(
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable)
{
    m_pStandardItemEnchantTable = pStandardItemEnchantTable;
    m_pSpecialItemEnchantTable = pSpecialItemEnchantTable;
}

const ItemTable *Party::itemTable() const
{
    return m_pItemTable;
}

const JournalQuestTable *Party::journalQuestTable() const
{
    return m_pJournalQuestTable;
}

const StandardItemEnchantTable *Party::standardItemEnchantTable() const
{
    return m_pStandardItemEnchantTable;
}

const SpecialItemEnchantTable *Party::specialItemEnchantTable() const
{
    return m_pSpecialItemEnchantTable;
}

size_t Party::equippedItemSetPieceCount(size_t memberIndex, const std::string &setId) const
{
    const Character *pMember = member(memberIndex);

    if (pMember == nullptr || m_pItemTable == nullptr || setId.empty())
    {
        return 0;
    }

    const std::array<std::pair<uint32_t, bool>, 16> equippedItems = {{
        {pMember->equipment.offHand, pMember->equipmentRuntime.offHand.broken},
        {pMember->equipment.mainHand, pMember->equipmentRuntime.mainHand.broken},
        {pMember->equipment.bow, pMember->equipmentRuntime.bow.broken},
        {pMember->equipment.armor, pMember->equipmentRuntime.armor.broken},
        {pMember->equipment.helm, pMember->equipmentRuntime.helm.broken},
        {pMember->equipment.belt, pMember->equipmentRuntime.belt.broken},
        {pMember->equipment.cloak, pMember->equipmentRuntime.cloak.broken},
        {pMember->equipment.gauntlets, pMember->equipmentRuntime.gauntlets.broken},
        {pMember->equipment.boots, pMember->equipmentRuntime.boots.broken},
        {pMember->equipment.amulet, pMember->equipmentRuntime.amulet.broken},
        {pMember->equipment.ring1, pMember->equipmentRuntime.ring1.broken},
        {pMember->equipment.ring2, pMember->equipmentRuntime.ring2.broken},
        {pMember->equipment.ring3, pMember->equipmentRuntime.ring3.broken},
        {pMember->equipment.ring4, pMember->equipmentRuntime.ring4.broken},
        {pMember->equipment.ring5, pMember->equipmentRuntime.ring5.broken},
        {pMember->equipment.ring6, pMember->equipmentRuntime.ring6.broken},
    }};
    return static_cast<size_t>(std::count_if(
        equippedItems.begin(),
        equippedItems.end(),
        [this, &setId](const std::pair<uint32_t, bool> &equippedItem)
        {
            const ItemDefinition *pItem = equippedItem.first != 0 && !equippedItem.second
                ? m_pItemTable->get(equippedItem.first)
                : nullptr;
            return pItem != nullptr && pItem->setId == setId;
        }));
}

int32_t Party::eventVariableValue(uint16_t variableId) const
{
    const auto iterator = m_eventVariables.find(variableId);
    return iterator != m_eventVariables.end() ? iterator->second : 0;
}

void Party::setEventVariableValue(uint16_t variableId, int32_t value)
{
    if (value == 0)
    {
        m_eventVariables.erase(variableId);
        return;
    }

    m_eventVariables[variableId] = value;
}

void Party::addEventVariableValue(uint16_t variableId, int32_t value)
{
    if (value == 0)
    {
        return;
    }

    setEventVariableValue(variableId, eventVariableValue(variableId) + value);
}

void Party::subtractEventVariableValue(uint16_t variableId, int32_t value)
{
    if (value == 0)
    {
        return;
    }

    setEventVariableValue(variableId, eventVariableValue(variableId) - value);
}

int Party::fineGold() const
{
    return m_fineGold;
}

void Party::addFineGold(int amount)
{
    if (amount == 0)
    {
        return;
    }

    m_fineGold = std::clamp(m_fineGold + amount, 0, 4000000);
}

void Party::clearFineGold()
{
    m_fineGold = 0;
}

int32_t Party::continentReputation(uint32_t continentId) const
{
    const std::unordered_map<uint32_t, int32_t>::const_iterator it = m_continentReputations.find(continentId);
    return it != m_continentReputations.end() ? it->second : 0;
}

void Party::setContinentReputation(uint32_t continentId, int32_t value)
{
    if (continentId == 0)
    {
        return;
    }

    m_continentReputations[continentId] = clampReputation(value);
}

void Party::setClassSkillTable(const ClassSkillTable *pClassSkillTable)
{
    m_pClassSkillTable = pClassSkillTable;

    for (Character &member : m_members)
    {
        member.className = normalizePartyClassName(
            member.className.empty() ? member.role : member.className,
            m_pClassSkillTable);

        if (member.skills.empty())
        {
            applyDefaultStartingSkills(member);
        }

        member.synchronizeInnateAbilitySpells();

        if (m_pClassMultiplierTable != nullptr)
        {
            GameMechanics::refreshCharacterBaseResources(member, false, m_pClassMultiplierTable);
        }

        initializePortraitRuntimeState(member);
    }

    for (AdventurersInnMember &member : m_adventurersInnMembers)
    {
        member.character.className = normalizePartyClassName(
            member.character.className.empty() ? member.character.role : member.character.className,
            m_pClassSkillTable);

        if (member.character.skills.empty())
        {
            applyDefaultStartingSkills(member.character);
        }

        member.character.synchronizeInnateAbilitySpells();

        initializePortraitRuntimeState(member.character);
        member.portraitPictureId = resolveAdventurersInnPortraitPictureId(
            member.character,
            member.portraitPictureId,
            m_pCharacterDollTable);
    }

    // The members' base hit and spell points changed: what items, buffs and the rules add on top follows them.
    rebuildMagicalBonusesFromBuffs();
}

const ClassSkillTable *Party::classSkillTable() const
{
    return m_pClassSkillTable;
}

void Party::setTrainerDirectory(const TrainerDirectory *pTrainerDirectory)
{
    m_pTrainerDirectory = pTrainerDirectory;
}

const TrainerDirectory *Party::trainerDirectory() const
{
    return m_pTrainerDirectory;
}

void Party::setClassMultiplierTable(const ClassMultiplierTable *pClassMultiplierTable)
{
    m_pClassMultiplierTable = pClassMultiplierTable;
}

const ClassMultiplierTable *Party::classMultiplierTable() const
{
    return m_pClassMultiplierTable;
}

Party::Snapshot Party::snapshot() const
{
    Snapshot snapshot = {};
    snapshot.members = m_members;
    snapshot.adventurersInnMembers = m_adventurersInnMembers;
    snapshot.activeMemberIndex = m_activeMemberIndex;
    snapshot.partyBuffs = m_partyBuffs;
    snapshot.characterBuffs = m_characterBuffs;
    snapshot.gold = m_gold;
    snapshot.bankGold = m_bankGold;
    snapshot.food = m_food;
    snapshot.daysWithoutRest = m_daysWithoutRest;
    snapshot.awakeDayIndex = m_awakeDayIndex;
    snapshot.fineGold = m_fineGold;
    snapshot.waterDamageTicks = m_waterDamageTicks;
    snapshot.burningDamageTicks = m_burningDamageTicks;
    snapshot.splashCount = m_splashCount;
    snapshot.landingSoundCount = m_landingSoundCount;
    snapshot.hardLandingSoundCount = m_hardLandingSoundCount;
    snapshot.monsterTargetSelectionCounter = m_monsterTargetSelectionCounter;
    snapshot.houseStockSeed = m_houseStockSeed;
    snapshot.itemEffectElapsedGameSeconds = m_periodicEffectElapsedGameSeconds;
    snapshot.itemWeeklyEffectSequence = m_itemWeeklyEffectSequence;
    snapshot.lastFallDamageDistance = m_lastFallDamageDistance;
    snapshot.foundArtifactItems = m_foundArtifactItems;
    snapshot.arcomageWonHouseIds = m_arcomageWonHouseIds;
    snapshot.worldCompletions = m_worldCompletions;
    snapshot.worldCompletionsUntracked = m_worldCompletionsUntracked;
    snapshot.arcomageWinCount = m_arcomageWinCount;
    snapshot.arcomageLossCount = m_arcomageLossCount;
    snapshot.everOwnedItemIds = m_everOwnedItemIds;
    snapshot.chosenMm9RudeRows = m_chosenMm9RudeRows;
    snapshot.teacherLedgers = m_teacherLedgers;
    snapshot.explosiveMixes = m_explosiveMixes;
    snapshot.continentReputations = m_continentReputations;
    snapshot.questBits = m_questBits;
    snapshot.autonotes = m_autonotes;
    snapshot.historyEventTimesByContinent = m_historyEventTimesByContinent;
    snapshot.journalMapNotes = m_journalMapNotes;
    snapshot.eventVariables = m_eventVariables;
    snapshot.npcTopicOverrides = m_npcTopicOverrides;
    snapshot.npcGroupNews = m_npcGroupNews;
    snapshot.npcGreetingOverrides = m_npcGreetingOverrides;
    snapshot.npcGreetingDisplayCounts = m_npcGreetingDisplayCounts;
    snapshot.npcHouseOverrides = m_npcHouseOverrides;
    snapshot.npcItemOverrides = m_npcItemOverrides;
    snapshot.unavailableNpcIds = m_unavailableNpcIds;
    snapshot.hiredNpcFollowers = m_hiredNpcFollowers;
    snapshot.mm9Hirelings = m_mm9Hirelings;
    snapshot.memberFormationCells = m_memberFormationCells;
    snapshot.lastOutdoorMapFileName = m_lastOutdoorMapFileName;

    for (const auto &[houseId, state] : m_houseStockStates)
    {
        (void)houseId;
        snapshot.houseStockStates.push_back(state);
    }

    return snapshot;
}

void Party::restoreSnapshot(const Snapshot &snapshot)
{
    m_members = snapshot.members;
    m_adventurersInnMembers = snapshot.adventurersInnMembers;
    m_activeMemberIndex = snapshot.activeMemberIndex;
    m_partyBuffs = snapshot.partyBuffs;
    m_characterBuffs = snapshot.characterBuffs;
    m_gold = snapshot.gold;
    m_bankGold = snapshot.bankGold;
    m_food = snapshot.food;
    m_daysWithoutRest = snapshot.daysWithoutRest;
    m_awakeDayIndex = snapshot.awakeDayIndex;
    m_fineGold = snapshot.fineGold;
    m_waterDamageTicks = snapshot.waterDamageTicks;
    m_burningDamageTicks = snapshot.burningDamageTicks;
    m_splashCount = snapshot.splashCount;
    m_landingSoundCount = snapshot.landingSoundCount;
    m_hardLandingSoundCount = snapshot.hardLandingSoundCount;
    m_monsterTargetSelectionCounter = snapshot.monsterTargetSelectionCounter;
    m_houseStockSeed = snapshot.houseStockSeed;
    m_periodicEffectElapsedGameSeconds = snapshot.itemEffectElapsedGameSeconds;
    m_itemWeeklyEffectSequence = snapshot.itemWeeklyEffectSequence;
    m_lastFallDamageDistance = snapshot.lastFallDamageDistance;
    m_foundArtifactItems = snapshot.foundArtifactItems;
    m_arcomageWonHouseIds = snapshot.arcomageWonHouseIds;
    m_worldCompletions = snapshot.worldCompletions;
    m_worldCompletionsUntracked = snapshot.worldCompletionsUntracked;
    m_arcomageWinCount = snapshot.arcomageWinCount;
    m_arcomageLossCount = snapshot.arcomageLossCount;
    m_everOwnedItemIds = snapshot.everOwnedItemIds;
    m_chosenMm9RudeRows = snapshot.chosenMm9RudeRows;
    m_teacherLedgers = snapshot.teacherLedgers;
    m_explosiveMixes = snapshot.explosiveMixes;
    m_continentReputations = snapshot.continentReputations;
    m_questBits = snapshot.questBits;
    m_autonotes = snapshot.autonotes;
    m_historyEventTimesByContinent = snapshot.historyEventTimesByContinent;
    m_journalMapNotes = snapshot.journalMapNotes;
    m_eventVariables = snapshot.eventVariables;
    m_npcTopicOverrides = snapshot.npcTopicOverrides;
    m_npcGroupNews = snapshot.npcGroupNews;
    m_npcGreetingOverrides = snapshot.npcGreetingOverrides;
    m_npcGreetingDisplayCounts = snapshot.npcGreetingDisplayCounts;
    m_npcHouseOverrides = snapshot.npcHouseOverrides;
    m_npcItemOverrides = snapshot.npcItemOverrides;
    m_unavailableNpcIds = snapshot.unavailableNpcIds;
    m_hiredNpcFollowers = snapshot.hiredNpcFollowers;
    m_mm9Hirelings = snapshot.mm9Hirelings;
    m_activeHirelingIndex.reset();
    m_memberFormationCells = snapshot.memberFormationCells;
    m_lastOutdoorMapFileName = snapshot.lastOutdoorMapFileName;
    normalizeFormationCells();
    m_houseStockStates.clear();

    for (const HouseStockState &state : snapshot.houseStockStates)
    {
        m_houseStockStates[state.houseId] = state;
    }

    for (Character &member : m_members)
    {
        applyCharacterIdentityFromDollTable(member, m_pCharacterDollTable);
        member.synchronizeInnateAbilitySpells();
        initializePortraitRuntimeState(member);
    }

    for (AdventurersInnMember &member : m_adventurersInnMembers)
    {
        applyCharacterIdentityFromDollTable(member.character, m_pCharacterDollTable);
        member.character.synchronizeInnateAbilitySpells();
        initializePortraitRuntimeState(member.character);
        member.portraitPictureId = resolveAdventurersInnPortraitPictureId(
            member.character,
            member.portraitPictureId,
            m_pCharacterDollTable);
    }

    if (m_members.empty())
    {
        m_activeMemberIndex = 0;
    }
    else
    {
        m_activeMemberIndex = std::min(m_activeMemberIndex, m_members.size() - 1);
    }

    m_lastStatus.clear();
    m_heldItemIdForQueries = 0;
    m_pendingAudioRequests.clear();
    recordEverOwnedItemsFromCurrentState();
    rebuildMagicalBonusesFromBuffs();
    ++m_dialogueEligibilityRevision;
}

void Party::seed(const PartySeed &seed)
{
    // A new party plays by Standard rules until its owner installs a ruleset's; the rules of a party it replaces may
    // already be gone.
    m_pRules = nullptr;
    m_members = seed.members;
    m_adventurersInnMembers.clear();
    m_activeMemberIndex = 0;
    m_partyBuffs = {};
    m_characterBuffs = {};
    m_gold = std::max(0, seed.gold);
    m_bankGold = 0;
    m_food = std::max(0, seed.food);
    m_fineGold = 0;
    m_monsterTargetSelectionCounter = 0;
    m_houseStockSeed = generateHouseStockSeed();
    m_periodicEffectElapsedGameSeconds = 0.0f;
    m_itemWeeklyEffectSequence = 0;
    m_foundArtifactItems.clear();
    m_everOwnedItemIds.clear();
    m_chosenMm9RudeRows.clear();
    m_teacherLedgers.clear();
    m_explosiveMixes.clear();
    m_continentReputations.clear();
    m_questBits.clear();
    m_autonotes.clear();
    m_historyEventTimesByContinent.clear();
    m_journalMapNotes.clear();
    m_eventVariables.clear();
    m_npcTopicOverrides.clear();
    m_npcGroupNews.clear();
    m_npcGreetingOverrides.clear();
    m_npcGreetingDisplayCounts.clear();
    m_npcHouseOverrides.clear();
    m_npcItemOverrides.clear();
    m_unavailableNpcIds.clear();
    m_hiredNpcFollowers.clear();
    m_mm9Hirelings.clear();
    m_activeHirelingIndex.reset();
    m_memberFormationCells.clear();
    m_lastOutdoorMapFileName.clear();
    m_houseStockStates.clear();
    ++m_dialogueEligibilityRevision;

    for (Character &member : m_members)
    {
        const std::vector<InventoryItem> seededInventory = member.inventory;
        applyCharacterIdentityFromDollTable(member, m_pCharacterDollTable);
        member.className = canonicalClassName(member.className.empty() ? member.role : member.className);
        member.role = normalizeRoleName(member.className);
        member.level = std::max<uint32_t>(1, member.level);
        member.skillPoints = std::max<uint32_t>(0u, member.skillPoints);
        member.maxHealth = std::max(1, member.maxHealth);
        member.health = std::clamp(member.health, 0, member.maxHealth);
        member.maxSpellPoints = std::max(0, member.maxSpellPoints);
        member.spellPoints = std::clamp(member.spellPoints, 0, member.maxSpellPoints);
        member.inventory.clear();

        for (const InventoryItem &seededItem : seededInventory)
        {
            InventoryItem resolvedItem = makeInventoryItem(m_pItemTable, seededItem.objectDescriptionId);
            resolvedItem.quantity = seededItem.quantity;
            resolvedItem.gridX = seededItem.gridX;
            resolvedItem.gridY = seededItem.gridY;
            resolvedItem.identified = seededItem.identified;
            resolvedItem.broken = seededItem.broken;
            resolvedItem.stolen = seededItem.stolen;
            resolvedItem.hardened = seededItem.hardened;
            resolvedItem.standardEnchantId = seededItem.standardEnchantId;
            resolvedItem.standardEnchantPower = seededItem.standardEnchantPower;
            resolvedItem.specialEnchantId = seededItem.specialEnchantId;
            resolvedItem.artifactId = seededItem.artifactId;
            resolvedItem.rarity = seededItem.rarity;
            resolvedItem.temporaryBonusRemainingSeconds = seededItem.temporaryBonusRemainingSeconds;
            resolvedItem.rulesetFields = seededItem.rulesetFields;
            resolvedItem.workshopModId = seededItem.workshopModId;

            if (seededItem.currentCharges != 0 || seededItem.maxCharges != 0)
            {
                resolvedItem.currentCharges = seededItem.currentCharges;
                resolvedItem.maxCharges = seededItem.maxCharges;
            }

            resolvedItem.width = resolveInventoryWidth(seededItem.objectDescriptionId);
            resolvedItem.height = resolveInventoryHeight(seededItem.objectDescriptionId);

            const bool placed = (seededItem.width > 0 && seededItem.height > 0)
                ? member.addInventoryItemAt(resolvedItem, seededItem.gridX, seededItem.gridY)
                : member.addInventoryItem(resolvedItem);

            if (!placed)
            {
                continue;
            }

            markArtifactItemFoundIfRelevant(resolvedItem);
            recordEverOwnedItemIfRelevant(resolvedItem);
        }

        if (member.skills.empty())
        {
            applyDefaultStartingSkills(member);
        }

        member.synchronizeInnateAbilitySpells();

        for (EquipmentSlot slot : {
                 EquipmentSlot::OffHand,
                 EquipmentSlot::MainHand,
                 EquipmentSlot::Bow,
                 EquipmentSlot::Armor,
                 EquipmentSlot::Helm,
                 EquipmentSlot::Belt,
                 EquipmentSlot::Cloak,
                 EquipmentSlot::Gauntlets,
                 EquipmentSlot::Boots,
                 EquipmentSlot::Amulet,
                 EquipmentSlot::Ring1,
                 EquipmentSlot::Ring2,
                 EquipmentSlot::Ring3,
                 EquipmentSlot::Ring4,
                 EquipmentSlot::Ring5,
                 EquipmentSlot::Ring6})
        {
            const uint32_t itemId = ::OpenYAMM::Game::equippedItemId(member.equipment, slot);

            if (itemId == 0)
            {
                continue;
            }

            markArtifactItemFoundIfRelevant(
                makeInventoryItem(m_pItemTable, itemId, equippedItemRuntimeState(member.equipmentRuntime, slot)));
        }

        if (m_pClassMultiplierTable != nullptr)
        {
            GameMechanics::refreshCharacterBaseResources(member, false, m_pClassMultiplierTable);
        }

        initializePortraitRuntimeState(member);
    }

    if (m_members.empty())
    {
        Character fallbackMember = {};
        fallbackMember.name = "Adventurer";
        fallbackMember.className = "Knight";
        fallbackMember.role = "Knight";
        fallbackMember.level = 1;
        fallbackMember.skillPoints = 0;
        fallbackMember.maxHealth = 100;
        fallbackMember.health = 100;
        m_members.push_back(fallbackMember);
    }

    for (const InventoryItem &item : seed.inventory)
    {
        grantItem(item.objectDescriptionId, std::max<uint32_t>(1, item.quantity));
    }

    m_waterDamageTicks = 0;
    m_burningDamageTicks = 0;
    m_splashCount = 0;
    m_landingSoundCount = 0;
    m_hardLandingSoundCount = 0;
    m_lastFallDamageDistance = 0.0f;
    m_daysWithoutRest = 0;
    m_awakeDayIndex.reset();
    m_lastStatus.clear();
    m_heldItemIdForQueries = 0;
    m_pendingAudioRequests.clear();
    normalizeFormationCells();
    recordEverOwnedItemsFromCurrentState();
    rebuildMagicalBonusesFromBuffs();
}

void Party::applyMovementEffects(const OutdoorMovementEffects &effects)
{
    for (uint32_t i = 0; i < effects.waterDamageTicks; ++i)
    {
        for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
        {
            // A Wetsuit keeps its wearer from drowning, as in MM7 (OY-309).
            if (m_members[memberIndex].waterWalking || GameMechanics::hasWetsuitEquipped(m_members[memberIndex]))
            {
                continue;
            }

            const int damage = rules().combat.environmentDamage(*this, memberIndex,
                std::max(1, m_members[memberIndex].maxHealth / 10), CombatDamageType::Water, effects.indoor);
            applyDamageToMember(memberIndex, damage, "");
        }

        m_waterDamageTicks += 1;
        m_lastStatus = "water damage";
    }

    for (uint32_t i = 0; i < effects.burningDamageTicks; ++i)
    {
        for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
        {
            const Character &member = m_members[memberIndex];
            const CombatDamageType burnType = m_floorBurnType.value_or(CombatDamageType::Fire);
            int damage = rules().combat.environmentDamage(*this, memberIndex,
                std::max(1, member.maxHealth / 10), burnType, effects.indoor);

            if (m_floorBurnResisted)
            {
                static thread_local std::mt19937 rng(std::random_device{}());
                damage = GameMechanics::resolveCharacterIncomingDamage(member, m_pItemTable,
                    m_pStandardItemEnchantTable, m_pSpecialItemEnchantTable, damage, burnType, rng);
            }
            else if (burnType == CombatDamageType::Fire && member.equippedItemEffectFlags.contains("FireImmune"))
            {
                damage = 0;
            }

            applyDamageToMember(memberIndex, damage, "");
        }

        m_burningDamageTicks += 1;
        m_lastStatus = "burning damage";
    }

    if (effects.maxFallDamageDistance > 0.0f)
    {
        m_lastFallDamageDistance = std::max(m_lastFallDamageDistance, effects.maxFallDamageDistance);

        for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
        {
            if (m_members[memberIndex].featherFalling)
            {
                continue;
            }

            const int fallDistance = std::max(0, static_cast<int>(effects.maxFallDamageDistance));
            const int healthFactor = std::max(0, m_members[memberIndex].maxHealth) / 10;
            const int damage = static_cast<int>(
                std::min<int64_t>(
                    std::numeric_limits<int>::max(),
                    static_cast<int64_t>(fallDistance) * healthFactor / 256));
            const int taken =
                rules().combat.environmentDamage(*this, memberIndex, damage, CombatDamageType::Physical, effects.indoor);
            applyDamageToMember(memberIndex, taken, "falling");
        }

        m_lastStatus = "fall damage";
    }

    if (effects.playSplashSound)
    {
        m_splashCount += 1;
        m_lastStatus = "splash";
        queueSound(SoundId::Splash);
    }

    if (effects.playLandingSound)
    {
        m_landingSoundCount += 1;
        m_lastStatus = "landing";
    }

    if (effects.playHardLandingSound)
    {
        m_hardLandingSoundCount += 1;
        m_lastStatus = "hard landing";
    }
}

void Party::applyEventRuntimeState(const EventRuntimeState &runtimeState, bool grantItemsToInventory)
{
    for (const InventoryItem &item : runtimeState.grantedItems)
    {
        if (grantItemsToInventory)
        {
            size_t recipientMemberIndex = 0;
            if (tryGrantInventoryItem(item, &recipientMemberIndex))
            {
                queueSound(SoundId::Gold);
                GAMEPLAY_DEBUG_TRACE(
                    "item_received destination=inventory source=event item_id="
                    + std::to_string(item.objectDescriptionId)
                    + gameplayDebugTraceItemSummary(item.objectDescriptionId, m_pItemTable)
                    + " member_index=" + std::to_string(recipientMemberIndex));
            }
        }
        else if (item.objectDescriptionId != 0)
        {
            markArtifactItemFoundIfRelevant(item);
        }

        m_lastStatus = "item granted";
    }

    for (uint32_t itemId : runtimeState.grantedItemIds)
    {
        if (grantItemsToInventory)
        {
            if (tryGrantItem(itemId))
            {
                queueSound(SoundId::Gold);
                GAMEPLAY_DEBUG_TRACE(
                    "item_received destination=inventory source=event item_id="
                    + std::to_string(itemId)
                    + gameplayDebugTraceItemSummary(itemId, m_pItemTable));
            }
        }
        else if (itemId != 0)
        {
            markArtifactItemFoundIfRelevant(makeInventoryItem(m_pItemTable, itemId));
        }

        m_lastStatus = "item granted";
    }

    for (uint32_t itemId : runtimeState.removedItemIds)
    {
        if (removeItem(itemId))
        {
            m_lastStatus = "item removed";
        }
    }

    for (uint32_t awardId : runtimeState.grantedAwardIds)
    {
        addAward(awardId);
        m_lastStatus = "award granted";
    }

    for (uint32_t awardId : runtimeState.removedAwardIds)
    {
        removeAward(awardId);
        m_lastStatus = "award removed";
    }

    bool followersChanged = false;
    for (const HiredNpcFollower &follower : runtimeState.hiredNpcFollowers)
    {
        // A world without followers (MM9) never takes new ones from its events.
        if (follower.npcId == 0 || !m_npcFollowersActive)
        {
            continue;
        }

        const auto followerIt = std::find_if(
            m_hiredNpcFollowers.begin(),
            m_hiredNpcFollowers.end(),
            [&follower](const HiredNpcFollower &existingFollower)
            {
                return existingFollower.npcId == follower.npcId;
            });

        if (followerIt == m_hiredNpcFollowers.end())
        {
            m_hiredNpcFollowers.push_back(follower);
            followersChanged = true;
        }
        else
        {
            followersChanged = followersChanged || followerIt->professionId != follower.professionId;
            *followerIt = follower;
        }
    }

    for (const HiredNpcFollower &follower : m_hiredNpcFollowers)
    {
        if (follower.npcId != 0)
        {
            m_unavailableNpcIds.insert(follower.npcId);
        }
    }
    if (followersChanged)
    {
        rebuildMagicalBonusesFromBuffs();
    }
}

bool Party::applyDamageToActiveMember(int damage, const std::string &status)
{
    if (damage <= 0 || m_members.empty())
    {
        return false;
    }

    size_t targetIndex = std::min(m_activeMemberIndex, m_members.size() - 1);

    if (m_members[targetIndex].health <= 0)
    {
        bool foundLivingMember = false;

        for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
        {
            if (m_members[memberIndex].health > 0)
            {
                targetIndex = memberIndex;
                foundLivingMember = true;
                break;
            }
        }

        if (!foundLivingMember)
        {
            return false;
        }
    }

    return applyDamageToMember(targetIndex, damage, status);
}

bool Party::applyPotionExplosionToMember(size_t memberIndex, uint8_t damageLevel)
{
    if (memberIndex >= m_members.size() || damageLevel == 0)
    {
        return false;
    }

    if (damageLevel >= 4)
    {
        applyMemberCondition(memberIndex, CharacterCondition::Eradicated);
        breakPotionExplosionItems(m_members[memberIndex], 0);
        return true;
    }

    bool applied = applyDamageToMember(memberIndex, potionExplosionDamage(damageLevel), "");

    if (damageLevel == 2)
    {
        breakPotionExplosionItems(m_members[memberIndex], 1);
        applied = true;
    }
    else if (damageLevel == 3)
    {
        breakPotionExplosionItems(m_members[memberIndex], 5);
        applied = true;
    }

    return applied;
}

void Party::setDebugDamageImmune(bool enabled)
{
    m_debugDamageImmune = enabled;
}

void Party::setDebugUnlimitedMana(bool enabled)
{
    m_debugUnlimitedMana = enabled;
}

bool Party::applyDamageToMember(
    size_t memberIndex,
    int damage,
    const std::string &status,
    bool allowUnconscious)
{
    // The source the combat controller named for this hit only (setIncomingDamageSource).
    const std::optional<std::pair<StatDamageTakenKind, std::string>> incomingSource = m_incomingDamageSource;
    m_incomingDamageSource.reset();

    if (damage > 0 && isHirelingCombatant(memberIndex))
    {
        return applyDamageToHireling(memberIndex, damage, status);
    }

    if (damage <= 0 || memberIndex >= m_members.size())
    {
        return false;
    }

    Character &member = m_members[memberIndex];
    const int previousHealth = member.health;
    const bool couldActBeforeDamage = GameMechanics::canAct(member);
    const size_t actingMembersBeforeDamage = countActingMembers(m_members);

    if (member.health <= 0 && (!allowUnconscious || !canReceiveUnconsciousAoeDamage(member)))
    {
        return false;
    }

    // The rules' shields take their share of every hit first (MAW's Mana Shield and lethal-damage saves).
    damage = rules().combat.absorbCharacterDamage(*this, memberIndex, damage);

    if (damage <= 0)
    {
        return true;
    }

    if (!m_debugDamageImmune)
    {
        const bool wasDead = member.conditions.test(static_cast<size_t>(CharacterCondition::Dead));
        const bool wasUnconscious = member.conditions.test(static_cast<size_t>(CharacterCondition::Unconscious));
        member.health -= damage;
        const bool preservationActive =
            m_characterBuffs[memberIndex][static_cast<size_t>(CharacterBuffId::Preservation)].active();
        updateMemberIncapacitatedCondition(member, preservationActive, m_gameMinutes);

        if (m_statistics.pStatistics != nullptr)
        {
            const StatDamageTakenKind kind =
                status.empty() && incomingSource ? incomingSource->first : StatDamageTakenKind::Environment;
            const std::string cause = !status.empty() ? status : incomingSource ? incomingSource->second : "";
            const StatMemberRef ref = statsMember(memberIndex);
            m_statistics.pStatistics->recordDamageTaken(ref, kind, uint64_t(damage), cause);
            m_lastDamageCause[ref.id] = cause;

            if (!wasDead && member.conditions.test(static_cast<size_t>(CharacterCondition::Dead)))
            {
                m_statistics.pStatistics->recordDeath(ref, false, cause);
            }
            else if (!wasUnconscious && member.conditions.test(static_cast<size_t>(CharacterCondition::Unconscious)))
            {
                m_statistics.pStatistics->recordKnockout(ref);
            }
        }
        rules().combat.characterDamaged(*this, memberIndex);

        if (preservationActive && previousHealth > 0 && member.health <= 0)
        {
            queueSpeech(memberIndex, SpeechId::CheatedDeath);
        }
    }

    const bool crossedMajorDamageThreshold =
        member.maxHealth > 0
        && previousHealth > member.maxHealth / 4
        && member.health > 0
        && member.health <= member.maxHealth / 4;

    if (status == "falling")
    {
        if (couldActBeforeDamage)
        {
            queueSpeech(memberIndex, SpeechId::Falling);
        }
    }
    else if (GameMechanics::canAct(member))
    {
        queueSpeech(memberIndex, SpeechId::DamageMinor);
    }

    // Only the blow that takes the member down: an unconscious one finished off by area damage stays silent.
    if (member.health <= 0 && previousHealth > 0)
    {
        queueSpeech(memberIndex, SpeechId::Dying);
    }
    else if (crossedMajorDamageThreshold)
    {
        queueSpeech(memberIndex, SpeechId::DamageMajor);
    }

    if (actingMembersBeforeDamage > 1 && countActingMembers(m_members) == 1)
    {
        const std::optional<size_t> remainingMemberIndex = firstActingMemberIndex(m_members);

        if (remainingMemberIndex)
        {
            queueSpeech(*remainingMemberIndex, SpeechId::LastPersonStanding);
        }
    }

    if (!status.empty())
    {
        m_lastStatus = status;
    }

    return true;
}

void Party::updateHirelingKnockOut(Character &hireling) const
{
    if (isDeadOrEradicated(hireling))
    {
        return;
    }

    const size_t unconsciousIndex = size_t(CharacterCondition::Unconscious);

    if (hireling.health > 0)
    {
        hireling.conditions.reset(unconsciousIndex);
        hireling.conditionStartGameMinutes[unconsciousIndex] = 0.0f;
        return;
    }

    hireling.health = 0;

    if (!hireling.conditions.test(unconsciousIndex))
    {
        hireling.conditionStartGameMinutes[unconsciousIndex] = std::max(0.0f, m_gameMinutes);
    }

    hireling.conditions.set(unconsciousIndex);
}

bool Party::applyDamageToHireling(size_t combatantIndex, int damage, const std::string &status)
{
    Character *pHireling = combatant(combatantIndex);

    // The shields, the ruleset's absorption and the voices are the members'; a hireling has none of them.
    if (pHireling == nullptr || damage <= 0 || pHireling->health <= 0 || isDeadOrEradicated(*pHireling))
    {
        return false;
    }

    if (!m_debugDamageImmune)
    {
        pHireling->health = std::max(0, pHireling->health - damage);
        updateHirelingKnockOut(*pHireling);
    }

    if (!status.empty())
    {
        m_lastStatus = status;
    }

    return true;
}

bool Party::applyDamageToAllLivingMembers(int damage, const std::string &status)
{
    if (damage <= 0 || m_members.empty())
    {
        return false;
    }

    bool applied = false;
    size_t appliedCount = 0;

    // The whole party: the hirelings too (MM9).
    for (size_t memberIndex = 0; memberIndex < combatantCount(); ++memberIndex)
    {
        const Character &member = *combatant(memberIndex);

        if (member.health <= 0 && !canReceiveUnconsciousAoeDamage(member))
        {
            continue;
        }

        if (applyDamageToMember(memberIndex, damage, "", true))
        {
            applied = true;
            ++appliedCount;
        }
    }

    if (appliedCount > 1)
    {
        queueSpeech(activeMemberIndex(), SpeechId::DamagedParty);
    }

    if (applied && !status.empty())
    {
        m_lastStatus = status;
    }

    return applied;
}

uint64_t Party::addExperienceToMember(size_t memberIndex, int64_t amount, ExperienceReason reason)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return 0;
    }

    // The cap stays far below int64_t's range, so the sum cannot overflow.
    const uint64_t previousExperience = pMember->experience;
    const int64_t maximum = int64_t(rules().experience.maximumExperience());
    pMember->experience = uint64_t(std::clamp<int64_t>(int64_t(pMember->experience) + amount, 0, maximum));

    if (m_statistics.pStatistics != nullptr && pMember->experience > previousExperience)
    {
        const ExperienceReason countedReason = reason != ExperienceReason::Other ? reason : m_experienceReasonScope;
        m_statistics.pStatistics->recordExperience(
            statsMember(memberIndex), countedReason, pMember->experience - previousExperience);
    }

    return pMember->experience;
}

uint64_t Party::setMemberExperience(size_t memberIndex, uint64_t experience)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return 0;
    }

    pMember->experience = std::min(experience, rules().experience.maximumExperience());
    return pMember->experience;
}

void Party::setRules(const GameRules *pRules)
{
    m_pRules = pRules;
}

void Party::setStatistics(PlaythroughStatistics *pStatistics)
{
    m_statistics.pStatistics = pStatistics;
}

PlaythroughStatistics *Party::statistics() const
{
    return m_statistics.pStatistics;
}

void Party::assignStatsMemberIds()
{
    for (Character &member : m_members)
    {
        if (member.statsMemberId == 0)
        {
            std::random_device device;
            member.statsMemberId = ((uint64_t(device()) << 32) ^ device()) | 1u;
        }
    }
}

StatMemberRef Party::statsMember(size_t memberIndex) const
{
    const Character *pMember = memberIndex < m_members.size() ? &m_members[memberIndex] : nullptr;

    if (pMember == nullptr)
    {
        return {};
    }

    return {pMember->statsMemberId, pMember->name, pMember->className};
}

void Party::setIncomingDamageSource(StatDamageTakenKind kind, const std::string &cause)
{
    m_incomingDamageSource = std::make_pair(kind, cause);
}

void Party::recordConditionStatistics(size_t memberIndex, CharacterCondition condition)
{
    if (m_statistics.pStatistics == nullptr || memberIndex >= m_members.size())
    {
        return;
    }

    const StatMemberRef ref = statsMember(memberIndex);
    const auto cause = m_lastDamageCause.find(ref.id);
    const std::string causeName = cause != m_lastDamageCause.end() ? cause->second : std::string();

    if (condition == CharacterCondition::Dead || condition == CharacterCondition::Eradicated)
    {
        m_statistics.pStatistics->recordDeath(ref, condition == CharacterCondition::Eradicated, causeName);
    }
    else if (condition == CharacterCondition::Petrified)
    {
        m_statistics.pStatistics->recordStoned();
    }
}

void Party::setRulesMovementMultiplier(float multiplier)
{
    m_rulesMovementMultiplier = std::clamp(multiplier, 0.0f, 1.0f);
}

float Party::rulesMovementMultiplier() const
{
    return m_rulesMovementMultiplier;
}

const GameRules &Party::rules() const
{
    return m_pRules != nullptr ? *m_pRules : standardGameRules();
}

uint32_t Party::grantMonsterKillExperience(const MonsterKillReward &kill)
{
    // Every gain the rules make for the kill counts as monster experience.
    const ExperienceReason previousScope = m_experienceReasonScope;
    m_experienceReasonScope = ExperienceReason::Monster;
    const uint32_t experience = rules().experience.grantKillExperience(*this, kill);
    m_experienceReasonScope = previousScope;
    return experience;
}

uint32_t Party::grantSharedExperience(uint32_t totalExperience, ExperienceReason reason)
{
    if (totalExperience == 0)
    {
        return 0;
    }

    size_t eligibleMemberCount = 0;

    for (const Character &member : m_members)
    {
        if (canReceiveSharedExperience(member))
        {
            ++eligibleMemberCount;
        }
    }

    if (eligibleMemberCount == 0)
    {
        return 0;
    }

    // Cleirach A'Lyrae: the award times 1.1 before it is split (object@0x10054c60).
    const int hirelingPercent = mm9HirelingPassives().experiencePercent;
    if (hirelingPercent > 0)
    {
        totalExperience += uint32_t(uint64_t(totalExperience) * uint32_t(hirelingPercent) / 100u);
    }

    const uint32_t experiencePerEligibleMember = totalExperience / eligibleMemberCount;
    uint32_t totalGrantedExperience = 0;

    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        const Character &member = m_members[memberIndex];

        if (!canReceiveSharedExperience(member))
        {
            continue;
        }

        const int learningPercent =
            rules().experience.learningGrantsExperience() ? learningPercentForExperienceGain(member) : 0;
        const uint32_t learnedExperience =
            experiencePerEligibleMember + experiencePerEligibleMember * learningPercent / 100;
        const uint32_t grantedExperience = static_cast<uint32_t>(std::max(
            0.0f,
            std::floor(static_cast<float>(learnedExperience) * member.experienceGainMultiplier)));
        addExperienceToMember(memberIndex, grantedExperience, reason);
        totalGrantedExperience += grantedExperience;
    }

    if (m_statistics.pStatistics != nullptr && reason == ExperienceReason::Event)
    {
        m_statistics.pStatistics->recordExperienceAward(totalGrantedExperience);
    }

    return totalGrantedExperience;
}

std::optional<size_t> Party::chooseMonsterAttackTarget(uint32_t attackPreferences, uint32_t seedHint)
{
    // MM9's formation (the MM9 world): the blow picks a combatant by rank; MM9 monsters have no preferences.
    if (m_formationTargetingActive)
    {
        const uint32_t selectionSeed =
            seedHint * 1103515245u + m_monsterTargetSelectionCounter * 2654435761u + 12345u;
        ++m_monsterTargetSelectionCounter;
        return chooseFormationAttackTarget(selectionSeed);
    }

    std::vector<size_t> candidates;
    candidates.reserve(m_members.size());

    static constexpr std::array<uint32_t, 15> PreferenceFlags = {{
        MonsterAttackPreferenceKnight,
        MonsterAttackPreferencePaladin,
        MonsterAttackPreferenceArcher,
        MonsterAttackPreferenceDruid,
        MonsterAttackPreferenceCleric,
        MonsterAttackPreferenceSorcerer,
        MonsterAttackPreferenceRanger,
        MonsterAttackPreferenceThief,
        MonsterAttackPreferenceMonk,
        MonsterAttackPreferenceMale,
        MonsterAttackPreferenceFemale,
        MonsterAttackPreferenceHuman,
        MonsterAttackPreferenceElf,
        MonsterAttackPreferenceDwarf,
        MonsterAttackPreferenceGoblin,
    }};

    if (attackPreferences != 0)
    {
        for (uint32_t preferenceFlag : PreferenceFlags)
        {
            if ((attackPreferences & preferenceFlag) == 0)
            {
                continue;
            }

            for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
            {
                const Character &member = m_members[memberIndex];

                if (!isValidMonsterAttackTarget(member) || !matchesMonsterAttackPreference(member, preferenceFlag))
                {
                    continue;
                }

                candidates.push_back(memberIndex);
            }
        }
    }

    if (candidates.empty())
    {
        for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
        {
            if (isValidMonsterAttackTarget(m_members[memberIndex]))
            {
                candidates.push_back(memberIndex);
            }
        }
    }

    if (candidates.empty())
    {
        return std::nullopt;
    }

    const uint32_t selectionSeed =
        seedHint * 1103515245u + m_monsterTargetSelectionCounter * 2654435761u + 12345u;
    ++m_monsterTargetSelectionCounter;
    return candidates[selectionSeed % candidates.size()];
}

void Party::addGold(int amount, GoldReason reason)
{
    const int previousGold = m_gold;
    m_gold = std::max(0, m_gold + amount);

    if (m_gold != previousGold)
    {
        ++m_dialogueEligibilityRevision;
        queueSound(SoundId::Gold);

        if (m_statistics.pStatistics != nullptr)
        {
            m_statistics.pStatistics->recordGold(int64_t(m_gold) - int64_t(previousGold), reason);
        }
    }
}

void Party::addFood(int amount)
{
    m_food = std::max(0, m_food + amount);
}

void Party::requestSound(SoundId soundId)
{
    queueSound(soundId);
}

void Party::requestDamageImpactSoundForMember(size_t memberIndex)
{
    queueSound(resolveDamageImpactSoundForMember(memberIndex));
}

void Party::requestSpeech(size_t memberIndex, SpeechId speechId)
{
    queueSpeech(memberIndex, speechId);
}

namespace
{
// Into the member's open bag, else another of their bags (a ruleset with several, MAW); the open bag stays open.
bool addToAnyBag(Character &member, const InventoryItem &item, int bagCount)
{
    if (member.addInventoryItem(item))
    {
        return true;
    }

    const uint8_t openBag = member.rulesetState.currentBag;
    bool added = false;

    for (int bag = 0; bag < bagCount && !added; ++bag)
    {
        added = InventoryBags::openBag(member, uint8_t(bag), bagCount) && member.addInventoryItem(item);
    }

    InventoryBags::openBag(member, openBag, bagCount);
    return added;
}

// One of the item out of the member's open bag, else out of their other bags (MAW); the open bag stays open.
bool removeFromAnyBag(Character &member, uint32_t objectDescriptionId)
{
    if (member.removeInventoryItem(objectDescriptionId))
    {
        return true;
    }

    for (auto &[bag, items] : member.rulesetState.storedBags)
    {
        const auto found = std::find_if(items.begin(), items.end(),
            [objectDescriptionId](const InventoryItem &item)
            {
                return item.objectDescriptionId == objectDescriptionId;
            });

        if (found != items.end())
        {
            if (found->quantity > 1)
            {
                --found->quantity;
            }
            else
            {
                items.erase(found);
            }

            return true;
        }
    }

    return false;
}
}

bool Party::tryGrantItem(uint32_t objectDescriptionId, uint32_t quantity)
{
    if (objectDescriptionId == 0 || quantity == 0)
    {
        return false;
    }

    std::vector<Character> testMembers = m_members;

    if (testMembers.empty())
    {
        m_lastStatus = "inventory full";
        return false;
    }

    const int bagCount = rules().items.bagCount(*this);

    for (uint32_t itemCount = 0; itemCount < quantity; ++itemCount)
    {
        InventoryItem item = makeInventoryItem(m_pItemTable, objectDescriptionId);
        // A fixed item that an event, a quest or a start gives comes identified, as in the originals (OY-182).
        item.identified = true;

        bool added = false;

        const size_t firstIndex = std::min(activeMemberIndex(), testMembers.size() - 1);

        for (size_t offset = 0; offset < testMembers.size(); ++offset)
        {
            Character &member = testMembers[(firstIndex + offset) % testMembers.size()];

            if (addToAnyBag(member, item, bagCount))
            {
                added = true;
                break;
            }
        }

        if (!added)
        {
            m_lastStatus = "inventory full";
            return false;
        }
    }

    // Member by member, so pointers to the members stay valid: an attack holds its attacker while a kill's reward
    // (MAW's map completion) reaches the party.
    for (size_t memberIndex = 0; memberIndex < testMembers.size(); ++memberIndex)
    {
        m_members[memberIndex] = std::move(testMembers[memberIndex]);
    }

    const InventoryItem recordedItem = makeInventoryItem(m_pItemTable, objectDescriptionId);
    markArtifactItemFoundIfRelevant(recordedItem);
    recordEverOwnedItemIfRelevant(recordedItem);
    return true;
}

bool Party::tryGrantInventoryItem(const InventoryItem &item, size_t *pRecipientMemberIndex)
{
    return tryGrantInventoryItemStartingAt(activeMemberIndex(), item, pRecipientMemberIndex);
}

bool Party::tryGrantInventoryItemToMember(size_t memberIndex, const InventoryItem &item)
{
    Character *pMember = member(memberIndex);
    if (pMember == nullptr || item.objectDescriptionId == 0 || item.quantity == 0 || !pMember->addInventoryItem(item))
    {
        m_lastStatus = "inventory full";
        return false;
    }
    markArtifactItemFoundIfRelevant(item);
    recordEverOwnedItemIfRelevant(item);
    return true;
}

bool Party::canGrantInventoryItem(const InventoryItem &item) const
{
    if (item.objectDescriptionId == 0 || item.quantity == 0)
    {
        return false;
    }

    const int bagCount = rules().items.bagCount(*this);

    for (const Character &member : m_members)
    {
        Character testMember = member;

        if (addToAnyBag(testMember, item, bagCount))
        {
            return true;
        }
    }

    return false;
}

bool Party::tryGrantInventoryItemStartingAt(
    size_t firstMemberIndex,
    const InventoryItem &item,
    size_t *pRecipientMemberIndex)
{
    if (item.objectDescriptionId == 0 || item.quantity == 0)
    {
        return false;
    }

    std::vector<Character> testMembers = m_members;

    if (testMembers.empty())
    {
        m_lastStatus = "inventory full";
        return false;
    }

    const size_t firstIndex = std::min(firstMemberIndex, testMembers.size() - 1);
    const int bagCount = rules().items.bagCount(*this);

    for (size_t offset = 0; offset < testMembers.size(); ++offset)
    {
        const size_t memberIndex = (firstIndex + offset) % testMembers.size();
        Character &member = testMembers[memberIndex];

        if (addToAnyBag(member, item, bagCount))
        {
            // Only the member who took it, so pointers to the members stay valid (see tryGrantItem).
            m_members[memberIndex] = std::move(member);
            markArtifactItemFoundIfRelevant(item);
            recordEverOwnedItemIfRelevant(item);

            if (pRecipientMemberIndex != nullptr)
            {
                *pRecipientMemberIndex = memberIndex;
            }

            return true;
        }
    }

    m_lastStatus = "inventory full";
    return false;
}

void Party::grantItem(uint32_t objectDescriptionId, uint32_t quantity)
{
    if (!tryGrantItem(objectDescriptionId, quantity))
    {
        return;
    }
}

bool Party::removeItem(uint32_t objectDescriptionId, uint32_t quantity)
{
    if (objectDescriptionId == 0 || quantity == 0)
    {
        return false;
    }

    uint32_t availableCount = 0;

    for (const Character &member : m_members)
    {
        for (const InventoryItem &item : member.inventory)
        {
            if (item.objectDescriptionId == objectDescriptionId)
            {
                availableCount += item.quantity;
            }
        }

        for (const auto &[bag, items] : member.rulesetState.storedBags)
        {
            for (const InventoryItem &item : items)
            {
                if (item.objectDescriptionId == objectDescriptionId)
                {
                    availableCount += item.quantity;
                }
            }
        }
    }

    if (availableCount < quantity)
    {
        return false;
    }

    uint32_t removedCount = 0;

    for (Character &member : m_members)
    {
        while (removedCount < quantity && removeFromAnyBag(member, objectDescriptionId))
        {
            removedCount += 1;
        }
    }

    return removedCount == quantity;
}

int Party::effectiveMaximumHealth(const Character &member)
{
    return GameMechanics::calculateEffectiveCharacterMaxHealth(member);
}

int Party::effectiveMaximumSpellPoints(const Character &member)
{
    return GameMechanics::calculateEffectiveCharacterMaxSpellPoints(member);
}

int Party::reachableMaximumHealth(size_t memberIndex) const
{
    // A hireling has no auras to reserve HP.
    if (const Mm9PartyHireling *pHireling = hirelingCombatant(memberIndex))
    {
        return std::max(1, effectiveMaximumHealth(pHireling->character));
    }

    return std::max(1,
        effectiveMaximumHealth(m_members[memberIndex]) - rules().spells.reservedHitPoints(*this, memberIndex));
}

int Party::reachableMaximumSpellPoints(size_t memberIndex) const
{
    return std::max(0,
        effectiveMaximumSpellPoints(m_members[memberIndex]) - rules().spells.reservedSpellPoints(*this, memberIndex));
}

bool Party::needsHealing() const
{
    for (const Character &member : m_members)
    {
        if (characterNeedsTempleHealing(member))
        {
            return true;
        }
    }

    return false;
}

bool Party::activeMemberNeedsHealing() const
{
    const Character *pMember = activeMember();

    if (pMember == nullptr)
    {
        return false;
    }

    return characterNeedsTempleHealing(*pMember);
}

void Party::restoreAll()
{
    restAndHealAll();
}

void Party::reviveAndRestoreAll()
{
    for (Character &member : m_members)
    {
        clearTemporaryEventBonuses(member);
    }

    m_partyBuffs = {};
    m_characterBuffs = {};

    for (Mm9PartyHireling &hireling : m_mm9Hirelings)
    {
        hireling.buffs = {};
    }

    rebuildMagicalBonusesFromBuffs();

    // The hirelings too.
    for (size_t combatantIndex = 0; combatantIndex < combatantCount(); ++combatantIndex)
    {
        Character &member = *combatant(combatantIndex);
        member.conditions.reset();
        member.conditionStartGameMinutes.fill(0.0f);
        member.recoverySecondsRemaining = 0.0f;
        member.healthRegenAccumulator = 0.0f;
        member.spellRegenAccumulator = 0.0f;
        member.health = currentMaximumHealth(member);
        member.spellPoints = currentMaximumSpellPoints(member);
    }

    if (!canSelectMemberInGameplay(m_activeMemberIndex))
    {
        m_activeMemberIndex = 0;
        switchToNextReadyMember();
    }
}

void Party::restAndHealAll()
{
    for (Character &member : m_members)
    {
        clearTemporaryEventBonuses(member);
    }

    m_partyBuffs = {};
    m_characterBuffs = {};

    for (Mm9PartyHireling &hireling : m_mm9Hirelings)
    {
        hireling.buffs = {};
    }

    rebuildMagicalBonusesFromBuffs();

    // The hirelings rest with the party: a knocked-out one wakes; the dead stay for a temple or a spell.
    for (size_t combatantIndex = 0; combatantIndex < combatantCount(); ++combatantIndex)
    {
        Character &member = *combatant(combatantIndex);

        if (member.conditions.test(static_cast<size_t>(CharacterCondition::Dead))
            || member.conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
            || member.conditions.test(static_cast<size_t>(CharacterCondition::Eradicated)))
        {
            continue;
        }

        member.conditions.reset(static_cast<size_t>(CharacterCondition::Unconscious));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Unconscious)] = 0.0f;
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Drunk));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Drunk)] = 0.0f;
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Fear));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Fear)] = 0.0f;
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Asleep));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Asleep)] = 0.0f;
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Weak));
        member.conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Weak)] = 0.0f;
        member.recoverySecondsRemaining = 0.0f;

        member.health = currentMaximumHealth(member);
        member.spellPoints = currentMaximumSpellPoints(member);

        if (member.conditions.test(static_cast<size_t>(CharacterCondition::Zombie)))
        {
            member.health = std::max(1, member.health / 2);
            member.spellPoints = 0;
        }
        else if (member.conditions.test(static_cast<size_t>(CharacterCondition::PoisonSevere))
            || member.conditions.test(static_cast<size_t>(CharacterCondition::DiseaseSevere)))
        {
            member.health = std::max(1, member.health / 4);
            member.spellPoints /= 4;
        }
        else if (member.conditions.test(static_cast<size_t>(CharacterCondition::PoisonMedium))
            || member.conditions.test(static_cast<size_t>(CharacterCondition::DiseaseMedium)))
        {
            member.health = std::max(1, member.health / 3);
            member.spellPoints /= 3;
        }
        else if (member.conditions.test(static_cast<size_t>(CharacterCondition::PoisonWeak))
            || member.conditions.test(static_cast<size_t>(CharacterCondition::DiseaseWeak)))
        {
            member.health = std::max(1, member.health / 2);
            member.spellPoints /= 2;
        }

        if (member.conditions.test(static_cast<size_t>(CharacterCondition::Insane)))
        {
            member.spellPoints = 0;
        }
    }

    clearDaysWithoutRest();
}

int Party::daysWithoutRest() const
{
    return m_daysWithoutRest;
}

void Party::clearDaysWithoutRest()
{
    m_daysWithoutRest = 0;
    m_awakeDayIndex.reset();
}

void Party::addDayWithoutRest()
{
    ++m_daysWithoutRest;
}

void Party::setGameMinutes(float gameMinutes)
{
    m_gameMinutes = std::max(0.0f, gameMinutes);
    // The calendar's year: 12 months of 28 days (OY-349).
    constexpr float MinutesPerYear = 12.0f * 28.0f * 24.0f * 60.0f;
    const uint32_t playedYears = uint32_t(m_gameMinutes / MinutesPerYear);

    // Timed conditions (a monster spell's duration) wear off once the clock passes them; a time left on a condition
    // that something else cleared is dropped.
    for (size_t combatantIndex = 0; combatantIndex < combatantCount(); ++combatantIndex)
    {
        Character &member = *combatant(combatantIndex);
        member.playedYears = playedYears;

        for (size_t index = 0; index < CharacterConditionCount; ++index)
        {
            float &expire = member.conditionExpireGameMinutes[index];

            if (expire <= 0.0f)
            {
                continue;
            }

            if (!member.conditions.test(index))
            {
                expire = 0.0f;
            }
            else if (m_gameMinutes >= expire)
            {
                member.conditions.reset(index);
                member.conditionStartGameMinutes[index] = 0.0f;
                expire = 0.0f;
            }
        }
    }
}

float Party::gameMinutes() const
{
    return m_gameMinutes;
}

void Party::updateDaysWithoutRest(float gameMinutes)
{
    // A new day dawns at 3 AM.
    constexpr float DawnMinuteOfDay = 3.0f * 60.0f;
    constexpr float MinutesPerDay = 24.0f * 60.0f;
    const int dayIndex = static_cast<int>(std::floor((gameMinutes - DawnMinuteOfDay) / MinutesPerDay));

    if (!m_awakeDayIndex || *m_awakeDayIndex >= dayIndex)
    {
        m_awakeDayIndex = dayIndex;
        return;
    }

    // Like the original timed effects, one time step passes at most one dawn, however many days it skips.
    m_awakeDayIndex = dayIndex;
    ++m_daysWithoutRest;

    if (m_daysWithoutRest <= 1)
    {
        return;
    }

    const bool starving = m_food <= 0;

    if (!starving)
    {
        addFood(-1);
    }

    static thread_local std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<int> percent(0, 99);

    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        Character &member = m_members[memberIndex];
        applyMemberCondition(memberIndex, CharacterCondition::Weak, gameMinutes);

        if (member.conditions.test(static_cast<size_t>(CharacterCondition::Dead))
            || member.conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
            || member.conditions.test(static_cast<size_t>(CharacterCondition::Eradicated)))
        {
            continue;
        }

        if (starving)
        {
            member.health = member.health / (m_daysWithoutRest + 1) + 1;
        }

        if (m_daysWithoutRest > 3)
        {
            clearTemporaryEventBonuses(member);

            if (percent(rng) < 5 * m_daysWithoutRest)
            {
                applyMemberCondition(memberIndex, CharacterCondition::Dead, gameMinutes);
            }

            if (percent(rng) < 10 * m_daysWithoutRest)
            {
                applyMemberCondition(memberIndex, CharacterCondition::Insane, gameMinutes);
            }
        }
    }
}

void Party::restoreActiveMember()
{
    Character *pMember = activeMember();

    if (pMember == nullptr)
    {
        return;
    }

    pMember->health = effectiveMaximumHealth(*pMember);
    pMember->spellPoints = effectiveMaximumSpellPoints(*pMember);
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Unconscious));
    pMember->conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Unconscious)] = 0.0f;
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Dead));
    pMember->conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Dead)] = 0.0f;
}

bool Party::trainLeader(uint32_t maxLevel, uint32_t &newLevel, uint32_t &skillPointsEarned)
{
    newLevel = 0;
    skillPointsEarned = 0;

    if (m_members.empty())
    {
        return false;
    }

    Character &leader = m_members.front();

    if (maxLevel > 0 && leader.level >= maxLevel)
    {
        return false;
    }

    if (leader.experience < rules().experience.experienceForNextLevel(leader.level))
    {
        return false;
    }

    leader.level += 1;
    skillPointsEarned = 5 + leader.level / 10;
    leader.skillPoints += skillPointsEarned;
    GameMechanics::refreshCharacterBaseResources(leader, true, m_pClassMultiplierTable);
    newLevel = leader.level;
    return true;
}

bool Party::trainActiveMember(uint32_t maxLevel, uint32_t &newLevel, uint32_t &skillPointsEarned)
{
    newLevel = 0;
    skillPointsEarned = 0;

    Character *pMember = activeMember();

    if (pMember == nullptr)
    {
        return false;
    }

    if (maxLevel > 0 && pMember->level >= maxLevel)
    {
        return false;
    }

    if (pMember->experience < rules().experience.experienceForNextLevel(pMember->level))
    {
        return false;
    }

    pMember->level += 1;
    skillPointsEarned = 5 + pMember->level / 10;

    if (m_statistics.pStatistics != nullptr)
    {
        m_statistics.pStatistics->recordLevelsGained(statsMember(m_activeMemberIndex), 1);
    }
    pMember->skillPoints += skillPointsEarned;
    GameMechanics::refreshCharacterBaseResources(*pMember, true, m_pClassMultiplierTable);
    newLevel = pMember->level;
    return true;
}

bool Party::canMemberLearnSkill(size_t memberIndex, const std::string &skillName) const
{
    const Character *pMember = member(memberIndex);
    const std::string canonicalSkill = canonicalSkillName(skillName);

    if (pMember == nullptr || canonicalSkill.empty() || m_pClassSkillTable == nullptr || pMember->hasSkill(canonicalSkill))
    {
        return false;
    }

    return m_pClassSkillTable->getEffectiveCap(pMember->className, pMember->raceId, canonicalSkill)
        != SkillMastery::None;
}

bool Party::learnMemberSkill(size_t memberIndex, const std::string &skillName)
{
    if (!canMemberLearnSkill(memberIndex, skillName))
    {
        return false;
    }

    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    CharacterSkill skill = {};
    skill.name = canonicalSkillName(skillName);
    skill.level = 1;
    skill.mastery = SkillMastery::Normal;
    pMember->skills[skill.name] = skill;
    pMember->synchronizeInnateAbilitySpells();
    GameMechanics::refreshCharacterBaseResources(*pMember, false, m_pClassMultiplierTable);
    return true;
}

bool Party::canActiveMemberLearnSkill(const std::string &skillName) const
{
    return canMemberLearnSkill(activeMemberIndex(), skillName);
}

bool Party::learnActiveMemberSkill(const std::string &skillName)
{
    return learnMemberSkill(activeMemberIndex(), skillName);
}

bool Party::canIncreaseActiveMemberSkillLevel(const std::string &skillName) const
{
    const Character *pMember = activeMember();
    const std::string canonicalSkill = canonicalSkillName(skillName);

    if (pMember == nullptr || canonicalSkill.empty())
    {
        return false;
    }

    return rules().skills.canRaiseSkill(*pMember, canonicalSkill);
}

bool Party::increaseActiveMemberSkillLevel(const std::string &skillName)
{
    if (!canIncreaseActiveMemberSkillLevel(skillName))
    {
        return false;
    }

    Character *pMember = activeMember();

    if (pMember == nullptr)
    {
        return false;
    }

    CharacterSkill *pSkill = pMember->findSkill(skillName);

    if (pSkill == nullptr)
    {
        return false;
    }

    const std::string canonicalSkill = canonicalSkillName(skillName);
    const uint32_t cost = rules().skills.skillRaiseCost(*pMember, canonicalSkill);
    pSkill->level += 1;
    uint32_t &points = isTechnologySkill(skillName) ? pMember->techPoints : pMember->skillPoints;
    points -= cost;
    m_lastStatus = rules().skills.afterSkillRaised(*pMember, canonicalSkill, m_pClassSkillTable);

    GameMechanics::refreshCharacterBaseResources(*pMember, false, m_pClassMultiplierTable);
    return true;
}

std::optional<int> Party::activeMemberSkillResetCost() const
{
    const Character *pMember = activeMember();
    return pMember != nullptr ? rules().skills.skillResetCost(*pMember) : std::nullopt;
}

bool Party::resetActiveMemberSkills()
{
    Character *pMember = activeMember();
    const std::optional<int> cost = activeMemberSkillResetCost();

    if (pMember == nullptr || !cost)
    {
        m_lastStatus = Engine::tr("No skills can be reset.");
        return false;
    }

    if (m_gold < *cost)
    {
        m_lastStatus = Engine::tr("Not enough gold.");
        return false;
    }

    if (!rules().skills.resetSkills(*pMember))
    {
        m_lastStatus = Engine::tr("No skills can be reset.");
        return false;
    }

    addGold(-*cost, GoldReason::Guild);
    GameMechanics::refreshCharacterBaseResources(*pMember, false, m_pClassMultiplierTable);
    m_lastStatus = Engine::tr("{name}'s skills were reset: {points} skill points.",
        {{"name", pMember->name}, {"points", pMember->skillPoints}});
    return true;
}

int Party::depositGoldToBank(int amount)
{
    const int transferableGold = std::clamp(amount, 0, m_gold);

    if (transferableGold <= 0)
    {
        return 0;
    }

    addGold(-transferableGold, GoldReason::Bank);
    m_bankGold += transferableGold;
    return transferableGold;
}

int Party::withdrawBankGold(int amount)
{
    const int transferableGold = std::clamp(amount, 0, m_bankGold);

    if (transferableGold <= 0)
    {
        return 0;
    }

    m_bankGold -= transferableGold;
    addGold(transferableGold, GoldReason::Bank);
    return transferableGold;
}

int Party::depositAllGoldToBank()
{
    return depositGoldToBank(m_gold);
}

int Party::withdrawAllBankGold()
{
    return withdrawBankGold(m_bankGold);
}

bool Party::isFull() const
{
    return m_members.size() >= MaxMembers;
}

bool Party::recruitRosterMember(const RosterEntry &rosterEntry)
{
    if (isFull())
    {
        return false;
    }

    m_members.push_back(buildCharacterFromRosterEntry(rosterEntry, m_pClassMultiplierTable));
    initializePortraitRuntimeState(m_members.back());
    grantRosterInventoryToCharacter(
        m_members.back(),
        rosterEntry,
        m_pItemTable,
        m_pStandardItemEnchantTable,
        m_pSpecialItemEnchantTable);
    rules().experience.prepareRosterCharacter(m_members.back());
    normalizeFormationCells();

    m_lastStatus = "party member recruited";
    return true;
}

bool Party::recruitCharacter(const Character &character)
{
    if (isFull())
    {
        return false;
    }

    m_members.push_back(character);
    applyCharacterIdentityFromDollTable(m_members.back(), m_pCharacterDollTable);
    m_members.back().className = canonicalClassName(
        m_members.back().className.empty() ? m_members.back().role : m_members.back().className);
    m_members.back().role = normalizeRoleName(m_members.back().className);

    if (m_members.back().skills.empty() && m_pClassSkillTable != nullptr)
    {
        applyDefaultStartingSkills(m_members.back());
    }

    m_members.back().synchronizeInnateAbilitySpells();

    GameMechanics::refreshCharacterBaseResources(m_members.back(), true, m_pClassMultiplierTable);
    initializePortraitRuntimeState(m_members.back());
    normalizeFormationCells();
    m_lastStatus = "party member recruited";
    return true;
}

bool Party::addAdventurersInnMember(const RosterEntry &rosterEntry, uint32_t portraitPictureId)
{
    Character character = buildCharacterFromRosterEntry(rosterEntry, m_pClassMultiplierTable);
    grantRosterInventoryToCharacter(
        character,
        rosterEntry,
        m_pItemTable,
        m_pStandardItemEnchantTable,
        m_pSpecialItemEnchantTable);
    rules().experience.prepareRosterCharacter(character);
    const uint32_t resolvedPortraitPictureId = resolveAdventurersInnPortraitPictureId(
        character,
        portraitPictureId,
        m_pCharacterDollTable);
    return addAdventurersInnMember(character, resolvedPortraitPictureId);
}

bool Party::addAdventurersInnMember(const Character &character, uint32_t portraitPictureId)
{
    AdventurersInnMember member = {};
    member.character = character;
    applyCharacterIdentityFromDollTable(member.character, m_pCharacterDollTable);
    member.character.className = canonicalClassName(
        member.character.className.empty() ? member.character.role : member.character.className);
    member.character.role = normalizeRoleName(member.character.className);

    if (member.character.skills.empty() && m_pClassSkillTable != nullptr)
    {
        applyDefaultStartingSkills(member.character);
    }

    member.character.synchronizeInnateAbilitySpells();

    initializePortraitRuntimeState(member.character);
    member.portraitPictureId = resolveAdventurersInnPortraitPictureId(
        member.character,
        portraitPictureId,
        m_pCharacterDollTable);
    m_adventurersInnMembers.push_back(std::move(member));
    m_lastStatus = "adventurer moved to inn";
    return true;
}

bool Party::hireAdventurersInnMember(size_t innIndex)
{
    if (isFull() || innIndex >= m_adventurersInnMembers.size())
    {
        return false;
    }

    m_members.push_back(m_adventurersInnMembers[innIndex].character);
    applyCharacterIdentityFromDollTable(m_members.back(), m_pCharacterDollTable);
    m_adventurersInnMembers.erase(m_adventurersInnMembers.begin() + innIndex);
    normalizeFormationCells();
    m_lastStatus = "adventurer hired from inn";
    return true;
}

bool Party::dismissMemberToAdventurersInn(size_t memberIndex)
{
    if (memberIndex == 0 || memberIndex >= m_members.size())
    {
        return false;
    }

    const Character dismissedMember = m_members[memberIndex];
    const uint32_t portraitPictureId = resolveAdventurersInnPortraitPictureId(
        dismissedMember,
        dismissedMember.portraitPictureId,
        m_pCharacterDollTable);

    if (!addAdventurersInnMember(dismissedMember, portraitPictureId))
    {
        return false;
    }

    rules().spells.memberLeaving(*this, memberIndex);
    m_members.erase(m_members.begin() + memberIndex);

    if (memberIndex < m_memberFormationCells.size())
    {
        m_memberFormationCells.erase(m_memberFormationCells.begin() + std::ptrdiff_t(memberIndex));
    }

    for (size_t index = memberIndex; index + 1 < m_characterBuffs.size(); ++index)
    {
        m_characterBuffs[index] = m_characterBuffs[index + 1];
    }

    m_characterBuffs.back() = {};

    for (PartyBuffState &buff : m_partyBuffs)
    {
        buff.casterMemberIndex = remapCasterMemberIndexAfterDismiss(buff.casterMemberIndex, memberIndex);
    }

    for (auto &memberBuffs : m_characterBuffs)
    {
        for (CharacterBuffState &buff : memberBuffs)
        {
            buff.casterMemberIndex = remapCasterMemberIndexAfterDismiss(buff.casterMemberIndex, memberIndex);
        }
    }

    m_pendingAudioRequests.erase(
        std::remove_if(
            m_pendingAudioRequests.begin(),
            m_pendingAudioRequests.end(),
            [memberIndex](PendingAudioRequest &request)
            {
                if (request.kind != PendingAudioRequest::Kind::Speech)
                {
                    return false;
                }

                if (request.memberIndex == memberIndex)
                {
                    return true;
                }

                if (request.memberIndex > memberIndex)
                {
                    request.memberIndex -= 1;
                }

                return false;
            }),
        m_pendingAudioRequests.end());

    if (m_members.empty())
    {
        m_activeMemberIndex = 0;
    }
    else if (m_activeMemberIndex > memberIndex)
    {
        m_activeMemberIndex -= 1;
    }
    else if (m_activeMemberIndex >= m_members.size())
    {
        m_activeMemberIndex = m_members.size() - 1;
    }

    normalizeFormationCells();
    rebuildMagicalBonusesFromBuffs();
    m_lastStatus = "party member dismissed";
    return true;
}

bool Party::replaceMemberWithRosterEntry(size_t memberIndex, const RosterEntry &rosterEntry)
{
    if (memberIndex >= m_members.size())
    {
        return false;
    }

    m_members[memberIndex] = buildCharacterFromRosterEntry(rosterEntry, m_pClassMultiplierTable);
    applyCharacterIdentityFromDollTable(m_members[memberIndex], m_pCharacterDollTable);
    initializePortraitRuntimeState(m_members[memberIndex]);
    grantRosterInventoryToCharacter(
        m_members[memberIndex],
        rosterEntry,
        m_pItemTable,
        m_pStandardItemEnchantTable,
        m_pSpecialItemEnchantTable);
    rules().experience.prepareRosterCharacter(m_members[memberIndex]);

    rebuildMagicalBonusesFromBuffs();
    m_lastStatus = "party member replaced from roster";
    return true;
}

bool Party::hasRosterMember(uint32_t rosterId) const
{
    if (rosterId == 0)
    {
        return false;
    }

    for (const Character &member : m_members)
    {
        if (member.rosterId == rosterId)
        {
            return true;
        }
    }

    for (const AdventurersInnMember &member : m_adventurersInnMembers)
    {
        if (member.character.rosterId == rosterId)
        {
            return true;
        }
    }

    return false;
}

bool Party::hasQuestBit(uint32_t questBitId) const
{
    return questBitId != 0 && m_questBits.contains(questBitId);
}

void Party::setQuestBit(uint32_t questBitId, bool value)
{
    if (questBitId == 0)
    {
        return;
    }

    if (value)
    {
        const bool inserted = m_questBits.insert(questBitId).second;
        if (inserted)
        {
            ++m_dialogueEligibilityRevision;
            GAMEPLAY_DEBUG_TRACE("qbit_set id=" + std::to_string(questBitId));
        }
    }
    else
    {
        const size_t erased = m_questBits.erase(questBitId);
        if (erased != 0)
        {
            ++m_dialogueEligibilityRevision;
            GAMEPLAY_DEBUG_TRACE("qbit_cleared id=" + std::to_string(questBitId));
        }
    }
}

bool Party::hasAutonote(uint32_t autonoteId) const
{
    return autonoteId != 0 && m_autonotes.contains(autonoteId);
}

void Party::setAutonote(uint32_t autonoteId, bool value)
{
    if (autonoteId == 0)
    {
        return;
    }

    if (value)
    {
        m_autonotes.insert(autonoteId);
    }
    else
    {
        m_autonotes.erase(autonoteId);
    }
}

const std::unordered_map<uint32_t, int32_t> &Party::historyEventTimes(uint32_t continentId) const
{
    static const std::unordered_map<uint32_t, int32_t> EmptyHistory;
    const auto continentIt = m_historyEventTimesByContinent.find(continentId);
    return continentIt != m_historyEventTimesByContinent.end() ? continentIt->second : EmptyHistory;
}

void Party::recordHistoryEvent(uint32_t continentId, uint32_t historyId, int32_t gameMinutes)
{
    if (historyId != 0)
    {
        m_historyEventTimesByContinent[continentId].try_emplace(historyId, gameMinutes);
    }
}

void Party::clearHistoryEvent(uint32_t continentId, uint32_t historyId)
{
    const auto continentIt = m_historyEventTimesByContinent.find(continentId);

    if (continentIt != m_historyEventTimesByContinent.end())
    {
        continentIt->second.erase(historyId);
    }
}

const std::vector<JournalMapNote> &Party::journalMapNotes() const
{
    return m_journalMapNotes;
}

const JournalMapNote *Party::findJournalMapNote(const std::string &mapFileName, uint32_t noteId) const
{
    for (const JournalMapNote &note : m_journalMapNotes)
    {
        if (note.id == noteId && note.mapFileName == mapFileName)
        {
            return &note;
        }
    }

    return nullptr;
}

void Party::setJournalMapNote(const JournalMapNote &note)
{
    for (JournalMapNote &existing : m_journalMapNotes)
    {
        if (existing.id == note.id && existing.mapFileName == note.mapFileName)
        {
            existing = note;
            return;
        }
    }

    m_journalMapNotes.push_back(note);
}

bool Party::removeJournalMapNote(const std::string &mapFileName, uint32_t noteId)
{
    const auto note = std::find_if(m_journalMapNotes.begin(), m_journalMapNotes.end(),
        [&mapFileName, noteId](const JournalMapNote &existing)
        {
            return existing.id == noteId && existing.mapFileName == mapFileName;
        });

    if (note == m_journalMapNotes.end())
    {
        return false;
    }

    m_journalMapNotes.erase(note);
    return true;
}

uint64_t Party::dialogueEligibilityRevision() const
{
    return m_dialogueEligibilityRevision;
}

void Party::applyGlobalNpcStateTo(EventRuntimeState &runtimeState) const
{
    // Where followers do not count (MM9) the map's events, dialogue, HUD and gold see none; the party keeps its own.
    const std::span<const HiredNpcFollower> followers = activeHiredNpcFollowers();
    std::unordered_set<uint32_t> partyFollowerIds;
    partyFollowerIds.reserve(followers.size());

    for (const HiredNpcFollower &follower : followers)
    {
        if (follower.npcId != 0)
        {
            partyFollowerIds.insert(follower.npcId);
        }
    }

    const auto staleFollowerIt = std::remove_if(
        runtimeState.hiredNpcFollowers.begin(),
        runtimeState.hiredNpcFollowers.end(),
        [this, &partyFollowerIds](const HiredNpcFollower &follower)
        {
            return !m_npcFollowersActive || (follower.npcId != 0 && !partyFollowerIds.contains(follower.npcId));
        });

    runtimeState.hiredNpcFollowers.erase(staleFollowerIt, runtimeState.hiredNpcFollowers.end());

    for (const auto &[npcId, topicOverrides] : m_npcTopicOverrides)
    {
        for (const auto &[topicSlotIndex, topicId] : topicOverrides)
        {
            runtimeState.npcTopicOverrides[npcId][topicSlotIndex] = topicId;
        }
    }

    for (const auto &[groupId, newsId] : m_npcGroupNews)
    {
        runtimeState.npcGroupNews[groupId] = newsId;
    }

    for (const auto &[npcId, greetingId] : m_npcGreetingOverrides)
    {
        runtimeState.npcGreetingOverrides[npcId] = greetingId;
    }

    for (const auto &[npcId, displayCount] : m_npcGreetingDisplayCounts)
    {
        runtimeState.npcGreetingDisplayCounts[npcId] = displayCount;
    }

    for (const auto &[npcId, houseId] : m_npcHouseOverrides)
    {
        runtimeState.npcHouseOverrides[npcId] = houseId;
    }

    for (const auto &[npcId, itemId] : m_npcItemOverrides)
    {
        runtimeState.npcItemOverrides[npcId] = itemId;
    }

    // The party's set replaces the map's: a map's saved state can keep an NPC unavailable after the party let them go
    // elsewhere (Sir Charles Quixote, hidden from his residence after the Crusader promotion in Wromthrax's cave).
    runtimeState.unavailableNpcIds = m_unavailableNpcIds;

    for (const HiredNpcFollower &follower : followers)
    {
        const auto existingFollowerIt = std::find_if(
            runtimeState.hiredNpcFollowers.begin(),
            runtimeState.hiredNpcFollowers.end(),
            [&follower](const HiredNpcFollower &runtimeFollower)
            {
                return runtimeFollower.npcId == follower.npcId;
            });

        if (existingFollowerIt == runtimeState.hiredNpcFollowers.end())
        {
            runtimeState.hiredNpcFollowers.push_back(follower);
        }
        else
        {
            *existingFollowerIt = follower;
        }

        if (follower.npcId != 0)
        {
            runtimeState.unavailableNpcIds.insert(follower.npcId);

            if (!follower.name.empty())
            {
                runtimeState.npcNameOverrides[follower.npcId] = follower.name;
            }

            if (follower.pictureId != 0)
            {
                runtimeState.npcPictureOverrides[follower.npcId] = follower.pictureId;
            }

            if (follower.professionId != 0)
            {
                runtimeState.npcProfessionOverrides[follower.npcId] = follower.professionId;
            }
        }
    }
}

void Party::setNpcTopicOverride(uint32_t npcId, uint32_t topicSlotIndex, uint32_t topicId)
{
    m_npcTopicOverrides[npcId][topicSlotIndex] = topicId;
}

void Party::setNpcGroupNews(uint32_t groupId, uint32_t newsId)
{
    m_npcGroupNews[groupId] = newsId;
}

void Party::setNpcGreetingOverride(uint32_t npcId, uint32_t greetingId)
{
    m_npcGreetingOverrides[npcId] = greetingId;
    m_npcGreetingDisplayCounts[npcId] = 0;
}

void Party::setNpcHouseOverride(uint32_t npcId, uint32_t houseId)
{
    m_npcHouseOverrides[npcId] = houseId;
}

void Party::clearNpcHouseOverride(uint32_t npcId)
{
    m_npcHouseOverrides.erase(npcId);
}

void Party::setNpcItemOverride(uint32_t npcId, uint32_t itemId)
{
    m_npcItemOverrides[npcId] = itemId;
}

void Party::setNpcUnavailable(uint32_t npcId, bool unavailable)
{
    if (unavailable)
    {
        m_unavailableNpcIds.insert(npcId);
    }
    else
    {
        m_unavailableNpcIds.erase(npcId);
    }
}

void Party::addHiredNpcFollower(const HiredNpcFollower &follower)
{
    if (follower.npcId == 0)
    {
        return;
    }

    const auto followerIt = std::find_if(
        m_hiredNpcFollowers.begin(),
        m_hiredNpcFollowers.end(),
        [&follower](const HiredNpcFollower &existingFollower)
        {
            return existingFollower.npcId == follower.npcId;
        });

    if (followerIt == m_hiredNpcFollowers.end())
    {
        m_hiredNpcFollowers.push_back(follower);
        GAMEPLAY_DEBUG_TRACE(
            "hireling_hired npc_id=" + std::to_string(follower.npcId)
            + " profession_id=" + std::to_string(follower.professionId)
            + " weekly_cost=" + std::to_string(follower.weeklyCost));
    }
    else
    {
        *followerIt = follower;
    }

    m_unavailableNpcIds.insert(follower.npcId);
    rebuildMagicalBonusesFromBuffs();
}

void Party::removeHiredNpcFollower(uint32_t npcId)
{
    const auto followerIt = std::remove_if(
        m_hiredNpcFollowers.begin(),
        m_hiredNpcFollowers.end(),
        [npcId](const HiredNpcFollower &follower)
        {
            return follower.npcId == npcId;
        });

    if (followerIt != m_hiredNpcFollowers.end())
    {
        for (auto iterator = followerIt; iterator != m_hiredNpcFollowers.end(); ++iterator)
        {
            GAMEPLAY_DEBUG_TRACE(
                "hireling_left npc_id=" + std::to_string(iterator->npcId)
                + " profession_id=" + std::to_string(iterator->professionId)
                + " weekly_cost=" + std::to_string(iterator->weeklyCost));
        }

        m_hiredNpcFollowers.erase(followerIt, m_hiredNpcFollowers.end());
        rebuildMagicalBonusesFromBuffs();
    }
}

void Party::setHiredNpcFollowerAbilityUsedDay(uint32_t npcId, uint32_t day)
{
    for (HiredNpcFollower &follower : m_hiredNpcFollowers)
    {
        if (follower.npcId == npcId)
        {
            follower.abilityUsedDay = day;
            return;
        }
    }
}

void Party::setNpcFollowersActive(bool active)
{
    if (m_npcFollowersActive != active)
    {
        m_npcFollowersActive = active;
        rebuildMagicalBonusesFromBuffs();
    }
}

bool Party::npcFollowersActive() const
{
    return m_npcFollowersActive;
}

std::span<const HiredNpcFollower> Party::activeHiredNpcFollowers() const
{
    return m_npcFollowersActive ? std::span<const HiredNpcFollower>(m_hiredNpcFollowers)
                                : std::span<const HiredNpcFollower>();
}

const std::vector<Mm9PartyHireling> &Party::hirelings() const
{
    return m_mm9Hirelings;
}

const Mm9PartyHireling *Party::findHireling(uint32_t rudeId) const
{
    for (const Mm9PartyHireling &hireling : m_mm9Hirelings)
    {
        if (hireling.rudeId == rudeId)
        {
            return &hireling;
        }
    }

    return nullptr;
}

Mm9PartyHireling *Party::findHireling(uint32_t rudeId)
{
    for (Mm9PartyHireling &hireling : m_mm9Hirelings)
    {
        if (hireling.rudeId == rudeId)
        {
            return &hireling;
        }
    }

    return nullptr;
}

size_t Party::paidHirelingCount() const
{
    return size_t(std::count_if(m_mm9Hirelings.begin(), m_mm9Hirelings.end(),
        [](const Mm9PartyHireling &hireling)
        {
            return hireling.kind == Mm9HirelingKind::Paid;
        }));
}

bool Party::canAddHireling(const Mm9Hireling &row) const
{
    return row.rudeId != 0 && findHireling(row.rudeId) == nullptr && m_mm9Hirelings.size() < MaxMm9Hirelings
        && (row.kind != Mm9HirelingKind::Paid || paidHirelingCount() < MaxPaidMm9Hirelings);
}

bool Party::addHireling(const Mm9Hireling &row)
{
    if (!canAddHireling(row))
    {
        return false;
    }

    Mm9PartyHireling hireling = {};
    hireling.rudeId = row.rudeId;
    hireling.kind = row.kind;
    Character &character = hireling.character;
    character.name = row.name;
    character.portraitTextureName = row.portrait;
    character.level = row.level;
    character.maxHealth = row.hitPoints;
    character.health = row.hitPoints;
    character.armorClassModifier = row.armorClass;
    character.baseResistances = row.resistances;
    character.might = Mm9HirelingPrimaryStat;
    character.intellect = Mm9HirelingPrimaryStat;
    character.personality = Mm9HirelingPrimaryStat;
    character.endurance = Mm9HirelingPrimaryStat;
    character.speed = Mm9HirelingPrimaryStat;
    character.accuracy = Mm9HirelingPrimaryStat;
    character.luck = Mm9HirelingPrimaryStat;
    hireling.hireDay = uint32_t(std::max(0.0f, m_gameMinutes) / (24.0f * 60.0f));
    hireling.nextWageGameMinutes =
        row.kind == Mm9HirelingKind::Paid ? m_gameMinutes + Mm9HirelingWagePeriodGameMinutes : 0.0f;
    m_mm9Hirelings.push_back(std::move(hireling));
    normalizeFormationCells();
    rebuildMagicalBonusesFromBuffs();
    return true;
}

bool Party::removeHireling(uint32_t rudeId)
{
    const auto found = std::find_if(m_mm9Hirelings.begin(), m_mm9Hirelings.end(),
        [rudeId](const Mm9PartyHireling &hireling)
        {
            return hireling.rudeId == rudeId;
        });

    if (found == m_mm9Hirelings.end())
    {
        return false;
    }

    const size_t removedIndex = size_t(found - m_mm9Hirelings.begin());
    m_mm9Hirelings.erase(found);

    if (m_activeHirelingIndex && *m_activeHirelingIndex == removedIndex)
    {
        m_activeHirelingIndex.reset();
    }
    else if (m_activeHirelingIndex && *m_activeHirelingIndex > removedIndex)
    {
        --*m_activeHirelingIndex;
    }

    // Its passives (skill bonuses) leave with it.
    rebuildMagicalBonusesFromBuffs();
    return true;
}

bool Party::addHirelingByRudeId(uint32_t rudeId)
{
    const Mm9Hireling *pRow = m_pMm9HirelingTable != nullptr ? m_pMm9HirelingTable->find(rudeId) : nullptr;
    return pRow != nullptr && addHireling(*pRow);
}

void Party::setMm9HirelingTable(const Mm9HirelingTable *pTable)
{
    m_pMm9HirelingTable = pTable;
    rebuildMagicalBonusesFromBuffs();
}

const Mm9HirelingTable *Party::mm9HirelingTable() const
{
    return m_pMm9HirelingTable;
}

Mm9HirelingPassives Party::mm9HirelingPassives() const
{
    if (m_pMm9HirelingTable == nullptr || m_mm9Hirelings.empty())
    {
        return {};
    }

    return mm9PartyHirelingPassives(*this, *m_pMm9HirelingTable);
}

size_t Party::combatantCount() const
{
    return m_members.size() + m_mm9Hirelings.size();
}

const Character *Party::combatant(size_t combatantIndex) const
{
    if (combatantIndex < m_members.size())
    {
        return &m_members[combatantIndex];
    }

    const size_t hirelingIndex = combatantIndex - m_members.size();
    return hirelingIndex < m_mm9Hirelings.size() ? &m_mm9Hirelings[hirelingIndex].character : nullptr;
}

Character *Party::combatant(size_t combatantIndex)
{
    return const_cast<Character *>(std::as_const(*this).combatant(combatantIndex));
}

bool Party::isHirelingCombatant(size_t combatantIndex) const
{
    return combatantIndex >= m_members.size() && combatantIndex < combatantCount();
}

const Mm9PartyHireling *Party::hirelingCombatant(size_t combatantIndex) const
{
    return isHirelingCombatant(combatantIndex) ? &m_mm9Hirelings[combatantIndex - m_members.size()] : nullptr;
}

std::array<CharacterBuffState, CharacterBuffCount> *Party::combatantBuffs(size_t combatantIndex)
{
    return const_cast<std::array<CharacterBuffState, CharacterBuffCount> *>(
        std::as_const(*this).combatantBuffs(combatantIndex));
}

const std::array<CharacterBuffState, CharacterBuffCount> *Party::combatantBuffs(size_t combatantIndex) const
{
    if (combatantIndex < m_members.size())
    {
        return combatantIndex < m_characterBuffs.size() ? &m_characterBuffs[combatantIndex] : nullptr;
    }

    const Mm9PartyHireling *pHireling = hirelingCombatant(combatantIndex);
    return pHireling != nullptr ? &pHireling->buffs : nullptr;
}

size_t Party::activeCombatantIndex() const
{
    if (m_activeHirelingIndex && *m_activeHirelingIndex < m_mm9Hirelings.size())
    {
        return m_members.size() + *m_activeHirelingIndex;
    }

    return activeMemberIndex();
}

const Mm9PartyHireling *Party::activeHireling() const
{
    return m_activeHirelingIndex && *m_activeHirelingIndex < m_mm9Hirelings.size()
        ? &m_mm9Hirelings[*m_activeHirelingIndex]
        : nullptr;
}

bool Party::setActiveCombatantIndex(size_t combatantIndex)
{
    if (combatantIndex < m_members.size())
    {
        return setActiveMemberIndex(combatantIndex);
    }

    if (!isHirelingCombatant(combatantIndex))
    {
        return false;
    }

    m_activeHirelingIndex = combatantIndex - m_members.size();
    return true;
}

bool Party::canSelectCombatantInGameplay(size_t combatantIndex) const
{
    const Character *pCombatant = combatant(combatantIndex);
    return pCombatant != nullptr && GameMechanics::canSelectInGameplay(*pCombatant);
}

float Party::hirelingRecoverySeconds(const Character &hireling, float rowRecoverySeconds)
{
    // MM9 adds its haste/slow modifier to the row's recovery (MM9_HIRELINGS.md 9.2); here the members' haste ticks,
    // down to a blow's minimum (GameMechanics' 30 ticks).
    constexpr int MinimumRecoveryTicks = 30;
    return std::max(ticksToRecoverySeconds(MinimumRecoveryTicks),
        rowRecoverySeconds - ticksToRecoverySeconds(hireling.attackRecoveryReductionTicks));
}

void Party::setFormationTargetingActive(bool active)
{
    m_formationTargetingActive = active;
}

bool Party::formationTargetingActive() const
{
    return m_formationTargetingActive;
}

int32_t Party::formationCell(size_t combatantIndex) const
{
    if (combatantIndex < m_members.size())
    {
        return combatantIndex < m_memberFormationCells.size() ? m_memberFormationCells[combatantIndex] : -1;
    }

    const Mm9PartyHireling *pHireling = hirelingCombatant(combatantIndex);
    return pHireling != nullptr ? pHireling->formationCell : -1;
}

bool Party::setFormationCell(size_t combatantIndex, int32_t cell)
{
    if (combatantIndex >= combatantCount() || cell < 0 || cell >= Mm9FormationCellCount)
    {
        return false;
    }

    for (size_t otherIndex = 0; otherIndex < combatantCount(); ++otherIndex)
    {
        if (otherIndex != combatantIndex && formationCell(otherIndex) == cell)
        {
            return false;
        }
    }

    if (combatantIndex < m_members.size())
    {
        m_memberFormationCells.resize(m_members.size(), -1);
        m_memberFormationCells[combatantIndex] = cell;
    }
    else
    {
        m_mm9Hirelings[combatantIndex - m_members.size()].formationCell = cell;
    }

    return true;
}

std::vector<int32_t> Party::formationCells() const
{
    std::vector<int32_t> cells;
    cells.reserve(combatantCount());

    for (size_t combatantIndex = 0; combatantIndex < combatantCount(); ++combatantIndex)
    {
        cells.push_back(formationCell(combatantIndex));
    }

    return cells;
}

bool Party::setFormationCells(const std::vector<int32_t> &cells)
{
    if (cells.size() != combatantCount())
    {
        return false;
    }

    std::array<bool, Mm9FormationCellCount> taken = {};

    for (const int32_t cell : cells)
    {
        if (cell < 0 || cell >= Mm9FormationCellCount || taken[size_t(cell)])
        {
            return false;
        }

        taken[size_t(cell)] = true;
    }

    m_memberFormationCells.assign(cells.begin(), cells.begin() + std::ptrdiff_t(m_members.size()));

    for (size_t hireling = 0; hireling < m_mm9Hirelings.size(); ++hireling)
    {
        m_mm9Hirelings[hireling].formationCell = cells[m_members.size() + hireling];
    }

    return true;
}

void Party::normalizeFormationCells()
{
    m_memberFormationCells.resize(m_members.size(), -1);
    std::array<bool, Mm9FormationCellCount> taken = {};
    std::vector<int32_t *> cells;
    cells.reserve(combatantCount());

    for (int32_t &cell : m_memberFormationCells)
    {
        cells.push_back(&cell);
    }

    for (Mm9PartyHireling &hireling : m_mm9Hirelings)
    {
        cells.push_back(&hireling.formationCell);
    }

    // Cells already held stay; a duplicate or an invalid cell is given up and refilled below.
    for (int32_t *pCell : cells)
    {
        if (*pCell >= 0 && *pCell < Mm9FormationCellCount && !taken[size_t(*pCell)])
        {
            taken[size_t(*pCell)] = true;
        }
        else
        {
            *pCell = -1;
        }
    }

    // MM9's default: the lowest free cell, members first, then the hirelings (section 10.3).
    for (int32_t *pCell : cells)
    {
        if (*pCell >= 0)
        {
            continue;
        }

        for (int32_t cell = 0; cell < Mm9FormationCellCount; ++cell)
        {
            if (!taken[size_t(cell)])
            {
                taken[size_t(cell)] = true;
                *pCell = cell;
                break;
            }
        }
    }
}

std::optional<size_t> Party::chooseFormationAttackTarget(uint32_t selectionSeed) const
{
    // MM9 (object@0x10054ea0, MM9_HIRELINGS.md 9.3 and 10.2): a d10 picks the rank, 1 the rear, 2-3 the middle,
    // 4-10 the front; a d3 a cell of it, rolled again while it is empty; a rank without anyone, or a pick that cannot
    // be hit, starts the whole choice again. Nobody is chosen once every member is down, hirelings standing or not.
    const bool anyMemberStanding = std::any_of(m_members.begin(), m_members.end(),
        [](const Character &member)
        {
            return isValidMonsterAttackTarget(member);
        });

    if (!anyMemberStanding)
    {
        return std::nullopt;
    }

    std::array<std::optional<size_t>, Mm9FormationCellCount> occupants = {};

    for (size_t combatantIndex = 0; combatantIndex < combatantCount(); ++combatantIndex)
    {
        const int32_t cell = formationCell(combatantIndex);

        if (cell >= 0 && cell < Mm9FormationCellCount)
        {
            occupants[size_t(cell)] = combatantIndex;
        }
    }

    std::mt19937 rng(selectionSeed);
    std::uniform_int_distribution<int> rankRoll(1, 10);
    std::uniform_int_distribution<int> cellRoll(0, Mm9FormationRankSize - 1);
    // A generous bound on the retries: a standing member is found long before (the odds of the rarest rank are 10 %).
    constexpr int MaximumChoices = 256;

    for (int choice = 0; choice < MaximumChoices; ++choice)
    {
        const int rankDie = rankRoll(rng);
        const int rank = rankDie == 1 ? 2 : rankDie <= 3 ? 1 : 0;
        const size_t firstCell = size_t(rank * Mm9FormationRankSize);
        const bool rankOccupied = occupants[firstCell] || occupants[firstCell + 1] || occupants[firstCell + 2];

        if (!rankOccupied)
        {
            continue;
        }

        std::optional<size_t> picked;

        while (!picked)
        {
            picked = occupants[firstCell + size_t(cellRoll(rng))];
        }

        const Character *pPicked = combatant(*picked);

        if (pPicked != nullptr && isValidMonsterAttackTarget(*pPicked))
        {
            return picked;
        }
    }

    return std::nullopt;
}

bool Party::hasAward(uint32_t awardId) const
{
    if (awardId == 0)
    {
        return false;
    }

    for (const Character &member : m_members)
    {
        if (member.awards.contains(awardId))
        {
            return true;
        }
    }

    return false;
}

bool Party::hasAward(size_t memberIndex, uint32_t awardId) const
{
    const Character *pMember = member(memberIndex);
    return pMember != nullptr && awardId != 0 && pMember->awards.contains(awardId);
}

void Party::addAward(uint32_t awardId)
{
    if (awardId == 0)
    {
        return;
    }

    bool acquired = false;
    for (Character &member : m_members)
    {
        acquired = member.awards.insert(awardId).second || acquired;
    }

    if (acquired)
    {
        GAMEPLAY_DEBUG_TRACE("award_acquired id=" + std::to_string(awardId) + " scope=party");
    }
}

void Party::addAward(size_t memberIndex, uint32_t awardId)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || awardId == 0)
    {
        return;
    }

    const bool acquired = pMember->awards.insert(awardId).second;
    if (acquired)
    {
        GAMEPLAY_DEBUG_TRACE(
            "award_acquired id=" + std::to_string(awardId)
            + " member_index=" + std::to_string(memberIndex));
    }
}

void Party::removeAward(uint32_t awardId)
{
    if (awardId == 0)
    {
        return;
    }

    bool cleared = false;
    for (Character &member : m_members)
    {
        cleared = member.awards.erase(awardId) != 0 || cleared;
    }

    if (cleared)
    {
        GAMEPLAY_DEBUG_TRACE("award_cleared id=" + std::to_string(awardId) + " scope=party");
    }
}

void Party::removeAward(size_t memberIndex, uint32_t awardId)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || awardId == 0)
    {
        return;
    }

    const bool cleared = pMember->awards.erase(awardId) != 0;
    if (cleared)
    {
        GAMEPLAY_DEBUG_TRACE(
            "award_cleared id=" + std::to_string(awardId)
            + " member_index=" + std::to_string(memberIndex));
    }
}

int Party::inventoryItemCount(uint32_t objectDescriptionId, std::optional<size_t> memberIndex) const
{
    if (objectDescriptionId == 0)
    {
        return 0;
    }

    int totalCount = 0;

    auto countMemberItems = [&](const Character &member)
    {
        static constexpr EquipmentSlot EquipmentSlots[] = {
            EquipmentSlot::OffHand,
            EquipmentSlot::MainHand,
            EquipmentSlot::Bow,
            EquipmentSlot::Armor,
            EquipmentSlot::Helm,
            EquipmentSlot::Belt,
            EquipmentSlot::Cloak,
            EquipmentSlot::Gauntlets,
            EquipmentSlot::Boots,
            EquipmentSlot::Amulet,
            EquipmentSlot::Ring1,
            EquipmentSlot::Ring2,
            EquipmentSlot::Ring3,
            EquipmentSlot::Ring4,
            EquipmentSlot::Ring5,
            EquipmentSlot::Ring6,
        };

        for (const InventoryItem &item : member.inventory)
        {
            if (item.objectDescriptionId == objectDescriptionId)
            {
                totalCount += static_cast<int>(item.quantity);
            }
        }

        // MAW's other bags count too: the inventory shows all four, unlike MAW's one bag at a time.
        for (const auto &[bag, items] : member.rulesetState.storedBags)
        {
            for (const InventoryItem &item : items)
            {
                if (item.objectDescriptionId == objectDescriptionId)
                {
                    totalCount += static_cast<int>(item.quantity);
                }
            }
        }

        for (EquipmentSlot slot : EquipmentSlots)
        {
            if (::OpenYAMM::Game::equippedItemId(member.equipment, slot) == objectDescriptionId)
            {
                totalCount += 1;
            }
        }
    };

    if (memberIndex)
    {
        const Character *pMember = member(*memberIndex);

        if (pMember != nullptr)
        {
            countMemberItems(*pMember);
        }

        return totalCount;
    }

    for (const Character &member : m_members)
    {
        countMemberItems(member);
    }

    return totalCount;
}

void Party::recordEverOwnedItem(uint32_t objectDescriptionId)
{
    if (objectDescriptionId == 0)
    {
        return;
    }

    const bool firstTime = m_everOwnedItemIds.insert(objectDescriptionId).second;

    if (firstTime && m_statistics.pStatistics != nullptr && m_pItemTable != nullptr)
    {
        const ItemDefinition *pItem = m_pItemTable->get(objectDescriptionId);

        if (pItem != nullptr && (pItem->rarity == ItemRarity::Artifact || pItem->rarity == ItemRarity::Relic))
        {
            m_statistics.pStatistics->recordArtifactFound(objectDescriptionId, pItem->name);
        }
    }
}

bool Party::hasEverOwnedItem(uint32_t objectDescriptionId) const
{
    return objectDescriptionId != 0 && m_everOwnedItemIds.contains(objectDescriptionId);
}

void Party::recordChosenMm9RudeRow(uint32_t rudeId, size_t rowIndex)
{
    m_chosenMm9RudeRows.insert((uint64_t(rudeId) << 32) | uint32_t(rowIndex));
}

bool Party::hasChosenMm9RudeRow(uint32_t rudeId, size_t rowIndex) const
{
    return m_chosenMm9RudeRows.contains((uint64_t(rudeId) << 32) | uint32_t(rowIndex));
}

bool Party::hasTeacherLedger(uint32_t continent) const
{
    return m_teacherLedgers.contains(continent);
}

void Party::addTeacherLedger(uint32_t continent)
{
    m_teacherLedgers.insert(continent);
}

const std::unordered_map<uint32_t, std::unordered_map<uint32_t, uint32_t>> &Party::npcTopicOverrides() const
{
    return m_npcTopicOverrides;
}

const std::unordered_map<uint32_t, uint32_t> &Party::npcHouseOverrides() const
{
    return m_npcHouseOverrides;
}

const std::unordered_set<uint32_t> &Party::unavailableNpcIds() const
{
    return m_unavailableNpcIds;
}

void Party::recordExplosiveMix(uint32_t targetItemId, uint32_t heldItemId)
{
    m_explosiveMixes.insert((static_cast<uint64_t>(targetItemId) << 32) | heldItemId);
}

bool Party::isExplosiveMixKnown(uint32_t targetItemId, uint32_t heldItemId) const
{
    return m_explosiveMixes.contains((static_cast<uint64_t>(targetItemId) << 32) | heldItemId);
}

void Party::setSpellField(std::vector<uint32_t> humQBits, std::vector<int> humPercents,
    std::optional<int> mapPercent)
{
    m_humQBits = std::move(humQBits);
    m_humPercents = std::move(humPercents);
    m_mapHumPercent = mapPercent;
}

void Party::setFloorBurn(CombatDamageType type, bool resisted)
{
    m_floorBurnType = type;
    m_floorBurnResisted = resisted;
}

void Party::setObjectiveQBits(std::vector<uint32_t> qbits)
{
    m_objectiveQBits = std::move(qbits);
}

size_t Party::objectivesDone() const
{
    return size_t(std::count_if(m_objectiveQBits.begin(), m_objectiveQBits.end(),
        [this](uint32_t qbit)
        {
            return hasQuestBit(qbit);
        }));
}

int Party::spellDamagePercentFor(const Character &caster) const
{
    int percent = 100;

    if (m_mapHumPercent)
    {
        percent = *m_mapHumPercent;
    }
    else if (!m_humPercents.empty())
    {
        size_t down = 0;

        for (const uint32_t qbit : m_humQBits)
        {
            down += hasQuestBit(qbit) ? 1 : 0;
        }

        percent = m_humPercents[std::min(down, m_humPercents.size() - 1)];
    }

    // A null field: only a Null Damper II casts there, at half power.
    if (percent <= 0)
    {
        return caster.equippedItemEffectFlags.contains("NullFieldCasting50") ? 50 : 0;
    }

    return std::min(100, percent + std::max(0, caster.humPoints));
}

bool Party::castingBlockedFor(const Character &caster) const
{
    return spellDamagePercentFor(caster) <= 0;
}

void Party::setHeldItemForQueries(const InventoryItem &item)
{
    m_heldItemIdForQueries = item.objectDescriptionId;
    recordEverOwnedItemIfRelevant(item);
}

uint32_t Party::heldItemIdForQueries() const
{
    return m_heldItemIdForQueries;
}

void Party::clearHeldItemForQueries()
{
    m_heldItemIdForQueries = 0;
}

bool Party::hasItemAnywhere(uint32_t objectDescriptionId) const
{
    return objectDescriptionId != 0
        && (inventoryItemCount(objectDescriptionId) > 0 || m_heldItemIdForQueries == objectDescriptionId);
}

bool Party::grantItemToMember(size_t memberIndex, uint32_t objectDescriptionId, uint32_t quantity)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || objectDescriptionId == 0 || quantity == 0)
    {
        return false;
    }

    for (uint32_t itemIndex = 0; itemIndex < quantity; ++itemIndex)
    {
        InventoryItem item = makeInventoryItem(m_pItemTable, objectDescriptionId);

        if (!pMember->addInventoryItem(item))
        {
            return false;
        }

        markArtifactItemFoundIfRelevant(item);
        recordEverOwnedItemIfRelevant(item);
    }

    m_lastStatus = "item granted";
    return true;
}

bool Party::removeItemFromMember(size_t memberIndex, uint32_t objectDescriptionId, uint32_t quantity)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || objectDescriptionId == 0 || quantity == 0)
    {
        return false;
    }

    for (uint32_t itemIndex = 0; itemIndex < quantity; ++itemIndex)
    {
        if (removeFromAnyBag(*pMember, objectDescriptionId))
        {
            continue;
        }

        // Not in a bag: a worn or wielded one goes, as the originals take it from the character too and as the item
        // checks count it (the Emerald Island judge's longbow: OY-172).
        bool removedEquipped = false;

        for (uint8_t slotIndex = 0; slotIndex <= uint8_t(EquipmentSlot::Ring6) && !removedEquipped; ++slotIndex)
        {
            const EquipmentSlot slot = EquipmentSlot(slotIndex);
            InventoryItem removedItem = {};
            removedEquipped = ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot) == objectDescriptionId
                && takeEquippedItemFromMember(memberIndex, slot, removedItem);
        }

        if (!removedEquipped)
        {
            return false;
        }
    }

    m_lastStatus = "item removed";
    return true;
}

bool Party::takeItemFromMemberInventoryCell(size_t memberIndex, uint8_t gridX, uint8_t gridY, InventoryItem &item)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    if (!pMember->takeInventoryItemAt(gridX, gridY, item))
    {
        return false;
    }

    m_lastStatus = "item picked up";
    return true;
}

bool Party::tryAutoPlaceItemInMemberInventory(size_t memberIndex, const InventoryItem &item)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    if (!addToAnyBag(*pMember, item, rules().items.bagCount(*this)))
    {
        m_lastStatus = "inventory full";
        return false;
    }

    recordEverOwnedItemIfRelevant(item);
    m_lastStatus = "item moved";
    return true;
}

bool Party::sortMemberInventory(size_t memberIndex)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    std::vector<InventoryItem> items = pMember->inventory;

    for (InventoryItem &item : items)
    {
        item.width = std::max<uint8_t>(1, item.width);
        item.height = std::max<uint8_t>(1, item.height);
    }

    const auto itemDefinition =
        [this](const InventoryItem &item) -> const ItemDefinition *
        {
            return m_pItemTable != nullptr ? m_pItemTable->get(item.objectDescriptionId) : nullptr;
        };
    const auto sizeAndIdentityKey =
        [](const InventoryItem &item)
        {
            return std::tuple(-int(item.height), -int(item.width), item.objectDescriptionId, item.gridX, item.gridY);
        };

    // Grouped by type for readability; tall items lead each group so columns fill cleanly.
    std::vector<InventoryItem> groupedItems = items;
    std::stable_sort(
        groupedItems.begin(),
        groupedItems.end(),
        [&itemDefinition, &sizeAndIdentityKey](const InventoryItem &left, const InventoryItem &right)
        {
            const int leftGroup = inventorySortGroup(itemDefinition(left));
            const int rightGroup = inventorySortGroup(itemDefinition(right));

            if (leftGroup != rightGroup)
            {
                return leftGroup < rightGroup;
            }

            return sizeAndIdentityKey(left) < sizeAndIdentityKey(right);
        });

    std::optional<std::vector<InventoryItem>> packed = packInventoryItems(groupedItems);

    if (!packed)
    {
        // A crowded inventory may only fit when packed purely by size.
        std::vector<InventoryItem> sizedItems = items;
        std::stable_sort(
            sizedItems.begin(),
            sizedItems.end(),
            [&sizeAndIdentityKey](const InventoryItem &left, const InventoryItem &right)
            {
                return sizeAndIdentityKey(left) < sizeAndIdentityKey(right);
            });
        packed = packInventoryItems(sizedItems);
    }

    if (!packed)
    {
        m_lastStatus = "not enough room to sort";
        return false;
    }

    pMember->inventory = std::move(*packed);
    m_lastStatus = "inventory sorted";
    return true;
}

bool Party::tryPlaceItemInMemberInventoryCell(
    size_t memberIndex,
    const InventoryItem &item,
    uint8_t gridX,
    uint8_t gridY,
    std::optional<InventoryItem> &replacedItem)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        replacedItem.reset();
        return false;
    }

    if (!pMember->tryPlaceInventoryItemAt(item, gridX, gridY, replacedItem))
    {
        return false;
    }

    recordEverOwnedItemIfRelevant(item);
    m_lastStatus = replacedItem.has_value() ? "item swapped" : "item moved";
    return true;
}

bool Party::takeEquippedItemFromMember(size_t memberIndex, EquipmentSlot slot, InventoryItem &item)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    const uint32_t itemId = ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot);

    if (itemId == 0)
    {
        return false;
    }

    item = {};
    item = makeInventoryItem(m_pItemTable, itemId, equippedItemRuntimeState(pMember->equipmentRuntime, slot));
    ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot) = 0;
    equippedItemRuntimeState(pMember->equipmentRuntime, slot) = {};
    rebuildMagicalBonusesFromBuffs();
    m_lastStatus = "item unequipped";
    return true;
}

bool Party::replaceEquippedItem(size_t memberIndex, EquipmentSlot slot, const InventoryItem &item)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot) == 0)
    {
        return false;
    }

    ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot) = item.objectDescriptionId;
    copyItemToEquippedRuntimeState(item, equippedItemRuntimeState(pMember->equipmentRuntime, slot));
    rebuildMagicalBonusesFromBuffs();
    return true;
}

bool Party::forceEquippedItem(size_t memberIndex, EquipmentSlot slot, const InventoryItem &item)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot) = item.objectDescriptionId;
    equippedItemRuntimeState(pMember->equipmentRuntime, slot) = {};

    if (item.objectDescriptionId != 0)
    {
        copyItemToEquippedRuntimeState(item, equippedItemRuntimeState(pMember->equipmentRuntime, slot));
    }

    rebuildMagicalBonusesFromBuffs();
    return true;
}

bool Party::tryEquipItemOnMember(
    size_t memberIndex,
    EquipmentSlot targetSlot,
    const InventoryItem &item,
    std::optional<EquipmentSlot> displacedSlot,
    bool autoStoreDisplacedItem,
    std::optional<InventoryItem> &heldReplacement)
{
    heldReplacement.reset();

    Character *pMember = member(memberIndex);

    if (pMember == nullptr || item.objectDescriptionId == 0)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable != nullptr ? m_pItemTable->get(item.objectDescriptionId) : nullptr;

    if (pItemDefinition == nullptr
        || !ItemRuntime::characterMeetsClassRestriction(*pMember, *pItemDefinition)
        || !ItemRuntime::characterMeetsRaceRestriction(*pMember, *pItemDefinition))
    {
        m_lastStatus = pItemDefinition != nullptr
            ? ItemRuntime::wearRequirementText(*pItemDefinition).value_or(Engine::tr("cannot equip"))
            : Engine::tr("cannot equip");
        return false;
    }

    if (const std::optional<std::string> refusal = rules().items.wearRefusal(item))
    {
        m_lastStatus = *refusal;
        return false;
    }

    const int requiredLevel = rules().items.levelRequirement(*pItemDefinition, item.rulesetFields);

    if (requiredLevel > 0 && pMember->level < uint32_t(requiredLevel))
    {
        m_lastStatus = Engine::tr("Level {level} required", {{"level", requiredLevel}});
        return false;
    }

    if (displacedSlot
        && *displacedSlot != targetSlot
        && ::OpenYAMM::Game::equippedItemId(pMember->equipment, targetSlot) != 0)
    {
        return false;
    }

    if (!displacedSlot && ::OpenYAMM::Game::equippedItemId(pMember->equipment, targetSlot) != 0)
    {
        displacedSlot = targetSlot;
    }

    if (!GameMechanics::isEquipmentAllowedWithWetsuit(
            *pMember,
            m_pItemTable,
            targetSlot,
            item.objectDescriptionId,
            displacedSlot))
    {
        m_lastStatus = Engine::tr("cannot equip");
        return false;
    }

    const uint32_t displacedItemId =
        displacedSlot ? ::OpenYAMM::Game::equippedItemId(pMember->equipment, *displacedSlot) : 0;
    const EquippedItemRuntimeState displacedRuntimeState =
        displacedSlot ? equippedItemRuntimeState(pMember->equipmentRuntime, *displacedSlot) : EquippedItemRuntimeState {};

    if (autoStoreDisplacedItem && displacedItemId != 0)
    {
        InventoryItem displacedInventoryItem = makeInventoryItem(
            m_pItemTable,
            displacedItemId,
            displacedRuntimeState);

        if (!pMember->addInventoryItem(displacedInventoryItem))
        {
            m_lastStatus = "inventory full";
            return false;
        }
    }

    if (displacedSlot)
    {
        ::OpenYAMM::Game::equippedItemId(pMember->equipment, *displacedSlot) = 0;
        equippedItemRuntimeState(pMember->equipmentRuntime, *displacedSlot) = {};
    }

    ::OpenYAMM::Game::equippedItemId(pMember->equipment, targetSlot) = item.objectDescriptionId;
    EquippedItemRuntimeState &targetRuntimeState = equippedItemRuntimeState(pMember->equipmentRuntime, targetSlot);
    targetRuntimeState.identified = item.identified;
    targetRuntimeState.broken = item.broken;
    targetRuntimeState.stolen = item.stolen;
    targetRuntimeState.hardened = item.hardened;
    targetRuntimeState.standardEnchantId = item.standardEnchantId;
    targetRuntimeState.standardEnchantPower = item.standardEnchantPower;
    targetRuntimeState.specialEnchantId = item.specialEnchantId;
    targetRuntimeState.artifactId = item.artifactId;
    targetRuntimeState.rarity = item.rarity;
    targetRuntimeState.currentCharges = item.currentCharges;
    targetRuntimeState.maxCharges = item.maxCharges;
    targetRuntimeState.temporaryBonusRemainingSeconds = item.temporaryBonusRemainingSeconds;
    targetRuntimeState.rulesetFields = item.rulesetFields;
    targetRuntimeState.workshopModId = item.workshopModId;

    if (targetRuntimeState.rarity == ItemRarity::Common && ItemRuntime::isRareItem(*pItemDefinition))
    {
        targetRuntimeState.rarity = pItemDefinition->rarity;
    }

    if (targetRuntimeState.artifactId == 0 && ItemRuntime::isRareItem(*pItemDefinition))
    {
        targetRuntimeState.artifactId = static_cast<uint16_t>(std::min<uint32_t>(pItemDefinition->itemId, 0xFFFFu));
    }

    if (!autoStoreDisplacedItem && displacedItemId != 0)
    {
        InventoryItem displacedInventoryItem = makeInventoryItem(m_pItemTable, displacedItemId, displacedRuntimeState);
        heldReplacement = displacedInventoryItem;
        m_lastStatus = "item swapped";
    }
    else
    {
        m_lastStatus = "item equipped";
    }

    rebuildMagicalBonusesFromBuffs();
    markArtifactItemFoundIfRelevant(item);
    recordEverOwnedItemIfRelevant(item);
    return true;
}

std::optional<InventoryItem> Party::equippedItem(size_t memberIndex, EquipmentSlot slot) const
{
    const Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return std::nullopt;
    }

    const uint32_t itemId = ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot);

    if (itemId == 0)
    {
        return std::nullopt;
    }

    return makeInventoryItem(m_pItemTable, itemId, equippedItemRuntimeState(pMember->equipmentRuntime, slot));
}

const InventoryItem *Party::memberInventoryItem(size_t memberIndex, uint8_t gridX, uint8_t gridY) const
{
    const Character *pMember = member(memberIndex);
    return pMember != nullptr ? pMember->inventoryItemAt(gridX, gridY) : nullptr;
}

InventoryItem *Party::memberInventoryItemMutable(size_t memberIndex, uint8_t gridX, uint8_t gridY)
{
    Character *pMember = member(memberIndex);
    return pMember != nullptr ? inventoryItemAtMutable(*pMember, gridX, gridY) : nullptr;
}

uint32_t Party::equippedItemId(size_t memberIndex, EquipmentSlot slot) const
{
    const Character *pMember = member(memberIndex);
    return pMember != nullptr ? ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot) : 0;
}

bool Party::memberCanWearArmor(size_t memberIndex) const
{
    const Character *pMember = member(memberIndex);
    const CharacterDollEntry *pDollEntry = pMember != nullptr && m_pCharacterDollTable != nullptr
        ? m_pCharacterDollTable->getCharacter(pMember->characterDataId)
        : nullptr;
    const CharacterDollTypeEntry *pDollType =
        pDollEntry != nullptr ? m_pCharacterDollTable->getDollType(pDollEntry->dollTypeId) : nullptr;
    return pDollType == nullptr || pDollType->canEquipArmor;
}

namespace
{
constexpr std::array<EquipmentSlot, 16> WorkshopModSlots = {EquipmentSlot::MainHand, EquipmentSlot::Bow,
    EquipmentSlot::OffHand, EquipmentSlot::Armor, EquipmentSlot::Helm, EquipmentSlot::Cloak, EquipmentSlot::Belt,
    EquipmentSlot::Gauntlets, EquipmentSlot::Boots, EquipmentSlot::Amulet, EquipmentSlot::Ring1, EquipmentSlot::Ring2,
    EquipmentSlot::Ring3, EquipmentSlot::Ring4, EquipmentSlot::Ring5, EquipmentSlot::Ring6};
}

uint32_t Party::workshopModTarget(size_t memberIndex, uint16_t modId) const
{
    const WorkshopModDefinition *pMod = m_pItemTable != nullptr ? m_pItemTable->workshopMod(modId) : nullptr;

    if (pMod == nullptr)
    {
        return 0;
    }

    for (const EquipmentSlot slot : WorkshopModSlots)
    {
        const uint32_t itemId = equippedItemId(memberIndex, slot);
        const ItemDefinition *pItem = itemId != 0 ? m_pItemTable->get(itemId) : nullptr;

        if (pItem != nullptr && m_pItemTable->workshopModFits(*pMod, *pItem))
        {
            return itemId;
        }
    }

    return 0;
}

uint32_t Party::fitWorkshopMod(size_t memberIndex, uint16_t modId)
{
    const uint32_t itemId = workshopModTarget(memberIndex, modId);

    for (const EquipmentSlot slot : WorkshopModSlots)
    {
        if (itemId != 0 && equippedItemId(memberIndex, slot) == itemId)
        {
            equippedItemRuntimeMutable(memberIndex, slot)->workshopModId = modId;
            rebuildMagicalBonusesFromBuffs();
            break;
        }
    }

    return itemId;
}

const EquippedItemRuntimeState *Party::equippedItemRuntime(size_t memberIndex, EquipmentSlot slot) const
{
    const Character *pMember = member(memberIndex);
    return pMember != nullptr ? &equippedItemRuntimeState(pMember->equipmentRuntime, slot) : nullptr;
}

EquippedItemRuntimeState *Party::equippedItemRuntimeMutable(size_t memberIndex, EquipmentSlot slot)
{
    Character *pMember = member(memberIndex);
    return pMember != nullptr ? &equippedItemRuntimeState(pMember->equipmentRuntime, slot) : nullptr;
}

bool Party::consumeEquippedWandCharge(size_t memberIndex)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || m_pItemTable == nullptr || pMember->equipment.mainHand == 0)
    {
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(pMember->equipment.mainHand);

    if (pItemDefinition == nullptr
        || pItemDefinition->equipStat != "WeaponW"
        || pMember->equipmentRuntime.mainHand.broken
        || pMember->equipmentRuntime.mainHand.currentCharges == 0)
    {
        return false;
    }

    --pMember->equipmentRuntime.mainHand.currentCharges;
    return true;
}

void Party::refreshDerivedState()
{
    rebuildMagicalBonusesFromBuffs();
}

bool Party::isPartyWideUtilitySkill(std::string_view skillName)
{
    const std::string canonical = canonicalPartyWideUtilitySkillName(skillName);

    return canonical == "RepairItem"
        || canonical == "DisarmTraps"
        || canonical == "Merchant"
        || canonical == "IdentifyItem"
        || canonical == "IdentifyMonster"
        || canonical == "Alchemy"
        || canonical == "Perception"
        || canonical == "Hacking";
}

std::optional<size_t> Party::bestPartyWideUtilitySkillMemberIndex(
    std::string_view skillName,
    bool requireCanAct) const
{
    const std::string canonical = canonicalPartyWideUtilitySkillName(skillName);

    if (!isPartyWideUtilitySkill(canonical))
    {
        return std::nullopt;
    }

    std::optional<size_t> bestMemberIndex;
    int bestScore = 0;

    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        const Character &member = m_members[memberIndex];

        if (requireCanAct && !GameMechanics::canAct(member))
        {
            continue;
        }

        const int score = partyWideUtilitySkillScore(member, canonical);

        if (score > bestScore)
        {
            bestScore = score;
            bestMemberIndex = memberIndex;
        }
    }

    return bestMemberIndex;
}

const Character *Party::bestPartyWideUtilitySkillMember(std::string_view skillName, bool requireCanAct) const
{
    const std::optional<size_t> memberIndex = bestPartyWideUtilitySkillMemberIndex(skillName, requireCanAct);
    return memberIndex ? member(*memberIndex) : nullptr;
}

int Party::bestPartyWideUtilitySkillValue(std::string_view skillName, bool requireCanAct) const
{
    const std::optional<size_t> memberIndex = bestPartyWideUtilitySkillMemberIndex(skillName, requireCanAct);
    const Character *pMember = memberIndex ? member(*memberIndex) : nullptr;

    if (pMember == nullptr)
    {
        return 0;
    }

    return partyWideUtilitySkillScore(*pMember, canonicalPartyWideUtilitySkillName(skillName));
}

bool Party::canIdentifyItem(const ItemDefinition &itemDefinition) const
{
    // MM9's Cleirach A'Lyrae: Identify Item never fails for lack of skill (cshell@0x10011970).
    if (hiredNpcHasProfession(activeHiredNpcFollowers(), 4) || mm9HirelingPassives().identifyAlways)
    {
        return true;
    }

    const Character *pInspector = bestPartyWideUtilitySkillMember("IdentifyItem");
    return pInspector != nullptr && ItemRuntime::canCharacterIdentifyItem(*pInspector, itemDefinition);
}

bool Party::canRepairItem(const ItemDefinition &itemDefinition) const
{
    // MM9's Alvar the Clumsy: Repair Item never fails for lack of skill (cshell@0x10011aa0).
    if (hiredNpcCanRepairItemKind(activeHiredNpcFollowers(), itemDefinition.equipStat)
        || mm9HirelingPassives().repairAlways)
    {
        return true;
    }
    const Character *pInspector = bestPartyWideUtilitySkillMember("RepairItem");
    return pInspector != nullptr && ItemRuntime::canCharacterRepairItem(*pInspector, itemDefinition);
}

bool Party::tryIdentifyMemberInventoryItem(
    size_t memberIndex,
    uint8_t gridX,
    uint8_t gridY,
    size_t inspectorMemberIndex,
    std::string &statusText)
{
    statusText.clear();
    Character *pMember = member(memberIndex);
    const Character *pInspector = bestPartyWideUtilitySkillMember("IdentifyItem");
    const Character *pRequestedInspector = member(inspectorMemberIndex);

    if (pMember == nullptr || pRequestedInspector == nullptr || m_pItemTable == nullptr)
    {
        return false;
    }

    InventoryItem *pItem = inventoryItemAtMutable(*pMember, gridX, gridY);

    if (pItem == nullptr)
    {
        statusText = Engine::tr("No item there.");
        logItemInteractionResult(
            "identify",
            pInspector,
            pMember,
            nullptr,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(pItem->objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = Engine::tr("Unavailable.");
        logItemInteractionResult(
            "identify",
            pInspector,
            pMember,
            nullptr,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    if (pItem->identified || !ItemRuntime::requiresIdentification(*pItemDefinition))
    {
        statusText = Engine::tr("Already identified.");
        logItemInteractionResult(
            "identify",
            pInspector,
            pMember,
            pItemDefinition,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    if (!canIdentifyItem(*pItemDefinition))
    {
        statusText = Engine::tr("Identify Failed");
        logItemInteractionResult(
            "identify",
            pInspector,
            pMember,
            pItemDefinition,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    const bool identified = identifyInventoryItemInstance(*pItem, *pItemDefinition, statusText);

    if (identified)
    {
        m_lastStatus = "item identified";
    }

    logItemInteractionResult(
        "identify",
        pInspector,
        pMember,
        pItemDefinition,
        "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
        identified,
        statusText);

    return identified;
}

bool Party::tryRepairMemberInventoryItem(
    size_t memberIndex,
    uint8_t gridX,
    uint8_t gridY,
    size_t inspectorMemberIndex,
    std::string &statusText)
{
    statusText.clear();
    Character *pMember = member(memberIndex);
    const Character *pInspector = bestPartyWideUtilitySkillMember("RepairItem");
    const Character *pRequestedInspector = member(inspectorMemberIndex);

    if (pMember == nullptr || pRequestedInspector == nullptr || m_pItemTable == nullptr)
    {
        return false;
    }

    InventoryItem *pItem = inventoryItemAtMutable(*pMember, gridX, gridY);

    if (pItem == nullptr)
    {
        statusText = Engine::tr("No item there.");
        logItemInteractionResult(
            "repair",
            pInspector,
            pMember,
            nullptr,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(pItem->objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = Engine::tr("Unavailable.");
        logItemInteractionResult(
            "repair",
            pInspector,
            pMember,
            nullptr,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    if (!pItem->broken)
    {
        statusText = Engine::tr("Nothing to repair.");
        logItemInteractionResult(
            "repair",
            pInspector,
            pMember,
            pItemDefinition,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    if (!canRepairItem(*pItemDefinition))
    {
        statusText = Engine::tr("Repair Failed");
        logItemInteractionResult(
            "repair",
            pInspector,
            pMember,
            pItemDefinition,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    const bool repaired = repairInventoryItemInstance(*pItem, *pItemDefinition, statusText);

    if (repaired)
    {
        rebuildMagicalBonusesFromBuffs();
        m_lastStatus = "item repaired";
    }

    logItemInteractionResult(
        "repair",
        pInspector,
        pMember,
        pItemDefinition,
        "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
        repaired,
        statusText);

    return repaired;
}

bool Party::identifyMemberInventoryItem(
    size_t memberIndex,
    uint8_t gridX,
    uint8_t gridY,
    std::string &statusText)
{
    statusText.clear();
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || m_pItemTable == nullptr)
    {
        return false;
    }

    InventoryItem *pItem = inventoryItemAtMutable(*pMember, gridX, gridY);

    if (pItem == nullptr)
    {
        statusText = Engine::tr("No item there.");
        logItemInteractionResult(
            "identify",
            nullptr,
            pMember,
            nullptr,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(pItem->objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = Engine::tr("Unavailable.");
        logItemInteractionResult(
            "identify",
            nullptr,
            pMember,
            nullptr,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    const bool identified = identifyInventoryItemInstance(*pItem, *pItemDefinition, statusText);

    if (identified)
    {
        m_lastStatus = "item identified";
    }

    logItemInteractionResult(
        "identify",
        nullptr,
        pMember,
        pItemDefinition,
        "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
        identified,
        statusText);

    return identified;
}

bool Party::repairMemberInventoryItem(
    size_t memberIndex,
    uint8_t gridX,
    uint8_t gridY,
    std::string &statusText)
{
    statusText.clear();
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || m_pItemTable == nullptr)
    {
        return false;
    }

    InventoryItem *pItem = inventoryItemAtMutable(*pMember, gridX, gridY);

    if (pItem == nullptr)
    {
        statusText = Engine::tr("No item there.");
        logItemInteractionResult(
            "repair",
            nullptr,
            pMember,
            nullptr,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(pItem->objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        statusText = Engine::tr("Unavailable.");
        logItemInteractionResult(
            "repair",
            nullptr,
            pMember,
            nullptr,
            "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
            false,
            statusText);
        return false;
    }

    const bool repaired = repairInventoryItemInstance(*pItem, *pItemDefinition, statusText);

    if (repaired)
    {
        rebuildMagicalBonusesFromBuffs();
        m_lastStatus = "item repaired";
    }

    logItemInteractionResult(
        "repair",
        nullptr,
        pMember,
        pItemDefinition,
        "inventory(" + std::to_string(gridX) + "," + std::to_string(gridY) + ")",
        repaired,
        statusText);

    return repaired;
}

bool Party::tryIdentifyEquippedItem(
    size_t memberIndex,
    EquipmentSlot slot,
    size_t inspectorMemberIndex,
    std::string &statusText)
{
    statusText.clear();
    Character *pMember = member(memberIndex);
    const Character *pInspector = bestPartyWideUtilitySkillMember("IdentifyItem");
    const Character *pRequestedInspector = member(inspectorMemberIndex);

    if (pMember == nullptr || pRequestedInspector == nullptr || m_pItemTable == nullptr)
    {
        return false;
    }

    const uint32_t itemId = ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot);

    if (itemId == 0)
    {
        statusText = Engine::tr("No item there.");
        logItemInteractionResult(
            "identify",
            pInspector,
            pMember,
            nullptr,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    EquippedItemRuntimeState &runtimeState = equippedItemRuntimeState(pMember->equipmentRuntime, slot);
    const ItemDefinition *pItemDefinition = m_pItemTable->get(itemId);

    if (pItemDefinition == nullptr)
    {
        statusText = Engine::tr("Unavailable.");
        logItemInteractionResult(
            "identify",
            pInspector,
            pMember,
            nullptr,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    if (runtimeState.identified || !ItemRuntime::requiresIdentification(*pItemDefinition))
    {
        statusText = Engine::tr("Already identified.");
        logItemInteractionResult(
            "identify",
            pInspector,
            pMember,
            pItemDefinition,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    if (!canIdentifyItem(*pItemDefinition))
    {
        statusText = Engine::tr("Identify Failed");
        logItemInteractionResult(
            "identify",
            pInspector,
            pMember,
            pItemDefinition,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    const bool identified = identifyEquippedItemInstance(runtimeState, *pItemDefinition, statusText);

    if (identified)
    {
        m_lastStatus = "item identified";
    }

    logItemInteractionResult(
        "identify",
        pInspector,
        pMember,
        pItemDefinition,
        std::string("equipped(") + equipmentSlotName(slot) + ")",
        identified,
        statusText);

    return identified;
}

bool Party::tryRepairEquippedItem(
    size_t memberIndex,
    EquipmentSlot slot,
    size_t inspectorMemberIndex,
    std::string &statusText)
{
    statusText.clear();
    Character *pMember = member(memberIndex);
    const Character *pInspector = bestPartyWideUtilitySkillMember("RepairItem");
    const Character *pRequestedInspector = member(inspectorMemberIndex);

    if (pMember == nullptr || pRequestedInspector == nullptr || m_pItemTable == nullptr)
    {
        return false;
    }

    const uint32_t itemId = ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot);

    if (itemId == 0)
    {
        statusText = Engine::tr("No item there.");
        logItemInteractionResult(
            "repair",
            pInspector,
            pMember,
            nullptr,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    EquippedItemRuntimeState &runtimeState = equippedItemRuntimeState(pMember->equipmentRuntime, slot);
    const ItemDefinition *pItemDefinition = m_pItemTable->get(itemId);

    if (pItemDefinition == nullptr)
    {
        statusText = Engine::tr("Unavailable.");
        logItemInteractionResult(
            "repair",
            pInspector,
            pMember,
            nullptr,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    if (!runtimeState.broken)
    {
        statusText = Engine::tr("Nothing to repair.");
        logItemInteractionResult(
            "repair",
            pInspector,
            pMember,
            pItemDefinition,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    if (!canRepairItem(*pItemDefinition))
    {
        statusText = Engine::tr("Repair Failed");
        logItemInteractionResult(
            "repair",
            pInspector,
            pMember,
            pItemDefinition,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    const bool repaired = repairEquippedItemInstance(runtimeState, *pItemDefinition, statusText);

    if (repaired)
    {
        rebuildMagicalBonusesFromBuffs();
        m_lastStatus = "item repaired";
    }

    logItemInteractionResult(
        "repair",
        pInspector,
        pMember,
        pItemDefinition,
        std::string("equipped(") + equipmentSlotName(slot) + ")",
        repaired,
        statusText);

    return repaired;
}

bool Party::identifyEquippedItem(size_t memberIndex, EquipmentSlot slot, std::string &statusText)
{
    statusText.clear();
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || m_pItemTable == nullptr)
    {
        return false;
    }

    const uint32_t itemId = ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot);

    if (itemId == 0)
    {
        statusText = Engine::tr("No item there.");
        logItemInteractionResult(
            "identify",
            nullptr,
            pMember,
            nullptr,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    EquippedItemRuntimeState &runtimeState = equippedItemRuntimeState(pMember->equipmentRuntime, slot);
    const ItemDefinition *pItemDefinition = m_pItemTable->get(itemId);

    if (pItemDefinition == nullptr)
    {
        statusText = Engine::tr("Unavailable.");
        logItemInteractionResult(
            "identify",
            nullptr,
            pMember,
            nullptr,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    const bool identified = identifyEquippedItemInstance(runtimeState, *pItemDefinition, statusText);

    if (identified)
    {
        m_lastStatus = "item identified";
    }

    logItemInteractionResult(
        "identify",
        nullptr,
        pMember,
        pItemDefinition,
        std::string("equipped(") + equipmentSlotName(slot) + ")",
        identified,
        statusText);

    return identified;
}

bool Party::repairEquippedItem(size_t memberIndex, EquipmentSlot slot, std::string &statusText)
{
    statusText.clear();
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || m_pItemTable == nullptr)
    {
        return false;
    }

    const uint32_t itemId = ::OpenYAMM::Game::equippedItemId(pMember->equipment, slot);

    if (itemId == 0)
    {
        statusText = Engine::tr("No item there.");
        logItemInteractionResult(
            "repair",
            nullptr,
            pMember,
            nullptr,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    EquippedItemRuntimeState &runtimeState = equippedItemRuntimeState(pMember->equipmentRuntime, slot);
    const ItemDefinition *pItemDefinition = m_pItemTable->get(itemId);

    if (pItemDefinition == nullptr)
    {
        statusText = Engine::tr("Unavailable.");
        logItemInteractionResult(
            "repair",
            nullptr,
            pMember,
            nullptr,
            std::string("equipped(") + equipmentSlotName(slot) + ")",
            false,
            statusText);
        return false;
    }

    const bool repaired = repairEquippedItemInstance(runtimeState, *pItemDefinition, statusText);

    if (repaired)
    {
        rebuildMagicalBonusesFromBuffs();
        m_lastStatus = "item repaired";
    }

    logItemInteractionResult(
        "repair",
        nullptr,
        pMember,
        pItemDefinition,
        std::string("equipped(") + equipmentSlotName(slot) + ")",
        repaired,
        statusText);

    return repaired;
}

bool Party::setMemberClassName(size_t memberIndex, const std::string &className, bool classOnly)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    pMember->className = canonicalClassName(className);
    pMember->role = normalizeRoleName(pMember->className);

    if (pMember->className == "Lich" && !classOnly)
    {
        applyLichIdentity(*pMember, m_pCharacterDollTable);
        applyLichState(*pMember);
    }

    GameMechanics::refreshCharacterBaseResources(*pMember, false, m_pClassMultiplierTable);
    m_lastStatus = "class changed";
    return true;
}

void Party::refreshMemberResources(size_t memberIndex)
{
    if (Character *pMember = member(memberIndex))
    {
        GameMechanics::refreshCharacterBaseResources(*pMember, false, m_pClassMultiplierTable);
    }
}

bool Party::applyLichTransformation(size_t memberIndex)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    pMember->className = "Lich";
    pMember->role = normalizeRoleName(pMember->className);
    applyLichIdentity(*pMember, m_pCharacterDollTable);
    applyLichState(*pMember);
    GameMechanics::refreshCharacterBaseResources(*pMember, false, m_pClassMultiplierTable);
    m_lastStatus = "lich transformation applied";
    return true;
}

const Character *Party::member(size_t memberIndex) const
{
    if (memberIndex >= m_members.size())
    {
        return nullptr;
    }

    return &m_members[memberIndex];
}

Character *Party::member(size_t memberIndex)
{
    if (memberIndex >= m_members.size())
    {
        return nullptr;
    }

    return &m_members[memberIndex];
}

bool Party::canSelectMemberInGameplay(size_t memberIndex) const
{
    const Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    return GameMechanics::canSelectInGameplay(*pMember);
}

bool Party::hasSelectableMemberInGameplay() const
{
    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        if (canSelectMemberInGameplay(memberIndex))
        {
            return true;
        }
    }

    return false;
}

bool Party::hasActableMember() const
{
    for (const Character &member : m_members)
    {
        if (!member.conditions.test(static_cast<size_t>(CharacterCondition::Paralyzed))
            && !member.conditions.test(static_cast<size_t>(CharacterCondition::Unconscious))
            && !member.conditions.test(static_cast<size_t>(CharacterCondition::Dead))
            && !member.conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
            && !member.conditions.test(static_cast<size_t>(CharacterCondition::Eradicated)))
        {
            return true;
        }
    }

    return false;
}

uint8_t Party::resolveInventoryWidth(uint32_t objectDescriptionId) const
{
    if (m_pItemTable == nullptr)
    {
        return 1;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return 1;
    }

    return std::max<uint8_t>(1, pItemDefinition->inventoryWidth);
}

uint8_t Party::resolveInventoryHeight(uint32_t objectDescriptionId) const
{
    if (m_pItemTable == nullptr)
    {
        return 1;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return 1;
    }

    return std::max<uint8_t>(1, pItemDefinition->inventoryHeight);
}

const std::vector<Character> &Party::members() const
{
    return m_members;
}

size_t Party::memberCount() const
{
    return m_members.size();
}

const std::vector<AdventurersInnMember> &Party::adventurersInnMembers() const
{
    return m_adventurersInnMembers;
}

const AdventurersInnMember *Party::adventurersInnMember(size_t innIndex) const
{
    return innIndex < m_adventurersInnMembers.size() ? &m_adventurersInnMembers[innIndex] : nullptr;
}

AdventurersInnMember *Party::adventurersInnMember(size_t innIndex)
{
    return innIndex < m_adventurersInnMembers.size() ? &m_adventurersInnMembers[innIndex] : nullptr;
}

const Character *Party::adventurersInnCharacter(size_t innIndex) const
{
    const AdventurersInnMember *pMember = adventurersInnMember(innIndex);
    return pMember != nullptr ? &pMember->character : nullptr;
}

Character *Party::adventurersInnCharacter(size_t innIndex)
{
    AdventurersInnMember *pMember = adventurersInnMember(innIndex);
    return pMember != nullptr ? &pMember->character : nullptr;
}

void Party::clearAdventurersInnMembers()
{
    m_adventurersInnMembers.clear();
}

bool Party::setActiveMemberIndex(size_t memberIndex)
{
    if (memberIndex >= m_members.size())
    {
        return false;
    }

    m_activeMemberIndex = memberIndex;
    m_activeHirelingIndex.reset();
    return true;
}

bool Party::canSpendSpellPoints(size_t memberIndex, int amount) const
{
    if (m_debugUnlimitedMana)
    {
        return true;
    }

    const Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    return amount <= 0 || pMember->spellPoints >= amount;
}

bool Party::spendSpellPoints(size_t memberIndex, int amount)
{
    if (m_debugUnlimitedMana)
    {
        return true;
    }

    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    if (amount <= 0)
    {
        return true;
    }

    if (pMember->spellPoints < amount)
    {
        return false;
    }

    pMember->spellPoints -= amount;
    return true;
}

bool Party::spendSpellPointsOnActiveMember(int amount)
{
    return spendSpellPoints(activeMemberIndex(), amount);
}

void Party::applyWeeklyItemEffects()
{
    ++m_itemWeeklyEffectSequence;
    bool grantWeeklyGold = false;

    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        Character &member = m_members[memberIndex];
        grantWeeklyGold = grantWeeklyGold
            || member.equippedItemEffectFlags.contains("WeeklyGold1000");
        const uint32_t rollSeed = m_itemWeeklyEffectSequence * 0x9e3779b9u
            ^ static_cast<uint32_t>(memberIndex + 1) * 0x85ebca6bu;

        if (member.equippedItemEffectFlags.contains("WeeklyInsanityChance10")
            && rollSeed % 100u < 10u)
        {
            applyMemberCondition(memberIndex, CharacterCondition::Insane);
        }

        if (member.equippedItemEffectFlags.contains("WeeklyHealthLossChance10")
            && (rollSeed ^ 0xc2b2ae35u) % 100u < 10u)
        {
            applyDamageToMember(
                memberIndex,
                std::max(1, currentMaximumHealth(member) / 10),
                Engine::tr("An equipped relic exacts its weekly price"));
        }
    }

    if (grantWeeklyGold)
    {
        addGold(1000, GoldReason::Other);
    }
}

void Party::advanceTimedStates(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    bool buffsChanged = false;
    bool itemsChanged = false;
    constexpr float GameSecondsPerWeek = 7.0f * 24.0f * 60.0f * 60.0f;
    const float previousRegenerationTick =
        std::floor(m_periodicEffectElapsedGameSeconds / OeFiveGameMinuteTickGameSeconds);
    m_periodicEffectElapsedGameSeconds += deltaSeconds;
    // The saved periodic clock preserves the five-minute tick phase; a week contains whole ticks.
    const int regenerationTicks = static_cast<int>(
        std::floor(m_periodicEffectElapsedGameSeconds / OeFiveGameMinuteTickGameSeconds) - previousRegenerationTick);

    if (regenerationTicks > 0)
    {
        for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
        {
            Character &member = m_members[memberIndex];
            const int spellPointsPerTick = rules().skills.meditationSpellPointsPerTick(member);

            if (spellPointsPerTick <= 0
                || member.conditions.test(static_cast<size_t>(CharacterCondition::Dead))
                || member.conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
                || member.conditions.test(static_cast<size_t>(CharacterCondition::Eradicated)))
            {
                continue;
            }

            member.spellPoints = std::min(std::max(member.spellPoints, reachableMaximumSpellPoints(memberIndex)),
                member.spellPoints + regenerationTicks * spellPointsPerTick);
        }
    }

    while (m_periodicEffectElapsedGameSeconds >= GameSecondsPerWeek)
    {
        m_periodicEffectElapsedGameSeconds -= GameSecondsPerWeek;
        applyWeeklyItemEffects();
    }

    for (PartyBuffState &buff : m_partyBuffs)
    {
        if (!buff.active())
        {
            continue;
        }

        const float previousRemainingSeconds = buff.remainingSeconds;
        buff.remainingSeconds = std::max(0.0f, buff.remainingSeconds - deltaSeconds);

        if (previousRemainingSeconds > 0.0f && buff.remainingSeconds <= 0.0f)
        {
            buffsChanged = true;

            // The hirelings share the party's haste and its weakness.
            if (isSpellId(buff.spellId, SpellId::Haste))
            {
                for (size_t memberIndex = 0; memberIndex < combatantCount(); ++memberIndex)
                {
                    applyMemberCondition(memberIndex, CharacterCondition::Weak);
                }
            }
        }
    }

    for (size_t memberIndex = 0; memberIndex < combatantCount(); ++memberIndex)
    {
        std::array<CharacterBuffState, CharacterBuffCount> *pBuffs = combatantBuffs(memberIndex);

        if (pBuffs == nullptr)
        {
            continue;
        }

        for (CharacterBuffState &buff : *pBuffs)
        {
            if (!buff.active())
            {
                continue;
            }

            const float previousRemainingSeconds = buff.remainingSeconds;
            buff.remainingSeconds = std::max(0.0f, buff.remainingSeconds - deltaSeconds);

            if (isSpellId(buff.spellId, SpellId::Regeneration))
            {
                buff.periodicAccumulatorSeconds += deltaSeconds;
                const int healPerTick = 5 * std::max(1, buff.power);

                while (buff.periodicAccumulatorSeconds >= OeFiveGameMinuteTickGameSeconds)
                {
                    buff.periodicAccumulatorSeconds -= OeFiveGameMinuteTickGameSeconds;
                    healMember(memberIndex, healPerTick);
                }
            }

            if (previousRemainingSeconds > 0.0f && buff.remainingSeconds <= 0.0f)
            {
                buffsChanged = true;
                buff.periodicAccumulatorSeconds = 0.0f;

                // A Haste potion leaves its drinker weak, like the spell.
                if (&buff == &(*pBuffs)[static_cast<size_t>(CharacterBuffId::Haste)])
                {
                    applyMemberCondition(memberIndex, CharacterCondition::Weak);
                }
            }
        }
    }

    const auto updateTimedInventoryItem =
        [&itemsChanged, deltaSeconds](InventoryItem &item)
        {
            if (item.temporaryBonusRemainingSeconds <= 0.0f)
            {
                return;
            }

            item.temporaryBonusRemainingSeconds = std::max(0.0f, item.temporaryBonusRemainingSeconds - deltaSeconds);

            if (item.temporaryBonusRemainingSeconds > 0.0f)
            {
                return;
            }

            item.standardEnchantId = 0;
            item.standardEnchantPower = 0;
            item.specialEnchantId = 0;
            itemsChanged = true;
        };
    const auto updateTimedEquippedItem =
        [&itemsChanged, deltaSeconds](EquippedItemRuntimeState &item)
        {
            if (item.temporaryBonusRemainingSeconds <= 0.0f)
            {
                return;
            }

            item.temporaryBonusRemainingSeconds = std::max(0.0f, item.temporaryBonusRemainingSeconds - deltaSeconds);

            if (item.temporaryBonusRemainingSeconds > 0.0f)
            {
                return;
            }

            item.standardEnchantId = 0;
            item.standardEnchantPower = 0;
            item.specialEnchantId = 0;
            itemsChanged = true;
        };

    for (Character &member : m_members)
    {
        // Potions' immunities, skill levels and auras run out.
        const size_t potionEffectsBefore = member.rulesetState.potionEffects.size();
        std::erase_if(
            member.rulesetState.potionEffects,
            [deltaSeconds](TimedPotionEffect &effect)
            {
                effect.remainingSeconds -= deltaSeconds;
                return effect.remainingSeconds <= 0;
            });
        buffsChanged = buffsChanged || member.rulesetState.potionEffects.size() != potionEffectsBefore;

        for (TimedPrimaryStatBonus &bonus : member.timedPrimaryStatBonuses)
        {
            if (bonus.remainingSeconds <= 0.0f)
            {
                continue;
            }
            bonus.remainingSeconds = std::max(0.0f, bonus.remainingSeconds - deltaSeconds);
            if (bonus.remainingSeconds <= 0.0f)
            {
                bonus.power = 0;
                buffsChanged = true;
            }
        }

        for (InventoryItem &item : member.inventory)
        {
            updateTimedInventoryItem(item);
        }

        updateTimedEquippedItem(member.equipmentRuntime.offHand);
        updateTimedEquippedItem(member.equipmentRuntime.mainHand);
        updateTimedEquippedItem(member.equipmentRuntime.bow);
        updateTimedEquippedItem(member.equipmentRuntime.armor);
        updateTimedEquippedItem(member.equipmentRuntime.helm);
        updateTimedEquippedItem(member.equipmentRuntime.belt);
        updateTimedEquippedItem(member.equipmentRuntime.cloak);
        updateTimedEquippedItem(member.equipmentRuntime.gauntlets);
        updateTimedEquippedItem(member.equipmentRuntime.boots);
        updateTimedEquippedItem(member.equipmentRuntime.amulet);
        updateTimedEquippedItem(member.equipmentRuntime.ring1);
        updateTimedEquippedItem(member.equipmentRuntime.ring2);
        updateTimedEquippedItem(member.equipmentRuntime.ring3);
        updateTimedEquippedItem(member.equipmentRuntime.ring4);
        updateTimedEquippedItem(member.equipmentRuntime.ring5);
        updateTimedEquippedItem(member.equipmentRuntime.ring6);

        for (std::optional<LloydBeacon> &beacon : member.lloydsBeacons)
        {
            if (!beacon.has_value())
            {
                continue;
            }

            beacon->remainingSeconds = std::max(0.0f, beacon->remainingSeconds - deltaSeconds);

            if (beacon->remainingSeconds <= 0.0f)
            {
                beacon.reset();
            }
        }
    }

    if (buffsChanged || itemsChanged)
    {
        rebuildMagicalBonusesFromBuffs();
    }

    if (!canSelectCombatantInGameplay(activeCombatantIndex()))
    {
        switchToNextReadyMember();
    }
}

void Party::updateRecovery(float deltaSeconds, float progressScale)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    const float clampedProgressScale = std::max(0.0f, progressScale);

    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        Character &member = m_members[memberIndex];
        const float recoveryDelta =
            deltaSeconds * clampedProgressScale * std::max(0.0f, member.recoveryProgressMultiplier);
        member.recoverySecondsRemaining = std::max(0.0f, member.recoverySecondsRemaining - recoveryDelta);
    }

    // The hirelings recover as the members do (haste and slow through recoveryProgressMultiplier).
    for (Mm9PartyHireling &hireling : m_mm9Hirelings)
    {
        Character &character = hireling.character;
        const float recoveryDelta =
            deltaSeconds * clampedProgressScale * std::max(0.0f, character.recoveryProgressMultiplier);
        character.recoverySecondsRemaining = std::max(0.0f, character.recoverySecondsRemaining - recoveryDelta);
    }

    updateRegeneration(deltaSeconds);
}

void Party::updateRegeneration(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    updatePersonalShields(deltaSeconds);

    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        Character &member = m_members[memberIndex];

        // The dead, the eradicated and stone do not regenerate (OE Engine::_regenerateHp, MMerge MiscTweaks).
        const bool regenerationBlocked = isDeadOrEradicated(member)
            || member.conditions.test(static_cast<size_t>(CharacterCondition::Petrified));

        if (regenerationBlocked)
        {
            member.healthRegenAccumulator = 0.0f;
        }
        else if (member.healthRegenPerSecond != 0.0f)
        {
            member.healthRegenAccumulator += member.healthRegenPerSecond * deltaSeconds;
            const int healthAmount = static_cast<int>(member.healthRegenAccumulator);

            // Regeneration stops at what the auras leave, or the next reservation clamp would take it back.
            if (healthAmount > 0)
            {
                member.healthRegenAccumulator -= static_cast<float>(healthAmount);
                member.health = std::min(
                    std::max(member.health, reachableMaximumHealth(memberIndex)), member.health + healthAmount);
            }
            else if (healthAmount < 0)
            {
                member.healthRegenAccumulator -= static_cast<float>(healthAmount);
                applyDamageToMember(memberIndex, -healthAmount, "");
            }
        }

        if (member.spellRegenPerSecond != 0.0f)
        {
            member.spellRegenAccumulator += member.spellRegenPerSecond * deltaSeconds;
            const int spellAmount = static_cast<int>(member.spellRegenAccumulator);

            if (spellAmount > 0)
            {
                member.spellRegenAccumulator -= static_cast<float>(spellAmount);
                member.spellPoints = std::min(
                    std::max(member.spellPoints, reachableMaximumSpellPoints(memberIndex)),
                    member.spellPoints + spellAmount);
            }
            else if (spellAmount < 0)
            {
                member.spellRegenAccumulator -= static_cast<float>(spellAmount);
                member.spellPoints = std::max(0, member.spellPoints + spellAmount);
            }
        }
    }
}

bool Party::applyRecoveryToMember(size_t memberIndex, float recoverySeconds)
{
    Character *pMember = combatant(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    pMember->recoverySecondsRemaining = std::max(pMember->recoverySecondsRemaining, std::max(0.0f, recoverySeconds));
    return true;
}

bool Party::applyRecoveryToActiveMember(float recoverySeconds)
{
    return applyRecoveryToMember(m_activeMemberIndex, recoverySeconds);
}

bool Party::switchToNextReadyMember()
{
    if (m_members.empty())
    {
        return false;
    }

    // The members, then the hirelings (MM9's rotation runs over every slot); without hirelings, the members only.
    const size_t count = combatantCount();
    const size_t currentIndex = activeCombatantIndex();

    for (size_t offset = 1; offset <= count; ++offset)
    {
        const size_t candidateIndex = (currentIndex + offset) % count;

        const Character *pCandidate = combatant(candidateIndex);

        if (pCandidate != nullptr && GameMechanics::canTakeGameplayAction(*pCandidate))
        {
            setActiveCombatantIndex(candidateIndex);
            return true;
        }
    }

    return false;
}

void Party::applyPartyBuff(
    PartyBuffId buffId,
    float durationSeconds,
    int power,
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    uint32_t casterMemberIndex)
{
    PartyBuffState &buff = m_partyBuffs[static_cast<size_t>(buffId)];
    buff.remainingSeconds = std::max(buff.remainingSeconds, std::max(0.0f, durationSeconds));
    buff.spellId = spellId;
    buff.skillLevel = skillLevel;
    buff.skillMastery = skillMastery;
    buff.power = power;
    buff.casterMemberIndex = casterMemberIndex;
    rebuildMagicalBonusesFromBuffs();
}

void Party::applyCharacterBuff(
    size_t memberIndex,
    CharacterBuffId buffId,
    float durationSeconds,
    int power,
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    uint32_t casterMemberIndex)
{
    std::array<CharacterBuffState, CharacterBuffCount> *pBuffs = combatantBuffs(memberIndex);

    if (pBuffs == nullptr)
    {
        return;
    }

    CharacterBuffState &buff = (*pBuffs)[static_cast<size_t>(buffId)];
    buff.remainingSeconds = std::max(buff.remainingSeconds, std::max(0.0f, durationSeconds));
    buff.spellId = spellId;
    buff.skillLevel = skillLevel;
    buff.skillMastery = skillMastery;
    buff.power = power;
    buff.casterMemberIndex = casterMemberIndex;
    rebuildMagicalBonusesFromBuffs();
}

void Party::applyTemporaryPrimaryStatBonus(uint32_t statIndex, int power, float durationSeconds)
{
    if (statIndex >= 6 || power <= 0 || durationSeconds <= 0.0f)
    {
        return;
    }

    for (Character &member : m_members)
    {
        TimedPrimaryStatBonus &bonus = member.timedPrimaryStatBonuses[statIndex];
        bonus.power += power;
        bonus.remainingSeconds = std::max(bonus.remainingSeconds, durationSeconds);
    }
    rebuildMagicalBonusesFromBuffs();
}

void Party::clearPartyBuff(PartyBuffId buffId)
{
    m_partyBuffs[static_cast<size_t>(buffId)] = {};
    rebuildMagicalBonusesFromBuffs();
}

void Party::clearCharacterBuff(size_t memberIndex, CharacterBuffId buffId)
{
    std::array<CharacterBuffState, CharacterBuffCount> *pBuffs = combatantBuffs(memberIndex);

    if (pBuffs == nullptr)
    {
        return;
    }

    (*pBuffs)[static_cast<size_t>(buffId)] = {};
    rebuildMagicalBonusesFromBuffs();
}

bool Party::clearDispellableBuffs()
{
    bool cleared = false;

    for (PartyBuffId buffId : {
             PartyBuffId::TorchLight,
             PartyBuffId::WizardEye,
             PartyBuffId::FeatherFall,
             PartyBuffId::DetectLife,
             PartyBuffId::WaterWalk,
             PartyBuffId::Fly,
             PartyBuffId::Invisibility,
             PartyBuffId::Stoneskin,
             PartyBuffId::DayOfGods,
             PartyBuffId::ProtectionFromMagic,
             PartyBuffId::FireResistance,
             PartyBuffId::WaterResistance,
             PartyBuffId::AirResistance,
             PartyBuffId::EarthResistance,
             PartyBuffId::MindResistance,
             PartyBuffId::BodyResistance,
             PartyBuffId::Shield,
             PartyBuffId::Heroism,
             PartyBuffId::Haste,
             PartyBuffId::Immolation})
    {
        const size_t buffIndex = static_cast<size_t>(buffId);
        cleared = m_partyBuffs[buffIndex].active() || cleared;
        m_partyBuffs[buffIndex] = {};
    }

    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        for (CharacterBuffId buffId : DispellableCharacterBuffs)
        {
            const size_t buffIndex = static_cast<size_t>(buffId);
            cleared = m_characterBuffs[memberIndex][buffIndex].active() || cleared;
            m_characterBuffs[memberIndex][buffIndex] = {};
        }
    }

    if (cleared)
    {
        rebuildMagicalBonusesFromBuffs();
    }

    return cleared;
}

bool Party::hasDispellableBuffs() const
{
    for (PartyBuffId buffId : {
             PartyBuffId::TorchLight,
             PartyBuffId::WizardEye,
             PartyBuffId::FeatherFall,
             PartyBuffId::DetectLife,
             PartyBuffId::WaterWalk,
             PartyBuffId::Fly,
             PartyBuffId::Invisibility,
             PartyBuffId::Stoneskin,
             PartyBuffId::DayOfGods,
             PartyBuffId::ProtectionFromMagic,
             PartyBuffId::FireResistance,
             PartyBuffId::WaterResistance,
             PartyBuffId::AirResistance,
             PartyBuffId::EarthResistance,
             PartyBuffId::MindResistance,
             PartyBuffId::BodyResistance,
             PartyBuffId::Shield,
             PartyBuffId::Heroism,
             PartyBuffId::Haste,
             PartyBuffId::Immolation})
    {
        if (m_partyBuffs[static_cast<size_t>(buffId)].active())
        {
            return true;
        }
    }

    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        for (CharacterBuffId buffId : DispellableCharacterBuffs)
        {
            if (m_characterBuffs[memberIndex][static_cast<size_t>(buffId)].active())
            {
                return true;
            }
        }
    }

    return false;
}

bool Party::hasPartyBuff(PartyBuffId buffId) const
{
    return partyBuff(buffId) != nullptr;
}

bool Party::hasCharacterBuff(size_t memberIndex, CharacterBuffId buffId) const
{
    return characterBuff(memberIndex, buffId) != nullptr;
}

const PartyBuffState *Party::partyBuff(PartyBuffId buffId) const
{
    const PartyBuffState &buff = m_partyBuffs[static_cast<size_t>(buffId)];
    if (buffId == PartyBuffId::WizardEye && m_cartographerWizardEye.active()
        && (!buff.active() || buff.skillMastery < SkillMastery::Expert))
    {
        return &m_cartographerWizardEye;
    }
    return buff.active() ? &buff : nullptr;
}

const CharacterBuffState *Party::characterBuff(size_t memberIndex, CharacterBuffId buffId) const
{
    const std::array<CharacterBuffState, CharacterBuffCount> *pBuffs = combatantBuffs(memberIndex);

    if (pBuffs == nullptr)
    {
        return nullptr;
    }

    const CharacterBuffState &buff = (*pBuffs)[static_cast<size_t>(buffId)];
    return buff.active() ? &buff : nullptr;
}

bool Party::blockConditionWithProtectionFromMagic(CharacterCondition condition)
{
    if (!conditionAffectedByProtectionFromMagic(condition))
    {
        return false;
    }

    PartyBuffState &buff = m_partyBuffs[static_cast<size_t>(PartyBuffId::ProtectionFromMagic)];

    if (!buff.active() || buff.power <= 0)
    {
        return false;
    }

    if (conditionRequiresGrandmasterProtectionFromMagic(condition)
        && buff.skillMastery < SkillMastery::Grandmaster)
    {
        return false;
    }

    --buff.power;

    if (buff.power < 1)
    {
        buff = {};
    }

    rebuildMagicalBonusesFromBuffs();
    return true;
}

bool Party::clearMemberCondition(size_t memberIndex, CharacterCondition condition)
{
    Character *pMember = combatant(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    pMember->conditions.reset(static_cast<size_t>(condition));
    pMember->conditionStartGameMinutes[static_cast<size_t>(condition)] = 0.0f;
    pMember->conditionExpireGameMinutes[static_cast<size_t>(condition)] = 0.0f;
    return true;
}

bool Party::applyMemberCondition(size_t memberIndex, CharacterCondition condition)
{
    return applyMemberCondition(memberIndex, condition, m_gameMinutes);
}

bool Party::applyMemberCondition(size_t memberIndex, CharacterCondition condition, float gameMinutes)
{
    return applyMemberCondition(memberIndex, condition, gameMinutes, 0.0f);
}

bool Party::applyMemberCondition(
    size_t memberIndex, CharacterCondition condition, float gameMinutes, float expireGameMinutes)
{
    Character *pMember = combatant(memberIndex);

    if (pMember == nullptr || hasConditionImmunity(*pMember, condition))
    {
        return false;
    }

    const bool alreadyHadCondition = pMember->conditions.test(static_cast<size_t>(condition));
    pMember->conditions.set(static_cast<size_t>(condition));
    float &expire = pMember->conditionExpireGameMinutes[static_cast<size_t>(condition)];

    if (!alreadyHadCondition)
    {
        expire = std::max(0.0f, expireGameMinutes);
    }
    else if (expire > 0.0f)
    {
        expire = expireGameMinutes > 0.0f ? std::max(expire, expireGameMinutes) : 0.0f;
    }

    if (!alreadyHadCondition)
    {
        pMember->conditionStartGameMinutes[static_cast<size_t>(condition)] = std::max(0.0f, gameMinutes);
        recordConditionStatistics(memberIndex, condition);

        switch (condition)
        {
            case CharacterCondition::Drunk:
                queueSpeech(memberIndex, SpeechId::Drunk);
                break;

            case CharacterCondition::Insane:
                queueSpeech(memberIndex, SpeechId::Insane);
                break;

            case CharacterCondition::Cursed:
                queueSpeech(memberIndex, SpeechId::Cursed);
                break;

            case CharacterCondition::Fear:
                queueSpeech(memberIndex, SpeechId::AfraidSilent);
                break;

            default:
                break;
        }
    }

    rules().combat.characterConditionApplied(*this, memberIndex, condition);
    return true;
}

bool Party::hasMemberConditionImmunity(size_t memberIndex, CharacterCondition condition) const
{
    const Character *pMember = combatant(memberIndex);
    return pMember != nullptr && hasConditionImmunity(*pMember, condition);
}

bool Party::healMember(size_t memberIndex, int amount)
{
    Character *pMember = combatant(memberIndex);

    if (pMember == nullptr || amount <= 0 || isDeadOrEradicated(*pMember))
    {
        return false;
    }

    // MM9: any heal wakes a knocked-out hireling (MM9_HIRELINGS.md 9.3).
    if (isHirelingCombatant(memberIndex))
    {
        const int previousHealth = pMember->health;
        pMember->health =
            std::min(pMember->health + amount, std::max(previousHealth, reachableMaximumHealth(memberIndex)));
        updateHirelingKnockOut(*pMember);
        return pMember->health > previousHealth;
    }

    // A heal keeps negative HP: a member knocked below zero wakes only once the whole deficit is healed, as in the
    // original games (SKL-1, FSPS-2-2).
    // Up to what the member's auras leave (MAW's legendary 32), never lowering HP the clamp has not caught up with.
    const int previousHealth = pMember->health;
    pMember->health =
        std::min(pMember->health + amount, std::max(previousHealth, reachableMaximumHealth(memberIndex)));
    updateMemberIncapacitatedCondition(
        *pMember,
        m_characterBuffs[memberIndex][static_cast<size_t>(CharacterBuffId::Preservation)].active(),
        m_gameMinutes);
    return pMember->health > previousHealth;
}

void Party::adjustMemberHealth(size_t memberIndex, int amount)
{
    Character *pMember = combatant(memberIndex);

    if (pMember == nullptr || amount == 0 || (amount > 0 && isDeadOrEradicated(*pMember)))
    {
        return;
    }

    pMember->health = std::min(pMember->health + amount, effectiveMaximumHealth(*pMember));

    if (isHirelingCombatant(memberIndex))
    {
        updateHirelingKnockOut(*pMember);
        return;
    }

    const bool wasDead = pMember->conditions.test(static_cast<size_t>(CharacterCondition::Dead));
    updateMemberIncapacitatedCondition(
        *pMember,
        m_characterBuffs[memberIndex][static_cast<size_t>(CharacterBuffId::Preservation)].active(),
        m_gameMinutes);

    if (!wasDead && pMember->conditions.test(static_cast<size_t>(CharacterCondition::Dead)))
    {
        recordConditionStatistics(memberIndex, CharacterCondition::Dead);
    }
}

bool Party::reviveMember(size_t memberIndex, int health, bool applyWeak)
{
    Character *pMember = combatant(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Unconscious));
    pMember->conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Unconscious)] = 0.0f;
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Dead));
    pMember->conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Dead)] = 0.0f;
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Petrified));
    pMember->conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Petrified)] = 0.0f;
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Eradicated));
    pMember->conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Eradicated)] = 0.0f;
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Zombie));
    pMember->conditionStartGameMinutes[static_cast<size_t>(CharacterCondition::Zombie)] = 0.0f;
    pMember->health = std::max(1, health);

    if (applyWeak)
    {
        applyMemberCondition(memberIndex, CharacterCondition::Weak);
    }

    return true;
}

const Character *Party::activeMember() const
{
    if (m_members.empty())
    {
        return nullptr;
    }

    return &m_members[std::min(m_activeMemberIndex, m_members.size() - 1)];
}

Character *Party::activeMember()
{
    if (m_members.empty())
    {
        return nullptr;
    }

    return &m_members[std::min(m_activeMemberIndex, m_members.size() - 1)];
}

size_t Party::activeMemberIndex() const
{
    return m_members.empty() ? 0 : std::min(m_activeMemberIndex, m_members.size() - 1);
}

int Party::totalHealth() const
{
    int totalHealth = 0;

    for (const Character &member : m_members)
    {
        totalHealth += member.health;
    }

    return totalHealth;
}

int Party::totalMaxHealth() const
{
    int totalMaxHealth = 0;

    for (const Character &member : m_members)
    {
        totalMaxHealth += currentMaximumHealth(member);
    }

    return totalMaxHealth;
}

int Party::gold() const
{
    return m_gold;
}

int Party::bankGold() const
{
    return m_bankGold;
}

int Party::food() const
{
    return m_food;
}

uint32_t Party::houseStockSeed() const
{
    return m_houseStockSeed;
}

bool Party::hasFoundArtifactItem(uint32_t itemId) const
{
    return itemId != 0 && m_foundArtifactItems.contains(itemId);
}

void Party::markArtifactItemFound(uint32_t itemId)
{
    if (itemId != 0)
    {
        m_foundArtifactItems.insert(itemId);
    }
}

void Party::clearFoundArtifactItems()
{
    m_foundArtifactItems.clear();
}

bool Party::arcomageTavernCountsForChampion(uint32_t houseId)
{
    return houseId <= LastMm8ArcomageHouseId || houseId >= FirstMm7ArcomageHouseId;
}

bool Party::hasArcomageWinAt(uint32_t houseId) const
{
    return houseId != 0 && m_arcomageWonHouseIds.contains(houseId);
}

void Party::recordArcomageWin(uint32_t houseId, int goldReward, uint32_t firstWinAwardId)
{
    ++m_arcomageWinCount;

    if (houseId != 0 && m_arcomageWonHouseIds.insert(houseId).second)
    {
        if (goldReward > 0)
        {
            addGold(goldReward, GoldReason::Event);
        }

        if (firstWinAwardId != 0)
        {
            addAward(firstWinAwardId);
        }

        const bool wonAllMm8Taverns = hasWonAllMm8ArcomageTaverns(m_arcomageWonHouseIds);
        const bool wonAllMm7Taverns = hasWonAllMm7ArcomageTaverns(m_arcomageWonHouseIds);

        // Every tavern of one continent, not wins counted across continents.
        if (wonAllMm8Taverns || wonAllMm7Taverns)
        {
            addAward(ArcomageChampionAwardId);
        }

        if (wonAllMm8Taverns)
        {
            setQuestBit(Mm8ArcomageChampionQBit, true);
        }

        if (wonAllMm7Taverns)
        {
            setQuestBit(Mm7ArcomageChampionQBit, true);
        }
    }
}

void Party::recordArcomageLoss()
{
    ++m_arcomageLossCount;
}

uint32_t Party::arcomageWinCount() const
{
    return m_arcomageWinCount;
}

const std::vector<WorldCompletionRecord> &Party::worldCompletions() const
{
    return m_worldCompletions;
}

const WorldCompletionRecord *Party::findWorldCompletion(const std::string &certificateId) const
{
    for (const WorldCompletionRecord &record : m_worldCompletions)
    {
        if (record.certificateId == certificateId)
        {
            return &record;
        }
    }

    return nullptr;
}

void Party::addWorldCompletion(const WorldCompletionRecord &record)
{
    if (findWorldCompletion(record.certificateId) == nullptr)
    {
        m_worldCompletions.push_back(record);
    }
}

bool Party::worldCompletionsUntracked() const
{
    return m_worldCompletionsUntracked;
}

void Party::clearWorldCompletionsUntracked()
{
    m_worldCompletionsUntracked = false;
}

uint32_t Party::arcomageLossCount() const
{
    return m_arcomageLossCount;
}

Party::HouseStockState *Party::houseStockState(uint32_t houseId)
{
    const std::unordered_map<uint32_t, HouseStockState>::iterator stateIt = m_houseStockStates.find(houseId);
    return stateIt != m_houseStockStates.end() ? &stateIt->second : nullptr;
}

const Party::HouseStockState *Party::houseStockState(uint32_t houseId) const
{
    const std::unordered_map<uint32_t, HouseStockState>::const_iterator stateIt = m_houseStockStates.find(houseId);
    return stateIt != m_houseStockStates.end() ? &stateIt->second : nullptr;
}

Party::HouseStockState &Party::ensureHouseStockState(uint32_t houseId)
{
    HouseStockState &state = m_houseStockStates[houseId];
    state.houseId = houseId;
    return state;
}

void Party::clearHouseStockStates()
{
    m_houseStockStates.clear();
}

size_t Party::inventoryItemCount() const
{
    size_t itemCount = 0;

    for (const Character &member : m_members)
    {
        itemCount += member.inventoryItemCount();
    }

    return itemCount;
}

size_t Party::usedInventoryCells() const
{
    size_t usedCells = 0;

    for (const Character &member : m_members)
    {
        usedCells += member.usedInventoryCells();
    }

    return usedCells;
}

size_t Party::inventoryCapacity() const
{
    size_t capacity = 0;

    for (const Character &member : m_members)
    {
        capacity += member.inventoryCapacity();
    }

    return capacity;
}

uint32_t Party::waterDamageTicks() const
{
    return m_waterDamageTicks;
}

uint32_t Party::burningDamageTicks() const
{
    return m_burningDamageTicks;
}

uint32_t Party::splashCount() const
{
    return m_splashCount;
}

uint32_t Party::landingSoundCount() const
{
    return m_landingSoundCount;
}

uint32_t Party::hardLandingSoundCount() const
{
    return m_hardLandingSoundCount;
}

float Party::lastFallDamageDistance() const
{
    return m_lastFallDamageDistance;
}

const std::string &Party::lastStatus() const
{
    return m_lastStatus;
}

const std::vector<Party::PendingAudioRequest> &Party::pendingAudioRequests() const
{
    return m_pendingAudioRequests;
}

void Party::clearPendingAudioRequests()
{
    m_pendingAudioRequests.clear();
}

void Party::queueSound(SoundId soundId)
{
    if (soundId == SoundId::None)
    {
        return;
    }

    PendingAudioRequest request = {};
    request.kind = PendingAudioRequest::Kind::Sound;
    request.soundId = soundId;
    m_pendingAudioRequests.push_back(request);
}

void Party::queueSpeech(size_t memberIndex, SpeechId speechId)
{
    if (speechId == SpeechId::None || memberIndex >= m_members.size())
    {
        return;
    }

    PendingAudioRequest request = {};
    request.kind = PendingAudioRequest::Kind::Speech;
    request.speechId = speechId;
    request.memberIndex = memberIndex;
    m_pendingAudioRequests.push_back(request);
}

SoundId Party::resolveDamageImpactSoundForMember(size_t memberIndex) const
{
    if (memberIndex >= m_members.size() || m_pItemTable == nullptr)
    {
        return SoundId::DullStrike;
    }

    const std::optional<InventoryItem> armor = equippedItem(memberIndex, EquipmentSlot::Armor);

    if (!armor.has_value())
    {
        return SoundId::DullStrike;
    }

    const ItemDefinition *pArmorDefinition = m_pItemTable->get(armor->objectDescriptionId);

    if (pArmorDefinition == nullptr)
    {
        return SoundId::DullStrike;
    }

    if (pArmorDefinition->skillGroup == "Chain")
    {
        static constexpr std::array<SoundId, 4> MetalArmorSounds = {
            SoundId::MetalArmorStrike01,
            SoundId::MetalArmorStrike02,
            SoundId::MetalArmorStrike03,
            SoundId::MetalVsMetal01,
        };
        return pickRandomSoundId(MetalArmorSounds);
    }

    if (pArmorDefinition->skillGroup == "Plate")
    {
        static constexpr std::array<SoundId, 4> PlateArmorSounds = {
            SoundId::MetalArmorStrike03,
            SoundId::MetalArmorStrike02,
            SoundId::MetalArmorStrike01,
            SoundId::MetalVsMetal01,
        };
        return pickRandomSoundId(PlateArmorSounds);
    }

    static constexpr std::array<SoundId, 4> DullArmorSounds = {
        SoundId::DullArmorStrike01,
        SoundId::DullArmorStrike02,
        SoundId::DullArmorStrike03,
        SoundId::DullStrike,
    };
    return pickRandomSoundId(DullArmorSounds);
}

void Party::applyPartyBuffBonuses(Character &member) const
{
    const auto applyResistanceBonus =
        [this, &member](PartyBuffId buffId, auto CharacterResistanceSet::*field)
        {
            const PartyBuffState &buff = m_partyBuffs[static_cast<size_t>(buffId)];

            if (!buff.active())
            {
                return;
            }

            member.magicalBonuses.resistances.*field += buff.power;
        };

    applyResistanceBonus(PartyBuffId::FireResistance, &CharacterResistanceSet::fire);
    applyResistanceBonus(PartyBuffId::WaterResistance, &CharacterResistanceSet::water);
    applyResistanceBonus(PartyBuffId::AirResistance, &CharacterResistanceSet::air);
    applyResistanceBonus(PartyBuffId::EarthResistance, &CharacterResistanceSet::earth);
    applyResistanceBonus(PartyBuffId::MindResistance, &CharacterResistanceSet::mind);
    applyResistanceBonus(PartyBuffId::BodyResistance, &CharacterResistanceSet::body);

    if (const PartyBuffState *pBuff = partyBuff(PartyBuffId::Stoneskin))
    {
        member.magicalBonuses.armorClass += pBuff->power;
    }

    // Heroism strengthens melee blows only: MM8 adds it to the melee damage stat alone (MM8-Rel.exe 0x490b48).
    if (const PartyBuffState *pBuff = partyBuff(PartyBuffId::Heroism))
    {
        member.magicalBonuses.meleeDamage += pBuff->power;
    }

    if (partyBuff(PartyBuffId::Haste) != nullptr)
    {
        member.attackRecoveryReductionTicks += 25;
    }

    if (partyBuff(PartyBuffId::Shield) != nullptr)
    {
        member.halfMissileDamage = true;
    }

    if (const PartyBuffState *pBuff = partyBuff(PartyBuffId::DayOfGods))
    {
        member.magicalBonuses.might += pBuff->power;
        member.magicalBonuses.intellect += pBuff->power;
        member.magicalBonuses.personality += pBuff->power;
        member.magicalBonuses.endurance += pBuff->power;
        member.magicalBonuses.speed += pBuff->power;
        member.magicalBonuses.accuracy += pBuff->power;
        member.magicalBonuses.luck += pBuff->power;
    }

    if (const PartyBuffState *pBuff = partyBuff(PartyBuffId::ProtectionFromMagic);
        pBuff != nullptr && rules().spells.protectionFromMagicRaisesResistances())
    {
        member.magicalBonuses.resistances.fire += pBuff->power;
        member.magicalBonuses.resistances.air += pBuff->power;
        member.magicalBonuses.resistances.water += pBuff->power;
        member.magicalBonuses.resistances.earth += pBuff->power;
        member.magicalBonuses.resistances.mind += pBuff->power;
        member.magicalBonuses.resistances.body += pBuff->power;
        member.magicalBonuses.resistances.spirit += pBuff->power;
    }

    if (const PartyBuffState *pBuff = partyBuff(PartyBuffId::Glamour))
    {
        member.merchantBonus += pBuff->power;
        member.glamourPower = pBuff->power;
        member.glamourMastery = pBuff->skillMastery;
    }
}

void Party::applyCharacterBuffBonuses(
    Character &member,
    const std::array<CharacterBuffState, CharacterBuffCount> &buffs) const
{
    const auto activeBuff = [&buffs](CharacterBuffId buffId) -> const CharacterBuffState *
    {
        const CharacterBuffState &buff = buffs[static_cast<size_t>(buffId)];
        return buff.active() ? &buff : nullptr;
    };

    if (const CharacterBuffState *pBuff = activeBuff(CharacterBuffId::Bless))
    {
        member.magicalBonuses.meleeAttack += pBuff->power;
        member.magicalBonuses.rangedAttack += pBuff->power;
    }

    if (const CharacterBuffState *pBuff = activeBuff(CharacterBuffId::Fate))
    {
        member.magicalBonuses.meleeAttack += pBuff->power;
        member.magicalBonuses.rangedAttack += pBuff->power;
    }

    if (const CharacterBuffState *pBuff = activeBuff(CharacterBuffId::Hammerhands))
    {
        member.magicalBonuses.meleeDamage += pBuff->power;
    }

    if (const CharacterBuffState *pBuff = activeBuff(CharacterBuffId::Mistform))
    {
        static_cast<void>(pBuff);
        member.physicalAttackDisabled = true;
        const float share = rules().combat.mistFormPhysicalShare();
        member.physicalDamageImmune = share <= 0.0f;
        member.mistFormPhysicalShare = share;
    }

    if (const CharacterBuffState *pBuff = activeBuff(CharacterBuffId::Glamour))
    {
        member.merchantBonus += pBuff->power;

        // With an event's party Glamour as well, the stronger one is the member's Glamour; the other adds plainly.
        if (pBuff->skillMastery > member.glamourMastery
            || (pBuff->skillMastery == member.glamourMastery && pBuff->power > member.glamourPower))
        {
            member.glamourPower = pBuff->power;
            member.glamourMastery = pBuff->skillMastery;
        }
    }

    if (activeBuff(CharacterBuffId::Haste) != nullptr && partyBuff(PartyBuffId::Haste) == nullptr)
    {
        member.attackRecoveryReductionTicks += 25;
    }

    if (const CharacterBuffState *pBuff = activeBuff(CharacterBuffId::Heroism))
    {
        member.magicalBonuses.meleeDamage += pBuff->power;
    }

    if (activeBuff(CharacterBuffId::Shield) != nullptr)
    {
        member.halfMissileDamage = true;
    }

    if (const CharacterBuffState *pBuff = activeBuff(CharacterBuffId::Stoneskin))
    {
        member.magicalBonuses.armorClass += pBuff->power;
    }

    if (activeBuff(CharacterBuffId::WaterBreathing) != nullptr)
    {
        member.waterWalking = true;
    }

    const std::array<std::pair<CharacterBuffId, int CharacterStatBonuses::*>, 7> tempStatBuffs = {{
        {CharacterBuffId::TempMight, &CharacterStatBonuses::might},
        {CharacterBuffId::TempIntellect, &CharacterStatBonuses::intellect},
        {CharacterBuffId::TempPersonality, &CharacterStatBonuses::personality},
        {CharacterBuffId::TempEndurance, &CharacterStatBonuses::endurance},
        {CharacterBuffId::TempSpeed, &CharacterStatBonuses::speed},
        {CharacterBuffId::TempAccuracy, &CharacterStatBonuses::accuracy},
        {CharacterBuffId::TempLuck, &CharacterStatBonuses::luck},
    }};

    for (const auto &[buffId, field] : tempStatBuffs)
    {
        if (const CharacterBuffState *pBuff = activeBuff(buffId))
        {
            member.magicalBonuses.*field += pBuff->power;
        }
    }

    const std::array<std::pair<CharacterBuffId, int CharacterResistanceSet::*>, 6> resistanceBuffs = {{
        {CharacterBuffId::FireResistance, &CharacterResistanceSet::fire},
        {CharacterBuffId::AirResistance, &CharacterResistanceSet::air},
        {CharacterBuffId::WaterResistance, &CharacterResistanceSet::water},
        {CharacterBuffId::EarthResistance, &CharacterResistanceSet::earth},
        {CharacterBuffId::MindResistance, &CharacterResistanceSet::mind},
        {CharacterBuffId::BodyResistance, &CharacterResistanceSet::body},
    }};

    for (const auto &[buffId, field] : resistanceBuffs)
    {
        if (const CharacterBuffState *pBuff = activeBuff(buffId))
        {
            member.magicalBonuses.resistances.*field += pBuff->power;
        }
    }
}

void Party::applyBuffBonusesToHirelings()
{
    // The party's buffs and their own reach the hirelings as the members' (MM9's party spells cover every slot); they
    // have no items, followers, skills or class to add.
    for (Mm9PartyHireling &hireling : m_mm9Hirelings)
    {
        Character &character = hireling.character;
        character.hiredNpcSkillBonuses.clear();
        resetMagicalState(character);
        applyPartyBuffBonuses(character);
        applyCharacterBuffBonuses(character, hireling.buffs);
        // A hireling has no primary stats (Mm9HirelingPrimaryStat): Day of the Gods and the stat buffs give it nothing,
        // else they would leak into the derived armour class (speed), saves (luck) and the rest.
        character.magicalBonuses.might = 0;
        character.magicalBonuses.intellect = 0;
        character.magicalBonuses.personality = 0;
        character.magicalBonuses.endurance = 0;
        character.magicalBonuses.speed = 0;
        character.magicalBonuses.accuracy = 0;
        character.magicalBonuses.luck = 0;
    }
}

void Party::rebuildMagicalBonusesFromBuffs()
{
    m_cartographerWizardEye = {};
    const std::span<const HiredNpcFollower> followers = activeHiredNpcFollowers();
    if (hiredNpcHasProfession(followers, 38))
    {
        m_cartographerWizardEye.remainingSeconds = std::numeric_limits<float>::infinity();
        m_cartographerWizardEye.spellId = spellIdValue(SpellId::WizardEye);
        m_cartographerWizardEye.skillLevel = 4;
        m_cartographerWizardEye.skillMastery = SkillMastery::Expert;
        m_cartographerWizardEye.power = 2;
    }
    std::unordered_map<std::string, int> followerSkills;
    if (!followers.empty())
    {
        for (const std::string &skillName : allCanonicalSkillNames())
        {
            const int bonus = hiredNpcSkillBonus(
                followers, skillName, !rules().skills.followerSkillBonusesStack(), &rules().skills);
            if (bonus != 0)
            {
                followerSkills[skillName] = bonus;
            }
        }
    }

    // MM9's Alberik (+6 Merchant) and Beagan (+4 Disarm Traps, Perception): only on a skill the member has
    // (cshell@0x1004dd3c), through the members' skill bonus as the followers'.
    const std::vector<Mm9HirelingSkillBonus> hirelingSkills = mm9HirelingPassives().skillBonuses;

    for (Character &member : m_members)
    {
        member.hiredNpcSkillBonuses = followerSkills;
        std::erase_if(member.hiredNpcSkillBonuses,
            [this, &member](const std::pair<const std::string, int> &bonus)
            { return rules().skills.followerSkillBonusNeedsSkill(bonus.first) && !member.hasSkill(bonus.first); });

        for (const Mm9HirelingSkillBonus &bonus : hirelingSkills)
        {
            if (member.hasSkill(bonus.skillName))
            {
                member.hiredNpcSkillBonuses[canonicalSkillName(bonus.skillName)] += bonus.amount;
            }
        }
        resetMagicalState(member);
        member.magicalBonuses.luck += hiredNpcPrimaryStatBonus(followers, "Luck");
        member.magicalBonuses.resistances.fire += hiredNpcResistanceBonus(followers, "Fire");
        member.magicalBonuses.resistances.air += hiredNpcResistanceBonus(followers, "Air");
        member.magicalBonuses.resistances.water += hiredNpcResistanceBonus(followers, "Water");
        member.magicalBonuses.resistances.earth += hiredNpcResistanceBonus(followers, "Earth");

        // Potions that add skill levels for a while (MAW's Meditation potion).
        for (const TimedPotionEffect &effect : member.rulesetState.potionEffects)
        {
            const std::optional<std::string> skillName = skillNameForSkillId(effect.key);

            if (effect.kind == TimedPotionEffect::Kind::SkillBonus && effect.remainingSeconds > 0 && skillName)
            {
                member.itemSkillBonuses[canonicalSkillName(*skillName)] += effect.amount;
            }
        }

        const std::array<int CharacterStatBonuses::*, 6> primaryStats = {
            &CharacterStatBonuses::might,
            &CharacterStatBonuses::intellect,
            &CharacterStatBonuses::personality,
            &CharacterStatBonuses::endurance,
            &CharacterStatBonuses::speed,
            &CharacterStatBonuses::accuracy,
        };
        for (size_t statIndex = 0; statIndex < primaryStats.size(); ++statIndex)
        {
            const TimedPrimaryStatBonus &bonus = member.timedPrimaryStatBonuses[statIndex];
            if (bonus.remainingSeconds > 0.0f)
            {
                member.magicalBonuses.*primaryStats[statIndex] += bonus.power;
            }
        }
    }

    for (Character &member : m_members)
    {
        member.healthRegenPerSecond += rules().skills.regenerationHealthPerSecond(member);
    }

    for (Character &member : m_members)
    {
        applyPartyBuffBonuses(member);
    }

    for (size_t memberIndex = 0; memberIndex < m_members.size() && memberIndex < m_characterBuffs.size(); ++memberIndex)
    {
        applyCharacterBuffBonuses(m_members[memberIndex], m_characterBuffs[memberIndex]);
    }

    const auto applyEquippedItemEnchant =
        [this](Character &member, uint32_t itemId, const EquippedItemRuntimeState &runtimeState)
        {
            if (itemId == 0 || runtimeState.broken)
            {
                return;
            }

            const ItemDefinition *pItemDefinition = m_pItemTable->get(itemId);

            if (pItemDefinition == nullptr)
            {
                return;
            }

            rules().items.applyEquippedEnchantEffects(
                *pItemDefinition,
                runtimeState,
                m_pStandardItemEnchantTable,
                m_pSpecialItemEnchantTable,
                member,
                member);

            // Its Workshop mod's effect, as the item's own (personal shield to the armour's pool).
            if (const WorkshopModDefinition *pMod = runtimeState.workshopModId != 0
                    ? m_pItemTable->workshopMod(runtimeState.workshopModId) : nullptr)
            {
                ItemEnchantRuntime::applyContentEffect(pMod->effect, member);
                member.armorShieldPoints += pMod->effect.personalShield;
            }
        };

    if (m_pItemTable != nullptr)
    {
        for (Character &member : m_members)
        {
            if (member.equipment.offHand != 0 && !member.equipmentRuntime.offHand.broken)
            {
                const ItemDefinition *pOffHand = m_pItemTable->get(member.equipment.offHand);
                const CharacterSkill *pShieldSkill = member.findSkill("Shield");

                if (pOffHand != nullptr
                    && pOffHand->skillGroup == "Shield"
                    && pShieldSkill != nullptr
                    && pShieldSkill->mastery >= SkillMastery::Grandmaster)
                {
                    member.halfMissileDamage = true;
                }
            }

            applyEquippedItemEnchant(member, member.equipment.offHand, member.equipmentRuntime.offHand);
            applyEquippedItemEnchant(member, member.equipment.mainHand, member.equipmentRuntime.mainHand);
            applyEquippedItemEnchant(member, member.equipment.bow, member.equipmentRuntime.bow);
            applyEquippedItemEnchant(member, member.equipment.armor, member.equipmentRuntime.armor);
            applyEquippedItemEnchant(member, member.equipment.helm, member.equipmentRuntime.helm);
            applyEquippedItemEnchant(member, member.equipment.belt, member.equipmentRuntime.belt);
            applyEquippedItemEnchant(member, member.equipment.cloak, member.equipmentRuntime.cloak);
            applyEquippedItemEnchant(member, member.equipment.gauntlets, member.equipmentRuntime.gauntlets);
            applyEquippedItemEnchant(member, member.equipment.boots, member.equipmentRuntime.boots);
            applyEquippedItemEnchant(member, member.equipment.amulet, member.equipmentRuntime.amulet);
            applyEquippedItemEnchant(member, member.equipment.ring1, member.equipmentRuntime.ring1);
            applyEquippedItemEnchant(member, member.equipment.ring2, member.equipmentRuntime.ring2);
            applyEquippedItemEnchant(member, member.equipment.ring3, member.equipmentRuntime.ring3);
            applyEquippedItemEnchant(member, member.equipment.ring4, member.equipmentRuntime.ring4);
            applyEquippedItemEnchant(member, member.equipment.ring5, member.equipmentRuntime.ring5);
            applyEquippedItemEnchant(member, member.equipment.ring6, member.equipmentRuntime.ring6);

            const std::array<std::pair<uint32_t, bool>, 16> equippedItems = {{
                {member.equipment.offHand, member.equipmentRuntime.offHand.broken},
                {member.equipment.mainHand, member.equipmentRuntime.mainHand.broken},
                {member.equipment.bow, member.equipmentRuntime.bow.broken},
                {member.equipment.armor, member.equipmentRuntime.armor.broken},
                {member.equipment.helm, member.equipmentRuntime.helm.broken},
                {member.equipment.belt, member.equipmentRuntime.belt.broken},
                {member.equipment.cloak, member.equipmentRuntime.cloak.broken},
                {member.equipment.gauntlets, member.equipmentRuntime.gauntlets.broken},
                {member.equipment.boots, member.equipmentRuntime.boots.broken},
                {member.equipment.amulet, member.equipmentRuntime.amulet.broken},
                {member.equipment.ring1, member.equipmentRuntime.ring1.broken},
                {member.equipment.ring2, member.equipmentRuntime.ring2.broken},
                {member.equipment.ring3, member.equipmentRuntime.ring3.broken},
                {member.equipment.ring4, member.equipmentRuntime.ring4.broken},
                {member.equipment.ring5, member.equipmentRuntime.ring5.broken},
                {member.equipment.ring6, member.equipmentRuntime.ring6.broken},
            }};
            std::unordered_map<std::string, size_t> equippedSetPieceCounts;

            for (const auto &[itemId, broken] : equippedItems)
            {
                const ItemDefinition *pItem = itemId != 0 && !broken ? m_pItemTable->get(itemId) : nullptr;

                if (pItem != nullptr && !pItem->setId.empty())
                {
                    ++equippedSetPieceCounts[pItem->setId];
                }
            }

            for (const ItemSetBonusDefinition &setBonus : m_pItemTable->setBonuses())
            {
                const auto foundPieceCount = equippedSetPieceCounts.find(setBonus.setId);

                if (foundPieceCount != equippedSetPieceCounts.end()
                    && foundPieceCount->second >= setBonus.requiredPieceCount)
                {
                    ItemEnchantRuntime::applyContentEffect(setBonus.effect, member);
                }
            }
        }

        for (Character &member : m_members)
        {
            applyImplants(member, *m_pItemTable);
        }

        for (const Character &owner : m_members)
        {
            for (const InventoryItem &item : owner.inventory)
            {
                const ItemDefinition *pItem = m_pItemTable->get(item.objectDescriptionId);

                if (pItem == nullptr
                    || std::find(
                        pItem->contentEffect.flags.begin(),
                        pItem->contentEffect.flags.end(),
                        "CarriedPartyEffect") == pItem->contentEffect.flags.end())
                {
                    continue;
                }

                for (Character &partyMember : m_members)
                {
                    ItemEnchantRuntime::applyContentEffect(pItem->contentEffect, partyMember);
                }
            }
        }

        const bool partyEndurancePenalty = std::any_of(
            m_members.begin(),
            m_members.end(),
            [](const Character &member)
            {
                return member.equippedItemEffectFlags.contains("PartyEnduranceMinus40");
            });

        if (partyEndurancePenalty)
        {
            for (Character &member : m_members)
            {
                member.magicalBonuses.endurance -= 40;
            }
        }
    }

    for (Character &member : m_members)
    {
        rules().skills.applyStatBonuses(member);
        applyMagicalPrimaryStatResourceBonuses(member, m_pClassMultiplierTable);
        rules().classes.applyClassBonuses(member);
        rules().skills.applyResourceBonuses(member);
        clampCurrentResourcesToMaximum(member);
        // Emitters grow by a share per Shield Tech rank; armour, belts and implants add as they are.
        const CharacterSkill *pShieldTech = member.findSkill("ShieldTech");
        const float emitterScale =
            1.0f + float(pShieldTech != nullptr ? pShieldTech->level : 0) * personalShieldRules().emitterBonusPerRank;
        member.personalShieldCapacity = member.armorShieldPoints
            + int(std::lround(float(member.emitterShieldPoints) * emitterScale)) + member.temporaryShieldPoints;
        member.personalShield = std::min(member.personalShield, float(member.personalShieldCapacity));
    }

    applyBuffBonusesToHirelings();
}

void Party::setPersonalShieldRules(const PartyShieldRules *pRules)
{
    m_pPersonalShieldRules = pRules;
}

const PartyShieldRules &Party::personalShieldRules() const
{
    static const PartyShieldRules defaults;
    return m_pPersonalShieldRules != nullptr ? *m_pPersonalShieldRules : defaults;
}

Party::PersonalShieldHit Party::absorbPersonalShieldHit(size_t memberIndex, int damage)
{
    PersonalShieldHit result;
    result.passedDamage = damage;
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || damage <= 0 || pMember->personalShieldCapacity <= 0)
    {
        return result;
    }

    pMember->personalShieldSecondsSinceDamage = 0.0f;

    if (pMember->personalShield <= 0.0f)
    {
        return result;
    }

    // Unlike a monster's shield, what the hit carries beyond the pool reaches the body: a weak shield does not stop
    // a cannon strike (COMBAT.md, Ion cannons).
    result.absorbed = true;
    const float taken = std::min(float(damage), pMember->personalShield);
    pMember->personalShield -= taken;
    result.passedDamage = damage - int(std::lround(taken));

    if (pMember->personalShield <= 0.5f)
    {
        pMember->personalShield = 0.0f;
        pMember->personalShieldSecondsSinceBreak = 0.0f;
        result.broke = true;
    }

    return result;
}

bool Party::chargePersonalShield(size_t memberIndex)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    if (pMember->personalShieldCapacity - pMember->temporaryShieldPoints <= 0)
    {
        // No shield of its own: the cell's temporary one (renewed if it already has one).
        const PartyShieldRules &rules = personalShieldRules();

        if (rules.shieldCellPoints <= 0)
        {
            return false;
        }

        pMember->temporaryShieldPoints = rules.shieldCellPoints;
        pMember->temporaryShieldSecondsRemaining = rules.shieldCellSeconds;
        pMember->personalShieldCapacity = rules.shieldCellPoints;
    }

    pMember->personalShieldInitialized = true;
    pMember->personalShield = float(pMember->personalShieldCapacity);
    pMember->personalShieldSecondsSinceBreak = -1.0f;
    return true;
}

bool Party::burstPersonalShields()
{
    const float fraction = personalShieldRules().shieldBurstFraction;
    bool charged = false;

    for (Character &member : m_members)
    {
        if (member.personalShieldCapacity > 0)
        {
            member.personalShieldInitialized = true;
            member.personalShield = std::min(float(member.personalShieldCapacity),
                member.personalShield + float(member.personalShieldCapacity) * fraction);
            member.personalShieldSecondsSinceBreak = -1.0f;
            charged = true;
        }
    }

    return charged;
}

void Party::updatePersonalShields(float deltaSeconds)
{
    const PartyShieldRules &rules = personalShieldRules();

    for (Character &member : m_members)
    {
        if (member.temporaryShieldPoints > 0)
        {
            member.temporaryShieldSecondsRemaining -= deltaSeconds;

            if (member.temporaryShieldSecondsRemaining <= 0.0f)
            {
                // The cell's shield fades: its points leave the pool.
                member.personalShieldCapacity =
                    std::max(0, member.personalShieldCapacity - member.temporaryShieldPoints);
                member.personalShield = std::min(member.personalShield, float(member.personalShieldCapacity));
                member.temporaryShieldPoints = 0;
                member.temporaryShieldSecondsRemaining = 0.0f;
            }
        }

        if (member.personalShieldCapacity <= 0)
        {
            member.personalShield = 0.0f;
            member.personalShieldInitialized = true;
            continue;
        }

        if (!member.personalShieldInitialized)
        {
            // A loaded game or a fresh party: shields start full.
            member.personalShieldInitialized = true;
            member.personalShield = float(member.personalShieldCapacity);
            member.personalShieldSecondsSinceDamage = rules.regenDelaySeconds;
        }

        if (member.personalShieldSecondsSinceBreak >= 0.0f)
        {
            member.personalShieldSecondsSinceBreak = std::min(member.personalShieldSecondsSinceBreak + deltaSeconds,
                60.0f);
        }

        const CharacterSkill *pShieldTech = member.findSkill("ShieldTech");
        const float delay = std::max(0.0f, rules.regenDelaySeconds + member.shieldRegenDelaySeconds
            - (pShieldTech != nullptr && pShieldTech->mastery >= SkillMastery::Expert
                ? rules.shieldTechExpertDelayReduction : 0.0f));
        const float regenerating =
            std::min(deltaSeconds, member.personalShieldSecondsSinceDamage + deltaSeconds - delay);
        member.personalShieldSecondsSinceDamage = std::min(member.personalShieldSecondsSinceDamage + deltaSeconds,
            3600.0f);

        if (regenerating > 0.0f && member.personalShield < float(member.personalShieldCapacity) && member.health > 0)
        {
            member.personalShield = std::min(float(member.personalShieldCapacity), member.personalShield
                + float(member.personalShieldCapacity) / std::max(rules.regenSeconds, 0.05f) * regenerating);
        }
    }
}

void Party::applyDefaultStartingSkills(Character &member) const
{
    if (m_pClassSkillTable == nullptr)
    {
        return;
    }

    const std::vector<CharacterSkill> defaultSkills =
        m_pClassSkillTable->getDefaultSkillsForCharacter(member.className, member.raceId);

    for (const CharacterSkill &skill : defaultSkills)
    {
        member.skills[skill.name] = skill;
    }

    member.synchronizeInnateAbilitySpells();
}

void Party::markArtifactItemFoundIfRelevant(const InventoryItem &item)
{
    if (item.objectDescriptionId == 0)
    {
        return;
    }

    if (item.artifactId != 0)
    {
        markArtifactItemFound(item.artifactId);
        return;
    }

    if (m_pItemTable == nullptr)
    {
        return;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(item.objectDescriptionId);

    if (pItemDefinition == nullptr || !ItemRuntime::isUniquelyGeneratedRareItem(*pItemDefinition))
    {
        return;
    }

    markArtifactItemFound(pItemDefinition->itemId);
}

void Party::recordEverOwnedItemIfRelevant(const InventoryItem &item)
{
    recordEverOwnedItem(item.objectDescriptionId);
}

void Party::recordEverOwnedItemsFromCurrentState()
{
    static constexpr EquipmentSlot EquipmentSlots[] = {
        EquipmentSlot::OffHand,
        EquipmentSlot::MainHand,
        EquipmentSlot::Bow,
        EquipmentSlot::Armor,
        EquipmentSlot::Helm,
        EquipmentSlot::Belt,
        EquipmentSlot::Cloak,
        EquipmentSlot::Gauntlets,
        EquipmentSlot::Boots,
        EquipmentSlot::Amulet,
        EquipmentSlot::Ring1,
        EquipmentSlot::Ring2,
        EquipmentSlot::Ring3,
        EquipmentSlot::Ring4,
        EquipmentSlot::Ring5,
        EquipmentSlot::Ring6,
    };

    // Items the party already holds (a restored save, a new party's kit) were not found now: no statistics.
    PlaythroughStatistics *pStatistics = m_statistics.pStatistics;
    m_statistics.pStatistics = nullptr;

    for (const Character &member : m_members)
    {
        for (const InventoryItem &item : member.inventory)
        {
            recordEverOwnedItemIfRelevant(item);
        }

        for (EquipmentSlot slot : EquipmentSlots)
        {
            recordEverOwnedItem(::OpenYAMM::Game::equippedItemId(member.equipment, slot));
        }
    }

    m_statistics.pStatistics = pStatistics;
}
}
