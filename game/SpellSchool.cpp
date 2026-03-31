#include "game/SpellSchool.h"

#include "game/SkillData.h"
#include "game/SpellIds.h"

namespace OpenYAMM::Game
{
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

    if (spellIdInRange(spellId, SpellId::Glamour, SpellId::DarkfireBolt))
    {
        return "DarkElfAbility";
    }

    if (spellIdInRange(spellId, SpellId::Lifedrain, SpellId::Mistform))
    {
        return "VampireAbility";
    }

    if (spellIdInRange(spellId, SpellId::Fear, SpellId::WingBuffet))
    {
        return "DragonAbility";
    }

    return std::nullopt;
}

std::optional<std::pair<uint32_t, uint32_t>> spellIdRangeForMagicSkill(const std::string &skillName)
{
    const std::string canonicalSkillNameValue = canonicalSkillName(skillName);

    if (canonicalSkillNameValue == "FireMagic")
    {
        return {{spellIdValue(SpellId::TorchLight), spellIdValue(SpellId::Incinerate)}};
    }

    if (canonicalSkillNameValue == "AirMagic")
    {
        return {{spellIdValue(SpellId::WizardEye), spellIdValue(SpellId::Starburst)}};
    }

    if (canonicalSkillNameValue == "WaterMagic")
    {
        return {{spellIdValue(SpellId::Awaken), spellIdValue(SpellId::LloydsBeacon)}};
    }

    if (canonicalSkillNameValue == "EarthMagic")
    {
        return {{spellIdValue(SpellId::Stun), spellIdValue(SpellId::MassDistortion)}};
    }

    if (canonicalSkillNameValue == "SpiritMagic")
    {
        return {{spellIdValue(SpellId::DetectLife), spellIdValue(SpellId::Resurrection)}};
    }

    if (canonicalSkillNameValue == "MindMagic")
    {
        return {{spellIdValue(SpellId::Telepathy), spellIdValue(SpellId::Enslave)}};
    }

    if (canonicalSkillNameValue == "BodyMagic")
    {
        return {{spellIdValue(SpellId::CureWeakness), spellIdValue(SpellId::PowerCure)}};
    }

    if (canonicalSkillNameValue == "LightMagic")
    {
        return {{spellIdValue(SpellId::LightBolt), spellIdValue(SpellId::DivineIntervention)}};
    }

    if (canonicalSkillNameValue == "DarkMagic")
    {
        return {{spellIdValue(SpellId::Reanimate), spellIdValue(SpellId::SoulDrinker)}};
    }

    if (canonicalSkillNameValue == "DarkElfAbility")
    {
        return {{spellIdValue(SpellId::Glamour), spellIdValue(SpellId::DarkfireBolt)}};
    }

    if (canonicalSkillNameValue == "VampireAbility")
    {
        return {{spellIdValue(SpellId::Lifedrain), spellIdValue(SpellId::Mistform)}};
    }

    if (canonicalSkillNameValue == "DragonAbility")
    {
        return {{spellIdValue(SpellId::Fear), spellIdValue(SpellId::WingBuffet)}};
    }

    return std::nullopt;
}
}
