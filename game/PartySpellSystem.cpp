#include "game/PartySpellSystem.h"

#include "game/GameMechanics.h"
#include "game/OutdoorPartyRuntime.h"
#include "game/OutdoorWorldRuntime.h"
#include "game/SpellIds.h"
#include "game/SpellTable.h"

#include <algorithm>
#include <array>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float OeRealtimeRecoveryScale = 2.133333333333333f;

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
    if (spellId < 1 || spellId > 99)
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

SkillMastery defaultRequiredMasteryForSpellId(uint32_t spellId)
{
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

float recoverySecondsForSpellEntry(const SpellEntry &spellEntry, SkillMastery mastery)
{
    switch (mastery)
    {
        case SkillMastery::Expert:
            return ticksToRecoverySeconds(spellEntry.expertRecoveryTicks);
        case SkillMastery::Master:
            return ticksToRecoverySeconds(spellEntry.masterRecoveryTicks);
        case SkillMastery::Grandmaster:
            return ticksToRecoverySeconds(spellEntry.grandmasterRecoveryTicks);
        case SkillMastery::Normal:
        case SkillMastery::None:
        default:
            return ticksToRecoverySeconds(spellEntry.normalRecoveryTicks);
    }
}

int manaCostForRule(const BackendSpellRule &rule, SkillMastery mastery)
{
    const int index = masteryIndex(mastery);
    return index >= 0 ? rule.manaByMastery[static_cast<size_t>(index)] : 0;
}

float recoverySecondsForRule(const BackendSpellRule &rule, SkillMastery mastery)
{
    const int index = masteryIndex(mastery);
    return index >= 0 ? ticksToRecoverySeconds(rule.recoveryTicksByMastery[static_cast<size_t>(index)]) : 0.0f;
}

float secondsFromHours(float hours)
{
    return hours * 3600.0f;
}

float secondsFromMinutes(float minutes)
{
    return minutes * 60.0f;
}

std::optional<std::string> resolveMagicSkillName(uint32_t spellId)
{
    if (spellIdInRange(spellId, SpellId::TorchLight, SpellId::Incinerate))
    {
        return "FireMagic";
    }

    if (spellIdInRange(spellId, SpellId::WizardEye, SpellId::Starburst))
    {
        return "AirMagic";
    }

    if (spellIdInRange(spellId, SpellId::Awaken, SpellId::LloydsBeacon))
    {
        return "WaterMagic";
    }

    if (spellIdInRange(spellId, SpellId::Stun, SpellId::MassDistortion))
    {
        return "EarthMagic";
    }

    if (spellIdInRange(spellId, SpellId::DetectLife, SpellId::Resurrection))
    {
        return "SpiritMagic";
    }

    if (spellIdInRange(spellId, SpellId::Telepathy, SpellId::Enslave))
    {
        return "MindMagic";
    }

    if (spellIdInRange(spellId, SpellId::CureWeakness, SpellId::PowerCure))
    {
        return "BodyMagic";
    }

    if (spellIdInRange(spellId, SpellId::LightBolt, SpellId::DivineIntervention))
    {
        return "LightMagic";
    }

    if (spellIdInRange(spellId, SpellId::Reanimate, SpellId::SoulDrinker))
    {
        return "DarkMagic";
    }

    return std::nullopt;
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

    switch (spellIdFromValue(spellId))
    {
        case SpellId::TorchLight:
            return BackendSpellRule{1, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {1, 1, 1, 1}, {60, 60, 60, 40}, PartyBuffId::TorchLight};
        case SpellId::FireBolt:
            return BackendSpellRule{2, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Normal, {2, 2, 2, 2}, {110, 110, 100, 90}, PartyBuffId::TorchLight, 0, 3, false};
        case SpellId::FireResistance:
            return BackendSpellRule{3, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {3, 3, 3, 3}, {120, 120, 120, 120}, PartyBuffId::FireResistance};
        case SpellId::Haste:
            return BackendSpellRule{5, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Expert, {5, 5, 5, 5}, {120, 120, 120, 120}, PartyBuffId::Haste};
        case SpellId::Fireball:
            return BackendSpellRule{6, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Expert, {8, 8, 8, 8}, {100, 100, 90, 80}, PartyBuffId::TorchLight, 0, 6, false};
        case SpellId::Immolation:
            return BackendSpellRule{8, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Master, {15, 15, 15, 15}, {120, 120, 120, 120}, PartyBuffId::Immolation};
        case SpellId::MeteorShower:
            return BackendSpellRule{9, PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::Projectile, SkillMastery::Master, {20, 20, 20, 20}, {100, 100, 100, 90}, PartyBuffId::TorchLight, 8, 1, true};
        case SpellId::Inferno:
            return BackendSpellRule{10, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 12, 2, true};
        case SpellId::Incinerate:
            return BackendSpellRule{11, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Grandmaster, {30, 30, 30, 30}, {90, 90, 90, 90}, PartyBuffId::TorchLight, 15, 15, false};
        case SpellId::WizardEye:
            return BackendSpellRule{12, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {1, 1, 1, 0}, {60, 60, 60, 60}, PartyBuffId::WizardEye};
        case SpellId::FeatherFall:
            return BackendSpellRule{13, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {2, 2, 2, 2}, {120, 120, 120, 100}, PartyBuffId::FeatherFall};
        case SpellId::AirResistance:
            return BackendSpellRule{14, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {3, 3, 3, 3}, {120, 120, 120, 120}, PartyBuffId::AirResistance};
        case SpellId::Sparks:
            return BackendSpellRule{15, PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::MultiProjectile, SkillMastery::Normal, {4, 4, 4, 4}, {110, 100, 90, 80}, PartyBuffId::TorchLight, 2, 1, true, sparksCount};
        case SpellId::Jump:
            return BackendSpellRule{16, PartySpellCastTargetKind::None, PartySpellCastEffectKind::Jump, SkillMastery::Expert, {5, 5, 5, 5}, {90, 90, 70, 50}, PartyBuffId::TorchLight};
        case SpellId::Shield:
            return BackendSpellRule{17, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Expert, {8, 8, 8, 8}, {120, 120, 120, 120}, PartyBuffId::Shield};
        case SpellId::LightningBolt:
            return BackendSpellRule{18, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Expert, {10, 10, 10, 10}, {100, 100, 90, 70}, PartyBuffId::TorchLight, 0, 8, false};
        case SpellId::Invisibility:
            return BackendSpellRule{19, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Master, {}, {}, PartyBuffId::Invisibility};
        case SpellId::Implosion:
            return BackendSpellRule{20, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 10, 10, false};
        case SpellId::Fly:
            return BackendSpellRule{21, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Master, {}, {}, PartyBuffId::Fly};
        case SpellId::Starburst:
            return BackendSpellRule{22, PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::Projectile, SkillMastery::Grandmaster, {}, {}, PartyBuffId::TorchLight, 20, 1, true};
        case SpellId::Awaken:
            return BackendSpellRule{23, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyRestore, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight};
        case SpellId::PoisonSpray:
            return BackendSpellRule{24, PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::MultiProjectile, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight, 2, 2, true, 3};
        case SpellId::WaterResistance:
            return BackendSpellRule{25, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {3, 3, 3, 3}, {120, 120, 120, 120}, PartyBuffId::WaterResistance};
        case SpellId::IceBolt:
            return BackendSpellRule{26, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight, 1, 4, false};
        case SpellId::WaterWalk:
            return BackendSpellRule{27, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Expert, {}, {}, PartyBuffId::WaterWalk};
        case SpellId::AcidBurst:
            return BackendSpellRule{29, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight, 9, 9, false};
        case SpellId::EnchantItem:
            return BackendSpellRule{spellId, PartySpellCastTargetKind::UtilityUi, PartySpellCastEffectKind::UtilityUi, SkillMastery::Master, {15, 15, 15, 15}, {140, 140, 140, 140}, PartyBuffId::TorchLight};
        case SpellId::TownPortal:
            return BackendSpellRule{spellId, PartySpellCastTargetKind::UtilityUi, PartySpellCastEffectKind::UtilityUi, SkillMastery::Master, {20, 20, 20, 20}, {200, 200, 200, 200}, PartyBuffId::TorchLight};
        case SpellId::LloydsBeacon:
            return BackendSpellRule{spellId, PartySpellCastTargetKind::UtilityUi, PartySpellCastEffectKind::UtilityUi, SkillMastery::Grandmaster, {30, 30, 30, 30}, {250, 250, 250, 250}, PartyBuffId::TorchLight};
        case SpellId::IceBlast:
            return BackendSpellRule{32, PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::MultiProjectile, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 12, 6, true, 7};
        case SpellId::Stun:
            return BackendSpellRule{34, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight};
        case SpellId::Slow:
            return BackendSpellRule{35, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight};
        case SpellId::EarthResistance:
            return BackendSpellRule{36, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {3, 3, 3, 3}, {120, 120, 120, 120}, PartyBuffId::EarthResistance};
        case SpellId::DeadlySwarm:
            return BackendSpellRule{37, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight, 5, 3, false};
        case SpellId::StoneSkin:
            return BackendSpellRule{38, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Expert, {5, 5, 5, 5}, {120, 120, 120, 120}, PartyBuffId::Stoneskin};
        case SpellId::Blades:
            return BackendSpellRule{39, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight, 1, 9, false};
        case SpellId::StoneToFlesh:
            return BackendSpellRule{40, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight};
        case SpellId::RockBlast:
            return BackendSpellRule{41, PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::Projectile, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 10, 10, false};
        case SpellId::DeathBlossom:
            return BackendSpellRule{43, PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::Projectile, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 20, 2, true};
        case SpellId::MassDistortion:
            return BackendSpellRule{44, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Grandmaster, {}, {}, PartyBuffId::TorchLight};
        case SpellId::DetectLife:
            return BackendSpellRule{45, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {}, {}, PartyBuffId::DetectLife};
        case SpellId::Bless:
            return BackendSpellRule{46, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterBuff, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight};
        case SpellId::Fate:
            return BackendSpellRule{47, PartySpellCastTargetKind::ActorOrCharacter, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight};
        case SpellId::TurnUndead:
            return BackendSpellRule{48, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight};
        case SpellId::RemoveCurse:
            return BackendSpellRule{49, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight};
        case SpellId::Preservation:
            return BackendSpellRule{50, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterBuff, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight};
        case SpellId::Heroism:
            return BackendSpellRule{51, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Expert, {10, 10, 10, 10}, {120, 120, 120, 120}, PartyBuffId::Heroism};
        case SpellId::SpiritLash:
            return BackendSpellRule{52, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 10, 8, false};
        case SpellId::RaiseDead:
            return BackendSpellRule{53, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight};
        case SpellId::SharedLife:
            return BackendSpellRule{54, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyRestore, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight};
        case SpellId::Resurrection:
            return BackendSpellRule{55, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Grandmaster, {}, {}, PartyBuffId::TorchLight};
        case SpellId::RemoveFear:
            return BackendSpellRule{57, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight};
        case SpellId::MindResistance:
            return BackendSpellRule{58, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {}, {}, PartyBuffId::MindResistance};
        case SpellId::MindBlast:
            return BackendSpellRule{59, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight, 3, 3, false};
        case SpellId::Charm:
            return BackendSpellRule{60, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight};
        case SpellId::CureParalysis:
            return BackendSpellRule{61, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight};
        case SpellId::Berserk:
            return BackendSpellRule{62, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight};
        case SpellId::MassFear:
            return BackendSpellRule{63, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight};
        case SpellId::CureInsanity:
            return BackendSpellRule{64, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight};
        case SpellId::PsychicShock:
            return BackendSpellRule{65, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 12, 12, false};
        case SpellId::Enslave:
            return BackendSpellRule{66, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Grandmaster, {}, {}, PartyBuffId::TorchLight};
        case SpellId::CureWeakness:
            return BackendSpellRule{67, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight};
        case SpellId::Heal:
            return BackendSpellRule{68, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight};
        case SpellId::BodyResistance:
            return BackendSpellRule{69, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Normal, {3, 3, 3, 3}, {120, 120, 120, 120}, PartyBuffId::BodyResistance};
        case SpellId::Harm:
            return BackendSpellRule{70, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight, 8, 2, false};
        case SpellId::Regeneration:
            return BackendSpellRule{71, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterBuff, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight};
        case SpellId::CurePoison:
            return BackendSpellRule{72, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight};
        case SpellId::Hammerhands:
            return BackendSpellRule{73, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterBuff, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight};
        case SpellId::CureDisease:
            return BackendSpellRule{74, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterRestore, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight};
        case SpellId::ProtectionFromMagic:
            return BackendSpellRule{75, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Master, {20, 20, 20, 20}, {120, 120, 120, 120}, PartyBuffId::ProtectionFromMagic};
        case SpellId::FlyingFist:
            return BackendSpellRule{76, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Master, {25, 25, 25, 25}, {110, 110, 110, 100}, PartyBuffId::TorchLight, 30, 5, false};
        case SpellId::PowerCure:
            return BackendSpellRule{77, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyRestore, SkillMastery::Grandmaster, {}, {}, PartyBuffId::TorchLight};
        case SpellId::LightBolt:
            return BackendSpellRule{78, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Normal, {5, 5, 5, 5}, {110, 100, 90, 80}, PartyBuffId::TorchLight, 0, 4, false};
        case SpellId::DestroyUndead:
            return BackendSpellRule{79, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight, 16, 16, false};
        case SpellId::DispelMagic:
            return BackendSpellRule{80, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight};
        case SpellId::Paralyze:
            return BackendSpellRule{81, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight};
        case SpellId::DayOfGods:
            return BackendSpellRule{83, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Expert, {30, 30, 30, 30}, {500, 500, 500, 500}, PartyBuffId::DayOfGods};
        case SpellId::PrismaticLight:
            return BackendSpellRule{84, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 25, 1, true};
        case SpellId::DayOfProtection:
            return BackendSpellRule{85, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Master, {40, 40, 40, 40}, {500, 500, 500, 500}, PartyBuffId::BodyResistance};
        case SpellId::HourOfPower:
            return BackendSpellRule{86, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyBuff, SkillMastery::Master, {45, 45, 45, 45}, {250, 250, 250, 250}, PartyBuffId::Heroism};
        case SpellId::Sunray:
            return BackendSpellRule{87, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 20, 20, false};
        case SpellId::DivineIntervention:
            return BackendSpellRule{88, PartySpellCastTargetKind::None, PartySpellCastEffectKind::PartyRestore, SkillMastery::Grandmaster, {}, {}, PartyBuffId::TorchLight};
        case SpellId::Reanimate:
            return BackendSpellRule{89, PartySpellCastTargetKind::ActorOrCharacter, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight};
        case SpellId::ToxicCloud:
            return BackendSpellRule{90, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight, 25, 10, false};
        case SpellId::ShrinkingRay:
            return BackendSpellRule{92, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Normal, {}, {}, PartyBuffId::TorchLight};
        case SpellId::Shrapmetal:
            return BackendSpellRule{93, PartySpellCastTargetKind::GroundPoint, PartySpellCastEffectKind::MultiProjectile, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight, 1, 6, true, 5};
        case SpellId::ControlUndead:
            return BackendSpellRule{94, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight};
        case SpellId::PainReflection:
            return BackendSpellRule{95, PartySpellCastTargetKind::Character, PartySpellCastEffectKind::CharacterBuff, SkillMastery::Expert, {}, {}, PartyBuffId::TorchLight};
        case SpellId::DarkGrasp:
            return BackendSpellRule{96, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::ActorEffect, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight};
        case SpellId::DragonBreath:
            return BackendSpellRule{97, PartySpellCastTargetKind::Actor, PartySpellCastEffectKind::Projectile, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 1, 25, false};
        case SpellId::Armageddon:
            return BackendSpellRule{98, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Master, {}, {}, PartyBuffId::TorchLight, 50, 1, false};
        case SpellId::SoulDrinker:
            return BackendSpellRule{99, PartySpellCastTargetKind::None, PartySpellCastEffectKind::AreaEffect, SkillMastery::Grandmaster, {}, {}, PartyBuffId::TorchLight, 25, 8, false};
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

    skillLevel = pSkill->level;
    skillMastery = pSkill->mastery;
    return skillLevel > 0;
}

bx::Vec3 resolveActorTargetPoint(const OutdoorWorldRuntime::MapActorState &actor)
{
    return {
        actor.preciseX,
        actor.preciseY,
        actor.preciseZ + std::max(48.0f, static_cast<float>(actor.height) * 0.6f)
    };
}

int rollSpellDamage(const BackendSpellRule &rule, uint32_t skillLevel)
{
    if (skillLevel == 0)
    {
        return std::max(0, rule.baseDamage);
    }

    if (rule.damageScalesLinearly)
    {
        return std::max(0, rule.baseDamage + rule.bonusSkillDamage * static_cast<int>(skillLevel));
    }

    return std::max(0, rule.baseDamage + static_cast<int>(skillLevel) * std::max(1, rule.bonusSkillDamage));
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
            party.applyPartyBuff(PartyBuffId::Haste, hasteDurationSeconds, 0, spellId, skillLevel, mastery, casterMemberIndex);
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
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * skillLevel))
                : secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * skillLevel));
        case SpellId::Regeneration:
        case SpellId::Hammerhands:
            return secondsFromHours(static_cast<float>(std::max<uint32_t>(1, skillLevel)));
        case SpellId::PainReflection:
            return mastery == SkillMastery::Grandmaster
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * skillLevel))
                : secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel));
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
        case SpellId::Regeneration:
            return mastery == SkillMastery::Grandmaster
                ? 4
                : mastery == SkillMastery::Master
                ? 3
                : 2;
        case SpellId::Hammerhands:
        case SpellId::PainReflection:
            return static_cast<int>(skillLevel);
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
    OutdoorPartyRuntime &partyRuntime,
    OutdoorWorldRuntime &worldRuntime,
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
            "Spell failed");
    }

    const SpellEntry *pSpellEntry = spellTable.findById(static_cast<int>(request.spellId));

    if (pSpellEntry == nullptr)
    {
        return makeFailure(
            request.spellId,
            PartySpellCastStatus::InvalidSpell,
            PartySpellCastTargetKind::None,
            PartySpellCastEffectKind::Unsupported,
            "Spell failed");
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
            "Spell failed");
    }

    const std::optional<BackendSpellRule> rule = resolveBackendSpellRule(request.spellId, skillMastery);

    if (!rule)
    {
        return makeFailure(
            request.spellId,
            PartySpellCastStatus::Unsupported,
            PartySpellCastTargetKind::None,
            PartySpellCastEffectKind::Unsupported,
            "Spell failed");
    }

    result.targetKind = rule->targetKind;
    result.effectKind = rule->effectKind;
    result.skillLevel = skillLevel;
    result.skillMastery = skillMastery;

    const SkillMastery requiredMastery =
        rule->requiredMastery != SkillMastery::None
            ? rule->requiredMastery
            : defaultRequiredMasteryForSpellId(request.spellId);

    if (skillMastery < requiredMastery)
    {
        return makeFailure(
            request.spellId,
            PartySpellCastStatus::NotSkilledEnough,
            rule->targetKind,
            rule->effectKind,
            "Spell failed");
    }

    result.manaCost = static_cast<uint32_t>(std::max(
        0,
        ruleHasExplicitManaCost(*rule)
            ? manaCostForRule(*rule, skillMastery)
            : defaultManaCostForSpellId(request.spellId)));
    result.recoverySeconds =
        ruleHasExplicitRecovery(*rule)
            ? recoverySecondsForRule(*rule, skillMastery)
            : recoverySecondsForSpellEntry(*pSpellEntry, skillMastery);

    if (request.spendMana && !party.canSpendSpellPoints(request.casterMemberIndex, static_cast<int>(result.manaCost)))
    {
        return makeFailure(
            request.spellId,
            PartySpellCastStatus::NotEnoughSpellPoints,
            rule->targetKind,
            rule->effectKind,
            "Not enough spell points");
    }

    bx::Vec3 targetPoint = {0.0f, 0.0f, 0.0f};

    if (rule->targetKind == PartySpellCastTargetKind::Actor)
    {
        if (!request.targetActorIndex)
        {
            return makeFailure(
                request.spellId,
                PartySpellCastStatus::NeedActorTarget,
                rule->targetKind,
                rule->effectKind,
                "Need actor target");
        }

        const OutdoorWorldRuntime::MapActorState *pActor = worldRuntime.mapActorState(*request.targetActorIndex);

        if (pActor == nullptr || pActor->isDead || pActor->isInvisible)
        {
            return makeFailure(
                request.spellId,
                PartySpellCastStatus::Failed,
                rule->targetKind,
                rule->effectKind,
                "Spell failed");
        }

        targetPoint = resolveActorTargetPoint(*pActor);
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
        const bool hasActorTarget =
            request.targetActorIndex && worldRuntime.mapActorState(*request.targetActorIndex) != nullptr;
        const bool hasCharacterTarget =
            request.targetCharacterIndex && party.member(*request.targetCharacterIndex) != nullptr;

        if (!hasActorTarget && !hasCharacterTarget)
        {
            return makeFailure(
                request.spellId,
                PartySpellCastStatus::NeedActorOrCharacterTarget,
                rule->targetKind,
                rule->effectKind,
                "Need spell target");
        }

        if (hasActorTarget)
        {
            const OutdoorWorldRuntime::MapActorState *pActor = worldRuntime.mapActorState(*request.targetActorIndex);

            if (pActor != nullptr)
            {
                targetPoint = resolveActorTargetPoint(*pActor);
            }
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
                "Need ground target");
        }

        targetPoint = {request.targetX, request.targetY, request.targetZ};
    }
    else if (rule->targetKind == PartySpellCastTargetKind::UtilityUi)
    {
        return makeFailure(
            request.spellId,
            PartySpellCastStatus::NeedUtilityUi,
            rule->targetKind,
            rule->effectKind,
            "Need spell UI");
    }

    bool castSucceeded = false;
    const OutdoorMoveState &moveState = partyRuntime.movementState();
    const float sourceX = moveState.x;
    const float sourceY = moveState.y;
    const float sourceZ = moveState.footZ + 96.0f;
    const std::string &spellName = pSpellEntry->normalizedName;
    const SpellId spellId = spellIdFromValue(request.spellId);

    if (rule->effectKind == PartySpellCastEffectKind::PartyBuff)
    {
        const float durationSeconds = resolvePartyBuffDurationSeconds(request.spellId, skillLevel, skillMastery);
        const int power = resolvePartyBuffPower(request.spellId, skillLevel, skillMastery);

        if (spellId == SpellId::DayOfProtection || spellId == SpellId::HourOfPower)
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

        partyRuntime.syncSpellMovementStatesFromPartyBuffs();
        castSucceeded = true;
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
                castSucceeded = worldRuntime.applyPartySpellToMapActor(
                    *request.targetActorIndex,
                    request.spellId,
                    skillLevel,
                    skillMastery,
                    power,
                    sourceX,
                    sourceY,
                    moveState.footZ);
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
            castSucceeded = party.healMember(*request.targetCharacterIndex, healAmount);
        }
        else
        {
            castSucceeded = applyCharacterRestoreSpell(
                party,
                request.spellId,
                *request.targetCharacterIndex,
                skillLevel);
        }
    }
    else if (rule->effectKind == PartySpellCastEffectKind::PartyRestore)
    {
        if (spellId == SpellId::Awaken)
        {
            castSucceeded = false;

            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                castSucceeded =
                    party.clearMemberCondition(memberIndex, CharacterCondition::Asleep) || castSucceeded;
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
                castSucceeded = party.healMember(memberIndex, share) || castSucceeded;
            }
        }
        else if (spellId == SpellId::PowerCure)
        {
            const int healAmount = 10 + static_cast<int>(5 * skillLevel);

            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                castSucceeded = party.healMember(memberIndex, healAmount) || castSucceeded;
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
                castSucceeded = true;
            }
        }
    }
    else if (rule->effectKind == PartySpellCastEffectKind::Jump)
    {
        partyRuntime.requestJump();
        castSucceeded = true;
    }
    else if (rule->effectKind == PartySpellCastEffectKind::Projectile)
    {
        OutdoorWorldRuntime::SpellCastRequest worldRequest = {};
        worldRequest.sourceKind = OutdoorWorldRuntime::RuntimeSpellSourceKind::Party;
        worldRequest.sourceId = static_cast<uint32_t>(request.casterMemberIndex + 1);
        worldRequest.sourcePartyMemberIndex = static_cast<uint32_t>(request.casterMemberIndex);
        worldRequest.ability = OutdoorWorldRuntime::MonsterAttackAbility::Spell1;
        worldRequest.spellId = request.spellId;
        worldRequest.skillLevel = skillLevel;
        worldRequest.skillMastery = static_cast<uint32_t>(skillMastery);
        worldRequest.damage = rollSpellDamage(*rule, skillLevel);
        worldRequest.attackBonus = 0;
        worldRequest.useActorHitChance = spellName != "lightning bolt" && spellName != "acid burst";
        worldRequest.sourceX = sourceX;
        worldRequest.sourceY = sourceY;
        worldRequest.sourceZ = sourceZ;
        worldRequest.targetX = targetPoint.x;
        worldRequest.targetY = targetPoint.y;
        worldRequest.targetZ = targetPoint.z;
            castSucceeded = worldRuntime.castPartySpell(worldRequest);
    }
    else if (rule->effectKind == PartySpellCastEffectKind::MultiProjectile)
    {
        const float targetAngleRadians = std::atan2(sourceY - targetPoint.y, targetPoint.x - sourceX);
        const float distance = std::sqrt(
            (targetPoint.x - sourceX) * (targetPoint.x - sourceX)
            + (targetPoint.y - sourceY) * (targetPoint.y - sourceY));
        const float baseTargetZ = targetPoint.z;
        const float spreadStartRadians = -0.45f;
        const float spreadStepRadians =
            rule->multiProjectileCount > 1 ? 0.9f / static_cast<float>(rule->multiProjectileCount - 1) : 0.0f;

        for (uint32_t projectileIndex = 0; projectileIndex < rule->multiProjectileCount; ++projectileIndex)
        {
            const float yawRadians =
                targetAngleRadians + spreadStartRadians + spreadStepRadians * static_cast<float>(projectileIndex);
            OutdoorWorldRuntime::SpellCastRequest worldRequest = {};
            worldRequest.sourceKind = OutdoorWorldRuntime::RuntimeSpellSourceKind::Party;
            worldRequest.sourceId = static_cast<uint32_t>(request.casterMemberIndex + 1);
            worldRequest.sourcePartyMemberIndex = static_cast<uint32_t>(request.casterMemberIndex);
            worldRequest.ability = OutdoorWorldRuntime::MonsterAttackAbility::Spell1;
            worldRequest.spellId = request.spellId;
            worldRequest.skillLevel = skillLevel;
            worldRequest.skillMastery = static_cast<uint32_t>(skillMastery);
            worldRequest.damage = rollSpellDamage(*rule, skillLevel);
            worldRequest.attackBonus = 0;
            worldRequest.useActorHitChance = true;
            worldRequest.sourceX = sourceX;
            worldRequest.sourceY = sourceY;
            worldRequest.sourceZ = sourceZ;
            worldRequest.targetX = sourceX + std::cos(yawRadians) * std::max(512.0f, distance);
            worldRequest.targetY = sourceY - std::sin(yawRadians) * std::max(512.0f, distance);
            worldRequest.targetZ = baseTargetZ;
            castSucceeded = worldRuntime.castPartySpell(worldRequest) || castSucceeded;
        }
    }
    else if (rule->effectKind == PartySpellCastEffectKind::ActorEffect)
    {
        if (spellId == SpellId::Sunray && (worldRuntime.currentHour() < 5 || worldRuntime.currentHour() >= 21))
        {
            return makeFailure(request.spellId, PartySpellCastStatus::Failed, rule->targetKind, rule->effectKind, "Spell failed");
        }

        if (request.targetActorIndex)
        {
            castSucceeded = worldRuntime.applyPartySpellToMapActor(
                *request.targetActorIndex,
                request.spellId,
                skillLevel,
                skillMastery,
                rollSpellDamage(*rule, skillLevel),
                sourceX,
                sourceY,
                moveState.footZ);
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
            }
            else if (spellId == SpellId::Reanimate)
            {
                castSucceeded = party.reviveMember(
                    *request.targetCharacterIndex,
                    std::max(1, static_cast<int>(skillLevel) * 20),
                    false);
            }
        }
    }
    else if (rule->effectKind == PartySpellCastEffectKind::AreaEffect)
    {
        const bool outdoorsOnly =
            spellId == SpellId::MeteorShower
            || spellId == SpellId::Starburst
            || spellId == SpellId::DeathBlossom
            || spellId == SpellId::Sunray
            || spellId == SpellId::Armageddon;
        const bool indoorsOnly = spellId == SpellId::Inferno || spellId == SpellId::PrismaticLight;
        const bool daylightOnly = spellId == SpellId::Sunray;

        if (indoorsOnly)
        {
            return makeFailure(request.spellId, PartySpellCastStatus::Failed, rule->targetKind, rule->effectKind, "Spell failed");
        }

        if (daylightOnly && (worldRuntime.currentHour() < 5 || worldRuntime.currentHour() >= 21))
        {
            return makeFailure(request.spellId, PartySpellCastStatus::Failed, rule->targetKind, rule->effectKind, "Spell failed");
        }

        const float effectRadius =
            spellId == SpellId::SpiritLash
                ? 768.0f
                : spellId == SpellId::Armageddon
                ? 8192.0f
                : 4096.0f;
        const std::vector<size_t> actorIndices = worldRuntime.collectMapActorIndicesWithinRadius(
            sourceX,
            sourceY,
            moveState.footZ + 64.0f,
            effectRadius,
            spellId != SpellId::Armageddon,
            sourceX,
            sourceY,
            sourceZ);

        for (size_t actorIndex : actorIndices)
        {
            const OutdoorWorldRuntime::MapActorState *pActor = worldRuntime.mapActorState(actorIndex);

            if (pActor == nullptr || !pActor->hostileToParty)
            {
                continue;
            }

            castSucceeded = worldRuntime.applyPartySpellToMapActor(
                actorIndex,
                request.spellId,
                skillLevel,
                skillMastery,
                rollSpellDamage(*rule, skillLevel),
                sourceX,
                sourceY,
                moveState.footZ)
                || castSucceeded;
        }

        if (spellId == SpellId::SoulDrinker && castSucceeded)
        {
            const int healAmount = 25 + static_cast<int>(7 * skillLevel);

            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                party.healMember(memberIndex, healAmount);
            }
        }
        else if (spellId == SpellId::Armageddon)
        {
            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                Character *pMember = party.member(memberIndex);

                if (pMember != nullptr)
                {
                    pMember->health = std::max(0, pMember->health - (50 + static_cast<int>(skillLevel)));
                }
            }

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

        static_cast<void>(outdoorsOnly);
    }

    if (!castSucceeded)
    {
        return makeFailure(
            request.spellId,
            PartySpellCastStatus::Failed,
            rule->targetKind,
            rule->effectKind,
            "Spell failed");
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
}
