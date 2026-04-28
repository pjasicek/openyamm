#include "game/party/PartySpellSystem.h"

#include "game/gameplay/GameMechanics.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/InventoryItemMixingRuntime.h"
#include "game/party/LloydsBeaconRuntime.h"
#include "game/party/SpellSchool.h"
#include "game/party/SpellIds.h"
#include "game/tables/SpellTable.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
constexpr float OeRealtimeRecoveryScale = 2.133333333333333f;
constexpr float Pi = 3.14159265358979323846f;
constexpr float SoulDrinkerOutdoorRange = 10240.0f;
constexpr float CameraVerticalFovRadians = Pi / 3.0f;
constexpr float PartyMemberProjectileLateralSpacing = 28.0f;
constexpr float ProjectileRightVectorEpsilon = 0.0001f;
constexpr float SpellFailureRecoveryScale = 0.5f;
constexpr uint32_t FirstBaseSpellId = spellIdValue(SpellId::TorchLight);
constexpr uint32_t LastBaseSpellId = spellIdValue(SpellId::SoulDrinker);
constexpr int16_t SummonWispNormalMonsterId = 97;
constexpr int16_t SummonWispMasterMonsterId = 98;
constexpr int16_t SummonWispGrandmasterMonsterId = 99;
constexpr size_t SummonWispActiveLimit = 5;

constexpr const char *SpellFailedText = "Spell failed";
constexpr const char *NoValidTargetText = "No valid target exists!";
constexpr const char *HostileCreaturesNearbyText = "There are hostile creatures nearby!";
constexpr const char *SummonLimitText = "This character can't summon any more monsters!";
constexpr const char *WandAlreadyChargedText = "Wand already charged!";
constexpr const char *ItemQualityTooLowText = "Item is not of high enough quality";

float secondsFromHours(float hours);
float secondsFromMinutes(float minutes);

struct SpellSourcePoint
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

float partyMemberProjectileLateralOffset(size_t memberIndex, size_t memberCount)
{
    if (memberCount <= 1 || memberIndex >= memberCount)
    {
        return 0.0f;
    }

    const float centerIndex = (static_cast<float>(memberCount) - 1.0f) * 0.5f;
    return (centerIndex - static_cast<float>(memberIndex)) * PartyMemberProjectileLateralSpacing;
}

SpellSourcePoint offsetPartyProjectileSourceForMember(
    const PartySpellCastRequest &request,
    const SpellSourcePoint &source,
    const SpellSourcePoint &target,
    size_t memberCount)
{
    const float lateralOffset = partyMemberProjectileLateralOffset(request.casterMemberIndex, memberCount);

    if (lateralOffset == 0.0f)
    {
        return source;
    }

    float rightX = 0.0f;
    float rightY = 0.0f;
    float rightZ = 0.0f;

    if (request.hasViewTransform)
    {
        rightX = -std::sin(request.viewYawRadians);
        rightY = std::cos(request.viewYawRadians);
    }
    else
    {
        const float forwardX = target.x - source.x;
        const float forwardY = target.y - source.y;
        const float forwardLength = std::sqrt(forwardX * forwardX + forwardY * forwardY);

        if (forwardLength <= ProjectileRightVectorEpsilon)
        {
            return source;
        }

        rightX = -forwardY / forwardLength;
        rightY = forwardX / forwardLength;
    }

    const float rightLength = std::sqrt(rightX * rightX + rightY * rightY + rightZ * rightZ);

    if (rightLength <= ProjectileRightVectorEpsilon)
    {
        return source;
    }

    return SpellSourcePoint{
        .x = source.x + rightX / rightLength * lateralOffset,
        .y = source.y + rightY / rightLength * lateralOffset,
        .z = source.z + rightZ / rightLength * lateralOffset,
    };
}

uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue)
{
    return 0xff000000u
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

const ItemDefinition *resolveTargetItemDefinition(
    Party &party,
    const PartySpellCastRequest &request,
    size_t &memberIndex,
    const InventoryItem *&pInventoryItem,
    EquippedItemRuntimeState *&pEquippedItemRuntime)
{
    memberIndex = request.targetItemMemberIndex.value_or(request.casterMemberIndex);
    pInventoryItem = nullptr;
    pEquippedItemRuntime = nullptr;

    if (request.targetInventoryGridX.has_value() && request.targetInventoryGridY.has_value())
    {
        pInventoryItem = party.memberInventoryItem(memberIndex, *request.targetInventoryGridX, *request.targetInventoryGridY);
        return pInventoryItem != nullptr && party.itemTable() != nullptr
            ? party.itemTable()->get(pInventoryItem->objectDescriptionId)
            : nullptr;
    }

    if (request.targetEquipmentSlot.has_value())
    {
        const uint32_t itemId = party.equippedItemId(memberIndex, *request.targetEquipmentSlot);
        pEquippedItemRuntime = party.equippedItemRuntimeMutable(memberIndex, *request.targetEquipmentSlot);
        return itemId != 0 && party.itemTable() != nullptr ? party.itemTable()->get(itemId) : nullptr;
    }

    return nullptr;
}

uint16_t findSpecialEnchantId(const SpecialItemEnchantTable *pTable, SpecialItemEnchantKind kind)
{
    if (pTable == nullptr)
    {
        return 0;
    }

    const std::vector<SpecialItemEnchantEntry> &entries = pTable->entries();

    for (size_t index = 0; index < entries.size(); ++index)
    {
        if (entries[index].kind == kind)
        {
            return static_cast<uint16_t>(index + 1);
        }
    }

    return 0;
}

bool canApplySpellWeaponEnchant(
    const ItemDefinition &itemDefinition,
    const InventoryItem *pInventoryItem,
    const EquippedItemRuntimeState *pEquippedItemRuntime)
{
    const bool isEnchantableWeapon =
        ItemEnchantRuntime::categoryForItem(itemDefinition) == ItemEnchantCategory::OneHandedWeapon
        || ItemEnchantRuntime::categoryForItem(itemDefinition) == ItemEnchantCategory::TwoHandedWeapon
        || ItemEnchantRuntime::categoryForItem(itemDefinition) == ItemEnchantCategory::Missile;

    if (!isEnchantableWeapon)
    {
        return false;
    }

    if (pInventoryItem != nullptr)
    {
        return !pInventoryItem->broken
            && pInventoryItem->rarity == ItemRarity::Common
            && pInventoryItem->specialEnchantId == 0
            && pInventoryItem->standardEnchantId == 0
            && pInventoryItem->artifactId == 0;
    }

    if (pEquippedItemRuntime != nullptr)
    {
        return !pEquippedItemRuntime->broken
            && pEquippedItemRuntime->rarity == ItemRarity::Common
            && pEquippedItemRuntime->specialEnchantId == 0
            && pEquippedItemRuntime->standardEnchantId == 0
            && pEquippedItemRuntime->artifactId == 0;
    }

    return false;
}

bool canApplyEnchantItemSpell(const ItemDefinition &itemDefinition, const InventoryItem &item)
{
    return ItemEnchantRuntime::isEnchantable(itemDefinition)
        && !item.broken
        && item.rarity == ItemRarity::Common
        && item.specialEnchantId == 0
        && item.standardEnchantId == 0
        && item.standardEnchantPower == 0
        && item.artifactId == 0;
}

bool hasNearbyHostileActor(const IGameplayWorldRuntime &worldRuntime)
{
    for (size_t actorIndex = 0; actorIndex < worldRuntime.mapActorCount(); ++actorIndex)
    {
        GameplayRuntimeActorState actor = {};

        if (worldRuntime.actorRuntimeState(actorIndex, actor)
            && !actor.isDead
            && !actor.isInvisible
            && actor.hostileToParty
            && actor.hasDetectedParty)
        {
            return true;
        }
    }

    return false;
}

bool isSummonWispMonsterId(int16_t monsterId)
{
    return monsterId == SummonWispNormalMonsterId
        || monsterId == SummonWispMasterMonsterId
        || monsterId == SummonWispGrandmasterMonsterId;
}

size_t activeFriendlyWispCount(const IGameplayWorldRuntime &worldRuntime)
{
    size_t count = 0;

    for (size_t actorIndex = 0; actorIndex < worldRuntime.mapActorCount(); ++actorIndex)
    {
        GameplayRuntimeActorState actor = {};

        if (worldRuntime.actorRuntimeState(actorIndex, actor)
            && isSummonWispMonsterId(actor.monsterId)
            && !actor.isDead
            && !actor.isInvisible
            && !actor.hostileToParty)
        {
            ++count;
        }
    }

    return count;
}

int16_t summonWispMonsterIdForMastery(SkillMastery skillMastery)
{
    return skillMastery == SkillMastery::Grandmaster
        ? SummonWispGrandmasterMonsterId
        : skillMastery == SkillMastery::Master
        ? SummonWispMasterMonsterId
        : SummonWispNormalMonsterId;
}

float summonWispDurationSeconds(uint32_t skillLevel, SkillMastery skillMastery)
{
    if (skillMastery == SkillMastery::Grandmaster)
    {
        return secondsFromHours(static_cast<float>(skillLevel));
    }

    if (skillMastery == SkillMastery::Master)
    {
        return secondsFromMinutes(static_cast<float>(15 * skillLevel));
    }

    return secondsFromMinutes(static_cast<float>(5 * skillLevel));
}

bool isSpellOutdoorOnly(SpellId spellId)
{
    return spellId == SpellId::MeteorShower
        || spellId == SpellId::Starburst
        || spellId == SpellId::DeathBlossom
        || spellId == SpellId::Sunray
        || spellId == SpellId::Armageddon
        || spellId == SpellId::Fly;
}

bool isSpellIndoorOnly(SpellId spellId)
{
    return spellId == SpellId::Inferno || spellId == SpellId::PrismaticLight;
}

std::string spellWorldUnavailableText(SpellId spellId, bool indoorMap)
{
    if (indoorMap)
    {
        switch (spellId)
        {
            case SpellId::MeteorShower:
                return "Can't cast Meteor Shower indoors!";
            case SpellId::Starburst:
                return "Can't cast Starburst indoors!";
            case SpellId::Fly:
                return "Can not cast Fly indoors!";
            case SpellId::Armageddon:
                return "Can't cast Armageddon indoors!";
            default:
                return SpellFailedText;
        }
    }

    switch (spellId)
    {
        case SpellId::Inferno:
            return "Can't cast Inferno outdoors!";
        case SpellId::PrismaticLight:
            return "Can't cast Prismatic Light outdoors!";
        default:
            return SpellFailedText;
    }
}

std::optional<std::string> spellWorldAvailabilityFailure(SpellId spellId, bool indoorMap)
{
    if ((indoorMap && isSpellOutdoorOnly(spellId))
        || (!indoorMap && isSpellIndoorOnly(spellId)))
    {
        return spellWorldUnavailableText(spellId, indoorMap);
    }

    return std::nullopt;
}

bool isActorPointInsideSpellView(
    const PartySpellCastRequest &request,
    float actorX,
    float actorY,
    float actorZ)
{
    if (!request.hasViewTransform)
    {
        return true;
    }

    const float cosPitch = std::cos(request.viewPitchRadians);
    const float sinPitch = std::sin(request.viewPitchRadians);
    const float cosYaw = std::cos(request.viewYawRadians);
    const float sinYaw = std::sin(request.viewYawRadians);
    const float forwardX = cosYaw * cosPitch;
    const float forwardY = sinYaw * cosPitch;
    const float forwardZ = sinPitch;
    const float rightX = -sinYaw;
    const float rightY = cosYaw;
    const float rightZ = 0.0f;
    const float upX = -cosYaw * sinPitch;
    const float upY = -sinYaw * sinPitch;
    const float upZ = cosPitch;
    const float deltaX = actorX - request.viewX;
    const float deltaY = actorY - request.viewY;
    const float deltaZ = actorZ - request.viewZ;
    const float forwardDistance = deltaX * forwardX + deltaY * forwardY + deltaZ * forwardZ;

    if (forwardDistance <= 0.0f)
    {
        return false;
    }

    const float halfVerticalFovTan = std::tan(CameraVerticalFovRadians * 0.5f);
    const float halfHorizontalFovTan = halfVerticalFovTan * std::max(0.1f, request.viewAspectRatio);
    const float lateralDistance = std::abs(deltaX * rightX + deltaY * rightY + deltaZ * rightZ);
    const float verticalDistance = std::abs(deltaX * upX + deltaY * upY + deltaZ * upZ);
    return lateralDistance <= forwardDistance * halfHorizontalFovTan
        && verticalDistance <= forwardDistance * halfVerticalFovTan;
}

bool areaSpellAffectsVisibleCreatures(SpellId spellId)
{
    return spellId == SpellId::PrismaticLight || spellId == SpellId::SoulDrinker;
}

struct BackendSpellRule
{
    uint32_t spellId = 0;
    PartySpellCastTargetKind targetKind = PartySpellCastTargetKind::None;
    PartySpellCastEffectKind effectKind = PartySpellCastEffectKind::Unsupported;
    SkillMastery requiredMastery = SkillMastery::Normal;
    std::array<int, 4> manaByMastery = {};
    std::array<int, 4> recoveryTicksByMastery = {};
    PartyBuffId partyBuffId = PartyBuffId::TorchLight;
    int baseDamage = 0;
    int bonusSkillDamage = 0;
    bool damageScalesLinearly = false;
    uint32_t multiProjectileCount = 1;
};

float ticksToRecoverySeconds(int ticks)
{
    return std::max(0.0f, static_cast<float>(ticks) / 128.0f * OeRealtimeRecoveryScale);
}

uint32_t spellSlotLevel(uint32_t spellId)
{
    if (spellId < FirstBaseSpellId || spellId > LastBaseSpellId)
    {
        return 1;
    }

    return ((spellId - 1) % 11) + 1;
}

int masteryIndex(SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Normal:
            return 0;
        case SkillMastery::Expert:
            return 1;
        case SkillMastery::Master:
            return 2;
        case SkillMastery::Grandmaster:
            return 3;
        case SkillMastery::None:
        default:
            return -1;
    }
}

BackendSpellRule makeBackendSpellRule(
    uint32_t spellId,
    PartySpellCastTargetKind targetKind,
    PartySpellCastEffectKind effectKind,
    SkillMastery requiredMastery,
    std::array<int, 4> manaByMastery = {},
    std::array<int, 4> recoveryTicksByMastery = {},
    PartyBuffId partyBuffId = PartyBuffId::TorchLight,
    int baseDamage = 0,
    int bonusSkillDamage = 0,
    bool damageScalesLinearly = false,
    uint32_t multiProjectileCount = 1)
{
    BackendSpellRule rule = {};
    rule.spellId = spellId;
    rule.targetKind = targetKind;
    rule.effectKind = effectKind;
    rule.requiredMastery = requiredMastery;
    rule.manaByMastery = manaByMastery;
    rule.recoveryTicksByMastery = recoveryTicksByMastery;
    rule.partyBuffId = partyBuffId;
    rule.baseDamage = baseDamage;
    rule.bonusSkillDamage = bonusSkillDamage;
    rule.damageScalesLinearly = damageScalesLinearly;
    rule.multiProjectileCount = multiProjectileCount;
    return rule;
}

bool ruleHasExplicitManaCost(const BackendSpellRule &rule)
{
    for (int manaCost : rule.manaByMastery)
    {
        if (manaCost > 0)
        {
            return true;
        }
    }

    return false;
}

bool ruleHasExplicitRecovery(const BackendSpellRule &rule)
{
    for (int recoveryTicks : rule.recoveryTicksByMastery)
    {
        if (recoveryTicks > 0)
        {
            return true;
        }
    }

    return false;
}

bool anyPartyMemberWeak(const Party &party)
{
    for (const Character &member : party.members())
    {
        if (member.conditions.test(static_cast<size_t>(CharacterCondition::Weak)))
        {
            return true;
        }
    }

    return false;
}

void appendAffectedCharacterIndex(std::vector<size_t> &indices, size_t memberIndex)
{
    if (std::find(indices.begin(), indices.end(), memberIndex) == indices.end())
    {
        indices.push_back(memberIndex);
    }
}

void appendAllPartyMemberIndices(const Party &party, std::vector<size_t> &indices)
{
    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        appendAffectedCharacterIndex(indices, memberIndex);
    }
}

SkillMastery defaultRequiredMasteryForSpellId(uint32_t spellId)
{
    if (spellIdInRange(spellId, SpellId::Glamour, SpellId::DarkfireBolt)
        || spellIdInRange(spellId, SpellId::Lifedrain, SpellId::Mistform)
        || spellIdInRange(spellId, SpellId::Fear, SpellId::WingBuffet))
    {
        const uint32_t offset =
            spellIdInRange(spellId, SpellId::Glamour, SpellId::DarkfireBolt)
                ? spellId - spellIdValue(SpellId::Glamour)
                : spellIdInRange(spellId, SpellId::Lifedrain, SpellId::Mistform)
                ? spellId - spellIdValue(SpellId::Lifedrain)
                : spellId - spellIdValue(SpellId::Fear);
        return offset == 0
            ? SkillMastery::Normal
            : offset == 1
            ? SkillMastery::Expert
            : offset == 2
            ? SkillMastery::Master
            : SkillMastery::Grandmaster;
    }

    const uint32_t level = spellSlotLevel(spellId);

    if (level >= 11)
    {
        return SkillMastery::Grandmaster;
    }

    if (level >= 8)
    {
        return SkillMastery::Master;
    }

    if (level >= 5)
    {
        return SkillMastery::Expert;
    }

    return SkillMastery::Normal;
}

int defaultManaCostForSpellId(uint32_t spellId)
{
    switch (spellSlotLevel(spellId))
    {
        case 1:
            return 1;
        case 2:
            return 2;
        case 3:
            return 3;
        case 4:
            return 4;
        case 5:
            return 5;
        case 6:
            return 8;
        case 7:
            return 10;
        case 8:
            return 15;
        case 9:
            return 20;
        case 10:
            return 25;
        case 11:
        default:
            return 30;
    }
}

int manaCostForSpellEntry(const SpellEntry &spellEntry, SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Expert:
            return spellEntry.expertManaCost;
        case SkillMastery::Master:
            return spellEntry.masterManaCost;
        case SkillMastery::Grandmaster:
            return spellEntry.grandmasterManaCost;
        case SkillMastery::Normal:
        case SkillMastery::None:
        default:
            return spellEntry.normalManaCost;
    }
}

int recoveryTicksForSpellEntry(const SpellEntry &spellEntry, SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Expert:
            return spellEntry.expertRecoveryTicks;
        case SkillMastery::Master:
            return spellEntry.masterRecoveryTicks;
        case SkillMastery::Grandmaster:
            return spellEntry.grandmasterRecoveryTicks;
        case SkillMastery::Normal:
        case SkillMastery::None:
        default:
            return spellEntry.normalRecoveryTicks;
    }
}

int manaCostForRule(const BackendSpellRule &rule, SkillMastery mastery)
{
    const int index = masteryIndex(mastery);
    return index >= 0 ? rule.manaByMastery[static_cast<size_t>(index)] : 0;
}

int recoveryTicksForRule(const BackendSpellRule &rule, SkillMastery mastery)
{
    const int index = masteryIndex(mastery);
    return index >= 0 ? rule.recoveryTicksByMastery[static_cast<size_t>(index)] : 0;
}

float secondsFromHours(float hours)
{
    return hours * 3600.0f;
}

float secondsFromMinutes(float minutes)
{
    return minutes * 60.0f;
}

std::optional<BackendSpellRule> resolveBackendSpellRule(uint32_t spellId, SkillMastery mastery)
{
    const uint32_t sparksCount = mastery == SkillMastery::Grandmaster
        ? 9
        : mastery == SkillMastery::Master
        ? 7
        : mastery == SkillMastery::Expert
        ? 5
        : 3;
    const uint32_t poisonSprayCount = mastery == SkillMastery::Grandmaster
        ? 7
        : mastery == SkillMastery::Master
        ? 5
        : mastery == SkillMastery::Expert
        ? 3
        : 1;

    switch (spellIdFromValue(spellId))
    {
        case SpellId::TorchLight:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {1, 1, 1, 1}, {60, 60, 60, 40}, PartyBuffId::TorchLight);
        case SpellId::FireBolt:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Normal, {2, 2, 2, 2}, {110, 110, 100, 90}, PartyBuffId::TorchLight, 0, 3, false);
        case SpellId::FireResistance:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {3, 3, 3, 3}, {120, 120, 120, 120}, PartyBuffId::FireResistance);
        case SpellId::FireAura:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::InventoryItem, PartySpellCastEffectKind::UtilityUi, SkillMastery::Normal, {4, 4, 4, 4}, {120, 120, 120, 120}, PartyBuffId::TorchLight);
        case SpellId::Haste:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Expert, {5, 5, 5, 5}, {120, 120, 120, 120}, PartyBuffId::Haste);
        case SpellId::Fireball:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Expert, {8, 8, 8, 8}, {100, 100, 90, 80}, PartyBuffId::TorchLight, 0, 6, false);
        case SpellId::FireSpike:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::AreaEffect, SkillMastery::Expert, {10, 10, 10, 10}, {150, 150, 150, 150}, PartyBuffId::TorchLight, 1, 6, false);
        case SpellId::Immolation:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Master, {15, 15, 15, 15}, {120, 120, 120, 120}, PartyBuffId::Immolation);
        case SpellId::MeteorShower:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::Projectile, SkillMastery::Master, {20, 20, 20, 20}, {100, 100, 100, 90}, PartyBuffId::TorchLight, 8, 1, true);
        case SpellId::Inferno:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 12, 2, true);
        case SpellId::Incinerate:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Grandmaster, {30, 30, 30, 30}, {90, 90, 90, 90}, PartyBuffId::TorchLight, 15, 15, false);
        case SpellId::WizardEye:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {1, 1, 1, 0}, {60, 60, 60, 60}, PartyBuffId::WizardEye);
        case SpellId::FeatherFall:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {2, 2, 2, 2}, {120, 120, 120, 100}, PartyBuffId::FeatherFall);
        case SpellId::AirResistance:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {3, 3, 3, 3}, {120, 120, 120, 120}, PartyBuffId::AirResistance);
        case SpellId::Sparks:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::MultiProjectile, SkillMastery::Normal, {4, 4, 4, 4}, {110, 100, 90, 80}, PartyBuffId::TorchLight, 2, 1, true, sparksCount);
        case SpellId::Jump:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::Jump, SkillMastery::Expert, {5, 5, 5, 5}, {90, 90, 70, 50}, PartyBuffId::TorchLight);
        case SpellId::Shield:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Expert, {8, 8, 8, 8}, {120, 120, 120, 120}, PartyBuffId::Shield);
        case SpellId::LightningBolt:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Expert, {10, 10, 10, 10}, {100, 100, 90, 70}, PartyBuffId::TorchLight, 0, 8, false);
        case SpellId::Invisibility:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Master, {}, {}, PartyBuffId::Invisibility);
        case SpellId::Implosion:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 10, 10, false);
        case SpellId::Fly:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Master, {}, {}, PartyBuffId::Fly);
        case SpellId::Starburst:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::Projectile, SkillMastery::Grandmaster, {}, {}, PartyBuffId::TorchLight, 20, 1, true);
        case SpellId::Awaken:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyRestore, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight);
        case SpellId::PoisonSpray:
            return makeBackendSpellRule(spellId,
                PartySpellCastTargetKind::GroundPoint,
                PartySpellCastEffectKind::MultiProjectile,
                SkillMastery::Normal,
                {},
                {},
                PartyBuffId::TorchLight,
                2,
                2,
                true,
                poisonSprayCount);
        case SpellId::WaterResistance:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {3, 3, 3, 3}, {120, 120, 120, 120}, PartyBuffId::WaterResistance);
        case SpellId::IceBolt:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight, 1, 4, false);
        case SpellId::WaterWalk:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Expert, {}, {}, PartyBuffId::WaterWalk);
        case SpellId::RechargeItem:
            return makeBackendSpellRule(
                spellId,
                PartySpellCastTargetKind::InventoryItem,
                PartySpellCastEffectKind::UtilityUi,
                SkillMastery::Expert,
                {8, 8, 8, 8},
                {200, 200, 200, 200},
                PartyBuffId::TorchLight);
        case SpellId::AcidBurst:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight, 9, 9, false);
        case SpellId::EnchantItem:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::InventoryItem, PartySpellCastEffectKind::UtilityUi, SkillMastery::Master, {15, 15, 15, 15}, {140, 140, 140, 140}, PartyBuffId::TorchLight);
        case SpellId::TownPortal:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::UtilityUi, PartySpellCastEffectKind::UtilityUi, SkillMastery::Master, {20, 20, 20, 20}, {200, 200, 200, 200}, PartyBuffId::TorchLight);
        case SpellId::LloydsBeacon:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::UtilityUi, PartySpellCastEffectKind::UtilityUi, SkillMastery::Grandmaster, {30, 30, 30, 30}, {250, 250, 250, 250}, PartyBuffId::TorchLight);
        case SpellId::IceBlast:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::MultiProjectile, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 12, 6, true, 7);
        case SpellId::Stun:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight);
        case SpellId::Slow:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight);
        case SpellId::EarthResistance:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {3, 3, 3, 3}, {120, 120, 120, 120}, PartyBuffId::EarthResistance);
        case SpellId::DeadlySwarm:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight, 5, 3, false);
        case SpellId::StoneSkin:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Expert, {5, 5, 5, 5}, {120, 120, 120, 120}, PartyBuffId::Stoneskin);
        case SpellId::Blades:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight, 1, 9, false);
        case SpellId::StoneToFlesh:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight);
        case SpellId::RockBlast:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::Projectile, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 10, 10, false);
        case SpellId::Telekinesis:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::UtilityUi, PartySpellCastEffectKind::UtilityUi, SkillMastery::Master, {20, 20, 20, 20}, {150, 150, 150, 150}, PartyBuffId::TorchLight);
        case SpellId::DeathBlossom:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::Projectile, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 20, 2, true);
        case SpellId::MassDistortion:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Grandmaster, {}, {}, PartyBuffId::TorchLight);
        case SpellId::DetectLife:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {}, {}, PartyBuffId::DetectLife);
        case SpellId::Bless:
            return makeBackendSpellRule(
                spellId,
                mastery == SkillMastery::Normal
                    ? PartySpellCastTargetKind::Character
                    : PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::CharacterBuff,
                SkillMastery::Normal,
                {},
                {},
                PartyBuffId::TorchLight);
        case SpellId::Fate:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::ActorOrCharacter, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight);
        case SpellId::TurnUndead:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight);
        case SpellId::RemoveCurse:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight);
        case SpellId::Preservation:
            return makeBackendSpellRule(
                spellId,
                mastery == SkillMastery::Master || mastery == SkillMastery::Grandmaster
                    ? PartySpellCastTargetKind::None
                    : PartySpellCastTargetKind::Character,
                PartySpellCastEffectKind::CharacterBuff,
                SkillMastery::Normal,
                {},
                {},
                PartyBuffId::TorchLight);
        case SpellId::Heroism:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Expert, {10, 10, 10, 10}, {120, 120, 120, 120}, PartyBuffId::Heroism);
        case SpellId::SpiritLash:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 10, 8, false);
        case SpellId::RaiseDead:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight);
        case SpellId::SharedLife:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyRestore, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight);
        case SpellId::Resurrection:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Grandmaster, {}, {}, PartyBuffId::TorchLight);
        case SpellId::Telepathy:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::UtilityUi, PartySpellCastEffectKind::UtilityUi, SkillMastery::Normal, {1, 1, 1, 1}, {90, 90, 90, 90}, PartyBuffId::TorchLight);
        case SpellId::RemoveFear:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight);
        case SpellId::MindResistance:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {}, {}, PartyBuffId::MindResistance);
        case SpellId::MindBlast:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight, 3, 3, false);
        case SpellId::Charm:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight);
        case SpellId::CureParalysis:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight);
        case SpellId::Berserk:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight);
        case SpellId::MassFear:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight);
        case SpellId::CureInsanity:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight);
        case SpellId::PsychicShock:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 12, 12, false);
        case SpellId::Enslave:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Grandmaster, {}, {}, PartyBuffId::TorchLight);
        case SpellId::CureWeakness:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight);
        case SpellId::Heal:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight);
        case SpellId::BodyResistance:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {3, 3, 3, 3}, {120, 120, 120, 120}, PartyBuffId::BodyResistance);
        case SpellId::Harm:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight, 8, 2, false);
        case SpellId::Regeneration:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterBuff, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight);
        case SpellId::CurePoison:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight);
        case SpellId::Hammerhands:
            return makeBackendSpellRule(
                spellId,
                mastery == SkillMastery::Grandmaster
                    ? PartySpellCastTargetKind::None
                    : PartySpellCastTargetKind::Character,
                PartySpellCastEffectKind::CharacterBuff,
                SkillMastery::Expert,
                {},
                {},
                PartyBuffId::TorchLight);
        case SpellId::CureDisease:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight);
        case SpellId::ProtectionFromMagic:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Master, {20, 20, 20, 20}, {120, 120, 120, 120}, PartyBuffId::ProtectionFromMagic);
        case SpellId::FlyingFist:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Master, {25, 25, 25, 25}, {110, 110, 110, 100}, PartyBuffId::TorchLight, 30, 5, false);
        case SpellId::PowerCure:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyRestore, SkillMastery::Grandmaster, {}, {}, PartyBuffId::TorchLight);
        case SpellId::LightBolt:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Normal, {5, 5, 5, 5}, {110, 100, 90, 80}, PartyBuffId::TorchLight, 0, 4, false);
        case SpellId::DestroyUndead:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight, 16, 16, false);
        case SpellId::DispelMagic:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight);
        case SpellId::Paralyze:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight);
        case SpellId::SummonWisp:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Normal, {25, 25, 25, 25}, {140, 140, 140, 140}, PartyBuffId::TorchLight);
        case SpellId::DayOfGods:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Expert, {30, 30, 30, 30}, {500, 500, 500, 500}, PartyBuffId::DayOfGods);
        case SpellId::PrismaticLight:
            return makeBackendSpellRule(
                spellId,
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::AreaEffect,
                SkillMastery::Expert,
                {},
                {},
                PartyBuffId::TorchLight,
                25,
                1,
                true);
        case SpellId::DayOfProtection:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Master, {40, 40, 40, 40}, {500, 500, 500, 500}, PartyBuffId::BodyResistance);
        case SpellId::HourOfPower:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Master, {45, 45, 45, 45}, {250, 250, 250, 250}, PartyBuffId::Heroism);
        case SpellId::Sunray:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 20, 20, false);
        case SpellId::DivineIntervention:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyRestore, SkillMastery::Grandmaster, {}, {}, PartyBuffId::TorchLight);
        case SpellId::Reanimate:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::ActorOrCharacter, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight);
        case SpellId::ToxicCloud:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight, 25, 10, false);
        case SpellId::VampiricWeapon:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::InventoryItem, PartySpellCastEffectKind::UtilityUi, SkillMastery::Normal, {20, 20, 20, 20}, {120, 100, 90, 120}, PartyBuffId::TorchLight);
        case SpellId::ShrinkingRay:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight);
        case SpellId::Shrapmetal:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::MultiProjectile, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight, 1, 6, true, 5);
        case SpellId::ControlUndead:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight);
        case SpellId::PainReflection:
            return makeBackendSpellRule(
                spellId,
                mastery == SkillMastery::Master || mastery == SkillMastery::Grandmaster
                    ? PartySpellCastTargetKind::None
                    : PartySpellCastTargetKind::Character,
                PartySpellCastEffectKind::CharacterBuff,
                SkillMastery::Expert,
                {},
                {},
                PartyBuffId::TorchLight);
        case SpellId::DarkGrasp:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight);
        case SpellId::DragonBreath:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 1, 25, false);
        case SpellId::Armageddon:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 50, 1, false);
        case SpellId::SoulDrinker:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Grandmaster, {}, {}, PartyBuffId::TorchLight, 25, 8, false);
        case SpellId::Glamour:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterBuff, SkillMastery::Normal, {5, 5, 5, 5}, {100, 100, 100, 100}, PartyBuffId::TorchLight);
        case SpellId::TravelersBoon:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Expert, {10, 10, 10, 10}, {100, 100, 100, 100}, PartyBuffId::TorchLight);
        case SpellId::Blind:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Master, {15, 15, 15, 15}, {120, 120, 120, 120}, PartyBuffId::TorchLight);
        case SpellId::DarkfireBolt:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Grandmaster, {30, 30, 30, 30}, {90, 90, 90, 90}, PartyBuffId::TorchLight, 0, 17, false);
        case SpellId::Lifedrain:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {5, 5, 5, 5}, {100, 80, 80, 80}, PartyBuffId::TorchLight, 3, 3, false);
        case SpellId::Levitate:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Expert, {10, 10, 10, 10}, {110, 110, 110, 110}, PartyBuffId::Levitate);
        case SpellId::VampireCharm:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Master, {20, 20, 20, 20}, {110, 110, 110, 110}, PartyBuffId::TorchLight);
        case SpellId::Mistform:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterBuff, SkillMastery::Grandmaster, {30, 30, 30, 30}, {110, 110, 110, 110}, PartyBuffId::TorchLight);
        case SpellId::Fear:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {5, 5, 5, 5}, {100, 100, 100, 100}, PartyBuffId::TorchLight);
        case SpellId::FlameBlast:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Expert, {10, 10, 10, 10}, {100, 100, 100, 100}, PartyBuffId::TorchLight, 10, 10, false);
        case SpellId::Flight:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Master, {15, 15, 15, 15}, {120, 120, 120, 120}, PartyBuffId::Fly);
        case SpellId::WingBuffet:
            return makeBackendSpellRule(spellId, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Grandmaster, {30, 30, 30, 30}, {110, 110, 110, 110}, PartyBuffId::TorchLight);
        default:
            return std::nullopt;
    }
}

bool resolveSpellSkill(
    const Character &caster,
    uint32_t spellId,
    const PartySpellCastRequest &request,
    uint32_t &skillLevel,
    SkillMastery &skillMastery)
{
    if (request.skillLevelOverride > 0 && request.skillMasteryOverride != SkillMastery::None)
    {
        skillLevel = request.skillLevelOverride;
        skillMastery = request.skillMasteryOverride;
        return true;
    }

    const std::optional<std::string> skillName = resolveMagicSkillName(spellId);

    if (!skillName)
    {
        return false;
    }

    const CharacterSkill *pSkill = caster.findSkill(*skillName);

    if (pSkill == nullptr || pSkill->mastery == SkillMastery::None)
    {
        return false;
    }

    const auto bonusIt = caster.itemSkillBonuses.find(*skillName);
    const int bonusLevel = bonusIt != caster.itemSkillBonuses.end() ? bonusIt->second : 0;
    skillLevel = std::max(0, static_cast<int>(pSkill->level) + bonusLevel);
    skillMastery = pSkill->mastery;
    return skillLevel > 0;
}

bx::Vec3 resolveActorTargetPoint(const GameplayRuntimeActorState &actor)
{
    return {
        actor.preciseX,
        actor.preciseY,
        actor.preciseZ + std::max(48.0f, static_cast<float>(actor.height) * 0.6f)
    };
}

int rollSpellDamage(const BackendSpellRule &rule, const SpellEntry &spellEntry, uint32_t skillLevel)
{
    const bool hasExplicitDamage = rule.baseDamage > 0 || rule.bonusSkillDamage > 0;
    const int baseDamage = hasExplicitDamage ? rule.baseDamage : spellEntry.damageBase;
    const int bonusSkillDamage = hasExplicitDamage ? rule.bonusSkillDamage : spellEntry.damageDiceSides;

    if (skillLevel == 0)
    {
        return std::max(0, baseDamage);
    }

    if (rule.damageScalesLinearly)
    {
        return std::max(0, baseDamage + bonusSkillDamage * static_cast<int>(skillLevel));
    }

    static thread_local std::mt19937 rng(std::random_device{}());
    const int diceSides = std::max(1, bonusSkillDamage);
    std::uniform_int_distribution<int> distribution(1, diceSides);
    int damage = baseDamage;

    for (uint32_t rollIndex = 0; rollIndex < skillLevel; ++rollIndex)
    {
        damage += distribution(rng);
    }

    return std::max(0, damage);
}

float resolvePartyBuffDurationSeconds(uint32_t spellId, uint32_t skillLevel, SkillMastery mastery)
{
    switch (spellIdFromValue(spellId))
    {
        case SpellId::TorchLight:
        case SpellId::WizardEye:
        case SpellId::Invisibility:
        case SpellId::Fly:
        case SpellId::WaterWalk:
        case SpellId::DetectLife:
        case SpellId::ProtectionFromMagic:
        case SpellId::Glamour:
            return secondsFromHours(static_cast<float>(skillLevel));
        case SpellId::FireResistance:
        case SpellId::AirResistance:
        case SpellId::WaterResistance:
        case SpellId::EarthResistance:
        case SpellId::BodyResistance:
            return secondsFromHours(static_cast<float>(skillLevel));
        case SpellId::FeatherFall:
            if (mastery == SkillMastery::Normal)
            {
                return secondsFromMinutes(static_cast<float>(5 * skillLevel));
            }

            if (mastery == SkillMastery::Expert)
            {
                return secondsFromMinutes(static_cast<float>(10 * skillLevel));
            }

            return secondsFromHours(static_cast<float>(skillLevel));
        case SpellId::Haste:
            if (mastery == SkillMastery::Expert)
            {
                return secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(skillLevel));
            }

            if (mastery == SkillMastery::Master)
            {
                return secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(3 * skillLevel));
            }

            return secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(4 * skillLevel));
        case SpellId::Shield:
        case SpellId::StoneSkin:
        case SpellId::Heroism:
            if (mastery == SkillMastery::Expert)
            {
                return secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel));
            }

            if (mastery == SkillMastery::Master)
            {
                return secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * skillLevel));
            }

            return secondsFromHours(static_cast<float>(skillLevel + 1));
        case SpellId::Immolation:
            return mastery == SkillMastery::Grandmaster
                ? secondsFromMinutes(static_cast<float>(10 * skillLevel))
                : secondsFromMinutes(static_cast<float>(skillLevel));
        case SpellId::Levitate:
            return mastery == SkillMastery::Expert
                ? secondsFromMinutes(static_cast<float>(10 * skillLevel))
                : mastery == SkillMastery::Master
                ? secondsFromHours(static_cast<float>(skillLevel))
                : secondsFromHours(static_cast<float>(3 * skillLevel));
        case SpellId::DayOfGods:
            return mastery == SkillMastery::Expert
                ? secondsFromHours(static_cast<float>(3 * skillLevel))
                : mastery == SkillMastery::Master
                ? secondsFromHours(static_cast<float>(4 * skillLevel))
                : secondsFromHours(static_cast<float>(5 * skillLevel));
        case SpellId::DayOfProtection:
            return mastery == SkillMastery::Master
                ? secondsFromHours(static_cast<float>(4 * skillLevel))
                : secondsFromHours(static_cast<float>(5 * skillLevel));
        case SpellId::HourOfPower:
            return mastery == SkillMastery::Master
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * 4 * skillLevel))
                : secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * 5 * skillLevel));
        case SpellId::TravelersBoon:
            return mastery == SkillMastery::Expert
                ? secondsFromMinutes(static_cast<float>(30 * skillLevel))
                : mastery == SkillMastery::Master
                ? secondsFromHours(static_cast<float>(skillLevel))
                : secondsFromHours(static_cast<float>(2 * skillLevel));
        case SpellId::Flight:
            return mastery == SkillMastery::Grandmaster
                ? secondsFromHours(24.0f)
                : secondsFromHours(static_cast<float>(skillLevel));
        default:
            return 0.0f;
    }
}

int resolvePartyBuffPower(uint32_t spellId, uint32_t skillLevel, SkillMastery mastery)
{
    switch (spellIdFromValue(spellId))
    {
        case SpellId::TorchLight:
            return mastery == SkillMastery::Normal ? 2 : mastery == SkillMastery::Expert ? 3 : 4;
        case SpellId::FireResistance:
        case SpellId::AirResistance:
        case SpellId::WaterResistance:
        case SpellId::EarthResistance:
        case SpellId::MindResistance:
        case SpellId::BodyResistance:
            return mastery == SkillMastery::Normal
                ? static_cast<int>(skillLevel)
                : mastery == SkillMastery::Expert
                ? static_cast<int>(2 * skillLevel)
                : mastery == SkillMastery::Master
                ? static_cast<int>(3 * skillLevel)
                : static_cast<int>(4 * skillLevel);
        case SpellId::StoneSkin:
        case SpellId::Heroism:
            return static_cast<int>(skillLevel) + 5;
        case SpellId::ProtectionFromMagic:
            return static_cast<int>(skillLevel);
        case SpellId::DayOfGods:
            return mastery == SkillMastery::Expert
                ? static_cast<int>(3 * skillLevel + 10)
                : mastery == SkillMastery::Master
                ? static_cast<int>(4 * skillLevel + 10)
                : static_cast<int>(5 * skillLevel + 10);
        case SpellId::DayOfProtection:
            return mastery == SkillMastery::Master
                ? static_cast<int>(4 * skillLevel)
                : static_cast<int>(5 * skillLevel);
        case SpellId::HourOfPower:
            return static_cast<int>(skillLevel) + 5;
        case SpellId::Immolation:
            return static_cast<int>(skillLevel);
        case SpellId::Glamour:
            return mastery == SkillMastery::Grandmaster
                ? static_cast<int>(3 * skillLevel)
                : static_cast<int>(2 * skillLevel);
        default:
            return 0;
    }
}

void applyCompositePartyBuff(
    Party &party,
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery mastery,
    uint32_t casterMemberIndex)
{
    const float durationSeconds = resolvePartyBuffDurationSeconds(spellId, skillLevel, mastery);
    const int power = resolvePartyBuffPower(spellId, skillLevel, mastery);

    switch (spellIdFromValue(spellId))
    {
        case SpellId::DayOfProtection:
            party.applyPartyBuff(PartyBuffId::BodyResistance, durationSeconds, power, spellId, skillLevel, mastery, casterMemberIndex);
            party.applyPartyBuff(PartyBuffId::MindResistance, durationSeconds, power, spellId, skillLevel, mastery, casterMemberIndex);
            party.applyPartyBuff(PartyBuffId::FireResistance, durationSeconds, power, spellId, skillLevel, mastery, casterMemberIndex);
            party.applyPartyBuff(PartyBuffId::WaterResistance, durationSeconds, power, spellId, skillLevel, mastery, casterMemberIndex);
            party.applyPartyBuff(PartyBuffId::AirResistance, durationSeconds, power, spellId, skillLevel, mastery, casterMemberIndex);
            party.applyPartyBuff(PartyBuffId::EarthResistance, durationSeconds, power, spellId, skillLevel, mastery, casterMemberIndex);
            party.applyPartyBuff(PartyBuffId::FeatherFall, durationSeconds, 0, spellId, skillLevel, mastery, casterMemberIndex);
            party.applyPartyBuff(PartyBuffId::WizardEye, durationSeconds, 0, spellId, skillLevel, mastery, casterMemberIndex);
            break;
        case SpellId::HourOfPower:
        {
            const float hasteDurationSeconds = mastery == SkillMastery::Master
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(3 * 4 * skillLevel))
                : secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(4 * 5 * skillLevel));
            party.applyPartyBuff(PartyBuffId::Heroism, durationSeconds, power, spellId, skillLevel, mastery, casterMemberIndex);
            party.applyPartyBuff(PartyBuffId::Shield, durationSeconds, 0, spellId, skillLevel, mastery, casterMemberIndex);
            party.applyPartyBuff(PartyBuffId::Stoneskin, durationSeconds, power, spellId, skillLevel, mastery, casterMemberIndex);

            if (!anyPartyMemberWeak(party))
            {
                party.applyPartyBuff(
                    PartyBuffId::Haste,
                    hasteDurationSeconds,
                    0,
                    spellId,
                    skillLevel,
                    mastery,
                    casterMemberIndex);
            }

            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                party.applyCharacterBuff(
                    memberIndex,
                    CharacterBuffId::Bless,
                    durationSeconds,
                    power,
                    spellIdValue(SpellId::Bless),
                    static_cast<uint32_t>(power),
                    mastery,
                    casterMemberIndex);
            }
            break;
        }
        case SpellId::TravelersBoon:
        {
            const float durationSeconds = resolvePartyBuffDurationSeconds(spellId, skillLevel, mastery);
            party.applyPartyBuff(PartyBuffId::TorchLight, durationSeconds, 3, spellId, skillLevel, mastery, casterMemberIndex);
            party.applyPartyBuff(PartyBuffId::WizardEye, durationSeconds, 0, spellId, skillLevel, mastery, casterMemberIndex);
            party.applyPartyBuff(PartyBuffId::FeatherFall, durationSeconds, 0, spellId, skillLevel, mastery, casterMemberIndex);
            break;
        }
        case SpellId::Levitate:
        {
            const float durationSeconds = resolvePartyBuffDurationSeconds(spellId, skillLevel, mastery);
            party.applyPartyBuff(PartyBuffId::Levitate, durationSeconds, 0, spellId, skillLevel, mastery, casterMemberIndex);
            party.applyPartyBuff(PartyBuffId::WaterWalk, durationSeconds, 0, spellId, skillLevel, mastery, casterMemberIndex);
            party.applyPartyBuff(PartyBuffId::FeatherFall, durationSeconds, 0, spellId, skillLevel, mastery, casterMemberIndex);
            break;
        }
        default:
            break;
    }
}

float resolveCharacterBuffDurationSeconds(uint32_t spellId, uint32_t skillLevel, SkillMastery mastery)
{
    switch (spellIdFromValue(spellId))
    {
        case SpellId::Bless:
            return mastery == SkillMastery::Normal
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel))
                : mastery == SkillMastery::Expert
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel))
                : mastery == SkillMastery::Master
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * skillLevel))
                : secondsFromHours(1.0f + static_cast<float>(skillLevel));
        case SpellId::Fate:
            return secondsFromMinutes(5.0f);
        case SpellId::Preservation:
            return mastery == SkillMastery::Expert
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel))
                : mastery == SkillMastery::Master
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel))
                : mastery == SkillMastery::Grandmaster
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * skillLevel))
                : secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * skillLevel));
        case SpellId::FireAura:
            return secondsFromHours(static_cast<float>(std::max<uint32_t>(1, skillLevel)));
        case SpellId::Regeneration:
        case SpellId::Hammerhands:
            return secondsFromHours(static_cast<float>(std::max<uint32_t>(1, skillLevel)));
        case SpellId::VampiricWeapon:
            return mastery == SkillMastery::Grandmaster
                ? secondsFromHours(24.0f * 365.0f)
                : secondsFromHours(static_cast<float>(std::max<uint32_t>(1, skillLevel)));
        case SpellId::Glamour:
            return mastery == SkillMastery::Master
                ? secondsFromHours(static_cast<float>(std::max<uint32_t>(1, skillLevel)))
                : secondsFromMinutes(static_cast<float>(5 * std::max<uint32_t>(1, skillLevel)));
        case SpellId::PainReflection:
            return mastery == SkillMastery::Grandmaster
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * skillLevel))
                : secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel));
        case SpellId::Mistform:
            return secondsFromHours(static_cast<float>(std::max<uint32_t>(1, skillLevel)));
        default:
            return secondsFromHours(static_cast<float>(std::max<uint32_t>(1, skillLevel)));
    }
}

int resolveCharacterBuffPower(uint32_t spellId, uint32_t skillLevel, SkillMastery mastery)
{
    switch (spellIdFromValue(spellId))
    {
        case SpellId::Bless:
            return 5 + static_cast<int>(skillLevel);
        case SpellId::Fate:
            return mastery == SkillMastery::Normal
                ? 20 + static_cast<int>(skillLevel)
                : mastery == SkillMastery::Expert
                ? 20 + static_cast<int>(2 * skillLevel)
                : mastery == SkillMastery::Master
                ? 20 + static_cast<int>(4 * skillLevel)
                : 20 + static_cast<int>(6 * skillLevel);
        case SpellId::FireAura:
            return mastery == SkillMastery::Grandmaster
                ? static_cast<int>(3 * skillLevel + 3)
                : mastery == SkillMastery::Master
                ? static_cast<int>(2 * skillLevel + 3)
                : mastery == SkillMastery::Expert
                ? static_cast<int>(skillLevel + 3)
                : static_cast<int>(skillLevel + 1);
        case SpellId::Regeneration:
            return mastery == SkillMastery::Grandmaster
                ? 4
                : mastery == SkillMastery::Master
                ? 3
                : 2;
        case SpellId::Hammerhands:
        case SpellId::PainReflection:
            return static_cast<int>(skillLevel);
        case SpellId::VampiricWeapon:
            return mastery == SkillMastery::Grandmaster
                ? 100
                : mastery == SkillMastery::Master
                ? 75
                : mastery == SkillMastery::Expert
                ? 50
                : 33;
        case SpellId::Glamour:
            return mastery == SkillMastery::Grandmaster
                ? static_cast<int>(3 * skillLevel)
                : static_cast<int>(skillLevel);
        case SpellId::Mistform:
            return 1;
        default:
            return static_cast<int>(skillLevel);
    }
}

bool applyCharacterRestoreSpell(
    Party &party,
    uint32_t spellId,
    size_t targetCharacterIndex,
    uint32_t skillLevel)
{
    switch (spellIdFromValue(spellId))
    {
        case SpellId::StoneToFlesh:
            return party.clearMemberCondition(targetCharacterIndex, CharacterCondition::Petrified);
        case SpellId::RemoveCurse:
            return party.clearMemberCondition(targetCharacterIndex, CharacterCondition::Cursed);
        case SpellId::RaiseDead:
            return party.reviveMember(targetCharacterIndex, std::max(1, static_cast<int>(skillLevel) * 5), true);
        case SpellId::Resurrection:
            return party.reviveMember(targetCharacterIndex, std::max(1, static_cast<int>(skillLevel) * 10), true);
        case SpellId::RemoveFear:
            return party.clearMemberCondition(targetCharacterIndex, CharacterCondition::Fear);
        case SpellId::CureParalysis:
            return party.clearMemberCondition(targetCharacterIndex, CharacterCondition::Paralyzed);
        case SpellId::CureInsanity:
            return party.clearMemberCondition(targetCharacterIndex, CharacterCondition::Insane);
        case SpellId::CureWeakness:
            return party.clearMemberCondition(targetCharacterIndex, CharacterCondition::Weak);
        case SpellId::Heal:
            return party.healMember(targetCharacterIndex, 5 + static_cast<int>(2 * skillLevel));
        case SpellId::CurePoison:
        {
            const bool weak = party.clearMemberCondition(targetCharacterIndex, CharacterCondition::PoisonWeak);
            const bool medium = party.clearMemberCondition(targetCharacterIndex, CharacterCondition::PoisonMedium);
            const bool severe = party.clearMemberCondition(targetCharacterIndex, CharacterCondition::PoisonSevere);
            return weak || medium || severe;
        }
        case SpellId::CureDisease:
        {
            const bool weak = party.clearMemberCondition(targetCharacterIndex, CharacterCondition::DiseaseWeak);
            const bool medium = party.clearMemberCondition(targetCharacterIndex, CharacterCondition::DiseaseMedium);
            const bool severe = party.clearMemberCondition(targetCharacterIndex, CharacterCondition::DiseaseSevere);
            return weak || medium || severe;
        }
        default:
            return false;
    }
}

PartySpellCastResult makeFailure(
    uint32_t spellId,
    PartySpellCastStatus status,
    PartySpellCastTargetKind targetKind,
    PartySpellCastEffectKind effectKind,
    const std::string &statusText)
{
    PartySpellCastResult result = {};
    result.spellId = spellId;
    result.status = status;
    result.targetKind = targetKind;
    result.effectKind = effectKind;
    result.statusText = statusText;
    return result;
}
}

PartySpellCastResult PartySpellSystem::castSpell(
    Party &party,
    IGameplayWorldRuntime &worldRuntime,
    const SpellTable &spellTable,
    const PartySpellCastRequest &request)
{
    PartySpellCastResult result = {};
    result.spellId = request.spellId;

    Character *pCaster = party.member(request.casterMemberIndex);

    if (pCaster == nullptr)
    {
        return makeFailure(
            request.spellId,
            PartySpellCastStatus::InvalidCaster,
            PartySpellCastTargetKind::None,
            PartySpellCastEffectKind::Unsupported,
            SpellFailedText);
    }

    const SpellEntry *pSpellEntry = spellTable.findById(static_cast<int>(request.spellId));

    if (pSpellEntry == nullptr)
    {
        return makeFailure(
            request.spellId,
            PartySpellCastStatus::InvalidSpell,
            PartySpellCastTargetKind::None,
            PartySpellCastEffectKind::Unsupported,
            SpellFailedText);
    }

    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;

    if (!resolveSpellSkill(*pCaster, request.spellId, request, skillLevel, skillMastery))
    {
        return makeFailure(
            request.spellId,
            PartySpellCastStatus::NotSkilledEnough,
            PartySpellCastTargetKind::None,
            PartySpellCastEffectKind::Unsupported,
            "Not skilled enough");
    }

    const std::optional<BackendSpellRule> rule = resolveBackendSpellRule(request.spellId, skillMastery);

    if (!rule)
    {
        return makeFailure(
            request.spellId,
            PartySpellCastStatus::Unsupported,
            PartySpellCastTargetKind::None,
            PartySpellCastEffectKind::Unsupported,
            SpellFailedText);
    }

    result.targetKind = rule->targetKind;
    result.effectKind = rule->effectKind;
    result.skillLevel = skillLevel;
    result.skillMastery = skillMastery;

    const SkillMastery requiredMastery =
        rule->requiredMastery != SkillMastery::None
            ? rule->requiredMastery
            : defaultRequiredMasteryForSpellId(request.spellId);

    if (!request.bypassRequiredMastery && skillMastery < requiredMastery)
    {
        return makeFailure(
            request.spellId,
            PartySpellCastStatus::NotSkilledEnough,
            rule->targetKind,
            rule->effectKind,
            "Not skilled enough");
    }

    result.manaCost = static_cast<uint32_t>(std::max(
        0,
        ruleHasExplicitManaCost(*rule)
            ? manaCostForRule(*rule, skillMastery)
            : std::max(manaCostForSpellEntry(*pSpellEntry, skillMastery), defaultManaCostForSpellId(request.spellId))));
    const int baseSpellRecoveryTicks =
        ruleHasExplicitRecovery(*rule)
            ? recoveryTicksForRule(*rule, skillMastery)
            : recoveryTicksForSpellEntry(*pSpellEntry, skillMastery);
    int spellRecoveryTicks = baseSpellRecoveryTicks;

    if (spellIdFromValue(request.spellId) == SpellId::DispelMagic)
    {
        spellRecoveryTicks = std::max(0, spellRecoveryTicks - static_cast<int>(skillLevel));
    }
    else if (spellIdFromValue(request.spellId) == SpellId::DivineIntervention)
    {
        spellRecoveryTicks = std::max(0, 5 * static_cast<int>(skillLevel));
    }

    result.recoverySeconds = ticksToRecoverySeconds(spellRecoveryTicks);
    const float failureRecoverySeconds = ticksToRecoverySeconds(baseSpellRecoveryTicks) * SpellFailureRecoveryScale;
    const auto makeFailureWithRecovery =
        [&](PartySpellCastStatus status,
            PartySpellCastTargetKind targetKind,
            PartySpellCastEffectKind effectKind,
            const std::string &statusText) -> PartySpellCastResult
        {
            PartySpellCastResult failure = makeFailure(request.spellId, status, targetKind, effectKind, statusText);
            failure.skillLevel = skillLevel;
            failure.skillMastery = skillMastery;
            failure.recoverySeconds = failureRecoverySeconds;

            if (request.applyRecovery && failureRecoverySeconds > 0.0f)
            {
                party.applyRecoveryToMember(request.casterMemberIndex, failureRecoverySeconds);
            }

            return failure;
        };

    if (request.spendMana && !party.canSpendSpellPoints(request.casterMemberIndex, static_cast<int>(result.manaCost)))
    {
        return makeFailure(
            request.spellId,
            PartySpellCastStatus::NotEnoughSpellPoints,
            rule->targetKind,
            rule->effectKind,
            "Not enough spell points");
    }

    if (request.spendMana
        && request.applyRecovery
        && request.skillLevelOverride == 0
        && !request.bypassRequiredMastery
        && spellIdFromValue(request.spellId) != SpellId::None
        && pCaster->conditions.test(static_cast<size_t>(CharacterCondition::Cursed)))
    {
        static thread_local std::mt19937 rng(std::random_device{}());

        if (std::uniform_int_distribution<int>(0, 99)(rng) < 50)
        {
            party.spendSpellPoints(request.casterMemberIndex, static_cast<int>(result.manaCost));
            return makeFailureWithRecovery(
                PartySpellCastStatus::Failed,
                rule->targetKind,
                rule->effectKind,
                SpellFailedText);
        }
    }

    bx::Vec3 targetPoint = {0.0f, 0.0f, 0.0f};
    const SpellId spellId = spellIdFromValue(request.spellId);
    const std::optional<std::string> worldAvailabilityFailure =
        spellWorldAvailabilityFailure(spellId, worldRuntime.isIndoorMap());

    if (worldAvailabilityFailure.has_value())
    {
        return makeFailureWithRecovery(
            PartySpellCastStatus::Failed,
            rule->targetKind,
            rule->effectKind,
            *worldAvailabilityFailure);
    }

    if (rule->targetKind == PartySpellCastTargetKind::Actor)
    {
        if (!request.targetActorIndex)
        {
            if (request.quickCast
                && rule->effectKind == PartySpellCastEffectKind::Projectile
                && request.hasTargetPoint)
            {
                targetPoint = {request.targetX, request.targetY, request.targetZ};
            }
            else
            {
                return makeFailure(
                    request.spellId,
                    PartySpellCastStatus::NeedActorTarget,
                    rule->targetKind,
                    rule->effectKind,
                    NoValidTargetText);
            }
        }
        else
        {
            GameplayRuntimeActorState actor = {};

            if (!worldRuntime.actorRuntimeState(*request.targetActorIndex, actor)
                || actor.isDead
                || actor.isInvisible)
            {
                return makeFailureWithRecovery(
                    PartySpellCastStatus::Failed,
                    rule->targetKind,
                    rule->effectKind,
                    SpellFailedText);
            }

            targetPoint = resolveActorTargetPoint(actor);
        }
    }
    else if (rule->targetKind == PartySpellCastTargetKind::Character)
    {
        if (!request.targetCharacterIndex || party.member(*request.targetCharacterIndex) == nullptr)
        {
            return makeFailure(
                request.spellId,
                PartySpellCastStatus::NeedCharacterTarget,
                rule->targetKind,
                rule->effectKind,
                "Need character target");
        }
    }
    else if (rule->targetKind == PartySpellCastTargetKind::ActorOrCharacter)
    {
        GameplayRuntimeActorState actor = {};
        const bool hasActorTarget =
            request.targetActorIndex && worldRuntime.actorRuntimeState(*request.targetActorIndex, actor);
        const bool hasCharacterTarget =
            request.targetCharacterIndex && party.member(*request.targetCharacterIndex) != nullptr;

        if (!hasActorTarget && !hasCharacterTarget)
        {
            return makeFailure(
                request.spellId,
                PartySpellCastStatus::NeedActorOrCharacterTarget,
                rule->targetKind,
                rule->effectKind,
                NoValidTargetText);
        }

        if (hasActorTarget)
        {
            targetPoint = resolveActorTargetPoint(actor);
        }
    }
    else if (rule->targetKind == PartySpellCastTargetKind::GroundPoint)
    {
        if (!request.hasTargetPoint)
        {
            return makeFailure(
                request.spellId,
                PartySpellCastStatus::NeedGroundPoint,
                rule->targetKind,
                rule->effectKind,
                NoValidTargetText);
        }

        targetPoint = {request.targetX, request.targetY, request.targetZ};
    }
    else if (rule->targetKind == PartySpellCastTargetKind::InventoryItem)
    {
        if ((!request.targetInventoryGridX.has_value() || !request.targetInventoryGridY.has_value())
            && !request.targetEquipmentSlot.has_value())
        {
            return makeFailure(
                request.spellId,
                PartySpellCastStatus::NeedInventoryItemTarget,
                rule->targetKind,
                rule->effectKind,
                "Select item target");
        }
    }
    else if (rule->targetKind == PartySpellCastTargetKind::UtilityUi)
    {
        if (spellId == SpellId::TownPortal)
        {
            if (skillMastery < SkillMastery::Grandmaster && hasNearbyHostileActor(worldRuntime))
            {
                return makeFailureWithRecovery(
                    PartySpellCastStatus::Failed,
                    rule->targetKind,
                    rule->effectKind,
                    SpellFailedText);
            }

            if (request.utilityAction == PartySpellUtilityActionKind::None)
            {
                if (skillMastery < SkillMastery::Grandmaster)
                {
                    static thread_local std::mt19937 rng(std::random_device{}());
                    const int successChancePercent = std::clamp(static_cast<int>(skillLevel) * 10, 0, 100);
                    std::uniform_int_distribution<int> distribution(1, 100);

                    if (distribution(rng) > successChancePercent)
                    {
                        return makeFailureWithRecovery(
                            PartySpellCastStatus::Failed,
                            rule->targetKind,
                            rule->effectKind,
                            SpellFailedText);
                    }
                }

                return makeFailure(
                    request.spellId,
                    PartySpellCastStatus::NeedUtilityUi,
                    rule->targetKind,
                    rule->effectKind,
                    "Need spell UI");
            }
        }
        else if (spellId == SpellId::LloydsBeacon && request.utilityAction == PartySpellUtilityActionKind::None)
        {
            return makeFailure(
                request.spellId,
                PartySpellCastStatus::NeedUtilityUi,
                rule->targetKind,
                rule->effectKind,
                "Need spell UI");
        }
        else if (request.utilityAction == PartySpellUtilityActionKind::None)
        {
            return makeFailure(
                request.spellId,
                PartySpellCastStatus::NeedUtilityUi,
                rule->targetKind,
                rule->effectKind,
                "Need spell UI");
        }
    }

    bool castSucceeded = false;
    const float sourceX = worldRuntime.partyX();
    const float sourceY = worldRuntime.partyY();
    const float footZ = worldRuntime.partyFootZ();
    const float sourceZ = footZ + 96.0f;
    result.hasSourcePoint = true;
    result.sourceX = sourceX;
    result.sourceY = sourceY;
    result.sourceZ = sourceZ;
    const std::string &spellName = pSpellEntry->normalizedName;

    if (rule->effectKind == PartySpellCastEffectKind::PartyBuff)
    {
        if (spellId == SpellId::Invisibility && hasNearbyHostileActor(worldRuntime))
        {
            return makeFailureWithRecovery(
                PartySpellCastStatus::Failed,
                rule->targetKind,
                rule->effectKind,
                HostileCreaturesNearbyText);
        }

        const float durationSeconds = resolvePartyBuffDurationSeconds(request.spellId, skillLevel, skillMastery);
        const int power = resolvePartyBuffPower(request.spellId, skillLevel, skillMastery);

        if (spellId == SpellId::DayOfProtection
            || spellId == SpellId::HourOfPower
            || spellId == SpellId::TravelersBoon
            || spellId == SpellId::Levitate)
        {
            applyCompositePartyBuff(
                party,
                request.spellId,
                skillLevel,
                skillMastery,
                static_cast<uint32_t>(request.casterMemberIndex));
        }
        else
        {
            party.applyPartyBuff(
                rule->partyBuffId,
                durationSeconds,
                power,
                request.spellId,
                skillLevel,
                skillMastery,
                static_cast<uint32_t>(request.casterMemberIndex));
        }

        worldRuntime.syncSpellMovementStatesFromPartyBuffs();
        castSucceeded = true;
        appendAllPartyMemberIndices(party, result.affectedCharacterIndices);
    }
    else if (rule->effectKind == PartySpellCastEffectKind::CharacterBuff)
    {
        const float durationSeconds = resolveCharacterBuffDurationSeconds(request.spellId, skillLevel, skillMastery);
        const int power = resolveCharacterBuffPower(request.spellId, skillLevel, skillMastery);
        auto applyBuffToMember =
            [&](size_t memberIndex, CharacterBuffId buffId)
            {
                party.applyCharacterBuff(
                    memberIndex,
                    buffId,
                    durationSeconds,
                    power,
                    request.spellId,
                    skillLevel,
                    skillMastery,
                    static_cast<uint32_t>(request.casterMemberIndex));
                castSucceeded = true;
                appendAffectedCharacterIndex(result.affectedCharacterIndices, memberIndex);
            };

        if (spellId == SpellId::Bless)
        {
            if (skillMastery == SkillMastery::Normal)
            {
                applyBuffToMember(*request.targetCharacterIndex, CharacterBuffId::Bless);
            }
            else
            {
                for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
                {
                    applyBuffToMember(memberIndex, CharacterBuffId::Bless);
                }
            }
        }
        else if (spellId == SpellId::Fate)
        {
            if (request.targetCharacterIndex)
            {
                applyBuffToMember(*request.targetCharacterIndex, CharacterBuffId::Fate);
            }
            else if (request.targetActorIndex)
            {
                castSucceeded = worldRuntime.applyPartySpellToActor(
                    *request.targetActorIndex,
                    request.spellId,
                    skillLevel,
                    skillMastery,
                    power,
                    sourceX,
                    sourceY,
                    footZ,
                    static_cast<uint32_t>(request.casterMemberIndex));
            }
        }
        else if (spellId == SpellId::Preservation)
        {
            if (skillMastery == SkillMastery::Master || skillMastery == SkillMastery::Grandmaster)
            {
                for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
                {
                    applyBuffToMember(memberIndex, CharacterBuffId::Preservation);
                }
            }
            else if (request.targetCharacterIndex)
            {
                applyBuffToMember(*request.targetCharacterIndex, CharacterBuffId::Preservation);
            }
        }
        else if (spellId == SpellId::Regeneration)
        {
            if (request.targetCharacterIndex)
            {
                applyBuffToMember(*request.targetCharacterIndex, CharacterBuffId::Regeneration);
            }
        }
        else if (spellId == SpellId::FireAura)
        {
            if (request.targetCharacterIndex)
            {
                applyBuffToMember(*request.targetCharacterIndex, CharacterBuffId::FireAura);
            }
        }
        else if (spellId == SpellId::Hammerhands)
        {
            if (skillMastery == SkillMastery::Grandmaster)
            {
                for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
                {
                    applyBuffToMember(memberIndex, CharacterBuffId::Hammerhands);
                }
            }
            else if (request.targetCharacterIndex)
            {
                applyBuffToMember(*request.targetCharacterIndex, CharacterBuffId::Hammerhands);
            }
        }
        else if (spellId == SpellId::VampiricWeapon)
        {
            if (request.targetCharacterIndex)
            {
                applyBuffToMember(*request.targetCharacterIndex, CharacterBuffId::VampiricWeapon);
            }
        }
        else if (spellId == SpellId::PainReflection)
        {
            if (skillMastery == SkillMastery::Master || skillMastery == SkillMastery::Grandmaster)
            {
                for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
                {
                    applyBuffToMember(memberIndex, CharacterBuffId::PainReflection);
                }
            }
            else if (request.targetCharacterIndex)
            {
                applyBuffToMember(*request.targetCharacterIndex, CharacterBuffId::PainReflection);
            }
        }
        else if (spellId == SpellId::Mistform)
        {
            if (request.targetCharacterIndex)
            {
                applyBuffToMember(*request.targetCharacterIndex, CharacterBuffId::Mistform);
            }
        }
        else if (spellId == SpellId::Glamour)
        {
            if (request.targetCharacterIndex)
            {
                applyBuffToMember(*request.targetCharacterIndex, CharacterBuffId::Glamour);
            }
        }
    }
    else if (rule->effectKind == PartySpellCastEffectKind::CharacterRestore)
    {
        if (!request.targetCharacterIndex)
        {
            return makeFailure(
                request.spellId,
                PartySpellCastStatus::NeedCharacterTarget,
                rule->targetKind,
                rule->effectKind,
                "Need character target");
        }

        castSucceeded = true;

        if (spellId == SpellId::Heal)
        {
            const int healAmount =
                skillMastery == SkillMastery::Grandmaster
                    ? 5 + static_cast<int>(5 * skillLevel)
                    : skillMastery == SkillMastery::Master
                    ? 5 + static_cast<int>(4 * skillLevel)
                    : skillMastery == SkillMastery::Expert
                    ? 5 + static_cast<int>(3 * skillLevel)
                    : 5 + static_cast<int>(2 * skillLevel);
            party.healMember(*request.targetCharacterIndex, healAmount);
        }
        else
        {
            applyCharacterRestoreSpell(
                party,
                request.spellId,
                *request.targetCharacterIndex,
                skillLevel);
        }

        if (castSucceeded)
        {
            appendAffectedCharacterIndex(result.affectedCharacterIndices, *request.targetCharacterIndex);
        }
    }
    else if (rule->effectKind == PartySpellCastEffectKind::PartyRestore)
    {
        castSucceeded = true;

        if (spellId == SpellId::Awaken)
        {
            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                party.clearMemberCondition(memberIndex, CharacterCondition::Asleep);
            }
        }
        else if (spellId == SpellId::SharedLife)
        {
            int totalHealth = 0;

            for (const Character &member : party.members())
            {
                totalHealth += std::max(0, member.health);
            }

            totalHealth += static_cast<int>(
                (skillMastery == SkillMastery::Grandmaster ? 4 : 3) * static_cast<int>(skillLevel));
            const int memberCount = std::max<int>(1, static_cast<int>(party.members().size()));
            const int share = std::max(0, totalHealth / memberCount);

            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                party.healMember(memberIndex, share);
            }
        }
        else if (spellId == SpellId::PowerCure)
        {
            const int healAmount = 10 + static_cast<int>(5 * skillLevel);

            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                party.healMember(memberIndex, healAmount);
            }
        }
        else if (spellId == SpellId::DivineIntervention)
        {
            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                Character *pMember = party.member(memberIndex);

                if (pMember == nullptr)
                {
                    continue;
                }

                pMember->conditions.reset();
                pMember->health = pMember->maxHealth;
                pMember->spellPoints = pMember->maxSpellPoints;
            }
        }

        if (castSucceeded)
        {
            appendAllPartyMemberIndices(party, result.affectedCharacterIndices);
        }
    }
    else if (rule->effectKind == PartySpellCastEffectKind::Jump)
    {
        worldRuntime.requestPartyJump();
        castSucceeded = true;
    }
    else if (rule->effectKind == PartySpellCastEffectKind::UtilityUi)
    {
        if (rule->targetKind == PartySpellCastTargetKind::InventoryItem)
        {
            size_t targetMemberIndex = request.casterMemberIndex;
            const InventoryItem *pTargetInventoryItem = nullptr;
            EquippedItemRuntimeState *pTargetEquippedRuntime = nullptr;
            const ItemDefinition *pTargetItemDefinition = resolveTargetItemDefinition(
                party,
                request,
                targetMemberIndex,
                pTargetInventoryItem,
                pTargetEquippedRuntime);

            if (pTargetItemDefinition == nullptr)
            {
                return makeFailureWithRecovery(
                    PartySpellCastStatus::Failed,
                    rule->targetKind,
                    rule->effectKind,
                    SpellFailedText);
            }

            InventoryItem *pMutableInventoryItem =
                request.targetInventoryGridX.has_value() && request.targetInventoryGridY.has_value()
                    ? party.memberInventoryItemMutable(
                        targetMemberIndex,
                        *request.targetInventoryGridX,
                        *request.targetInventoryGridY)
                    : nullptr;

            if (spellId == SpellId::FireAura || spellId == SpellId::VampiricWeapon)
            {
                if (!canApplySpellWeaponEnchant(*pTargetItemDefinition, pTargetInventoryItem, pTargetEquippedRuntime))
                {
                    return makeFailureWithRecovery(
                        PartySpellCastStatus::Failed,
                        rule->targetKind,
                        rule->effectKind,
                        SpellFailedText);
                }

                const SpecialItemEnchantKind enchantKind =
                    spellId == SpellId::FireAura
                        ? skillMastery == SkillMastery::Normal
                            ? SpecialItemEnchantKind::Fire
                            : skillMastery == SkillMastery::Expert
                            ? SpecialItemEnchantKind::Flame
                            : SpecialItemEnchantKind::Infernos
                        : SpecialItemEnchantKind::Vampiric;
                const uint16_t enchantId = findSpecialEnchantId(party.specialItemEnchantTable(), enchantKind);

                if (enchantId == 0)
                {
                    return makeFailureWithRecovery(
                        PartySpellCastStatus::Failed,
                        rule->targetKind,
                        rule->effectKind,
                        SpellFailedText);
                }

                const float durationSeconds =
                    skillMastery == SkillMastery::Grandmaster
                        ? 0.0f
                        : secondsFromHours(static_cast<float>(std::max<uint32_t>(1, skillLevel)));

                if (pMutableInventoryItem != nullptr)
                {
                    pMutableInventoryItem->specialEnchantId = enchantId;
                    pMutableInventoryItem->temporaryBonusRemainingSeconds = durationSeconds;
                }
                else if (pTargetEquippedRuntime != nullptr)
                {
                    pTargetEquippedRuntime->specialEnchantId = enchantId;
                    pTargetEquippedRuntime->temporaryBonusRemainingSeconds = durationSeconds;
                }

                party.refreshDerivedState();
                appendAffectedCharacterIndex(result.affectedCharacterIndices, targetMemberIndex);
                castSucceeded = true;
            }
            else if (spellId == SpellId::RechargeItem)
            {
                if (!InventoryItemMixingRuntime::isWandItem(*pTargetItemDefinition)
                    || (pMutableInventoryItem != nullptr && pMutableInventoryItem->broken)
                    || (pTargetEquippedRuntime != nullptr && pTargetEquippedRuntime->broken)
                    || (pMutableInventoryItem == nullptr && pTargetEquippedRuntime == nullptr))
                {
                    return makeFailureWithRecovery(
                        PartySpellCastStatus::Failed,
                        rule->targetKind,
                        rule->effectKind,
                        SpellFailedText);
                }

                const uint16_t currentCharges =
                    pMutableInventoryItem != nullptr
                        ? pMutableInventoryItem->currentCharges
                        : pTargetEquippedRuntime->currentCharges;
                const uint16_t maxCharges =
                    pMutableInventoryItem != nullptr
                        ? pMutableInventoryItem->maxCharges
                        : pTargetEquippedRuntime->maxCharges;
                const uint16_t newCharges = InventoryItemMixingRuntime::calculateSpellRechargeCharges(
                    maxCharges,
                    currentCharges,
                    skillLevel,
                    skillMastery);

                if (newCharges == 0)
                {
                    return makeFailureWithRecovery(
                        PartySpellCastStatus::Failed,
                        rule->targetKind,
                        rule->effectKind,
                        WandAlreadyChargedText);
                }

                if (pMutableInventoryItem != nullptr)
                {
                    pMutableInventoryItem->maxCharges = newCharges;
                    pMutableInventoryItem->currentCharges = newCharges;
                }
                else if (pTargetEquippedRuntime != nullptr)
                {
                    pTargetEquippedRuntime->maxCharges = newCharges;
                    pTargetEquippedRuntime->currentCharges = newCharges;
                }

                appendAffectedCharacterIndex(result.affectedCharacterIndices, targetMemberIndex);
                castSucceeded = true;
            }
            else if (spellId == SpellId::EnchantItem)
            {
                if (pMutableInventoryItem == nullptr || !canApplyEnchantItemSpell(*pTargetItemDefinition, *pMutableInventoryItem))
                {
                    return makeFailureWithRecovery(
                        PartySpellCastStatus::Failed,
                        rule->targetKind,
                        rule->effectKind,
                        SpellFailedText);
                }

                static thread_local std::mt19937 rng(std::random_device{}());
                const int successChancePercent = std::clamp(static_cast<int>(skillLevel) * 10, 0, 100);
                const int itemValue = ItemEnchantRuntime::itemValue(
                    *pMutableInventoryItem,
                    *pTargetItemDefinition,
                    party.standardItemEnchantTable(),
                    party.specialItemEnchantTable());
                const ItemEnchantCategory enchantCategory = ItemEnchantRuntime::categoryForItem(*pTargetItemDefinition);
                const bool isWeapon =
                    enchantCategory == ItemEnchantCategory::OneHandedWeapon
                    || enchantCategory == ItemEnchantCategory::TwoHandedWeapon
                    || enchantCategory == ItemEnchantCategory::Missile;
                const int qualityThreshold = isWeapon ? 250 : 450;

                if (itemValue < qualityThreshold)
                {
                    pMutableInventoryItem->broken = true;
                    return makeFailureWithRecovery(
                        PartySpellCastStatus::Failed,
                        rule->targetKind,
                        rule->effectKind,
                        ItemQualityTooLowText);
                }

                std::uniform_int_distribution<int> distribution(1, 100);
                const int roll = distribution(rng);

                if (roll > successChancePercent)
                {
                    pMutableInventoryItem->broken = true;
                    return makeFailureWithRecovery(
                        PartySpellCastStatus::Failed,
                        rule->targetKind,
                        rule->effectKind,
                        SpellFailedText);
                }

                const bool preferStandardEnchant =
                    !isWeapon && distribution(rng) <= 80 && party.standardItemEnchantTable() != nullptr;

                if (preferStandardEnchant)
                {
                    const std::optional<uint16_t> standardEnchantId =
                        ItemEnchantRuntime::chooseStandardEnchantId(
                            *pTargetItemDefinition,
                            *party.standardItemEnchantTable(),
                            rng);

                    if (!standardEnchantId.has_value())
                    {
                        return makeFailureWithRecovery(
                            PartySpellCastStatus::Failed,
                            rule->targetKind,
                            rule->effectKind,
                            SpellFailedText);
                    }

                    pMutableInventoryItem->standardEnchantId = *standardEnchantId;
                    std::uniform_int_distribution<int> powerDistribution(
                        skillMastery == SkillMastery::Grandmaster ? 6 : 3,
                        skillMastery == SkillMastery::Grandmaster ? 12 : 8);
                    pMutableInventoryItem->standardEnchantPower = static_cast<uint16_t>(powerDistribution(rng));
                }
                else
                {
                    const int enchantTreasureLevel = skillMastery == SkillMastery::Grandmaster ? 5 : 3;
                    const std::optional<uint16_t> specialEnchantId =
                        party.specialItemEnchantTable() != nullptr
                            ? ItemEnchantRuntime::chooseSpecialEnchantId(
                                *pTargetItemDefinition,
                                *party.specialItemEnchantTable(),
                                enchantTreasureLevel,
                                rng)
                            : std::nullopt;

                    if (!specialEnchantId.has_value())
                    {
                        return makeFailureWithRecovery(
                            PartySpellCastStatus::Failed,
                            rule->targetKind,
                            rule->effectKind,
                            SpellFailedText);
                    }

                    pMutableInventoryItem->specialEnchantId = *specialEnchantId;
                }

                party.refreshDerivedState();
                appendAffectedCharacterIndex(result.affectedCharacterIndices, targetMemberIndex);
                castSucceeded = true;
            }
        }
        else if (rule->targetKind == PartySpellCastTargetKind::UtilityUi)
        {
            if (spellId == SpellId::TownPortal)
            {
                if (request.utilityAction != PartySpellUtilityActionKind::TownPortalDestination
                    || !request.hasUtilityMapMove)
                {
                    return makeFailure(
                        request.spellId,
                        PartySpellCastStatus::NeedUtilityUi,
                        rule->targetKind,
                        rule->effectKind,
                        "Need spell UI");
                }

                EventRuntimeState *pEventRuntimeState = worldRuntime.eventRuntimeState();

                if (pEventRuntimeState == nullptr)
                {
                    return makeFailureWithRecovery(
                        PartySpellCastStatus::Failed,
                        rule->targetKind,
                        rule->effectKind,
                        SpellFailedText);
                }

                EventRuntimeState::PendingMapMove move = {};
                move.x = request.utilityMapMoveX;
                move.y = request.utilityMapMoveY;
                move.z = request.utilityMapMoveZ;
                move.mapName =
                    request.utilityMapMoveMapName.empty()
                        ? std::nullopt
                        : std::optional<std::string>(request.utilityMapMoveMapName);
                move.directionDegrees = request.utilityMapMoveDirectionDegrees;
                move.useMapStartPosition = request.utilityMapMoveUseMapStartPosition;
                pEventRuntimeState->pendingMapMove = move;
                castSucceeded = true;
            }
            else if (spellId == SpellId::LloydsBeacon)
            {
                Character *pTargetMember = party.member(request.casterMemberIndex);

                if (pTargetMember == nullptr || request.utilitySlotIndex >= pTargetMember->lloydsBeacons.size())
                {
                    return makeFailureWithRecovery(
                        PartySpellCastStatus::Failed,
                        rule->targetKind,
                        rule->effectKind,
                        SpellFailedText);
                }

                if (request.utilityAction == PartySpellUtilityActionKind::LloydsBeaconSet)
                {
                    LloydBeacon beacon = {};
                    beacon.mapName =
                        request.utilityMapMoveMapName.empty()
                            ? worldRuntime.mapName()
                            : request.utilityMapMoveMapName;
                    beacon.locationName =
                        request.utilityStatusText.empty()
                            ? worldRuntime.mapName()
                            : request.utilityStatusText;
                    beacon.x = sourceX;
                    beacon.y = sourceY;
                    beacon.z = footZ;
                    beacon.directionDegrees = request.utilityMapMoveDirectionDegrees.value_or(
                        static_cast<int32_t>(std::round(request.viewYawRadians * 180.0f / Pi)));
                    beacon.remainingSeconds = lloydsBeaconDurationSeconds(skillLevel);

                    if (request.utilityPreviewWidth > 0
                        && request.utilityPreviewHeight > 0
                        && request.utilityPreviewPixelsBgra.size()
                            == static_cast<size_t>(request.utilityPreviewWidth)
                                * static_cast<size_t>(request.utilityPreviewHeight)
                                * 4u)
                    {
                        beacon.previewWidth = request.utilityPreviewWidth;
                        beacon.previewHeight = request.utilityPreviewHeight;
                        beacon.previewPixelsBgra = request.utilityPreviewPixelsBgra;
                    }

                    pTargetMember->lloydsBeacons[request.utilitySlotIndex] = std::move(beacon);
                    castSucceeded = true;
                }
                else if (request.utilityAction == PartySpellUtilityActionKind::LloydsBeaconRecall)
                {
                    const std::optional<LloydBeacon> &beacon = pTargetMember->lloydsBeacons[request.utilitySlotIndex];

                    if (!beacon.has_value())
                    {
                        return makeFailureWithRecovery(
                            PartySpellCastStatus::Failed,
                            rule->targetKind,
                            rule->effectKind,
                            SpellFailedText);
                    }

                    EventRuntimeState *pEventRuntimeState = worldRuntime.eventRuntimeState();

                    if (pEventRuntimeState == nullptr)
                    {
                        return makeFailureWithRecovery(
                            PartySpellCastStatus::Failed,
                            rule->targetKind,
                            rule->effectKind,
                            SpellFailedText);
                    }

                    EventRuntimeState::PendingMapMove move = {};
                    move.x = static_cast<int32_t>(std::lround(beacon->x));
                    move.y = static_cast<int32_t>(std::lround(beacon->y));
                    move.z = static_cast<int32_t>(std::lround(beacon->z));
                    move.mapName = beacon->mapName;
                    move.directionDegrees = static_cast<int32_t>(std::lround(beacon->directionDegrees));
                    move.useMapStartPosition = false;
                    pEventRuntimeState->pendingMapMove = move;
                    castSucceeded = true;
                }
            }
        }
    }
    else if (rule->effectKind == PartySpellCastEffectKind::Projectile)
    {
        const SpellSourcePoint projectileSource = offsetPartyProjectileSourceForMember(
            request,
            SpellSourcePoint{.x = sourceX, .y = sourceY, .z = sourceZ},
            SpellSourcePoint{.x = targetPoint.x, .y = targetPoint.y, .z = targetPoint.z},
            party.members().size());
        GameplayPartySpellProjectileRequest worldRequest = {};
        worldRequest.casterMemberIndex = static_cast<uint32_t>(request.casterMemberIndex);
        worldRequest.spellId = request.spellId;
        worldRequest.skillLevel = skillLevel;
        worldRequest.skillMastery = skillMastery;
        worldRequest.damage = rollSpellDamage(*rule, *pSpellEntry, skillLevel);
        worldRequest.sourceX = projectileSource.x;
        worldRequest.sourceY = projectileSource.y;
        worldRequest.sourceZ = projectileSource.z;
        worldRequest.targetX = targetPoint.x;
        worldRequest.targetY = targetPoint.y;
        worldRequest.targetZ = targetPoint.z;
        castSucceeded = worldRuntime.castPartySpellProjectile(worldRequest);
    }
    else if (rule->effectKind == PartySpellCastEffectKind::MultiProjectile)
    {
        const float targetAngleRadians = std::atan2(targetPoint.y - sourceY, targetPoint.x - sourceX);
        const float distance = std::sqrt(
            (targetPoint.x - sourceX) * (targetPoint.x - sourceX)
            + (targetPoint.y - sourceY) * (targetPoint.y - sourceY));
        const float baseTargetZ = targetPoint.z;
        const float spreadArcRadians = Pi / 3.0f;
        const float spreadStartRadians = rule->multiProjectileCount > 1 ? -spreadArcRadians * 0.5f : 0.0f;
        const float spreadStepRadians =
            rule->multiProjectileCount > 1
                ? spreadArcRadians / static_cast<float>(rule->multiProjectileCount - 1)
                : 0.0f;
        const SpellSourcePoint projectileSource = offsetPartyProjectileSourceForMember(
            request,
            SpellSourcePoint{.x = sourceX, .y = sourceY, .z = sourceZ},
            SpellSourcePoint{.x = targetPoint.x, .y = targetPoint.y, .z = targetPoint.z},
            party.members().size());

        for (uint32_t projectileIndex = 0; projectileIndex < rule->multiProjectileCount; ++projectileIndex)
        {
            const float yawRadians =
                targetAngleRadians + spreadStartRadians + spreadStepRadians * static_cast<float>(projectileIndex);
            GameplayPartySpellProjectileRequest worldRequest = {};
            worldRequest.casterMemberIndex = static_cast<uint32_t>(request.casterMemberIndex);
            worldRequest.spellId = request.spellId;
            worldRequest.skillLevel = skillLevel;
            worldRequest.skillMastery = skillMastery;
            worldRequest.damage = rollSpellDamage(*rule, *pSpellEntry, skillLevel);
            worldRequest.sourceX = projectileSource.x;
            worldRequest.sourceY = projectileSource.y;
            worldRequest.sourceZ = projectileSource.z;
            worldRequest.targetX = sourceX + std::cos(yawRadians) * std::max(512.0f, distance);
            worldRequest.targetY = sourceY + std::sin(yawRadians) * std::max(512.0f, distance);
            worldRequest.targetZ = baseTargetZ;
            castSucceeded = worldRuntime.castPartySpellProjectile(worldRequest) || castSucceeded;
        }
    }
    else if (rule->effectKind == PartySpellCastEffectKind::ActorEffect)
    {
        if (spellId == SpellId::Sunray && (worldRuntime.currentHour() < 5 || worldRuntime.currentHour() >= 21))
        {
            return makeFailureWithRecovery(
                PartySpellCastStatus::Failed,
                rule->targetKind,
                rule->effectKind,
                SpellFailedText);
        }

        if (request.targetActorIndex)
        {
            castSucceeded = worldRuntime.applyPartySpellToActor(
                *request.targetActorIndex,
                request.spellId,
                skillLevel,
                skillMastery,
                rollSpellDamage(*rule, *pSpellEntry, skillLevel),
                sourceX,
                sourceY,
                footZ,
                static_cast<uint32_t>(request.casterMemberIndex));

            if (castSucceeded && spellId == SpellId::Lifedrain)
            {
                const int healAmount =
                    skillMastery == SkillMastery::Grandmaster
                        ? 7 + static_cast<int>(7 * skillLevel)
                        : skillMastery == SkillMastery::Master
                        ? 5 + static_cast<int>(5 * skillLevel)
                        : 3 + static_cast<int>(3 * skillLevel);
                party.healMember(request.casterMemberIndex, std::max(1, healAmount / 3));
            }

            if (castSucceeded && spellId == SpellId::Fear && skillMastery >= SkillMastery::Master)
            {
                const float radius = skillMastery == SkillMastery::Grandmaster ? 4096.0f : 512.0f;
                const std::vector<size_t> actorIndices = worldRuntime.collectMapActorIndicesWithinRadius(
                    targetPoint.x,
                    targetPoint.y,
                    targetPoint.z,
                    radius,
                    skillMastery == SkillMastery::Grandmaster,
                    sourceX,
                    sourceY,
                    sourceZ);

                for (size_t nearbyActorIndex : actorIndices)
                {
                    if (nearbyActorIndex == *request.targetActorIndex)
                    {
                        continue;
                    }

                    worldRuntime.applyPartySpellToActor(
                        nearbyActorIndex,
                        request.spellId,
                        skillLevel,
                        skillMastery,
                        0,
                        sourceX,
                        sourceY,
                        footZ,
                        static_cast<uint32_t>(request.casterMemberIndex));
                }
            }
        }
        else if (request.targetCharacterIndex)
        {
            if (spellId == SpellId::Fate)
            {
                const float durationSeconds = resolveCharacterBuffDurationSeconds(request.spellId, skillLevel, skillMastery);
                const int power = resolveCharacterBuffPower(request.spellId, skillLevel, skillMastery);
                party.applyCharacterBuff(
                    *request.targetCharacterIndex,
                    CharacterBuffId::Fate,
                    durationSeconds,
                    power,
                    request.spellId,
                    skillLevel,
                    skillMastery,
                    static_cast<uint32_t>(request.casterMemberIndex));
                castSucceeded = true;
                appendAffectedCharacterIndex(result.affectedCharacterIndices, *request.targetCharacterIndex);
            }
            else if (spellId == SpellId::Reanimate)
            {
                Character *pTargetMember = party.member(*request.targetCharacterIndex);
                castSucceeded =
                    pTargetMember != nullptr
                    && pTargetMember->conditions.test(static_cast<size_t>(CharacterCondition::Dead));

                if (castSucceeded)
                {
                    party.clearMemberCondition(*request.targetCharacterIndex, CharacterCondition::Unconscious);
                    party.clearMemberCondition(*request.targetCharacterIndex, CharacterCondition::Dead);
                    party.clearMemberCondition(*request.targetCharacterIndex, CharacterCondition::Petrified);
                    party.clearMemberCondition(*request.targetCharacterIndex, CharacterCondition::Eradicated);
                    party.applyMemberCondition(*request.targetCharacterIndex, CharacterCondition::Zombie);
                    pTargetMember->health = std::max(1, static_cast<int>(skillLevel) * 20);
                }

                if (castSucceeded)
                {
                    appendAffectedCharacterIndex(result.affectedCharacterIndices, *request.targetCharacterIndex);
                }
            }
        }
    }
    else if (rule->effectKind == PartySpellCastEffectKind::AreaEffect)
    {
        const float effectCenterX = request.hasTargetPoint ? targetPoint.x : sourceX;
        const float effectCenterY = request.hasTargetPoint ? targetPoint.y : sourceY;
        const float effectCenterZ = request.hasTargetPoint ? targetPoint.z : (footZ + 64.0f);

        if (spellId == SpellId::FireSpike)
        {
            castSucceeded = worldRuntime.spawnPartyFireSpikeTrap(
                static_cast<uint32_t>(request.casterMemberIndex),
                request.spellId,
                skillLevel,
                static_cast<uint32_t>(skillMastery),
                effectCenterX,
                effectCenterY,
                effectCenterZ);
        }
        else
        {
            if (spellId == SpellId::SummonWisp)
            {
                if (activeFriendlyWispCount(worldRuntime) >= SummonWispActiveLimit)
                {
                    return makeFailureWithRecovery(
                        PartySpellCastStatus::Failed,
                        rule->targetKind,
                        rule->effectKind,
                        SummonLimitText);
                }

                castSucceeded = worldRuntime.summonFriendlyMonsterById(
                    summonWispMonsterIdForMastery(skillMastery),
                    1,
                    summonWispDurationSeconds(skillLevel, skillMastery),
                    sourceX,
                    sourceY,
                    footZ);
            }

            const bool daylightOnly = spellId == SpellId::Sunray;

            if (daylightOnly && (worldRuntime.currentHour() < 5 || worldRuntime.currentHour() >= 21))
            {
                return makeFailureWithRecovery(
                    PartySpellCastStatus::Failed,
                    rule->targetKind,
                    rule->effectKind,
                    SpellFailedText);
            }

            if (spellId == SpellId::Armageddon)
            {
                std::string failureText;

                if (!worldRuntime.tryStartArmageddon(
                        request.casterMemberIndex,
                        skillLevel,
                        skillMastery,
                        failureText))
                {
                    return makeFailureWithRecovery(
                        PartySpellCastStatus::Failed,
                        rule->targetKind,
                        rule->effectKind,
                        failureText.empty() ? SpellFailedText : failureText);
                }

                castSucceeded = true;
            }

            const float effectRadius =
                spellId == SpellId::WingBuffet
                    ? 768.0f
                    : spellId == SpellId::SummonWisp
                    ? 0.0f
                    : spellId == SpellId::SpiritLash
                    ? 768.0f
                    : spellId == SpellId::SoulDrinker
                    ? SoulDrinkerOutdoorRange
                    : spellId == SpellId::Armageddon
                    ? 8192.0f
                    : 4096.0f;
            const std::vector<size_t> actorIndices =
                effectRadius > 0.0f && spellId != SpellId::Armageddon
                    ? worldRuntime.collectMapActorIndicesWithinRadius(
                        effectCenterX,
                        effectCenterY,
                        effectCenterZ,
                        effectRadius,
                        spellId != SpellId::Armageddon,
                        sourceX,
                        sourceY,
                        sourceZ)
                    : std::vector<size_t>{};

            int totalSoulDrinkerDrain = 0;

            for (size_t actorIndex : actorIndices)
            {
                GameplayRuntimeActorState actor = {};

                if (!worldRuntime.actorRuntimeState(actorIndex, actor))
                {
                    continue;
                }

                if (!areaSpellAffectsVisibleCreatures(spellId) && !actor.hostileToParty)
                {
                    continue;
                }

                if (areaSpellAffectsVisibleCreatures(spellId))
                {
                    const float actorTargetZ =
                        actor.preciseZ + std::max(48.0f, static_cast<float>(actor.height) * 0.6f);

                    if (!isActorPointInsideSpellView(request, actor.preciseX, actor.preciseY, actorTargetZ))
                    {
                        continue;
                    }
                }

                const int spellDamage = rollSpellDamage(*rule, *pSpellEntry, skillLevel);
                const bool applied = worldRuntime.applyPartySpellToActor(
                    actorIndex,
                    request.spellId,
                    skillLevel,
                    skillMastery,
                    spellDamage,
                    sourceX,
                    sourceY,
                    footZ,
                    static_cast<uint32_t>(request.casterMemberIndex));
                castSucceeded = applied || castSucceeded;

                if (spellId == SpellId::SoulDrinker && applied)
                {
                    totalSoulDrinkerDrain += std::max(1, spellDamage);
                }
            }

            if (spellId == SpellId::SoulDrinker && castSucceeded)
            {
                std::vector<size_t> recipientIndices;
                recipientIndices.reserve(party.members().size());

                for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
                {
                    const Character *pMember = party.member(memberIndex);

                    if (pMember != nullptr && GameMechanics::canAct(*pMember))
                    {
                        recipientIndices.push_back(memberIndex);
                    }
                }

                if (recipientIndices.empty())
                {
                    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
                    {
                        recipientIndices.push_back(memberIndex);
                    }
                }

                if (!recipientIndices.empty())
                {
                    const int share = totalSoulDrinkerDrain / static_cast<int>(recipientIndices.size());
                    int remainder = totalSoulDrinkerDrain % static_cast<int>(recipientIndices.size());

                    for (size_t recipientIndex : recipientIndices)
                    {
                        int healAmount = share;

                        if (remainder > 0)
                        {
                            ++healAmount;
                            --remainder;
                        }

                        if (healAmount > 0 && party.healMember(recipientIndex, healAmount))
                        {
                            appendAffectedCharacterIndex(result.affectedCharacterIndices, recipientIndex);
                        }
                    }
                }

                result.screenOverlayRequest = PartySpellCastResult::ScreenOverlayRequest{
                    .colorAbgr = makeAbgr(56, 0, 12),
                    .durationSeconds = 0.52f,
                    .peakAlpha = 0.65f
                };
            }
            else if (spellId == SpellId::PrismaticLight && castSucceeded)
            {
                result.screenOverlayRequest = PartySpellCastResult::ScreenOverlayRequest{
                    .colorAbgr = makeAbgr(255, 255, 224),
                    .durationSeconds = 0.52f,
                    .peakAlpha = 0.55f
                };
            }
            else if (spellId == SpellId::Armageddon)
            {
                castSucceeded = true;
            }
            else if (spellId == SpellId::DispelMagic)
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
                    party.clearPartyBuff(buffId);
                }

                for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
                {
                    for (CharacterBuffId buffId : {
                             CharacterBuffId::Bless,
                             CharacterBuffId::Fate,
                             CharacterBuffId::Preservation,
                             CharacterBuffId::Regeneration,
                             CharacterBuffId::Hammerhands,
                             CharacterBuffId::PainReflection})
                    {
                        party.clearCharacterBuff(memberIndex, buffId);
                    }
                }

                castSucceeded = true;
            }

        }
    }

    if (!castSucceeded)
    {
        return makeFailureWithRecovery(
            PartySpellCastStatus::Failed,
            rule->targetKind,
            rule->effectKind,
            SpellFailedText);
    }

    if (request.spendMana)
    {
        party.spendSpellPoints(request.casterMemberIndex, static_cast<int>(result.manaCost));
    }

    if (request.applyRecovery && result.recoverySeconds > 0.0f)
    {
        party.applyRecoveryToMember(request.casterMemberIndex, result.recoverySeconds);
    }

    result.status = PartySpellCastStatus::Succeeded;
    return result;
}

std::optional<PartySpellDescriptor> PartySpellSystem::describeSpell(uint32_t spellId)
{
    const std::optional<BackendSpellRule> rule = resolveBackendSpellRule(spellId, SkillMastery::Grandmaster);

    if (!rule)
    {
        return std::nullopt;
    }

    PartySpellDescriptor descriptor = {};
    descriptor.spellId = spellId;
    descriptor.targetKind = rule->targetKind;
    descriptor.effectKind = rule->effectKind;
    return descriptor;
}
}
