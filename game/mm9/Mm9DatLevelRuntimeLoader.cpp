#include "game/mm9/Mm9DatLevelRuntimeLoader.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <exception>
#include <fstream>
#include <iterator>
#include <unordered_map>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
bool readTextFile(const std::filesystem::path &path, std::string &text)
{
    std::ifstream input(path);

    if (!input)
    {
        return false;
    }

    text.assign(std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
    return true;
}

bool requireMap(const YAML::Node &node, const char *key, YAML::Node &result, std::string &errorMessage)
{
    result = node[key];

    if (!result || result.IsNull())
    {
        errorMessage = std::string("missing required section: ") + key;
        return false;
    }

    if (!result.IsMap())
    {
        errorMessage = std::string("section must be a map: ") + key;
        return false;
    }

    return true;
}

bool readRequiredString(
    const YAML::Node &node,
    const char *key,
    std::string &value,
    std::string &errorMessage)
{
    const YAML::Node valueNode = node[key];

    if (!valueNode || valueNode.IsNull())
    {
        errorMessage = std::string("missing required field: ") + key;
        return false;
    }

    if (!valueNode.IsScalar())
    {
        errorMessage = std::string("field must be scalar: ") + key;
        return false;
    }

    value = valueNode.as<std::string>();
    return true;
}

template <typename ValueType>
ValueType optionalScalarValue(const YAML::Node &node, const char *key, const ValueType &defaultValue)
{
    const YAML::Node valueNode = node[key];

    if (!valueNode || valueNode.IsNull() || !valueNode.IsScalar())
    {
        return defaultValue;
    }

    return valueNode.as<ValueType>(defaultValue);
}

std::optional<std::string> optionalNullableString(const YAML::Node &node, const char *key)
{
    const YAML::Node valueNode = node[key];

    if (!valueNode || valueNode.IsNull() || !valueNode.IsScalar())
    {
        return std::nullopt;
    }

    return valueNode.as<std::string>();
}

std::string lowerCopy(const std::string &value)
{
    std::string output = value;
    std::transform(
        output.begin(),
        output.end(),
        output.begin(),
        [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        });
    return output;
}

std::optional<YAML::Node> loadYamlMapFromText(
    const std::string &text,
    const char *label,
    std::string &errorMessage)
{
    YAML::Node root;

    try
    {
        root = YAML::Load(text);
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = std::string("could not parse ") + label + " YAML: " + exception.what();
        return std::nullopt;
    }

    if (!root || !root.IsMap())
    {
        errorMessage = std::string(label) + " YAML root must be a map.";
        return std::nullopt;
    }

    return root;
}

Mm9DatModelRenderRole parseModelRole(const YAML::Node &modelNode)
{
    Mm9DatModelRenderRole role = {};
    role.sourceModelIndex = optionalScalarValue<size_t>(modelNode, "source_model_index", 0);

    const YAML::Node rolesNode = modelNode["roles"];

    if (!rolesNode || !rolesNode.IsMap())
    {
        return role;
    }

    role.visible = optionalScalarValue<bool>(rolesNode, "visible", false);
    role.terrain = optionalScalarValue<bool>(rolesNode, "terrain", false);
    role.physicsBsp = optionalScalarValue<bool>(rolesNode, "physics_bsp", false);
    role.visBsp = optionalScalarValue<bool>(rolesNode, "vis_bsp", false);
    role.sky = optionalScalarValue<bool>(rolesNode, "sky", false);
    role.water = optionalScalarValue<bool>(rolesNode, "water", false);
    role.triggerOrVolume = optionalScalarValue<bool>(rolesNode, "trigger_or_volume", false);
    role.movable = optionalScalarValue<bool>(rolesNode, "movable", false);
    return role;
}

std::optional<std::string> objectProperty(
    const Mm9ScriptedObject &object,
    const std::string &propertyName)
{
    const std::string normalizedName = lowerCopy(propertyName);
    for (const auto &property : object.normalizedProperties)
    {
        if (lowerCopy(property.first) == normalizedName)
        {
            return property.second;
        }
    }

    return std::nullopt;
}

bool parseBoolProperty(const std::optional<std::string> &value, bool fallback)
{
    if (!value.has_value() || value->empty())
    {
        return fallback;
    }

    const std::string normalized = lowerCopy(*value);
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

float parseFloatProperty(const std::optional<std::string> &value, float fallback)
{
    if (!value.has_value() || value->empty())
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
    if (!value.has_value() || value->empty())
    {
        return false;
    }

    const std::string normalized = lowerCopy(*value);
    return normalized != "0" && normalized != "none";
}

bool likelyFlyingObject(const Mm9ScriptedObject &object)
{
    const std::string className = lowerCopy(object.sourceClass);
    const std::string modelName = lowerCopy(object.sourceModel);
    const std::string objectName = lowerCopy(object.sourceName);

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
    movement.moveToFloor = parseBoolProperty(objectProperty(object, "MoveToFloor"), true);
    movement.wanderEnabled =
        parseBoolProperty(objectProperty(object, "WanderON"), false)
        || parseBoolProperty(objectProperty(object, "WanderOptions"), false);
    movement.wanderPathName = objectProperty(object, "WanderPathName").value_or("");
    movement.scriptedPath =
        propertyNamesPath(objectProperty(object, "WanderPathName"))
        || propertyNamesPath(objectProperty(object, "MaxRailPath"));
    movement.animationSpeed = parseFloatProperty(objectProperty(object, "AnimationSpeed"), 0.0f);
    movement.speed = parseFloatProperty(objectProperty(object, "Speed"), 0.0f);
    movement.closingSpeed = parseFloatProperty(objectProperty(object, "ClosingSpeed"), 0.0f);
    movement.runawayChance = parseFloatProperty(objectProperty(object, "RunawayChance"), 0.0f);
    movement.wanderLeash = parseFloatProperty(objectProperty(object, "WanderLeash"), 0.0f);
    movement.flying = likelyFlyingObject(object);
    movement.fleeing = movement.runawayChance > 0.0f;
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

const Mm9DatObjectProperty *findDatObjectProperty(
    const Mm9DatObject &object,
    const std::string &propertyName)
{
    const std::string normalizedName = lowerCopy(propertyName);

    for (const Mm9DatObjectProperty &property : object.properties)
    {
        if (lowerCopy(property.name) == normalizedName)
        {
            return &property;
        }
    }

    return nullptr;
}

std::string datObjectPropertyStringValue(const Mm9DatObjectProperty &property)
{
    switch (property.type)
    {
    case Mm9DatObjectPropertyType::String:
        return property.stringValue;
    case Mm9DatObjectPropertyType::Vector:
    case Mm9DatObjectPropertyType::Color:
        return std::to_string(property.vectorValue.x)
            + " " + std::to_string(property.vectorValue.y)
            + " " + std::to_string(property.vectorValue.z);
    case Mm9DatObjectPropertyType::Real:
        return std::to_string(property.floatValue);
    case Mm9DatObjectPropertyType::Flags:
    case Mm9DatObjectPropertyType::LongInt:
        return std::to_string(property.intValue);
    case Mm9DatObjectPropertyType::Bool:
        return property.boolValue ? "1" : "0";
    case Mm9DatObjectPropertyType::Rotation:
        return std::to_string(property.rotationValue[0])
            + " " + std::to_string(property.rotationValue[1])
            + " " + std::to_string(property.rotationValue[2])
            + " " + std::to_string(property.rotationValue[3]);
    case Mm9DatObjectPropertyType::Unknown:
        return {};
    }

    return {};
}

std::optional<std::string> datObjectStringProperty(
    const Mm9DatObject &object,
    const std::string &propertyName)
{
    const Mm9DatObjectProperty *pProperty = findDatObjectProperty(object, propertyName);

    if (pProperty == nullptr || !pProperty->decoded)
    {
        return std::nullopt;
    }

    return datObjectPropertyStringValue(*pProperty);
}

std::optional<Mm9DatVec3> datObjectVectorProperty(
    const Mm9DatObject &object,
    const std::string &propertyName)
{
    const Mm9DatObjectProperty *pProperty = findDatObjectProperty(object, propertyName);

    if (pProperty == nullptr || !pProperty->decoded)
    {
        return std::nullopt;
    }

    if (pProperty->type != Mm9DatObjectPropertyType::Vector
        && pProperty->type != Mm9DatObjectPropertyType::Color)
    {
        return std::nullopt;
    }

    return pProperty->vectorValue;
}

std::optional<std::array<float, 4>> datObjectRotationProperty(
    const Mm9DatObject &object,
    const std::string &propertyName)
{
    const Mm9DatObjectProperty *pProperty = findDatObjectProperty(object, propertyName);

    if (pProperty == nullptr || !pProperty->decoded || pProperty->type != Mm9DatObjectPropertyType::Rotation)
    {
        return std::nullopt;
    }

    return pProperty->rotationValue;
}

std::optional<float> datObjectFloatProperty(
    const Mm9DatObject &object,
    const std::string &propertyName)
{
    const Mm9DatObjectProperty *pProperty = findDatObjectProperty(object, propertyName);

    if (pProperty == nullptr || !pProperty->decoded)
    {
        return std::nullopt;
    }

    switch (pProperty->type)
    {
    case Mm9DatObjectPropertyType::Real:
        return pProperty->floatValue;
    case Mm9DatObjectPropertyType::Flags:
    case Mm9DatObjectPropertyType::LongInt:
        if (pProperty->rawUIntValue != 0 || pProperty->floatValue != 0.0f)
        {
            return pProperty->floatValue;
        }
        return static_cast<float>(pProperty->intValue);
    case Mm9DatObjectPropertyType::Bool:
        return pProperty->boolValue ? 1.0f : 0.0f;
    default:
        return std::nullopt;
    }
}

bool hasDatObjectProperty(
    const Mm9DatObject &object,
    const std::string &propertyName)
{
    return findDatObjectProperty(object, propertyName) != nullptr;
}

std::vector<float> floatVectorFromLtVec3(const Mm9DatVec3 &value)
{
    return {
        value.x,
        value.y,
        value.z,
    };
}

Mm9DatVec3 datObjectLtToOpenYamm(const Mm9DatVec3 &position)
{
    return {
        position.x * Mm9DatToOpenYammScale,
        position.z * Mm9DatToOpenYammScale,
        position.y * Mm9DatToOpenYammScale,
    };
}

std::string normalizeMm9DatMapId(const std::string &value)
{
    std::string normalized;
    normalized.reserve(value.size());

    for (char character : value)
    {
        const unsigned char unsignedCharacter = static_cast<unsigned char>(character);
        if (std::isalnum(unsignedCharacter))
        {
            normalized.push_back(static_cast<char>(std::tolower(unsignedCharacter)));
        }
        else if (character == '_' || character == '-')
        {
            normalized.push_back(character);
        }
    }

    return normalized;
}

void copyDatObjectPropertyRefs(const Mm9DatObject &sourceObject, Mm9ScriptedObject &targetObject)
{
    targetObject.rawPropertyCount = sourceObject.properties.size();
    targetObject.rawProperties.reserve(sourceObject.properties.size());

    for (size_t propertyIndex = 0; propertyIndex < sourceObject.properties.size(); ++propertyIndex)
    {
        const Mm9DatObjectProperty &sourceProperty = sourceObject.properties[propertyIndex];
        Mm9ScriptedObjectRawPropertyRef ref = {};
        ref.propertyIndex = propertyIndex;
        ref.name = sourceProperty.name;
        ref.decoded = sourceProperty.decoded;
        ref.code = sourceProperty.code;
        ref.flags = static_cast<int>(sourceProperty.flags);
        ref.rawRef = targetObject.sourceRef + ".properties[" + std::to_string(propertyIndex) + "]";
        targetObject.rawProperties.push_back(std::move(ref));
    }
}

std::vector<Mm9ScriptedObject> buildScriptedObjectsFromDatObjects(
    const std::string &mapId,
    const std::vector<Mm9DatObject> &sourceObjects)
{
    std::vector<Mm9ScriptedObject> objects;
    objects.reserve(sourceObjects.size());

    for (const Mm9DatObject &sourceObject : sourceObjects)
    {
        Mm9ScriptedObject object = {};
        object.mapId = mapId;
        object.visualId = "mm9_dat_object";
        object.sourceObjectIndex = sourceObject.sourceObjectIndex;
        object.sourceRef = "dat:ObjectData#objects[" + std::to_string(sourceObject.sourceObjectIndex) + "]";
        object.rawObjectRef = object.sourceRef;
        object.sourceKind = sourceObject.className;
        object.sourceClass = sourceObject.className;
        object.sourceName = datObjectStringProperty(sourceObject, "Name").value_or(
            sourceObject.className + std::to_string(sourceObject.sourceObjectIndex));
        object.objectId = "mm9:" + mapId + ":object:" + std::to_string(sourceObject.sourceObjectIndex);
        object.sourceObjectId = object.objectId;
        object.instanceId = object.objectId;
        object.sourceModel = datObjectStringProperty(sourceObject, "Filename").value_or("");
        object.sourceSkin = datObjectStringProperty(sourceObject, "Skin").value_or("");
        object.scriptName = datObjectStringProperty(sourceObject, "ScriptName").value_or("");
        object.scriptParams = datObjectStringProperty(sourceObject, "ScriptParams").value_or("");
        object.scale = parseFloatProperty(datObjectStringProperty(sourceObject, "Scale"), 1.0f);
        object.visible = parseBoolProperty(datObjectStringProperty(sourceObject, "Visible"), true);
        object.solid = parseBoolProperty(datObjectStringProperty(sourceObject, "Solid"), true);
        object.rayHit = parseBoolProperty(datObjectStringProperty(sourceObject, "RayHit"), object.solid);
        object.pickable = object.visible && object.rayHit;
        object.needsTick = parseBoolProperty(datObjectStringProperty(sourceObject, "NeedsTick"), false);

        const std::optional<Mm9DatVec3> positionLt = datObjectVectorProperty(sourceObject, "Pos");
        if (positionLt.has_value())
        {
            const Mm9DatVec3 position = datObjectLtToOpenYamm(*positionLt);
            object.x = position.x;
            object.y = position.y;
            object.z = position.z;
        }

        const std::optional<Mm9DatVec3> dimsLt = datObjectVectorProperty(sourceObject, "Dims");
        if (dimsLt.has_value())
        {
            const Mm9DatVec3 dims = datObjectLtToOpenYamm(*dimsLt);
            object.radius = std::max(std::fabs(dims.x), std::fabs(dims.z));
            object.height = std::max(1.0f, std::fabs(dims.y) * 2.0f);
        }

        object.normalizedProperties.reserve(sourceObject.properties.size());
        for (const Mm9DatObjectProperty &property : sourceObject.properties)
        {
            if (property.decoded)
            {
                object.normalizedProperties[property.name] = datObjectPropertyStringValue(property);
            }
        }

        copyDatObjectPropertyRefs(sourceObject, object);
        object.movement = buildMovementState(object);
        object.movementState = movementStateName(object.movement);
        objects.push_back(std::move(object));
    }

    return objects;
}

std::vector<Mm9DatRuntimeStartPoint> buildRuntimeStartPointsFromDatObjects(
    const std::vector<Mm9DatObject> &sourceObjects)
{
    std::vector<Mm9DatRuntimeStartPoint> startPoints;

    for (const Mm9DatObject &sourceObject : sourceObjects)
    {
        if (lowerCopy(sourceObject.className) != "startpoint")
        {
            continue;
        }

        const std::optional<Mm9DatVec3> positionLt = datObjectVectorProperty(sourceObject, "Pos");

        if (!positionLt.has_value())
        {
            continue;
        }

        Mm9DatRuntimeStartPoint startPoint = {};
        startPoint.name = datObjectStringProperty(sourceObject, "Name").value_or(
            sourceObject.className + std::to_string(sourceObject.sourceObjectIndex));
        startPoint.sourceObjectIndex = sourceObject.sourceObjectIndex;
        startPoint.positionLt = *positionLt;
        startPoint.position = datObjectLtToOpenYamm(*positionLt);
        startPoint.rotationLt = datObjectRotationProperty(sourceObject, "Rotation").value_or(startPoint.rotationLt);
        startPoint.yawRadians = startPoint.rotationLt[1];
        startPoint.movePlayerToFloor =
            parseBoolProperty(datObjectStringProperty(sourceObject, "MovePlayerToFloor"), true);
        startPoints.push_back(std::move(startPoint));
    }

    return startPoints;
}

std::vector<Mm9DatRuntimeExitTrigger> buildRuntimeExitTriggersFromDatObjects(
    const std::vector<Mm9DatObject> &sourceObjects)
{
    std::vector<Mm9DatRuntimeExitTrigger> exitTriggers;

    for (const Mm9DatObject &sourceObject : sourceObjects)
    {
        if (lowerCopy(sourceObject.className) != "exittrigger")
        {
            continue;
        }

        Mm9DatRuntimeExitTrigger exitTrigger = {};
        exitTrigger.name = datObjectStringProperty(sourceObject, "Name").value_or(
            sourceObject.className + std::to_string(sourceObject.sourceObjectIndex));
        exitTrigger.sourceObjectIndex = sourceObject.sourceObjectIndex;
        exitTrigger.destinationWorld = datObjectStringProperty(sourceObject, "DestinationWorld").value_or("");
        exitTrigger.destinationMapId = normalizeMm9DatMapId(exitTrigger.destinationWorld);
        exitTrigger.startPointName = datObjectStringProperty(sourceObject, "StartPointName").value_or("");
        exitTrigger.loadScreen = datObjectStringProperty(sourceObject, "LoadScreen").value_or("");
        exitTrigger.travelDays = datObjectFloatProperty(sourceObject, "TravelDays").value_or(0.0f);
        exitTrigger.askPlayer = parseBoolProperty(datObjectStringProperty(sourceObject, "AskPlayer"), false);
        exitTrigger.startOn = parseBoolProperty(datObjectStringProperty(sourceObject, "StartOn"), true);

        const std::optional<Mm9DatVec3> positionLt = datObjectVectorProperty(sourceObject, "Pos");
        if (positionLt.has_value())
        {
            exitTrigger.positionLt = *positionLt;
            exitTrigger.position = datObjectLtToOpenYamm(*positionLt);
        }

        const std::optional<Mm9DatVec3> dimsLt = datObjectVectorProperty(sourceObject, "Dims");
        if (dimsLt.has_value())
        {
            exitTrigger.dimsLt = *dimsLt;
            exitTrigger.dims = datObjectLtToOpenYamm(*dimsLt);
        }

        exitTriggers.push_back(std::move(exitTrigger));
    }

    return exitTriggers;
}

std::string sourceObjectId(const std::string &mapId, size_t sourceObjectIndex)
{
    return "mm9:" + mapId + ":object:" + std::to_string(sourceObjectIndex);
}

std::string mechanismKindForClass(const std::string &className)
{
    static const std::unordered_map<std::string, std::string> mechanismKinds = {
        {"Door", "linear_door"},
        {"RotatingDoor", "rotating_door"},
        {"WeightedLift", "weighted_lift"},
        {"RotatingBrush", "rotating_brush"},
        {"BlueWater", "water_volume"},
        {"Ladder", "ladder_volume"},
        {"Shooter", "shooter"},
        {"InvisibleBrush", "collision_volume"},
        {"DestructableBrush", "destructible_brush"},
        {"DestructableProp", "destructible_prop"},
        {"AIBarrier", "ai_barrier"},
        {"PerceptionBrush", "perception_brush"},
        {"ScriptObject", "script_object"},
    };

    const auto iterator = mechanismKinds.find(className);
    return iterator != mechanismKinds.end() ? iterator->second : std::string();
}

Mm9EventObject buildDatEventObject(const std::string &mapId, const Mm9DatObject &sourceObject)
{
    Mm9EventObject eventObject = {};
    eventObject.objectId = sourceObjectId(mapId, sourceObject.sourceObjectIndex);
    eventObject.sourceObjectIndex = static_cast<int>(sourceObject.sourceObjectIndex);
    eventObject.sourceClass = sourceObject.className;
    eventObject.sourceName = datObjectStringProperty(sourceObject, "Name").value_or("");
    eventObject.rawObjectRef = "dat:ObjectData#objects[" + std::to_string(sourceObject.sourceObjectIndex) + "]";
    eventObject.rawPropertyCount = sourceObject.properties.size();

    if (!mechanismKindForClass(sourceObject.className).empty())
    {
        eventObject.classifications.push_back("mechanism");
    }
    if (sourceObject.className == "Trigger")
    {
        eventObject.classifications.push_back("trigger");
    }
    if (sourceObject.className == "Door"
        || sourceObject.className == "RotatingDoor"
        || sourceObject.className == "WeightedLift"
        || sourceObject.className == "Trigger"
        || sourceObject.className == "ScriptObject"
        || sourceObject.className == "Prop"
        || sourceObject.className == "WorldObject"
        || sourceObject.className == "TreasureChest"
        || sourceObject.className == "DestructableProp"
        || sourceObject.className == "DestructableBrush"
        || sourceObject.className == "BlueWater"
        || sourceObject.className == "Ladder"
        || hasDatObjectProperty(sourceObject, "ScriptName"))
    {
        eventObject.classifications.push_back("interaction");
    }

    eventObject.rawProperties.reserve(sourceObject.properties.size());
    for (size_t propertyIndex = 0; propertyIndex < sourceObject.properties.size(); ++propertyIndex)
    {
        const Mm9DatObjectProperty &sourceProperty = sourceObject.properties[propertyIndex];
        Mm9EventObject::RawPropertyRef ref = {};
        ref.propertyIndex = propertyIndex;
        ref.name = sourceProperty.name;
        ref.decoded = sourceProperty.decoded;
        ref.code = sourceProperty.code;
        ref.flags = static_cast<int>(sourceProperty.flags);
        ref.rawRef = "dat:ObjectData#objects[" + std::to_string(sourceObject.sourceObjectIndex)
            + "].properties[" + std::to_string(propertyIndex) + "]";
        eventObject.rawProperties.push_back(std::move(ref));

        if (sourceProperty.decoded)
        {
            eventObject.normalizedProperties[sourceProperty.name] =
                datObjectPropertyStringValue(sourceProperty);
        }
    }

    return eventObject;
}

void applyOptionalBoolProperty(
    const Mm9DatObject &sourceObject,
    const std::string &propertyName,
    bool &value,
    bool &present)
{
    if (!hasDatObjectProperty(sourceObject, propertyName))
    {
        return;
    }

    value = parseBoolProperty(datObjectStringProperty(sourceObject, propertyName), value);
    present = true;
}

void applyOptionalFloatProperty(
    const Mm9DatObject &sourceObject,
    const std::string &propertyName,
    float &value,
    bool &present)
{
    if (!hasDatObjectProperty(sourceObject, propertyName))
    {
        return;
    }

    value = parseFloatProperty(datObjectStringProperty(sourceObject, propertyName), value);
    present = true;
}

void applyOptionalVectorProperty(
    const Mm9DatObject &sourceObject,
    const std::string &propertyName,
    std::vector<float> &value,
    bool &present)
{
    const std::optional<Mm9DatVec3> vectorValue = datObjectVectorProperty(sourceObject, propertyName);

    if (!vectorValue.has_value())
    {
        return;
    }

    value = floatVectorFromLtVec3(*vectorValue);
    present = true;
}

std::vector<Mm9EventTriggerOutput> collectDatTriggerOutputs(const Mm9DatObject &sourceObject)
{
    std::vector<Mm9EventTriggerOutput> outputs;

    for (int slot = 1; slot <= 10; ++slot)
    {
        const std::string targetName =
            datObjectStringProperty(sourceObject, "TargetName" + std::to_string(slot)).value_or("");
        const std::string messageName =
            datObjectStringProperty(sourceObject, "MessageName" + std::to_string(slot)).value_or("");

        if (!targetName.empty() || !messageName.empty())
        {
            Mm9EventTriggerOutput output = {};
            output.phase = "trigger";
            output.slot = slot;
            output.targetName = targetName;
            output.messageName = messageName;
            outputs.push_back(std::move(output));
        }
    }

    for (const std::string &phase : {"open", "close"})
    {
        const std::string targetPrefix = phase == "open" ? "OpenTriggerTarget" : "CloseTriggerTarget";
        const std::string messagePrefix = phase == "open" ? "OpenTrigger" : "CloseTrigger";

        for (int slot = 0; slot < 4; ++slot)
        {
            const std::string targetName =
                datObjectStringProperty(sourceObject, targetPrefix + std::to_string(slot)).value_or("");
            const std::string messageName =
                datObjectStringProperty(sourceObject, messagePrefix + std::to_string(slot)).value_or("");

            if (!targetName.empty() || !messageName.empty())
            {
                Mm9EventTriggerOutput output = {};
                output.phase = phase;
                output.slot = slot;
                output.targetName = targetName;
                output.messageName = messageName;
                outputs.push_back(std::move(output));
            }
        }
    }

    return outputs;
}

std::vector<Mm9EventMechanismSound> collectDatMechanismSounds(const Mm9DatObject &sourceObject)
{
    const std::vector<std::pair<std::string, std::string>> soundProperties = {
        {"open", "OpenSoundName"},
        {"close", "CloseSoundName"},
        {"open_start", "OpenStartSound"},
        {"open_busy", "OpenBusySound"},
        {"open_stop", "OpenStopSound"},
        {"close_start", "CloseStartSound"},
        {"close_busy", "CloseBusySound"},
        {"close_stop", "CloseStopSound"},
        {"jiggle", "JiggleSound"},
    };

    std::vector<Mm9EventMechanismSound> sounds;

    for (const auto &soundProperty : soundProperties)
    {
        if (!hasDatObjectProperty(sourceObject, soundProperty.second))
        {
            continue;
        }

        Mm9EventMechanismSound sound = {};
        sound.phase = soundProperty.first;
        sound.sourceProperty = soundProperty.second;
        sound.soundName = datObjectStringProperty(sourceObject, soundProperty.second).value_or("");
        sound.authored = true;
        sounds.push_back(std::move(sound));
    }

    return sounds;
}

Mm9EventMechanism buildDatMechanism(const std::string &mapId, const Mm9DatObject &sourceObject)
{
    Mm9EventMechanism mechanism = {};
    mechanism.objectId = sourceObjectId(mapId, sourceObject.sourceObjectIndex);
    mechanism.mechanismId = mechanism.objectId + ":mechanism";
    mechanism.sourceObjectIndex = static_cast<int>(sourceObject.sourceObjectIndex);
    mechanism.sourceClass = sourceObject.className;
    mechanism.sourceName = datObjectStringProperty(sourceObject, "Name").value_or("");
    mechanism.kind = mechanismKindForClass(sourceObject.className);
    applyOptionalBoolProperty(
        sourceObject,
        "StartOpen",
        mechanism.activation.startOpen,
        mechanism.activation.hasStartOpen);
    applyOptionalBoolProperty(sourceObject, "Locked", mechanism.activation.locked, mechanism.activation.hasLocked);
    applyOptionalBoolProperty(
        sourceObject,
        "PushOpen",
        mechanism.activation.pushOpen,
        mechanism.activation.hasPushOpen);
    applyOptionalBoolProperty(
        sourceObject,
        "TouchToOpen",
        mechanism.activation.touchToOpen,
        mechanism.activation.hasTouchToOpen);
    applyOptionalBoolProperty(
        sourceObject,
        "ReopenOnContact",
        mechanism.activation.reopenOnContact,
        mechanism.activation.hasReopenOnContact);
    applyOptionalVectorProperty(sourceObject, "MoveDir", mechanism.linear.moveDirLt, mechanism.linear.hasMoveDir);
    applyOptionalFloatProperty(sourceObject, "MoveDist", mechanism.linear.moveDistLt, mechanism.linear.hasMoveDist);
    applyOptionalFloatProperty(
        sourceObject,
        "Speed",
        mechanism.linear.openSpeedLtPerSecond,
        mechanism.linear.hasOpenSpeed);
    applyOptionalFloatProperty(
        sourceObject,
        "ClosingSpeed",
        mechanism.linear.closeSpeedLtPerSecond,
        mechanism.linear.hasCloseSpeed);
    applyOptionalVectorProperty(
        sourceObject,
        "RotationPoint",
        mechanism.rotation.rotationPointLt,
        mechanism.rotation.hasRotationPoint);
    applyOptionalVectorProperty(
        sourceObject,
        "RotationAngles",
        mechanism.rotation.rotationAnglesDeg,
        mechanism.rotation.hasRotationAngles);
    applyOptionalBoolProperty(sourceObject, "OpenAway", mechanism.rotation.openAway, mechanism.rotation.hasOpenAway);
    applyOptionalFloatProperty(
        sourceObject,
        "MoveDelay",
        mechanism.timing.moveDelaySecondsSource,
        mechanism.timing.hasMoveDelaySecondsSource);
    applyOptionalFloatProperty(
        sourceObject,
        "OpenWaitTime",
        mechanism.timing.openWaitSecondsSource,
        mechanism.timing.hasOpenWaitSecondsSource);
    mechanism.sounds = collectDatMechanismSounds(sourceObject);
    mechanism.triggerOutputs = collectDatTriggerOutputs(sourceObject);
    return mechanism;
}

std::unordered_map<std::string, std::vector<size_t>> buildWorldModelIndicesByName(const Mm9DatWorld &world)
{
    std::unordered_map<std::string, std::vector<size_t>> indicesByName;

    for (size_t modelIndex = 0; modelIndex < world.worldModels.size(); ++modelIndex)
    {
        indicesByName[lowerCopy(world.worldModels[modelIndex].name)].push_back(modelIndex);
    }

    return indicesByName;
}

std::vector<Mm9EventBindingTarget> buildExactWorldModelTargets(
    const Mm9DatWorld &world,
    const std::unordered_map<std::string, std::vector<size_t>> &worldModelIndicesByName,
    const std::string &sourceName)
{
    std::vector<Mm9EventBindingTarget> targets;
    const auto iterator = worldModelIndicesByName.find(lowerCopy(sourceName));

    if (iterator == worldModelIndicesByName.end())
    {
        return targets;
    }

    for (size_t modelIndex : iterator->second)
    {
        const Mm9DatWorldModel &model = world.worldModels[modelIndex];
        Mm9EventBindingTarget target = {};
        target.targetKind = "odm_bmodel";
        target.targetId = "dat:world_model:" + std::to_string(modelIndex);
        target.confidence = "exact_source_model_name";
        target.bmodelIndex = modelIndex;
        target.bmodelName = model.name;
        target.sourceModelName = model.name;

        Mm9EventBindingTarget::SourcePolygonGroup group = {};
        group.sourceModelIndex = modelIndex;
        group.sourceModelName = model.name;
        group.sourcePolyCount = model.polies.size();
        group.sourceSurfaceCount = model.surfaces.size();
        group.boundsMinLt = floatVectorFromLtVec3(model.boundsMinLt);
        group.boundsMaxLt = floatVectorFromLtVec3(model.boundsMaxLt);
        group.movable = (model.worldInfoFlags & (1u << 1)) != 0;
        group.hasMovable = true;
        target.sourcePolygonGroup = std::move(group);
        targets.push_back(std::move(target));
    }

    return targets;
}

Mm9EventsData buildMm9EventsDataFromDatWorld(
    const std::string &mapId,
    const std::filesystem::path &sourceDatPath,
    const Mm9DatWorld &world)
{
    Mm9EventsData events = {};
    events.formatVersion = 1;
    events.kind = "mm9_events";
    events.sourceDat = sourceDatPath.generic_string();
    events.sourceRawObjects = "dat:ObjectData";

    const std::unordered_map<std::string, std::vector<size_t>> worldModelIndicesByName =
        buildWorldModelIndicesByName(world);

    events.objects.reserve(world.objects.size());

    for (const Mm9DatObject &sourceObject : world.objects)
    {
        const std::string sourceName = datObjectStringProperty(sourceObject, "Name").value_or("");
        Mm9EventObject eventObject = buildDatEventObject(mapId, sourceObject);
        events.objects.push_back(std::move(eventObject));

        const std::vector<Mm9EventBindingTarget> targets =
            buildExactWorldModelTargets(world, worldModelIndicesByName, sourceName);
        if (!targets.empty())
        {
            Mm9EventBinding binding = {};
            binding.objectId = sourceObjectId(mapId, sourceObject.sourceObjectIndex);
            binding.sourceObjectIndex = static_cast<int>(sourceObject.sourceObjectIndex);
            binding.targets = targets;
            events.bindings.push_back(std::move(binding));
        }

        if (!mechanismKindForClass(sourceObject.className).empty())
        {
            events.mechanisms.push_back(buildDatMechanism(mapId, sourceObject));
        }
    }

    events.mechanismCount = events.mechanisms.size();
    return events;
}
}

std::filesystem::path resolveMm9DatLevelRuntimeRelativePath(
    const std::filesystem::path &levelPath,
    const std::string &relativePath)
{
    const std::filesystem::path path(relativePath);

    if (path.is_absolute())
    {
        return path.lexically_normal();
    }

    return (levelPath.parent_path() / path).lexically_normal();
}

std::optional<Mm9DatLevelRuntimeMetadata> parseMm9DatLevelRuntimeMetadata(
    const std::string &text,
    std::string &errorMessage)
{
    errorMessage.clear();
    const std::optional<YAML::Node> root = loadYamlMapFromText(text, "MM9 DAT level", errorMessage);

    if (!root.has_value())
    {
        return std::nullopt;
    }

    Mm9DatLevelRuntimeMetadata metadata = {};
    metadata.formatVersion = optionalScalarValue<int>(*root, "format_version", 0);

    if (!readRequiredString(*root, "kind", metadata.kind, errorMessage))
    {
        return std::nullopt;
    }

    if (metadata.kind != "mm9_level")
    {
        errorMessage = "unsupported level kind: " + metadata.kind;
        return std::nullopt;
    }

    if (!readRequiredString(*root, "map_id", metadata.mapId, errorMessage)
        || !readRequiredString(*root, "display_name", metadata.displayName, errorMessage))
    {
        return std::nullopt;
    }

    YAML::Node sourceNode;
    YAML::Node runtimeNode;

    if (!requireMap(*root, "source", sourceNode, errorMessage)
        || !requireMap(*root, "runtime", runtimeNode, errorMessage))
    {
        return std::nullopt;
    }

    if (!readRequiredString(sourceNode, "dat", metadata.source.dat, errorMessage)
        || !readRequiredString(sourceNode, "manifest", metadata.source.manifest, errorMessage)
        || !readRequiredString(sourceNode, "original_dat", metadata.source.originalDat, errorMessage)
        || !readRequiredString(sourceNode, "source_game", metadata.source.sourceGame, errorMessage)
        || !readRequiredString(sourceNode, "content_hash", metadata.source.contentHash, errorMessage))
    {
        return std::nullopt;
    }

    metadata.source.datVersion = optionalScalarValue<int>(sourceNode, "dat_version", 0);

    if (!readRequiredString(runtimeNode, "world_backend", metadata.worldBackend, errorMessage)
        || !readRequiredString(runtimeNode, "visibility", metadata.visibility, errorMessage)
        || !readRequiredString(runtimeNode, "collision", metadata.collision, errorMessage)
        || !readRequiredString(runtimeNode, "render", metadata.render, errorMessage))
    {
        return std::nullopt;
    }

    metadata.sky = optionalScalarValue<bool>(runtimeNode, "sky", false);

    const YAML::Node sidecarsNode = (*root)["sidecars"];
    if (sidecarsNode && !sidecarsNode.IsNull() && !sidecarsNode.IsMap())
    {
        errorMessage = "section must be a map: sidecars";
        return std::nullopt;
    }

    if (sidecarsNode && sidecarsNode.IsMap())
    {
        metadata.sidecars.datWorld = optionalScalarValue<std::string>(sidecarsNode, "dat_world", std::string());
        metadata.sidecars.rawObjects = optionalScalarValue<std::string>(sidecarsNode, "raw_objects", std::string());
        metadata.sidecars.materials = optionalScalarValue<std::string>(sidecarsNode, "materials", std::string());
        metadata.sidecars.events = optionalScalarValue<std::string>(sidecarsNode, "events", std::string());
        metadata.sidecars.sourceAssetAliases = optionalNullableString(sidecarsNode, "source_asset_aliases");
        metadata.sidecars.sceneCompat = optionalNullableString(sidecarsNode, "scene_compat");
        metadata.sidecars.sourceMetadataCompat = optionalNullableString(sidecarsNode, "source_metadata_compat");
        metadata.sidecars.bspCompat = optionalNullableString(sidecarsNode, "bsp_compat");
        metadata.sidecars.geometryCompat = optionalNullableString(sidecarsNode, "geometry_compat");
        metadata.sidecars.modelAssetsCompat = optionalNullableString(sidecarsNode, "model_assets_compat");
        metadata.sidecars.odmCompat = optionalNullableString(sidecarsNode, "odm_compat");
        metadata.sidecars.blvCompat = optionalNullableString(sidecarsNode, "blv_compat");
    }

    if (metadata.formatVersion <= 0)
    {
        errorMessage = "MM9 DAT level format_version must be positive.";
        return std::nullopt;
    }

    if (metadata.source.datVersion != 66)
    {
        errorMessage = "MM9 DAT level source.dat_version must be 66.";
        return std::nullopt;
    }

    if (metadata.worldBackend != "dat_world")
    {
        errorMessage = "MM9 DAT level runtime.world_backend must be dat_world.";
        return std::nullopt;
    }

    return metadata;
}

std::optional<Mm9DatWorldSidecarRuntimeData> parseMm9DatWorldSidecarRuntimeData(
    const std::string &text,
    std::string &errorMessage)
{
    errorMessage.clear();
    const std::optional<YAML::Node> root = loadYamlMapFromText(text, "MM9 DAT world sidecar", errorMessage);

    if (!root.has_value())
    {
        return std::nullopt;
    }

    const std::string kind = optionalScalarValue<std::string>(*root, "kind", std::string());

    if (kind != "mm9_dat_world")
    {
        errorMessage = "unsupported DAT world sidecar kind: " + kind;
        return std::nullopt;
    }

    Mm9DatWorldSidecarRuntimeData data = {};
    data.mapId = optionalScalarValue<std::string>(*root, "map_id", std::string());
    data.sourceDat = optionalScalarValue<std::string>(*root, "source_dat", std::string());
    data.datVersion = optionalScalarValue<int>(*root, "dat_version", 0);

    const YAML::Node totalsNode = (*root)["totals"];
    if (totalsNode && totalsNode.IsMap())
    {
        data.worldModelCount = optionalScalarValue<size_t>(totalsNode, "world_model_count", 0);
    }

    const YAML::Node modelsNode = (*root)["world_models"];

    if (!modelsNode || !modelsNode.IsSequence())
    {
        errorMessage = "MM9 DAT world sidecar world_models must be a sequence.";
        return std::nullopt;
    }

    data.modelRoles.reserve(modelsNode.size());

    for (const YAML::Node &modelNode : modelsNode)
    {
        if (!modelNode.IsMap())
        {
            errorMessage = "MM9 DAT world sidecar world model entry must be a map.";
            return std::nullopt;
        }

        data.modelRoles.push_back(parseModelRole(modelNode));
    }

    if (data.datVersion != 66)
    {
        errorMessage = "MM9 DAT world sidecar dat_version must be 66.";
        return std::nullopt;
    }

    if (data.worldModelCount != 0 && data.worldModelCount != data.modelRoles.size())
    {
        errorMessage = "MM9 DAT world sidecar world_model_count does not match world_models size.";
        return std::nullopt;
    }

    return data;
}

std::optional<Mm9DatLevelRuntimeLoadResult> loadMm9DatLevelRuntime(
    const std::filesystem::path &levelPath,
    std::string &errorMessage)
{
    errorMessage.clear();

    std::string levelText;
    if (!readTextFile(levelPath, levelText))
    {
        errorMessage = "could not read MM9 DAT level file: " + levelPath.generic_string();
        return std::nullopt;
    }

    std::optional<Mm9DatLevelRuntimeMetadata> metadata =
        parseMm9DatLevelRuntimeMetadata(levelText, errorMessage);

    if (!metadata.has_value())
    {
        return std::nullopt;
    }

    Mm9DatLevelRuntimeLoadResult result = {};
    result.metadata = *metadata;
    result.levelPath = levelPath.lexically_normal();
    result.sourceDatPath = resolveMm9DatLevelRuntimeRelativePath(result.levelPath, metadata->source.dat);
    if (!metadata->sidecars.datWorld.empty())
    {
        result.datWorldSidecarPath =
            resolveMm9DatLevelRuntimeRelativePath(result.levelPath, metadata->sidecars.datWorld);
    }
    if (!metadata->sidecars.rawObjects.empty())
    {
        result.rawObjectsSidecarPath =
            resolveMm9DatLevelRuntimeRelativePath(result.levelPath, metadata->sidecars.rawObjects);
    }
    if (metadata->sidecars.sceneCompat.has_value())
    {
        result.sceneCompatPath =
            resolveMm9DatLevelRuntimeRelativePath(result.levelPath, *metadata->sidecars.sceneCompat);
    }
    if (!metadata->sidecars.events.empty())
    {
        result.eventsSidecarPath =
            resolveMm9DatLevelRuntimeRelativePath(result.levelPath, metadata->sidecars.events);
    }

    std::optional<Mm9DatWorld> world = loadMm9DatWorld(result.sourceDatPath, errorMessage);
    if (!world.has_value())
    {
        errorMessage = "could not load MM9 DAT world " + result.sourceDatPath.generic_string() + ": "
            + errorMessage;
        return std::nullopt;
    }
    result.world = std::move(*world);
    result.modelRoles = deriveMm9DatModelRenderRoles(result.world);
    result.events = buildMm9EventsDataFromDatWorld(result.metadata.mapId, result.sourceDatPath, result.world);
    result.scriptedObjects = buildScriptedObjectsFromDatObjects(result.metadata.mapId, result.world.objects);
    result.startPoints = buildRuntimeStartPointsFromDatObjects(result.world.objects);
    result.exitTriggers = buildRuntimeExitTriggersFromDatObjects(result.world.objects);

    Mm9DatWorldRuntimeBuildInput input = {};
    input.mapId = result.metadata.mapId;
    input.pWorld = &result.world;
    input.pEvents = &result.events;
    input.modelRoles = result.modelRoles;
    input.scriptedObjects = result.scriptedObjects;
    if (!result.metadata.source.manifest.empty())
    {
        const std::filesystem::path sourceManifestPath =
            resolveMm9DatLevelRuntimeRelativePath(result.levelPath, result.metadata.source.manifest);
        input.textureSourceRoots.push_back((sourceManifestPath.parent_path() / "textures").lexically_normal());
    }
    result.runtime = buildMm9DatWorldRuntime(input);
    result.diagnostics = result.runtime.diagnostics;
    return result;
}

std::optional<Mm9DatLevelRuntimeLoadResult> loadMm9DatLevelRuntimeForMap(
    const std::filesystem::path &sourceRoot,
    const std::string &mapId,
    std::string &errorMessage)
{
    const std::filesystem::path levelPath =
        sourceRoot / "assets_dev/worlds/mm9/maps" / (mapId + ".level.yml");
    return loadMm9DatLevelRuntime(levelPath, errorMessage);
}
}
