#include "game/tables/ItemTable.h"
#include "game/items/ItemEnchantTables.h"
#include "engine/ImageAssetLoader.h"
#include "engine/Localization.h"
#include "game/party/SkillData.h"
#include "game/party/CharacterState.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/MonsterTable.h"
#include <charconv>
#include "game/StringUtils.h"

#include <algorithm>
#include <array>
#include <cerrno>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <unordered_map>
#include <unordered_set>

#include <yaml-cpp/yaml.h>

namespace OpenYAMM::Game
{
uint32_t itemSlayingKindFlag(const std::string &flag)
{
    static const std::array<std::pair<const char *, MonsterKind>, 7> Kinds = {{
        {"SlayingDemon", MonsterKind::Demon}, {"SlayingUndead", MonsterKind::Undead},
        {"SlayingDragon", MonsterKind::Dragon}, {"SlayingOgre", MonsterKind::Ogre},
        {"SlayingElemental", MonsterKind::Elemental}, {"SlayingElf", MonsterKind::Elf},
        {"SlayingTitan", MonsterKind::Titan},
    }};

    for (const auto &[pName, kind] : Kinds)
    {
        if (flag == pName)
        {
            return monsterKindFlag(kind);
        }
    }

    return 0;
}

uint32_t itemSlayingKindFlags(const ItemContentEffect &effect)
{
    uint32_t kinds = 0;

    for (const std::string &flag : effect.flags)
    {
        kinds |= itemSlayingKindFlag(flag);
    }

    return kinds;
}

namespace
{
constexpr std::array<std::string_view, ImplantEffectCount> ImplantEffectNames = {"intellect_personality", "berserk",
    "converter", "max_health", "max_sp", "all_stats", "siphon", "recovery", "fire_resistance", "armor_class", "reflect",
    "projectile_speed", "accuracy"};

// "+5" for a gain, "-3" for a cost.
std::string signedPercentText(float percent)
{
    return (percent < 0.0f ? "-" : "+") + implantPercentText(std::fabs(percent));
}
}

std::optional<ImplantEffect> parseImplantEffect(std::string_view name)
{
    for (size_t index = 0; index < ImplantEffectNames.size(); ++index)
    {
        if (ImplantEffectNames[index] == name)
        {
            return ImplantEffect(index);
        }
    }

    return std::nullopt;
}

bool implantEffectMayBeNegative(ImplantEffect effect)
{
    return effect == ImplantEffect::AllStats || effect == ImplantEffect::MaxHealth
        || effect == ImplantEffect::MaxSpellPoints;
}

uint32_t implantStageKills(const ImplantDefinition &implant, uint32_t stage, float evolveFactor)
{
    const uint32_t kills = stage >= 2 ? implant.stageTwoKills : 0;
    return uint32_t(std::lround(double(kills) * double(std::max(evolveFactor, 0.0f))));
}

uint32_t implantStage(const ImplantDefinition &implant, uint32_t kills, float evolveFactor)
{
    return kills >= implantStageKills(implant, 2, evolveFactor) ? 2 : 1;
}

std::string implantStageName(uint32_t stage)
{
    return stage >= 2 ? "II" : "I";
}

float implantEffectPercent(const ImplantShare &share, uint32_t stage, int effectLevel)
{
    const size_t index = stage >= 2 ? 1 : 0;
    const int level = std::clamp(effectLevel, 0, ImplantEffectLevelCap);
    return share.basePercent[index] + share.perLevelPercent[index] * float(level);
}

namespace
{
// A per cent with `decimals` decimals at most, trailing zeros dropped; the small epsilon rounds a half that float
// arithmetic left just below it (29.05) up, as the player expects.
std::string roundedPercentText(float percent, int decimals)
{
    if (percent < 0.0f)
    {
        return "-" + roundedPercentText(-percent, decimals);
    }

    long scale = 1;

    for (int digit = 0; digit < decimals; ++digit)
    {
        scale *= 10;
    }

    const long scaled = std::lround(double(percent) * double(scale) + 1e-3);
    std::string text = std::to_string(scaled / scale);
    std::string fraction = decimals > 0 ? std::to_string(scaled % scale) : std::string();
    fraction.insert(0, size_t(decimals) - fraction.size(), '0');

    while (!fraction.empty() && fraction.back() == '0')
    {
        fraction.pop_back();
    }

    return fraction.empty() ? text : text + "." + fraction;
}
}

std::string implantPercentText(float percent)
{
    return roundedPercentText(percent, 1);
}

std::string implantRateText(float percent)
{
    const float size = std::fabs(percent);
    const int magnitude = size > 0.0f ? int(std::floor(std::log10(double(size)) + 1e-6)) : 0;
    return roundedPercentText(percent, std::max(0, 2 - magnitude));
}

std::string implantEffectText(ImplantEffect effect, float percent, uint8_t exceptStats)
{
    const std::string amount = implantPercentText(percent);
    const std::string signedAmount = signedPercentText(percent);

    switch (effect)
    {
        case ImplantEffect::IntellectPersonality:
            return Engine::tr("+{percent} % of total Intellect and Personality", {{"percent", amount}});
        case ImplantEffect::BerserkDamage:
            return Engine::tr("+{percent} % damage while an enemy is in melee reach, which drains 5 % of maximum hit "
                "points and spell points each second", {{"percent", amount}});
        case ImplantEffect::Converter:
            return Engine::tr("{percent} % of each other attribute converted into your highest", {{"percent", amount}});
        case ImplantEffect::MaxHealth:
            return Engine::tr("{percent} % of total hit points", {{"percent", signedAmount}});
        case ImplantEffect::MaxSpellPoints:
            return Engine::tr("{percent} % of total spell points", {{"percent", signedAmount}});
        case ImplantEffect::AllStats:
        {
            if (exceptStats == 0)
            {
                return Engine::tr("{percent} % of all seven attributes", {{"percent", signedAmount}});
            }

            constexpr std::array<std::string_view, 7> StatDisplayNames = {Engine::trNoop("Might"),
                Engine::trNoop("Intellect"), Engine::trNoop("Personality"), Engine::trNoop("Endurance"),
                Engine::trNoop("Accuracy"), Engine::trNoop("Speed"), Engine::trNoop("Luck")};
            std::string spared;

            for (size_t stat = 0; stat < StatDisplayNames.size(); ++stat)
            {
                if ((exceptStats & (1u << stat)) != 0)
                {
                    spared += (spared.empty() ? "" : ", ") + Engine::tr(StatDisplayNames[stat]);
                }
            }

            return Engine::tr("{percent} % of every attribute except {stats}",
                {{"percent", signedAmount}, {"stats", spared}});
        }
        case ImplantEffect::Siphon:
            return Engine::tr("{percent} % of damage dealt returns as hit points and spell points over 2 seconds",
                {{"percent", amount}});
        case ImplantEffect::Recovery:
            return Engine::tr("{percent} % shorter recovery", {{"percent", amount}});
        case ImplantEffect::FireResistance:
            return Engine::tr("+{percent} % of total fire resistance", {{"percent", amount}});
        case ImplantEffect::ArmorClass:
            return Engine::tr("+{percent} % of total armour class", {{"percent", amount}});
        case ImplantEffect::Reflect:
            return Engine::tr("{percent} % chance to send a missile back at its shooter", {{"percent", amount}});
        case ImplantEffect::ProjectileSpeed:
            return Engine::tr("+{percent} % speed of your missiles and spells", {{"percent", amount}});
        case ImplantEffect::Accuracy:
            return Engine::tr("+{percent} % of total Accuracy", {{"percent", amount}});
    }

    return {};
}

int implantShareOf(int total, float percent)
{
    if (total <= 0 || percent == 0.0f)
    {
        return 0;
    }

    // The small epsilon keeps a share that is whole on paper (18 % of 100) from rounding down through float error.
    const int size = int(std::floor(double(total) * double(std::fabs(percent)) / 100.0 + 1e-6));
    return percent < 0.0f ? -size : size;
}

float implantRecoveryCut(float factor, float recoveryPercent)
{
    return factor * (1.0f - std::clamp(recoveryPercent, 0.0f, 100.0f) / 100.0f);
}

float implantRecoveryFactor(float product)
{
    return std::clamp(product, ImplantMinimumRecoveryFactor, 1.0f);
}

std::array<int, 7> implantConverterChanges(const std::array<int, 7> &totals, float percent)
{
    std::array<int, 7> changes = {};
    size_t highest = 0;

    for (size_t index = 1; index < totals.size(); ++index)
    {
        if (totals[index] > totals[highest])
        {
            highest = index;
        }
    }

    for (size_t index = 0; index < totals.size(); ++index)
    {
        if (index != highest)
        {
            const int share = implantShareOf(totals[index], percent);
            changes[index] -= share;
            changes[highest] += share;
        }
    }

    return changes;
}

namespace
{
std::string trimCopy(const std::string &value)
{
    size_t begin = 0;

    while (begin < value.size() && std::isspace(static_cast<unsigned char>(value[begin])))
    {
        ++begin;
    }

    size_t end = value.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])))
    {
        --end;
    }

    return value.substr(begin, end - begin);
}

std::string getCell(const std::vector<std::string> &row, size_t index)
{
    if (index >= row.size())
    {
        return {};
    }

    return trimCopy(row[index]);
}

std::vector<std::string> splitPipeSeparated(const std::string &value)
{
    std::vector<std::string> result;
    size_t begin = 0;

    while (begin <= value.size())
    {
        const size_t end = value.find('|', begin);
        const std::string token = trimCopy(value.substr(begin, end - begin));

        if (!token.empty())
        {
            result.push_back(token);
        }

        if (end == std::string::npos)
        {
            break;
        }

        begin = end + 1;
    }

    return result;
}

int parseInt(const std::string &value)
{
    if (value.empty())
    {
        return 0;
    }

    try
    {
        return std::stoi(value);
    }
    catch (...)
    {
        return 0;
    }
}

float parseFloat(const std::string &value)
{
    if (value.empty())
    {
        return 0.0f;
    }

    try
    {
        return std::stof(value);
    }
    catch (...)
    {
        return 0.0f;
    }
}

bool isSupportedContentEffectFlag(const std::string &flag)
{
    static const std::unordered_set<std::string> SupportedFlags = {
        "AgingImmunity",
        "AllConditionImmunity",
        "Amelioration",
        "BreakAfterFirstAttack",
        "BreakChance2SelfDamage",
        "BypassArmorChance20",
        "CarriedPartyEffect",
        "DisableDivineIntervention",
        "DiseaseWeaponDamage",
        "EncounterChancePlus15Percent",
        "EnrageOnHit5Grandmaster",
        "Everlasting",
        "ExperienceGainMinus15Percent",
        "FeatherFalling",
        "FearOnHit10",
        "FearImmunity",
        "HalveTargetArmor",
        "HalfMissileDamage",
        "KillOnHit10",
        "MagicArmor20",
        "MeleeArmor40",
        "MissileArmor30",
        "PartyEnduranceMinus40",
        "PerfectAccuracy",
        "ParalysisImmunity",
        "PhysicalDamageReduction3Percent",
        "PoisonImmunity",
        "PoisonOnHit40Grandmaster",
        "PoisonWeaponDamage",
        "RangedArmorMinus10",
        "ReelOnHit",
        "SelfKnockoutOnFailedStun70",
        "SleepImmunity",
        "StoneImmunity",
        "StunOnHit5",
        "TripleProjectile",
        "Vampiric",
        "WeeklyGold1000",
        "WeeklyHealthLossChance10",
        "WeeklyInsanityChance10",
        "WaterWalking",
        "DiseaseImmunity",
        // Hesper: the melee floor 5 ticks lower (the Striking Lattice); spells cast at half power in null fields.
        "MeleeAttackFloorMinus5",
        "NullFieldCasting50",
    };
    if (SupportedFlags.contains(flag))
    {
        return true;
    }
    // x2 damage against a kind of monster (Xeen's Slayer Sword: SlayingDemon; D-2.3).
    if (itemSlayingKindFlag(flag) != 0)
    {
        return true;
    }
    // Hesper's numbered flags: a share of spell (Resonator) or ordinary weapon (Coupler) damage strikes raised
    // shields as Kreegan energy; a melee floor of <ticks>; melee recovery <percent> faster; a Workshop mod's weapon
    // damage to shields <percent> higher (ShieldDamage).
    for (const char *pPrefix :
        {"Resonator", "Coupler", "MeleeAttackFloor", "MeleeRecovery", "ShieldDamage"})
    {
        const std::string prefix = pPrefix;
        std::string number = flag.size() > prefix.size() && flag.rfind(prefix, 0) == 0 ? flag.substr(prefix.size())
                                                                                      : std::string();
        if (prefix == "MeleeRecovery" && number.size() > 3 && number.substr(number.size() - 3) == "Pct")
        {
            number.resize(number.size() - 3);
        }
        else if (prefix == "MeleeRecovery")
        {
            number.clear();
        }
        if (!number.empty() && std::all_of(number.begin(), number.end(), [](char c) { return c >= '0' && c <= '9'; }))
        {
            return true;
        }
    }
    return false;
}

bool parseContentEffect(
    const std::vector<std::string> &row,
    size_t startColumn,
    ItemContentEffect &effect,
    std::string &errorMessage)
{
    effect = {};
    effect.might = parseInt(getCell(row, startColumn));
    effect.intellect = parseInt(getCell(row, startColumn + 1));
    effect.personality = parseInt(getCell(row, startColumn + 2));
    effect.endurance = parseInt(getCell(row, startColumn + 3));
    effect.speed = parseInt(getCell(row, startColumn + 4));
    effect.accuracy = parseInt(getCell(row, startColumn + 5));
    effect.luck = parseInt(getCell(row, startColumn + 6));
    effect.maxHealth = parseInt(getCell(row, startColumn + 7));
    effect.maxSpellPoints = parseInt(getCell(row, startColumn + 8));
    effect.armorClass = parseInt(getCell(row, startColumn + 9));
    effect.meleeAttack = parseInt(getCell(row, startColumn + 10));
    effect.rangedAttack = parseInt(getCell(row, startColumn + 11));
    effect.meleeDamage = parseInt(getCell(row, startColumn + 12));
    effect.rangedDamage = parseInt(getCell(row, startColumn + 13));
    effect.allResistances = parseInt(getCell(row, startColumn + 14));
    effect.fireResistance = parseInt(getCell(row, startColumn + 15));
    effect.airResistance = parseInt(getCell(row, startColumn + 16));
    effect.waterResistance = parseInt(getCell(row, startColumn + 17));
    effect.earthResistance = parseInt(getCell(row, startColumn + 18));
    effect.mindResistance = parseInt(getCell(row, startColumn + 19));
    effect.bodyResistance = parseInt(getCell(row, startColumn + 20));
    effect.spiritResistance = parseInt(getCell(row, startColumn + 21));

    for (const std::string &token : splitPipeSeparated(getCell(row, startColumn + 22)))
    {
        const size_t separator = token.rfind(':');

        if (separator == std::string::npos)
        {
            errorMessage = "invalid skill bonus token '" + token + "'";
            return false;
        }

        const std::string skillName = canonicalSkillName(token.substr(0, separator));
        const int amount = parseInt(trimCopy(token.substr(separator + 1)));

        if (skillName.empty() || amount == 0)
        {
            errorMessage = "invalid skill bonus token '" + token + "'";
            return false;
        }

        effect.skillBonuses[skillName] += amount;
    }

    effect.weaponDamage = parseInt(getCell(row, startColumn + 23));
    effect.recoveryReductionTicks = parseInt(getCell(row, startColumn + 24));
    effect.healthRegenPerSecond = parseFloat(getCell(row, startColumn + 25));
    effect.spellRegenPerSecond = parseFloat(getCell(row, startColumn + 26));
    effect.flags = splitPipeSeparated(getCell(row, startColumn + 27));
    effect.energyResistance = parseInt(getCell(row, startColumn + 28));
    effect.personalShield = std::max(0, parseInt(getCell(row, startColumn + 29)));
    effect.shieldRegenDelaySeconds = parseFloat(getCell(row, startColumn + 30));
    effect.humPoints = parseInt(getCell(row, startColumn + 31));
    effect.rangedDamagePercent = parseInt(getCell(row, startColumn + 32));
    effect.meleeDamagePercent = parseInt(getCell(row, startColumn + 33));
    effect.spellDamagePercent = parseInt(getCell(row, startColumn + 34));
    effect.energyDamageTakenPercent = parseInt(getCell(row, startColumn + 35));
    effect.gunRecoveryReductionTicks = parseInt(getCell(row, startColumn + 36));
    effect.meleeRecoveryReductionTicks = parseInt(getCell(row, startColumn + 37));

    for (const std::string &flag : effect.flags)
    {
        if (!isSupportedContentEffectFlag(flag))
        {
            errorMessage = "unsupported content effect flag '" + flag + "'";
            return false;
        }
    }
    return true;
}

uint32_t parseUint32(const std::string &value)
{
    if (value.empty())
    {
        return 0;
    }

    try
    {
        return static_cast<uint32_t>(std::stoul(value));
    }
    catch (...)
    {
        return 0;
    }
}

ItemRarity parseItemRarity(const std::string &value)
{
    const std::string normalized = toLowerCopy(trimCopy(value));

    if (normalized == "artifact")
    {
        return ItemRarity::Artifact;
    }

    if (normalized == "relic")
    {
        return ItemRarity::Relic;
    }

    if (normalized == "special")
    {
        return ItemRarity::Special;
    }

    return ItemRarity::Common;
}

std::optional<uint32_t> parseItemId(const std::vector<std::string> &row)
{
    const std::string rawItemId = getCell(row, 0);

    if (rawItemId.empty())
    {
        return std::nullopt;
    }

    for (char character : rawItemId)
    {
        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            return std::nullopt;
        }
    }

    try
    {
        return static_cast<uint32_t>(std::stoul(rawItemId));
    }
    catch (...)
    {
        return std::nullopt;
    }
}

bool loadBitmapDimensions(
    const Engine::AssetFileSystem &assetFileSystem,
    Engine::DirectoryAssetPathCache &directories,
    Engine::AssetPathLookupCache &paths,
    std::unordered_map<std::string, std::optional<Engine::ImageDimensions>> &dimensions,
    const std::string &iconName,
    int &width,
    int &height,
    std::string &virtualPath
)
{
    if (iconName.empty())
    {
        return false;
    }

    const std::optional<std::string> imagePath =
        Engine::findImageAssetPath(assetFileSystem, "Data/icons", iconName, directories, paths);

    if (!imagePath)
    {
        return false;
    }

    auto [entry, inserted] = dimensions.try_emplace(*imagePath);
    if (inserted)
    {
        entry->second = Engine::loadImageDimensions(assetFileSystem, *imagePath);
    }
    if (!entry->second)
    {
        return false;
    }
    width = entry->second->width;
    height = entry->second->height;

    const Engine::AssetScaleTier loadedTier = Engine::assetScaleTierFromResolvedPath(*imagePath);
    width = Engine::scalePhysicalPixelsToLogical(width, loadedTier);
    height = Engine::scalePhysicalPixelsToLogical(height, loadedTier);
    virtualPath = *imagePath;
    return true;
}

uint8_t inventorySlotsFromPixels(int pixelSize)
{
    const int clampedPixels = std::max(14, pixelSize);
    const int slots = 1 + (clampedPixels - 14) / 32;
    return static_cast<uint8_t>(std::clamp(slots, 1, 14));
}
}

bool ItemTable::load(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::vector<std::string>> &itemRows,
    const std::vector<std::vector<std::string>> &randomItemRows
)
{
    Engine::DirectoryAssetPathCache directories;
    Engine::AssetPathLookupCache paths;
    std::unordered_map<std::string, std::optional<Engine::ImageDimensions>> dimensions;
    uint32_t maxItemId = 0;
    m_worldLoot.clear();

    for (const std::vector<std::string> &row : itemRows)
    {
        const std::optional<uint32_t> itemId = parseItemId(row);

        if (!itemId)
        {
            continue;
        }

        maxItemId = std::max(maxItemId, *itemId);
    }

    if (maxItemId == 0)
    {
        return false;
    }

    m_entries.clear();
    m_entries.resize(static_cast<size_t>(maxItemId) + 1);

    for (size_t itemIndex = 0; itemIndex < m_entries.size(); ++itemIndex)
    {
        m_entries[itemIndex].itemId = static_cast<uint32_t>(itemIndex);
    }

    for (const std::vector<std::string> &row : itemRows)
    {
        const std::optional<uint32_t> itemId = parseItemId(row);

        if (!itemId || *itemId >= m_entries.size())
        {
            continue;
        }

        ItemDefinition &entry = m_entries[*itemId];
        entry.itemId = *itemId;
        entry.packageId = getCell(row, 17);
        entry.canonicalId = getCell(row, 18);
        entry.sourceItemId = parseUint32(getCell(row, 19));

        if (entry.packageId.empty())
        {
            entry.packageId = "engine";
        }

        if (entry.canonicalId.empty())
        {
            entry.canonicalId = "engine:item/" + std::to_string(*itemId);
        }

        if (entry.sourceItemId == 0)
        {
            entry.sourceItemId = *itemId;
        }

        entry.iconName = getCell(row, 1);
        entry.name = getCell(row, 2);
        entry.value = parseInt(getCell(row, 3));
        entry.equipStat = getCell(row, 4);
        entry.skillGroup = getCell(row, 5);
        entry.mod1 = getCell(row, 6);
        entry.mod2 = getCell(row, 7);
        entry.material = parseInt(getCell(row, 8));
        entry.materialName = getCell(row, 8);
        entry.rarity = parseItemRarity(entry.materialName);
        entry.idRepSt = getCell(row, 9);
        entry.identifyRepairDifficulty = parseInt(entry.idRepSt);
        entry.unidentifiedName = getCell(row, 10);
        entry.spriteIndex = static_cast<uint16_t>(std::max(0, parseInt(getCell(row, 11))));
        entry.varAText = trimCopy(getCell(row, 12));
        entry.varA = parseInt(entry.varAText);
        entry.varB = parseInt(getCell(row, 13));
        entry.equipX = parseInt(getCell(row, 14));
        entry.equipY = parseInt(getCell(row, 15));
        entry.notes = getCell(row, 16);
        entry.contentFlags = splitPipeSeparated(getCell(row, 20));
        entry.worldIds.clear();

        for (const std::string &flag : entry.contentFlags)
        {
            const std::string normalizedFlag = toLowerCopy(trimCopy(flag));

            if (normalizedFlag.starts_with("world:"))
            {
                entry.worldIds.push_back(normalizedFlag.substr(6));
            }
        }
        entry.normalizedTier = static_cast<uint8_t>(std::clamp(parseInt(getCell(row, 21)), 0, 7));
        entry.useAction = getCell(row, 22);
        entry.useTarget = getCell(row, 23);
        entry.setId = getCell(row, 24);
        entry.effectProfile = getCell(row, 25);
        entry.allowedClassRoots = splitPipeSeparated(getCell(row, 26));
        entry.requiredMight = std::max(0, parseInt(getCell(row, 27)));
        entry.requiredAccuracy = std::max(0, parseInt(getCell(row, 28)));
        const int authoredInventoryWidth = parseInt(getCell(row, 29));
        const int authoredInventoryHeight = parseInt(getCell(row, 30));
        entry.visualStatus = getCell(row, 31);
        entry.sourceEquipType = getCell(row, 34);
        entry.sourceSkill = getCell(row, 35);
        entry.sourceIconPath = getCell(row, 36);
        entry.importStatus = getCell(row, 43);
        entry.balanceProfile = getCell(row, 44);

        int iconWidth = 0;
        int iconHeight = 0;

        if (loadBitmapDimensions(
                assetFileSystem, directories, paths, dimensions, entry.iconName,
                iconWidth, iconHeight, entry.iconVirtualPath))
        {
            entry.inventoryWidth = inventorySlotsFromPixels(iconWidth);
            entry.inventoryHeight = inventorySlotsFromPixels(iconHeight);
        }
        else
        {
            entry.inventoryWidth = 1;
            entry.inventoryHeight = 1;
        }

        if (authoredInventoryWidth > 0 && authoredInventoryHeight > 0)
        {
            entry.inventoryWidth = static_cast<uint8_t>(std::clamp(authoredInventoryWidth, 1, 14));
            entry.inventoryHeight = static_cast<uint8_t>(std::clamp(authoredInventoryHeight, 1, 9));
        }
    }

    for (const std::vector<std::string> &row : randomItemRows)
    {
        const std::optional<uint32_t> itemId = parseItemId(row);

        if (!itemId || *itemId >= m_entries.size())
        {
            continue;
        }

        ItemDefinition &entry = m_entries[*itemId];

        for (size_t weightIndex = 0; weightIndex < entry.randomTreasureWeights.size(); ++weightIndex)
        {
            entry.randomTreasureWeights[weightIndex] = parseInt(getCell(row, 2 + weightIndex));
        }
    }

    m_itemPackageIds.clear();

    for (const ItemDefinition &entry : m_entries)
    {
        if (entry.itemId != 0)
        {
            m_itemPackageIds.insert(toLowerCopy(entry.packageId));
        }
    }

    return true;
}

bool ItemDefinition::hasContentFlag(const std::string &flag) const
{
    const std::string normalizedFlag = toLowerCopy(trimCopy(flag));

    return std::any_of(
        contentFlags.begin(),
        contentFlags.end(),
        [&normalizedFlag](const std::string &candidate)
        {
            return toLowerCopy(candidate) == normalizedFlag;
        });
}

std::optional<uint32_t> ItemTable::spellbookItemIdForSpell(uint32_t spellId, const std::string &worldId) const
{
    const std::string spellToken = "S" + std::to_string(spellId);

    for (const ItemDefinition &entry : m_entries)
    {
        if (entry.itemId != 0
            && entry.equipStat == "Book"
            && entry.mod1 == spellToken
            && entry.availableInWorld(worldId))
        {
            return entry.itemId;
        }
    }

    return std::nullopt;
}

bool ItemDefinition::availableInWorld(const std::string &worldId) const
{
    return worldIds.empty() || std::find(worldIds.begin(), worldIds.end(), toLowerCopy(worldId)) != worldIds.end();
}

bool ItemDefinition::isGold() const
{
    return toLowerCopy(equipStat) == "gold";
}

const std::vector<WorldLootTable::Entry> *WorldLootTable::entriesForTreasureLevel(int treasureLevel) const
{
    const auto found = classes.find(classForTreasureLevel(treasureLevel));
    return found != classes.end() ? &found->second : nullptr;
}

const std::string &WorldLootTable::classForTreasureLevel(int treasureLevel) const
{
    return classByTreasureLevel[static_cast<size_t>(std::clamp(treasureLevel, 1, 6) - 1)];
}

bool ItemTable::loadWorldLootYaml(const std::string &text, const std::string &worldId, std::string &errorMessage)
{
    const std::string where = "worlds/" + worldId + "/loot.yml: ";
    WorldLootTable loot;

    try
    {
        const YAML::Node root = YAML::Load(text);

        if (!root.IsMap() || root["schema"].as<std::string>("") != "openyamm.worldLoot.v1")
        {
            errorMessage = where + "expected schema openyamm.worldLoot.v1";
            return false;
        }

        const YAML::Node classes = root["classes"];

        if (!classes || !classes.IsMap())
        {
            errorMessage = where + "expected a classes map";
            return false;
        }

        for (const auto &classNode : classes)
        {
            const std::string className = classNode.first.as<std::string>();
            std::vector<WorldLootTable::Entry> &entries = loot.classes[className];

            for (const auto &itemNode : classNode.second)
            {
                const WorldLootTable::Entry entry = {itemNode.first.as<uint32_t>(), itemNode.second.as<int>()};
                const ItemDefinition *pItem = get(entry.itemId);

                if (pItem == nullptr || !pItem->availableInWorld(worldId))
                {
                    errorMessage = where + "class " + className + " lists item " + std::to_string(entry.itemId)
                        + ", which the world does not have";
                    return false;
                }

                if (entry.weight < 0)
                {
                    errorMessage = where + "class " + className + " gives item " + std::to_string(entry.itemId)
                        + " a negative weight";
                    return false;
                }

                if (entry.weight > 0)
                {
                    entries.push_back(entry);
                    loot.listedItemIds.insert(entry.itemId);
                }
            }
        }

        if (const YAML::Node enchantments = root["enchantments"])
        {
            loot.curatesEnchantments = true;

            for (const YAML::Node &name : enchantments["standard"])
            {
                loot.standardEnchantments.insert(toLowerCopy(name.as<std::string>()));
            }

            for (const auto &classNode : enchantments["special"])
            {
                std::unordered_set<std::string> &names =
                    loot.specialEnchantmentsByClass[classNode.first.as<std::string>()];

                for (const YAML::Node &name : classNode.second)
                {
                    names.insert(toLowerCopy(name.as<std::string>()));
                }
            }
        }

        const YAML::Node levels = root["treasure_levels"];

        if (!levels || !levels.IsSequence() || levels.size() != loot.classByTreasureLevel.size())
        {
            errorMessage = where + "treasure_levels needs one class for each treasure level 1-6";
            return false;
        }

        for (size_t level = 0; level < loot.classByTreasureLevel.size(); ++level)
        {
            loot.classByTreasureLevel[level] = levels[level].as<std::string>();

            if (!loot.classes.contains(loot.classByTreasureLevel[level]))
            {
                errorMessage = where + "treasure level " + std::to_string(level + 1) + " names unknown class "
                    + loot.classByTreasureLevel[level];
                return false;
            }
        }
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = where + exception.what();
        return false;
    }

    m_worldLoot[toLowerCopy(worldId)] = std::move(loot);
    return true;
}

const WorldLootTable *ItemTable::worldLoot(const std::string &worldId) const
{
    if (m_worldLoot.empty())
    {
        return nullptr;
    }

    const auto found = m_worldLoot.find(toLowerCopy(worldId));
    return found != m_worldLoot.end() ? &found->second : nullptr;
}

bool ItemTable::loadVisualRows(const std::vector<std::vector<std::string>> &rows, std::string &errorMessage)
{
    // Validate a complete import before replacing any existing visual metadata.
    std::vector<ItemDefinition> entries = m_entries;
    std::unordered_set<std::string> keys;
    const std::array<std::string, 16> slots = {"OffHand", "MainHand", "Bow", "Armor", "Helm", "Belt",
        "Cloak", "Gauntlets", "Boots", "Amulet", "Ring1", "Ring2", "Ring3", "Ring4", "Ring5", "Ring6"};
    const auto integer = [](const std::string &text, int &value)
    {
        const auto result = std::from_chars(text.data(), text.data() + text.size(), value);
        return result.ec == std::errc() && result.ptr == text.data() + text.size();
    };
    const auto scale = [](const std::string &text, float &value)
    {
        char *pEnd = nullptr;
        errno = 0;
        value = std::strtof(text.c_str(), &pEnd);
        return errno != ERANGE && pEnd == text.c_str() + text.size()
            && std::isfinite(value) && value > 0.0f && value <= 1.0f;
    };
    for (ItemDefinition &entry : entries)
    {
        entry.equipmentPlacements.clear();
        entry.inventoryDrawScale = 1.0f;
        entry.jewelryDrawScale = 1.0f;
    }
    for (size_t rowIndex = 0; rowIndex < rows.size(); ++rowIndex)
    {
        const std::vector<std::string> &row = rows[rowIndex];
        const std::string kind = getCell(row, 0);
        if (kind.empty() || kind.starts_with("#") || kind == "Kind")
        {
            continue;
        }
        int itemId = 0;
        bool valid = integer(getCell(row, 1), itemId) && itemId > 0
            && static_cast<size_t>(itemId) < entries.size() && !entries[itemId].canonicalId.empty();
        if (valid)
        {
            ItemDefinition &entry = entries[itemId];
            if (kind == "inventory")
            {
                int width = 0;
                int height = 0;
                valid = keys.insert(kind + ":" + std::to_string(itemId)).second
                    && integer(getCell(row, 6), width) && integer(getCell(row, 7), height)
                    && width >= 1 && width <= 14 && height >= 1 && height <= 9
                    && scale(getCell(row, 8), entry.inventoryDrawScale)
                    && scale(getCell(row, 9), entry.jewelryDrawScale);
                if (valid)
                {
                    entry.inventoryWidth = static_cast<uint8_t>(width);
                    entry.inventoryHeight = static_cast<uint8_t>(height);
                }
            }
            else if (kind == "placement")
            {
                int dollType = 0;
                ItemEquipmentPlacement placement;
                const std::string slot = getCell(row, 3);
                const auto position = std::find(slots.begin(), slots.end(), slot);
                valid = integer(getCell(row, 2), dollType) && dollType >= 0 && dollType <= 5
                    && position != slots.end() && integer(getCell(row, 4), placement.x)
                    && integer(getCell(row, 5), placement.y)
                    && keys.insert(kind + ":" + std::to_string(itemId) + ":"
                        + std::to_string(dollType) + ":" + slot).second;
                if (valid)
                {
                    placement.dollType = static_cast<uint32_t>(dollType);
                    placement.slot = static_cast<EquipmentSlot>(std::distance(slots.begin(), position));
                    entry.equipmentPlacements.push_back(placement);
                }
            }
            else
            {
                valid = false;
            }
        }
        if (!valid)
        {
            errorMessage = "Invalid or duplicate item visual row " + std::to_string(rowIndex + 1);
            return false;
        }
    }
    m_entries = std::move(entries);
    errorMessage.clear();
    return true;
}

std::string ItemTable::lootPoolForWorld(const std::string &worldId) const
{
    if (worldId.empty())
    {
        return {};
    }

    const std::string world = toLowerCopy(worldId);
    return m_itemPackageIds.contains(world) ? world : std::string("engine");
}

std::vector<std::string> ItemTable::lootPoolsForWorld(const std::string &worldId) const
{
    std::vector<std::string> pools;

    if (worldId.empty())
    {
        return pools;
    }

    pools.push_back(lootPoolForWorld(worldId));
    const auto found = m_worldDependencies.find(toLowerCopy(worldId));

    if (found != m_worldDependencies.end())
    {
        for (const std::string &dependency : found->second)
        {
            const std::string pool = lootPoolForWorld(dependency);

            if (std::find(pools.begin(), pools.end(), pool) == pools.end())
            {
                pools.push_back(pool);
            }
        }
    }

    return pools;
}

void ItemTable::setWorldDependencies(std::unordered_map<std::string, std::vector<std::string>> dependenciesByWorld)
{
    m_worldDependencies.clear();

    for (auto &[worldId, dependencies] : dependenciesByWorld)
    {
        std::vector<std::string> &lowered = m_worldDependencies[toLowerCopy(worldId)];

        for (const std::string &dependency : dependencies)
        {
            lowered.push_back(toLowerCopy(dependency));
        }
    }
}

void ItemTable::setChestArtifactsOnlyWorlds(std::unordered_set<std::string> worldIds)
{
    m_chestArtifactsOnlyWorlds.clear();

    for (const std::string &worldId : worldIds)
    {
        m_chestArtifactsOnlyWorlds.insert(toLowerCopy(worldId));
    }
}

bool ItemTable::chestArtifactsOnly(const std::string &worldId) const
{
    return !worldId.empty() && m_chestArtifactsOnlyWorlds.contains(toLowerCopy(worldId));
}

void ItemTable::setGroundGoldByItemTierWorlds(std::unordered_set<std::string> worldIds)
{
    m_groundGoldByItemTierWorlds.clear();

    for (const std::string &worldId : worldIds)
    {
        m_groundGoldByItemTierWorlds.insert(toLowerCopy(worldId));
    }
}

bool ItemTable::groundGoldByItemTier(const std::string &worldId) const
{
    return !worldId.empty() && m_groundGoldByItemTierWorlds.contains(toLowerCopy(worldId));
}

const ItemDefinition *ItemTable::get(uint32_t itemId) const
{
    if (itemId >= m_entries.size())
    {
        return nullptr;
    }

    const ItemDefinition &entry = m_entries[itemId];

    if (entry.itemId == 0 && itemId != 0)
    {
        return nullptr;
    }

    if (itemId != 0 && entry.name.empty() && entry.iconName.empty())
    {
        return nullptr;
    }

    return &entry;
}

const ItemDefinition *ItemTable::findBySpriteIndex(uint16_t spriteIndex) const
{
    if (spriteIndex == 0)
    {
        return nullptr;
    }

    for (const ItemDefinition &entry : m_entries)
    {
        if (entry.itemId != 0 && entry.spriteIndex == spriteIndex)
        {
            return &entry;
        }
    }

    return nullptr;
}

const std::vector<ItemDefinition> &ItemTable::entries() const
{
    return m_entries;
}

bool ItemTable::loadContentEffectRows(
    const std::vector<std::vector<std::string>> &rows,
    std::string &errorMessage)
{
    std::unordered_map<std::string, uint32_t> profileOwners;

    for (const std::vector<std::string> &row : rows)
    {
        const std::optional<uint32_t> itemId = parseItemId(row);

        if (!itemId)
        {
            continue;
        }

        ItemDefinition *pItem = *itemId < m_entries.size() ? &m_entries[*itemId] : nullptr;
        const std::string profile = getCell(row, 1);

        if (pItem == nullptr || get(*itemId) == nullptr || profile.empty() || pItem->effectProfile != profile)
        {
            errorMessage = "item effect row does not match item " + std::to_string(*itemId) + " profile";
            return false;
        }

        if (!profileOwners.emplace(toLowerCopy(profile), *itemId).second)
        {
            errorMessage = "duplicate item effect profile '" + profile + "'";
            return false;
        }

        if (!parseContentEffect(row, 2, pItem->contentEffect, errorMessage))
        {
            errorMessage = "item " + std::to_string(*itemId) + ": " + errorMessage;
            return false;
        }
    }

    return true;
}

bool ItemTable::loadWorkshopModRows(const std::vector<std::vector<std::string>> &rows, std::string &errorMessage)
{
    m_workshopMods.clear();

    for (const std::vector<std::string> &row : rows)
    {
        const std::string idCell = getCell(row, 0);

        if (idCell.empty() || toLowerCopy(idCell) == "mod_id")
        {
            continue;
        }

        WorkshopModDefinition mod = {};
        mod.id = static_cast<uint16_t>(parseInt(idCell));
        mod.name = getCell(row, 1);
        mod.fits = splitPipeSeparated(getCell(row, 2));

        if (mod.id == 0 || mod.name.empty() || mod.fits.empty())
        {
            errorMessage = "workshop mod '" + idCell + "' needs an id, a name and what it fits";
            return false;
        }

        if (!parseContentEffect(row, 3, mod.effect, errorMessage))
        {
            errorMessage = "workshop mod '" + mod.name + "': " + errorMessage;
            return false;
        }

        if (!m_workshopMods.emplace(mod.id, std::move(mod)).second)
        {
            errorMessage = "duplicate workshop mod " + idCell;
            return false;
        }
    }

    return true;
}

bool ItemTable::loadImplantRows(const std::vector<std::vector<std::string>> &rows, std::string &errorMessage)
{
    m_implants.clear();
    // The columns by the header row's names (DECISIONS H-91), so a later column moves nothing. One row per part of an
    // implant; empty maw_ cells take Standard's value.
    std::unordered_map<std::string, size_t> columns;
    const auto column = [&columns](const std::vector<std::string> &row, const char *pName)
    {
        const auto found = columns.find(pName);
        return found != columns.end() ? getCell(row, found->second) : std::string();
    };
    const auto share = [&column](const std::vector<std::string> &row, const char *pPrefix, const ImplantShare *pFallback)
    {
        ImplantShare values = pFallback != nullptr ? *pFallback : ImplantShare{};
        const std::string prefix = pPrefix;
        const std::array<std::string, 4> names = {
            prefix + "base_i", prefix + "per_level_i", prefix + "base_ii", prefix + "per_level_ii"};
        const std::array<float *, 4> targets = {&values.basePercent[0], &values.perLevelPercent[0],
            &values.basePercent[1], &values.perLevelPercent[1]};

        for (size_t index = 0; index < names.size(); ++index)
        {
            const std::string cell = column(row, names[index].c_str());

            if (!cell.empty() || pFallback == nullptr)
            {
                *targets[index] = parseFloat(cell);
            }
        }

        return values;
    };

    for (const std::vector<std::string> &row : rows)
    {
        const std::string idCell = getCell(row, 0);

        if (toLowerCopy(idCell) == "item_id")
        {
            columns.clear();

            for (size_t index = 0; index < row.size(); ++index)
            {
                columns[toLowerCopy(getCell(row, index))] = index;
            }

            for (const char *pName : {"socket", "effect", "base_i", "per_level_i", "base_ii", "per_level_ii"})
            {
                if (!columns.contains(pName))
                {
                    errorMessage = std::string("implants table has no '") + pName + "' column";
                    return false;
                }
            }

            continue;
        }

        // A generator's "#" note.
        if (idCell.empty() || std::isdigit(static_cast<unsigned char>(idCell.front())) == 0)
        {
            continue;
        }

        if (columns.empty())
        {
            errorMessage = "implants table has no header row";
            return false;
        }

        const uint32_t itemId = parseUint32(idCell);
        const ItemDefinition *pItem = get(itemId);

        if (pItem == nullptr || pItem->equipStat != "Implant")
        {
            errorMessage = "implant row " + idCell + " names no Implant item";
            return false;
        }

        const std::optional<ImplantSocket> socket = parseImplantSocket(toLowerCopy(column(row, "socket")));
        const std::optional<ImplantEffect> effect = parseImplantEffect(toLowerCopy(column(row, "effect")));

        if (!socket)
        {
            errorMessage = "implant " + idCell + ": unknown socket '" + column(row, "socket") + "'";
            return false;
        }

        if (!effect)
        {
            errorMessage = "implant " + idCell + ": unknown effect '" + column(row, "effect") + "'";
            return false;
        }

        ImplantComponent component = {};
        component.effect = *effect;
        component.standard = share(row, "", nullptr);
        component.maw = share(row, "maw_", &component.standard);

        for (const ImplantShare *pShare : {&component.standard, &component.maw})
        {
            for (size_t stage = 0; stage < ImplantStageCount; ++stage)
            {
                if (!implantEffectMayBeNegative(*effect)
                    && (pShare->basePercent[stage] < 0.0f || pShare->perLevelPercent[stage] < 0.0f))
                {
                    errorMessage = "implant " + idCell + ": only all_stats, max_health and max_sp may be negative";
                    return false;
                }
            }
        }

        for (const std::string &name : splitPipeSeparated(toLowerCopy(column(row, "except"))))
        {
            const auto found = std::find(ImplantStatNames.begin(), ImplantStatNames.end(), name);

            if (found == ImplantStatNames.end() || *effect != ImplantEffect::AllStats)
            {
                errorMessage = "implant " + idCell + ": except '" + name + "' (a primary stat, all_stats only)";
                return false;
            }

            component.exceptStats |= uint8_t(1u << size_t(found - ImplantStatNames.begin()));
        }

        const uint32_t stageTwoKills =
            column(row, "evolve_ii").empty() ? 250 : parseUint32(column(row, "evolve_ii"));
        const uint32_t evolveSoundId = parseUint32(column(row, "evolve_sound"));
        const uint32_t fitSoundId = parseUint32(column(row, "fit_sound"));
        const uint32_t removeSoundId = parseUint32(column(row, "remove_sound"));

        if (stageTwoKills == 0)
        {
            errorMessage = "implant " + idCell + ": stage II needs kills";
            return false;
        }

        if (pItem->contentEffect.skillBonuses.contains("Implants"))
        {
            errorMessage = "implant " + idCell + " raises Implants itself";
            return false;
        }

        const auto [found, created] = m_implants.try_emplace(itemId);
        ImplantDefinition &implant = found->second;

        if (created)
        {
            implant.socket = *socket;
            implant.stageTwoKills = stageTwoKills;
            implant.evolveSoundId = evolveSoundId;
            implant.fitSoundId = fitSoundId;
            implant.removeSoundId = removeSoundId;
        }
        else if (implant.socket != *socket || implant.stageTwoKills != stageTwoKills
            || implant.evolveSoundId != evolveSoundId || implant.fitSoundId != fitSoundId
            || implant.removeSoundId != removeSoundId)
        {
            errorMessage = "implant " + idCell + ": its rows disagree on socket, evolve_ii or a sound";
            return false;
        }

        implant.components.push_back(component);
    }

    // A package that brings implants rows needs one for each of its Implant items (an older package without the table,
    // such as Hesper's October stage, keeps unfittable Implant items).
    std::unordered_set<std::string> implantPackages;

    for (const auto &[itemId, implant] : m_implants)
    {
        implantPackages.insert(get(itemId)->packageId);
    }

    for (const ItemDefinition &item : m_entries)
    {
        if (item.itemId != 0 && item.equipStat == "Implant" && implantPackages.contains(item.packageId)
            && !m_implants.contains(item.itemId))
        {
            errorMessage = "Implant item " + std::to_string(item.itemId) + " has no implants row";
            return false;
        }
    }

    return true;
}

bool ItemTable::implantsAvailable() const
{
    return !m_implants.empty();
}

const ImplantDefinition *ItemTable::implant(uint32_t itemId) const
{
    const auto found = m_implants.find(itemId);
    return found != m_implants.end() ? &found->second : nullptr;
}

const WorkshopModDefinition *ItemTable::workshopMod(uint16_t modId) const
{
    const auto found = m_workshopMods.find(modId);
    return found != m_workshopMods.end() ? &found->second : nullptr;
}

bool ItemTable::workshopModFits(const WorkshopModDefinition &mod, const ItemDefinition &item) const
{
    return item.rarity != ItemRarity::Relic && !item.hasContentFlag("QuestItem")
        && std::any_of(mod.fits.begin(), mod.fits.end(),
            [&item](const std::string &equipStat)
            {
                return toLowerCopy(equipStat) == toLowerCopy(item.equipStat);
            });
}

bool ItemTable::loadItemSetRows(
    const std::vector<std::vector<std::string>> &rows,
    std::string &errorMessage)
{
    m_setBonuses.clear();
    std::unordered_map<std::string, size_t> setThresholds;

    for (const std::vector<std::string> &row : rows)
    {
        const std::string setId = getCell(row, 0);

        if (setId.empty() || toLowerCopy(setId) == "set_id")
        {
            continue;
        }

        const int requiredPieceCount = parseInt(getCell(row, 1));
        const std::string profile = getCell(row, 2);

        if (requiredPieceCount <= 0 || profile.empty())
        {
            errorMessage = "invalid item set bonus for '" + setId + "'";
            return false;
        }

        const std::string thresholdKey = toLowerCopy(setId) + ":" + std::to_string(requiredPieceCount);

        if (!setThresholds.emplace(thresholdKey, static_cast<size_t>(requiredPieceCount)).second)
        {
            errorMessage = "duplicate item set threshold '" + thresholdKey + "'";
            return false;
        }

        ItemSetBonusDefinition definition = {};
        definition.setId = setId;
        definition.requiredPieceCount = static_cast<size_t>(requiredPieceCount);
        definition.effectProfile = profile;

        if (!parseContentEffect(row, 3, definition.effect, errorMessage))
        {
            errorMessage = "item set '" + setId + "': " + errorMessage;
            return false;
        }

        m_setBonuses.push_back(std::move(definition));
    }

    return true;
}

const std::vector<ItemSetBonusDefinition> &ItemTable::setBonuses() const
{
    return m_setBonuses;
}

void ItemTable::applyPotionSettings(const MergedPotionSettingTable &potionSettingTable)
{
    for (ItemDefinition &entry : m_entries)
    {
        entry.hasPotionPower = false;
    }

    for (const MergedPotionSettingEntry &setting : potionSettingTable.entries())
    {
        if (setting.potionId != 0 && setting.itemId < m_entries.size())
        {
            m_entries[setting.itemId].hasPotionPower = true;
        }
    }
}

std::vector<uint32_t> ItemTable::resolveSpecialItemEnchants(
    const StandardItemEnchantTable &standardTable,
    const SpecialItemEnchantTable &specialTable)
{
    // Enchantment ids are 1-based in both tables.
    const auto findSuffix =
        [](const auto &entries, const std::string &name) -> uint16_t
        {
            for (size_t index = 0; index < entries.size(); ++index)
            {
                if (!entries[index].suffix.empty() && toLowerCopy(trimCopy(entries[index].suffix)) == name)
                {
                    return uint16_t(index + 1);
                }
            }

            return 0;
        };
    std::vector<uint32_t> unresolved;

    for (ItemDefinition &entry : m_entries)
    {
        entry.specialItemStandardEnchantId = 0;
        entry.specialItemStandardEnchantPower = 0;
        entry.specialItemSpecialEnchantId = 0;

        if (entry.rarity != ItemRarity::Special || entry.varAText.empty() || entry.varAText == "0")
        {
            continue;
        }

        const std::string name = toLowerCopy(entry.varAText);

        if (const uint16_t standardId = findSuffix(standardTable.entries(), name); standardId != 0)
        {
            entry.specialItemStandardEnchantId = standardId;
            entry.specialItemStandardEnchantPower = uint16_t(std::max(1, entry.varB));
        }
        else if (const uint16_t specialId = findSuffix(specialTable.entries(), name); specialId != 0)
        {
            entry.specialItemSpecialEnchantId = specialId;
        }
        else
        {
            unresolved.push_back(entry.itemId);
        }
    }

    return unresolved;
}

void ItemTable::setGroundModels(const ItemModelBindings &bindings)
{
    m_groundModels.clear();
    m_groundModelIndexByItemId.assign(m_entries.size(), -1);
    std::unordered_map<std::string, int32_t> indexByIcon;

    for (size_t itemId = 0; itemId < m_entries.size(); ++itemId)
    {
        const std::string icon = toLowerCopy(m_entries[itemId].iconName);
        const auto binding = bindings.find(icon);

        if (binding == bindings.end())
        {
            continue;
        }

        const auto [index, inserted] = indexByIcon.try_emplace(icon, int32_t(m_groundModels.size()));

        if (inserted)
        {
            m_groundModels.push_back(binding->second);
        }

        m_groundModelIndexByItemId[itemId] = index->second;
    }
}

const ItemModelBinding &ItemTable::groundModel(uint32_t itemId) const
{
    return hasGroundModel(itemId)
        ? m_groundModels[size_t(m_groundModelIndexByItemId[itemId])]
        : missingItemModelBinding();
}

bool ItemTable::hasGroundModel(uint32_t itemId) const
{
    return itemId < m_groundModelIndexByItemId.size() && m_groundModelIndexByItemId[itemId] >= 0;
}

bool ItemTable::loadSourceAliasRows(
    const std::vector<std::vector<std::string>> &rows,
    std::string &errorMessage)
{
    m_sourceAliases.clear();

    for (const std::vector<std::string> &row : rows)
    {
        const std::string packageId = toLowerCopy(getCell(row, 0));
        const uint32_t sourceItemId = parseUint32(getCell(row, 1));
        const uint32_t itemId = parseUint32(getCell(row, 2));

        if (packageId.empty() || packageId == "package_id")
        {
            continue;
        }

        const ItemDefinition *pTarget = get(itemId);
        const std::string key = packageId + ":" + std::to_string(sourceItemId);

        if (sourceItemId == 0 || pTarget == nullptr || !m_sourceAliases.emplace(key, itemId).second)
        {
            errorMessage = "invalid or duplicate source item alias '" + key + "'";
            return false;
        }

        if (toLowerCopy(pTarget->packageId) == packageId && pTarget->sourceItemId != sourceItemId)
        {
            errorMessage = "source item alias '" + key + "' does not match its package definition";
            return false;
        }
    }

    return true;
}

const ItemDefinition *ItemTable::resolvePackageSourceItemId(
    const std::string &packageId,
    uint32_t sourceItemId) const
{
    const std::string key = toLowerCopy(trimCopy(packageId)) + ":" + std::to_string(sourceItemId);
    const auto foundAlias = m_sourceAliases.find(key);
    return foundAlias != m_sourceAliases.end() ? get(foundAlias->second) : nullptr;
}
}
