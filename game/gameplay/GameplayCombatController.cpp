#include "game/gameplay/GameplayCombatController.h"

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <cmath>
#include <iterator>
#include <limits>
#include <random>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t KillSpeechChancePercent = 20;
constexpr float OeRealtimeRecoveryScale = 2.133333333333333f;

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

bool monsterImpactHitsMember(
    const GameplayCombatController::PendingCombatEventContext &context,
    const GameplayCombatController::CombatEvent &event,
    const GameplayCombatActorInfo &sourceActor,
    size_t targetMemberIndex)
{
    const Character *pMember = context.party.member(targetMemberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    const int armorClass = incomingAttackArmorClass(*pMember, context.pRuntime);
    std::mt19937 rng = buildMonsterAttackRng(event, targetMemberIndex, animationTicks(context.pRuntime));
    const int attackBonus = event.attackBonus > 0 ? event.attackBonus : sourceActor.attackBonus;
    return GameMechanics::monsterAttackHitsArmorClass(
        armorClass,
        sourceActor.monsterLevel,
        attackBonus,
        rng);
}

int characterCombatSkillLevel(const Character &character, const std::string &skillName)
{
    const CharacterSkill *pSkill = character.findSkill(skillName);
    const std::unordered_map<std::string, int>::const_iterator bonusIt =
        character.itemSkillBonuses.find(skillName);
    const int bonusLevel = bonusIt != character.itemSkillBonuses.end() ? bonusIt->second : 0;
    return (pSkill != nullptr ? static_cast<int>(pSkill->level) : 0) + bonusLevel;
}

SkillMastery characterCombatSkillMastery(const Character &character, const std::string &skillName)
{
    const CharacterSkill *pSkill = character.findSkill(skillName);
    return pSkill != nullptr ? pSkill->mastery : SkillMastery::None;
}

bool characterEvadesMonsterImpact(
    const Character &character,
    const GameplayCombatController::CombatEvent &event,
    size_t targetMemberIndex,
    uint32_t frameTicks)
{
    const bool canEvadeMelee = event.type == GameplayCombatController::CombatEventType::MonsterMeleeImpact;
    const bool canEvadeProjectile =
        event.type == GameplayCombatController::CombatEventType::PartyProjectileImpact
        && !event.affectsAllParty
        && event.spellId == 0
        && event.damageType == CombatDamageType::Physical;

    if ((!canEvadeMelee && !canEvadeProjectile)
        || characterCombatSkillMastery(character, "Unarmed") < SkillMastery::Grandmaster)
    {
        return false;
    }

    const int unarmedLevel = characterCombatSkillLevel(character, "Unarmed");

    if (unarmedLevel <= 0)
    {
        return false;
    }

    std::mt19937 rng = buildMonsterAttackRng(event, targetMemberIndex, frameTicks ^ 0x9e3779b9u);
    return std::uniform_int_distribution<int>(1, 100)(rng) <= std::min(100, unarmedLevel);
}

int adjustedIncomingDamageForMember(
    const GameplayCombatController::PendingCombatEventContext &context,
    const GameplayCombatController::CombatEvent &event,
    const Character &member,
    size_t memberIndex,
    bool isPhysicalProjectile)
{
    int damage = event.damage;

    if (isPhysicalProjectile && member.halfMissileDamage)
    {
        damage = std::max(1, (damage + 1) / 2);
    }

    std::mt19937 rng = buildMonsterAttackRng(event, memberIndex, animationTicks(context.pRuntime));
    return GameMechanics::resolveCharacterIncomingDamage(
        member,
        context.pRuntime != nullptr ? context.pRuntime->itemTable() : nullptr,
        context.pRuntime != nullptr ? context.pRuntime->standardItemEnchantTable() : nullptr,
        context.pRuntime != nullptr ? context.pRuntime->specialItemEnchantTable() : nullptr,
        damage,
        event.damageType,
        rng);
}

int parameterBonusForCombat(int value)
{
    constexpr int thresholds[29] = {
        500, 400, 350, 300, 275, 250, 225, 200, 175, 150, 125, 100, 75, 50, 40,
        35, 30, 25, 21, 19, 17, 15, 13, 11, 9, 7, 5, 3, 0,
    };
    constexpr int bonuses[29] = {
        30, 25, 21, 19, 17, 15, 13, 11, 9, 7, 5, 4, 3, 2, 1, 0, -1, -2, -3,
        -4, -5, -6, -7, -8, -9, -10, -11, -12, -13,
    };

    for (size_t index = 0; index < std::size(thresholds); ++index)
    {
        if (value >= thresholds[index])
        {
            return bonuses[index];
        }
    }

    return bonuses[std::size(bonuses) - 1];
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

bool isBreakableItemDefinition(const ItemDefinition &itemDefinition)
{
    return itemDefinition.rarity == ItemRarity::Common;
}

bool itemMatchesBreakSpecial(
    const ItemDefinition &itemDefinition,
    MonsterSpecialAttackKind specialAttackKind)
{
    const ItemEnchantCategory category = ItemEnchantRuntime::categoryForItem(itemDefinition);

    switch (specialAttackKind)
    {
        case MonsterSpecialAttackKind::BreakAny:
            return isBreakableItemDefinition(itemDefinition);
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

            if (pItemDefinition != nullptr && !item.broken && itemMatchesBreakSpecial(*pItemDefinition, specialAttackKind))
            {
                candidates.push_back({&item, nullptr, pItemDefinition});
            }
        }

        return candidates;
    }

    constexpr EquipmentSlot slots[] = {
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

    for (EquipmentSlot slot : slots)
    {
        const uint32_t itemId = equippedItemId(member, slot);
        EquippedItemRuntimeState *pRuntimeState = equippedItemRuntimeState(member, slot);
        const ItemDefinition *pItemDefinition = pItemTable->get(itemId);

        if (itemId != 0
            && pRuntimeState != nullptr
            && pItemDefinition != nullptr
            && !pRuntimeState->broken
            && isBreakableItemDefinition(*pItemDefinition)
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
            return parameterBonusForCombat(summary.personality.actual);
        case MonsterSpecialAttackKind::Weak:
        case MonsterSpecialAttackKind::Sleep:
        case MonsterSpecialAttackKind::Drunk:
        case MonsterSpecialAttackKind::DiseaseWeak:
        case MonsterSpecialAttackKind::DiseaseMedium:
        case MonsterSpecialAttackKind::DiseaseSevere:
        case MonsterSpecialAttackKind::Unconscious:
        case MonsterSpecialAttackKind::Aging:
            return parameterBonusForCombat(summary.endurance.actual);
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
            return (parameterBonusForCombat(summary.intellect.actual) + parameterBonusForCombat(summary.personality.actual)) / 2;
        case MonsterSpecialAttackKind::BreakAny:
        case MonsterSpecialAttackKind::BreakArmor:
        case MonsterSpecialAttackKind::BreakWeapon:
            if (pBreakCandidate != nullptr && pBreakCandidate->pItemDefinition != nullptr)
            {
                return 3 * (static_cast<int>(pBreakCandidate->pItemDefinition->rarity) + 1);
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
    const int saveCheck = parameterBonusForCombat(summary.luck.actual)
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

bool shouldApplyMonsterSpecialAttack(
    const GameplayCombatController::CombatEvent &event,
    const GameplayCombatActorInfo &sourceActor,
    std::mt19937 &rng)
{
    if (event.type != GameplayCombatController::CombatEventType::MonsterMeleeImpact
        || event.ability != GameplayActorAttackAbility::Attack1
        || sourceActor.specialAttackKind == MonsterSpecialAttackKind::None
        || sourceActor.specialAttackLevel <= 0
        || sourceActor.monsterLevel <= 0)
    {
        return false;
    }

    const int chancePercent = sourceActor.monsterLevel * sourceActor.specialAttackLevel;
    return chancePercent >= 100 || std::uniform_int_distribution<int>(0, 99)(rng) < chancePercent;
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

    if (!shouldApplyMonsterSpecialAttack(event, sourceActor, rng))
    {
        return false;
    }

    std::vector<BreakItemCandidate> breakCandidates;
    const BreakItemCandidate *pBreakCandidate = nullptr;

    if (sourceActor.specialAttackKind == MonsterSpecialAttackKind::BreakAny
        || sourceActor.specialAttackKind == MonsterSpecialAttackKind::BreakArmor
        || sourceActor.specialAttackKind == MonsterSpecialAttackKind::BreakWeapon)
    {
        breakCandidates = collectBreakItemCandidates(
            *pMember,
            context.pRuntime != nullptr ? context.pRuntime->itemTable() : nullptr,
            sourceActor.specialAttackKind);

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
        context.pRuntime != nullptr ? context.pRuntime->itemTable() : nullptr,
        context.pRuntime != nullptr ? context.pRuntime->standardItemEnchantTable() : nullptr,
        context.pRuntime != nullptr ? context.pRuntime->specialItemEnchantTable() : nullptr);

    if (memberImmuneToMonsterSpecialAttack(summary, sourceActor.specialAttackKind))
    {
        return false;
    }

    if (memberSavesAgainstMonsterSpecialAttack(
            *pMember,
            summary,
            sourceActor.specialAttackKind,
            pBreakCandidate,
            rng))
    {
        return false;
    }

    bool applied = false;
    const std::optional<CharacterCondition> condition =
        conditionForMonsterSpecialAttack(sourceActor.specialAttackKind);

    if (condition)
    {
        applied = context.party.applyMemberCondition(memberIndex, *condition);
    }
    else if (sourceActor.specialAttackKind == MonsterSpecialAttackKind::ManaDrain)
    {
        applied = pMember->spellPoints > 0;
        pMember->spellPoints = 0;
    }
    else if (sourceActor.specialAttackKind == MonsterSpecialAttackKind::Aging)
    {
        ++pMember->ageModifier;
        applied = true;
    }
    else if (pBreakCandidate != nullptr)
    {
        if (pBreakCandidate->pInventoryItem != nullptr)
        {
            applied = !pBreakCandidate->pInventoryItem->broken;
            pBreakCandidate->pInventoryItem->broken = true;
        }
        else if (pBreakCandidate->pEquippedRuntime != nullptr)
        {
            applied = !pBreakCandidate->pEquippedRuntime->broken;
            pBreakCandidate->pEquippedRuntime->broken = true;
        }
    }

    if (applied)
    {
        triggerPortraitFaceAnimation(
            context.pRuntime,
            memberIndex,
            faceAnimationForMonsterSpecialAttack(sourceActor.specialAttackKind));
    }

    return applied;
}

void applyIncomingHitSideEffects(
    GameplayCombatController::PendingCombatEventContext &context,
    size_t memberIndex)
{
    Character *pMember = context.party.member(memberIndex);

    if (pMember == nullptr)
    {
        return;
    }

    context.party.clearMemberCondition(memberIndex, CharacterCondition::Asleep);

    const CharacterSheetSummary summary = GameMechanics::buildCharacterSheetSummary(
        *pMember,
        context.pRuntime != nullptr ? context.pRuntime->itemTable() : nullptr,
        context.pRuntime != nullptr ? context.pRuntime->standardItemEnchantTable() : nullptr,
        context.pRuntime != nullptr ? context.pRuntime->specialItemEnchantTable() : nullptr);
    const int recoveryTicks = 20 - parameterBonusForCombat(summary.endurance.actual);
    context.party.applyRecoveryToMember(memberIndex, recoverySecondsFromTicks(recoveryTicks));
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

    if (context.party.characterBuff(memberIndex, CharacterBuffId::PainReflection) == nullptr)
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
    CombatDamageType damageType)
{
    CombatEvent event = {};
    event.type = CombatEventType::PartyProjectileImpact;
    event.sourceId = sourceId;
    event.damage = damage;
    event.attackBonus = attackBonus;
    event.spellId = spellId;
    event.affectsAllParty = affectsAllParty;
    event.damageType = damageType;
    return event;
}

GameplayCombatController::CombatEvent GameplayCombatController::buildPartyProjectileActorImpactEvent(
    uint32_t sourceId,
    uint32_t sourcePartyMemberIndex,
    uint32_t targetActorId,
    int damage,
    int spellId,
    bool hit,
    bool killed)
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
    return event;
}

std::string GameplayCombatController::formatPartyAttackStatusText(
    const std::string &attackerName,
    const std::string &targetName,
    const CharacterAttackResult &attack,
    bool killed)
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

    if (killed)
    {
        return attackerName + " inflicts " + std::to_string(attack.damage) + " points killing " + targetName;
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
        return attackerName + " shoots " + targetName + " for " + std::to_string(attack.damage) + " points";
    }

    return attackerName + " hits " + targetName + " for " + std::to_string(attack.damage) + " damage";
}

void GameplayCombatController::handlePartyAttackPresentation(
    GameplayScreenRuntime *pRuntime,
    const PartyAttackPresentation &attack)
{
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

    showHitStatus(
        pRuntime,
        formatPartyAttackStatusText(
            attack.attackerName,
            attack.targetName,
            attack.attack,
            attack.killed));
}

void GameplayCombatController::handlePendingCombatEvents(
    PendingCombatEventContext &context,
    const std::vector<CombatEvent> &events)
{
    for (const CombatEvent &event : events)
    {
        if (event.type == CombatEventType::PartyProjectileActorImpact)
        {
            const Character *pSourceMember = context.party.member(event.sourcePartyMemberIndex);
            const std::optional<GameplayCombatActorInfo> targetActor = resolveActor(context, event.targetActorId);
            const std::string sourceName =
                pSourceMember != nullptr && !pSourceMember->name.empty() ? pSourceMember->name : "party";
            const std::string targetName = targetActor ? targetActor->displayName : "monster";

            if (!event.hit)
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

                showHitStatus(
                    context.pRuntime,
                    sourceName + " inflicts " + std::to_string(event.damage) + " points killing " + targetName);
            }
            else
            {
                triggerPortraitFaceAnimation(
                    context.pRuntime,
                    event.sourcePartyMemberIndex,
                    FaceAnimationId::AttackHit);
                playSpeechReaction(context.pRuntime, event.sourcePartyMemberIndex, SpeechId::AttackHit, false);

                showHitStatus(
                    context.pRuntime,
                    sourceName + " shoots " + targetName + " for " + std::to_string(event.damage) + " points");
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

        if (!event.affectsAllParty)
        {
            targetMemberIndex = context.party.chooseMonsterAttackTarget(
                sourceAttackPreferences,
                event.sourceId ^ static_cast<uint32_t>(event.damage) ^ static_cast<uint32_t>(event.spellId));
        }

        Character *pTargetMember = targetMemberIndex ? context.party.member(*targetMemberIndex) : nullptr;
        const bool needsArmorHitRoll = monsterImpactRequiresArmorHitRoll(event, sourceActor);

        if (needsArmorHitRoll && targetMemberIndex.has_value() && sourceActor
            && !monsterImpactHitsMember(context, event, *sourceActor, *targetMemberIndex))
        {
            continue;
        }

        const bool ignorePhysicalDamage =
            pTargetMember != nullptr
            && pTargetMember->physicalDamageImmune
            && event.damageType == CombatDamageType::Physical;

        if (ignorePhysicalDamage)
        {
            continue;
        }

        const bool isPhysicalProjectile =
            event.type == CombatEventType::PartyProjectileImpact && event.damageType == CombatDamageType::Physical;
        bool damagedParty = false;
        std::vector<DamagedMember> damagedMembers;

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
                    continue;
                }

                if (characterEvadesMonsterImpact(
                        *pMember,
                        event,
                        memberIndex,
                        animationTicks(context.pRuntime)))
                {
                    showHitStatus(context.pRuntime, pMember->name + " evades damage");
                    continue;
                }

                const int adjustedDamage =
                    adjustedIncomingDamageForMember(context, event, *pMember, memberIndex, isPhysicalProjectile);
                const bool applied = context.party.applyDamageToMember(memberIndex, adjustedDamage, "", true);
                damagedParty = applied || damagedParty;

                if (applied)
                {
                    damagedMembers.push_back({memberIndex, adjustedDamage});
                }
            }
        }
        else
        {
            const int adjustedDamage =
                pTargetMember != nullptr && targetMemberIndex
                    ? adjustedIncomingDamageForMember(
                        context,
                        event,
                        *pTargetMember,
                        *targetMemberIndex,
                        isPhysicalProjectile)
                    : event.damage;
            const bool evaded =
                pTargetMember != nullptr && targetMemberIndex
                    ? characterEvadesMonsterImpact(
                        *pTargetMember,
                        event,
                        *targetMemberIndex,
                        animationTicks(context.pRuntime))
                    : false;

            if (evaded)
            {
                showHitStatus(context.pRuntime, pTargetMember->name + " evades damage");
            }

            damagedParty = targetMemberIndex
                ? (!evaded && context.party.applyDamageToMember(*targetMemberIndex, adjustedDamage, ""))
                : false;

            if (damagedParty && targetMemberIndex.has_value())
            {
                damagedMembers.push_back({*targetMemberIndex, adjustedDamage});
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
                    applyMonsterSpecialAttack(context, event, *sourceActor, damagedMember.memberIndex);
                }
            }

            if (event.affectsAllParty)
            {
                triggerPortraitFaceAnimationForAllLivingMembers(context.pRuntime, FaceAnimationId::DamagedParty);
            }
            else
            {
                triggerPortraitFaceAnimation(context.pRuntime, *targetMemberIndex, FaceAnimationId::Damaged);
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
    m_pendingCombatEvents.push_back(
        buildPartyProjectileImpactEvent(sourceId, damage, attackBonus, spellId, affectsAllParty, damageType));
}

void GameplayCombatController::recordPartyProjectileActorImpact(
    uint32_t sourceId,
    uint32_t sourcePartyMemberIndex,
    uint32_t targetActorId,
    int damage,
    int spellId,
    bool hit,
    bool killed)
{
    m_pendingCombatEvents.push_back(
        buildPartyProjectileActorImpactEvent(
            sourceId,
            sourcePartyMemberIndex,
            targetActorId,
            damage,
            spellId,
            hit,
            killed));
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
