#include "game/maps/OutdoorSceneYml.h"

#include "game/FaceEnums.h"
#include "game/StringUtils.h"
#include "game/maps/MapItemSourceYml.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
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
constexpr uint32_t SurfaceAnimationTicksPerSecond = 128;

bool isFiniteFloatNode(const YAML::Node &node, float &value)
{
    if (!node || !node.IsScalar())
    {
        return false;
    }

    try
    {
        value = node.as<float>();
    }
    catch (const std::exception &)
    {
        return false;
    }

    return std::isfinite(value);
}

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

bool parseOptionalSceneProfile(
    const YAML::Node &parentNode,
    OutdoorSceneProfile &profile,
    std::string &errorMessage)
{
    if (!parentNode["scene_profile"])
    {
        return true;
    }

    std::string value;

    if (!readScalarNode(parentNode, "scene_profile", value, errorMessage))
    {
        return false;
    }

    const std::string normalizedValue = toLowerCopy(value);

    if (normalizedValue == "classic_odm")
    {
        profile = OutdoorSceneProfile::ClassicOdm;
        return true;
    }

    if (normalizedValue == "bmodel_world")
    {
        profile = OutdoorSceneProfile::BModelWorld;
        return true;
    }

    errorMessage = "scene_profile must be \"classic_odm\" or \"bmodel_world\"";
    return false;
}

bool parseOptionalLocationType(
    const YAML::Node &environmentNode,
    OutdoorLocationType &locationType,
    std::string &errorMessage)
{
    if (!environmentNode["location_type"])
    {
        return true;
    }

    std::string value;

    if (!readScalarNode(environmentNode, "location_type", value, errorMessage))
    {
        return false;
    }

    const std::string normalizedValue = toLowerCopy(value);

    if (normalizedValue == "exterior")
    {
        locationType = OutdoorLocationType::Exterior;
        return true;
    }

    if (normalizedValue == "enclosed")
    {
        locationType = OutdoorLocationType::Enclosed;
        return true;
    }

    errorMessage = "environment.location_type must be \"exterior\" or \"enclosed\"";
    return false;
}

bool parseOptionalLighting(
    const YAML::Node &rootNode,
    OutdoorSceneLighting &lighting,
    std::string &errorMessage)
{
    const YAML::Node lightingNode = rootNode["lighting"];

    if (!lightingNode)
    {
        return true;
    }

    if (!lightingNode.IsMap())
    {
        errorMessage = "lighting must be a map";
        return false;
    }

    if (!readScalarNode(
            lightingNode,
            "lightmap_brightness_scale",
            lighting.lightmapBrightnessScale,
            errorMessage,
            false))
    {
        return false;
    }

    if (!std::isfinite(lighting.lightmapBrightnessScale) || lighting.lightmapBrightnessScale <= 0.0f)
    {
        errorMessage = "lighting.lightmap_brightness_scale must be finite and greater than zero";
        return false;
    }

    return true;
}

bool parseOptionalRendering(
    const YAML::Node &rootNode,
    OutdoorSceneRendering &rendering,
    std::string &errorMessage)
{
    const YAML::Node renderingNode = rootNode["rendering"];

    if (!renderingNode)
    {
        return true;
    }

    if (!renderingNode.IsMap())
    {
        errorMessage = "rendering must be a map";
        return false;
    }

    if (renderingNode["view_distance_scale"])
    {
        float viewDistanceScale = rendering.viewDistanceScale.value_or(1.0f);
        if (!readScalarNode(renderingNode, "view_distance_scale", viewDistanceScale, errorMessage, false))
        {
            return false;
        }

        if (!std::isfinite(viewDistanceScale) || viewDistanceScale <= 0.0f)
        {
            errorMessage = "rendering.view_distance_scale must be finite and greater than zero";
            return false;
        }

        rendering.viewDistanceScale = viewDistanceScale;
    }

    // A puddles-only rendering block parses without view_distance_scale. An overlay's
    // explicit puddles block replaces the base one; absence keeps the base value.
    const YAML::Node puddlesNode = renderingNode["puddles"];

    if (puddlesNode)
    {
        OutdoorScenePuddles puddles = {};

        if (!puddlesNode.IsMap())
        {
            errorMessage = "rendering.puddles must be a map";
            return false;
        }

        if (!readScalarNode(puddlesNode, "mask", puddles.mask, errorMessage))
        {
            return false;
        }

        if (puddles.mask.empty() || puddles.mask.front() == '-')
        {
            errorMessage = "rendering.puddles.mask must be a non-empty mounted asset path";
            return false;
        }

        const YAML::Node originNode = puddlesNode["origin"];
        if (!originNode || !originNode.IsSequence() || originNode.size() != 2
            || !isFiniteFloatNode(originNode[0], puddles.origin[0])
            || !isFiniteFloatNode(originNode[1], puddles.origin[1]))
        {
            errorMessage = "rendering.puddles.origin must be two finite coordinates";
            return false;
        }

        const YAML::Node extentNode = puddlesNode["extent"];
        if (!extentNode || !extentNode.IsSequence() || extentNode.size() != 2
            || !isFiniteFloatNode(extentNode[0], puddles.extent[0])
            || !isFiniteFloatNode(extentNode[1], puddles.extent[1]))
        {
            errorMessage = "rendering.puddles.extent must be two finite coordinates";
            return false;
        }

        if (puddles.extent[0] == 0.0f || puddles.extent[1] == 0.0f
            || !std::isfinite(puddles.extent[0]) || !std::isfinite(puddles.extent[1]))
        {
            errorMessage = "rendering.puddles.extent must have nonzero signed components";
            return false;
        }

        rendering.puddles = puddles;
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

    if (fogModeText == "authored_day_night")
    {
        fogMode = OutdoorFogMode::AuthoredDayNight;
        return true;
    }

    errorMessage = "environment.weather.fog_mode must be one of: static, daily_random, authored_day_night";
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

OutdoorScenePerceptionFace *findOutdoorPerceptionFace(
    OutdoorSceneData &sceneData,
    size_t bmodelIndex,
    size_t faceIndex)
{
    for (OutdoorScenePerceptionFace &face : sceneData.perceptionFaces)
    {
        if (face.bmodelIndex == bmodelIndex && face.faceIndex == faceIndex)
        {
            return &face;
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

bool parseOutdoorPerceptionFace(
    const YAML::Node &perceptionFaceNode,
    OutdoorScenePerceptionFace &face,
    std::string &errorMessage)
{
    if (!perceptionFaceNode.IsMap())
    {
        errorMessage = "perception face entry must be a map";
        return false;
    }

    if (!readScalarNode(perceptionFaceNode, "bmodel_index", face.bmodelIndex, errorMessage)
        || !readScalarNode(perceptionFaceNode, "face_index", face.faceIndex, errorMessage)
        || !readScalarNode(perceptionFaceNode, "difficulty", face.difficulty, errorMessage))
    {
        return false;
    }

    if (face.difficulty < 0 || face.difficulty > 20)
    {
        errorMessage = "perception face difficulty must be in the 0-20 range";
        return false;
    }

    return true;
}

OutdoorBModelMechanismKind outdoorMechanismKindFromText(const std::string &kind)
{
    const std::string normalizedKind = toLowerCopy(kind);

    if (normalizedKind == "linear_door" || normalizedKind == "linear_button")
    {
        return OutdoorBModelMechanismKind::LinearDoor;
    }

    if (normalizedKind == "weighted_lift")
    {
        return OutdoorBModelMechanismKind::WeightedLift;
    }

    if (normalizedKind == "rotating_door" || normalizedKind == "rotating_switch")
    {
        return OutdoorBModelMechanismKind::RotatingDoor;
    }

    if (normalizedKind == "rotating_brush")
    {
        return OutdoorBModelMechanismKind::RotatingBrush;
    }

    if (normalizedKind == "collision_volume")
    {
        return OutdoorBModelMechanismKind::CollisionVolume;
    }

    return OutdoorBModelMechanismKind::Unsupported;
}

bool parseOutdoorBModelMechanism(
    const YAML::Node &mechanismNode,
    OutdoorBModelMechanism &mechanism,
    std::string &errorMessage)
{
    if (!mechanismNode.IsMap())
    {
        errorMessage = "mechanism entry must be a map";
        return false;
    }

    if (!readScalarNode(mechanismNode, "mechanism_id", mechanism.mechanismId, errorMessage)
        || !readScalarNode(mechanismNode, "event_id", mechanism.interactionEventId, errorMessage, false)
        || !readScalarNode(mechanismNode, "source_object_index", mechanism.sourceObjectIndex, errorMessage)
        || !readScalarNode(mechanismNode, "source_class", mechanism.sourceClass, errorMessage)
        || !readScalarNode(mechanismNode, "source_name", mechanism.sourceName, errorMessage)
        || !readScalarNode(mechanismNode, "kind", mechanism.sourceKind, errorMessage))
    {
        return false;
    }

    mechanism.kind = outdoorMechanismKindFromText(mechanism.sourceKind);
    mechanism.moveParty = mechanism.kind == OutdoorBModelMechanismKind::WeightedLift;

    const YAML::Node bindingNode = mechanismNode["binding"];

    if (!bindingNode || !bindingNode.IsMap())
    {
        errorMessage = "mechanism.binding must be a map";
        return false;
    }

    std::string targetKind;
    if (!readScalarNode(bindingNode, "target_kind", targetKind, errorMessage)
        || !readScalarNode(bindingNode, "confidence", mechanism.bindingConfidence, errorMessage, false))
    {
        return false;
    }

    targetKind = toLowerCopy(targetKind);

    if (targetKind == "odm_bmodel")
    {
        mechanism.hasBModelBinding = true;

        if (!readScalarNode(bindingNode, "bmodel_index", mechanism.bmodelIndex, errorMessage)
            || !readScalarNode(bindingNode, "bmodel_name", mechanism.bmodelName, errorMessage))
        {
            return false;
        }
    }
    else if (targetKind != "unresolved")
    {
        errorMessage = "mechanism.binding.target_kind must be odm_bmodel or unresolved";
        return false;
    }

    const YAML::Node motionNode = mechanismNode["motion"];

    if (!motionNode || !motionNode.IsMap()
        || !readScalarNode(motionNode, "move_time_ms", mechanism.moveTimeMs, errorMessage))
    {
        errorMessage = errorMessage.empty() ? "mechanism.motion must be a map" : errorMessage;
        return false;
    }

    const YAML::Node linearNode = motionNode["linear"];
    const YAML::Node rotationNode = motionNode["rotation"];

    if (linearNode && rotationNode)
    {
        errorMessage = "mechanism.motion cannot contain both linear and rotation motion";
        return false;
    }

    if (linearNode)
    {
        if (!linearNode.IsMap()
            || !parsePositionNode(
                linearNode["delta_openyamm"],
                mechanism.deltaX,
                mechanism.deltaY,
                mechanism.deltaZ,
                errorMessage))
        {
            errorMessage = errorMessage.empty() ? "mechanism.motion.linear must be a map" : errorMessage;
            return false;
        }

        mechanism.motionKind = OutdoorBModelMechanismMotionKind::Linear;
    }
    else if (rotationNode)
    {
        if (!rotationNode.IsMap()
            || !parsePositionNode(
                rotationNode["pivot_openyamm"],
                mechanism.pivotX,
                mechanism.pivotY,
                mechanism.pivotZ,
                errorMessage)
            || !parsePositionNode(
                rotationNode["rotation_angles_openyamm_deg"],
                mechanism.rotationDegreesX,
                mechanism.rotationDegreesY,
                mechanism.rotationDegreesZ,
                errorMessage))
        {
            errorMessage = errorMessage.empty() ? "mechanism.motion.rotation must be a map" : errorMessage;
            return false;
        }

        mechanism.motionKind = OutdoorBModelMechanismMotionKind::Rotation;
    }

    const YAML::Node activationNode = mechanismNode["activation"];

    if (activationNode && !activationNode.IsNull())
    {
        if (!activationNode.IsMap()
            || !readScalarNode(activationNode, "start_open", mechanism.startOpen, errorMessage, false)
            || !readScalarNode(activationNode, "start_on", mechanism.startOn, errorMessage, false)
            || !readScalarNode(activationNode, "push_open", mechanism.pushOpen, errorMessage, false)
            || !readScalarNode(activationNode, "touch_to_open", mechanism.touchToOpen, errorMessage, false)
            || !readScalarNode(activationNode, "locked", mechanism.locked, errorMessage, false)
            || !readScalarNode(activationNode, "open_away", mechanism.openAway, errorMessage, false)
            || !readScalarNode(activationNode, "move_party", mechanism.moveParty, errorMessage, false))
        {
            errorMessage = errorMessage.empty() ? "mechanism.activation must be a map" : errorMessage;
            return false;
        }
    }

    const YAML::Node soundsNode = mechanismNode["sounds"];

    if (soundsNode && !soundsNode.IsNull())
    {
        if (!soundsNode.IsMap()
            || !readScalarNode(soundsNode, "open", mechanism.audio.openSound, errorMessage, false)
            || !readScalarNode(soundsNode, "close", mechanism.audio.closeSound, errorMessage, false)
            || !readScalarNode(
                soundsNode, "open_start", mechanism.audio.openStartSound, errorMessage, false)
            || !readScalarNode(
                soundsNode, "open_busy", mechanism.audio.openBusySound, errorMessage, false)
            || !readScalarNode(
                soundsNode, "open_stop", mechanism.audio.openStopSound, errorMessage, false)
            || !readScalarNode(
                soundsNode, "close_start", mechanism.audio.closeStartSound, errorMessage, false)
            || !readScalarNode(
                soundsNode, "close_busy", mechanism.audio.closeBusySound, errorMessage, false)
            || !readScalarNode(
                soundsNode, "close_stop", mechanism.audio.closeStopSound, errorMessage, false)
            || !readScalarNode(soundsNode, "jiggle", mechanism.audio.jiggleSound, errorMessage, false))
        {
            errorMessage = errorMessage.empty() ? "mechanism.sounds must be a map" : errorMessage;
            return false;
        }

        const YAML::Node positionNode = soundsNode["position"];

        if (positionNode)
        {
            if (!parsePositionNode(
                positionNode,
                mechanism.audio.x,
                mechanism.audio.y,
                mechanism.audio.z,
                errorMessage))
            {
                return false;
            }

            mechanism.audio.positional = true;
        }
    }

    return true;
}

bool parseOutdoorDestructible(
    const YAML::Node &node,
    OutdoorDestructible &destructible,
    std::string &errorMessage)
{
    if (!node.IsMap()
        || !readScalarNode(node, "source_object_index", destructible.sourceObjectIndex, errorMessage)
        || !readScalarNode(node, "runtime_object_id", destructible.runtimeObjectId, errorMessage)
        || !readScalarNode(node, "source_name", destructible.sourceName, errorMessage)
        || !readScalarNode(node, "initial_hp", destructible.initialHp, errorMessage, false)
        || !readScalarNode(
            node, "initially_damage_enabled", destructible.initiallyDamageEnabled, errorMessage, false)
        || !readScalarNode(node, "trigger_destroy_only", destructible.triggerDestroyOnly, errorMessage, false)
        || !readScalarNode(node, "should_mini_save", destructible.shouldMiniSave, errorMessage, false)
        || !readScalarNode(node, "destruction_sound", destructible.destructionSound, errorMessage, false)
        || !readScalarNode(
            node, "death_target_source_object_index", destructible.deathTargetSourceObjectIndex,
            errorMessage, false)
        || !readScalarNode(node, "death_message", destructible.deathMessage, errorMessage, false))
    {
        errorMessage = errorMessage.empty() ? "destructible entry must be a map" : errorMessage;
        return false;
    }

    const YAML::Node bindingNode = node["binding"];
    std::string targetKind;
    if (!bindingNode || !bindingNode.IsMap()
        || !readScalarNode(bindingNode, "target_kind", targetKind, errorMessage)
        || toLowerCopy(targetKind) != "odm_bmodel"
        || !readScalarNode(bindingNode, "bmodel_index", destructible.bmodelIndex, errorMessage)
        || !readScalarNode(bindingNode, "bmodel_name", destructible.bmodelName, errorMessage))
    {
        errorMessage = errorMessage.empty()
            ? "destructible.binding must target an odm_bmodel"
            : errorMessage;
        return false;
    }

    if (destructible.initialHp <= 0)
    {
        errorMessage = "destructible.initial_hp must be positive";
        return false;
    }

    const YAML::Node auxiliaryBmodelIndicesNode = bindingNode["auxiliary_bmodel_indices"];
    if (auxiliaryBmodelIndicesNode)
    {
        if (!auxiliaryBmodelIndicesNode.IsSequence())
        {
            errorMessage = "destructible.binding.auxiliary_bmodel_indices must be a sequence";
            return false;
        }

        try
        {
            for (const YAML::Node &indexNode : auxiliaryBmodelIndicesNode)
            {
                destructible.auxiliaryBmodelIndices.push_back(indexNode.as<size_t>());
            }
        }
        catch (const YAML::Exception &exception)
        {
            errorMessage = std::string("invalid destructible auxiliary BModel index: ") + exception.what();
            return false;
        }
    }

    return true;
}

bool parseOutdoorDestructibleReceiver(
    const YAML::Node &node,
    OutdoorDestructibleReceiver &receiver,
    std::string &errorMessage)
{
    if (!node.IsMap()
        || !readScalarNode(node, "source_object_index", receiver.sourceObjectIndex, errorMessage)
        || !readScalarNode(node, "source_name", receiver.sourceName, errorMessage)
        || !readScalarNode(
            node, "required_destruction_count", receiver.requiredDestructionCount, errorMessage)
        || !readScalarNode(node, "reward_raw_quest_key", receiver.rewardRawQuestKey, errorMessage)
        || !readScalarNode(node, "reward_experience", receiver.rewardExperience, errorMessage))
    {
        errorMessage = errorMessage.empty() ? "destructible receiver entry must be a map" : errorMessage;
        return false;
    }

    if (receiver.requiredDestructionCount == 0 || receiver.rewardRawQuestKey <= 0)
    {
        errorMessage = "destructible receiver requires a positive count and quest key";
        return false;
    }

    return true;
}

std::optional<OutdoorTriggerAction> outdoorTriggerActionFromText(const std::string &value)
{
    const std::string normalized = toLowerCopy(value);
    if (normalized == "damage_on")
    {
        return OutdoorTriggerAction::DamageOn;
    }
    if (normalized == "damage_off")
    {
        return OutdoorTriggerAction::DamageOff;
    }
    if (normalized == "damage")
    {
        return OutdoorTriggerAction::Damage;
    }
    if (normalized == "destroy")
    {
        return OutdoorTriggerAction::Destroy;
    }
    if (normalized == "remove")
    {
        return OutdoorTriggerAction::Remove;
    }
    return std::nullopt;
}

bool parseOutdoorTriggerVolume(
    const YAML::Node &node,
    OutdoorTriggerVolume &trigger,
    std::string &errorMessage)
{
    if (!node.IsMap()
        || !readScalarNode(node, "source_object_index", trigger.sourceObjectIndex, errorMessage)
        || !readScalarNode(node, "source_name", trigger.sourceName, errorMessage)
        || !parsePositionNode(node["position"], trigger.x, trigger.y, trigger.z, errorMessage)
        || !parsePositionNode(
            node["half_extents"], trigger.halfExtentX, trigger.halfExtentY, trigger.halfExtentZ, errorMessage)
        || !readScalarNode(node, "start_on", trigger.startOn, errorMessage, false))
    {
        errorMessage = errorMessage.empty() ? "trigger volume entry must be a map" : errorMessage;
        return false;
    }

    const YAML::Node outputsNode = node["outputs"];
    if (!outputsNode || !outputsNode.IsSequence())
    {
        errorMessage = "trigger volume outputs must be a sequence";
        return false;
    }

    for (const YAML::Node &outputNode : outputsNode)
    {
        OutdoorTriggerOutput output = {};
        std::string action;
        if (!outputNode.IsMap()
            || !readScalarNode(
                outputNode, "target_source_object_index", output.targetSourceObjectIndex, errorMessage)
            || !readScalarNode(outputNode, "action", action, errorMessage)
            || !readScalarNode(outputNode, "damage", output.damage, errorMessage, false))
        {
            errorMessage = errorMessage.empty() ? "trigger output entry must be a map" : errorMessage;
            return false;
        }

        const std::optional<OutdoorTriggerAction> parsedAction = outdoorTriggerActionFromText(action);
        if (!parsedAction)
        {
            errorMessage = "unsupported trigger output action: " + action;
            return false;
        }

        output.action = *parsedAction;
        trigger.outputs.push_back(output);
    }

    return true;
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

void mergeOutdoorPerceptionFace(OutdoorSceneData &sceneData, const OutdoorScenePerceptionFace &sourceFace)
{
    OutdoorScenePerceptionFace *pTargetFace =
        findOutdoorPerceptionFace(sceneData, sourceFace.bmodelIndex, sourceFace.faceIndex);

    if (pTargetFace == nullptr)
    {
        sceneData.perceptionFaces.push_back(sourceFace);
        return;
    }

    *pTargetFace = sourceFace;
}

bool parseOutdoorSurfaceAnimation(
    const YAML::Node &animationNode,
    OutdoorSceneSurfaceAnimation &surfaceAnimation,
    std::string &errorMessage)
{
    if (!animationNode.IsMap())
    {
        errorMessage = "surface animation entry must be a map";
        return false;
    }

    uint32_t framesPerSecond = 0;

    if (!readScalarNode(animationNode, "texture", surfaceAnimation.textureName, errorMessage)
        || !readScalarNode(animationNode, "frames_per_second", framesPerSecond, errorMessage))
    {
        return false;
    }

    if (surfaceAnimation.textureName.empty())
    {
        errorMessage = "surface animation texture must not be empty";
        return false;
    }

    surfaceAnimation.textureName = toLowerCopy(surfaceAnimation.textureName);

    if (framesPerSecond == 0 || framesPerSecond > SurfaceAnimationTicksPerSecond)
    {
        errorMessage = "surface animation frames_per_second must be between 1 and 128";
        return false;
    }

    const YAML::Node framesNode = animationNode["frames"];

    if (!framesNode || !framesNode.IsSequence() || framesNode.size() < 2)
    {
        errorMessage = "surface animation frames must contain at least two entries";
        return false;
    }

    surfaceAnimation.animation.frames.reserve(framesNode.size());

    for (const YAML::Node &frameNode : framesNode)
    {
        if (!frameNode.IsScalar())
        {
            errorMessage = "surface animation frame must be a texture-name scalar";
            return false;
        }

        SurfaceAnimationFrame frame = {};
        frame.textureName = frameNode.as<std::string>();

        if (frame.textureName.empty())
        {
            errorMessage = "surface animation frame texture must not be empty";
            return false;
        }

        surfaceAnimation.animation.frames.push_back(std::move(frame));
    }

    const uint32_t frameCount = static_cast<uint32_t>(surfaceAnimation.animation.frames.size());
    const double exactAnimationLength = static_cast<double>(frameCount)
        * static_cast<double>(SurfaceAnimationTicksPerSecond)
        / static_cast<double>(framesPerSecond);
    const uint32_t animationLengthTicks =
        std::max(frameCount, static_cast<uint32_t>(std::lround(exactAnimationLength)));
    const uint32_t baseFrameLength = animationLengthTicks / frameCount;
    uint32_t remainder = animationLengthTicks % frameCount;

    surfaceAnimation.animation.animationLengthTicks = animationLengthTicks;

    for (SurfaceAnimationFrame &frame : surfaceAnimation.animation.frames)
    {
        frame.frameLengthTicks = baseFrameLength + (remainder > 0 ? 1U : 0U);

        if (remainder > 0)
        {
            --remainder;
        }
    }

    return true;
}

void mergeOutdoorSurfaceAnimation(
    OutdoorSceneData &sceneData,
    const OutdoorSceneSurfaceAnimation &sourceAnimation)
{
    const std::string normalizedTextureName = toLowerCopy(sourceAnimation.textureName);
    const auto animationIt = std::find_if(
        sceneData.surfaceAnimations.begin(),
        sceneData.surfaceAnimations.end(),
        [&normalizedTextureName](const OutdoorSceneSurfaceAnimation &animation)
        {
            return animation.textureName == normalizedTextureName;
        });

    if (animationIt == sceneData.surfaceAnimations.end())
    {
        sceneData.surfaceAnimations.push_back(sourceAnimation);
        return;
    }

    *animationIt = sourceAnimation;
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

bool parseAuthoredFogState(
    const YAML::Node &authoredFogNode,
    const char *key,
    OutdoorAuthoredFogState &state,
    std::string &errorMessage)
{
    const YAML::Node stateNode = authoredFogNode[key];

    if (!stateNode)
    {
        return true;
    }

    if (!stateNode.IsMap())
    {
        errorMessage = std::string("authored fog state must be a map: ") + key;
        return false;
    }

    bool hasColor = false;

    if (!readScalarNode(stateNode, "enabled", state.enabled, errorMessage)
        || !readScalarNode(stateNode, "near_distance", state.distances.weakDistance, errorMessage)
        || !readScalarNode(stateNode, "far_distance", state.distances.strongDistance, errorMessage)
        || !parseRgbTripletNode(stateNode, "color_rgb", hasColor, state.colorRgb, errorMessage))
    {
        return false;
    }

    if (!hasColor)
    {
        errorMessage = std::string("authored fog state requires color_rgb: ") + key;
        return false;
    }

    if (state.enabled
        && (state.distances.weakDistance < 0
            || state.distances.strongDistance <= state.distances.weakDistance))
    {
        errorMessage = std::string("authored fog state requires 0 <= near_distance < far_distance: ") + key;
        return false;
    }

    state.configured = true;
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
    const YAML::Node authoredFogNode = weatherNode["authored_fog"];

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

    if (authoredFogNode)
    {
        if (!authoredFogNode.IsMap()
            || !parseAuthoredFogState(
                authoredFogNode,
                "day",
                weatherConfig.authoredDayFog,
                errorMessage)
            || !parseAuthoredFogState(
                authoredFogNode,
                "night",
                weatherConfig.authoredNightFog,
                errorMessage))
        {
            errorMessage = errorMessage.empty() ? "environment.weather.authored_fog must be a map" : errorMessage;
            return false;
        }
    }

    if (weatherConfig.fogMode == OutdoorFogMode::AuthoredDayNight
        && (!weatherConfig.authoredDayFog.configured || !weatherConfig.authoredNightFog.configured))
    {
        errorMessage = "authored_day_night fog mode requires authored_fog.day and authored_fog.night";
        return false;
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

bool parseOutdoorSpawn(
    const YAML::Node &spawnNode,
    OutdoorSceneSpawn &spawn,
    std::string &errorMessage)
{
    if (!spawnNode.IsMap())
    {
        errorMessage = "spawn entry must be a map";
        return false;
    }

    return readScalarNode(spawnNode, "spawn_index", spawn.spawnIndex, errorMessage)
        && readScalarNode(spawnNode, "radius", spawn.spawn.radius, errorMessage)
        && readScalarNode(spawnNode, "type_id", spawn.spawn.typeId, errorMessage)
        && readScalarNode(spawnNode, "index", spawn.spawn.index, errorMessage)
        && readScalarNode(spawnNode, "attributes", spawn.spawn.attributes, errorMessage)
        && readScalarNode(spawnNode, "group", spawn.spawn.group, errorMessage)
        && parsePositionNode(spawnNode["position"], spawn.spawn.x, spawn.spawn.y, spawn.spawn.z, errorMessage);
}

bool parseOutdoorEntity(
    const YAML::Node &entityNode,
    OutdoorSceneEntity &entity,
    std::string &errorMessage)
{
    if (!entityNode.IsMap())
    {
        errorMessage = "entity entry must be a map";
        return false;
    }

    return readScalarNode(entityNode, "entity_index", entity.entityIndex, errorMessage)
        && readScalarNode(entityNode, "name", entity.entity.name, errorMessage)
        && readScalarNode(entityNode, "decoration_list_id", entity.entity.decorationListId, errorMessage)
        && readScalarNode(entityNode, "ai_attributes", entity.entity.aiAttributes, errorMessage)
        && readScalarNode(entityNode, "facing", entity.entity.facing, errorMessage)
        && readScalarNode(entityNode, "event_id_primary", entity.entity.eventIdPrimary, errorMessage)
        && readScalarNode(entityNode, "event_id_secondary", entity.entity.eventIdSecondary, errorMessage)
        && readScalarNode(entityNode, "variable_primary", entity.entity.variablePrimary, errorMessage)
        && readScalarNode(entityNode, "variable_secondary", entity.entity.variableSecondary, errorMessage)
        && readScalarNode(entityNode, "special_trigger", entity.entity.specialTrigger, errorMessage)
        && readScalarNode(entityNode, "initial_decoration_flag", entity.initialDecorationFlag, errorMessage)
        && parsePositionNode(entityNode["position"], entity.entity.x, entity.entity.y, entity.entity.z, errorMessage);
}

bool parseOutdoorActor(
    const YAML::Node &actorNode,
    size_t actorIndex,
    MapDeltaActor &actor,
    std::string &errorMessage)
{
    if (!actorNode.IsMap())
    {
        errorMessage = "actor entry must be a map";
        return false;
    }

    actor.diagnosticSourceActorIndex = actorIndex;

    if (!readScalarNode(actorNode, "name", actor.name, errorMessage)
        || !readScalarNode(actorNode, "npc_id", actor.npcId, errorMessage)
        || !readScalarNode(actorNode, "mm9_rude_id", actor.mm9RudeId, errorMessage, false)
        || !readScalarNode(
            actorNode,
            "mm9_source_object_index",
            actor.mm9SourceObjectIndex,
            errorMessage,
            false)
        || !readScalarNode(
            actorNode,
            "mm9_can_receive_damage",
            actor.mm9CanReceiveDamage,
            errorMessage,
            false)
        || !readScalarNode(actorNode, "mm9_civilian", actor.mm9Civilian, errorMessage, false)
        || !readScalarNode(actorNode, "mm9_guard", actor.mm9Guard, errorMessage, false)
        || !readScalarNode(actorNode, "initial_yaw_units", actor.initialYawUnits, errorMessage, false)
        || !readScalarNode(actorNode, "immobile", actor.immobile, errorMessage, false)
        || !readScalarNode(actorNode, "attributes", actor.attributes, errorMessage)
        || !readScalarNode(actorNode, "hp", actor.hp, errorMessage)
        || !readScalarNode(actorNode, "hostility_type", actor.hostilityType, errorMessage)
        || !readScalarNode(actorNode, "monster_info_id", actor.monsterInfoId, errorMessage)
        || !readScalarNode(actorNode, "monster_id", actor.monsterId, errorMessage)
        || !readScalarNode(actorNode, "radius", actor.radius, errorMessage)
        || !readScalarNode(actorNode, "height", actor.height, errorMessage)
        || !readScalarNode(actorNode, "move_speed", actor.moveSpeed, errorMessage)
        || !readScalarNode(actorNode, "sector_id", actor.sectorId, errorMessage)
        || !readScalarNode(actorNode, "current_action_animation", actor.currentActionAnimation, errorMessage)
        || !readScalarNode(actorNode, "group", actor.group, errorMessage)
        || !readScalarNode(actorNode, "ally", actor.ally, errorMessage)
        || !readScalarNode(actorNode, "unique_name_index", actor.uniqueNameIndex, errorMessage)
        || !parsePositionNode(actorNode["position"], actor.x, actor.y, actor.z, errorMessage))
    {
        return false;
    }

    if (!readScalarNode(actorNode, "carried_item_id", actor.carriedItemId, errorMessage, false))
    {
        actor.carriedItemId = 0;
    }

    const YAML::Node spriteIdsNode = actorNode["sprite_ids"];

    if (!spriteIdsNode || !spriteIdsNode.IsSequence() || spriteIdsNode.size() != actor.spriteIds.size())
    {
        errorMessage = "actor.sprite_ids must have exactly 4 entries";
        return false;
    }

    for (size_t spriteIndex = 0; spriteIndex < actor.spriteIds.size(); ++spriteIndex)
    {
        if (!spriteIdsNode[spriteIndex].IsScalar())
        {
            errorMessage = "actor sprite_ids entries must be scalar";
            return false;
        }

        try
        {
            actor.spriteIds[spriteIndex] = spriteIdsNode[spriteIndex].as<uint16_t>();
        }
        catch (const std::exception &exception)
        {
            errorMessage = std::string("could not parse actor sprite id: ") + exception.what();
            return false;
        }
    }

    return true;
}

bool parseOutdoorSpriteObject(
    const YAML::Node &spriteObjectNode,
    MapDeltaSpriteObject &spriteObject,
    std::string &errorMessage)
{
    if (!spriteObjectNode.IsMap())
    {
        errorMessage = "sprite object entry must be a map";
        return false;
    }

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
        || !readScalarNode(spriteObjectNode, "time_since_created", spriteObject.timeSinceCreated, errorMessage)
        || !readScalarNode(spriteObjectNode, "temporary_lifetime", spriteObject.temporaryLifetime, errorMessage)
        || !readScalarNode(
            spriteObjectNode,
            "glow_radius_multiplier",
            spriteObject.glowRadiusMultiplier,
            errorMessage)
        || !readScalarNode(spriteObjectNode, "spell_id", spriteObject.spellId, errorMessage)
        || !readScalarNode(spriteObjectNode, "spell_level", spriteObject.spellLevel, errorMessage)
        || !readScalarNode(spriteObjectNode, "spell_skill", spriteObject.spellSkill, errorMessage)
        || !readScalarNode(spriteObjectNode, "field54", spriteObject.field54, errorMessage)
        || !readScalarNode(spriteObjectNode, "spell_caster_pid", spriteObject.spellCasterPid, errorMessage)
        || !readScalarNode(spriteObjectNode, "spell_target_pid", spriteObject.spellTargetPid, errorMessage)
        || !readScalarNode(spriteObjectNode, "lod_distance", spriteObject.lodDistance, errorMessage)
        || !readScalarNode(
            spriteObjectNode,
            "spell_caster_ability",
            spriteObject.spellCasterAbility,
            errorMessage)
        || !readScalarNode(spriteObjectNode, "raw_containing_item_hex", rawContainingItemHex, errorMessage)
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
        return false;
    }

    return parseHexBytes(
        rawContainingItemHex,
        SpriteObjectContainingItemSize,
        spriteObject.rawContainingItem,
        errorMessage);
}

bool parseOutdoorChest(
    const YAML::Node &chestNode,
    MapDeltaChest &chest,
    std::string &errorMessage)
{
    if (!chestNode.IsMap())
    {
        errorMessage = "chest entry must be a map";
        return false;
    }

    std::string rawItemsHex;
    std::vector<uint8_t> rawItems;
    std::vector<int> inventoryMatrixValues;

    if (!readScalarNode(chestNode, "chest_type_id", chest.chestTypeId, errorMessage)
        || !readScalarNode(chestNode, "flags", chest.flags, errorMessage)
        || !readScalarNode(chestNode, "raw_items_hex", rawItemsHex, errorMessage, false))
    {
        return false;
    }

    const YAML::Node inventoryMatrixNode = chestNode["inventory_matrix"];
    if (inventoryMatrixNode)
    {
        if (!parseIntSequence(inventoryMatrixNode, 140, inventoryMatrixValues, errorMessage))
        {
            return false;
        }
    }
    else
    {
        inventoryMatrixValues.assign(140, 0);
    }

    if (rawItemsHex.empty())
    {
        rawItems.assign(ChestItemPayloadSize, 0);
    }
    else if (!parseHexBytes(rawItemsHex, ChestItemPayloadSize, rawItems, errorMessage))
    {
        return false;
    }

    chest.rawItems = std::move(rawItems);
    chest.inventoryMatrix.reserve(inventoryMatrixValues.size());

    for (int value : inventoryMatrixValues)
    {
        chest.inventoryMatrix.push_back(static_cast<int16_t>(value));
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

    if (!parseMapItemSourceData(rootNode, sceneData.itemSources, errorMessage))
    {
        return std::nullopt;
    }

    if (!parseOptionalSceneProfile(rootNode, sceneData.sceneProfile, errorMessage))
    {
        return std::nullopt;
    }

    if (!parseOptionalLighting(rootNode, sceneData.lighting, errorMessage))
    {
        return std::nullopt;
    }

    if (!parseOptionalRendering(rootNode, sceneData.rendering, errorMessage))
    {
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
                "allow_rest",
                sceneData.runtimeRestrictions.allowRest,
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

    if (!parseOptionalLocationType(environmentNode, sceneData.environment.locationType, errorMessage))
    {
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

    const YAML::Node surfaceAnimationsNode = rootNode["surface_animations"];

    if (surfaceAnimationsNode)
    {
        if (!surfaceAnimationsNode.IsSequence())
        {
            errorMessage = "surface_animations must be a sequence";
            return std::nullopt;
        }

        sceneData.surfaceAnimations.reserve(surfaceAnimationsNode.size());

        for (const YAML::Node &animationNode : surfaceAnimationsNode)
        {
            OutdoorSceneSurfaceAnimation surfaceAnimation = {};

            if (!parseOutdoorSurfaceAnimation(animationNode, surfaceAnimation, errorMessage))
            {
                return std::nullopt;
            }

            const std::string &normalizedTextureName = surfaceAnimation.textureName;
            const bool duplicate = std::any_of(
                sceneData.surfaceAnimations.begin(),
                sceneData.surfaceAnimations.end(),
                [&normalizedTextureName](const OutdoorSceneSurfaceAnimation &animation)
                {
                    return animation.textureName == normalizedTextureName;
                });

            if (duplicate)
            {
                errorMessage = "surface animation texture must be unique";
                return std::nullopt;
            }

            sceneData.surfaceAnimations.push_back(std::move(surfaceAnimation));
        }
    }

    const YAML::Node bmodelFacesNode = rootNode["bmodel_faces"];
    const YAML::Node interactiveFacesNode = bmodelFacesNode ? bmodelFacesNode["interactive_faces"] : YAML::Node();

    if (!bmodelFacesNode || !bmodelFacesNode.IsMap() || !interactiveFacesNode || !interactiveFacesNode.IsSequence())
    {
        errorMessage = "bmodel_faces.interactive_faces must be a sequence";
        return std::nullopt;
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

    const YAML::Node perceptionFacesNode = bmodelFacesNode["perception_faces"];

    if (perceptionFacesNode)
    {
        if (!perceptionFacesNode.IsSequence())
        {
            errorMessage = "bmodel_faces.perception_faces must be a sequence";
            return std::nullopt;
        }

        sceneData.perceptionFaces.reserve(perceptionFacesNode.size());

        for (const YAML::Node &perceptionFaceNode : perceptionFacesNode)
        {
            OutdoorScenePerceptionFace face = {};

            if (!parseOutdoorPerceptionFace(perceptionFaceNode, face, errorMessage))
            {
                return std::nullopt;
            }

            sceneData.perceptionFaces.push_back(face);
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
            OutdoorBModelMechanism mechanism = {};

            if (!parseOutdoorBModelMechanism(mechanismNode, mechanism, errorMessage))
            {
                return std::nullopt;
            }

            const auto duplicate = std::find_if(
                sceneData.mechanisms.begin(),
                sceneData.mechanisms.end(),
                [&mechanism](const OutdoorBModelMechanism &existing)
                {
                    return existing.mechanismId == mechanism.mechanismId;
                });

            if (duplicate != sceneData.mechanisms.end())
            {
                errorMessage = "mechanism_id must be unique";
                return std::nullopt;
            }

            sceneData.mechanisms.push_back(std::move(mechanism));
        }
    }

    const YAML::Node destructiblesNode = rootNode["destructibles"];

    if (destructiblesNode)
    {
        if (!destructiblesNode.IsSequence())
        {
            errorMessage = "destructibles must be a sequence";
            return std::nullopt;
        }

        for (const YAML::Node &destructibleNode : destructiblesNode)
        {
            OutdoorDestructible destructible = {};
            if (!parseOutdoorDestructible(destructibleNode, destructible, errorMessage))
            {
                return std::nullopt;
            }

            const auto duplicate = std::find_if(
                sceneData.destructibles.begin(),
                sceneData.destructibles.end(),
                [&destructible](const OutdoorDestructible &existing)
                {
                    return existing.sourceObjectIndex == destructible.sourceObjectIndex;
                });
            if (duplicate != sceneData.destructibles.end())
            {
                errorMessage = "destructible source_object_index must be unique";
                return std::nullopt;
            }

            sceneData.destructibles.push_back(std::move(destructible));
        }
    }

    const YAML::Node triggerVolumesNode = rootNode["trigger_volumes"];

    const YAML::Node destructibleReceiversNode = rootNode["destructible_receivers"];

    if (destructibleReceiversNode)
    {
        if (!destructibleReceiversNode.IsSequence())
        {
            errorMessage = "destructible_receivers must be a sequence";
            return std::nullopt;
        }

        for (const YAML::Node &receiverNode : destructibleReceiversNode)
        {
            OutdoorDestructibleReceiver receiver = {};
            if (!parseOutdoorDestructibleReceiver(receiverNode, receiver, errorMessage))
            {
                return std::nullopt;
            }

            const auto duplicate = std::find_if(
                sceneData.destructibleReceivers.begin(),
                sceneData.destructibleReceivers.end(),
                [&receiver](const OutdoorDestructibleReceiver &existing)
                {
                    return existing.sourceObjectIndex == receiver.sourceObjectIndex;
                });
            if (duplicate != sceneData.destructibleReceivers.end())
            {
                errorMessage = "destructible receiver source_object_index must be unique";
                return std::nullopt;
            }

            sceneData.destructibleReceivers.push_back(std::move(receiver));
        }
    }

    if (triggerVolumesNode)
    {
        if (!triggerVolumesNode.IsSequence())
        {
            errorMessage = "trigger_volumes must be a sequence";
            return std::nullopt;
        }

        for (const YAML::Node &triggerNode : triggerVolumesNode)
        {
            OutdoorTriggerVolume trigger = {};
            if (!parseOutdoorTriggerVolume(triggerNode, trigger, errorMessage))
            {
                return std::nullopt;
            }

            sceneData.triggerVolumes.push_back(std::move(trigger));
        }
    }

    const YAML::Node mm9NpcGreetingsNode = rootNode["mm9_npc_greetings"];

    if (mm9NpcGreetingsNode)
    {
        if (!mm9NpcGreetingsNode.IsSequence())
        {
            errorMessage = "mm9_npc_greetings must be a sequence";
            return std::nullopt;
        }

        sceneData.mm9NpcGreetings.reserve(mm9NpcGreetingsNode.size());

        for (const YAML::Node &greetingNode : mm9NpcGreetingsNode)
        {
            OutdoorMm9NpcGreeting greeting = {};

            if (!greetingNode.IsMap()
                || !readScalarNode(
                    greetingNode,
                    "source_object_index",
                    greeting.sourceObjectIndex,
                    errorMessage)
                || !readScalarNode(greetingNode, "sound", greeting.soundName, errorMessage))
            {
                errorMessage = errorMessage.empty() ? "MM9 NPC greeting entry must be a map" : errorMessage;
                return std::nullopt;
            }

            const bool duplicate = std::any_of(
                sceneData.mm9NpcGreetings.begin(),
                sceneData.mm9NpcGreetings.end(),
                [&greeting](const OutdoorMm9NpcGreeting &existing)
                {
                    return existing.sourceObjectIndex == greeting.sourceObjectIndex;
                });

            if (duplicate)
            {
                errorMessage = "MM9 NPC greeting source_object_index must be unique";
                return std::nullopt;
            }

            sceneData.mm9NpcGreetings.push_back(std::move(greeting));
        }
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
        OutdoorSceneEntity entity = {};

        if (!parseOutdoorEntity(entityNode, entity, errorMessage))
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
        OutdoorSceneSpawn spawn = {};

        if (!parseOutdoorSpawn(spawnNode, spawn, errorMessage))
        {
            return std::nullopt;
        }

        sceneData.spawns.push_back(std::move(spawn));
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

    for (size_t actorIndex = 0; actorIndex < actorsNode.size(); ++actorIndex)
    {
        const YAML::Node actorNode = actorsNode[actorIndex];
        MapDeltaActor actor = {};

        if (!parseOutdoorActor(actorNode, actorIndex, actor, errorMessage))
        {
            return std::nullopt;
        }

        sceneData.initialState.actors.push_back(std::move(actor));
    }

    sceneData.initialState.spriteObjects.reserve(spriteObjectsNode.size());

    for (const YAML::Node &spriteObjectNode : spriteObjectsNode)
    {
        MapDeltaSpriteObject spriteObject = {};

        if (!parseOutdoorSpriteObject(spriteObjectNode, spriteObject, errorMessage))
        {
            return std::nullopt;
        }

        sceneData.initialState.spriteObjects.push_back(std::move(spriteObject));
    }

    sceneData.initialState.chests.reserve(chestsNode.size());

    for (const YAML::Node &chestNode : chestsNode)
    {
        MapDeltaChest chest = {};

        if (!parseOutdoorChest(chestNode, chest, errorMessage))
        {
            return std::nullopt;
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

    sceneData.baseContentCounts.entities = sceneData.entities.size();
    sceneData.baseContentCounts.spawns = sceneData.spawns.size();
    sceneData.baseContentCounts.actors = sceneData.initialState.actors.size();
    sceneData.baseContentCounts.spriteObjects = sceneData.initialState.spriteObjects.size();
    sceneData.baseContentCounts.chests = sceneData.initialState.chests.size();

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

    if (!parseOptionalSceneProfile(rootNode, sceneData.sceneProfile, errorMessage))
    {
        return false;
    }

    if (!parseOptionalLighting(rootNode, sceneData.lighting, errorMessage))
    {
        return false;
    }

    if (!parseOptionalRendering(rootNode, sceneData.rendering, errorMessage))
    {
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

        if (!parseOptionalLocationType(environmentNode, sceneData.environment.locationType, errorMessage))
        {
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
                "allow_rest",
                sceneData.runtimeRestrictions.allowRest,
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

    const YAML::Node surfaceAnimationsNode = rootNode["surface_animations"];

    if (surfaceAnimationsNode)
    {
        if (!surfaceAnimationsNode.IsSequence())
        {
            errorMessage = "surface_animations must be a sequence";
            return false;
        }

        for (const YAML::Node &animationNode : surfaceAnimationsNode)
        {
            OutdoorSceneSurfaceAnimation surfaceAnimation = {};

            if (!parseOutdoorSurfaceAnimation(animationNode, surfaceAnimation, errorMessage))
            {
                return false;
            }

            mergeOutdoorSurfaceAnimation(sceneData, surfaceAnimation);
        }
    }

    if (bmodelFacesNode)
    {
        if (!bmodelFacesNode.IsMap())
        {
            errorMessage = "bmodel_faces must be a map";
            return false;
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

        const YAML::Node perceptionFacesNode = bmodelFacesNode["perception_faces"];

        if (perceptionFacesNode)
        {
            if (!perceptionFacesNode.IsSequence())
            {
                errorMessage = "bmodel_faces.perception_faces must be a sequence";
                return false;
            }

            for (const YAML::Node &perceptionFaceNode : perceptionFacesNode)
            {
                OutdoorScenePerceptionFace face = {};

                if (!parseOutdoorPerceptionFace(perceptionFaceNode, face, errorMessage))
                {
                    return false;
                }

                mergeOutdoorPerceptionFace(sceneData, face);
            }
        }
    }

    const YAML::Node authoredContentNode = rootNode["authored_content"];

    if (authoredContentNode)
    {
        if (!authoredContentNode.IsMap())
        {
            errorMessage = "authored_content must be a map";
            return false;
        }

        const YAML::Node entitiesNode = authoredContentNode["entities"];

        if (entitiesNode)
        {
            if (!entitiesNode.IsSequence())
            {
                errorMessage = "authored_content.entities must be a sequence";
                return false;
            }

            sceneData.entities.reserve(sceneData.entities.size() + entitiesNode.size());

            for (const YAML::Node &entityNode : entitiesNode)
            {
                OutdoorSceneEntity entity = {};

                if (!parseOutdoorEntity(entityNode, entity, errorMessage))
                {
                    return false;
                }

                sceneData.entities.push_back(std::move(entity));
            }
        }

        const YAML::Node spawnsNode = authoredContentNode["spawns"];

        if (spawnsNode)
        {
            if (!spawnsNode.IsSequence())
            {
                errorMessage = "authored_content.spawns must be a sequence";
                return false;
            }

            sceneData.spawns.reserve(sceneData.spawns.size() + spawnsNode.size());

            for (const YAML::Node &spawnNode : spawnsNode)
            {
                OutdoorSceneSpawn spawn = {};

                if (!parseOutdoorSpawn(spawnNode, spawn, errorMessage))
                {
                    return false;
                }

                sceneData.spawns.push_back(std::move(spawn));
            }
        }

        const YAML::Node actorsNode = authoredContentNode["actors"];

        if (actorsNode)
        {
            if (!actorsNode.IsSequence())
            {
                errorMessage = "authored_content.actors must be a sequence";
                return false;
            }

            sceneData.initialState.actors.reserve(sceneData.initialState.actors.size() + actorsNode.size());

            for (const YAML::Node &actorNode : actorsNode)
            {
                MapDeltaActor actor = {};
                const size_t actorIndex = sceneData.initialState.actors.size();

                if (!parseOutdoorActor(actorNode, actorIndex, actor, errorMessage))
                {
                    return false;
                }

                sceneData.initialState.actors.push_back(std::move(actor));
            }
        }

        const YAML::Node spriteObjectsNode = authoredContentNode["sprite_objects"];

        if (spriteObjectsNode)
        {
            if (!spriteObjectsNode.IsSequence())
            {
                errorMessage = "authored_content.sprite_objects must be a sequence";
                return false;
            }

            sceneData.initialState.spriteObjects.reserve(
                sceneData.initialState.spriteObjects.size() + spriteObjectsNode.size());

            for (const YAML::Node &spriteObjectNode : spriteObjectsNode)
            {
                MapDeltaSpriteObject spriteObject = {};

                if (!parseOutdoorSpriteObject(spriteObjectNode, spriteObject, errorMessage))
                {
                    return false;
                }

                sceneData.initialState.spriteObjects.push_back(std::move(spriteObject));
            }
        }

        const YAML::Node chestsNode = authoredContentNode["chests"];

        if (chestsNode)
        {
            if (!chestsNode.IsSequence())
            {
                errorMessage = "authored_content.chests must be a sequence";
                return false;
            }

            sceneData.initialState.chests.reserve(sceneData.initialState.chests.size() + chestsNode.size());

            for (const YAML::Node &chestNode : chestsNode)
            {
                MapDeltaChest chest = {};

                if (!parseOutdoorChest(chestNode, chest, errorMessage))
                {
                    return false;
                }

                sceneData.initialState.chests.push_back(std::move(chest));
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

bool buildOutdoorMapStateFromScene(
    const OutdoorSceneData &sceneData,
    OutdoorMapData &outdoorMapData,
    MapDeltaData &mapDeltaData,
    std::string &errorMessage)
{
    outdoorMapData.sceneProfile = sceneData.sceneProfile;
    outdoorMapData.locationType = sceneData.environment.locationType;
    outdoorMapData.lightmapBrightnessScale = sceneData.lighting.lightmapBrightnessScale;
    if (sceneData.rendering.puddles)
    {
        OutdoorMapData::PuddleMask puddleMask = {};
        puddleMask.maskPath = sceneData.rendering.puddles->mask;
        puddleMask.originX = sceneData.rendering.puddles->origin[0];
        puddleMask.originY = sceneData.rendering.puddles->origin[1];
        puddleMask.extentX = sceneData.rendering.puddles->extent[0];
        puddleMask.extentY = sceneData.rendering.puddles->extent[1];
        outdoorMapData.puddleMask = puddleMask;
    }

    outdoorMapData.viewDistanceScale = sceneData.rendering.viewDistanceScale.value_or(
        sceneData.sceneProfile == OutdoorSceneProfile::BModelWorld
                && sceneData.environment.locationType == OutdoorLocationType::Enclosed
            ? 0.4f
            : 1.0f);
    outdoorMapData.skyTexture = sceneData.environment.skyTexture;
    outdoorMapData.groundTilesetName = sceneData.environment.groundTilesetName;
    outdoorMapData.masterTile = sceneData.environment.masterTile;
    outdoorMapData.tileSetLookupIndices = sceneData.environment.tileSetLookupIndices;
    outdoorMapData.mechanisms.clear();
    outdoorMapData.destructibles.clear();
    outdoorMapData.destructibleReceivers.clear();
    outdoorMapData.triggerVolumes.clear();
    outdoorMapData.mm9NpcGreetings = sceneData.mm9NpcGreetings;

    if (sceneData.sceneProfile == OutdoorSceneProfile::ClassicOdm
        && (!sceneData.mechanisms.empty()
            || !sceneData.destructibles.empty()
            || !sceneData.destructibleReceivers.empty()
            || !sceneData.triggerVolumes.empty()))
    {
        errorMessage = "outdoor mechanisms and triggers require scene_profile bmodel_world";
        return false;
    }

    for (const OutdoorBModelMechanism &mechanism : sceneData.mechanisms)
    {
        if (mechanism.hasBModelBinding && mechanism.bmodelIndex >= outdoorMapData.bmodels.size())
        {
            errorMessage = "mechanism BModel binding is out of bounds";
            return false;
        }

        outdoorMapData.mechanisms.push_back(mechanism);
    }

    for (const OutdoorDestructible &destructible : sceneData.destructibles)
    {
        if (destructible.bmodelIndex >= outdoorMapData.bmodels.size())
        {
            errorMessage = "destructible BModel binding is out of bounds";
            return false;
        }

        if (std::any_of(
            destructible.auxiliaryBmodelIndices.begin(),
            destructible.auxiliaryBmodelIndices.end(),
            [&outdoorMapData](size_t bmodelIndex)
            {
                return bmodelIndex >= outdoorMapData.bmodels.size();
            }))
        {
            errorMessage = "destructible auxiliary BModel binding is out of bounds";
            return false;
        }

        outdoorMapData.destructibles.push_back(destructible);
    }

    outdoorMapData.destructibleReceivers = sceneData.destructibleReceivers;
    outdoorMapData.triggerVolumes = sceneData.triggerVolumes;
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
            face.perceptionDifficulty = -1;
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

    for (const OutdoorScenePerceptionFace &perceptionFace : sceneData.perceptionFaces)
    {
        if (perceptionFace.bmodelIndex >= outdoorMapData.bmodels.size()
            || perceptionFace.faceIndex >= outdoorMapData.bmodels[perceptionFace.bmodelIndex].faces.size())
        {
            errorMessage = "scene perception face index is out of bounds";
            return false;
        }

        OutdoorBModelFace &face =
            outdoorMapData.bmodels[perceptionFace.bmodelIndex].faces[perceptionFace.faceIndex];

        if (!hasFaceAttribute(face.attributes, FaceAttribute::IsSecret))
        {
            errorMessage = "scene perception face must have the secret attribute";
            return false;
        }

        face.perceptionDifficulty = perceptionFace.difficulty;
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
