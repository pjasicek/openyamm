#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/TextTable.h"
#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/HouseServiceRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/PriceCalculator.h"
#include "game/gameplay/MasteryTeacherDialog.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/maps/SaveGame.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"
#include "game/tables/HouseTable.h"
#include "game/StringUtils.h"
#include "tests/RegressionGameData.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <sstream>

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
    member.maxHealth = 50;
    member.health = 50;
    return member;
}

Party makeParty(const std::vector<Character> &members, int gold)
{
    Party party = {};
    party.setClassSkillTable(&gameData().classSkillTable);
    PartySeed seed = {};
    seed.gold = gold;
    seed.food = 7;
    seed.members = members;
    party.seed(seed);
    return party;
}

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

// The engine's items plus three of Hesper's draft rows (design/kreegan_world/data/items.txt): the Pulse Pistol, the
// Plasma Saber and the Engram Shard.
const ItemTable &itemTableWithHesperItems()
{
    static const ItemTable table = []()
    {
        OpenYAMM::Engine::AssetFileSystem assetFileSystem;
        const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
        REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1));
        std::vector<std::vector<std::string>> itemRows =
            rowsFromText(*assetFileSystem.readTextFile("engine/data_tables/items.txt"));
        const std::vector<std::vector<std::string>> randomItemRows =
            rowsFromText(*assetFileSystem.readTextFile("engine/data_tables/random_items.txt"));
        const std::vector<std::vector<std::string>> hesperRows = rowsFromText(
            "11000\thes_pulse_pistol\tPulse Pistol\t10000\tWeapon\tBlaster\t4d6\t10\t4\t15\tKreegan Sidearm\t0\t0"
            "\t0\t0\t0\tA pistol.\thesper\thesper:item/pulse_pistol\t\tKreeganEnergy|EnergyWeapon|EnergyGun|Fast\n"
            "11008\thes_disruptor_cannon\tDisruptor Cannon\t90000\tWeapon2\tBlaster\t12d10\t40\t4\t15"
            "\tKreegan Cannon\t0"
            "\t0\t0\t0\t0\tA cannon.\thesper\thesper:item/disruptor_cannon\t\tKreeganEnergy|EnergyWeapon|EnergyGun"
            "|Recovery160\n"
            "11022\thes_plasma_saber\tPlasma Saber\t22000\tWeapon\tSword\t4d10\t12\t5\t25\tKreegan Sword\t0\t0"
            "\t0\t0\t0\tA saber.\thesper\thesper:item/plasma_saber\t\tKreeganEnergy|EnergyWeapon|EnergyBlade\n"
            "11100\thes_weave_suit\tWeave Suit\t8000\tArmor\tLeather\t10\t0\t4\t15\tKreegan Suit\t0\t0"
            "\t0\t0\t0\tA suit.\thesper\thesper:item/weave_suit\t\t\n"
            "11330\thes_engram_shard\tEngram Shard\t0\tN / A\tMisc\t0\t0\t4\t0\tEngram\t0\t2\t0\t0\t0\tTech points."
            "\thesper\thesper:item/engram_shard\t\t\t4\tgrantTechPoints\tcharacter\n"
            "11302\thes_stim\tStim\t300\tN / A\tMisc\t0\t0\t4\t0\tStim\t0\t0\t0\t0\t0\tA stim."
            "\thesper\thesper:item/stim\t\t\t4\tuseStim\tcharacter\n"
            "11304\thes_breach_charge\tBreach Charge\t1500\tN / A\tMisc\t0\t0\t4\t0\tCharge\t0\t0\t0\t0\t0"
            "\tA charge.\thesper\thesper:item/breach_charge\t\t\t4\tplaceBreachCharge\tground\n"
            "11305\thes_ration\tHesper Ration\t50\tN / A\tMisc\t0\t0\t4\t0\tRation\t0\t2\t0\t0\t0\tFood."
            "\thesper\thesper:item/ration\t\t\t4\teatFood\tparty\n");
        itemRows.insert(itemRows.end(), hesperRows.begin(), hesperRows.end());
        // Three implants and their effects, as the design's tables have them.
        const std::vector<std::vector<std::string>> implantRows = rowsFromText(
            "11200\thes_dermal_1\tDermal Mesh I\t10000\tImplant\tMisc\t0\t0\t4\t15\tImplant\t0\t0\t0\t0\t0"
            "\tImplant.\thesper\thesper:item/dermal_1\t\t\t4\t\tfamily:dermal\t\thesper:item_effect/dermal_1"
            "\t\t0\t0\t1\t1\tneeds_art\n"
            "11201\thes_dermal_2\tDermal Mesh II\t50000\tImplant\tMisc\t0\t0\t6\t35\tImplant\t0\t0\t0\t0\t0"
            "\tImplant.\thesper\thesper:item/dermal_2\t\t\t6\t\tfamily:dermal\t\thesper:item_effect/dermal_2"
            "\t\t0\t0\t1\t1\tneeds_art\n"
            "11213\thes_damping_2\tDamping Weave II\t50000\tImplant\tMisc\t0\t0\t6\t35\tImplant\t0\t0\t0\t0\t0"
            "\tImplant.\thesper\thesper:item/damping_2\t\t\t6\t\tfamily:damping\t\thesper:item_effect/damping_2"
            "\t\t0\t0\t1\t1\tneeds_art\n"
        );
        itemRows.insert(itemRows.end(), implantRows.begin(), implantRows.end());
        ItemTable loaded = {};
        REQUIRE(loaded.load(assetFileSystem, itemRows, randomItemRows));
        std::string error;
        // Effect columns after the profile: armor_class is the tenth, energy_damage_taken_pct the 36th.
        REQUIRE_MESSAGE(loaded.loadContentEffectRows(rowsFromText(
            "11200\thesper:item_effect/dermal_1\t" "\t\t\t\t\t\t\t\t\t20\t\t\t\t\t\t\t\t\t\t"
            "\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\n"
            "11201\thesper:item_effect/dermal_2\t" "\t\t\t\t\t\t\t\t\t40\t\t\t\t\t\t\t\t\t\t"
            "\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\n"
            "11213\thesper:item_effect/damping_2\t" "\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t"
            "\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t-20\t\t\t\t\n"
            ), error), error);
        return loaded;
    }();
    return table;
}

std::pair<int, int> damageRange(const std::string &text)
{
    std::istringstream stream(text);
    int minimum = 0;
    int maximum = 0;
    char dash = 0;
    stream >> minimum >> dash >> maximum;
    return {minimum, maximum};
}

MergedTeacherTopicTable teacherTopicsWithHesperRows()
{
    MergedTeacherTopicTable table = {};
    REQUIRE(table.loadFromRows({
        {"TopicId", "Notes", "SkillId", "Mastery", "TextId", "Req. Gold", "Req. Skill"},
        {"303", "Expert Sword", "1", "1", "303", "", ""},
        {"9201", "Expert Energy Guns", "EnergyGuns", "1", "9201", "15000", ""},
        {"9208", "Master Hacking", "Hacking", "2", "9208", "", ""},
    }));
    return table;
}
}

TEST_CASE("technology skills are appended after the classic skill ids")
{
    const std::vector<std::string> classicSkills = {
        "Staff", "Sword", "Dagger", "Axe", "Spear", "Bow", "Mace", "Blaster", "Shield", "LeatherArmor", "ChainArmor",
        "PlateArmor", "FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "SpiritMagic", "MindMagic", "BodyMagic",
        "LightMagic", "DarkMagic", "DarkElfAbility", "VampireAbility", "DragonAbility", "IdentifyItem", "Merchant",
        "RepairItem", "Bodybuilding", "Meditation", "Perception", "Regeneration", "DisarmTraps", "Dodging", "Unarmed",
        "IdentifyMonster", "Armsmaster", "Stealing", "Alchemy", "Learning", "Throwing"};
    const std::vector<std::string> allSkills = allCanonicalSkillNames();

    REQUIRE_EQ(allSkills.size(), 49u);
    CHECK(std::equal(classicSkills.begin(), classicSkills.end(), allSkills.begin()));
    CHECK_EQ(FirstTechnologySkillId, 40u);
    CHECK_EQ(skillNameForSkillId(40).value_or(""), "EnergyGuns");
    CHECK_EQ(skillNameForSkillId(41).value_or(""), "EnergyBlades");
    CHECK_EQ(skillNameForSkillId(42).value_or(""), "ShieldTech");
    CHECK_EQ(skillNameForSkillId(43).value_or(""), "Hacking");
    CHECK_EQ(skillNameForSkillId(44).value_or(""), "Cover");
    CHECK_EQ(skillNameForSkillId(47).value_or(""), "Retaliation");
    // Cybernetics, the fifth technology skill, came after MAW's skills.
    CHECK_EQ(skillNameForSkillId(CyberneticsSkillId).value_or(""), "Cybernetics");
    CHECK_FALSE(skillNameForSkillId(49).has_value());
    CHECK(isTechnologySkill("Cybernetics"));
    CHECK_FALSE(isRulesetSkill("Cybernetics"));
    CHECK_FALSE(isTechnologySkill("Cover"));
    CHECK_EQ(displaySkillName("ManaShield"), "Mana Shield");
    CHECK_EQ(skillIdForSkillName("Energy Guns").value_or(0), 40u);
    CHECK_EQ(skillIdForSkillName("Learning").value_or(0), 38u);
    CHECK_EQ(canonicalSkillName("Shield Tech"), "ShieldTech");
    CHECK_EQ(displaySkillName("EnergyBlades"), "Energy Blades");
    CHECK_EQ(displaySkillName("Hacking"), "Hacking");
    CHECK(isTechnologySkill("Hacking"));
    CHECK_FALSE(isTechnologySkill("Blaster"));
    CHECK_FALSE(isTechnologySkill("Throwing"));
}

TEST_CASE("technology skills have no class caps and never start on a character")
{
    const ClassSkillTable &table = gameData().classSkillTable;

    for (const char *pClassName : {"Knight", "Sorcerer", "Lich", "Peasant", "Dragon", "Monk"})
    {
        for (const std::string &skillName : skillSheetGroupSkillNames(SkillSheetGroup::Technology))
        {
            CHECK_EQ(table.getEffectiveCap(pClassName, 0, skillName), SkillMastery::Grandmaster);
            CHECK_EQ(
                table.getEffectiveStartingSkillAvailability(pClassName, 0, skillName),
                StartingSkillAvailability::None);
        }

        for (const CharacterSkill &skill : table.getDefaultSkillsForCharacter(pClassName, 0))
        {
            CHECK_FALSE(isTechnologySkill(skill.name));
        }
    }

    // Classic caps still come from class_skills.txt.
    CHECK_EQ(table.getClassCap("Sorcerer", "Sword"), SkillMastery::None);
    CHECK_EQ(table.getClassCap("Knight", "FireMagic"), SkillMastery::None);
}

TEST_CASE("the sheet's skill groups are unchanged and Technology shows only with a technology skill")
{
    CHECK_EQ(skillSheetGroupSkillNames(SkillSheetGroup::Weapons),
        std::vector<std::string>{"Axe", "Bow", "Throwing", "Dagger", "Mace", "Spear", "Staff", "Sword", "Unarmed",
            "Blaster"});
    CHECK_EQ(skillSheetGroupSkillNames(SkillSheetGroup::Armor),
        std::vector<std::string>{"LeatherArmor", "ChainArmor", "PlateArmor", "Shield", "Dodging", "Cover", "Retaliation",
            "ManaShield"});
    CHECK_EQ(skillSheetGroupSkillNames(SkillSheetGroup::Misc).size(), 12u);
    CHECK_EQ(skillSheetGroupSkillNames(SkillSheetGroup::Magic).size(), 12u);
    CHECK_EQ(skillSheetGroupSkillNames(SkillSheetGroup::Technology),
        std::vector<std::string>{"EnergyGuns", "EnergyBlades", "ShieldTech", "Hacking", "Cybernetics"});

    Character character = makeMember("Ada", "Knight");
    character.skills["Sword"] = {"Sword", 10, SkillMastery::Grandmaster};
    character.skills["Blaster"] = {"Blaster", 10, SkillMastery::Grandmaster};
    CHECK_FALSE(character.hasTechnologySkill());
    character.skills["Hacking"] = {"Hacking", 1, SkillMastery::Normal};
    CHECK(character.hasTechnologySkill());
}

TEST_CASE("teacher topics name technology skills by name and keep classic skill ids")
{
    const MergedTeacherTopicTable table = teacherTopicsWithHesperRows();

    const std::optional<MasteryTeacherTopicDefinition> sword = resolveMasteryTeacherTopic(303, &table);
    REQUIRE(sword.has_value());
    CHECK_EQ(sword->skillName, "Sword");
    CHECK_EQ(sword->targetMastery, SkillMastery::Expert);

    const std::optional<MasteryTeacherTopicDefinition> guns = resolveMasteryTeacherTopic(9201, &table);
    REQUIRE(guns.has_value());
    CHECK_EQ(guns->skillId, 40u);
    CHECK_EQ(guns->skillName, "EnergyGuns");
    CHECK_EQ(guns->targetMastery, SkillMastery::Expert);
    CHECK_EQ(guns->requiredGold, 15000u);

    const std::optional<MasteryTeacherTopicDefinition> hacking = resolveMasteryTeacherTopic(9208, &table);
    REQUIRE(hacking.has_value());
    CHECK_EQ(hacking->skillName, "Hacking");
    CHECK_EQ(hacking->targetMastery, SkillMastery::Master);

    // The engine's own teacher table is unchanged.
    const std::optional<MasteryTeacherTopicDefinition> engineSword =
        resolveMasteryTeacherTopic(303, &gameData().mergedTeacherTopicTable);
    REQUIRE(engineSword.has_value());
    CHECK_EQ(engineSword->skillName, "Sword");
}

TEST_CASE("a technology teacher promotes any class at the rank, for the topic's gold or the Hesper price")
{
    const MergedTeacherTopicTable table = teacherTopicsWithHesperRows();
    Character sorcerer = makeMember("Bram", "Sorcerer");
    sorcerer.skills["EnergyGuns"] = {"EnergyGuns", 3, SkillMastery::Normal};
    sorcerer.skills["Hacking"] = {"Hacking", 7, SkillMastery::Expert};
    Party party = makeParty({sorcerer}, 60000);

    std::optional<MasteryTeacherEvaluation> evaluation =
        evaluateMasteryTeacherTopic(9201, party, gameData().classSkillTable, gameData().npcDialogTable, &table);
    REQUIRE(evaluation.has_value());
    CHECK_FALSE(evaluation->approved);

    party.member(0)->skills["EnergyGuns"].level = 4;
    evaluation =
        evaluateMasteryTeacherTopic(9201, party, gameData().classSkillTable, gameData().npcDialogTable, &table);
    REQUIRE(evaluation.has_value());
    CHECK(evaluation->approved);
    CHECK_EQ(evaluation->cost, 15000);
    CHECK_EQ(evaluation->displayText, "Become Expert in Energy Guns for 15000 gold");

    // No Req. Gold: the Hesper Master price.
    evaluation =
        evaluateMasteryTeacherTopic(9208, party, gameData().classSkillTable, gameData().npcDialogTable, &table);
    REQUIRE(evaluation.has_value());
    CHECK(evaluation->approved);
    CHECK_EQ(evaluation->cost, 40000);
}

TEST_CASE("a house that lists offered skills sells their Novice; plain MM houses are unchanged")
{
    const ClassSkillTable &classSkillTable = gameData().classSkillTable;
    Party party = makeParty({makeMember("Ada", "Knight")}, 5000);

    HouseEntry salvage = {};
    salvage.id = 9201;
    salvage.type = "House";
    salvage.name = "Salvage & Arms";
    salvage.priceMultiplier = 1.0f;
    salvage.skillPriceMultiplier = 2.0f;
    salvage.offeredSkills = {"EnergyGuns", "EnergyBlades"};

    std::vector<HouseActionOption> options =
        buildHouseActionOptions(salvage, &party, &classSkillTable, nullptr, 0.0f, DialogueMenuId::None);
    REQUIRE_EQ(options.size(), 1u);
    CHECK_EQ(options.front().id, HouseActionId::OpenLearnSkillsMenu);

    options = buildHouseActionOptions(salvage, &party, &classSkillTable, nullptr, 0.0f, DialogueMenuId::LearnSkills);
    REQUIRE_EQ(options.size(), 2u);
    CHECK_EQ(options[0].label, "Learn Energy Blades for 1000 gold");
    CHECK_EQ(options[1].label, "Learn Energy Guns for 1000 gold");

    const HouseActionResult result =
        performHouseAction(options[1], salvage, party, &classSkillTable, nullptr, &gameData().npcDialogTable);
    CHECK(result.succeeded);
    CHECK_EQ(party.gold(), 4000);
    const CharacterSkill *pSkill = party.member(0)->findSkill("EnergyGuns");
    REQUIRE(pSkill != nullptr);
    CHECK_EQ(pSkill->level, 1u);
    CHECK_EQ(pSkill->mastery, SkillMastery::Normal);

    HouseEntry plainHouse = salvage;
    plainHouse.offeredSkills.clear();
    CHECK(buildHouseActionOptions(plainHouse, &party, &classSkillTable, nullptr, 0.0f, DialogueMenuId::None).empty());
}

TEST_CASE("a house whose skill cell says none teaches nothing; an empty cell keeps its type's skills")
{
    const auto row = [](const std::string &id, const std::string &skills)
    {
        return std::vector<std::string>{id, "0", "Tavern", "0", "27", "Inn " + id, "", "", "0", "0", "0", "0", "1",
            "1", "", "0", "", "", "0", "0", "0", "0", "0", "", skills};
    };
    HouseTable table = {};
    REQUIRE(table.loadFromRows({row("9451", "none"), row("9452", ""), row("9453", "Perception")}));
    REQUIRE(table.get(9451) != nullptr);
    CHECK(table.get(9451)->offeredSkills.empty());
    CHECK(table.get(9451)->teachesNothing);
    CHECK_FALSE(table.get(9452)->offeredSkills.empty());
    REQUIRE_EQ(table.get(9453)->offeredSkills.size(), 1u);
    CHECK_EQ(table.get(9453)->offeredSkills.front(), "Perception");
}

TEST_CASE("tech points raise technology skills, skill points raise classic skills")
{
    Character member = makeMember("Ada", "Knight");
    member.skills["Sword"] = {"Sword", 1, SkillMastery::Normal};
    member.skills["EnergyGuns"] = {"EnergyGuns", 1, SkillMastery::Normal};
    member.skillPoints = 10;
    member.techPoints = 0;
    Party party = makeParty({member}, 0);

    CHECK(party.canIncreaseActiveMemberSkillLevel("Sword"));
    CHECK_FALSE(party.canIncreaseActiveMemberSkillLevel("EnergyGuns"));

    party.member(0)->techPoints = 2;
    REQUIRE(party.increaseActiveMemberSkillLevel("EnergyGuns"));
    CHECK_EQ(party.member(0)->findSkill("EnergyGuns")->level, 2u);
    CHECK_EQ(party.member(0)->techPoints, 0u);
    CHECK_EQ(party.member(0)->skillPoints, 10u);

    REQUIRE(party.increaseActiveMemberSkillLevel("Sword"));
    CHECK_EQ(party.member(0)->skillPoints, 8u);
    CHECK_EQ(party.member(0)->techPoints, 0u);
}

TEST_CASE("an Engram gives its VarA in tech points")
{
    const ItemTable &itemTable = itemTableWithHesperItems();
    Party party = makeParty({makeMember("Ada", "Knight")}, 0);
    InventoryItem engram = {};
    engram.objectDescriptionId = 11330;
    engram.identified = true;

    CHECK_EQ(InventoryItemUseRuntime::classifyItemUse(engram, itemTable), InventoryItemUseAction::GrantTechPoints);
    const InventoryItemUseResult result =
        InventoryItemUseRuntime::useItemOnMember(party, 0, engram, itemTable, nullptr);
    CHECK(result.handled);
    CHECK(result.consumed);
    CHECK_EQ(result.statusText, "+2 Tech Points!");
    CHECK_EQ(party.member(0)->techPoints, 2u);
    CHECK_EQ(party.member(0)->skillPoints, 0u);
}

TEST_CASE("save round trips keep technology skills and tech points, and leave other characters unchanged")
{
    Character hesperMember = makeMember("Ada", "Knight");
    hesperMember.skills["Sword"] = {"Sword", 10, SkillMastery::Grandmaster};
    hesperMember.skills["EnergyBlades"] = {"EnergyBlades", 4, SkillMastery::Expert};
    hesperMember.skills["Hacking"] = {"Hacking", 2, SkillMastery::Normal};
    hesperMember.skillPoints = 3;
    hesperMember.techPoints = 7;
    Character homeMember = makeMember("Bram", "Sorcerer");
    homeMember.skills["FireMagic"] = {"FireMagic", 5, SkillMastery::Expert};
    homeMember.skillPoints = 12;
    Party party = makeParty({hesperMember, homeMember}, 100);

    GameSaveData saveData = {};
    saveData.mapFileName = "tech_skills_roundtrip.odm";
    saveData.party = party.snapshot();
    const std::filesystem::path savePath =
        std::filesystem::temp_directory_path() / "openyamm_technology_skill_roundtrip.oysav";
    std::string error;
    REQUIRE(saveGameDataToPath(savePath, saveData, error));
    const std::optional<GameSaveData> loaded = loadGameDataFromPath(savePath, error);
    std::filesystem::remove(savePath);
    REQUIRE_MESSAGE(loaded.has_value(), error.c_str());
    REQUIRE_EQ(loaded->party.members.size(), 2u);

    for (size_t memberIndex = 0; memberIndex < 2; ++memberIndex)
    {
        const Character &before = saveData.party.members[memberIndex];
        const Character &after = loaded->party.members[memberIndex];
        CHECK_EQ(after.skillPoints, before.skillPoints);
        CHECK_EQ(after.techPoints, before.techPoints);
        REQUIRE_EQ(after.skills.size(), before.skills.size());

        for (const auto &[name, skill] : before.skills)
        {
            const CharacterSkill *pSkill = after.findSkill(name);
            REQUIRE(pSkill != nullptr);
            CHECK_EQ(pSkill->level, skill.level);
            CHECK_EQ(pSkill->mastery, skill.mastery);
        }
    }

    CHECK_EQ(loaded->party.members[0].techPoints, 7u);
    CHECK_EQ(loaded->party.members[1].techPoints, 0u);
    CHECK_FALSE(loaded->party.members[1].hasTechnologySkill());
}

TEST_CASE("technology skill event variables and Hacking checks in Lua events")
{
    Character member = makeMember("Ada", "Knight");
    Party party = makeParty({member, makeMember("Bram", "Sorcerer")}, 0);
    EventRuntimeState runtimeState = {};
    const uint32_t hackingVariable = static_cast<uint32_t>(EvtVariable::HackingSkill);

    CHECK_EQ(EventRuntime::getVariableValue(runtimeState, EventRuntime::decodeVariable(hackingVariable), &party, 0), 0);
    EventRuntime::setVariableValue(runtimeState, EventRuntime::decodeVariable(hackingVariable), 1, &party, {1});
    const CharacterSkill *pHacking = party.member(1)->findSkill("Hacking");
    REQUIRE(pHacking != nullptr);
    CHECK_EQ(pHacking->level, 1u);
    CHECK_EQ(pHacking->mastery, SkillMastery::Normal);
    CHECK(Party::isPartyWideUtilitySkill("Hacking"));

    const std::string source = sourceFileText("assets_dev/engine/scripts/common/event_support.lua") + "\n"
        "RegisterGlobalEvent(9001, \"Terminal\", function()\n"
        "    if evt.CheckSkill(const.Skills.Hacking, const.SkillCheck.Expert, 4) then\n"
        "        evt.StatusText(\"open\")\n"
        "    elseif IsAtLeast(HackingSkill, 1) then\n"
        "        evt.StatusText(\"novice\")\n"
        "    else\n"
        "        evt.StatusText(\"locked\")\n"
        "    end\n"
        "end)\n";
    std::string error;
    const std::optional<ScriptedEventProgram> program =
        ScriptedEventProgram::loadFromLuaText(source, "@tech_skill_test.lua", ScriptedEventScope::Global, error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());

    EventRuntime eventRuntime = {};
    runtimeState.statusMessages.clear();
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9001, runtimeState, &party));
    REQUIRE_EQ(runtimeState.statusMessages.size(), 1u);
    CHECK_EQ(runtimeState.statusMessages.front(), "novice");

    party.member(1)->skills["Hacking"] = {"Hacking", 4, SkillMastery::Expert};
    runtimeState.statusMessages.clear();
    REQUIRE(eventRuntime.executeEventById(std::nullopt, program, 9001, runtimeState, &party));
    REQUIRE_EQ(runtimeState.statusMessages.size(), 1u);
    CHECK_EQ(runtimeState.statusMessages.front(), "open");
}

TEST_CASE("energy guns use Blaster and add Energy Guns' share of their damage; energy blades add Energy Blades'")
{
    const ItemTable &itemTable = itemTableWithHesperItems();

    // The Pulse Pistol (4d6+10: 14-34) on Blaster: hit chance and mastery from Blaster, Energy Guns adds its share.
    Character gunner = makeMember("Ada", "Knight");
    gunner.skills["Blaster"] = {"Blaster", 3, SkillMastery::Normal};
    gunner.equipment.mainHand = 11000;
    const CharacterAttackProfile plain = GameMechanics::buildCharacterAttackProfile(gunner, &itemTable, nullptr);
    CHECK(plain.hasBlaster);
    CHECK_EQ(plain.rangedSkillLevel, 3u);
    CHECK_EQ(plain.rangedShieldTier, ShieldAttackTier::KreeganEnergy);
    // Grandmaster rank 10: +10 % a rank, +100 %.
    gunner.skills["EnergyGuns"] = {"EnergyGuns", 10, SkillMastery::Grandmaster};
    const CharacterAttackProfile gun = GameMechanics::buildCharacterAttackProfile(gunner, &itemTable, nullptr);
    CHECK_EQ(gun.rangedSkillLevel, 3u);
    CHECK_EQ(gun.rangedMinDamage, plain.rangedMinDamage + 14);
    CHECK_EQ(gun.rangedMaxDamage, plain.rangedMaxDamage + 34);
    // Expert rank 5: +4 % a rank, +20 %.
    gunner.skills["EnergyGuns"] = {"EnergyGuns", 5, SkillMastery::Expert};
    const CharacterAttackProfile expert = GameMechanics::buildCharacterAttackProfile(gunner, &itemTable, nullptr);
    CHECK_EQ(expert.rangedMinDamage, plain.rangedMinDamage + 14 * 20 / 100);
    CHECK_EQ(expert.rangedMaxDamage, plain.rangedMaxDamage + 34 * 20 / 100);

    // Gun recovery: the pistol at the blaster's 30, the Disruptor Cannon's own 160; neither below 15.
    gunner.skills.erase("EnergyGuns");
    gunner.speed = 400;
    const float fastPistol =
        GameMechanics::buildCharacterAttackProfile(gunner, &itemTable, nullptr).rangedRecoverySeconds;
    gunner.equipment.mainHand = 11008;
    const float cannon = GameMechanics::buildCharacterAttackProfile(gunner, &itemTable, nullptr).rangedRecoverySeconds;
    CHECK(cannon > fastPistol * 4.0f);
    CHECK(fastPistol == doctest::Approx(ticksToRecoverySeconds(15)));

    // The Plasma Saber (4d10+12: 16-52) on Sword, Energy Blades Novice rank 5: +2 % a rank, +10 %.
    Character swordsman = makeMember("Bram", "Knight");
    swordsman.skills["Sword"] = {"Sword", 4, SkillMastery::Normal};
    swordsman.equipment.mainHand = 11022;
    const CharacterSheetSummary classic = GameMechanics::buildCharacterSheetSummary(swordsman, &itemTable);
    swordsman.skills["EnergyBlades"] = {"EnergyBlades", 5, SkillMastery::Normal};
    const CharacterSheetSummary energy = GameMechanics::buildCharacterSheetSummary(swordsman, &itemTable);
    CHECK_EQ(classic.combat.attack, energy.combat.attack);
    CHECK_EQ(damageRange(energy.combat.meleeDamageText).first, damageRange(classic.combat.meleeDamageText).first + 1);
    CHECK_EQ(damageRange(energy.combat.meleeDamageText).second, damageRange(classic.combat.meleeDamageText).second + 5);

    // A classic sword with the same skills gets nothing from Energy Blades.
    swordsman.equipment.mainHand = 2;
    const CharacterSheetSummary classicSword = GameMechanics::buildCharacterSheetSummary(swordsman, &itemTable);
    swordsman.skills.erase("EnergyBlades");
    CHECK_EQ(GameMechanics::buildCharacterSheetSummary(swordsman, &itemTable).combat.meleeDamageText,
        classicSword.combat.meleeDamageText);
}

TEST_CASE("energy weapon masteries: shields from Expert, exposed bodies and cleave from Master, homing at Grandmaster")
{
    const ItemTable &itemTable = itemTableWithHesperItems();
    Character gunner = makeMember("Ada", "Knight");
    gunner.skills["Blaster"] = {"Blaster", 4, SkillMastery::Expert};
    gunner.equipment.mainHand = 11000;
    gunner.skills["EnergyGuns"] = {"EnergyGuns", 3, SkillMastery::Normal};
    CharacterAttackProfile gun = GameMechanics::buildCharacterAttackProfile(gunner, &itemTable, nullptr);
    CHECK(gun.rangedShieldModifiers.shieldDamageMultiplier == doctest::Approx(1.0f));
    CHECK(gun.rangedShieldModifiers.exposedMultiplier == doctest::Approx(1.0f));
    CHECK_FALSE(gun.rangedHoming);
    gunner.skills["EnergyGuns"] = {"EnergyGuns", 4, SkillMastery::Expert};
    gun = GameMechanics::buildCharacterAttackProfile(gunner, &itemTable, nullptr);
    CHECK(gun.rangedShieldModifiers.shieldDamageMultiplier == doctest::Approx(1.25f));
    gunner.skills["EnergyGuns"] = {"EnergyGuns", 7, SkillMastery::Master};
    gun = GameMechanics::buildCharacterAttackProfile(gunner, &itemTable, nullptr);
    CHECK(gun.rangedShieldModifiers.exposedMultiplier == doctest::Approx(1.2f));
    CHECK_FALSE(gun.rangedHoming);
    gunner.skills["EnergyGuns"] = {"EnergyGuns", 10, SkillMastery::Grandmaster};
    CHECK(GameMechanics::buildCharacterAttackProfile(gunner, &itemTable, nullptr).rangedHoming);

    Character swordsman = makeMember("Bram", "Knight");
    swordsman.skills["Sword"] = {"Sword", 4, SkillMastery::Normal};
    swordsman.equipment.mainHand = 11022;
    swordsman.skills["EnergyBlades"] = {"EnergyBlades", 7, SkillMastery::Master};
    const CharacterAttackProfile blade = GameMechanics::buildCharacterAttackProfile(swordsman, &itemTable, nullptr);
    CHECK(blade.meleeShieldModifiers.shieldDamageMultiplier == doctest::Approx(1.25f));
    CHECK(blade.meleeShieldModifiers.cleave);
    CHECK_FALSE(blade.meleeShieldOverload);
}

TEST_CASE("implants: Cybernetics opens the sockets, the better of a family counts, bonuses grow 5 % a rank")
{
    const ItemTable &itemTable = itemTableWithHesperItems();
    Party party = makeParty({makeMember("Ada", "Knight")}, 0);
    party.setItemTable(&itemTable);
    Character &member = *party.member(0);
    const auto implant = [&itemTable](uint32_t itemId)
    {
        return ItemGenerator::makeInventoryItem(itemId, itemTable, ItemGenerationMode::Generic);
    };
    std::optional<InventoryItem> replaced;

    // No Cybernetics: no socket.
    CHECK_EQ(member.implantSocketCount(), 0u);
    CHECK_FALSE(party.fitImplant(0, 0, implant(11201), replaced));
    member.skills["Cybernetics"] = {"Cybernetics", 4, SkillMastery::Expert};
    CHECK_EQ(member.implantSocketCount(), 2u);
    CHECK_FALSE(party.fitImplant(0, 2, implant(11201), replaced));
    // Not an implant.
    CHECK_FALSE(party.fitImplant(0, 0, implant(11022), replaced));

    const int armorClassBefore = member.magicalBonuses.armorClass;
    REQUIRE(party.fitImplant(0, 0, implant(11200), replaced));
    CHECK_FALSE(replaced.has_value());
    // Dermal Mesh I: +20 armor class, +20 % at rank 4: 24.
    CHECK_EQ(member.magicalBonuses.armorClass - armorClassBefore, 24);
    // Mesh II in the second socket: only the better of the family counts (+40 x 1.2 = 48).
    REQUIRE(party.fitImplant(0, 1, implant(11201), replaced));
    CHECK_EQ(member.magicalBonuses.armorClass - armorClassBefore, 48);
    // Replacing hands the old implant back.
    REQUIRE(party.fitImplant(0, 0, implant(11213), replaced));
    REQUIRE(replaced.has_value());
    CHECK_EQ(replaced->objectDescriptionId, 11200u);
    // Damping Weave II: -20 % Energy damage taken, x1.2: -24.
    CHECK_EQ(member.energyDamageTakenPercent, -24);

    InventoryItem taken = {};
    REQUIRE(party.takeImplant(0, 1, taken));
    CHECK_EQ(taken.objectDescriptionId, 11201u);
    CHECK_EQ(member.magicalBonuses.armorClass, armorClassBefore);
    CHECK_FALSE(party.takeImplant(0, 1, taken));
}

TEST_CASE("a world's loot.yml: its random items roll only from its classes, by treasure level")
{
    ItemTable itemTable = itemTableWithHesperItems();
    std::string error;
    REQUIRE_MESSAGE(itemTable.loadWorldLootYaml(
        "schema: openyamm.worldLoot.v1\n"
        "treasure_levels: [H1, H1, H1, H2, H2, H3]\n"
        "classes:\n"
        "  H1: {11000: 6, 11022: 1}\n"
        "  H2: {11022: 5, 11000: 0}\n"
        "  H3: {11008: 1}\n", "hesper", error), error);
    REQUIRE(itemTable.worldLoot("hesper") != nullptr);
    CHECK(itemTable.worldLoot("mm8") == nullptr);

    std::mt19937 rng(7);
    const auto roll = [&](const std::string &worldId, int treasureLevel)
    {
        ItemGenerationRequest request = {};
        request.worldId = worldId;
        request.treasureLevel = treasureLevel;
        request.mode = ItemGenerationMode::ChestLoot;
        request.allowRareItems = false;
        return ItemGenerator::generateRandomInventoryItem(itemTable, gameData().standardItemEnchantTable,
            gameData().specialItemEnchantTable, request, nullptr, rng);
    };

    for (int trial = 0; trial < 200; ++trial)
    {
        const std::optional<InventoryItem> easy = roll("hesper", 2);
        REQUIRE(easy.has_value());
        CHECK((easy->objectDescriptionId == 11000 || easy->objectDescriptionId == 11022));
        const std::optional<InventoryItem> medium = roll("hesper", 5);
        REQUIRE(medium.has_value());
        CHECK(medium->objectDescriptionId == 11022);
        const std::optional<InventoryItem> hard = roll("hesper", 7);
        REQUIRE(hard.has_value());
        CHECK(hard->objectDescriptionId == 11008);
        const std::optional<InventoryItem> home = roll("mm8", 6);
        REQUIRE(home.has_value());
        CHECK(home->objectDescriptionId < 11000);
    }

    CHECK_FALSE(itemTable.loadWorldLootYaml(
        "schema: openyamm.worldLoot.v1\ntreasure_levels: [H1, H1, H1, H2, H2, H3]\nclasses:\n  H1: {11000: 1}\n",
        "hesper", error));
    CHECK(error.find("unknown class H2") != std::string::npos);
    CHECK_FALSE(itemTable.loadWorldLootYaml(
        "schema: openyamm.worldLoot.v1\ntreasure_levels: [H1, H1, H1, H1, H1, H1]\nclasses:\n  H1: {99999: 1}\n",
        "hesper", error));
    CHECK(error.find("99999") != std::string::npos);
}

TEST_CASE("the Hum: damage spells at its share by nodes down, a map's own share, Hum points and the null field")
{
    Party party = makeParty({makeMember("Ada", "Sorcerer")}, 0);
    Character caster = *party.member(0);
    party.setSpellField({100009, 100010, 100014}, {50, 65, 80, 100}, std::nullopt);
    CHECK_EQ(party.spellDamagePercentFor(caster), 50);
    party.setQuestBit(100010, true);
    CHECK_EQ(party.spellDamagePercentFor(caster), 65);
    caster.humPoints = 30;
    CHECK_EQ(party.spellDamagePercentFor(caster), 95);
    party.setQuestBit(100009, true);
    party.setQuestBit(100014, true);
    CHECK_EQ(party.spellDamagePercentFor(caster), 100);

    // The Crownspire keeps the full Hum; D9 is a null field.
    party.setSpellField({100009, 100010, 100014}, {50, 65, 80, 100}, 50);
    caster.humPoints = 0;
    CHECK_EQ(party.spellDamagePercentFor(caster), 50);
    party.setSpellField({}, {}, 0);
    CHECK(party.castingBlockedFor(caster));
    caster.equippedItemEffectFlags.insert("NullFieldCasting50");
    CHECK_FALSE(party.castingBlockedFor(caster));
    CHECK_EQ(party.spellDamagePercentFor(caster), 50);

    // A world without a Hum.
    party.setSpellField({}, {}, std::nullopt);
    CHECK_EQ(party.spellDamagePercentFor(caster), 100);
}

TEST_CASE("Hesper consumables: a stim heals and cures Weakness, a ration feeds, a breach charge is set off")
{
    const ItemTable &itemTable = itemTableWithHesperItems();
    Party party = makeParty({makeMember("Ada", "Knight")}, 0);
    Character &ada = *party.member(0);
    ada.health = 10;
    ada.conditions.set(static_cast<size_t>(CharacterCondition::Weak));

    const InventoryItemUseResult stim = InventoryItemUseRuntime::useItemOnMember(
        party, 0, ItemGenerator::makeInventoryItem(11302, itemTable, ItemGenerationMode::Generic), itemTable, nullptr);
    CHECK(stim.consumed);
    CHECK_EQ(party.member(0)->health, 25);
    CHECK_FALSE(party.member(0)->conditions.test(static_cast<size_t>(CharacterCondition::Weak)));

    const int food = party.food();
    const InventoryItemUseResult ration = InventoryItemUseRuntime::useItemOnMember(
        party, 0, ItemGenerator::makeInventoryItem(11305, itemTable, ItemGenerationMode::Generic), itemTable, nullptr);
    CHECK(ration.consumed);
    CHECK_EQ(party.food(), food + 2);

    const InventoryItemUseResult breach = InventoryItemUseRuntime::useItemOnMember(
        party, 0, ItemGenerator::makeInventoryItem(11304, itemTable, ItemGenerationMode::Generic), itemTable, nullptr);
    CHECK(breach.consumed);
    CHECK(breach.action == InventoryItemUseAction::PlaceBreachCharge);
}

TEST_CASE("a house price switched by a QBit: get answers with the switched price once the party has it")
{
    std::vector<std::string> row = {"9451", "0", "Tavern", "0", "27", "The Last Lamp", "", "", "0", "0", "0", "0",
        "13", "1", "", "0", "", "", "0", "0", "0", "0", "0", "", "none", "100102:9"};
    HouseTable table = {};
    REQUIRE(table.loadFromRows({row}));
    REQUIRE(table.get(9451) != nullptr);
    CHECK_EQ(table.get(9451)->priceMultiplier, doctest::Approx(13.0f));
    bool done = false;
    table.setQuestBitQuery([&done](uint32_t qbit) { return qbit == 100102 && done; });
    CHECK_EQ(table.get(9451)->priceMultiplier, doctest::Approx(13.0f));
    done = true;
    CHECK_EQ(table.get(9451)->priceMultiplier, doctest::Approx(9.0f));
    CHECK(table.get(9451)->teachesNothing);
}

TEST_CASE("a world's floor burn: its damage type, resisted when it says so, and FireImmune spares a Fire floor")
{
    Party party = makeParty({makeMember("Ada", "Knight"), makeMember("Bram", "Knight")}, 0);
    const auto resetHealth = [&party]()
    {
        for (size_t index = 0; index < 2; ++index)
        {
            party.member(index)->maxHealth = 1000;
            party.member(index)->health = 1000;
        }
    };
    OutdoorMovementEffects burn = {};
    burn.burningDamageTicks = 1;
    resetHealth();
    party.member(1)->equippedItemEffectFlags.insert("FireImmune");

    // MM: a tenth of each member's health as Fire; the immune member is spared.
    party.applyMovementEffects(burn);
    CHECK_EQ(party.member(0)->health, 900);
    CHECK_EQ(party.member(1)->health, 1000);

    // Resisted Fire: the immunity is a resistance too.
    party.setFloorBurn(CombatDamageType::Fire, true);
    resetHealth();
    party.applyMovementEffects(burn);
    CHECK_GE(party.member(0)->health, 900);
    CHECK_EQ(party.member(1)->health, 1000);

    // Another type burns the immune member as well.
    party.setFloorBurn(CombatDamageType::Body, false);
    resetHealth();
    party.applyMovementEffects(burn);
    CHECK_EQ(party.member(1)->health, 900);
}

TEST_CASE("a worn Wetsuit spares its wearer the water damage (OY-309)")
{
    Party party = makeParty({makeMember("Ada", "Knight"), makeMember("Bram", "Knight")}, 0);

    for (size_t index = 0; index < 2; ++index)
    {
        party.member(index)->maxHealth = 1000;
        party.member(index)->health = 1000;
    }

    party.member(1)->equipment.armor = 1406;
    OutdoorMovementEffects water = {};
    water.waterDamageTicks = 1;
    party.applyMovementEffects(water);
    CHECK_LT(party.member(0)->health, 1000);
    CHECK_EQ(party.member(1)->health, 1000);
}

TEST_CASE("an item of Power adds five worn levels (OY-199)")
{
    Character member = {};
    member.level = 10;
    ItemEnchantRuntime::applySpecialEnchantBonus(member, SpecialItemEnchantKind::Power);
    CHECK_EQ(member.equippedLevelBonus, 5);
}

TEST_CASE("characters age with the calendar and with magical ageing (OY-349)")
{
    Party party = makeParty({makeMember("Ada", "Knight")}, 0);
    Character &member = *party.member(0);
    member.birthYear = 1150;
    CHECK_EQ(GameMechanics::characterAge(member), 18);

    // Forty years of 12 months of 28 days later.
    party.setGameMinutes(40.0f * 12.0f * 28.0f * 24.0f * 60.0f + 60.0f);
    CHECK_EQ(member.playedYears, 40u);
    CHECK_EQ(GameMechanics::characterAge(member), 58);

    // A ghost's touch adds years.
    member.ageModifier = 50;
    CHECK_EQ(GameMechanics::characterAge(member), 108);
}

TEST_CASE("vendor stock gated by the world's objectives: a tiered lane shows what the party has earned")
{
    std::vector<std::string> vendorRow(25);
    vendorRow[0] = "9450";
    vendorRow[1] = "hesper";
    vendorRow[2] = "9450";
    vendorRow[3] = "hesper:vendor/9450";
    vendorRow[4] = "Provisions";
    vendorRow[5] = "Landfall";
    vendorRow[6] = "General Store";
    vendorRow[8] = "Mm9GeneralStore";
    vendorRow[11] = "1";
    vendorRow[13] = "1";
    vendorRow[16] = "1";
    vendorRow[18] = "7";
    vendorRow[19] = "1";
    vendorRow[22] = "LiveGameplay";
    std::vector<std::vector<std::string>> stockRows;
    // A page of eight (the general store's), the four entries twice, as stage.py pads a tiered list.
    const std::array<std::pair<uint32_t, uint32_t>, 8> stock = {
        {{1, 0}, {2, 0}, {3, 3}, {4, 7}, {1, 0}, {2, 0}, {3, 3}, {4, 7}}};
    for (size_t slot = 0; slot < stock.size(); ++slot)
    {
        for (const char *pLane : {"standard", "special"})
        {
            stockRows.push_back({"9450", pLane, "0", std::to_string(slot), std::to_string(stock[slot].first), "1",
                "1", "0", "0", "0", "1", std::to_string(stock[slot].second)});
        }
    }
    HouseTable houseTable;
    std::string error;
    REQUIRE_MESSAGE(houseTable.appendVendorRows({vendorRow}, {{"9450", "hesper", "9450", "0"}}, stockRows, error),
        error);
    const HouseEntry *pVendor = houseTable.get(9450);
    REQUIRE(pVendor != nullptr);

    const auto shown = [pVendor](size_t objectivesDone)
    {
        Party party = makeParty({makeMember("Ada", "Knight")}, 0);
        party.setObjectiveQBits({100040, 100041, 100042, 100043, 100009, 100010, 100014, 100018});
        for (size_t index = 0; index < objectivesDone; ++index)
        {
            party.setQuestBit(std::array<uint32_t, 8>{100040, 100041, 100042, 100043, 100009, 100010, 100014,
                100018}[index], true);
        }
        CHECK_EQ(party.objectivesDone(), objectivesDone);
        const ItemTable itemTable = {};
        const StandardItemEnchantTable standardTable = {};
        const SpecialItemEnchantTable specialTable = {};
        std::vector<uint32_t> ids;
        for (const InventoryItem &item : HouseServiceRuntime::ensureStock(party, itemTable, standardTable,
                 specialTable, *pVendor, 0.0f, HouseStockMode::ShopStandard))
        {
            ids.push_back(item.objectDescriptionId);
        }
        return ids;
    };
    CHECK(shown(0) == std::vector<uint32_t>{1, 2, 1, 2, 1, 2, 1, 2});
    CHECK(shown(3) == std::vector<uint32_t>{1, 2, 3, 1, 2, 3, 1, 2});
    CHECK(shown(7) == std::vector<uint32_t>{1, 2, 3, 4, 1, 2, 3, 4});
}

TEST_CASE("a world's curated enchantment pool: its loot rolls only the enchantments it lists, special by class")
{
    ItemTable itemTable = itemTableWithHesperItems();
    std::string error;
    // The engine already keeps specials to the treasure level's grades (level 3: A and B, 5: B to D, 6: D).
    REQUIRE_MESSAGE(itemTable.loadWorldLootYaml(
        "schema: openyamm.worldLoot.v1\n"
        "treasure_levels: [H1, H1, H1, H2, H2, H3]\n"
        "classes:\n"
        "  H1: {11022: 1, 11100: 1}\n"
        "  H2: {11022: 1, 11100: 1}\n"
        "  H3: {11022: 1, 11100: 1}\n"
        "enchantments:\n"
        "  standard: [\"of Health\"]\n"
        "  special: {H1: [\"of Cold\"], H2: [], H3: [\"of Ice\", \"Vampiric\"]}\n", "hesper", error), error);

    const StandardItemEnchantTable &standardTable = gameData().standardItemEnchantTable;
    const SpecialItemEnchantTable &specialTable = gameData().specialItemEnchantTable;
    std::mt19937 rng(11);
    size_t standardCount = 0;
    std::array<size_t, 3> specialCounts = {};

    for (int trial = 0; trial < 600; ++trial)
    {
        for (size_t tier = 0; tier < 3; ++tier)
        {
            ItemGenerationRequest request = {};
            request.worldId = "hesper";
            request.treasureLevel = std::array<int, 3>{3, 5, 6}[tier];
            request.mode = ItemGenerationMode::ChestLoot;
            request.allowRareItems = false;
            const std::optional<InventoryItem> item = ItemGenerator::generateRandomInventoryItem(
                itemTable, standardTable, specialTable, request, nullptr, rng);
            REQUIRE(item.has_value());

            if (item->standardEnchantId != 0)
            {
                CHECK(toLowerCopy(standardTable.get(item->standardEnchantId)->suffix) == "of health");
                ++standardCount;
            }

            if (item->specialEnchantId != 0)
            {
                const std::string suffix = toLowerCopy(specialTable.get(item->specialEnchantId)->suffix);
                CHECK((tier == 0 ? suffix == "of cold" : (suffix == "of ice" || suffix == "vampiric")));
                ++specialCounts[tier];
            }
        }
    }

    CHECK(standardCount > 0);
    CHECK(specialCounts[0] > 0);
    CHECK(specialCounts[1] == 0);
    CHECK(specialCounts[2] > 0);
}

TEST_CASE("Workshop mods: fitted to the first worn item they suit, saved with it, their effect worn with it")
{
    ItemTable itemTable = itemTableWithHesperItems();
    std::string error;
    std::vector<std::vector<std::string>> modRows = rowsFromText(
        "mod_id\tname\tfits\n"
        "1\tShieldbreaker\tWeapon|Weapon2\n"
        "2\tInsulation\tArmor|Helm|Cloak\n");
    // Insulation: +20 Energy resistance (the item_effects energy_resistance column, the 29th after might).
    modRows[2].resize(3 + 38);
    modRows[2][3 + 28] = "20";
    modRows[1].resize(3 + 38);
    modRows[1][3 + 27] = "ShieldDamage20";
    REQUIRE_MESSAGE(itemTable.loadWorkshopModRows(modRows, error), error);
    REQUIRE(itemTable.workshopMod(2) != nullptr);
    CHECK(itemTable.workshopMod(2)->effect.energyResistance == 20);

    Character member = makeMember("Ada", "Knight");
    member.equipment.mainHand = 11022;     // Plasma Saber (Weapon)
    member.equipment.armor = 11100;        // Weave Suit (Armor)
    Party party = makeParty({member}, 0);
    party.setItemTable(&itemTable);
    CHECK_EQ(party.workshopModTarget(0, 1), 11022u);
    CHECK_EQ(party.workshopModTarget(0, 2), 11100u);
    CHECK_EQ(party.workshopModTarget(0, 9), 0u);

    const int before = party.member(0)->energyResistance;
    CHECK_EQ(party.fitWorkshopMod(0, 2), 11100u);
    CHECK_EQ(party.equippedItemRuntime(0, EquipmentSlot::Armor)->workshopModId, 2);
    CHECK_EQ(party.member(0)->energyResistance, before + 20);
}

TEST_CASE("a vendor's resale cap: it pays at most its share of the value, whatever the Merchant skill")
{
    const ItemTable &itemTable = itemTableWithHesperItems();
    const ItemDefinition *pSaber = itemTable.get(11022);
    REQUIRE(pSaber != nullptr);
    InventoryItem saber = ItemGenerator::makeInventoryItem(11022, itemTable, ItemGenerationMode::Generic);
    Character merchant = makeMember("Ada", "Knight");
    merchant.skills["Merchant"] = CharacterSkill{"Merchant", 10, SkillMastery::Grandmaster};
    const int uncapped = PriceCalculator::itemSellingPrice(&merchant, saber, *pSaber, 1.0f);
    const int capped = PriceCalculator::itemSellingPrice(&merchant, saber, *pSaber, 1.0f, nullptr, nullptr, 0, 30);
    CHECK(uncapped > capped);
    CHECK_EQ(capped, pSaber->value * 30 / 100);
}

TEST_CASE("a world's own enchantments roll only on its items and work worn and in attacks")
{
    StandardItemEnchantTable standardTable = gameData().standardItemEnchantTable;
    SpecialItemEnchantTable specialTable = gameData().specialItemEnchantTable;
    std::string error;
    REQUIRE_MESSAGE(loadWorldEnchantments(
        "schema: openyamm.worldEnchantments.v1\n"
        "standard:\n"
        "  - {id: 100, name: of Insulation, stat: energy_resistance, slots: [10, 10, 10, 0, 10, 10, 10, 10, 10]}\n"
        "special:\n"
        "  - {id: 100, name: of Static, rarity: A, slots: [20, 20, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0], value: 1500,\n"
        "     description: '+15 % damage to shields', effect: {shield_damage: 15, bonus_damage: 20,\n"
        "     against: [[10000, 10062]]}}\n"
        "  - {id: 101, name: of Charge, rarity: A, slots: [0, 0, 0, 10, 10, 0, 0, 0, 0, 0, 10, 10],\n"
        "     effect: {personal_shield: 200}}\n", "hesper", standardTable, specialTable, error), error);
    REQUIRE(specialTable.get(100) != nullptr);
    CHECK(specialTable.get(100)->kind == SpecialItemEnchantKind::World);
    CHECK(specialTable.get(100)->worldEffect.bonusAgainst(10010));
    CHECK_FALSE(specialTable.get(100)->worldEffect.bonusAgainst(10070));
    CHECK(standardTable.get(100)->kind == StandardItemEnchantKind::EnergyResistance);
    // Ids already taken are refused.
    SpecialItemEnchantTable twice = specialTable;
    StandardItemEnchantTable twiceStandard = standardTable;
    CHECK_FALSE(loadWorldEnchantments("schema: openyamm.worldEnchantments.v1\nspecial:\n  - {id: 100, name: x, "
        "rarity: A, slots: [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]}\n", "hesper", twiceStandard, twice, error));

    // A level-3 weapon in Hesper may roll it; anywhere else never.
    const ItemTable &itemTable = itemTableWithHesperItems();
    const ItemDefinition &saber = *itemTable.get(11022);
    std::mt19937 rng(5);
    bool rolledInHesper = false;
    for (int trial = 0; trial < 400; ++trial)
    {
        rolledInHesper = rolledInHesper
            || ItemEnchantRuntime::chooseSpecialEnchantId(saber, specialTable, 3, rng, "hesper") == 100;
        CHECK(ItemEnchantRuntime::chooseSpecialEnchantId(saber, specialTable, 3, rng, "mm8") != 100);
    }
    CHECK(rolledInHesper);

    // Worn: of Charge adds its personal shield; on the sword, of Static raises the melee hit on shields and against
    // the Kreegans.
    Character member = makeMember("Ada", "Knight");
    member.equipment.mainHand = 11022;
    member.equipmentRuntime.mainHand.specialEnchantId = 100;
    member.equipment.armor = 11100;
    member.equipmentRuntime.armor.specialEnchantId = 101;
    Party party = makeParty({member}, 0);
    party.setItemTable(&itemTable);
    party.setItemEnchantTables(&standardTable, &specialTable);
    party.rebuildMagicalBonusesFromBuffs();
    const Character &worn = *party.member(0);
    CHECK(worn.armorShieldPoints >= 200);
    CHECK_EQ(worn.meleeWeaponEnchant.shieldDamagePercent, 15);
    CHECK(worn.meleeWeaponEnchant.bonusAgainst(10040));
    const CharacterAttackProfile profile = GameMechanics::buildCharacterAttackProfile(worn, &itemTable, nullptr);
    CHECK(profile.meleeShieldModifiers.shieldDamageMultiplier > 1.0f);
}
