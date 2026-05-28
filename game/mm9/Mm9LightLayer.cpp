#include "game/mm9/Mm9LightLayer.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <set>
#include <sstream>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float DefaultLightRadius = 0.0f;

std::string lowerCopy(const std::string &value)
{
    std::string output = value;
    for (char &character : output)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }
    return output;
}

bool equalsIgnoreCase(const std::string &left, const std::string &right)
{
    return lowerCopy(left) == lowerCopy(right);
}

std::optional<float> parseFloat(const std::string &text)
{
    if (text.empty())
    {
        return std::nullopt;
    }

    char *pEnd = nullptr;
    const float value = std::strtof(text.c_str(), &pEnd);
    if (pEnd == text.c_str() || *pEnd != '\0')
    {
        return std::nullopt;
    }

    return value;
}

std::vector<std::string> tokenizeWorldInfo(const std::string &propertyString)
{
    std::string normalized;
    normalized.reserve(propertyString.size());
    for (char character : propertyString)
    {
        normalized.push_back(character == ';' ? ' ' : character);
    }

    std::istringstream stream(normalized);
    std::vector<std::string> tokens;
    std::string token;
    while (stream >> token)
    {
        tokens.push_back(token);
    }
    return tokens;
}

void addDiagnostic(
    std::vector<Mm9LightLayerDiagnostic> &diagnostics,
    size_t sourceObjectIndex,
    const std::string &sourceClass,
    const std::string &sourceName,
    const std::string &propertyName,
    const std::string &message)
{
    Mm9LightLayerDiagnostic diagnostic = {};
    diagnostic.sourceObjectIndex = sourceObjectIndex;
    diagnostic.sourceClass = sourceClass;
    diagnostic.sourceName = sourceName;
    diagnostic.propertyName = propertyName;
    diagnostic.message = message;
    diagnostics.push_back(std::move(diagnostic));
}

void addObjectDiagnostic(
    Mm9LightLayer &layer,
    const Mm9LightSourceObject &sourceObject,
    const std::string &propertyName,
    const std::string &message)
{
    addDiagnostic(
        layer.diagnostics,
        sourceObject.sourceObjectIndex,
        sourceObject.sourceClass,
        sourceObject.sourceName,
        propertyName,
        message);
}

const Mm9LightSourceProperty *findProperty(const Mm9LightSourceObject &object, const std::string &name)
{
    for (const Mm9LightSourceProperty &property : object.properties)
    {
        if (equalsIgnoreCase(property.name, name))
        {
            return &property;
        }
    }
    return nullptr;
}

bool boolProperty(
    const Mm9LightSourceObject &object,
    const std::string &name,
    bool fallback,
    Mm9LightLayer &layer)
{
    const Mm9LightSourceProperty *pProperty = findProperty(object, name);
    if (pProperty == nullptr)
    {
        return fallback;
    }
    if (pProperty->kind == Mm9LightSourcePropertyKind::Boolean)
    {
        return pProperty->booleanValue;
    }
    if (pProperty->kind == Mm9LightSourcePropertyKind::Integer)
    {
        return pProperty->integerValue != 0;
    }
    if (pProperty->kind == Mm9LightSourcePropertyKind::Number)
    {
        return pProperty->numberValue != 0.0f;
    }

    addObjectDiagnostic(layer, object, name, "invalid_boolean_property");
    return fallback;
}

float numberProperty(
    const Mm9LightSourceObject &object,
    const std::string &name,
    float fallback,
    bool &present,
    Mm9LightLayer &layer)
{
    const Mm9LightSourceProperty *pProperty = findProperty(object, name);
    present = false;
    if (pProperty == nullptr)
    {
        return fallback;
    }
    if (pProperty->kind == Mm9LightSourcePropertyKind::Number)
    {
        present = true;
        return pProperty->numberValue;
    }
    if (pProperty->kind == Mm9LightSourcePropertyKind::Integer)
    {
        present = true;
        return static_cast<float>(pProperty->integerValue);
    }

    addObjectDiagnostic(layer, object, name, "invalid_number_property");
    return fallback;
}

std::string stringProperty(
    const Mm9LightSourceObject &object,
    const std::string &name,
    bool &present,
    Mm9LightLayer &layer)
{
    const Mm9LightSourceProperty *pProperty = findProperty(object, name);
    present = false;
    if (pProperty == nullptr)
    {
        return {};
    }
    if (pProperty->kind == Mm9LightSourcePropertyKind::String)
    {
        present = true;
        return pProperty->stringValue;
    }
    if (pProperty->kind == Mm9LightSourcePropertyKind::Integer)
    {
        present = true;
        return std::to_string(pProperty->integerValue);
    }

    addObjectDiagnostic(layer, object, name, "invalid_string_property");
    return {};
}

Mm9DatVec3 vec3Property(
    const Mm9LightSourceObject &object,
    const std::string &name,
    bool &present,
    Mm9LightLayer &layer)
{
    const Mm9LightSourceProperty *pProperty = findProperty(object, name);
    present = false;
    if (pProperty == nullptr)
    {
        return {};
    }
    if (pProperty->kind == Mm9LightSourcePropertyKind::Vec3)
    {
        present = true;
        return pProperty->vec3Value;
    }

    addObjectDiagnostic(layer, object, name, "invalid_vec3_property");
    return {};
}

std::vector<float> numberListProperty(
    const Mm9LightSourceObject &object,
    const std::string &name,
    Mm9LightLayer &layer)
{
    const Mm9LightSourceProperty *pProperty = findProperty(object, name);
    if (pProperty == nullptr)
    {
        return {};
    }
    if (pProperty->kind == Mm9LightSourcePropertyKind::NumberList)
    {
        return pProperty->numberValues;
    }
    if (pProperty->kind == Mm9LightSourcePropertyKind::Vec3)
    {
        return {pProperty->vec3Value.x, pProperty->vec3Value.y, pProperty->vec3Value.z};
    }

    addObjectDiagnostic(layer, object, name, "invalid_number_list_property");
    return {};
}

Mm9LightColor colorProperty(
    const Mm9LightSourceObject &object,
    const std::string &name,
    bool &present,
    Mm9LightLayer &layer)
{
    const Mm9DatVec3 value = vec3Property(object, name, present, layer);
    return {value.x, value.y, value.z};
}

bool lightClass(const std::string &sourceClass)
{
    return equalsIgnoreCase(sourceClass, "Light")
        || equalsIgnoreCase(sourceClass, "DirLight")
        || equalsIgnoreCase(sourceClass, "ObjectLight");
}

std::set<std::string> knownLightProperties()
{
    return {
        "attcoefs",
        "attenuation",
        "attexps",
        "brightscale",
        "castshadows",
        "cliplight",
        "converttoambient",
        "fastlightobjects",
        "fov",
        "innercolor",
        "lightcolor",
        "lightgroup",
        "lightobjects",
        "lightradius",
        "name",
        "objectbrightscale",
        "outercolor",
        "pos",
        "rotation",
        "time",
    };
}

uint8_t colorChannel(float value)
{
    return static_cast<uint8_t>(std::clamp(std::lround(value), 0l, 255l));
}

uint32_t makeAbgr(const Mm9LightColor &color)
{
    const uint32_t red = colorChannel(color.r);
    const uint32_t green = colorChannel(color.g);
    const uint32_t blue = colorChannel(color.b);
    return 0xff000000u | (blue << 16) | (green << 8) | red;
}

bx::Vec3 ltToOpenYamm(const Mm9DatVec3 &value, float scale)
{
    return {value.x * scale, value.z * scale, value.y * scale};
}

}

Mm9LightSourceProperty mm9LightStringProperty(const std::string &name, const std::string &value)
{
    Mm9LightSourceProperty property = {};
    property.name = name;
    property.kind = Mm9LightSourcePropertyKind::String;
    property.stringValue = value;
    property.rawValue = value;
    return property;
}

Mm9LightSourceProperty mm9LightIntegerProperty(const std::string &name, int value)
{
    Mm9LightSourceProperty property = {};
    property.name = name;
    property.kind = Mm9LightSourcePropertyKind::Integer;
    property.integerValue = value;
    property.numberValue = static_cast<float>(value);
    property.rawValue = std::to_string(value);
    return property;
}

Mm9LightSourceProperty mm9LightNumberProperty(const std::string &name, float value)
{
    Mm9LightSourceProperty property = {};
    property.name = name;
    property.kind = Mm9LightSourcePropertyKind::Number;
    property.numberValue = value;
    property.integerValue = static_cast<int>(value);
    property.rawValue = std::to_string(value);
    return property;
}

Mm9LightSourceProperty mm9LightBooleanProperty(const std::string &name, bool value)
{
    Mm9LightSourceProperty property = {};
    property.name = name;
    property.kind = Mm9LightSourcePropertyKind::Boolean;
    property.booleanValue = value;
    property.integerValue = value ? 1 : 0;
    property.numberValue = value ? 1.0f : 0.0f;
    property.rawValue = value ? "true" : "false";
    return property;
}

Mm9LightSourceProperty mm9LightVec3Property(const std::string &name, const Mm9DatVec3 &value)
{
    Mm9LightSourceProperty property = {};
    property.name = name;
    property.kind = Mm9LightSourcePropertyKind::Vec3;
    property.vec3Value = value;
    property.rawValue =
        std::to_string(value.x) + " " + std::to_string(value.y) + " " + std::to_string(value.z);
    return property;
}

Mm9LightSourceProperty mm9LightNumberListProperty(const std::string &name, const std::vector<float> &values)
{
    Mm9LightSourceProperty property = {};
    property.name = name;
    property.kind = Mm9LightSourcePropertyKind::NumberList;
    property.numberValues = values;
    return property;
}

Mm9LightSourceProperty mm9LightStringListProperty(
    const std::string &name,
    const std::vector<std::string> &values)
{
    Mm9LightSourceProperty property = {};
    property.name = name;
    property.kind = Mm9LightSourcePropertyKind::StringList;
    property.stringValues = values;
    return property;
}

Mm9WorldLightingInfo parseMm9WorldLightingInfo(const Mm9DatWorldInfo &worldInfo)
{
    Mm9WorldLightingInfo lightingInfo = {};
    lightingInfo.rawPropertyString = worldInfo.propertyString;
    lightingInfo.sourceLightMapGridSize = worldInfo.lightMapGridSize;

    const std::vector<std::string> tokens = tokenizeWorldInfo(worldInfo.propertyString);
    for (size_t index = 0; index < tokens.size(); ++index)
    {
        const std::string key = lowerCopy(tokens[index]);
        if (key == "ambientlight")
        {
            if (index + 3 >= tokens.size())
            {
                addDiagnostic(lightingInfo.diagnostics, 0, "WorldInfo", "", "AmbientLight", "invalid_world_info_value");
                continue;
            }

            const std::optional<float> red = parseFloat(tokens[index + 1]);
            const std::optional<float> green = parseFloat(tokens[index + 2]);
            const std::optional<float> blue = parseFloat(tokens[index + 3]);
            if (!red || !green || !blue)
            {
                addDiagnostic(lightingInfo.diagnostics, 0, "WorldInfo", "", "AmbientLight", "invalid_world_info_value");
                continue;
            }

            lightingInfo.ambientLight = {*red, *green, *blue};
            lightingInfo.hasAmbientLight = true;
            index += 3;
        }
        else if (key == "lmgridsize" || key == "maxlmsize" || key == "pblocksize")
        {
            if (index + 1 >= tokens.size())
            {
                addDiagnostic(lightingInfo.diagnostics, 0, "WorldInfo", "", tokens[index], "invalid_world_info_value");
                continue;
            }

            const std::optional<float> value = parseFloat(tokens[index + 1]);
            if (!value)
            {
                addDiagnostic(lightingInfo.diagnostics, 0, "WorldInfo", "", tokens[index], "invalid_world_info_value");
                continue;
            }

            if (key == "lmgridsize")
            {
                lightingInfo.lmGridSize = *value;
                lightingInfo.hasLmGridSize = true;
            }
            else if (key == "maxlmsize")
            {
                lightingInfo.maxLmSize = *value;
                lightingInfo.hasMaxLmSize = true;
            }
            else
            {
                lightingInfo.pBlockSize = *value;
                lightingInfo.hasPBlockSize = true;
            }
            ++index;
        }
    }

    return lightingInfo;
}

Mm9LightLayer buildMm9LightLayer(
    const Mm9DatWorldInfo &worldInfo,
    const std::vector<Mm9LightSourceObject> &sourceObjects)
{
    Mm9LightLayer layer = {};
    layer.worldInfo = parseMm9WorldLightingInfo(worldInfo);
    layer.diagnostics = layer.worldInfo.diagnostics;
    const std::set<std::string> knownProperties = knownLightProperties();

    for (const Mm9LightSourceObject &sourceObject : sourceObjects)
    {
        if (!lightClass(sourceObject.sourceClass))
        {
            continue;
        }

        Mm9LightObject light = {};
        light.sourceObjectIndex = sourceObject.sourceObjectIndex;
        light.sourceClass = sourceObject.sourceClass;
        light.sourceName = sourceObject.sourceName;
        light.sourceProperties = sourceObject.properties;

        bool present = false;
        const std::string sourceName = stringProperty(sourceObject, "Name", present, layer);
        if (present)
        {
            light.sourceName = sourceName;
        }
        light.positionLt = vec3Property(sourceObject, "Pos", light.hasPosition, layer);
        light.rotationLt = vec3Property(sourceObject, "Rotation", light.hasRotation, layer);
        light.lightRadius = numberProperty(
            sourceObject,
            "LightRadius",
            DefaultLightRadius,
            light.hasLightRadius,
            layer);
        light.lightColor = colorProperty(sourceObject, "LightColor", light.hasLightColor, layer);
        light.innerColor = colorProperty(sourceObject, "InnerColor", light.hasInnerColor, layer);
        light.outerColor = colorProperty(sourceObject, "OuterColor", light.hasOuterColor, layer);
        light.brightScale = numberProperty(sourceObject, "BrightScale", 1.0f, light.hasBrightScale, layer);
        light.objectBrightScale = numberProperty(
            sourceObject,
            "ObjectBrightScale",
            1.0f,
            light.hasObjectBrightScale,
            layer);
        light.attCoefs = numberListProperty(sourceObject, "AttCoefs", layer);
        light.attExps = numberListProperty(sourceObject, "AttExps", layer);
        light.attenuation = numberListProperty(sourceObject, "Attenuation", layer);
        light.lightObjects = boolProperty(sourceObject, "LightObjects", false, layer);
        light.hasLightObjects = findProperty(sourceObject, "LightObjects") != nullptr;
        light.fastLightObjects = boolProperty(sourceObject, "FastLightObjects", false, layer);
        light.hasFastLightObjects = findProperty(sourceObject, "FastLightObjects") != nullptr;
        light.castShadows = boolProperty(sourceObject, "CastShadows", false, layer);
        light.hasCastShadows = findProperty(sourceObject, "CastShadows") != nullptr;
        light.clipLight = boolProperty(sourceObject, "ClipLight", false, layer);
        light.hasClipLight = findProperty(sourceObject, "ClipLight") != nullptr;
        light.convertToAmbient = boolProperty(sourceObject, "ConvertToAmbient", false, layer);
        light.hasConvertToAmbient = findProperty(sourceObject, "ConvertToAmbient") != nullptr;
        light.fov = numberProperty(sourceObject, "FOV", 0.0f, light.hasFov, layer);
        light.time = numberProperty(sourceObject, "Time", 0.0f, light.hasTime, layer);
        light.lightGroup = stringProperty(sourceObject, "LightGroup", light.hasLightGroup, layer);

        if (!light.hasPosition)
        {
            addObjectDiagnostic(layer, sourceObject, "Pos", "missing_light_position");
        }
        if (!light.hasLightColor)
        {
            addObjectDiagnostic(layer, sourceObject, "LightColor", "missing_light_color");
        }
        if (!light.hasLightRadius)
        {
            addObjectDiagnostic(layer, sourceObject, "LightRadius", "missing_light_radius");
        }

        for (const Mm9LightSourceProperty &property : sourceObject.properties)
        {
            if (knownProperties.count(lowerCopy(property.name)) == 0)
            {
                light.unsupportedProperties.push_back(property.name);
                addObjectDiagnostic(layer, sourceObject, property.name, "unsupported_light_property");
            }
        }

        layer.lights.push_back(std::move(light));
    }

    return layer;
}

std::optional<RenderLight> convertMm9LightObjectToRenderLight(
    const Mm9LightObject &lightObject,
    float scale)
{
    if (!lightObject.hasPosition
        || !lightObject.hasLightColor
        || !lightObject.hasLightRadius
        || lightObject.lightRadius <= 0.0f)
    {
        return std::nullopt;
    }

    RenderLight light = {};
    light.position = ltToOpenYamm(lightObject.positionLt, scale);
    light.radius = lightObject.lightRadius * scale;
    light.colorAbgr = makeAbgr(lightObject.lightColor);
    light.intensity = lightObject.hasBrightScale ? lightObject.brightScale : 1.0f;
    light.kind = RenderLightKind::Static;
    light.stableId = static_cast<uint32_t>(lightObject.sourceObjectIndex + 1);
    light.dynamic = false;
    light.important = lightObject.lightObjects && !lightObject.fastLightObjects;
    return light;
}

std::vector<RenderLight> buildMm9StaticRenderLights(
    const Mm9LightLayer &lightLayer,
    float scale)
{
    std::vector<RenderLight> lights;
    lights.reserve(lightLayer.lights.size());
    for (const Mm9LightObject &lightObject : lightLayer.lights)
    {
        const std::optional<RenderLight> light = convertMm9LightObjectToRenderLight(lightObject, scale);
        if (light)
        {
            lights.push_back(*light);
        }
    }
    return lights;
}
}
