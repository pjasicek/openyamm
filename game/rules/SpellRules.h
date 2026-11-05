#pragma once

#include "game/party/EventSpellBuffs.h"
#include "game/rules/AuraReport.h"
#include "game/rules/CombatRules.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class Party;
struct ActorRulesetFacts;
struct SpellEntry;
class SpellTable;

// A buff spell cast under rules that make buffs auras (MAW).
enum class AuraCastResult : uint8_t
{
    // The caster holds the aura now.
    Held,
    // The holder cast it again and let it go.
    Released,
    // The caster's mana pool cannot cover the aura's reservation.
    NotEnoughMana,
};

// A party member's crowd-control spell landing on a monster.
struct CrowdControlCast
{
    uint32_t spellId = 0;
    SkillMastery mastery = SkillMastery::None;
    uint32_t skillLevel = 0;
    const Character *pCaster = nullptr;
    // The monster's resistance to the spell, its level, whether it is a boss, and a key naming it on its map.
    int resistance = 0;
    int targetLevel = 0;
    bool boss = false;
    // What the ruleset resolved for the monster, when known.
    const ActorRulesetFacts *pTargetFacts = nullptr;
    uint64_t targetKey = 0;
    size_t partySize = 1;
    // The world clock in real seconds, for diminishing returns.
    double nowSeconds = 0.0;
};

// Further monsters a single-target spell takes near the one it struck.
struct SpellSplash
{
    size_t extraTargets = 0;
    float radius = 0.0f;
};

// A spell's spellbook tooltip as one caster reads it.
struct SpellTooltipText
{
    std::string name;
    std::string description;
    // Novice to Grandmaster; an empty line is not shown.
    std::array<std::string, 4> masteryLines;
};

// What a party member's spell costs and how long its cast takes, and how much a healing spell heals
// (devdocs/maw/HANDOFF.md §3.5). Damage is the combat rules' (CombatRules::rollSpellDamage). This class is the Standard
// MMMerge rules: the spell table's numbers at the caster's mastery.
class SpellRules
{
public:
    virtual ~SpellRules() = default;

    // The spell's name as the caster's class knows it (MAW: Death Knights and Assassins rename theirs).
    virtual std::string spellName(const Character &caster, const SpellEntry &spell) const;
    // The mana the cast costs, from the table's cost at the caster's mastery.
    virtual int manaCost(const CharacterSpellCast &cast, int tableCost) const;
    // Why the member cannot cast the spell now beyond mana (MAW: an Assassin's combo points), or nothing.
    virtual std::optional<std::string> castRefusal(const Party &party, size_t casterIndex, uint32_t spellId) const;
    // The school mastery a class spell of the caster needs, in place of the spell table's; None: castable without the
    // school skill. Nothing for any other spell (Standard: always nothing).
    virtual std::optional<SkillMastery> classSpellMastery(const Character &caster, uint32_t spellId) const;
    // After a cast that spent its cost: what else it uses up or changes (MAW: combo points, the Elementalist's stacks
    // and rotation). `fromSpellbook`: chosen in the spellbook, not a quick or attack spell. Standard: nothing.
    virtual void afterCast(
        Party &party,
        size_t casterIndex,
        uint32_t spellId,
        const SpellTable &spellTable,
        bool indoor,
        bool fromSpellbook) const;
    // Switches the member's spell rotation (MAW's Elementalists) and says whether it is on now; nothing for a member
    // without one.
    virtual std::optional<bool> toggleSpellRotation(Character &member) const;
    // The recovery ticks the cast takes, from the table's.
    virtual int recoveryTicks(const CharacterSpellCast &cast, int tableTicks) const;
    // The HP a healing spell gives each target; nothing keeps Standard's heal.
    virtual std::optional<int> healAmount(const CharacterSpellCast &cast) const;
    // Casts a buff spell as an aura the caster holds (MAW): toggles it, spending no mana. Nothing casts the spell as
    // Standard does.
    virtual std::optional<AuraCastResult> castAura(Party &party, size_t casterIndex, uint32_t spellId) const;
    // The further monsters a single-target monster spell takes near its target (MAW's Shrinking Ray). Standard: none.
    virtual SpellSplash spellSplash(uint32_t spellId, SkillMastery mastery) const;
    // Whether no crowd control holds the monster, so a splash passes it over (MAW's Unstoppable bosses). Standard: no.
    virtual bool ignoresCrowdControl(const ActorRulesetFacts &target) const;
    // A buff from a scroll, a map event, a temple or a hireling. True when the rules dealt with it and the engine's
    // buff is not applied (MAW: a fixed aura, or nothing for a hireling's). Standard: false.
    virtual bool castSourceBuff(Party &party, uint32_t spellId, BuffSource source) const;
    // One tick of a damaging party aura on a monster (Immolation), before its resistance; nothing keeps the engine's
    // roll from the buff's skill.
    virtual std::optional<int> auraDamage(const Party &party, uint32_t spellId) const;
    // How long a party buff lasts, in game seconds, cast by a member or read from a scroll (MAW's Invisibility, a solo
    // party's Fly scroll); nothing keeps the engine's.
    virtual std::optional<float> partyBuffSeconds(
        const Party &party,
        uint32_t spellId,
        uint32_t skillLevel,
        SkillMastery mastery,
        bool fromScroll) const;
    // Whether a scroll of the spell survives its reading (MAW: Jump, Fly, Water Walk, Town Portal and Lloyd's Beacon
    // for a party of one). Standard: false.
    virtual bool keepsScroll(const Party &party, uint32_t spellId) const;
    // Whether castAura toggles the spell for this member, so a quick cast needs no target. Standard: false.
    virtual bool castsAsAura(const Party &party, size_t casterIndex, uint32_t spellId) const;
    // Each frame of play: re-applies the auras the party holds and keeps the mana they reserve. Standard: nothing.
    virtual void updateAuras(Party &party, float deltaSeconds) const;
    // The spell points the member's auras reserve. Standard: none.
    virtual int reservedSpellPoints(const Party &party, size_t memberIndex) const;
    // The hit points the member's auras reserve instead of spell points. Standard: none.
    virtual int reservedHitPoints(const Party &party, size_t memberIndex) const;
    // A heal spell landed: `overheal` of `healed` went past full HP. The rules may refund mana or shorten the
    // recovery (MAW's legendaries 34 and 35). Standard: nothing.
    virtual void afterHeal(Party &party, size_t casterIndex, int healed, int overheal, int manaCost,
        float &recoverySeconds) const;
    // Shared Life with the ruleset's heal: pools it with the members' hit points and shares them back, and says
    // whether it did. Standard: false, the engine's even share.
    virtual bool shareLife(Party &party, int heal) const;
    // A member is about to leave the party (dismissed to the inn); the members after it will move up a slot.
    // Standard: nothing.
    virtual void memberLeaving(const Party &party, size_t memberIndex) const;
    // What a buff's popup shows instead of its time left while a member holds it as an aura (MAW: "Held by Name").
    // Standard: nothing, buffs run out.
    virtual std::optional<std::string> heldBuffText(const Party &party, uint32_t spellId) const;
    // Auras held now that no party or member buff slot shows (MAW's Empower Magic and Meditation). Standard: none.
    virtual std::vector<uint32_t> heldAurasWithoutBuffSlot(const Party &party) const;
    // The spellbook tooltip of a spell for a caster in the party (MAW: its own texts with the caster's numbers).
    // Standard: the spell table's texts.
    virtual SpellTooltipText spellTooltip(const Party &party, const Character &caster, const SpellEntry &spell) const;
    // How many real seconds a crowd-control spell holds the monster (MAW: no resistance roll, its own durations and
    // diminishing returns); 0 when it does not take; nothing for Standard's resistance roll and durations.
    virtual std::optional<float> crowdControlSeconds(const CrowdControlCast &cast) const;
    // The spellbook's R key: ends every buff the party holds and returns the status line (MAW: every aura is
    // released). Standard: nothing, the key does nothing.
    virtual std::optional<std::string> removeAllBuffs(Party &party) const;
    // The aura panel's read of the party's auras: each held aura's holder, reservation, strength, effects and what
    // each member gets of them (MAW). Pure. Standard: nothing, buffs are no auras and there is no panel.
    virtual std::optional<AuraReport> auraReport(const Party &party) const;
    // Whether Tab in the spellbook turns to the member's next school (MAW). Standard: no.
    virtual bool tabCyclesSpellbookSchools() const;
    // Whether Sunray can be cast indoors, at any hour there (MAW: SP:1006); outdoors it still needs daylight.
    // Standard: no, outdoors only.
    virtual bool sunrayWorksIndoors() const;
    // Spirit Lash's reach at this mastery. Standard: 768; MAW: 384 at Master (an engine patch, SP:1009-1014; SPL-13).
    virtual float spiritLashRadius(SkillMastery mastery) const;
    // Whether Raise Dead at this mastery revives an eradicated member. Standard: yes; MAW: Grandmaster only, as the
    // engine below it (SP:250-260, SPL-15).
    virtual bool raiseDeadLiftsEradication(SkillMastery mastery) const;
    // How many permanent Grandmaster wisps a Summon Wisp at this mastery may add once the normal wisps are at their
    // limit (MAW: 2 x mastery - 3, so Expert 1, Master 3, Grandmaster 5; SP:3435-3455, SPL-8). Standard: none.
    virtual size_t extraPermanentWisps(SkillMastery mastery) const;
    // Whether a quick cast of this crowd-control spell with no monster under the cursor takes the visible hostile
    // whose debuff of the spell ends soonest, within 4800 (MAW: SP:1486-1526, so repeated casts spread over a pack;
    // SPL-18). Standard: no, the closest visible hostile.
    virtual bool quickCastSpreadsDebuff(uint32_t spellId) const;
    // Whether Protection from Magic's charges also add to every resistance. Standard: yes; MAW: no, its charges are
    // only a count (SPL-3).
    virtual bool protectionFromMagicRaisesResistances() const;
};

const SpellRules &standardSpellRules();

// The crowd-control duration the party's rules give a party member's spell on a map actor (SpellRules::
// crowdControlSeconds), from what the worlds know of the actor; nothing for Standard's, and nothing (no diminishing
// returns recorded) for Turn Undead or Control Undead on a living monster (SPL-10).
std::optional<float> partyCrowdControlSeconds(
    const Party *pParty,
    uint32_t casterIndex,
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery mastery,
    int resistance,
    const ActorRulesetFacts &targetFacts,
    int targetTableLevel,
    bool targetUndead,
    const std::string &mapName,
    size_t actorIndex,
    double gameMinutes);
}
