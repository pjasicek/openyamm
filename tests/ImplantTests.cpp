#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/TextTable.h"
#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayActionController.h"
#include "game/gameplay/GameplayScreenState.h"
#include "game/items/ItemGenerator.h"
#include "game/maps/SaveGame.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/ClassSkillTable.h"
#include "game/ui/GameplayBuffHud.h"
#include "tests/RegressionGameData.h"

#include <algorithm>
#include <array>
#include <filesystem>
#include <fstream>
#include <random>
#include <set>
#include <sstream>

// Hesper's Implants (DECISIONS H-91, level_generation/projects/hesper_hive/concept/implants_ui/REDESIGN_20261126.md):
// the skill, the six sockets open from level 1, the 13 implants' per cent shares (Standard and MAW), two stages, the
// shares of totals through the party rebuild, the timed implants, the world table's checks, saves, the script hooks
// and the held-key fast lane.
namespace
{
using namespace OpenYAMM::Game;

const OpenYAMM::Tests::RegressionGameData &gameData()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    return OpenYAMM::Tests::regressionGameData();
}

std::string sourceFileText(const std::string &relativePath)
{
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / relativePath);
    REQUIRE(file.good());
    std::ostringstream text;
    text << file.rdbuf();
    return text.str();
}

Character makeMember(const std::string &name, const std::string &className)
{
    Character member = {};
    member.name = name;
    member.className = className;
    member.role = className;
    member.level = 5;
    member.might = 15;
    member.intellect = 15;
    member.personality = 15;
    member.endurance = 15;
    member.speed = 15;
    member.accuracy = 15;
    member.luck = 15;
    member.maxHealth = 1000;
    member.health = 1000;
    return member;
}

Party makeParty(const std::vector<Character> &members)
{
    Party party = {};
    party.setClassSkillTable(&gameData().classSkillTable);
    PartySeed seed = {};
    seed.food = 7;
    seed.members = members;
    party.seed(seed);
    return party;
}

// Implants exist only while a world provides them (setImplantsAvailable, set by the data load): the cases that use them
// switch them on for their own length.
struct ImplantsAvailableScope
{
    explicit ImplantsAvailableScope(bool available) : previous(implantsAvailable())
    {
        setImplantsAvailable(available);
    }
    ~ImplantsAvailableScope()
    {
        setImplantsAvailable(previous);
    }
    bool previous;
};

std::vector<std::vector<std::string>> rowsFromText(const std::string &text)
{
    const std::optional<OpenYAMM::Engine::TextTable> table = OpenYAMM::Engine::TextTable::parseTabSeparated(text);
    REQUIRE(table.has_value());
    std::vector<std::vector<std::string>> rows;

    for (size_t rowIndex = 0; rowIndex < table->getRowCount(); ++rowIndex)
    {
        rows.push_back(table->getRow(rowIndex));
    }

    return rows;
}

// The implants table's header and rows, as level_generation/projects/hesper_hive/world/tools/build_world.py writes
// them (output/hesper_hive/KI2/world/data_tables/implants.txt): one row per part, Adrenaline Gland's three.
const std::vector<std::string> ImplantHeader = {"item_id", "socket", "effect", "base_i", "per_level_i", "base_ii",
    "per_level_ii", "maw_base_i", "maw_per_level_i", "maw_base_ii", "maw_per_level_ii", "except", "evolve_ii",
    "evolve_sound"};

const std::vector<std::vector<std::string>> &implantRows()
{
    static const std::vector<std::vector<std::string>> Rows = {
        {"11405", "cranial", "intellect_personality", "5", "0.5", "10", "1", "", "", "", "", "", "250", "60302"},
        {"11409", "cranial", "berserk", "5", "1", "10", "2", "", "", "", "", "", "250", "60302"},
        {"11403", "cardiac", "max_health", "4", "0.4", "8", "0.8", "", "", "", "", "", "250", "60302"},
        {"11404", "cardiac", "max_sp", "4", "0.4", "8", "0.8", "", "", "", "", "", "250", "60302"},
        {"11410", "cardiac", "siphon", "1.5", "0.15", "3", "0.3", "", "", "", "", "", "250", "60302"},
        {"11413", "cardiac", "recovery", "3", "0.3", "6", "0.6", "3", "0.6", "6", "0.68", "", "250", "60302"},
        {"11413", "cardiac", "all_stats", "-4.15", "-0.415", "-8.3", "-0.83", "-1.5", "-0.3", "-3", "-0.6", "speed",
            "250", "60302"},
        {"11413", "cardiac", "max_health", "-2.08", "-0.208", "-4.17", "-0.417", "0", "0", "0", "0", "", "250",
            "60302"},
        {"11400", "dermal", "fire_resistance", "5", "0.5", "10", "1", "", "", "", "", "", "250", "60302"},
        {"11401", "dermal", "armor_class", "2", "0.2", "4", "0.4", "", "", "", "", "", "250", "60302"},
        {"11411", "dermal", "reflect", "3", "0.3", "6", "0.6", "", "", "", "", "", "250", "60302"},
        {"11406", "spinal", "recovery", "1", "0.1", "2", "0.2", "", "", "", "", "", "250", "60302"},
        {"11412", "spinal", "projectile_speed", "5", "1", "10", "2", "", "", "", "", "", "250", "60302"},
        {"11407", "optic", "accuracy", "5", "0.5", "10", "1", "", "", "", "", "", "250", "60302"},
        {"11408", "neural", "converter", "3", "0.3", "6", "0.6", "", "", "", "", "", "250", "60302"},
    };
    return Rows;
}

struct ImplantItem
{
    uint32_t id;
    std::string key;
    std::string name;
};

// The 13 implants (level_generation/projects/hesper_hive/world/source/items.yml).
const std::vector<ImplantItem> &implantItems()
{
    static const std::vector<ImplantItem> Items = {
        {11400, "ember_lattice", "Ember Lattice"},
        {11401, "chitin_graft", "Chitin Graft"},
        {11403, "kreegan_heart", "Kreegan Heart"},
        {11404, "mana_gland", "Mana Gland"},
        {11405, "neural_loom", "Neural Loom"},
        {11406, "reflex_mesh", "Reflex Mesh"},
        {11407, "hunters_eye", "Hunter's Eye"},
        {11408, "converter", "Converter"},
        {11409, "berserkers_seed", "Berserker's Seed"},
        {11410, "siphoner", "Siphoner"},
        {11411, "mirror_carapace", "Mirror Carapace"},
        {11412, "kinetic_coil", "Kinetic Coil"},
        {11413, "adrenaline_gland", "Adrenaline Gland"},
    };
    return Items;
}

// An items row of Hesper's package; an effect profile only where an item_effects row follows.
std::vector<std::string> implantItemRow(uint32_t id, const std::string &key, const std::string &name,
    const std::string &equipStat = "Implant", const std::string &effectProfile = "")
{
    std::vector<std::string> row(32);
    row[0] = std::to_string(id);
    row[1] = "hh_implant_" + key;
    row[2] = name;
    row[3] = "4000";
    row[4] = equipStat;
    row[5] = "Misc";
    row[9] = "0";
    row[10] = "Implant";
    row[16] = "An implant.";
    row[17] = "hesper";
    row[18] = "hesper:item/" + key;
    row[19] = std::to_string(id);
    row[20] = "NoRandom|NoShop";
    row[21] = "5";
    row[25] = effectProfile;
    row[29] = "1";
    row[30] = "1";
    return row;
}

// The engine's items plus the 13 implants and their implants rows. `rows` replaces the implants rows and `header` the
// header (for the loader's checks); `extraEffects` are item_effects rows of `extraItems`.
bool loadImplantTable(ItemTable &table, std::string &error,
    const std::optional<std::vector<std::vector<std::string>>> &rows = std::nullopt,
    const std::vector<std::vector<std::string>> &extraItems = {},
    const std::vector<std::vector<std::string>> &extraEffects = {},
    const std::vector<std::string> &header = ImplantHeader)
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1));
    std::vector<std::vector<std::string>> itemRows =
        rowsFromText(*assetFileSystem.readTextFile("engine/data_tables/items.txt"));
    const std::vector<std::vector<std::string>> randomItemRows =
        rowsFromText(*assetFileSystem.readTextFile("engine/data_tables/random_items.txt"));

    for (const ImplantItem &implant : implantItems())
    {
        itemRows.push_back(implantItemRow(implant.id, implant.key, implant.name));
    }

    itemRows.insert(itemRows.end(), extraItems.begin(), extraItems.end());

    if (!table.load(assetFileSystem, itemRows, randomItemRows))
    {
        error = "items";
        return false;
    }

    std::vector<std::vector<std::string>> withHeader = {header};
    const std::vector<std::vector<std::string>> &body = rows ? *rows : implantRows();
    withHeader.insert(withHeader.end(), body.begin(), body.end());
    return table.loadContentEffectRows(extraEffects, error) && table.loadImplantRows(withHeader, error);
}

const ItemTable &implantTable()
{
    static const ItemTable table = []()
    {
        ItemTable loaded;
        std::string error;
        REQUIRE_MESSAGE(loadImplantTable(loaded, error), error);
        return loaded;
    }();
    return table;
}

InventoryItem implantItem(uint32_t itemId)
{
    return ItemGenerator::makeInventoryItem(itemId, implantTable(), ItemGenerationMode::Generic);
}

// A party of one with the implants' table.
Party implantParty()
{
    Party party = makeParty({makeMember("Ada", "Knight")});
    party.setItemTable(&implantTable());
    return party;
}

void setImplants(Party &party, uint32_t level, size_t memberIndex = 0)
{
    party.member(memberIndex)->skills["Implants"] = {"Implants", level, SkillMastery::Normal};
    party.rebuildMagicalBonusesFromBuffs();
}

// Fits an implant regardless of the skill (as an old save would hold it), then rebuilds.
void wear(Party &party, ImplantSocket socket, uint32_t itemId, uint32_t kills = 0, size_t memberIndex = 0)
{
    party.member(memberIndex)->implants[size_t(socket)] = implantItem(itemId);
    party.member(memberIndex)->implants[size_t(socket)].implantKills = kills;
    party.rebuildMagicalBonusesFromBuffs();
}

void unwear(Party &party, ImplantSocket socket, size_t memberIndex = 0)
{
    party.member(memberIndex)->implants[size_t(socket)] = {};
    party.rebuildMagicalBonusesFromBuffs();
}

// The seven primary stats' totals as the implants count them (base, permanent and magical bonuses), in
// ImplantStatNames' order: Might, Intellect, Personality, Endurance, Accuracy, Speed, Luck.
std::array<int, 7> primaryTotals(const Character &member)
{
    return {int(member.might) + member.permanentBonuses.might + member.magicalBonuses.might,
        int(member.intellect) + member.permanentBonuses.intellect + member.magicalBonuses.intellect,
        int(member.personality) + member.permanentBonuses.personality + member.magicalBonuses.personality,
        int(member.endurance) + member.permanentBonuses.endurance + member.magicalBonuses.endurance,
        int(member.accuracy) + member.permanentBonuses.accuracy + member.magicalBonuses.accuracy,
        int(member.speed) + member.permanentBonuses.speed + member.magicalBonuses.speed,
        int(member.luck) + member.permanentBonuses.luck + member.magicalBonuses.luck};
}

void setPrimaryStats(Character &member, const std::array<uint32_t, 7> &stats)
{
    member.might = stats[0];
    member.intellect = stats[1];
    member.personality = stats[2];
    member.endurance = stats[3];
    member.accuracy = stats[4];
    member.speed = stats[5];
    member.luck = stats[6];
}

int maxHealthOf(const Character &member)
{
    return GameMechanics::calculateEffectiveCharacterMaxHealth(member);
}

int maxSpellPointsOf(const Character &member)
{
    return GameMechanics::calculateEffectiveCharacterMaxSpellPoints(member);
}

const ImplantComponent *findComponent(uint32_t itemId, ImplantEffect effect)
{
    const ImplantDefinition *pImplant = implantTable().implant(itemId);
    REQUIRE(pImplant != nullptr);

    for (const ImplantComponent &component : pImplant->components)
    {
        if (component.effect == effect)
        {
            return &component;
        }
    }

    return nullptr;
}

}

TEST_CASE("implants: skill 48 is Implants, an ordinary skill every class learns at Normal, never listed")
{
    const ImplantsAvailableScope implants(true);
    CHECK_EQ(skillNameForSkillId(48).value_or(""), "Implants");
    CHECK_EQ(canonicalSkillName("cybernetics"), "Implants");
    CHECK_EQ(canonicalSkillName("Cybernetics"), "Implants");
    CHECK_EQ(displaySkillName("Implants"), "Implants");
    CHECK_FALSE(isTechnologySkill("Implants"));
    CHECK(isTaughtOnlySkill("Implants"));
    CHECK(std::find(skillSheetGroupSkillNames(SkillSheetGroup::Misc).begin(),
              skillSheetGroupSkillNames(SkillSheetGroup::Misc).end(), "Implants")
        != skillSheetGroupSkillNames(SkillSheetGroup::Misc).end());

    // Raised with skill points at the new level, as any skill.
    Character character = makeMember("Ada", "Knight");
    character.skills["Implants"] = {"Implants", 3, SkillMastery::Normal};
    CHECK_EQ(standardSkillRules().skillRaiseCost(character, "Implants"), 4u);
    character.skillPoints = 4;
    character.techPoints = 0;
    CHECK_EQ(character.pointsForRaisingSkill("Implants"), 4u);

    // No masteries (H-91): every class's cap is Normal; no class starts with it or lists it.
    const ClassSkillTable &table = gameData().classSkillTable;

    for (const char *pClassName : {"Knight", "Sorcerer", "Lich", "Peasant", "Dragon", "Monk", "Thief"})
    {
        CHECK_EQ(table.getClassCap(pClassName, "Implants"), SkillMastery::Normal);
        CHECK_EQ(table.getEffectiveStartingSkillAvailability(pClassName, 0, "Implants"),
            StartingSkillAvailability::None);

        for (const CharacterSkill &skill : table.getDefaultSkillsForCharacter(pClassName, 0))
        {
            CHECK_NE(skill.name, "Implants");
        }
    }

    // The skill's EVT variable keeps 0x0144 under its new name.
    CHECK_EQ(static_cast<uint32_t>(EvtVariable::ImplantsSkill), 0x0144u);
}

TEST_CASE("implants: every part's per cent at skill 0, 25 and 50, both stages, Standard and MAW; level 50 caps")
{
    const ImplantsAvailableScope implants(true);

    struct ExpectedPart
    {
        uint32_t itemId;
        ImplantEffect effect;
        ImplantSocket socket;
        // At skill 0, 25 and 50.
        std::array<float, 3> standardOne;
        std::array<float, 3> standardTwo;
        std::array<float, 3> mawOne;
        std::array<float, 3> mawTwo;
    };

    // The redesign's table (Standard; MAW the same except Adrenaline Gland's maw_ columns).
    const std::vector<ExpectedPart> parts = {
        {11405, ImplantEffect::IntellectPersonality, ImplantSocket::Cranial, {5, 17.5f, 30}, {10, 35, 60},
            {5, 17.5f, 30}, {10, 35, 60}},
        {11409, ImplantEffect::BerserkDamage, ImplantSocket::Cranial, {5, 30, 55}, {10, 60, 110}, {5, 30, 55},
            {10, 60, 110}},
        {11408, ImplantEffect::Converter, ImplantSocket::Neural, {3, 10.5f, 18}, {6, 21, 36}, {3, 10.5f, 18},
            {6, 21, 36}},
        {11403, ImplantEffect::MaxHealth, ImplantSocket::Cardiac, {4, 14, 24}, {8, 28, 48}, {4, 14, 24},
            {8, 28, 48}},
        {11404, ImplantEffect::MaxSpellPoints, ImplantSocket::Cardiac, {4, 14, 24}, {8, 28, 48}, {4, 14, 24},
            {8, 28, 48}},
        {11410, ImplantEffect::Siphon, ImplantSocket::Cardiac, {1.5f, 5.25f, 9}, {3, 10.5f, 18}, {1.5f, 5.25f, 9},
            {3, 10.5f, 18}},
        {11413, ImplantEffect::Recovery, ImplantSocket::Cardiac, {3, 10.5f, 18}, {6, 21, 36}, {3, 18, 33},
            {6, 23, 40}},
        {11413, ImplantEffect::AllStats, ImplantSocket::Cardiac, {-4.15f, -14.525f, -24.9f}, {-8.3f, -29.05f, -49.8f},
            {-1.5f, -9, -16.5f}, {-3, -18, -33}},
        {11413, ImplantEffect::MaxHealth, ImplantSocket::Cardiac, {-2.08f, -7.28f, -12.48f},
            {-4.17f, -14.595f, -25.02f}, {0, 0, 0}, {0, 0, 0}},
        {11400, ImplantEffect::FireResistance, ImplantSocket::Dermal, {5, 17.5f, 30}, {10, 35, 60}, {5, 17.5f, 30},
            {10, 35, 60}},
        {11401, ImplantEffect::ArmorClass, ImplantSocket::Dermal, {2, 7, 12}, {4, 14, 24}, {2, 7, 12}, {4, 14, 24}},
        {11411, ImplantEffect::Reflect, ImplantSocket::Dermal, {3, 10.5f, 18}, {6, 21, 36}, {3, 10.5f, 18},
            {6, 21, 36}},
        {11406, ImplantEffect::Recovery, ImplantSocket::Spinal, {1, 3.5f, 6}, {2, 7, 12}, {1, 3.5f, 6}, {2, 7, 12}},
        {11412, ImplantEffect::ProjectileSpeed, ImplantSocket::Spinal, {5, 30, 55}, {10, 60, 110}, {5, 30, 55},
            {10, 60, 110}},
        {11407, ImplantEffect::Accuracy, ImplantSocket::Optic, {5, 17.5f, 30}, {10, 35, 60}, {5, 17.5f, 30},
            {10, 35, 60}},
    };
    const std::array<int, 3> levels = {0, 25, 50};
    MawRules maw(RulesetOptions{}, MawMapLevels{});
    const SkillRules &mawSkills = maw.gameRules().skills;

    for (const ExpectedPart &part : parts)
    {
        CAPTURE(part.itemId);
        CAPTURE(int(part.effect));
        const ImplantDefinition *pImplant = implantTable().implant(part.itemId);
        REQUIRE(pImplant != nullptr);
        CHECK_EQ(pImplant->socket, part.socket);
        CHECK_EQ(pImplant->stageTwoKills, 250u);
        CHECK_EQ(pImplant->evolveSoundId, 60302u);
        const ImplantComponent *pComponent = findComponent(part.itemId, part.effect);
        // Adrenaline Gland's own MaxHealth part, not Kreegan Heart's.
        REQUIRE(pComponent != nullptr);

        for (size_t index = 0; index < levels.size(); ++index)
        {
            CAPTURE(levels[index]);
            CHECK_EQ(implantEffectPercent(pComponent->standard, 1, levels[index]),
                doctest::Approx(part.standardOne[index]));
            CHECK_EQ(implantEffectPercent(pComponent->standard, 2, levels[index]),
                doctest::Approx(part.standardTwo[index]));
            CHECK_EQ(implantEffectPercent(pComponent->maw, 1, levels[index]), doctest::Approx(part.mawOne[index]));
            CHECK_EQ(implantEffectPercent(pComponent->maw, 2, levels[index]), doctest::Approx(part.mawTwo[index]));
            // The rules hand out their own values.
            CHECK_EQ(implantEffectPercent(standardSkillRules().implantShare(*pComponent), 2, levels[index]),
                doctest::Approx(part.standardTwo[index]));
            CHECK_EQ(implantEffectPercent(mawSkills.implantShare(*pComponent), 2, levels[index]),
                doctest::Approx(part.mawTwo[index]));
        }

        // Past 50 the per-level share stops: 60 and 500 count as 50.
        for (const int level : {60, 500})
        {
            CHECK_EQ(implantEffectPercent(pComponent->standard, 1, level), doctest::Approx(part.standardOne[2]));
            CHECK_EQ(implantEffectPercent(pComponent->standard, 2, level), doctest::Approx(part.standardTwo[2]));
            CHECK_EQ(implantEffectPercent(pComponent->maw, 2, level), doctest::Approx(part.mawTwo[2]));
        }
    }

    // Adrenaline Gland: three parts; its stat cut spares Speed; Standard does not touch SP.
    REQUIRE_EQ(implantTable().implant(11413)->components.size(), 3u);
    CHECK_EQ(findComponent(11413, ImplantEffect::AllStats)->exceptStats, uint8_t(1u << 5));
    CHECK_EQ(ImplantStatNames[5], "speed");
    CHECK(findComponent(11413, ImplantEffect::MaxSpellPoints) == nullptr);

    for (const ImplantItem &item : implantItems())
    {
        if (item.id != 11413)
        {
            CHECK_EQ(implantTable().implant(item.id)->components.size(), 1u);
        }
    }

    // The effect level: the Implants level with its item bonuses, capped at 50 in every ruleset (MAW has no factor).
    Character character = makeMember("Ada", "Knight");
    CHECK_EQ(standardSkillRules().implantEffectLevel(character), 0);
    CHECK_EQ(mawSkills.implantEffectLevel(character), 0);

    for (const auto &[level, effect] : std::array<std::pair<uint32_t, int>, 5>{
             {{1, 1}, {30, 30}, {50, 50}, {60, 50}, {500, 50}}})
    {
        character.skills["Implants"] = {"Implants", level, SkillMastery::Normal};
        CHECK_EQ(standardSkillRules().implantEffectLevel(character), effect);
        CHECK_EQ(mawSkills.implantEffectLevel(character), effect);
    }

    // Under MAW's other progressions too.
    RulesetOptions horizontal;
    horizontal.progression = RulesetProgression::Horizontal;
    maw.setOptions(horizontal);
    character.skills["Implants"].level = 30;
    CHECK_EQ(mawSkills.implantEffectLevel(character), 30);
    character.skills["Implants"].level = 100;
    CHECK_EQ(mawSkills.implantEffectLevel(character), 50);

    // How the inspect lines print the per cents.
    // Values with one decimal at most (a half rounds up even where float arithmetic left it just below), rates with
    // three significant digits at most; a no-break space before "%" keeps a number and its sign on one line.
    CHECK_EQ(implantPercentText(1.5f), "1.5");
    CHECK_EQ(implantPercentText(12.0f), "12");
    CHECK_EQ(implantPercentText(14.595f), "14.6");
    CHECK_EQ(implantPercentText(-29.05f), "-29.1");
    CHECK_EQ(implantPercentText(-14.525f), "-14.5");
    CHECK_EQ(implantRateText(0.415f), "0.415");
    CHECK_EQ(implantRateText(0.208f), "0.208");
    CHECK_EQ(implantRateText(0.83f), "0.83");
    CHECK_EQ(implantRateText(4.15f), "4.15");
    CHECK_EQ(implantRateText(10.0f), "10");
    CHECK_EQ(implantRateText(-0.417f), "-0.417");
    CHECK_EQ(implantEffectText(ImplantEffect::IntellectPersonality, 12.5f),
        "+12.5 % of total Intellect and Personality");
    CHECK_EQ(implantEffectText(ImplantEffect::MaxHealth, -2.08f), "-2.1 % of total hit points");
    CHECK_EQ(implantEffectText(ImplantEffect::AllStats, -29.05f, uint8_t(1u << 5)),
        "-29.1 % of every attribute except Speed");
    CHECK_EQ(parseImplantEffect("berserk"), std::optional<ImplantEffect>(ImplantEffect::BerserkDamage));
    CHECK_FALSE(parseImplantEffect("leech").has_value());
}

TEST_CASE("implants: two stages, II at 250 kills (MAW 750), credited by party kills with a line and a sound")
{
    const ImplantsAvailableScope implants(true);
    const ImplantDefinition *pLoom = implantTable().implant(11405);
    REQUIRE(pLoom != nullptr);
    CHECK_EQ(implantStage(*pLoom, 0, 1.0f), 1u);
    CHECK_EQ(implantStage(*pLoom, 249, 1.0f), 1u);
    CHECK_EQ(implantStage(*pLoom, 250, 1.0f), 2u);
    // No stage III: any count past II stays II.
    CHECK_EQ(implantStage(*pLoom, 400, 1.0f), 2u);
    CHECK_EQ(implantStage(*pLoom, 1000000, 1.0f), 2u);
    CHECK_EQ(implantStageKills(*pLoom, 1, 1.0f), 0u);
    CHECK_EQ(implantStageKills(*pLoom, 2, 1.0f), 250u);
    // MAW's evolve factor 3: 750.
    CHECK_EQ(implantStageKills(*pLoom, 2, 3.0f), 750u);
    CHECK_EQ(implantStage(*pLoom, 749, 3.0f), 1u);
    CHECK_EQ(implantStage(*pLoom, 750, 3.0f), 2u);
    CHECK_EQ(implantStageName(1), "I");
    CHECK_EQ(implantStageName(2), "II");
    CHECK_EQ(implantStageName(3), "II");

    // The rules' factors: Standard 1, MAW 3 unless its balance file says otherwise.
    CHECK_EQ(standardSkillRules().implantEvolveFactor(), doctest::Approx(1.0f));
    MawRules maw(RulesetOptions{}, MawMapLevels{});
    CHECK_EQ(maw.gameRules().skills.implantEvolveFactor(), doctest::Approx(3.0f));
    MawMapLevels levels;
    std::string error;
    REQUIRE_MESSAGE(levels.loadWorldBalance("implants: {evolve_factor: 2.5}\n", error), error);
    MawRules slower(RulesetOptions{}, levels);
    CHECK_EQ(slower.gameRules().skills.implantEvolveFactor(), doctest::Approx(2.5f));
    CHECK_FALSE(levels.loadWorldBalance("implants: {evolve_factor: 0}\n", error));

    // Party kills: Neural Loom at Implants 10, 10 % of Intellect at I, 20 % at II.
    Party party = makeParty({makeMember("Ada", "Knight"), makeMember("Bram", "Cleric")});
    party.setItemTable(&implantTable());
    party.member(0)->intellect = 100;
    party.member(1)->intellect = 100;
    setImplants(party, 10, 0);
    setImplants(party, 10, 1);
    wear(party, ImplantSocket::Cranial, 11405, 0, 0);
    wear(party, ImplantSocket::Cranial, 11405, 0, 1);
    // The dead do not count.
    party.member(1)->conditions.set(size_t(CharacterCondition::Dead));
    const InventoryItem &loom = party.member(0)->implants[size_t(ImplantSocket::Cranial)];
    CHECK_EQ(party.member(0)->magicalBonuses.intellect, 10);
    CHECK_EQ(party.implantStage(loom), 1u);

    party.clearPendingAudioRequests();
    CHECK(party.creditImplantKills(249).empty());
    CHECK_EQ(loom.implantKills, 249u);
    CHECK_EQ(party.member(1)->implants[size_t(ImplantSocket::Cranial)].implantKills, 0u);
    const std::vector<std::string> evolved = party.creditImplantKills(1);
    REQUIRE_EQ(evolved.size(), 1u);
    CHECK_NE(evolved.front().find("Ada"), std::string::npos);
    CHECK_NE(evolved.front().find("Neural Loom"), std::string::npos);
    CHECK_NE(evolved.front().find("II"), std::string::npos);
    REQUIRE_FALSE(party.pendingAudioRequests().empty());
    CHECK_EQ(uint32_t(party.pendingAudioRequests().back().soundId), 60302u);
    CHECK_EQ(party.implantStage(loom), 2u);
    CHECK_EQ(party.member(0)->magicalBonuses.intellect, 20);

    // Nothing past II.
    CHECK(party.creditImplantKills(100000).empty());
    CHECK_EQ(party.implantStage(loom), 2u);
    CHECK_EQ(loom.implantKills, 100250u);

    // Taken out, its count stays with it.
    InventoryItem taken = {};
    REQUIRE(party.takeImplant(0, ImplantSocket::Cranial, taken));
    CHECK_EQ(taken.implantKills, 100250u);

    // MAW: 750.
    Party mawParty = implantParty();
    mawParty.setRules(&maw.gameRules());
    setImplants(mawParty, 10);
    wear(mawParty, ImplantSocket::Cranial, 11405);
    CHECK(mawParty.creditImplantKills(250).empty());
    CHECK(mawParty.creditImplantKills(499).empty());
    CHECK_EQ(mawParty.creditImplantKills(1).size(), 1u);
    CHECK_EQ(mawParty.implantStage(mawParty.member(0)->implants[size_t(ImplantSocket::Cranial)]), 2u);
}

TEST_CASE("implants: Implants level 1 opens all six sockets; an implant fits only its own socket")
{
    const ImplantsAvailableScope implants(true);
    Party party = implantParty();
    Character &member = *party.member(0);
    std::optional<InventoryItem> replaced;

    // Without the skill no socket is open and the overlay stays hidden.
    for (size_t socket = 0; socket < ImplantSocketCount; ++socket)
    {
        CHECK_FALSE(member.implantSocketOpen(ImplantSocket(socket)));
    }

    CHECK_FALSE(member.showsImplantSockets());
    CHECK_EQ(party.fitImplant(0, ImplantSocket::Cardiac, implantItem(11404), replaced),
        Party::ImplantFitResult::SocketClosed);

    // Level 0 is not learned.
    setImplants(party, 0);
    CHECK_FALSE(member.implantSocketOpen(ImplantSocket::Cranial));

    // Level 1 (Normal, the only rank): all six.
    setImplants(party, 1);
    CHECK(member.showsImplantSockets());

    for (size_t socket = 0; socket < ImplantSocketCount; ++socket)
    {
        CHECK(member.implantSocketOpen(ImplantSocket(socket)));
    }

    // Not an implant; another socket's implant.
    CHECK_EQ(
        party.fitImplant(0, ImplantSocket::Cardiac, implantItem(182), replaced), Party::ImplantFitResult::NotImplant);
    CHECK_EQ(party.fitImplant(0, ImplantSocket::Cardiac, implantItem(11405), replaced),
        Party::ImplantFitResult::WrongSocket);
    CHECK_EQ(party.fitImplant(0, ImplantSocket::Neural, implantItem(11400), replaced),
        Party::ImplantFitResult::WrongSocket);
    CHECK_EQ(party.implantSocketForItem(11400), std::optional<ImplantSocket>(ImplantSocket::Dermal));
    CHECK_EQ(party.implantSocketForItem(11408), std::optional<ImplantSocket>(ImplantSocket::Neural));
    CHECK_EQ(party.implantSocketForItem(11413), std::optional<ImplantSocket>(ImplantSocket::Cardiac));
    CHECK_FALSE(party.implantSocketForItem(182).has_value());

    // Fitting, then replacing hands the old one back.
    REQUIRE_EQ(
        party.fitImplant(0, ImplantSocket::Cardiac, implantItem(11403), replaced), Party::ImplantFitResult::Fitted);
    CHECK_FALSE(replaced.has_value());
    REQUIRE_EQ(
        party.fitImplant(0, ImplantSocket::Cardiac, implantItem(11404), replaced), Party::ImplantFitResult::Fitted);
    REQUIRE(replaced.has_value());
    CHECK_EQ(replaced->objectDescriptionId, 11403u);
    CHECK_EQ(member.implants[size_t(ImplantSocket::Cardiac)].objectDescriptionId, 11404u);

    // Every kind fits its socket at level 1.
    for (const auto &[socket, itemId] : std::array<std::pair<ImplantSocket, uint32_t>, 5>{
             {{ImplantSocket::Cranial, 11405}, {ImplantSocket::Spinal, 11406}, {ImplantSocket::Dermal, 11401},
                 {ImplantSocket::Optic, 11407}, {ImplantSocket::Neural, 11408}}})
    {
        CHECK_EQ(party.fitImplant(0, socket, implantItem(itemId), replaced), Party::ImplantFitResult::Fitted);
    }

    CHECK_EQ(member.implantArmorClassPercent, doctest::Approx(2.2f));

    // Without the skill an implant still fitted does nothing, keeps the overlay shown and can be taken out.
    member.skills.erase("Implants");
    party.rebuildMagicalBonusesFromBuffs();
    CHECK_EQ(member.implantArmorClassPercent, doctest::Approx(0.0f));
    CHECK(member.showsImplantSockets());
    InventoryItem taken = {};
    REQUIRE(party.takeImplant(0, ImplantSocket::Dermal, taken));
    CHECK_EQ(taken.objectDescriptionId, 11401u);
    CHECK_FALSE(party.takeImplant(0, ImplantSocket::Dermal, taken));
}

// A world's fit_sound and remove_sound columns: fitting plays the implant's fit sound, taking it out its remove sound;
// a table without the columns (or 0) plays nothing, as before.
TEST_CASE("implants: fitting and taking out play the implant's own sounds, none without them")
{
    const ImplantsAvailableScope implants(true);
    std::vector<std::string> header = ImplantHeader;
    header.push_back("fit_sound");
    header.push_back("remove_sound");
    std::vector<std::vector<std::string>> rows = implantRows();

    for (std::vector<std::string> &row : rows)
    {
        row.push_back("60308");
        row.push_back("60309");
    }

    ItemTable table;
    std::string error;
    REQUIRE_MESSAGE(loadImplantTable(table, error, rows, {}, {}, header), error);
    REQUIRE(table.implant(11403) != nullptr);
    CHECK_EQ(table.implant(11403)->fitSoundId, 60308u);
    CHECK_EQ(table.implant(11403)->removeSoundId, 60309u);
    CHECK_EQ(implantTable().implant(11403)->fitSoundId, 0u);
    CHECK_EQ(implantTable().implant(11403)->removeSoundId, 0u);

    Party party = makeParty({makeMember("Ada", "Knight")});
    party.setItemTable(&table);
    setImplants(party, 1);
    party.clearPendingAudioRequests();
    std::optional<InventoryItem> replaced;
    REQUIRE_EQ(party.fitImplant(0, ImplantSocket::Cardiac, implantItem(11403), replaced),
        Party::ImplantFitResult::Fitted);
    REQUIRE_EQ(party.pendingAudioRequests().size(), 1u);
    CHECK_EQ(uint32_t(party.pendingAudioRequests().back().soundId), 60308u);
    // A world's sound: played from the mounted worlds' table, not the engine's (lane KX).
    CHECK(party.pendingAudioRequests().back().scope == SoundScope::World);

    // A refused fit plays nothing.
    party.clearPendingAudioRequests();
    CHECK_EQ(party.fitImplant(0, ImplantSocket::Neural, implantItem(11403), replaced),
        Party::ImplantFitResult::WrongSocket);
    CHECK(party.pendingAudioRequests().empty());

    InventoryItem taken = {};
    REQUIRE(party.takeImplant(0, ImplantSocket::Cardiac, taken));
    REQUIRE_EQ(party.pendingAudioRequests().size(), 1u);
    CHECK_EQ(uint32_t(party.pendingAudioRequests().back().soundId), 60309u);
    CHECK(party.pendingAudioRequests().back().scope == SoundScope::World);

    // Without the columns: silent.
    Party plain = implantParty();
    setImplants(plain, 1);
    plain.clearPendingAudioRequests();
    REQUIRE_EQ(plain.fitImplant(0, ImplantSocket::Cardiac, implantItem(11403), replaced),
        Party::ImplantFitResult::Fitted);
    REQUIRE(plain.takeImplant(0, ImplantSocket::Cardiac, taken));
    CHECK(plain.pendingAudioRequests().empty());

    // An implant's rows must agree on its sounds (Adrenaline Gland's second of three rows).
    REQUIRE_EQ(rows[6][0], "11413");
    rows[6][header.size() - 1] = "60302";
    ItemTable disagreeing;
    CHECK_FALSE(loadImplantTable(disagreeing, error, rows, {}, {}, header));
    CHECK_NE(error.find("disagree"), std::string::npos);
}

TEST_CASE("implants: Neural Loom and Hunter's Eye add their share of the totals, buffs included, rounded down")
{
    const ImplantsAvailableScope implants(true);
    Party party = implantParty();
    Character &member = *party.member(0);
    setImplants(party, 10);
    // Buffs first: the shares count the totals they make.
    party.applyCharacterBuff(0, CharacterBuffId::TempIntellect, 600.0f, 25, 0, 0, SkillMastery::None, 0);
    party.applyCharacterBuff(0, CharacterBuffId::TempAccuracy, 600.0f, 25, 0, 0, SkillMastery::None, 0);
    party.rebuildMagicalBonusesFromBuffs();
    const std::array<int, 7> before = primaryTotals(member);
    REQUIRE_EQ(before[1], 40);
    REQUIRE_EQ(before[2], 15);
    REQUIRE_EQ(before[4], 40);

    // Neural Loom at Implants 10: 10 % of total Intellect (40: +4) and Personality (15: 1.5, rounded down +1).
    wear(party, ImplantSocket::Cranial, 11405);
    std::array<int, 7> after = primaryTotals(member);
    CHECK_EQ(after[1], 44);
    CHECK_EQ(after[2], 16);
    CHECK_EQ(after[0], before[0]);
    CHECK_EQ(after[4], before[4]);

    // Hunter's Eye: 10 % of total Accuracy.
    wear(party, ImplantSocket::Optic, 11407);
    after = primaryTotals(member);
    CHECK_EQ(after[4], 44);
    CHECK_EQ(after[1], 44);

    // Stage II at Implants 50: 60 %.
    member.implants[size_t(ImplantSocket::Optic)].implantKills = 250;
    setImplants(party, 50);
    CHECK_EQ(primaryTotals(member)[4], 64);

    // The share's size rounds down, gains and costs alike; nothing of a total of 0 or less.
    CHECK_EQ(implantShareOf(100, 5.0f), 5);
    CHECK_EQ(implantShareOf(19, 10.0f), 1);
    CHECK_EQ(implantShareOf(19, -10.0f), -1);
    CHECK_EQ(implantShareOf(100, 18.0f), 18);
    CHECK_EQ(implantShareOf(9, 10.0f), 0);
    CHECK_EQ(implantShareOf(9, -10.0f), 0);
    CHECK_EQ(implantShareOf(0, 50.0f), 0);
    CHECK_EQ(implantShareOf(-10, 50.0f), 0);
    CHECK_EQ(implantShareOf(100, 0.0f), 0);
}

TEST_CASE("implants: Converter moves the share of the other six into the highest, before the other shares")
{
    const ImplantsAvailableScope implants(true);

    // 10 % of each other stat, rounded down, into Might (the highest).
    CHECK_EQ(implantConverterChanges({100, 50, 30, 20, 19, 10, 9}, 10.0f),
        std::array<int, 7>{12, -5, -3, -2, -1, -1, 0});
    // Ties: the first in ImplantStatNames' order (Might, Intellect, Personality, Endurance, Accuracy, Speed, Luck).
    CHECK_EQ(implantConverterChanges({20, 30, 30, 10, 10, 10, 10}, 10.0f),
        std::array<int, 7>{-2, 9, -3, -1, -1, -1, -1});
    CHECK_EQ(implantConverterChanges({10, 10, 10, 10, 40, 40, 10}, 10.0f),
        std::array<int, 7>{-1, -1, -1, -1, 9, -4, -1});
    CHECK_EQ(implantConverterChanges({10, 10, 10, 10, 10, 10, 10}, 10.0f),
        std::array<int, 7>{6, -1, -1, -1, -1, -1, -1});
    CHECK_EQ(implantConverterChanges({10, 10, 10, 10, 10, 10, 10}, 0.0f), std::array<int, 7>{});

    // Through the rebuild: Converter at Implants 10 (6 %), then Neural Loom (10 %) of the converted totals.
    Party party = implantParty();
    Character &member = *party.member(0);
    setPrimaryStats(member, {100, 50, 30, 20, 20, 20, 10});
    setImplants(party, 10);
    REQUIRE_EQ(primaryTotals(member), std::array<int, 7>{100, 50, 30, 20, 20, 20, 10});

    // Converter alone: 3 + 1 + 1 + 1 + 1 + 0 into Might.
    wear(party, ImplantSocket::Neural, 11408);
    CHECK_EQ(primaryTotals(member), std::array<int, 7>{107, 47, 29, 19, 19, 19, 10});

    // With Neural Loom: 47 -> +4 and 29 -> +2, not 50 -> +5 and 30 -> +3.
    wear(party, ImplantSocket::Cranial, 11405);
    CHECK_EQ(primaryTotals(member), std::array<int, 7>{107, 51, 31, 19, 19, 19, 10});
}

TEST_CASE("implants: Adrenaline Gland, Standard: faster recovery, stats but Speed and max HP cut, SP untouched")
{
    const ImplantsAvailableScope implants(true);
    Party party = implantParty();
    Character &member = *party.member(0);
    member.maxSpellPoints = 300;

    // At Implants 1 the 15s lose nothing (4.565 % of 15 rounds to 0), so max HP is the only change: -2.288 %.
    setImplants(party, 1);
    const int healthBefore = maxHealthOf(member);
    const int spellPointsBefore = maxSpellPointsOf(member);
    wear(party, ImplantSocket::Cardiac, 11413);
    const float healthCut = implantEffectPercent(findComponent(11413, ImplantEffect::MaxHealth)->standard, 1, 1);
    CHECK_EQ(healthCut, doctest::Approx(-2.288f));
    CHECK_EQ(maxHealthOf(member), healthBefore + implantShareOf(healthBefore, healthCut));
    CHECK_LT(maxHealthOf(member), healthBefore);
    CHECK_EQ(maxSpellPointsOf(member), spellPointsBefore);
    CHECK_EQ(member.implantRecoveryFactor, doctest::Approx(1.0f - 0.033f));

    // At Implants 10: recovery 6 % shorter; 8.3 % off every stat but Speed, rounded down.
    unwear(party, ImplantSocket::Cardiac);
    setPrimaryStats(member, {100, 60, 60, 120, 80, 100, 40});
    setImplants(party, 10);
    REQUIRE_EQ(primaryTotals(member), std::array<int, 7>{100, 60, 60, 120, 80, 100, 40});
    wear(party, ImplantSocket::Cardiac, 11413);
    CHECK_EQ(primaryTotals(member), std::array<int, 7>{92, 56, 56, 111, 74, 100, 37});
    CHECK_EQ(member.implantRecoveryFactor, doctest::Approx(0.94f));

    // Recovery: applyRecoveryToMember multiplies by the factor.
    member.recoverySecondsRemaining = 0.0f;
    REQUIRE(party.applyRecoveryToMember(0, 2.0f));
    CHECK_EQ(member.recoverySecondsRemaining, doctest::Approx(2.0f * 0.94f));
    CHECK_EQ(member.recoveryTotalSeconds, doctest::Approx(2.0f * 0.94f));

    // With Reflex Mesh (2 % at Implants 10) the cuts multiply: 0.94 x 0.98.
    wear(party, ImplantSocket::Spinal, 11406);
    CHECK_EQ(member.implantRecoveryFactor, doctest::Approx(0.94f * 0.98f));

    // A member at the 30-tick floor gains the full share: the floor shrinks by the same factor.
    const float floorSeconds = ticksToRecoverySeconds(30);
    member.recoverySecondsRemaining = 0.0f;
    REQUIRE(party.applyRecoveryToMember(0, floorSeconds));
    CHECK_EQ(member.recoverySecondsRemaining, doctest::Approx(floorSeconds * 0.94f * 0.98f));

    // Stage II at Implants 50: 36 % and 12 % shorter, 49.8 % off the stats.
    member.implants[size_t(ImplantSocket::Cardiac)].implantKills = 250;
    member.implants[size_t(ImplantSocket::Spinal)].implantKills = 250;
    setImplants(party, 50);
    CHECK_EQ(member.implantRecoveryFactor, doctest::Approx(0.64f * 0.88f));
    CHECK_EQ(primaryTotals(member)[0], 51);
    CHECK_EQ(primaryTotals(member)[5], 100);

    // The factor never goes below 1/30, so the 30-tick floor keeps a tick.
    CHECK_EQ(implantRecoveryCut(1.0f, 6.0f), doctest::Approx(0.94f));
    CHECK_EQ(implantRecoveryCut(0.94f, 2.0f), doctest::Approx(0.9212f));
    CHECK_EQ(implantRecoveryFactor(implantRecoveryCut(1.0f, 100.0f)), doctest::Approx(ImplantMinimumRecoveryFactor));
    CHECK_EQ(implantRecoveryFactor(0.01f), doctest::Approx(1.0f / 30.0f));
    CHECK_EQ(implantRecoveryFactor(0.5f), doctest::Approx(0.5f));
    CHECK_EQ(implantRecoveryFactor(1.5f), doctest::Approx(1.0f));
}

TEST_CASE("implants: Adrenaline Gland under MAW: its own values, Speed spared, no HP cut")
{
    const ImplantsAvailableScope implants(true);
    MawRules maw(RulesetOptions{}, MawMapLevels{});
    Party party = implantParty();
    party.setRules(&maw.gameRules());
    Character &member = *party.member(0);
    member.maxSpellPoints = 300;

    // At Implants 1 (1.8 % off the 15s: nothing) max HP and SP stay; recovery 3.6 % shorter.
    setImplants(party, 1);
    const int healthBefore = maxHealthOf(member);
    const int spellPointsBefore = maxSpellPointsOf(member);
    const std::array<int, 7> fifteens = primaryTotals(member);
    wear(party, ImplantSocket::Cardiac, 11413);
    CHECK_EQ(primaryTotals(member), fifteens);
    CHECK_EQ(maxHealthOf(member), healthBefore);
    CHECK_EQ(maxSpellPointsOf(member), spellPointsBefore);
    CHECK_EQ(member.implantRecoveryFactor, doctest::Approx(1.0f - 0.036f));

    // At Implants 10: 9 % shorter recovery and 4.5 % off every stat but Speed.
    unwear(party, ImplantSocket::Cardiac);
    setPrimaryStats(member, {100, 60, 60, 120, 80, 100, 40});
    setImplants(party, 10);
    const std::array<int, 7> before = primaryTotals(member);
    wear(party, ImplantSocket::Cardiac, 11413);
    const std::array<int, 7> after = primaryTotals(member);
    const float cut = implantEffectPercent(findComponent(11413, ImplantEffect::AllStats)->maw, 1, 10);
    CHECK_EQ(cut, doctest::Approx(-4.5f));

    for (size_t stat = 0; stat < after.size(); ++stat)
    {
        CAPTURE(stat);
        CHECK_EQ(after[stat], stat == 5 ? before[stat] : before[stat] + implantShareOf(before[stat], cut));
    }

    CHECK_LT(after[0], before[0]);
    CHECK_EQ(member.implantRecoveryFactor, doctest::Approx(0.91f));

    // Stage II at Implants 50 (750 kills under MAW): 40 % shorter.
    member.implants[size_t(ImplantSocket::Cardiac)].implantKills = 750;
    setImplants(party, 50);
    CHECK_EQ(member.implantRecoveryFactor, doctest::Approx(0.6f));
    party.setRules(nullptr);
}

TEST_CASE("implants: Kreegan Heart and Mana Gland add their share of the effective maximum HP and SP")
{
    const ImplantsAvailableScope implants(true);
    Party party = implantParty();
    Character &member = *party.member(0);
    member.permanentBonuses.maxHealth = 200;
    member.maxSpellPoints = 500;
    setImplants(party, 10);
    REQUIRE_EQ(maxHealthOf(member), 1200);
    REQUIRE_EQ(maxSpellPointsOf(member), 500);

    // Kreegan Heart at Implants 10: 8 % of 1200.
    wear(party, ImplantSocket::Cardiac, 11403);
    CHECK_EQ(maxHealthOf(member), 1296);
    CHECK_EQ(maxSpellPointsOf(member), 500);
    // Stage II at Implants 50: 48 %.
    member.implants[size_t(ImplantSocket::Cardiac)].implantKills = 250;
    setImplants(party, 50);
    CHECK_EQ(maxHealthOf(member), 1776);

    // Mana Gland at Implants 10: 8 % of 500.
    setImplants(party, 10);
    wear(party, ImplantSocket::Cardiac, 11404);
    CHECK_EQ(maxHealthOf(member), 1200);
    CHECK_EQ(maxSpellPointsOf(member), 540);
}

TEST_CASE("implants: Chitin Graft and Ember Lattice add their share of the sheet's armour class and fire resistance")
{
    const ImplantsAvailableScope implants(true);
    Party party = implantParty();
    Character &member = *party.member(0);
    member.permanentBonuses.armorClass = 60;
    member.baseResistances.fire = 40;
    setImplants(party, 10);
    const CharacterSheetSummary before = GameMechanics::buildCharacterSheetSummary(member, &implantTable());
    REQUIRE_GT(before.armorClass.actual, 50);
    REQUIRE_EQ(before.fireResistance.actual, 40);

    // Chitin Graft at Implants 10: 4 % of the total armour class.
    wear(party, ImplantSocket::Dermal, 11401);
    CHECK_EQ(member.implantArmorClassPercent, doctest::Approx(4.0f));
    CharacterSheetSummary after = GameMechanics::buildCharacterSheetSummary(member, &implantTable());
    CHECK_EQ(after.armorClass.actual, before.armorClass.actual + before.armorClass.actual * 4 / 100);
    CHECK_EQ(after.fireResistance.actual, 40);

    // Ember Lattice at Implants 10: 10 % of the total fire resistance.
    wear(party, ImplantSocket::Dermal, 11400);
    CHECK_EQ(member.implantFireResistancePercent, doctest::Approx(10.0f));
    after = GameMechanics::buildCharacterSheetSummary(member, &implantTable());
    CHECK_EQ(after.fireResistance.actual, 44);
    CHECK_EQ(after.armorClass.actual, before.armorClass.actual);

    // No fire resistance: nothing to take a share of.
    member.baseResistances.fire = 0;
    party.rebuildMagicalBonusesFromBuffs();
    after = GameMechanics::buildCharacterSheetSummary(member, &implantTable());
    CHECK_EQ(after.fireResistance.actual, 0);
}

TEST_CASE("implants: Berserker's Seed drains 5 % of max HP and SP a second, only with a hostile in melee reach")
{
    const ImplantsAvailableScope implants(true);
    Party party = makeParty({makeMember("Ada", "Knight"), makeMember("Bram", "Knight")});
    party.setItemTable(&implantTable());

    // Nobody wears one: the check is never due and clears the state.
    party.setHostileInMeleeReach(true);
    CHECK_FALSE(party.implantMeleeReachCheckDue(0.5f));
    CHECK_FALSE(party.hostileInMeleeReach());

    for (size_t index = 0; index < 2; ++index)
    {
        party.member(index)->maxSpellPoints = 200;
        setImplants(party, 10, index);
    }

    wear(party, ImplantSocket::Cranial, 11409);
    Character &wearer = *party.member(0);
    Character &other = *party.member(1);
    CHECK_EQ(wearer.implantBerserkDamagePercent, doctest::Approx(15.0f));
    CHECK_EQ(other.implantBerserkDamagePercent, doctest::Approx(0.0f));
    wearer.health = 1000;
    wearer.spellPoints = 200;
    other.health = 1000;
    other.spellPoints = 200;

    // No hostile in reach: no bonus, no drain.
    CHECK_FALSE(wearer.implantBerserkActive);
    party.updateImplantTimers(1.0f);
    CHECK_EQ(wearer.health, 1000);
    CHECK_EQ(wearer.spellPoints, 200);

    // A wearer's check is due at once, then every 0.25 s.
    CHECK(party.implantMeleeReachCheckDue(0.1f));
    CHECK_FALSE(party.implantMeleeReachCheckDue(0.1f));
    CHECK_FALSE(party.implantMeleeReachCheckDue(0.1f));
    CHECK(party.implantMeleeReachCheckDue(0.1f));
    CHECK_FALSE(party.implantMeleeReachCheckDue(0.1f));

    // A hostile in reach: only the wearer's bonus is on; it stays on through a rebuild.
    party.setHostileInMeleeReach(true);
    CHECK(party.hostileInMeleeReach());
    CHECK(wearer.implantBerserkActive);
    CHECK_FALSE(other.implantBerserkActive);
    party.rebuildMagicalBonusesFromBuffs();
    CHECK(wearer.implantBerserkActive);
    CHECK_FALSE(other.implantBerserkActive);

    // 5 % of 1000 HP and 200 SP per second.
    party.updateImplantTimers(1.0f);
    CHECK_EQ(wearer.health, 950);
    CHECK_EQ(wearer.spellPoints, 190);
    CHECK_EQ(other.health, 1000);
    CHECK_EQ(other.spellPoints, 200);

    // Never below 1 HP; SP stops at 0; the bonus stays on.
    wearer.health = 30;
    wearer.spellPoints = 5;
    party.updateImplantTimers(1.0f);
    CHECK_EQ(wearer.health, 1);
    CHECK_EQ(wearer.spellPoints, 0);
    party.updateImplantTimers(1.0f);
    CHECK_EQ(wearer.health, 1);
    CHECK_EQ(wearer.spellPoints, 0);
    CHECK(wearer.implantBerserkActive);

    // Out of reach again: the drain stops.
    party.setHostileInMeleeReach(false);
    CHECK_FALSE(wearer.implantBerserkActive);
    wearer.health = 500;
    party.updateImplantTimers(1.0f);
    CHECK_EQ(wearer.health, 500);

    // Taken off: the check is no longer due and the state clears.
    party.setHostileInMeleeReach(true);
    unwear(party, ImplantSocket::Cranial);
    CHECK_FALSE(wearer.implantBerserkActive);
    CHECK_FALSE(party.implantMeleeReachCheckDue(1.0f));
    CHECK_FALSE(party.hostileInMeleeReach());
}

TEST_CASE("implants: Siphoner pays its share of damage dealt as HP and as SP evenly over 2 seconds")
{
    const ImplantsAvailableScope implants(true);
    Party party = implantParty();
    Character &member = *party.member(0);
    member.maxSpellPoints = 1000;
    setImplants(party, 10);
    wear(party, ImplantSocket::Cardiac, 11410);
    CHECK_EQ(member.implantSiphonPercent, doctest::Approx(3.0f));
    member.health = 100;
    member.spellPoints = 0;

    // Nothing at once: 3 % of 1000 is 30 HP and 30 SP, 15 a second.
    party.addImplantSiphon(0, 1000);
    CHECK_EQ(member.health, 100);
    CHECK_EQ(member.spellPoints, 0);
    REQUIRE_EQ(member.implantSiphonGrants.size(), 1u);
    party.updateImplantTimers(1.0f);
    CHECK_EQ(member.health, 115);
    CHECK_EQ(member.spellPoints, 15);
    party.updateImplantTimers(1.0f);
    CHECK_EQ(member.health, 130);
    CHECK_EQ(member.spellPoints, 30);
    CHECK(member.implantSiphonGrants.empty());
    party.updateImplantTimers(1.0f);
    CHECK_EQ(member.health, 130);
    CHECK_EQ(member.spellPoints, 30);

    // Hits overlap: 30 over the first two seconds, 60 over the next two from one second on.
    party.addImplantSiphon(0, 1000);
    party.updateImplantTimers(1.0f);
    CHECK_EQ(member.health, 145);
    party.addImplantSiphon(0, 2000);
    CHECK_EQ(member.implantSiphonGrants.size(), 2u);
    party.updateImplantTimers(1.0f);
    CHECK_EQ(member.health, 190);
    CHECK_EQ(member.spellPoints, 90);
    CHECK_EQ(member.implantSiphonGrants.size(), 1u);
    party.updateImplantTimers(1.0f);
    CHECK_EQ(member.health, 220);
    CHECK_EQ(member.spellPoints, 120);
    party.updateImplantTimers(1.0f);
    CHECK_EQ(member.health, 220);
    CHECK_EQ(member.spellPoints, 120);

    // No damage, no payment; a member without one takes nothing.
    party.addImplantSiphon(0, 0);
    CHECK(member.implantSiphonGrants.empty());
    unwear(party, ImplantSocket::Cardiac);
    party.addImplantSiphon(0, 1000);
    CHECK(member.implantSiphonGrants.empty());
}

TEST_CASE("implants: Mirror Carapace and Kinetic Coil have no cap")
{
    const ImplantsAvailableScope implants(true);
    Party party = implantParty();
    Character &member = *party.member(0);
    setImplants(party, 10);

    wear(party, ImplantSocket::Dermal, 11411);
    CHECK_EQ(member.reflectPercent, doctest::Approx(6.0f));
    member.implants[size_t(ImplantSocket::Dermal)].implantKills = 250;
    setImplants(party, 50);
    CHECK_EQ(member.reflectPercent, doctest::Approx(36.0f));

    setImplants(party, 10);
    wear(party, ImplantSocket::Spinal, 11412);
    CHECK_EQ(member.projectileSpeedPercent, doctest::Approx(15.0f));
    CHECK_EQ(implantProjectileSpeedMultiplier(&member), doctest::Approx(1.15f));
    member.implants[size_t(ImplantSocket::Spinal)].implantKills = 250;
    setImplants(party, 50);
    CHECK_EQ(member.projectileSpeedPercent, doctest::Approx(110.0f));
    CHECK_EQ(implantProjectileSpeedMultiplier(&member), doctest::Approx(2.1f));
    setImplants(party, 60);
    CHECK_EQ(implantProjectileSpeedMultiplier(&member), doctest::Approx(2.1f));
    CHECK_EQ(implantProjectileSpeedMultiplier(nullptr), doctest::Approx(1.0f));
}

TEST_CASE("implants: an item's bonus to Implants raises the effect level up to the cap, not the sockets")
{
    const ImplantsAvailableScope implants(true);
    // A worn amulet with +3 Implants (item_effects skill_bonuses, the 23rd effect column).
    std::vector<std::string> charm = {"11498", "hesper:item_effect/implant_charm"};
    charm.resize(2 + 22);
    charm.push_back("Implants:3");
    ItemTable table;
    std::string error;
    REQUIRE_MESSAGE(loadImplantTable(table, error, std::nullopt,
                        {implantItemRow(11498, "implant_charm", "Charm", "Amulet",
                            "hesper:item_effect/implant_charm")},
                        {charm}),
        error);
    Party party = makeParty({makeMember("Ada", "Knight")});
    party.setItemTable(&table);
    Character &member = *party.member(0);
    member.intellect = 100;
    member.implants[size_t(ImplantSocket::Cranial)] =
        ItemGenerator::makeInventoryItem(11405, table, ItemGenerationMode::Generic);
    member.skills["Implants"] = {"Implants", 2, SkillMastery::Normal};
    party.rebuildMagicalBonusesFromBuffs();
    // Neural Loom at 2: 6 %.
    CHECK_EQ(member.magicalBonuses.intellect, 6);

    member.equipment.amulet = 11498;
    party.rebuildMagicalBonusesFromBuffs();
    CHECK_EQ(member.skillBonus("Implants"), 3);
    // At 2 + 3: 7.5 %.
    CHECK_EQ(standardSkillRules().implantEffectLevel(member), 5);
    CHECK_EQ(member.magicalBonuses.intellect, 7);

    // 48 + 3 counts 50: 30 %.
    member.skills["Implants"].level = 48;
    party.rebuildMagicalBonusesFromBuffs();
    CHECK_EQ(standardSkillRules().implantEffectLevel(member), 50);
    CHECK_EQ(member.magicalBonuses.intellect, 30);

    // Without the skill the bonus opens nothing.
    member.skills.erase("Implants");
    party.rebuildMagicalBonusesFromBuffs();
    CHECK_FALSE(member.implantSocketOpen(ImplantSocket::Cranial));
    CHECK_EQ(standardSkillRules().implantEffectLevel(member), 0);
    CHECK_EQ(member.magicalBonuses.intellect, 0);
}

TEST_CASE("implants: the world table's checks")
{
    const ImplantsAvailableScope implants(true);
    std::string error;

    // A world with neither implants nor rows loads as before.
    {
        ItemTable table;
        CHECK(table.loadImplantRows({}, error));
        CHECK(table.implant(11400) == nullptr);
        CHECK_FALSE(table.implantsAvailable());
    }

    // The real rows load; empty maw_ cells take Standard's values.
    {
        ItemTable table;
        REQUIRE_MESSAGE(loadImplantTable(table, error), error);
        CHECK(table.implantsAvailable());
        REQUIRE(table.implant(11410) != nullptr);
        CHECK_EQ(table.implant(11410)->components.front().maw.perLevelPercent[1], doctest::Approx(0.3f));
        CHECK(table.implant(11402) == nullptr);
    }

    // Columns are found by name: a reordered header reads the same.
    {
        std::vector<std::string> header = ImplantHeader;
        std::vector<std::vector<std::string>> rows = implantRows();
        std::swap(header[3], header[5]);

        for (std::vector<std::string> &row : rows)
        {
            std::swap(row[3], row[5]);
        }

        ItemTable table;
        REQUIRE_MESSAGE(loadImplantTable(table, error, rows, {}, {}, header), error);
        CHECK_EQ(implantEffectPercent(table.implant(11405)->components.front().standard, 2, 0),
            doctest::Approx(10.0f));
    }

    const auto fails = [&error](const std::vector<std::vector<std::string>> &rows, const std::string &message,
                           const std::vector<std::string> &header = ImplantHeader,
                           const std::vector<std::vector<std::string>> &extraItems = {})
    {
        ItemTable table;
        error.clear();
        CHECK_FALSE(loadImplantTable(table, error, rows, extraItems, {}, header));
        CHECK_MESSAGE(error.find(message) != std::string::npos, error);
    };
    std::vector<std::vector<std::string>> bad = implantRows();

    // An unknown effect; an unknown socket.
    bad.front()[2] = "glow";
    fails(bad, "unknown effect");
    bad = implantRows();
    bad.front()[1] = "elbow";
    fails(bad, "unknown socket");

    // Only all_stats, max_health and max_sp may be negative (Standard or MAW).
    bad = implantRows();
    bad.front()[3] = "-5";
    fails(bad, "may be negative");
    bad = implantRows();
    bad.front()[8] = "-0.5";
    fails(bad, "may be negative");

    // except names primary stats, on an all_stats part only.
    bad = implantRows();
    bad.front()[11] = "speed";
    fails(bad, "all_stats only");
    bad = implantRows();
    bad[6][11] = "charisma";
    fails(bad, "all_stats only");

    // An item's rows agree on socket and evolution.
    bad = implantRows();
    bad[7][1] = "dermal";
    fails(bad, "disagree");
    bad = implantRows();
    bad[7][12] = "300";
    fails(bad, "disagree");

    // A row naming an item that is not an implant.
    bad = implantRows();
    bad.push_back({"182", "cardiac", "max_health", "4", "0.4", "8", "0.8", "", "", "", "", "", "250", "60302"});
    fails(bad, "names no Implant item");

    // An Implant item without a row.
    fails(implantRows(), "has no implants row", ImplantHeader, {implantItemRow(11499, "orphan", "Orphan")});

    // A header without a needed column.
    for (const char *pColumn : {"socket", "effect", "base_i", "per_level_i", "base_ii", "per_level_ii"})
    {
        CAPTURE(pColumn);
        std::vector<std::string> header = ImplantHeader;
        std::replace(header.begin(), header.end(), std::string(pColumn), std::string("unused"));
        fails(implantRows(), std::string("no '") + pColumn + "' column", header);
    }
}

TEST_CASE("implants: six sockets round-trip a save; a character without the skill keeps empty sockets")
{
    const ImplantsAvailableScope implants(true);
    Party party = implantParty();
    PartySeed seed = {};
    seed.members = {makeMember("Ada", "Knight"), makeMember("Bram", "Sorcerer")};
    party.seed(seed);
    party.member(0)->skills["Implants"] = {"Implants", 10, SkillMastery::Normal};
    const std::array<uint32_t, ImplantSocketCount> fittedIds = {11405, 11413, 11412, 11411, 11407, 11408};

    for (size_t socket = 0; socket < ImplantSocketCount; ++socket)
    {
        party.member(0)->implants[socket] = implantItem(fittedIds[socket]);
        party.member(0)->implants[socket].implantKills = uint32_t(socket * 50 + 7);
    }

    GameSaveData saveData = {};
    saveData.mapFileName = "implants_roundtrip.odm";
    saveData.party = party.snapshot();
    const std::filesystem::path savePath = std::filesystem::temp_directory_path() / "openyamm_implants_roundtrip.oysav";
    std::string error;
    REQUIRE(saveGameDataToPath(savePath, saveData, error));
    const std::optional<GameSaveData> loaded = loadGameDataFromPath(savePath, error);
    std::filesystem::remove(savePath);
    REQUIRE_MESSAGE(loaded.has_value(), error.c_str());
    REQUIRE_EQ(loaded->party.members.size(), 2u);
    CHECK_EQ(loaded->party.members[0].implants, saveData.party.members[0].implants);
    CHECK_EQ(loaded->party.members[0].findSkill("Implants")->level, 10u);
    CHECK_EQ(loaded->party.members[1].implants, std::array<InventoryItem, ImplantSocketCount>{});
    CHECK_EQ(loaded->party.members[0].implants[3].implantKills, 157u);
}

TEST_CASE("implants: Lua teaches the skill and the fitted implants follow at once")
{
    const ImplantsAvailableScope implants(true);
    Party party = implantParty();
    party.member(0)->intellect = 100;
    wear(party, ImplantSocket::Cranial, 11405);
    CHECK_EQ(party.member(0)->magicalBonuses.intellect, 0);
    EventRuntimeState runtimeState = {};

    const std::string source = sourceFileText("assets_dev/engine/scripts/common/event_support.lua") + "\n"
        "RegisterGlobalEvent(9101, \"Archive\", function()\n"
        "    evt.SetPlayerSkill(0, \"Implants\", 4, 1)\n"
        "    if IsAtLeast(ImplantsSkill, 4) then evt.StatusText(\"learned\") end\n"
        "    if evt.MasteryRequiredLevel == nil then evt.StatusText(\"no masteries\") end\n"
        "end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@implants_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());

    EventRuntime eventRuntime = {};
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9101, runtimeState, &party));
    REQUIRE_EQ(runtimeState.statusMessages.size(), 2u);
    CHECK_EQ(runtimeState.statusMessages[0], "learned");
    CHECK_EQ(runtimeState.statusMessages[1], "no masteries");
    // Neural Loom at Implants 4: 7 % of 100 Intellect.
    CHECK_EQ(party.member(0)->magicalBonuses.intellect, 7);
    // Learning it shows the learned portrait effect.
    CHECK_FALSE(runtimeState.portraitFxRequests.empty());
}

TEST_CASE("implants: the quick member is one whose last recovery was shorter than the held-key repeat")
{
    const ImplantsAvailableScope implants(true);
    Party party = makeParty({makeMember("Ada", "Knight"), makeMember("Bram", "Archer"), makeMember("Cid", "Thief")});
    const float repeat = GameplayActionController::HeldActionRepeatDebounceSeconds;

    // Nobody has acted yet.
    CHECK_FALSE(party.quickRecoveryReadyMember(repeat).has_value());

    // The 30-tick floor is 0.5 s: not quick. 9 ticks is 0.15 s, still longer than 0.14 s; 8 ticks (0.133 s) is quick.
    party.member(0)->recoveryTotalSeconds = ticksToRecoverySeconds(30);
    party.member(1)->recoveryTotalSeconds = ticksToRecoverySeconds(9);
    party.member(2)->recoveryTotalSeconds = ticksToRecoverySeconds(8);
    CHECK_EQ(ticksToRecoverySeconds(30), doctest::Approx(0.5f));
    CHECK_GT(ticksToRecoverySeconds(9), repeat);
    CHECK_LT(ticksToRecoverySeconds(8), repeat);
    CHECK_EQ(party.quickRecoveryReadyMember(repeat), std::optional<size_t>(2));

    // The first such member.
    party.member(1)->recoveryTotalSeconds = ticksToRecoverySeconds(5);
    CHECK_EQ(party.quickRecoveryReadyMember(repeat), std::optional<size_t>(1));

    // One who cannot act is not offered.
    party.member(1)->conditions.set(size_t(CharacterCondition::Paralyzed));
    CHECK_EQ(party.quickRecoveryReadyMember(repeat), std::optional<size_t>(2));

    // Nor one still recovering: "can act now" (Party.h, quickRecoveryReadyMember).
    party.member(2)->recoverySecondsRemaining = 0.1f;
    CHECK_FALSE(party.quickRecoveryReadyMember(repeat).has_value());
}

// Hesper's Ember Skin (DECISIONS H-59): the LavaWalk party buff, its own movement indicator, Lua, co-op and saves.
TEST_CASE("lava walk: a party buff with its own movement indicator, never a skull layer or badge")
{
    const ImplantsAvailableScope implants(true);
    Party party = makeParty({makeMember("Ada", "Knight")});
    CHECK_FALSE(party.hasPartyBuff(PartyBuffId::LavaWalk));
    party.applyPartyBuff(PartyBuffId::LavaWalk, 1800.0f, 0, 0, 0, SkillMastery::None, 0);
    CHECK(party.hasPartyBuff(PartyBuffId::LavaWalk));
    // Water Walk stays water-only: Lava Walk does not switch it on.
    CHECK_FALSE(party.hasPartyBuff(PartyBuffId::WaterWalk));

    const GameplayBuffHudDefinition &definition = GameplayBuffHudDefinitions[size_t(PartyBuffId::LavaWalk)];
    CHECK(definition.presentation == GameplayBuffPresentation::Movement);
    CHECK(definition.pLayer == nullptr);
    CHECK(gameplayBuffPanelLayoutId(definition.presentation) == nullptr);
    const std::vector<GameplayMovementIndicator> indicators = gameplayMovementIndicators(party);
    REQUIRE_EQ(indicators.size(), 1u);
    CHECK_EQ(std::string(indicators.front().pLayoutId), "OutdoorLavaWalkBuffIcon");

    // It lasts its game time, and Dispel Magic ends it as any party buff.
    party.advanceTimedStates(1700.0f);
    CHECK(party.hasPartyBuff(PartyBuffId::LavaWalk));
    party.advanceTimedStates(200.0f);
    CHECK_FALSE(party.hasPartyBuff(PartyBuffId::LavaWalk));
    party.applyPartyBuff(PartyBuffId::LavaWalk, 1800.0f, 0, 0, 0, SkillMastery::None, 0);
    CHECK(party.clearDispellableBuffs());
    CHECK_FALSE(party.hasPartyBuff(PartyBuffId::LavaWalk));
}

TEST_CASE("lava walk: Lua gives it by name and a save keeps it")
{
    const ImplantsAvailableScope implants(true);
    Party party = makeParty({makeMember("Ada", "Knight")});
    EventRuntimeState runtimeState = {};
    const std::string source = sourceFileText("assets_dev/engine/scripts/common/event_support.lua") + "\n"
        "RegisterGlobalEvent(9102, \"Ember Skin\", function()\n"
        "    assert(not evt.HasPartyBuff(\"LavaWalk\"))\n"
        "    evt.ApplyPartyBuff(\"LavaWalk\", 1800)\n"
        "    if evt.HasPartyBuff(\"LavaWalk\") then evt.StatusText(\"on\") end\n"
        "end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@lava_walk_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9102, runtimeState, &party));
    REQUIRE_EQ(runtimeState.statusMessages.size(), 1u);
    CHECK_EQ(runtimeState.statusMessages.front(), "on");
    REQUIRE(party.partyBuff(PartyBuffId::LavaWalk) != nullptr);
    CHECK_EQ(party.partyBuff(PartyBuffId::LavaWalk)->remainingSeconds, doctest::Approx(1800.0f));

    GameSaveData saveData = {};
    saveData.mapFileName = "lava_walk_roundtrip.odm";
    saveData.party = party.snapshot();
    const std::filesystem::path savePath =
        std::filesystem::temp_directory_path() / "openyamm_lava_walk_roundtrip.oysav";
    REQUIRE(saveGameDataToPath(savePath, saveData, error));
    const std::optional<GameSaveData> loaded = loadGameDataFromPath(savePath, error);
    std::filesystem::remove(savePath);
    REQUIRE_MESSAGE(loaded.has_value(), error.c_str());
    CHECK_EQ(loaded->party.partyBuffs[size_t(PartyBuffId::LavaWalk)].remainingSeconds, doctest::Approx(1800.0f));
}

// Hesper is not mounted (v3.4): no world provides the implants table, so nothing shows, lists, teaches or applies them.
TEST_CASE("implants gate: without a world that provides implants they are hidden, unlisted and unteachable")
{
    const ImplantsAvailableScope implants(false);
    CHECK_FALSE(skillAvailable("Implants"));
    CHECK(skillAvailable("Sword"));
    const std::vector<std::string> &misc = skillSheetGroupSkillNames(SkillSheetGroup::Misc);
    CHECK(std::find(misc.begin(), misc.end(), "Implants") == misc.end());
    CHECK_EQ(gameData().classSkillTable.getClassCap("Knight", "Implants"), SkillMastery::None);
    CHECK_EQ(gameData().classSkillTable.getEffectiveCap("Sorcerer", 0, "Implants"), SkillMastery::None);

    // A save that somehow holds the skill and a fitted implant keeps both, unseen and without effect.
    Party party = implantParty();
    Character &member = *party.member(0);
    member.intellect = 100;
    member.skills["Implants"] = {"Implants", 10, SkillMastery::Normal};
    member.implants[size_t(ImplantSocket::Cranial)].objectDescriptionId = 11405;
    party.rebuildMagicalBonusesFromBuffs();
    CHECK_FALSE(member.showsImplantSockets());
    CHECK_FALSE(member.implantSocketOpen(ImplantSocket::Cranial));
    CHECK_EQ(member.magicalBonuses.intellect, 0);
    CHECK_EQ(member.implants[size_t(ImplantSocket::Cranial)].objectDescriptionId, 11405u);
    std::optional<InventoryItem> replaced;
    CHECK_NE(party.fitImplant(0, ImplantSocket::Cardiac, implantItem(11403), replaced),
        Party::ImplantFitResult::Fitted);

    // The script hooks refuse: no teaching, no skill read back, no EVT variable.
    Party plain = implantParty();
    EventRuntimeState runtimeState = {};
    const std::string source = sourceFileText("assets_dev/engine/scripts/common/event_support.lua") + "\n"
        "RegisterGlobalEvent(9103, \"Archive\", function()\n"
        "    assert(not evt.SetPlayerSkill(0, \"Implants\", 4, 1), \"teaching is refused\")\n"
        "    assert(evt.MasteryRequiredLevel == nil, \"no mastery levels\")\n"
        "    assert(evt.GetPlayerSkill(0, \"Implants\") == 0, \"no skill\")\n"
        "    assert(not evt.CanPlayerLearnSkill(0, \"Implants\", 1), \"no class can learn it\")\n"
        "    evt.StatusText(\"refused\")\n"
        "end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@implants_gate.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    EventRuntime eventRuntime = {};
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9103, runtimeState, &plain));
    REQUIRE_EQ(runtimeState.statusMessages.size(), 1u);
    CHECK_EQ(runtimeState.statusMessages.front(), "refused");
    CHECK(plain.member(0)->findSkill("Implants") == nullptr);
    const uint32_t implantsVariable = static_cast<uint32_t>(EvtVariable::ImplantsSkill);
    EventRuntime::setVariableValue(runtimeState, EventRuntime::decodeVariable(implantsVariable), 4, &plain, {0});
    CHECK(plain.member(0)->findSkill("Implants") == nullptr);
}

// Implants never come from random loot, even with Hesper mounted and with no NoRandom flag: only scripts give them.
TEST_CASE("implants: never rolled as random loot, even listed in a world's loot table")
{
    const ImplantsAvailableScope implants(true);
    std::vector<std::string> unflagged = implantItemRow(11496, "unflagged", "Unflagged Gland");
    unflagged[20] = "";
    std::vector<std::vector<std::string>> rows = implantRows();
    rows.push_back({"11496", "cardiac", "max_health", "4", "0.4", "8", "0.8", "", "", "", "", "", "250", "60302"});

    ItemTable table;
    std::string error;
    REQUIRE_MESSAGE(loadImplantTable(table, error, rows, {unflagged}), error);
    REQUIRE_MESSAGE(table.loadWorldLootYaml("schema: openyamm.worldLoot.v1\n"
                                            "treasure_levels: [H1, H1, H1, H1, H1, H1]\n"
                                            "classes:\n  H1: {11496: 50, 11404: 50, 182: 1}\n",
                        "hesper", error),
        error);
    std::mt19937 rng(11);

    for (int trial = 0; trial < 200; ++trial)
    {
        ItemGenerationRequest request = {};
        request.worldId = "hesper";
        request.treasureLevel = 3;
        request.mode = ItemGenerationMode::ChestLoot;
        request.allowRareItems = false;
        const std::optional<InventoryItem> item = ItemGenerator::generateRandomInventoryItem(table,
            gameData().standardItemEnchantTable, gameData().specialItemEnchantTable, request, nullptr, rng);
        REQUIRE(item.has_value());
        CHECK_EQ(item->objectDescriptionId, 182u);
    }
}

TEST_CASE("implants: party sound requests name their table, the engine's by default, a world's for world sounds")
{
    Party party = makeParty({makeMember("Ada", "Knight")});
    party.clearPendingAudioRequests();
    party.requestSound(SoundId::Chimes);
    party.requestWorldSound(60302);
    party.requestWorldSound(0);
    const std::vector<Party::PendingAudioRequest> &requests = party.pendingAudioRequests();
    REQUIRE_EQ(requests.size(), 2u);
    CHECK(requests[0].soundId == SoundId::Chimes);
    CHECK(requests[0].scope == SoundScope::Engine);
    CHECK_EQ(uint32_t(requests[1].soundId), 60302u);
    CHECK(requests[1].scope == SoundScope::World);
}
