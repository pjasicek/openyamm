#include "game/rules/maw/MawPotionRules.h"
#include "engine/Localization.h"

#include "game/items/InventoryItemMixingRuntime.h"
#include "game/party/Party.h"
#include "game/rules/SkillRules.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/ItemTable.h"
#include "game/tables/PotionEffectTable.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
MawPotionRules::MawPotionRules(MawRules &rules)
    : m_rules(rules)
{
}

int mawReagentBasePower(int basePower, int itemLevel)
{
    if (itemLevel <= 0)
    {
        return basePower;
    }

    return int(std::floor(basePower * (1 + itemLevel * 0.25 / 20) + 0.75 * itemLevel));
}

int MawPotionRules::reagentPower(
    const ItemDefinition &reagentDefinition,
    const InventoryItem &reagent,
    SkillMastery alchemyMastery,
    uint32_t alchemyLevel) const
{
    const int base = InventoryItemMixingRuntime::reagentPower(reagentDefinition);
    double power = mawReagentBasePower(base, reagent.rulesetFields.dropLevel);

    if (alchemyMastery == SkillMastery::Master)
    {
        power += 0.5 * alchemyLevel;
    }
    else if (alchemyMastery >= SkillMastery::Grandmaster)
    {
        power += alchemyLevel;
    }

    return mawCappedReagentPower(power);
}

int mawCappedReagentPower(double power)
{
    constexpr int ReagentPowerCap = 255;
    const int whole = int(power);

    if (whole <= ReagentPowerCap)
    {
        return whole;
    }

    return ReagentPowerCap + std::min(int(std::floor((power - ReagentPowerCap) / 2)), 900);
}

std::optional<std::string> MawPotionRules::noBenefitText() const
{
    return Engine::tr("Can't benefit anymore");
}

uint32_t MawPotionRules::mixingAlchemyLevel(const Character &alchemist) const
{
    const CharacterSkill *pSkill = alchemist.findSkill("Alchemy");
    const uint32_t trained = pSkill != nullptr ? pSkill->level : 0;
    const auto bonus = alchemist.itemSkillBonuses.find("Alchemy");
    const int64_t level = int64_t(trained) + (bonus != alchemist.itemSkillBonuses.end() ? bonus->second : 0);
    const std::optional<uint32_t> cap = m_rules.gameRules().skills.skillLevelCap("Alchemy");
    return uint32_t(std::clamp<int64_t>(level, 0, cap ? int64_t(*cap) * 2 : level));
}

int MawPotionRules::catalystMixPower(
    int targetPower,
    int heldPower,
    bool,
    SkillMastery alchemyMastery,
    uint32_t alchemyLevel) const
{
    const double combined = std::max(targetPower + heldPower / 2.0, targetPower / 2.0 + heldPower);
    const double limit = double(alchemyLevel) * int(alchemyMastery) / 2;
    return std::max({int(std::min(std::round(combined), limit)), targetPower, heldPower});
}

double MawPotionRules::estimatedPool(PotionPool pool, int level) const
{
    MawBalanceModel &model = m_rules.model(5);
    return pool == PotionPool::HitPoints ? model.health(std::max(1, level)) : model.mana(std::max(1, level));
}
}
