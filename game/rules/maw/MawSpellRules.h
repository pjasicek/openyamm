#pragma once

#include "game/rules/SpellRules.h"

#include <array>
#include <unordered_map>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
class MawRules;

// MAW's spell costs, cast times and heals (devdocs/maw/CLASSES_SPELLS_SPEC.md §1-2): Ascension (the Learning skill)
// makes damage, healing and crowd-control spells dearer and slower, its mastery and the caster's Personality make
// them cheaper; heals follow MAW's heal table.
class MawSpellRules : public SpellRules
{
public:
    explicit MawSpellRules(MawRules &rules);

    int manaCost(const CharacterSpellCast &cast, int tableCost) const override;
    int recoveryTicks(const CharacterSpellCast &cast, int tableTicks) const override;
    std::optional<int> healAmount(const CharacterSpellCast &cast) const override;
    // Buff spells are auras (CLASSES_SPELLS_SPEC.md §3): a cast toggles the caster's hold on it.
    std::optional<AuraCastResult> castAura(Party &party, size_t casterIndex, uint32_t spellId) const override;
    // Shrinking Ray takes one more monster within 512 per mastery above Novice (SP:1659-1732).
    SpellSplash spellSplash(uint32_t spellId, SkillMastery mastery) const override;
    // Unstoppable bosses (zzMaw-Spells.lua:1680-1684).
    bool ignoresCrowdControl(const ActorRulesetFacts &target) const override;
    // Scrolls, pedestals and temples hold the buff as a fixed aura of skill 7 at Master for level 40 (vars.mawbuff
    // holds the map's name or "Temple", getSpecialBuffSkill); a hireling's buff is wiped by the aura pass, so it does
    // nothing. A member's own hold stays.
    bool castSourceBuff(Party &party, uint32_t spellId, BuffSource source) const override;
    // Immolation burns as its holder's spell: 10 + 1-30 per point of the aura's skill with Ascension, through the
    // spell damage rules (the spells patch; Party.SpellBuffs[10].Caster names the holder, SP:2946-2951).
    std::optional<int> auraDamage(const Party &party, uint32_t spellId) const override;
    // Invisibility lasts (15 + s) x 1.5 game minutes at Master, (30 + 2 s) x 1.5 at Grandmaster (SP:711-718); a solo
    // party's Fly scroll seven hours (SP:1109-1117).
    std::optional<float> partyBuffSeconds(
        const Party &party,
        uint32_t spellId,
        uint32_t skillLevel,
        SkillMastery mastery,
        bool fromScroll) const override;
    // A solo party's travel scrolls come back (SP:1100-1122).
    bool keepsScroll(const Party &party, uint32_t spellId) const override;
    bool castsAsAura(const Party &party, size_t casterIndex, uint32_t spellId) const override;
    // Death Knights and Assassins know their spells under their own names (MCC:108-131, 69-101).
    std::string spellName(const Character &caster, const SpellEntry &spell) const override;
    // MAW's texts (data/texts.yml) with the caster's numbers, the aura's reservation and holder, and the cast time.
    SpellTooltipText spellTooltip(const Party &party, const Character &caster, const SpellEntry &spell) const override;
    // An Assassin's damage spells need combo points as well as energy (MCC:239-292).
    std::optional<std::string> castRefusal(const Party &party, size_t casterIndex, uint32_t spellId) const override;
    // MAW marks class spells known by its own mastery steps and the original engine casts any known spell: the
    // Assassin's and Death Knight's at their class step (Shield unskilled, Stone Skin and Water Walk at Novice;
    // MCC:595-625), an Elementalist's known element spells without a mastery (its four starters even without the school;
    // MCC:495-506).
    std::optional<SkillMastery> classSpellMastery(const Character &caster, uint32_t spellId) const override;
    // A spellbook cast of an offensive spell starts an Elementalist's stacks over (MCC:541-553).
    void afterCast(
        Party &party,
        size_t casterIndex,
        uint32_t spellId,
        const SpellTable &spellTable,
        bool indoor,
        bool fromSpellbook) const override;
    std::optional<bool> toggleSpellRotation(Character &member) const override;
    // Applies every aura whose holder is conscious through the party's buffs, with MAW's strengths, and keeps each
    // holder's mana below its unreserved pool: every half second of play, and at once for a zero step.
    void updateAuras(Party &party, float deltaSeconds) const override;
    // cost / (class SP factor + Enlightenment mastery / 2) percent of the maximum mana per aura held; Death Knights
    // and the Thief line reserve nothing.
    int reservedSpellPoints(const Party &party, size_t memberIndex) const override;
    // Legendary 34 refunds the overhealed share of the mana, 35 takes half that share off the recovery (SP:1149-1180).
    void afterHeal(Party &party, size_t casterIndex, int healed, int overheal, int manaCost,
        float &recoverySeconds) const override;
    // Shared Life (SP:824-1003): the living members, highest HP first while the pool stays at or above zero, pool
    // their hit points with the heal and share them back evenly up to each one's maximum.
    bool shareLife(Party &party, int heal) const override;
    // The leaving member's auras go with them; holders and class state after it move up a slot.
    void memberLeaving(const Party &party, size_t memberIndex) const override;
    // The hit points a legendary 32 wearer's auras hold back (0 for everyone else).
    int reservedHitPoints(const Party &party, size_t memberIndex) const override;
    std::optional<std::string> heldBuffText(const Party &party, uint32_t spellId) const override;
    std::vector<uint32_t> heldAurasWithoutBuffSlot(const Party &party) const override;
    // CLASSES_SPELLS_SPEC.md §4: durations by mastery, Ascension and resistance, twice as long solo; diminishing
    // returns per monster for fear and control and for paralysis, bosses half as long; Stun rolls 30 / (30 + L / 4).
    std::optional<float> crowdControlSeconds(const CrowdControlCast &cast) const override;
    // R releases every aura, the scroll, pedestal and temple ones too; the next update ends their buffs (SP:22-27).
    std::optional<std::string> removeAllBuffs(Party &party) const override;
    // The held auras with their holders' strengths: each effect against the party's other auras at their strengths
    // (Hour of Power's parts at skill / 1.5, Day of Protection's at skill / 1.4, Day of the Gods' stat part) and the
    // members' own potion copies; they never add up (game/rules/maw/MawAuraReport.cpp).
    std::optional<AuraReport> auraReport(const Party &party) const override;
    bool tabCyclesSpellbookSchools() const override;
    bool sunrayWorksIndoors() const override;
    float spiritLashRadius(SkillMastery mastery) const override;
    bool raiseDeadLiftsEradication(SkillMastery mastery) const override;
    // Slow, both Charms, Berserk, Paralyze, Enslave, Dark Grasp and Control Undead (SP:1431-1440).
    bool quickCastSpreadsDebuff(uint32_t spellId) const override;
    size_t extraPermanentWisps(SkillMastery mastery) const override;
    bool protectionFromMagicRaisesResistances() const override;

private:
    int reservedPoints(const Party &party, size_t memberIndex, bool health) const;
    // What holding the aura would cost the member, as castAura reckons it.
    AuraReservationCost auraCost(const Party &party, size_t memberIndex, uint32_t spellId) const;
    // The recovery before a dimension map's affix.
    int baseRecoveryTicks(const CharacterSpellCast &cast, int tableTicks) const;
    // The recovery a member's cast of the spell takes now, at their school's skill and mastery; 0 for an unknown spell.
    int castRecoveryTicks(const Party &party, const Character &caster, uint32_t spellId, const SpellTable &spellTable)
        const;

    MawRules &m_rules;
    // The buff slots the auras set at the last update, to clear those no aura sets any more.
    mutable std::vector<uint32_t> m_appliedPartyBuffs;
    mutable std::vector<uint32_t> m_appliedCharacterBuffs;
    // Whether the last update applied a held Preservation aura to every member.
    mutable bool m_preservationAuraApplied = false;
    // The map the last update ran on, to end the fixed auras a map change ends.
    mutable std::string m_auraMap;
    // Time since the last timed aura update.
    mutable float m_auraSeconds = 0.0f;
};
}
