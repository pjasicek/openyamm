#pragma once

#include "game/gameplay/GameMechanics.h"
#include "game/rules/ActorRulesetFacts.h"
#include "game/rules/DamagePipeline.h"

#include <cstdint>
#include <optional>
#include <random>
#include <string>

namespace OpenYAMM::Game
{
struct Character;
class IGameplayWorldRuntime;
class Party;
class ItemTable;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;
struct SpellEntry;

// A hit on a monster, before its resistances.
struct MonsterDamageHit
{
    int amount = 0;
    CombatDamageType type = CombatDamageType::Physical;
    // The monster's resistance to `type`; weapon hits use `resistances` instead.
    int resistance = 0;
    // A weapon's elemental additions, each resisted by its own element.
    std::optional<ElementalDamageBonuses> weaponElements;
    // Rules pipeline scratch: the additions after their resistances, held until a later stage adds them (MAW adds
    // them after the boss affixes).
    double resistedAdditions = 0;
    // A weapon blow's damage the rules add after their other stages, by damage type (CharacterAttackResult::
    // rulesLateDamage).
    std::array<int, CombatDamageTypeCount> lateDamage = {};
    MonsterDamageResistances resistances;
    int hourOfPowerResistanceBonus = 0;
    // What the ruleset resolved for the monster hit, and for the monster that hit it (monster against monster).
    ActorRulesetFacts targetFacts;
    ActorRulesetFacts attackerFacts;
    // A party member's weapon blow: who struck and the item table to read their weapons (null for every other hit).
    const Character *pMeleeAttacker = nullptr;
    const ItemTable *pItemTable = nullptr;
    // The struck monster's HP before the blow.
    int targetCurrentHp = 0;
    // A party member's missile or spell (null for every other hit): who sent it and its spell, 0 for an arrow or a
    // shot; the item table and the HP above are set with it.
    const Character *pMissileAttacker = nullptr;
    uint32_t missileSpellId = 0;
    std::mt19937 *pRng = nullptr;
    bool stop = false;
};

// A party member's missile or spell reaching a monster, for resolveDamageToMonster (no attacker: another hit).
struct PartyMissileSource
{
    const Character *pAttacker = nullptr;
    const ItemTable *pItemTable = nullptr;
    uint32_t spellId = 0;
    int targetCurrentHp = 0;
    // The struck monster's every resistance (MAW: a dragon's breath takes the lowest).
    MonsterDamageResistances resistances;
    // An arrow's elemental damage from its bow, which joins the hit, and the hit's elemental parts, each resisted by
    // its own element (GameplayProjectileService::addPartyArrowElements).
    int addedElementalDamage = 0;
    std::optional<ElementalDamageBonuses> weaponElements;
};

// A monster's attack reaching a party member, before it lands.
// What the rules do with a monster's missile attack (not a spell), by its missile token ("Fire", "Arrow"...).
struct MonsterMissileRules
{
    // The monster's special attack (poison, death...) does not ride on the missile.
    bool noSpecialAttack = false;
    // A struck member's Pain Reflection does not send it back.
    bool noPainReflection = false;
    // It strikes a conscious member at random instead of the monster's choice.
    bool randomTarget = false;
    // The member's Speed is rolled a second time against it.
    bool secondSpeedRoll = false;
};

struct MonsterAttackOnCharacter
{
    const Character *pCharacter = nullptr;
    const ItemTable *pItemTable = nullptr;
    const StandardItemEnchantTable *pStandardItemEnchantTable = nullptr;
    const SpecialItemEnchantTable *pSpecialItemEnchantTable = nullptr;
    CombatDamageType type = CombatDamageType::Physical;
    // A melee blow; otherwise a missile or a spell (spellId), which may hit the whole party.
    bool melee = false;
    int spellId = 0;
    // A missile attack's token ("Fire", "Arrow"); empty for blows and spells.
    std::string missileToken;
    bool affectsAllParty = false;
    int monsterLevel = 0;
    // What the ruleset resolved for the attacker, when known.
    const ActorRulesetFacts *pAttackerFacts = nullptr;
    int partyCount = 1;
    // The attacker's armour-roll inputs: the target's armour class as the attack sees it, and the attack bonus.
    int armorClass = 0;
    int attackBonus = 0;
    std::mt19937 *pRng = nullptr;
};

// Names a map actor for the rules' per-monster runtime state (MAW's diminishing returns).
uint64_t mapActorKey(const std::string &mapName, size_t actorIndex);

// A party member's weapon attack as the engine resolved it, and what the rules need to decide it again.
struct CharacterAttackOnMonster
{
    const Character *pCharacter = nullptr;
    const ItemTable *pItemTable = nullptr;
    const StandardItemEnchantTable *pStandardItemEnchantTable = nullptr;
    const SpecialItemEnchantTable *pSpecialItemEnchantTable = nullptr;
    // The damage range of the attack's mode.
    int minimumDamage = 0;
    int maximumDamage = 0;
    // The target's ruleset facts; null when the attack has no target yet (a missile finds one on impact).
    const ActorRulesetFacts *pTargetFacts = nullptr;
    int targetCurrentHp = 0;
    // The target's monster kinds (MonsterKind flags), for weapons that hurt some kinds more.
    uint32_t targetKindFlags = 0;
    // The target as mapActorKey names it, and the world clock in real seconds, for diminishing returns.
    uint64_t targetKey = 0;
    double nowSeconds = 0.0;
    // Living monsters within 384 of a melee blow's target, the target included (MAW's Assassination); 0 when unknown.
    int monstersNearTarget = 0;
    // Whether the target is hostile to the party (a hit with friendly fire on is not; MAW's Assassination).
    bool targetHostile = true;
    bool sparring = false;
    int partyCount = 1;
    std::mt19937 *pRng = nullptr;
};

// A party member's hit that landed on a monster.
struct PartyHitOnMonster
{
    size_t memberIndex = 0;
    const ActorRulesetFacts *pTarget = nullptr;
    int damage = 0;
    // The part of a weapon blow's damage its enchantments and Fire Aura added.
    int elementalDamage = 0;
    CombatDamageType type = CombatDamageType::Physical;
    // A weapon blow; otherwise a missile, a spell's when spellId is set.
    bool melee = false;
    uint32_t spellId = 0;
    bool killed = false;
    // The world and the actor hit, for effects on the monster (null when not known).
    IGameplayWorldRuntime *pWorld = nullptr;
    std::optional<size_t> targetActorIndex;
};

// A party member's missile reaching a monster.
struct CharacterMissileOnMonster
{
    int attackBonus = 0;
    int targetArmorClass = 0;
    float targetDistance = 0.0f;
    ActorRulesetFacts targetFacts;
    int partyCount = 1;
    // The member who fired it, while in the party.
    const Character *pShooter = nullptr;
    std::mt19937 *pRng = nullptr;
};

// A party member's damage spell, before it reaches a target.
struct CharacterSpellCast
{
    const Character *pCaster = nullptr;
    const ItemTable *pItemTable = nullptr;
    const StandardItemEnchantTable *pStandardItemEnchantTable = nullptr;
    const SpecialItemEnchantTable *pSpecialItemEnchantTable = nullptr;
    const SpellEntry *pSpell = nullptr;
    SkillMastery mastery = SkillMastery::None;
    uint32_t skillLevel = 0;
    int partyCount = 1;
    // The monster the cast names, when it names one: its level and the living monsters within 384 of it, itself
    // included (MAW's class spells crit against it and thin an Assassin's bonus by the crowd); 0 when unknown.
    int targetLevel = 0;
    int monstersNearTarget = 0;
    // Read from a scroll: the scroll's skill and mastery, not the reader's.
    bool fromScroll = false;
};

// The monster a party spell lands on, for spells that read it (Mass Distortion).
struct SpellTargetState
{
    int currentHp = 0;
    int maxHp = 0;
    // What the ruleset resolved for the monster, or null.
    const ActorRulesetFacts *pFacts = nullptr;
};

// A hit on a party member, before their resistances and armour.
struct CharacterDamageHit
{
    int amount = 0;
    CombatDamageType type = CombatDamageType::Physical;
    const Character *pCharacter = nullptr;
    const ItemTable *pItemTable = nullptr;
    const StandardItemEnchantTable *pStandardItemEnchantTable = nullptr;
    const SpecialItemEnchantTable *pSpecialItemEnchantTable = nullptr;
    // A monster's attack (traps and other sources skip the attack-only stages); a missile when physicalProjectile.
    bool monsterAttack = false;
    bool physicalProjectile = false;
    // A monster attack's source: its level and ruleset facts, which attack it was, and the damage it rolled before a
    // personal shield took its share (amount is what passed the shield).
    int attackerLevel = 0;
    ActorRulesetFacts attackerFacts;
    // The attacker's hit points now and at most (MAW's Berserker bosses); 0 when unknown.
    int attackerCurrentHp = 0;
    int attackerMaxHp = 0;
    bool attack2 = false;
    int spellId = 0;
    int rolledAmount = 0;
    // Shrinking Ray or Dark Grasp held the attacker.
    bool attackerDebuffed = false;
    // A party of one covered the hit (MAW's Cover halves it instead of moving it).
    bool coverHalved = false;
    int partyCount = 1;
    std::mt19937 *pRng = nullptr;
    bool stop = false;
};

// A monster's single-target attack about to land on a party member, before anyone covers it.
struct MonsterAttackCover
{
    size_t targetIndex = 0;
    bool spell = false;
    CombatDamageType type = CombatDamageType::Physical;
    std::mt19937 *pRng = nullptr;
};

// Who takes a covered attack: another member, or the target itself at half the hit (a party of one).
struct CoverOutcome
{
    size_t memberIndex = 0;
    bool halved = false;
};

// A party member's hit on a monster, as the status line tells it.
struct PartyHitStatus
{
    std::string attackerName;
    std::string targetName;
    int damage = 0;
    bool killed = false;
    bool critical = false;
    // An arrow, bolt or shot rather than a blow.
    bool missile = false;
    // The spell that dealt it (0 for a blow or a missile); how many monsters it hit at once, `damage` being their total.
    uint32_t spellId = 0;
    int monstersHit = 1;
};

// How damage is resolved (devdocs/maw/HANDOFF.md §3.5-3.6). This class builds the Standard MMMerge stages; a ruleset
// that changes combat derives from it and builds its own lists. Each hit is written stage by stage to the combat
// trace when that is enabled.
class CombatRules
{
public:
    CombatRules();
    virtual ~CombatRules() = default;

    int damageToMonster(MonsterDamageHit &hit, bool recordCombatLog = true) const;
    int damageToCharacter(CharacterDamageHit &hit, bool recordCombatLog = true) const;
    // Whether a monster's melee blow or arrow passes the target's armour (Standard: level and attack bonus against
    // armour class).
    virtual bool monsterAttackLands(const MonsterAttackOnCharacter &attack) const;
    // Whether the target avoids an attack that landed (Standard: Grandmaster Unarmed).
    virtual bool characterEvades(const MonsterAttackOnCharacter &attack) const;
    // Lets a ruleset decide a party member's weapon attack again: hit, damage, crit and recovery. Standard keeps the
    // engine's attack.
    virtual void resolveCharacterAttack(CharacterAttackResult &attack, const CharacterAttackOnMonster &context) const;
    // The recovery ticks of a party member's weapon attack as the rules decide it, for the character sheet; nothing
    // when the engine's own recovery applies (Standard).
    virtual std::optional<int> characterAttackRecoveryTicks(
        const Character &character,
        CharacterAttackMode mode,
        const ItemTable &itemTable,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable) const;
    // Whether a party member's missile hits the monster it reached (Standard: attack bonus against armour class and
    // distance).
    virtual bool characterMissileHits(const CharacterMissileOnMonster &missile) const;
    // Damage from no monster (map event traps, hazards) as a party member takes it; Standard takes the event's number.
    virtual int environmentDamage(
        const Party &party,
        size_t memberIndex,
        int damage,
        CombatDamageType type,
        bool indoor) const;
    // How fast a party member's missile turns toward the actor it was aimed at, in radians per second; 0 (Standard)
    // flies straight.
    virtual float partyMissileHomingTurnRate() const;
    // Whether bows, crossbows, thrown weapons and a dragon's breath stay silent, so the party's attack is the melee one
    // at its pace (MAW's Bow preference, disableBow). Standard: no.
    virtual bool bowDisabled() const;
    // How fast, in radians a second, the party may move across the flight of a monster's missile of this spell
    // (0: an attack) and still have it re-aim at the party; 0 (Standard) flies straight.
    virtual float monsterMissileHomingLockRate(uint32_t spellId) const;
    // What a monster's Pain Reflection sends back to the member whose `damage` it took. Standard: all of it; MAW: the
    // hit mitigated as an ordinary hit of its kind, then ^0.85 (Damage.lua:1593-1598).
    virtual int reflectedDamage(const Party &party, size_t memberIndex, int damage, CombatDamageType type) const;
    // How a monster's missile attack of this token is handled. Standard: as any attack. MAW (its default "M&M6
    // Projectiles"): elemental missiles bypass the engine's hit, so no special attack, no Pain Reflection and a
    // random conscious target; arrows and Body, Mind and Spirit missiles pass the engine's Speed roll and the
    // pipeline's (zzMaw-Monsters.lua:3809-4008, zzMaw_MonsterHit.lua:12-31; OVR2-2-1, FMON-2-1).
    virtual MonsterMissileRules monsterMissileRules(const std::string &missileToken) const;
    // The share of a melee blow's recovery its member keeps when the blow killed (MAW's Legendary 11: half).
    // Standard: all of it.
    virtual float killRecoveryScale(const Character &killer) const;
    // Whether Lifedrain heals its caster a third of the health it drained. Standard: yes; MAW swaps the hit's spell
    // to 200 so the engine's heal never runs (SP:3781-3790) and leeches through its own rules instead.
    virtual bool lifedrainHealsCasterThird() const;
    // Whether a weapon's "x2 against a kind of monster" (artifacts, relics, the slaying enchantments) multiplies the
    // whole blow or arrow. Standard: yes; MAW rebuilds every hit and gives the artifacts' versus damage on their
    // on-hit part only.
    virtual bool weaponKindMultiplierApplies() const;
    // Whether a blow or an arrow gains its own weapons' elemental enchantment and artifact damage, rolled for each hit
    // and resisted by its element (ItemEnchantRuntime::rollCharacterAttackElementalDamage). Standard: yes; MAW builds
    // each hit's additions in resolveCharacterAttack.
    virtual bool addsWeaponElementalDamage() const;
    // A party spell whose damage the world rolls itself (a Fire Spike trap, Armageddon on the monsters), when the rules
    // roll it as the spell instead (MAW: rollSpellDamage at the caster's stored skill and mastery, SPL-5, SPL-6).
    // Standard: none, the world's own roll.
    virtual std::optional<int> worldSpellDamage(const CharacterSpellCast &cast) const;
    // A damage spell's roll: the table's base plus its dice per skill point at the cast mastery. pCritical, when given,
    // learns whether the roll was a critical hit (Standard: never).
    virtual int rollSpellDamage(const CharacterSpellCast &cast, bool *pCritical = nullptr) const;
    // A spell whose damage is a share of its target's hit points (Mass Distortion): the damage on this target, or
    // nothing for the roll above. Standard: 25 % of the target's current hit points plus 2 % per skill point.
    virtual std::optional<int> spellDamageOnTarget(const CharacterSpellCast &cast, const SpellTargetState &target) const;
    // The mastery a party spell projectile carries on to the next monster after a hit (MAW's Chain Lightning), or
    // nothing when it stops there. Standard: nothing.
    virtual std::optional<SkillMastery> spellChainMastery(int spellId, SkillMastery mastery) const;
    // The party member a monster's single-target attack goes for, when the rules decide it (MAW's Fixator bosses);
    // otherwise the monster's attack preferences choose.
    virtual std::optional<size_t> monsterAttackTarget(const Party &party, const ActorRulesetFacts &attacker) const;
    // What a party member's hit on a monster does back to them after it landed (MAW's Thorn and Reflecting bosses).
    // Standard: nothing.
    virtual void applyPartyHitEffects(Party &party, const PartyHitOnMonster &hit) const;
    // Whether applyPartyHitEffects does anything, so callers skip building its hit (finding the actor) when not.
    // Standard: no.
    virtual bool usesPartyHitEffects() const;
    // Whether the attack's caller halves a Weak member's missile of this mode after resolveCharacterAttack. Standard:
    // yes; MAW: not for bows and blasters, whose attack halves the shot's own roll and leaves the add-ons whole
    // (CMB-16).
    virtual bool callerHalvesWeakMissile(CharacterAttackMode mode) const;
    // Whether a monster under Shield halves a party member's missile of this spell (0: an arrow or a shot). Standard:
    // yes; MAW: not arrows and shots, whose damage its own pipeline rebuilds (DM:420-449, CMB-21).
    virtual bool monsterShieldHalvesPartyMissile(uint32_t spellId) const;
    // Whether the party's protections keep a monster's special attack from giving a member this condition beyond
    // Protection from Magic's own list (MAW's keeps members conscious), without spending anything. Standard: no.
    virtual bool blocksMonsterCondition(const Party &party, CharacterCondition condition) const;
    // Whether a monster's special attack lands although the member saved against it (MAW: a dimension map's affix).
    // Standard: never.
    virtual bool piercesConditionSave(const Party &party) const;
    // Whether no special attack of a monster (conditions, drains, breaks) takes hold on this member. Standard: no.
    virtual bool immuneToMonsterSpecialAttacks(const Character &member) const;
    // Whether the party's hits hurt monsters that are not hostile to it (MAW's friendly-fire preference). Standard:
    // always.
    virtual bool harmsFriendlyActors() const;
    // Whether a party hit on the actor is turned aside before it lands; the rules may move monsters through the world
    // (MAW's Swapper bosses swap places with the other monsters instead). Standard: never.
    virtual bool deflectsPartyHit(IGameplayWorldRuntime &world, size_t actorIndex) const;
    // The share of physical damage Mist Form lets through: Standard 0 (immunity).
    virtual float mistFormPhysicalShare() const;
    // How far the party may walk from where a turn-based movement phase began before it ends. Standard: no limit,
    // only the phase's time.
    virtual std::optional<float> turnBasedWalkLimit() const;
    // The damage type of a party member's spell missile, from the spell table's (Standard keeps it).
    virtual CombatDamageType partySpellDamageType(uint32_t spellId, CombatDamageType tableType) const;
    // Who takes a single-target monster attack instead of its target (MAW's Cover). Standard: nobody.
    virtual std::optional<CoverOutcome> coverMonsterAttack(Party &party, const MonsterAttackCover &attack) const;
    // The part of a hit that reaches the member's HP after the rules' own shields, which may spend the member's
    // spell points (MAW's Mana Shield). Standard: all of it.
    virtual int absorbCharacterDamage(Party &party, size_t memberIndex, int damage, bool preview = false) const;
    // After a hit took a member's HP (MAW: a deep overkill kills or eradicates). Standard: nothing.
    virtual void characterDamaged(Party &party, size_t memberIndex) const;
    // Each frame of play: combat state that lapses with time (MAW's Retaliation stacks). Standard: none.
    virtual void updateCombat(Party &party, IGameplayWorldRuntime &world, float deltaSeconds) const;
    // A condition landed on a member (again or for the first time). Standard: nothing.
    virtual void characterConditionApplied(Party &party, size_t memberIndex, CharacterCondition condition) const;
    // What else a monster's hit does to the party after its damage landed (MAW boss affixes); the attacker's actor id
    // finds it in the world. Standard: nothing.
    virtual void applyMonsterHitEffects(
        Party &party,
        IGameplayWorldRuntime *pWorld,
        size_t memberIndex,
        const ActorRulesetFacts &attacker,
        uint32_t attackerActorId,
        int appliedDamage,
        CombatDamageType type) const;
    // The status line of a party member's hit (MAW: the spell named as the attacker, "(CRIT!)", an area spell's
    // total). Standard: none, the engine's own line.
    virtual std::optional<std::string> partyHitStatusText(const PartyHitStatus &status) const;
    const DamagePipeline<MonsterDamageHit> &damageToMonsterStages() const;
    const DamagePipeline<CharacterDamageHit> &damageToCharacterStages() const;

protected:
    // For rulesets that build their own stage lists.
    struct NoStages
    {
    };
    explicit CombatRules(NoStages);

    DamagePipeline<MonsterDamageHit> m_damageToMonster;
    DamagePipeline<CharacterDamageHit> m_damageToCharacter;
};

// A hit on a monster that is not a weapon swing, through the rules' stages.
int resolveDamageToMonster(
    const CombatRules &rules,
    int damage,
    CombatDamageType type,
    int resistance,
    int hourOfPowerResistanceBonus,
    std::mt19937 &rng,
    const ActorRulesetFacts &targetFacts,
    const ActorRulesetFacts &attackerFacts = {},
    const PartyMissileSource &missileSource = {});
}
