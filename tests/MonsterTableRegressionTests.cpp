#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/ImageAssetLoader.h"
#include "engine/TextTable.h"
#include "game/maps/MapAssetLoader.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/SpriteTables.h"
#include "game/gameplay/ActorInspectPreviewAnimation.h"

#include <array>
#include <cctype>
#include <filesystem>
#include <set>

namespace
{
std::vector<std::string> makeMonsterStatsRow(
    int id,
    const std::string &name,
    bool bloodSplat,
    const std::string &attack1Missile,
    int attack2Chance,
    const std::string &attack2Missile,
    int spell1Chance,
    const std::string &spell1Descriptor)
{
    std::vector<std::string> row(38);
    row[0] = std::to_string(id);
    row[1] = name;
    row[2] = name + "Pic";
    row[3] = "1";
    row[4] = "10";
    row[5] = "0";
    row[6] = "10";
    row[7] = "0";
    row[8] = bloodSplat ? "1" : "0";
    row[10] = "short";
    row[11] = "normal";
    row[12] = "0";
    row[13] = "100";
    row[14] = "30";
    row[17] = "Physical";
    row[18] = "1d4";
    row[19] = attack1Missile;
    row[20] = std::to_string(attack2Chance);
    row[21] = "Physical";
    row[22] = "1d4";
    row[23] = attack2Missile;
    row[24] = std::to_string(spell1Chance);
    row[25] = spell1Descriptor;
    return row;
}

std::vector<std::string> makeMonsterPresentationRow(
    int id,
    const std::string &internalName,
    const std::array<std::string, 8> &spriteNames)
{
    std::vector<std::string> row(19, "0");
    row[0] = std::to_string(id);
    row[1] = internalName;

    for (size_t spriteIndex = 0; spriteIndex < spriteNames.size(); ++spriteIndex)
    {
        row[11 + spriteIndex] = spriteNames[spriteIndex];
    }

    return row;
}
}

TEST_CASE("monster stats parser preserves blood splat on death flag")
{
    OpenYAMM::Game::MonsterTable table = {};

    REQUIRE(table.loadStatsFromRows({
        makeMonsterStatsRow(1, "Lizardman", true, "", 0, "", 0, ""),
        makeMonsterStatsRow(98, "Wisp", false, "", 0, "", 0, "")
    }));

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pLizardman = table.findStatsById(1);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pWisp = table.findStatsById(98);

    REQUIRE(pLizardman != nullptr);
    REQUIRE(pWisp != nullptr);
    CHECK(pLizardman->bloodSplatOnDeath);
    CHECK_FALSE(pWisp->bloodSplatOnDeath);
}

TEST_CASE("MM6 merged monster data defines biological blood defaults")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1));

    const std::optional<std::string> tableText =
        assetFileSystem.readTextFile("engine/data_tables/monster_data.txt");
    REQUIRE(tableText.has_value());
    const std::optional<OpenYAMM::Engine::TextTable> parsedTable =
        OpenYAMM::Engine::TextTable::parseTabSeparated(*tableText);
    REQUIRE(parsedTable.has_value());

    std::vector<std::vector<std::string>> rows;
    rows.reserve(parsedTable->getRowCount());
    for (size_t rowIndex = 0; rowIndex < parsedTable->getRowCount(); ++rowIndex)
    {
        rows.push_back(parsedTable->getRow(rowIndex));
    }

    OpenYAMM::Game::MonsterTable table;
    REQUIRE(table.loadStatsFromRows(rows));

    for (int monsterId = 475; monsterId <= 652; ++monsterId)
    {
        CAPTURE(monsterId);
        const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pStats = table.findStatsById(monsterId);
        if (monsterId >= 649 && monsterId <= 651)
        {
            // The Cactus (only placed in MMerge's removed BrAlvar map) is not part of the game.
            CHECK(pStats == nullptr);
            continue;
        }
        REQUIRE(pStats != nullptr);
        const bool bloodlessMaterial =
            (monsterId >= 523 && monsterId <= 534)
            || (monsterId >= 541 && monsterId <= 549)
            || (monsterId >= 562 && monsterId <= 570)
            || (monsterId >= 589 && monsterId <= 591)
            || (monsterId >= 622 && monsterId <= 624)
            || (monsterId >= 628 && monsterId <= 630)
            || (monsterId >= 647 && monsterId <= 652);
        CHECK_EQ(pStats->bloodSplatOnDeath, !bloodlessMaterial);
    }

    for (int monsterId = 901; monsterId <= 906; ++monsterId)
    {
        CAPTURE(monsterId);
        const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pStats = table.findStatsById(monsterId);
        REQUIRE(pStats != nullptr);
        CHECK(pStats->bloodSplatOnDeath);
    }
}

TEST_CASE("monster stats parser treats plain numeric damage like OE Nd1 damage")
{
    OpenYAMM::Game::MonsterTable table = {};
    std::vector<std::string> row = makeMonsterStatsRow(1, "FlatDamage", true, "", 0, "", 0, "");
    row[18] = "5";
    row[22] = "3";

    REQUIRE(table.loadStatsFromRows({row}));

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pMonster = table.findStatsById(1);

    REQUIRE(pMonster != nullptr);
    CHECK_EQ(pMonster->attack1Damage.diceRolls, 5);
    CHECK_EQ(pMonster->attack1Damage.diceSides, 1);
    CHECK_EQ(pMonster->attack1Damage.bonus, 0);
    CHECK_EQ(pMonster->attack2Damage.diceRolls, 3);
    CHECK_EQ(pMonster->attack2Damage.diceSides, 1);
    CHECK_EQ(pMonster->attack2Damage.bonus, 0);
}

TEST_CASE("monster stats parser classifies melee mixed and ranged attack styles")
{
    OpenYAMM::Game::MonsterTable table = {};

    REQUIRE(table.loadStatsFromRows({
        makeMonsterStatsRow(12, "Melee", true, "", 0, "", 0, ""),
        makeMonsterStatsRow(5, "Mixed", true, "", 35, "arrow", 0, ""),
        makeMonsterStatsRow(16, "Ranged", true, "arrow", 0, "", 0, "")
    }));

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pMelee = table.findStatsById(12);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pMixed = table.findStatsById(5);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pRanged = table.findStatsById(16);

    REQUIRE(pMelee != nullptr);
    REQUIRE(pMixed != nullptr);
    REQUIRE(pRanged != nullptr);
    CHECK(pMelee->attackStyle == OpenYAMM::Game::MonsterTable::MonsterAttackStyle::MeleeOnly);
    CHECK(pMixed->attackStyle == OpenYAMM::Game::MonsterTable::MonsterAttackStyle::MixedMeleeRanged);
    CHECK(pRanged->attackStyle == OpenYAMM::Game::MonsterTable::MonsterAttackStyle::Ranged);
}

TEST_CASE("monster stats parser recognizes supported elemental missile tokens")
{
    OpenYAMM::Game::MonsterTable table = {};

    REQUIRE(table.loadStatsFromRows({
        makeMonsterStatsRow(71, "Dragon Flightleader", true, "Cold", 0, "", 0, ""),
        makeMonsterStatsRow(72, "Great Wyrm", true, "Elec", 0, "", 0, ""),
        makeMonsterStatsRow(112, "Emerald Dragon", true, "Ener", 0, "", 0, "")
    }));

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pFlightleader = table.findStatsById(71);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pGreatWyrm = table.findStatsById(72);
    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pEmeraldDragon = table.findStatsById(112);

    REQUIRE(pFlightleader != nullptr);
    REQUIRE(pGreatWyrm != nullptr);
    REQUIRE(pEmeraldDragon != nullptr);
    CHECK(pFlightleader->attack1HasMissile);
    CHECK(pGreatWyrm->attack1HasMissile);
    CHECK(pEmeraldDragon->attack1HasMissile);
    CHECK(pFlightleader->attackStyle == OpenYAMM::Game::MonsterTable::MonsterAttackStyle::Ranged);
    CHECK(pGreatWyrm->attackStyle == OpenYAMM::Game::MonsterTable::MonsterAttackStyle::Ranged);
    CHECK(pEmeraldDragon->attackStyle == OpenYAMM::Game::MonsterTable::MonsterAttackStyle::Ranged);
}

TEST_CASE("monster stats applies supported kind flags from bolster monster type data")
{
    OpenYAMM::Game::MonsterTable table = {};
    std::vector<std::string> row = makeMonsterStatsRow(52, "Vampire", true, "", 0, "", 0, "");

    REQUIRE(table.loadStatsFromRows({row}));

    OpenYAMM::Game::MergedBolsterMonsterTable bolsterMonsterTable = {};
    REQUIRE(bolsterMonsterTable.loadFromRows({
        {
            "#",
            "Note",
            "Type",
            "ExtraType",
            "Creed",
            "Gender",
            "Style",
            "Pref magic",
            "No bounty hunt",
            "New ranged attacks",
            "New spells",
            "Size affects HP",
            "Replicate",
            "New summons",
            "Summon Id",
            "Extra points",
            "Max HP Boost (%)",
        },
        {
            "52", "Vampire", "Undead", "Peasant,NoArena,Titan", "Dark", "", "", "", "-", "-", "-", "-", "-", "-",
            "", "", "",
        },
    }));
    REQUIRE(table.applyKindFlagsFromBolsterMonsterTable(bolsterMonsterTable));

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pMonster = table.findStatsById(52);

    REQUIRE(pMonster != nullptr);
    CHECK(pMonster->hasKind(OpenYAMM::Game::MonsterKind::Undead));
    CHECK(pMonster->hasKind(OpenYAMM::Game::MonsterKind::Peasant));
    CHECK(pMonster->hasKind(OpenYAMM::Game::MonsterKind::NoArena));
    CHECK(pMonster->hasKind(OpenYAMM::Game::MonsterKind::Titan));
    CHECK_FALSE(pMonster->hasKind(OpenYAMM::Game::MonsterKind::NoCorpse));
    CHECK_FALSE(pMonster->hasKind(OpenYAMM::Game::MonsterKind::Dragon));
}

TEST_CASE("monster stats applies no corpse kind from bolster monster extra type data")
{
    OpenYAMM::Game::MonsterTable table = {};
    std::vector<std::string> row = makeMonsterStatsRow(499, "Devil Captain", true, "", 0, "", 0, "");

    REQUIRE(table.loadStatsFromRows({row}));

    OpenYAMM::Game::MergedBolsterMonsterTable bolsterMonsterTable = {};
    REQUIRE(bolsterMonsterTable.loadFromRows({
        {
            "#",
            "Note",
            "Type",
            "ExtraType",
            "Creed",
            "Gender",
            "Style",
            "Pref magic",
            "No bounty hunt",
            "New ranged attacks",
            "New spells",
            "Size affects HP",
            "Replicate",
            "New summons",
            "Summon Id",
            "Extra points",
            "Max HP Boost (%)",
        },
        {"499", "Devil Captain", "Demon", "NoCorpse", "Dark", "", "", "", "-", "-", "-", "-", "-", "-", "", "", ""},
    }));
    REQUIRE(table.applyKindFlagsFromBolsterMonsterTable(bolsterMonsterTable));

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pMonster = table.findStatsById(499);

    REQUIRE(pMonster != nullptr);
    CHECK(pMonster->hasKind(OpenYAMM::Game::MonsterKind::NoCorpse));
}

TEST_CASE("monster death drop parser maps multiple drops to monster id")
{
    OpenYAMM::Game::MonsterTable table = {};

    REQUIRE(table.loadDeathDropsFromRows({
        {"MonsterID", "MonsterName", "ItemID", "ItemName", "ChancePercent", "Description"},
        {"85", "Dire Wolf Yearling", "201", "Wolf's Eye", "20", "Reagent drop"},
        {"85", "Dire Wolf Yearling", "633", "Dire Wolf Pelt", "35", "Bounty drop"},
        {"86", "Dire Wolf", "633", "Dire Wolf Pelt", "0", "Disabled drop"}
    }));

    const std::vector<OpenYAMM::Game::MonsterTable::MonsterDeathDropEntry> &drops =
        table.deathDropsForMonsterId(85);
    const std::vector<OpenYAMM::Game::MonsterTable::MonsterDeathDropEntry> &disabledDrops =
        table.deathDropsForMonsterId(86);

    REQUIRE_EQ(drops.size(), 2);
    CHECK_EQ(drops[0].itemId, 201u);
    CHECK_EQ(drops[0].chancePercent, 20);
    CHECK_EQ(drops[1].itemId, 633u);
    CHECK_EQ(drops[1].chancePercent, 35);
    CHECK(disabledDrops.empty());
}

TEST_CASE("dynamic bounty monsters load their sprite frame families")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1));

    OpenYAMM::Game::MonsterTable monsterTable;
    REQUIRE(monsterTable.loadEntriesFromRows({
        makeMonsterPresentationRow(
            218,
            "Cleric Sun B",
            {"m176s", "m176w", "m176a", "m176a", "m176n", "m176d", "m176x", "m176f"}),
        makeMonsterPresentationRow(
            242,
            "Elemental Light B",
            {"m208w", "m208w", "m208a", "m208a", "m208n", "m208d", "null", "m208w"})
    }));
    OpenYAMM::Game::SpriteFrameTable reloadedMapSpriteFrameTable;
    CHECK_FALSE(reloadedMapSpriteFrameTable.findFrameIndexBySpriteName("m176s").has_value());
    CHECK_FALSE(reloadedMapSpriteFrameTable.findFrameIndexBySpriteName("m208w").has_value());

    REQUIRE(OpenYAMM::Game::ensureMonsterSpriteFramesLoaded(
        assetFileSystem,
        monsterTable,
        218,
        reloadedMapSpriteFrameTable));
    CHECK(reloadedMapSpriteFrameTable.findFrameIndexBySpriteName("m176s").has_value());

    REQUIRE(OpenYAMM::Game::ensureMonsterSpriteFramesLoaded(
        assetFileSystem,
        monsterTable,
        242,
        reloadedMapSpriteFrameTable));
    CHECK(reloadedMapSpriteFrameTable.findFrameIndexBySpriteName("m176s").has_value());
    CHECK(reloadedMapSpriteFrameTable.findFrameIndexBySpriteName("m208w").has_value());

    // Their frames are metadata only (tier scales, attack timing): the monster billboard images left the runtime on
    // 2026-10-21 (assets_legacy/sprites_mm7_monsters_20261021) and every monster draws its model.
}

TEST_CASE("creature inspect metadata uses original families after merged ID mapping")
{
    using namespace OpenYAMM;
    const std::filesystem::path root = OPENYAMM_SOURCE_DIR;
    Engine::AssetFileSystem assets;
    REQUIRE(assets.initialize(root, root / "assets_dev", Engine::AssetScaleTier::X1));
    const std::optional<std::string> text = assets.readTextFile("engine/data_tables/monster_descriptors.txt");
    REQUIRE(text);
    const std::optional<Engine::TextTable> parsed = Engine::TextTable::parseTabSeparated(*text);
    REQUIRE(parsed);
    std::vector<std::vector<std::string>> rows;
    for (size_t i = 0; i < parsed->getRowCount(); ++i)
    {
        rows.push_back(parsed->getRow(i));
    }
    Game::MonsterTable table;
    REQUIRE(table.loadEntriesFromRows(rows));
    REQUIRE(table.findById(1));
    REQUIRE(table.findById(199));
    REQUIRE(table.findById(475));
    CHECK(table.findById(1)->inspectYOffset == -55); // MM8 lizardman peasant.
    CHECK(table.findById(4)->inspectYOffset == -90); // MM8 warrior, different original family.
    CHECK(table.findById(1)->inspectFidgetWhenMoving);
    CHECK(table.findById(199)->inspectYOffset == -60); // MM7 angel, native ID 1.
    CHECK(table.findById(313)->inspectAttackChance == 0); // MM7 peasant, native ID 115.
    CHECK(table.findById(430)->inspectAttackChance == 0); // MM7 second peasant range.
    CHECK_FALSE(table.findById(312)->inspectFidgetWhenMoving);
    CHECK(table.findById(312)->inspectAttackChance == 100);
    CHECK(table.findById(475)->inspectYOffset == -40); // MM6 goblin, native ID 1.
    CHECK(table.findById(475)->inspectAttackChance == 30);
    CHECK(table.findById(502)->inspectYOffset == 0); // MM6 cleric, native ID 28.
}

TEST_CASE("creature inspect animation snapshots AI and resets only for a different type")
{
    using namespace OpenYAMM::Game;
    SpriteFrameTable frames;
    std::string error;
    REQUIRE(frames.loadFromYaml(R"(
sprites:
  - sprite_name: inspect_attack
    sprite_id: 10
    animation_length_raw: 4
    frames:
      - {texture_name: first, frame_length_raw: 2}
      - {texture_name: second, frame_length_raw: 2}
  - sprite_name: inspect_fidget
    sprite_id: 20
    animation_length_raw: 5
    frames:
      - {texture_name: fidget, frame_length_raw: 5}
)", error));
    MonsterEntry entry;
    entry.inspectFidgetWhenMoving = true;
    ActorInspectPreviewAnimation preview;
    const std::array<uint16_t, 8> indices = {0, 0, 10, 0, 0, 0, 0, 20};
    preview.advance(1, true, entry, indices, 0, frames, 1000);
    CHECK(preview.animation == ActorAiAnimationState::Bored);
    CHECK(preview.actionLengthTicks >= 128);
    CHECK(preview.actionLengthTicks <= 383);
    CHECK(preview.displayTimeTicks == 0);
    preview.actionTimeTicks = preview.actionLengthTicks;
    preview.advance(1, false, entry, indices, 0, frames, 1016);
    CHECK(preview.animation == ActorAiAnimationState::Bored); // Equality does not expire.
    preview.advance(1, false, entry, indices, 0, frames, 1032);
    CHECK(preview.animation == ActorAiAnimationState::Standing);
    CHECK(preview.displayTimeTicks == 0);
    CHECK(preview.actionTimeTicks == 16); // Advance after drawing; discard previous overshoot.
    CHECK(preview.actionLengthTicks >= 128);
    CHECK(preview.actionLengthTicks <= 255);
    preview.actionTimeTicks = preview.actionLengthTicks + 1;
    preview.advance(1, false, entry, indices, 0, frames, 1048);
    CHECK(preview.animation == ActorAiAnimationState::Bored); // Uses the original moving snapshot.
    CHECK(preview.actionLengthTicks == 40);
    preview.advance(2, false, entry, indices, 0, frames, 1064);
    CHECK_FALSE(preview.movingAtFirstInspect);
    CHECK(preview.displayTimeTicks == 0);
    preview.animation = ActorAiAnimationState::Standing;
    preview.actionTimeTicks = preview.actionLengthTicks + 1;
    preview.advance(2, true, entry, indices, 0, frames, 1080);
    CHECK(preview.animation == ActorAiAnimationState::AttackMelee);
    CHECK(preview.actionLengthTicks == 32);
    preview.displayTimeTicks = 16;
    const SpriteFrameEntry *pAttack = frames.getFrame(10, 0);
    REQUIRE(pAttack);
    CHECK(frames.getFrame(10, preview.frameTimeTicks(*pAttack))->textureName == "first");
    preview.displayTimeTicks = 24;
    CHECK(frames.getFrame(10, preview.frameTimeTicks(*pAttack))->textureName == "second");
    entry.inspectAttackChance = 0;
    preview.animation = ActorAiAnimationState::Standing;
    preview.actionTimeTicks = preview.actionLengthTicks + 1;
    preview.advance(2, false, entry, indices, 0, frames, 1096);
    CHECK(preview.animation == ActorAiAnimationState::Bored);

    SpriteFrameEntry frame;
    frame.animationLengthTicks = 32;
    preview.displayTimeTicks = 15;
    CHECK(preview.frameTimeTicks(frame) == 7);
    preview.displayTimeTicks = 16;
    CHECK(preview.frameTimeTicks(frame) == 15);
    preview.displayTimeTicks = 32;
    CHECK(preview.frameTimeTicks(frame) == 0);
}

TEST_CASE("melee hit materials resolve each monster's HitMaterial and default to flesh")
{
    const auto descriptorRow = [](int id, const std::string &name, const std::string &material)
    {
        std::vector<std::string> row(23);
        row[0] = std::to_string(id);
        row[1] = name;
        row[22] = material;
        return row;
    };
    OpenYAMM::Game::MonsterTable table = {};
    REQUIRE(table.loadEntriesFromRows({
        descriptorRow(1, "Skeleton B", "Bone"),
        descriptorRow(2, "KnightPlate A", "armorplate"),
        descriptorRow(3, "Rat C", ""),
    }));

    const std::vector<std::vector<std::string>> materialRows = {
        {"#", "Material", "Glancing", "Normal", "Crushing", "ContactEffect", "Blood"},
        {"1", "Flesh", "flesh_g.wav", "flesh_n.wav", "flesh_c.wav", "blood", "1"},
        {"2", "Bone", "bone_g.wav", "bone_n.wav", "bone_c.wav", "bone_dust", "0"},
        {"3", "ArmorPlate", "plate_g.wav", "plate_n.wav", "plate_c.wav", "sparks", "0"},
    };
    REQUIRE(table.loadMeleeHitMaterialsFromRows(materialRows));

    const OpenYAMM::Game::MonsterTable::MeleeHitMaterial *pSkeleton = table.findMeleeHitMaterial(1);
    const OpenYAMM::Game::MonsterTable::MeleeHitMaterial *pKnight = table.findMeleeHitMaterial(2);
    const OpenYAMM::Game::MonsterTable::MeleeHitMaterial *pRat = table.findMeleeHitMaterial(3);
    const OpenYAMM::Game::MonsterTable::MeleeHitMaterial *pUnknown = table.findMeleeHitMaterial(99);
    REQUIRE(pSkeleton != nullptr);
    REQUIRE(pKnight != nullptr);
    REQUIRE(pRat != nullptr);
    REQUIRE(pUnknown != nullptr);
    CHECK_EQ(pSkeleton->name, "Bone");
    CHECK_EQ(pSkeleton->impactSoundPaths[2], "bone_c.wav");
    CHECK_EQ(pSkeleton->contactEffectId, "bone_dust");
    CHECK_FALSE(pSkeleton->blood);
    CHECK_EQ(pKnight->name, "ArmorPlate");
    CHECK_EQ(pRat->name, "Flesh");
    CHECK(pRat->blood);
    CHECK_EQ(pUnknown->name, "Flesh");

    // A monster naming a material the table lacks fails the load, as does a table without Flesh.
    REQUIRE(table.loadEntriesFromRows({descriptorRow(1, "Skeleton B", "Ivory")}));
    CHECK_FALSE(table.loadMeleeHitMaterialsFromRows(materialRows));
    CHECK_FALSE(table.loadMeleeHitMaterialsFromRows({{"1", "Bone", "", "", ""}}));
}

TEST_CASE("engine melee hit materials name existing sounds and classify every monster")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1));

    const auto readRows = [&assetFileSystem](const std::string &path)
    {
        const std::optional<std::string> text = assetFileSystem.readTextFile(path);
        REQUIRE(text.has_value());
        const std::optional<OpenYAMM::Engine::TextTable> parsed =
            OpenYAMM::Engine::TextTable::parseTabSeparated(*text);
        REQUIRE(parsed.has_value());
        std::vector<std::vector<std::string>> rows;
        for (size_t rowIndex = 0; rowIndex < parsed->getRowCount(); ++rowIndex)
        {
            rows.push_back(parsed->getRow(rowIndex));
        }
        return rows;
    };

    const std::vector<std::vector<std::string>> descriptorRows =
        readRows("engine/data_tables/monster_descriptors.txt");
    const std::vector<std::vector<std::string>> materialRows =
        readRows("engine/data_tables/melee_hit_materials.txt");
    OpenYAMM::Game::MonsterTable table;
    REQUIRE(table.loadEntriesFromRows(descriptorRows));
    REQUIRE(table.loadDisplayNamesFromRows(readRows("engine/data_tables/monster_data.txt")));
    REQUIRE(table.loadMeleeHitMaterialsFromRows(materialRows));

    // Every monster row names its material explicitly.
    for (const std::vector<std::string> &row : descriptorRows)
    {
        if (row.size() < 2 || row[0].empty() || !std::isdigit(static_cast<unsigned char>(row[0][0])))
        {
            continue;
        }
        CAPTURE(row[1]);
        REQUIRE(row.size() > 22);
        CHECK_FALSE(row[22].empty());
    }

    for (const std::vector<std::string> &row : materialRows)
    {
        if (row.size() < 2 || row[0].empty() || row[0][0] == '#')
        {
            continue;
        }
        for (size_t column = 2; column < std::min<size_t>(row.size(), 5); ++column)
        {
            if (!row[column].empty())
            {
                CAPTURE(row[column]);
                CHECK(assetFileSystem.exists(row[column]));
            }
        }
    }

    // Skeleton Warrior A, Ruby Dragon (Crystal Dragon C) and Goblin A.
    REQUIRE(table.findMeleeHitMaterial(397) != nullptr);
    CHECK_EQ(table.findMeleeHitMaterial(397)->name, "Bone");
    CHECK_EQ(table.findMeleeHitMaterial(114)->name, "Glass");
    CHECK_EQ(table.findMeleeHitMaterial(271)->name, "Flesh");
    CHECK(table.findMeleeHitMaterial(271)->blood);
}
