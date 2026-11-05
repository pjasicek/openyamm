#include "game/gameplay/GameplayCombatController.h"

#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/GameplayBolsterRuntime.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/rules/GameRules.h"
#include "game/tables/ItemTable.h"
#include "game/tables/SpellTable.h"

#include <algorithm>
#include <cmath>
#include <iterator>
#include <limits>
#include <random>
#include <sstream>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t KillSpeechChancePercent = 20;
constexpr float OeRealtimeRecoveryScale = 2.133333333333333f;
constexpr uint32_t FirstRegularBreakableItemId = 1;
constexpr uint32_t LastRegularBreakableItemId = 134;

struct DamagedMember
{
    size_t memberIndex = 0;
    int damage = 0;
};

struct BreakItemCandidate
{
    InventoryItem *pInventoryItem = nullptr;
    EquippedItemRuntimeState *pEquippedRuntime = nullptr;
    const ItemDefinition *pItemDefinition = nullptr;
};

struct MonsterImpactHitCheck
{
    bool hit = false;
    int baseArmorClass = 0;
    int adjustedArmorClass = 0;
    int monsterLevel = 0;
    int attackBonus = 0;
    bool bolsterAffectsArmorClass = false;
};

constexpr EquipmentSlot BreakItemEquipmentSlots[] = {
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

std::optional<GameplayCombatActorInfo> resolveActor(
    const GameplayCombatController::PendingCombatEventContext &context,
    uint32_t actorId)
{
    if (context.pWorldRuntime == nullptr)
    {
        return std::nullopt;
    }

    return context.pWorldRuntime->combatActorInfoById(actorId);
}

const char *boolText(bool value)
{
    return value ? "true" : "false";
}

const char *combatDamageTypeName(CombatDamageType damageType)
{
    switch (damageType)
    {
        case CombatDamageType::Physical: return "physical";
        case CombatDamageType::Fire: return "fire";
        case CombatDamageType::Air: return "air";
        case CombatDamageType::Water: return "water";
        case CombatDamageType::Earth: return "earth";
        case CombatDamageType::Spirit: return "spirit";
        case CombatDamageType::Mind: return "mind";
        case CombatDamageType::Body: return "body";
        case CombatDamageType::Light: return "light";
        case CombatDamageType::Dark: return "dark";
        case CombatDamageType::Energy: return "energy";
        case CombatDamageType::Irresistible: return "irresistible";
    }

    return "unknown";
}

const char *actorAbilityName(GameplayActorAttackAbility ability)
{
    switch (ability)
    {
        case GameplayActorAttackAbility::Attack1: return "attack1";
        case GameplayActorAttackAbility::Attack2: return "attack2";
        case GameplayActorAttackAbility::Spell1: return "spell1";
        case GameplayActorAttackAbility::Spell2: return "spell2";
    }

    return "unknown";
}

const char *combatEventTypeName(GameplayCombatController::CombatEventType type)
{
    switch (type)
    {
        case GameplayCombatController::CombatEventType::MonsterMeleeImpact: return "monster_melee_impact";
        case GameplayCombatController::CombatEventType::MonsterRangedRelease: return "monster_ranged_release";
        case GameplayCombatController::CombatEventType::PartyProjectileImpact: return "party_projectile_impact";
        case GameplayCombatController::CombatEventType::PartyProjectileActorImpact:
            return "party_projectile_actor_impact";
    }

    return "unknown";
}

const char *characterAttackModeName(CharacterAttackMode mode)
{
    switch (mode)
    {
        case CharacterAttackMode::None: return "none";
        case CharacterAttackMode::Melee: return "melee";
        case CharacterAttackMode::Bow: return "bow";
        case CharacterAttackMode::Wand: return "wand";
        case CharacterAttackMode::Blaster: return "blaster";
        case CharacterAttackMode::DragonBreath: return "dragon_breath";
    }

    return "unknown";
}

void appendCombatEventSummary(std::ostream &out, const GameplayCombatController::CombatEvent &event)
{
    out << " event_type=" << combatEventTypeName(event.type)
        << " source_id=" << event.sourceId
        << " source_party_member_index=" << event.sourcePartyMemberIndex
        << " target_actor_id=" << event.targetActorId
        << " input_damage=" << event.damage
        << " attack_bonus=" << event.attackBonus
        << " spell_id=" << event.spellId
        << " damage_type=" << combatDamageTypeName(event.damageType)
        << " ability=" << actorAbilityName(event.ability)
        << " affects_all_party=" << boolText(event.affectsAllParty)
        << " event_hit=" << boolText(event.hit)
        << " event_killed=" << boolText(event.killed);
}

void appendActorSummary(std::ostream &out, const std::optional<GameplayCombatActorInfo> &actor)
{
    if (!actor)
    {
        out << " actor_present=false";
        return;
    }

    out << " actor_present=true"
        << " actor_id=" << actor->actorId
        << " actor_monster_id=" << actor->monsterId
        << " actor_name=\"" << actor->displayName << "\""
        << " actor_level=" << actor->monsterLevel
        << " actor_max_hp=" << actor->maxHp
        << " actor_attack_bonus=" << actor->attackBonus
        << " actor_attack_preferences=" << actor->attackPreferences
        << " actor_special_attack=" << static_cast<int>(actor->specialAttackKind)
        << " actor_special_attack_level=" << actor->specialAttackLevel
        << " actor_bolster_affects_player_ac=" << boolText(actor->bolsterAffectsPlayerArmorClass);
}

void appendMemberDefenseSummary(
    std::ostream &out,
    const Character &member,
    const GameplayScreenRuntime *pRuntime)
{
    const ItemTable *pItemTable = pRuntime != nullptr ? pRuntime->itemTable() : nullptr;
    const StandardItemEnchantTable *pStandardItemEnchantTable =
        pRuntime != nullptr ? pRuntime->standardItemEnchantTable() : nullptr;
    const SpecialItemEnchantTable *pSpecialItemEnchantTable =
        pRuntime != nullptr ? pRuntime->specialItemEnchantTable() : nullptr;
    const CharacterSheetSummary summary = GameMechanics::buildCharacterSheetSummary(
        member,
        pItemTable,
        pStandardItemEnchantTable,
        pSpecialItemEnchantTable);

    out << " member_name=\"" << member.name << "\""
        << " member_health=" << member.health
        << " member_max_health=" << member.maxHealth
        << " member_level=" << member.level
        << " member_ac_actual=" << summary.armorClass.actual
        << " member_ac_modifier=" << member.armorClassModifier
        << " member_luck_actual=" << summary.luck.actual
        << " member_fire_resist=" << summary.fireResistance.actual
        << " member_air_resist=" << summary.airResistance.actual
        << " member_water_resist=" << summary.waterResistance.actual
        << " member_earth_resist=" << summary.earthResistance.actual
        << " member_mind_resist=" << summary.mindResistance.actual
        << " member_body_resist=" << summary.bodyResistance.actual
        << " member_physical_immune=" << boolText(member.physicalDamageImmune)
        << " member_half_missile_damage=" << boolText(member.halfMissileDamage);
}

void triggerPortraitFaceAnimation(
    GameplayScreenRuntime *pRuntime,
    size_t memberIndex,
    FaceAnimationId animationId)
{
    if (pRuntime != nullptr)
    {
        pRuntime->triggerPortraitFaceAnimation(memberIndex, animationId);
    }
}

void triggerMonsterSpecialPortraitFx(
    GameplayScreenRuntime *pRuntime,
    size_t memberIndex)
{
    if (pRuntime != nullptr)
    {
        pRuntime->triggerPortraitEventFxWithoutSpeech(memberIndex, PortraitFxEventKind::MonsterSpecial);
    }
}

SoundId soundForMonsterSpecialAttack(MonsterSpecialAttackKind specialAttackKind)
{
    switch (specialAttackKind)
    {
        case MonsterSpecialAttackKind::Curse:
        case MonsterSpecialAttackKind::Weak:
        case MonsterSpecialAttackKind::Sleep:
        case MonsterSpecialAttackKind::Drunk:
        case MonsterSpecialAttackKind::Fear:
            return SoundId::Star1;

        case MonsterSpecialAttackKind::PoisonWeak:
        case MonsterSpecialAttackKind::PoisonMedium:
        case MonsterSpecialAttackKind::PoisonSevere:
        case MonsterSpecialAttackKind::DiseaseWeak:
        case MonsterSpecialAttackKind::DiseaseMedium:
        case MonsterSpecialAttackKind::DiseaseSevere:
            return SoundId::Star2;

        case MonsterSpecialAttackKind::Insane:
        case MonsterSpecialAttackKind::Paralyze:
        case MonsterSpecialAttackKind::Unconscious:
            return SoundId::Star4;

        case MonsterSpecialAttackKind::Dead:
        case MonsterSpecialAttackKind::Petrify:
        case MonsterSpecialAttackKind::Eradicate:
            return SoundId::Eradicate;

        case MonsterSpecialAttackKind::BreakAny:
        case MonsterSpecialAttackKind::BreakArmor:
        case MonsterSpecialAttackKind::BreakWeapon:
            return SoundId::MetalVsMetal03;

        case MonsterSpecialAttackKind::Aging:
        case MonsterSpecialAttackKind::ManaDrain:
            return SoundId::ElecCircle;

        default:
            return SoundId::None;
    }
}

void playMonsterSpecialAttackSound(
    GameplayScreenRuntime *pRuntime,
    MonsterSpecialAttackKind specialAttackKind)
{
    if (pRuntime == nullptr)
    {
        return;
    }

    const SoundId soundId = soundForMonsterSpecialAttack(specialAttackKind);
    if (soundId != SoundId::None)
    {
        pRuntime->playCommonUiSound(soundId);
    }
}

void triggerPortraitFaceAnimationForAllLivingMembers(
    GameplayScreenRuntime *pRuntime,
    FaceAnimationId animationId)
{
    if (pRuntime != nullptr)
    {
        pRuntime->triggerPortraitFaceAnimationForAllLivingMembers(animationId);
    }
}

void playSpeechReaction(
    GameplayScreenRuntime *pRuntime,
    size_t memberIndex,
    SpeechId speechId,
    bool triggerFaceAnimation)
{
    if (pRuntime != nullptr)
    {
        pRuntime->playSpeechReaction(memberIndex, speechId, triggerFaceAnimation);
    }
}

// The combat log while it records (the combat_log setting), else null: the one the damage rules feed.
CombatLog *recordingCombatLog()
{
    CombatLog *pLog = boundCombatLog();
    return pLog != nullptr && pLog->recording() ? pLog : nullptr;
}

// A spell's name for the combat log; "a spell" where no spell table is at hand.
std::string combatLogSpellName(GameplayScreenRuntime *pRuntime, int spellId)
{
    const SpellTable *pSpells = pRuntime != nullptr ? pRuntime->spellTable() : nullptr;
    const SpellEntry *pSpell = pSpells != nullptr ? pSpells->findById(spellId) : nullptr;
    return pSpell != nullptr && !pSpell->name.empty() ? pSpell->name : "a spell";
}

void showHitStatus(
    GameplayScreenRuntime *pRuntime,
    const std::string &status)
{
    if (pRuntime == nullptr || status.empty() || !pRuntime->settingsSnapshot().showHits)
    {
        return;
    }

    pRuntime->setStatusBarEvent(status);
}

uint32_t animationTicks(const GameplayScreenRuntime *pRuntime)
{
    if (pRuntime != nullptr)
    {
        return pRuntime->animationTicks();
    }

    return 0;
}

int incomingAttackArmorClass(
    const Character &member,
    const GameplayScreenRuntime *pRuntime)
{
    const ItemTable *pItemTable = pRuntime != nullptr ? pRuntime->itemTable() : nullptr;
    const StandardItemEnchantTable *pStandardItemEnchantTable =
        pRuntime != nullptr ? pRuntime->standardItemEnchantTable() : nullptr;
    const SpecialItemEnchantTable *pSpecialItemEnchantTable =
        pRuntime != nullptr ? pRuntime->specialItemEnchantTable() : nullptr;
    const CharacterSheetSummary summary = GameMechanics::buildCharacterSheetSummary(
        member,
        pItemTable,
        pStandardItemEnchantTable,
        pSpecialItemEnchantTable);

    return std::max(0, summary.armorClass.actual + member.armorClassModifier);
}

std::mt19937 buildMonsterAttackRng(
    const GameplayCombatController::CombatEvent &event,
    size_t targetMemberIndex,
    uint32_t frameTicks)
{
    uint32_t seed = frameTicks
        ^ (event.sourceId * 2654435761u)
        ^ (static_cast<uint32_t>(targetMemberIndex + 1) * 40503u)
        ^ (static_cast<uint32_t>(std::max(0, event.damage)) * 1103515245u)
        ^ (static_cast<uint32_t>(std::max(0, event.spellId)) * 2246822519u);

    if (seed == 0)
    {
        seed = 1;
    }

    return std::mt19937(seed);
}

bool monsterImpactRequiresArmorHitRoll(
    const GameplayCombatController::CombatEvent &event,
    const std::optional<GameplayCombatActorInfo> &sourceActor)
{
    if (!sourceActor)
    {
        return false;
    }

    if (event.type == GameplayCombatController::CombatEventType::MonsterMeleeImpact)
    {
        return true;
    }

    return event.type == GameplayCombatController::CombatEventType::PartyProjectileImpact
        && !event.affectsAllParty
        && event.spellId == 0;
}

// The token of a monster's missile attack ("Fire", "Arrow"), from its monster's attack; empty for blows and spells.
std::string monsterMissileToken(
    const GameplayCombatController::PendingCombatEventContext &context,
    const GameplayCombatController::CombatEvent &event)
{
    const MonsterTable *pMonsterTable =
        context.pWorldRuntime != nullptr ? context.pWorldRuntime->monsterTable() : nullptr;

    if (event.type != GameplayCombatController::CombatEventType::PartyProjectileImpact || event.spellId != 0
        || pMonsterTable == nullptr)
    {
        return {};
    }

    const std::optional<GameplayCombatActorInfo> source = resolveActor(context, event.sourceId);
    const MonsterTable::MonsterStatsEntry *pStats =
        source ? pMonsterTable->findStatsById(source->monsterId) : nullptr;

    if (pStats == nullptr)
    {
        return {};
    }

    return event.ability == GameplayActorAttackAbility::Attack2 ? pStats->attack2MissileType
        : event.ability == GameplayActorAttackAbility::Attack1  ? pStats->attack1MissileType
                                                                : std::string();
}

MonsterAttackOnCharacter monsterAttackOnCharacter(
    const GameplayCombatController::PendingCombatEventContext &context,
    const GameplayCombatController::CombatEvent &event,
    const Character &member,
    int monsterLevel)
{
    MonsterAttackOnCharacter attack = {};
    attack.pCharacter = &member;
    attack.pItemTable = context.pRuntime != nullptr ? context.pRuntime->itemTable() : nullptr;
    attack.pStandardItemEnchantTable =
        context.pRuntime != nullptr ? context.pRuntime->standardItemEnchantTable() : nullptr;
    attack.pSpecialItemEnchantTable =
        context.pRuntime != nullptr ? context.pRuntime->specialItemEnchantTable() : nullptr;
    attack.type = event.damageType;
    attack.melee = event.type == GameplayCombatController::CombatEventType::MonsterMeleeImpact;
    attack.spellId = event.spellId;
    attack.affectsAllParty = event.affectsAllParty;
    attack.monsterLevel = monsterLevel;
    attack.partyCount = int(std::max<size_t>(1, context.party.members().size()));
    attack.missileToken = monsterMissileToken(context, event);
    return attack;
}

MonsterImpactHitCheck resolveMonsterImpactHitCheck(
    const GameplayCombatController::PendingCombatEventContext &context,
    const GameplayCombatController::CombatEvent &event,
    const GameplayCombatActorInfo &sourceActor,
    size_t targetMemberIndex)
{
    MonsterImpactHitCheck result = {};
    result.monsterLevel = sourceActor.monsterLevel;
    result.bolsterAffectsArmorClass = sourceActor.bolsterAffectsPlayerArmorClass;
    result.attackBonus = event.attackBonus > 0 ? event.attackBonus : sourceActor.attackBonus;

    const Character *pMember = context.party.member(targetMemberIndex);

    if (pMember == nullptr)
    {
        return result;
    }

    result.baseArmorClass = incomingAttackArmorClass(*pMember, context.pRuntime);

    if (event.spellId != 0)
    {
        result.baseArmorClass += pMember->magicArmorClassBonus;
    }
    else if (event.type == GameplayCombatController::CombatEventType::MonsterMeleeImpact)
    {
        result.baseArmorClass += pMember->meleeArmorClassBonus;
    }
    else
    {
        result.baseArmorClass += pMember->missileArmorClassBonus;
    }

    result.baseArmorClass = std::max(0, result.baseArmorClass);
    result.adjustedArmorClass =
        gameplayBolsterPlayerArmorClass(
            result.baseArmorClass,
            result.monsterLevel,
            static_cast<int>(std::max<uint32_t>(1, pMember->level)),
            result.bolsterAffectsArmorClass);
    std::mt19937 rng = buildMonsterAttackRng(event, targetMemberIndex, animationTicks(context.pRuntime));
    MonsterAttackOnCharacter attack = monsterAttackOnCharacter(context, event, *pMember, sourceActor.monsterLevel);
    attack.pAttackerFacts = &sourceActor.rulesetFacts;
    attack.armorClass = result.adjustedArmorClass;
    attack.attackBonus = result.attackBonus;
    attack.pRng = &rng;
    result.hit = context.party.rules().combat.monsterAttackLands(attack);
    return result;
}

bool characterEvadesMonsterImpact(
    const GameplayCombatController::PendingCombatEventContext &context,
    const Character &character,
    const GameplayCombatController::CombatEvent &event,
    const std::optional<GameplayCombatActorInfo> &sourceActor,
    size_t targetMemberIndex)
{
    std::mt19937 rng =
        buildMonsterAttackRng(event, targetMemberIndex, animationTicks(context.pRuntime) ^ 0x9e3779b9u);
    MonsterAttackOnCharacter attack =
        monsterAttackOnCharacter(context, event, character, sourceActor ? sourceActor->monsterLevel : 0);
    attack.pAttackerFacts = sourceActor ? &sourceActor->rulesetFacts : nullptr;
    attack.pRng = &rng;
    return context.party.rules().combat.characterEvades(attack);
}

// A personal shield sound through the world's pending sounds (played by name, its placeholder fallback meanwhile).
void playPersonalShieldSound(
    const GameplayCombatController::PendingCombatEventContext &context,
    const MonsterTable *pMonsterTable,
    const std::string &soundName)
{
    EventRuntimeState *pEventRuntimeState =
        context.pWorldRuntime != nullptr ? context.pWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr || soundName.empty())
    {
        return;
    }

    EventRuntimeState::PendingSound request = {};
    request.soundScope = SoundScope::World;
    request.soundName = soundName;
    const ShieldSoundDefinition *pSound =
        pMonsterTable != nullptr ? pMonsterTable->shields().findSound(soundName) : nullptr;
    request.fallbackSoundName = pSound != nullptr ? pSound->fallback : std::string();
    pEventRuntimeState->pendingSounds.push_back(std::move(request));
}

// The member's personal shield takes the hit first (Physical and Energy; every school at Shield Tech Master); what
// passes it reaches the body, Energy from a monster that follows the shield rules (shields.yml) x the exposed
// multiplier once the shield is down (x1.25 at Shield Tech Grandmaster). Members without a shield, hit by monsters
// without a shield profile (every MM6-MM9 monster), take the damage unchanged.
int personalShieldPassedDamage(
    const GameplayCombatController::PendingCombatEventContext &context,
    const GameplayCombatController::CombatEvent &event,
    const std::optional<GameplayCombatActorInfo> &sourceActor,
    size_t memberIndex)
{
    const Character *pMember = context.party.member(memberIndex);
    const MonsterTable *pMonsterTable =
        context.pWorldRuntime != nullptr ? context.pWorldRuntime->monsterTable() : nullptr;
    const bool attackerFollowsShieldRules = pMonsterTable != nullptr && sourceActor
        && pMonsterTable->findShieldProfile(sourceActor->monsterId) != nullptr;

    if (pMember == nullptr || event.damage <= 0
        || (pMember->personalShieldCapacity <= 0 && !attackerFollowsShieldRules))
    {
        return event.damage;
    }

    const CharacterSkill *pShieldTech = pMember->findSkill("ShieldTech");
    const SkillMastery shieldTechMastery = pShieldTech != nullptr ? pShieldTech->mastery : SkillMastery::None;
    const bool absorbable = event.damageType == CombatDamageType::Physical
        || event.damageType == CombatDamageType::Energy
        || shieldTechMastery >= SkillMastery::Master;
    int damage = event.damage;

    if (absorbable)
    {
        const Party::PersonalShieldHit hit = context.party.absorbPersonalShieldHit(memberIndex, damage);
        damage = hit.passedDamage;
        const PartyShieldRules &rules = context.party.personalShieldRules();

        if (hit.broke)
        {
            playPersonalShieldSound(context, pMonsterTable, rules.breakSound);
        }
        else if (hit.absorbed)
        {
            playPersonalShieldSound(context, pMonsterTable, rules.hitSound);
        }
    }

    if (attackerFollowsShieldRules && event.damageType == CombatDamageType::Energy && damage > 0
        && pMember->personalShield <= 0.0f)
    {
        const float multiplier = shieldTechMastery >= SkillMastery::Grandmaster
            ? context.party.personalShieldRules().hardenedExposedMultiplier
            : pMonsterTable->shields().exposedEnergyMultiplier();
        damage = int(std::lround(float(damage) * multiplier));
    }

    return damage;
}

int adjustedIncomingDamageForMember(
    const GameplayCombatController::PendingCombatEventContext &context,
    const GameplayCombatController::CombatEvent &event,
    const std::optional<GameplayCombatActorInfo> &sourceActor,
    const Character &member,
    size_t memberIndex,
    bool isPhysicalProjectile,
    int incomingDamage,
    bool coverHalved = false)
{
    std::mt19937 rng = buildMonsterAttackRng(event, memberIndex, animationTicks(context.pRuntime));
    CharacterDamageHit hit = {};
    hit.amount = incomingDamage;
    hit.type = event.damageType;
    hit.pCharacter = &member;
    hit.pItemTable = context.pRuntime != nullptr ? context.pRuntime->itemTable() : nullptr;
    hit.pStandardItemEnchantTable =
        context.pRuntime != nullptr ? context.pRuntime->standardItemEnchantTable() : nullptr;
    hit.pSpecialItemEnchantTable =
        context.pRuntime != nullptr ? context.pRuntime->specialItemEnchantTable() : nullptr;
    hit.monsterAttack = true;
    hit.physicalProjectile = isPhysicalProjectile;
    hit.attackerLevel = sourceActor ? sourceActor->monsterLevel : 0;
    hit.attackerFacts = sourceActor ? sourceActor->rulesetFacts : ActorRulesetFacts{};
    hit.attackerCurrentHp = sourceActor ? sourceActor->currentHp : 0;
    hit.attackerMaxHp = sourceActor ? sourceActor->maxHp : 0;
    hit.attack2 = event.ability == GameplayActorAttackAbility::Attack2;
    hit.spellId = event.spellId;
    hit.rolledAmount = event.damage;
    hit.attackerDebuffed = sourceActor && sourceActor->damageDebuffed;
    hit.coverHalved = coverHalved;
    hit.partyCount = int(std::max<size_t>(1, context.party.members().size()));
    hit.pRng = &rng;
    // What shields absorb is taken where every hit lands (Party::applyDamageToMember).
    return context.party.rules().combat.damageToCharacter(hit);
}

float recoverySecondsFromTicks(int ticks)
{
    return std::max(0.0f, static_cast<float>(ticks) / 128.0f * OeRealtimeRecoveryScale);
}

uint32_t equippedItemId(const Character &character, EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return character.equipment.offHand;
        case EquipmentSlot::MainHand:
            return character.equipment.mainHand;
        case EquipmentSlot::Bow:
            return character.equipment.bow;
        case EquipmentSlot::Armor:
            return character.equipment.armor;
        case EquipmentSlot::Helm:
            return character.equipment.helm;
        case EquipmentSlot::Belt:
            return character.equipment.belt;
        case EquipmentSlot::Cloak:
            return character.equipment.cloak;
        case EquipmentSlot::Gauntlets:
            return character.equipment.gauntlets;
        case EquipmentSlot::Boots:
            return character.equipment.boots;
        case EquipmentSlot::Amulet:
            return character.equipment.amulet;
        case EquipmentSlot::Ring1:
            return character.equipment.ring1;
        case EquipmentSlot::Ring2:
            return character.equipment.ring2;
        case EquipmentSlot::Ring3:
            return character.equipment.ring3;
        case EquipmentSlot::Ring4:
            return character.equipment.ring4;
        case EquipmentSlot::Ring5:
            return character.equipment.ring5;
        case EquipmentSlot::Ring6:
            return character.equipment.ring6;
    }

    return 0;
}

EquippedItemRuntimeState *equippedItemRuntimeState(Character &character, EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return &character.equipmentRuntime.offHand;
        case EquipmentSlot::MainHand:
            return &character.equipmentRuntime.mainHand;
        case EquipmentSlot::Bow:
            return &character.equipmentRuntime.bow;
        case EquipmentSlot::Armor:
            return &character.equipmentRuntime.armor;
        case EquipmentSlot::Helm:
            return &character.equipmentRuntime.helm;
        case EquipmentSlot::Belt:
            return &character.equipmentRuntime.belt;
        case EquipmentSlot::Cloak:
            return &character.equipmentRuntime.cloak;
        case EquipmentSlot::Gauntlets:
            return &character.equipmentRuntime.gauntlets;
        case EquipmentSlot::Boots:
            return &character.equipmentRuntime.boots;
        case EquipmentSlot::Amulet:
            return &character.equipmentRuntime.amulet;
        case EquipmentSlot::Ring1:
            return &character.equipmentRuntime.ring1;
        case EquipmentSlot::Ring2:
            return &character.equipmentRuntime.ring2;
        case EquipmentSlot::Ring3:
            return &character.equipmentRuntime.ring3;
        case EquipmentSlot::Ring4:
            return &character.equipmentRuntime.ring4;
        case EquipmentSlot::Ring5:
            return &character.equipmentRuntime.ring5;
        case EquipmentSlot::Ring6:
            return &character.equipmentRuntime.ring6;
    }

    return nullptr;
}

int parseIntegerOrZero(const std::string &text)
{
    if (text.empty())
    {
        return 0;
    }

    try
    {
        return std::stoi(text);
    }
    catch (...)
    {
        return 0;
    }
}

bool isRegularBreakableItemDefinition(const ItemDefinition &itemDefinition)
{
    return itemDefinition.itemId >= FirstRegularBreakableItemId
        && itemDefinition.itemId <= LastRegularBreakableItemId;
}

int breakItemSaveBonus(const ItemDefinition &itemDefinition)
{
    return 3 * (static_cast<int>(itemDefinition.rarity) + parseIntegerOrZero(itemDefinition.mod2));
}

bool itemMatchesBreakSpecial(
    const ItemDefinition &itemDefinition,
    MonsterSpecialAttackKind specialAttackKind)
{
    const ItemEnchantCategory category = ItemEnchantRuntime::categoryForItem(itemDefinition);

    switch (specialAttackKind)
    {
        case MonsterSpecialAttackKind::BreakAny:
            return isRegularBreakableItemDefinition(itemDefinition);
        case MonsterSpecialAttackKind::BreakArmor:
            return category == ItemEnchantCategory::Armor || category == ItemEnchantCategory::Shield;
        case MonsterSpecialAttackKind::BreakWeapon:
            return category == ItemEnchantCategory::OneHandedWeapon
                || category == ItemEnchantCategory::TwoHandedWeapon
                || category == ItemEnchantCategory::Missile;
        default:
            return false;
    }
}

std::vector<BreakItemCandidate> collectBreakItemCandidates(
    Character &member,
    const ItemTable *pItemTable,
    MonsterSpecialAttackKind specialAttackKind)
{
    std::vector<BreakItemCandidate> candidates;

    if (pItemTable == nullptr)
    {
        return candidates;
    }

    if (specialAttackKind == MonsterSpecialAttackKind::BreakAny)
    {
        for (InventoryItem &item : member.inventory)
        {
            const ItemDefinition *pItemDefinition = pItemTable->get(item.objectDescriptionId);

            if (pItemDefinition != nullptr
                && !item.broken
                && std::find(
                    pItemDefinition->contentEffect.flags.begin(),
                    pItemDefinition->contentEffect.flags.end(),
                    "Everlasting") == pItemDefinition->contentEffect.flags.end()
                && itemMatchesBreakSpecial(*pItemDefinition, specialAttackKind))
            {
                candidates.push_back({&item, nullptr, pItemDefinition});
            }
        }
    }

    for (EquipmentSlot slot : BreakItemEquipmentSlots)
    {
        const uint32_t itemId = equippedItemId(member, slot);
        EquippedItemRuntimeState *pRuntimeState = equippedItemRuntimeState(member, slot);
        const ItemDefinition *pItemDefinition = pItemTable->get(itemId);

        if (itemId != 0
            && pRuntimeState != nullptr
            && pItemDefinition != nullptr
            && !pRuntimeState->broken
            && std::find(
                pItemDefinition->contentEffect.flags.begin(),
                pItemDefinition->contentEffect.flags.end(),
                "Everlasting") == pItemDefinition->contentEffect.flags.end()
            && itemMatchesBreakSpecial(*pItemDefinition, specialAttackKind))
        {
            candidates.push_back({nullptr, pRuntimeState, pItemDefinition});
        }
    }

    return candidates;
}

std::optional<CharacterCondition> conditionForMonsterSpecialAttack(MonsterSpecialAttackKind specialAttackKind)
{
    switch (specialAttackKind)
    {
        case MonsterSpecialAttackKind::Curse:
            return CharacterCondition::Cursed;
        case MonsterSpecialAttackKind::Weak:
            return CharacterCondition::Weak;
        case MonsterSpecialAttackKind::Sleep:
            return CharacterCondition::Asleep;
        case MonsterSpecialAttackKind::Fear:
            return CharacterCondition::Fear;
        case MonsterSpecialAttackKind::Drunk:
            return CharacterCondition::Drunk;
        case MonsterSpecialAttackKind::Insane:
            return CharacterCondition::Insane;
        case MonsterSpecialAttackKind::PoisonWeak:
            return CharacterCondition::PoisonWeak;
        case MonsterSpecialAttackKind::PoisonMedium:
            return CharacterCondition::PoisonMedium;
        case MonsterSpecialAttackKind::PoisonSevere:
            return CharacterCondition::PoisonSevere;
        case MonsterSpecialAttackKind::DiseaseWeak:
            return CharacterCondition::DiseaseWeak;
        case MonsterSpecialAttackKind::DiseaseMedium:
            return CharacterCondition::DiseaseMedium;
        case MonsterSpecialAttackKind::DiseaseSevere:
            return CharacterCondition::DiseaseSevere;
        case MonsterSpecialAttackKind::Paralyze:
            return CharacterCondition::Paralyzed;
        case MonsterSpecialAttackKind::Unconscious:
            return CharacterCondition::Unconscious;
        case MonsterSpecialAttackKind::Dead:
            return CharacterCondition::Dead;
        case MonsterSpecialAttackKind::Petrify:
            return CharacterCondition::Petrified;
        case MonsterSpecialAttackKind::Eradicate:
            return CharacterCondition::Eradicated;
        default:
            return std::nullopt;
    }
}

bool monsterSpecialAttackSetsZeroHealth(MonsterSpecialAttackKind specialAttackKind)
{
    switch (specialAttackKind)
    {
        case MonsterSpecialAttackKind::Unconscious:
        case MonsterSpecialAttackKind::Dead:
        case MonsterSpecialAttackKind::Eradicate:
            return true;

        default:
            return false;
    }
}

FaceAnimationId faceAnimationForMonsterSpecialAttack(MonsterSpecialAttackKind specialAttackKind)
{
    switch (specialAttackKind)
    {
        case MonsterSpecialAttackKind::Curse:
            return FaceAnimationId::Cursed;
        case MonsterSpecialAttackKind::Weak:
            return FaceAnimationId::Weak;
        case MonsterSpecialAttackKind::Sleep:
            return FaceAnimationId::Tired;
        case MonsterSpecialAttackKind::Fear:
            return FaceAnimationId::Afraid;
        case MonsterSpecialAttackKind::Drunk:
            return FaceAnimationId::Drunk;
        case MonsterSpecialAttackKind::Insane:
            return FaceAnimationId::Insane;
        case MonsterSpecialAttackKind::PoisonWeak:
        case MonsterSpecialAttackKind::PoisonMedium:
        case MonsterSpecialAttackKind::PoisonSevere:
            return FaceAnimationId::Poisoned;
        case MonsterSpecialAttackKind::DiseaseWeak:
        case MonsterSpecialAttackKind::DiseaseMedium:
        case MonsterSpecialAttackKind::DiseaseSevere:
            return FaceAnimationId::Diseased;
        case MonsterSpecialAttackKind::Paralyze:
            return FaceAnimationId::Afraid;
        case MonsterSpecialAttackKind::Unconscious:
            return FaceAnimationId::Unconscious;
        case MonsterSpecialAttackKind::Dead:
            return FaceAnimationId::Death;
        case MonsterSpecialAttackKind::Petrify:
            return FaceAnimationId::Stoned;
        case MonsterSpecialAttackKind::Eradicate:
            return FaceAnimationId::Eradicated;
        case MonsterSpecialAttackKind::BreakAny:
        case MonsterSpecialAttackKind::BreakArmor:
        case MonsterSpecialAttackKind::BreakWeapon:
            return FaceAnimationId::ItemBrokenStolen;
        case MonsterSpecialAttackKind::Aging:
            return FaceAnimationId::Aged;
        case MonsterSpecialAttackKind::ManaDrain:
            return FaceAnimationId::SpellPointsDrained;
        default:
            return FaceAnimationId::Damaged;
    }
}

int monsterSpecialAttackSaveBonus(
    const Character &member,
    const CharacterSheetSummary &summary,
    MonsterSpecialAttackKind specialAttackKind,
    const BreakItemCandidate *pBreakCandidate)
{
    switch (specialAttackKind)
    {
        case MonsterSpecialAttackKind::Curse:
            return GameMechanics::primaryStatBonus(summary.personality.actual);
        case MonsterSpecialAttackKind::Weak:
        case MonsterSpecialAttackKind::Sleep:
        case MonsterSpecialAttackKind::Drunk:
        case MonsterSpecialAttackKind::DiseaseWeak:
        case MonsterSpecialAttackKind::DiseaseMedium:
        case MonsterSpecialAttackKind::DiseaseSevere:
        case MonsterSpecialAttackKind::Unconscious:
        case MonsterSpecialAttackKind::Aging:
            return GameMechanics::primaryStatBonus(summary.endurance.actual);
        case MonsterSpecialAttackKind::Insane:
        case MonsterSpecialAttackKind::Paralyze:
        case MonsterSpecialAttackKind::Fear:
            return summary.mindResistance.actual;
        case MonsterSpecialAttackKind::Petrify:
            return summary.earthResistance.actual;
        case MonsterSpecialAttackKind::PoisonWeak:
        case MonsterSpecialAttackKind::PoisonMedium:
        case MonsterSpecialAttackKind::PoisonSevere:
        case MonsterSpecialAttackKind::Dead:
        case MonsterSpecialAttackKind::Eradicate:
            return summary.bodyResistance.actual;
        case MonsterSpecialAttackKind::ManaDrain:
            return (GameMechanics::primaryStatBonus(summary.intellect.actual)
                + GameMechanics::primaryStatBonus(summary.personality.actual)) / 2;
        case MonsterSpecialAttackKind::BreakAny:
        case MonsterSpecialAttackKind::BreakArmor:
        case MonsterSpecialAttackKind::BreakWeapon:
            if (pBreakCandidate != nullptr && pBreakCandidate->pItemDefinition != nullptr)
            {
                return breakItemSaveBonus(*pBreakCandidate->pItemDefinition);
            }
            return 0;
        default:
            break;
    }

    (void)member;
    return 0;
}

bool memberSavesAgainstMonsterSpecialAttack(
    const Character &member,
    const CharacterSheetSummary &summary,
    MonsterSpecialAttackKind specialAttackKind,
    const BreakItemCandidate *pBreakCandidate,
    std::mt19937 &rng)
{
    // MM8 rolls rand() % (stat bonus + Luck bonus + 30) and saves on 30 or more (MM8-Rel.exe 0x48ef5c).
    const int saveCheck = GameMechanics::primaryStatBonus(summary.luck.actual)
        + monsterSpecialAttackSaveBonus(member, summary, specialAttackKind, pBreakCandidate)
        + 30;

    if (saveCheck <= 0)
    {
        return false;
    }

    return std::uniform_int_distribution<int>(0, saveCheck - 1)(rng) >= 30;
}

bool memberImmuneToMonsterSpecialAttack(
    const CharacterSheetSummary &summary,
    MonsterSpecialAttackKind specialAttackKind)
{
    switch (specialAttackKind)
    {
        case MonsterSpecialAttackKind::Insane:
        case MonsterSpecialAttackKind::Paralyze:
        case MonsterSpecialAttackKind::Fear:
            return summary.mindResistance.infinite;

        case MonsterSpecialAttackKind::Petrify:
            return summary.earthResistance.infinite;

        case MonsterSpecialAttackKind::PoisonWeak:
        case MonsterSpecialAttackKind::PoisonMedium:
        case MonsterSpecialAttackKind::PoisonSevere:
        case MonsterSpecialAttackKind::Dead:
        case MonsterSpecialAttackKind::Eradicate:
            return summary.bodyResistance.infinite;

        default:
            return false;
    }
}

// What a monster's hit on a party member may leave, and its chance in percent.
struct MonsterHitCondition
{
    MonsterSpecialAttackKind kind = MonsterSpecialAttackKind::None;
    int chancePercent = 0;
};

// A hit by its Spell1 or Spell2 leaves that spell's spell_conditions condition (none without one); a melee hit or a
// single-target Attack1 missile its special attack, at monster level x special attack level percent.
std::optional<MonsterHitCondition> monsterHitCondition(
    const GameplayCombatController::CombatEvent &event,
    const GameplayCombatActorInfo &sourceActor)
{
    const bool projectile = event.type == GameplayCombatController::CombatEventType::PartyProjectileImpact;

    if (projectile && event.spellId != 0)
    {
        const MonsterSpecialAttackKind kind = event.ability == GameplayActorAttackAbility::Spell1
            ? sourceActor.spell1Condition
            : event.ability == GameplayActorAttackAbility::Spell2 ? sourceActor.spell2Condition
                                                                   : MonsterSpecialAttackKind::None;
        if (kind == MonsterSpecialAttackKind::None)
        {
            return std::nullopt;
        }
        return MonsterHitCondition {kind, int(std::lround(sourceActor.spellConditionChance * 100.0f))};
    }

    const bool monsterMelee = event.type == GameplayCombatController::CombatEventType::MonsterMeleeImpact;
    const bool attack1Projectile =
        projectile && !event.affectsAllParty && event.ability == GameplayActorAttackAbility::Attack1;

    if ((!monsterMelee && !attack1Projectile)
        || sourceActor.specialAttackKind == MonsterSpecialAttackKind::None
        || sourceActor.specialAttackLevel <= 0
        || sourceActor.monsterLevel <= 0)
    {
        return std::nullopt;
    }

    const int chancePercent = sourceActor.monsterLevel * sourceActor.specialAttackLevel;
    return MonsterHitCondition {sourceActor.specialAttackKind, chancePercent};
}

bool rollMonsterHitCondition(const MonsterHitCondition &condition, std::mt19937 &rng)
{
    return condition.chancePercent >= 100
        || std::uniform_int_distribution<int>(0, 99)(rng) < condition.chancePercent;
}

bool applyMonsterSpecialAttack(
    GameplayCombatController::PendingCombatEventContext &context,
    const GameplayCombatController::CombatEvent &event,
    const GameplayCombatActorInfo &sourceActor,
    size_t memberIndex)
{
    Character *pMember = context.party.member(memberIndex);

    if (pMember == nullptr || pMember->health <= 0)
    {
        return false;
    }

    std::mt19937 rng = buildMonsterAttackRng(
        event,
        memberIndex,
        animationTicks(context.pRuntime) ^ 0x85ebca6bu);

    const std::optional<MonsterHitCondition> hitCondition = monsterHitCondition(event, sourceActor);

    if (!hitCondition
        || !rollMonsterHitCondition(*hitCondition, rng)
        || context.party.rules().combat.monsterMissileRules(monsterMissileToken(context, event)).noSpecialAttack)
    {
        return false;
    }

    const MonsterSpecialAttackKind kind = hitCondition->kind;

    std::vector<BreakItemCandidate> breakCandidates;
    const BreakItemCandidate *pBreakCandidate = nullptr;
    const ItemTable *pItemTable =
        context.pRuntime != nullptr ? context.pRuntime->itemTable() : context.party.itemTable();
    const StandardItemEnchantTable *pStandardItemEnchantTable =
        context.pRuntime != nullptr
            ? context.pRuntime->standardItemEnchantTable()
            : context.party.standardItemEnchantTable();
    const SpecialItemEnchantTable *pSpecialItemEnchantTable =
        context.pRuntime != nullptr
            ? context.pRuntime->specialItemEnchantTable()
            : context.party.specialItemEnchantTable();

    if (kind == MonsterSpecialAttackKind::BreakAny
        || kind == MonsterSpecialAttackKind::BreakArmor
        || kind == MonsterSpecialAttackKind::BreakWeapon)
    {
        breakCandidates = collectBreakItemCandidates(
            *pMember,
            pItemTable,
            kind);

        if (breakCandidates.empty())
        {
            return false;
        }

        pBreakCandidate = &breakCandidates[std::uniform_int_distribution<size_t>(
            0,
            breakCandidates.size() - 1)(rng)];
    }

    const CharacterSheetSummary summary = GameMechanics::buildCharacterSheetSummary(
        *pMember,
        pItemTable,
        pStandardItemEnchantTable,
        pSpecialItemEnchantTable);

    if (memberImmuneToMonsterSpecialAttack(summary, kind)
        || context.party.rules().combat.immuneToMonsterSpecialAttacks(*pMember))
    {
        return false;
    }

    if (memberSavesAgainstMonsterSpecialAttack(
            *pMember,
            summary,
            kind,
            pBreakCandidate,
            rng)
        && !context.party.rules().combat.piercesConditionSave(context.party))
    {
        return false;
    }

    bool applied = false;
    const std::optional<CharacterCondition> condition =
        conditionForMonsterSpecialAttack(kind);

    if (condition)
    {
        const size_t conditionIndex = static_cast<size_t>(*condition);
        const bool alreadyHadCondition =
            conditionIndex < CharacterConditionCount && pMember->conditions.test(conditionIndex);

        if (!alreadyHadCondition && context.party.rules().combat.blocksMonsterCondition(context.party, *condition))
        {
            return false;
        }

        if (alreadyHadCondition || !context.party.blockConditionWithProtectionFromMagic(*condition))
        {
            const float gameMinutes = context.pWorldRuntime != nullptr ? context.pWorldRuntime->gameMinutes() : 0.0f;
            applied = context.party.applyMemberCondition(memberIndex, *condition, gameMinutes);
            if (applied && monsterSpecialAttackSetsZeroHealth(kind))
            {
                pMember->health = 0;
            }
        }
    }
    else if (kind == MonsterSpecialAttackKind::ManaDrain)
    {
        if (!pMember->manaDrainImmune)
        {
            applied = pMember->spellPoints > 0;
            pMember->spellPoints = 0;
        }
    }
    else if (kind == MonsterSpecialAttackKind::Aging)
    {
        if (!pMember->agingImmune)
        {
            ++pMember->ageModifier;
            applied = true;
        }
    }
    else if (pBreakCandidate != nullptr)
    {
        // A hardened item stays a candidate, as in the original game; the attack just fails to break it.
        if (pBreakCandidate->pInventoryItem != nullptr
            && !ItemRuntime::isHardened(pBreakCandidate->pInventoryItem->hardened, *pBreakCandidate->pItemDefinition))
        {
            applied = !pBreakCandidate->pInventoryItem->broken;
            pBreakCandidate->pInventoryItem->broken = true;
        }
        else if (pBreakCandidate->pEquippedRuntime != nullptr
            && !ItemRuntime::isHardened(pBreakCandidate->pEquippedRuntime->hardened, *pBreakCandidate->pItemDefinition))
        {
            applied = !pBreakCandidate->pEquippedRuntime->broken;
            pBreakCandidate->pEquippedRuntime->broken = true;
        }
    }

    if (applied)
    {
        triggerMonsterSpecialPortraitFx(context.pRuntime, memberIndex);
        playMonsterSpecialAttackSound(context.pRuntime, kind);
        triggerPortraitFaceAnimation(
            context.pRuntime,
            memberIndex,
            faceAnimationForMonsterSpecialAttack(kind));
    }

    return applied;
}

void applyIncomingHitSideEffects(
    GameplayCombatController::PendingCombatEventContext &context,
    size_t memberIndex)
{
    context.party.clearMemberCondition(memberIndex, CharacterCondition::Asleep);
}

void applyPainReflection(
    GameplayCombatController::PendingCombatEventContext &context,
    const GameplayCombatController::CombatEvent &event,
    size_t memberIndex,
    int damage)
{
    if (context.pWorldRuntime == nullptr || damage <= 0)
    {
        return;
    }

    if (context.party.characterBuff(memberIndex, CharacterBuffId::PainReflection) == nullptr
        || context.party.rules().combat.monsterMissileRules(monsterMissileToken(context, event)).noPainReflection)
    {
        return;
    }

    context.pWorldRuntime->applyReflectedDamageToActor(
        event.sourceId,
        damage,
        event.damageType,
        static_cast<uint32_t>(memberIndex));
}

} // namespace

GameplayCombatController::CombatEvent GameplayCombatController::buildMonsterMeleeImpactEvent(
    uint32_t sourceId,
    int damage,
    int attackBonus,
    CombatDamageType damageType,
    GameplayActorAttackAbility ability)
{
    CombatEvent event = {};
    event.type = CombatEventType::MonsterMeleeImpact;
    event.sourceId = sourceId;
    event.damage = damage;
    event.attackBonus = attackBonus;
    event.damageType = damageType;
    event.ability = ability;
    return event;
}

GameplayCombatController::CombatEvent GameplayCombatController::buildMonsterRangedReleaseEvent(
    uint32_t sourceId,
    int damage,
    CombatDamageType damageType)
{
    CombatEvent event = {};
    event.type = CombatEventType::MonsterRangedRelease;
    event.sourceId = sourceId;
    event.damage = damage;
    event.damageType = damageType;
    return event;
}

GameplayCombatController::CombatEvent GameplayCombatController::buildPartyProjectileImpactEvent(
    uint32_t sourceId,
    int damage,
    int attackBonus,
    int spellId,
    bool affectsAllParty,
    CombatDamageType damageType,
    GameplayActorAttackAbility ability)
{
    CombatEvent event = {};
    event.type = CombatEventType::PartyProjectileImpact;
    event.sourceId = sourceId;
    event.damage = damage;
    event.attackBonus = attackBonus;
    event.spellId = spellId;
    event.affectsAllParty = affectsAllParty;
    event.damageType = damageType;
    event.ability = ability;
    return event;
}

GameplayCombatController::CombatEvent GameplayCombatController::buildPartyProjectileActorImpactEvent(
    uint32_t sourceId,
    uint32_t sourcePartyMemberIndex,
    uint32_t targetActorId,
    int damage,
    int spellId,
    bool hit,
    bool killed,
    bool critical)
{
    CombatEvent event = {};
    event.type = CombatEventType::PartyProjectileActorImpact;
    event.sourceId = sourceId;
    event.sourcePartyMemberIndex = sourcePartyMemberIndex;
    event.targetActorId = targetActorId;
    event.damage = hit ? damage : 0;
    event.spellId = spellId;
    event.hit = hit;
    event.killed = killed;
    event.critical = hit && critical;
    return event;
}

bool GameplayCombatController::partyHitLands(int appliedDamage, bool stunsTarget)
{
    return appliedDamage > 0 || stunsTarget;
}

std::string GameplayCombatController::formatPartyProjectileActorImpactStatusText(
    const std::string &sourceName,
    const std::string &targetName,
    const CombatEvent &event,
    const CombatRules *pRules,
    int monstersHit,
    int totalDamage)
{
    if (!event.hit)
    {
        return {};
    }

    if (pRules != nullptr && (event.killed || partyHitLands(event.damage, false)))
    {
        PartyHitStatus status;
        status.attackerName = sourceName;
        status.targetName = targetName;
        status.damage = monstersHit >= 2 ? totalDamage : event.damage;
        status.killed = event.killed;
        status.critical = event.critical;
        status.missile = true;
        status.spellId = uint32_t(std::max(0, event.spellId));
        status.monstersHit = monstersHit;

        if (const std::optional<std::string> text = pRules->partyHitStatusText(status))
        {
            return *text;
        }
    }

    if (event.killed)
    {
        return sourceName + " inflicts " + std::to_string(event.damage) + " points killing " + targetName;
    }

    if (!partyHitLands(event.damage, false))
    {
        return {};
    }

    return sourceName + " shoots " + targetName + " for " + std::to_string(event.damage) + " points";
}

std::string GameplayCombatController::formatPartyAttackStatusText(
    const std::string &attackerName,
    const std::string &targetName,
    const CharacterAttackResult &attack,
    bool killed,
    std::optional<int> appliedDamage,
    const CombatRules *pRules)
{
    if (!attack.canAttack)
    {
        return {};
    }

    if (attack.resolvesOnImpact)
    {
        return {};
    }

    if (targetName.empty())
    {
        return {};
    }

    if (!attack.hit)
    {
        return {};
    }

    const int statusDamage = std::max(0, appliedDamage.value_or(attack.damage));

    if (pRules != nullptr && (killed || partyHitLands(statusDamage, attack.stunTarget)))
    {
        PartyHitStatus status;
        status.attackerName = attackerName;
        status.targetName = targetName;
        status.damage = statusDamage;
        status.killed = killed;
        status.critical = attack.criticalDamage;
        status.missile = attack.mode == CharacterAttackMode::Bow || attack.mode == CharacterAttackMode::Wand
            || attack.mode == CharacterAttackMode::Blaster || attack.mode == CharacterAttackMode::DragonBreath;

        if (const std::optional<std::string> text = pRules->partyHitStatusText(status))
        {
            return *text;
        }
    }

    if (killed)
    {
        return attackerName + " inflicts " + std::to_string(statusDamage) + " points killing " + targetName;
    }

    if (!partyHitLands(statusDamage, attack.stunTarget))
    {
        return {};
    }

    if (attack.paralyzeTarget)
    {
        return attackerName + " paralyzes " + targetName;
    }

    if (attack.stunTarget)
    {
        return attackerName + " stuns " + targetName;
    }

    if (attack.mode == CharacterAttackMode::Bow
        || attack.mode == CharacterAttackMode::Wand
        || attack.mode == CharacterAttackMode::Blaster
        || attack.mode == CharacterAttackMode::DragonBreath)
    {
        return attackerName + " shoots " + targetName + " for " + std::to_string(statusDamage) + " points";
    }

    return attackerName + " hits " + targetName + " for " + std::to_string(statusDamage) + " damage";
}

void GameplayCombatController::handlePartyAttackPresentation(
    GameplayScreenRuntime *pRuntime,
    const PartyAttackPresentation &attack)
{
    GAMEPLAY_COMBAT_TRACE_BLOCK(
    {
        std::ostringstream out;
        out << "party_attack_attempt"
            << " member_index=" << attack.memberIndex
            << " attacker=\"" << attack.attackerName << "\""
            << " target=\"" << attack.targetName << "\""
            << " action_performed=" << boolText(attack.actionPerformed)
            << " attacked=" << boolText(attack.attacked)
            << " had_melee_target=" << boolText(attack.hadMeleeTarget)
            << " mode=" << characterAttackModeName(attack.attack.mode)
            << " can_attack=" << boolText(attack.attack.canAttack)
            << " hit=" << boolText(attack.attack.hit)
            << " resolves_on_impact=" << boolText(attack.attack.resolvesOnImpact)
            << " raw_damage=" << attack.attack.damage
            << " applied_damage=";
        if (attack.appliedDamage)
        {
            out << *attack.appliedDamage;
        }
        else
        {
            out << "none";
        }
        out << " attack_bonus=" << attack.attack.attackBonus
            << " target_ac=" << attack.attack.targetArmorClass
            << " target_distance=" << attack.attack.targetDistance
            << " recovery_seconds=" << attack.attack.recoverySeconds
            << " skill_level=" << attack.attack.skillLevel
            << " skill_mastery=" << attack.attack.skillMastery
            << " spell_id=" << attack.attack.spellId
            << " damage_type=" << combatDamageTypeName(attack.attack.damageType)
            << " critical=" << boolText(attack.attack.criticalDamage)
            << " stun=" << boolText(attack.attack.stunTarget)
            << " paralyze=" << boolText(attack.attack.paralyzeTarget)
            << " halve_target_ac=" << boolText(attack.attack.halveTargetArmorClass)
            << " killed=" << boolText(attack.killed)
            << " target_strong_enemy=" << boolText(attack.targetStrongEnemy);
        gameplayCombatTraceWrite(out.str());
    });

    if (attack.actionPerformed)
    {
        if (attack.attack.mode == CharacterAttackMode::Melee)
        {
            if (attack.hadMeleeTarget)
            {
                SpeechId speechId =
                    attack.attacked && attack.attack.hit ? SpeechId::AttackHit : SpeechId::AttackMiss;

                if (attack.killed)
                {
                    speechId = attack.targetStrongEnemy ? SpeechId::KillStrongEnemy : SpeechId::KillWeakEnemy;
                }

                triggerPortraitFaceAnimation(
                    pRuntime,
                    attack.memberIndex,
                    attack.attacked && attack.attack.hit ? FaceAnimationId::AttackHit : FaceAnimationId::AttackMiss);
                playSpeechReaction(pRuntime, attack.memberIndex, speechId, false);
            }
        }
        else
        {
            triggerPortraitFaceAnimation(pRuntime, attack.memberIndex, FaceAnimationId::Shoot);
            playSpeechReaction(pRuntime, attack.memberIndex, SpeechId::Shoot, false);
        }
    }

    const std::string status = formatPartyAttackStatusText(
        attack.attackerName,
        attack.targetName,
        attack.attack,
        attack.killed,
        attack.appliedDamage,
        &boundGameRules().combat);
    showHitStatus(pRuntime, status);

    // Missiles and spells are logged when they land (handlePendingCombatEvents).
    CombatLog *pLog = recordingCombatLog();

    if (pLog != nullptr && attack.actionPerformed && attack.attack.mode == CharacterAttackMode::Melee
        && attack.attacked && attack.attack.hit && attack.appliedDamage && *attack.appliedDamage > 0)
    {
        CombatLogEntry entry;
        entry.kind = CombatLogKind::Dealt;
        entry.attacker = attack.attackerName;
        entry.verb = "hits";
        entry.target = attack.targetName;
        entry.amount = *attack.appliedDamage;
        entry.critical = attack.attack.criticalDamage;
        entry.killed = attack.killed;
        pLog->add(std::move(entry));
    }
}

namespace
{
// A monster's hit on a party member, for the combat log: "<monster> hits <member> for N", killing when it fell.
void logMonsterHit(
    GameplayCombatController::PendingCombatEventContext &context,
    const GameplayCombatController::CombatEvent &event,
    const std::optional<GameplayCombatActorInfo> &sourceActor,
    size_t memberIndex,
    int damage)
{
    const Character *pMember = context.party.member(memberIndex);
    CombatLog *pLog = recordingCombatLog();

    if (pLog == nullptr || pMember == nullptr || damage <= 0)
    {
        return;
    }

    CombatLogEntry entry;
    entry.kind = CombatLogKind::Taken;
    entry.attacker = sourceActor && !sourceActor->displayName.empty() ? sourceActor->displayName : "A monster";
    entry.verb = event.type == GameplayCombatController::CombatEventType::MonsterMeleeImpact ? "hits"
        : event.spellId > 0                                                                    ? "casts"
                                                                                               : "shoots";
    entry.spell = event.spellId > 0 ? combatLogSpellName(context.pRuntime, event.spellId) : std::string();
    entry.target = pMember->name;
    entry.amount = damage;
    entry.killed = pMember->conditions.test(size_t(CharacterCondition::Dead))
        || pMember->conditions.test(size_t(CharacterCondition::Eradicated));
    pLog->add(std::move(entry));
}
}

void GameplayCombatController::handlePendingCombatEvents(
    PendingCombatEventContext &context,
    const std::vector<CombatEvent> &events)
{
    // A spell that hit several monsters in one frame (an area spell's explosion): the status line can give its total.
    std::vector<std::pair<std::pair<uint32_t, int>, std::pair<int, int>>> spellTotals;
    std::vector<std::pair<uint32_t, int>> loggedSpellTotals;

    for (const CombatEvent &event : events)
    {
        if (event.type != CombatEventType::PartyProjectileActorImpact || !event.hit || event.spellId <= 0)
        {
            continue;
        }

        const std::pair<uint32_t, int> key(event.sourcePartyMemberIndex, event.spellId);
        const auto found = std::find_if(spellTotals.begin(), spellTotals.end(),
            [&key](const auto &entry) { return entry.first == key; });

        if (found == spellTotals.end())
        {
            spellTotals.push_back({key, {1, event.damage}});
        }
        else
        {
            found->second.first += 1;
            found->second.second += event.damage;
        }
    }

    for (const CombatEvent &event : events)
    {
        if (event.type == CombatEventType::PartyProjectileActorImpact)
        {
            const Character *pSourceMember = context.party.member(event.sourcePartyMemberIndex);
            const std::optional<GameplayCombatActorInfo> targetActor = resolveActor(context, event.targetActorId);
            const std::string sourceName =
                pSourceMember != nullptr && !pSourceMember->name.empty() ? pSourceMember->name : "party";
            const std::string targetName = targetActor ? targetActor->displayName : "monster";

            GAMEPLAY_COMBAT_TRACE_BLOCK(
            {
                std::ostringstream out;
                out << "party_projectile_actor_result"
                    << " source_name=\"" << sourceName << "\""
                    << " target_name=\"" << targetName << "\"";
                appendCombatEventSummary(out, event);
                appendActorSummary(out, targetActor);
                if (pSourceMember != nullptr)
                {
                    out << " source_member_name=\"" << pSourceMember->name << "\""
                        << " source_member_health=" << pSourceMember->health
                        << " source_member_level=" << pSourceMember->level
                        << " source_member_luck=" << pSourceMember->luck;
                }
                out << " result=" << (!event.hit ? "missed" : event.killed ? "killed" : "hit")
                    << " final_damage=" << event.damage;
                gameplayCombatTraceWrite(out.str());
            });

            if (!event.hit || (!event.killed && !partyHitLands(event.damage, false)))
            {
                triggerPortraitFaceAnimation(
                    context.pRuntime,
                    event.sourcePartyMemberIndex,
                    FaceAnimationId::AttackMiss);
                playSpeechReaction(context.pRuntime, event.sourcePartyMemberIndex, SpeechId::AttackMiss, false);
            }
            else if (event.killed)
            {
                triggerPortraitFaceAnimation(
                    context.pRuntime,
                    event.sourcePartyMemberIndex,
                    FaceAnimationId::AttackHit);
                SpeechId speechId = SpeechId::AttackHit;

                if ((animationTicks(context.pRuntime) + event.targetActorId) % 100u < KillSpeechChancePercent)
                {
                    speechId = targetActor && targetActor->maxHp >= 100
                        ? SpeechId::KillStrongEnemy
                        : SpeechId::KillWeakEnemy;
                }

                playSpeechReaction(context.pRuntime, event.sourcePartyMemberIndex, speechId, false);
            }
            else
            {
                triggerPortraitFaceAnimation(
                    context.pRuntime,
                    event.sourcePartyMemberIndex,
                    FaceAnimationId::AttackHit);
                playSpeechReaction(context.pRuntime, event.sourcePartyMemberIndex, SpeechId::AttackHit, false);
            }

            const auto total = std::find_if(spellTotals.begin(), spellTotals.end(),
                [&event](const auto &entry)
                {
                    return entry.first == std::pair<uint32_t, int>(event.sourcePartyMemberIndex, event.spellId);
                });
            const int monstersHit = total != spellTotals.end() ? total->second.first : 1;
            const std::string status = formatPartyProjectileActorImpactStatusText(sourceName, targetName, event,
                &context.party.rules().combat,
                monstersHit,
                total != spellTotals.end() ? total->second.second : event.damage);
            showHitStatus(context.pRuntime, status);

            // An area spell's hits are one line with their total, logged once (its first hit), without stages.
            if (CombatLog *pLog = recordingCombatLog(); pLog != nullptr && event.hit && event.damage > 0)
            {
                CombatLogEntry entry;
                entry.kind = CombatLogKind::Dealt;
                entry.attacker = sourceName;
                entry.verb = event.spellId > 0 ? "casts" : "shoots";
                entry.spell = event.spellId > 0 ? combatLogSpellName(context.pRuntime, event.spellId) : std::string();
                entry.target = targetName;
                entry.amount = event.damage;
                entry.critical = event.critical;
                entry.killed = event.killed;

                if (monstersHit <= 1)
                {
                    pLog->add(std::move(entry));
                }
                else if (std::find(loggedSpellTotals.begin(), loggedSpellTotals.end(), total->first)
                    == loggedSpellTotals.end())
                {
                    loggedSpellTotals.push_back(total->first);
                    entry.target = std::to_string(monstersHit) + " monsters";
                    entry.amount = total->second.second;
                    entry.killed = false;
                    pLog->add(std::move(entry), false);
                }
            }

            // Only rules with hit effects need the hit, and its actor found by a scan of the map's actors (STD3-4).
            if (event.hit && event.damage > 0 && targetActor && context.party.rules().combat.usesPartyHitEffects())
            {
                PartyHitOnMonster hit;
                hit.memberIndex = event.sourcePartyMemberIndex;
                hit.pTarget = &targetActor->rulesetFacts;
                hit.damage = event.damage;
                hit.type = event.damageType;
                hit.spellId = uint32_t(std::max(0, event.spellId));
                hit.killed = event.killed;
                hit.pWorld = context.pWorldRuntime;

                for (size_t actorIndex = 0; context.pWorldRuntime != nullptr
                     && actorIndex < context.pWorldRuntime->mapActorCount();
                     ++actorIndex)
                {
                    GameplayRuntimeActorState state;

                    if (context.pWorldRuntime->actorRuntimeState(actorIndex, state)
                        && state.actorId == targetActor->actorId)
                    {
                        hit.targetActorIndex = actorIndex;
                        break;
                    }
                }

                context.party.rules().combat.applyPartyHitEffects(context.party, hit);
            }

            if (event.hit
                && event.damage > 0
                && event.spellId == 0
                && pSourceMember != nullptr
                && pSourceMember->vampiricHealFraction > 0.0f)
            {
                context.party.healMember(
                    event.sourcePartyMemberIndex,
                    std::max(1, static_cast<int>(
                        std::round(static_cast<float>(event.damage) * pSourceMember->vampiricHealFraction))));
            }

            continue;
        }

        if (event.type != CombatEventType::MonsterMeleeImpact
            && event.type != CombatEventType::PartyProjectileImpact)
        {
            continue;
        }

        uint32_t sourceAttackPreferences = 0;

        const std::optional<GameplayCombatActorInfo> sourceActor = resolveActor(context, event.sourceId);
        if (sourceActor)
        {
            sourceAttackPreferences = sourceActor->attackPreferences;
        }

        std::optional<size_t> targetMemberIndex = std::nullopt;
        bool coverHalved = false;

        if (!event.affectsAllParty)
        {
            targetMemberIndex = sourceActor
                ? context.party.rules().combat.monsterAttackTarget(context.party, sourceActor->rulesetFacts)
                : std::nullopt;

            // A target the rules chose cannot be covered (MAW's Fixator).
            if (!targetMemberIndex)
            {
                targetMemberIndex = context.party.chooseMonsterAttackTarget(
                    sourceAttackPreferences,
                    event.sourceId ^ static_cast<uint32_t>(event.damage) ^ static_cast<uint32_t>(event.spellId));

                // Some missiles strike a conscious member at random instead (MAW's elemental missiles).
                if (context.party.rules().combat.monsterMissileRules(monsterMissileToken(context, event)).randomTarget)
                {
                    std::vector<size_t> conscious;

                    for (size_t memberIndex = 0; memberIndex < context.party.members().size(); ++memberIndex)
                    {
                        if (GameMechanics::canAct(*context.party.member(memberIndex)))
                        {
                            conscious.push_back(memberIndex);
                        }
                    }

                    if (!conscious.empty())
                    {
                        std::mt19937 targetRng =
                            buildMonsterAttackRng(event, 0x51ed270bu, animationTicks(context.pRuntime));
                        targetMemberIndex =
                            conscious[std::uniform_int_distribution<size_t>(0, conscious.size() - 1)(targetRng)];
                    }
                }

                if (targetMemberIndex && sourceActor)
                {
                    std::mt19937 coverRng =
                        buildMonsterAttackRng(event, *targetMemberIndex + 16, animationTicks(context.pRuntime));
                    const std::optional<CoverOutcome> cover = context.party.rules().combat.coverMonsterAttack(
                        context.party,
                        MonsterAttackCover {*targetMemberIndex, event.spellId != 0, event.damageType, &coverRng});

                    if (cover)
                    {
                        const Character *pCoverer = context.party.member(cover->memberIndex);
                        const Character *pCovered = context.party.member(*targetMemberIndex);

                        if (pCoverer != nullptr && pCovered != nullptr)
                        {
                            showHitStatus(context.pRuntime, cover->halved
                                ? pCoverer->name + " covers the blow"
                                : pCoverer->name + " covers " + pCovered->name);
                        }

                        // As MAW shows it (zzMaw-Monsters.lua:3970-3971): the Shield spell's portrait flash on the
                        // member the blow was meant for (SetPlayerBuffAnim, Shield) and the skill-increase face on
                        // the coverer (ShowFaceAnimation(14)).
                        if (context.pRuntime != nullptr)
                        {
                            context.pRuntime->triggerPortraitEventFxWithoutSpeech(
                                *targetMemberIndex, PortraitFxEventKind::Cover);
                            triggerPortraitFaceAnimation(
                                context.pRuntime, cover->memberIndex, FaceAnimationId::SkillIncreased);
                        }

                        targetMemberIndex = cover->memberIndex;
                        coverHalved = cover->halved;
                    }
                }
            }
        }

        Character *pTargetMember = targetMemberIndex ? context.party.member(*targetMemberIndex) : nullptr;
        const bool needsArmorHitRoll = monsterImpactRequiresArmorHitRoll(event, sourceActor);

        std::optional<MonsterImpactHitCheck> hitCheck = std::nullopt;
        if (needsArmorHitRoll && targetMemberIndex.has_value() && sourceActor)
        {
            hitCheck = resolveMonsterImpactHitCheck(context, event, *sourceActor, *targetMemberIndex);
        }

        if (hitCheck && !hitCheck->hit)
        {
            GAMEPLAY_COMBAT_TRACE_BLOCK(
            {
                std::ostringstream out;
                out << "monster_attack_result result=missed";
                appendCombatEventSummary(out, event);
                appendActorSummary(out, sourceActor);
                out << " target_member_index=" << *targetMemberIndex
                    << " target_selected=true"
                    << " needs_armor_hit_roll=" << boolText(needsArmorHitRoll)
                    << " hit_roll_result=false"
                    << " base_ac=" << hitCheck->baseArmorClass
                    << " adjusted_ac=" << hitCheck->adjustedArmorClass
                    << " monster_level=" << hitCheck->monsterLevel
                    << " attack_bonus_used=" << hitCheck->attackBonus
                    << " bolster_affects_ac=" << boolText(hitCheck->bolsterAffectsArmorClass);
                if (pTargetMember != nullptr)
                {
                    appendMemberDefenseSummary(out, *pTargetMember, context.pRuntime);
                }
                gameplayCombatTraceWrite(out.str());
            });
            continue;
        }

        const bool ignorePhysicalDamage =
            pTargetMember != nullptr
            && pTargetMember->physicalDamageImmune
            && event.damageType == CombatDamageType::Physical;

        if (ignorePhysicalDamage)
        {
            GAMEPLAY_COMBAT_TRACE_BLOCK(
            {
                std::ostringstream out;
                out << "monster_attack_result result=immune";
                appendCombatEventSummary(out, event);
                appendActorSummary(out, sourceActor);
                out << " target_member_index=";
                if (targetMemberIndex)
                {
                    out << *targetMemberIndex;
                }
                else
                {
                    out << "none";
                }
                out << " target_selected=" << boolText(targetMemberIndex.has_value())
                    << " needs_armor_hit_roll=" << boolText(needsArmorHitRoll);
                if (hitCheck)
                {
                    out << " hit_roll_result=" << boolText(hitCheck->hit)
                        << " base_ac=" << hitCheck->baseArmorClass
                        << " adjusted_ac=" << hitCheck->adjustedArmorClass
                        << " monster_level=" << hitCheck->monsterLevel
                        << " attack_bonus_used=" << hitCheck->attackBonus
                        << " bolster_affects_ac=" << boolText(hitCheck->bolsterAffectsArmorClass);
                }
                if (pTargetMember != nullptr)
                {
                    appendMemberDefenseSummary(out, *pTargetMember, context.pRuntime);
                }
                gameplayCombatTraceWrite(out.str());
            });
            continue;
        }

        const bool isPhysicalProjectile =
            event.type == CombatEventType::PartyProjectileImpact && event.damageType == CombatDamageType::Physical;
        bool damagedParty = false;
        std::vector<DamagedMember> damagedMembers;
        std::vector<size_t> specialAttackMembers;

        if (event.affectsAllParty)
        {
            for (size_t memberIndex = 0; memberIndex < context.party.members().size(); ++memberIndex)
            {
                Character *pMember = context.party.member(memberIndex);

                if (pMember == nullptr
                    || (pMember->health <= 0
                        && !pMember->conditions.test(static_cast<size_t>(CharacterCondition::Unconscious)))
                    || pMember->conditions.test(static_cast<size_t>(CharacterCondition::Dead))
                    || pMember->conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
                    || pMember->conditions.test(static_cast<size_t>(CharacterCondition::Eradicated)))
                {
                    continue;
                }

                if (pMember->physicalDamageImmune
                    && event.damageType == CombatDamageType::Physical)
                {
                    GAMEPLAY_COMBAT_TRACE_BLOCK(
                    {
                        std::ostringstream out;
                        out << "monster_attack_result result=immune";
                        appendCombatEventSummary(out, event);
                        appendActorSummary(out, sourceActor);
                        out << " target_member_index=" << memberIndex
                            << " target_selected=true"
                            << " affects_all_member=true"
                            << " needs_armor_hit_roll=" << boolText(needsArmorHitRoll);
                        appendMemberDefenseSummary(out, *pMember, context.pRuntime);
                        gameplayCombatTraceWrite(out.str());
                    });
                    continue;
                }

                if (characterEvadesMonsterImpact(context, *pMember, event, sourceActor, memberIndex))
                {
                    GAMEPLAY_COMBAT_TRACE_BLOCK(
                    {
                        std::ostringstream out;
                        out << "monster_attack_result result=evaded";
                        appendCombatEventSummary(out, event);
                        appendActorSummary(out, sourceActor);
                        out << " target_member_index=" << memberIndex
                            << " target_selected=true"
                            << " affects_all_member=true"
                            << " needs_armor_hit_roll=" << boolText(needsArmorHitRoll);
                        appendMemberDefenseSummary(out, *pMember, context.pRuntime);
                        gameplayCombatTraceWrite(out.str());
                    });
                    showHitStatus(context.pRuntime, pMember->name + " evades damage");
                    continue;
                }

                specialAttackMembers.push_back(memberIndex);

                const int shieldedDamage = personalShieldPassedDamage(context, event, sourceActor, memberIndex);
                const int adjustedDamage = shieldedDamage > 0
                    ? adjustedIncomingDamageForMember(
                        context, event, sourceActor, *pMember, memberIndex, isPhysicalProjectile, shieldedDamage)
                    : 0;
                const bool applied = context.party.applyDamageToMember(memberIndex, adjustedDamage, "", true);
                damagedParty = applied || damagedParty;

                GAMEPLAY_COMBAT_TRACE_BLOCK(
                {
                    std::ostringstream out;
                    out << "monster_attack_result result=" << (applied ? "damaged" : "no_damage_applied");
                    appendCombatEventSummary(out, event);
                    appendActorSummary(out, sourceActor);
                    out << " target_member_index=" << memberIndex
                        << " target_selected=true"
                        << " affects_all_member=true"
                        << " needs_armor_hit_roll=" << boolText(needsArmorHitRoll)
                        << " input_damage=" << event.damage
                        << " final_damage=" << adjustedDamage
                        << " resisted_or_adjusted_damage=" << (event.damage - adjustedDamage)
                        << " physical_projectile=" << boolText(isPhysicalProjectile)
                        << " applied=" << boolText(applied);
                    appendMemberDefenseSummary(out, *pMember, context.pRuntime);
                    gameplayCombatTraceWrite(out.str());
                });

                if (applied)
                {
                    damagedMembers.push_back({memberIndex, adjustedDamage});
                    logMonsterHit(context, event, sourceActor, memberIndex, adjustedDamage);
                }
            }
        }
        else
        {
            const bool evaded =
                pTargetMember != nullptr && targetMemberIndex
                    ? characterEvadesMonsterImpact(context, *pTargetMember, event, sourceActor, *targetMemberIndex)
                    : false;

            if (evaded)
            {
                GAMEPLAY_COMBAT_TRACE_BLOCK(
                {
                    std::ostringstream out;
                    out << "monster_attack_result result=evaded";
                    appendCombatEventSummary(out, event);
                    appendActorSummary(out, sourceActor);
                    out << " target_member_index=" << (targetMemberIndex ? std::to_string(*targetMemberIndex) : "none")
                        << " target_selected=" << boolText(targetMemberIndex.has_value())
                        << " affects_all_member=false"
                        << " needs_armor_hit_roll=" << boolText(needsArmorHitRoll);
                    if (hitCheck)
                    {
                        out << " hit_roll_result=" << boolText(hitCheck->hit)
                            << " base_ac=" << hitCheck->baseArmorClass
                            << " adjusted_ac=" << hitCheck->adjustedArmorClass
                            << " monster_level=" << hitCheck->monsterLevel
                            << " attack_bonus_used=" << hitCheck->attackBonus
                            << " bolster_affects_ac=" << boolText(hitCheck->bolsterAffectsArmorClass);
                    }
                    if (pTargetMember != nullptr)
                    {
                        appendMemberDefenseSummary(out, *pTargetMember, context.pRuntime);
                    }
                    gameplayCombatTraceWrite(out.str());
                });
                showHitStatus(context.pRuntime, pTargetMember->name + " evades damage");
            }

            if (!evaded && targetMemberIndex.has_value())
            {
                specialAttackMembers.push_back(*targetMemberIndex);
            }

            // After the evasion roll, so an evaded hit leaves the personal shield untouched.
            const int shieldedDamage = pTargetMember != nullptr && targetMemberIndex && !evaded
                ? personalShieldPassedDamage(context, event, sourceActor, *targetMemberIndex)
                : event.damage;
            const int adjustedDamage =
                pTargetMember != nullptr && targetMemberIndex
                    ? (shieldedDamage > 0
                        ? adjustedIncomingDamageForMember(
                            context,
                            event,
                            sourceActor,
                            *pTargetMember,
                            *targetMemberIndex,
                            isPhysicalProjectile,
                            shieldedDamage,
                            coverHalved)
                        : 0)
                    : event.damage;

            damagedParty = targetMemberIndex
                ? (!evaded && context.party.applyDamageToMember(*targetMemberIndex, adjustedDamage, ""))
                : false;

            if (!evaded)
            {
                GAMEPLAY_COMBAT_TRACE_BLOCK(
                {
                    std::ostringstream out;
                    out << "monster_attack_result result=" << (damagedParty ? "damaged" : "no_damage_applied");
                    appendCombatEventSummary(out, event);
                    appendActorSummary(out, sourceActor);
                    out << " target_member_index=" << (targetMemberIndex ? std::to_string(*targetMemberIndex) : "none")
                        << " target_selected=" << boolText(targetMemberIndex.has_value())
                        << " affects_all_member=false"
                        << " needs_armor_hit_roll=" << boolText(needsArmorHitRoll);
                    if (hitCheck)
                    {
                        out << " hit_roll_result=" << boolText(hitCheck->hit)
                            << " base_ac=" << hitCheck->baseArmorClass
                            << " adjusted_ac=" << hitCheck->adjustedArmorClass
                            << " monster_level=" << hitCheck->monsterLevel
                            << " attack_bonus_used=" << hitCheck->attackBonus
                            << " bolster_affects_ac=" << boolText(hitCheck->bolsterAffectsArmorClass);
                    }
                    out << " input_damage=" << event.damage
                        << " final_damage=" << adjustedDamage
                        << " resisted_or_adjusted_damage=" << (event.damage - adjustedDamage)
                        << " physical_projectile=" << boolText(isPhysicalProjectile)
                        << " applied=" << boolText(damagedParty);
                    if (pTargetMember != nullptr)
                    {
                        appendMemberDefenseSummary(out, *pTargetMember, context.pRuntime);
                    }
                    gameplayCombatTraceWrite(out.str());
                });
            }

            if (damagedParty && targetMemberIndex.has_value())
            {
                damagedMembers.push_back({*targetMemberIndex, adjustedDamage});
                logMonsterHit(context, event, sourceActor, *targetMemberIndex, adjustedDamage);
            }
        }

        if (damagedParty)
        {
            // Physical projectiles use the same armor-impact path as melee hits.
            if (event.type == CombatEventType::MonsterMeleeImpact || isPhysicalProjectile)
            {
                for (const DamagedMember &damagedMember : damagedMembers)
                {
                    context.party.requestDamageImpactSoundForMember(damagedMember.memberIndex);
                }
            }

            for (const DamagedMember &damagedMember : damagedMembers)
            {
                applyIncomingHitSideEffects(context, damagedMember.memberIndex);
                applyPainReflection(context, event, damagedMember.memberIndex, damagedMember.damage);

                if (sourceActor)
                {
                    context.party.rules().combat.applyMonsterHitEffects(
                        context.party,
                        context.pWorldRuntime,
                        damagedMember.memberIndex,
                        sourceActor->rulesetFacts,
                        sourceActor->actorId,
                        damagedMember.damage,
                        event.damageType);
                }
            }

            if (sourceActor)
            {
                for (size_t memberIndex : specialAttackMembers)
                {
                    applyMonsterSpecialAttack(context, event, *sourceActor, memberIndex);
                }
            }

            if (event.affectsAllParty)
            {
                triggerPortraitFaceAnimationForAllLivingMembers(context.pRuntime, FaceAnimationId::DamagedParty);
                playSpeechReaction(context.pRuntime, context.party.activeMemberIndex(), SpeechId::DamagedParty, false);
            }
            else
            {
                triggerPortraitFaceAnimation(context.pRuntime, *targetMemberIndex, FaceAnimationId::Damaged);
            }
        }
        else if (sourceActor)
        {
            for (size_t memberIndex : specialAttackMembers)
            {
                applyMonsterSpecialAttack(context, event, *sourceActor, memberIndex);
            }
        }
    }
}

void GameplayCombatController::clear()
{
    m_pendingCombatEvents.clear();
}

void GameplayCombatController::recordMonsterMeleeImpact(uint32_t sourceId, int damage)
{
    m_pendingCombatEvents.push_back(
        buildMonsterMeleeImpactEvent(
            sourceId,
            damage,
            0,
            CombatDamageType::Physical,
            GameplayActorAttackAbility::Attack1));
}

void GameplayCombatController::recordMonsterMeleeImpact(uint32_t sourceId, int damage, int attackBonus)
{
    m_pendingCombatEvents.push_back(
        buildMonsterMeleeImpactEvent(
            sourceId,
            damage,
            attackBonus,
            CombatDamageType::Physical,
            GameplayActorAttackAbility::Attack1));
}

void GameplayCombatController::recordMonsterMeleeImpact(
    uint32_t sourceId,
    int damage,
    int attackBonus,
    CombatDamageType damageType,
    GameplayActorAttackAbility ability)
{
    m_pendingCombatEvents.push_back(
        buildMonsterMeleeImpactEvent(sourceId, damage, attackBonus, damageType, ability));
}

void GameplayCombatController::recordMonsterRangedRelease(
    uint32_t sourceId,
    int damage)
{
    recordMonsterRangedRelease(sourceId, damage, CombatDamageType::Physical);
}

void GameplayCombatController::recordMonsterRangedRelease(
    uint32_t sourceId,
    int damage,
    CombatDamageType damageType)
{
    m_pendingCombatEvents.push_back(buildMonsterRangedReleaseEvent(sourceId, damage, damageType));
}

void GameplayCombatController::recordPartyProjectileImpact(
    uint32_t sourceId,
    int damage,
    int spellId,
    bool affectsAllParty)
{
    recordPartyProjectileImpact(sourceId, damage, spellId, affectsAllParty, CombatDamageType::Physical);
}

void GameplayCombatController::recordPartyProjectileImpact(
    uint32_t sourceId,
    int damage,
    int spellId,
    bool affectsAllParty,
    CombatDamageType damageType)
{
    recordPartyProjectileImpact(sourceId, damage, 0, spellId, affectsAllParty, damageType);
}

void GameplayCombatController::recordPartyProjectileImpact(
    uint32_t sourceId,
    int damage,
    int attackBonus,
    int spellId,
    bool affectsAllParty,
    CombatDamageType damageType)
{
    recordPartyProjectileImpact(
        sourceId,
        damage,
        attackBonus,
        spellId,
        affectsAllParty,
        damageType,
        GameplayActorAttackAbility::Attack1);
}

void GameplayCombatController::recordPartyProjectileImpact(
    uint32_t sourceId,
    int damage,
    int attackBonus,
    int spellId,
    bool affectsAllParty,
    CombatDamageType damageType,
    GameplayActorAttackAbility ability)
{
    m_pendingCombatEvents.push_back(
        buildPartyProjectileImpactEvent(sourceId, damage, attackBonus, spellId, affectsAllParty, damageType, ability));
}

void GameplayCombatController::recordPartyProjectileActorImpact(
    uint32_t sourceId,
    uint32_t sourcePartyMemberIndex,
    uint32_t targetActorId,
    int damage,
    int spellId,
    bool hit,
    bool killed,
    bool critical)
{
    m_pendingCombatEvents.push_back(
        buildPartyProjectileActorImpactEvent(
            sourceId,
            sourcePartyMemberIndex,
            targetActorId,
            damage,
            spellId,
            hit,
            killed,
            critical));
}

const std::vector<GameplayCombatController::CombatEvent> &GameplayCombatController::pendingCombatEvents() const
{
    return m_pendingCombatEvents;
}

void GameplayCombatController::clearPendingCombatEvents()
{
    m_pendingCombatEvents.clear();
}

void GameplayCombatController::handleAndClearPendingCombatEvents(PendingCombatEventContext &context)
{
    handlePendingCombatEvents(context, m_pendingCombatEvents);
    m_pendingCombatEvents.clear();
}
} // namespace OpenYAMM::Game
