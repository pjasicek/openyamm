#include "game/mm9/Mm9ScriptedObjectRuntime.h"

#include "game/maps/MapIdentity.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <exception>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
std::string toLowerCopy(const std::string &value)
{
    std::string output = value;
    std::transform(
        output.begin(),
        output.end(),
        output.begin(),
        [](unsigned char value)
        {
            return static_cast<char>(std::tolower(value));
        });
    return output;
}

float yawRadiansFromQuaternion(const std::array<float, 4> &quaternion)
{
    const float x = quaternion[0];
    const float y = quaternion[1];
    const float z = quaternion[2];
    const float w = quaternion[3];
    const float sinyCosp = 2.0f * (w * z + x * y);
    const float cosyCosp = 1.0f - 2.0f * (y * y + z * z);
    return std::atan2(sinyCosp, cosyCosp);
}

const Mm9EventObject *findEventObject(
    const Mm9EventsData *pEventsData,
    size_t sourceObjectIndex)
{
    if (pEventsData == nullptr)
    {
        return nullptr;
    }

    for (const Mm9EventObject &eventObject : pEventsData->objects)
    {
        if (eventObject.sourceObjectIndex >= 0
            && static_cast<size_t>(eventObject.sourceObjectIndex) == sourceObjectIndex)
        {
            return &eventObject;
        }
    }
    return nullptr;
}

std::optional<std::string> normalizedProperty(
    const Mm9EventObject *pEventObject,
    const std::string &name)
{
    if (pEventObject == nullptr)
    {
        return std::nullopt;
    }

    const std::string normalizedName = toLowerCopy(name);
    for (const auto &entry : pEventObject->normalizedProperties)
    {
        if (toLowerCopy(entry.first) == normalizedName)
        {
            return entry.second;
        }
    }
    return std::nullopt;
}

bool parseBoolProperty(const std::optional<std::string> &value, bool fallback)
{
    if (!value || value->empty())
    {
        return fallback;
    }

    const std::string normalized = toLowerCopy(*value);
    if (normalized == "true" || normalized == "yes")
    {
        return true;
    }
    if (normalized == "false" || normalized == "no")
    {
        return false;
    }

    try
    {
        return std::stoi(*value) != 0;
    }
    catch (const std::exception &)
    {
        return fallback;
    }
}

bool parseBoolPropertyIfPresent(const std::optional<std::string> &value)
{
    return value.has_value() && parseBoolProperty(value, false);
}

float parseFloatProperty(const std::optional<std::string> &value, float fallback)
{
    if (!value || value->empty())
    {
        return fallback;
    }

    try
    {
        return std::stof(*value);
    }
    catch (const std::exception &)
    {
        return fallback;
    }
}

bool propertyNamesPath(const std::optional<std::string> &value)
{
    if (!value || value->empty())
    {
        return false;
    }

    const std::string normalized = toLowerCopy(*value);
    return normalized != "0" && normalized != "none";
}

std::optional<std::string> runtimeObjectProperty(
    const Mm9ScriptedObject &object,
    const std::string &name)
{
    const std::string normalizedName = toLowerCopy(name);
    for (const auto &entry : object.normalizedProperties)
    {
        if (toLowerCopy(entry.first) == normalizedName)
        {
            return entry.second;
        }
    }
    return std::nullopt;
}

std::vector<Mm9ScriptedObjectRawPropertyRef> copyRawProperties(const Mm9EventObject *pEventObject)
{
    std::vector<Mm9ScriptedObjectRawPropertyRef> output;
    if (pEventObject == nullptr)
    {
        return output;
    }

    output.reserve(pEventObject->rawProperties.size());
    for (const Mm9EventObject::RawPropertyRef &property : pEventObject->rawProperties)
    {
        output.push_back(
            Mm9ScriptedObjectRawPropertyRef{
                .propertyIndex = property.propertyIndex,
                .name = property.name,
                .decoded = property.decoded,
                .code = property.code,
                .flags = property.flags,
                .rawRef = property.rawRef,
            });
    }
    return output;
}

bool likelyMm9ScriptedActorObject(const OutdoorSceneModelInstance &modelInstance)
{
    if (modelInstance.sourceModel.empty())
    {
        return false;
    }

    return toLowerCopy(modelInstance.sourceClass) != "prop";
}

bool likelyFlyingMm9Object(const Mm9ScriptedObject &object)
{
    const std::string className = toLowerCopy(object.sourceClass);
    const std::string modelName = toLowerCopy(object.sourceModel);
    const std::string objectName = toLowerCopy(object.sourceName);

    return className.find("fly") != std::string::npos
        || className.find("dragon") != std::string::npos
        || modelName.find("fly") != std::string::npos
        || modelName.find("dragon") != std::string::npos
        || objectName.find("fly") != std::string::npos
        || objectName.find("dragon") != std::string::npos;
}

Mm9ScriptedObjectMovementState buildMovementState(const Mm9ScriptedObject &object)
{
    Mm9ScriptedObjectMovementState movement = {};
    movement.moveToFloor = parseBoolProperty(runtimeObjectProperty(object, "MoveToFloor"), true);
    movement.wanderEnabled =
        parseBoolPropertyIfPresent(runtimeObjectProperty(object, "WanderON"))
        || parseBoolPropertyIfPresent(runtimeObjectProperty(object, "WanderOptions"));
    movement.wanderPathName = runtimeObjectProperty(object, "WanderPathName").value_or("");
    movement.scriptedPath =
        propertyNamesPath(runtimeObjectProperty(object, "WanderPathName"))
        || propertyNamesPath(runtimeObjectProperty(object, "MaxRailPath"));
    movement.animationSpeed = parseFloatProperty(runtimeObjectProperty(object, "AnimationSpeed"), 0.0f);
    movement.speed = parseFloatProperty(runtimeObjectProperty(object, "Speed"), 0.0f);
    movement.closingSpeed = parseFloatProperty(runtimeObjectProperty(object, "ClosingSpeed"), 0.0f);
    movement.runawayChance = parseFloatProperty(runtimeObjectProperty(object, "RunawayChance"), 0.0f);
    movement.wanderLeash = parseFloatProperty(runtimeObjectProperty(object, "WanderLeash"), 0.0f);
    movement.flying = likelyFlyingMm9Object(object);
    movement.fleeing = movement.runawayChance > 0.0f;
    movement.returning = false;
    movement.walking = movement.wanderEnabled && movement.speed <= 250.0f;
    movement.running = movement.wanderEnabled && movement.speed > 250.0f;
    movement.stationary = !movement.walking
        && !movement.running
        && !movement.scriptedPath
        && !movement.fleeing
        && !movement.returning;
    movement.rooted = movement.stationary && !movement.flying;
    return movement;
}

std::string movementStateName(const Mm9ScriptedObjectMovementState &movement)
{
    if (movement.fleeing)
    {
        return "fleeing";
    }
    if (movement.returning)
    {
        return "returning";
    }
    if (movement.flying)
    {
        return "flying";
    }
    if (movement.running)
    {
        return "running";
    }
    if (movement.walking)
    {
        return "walking";
    }
    if (movement.scriptedPath)
    {
        return "scripted_path";
    }
    if (movement.rooted)
    {
        return "rooted";
    }
    return "stationary";
}

Mm9ScriptedObject populateBaseObject(
    const std::string &mapId,
    const OutdoorSceneModelInstance &modelInstance,
    const Mm9EventObject *pEventObject,
    const std::string &visualId)
{
    Mm9ScriptedObject object = {};
    object.mapId = mapId;
    object.visualId = visualId;
    object.instanceId = modelInstance.instanceId;
    object.sourceRef = modelInstance.sourceRef;
    object.sourceKind = modelInstance.sourceKind;
    object.objectId =
        pEventObject != nullptr && !pEventObject->objectId.empty()
            ? pEventObject->objectId
            : (!modelInstance.instanceId.empty()
                ? modelInstance.instanceId
                : ("mm9:" + mapId + ":object:" + std::to_string(modelInstance.sourceObjectIndex)));
    object.sourceObjectId = object.objectId;
    object.sourceObjectIndex = modelInstance.sourceObjectIndex;
    object.sourceClass =
        pEventObject != nullptr && !pEventObject->sourceClass.empty()
            ? pEventObject->sourceClass
            : modelInstance.sourceClass;
    object.sourceName =
        pEventObject != nullptr && !pEventObject->sourceName.empty()
            ? pEventObject->sourceName
            : modelInstance.sourceName;
    object.sourceModel = normalizedProperty(pEventObject, "Filename").value_or(modelInstance.sourceModel);
    object.sourceSkin = normalizedProperty(pEventObject, "Skin").value_or(modelInstance.sourceSkin);
    object.modelAsset = modelInstance.modelAsset;
    object.modelSkinBinding = modelInstance.modelSkinBinding;
    object.scriptName = normalizedProperty(pEventObject, "ScriptName").value_or("");
    object.scriptParams = normalizedProperty(pEventObject, "ScriptParams").value_or("");
    object.rawObjectRef = pEventObject != nullptr ? pEventObject->rawObjectRef : "";
    object.rawPropertyCount = pEventObject != nullptr ? pEventObject->rawPropertyCount : 0;
    object.rawProperties = copyRawProperties(pEventObject);
    object.normalizedProperties = pEventObject != nullptr ? pEventObject->normalizedProperties
                                                         : std::unordered_map<std::string, std::string>();
    object.visible = parseBoolProperty(normalizedProperty(pEventObject, "Visible"), true);
    object.solid = parseBoolProperty(normalizedProperty(pEventObject, "Solid"), true);
    object.rayHit = parseBoolProperty(normalizedProperty(pEventObject, "RayHit"), true);
    object.rayHit = parseBoolProperty(normalizedProperty(pEventObject, "Rayhit"), object.rayHit);
    object.needsTick = parseBoolProperty(normalizedProperty(pEventObject, "NeedsTick"), false);
    object.pickable = object.visible && object.rayHit;
    object.currentClip = "placeholder";
    object.x = static_cast<float>(modelInstance.x);
    object.y = static_cast<float>(modelInstance.y);
    object.z = static_cast<float>(modelInstance.z);
    object.facingRadians = yawRadiansFromQuaternion(modelInstance.rotationQuat);
    object.scale = parseFloatProperty(normalizedProperty(pEventObject, "Scale"), modelInstance.scale[0]);
    object.movement = buildMovementState(object);
    object.movementState = movementStateName(object.movement);
    return object;
}

void applyVisualMetadata(
    Mm9ScriptedObject &object,
    const Mm9ScriptedBillboardVisual &visual,
    const OutdoorSceneModelInstance &modelInstance)
{
    object.radius = static_cast<float>(std::max(visual.collision.radius, 1));
    object.height = static_cast<float>(std::max(visual.collision.height, 1));
    object.verticalOffset = static_cast<float>(visual.collision.verticalOffset);

    for (const Mm9ScriptedBillboardUse &usedBy : visual.usedBy)
    {
        if (usedBy.mapId == object.mapId && usedBy.sourceObjectIndex == modelInstance.sourceObjectIndex)
        {
            object.objectId = usedBy.objectId;
            object.sourceObjectId = usedBy.objectId;
            if (object.sourceClass.empty() && !usedBy.sourceClass.empty())
            {
                object.sourceClass = usedBy.sourceClass;
            }
            if (object.sourceName.empty() && !usedBy.sourceName.empty())
            {
                object.sourceName = usedBy.sourceName;
            }
            if (object.scriptName.empty() && !usedBy.scriptName.empty())
            {
                object.scriptName = usedBy.scriptName;
            }
            if (object.scriptParams.empty() && !usedBy.scriptParams.empty())
            {
                object.scriptParams = usedBy.scriptParams;
            }
            break;
        }
    }
}
}

bool Mm9ScriptedObjectRuntime::initialize(
    const std::string &mapId,
    const OutdoorSceneData &sceneData,
    const Mm9ScriptedBillboardVisualSet &visualSet,
    const Mm9EventsData *pEventsData)
{
    m_objects.clear();
    const std::string normalizedMapId = normalizeWorldId(mapId);

    for (const OutdoorSceneModelInstance &modelInstance : sceneData.modelInstances)
    {
        const std::optional<std::string> visualId =
            visualSet.resolveVisualIdForModelInstance(normalizedMapId, modelInstance);
        if (!visualId && !likelyMm9ScriptedActorObject(modelInstance))
        {
            continue;
        }

        const Mm9EventObject *pEventObject = findEventObject(pEventsData, modelInstance.sourceObjectIndex);
        Mm9ScriptedObject object =
            populateBaseObject(
                normalizedMapId,
                modelInstance,
                pEventObject,
                visualId.value_or("mm9_missing_visual"));

        if (!visualId)
        {
            object.missingVisual = true;
            object.missingVisualReason = "unresolved_visual";
            m_objects.push_back(std::move(object));
            continue;
        }

        const Mm9ScriptedBillboardVisual *pVisual = visualSet.findVisual(*visualId);
        if (pVisual == nullptr)
        {
            object.missingVisual = true;
            object.missingVisualReason = "visual_metadata_missing";
            m_objects.push_back(std::move(object));
            continue;
        }

        applyVisualMetadata(object, *pVisual, modelInstance);
        if (const Mm9ScriptedBillboardClip *pClip = visualSet.findIdleClip(*pVisual))
        {
            object.currentClip = pClip->name;
        }

        if (visualSet.findFirstIdleFrame(*pVisual) == nullptr)
        {
            object.missingVisual = true;
            object.missingVisualReason = "idle_frame_missing";
        }

        m_objects.push_back(std::move(object));
    }

    return true;
}

const std::vector<Mm9ScriptedObject> &Mm9ScriptedObjectRuntime::objects() const
{
    return m_objects;
}

std::vector<Mm9ScriptedObject> &Mm9ScriptedObjectRuntime::objects()
{
    return m_objects;
}
}
