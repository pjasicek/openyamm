#include "doctest/doctest.h"

#include "game/app/GameSettings.h"
#include "game/party/Party.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/SpriteTables.h"

#include "tests/RegressionGameData.h"

#include <cctype>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <optional>
#include <set>
#include <sstream>
#include <vector>

namespace
{
const OpenYAMM::Tests::RegressionGameData &requireRegressionGameData()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    return OpenYAMM::Tests::regressionGameData();
}

bool runtimeItemIsIdentified(
    const OpenYAMM::Game::EquippedItemRuntimeState &runtimeState,
    uint32_t equippedItemId)
{
    return equippedItemId == 0 || runtimeState.identified;
}

bool characterHasAnyEquippedItem(const OpenYAMM::Game::Character &character)
{
    return character.equipment.mainHand != 0
        || character.equipment.offHand != 0
        || character.equipment.bow != 0
        || character.equipment.armor != 0
        || character.equipment.helm != 0
        || character.equipment.belt != 0
        || character.equipment.cloak != 0
        || character.equipment.gauntlets != 0
        || character.equipment.boots != 0
        || character.equipment.amulet != 0
        || character.equipment.ring1 != 0
        || character.equipment.ring2 != 0
        || character.equipment.ring3 != 0
        || character.equipment.ring4 != 0
        || character.equipment.ring5 != 0
        || character.equipment.ring6 != 0;
}

bool characterHasItem(const OpenYAMM::Game::Character &character, uint32_t itemId)
{
    if (itemId == 0)
    {
        return false;
    }

    for (const OpenYAMM::Game::InventoryItem &item : character.inventory)
    {
        if (item.objectDescriptionId == itemId)
        {
            return true;
        }
    }

    return character.equipment.mainHand == itemId
        || character.equipment.offHand == itemId
        || character.equipment.bow == itemId
        || character.equipment.armor == itemId
        || character.equipment.helm == itemId
        || character.equipment.belt == itemId
        || character.equipment.cloak == itemId
        || character.equipment.gauntlets == itemId
        || character.equipment.boots == itemId
        || character.equipment.amulet == itemId
        || character.equipment.ring1 == itemId
        || character.equipment.ring2 == itemId
        || character.equipment.ring3 == itemId
        || character.equipment.ring4 == itemId
        || character.equipment.ring5 == itemId
        || character.equipment.ring6 == itemId;
}

std::string readSourceTextFile(const std::filesystem::path &path)
{
    std::ifstream stream(path);
    REQUIRE(stream.is_open());

    std::ostringstream buffer;
    buffer << stream.rdbuf();
    return buffer.str();
}

std::vector<uint8_t> readSourceBinaryFile(const std::filesystem::path &path)
{
    std::ifstream stream(path, std::ios::binary);
    REQUIRE(stream.good());

    return std::vector<uint8_t>(
        std::istreambuf_iterator<char>(stream),
        std::istreambuf_iterator<char>());
}

uint64_t fnv1a64(const std::vector<uint8_t> &bytes)
{
    uint64_t hash = 14695981039346656037ull;

    for (uint8_t byte : bytes)
    {
        hash ^= byte;
        hash *= 1099511628211ull;
    }

    return hash;
}

OpenYAMM::Game::SpriteFrameTable loadCommonSpriteFrameTable()
{
    const std::string yamlText =
        readSourceTextFile(
            std::filesystem::path(OPENYAMM_SOURCE_DIR)
            / "assets_dev/engine/rendering/sprite_frame_data_common.yml");

    OpenYAMM::Game::SpriteFrameTable spriteFrameTable;
    std::string errorMessage;
    REQUIRE(spriteFrameTable.loadFromYaml(yamlText, errorMessage, false));

    return spriteFrameTable;
}

std::string lowercaseFileName(const std::filesystem::path &path)
{
    std::string name = path.filename().string();
    for (char &character : name)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }
    return name;
}

void checkFirstSpriteFrameTexture(
    const OpenYAMM::Game::SpriteFrameTable &spriteFrameTable,
    const std::string &spriteName,
    const std::string &expectedTextureName,
    const std::string &expectedAssetFileName)
{
    const std::optional<uint16_t> spriteFrameIndex = spriteFrameTable.findFrameIndexBySpriteName(spriteName);
    REQUIRE(spriteFrameIndex.has_value());

    const OpenYAMM::Game::SpriteFrameEntry *pFrame = spriteFrameTable.getFrame(*spriteFrameIndex, 0);
    REQUIRE(pFrame != nullptr);

    const OpenYAMM::Game::ResolvedSpriteTexture texture = OpenYAMM::Game::SpriteFrameTable::resolveTexture(*pFrame, 0);
    CHECK_EQ(texture.textureName, expectedTextureName);
    CHECK(std::filesystem::exists(
        std::filesystem::path(OPENYAMM_SOURCE_DIR)
        / "assets_dev/engine/sprites"
        / expectedAssetFileName));
}
}

TEST_CASE("settings debug startup options round trip")
{
    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / "openyamm_debug_god_lich_settings.ini";

    OpenYAMM::Game::GameSettings settings = OpenYAMM::Game::GameSettings::createDefault();
    settings.startWorldId = "mm7";
    settings.startMapFile.clear();
    settings.newGameGodLich = true;

    std::string error;
    REQUIRE(OpenYAMM::Game::saveGameSettings(path, settings, error));

    const std::optional<OpenYAMM::Game::GameSettings> loadedSettings =
        OpenYAMM::Game::loadGameSettings(path, error);

    REQUIRE(loadedSettings.has_value());
    CHECK_EQ(loadedSettings->startWorldId, "mm7");
    CHECK(loadedSettings->startMapFile.empty());
    CHECK(loadedSettings->newGameGodLich);

    std::filesystem::remove(path);
}

TEST_CASE("house data magic guild types are explicit")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    const OpenYAMM::Game::HouseEntry *pElementalGuild = gameData.houseTable.get(139);
    const OpenYAMM::Game::HouseEntry *pLightGuild = gameData.houseTable.get(170);
    const OpenYAMM::Game::HouseEntry *pDarkGuild = gameData.houseTable.get(175);

    REQUIRE(pElementalGuild != nullptr);
    REQUIRE(pLightGuild != nullptr);
    REQUIRE(pDarkGuild != nullptr);

    CHECK_EQ(pElementalGuild->type, "Air Guild");
    CHECK_EQ(pLightGuild->type, "Light Guild");
    CHECK_EQ(pDarkGuild->type, "Dark Guild");
}

TEST_CASE("mmerge house movie metadata drives videos and proprietor portraits")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    const OpenYAMM::Game::HouseEntry *pMm8Temple = gameData.houseTable.get(303);
    const OpenYAMM::Game::HouseEntry *pMm7WeaponShop = gameData.houseTable.get(11);
    const OpenYAMM::Game::HouseEntry *pMm7DungeonEntrance = gameData.houseTable.get(399);

    REQUIRE(pMm8Temple != nullptr);
    REQUIRE(pMm7WeaponShop != nullptr);
    REQUIRE(pMm7DungeonEntrance != nullptr);

    CHECK_EQ(pMm8Temple->mapId, 1u);
    CHECK_EQ(pMm8Temple->videoName, "ltemple");
    CHECK_EQ(pMm8Temple->proprietorPictureId, 1130u);
    CHECK_EQ(pMm7WeaponShop->mapId, 65u);
    CHECK(pMm7WeaponShop->videoName.empty());
    CHECK_EQ(pMm7WeaponShop->proprietorPictureId, 527u);
    CHECK(pMm7DungeonEntrance->videoName.empty());

    const std::filesystem::path assetRoot = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev";
    const std::filesystem::path engineRoot = assetRoot / "engine";
    const std::filesystem::path mm7WorldRoot = assetRoot / "worlds/mm7";
    const std::filesystem::path mm8WorldRoot = assetRoot / "worlds/mm8";
    CHECK(std::filesystem::exists(mm7WorldRoot / "icons" / "npc0527.bmp"));
    CHECK(std::filesystem::exists(engineRoot / "icons" / "npc1582.bmp"));
    CHECK(std::filesystem::exists(mm8WorldRoot / "videos/Houses/ltemple.ogv"));
    CHECK_FALSE(std::filesystem::exists(engineRoot / "videos"));
    CHECK(std::filesystem::exists(mm8WorldRoot / "icons/npc1465.bmp"));
    CHECK(std::filesystem::exists(mm8WorldRoot / "icons/npc1325.bmp"));
}

TEST_CASE("outdoor minimap icons are world-owned")
{
    const std::filesystem::path assetRoot = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev";
    const std::filesystem::path engineIcons = assetRoot / "engine/icons";
    const std::filesystem::path mm6Icons = assetRoot / "worlds/mm6/icons";
    const std::filesystem::path mm7Icons = assetRoot / "worlds/mm7/icons";
    const std::filesystem::path mm8Icons = assetRoot / "worlds/mm8/icons";

    const std::pair<std::filesystem::path, const char *> expectedWorldIcons[] = {
        {mm6Icons, "outc1.bmp"},
        {mm6Icons, "6outside.bmp"},
        {mm7Icons, "7out15.bmp"},
        {mm7Icons, "out14.bmp"},
        {mm8Icons, "out06.bmp"},
        {mm8Icons, "out13.bmp"},
        {mm8Icons, "elema.bmp"},
        {mm8Icons, "pbp.bmp"},
        {mm8Icons, "outside.bmp"},
    };

    for (const std::pair<std::filesystem::path, const char *> &entry : expectedWorldIcons)
    {
        const std::filesystem::path iconPath = entry.first / entry.second;
        CHECK(std::filesystem::exists(iconPath));
        CHECK_EQ(
            std::filesystem::status(iconPath).permissions() & std::filesystem::perms::all,
            std::filesystem::perms::owner_read
                | std::filesystem::perms::owner_write
                | std::filesystem::perms::group_read
                | std::filesystem::perms::others_read);
    }

    const char *engineForbiddenIcons[] = {
        "out06.bmp",
        "out13.bmp",
        "outc1.bmp",
        "7out15.bmp",
        "elema.bmp",
        "pbp.bmp",
        "outside.bmp",
        "6outside.bmp",
        "7outside.bmp",
    };

    for (const char *iconName : engineForbiddenIcons)
    {
        CHECK_FALSE(std::filesystem::exists(engineIcons / iconName));
    }
}

TEST_CASE("mm8 icons do not duplicate engine-owned icons")
{
    const std::filesystem::path assetRoot = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev";
    const std::filesystem::path engineIcons = assetRoot / "engine/icons";
    const std::filesystem::path mm8Icons = assetRoot / "worlds/mm8/icons";

    std::set<std::string> engineIconNames;
    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(engineIcons))
    {
        if (entry.is_regular_file())
        {
            engineIconNames.insert(lowercaseFileName(entry.path()));
        }
    }

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(mm8Icons))
    {
        if (!entry.is_regular_file())
        {
            continue;
        }

        CHECK_FALSE(engineIconNames.contains(lowercaseFileName(entry.path())));
    }
}

TEST_CASE("mm8 screen backgrounds remain the engine defaults")
{
    const std::filesystem::path engineIcons =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/icons";

    struct ExpectedBackground
    {
        const char *fileName;
        uintmax_t fileSize;
        uint64_t fnvHash;
    };

    const ExpectedBackground expectedBackgrounds[] = {
        {"title.pcx", 826904u, 0xacb405aa6d8fa528ull},
        {"makeme.pcx", 712504u, 0x00f643e26313af10ull},
        {"restmain.bmp", 235318u, 0x31067b73f0375f04ull},
    };

    for (const ExpectedBackground &expectedBackground : expectedBackgrounds)
    {
        const std::filesystem::path path = engineIcons / expectedBackground.fileName;
        REQUIRE(std::filesystem::exists(path));
        CHECK_EQ(std::filesystem::file_size(path), expectedBackground.fileSize);
        CHECK_EQ(fnv1a64(readSourceBinaryFile(path)), expectedBackground.fnvHash);
        CHECK_EQ(
            std::filesystem::status(path).permissions() & std::filesystem::perms::all,
            std::filesystem::perms::owner_read
                | std::filesystem::perms::owner_write
                | std::filesystem::perms::group_read
                | std::filesystem::perms::others_read);
    }
}

TEST_CASE("monster spell descriptors preserve skill mastery and level")
{
    OpenYAMM::Game::MonsterTable monsterTable;
    std::vector<std::string> row(37, "0");
    row[0] = "999";
    row[1] = "Test Caster";
    row[2] = "test caster";
    row[3] = "12";
    row[4] = "40";
    row[5] = "3";
    row[12] = "2";
    row[13] = "200";
    row[14] = "80";
    row[24] = "35";
    row[25] = "Lightning Bolt,M,7";
    row[26] = "45";
    row[27] = "Fireball,G,9";

    REQUIRE(monsterTable.loadStatsFromRows({row}));

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(999);
    REQUIRE(pStats != nullptr);
    CHECK_EQ(pStats->spell1Name, "lightning bolt");
    CHECK_EQ(pStats->spell1SkillMastery, OpenYAMM::Game::SkillMastery::Master);
    CHECK_EQ(pStats->spell1SkillLevel, 7u);
    CHECK_EQ(pStats->spell2Name, "fireball");
    CHECK_EQ(pStats->spell2SkillMastery, OpenYAMM::Game::SkillMastery::Grandmaster);
    CHECK_EQ(pStats->spell2SkillLevel, 9u);
}

TEST_CASE("monster hostility table follows merged MMerge party relations")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    CHECK_FALSE(gameData.monsterTable.isHostileToParty(49));
    CHECK_FALSE(gameData.monsterTable.isHostileToParty(52));
    CHECK(gameData.monsterTable.isHostileToParty(73));
    CHECK(gameData.monsterTable.isHostileToParty(74));
    CHECK(gameData.monsterTable.isHostileToParty(75));
}

TEST_CASE("harm projectile sprite resolves to an existing billboard texture")
{
    const OpenYAMM::Game::SpriteFrameTable spriteFrameTable = loadCommonSpriteFrameTable();

    checkFirstSpriteFrameTexture(spriteFrameTable, "spell70", "spell70b10", "Spell70b10.bmp");
}

TEST_CASE("light bolt sprites resolve to existing billboard textures")
{
    const OpenYAMM::Game::SpriteFrameTable spriteFrameTable = loadCommonSpriteFrameTable();

    checkFirstSpriteFrameTexture(spriteFrameTable, "spell78b", "sp78b", "sp78b.bmp");
    checkFirstSpriteFrameTexture(spriteFrameTable, "spell78c", "sp78c", "sp78c.bmp");
}

TEST_CASE("directional sprite bases resolve with an octant suffix")
{
    OpenYAMM::Game::SpriteFrameEntry frame;
    frame.textureName = "pfemsta";
    frame.flags =
        static_cast<uint32_t>(OpenYAMM::Game::SpriteFrameFlag::First)
        | static_cast<uint32_t>(OpenYAMM::Game::SpriteFrameFlag::Mirror5)
        | static_cast<uint32_t>(OpenYAMM::Game::SpriteFrameFlag::Mirror6)
        | static_cast<uint32_t>(OpenYAMM::Game::SpriteFrameFlag::Mirror7);

    OpenYAMM::Game::ResolvedSpriteTexture frontTexture =
        OpenYAMM::Game::SpriteFrameTable::resolveTexture(frame, 0);
    OpenYAMM::Game::ResolvedSpriteTexture sideTexture =
        OpenYAMM::Game::SpriteFrameTable::resolveTexture(frame, 3);
    OpenYAMM::Game::ResolvedSpriteTexture mirroredSideTexture =
        OpenYAMM::Game::SpriteFrameTable::resolveTexture(frame, 5);

    CHECK_EQ(frontTexture.textureName, "pfemsta0");
    CHECK_FALSE(frontTexture.mirrored);
    CHECK_EQ(sideTexture.textureName, "pfemsta3");
    CHECK_FALSE(sideTexture.mirrored);
    CHECK_EQ(mirroredSideTexture.textureName, "pfemsta3");
    CHECK(mirroredSideTexture.mirrored);
}

TEST_CASE("already resolved directional texture names are preserved")
{
    OpenYAMM::Game::SpriteFrameEntry frame;
    frame.textureName = "m528aa0";
    frame.flags = static_cast<uint32_t>(OpenYAMM::Game::SpriteFrameFlag::First);

    OpenYAMM::Game::ResolvedSpriteTexture texture =
        OpenYAMM::Game::SpriteFrameTable::resolveTexture(frame, 2);

    CHECK_EQ(texture.textureName, "m528aa0");
}

TEST_CASE("roster join offer mapping samples")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    struct ExpectedRosterJoinOffer
    {
        uint32_t topicId = 0;
        uint32_t rosterId = 0;
        uint32_t inviteTextId = 0;
        uint32_t partyFullTextId = 0;
    };

    const std::array<ExpectedRosterJoinOffer, 9> expectedOffers = {{
        {602, 2, 202, 203},
        {604, 4, 206, 207},
        {606, 6, 210, 211},
        {611, 11, 220, 221},
        {627, 27, 252, 253},
        {630, 30, 258, 259},
        {632, 32, 262, 263},
        {634, 34, 266, 267},
        {635, 35, 268, 269},
    }};

    for (const ExpectedRosterJoinOffer &expectedOffer : expectedOffers)
    {
        const std::optional<OpenYAMM::Game::NpcDialogTable::RosterJoinOffer> actualOffer =
            gameData.npcDialogTable.getRosterJoinOfferForTopic(expectedOffer.topicId);

        REQUIRE(actualOffer.has_value());
        CHECK_EQ(actualOffer->rosterId, expectedOffer.rosterId);
        CHECK_EQ(actualOffer->inviteTextId, expectedOffer.inviteTextId);
        CHECK_EQ(actualOffer->partyFullTextId, expectedOffer.partyFullTextId);
    }

    CHECK_FALSE(gameData.npcDialogTable.getRosterJoinOfferForTopic(600).has_value());
    CHECK_FALSE(gameData.npcDialogTable.getRosterJoinOfferForTopic(650).has_value());
}

TEST_CASE("recruit roster member loads birth experience resistances and items")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::RosterEntry *pRosterEntry = gameData.rosterTable.get(3);
    const OpenYAMM::Game::RosterEntry *pBlazenRosterEntry = gameData.rosterTable.get(35);

    REQUIRE(pRosterEntry != nullptr);
    REQUIRE(pBlazenRosterEntry != nullptr);
    CHECK_EQ(pRosterEntry->unlockQuestBitId, 403u);
    CHECK_EQ(pBlazenRosterEntry->unlockQuestBitId, 435u);

    OpenYAMM::Game::Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.setItemEnchantTables(&gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable);

    REQUIRE(party.recruitRosterMember(*pRosterEntry));

    const OpenYAMM::Game::Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    CHECK_EQ(pMember->birthYear, pRosterEntry->birthYear);
    CHECK_EQ(pMember->experience, pRosterEntry->experience);
    CHECK_EQ(pMember->baseResistances.fire, pRosterEntry->baseResistances.fire);
    CHECK_EQ(pMember->baseResistances.body, pRosterEntry->baseResistances.body);
    CHECK((!pMember->inventory.empty() || characterHasAnyEquippedItem(*pMember)));

    for (const OpenYAMM::Game::InventoryItem &item : pMember->inventory)
    {
        CHECK(item.identified);
    }

    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.mainHand, pMember->equipment.mainHand));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.offHand, pMember->equipment.offHand));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.bow, pMember->equipment.bow));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.armor, pMember->equipment.armor));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.helm, pMember->equipment.helm));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.belt, pMember->equipment.belt));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.cloak, pMember->equipment.cloak));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.gauntlets, pMember->equipment.gauntlets));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.boots, pMember->equipment.boots));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.amulet, pMember->equipment.amulet));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring1, pMember->equipment.ring1));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring2, pMember->equipment.ring2));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring3, pMember->equipment.ring3));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring4, pMember->equipment.ring4));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring5, pMember->equipment.ring5));
    CHECK(runtimeItemIsIdentified(pMember->equipmentRuntime.ring6, pMember->equipment.ring6));

    for (uint32_t itemId : pRosterEntry->startingInventoryItemIds)
    {
        CHECK(characterHasItem(*pMember, itemId));
    }

    REQUIRE_FALSE(pBlazenRosterEntry->startingItems.empty());
    CHECK_EQ(pBlazenRosterEntry->startingItems[0].rawValue, 5005u);
    CHECK_EQ(pBlazenRosterEntry->startingItems[0].itemId, 5u);
    CHECK_EQ(pBlazenRosterEntry->startingItems[0].enchantmentLevel, 5u);

    OpenYAMM::Game::Party blazenParty = {};
    blazenParty.setItemTable(&gameData.itemTable);
    blazenParty.setItemEnchantTables(&gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable);

    REQUIRE(blazenParty.recruitRosterMember(*pBlazenRosterEntry));

    const OpenYAMM::Game::Character *pBlazen = blazenParty.member(0);
    REQUIRE(pBlazen != nullptr);
    CHECK(characterHasAnyEquippedItem(*pBlazen));

    for (uint32_t itemId : pBlazenRosterEntry->startingInventoryItemIds)
    {
        CHECK(characterHasItem(*pBlazen, itemId));
    }
}
