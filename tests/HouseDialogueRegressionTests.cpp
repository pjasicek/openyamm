#include "doctest/doctest.h"

#include "game/audio/SoundIds.h"
#include "game/events/EvtEnums.h"
#include "game/events/ISceneEventContext.h"
#include "game/gameplay/GenericActorDialog.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/HouseServiceRuntime.h"
#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/items/PriceCalculator.h"
#include "game/maps/SaveGame.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SpellIds.h"
#include "game/tables/MapStats.h"
#include "game/tables/MergedBaseTables.h"

#include "tests/HouseDialogueTestHarness.h"
#include "tests/RegressionGameData.h"

#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <optional>
#include <string>
#include <utility>
#include <unordered_map>
#include <vector>

namespace
{
constexpr uint32_t TempleHouseId = 303;
constexpr uint32_t NewSorpigalTempleHouseId = 325;
constexpr uint32_t FreeHavenTempleStoneHouseId = 326;
constexpr uint32_t BlackshireTempleHouseId = 327;
constexpr uint32_t FreeHavenTempleHouseId = 1442;
constexpr uint32_t ElementalGuildHouseId = 139;
constexpr uint32_t TrainingHallHouseId = 1564;
constexpr uint32_t BankHouseId = 281;
constexpr uint32_t AdventurersInnHouseId = 756;
constexpr uint32_t ServiceTavernWithResidentHouseId = 260;
constexpr uint32_t DaggerWoundTavernHouseId = 228;
constexpr uint32_t BullsEyeInnHouseId = 235;
constexpr uint32_t HarmondaleTavernHouseId = 240;
constexpr uint32_t ArcomageDeckItemId = 1453;
constexpr uint32_t WindlingBoatHouseId = 479;
constexpr uint32_t SmokeBoatHouseId = 481;
constexpr uint32_t WindBoatHouseId = 483;
constexpr uint32_t NewSorpigalStableHouseId = 470;
constexpr uint32_t NewSorpigalBoatHouseId = 496;
constexpr uint32_t BuccaneersLairHouseId = 191;

class TempleConditionTimeSceneContext : public OpenYAMM::Game::ISceneEventContext
{
public:
    explicit TempleConditionTimeSceneContext(float currentGameMinutes)
        : m_currentGameMinutes(currentGameMinutes)
    {
    }

    float currentGameMinutes() const override
    {
        return m_currentGameMinutes;
    }

    const OpenYAMM::Game::MapDeltaData *mapDeltaData() const override
    {
        return nullptr;
    }

    OpenYAMM::Game::MapDeltaData *mapDeltaData() override
    {
        return nullptr;
    }

    bool setFacetBit(uint32_t cogNumber, uint32_t bit, bool isOn) override
    {
        (void)cogNumber;
        (void)bit;
        (void)isOn;
        return false;
    }

    bool castEventSpell(
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        int32_t fromX,
        int32_t fromY,
        int32_t fromZ,
        int32_t toX,
        int32_t toY,
        int32_t toZ) override
    {
        (void)spellId;
        (void)skillLevel;
        (void)skillMastery;
        (void)fromX;
        (void)fromY;
        (void)fromZ;
        (void)toX;
        (void)toY;
        (void)toZ;
        return false;
    }

    bool summonMonsters(
        uint32_t typeIndexInMapStats,
        uint32_t level,
        uint32_t count,
        int32_t x,
        int32_t y,
        int32_t z,
        uint32_t group,
        uint32_t uniqueNameId) override
    {
        (void)typeIndexInMapStats;
        (void)level;
        (void)count;
        (void)x;
        (void)y;
        (void)z;
        (void)group;
        (void)uniqueNameId;
        return false;
    }

    bool summonEventItem(
        uint32_t itemId,
        int32_t x,
        int32_t y,
        int32_t z,
        int32_t speed,
        uint32_t count,
        bool randomRotate) override
    {
        (void)itemId;
        (void)x;
        (void)y;
        (void)z;
        (void)speed;
        (void)count;
        (void)randomRotate;
        return false;
    }

    bool checkMonstersKilled(uint32_t checkType, uint32_t id, uint32_t count, bool invisibleAsDead) const override
    {
        (void)checkType;
        (void)id;
        (void)count;
        (void)invisibleAsDead;
        return false;
    }

private:
    float m_currentGameMinutes = 0.0f;
};
constexpr uint32_t BerserkersFuryHouseId = 199;
constexpr uint32_t BrekishHallHouseId = 212;
constexpr uint32_t FreeHavenHighCouncilHouseId = 209;
constexpr uint32_t OracleHouseId = 451;
constexpr uint32_t ElgarFellmoonHouseId = 354;
constexpr uint32_t SandroThantThroneRoomHouseId = 213;
constexpr uint32_t FredrickHouseId = 866;
constexpr uint32_t HissHouseId = 761;
constexpr uint32_t OverduneHouseId = 752;
constexpr uint32_t FreeHavenSewerEntranceHouseId = 1532;
constexpr uint32_t MasterIdentifyItemTeacherNpcId = 200;
constexpr uint32_t CarolynWeathersNpcId = 348;
constexpr uint32_t HaroldHessNpcId = 818;
constexpr uint32_t TessTuckerNpcId = 835;
constexpr uint32_t BufordAllmanNpcId = 992;
constexpr uint32_t AbdulaiMahgrebNpcId = 1010;
constexpr uint32_t KevinWatchPeasantNpcId = 977;
constexpr uint32_t ChitaniaRetianiNpcId = 1011;
constexpr uint32_t ChitaniaRetianiHouseId = 1513;
constexpr uint32_t JoHandlebaumSpellMasterNpcId = 979;
constexpr uint32_t JoHandlebaumSpellMasterHouseId = 1377;
constexpr uint32_t GingerAstorTeacherNpcId = 888;
constexpr uint32_t GingerAstorTeacherHouseId = 1514;
constexpr uint32_t NoahWhiteInstructorNpcId = 815;
constexpr uint32_t NoahWhiteInstructorHouseId = 1366;
constexpr uint32_t KernCarnegieArmsMasterNpcId = 987;
constexpr uint32_t KernCarnegieArmsMasterHouseId = 1333;
constexpr uint32_t MiriamBoyerWeaponsMasterNpcId = 1050;
constexpr uint32_t MiriamBoyerWeaponsMasterHouseId = 1444;
constexpr uint32_t IrisPoppyfieldNpcId = 971;
constexpr uint32_t WilmaCookGateMasterNpcId = 1035;
constexpr uint32_t NaomiWindNpcId = 1051;
constexpr uint32_t NaomiWindHouseId = 1377;
constexpr uint32_t TorBrockNpcId = 1150;
constexpr uint32_t TorBrockHouseId = 1553;
constexpr uint32_t PaulHapsburgNpcId = 1164;
constexpr uint32_t BardProfessionId = 36;
constexpr uint32_t PotterProfessionId = 58;
constexpr uint32_t TeacherProfessionId = 13;
constexpr uint32_t InstructorProfessionId = 14;
constexpr uint32_t ArmsMasterProfessionId = 15;
constexpr uint32_t WeaponsMasterProfessionId = 16;
constexpr uint32_t SpellMasterProfessionId = 19;
constexpr uint32_t WindMasterProfessionId = 39;
constexpr uint32_t WaterMasterProfessionId = 40;
constexpr uint32_t GateMasterProfessionId = 41;
constexpr uint32_t AcolyteProfessionId = 42;
constexpr uint32_t PiperProfessionId = 43;
constexpr uint32_t MasterHealerProfessionId = 12;
constexpr uint32_t StonNpcId = 27;
constexpr uint32_t LawrenceMarkNpcId = 379;
constexpr uint32_t ExpertBlasterNpcId = 558;
constexpr uint32_t HintTeacherNpcId = 633;
constexpr uint32_t SandroNpcId = 9;
constexpr uint32_t ThantNpcId = 10;
constexpr uint32_t RelocatedThantNpcId = 63;
constexpr uint32_t DysonNpcId = 11;
constexpr uint32_t PrestonSteelNpcId = 1084;
constexpr uint32_t ToriGoldmanNpcId = 1085;
constexpr uint32_t IsaacRockwellNpcId = 1086;
constexpr uint32_t OlafHeimdallNpcId = 1087;
constexpr uint32_t EuclidKeplerNpcId = 1088;
constexpr uint32_t SlickerSilvertongueNpcId = 1089;
constexpr uint32_t BrekishOnefangNpcId = 1;
constexpr uint32_t ElgarFellmoonNpcId = 3;
constexpr uint32_t LongTailNpcId = 97;
constexpr uint32_t FredrickNpcId = 28;
constexpr uint32_t SalSharktoothNpcId = 346;
constexpr uint32_t DysonDirectNpcId = 295;
constexpr uint32_t BlazenQuestNpcId = 107;
constexpr uint32_t BlazenJoinNpcId = 296;
constexpr uint32_t RohaniNpcId = 267;
constexpr uint32_t StephenNpcId = 59;
constexpr uint32_t OverduneNpcId = 7;
constexpr uint32_t AndoverPotbelloNpcId = 786;
constexpr uint32_t BlazenRosterId = 35;
constexpr uint32_t OverduneRosterId = 4;
constexpr uint32_t GemOfRestorationItemId = 623;
constexpr uint32_t WealthyHatItemId = 1433;
constexpr uint32_t SalSharktoothGroupId = 54;

const OpenYAMM::Game::Character *findPartyMemberByRosterId(
    const OpenYAMM::Game::Party &party,
    uint32_t rosterId)
{
    for (const OpenYAMM::Game::Character &member : party.members())
    {
        if (member.rosterId == rosterId)
        {
            return &member;
        }
    }

    return nullptr;
}

bool innEquipmentItemIdentified(
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

const OpenYAMM::Tests::RegressionGameData &requireRegressionGameData()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    return OpenYAMM::Tests::regressionGameData();
}

std::optional<OpenYAMM::Game::ScriptedEventProgram> loadSyntheticMapEventProgram(
    const std::string &body,
    const std::string &chunkName)
{
    std::string luaSourceText = body;
    luaSourceText += "\n";
    luaSourceText += "evt.meta = evt.meta or {}\n";
    luaSourceText += "evt.meta.map = evt.meta.map or {}\n";
    luaSourceText += "evt.meta.map.onLoad = {}\n";
    luaSourceText += "evt.meta.map.hint = {}\n";
    luaSourceText += "evt.meta.map.summary = {}\n";
    luaSourceText += "evt.meta.map.openedChestIds = {}\n";
    luaSourceText += "evt.meta.map.textureNames = {}\n";
    luaSourceText += "evt.meta.map.spriteNames = {}\n";
    luaSourceText += "evt.meta.map.castSpellIds = {}\n";
    luaSourceText += "evt.meta.map.timers = {}\n";

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> program =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            luaSourceText,
            chunkName,
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);
    INFO(error);
    return program;
}

bool dialogContainsText(const OpenYAMM::Game::EventDialogContent &dialog, const std::string &text)
{
    for (const std::string &line : dialog.lines)
    {
        if (line.find(text) != std::string::npos)
        {
            return true;
        }
    }

    return false;
}

bool dialogHasActionLabel(const OpenYAMM::Game::EventDialogContent &dialog, const std::string &label)
{
    for (const OpenYAMM::Game::EventDialogAction &action : dialog.actions)
    {
        if (action.label == label)
        {
            return true;
        }
    }

    return false;
}

bool dialogHasAction(
    const OpenYAMM::Game::EventDialogContent &dialog,
    OpenYAMM::Game::EventDialogActionKind kind,
    const std::string &label)
{
    for (const OpenYAMM::Game::EventDialogAction &action : dialog.actions)
    {
        if (action.kind == kind && action.label == label)
        {
            return true;
        }
    }

    return false;
}

bool portraitFxContainsMember(
    const OpenYAMM::Game::EventRuntimeState &runtimeState,
    OpenYAMM::Game::PortraitFxEventKind kind,
    size_t memberIndex)
{
    for (const OpenYAMM::Game::EventRuntimeState::PortraitFxRequest &request : runtimeState.portraitFxRequests)
    {
        if (request.kind != kind)
        {
            continue;
        }

        if (std::find(request.memberIndices.begin(), request.memberIndices.end(), memberIndex)
            != request.memberIndices.end())
        {
            return true;
        }
    }

    return false;
}

std::optional<size_t> findActionIndexByLabel(
    const OpenYAMM::Game::EventDialogContent &dialog,
    const std::string &label)
{
    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        if (dialog.actions[actionIndex].label == label)
        {
            return actionIndex;
        }
    }

    return std::nullopt;
}

std::optional<size_t> findActionIndexByHouseActionId(
    const OpenYAMM::Game::EventDialogContent &dialog,
    OpenYAMM::Game::HouseActionId actionId)
{
    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        if (dialog.actions[actionIndex].kind == OpenYAMM::Game::EventDialogActionKind::HouseService
            && dialog.actions[actionIndex].id == static_cast<uint32_t>(actionId))
        {
            return actionIndex;
        }
    }

    return std::nullopt;
}

size_t actionLabelCount(const OpenYAMM::Game::EventDialogContent &dialog, const std::string &label)
{
    return static_cast<size_t>(std::count_if(
        dialog.actions.begin(),
        dialog.actions.end(),
        [&label](const OpenYAMM::Game::EventDialogAction &action)
        {
            return action.label == label;
        }));
}

bool houseActionsContainDestination(
    const std::vector<OpenYAMM::Game::HouseActionOption> &actions,
    const std::string &destination)
{
    for (const OpenYAMM::Game::HouseActionOption &action : actions)
    {
        if (action.label.find(destination) != std::string::npos)
        {
            return true;
        }
    }

    return false;
}

std::optional<OpenYAMM::Game::HouseActionOption> findHouseActionById(
    const std::vector<OpenYAMM::Game::HouseActionOption> &actions,
    OpenYAMM::Game::HouseActionId actionId)
{
    for (const OpenYAMM::Game::HouseActionOption &action : actions)
    {
        if (action.id == actionId)
        {
            return action;
        }
    }

    return std::nullopt;
}

std::optional<size_t> findActionIndexByLabelPrefix(
    const OpenYAMM::Game::EventDialogContent &dialog,
    const std::string &labelPrefix)
{
    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        if (dialog.actions[actionIndex].label.rfind(labelPrefix, 0) == 0)
        {
            return actionIndex;
        }
    }

    return std::nullopt;
}

std::vector<std::string> collectActionLabels(const OpenYAMM::Game::EventDialogContent &dialog)
{
    std::vector<std::string> labels;

    for (const OpenYAMM::Game::EventDialogAction &action : dialog.actions)
    {
        labels.push_back(action.label);
    }

    return labels;
}

void checkJoinableProfessionNewsDialog(
    OpenYAMM::Tests::HouseDialogueTestHarness &harness,
    const OpenYAMM::Tests::RegressionGameData &gameData,
    uint32_t npcId,
    uint32_t houseId,
    uint32_t professionId,
    const std::string &newsLabel)
{
    const OpenYAMM::Game::NpcEntry *pNpc = gameData.npcDialogTable.getNpc(npcId);
    REQUIRE(pNpc != nullptr);
    CHECK_EQ(pNpc->professionId, professionId);
    CHECK(pNpc->joins);

    const OpenYAMM::Game::MergedNpcProfessionEntry *pProfession =
        gameData.mergedNpcProfessionTable.get(professionId);
    REQUIRE(pProfession != nullptr);

    const OpenYAMM::Game::EventDialogContent dialog = harness.openNpcDialogue(npcId, houseId);
    CHECK(findActionIndexByLabel(dialog, "Join").has_value());
    CHECK(findActionIndexByLabel(dialog, "More Info").has_value());
    CHECK(dialogHasAction(dialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionNews, newsLabel));
    CHECK_FALSE(
        dialogHasAction(dialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionAction, pProfession->profession));
}

int firstTreasureLevelForItem(const OpenYAMM::Game::ItemDefinition &itemDefinition)
{
    for (size_t tierIndex = 0; tierIndex < itemDefinition.randomTreasureWeights.size(); ++tierIndex)
    {
        if (itemDefinition.randomTreasureWeights[tierIndex] > 0)
        {
            return static_cast<int>(tierIndex) + 1;
        }
    }

    return 0;
}

bool itemHasTreasureWeightAtOrAboveTier(const OpenYAMM::Game::ItemDefinition &itemDefinition, int tier)
{
    const int startTier = std::clamp(tier, 1, static_cast<int>(itemDefinition.randomTreasureWeights.size())) - 1;

    for (size_t tierIndex = static_cast<size_t>(startTier); tierIndex < itemDefinition.randomTreasureWeights.size();
         ++tierIndex)
    {
        if (itemDefinition.randomTreasureWeights[tierIndex] > 0)
        {
            return true;
        }
    }

    return false;
}

OpenYAMM::Game::CharacterSkill *setCharacterSkill(
    OpenYAMM::Game::Character &character,
    const std::string &skillName,
    uint32_t level,
    OpenYAMM::Game::SkillMastery mastery)
{
    character.skills[skillName] = {skillName, level, mastery};
    return character.findSkill(skillName);
}

OpenYAMM::Game::EventRuntimeState::DialogueOfferState makeRosterJoinOffer(
    uint32_t npcId,
    uint32_t rosterId,
    uint32_t messageTextId,
    uint32_t partyFullTextId)
{
    OpenYAMM::Game::EventRuntimeState::DialogueOfferState invite = {};
    invite.kind = OpenYAMM::Game::DialogueOfferKind::RosterJoin;
    invite.npcId = npcId;
    invite.rosterId = rosterId;
    invite.messageTextId = messageTextId;
    invite.partyFullTextId = partyFullTextId;
    return invite;
}

void advanceBrekishQuest(OpenYAMM::Tests::HouseDialogueTestHarness &harness)
{
    const OpenYAMM::Game::EventDialogContent &hallDialog = harness.openHouseDialog(BrekishHallHouseId);
    const std::optional<size_t> brekishIndex = findActionIndexByLabel(hallDialog, "Brekish Onefang");

    REQUIRE(brekishIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &brekishDialog = harness.executeAndPresent(*brekishIndex);
    const std::optional<size_t> portalsIndex = findActionIndexByLabel(brekishDialog, "Portals of Stone");

    REQUIRE(portalsIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &portalsDialog = harness.executeAndPresent(*portalsIndex);
    const std::optional<size_t> questIndex = findActionIndexByLabel(portalsDialog, "Quest");

    REQUIRE(questIndex.has_value());
    harness.executeAndPresent(*questIndex);
}

std::vector<uint8_t> readBinaryFileBytes(const std::filesystem::path &path)
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
}

TEST_CASE("generic actor dialog resolves lizardman portraits")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::EventRuntimeState runtimeState = {};

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> villagerResolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "out01.odm",
            "Lizardman Villager",
            1,
            runtimeState,
            gameData.npcDialogTable);
    REQUIRE(villagerResolution.has_value());
    CHECK_EQ(villagerResolution->npcId, 328u);
    const OpenYAMM::Game::NpcEntry *pVillagerNpc = gameData.npcDialogTable.getNpc(villagerResolution->npcId);
    REQUIRE(pVillagerNpc != nullptr);
    CHECK_EQ(pVillagerNpc->pictureId, 1487u);

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> soldierResolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "out01.odm",
            "Lizardman Soldier",
            2,
            runtimeState,
            gameData.npcDialogTable);
    REQUIRE(soldierResolution.has_value());
    CHECK_EQ(soldierResolution->npcId, 329u);
    const OpenYAMM::Game::NpcEntry *pSoldierNpc = gameData.npcDialogTable.getNpc(soldierResolution->npcId);
    REQUIRE(pSoldierNpc != nullptr);
    CHECK_EQ(pSoldierNpc->pictureId, 1475u);

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> guardResolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "out01.odm",
            "Guard",
            9,
            runtimeState,
            gameData.npcDialogTable);
    REQUIRE(guardResolution.has_value());
    CHECK_EQ(guardResolution->npcId, 329u);
}

TEST_CASE("mm8 house NPC dialogs use merged NPCData portrait ids")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::NpcEntry *pBrekish = gameData.npcDialogTable.getNpc(BrekishOnefangNpcId);
    const OpenYAMM::Game::NpcEntry *pSton = gameData.npcDialogTable.getNpc(StonNpcId);
    const OpenYAMM::Game::NpcEntry *pElgar = gameData.npcDialogTable.getNpc(ElgarFellmoonNpcId);
    REQUIRE(pBrekish != nullptr);
    REQUIRE(pSton != nullptr);
    REQUIRE(pElgar != nullptr);
    CHECK_EQ(pBrekish->pictureId, 1465u);
    CHECK_EQ(pSton->pictureId, 1477u);
    CHECK_EQ(pElgar->pictureId, 1438u);

    const OpenYAMM::Game::EventDialogContent &brekishDialog =
        harness.openNpcDialogue(BrekishOnefangNpcId, BrekishHallHouseId);
    CHECK_EQ(brekishDialog.title, "Brekish Onefang");
    CHECK_EQ(brekishDialog.participantPictureId, 1465u);

    const OpenYAMM::Game::EventDialogContent &stonDialog = harness.openNpcDialogue(StonNpcId);
    CHECK_EQ(stonDialog.title, "S'ton");
    CHECK_EQ(stonDialog.participantPictureId, 1477u);
    CHECK(dialogHasActionLabel(stonDialog, "Cataclysm"));
    CHECK(dialogHasActionLabel(stonDialog, "Caravan Master"));
    CHECK(dialogHasActionLabel(stonDialog, "Pirates of Regna"));

    const OpenYAMM::Game::EventDialogContent &elgarDialog =
        harness.openNpcDialogue(ElgarFellmoonNpcId, ElgarFellmoonHouseId);
    CHECK_EQ(elgarDialog.title, "Elgar Fellmoon");
    CHECK_EQ(elgarDialog.participantPictureId, 1438u);
}

TEST_CASE("ravenshore dark elf peasants use merged generic NPC portrait")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> resolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "out02.odm",
            "Dark Elf Peasant",
            5,
            harness.eventRuntimeState(),
            gameData.npcDialogTable);
    REQUIRE(resolution.has_value());
    CHECK_EQ(resolution->npcId, 330u);

    const OpenYAMM::Game::NpcEntry *pNpc = gameData.npcDialogTable.getNpc(resolution->npcId);
    REQUIRE(pNpc != nullptr);
    CHECK_EQ(pNpc->name, "Dark Elf Peasant");
    CHECK_EQ(pNpc->pictureId, 1402u);

    const std::optional<std::string> newsText = gameData.npcDialogTable.getNewsText(resolution->newsId);
    REQUIRE(newsText.has_value());

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openNpcNews(resolution->npcId, resolution->newsId, "Dark Elf Peasant", *newsText);

    CHECK_EQ(dialog.title, "Dark Elf Peasant");
    CHECK_EQ(dialog.participantPictureId, 1402u);
}

TEST_CASE("dwi actor peasant news")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> resolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "out01.odm",
            "Lizardman Peasant",
            1,
            harness.eventRuntimeState(),
            gameData.npcDialogTable);
    REQUIRE(resolution.has_value());

    const OpenYAMM::Game::NpcEntry *pNpc = gameData.npcDialogTable.getNpc(resolution->npcId);
    REQUIRE(pNpc != nullptr);
    const std::optional<std::string> newsText = gameData.npcDialogTable.getNewsText(resolution->newsId);
    REQUIRE(newsText.has_value());

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openNpcNews(resolution->npcId, resolution->newsId, "Lizardman Peasant", *newsText);

    CHECK_EQ(dialog.title, "Lizardman Peasant");
    CHECK_EQ(dialog.participantPictureId, 1487u);
    CHECK(dialogContainsText(dialog, "If the pirates make it through our warriors"));
}

TEST_CASE("dwi actor lookout news")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> resolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "out01.odm",
            "Lizardman Lookout",
            9,
            harness.eventRuntimeState(),
            gameData.npcDialogTable);
    REQUIRE(resolution.has_value());

    const OpenYAMM::Game::NpcEntry *pNpc = gameData.npcDialogTable.getNpc(resolution->npcId);
    REQUIRE(pNpc != nullptr);
    const std::optional<std::string> newsText = gameData.npcDialogTable.getNewsText(resolution->newsId);
    REQUIRE(newsText.has_value());

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openNpcNews(resolution->npcId, resolution->newsId, "Lizardman Lookout", *newsText);

    CHECK(dialogContainsText(dialog, "Would you like to fire the cannons"));
}

TEST_CASE("mm6 and mm7 generic peasants fall back from placeholder group news to area topics")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::MergedNewsTopicTable areaNewsTable;
    REQUIRE(areaNewsTable.loadFromRows({
        {"#", "Topic", "Text"},
        {"151", "102", "102"},
        {"62", "788", "987"},
    }));

    OpenYAMM::Game::MapStatsEntry newSorpigal = {};
    newSorpigal.id = 151;
    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> newSorpigalResolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "oute3.odm",
            "Peasant",
            85,
            OpenYAMM::Game::EventRuntimeState{},
            gameData.npcDialogTable,
            nullptr,
            &newSorpigal,
            &areaNewsTable);

    REQUIRE(newSorpigalResolution.has_value());
    CHECK_EQ(newSorpigalResolution->newsId, 102u);
    CHECK(gameData.npcDialogTable.getNewsDialogText(newSorpigalResolution->newsId).has_value());

    OpenYAMM::Game::MapStatsEntry emeraldIsland = {};
    emeraldIsland.id = 62;
    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> emeraldResolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "7out01.odm",
            "Peasant",
            51,
            OpenYAMM::Game::EventRuntimeState{},
            gameData.npcDialogTable,
            nullptr,
            &emeraldIsland,
            &areaNewsTable);

    REQUIRE(emeraldResolution.has_value());
    CHECK_EQ(emeraldResolution->newsId, 987u);
    const std::optional<std::string> emeraldText =
        gameData.npcDialogTable.getNewsDialogText(emeraldResolution->newsId);
    REQUIRE(emeraldText.has_value());
    CHECK(emeraldText->find("Wild Dragonflies") != std::string::npos);
}

TEST_CASE("generic actor news falls back to merged continent topics after area topics")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::MergedNewsTopicTable continentNewsTable;
    REQUIRE(continentNewsTable.loadFromRows({
        {"Continent", "Topic Name", "Text"},
        {"3", "361", "361"},
    }));

    OpenYAMM::Game::MapStatsEntry enrothMap = {};
    enrothMap.id = 151;
    enrothMap.mergedContinentId = 3;

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> resolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "oute3.odm",
            "Peasant",
            85,
            OpenYAMM::Game::EventRuntimeState{},
            gameData.npcDialogTable,
            nullptr,
            &enrothMap,
            nullptr,
            &continentNewsTable);

    REQUIRE(resolution.has_value());
    CHECK_EQ(resolution->newsId, 361u);
    const std::optional<std::string> newsText = gameData.npcDialogTable.getNewsDialogText(resolution->newsId);
    REQUIRE(newsText.has_value());
    CHECK(newsText->find("Sweet Water") != std::string::npos);
}

TEST_CASE("generated generic actors use merged NPC names, professions, and rarity caps")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    OpenYAMM::Game::MapStatsEntry emeraldIsland = {};
    emeraldIsland.id = 62;
    emeraldIsland.fileName = "7out01.odm";
    emeraldIsland.mergedContinentId = 2;

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> resolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "7out01.odm",
            "Peasant",
            51,
            harness.eventRuntimeState(),
            gameData.npcDialogTable,
            nullptr,
            &emeraldIsland,
            nullptr,
            nullptr,
            &gameData.mergedNpcNameTable,
            &gameData.mergedNpcProfessionTable,
            &gameData.mergedBolsterMapTable,
            &gameData.mergedBolsterMonsterTable,
            322,
            4);

    REQUIRE(resolution.has_value());
    CHECK(resolution->opensNpcTalk);
    CHECK(resolution->generatedNpc);
    CHECK_GE(resolution->npcId, 1184u);
    CHECK_LE(resolution->npcId, 1223u);
    CHECK_FALSE(resolution->generatedName.empty());

    const OpenYAMM::Game::MergedNpcProfessionEntry *pProfession =
        gameData.mergedNpcProfessionTable.get(resolution->generatedProfessionId);
    REQUIRE(pProfession != nullptr);
    REQUIRE(pProfession->rarity <= 10u);

    OpenYAMM::Game::applyGenericActorDialogResolution(harness.eventRuntimeState(), *resolution);
    const OpenYAMM::Game::EventDialogContent &dialog = harness.openNpcDialogue(resolution->npcId);

    CHECK_EQ(dialog.title, resolution->generatedName);
    CHECK_FALSE(dialogHasActionLabel(dialog, "Beg"));
    CHECK_FALSE(dialogHasActionLabel(dialog, "Threat"));
    CHECK_FALSE(dialogHasActionLabel(dialog, "Bribe"));

    const std::vector<std::string> labels = collectActionLabels(dialog);
    if (pProfession->joins)
    {
        CHECK(std::find(labels.begin(), labels.end(), "Join") != labels.end());
        CHECK_FALSE(
            dialogHasAction(
                dialog,
                OpenYAMM::Game::EventDialogActionKind::NpcProfessionAction,
                pProfession->profession));
        CHECK_EQ(
            std::find(labels.begin(), labels.end(), "More Info") != labels.end(),
            pProfession->descriptionTextId != 0);
    }
    else
    {
        CHECK(std::find(labels.begin(), labels.end(), pProfession->profession) != labels.end());
    }
}

TEST_CASE("generated generic actors are limited to peasant bolster monsters")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    OpenYAMM::Game::MapStatsEntry emeraldIsland = {};
    emeraldIsland.id = 62;
    emeraldIsland.fileName = "7out01.odm";
    emeraldIsland.mergedContinentId = 2;

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> goblinResolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "7out01.odm",
            "Goblin",
            271,
            OpenYAMM::Game::EventRuntimeState{},
            gameData.npcDialogTable,
            &gameData.mergedMonsterPortraitTable,
            &emeraldIsland,
            nullptr,
            nullptr,
            &gameData.mergedNpcNameTable,
            &gameData.mergedNpcProfessionTable,
            &gameData.mergedBolsterMapTable,
            &gameData.mergedBolsterMonsterTable,
            271,
            4);

    CHECK_FALSE(goblinResolution.has_value());
}

TEST_CASE("generated generic actor names follow MMerge bolster monster gender")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::EventRuntimeState runtimeState = {};

    OpenYAMM::Game::MapStatsEntry emeraldIsland = {};
    emeraldIsland.id = 62;
    emeraldIsland.fileName = "7out01.odm";
    emeraldIsland.mergedContinentId = 2;

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> femaleResolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "7out01.odm",
            "Peasant",
            51,
            runtimeState,
            gameData.npcDialogTable,
            &gameData.mergedMonsterPortraitTable,
            &emeraldIsland,
            nullptr,
            nullptr,
            &gameData.mergedNpcNameTable,
            &gameData.mergedNpcProfessionTable,
            &gameData.mergedBolsterMapTable,
            &gameData.mergedBolsterMonsterTable,
            313,
            4);
    REQUIRE(femaleResolution.has_value());
    CHECK(
        std::find(
            gameData.mergedNpcNameTable.femaleNames().begin(),
            gameData.mergedNpcNameTable.femaleNames().end(),
            femaleResolution->generatedName) != gameData.mergedNpcNameTable.femaleNames().end());
    CHECK(gameData.mergedMonsterPortraitTable.portraitForMonsterId(313, 0).has_value());
    CHECK_NE(femaleResolution->portraitPictureId, 0u);

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> maleResolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "7out01.odm",
            "Peasant",
            51,
            runtimeState,
            gameData.npcDialogTable,
            &gameData.mergedMonsterPortraitTable,
            &emeraldIsland,
            nullptr,
            nullptr,
            &gameData.mergedNpcNameTable,
            &gameData.mergedNpcProfessionTable,
            &gameData.mergedBolsterMapTable,
            &gameData.mergedBolsterMonsterTable,
            322,
            5);
    REQUIRE(maleResolution.has_value());
    CHECK(
        std::find(
            gameData.mergedNpcNameTable.maleNames().begin(),
            gameData.mergedNpcNameTable.maleNames().end(),
            maleResolution->generatedName) != gameData.mergedNpcNameTable.maleNames().end());
    CHECK(gameData.mergedMonsterPortraitTable.portraitForMonsterId(322, 0).has_value());
    CHECK_NE(maleResolution->portraitPictureId, 0u);
}

TEST_CASE("generated follower actor state hides and survives save data round trip")
{
    OpenYAMM::Game::MapStatsEntry emeraldIsland = {};
    emeraldIsland.fileName = "7out01.odm";

    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    runtimeState.generatedNpcIdsByActorKey["7out01.odm#4#51#Peasant"] = 1184;
    runtimeState.npcNameOverrides[1184] = "Aaron";
    runtimeState.npcPictureOverrides[1184] = 123;
    runtimeState.npcProfessionOverrides[1184] = 52;
    runtimeState.unavailableNpcIds.insert(1184);

    OpenYAMM::Game::EventRuntimeState::HiredNpcFollower follower = {};
    follower.npcId = 1184;
    follower.professionId = 52;
    follower.weeklyCost = 300;
    follower.abilityUsedDay = 7;
    runtimeState.hiredNpcFollowers.push_back(follower);

    REQUIRE(OpenYAMM::Game::hideGeneratedNpcActor(runtimeState, 1184, &emeraldIsland));
    const uint32_t invisibleBit = static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Invisible);
    CHECK((runtimeState.actorSetMasks[4] & invisibleBit) != 0);

    OpenYAMM::Game::GameSaveData saveData = {};
    saveData.mapFileName = "7out01.odm";
    saveData.hasOutdoorRuntimeState = true;
    saveData.outdoorWorld.eventRuntimeState = runtimeState;

    const std::filesystem::path savePath =
        std::filesystem::temp_directory_path() / "openyamm_generated_follower_roundtrip.oysav";
    std::string error;
    REQUIRE(OpenYAMM::Game::saveGameDataToPath(savePath, saveData, error));

    const std::optional<OpenYAMM::Game::GameSaveData> loaded =
        OpenYAMM::Game::loadGameDataFromPath(savePath, error);
    std::filesystem::remove(savePath);

    REQUIRE(loaded.has_value());
    REQUIRE(loaded->outdoorWorld.eventRuntimeState.has_value());

    const OpenYAMM::Game::EventRuntimeState &loadedState = *loaded->outdoorWorld.eventRuntimeState;
    CHECK_EQ(loadedState.generatedNpcIdsByActorKey.at("7out01.odm#4#51#Peasant"), 1184u);
    CHECK_EQ(loadedState.npcNameOverrides.at(1184), "Aaron");
    CHECK_EQ(loadedState.npcPictureOverrides.at(1184), 123u);
    CHECK_EQ(loadedState.npcProfessionOverrides.at(1184), 52u);
    CHECK(loadedState.unavailableNpcIds.contains(1184));
    REQUIRE_EQ(loadedState.hiredNpcFollowers.size(), 1u);
    CHECK_EQ(loadedState.hiredNpcFollowers.front().npcId, 1184u);
    CHECK_EQ(loadedState.hiredNpcFollowers.front().professionId, 52u);
    CHECK_EQ(loadedState.hiredNpcFollowers.front().weeklyCost, 300u);
    CHECK_EQ(loadedState.hiredNpcFollowers.front().abilityUsedDay, 7u);
    CHECK((loadedState.actorSetMasks.at(4) & invisibleBit) != 0);
}

TEST_CASE("persistent lua runtime travel state survives save data round trip")
{
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    OpenYAMM::Game::EventRuntimeState::SavedLocation location = {};
    location.mapName = "7out03.odm";
    location.x = 101;
    location.y = 202;
    location.z = 303;
    location.continentId = 2;
    runtimeState.savedLocations["TempleInABottleReturn"] = location;

    OpenYAMM::Game::EventRuntimeState::TransportRouteOverride route = {};
    route.houseId = 462;
    route.routeIndex = 4;
    route.destinationName = "Emerald Island";
    route.mapFileName = "7Out01.odm";
    route.daysAvailable = {false, false, true, false, false, false, false};
    route.travelDays = 6;
    route.x = 12552;
    route.y = 800;
    route.z = 193;
    route.directionDegrees = 90;
    runtimeState.transportRouteOverrides[
        OpenYAMM::Game::EventRuntime::transportRouteOverrideKey(route.houseId, route.routeIndex)] = route;

    OpenYAMM::Game::GameSaveData saveData = {};
    saveData.mapFileName = "7out03.odm";
    saveData.hasOutdoorRuntimeState = true;
    saveData.outdoorWorld.eventRuntimeState = runtimeState;

    const std::filesystem::path savePath =
        std::filesystem::temp_directory_path() / "openyamm_persistent_lua_runtime_state_roundtrip.oysav";
    std::string error;
    REQUIRE(OpenYAMM::Game::saveGameDataToPath(savePath, saveData, error));

    const std::optional<OpenYAMM::Game::GameSaveData> loaded =
        OpenYAMM::Game::loadGameDataFromPath(savePath, error);
    std::filesystem::remove(savePath);

    REQUIRE(loaded.has_value());
    REQUIRE(loaded->outdoorWorld.eventRuntimeState.has_value());
    const OpenYAMM::Game::EventRuntimeState &loadedState = *loaded->outdoorWorld.eventRuntimeState;
    REQUIRE(loadedState.savedLocations.contains("TempleInABottleReturn"));
    CHECK_EQ(loadedState.savedLocations.at("TempleInABottleReturn").mapName, "7out03.odm");
    CHECK_EQ(loadedState.savedLocations.at("TempleInABottleReturn").x, 101);

    const uint64_t routeKey = OpenYAMM::Game::EventRuntime::transportRouteOverrideKey(462, 4);
    REQUIRE(loadedState.transportRouteOverrides.contains(routeKey));
    CHECK_EQ(loadedState.transportRouteOverrides.at(routeKey).mapFileName, "7Out01.odm");
    CHECK_EQ(loadedState.transportRouteOverrides.at(routeKey).daysAvailable[2], true);
    CHECK_EQ(loadedState.transportRouteOverrides.at(routeKey).directionDegrees, 90);
}

TEST_CASE("hired follower views use runtime NPC overrides")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::EventRuntimeState runtimeState = {};

    runtimeState.npcNameOverrides[1184] = "Aaron";
    runtimeState.npcPictureOverrides[1184] = 123;
    runtimeState.npcProfessionOverrides[1184] = 52;

    OpenYAMM::Game::EventRuntimeState::HiredNpcFollower follower = {};
    follower.npcId = 1184;
    follower.professionId = 52;
    follower.weeklyCost = 300;
    runtimeState.hiredNpcFollowers.push_back(follower);

    const std::vector<OpenYAMM::Game::HiredNpcFollowerView> views =
        OpenYAMM::Game::buildHiredNpcFollowerViews(
            runtimeState,
            gameData.npcDialogTable,
            gameData.mergedNpcProfessionTable);

    REQUIRE_EQ(views.size(), 1u);
    CHECK_EQ(views.front().npcId, 1184u);
    CHECK_EQ(views.front().name, "Aaron");
    CHECK_EQ(views.front().portraitPictureId, 123u);
    CHECK_EQ(views.front().professionId, 52u);
    CHECK_EQ(views.front().weeklyCost, 300u);
    CHECK_EQ(views.front().feePercent, 3u);
    const OpenYAMM::Game::MergedNpcProfessionEntry *pProfession = gameData.mergedNpcProfessionTable.get(52);
    REQUIRE(pProfession != nullptr);
    CHECK_EQ(views.front().profession, pProfession->profession);
    CHECK_EQ(OpenYAMM::Game::totalHiredNpcFollowerFeePercent(runtimeState), 3u);
    CHECK_EQ(OpenYAMM::Game::hiredNpcFollowerGoldShare(1000, runtimeState), 30u);
    CHECK(OpenYAMM::Game::hiredNpcHasProfession(runtimeState, 52));

    OpenYAMM::Game::EventRuntimeState travelState = {};
    travelState.hiredNpcFollowers.push_back({1185, 9, 300});
    travelState.hiredNpcFollowers.push_back({1186, 45, 300});
    travelState.hiredNpcFollowers.push_back({1187, 35, 300});
    CHECK_EQ(OpenYAMM::Game::hiredNpcTransportDayReduction(travelState, false), 5);
    CHECK_EQ(OpenYAMM::Game::hiredNpcTransportDayReduction(travelState, true), 2);
}

TEST_CASE("hired follower views include party followers missing from current map runtime")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Game::Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.addHiredNpcFollower({WilmaCookGateMasterNpcId, GateMasterProfessionId, 2000});

    const OpenYAMM::Game::EventRuntimeState runtimeState = {};
    const std::vector<OpenYAMM::Game::HiredNpcFollowerView> views =
        OpenYAMM::Game::buildHiredNpcFollowerViews(
            runtimeState,
            &party,
            gameData.npcDialogTable,
            gameData.mergedNpcProfessionTable);

    REQUIRE_EQ(views.size(), 1u);
    CHECK_EQ(views.front().npcId, WilmaCookGateMasterNpcId);
    CHECK_EQ(views.front().professionId, GateMasterProfessionId);
    CHECK_EQ(views.front().weeklyCost, 2000u);
}

TEST_CASE("generic actor news uses actor portrait override")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    OpenYAMM::Game::MergedMonsterPortraitTable portraitTable;
    REQUIRE(portraitTable.loadFromRows({
        {"#", "Portraits", "Name"},
        {"185", "1016", "Guard"},
    }));

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> resolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "7out01.odm",
            "Guard",
            55,
            harness.eventRuntimeState(),
            gameData.npcDialogTable,
            &portraitTable);

    REQUIRE(resolution.has_value());
    CHECK_EQ(resolution->portraitPictureId, 1016u);

    const std::optional<std::string> newsText = gameData.npcDialogTable.getNewsDialogText(resolution->newsId);
    REQUIRE(newsText.has_value());

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openNpcNews(
            resolution->npcId,
            resolution->newsId,
            "Guard",
            *newsText,
            resolution->portraitPictureId);

    CHECK_EQ(dialog.title, "Guard");
    CHECK_EQ(dialog.participantPictureId, 1016u);
}

TEST_CASE("mm7 temple swordsmen resolve generic guard news")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> resolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "7d06.blv",
            "Swordsman",
            54,
            harness.eventRuntimeState(),
            gameData.npcDialogTable);

    REQUIRE(resolution.has_value());
    CHECK_NE(resolution->npcId, 0u);

    const std::optional<std::string> newsText = gameData.npcDialogTable.getNewsDialogText(resolution->newsId);
    REQUIRE(newsText.has_value());

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openNpcNews(
            resolution->npcId,
            resolution->newsId,
            "Swordsman",
            *newsText,
            resolution->portraitPictureId);

    CHECK_EQ(dialog.title, "Swordsman");
    CHECK(!dialog.lines.empty());
}

TEST_CASE("single resident auto open")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(FredrickHouseId);

    CHECK_EQ(dialog.title, "Fredrick Talimere");
    CHECK(dialogHasActionLabel(dialog, "Portals of Stone"));
    CHECK(dialogHasActionLabel(dialog, "Cataclysm"));
}

TEST_CASE("merged house exits add direct destination actions with entrance coordinates")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::HouseEntry *pHouse = gameData.houseTable.get(FreeHavenSewerEntranceHouseId);
    REQUIRE(pHouse != nullptr);
    REQUIRE(pHouse->extraExit.has_value());
    CHECK_EQ(pHouse->extraExit->pictureId, 1567u);
    CHECK_EQ(pHouse->extraExit->destinationMapFileName, "sewer.blv");
    CHECK_EQ(pHouse->extraExit->x, -6575);
    CHECK_EQ(pHouse->extraExit->y, 13740);
    CHECK_EQ(pHouse->extraExit->z, 177);

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openHouseDialog(FreeHavenSewerEntranceHouseId);
    const std::optional<size_t> residentIndex = findActionIndexByLabel(dialog, "Takao");
    const std::optional<size_t> sewerIndex = findActionIndexByLabel(dialog, "Free Haven Sewer");

    REQUIRE(residentIndex.has_value());
    CHECK_EQ(dialog.actions[*residentIndex].kind, OpenYAMM::Game::EventDialogActionKind::HouseResident);
    REQUIRE(sewerIndex.has_value());
    CHECK_EQ(dialog.actions[*sewerIndex].kind, OpenYAMM::Game::EventDialogActionKind::HouseExtraExit);
    CHECK_EQ(dialog.actions[*sewerIndex].participantPictureId, 1567u);

    const OpenYAMM::Game::EventDialogContent &sewerDialog = harness.executeAndPresent(*sewerIndex);
    CHECK_EQ(sewerDialog.participantPictureId, 1567u);

    const std::optional<size_t> enterIndex = findActionIndexByLabel(sewerDialog, "Enter");
    REQUIRE(enterIndex.has_value());

    const OpenYAMM::Game::GameplayDialogController::Result result =
        harness.executeActiveDialogAction(*enterIndex);
    CHECK(result.shouldCloseActiveDialog);
    REQUIRE(harness.eventRuntimeState().pendingMapMove.has_value());
    CHECK_EQ(harness.eventRuntimeState().pendingMapMove->mapName, std::optional<std::string>("sewer.blv"));
    CHECK_EQ(harness.eventRuntimeState().pendingMapMove->x, -6575);
    CHECK_EQ(harness.eventRuntimeState().pendingMapMove->y, 13740);
    CHECK_EQ(harness.eventRuntimeState().pendingMapMove->z, 177);
    CHECK_FALSE(harness.eventRuntimeState().pendingMapMove->useMapStartPosition);
}

TEST_CASE("merged house exits without explicit entrance coordinates use destination map start")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    harness.party().setQuestBit(1193, true);

    const OpenYAMM::Game::HouseEntry *pHouse = gameData.houseTable.get(OracleHouseId);
    REQUIRE(pHouse != nullptr);
    REQUIRE(pHouse->extraExit.has_value());
    CHECK_EQ(pHouse->extraExit->destinationMapFileName, "sci-fi.blv");
    CHECK(pHouse->extraExit->useMapStartPosition);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(OracleHouseId);
    const std::optional<size_t> enterIndex = findActionIndexByLabel(dialog, "Enter");
    REQUIRE(enterIndex.has_value());

    const OpenYAMM::Game::GameplayDialogController::Result result =
        harness.executeActiveDialogAction(*enterIndex);
    CHECK(result.shouldCloseActiveDialog);
    REQUIRE(harness.eventRuntimeState().pendingMapMove.has_value());
    CHECK_EQ(harness.eventRuntimeState().pendingMapMove->mapName, std::optional<std::string>("sci-fi.blv"));
    CHECK(harness.eventRuntimeState().pendingMapMove->useMapStartPosition);
}

TEST_CASE("merged NPC profession suite supplies follower, profession, and news actions")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    harness.party().addGold(10000);

    OpenYAMM::Game::EventDialogContent dialog = harness.openNpcDialogue(WilmaCookGateMasterNpcId);
    const std::optional<size_t> gateMasterHireIndex = findActionIndexByLabel(dialog, "Join");
    const std::optional<size_t> gateMasterInfoIndex = findActionIndexByLabel(dialog, "More Info");

    CHECK(gateMasterHireIndex.has_value());
    REQUIRE(gateMasterInfoIndex.has_value());
    CHECK_FALSE(findActionIndexByLabel(dialog, "Cast Town Portal").has_value());
    CHECK(dialogHasAction(dialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionNews, "Town Portal"));
    CHECK_FALSE(dialogHasAction(dialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionAction, "Gate Master"));
    CHECK_FALSE(findActionIndexByLabel(dialog, "Beg").has_value());
    CHECK_FALSE(findActionIndexByLabel(dialog, "Threat").has_value());
    CHECK_FALSE(findActionIndexByLabel(dialog, "Bribe").has_value());

    harness.executeAndPresent(*gateMasterInfoIndex);
    REQUIRE_FALSE(harness.eventRuntimeState().messages.empty());
    CHECK(harness.eventRuntimeState().messages.back().find("Town Portal spell") != std::string::npos);

    const OpenYAMM::Game::NpcEntry *pIris = gameData.npcDialogTable.getNpc(IrisPoppyfieldNpcId);
    REQUIRE(pIris != nullptr);
    CHECK_EQ(pIris->professionId, BardProfessionId);
    CHECK(pIris->joins);

    dialog = harness.openNpcDialogue(IrisPoppyfieldNpcId);
    CHECK(findActionIndexByLabel(dialog, "Join").has_value());
    CHECK(findActionIndexByLabel(dialog, "More Info").has_value());
    CHECK(dialogHasAction(dialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionNews, "Free Haven"));
    CHECK_FALSE(dialogHasAction(dialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionAction, "Bard"));

    const OpenYAMM::Game::MergedNpcProfessionEntry *pBardProfession =
        gameData.mergedNpcProfessionTable.get(BardProfessionId);
    REQUIRE(pBardProfession != nullptr);
    CHECK(pBardProfession->joins);

    OpenYAMM::Tests::HouseDialogueTestHarness generatedBardHarness(gameData);
    constexpr uint32_t GeneratedBardNpcId = 20004;
    generatedBardHarness.eventRuntimeState().npcNameOverrides[GeneratedBardNpcId] = "Christine";
    generatedBardHarness.eventRuntimeState().npcPictureOverrides[GeneratedBardNpcId] = 1;
    generatedBardHarness.eventRuntimeState().npcProfessionOverrides[GeneratedBardNpcId] = BardProfessionId;

    OpenYAMM::Game::MapStatsEntry jadameMap = {};
    jadameMap.mergedContinentId = 1;
    generatedBardHarness.setCurrentMap(jadameMap);

    dialog = generatedBardHarness.openNpcDialogue(GeneratedBardNpcId);
    CHECK(findActionIndexByLabel(dialog, "Join").has_value());
    CHECK(findActionIndexByLabel(dialog, "More Info").has_value());
    CHECK_FALSE(dialogHasAction(dialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionAction, "Bard"));

    const OpenYAMM::Game::NpcEntry *pPaul = gameData.npcDialogTable.getNpc(PaulHapsburgNpcId);
    REQUIRE(pPaul != nullptr);
    CHECK_EQ(pPaul->professionId, MasterHealerProfessionId);
    CHECK(pPaul->joins);

    dialog = harness.openNpcDialogue(PaulHapsburgNpcId);
    CHECK(findActionIndexByLabel(dialog, "Join").has_value());
    const std::optional<size_t> paulInfoIndex = findActionIndexByLabel(dialog, "More Info");
    REQUIRE(paulInfoIndex.has_value());
    CHECK(dialogHasAction(dialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionNews, "Advanced Alchemy"));
    CHECK_FALSE(dialogHasAction(dialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionAction, "Master Healer"));

    harness.executeAndPresent(*paulInfoIndex);
    REQUIRE_FALSE(harness.eventRuntimeState().messages.empty());
    CHECK(harness.eventRuntimeState().messages.back().find("Completely heals party") != std::string::npos);
    CHECK(harness.eventRuntimeState().messages.back().find("potions") == std::string::npos);

    dialog = harness.openNpcDialogue(KevinWatchPeasantNpcId, 0, 4);
    const std::optional<size_t> peasantHireIndex = findActionIndexByLabel(dialog, "Join");
    REQUIRE(peasantHireIndex.has_value());
    CHECK(dialogHasAction(dialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionNews, "Temple of Baa"));
    CHECK_FALSE(dialogHasAction(dialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionAction, "Peasant"));
    CHECK_FALSE(findActionIndexByLabel(dialog, "More Info").has_value());

    const OpenYAMM::Game::NpcEntry *pTor = gameData.npcDialogTable.getNpc(TorBrockNpcId);
    REQUIRE(pTor != nullptr);
    CHECK_EQ(pTor->professionId, PotterProfessionId);
    CHECK(pTor->joins);

    dialog = harness.openNpcDialogue(TorBrockNpcId, TorBrockHouseId);
    CHECK(findActionIndexByLabel(dialog, "Join").has_value());
    CHECK_FALSE(findActionIndexByLabel(dialog, "More Info").has_value());
    const std::optional<size_t> potterNewsIndex = findActionIndexByLabel(dialog, "Hot Fires");
    REQUIRE(potterNewsIndex.has_value());
    CHECK_EQ(dialog.actions[*potterNewsIndex].kind, OpenYAMM::Game::EventDialogActionKind::NpcProfessionNews);

    harness.executeAndPresent(*potterNewsIndex);
    REQUIRE_FALSE(harness.eventRuntimeState().messages.empty());
    CHECK(harness.eventRuntimeState().messages.back().find("pottery") != std::string::npos);

    dialog = harness.openNpcDialogue(ChitaniaRetianiNpcId, ChitaniaRetianiHouseId);
    CHECK(findActionIndexByLabel(dialog, "Join").has_value());
    CHECK_FALSE(findActionIndexByLabel(dialog, "More Info").has_value());
    const std::optional<size_t> chitaniaNewsIndex = findActionIndexByLabel(dialog, "Hot Fires");
    REQUIRE(chitaniaNewsIndex.has_value());
    CHECK_EQ(dialog.actions[*chitaniaNewsIndex].kind, OpenYAMM::Game::EventDialogActionKind::NpcProfessionNews);

    harness.worldRuntime().advanceGameMinutes(2.0f * 1440.0f);
    const OpenYAMM::Game::NpcEntry *pJo = gameData.npcDialogTable.getNpc(JoHandlebaumSpellMasterNpcId);
    REQUIRE(pJo != nullptr);
    CHECK_EQ(pJo->professionId, SpellMasterProfessionId);
    CHECK(pJo->joins);

    dialog = harness.openNpcDialogue(JoHandlebaumSpellMasterNpcId, JoHandlebaumSpellMasterHouseId);
    CHECK(findActionIndexByLabel(dialog, "Join").has_value());
    CHECK(findActionIndexByLabel(dialog, "More Info").has_value());
    const std::optional<size_t> spellMasterNewsIndex = findActionIndexByLabel(dialog, "Terrax's Crystal");
    REQUIRE(spellMasterNewsIndex.has_value());
    CHECK_EQ(dialog.actions[*spellMasterNewsIndex].kind, OpenYAMM::Game::EventDialogActionKind::NpcProfessionNews);
    CHECK_FALSE(
        dialogHasAction(dialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionAction, "Spell Master"));

    harness.executeAndPresent(*spellMasterNewsIndex);
    REQUIRE_FALSE(harness.eventRuntimeState().messages.empty());
    CHECK(harness.eventRuntimeState().messages.back().find("Corlagon took Terrax's Crystal") != std::string::npos);
    harness.worldRuntime().advanceGameMinutes(-2.0f * 1440.0f);

    checkJoinableProfessionNewsDialog(
        harness,
        gameData,
        GingerAstorTeacherNpcId,
        GingerAstorTeacherHouseId,
        TeacherProfessionId,
        "Skills");
    checkJoinableProfessionNewsDialog(
        harness,
        gameData,
        NoahWhiteInstructorNpcId,
        NoahWhiteInstructorHouseId,
        InstructorProfessionId,
        "Kriegspire");
    checkJoinableProfessionNewsDialog(
        harness,
        gameData,
        KernCarnegieArmsMasterNpcId,
        KernCarnegieArmsMasterHouseId,
        ArmsMasterProfessionId,
        "Battle Tactics");
    checkJoinableProfessionNewsDialog(
        harness,
        gameData,
        MiriamBoyerWeaponsMasterNpcId,
        MiriamBoyerWeaponsMasterHouseId,
        WeaponsMasterProfessionId,
        "Magic Weapons");

    dialog = harness.openNpcDialogue(KevinWatchPeasantNpcId, 0, 4);
    const std::optional<size_t> refreshedPeasantHireIndex = findActionIndexByLabel(dialog, "Join");
    REQUIRE(refreshedPeasantHireIndex.has_value());
    const OpenYAMM::Game::EventDialogContent offerDialog =
        harness.executeAndPresent(*refreshedPeasantHireIndex);
    const std::optional<size_t> acceptIndex = findActionIndexByLabel(offerDialog, "Yes");
    REQUIRE(acceptIndex.has_value());

    const OpenYAMM::Game::EventDialogContent hiredDialog = harness.executeAndPresent(*acceptIndex);
    CHECK_EQ(harness.eventRuntimeState().hiredNpcFollowers.size(), 1u);
    CHECK_EQ(harness.eventRuntimeState().hiredNpcFollowers.front().professionId, 52u);
    CHECK(harness.eventRuntimeState().unavailableNpcIds.contains(KevinWatchPeasantNpcId));
    const uint32_t invisibleBit = static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Invisible);
    CHECK((harness.eventRuntimeState().actorSetMasks[4] & invisibleBit) != 0);

    const uint32_t hiredPeasantVariable =
        (52u << 16) | static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::HiredNpcHasSpeciality);
    CHECK_EQ(
        OpenYAMM::Game::EventRuntime::getVariableValue(
            harness.eventRuntimeState(),
            OpenYAMM::Game::EventRuntime::decodeVariable(hiredPeasantVariable),
            &harness.party()),
        1);
    CHECK_FALSE(hiredDialog.isActive);
    CHECK_FALSE(harness.eventRuntimeState().messages.empty());
    CHECK(harness.eventRuntimeState().messages.back().find("joined the followers") != std::string::npos);
}

TEST_CASE("merged in-house plain NPC followers can be hired and leave their house")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    harness.party().addGold(10000);

    constexpr uint32_t WilmaCookHouseId = 1476;
    const OpenYAMM::Game::HouseEntry *pHouse = gameData.houseTable.get(WilmaCookHouseId);
    REQUIRE(pHouse != nullptr);

    const OpenYAMM::Game::EventDialogContent naomiDialog =
        harness.openNpcDialogue(NaomiWindNpcId, NaomiWindHouseId);
    CHECK(findActionIndexByLabel(naomiDialog, "Join").has_value());
    CHECK(findActionIndexByLabel(naomiDialog, "More Info").has_value());
    CHECK(dialogHasAction(naomiDialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionNews, "Town Portal"));
    CHECK_FALSE(
        dialogHasAction(naomiDialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionAction, "Gate Master"));

    std::vector<uint32_t> residentIds =
        OpenYAMM::Game::collectSelectableResidentNpcIds(
            *pHouse,
            gameData.npcDialogTable,
            harness.eventRuntimeState());
    CHECK(std::find(residentIds.begin(), residentIds.end(), WilmaCookGateMasterNpcId) != residentIds.end());

    const OpenYAMM::Game::EventDialogContent dialog =
        harness.openNpcDialogue(WilmaCookGateMasterNpcId, WilmaCookHouseId);
    const std::optional<size_t> hireIndex = findActionIndexByLabel(dialog, "Join");
    REQUIRE(hireIndex.has_value());
    CHECK_FALSE(findActionIndexByLabel(dialog, "Beg").has_value());
    CHECK_FALSE(findActionIndexByLabel(dialog, "Threat").has_value());
    CHECK_FALSE(findActionIndexByLabel(dialog, "Bribe").has_value());

    const OpenYAMM::Game::EventDialogContent offerDialog = harness.executeAndPresent(*hireIndex);
    const std::optional<size_t> acceptIndex = findActionIndexByLabel(offerDialog, "Yes");
    REQUIRE(acceptIndex.has_value());

    const OpenYAMM::Game::EventDialogContent hiredDialog = harness.executeAndPresent(*acceptIndex);
    CHECK_FALSE(hiredDialog.isActive);
    REQUIRE_EQ(harness.eventRuntimeState().hiredNpcFollowers.size(), 1u);
    CHECK_EQ(harness.eventRuntimeState().hiredNpcFollowers.front().npcId, WilmaCookGateMasterNpcId);
    CHECK_EQ(harness.eventRuntimeState().hiredNpcFollowers.front().professionId, GateMasterProfessionId);
    CHECK(harness.eventRuntimeState().unavailableNpcIds.contains(WilmaCookGateMasterNpcId));

    OpenYAMM::Game::EventRuntimeState transitionedRuntimeState = {};
    harness.party().applyGlobalNpcStateTo(transitionedRuntimeState);
    REQUIRE_EQ(transitionedRuntimeState.hiredNpcFollowers.size(), 1u);
    CHECK_EQ(transitionedRuntimeState.hiredNpcFollowers.front().npcId, WilmaCookGateMasterNpcId);
    CHECK(transitionedRuntimeState.unavailableNpcIds.contains(WilmaCookGateMasterNpcId));

    const OpenYAMM::Game::Party::Snapshot partySnapshot = harness.party().snapshot();
    OpenYAMM::Game::Party restoredParty = {};
    restoredParty.restoreSnapshot(partySnapshot);
    OpenYAMM::Game::EventRuntimeState restoredRuntimeState = {};
    restoredParty.applyGlobalNpcStateTo(restoredRuntimeState);
    REQUIRE_EQ(restoredRuntimeState.hiredNpcFollowers.size(), 1u);
    CHECK_EQ(restoredRuntimeState.hiredNpcFollowers.front().npcId, WilmaCookGateMasterNpcId);

    residentIds =
        OpenYAMM::Game::collectSelectableResidentNpcIds(
            *pHouse,
            gameData.npcDialogTable,
            harness.eventRuntimeState());
    CHECK(std::find(residentIds.begin(), residentIds.end(), WilmaCookGateMasterNpcId) == residentIds.end());
}

TEST_CASE("Naomi Wind in-house hire requires start gold and leaves house after hire")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    const OpenYAMM::Game::HouseEntry *pHouse = gameData.houseTable.get(NaomiWindHouseId);
    REQUIRE(pHouse != nullptr);

    {
        OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
        harness.party().addGold(175);

        const OpenYAMM::Game::EventDialogContent dialog =
            harness.openNpcDialogue(NaomiWindNpcId, NaomiWindHouseId);
        const std::optional<size_t> infoIndex = findActionIndexByLabel(dialog, "More Info");
        REQUIRE(infoIndex.has_value());
        CHECK(dialogHasAction(dialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionNews, "Town Portal"));
        CHECK_FALSE(dialogHasAction(dialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionAction, "Gate Master"));

        harness.executeAndPresent(*infoIndex);
        REQUIRE_FALSE(harness.eventRuntimeState().messages.empty());
        CHECK(harness.eventRuntimeState().messages.back().find("Town Portal spell") != std::string::npos);

        const OpenYAMM::Game::EventDialogContent refreshedDialog =
            harness.openNpcDialogue(NaomiWindNpcId, NaomiWindHouseId);
        const std::optional<size_t> hireIndex = findActionIndexByLabel(refreshedDialog, "Join");
        REQUIRE(hireIndex.has_value());

        const OpenYAMM::Game::EventDialogContent offerDialog = harness.executeAndPresent(*hireIndex);
        const std::optional<size_t> acceptIndex = findActionIndexByLabel(offerDialog, "Yes");
        REQUIRE(acceptIndex.has_value());

        const OpenYAMM::Game::EventDialogContent refusedDialog = harness.executeAndPresent(*acceptIndex);
        CHECK(refusedDialog.isActive);
        CHECK(harness.eventRuntimeState().hiredNpcFollowers.empty());
        CHECK_FALSE(harness.eventRuntimeState().unavailableNpcIds.contains(NaomiWindNpcId));
        REQUIRE_FALSE(harness.eventRuntimeState().messages.empty());
        CHECK_EQ(harness.eventRuntimeState().messages.back(), "You don't have enough gold!");
        CHECK(harness.eventRuntimeState().messages.back().find("Lost Book") == std::string::npos);

        const std::vector<uint32_t> residentIds =
            OpenYAMM::Game::collectSelectableResidentNpcIds(
                *pHouse,
                gameData.npcDialogTable,
                harness.eventRuntimeState());
        CHECK(std::find(residentIds.begin(), residentIds.end(), NaomiWindNpcId) != residentIds.end());
    }

    {
        OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
        harness.party().addGold(2000);

        const OpenYAMM::Game::EventDialogContent dialog =
            harness.openNpcDialogue(NaomiWindNpcId, NaomiWindHouseId);
        const std::optional<size_t> hireIndex = findActionIndexByLabel(dialog, "Join");
        REQUIRE(hireIndex.has_value());

        const OpenYAMM::Game::EventDialogContent offerDialog = harness.executeAndPresent(*hireIndex);
        const std::optional<size_t> acceptIndex = findActionIndexByLabel(offerDialog, "Yes");
        REQUIRE(acceptIndex.has_value());

        const OpenYAMM::Game::EventDialogContent hiredDialog = harness.executeAndPresent(*acceptIndex);
        CHECK_FALSE(hiredDialog.isActive);
        REQUIRE_EQ(harness.eventRuntimeState().hiredNpcFollowers.size(), 1u);
        CHECK_EQ(harness.eventRuntimeState().hiredNpcFollowers.front().npcId, NaomiWindNpcId);
        CHECK(harness.eventRuntimeState().unavailableNpcIds.contains(NaomiWindNpcId));

        const std::vector<uint32_t> residentIds =
            OpenYAMM::Game::collectSelectableResidentNpcIds(
                *pHouse,
                gameData.npcDialogTable,
                harness.eventRuntimeState());
        CHECK(std::find(residentIds.begin(), residentIds.end(), NaomiWindNpcId) == residentIds.end());
    }
}

TEST_CASE("merged in-house scripted teachers do not offer profession hire")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    constexpr uint32_t MasterIdentifyItemTeacherHouseId = 798;
    const OpenYAMM::Game::EventDialogContent dialog =
        harness.openNpcDialogue(MasterIdentifyItemTeacherNpcId, MasterIdentifyItemTeacherHouseId);

    CHECK(dialogHasActionLabel(dialog, "Master Identify Item"));
    CHECK_FALSE(findActionIndexByLabel(dialog, "Join").has_value());
}

TEST_CASE("merged NPC follower action topics execute abilities instead of stale topic text")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    constexpr uint32_t SharlaQuinnMasterHealerNpcId = 1055;
    harness.eventRuntimeState().hiredNpcFollowers.push_back({SharlaQuinnMasterHealerNpcId, 12, 5000});
    harness.eventRuntimeState().unavailableNpcIds.insert(SharlaQuinnMasterHealerNpcId);
    harness.party().addHiredNpcFollower({SharlaQuinnMasterHealerNpcId, 12, 5000});

    OpenYAMM::Game::Character *pMember = harness.party().member(0);
    REQUIRE(pMember != nullptr);
    pMember->maxHealth = 80;
    pMember->health = 1;
    pMember->maxSpellPoints = 60;
    pMember->spellPoints = 0;
    REQUIRE(harness.party().applyMemberCondition(0, OpenYAMM::Game::CharacterCondition::PoisonSevere));

    const OpenYAMM::Game::EventDialogContent dialog =
        harness.openNpcDialogue(SharlaQuinnMasterHealerNpcId);
    const std::optional<size_t> healIndex = findActionIndexByLabel(dialog, "Heal Party");
    REQUIRE(healIndex.has_value());
    CHECK_FALSE(findActionIndexByLabel(dialog, "Master Healer").has_value());

    const OpenYAMM::Game::EventDialogContent afterHealDialog =
        harness.executeAndPresent(*healIndex);

    pMember = harness.party().member(0);
    REQUIRE(pMember != nullptr);
    CHECK_EQ(pMember->health, 80);
    CHECK_EQ(pMember->spellPoints, 60);
    CHECK_FALSE(pMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::PoisonSevere)));
    REQUIRE_FALSE(harness.eventRuntimeState().messages.empty());
    CHECK_EQ(harness.eventRuntimeState().messages.back(), "Done!");
    CHECK_FALSE(findActionIndexByLabel(afterHealDialog, "Heal Party").has_value());
    REQUIRE_EQ(harness.eventRuntimeState().hiredNpcFollowers.size(), 1u);
    CHECK_EQ(
        harness.eventRuntimeState().hiredNpcFollowers.front().abilityUsedDay,
        OpenYAMM::Game::npcProfessionActionCooldownDay(harness.worldRuntime().gameMinutes()));
    CHECK_EQ(
        harness.eventRuntimeState().variables[OpenYAMM::Game::npcProfessionActionCooldownVariableKey(
            SharlaQuinnMasterHealerNpcId)],
        static_cast<int32_t>(OpenYAMM::Game::npcProfessionActionCooldownDay(
            harness.worldRuntime().gameMinutes())));
}

TEST_CASE("gate master town portal uses follower spell power")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    harness.eventRuntimeState().hiredNpcFollowers.push_back({WilmaCookGateMasterNpcId, GateMasterProfessionId, 2000});
    harness.eventRuntimeState().unavailableNpcIds.insert(WilmaCookGateMasterNpcId);
    harness.party().addHiredNpcFollower({WilmaCookGateMasterNpcId, GateMasterProfessionId, 2000});

    OpenYAMM::Game::Character *pActiveMember = harness.party().activeMember();
    REQUIRE(pActiveMember != nullptr);
    pActiveMember->skills.erase("WaterMagic");
    pActiveMember->spellPoints = 0;
    pActiveMember->recoverySecondsRemaining = 0.0f;

    const OpenYAMM::Game::EventDialogContent dialog =
        harness.openNpcDialogue(WilmaCookGateMasterNpcId);
    const std::optional<size_t> townPortalIndex = findActionIndexByLabel(dialog, "Cast Town Portal");
    REQUIRE(townPortalIndex.has_value());

    harness.executeAndPresent(*townPortalIndex);

    const OpenYAMM::Game::GameplayUiController::UtilitySpellOverlayState &overlay =
        harness.uiController().utilitySpellOverlay();
    REQUIRE(overlay.active);
    CHECK_EQ(overlay.mode, OpenYAMM::Game::GameplayUiController::UtilitySpellOverlayMode::TownPortal);
    CHECK_EQ(overlay.skillLevelOverride, 10u);
    CHECK_EQ(overlay.skillMasteryOverride, OpenYAMM::Game::SkillMastery::Grandmaster);
    CHECK_FALSE(overlay.spendMana);
    CHECK_FALSE(overlay.applyRecovery);
    CHECK(overlay.bypassGameplayCasterValidation);
    CHECK(overlay.bypassTownPortalFailureChecks);

    OpenYAMM::Game::GameplayRuntimeActorState hostileActor = {};
    hostileActor.hostileToParty = true;
    hostileActor.hasDetectedParty = true;
    harness.worldRuntime().addActor(hostileActor);

    OpenYAMM::Game::PartySpellCastRequest request = {};
    request.casterMemberIndex = overlay.casterMemberIndex;
    request.spellId = overlay.spellId;
    request.skillLevelOverride = overlay.skillLevelOverride;
    request.skillMasteryOverride = overlay.skillMasteryOverride;
    request.spendMana = overlay.spendMana;
    request.applyRecovery = overlay.applyRecovery;
    request.bypassGameplayCasterValidation = overlay.bypassGameplayCasterValidation;
    request.bypassTownPortalFailureChecks = overlay.bypassTownPortalFailureChecks;
    request.utilityAction = OpenYAMM::Game::PartySpellUtilityActionKind::TownPortalDestination;
    request.hasUtilityMapMove = true;
    request.utilityMapMoveMapName = "out01.odm";
    request.utilityMapMoveX = 10;
    request.utilityMapMoveY = 20;
    request.utilityMapMoveZ = 30;
    request.utilityMapMoveDirectionDegrees = 90;

    const OpenYAMM::Game::PartySpellCastResult result = OpenYAMM::Game::PartySpellSystem::castSpell(
        harness.party(),
        harness.worldRuntime(),
        gameData.spellTable,
        request);

    CHECK(result.succeeded());
    REQUIRE(harness.eventRuntimeState().pendingMapMove.has_value());
    CHECK_EQ(harness.eventRuntimeState().pendingMapMove->mapName, std::optional<std::string>("out01.odm"));
    CHECK_EQ(harness.eventRuntimeState().pendingMapMove->x, 10);

    REQUIRE_EQ(harness.eventRuntimeState().hiredNpcFollowers.size(), 1u);
    CHECK_EQ(
        harness.eventRuntimeState().hiredNpcFollowers.front().abilityUsedDay,
        OpenYAMM::Game::npcProfessionActionCooldownDay(harness.worldRuntime().gameMinutes()));

    const OpenYAMM::Game::EventDialogContent usedDialog =
        harness.openNpcDialogue(WilmaCookGateMasterNpcId);
    CHECK_FALSE(findActionIndexByLabel(usedDialog, "Cast Town Portal").has_value());

    harness.worldRuntime().advanceGameMinutes(18.0f * 60.0f);
    const OpenYAMM::Game::EventDialogContent nextDayDialog =
        harness.openNpcDialogue(WilmaCookGateMasterNpcId);
    CHECK(findActionIndexByLabel(nextDayDialog, "Cast Town Portal").has_value());
}

TEST_CASE("wind master follower spell queues normal cast feedback")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    harness.eventRuntimeState().npcProfessionOverrides[KevinWatchPeasantNpcId] = WindMasterProfessionId;
    harness.eventRuntimeState().hiredNpcFollowers.push_back({KevinWatchPeasantNpcId, WindMasterProfessionId, 2000});
    harness.eventRuntimeState().unavailableNpcIds.insert(KevinWatchPeasantNpcId);
    harness.party().addHiredNpcFollower({KevinWatchPeasantNpcId, WindMasterProfessionId, 2000});

    const OpenYAMM::Game::EventDialogContent dialog =
        harness.openNpcDialogue(KevinWatchPeasantNpcId);
    const std::optional<size_t> flyIndex = findActionIndexByLabel(dialog, "Cast Fly");
    REQUIRE(flyIndex.has_value());

    harness.executeAndPresent(*flyIndex);

    const OpenYAMM::Game::PartyBuffState *pFlyBuff =
        harness.party().partyBuff(OpenYAMM::Game::PartyBuffId::Fly);
    REQUIRE(pFlyBuff != nullptr);
    CHECK(pFlyBuff->active());

    REQUIRE_EQ(harness.eventRuntimeState().spellFxRequests.size(), 1u);
    CHECK_EQ(
        harness.eventRuntimeState().spellFxRequests.front().spellId,
        OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Fly));
    CHECK_EQ(
        harness.eventRuntimeState().spellFxRequests.front().memberIndices.size(),
        harness.party().members().size());

    const OpenYAMM::Game::SpellEntry *pFlySpell =
        gameData.spellTable.findById(static_cast<int>(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Fly)));
    REQUIRE(pFlySpell != nullptr);
    REQUIRE_FALSE(harness.eventRuntimeState().pendingSounds.empty());
    CHECK_EQ(harness.eventRuntimeState().pendingSounds.back().soundId, pFlySpell->effectSoundId);
}

TEST_CASE("hired NPC spell abilities use OE durations")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    auto castFollowerSpell = [&gameData](uint32_t professionId, const std::string &actionLabel)
    {
        OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
        harness.eventRuntimeState().npcProfessionOverrides[KevinWatchPeasantNpcId] = professionId;
        harness.eventRuntimeState().hiredNpcFollowers.push_back({KevinWatchPeasantNpcId, professionId, 2000});
        harness.eventRuntimeState().unavailableNpcIds.insert(KevinWatchPeasantNpcId);
        harness.party().addHiredNpcFollower({KevinWatchPeasantNpcId, professionId, 2000});

        const OpenYAMM::Game::EventDialogContent dialog = harness.openNpcDialogue(KevinWatchPeasantNpcId);
        const std::optional<size_t> actionIndex = findActionIndexByLabel(dialog, actionLabel);
        REQUIRE(actionIndex.has_value());
        harness.executeAndPresent(*actionIndex);

        return harness;
    };

    OpenYAMM::Tests::HouseDialogueTestHarness flyHarness =
        castFollowerSpell(WindMasterProfessionId, "Cast Fly");
    const OpenYAMM::Game::PartyBuffState *pFly =
        flyHarness.party().partyBuff(OpenYAMM::Game::PartyBuffId::Fly);
    REQUIRE(pFly != nullptr);
    CHECK_EQ(pFly->remainingSeconds, doctest::Approx(7200.0f));
    CHECK_EQ(pFly->skillLevel, 2u);
    CHECK_EQ(pFly->skillMastery, OpenYAMM::Game::SkillMastery::Master);

    OpenYAMM::Tests::HouseDialogueTestHarness waterWalkHarness =
        castFollowerSpell(WaterMasterProfessionId, "Cast Walk on Water");
    const OpenYAMM::Game::PartyBuffState *pWaterWalk =
        waterWalkHarness.party().partyBuff(OpenYAMM::Game::PartyBuffId::WaterWalk);
    REQUIRE(pWaterWalk != nullptr);
    CHECK_EQ(pWaterWalk->remainingSeconds, doctest::Approx(10800.0f));
    CHECK_EQ(pWaterWalk->skillLevel, 3u);
    CHECK_EQ(pWaterWalk->skillMastery, OpenYAMM::Game::SkillMastery::Master);

    OpenYAMM::Tests::HouseDialogueTestHarness blessHarness =
        castFollowerSpell(AcolyteProfessionId, "Cast Bless");
    for (size_t memberIndex = 0; memberIndex < blessHarness.party().members().size(); ++memberIndex)
    {
        const OpenYAMM::Game::CharacterBuffState *pBless =
            blessHarness.party().characterBuff(memberIndex, OpenYAMM::Game::CharacterBuffId::Bless);
        REQUIRE(pBless != nullptr);
        CHECK_EQ(pBless->remainingSeconds, doctest::Approx(8100.0f));
        CHECK_EQ(pBless->skillLevel, 5u);
        CHECK_EQ(pBless->skillMastery, OpenYAMM::Game::SkillMastery::Master);
    }

    OpenYAMM::Tests::HouseDialogueTestHarness heroismHarness =
        castFollowerSpell(PiperProfessionId, "Cast Heroism");
    const OpenYAMM::Game::PartyBuffState *pHeroism =
        heroismHarness.party().partyBuff(OpenYAMM::Game::PartyBuffId::Heroism);
    REQUIRE(pHeroism != nullptr);
    CHECK_EQ(pHeroism->remainingSeconds, doctest::Approx(8100.0f));
    CHECK_EQ(pHeroism->skillLevel, 5u);
    CHECK_EQ(pHeroism->skillMastery, OpenYAMM::Game::SkillMastery::Master);
}

TEST_CASE("dismissing hired NPC closes dialogue")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    harness.eventRuntimeState().hiredNpcFollowers.push_back({KevinWatchPeasantNpcId, 52, 1});
    harness.eventRuntimeState().unavailableNpcIds.insert(KevinWatchPeasantNpcId);
    harness.party().addHiredNpcFollower({KevinWatchPeasantNpcId, 52, 1});

    const OpenYAMM::Game::EventDialogContent dialog = harness.openNpcDialogue(KevinWatchPeasantNpcId);
    const std::optional<size_t> dismissIndex = findActionIndexByLabel(dialog, "Dismiss");
    REQUIRE(dismissIndex.has_value());

    const OpenYAMM::Game::EventDialogContent dismissedDialog = harness.executeAndPresent(*dismissIndex);
    CHECK_FALSE(dismissedDialog.isActive);
    CHECK(harness.eventRuntimeState().hiredNpcFollowers.empty());
    CHECK_FALSE(harness.eventRuntimeState().unavailableNpcIds.contains(KevinWatchPeasantNpcId));
}

TEST_CASE("random NPC BTB gate follows merged continent reputation rules")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    harness.party().addGold(10000);

    OpenYAMM::Game::MapStatsEntry map = {};
    map.mergedContinentId = 3;
    harness.setCurrentMap(map);
    harness.worldRuntime().setCurrentLocationReputation(10);

    constexpr uint32_t RandomPeasantNpcId = 20001;
    harness.eventRuntimeState().npcNameOverrides[RandomPeasantNpcId] = "Kevin";
    harness.eventRuntimeState().npcPictureOverrides[RandomPeasantNpcId] = 1;
    harness.eventRuntimeState().npcProfessionOverrides[RandomPeasantNpcId] = 52;

    OpenYAMM::Game::EventDialogContent dialog = harness.openNpcDialogue(RandomPeasantNpcId);
    CHECK_FALSE(findActionIndexByLabel(dialog, "Join").has_value());
    REQUIRE(findActionIndexByLabel(dialog, "Beg").has_value());
    REQUIRE(findActionIndexByLabel(dialog, "Threat").has_value());
    REQUIRE(findActionIndexByLabel(dialog, "Bribe 1 Gold").has_value());

    const OpenYAMM::Game::EventDialogContent normalDialog =
        harness.executeAndPresent(*findActionIndexByLabel(dialog, "Threat"));
    CHECK(findActionIndexByLabel(normalDialog, "Join").has_value());
    CHECK_FALSE(findActionIndexByLabel(normalDialog, "Threat").has_value());
    REQUIRE_FALSE(harness.eventRuntimeState().messages.empty());
    CHECK(harness.eventRuntimeState().messages.back().find("%11") == std::string::npos);
    CHECK(harness.eventRuntimeState().messages.back().find("%12") == std::string::npos);
}

TEST_CASE("random NPC BTB gate is disabled when merged continent does not affect NPC reputation")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    OpenYAMM::Game::MapStatsEntry map = {};
    map.mergedContinentId = 1;
    harness.setCurrentMap(map);
    harness.worldRuntime().setCurrentLocationReputation(10);

    constexpr uint32_t RandomPeasantNpcId = 20002;
    harness.eventRuntimeState().npcNameOverrides[RandomPeasantNpcId] = "Kevin";
    harness.eventRuntimeState().npcPictureOverrides[RandomPeasantNpcId] = 1;
    harness.eventRuntimeState().npcProfessionOverrides[RandomPeasantNpcId] = 52;

    const OpenYAMM::Game::EventDialogContent dialog = harness.openNpcDialogue(RandomPeasantNpcId);
    CHECK(findActionIndexByLabel(dialog, "Join").has_value());
    CHECK_FALSE(findActionIndexByLabel(dialog, "Beg").has_value());
    CHECK_FALSE(findActionIndexByLabel(dialog, "Threat").has_value());
    CHECK_FALSE(findActionIndexByLabel(dialog, "Bribe 1 Gold").has_value());
}

TEST_CASE("merged continent settings gate profession news fallback")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    harness.party().addGold(10000);

    constexpr uint32_t KyleLutvigChildNpcId = 810;

    OpenYAMM::Game::MapStatsEntry jadameMap = {};
    jadameMap.mergedContinentId = 1;
    harness.setCurrentMap(jadameMap);

    const OpenYAMM::Game::EventDialogContent jadameDialog = harness.openNpcDialogue(KyleLutvigChildNpcId);
    CHECK_FALSE(findActionIndexByLabel(jadameDialog, "Child").has_value());

    OpenYAMM::Game::MapStatsEntry betweenTimeMap = {};
    betweenTimeMap.mergedContinentId = 4;
    harness.setCurrentMap(betweenTimeMap);

    const OpenYAMM::Game::EventDialogContent betweenTimeDialog = harness.openNpcDialogue(KyleLutvigChildNpcId);
    CHECK(dialogHasAction(betweenTimeDialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionNews, "School"));
    CHECK_FALSE(
        dialogHasAction(betweenTimeDialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionAction, "Child"));
}

TEST_CASE("merged continent settings gate NPC follower offers")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    harness.party().addGold(10000);
    harness.worldRuntime().setCurrentLocationReputation(10);

    OpenYAMM::Game::MapStatsEntry betweenTimeMap = {};
    betweenTimeMap.mergedContinentId = 4;
    harness.setCurrentMap(betweenTimeMap);

    constexpr uint32_t RandomPeasantNpcId = 20003;
    harness.eventRuntimeState().npcNameOverrides[RandomPeasantNpcId] = "Kevin";
    harness.eventRuntimeState().npcPictureOverrides[RandomPeasantNpcId] = 1;
    harness.eventRuntimeState().npcProfessionOverrides[RandomPeasantNpcId] = 52;

    const OpenYAMM::Game::EventDialogContent dialog = harness.openNpcDialogue(RandomPeasantNpcId);
    CHECK_FALSE(findActionIndexByLabel(dialog, "Join").has_value());
    CHECK_FALSE(findActionIndexByLabel(dialog, "Beg").has_value());
    CHECK_FALSE(findActionIndexByLabel(dialog, "Threat").has_value());
    CHECK_FALSE(findActionIndexByLabel(dialog, "Bribe 1 Gold").has_value());
    CHECK(dialogHasAction(dialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionNews, "Temple of Baa"));
    CHECK_FALSE(dialogHasAction(dialog, OpenYAMM::Game::EventDialogActionKind::NpcProfessionAction, "Peasant"));
}

TEST_CASE("fredrick initial topics exact")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(FredrickHouseId);
    const std::vector<std::string> expectedLabels = {
        "Portals of Stone",
        "Cataclysm",
    };

    CHECK(collectActionLabels(dialog) == expectedLabels);
}

TEST_CASE("multi resident house selection")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(BrekishHallHouseId);

    CHECK_EQ(dialog.title, "Clan Leader's Hall");
    CHECK(dialogHasActionLabel(dialog, "Brekish Onefang"));
    CHECK(dialogHasActionLabel(dialog, "Dadeross"));
}

TEST_CASE("free haven high council residents")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(FreeHavenHighCouncilHouseId);
    const std::optional<size_t> prestonIndex = findActionIndexByLabel(dialog, "Preston Steel");
    const std::optional<size_t> toriIndex = findActionIndexByLabel(dialog, "Tori Goldman");
    const std::optional<size_t> isaacIndex = findActionIndexByLabel(dialog, "Isaac Rockwell");
    const std::optional<size_t> olafIndex = findActionIndexByLabel(dialog, "Olaf Heimdall");
    const std::optional<size_t> euclidIndex = findActionIndexByLabel(dialog, "Euclid Kepler");
    const std::optional<size_t> slickerIndex = findActionIndexByLabel(dialog, "Slicker Silvertongue");

    CHECK_EQ(dialog.title, "High Council");
    REQUIRE(prestonIndex.has_value());
    CHECK_EQ(dialog.actions[*prestonIndex].id, PrestonSteelNpcId);
    REQUIRE(toriIndex.has_value());
    CHECK_EQ(dialog.actions[*toriIndex].id, ToriGoldmanNpcId);
    REQUIRE(isaacIndex.has_value());
    CHECK_EQ(dialog.actions[*isaacIndex].id, IsaacRockwellNpcId);
    REQUIRE(olafIndex.has_value());
    CHECK_EQ(dialog.actions[*olafIndex].id, OlafHeimdallNpcId);
    REQUIRE(euclidIndex.has_value());
    CHECK_EQ(dialog.actions[*euclidIndex].id, EuclidKeplerNpcId);
    REQUIRE(slickerIndex.has_value());
    CHECK_EQ(dialog.actions[*slickerIndex].id, SlickerSilvertongueNpcId);
}

TEST_CASE("free haven high council is not a generic town hall service")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouse = gameData.houseTable.get(FreeHavenHighCouncilHouseId);
    REQUIRE(pHouse != nullptr);
    REQUIRE(pHouse->extraExit.has_value());
    CHECK_EQ(pHouse->extraExit->destinationMapFileName, "oracle.blv");
    CHECK(pHouse->extraExit->useMapStartPosition);

    const std::vector<OpenYAMM::Game::HouseActionOption> lockedActions =
        OpenYAMM::Game::buildHouseActionOptions(
            *pHouse,
            &harness.party(),
            &gameData.classSkillTable,
            &harness.worldRuntime(),
            harness.worldRuntime().gameMinutes(),
            OpenYAMM::Game::DialogueMenuId::None);

    CHECK_FALSE(findHouseActionById(lockedActions, OpenYAMM::Game::HouseActionId::TownHallCurrentFine).has_value());
    CHECK_FALSE(findHouseActionById(lockedActions, OpenYAMM::Game::HouseActionId::TownHallPayFine).has_value());
    CHECK_FALSE(findHouseActionById(lockedActions, OpenYAMM::Game::HouseActionId::TownHallBountyHunt).has_value());
    CHECK_FALSE(findHouseActionById(lockedActions, OpenYAMM::Game::HouseActionId::ExtraExit).has_value());

    harness.party().setQuestBit(1191, true);
    const std::vector<OpenYAMM::Game::HouseActionOption> unlockedActions =
        OpenYAMM::Game::buildHouseActionOptions(
            *pHouse,
            &harness.party(),
            &gameData.classSkillTable,
            &harness.worldRuntime(),
            harness.worldRuntime().gameMinutes(),
            OpenYAMM::Game::DialogueMenuId::None);

    CHECK_FALSE(findHouseActionById(unlockedActions, OpenYAMM::Game::HouseActionId::TownHallCurrentFine).has_value());
    CHECK_FALSE(findHouseActionById(unlockedActions, OpenYAMM::Game::HouseActionId::TownHallPayFine).has_value());
    CHECK_FALSE(findHouseActionById(unlockedActions, OpenYAMM::Game::HouseActionId::TownHallBountyHunt).has_value());
    CHECK(findHouseActionById(unlockedActions, OpenYAMM::Game::HouseActionId::ExtraExit).has_value());

    const OpenYAMM::Game::EventDialogContent &unexposedDialog =
        harness.openHouseDialog(FreeHavenHighCouncilHouseId);
    REQUIRE_EQ(unexposedDialog.actions.size(), 6u);
    CHECK_FALSE(dialogHasActionLabel(unexposedDialog, "Enter"));
    CHECK_FALSE(dialogHasActionLabel(unexposedDialog, "Current Fine: 0 gold"));
    CHECK_FALSE(dialogHasActionLabel(unexposedDialog, "Pay Fine"));
    CHECK_FALSE(dialogHasActionLabel(unexposedDialog, "Bounty Hunt"));
    for (const OpenYAMM::Game::EventDialogAction &action : unexposedDialog.actions)
    {
        CHECK_EQ(action.kind, OpenYAMM::Game::EventDialogActionKind::HouseResident);
    }

    OpenYAMM::Tests::HouseDialogueTestHarness exposedHarness(gameData);
    exposedHarness.party().setQuestBit(1191, true);
    exposedHarness.eventRuntimeState().npcHouseOverrides[SlickerSilvertongueNpcId] = 0;
    const OpenYAMM::Game::EventDialogContent &exposedDialog =
        exposedHarness.openHouseDialog(FreeHavenHighCouncilHouseId);
    REQUIRE_EQ(exposedDialog.actions.size(), 6u);
    CHECK_FALSE(dialogHasActionLabel(exposedDialog, "Current Fine: 0 gold"));
    CHECK_FALSE(dialogHasActionLabel(exposedDialog, "Pay Fine"));
    CHECK_FALSE(dialogHasActionLabel(exposedDialog, "Bounty Hunt"));

    std::optional<size_t> oracleDoorIndex;
    size_t residentCount = 0;
    for (size_t actionIndex = 0; actionIndex < exposedDialog.actions.size(); ++actionIndex)
    {
        const OpenYAMM::Game::EventDialogAction &action = exposedDialog.actions[actionIndex];
        if (action.kind == OpenYAMM::Game::EventDialogActionKind::HouseResident)
        {
            ++residentCount;
        }
        else if (action.kind == OpenYAMM::Game::EventDialogActionKind::HouseExtraExit)
        {
            oracleDoorIndex = actionIndex;
        }
    }

    CHECK_EQ(residentCount, 5u);
    REQUIRE(oracleDoorIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &oracleDoorDialog =
        exposedHarness.executeAndPresent(*oracleDoorIndex);
    const std::optional<size_t> enterIndex = findActionIndexByLabel(oracleDoorDialog, "Enter");
    REQUIRE(enterIndex.has_value());
    CHECK_FALSE(dialogHasActionLabel(oracleDoorDialog, "Current Fine: 0 gold"));
    CHECK_FALSE(dialogHasActionLabel(oracleDoorDialog, "Pay Fine"));
    CHECK_FALSE(dialogHasActionLabel(oracleDoorDialog, "Bounty Hunt"));

    exposedHarness.executeAndPresent(*enterIndex);
    REQUIRE(exposedHarness.eventRuntimeState().pendingMapMove.has_value());
    CHECK_EQ(exposedHarness.eventRuntimeState().pendingMapMove->mapName, std::optional<std::string>("oracle.blv"));
    CHECK(exposedHarness.eventRuntimeState().pendingMapMove->useMapStartPosition);
}

TEST_CASE("sandro thant throne room residents")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(SandroThantThroneRoomHouseId);
    const std::optional<size_t> sandroIndex = findActionIndexByLabel(dialog, "Sandro");
    const std::optional<size_t> thantIndex = findActionIndexByLabel(dialog, "Thant");

    CHECK_EQ(dialog.title, "Sandro/Thant's Throne Room");
    REQUIRE(sandroIndex.has_value());
    CHECK_EQ(dialog.actions[*sandroIndex].id, SandroNpcId);
    REQUIRE(thantIndex.has_value());
    CHECK_EQ(dialog.actions[*thantIndex].id, ThantNpcId);
    CHECK_FALSE(dialogHasActionLabel(dialog, "Brekish Onefang"));
}

TEST_CASE("throne room sentence clears fines without hiding residents by default")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &normalDialog =
        harness.openHouseDialog(SandroThantThroneRoomHouseId);
    CHECK_FALSE(findActionIndexByLabel(normalDialog, "Serve Sentence").has_value());
    CHECK(findActionIndexByLabel(normalDialog, "Sandro").has_value());
    CHECK(findActionIndexByLabel(normalDialog, "Thant").has_value());

    harness.party().addFineGold(2500);
    const float beforeMinutes = harness.worldRuntime().gameMinutes();
    const OpenYAMM::Game::EventDialogContent &fineDialog =
        harness.openHouseDialog(SandroThantThroneRoomHouseId);
    const std::optional<size_t> serveSentenceIndex = findActionIndexByLabel(fineDialog, "Serve Sentence");
    REQUIRE(serveSentenceIndex.has_value());

    harness.executeAndPresent(*serveSentenceIndex);

    CHECK_EQ(harness.party().fineGold(), 0);
    CHECK_EQ(
        harness.party().eventVariableValue(
            static_cast<uint16_t>(OpenYAMM::Game::EvtVariable::PrisonTerms)),
        1);
    CHECK(harness.party().hasAward(87));
    CHECK_EQ(harness.worldRuntime().gameMinutes(), beforeMinutes + 365.0f * 24.0f * 60.0f);
}

TEST_CASE("relocated thant is silent after necromancer alliance")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    harness.eventRuntimeState().npcHouseOverrides[SandroNpcId] = 0;
    harness.eventRuntimeState().npcHouseOverrides[ThantNpcId] = 0;
    harness.eventRuntimeState().npcHouseOverrides[RelocatedThantNpcId] = SandroThantThroneRoomHouseId;

    const OpenYAMM::Game::EventDialogContent &thantDialog =
        harness.openHouseDialog(SandroThantThroneRoomHouseId);

    CHECK_EQ(thantDialog.title, "Thant");
    CHECK_EQ(thantDialog.sourceId, RelocatedThantNpcId);
    CHECK(thantDialog.lines.empty());
    CHECK(thantDialog.actions.empty());
}

TEST_CASE("global npc move populates overdune house after changing maps")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.executeGlobalEvent(42));
    harness.eventRuntimeState() = {};

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(OverduneHouseId);

    CHECK_EQ(dialog.title, "Overdune's House");
    CHECK(dialogHasActionLabel(dialog, "Overdune Snapfinger"));
    CHECK(dialogHasActionLabel(dialog, "Farhill Snapfinger"));
}

TEST_CASE("brekish topic mutation")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &hallDialog = harness.openHouseDialog(BrekishHallHouseId);
    const std::optional<size_t> brekishIndex = findActionIndexByLabel(hallDialog, "Brekish Onefang");

    REQUIRE(brekishIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &brekishDialog = harness.executeAndPresent(*brekishIndex);
    const std::optional<size_t> portalsIndex = findActionIndexByLabel(brekishDialog, "Portals of Stone");

    REQUIRE(portalsIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &updatedDialog = harness.executeAndPresent(*portalsIndex);

    CHECK(dialogHasActionLabel(updatedDialog, "Quest"));
}

TEST_CASE("fredrick topics after brekish quest")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    advanceBrekishQuest(harness);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(FredrickHouseId);

    CHECK(dialogHasActionLabel(dialog, "Power Stone"));
    CHECK(dialogHasActionLabel(dialog, "Abandoned Temple"));
}

TEST_CASE("fredrick topics exact after brekish quest")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    advanceBrekishQuest(harness);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(FredrickHouseId);
    const std::vector<std::string> expectedLabels = {
        "Portals of Stone",
        "Cataclysm",
        "Power Stone",
        "Abandoned Temple",
    };

    CHECK(collectActionLabels(dialog) == expectedLabels);
}

TEST_CASE("award gated topic stephen")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    OpenYAMM::Game::EventDialogContent dialog = harness.openNpcDialogue(StephenNpcId);
    CHECK(dialogHasActionLabel(dialog, "Clues"));

    harness.party().addAward(30);
    dialog = harness.openNpcDialogue(StephenNpcId);
    CHECK(dialogHasActionLabel(dialog, "Clues"));

    harness.party().removeAward(30);
    harness.party().addAward(31);
    dialog = harness.openNpcDialogue(StephenNpcId);
    CHECK_FALSE(dialogHasActionLabel(dialog, "Clues"));

    harness.party().removeAward(31);
    dialog = harness.openNpcDialogue(StephenNpcId);
    CHECK(dialogHasActionLabel(dialog, "Clues"));
}

TEST_CASE("hiss quest followup persists across reentry")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(HissHouseId);
    const std::optional<size_t> questIndex = findActionIndexByLabel(dialog, "Quest");

    REQUIRE(questIndex.has_value());
    harness.executeAndPresent(*questIndex);

    harness.uiController().clearEventDialog();
    harness.eventRuntimeState().pendingDialogueContext.reset();
    harness.eventRuntimeState().dialogueState = {};
    harness.eventRuntimeState().messages.clear();

    const OpenYAMM::Game::EventDialogContent &reenteredDialog = harness.openHouseDialog(HissHouseId);
    const std::optional<size_t> idolIndex = findActionIndexByLabel(reenteredDialog, "Do you have the Idol?");

    REQUIRE(idolIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &followupDialog = harness.executeAndPresent(*idolIndex);

    CHECK(dialogContainsText(followupDialog, "Where is the Idol?"));
}

TEST_CASE("dwi shop service menu structure")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &rootDialog = harness.openHouseDialog(1);

    CHECK(dialogHasActionLabel(rootDialog, "Buy Standard"));
    CHECK(dialogHasActionLabel(rootDialog, "Buy Special"));
    CHECK(dialogHasActionLabel(rootDialog, "Display Equipment"));
    CHECK(dialogHasActionLabel(rootDialog, "Learn Skills"));

    const std::optional<size_t> equipmentIndex = findActionIndexByLabel(rootDialog, "Display Equipment");
    REQUIRE(equipmentIndex.has_value());

    const OpenYAMM::Game::EventDialogContent &equipmentDialog = harness.executeAndPresent(*equipmentIndex);

    CHECK(dialogHasActionLabel(equipmentDialog, "Sell"));
    CHECK(dialogHasActionLabel(equipmentDialog, "Identify"));
    CHECK(dialogHasActionLabel(equipmentDialog, "Repair"));

    const std::optional<size_t> sellIndex = findActionIndexByLabel(equipmentDialog, "Sell");
    const std::optional<size_t> identifyIndex = findActionIndexByLabel(equipmentDialog, "Identify");
    const std::optional<size_t> repairIndex = findActionIndexByLabel(equipmentDialog, "Repair");

    REQUIRE(sellIndex.has_value());
    REQUIRE(identifyIndex.has_value());
    REQUIRE(repairIndex.has_value());
    CHECK(equipmentDialog.actions[*sellIndex].enabled);
    CHECK(equipmentDialog.actions[*identifyIndex].enabled);
    CHECK(equipmentDialog.actions[*repairIndex].enabled);
}

TEST_CASE("house service shop standard stock generates and buys")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(1);
    REQUIRE(pHouseEntry != nullptr);

    harness.party().addGold(50000);
    const std::vector<OpenYAMM::Game::InventoryItem> &stock = OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::HouseStockMode::ShopStandard);
    const auto stockIt =
        std::find_if(stock.begin(), stock.end(), [](const OpenYAMM::Game::InventoryItem &item)
    {
        return item.objectDescriptionId != 0;
    });

    REQUIRE(stockIt != stock.end());
    const size_t slotIndex = static_cast<size_t>(std::distance(stock.begin(), stockIt));
    const int initialGold = harness.party().gold();
    const size_t initialInventoryCount = harness.party().inventoryItemCount();
    std::string statusText;

    REQUIRE(OpenYAMM::Game::HouseServiceRuntime::tryBuyStockItem(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::HouseStockMode::ShopStandard,
        slotIndex,
        statusText));
    CHECK_LT(harness.party().gold(), initialGold);
    CHECK_GT(harness.party().inventoryItemCount(), initialInventoryCount);
}

TEST_CASE("house service shop stock uses merged house rules")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(1);
    REQUIRE(pHouseEntry != nullptr);

    CHECK_EQ(pHouseEntry->standardStockTier, 1);
    CHECK_EQ(pHouseEntry->specialStockTier, 2);
    CHECK_EQ(pHouseEntry->standardStockRule.quality, 1);
    CHECK_EQ(pHouseEntry->standardStockRule.itemTypes, std::vector<uint32_t>{23, 27, 25, 20});
    CHECK_EQ(pHouseEntry->specialStockRule.quality, 2);
    CHECK_EQ(pHouseEntry->specialStockRule.itemTypes, std::vector<uint32_t>{28, 30, 26, 20});

    const std::vector<OpenYAMM::Game::InventoryItem> &standardStock = OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::HouseStockMode::ShopStandard);
    const std::vector<OpenYAMM::Game::InventoryItem> &specialStock = OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::HouseStockMode::ShopSpecial);

    for (const OpenYAMM::Game::InventoryItem &item : standardStock)
    {
        if (item.objectDescriptionId == 0)
        {
            continue;
        }

        const OpenYAMM::Game::ItemDefinition *pItemDefinition = gameData.itemTable.get(item.objectDescriptionId);
        REQUIRE(pItemDefinition != nullptr);
        CHECK_LE(firstTreasureLevelForItem(*pItemDefinition), pHouseEntry->standardStockTier);
    }

    for (const OpenYAMM::Game::InventoryItem &item : specialStock)
    {
        if (item.objectDescriptionId == 0)
        {
            continue;
        }

        const OpenYAMM::Game::ItemDefinition *pItemDefinition = gameData.itemTable.get(item.objectDescriptionId);
        REQUIRE(pItemDefinition != nullptr);
        CHECK(itemHasTreasureWeightAtOrAboveTier(*pItemDefinition, pHouseEntry->specialStockTier));
    }
}

TEST_CASE("house service shop stock excludes rare items")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(1);
    REQUIRE(pHouseEntry != nullptr);

    const auto validateStock =
        [&](const std::vector<OpenYAMM::Game::InventoryItem> &stock)
    {
        for (const OpenYAMM::Game::InventoryItem &item : stock)
        {
            if (item.objectDescriptionId == 0)
            {
                continue;
            }

            const OpenYAMM::Game::ItemDefinition *pItemDefinition = gameData.itemTable.get(item.objectDescriptionId);
            REQUIRE(pItemDefinition != nullptr);
            CHECK(pItemDefinition->rarity == OpenYAMM::Game::ItemRarity::Common);
        }
    };

    const std::vector<OpenYAMM::Game::InventoryItem> &standardStock = OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::HouseStockMode::ShopStandard);
    const std::vector<OpenYAMM::Game::InventoryItem> &specialStock = OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::HouseStockMode::ShopSpecial);

    validateStock(standardStock);
    validateStock(specialStock);
}

TEST_CASE("house service guild spellbook stock generates and buys")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(139);
    REQUIRE(pHouseEntry != nullptr);

    harness.party().addGold(50000);
    const std::vector<OpenYAMM::Game::InventoryItem> &stock = OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::HouseStockMode::GuildSpellbooks);
    const auto stockIt =
        std::find_if(stock.begin(), stock.end(), [](const OpenYAMM::Game::InventoryItem &item)
    {
        return item.objectDescriptionId != 0;
    });

    REQUIRE(stockIt != stock.end());
    const OpenYAMM::Game::ItemDefinition *pSpellbook = gameData.itemTable.get(stockIt->objectDescriptionId);
    REQUIRE(pSpellbook != nullptr);
    CHECK_EQ(pSpellbook->equipStat, "Book");

    const size_t slotIndex = static_cast<size_t>(std::distance(stock.begin(), stockIt));
    const size_t initialInventoryCount = harness.party().inventoryItemCount();
    std::string statusText;

    REQUIRE(OpenYAMM::Game::HouseServiceRuntime::tryBuyStockItem(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::HouseStockMode::GuildSpellbooks,
        slotIndex,
        statusText));
    CHECK_GT(harness.party().inventoryItemCount(), initialInventoryCount);
}

TEST_CASE("house service shop sell accepts matching item")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(1);
    REQUIRE(pHouseEntry != nullptr);

    std::optional<uint32_t> sellableItemId;

    for (const OpenYAMM::Game::ItemDefinition &itemDefinition : gameData.itemTable.entries())
    {
        if (itemDefinition.itemId == 0)
        {
            continue;
        }

        OpenYAMM::Game::InventoryItem candidate = {};
        candidate.objectDescriptionId = itemDefinition.itemId;
        candidate.quantity = 1;
        candidate.width = itemDefinition.inventoryWidth;
        candidate.height = itemDefinition.inventoryHeight;

        if (OpenYAMM::Game::HouseServiceRuntime::canSellItemToHouse(gameData.itemTable, *pHouseEntry, candidate))
        {
            sellableItemId = itemDefinition.itemId;
            break;
        }
    }

    REQUIRE(sellableItemId.has_value());
    REQUIRE(harness.party().grantItemToMember(harness.party().activeMemberIndex(), *sellableItemId, 1));

    const OpenYAMM::Game::Character *pMember = harness.party().activeMember();
    REQUIRE(pMember != nullptr);

    std::optional<std::pair<uint8_t, uint8_t>> matchingCell;

    for (const OpenYAMM::Game::InventoryItem &item : pMember->inventory)
    {
        if (item.objectDescriptionId == *sellableItemId)
        {
            matchingCell = std::pair<uint8_t, uint8_t>(item.gridX, item.gridY);
            break;
        }
    }

    REQUIRE(matchingCell.has_value());
    const int initialGold = harness.party().gold();
    const size_t initialInventoryCount = harness.party().inventoryItemCount();
    std::string statusText;

    REQUIRE(OpenYAMM::Game::HouseServiceRuntime::trySellInventoryItem(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.party().activeMemberIndex(),
        matchingCell->first,
        matchingCell->second,
        statusText));
    CHECK_GT(harness.party().gold(), initialGold);
    CHECK_LT(harness.party().inventoryItemCount(), initialInventoryCount);
}

TEST_CASE("dwi temple service participant identity")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(TempleHouseId);

    CHECK_EQ(dialog.houseTitle, "Mystic Medicine");
    CHECK_EQ(dialog.title, "Pish, Healer");
    CHECK_EQ(dialog.participantPictureId, 1130u);
}

TEST_CASE("dwi temple proprietor portrait uses mm8 overlay icon")
{
    const std::filesystem::path sourceRoot = std::filesystem::path(OPENYAMM_SOURCE_DIR);
    const std::filesystem::path worldPortrait =
        sourceRoot / "assets_dev/worlds/mm8/icons/npc1130.bmp";
    const std::filesystem::path uppercaseWorldPortrait =
        sourceRoot / "assets_dev/worlds/mm8/icons/NPC1130.bmp";
    const std::filesystem::path enginePortrait =
        sourceRoot / "assets_dev/engine/icons/npc1130.bmp";
    const std::filesystem::path uppercaseEnginePortrait =
        sourceRoot / "assets_dev/engine/icons/NPC1130.bmp";

    REQUIRE(std::filesystem::exists(worldPortrait));
    CHECK_FALSE(std::filesystem::exists(uppercaseWorldPortrait));
    CHECK_FALSE(std::filesystem::exists(enginePortrait));
    CHECK_FALSE(std::filesystem::exists(uppercaseEnginePortrait));

    const std::filesystem::perms portraitPermissions = std::filesystem::status(worldPortrait).permissions();
    CHECK_EQ(
        portraitPermissions & std::filesystem::perms::all,
        std::filesystem::perms::owner_read
            | std::filesystem::perms::owner_write
            | std::filesystem::perms::group_read
            | std::filesystem::perms::others_read);

    CHECK_EQ(fnv1a64(readBinaryFileBytes(worldPortrait)), 0xc2f7b93995f0bd00ull);
}

TEST_CASE("dwi temple skill learning")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(1));
    harness.party().addGold(2000);
    const int initialGold = harness.party().gold();

    const OpenYAMM::Game::EventDialogContent &rootDialog = harness.openHouseDialog(TempleHouseId);
    const std::optional<size_t> learnSkillsIndex = findActionIndexByLabel(rootDialog, "Learn Skills");

    REQUIRE(learnSkillsIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &skillDialog = harness.executeAndPresent(*learnSkillsIndex);
    const std::optional<size_t> merchantIndex = findActionIndexByLabelPrefix(skillDialog, "Learn Merchant ");

    REQUIRE(merchantIndex.has_value());
    harness.executeAndPresent(*merchantIndex);

    const OpenYAMM::Game::Character *pCleric = harness.party().member(1);
    REQUIRE(pCleric != nullptr);
    CHECK(pCleric->hasSkill("Merchant"));
    CHECK_LT(harness.party().gold(), initialGold);
}

TEST_CASE("temple healing restores active member to effective resource maximums")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pTempleHouse = gameData.houseTable.get(TempleHouseId);

    REQUIRE(pTempleHouse != nullptr);

    harness.party().addGold(1000);
    OpenYAMM::Game::Character *pMember = harness.party().activeMember();
    REQUIRE(pMember != nullptr);
    pMember->maxHealth = 80;
    pMember->health = 80;
    pMember->maxSpellPoints = 60;
    pMember->spellPoints = 60;
    pMember->magicalBonuses.maxHealth = 30;
    pMember->magicalBonuses.maxSpellPoints = 15;

    const std::vector<OpenYAMM::Game::HouseActionOption> actions = OpenYAMM::Game::buildHouseActionOptions(
        *pTempleHouse,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        0.0f,
        OpenYAMM::Game::DialogueMenuId::None);
    const std::optional<OpenYAMM::Game::HouseActionOption> healAction =
        findHouseActionById(actions, OpenYAMM::Game::HouseActionId::TempleHeal);

    REQUIRE(healAction.has_value());

    const OpenYAMM::Game::HouseActionResult result = OpenYAMM::Game::performHouseAction(
        *healAction,
        *pTempleHouse,
        harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime());

    CHECK(result.succeeded);
    pMember = harness.party().activeMember();
    REQUIRE(pMember != nullptr);
    CHECK_EQ(pMember->health, 110);
    CHECK_EQ(pMember->spellPoints, 75);
}

TEST_CASE("temple healing price uses condition age and house multiplier")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pTempleHouse = gameData.houseTable.get(TempleHouseId);

    REQUIRE(pTempleHouse != nullptr);

    OpenYAMM::Game::Character *pMember = harness.party().activeMember();
    REQUIRE(pMember != nullptr);
    pMember->maxHealth = 80;
    pMember->health = 60;
    pMember->maxSpellPoints = 20;
    pMember->spellPoints = 20;

    std::vector<OpenYAMM::Game::HouseActionOption> actions = OpenYAMM::Game::buildHouseActionOptions(
        *pTempleHouse,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);
    std::optional<OpenYAMM::Game::HouseActionOption> healAction =
        findHouseActionById(actions, OpenYAMM::Game::HouseActionId::TempleHeal);

    REQUIRE(healAction.has_value());
    CHECK_EQ(healAction->label, "Heal 10 gold");

    harness.worldRuntime().advanceGameMinutes(10.0f * 24.0f * 60.0f);
    pMember->health = pMember->maxHealth;
    const size_t deadIndex = static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Dead);
    pMember->conditions.set(deadIndex);
    pMember->conditionStartGameMinutes[deadIndex] =
        harness.worldRuntime().gameMinutes() - 2.0f * 24.0f * 60.0f;

    actions = OpenYAMM::Game::buildHouseActionOptions(
        *pTempleHouse,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);
    healAction = findHouseActionById(actions, OpenYAMM::Game::HouseActionId::TempleHeal);

    REQUIRE(healAction.has_value());
    CHECK_EQ(healAction->label, "Heal 150 gold");
}

TEST_CASE("event-applied conditions use absolute game time for temple healing price")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pTempleHouse = gameData.houseTable.get(TempleHouseId);

    REQUIRE(pTempleHouse != nullptr);

    constexpr float OneYearMinutes = 12.0f * 28.0f * 24.0f * 60.0f;
    harness.worldRuntime().advanceGameMinutes(OneYearMinutes);

    OpenYAMM::Game::Character *pMember = harness.party().activeMember();
    REQUIRE(pMember != nullptr);
    pMember->health = pMember->maxHealth;
    pMember->spellPoints = pMember->maxSpellPoints;

    harness.eventRuntimeState().variables[static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::Hour)] = 12;
    harness.eventRuntimeState().variables[static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::DayOfYear)] = 1;
    TempleConditionTimeSceneContext sceneContext(harness.worldRuntime().gameMinutes());
    const OpenYAMM::Game::EventRuntime::VariableRef weakVariable =
        OpenYAMM::Game::EventRuntime::decodeVariable(
            static_cast<uint32_t>(OpenYAMM::Game::EvtVariable::Weak));

    OpenYAMM::Game::EventRuntime::setVariableValue(
        harness.eventRuntimeState(),
        weakVariable,
        1,
        &harness.party(),
        {harness.party().activeMemberIndex()},
        &sceneContext);

    std::vector<OpenYAMM::Game::HouseActionOption> actions = OpenYAMM::Game::buildHouseActionOptions(
        *pTempleHouse,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);
    const std::optional<OpenYAMM::Game::HouseActionOption> healAction =
        findHouseActionById(actions, OpenYAMM::Game::HouseActionId::TempleHeal);

    REQUIRE(healAction.has_value());
    CHECK_EQ(healAction->label, "Heal 10 gold");
}

TEST_CASE("mm6 temple healing tier limits serious condition treatment")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pNewSorpigalTemple = gameData.houseTable.get(NewSorpigalTempleHouseId);
    const OpenYAMM::Game::HouseEntry *pFreeHavenTempleStone = gameData.houseTable.get(FreeHavenTempleStoneHouseId);
    const OpenYAMM::Game::HouseEntry *pFreeHavenTemple = gameData.houseTable.get(FreeHavenTempleHouseId);
    const OpenYAMM::Game::HouseEntry *pBlackshireTemple = gameData.houseTable.get(BlackshireTempleHouseId);

    REQUIRE(pNewSorpigalTemple != nullptr);
    REQUIRE(pFreeHavenTempleStone != nullptr);
    REQUIRE(pFreeHavenTemple != nullptr);
    REQUIRE(pBlackshireTemple != nullptr);
    CHECK_EQ(pNewSorpigalTemple->templeHealingTier, doctest::Approx(2.0f));
    CHECK_EQ(pFreeHavenTempleStone->templeHealingTier, doctest::Approx(2.5f));
    CHECK_EQ(OpenYAMM::Game::resolveHouseServiceType(*pFreeHavenTemple), OpenYAMM::Game::HouseServiceType::None);
    CHECK_EQ(pBlackshireTemple->templeHealingTier, doctest::Approx(2.5f));

    OpenYAMM::Game::Character *pMember = harness.party().activeMember();
    REQUIRE(pMember != nullptr);
    const size_t deadIndex = static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Dead);
    const size_t eradicatedIndex = static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Eradicated);

    pMember->conditions.set(deadIndex);
    pMember->conditionStartGameMinutes[deadIndex] = harness.worldRuntime().gameMinutes();

    std::vector<OpenYAMM::Game::HouseActionOption> actions = OpenYAMM::Game::buildHouseActionOptions(
        *pNewSorpigalTemple,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);
    CHECK(findHouseActionById(actions, OpenYAMM::Game::HouseActionId::TempleHeal).has_value());

    pMember->conditions.reset();
    pMember->conditionStartGameMinutes.fill(0.0f);
    pMember->conditions.set(eradicatedIndex);
    pMember->conditionStartGameMinutes[eradicatedIndex] = harness.worldRuntime().gameMinutes();

    actions = OpenYAMM::Game::buildHouseActionOptions(
        *pNewSorpigalTemple,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);
    CHECK_FALSE(findHouseActionById(actions, OpenYAMM::Game::HouseActionId::TempleHeal).has_value());

    actions = OpenYAMM::Game::buildHouseActionOptions(
        *pFreeHavenTempleStone,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);
    CHECK(findHouseActionById(actions, OpenYAMM::Game::HouseActionId::TempleHeal).has_value());

    actions = OpenYAMM::Game::buildHouseActionOptions(
        *pFreeHavenTemple,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);
    CHECK_FALSE(findHouseActionById(actions, OpenYAMM::Game::HouseActionId::TempleHeal).has_value());
    CHECK_FALSE(findHouseActionById(actions, OpenYAMM::Game::HouseActionId::TempleDonate).has_value());
    CHECK_FALSE(findHouseActionById(actions, OpenYAMM::Game::HouseActionId::OpenLearnSkillsMenu).has_value());

    actions = OpenYAMM::Game::buildHouseActionOptions(
        *pBlackshireTemple,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);
    CHECK(findHouseActionById(actions, OpenYAMM::Game::HouseActionId::TempleHeal).has_value());
}

TEST_CASE("dwi guild skill learning")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(3));
    harness.party().addGold(2000);

    const OpenYAMM::Game::EventDialogContent &rootDialog = harness.openHouseDialog(ElementalGuildHouseId);

    CHECK(dialogHasActionLabel(rootDialog, "Buy Spellbooks"));
    CHECK(dialogHasActionLabel(rootDialog, "Learn Skills"));

    const std::optional<size_t> learnSkillsIndex = findActionIndexByLabel(rootDialog, "Learn Skills");
    REQUIRE(learnSkillsIndex.has_value());

    const OpenYAMM::Game::EventDialogContent &skillDialog = harness.executeAndPresent(*learnSkillsIndex);
    const std::optional<size_t> airMagicIndex = findActionIndexByLabelPrefix(skillDialog, "Learn Air Magic ");

    REQUIRE(airMagicIndex.has_value());
    harness.executeAndPresent(*airMagicIndex);

    const OpenYAMM::Game::Character *pSorcerer = harness.party().member(3);
    REQUIRE(pSorcerer != nullptr);
    CHECK(pSorcerer->hasSkill("AirMagic"));
}

TEST_CASE("mm6 skill guilds require membership and expose learning only")
{
    constexpr uint16_t BuccaneersLairMembershipVariable = 0x8010u;

    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::HouseEntry *pBuccaneersLair =
        gameData.houseTable.get(BuccaneersLairHouseId);
    REQUIRE(pBuccaneersLair != nullptr);
    CHECK_EQ(OpenYAMM::Game::resolveHouseServiceType(*pBuccaneersLair), OpenYAMM::Game::HouseServiceType::Guild);
    CHECK(std::find(
        pBuccaneersLair->offeredSkills.begin(),
        pBuccaneersLair->offeredSkills.end(),
        "Stealing") != pBuccaneersLair->offeredSkills.end());

    const std::vector<OpenYAMM::Game::HouseActionOption> nonMemberActions =
        OpenYAMM::Game::buildHouseActionOptions(
            *pBuccaneersLair,
            &harness.party(),
            &gameData.classSkillTable,
            &harness.worldRuntime(),
            18.0f * 60.0f,
            OpenYAMM::Game::DialogueMenuId::None);
    const std::optional<OpenYAMM::Game::HouseActionOption> blockedLearn =
        findHouseActionById(nonMemberActions, OpenYAMM::Game::HouseActionId::OpenLearnSkillsMenu);
    const std::vector<std::string> nonMemberLines =
        OpenYAMM::Game::buildHouseServiceInfoLines(
            *pBuccaneersLair,
            &harness.party(),
            &gameData.classSkillTable,
            OpenYAMM::Game::DialogueMenuId::None);

    REQUIRE(blockedLearn.has_value());
    CHECK_FALSE(blockedLearn->enabled);
    CHECK(std::find(
        nonMemberLines.begin(),
        nonMemberLines.end(),
        "You must be a member of this guild to study here.") != nonMemberLines.end());
    CHECK_FALSE(findHouseActionById(nonMemberActions, OpenYAMM::Game::HouseActionId::GuildBuySpellbooks).has_value());

    harness.party().setEventVariableValue(BuccaneersLairMembershipVariable, 1);
    const std::vector<OpenYAMM::Game::HouseActionOption> memberActions =
        OpenYAMM::Game::buildHouseActionOptions(
            *pBuccaneersLair,
            &harness.party(),
            &gameData.classSkillTable,
            &harness.worldRuntime(),
            18.0f * 60.0f,
            OpenYAMM::Game::DialogueMenuId::None);
    const std::optional<OpenYAMM::Game::HouseActionOption> learn =
        findHouseActionById(memberActions, OpenYAMM::Game::HouseActionId::OpenLearnSkillsMenu);

    REQUIRE(learn.has_value());
    CHECK(learn->enabled);
    CHECK_FALSE(findHouseActionById(memberActions, OpenYAMM::Game::HouseActionId::GuildBuySpellbooks).has_value());

    const OpenYAMM::Game::HouseEntry *pBerserkersFury =
        gameData.houseTable.get(BerserkersFuryHouseId);
    REQUIRE(pBerserkersFury != nullptr);
    CHECK(std::find(
        pBerserkersFury->offeredSkills.begin(),
        pBerserkersFury->offeredSkills.end(),
        "Armsmaster") != pBerserkersFury->offeredSkills.end());
}

TEST_CASE("dwi training service uses active member")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    OpenYAMM::Game::Character *pActiveMember = harness.party().activeMember();
    REQUIRE(pActiveMember != nullptr);
    pActiveMember->experience = 50000;

    const OpenYAMM::Game::EventDialogContent &initialDialog = harness.openHouseDialog(TrainingHallHouseId);
    CHECK(findActionIndexByLabelPrefix(initialDialog, "Train to level ").has_value());

    REQUIRE(harness.party().setActiveMemberIndex(1));
    OpenYAMM::Game::Character *pCleric = harness.party().activeMember();
    REQUIRE(pCleric != nullptr);
    pCleric->experience = 50000;

    const OpenYAMM::Game::EventDialogContent &refreshedDialog = harness.refreshCurrentHouseDialog();
    CHECK(findActionIndexByLabelPrefix(refreshedDialog, "Train to level ").has_value());
}

TEST_CASE("dwi training service applies merchant discount")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::HouseEntry *pTrainingHall = gameData.houseTable.get(TrainingHallHouseId);
    REQUIRE(pTrainingHall != nullptr);

    OpenYAMM::Game::Character *pMember = harness.party().activeMember();
    REQUIRE(pMember != nullptr);
    pMember->level = 4;
    pMember->experience = 10000;
    pMember->skills.erase("Merchant");

    const int undiscountedPrice = OpenYAMM::Game::PriceCalculator::trainingPrice(pMember, *pTrainingHall);
    REQUIRE(setCharacterSkill(*pMember, "Merchant", 10, OpenYAMM::Game::SkillMastery::Normal) != nullptr);

    const int discountedPrice = OpenYAMM::Game::PriceCalculator::trainingPrice(pMember, *pTrainingHall);
    CHECK_LT(discountedPrice, undiscountedPrice);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(TrainingHallHouseId);
    CHECK(findActionIndexByLabelPrefix(dialog, "Train to level 5 for ").has_value());
}

TEST_CASE("dwi training service stays open after success")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    OpenYAMM::Game::Character *pMember = harness.party().activeMember();
    REQUIRE(pMember != nullptr);
    pMember->experience = 50000;
    harness.party().addGold(1000);

    OpenYAMM::Game::Character *pOtherMember = harness.party().member(1);
    REQUIRE(pOtherMember != nullptr);
    pOtherMember->health = 1;
    pOtherMember->spellPoints = 0;

    const float initialGameMinutes = harness.worldRuntime().gameMinutes();
    const int initialMinuteOfDay = static_cast<int>(initialGameMinutes) % (24 * 60);
    int minutesUntilDawn = 5 * 60 - initialMinuteOfDay;
    if (minutesUntilDawn <= 0)
    {
        minutesUntilDawn += 24 * 60;
    }
    const float expectedTrainingMinutes = 7.0f * 24.0f * 60.0f
        + static_cast<float>(minutesUntilDawn)
        + 4.0f * 60.0f;
    const uint32_t expectedLevel = pMember->level + 1;
    const uint32_t expectedSkillPoints = 5 + expectedLevel / 10;

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(TrainingHallHouseId);
    const std::optional<size_t> trainIndex = findActionIndexByLabelPrefix(dialog, "Train to level ");

    REQUIRE(trainIndex.has_value());
    CHECK(dialog.actions[*trainIndex].enabled);
    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(*trainIndex);

    CHECK(resultDialog.isActive);
    CHECK_EQ(pMember->level, expectedLevel);
    CHECK_GE(pMember->skillPoints, expectedSkillPoints);
    CHECK_EQ(
        harness.worldRuntime().gameMinutes(),
        doctest::Approx(initialGameMinutes + expectedTrainingMinutes));
    CHECK_EQ(
        pOtherMember->health,
        OpenYAMM::Game::GameMechanics::calculateEffectiveCharacterMaxHealth(*pOtherMember));
    CHECK_EQ(
        pOtherMember->spellPoints,
        OpenYAMM::Game::GameMechanics::calculateEffectiveCharacterMaxSpellPoints(*pOtherMember));
}

TEST_CASE("dwi tavern arcomage submenu")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &rootDialog = harness.openHouseDialog(BullsEyeInnHouseId);
    const std::optional<size_t> arcomageIndex =
        findActionIndexByHouseActionId(rootDialog, OpenYAMM::Game::HouseActionId::OpenTavernArcomageMenu);

    REQUIRE(arcomageIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &submenuDialog = harness.executeAndPresent(*arcomageIndex);

    CHECK(dialogHasActionLabel(submenuDialog, "Rules"));
    CHECK(dialogHasActionLabel(submenuDialog, "Victory Conditions"));
    CHECK(dialogHasActionLabel(submenuDialog, "Play"));

    const std::optional<size_t> rulesIndex = findActionIndexByLabel(submenuDialog, "Rules");
    REQUIRE(rulesIndex.has_value());

    const OpenYAMM::Game::EventDialogContent &rulesDialog = harness.executeAndPresent(*rulesIndex);

    CHECK(dialogHasActionLabel(rulesDialog, "Rules"));
    CHECK(dialogHasActionLabel(rulesDialog, "Victory Conditions"));
    CHECK(dialogHasActionLabel(rulesDialog, "Play"));
}

TEST_CASE("mm7 tavern arcomage submenu requires deck to play")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHarmondaleTavern = gameData.houseTable.get(HarmondaleTavernHouseId);
    REQUIRE(pHarmondaleTavern != nullptr);

    const std::vector<OpenYAMM::Game::HouseActionOption> rootOptions =
        OpenYAMM::Game::buildHouseActionOptions(
            *pHarmondaleTavern,
            &harness.party(),
            &gameData.classSkillTable,
            &harness.worldRuntime(),
            18.0f * 60.0f,
            OpenYAMM::Game::DialogueMenuId::None);
    const std::vector<OpenYAMM::Game::HouseActionOption> submenuOptions =
        OpenYAMM::Game::buildHouseActionOptions(
            *pHarmondaleTavern,
            &harness.party(),
            &gameData.classSkillTable,
            &harness.worldRuntime(),
            18.0f * 60.0f,
            OpenYAMM::Game::DialogueMenuId::TavernArcomage);
    const std::vector<std::string> submenuLines =
        OpenYAMM::Game::buildHouseServiceInfoLines(
            *pHarmondaleTavern,
            &harness.party(),
            &gameData.classSkillTable,
            OpenYAMM::Game::DialogueMenuId::TavernArcomage);

    CHECK(findHouseActionById(rootOptions, OpenYAMM::Game::HouseActionId::OpenTavernArcomageMenu).has_value());
    CHECK(findHouseActionById(submenuOptions, OpenYAMM::Game::HouseActionId::TavernArcomageRules).has_value());
    CHECK(findHouseActionById(
        submenuOptions,
        OpenYAMM::Game::HouseActionId::TavernArcomageVictoryConditions).has_value());
    CHECK_FALSE(findHouseActionById(submenuOptions, OpenYAMM::Game::HouseActionId::TavernArcomagePlay).has_value());
    CHECK(std::find(
        submenuLines.begin(),
        submenuLines.end(),
        "You must have your own card deck to play here.") != submenuLines.end());

    harness.party().grantItem(ArcomageDeckItemId);
    const std::vector<OpenYAMM::Game::HouseActionOption> submenuOptionsWithDeck =
        OpenYAMM::Game::buildHouseActionOptions(
            *pHarmondaleTavern,
            &harness.party(),
            &gameData.classSkillTable,
            &harness.worldRuntime(),
            18.0f * 60.0f,
            OpenYAMM::Game::DialogueMenuId::TavernArcomage);
    CHECK(findHouseActionById(
        submenuOptionsWithDeck,
        OpenYAMM::Game::HouseActionId::TavernArcomagePlay).has_value());
}

TEST_CASE("merged tavern arcomage topics follow world rules")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    const auto hasArcomageTopic =
        [&gameData](uint32_t houseId)
        {
            const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(houseId);
            REQUIRE(pHouseEntry != nullptr);

            const std::vector<OpenYAMM::Game::HouseActionOption> options =
                OpenYAMM::Game::buildHouseActionOptions(
                    *pHouseEntry,
                    nullptr,
                    &gameData.classSkillTable,
                    nullptr,
                    12.0f * 60.0f,
                    OpenYAMM::Game::DialogueMenuId::None);

            return findHouseActionById(options, OpenYAMM::Game::HouseActionId::OpenTavernArcomageMenu).has_value();
        };
    const auto rootTopicCount =
        [&gameData](uint32_t houseId)
        {
            const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(houseId);
            REQUIRE(pHouseEntry != nullptr);

            return OpenYAMM::Game::buildHouseActionOptions(
                *pHouseEntry,
                nullptr,
                &gameData.classSkillTable,
                nullptr,
                12.0f * 60.0f,
                OpenYAMM::Game::DialogueMenuId::None).size();
        };

    CHECK(hasArcomageTopic(BullsEyeInnHouseId));
    CHECK(hasArcomageTopic(HarmondaleTavernHouseId));
    CHECK_FALSE(hasArcomageTopic(ServiceTavernWithResidentHouseId));
    CHECK_EQ(rootTopicCount(BullsEyeInnHouseId), 4u);
    CHECK_EQ(rootTopicCount(HarmondaleTavernHouseId), 4u);
    CHECK_EQ(rootTopicCount(ServiceTavernWithResidentHouseId), 3u);
}

TEST_CASE("dwi bank deposit withdraw roundtrip")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &rootDialog = harness.openHouseDialog(BankHouseId);
    const std::optional<size_t> depositIndex = findActionIndexByLabel(rootDialog, "Deposit");

    REQUIRE(depositIndex.has_value());
    const int initialCarriedGold = harness.party().gold();

    harness.executeAndPresent(*depositIndex);
    harness.confirmHouseBankInput(std::to_string(initialCarriedGold));

    CHECK_EQ(harness.party().gold(), 0);
    CHECK_EQ(harness.party().bankGold(), initialCarriedGold);

    const OpenYAMM::Game::EventDialogContent &bankDialog = harness.activeDialog();
    const std::optional<size_t> withdrawIndex = findActionIndexByLabel(bankDialog, "Withdraw");

    REQUIRE(withdrawIndex.has_value());
    const int bankGold = harness.party().bankGold();

    harness.executeAndPresent(*withdrawIndex);
    harness.confirmHouseBankInput(std::to_string(bankGold));

    CHECK_EQ(harness.party().bankGold(), 0);
    CHECK_EQ(harness.party().gold(), initialCarriedGold);
}

TEST_CASE("service house with resident opens occupant selector before service topics")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &selectorDialog =
        harness.openHouseDialog(ServiceTavernWithResidentHouseId);

    REQUIRE_GE(selectorDialog.actions.size(), 2u);
    CHECK(selectorDialog.isHouseDialog);
    CHECK_EQ(selectorDialog.actions[0].kind, OpenYAMM::Game::EventDialogActionKind::HouseProprietor);
    CHECK_EQ(selectorDialog.actions[0].id, ServiceTavernWithResidentHouseId);
    const auto andoverActionIt = std::find_if(
        selectorDialog.actions.begin(),
        selectorDialog.actions.end(),
        [](const OpenYAMM::Game::EventDialogAction &action)
        {
            return action.kind == OpenYAMM::Game::EventDialogActionKind::HouseResident
                && action.id == AndoverPotbelloNpcId;
        });
    REQUIRE(andoverActionIt != selectorDialog.actions.end());
    CHECK_FALSE(dialogHasActionLabel(selectorDialog, "Learn Skills"));

    const OpenYAMM::Game::EventDialogContent &serviceDialog = harness.executeAndPresent(0);

    CHECK(serviceDialog.isHouseDialog);
    CHECK(dialogHasActionLabel(serviceDialog, "Learn Skills"));
    CHECK(findActionIndexByLabelPrefix(serviceDialog, "Rent room").has_value());

    harness.eventRuntimeState().dialogueState.menuStack.clear();
    const OpenYAMM::Game::EventDialogContent &freshSelectorDialog =
        harness.openHouseDialog(ServiceTavernWithResidentHouseId);

    const auto freshAndoverActionIt = std::find_if(
        freshSelectorDialog.actions.begin(),
        freshSelectorDialog.actions.end(),
        [](const OpenYAMM::Game::EventDialogAction &action)
        {
            return action.kind == OpenYAMM::Game::EventDialogActionKind::HouseResident
                && action.id == AndoverPotbelloNpcId;
        });
    REQUIRE(freshAndoverActionIt != freshSelectorDialog.actions.end());
    const size_t freshAndoverActionIndex =
        static_cast<size_t>(std::distance(freshSelectorDialog.actions.begin(), freshAndoverActionIt));
    const OpenYAMM::Game::EventDialogContent &npcDialog = harness.executeAndPresent(freshAndoverActionIndex);

    CHECK_FALSE(npcDialog.isHouseDialog);
    CHECK_EQ(npcDialog.sourceId, AndoverPotbelloNpcId);
    REQUIRE(harness.eventRuntimeState().pendingDialogueContext.has_value());
    CHECK_EQ(
        harness.eventRuntimeState().pendingDialogueContext->kind,
        OpenYAMM::Game::DialogueContextKind::NpcTalk);
    CHECK_EQ(harness.eventRuntimeState().pendingDialogueContext->hostHouseId, ServiceTavernWithResidentHouseId);
}

TEST_CASE("transport routes filter by weekday and qbit")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pSmugglerHouse = gameData.houseTable.get(SmokeBoatHouseId);
    const OpenYAMM::Game::HouseEntry *pQBitHouse = gameData.houseTable.get(WindBoatHouseId);

    REQUIRE(pSmugglerHouse != nullptr);
    REQUIRE(pQBitHouse != nullptr);
    harness.party().setQuestBit(10, true);

    const std::vector<OpenYAMM::Game::HouseActionOption> mondayActions = OpenYAMM::Game::buildHouseActionOptions(
        *pSmugglerHouse,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        0.0f,
        OpenYAMM::Game::DialogueMenuId::None);
    const std::vector<OpenYAMM::Game::HouseActionOption> tuesdayActions = OpenYAMM::Game::buildHouseActionOptions(
        *pSmugglerHouse,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        24.0f * 60.0f,
        OpenYAMM::Game::DialogueMenuId::None);

    CHECK(houseActionsContainDestination(mondayActions, "Ravage Roaming"));
    CHECK_FALSE(houseActionsContainDestination(mondayActions, "Ravenshore"));
    CHECK(houseActionsContainDestination(tuesdayActions, "Ravenshore"));
    CHECK_FALSE(houseActionsContainDestination(tuesdayActions, "Ravage Roaming"));

    harness.party().setQuestBit(10, false);

    const std::vector<OpenYAMM::Game::HouseActionOption> lockedActions = OpenYAMM::Game::buildHouseActionOptions(
        *pQBitHouse,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);

    REQUIRE_EQ(lockedActions.size(), 1u);
    CHECK_EQ(lockedActions.front().label, "Sorry, come back another day");
    CHECK_FALSE(lockedActions.front().enabled);

    harness.party().setQuestBit(10, true);

    const std::vector<OpenYAMM::Game::HouseActionOption> unlockedActions = OpenYAMM::Game::buildHouseActionOptions(
        *pQBitHouse,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);

    REQUIRE_EQ(unlockedActions.size(), 1u);
    CHECK(houseActionsContainDestination(unlockedActions, "Ravage Roaming"));
}

TEST_CASE("mastery teacher not enough gold")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(3));
    OpenYAMM::Game::Character *pCharacter = harness.party().activeMember();
    REQUIRE(pCharacter != nullptr);
    REQUIRE(setCharacterSkill(
        *pCharacter,
        "IdentifyItem",
        7,
        OpenYAMM::Game::SkillMastery::Expert) != nullptr);

    harness.party().addGold(-harness.party().gold());

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openMasteryTeacherOffer(MasterIdentifyItemTeacherNpcId, "Master Identify Item");

    REQUIRE_FALSE(dialog.actions.empty());
    CHECK_EQ(dialog.actions.front().label, "You don't have enough gold!");

    constexpr uint32_t MergedMasterIdentifyItemAutonoteId = 162;
    constexpr uint32_t MergedMasterIdentifyItemAutonoteVariable =
        (MergedMasterIdentifyItemAutonoteId << 16) | 0x00e1u;
    const auto noteIt = harness.eventRuntimeState().variables.find(MergedMasterIdentifyItemAutonoteVariable);
    REQUIRE(noteIt != harness.eventRuntimeState().variables.end());
    CHECK_EQ(noteIt->second, 1);
}

TEST_CASE("teacher topic with explicit autonote also creates merged teacher map note")
{
    OpenYAMM::Game::MapStatsEntry emeraldIsland = {};
    emeraldIsland.id = 62;
    emeraldIsland.fileName = "7out01.odm";

    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    harness.setCurrentMap(emeraldIsland);

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openNpcDialogue(MasterIdentifyItemTeacherNpcId);
    CHECK(dialogHasActionLabel(dialog, "Master Identify Item"));

    constexpr uint32_t MergedMasterIdentifyItemAutonoteId = 162;
    constexpr uint32_t MergedMasterIdentifyItemAutonoteVariable =
        (MergedMasterIdentifyItemAutonoteId << 16) | 0x00e1u;
    const auto variableIt = harness.eventRuntimeState().variables.find(MergedMasterIdentifyItemAutonoteVariable);
    REQUIRE(variableIt != harness.eventRuntimeState().variables.end());
    CHECK_EQ(variableIt->second, 1);

    constexpr uint32_t MasterIdentifyItemMapNoteId = 2224;
    const auto noteIt = harness.eventRuntimeState().runtimeMapNotes.find(MasterIdentifyItemMapNoteId);
    REQUIRE(noteIt != harness.eventRuntimeState().runtimeMapNotes.end());
    CHECK(noteIt->second.active);
    CHECK_EQ(noteIt->second.mapFileName, "7out01.odm");
    CHECK_EQ(noteIt->second.text, "Identify Item - Master");
}

TEST_CASE("mastery teacher missing skill")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(3));
    OpenYAMM::Game::Character *pCharacter = harness.party().activeMember();
    REQUIRE(pCharacter != nullptr);
    pCharacter->skills.erase("IdentifyItem");

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openMasteryTeacherOffer(MasterIdentifyItemTeacherNpcId, "Master Identify Item");

    REQUIRE_FALSE(dialog.actions.empty());
    CHECK_EQ(
        dialog.actions.front().label,
        "You must know the skill before you can become an expert in it!");
}

TEST_CASE("mastery teacher insufficient skill level")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(3));
    OpenYAMM::Game::Character *pCharacter = harness.party().activeMember();
    REQUIRE(pCharacter != nullptr);
    REQUIRE(setCharacterSkill(
        *pCharacter,
        "IdentifyItem",
        6,
        OpenYAMM::Game::SkillMastery::Expert) != nullptr);

    harness.party().addGold(5000);

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openMasteryTeacherOffer(MasterIdentifyItemTeacherNpcId, "Master Identify Item");

    REQUIRE_FALSE(dialog.actions.empty());
    CHECK_EQ(
        dialog.actions.front().label,
        "You don't meet the requirements, and cannot be taught until you do.");
}

TEST_CASE("mastery teacher wrong class")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(0));
    OpenYAMM::Game::Character *pCharacter = harness.party().activeMember();
    REQUIRE(pCharacter != nullptr);
    REQUIRE(setCharacterSkill(
        *pCharacter,
        "IdentifyItem",
        7,
        OpenYAMM::Game::SkillMastery::Expert) != nullptr);

    harness.party().addGold(5000);

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openMasteryTeacherOffer(MasterIdentifyItemTeacherNpcId, "Master Identify Item");

    REQUIRE_FALSE(dialog.actions.empty());
    CHECK_EQ(dialog.actions.front().label, "This skill level can not be learned by the Knight class.");
}

TEST_CASE("mastery teacher character switch changes logic")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(0));
    OpenYAMM::Game::Character *pKnight = harness.party().activeMember();
    REQUIRE(pKnight != nullptr);
    REQUIRE(setCharacterSkill(
        *pKnight,
        "IdentifyItem",
        7,
        OpenYAMM::Game::SkillMastery::Expert) != nullptr);

    harness.party().addGold(5000);

    const OpenYAMM::Game::EventDialogContent &knightDialog =
        harness.openMasteryTeacherOffer(MasterIdentifyItemTeacherNpcId, "Master Identify Item");

    REQUIRE_FALSE(knightDialog.actions.empty());
    CHECK_EQ(knightDialog.actions.front().label, "This skill level can not be learned by the Knight class.");

    REQUIRE(harness.party().setActiveMemberIndex(3));
    OpenYAMM::Game::Character *pSorcerer = harness.party().activeMember();
    REQUIRE(pSorcerer != nullptr);
    REQUIRE(setCharacterSkill(
        *pSorcerer,
        "IdentifyItem",
        7,
        OpenYAMM::Game::SkillMastery::Expert) != nullptr);

    const OpenYAMM::Game::EventDialogContent &sorcererDialog = harness.refreshCurrentNpcDialog();

    REQUIRE_FALSE(sorcererDialog.actions.empty());
    CHECK_EQ(sorcererDialog.actions.front().label, "Become Master in Identify Item for 2500 gold");
}

TEST_CASE("mastery teacher offer and learn")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(3));
    OpenYAMM::Game::Character *pCharacter = harness.party().activeMember();
    REQUIRE(pCharacter != nullptr);
    REQUIRE(setCharacterSkill(
        *pCharacter,
        "IdentifyItem",
        7,
        OpenYAMM::Game::SkillMastery::Expert) != nullptr);

    const int initialGold = harness.party().gold();
    harness.party().addGold(5000);

    const OpenYAMM::Game::EventDialogContent &offerDialog =
        harness.openMasteryTeacherOffer(MasterIdentifyItemTeacherNpcId, "Master Identify Item");

    REQUIRE_FALSE(offerDialog.actions.empty());
    CHECK_EQ(offerDialog.actions.front().label, "Become Master in Identify Item for 2500 gold");

    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(0);

    const OpenYAMM::Game::Character *pUpdatedCharacter = harness.party().activeMember();
    REQUIRE(pUpdatedCharacter != nullptr);
    const OpenYAMM::Game::CharacterSkill *pUpdatedSkill = pUpdatedCharacter->findSkill("IdentifyItem");
    REQUIRE(pUpdatedSkill != nullptr);

    CHECK_EQ(pUpdatedSkill->mastery, OpenYAMM::Game::SkillMastery::Master);
    CHECK_EQ(harness.party().gold(), initialGold + 5000 - 2500);

    REQUIRE_FALSE(resultDialog.actions.empty());
    CHECK_EQ(resultDialog.actions.front().label, "You are already a master in this skill.");
    CHECK(dialogContainsText(resultDialog, "With Mastery of the Identify Items skill"));
}

TEST_CASE("mm6 suffix mastery teacher topic opens native mastery offer")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(1));
    OpenYAMM::Game::Character *pCharacter = harness.party().activeMember();
    REQUIRE(pCharacter != nullptr);
    REQUIRE(setCharacterSkill(
        *pCharacter,
        "BodyMagic",
        4,
        OpenYAMM::Game::SkillMastery::Normal) != nullptr);
    harness.party().addGold(1000);

    const OpenYAMM::Game::EventDialogContent &offerDialog =
        harness.openMasteryTeacherOffer(AbdulaiMahgrebNpcId, "Body Magic Expert");

    REQUIRE_FALSE(offerDialog.actions.empty());
    CHECK_EQ(offerDialog.actions.front().label, "Become Expert in Body Magic for 1000 gold");
}

TEST_CASE("mm6 suffix mastery teacher topic does not show unrelated fallback text")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(1));
    OpenYAMM::Game::Character *pCharacter = harness.party().activeMember();
    REQUIRE(pCharacter != nullptr);
    REQUIRE(setCharacterSkill(
        *pCharacter,
        "BodyMagic",
        4,
        OpenYAMM::Game::SkillMastery::Expert) != nullptr);

    const OpenYAMM::Game::EventDialogContent &offerDialog =
        harness.openMasteryTeacherOffer(AbdulaiMahgrebNpcId, "Body Magic Expert");

    REQUIRE_FALSE(offerDialog.actions.empty());
    CHECK_EQ(offerDialog.actions.front().label, "You are already an expert in this skill.");
    CHECK_FALSE(dialogContainsText(offerDialog, "So"));
    CHECK_FALSE(dialogContainsText(offerDialog, "Carmine traitor"));
}

TEST_CASE("mm6 free haven armsmaster teachers use mmerge topic data")
{
    constexpr uint32_t WinstonHistorianNpcId = 860;
    constexpr uint32_t WinstonHistorianHouseId = 1281;
    constexpr uint32_t LawrenceAlemanNpcId = 1114;
    constexpr uint32_t LawrenceAlemanHouseId = 1540;

    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    harness.eventRuntimeState().npcTopicOverrides[LawrenceAlemanNpcId][3] = 405;
    harness.eventRuntimeState().npcTopicOverrides[WinstonHistorianNpcId][3] = 406;
    harness.eventRuntimeState().npcTopicOverrides[WinstonHistorianNpcId][4] = 407;

    const OpenYAMM::Game::EventDialogContent &lawrenceDialog =
        harness.openNpcDialogue(LawrenceAlemanNpcId, LawrenceAlemanHouseId);

    CHECK_EQ(actionLabelCount(lawrenceDialog, "Expert Armsmaster"), 1u);

    const std::optional<size_t> gongsIndex = findActionIndexByLabel(lawrenceDialog, "Gongs");
    REQUIRE(gongsIndex.has_value());
    CHECK_EQ(lawrenceDialog.actions[*gongsIndex].kind, OpenYAMM::Game::EventDialogActionKind::NpcTopic);

    const std::optional<size_t> expertIndex = findActionIndexByLabel(lawrenceDialog, "Expert Armsmaster");
    REQUIRE(expertIndex.has_value());
    CHECK_EQ(
        lawrenceDialog.actions[*expertIndex].kind,
        OpenYAMM::Game::EventDialogActionKind::MasteryTeacherOffer);

    const OpenYAMM::Game::EventDialogContent &winstonDialog =
        harness.openNpcDialogue(WinstonHistorianNpcId, WinstonHistorianHouseId);

    CHECK_EQ(actionLabelCount(winstonDialog, "Master Armsmaster"), 1u);
    CHECK_EQ(actionLabelCount(winstonDialog, "Grand Master Armsmaster"), 1u);

    const std::optional<size_t> guildIndex = findActionIndexByLabel(winstonDialog, "Duelist's Edge Membership");
    REQUIRE(guildIndex.has_value());
    CHECK_EQ(winstonDialog.actions[*guildIndex].kind, OpenYAMM::Game::EventDialogActionKind::GuildMembershipOffer);

    const std::optional<size_t> masterIndex = findActionIndexByLabel(winstonDialog, "Master Armsmaster");
    REQUIRE(masterIndex.has_value());
    CHECK_EQ(winstonDialog.actions[*masterIndex].kind, OpenYAMM::Game::EventDialogActionKind::MasteryTeacherOffer);

    const std::optional<size_t> grandmasterIndex =
        findActionIndexByLabel(winstonDialog, "Grand Master Armsmaster");
    REQUIRE(grandmasterIndex.has_value());
    CHECK_EQ(
        winstonDialog.actions[*grandmasterIndex].kind,
        OpenYAMM::Game::EventDialogActionKind::MasteryTeacherOffer);
}

TEST_CASE("mastery teacher topics are identified from merged table and vanilla range only")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &stonDialog = harness.openNpcDialogue(StonNpcId);
    const std::optional<size_t> caravanIndex = findActionIndexByLabel(stonDialog, "Caravan Master");
    REQUIRE(caravanIndex.has_value());
    CHECK_EQ(stonDialog.actions[*caravanIndex].kind, OpenYAMM::Game::EventDialogActionKind::NpcTopic);

    const OpenYAMM::Game::EventDialogContent &archerDialog = harness.openNpcDialogue(LawrenceMarkNpcId);
    const std::optional<size_t> archerIndex = findActionIndexByLabel(archerDialog, "Master Archer");
    REQUIRE(archerIndex.has_value());
    CHECK_EQ(archerDialog.actions[*archerIndex].kind, OpenYAMM::Game::EventDialogActionKind::NpcTopic);

    const OpenYAMM::Game::EventDialogContent &hintDialog = harness.openNpcDialogue(HintTeacherNpcId);
    const std::optional<size_t> teachersIndex = findActionIndexByLabel(hintDialog, "Expert Teachers");
    REQUIRE(teachersIndex.has_value());
    CHECK_EQ(hintDialog.actions[*teachersIndex].kind, OpenYAMM::Game::EventDialogActionKind::NpcTopic);
}

TEST_CASE("vanilla mm8 blaster teacher gap remains a mastery teacher")
{
    constexpr uint32_t ExpertBlasterAutonoteVariable = (344u << 16) | 0x00e1u;

    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    OpenYAMM::Game::Character *pCharacter = harness.party().activeMember();
    REQUIRE(pCharacter != nullptr);
    REQUIRE(setCharacterSkill(
        *pCharacter,
        "Blaster",
        4,
        OpenYAMM::Game::SkillMastery::Normal) != nullptr);
    harness.party().addGold(2000);

    const OpenYAMM::Game::EventDialogContent &offerDialog =
        harness.openMasteryTeacherOffer(ExpertBlasterNpcId, "Expert Blaster");

    REQUIRE_FALSE(offerDialog.actions.empty());
    CHECK_EQ(offerDialog.actions.front().label, "Become Expert in Blaster for 2000 gold");

    const auto noteIt = harness.eventRuntimeState().variables.find(ExpertBlasterAutonoteVariable);
    REQUIRE(noteIt != harness.eventRuntimeState().variables.end());
    CHECK_NE(noteIt->second, 0);
}

TEST_CASE("teacher topic without explicit autonote creates merged teacher map note")
{
    OpenYAMM::Game::MapStatsEntry jadamMap = {};
    jadamMap.id = 0;
    jadamMap.fileName = "out01.odm";

    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    harness.setCurrentMap(jadamMap);

    harness.eventRuntimeState().npcTopicOverrides[StonNpcId][0] = 1549;

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openNpcDialogue(StonNpcId);
    CHECK(findActionIndexByLabel(dialog, "Body Magic Expert").has_value());

    constexpr uint32_t BodyMagicExpertMapNoteId = 1118;
    const auto noteIt = harness.eventRuntimeState().runtimeMapNotes.find(BodyMagicExpertMapNoteId);
    REQUIRE(noteIt != harness.eventRuntimeState().runtimeMapNotes.end());
    CHECK(noteIt->second.active);
    CHECK_EQ(noteIt->second.text, "Body Magic - Expert");
}

TEST_CASE("mm6 guild membership topic opens native guild offer")
{
    constexpr uint16_t ElementalGuildMembershipVariable = 0x800eu;
    constexpr uint32_t ElementalGuildAutonoteId = 564;
    constexpr uint32_t ElementalGuildAutonoteVariable = (ElementalGuildAutonoteId << 16) | 0x00e1u;

    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const int initialGold = harness.party().gold();
    const OpenYAMM::Game::EventDialogContent &dialog = harness.openNpcDialogue(BufordAllmanNpcId);
    const std::optional<size_t> membershipIndex = findActionIndexByLabel(dialog, "Elemental Guild Membership");
    REQUIRE(membershipIndex.has_value());

    const OpenYAMM::Game::EventDialogContent &offerDialog = harness.executeAndPresent(*membershipIndex);

    CHECK_FALSE(dialogContainsText(offerDialog, "That topic does not have an event yet."));
    CHECK(dialogContainsText(offerDialog, "join the Guild of the Elements"));

    const std::optional<size_t> joinIndex = findActionIndexByLabel(
        offerDialog,
        "Join the Elemental Guild for 100 gold");
    REQUIRE(joinIndex.has_value());

    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(*joinIndex);

    CHECK_FALSE(dialogContainsText(resultDialog, "That topic does not have an event yet."));
    CHECK_EQ(harness.party().gold(), initialGold - 100);
    CHECK_EQ(harness.party().eventVariableValue(ElementalGuildMembershipVariable), 1);

    const auto noteIt = harness.eventRuntimeState().variables.find(ElementalGuildAutonoteVariable);
    REQUIRE(noteIt != harness.eventRuntimeState().variables.end());
    CHECK_EQ(noteIt->second, 1);
}

TEST_CASE("mm7 guild membership topic opens native guild offer")
{
    constexpr uint16_t FireGuildMembershipVariable = 0x8005u;

    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openNpcDialogue(CarolynWeathersNpcId);
    const std::optional<size_t> membershipIndex = findActionIndexByLabel(dialog, "Fire Guild Membership");
    REQUIRE(membershipIndex.has_value());

    const OpenYAMM::Game::EventDialogContent &offerDialog = harness.executeAndPresent(*membershipIndex);

    CHECK_FALSE(dialogContainsText(offerDialog, "That topic does not have an event yet."));
    CHECK(dialogContainsText(offerDialog, "Why be subtle when you can learn Fire magic?"));

    const std::optional<size_t> joinIndex = findActionIndexByLabel(offerDialog, "Join the Fire Guild for 50 gold");
    REQUIRE(joinIndex.has_value());

    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(*joinIndex);

    CHECK_FALSE(dialogContainsText(resultDialog, "That topic does not have an event yet."));
    CHECK_EQ(harness.party().eventVariableValue(FireGuildMembershipVariable), 1);
}

TEST_CASE("mm6 smuggler guild membership topic opens native guild offer")
{
    constexpr uint16_t SmugglerGuildMembershipVariable = 0x8012u;
    constexpr uint32_t SmugglerGuildAutonoteId = 631;
    constexpr uint32_t SmugglerGuildAutonoteVariable = (SmugglerGuildAutonoteId << 16) | 0x00e1u;

    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const int initialGold = harness.party().gold();
    const OpenYAMM::Game::EventDialogContent &dialog = harness.openNpcDialogue(TessTuckerNpcId);
    const std::optional<size_t> membershipIndex = findActionIndexByLabel(dialog, "Smuggler's Guild Membership");
    REQUIRE(membershipIndex.has_value());

    const OpenYAMM::Game::EventDialogContent &offerDialog = harness.executeAndPresent(*membershipIndex);

    CHECK_FALSE(dialogContainsText(offerDialog, "That topic does not have an event yet."));
    CHECK(dialogContainsText(offerDialog, "Smugglers' Guild doesn't just run contraband goods"));

    const std::optional<size_t> joinIndex = findActionIndexByLabel(offerDialog, "Join Smugglers' Guild for 50 gold");
    REQUIRE(joinIndex.has_value());

    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(*joinIndex);

    CHECK_FALSE(dialogContainsText(resultDialog, "That topic does not have an event yet."));
    CHECK_EQ(harness.party().gold(), initialGold - 50);
    CHECK_EQ(harness.party().eventVariableValue(SmugglerGuildMembershipVariable), 1);

    const auto noteIt = harness.eventRuntimeState().variables.find(SmugglerGuildAutonoteVariable);
    REQUIRE(noteIt != harness.eventRuntimeState().variables.end());
    CHECK_EQ(noteIt->second, 1);
}

TEST_CASE("mm6 blades end guild membership topic opens native guild offer")
{
    constexpr uint16_t BladesEndGuildMembershipVariable = 0x8013u;
    constexpr uint32_t BladesEndGuildAutonoteId = 632;
    constexpr uint32_t BladesEndGuildAutonoteVariable = (BladesEndGuildAutonoteId << 16) | 0x00e1u;

    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const int initialGold = harness.party().gold();
    const OpenYAMM::Game::EventDialogContent &dialog = harness.openNpcDialogue(HaroldHessNpcId);
    const std::optional<size_t> membershipIndex = findActionIndexByLabel(dialog, "Blade's End Membership");
    REQUIRE(membershipIndex.has_value());

    const OpenYAMM::Game::EventDialogContent &offerDialog = harness.executeAndPresent(*membershipIndex);

    CHECK_FALSE(dialogContainsText(offerDialog, "That topic does not have an event yet."));
    CHECK(dialogContainsText(offerDialog, "Blades' End mercenary's guild wants YOU"));

    const std::optional<size_t> joinIndex = findActionIndexByLabel(offerDialog, "Join Blades' End for 25 gold");
    REQUIRE(joinIndex.has_value());

    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(*joinIndex);

    CHECK_FALSE(dialogContainsText(resultDialog, "That topic does not have an event yet."));
    CHECK_EQ(harness.party().gold(), initialGold - 25);
    CHECK_EQ(harness.party().eventVariableValue(BladesEndGuildMembershipVariable), 1);

    const auto noteIt = harness.eventRuntimeState().variables.find(BladesEndGuildAutonoteVariable);
    REQUIRE(noteIt != harness.eventRuntimeState().variables.end());
    CHECK_EQ(noteIt->second, 1);
}

TEST_CASE("actual roster join rohani")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openNpcDialogue(RohaniNpcId);
    const std::optional<size_t> joinIndex = findActionIndexByLabel(dialog, "Join");

    REQUIRE(joinIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &offerDialog = harness.executeAndPresent(*joinIndex);
    CHECK(dialogContainsText(offerDialog, "Will you have Rohani Oscleton the Dark Elf join you?"));

    const std::optional<size_t> yesIndex = findActionIndexByLabel(offerDialog, "Yes");
    REQUIRE(yesIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(*yesIndex);

    CHECK(harness.party().hasRosterMember(6));
    CHECK(harness.eventRuntimeState().unavailableNpcIds.contains(RohaniNpcId));
    CHECK(dialogContainsText(resultDialog, "joined the party"));
}

TEST_CASE("overdune quest completion unlocks roster join")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    harness.party().setQuestBit(62, true);
    REQUIRE(harness.executeGlobalEvent(46));

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openNpcDialogue(OverduneNpcId);
    const std::optional<size_t> joinIndex = findActionIndexByLabel(dialog, "Join");

    REQUIRE(joinIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &offerDialog = harness.executeAndPresent(*joinIndex);
    CHECK(dialogContainsText(offerDialog, "Shall we be off?"));

    const std::optional<size_t> yesIndex = findActionIndexByLabel(offerDialog, "Yes");
    REQUIRE(yesIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(*yesIndex);

    CHECK(harness.party().hasRosterMember(OverduneRosterId));
    CHECK(harness.eventRuntimeState().unavailableNpcIds.contains(OverduneNpcId));
    CHECK(dialogContainsText(resultDialog, "joined the party"));

    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram = loadSyntheticMapEventProgram(
        "evt.map[1] = function()\n"
        "    if evt._IsNpcInParty(4) then\n"
        "        evt.SimpleMessage(\"Overdune active\")\n"
        "    else\n"
        "        evt.SimpleMessage(\"Overdune missing\")\n"
        "    end\n"
        "end\n",
        "@SyntheticOverduneActiveRosterCheck.lua");
    REQUIRE(localEventProgram.has_value());

    OpenYAMM::Game::EventRuntimeState rosterCheckState = {};
    OpenYAMM::Game::EventRuntime rosterCheckRuntime = {};
    REQUIRE(rosterCheckRuntime.executeEventById(
        localEventProgram,
        std::nullopt,
        1,
        rosterCheckState,
        &harness.party()));
    REQUIRE_FALSE(rosterCheckState.messages.empty());
    CHECK_EQ(rosterCheckState.messages.back(), "Overdune active");
}

TEST_CASE("actual roster join rohani full party")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::RosterEntry *pExtraMember = gameData.rosterTable.get(3);

    REQUIRE(pExtraMember != nullptr);
    REQUIRE(harness.party().recruitRosterMember(*pExtraMember));

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openNpcDialogue(RohaniNpcId);
    const std::optional<size_t> joinIndex = findActionIndexByLabel(dialog, "Join");

    REQUIRE(joinIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &offerDialog = harness.executeAndPresent(*joinIndex);
    const std::optional<size_t> yesIndex = findActionIndexByLabel(offerDialog, "Yes");

    REQUIRE(yesIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(*yesIndex);
    const auto movedHouseIt = harness.eventRuntimeState().npcHouseOverrides.find(RohaniNpcId);

    CHECK(dialogContainsText(resultDialog, "I'm glad you've decided to take me"));
    CHECK_FALSE(harness.eventRuntimeState().unavailableNpcIds.contains(RohaniNpcId));
    REQUIRE(movedHouseIt != harness.eventRuntimeState().npcHouseOverrides.end());
    CHECK_EQ(movedHouseIt->second, AdventurersInnHouseId);
}

TEST_CASE("actual roster join dyson direct")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openNpcDialogue(DysonDirectNpcId);
    const std::optional<size_t> joinIndex = findActionIndexByLabel(dialog, "Join");

    REQUIRE(joinIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &offerDialog = harness.executeAndPresent(*joinIndex);
    CHECK(dialogContainsText(offerDialog, "I will gladly join you."));

    const std::optional<size_t> yesIndex = findActionIndexByLabel(offerDialog, "Yes");
    REQUIRE(yesIndex.has_value());
    harness.executeAndPresent(*yesIndex);

    CHECK(harness.party().hasRosterMember(34));
}

TEST_CASE("blazen cure unlocks roster entry in ravenshore inn")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    harness.party().grantItem(GemOfRestorationItemId);

    REQUIRE(harness.executeGlobalEvent(54));

    CHECK(harness.party().hasQuestBit(435));
    CHECK_FALSE(harness.eventRuntimeState().npcHouseOverrides.contains(BlazenJoinNpcId));
    CHECK_EQ(harness.party().inventoryItemCount(GemOfRestorationItemId), 0);

    harness.eventRuntimeState().messages.clear();
    harness.openHouseDialog(AdventurersInnHouseId);

    const std::vector<OpenYAMM::Game::AdventurersInnMember> &innMembers =
        harness.party().adventurersInnMembers();
    const auto blazenInnIt = std::find_if(
        innMembers.begin(),
        innMembers.end(),
        [](const OpenYAMM::Game::AdventurersInnMember &member)
        {
            return member.character.rosterId == BlazenRosterId;
        });
    REQUIRE(blazenInnIt != innMembers.end());
    CHECK_EQ(blazenInnIt->character.name, "Blazen Stormlance");
    CHECK(characterHasAnyEquippedItem(blazenInnIt->character));
    CHECK(characterHasItem(blazenInnIt->character, 5));
    CHECK(characterHasItem(blazenInnIt->character, 45));
    CHECK(characterHasItem(blazenInnIt->character, 63));
    CHECK(characterHasItem(blazenInnIt->character, 97));
    CHECK(characterHasItem(blazenInnIt->character, 103));

    const size_t blazenInnIndex = static_cast<size_t>(std::distance(innMembers.begin(), blazenInnIt));
    REQUIRE(harness.party().hireAdventurersInnMember(blazenInnIndex));
    CHECK(harness.party().hasRosterMember(BlazenRosterId));
}

TEST_CASE("blazen cure keeps placed quest npc on original post-cure topics")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    harness.party().grantItem(GemOfRestorationItemId);

    REQUIRE(harness.executeGlobalEvent(54));

    harness.eventRuntimeState().messages.clear();

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openNpcDialogue(BlazenQuestNpcId);
    CHECK_FALSE(dialogHasActionLabel(dialog, "Cure"));
    CHECK(dialogHasActionLabel(dialog, "Ebonest"));
    CHECK(dialogHasActionLabel(dialog, "Mad Necromancer"));
    CHECK_FALSE(dialogHasActionLabel(dialog, "Join"));
}

TEST_CASE("actual roster join blazen direct")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openNpcDialogue(BlazenJoinNpcId);
    const std::optional<size_t> joinIndex = findActionIndexByLabel(dialog, "Join");

    REQUIRE(joinIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &offerDialog = harness.executeAndPresent(*joinIndex);
    CHECK(dialogContainsText(offerDialog, "I will be forever in your debt."));

    const std::optional<size_t> yesIndex = findActionIndexByLabel(offerDialog, "Yes");
    REQUIRE(yesIndex.has_value());
    harness.executeAndPresent(*yesIndex);

    CHECK(harness.party().hasRosterMember(BlazenRosterId));
}

TEST_CASE("moved roster join npcs populate adventurers inn overlay")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    harness.eventRuntimeState().npcHouseOverrides[BlazenJoinNpcId] = AdventurersInnHouseId;

    harness.openHouseDialog(AdventurersInnHouseId);

    bool foundBlazen = false;

    for (const OpenYAMM::Game::AdventurersInnMember &member : harness.party().adventurersInnMembers())
    {
        if (member.character.rosterId == BlazenRosterId)
        {
            foundBlazen = true;
        }
    }

    CHECK(foundBlazen);
}

TEST_CASE("dagger wound init event unlocks starting adventurers inn roster")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.executeOut01LocalEvent(3));
    harness.openHouseDialog(AdventurersInnHouseId);

    bool foundDevlin = false;
    bool foundElsbeth = false;

    for (const OpenYAMM::Game::AdventurersInnMember &member : harness.party().adventurersInnMembers())
    {
        if (member.character.rosterId == 1)
        {
            foundDevlin = true;
        }
        else if (member.character.rosterId == 7)
        {
            foundElsbeth = true;
        }
    }

    CHECK(foundDevlin);
    CHECK(foundElsbeth);
}

TEST_CASE("roster join mapping and players can show topic")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    OpenYAMM::Game::EventDialogContent dialog = harness.openNpcDialogue(SandroNpcId);
    CHECK(dialogHasActionLabel(dialog, "Dyson Leland"));

    harness.eventRuntimeState().npcTopicOverrides[DysonNpcId][3] = 634;
    dialog = harness.openNpcDialogue(DysonNpcId);

    const std::optional<size_t> joinIndex = findActionIndexByLabel(dialog, "Join");
    REQUIRE(joinIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &offerDialog = harness.executeAndPresent(*joinIndex);

    CHECK(dialogContainsText(offerDialog, "I will gladly join you."));

    const std::optional<size_t> yesIndex = findActionIndexByLabel(offerDialog, "Yes");
    REQUIRE(yesIndex.has_value());
    harness.executeAndPresent(*yesIndex);

    CHECK(harness.party().hasRosterMember(34));

    dialog = harness.openNpcDialogue(SandroNpcId);
    CHECK_FALSE(dialogHasActionLabel(dialog, "Dyson Leland"));
}

TEST_CASE("synthetic roster join accept")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const std::optional<std::string> inviteText = gameData.npcDialogTable.getText(202);

    if (inviteText.has_value())
    {
        harness.eventRuntimeState().messages.push_back(*inviteText);
    }

    harness.eventRuntimeState().dialogueState.currentOffer = makeRosterJoinOffer(FredrickNpcId, 2, 202, 203);

    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext context = {};
    context.kind = OpenYAMM::Game::DialogueContextKind::NpcTalk;
    context.sourceId = FredrickNpcId;
    harness.eventRuntimeState().pendingDialogueContext = context;

    const OpenYAMM::Game::EventDialogContent &dialog = harness.presentPendingDialog(0, true);
    const std::optional<size_t> yesIndex = findActionIndexByLabel(dialog, "Yes");

    REQUIRE(yesIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(*yesIndex);

    CHECK_EQ(harness.party().members().size(), 5u);
    CHECK(harness.eventRuntimeState().unavailableNpcIds.contains(FredrickNpcId));
    CHECK(dialogContainsText(resultDialog, "joined the party"));
}

TEST_CASE("synthetic roster join full party")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::RosterEntry *pExtraMember = gameData.rosterTable.get(3);
    const std::optional<std::string> inviteText = gameData.npcDialogTable.getText(202);

    REQUIRE(pExtraMember != nullptr);
    REQUIRE(harness.party().recruitRosterMember(*pExtraMember));

    if (inviteText.has_value())
    {
        harness.eventRuntimeState().messages.push_back(*inviteText);
    }

    harness.eventRuntimeState().dialogueState.currentOffer = makeRosterJoinOffer(FredrickNpcId, 2, 202, 203);

    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext context = {};
    context.kind = OpenYAMM::Game::DialogueContextKind::NpcTalk;
    context.sourceId = FredrickNpcId;
    harness.eventRuntimeState().pendingDialogueContext = context;

    const OpenYAMM::Game::EventDialogContent &dialog = harness.presentPendingDialog(0, true);
    const std::optional<size_t> yesIndex = findActionIndexByLabel(dialog, "Yes");

    REQUIRE(yesIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(*yesIndex);
    const auto movedHouseIt = harness.eventRuntimeState().npcHouseOverrides.find(FredrickNpcId);

    CHECK_EQ(harness.party().members().size(), 5u);
    CHECK_FALSE(harness.eventRuntimeState().unavailableNpcIds.contains(FredrickNpcId));
    REQUIRE(movedHouseIt != harness.eventRuntimeState().npcHouseOverrides.end());
    CHECK_EQ(movedHouseIt->second, AdventurersInnHouseId);
    CHECK(dialogContainsText(resultDialog, "party's all full up"));

    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext innContext = {};
    innContext.kind = OpenYAMM::Game::DialogueContextKind::HouseService;
    innContext.sourceId = AdventurersInnHouseId;
    innContext.hostHouseId = AdventurersInnHouseId;
    harness.eventRuntimeState().pendingDialogueContext = innContext;

    const OpenYAMM::Game::EventDialogContent innDialog = harness.buildPendingDialogContent(0, true);
    const bool showsFredrickTitle = innDialog.title == "Fredrick Talimere";
    const bool showsFredrickAction = dialogHasActionLabel(innDialog, "Fredrick Talimere");
    const bool showsFredrick = showsFredrickTitle || showsFredrickAction;

    CHECK(showsFredrick);
    CHECK_FALSE(dialogHasActionLabel(innDialog, "Rent room for 5 gold"));
    CHECK_FALSE(dialogHasActionLabel(innDialog, "Fill packs to 14 days for 2 gold"));
    CHECK_FALSE(dialogHasActionLabel(innDialog, "Play Arcomage"));
}

TEST_CASE("adventurers inn hire moves character into party")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::RosterEntry *pRosterEntry = gameData.rosterTable.get(3);
    const OpenYAMM::Game::NpcEntry *pNpcEntry =
        pRosterEntry != nullptr ? gameData.npcDialogTable.findNpcByName(pRosterEntry->name) : nullptr;

    REQUIRE(pRosterEntry != nullptr);
    REQUIRE(harness.party().addAdventurersInnMember(*pRosterEntry, pNpcEntry != nullptr ? pNpcEntry->pictureId : 0));

    const size_t initialPartyCount = harness.party().members().size();

    REQUIRE(harness.party().hireAdventurersInnMember(0));
    CHECK_EQ(harness.party().members().size(), initialPartyCount + 1);
    CHECK(harness.party().hasRosterMember(3));
    CHECK(harness.party().adventurersInnMembers().empty());
}

TEST_CASE("adventurers inn hire preserves roster spell knowledge")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::RosterEntry *pRosterEntry = gameData.rosterTable.get(1);

    REQUIRE(pRosterEntry != nullptr);
    REQUIRE(harness.party().addAdventurersInnMember(*pRosterEntry, 0));
    REQUIRE(harness.party().hireAdventurersInnMember(0));

    const OpenYAMM::Game::Character *pHiredMember = findPartyMemberByRosterId(harness.party(), 1);
    REQUIRE(pHiredMember != nullptr);

    CHECK(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::TorchLight)));
    CHECK(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::FireBolt)));
    CHECK(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::WizardEye)));
    CHECK(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::FeatherFall)));
    CHECK(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Reanimate)));
    CHECK(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::ToxicCloud)));
    CHECK(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::VampiricWeapon)));

    CHECK_FALSE(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Inferno)));
    CHECK_FALSE(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Fly)));
    CHECK_FALSE(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::PainReflection)));
}

TEST_CASE("party dismiss moves member to adventurers inn tail")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE_GE(harness.party().members().size(), 3u);

    const size_t dismissedMemberIndex = 1;
    const std::string dismissedName = harness.party().members()[dismissedMemberIndex].name;
    const size_t initialPartyCount = harness.party().members().size();
    const size_t initialInnCount = harness.party().adventurersInnMembers().size();

    CHECK_FALSE(harness.party().dismissMemberToAdventurersInn(0));
    REQUIRE(harness.party().dismissMemberToAdventurersInn(dismissedMemberIndex));

    CHECK_EQ(harness.party().members().size(), initialPartyCount - 1);
    CHECK_EQ(harness.party().adventurersInnMembers().size(), initialInnCount + 1);

    const OpenYAMM::Game::AdventurersInnMember *pDismissedMember =
        harness.party().adventurersInnMember(harness.party().adventurersInnMembers().size() - 1);

    REQUIRE(pDismissedMember != nullptr);
    CHECK_EQ(pDismissedMember->character.name, dismissedName);
    CHECK_EQ(harness.party().lastStatus(), "party member dismissed");
}

TEST_CASE("adventurers inn roster members use roster portraits and identified items")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::RosterEntry *pRosterEntry = gameData.rosterTable.get(1);

    REQUIRE(pRosterEntry != nullptr);
    REQUIRE(harness.party().addAdventurersInnMember(*pRosterEntry, 1));

    const OpenYAMM::Game::AdventurersInnMember *pInnMember = harness.party().adventurersInnMember(0);

    REQUIRE(pInnMember != nullptr);
    CHECK_EQ(pInnMember->portraitPictureId, 2909u);

    for (const OpenYAMM::Game::InventoryItem &item : pInnMember->character.inventory)
    {
        CHECK(item.identified);
    }

    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.mainHand,
        pInnMember->character.equipment.mainHand));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.offHand,
        pInnMember->character.equipment.offHand));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.bow,
        pInnMember->character.equipment.bow));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.armor,
        pInnMember->character.equipment.armor));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.helm,
        pInnMember->character.equipment.helm));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.belt,
        pInnMember->character.equipment.belt));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.cloak,
        pInnMember->character.equipment.cloak));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.gauntlets,
        pInnMember->character.equipment.gauntlets));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.boots,
        pInnMember->character.equipment.boots));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.amulet,
        pInnMember->character.equipment.amulet));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.ring1,
        pInnMember->character.equipment.ring1));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.ring2,
        pInnMember->character.equipment.ring2));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.ring3,
        pInnMember->character.equipment.ring3));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.ring4,
        pInnMember->character.equipment.ring4));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.ring5,
        pInnMember->character.equipment.ring5));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.ring6,
        pInnMember->character.equipment.ring6));
}

TEST_CASE("transport action spends gold advances time and queues map move")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(WindlingBoatHouseId);

    REQUIRE(pHouseEntry != nullptr);

    harness.party().addGold(1000);
    const float initialGameMinutes = harness.worldRuntime().gameMinutes();
    const int initialGold = harness.party().gold();
    const OpenYAMM::Game::Character *pMember = harness.party().activeMember();
    REQUIRE(pMember != nullptr);
    const int expectedPrice = OpenYAMM::Game::PriceCalculator::transportPrice(pMember, *pHouseEntry, true);
    OpenYAMM::Game::Character *pActiveMember = harness.party().activeMember();
    REQUIRE(pActiveMember != nullptr);

    harness.party().applyPartyBuff(
        OpenYAMM::Game::PartyBuffId::TorchLight,
        600.0f,
        1,
        0,
        0,
        OpenYAMM::Game::SkillMastery::None,
        0);
    pActiveMember->health = std::max(1, pActiveMember->health - 20);
    pActiveMember->spellPoints = std::max(0, pActiveMember->spellPoints - 5);
    pActiveMember->recoverySecondsRemaining = 3.0f;
    pActiveMember->levelModifier = 30;
    pActiveMember->armorClassModifier = 40;
    pActiveMember->ageModifier = 5;
    pActiveMember->magicalBonuses.might = 25;
    pActiveMember->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Weak));
    pActiveMember->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Fear));

    const std::vector<OpenYAMM::Game::HouseActionOption> actions = OpenYAMM::Game::buildHouseActionOptions(
        *pHouseEntry,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        0.0f,
        OpenYAMM::Game::DialogueMenuId::None);
    const std::optional<OpenYAMM::Game::HouseActionOption> action =
        findHouseActionById(actions, OpenYAMM::Game::HouseActionId::TransportRoute);

    REQUIRE(action.has_value());
    const OpenYAMM::Game::HouseActionResult result = OpenYAMM::Game::performHouseAction(
        *action,
        *pHouseEntry,
        harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime());

    CHECK(result.succeeded);
    REQUIRE(result.soundType.has_value());
    CHECK_EQ(*result.soundType, OpenYAMM::Game::HouseSoundType::TransportTravel);
    CHECK_EQ(harness.party().gold(), initialGold - expectedPrice);
    CHECK_EQ(harness.worldRuntime().gameMinutes(), doctest::Approx(initialGameMinutes + 4.0f * 24.0f * 60.0f));

    pActiveMember = harness.party().activeMember();
    REQUIRE(pActiveMember != nullptr);
    CHECK_EQ(pActiveMember->health, pActiveMember->maxHealth);
    CHECK_EQ(pActiveMember->spellPoints, pActiveMember->maxSpellPoints);
    CHECK_FALSE(pActiveMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Weak)));
    CHECK_FALSE(pActiveMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Fear)));
    CHECK_EQ(pActiveMember->recoverySecondsRemaining, doctest::Approx(0.0f));
    CHECK_EQ(pActiveMember->levelModifier, 0);
    CHECK_EQ(pActiveMember->armorClassModifier, 0);
    CHECK_EQ(pActiveMember->ageModifier, 0);
    CHECK_EQ(pActiveMember->magicalBonuses.might, 0);
    CHECK_FALSE(harness.party().hasPartyBuff(OpenYAMM::Game::PartyBuffId::TorchLight));

    const OpenYAMM::Game::EventRuntimeState *pWorldRuntimeState = harness.worldRuntime().eventRuntimeState();

    REQUIRE(pWorldRuntimeState != nullptr);
    const std::optional<OpenYAMM::Game::EventRuntimeState::PendingMapMove> &pendingMapMove =
        pWorldRuntimeState->pendingMapMove;

    REQUIRE(pendingMapMove.has_value());
    REQUIRE(pendingMapMove->mapName.has_value());
    CHECK_EQ(*pendingMapMove->mapName, "Out02.odm");
    CHECK_EQ(pendingMapMove->x, 8609);
    CHECK_EQ(pendingMapMove->y, -15609);
    CHECK_EQ(pendingMapMove->z, 265);
    REQUIRE(pendingMapMove->directionDegrees.has_value());
    CHECK_EQ(*pendingMapMove->directionDegrees, 0);
    CHECK_FALSE(pendingMapMove->useMapStartPosition);
}

TEST_CASE("outdoor transition map move applies travel rest food and temporary reset")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    OpenYAMM::Game::MapStatsEntry currentMap = {};
    currentMap.name = "Ravenshore";
    currentMap.fileName = "Out02.odm";
    harness.setCurrentMap(currentMap);

    OpenYAMM::Game::EventRuntimeState::PendingMapMove mapMove = {};
    mapMove.mapName = std::string("Out06.odm");
    mapMove.x = 100;
    mapMove.y = 200;
    mapMove.z = 300;

    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext pendingContext = {};
    pendingContext.kind = OpenYAMM::Game::DialogueContextKind::MapTransition;
    pendingContext.transitionMapMove = mapMove;
    harness.eventRuntimeState().pendingDialogueContext = pendingContext;

    harness.party().addFood(10);
    const int initialFood = harness.party().food();
    harness.party().applyPartyBuff(
        OpenYAMM::Game::PartyBuffId::TorchLight,
        600.0f,
        1,
        0,
        0,
        OpenYAMM::Game::SkillMastery::None,
        0);

    OpenYAMM::Game::Character *pActiveMember = harness.party().activeMember();
    REQUIRE(pActiveMember != nullptr);
    pActiveMember->health = std::max(1, pActiveMember->health - 20);
    pActiveMember->spellPoints = std::max(0, pActiveMember->spellPoints - 5);
    pActiveMember->levelModifier = 30;
    pActiveMember->armorClassModifier = 40;
    pActiveMember->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Weak));

    const float initialGameMinutes = harness.worldRuntime().gameMinutes();
    const OpenYAMM::Game::EventDialogContent &dialog = harness.presentPendingDialog(0, true);
    std::optional<size_t> confirmIndex;

    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        if (dialog.actions[actionIndex].kind == OpenYAMM::Game::EventDialogActionKind::MapTransitionConfirm)
        {
            confirmIndex = actionIndex;
            break;
        }
    }

    REQUIRE(confirmIndex.has_value());
    const OpenYAMM::Game::GameplayDialogController::Result result =
        harness.executeActiveDialogAction(*confirmIndex);

    CHECK(result.shouldCloseActiveDialog);
    CHECK_EQ(harness.worldRuntime().gameMinutes(), doctest::Approx(initialGameMinutes + 5.0f * 24.0f * 60.0f));
    CHECK_EQ(harness.party().food(), initialFood - 5);

    pActiveMember = harness.party().activeMember();
    REQUIRE(pActiveMember != nullptr);
    CHECK_EQ(pActiveMember->health, pActiveMember->maxHealth);
    CHECK_EQ(pActiveMember->spellPoints, pActiveMember->maxSpellPoints);
    CHECK_EQ(pActiveMember->levelModifier, 0);
    CHECK_EQ(pActiveMember->armorClassModifier, 0);
    CHECK_FALSE(pActiveMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Weak)));
    CHECK_FALSE(harness.party().hasPartyBuff(OpenYAMM::Game::PartyBuffId::TorchLight));

    REQUIRE(harness.eventRuntimeState().pendingMapMove.has_value());
    CHECK_EQ(harness.eventRuntimeState().pendingMapMove->mapName, std::optional<std::string>("Out06.odm"));
}

TEST_CASE("zero day map transition preserves party resources and temporary effects")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    OpenYAMM::Game::MapStatsEntry currentMap = {};
    currentMap.name = "Ravenshore";
    currentMap.fileName = "Out02.odm";
    currentMap.eastTransition.emplace();
    currentMap.eastTransition->destinationMapFileName = "D18.blv";
    currentMap.eastTransition->travelDays = 0;
    harness.setCurrentMap(currentMap);

    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext pendingContext = {};
    pendingContext.kind = OpenYAMM::Game::DialogueContextKind::MapTransition;
    pendingContext.sourceId = static_cast<uint32_t>(OpenYAMM::Game::MapBoundaryEdge::East);
    harness.eventRuntimeState().pendingDialogueContext = pendingContext;

    harness.party().addFood(10);
    const int initialFood = harness.party().food();
    harness.party().applyPartyBuff(
        OpenYAMM::Game::PartyBuffId::TorchLight,
        600.0f,
        1,
        0,
        0,
        OpenYAMM::Game::SkillMastery::None,
        0);

    OpenYAMM::Game::Character *pActiveMember = harness.party().activeMember();
    REQUIRE(pActiveMember != nullptr);
    pActiveMember->health = std::max(1, pActiveMember->health - 20);
    pActiveMember->spellPoints = std::max(0, pActiveMember->spellPoints - 5);
    pActiveMember->levelModifier = 30;
    pActiveMember->armorClassModifier = 40;
    pActiveMember->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Weak));

    const int initialHealth = pActiveMember->health;
    const int initialSpellPoints = pActiveMember->spellPoints;
    const float initialGameMinutes = harness.worldRuntime().gameMinutes();

    const OpenYAMM::Game::EventDialogContent &dialog = harness.presentPendingDialog(0, true);
    std::optional<size_t> confirmIndex;

    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        if (dialog.actions[actionIndex].kind == OpenYAMM::Game::EventDialogActionKind::MapTransitionConfirm)
        {
            confirmIndex = actionIndex;
            break;
        }
    }

    REQUIRE(confirmIndex.has_value());
    const OpenYAMM::Game::GameplayDialogController::Result result =
        harness.executeActiveDialogAction(*confirmIndex);

    CHECK(result.shouldCloseActiveDialog);
    CHECK_EQ(harness.worldRuntime().gameMinutes(), doctest::Approx(initialGameMinutes));
    CHECK_EQ(harness.party().food(), initialFood);

    pActiveMember = harness.party().activeMember();
    REQUIRE(pActiveMember != nullptr);
    CHECK_EQ(pActiveMember->health, initialHealth);
    CHECK_EQ(pActiveMember->spellPoints, initialSpellPoints);
    CHECK_EQ(pActiveMember->levelModifier, 30);
    CHECK_EQ(pActiveMember->armorClassModifier, 40);
    CHECK(pActiveMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Weak)));
    CHECK(harness.party().hasPartyBuff(OpenYAMM::Game::PartyBuffId::TorchLight));

    REQUIRE(harness.eventRuntimeState().pendingMapMove.has_value());
    CHECK_EQ(harness.eventRuntimeState().pendingMapMove->mapName, std::optional<std::string>("D18.blv"));
}

TEST_CASE("merged transport tables drive mm8 boat routes")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(WindBoatHouseId);

    REQUIRE(pHouseEntry != nullptr);
    REQUIRE_EQ(pHouseEntry->transportRoutes.size(), 2u);
    CHECK_EQ(pHouseEntry->transportRoutes[0].destinationName, "Ravage Roaming");
    CHECK_EQ(pHouseEntry->transportRoutes[0].mapFileName, "Out08.odm");
    CHECK_EQ(pHouseEntry->transportRoutes[0].travelDays, 4u);
    CHECK_EQ(pHouseEntry->transportRoutes[0].requiredQBit, 10u);
    harness.party().setQuestBit(10, true);

    std::vector<OpenYAMM::Game::HouseActionOption> actions = OpenYAMM::Game::buildHouseActionOptions(
        *pHouseEntry,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);

    CHECK(houseActionsContainDestination(actions, "Ravage Roaming"));
    CHECK_FALSE(houseActionsContainDestination(actions, "Shadowspire"));

    harness.worldRuntime().advanceGameMinutes(2.0f * 24.0f * 60.0f);
    actions = OpenYAMM::Game::buildHouseActionOptions(
        *pHouseEntry,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);

    CHECK_FALSE(houseActionsContainDestination(actions, "Ravage Roaming"));
    CHECK(houseActionsContainDestination(actions, "Shadowspire"));
}

TEST_CASE("merged transport tables populate mm6 stable and boat routes")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pStableHouse = gameData.houseTable.get(NewSorpigalStableHouseId);
    const OpenYAMM::Game::HouseEntry *pBoatHouse = gameData.houseTable.get(NewSorpigalBoatHouseId);

    REQUIRE(pStableHouse != nullptr);
    REQUIRE(pBoatHouse != nullptr);
    REQUIRE_FALSE(pStableHouse->transportRoutes.empty());
    REQUIRE_FALSE(pBoatHouse->transportRoutes.empty());

    CHECK_EQ(pStableHouse->transportRoutes.front().destinationName, "Castle Ironfist");
    CHECK_EQ(pStableHouse->transportRoutes.front().mapFileName, "Outd3.odm");
    CHECK_EQ(pStableHouse->transportRoutes.front().travelDays, 2u);
    CHECK_EQ(pStableHouse->transportRoutes.front().x, 14317);
    CHECK_EQ(pStableHouse->transportRoutes.front().y, 2696);
    CHECK_EQ(pStableHouse->transportRoutes.front().z, 96);
    CHECK_EQ(pStableHouse->transportRoutes.front().directionDegrees, 180);

    std::vector<OpenYAMM::Game::HouseActionOption> actions = OpenYAMM::Game::buildHouseActionOptions(
        *pStableHouse,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        0.0f,
        OpenYAMM::Game::DialogueMenuId::None);

    CHECK(houseActionsContainDestination(actions, "Castle Ironfist"));

    actions = OpenYAMM::Game::buildHouseActionOptions(
        *pBoatHouse,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        24.0f * 60.0f,
        OpenYAMM::Game::DialogueMenuId::None);

    CHECK_EQ(pBoatHouse->transportRoutes.front().destinationName, "Misty Islands");
    CHECK_EQ(pBoatHouse->transportRoutes.front().mapFileName, "Oute2.odm");
    CHECK(houseActionsContainDestination(actions, "Misty Islands"));
}

TEST_CASE("mm6 loretta price fixing appears as a stable house action")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pStableHouse = gameData.houseTable.get(NewSorpigalStableHouseId);

    REQUIRE(pStableHouse != nullptr);

    std::vector<OpenYAMM::Game::HouseActionOption> actions = OpenYAMM::Game::buildHouseActionOptions(
        *pStableHouse,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        12.0f * 60.0f,
        OpenYAMM::Game::DialogueMenuId::None);

    CHECK_FALSE(findHouseActionById(actions, OpenYAMM::Game::HouseActionId::LorettaPriceFixing).has_value());

    harness.party().setQuestBit(1140, true);
    actions = OpenYAMM::Game::buildHouseActionOptions(
        *pStableHouse,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        12.0f * 60.0f,
        OpenYAMM::Game::DialogueMenuId::None);

    const std::optional<OpenYAMM::Game::HouseActionOption> priceFixingAction =
        findHouseActionById(actions, OpenYAMM::Game::HouseActionId::LorettaPriceFixing);

    REQUIRE(priceFixingAction.has_value());
    CHECK_EQ(priceFixingAction->label, "Price Fixing");

    const OpenYAMM::Game::HouseActionResult priceFixingResult = OpenYAMM::Game::performHouseAction(
        *priceFixingAction,
        *pStableHouse,
        harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime());

    CHECK(priceFixingResult.succeeded);
    REQUIRE_FALSE(priceFixingResult.messages.empty());
    CHECK(priceFixingResult.messages.front().find("Loretta's got a new scheme") != std::string::npos);
    CHECK(harness.party().hasQuestBit(1523));
    CHECK_FALSE(harness.party().hasQuestBit(1141));

    actions = OpenYAMM::Game::buildHouseActionOptions(
        *pStableHouse,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        12.0f * 60.0f,
        OpenYAMM::Game::DialogueMenuId::None);

    CHECK_FALSE(findHouseActionById(actions, OpenYAMM::Game::HouseActionId::LorettaPriceFixing).has_value());
}

TEST_CASE("merged house movie sound bases drive mm8 house speech")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    struct ExpectedHouseSound
    {
        uint32_t houseId = 0;
        uint32_t expectedBaseId = 0;
        uint32_t expectedGreetingId = 0;
    };

    const ExpectedHouseSound expectedSounds[] = {
        {4, 33500, 33501},
        {37, 33600, 33601},
        {232, 34200, 34201},
        {306, 33400, 33401},
        {1567, 34000, 34001},
    };

    for (const ExpectedHouseSound &expected : expectedSounds)
    {
        const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(expected.houseId);

        REQUIRE(pHouseEntry != nullptr);
        CHECK_EQ(pHouseEntry->roomSoundId, 0);
        CHECK_EQ(pHouseEntry->houseSoundBaseId, expected.expectedBaseId);

        const std::optional<uint32_t> greetingSoundId =
            OpenYAMM::Game::deriveHouseSoundId(*pHouseEntry, OpenYAMM::Game::HouseSoundType::GeneralGreeting);

        REQUIRE(greetingSoundId.has_value());
        CHECK_EQ(*greetingSoundId, expected.expectedGreetingId);
    }
}

TEST_CASE("transport route quest bit gates show unavailable fallback until unlocked")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(WindBoatHouseId);

    REQUIRE(pHouseEntry != nullptr);

    std::vector<OpenYAMM::Game::HouseActionOption> actions = OpenYAMM::Game::buildHouseActionOptions(
        *pHouseEntry,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);

    REQUIRE_EQ(actions.size(), 1);
    CHECK_EQ(actions.front().label, "Sorry, come back another day");
    CHECK_FALSE(actions.front().enabled);

    harness.party().setQuestBit(10, true);
    actions = OpenYAMM::Game::buildHouseActionOptions(
        *pHouseEntry,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);

    REQUIRE_EQ(actions.size(), 1);
    CHECK(actions.front().enabled);
    CHECK(houseActionsContainDestination(actions, "Ravage Roaming"));
}

TEST_CASE("transport route travel time is clamped to at least one day")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    OpenYAMM::Game::HouseEntry houseEntry = {};
    houseEntry.id = 99999;
    houseEntry.type = "Boats";
    houseEntry.priceMultiplier = 1.0f;

    OpenYAMM::Game::HouseEntry::TransportRoute route = {};
    route.routeIndex = 1;
    route.destinationName = "Test Harbor";
    route.mapFileName = "Out02.odm";
    route.travelDays = 0;
    route.useMapStartPosition = true;
    houseEntry.transportRoutes.push_back(route);

    harness.party().addGold(1000);
    const float initialGameMinutes = harness.worldRuntime().gameMinutes();
    const std::vector<OpenYAMM::Game::HouseActionOption> actions = OpenYAMM::Game::buildHouseActionOptions(
        houseEntry,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);

    REQUIRE_EQ(actions.size(), 1);
    CHECK(actions.front().label.find("1 day to Test Harbor") != std::string::npos);

    const OpenYAMM::Game::HouseActionResult result = OpenYAMM::Game::performHouseAction(
        actions.front(),
        houseEntry,
        harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime());

    CHECK(result.succeeded);
    CHECK_EQ(harness.worldRuntime().gameMinutes(), doctest::Approx(initialGameMinutes + 24.0f * 60.0f));
    REQUIRE_FALSE(result.messages.empty());
    CHECK_EQ(result.messages.front(), "It will take 1 day to travel to Test Harbor.");
}

TEST_CASE("transport route travel time uses hired NPC travel reductions")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    OpenYAMM::Game::HouseEntry houseEntry = {};
    houseEntry.id = 99998;
    houseEntry.type = "Boats";
    houseEntry.priceMultiplier = 1.0f;

    OpenYAMM::Game::HouseEntry::TransportRoute route = {};
    route.routeIndex = 1;
    route.destinationName = "Test Harbor";
    route.mapFileName = "Out02.odm";
    route.travelDays = 5;
    route.useMapStartPosition = true;
    houseEntry.transportRoutes.push_back(route);

    OpenYAMM::Game::EventRuntimeState::HiredNpcFollower navigator = {};
    navigator.npcId = 1184;
    navigator.professionId = 9;
    navigator.weeklyCost = 300;
    harness.eventRuntimeState().hiredNpcFollowers.push_back(navigator);

    harness.party().addGold(1000);
    const float initialGameMinutes = harness.worldRuntime().gameMinutes();
    const std::vector<OpenYAMM::Game::HouseActionOption> actions = OpenYAMM::Game::buildHouseActionOptions(
        houseEntry,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);

    REQUIRE_EQ(actions.size(), 1);
    CHECK(actions.front().label.find("2 days to Test Harbor") != std::string::npos);

    const OpenYAMM::Game::HouseActionResult result = OpenYAMM::Game::performHouseAction(
        actions.front(),
        houseEntry,
        harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime());

    CHECK(result.succeeded);
    CHECK_EQ(harness.worldRuntime().gameMinutes(), doctest::Approx(initialGameMinutes + 2.0f * 24.0f * 60.0f));
    REQUIRE_FALSE(result.messages.empty());
    CHECK_EQ(result.messages.front(), "It will take 2 days to travel to Test Harbor.");
}

TEST_CASE("transport route override changes visible route and travel target")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    OpenYAMM::Game::HouseEntry houseEntry = {};
    houseEntry.id = 99997;
    houseEntry.type = "Stables";
    houseEntry.priceMultiplier = 1.0f;

    OpenYAMM::Game::HouseEntry::TransportRoute route = {};
    route.routeIndex = 1;
    route.destinationName = "Base Route";
    route.mapFileName = "base.odm";
    route.travelDays = 1;
    houseEntry.transportRoutes.push_back(route);

    OpenYAMM::Game::EventRuntimeState::TransportRouteOverride overrideRoute = {};
    overrideRoute.houseId = houseEntry.id;
    overrideRoute.routeIndex = 1;
    overrideRoute.destinationName = "Override Route";
    overrideRoute.mapFileName = "override.odm";
    overrideRoute.travelDays = 4;
    overrideRoute.x = 11;
    overrideRoute.y = 22;
    overrideRoute.z = 33;
    overrideRoute.directionDegrees = 180;
    harness.eventRuntimeState().transportRouteOverrides[
        OpenYAMM::Game::EventRuntime::transportRouteOverrideKey(houseEntry.id, 1)] = overrideRoute;
    const uint64_t routeOverrideKey =
        OpenYAMM::Game::EventRuntime::transportRouteOverrideKey(houseEntry.id, 1);

    harness.party().addGold(1000);
    const std::vector<OpenYAMM::Game::HouseActionOption> actions = OpenYAMM::Game::buildHouseActionOptions(
        houseEntry,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);

    REQUIRE_EQ(actions.size(), 1);
    REQUIRE(harness.eventRuntimeState().transportRouteOverrides.contains(routeOverrideKey));
    CHECK(actions.front().label.find("Override Route") != std::string::npos);
    CHECK(actions.front().label.find("Base Route") == std::string::npos);

    const OpenYAMM::Game::HouseActionResult result = OpenYAMM::Game::performHouseAction(
        actions.front(),
        houseEntry,
        harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime());

    CHECK(result.succeeded);
    REQUIRE(harness.eventRuntimeState().pendingMapMove.has_value());
    CHECK_EQ(harness.eventRuntimeState().pendingMapMove->mapName, std::optional<std::string>("override.odm"));
    CHECK_EQ(harness.eventRuntimeState().pendingMapMove->x, 11);
    CHECK_EQ(harness.eventRuntimeState().pendingMapMove->directionDegrees, std::optional<int32_t>(180));
    REQUIRE_FALSE(result.messages.empty());
    CHECK_EQ(result.messages.front(), "It will take 4 days to travel to Override Route.");
}

TEST_CASE("tavern rent room defers recovery until rest screen")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pTavernHouse = gameData.houseTable.get(DaggerWoundTavernHouseId);

    REQUIRE(pTavernHouse != nullptr);

    OpenYAMM::Game::Character *pTavernMember = harness.party().activeMember();
    REQUIRE(pTavernMember != nullptr);

    harness.party().addGold(1000);
    harness.party().applyPartyBuff(
        OpenYAMM::Game::PartyBuffId::WizardEye,
        600.0f,
        1,
        0,
        0,
        OpenYAMM::Game::SkillMastery::None,
        0);
    const int initialHealth = std::max(1, pTavernMember->health - 17);
    const int initialSpellPoints = std::max(0, pTavernMember->spellPoints - 4);
    pTavernMember->health = initialHealth;
    pTavernMember->spellPoints = initialSpellPoints;
    pTavernMember->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Asleep));
    pTavernMember->recoverySecondsRemaining = 2.0f;
    const float initialGameMinutes = harness.worldRuntime().gameMinutes();

    const OpenYAMM::Game::HouseActionResult tavernResult = OpenYAMM::Game::performHouseAction(
        OpenYAMM::Game::HouseActionOption{
            OpenYAMM::Game::HouseActionId::TavernRentRoom,
            "Rent room",
            "",
            true,
            ""},
        *pTavernHouse,
        harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime());

    CHECK(tavernResult.succeeded);
    REQUIRE(tavernResult.pendingInnRest.has_value());
    CHECK_EQ(tavernResult.pendingInnRest->houseId, pTavernHouse->id);
    REQUIRE(tavernResult.soundType.has_value());
    CHECK_EQ(*tavernResult.soundType, OpenYAMM::Game::HouseSoundType::TavernRentRoom);
    CHECK_EQ(harness.worldRuntime().gameMinutes(), doctest::Approx(initialGameMinutes));
    CHECK_EQ(pTavernMember->health, initialHealth);
    CHECK_EQ(pTavernMember->spellPoints, initialSpellPoints);
    CHECK_EQ(pTavernMember->recoverySecondsRemaining, doctest::Approx(2.0f));
    CHECK(pTavernMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Asleep)));
    CHECK(harness.party().hasPartyBuff(OpenYAMM::Game::PartyBuffId::WizardEye));
}

TEST_CASE("house actions expose mmmerge speech reactions for service outcomes")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pTavernHouse = gameData.houseTable.get(DaggerWoundTavernHouseId);
    const OpenYAMM::Game::HouseEntry *pGuildHouse = gameData.houseTable.get(ElementalGuildHouseId);
    const OpenYAMM::Game::HouseEntry *pTempleHouse = gameData.houseTable.get(TempleHouseId);

    REQUIRE(pTavernHouse != nullptr);
    REQUIRE(pGuildHouse != nullptr);
    REQUIRE(pTempleHouse != nullptr);

    harness.party().addFood(100);
    const OpenYAMM::Game::HouseActionResult fullPacksResult = OpenYAMM::Game::performHouseAction(
        OpenYAMM::Game::HouseActionOption{
            OpenYAMM::Game::HouseActionId::TavernBuyFood,
            "Buy food",
            "",
            true,
            ""},
        *pTavernHouse,
        harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime());

    CHECK_FALSE(fullPacksResult.succeeded);
    CHECK_EQ(fullPacksResult.speechId, OpenYAMM::Game::SpeechId::TavernPacksFull);

    harness.party().addGold(-harness.party().gold());
    const OpenYAMM::Game::HouseActionResult noGoldResult = OpenYAMM::Game::performHouseAction(
        OpenYAMM::Game::HouseActionOption{
            OpenYAMM::Game::HouseActionId::TempleDonate,
            "Donate",
            "",
            true,
            ""},
        *pTempleHouse,
        harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime());

    CHECK_FALSE(noGoldResult.succeeded);
    CHECK_EQ(noGoldResult.speechId, OpenYAMM::Game::SpeechId::NotEnoughGold);

    harness.party().addGold(10000);
    REQUIRE(harness.party().setActiveMemberIndex(3));
    const OpenYAMM::Game::HouseActionResult learnSkillResult = OpenYAMM::Game::performHouseAction(
        OpenYAMM::Game::HouseActionOption{
            OpenYAMM::Game::HouseActionId::LearnSkill,
            "Learn",
            "AirMagic",
            true,
            ""},
        *pGuildHouse,
        harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime());

    CHECK(learnSkillResult.succeeded);
    CHECK_EQ(learnSkillResult.speechId, OpenYAMM::Game::SpeechId::SkillLearned);
}

TEST_CASE("temple donate applies oe reputation gating and buffs")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pTempleHouse = gameData.houseTable.get(TempleHouseId);

    REQUIRE(pTempleHouse != nullptr);

    harness.party().addGold(5000);
    harness.worldRuntime().advanceGameMinutes(24.0f * 60.0f);
    harness.worldRuntime().setCurrentLocationReputation(-25);

    OpenYAMM::Game::Character *pWeakMember = harness.party().member(1);
    REQUIRE(pWeakMember != nullptr);

    pWeakMember->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Weak));
    const int donationPrice = std::max(1, static_cast<int>(std::round(pTempleHouse->priceMultiplier)));
    const int initialGold = harness.party().gold();

    for (int donationIndex = 0; donationIndex < 3; ++donationIndex)
    {
        const OpenYAMM::Game::HouseActionResult result = OpenYAMM::Game::performHouseAction(
            OpenYAMM::Game::HouseActionOption{
                OpenYAMM::Game::HouseActionId::TempleDonate,
                "Donate",
                "",
                true,
                ""},
            *pTempleHouse,
            harness.party(),
            &gameData.classSkillTable,
            &harness.worldRuntime());

        CHECK(result.succeeded);
        CHECK(result.messages == std::vector<std::string>{"Thank You"});
    }

    CHECK_EQ(harness.party().gold(), initialGold - donationPrice * 3);
    CHECK_EQ(harness.worldRuntime().currentLocationReputation(), -25);
    CHECK_EQ(
        harness.eventRuntimeState().dialogueState.templeDonationCounters[harness.party().activeMemberIndex()],
        3);

    const OpenYAMM::Game::PartyBuffState *pWizardEye =
        harness.party().partyBuff(OpenYAMM::Game::PartyBuffId::WizardEye);
    const OpenYAMM::Game::PartyBuffState *pFeatherFall =
        harness.party().partyBuff(OpenYAMM::Game::PartyBuffId::FeatherFall);
    const OpenYAMM::Game::PartyBuffState *pProtectionFromMagic =
        harness.party().partyBuff(OpenYAMM::Game::PartyBuffId::ProtectionFromMagic);
    const OpenYAMM::Game::PartyBuffState *pHeroism =
        harness.party().partyBuff(OpenYAMM::Game::PartyBuffId::Heroism);
    const OpenYAMM::Game::PartyBuffState *pShield =
        harness.party().partyBuff(OpenYAMM::Game::PartyBuffId::Shield);
    const OpenYAMM::Game::PartyBuffState *pStoneskin =
        harness.party().partyBuff(OpenYAMM::Game::PartyBuffId::Stoneskin);
    const OpenYAMM::Game::PartyBuffState *pBodyResistance =
        harness.party().partyBuff(OpenYAMM::Game::PartyBuffId::BodyResistance);

    REQUIRE(pFeatherFall != nullptr);
    CHECK(pFeatherFall->active());
    CHECK_EQ(pFeatherFall->remainingSeconds, doctest::Approx(43200.0f));

    REQUIRE(pWizardEye != nullptr);
    CHECK(pWizardEye->active());
    CHECK_EQ(pWizardEye->remainingSeconds, doctest::Approx(43200.0f));
    CHECK_EQ(pWizardEye->power, 0);

    REQUIRE(pProtectionFromMagic != nullptr);
    CHECK(pProtectionFromMagic->active());
    CHECK_EQ(pProtectionFromMagic->remainingSeconds, doctest::Approx(10800.0f));
    CHECK_EQ(pProtectionFromMagic->power, 3);

    REQUIRE(pHeroism != nullptr);
    CHECK(pHeroism->active());
    CHECK_EQ(pHeroism->remainingSeconds, doctest::Approx(14400.0f));
    CHECK_EQ(pHeroism->power, 8);

    REQUIRE(pShield != nullptr);
    CHECK(pShield->active());
    CHECK_EQ(pShield->remainingSeconds, doctest::Approx(14400.0f));

    REQUIRE(pStoneskin != nullptr);
    CHECK(pStoneskin->active());
    CHECK_EQ(pStoneskin->remainingSeconds, doctest::Approx(14400.0f));
    CHECK_EQ(pStoneskin->power, 8);

    REQUIRE(pBodyResistance != nullptr);
    CHECK(pBodyResistance->active());
    CHECK_EQ(pBodyResistance->remainingSeconds, doctest::Approx(43200.0f));
    CHECK_EQ(pBodyResistance->power, 12);

    CHECK_FALSE(harness.party().hasPartyBuff(OpenYAMM::Game::PartyBuffId::Haste));

    for (size_t memberIndex = 0; memberIndex < harness.party().members().size(); ++memberIndex)
    {
        const OpenYAMM::Game::CharacterBuffState *pBless =
            harness.party().characterBuff(memberIndex, OpenYAMM::Game::CharacterBuffId::Bless);
        const OpenYAMM::Game::CharacterBuffState *pPreservation =
            harness.party().characterBuff(memberIndex, OpenYAMM::Game::CharacterBuffId::Preservation);

        REQUIRE(pBless != nullptr);
        CHECK(pBless->active());
        CHECK_EQ(pBless->remainingSeconds, doctest::Approx(14400.0f));
        CHECK_EQ(pBless->power, 8);

        REQUIRE(pPreservation != nullptr);
        CHECK(pPreservation->active());
        CHECK_EQ(pPreservation->remainingSeconds, doctest::Approx(4500.0f));
    }

    REQUIRE_EQ(harness.eventRuntimeState().spellFxRequests.size(), 5u);
    CHECK_EQ(
        harness.eventRuntimeState().spellFxRequests.front().spellId,
        OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Bless));
}

TEST_CASE("empty house after departure")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    harness.eventRuntimeState().unavailableNpcIds.insert(FredrickNpcId);

    REQUIRE(harness.executeOut01LocalEvent(37));

    const OpenYAMM::Game::EventDialogContent &dialog = harness.presentPendingDialog(0, true);

    CHECK(dialog.lines.empty());
    CHECK(dialog.actions.empty());
}

TEST_CASE("event fountain heal and refresh status work")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    OpenYAMM::Game::Character *pMember = harness.party().activeMember();

    REQUIRE(pMember != nullptr);

    pMember->health = std::max(1, pMember->health - 40);
    const int expectedHealedHealth = std::min(pMember->maxHealth, pMember->health + 25);

    REQUIRE(harness.executeOut01LocalEvent(104));
    CHECK_EQ(pMember->health, expectedHealedHealth);
    REQUIRE_FALSE(harness.eventRuntimeState().statusMessages.empty());
    CHECK_EQ(harness.eventRuntimeState().statusMessages.back(), "Your Wounds begin to Heal");

    harness.eventRuntimeState().statusMessages.clear();
    pMember->health = pMember->maxHealth;

    REQUIRE(harness.executeOut01LocalEvent(104));
    REQUIRE_FALSE(harness.eventRuntimeState().statusMessages.empty());
    CHECK_EQ(harness.eventRuntimeState().statusMessages.back(), "Refreshing");
}

TEST_CASE("event luck fountain grants permanent bonus once")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    OpenYAMM::Game::Character *pMember = harness.party().activeMember();

    REQUIRE(pMember != nullptr);

    pMember->luck = 10;

    REQUIRE(harness.executeOut01LocalEvent(102));
    CHECK_EQ(pMember->luck, 12);
    REQUIRE_FALSE(harness.eventRuntimeState().statusMessages.empty());
    CHECK_EQ(harness.eventRuntimeState().statusMessages.back(), "Luck +2 (Permanent)");

    harness.eventRuntimeState().statusMessages.clear();

    REQUIRE(harness.executeOut01LocalEvent(102));
    REQUIRE(harness.executeOut01LocalEvent(102));
    REQUIRE(harness.executeOut01LocalEvent(102));
    CHECK_EQ(pMember->luck, 16);

    harness.eventRuntimeState().statusMessages.clear();

    REQUIRE(harness.executeOut01LocalEvent(102));
    CHECK_EQ(pMember->luck, 16);
    REQUIRE_FALSE(harness.eventRuntimeState().statusMessages.empty());
    CHECK_EQ(harness.eventRuntimeState().statusMessages.back(), "Refreshing");
}

TEST_CASE("event hidden well uses bank gold gate and mapvar progress")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness blockedHarness(gameData);
    OpenYAMM::Game::Character *pBlockedMember = blockedHarness.party().activeMember();

    REQUIRE(pBlockedMember != nullptr);

    pBlockedMember->luck = 14;
    blockedHarness.party().addGold(150);
    blockedHarness.party().depositGoldToBank(100);
    blockedHarness.party().addGold(-blockedHarness.party().gold());

    REQUIRE(blockedHarness.executeOut01LocalEvent(103));
    REQUIRE_FALSE(blockedHarness.eventRuntimeState().statusMessages.empty());
    CHECK_EQ(blockedHarness.eventRuntimeState().statusMessages.back(), "Refreshing");

    OpenYAMM::Tests::HouseDialogueTestHarness rewardHarness(gameData);
    OpenYAMM::Game::Character *pRewardMember = rewardHarness.party().activeMember();

    REQUIRE(pRewardMember != nullptr);

    pRewardMember->luck = 14;
    rewardHarness.party().addGold(-rewardHarness.party().gold());

    REQUIRE(rewardHarness.executeOut01LocalEvent(103));
    CHECK_EQ(rewardHarness.party().gold(), 1000);
    CHECK_EQ(rewardHarness.eventRuntimeState().mapVars[31], 1);

}

TEST_CASE("event beacon actual stat checks include temporary bonuses")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    OpenYAMM::Game::Character *pMember = harness.party().activeMember();

    REQUIRE(pMember != nullptr);

    pMember->endurance = 20;
    pMember->permanentBonuses.endurance = 0;
    pMember->magicalBonuses.endurance = 5;

    REQUIRE(harness.executeGlobalEvent(544));
    REQUIRE_FALSE(harness.eventRuntimeState().statusMessages.empty());
    CHECK_EQ(harness.eventRuntimeState().statusMessages.back(), "You win!");
}

TEST_CASE("event beacon actual stat checks include equipped item bonuses")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    OpenYAMM::Game::Character *pMember = harness.party().activeMember();

    REQUIRE(pMember != nullptr);

    pMember->endurance = 20;
    pMember->permanentBonuses.endurance = 0;
    pMember->magicalBonuses.endurance = 0;
    pMember->equipment.mainHand = 503;

    REQUIRE(harness.executeGlobalEvent(544));
    REQUIRE_FALSE(harness.eventRuntimeState().statusMessages.empty());
    CHECK_EQ(harness.eventRuntimeState().statusMessages.back(), "You win!");
}

TEST_CASE("promotion champion event primary knight")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    harness.party().setQuestBit(1541, true);

    REQUIRE(harness.executeGlobalEvent(735));

    const OpenYAMM::Game::Character *pMember0 = harness.party().member(0);
    const OpenYAMM::Game::Character *pMember1 = harness.party().member(1);

    REQUIRE(pMember0 != nullptr);
    REQUIRE(pMember1 != nullptr);
    CHECK_EQ(pMember0->className, "Champion");
    CHECK_EQ(pMember0->maxHealth, 43);
    CHECK_EQ(pMember0->health, pMember0->maxHealth);
    CHECK_EQ(pMember1->className, "Cleric");
    CHECK(harness.party().hasQuestBit(1540));
}

TEST_CASE("promotion champion event multiple member indices")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setMemberClassName(0, "Cleric"));
    REQUIRE(harness.party().setMemberClassName(1, "Knight"));
    REQUIRE(harness.party().setMemberClassName(2, "Knight"));
    harness.party().setQuestBit(1541, true);

    REQUIRE(harness.executeGlobalEvent(735));

    const OpenYAMM::Game::Character *pMember0 = harness.party().member(0);
    const OpenYAMM::Game::Character *pMember1 = harness.party().member(1);
    const OpenYAMM::Game::Character *pMember2 = harness.party().member(2);
    const OpenYAMM::Game::Character *pMember3 = harness.party().member(3);

    REQUIRE(pMember0 != nullptr);
    REQUIRE(pMember1 != nullptr);
    REQUIRE(pMember2 != nullptr);
    REQUIRE(pMember3 != nullptr);
    CHECK_EQ(pMember0->className, "Cleric");
    CHECK_EQ(pMember1->className, "Champion");
    CHECK_EQ(pMember2->className, "Champion");
    CHECK_NE(pMember3->className, "Champion");
    CHECK(harness.party().hasQuestBit(1540));
}

TEST_CASE("promote dragons includes first member and suppresses repeated no-op fx")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setMemberClassName(0, "Dragon"));
    REQUIRE(harness.party().setMemberClassName(1, "Dragon"));
    harness.party().setQuestBit(1544, true);

    REQUIRE(harness.executeGlobalEvent(736));

    const OpenYAMM::Game::Character *pMember0 = harness.party().member(0);
    const OpenYAMM::Game::Character *pMember1 = harness.party().member(1);

    REQUIRE(pMember0 != nullptr);
    REQUIRE(pMember1 != nullptr);
    CHECK_EQ(pMember0->className, "GreatWyrm");
    CHECK_EQ(pMember1->className, "GreatWyrm");
    CHECK(harness.party().hasQuestBit(1543));
    CHECK(portraitFxContainsMember(
        harness.eventRuntimeState(),
        OpenYAMM::Game::PortraitFxEventKind::AwardGain,
        0));

    harness.eventRuntimeState().portraitFxRequests.clear();

    REQUIRE(harness.executeGlobalEvent(736));

    CHECK(harness.eventRuntimeState().portraitFxRequests.empty());
}

TEST_CASE("repeat promotion events include first member")
{
    struct RepeatPromotionCase
    {
        uint16_t eventId = 0;
        const char *baseClassName = nullptr;
        const char *promotedClassName = nullptr;
        uint32_t prerequisiteId = 0;
        bool prerequisiteIsAward = false;
        uint32_t completionQBit = 0;
    };

    const std::vector<RepeatPromotionCase> cases = {
        {733, "DarkElf", "Patriarch", 20, true, 1537},
        {734, "Troll", "WarTroll", 1539, false, 1538},
        {735, "Knight", "Champion", 1541, false, 1540},
        {736, "Dragon", "GreatWyrm", 1544, false, 1543},
        {737, "Cleric", "PriestLight", 31, true, 1546},
        {738, "Necromancer", "Lich", 35, true, 1548},
        {739, "Vampire", "Nosferatu", 33, true, 1547},
        {740, "Minotaur", "MinotaurLord", 29, true, 1545},
    };

    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();

    for (const RepeatPromotionCase &testCase : cases)
    {
        CAPTURE(testCase.eventId);
        OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

        REQUIRE(harness.party().setMemberClassName(0, testCase.baseClassName));

        if (testCase.eventId == 738)
        {
            for (size_t memberIndex = 1; memberIndex < harness.party().members().size(); ++memberIndex)
            {
                REQUIRE(harness.party().setMemberClassName(memberIndex, testCase.baseClassName));
            }
        }

        if (testCase.prerequisiteIsAward)
        {
            harness.party().addAward(0, testCase.prerequisiteId);
        }
        else
        {
            harness.party().setQuestBit(testCase.prerequisiteId, true);
        }

        if (testCase.eventId == 738)
        {
            for (size_t memberIndex = 0; memberIndex < harness.party().members().size(); ++memberIndex)
            {
                REQUIRE(harness.party().grantItemToMember(memberIndex, 628));
            }
        }

        REQUIRE(harness.executeGlobalEvent(testCase.eventId));

        const OpenYAMM::Game::Character *pMember0 = harness.party().member(0);

        REQUIRE(pMember0 != nullptr);
        CHECK_EQ(pMember0->className, testCase.promotedClassName);

        if (testCase.eventId == 738)
        {
            CHECK_EQ(pMember0->characterDataId, 27u);
            CHECK_EQ(pMember0->portraitPictureId, 26u);
            CHECK_EQ(pMember0->portraitTextureName, "pc27-01");
            CHECK_EQ(pMember0->voiceId, 26);

            for (size_t memberIndex = 0; memberIndex < harness.party().members().size(); ++memberIndex)
            {
                const OpenYAMM::Game::Character *pMember = harness.party().member(memberIndex);

                REQUIRE(pMember != nullptr);

                if (pMember->sexId == 1)
                {
                    CHECK_EQ(pMember->characterDataId, 28u);
                    CHECK_EQ(pMember->portraitPictureId, 27u);
                    CHECK_EQ(pMember->portraitTextureName, "pc28-01");
                    CHECK_EQ(pMember->voiceId, 27);
                }
            }
        }

        CHECK(harness.party().hasQuestBit(testCase.completionQBit));
        CHECK(portraitFxContainsMember(
            harness.eventRuntimeState(),
            OpenYAMM::Game::PortraitFxEventKind::AwardGain,
            0));

        harness.eventRuntimeState().portraitFxRequests.clear();

        REQUIRE(harness.executeGlobalEvent(testCase.eventId));

        CHECK(harness.eventRuntimeState().portraitFxRequests.empty());
    }
}

TEST_CASE("mm8 lich promotion only requires jars from necromancers")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setMemberClassName(0, "Knight"));
    REQUIRE(harness.party().setMemberClassName(1, "Necromancer"));
    REQUIRE(harness.party().setMemberClassName(2, "Cleric"));
    REQUIRE(harness.party().grantItemToMember(0, 611));
    REQUIRE(harness.party().grantItemToMember(1, 628));

    REQUIRE(harness.executeGlobalEvent(89));

    const OpenYAMM::Game::Character *pNecromancer = harness.party().member(1);

    REQUIRE(pNecromancer != nullptr);
    CHECK_EQ(pNecromancer->className, "Lich");
    CHECK_EQ(harness.party().inventoryItemCount(611), 0);
    CHECK_EQ(harness.party().inventoryItemCount(628), 0);
    CHECK(harness.party().hasQuestBit(1548));
}

TEST_CASE("deftclaw visible topics do not depend on active member refresh")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    constexpr uint32_t DeftclawNpcId = 17;
    harness.party().setQuestBit(17, true);
    harness.party().setQuestBit(75, true);
    harness.eventRuntimeState().npcTopicOverrides[DeftclawNpcId][1] = 61;
    REQUIRE(harness.party().setActiveMemberIndex(3));

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openNpcDialogue(DeftclawNpcId);
    const std::vector<std::string> labelsBeforeRefresh = collectActionLabels(dialog);

    REQUIRE(harness.party().setActiveMemberIndex(0));
    const OpenYAMM::Game::EventDialogContent &refreshedDialog = harness.refreshCurrentNpcDialog();
    const std::vector<std::string> labelsAfterRefresh = collectActionLabels(refreshedDialog);

    CHECK_EQ(labelsBeforeRefresh, labelsAfterRefresh);
    CHECK(dialogHasActionLabel(refreshedDialog, "Alliance"));
    CHECK_FALSE(dialogHasActionLabel(refreshedDialog, "Dragon Slayers"));
    CHECK(dialogHasActionLabel(refreshedDialog, "Sword of the Slayer"));
}

TEST_CASE("event buoys grant skill points")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness northHarness(gameData);
    OpenYAMM::Game::Character *pNorthMember = northHarness.party().activeMember();

    REQUIRE(pNorthMember != nullptr);

    pNorthMember->luck = 13;
    pNorthMember->skillPoints = 0;

    REQUIRE(northHarness.executeOut01LocalEvent(497));
    CHECK_EQ(pNorthMember->skillPoints, 2);

    OpenYAMM::Tests::HouseDialogueTestHarness southHarness(gameData);
    OpenYAMM::Game::Character *pSouthMember = southHarness.party().activeMember();

    REQUIRE(pSouthMember != nullptr);

    pSouthMember->luck = 20;
    pSouthMember->skillPoints = 0;

    REQUIRE(southHarness.executeOut01LocalEvent(498));
    CHECK_EQ(pSouthMember->skillPoints, 5);
}

TEST_CASE("event palm tree requires perception skill")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness blockedHarness(gameData);
    OpenYAMM::Game::Character *pBlockedMember = blockedHarness.party().activeMember();

    REQUIRE(pBlockedMember != nullptr);
    REQUIRE(setCharacterSkill(
        *pBlockedMember,
        "DisarmTraps",
        2,
        OpenYAMM::Game::SkillMastery::Normal) != nullptr);

    REQUIRE(blockedHarness.executeOut01LocalEvent(494));
    CHECK_FALSE(blockedHarness.party().hasQuestBit(270));

    OpenYAMM::Tests::HouseDialogueTestHarness rewardHarness(gameData);
    OpenYAMM::Game::Character *pRewardMember = rewardHarness.party().activeMember();

    REQUIRE(pRewardMember != nullptr);
    REQUIRE(setCharacterSkill(
        *pRewardMember,
        "DisarmTraps",
        3,
        OpenYAMM::Game::SkillMastery::Normal) != nullptr);

    REQUIRE(rewardHarness.executeOut01LocalEvent(494));
    CHECK(rewardHarness.party().hasQuestBit(270));
}

TEST_CASE("long tail tobersk buy topic remains available after purchase")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    harness.party().addGold(1000);

    OpenYAMM::Game::EventDialogContent dialog = harness.openNpcDialogue(LongTailNpcId);
    CHECK(dialogHasActionLabel(dialog, "Buy Tobersk Fruit for 200 gold"));

    const std::optional<size_t> buyTopicIndex =
        findActionIndexByLabel(dialog, "Buy Tobersk Fruit for 200 gold");

    REQUIRE(buyTopicIndex.has_value());
    harness.executeAndPresent(*buyTopicIndex);

    dialog = harness.openNpcDialogue(LongTailNpcId);
    CHECK(dialogHasActionLabel(dialog, "Buy Tobersk Fruit for 200 gold"));
}

TEST_CASE("event tobersk buy and sell update gold items and weekday price")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    harness.party().addGold(1000);
    const int goldBeforeBuy = harness.party().gold();

    REQUIRE(harness.executeGlobalEvent(250));
    CHECK_EQ(harness.party().gold(), goldBeforeBuy - 200);
    CHECK_EQ(harness.party().inventoryItemCount(643), 1);

    REQUIRE(harness.party().grantItemToMember(2, 645));

    harness.worldRuntime().advanceGameMinutes(-harness.worldRuntime().gameMinutes());
    const int goldBeforeSale = harness.party().gold();

    REQUIRE(harness.executeGlobalEvent(251));
    CHECK_EQ(harness.party().inventoryItemCount(645), 0);
    CHECK_EQ(harness.party().gold(), goldBeforeSale + 557);
}

TEST_CASE("sal sharktooth hat topic uses party inventory and hostile refusal branch")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(0));

    OpenYAMM::Game::EventDialogContent dialog = harness.openNpcDialogue(SalSharktoothNpcId);
    CHECK_FALSE(findActionIndexByLabelPrefix(dialog, "Your hat").has_value());
    CHECK(dialogHasActionLabel(dialog, "Temple"));

    REQUIRE(harness.party().grantItemToMember(2, WealthyHatItemId, 1));

    dialog = harness.openNpcDialogue(SalSharktoothNpcId);
    const std::optional<size_t> hatTopicIndex = findActionIndexByLabelPrefix(dialog, "Your hat");
    REQUIRE(hatTopicIndex.has_value());

    const OpenYAMM::Game::EventDialogContent &offerDialog = harness.executeAndPresent(*hatTopicIndex);
    CHECK(dialogContainsText(offerDialog, "we let you keep your lives"));

    const std::optional<size_t> keepHatIndex = findActionIndexByLabel(offerDialog, "Keep Hat");
    REQUIRE(keepHatIndex.has_value());

    const OpenYAMM::Game::EventDialogContent &refusalDialog = harness.executeAndPresent(*keepHatIndex);
    CHECK(dialogContainsText(refusalDialog, "accepted my offer"));

    const std::unordered_map<uint32_t, uint32_t>::const_iterator groupIt =
        harness.eventRuntimeState().actorGroupSetMasks.find(SalSharktoothGroupId);
    REQUIRE(groupIt != harness.eventRuntimeState().actorGroupSetMasks.end());
    CHECK(
        (groupIt->second & static_cast<uint32_t>(OpenYAMM::Game::EvtActorAttribute::Hostile))
        != 0);
}

TEST_CASE("event teacher hint sets autonote and note fx")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.executeGlobalEvent(430));

    constexpr uint32_t SpearMasterAutoNoteRawId = (102u << 16) | 0x00e1u;
    const auto noteIt = harness.eventRuntimeState().variables.find(SpearMasterAutoNoteRawId);

    REQUIRE(noteIt != harness.eventRuntimeState().variables.end());
    CHECK_NE(noteIt->second, 0);

    bool sawAutoNoteFx = false;

    for (const OpenYAMM::Game::EventRuntimeState::PortraitFxRequest &request :
         harness.eventRuntimeState().portraitFxRequests)
    {
        if (request.kind == OpenYAMM::Game::PortraitFxEventKind::AutoNote
            && std::find(
                   request.memberIndices.begin(),
                   request.memberIndices.end(),
                   harness.party().activeMemberIndex()) != request.memberIndices.end())
        {
            sawAutoNoteFx = true;
            break;
        }
    }

    CHECK(sawAutoNoteFx);
    REQUIRE_FALSE(harness.eventRuntimeState().pendingSounds.empty());
    CHECK_EQ(
        harness.eventRuntimeState().pendingSounds.back().soundId,
        static_cast<uint32_t>(OpenYAMM::Game::SoundId::Quest));
    REQUIRE_FALSE(harness.eventRuntimeState().messages.empty());
    CHECK_NE(
        harness.eventRuntimeState().messages.front().find("Ashandra Withersmythe"),
        std::string::npos);
}

TEST_CASE("npc topic execution prefers global dialogue handler over colliding local map event")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    REQUIRE(gameData.globalEventProgram.has_value());

    const std::optional<OpenYAMM::Game::ScriptedEventProgram> localEventProgram = loadSyntheticMapEventProgram(
        "evt.map[53] = function()\n"
        "    evt.SimpleMessage(\"LOCAL DOOR HANDLER\")\n"
        "end\n",
        "@SyntheticLocalTopicCollision.lua");
    REQUIRE(localEventProgram.has_value());

    OpenYAMM::Game::EventRuntimeState genericState = {};
    OpenYAMM::Game::EventRuntime genericRuntime = {};
    REQUIRE(genericRuntime.executeEventById(
        localEventProgram,
        gameData.globalEventProgram,
        53,
        genericState));
    REQUIRE_FALSE(genericState.messages.empty());
    CHECK_EQ(genericState.messages.back(), "LOCAL DOOR HANDLER");

    OpenYAMM::Game::EventRuntimeState topicState = {};
    OpenYAMM::Game::EventRuntime topicRuntime = {};
    REQUIRE(topicRuntime.executeNpcTopicEventById(
        localEventProgram,
        gameData.globalEventProgram,
        53,
        topicState));
    REQUIRE_FALSE(topicState.messages.empty());
    CHECK_NE(topicState.messages.back().find("I was captured"), std::string::npos);
    CHECK_EQ(topicState.messages.back().find("LOCAL DOOR HANDLER"), std::string::npos);
}
