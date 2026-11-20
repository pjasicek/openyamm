#include "game/ui/SpellbookUiLayout.h"

#include "engine/Localization.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"
#include "game/rules/GameRules.h"
#include "game/rules/SpellRules.h"

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

// English names (the display translates them); each view is of a literal, so data() ends with its terminator.
const char *spellbookSchoolDisplayName(SpellbookSchool school)
{
    switch (school)
    {
        case SpellbookSchool::Fire:
            return Engine::trNoop("Fire Magic").data();
        case SpellbookSchool::Air:
            return Engine::trNoop("Air Magic").data();
        case SpellbookSchool::Water:
            return Engine::trNoop("Water Magic").data();
        case SpellbookSchool::Earth:
            return Engine::trNoop("Earth Magic").data();
        case SpellbookSchool::Spirit:
            return Engine::trNoop("Spirit Magic").data();
        case SpellbookSchool::Mind:
            return Engine::trNoop("Mind Magic").data();
        case SpellbookSchool::Body:
            return Engine::trNoop("Body Magic").data();
        case SpellbookSchool::Light:
            return Engine::trNoop("Light Magic").data();
        case SpellbookSchool::Dark:
            return Engine::trNoop("Dark Magic").data();
        case SpellbookSchool::DarkElf:
            return Engine::trNoop("Dark Elf Ability").data();
        case SpellbookSchool::Vampire:
            return Engine::trNoop("Vampire Ability").data();
        case SpellbookSchool::Dragon:
            return Engine::trNoop("Dragon Ability").data();
    }

    return "";
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

const SpellbookSkin *activeSpellbookSkin(const Party *pParty)
{
    const Character *pMember = pParty != nullptr ? pParty->activeMember() : nullptr;
    return pMember != nullptr ? gameRulesFor(pParty).spells.spellbookSkin(*pMember) : nullptr;
}

const SpellbookSkinPage *activeSpellbookSkinPage(const Party *pParty, SpellbookSchool school)
{
    const SpellbookSkin *pSkin = activeSpellbookSkin(pParty);
    const SpellbookSchoolUiDefinition *pDefinition = findSpellbookSchoolUiDefinition(school);
    return pSkin != nullptr && pDefinition != nullptr ? pSkin->page(pDefinition->firstSpellId) : nullptr;
}

std::vector<SpellbookSkinTab> spellbookSkinTabs(
    const SpellbookSkin &skin,
    const std::function<bool(SpellbookSchool)> &memberHasSchool)
{
    // The standard tabs: 48 x 39 at the book's right edge, the first 2 from the top, one every 39 (spellbook.yml).
    static constexpr float TabWidth = 48;
    static constexpr float TabHeight = 39;
    static constexpr float TabTop = 2;
    std::vector<SpellbookSkinTab> tabs;
    const auto add = [&tabs](SpellbookSchool school, const SpellbookSkinPage *pPage)
    {
        const float top = TabTop + TabHeight * float(tabs.size());
        tabs.push_back({school, pPage, {640 - TabWidth, top, TabWidth, TabHeight}});
    };

    for (const SpellbookSkinPage &page : skin.pages)
    {
        const SpellbookSchoolUiDefinition *pDefinition = findSpellbookSchoolUiDefinitionForSpellId(page.firstSpellId);

        if (pDefinition != nullptr && memberHasSchool(pDefinition->school))
        {
            add(pDefinition->school, &page);
        }
    }

    for (const SpellbookSchoolUiDefinition &definition : SpellbookSchoolUiDefinitions)
    {
        if (skin.page(definition.firstSpellId) == nullptr && memberHasSchool(definition.school))
        {
            add(definition.school, nullptr);
        }
    }

    return tabs;
}

GameplayResolvedHudLayoutElement spellbookSkinScreenRect(
    const GameplayResolvedHudLayoutElement &root,
    const SpellbookSkinRect &rect)
{
    const float scale = root.width / 640;
    GameplayResolvedHudLayoutElement resolved;
    resolved.x = root.x + rect.x * scale;
    resolved.y = root.y + rect.y * scale;
    resolved.width = rect.width * scale;
    resolved.height = rect.height * scale;
    resolved.scale = root.scale;
    return resolved;
}
}
