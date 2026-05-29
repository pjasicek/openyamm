#pragma once

#include "game/mm9/Mm9DatCollisionWorld.h"
#include "game/mm9/Mm9LightLayer.h"
#include "game/mm9/Mm9ScriptedObjectRuntime.h"
#include "game/mm9/Mm9SkyLayer.h"
#include "game/render/lighting/RenderLight.h"

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
enum class Mm9DatRenderPartitionBlendMode
{
    Opaque,
    Translucent,
};

static constexpr size_t Mm9DatInvalidRuntimeMaterialIndex = static_cast<size_t>(-1);

struct Mm9DatRenderPartition
{
    size_t partitionIndex = 0;
    size_t sourceModelIndex = 0;
    std::string materialKey;
    uint32_t filterFlags = 0;
    Mm9DatRenderPartitionBlendMode blendMode = Mm9DatRenderPartitionBlendMode::Opaque;
    std::vector<size_t> triangleIndices;
    Mm9DatRenderBounds bounds;
};

struct Mm9DatRenderWorldStats
{
    size_t sourceTriangleCount = 0;
    size_t normalVisualTriangleCount = 0;
    size_t visibleWaterTriangleCount = 0;
    size_t waterVolumeSkippedTriangleCount = 0;
    size_t helperSkippedTriangleCount = 0;
    size_t dynamicMechanismSkippedTriangleCount = 0;
    size_t partitionCount = 0;
    size_t opaquePartitionCount = 0;
    size_t translucentPartitionCount = 0;
    size_t missingMaterialTriangleCount = 0;
};

struct Mm9DatRenderWorld
{
    std::vector<Mm9DatRenderPartition> partitions;
    Mm9DatRenderWorldStats stats;
};

struct Mm9DatMechanismRenderBatch
{
    uint32_t mechanismHandle = 0;
    std::string mechanismId;
    std::string objectId;
    size_t sourceModelIndex = 0;
    std::string sourceModelName;
    Mm9DatMechanismPreviewMotion motion;
    Mm9DatRenderBounds currentBounds;
    std::vector<size_t> triangleIndices;
};

struct Mm9DatMechanismRenderWorldStats
{
    size_t batchCount = 0;
    size_t sourceTriangleCount = 0;
    size_t transformedTriangleCount = 0;
    size_t activeMechanismCount = 0;
};

struct Mm9DatMechanismRenderWorld
{
    std::vector<Mm9DatMechanismRenderBatch> batches;
    Mm9DatMechanismRenderWorldStats stats;
};

struct Mm9DatPreparedRenderVertex
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float uPixels = 0.0f;
    float vPixels = 0.0f;
};

struct Mm9DatPreparedRenderSection
{
    size_t sectionIndex = 0;
    bool dynamic = false;
    uint32_t mechanismHandle = 0;
    std::string mechanismId;
    std::string objectId;
    size_t sourceModelIndex = 0;
    std::string sourceModelName;
    std::string materialKey;
    size_t materialIndex = Mm9DatInvalidRuntimeMaterialIndex;
    uint32_t filterFlags = 0;
    Mm9DatRenderPartitionBlendMode blendMode = Mm9DatRenderPartitionBlendMode::Opaque;
    size_t vertexStart = 0;
    size_t vertexCount = 0;
    size_t indexStart = 0;
    size_t indexCount = 0;
    std::vector<size_t> sourceTriangleIndices;
    Mm9DatRenderBounds bounds;
};

struct Mm9DatPreparedRenderWorldStats
{
    size_t sectionCount = 0;
    size_t staticSectionCount = 0;
    size_t dynamicSectionCount = 0;
    size_t opaqueSectionCount = 0;
    size_t translucentSectionCount = 0;
    size_t vertexCount = 0;
    size_t indexCount = 0;
    size_t triangleCount = 0;
    size_t staticTriangleCount = 0;
    size_t dynamicTriangleCount = 0;
};

struct Mm9DatPreparedRenderWorld
{
    std::vector<Mm9DatPreparedRenderVertex> vertices;
    std::vector<uint32_t> indices;
    std::vector<Mm9DatPreparedRenderSection> sections;
    Mm9DatPreparedRenderWorldStats stats;
};

struct Mm9DatRuntimeMaterial
{
    size_t materialIndex = 0;
    std::string materialKey;
    std::string sourceTexture;
    std::string resolvedSourcePath;
    bool missing = false;
    bool sourceTextureMaterial = false;
    bool resolvedMaterial = false;
    bool textureCacheEligible = false;
};

struct Mm9DatRuntimeMaterialTableStats
{
    size_t materialCount = 0;
    size_t sourceTextureMaterialCount = 0;
    size_t resolvedMaterialCount = 0;
    size_t missingMaterialCount = 0;
    size_t textureCacheEligibleCount = 0;
};

struct Mm9DatRuntimeMaterialTable
{
    std::vector<Mm9DatRuntimeMaterial> materials;
    Mm9DatRuntimeMaterialTableStats stats;
};

struct Mm9DatRuntimeTextureCatalogEntry
{
    size_t catalogEntryIndex = 0;
    std::filesystem::path physicalPath;
    std::string relativePathKey;
    std::string fileNameKey;
    std::string stemKey;
};

struct Mm9DatRuntimeTextureCatalogStats
{
    size_t sourceRootCount = 0;
    size_t scannedFileCount = 0;
    size_t dtxFileCount = 0;
    size_t catalogEntryCount = 0;
    size_t catalogKeyCount = 0;
    size_t duplicateCatalogKeyCount = 0;
};

struct Mm9DatRuntimeTextureCatalog
{
    std::vector<std::filesystem::path> sourceRoots;
    std::vector<Mm9DatRuntimeTextureCatalogEntry> entries;
    std::unordered_map<std::string, size_t> entryIndexByKey;
    Mm9DatRuntimeTextureCatalogStats stats;
};

struct Mm9DatRuntimeTextureBinding
{
    size_t materialIndex = Mm9DatInvalidRuntimeMaterialIndex;
    size_t catalogEntryIndex = static_cast<size_t>(-1);
    std::string materialKey;
    std::string sourceTexture;
    std::filesystem::path physicalPath;
    bool resolved = false;
    bool missing = false;
};

struct Mm9DatRuntimeTextureBindingStats
{
    size_t materialLookupCount = 0;
    size_t resolvedMaterialCount = 0;
    size_t missingMaterialCount = 0;
};

struct Mm9DatRuntimeTextureBindings
{
    std::vector<Mm9DatRuntimeTextureBinding> bindings;
    Mm9DatRuntimeTextureBindingStats stats;
};

struct Mm9DatRenderSubmissionOptions
{
    bool includeStatic = true;
    bool includeDynamic = true;
    bool includeOpaque = true;
    bool includeTranslucent = true;
    bool cullByDistance = false;
    Mm9DatVec3 viewPosition;
    float maxVisibleDistance = 0.0f;
};

struct Mm9DatRenderDrawCommand
{
    size_t commandIndex = 0;
    size_t sectionIndex = 0;
    bool dynamic = false;
    uint32_t mechanismHandle = 0;
    size_t sourceModelIndex = 0;
    std::string materialKey;
    size_t materialIndex = Mm9DatInvalidRuntimeMaterialIndex;
    Mm9DatRenderPartitionBlendMode blendMode = Mm9DatRenderPartitionBlendMode::Opaque;
    size_t vertexStart = 0;
    size_t vertexCount = 0;
    size_t indexStart = 0;
    size_t indexCount = 0;
    size_t triangleCount = 0;
    Mm9DatRenderBounds bounds;
};

struct Mm9DatRenderSubmissionStats
{
    size_t sourceSectionCount = 0;
    size_t visibleSectionCount = 0;
    size_t culledSectionCount = 0;
    size_t drawCallCount = 0;
    size_t opaqueDrawCallCount = 0;
    size_t translucentDrawCallCount = 0;
    size_t staticDrawCallCount = 0;
    size_t dynamicDrawCallCount = 0;
    size_t submittedTriangleCount = 0;
    size_t submittedIndexCount = 0;
    size_t textureMissDrawCallCount = 0;
};

struct Mm9DatRenderSubmissionPlan
{
    std::vector<Mm9DatRenderDrawCommand> commands;
    Mm9DatRenderSubmissionStats stats;
};

enum class Mm9DatObjectPlacementStatus
{
    Authored,
    SnappedToFloor,
    UnsupportedMoveToFloor,
    PolicySkipped,
};

struct Mm9DatRuntimeObject
{
    uint32_t handle = 0;
    size_t sourceObjectIndex = 0;
    std::string objectId;
    std::string sourceClass;
    std::string sourceName;
    std::string sourceModel;
    std::string modelAsset;
    std::string visualId;
    std::string scriptName;
    std::string scriptParams;
    Mm9DatVec3 originalPosition;
    Mm9DatVec3 position;
    float radius = 0.0f;
    float height = 0.0f;
    bool visible = true;
    bool solid = true;
    bool rayHit = true;
    bool pickable = true;
    bool moveToFloor = false;
    bool flying = false;
    bool needsTick = false;
    Mm9DatObjectPlacementStatus placementStatus = Mm9DatObjectPlacementStatus::Authored;
    size_t floorCandidateTriangleCount = 0;
    size_t floorTestedTriangleCount = 0;
    std::string placementDiagnostic;
};

struct Mm9DatObjectRegistryStats
{
    size_t objectCount = 0;
    size_t visibleObjectCount = 0;
    size_t solidObjectCount = 0;
    size_t rayHitObjectCount = 0;
    size_t moveToFloorObjectCount = 0;
    size_t renderableObjectCount = 0;
    size_t collidableObjectCount = 0;
    size_t triggerObjectCount = 0;
    size_t interactableObjectCount = 0;
    size_t actorObjectCount = 0;
    size_t propObjectCount = 0;
    size_t pickupObjectCount = 0;
    size_t lightObjectCount = 0;
    size_t mechanismObjectCount = 0;
    size_t tickingObjectCount = 0;
    size_t snappedToFloorCount = 0;
    size_t unsupportedMoveToFloorCount = 0;
    size_t policySkippedMoveToFloorCount = 0;
    size_t pickableCellCount = 0;
    size_t pickableCellObjectRefs = 0;
    size_t maxPickableCellObjectRefs = 0;
    size_t collidableCellCount = 0;
    size_t collidableCellObjectRefs = 0;
    size_t maxCollidableCellObjectRefs = 0;
    size_t actorCellCount = 0;
    size_t actorCellObjectRefs = 0;
    size_t maxActorCellObjectRefs = 0;
};

struct Mm9DatObjectRegistry
{
    std::vector<Mm9DatRuntimeObject> objects;
    std::vector<size_t> renderableObjectIndices;
    std::vector<size_t> collidableObjectIndices;
    std::vector<size_t> rayHitObjectIndices;
    std::vector<size_t> triggerObjectIndices;
    std::vector<size_t> interactableObjectIndices;
    std::vector<size_t> actorObjectIndices;
    std::vector<size_t> propObjectIndices;
    std::vector<size_t> pickupObjectIndices;
    std::vector<size_t> lightObjectIndices;
    std::vector<size_t> mechanismObjectIndices;
    std::vector<size_t> tickingObjectIndices;
    std::vector<size_t> actorIndexByObjectIndex;
    std::unordered_map<std::string, size_t> objectIndexByObjectId;
    std::unordered_map<uint32_t, size_t> objectIndexByHandle;
    std::unordered_map<std::string, std::vector<size_t>> objectIndicesBySourceNameLower;
    std::unordered_map<int64_t, std::vector<size_t>> pickableObjectIndicesByCell;
    std::unordered_map<int64_t, std::vector<size_t>> collidableObjectIndicesByCell;
    std::unordered_map<int64_t, std::vector<size_t>> actorObjectIndicesByCell;
    float pickableObjectCellSize = 512.0f;
    float collidableObjectCellSize = 512.0f;
    float actorObjectCellSize = 512.0f;
    Mm9DatObjectRegistryStats stats;
};

enum class Mm9DatObjectPresentationKind
{
    Object,
    Actor,
    Prop,
    Pickup,
    Light,
    Mechanism,
};

struct Mm9DatObjectPresentationInstance
{
    size_t instanceIndex = 0;
    size_t objectIndex = 0;
    uint32_t objectHandle = 0;
    size_t sourceObjectIndex = 0;
    std::string objectId;
    std::string sourceClass;
    std::string sourceName;
    std::string sourceModel;
    std::string modelAsset;
    std::string visualId;
    Mm9DatVec3 position;
    float radius = 0.0f;
    float height = 0.0f;
    Mm9DatObjectPresentationKind kind = Mm9DatObjectPresentationKind::Object;
    bool collidable = false;
    bool interactable = false;
    bool ticking = false;
};

struct Mm9DatObjectPresentationWorldStats
{
    size_t instanceCount = 0;
    size_t actorInstanceCount = 0;
    size_t propInstanceCount = 0;
    size_t pickupInstanceCount = 0;
    size_t lightInstanceCount = 0;
    size_t mechanismInstanceCount = 0;
    size_t genericObjectInstanceCount = 0;
    size_t collidableInstanceCount = 0;
    size_t interactableInstanceCount = 0;
    size_t tickingInstanceCount = 0;
    size_t sourceModelInstanceCount = 0;
    size_t modelAssetInstanceCount = 0;
    size_t visualIdInstanceCount = 0;
    size_t sourceModelWithoutModelAssetCount = 0;
};

struct Mm9DatObjectPresentationWorld
{
    std::vector<Mm9DatObjectPresentationInstance> instances;
    Mm9DatObjectPresentationWorldStats stats;
};

struct Mm9DatObjectModelRenderPlanStats
{
    size_t presentationInstanceCount = 0;
    size_t candidateInstanceCount = 0;
    size_t sourceModelCandidateCount = 0;
    size_t modelAssetCandidateCount = 0;
    size_t scriptedObjectMatchCount = 0;
    size_t missingScriptedObjectCount = 0;
    size_t renderInstanceCount = 0;
};

struct Mm9DatObjectModelRenderInstance
{
    size_t renderInstanceIndex = 0;
    size_t presentationInstanceIndex = 0;
    size_t sourceObjectIndex = 0;
    uint32_t objectHandle = 0;
    Mm9DatVec3 runtimePosition;
    Mm9ScriptedObject object;
};

struct Mm9DatObjectModelRenderPlan
{
    std::vector<Mm9DatObjectModelRenderInstance> instances;
    Mm9DatObjectModelRenderPlanStats stats;
};

enum class Mm9DatMechanismState
{
    Closed,
    Opening,
    Open,
    Closing,
};

enum class Mm9DatMechanismCommand
{
    Open,
    Close,
    Toggle,
};

enum class Mm9DatMechanismCommandStatus
{
    Applied,
    AlreadyInRequestedState,
    MissingHandle,
    Inert,
    Locked,
};

struct Mm9DatMechanismInstance
{
    uint32_t handle = 0;
    size_t mechanismIndex = 0;
    std::string mechanismId;
    std::string objectId;
    int sourceObjectIndex = -1;
    std::string sourceClass;
    std::string sourceName;
    std::string kind;
    size_t sourceModelIndex = 0;
    std::string sourceModelName;
    Mm9DatMechanismState state = Mm9DatMechanismState::Closed;
    float progress = 0.0f;
    float openingDurationSeconds = 1.0f;
    float closingDurationSeconds = 1.0f;
    bool locked = false;
    bool lockOnClose = false;
    bool pushOpen = false;
    bool touchToOpen = false;
    bool reopenOnContact = false;
    float moveDelaySeconds = 0.0f;
    float moveDelayRemainingSeconds = 0.0f;
    float openWaitSeconds = 0.0f;
    float openWaitRemainingSeconds = 0.0f;
    bool active = false;
    bool inert = false;
    std::string inertReason;
    Mm9DatMechanismPreviewMotion motion;
    Mm9DatRenderBounds closedBounds;
    Mm9DatRenderBounds openBounds;
    Mm9DatRenderBounds currentBounds;
    bool boundsChangeKnown = false;
    bool boundsChanged = false;
    bool queuedForUpdate = false;
    std::vector<Mm9EventTriggerOutput> triggerOutputs;
    std::vector<Mm9EventMechanismSound> sounds;
};

struct Mm9DatMechanismCommandResult
{
    Mm9DatMechanismCommandStatus status = Mm9DatMechanismCommandStatus::MissingHandle;
    uint32_t handle = 0;
    size_t mechanismIndex = 0;
    Mm9DatMechanismState previousState = Mm9DatMechanismState::Closed;
    Mm9DatMechanismState newState = Mm9DatMechanismState::Closed;
    float previousProgress = 0.0f;
    float newProgress = 0.0f;
    bool stateChanged = false;
};

struct Mm9DatMechanismUpdateStats
{
    size_t updatedMechanismCount = 0;
    size_t completedMechanismCount = 0;
    size_t changedBoundsCount = 0;
    std::vector<size_t> changedMechanismIndices;
};

struct Mm9DatMechanismRuntimeStats
{
    size_t mechanismCount = 0;
    size_t activeMechanismCount = 0;
    size_t inertMechanismCount = 0;
    size_t linearMotionCount = 0;
    size_t rotationMotionCount = 0;
    size_t changedBoundsCount = 0;
    size_t unresolvedBindingCount = 0;
    size_t unresolvedTargetCount = 0;
};

struct Mm9DatMechanismRuntime
{
    std::vector<Mm9DatMechanismInstance> mechanisms;
    std::vector<size_t> movingMechanismIndices;
    std::unordered_map<std::string, size_t> mechanismIndexByObjectId;
    std::unordered_map<uint32_t, size_t> mechanismIndexByHandle;
    Mm9DatMechanismRuntimeStats stats;
};

struct Mm9DatMechanismBoundsIndexStats
{
    size_t mechanismCount = 0;
    size_t indexedMechanismCount = 0;
    size_t cellCount = 0;
    size_t mechanismCellRefs = 0;
    size_t maxCellMechanismRefs = 0;
    float cellSize = 512.0f;
};

struct Mm9DatMechanismBoundsIndex
{
    std::unordered_map<int64_t, std::vector<size_t>> mechanismIndicesByCell;
    std::vector<std::vector<int64_t>> cellKeysByMechanismIndex;
    float cellSize = 512.0f;
    Mm9DatMechanismBoundsIndexStats stats;
};

struct Mm9DatMechanismCollisionBatch
{
    uint32_t mechanismHandle = 0;
    std::string mechanismId;
    std::string objectId;
    size_t sourceModelIndex = 0;
    std::string sourceModelName;
    Mm9DatMechanismPreviewMotion motion;
    Mm9DatRenderBounds currentBounds;
    std::vector<size_t> sourceTriangleIndices;
    std::vector<Mm9DatRenderTriangle> transformedTriangles;
};

struct Mm9DatMechanismCollisionCacheStats
{
    size_t batchCount = 0;
    size_t sourceTriangleCount = 0;
    size_t transformedTriangleCount = 0;
    size_t activeMechanismCount = 0;
    size_t indexedBatchCount = 0;
};

struct Mm9DatMechanismCollisionCache
{
    std::vector<Mm9DatMechanismCollisionBatch> batches;
    std::unordered_map<uint32_t, size_t> batchIndexByMechanismHandle;
    Mm9DatMechanismCollisionCacheStats stats;
};

struct Mm9DatWorldRuntimeBuildInput
{
    std::string mapId;
    const Mm9DatWorld *pWorld = nullptr;
    const Mm9EventsData *pEvents = nullptr;
    std::vector<Mm9DatModelRenderRole> modelRoles;
    std::vector<Mm9DatRenderMaterialAssignment> materialAssignments;
    std::vector<Mm9ScriptedObject> scriptedObjects;
    std::vector<std::filesystem::path> textureSourceRoots;
};

struct Mm9DatWorldRuntimeStats
{
    std::string mapId;
    size_t worldModelCount = 0;
    size_t sourcePolyCount = 0;
    size_t renderTriangleCount = 0;
    size_t visibleWaterTriangleCount = 0;
    size_t waterVolumeTriangleCount = 0;
    size_t renderPartitionCount = 0;
    size_t dynamicMechanismRenderBatchCount = 0;
    size_t dynamicMechanismTriangleCount = 0;
    size_t preparedRenderSectionCount = 0;
    size_t preparedRenderVertexCount = 0;
    size_t preparedRenderIndexCount = 0;
    size_t renderDrawCallCount = 0;
    size_t renderSubmittedTriangleCount = 0;
    size_t renderTextureMissDrawCallCount = 0;
    size_t runtimeMaterialCount = 0;
    size_t runtimeMissingMaterialCount = 0;
    size_t runtimeTextureCacheEligibleCount = 0;
    size_t runtimeTextureCatalogEntryCount = 0;
    size_t runtimeTextureCatalogKeyCount = 0;
    size_t runtimeResolvedTextureMaterialCount = 0;
    size_t runtimeMissingTextureMaterialCount = 0;
    size_t collisionTriangleCount = 0;
    size_t collisionCellCount = 0;
    size_t objectCount = 0;
    size_t renderableObjectCount = 0;
    size_t collidableObjectCount = 0;
    size_t collidableObjectCellCount = 0;
    size_t collidableObjectCellRefs = 0;
    size_t maxCollidableObjectCellRefs = 0;
    size_t actorObjectCellCount = 0;
    size_t actorObjectCellRefs = 0;
    size_t maxActorObjectCellRefs = 0;
    size_t objectRenderInstanceCount = 0;
    size_t actorRenderInstanceCount = 0;
    size_t propRenderInstanceCount = 0;
    size_t objectRenderModelAssetInstanceCount = 0;
    size_t objectRenderSourceModelWithoutAssetCount = 0;
    size_t interactableObjectCount = 0;
    size_t actorObjectCount = 0;
    size_t propObjectCount = 0;
    size_t triggerObjectCount = 0;
    size_t mechanismObjectCount = 0;
    size_t tickingObjectCount = 0;
    size_t snappedToFloorCount = 0;
    size_t mechanismCount = 0;
    size_t activeMechanismCount = 0;
    size_t inertMechanismCount = 0;
    size_t mechanismBoundsCellCount = 0;
    size_t mechanismBoundsCellRefs = 0;
    size_t mechanismCollisionBatchCount = 0;
    size_t mechanismCollisionTriangleCount = 0;
    size_t lightCount = 0;
    size_t staticRenderLightCount = 0;
    size_t skyDefinitionCount = 0;
    size_t skyObjectCount = 0;
    size_t skyModelCount = 0;
};

struct Mm9DatWorldRuntime
{
    std::string mapId;
    Mm9DatRenderMesh renderMesh;
    Mm9DatRenderFilterResult renderFilters;
    Mm9DatRenderWorld renderWorld;
    Mm9DatMechanismRenderWorld mechanismRenderWorld;
    Mm9DatPreparedRenderWorld preparedRenderWorld;
    Mm9DatRuntimeMaterialTable materialTable;
    Mm9DatRuntimeTextureCatalog textureCatalog;
    Mm9DatRuntimeTextureBindings textureBindings;
    Mm9DatRenderSubmissionPlan renderSubmissionPlan;
    Mm9DatPhysicsQueryView physicsQueryView;
    Mm9DatCollisionWorld collisionWorld;
    Mm9DatObjectRegistry objectRegistry;
    Mm9DatObjectPresentationWorld objectPresentationWorld;
    Mm9DatMechanismRuntime mechanismRuntime;
    Mm9DatMechanismBoundsIndex mechanismBoundsIndex;
    Mm9DatMechanismCollisionCache mechanismCollisionCache;
    Mm9LightLayer lightLayer;
    std::vector<RenderLight> staticRenderLights;
    Mm9SkyLayer skyLayer;
    std::optional<Mm9SkyDef> activeSkyDef;
    std::optional<Mm9SkyCameraMap> skyCameraMap;
    Mm9DatWorldRuntimeStats stats;
    std::vector<std::string> diagnostics;
};

struct Mm9DatPartyMovementStep
{
    Mm9DatVec3 position;
    Mm9DatVec3 desiredDisplacement;
    float radius = 24.0f;
    float halfHeight = 64.0f;
    float floorSnapDistance = 96.0f;
    float floorBias = 0.1f;
    float maxStepHeight = 24.0f;
    uint32_t wallChannelMask = Mm9DatPhysicsQueryChannelPhysics;
    uint32_t floorChannelMask = Mm9DatPhysicsQueryChannelPhysics;
};

struct Mm9DatMechanismCollisionHit
{
    Mm9DatVec3 point;
    Mm9DatVec3 normal;
    float distance = 0.0f;
    uint32_t mechanismHandle = 0;
    std::string mechanismId;
    std::string objectId;
    size_t sourceObjectIndex = 0;
    size_t sourceModelIndex = 0;
    size_t sourcePolyIndex = 0;
    size_t sourceSurfaceIndex = 0;
    std::string sourceModelName;
};

struct Mm9DatObjectCollisionHit
{
    Mm9DatVec3 point;
    Mm9DatVec3 normal;
    float distance = 0.0f;
    uint32_t objectHandle = 0;
    std::string objectId;
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
};

struct Mm9DatPartyMovementResult
{
    Mm9DatVec3 startPosition;
    Mm9DatVec3 finalPosition;
    Mm9DatVec3 appliedDisplacement;
    bool blockedByWall = false;
    bool blockedByMechanism = false;
    bool blockedByObject = false;
    bool slidAlongWall = false;
    bool steppedUp = false;
    bool onGround = false;
    bool mechanismContactCommandAttempted = false;
    size_t wallCandidateTriangleCount = 0;
    size_t wallTestedTriangleCount = 0;
    size_t objectCandidateCount = 0;
    size_t objectTestedCount = 0;
    size_t mechanismCandidateCount = 0;
    size_t mechanismTestedCount = 0;
    size_t mechanismCandidateTriangleCount = 0;
    size_t mechanismTestedTriangleCount = 0;
    size_t floorCandidateTriangleCount = 0;
    size_t floorTestedTriangleCount = 0;
    std::optional<Mm9DatCollisionRayHit> wallHit;
    std::optional<Mm9DatObjectCollisionHit> objectHit;
    std::optional<Mm9DatMechanismCollisionHit> mechanismHit;
    std::optional<Mm9DatMechanismCollisionHit> mechanismFloorHit;
    std::optional<Mm9DatFloorSupportHit> floorHit;
    Mm9DatMechanismCommandResult mechanismContactCommand;
};

enum class Mm9DatWorldPickHitKind
{
    None,
    World,
    Object,
    Mechanism,
};

struct Mm9DatWorldPickOptions
{
    uint32_t worldChannelMask = Mm9DatPhysicsQueryChannelPhysics | Mm9DatPhysicsQueryChannelVisible;
    float maxDistance = 512.0f;
    bool includeBackfaces = true;
    bool includeWorld = true;
    bool includeObjects = true;
    bool includeMechanisms = true;
};

struct Mm9DatWorldPickHit
{
    Mm9DatWorldPickHitKind kind = Mm9DatWorldPickHitKind::None;
    Mm9DatVec3 point;
    Mm9DatVec3 normal;
    float distance = 0.0f;
    uint32_t objectHandle = 0;
    uint32_t mechanismHandle = 0;
    std::string objectId;
    std::string mechanismId;
    size_t sourceObjectIndex = 0;
    size_t sourceModelIndex = 0;
    size_t sourcePolyIndex = 0;
    size_t sourceSurfaceIndex = 0;
    std::string sourceModelName;
    size_t candidateObjectCount = 0;
    size_t testedObjectCount = 0;
    size_t candidateMechanismCount = 0;
    size_t testedMechanismCount = 0;
    size_t candidateTriangleCount = 0;
    size_t testedTriangleCount = 0;
};

struct Mm9DatWorldActivationInfo
{
    bool hasObject = false;
    bool hasMechanism = false;
    uint32_t objectHandle = 0;
    uint32_t mechanismHandle = 0;
    std::string objectId;
    int objectSourceObjectIndex = -1;
    std::string objectSourceClass;
    std::string objectSourceName;
    std::string objectSourceModel;
    std::string objectScriptName;
    std::string objectScriptParams;
    std::string mechanismId;
    int mechanismSourceObjectIndex = -1;
    std::string mechanismSourceClass;
    std::string mechanismSourceName;
    std::string mechanismKind;
    std::string mechanismSourceModelName;
    std::vector<Mm9EventTriggerOutput> triggerOutputs;
    std::vector<Mm9EventMechanismSound> sounds;
};

struct Mm9DatWorldTriggerDispatch
{
    std::string phase;
    int slot = -1;
    std::string sourceObjectId;
    std::string sourceMechanismId;
    std::string targetName;
    std::string messageName;
    std::string targetHandle;
    std::string targetObjectId;
    uint32_t targetObjectHandle = 0;
    int targetSourceObjectIndex = -1;
    std::string targetSourceClass;
    std::string targetSourceName;
    bool resolvedTarget = false;
    bool ambiguousTarget = false;
    size_t targetCandidateCount = 0;
};

struct Mm9DatWorldUseResult
{
    bool picked = false;
    bool commandAttempted = false;
    bool activated = false;
    Mm9DatWorldPickHit hit;
    Mm9DatWorldActivationInfo activation;
    std::vector<Mm9DatWorldTriggerDispatch> triggerDispatches;
    Mm9DatMechanismCommandResult mechanismCommand;
};

struct Mm9DatWorldRuntimeUpdateStats
{
    Mm9DatMechanismUpdateStats mechanisms;
    bool mechanismRenderWorldUpdated = false;
};

Mm9DatRenderWorld buildMm9DatRenderWorld(
    const Mm9DatRenderMesh &mesh,
    const Mm9DatRenderFilterResult &filters,
    const std::vector<Mm9DatRenderMaterialAssignment> &materialAssignments = {},
    const std::vector<size_t> &dynamicSourceModelIndices = {});

Mm9DatMechanismRenderWorld buildMm9DatMechanismRenderWorld(
    const Mm9DatRenderMesh &mesh,
    const Mm9DatMechanismRuntime &mechanismRuntime);

void updateMm9DatMechanismRenderWorldTransforms(
    Mm9DatMechanismRenderWorld &renderWorld,
    const Mm9DatMechanismRuntime &mechanismRuntime);

Mm9DatPreparedRenderWorld buildMm9DatPreparedRenderWorld(
    const Mm9DatRenderMesh &mesh,
    const Mm9DatRenderWorld &renderWorld,
    const Mm9DatMechanismRenderWorld &mechanismRenderWorld,
    const Mm9DatRenderFilterResult &filters,
    const std::vector<Mm9DatRenderMaterialAssignment> &materialAssignments = {});

void updateMm9DatPreparedMechanismRenderWorld(
    Mm9DatPreparedRenderWorld &preparedRenderWorld,
    const Mm9DatRenderMesh &mesh,
    const Mm9DatMechanismRenderWorld &mechanismRenderWorld);

Mm9DatRuntimeMaterialTable buildMm9DatRuntimeMaterialTable(
    Mm9DatPreparedRenderWorld &preparedRenderWorld);

Mm9DatRuntimeTextureCatalog buildMm9DatRuntimeTextureCatalog(
    const std::vector<std::filesystem::path> &sourceRoots);

Mm9DatRuntimeTextureBindings bindMm9DatRuntimeTextures(
    const Mm9DatRuntimeMaterialTable &materialTable,
    const Mm9DatRuntimeTextureCatalog &textureCatalog);

Mm9DatRenderSubmissionPlan buildMm9DatRenderSubmissionPlan(
    const Mm9DatPreparedRenderWorld &preparedRenderWorld,
    const Mm9DatRenderSubmissionOptions &options = {});

Mm9DatObjectRegistry buildMm9DatObjectRegistry(
    const std::vector<Mm9ScriptedObject> &objects,
    const Mm9DatCollisionWorld &collisionWorld,
    const Mm9DatMechanismRuntime *pMechanismRuntime = nullptr);

Mm9DatObjectPresentationWorld buildMm9DatObjectPresentationWorld(
    const Mm9DatObjectRegistry &registry);

Mm9DatObjectModelRenderPlan buildMm9DatObjectModelRenderPlan(
    const Mm9DatObjectPresentationWorld &presentationWorld,
    const std::vector<Mm9ScriptedObject> &scriptedObjects);

std::vector<size_t> collectMm9DatActorObjectIndicesWithinRadius(
    const Mm9DatObjectRegistry &registry,
    const Mm9DatVec3 &center,
    float radius);

Mm9DatMechanismRuntime buildMm9DatMechanismRuntime(
    const Mm9EventsData &events,
    const Mm9DatRenderMesh &renderMesh);

Mm9DatMechanismBoundsIndex buildMm9DatMechanismBoundsIndex(
    const Mm9DatMechanismRuntime &runtime,
    float cellSize = 512.0f);

void updateMm9DatMechanismBoundsIndex(
    Mm9DatMechanismBoundsIndex &index,
    const Mm9DatMechanismRuntime &runtime,
    const std::vector<size_t> &mechanismIndices);

Mm9DatMechanismCollisionCache buildMm9DatMechanismCollisionCache(
    const Mm9DatRenderMesh &mesh,
    const Mm9DatMechanismRuntime &runtime);

void updateMm9DatMechanismCollisionCache(
    Mm9DatMechanismCollisionCache &cache,
    const Mm9DatRenderMesh &mesh,
    const Mm9DatMechanismRuntime &runtime,
    const std::vector<size_t> &mechanismIndices);

Mm9DatMechanismCommandResult commandMm9DatMechanism(
    Mm9DatMechanismRuntime &runtime,
    uint32_t handle,
    Mm9DatMechanismCommand command,
    bool ignoreLocks = false);

Mm9DatMechanismUpdateStats updateMm9DatMechanisms(
    Mm9DatMechanismRuntime &runtime,
    float deltaSeconds);

Mm9DatPartyMovementResult moveMm9DatParty(
    const Mm9DatCollisionWorld &collisionWorld,
    const Mm9DatPartyMovementStep &step);

Mm9DatPartyMovementResult moveMm9DatPartyInWorldRuntime(
    Mm9DatWorldRuntime &runtime,
    const Mm9DatPartyMovementStep &step);

std::optional<Mm9DatWorldPickHit> pickMm9DatWorldRuntime(
    const Mm9DatWorldRuntime &runtime,
    const Mm9DatPickRay &ray,
    const Mm9DatWorldPickOptions &options = {});

Mm9DatMechanismCommandResult commandMm9DatMechanismByObject(
    Mm9DatMechanismRuntime &runtime,
    const std::string &objectId,
    Mm9DatMechanismCommand command,
    bool ignoreLocks = false);

Mm9DatWorldUseResult useMm9DatWorldRuntime(
    Mm9DatWorldRuntime &runtime,
    const Mm9DatPickRay &ray,
    const Mm9DatWorldPickOptions &options = {},
    Mm9DatMechanismCommand command = Mm9DatMechanismCommand::Toggle,
    bool ignoreLocks = false);

Mm9DatWorldUseResult useMm9DatWorldPickedHitRuntime(
    Mm9DatWorldRuntime &runtime,
    const Mm9DatWorldPickHit &hit,
    Mm9DatMechanismCommand command = Mm9DatMechanismCommand::Toggle,
    bool ignoreLocks = false);

Mm9DatWorldRuntimeUpdateStats updateMm9DatWorldRuntime(
    Mm9DatWorldRuntime &runtime,
    float deltaSeconds);

Mm9DatWorldRuntime buildMm9DatWorldRuntime(
    const Mm9DatWorldRuntimeBuildInput &input);
}
