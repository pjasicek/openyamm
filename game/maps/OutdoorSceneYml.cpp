#include "game/maps/OutdoorSceneYml.h"

#include "game/StringUtils.h"

#include <yaml-cpp/yaml.h>

#include <array>
#include <cctype>
#include <cstring>
#include <exception>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
constexpr size_t FaceAttributeMapVariableCount = 75;
constexpr size_t FaceAttributeDecorVariableCount = 125;
constexpr size_t SpriteObjectContainingItemSize = 0x24;
constexpr size_t ChestItemPayloadSize = 140 * 36;
constexpr int32_t EnvironmentFlagFoggy = 0x01;
constexpr uint32_t EnvironmentFlagRain = 0x01;
constexpr uint32_t EnvironmentFlagSnow = 0x02;
constexpr uint32_t EnvironmentFlagUnderwater = 0x04;
constexpr uint32_t EnvironmentFlagNoTerrain = 0x08;
constexpr uint32_t EnvironmentFlagAlwaysDark = 0x10;
constexpr uint32_t EnvironmentFlagAlwaysLight = 0x20;
constexpr uint32_t EnvironmentFlagAlwaysFoggy = 0x40;
constexpr uint32_t EnvironmentFlagRedFog = 0x80;

template <typename ValueType>
bool readScalarNode(
    const YAML::Node &parentNode,
    const char *key,
    ValueType &value,
    std::string &errorMessage,
    bool required = true)
{
    const YAML::Node childNode = parentNode[key];

    if (!childNode)
    {
        if (required)
        {
            errorMessage = std::string("missing required field: ") + key;
            return false;
        }

        return true;
    }

    if (!childNode.IsScalar())
    {
        errorMessage = std::string("field must be a scalar: ") + key;
        return false;
    }

    try
    {
        value = childNode.as<ValueType>();
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("could not parse field ") + key + ": " + exception.what();
        return false;
    }

    return true;
}

template <typename CoordinateType>
bool parsePositionNode(
    const YAML::Node &node,
    CoordinateType &x,
    CoordinateType &y,
    CoordinateType &z,
    std::string &errorMessage)
{
    if (!node || !node.IsMap())
    {
        errorMessage = "position must be a map";
        return false;
    }

    return readScalarNode(node, "x", x, errorMessage)
        && readScalarNode(node, "y", y, errorMessage)
        && readScalarNode(node, "z", z, errorMessage);
}

bool parseFloat3Node(
    const YAML::Node &node,
    std::array<float, 3> &value,
    const char *pName,
    std::string &errorMessage)
{
    if (!node || !node.IsMap())
    {
        errorMessage = std::string(pName) + " must be a map";
        return false;
    }

    return readScalarNode(node, "x", value[0], errorMessage)
        && readScalarNode(node, "y", value[1], errorMessage)
        && readScalarNode(node, "z", value[2], errorMessage);
}

bool parseFloat4Node(
    const YAML::Node &node,
    std::array<float, 4> &value,
    const char *pName,
    std::string &errorMessage)
{
    if (!node || !node.IsMap())
    {
        errorMessage = std::string(pName) + " must be a map";
        return false;
    }

    return readScalarNode(node, "x", value[0], errorMessage)
        && readScalarNode(node, "y", value[1], errorMessage)
        && readScalarNode(node, "z", value[2], errorMessage)
        && readScalarNode(node, "w", value[3], errorMessage);
}

bool parseUint8TripletNode(
    const YAML::Node &node,
    std::array<uint8_t, 3> &value,
    const char *pName,
    std::string &errorMessage)
{
    if (!node || !node.IsSequence() || node.size() != value.size())
    {
        errorMessage = std::string(pName) + " must be a 3-item sequence";
        return false;
    }

    for (size_t index = 0; index < value.size(); ++index)
    {
        if (!node[index].IsScalar())
        {
            errorMessage = std::string(pName) + " item must be a scalar";
            return false;
        }

        int channel = 0;
        try
        {
            channel = node[index].as<int>();
        }
        catch (const std::exception &exception)
        {
            errorMessage = std::string("could not parse ") + pName + ": " + exception.what();
            return false;
        }

        if (channel < 0 || channel > 255)
        {
            errorMessage = std::string(pName) + " item is outside 0..255";
            return false;
        }

        value[index] = static_cast<uint8_t>(channel);
    }

    return true;
}

bool readOptionalBoolFlag(
    const YAML::Node &flagsNode,
    const char *key,
    bool &value,
    std::string &errorMessage)
{
    return readScalarNode(flagsNode, key, value, errorMessage, false);
}

bool parseEnvironmentFlags(
    const YAML::Node &flagsNode,
    OutdoorSceneEnvironment::Flags &flags,
    std::string &errorMessage)
{
    return readScalarNode(flagsNode, "foggy", flags.foggy, errorMessage)
        && readScalarNode(flagsNode, "raining", flags.raining, errorMessage)
        && readScalarNode(flagsNode, "snowing", flags.snowing, errorMessage)
        && readScalarNode(flagsNode, "underwater", flags.underwater, errorMessage)
        && readScalarNode(flagsNode, "no_terrain", flags.noTerrain, errorMessage)
        && readScalarNode(flagsNode, "always_dark", flags.alwaysDark, errorMessage)
        && readScalarNode(flagsNode, "always_light", flags.alwaysLight, errorMessage)
        && readScalarNode(flagsNode, "always_foggy", flags.alwaysFoggy, errorMessage)
        && readScalarNode(flagsNode, "red_fog", flags.redFog, errorMessage);
}

bool parseOptionalEnvironmentFlags(
    const YAML::Node &flagsNode,
    OutdoorSceneEnvironment::Flags &flags,
    std::string &errorMessage)
{
    return readOptionalBoolFlag(flagsNode, "foggy", flags.foggy, errorMessage)
        && readOptionalBoolFlag(flagsNode, "raining", flags.raining, errorMessage)
        && readOptionalBoolFlag(flagsNode, "snowing", flags.snowing, errorMessage)
        && readOptionalBoolFlag(flagsNode, "underwater", flags.underwater, errorMessage)
        && readOptionalBoolFlag(flagsNode, "no_terrain", flags.noTerrain, errorMessage)
        && readOptionalBoolFlag(flagsNode, "always_dark", flags.alwaysDark, errorMessage)
        && readOptionalBoolFlag(flagsNode, "always_light", flags.alwaysLight, errorMessage)
        && readOptionalBoolFlag(flagsNode, "always_foggy", flags.alwaysFoggy, errorMessage)
        && readOptionalBoolFlag(flagsNode, "red_fog", flags.redFog, errorMessage);
}

void syncEnvironmentRawBits(OutdoorSceneEnvironment &environment)
{
    environment.dayBitsRaw = environment.flags.foggy ? EnvironmentFlagFoggy : 0;
    environment.mapExtraBitsRaw = 0;

    if (environment.flags.raining)
    {
        environment.mapExtraBitsRaw |= EnvironmentFlagRain;
    }

    if (environment.flags.snowing)
    {
        environment.mapExtraBitsRaw |= EnvironmentFlagSnow;
    }

    if (environment.flags.underwater)
    {
        environment.mapExtraBitsRaw |= EnvironmentFlagUnderwater;
    }

    if (environment.flags.noTerrain)
    {
        environment.mapExtraBitsRaw |= EnvironmentFlagNoTerrain;
    }

    if (environment.flags.alwaysDark)
    {
        environment.mapExtraBitsRaw |= EnvironmentFlagAlwaysDark;
    }

    if (environment.flags.alwaysLight)
    {
        environment.mapExtraBitsRaw |= EnvironmentFlagAlwaysLight;
    }

    if (environment.flags.alwaysFoggy)
    {
        environment.mapExtraBitsRaw |= EnvironmentFlagAlwaysFoggy;
    }

    if (environment.flags.redFog)
    {
        environment.mapExtraBitsRaw |= EnvironmentFlagRedFog;
    }
}

bool parseFogMode(
    const YAML::Node &weatherNode,
    OutdoorFogMode &fogMode,
    std::string &errorMessage)
{
    std::string fogModeText = "static";

    if (!readScalarNode(weatherNode, "fog_mode", fogModeText, errorMessage, false))
    {
        return false;
    }

    fogModeText = toLowerCopy(fogModeText);

    if (fogModeText == "static")
    {
        fogMode = OutdoorFogMode::Static;
        return true;
    }

    if (fogModeText == "daily_random")
    {
        fogMode = OutdoorFogMode::DailyRandom;
        return true;
    }

    errorMessage = "environment.weather.fog_mode must be one of: static, daily_random";
    return false;
}

bool parsePrecipitationKind(
    const YAML::Node &weatherNode,
    OutdoorPrecipitationKind &precipitation,
    std::string &errorMessage)
{
    std::string precipitationText = "none";

    if (!readScalarNode(weatherNode, "precipitation", precipitationText, errorMessage, false))
    {
        return false;
    }

    precipitationText = toLowerCopy(precipitationText);

    if (precipitationText == "none")
    {
        precipitation = OutdoorPrecipitationKind::None;
        return true;
    }

    if (precipitationText == "snow")
    {
        precipitation = OutdoorPrecipitationKind::Snow;
        return true;
    }

    if (precipitationText == "rain")
    {
        precipitation = OutdoorPrecipitationKind::Rain;
        return true;
    }

    errorMessage = "environment.weather.precipitation must be one of: none, snow, rain";
    return false;
}

OutdoorSceneTerrainFootstepSoundOverride *findOutdoorTerrainFootstepSoundOverride(
    OutdoorSceneData &sceneData,
    uint8_t tileId)
{
    for (OutdoorSceneTerrainFootstepSoundOverride &overrideEntry : sceneData.terrainFootstepSoundOverrides)
    {
        if (overrideEntry.tileId == tileId)
        {
            return &overrideEntry;
        }
    }

    return nullptr;
}

OutdoorSceneInteractiveFace *findOutdoorInteractiveFace(
    OutdoorSceneData &sceneData,
    size_t bmodelIndex,
    size_t faceIndex)
{
    for (OutdoorSceneInteractiveFace &face : sceneData.interactiveFaces)
    {
        if (face.bmodelIndex == bmodelIndex && face.faceIndex == faceIndex)
        {
            return &face;
        }
    }

    return nullptr;
}

OutdoorSceneBModelFaceSource *findOutdoorBModelFaceSource(
    OutdoorSceneData &sceneData,
    size_t bmodelIndex,
    size_t faceIndex)
{
    for (OutdoorSceneBModelFaceSource &faceSource : sceneData.bmodelFaceSources)
    {
        if (faceSource.bmodelIndex == bmodelIndex && faceSource.faceIndex == faceIndex)
        {
            return &faceSource;
        }
    }

    return nullptr;
}

bool parseOutdoorTerrainFootstepSoundOverride(
    const YAML::Node &overrideNode,
    OutdoorSceneTerrainFootstepSoundOverride &overrideEntry,
    std::string &errorMessage)
{
    if (!overrideNode.IsMap())
    {
        errorMessage = "terrain footstep sound override must be a map";
        return false;
    }

    return readScalarNode(overrideNode, "tile_id", overrideEntry.tileId, errorMessage)
        && readScalarNode(overrideNode, "walk_sound_id", overrideEntry.walkSoundId, errorMessage)
        && readScalarNode(overrideNode, "run_sound_id", overrideEntry.runSoundId, errorMessage);
}

bool parseOutdoorBModelFaceSource(
    const YAML::Node &faceSourceNode,
    OutdoorSceneBModelFaceSource &faceSource,
    std::string &errorMessage)
{
    if (!faceSourceNode.IsMap())
    {
        errorMessage = "bmodel face source entry must be a map";
        return false;
    }

    return readScalarNode(faceSourceNode, "bmodel_index", faceSource.bmodelIndex, errorMessage)
        && readScalarNode(faceSourceNode, "face_index", faceSource.faceIndex, errorMessage)
        && readScalarNode(faceSourceNode, "source_kind", faceSource.sourceKind, errorMessage)
        && readScalarNode(faceSourceNode, "source_model_index", faceSource.sourceModelIndex, errorMessage)
        && readScalarNode(faceSourceNode, "source_model_name", faceSource.sourceModelName, errorMessage)
        && readScalarNode(faceSourceNode, "source_poly_index", faceSource.sourcePolyIndex, errorMessage)
        && readScalarNode(faceSourceNode, "texture_alias", faceSource.textureAlias, errorMessage, false);
}

bool parseOutdoorModelInstance(
    const YAML::Node &modelInstanceNode,
    OutdoorSceneModelInstance &modelInstance,
    std::string &errorMessage)
{
    if (!modelInstanceNode.IsMap())
    {
        errorMessage = "model instance entry must be a map";
        return false;
    }

    return readScalarNode(modelInstanceNode, "instance_id", modelInstance.instanceId, errorMessage)
        && readScalarNode(modelInstanceNode, "source_ref", modelInstance.sourceRef, errorMessage)
        && readScalarNode(modelInstanceNode, "source_kind", modelInstance.sourceKind, errorMessage)
        && readScalarNode(modelInstanceNode, "source_object_index", modelInstance.sourceObjectIndex, errorMessage)
        && readScalarNode(modelInstanceNode, "source_class", modelInstance.sourceClass, errorMessage)
        && readScalarNode(modelInstanceNode, "source_name", modelInstance.sourceName, errorMessage)
        && readScalarNode(modelInstanceNode, "source_model", modelInstance.sourceModel, errorMessage)
        && readScalarNode(modelInstanceNode, "source_skin", modelInstance.sourceSkin, errorMessage, false)
        && readScalarNode(modelInstanceNode, "model_asset", modelInstance.modelAsset, errorMessage, false)
        && readScalarNode(modelInstanceNode, "model_skin_binding", modelInstance.modelSkinBinding, errorMessage, false)
        && parsePositionNode(
            modelInstanceNode["position"],
            modelInstance.x,
            modelInstance.y,
            modelInstance.z,
            errorMessage)
        && parseFloat4Node(
            modelInstanceNode["rotation_quat"],
            modelInstance.rotationQuat,
            "rotation_quat",
            errorMessage)
        && parseFloat3Node(modelInstanceNode["scale"], modelInstance.scale, "scale", errorMessage)
        && readScalarNode(modelInstanceNode, "collision", modelInstance.collisionMode, errorMessage);
}

bool parseOutdoorSceneLight(
    const YAML::Node &lightNode,
    OutdoorSceneLight &light,
    std::string &errorMessage)
{
    if (!lightNode.IsMap())
    {
        errorMessage = "light entry must be a map";
        return false;
    }

    return readScalarNode(lightNode, "source_object_index", light.sourceObjectIndex, errorMessage)
        && readScalarNode(lightNode, "source_class", light.sourceClass, errorMessage)
        && readScalarNode(lightNode, "source_name", light.sourceName, errorMessage)
        && parsePositionNode(lightNode["position"], light.x, light.y, light.z, errorMessage)
        && readScalarNode(lightNode, "radius", light.radius, errorMessage)
        && parseUint8TripletNode(lightNode["color"], light.color, "color", errorMessage)
        && parseUint8TripletNode(lightNode["effective_color"], light.effectiveColor, "effective_color", errorMessage)
        && readScalarNode(lightNode, "type", light.type, errorMessage)
        && readScalarNode(lightNode, "light_objects", light.lightObjects, errorMessage)
        && readScalarNode(lightNode, "fast_light_objects", light.fastLightObjects, errorMessage)
        && readScalarNode(
            lightNode,
            "static_object_light_eligible",
            light.staticObjectLightEligible,
            errorMessage);
}

bool parseOutdoorSceneMechanism(
    const YAML::Node &mechanismNode,
    OutdoorSceneMechanism &mechanism,
    std::string &errorMessage)
{
    if (!mechanismNode.IsMap())
    {
        errorMessage = "mechanism entry must be a map";
        return false;
    }

    if (!readScalarNode(mechanismNode, "mechanism_id", mechanism.mechanismId, errorMessage)
        || !readScalarNode(
            mechanismNode,
            "source_object_index",
            mechanism.sourceObjectIndex,
            errorMessage,
            false)
        || !readScalarNode(mechanismNode, "source_class", mechanism.sourceClass, errorMessage, false)
        || !readScalarNode(mechanismNode, "source_name", mechanism.sourceName, errorMessage, false)
        || !readScalarNode(mechanismNode, "kind", mechanism.kind, errorMessage, false))
    {
        return false;
    }

    const YAML::Node bindingNode = mechanismNode["binding"];
    if (bindingNode && bindingNode.IsMap())
    {
        if (!readScalarNode(bindingNode, "target_kind", mechanism.binding.targetKind, errorMessage, false)
            || !readScalarNode(bindingNode, "bmodel_index", mechanism.binding.bmodelIndex, errorMessage, false)
            || !readScalarNode(bindingNode, "bmodel_name", mechanism.binding.bmodelName, errorMessage, false)
            || !readScalarNode(bindingNode, "confidence", mechanism.binding.confidence, errorMessage, false))
        {
            return false;
        }
    }

    const YAML::Node motionNode = mechanismNode["motion"];
    if (motionNode && motionNode.IsMap())
    {
        const YAML::Node linearNode = motionNode["linear"];
        if (linearNode && linearNode.IsMap())
        {
            const YAML::Node deltaNode = linearNode["delta_openyamm"];
            if (deltaNode)
            {
                if (!parsePositionNode(deltaNode, mechanism.motion.dx, mechanism.motion.dy, mechanism.motion.dz, errorMessage))
                {
                    return false;
                }
                mechanism.motion.hasLinear = true;
            }
        }

        const YAML::Node rotationNode = motionNode["rotation"];
        if (rotationNode && rotationNode.IsMap())
        {
            std::array<float, 3> pivot = {};
            std::array<float, 3> angles = {};
            if (rotationNode["pivot_openyamm"]
                && !parseFloat3Node(rotationNode["pivot_openyamm"], pivot, "pivot_openyamm", errorMessage))
            {
                return false;
            }
            if (rotationNode["rotation_angles_openyamm_deg"]
                && !parseFloat3Node(
                    rotationNode["rotation_angles_openyamm_deg"],
                    angles,
                    "rotation_angles_openyamm_deg",
                    errorMessage))
            {
                return false;
            }
            mechanism.motion.hasRotation = rotationNode["pivot_openyamm"] && rotationNode["rotation_angles_openyamm_deg"];
            mechanism.motion.rotationPivotX = pivot[0];
            mechanism.motion.rotationPivotY = pivot[1];
            mechanism.motion.rotationPivotZ = pivot[2];
            mechanism.motion.rotationDegreesX = angles[0];
            mechanism.motion.rotationDegreesY = angles[1];
            mechanism.motion.rotationDegreesZ = angles[2];
        }

        readScalarNode(motionNode, "move_time_ms", mechanism.motion.moveTimeMs, errorMessage, false);
    }

    const YAML::Node activationNode = mechanismNode["activation"];
    if (activationNode && activationNode.IsMap())
    {
        if (!readScalarNode(activationNode, "start_open", mechanism.activation.startOpen, errorMessage, false)
            || !readScalarNode(activationNode, "locked", mechanism.activation.locked, errorMessage, false))
        {
            return false;
        }
    }

    return true;
}

bool applyOptionalActorCoordinateOverride(
    const YAML::Node &positionNode,
    const char *key,
    int &targetCoordinate,
    bool &hasCoordinateOverride,
    std::string &errorMessage)
{
    const YAML::Node coordinateNode = positionNode[key];

    if (!coordinateNode)
    {
        return true;
    }

    if (!coordinateNode.IsScalar())
    {
        errorMessage = std::string("actor position override coordinate must be scalar: ") + key;
        return false;
    }

    try
    {
        targetCoordinate = coordinateNode.as<int>();
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("could not parse actor position override coordinate ") + key + ": "
            + exception.what();
        return false;
    }

    hasCoordinateOverride = true;
    return true;
}

bool parseOutdoorInteractiveFace(
    const YAML::Node &interactiveFaceNode,
    OutdoorSceneInteractiveFace &face,
    std::string &errorMessage,
    bool allowNamedFaceReference = false)
{
    if (!interactiveFaceNode.IsMap())
    {
        errorMessage = "interactive face entry must be a map";
        return false;
    }

    if (!readScalarNode(interactiveFaceNode, "bmodel_name", face.bmodelName, errorMessage, false)
        || !readScalarNode(interactiveFaceNode, "all_faces", face.allFaces, errorMessage, false))
    {
        return false;
    }

    if (!face.bmodelName.empty())
    {
        if (!allowNamedFaceReference)
        {
            errorMessage = "bmodel_name is only supported in outdoor scene overlays";
            return false;
        }

        if (!face.allFaces
            && !readScalarNode(interactiveFaceNode, "face_index", face.faceIndex, errorMessage))
        {
            return false;
        }
    }
    else if (!readScalarNode(interactiveFaceNode, "bmodel_index", face.bmodelIndex, errorMessage)
        || !readScalarNode(interactiveFaceNode, "face_index", face.faceIndex, errorMessage))
    {
        return false;
    }

    face.hasLegacyAttributes = static_cast<bool>(interactiveFaceNode["legacy_attributes"]);
    face.hasCogNumber = static_cast<bool>(interactiveFaceNode["cog_number"]);
    face.hasCogTriggeredNumber = static_cast<bool>(interactiveFaceNode["cog_triggered_number"]);
    face.hasCogTrigger = static_cast<bool>(interactiveFaceNode["cog_trigger"]);

    if (!allowNamedFaceReference
        && (!face.hasLegacyAttributes
            || !face.hasCogNumber
            || !face.hasCogTriggeredNumber
            || !face.hasCogTrigger))
    {
        errorMessage = "base interactive face entries must provide all legacy face fields";
        return false;
    }

    return readScalarNode(interactiveFaceNode, "legacy_attributes", face.legacyAttributes, errorMessage, false)
        && readScalarNode(interactiveFaceNode, "cog_number", face.cogNumber, errorMessage, false)
        && readScalarNode(interactiveFaceNode, "cog_triggered_number", face.cogTriggeredNumber, errorMessage, false)
        && readScalarNode(interactiveFaceNode, "cog_trigger", face.cogTrigger, errorMessage, false);
}

void mergeOutdoorTerrainFootstepSoundOverride(
    OutdoorSceneData &sceneData,
    const OutdoorSceneTerrainFootstepSoundOverride &sourceOverride)
{
    OutdoorSceneTerrainFootstepSoundOverride *pTargetOverride =
        findOutdoorTerrainFootstepSoundOverride(sceneData, sourceOverride.tileId);

    if (pTargetOverride == nullptr)
    {
        sceneData.terrainFootstepSoundOverrides.push_back(sourceOverride);
        return;
    }

    *pTargetOverride = sourceOverride;
}

void mergeOutdoorInteractiveFace(OutdoorSceneData &sceneData, const OutdoorSceneInteractiveFace &sourceFace)
{
    if (!sourceFace.bmodelName.empty() || sourceFace.allFaces)
    {
        sceneData.interactiveFaces.push_back(sourceFace);
        return;
    }

    OutdoorSceneInteractiveFace *pTargetFace =
        findOutdoorInteractiveFace(sceneData, sourceFace.bmodelIndex, sourceFace.faceIndex);

    if (pTargetFace == nullptr)
    {
        sceneData.interactiveFaces.push_back(sourceFace);
        return;
    }

    *pTargetFace = sourceFace;
}

void mergeOutdoorBModelFaceSource(
    OutdoorSceneData &sceneData,
    const OutdoorSceneBModelFaceSource &sourceFace)
{
    OutdoorSceneBModelFaceSource *pTargetFaceSource =
        findOutdoorBModelFaceSource(sceneData, sourceFace.bmodelIndex, sourceFace.faceIndex);

    if (pTargetFaceSource == nullptr)
    {
        sceneData.bmodelFaceSources.push_back(sourceFace);
        return;
    }

    *pTargetFaceSource = sourceFace;
}

void applyOutdoorInteractiveFaceValues(
    OutdoorBModelFace &targetFace,
    const OutdoorSceneInteractiveFace &sourceFace)
{
    if (sourceFace.hasLegacyAttributes)
    {
        targetFace.attributes = sourceFace.legacyAttributes;
    }

    if (sourceFace.hasCogNumber)
    {
        targetFace.cogNumber = sourceFace.cogNumber;
    }

    if (sourceFace.hasCogTriggeredNumber)
    {
        targetFace.cogTriggeredNumber = sourceFace.cogTriggeredNumber;
    }

    if (sourceFace.hasCogTrigger)
    {
        targetFace.cogTrigger = sourceFace.cogTrigger;
    }
}

bool parseFogDistancesNode(
    const YAML::Node &parentNode,
    const char *key,
    OutdoorFogDistances &distances,
    std::string &errorMessage)
{
    const YAML::Node distancesNode = parentNode[key];

    if (!distancesNode)
    {
        return true;
    }

    if (!distancesNode.IsMap())
    {
        errorMessage = std::string("field must be a map: ") + key;
        return false;
    }

    return readScalarNode(distancesNode, "weak_distance", distances.weakDistance, errorMessage)
        && readScalarNode(distancesNode, "strong_distance", distances.strongDistance, errorMessage);
}

bool parseRgbTripletNode(
    const YAML::Node &parentNode,
    const char *key,
    bool &hasValue,
    std::array<uint8_t, 3> &rgb,
    std::string &errorMessage)
{
    const YAML::Node rgbNode = parentNode[key];

    if (!rgbNode)
    {
        return true;
    }

    if (!rgbNode.IsSequence() || rgbNode.size() != 3)
    {
        errorMessage = std::string("field must be an RGB sequence with exactly 3 values: ") + key;
        return false;
    }

    for (size_t componentIndex = 0; componentIndex < 3; ++componentIndex)
    {
        int componentValue = 0;

        if (!rgbNode[componentIndex].IsScalar())
        {
            errorMessage = std::string("RGB component must be scalar: ") + key;
            return false;
        }

        try
        {
            componentValue = rgbNode[componentIndex].as<int>();
        }
        catch (const YAML::Exception &)
        {
            errorMessage = std::string("RGB component must be an integer: ") + key;
            return false;
        }

        if (componentValue < 0 || componentValue > 255)
        {
            errorMessage = std::string("RGB component out of range 0..255: ") + key;
            return false;
        }

        rgb[componentIndex] = static_cast<uint8_t>(componentValue);
    }

    hasValue = true;
    return true;
}

bool parseWeatherConfig(
    const YAML::Node &environmentNode,
    OutdoorSceneEnvironment::WeatherConfig &weatherConfig,
    std::string &errorMessage)
{
    const YAML::Node weatherNode = environmentNode["weather"];

    if (!weatherNode)
    {
        return true;
    }

    if (!weatherNode.IsMap())
    {
        errorMessage = "environment.weather must be a map";
        return false;
    }

    const YAML::Node dailyFogNode = weatherNode["daily_fog"];

    if (!parseFogMode(weatherNode, weatherConfig.fogMode, errorMessage)
        || !parsePrecipitationKind(weatherNode, weatherConfig.precipitation, errorMessage)
        || !parseRgbTripletNode(
            weatherNode,
            "fog_tint_rgb",
            weatherConfig.hasFogTint,
            weatherConfig.fogTintRgb,
            errorMessage))
    {
        return false;
    }

    if (dailyFogNode)
    {
        if (!dailyFogNode.IsMap())
        {
            errorMessage = "environment.weather.daily_fog must be a map";
            return false;
        }

        if (!readScalarNode(dailyFogNode, "small_chance", weatherConfig.smallFogChance, errorMessage, false)
            || !readScalarNode(dailyFogNode, "average_chance", weatherConfig.averageFogChance, errorMessage, false)
            || !readScalarNode(dailyFogNode, "dense_chance", weatherConfig.denseFogChance, errorMessage, false)
            || !parseFogDistancesNode(dailyFogNode, "small", weatherConfig.smallFog, errorMessage)
            || !parseFogDistancesNode(dailyFogNode, "average", weatherConfig.averageFog, errorMessage)
            || !parseFogDistancesNode(dailyFogNode, "dense", weatherConfig.denseFog, errorMessage))
        {
            return false;
        }
    }

    return true;
}

bool parseHexBytes(
    const std::string &text,
    size_t expectedSize,
    std::vector<uint8_t> &bytes,
    std::string &errorMessage)
{
    bytes.clear();

    if (text.size() != expectedSize * 2)
    {
        std::ostringstream stream;
        stream << "hex payload has wrong length, expected " << (expectedSize * 2)
               << " characters, got " << text.size();
        errorMessage = stream.str();
        return false;
    }

    bytes.reserve(expectedSize);

    auto decodeNibble = [](char character) -> int
    {
        if (character >= '0' && character <= '9')
        {
            return character - '0';
        }

        const char lowered = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));

        if (lowered >= 'a' && lowered <= 'f')
        {
            return 10 + lowered - 'a';
        }

        return -1;
    };

    for (size_t offset = 0; offset < text.size(); offset += 2)
    {
        const int highNibble = decodeNibble(text[offset]);
        const int lowNibble = decodeNibble(text[offset + 1]);

        if (highNibble < 0 || lowNibble < 0)
        {
            errorMessage = "hex payload contains non-hex characters";
            return false;
        }

        bytes.push_back(static_cast<uint8_t>((highNibble << 4) | lowNibble));
    }

    return true;
}

bool parseIntSequence(
    const YAML::Node &node,
    size_t expectedSize,
    std::vector<int> &values,
    std::string &errorMessage)
{
    values.clear();

    if (!node || !node.IsSequence())
    {
        errorMessage = "sequence field must be a YAML sequence";
        return false;
    }

    if (expectedSize != 0 && node.size() != expectedSize)
    {
        std::ostringstream stream;
        stream << "sequence field has wrong length, expected " << expectedSize << ", got " << node.size();
        errorMessage = stream.str();
        return false;
    }

    values.reserve(node.size());

    for (const YAML::Node &entryNode : node)
    {
        if (!entryNode.IsScalar())
        {
            errorMessage = "sequence entry must be scalar";
            return false;
        }

        try
        {
            values.push_back(entryNode.as<int>());
        }
        catch (const std::exception &exception)
        {
            errorMessage = std::string("could not parse sequence entry: ") + exception.what();
            return false;
        }
    }

    return true;
}

void encodeSceneMapExtra(uint32_t mapExtraBitsRaw, int32_t ceiling, std::array<uint8_t, 24> &reservedBytes)
{
    reservedBytes.fill(0);
    std::memcpy(reservedBytes.data(), &mapExtraBitsRaw, sizeof(mapExtraBitsRaw));
    std::memcpy(reservedBytes.data() + sizeof(mapExtraBitsRaw), &ceiling, sizeof(ceiling));
}

uint32_t totalOutdoorFaceCount(const OutdoorMapData &outdoorMapData)
{
    uint32_t faceCount = 0;

    for (const OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        faceCount += static_cast<uint32_t>(bmodel.faces.size());
    }

    return faceCount;
}

}

std::optional<OutdoorSceneData> OutdoorSceneYmlLoader::loadFromText(
    const std::string &yamlText,
    std::string &errorMessage) const
{
    OutdoorSceneData sceneData = {};
    YAML::Node rootNode;

    try
    {
        rootNode = YAML::Load(yamlText);
    }
    catch (const std::exception &exception)
    {
        errorMessage = exception.what();
        return std::nullopt;
    }

    if (!rootNode || !rootNode.IsMap())
    {
        errorMessage = "scene yaml root must be a map";
        return std::nullopt;
    }

    if (!readScalarNode(rootNode, "format_version", sceneData.formatVersion, errorMessage))
    {
        return std::nullopt;
    }

    if (sceneData.formatVersion != 1)
    {
        errorMessage = "unsupported outdoor scene format_version";
        return std::nullopt;
    }

    std::string kind;

    if (!readScalarNode(rootNode, "kind", kind, errorMessage) || toLowerCopy(kind) != "outdoor_scene")
    {
        errorMessage = "kind must be \"outdoor_scene\"";
        return std::nullopt;
    }

    const YAML::Node sourceNode = rootNode["source"];

    if (!sourceNode || !sourceNode.IsMap())
    {
        errorMessage = "source must be a map";
        return std::nullopt;
    }

    if (!readScalarNode(sourceNode, "geometry_file", sceneData.geometryFile, errorMessage))
    {
        return std::nullopt;
    }

    std::string legacyCompanionFile;

    if (readScalarNode(sourceNode, "legacy_companion_file", legacyCompanionFile, errorMessage, false)
        && !legacyCompanionFile.empty())
    {
        sceneData.legacyCompanionFile = legacyCompanionFile;
    }

    std::string sourceMetadataFile;

    if (readScalarNode(sourceNode, "source_metadata_file", sourceMetadataFile, errorMessage, false)
        && !sourceMetadataFile.empty())
    {
        sceneData.sourceMetadataFile = sourceMetadataFile;
    }

    const YAML::Node runtimeRestrictionsNode = rootNode["runtime_restrictions"];

    if (runtimeRestrictionsNode)
    {
        if (!runtimeRestrictionsNode.IsMap())
        {
            errorMessage = "runtime_restrictions must be a map";
            return std::nullopt;
        }

        if (!readScalarNode(
                runtimeRestrictionsNode,
                "allow_save_game",
                sceneData.runtimeRestrictions.allowSaveGame,
                errorMessage,
                false)
            || !readScalarNode(
                runtimeRestrictionsNode,
                "allow_lloyds_beacon",
                sceneData.runtimeRestrictions.allowLloydsBeacon,
                errorMessage,
                false)
            || !readScalarNode(
                runtimeRestrictionsNode,
                "arena",
                sceneData.runtimeRestrictions.isArena,
                errorMessage,
                false))
        {
            return std::nullopt;
        }
    }

    const YAML::Node environmentNode = rootNode["environment"];

    if (!environmentNode || !environmentNode.IsMap())
    {
        errorMessage = "environment must be a map";
        return std::nullopt;
    }

    if (!readScalarNode(environmentNode, "sky_texture", sceneData.environment.skyTexture, errorMessage)
        || !readScalarNode(
            environmentNode,
            "ground_tileset_name",
            sceneData.environment.groundTilesetName,
            errorMessage)
        || !readScalarNode(environmentNode, "master_tile", sceneData.environment.masterTile, errorMessage)
        || !readScalarNode(environmentNode, "day_bits_raw", sceneData.environment.dayBitsRaw, errorMessage)
        || !readScalarNode(
            environmentNode,
            "map_extra_bits_raw",
            sceneData.environment.mapExtraBitsRaw,
            errorMessage)
        || !readScalarNode(environmentNode, "ceiling", sceneData.environment.ceiling, errorMessage))
    {
        return std::nullopt;
    }

    const YAML::Node lookupIndicesNode = environmentNode["tile_set_lookup_indices"];

    if (!lookupIndicesNode || !lookupIndicesNode.IsSequence() || lookupIndicesNode.size() != 4)
    {
        errorMessage = "environment.tile_set_lookup_indices must have 4 entries";
        return std::nullopt;
    }

    for (size_t index = 0; index < sceneData.environment.tileSetLookupIndices.size(); ++index)
    {
        if (!lookupIndicesNode[index].IsScalar())
        {
            errorMessage = "environment.tile_set_lookup_indices entries must be scalar";
            return std::nullopt;
        }

        try
        {
            sceneData.environment.tileSetLookupIndices[index] = lookupIndicesNode[index].as<uint16_t>();
        }
        catch (const std::exception &exception)
        {
            errorMessage = std::string("could not parse tile_set_lookup_indices: ") + exception.what();
            return std::nullopt;
        }
    }

    const YAML::Node flagsNode = environmentNode["flags"];
    const YAML::Node fogNode = environmentNode["fog"];

    if (!flagsNode || !flagsNode.IsMap())
    {
        errorMessage = "environment.flags must be a map";
        return std::nullopt;
    }

    if (!fogNode || !fogNode.IsMap())
    {
        errorMessage = "environment.fog must be a map";
        return std::nullopt;
    }

    if (!readScalarNode(fogNode, "weak_distance", sceneData.environment.fogWeakDistance, errorMessage)
        || !readScalarNode(fogNode, "strong_distance", sceneData.environment.fogStrongDistance, errorMessage))
    {
        return std::nullopt;
    }

    if (!parseEnvironmentFlags(flagsNode, sceneData.environment.flags, errorMessage))
    {
        return std::nullopt;
    }
    syncEnvironmentRawBits(sceneData.environment);

    if (!parseWeatherConfig(environmentNode, sceneData.environment.weather, errorMessage))
    {
        return std::nullopt;
    }

    const YAML::Node terrainNode = rootNode["terrain"];
    const YAML::Node terrainOverridesNode = terrainNode ? terrainNode["attribute_overrides"] : YAML::Node();
    const YAML::Node terrainFootstepSoundOverridesNode =
        terrainNode ? terrainNode["footstep_sound_overrides"] : YAML::Node();

    if (!terrainNode || !terrainNode.IsMap() || !terrainOverridesNode || !terrainOverridesNode.IsSequence())
    {
        errorMessage = "terrain.attribute_overrides must be a sequence";
        return std::nullopt;
    }

    sceneData.terrainAttributeOverrides.reserve(terrainOverridesNode.size());

    for (const YAML::Node &overrideNode : terrainOverridesNode)
    {
        if (!overrideNode.IsMap())
        {
            errorMessage = "terrain attribute override must be a map";
            return std::nullopt;
        }

        OutdoorSceneTerrainAttributeOverride overrideEntry = {};
        bool burn = false;
        bool water = false;

        if (!readScalarNode(overrideNode, "x", overrideEntry.x, errorMessage)
            || !readScalarNode(overrideNode, "y", overrideEntry.y, errorMessage)
            || !readScalarNode(overrideNode, "legacy_attributes", overrideEntry.legacyAttributes, errorMessage)
            || !readScalarNode(overrideNode, "burn", burn, errorMessage)
            || !readScalarNode(overrideNode, "water", water, errorMessage))
        {
            return std::nullopt;
        }

        if ((overrideEntry.legacyAttributes & 0x01) != (burn ? 0x01 : 0x00))
        {
            errorMessage = "terrain burn flag does not match legacy_attributes";
            return std::nullopt;
        }

        if ((overrideEntry.legacyAttributes & 0x02) != (water ? 0x02 : 0x00))
        {
            errorMessage = "terrain water flag does not match legacy_attributes";
            return std::nullopt;
        }

        sceneData.terrainAttributeOverrides.push_back(overrideEntry);
    }

    if (terrainFootstepSoundOverridesNode)
    {
        if (!terrainFootstepSoundOverridesNode.IsSequence())
        {
            errorMessage = "terrain.footstep_sound_overrides must be a sequence";
            return std::nullopt;
        }

        sceneData.terrainFootstepSoundOverrides.reserve(terrainFootstepSoundOverridesNode.size());

        for (const YAML::Node &overrideNode : terrainFootstepSoundOverridesNode)
        {
            OutdoorSceneTerrainFootstepSoundOverride overrideEntry = {};

            if (!parseOutdoorTerrainFootstepSoundOverride(overrideNode, overrideEntry, errorMessage))
            {
                return std::nullopt;
            }

            sceneData.terrainFootstepSoundOverrides.push_back(overrideEntry);
        }
    }

    const YAML::Node bmodelFacesNode = rootNode["bmodel_faces"];
    const YAML::Node faceSourcesNode = bmodelFacesNode ? bmodelFacesNode["source_faces"] : YAML::Node();
    const YAML::Node interactiveFacesNode = bmodelFacesNode ? bmodelFacesNode["interactive_faces"] : YAML::Node();

    if (!bmodelFacesNode || !bmodelFacesNode.IsMap() || !interactiveFacesNode || !interactiveFacesNode.IsSequence())
    {
        errorMessage = "bmodel_faces.interactive_faces must be a sequence";
        return std::nullopt;
    }

    if (faceSourcesNode)
    {
        if (!faceSourcesNode.IsSequence())
        {
            errorMessage = "bmodel_faces.source_faces must be a sequence";
            return std::nullopt;
        }

        sceneData.bmodelFaceSources.reserve(faceSourcesNode.size());

        for (const YAML::Node &faceSourceNode : faceSourcesNode)
        {
            OutdoorSceneBModelFaceSource faceSource = {};

            if (!parseOutdoorBModelFaceSource(faceSourceNode, faceSource, errorMessage))
            {
                return std::nullopt;
            }

            sceneData.bmodelFaceSources.push_back(std::move(faceSource));
        }
    }

    sceneData.interactiveFaces.reserve(interactiveFacesNode.size());

    for (const YAML::Node &interactiveFaceNode : interactiveFacesNode)
    {
        OutdoorSceneInteractiveFace face = {};

        if (!parseOutdoorInteractiveFace(interactiveFaceNode, face, errorMessage))
        {
            return std::nullopt;
        }

        sceneData.interactiveFaces.push_back(face);
    }

    const YAML::Node entitiesNode = rootNode["entities"];

    if (!entitiesNode || !entitiesNode.IsSequence())
    {
        errorMessage = "entities must be a sequence";
        return std::nullopt;
    }

    sceneData.entities.reserve(entitiesNode.size());

    for (const YAML::Node &entityNode : entitiesNode)
    {
        if (!entityNode.IsMap())
        {
            errorMessage = "entity entry must be a map";
            return std::nullopt;
        }

        OutdoorSceneEntity entity = {};

        if (!readScalarNode(entityNode, "entity_index", entity.entityIndex, errorMessage)
            || !readScalarNode(entityNode, "name", entity.entity.name, errorMessage)
            || !readScalarNode(entityNode, "decoration_list_id", entity.entity.decorationListId, errorMessage)
            || !readScalarNode(entityNode, "ai_attributes", entity.entity.aiAttributes, errorMessage)
            || !readScalarNode(entityNode, "facing", entity.entity.facing, errorMessage)
            || !readScalarNode(entityNode, "event_id_primary", entity.entity.eventIdPrimary, errorMessage)
            || !readScalarNode(entityNode, "event_id_secondary", entity.entity.eventIdSecondary, errorMessage)
            || !readScalarNode(entityNode, "variable_primary", entity.entity.variablePrimary, errorMessage)
            || !readScalarNode(entityNode, "variable_secondary", entity.entity.variableSecondary, errorMessage)
            || !readScalarNode(entityNode, "special_trigger", entity.entity.specialTrigger, errorMessage)
            || !readScalarNode(
                entityNode,
                "initial_decoration_flag",
                entity.initialDecorationFlag,
                errorMessage)
            || !parsePositionNode(
                entityNode["position"],
                entity.entity.x,
                entity.entity.y,
                entity.entity.z,
                errorMessage))
        {
            return std::nullopt;
        }

        sceneData.entities.push_back(std::move(entity));
    }

    const YAML::Node spawnsNode = rootNode["spawns"];

    if (!spawnsNode || !spawnsNode.IsSequence())
    {
        errorMessage = "spawns must be a sequence";
        return std::nullopt;
    }

    sceneData.spawns.reserve(spawnsNode.size());

    for (const YAML::Node &spawnNode : spawnsNode)
    {
        if (!spawnNode.IsMap())
        {
            errorMessage = "spawn entry must be a map";
            return std::nullopt;
        }

        OutdoorSceneSpawn spawn = {};

        if (!readScalarNode(spawnNode, "spawn_index", spawn.spawnIndex, errorMessage)
            || !readScalarNode(spawnNode, "radius", spawn.spawn.radius, errorMessage)
            || !readScalarNode(spawnNode, "type_id", spawn.spawn.typeId, errorMessage)
            || !readScalarNode(spawnNode, "index", spawn.spawn.index, errorMessage)
            || !readScalarNode(spawnNode, "attributes", spawn.spawn.attributes, errorMessage)
            || !readScalarNode(spawnNode, "group", spawn.spawn.group, errorMessage)
            || !parsePositionNode(
                spawnNode["position"],
                spawn.spawn.x,
                spawn.spawn.y,
                spawn.spawn.z,
                errorMessage))
        {
            return std::nullopt;
        }

        sceneData.spawns.push_back(std::move(spawn));
    }

    const YAML::Node lightsNode = rootNode["lights"];

    if (lightsNode)
    {
        if (!lightsNode.IsSequence())
        {
            errorMessage = "lights must be a sequence";
            return std::nullopt;
        }

        sceneData.lights.reserve(lightsNode.size());

        for (const YAML::Node &lightNode : lightsNode)
        {
            OutdoorSceneLight light = {};

            if (!parseOutdoorSceneLight(lightNode, light, errorMessage))
            {
                return std::nullopt;
            }

            sceneData.lights.push_back(std::move(light));
        }
    }

    const YAML::Node modelInstancesNode = rootNode["model_instances"];

    if (modelInstancesNode)
    {
        if (!modelInstancesNode.IsSequence())
        {
            errorMessage = "model_instances must be a sequence";
            return std::nullopt;
        }

        sceneData.modelInstances.reserve(modelInstancesNode.size());

        for (const YAML::Node &modelInstanceNode : modelInstancesNode)
        {
            OutdoorSceneModelInstance modelInstance = {};

            if (!parseOutdoorModelInstance(modelInstanceNode, modelInstance, errorMessage))
            {
                return std::nullopt;
            }

            sceneData.modelInstances.push_back(std::move(modelInstance));
        }
    }

    const YAML::Node mechanismsNode = rootNode["mechanisms"];

    if (mechanismsNode)
    {
        if (!mechanismsNode.IsSequence())
        {
            errorMessage = "mechanisms must be a sequence";
            return std::nullopt;
        }

        sceneData.mechanisms.reserve(mechanismsNode.size());

        for (const YAML::Node &mechanismNode : mechanismsNode)
        {
            OutdoorSceneMechanism mechanism = {};

            if (!parseOutdoorSceneMechanism(mechanismNode, mechanism, errorMessage))
            {
                return std::nullopt;
            }

            sceneData.mechanisms.push_back(std::move(mechanism));
        }
    }

    const YAML::Node initialStateNode = rootNode["initial_state"];
    const YAML::Node locationNode = initialStateNode ? initialStateNode["location"] : YAML::Node();
    const YAML::Node faceAttributeOverridesNode =
        initialStateNode ? initialStateNode["face_attribute_overrides"] : YAML::Node();
    const YAML::Node actorsNode = initialStateNode ? initialStateNode["actors"] : YAML::Node();
    const YAML::Node spriteObjectsNode = initialStateNode ? initialStateNode["sprite_objects"] : YAML::Node();
    const YAML::Node chestsNode = initialStateNode ? initialStateNode["chests"] : YAML::Node();
    const YAML::Node variablesNode = initialStateNode ? initialStateNode["variables"] : YAML::Node();

    if (!initialStateNode || !initialStateNode.IsMap()
        || !locationNode || !locationNode.IsMap()
        || !faceAttributeOverridesNode || !faceAttributeOverridesNode.IsSequence()
        || !actorsNode || !actorsNode.IsSequence()
        || !spriteObjectsNode || !spriteObjectsNode.IsSequence()
        || !chestsNode || !chestsNode.IsSequence()
        || !variablesNode || !variablesNode.IsMap())
    {
        errorMessage = "initial_state has invalid structure";
        return std::nullopt;
    }

    if (!readScalarNode(locationNode, "respawn_count", sceneData.initialState.locationInfo.respawnCount, errorMessage)
        || !readScalarNode(
            locationNode,
            "last_respawn_day",
            sceneData.initialState.locationInfo.lastRespawnDay,
            errorMessage)
        || !readScalarNode(locationNode, "reputation", sceneData.initialState.locationInfo.reputation, errorMessage)
        || !readScalarNode(
            locationNode,
            "alert_status",
            sceneData.initialState.locationInfo.alertStatus,
            errorMessage))
    {
        return std::nullopt;
    }

    sceneData.initialState.faceAttributeOverrides.reserve(faceAttributeOverridesNode.size());

    for (const YAML::Node &overrideNode : faceAttributeOverridesNode)
    {
        if (!overrideNode.IsMap())
        {
            errorMessage = "face attribute override entry must be a map";
            return std::nullopt;
        }

        OutdoorSceneFaceAttributeOverride faceOverride = {};

        if (!readScalarNode(overrideNode, "bmodel_index", faceOverride.bmodelIndex, errorMessage)
            || !readScalarNode(overrideNode, "face_index", faceOverride.faceIndex, errorMessage)
            || !readScalarNode(overrideNode, "legacy_attributes", faceOverride.legacyAttributes, errorMessage))
        {
            return std::nullopt;
        }

        sceneData.initialState.faceAttributeOverrides.push_back(faceOverride);
    }

    sceneData.initialState.actors.reserve(actorsNode.size());

    for (const YAML::Node &actorNode : actorsNode)
    {
        if (!actorNode.IsMap())
        {
            errorMessage = "actor entry must be a map";
            return std::nullopt;
        }

        MapDeltaActor actor = {};

        if (!readScalarNode(actorNode, "name", actor.name, errorMessage)
            || !readScalarNode(actorNode, "npc_id", actor.npcId, errorMessage)
            || !readScalarNode(actorNode, "attributes", actor.attributes, errorMessage)
            || !readScalarNode(actorNode, "hp", actor.hp, errorMessage)
            || !readScalarNode(actorNode, "hostility_type", actor.hostilityType, errorMessage)
            || !readScalarNode(actorNode, "monster_info_id", actor.monsterInfoId, errorMessage)
            || !readScalarNode(actorNode, "monster_id", actor.monsterId, errorMessage)
            || !readScalarNode(actorNode, "radius", actor.radius, errorMessage)
            || !readScalarNode(actorNode, "height", actor.height, errorMessage)
            || !readScalarNode(actorNode, "move_speed", actor.moveSpeed, errorMessage)
            || !readScalarNode(actorNode, "sector_id", actor.sectorId, errorMessage)
            || !readScalarNode(
                actorNode,
                "current_action_animation",
                actor.currentActionAnimation,
                errorMessage)
            || !readScalarNode(actorNode, "group", actor.group, errorMessage)
            || !readScalarNode(actorNode, "ally", actor.ally, errorMessage)
            || !readScalarNode(actorNode, "unique_name_index", actor.uniqueNameIndex, errorMessage)
            || !parsePositionNode(actorNode["position"], actor.x, actor.y, actor.z, errorMessage))
        {
            return std::nullopt;
        }

        if (!readScalarNode(actorNode, "carried_item_id", actor.carriedItemId, errorMessage, false))
        {
            actor.carriedItemId = 0;
        }

        const YAML::Node spriteIdsNode = actorNode["sprite_ids"];

        if (!spriteIdsNode || !spriteIdsNode.IsSequence() || spriteIdsNode.size() != actor.spriteIds.size())
        {
            errorMessage = "actor.sprite_ids must have exactly 4 entries";
            return std::nullopt;
        }

        for (size_t spriteIndex = 0; spriteIndex < actor.spriteIds.size(); ++spriteIndex)
        {
            if (!spriteIdsNode[spriteIndex].IsScalar())
            {
                errorMessage = "actor sprite_ids entries must be scalar";
                return std::nullopt;
            }

            try
            {
                actor.spriteIds[spriteIndex] = spriteIdsNode[spriteIndex].as<uint16_t>();
            }
            catch (const std::exception &exception)
            {
                errorMessage = std::string("could not parse actor sprite id: ") + exception.what();
                return std::nullopt;
            }
        }

        sceneData.initialState.actors.push_back(std::move(actor));
    }

    sceneData.initialState.spriteObjects.reserve(spriteObjectsNode.size());

    for (const YAML::Node &spriteObjectNode : spriteObjectsNode)
    {
        if (!spriteObjectNode.IsMap())
        {
            errorMessage = "sprite object entry must be a map";
            return std::nullopt;
        }

        MapDeltaSpriteObject spriteObject = {};
        std::string rawContainingItemHex;

        if (!readScalarNode(spriteObjectNode, "sprite_id", spriteObject.spriteId, errorMessage)
            || !readScalarNode(
                spriteObjectNode,
                "object_description_id",
                spriteObject.objectDescriptionId,
                errorMessage)
            || !readScalarNode(spriteObjectNode, "yaw_angle", spriteObject.yawAngle, errorMessage)
            || !readScalarNode(spriteObjectNode, "sound_id", spriteObject.soundId, errorMessage)
            || !readScalarNode(spriteObjectNode, "attributes", spriteObject.attributes, errorMessage)
            || !readScalarNode(spriteObjectNode, "sector_id", spriteObject.sectorId, errorMessage)
            || !readScalarNode(
                spriteObjectNode,
                "time_since_created",
                spriteObject.timeSinceCreated,
                errorMessage)
            || !readScalarNode(
                spriteObjectNode,
                "temporary_lifetime",
                spriteObject.temporaryLifetime,
                errorMessage)
            || !readScalarNode(
                spriteObjectNode,
                "glow_radius_multiplier",
                spriteObject.glowRadiusMultiplier,
                errorMessage)
            || !readScalarNode(spriteObjectNode, "spell_id", spriteObject.spellId, errorMessage)
            || !readScalarNode(spriteObjectNode, "spell_level", spriteObject.spellLevel, errorMessage)
            || !readScalarNode(spriteObjectNode, "spell_skill", spriteObject.spellSkill, errorMessage)
            || !readScalarNode(spriteObjectNode, "field54", spriteObject.field54, errorMessage)
            || !readScalarNode(
                spriteObjectNode,
                "spell_caster_pid",
                spriteObject.spellCasterPid,
                errorMessage)
            || !readScalarNode(
                spriteObjectNode,
                "spell_target_pid",
                spriteObject.spellTargetPid,
                errorMessage)
            || !readScalarNode(spriteObjectNode, "lod_distance", spriteObject.lodDistance, errorMessage)
            || !readScalarNode(
                spriteObjectNode,
                "spell_caster_ability",
                spriteObject.spellCasterAbility,
                errorMessage)
            || !readScalarNode(
                spriteObjectNode,
                "raw_containing_item_hex",
                rawContainingItemHex,
                errorMessage)
            || !parsePositionNode(
                spriteObjectNode["position"],
                spriteObject.x,
                spriteObject.y,
                spriteObject.z,
                errorMessage)
            || !parsePositionNode(
                spriteObjectNode["velocity"],
                spriteObject.velocityX,
                spriteObject.velocityY,
                spriteObject.velocityZ,
                errorMessage)
            || !parsePositionNode(
                spriteObjectNode["initial_position"],
                spriteObject.initialX,
                spriteObject.initialY,
                spriteObject.initialZ,
                errorMessage))
        {
            return std::nullopt;
        }

        if (!parseHexBytes(
                rawContainingItemHex,
                SpriteObjectContainingItemSize,
                spriteObject.rawContainingItem,
                errorMessage))
        {
            return std::nullopt;
        }

        sceneData.initialState.spriteObjects.push_back(std::move(spriteObject));
    }

    sceneData.initialState.chests.reserve(chestsNode.size());

    for (const YAML::Node &chestNode : chestsNode)
    {
        if (!chestNode.IsMap())
        {
            errorMessage = "chest entry must be a map";
            return std::nullopt;
        }

        MapDeltaChest chest = {};
        std::string rawItemsHex;
        std::vector<uint8_t> rawItems;
        std::vector<int> inventoryMatrixValues;

        if (!readScalarNode(chestNode, "chest_type_id", chest.chestTypeId, errorMessage)
            || !readScalarNode(chestNode, "flags", chest.flags, errorMessage)
            || !readScalarNode(chestNode, "raw_items_hex", rawItemsHex, errorMessage)
            || !parseIntSequence(
                chestNode["inventory_matrix"],
                140,
                inventoryMatrixValues,
                errorMessage))
        {
            return std::nullopt;
        }

        if (!parseHexBytes(rawItemsHex, ChestItemPayloadSize, rawItems, errorMessage))
        {
            return std::nullopt;
        }

        chest.rawItems = std::move(rawItems);
        chest.inventoryMatrix.reserve(inventoryMatrixValues.size());

        for (int value : inventoryMatrixValues)
        {
            chest.inventoryMatrix.push_back(static_cast<int16_t>(value));
        }

        sceneData.initialState.chests.push_back(std::move(chest));
    }

    std::vector<int> mapVariableValues;
    std::vector<int> decorVariableValues;

    if (!parseIntSequence(variablesNode["map"], FaceAttributeMapVariableCount, mapVariableValues, errorMessage)
        || !parseIntSequence(
            variablesNode["decor"],
            FaceAttributeDecorVariableCount,
            decorVariableValues,
            errorMessage))
    {
        return std::nullopt;
    }

    for (size_t index = 0; index < sceneData.initialState.eventVariables.mapVars.size(); ++index)
    {
        sceneData.initialState.eventVariables.mapVars[index] = static_cast<uint8_t>(mapVariableValues[index]);
    }

    for (size_t index = 0; index < sceneData.initialState.eventVariables.decorVars.size(); ++index)
    {
        sceneData.initialState.eventVariables.decorVars[index] = static_cast<uint8_t>(decorVariableValues[index]);
    }

    return sceneData;
}

bool OutdoorSceneYmlLoader::applyOverlayFromText(
    OutdoorSceneData &sceneData,
    const std::string &yamlText,
    std::string &errorMessage) const
{
    YAML::Node rootNode;

    try
    {
        rootNode = YAML::Load(yamlText);
    }
    catch (const std::exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }

    if (!rootNode || !rootNode.IsMap())
    {
        errorMessage = "scene overlay yaml root must be a map";
        return false;
    }

    int formatVersion = 0;

    if (!readScalarNode(rootNode, "format_version", formatVersion, errorMessage))
    {
        return false;
    }

    if (formatVersion != 1)
    {
        errorMessage = "unsupported outdoor scene overlay format_version";
        return false;
    }

    std::string kind;

    if (!readScalarNode(rootNode, "kind", kind, errorMessage) || toLowerCopy(kind) != "outdoor_scene_overlay")
    {
        errorMessage = "kind must be \"outdoor_scene_overlay\"";
        return false;
    }

    const YAML::Node sourceNode = rootNode["source"];

    if (sourceNode)
    {
        if (!sourceNode.IsMap())
        {
            errorMessage = "source must be a map";
            return false;
        }

        std::string geometryFile;

        if (!readScalarNode(sourceNode, "geometry_file", geometryFile, errorMessage, false))
        {
            return false;
        }

        if (!geometryFile.empty() && toLowerCopy(geometryFile) != toLowerCopy(sceneData.geometryFile))
        {
            errorMessage = "scene overlay geometry_file does not match base scene";
            return false;
        }
    }

    const YAML::Node environmentNode = rootNode["environment"];

    if (environmentNode)
    {
        if (!environmentNode.IsMap())
        {
            errorMessage = "environment must be a map";
            return false;
        }

        if (!readScalarNode(environmentNode, "sky_texture", sceneData.environment.skyTexture, errorMessage, false)
            || !readScalarNode(
                environmentNode,
                "ground_tileset_name",
                sceneData.environment.groundTilesetName,
                errorMessage,
                false)
            || !readScalarNode(environmentNode, "master_tile", sceneData.environment.masterTile, errorMessage, false)
            || !readScalarNode(environmentNode, "ceiling", sceneData.environment.ceiling, errorMessage, false))
        {
            return false;
        }

        const YAML::Node lookupIndicesNode = environmentNode["tile_set_lookup_indices"];

        if (lookupIndicesNode)
        {
            if (!lookupIndicesNode.IsSequence() || lookupIndicesNode.size() != 4)
            {
                errorMessage = "environment.tile_set_lookup_indices must have 4 entries";
                return false;
            }

            for (size_t index = 0; index < sceneData.environment.tileSetLookupIndices.size(); ++index)
            {
                if (!lookupIndicesNode[index].IsScalar())
                {
                    errorMessage = "environment.tile_set_lookup_indices entries must be scalar";
                    return false;
                }

                try
                {
                    sceneData.environment.tileSetLookupIndices[index] = lookupIndicesNode[index].as<uint16_t>();
                }
                catch (const std::exception &exception)
                {
                    errorMessage = std::string("could not parse tile_set_lookup_indices: ") + exception.what();
                    return false;
                }
            }
        }

        const YAML::Node flagsNode = environmentNode["flags"];

        if (flagsNode)
        {
            if (!flagsNode.IsMap())
            {
                errorMessage = "environment.flags must be a map";
                return false;
            }

            if (!parseOptionalEnvironmentFlags(flagsNode, sceneData.environment.flags, errorMessage))
            {
                return false;
            }

            syncEnvironmentRawBits(sceneData.environment);
        }

        const YAML::Node fogNode = environmentNode["fog"];

        if (fogNode)
        {
            if (!fogNode.IsMap())
            {
                errorMessage = "environment.fog must be a map";
                return false;
            }

            if (!readScalarNode(
                    fogNode,
                    "weak_distance",
                    sceneData.environment.fogWeakDistance,
                    errorMessage,
                    false)
                || !readScalarNode(
                    fogNode,
                    "strong_distance",
                    sceneData.environment.fogStrongDistance,
                    errorMessage,
                    false))
            {
                return false;
            }
        }

        if (!parseWeatherConfig(environmentNode, sceneData.environment.weather, errorMessage))
        {
            return false;
        }
    }

    const YAML::Node runtimeRestrictionsNode = rootNode["runtime_restrictions"];

    if (runtimeRestrictionsNode)
    {
        if (!runtimeRestrictionsNode.IsMap())
        {
            errorMessage = "runtime_restrictions must be a map";
            return false;
        }

        if (!readScalarNode(
                runtimeRestrictionsNode,
                "allow_save_game",
                sceneData.runtimeRestrictions.allowSaveGame,
                errorMessage,
                false)
            || !readScalarNode(
                runtimeRestrictionsNode,
                "allow_lloyds_beacon",
                sceneData.runtimeRestrictions.allowLloydsBeacon,
                errorMessage,
                false)
            || !readScalarNode(
                runtimeRestrictionsNode,
                "arena",
                sceneData.runtimeRestrictions.isArena,
                errorMessage,
                false))
        {
            return false;
        }
    }

    const YAML::Node terrainNode = rootNode["terrain"];

    if (terrainNode)
    {
        if (!terrainNode.IsMap())
        {
            errorMessage = "terrain must be a map";
            return false;
        }

        const YAML::Node terrainFootstepSoundOverridesNode = terrainNode["footstep_sound_overrides"];

        if (terrainFootstepSoundOverridesNode)
        {
            if (!terrainFootstepSoundOverridesNode.IsSequence())
            {
                errorMessage = "terrain.footstep_sound_overrides must be a sequence";
                return false;
            }

            for (const YAML::Node &overrideNode : terrainFootstepSoundOverridesNode)
            {
                OutdoorSceneTerrainFootstepSoundOverride overrideEntry = {};

                if (!parseOutdoorTerrainFootstepSoundOverride(overrideNode, overrideEntry, errorMessage))
                {
                    return false;
                }

                mergeOutdoorTerrainFootstepSoundOverride(sceneData, overrideEntry);
            }
        }
    }

    const YAML::Node bmodelFacesNode = rootNode["bmodel_faces"];

    if (bmodelFacesNode)
    {
        if (!bmodelFacesNode.IsMap())
        {
            errorMessage = "bmodel_faces must be a map";
            return false;
        }

        const YAML::Node faceSourcesNode = bmodelFacesNode["source_faces"];

        if (faceSourcesNode)
        {
            if (!faceSourcesNode.IsSequence())
            {
                errorMessage = "bmodel_faces.source_faces must be a sequence";
                return false;
            }

            for (const YAML::Node &faceSourceNode : faceSourcesNode)
            {
                OutdoorSceneBModelFaceSource faceSource = {};

                if (!parseOutdoorBModelFaceSource(faceSourceNode, faceSource, errorMessage))
                {
                    return false;
                }

                mergeOutdoorBModelFaceSource(sceneData, faceSource);
            }
        }

        const YAML::Node interactiveFacesNode = bmodelFacesNode["interactive_faces"];

        if (interactiveFacesNode)
        {
            if (!interactiveFacesNode.IsSequence())
            {
                errorMessage = "bmodel_faces.interactive_faces must be a sequence";
                return false;
            }

            for (const YAML::Node &interactiveFaceNode : interactiveFacesNode)
            {
                OutdoorSceneInteractiveFace face = {};

                if (!parseOutdoorInteractiveFace(interactiveFaceNode, face, errorMessage, true))
                {
                    return false;
                }

                mergeOutdoorInteractiveFace(sceneData, face);
            }
        }
    }

    const YAML::Node initialStateNode = rootNode["initial_state"];

    if (initialStateNode)
    {
        if (!initialStateNode.IsMap())
        {
            errorMessage = "initial_state must be a map";
            return false;
        }

        const YAML::Node actorPositionOverridesNode = initialStateNode["actor_position_overrides"];

        if (actorPositionOverridesNode)
        {
            if (!actorPositionOverridesNode.IsSequence())
            {
                errorMessage = "initial_state.actor_position_overrides must be a sequence";
                return false;
            }

            for (const YAML::Node &overrideNode : actorPositionOverridesNode)
            {
                if (!overrideNode.IsMap())
                {
                    errorMessage = "actor position override entry must be a map";
                    return false;
                }

                size_t actorIndex = 0;

                if (!readScalarNode(overrideNode, "actor_index", actorIndex, errorMessage))
                {
                    return false;
                }

                if (actorIndex >= sceneData.initialState.actors.size())
                {
                    errorMessage = "actor position override actor_index is out of range";
                    return false;
                }

                const YAML::Node positionNode = overrideNode["position"];

                if (!positionNode || !positionNode.IsMap())
                {
                    errorMessage = "actor position override position must be a map";
                    return false;
                }

                bool hasCoordinateOverride = false;
                MapDeltaActor &actor = sceneData.initialState.actors[actorIndex];

                if (!applyOptionalActorCoordinateOverride(
                        positionNode,
                        "x",
                        actor.x,
                        hasCoordinateOverride,
                        errorMessage)
                    || !applyOptionalActorCoordinateOverride(
                        positionNode,
                        "y",
                        actor.y,
                        hasCoordinateOverride,
                        errorMessage)
                    || !applyOptionalActorCoordinateOverride(
                        positionNode,
                        "z",
                        actor.z,
                        hasCoordinateOverride,
                        errorMessage))
                {
                    return false;
                }

                if (!hasCoordinateOverride)
                {
                    errorMessage = "actor position override position must include at least one coordinate";
                    return false;
                }
            }
        }

        const YAML::Node actorNpcIdOverridesNode = initialStateNode["actor_npc_id_overrides"];

        if (actorNpcIdOverridesNode)
        {
            if (!actorNpcIdOverridesNode.IsSequence())
            {
                errorMessage = "initial_state.actor_npc_id_overrides must be a sequence";
                return false;
            }

            for (const YAML::Node &overrideNode : actorNpcIdOverridesNode)
            {
                if (!overrideNode.IsMap())
                {
                    errorMessage = "actor npc id override entry must be a map";
                    return false;
                }

                size_t actorIndex = 0;
                int16_t npcId = 0;

                if (!readScalarNode(overrideNode, "actor_index", actorIndex, errorMessage)
                    || !readScalarNode(overrideNode, "npc_id", npcId, errorMessage))
                {
                    return false;
                }

                if (actorIndex >= sceneData.initialState.actors.size())
                {
                    errorMessage = "actor npc id override actor_index is out of range";
                    return false;
                }

                sceneData.initialState.actors[actorIndex].npcId = npcId;
            }
        }
    }

    return true;
}

bool OutdoorSceneYmlLoader::applySourceMetadataFromText(
    OutdoorSceneData &sceneData,
    const std::string &yamlText,
    std::string &errorMessage) const
{
    YAML::Node rootNode;

    try
    {
        rootNode = YAML::Load(yamlText);
    }
    catch (const std::exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }

    if (!rootNode || !rootNode.IsMap())
    {
        errorMessage = "source metadata yaml root must be a map";
        return false;
    }

    int formatVersion = 0;

    if (!readScalarNode(rootNode, "format_version", formatVersion, errorMessage))
    {
        return false;
    }

    if (formatVersion != 1)
    {
        errorMessage = "unsupported outdoor source metadata format_version";
        return false;
    }

    std::string kind;

    if (!readScalarNode(rootNode, "kind", kind, errorMessage) || toLowerCopy(kind) != "outdoor_source_metadata")
    {
        errorMessage = "kind must be \"outdoor_source_metadata\"";
        return false;
    }

    const YAML::Node sourceNode = rootNode["source"];

    if (sourceNode)
    {
        if (!sourceNode.IsMap())
        {
            errorMessage = "source must be a map";
            return false;
        }

        std::string geometryFile;

        if (!readScalarNode(sourceNode, "geometry_file", geometryFile, errorMessage, false))
        {
            return false;
        }

        if (!geometryFile.empty() && toLowerCopy(geometryFile) != toLowerCopy(sceneData.geometryFile))
        {
            errorMessage = "source metadata geometry_file does not match base scene";
            return false;
        }
    }

    const YAML::Node bmodelFacesNode = rootNode["bmodel_faces"];

    if (bmodelFacesNode)
    {
        if (!bmodelFacesNode.IsMap())
        {
            errorMessage = "bmodel_faces must be a map";
            return false;
        }

        const YAML::Node faceSourcesNode = bmodelFacesNode["source_faces"];

        if (faceSourcesNode)
        {
            if (!faceSourcesNode.IsSequence())
            {
                errorMessage = "bmodel_faces.source_faces must be a sequence";
                return false;
            }

            for (const YAML::Node &faceSourceNode : faceSourcesNode)
            {
                OutdoorSceneBModelFaceSource faceSource = {};

                if (!parseOutdoorBModelFaceSource(faceSourceNode, faceSource, errorMessage))
                {
                    return false;
                }

                mergeOutdoorBModelFaceSource(sceneData, faceSource);
            }
        }
    }

    return true;
}

bool buildOutdoorMapStateFromScene(
    const OutdoorSceneData &sceneData,
    OutdoorMapData &outdoorMapData,
    MapDeltaData &mapDeltaData,
    std::string &errorMessage)
{
    outdoorMapData.skyTexture = sceneData.environment.skyTexture;
    outdoorMapData.groundTilesetName = sceneData.environment.groundTilesetName;
    outdoorMapData.masterTile = sceneData.environment.masterTile;
    outdoorMapData.tileSetLookupIndices = sceneData.environment.tileSetLookupIndices;
    outdoorMapData.attributeMap.assign(
        OutdoorMapData::TerrainWidth * OutdoorMapData::TerrainHeight,
        0);
    outdoorMapData.terrainFootstepSoundOverrides.clear();
    outdoorMapData.terrainFootstepSoundOverrides.reserve(sceneData.terrainFootstepSoundOverrides.size());

    for (const OutdoorSceneTerrainFootstepSoundOverride &overrideEntry : sceneData.terrainFootstepSoundOverrides)
    {
        OutdoorTerrainFootstepSoundOverride terrainOverride = {};
        terrainOverride.tileId = overrideEntry.tileId;
        terrainOverride.walkSoundId = overrideEntry.walkSoundId;
        terrainOverride.runSoundId = overrideEntry.runSoundId;
        outdoorMapData.terrainFootstepSoundOverrides.push_back(terrainOverride);
    }

    for (OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        for (OutdoorBModelFace &face : bmodel.faces)
        {
            face.cogNumber = 0;
            face.cogTriggeredNumber = 0;
            face.cogTrigger = 0;
        }
    }

    for (const OutdoorSceneTerrainAttributeOverride &overrideEntry : sceneData.terrainAttributeOverrides)
    {
        if (overrideEntry.x < 0
            || overrideEntry.y < 0
            || overrideEntry.x >= OutdoorMapData::TerrainWidth
            || overrideEntry.y >= OutdoorMapData::TerrainHeight)
        {
            errorMessage = "scene terrain override is out of bounds";
            return false;
        }

        const size_t cellIndex =
            static_cast<size_t>(overrideEntry.y) * OutdoorMapData::TerrainWidth + static_cast<size_t>(overrideEntry.x);
        outdoorMapData.attributeMap[cellIndex] = overrideEntry.legacyAttributes;
    }

    for (const OutdoorSceneInteractiveFace &interactiveFace : sceneData.interactiveFaces)
    {
        if (!interactiveFace.bmodelName.empty())
        {
            continue;
        }

        if (interactiveFace.bmodelIndex >= outdoorMapData.bmodels.size()
            || interactiveFace.faceIndex >= outdoorMapData.bmodels[interactiveFace.bmodelIndex].faces.size())
        {
            errorMessage = "scene interactive face index is out of bounds";
            return false;
        }

        OutdoorBModelFace &face = outdoorMapData.bmodels[interactiveFace.bmodelIndex].faces[interactiveFace.faceIndex];
        applyOutdoorInteractiveFaceValues(face, interactiveFace);
    }

    for (const OutdoorSceneInteractiveFace &interactiveFace : sceneData.interactiveFaces)
    {
        if (interactiveFace.bmodelName.empty())
        {
            continue;
        }

        bool matchedBmodel = false;

        for (OutdoorBModel &bmodel : outdoorMapData.bmodels)
        {
            if (bmodel.name != interactiveFace.bmodelName)
            {
                continue;
            }

            matchedBmodel = true;

            if (interactiveFace.allFaces)
            {
                for (OutdoorBModelFace &face : bmodel.faces)
                {
                    applyOutdoorInteractiveFaceValues(face, interactiveFace);
                }

                continue;
            }

            if (interactiveFace.faceIndex >= bmodel.faces.size())
            {
                errorMessage = "scene named interactive face index is out of bounds";
                return false;
            }

            applyOutdoorInteractiveFaceValues(bmodel.faces[interactiveFace.faceIndex], interactiveFace);
        }

        if (!matchedBmodel)
        {
            errorMessage = "scene named interactive face bmodel was not found: " + interactiveFace.bmodelName;
            return false;
        }
    }

    outdoorMapData.entities.assign(sceneData.entities.size(), {});

    for (const OutdoorSceneEntity &entity : sceneData.entities)
    {
        if (entity.entityIndex >= outdoorMapData.entities.size())
        {
            errorMessage = "scene entity_index is out of bounds";
            return false;
        }

        outdoorMapData.entities[entity.entityIndex] = entity.entity;
    }

    outdoorMapData.spawns.assign(sceneData.spawns.size(), {});

    for (const OutdoorSceneSpawn &spawn : sceneData.spawns)
    {
        if (spawn.spawnIndex >= outdoorMapData.spawns.size())
        {
            errorMessage = "scene spawn_index is out of bounds";
            return false;
        }

        outdoorMapData.spawns[spawn.spawnIndex] = spawn.spawn;
    }

    outdoorMapData.entityCount = outdoorMapData.entities.size();
    outdoorMapData.spawnCount = outdoorMapData.spawns.size();

    mapDeltaData = {};
    mapDeltaData.locationInfo = sceneData.initialState.locationInfo;
    mapDeltaData.locationInfo.totalFacesCount = totalOutdoorFaceCount(outdoorMapData);
    mapDeltaData.locationInfo.decorationCount = static_cast<uint32_t>(outdoorMapData.entities.size());
    mapDeltaData.locationInfo.bmodelCount = static_cast<uint32_t>(outdoorMapData.bmodels.size());

    mapDeltaData.decorationFlags.assign(outdoorMapData.entities.size(), 0);

    for (const OutdoorSceneEntity &entity : sceneData.entities)
    {
        if (entity.entityIndex >= mapDeltaData.decorationFlags.size())
        {
            errorMessage = "scene entity decoration flag index is out of bounds";
            return false;
        }

        mapDeltaData.decorationFlags[entity.entityIndex] = entity.initialDecorationFlag;
    }

    for (const OutdoorBModel &bmodel : outdoorMapData.bmodels)
    {
        for (const OutdoorBModelFace &face : bmodel.faces)
        {
            mapDeltaData.faceAttributes.push_back(face.attributes);
        }
    }

    for (const OutdoorSceneFaceAttributeOverride &faceOverride : sceneData.initialState.faceAttributeOverrides)
    {
        if (faceOverride.bmodelIndex >= outdoorMapData.bmodels.size()
            || faceOverride.faceIndex >= outdoorMapData.bmodels[faceOverride.bmodelIndex].faces.size())
        {
            errorMessage = "scene initial face attribute override is out of bounds";
            return false;
        }

        size_t flattenedFaceIndex = 0;

        for (size_t bmodelIndex = 0; bmodelIndex < faceOverride.bmodelIndex; ++bmodelIndex)
        {
            flattenedFaceIndex += outdoorMapData.bmodels[bmodelIndex].faces.size();
        }

        flattenedFaceIndex += faceOverride.faceIndex;

        if (flattenedFaceIndex >= mapDeltaData.faceAttributes.size())
        {
            errorMessage = "scene initial face attribute override could not be flattened";
            return false;
        }

        mapDeltaData.faceAttributes[flattenedFaceIndex] = faceOverride.legacyAttributes;
    }

    mapDeltaData.actors = sceneData.initialState.actors;
    mapDeltaData.spriteObjects = sceneData.initialState.spriteObjects;
    mapDeltaData.chests = sceneData.initialState.chests;
    mapDeltaData.eventVariables = sceneData.initialState.eventVariables;
    mapDeltaData.locationTime.skyTextureName = sceneData.environment.skyTexture;
    mapDeltaData.locationTime.weatherFlags = sceneData.environment.dayBitsRaw;
    mapDeltaData.locationTime.fogWeakDistance = sceneData.environment.fogWeakDistance;
    mapDeltaData.locationTime.fogStrongDistance = sceneData.environment.fogStrongDistance;
    encodeSceneMapExtra(
        sceneData.environment.mapExtraBitsRaw,
        sceneData.environment.ceiling,
        mapDeltaData.locationTime.reserved);
    return true;
}
}
