#pragma once

#include "editor/document/EditorDocument.h"
#include "editor/document/OutdoorGeometryMetadata.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/tables/ChestTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/ObjectTable.h"
#include "game/tables/SpriteTables.h"
#include "tools/legacy_events/EvtProgram.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Editor
{
enum class EditorSelectionKind
{
    None,
    Summary,
    Environment,
    Terrain,
    BModel,
    InteractiveFace,
    Entity,
    Spawn,
    Actor,
    SpriteObject,
    Chest,
    Light,
    Door
};

struct EditorSelection
{
    EditorSelectionKind kind = EditorSelectionKind::None;
    size_t index = 0;
};

struct EditorChestContentRecord
{
    size_t recordIndex = 0;
    int32_t rawItemId = 0;
    std::string summary;
    std::string anchor;
};

struct EditorChestLink
{
    enum class Kind
    {
        Entity,
        Face
    };

    Kind kind = Kind::Entity;
    size_t entityIndex = 0;
    size_t bmodelIndex = 0;
    size_t faceIndex = 0;
    uint16_t eventId = 0;
};

struct EditorEntityBillboardPreview
{
    size_t entityIndex = 0;
    uint16_t spriteId = 0;
    uint16_t flags = 0;
    uint16_t height = 0;
    int16_t radius = 0;
    int x = 0;
    int y = 0;
    int z = 0;
    int facing = 0;
    std::string name;
};

struct EditorActorBillboardPreview
{
    enum class Source
    {
        Actor,
        Spawn
    };

    Source source = Source::Actor;
    size_t sourceIndex = 0;
    uint16_t spriteFrameIndex = 0;
    int x = 0;
    int y = 0;
    int z = 0;
    uint16_t radius = 0;
    uint16_t height = 0;
    float yawRadians = 0.0f;
    std::string name;
};

struct EditorIdLabelOption
{
    uint32_t id = 0;
    std::string label;
};

struct EditorImportedMaterialDiagnostic
{
    std::string sourceMaterialName;
    std::string resolvedTextureName;
    bool hasExplicitRemap = false;
    bool resolvesToKnownBitmap = false;
    bool usesDefaultFallback = false;
};

struct EditorPreviewMechanismState
{
    uint16_t state = 0;
    float timeSinceTriggeredMs = 0.0f;
    float currentDistance = 0.0f;
    bool isMoving = false;
};

enum class EditorTerrainPaintMode
{
    Brush,
    Rectangle,
    Fill
};

enum class EditorTerrainFalloffMode
{
    Flat,
    Linear,
    Smooth
};

enum class EditorTerrainFlattenTargetMode
{
    Sampled,
    Numeric
};

enum class EditorTerrainSculptMode
{
    Raise,
    Lower,
    Flatten,
    Smooth,
    Noise,
    Ramp
};

enum class EditorOutdoorMapTilesetPreset
{
    Grassland,
    Shadowspire,
    IronsandDesert
};

class EditorSession
{
public:
    void initialize(const Engine::AssetFileSystem &assetFileSystem);

    bool openDefaultOutdoorDocument(std::string &errorMessage);
    bool openOutdoorMap(const std::string &mapFileName, std::string &errorMessage);
    bool openIndoorMap(const std::string &mapFileName, std::string &errorMessage);
    bool openMapPhysicalPath(const std::filesystem::path &path, std::string &errorMessage);
    bool switchActiveWorld(const std::string &worldId, std::string &errorMessage);
    bool createNewOutdoorMap(
        const std::string &mapId,
        const std::string &displayName,
        EditorOutdoorMapTilesetPreset tilesetPreset,
        std::string &errorMessage);
    bool saveActiveDocumentAs(
        const std::string &mapId,
        const std::string &displayName,
        std::string &errorMessage);
    bool duplicateActiveDocumentAs(
        const std::string &mapId,
        const std::string &displayName,
        std::string &errorMessage);
    bool deleteActiveDocumentPackage(std::string &errorMessage);
    bool saveActiveDocument(std::string &errorMessage);
    bool buildActiveDocument(std::string &errorMessage);
    void beginFrameEditTracking();
    void captureUndoSnapshot();
    void noteDocumentMutated(const std::string &reason);
    bool canUndo() const;
    bool canRedo() const;
    bool undo(std::string &errorMessage);
    bool redo(std::string &errorMessage);
    bool createOutdoorObject(EditorSelectionKind kind, int x, int y, int z, std::string &errorMessage);
    bool duplicateSelectedObject(std::string &errorMessage);
    bool deleteSelectedObject(std::string &errorMessage);
    bool replaceSelectedBModelFromModel(
        const std::string &sourcePath,
        float importScale,
        const std::string &defaultTextureName,
        const std::string &sourceMeshName,
        bool mergeCoplanarFaces,
        std::string &errorMessage);
    bool importNewBModelFromModel(
        const std::string &sourcePath,
        float importScale,
        const std::string &defaultTextureName,
        const std::string &sourceMeshName,
        bool splitByMesh,
        bool mergeCoplanarFaces,
        std::string &errorMessage);
    bool importIndoorSourceGeometryFromModel(
        const std::string &sourcePath,
        std::string &errorMessage);
    bool reimportSelectedBModel(std::string &errorMessage);
    bool captureSelectedBModelMaterialRemaps(std::string &errorMessage);

    void select(EditorSelectionKind kind, size_t index = 0);
    void replaceInteractiveFaceSelection(size_t flatIndex);
    void addInteractiveFaceSelection(size_t flatIndex);
    void toggleInteractiveFaceSelection(size_t flatIndex);
    void clearInteractiveFaceSelection();
    bool isInteractiveFaceSelected(size_t flatIndex) const;
    const std::vector<size_t> &selectedInteractiveFaceIndices() const;
    const EditorSelection &selection() const;
    const Engine::AssetFileSystem *assetFileSystem() const;

    bool hasDocument() const;
    EditorDocument &document();
    const EditorDocument &document() const;
    const Game::MonsterTable &monsterTable() const;
    const Game::ChestTable &chestTable() const;
    const Game::MapStats &mapStats() const;
    const Game::MapStatsEntry *currentMapStatsEntry() const;
    const Game::ObjectTable &objectTable() const;
    const Game::DecorationTable &decorationTable() const;
    const Game::ItemTable &itemTable() const;
    const std::vector<EditorIdLabelOption> &monsterOptions() const;
    const std::vector<EditorIdLabelOption> &chestOptions() const;
    const std::vector<EditorIdLabelOption> &decorationOptions() const;
    const std::vector<EditorIdLabelOption> &objectOptions() const;
    const std::vector<EditorIdLabelOption> &itemOptions() const;
    const std::vector<std::string> &bitmapTextureNames() const;
    uint16_t pendingEntityDecorationListId() const;
    void setPendingEntityDecorationListId(uint16_t decorationListId);
    const Game::OutdoorSpawn &pendingSpawn() const;
    Game::OutdoorSpawn &mutablePendingSpawn();
    void setPendingSpawn(const Game::OutdoorSpawn &spawn);
    const Game::MapDeltaActor &pendingActor() const;
    Game::MapDeltaActor &mutablePendingActor();
    void setPendingActor(const Game::MapDeltaActor &actor);
    uint32_t pendingSpriteObjectItemId() const;
    void setPendingSpriteObjectItemId(uint32_t itemId);
    uint16_t pendingSpriteObjectDescriptionId() const;
    void setPendingSpriteObjectDescriptionId(uint16_t objectDescriptionId);
    std::optional<uint16_t> objectDescriptionIdForItem(uint32_t itemId) const;
    uint16_t resolvedSpriteObjectObjectDescriptionId(const Game::MapDeltaSpriteObject &spriteObject) const;
    bool isHintOnlyEvent(uint16_t eventId) const;
    std::optional<EditorBModelImportSource> bmodelImportSource(size_t bmodelIndex) const;
    std::vector<std::string> usedBitmapTextureNamesInMap() const;
    std::vector<std::string> usedBitmapTextureNamesForBModel(size_t bmodelIndex) const;
    std::string itemDisplayName(uint32_t itemId) const;
    std::vector<EditorChestContentRecord> decodeChestContents(size_t chestIndex) const;
    const Game::SpriteFrameTable *entityBillboardSpriteFrameTable() const;
    const std::vector<EditorEntityBillboardPreview> &entityBillboardPreviews() const;
    const Game::SpriteFrameTable *actorBillboardSpriteFrameTable() const;
    const std::vector<EditorActorBillboardPreview> &actorBillboardPreviews() const;
    const std::vector<std::vector<uint16_t>> &effectiveOutdoorFaceEvents() const;
    const std::vector<std::optional<uint16_t>> &derivedOutdoorBModelDefaultEvents() const;
    std::optional<std::pair<std::string, int16_t>> previewDecorationTexture(uint16_t decorationListId) const;
    std::optional<std::pair<std::string, int16_t>> previewObjectTexture(uint16_t objectDescriptionId) const;
    std::optional<std::pair<std::string, int16_t>> previewMonsterTexture(int16_t monsterInfoId, int16_t monsterId) const;
    std::optional<std::pair<std::string, int16_t>> previewSpawnMonsterTexture(uint16_t typeId, uint16_t index) const;
    const std::vector<EditorIdLabelOption> &mapEventOptions() const;
    std::optional<std::string> describeMapEvent(uint16_t eventId) const;
    std::optional<std::string> localScriptModulePath() const;
    bool ensurePreviewEventRuntimeState(std::string &errorMessage);
    void syncPreviewMechanismState(uint32_t mechanismId, uint16_t state, float distance, bool isMoving);
    bool simulateMapEvent(uint16_t eventId, std::string &errorMessage);
    void resetPreviewEventRuntimeState();
    std::optional<EditorPreviewMechanismState> previewMechanismState(uint32_t mechanismId) const;
    std::optional<uint16_t> lastPreviewEventId() const;
    const std::vector<std::string> &lastPreviewEventMessages() const;
    const std::vector<std::string> &lastPreviewEventStatusMessages() const;
    uint16_t effectiveOutdoorFaceEventId(size_t bmodelIndex, size_t faceIndex) const;
    std::optional<uint16_t> derivedBModelDefaultEventId(size_t bmodelIndex) const;
    std::vector<EditorChestLink> findChestLinks(size_t chestIndex) const;
    const std::vector<EditorImportedMaterialDiagnostic> &importedMaterialDiagnostics(size_t bmodelIndex) const;
    uint8_t terrainPaintTileId() const;
    void setTerrainPaintTileId(uint8_t tileId);
    EditorTerrainPaintMode terrainPaintMode() const;
    void setTerrainPaintMode(EditorTerrainPaintMode mode);
    int terrainPaintRadius() const;
    void setTerrainPaintRadius(int radius);
    int terrainPaintEdgeNoise() const;
    void setTerrainPaintEdgeNoise(int edgeNoise);
    bool terrainPaintEnabled() const;
    void setTerrainPaintEnabled(bool enabled);
    bool terrainSculptEnabled() const;
    void setTerrainSculptEnabled(bool enabled);
    EditorTerrainSculptMode terrainSculptMode() const;
    void setTerrainSculptMode(EditorTerrainSculptMode mode);
    int terrainSculptRadius() const;
    void setTerrainSculptRadius(int radius);
    int terrainSculptStrength() const;
    void setTerrainSculptStrength(int strength);
    EditorTerrainFalloffMode terrainSculptFalloffMode() const;
    void setTerrainSculptFalloffMode(EditorTerrainFalloffMode mode);
    EditorTerrainFlattenTargetMode terrainFlattenTargetMode() const;
    void setTerrainFlattenTargetMode(EditorTerrainFlattenTargetMode mode);
    int terrainFlattenTargetHeight() const;
    void setTerrainFlattenTargetHeight(int height);
    bool hasTerrainFlattenSampledTarget() const;
    void setTerrainFlattenSampledTargetHeight(int height);

    void logInfo(const std::string &message);
    void logError(const std::string &message);
    const std::vector<std::string> &logMessages() const;
    const std::vector<std::string> &validationMessages() const;

private:
    void appendLog(const std::string &prefix, const std::string &message);
    void refreshValidation();
    void refreshDirtyState();
    void resetHistory();
    void ensureOutdoorDerivedCaches() const;
    void normalizeOutdoorSceneCollections();
    void loadOutdoorEditorSupportData(const std::string &mapFileName);
    void pruneBModelImportSources();
    std::string previewEventRuntimeKey() const;

    Engine::AssetFileSystem *m_pAssetFileSystem = nullptr;
    Game::MonsterTable m_monsterTable;
    Game::ChestTable m_chestTable;
    Game::MapStats m_mapStats;
    Game::ObjectTable m_objectTable;
    Game::DecorationTable m_decorationTable;
    Game::ItemTable m_itemTable;
    Game::SpriteFrameTable m_entityBillboardSpriteFrameTable;
    std::unordered_map<uint32_t, std::string> m_itemNames;
    std::vector<EditorIdLabelOption> m_monsterOptions;
    std::vector<EditorIdLabelOption> m_chestOptions;
    std::vector<EditorIdLabelOption> m_decorationOptions;
    std::vector<EditorIdLabelOption> m_objectOptions;
    std::vector<EditorIdLabelOption> m_itemOptions;
    std::vector<std::string> m_bitmapTextureNames;
    std::optional<Game::EvtProgram> m_localEvtProgram;
    std::optional<Game::EvtProgram> m_globalEvtProgram;
    std::optional<Game::ScriptedEventProgram> m_localScriptedEventProgram;
    std::optional<Game::ScriptedEventProgram> m_globalScriptedEventProgram;
    bool m_hasPreviewEventRuntimeState = false;
    std::array<uint8_t, 75> m_previewEventMapVars = {};
    std::array<uint8_t, 125> m_previewEventDecorVars = {};
    std::unordered_map<uint32_t, int32_t> m_previewEventVariables;
    std::unordered_map<uint32_t, EditorPreviewMechanismState> m_previewEventMechanisms;
    std::optional<uint16_t> m_lastPreviewEventId;
    std::vector<std::string> m_lastPreviewEventMessages;
    std::vector<std::string> m_lastPreviewEventStatusMessages;
    std::string m_previewEventRuntimeKey;
    std::vector<EditorIdLabelOption> m_mapEventOptions;
    std::optional<std::string> m_localScriptModulePath;
    EditorDocument m_document;
    EditorSelection m_selection = {};
    std::vector<size_t> m_selectedInteractiveFaceIndices;
    std::vector<std::string> m_logMessages;
    std::vector<std::string> m_validationMessages;
    std::vector<std::string> m_undoSnapshots;
    std::vector<std::string> m_redoSnapshots;
    mutable bool m_hasCachedOutdoorDerivedState = false;
    mutable EditorDocument::Kind m_cachedOutdoorDerivedKind = EditorDocument::Kind::None;
    mutable uint64_t m_cachedOutdoorDerivedSceneRevision = 0;
    mutable uint16_t m_cachedOutdoorDerivedPendingActorMonsterInfoId = 0;
    mutable uint16_t m_cachedOutdoorDerivedPendingActorMonsterId = 0;
    mutable uint16_t m_cachedOutdoorDerivedPendingSpawnTypeId = 0;
    mutable uint16_t m_cachedOutdoorDerivedPendingSpawnIndex = 0;
    mutable std::vector<EditorEntityBillboardPreview> m_cachedEntityBillboardPreviews;
    mutable std::vector<EditorActorBillboardPreview> m_cachedActorBillboardPreviews;
    mutable Game::SpriteFrameTable m_cachedActorBillboardSpriteFrameTable;
    mutable std::vector<std::vector<uint16_t>> m_cachedEffectiveFaceEvents;
    mutable std::vector<std::optional<uint16_t>> m_cachedDefaultBModelEvents;
    mutable std::vector<std::vector<EditorChestLink>> m_cachedChestLinks;
    mutable std::vector<std::vector<EditorImportedMaterialDiagnostic>> m_cachedImportedMaterialDiagnostics;
    mutable std::vector<bool> m_cachedImportedMaterialDiagnosticsValid;
    std::string m_savedSnapshot;
    bool m_frameMutationCaptured = false;
    uint8_t m_terrainPaintTileId = 0;
    EditorTerrainPaintMode m_terrainPaintMode = EditorTerrainPaintMode::Brush;
    int m_terrainPaintRadius = 0;
    int m_terrainPaintEdgeNoise = 35;
    bool m_terrainPaintEnabled = false;
    bool m_terrainSculptEnabled = false;
    EditorTerrainSculptMode m_terrainSculptMode = EditorTerrainSculptMode::Raise;
    int m_terrainSculptRadius = 1;
    int m_terrainSculptStrength = 1;
    EditorTerrainFalloffMode m_terrainSculptFalloffMode = EditorTerrainFalloffMode::Linear;
    EditorTerrainFlattenTargetMode m_terrainFlattenTargetMode = EditorTerrainFlattenTargetMode::Sampled;
    int m_terrainFlattenTargetHeight = 0;
    bool m_hasTerrainFlattenSampledTarget = false;
    uint16_t m_pendingEntityDecorationListId = 0;
    Game::OutdoorSpawn m_pendingSpawn = {};
    Game::MapDeltaActor m_pendingActor = {};
    uint32_t m_pendingSpriteObjectItemId = 0;
    uint16_t m_pendingSpriteObjectDescriptionId = 0;
    bool m_hasEntityBillboardSpriteFrameTable = false;
    bool m_hasDecorationTable = false;
    mutable bool m_hasCachedActorBillboardSpriteFrameTable = false;
};
}
