#include "game/SpellbookUiLayout.h"

#include "game/SpellIds.h"

#include <array>
#include <iomanip>
#include <sstream>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
constexpr std::array<SpellbookSchoolUiDefinition, 12> SpellbookSchoolUiDefinitions = {{
    {SpellbookSchool::Fire, "SpellbookPageFire", "SpellbookSchoolButtonFire", spellIdValue(SpellId::TorchLight), 11},
    {SpellbookSchool::Air, "SpellbookPageAir", "SpellbookSchoolButtonAir", spellIdValue(SpellId::WizardEye), 11},
    {SpellbookSchool::Water, "SpellbookPageWater", "SpellbookSchoolButtonWater", spellIdValue(SpellId::Awaken), 11},
    {SpellbookSchool::Earth, "SpellbookPageEarth", "SpellbookSchoolButtonEarth", spellIdValue(SpellId::Stun), 11},
    {
        SpellbookSchool::Spirit,
        "SpellbookPageSpirit",
        "SpellbookSchoolButtonSpirit",
        spellIdValue(SpellId::DetectLife),
        11
    },
    {SpellbookSchool::Mind, "SpellbookPageMind", "SpellbookSchoolButtonMind", spellIdValue(SpellId::Telepathy), 11},
    {SpellbookSchool::Body, "SpellbookPageBody", "SpellbookSchoolButtonBody", spellIdValue(SpellId::CureWeakness), 11},
    {SpellbookSchool::Light, "SpellbookPageLight", "SpellbookSchoolButtonLight", spellIdValue(SpellId::LightBolt), 11},
    {SpellbookSchool::Dark, "SpellbookPageDark", "SpellbookSchoolButtonDark", spellIdValue(SpellId::Reanimate), 11},
    {
        SpellbookSchool::DarkElf,
        "SpellbookPageDarkElf",
        "SpellbookSchoolButtonDarkElf",
        spellIdValue(SpellId::Glamour),
        4
    },
    {
        SpellbookSchool::Vampire,
        "SpellbookPageVampire",
        "SpellbookSchoolButtonVampire",
        spellIdValue(SpellId::Lifedrain),
        4
    },
    {SpellbookSchool::Dragon, "SpellbookPageDragon", "SpellbookSchoolButtonDragon", spellIdValue(SpellId::Fear), 4},
}};
}

const std::array<SpellbookSchoolUiDefinition, 12> &spellbookSchoolUiDefinitions()
{
    return SpellbookSchoolUiDefinitions;
}

const SpellbookSchoolUiDefinition *findSpellbookSchoolUiDefinition(SpellbookSchool school)
{
    for (const SpellbookSchoolUiDefinition &definition : SpellbookSchoolUiDefinitions)
    {
        if (definition.school == school)
        {
            return &definition;
        }
    }

    return nullptr;
}

const SpellbookSchoolUiDefinition *findSpellbookSchoolUiDefinitionForSpellId(uint32_t spellId)
{
    for (const SpellbookSchoolUiDefinition &definition : SpellbookSchoolUiDefinitions)
    {
        if (spellId >= definition.firstSpellId && spellId < definition.firstSpellId + definition.spellCount)
        {
            return &definition;
        }
    }

    return nullptr;
}

std::string spellbookSpellLayoutId(SpellbookSchool school, uint32_t spellOrdinal)
{
    const SpellbookSchoolUiDefinition *pDefinition = findSpellbookSchoolUiDefinition(school);

    if (pDefinition == nullptr)
    {
        return "";
    }

    const auto spellLayoutIdForSuffixes =
        [pDefinition, spellOrdinal](const auto &suffixes) -> std::string
        {
            if (spellOrdinal >= 1 && spellOrdinal <= suffixes.size())
            {
                return std::string(pDefinition->pPageLayoutId) + "Spell" + suffixes[spellOrdinal - 1];
            }

            return "";
        };

    if (school == SpellbookSchool::Fire)
    {
        static constexpr std::array<const char *, 11> suffixes = {{
            "Torchlight",
            "Firebolt",
            "Fireresistance",
            "Fireaura",
            "Haste",
            "Fireball",
            "Firespike",
            "Immolation",
            "Meteorshower",
            "Inferno",
            "Incinerate",
        }};

        return spellLayoutIdForSuffixes(suffixes);
    }

    if (school == SpellbookSchool::Air)
    {
        static constexpr std::array<const char *, 11> suffixes = {{
            "Wizardeye",
            "Featherfall",
            "Airresistance",
            "Sparks",
            "Jump",
            "Shield",
            "Lightningbolt",
            "Invisibility",
            "Implosion",
            "Fly",
            "Starburst",
        }};

        return spellLayoutIdForSuffixes(suffixes);
    }

    if (school == SpellbookSchool::Water)
    {
        static constexpr std::array<const char *, 11> suffixes = {{
            "Awaken",
            "Poisonspray",
            "Waterresistance",
            "Icebolt",
            "Waterwalk",
            "Rechargeitem",
            "Acidburst",
            "Enchantitem",
            "Townportal",
            "Iceblast",
            "Lloydsbeacon",
        }};

        return spellLayoutIdForSuffixes(suffixes);
    }

    if (school == SpellbookSchool::Earth)
    {
        static constexpr std::array<const char *, 11> suffixes = {{
            "Stun",
            "Slow",
            "Earthresistance",
            "Deadlyswarm",
            "Stoneskin",
            "Blades",
            "Stonetoflesh",
            "Rockblast",
            "Telekinesis",
            "Deathblossom",
            "Massdistortion",
        }};

        return spellLayoutIdForSuffixes(suffixes);
    }

    if (school == SpellbookSchool::Spirit)
    {
        static constexpr std::array<const char *, 11> suffixes = {{
            "Detectlife",
            "Bless",
            "Fate",
            "Turnundead",
            "Removecurse",
            "Preservation",
            "Heroism",
            "Spiritlash",
            "Raisedead",
            "Sharedlife",
            "Resurrection",
        }};

        return spellLayoutIdForSuffixes(suffixes);
    }

    if (school == SpellbookSchool::Mind)
    {
        static constexpr std::array<const char *, 11> suffixes = {{
            "Telepathy",
            "Removefear",
            "Mindresistance",
            "Mindblast",
            "Charm",
            "Cureparalysis",
            "Berserk",
            "Massfear",
            "Cureinsanity",
            "Psychicshock",
            "Enslave",
        }};

        return spellLayoutIdForSuffixes(suffixes);
    }

    if (school == SpellbookSchool::Body)
    {
        static constexpr std::array<const char *, 11> suffixes = {{
            "Cureweakness",
            "Heal",
            "Bodyresistance",
            "Harm",
            "Regeneration",
            "Curepoison",
            "Hammerhands",
            "Curedisease",
            "Protectionfrommagic",
            "Flyingfist",
            "Powercure",
        }};

        return spellLayoutIdForSuffixes(suffixes);
    }

    if (school == SpellbookSchool::Light)
    {
        static constexpr std::array<const char *, 11> suffixes = {{
            "Lightbolt",
            "Destroyundead",
            "Dispelmagic",
            "Paralyze",
            "Summonwisp",
            "Dayofthegods",
            "Prismaticlight",
            "Dayofprotection",
            "Hourofpower",
            "Sunray",
            "Divineintervention",
        }};

        return spellLayoutIdForSuffixes(suffixes);
    }

    if (school == SpellbookSchool::Dark)
    {
        static constexpr std::array<const char *, 11> suffixes = {{
            "Reanimate",
            "Toxiccloud",
            "Vampiricweapon",
            "Shrinkingray",
            "Shrapmetal",
            "Controlundead",
            "Painreflection",
            "Darkgrasp",
            "Dragonbreath",
            "Armageddon",
            "Souldrinker",
        }};

        return spellLayoutIdForSuffixes(suffixes);
    }

    if (school == SpellbookSchool::DarkElf)
    {
        static constexpr std::array<const char *, 4> suffixes = {{
            "Glamour",
            "Travelersboon",
            "Blind",
            "Darkfirebolt",
        }};

        return spellLayoutIdForSuffixes(suffixes);
    }

    if (school == SpellbookSchool::Vampire)
    {
        static constexpr std::array<const char *, 4> suffixes = {{
            "Lifedrain",
            "Levitate",
            "Charm",
            "Mistform",
        }};

        return spellLayoutIdForSuffixes(suffixes);
    }

    if (school == SpellbookSchool::Dragon)
    {
        static constexpr std::array<const char *, 4> suffixes = {{
            "Fear",
            "Flameblast",
            "Flight",
            "Wingbuffet",
        }};

        return spellLayoutIdForSuffixes(suffixes);
    }

    std::ostringstream stream;
    stream << pDefinition->pPageLayoutId << "Spell" << std::setw(2) << std::setfill('0') << spellOrdinal;
    return stream.str();
}
}
