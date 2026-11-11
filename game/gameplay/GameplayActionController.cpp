#include "game/gameplay/GameplayActionController.h"
#include "engine/Localization.h"

#include "game/audio/GameAudioSystem.h"
#include "game/gameplay/CorpseLootRuntime.h"
#include "game/gameplay/GameplayActorHitFeedback.h"
#include "game/gameplay/GameplayFxService.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplaySparring.h"
#include "game/gameplay/GameplaySpellService.h"
#include "game/gameplay/MeleeContactEffects.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/mm9/Mm9HirelingCombat.h"
#include "game/mm9/Mm9HirelingTable.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SkillData.h"
#include "game/party/SpellIds.h"
#include "game/rules/GameRules.h"
#include "game/StringUtils.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MonsterProjectileTable.h"
#include "game/tables/MonsterTable.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
constexpr float CharacterMeleeAttackDistance = 407.2f;
constexpr float CharacterRangedAttackDistance = 5120.0f;
constexpr float DragonBreathSourceHeight = 96.0f;
constexpr float PartyMemberProjectileLateralSpacing = 28.0f;
constexpr float ProjectileRightVectorEpsilon = 0.0001f;
constexpr float MeleeContactNormalEpsilon = 0.0001f;
// A blow below this fraction of the target's maximum HP glances; at or above the crushing fraction (or a kill or
// critical damage) it crushes.
constexpr float MeleeGlancingDamageFraction = 0.06f;
constexpr float MeleeCrushingDamageFraction = 0.3f;
// The camera kick on a critical or killing melee blow, about 1.5 degrees.
constexpr float MeleeCameraKickRadians = 0.026f;
// Fireball's explosion, where a Carnage arrow strikes.
constexpr uint32_t FireballExplosionObjectId = 1051;

void resetQuickCastRepeatState(GameplayScreenState::QuickSpellState &quickSpellState)
{
    quickSpellState.castRepeatCooldownSeconds = 0.0f;
    quickSpellState.castLatch = false;
    quickSpellState.castRepeating = false;
    quickSpellState.readyMemberAvailableWhileHeld = false;
}

float distanceBetween(
    const GameplayActionController::WorldPoint &left,
    const GameplayActionController::WorldPoint &right)
{
    const float deltaX = left.x - right.x;
    const float deltaY = left.y - right.y;
    const float deltaZ = left.z - right.z;
    return std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
}

float actorDistanceFromParty(
    const GameplayActionController::PartyAttackActorFacts &actor,
    const GameplayActionController::WorldPoint &partyPosition)
{
    return std::max(0.0f, distanceBetween(actor.position, partyPosition) - static_cast<float>(actor.radius));
}

GameplayActionController::WorldPoint actorRangedTargetPoint(
    const GameplayActionController::PartyAttackActorFacts &actor)
{
    return GameplayActionController::WorldPoint{
        .x = actor.position.x,
        .y = actor.position.y,
        .z = actor.position.z + GameMechanics::actorTargetHeight(actor.height),
    };
}

GameplayWorldPoint toRuntimeWorldPoint(const GameplayActionController::WorldPoint &point)
{
    return GameplayWorldPoint{
        .x = point.x,
        .y = point.y,
        .z = point.z,
    };
}

struct MeleeContact
{
    GameplayActionController::WorldPoint point = {};
    GameplayActionController::WorldPoint normal = {};
};

// Where the blow lands: the crosshair hit on the target, else the world's visual contact point, else the target's body
// surface facing the party. The normal points outward from the target's centre.
std::optional<MeleeContact> resolveMeleeContact(
    const GameplayActionController::PartyAttackConfig &config,
    const GameplayActionController::PartyAttackActorFacts &target)
{
    const GameplayActionController::WorldPoint center = {
        .x = target.position.x,
        .y = target.position.y,
        .z = target.position.z + static_cast<float>(target.height) * 0.5f,
    };
    const GameplayActionController::WorldPoint sourceNormal = {
        .x = config.rangedSource.x - center.x,
        .y = config.rangedSource.y - center.y,
        .z = config.rangedSource.z - center.z,
    };
    GameplayActionController::WorldPoint normal = sourceNormal;
    GameplayActionController::WorldPoint contact = center;
    bool resolvedVisualContact = false;
    if (config.directTargetActorIndex == target.actorIndex && config.directTargetHitPoint)
    {
        contact = *config.directTargetHitPoint;
        resolvedVisualContact = true;
    }
    else if (config.pWorldRuntime != nullptr)
    {
        const std::optional<GameplayWorldPoint> fallbackContact =
            config.pWorldRuntime->partyAttackActorContactPoint(target.actorIndex, config.fallbackQuery);
        if (fallbackContact)
        {
            contact = {fallbackContact->x, fallbackContact->y, fallbackContact->z};
            resolvedVisualContact = true;
        }
    }

    if (resolvedVisualContact)
    {
        normal = {
            .x = contact.x - center.x,
            .y = contact.y - center.y,
            .z = contact.z - center.z,
        };
    }

    float normalLength = std::sqrt(normal.x * normal.x + normal.y * normal.y + normal.z * normal.z);
    if (!std::isfinite(normalLength) || normalLength <= MeleeContactNormalEpsilon)
    {
        normal = sourceNormal;
        normalLength = std::sqrt(normal.x * normal.x + normal.y * normal.y + normal.z * normal.z);
    }
    if (!std::isfinite(normalLength) || normalLength <= MeleeContactNormalEpsilon)
    {
        return std::nullopt;
    }
    normal.x /= normalLength;
    normal.y /= normalLength;
    normal.z /= normalLength;

    if (!resolvedVisualContact)
    {
        const float contactRadius = std::max(1.0f, static_cast<float>(target.radius));
        contact.x += normal.x * contactRadius;
        contact.y += normal.y * contactRadius;
        contact.z += normal.z * contactRadius;
    }

    return MeleeContact{contact, normal};
}

// The struck material's contact effect (blood, sparks, chips, drops) on the contact point, out of the body, more of it
// for a harder blow. Blood and gore follow the blood setting, the rest the hit effects setting.
void queueMeleeContactParticles(
    const GameplayActionController::PartyAttackConfig &config,
    const GameplayActionController::PartyAttackActorFacts &target,
    const MeleeContact &contact,
    MeleeHitStrength strength)
{
    if (config.pRuntime == nullptr || config.pMonsterTable == nullptr)
    {
        return;
    }

    const MonsterTable::MeleeHitMaterial *pMaterial = config.pMonsterTable->findMeleeHitMaterial(target.monsterId);
    const GameSettings &settings = config.pRuntime->settingsSnapshot();

    if (pMaterial == nullptr
        || pMaterial->contactEffectId.empty()
        || !(pMaterial->blood ? settings.meleeHitBloodEffects : settings.meleeHitEffects))
    {
        return;
    }

    config.pRuntime->fxService().queueSurfaceEffect(
        meleeContactEffectVariant(pMaterial->contactEffectId, strength),
        {contact.point.x, contact.point.y, contact.point.z},
        {contact.normal.x, contact.normal.y, contact.normal.z},
        meleeContactParticleScale(static_cast<float>(target.height)));
}

MeleeHitStrength resolveMeleeHitStrength(
    const GameplayActionController::PartyAttackActorFacts &target,
    const CharacterAttackResult &attack,
    int appliedDamage,
    bool killed)
{
    const float damageFraction = target.maxHp > 0
        ? static_cast<float>(appliedDamage) / static_cast<float>(target.maxHp) : 1.0f;

    if (killed || attack.criticalDamage || damageFraction >= MeleeCrushingDamageFraction)
    {
        return MeleeHitStrength::Crushing;
    }

    return damageFraction < MeleeGlancingDamageFraction ? MeleeHitStrength::Glancing : MeleeHitStrength::Normal;
}

// Where and how the attacker's blow is drawn over the contact point: the weapon's class and element, from the
// attacker's side of the party. Empty when the blow cannot face the camera.
std::optional<MeleeContactEffectPlacement> placeMeleeBlow(
    const GameplayActionController::PartyAttackConfig &config,
    const Character &attacker,
    size_t attackerIndex,
    const GameplayActionController::PartyAttackActorFacts &target,
    const MeleeContact &contact,
    MeleeHitStrength strength,
    bool missed)
{
    const ItemDefinition *pWeapon = config.pItemTable != nullptr && attacker.equipment.mainHand != 0
            && !attacker.equipmentRuntime.mainHand.broken
        ? config.pItemTable->get(attacker.equipment.mainHand) : nullptr;
    std::mt19937 rng(config.randomSeed
        ^ static_cast<uint32_t>((target.actorIndex + 1) * 2246822519u)
        ^ static_cast<uint32_t>((attackerIndex + 1) * 3266489917u));
    std::uniform_real_distribution<float> variation(-1.0f, 1.0f);

    MeleeContactEffectInput input;
    input.weaponClass =
        meleeWeaponClassForSkill(canonicalSkillName(pWeapon != nullptr ? pWeapon->skillGroup : "Unarmed"));
    input.strength = strength;
    input.missed = missed;
    ElementalDamageBonuses weaponElements = ItemEnchantRuntime::characterAttackElementalDamageRange(
        attacker,
        CharacterAttackMode::Melee,
        config.pItemTable,
        config.pSpecialItemEnchantTable).maximum;
    weaponElements += ItemEnchantRuntime::characterWeaponDamageElements(
        attacker, CharacterAttackMode::Melee, config.pItemTable);
    input.elements = meleeWeaponElementsFor(weaponElements);
    input.contact = {contact.point.x, contact.point.y, contact.point.z};
    input.viewer = {config.rangedSource.x, config.rangedSource.y, config.rangedSource.z};

    // The camera from the attack's view matrix (bx column-major rows: right, up, back; translation in 12 to 14).
    const std::array<float, 16> &view = config.fallbackQuery.viewMatrix;
    const std::array<float, 3> cameraRight = {view[0], view[4], view[8]};
    const std::array<float, 3> cameraUp = {view[1], view[5], view[9]};
    const std::array<float, 3> cameraBack = {view[2], view[6], view[10]};

    if (std::abs(cameraRight[0] * cameraRight[0] + cameraRight[1] * cameraRight[1] + cameraRight[2] * cameraRight[2]
            - 1.0f) < 0.01f)
    {
        for (size_t axis = 0; axis < 3; ++axis)
        {
            input.viewer[axis] =
                -(view[12] * cameraRight[axis] + view[13] * cameraUp[axis] + view[14] * cameraBack[axis]);
        }
        input.screenRight = cameraRight;
        input.screenUp = cameraUp;
    }
    input.memberIndex = attackerIndex;
    input.memberCount = config.pParty != nullptr ? config.pParty->memberCount() : 1;
    input.targetHeight = static_cast<float>(target.height);
    input.twoHanded = pWeapon != nullptr
        && (pWeapon->equipStat == "Weapon2" || (pWeapon->equipStat == "Weapon1or2" && attacker.equipment.offHand == 0));
    input.variation = variation(rng);
    return buildMeleeContactEffect(input);
}

// The blow's effect and its element accents, when hit effects are on.
void queueMeleeBlowEffects(
    const GameplayActionController::PartyAttackConfig &config,
    const MeleeContactEffectPlacement &placement)
{
    if (config.pRuntime == nullptr || !config.pRuntime->settingsSnapshot().meleeHitEffects)
    {
        return;
    }

    GameplayFxService &fxService = config.pRuntime->fxService();
    fxService.queueWorldEffect(placement.effectId, placement.position, placement.rotation, placement.scale);

    for (const std::string &accentEffectId : placement.accentEffectIds)
    {
        fxService.queueWorldEffect(accentEffectId, placement.position, placement.rotation, placement.scale);
    }
}

// A small turn of the view along a critical or killing blow, when the camera kick is on.
void kickCameraAlongMeleeBlow(
    const GameplayActionController::PartyAttackConfig &config,
    const MeleeContactEffectPlacement &placement)
{
    if (config.pRuntime == nullptr
        || config.pWorldRuntime == nullptr
        || !config.pRuntime->settingsSnapshot().meleeCameraKick)
    {
        return;
    }

    config.pWorldRuntime->actorHitFeedback().triggerCameraKick(
        placement.blowScreenDirection[0],
        placement.blowScreenDirection[1],
        MeleeCameraKickRadians);
}

// Impact sound of the struck material, then an optional flash and a hitstop on the target, scaled by the blow's
// strength.
void presentMeleeHitFeedback(
    const GameplayActionController::PartyAttackConfig &config,
    const GameplayActionController::PartyAttackActorFacts &target,
    const MeleeContact &contact,
    MeleeHitStrength strength)
{
    if (config.pRuntime == nullptr
        || config.pWorldRuntime == nullptr
        || !config.pRuntime->settingsSnapshot().meleeHitFeedback)
    {
        return;
    }

    const MonsterTable::MeleeHitMaterial *pMaterial =
        config.pMonsterTable != nullptr ? config.pMonsterTable->findMeleeHitMaterial(target.monsterId) : nullptr;
    GameAudioSystem *pAudioSystem = config.pRuntime->audioSystem();

    if (pMaterial != nullptr && pAudioSystem != nullptr)
    {
        const std::string &soundPath = pMaterial->impactSoundPaths[static_cast<size_t>(strength)];

        if (!soundPath.empty())
        {
            pAudioSystem->playAssetInstance(
                soundPath,
                GameAudioSystem::PlaybackGroup::World,
                GameAudioSystem::WorldPosition{contact.point.x, contact.point.y, contact.point.z},
                false);
        }
    }

    struct HitFeedbackTuning
    {
        float flashSeconds;
        float flashPeak;
        float hitstopSeconds;
    };
    static constexpr std::array<HitFeedbackTuning, 3> TuningByStrength = {{
        {0.07f, 0.12f, 0.0f},
        {0.09f, 0.18f, 0.05f},
        {0.12f, 0.25f, 0.09f},
    }};
    const HitFeedbackTuning &tuning = TuningByStrength[static_cast<size_t>(strength)];
    const bool flash = config.pRuntime->settingsSnapshot().meleeHitFlash;
    config.pWorldRuntime->actorHitFeedback().trigger(
        target.actorIndex,
        flash ? tuning.flashSeconds : 0.0f,
        flash ? tuning.flashPeak : 0.0f,
        tuning.hitstopSeconds);
}

float partyMemberProjectileLateralOffset(size_t memberIndex, size_t memberCount)
{
    if (memberCount <= 1 || memberIndex >= memberCount)
    {
        return 0.0f;
    }

    const float centerIndex = (static_cast<float>(memberCount) - 1.0f) * 0.5f;
    return (centerIndex - static_cast<float>(memberIndex)) * PartyMemberProjectileLateralSpacing;
}

GameplayActionController::WorldPoint offsetPartyProjectileSourceForMember(
    const GameplayActionController::PartyAttackConfig &config,
    const GameplayActionController::WorldPoint &target,
    size_t memberIndex,
    size_t memberCount)
{
    const float lateralOffset = partyMemberProjectileLateralOffset(memberIndex, memberCount);

    if (lateralOffset == 0.0f)
    {
        return config.rangedSource;
    }

    float rightX = config.rangedRight.x;
    float rightY = config.rangedRight.y;
    float rightZ = config.rangedRight.z;
    float rightLength = std::sqrt(rightX * rightX + rightY * rightY + rightZ * rightZ);

    if (rightLength <= ProjectileRightVectorEpsilon)
    {
        const float forwardX = target.x - config.rangedSource.x;
        const float forwardY = target.y - config.rangedSource.y;
        const float forwardLength = std::sqrt(forwardX * forwardX + forwardY * forwardY);

        if (forwardLength <= ProjectileRightVectorEpsilon)
        {
            return config.rangedSource;
        }

        rightX = -forwardY / forwardLength;
        rightY = forwardX / forwardLength;
        rightZ = 0.0f;
        rightLength = 1.0f;
    }

    GameplayActionController::WorldPoint source = config.rangedSource;
    source.x += rightX / rightLength * lateralOffset;
    source.y += rightY / rightLength * lateralOffset;
    source.z += rightZ / rightLength * lateralOffset;
    return source;
}

GameplayActionController::WorldPoint dragonBreathSourcePoint(
    const GameplayActionController::WorldPoint &rangedSource,
    const GameplayActionController::PartyAttackConfig &config)
{
    GameplayActionController::WorldPoint source = rangedSource;
    source.z = std::min(source.z, config.partyPosition.z + DragonBreathSourceHeight);
    return source;
}

CharacterAttackMode choosePartyAttackMode(
    const CharacterAttackProfile &profile,
    bool targetInMeleeRange,
    bool eyeUnderWater)
{
    // A dragon bites a target in melee range and breathes at anything further.
    if (profile.hasDragonBreath && profile.rangedAttackBonus.has_value() && !targetInMeleeRange)
    {
        return CharacterAttackMode::DragonBreath;
    }

    if (profile.hasBlaster && profile.rangedAttackBonus.has_value())
    {
        return CharacterAttackMode::Blaster;
    }

    if (profile.hasWand && profile.rangedAttackBonus.has_value())
    {
        return CharacterAttackMode::Wand;
    }

    if (targetInMeleeRange)
    {
        return CharacterAttackMode::Melee;
    }

    // No bow, crossbow or thrown weapon is fired with the eye under a scene water volume (MM9 object.lto 0x100b3ede).
    if (profile.hasBow && profile.rangedAttackBonus.has_value() && !eyeUnderWater)
    {
        return CharacterAttackMode::Bow;
    }

    return CharacterAttackMode::Melee;
}

// Energy Blades Grandmaster: the hit may cut a raised shield to a share of what is left before it lands
// (MonsterShieldTable::overloadRules). Only rolls against a raised shield, so other targets keep their dice.
void tryOverloadActorShield(const GameplayActionController::PartyAttackConfig &config, size_t actorIndex,
    std::mt19937 &rng, std::optional<float> chance = std::nullopt)
{
    GameplayActorShields *pShields = config.pWorldRuntime->actorShields();

    if (pShields == nullptr || pShields->table() == nullptr || pShields->shieldPoints(actorIndex) <= 0.0f)
    {
        return;
    }

    const ShieldOverloadRules &rules = pShields->table()->overloadRules();

    if (std::uniform_real_distribution<float>(0.0f, 1.0f)(rng) < chance.value_or(rules.chance))
    {
        pShields->cutRaisedShield(actorIndex, rules.remainingFraction);
    }
}

CharacterAttackResult buildUntargetedMeleeAttack(const CharacterAttackProfile &profile)
{
    CharacterAttackResult attack = {};
    attack.mode = CharacterAttackMode::Melee;
    attack.canAttack = true;
    attack.hit = false;
    attack.attackBonus = profile.meleeAttackBonus;
    attack.recoverySeconds = profile.meleeRecoverySeconds;
    attack.shieldTier = profile.meleeShieldTier;
    attack.attackSoundHook = "melee_swing";
    attack.voiceHook = "attack";
    return attack;
}

CharacterAttackResult buildWorldObjectMeleeAttack(
    const CharacterAttackProfile &profile,
    float targetDistance,
    std::mt19937 &rng)
{
    CharacterAttackResult attack = buildUntargetedMeleeAttack(profile);
    attack.hit = true;
    attack.damageType = CombatDamageType::Physical;
    attack.targetDistance = std::max(0.0f, targetDistance);
    const int minimumDamage = std::max(1, profile.meleeMinDamage);
    const int maximumDamage = std::max(minimumDamage, profile.meleeMaxDamage);
    std::uniform_int_distribution<int> damageDistribution(minimumDamage, maximumDamage);
    attack.damage = damageDistribution(rng);
    return attack;
}

CharacterAttackResult buildRangedReleaseAttack(
    CharacterAttackMode mode,
    const CharacterAttackProfile &profile,
    std::mt19937 &rng)
{
    CharacterAttackResult attack = {};
    attack.mode = mode;
    attack.canAttack = profile.rangedAttackBonus.has_value();
    attack.hit = false;
    attack.resolvesOnImpact = true;
    attack.attackBonus = profile.rangedAttackBonus.value_or(profile.meleeAttackBonus);
    attack.recoverySeconds = profile.rangedRecoverySeconds;
    attack.skillLevel = profile.rangedSkillLevel;
    attack.skillMastery = profile.rangedSkillMastery;
    attack.projectileCount = profile.rangedProjectileCount;
    attack.projectileSpreadArcRadians = profile.rangedSpreadArcRadians;
    attack.spellId = profile.rangedSpellId;
    attack.shieldTier = profile.rangedShieldTier;
    attack.attackSoundHook = "wand_cast";

    if (mode == CharacterAttackMode::Bow)
    {
        attack.attackSoundHook = "bow_shot";
    }
    else if (mode == CharacterAttackMode::Blaster)
    {
        attack.attackSoundHook = attack.projectileSpreadArcRadians > 0.0f ? "blaster_scatter_shot" : "blaster_shot";
        attack.damageType = CombatDamageType::Irresistible;
    }
    else if (mode == CharacterAttackMode::DragonBreath)
    {
        attack.damageType = CombatDamageType::Irresistible;
    }

    attack.voiceHook = "attack";

    if (attack.canAttack)
    {
        attack.minimumDamage = profile.rangedMinDamage;
        attack.maximumDamage = std::max(profile.rangedMinDamage, profile.rangedMaxDamage);
        attack.damage = std::uniform_int_distribution<int>(attack.minimumDamage, attack.maximumDamage)(rng);
    }

    return attack;
}

std::optional<GameplayActionController::PartyAttackActorFacts> resolveUsableActorTarget(
    const GameplayActionController::PartyAttackConfig &config,
    std::optional<size_t> actorIndex)
{
    if (!actorIndex || config.pWorldRuntime == nullptr)
    {
        return std::nullopt;
    }

    const std::optional<GameplayPartyAttackActorFacts> actor =
        config.pWorldRuntime->partyAttackActorFacts(*actorIndex, false);

    if (!actor || !GameplayActionController::isPartyAttackActorTargetable(*actor) || !actor->lineOfSightToParty)
    {
        return std::nullopt;
    }

    return GameplayActionController::PartyAttackActorFacts{
        .actorIndex = actor->actorIndex,
        .monsterId = actor->monsterId,
        .displayName = actor->displayName,
        .position = {
            .x = actor->position.x,
            .y = actor->position.y,
            .z = actor->position.z,
        },
        .radius = actor->radius,
        .height = actor->height,
        .currentHp = actor->currentHp,
        .maxHp = actor->maxHp,
        .effectiveArmorClass = actor->effectiveArmorClass,
        .hourOfPowerPower = actor->hourOfPowerPower,
        .rulesetFacts = actor->rulesetFacts,
        .isDead = actor->isDead,
        .isInvisible = actor->isInvisible,
        .hostileToParty = actor->hostileToParty,
        .visibleForFallback = actor->visibleForFallback,
        .lineOfSightToParty = actor->lineOfSightToParty,
    };
}

std::optional<GameplayActionController::PartyAttackActorFacts> chooseFallbackRangedTarget(
    const GameplayActionController::PartyAttackConfig &config)
{
    if (config.pWorldRuntime == nullptr)
    {
        return std::nullopt;
    }

    const std::vector<GameplayPartyAttackActorFacts> actors =
        config.pWorldRuntime->collectPartyAttackFallbackActors(config.fallbackQuery);
    float bestDistance = std::numeric_limits<float>::max();
    std::optional<GameplayActionController::PartyAttackActorFacts> bestActor;

    for (const GameplayPartyAttackActorFacts &actor : actors)
    {
        if (!GameplayActionController::isPartyAttackFallbackCandidate(actor))
        {
            continue;
        }

        const GameplayActionController::PartyAttackActorFacts actionActor{
            .actorIndex = actor.actorIndex,
            .monsterId = actor.monsterId,
            .displayName = actor.displayName,
            .position = {
                .x = actor.position.x,
                .y = actor.position.y,
                .z = actor.position.z,
            },
            .radius = actor.radius,
            .height = actor.height,
            .currentHp = actor.currentHp,
            .maxHp = actor.maxHp,
            .effectiveArmorClass = actor.effectiveArmorClass,
            .hourOfPowerPower = actor.hourOfPowerPower,
            .rulesetFacts = actor.rulesetFacts,
            .isDead = actor.isDead,
            .isInvisible = actor.isInvisible,
            .hostileToParty = actor.hostileToParty,
            .visibleForFallback = actor.visibleForFallback,
            .lineOfSightToParty = actor.lineOfSightToParty,
        };
        const float distance = actorDistanceFromParty(actionActor, config.partyPosition);

        if (distance > CharacterRangedAttackDistance)
        {
            continue;
        }

        if (distance < bestDistance)
        {
            bestDistance = distance;
            bestActor = actionActor;
        }
    }

    return bestActor;
}

// The world missile an attacker's equipped gun fires (monster_projectiles.yml party), the main hand's first.
std::optional<PartyGunMissile> resolvePartyGunMissile(
    const GameplayActionController::PartyAttackConfig &config,
    const Character &attacker,
    const CharacterAttackResult &attack)
{
    if (attack.mode != CharacterAttackMode::Blaster || config.pMonsterProjectileTable == nullptr)
    {
        return std::nullopt;
    }

    for (const uint32_t itemId : {attacker.equipment.mainHand, attacker.equipment.bow})
    {
        if (const std::optional<PartyGunMissile> gun = config.pMonsterProjectileTable->findPartyGun(itemId))
        {
            return gun;
        }
    }

    return std::nullopt;
}

void playPartyAttackSound(
    const GameplayActionController::PartyAttackConfig &config,
    const Character &attacker,
    const CharacterAttackResult &attack)
{
    if (config.pRuntime == nullptr)
    {
        return;
    }

    if (attack.attackSoundHook == "wand_cast" && attack.spellId > 0)
    {
        return;
    }

    SoundId soundId = SoundId::SwingBlunt01;

    if (attack.attackSoundHook == "bow_shot")
    {
        soundId = SoundId::ShootBow;
    }
    else if (const std::optional<PartyGunMissile> gun = resolvePartyGunMissile(config, attacker, attack);
             gun && gun->shotSoundId != 0)
    {
        if (GameAudioSystem *pAudioSystem = config.pRuntime->audioSystem())
        {
            pAudioSystem->playSound(
                gun->shotSoundId,
                GameAudioSystem::PlaybackGroup::World,
                GameAudioSystem::WorldPosition{config.rangedSource.x, config.rangedSource.y, config.rangedSource.z});
        }

        return;
    }
    else if (attack.attackSoundHook == "blaster_shot")
    {
        soundId = SoundId::ShootBlaster;
    }
    else if (attack.attackSoundHook == "blaster_scatter_shot")
    {
        soundId = SoundId::ShootBlasterScatter;
    }
    else
    {
        soundId = GameMechanics::resolveCharacterAttackSoundId(attacker, config.pItemTable, attack.mode);
    }

    GameAudioSystem *pAudioSystem = config.pRuntime->audioSystem();

    if (pAudioSystem == nullptr)
    {
        return;
    }

    pAudioSystem->playCommonSound(
        soundId,
        GameAudioSystem::PlaybackGroup::World,
        GameAudioSystem::WorldPosition{config.rangedSource.x, config.rangedSource.y, config.rangedSource.z});
}

// The blow's damage after the monster's resistances; `elementalDamage` gets what its enchantments and auras added.
int resolveMeleeAppliedDamage(
    const GameplayActionController::PartyAttackConfig &config,
    const Character &attacker,
    const GameplayActionController::PartyAttackActorFacts &target,
    const CharacterAttackResult &attack,
    std::mt19937 &rng,
    int &elementalDamage,
    bool recordCombatLog = true)
{
    elementalDamage = 0;
    int appliedDamage = attack.damage;

    if (config.pMonsterTable == nullptr)
    {
        return appliedDamage;
    }

    const MonsterTable::MonsterStatsEntry *pStats = config.pMonsterTable->findStatsById(target.monsterId);

    if (pStats == nullptr)
    {
        return appliedDamage;
    }

    const int multiplier = gameRulesFor(config.pParty).combat.weaponKindMultiplierApplies()
        ? ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
              attacker,
              CharacterAttackMode::Melee,
              config.pItemTable,
              config.pSpecialItemEnchantTable,
              pStats->kindFlags)
        : 1;
    // The weapons' elemental enchantments roll for each blow and join it; a weapon's poison share is already in it.
    // Each part is resisted by its own element. A ruleset that builds its blows' elements itself supplies them.
    ElementalDamageBonuses additionalDamage = {};

    if (!attack.rulesWeaponElements && gameRulesFor(config.pParty).combat.addsWeaponElementalDamage())
    {
        const ElementalDamageBonuses enchantDamage = ItemEnchantRuntime::rollCharacterAttackElementalDamage(
            attacker,
            CharacterAttackMode::Melee,
            config.pItemTable,
            config.pSpecialItemEnchantTable,
            rng);
        appliedDamage += enchantDamage.total();
        additionalDamage = enchantDamage;
        additionalDamage += ItemEnchantRuntime::characterWeaponDamageElements(
            attacker, CharacterAttackMode::Melee, config.pItemTable);
    }

    additionalDamage.fire *= multiplier;
    additionalDamage.air *= multiplier;
    additionalDamage.water *= multiplier;
    additionalDamage.body *= multiplier;
    additionalDamage.light *= multiplier;
    additionalDamage.dark *= multiplier;
    additionalDamage.fire += attack.rulesElementalDamage.fire;
    additionalDamage.air += attack.rulesElementalDamage.air;
    additionalDamage.water += attack.rulesElementalDamage.water;
    additionalDamage.body += attack.rulesElementalDamage.body;
    additionalDamage.light += attack.rulesElementalDamage.light;
    additionalDamage.dark += attack.rulesElementalDamage.dark;
    elementalDamage = additionalDamage.fire + additionalDamage.air + additionalDamage.water + additionalDamage.body
        + additionalDamage.light + additionalDamage.dark;

    // A world enchantment's bonus against its monsters (Hesper's Kreegan-bane).
    if (attacker.meleeWeaponEnchant.bonusAgainst(target.monsterId))
    {
        appliedDamage += appliedDamage * attacker.meleeWeaponEnchant.bonusDamagePercent / 100;
    }

    MonsterDamageHit hit = {};
    hit.amount = appliedDamage * multiplier;
    hit.type = attack.damageType;
    hit.weaponElements = additionalDamage;
    hit.resistances = MonsterDamageResistances{
        .fire = pStats->fireResistance,
        .air = pStats->airResistance,
        .water = pStats->waterResistance,
        .earth = pStats->earthResistance,
        .spirit = pStats->spiritResistance,
        .mind = pStats->mindResistance,
        .body = pStats->bodyResistance,
        .light = pStats->lightResistance,
        .dark = pStats->darkResistance,
        .physical = pStats->physicalResistance,
    };
    hit.hourOfPowerResistanceBonus = target.hourOfPowerPower;
    hit.targetFacts = target.rulesetFacts;
    hit.pMeleeAttacker = &attacker;
    hit.lateDamage = attack.rulesLateDamage;
    hit.pItemTable = config.pItemTable;
    hit.targetCurrentHp = target.currentHp;
    hit.pRng = &rng;
    return gameRulesFor(config.pParty).combat.damageToMonster(hit, recordCombatLog);
}

std::mt19937 buildPartyAttackRng(
    const GameplayActionController::PartyAttackConfig &config,
    size_t actingMemberIndex,
    std::optional<size_t> targetActorIndex)
{
    const uint32_t seed =
        config.randomSeed
        ^ static_cast<uint32_t>((targetActorIndex.value_or(0) + 1) * 2654435761u)
        ^ static_cast<uint32_t>(actingMemberIndex * 40503u);
    return std::mt19937(seed);
}

void clearInvisibility(Party &party)
{
    if (party.hasPartyBuff(PartyBuffId::Invisibility))
    {
        party.clearPartyBuff(PartyBuffId::Invisibility);
    }
}

// The ranged weapon a Shoot order fires, choosePartyAttackMode's choice at a target out of reach; none without one.
std::optional<CharacterAttackMode> shootingAttackMode(const CharacterAttackProfile &profile, bool eyeUnderWater)
{
    const CharacterAttackMode mode = choosePartyAttackMode(profile, false, eyeUnderWater);
    return mode != CharacterAttackMode::Melee ? std::optional<CharacterAttackMode>(mode) : std::nullopt;
}

BattleOrderSituation battleOrderSituation(const Party &party, size_t memberIndex, std::optional<float> targetDistance)
{
    BattleOrderSituation situation;
    situation.targetDistance = targetDistance;

    for (size_t index = 0; index < party.members().size(); ++index)
    {
        const Character &member = party.members()[index];
        const int maximum = party.reachableMaximumHealth(index);

        // The dead, eradicated and stoned are beyond a heal.
        if (maximum <= 0
            || member.conditions.test(size_t(CharacterCondition::Dead))
            || member.conditions.test(size_t(CharacterCondition::Eradicated))
            || member.conditions.test(size_t(CharacterCondition::Petrified)))
        {
            continue;
        }

        situation.lowestAllyHealthShare =
            std::min(situation.lowestAllyHealthShare, std::max(0.0f, float(member.health) / float(maximum)));
    }

    if (const Character *pMember = party.member(memberIndex))
    {
        situation.spellPoints = pMember->spellPoints;
        situation.maximumSpellPoints = party.reachableMaximumSpellPoints(memberIndex);
    }

    return situation;
}

// A spell order the member can cast now: known, paid for (mana and the rules' other means: an Assassin's combo
// points), its conditions met with the SP it leaves, no party buff it gives already up, and allowed at this place and
// hour. Whether it finds a target is the cast's own business.
bool castableOrderSpell(
    const GameplayActionController::PartyAttackConfig &config,
    size_t memberIndex,
    const Character &member,
    const BattleOrder &order,
    const BattleOrderSituation &situation)
{
    if (config.pParty == nullptr || config.pSpellTable == nullptr || config.pRuntime == nullptr
        || config.pSpellService == nullptr)
    {
        return false;
    }

    const SpellEntry *pSpellEntry = config.pSpellTable->findByName(order.spellName, spellKnownBy(member));

    if (pSpellEntry == nullptr || !member.knowsSpell(uint32_t(pSpellEntry->id)))
    {
        return false;
    }

    const uint32_t spellId = uint32_t(pSpellEntry->id);
    const Party &party = *config.pParty;
    const std::optional<uint32_t> manaCost = PartySpellSystem::manaCost(party, member, *config.pSpellTable, spellId);

    if ((manaCost && !party.canSpendSpellPoints(memberIndex, int(*manaCost)))
        || party.rules().spells.castRefusal(party, memberIndex, spellId).has_value()
        || !battleOrderConditionsHold(order, situation, manaCost.value_or(0)))
    {
        return false;
    }

    const std::optional<PartyBuffId> partyBuff = PartySpellSystem::partyBuffOfSpell(party, spellId);

    if (partyBuff && party.hasPartyBuff(*partyBuff))
    {
        return false;
    }

    return config.pWorldRuntime == nullptr || PartySpellSystem::worldAllowsSpell(party, *config.pWorldRuntime, spellId);
}

// An MM9 hireling's turn (devdocs/mm9/MM9_HIRELINGS.md 9.2): it acts from the party's position at the creature under
// the crosshair. A blow or shot rolls the row's dice with the monster attack rules (Mm9HirelingCombat; its numbers are
// a MONSTERS row) and lands through the party's own melee and missile paths, so monster resistances, kills and
// experience stay with them. A caster's spell goes through PartySpellSystem::castSpell as a wand's does, at the row's
// skill and mastery and without mana, so each spell keeps its one implementation. Then the row's recovery.
GameplayActionController::PartyAttackExecutionResult executeHirelingAttack(
    const GameplayActionController::PartyAttackConfig &config,
    size_t combatantIndex)
{
    GameplayActionController::PartyAttackExecutionResult result = {};
    Party &party = *config.pParty;
    const Mm9PartyHireling *pPartyHireling = party.hirelingCombatant(combatantIndex);
    const Mm9Hireling *pRow = pPartyHireling != nullptr && config.pMm9HirelingTable != nullptr
        ? config.pMm9HirelingTable->find(pPartyHireling->rudeId)
        : nullptr;
    Character *pHireling = party.combatant(combatantIndex);

    if (pRow == nullptr || pHireling == nullptr || !GameMechanics::canTakeGameplayAction(*pHireling))
    {
        return result;
    }

    // The rules' scale of the row (MAW: the party's level, MawClassRules::scaleHirelings); 1 under Standard.
    const double damageScale = pPartyHireling->rulesDamageScale;
    const double skillScale = pPartyHireling->rulesSkillScale;
    result.attempted = true;
    result.actingMemberIndex = combatantIndex;

    if (party.hasPartyBuff(PartyBuffId::Invisibility))
    {
        party.clearPartyBuff(PartyBuffId::Invisibility);
    }

    const std::optional<GameplayActionController::PartyAttackActorFacts> target =
        resolveUsableActorTarget(config, config.directTargetActorIndex);
    result.targetActorIndex = target ? std::optional<size_t>(target->actorIndex) : std::nullopt;
    const float targetDistance = target ? actorDistanceFromParty(*target, config.partyPosition) : 0.0f;
    const bool targetInMeleeRange = target.has_value() && targetDistance <= CharacterMeleeAttackDistance;
    std::mt19937 rng = buildPartyAttackRng(config, combatantIndex, result.targetActorIndex);
    const bool turnBased = config.pRuntime != nullptr && config.pRuntime->turnBasedCombatRuntime().active();
    const Mm9HirelingAction action = chooseMm9HirelingAction(
        *pRow, target.has_value(), targetInMeleeRange, std::uniform_int_distribution<int>(1, 100)(rng), turnBased);
    CharacterAttackResult attack = {};
    attack.recoverySeconds = Party::hirelingRecoverySeconds(*pHireling, pRow->recoverySeconds);
    bool actionPerformed = false;
    bool attacked = false;
    bool killed = false;
    std::optional<int> appliedMeleeDamage;
    GameplayActionController::WorldPoint rangedTarget = target ? actorRangedTargetPoint(*target)
        : config.hasRayRangedTarget ? config.rayRangedTarget
                                    : config.defaultRangedTarget;

    if (action.kind == Mm9HirelingActionKind::Spell && config.pSpellTable != nullptr && config.pWorldRuntime != nullptr)
    {
        const SpellEntry *pSpellEntry = config.pSpellTable->findByName(action.pSpell->name);

        if (pSpellEntry != nullptr)
        {
            PartySpellCastRequest spellRequest = {};
            spellRequest.casterMemberIndex = combatantIndex;
            spellRequest.spellId = uint32_t(pSpellEntry->id);
            spellRequest.quickCast = true;
            spellRequest.targetActorIndex = result.targetActorIndex;
            spellRequest.hasTargetPoint = true;
            spellRequest.targetX = rangedTarget.x;
            spellRequest.targetY = rangedTarget.y;
            spellRequest.targetZ = rangedTarget.z;
            spellRequest.skillLevelOverride =
                std::max<uint32_t>(1, uint32_t(std::lround(action.pSpell->skillLevel * skillScale)));
            spellRequest.skillMasteryOverride = action.pSpell->mastery;
            spellRequest.bypassRequiredMastery = true;
            spellRequest.turnBasedPendingAction = turnBased;
            spellRequest.spendMana = false;
            spellRequest.applyRecovery = false;
            const PartySpellCastResult spellResult =
                PartySpellSystem::castSpell(party, *config.pWorldRuntime, *config.pSpellTable, spellRequest);
            attacked = spellResult.status == PartySpellCastStatus::Succeeded;
            actionPerformed = attacked;
            attack.mode = CharacterAttackMode::Wand;
            attack.canAttack = true;
            attack.spellId = pSpellEntry->id;

            if (attacked)
            {
                config.pWorldRuntime->applyPendingSpellCastWorldEffects(spellResult);
            }
        }
    }
    else if (action.kind == Mm9HirelingActionKind::Melee && config.pWorldRuntime != nullptr)
    {
        attack.mode = CharacterAttackMode::Melee;
        attack.canAttack = true;
        attack.damageType = action.pAttack->damageType;
        actionPerformed = true;

        // Turn-based with nothing in reach: the blow swings at the air and spends the turn.
        if (targetInMeleeRange)
        {
            attack.targetArmorClass = target->effectiveArmorClass;
            attack.targetDistance = targetDistance;
            attack.hit = mm9HirelingAttackHits(*pHireling, true, target->effectiveArmorClass, rng);
            attack.damage = attack.hit
                ? int(std::lround(rollMm9HirelingAttackDamage(*action.pAttack, *pHireling, true, rng) * damageScale))
                : 0;
        }

        if (attack.hit)
        {
            int elementalDamage = 0;
            const int appliedDamage =
                resolveMeleeAppliedDamage(config, *pHireling, *target, attack, rng, elementalDamage);
            appliedMeleeDamage = appliedDamage;
            const int beforeHp = target->currentHp;
            attacked = GameplayCombatController::partyHitLands(appliedDamage, false)
                && config.pWorldRuntime->applyPartyAttackMeleeDamage(
                    target->actorIndex,
                    appliedDamage,
                    toRuntimeWorldPoint(config.partyPosition),
                    attack.shieldTier,
                    attack.shieldModifiers);

            if (attacked)
            {
                const std::optional<GameplayPartyAttackActorFacts> afterTarget =
                    config.pWorldRuntime->partyAttackActorFacts(target->actorIndex, false);
                killed = beforeHp > 0 && afterTarget && afterTarget->currentHp <= 0;

                if (const std::optional<MeleeContact> contact = resolveMeleeContact(config, *target))
                {
                    const MeleeHitStrength strength = resolveMeleeHitStrength(*target, attack, appliedDamage, killed);
                    queueMeleeContactParticles(config, *target, *contact, strength);
                    presentMeleeHitFeedback(config, *target, *contact, strength);
                }

                config.pWorldRuntime->refreshWorldHover(config.worldInspectionRefreshRequest);
            }
        }
    }
    else if (action.kind == Mm9HirelingActionKind::Ranged && config.pWorldRuntime != nullptr)
    {
        attack.mode = CharacterAttackMode::Bow;
        attack.canAttack = true;
        attack.damageType = action.pAttack->damageType;
        attack.damage =
            int(std::lround(rollMm9HirelingAttackDamage(*action.pAttack, *pHireling, false, rng) * damageScale));
        // The missile's hit roll on impact takes the hireling's level as its attack bonus, as a monster's level
        // drives its own hit roll.
        attack.attackBonus = int(pHireling->level) + pHireling->magicalBonuses.rangedAttack;
        const GameplayPartyAttackProjectileRequest projectileRequest = {
            .sourcePartyMemberIndex = combatantIndex,
            .objectId = config.arrowProjectileObjectId,
            .damage = attack.damage,
            .attackBonus = attack.attackBonus,
            .useActorHitChance = true,
            .damageType = attack.damageType,
            .source = toRuntimeWorldPoint(config.rangedSource),
            .target = toRuntimeWorldPoint(rangedTarget),
            .turnBasedPendingAction = turnBased,
            .targetActorIndex = result.targetActorIndex,
        };
        attacked = config.pWorldRuntime->spawnPartyAttackProjectile(projectileRequest);
        actionPerformed = attacked;
    }

    if (actionPerformed)
    {
        playPartyAttackSound(config, *pHireling, attack);

        if (turnBased)
        {
            config.pRuntime->turnBasedCombatRuntime().storeMemberTurnRecovery(combatantIndex, attack.recoverySeconds);
        }
        else
        {
            party.applyRecoveryToMember(combatantIndex, attack.recoverySeconds);
            party.switchToNextReadyMember();
        }
    }
    else if (!turnBased && action.kind == Mm9HirelingActionKind::None)
    {
        // Nothing in reach: MM9 passes the hireling over (9.1).
        party.switchToNextReadyMember();
    }

    GameplayCombatController::handlePartyAttackPresentation(
        config.pRuntime,
        GameplayCombatController::PartyAttackPresentation{
            .memberIndex = combatantIndex,
            .attackerName = pHireling->name,
            .targetName = target ? (!config.directTargetName.empty() ? config.directTargetName : target->displayName)
                                 : std::string(),
            .attack = attack,
            .appliedDamage = appliedMeleeDamage,
            .actionPerformed = actionPerformed && attack.mode != CharacterAttackMode::Wand,
            .attacked = attacked,
            .hadMeleeTarget = targetInMeleeRange,
            .killed = killed,
            .targetStrongEnemy = target.has_value() && target->maxHp >= 100,
        });

    if (config.pWorldRuntime != nullptr)
    {
        config.pWorldRuntime->recordPartyAttackWorldResult(result.targetActorIndex, attacked, actionPerformed);
    }

    result.actionPerformed = actionPerformed;
    result.attacked = attacked;
    result.killed = killed;
    result.attack = attack;
    return result;
}
} // namespace

void GameplayActionController::updateCooldowns(GameplayScreenState &screenState, float deltaSeconds)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    GameplayScreenState::AttackActionState &attackActionState = screenState.attackActionState();
    GameplayScreenState::QuickSpellState &quickSpellState = screenState.quickSpellState();

    attackActionState.inspectRepeatCooldownSeconds =
        std::max(0.0f, attackActionState.inspectRepeatCooldownSeconds - deltaSeconds);
    quickSpellState.castRepeatCooldownSeconds =
        std::max(0.0f, quickSpellState.castRepeatCooldownSeconds - deltaSeconds);
}

GameplayActionController::QuickCastActionDecision GameplayActionController::updateQuickCastAction(
    GameplayScreenState::QuickSpellState &quickSpellState,
    const QuickCastActionConfig &config)
{
    if (!config.canRunAction)
    {
        resetQuickCastRepeatState(quickSpellState);
        return {};
    }

    bool readyMemberTransitionWhileHeld = false;

    if (config.quickCastPressed)
    {
        readyMemberTransitionWhileHeld =
            !quickSpellState.readyMemberAvailableWhileHeld && config.hasReadyMember;
        quickSpellState.readyMemberAvailableWhileHeld = config.hasReadyMember;
    }
    else
    {
        quickSpellState.readyMemberAvailableWhileHeld = false;
    }

    const bool pressedThisFrame = config.quickCastPressed && !quickSpellState.castLatch;
    const bool repeatReady =
        !config.turnBased
        && config.quickCastPressed
        && quickSpellState.castLatch
        && (quickSpellState.castRepeatCooldownSeconds <= 0.0f
            || ((quickSpellState.castRepeating || config.fastRepeat) && readyMemberTransitionWhileHeld));

    if (pressedThisFrame || repeatReady)
    {
        quickSpellState.attackFallbackRequested = false;
        quickSpellState.castLatch = true;
        quickSpellState.castRepeating = repeatReady;
        quickSpellState.castRepeatCooldownSeconds = repeatReady || config.fastRepeat
            ? HeldActionRepeatDebounceSeconds
            : HeldActionFirstRepeatDelaySeconds;
        return QuickCastActionDecision{
            .shouldBeginQuickCast = true,
        };
    }

    if (!config.quickCastPressed)
    {
        resetQuickCastRepeatState(quickSpellState);
    }

    return {};
}

void GameplayActionController::applyQuickCastActionResult(
    GameplayScreenState::QuickSpellState &quickSpellState,
    QuickCastActionResult result)
{
    quickSpellState.attackFallbackRequested = result == QuickCastActionResult::AttackFallback;
}

GameplayActionController::AttackActionDecision GameplayActionController::updateAttackAction(
    GameplayScreenState::AttackActionState &attackActionState,
    GameplayScreenState::QuickSpellState &quickSpellState,
    const AttackActionConfig &config)
{
    if (attackActionState.blocksAttackInput(config.attackPressed))
    {
        quickSpellState.attackFallbackRequested = false;
        return {};
    }

    const bool attackTriggeredByQuickCastFallback = quickSpellState.attackFallbackRequested;
    bool readyMemberTransitionWhileHeld = false;

    if (config.attackPressed)
    {
        readyMemberTransitionWhileHeld =
            !attackActionState.readyMemberAvailableWhileHeld && config.hasReadyMember;
        attackActionState.readyMemberAvailableWhileHeld = config.hasReadyMember;
    }
    else
    {
        attackActionState.readyMemberAvailableWhileHeld = false;
    }

    const bool pressedThisFrame =
        (config.attackPressed || attackTriggeredByQuickCastFallback) && !attackActionState.inspectLatch;
    const bool repeatReady =
        !config.turnBased
        && (config.attackPressed || attackTriggeredByQuickCastFallback)
        && attackActionState.inspectLatch
        && (attackActionState.inspectRepeatCooldownSeconds <= 0.0f
            || ((attackActionState.inspectRepeating || config.fastRepeat) && readyMemberTransitionWhileHeld));

    quickSpellState.attackFallbackRequested = false;

    if (pressedThisFrame || repeatReady)
    {
        attackActionState.inspectLatch = true;
        attackActionState.inspectRepeating = repeatReady;
        attackActionState.inspectRepeatCooldownSeconds = attackActionState.inspectRepeating || config.fastRepeat
            ? HeldActionRepeatDebounceSeconds
            : HeldActionFirstRepeatDelaySeconds;

        return AttackActionDecision{
            .shouldAttemptAttack = true,
            .pressedThisFrame = pressedThisFrame,
        };
    }

    if (!config.attackPressed)
    {
        attackActionState.clear();
    }

    return {};
}

bool GameplayActionController::crosshairDestructibleOverridesFallback(
    bool crosshairOnStandingDestructible,
    float fallbackDistance)
{
    return crosshairOnStandingDestructible && fallbackDistance > CharacterMeleeAttackDistance;
}

// One press for the active combatant: a hireling's attack, or a member's battle orders and weapon.
GameplayActionController::PartyAttackExecutionResult GameplayActionController::executeActiveCombatantAttack(
    const PartyAttackConfig &config)
{
    PartyAttackExecutionResult result = {};

    if (config.pParty == nullptr)
    {
        return result;
    }

    Party &party = *config.pParty;

    // An MM9 hireling's turn in the rotation (Party::activeCombatantIndex).
    {
        const Character *pActing = party.combatant(party.activeCombatantIndex());

        if (party.activeHireling() != nullptr
            && (pActing == nullptr || !GameMechanics::canTakeGameplayAction(*pActing)))
        {
            party.switchToNextReadyMember();
        }

        if (party.activeHireling() != nullptr)
        {
            return executeHirelingAttack(config, party.activeCombatantIndex());
        }
    }

    Character *pAttacker = party.activeMember();

    if ((pAttacker == nullptr || !GameMechanics::canTakeGameplayAction(*pAttacker))
        && party.switchToNextReadyMember())
    {
        if (party.activeHireling() != nullptr)
        {
            return executeHirelingAttack(config, party.activeCombatantIndex());
        }

        pAttacker = party.activeMember();
    }

    if (pAttacker == nullptr || !GameMechanics::canTakeGameplayAction(*pAttacker))
    {
        return result;
    }

    const size_t actingMemberIndex = party.activeMemberIndex();
    result.actingMemberIndex = actingMemberIndex;

    // A world target a blow or missile damages: a standing destructible BModel or face, or a destructible decoration
    // (an entity).
    const bool bModelTargetHit = config.pWorldRuntime != nullptr
        && config.directTargetBModelIndex.has_value()
        && config.pWorldRuntime->isPartyAttackMeleeBModelTarget(*config.directTargetBModelIndex);
    const bool entityTargetHit = config.pWorldRuntime != nullptr
        && config.directTargetEntityIndex.has_value()
        && config.pWorldRuntime->isPartyAttackMeleeEntityTarget(*config.directTargetEntityIndex);
    std::optional<PartyAttackActorFacts> target = resolveUsableActorTarget(config, config.directTargetActorIndex);

    if (!target)
    {
        target = chooseFallbackRangedTarget(config);

        // A standing destructible under the crosshair wins over a fallback hostile out of blow reach: the shot flies
        // at the crosshair (devdocs/INDOOR_DESTRUCTIBLES.md "Aiming").
        if (target
            && crosshairDestructibleOverridesFallback(
                bModelTargetHit || entityTargetHit,
                actorDistanceFromParty(*target, config.partyPosition)))
        {
            target.reset();
        }
    }

    result.targetActorIndex = target ? std::optional<size_t>(target->actorIndex) : std::nullopt;

    const float targetDistance = target ? actorDistanceFromParty(*target, config.partyPosition) : 0.0f;
    const bool targetInMeleeRange = target.has_value() && targetDistance <= CharacterMeleeAttackDistance;
    const bool worldTargetInMeleeRange = (bModelTargetHit || entityTargetHit)
        && config.directWorldTargetDistance <= CharacterMeleeAttackDistance;
    const CharacterAttackTuning attackTuning = config.pRuntime != nullptr
        ? characterAttackTuningFromSettings(config.pRuntime->settingsSnapshot())
        : CharacterAttackTuning{};
    const CharacterAttackProfile attackProfile =
        GameMechanics::buildCharacterAttackProfile(*pAttacker, config.pItemTable, config.pSpellTable, attackTuning);
    const bool eyeUnderWater =
        config.pWorldRuntime != nullptr && config.pWorldRuntime->partyBreathFraction().has_value();
    // The battle orders (game/party/BattleOrders.h): the first that holds and can be done now; a spell without a target
    // passes to the next order.
    const BattleOrderSituation situation =
        battleOrderSituation(party, actingMemberIndex, target ? std::optional<float>(targetDistance) : std::nullopt);
    std::optional<CharacterAttackMode> orderedMode;

    for (const BattleOrder &order : pAttacker->battleOrders)
    {
        if (!order.enabled)
        {
            continue;
        }

        if (order.kind == BattleOrderKind::Melee)
        {
            if ((targetInMeleeRange || worldTargetInMeleeRange) && battleOrderConditionsHold(order, situation))
            {
                orderedMode = CharacterAttackMode::Melee;
                break;
            }

            continue;
        }

        if (order.kind == BattleOrderKind::Shoot)
        {
            const std::optional<CharacterAttackMode> shooting = shootingAttackMode(attackProfile, eyeUnderWater);

            if (shooting && battleOrderConditionsHold(order, situation))
            {
                orderedMode = shooting;
                break;
            }

            continue;
        }

        if (!castableOrderSpell(config, actingMemberIndex, *pAttacker, order, situation))
        {
            continue;
        }

        GameplaySpellActionController::TargetQueries targetQueries = config.targetQueries;
        targetQueries.preferredActorIndex = target ? std::optional<size_t>(target->actorIndex)
                                                   : config.directTargetActorIndex;
        const GameplaySpellActionController::AttackCastResult cast = GameplaySpellActionController::tryBeginAttackCast(
            *config.pRuntime,
            *config.pSpellService,
            actingMemberIndex,
            order.spellName,
            targetQueries);

        if (cast.disposition == GameplaySpellActionController::AttackCastDisposition::NoTarget)
        {
            continue;
        }

        result.attempted = true;
        clearInvisibility(party);

        if (cast.disposition == GameplaySpellActionController::AttackCastDisposition::CastStarted
            && !cast.followupUiActive
            && !config.pRuntime->turnBasedCombatRuntime().active())
        {
            party.switchToNextReadyMember();
        }

        return result;
    }

    if (!orderedMode && pAttacker->battleOrderFallback == BattleOrderFallback::Hold)
    {
        result.held = true;
        return result;
    }

    result.attempted = true;
    clearInvisibility(party);
    // A destructible under the crosshair in blow reach takes a blow, as a hostile there would.
    const CharacterAttackMode attackMode = orderedMode.value_or(
        choosePartyAttackMode(attackProfile, targetInMeleeRange || worldTargetInMeleeRange, eyeUnderWater));
    std::mt19937 rng = buildPartyAttackRng(config, actingMemberIndex, result.targetActorIndex);
    CharacterAttackResult attack = {};

    if (attackMode == CharacterAttackMode::Melee && target && targetInMeleeRange)
    {
        attack = GameMechanics::resolveCharacterAttackAgainstArmorClass(
            *pAttacker,
            config.pItemTable,
            config.pSpellTable,
            target->effectiveArmorClass,
            targetDistance,
            rng,
            attackTuning);
    }
    else if (attackMode == CharacterAttackMode::Melee && worldTargetInMeleeRange)
    {
        attack = buildWorldObjectMeleeAttack(
            attackProfile,
            config.directWorldTargetDistance,
            rng);
    }
    else if (attackMode == CharacterAttackMode::Melee)
    {
        attack = buildUntargetedMeleeAttack(attackProfile);
    }
    else
    {
        attack = buildRangedReleaseAttack(attackMode, attackProfile, rng);
    }

    CharacterAttackOnMonster attackContext = {};
    attackContext.pCharacter = pAttacker;
    attackContext.pItemTable = config.pItemTable;
    attackContext.pSpecialItemEnchantTable = config.pSpecialItemEnchantTable;
    attackContext.minimumDamage =
        attack.mode == CharacterAttackMode::Melee ? attackProfile.meleeMinDamage : attackProfile.rangedMinDamage;
    attackContext.maximumDamage =
        attack.mode == CharacterAttackMode::Melee ? attackProfile.meleeMaxDamage : attackProfile.rangedMaxDamage;
    // A blow reads the target in reach; a missile the actor it is aimed at (rules crit against its level).
    attackContext.pTargetFacts = target && (attack.mode != CharacterAttackMode::Melee || targetInMeleeRange)
        ? &target->rulesetFacts
        : nullptr;
    attackContext.targetCurrentHp = attackContext.pTargetFacts != nullptr ? target->currentHp : 0;

    if (target && config.pMonsterTable != nullptr)
    {
        if (const MonsterTable::MonsterStatsEntry *pStats = config.pMonsterTable->findStatsById(target->monsterId))
        {
            attackContext.targetKindFlags = pStats->kindFlags;
        }
    }

    if (attackContext.pTargetFacts != nullptr && config.pWorldRuntime != nullptr)
    {
        attackContext.targetKey = mapActorKey(config.pWorldRuntime->mapName(), target->actorIndex);
        // A game minute is two real seconds.
        attackContext.nowSeconds = double(config.pWorldRuntime->gameMinutes()) * 2.0;

        attackContext.targetHostile = target->hostileToParty;

        // The crowd around a blow's target (MAW's Assassination thins its bonus by it, MCC:414-421).
        if (attack.mode == CharacterAttackMode::Melee)
        {
            for (const size_t nearIndex : config.pWorldRuntime->collectMapActorIndicesWithinRadius(target->position.x,
                     target->position.y, target->position.z, 384.0f, false, target->position.x, target->position.y,
                     target->position.z))
            {
                GameplayRuntimeActorState nearActor = {};
                attackContext.monstersNearTarget +=
                    config.pWorldRuntime->actorRuntimeState(nearIndex, nearActor) && !nearActor.isDead ? 1 : 0;
            }
        }
    }
    attackContext.partyCount = config.pParty != nullptr ? int(std::max<size_t>(1, config.pParty->members().size())) : 1;
    const bool sparringTarget = attack.mode == CharacterAttackMode::Melee && targetInMeleeRange
        && isSparringOpponent(config.pWorldRuntime, target->actorIndex);
    attackContext.sparring = sparringTarget;
    attackContext.pRng = &rng;
    gameRulesFor(config.pParty).combat.resolveCharacterAttack(attack, attackContext);
    result.attack = attack;

    if (attack.canAttack && attack.mode != CharacterAttackMode::Melee
        && pAttacker->conditions.test(static_cast<size_t>(CharacterCondition::Weak))
        && gameRulesFor(config.pParty).combat.callerHalvesWeakMissile(attack.mode))
    {
        attack.damage /= 2;
        result.attack = attack;
    }

    bool actionPerformed = false;
    bool attacked = false;
    bool killed = false;
    std::optional<int> appliedMeleeDamage;
    const bool hadMeleeTarget = target.has_value() && targetInMeleeRange;
    // A hit the target fully resists plays out as a miss, as in the original game.
    bool hitWithoutDamage = false;

    if (attack.mode == CharacterAttackMode::Melee)
    {
        actionPerformed = attack.canAttack;

        if (sparringTarget && attack.hit)
        {
            int elementalDamage = 0;
            const int damage = resolveMeleeAppliedDamage(config, *pAttacker, *target, attack, rng,
                elementalDamage, false);
            attacked = damage > 0;
            hitWithoutDamage = !attacked;
            if (attacked)
            {
                // Keep melee control effects, but skip damage reactions and damage-triggered effects like Fangs.
                config.pWorldRuntime->applyPartyAttackMeleeEffects(
                    target->actorIndex, attack, toRuntimeWorldPoint(config.partyPosition));
                scoreSparringHit(*config.pWorldRuntime, config.pRuntime, true, damage);
            }
        }
        else if (target
            && targetInMeleeRange
            && attack.hit
            && config.pWorldRuntime != nullptr)
        {
            int elementalDamage = 0;
            const int appliedDamage =
                resolveMeleeAppliedDamage(config, *pAttacker, *target, attack, rng, elementalDamage);
            appliedMeleeDamage = appliedDamage;
            hitWithoutDamage = !GameplayCombatController::partyHitLands(appliedDamage, attack.stunTarget);
            const int beforeHp = target->currentHp;
            const std::optional<MeleeContact> contact = resolveMeleeContact(config, *target);

            if (attack.shieldOverload && !hitWithoutDamage)
            {
                tryOverloadActorShield(config, target->actorIndex, rng);
            }

            // A world enchantment's overload (Hesper's Overloading): its own chance, the rules' cut.
            if (attack.shieldOverloadChance > 0.0f && !hitWithoutDamage)
            {
                tryOverloadActorShield(config, target->actorIndex, rng, attack.shieldOverloadChance);
            }

            attacked = !hitWithoutDamage
                && config.pWorldRuntime->applyPartyAttackMeleeDamage(
                    target->actorIndex,
                    appliedDamage,
                    toRuntimeWorldPoint(config.partyPosition),
                    attack.shieldTier,
                    attack.shieldModifiers);

            if (attacked)
            {
                config.pWorldRuntime->applyPartyAttackMeleeEffects(
                    target->actorIndex,
                    attack,
                    toRuntimeWorldPoint(config.partyPosition));

                const std::optional<GameplayPartyAttackActorFacts> afterTarget =
                    config.pWorldRuntime->partyAttackActorFacts(target->actorIndex, false);
                killed = beforeHp > 0 && afterTarget && afterTarget->currentHp <= 0;
                PartyHitOnMonster hit;
                hit.memberIndex = actingMemberIndex;
                hit.pTarget = &target->rulesetFacts;
                hit.damage = appliedDamage;
                hit.elementalDamage = std::min(elementalDamage, appliedDamage);
                hit.type = attack.damageType;
                hit.melee = true;
                hit.killed = killed;
                hit.pWorld = config.pWorldRuntime;
                hit.targetActorIndex = target->actorIndex;
                gameRulesFor(config.pParty).combat.applyPartyHitEffects(party, hit);

                // A kill may shorten the blow's recovery (MAW's Legendary 11), before it is applied below.
                if (killed)
                {
                    attack.recoverySeconds *= gameRulesFor(config.pParty).combat.killRecoveryScale(*pAttacker);
                }

                if (contact)
                {
                    const MeleeHitStrength strength =
                        resolveMeleeHitStrength(*target, attack, appliedDamage, killed);
                    queueMeleeContactParticles(config, *target, *contact, strength);
                    const std::optional<MeleeContactEffectPlacement> blow = placeMeleeBlow(
                        config, *pAttacker, actingMemberIndex, *target, *contact, strength, false);

                    if (blow)
                    {
                        queueMeleeBlowEffects(config, *blow);

                        if (killed || attack.criticalDamage)
                        {
                            kickCameraAlongMeleeBlow(config, *blow);
                        }
                    }

                    presentMeleeHitFeedback(config, *target, *contact, strength);
                }

                if (pAttacker->vampiricHealFraction > 0.0f && appliedDamage > 0)
                {
                    party.healMember(
                        actingMemberIndex,
                        std::max(1, static_cast<int>(std::round(
                            static_cast<float>(appliedDamage) * pAttacker->vampiricHealFraction))));
                }

                if (config.pWorldRuntime != nullptr)
                {
                    config.pWorldRuntime->refreshWorldHover(config.worldInspectionRefreshRequest);
                }
            }
        }
        else if (worldTargetInMeleeRange
            && attack.hit
            && attack.damage > 0
            && config.pWorldRuntime != nullptr)
        {
            appliedMeleeDamage = attack.damage;
            attacked = bModelTargetHit
                ? config.pWorldRuntime->applyPartyAttackMeleeBModelDamage(
                    *config.directTargetBModelIndex,
                    attack.damage)
                : config.pWorldRuntime->applyPartyAttackMeleeEntityDamage(
                    *config.directTargetEntityIndex,
                    attack.damage);
        }

        // A miss shows the blow passing the target; the swing sound already plays.
        if (target && targetInMeleeRange && attack.canAttack && (!attack.hit || hitWithoutDamage))
        {
            const std::optional<MeleeContact> contact = resolveMeleeContact(config, *target);
            const std::optional<MeleeContactEffectPlacement> blow = contact
                ? placeMeleeBlow(config, *pAttacker, actingMemberIndex, *target, *contact, MeleeHitStrength::Normal, true)
                : std::nullopt;

            if (blow)
            {
                queueMeleeBlowEffects(config, *blow);
            }
        }
    }
    else if (attack.canAttack)
    {
        WorldPoint rangedTarget = config.defaultRangedTarget;

        if (target)
        {
            rangedTarget = actorRangedTargetPoint(*target);
        }
        else if (config.hasRayRangedTarget)
        {
            rangedTarget = config.rayRangedTarget;
        }

        const WorldPoint rangedSource = offsetPartyProjectileSourceForMember(
            config,
            rangedTarget,
            actingMemberIndex,
            party.members().size());

        if (attack.mode == CharacterAttackMode::DragonBreath)
        {
            if (attack.spellId > 0 && config.pWorldRuntime != nullptr)
            {
                const WorldPoint source = dragonBreathSourcePoint(rangedSource, config);
                attacked = config.pWorldRuntime->castPartySpellProjectile(
                    GameplayPartySpellProjectileRequest{
                        .casterMemberIndex = static_cast<uint32_t>(actingMemberIndex),
                        .spellId = static_cast<uint32_t>(attack.spellId),
                        .skillLevel = attack.skillLevel,
                        .skillMastery = static_cast<SkillMastery>(attack.skillMastery),
                        .damage = attack.damage,
                        .damageType = GameMechanics::spellCombatDamageType(
                            static_cast<uint32_t>(attack.spellId),
                            config.pSpellTable),
                        .sourceX = source.x,
                        .sourceY = source.y,
                        .sourceZ = source.z,
                        .targetX = rangedTarget.x,
                        .targetY = rangedTarget.y,
                        .targetZ = rangedTarget.z,
                        .effectSoundIdOverride = static_cast<uint32_t>(SoundId::DragonBreath),
                        .impactSoundIdOverride = static_cast<uint32_t>(SoundId::DragonBreathImpact),
                        .turnBasedPendingAction =
                            config.pRuntime != nullptr && config.pRuntime->turnBasedCombatRuntime().active(),
                        .targetActorIndex = result.targetActorIndex,
                        .critical = attack.criticalDamage,
                    });
            }
        }
        else if (attack.mode == CharacterAttackMode::Wand)
        {
            if (attack.spellId > 0 && config.pSpellTable != nullptr && config.pWorldRuntime != nullptr)
            {
                PartySpellCastRequest spellRequest = {};
                spellRequest.casterMemberIndex = actingMemberIndex;
                spellRequest.spellId = static_cast<uint32_t>(attack.spellId);
                spellRequest.quickCast = true;
                spellRequest.targetActorIndex = target ? std::optional<size_t>(target->actorIndex) : std::nullopt;
                spellRequest.hasTargetPoint = true;
                spellRequest.targetX = rangedTarget.x;
                spellRequest.targetY = rangedTarget.y;
                spellRequest.targetZ = rangedTarget.z;
                spellRequest.skillLevelOverride = attack.skillLevel;
                spellRequest.skillMasteryOverride = static_cast<SkillMastery>(attack.skillMastery);
                // Wands cast at fixed wand power; the spell mastery gate is for learned spell casting.
                spellRequest.bypassRequiredMastery = true;
                spellRequest.spendMana = false;
                spellRequest.applyRecovery = false;

                const PartySpellCastResult spellResult =
                    PartySpellSystem::castSpell(party, *config.pWorldRuntime, *config.pSpellTable, spellRequest);
                attacked = spellResult.status == PartySpellCastStatus::Succeeded;

                if (attacked)
                {
                    config.pWorldRuntime->applyPendingSpellCastWorldEffects(spellResult);
                    party.consumeEquippedWandCharge(actingMemberIndex);
                }
            }
        }
        else if (config.pWorldRuntime != nullptr)
        {
            uint32_t projectileObjectId = attack.fireArrow && config.fireArrowProjectileObjectId != 0
                ? config.fireArrowProjectileObjectId
                : config.arrowProjectileObjectId;
            const ItemDefinition *pRangedWeapon = config.pItemTable != nullptr
                ? config.pItemTable->get(pAttacker->equipment.bow)
                : nullptr;

            if (pRangedWeapon != nullptr && canonicalSkillName(pRangedWeapon->skillGroup) == "Throwing")
            {
                projectileObjectId = toLowerCopy(pRangedWeapon->unidentifiedName).find("axe") != std::string::npos
                    ? config.throwingAxeProjectileObjectId
                    : config.throwingDaggerProjectileObjectId;
            }

            const std::optional<PartyGunMissile> partyGun = resolvePartyGunMissile(config, *pAttacker, attack);
            GameplayPartyAttackProjectileRequest projectileRequest = {
                .sourcePartyMemberIndex = actingMemberIndex,
                .objectId = partyGun ? uint32_t(partyGun->pMissile->objectId)
                    : attack.mode == CharacterAttackMode::Blaster
                        ? config.blasterProjectileObjectId
                        : projectileObjectId,
                .impactObjectId = partyGun ? uint32_t(partyGun->pMissile->impactObjectId)
                    : attack.mode == CharacterAttackMode::Blaster ? config.blasterProjectileObjectId + 1
                    : attack.explosiveArrow                       ? FireballExplosionObjectId
                                                                  : 0,
                .impactSoundId = partyGun ? partyGun->pMissile->impactSoundId : 0,
                .damage = attack.damage,
                .attackBonus = attack.attackBonus,
                // A Carnage arrow never misses (it explodes).
                .useActorHitChance = !attack.explosiveArrow,
                .damageType = attack.damageType,
                .shieldTier = attack.shieldTier,
                .shieldModifiers = attack.shieldModifiers,
                .weakerOfPhysicalAndFire = attack.fireArrow,
                .explosionRadius = attack.explosiveArrow
                    ? GameplayProjectileService::spellImpactDamageRadius(uint32_t(SpellId::Fireball))
                    : 0.0f,
                .source = toRuntimeWorldPoint(rangedSource),
                .target = toRuntimeWorldPoint(rangedTarget),
                .turnBasedPendingAction =
                    config.pRuntime != nullptr && config.pRuntime->turnBasedCombatRuntime().active(),
                // A fanned volley spreads on purpose; only a single shot homes.
                .targetActorIndex =
                    attack.projectileSpreadArcRadians > 0.0f ? std::nullopt : result.targetActorIndex,
                .homing = attack.homing,
                .critical = attack.criticalDamage,
            };
            if (attack.projectileSpreadArcRadians > 0.0f)
            {
                // A fanned volley: every projectile flies its own heading and rolls its own damage.
                const float deltaX = rangedTarget.x - rangedSource.x;
                const float deltaY = rangedTarget.y - rangedSource.y;
                const float aimYawRadians = std::atan2(deltaY, deltaX);
                const float fanDistance = std::max(512.0f, std::sqrt(deltaX * deltaX + deltaY * deltaY));
                std::uniform_int_distribution<int> damageDistribution(attack.minimumDamage, attack.maximumDamage);

                for (uint8_t projectileIndex = 0; projectileIndex < attack.projectileCount; ++projectileIndex)
                {
                    const float yawRadians = aimYawRadians + GameMechanics::projectileFanYawOffsetRadians(
                        attack.projectileCount,
                        projectileIndex,
                        attack.projectileSpreadArcRadians);
                    projectileRequest.target = toRuntimeWorldPoint(WorldPoint{
                        .x = rangedSource.x + std::cos(yawRadians) * fanDistance,
                        .y = rangedSource.y + std::sin(yawRadians) * fanDistance,
                        .z = rangedTarget.z,
                    });
                    projectileRequest.damage = damageDistribution(rng);
                    projectileRequest.critical = false;
                    attacked = config.pWorldRuntime->spawnPartyAttackProjectile(projectileRequest) || attacked;
                }
            }
            else
            {
                attacked = config.pWorldRuntime->spawnPartyAttackProjectile(projectileRequest);

                for (uint8_t projectileIndex = 1; projectileIndex < attack.projectileCount; ++projectileIndex)
                {
                    const WorldPoint secondSource = offsetPartyProjectileSourceForMember(
                        config,
                        rangedTarget,
                        actingMemberIndex + projectileIndex,
                        party.members().size() + attack.projectileCount - 1);
                    projectileRequest.source = toRuntimeWorldPoint(secondSource);
                    attacked = config.pWorldRuntime->spawnPartyAttackProjectile(projectileRequest) || attacked;
                }
            }
        }

        actionPerformed = attacked;
    }

    if (actionPerformed)
    {
        const EquipmentSlot weaponSlot = attack.mode == CharacterAttackMode::Melee
            ? EquipmentSlot::MainHand
            : EquipmentSlot::Bow;
        EquippedItemRuntimeState *pWeaponRuntime = party.equippedItemRuntimeMutable(actingMemberIndex, weaponSlot);
        bool equippedStateChanged = false;

        if (pWeaponRuntime != nullptr
            && !pWeaponRuntime->broken
            && pAttacker->equippedItemEffectFlags.contains("BreakAfterFirstAttack"))
        {
            pWeaponRuntime->broken = true;
            equippedStateChanged = true;
        }

        if (pWeaponRuntime != nullptr
            && !pWeaponRuntime->broken
            && pAttacker->equippedItemEffectFlags.contains("BreakChance2SelfDamage")
            && std::uniform_int_distribution<int>(0, 99)(rng) < 2)
        {
            pWeaponRuntime->broken = true;
            party.applyDamageToMember(
                actingMemberIndex,
                std::max(1, pAttacker->maxHealth / 10),
                Engine::tr("The weapon backfires"));
            equippedStateChanged = true;
        }

        if (attack.hit
            && !attack.stunTarget
            && pAttacker->equippedItemEffectFlags.contains("SelfKnockoutOnFailedStun70")
            && std::uniform_int_distribution<int>(0, 99)(rng) < 70)
        {
            party.applyMemberCondition(actingMemberIndex, CharacterCondition::Unconscious);
        }

        if (equippedStateChanged)
        {
            party.refreshDerivedState();
        }

        playPartyAttackSound(config, *pAttacker, attack);

        if (config.pRuntime != nullptr && config.pRuntime->turnBasedCombatRuntime().active())
        {
            config.pRuntime->turnBasedCombatRuntime().storeMemberTurnRecovery(
                actingMemberIndex,
                attack.recoverySeconds);
        }
        else
        {
            party.applyRecoveryToActiveMember(attack.recoverySeconds);
            party.switchToNextReadyMember();
        }
    }

    std::string targetName;

    if (!(attack.mode == CharacterAttackMode::Melee && !targetInMeleeRange) && target)
    {
        targetName = !config.directTargetName.empty() ? config.directTargetName : target->displayName;
    }

    GameplayCombatController::handlePartyAttackPresentation(
        config.pRuntime,
        GameplayCombatController::PartyAttackPresentation{
            .memberIndex = actingMemberIndex,
            .attackerName = pAttacker->name,
            .targetName = targetName,
            .attack = attack,
            .appliedDamage = appliedMeleeDamage,
            .actionPerformed = actionPerformed,
            .attacked = attacked,
            .hadMeleeTarget = hadMeleeTarget,
            .killed = killed,
            .targetStrongEnemy = target.has_value() && target->maxHp >= 100,
            .sparring = sparringTarget,
        });

    if (config.pWorldRuntime != nullptr)
    {
        config.pWorldRuntime->recordPartyAttackWorldResult(result.targetActorIndex, attacked, actionPerformed);
    }

    result.actionPerformed = actionPerformed;
    result.attacked = attacked;
    result.killed = killed;
    result.attack = attack;
    return result;
}

GameplayActionController::PartyAttackExecutionResult GameplayActionController::executePartyAttack(
    const PartyAttackConfig &config)
{
    PartyAttackExecutionResult result = executeActiveCombatantAttack(config);

    if (!result.held
        || config.pParty == nullptr
        || (config.pRuntime != nullptr && config.pRuntime->turnBasedCombatRuntime().active()))
    {
        return result;
    }

    // Real time: the holder stays ready and the press goes to the next ready combatant, each tried once.
    Party &party = *config.pParty;
    const size_t holder = party.activeCombatantIndex();
    std::vector<bool> tried(party.combatantCount(), false);

    if (holder < tried.size())
    {
        tried[holder] = true;
    }

    while (party.switchToNextReadyMember())
    {
        const size_t next = party.activeCombatantIndex();

        if (next >= tried.size() || tried[next])
        {
            break;
        }

        tried[next] = true;
        const PartyAttackExecutionResult nextResult = executeActiveCombatantAttack(config);

        if (!nextResult.held)
        {
            return nextResult;
        }
    }

    // Everyone ready holds: the selection stays with the first holder, and a fresh press says so.
    party.setActiveCombatantIndex(holder);

    if (config.pressedThisFrame && config.pRuntime != nullptr)
    {
        if (const Character *pHolder = party.member(result.actingMemberIndex))
        {
            config.pRuntime->setStatusBarEvent(Engine::tr("{member} holds", {{"member", pHolder->name}}));
        }
    }

    return result;
}

bool GameplayActionController::tryUnstuckParty(
    Party &party,
    IGameplayWorldRuntime &worldRuntime,
    std::string &statusText)
{
    const std::optional<float> lift = party.rules().classes.unstuckLift(worldRuntime.gameMinutes());

    if (!lift)
    {
        statusText = Engine::tr("You can't do that yet");
        return false;
    }

    return worldRuntime.liftParty(*lift);
}

std::optional<std::string> GameplayActionController::tryPartyCharge(
    Party &party,
    IGameplayWorldRuntime &worldRuntime,
    std::optional<size_t> targetActorIndex)
{
    return party.rules().classes.partyCharge(party, worldRuntime, targetActorIndex);
}

GameplayActionController::GatherLootResult GameplayActionController::gatherLoot(
    Party &party,
    IGameplayWorldRuntime &worldRuntime)
{
    const ItemRules &items = party.rules().items;
    const std::optional<LootGathering> gathering = items.lootGathering();
    GatherLootResult result = {};

    if (!gathering)
    {
        return result;
    }

    // A completed map has nothing left to fight for its loot: the satchels empty straight into the bags, and only
    // what did not fit is gathered.
    const std::optional<RulesetMapProgress> progress = party.rules().monsters.mapProgress(worldRuntime);

    if (progress && progress->complete && progress->kind != RulesetMapProgress::Kind::Arena)
    {
        result.summary = lootAllCorpses(worldRuntime, party);
    }

    const size_t corpses = worldRuntime.gatherCorpsesToParty(gathering->corpses);
    const size_t gathered = worldRuntime.gatherWorldItemsToParty(gathering->items,
        [&items](const InventoryItem &item)
        {
            return items.gathersItem(item);
        });
    // English says "monsters" and "crafting items" for every count; a language gives its own forms.
    const std::string corpseText =
        Engine::trn("{count} monsters", "{count} monsters", uint64_t(corpses), {{"count", uint64_t(corpses)}});
    const std::string itemText = Engine::trn(
        "{count} crafting items", "{count} crafting items", uint64_t(gathered), {{"count", uint64_t(gathered)}});
    result.statusText = gathered == 0 ? Engine::tr("Teleported {monsters}", {{"monsters", corpseText}})
        : corpses == 0               ? Engine::tr("Teleported {items}", {{"items", itemText}})
                                     : Engine::tr("Teleported {monsters} and {items}",
                                         {{"monsters", corpseText}, {"items", itemText}});
    return result;
}
} // namespace OpenYAMM::Game
