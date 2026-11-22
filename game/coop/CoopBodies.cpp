#include "game/coop/CoopBodies.h"

#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/party/Party.h"
#include "game/render/HeldWeapons.h"
#include "game/tables/ItemTable.h"
#include "game/ui/GameplayUiSkin.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <string_view>

namespace OpenYAMM::Game
{
namespace
{
// What a class looks like, read off its name: a class and its promotions share one.
enum class BodyKind : uint8_t
{
    Any,
    Warrior,
    Archer,
    Thief,
    Monk,
    Priest,
    Mage,
    Necromancer,
    DeathKnight,
    Seraphim,
    Shaman,
    Peasant,
};

enum class BodySex : uint8_t
{
    Any,
    Male,
    Female,
};

struct ClassKind
{
    // Part of the class name, lowercase and without spaces; the whole name where `whole` is set.
    std::string_view classPart;
    BodyKind kind;
    bool whole = false;
};

// Checked in order, so the longer names stand before the names they contain (a Death Knight before a Knight, a
// Warrior Mage before a Mage, a Lich King before a Lich). The Monk's Initiate and Master are whole names: a Master
// Archer and a Master Wizard are not monks.
constexpr std::array<ClassKind, 50> ClassKinds = {{
    {"deathknight", BodyKind::DeathKnight},
    {"deathlord", BodyKind::DeathKnight},
    {"lichking", BodyKind::DeathKnight},
    {"seraphim", BodyKind::Seraphim},
    {"angel", BodyKind::Seraphim},
    {"shaman", BodyKind::Shaman},
    {"sekhem", BodyKind::Shaman},
    {"marabou", BodyKind::Shaman},
    {"peasant", BodyKind::Peasant},
    {"warriormage", BodyKind::Archer},
    {"battlemage", BodyKind::Archer},
    {"archer", BodyKind::Archer},
    {"sniper", BodyKind::Archer},
    {"ranger", BodyKind::Archer},
    {"hunter", BodyKind::Archer},
    {"darkelf", BodyKind::Archer},
    {"patriarch", BodyKind::Archer},
    {"knight", BodyKind::Warrior},
    {"cavalier", BodyKind::Warrior},
    {"champion", BodyKind::Warrior},
    {"paladin", BodyKind::Warrior},
    {"crusader", BodyKind::Warrior},
    {"hero", BodyKind::Warrior},
    {"villain", BodyKind::Warrior},
    {"thief", BodyKind::Thief},
    {"rogue", BodyKind::Thief},
    {"assassin", BodyKind::Thief},
    {"spy", BodyKind::Thief, true},
    {"monk", BodyKind::Monk},
    {"ninja", BodyKind::Monk},
    {"initiate", BodyKind::Monk, true},
    {"master", BodyKind::Monk, true},
    {"necromancer", BodyKind::Necromancer},
    {"lich", BodyKind::Necromancer},
    {"cleric", BodyKind::Priest},
    {"priest", BodyKind::Priest},
    {"druid", BodyKind::Priest},
    {"warlock", BodyKind::Priest},
    {"sorcerer", BodyKind::Mage},
    {"wizard", BodyKind::Mage},
    {"mage", BodyKind::Mage},
    {"element", BodyKind::Mage},
    // The classes of a race, where a character of another race has one (MAW's free selection).
    {"vampire", BodyKind::Thief},
    {"nosferatu", BodyKind::Thief},
    {"minotaur", BodyKind::Warrior},
    {"troll", BodyKind::Warrior},
    {"dragon", BodyKind::Warrior},
    {"wyrm", BodyKind::Warrior},
    {"fighter", BodyKind::Warrior},
    {"mercenary", BodyKind::Warrior},
}};

// The kind a kind without a fitting body stands by.
constexpr BodyKind generalKind(BodyKind kind)
{
    switch (kind)
    {
        case BodyKind::DeathKnight:
        case BodyKind::Peasant:
            return BodyKind::Warrior;

        case BodyKind::Seraphim:
        case BodyKind::Shaman:
            return BodyKind::Priest;

        case BodyKind::Necromancer:
            return BodyKind::Mage;

        default:
            return BodyKind::Any;
    }
}

// Race ids are character_selection.yml's.
constexpr uint32_t RaceHuman = 0;
constexpr uint32_t RaceVampire = 1;
constexpr uint32_t RaceDarkElf = 2;
constexpr uint32_t RaceMinotaur = 3;
constexpr uint32_t RaceTroll = 4;
constexpr uint32_t RaceDragon = 5;
constexpr uint32_t RaceUndead = 6;
constexpr uint32_t RaceElf = 7;
// MM7's goblins and MM9's half-orcs.
constexpr uint32_t RaceGoblin = 8;
constexpr uint32_t RaceDwarf = 9;
constexpr uint32_t RaceZombie = 10;
constexpr uint32_t SexFemale = 1;

// The models that stand for a race, a sex and a kind of class, best first: those of the worlds' monsters and
// townsfolk that have a run and an attack (the user's choices of 2026-11-21, then the nearest of each other world).
// For one character the rows are tried by kind (its own, its general one, then any), and within a kind in this
// order, so a woman's rows stand before the rows of both sexes. A hooded or helmeted model serves both sexes.
struct BodyRow
{
    uint32_t raceId;
    BodySex sex;
    BodyKind kind;
    std::array<std::string_view, 6> descriptors;
};

constexpr std::array<BodyRow, 40> BodyRows = {{
    {RaceDragon, BodySex::Any, BodyKind::Any, {"Wimpy Dragon A", "Dragon A", "ADragon A", "DragonLand A", "", ""}},
    {RaceUndead, BodySex::Any, BodyKind::Any,
        {"Lich A", "BLich A", "MM9 Lich A", "Necromancer (monster) A", "Skeleton A", ""}},
    {RaceZombie, BodySex::Any, BodyKind::Any, {"Zombie A", "Ghoul A", "MM9 Zombie A", "", "", ""}},
    {RaceTroll, BodySex::Any, BodyKind::Any, {"Troll A", "ATroll A", "Troll Pesant A", "", "", ""}},
    {RaceMinotaur, BodySex::Any, BodyKind::Any,
        {"Minotaur A", "BMinotaur A", "AMinotaur A", "Minotaur Pesant A", "", ""}},
    // A vampire woman has no model with an attack yet: the man's.
    {RaceVampire, BodySex::Any, BodyKind::Any,
        {"Vampire A", "Vampire (monster) A", "MM9 Nosferatu A", "", "", ""}},
    {RaceDarkElf, BodySex::Any, BodyKind::Any,
        {"Dark Elf Warrior A", "Elf Archer A", "Elf Spearman A", "", "", ""}},

    // An elf in a closed helm or a hood is the human's model; the others are the elves' own.
    {RaceElf, BodySex::Female, BodyKind::Warrior, {"Fighter Chain A", "", "", "", "", ""}},
    {RaceElf, BodySex::Male, BodyKind::Warrior, {"Fighter Plate A", "Swordsman A", "", "", "", ""}},
    {RaceElf, BodySex::Male, BodyKind::Thief, {"BThief A", "", "", "", "", ""}},
    {RaceElf, BodySex::Any, BodyKind::Monk, {"Monk A", "BMonk A", "", "", "", ""}},
    {RaceElf, BodySex::Female, BodyKind::Any, {"Elf Archer A", "", "", "", "", ""}},
    {RaceElf, BodySex::Any, BodyKind::Any, {"Elf Spearman A", "Elf Archer A", "Dark Elf Warrior A", "", "", ""}},

    // The goblin with a cast clip for those who cast.
    {RaceGoblin, BodySex::Any, BodyKind::Priest, {"BGoblin A", "Goblin A", "MM9 Half Orc A", "", "", ""}},
    {RaceGoblin, BodySex::Any, BodyKind::Mage, {"BGoblin A", "Goblin A", "MM9 Half Orc A", "", "", ""}},
    {RaceGoblin, BodySex::Any, BodyKind::Any, {"Goblin A", "BGoblin A", "MM9 Half Orc A", "", "", ""}},

    {RaceDwarf, BodySex::Any, BodyKind::Warrior, {"Dwarf A", "BDwarf A", "MM9 Dwarf A", "Dark Dwarf A", "", ""}},
    {RaceDwarf, BodySex::Any, BodyKind::Archer, {"Dark Dwarf A", "Dwarf A", "BDwarf A", "MM9 Dwarf A", "", ""}},
    {RaceDwarf, BodySex::Any, BodyKind::Any, {"BDwarf A", "Dwarf A", "MM9 Dwarf A", "Dark Dwarf A", "", ""}},

    // A human, and every race the mounted worlds have no model of.
    {RaceHuman, BodySex::Female, BodyKind::Warrior,
        {"Fighter Chain A", "Barbarian A", "MM9 251 Kira the Cold", "Pirate Crossbowman (Female) A", "PeasantF3 A",
            ""}},
    {RaceHuman, BodySex::Any, BodyKind::Warrior,
        {"Fighter Plate A", "Swordsman A", "Nobleman A", "Human Mercenary A", "FighterChain A", "KnightPlate A"}},
    {RaceHuman, BodySex::Female, BodyKind::Archer,
        {"BArcher A", "Elf Archer A", "Pirate Crossbowman (Female) A", "", "", ""}},
    {RaceHuman, BodySex::Any, BodyKind::Archer, {"Archer A", "BArcher A", "Elf Archer A", "", "", ""}},
    {RaceHuman, BodySex::Female, BodyKind::Thief, {"Pirate Crossbowman (Female) A", "", "", "", "", ""}},
    {RaceHuman, BodySex::Any, BodyKind::Thief,
        {"BThief A", "Thief A", "Fighter Leather A", "FighterLeath A", "", ""}},
    {RaceHuman, BodySex::Any, BodyKind::Monk, {"Monk A", "BMonk A", "MM9 Monk A", "", "", ""}},
    {RaceHuman, BodySex::Female, BodyKind::Priest, {"Druidess A", "Warlock A", "PeasantF4 A", "", "", ""}},
    {RaceHuman, BodySex::Any, BodyKind::Priest,
        {"Cleric A", "Cleric (human male) A", "Cleric Sun A", "Cleric Moon A", "", ""}},
    {RaceHuman, BodySex::Female, BodyKind::Necromancer, {"Necromancer A", "", "", "", "", ""}},
    {RaceHuman, BodySex::Female, BodyKind::Mage, {"Warlock A", "Necromancer A", "Druidess A", "PeasantF4 A", "", ""}},
    {RaceHuman, BodySex::Any, BodyKind::Mage,
        {"Sorcerer A", "Mage A", "Necromancer (monster) A", "Pirate Mage Male A", "MM9 Evil Sorcerer A", ""}},
    {RaceHuman, BodySex::Any, BodyKind::DeathKnight, {"KnightPlate A", "", "", "", "", ""}},
    {RaceHuman, BodySex::Any, BodyKind::Seraphim, {"Angel A", "", "", "", "", ""}},
    {RaceHuman, BodySex::Female, BodyKind::Shaman, {"PeasantF4 A", "", "", "", "", ""}},
    {RaceHuman, BodySex::Any, BodyKind::Shaman, {"PeasantM4 A", "PeasantF4 A", "", "", "", ""}},
    {RaceHuman, BodySex::Female, BodyKind::Peasant, {"PeasantF1 A", "PeasantF3 A", "", "", "", ""}},
    {RaceHuman, BodySex::Any, BodyKind::Peasant, {"PeasantM2 A", "PeasantM3 A", "", "", "", ""}},
    // Any fighter of the mounted worlds, for a world without the first choices.
    {RaceHuman, BodySex::Female, BodyKind::Any,
        {"Fighter Chain A", "Barbarian A", "Pirate Crossbowman (Female) A", "PeasantF3 A", "PeasantF1 A", ""}},
    {RaceHuman, BodySex::Any, BodyKind::Any,
        {"Fighter Plate A", "Human Mercenary A", "KnightPlate A", "Fighter Chain A", "FighterChain A",
            "MM9 Guard A"}},
    {RaceHuman, BodySex::Any, BodyKind::Any, {"Swordsman A", "Nobleman A", "MM9 Nobleman A", "", "", ""}},
}};

BodyKind bodyKind(const std::string &className)
{
    std::string lowered;

    for (char character : className)
    {
        if (character != ' ')
        {
            lowered.push_back(char(std::tolower(static_cast<unsigned char>(character))));
        }
    }

    for (const ClassKind &entry : ClassKinds)
    {
        if (entry.whole ? lowered == entry.classPart : lowered.find(entry.classPart) != std::string::npos)
        {
            return entry.kind;
        }
    }

    return BodyKind::Warrior;
}

// The first mounted model of a race's rows for a sex and a kind; empty when the race has none.
std::string raceBody(
    uint32_t raceId,
    BodySex sex,
    BodyKind kind,
    const std::function<bool(const std::string &)> &binds)
{
    const std::array<BodyKind, 3> kinds = {kind, generalKind(kind), BodyKind::Any};

    for (size_t kindIndex = 0; kindIndex < kinds.size(); ++kindIndex)
    {
        // A kind without a general one is not tried twice.
        if (kindIndex == 1 && kinds[1] == BodyKind::Any)
        {
            continue;
        }

        for (const BodyRow &row : BodyRows)
        {
            if (row.raceId != raceId || row.kind != kinds[kindIndex]
                || (row.sex != BodySex::Any && row.sex != sex))
            {
                continue;
            }

            for (std::string_view descriptor : row.descriptors)
            {
                if (!descriptor.empty() && binds(std::string(descriptor)))
                {
                    return std::string(descriptor);
                }
            }
        }
    }

    return {};
}
}

std::string coopBodyDescriptor(
    uint32_t raceId,
    uint32_t sexId,
    const std::string &className,
    const std::function<bool(const std::string &)> &binds)
{
    const BodySex sex = sexId == SexFemale ? BodySex::Female : BodySex::Male;
    const BodyKind kind = bodyKind(className);

    // The race first: whatever its class, a minotaur is a minotaur.
    if (raceId != RaceHuman)
    {
        if (std::string descriptor = raceBody(raceId, sex, kind, binds); !descriptor.empty())
        {
            return descriptor;
        }
    }

    // A human, and a race the mounted worlds have no model of, by its class.
    return raceBody(RaceHuman, sex, kind, binds);
}

float coopBodyHeight(uint32_t raceId, uint32_t sexId)
{
    const bool woman = sexId == SexFemale;

    switch (raceId)
    {
        case RaceDragon:
            return 370.0f;

        case RaceMinotaur:
        case RaceTroll:
            return 235.0f;

        case RaceDwarf:
            return woman ? 130.0f : 140.0f;

        case RaceGoblin:
            return woman ? 175.0f : 180.0f;

        case RaceUndead:
        case RaceZombie:
            return 195.0f;

        default:
            return woman ? 180.0f : 190.0f;
    }
}

uint8_t coopGearTier(std::span<const uint8_t> pieceTiers)
{
    if (pieceTiers.empty())
    {
        return 0;
    }

    uint32_t sum = 0;

    for (uint8_t tier : pieceTiers)
    {
        sum += tier;
    }

    const uint32_t count = uint32_t(pieceTiers.size());
    return uint8_t((sum * 2 + count) / (count * 2));
}

uint8_t coopPartyGearTier(std::span<const Character> members, const ItemTable &itemTable,
    const HeldSkinRules &rules)
{
    if (rules.tierCount == 0)
    {
        return 0;
    }

    std::vector<uint8_t> tiers;
    tiers.reserve(members.size() * 9);

    for (const Character &character : members)
    {
        struct Piece
        {
            uint32_t itemId;
            const EquippedItemRuntimeState &state;
        };

        const std::array<Piece, 9> pieces = {{
            {character.equipment.mainHand, character.equipmentRuntime.mainHand},
            {character.equipment.offHand, character.equipmentRuntime.offHand},
            {character.equipment.bow, character.equipmentRuntime.bow},
            {character.equipment.armor, character.equipmentRuntime.armor},
            {character.equipment.helm, character.equipmentRuntime.helm},
            {character.equipment.belt, character.equipmentRuntime.belt},
            {character.equipment.cloak, character.equipmentRuntime.cloak},
            {character.equipment.gauntlets, character.equipmentRuntime.gauntlets},
            {character.equipment.boots, character.equipmentRuntime.boots},
        }};

        for (const Piece &piece : pieces)
        {
            const ItemDefinition *pItem =
                piece.itemId != 0 && !piece.state.broken ? itemTable.get(piece.itemId) : nullptr;

            if (pItem == nullptr)
            {
                continue;
            }

            tiers.push_back(heldSkinTier(rules, {.value = pItem->value,
                .equipStat = pItem->equipStat,
                .unique = pItem->rarity != ItemRarity::Common || piece.state.rarity != ItemRarity::Common,
                .enchanted = piece.state.standardEnchantId != 0 || piece.state.specialEnchantId != 0,
                .lootRarity = piece.state.rulesetFields.lootRarity}));
        }
    }

    return coopGearTier(std::span<const uint8_t>(tiers));
}

void renderCoopPlayerLabels(
    const GameplayScreenRuntime &screenRuntime,
    const std::vector<CoopPlayerLabel> &labels,
    const std::function<bool(const bx::Vec3 &, float &, float &)> &project)
{
    constexpr const char *FontName = GameplayUiSkin::CombatFontName;
    constexpr float FontScale = 1.0f;
    constexpr float LiftUnits = 8.0f;
    constexpr uint32_t StandingColor = 0xffc8f0ffu;
    constexpr uint32_t DownColor = 0xff6060e0u;
    constexpr uint32_t PingColor = 0xff60e0ffu;
    const float lineHeight = float(screenRuntime.hudFontHeight(FontName)) * FontScale;

    for (const CoopPlayerLabel &label : labels)
    {
        float screenX = 0.0f;
        float screenY = 0.0f;

        if (label.name.empty() || !project(bx::Vec3{label.x, label.y, label.z + LiftUnits}, screenX, screenY))
        {
            continue;
        }

        const float width = screenRuntime.measureHudTextWidth(FontName, label.name) * FontScale;
        screenRuntime.renderHudTextLine(FontName,
            label.ping ? PingColor : label.down ? DownColor : StandingColor, label.name,
            screenX - width * 0.5f, screenY - lineHeight, FontScale);
    }
}
}
