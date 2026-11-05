#include "game/party/PartySpellSystem.h"

#include "game/gameplay/CorpseLootRuntime.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/PartyHostileAlert.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/InventoryItemMixingRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/party/LloydsBeaconRuntime.h"
#include "game/party/SpellSchool.h"
#include "game/party/SpellIds.h"
#include "game/rules/GameRules.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/SpellTable.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
constexpr float Pi = 3.14159265358979323846f;
constexpr float SoulDrinkerOutdoorRange = 10240.0f;
constexpr float CameraVerticalFovRadians = Pi / 3.0f;
constexpr float PartyMemberProjectileLateralSpacing = 28.0f;
constexpr float ProjectileRightVectorEpsilon = 0.0001f;
constexpr float SpellFailureRecoveryScale = 0.5f;
constexpr float JumpSpellVerticalVelocity = 1000.0f;
constexpr float JumpSpellLift = 5.0f;
constexpr int16_t SummonWispNormalMonsterId = 97;
constexpr int16_t SummonWispMasterMonsterId = 98;
constexpr int16_t SummonWispGrandmasterMonsterId = 99;
// A wisp the rules add past the limit stays until it dies.
constexpr float PermanentWispSeconds = 1.0e9f;

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

// The living monsters a party member summoned: MM8 counts every monster whose summoner is the caster, wisp or not
// (MM8-Rel 0x42c1a0-0x42c1b2).
size_t summonedMonsterCount(const IGameplayWorldRuntime &worldRuntime, size_t casterMemberIndex)
{
    size_t count = 0;

    for (size_t actorIndex = 0; actorIndex < worldRuntime.mapActorCount(); ++actorIndex)
    {
        GameplayRuntimeActorState actor = {};

        if (worldRuntime.actorRuntimeState(actorIndex, actor)
            && actor.summonerMemberIndex == int32_t(casterMemberIndex)
            && !actor.isDead
            && !actor.isInvisible)
        {
            ++count;
        }
    }

    return count;
}

// How many monsters a caster's Summon Wisp keeps at once: 1 up to Expert, 3 at Master, 5 at Grandmaster (MM8-Rel
// 0x42c12b).
size_t summonWispLimit(SkillMastery skillMastery)
{
    return skillMastery == SkillMastery::Grandmaster ? 5 : skillMastery == SkillMastery::Master ? 3 : 1;
}

int16_t summonWispMonsterIdForMastery(SkillMastery skillMastery)
{
    return skillMastery == SkillMastery::Grandmaster
        ? SummonWispGrandmasterMonsterId
        : skillMastery == SkillMastery::Master
        ? SummonWispMasterMonsterId
        : SummonWispNormalMonsterId;
}

// 15 game minutes a point from Master, 5 below (MM8-Rel 0x42c12b).
float summonWispDurationSeconds(uint32_t skillLevel, SkillMastery skillMastery)
{
    const uint32_t minutesPerPoint = skillMastery >= SkillMastery::Master ? 15 : 5;
    return secondsFromMinutes(static_cast<float>(minutesPerPoint * skillLevel));
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
    return spellId == SpellId::Fear
        || spellId == SpellId::Inferno
        || spellId == SpellId::PrismaticLight
        || spellId == SpellId::SoulDrinker;
}

// OpenEnroth casts these on every creature in sight and spends the mana even when none is there.
bool areaSpellSucceedsWithoutTargets(SpellId spellId)
{
    return spellId == SpellId::TurnUndead
        || spellId == SpellId::MassFear
        || spellId == SpellId::Inferno
        || spellId == SpellId::PrismaticLight
        || spellId == SpellId::SoulDrinker;
}

// How a party cast of a spell behaves. Its numbers (cost, recovery, damage, projectiles and the mastery it needs) come
// from spells.txt (spellNumbersAtMastery), so a ruleset changes them through its table.
struct BackendSpellRule
{
    PartySpellCastTargetKind targetKind = PartySpellCastTargetKind::None;
    PartySpellCastEffectKind effectKind = PartySpellCastEffectKind::Unsupported;
    PartyBuffId partyBuffId = PartyBuffId::TorchLight;
};

BackendSpellRule makeBackendSpellRule(
    PartySpellCastTargetKind targetKind,
    PartySpellCastEffectKind effectKind,
    PartyBuffId partyBuffId = PartyBuffId::TorchLight)
{
    BackendSpellRule rule = {};
    rule.targetKind = targetKind;
    rule.effectKind = effectKind;
    rule.partyBuffId = partyBuffId;
    return rule;
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

// Casts the spell again on the rules' further targets near the struck monster: living hostile monsters in reach not
// yet shrunk, nearest first, then those whose shrinking ends soonest (SP:1674-1703).
void applySpellSplash(
    IGameplayWorldRuntime &worldRuntime,
    const SpellRules &spellRules,
    const PartySpellCastRequest &request,
    const SpellSplash &splash,
    const bx::Vec3 &center,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    float sourceX,
    float sourceY,
    float sourceZ,
    float footZ)
{
    struct Candidate
    {
        size_t actorIndex = 0;
        bool fresh = false;
        float order = 0.0f;
    };

    std::vector<Candidate> candidates;

    for (const size_t actorIndex : worldRuntime.collectMapActorIndicesWithinRadius(
             center.x, center.y, center.z, splash.radius, false, sourceX, sourceY, sourceZ))
    {
        GameplayRuntimeActorState actor = {};
        GameplayActorInspectState inspect = {};

        if (actorIndex == *request.targetActorIndex
            || !worldRuntime.actorRuntimeState(actorIndex, actor)
            || actor.isDead
            || actor.isInvisible
            || !actor.hostileToParty
            || spellRules.ignoresCrowdControl(actor.rulesetFacts))
        {
            continue;
        }

        const float distance = std::hypot(actor.preciseX - center.x, actor.preciseY - center.y,
            actor.preciseZ - center.z);
        const bool fresh =
            !worldRuntime.actorInspectState(actorIndex, 0, inspect) || inspect.shrinkRemainingSeconds <= 0.0f;
        candidates.push_back({actorIndex, fresh, fresh ? distance : inspect.shrinkRemainingSeconds});
    }

    std::sort(candidates.begin(), candidates.end(),
        [](const Candidate &left, const Candidate &right)
        {
            return left.fresh != right.fresh ? left.fresh : left.order < right.order;
        });
    candidates.resize(std::min(candidates.size(), splash.extraTargets));

    for (const Candidate &candidate : candidates)
    {
        worldRuntime.applyPartySpellToActor(
            candidate.actorIndex,
            request.spellId,
            skillLevel,
            skillMastery,
            0,
            sourceX,
            sourceY,
            footZ,
            uint32_t(request.casterMemberIndex),
            false);
    }
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

    switch (spellIdFromValue(spellId))
    {
        case SpellId::TorchLight:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff);
        case SpellId::FireBolt:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::FireResistance:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::FireResistance);
        case SpellId::FireAura:
            return makeBackendSpellRule(PartySpellCastTargetKind::InventoryItem, PartySpellCastEffectKind::UtilityUi);
        case SpellId::Haste:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::Haste);
        case SpellId::Fireball:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::FireSpike:
            return makeBackendSpellRule(PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::AreaEffect);
        case SpellId::Immolation:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::Immolation);
        case SpellId::MeteorShower:
            return makeBackendSpellRule(PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::Projectile);
        case SpellId::Inferno:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect);
        case SpellId::Incinerate:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::WizardEye:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::WizardEye);
        case SpellId::FeatherFall:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::FeatherFall);
        case SpellId::AirResistance:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::AirResistance);
        case SpellId::Sparks:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::GroundPoint,
                PartySpellCastEffectKind::MultiProjectile);
        case SpellId::Jump:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::Jump);
        case SpellId::Shield:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::Shield);
        case SpellId::LightningBolt:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::Invisibility:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::Invisibility);
        case SpellId::Implosion:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::Fly:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::Fly);
        case SpellId::Starburst:
            return makeBackendSpellRule(PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::Projectile);
        case SpellId::Awaken:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyRestore);
        case SpellId::PoisonSpray:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::GroundPoint,
                PartySpellCastEffectKind::MultiProjectile);
        case SpellId::WaterResistance:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::WaterResistance);
        case SpellId::IceBolt:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::WaterWalk:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::WaterWalk);
        case SpellId::RechargeItem:
            return makeBackendSpellRule(PartySpellCastTargetKind::InventoryItem, PartySpellCastEffectKind::UtilityUi);
        case SpellId::AcidBurst:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::EnchantItem:
            return makeBackendSpellRule(PartySpellCastTargetKind::InventoryItem, PartySpellCastEffectKind::UtilityUi);
        case SpellId::TownPortal:
            return makeBackendSpellRule(PartySpellCastTargetKind::UtilityUi, PartySpellCastEffectKind::UtilityUi);
        case SpellId::LloydsBeacon:
            return makeBackendSpellRule(PartySpellCastTargetKind::UtilityUi, PartySpellCastEffectKind::UtilityUi);
        case SpellId::IceBlast:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::GroundPoint,
                PartySpellCastEffectKind::MultiProjectile);
        case SpellId::Stun:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::Slow:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::EarthResistance:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::EarthResistance);
        case SpellId::DeadlySwarm:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::StoneSkin:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::Stoneskin);
        case SpellId::Blades:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::StoneToFlesh:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::CharacterOrWorldTarget,
                PartySpellCastEffectKind::CharacterRestore);
        case SpellId::RockBlast:
            return makeBackendSpellRule(PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::Projectile);
        case SpellId::Telekinesis:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::TelekinesisTarget,
                PartySpellCastEffectKind::Telekinesis);
        case SpellId::DeathBlossom:
            return makeBackendSpellRule(PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::Projectile);
        case SpellId::MassDistortion:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::DetectLife:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::DetectLife);
        case SpellId::Bless:
            return makeBackendSpellRule(
                mastery == SkillMastery::Normal
                    ? PartySpellCastTargetKind::Character
                    : PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::CharacterBuff);
        case SpellId::Fate:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::ActorOrCharacter,
                PartySpellCastEffectKind::ActorEffect);
        case SpellId::TurnUndead:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect);
        case SpellId::RemoveCurse:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::Character,
                PartySpellCastEffectKind::CharacterRestore);
        case SpellId::Preservation:
            return makeBackendSpellRule(
                mastery == SkillMastery::Master || mastery == SkillMastery::Grandmaster
                    ? PartySpellCastTargetKind::None
                    : PartySpellCastTargetKind::Character,
                PartySpellCastEffectKind::CharacterBuff);
        case SpellId::Heroism:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::Heroism);
        case SpellId::SpiritLash:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect);
        case SpellId::RaiseDead:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::Character,
                PartySpellCastEffectKind::CharacterRestore);
        case SpellId::SharedLife:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyRestore);
        case SpellId::Resurrection:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::Character,
                PartySpellCastEffectKind::CharacterRestore);
        case SpellId::Telepathy:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::RemoveFear:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::Character,
                PartySpellCastEffectKind::CharacterRestore);
        case SpellId::MindResistance:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::MindResistance);
        case SpellId::MindBlast:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::Charm:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::CureParalysis:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::Character,
                PartySpellCastEffectKind::CharacterRestore);
        case SpellId::Berserk:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::MassFear:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect);
        case SpellId::CureInsanity:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::Character,
                PartySpellCastEffectKind::CharacterRestore);
        case SpellId::PsychicShock:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::Enslave:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::CureWeakness:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::Character,
                PartySpellCastEffectKind::CharacterRestore);
        case SpellId::Heal:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::Character,
                PartySpellCastEffectKind::CharacterRestore);
        case SpellId::BodyResistance:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::BodyResistance);
        case SpellId::Harm:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::Regeneration:
            return makeBackendSpellRule(PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterBuff);
        case SpellId::CurePoison:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::Character,
                PartySpellCastEffectKind::CharacterRestore);
        case SpellId::Hammerhands:
            return makeBackendSpellRule(
                mastery == SkillMastery::Grandmaster
                    ? PartySpellCastTargetKind::None
                    : PartySpellCastTargetKind::Character,
                PartySpellCastEffectKind::CharacterBuff);
        case SpellId::CureDisease:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::Character,
                PartySpellCastEffectKind::CharacterRestore);
        case SpellId::ProtectionFromMagic:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::ProtectionFromMagic);
        case SpellId::FlyingFist:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::PowerCure:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyRestore);
        case SpellId::LightBolt:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::DestroyUndead:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::DispelMagic:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect);
        case SpellId::Paralyze:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::SummonWisp:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect);
        case SpellId::DayOfGods:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::DayOfGods);
        case SpellId::PrismaticLight:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect);
        case SpellId::DayOfProtection:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::BodyResistance);
        case SpellId::HourOfPower:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::Heroism);
        case SpellId::Sunray:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::DivineIntervention:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyRestore);
        case SpellId::Reanimate:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::ActorOrCharacter,
                PartySpellCastEffectKind::ActorEffect);
        case SpellId::ToxicCloud:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::VampiricWeapon:
            return makeBackendSpellRule(PartySpellCastTargetKind::InventoryItem, PartySpellCastEffectKind::UtilityUi);
        case SpellId::ShrinkingRay:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::Shrapmetal:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::GroundPoint,
                PartySpellCastEffectKind::MultiProjectile);
        case SpellId::ControlUndead:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::PainReflection:
            return makeBackendSpellRule(
                mastery == SkillMastery::Master || mastery == SkillMastery::Grandmaster
                    ? PartySpellCastTargetKind::None
                    : PartySpellCastTargetKind::Character,
                PartySpellCastEffectKind::CharacterBuff);
        case SpellId::DarkGrasp:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::DragonBreath:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::Armageddon:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect);
        case SpellId::SoulDrinker:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect);
        case SpellId::Glamour:
            // Party-wide (OpenYAMM, user 2026-11-04; MM8 and MAW target one member): the party's best merchant trades
            // for everyone, so a single target only mattered when it was the wrong one.
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::CharacterBuff);
        case SpellId::TravelersBoon:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff);
        case SpellId::Blind:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::DarkfireBolt:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::Lifedrain:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::Levitate:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::Levitate);
        case SpellId::VampireCharm:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect);
        case SpellId::Mistform:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::CharacterBuff);
        case SpellId::Fear:
            return makeBackendSpellRule(
                mastery == SkillMastery::Grandmaster
                    ? PartySpellCastTargetKind::None
                    : PartySpellCastTargetKind::Actor,
                mastery == SkillMastery::Grandmaster
                    ? PartySpellCastEffectKind::AreaEffect
                    : PartySpellCastEffectKind::ActorEffect);
        case SpellId::FlameBlast:
            return makeBackendSpellRule(PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile);
        case SpellId::Flight:
            return makeBackendSpellRule(
                PartySpellCastTargetKind::None,
                PartySpellCastEffectKind::PartyBuff,
                PartyBuffId::Fly);
        case SpellId::WingBuffet:
            return makeBackendSpellRule(PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect);
        default:
            return std::nullopt;
    }
}

// Standard's Heal: 5 HP plus 2, 3, 4 or 5 per point of Body Magic by mastery.
int standardHealAmount(SkillMastery mastery, uint32_t skillLevel)
{
    const int perPoint = mastery == SkillMastery::Grandmaster ? 5
        : mastery == SkillMastery::Master                     ? 4
        : mastery == SkillMastery::Expert                     ? 3
                                                              : 2;
    return 5 + perPoint * static_cast<int>(skillLevel);
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

    const int bonusLevel = caster.skillBonus(*skillName);
    skillLevel = std::max(0, static_cast<int>(pSkill->level) + bonusLevel);
    skillMastery = pSkill->mastery;
    return skillLevel > 0;
}

bx::Vec3 resolveActorTargetPoint(const GameplayRuntimeActorState &actor)
{
    return {
        actor.preciseX,
        actor.preciseY,
        actor.preciseZ + GameMechanics::actorTargetHeight(actor.height)
    };
}

float resolvePartyBuffDurationSeconds(uint32_t spellId, uint32_t skillLevel, SkillMastery mastery)
{
    switch (spellIdFromValue(spellId))
    {
        case SpellId::TorchLight:
        case SpellId::WizardEye:
        case SpellId::Fly:
        case SpellId::WaterWalk:
        case SpellId::DetectLife:
        case SpellId::ProtectionFromMagic:
        case SpellId::Glamour:
            return secondsFromHours(static_cast<float>(skillLevel));
        case SpellId::Invisibility:
            return mastery >= SkillMastery::Grandmaster
                ? secondsFromHours(static_cast<float>(skillLevel))
                : secondsFromMinutes(static_cast<float>(10 * skillLevel));
        case SpellId::FireResistance:
        case SpellId::AirResistance:
        case SpellId::WaterResistance:
        case SpellId::EarthResistance:
        case SpellId::MindResistance:
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
            return mastery == SkillMastery::Grandmaster
                ? secondsFromHours(static_cast<float>(2 * std::max<uint32_t>(1, skillLevel)))
                : mastery == SkillMastery::Master
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
                ? 10
                : mastery == SkillMastery::Master
                ? 3
                : 1;
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
            // MM8 casts (skill + 5) / 2 at every mastery (MM8-Rel.exe 0x42d544).
            return (static_cast<int>(skillLevel) + 5) / 2;
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

bool isStoneToFleshWorldTarget(const GameplayWorldHit &hit)
{
    return hit.hasHit
        && hit.kind == GameplayWorldHitKind::EventTarget
        && hit.eventTarget.has_value()
        && hit.eventTarget->contextActionMetadata.has_value()
        && hit.eventTarget->contextActionMetadata->kind == "stone_to_flesh";
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

    if (spellIdFromValue(request.spellId) == SpellId::DivineIntervention
        && pCaster->equippedItemEffectFlags.contains("DisableDivineIntervention"))
    {
        return makeFailure(
            request.spellId,
            PartySpellCastStatus::Unsupported,
            PartySpellCastTargetKind::None,
            PartySpellCastEffectKind::PartyRestore,
            "Divine Intervention is blocked by equipped gear");
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

    // A null field (the world's Hum at 0 here): no spell is cast without a Null Damper II.
    if (party.castingBlockedFor(*pCaster))
    {
        return makeFailure(
            request.spellId,
            PartySpellCastStatus::Unsupported,
            PartySpellCastTargetKind::None,
            PartySpellCastEffectKind::Unsupported,
            "Your magic scatters in the null field");
    }

    // The monster the request names, for rules that read it (MAW's class spells): its level and the crowd around it.
    int targetLevel = 0;
    int monstersNearTarget = 0;
    GameplayRuntimeActorState targetActor = {};

    if (request.targetActorIndex && worldRuntime.actorRuntimeState(*request.targetActorIndex, targetActor))
    {
        targetLevel = targetActor.rulesetFacts.level;

        for (const size_t nearIndex : worldRuntime.collectMapActorIndicesWithinRadius(targetActor.preciseX,
                 targetActor.preciseY, targetActor.preciseZ, 384.0f, false, targetActor.preciseX, targetActor.preciseY,
                 targetActor.preciseZ))
        {
            GameplayRuntimeActorState nearActor = {};
            monstersNearTarget += worldRuntime.actorRuntimeState(nearIndex, nearActor) && !nearActor.isDead ? 1 : 0;
        }
    }

    const auto castAtLevel = [&party, pCaster, targetLevel, monstersNearTarget](
                                 const SpellEntry &spellEntry, SkillMastery mastery, uint32_t level)
    {
        CharacterSpellCast cast = {};
        cast.targetLevel = targetLevel;
        cast.monstersNearTarget = monstersNearTarget;
        cast.pCaster = pCaster;
        cast.pItemTable = party.itemTable();
        cast.pStandardItemEnchantTable = party.standardItemEnchantTable();
        cast.pSpecialItemEnchantTable = party.specialItemEnchantTable();
        cast.pSpell = &spellEntry;
        cast.mastery = mastery;
        cast.skillLevel = level;
        cast.partyCount = int(std::max<size_t>(1, party.members().size()));
        return cast;
    };
    // `critical` learns whether the roll was a critical hit.
    const auto rollSpellDamage =
        [&party, &castAtLevel](const SpellEntry &spellEntry, SkillMastery mastery, uint32_t level, bool &critical)
    {
        const CharacterSpellCast cast = castAtLevel(spellEntry, mastery, level);
        int damage = party.rules().combat.rollSpellDamage(cast, &critical);
        // Hesper's item effects: per-cent spell damage (item_effects spell_damage_pct).
        const int percent = cast.pCaster != nullptr ? cast.pCaster->spellDamagePercent : 0;
        damage = percent != 0 ? std::max(0, damage + damage * percent / 100) : damage;
        // The world's Hum (Party::spellDamagePercentFor): 100 without one.
        const int humPercent = cast.pCaster != nullptr ? party.spellDamagePercentFor(*cast.pCaster) : 100;
        return humPercent < 100 ? damage * humPercent / 100 : damage;
    };

    if (party.hasPartyBuff(PartyBuffId::Invisibility))
    {
        party.clearPartyBuff(PartyBuffId::Invisibility);
    }

    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;
    // A class spell the rules mark known at their own mastery step needs that step, not the table's; one needing none
    // casts without the school skill, at skill 0 and Novice, as the original engine casts any known spell.
    const std::optional<SkillMastery> classMastery = request.skillLevelOverride == 0
        ? party.rules().spells.classSpellMastery(*pCaster, request.spellId)
        : std::nullopt;
    const bool unskilledClassSpell = classMastery == SkillMastery::None && pCaster->knowsSpell(request.spellId);

    const bool skilled = resolveSpellSkill(*pCaster, request.spellId, request, skillLevel, skillMastery);

    if (!skilled && unskilledClassSpell)
    {
        skillLevel = 0;
        skillMastery = SkillMastery::Normal;
    }
    else if (!skilled)
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

    if (!request.bypassRequiredMastery && skillMastery < classMastery.value_or(pSpellEntry->requiredMastery))
    {
        return makeFailure(
            request.spellId,
            PartySpellCastStatus::NotSkilledEnough,
            rule->targetKind,
            rule->effectKind,
            "Not skilled enough");
    }

    CharacterSpellCast spellCast = {};
    spellCast.pCaster = pCaster;
    spellCast.pItemTable = party.itemTable();
    spellCast.pStandardItemEnchantTable = party.standardItemEnchantTable();
    spellCast.pSpecialItemEnchantTable = party.specialItemEnchantTable();
    spellCast.pSpell = pSpellEntry;
    spellCast.mastery = skillMastery;
    spellCast.skillLevel = skillLevel;
    spellCast.partyCount = int(std::max<size_t>(1, party.members().size()));
    spellCast.fromScroll = request.fromScroll;
    const SpellRules &spellRules = party.rules().spells;
    const SpellMasteryNumbers spellNumbers = spellNumbersAtMastery(*pSpellEntry, skillMastery);
    result.manaCost = static_cast<uint32_t>(spellRules.manaCost(spellCast, spellNumbers.manaCost));
    const int baseSpellRecoveryTicks = spellRules.recoveryTicks(spellCast, spellNumbers.recoveryTicks);
    // A ruleset's heal for this spell (MAW's heal table), else Standard's.
    const std::optional<int> rulesetHeal = spellRules.healAmount(spellCast);
    int spellRecoveryTicks = baseSpellRecoveryTicks;
    // What the cast healed and how much of it went past full HP, for rules that reward overhealing (MAW).
    int healedTotal = 0;
    int overhealed = 0;
    const auto healTracked = [&party, &healedTotal, &overhealed](size_t memberIndex, int amount)
    {
        const Character *pMember = party.member(memberIndex);

        if (pMember != nullptr && amount > 0)
        {
            healedTotal += amount;
            overhealed += std::max(0, amount - std::max(0, Party::effectiveMaximumHealth(*pMember) - pMember->health));
        }

        return party.healMember(memberIndex, amount);
    };

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

    // A scroll's buff the rules hold as an aura of the place (MAW).
    if (request.fromScroll && spellRules.castSourceBuff(party, request.spellId, BuffSource::Scroll))
    {
        result.manaCost = 0;
        result.status = PartySpellCastStatus::Succeeded;
        appendAllPartyMemberIndices(party, result.affectedCharacterIndices);

        if (request.applyRecovery && result.recoverySeconds > 0.0f)
        {
            party.applyRecoveryToMember(request.casterMemberIndex, result.recoverySeconds);
        }

        return result;
    }

    // A member's own buff cast under rules that make buffs auras (MAW) toggles the aura and spends no mana.
    if (request.spendMana && request.skillLevelOverride == 0 && !request.bypassRequiredMastery)
    {
        if (const std::optional<AuraCastResult> aura =
                spellRules.castAura(party, request.casterMemberIndex, request.spellId))
        {
            if (*aura == AuraCastResult::NotEnoughMana)
            {
                return makeFailure(
                    request.spellId,
                    PartySpellCastStatus::NotEnoughSpellPoints,
                    rule->targetKind,
                    rule->effectKind,
                    "Not enough mana to hold " + spellRules.spellName(*pCaster, *pSpellEntry));
            }

            spellRules.updateAuras(party, 0.0f);
            result.manaCost = 0;
            result.status = PartySpellCastStatus::Succeeded;
            result.statusText = *aura == AuraCastResult::Held
                ? spellRules.spellName(*pCaster, *pSpellEntry) + " held by " + pCaster->name
                : spellRules.spellName(*pCaster, *pSpellEntry) + " released";

            // Letting an aura go takes no time (SP:2851-2858 sets no recovery).
            if (*aura == AuraCastResult::Released)
            {
                result.recoverySeconds = 0.0f;
            }

            if (request.applyRecovery && result.recoverySeconds > 0.0f)
            {
                party.applyRecoveryToMember(request.casterMemberIndex, result.recoverySeconds);
            }

            return result;
        }
    }

    if (request.spendMana)
    {
        if (const std::optional<std::string> refusal =
                spellRules.castRefusal(party, request.casterMemberIndex, request.spellId))
        {
            return makeFailure(
                request.spellId,
                PartySpellCastStatus::NotEnoughSpellPoints,
                rule->targetKind,
                rule->effectKind,
                *refusal);
        }
    }

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
    // Sunray indoors where the rules allow it (MAW), at any hour; outdoors it keeps its daylight check.
    const bool sunrayIndoors =
        spellId == SpellId::Sunray && worldRuntime.isIndoorMap() && party.rules().spells.sunrayWorksIndoors();
    const std::optional<std::string> worldAvailabilityFailure = sunrayIndoors
        ? std::nullopt
        : spellWorldAvailabilityFailure(spellId, worldRuntime.isIndoorMap());

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
    else if (rule->targetKind == PartySpellCastTargetKind::CharacterOrWorldTarget)
    {
        const bool hasCharacterTarget =
            request.targetCharacterIndex && party.member(*request.targetCharacterIndex) != nullptr;
        const bool hasWorldTarget =
            request.targetWorldHit.has_value() && isStoneToFleshWorldTarget(*request.targetWorldHit);

        if (!hasCharacterTarget && !hasWorldTarget)
        {
            return makeFailure(
                request.spellId,
                PartySpellCastStatus::NeedCharacterOrWorldTarget,
                rule->targetKind,
                rule->effectKind,
                NoValidTargetText);
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

        targetPoint = resolveFallingSpellTargetPoint(
            worldRuntime, request.spellId, {request.targetX, request.targetY, request.targetZ});
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
    else if (rule->targetKind == PartySpellCastTargetKind::TelekinesisTarget)
    {
        if (!request.telekinesisTarget.has_value())
        {
            return makeFailure(
                request.spellId,
                PartySpellCastStatus::NeedTelekinesisTarget,
                rule->targetKind,
                rule->effectKind,
                NoValidTargetText);
        }

        if (!worldRuntime.canActivateTelekinesisTarget(*request.telekinesisTarget))
        {
            return makeFailureWithRecovery(
                PartySpellCastStatus::Failed,
                rule->targetKind,
                rule->effectKind,
                SpellFailedText);
        }
    }
    else if (rule->targetKind == PartySpellCastTargetKind::UtilityUi)
    {
        if ((spellId == SpellId::TownPortal || spellId == SpellId::LloydsBeacon)
            && party.rules().monsters.teleportBlockedNearEnemies()
            && partyHasYellowAlert(worldRuntime))
        {
            return makeFailure(
                request.spellId,
                PartySpellCastStatus::Failed,
                rule->targetKind,
                rule->effectKind,
                party.rules().monsters.teleportBlockedText(spellId == SpellId::TownPortal));
        }

        if (spellId == SpellId::TownPortal)
        {
            if (skillMastery < SkillMastery::Grandmaster
                && partyHasYellowAlert(worldRuntime))
            {
                return makeFailureWithRecovery(
                    PartySpellCastStatus::Failed,
                    rule->targetKind,
                    rule->effectKind,
                    SpellFailedText);
            }

            if (request.utilityAction == PartySpellUtilityActionKind::None)
            {
                // No success roll (the original games' skill x 10 %, user 2026-11-04): only hostiles nearby stop it.
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
        if (spellId == SpellId::Invisibility && partyHasYellowAlert(worldRuntime))
        {
            return makeFailureWithRecovery(
                PartySpellCastStatus::Failed,
                rule->targetKind,
                rule->effectKind,
                HostileCreaturesNearbyText);
        }

        const float durationSeconds =
            spellRules.partyBuffSeconds(party, request.spellId, skillLevel, skillMastery, request.fromScroll)
                .value_or(resolvePartyBuffDurationSeconds(request.spellId, skillLevel, skillMastery));
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
                    static_cast<uint32_t>(request.casterMemberIndex),
                    false);
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
            applyBuffToMember(request.casterMemberIndex, CharacterBuffId::Mistform);
        }
        else if (spellId == SpellId::Glamour)
        {
            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                applyBuffToMember(memberIndex, CharacterBuffId::Glamour);
            }
        }
    }
    else if (rule->effectKind == PartySpellCastEffectKind::CharacterRestore)
    {
        if (spellId == SpellId::StoneToFlesh
            && request.targetWorldHit.has_value()
            && isStoneToFleshWorldTarget(*request.targetWorldHit))
        {
            castSucceeded = worldRuntime.activateWorldHitFromSpell(*request.targetWorldHit, request.spellId);
        }
        else
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

            // Below Grandmaster, Raise Dead leaves the eradicated under rules that keep the engine's limit (MAW).
            const Character *pRestored = party.member(*request.targetCharacterIndex);

            if (spellId == SpellId::RaiseDead && skillMastery < SkillMastery::Grandmaster && pRestored != nullptr
                && pRestored->conditions.test(size_t(CharacterCondition::Eradicated))
                && !party.rules().spells.raiseDeadLiftsEradication(skillMastery))
            {
                return makeFailureWithRecovery(
                    PartySpellCastStatus::Failed,
                    rule->targetKind,
                    rule->effectKind,
                    SpellFailedText);
            }

            castSucceeded = true;

            if (rulesetHeal)
            {
                // The ruleset's heal, with the spell's own cure (Remove Curse, Greater Heal) or revival; on a living
                // target Resurrection only heals (MAW, SP:300-312).
                const Character *pTarget = party.member(*request.targetCharacterIndex);
                const bool targetDead = pTarget != nullptr
                    && (pTarget->conditions.test(size_t(CharacterCondition::Dead))
                        || pTarget->conditions.test(size_t(CharacterCondition::Eradicated)));

                if (spellId == SpellId::Resurrection && !targetDead)
                {
                    healTracked(*request.targetCharacterIndex, *rulesetHeal);
                }
                else if (spellId == SpellId::Resurrection)
                {
                    party.reviveMember(*request.targetCharacterIndex, std::max(1, *rulesetHeal), true);
                }
                else
                {
                    if (spellId != SpellId::Heal)
                    {
                        applyCharacterRestoreSpell(party, request.spellId, *request.targetCharacterIndex, skillLevel);
                    }

                    healTracked(*request.targetCharacterIndex, *rulesetHeal);
                }
            }
            else if (spellId == SpellId::Heal)
            {
                party.healMember(*request.targetCharacterIndex, standardHealAmount(skillMastery, skillLevel));
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
    }
    else if (rule->effectKind == PartySpellCastEffectKind::PartyRestore)
    {
        castSucceeded = true;

        if (spellId == SpellId::Awaken)
        {
            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                const Character *pMember = party.member(memberIndex);

                if (pMember != nullptr
                    && pMember->conditions.test(static_cast<size_t>(CharacterCondition::Asleep)))
                {
                    appendAffectedCharacterIndex(result.affectedCharacterIndices, memberIndex);
                }

                party.clearMemberCondition(memberIndex, CharacterCondition::Asleep);
            }
        }
        else if (spellId == SpellId::SharedLife && rulesetHeal && spellRules.shareLife(party, *rulesetHeal))
        {
            // The ruleset pooled and shared the hit points.
        }
        else if (spellId == SpellId::SharedLife)
        {
            int totalHealth = 0;

            for (const Character &member : party.members())
            {
                totalHealth += std::max(0, member.health);
            }

            totalHealth += rulesetHeal.value_or(static_cast<int>(
                (skillMastery == SkillMastery::Grandmaster ? 4 : 3) * static_cast<int>(skillLevel)));
            const int memberCount = std::max<int>(1, static_cast<int>(party.members().size()));
            const int share = std::max(0, totalHealth / memberCount);

            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                party.healMember(memberIndex, share);
            }
        }
        else if (spellId == SpellId::PowerCure)
        {
            const int healAmount = rulesetHeal.value_or(10 + static_cast<int>(5 * skillLevel));

            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                healTracked(memberIndex, healAmount);
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
                pMember->conditionStartGameMinutes.fill(0.0f);
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
        worldRuntime.requestPartyJump(JumpSpellVerticalVelocity, JumpSpellLift);
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
                const uint16_t enchantId = party.specialItemEnchantTable() != nullptr
                    ? party.specialItemEnchantTable()->findId(enchantKind)
                    : 0;

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

                // A failed enchantment breaks the item unless it is hardened.
                const bool canBreak = !ItemRuntime::isHardened(pMutableInventoryItem->hardened, *pTargetItemDefinition);

                if (itemValue < qualityThreshold)
                {
                    pMutableInventoryItem->broken = canBreak;
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
                    pMutableInventoryItem->broken = canBreak;
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
                move.useFullscreenLoading = request.utilityMapMoveUseFullscreenLoading;
                pEventRuntimeState->pendingMapMove = move;
                castSucceeded = true;
            }
            else if (spellId == SpellId::LloydsBeacon)
            {
                if (!worldRuntime.allowsLloydsBeacon())
                {
                    return makeFailureWithRecovery(
                        PartySpellCastStatus::Failed,
                        rule->targetKind,
                        rule->effectKind,
                        SpellFailedText);
                }

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
    else if (rule->effectKind == PartySpellCastEffectKind::Telekinesis)
    {
        if (request.telekinesisTarget.has_value())
        {
            castSucceeded = worldRuntime.activateTelekinesisTarget(*request.telekinesisTarget);
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
        worldRequest.damage = rollSpellDamage(*pSpellEntry, skillMastery, skillLevel, worldRequest.critical);
        worldRequest.damageType = party.rules().combat.partySpellDamageType(
            request.spellId, GameMechanics::spellCombatDamageType(request.spellId, &spellTable));
        worldRequest.turnBasedPendingAction = request.turnBasedPendingAction;
        worldRequest.sourceX = projectileSource.x;
        worldRequest.sourceY = projectileSource.y;
        worldRequest.sourceZ = projectileSource.z;
        worldRequest.targetX = targetPoint.x;
        worldRequest.targetY = targetPoint.y;
        worldRequest.targetZ = targetPoint.z;
        worldRequest.targetActorIndex = request.targetActorIndex;
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
        const SpellSourcePoint projectileSource = offsetPartyProjectileSourceForMember(
            request,
            SpellSourcePoint{.x = sourceX, .y = sourceY, .z = sourceZ},
            SpellSourcePoint{.x = targetPoint.x, .y = targetPoint.y, .z = targetPoint.z},
            party.members().size());

        for (uint32_t projectileIndex = 0; projectileIndex < spellNumbers.projectileCount; ++projectileIndex)
        {
            const float yawRadians = targetAngleRadians + GameMechanics::projectileFanYawOffsetRadians(
                spellNumbers.projectileCount,
                projectileIndex,
                spreadArcRadians);
            GameplayPartySpellProjectileRequest worldRequest = {};
            worldRequest.casterMemberIndex = static_cast<uint32_t>(request.casterMemberIndex);
            worldRequest.spellId = request.spellId;
            worldRequest.skillLevel = skillLevel;
            worldRequest.skillMastery = skillMastery;
            worldRequest.damage = rollSpellDamage(*pSpellEntry, skillMastery, skillLevel, worldRequest.critical);
            worldRequest.damageType = party.rules().combat.partySpellDamageType(
                request.spellId, GameMechanics::spellCombatDamageType(request.spellId, &spellTable));
            worldRequest.turnBasedPendingAction = request.turnBasedPendingAction;
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
        if (spellId == SpellId::Sunray && !sunrayIndoors
            && (worldRuntime.currentHour() < 5 || worldRuntime.currentHour() >= 21))
        {
            return makeFailureWithRecovery(
                PartySpellCastStatus::Failed,
                rule->targetKind,
                rule->effectKind,
                SpellFailedText);
        }

        if (request.targetActorIndex && spellId == SpellId::Telepathy)
        {
            const std::optional<GameplayCorpseViewState> loot =
                worldRuntime.revealActorLoot(*request.targetActorIndex);

            if (!loot)
            {
                return makeFailureWithRecovery(
                    PartySpellCastStatus::Failed,
                    rule->targetKind,
                    rule->effectKind,
                    SpellFailedText);
            }

            result.statusText = telepathyLootStatusText(*loot, party.itemTable());
            castSucceeded = true;
        }
        else if (request.targetActorIndex)
        {
            GameplayActorInspectState targetBefore = {};
            const bool hasTarget = worldRuntime.actorInspectState(*request.targetActorIndex, 0, targetBefore);
            const bool hasDrainTarget =
                spellId == SpellId::Lifedrain && hasTarget && party.rules().combat.lifedrainHealsCasterThird();
            bool critical = false;
            int damage = rollSpellDamage(*pSpellEntry, skillMastery, skillLevel, critical);

            // A share of the target's hit points replaces the roll under rules that have one (MAW's Mass Distortion).
            if (hasTarget)
            {
                GameplayRuntimeActorState targetRuntime = {};
                const bool hasFacts = worldRuntime.actorRuntimeState(*request.targetActorIndex, targetRuntime);
                const SpellTargetState target = {
                    targetBefore.currentHp, targetBefore.maxHp, hasFacts ? &targetRuntime.rulesetFacts : nullptr};

                if (const std::optional<int> share = party.rules().combat.spellDamageOnTarget(
                        castAtLevel(*pSpellEntry, skillMastery, skillLevel), target))
                {
                    damage = *share;
                }
            }

            castSucceeded = worldRuntime.applyPartySpellToActor(
                *request.targetActorIndex,
                request.spellId,
                skillLevel,
                skillMastery,
                damage,
                sourceX,
                sourceY,
                footZ,
                static_cast<uint32_t>(request.casterMemberIndex),
                critical);

            if (castSucceeded && hasDrainTarget)
            {
                GameplayActorInspectState targetAfter = {};

                if (worldRuntime.actorInspectState(*request.targetActorIndex, 0, targetAfter))
                {
                    const int drainedHealth = targetBefore.currentHp - targetAfter.currentHp;

                    if (drainedHealth > 0
                        && party.healMember(request.casterMemberIndex, std::max(1, drainedHealth / 3)))
                    {
                        appendAffectedCharacterIndex(result.affectedCharacterIndices, request.casterMemberIndex);
                    }
                }
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
                        static_cast<uint32_t>(request.casterMemberIndex),
                        false);
                }
            }

            const SpellSplash splash = spellRules.spellSplash(request.spellId, skillMastery);

            if (castSucceeded && splash.extraTargets > 0)
            {
                applySpellSplash(
                    worldRuntime,
                    spellRules,
                    request,
                    splash,
                    targetPoint,
                    skillLevel,
                    skillMastery,
                    sourceX,
                    sourceY,
                    sourceZ,
                    footZ);
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
                // Each caster keeps their own summons up to the mastery's limit; past it the rules may add a permanent
                // Grandmaster wisp (MAW). At the limit the cast is refused without spending SP or recovery, and no
                // wisp is replaced (MM8-Rel 0x42c1c9).
                const size_t summoned = summonedMonsterCount(worldRuntime, request.casterMemberIndex);
                const size_t limit = summonWispLimit(skillMastery);
                const size_t extraWisps = party.rules().spells.extraPermanentWisps(skillMastery);
                const bool permanent = summoned >= limit;

                if (summoned >= limit + extraWisps)
                {
                    return makeFailure(
                        request.spellId,
                        PartySpellCastStatus::Failed,
                        rule->targetKind,
                        rule->effectKind,
                        SummonLimitText);
                }

                castSucceeded = worldRuntime.summonFriendlyMonsterById(
                    permanent ? SummonWispGrandmasterMonsterId : summonWispMonsterIdForMastery(skillMastery),
                    1,
                    permanent ? PermanentWispSeconds : summonWispDurationSeconds(skillLevel, skillMastery),
                    sourceX,
                    sourceY,
                    footZ,
                    int32_t(request.casterMemberIndex));
            }

            const bool daylightOnly = spellId == SpellId::Sunray && !sunrayIndoors;

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
                    : spellId == SpellId::Fear
                    ? 4096.0f
                    : spellId == SpellId::SummonWisp
                    ? 0.0f
                    : spellId == SpellId::SpiritLash
                    ? party.rules().spells.spiritLashRadius(skillMastery)
                    : spellId == SpellId::SoulDrinker
                    ? SoulDrinkerOutdoorRange
                    : spellId == SpellId::Armageddon
                    ? 8192.0f
                    : 4096.0f;
            std::vector<size_t> actorIndices;
            if (effectRadius > 0.0f && spellId != SpellId::Armageddon)
            {
                if (areaSpellAffectsVisibleCreatures(spellId))
                {
                    actorIndices = worldRuntime.collectVisibleMapActorIndicesWithinRadius(
                        effectCenterX,
                        effectCenterY,
                        effectCenterZ,
                        effectRadius,
                        sourceX,
                        sourceY,
                        sourceZ,
                        request.viewX,
                        request.viewY,
                        request.viewZ,
                        request.viewYawRadians,
                        request.viewPitchRadians,
                        request.viewAspectRatio);
                }
                else
                {
                    actorIndices = worldRuntime.collectMapActorIndicesWithinRadius(
                        effectCenterX,
                        effectCenterY,
                        effectCenterZ,
                        effectRadius,
                        true,
                        sourceX,
                        sourceY,
                        sourceZ);
                }
            }

            int totalSoulDrinkerDrain = 0;

            for (size_t actorIndex : actorIndices)
            {
                GameplayRuntimeActorState actor = {};

                if (!worldRuntime.actorRuntimeState(actorIndex, actor))
                {
                    continue;
                }

                if ((spellId == SpellId::Fear || !areaSpellAffectsVisibleCreatures(spellId))
                    && !actor.hostileToParty)
                {
                    continue;
                }

                if (areaSpellAffectsVisibleCreatures(spellId))
                {
                    const float actorTargetZ =
                        actor.preciseZ + GameMechanics::actorTargetHeight(actor.height);

                    if (!isActorPointInsideSpellView(request, actor.preciseX, actor.preciseY, actorTargetZ))
                    {
                        continue;
                    }
                }

                bool critical = false;
                const int spellDamage = rollSpellDamage(*pSpellEntry, skillMastery, skillLevel, critical);
                const bool applied = worldRuntime.applyPartySpellToActor(
                    actorIndex,
                    request.spellId,
                    skillLevel,
                    skillMastery,
                    spellDamage,
                    sourceX,
                    sourceY,
                    footZ,
                    static_cast<uint32_t>(request.casterMemberIndex),
                    critical);
                castSucceeded = applied || castSucceeded;

                if (spellId == SpellId::SoulDrinker && applied)
                {
                    totalSoulDrinkerDrain += std::max(1, spellDamage);
                }
            }

            castSucceeded = castSucceeded || areaSpellSucceedsWithoutTargets(spellId);

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
            else if (spellId == SpellId::Inferno && castSucceeded)
            {
                result.screenOverlayRequest = PartySpellCastResult::ScreenOverlayRequest{
                    .colorAbgr = makeAbgr(255, 56, 24),
                    .durationSeconds = 0.52f,
                    .peakAlpha = 0.60f
                };
            }
            else if (spellId == SpellId::Armageddon)
            {
                castSucceeded = true;
            }
            else if (spellId == SpellId::DispelMagic)
            {
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
        spellRules.afterCast(party, request.casterMemberIndex, request.spellId, spellTable, worldRuntime.isIndoorMap(),
            !request.quickCast);
    }

    if (healedTotal > 0)
    {
        spellRules.afterHeal(party, request.casterMemberIndex, healedTotal, overhealed, int(result.manaCost),
            result.recoverySeconds);
    }

    if (request.applyRecovery && result.recoverySeconds > 0.0f)
    {
        party.applyRecoveryToMember(request.casterMemberIndex, result.recoverySeconds);
    }

    result.status = PartySpellCastStatus::Succeeded;
    return result;
}

std::optional<uint32_t> PartySpellSystem::manaCost(
    const Party &party,
    const Character &caster,
    const SpellTable &spellTable,
    uint32_t spellId)
{
    const SpellEntry *pSpellEntry = spellTable.findById(static_cast<int>(spellId));
    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;

    if (pSpellEntry == nullptr || !resolveSpellSkill(caster, spellId, {}, skillLevel, skillMastery))
    {
        return std::nullopt;
    }

    if (!resolveBackendSpellRule(spellId, skillMastery))
    {
        return std::nullopt;
    }

    CharacterSpellCast cast = {};
    cast.pCaster = &caster;
    cast.pItemTable = party.itemTable();
    cast.pStandardItemEnchantTable = party.standardItemEnchantTable();
    cast.pSpecialItemEnchantTable = party.specialItemEnchantTable();
    cast.pSpell = pSpellEntry;
    cast.mastery = skillMastery;
    cast.skillLevel = skillLevel;
    cast.partyCount = int(std::max<size_t>(1, party.members().size()));
    return static_cast<uint32_t>(
        party.rules().spells.manaCost(cast, spellNumbersAtMastery(*pSpellEntry, skillMastery).manaCost));
}

std::optional<int> PartySpellSystem::healAmount(
    const Party &party,
    const Character &caster,
    const SpellTable &spellTable,
    uint32_t spellId)
{
    const SpellEntry *pSpellEntry = spellTable.findById(static_cast<int>(spellId));
    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;

    if (pSpellEntry == nullptr || !resolveSpellSkill(caster, spellId, {}, skillLevel, skillMastery))
    {
        return std::nullopt;
    }

    CharacterSpellCast cast = {};
    cast.pCaster = &caster;
    cast.pItemTable = party.itemTable();
    cast.pStandardItemEnchantTable = party.standardItemEnchantTable();
    cast.pSpecialItemEnchantTable = party.specialItemEnchantTable();
    cast.pSpell = pSpellEntry;
    cast.mastery = skillMastery;
    cast.skillLevel = skillLevel;
    cast.partyCount = int(std::max<size_t>(1, party.members().size()));

    if (const std::optional<int> rulesetHeal = party.rules().spells.healAmount(cast))
    {
        return rulesetHeal;
    }

    return spellIdFromValue(spellId) == SpellId::Heal ? std::optional<int>(standardHealAmount(skillMastery, skillLevel))
                                                      : std::nullopt;
}

// Meteor Shower and Starburst rain down on the point itself rather than flying towards it. The far point's height is
// kept low, the party's feet or the far point, whichever is lower: the outdoor cast and the marker lift it to the
// ground under it, so a far mountain top or a flying party does not burst it in the air.
bx::Vec3 PartySpellSystem::resolveFallingSpellTargetPoint(
    const IGameplayWorldRuntime &worldRuntime,
    uint32_t spellId,
    const bx::Vec3 &targetPoint)
{
    if (!isSpellId(spellId, SpellId::MeteorShower) && !isSpellId(spellId, SpellId::Starburst))
    {
        return targetPoint;
    }

    const float dx = targetPoint.x - worldRuntime.partyX();
    const float dy = targetPoint.y - worldRuntime.partyY();
    const float distance = std::sqrt(dx * dx + dy * dy);

    if (distance <= FallingSpellTargetRange)
    {
        return targetPoint;
    }

    const float scale = FallingSpellTargetRange / distance;
    return {
        worldRuntime.partyX() + dx * scale,
        worldRuntime.partyY() + dy * scale,
        std::min(worldRuntime.partyFootZ(), targetPoint.z)
    };
}

bool PartySpellSystem::isActorWithinSpellTargetRange(const IGameplayWorldRuntime &worldRuntime, size_t actorIndex)
{
    GameplayRuntimeActorState actor = {};

    if (!worldRuntime.actorRuntimeState(actorIndex, actor))
    {
        return false;
    }

    const float dx = actor.preciseX - worldRuntime.partyX();
    const float dy = actor.preciseY - worldRuntime.partyY();
    const float dz = actor.preciseZ - worldRuntime.partyFootZ();
    return dx * dx + dy * dy + dz * dz <= SpellActorTargetRange * SpellActorTargetRange;
}

bool PartySpellSystem::isUsableSpellActorTarget(
    const IGameplayWorldRuntime &worldRuntime,
    size_t actorIndex,
    bool requireHostile)
{
    GameplayRuntimeActorState actor = {};

    if (!worldRuntime.actorRuntimeState(actorIndex, actor)
        || actor.isDead
        || actor.isInvisible
        || (requireHostile && !actor.hostileToParty))
    {
        return false;
    }

    return isActorWithinSpellTargetRange(worldRuntime, actorIndex);
}

std::optional<size_t> PartySpellSystem::quickCastActorTarget(
    const IGameplayWorldRuntime &worldRuntime,
    const SpellRules &spellRules,
    uint32_t spellId)
{
    std::vector<size_t> visible = worldRuntime.spellActionVisibleHostileActorIndices();
    std::erase_if(visible, [&worldRuntime](size_t actorIndex)
        {
            return !isUsableSpellActorTarget(worldRuntime, actorIndex, true);
        });

    if (!spellRules.quickCastSpreadsDebuff(spellId))
    {
        return visible.empty() ? std::nullopt : std::optional<size_t>(visible.front());
    }

    constexpr float MaxDistance = 4800.0f;
    const SpellId spell = spellIdFromValue(spellId);
    const MonsterTable *pMonsterTable = worldRuntime.monsterTable();
    std::optional<size_t> target;
    float soonest = std::numeric_limits<float>::max();

    for (size_t actorIndex : visible)
    {
        GameplayRuntimeActorState actor = {};
        GameplayActorInspectState debuffs = {};

        if (!worldRuntime.actorRuntimeState(actorIndex, actor)
            || !worldRuntime.actorInspectState(actorIndex, 0, debuffs))
        {
            continue;
        }

        const float dx = actor.preciseX - worldRuntime.partyX();
        const float dy = actor.preciseY - worldRuntime.partyY();
        const float dz = actor.preciseZ - worldRuntime.partyFootZ();

        // Not a monster no crowd control holds (MAW's Unstoppable bosses, castCCSpell).
        if (dx * dx + dy * dy + dz * dz > MaxDistance * MaxDistance
            || spellRules.ignoresCrowdControl(actor.rulesetFacts))
        {
            continue;
        }

        if (spell == SpellId::ControlUndead)
        {
            const MonsterTable::MonsterStatsEntry *pStats =
                pMonsterTable != nullptr ? pMonsterTable->findStatsById(actor.monsterId) : nullptr;

            if (pStats == nullptr || !pStats->hasKind(MonsterKind::Undead))
            {
                continue;
            }
        }

        // The time left on this spell's debuff; MAW keeps Charm, Berserk and Enslave apart, our actors hold one
        // control.
        const auto controlFor = [&debuffs](GameplayActorControlMode mode)
        {
            return debuffs.controlMode == mode ? debuffs.controlRemainingSeconds : 0.0f;
        };
        float remaining = 0.0f;

        switch (spell)
        {
            case SpellId::Slow:
                remaining = debuffs.slowRemainingSeconds;
                break;
            case SpellId::Paralyze:
                remaining = debuffs.paralyzeRemainingSeconds;
                break;
            case SpellId::DarkGrasp:
                remaining = debuffs.darkGraspRemainingSeconds;
                break;
            case SpellId::Berserk:
                remaining = controlFor(GameplayActorControlMode::Berserk);
                break;
            case SpellId::Enslave:
            case SpellId::ControlUndead:
                remaining = std::max(controlFor(GameplayActorControlMode::Enslaved),
                    controlFor(GameplayActorControlMode::ControlUndead));
                break;
            default:
                remaining = controlFor(GameplayActorControlMode::Charm);
                break;
        }

        if (remaining < soonest)
        {
            soonest = remaining;
            target = actorIndex;
        }
    }

    return target;
}

bool PartySpellSystem::hasQuickCastCharacterTarget(uint32_t spellId)
{
    switch (spellIdFromValue(spellId))
    {
        case SpellId::Heal:
        case SpellId::CureDisease:
        case SpellId::RemoveCurse:
        case SpellId::RemoveFear:
        case SpellId::CureParalysis:
        case SpellId::CureInsanity:
        case SpellId::CureWeakness:
        case SpellId::CurePoison:
        case SpellId::RaiseDead:
        case SpellId::Resurrection:
        case SpellId::StoneToFlesh:
            return true;
        default:
            return false;
    }
}

std::optional<size_t> PartySpellSystem::quickCastCharacterTarget(
    const Party &party,
    size_t casterIndex,
    uint32_t spellId,
    const SpellTable *pSpellTable)
{
    // Measured against the HP a member can reach: what its auras hold back (MAW's legendary 32) never fills.
    const auto share = [&party](size_t memberIndex)
    {
        return double(party.members()[memberIndex].health) / party.reachableMaximumHealth(memberIndex);
    };
    const auto has = [](const Character &member, std::initializer_list<CharacterCondition> conditions)
    {
        return std::any_of(conditions.begin(), conditions.end(),
            [&member](CharacterCondition condition)
            {
                return member.conditions.test(size_t(condition));
            });
    };
    using enum CharacterCondition;
    const std::initializer_list<CharacterCondition> beyondHealing = {Dead, Eradicated, Petrified};

    // The member who has what the spell cures (the dead for the revivals), the lowest HP share first; a cure passes the
    // dead, eradicated and petrified by (STD2-4).
    const auto withCondition = [&](std::initializer_list<CharacterCondition> conditions,
                                   bool skipBeyondHealing = false) -> std::optional<size_t>
    {
        std::optional<size_t> target;

        for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
        {
            const Character &member = party.members()[memberIndex];

            if (has(member, conditions) && !(skipBeyondHealing && has(member, beyondHealing))
                && (!target || share(memberIndex) < share(*target)))
            {
                target = memberIndex;
            }
        }

        return target;
    };

    switch (spellIdFromValue(spellId))
    {
        case SpellId::RaiseDead:
            return withCondition({Dead});
        case SpellId::Resurrection:
            return withCondition({Dead, Eradicated});
        case SpellId::StoneToFlesh:
            return withCondition({Petrified});
        default:
            break;
    }

    // A heal goes where it does the most: to the lowest share among members at or below a third of their maximum,
    // else to whoever gains the most HP from this cast, ties to the lowest share. Never to the dead, petrified or
    // whole.
    const Character *pCaster = party.member(casterIndex);
    const std::optional<int> heal = pCaster != nullptr && pSpellTable != nullptr
        ? healAmount(party, *pCaster, *pSpellTable, spellId)
        : std::nullopt;

    if (heal)
    {
        std::optional<size_t> endangered;
        std::optional<size_t> bestGain;
        int bestGainAmount = 0;

        for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
        {
            const Character &member = party.members()[memberIndex];
            const int missing = party.reachableMaximumHealth(memberIndex) - member.health;

            if (missing <= 0 || has(member, beyondHealing))
            {
                continue;
            }

            if (share(memberIndex) <= 1.0 / 3.0 && (!endangered || share(memberIndex) < share(*endangered)))
            {
                endangered = memberIndex;
            }

            const int gain = std::min(*heal, missing);

            if (!bestGain || gain > bestGainAmount
                || (gain == bestGainAmount && share(memberIndex) < share(*bestGain)))
            {
                bestGain = memberIndex;
                bestGainAmount = gain;
            }
        }

        if (endangered || bestGain)
        {
            return endangered ? endangered : bestGain;
        }

        // Nobody wounded: a heal that also cures (MAW's Greater Heal, Remove Curse) goes to the condition below.
    }

    switch (spellIdFromValue(spellId))
    {
        case SpellId::RemoveCurse:
            return withCondition({Cursed}, true);
        case SpellId::RemoveFear:
            return withCondition({Fear}, true);
        case SpellId::CureParalysis:
            return withCondition({Paralyzed}, true);
        case SpellId::CureInsanity:
            return withCondition({Insane}, true);
        case SpellId::CureWeakness:
            return withCondition({Weak}, true);
        case SpellId::CurePoison:
            return withCondition({PoisonWeak, PoisonMedium, PoisonSevere}, true);
        case SpellId::CureDisease:
            return withCondition({DiseaseWeak, DiseaseMedium, DiseaseSevere}, true);
        default:
            break;
    }

    // Any other spell on a member (buffs): the wounded member with the fewest hit points.
    std::optional<size_t> target;

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        const Character &member = party.members()[memberIndex];

        if (member.health >= party.reachableMaximumHealth(memberIndex) || has(member, beyondHealing))
        {
            continue;
        }

        if (!target || member.health < party.members()[*target].health)
        {
            target = memberIndex;
        }
    }

    return target;
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
