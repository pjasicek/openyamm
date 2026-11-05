#include "game/rules/CombatRules.h"

#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/CombatLog.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"
#include "game/tables/SpellTable.h"

#include <algorithm>
#include <cmath>
#include <functional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
// The stages go to the combat trace and to the combat log while either is on; with both off nothing is recorded.
template <typename Hit>
int runRecorded(const DamagePipeline<Hit> &pipeline, Hit &hit, bool onCharacter)
{
    CombatLog *pLog = boundCombatLog();
    const bool logging = pLog != nullptr && pLog->recording();

    if (!gameplayCombatTraceEnabled() && !logging)
    {
        return pipeline.run(hit);
    }

    std::vector<DamageStageRecord> record;
    const int amount = pipeline.run(hit, &record);

    if (logging)
    {
        pLog->recordStages(onCharacter, amount, record);
    }

    if (gameplayCombatTraceEnabled())
    {
        std::string line = std::string("damage_stages target=") + (onCharacter ? "character" : "monster");

        for (const DamageStageRecord &stage : record)
        {
            line += " " + stage.stage + "=" + std::to_string(stage.before) + "->" + std::to_string(stage.after);
        }

        gameplayCombatTraceWrite(line);
    }

    return amount;
}
}

CombatRules::CombatRules()
{
    m_damageToMonster.add(
        "resistance",
        [](MonsterDamageHit &hit)
        {
            hit.amount = hit.weaponElements
                ? GameMechanics::resolveMonsterIncomingWeaponDamage(
                      hit.amount,
                      hit.type,
                      *hit.weaponElements,
                      hit.resistances,
                      hit.hourOfPowerResistanceBonus,
                      *hit.pRng)
                : GameMechanics::resolveMonsterIncomingDamage(
                      hit.amount,
                      hit.type,
                      hit.resistance,
                      hit.hourOfPowerResistanceBonus,
                      *hit.pRng);
        });

    // A character with half missile damage (a Shield effect) takes half of a physical missile.
    m_damageToCharacter.add(
        "missile-shield",
        [](CharacterDamageHit &hit)
        {
            if (hit.monsterAttack && hit.physicalProjectile && hit.pCharacter->halfMissileDamage)
            {
                hit.amount = GameMechanics::resolveShieldedPhysicalProjectileDamage(hit.amount);
            }
        });
    m_damageToCharacter.add(
        "physical-taken",
        [](CharacterDamageHit &hit)
        {
            if (hit.monsterAttack && hit.type == CombatDamageType::Physical)
            {
                hit.amount = std::max(0, static_cast<int>(std::round(
                    static_cast<float>(hit.amount) * hit.pCharacter->physicalDamageTakenMultiplier)));
            }
        });
    m_damageToCharacter.add(
        "resistance-and-armor",
        [](CharacterDamageHit &hit)
        {
            hit.amount = GameMechanics::resolveCharacterIncomingDamage(
                *hit.pCharacter,
                hit.pItemTable,
                hit.pStandardItemEnchantTable,
                hit.pSpecialItemEnchantTable,
                hit.amount,
                hit.type,
                *hit.pRng);
        });
}

CombatRules::CombatRules(NoStages)
{
}

bool CombatRules::monsterAttackLands(const MonsterAttackOnCharacter &attack) const
{
    return GameMechanics::monsterAttackHitsArmorClass(
        attack.armorClass,
        attack.monsterLevel,
        attack.attackBonus,
        *attack.pRng);
}

bool CombatRules::characterEvades(const MonsterAttackOnCharacter &attack) const
{
    const bool singlePhysicalMissile =
        !attack.melee && !attack.affectsAllParty && attack.spellId == 0 && attack.type == CombatDamageType::Physical;
    const CharacterSkill *pUnarmed = attack.pCharacter->findSkill("Unarmed");

    if ((!attack.melee && !singlePhysicalMissile)
        || pUnarmed == nullptr
        || pUnarmed->mastery < SkillMastery::Grandmaster)
    {
        return false;
    }

    const int unarmedLevel = int(pUnarmed->level) + attack.pCharacter->skillBonus("Unarmed");

    if (unarmedLevel <= 0)
    {
        return false;
    }

    return std::uniform_int_distribution<int>(1, 100)(*attack.pRng) <= std::min(100, unarmedLevel);
}

uint64_t mapActorKey(const std::string &mapName, size_t actorIndex)
{
    return std::hash<std::string>{}(mapName) ^ (uint64_t(actorIndex) << 40);
}

void CombatRules::resolveCharacterAttack(CharacterAttackResult &, const CharacterAttackOnMonster &) const
{
}

int CombatRules::rollSpellDamage(const CharacterSpellCast &cast, bool *pCritical) const
{
    if (pCritical != nullptr)
    {
        *pCritical = false;
    }

    const SpellMasteryNumbers numbers = spellNumbersAtMastery(*cast.pSpell, cast.mastery);

    if (cast.skillLevel == 0)
    {
        return std::max(0, numbers.damageBase);
    }

    if (numbers.damageDiceMin == numbers.damageDiceMax)
    {
        return std::max(0, numbers.damageBase + numbers.damageDiceMax * static_cast<int>(cast.skillLevel));
    }

    static thread_local std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<int> distribution(numbers.damageDiceMin, numbers.damageDiceMax);
    int damage = numbers.damageBase;

    for (uint32_t rollIndex = 0; rollIndex < cast.skillLevel; ++rollIndex)
    {
        damage += distribution(rng);
    }

    return std::max(0, damage);
}

bool CombatRules::weaponKindMultiplierApplies() const
{
    return true;
}

std::optional<int> CombatRules::worldSpellDamage(const CharacterSpellCast &) const
{
    return std::nullopt;
}

bool CombatRules::usesPartyHitEffects() const
{
    return false;
}

bool CombatRules::callerHalvesWeakMissile(CharacterAttackMode) const
{
    return true;
}

bool CombatRules::monsterShieldHalvesPartyMissile(uint32_t) const
{
    return true;
}

bool CombatRules::lifedrainHealsCasterThird() const
{
    return true;
}

float CombatRules::killRecoveryScale(const Character &) const
{
    return 1.0f;
}

MonsterMissileRules CombatRules::monsterMissileRules(const std::string &) const
{
    return {};
}

int CombatRules::reflectedDamage(const Party &, size_t, int damage, CombatDamageType) const
{
    return damage;
}

std::optional<int> CombatRules::spellDamageOnTarget(const CharacterSpellCast &cast, const SpellTargetState &target) const
{
    // Mass Distortion takes 25 % of the target's current hit points plus 2 % per skill point.
    if (cast.pSpell == nullptr || cast.pSpell->id != int(SpellId::MassDistortion))
    {
        return std::nullopt;
    }

    return std::max(1, int(std::round(float(target.currentHp) * (0.25f + 0.02f * float(cast.skillLevel)))));
}

std::optional<SkillMastery> CombatRules::spellChainMastery(int, SkillMastery) const
{
    return std::nullopt;
}

int CombatRules::environmentDamage(const Party &, size_t, int damage, CombatDamageType, bool) const
{
    return damage;
}

float CombatRules::partyMissileHomingTurnRate() const
{
    return 0.0f;
}

bool CombatRules::bowDisabled() const
{
    return false;
}

float CombatRules::monsterMissileHomingLockRate(uint32_t) const
{
    return 0.0f;
}

std::optional<size_t> CombatRules::monsterAttackTarget(const Party &, const ActorRulesetFacts &) const
{
    return std::nullopt;
}

std::optional<CoverOutcome> CombatRules::coverMonsterAttack(Party &, const MonsterAttackCover &) const
{
    return std::nullopt;
}

int CombatRules::absorbCharacterDamage(Party &, size_t, int damage) const
{
    return damage;
}

void CombatRules::characterDamaged(Party &, size_t) const
{
}

void CombatRules::updateCombat(Party &, IGameplayWorldRuntime &, float) const
{
}

void CombatRules::characterConditionApplied(Party &, size_t, CharacterCondition) const
{
}

void CombatRules::applyMonsterHitEffects(
    Party &,
    IGameplayWorldRuntime *,
    size_t,
    const ActorRulesetFacts &,
    uint32_t,
    int,
    CombatDamageType) const
{
}

std::optional<std::string> CombatRules::partyHitStatusText(const PartyHitStatus &) const
{
    return std::nullopt;
}

bool CombatRules::blocksMonsterCondition(const Party &, CharacterCondition) const
{
    return false;
}

bool CombatRules::piercesConditionSave(const Party &) const
{
    return false;
}

bool CombatRules::immuneToMonsterSpecialAttacks(const Character &) const
{
    return false;
}

bool CombatRules::harmsFriendlyActors() const
{
    return true;
}

bool CombatRules::deflectsPartyHit(IGameplayWorldRuntime &, size_t) const
{
    return false;
}

float CombatRules::mistFormPhysicalShare() const
{
    return 0.0f;
}

std::optional<float> CombatRules::turnBasedWalkLimit() const
{
    return std::nullopt;
}

CombatDamageType CombatRules::partySpellDamageType(uint32_t, CombatDamageType tableType) const
{
    return tableType;
}

void CombatRules::applyPartyHitEffects(Party &, const PartyHitOnMonster &) const
{
}

std::optional<int> CombatRules::characterAttackRecoveryTicks(
    const Character &,
    CharacterAttackMode,
    const ItemTable &,
    const StandardItemEnchantTable *,
    const SpecialItemEnchantTable *) const
{
    return std::nullopt;
}

bool CombatRules::characterMissileHits(const CharacterMissileOnMonster &missile) const
{
    return GameMechanics::characterRangedAttackHitsArmorClass(
        missile.targetArmorClass,
        missile.attackBonus,
        missile.targetDistance,
        *missile.pRng);
}

int CombatRules::damageToMonster(MonsterDamageHit &hit) const
{
    return runRecorded(m_damageToMonster, hit, false);
}

int CombatRules::damageToCharacter(CharacterDamageHit &hit) const
{
    return runRecorded(m_damageToCharacter, hit, true);
}

const DamagePipeline<MonsterDamageHit> &CombatRules::damageToMonsterStages() const
{
    return m_damageToMonster;
}

const DamagePipeline<CharacterDamageHit> &CombatRules::damageToCharacterStages() const
{
    return m_damageToCharacter;
}

int resolveDamageToMonster(
    const CombatRules &rules,
    int damage,
    CombatDamageType type,
    int resistance,
    int hourOfPowerResistanceBonus,
    std::mt19937 &rng,
    const ActorRulesetFacts &targetFacts,
    const ActorRulesetFacts &attackerFacts,
    const PartyMissileSource &missileSource)
{
    MonsterDamageHit hit = {};

    if (missileSource.pAttacker != nullptr)
    {
        hit.pMissileAttacker = missileSource.pAttacker;
        hit.missileSpellId = missileSource.spellId;
        hit.pItemTable = missileSource.pItemTable;
        hit.targetCurrentHp = missileSource.targetCurrentHp;
        hit.resistances = missileSource.resistances;
    }

    hit.amount = damage;
    hit.type = type;
    hit.resistance = resistance;
    hit.hourOfPowerResistanceBonus = hourOfPowerResistanceBonus;
    hit.targetFacts = targetFacts;
    hit.attackerFacts = attackerFacts;
    hit.pRng = &rng;
    return rules.damageToMonster(hit);
}
}
