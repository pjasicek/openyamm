#pragma once

#include "game/tables/SpriteTables.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct IndoorEntity;
struct IndoorMapData;
struct OutdoorEntity;
struct EventRuntimeState;
class Party;

const DecorationEntry *toggleableDecorationCounterpart(
    const DecorationTable &table, const DecorationEntry &decoration);
const DecorationEntry *runtimeDecorationEntry(
    const DecorationTable &table, const DecorationEntry &decoration,
    uint32_t spriteOverrideKey, const EventRuntimeState *pState);
const DecorationEntry *indoorDecorationLightToggleTarget(
    const IndoorMapData &map, const DecorationTable &table, size_t entityIndex,
    const EventRuntimeState *pState);
bool toggleIndoorDecorationLight(
    const IndoorMapData &map, const DecorationTable &table, size_t entityIndex,
    EventRuntimeState &state);

enum class InteractiveDecorationFamily : uint8_t
{
    None = 0,
    Barrel,
    Cauldron,
    TrashHeap,
    CampFire,
    Cask,
    FlourSack,
    LargeBag,
    Bucket,
    MightAndMagicSixTrashHeap,
    Crystal,
    GoldBag,
};

struct InteractiveDecorationBindingSpec
{
    uint16_t baseEventId = 0;
    uint8_t eventCount = 0;
    uint8_t initialState = 0;
    bool useSeededInitialState = false;
    bool hideWhenCleared = false;
    bool fixedEvent = false;
    InteractiveDecorationFamily family = InteractiveDecorationFamily::None;
};

std::optional<InteractiveDecorationFamily> classifyInteractiveDecorationFamily(
    const DecorationEntry &decoration,
    const std::string &instanceName);

std::optional<InteractiveDecorationBindingSpec> resolveInteractiveDecorationBindingSpec(
    const DecorationEntry &decoration,
    const std::string &instanceName);

uint32_t makeInteractiveDecorationSeed(
    size_t entityIndex,
    uint16_t decorationListId,
    int x,
    int y,
    int z);

uint8_t initialInteractiveDecorationState(InteractiveDecorationFamily family, uint32_t seed);

// Initialize fresh map assets only; saved map state must be restored afterwards.
void initializeMapInteractiveDecorations(
    std::span<const IndoorEntity> entities,
    const DecorationTable &decorationTable,
    std::array<uint8_t, 125> &decorVars,
    uint32_t randomSeed);

void initializeMapInteractiveDecorations(
    std::span<const OutdoorEntity> entities,
    const DecorationTable &decorationTable,
    std::array<uint8_t, 125> &decorVars,
    uint32_t randomSeed);

bool interactiveDecorationIsCleared(uint8_t state, uint8_t eventCount, bool hideWhenCleared);

std::optional<uint16_t> interactiveDecorationEventId(
    uint8_t state, uint16_t baseEventId, uint8_t eventCount, bool hideWhenCleared, bool fixedEvent);

// The map file's (and saved map state's) per-decoration flag that hides a decoration (MM LEVEL_DECORATION_INVISIBLE).
constexpr uint16_t LevelDecorationInvisible = 0x0020;

// How each entity's decor var can hide it; it depends only on the map and decoration table, so a world resolves it
// once per map and applies it to the current event state.
struct DecorationClearRule
{
    int16_t decorVarIndex = -1;
    uint8_t eventCount = 0;
    bool hideWhenCleared = false;
};

std::vector<DecorationClearRule> decorationClearRules(
    std::span<const IndoorEntity> entities, const DecorationTable &table);
std::vector<DecorationClearRule> decorationClearRules(
    std::span<const OutdoorEntity> entities, const DecorationTable &table);

// Whether one decoration is hidden: an event override (evt.SetSprite) decides when present, otherwise the map's
// invisible flag (mapFlags); a cleared interactive decoration (an eaten campfire) is hidden either way. pRule may be
// null for an entity without a decor var.
bool isDecorationHidden(
    uint32_t spriteOverrideKey, uint16_t mapFlags, const DecorationClearRule *pRule, const EventRuntimeState &state);

// isDecorationHidden for every entity. The map flags come from pDecorationFlags (the map state's decorationFlags)
// where it covers the entity, else from the entity's own flags.
std::vector<bool> hiddenDecorationEntities(
    std::span<const IndoorEntity> entities, std::span<const DecorationClearRule> rules,
    const std::vector<uint16_t> *pDecorationFlags, const EventRuntimeState &state);
std::vector<bool> hiddenDecorationEntities(
    std::span<const OutdoorEntity> entities, std::span<const DecorationClearRule> rules,
    const std::vector<uint16_t> *pDecorationFlags, const EventRuntimeState &state);

// Saves before SaveVersionMMergeCampfireDecorVars numbered a map's decoration states (decorVars) with the legacy
// campfire keys (hints "campfire" and "camp fire"), before MMerge's name list added the MM6 fires and dropped MM8's
// dec04. For each legacy index, the index the same decoration has now, or -1 when it is no longer interactive; empty
// when the map's numbering did not change.
std::vector<int16_t> legacyCampFireDecorVarRemap(
    std::span<const IndoorEntity> entities, const DecorationTable &table);
std::vector<int16_t> legacyCampFireDecorVarRemap(
    std::span<const OutdoorEntity> entities, const DecorationTable &table);

// Moves each decoration state to its new index (legacyCampFireDecorVarRemap); a decoration that is new in the
// numbering starts fresh at 0.
void remapDecorVars(std::array<uint8_t, 125> &decorVars, std::span<const int16_t> remap);

// A saved state of the map still marked legacyCampFireDecorVars: renumbers its decoration states, and those the party's
// rules remember for the map (MonsterRules::decorationsRenumbered), then clears the mark. Does nothing to other states.
void renumberLegacyCampFireDecorVars(
    EventRuntimeState &state, const std::string &mapFileName, std::span<const IndoorEntity> entities,
    const DecorationTable &table, const Party &party);
void renumberLegacyCampFireDecorVars(
    EventRuntimeState &state, const std::string &mapFileName, std::span<const OutdoorEntity> entities,
    const DecorationTable &table, const Party &party);

// A saved state of the map still marked legacySmallBarrelDecorVars (MM6's small barrels were casks): gives each
// unopened small barrel a stat barrel's colour, leaves the opened ones empty, then clears the mark.
void refillLegacySmallBarrels(
    EventRuntimeState &state, std::span<const IndoorEntity> entities, const DecorationTable &table);
void refillLegacySmallBarrels(
    EventRuntimeState &state, std::span<const OutdoorEntity> entities, const DecorationTable &table);

// Every member's base stats and base resistances, to tell whether a decoration's event (a barrel, a cauldron) raised
// one: compare a snapshot before the event with one after.
std::vector<int64_t> partyBaseStatSnapshot(const Party &party);

// After a decoration's event ran: if it raised a base stat, tells the party's rules which decoration it was and the
// state the event left it in.
void reportDecorationStatGain(const Party &party, const EventRuntimeState &state, uint8_t decorVarIndex,
    const std::vector<int64_t> &statsBefore);
}
