#include "game/mm9/Mm9HirelingHud.h"

#include "engine/Localization.h"
#include "game/gameplay/GameMechanics.h"
#include "game/mm9/Mm9HirelingTable.h"
#include "game/party/SkillData.h"

namespace OpenYAMM::Game
{
Mm9HirelingRailRect mm9HirelingRailPanel(
    const Mm9HirelingRailRect &rail,
    const Mm9HirelingRailRect &firstSlot,
    const Mm9HirelingRailRect &lastLiveSlot)
{
    const float band = firstSlot.y - rail.y;
    Mm9HirelingRailRect panel = rail;
    panel.height = lastLiveSlot.y + lastLiveSlot.height + band - rail.y;
    return panel;
}

std::optional<size_t> mm9HirelingRailSlotAt(const std::vector<Mm9HirelingRailRect> &liveSlots, float x, float y)
{
    for (size_t slot = 0; slot < liveSlots.size(); ++slot)
    {
        if (liveSlots[slot].contains(x, y))
        {
            return slot;
        }
    }

    return std::nullopt;
}

std::string_view mm9HirelingDamageTypeName(CombatDamageType damageType)
{
    switch (damageType)
    {
        case CombatDamageType::Physical: return Engine::trNoop("Physical");
        case CombatDamageType::Fire: return Engine::trNoop("Fire");
        case CombatDamageType::Air: return Engine::trNoop("Air");
        case CombatDamageType::Water: return Engine::trNoop("Water");
        case CombatDamageType::Earth: return Engine::trNoop("Earth");
        case CombatDamageType::Spirit: return Engine::trNoop("Spirit");
        case CombatDamageType::Mind: return Engine::trNoop("Mind");
        case CombatDamageType::Body: return Engine::trNoop("Body");
        case CombatDamageType::Light: return Engine::trNoop("Light");
        case CombatDamageType::Dark: return Engine::trNoop("Dark");
        case CombatDamageType::Energy: return Engine::trNoop("Energy");
        case CombatDamageType::Irresistible: return Engine::trNoop("Irresistible");
    }

    return Engine::trNoop("Physical");
}

std::string formatMm9HirelingAttack(const Mm9HirelingAttack &attack)
{
    if (!attack.present || attack.damage.diceRolls <= 0 || attack.damage.diceSides <= 0)
    {
        return {};
    }

    std::string text = std::to_string(attack.damage.diceRolls) + "d" + std::to_string(attack.damage.diceSides);

    if (attack.damage.bonus != 0)
    {
        text += (attack.damage.bonus > 0 ? "+" : "") + std::to_string(attack.damage.bonus);
    }

    const std::string element = Engine::tr(mm9HirelingDamageTypeName(attack.damageType));

    if (!attack.missile.empty())
    {
        return Engine::tr("{dice} {element}, {missile}",
            {{"dice", text}, {"element", element}, {"missile", Engine::localize(attack.missile)}});
    }

    return Engine::tr("{dice} {element}", {{"dice", text}, {"element", element}});
}

std::string formatMm9HirelingSpell(const Mm9HirelingSpell &spell, const std::string &displayName)
{
    const std::string text = displayName.empty() ? spell.name : displayName;

    if (spell.mastery != SkillMastery::None && spell.skillLevel > 0)
    {
        return Engine::tr("{spell}, {mastery} {level}",
            {{"spell", text},
             {"mastery", Engine::localize(masteryDisplayName(spell.mastery), "mastery")},
             {"level", spell.skillLevel}});
    }

    return text;
}
}
