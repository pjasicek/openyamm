#pragma once

#include "game/rules/PotionRules.h"

namespace OpenYAMM::Game
{
class MawRules;

// MAW's alchemy (CLASSES_SPELLS_SPEC.md §7): reagents grow with their item level and the alchemist's mastery, and
// the healing and mana potions restore a share of what a character of the potion's power in levels is expected to
// have.
class MawPotionRules : public PotionRules
{
public:
    explicit MawPotionRules(MawRules &rules);

    // floor(base x (1 + level x 0.25 / 20) + 0.75 x level) for a reagent of item level > 0 (else base), plus half the
    // Alchemy skill at Master or all of it at Grandmaster; at most 255, and half of what lies above, up to 900, adds to
    // the alchemist's Alchemy for the mix (AL:601-637).
    int reagentPower(
        const ItemDefinition &reagentDefinition,
        const InventoryItem &reagent,
        SkillMastery alchemyMastery,
        uint32_t alchemyLevel) const override;
    // The balance model's expected HP or SP at that level (E:253-345).
    double estimatedPool(PotionPool pool, int level) const override;
    // The Alchemy skill with item bonuses, at most twice the skill cap (zzMAW-Skills.lua GetSkill).
    uint32_t mixingAlchemyLevel(const Character &alchemist) const override;
    // max(min(round(max(T + M / 2, T / 2 + M)), Alchemy x mastery / 2), T, M) for target T and held M
    // (MiscTweaks.lua:781-788).
    int catalystMixPower(
        int targetPower,
        int heldPower,
        bool bothCatalysts,
        SkillMastery alchemyMastery,
        uint32_t alchemyLevel) const override;
    // "Can't benefit anymore" (zzAlchemy.lua:211, 240).
    std::optional<std::string> noBenefitText() const override;
    // The potion's aura beats the party's own aura of the spell (memberAura's comparison, buffStrength).
    bool potionAuraCounts(uint32_t spellId, int power) const override;

private:
    MawRules &m_rules;
};

// The reagent part of MAW's formula, before the Alchemy bonus and cap.
int mawReagentBasePower(int basePower, int itemLevel);
// What a reagent of this power (Alchemy bonus included) adds to a mix: up to 255, then half the excess, at most 900
// more (AL:601-637).
int mawCappedReagentPower(double power);
}
