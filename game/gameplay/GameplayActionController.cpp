#include "game/gameplay/GameplayActionController.h"

#include "game/audio/GameAudioSystem.h"
#include "game/gameplay/CorpseLootRuntime.h"
#include "game/gameplay/GameplayActorHitFeedback.h"
#include "game/gameplay/GameplayFxService.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplaySpellService.h"
#include "game/gameplay/MeleeContactEffects.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
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
    input.elements = meleeWeaponElementsFor(ItemEnchantRuntime::characterAttackElementalDamageBonuses(
        attacker,
        CharacterAttackMode::Melee,
        config.pItemTable,
        config.pSpecialItemEnchantTable));
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
    int &elementalDamage)
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
    ElementalDamageBonuses additionalDamage = attack.rulesWeaponElements
        ? ElementalDamageBonuses{}
        : ItemEnchantRuntime::characterAttackElementalDamageBonuses(
              attacker,
              CharacterAttackMode::Melee,
              config.pItemTable,
              config.pSpecialItemEnchantTable);
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
    return gameRulesFor(config.pParty).combat.damageToMonster(hit);
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

// An attacker who no longer knows their attack spell, lacks its mana or the rules' other means (an Assassin's combo
// points) swings or shoots their weapon instead, as a quick cast does.
bool cannotCastAttackSpell(
    const GameplayActionController::PartyAttackConfig &config,
    size_t attackerMemberIndex,
    const Character &attacker)
{
    if (config.pParty == nullptr || config.pSpellTable == nullptr)
    {
        return false;
    }

    const SpellEntry *pSpellEntry = config.pSpellTable->findByName(attacker.attackSpellName, spellKnownBy(attacker));

    if (pSpellEntry == nullptr)
    {
        return false;
    }

    const uint32_t spellId = uint32_t(pSpellEntry->id);

    if (!attacker.knowsSpell(spellId))
    {
        return true;
    }

    const std::optional<uint32_t> manaCost =
        PartySpellSystem::manaCost(*config.pParty, attacker, *config.pSpellTable, spellId);
    return (manaCost && !config.pParty->canSpendSpellPoints(attackerMemberIndex, int(*manaCost)))
        || config.pParty->rules().spells.castRefusal(*config.pParty, attackerMemberIndex, spellId).has_value();
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
        config.quickCastPressed
        && quickSpellState.castLatch
        && (quickSpellState.castRepeatCooldownSeconds <= 0.0f || readyMemberTransitionWhileHeld);

    if (pressedThisFrame || repeatReady)
    {
        quickSpellState.attackFallbackRequested = false;
        quickSpellState.castLatch = true;
        quickSpellState.castRepeatCooldownSeconds = HeldActionRepeatDebounceSeconds;
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
        (config.attackPressed || attackTriggeredByQuickCastFallback)
        && attackActionState.inspectLatch
        && (attackActionState.inspectRepeatCooldownSeconds <= 0.0f || readyMemberTransitionWhileHeld);

    quickSpellState.attackFallbackRequested = false;

    if (pressedThisFrame || repeatReady)
    {
        attackActionState.inspectLatch = true;
        attackActionState.inspectRepeatCooldownSeconds = HeldActionRepeatDebounceSeconds;

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

GameplayActionController::PartyAttackExecutionResult GameplayActionController::executePartyAttack(
    const PartyAttackConfig &config)
{
    PartyAttackExecutionResult result = {};

    if (config.pParty == nullptr)
    {
        return result;
    }

    Party &party = *config.pParty;
    Character *pAttacker = party.activeMember();

    if ((pAttacker == nullptr || !GameMechanics::canTakeGameplayAction(*pAttacker))
        && party.switchToNextReadyMember())
    {
        pAttacker = party.activeMember();
    }

    if (pAttacker == nullptr || !GameMechanics::canTakeGameplayAction(*pAttacker))
    {
        return result;
    }

    const size_t actingMemberIndex = party.activeMemberIndex();
    result.attempted = true;
    result.actingMemberIndex = actingMemberIndex;
    if (party.hasPartyBuff(PartyBuffId::Invisibility))
    {
        party.clearPartyBuff(PartyBuffId::Invisibility);
    }

    if (!pAttacker->attackSpellName.empty() && !cannotCastAttackSpell(config, actingMemberIndex, *pAttacker))
    {
        AttackCastResult attackCastResult = {};
        bool noSpellTarget = false;

        if (config.pRuntime != nullptr && config.pSpellService != nullptr)
        {
            GameplaySpellActionController::TargetQueries targetQueries = config.targetQueries;
            targetQueries.preferredActorIndex = config.directTargetActorIndex;
            const GameplaySpellActionController::AttackCastResult spellAttackCastResult =
                GameplaySpellActionController::tryBeginAttackCast(
                    *config.pRuntime,
                    *config.pSpellService,
                    actingMemberIndex,
                    pAttacker->attackSpellName,
                    targetQueries);
            attackCastResult.castStarted =
                spellAttackCastResult.disposition
                == GameplaySpellActionController::AttackCastDisposition::CastStarted;
            attackCastResult.followupUiActive = spellAttackCastResult.followupUiActive;
            noSpellTarget =
                spellAttackCastResult.disposition == GameplaySpellActionController::AttackCastDisposition::NoTarget;
        }

        if (attackCastResult.castStarted
            && !attackCastResult.followupUiActive
            && (config.pRuntime == nullptr || !config.pRuntime->turnBasedCombatRuntime().active()))
        {
            party.switchToNextReadyMember();
        }

        // An attack spell with nothing to aim at swings the weapon instead, as an unaffordable one does.
        if (!noSpellTarget)
        {
            return result;
        }

        // Except a spell for a party member (Heal, a cure) when nobody needs it: no blow or arrow either (OY-190).
        const SpellEntry *pSpellEntry = config.pSpellTable != nullptr
            ? config.pSpellTable->findByName(pAttacker->attackSpellName, spellKnownBy(*pAttacker))
            : nullptr;
        const std::optional<PartySpellDescriptor> descriptor = pSpellEntry != nullptr
            ? PartySpellSystem::describeSpell(uint32_t(pSpellEntry->id))
            : std::nullopt;

        if (descriptor && descriptor->targetKind == PartySpellCastTargetKind::Character)
        {
            if (config.pRuntime != nullptr)
            {
                config.pRuntime->setStatusBarEvent("Nobody needs " + pSpellEntry->name);
            }

            return result;
        }
    }

    std::optional<PartyAttackActorFacts> target = resolveUsableActorTarget(config, config.directTargetActorIndex);

    if (!target)
    {
        target = chooseFallbackRangedTarget(config);
    }

    result.targetActorIndex = target ? std::optional<size_t>(target->actorIndex) : std::nullopt;

    const float targetDistance = target ? actorDistanceFromParty(*target, config.partyPosition) : 0.0f;
    const bool targetInMeleeRange = target.has_value() && targetDistance <= CharacterMeleeAttackDistance;
    // A world target a blow damages: a destructible BModel or face, or a destructible decoration (an entity).
    const bool bModelTargetHit = config.pWorldRuntime != nullptr
        && config.directTargetBModelIndex.has_value()
        && config.pWorldRuntime->isPartyAttackMeleeBModelTarget(*config.directTargetBModelIndex);
    const bool entityTargetHit = config.pWorldRuntime != nullptr
        && config.directTargetEntityIndex.has_value()
        && config.pWorldRuntime->isPartyAttackMeleeEntityTarget(*config.directTargetEntityIndex);
    const bool worldTargetInMeleeRange = (bModelTargetHit || entityTargetHit)
        && config.directWorldTargetDistance <= CharacterMeleeAttackDistance;
    const CharacterAttackTuning attackTuning = config.pRuntime != nullptr
        ? characterAttackTuningFromSettings(config.pRuntime->settingsSnapshot())
        : CharacterAttackTuning{};
    const CharacterAttackProfile attackProfile =
        GameMechanics::buildCharacterAttackProfile(*pAttacker, config.pItemTable, config.pSpellTable, attackTuning);
    const bool eyeUnderWater =
        config.pWorldRuntime != nullptr && config.pWorldRuntime->partyBreathFraction().has_value();
    const CharacterAttackMode attackMode = choosePartyAttackMode(attackProfile, targetInMeleeRange, eyeUnderWater);
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

        if (target
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
                "The weapon backfires");
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

bool GameplayActionController::tryUnstuckParty(
    Party &party,
    IGameplayWorldRuntime &worldRuntime,
    std::string &statusText)
{
    const std::optional<float> lift = party.rules().classes.unstuckLift(worldRuntime.gameMinutes());

    if (!lift)
    {
        statusText = "You can't do that yet";
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
    const std::string corpseText = std::to_string(corpses) + " monsters";
    const std::string itemText = std::to_string(gathered) + " crafting items";
    result.statusText =
        "Teleported " + (gathered == 0 ? corpseText : corpses == 0 ? itemText : corpseText + " and " + itemText);
    return result;
}
} // namespace OpenYAMM::Game
