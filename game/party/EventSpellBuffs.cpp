#include "game/party/EventSpellBuffs.h"

#include "game/party/Party.h"
#include "game/party/SpellIds.h"

namespace OpenYAMM::Game
{
namespace
{
float secondsFromHours(float hours)
{
    return hours * 3600.0f;
}

float secondsFromMinutes(float minutes)
{
    return minutes * 60.0f;
}

SkillMastery normalizeEventSkillMastery(uint32_t rawSkillMastery)
{
    if (rawSkillMastery >= static_cast<uint32_t>(SkillMastery::Grandmaster))
    {
        return SkillMastery::Grandmaster;
    }

    return static_cast<SkillMastery>(rawSkillMastery);
}

float resolveEventPartyBuffDurationSeconds(uint32_t spellId, uint32_t skillLevel, SkillMastery mastery)
{
    switch (spellIdFromValue(spellId))
    {
        case SpellId::TorchLight:
        case SpellId::WizardEye:
        case SpellId::Invisibility:
        case SpellId::Fly:
        case SpellId::WaterWalk:
        case SpellId::DetectLife:
        case SpellId::ProtectionFromMagic:
        case SpellId::Glamour:
        case SpellId::FireResistance:
        case SpellId::AirResistance:
        case SpellId::WaterResistance:
        case SpellId::EarthResistance:
        case SpellId::MindResistance:
        case SpellId::BodyResistance:
            return secondsFromHours(static_cast<float>(skillLevel));

        case SpellId::FeatherFall:
            if (mastery == SkillMastery::Normal)
            {
                return secondsFromMinutes(static_cast<float>(5 * skillLevel));
            }

            if (mastery == SkillMastery::Expert)
            {
                return secondsFromMinutes(static_cast<float>(10 * skillLevel));
            }

            return secondsFromHours(static_cast<float>(skillLevel));

        case SpellId::Haste:
            if (mastery == SkillMastery::Expert)
            {
                return secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(skillLevel));
            }

            if (mastery == SkillMastery::Master)
            {
                return secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(3 * skillLevel));
            }

            return secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(4 * skillLevel));

        case SpellId::Shield:
        case SpellId::StoneSkin:
        case SpellId::Heroism:
            if (mastery == SkillMastery::Expert)
            {
                return secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel));
            }

            if (mastery == SkillMastery::Master)
            {
                return secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * skillLevel));
            }

            return secondsFromHours(static_cast<float>(skillLevel + 1));

        case SpellId::Immolation:
            return mastery == SkillMastery::Grandmaster
                ? secondsFromMinutes(static_cast<float>(10 * skillLevel))
                : secondsFromMinutes(static_cast<float>(skillLevel));

        case SpellId::Levitate:
            return mastery == SkillMastery::Expert
                ? secondsFromMinutes(static_cast<float>(10 * skillLevel))
                : mastery == SkillMastery::Master
                ? secondsFromHours(static_cast<float>(skillLevel))
                : secondsFromHours(static_cast<float>(3 * skillLevel));

        case SpellId::DayOfGods:
            return mastery == SkillMastery::Expert
                ? secondsFromHours(static_cast<float>(3 * skillLevel))
                : mastery == SkillMastery::Master
                ? secondsFromHours(static_cast<float>(4 * skillLevel))
                : secondsFromHours(static_cast<float>(5 * skillLevel));

        case SpellId::DayOfProtection:
            return mastery == SkillMastery::Master
                ? secondsFromHours(static_cast<float>(4 * skillLevel))
                : secondsFromHours(static_cast<float>(5 * skillLevel));

        case SpellId::HourOfPower:
            return mastery == SkillMastery::Master
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * 4 * skillLevel))
                : secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * 5 * skillLevel));

        case SpellId::TravelersBoon:
            return mastery == SkillMastery::Expert
                ? secondsFromMinutes(static_cast<float>(30 * skillLevel))
                : mastery == SkillMastery::Master
                ? secondsFromHours(static_cast<float>(skillLevel))
                : secondsFromHours(static_cast<float>(2 * skillLevel));

        case SpellId::Flight:
            return mastery == SkillMastery::Grandmaster
                ? secondsFromHours(24.0f)
                : secondsFromHours(static_cast<float>(skillLevel));

        default:
            return 0.0f;
    }
}

int resolveEventPartyBuffPower(uint32_t spellId, uint32_t skillLevel, SkillMastery mastery)
{
    switch (spellIdFromValue(spellId))
    {
        case SpellId::TorchLight:
            return mastery == SkillMastery::Normal ? 2 : mastery == SkillMastery::Expert ? 3 : 4;

        case SpellId::FireResistance:
        case SpellId::AirResistance:
        case SpellId::WaterResistance:
        case SpellId::EarthResistance:
        case SpellId::MindResistance:
        case SpellId::BodyResistance:
            return mastery == SkillMastery::Normal
                ? static_cast<int>(skillLevel)
                : mastery == SkillMastery::Expert
                ? static_cast<int>(2 * skillLevel)
                : mastery == SkillMastery::Master
                ? static_cast<int>(3 * skillLevel)
                : static_cast<int>(4 * skillLevel);

        case SpellId::StoneSkin:
        case SpellId::Heroism:
            return static_cast<int>(skillLevel) + 5;

        case SpellId::ProtectionFromMagic:
        case SpellId::Immolation:
            return static_cast<int>(skillLevel);

        case SpellId::DayOfGods:
            return mastery == SkillMastery::Expert
                ? static_cast<int>(3 * skillLevel + 10)
                : mastery == SkillMastery::Master
                ? static_cast<int>(4 * skillLevel + 10)
                : static_cast<int>(5 * skillLevel + 10);

        case SpellId::DayOfProtection:
            return mastery == SkillMastery::Master
                ? static_cast<int>(4 * skillLevel)
                : static_cast<int>(5 * skillLevel);

        case SpellId::HourOfPower:
            return static_cast<int>(skillLevel) + 5;

        case SpellId::Glamour:
            return mastery == SkillMastery::Grandmaster
                ? static_cast<int>(3 * skillLevel)
                : static_cast<int>(2 * skillLevel);

        default:
            return 0;
    }
}

bool applyCompositeEventPartyBuff(Party &party, uint32_t spellId, uint32_t skillLevel, SkillMastery mastery)
{
    const float durationSeconds = resolveEventPartyBuffDurationSeconds(spellId, skillLevel, mastery);
    const int power = resolveEventPartyBuffPower(spellId, skillLevel, mastery);

    switch (spellIdFromValue(spellId))
    {
        case SpellId::DayOfProtection:
            party.applyPartyBuff(PartyBuffId::BodyResistance, durationSeconds, power, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::MindResistance, durationSeconds, power, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::FireResistance, durationSeconds, power, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::WaterResistance, durationSeconds, power, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::AirResistance, durationSeconds, power, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::EarthResistance, durationSeconds, power, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::FeatherFall, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::WizardEye, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::HourOfPower:
        {
            const float hasteDurationSeconds = mastery == SkillMastery::Master
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(3 * 4 * skillLevel))
                : secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(4 * 5 * skillLevel));

            party.applyPartyBuff(PartyBuffId::Heroism, durationSeconds, power, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::Shield, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::Stoneskin, durationSeconds, power, spellId, skillLevel, mastery, 0);

            bool anyWeak = false;

            for (const Character &member : party.members())
            {
                if (member.conditions.test(static_cast<size_t>(CharacterCondition::Weak)))
                {
                    anyWeak = true;
                    break;
                }
            }

            if (!anyWeak)
            {
                party.applyPartyBuff(PartyBuffId::Haste, hasteDurationSeconds, 0, spellId, skillLevel, mastery, 0);
            }

            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                party.applyCharacterBuff(
                    memberIndex,
                    CharacterBuffId::Bless,
                    durationSeconds,
                    power,
                    spellIdValue(SpellId::Bless),
                    static_cast<uint32_t>(power),
                    mastery,
                    0);
            }

            return true;
        }

        case SpellId::TravelersBoon:
            party.applyPartyBuff(PartyBuffId::TorchLight, durationSeconds, 3, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::WizardEye, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::FeatherFall, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::Levitate:
            party.applyPartyBuff(PartyBuffId::Levitate, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::WaterWalk, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            party.applyPartyBuff(PartyBuffId::FeatherFall, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        default:
            return false;
    }
}

float resolveEventCharacterBuffDurationSeconds(uint32_t spellId, uint32_t skillLevel, SkillMastery mastery)
{
    switch (spellIdFromValue(spellId))
    {
        case SpellId::Bless:
            return mastery == SkillMastery::Normal
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel))
                : mastery == SkillMastery::Expert
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel))
                : mastery == SkillMastery::Master
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * skillLevel))
                : secondsFromHours(1.0f + static_cast<float>(skillLevel));

        case SpellId::Preservation:
            return mastery == SkillMastery::Expert
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel))
                : mastery == SkillMastery::Master
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(5 * skillLevel))
                : mastery == SkillMastery::Grandmaster
                ? secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * skillLevel))
                : secondsFromHours(1.0f) + secondsFromMinutes(static_cast<float>(15 * skillLevel));

        default:
            return 0.0f;
    }
}

bool tryApplyEventCharacterBuff(Party &party, uint32_t spellId, uint32_t skillLevel, uint32_t rawSkillMastery)
{
    const SkillMastery mastery = normalizeEventSkillMastery(rawSkillMastery);
    const float durationSeconds = resolveEventCharacterBuffDurationSeconds(spellId, skillLevel, mastery);

    if (durationSeconds <= 0.0f)
    {
        return false;
    }

    switch (spellIdFromValue(spellId))
    {
        case SpellId::Bless:
            if (mastery == SkillMastery::Normal)
            {
                return false;
            }

            for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
            {
                party.applyCharacterBuff(
                    memberIndex,
                    CharacterBuffId::Bless,
                    durationSeconds,
                    5 + static_cast<int>(skillLevel),
                    spellId,
                    skillLevel,
                    mastery,
                    0);
            }

            return true;

        case SpellId::Preservation:
            if (mastery == SkillMastery::Master || mastery == SkillMastery::Grandmaster)
            {
                for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
                {
                    party.applyCharacterBuff(
                        memberIndex,
                        CharacterBuffId::Preservation,
                        durationSeconds,
                        0,
                        spellId,
                        skillLevel,
                        mastery,
                        0);
                }

                return true;
            }

            return false;

        default:
            return false;
    }
}

bool tryApplyEventPartyBuff(Party &party, uint32_t spellId, uint32_t skillLevel, uint32_t rawSkillMastery)
{
    const SkillMastery mastery = normalizeEventSkillMastery(rawSkillMastery);
    const float durationSeconds = resolveEventPartyBuffDurationSeconds(spellId, skillLevel, mastery);

    if (durationSeconds <= 0.0f)
    {
        return false;
    }

    switch (spellIdFromValue(spellId))
    {
        case SpellId::DayOfProtection:
        case SpellId::HourOfPower:
        case SpellId::TravelersBoon:
        case SpellId::Levitate:
            return applyCompositeEventPartyBuff(party, spellId, skillLevel, mastery);

        case SpellId::TorchLight:
            party.applyPartyBuff(PartyBuffId::TorchLight, durationSeconds, 3, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::WizardEye:
            party.applyPartyBuff(PartyBuffId::WizardEye, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::FeatherFall:
            party.applyPartyBuff(PartyBuffId::FeatherFall, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::Haste:
            party.applyPartyBuff(PartyBuffId::Haste, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::Immolation:
            party.applyPartyBuff(
                PartyBuffId::Immolation,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::Shield:
            party.applyPartyBuff(PartyBuffId::Shield, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::FireResistance:
            party.applyPartyBuff(
                PartyBuffId::FireResistance,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::AirResistance:
            party.applyPartyBuff(
                PartyBuffId::AirResistance,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::WaterResistance:
            party.applyPartyBuff(
                PartyBuffId::WaterResistance,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::EarthResistance:
            party.applyPartyBuff(
                PartyBuffId::EarthResistance,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::DayOfGods:
            party.applyPartyBuff(
                PartyBuffId::DayOfGods,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::Heroism:
            party.applyPartyBuff(
                PartyBuffId::Heroism,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::MindResistance:
            party.applyPartyBuff(
                PartyBuffId::MindResistance,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::BodyResistance:
            party.applyPartyBuff(
                PartyBuffId::BodyResistance,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::StoneSkin:
            party.applyPartyBuff(
                PartyBuffId::Stoneskin,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::ProtectionFromMagic:
            party.applyPartyBuff(
                PartyBuffId::ProtectionFromMagic,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        case SpellId::Invisibility:
            party.applyPartyBuff(PartyBuffId::Invisibility, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::Fly:
            party.applyPartyBuff(PartyBuffId::Fly, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::WaterWalk:
            party.applyPartyBuff(PartyBuffId::WaterWalk, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::DetectLife:
            party.applyPartyBuff(PartyBuffId::DetectLife, durationSeconds, 0, spellId, skillLevel, mastery, 0);
            return true;

        case SpellId::Glamour:
            party.applyPartyBuff(
                PartyBuffId::Glamour,
                durationSeconds,
                resolveEventPartyBuffPower(spellId, skillLevel, mastery),
                spellId,
                skillLevel,
                mastery,
                0);
            return true;

        default:
            return false;
    }
}
}

bool tryApplyEventSpellBuffs(
    Party &party,
    uint32_t spellId,
    uint32_t skillLevel,
    uint32_t rawSkillMastery)
{
    return tryApplyEventPartyBuff(party, spellId, skillLevel, rawSkillMastery)
        || tryApplyEventCharacterBuff(party, spellId, skillLevel, rawSkillMastery);
}
}
