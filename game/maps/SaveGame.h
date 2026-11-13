#pragma once

#include "game/content/RulesetOptions.h"
#include "game/scene/IndoorSceneRuntime.h"
#include "game/scene/SceneKind.h"
#include "game/outdoor/OutdoorPartyRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/party/Party.h"
#include "game/rules/maw/MawGameState.h"

#include <cstdint>
#include <filesystem>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;
class HouseTable;

struct GameSaveData
{
    SceneKind currentSceneKind = SceneKind::Outdoor;
    std::string mapFileName;
    Party::Snapshot party;
    std::unordered_map<std::string, int32_t> namedGlobalVars;
    bool hasOutdoorRuntimeState = false;
    OutdoorPartyRuntime::Snapshot outdoorParty;
    OutdoorWorldRuntime::Snapshot outdoorWorld;
    std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> outdoorWorldStates;
    bool hasIndoorSceneState = false;
    IndoorSceneRuntime::Snapshot indoorScene;
    std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> indoorSceneStates;
    float savedGameMinutes = 0.0f;
    // Camera angles of the current scene (outdoor or indoor). Saves older than SaveVersionIndoorCamera stored only the
    // outdoor camera, so for them the angles are valid only when the save was made outdoors.
    float cameraYawRadians = 0.0f;
    float cameraPitchRadians = 0.0f;
    bool cameraAnglesValid = false;
    bool heldInventoryItemActive = false;
    InventoryItem heldInventoryItem = {};
    uint8_t heldInventoryItemGrabCellOffsetX = 0;
    uint8_t heldInventoryItemGrabCellOffsetY = 0;
    float heldInventoryItemGrabOffsetX = 0.0f;
    float heldInventoryItemGrabOffsetY = 0.0f;
    std::unordered_map<std::string, uint32_t> requiredContentPackages;
    RulesetSelection ruleset;
    // Root of the game's random streams (game/rules/RandomStreams.h); 0 in saves older than the streams.
    uint64_t randomRootSeed = 0;
    // MAW games only.
    std::optional<MawGameState> mawState;
    // The playthrough this save belongs to and its statistics timeline as YAML (game/party/PlaythroughStatistics.h);
    // both empty in saves older than the statistics.
    std::string playthroughId;
    std::string playthroughTimeline;
    // The real time played up to the save (the timeline's), for the save lists.
    double playthroughPlayedSeconds = 0.0;
    std::string saveName;
    std::vector<uint8_t> previewBmp;
    // The version the save was written with (set when loading, not saved), for migrations that need the game tables.
    uint32_t sourceSaveVersion = 0;
};

// The playthrough a save belongs to (empty: a save from before playthroughs with no random seed to name one by) and
// the real time played up to it.
struct SavePlaythroughInfo
{
    std::string id;
    double playedSeconds = 0.0;
};

// What the Load and Save screens list about a save: the same fields of its GameSaveData.
struct GameSaveSummary
{
    std::string mapFileName;
    float savedGameMinutes = 0.0f;
    RulesetSelection ruleset;
    std::string saveName;
    std::vector<uint8_t> previewBmp;
    // Nothing in saves before version 175, which keep it behind the game state (loadSavePlaythroughInfoFromPath).
    std::optional<SavePlaythroughInfo> playthrough;
};

// MAW games carry four bags a member from this version on; older saves fit theirs into four when loaded
// (InventoryBags::fitIntoBagCount).
constexpr uint32_t SaveVersionFourMawBags = 121;
// A promotion grants MAW's ladder masteries (Cover, Mana Shield, Enlightenment, Retaliation) that the new class's limits
// allow; members promoted in older saves get them when loaded (Party::grantClassChangeMasteries).
constexpr uint32_t SaveVersionClassChangeMasteries = 174;
// Special items (Noblebone Bow, Moon Cloak) carry the enchantment their item row names from this version on; older
// saves give the party's ones theirs when loaded (Party::assignSpecialItemEnchants, OY-553).
constexpr uint32_t SaveVersionSpecialItemEnchants = 177;
// Formations are on in every world from this version on; an older save's party still in the default formation stands
// by health when loaded (Party::arrangeDefaultFormationByHealth).
constexpr uint32_t SaveVersionFormationsEverywhere = 179;

void migrateLegacyConsumedCorpseMarkers(GameSaveData &data, uint32_t sourceSaveVersion);
void migrateLegacyNpcRosters(GameSaveData &data);
void migrateLegacyMapAutonotes(GameSaveData &data, uint32_t sourceSaveVersion);
void migrateLegacyMapHistory(GameSaveData &data, uint32_t sourceSaveVersion);
// Saves before version 141 recorded MMerge history pages two pages late: moves pages from 3 down by two.
void migrateLegacyHistoryNumbering(GameSaveData &data, uint32_t sourceSaveVersion);
void migrateLegacyMapJournalNotes(GameSaveData &data, uint32_t sourceSaveVersion);
// Saves before version 129 numbered the decoration states with the legacy campfire keys: marks every saved map state
// (EventRuntimeState::legacyCampFireDecorVars) for the map to renumber when it is next entered.
void markLegacyCampFireDecorVars(GameSaveData &data, uint32_t sourceSaveVersion);
// Saves before version 144 held MM6's small barrels as casks: marks every saved map state
// (EventRuntimeState::legacySmallBarrelDecorVars) for the map to refill them when it is next entered.
void markLegacySmallBarrelDecorVars(GameSaveData &data, uint32_t sourceSaveVersion);
// Saves before version 144 gave Liches (and Lich or vampire mercenaries) Light and Dark immunity in place of the Mind
// and Body ones the rules now derive: clears it from every member, Adventurer's Inn character and offered recruit.
void migrateLegacyLichImmunities(GameSaveData &data, uint32_t sourceSaveVersion);
bool saveGameDataToPath(const std::filesystem::path &path, const GameSaveData &data, std::string &error);

// The load error for a save written by a newer build; the Load screen counts such saves instead of listing them.
inline constexpr const char *SaveFromNewerVersionError = "written by a newer version of OpenYAMM";

std::optional<GameSaveData> loadGameDataFromPath(const std::filesystem::path &path, std::string &error);
// Reads only the summary of current saves; older ones keep it behind the game state and are read whole.
std::optional<GameSaveSummary> loadGameSaveSummaryFromPath(const std::filesystem::path &path, std::string &error);
// Reads the whole save for its playthrough: for saves whose summary has none.
std::optional<SavePlaythroughInfo> loadSavePlaythroughInfoFromPath(
    const std::filesystem::path &path,
    std::string &error);

// A playthrough's own Quicksave and Autosave, saves/quicksave_<id>.oysav and saves/autosave_<id>.oysav. Without an id
// they are saves/quicksave.oysav and saves/autosave.oysav, which every playthrough shared in earlier builds.
// A playthrough keeps its last quicksaves, as many as the Quicksaves kept setting says: slot 1 is the newest, the
// older ones are saves/quicksave2_<id>.oysav, saves/quicksave3_<id>.oysav and so on.
constexpr int DefaultQuickSaveSlotCount = 3;
constexpr int MaxQuickSaveSlotCount = 20;
std::filesystem::path quickSavePath(const std::string &playthroughId, int slot = 1);
std::filesystem::path autosavePath(const std::string &playthroughId);
bool isQuickSavePath(const std::filesystem::path &path);
bool isAutosavePath(const std::filesystem::path &path);
// 1 to MaxQuickSaveSlotCount for a quicksave file, 0 for any other.
int quickSaveSlot(const std::filesystem::path &path);
// Writes a playthrough's newest quicksave, `path` of slot 1, keeping `slotCount` of them. The quicksaves it has move
// one slot down into the first free slot, or over the oldest when all are taken; those in slots past `slotCount` (the
// setting was lowered) are removed. A failed write leaves them as they were.
bool saveQuickSaveToPath(
    const std::filesystem::path &path,
    const GameSaveData &data,
    int slotCount,
    std::string &error);
// Renames the folder's shared quicksave.oysav and autosave.oysav of earlier builds to the names of the playthroughs
// that wrote them. One that names no playthrough, or whose playthrough has its own already, stays.
void migrateSharedSaveSlots(const std::filesystem::path &savesDirectory);
std::unordered_map<std::string, uint32_t> collectRequiredContentPackages(
    const GameSaveData &data,
    const ItemTable &itemTable,
    const HouseTable &houseTable,
    const std::unordered_map<std::string, uint32_t> &loadedPackageSchemas);
// Saves before version 115 keep the MM6 maps' SetTexture swaps under the face number; MMerge's MM6 scripts now name
// faces with a negative reference, stored under EventRuntime::indoorFaceReferenceKey (audit STD3-6, plan D10).
// `isMm6IndoorMap` tells which saved maps are MM6's.
void migrateLegacyMm6FaceTextureKeys(
    GameSaveData &data,
    const std::function<bool(const std::string &mapFileName)> &isMm6IndoorMap);
// Whether every content package the save needs is loaded at the schema it was written with; the item and house checks
// of validateRequiredContentPackages need the tables, this one does not.
bool validateRequiredContentPackageSchemas(
    const GameSaveData &data,
    const std::unordered_map<std::string, uint32_t> &loadedPackageSchemas,
    std::string &error);
bool validateRequiredContentPackages(
    const GameSaveData &data,
    const ItemTable &itemTable,
    const HouseTable &houseTable,
    const std::unordered_map<std::string, uint32_t> &loadedPackageSchemas,
    std::string &error);
// Quicksave, Autosave, then the rest by shown save name, case-insensitive with digit runs compared as numbers.
int compareSaveNamesNaturally(const std::string &left, const std::string &right);
bool compareSavesForDisplay(
    const std::filesystem::path &leftPath,
    const std::string &leftName,
    const std::filesystem::path &rightPath,
    const std::string &rightName);
}
