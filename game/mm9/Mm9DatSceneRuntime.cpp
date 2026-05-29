#include "game/mm9/Mm9DatSceneRuntime.h"

#include "game/gameplay/GameplayInputFrame.h"
#include "game/mm9/Mm9AnimatedActorBinding.h"
#include "game/mm9/Mm9AnimatedModelResolver.h"
#include "game/mm9/Mm9AnimatedModelSidecar.h"
#include "game/mm9/Mm9DialogueRuntime.h"
#include "game/mm9/Mm9DtxTexture.h"
#include "game/mm9/Mm9ScriptRuntime.h"
#include "game/render/TextureFiltering.h"
#include "game/ui/GameplayOverlayTypes.h"

#include <bgfx/bgfx.h>
#include <bx/math.h>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <limits>
#include <memory>
#include <sstream>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float RadiansPerDegree = 0.01745329251994329576923690768489f;
constexpr bgfx::ViewId Mm9DatWorldViewId = 0;
constexpr float Mm9DatCameraVerticalFovDegrees = 60.0f;
constexpr float Mm9DatCameraEyeHeight = 96.0f;
constexpr float Mm9DatKeyboardYawSpeed = 1.75f;
constexpr float Mm9DatKeyboardPitchSpeed = 1.25f;
constexpr float Mm9DatMouseRotateSpeed = 0.0045f;
constexpr float Mm9DatMaxPitchRadians = 1.35f;
constexpr float Pi = 3.14159265358979323846f;

std::string lowerCopy(const std::string &value)
{
    std::string result;
    result.reserve(value.size());

    for (char character : value)
    {
        result.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
    }

    return result;
}

std::string normalizeMm9DatSceneTextureKey(const std::string &value)
{
    std::string normalized = value;
    std::replace(normalized.begin(), normalized.end(), '\\', '/');

    while (!normalized.empty() && normalized.front() == '/')
    {
        normalized.erase(normalized.begin());
    }

    return lowerCopy(normalized);
}

std::optional<size_t> findMm9DatSceneTextureCatalogEntry(
    const Mm9DatRuntimeTextureCatalog &catalog,
    const std::string &textureName)
{
    const std::string key = normalizeMm9DatSceneTextureKey(textureName);
    if (key.empty())
    {
        return std::nullopt;
    }

    const auto exactIterator = catalog.entryIndexByKey.find(key);
    if (exactIterator != catalog.entryIndexByKey.end())
    {
        return exactIterator->second;
    }

    if (std::filesystem::path(key).extension().empty())
    {
        const auto dtxIterator = catalog.entryIndexByKey.find(key + ".dtx");
        if (dtxIterator != catalog.entryIndexByKey.end())
        {
            return dtxIterator->second;
        }
    }

    return std::nullopt;
}

float axisValue(bool positive, bool negative)
{
    return (positive ? 1.0f : 0.0f) - (negative ? 1.0f : 0.0f);
}

std::string shaderDirectoryForRenderer(bgfx::RendererType::Enum rendererType)
{
    switch (rendererType)
    {
        case bgfx::RendererType::Direct3D11:
            return "dxbc";
        case bgfx::RendererType::OpenGL:
        case bgfx::RendererType::Noop:
            return "glsl";
        case bgfx::RendererType::OpenGLES:
            return "essl";
        default:
            return {};
    }
}

bgfx::ShaderHandle loadMm9DatShader(const char *pShaderName)
{
    const std::string shaderDirectory = shaderDirectoryForRenderer(bgfx::getRendererType());
    if (shaderDirectory.empty())
    {
        return BGFX_INVALID_HANDLE;
    }

    const std::filesystem::path shaderPath =
        std::filesystem::path(OPENYAMM_BGFX_SHADER_DIR) / shaderDirectory / (std::string(pShaderName) + ".bin");
    std::ifstream stream(shaderPath, std::ios::binary);
    if (!stream)
    {
        std::cerr << "Mm9DatSceneRuntime: missing shader " << shaderPath << '\n';
        return BGFX_INVALID_HANDLE;
    }

    std::vector<char> shaderBytes(
        (std::istreambuf_iterator<char>(stream)),
        std::istreambuf_iterator<char>());
    if (shaderBytes.empty())
    {
        std::cerr << "Mm9DatSceneRuntime: empty shader " << shaderPath << '\n';
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createShader(bgfx::copy(shaderBytes.data(), static_cast<uint32_t>(shaderBytes.size())));
}

bgfx::ProgramHandle loadMm9DatProgram(const char *pVertexShaderName, const char *pFragmentShaderName)
{
    const bgfx::ShaderHandle vertexShaderHandle = loadMm9DatShader(pVertexShaderName);
    const bgfx::ShaderHandle fragmentShaderHandle = loadMm9DatShader(pFragmentShaderName);
    if (!bgfx::isValid(vertexShaderHandle) || !bgfx::isValid(fragmentShaderHandle))
    {
        if (bgfx::isValid(vertexShaderHandle))
        {
            bgfx::destroy(vertexShaderHandle);
        }
        if (bgfx::isValid(fragmentShaderHandle))
        {
            bgfx::destroy(fragmentShaderHandle);
        }
        return BGFX_INVALID_HANDLE;
    }

    return bgfx::createProgram(vertexShaderHandle, fragmentShaderHandle, true);
}

bx::Vec3 gameplayVecFromMm9DatVec(const Mm9DatVec3 &value)
{
    return {value.x, value.z, value.y};
}

Mm9DatVec3 mm9DatVecFromGameplayVec(const bx::Vec3 &value)
{
    return {value.x, value.z, value.y};
}

Mm9DatPickRay mm9DatPartyPickRay(const Mm9DatPartyRuntimeState &partyState)
{
    Mm9DatPickRay ray = {};
    ray.origin = {
        partyState.position.x,
        partyState.position.y + Mm9DatCameraEyeHeight,
        partyState.position.z,
    };
    ray.direction = mm9DatPartyForwardVector(partyState.yawRadians, partyState.pitchRadians);
    return ray;
}

Mm9DatPickRay mm9DatPickRayFromGameplayRequest(
    const GameplayWorldPickRequest &request,
    const Mm9DatPartyRuntimeState &partyState)
{
    if (!request.hasRay)
    {
        return mm9DatPartyPickRay(partyState);
    }

    Mm9DatPickRay ray = {};
    ray.origin = mm9DatVecFromGameplayVec(request.rayOrigin);
    ray.direction = mm9DatVecFromGameplayVec(request.rayDirection);
    return ray;
}

Mm9DatWorldPickOptions mm9DatGameplayInteractionPickOptions()
{
    Mm9DatWorldPickOptions options = {};
    options.maxDistance = 512.0f;
    options.includeWorld = true;
    options.includeObjects = true;
    options.includeMechanisms = true;
    return options;
}

const Mm9DatMechanismInstance *findMm9DatMechanismByHandle(
    const Mm9DatMechanismRuntime &runtime,
    uint32_t handle)
{
    const auto mechanismIterator = runtime.mechanismIndexByHandle.find(handle);
    if (mechanismIterator == runtime.mechanismIndexByHandle.end()
        || mechanismIterator->second >= runtime.mechanisms.size())
    {
        return nullptr;
    }

    return &runtime.mechanisms[mechanismIterator->second];
}

const Mm9DatMechanismInstance *findMm9DatMechanismByObjectId(
    const Mm9DatMechanismRuntime &runtime,
    const std::string &objectId)
{
    const auto mechanismIterator = runtime.mechanismIndexByObjectId.find(objectId);

    return mechanismIterator != runtime.mechanismIndexByObjectId.end()
        && mechanismIterator->second < runtime.mechanisms.size()
            ? &runtime.mechanisms[mechanismIterator->second]
            : nullptr;
}

const Mm9DatRuntimeObject *findMm9DatObjectByHandle(
    const Mm9DatObjectRegistry &registry,
    uint32_t handle)
{
    const auto objectIterator = registry.objectIndexByHandle.find(handle);
    if (objectIterator == registry.objectIndexByHandle.end()
        || objectIterator->second >= registry.objects.size())
    {
        return nullptr;
    }

    return &registry.objects[objectIterator->second];
}

std::optional<size_t> mm9DatActorIndexByObjectHandle(
    const Mm9DatObjectRegistry &registry,
    uint32_t objectHandle)
{
    const auto objectIterator = registry.objectIndexByHandle.find(objectHandle);
    if (objectIterator == registry.objectIndexByHandle.end())
    {
        return std::nullopt;
    }

    const size_t objectIndex = objectIterator->second;
    if (objectIndex >= registry.actorIndexByObjectIndex.size())
    {
        return std::nullopt;
    }

    const size_t actorIndex = registry.actorIndexByObjectIndex[objectIndex];
    return actorIndex < registry.actorObjectIndices.size()
        ? std::optional<size_t>(actorIndex)
        : std::nullopt;
}

std::optional<int32_t> mm9DatSourceObjectIndexMetadata(size_t sourceObjectIndex)
{
    if (sourceObjectIndex > static_cast<size_t>(std::numeric_limits<int32_t>::max()))
    {
        return std::nullopt;
    }

    return static_cast<int32_t>(sourceObjectIndex);
}

std::string mm9DatInteractionName(
    const Mm9DatWorldPickHit &hit,
    const Mm9DatMechanismInstance *pMechanism,
    const Mm9DatRuntimeObject *pObject)
{
    if (pObject != nullptr && !pObject->sourceName.empty())
    {
        return pObject->sourceName;
    }
    if (pMechanism != nullptr && !pMechanism->sourceName.empty())
    {
        return pMechanism->sourceName;
    }
    if (!hit.sourceModelName.empty())
    {
        return hit.sourceModelName;
    }
    if (!hit.mechanismId.empty())
    {
        return hit.mechanismId;
    }
    return hit.objectId;
}

GameplayEventTargetContextActionMetadata mm9DatContextActionMetadata(
    const Mm9DatWorldPickHit &hit,
    const Mm9DatMechanismInstance *pMechanism,
    const Mm9DatRuntimeObject *pObject,
    bool objectRoutesToMechanism)
{
    GameplayEventTargetContextActionMetadata metadata = {};
    metadata.kind = objectRoutesToMechanism ? "use_switch" : "generic_event";
    metadata.source = "mm9_dat";
    metadata.targetName = mm9DatInteractionName(hit, pMechanism, pObject);
    metadata.mm9ObjectId = !hit.objectId.empty()
        ? hit.objectId
        : (pMechanism != nullptr ? pMechanism->objectId : "");
    metadata.mm9SourceObjectIndex = mm9DatSourceObjectIndexMetadata(hit.sourceObjectIndex);
    metadata.mm9SourceClass = pMechanism != nullptr ? pMechanism->sourceClass : "";
    metadata.mm9SourceName = pMechanism != nullptr ? pMechanism->sourceName : "";

    if (pObject != nullptr)
    {
        metadata.mm9SourceClass = pObject->sourceClass;
        metadata.mm9SourceName = pObject->sourceName;
        metadata.mm9SourceObjectIndex = mm9DatSourceObjectIndexMetadata(pObject->sourceObjectIndex);
    }

    if (pMechanism != nullptr && pMechanism->sourceObjectIndex >= 0)
    {
        metadata.mm9SourceObjectIndex =
            mm9DatSourceObjectIndexMetadata(static_cast<size_t>(pMechanism->sourceObjectIndex));
    }

    return metadata;
}

GameplayWorldHit gameplayWorldHitFromMm9DatPickHit(
    const Mm9DatWorldRuntime &runtime,
    const Mm9DatWorldPickHit &hit)
{
    GameplayWorldHit gameplayHit = {};
    gameplayHit.hasHit = true;

    if (hit.kind == Mm9DatWorldPickHitKind::World)
    {
        GameplayGroundTargetHit ground = {};
        ground.worldPoint = gameplayVecFromMm9DatVec(hit.point);
        ground.distance = hit.distance;
        ground.isValid = true;
        gameplayHit.kind = GameplayWorldHitKind::Ground;
        gameplayHit.ground = ground;
        return gameplayHit;
    }

    const Mm9DatMechanismInstance *pMechanism = nullptr;
    const Mm9DatRuntimeObject *pObject = nullptr;
    if (hit.kind == Mm9DatWorldPickHitKind::Mechanism)
    {
        pMechanism = findMm9DatMechanismByHandle(runtime.mechanismRuntime, hit.mechanismHandle);
    }
    else if (hit.kind == Mm9DatWorldPickHitKind::Object)
    {
        pObject = findMm9DatObjectByHandle(runtime.objectRegistry, hit.objectHandle);
        pMechanism = findMm9DatMechanismByObjectId(runtime.mechanismRuntime, hit.objectId);
    }

    if (hit.kind == Mm9DatWorldPickHitKind::Object && pObject != nullptr)
    {
        const std::optional<size_t> actorIndex =
            mm9DatActorIndexByObjectHandle(runtime.objectRegistry, hit.objectHandle);
        if (actorIndex)
        {
            GameplayActorTargetHit actor = {};
            actor.actorIndex = *actorIndex;
            actor.displayName =
                !pObject->sourceName.empty()
                    ? pObject->sourceName
                    : (!pObject->sourceClass.empty() ? pObject->sourceClass : pObject->objectId);
            actor.hitPoint = gameplayVecFromMm9DatVec(hit.point);
            actor.distance = hit.distance;

            gameplayHit.kind = GameplayWorldHitKind::Actor;
            gameplayHit.actor = actor;
            return gameplayHit;
        }
    }

    if (hit.kind == Mm9DatWorldPickHitKind::Mechanism || hit.kind == Mm9DatWorldPickHitKind::Object)
    {
        const bool objectRoutesToMechanism =
            hit.kind == Mm9DatWorldPickHitKind::Mechanism || pMechanism != nullptr;
        GameplayEventTargetHit eventTarget = {};
        eventTarget.targetKind = hit.kind == Mm9DatWorldPickHitKind::Mechanism
            ? GameplayWorldEventTargetKind::Mechanism
            : GameplayWorldEventTargetKind::Object;
        eventTarget.targetIndex = hit.kind == Mm9DatWorldPickHitKind::Mechanism
            ? static_cast<size_t>(hit.mechanismHandle)
            : static_cast<size_t>(hit.objectHandle);
        eventTarget.secondaryIndex = hit.sourceModelIndex;
        eventTarget.name = mm9DatInteractionName(hit, pMechanism, pObject);
        eventTarget.contextActionMetadata =
            mm9DatContextActionMetadata(hit, pMechanism, pObject, objectRoutesToMechanism);
        eventTarget.hitPoint = gameplayVecFromMm9DatVec(hit.point);
        eventTarget.distance = hit.distance;

        gameplayHit.kind = GameplayWorldHitKind::EventTarget;
        gameplayHit.eventTarget = eventTarget;
        return gameplayHit;
    }

    gameplayHit.hasHit = false;
    gameplayHit.kind = GameplayWorldHitKind::None;
    return gameplayHit;
}

GameplayWorldHit pickMm9DatGameplayWorldHit(
    const Mm9DatWorldRuntime &runtime,
    const Mm9DatPartyRuntimeState &partyState,
    const GameplayWorldPickRequest &request)
{
    const Mm9DatPickRay ray = mm9DatPickRayFromGameplayRequest(request, partyState);
    const std::optional<Mm9DatWorldPickHit> hit =
        pickMm9DatWorldRuntime(runtime, ray, mm9DatGameplayInteractionPickOptions());

    if (!hit)
    {
        return {};
    }

    return gameplayWorldHitFromMm9DatPickHit(runtime, *hit);
}

uint16_t clampedUint16FromFloat(float value)
{
    if (value <= 0.0f)
    {
        return 0;
    }

    return static_cast<uint16_t>(
        std::min(value, static_cast<float>(std::numeric_limits<uint16_t>::max())));
}

bool mm9DatActorRuntimeStateFromObject(
    const Mm9DatRuntimeObject &object,
    GameplayRuntimeActorState &state)
{
    state = {};
    state.preciseX = object.position.x;
    state.preciseY = object.position.z;
    state.preciseZ = object.position.y;
    state.radius = clampedUint16FromFloat(object.radius);
    state.height = clampedUint16FromFloat(object.height);
    state.isInvisible = !object.visible;
    return true;
}

bool mm9DatHasLineOfSight(
    const Mm9DatWorldRuntime &runtime,
    const Mm9DatVec3 &source,
    const Mm9DatVec3 &target)
{
    const Mm9DatVec3 displacement = {
        target.x - source.x,
        target.y - source.y,
        target.z - source.z,
    };
    const float distance =
        std::sqrt(displacement.x * displacement.x + displacement.y * displacement.y + displacement.z * displacement.z);
    if (distance <= 0.0001f)
    {
        return true;
    }

    Mm9DatPickRay ray = {};
    ray.origin = source;
    ray.direction = {
        displacement.x / distance,
        displacement.y / distance,
        displacement.z / distance,
    };

    Mm9DatWorldPickOptions options = {};
    options.worldChannelMask = Mm9DatPhysicsQueryChannelPhysics | Mm9DatPhysicsQueryChannelVisible;
    options.maxDistance = distance;
    options.includeBackfaces = true;
    options.includeWorld = true;
    options.includeObjects = false;
    options.includeMechanisms = true;

    const std::optional<Mm9DatWorldPickHit> hit =
        pickMm9DatWorldRuntime(runtime, ray, options);
    return !hit || hit->distance > distance - 0.0001f;
}

std::optional<Mm9DatWorldPickHit> mm9DatPickHitFromGameplayHit(
    const GameplayWorldHit &hit,
    const Mm9DatMechanismRuntime &mechanismRuntime)
{
    if (!hit.hasHit || hit.kind != GameplayWorldHitKind::EventTarget || !hit.eventTarget)
    {
        return std::nullopt;
    }

    Mm9DatWorldPickHit datHit = {};
    datHit.point = mm9DatVecFromGameplayVec(hit.eventTarget->hitPoint);
    datHit.distance = hit.eventTarget->distance;

    if (hit.eventTarget->targetKind == GameplayWorldEventTargetKind::Mechanism
        && hit.eventTarget->targetIndex != GameplayInvalidWorldIndex
        && hit.eventTarget->targetIndex <= std::numeric_limits<uint32_t>::max())
    {
        datHit.kind = Mm9DatWorldPickHitKind::Mechanism;
        datHit.mechanismHandle = static_cast<uint32_t>(hit.eventTarget->targetIndex);
        const Mm9DatMechanismInstance *pMechanism =
            findMm9DatMechanismByHandle(mechanismRuntime, datHit.mechanismHandle);
        if (pMechanism != nullptr)
        {
            datHit.mechanismId = pMechanism->mechanismId;
            datHit.objectId = pMechanism->objectId;
            datHit.sourceModelIndex = pMechanism->sourceModelIndex;
            datHit.sourceModelName = pMechanism->sourceModelName;
        }
        return datHit;
    }

    if (hit.eventTarget->targetKind == GameplayWorldEventTargetKind::Object
        && hit.eventTarget->targetIndex != GameplayInvalidWorldIndex
        && hit.eventTarget->targetIndex <= std::numeric_limits<uint32_t>::max())
    {
        datHit.kind = Mm9DatWorldPickHitKind::Object;
        datHit.objectHandle = static_cast<uint32_t>(hit.eventTarget->targetIndex);
        if (hit.eventTarget->contextActionMetadata && hit.eventTarget->contextActionMetadata->mm9ObjectId)
        {
            datHit.objectId = *hit.eventTarget->contextActionMetadata->mm9ObjectId;
        }
        return datHit;
    }

    return std::nullopt;
}

Mm9DialogueOwnerContext mm9DatActivationOwnerContext(
    const Mm9DialoguePackage *pPackage,
    const std::string &mapId,
    const Mm9DatWorldUseResult &useResult,
    Mm9DialogueRuntime *pDialogueRuntime = nullptr)
{
    const int32_t sourceObjectIndex =
        useResult.activation.objectSourceObjectIndex >= 0
            ? useResult.activation.objectSourceObjectIndex
            : useResult.activation.mechanismSourceObjectIndex;

    Mm9DialogueOwnerContext owner = {};
    if (pPackage != nullptr && pDialogueRuntime != nullptr && sourceObjectIndex >= 0)
    {
        std::string ownerError;
        if (pDialogueRuntime->ownerContextForObject(mapId, sourceObjectIndex, owner, &ownerError))
        {
            return owner;
        }
    }

    (void)pPackage;
    owner.mapId = mapId;
    owner.objectIndex = sourceObjectIndex;
    owner.objectName = !useResult.activation.objectSourceName.empty()
        ? useResult.activation.objectSourceName
        : useResult.activation.mechanismSourceName;
    owner.scriptName = useResult.activation.objectScriptName;
    if (!useResult.activation.objectScriptParams.empty())
    {
        owner.scriptParams.push_back(useResult.activation.objectScriptParams);
    }
    return owner;
}

void appendMm9DatTriggerDispatchesToScriptState(
    Mm9ScriptRuntimeState &scriptState,
    const std::string &mapId,
    const Mm9DatWorldUseResult &useResult)
{
    if (!useResult.activated)
    {
        return;
    }

    const Mm9DialogueOwnerContext owner =
        mm9DatActivationOwnerContext(nullptr, mapId, useResult);

    for (const Mm9DatWorldTriggerDispatch &dispatch : useResult.triggerDispatches)
    {
        if (!dispatch.resolvedTarget || dispatch.targetHandle.empty() || dispatch.messageName.empty())
        {
            continue;
        }

        Mm9ScriptRuntimeTriggerDispatch scriptDispatch = {};
        scriptDispatch.scriptSource = owner.scriptName;
        scriptDispatch.mapId = owner.mapId;
        scriptDispatch.objectIndex = owner.objectIndex;
        scriptDispatch.targetHandle = dispatch.targetHandle;
        scriptDispatch.message = dispatch.messageName;
        scriptState.triggerDispatches.push_back(std::move(scriptDispatch));
    }
}

void processMm9DatTriggerDispatches(
    Mm9ScriptRuntimeState &scriptState,
    Party *pParty,
    const Mm9DialoguePackage *pPackage,
    const std::string &mapId,
    const Mm9DatWorldUseResult &useResult)
{
    if (pPackage == nullptr || pParty == nullptr)
    {
        appendMm9DatTriggerDispatchesToScriptState(scriptState, mapId, useResult);
        return;
    }

    Mm9DialogueRuntime dialogueRuntime(*pPackage, *pParty);
    Mm9ScriptRuntime scriptRuntime(*pPackage, dialogueRuntime);
    scriptRuntime.restoreState(scriptState);

    const Mm9DialogueOwnerContext owner =
        mm9DatActivationOwnerContext(pPackage, mapId, useResult, &dialogueRuntime);
    if (!owner.scriptName.empty() && owner.objectIndex >= 0)
    {
        std::optional<std::string> scriptError;
        scriptRuntime.runLabelForObject(
            owner.scriptName,
            "OnUse",
            owner.mapId,
            owner.objectIndex,
            owner.scriptParams,
            scriptError);
    }

    for (const Mm9DatWorldTriggerDispatch &dispatch : useResult.triggerDispatches)
    {
        if (!dispatch.resolvedTarget || dispatch.targetHandle.empty() || dispatch.messageName.empty())
        {
            continue;
        }

        scriptRuntime.dispatchTriggerFromObject(
            owner,
            owner.scriptName,
            dispatch.targetHandle,
            dispatch.messageName,
            0);
    }

    scriptState = scriptRuntime.state();
}

std::string mm9DatDebugFloat(float value)
{
    std::ostringstream out;
    out << std::fixed << std::setprecision(2) << value;
    return out.str();
}

std::string mm9DatDebugVec3(const Mm9DatVec3 &value)
{
    return mm9DatDebugFloat(value.x) + ","
        + mm9DatDebugFloat(value.y) + ","
        + mm9DatDebugFloat(value.z);
}

std::string mm9DatDebugBool(bool value)
{
    return value ? "yes" : "no";
}

std::string mm9DatDebugPickKind(Mm9DatWorldPickHitKind kind)
{
    switch (kind)
    {
    case Mm9DatWorldPickHitKind::World:
        return "world";
    case Mm9DatWorldPickHitKind::Object:
        return "object";
    case Mm9DatWorldPickHitKind::Mechanism:
        return "mechanism";
    case Mm9DatWorldPickHitKind::None:
    default:
        return "none";
    }
}
}

Mm9DatWorldGameplayRuntime::Mm9DatWorldGameplayRuntime(
    std::string mapFileName,
    Mm9DatRuntimeDevEntryResult entry,
    Party *pParty,
    EventRuntimeState *pEventRuntimeState,
    const std::optional<ScriptedEventProgram> *pGlobalEventProgram,
    Mm9ScriptRuntimeState *pMm9ScriptRuntimeState,
    const Mm9DialoguePackage *pMm9DialoguePackage,
    float gameMinutes)
    : m_mapFileName(std::move(mapFileName))
    , m_entry(std::move(entry))
    , m_pParty(pParty)
    , m_pEventRuntimeState(pEventRuntimeState)
    , m_pGlobalEventProgram(pGlobalEventProgram)
    , m_pMm9ScriptRuntimeState(pMm9ScriptRuntimeState)
    , m_pMm9DialoguePackage(pMm9DialoguePackage)
    , m_partyState(initializeMm9DatPartyRuntimeState(m_entry.startPose))
    , m_gameMinutes(std::max(0.0f, gameMinutes))
{
}

Mm9DatWorldGameplayRuntime::~Mm9DatWorldGameplayRuntime()
{
    destroyRenderResources();
}

bool Mm9DatWorldGameplayRuntime::initializeRenderResources()
{
    if (m_renderResourcesInitialized)
    {
        return true;
    }

    m_renderUploadPlan = buildMm9DatWorldRenderUploadPlan(m_entry.level.runtime.preparedRenderWorld);
    m_textureResources = createMm9DatWorldTextureResources(m_entry.level.runtime.textureBindings);
    applyMm9DatWorldTextureUvScale(m_renderUploadPlan, m_textureResources);
    m_renderSubmitPlan = buildMm9DatWorldRenderSubmitPlan(
        m_entry.level.runtime.renderSubmissionPlan,
        m_renderUploadPlan,
        m_textureResources);

    if (!createMm9DatWorldGeometryResources(m_renderUploadPlan, m_geometryResources))
    {
        destroyRenderResources();
        return false;
    }

    m_renderProgramHandle = loadMm9DatProgram("vs_editor_textured", "fs_editor_textured");
    m_textureSamplerHandle = bgfx::createUniform("s_texColor", bgfx::UniformType::Sampler);

    if (!bgfx::isValid(m_renderProgramHandle) || !bgfx::isValid(m_textureSamplerHandle))
    {
        destroyRenderResources();
        return false;
    }

    AnimatedModelRenderer::initializeResources(m_animatedModelRenderResources);
    initializeAnimatedObjectInstances();

    m_renderResourcesInitialized = true;
    m_dynamicRenderUploadDirty = false;
    return true;
}

void Mm9DatWorldGameplayRuntime::destroyRenderResources()
{
    for (Mm9DatAnimatedObjectTextureHandle &textureHandle : m_animatedObjectTextureHandles)
    {
        if (bgfx::isValid(textureHandle.textureHandle))
        {
            bgfx::destroy(textureHandle.textureHandle);
            textureHandle.textureHandle = BGFX_INVALID_HANDLE;
        }
    }
    m_animatedObjectTextureHandles.clear();
    m_animatedObjectTextureIndexByName.clear();
    m_animatedObjectInstances.clear();
    m_animatedObjectInstancesInitialized = false;
    AnimatedModelRenderer::shutdownResources(m_animatedModelRenderResources);

    destroyMm9DatWorldTextureResources(m_textureResources);
    destroyMm9DatWorldGeometryResources(m_geometryResources);

    if (bgfx::isValid(m_renderProgramHandle))
    {
        bgfx::destroy(m_renderProgramHandle);
        m_renderProgramHandle = BGFX_INVALID_HANDLE;
    }

    if (bgfx::isValid(m_textureSamplerHandle))
    {
        bgfx::destroy(m_textureSamplerHandle);
        m_textureSamplerHandle = BGFX_INVALID_HANDLE;
    }

    m_renderUploadPlan = {};
    m_renderSubmitPlan = {};
    m_lastRenderSubmitStats = {};
    m_renderResourcesInitialized = false;
    m_dynamicRenderUploadDirty = true;
}

void Mm9DatWorldGameplayRuntime::markDynamicRenderUploadDirty(
    const Mm9DatWorldRuntimeUpdateStats &stats)
{
    if (stats.mechanismRenderWorldUpdated
        || stats.mechanisms.updatedMechanismCount != 0
        || stats.mechanisms.completedMechanismCount != 0
        || stats.mechanisms.changedBoundsCount != 0)
    {
        m_dynamicRenderUploadDirty = true;
    }
}

void Mm9DatWorldGameplayRuntime::markDynamicRenderUploadDirty(
    const Mm9DatWorldUseResult &result)
{
    if (result.activated || result.mechanismCommand.stateChanged)
    {
        m_dynamicRenderUploadDirty = true;
    }
}

bool Mm9DatWorldGameplayRuntime::refreshDynamicRenderUploadIfNeeded()
{
    if (!m_dynamicRenderUploadDirty)
    {
        return true;
    }

    if (!refreshMm9DatWorldDynamicUploadVertices(
            m_entry.level.runtime.preparedRenderWorld,
            m_textureResources,
            m_renderUploadPlan))
    {
        return false;
    }

    if (!updateMm9DatWorldDynamicGeometryResources(m_renderUploadPlan, m_geometryResources))
    {
        return false;
    }

    m_renderSubmitPlan = buildMm9DatWorldRenderSubmitPlan(
        m_entry.level.runtime.renderSubmissionPlan,
        m_renderUploadPlan,
        m_textureResources);
    m_dynamicRenderUploadDirty = false;
    return true;
}

void Mm9DatWorldGameplayRuntime::initializeAnimatedObjectInstances()
{
    if (m_animatedObjectInstancesInitialized)
    {
        return;
    }

    m_animatedObjectInstancesInitialized = true;
    m_animatedObjectInstances.clear();

    if (m_entry.level.runtime.objectPresentationWorld.instances.empty())
    {
        return;
    }

    const std::filesystem::path worldRoot = m_entry.level.levelPath.parent_path().parent_path();
    const std::filesystem::path registryPath = worldRoot / "models" / "model_registry.yml";

    Mm9AnimatedModelResolver resolver = {};
    std::string resolverError;
    if (!resolver.loadRegistry(registryPath, resolverError))
    {
        if (!resolverError.empty())
        {
            std::cerr << resolverError << '\n';
        }
        return;
    }

    const Mm9DatObjectModelRenderPlan renderPlan = buildMm9DatObjectModelRenderPlan(
        m_entry.level.runtime.objectPresentationWorld,
        m_entry.level.scriptedObjects);
    std::unordered_map<std::string, std::shared_ptr<AnimatedModelAsset>> assetCache;
    for (const Mm9DatObjectModelRenderInstance &instance : renderPlan.instances)
    {
        std::vector<AnimatedModelDiagnostic> diagnostics;
        const std::optional<Mm9AnimatedActorResolvedSource> resolved =
            resolveMm9AnimatedActorVisualSource(instance.object, resolver, diagnostics);
        if (!resolved.has_value())
        {
            continue;
        }

        const std::string assetKey = resolved->resolution.modelAssetPath.generic_string();
        std::shared_ptr<AnimatedModelAsset> asset;
        const auto assetIterator = assetCache.find(assetKey);
        if (assetIterator != assetCache.end())
        {
            asset = assetIterator->second;
        }
        else
        {
            std::string assetError;
            std::optional<AnimatedModelAsset> loadedAsset =
                loadAnimatedModelAsset(resolved->resolution.modelAssetPath, assetError);
            if (!loadedAsset.has_value())
            {
                continue;
            }

            std::optional<Mm9AnimatedModelSidecar> sidecar =
                loadMm9AnimatedModelSidecar(resolved->resolution.modelSidecarPath, assetError);
            if (!sidecar.has_value())
            {
                continue;
            }

            mergeMm9AnimatedModelSidecar(*sidecar, *loadedAsset);
            if (loadedAsset->hasErrors())
            {
                continue;
            }

            asset = std::make_shared<AnimatedModelAsset>(std::move(*loadedAsset));
            assetCache.emplace(assetKey, asset);
        }

        Mm9AnimatedActorVisual visual = {};
        initializeMm9AnimatedActorVisual(
            resolved->source,
            resolved->resolution,
            *asset,
            visual);
        if (visual.renderPrepCache.drawItems.empty() || !visual.worldBounds.valid)
        {
            continue;
        }

        m_animatedObjectInstances.push_back(Mm9DatAnimatedObjectInstance{
            .visual = std::move(visual),
            .asset = asset,
        });
    }
}

void Mm9DatWorldGameplayRuntime::updateAnimatedObjectInstances(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    for (Mm9DatAnimatedObjectInstance &instance : m_animatedObjectInstances)
    {
        if (instance.asset)
        {
            updateMm9AnimatedActorVisual(instance.visual, *instance.asset, deltaSeconds);
        }
    }
}

const Mm9DatWorldGameplayRuntime::Mm9DatAnimatedObjectTextureHandle *
Mm9DatWorldGameplayRuntime::ensureAnimatedObjectTexture(
    const std::string &textureName)
{
    if (textureName.empty())
    {
        return nullptr;
    }

    const std::string normalizedTextureName = normalizeMm9DatSceneTextureKey(textureName);
    const auto cachedTexture = m_animatedObjectTextureIndexByName.find(normalizedTextureName);
    if (cachedTexture != m_animatedObjectTextureIndexByName.end()
        && cachedTexture->second < m_animatedObjectTextureHandles.size())
    {
        return &m_animatedObjectTextureHandles[cachedTexture->second];
    }

    Mm9DatAnimatedObjectTextureHandle textureHandle = {};
    textureHandle.textureName = normalizedTextureName;

    const std::optional<size_t> catalogEntryIndex =
        findMm9DatSceneTextureCatalogEntry(m_entry.level.runtime.textureCatalog, textureName);
    if (catalogEntryIndex.has_value() && *catalogEntryIndex < m_entry.level.runtime.textureCatalog.entries.size())
    {
        const Mm9DatRuntimeTextureCatalogEntry &catalogEntry =
            m_entry.level.runtime.textureCatalog.entries[*catalogEntryIndex];
        std::string errorMessage;
        const std::optional<Mm9DtxTexture> texture =
            loadMm9DtxTexture(catalogEntry.physicalPath, errorMessage);
        if (texture.has_value()
            && texture->width <= std::numeric_limits<uint16_t>::max()
            && texture->height <= std::numeric_limits<uint16_t>::max()
            && texture->pixelsBgra.size() <= std::numeric_limits<uint32_t>::max())
        {
            textureHandle.width = static_cast<int>(texture->width);
            textureHandle.height = static_cast<int>(texture->height);
            textureHandle.textureHandle = createBgraTexture2D(
                static_cast<uint16_t>(texture->width),
                static_cast<uint16_t>(texture->height),
                texture->pixelsBgra.data(),
                static_cast<uint32_t>(texture->pixelsBgra.size()),
                TextureFilterProfile::BModel);
        }
    }

    const size_t textureIndex = m_animatedObjectTextureHandles.size();
    m_animatedObjectTextureIndexByName[normalizedTextureName] = textureIndex;
    m_animatedObjectTextureHandles.push_back(textureHandle);
    return &m_animatedObjectTextureHandles.back();
}

void Mm9DatWorldGameplayRuntime::submitAnimatedObjectInstances()
{
    if (m_animatedObjectInstances.empty() || !m_animatedModelRenderResources.isReady())
    {
        return;
    }

    AnimatedModelLightParameters lightParameters = {};
    for (const Mm9DatAnimatedObjectInstance &instance : m_animatedObjectInstances)
    {
        if (!instance.visual.visible)
        {
            continue;
        }

        for (const AnimatedModelDrawItem &drawItem : instance.visual.renderPrepCache.drawItems)
        {
            const Mm9DatAnimatedObjectTextureHandle *pTexture =
                ensureAnimatedObjectTexture(drawItem.texture);
            if (pTexture == nullptr || !bgfx::isValid(pTexture->textureHandle))
            {
                continue;
            }

            AnimatedModelRenderer::submitDrawItem(
                m_animatedModelRenderResources,
                Mm9DatWorldViewId,
                drawItem,
                instance.visual.modelToWorld,
                pTexture->textureHandle,
                nullptr,
                &lightParameters);
        }
    }
}

const std::string &Mm9DatWorldGameplayRuntime::mapName() const
{
    return m_mapFileName;
}

std::string Mm9DatWorldGameplayRuntime::currentMapWorldId() const
{
    return "mm9";
}

bool Mm9DatWorldGameplayRuntime::isIndoorMap() const
{
    return false;
}

float Mm9DatWorldGameplayRuntime::gameMinutes() const
{
    return m_gameMinutes;
}

int Mm9DatWorldGameplayRuntime::currentHour() const
{
    const int hour = static_cast<int>(std::floor(std::max(0.0f, m_gameMinutes) / 60.0f));
    return ((hour % 24) + 24) % 24;
}

const std::vector<uint8_t> *Mm9DatWorldGameplayRuntime::journalMapFullyRevealedCells() const
{
    return nullptr;
}

const std::vector<uint8_t> *Mm9DatWorldGameplayRuntime::journalMapPartiallyRevealedCells() const
{
    return nullptr;
}

int Mm9DatWorldGameplayRuntime::restFoodRequired() const
{
    return 0;
}

void Mm9DatWorldGameplayRuntime::advanceGameMinutes(float minutes)
{
    m_gameMinutes = std::max(0.0f, m_gameMinutes + minutes);
}

int Mm9DatWorldGameplayRuntime::currentLocationReputation() const
{
    return m_currentLocationReputation;
}

void Mm9DatWorldGameplayRuntime::setCurrentLocationReputation(int reputation)
{
    m_currentLocationReputation = reputation;
}

Party *Mm9DatWorldGameplayRuntime::party()
{
    return m_pParty;
}

const Party *Mm9DatWorldGameplayRuntime::party() const
{
    return m_pParty;
}

float Mm9DatWorldGameplayRuntime::partyX() const
{
    return m_partyState.position.x;
}

float Mm9DatWorldGameplayRuntime::partyY() const
{
    return m_partyState.position.z;
}

float Mm9DatWorldGameplayRuntime::partyFootZ() const
{
    return m_partyState.position.y;
}

float Mm9DatWorldGameplayRuntime::gameplayCameraYawRadians() const
{
    return m_partyState.yawRadians;
}

float Mm9DatWorldGameplayRuntime::gameplayCameraPitchRadians() const
{
    return m_partyState.pitchRadians;
}

void Mm9DatWorldGameplayRuntime::syncSpellMovementStatesFromPartyBuffs()
{
}

void Mm9DatWorldGameplayRuntime::requestPartyJump(float verticalVelocity, float lift)
{
    const float jumpVelocity = verticalVelocity > 0.0f ? verticalVelocity : 256.0f * std::max(0.1f, lift);
    m_partyState.verticalVelocityLtPerSecond =
        std::max(m_partyState.verticalVelocityLtPerSecond, jumpVelocity);
    m_partyState.onGround = false;
    m_partyState.mechanismSupportHandle.reset();
    m_partyState.mechanismSupportProgress = 0.0f;
}

void Mm9DatWorldGameplayRuntime::setAlwaysRunEnabled(bool enabled)
{
    m_alwaysRun = enabled;
}

void Mm9DatWorldGameplayRuntime::updateWorldMovement(
    const GameplayInputFrame &input,
    float deltaSeconds,
    bool allowWorldInput)
{
    if (!allowWorldInput)
    {
        return;
    }

    if (input.relativeMouseX != 0.0f || input.relativeMouseY != 0.0f)
    {
        m_partyState.yawRadians -= input.relativeMouseX * Mm9DatMouseRotateSpeed;
        m_partyState.pitchRadians -= input.relativeMouseY * Mm9DatMouseRotateSpeed;
    }

    if (!input.modernControls && input.action(KeyboardAction::Left).held)
    {
        m_partyState.yawRadians += Mm9DatKeyboardYawSpeed * deltaSeconds;
    }

    if (!input.modernControls && input.action(KeyboardAction::Right).held)
    {
        m_partyState.yawRadians -= Mm9DatKeyboardYawSpeed * deltaSeconds;
    }

    if (input.action(KeyboardAction::LookUp).held)
    {
        m_partyState.pitchRadians += Mm9DatKeyboardPitchSpeed * deltaSeconds;
    }

    if (input.action(KeyboardAction::LookDown).held)
    {
        m_partyState.pitchRadians -= Mm9DatKeyboardPitchSpeed * deltaSeconds;
    }

    if (input.action(KeyboardAction::CenterView).held)
    {
        m_partyState.pitchRadians = 0.0f;
    }

    if (m_partyState.yawRadians > Pi)
    {
        m_partyState.yawRadians -= Pi * 2.0f;
    }
    else if (m_partyState.yawRadians < -Pi)
    {
        m_partyState.yawRadians += Pi * 2.0f;
    }

    m_partyState.pitchRadians =
        std::clamp(m_partyState.pitchRadians, -Mm9DatMaxPitchRadians, Mm9DatMaxPitchRadians);

    Mm9DatPartyRuntimeMoveInput moveInput = {};
    moveInput.forward = axisValue(
        input.action(KeyboardAction::Forward).held,
        input.action(KeyboardAction::Backward).held);
    if (input.modernControls)
    {
        moveInput.strafe = axisValue(
            input.action(KeyboardAction::Right).held,
            input.action(KeyboardAction::Left).held);
    }
    moveInput.vertical = axisValue(
        input.action(KeyboardAction::FlyUp).held,
        input.action(KeyboardAction::FlyDown).held);
    moveInput.deltaSeconds = deltaSeconds;
    moveInput.running = m_alwaysRun || input.action(KeyboardAction::AlwaysRun).held;

    m_lastMoveResult =
        moveMm9DatPartyRuntime(m_entry.level.runtime, m_partyState, moveInput);
    markDynamicRenderUploadDirty(m_lastMoveResult->worldUpdate);
    if (m_lastMoveResult->movement.mechanismContactCommand.stateChanged)
    {
        m_dynamicRenderUploadDirty = true;
    }
    m_worldAdvancedSinceLastUpdateWorld = true;

    if (input.action(KeyboardAction::Use).pressed || input.action(KeyboardAction::Trigger).pressed)
    {
        m_lastUseResult = useMm9DatPartyRuntime(m_entry.level.runtime, m_partyState);
        markDynamicRenderUploadDirty(*m_lastUseResult);
    }
}

void Mm9DatWorldGameplayRuntime::updateActorAi(float deltaSeconds)
{
    (void)deltaSeconds;
}

void Mm9DatWorldGameplayRuntime::updateWorld(float deltaSeconds)
{
    updateAnimatedObjectInstances(deltaSeconds);

    if (m_worldAdvancedSinceLastUpdateWorld)
    {
        m_worldAdvancedSinceLastUpdateWorld = false;
        return;
    }

    const Mm9DatWorldRuntimeUpdateStats stats =
        updateMm9DatWorldRuntime(m_entry.level.runtime, deltaSeconds);
    markDynamicRenderUploadDirty(stats);
}

void Mm9DatWorldGameplayRuntime::renderWorld(
    int width,
    int height,
    const GameplayInputFrame &input,
    float deltaSeconds)
{
    (void)input;
    (void)deltaSeconds;

    const uint16_t viewWidth = static_cast<uint16_t>(std::max(1, std::min(width, 65535)));
    const uint16_t viewHeight = static_cast<uint16_t>(std::max(1, std::min(height, 65535)));
    bgfx::setViewRect(Mm9DatWorldViewId, 0, 0, viewWidth, viewHeight);
    bgfx::setViewMode(Mm9DatWorldViewId, bgfx::ViewMode::Sequential);
    bgfx::setViewClear(Mm9DatWorldViewId, BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH, 0x000000ffu, 1.0f, 0);

    const float cosPitch = std::cos(m_partyState.pitchRadians);
    const float sinPitch = std::sin(m_partyState.pitchRadians);
    const float cosYaw = std::cos(m_partyState.yawRadians);
    const float sinYaw = std::sin(m_partyState.yawRadians);
    const bx::Vec3 eye = {
        m_partyState.position.x,
        m_partyState.position.z,
        m_partyState.position.y + Mm9DatCameraEyeHeight
    };
    const bx::Vec3 viewForward = {cosYaw * cosPitch, sinYaw * cosPitch, sinPitch};
    const bx::Vec3 at = {eye.x + viewForward.x, eye.y + viewForward.y, eye.z + viewForward.z};
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};

    float viewMatrix[16] = {};
    float projectionMatrix[16] = {};
    bx::mtxLookAt(viewMatrix, eye, at, up, bx::Handedness::Right);
    bx::mtxProj(
        projectionMatrix,
        Mm9DatCameraVerticalFovDegrees,
        static_cast<float>(viewWidth) / static_cast<float>(viewHeight),
        0.1f,
        50000.0f,
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right);
    bgfx::setViewTransform(Mm9DatWorldViewId, viewMatrix, projectionMatrix);
    bgfx::touch(Mm9DatWorldViewId);

    if (!initializeRenderResources())
    {
        return;
    }

    if (!refreshDynamicRenderUploadIfNeeded())
    {
        return;
    }

    m_lastRenderSubmitStats = submitMm9DatWorldRenderSubmitPlan(
        m_renderSubmitPlan,
        m_geometryResources,
        m_textureResources,
        Mm9DatWorldViewId,
        m_renderProgramHandle,
        m_textureSamplerHandle);
    submitAnimatedObjectInstances();
}

GameplayWorldUiRenderState Mm9DatWorldGameplayRuntime::gameplayUiRenderState(int width, int height) const
{
    (void)width;
    (void)height;
    GameplayWorldUiRenderState state = {};
    state.canRenderHudOverlays = false;
    state.renderGameplayHud = false;
    state.renderActorInspectOverlay = false;
    state.renderDebugFallbacks = false;
    return state;
}

bool Mm9DatWorldGameplayRuntime::requestTravelAutosave()
{
    return false;
}

void Mm9DatWorldGameplayRuntime::cancelPendingMapTransition()
{
}

bool Mm9DatWorldGameplayRuntime::executeNpcTopicEvent(
    uint16_t eventId,
    size_t &previousMessageCount,
    std::optional<uint8_t> continueStep)
{
    (void)eventId;
    (void)previousMessageCount;
    (void)continueStep;
    return false;
}

bool Mm9DatWorldGameplayRuntime::executeMapEvent(
    uint16_t eventId,
    size_t &previousMessageCount,
    std::optional<uint8_t> continueStep)
{
    (void)eventId;
    (void)previousMessageCount;
    (void)continueStep;
    return false;
}

const std::optional<ScriptedEventProgram> *Mm9DatWorldGameplayRuntime::globalEventProgram() const
{
    return m_pGlobalEventProgram;
}

EventRuntimeState *Mm9DatWorldGameplayRuntime::eventRuntimeState()
{
    return m_pEventRuntimeState;
}

const EventRuntimeState *Mm9DatWorldGameplayRuntime::eventRuntimeState() const
{
    return m_pEventRuntimeState;
}

bool Mm9DatWorldGameplayRuntime::castEventSpell(
    uint32_t spellId,
    uint32_t skillLevel,
    uint32_t skillMastery,
    int32_t fromX,
    int32_t fromY,
    int32_t fromZ,
    int32_t toX,
    int32_t toY,
    int32_t toZ)
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

size_t Mm9DatWorldGameplayRuntime::mapActorCount() const
{
    return m_entry.level.runtime.objectRegistry.actorObjectIndices.size();
}

bool Mm9DatWorldGameplayRuntime::actorRuntimeState(size_t actorIndex, GameplayRuntimeActorState &state) const
{
    const Mm9DatObjectRegistry &registry = m_entry.level.runtime.objectRegistry;
    if (actorIndex >= registry.actorObjectIndices.size())
    {
        return false;
    }

    const size_t objectIndex = registry.actorObjectIndices[actorIndex];
    if (objectIndex >= registry.objects.size())
    {
        return false;
    }

    return mm9DatActorRuntimeStateFromObject(registry.objects[objectIndex], state);
}

bool Mm9DatWorldGameplayRuntime::actorInspectState(
    size_t actorIndex,
    uint32_t animationTicks,
    GameplayActorInspectState &state) const
{
    (void)animationTicks;
    const Mm9DatObjectRegistry &registry = m_entry.level.runtime.objectRegistry;
    if (actorIndex >= registry.actorObjectIndices.size())
    {
        return false;
    }

    const size_t objectIndex = registry.actorObjectIndices[actorIndex];
    if (objectIndex >= registry.objects.size())
    {
        return false;
    }

    const Mm9DatRuntimeObject &object = registry.objects[objectIndex];
    state = {};
    state.displayName =
        !object.sourceName.empty()
            ? object.sourceName
            : (!object.sourceClass.empty() ? object.sourceClass : object.objectId);
    state.previewTextureName = object.visualId;
    state.currentHp = 1;
    state.maxHp = 1;
    state.isDead = false;
    return true;
}

std::optional<GameplayCombatActorInfo> Mm9DatWorldGameplayRuntime::combatActorInfoById(uint32_t actorId) const
{
    (void)actorId;
    return std::nullopt;
}

bool Mm9DatWorldGameplayRuntime::castPartySpellProjectile(const GameplayPartySpellProjectileRequest &request)
{
    (void)request;
    return false;
}

bool Mm9DatWorldGameplayRuntime::applyPartySpellToActor(
    size_t actorIndex,
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    int damage,
    float partyX,
    float partyY,
    float partyZ,
    uint32_t sourcePartyMemberIndex)
{
    (void)actorIndex;
    (void)spellId;
    (void)skillLevel;
    (void)skillMastery;
    (void)damage;
    (void)partyX;
    (void)partyY;
    (void)partyZ;
    (void)sourcePartyMemberIndex;
    return false;
}

std::vector<size_t> Mm9DatWorldGameplayRuntime::collectMapActorIndicesWithinRadius(
    float centerX,
    float centerY,
    float centerZ,
    float radius,
    bool requireLineOfSight,
    float sourceX,
    float sourceY,
    float sourceZ) const
{
    std::vector<size_t> result;
    if (radius <= 0.0f)
    {
        return result;
    }

    const Mm9DatObjectRegistry &registry = m_entry.level.runtime.objectRegistry;
    const Mm9DatVec3 center = {centerX, centerZ, centerY};
    const Mm9DatVec3 source = {sourceX, sourceZ, sourceY};
    const std::vector<size_t> candidateObjectIndices =
        collectMm9DatActorObjectIndicesWithinRadius(registry, center, radius);

    for (size_t objectIndex : candidateObjectIndices)
    {
        if (objectIndex >= registry.objects.size()
            || objectIndex >= registry.actorIndexByObjectIndex.size()
            || registry.actorIndexByObjectIndex[objectIndex] >= registry.actorObjectIndices.size())
        {
            continue;
        }

        const size_t actorIndex = registry.actorIndexByObjectIndex[objectIndex];
        const Mm9DatRuntimeObject &object = registry.objects[objectIndex];
        if (!object.visible)
        {
            continue;
        }

        const Mm9DatVec3 target = {
            object.position.x,
            object.position.y + std::max(24.0f, object.height * 0.7f),
            object.position.z,
        };
        const float deltaX = target.x - center.x;
        const float deltaY = target.y - center.y;
        const float deltaZ = target.z - center.z;
        const float distance =
            std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
        const float edgeDistance = std::max(0.0f, distance - object.radius);
        if (edgeDistance > radius)
        {
            continue;
        }

        if (requireLineOfSight && !mm9DatHasLineOfSight(m_entry.level.runtime, source, target))
        {
            continue;
        }

        result.push_back(actorIndex);
    }

    std::sort(result.begin(), result.end());
    return result;
}

bool Mm9DatWorldGameplayRuntime::spawnPartyFireSpikeTrap(
    uint32_t casterMemberIndex,
    uint32_t spellId,
    uint32_t skillLevel,
    uint32_t skillMastery,
    float x,
    float y,
    float z)
{
    (void)casterMemberIndex;
    (void)spellId;
    (void)skillLevel;
    (void)skillMastery;
    (void)x;
    (void)y;
    (void)z;
    return false;
}

bool Mm9DatWorldGameplayRuntime::summonFriendlyMonsterById(
    int16_t monsterId,
    uint32_t count,
    float durationSeconds,
    float x,
    float y,
    float z)
{
    (void)monsterId;
    (void)count;
    (void)durationSeconds;
    (void)x;
    (void)y;
    (void)z;
    return false;
}

bool Mm9DatWorldGameplayRuntime::teleportPartyTo(float x, float y, float z, int32_t directionDegrees)
{
    const Mm9DatVec3 requestedPosition = {x, z, y};
    const float yawRadians = static_cast<float>(directionDegrees) * RadiansPerDegree;
    teleportMm9DatPartyRuntime(m_entry.level.runtime, m_partyState, requestedPosition, yawRadians);
    return true;
}

bool Mm9DatWorldGameplayRuntime::tryStartArmageddon(
    size_t casterMemberIndex,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    std::string &failureText)
{
    (void)casterMemberIndex;
    (void)skillLevel;
    (void)skillMastery;
    failureText = "Armageddon is not implemented for native MM9 DAT runtime.";
    return false;
}

bool Mm9DatWorldGameplayRuntime::canActivateWorldHit(
    const GameplayWorldHit &hit,
    GameplayInteractionMethod interactionMethod) const
{
    (void)interactionMethod;
    if (!hit.hasHit || hit.kind != GameplayWorldHitKind::EventTarget || !hit.eventTarget)
    {
        return false;
    }

    if (hit.eventTarget->targetKind == GameplayWorldEventTargetKind::Mechanism
        && hit.eventTarget->targetIndex != GameplayInvalidWorldIndex
        && hit.eventTarget->targetIndex <= std::numeric_limits<uint32_t>::max())
    {
        const uint32_t handle = static_cast<uint32_t>(hit.eventTarget->targetIndex);
        return findMm9DatMechanismByHandle(m_entry.level.runtime.mechanismRuntime, handle) != nullptr;
    }

    if (hit.eventTarget->targetKind == GameplayWorldEventTargetKind::Object
        && hit.eventTarget->contextActionMetadata
        && hit.eventTarget->contextActionMetadata->mm9ObjectId)
    {
        return findMm9DatMechanismByObjectId(
            m_entry.level.runtime.mechanismRuntime,
            *hit.eventTarget->contextActionMetadata->mm9ObjectId) != nullptr;
    }

    return false;
}

bool Mm9DatWorldGameplayRuntime::activateWorldHit(const GameplayWorldHit &hit)
{
    if (!canActivateWorldHit(hit, GameplayInteractionMethod::Keyboard))
    {
        m_lastUseResult = std::nullopt;
        return false;
    }

    const std::optional<Mm9DatWorldPickHit> datHit =
        mm9DatPickHitFromGameplayHit(hit, m_entry.level.runtime.mechanismRuntime);
    if (!datHit)
    {
        m_lastUseResult = std::nullopt;
        return false;
    }

    m_lastUseResult = useMm9DatWorldPickedHitRuntime(
        m_entry.level.runtime,
        *datHit,
        Mm9DatMechanismCommand::Toggle);
    if (m_pMm9ScriptRuntimeState != nullptr)
    {
        processMm9DatTriggerDispatches(
            *m_pMm9ScriptRuntimeState,
            m_pParty,
            m_pMm9DialoguePackage,
            m_entry.level.metadata.mapId,
            *m_lastUseResult);
    }
    markDynamicRenderUploadDirty(*m_lastUseResult);
    return m_lastUseResult->activated;
}

bool Mm9DatWorldGameplayRuntime::canActivateTelekinesisTarget(const GameplayWorldHit &hit) const
{
    (void)hit;
    return false;
}

bool Mm9DatWorldGameplayRuntime::activateTelekinesisTarget(const GameplayWorldHit &hit)
{
    (void)hit;
    return false;
}

std::optional<GameplayPartyAttackActorFacts> Mm9DatWorldGameplayRuntime::partyAttackActorFacts(
    size_t actorIndex,
    bool visibleForFallback) const
{
    (void)actorIndex;
    (void)visibleForFallback;
    return std::nullopt;
}

std::vector<GameplayPartyAttackActorFacts> Mm9DatWorldGameplayRuntime::collectPartyAttackFallbackActors(
    const GameplayPartyAttackFallbackQuery &query) const
{
    (void)query;
    return {};
}

bool Mm9DatWorldGameplayRuntime::applyPartyAttackMeleeDamage(
    size_t actorIndex,
    int damage,
    const GameplayWorldPoint &source)
{
    (void)actorIndex;
    (void)damage;
    (void)source;
    return false;
}

bool Mm9DatWorldGameplayRuntime::spawnPartyAttackProjectile(const GameplayPartyAttackProjectileRequest &request)
{
    (void)request;
    return false;
}

bool Mm9DatWorldGameplayRuntime::castPartyAttackSpell(const GameplayPartyAttackSpellRequest &request)
{
    (void)request;
    return false;
}

void Mm9DatWorldGameplayRuntime::recordPartyAttackWorldResult(
    std::optional<size_t> actorIndex,
    bool attacked,
    bool actionPerformed)
{
    (void)actorIndex;
    (void)attacked;
    (void)actionPerformed;
}

bool Mm9DatWorldGameplayRuntime::worldInteractionReady() const
{
    return true;
}

bool Mm9DatWorldGameplayRuntime::worldInspectModeActive() const
{
    return false;
}

GameplayWorldPickRequest Mm9DatWorldGameplayRuntime::buildWorldPickRequest(
    const GameplayWorldPickRequestInput &input) const
{
    GameplayWorldPickRequest request = {};
    request.screenX = input.screenX;
    request.screenY = input.screenY;
    request.viewWidth = input.screenWidth;
    request.viewHeight = input.screenHeight;

    if (input.includeRay)
    {
        const Mm9DatPickRay ray = mm9DatPartyPickRay(m_partyState);
        request.rayOrigin = gameplayVecFromMm9DatVec(ray.origin);
        request.rayDirection = gameplayVecFromMm9DatVec(ray.direction);
        request.eye = request.rayOrigin;
        request.hasRay = true;
    }

    return request;
}

std::optional<GameplayHeldItemDropRequest> Mm9DatWorldGameplayRuntime::buildHeldItemDropRequest() const
{
    return std::nullopt;
}

GameplayPartyAttackFrameInput Mm9DatWorldGameplayRuntime::buildPartyAttackFrameInput(
    const GameplayWorldPickRequest &pickRequest) const
{
    (void)pickRequest;
    return {};
}

std::optional<size_t> Mm9DatWorldGameplayRuntime::spellActionHoveredActorIndex() const
{
    return std::nullopt;
}

std::optional<size_t> Mm9DatWorldGameplayRuntime::spellActionClosestVisibleHostileActorIndex() const
{
    return std::nullopt;
}

std::optional<bx::Vec3> Mm9DatWorldGameplayRuntime::spellActionActorTargetPoint(size_t actorIndex) const
{
    (void)actorIndex;
    return std::nullopt;
}

std::optional<bx::Vec3> Mm9DatWorldGameplayRuntime::spellActionGroundTargetPoint(float screenX, float screenY) const
{
    (void)screenX;
    (void)screenY;
    return std::nullopt;
}

GameplayPendingSpellWorldTargetFacts Mm9DatWorldGameplayRuntime::pickPendingSpellWorldTarget(
    const GameplayWorldPickRequest &request)
{
    (void)request;
    return {};
}

GameplayWorldHit Mm9DatWorldGameplayRuntime::pickKeyboardInteractionTarget(const GameplayWorldPickRequest &request)
{
    return pickMm9DatGameplayWorldHit(m_entry.level.runtime, m_partyState, request);
}

GameplayWorldHit Mm9DatWorldGameplayRuntime::pickHeldItemWorldTarget(const GameplayWorldPickRequest &request)
{
    return pickMm9DatGameplayWorldHit(m_entry.level.runtime, m_partyState, request);
}

GameplayWorldHit Mm9DatWorldGameplayRuntime::pickMouseInteractionTarget(const GameplayWorldPickRequest &request)
{
    return pickMm9DatGameplayWorldHit(m_entry.level.runtime, m_partyState, request);
}

GameplayWorldHoverCacheState Mm9DatWorldGameplayRuntime::worldHoverCacheState() const
{
    return m_hoverCacheState;
}

GameplayHoverStatusPayload Mm9DatWorldGameplayRuntime::refreshWorldHover(const GameplayWorldHoverRequest &request)
{
    m_cachedHoverPayload = {};
    m_cachedHoverPayload.worldHit =
        pickMm9DatGameplayWorldHit(m_entry.level.runtime, m_partyState, request.primaryPickRequest);

    if (!m_cachedHoverPayload.worldHit.hasHit && request.secondaryPickRequest)
    {
        m_cachedHoverPayload.worldHit =
            pickMm9DatGameplayWorldHit(m_entry.level.runtime, m_partyState, *request.secondaryPickRequest);
    }

    if (m_cachedHoverPayload.worldHit.eventTarget)
    {
        const GameplayEventTargetHit &eventTarget = *m_cachedHoverPayload.worldHit.eventTarget;
        if (eventTarget.contextActionMetadata
            && eventTarget.contextActionMetadata->targetName
            && !eventTarget.contextActionMetadata->targetName->empty())
        {
            m_cachedHoverPayload.eventTargetStatusText = *eventTarget.contextActionMetadata->targetName;
        }
        else if (!eventTarget.name.empty())
        {
            m_cachedHoverPayload.eventTargetStatusText = eventTarget.name;
        }
    }

    m_hoverCacheState.hasCachedHover = m_cachedHoverPayload.worldHit.hasHit;
    m_hoverCacheState.lastUpdateNanoseconds = request.updateTickNanoseconds;
    return m_cachedHoverPayload;
}

GameplayHoverStatusPayload Mm9DatWorldGameplayRuntime::readCachedWorldHover()
{
    return m_cachedHoverPayload;
}

void Mm9DatWorldGameplayRuntime::clearWorldHover()
{
    m_cachedHoverPayload = {};
    m_hoverCacheState = {};
}

bool Mm9DatWorldGameplayRuntime::canUseHeldItemOnWorld(const GameplayWorldHit &hit) const
{
    (void)hit;
    return false;
}

bool Mm9DatWorldGameplayRuntime::useHeldItemOnWorld(const GameplayWorldHit &hit)
{
    (void)hit;
    return false;
}

void Mm9DatWorldGameplayRuntime::applyPendingSpellCastWorldEffects(const PartySpellCastResult &castResult)
{
    (void)castResult;
}

bool Mm9DatWorldGameplayRuntime::dropHeldItemToWorld(const GameplayHeldItemDropRequest &request)
{
    (void)request;
    return false;
}

bool Mm9DatWorldGameplayRuntime::tryGetGameplayMinimapState(GameplayMinimapState &state) const
{
    (void)state;
    return false;
}

void Mm9DatWorldGameplayRuntime::collectGameplayMinimapLines(std::vector<GameplayMinimapLineState> &lines)
{
    lines.clear();
}

void Mm9DatWorldGameplayRuntime::collectGameplayMinimapMarkers(
    std::vector<GameplayMinimapMarkerState> &markers) const
{
    markers.clear();
}

GameplayChestViewState *Mm9DatWorldGameplayRuntime::activeChestView()
{
    return nullptr;
}

const GameplayChestViewState *Mm9DatWorldGameplayRuntime::activeChestView() const
{
    return nullptr;
}

void Mm9DatWorldGameplayRuntime::commitActiveChestView()
{
}

bool Mm9DatWorldGameplayRuntime::takeActiveChestItem(size_t itemIndex, GameplayChestItemState &item)
{
    (void)itemIndex;
    (void)item;
    return false;
}

bool Mm9DatWorldGameplayRuntime::takeActiveChestItemAt(uint8_t gridX, uint8_t gridY, GameplayChestItemState &item)
{
    (void)gridX;
    (void)gridY;
    (void)item;
    return false;
}

bool Mm9DatWorldGameplayRuntime::tryPlaceActiveChestItemAt(
    const GameplayChestItemState &item,
    uint8_t gridX,
    uint8_t gridY)
{
    (void)item;
    (void)gridX;
    (void)gridY;
    return false;
}

void Mm9DatWorldGameplayRuntime::closeActiveChestView()
{
}

GameplayCorpseViewState *Mm9DatWorldGameplayRuntime::activeCorpseView()
{
    return nullptr;
}

const GameplayCorpseViewState *Mm9DatWorldGameplayRuntime::activeCorpseView() const
{
    return nullptr;
}

void Mm9DatWorldGameplayRuntime::commitActiveCorpseView()
{
}

bool Mm9DatWorldGameplayRuntime::takeActiveCorpseItem(size_t itemIndex, GameplayChestItemState &item)
{
    (void)itemIndex;
    (void)item;
    return false;
}

void Mm9DatWorldGameplayRuntime::closeActiveCorpseView()
{
}

Mm9DatWorldRuntime &Mm9DatWorldGameplayRuntime::datRuntime()
{
    return m_entry.level.runtime;
}

const Mm9DatWorldRuntime &Mm9DatWorldGameplayRuntime::datRuntime() const
{
    return m_entry.level.runtime;
}

Mm9DatPartyRuntimeState &Mm9DatWorldGameplayRuntime::partyRuntimeState()
{
    return m_partyState;
}

const Mm9DatPartyRuntimeState &Mm9DatWorldGameplayRuntime::partyRuntimeState() const
{
    return m_partyState;
}

const std::optional<Mm9DatPartyRuntimeMoveResult> &Mm9DatWorldGameplayRuntime::lastMoveResult() const
{
    return m_lastMoveResult;
}

const std::optional<Mm9DatWorldUseResult> &Mm9DatWorldGameplayRuntime::lastUseResult() const
{
    return m_lastUseResult;
}

std::vector<std::string> Mm9DatWorldGameplayRuntime::debugStatusLines() const
{
    const Mm9DatWorldRuntime &runtime = m_entry.level.runtime;
    const Mm9DatWorldRuntimeStats &stats = runtime.stats;

    std::vector<std::string> lines;
    lines.reserve(12);
    lines.push_back(
        "mm9.dat map=" + stats.mapId
        + " file=" + m_mapFileName
        + " backend=" + m_entry.level.metadata.worldBackend);
    lines.push_back(
        "inputs level_yml+dat sidecars=no diagnostics="
        + std::to_string(runtime.diagnostics.size()));
    lines.push_back(
        "party dat_pos=" + mm9DatDebugVec3(m_partyState.position)
        + " yaw=" + mm9DatDebugFloat(m_partyState.yawRadians)
        + " pitch=" + mm9DatDebugFloat(m_partyState.pitchRadians)
        + " ground=" + mm9DatDebugBool(m_partyState.onGround)
        + " vertical_vel=" + mm9DatDebugFloat(m_partyState.verticalVelocityLtPerSecond));
    lines.push_back(
        "render tris=" + std::to_string(stats.renderTriangleCount)
        + " water_visible=" + std::to_string(stats.visibleWaterTriangleCount)
        + " water_volume=" + std::to_string(stats.waterVolumeTriangleCount)
        + " sections=" + std::to_string(stats.preparedRenderSectionCount)
        + " draws=" + std::to_string(stats.renderDrawCallCount)
        + " submitted_tris=" + std::to_string(stats.renderSubmittedTriangleCount));
    lines.push_back(
        "live_submit commands=" + std::to_string(m_renderSubmitPlan.stats.submittedCommandCount)
        + " static=" + std::to_string(m_renderSubmitPlan.stats.staticCommandCount)
        + " dynamic=" + std::to_string(m_renderSubmitPlan.stats.dynamicCommandCount)
        + " last_submitted=" + std::to_string(m_lastRenderSubmitStats.submittedCommandCount)
        + " missing_texture=" + std::to_string(m_renderSubmitPlan.stats.skippedMissingTextureCount));
    lines.push_back(
        "materials total=" + std::to_string(stats.runtimeMaterialCount)
        + " missing=" + std::to_string(stats.runtimeMissingMaterialCount)
        + " texture_catalog=" + std::to_string(stats.runtimeTextureCatalogEntryCount)
        + " bound=" + std::to_string(stats.runtimeResolvedTextureMaterialCount)
        + " missing_texture=" + std::to_string(stats.runtimeMissingTextureMaterialCount));
    lines.push_back(
        "collision tris=" + std::to_string(stats.collisionTriangleCount)
        + " cells=" + std::to_string(stats.collisionCellCount)
        + " objects=" + std::to_string(stats.collidableObjectCount)
        + " object_cells=" + std::to_string(stats.collidableObjectCellCount)
        + " object_refs=" + std::to_string(stats.collidableObjectCellRefs));
    lines.push_back(
        "objects total=" + std::to_string(stats.objectCount)
        + " renderable=" + std::to_string(stats.renderableObjectCount)
        + " actors=" + std::to_string(stats.actorObjectCount)
        + " props=" + std::to_string(stats.propObjectCount)
        + " interactable=" + std::to_string(stats.interactableObjectCount)
        + " snapped=" + std::to_string(stats.snappedToFloorCount));
    lines.push_back(
        "mechanisms total=" + std::to_string(stats.mechanismCount)
        + " active=" + std::to_string(stats.activeMechanismCount)
        + " inert=" + std::to_string(stats.inertMechanismCount)
        + " bounds_cells=" + std::to_string(stats.mechanismBoundsCellCount)
        + " bounds_refs=" + std::to_string(stats.mechanismBoundsCellRefs)
        + " collision_batches=" + std::to_string(stats.mechanismCollisionBatchCount));

    if (m_lastMoveResult)
    {
        const Mm9DatPartyRuntimeMoveResult &move = *m_lastMoveResult;
        const Mm9DatPartyMovementResult &movement = move.movement;
        lines.push_back(
            "last_move end=" + mm9DatDebugVec3(movement.finalPosition)
            + " ground=" + mm9DatDebugBool(movement.onGround)
            + " wall=" + mm9DatDebugBool(movement.blockedByWall)
            + " object=" + mm9DatDebugBool(movement.blockedByObject)
            + " mechanism=" + mm9DatDebugBool(movement.blockedByMechanism)
            + " floor_candidates=" + std::to_string(movement.floorCandidateTriangleCount)
            + " floor_tested=" + std::to_string(movement.floorTestedTriangleCount)
            + " gravity=" + mm9DatDebugBool(move.gravityApplied));
    }
    else
    {
        lines.push_back("last_move none");
    }

    if (m_lastUseResult)
    {
        const Mm9DatWorldUseResult &use = *m_lastUseResult;
        lines.push_back(
            "last_use picked=" + mm9DatDebugBool(use.picked)
            + " kind=" + mm9DatDebugPickKind(use.hit.kind)
            + " activated=" + mm9DatDebugBool(use.activated)
            + " object_handle=" + std::to_string(use.hit.objectHandle)
            + " mechanism_handle=" + std::to_string(use.hit.mechanismHandle)
            + " trigger_dispatches=" + std::to_string(use.triggerDispatches.size()));
    }
    else
    {
        lines.push_back("last_use none");
    }

    return lines;
}

Mm9DatSceneRuntime::Mm9DatSceneRuntime(
    const std::string &mapFileName,
    Mm9DatRuntimeDevEntryResult entry,
    Party party,
    float gameMinutes,
    Mm9ScriptRuntimeState *pMm9ScriptRuntimeState,
    const Mm9DialoguePackage *pMm9DialoguePackage)
    : m_mapFileName(mapFileName)
    , m_party(std::move(party))
    , m_worldRuntime(
        mapFileName,
        std::move(entry),
        &m_party,
        &m_eventRuntimeState,
        &m_globalEventProgram,
        pMm9ScriptRuntimeState,
        pMm9DialoguePackage,
        gameMinutes)
{
    m_eventRuntimeState.mapFileName = mapFileName;
}

SceneKind Mm9DatSceneRuntime::kind() const
{
    return SceneKind::Outdoor;
}

const std::string &Mm9DatSceneRuntime::currentMapFileName() const
{
    return m_mapFileName;
}

Party &Mm9DatSceneRuntime::party()
{
    return m_party;
}

const Party &Mm9DatSceneRuntime::party() const
{
    return m_party;
}

EventRuntimeState *Mm9DatSceneRuntime::eventRuntimeState()
{
    return &m_eventRuntimeState;
}

const EventRuntimeState *Mm9DatSceneRuntime::eventRuntimeState() const
{
    return &m_eventRuntimeState;
}

ISceneEventContext *Mm9DatSceneRuntime::sceneEventContext()
{
    return nullptr;
}

const std::optional<ScriptedEventProgram> &Mm9DatSceneRuntime::localEventProgram() const
{
    return m_localEventProgram;
}

const std::optional<ScriptedEventProgram> &Mm9DatSceneRuntime::globalEventProgram() const
{
    return m_globalEventProgram;
}

std::optional<EventRuntimeState::PendingMapMove> Mm9DatSceneRuntime::consumePendingMapMove()
{
    if (!m_eventRuntimeState.pendingMapMove)
    {
        return std::nullopt;
    }

    std::optional<EventRuntimeState::PendingMapMove> pendingMapMove =
        std::move(m_eventRuntimeState.pendingMapMove);
    m_eventRuntimeState.pendingMapMove.reset();
    return pendingMapMove;
}

void Mm9DatSceneRuntime::advanceGameMinutes(float minutes)
{
    m_worldRuntime.advanceGameMinutes(minutes);
}

Mm9DatWorldGameplayRuntime &Mm9DatSceneRuntime::worldRuntime()
{
    return m_worldRuntime;
}

const Mm9DatWorldGameplayRuntime &Mm9DatSceneRuntime::worldRuntime() const
{
    return m_worldRuntime;
}
}
