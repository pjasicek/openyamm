#include "game/rules/ClassRules.h"
#include "engine/Localization.h"

#include "game/party/Party.h"
#include "game/party/SkillData.h"

namespace OpenYAMM::Game
{
std::optional<int> ClassRules::baseMaxHealth(const Character &, const ClassMultiplierEntry &) const
{
    return std::nullopt;
}

std::optional<int> ClassRules::baseMaxSpellPoints(const Character &, const ClassMultiplierEntry &) const
{
    return std::nullopt;
}

namespace
{
constexpr uint32_t VampireRace = 1;
constexpr uint32_t UndeadRace = 6;
} // namespace

void ClassRules::applyClassBonuses(Character &member) const
{
    // MMerge MiscTweaks.lua (races 6 and 1, the executable's own Lich rule switched off); MM7 gives a Lich Mind and
    // Body by class (OE Character.cpp), which the class check keeps for a Lich whose race did not change.
    const std::string canonicalClass = canonicalClassName(member.className);

    if (member.raceId == UndeadRace || canonicalClass == "Lich")
    {
        member.magicalImmunities.mind = true;
        member.magicalImmunities.body = true;
    }
    else if (member.raceId == VampireRace || canonicalClass == "Vampire" || canonicalClass == "Nosferatu")
    {
        member.magicalImmunities.mind = true;
    }
}

bool ClassRules::learnsSpellsFromBooks(const Character &) const
{
    return true;
}

bool ClassRules::isDragon(const Character &character) const
{
    const std::string canonicalClass = canonicalClassName(character.className);
    return canonicalClass == "Dragon" || canonicalClass == "GreatWyrm";
}

PortraitCounter ClassRules::portraitCounter(const Character &) const
{
    return {};
}

std::string ClassRules::displayName(const Party &, const Character &member) const
{
    return Engine::localize(displayClassName(!member.className.empty() ? member.className : member.role), "class");
}

void ClassRules::update(Party &, const IGameplayWorldRuntime &, float) const
{
}

bool ClassRules::offersMercenaries() const
{
    return true;
}

uint32_t ClassRules::mercenarySkillPoints(uint32_t level) const
{
    return level > 0 ? level * 5 - 5 : 0;
}

std::vector<uint32_t> ClassRules::mercenaryClassKinds(uint32_t, std::vector<uint32_t> offeredKinds) const
{
    return offeredKinds;
}

// The race's immunities from applyClassBonuses, for the party creation race card.
std::vector<std::string> ClassRules::raceNotes(const Character &character) const
{
    if (character.raceId == UndeadRace)
    {
        return {Engine::tr("Immune to Mind and Body magic.")};
    }

    if (character.raceId == VampireRace)
    {
        return {Engine::tr("Immune to Mind magic.")};
    }

    return {};
}

bool ClassRules::showsCreationSkillMatrix() const
{
    return false;
}

std::optional<float> ClassRules::unstuckLift(double) const
{
    return std::nullopt;
}

std::optional<std::string> ClassRules::partyCharge(Party &, IGameplayWorldRuntime &, std::optional<size_t>) const
{
    return std::nullopt;
}

std::optional<FollowerHireRefusal> ClassRules::followerHireRefusal(uint32_t) const
{
    return std::nullopt;
}

std::optional<FollowerHireRefusal> ClassRules::paidHirelingRefusal() const
{
    return std::nullopt;
}

const ClassRules &standardClassRules()
{
    static const ClassRules Rules;
    return Rules;
}
}
