#pragma once

#include "game/mm9/Mm9DatWorld.h"
#include "game/render/lighting/RenderLight.h"

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
enum class Mm9LightSourcePropertyKind
{
    String,
    Integer,
    Number,
    Boolean,
    Vec3,
    NumberList,
    StringList,
};

struct Mm9LightColor
{
    float r = 0.0f;
    float g = 0.0f;
    float b = 0.0f;
};

struct Mm9LightSourceProperty
{
    std::string name;
    Mm9LightSourcePropertyKind kind = Mm9LightSourcePropertyKind::String;
    std::string stringValue;
    int integerValue = 0;
    float numberValue = 0.0f;
    bool booleanValue = false;
    Mm9DatVec3 vec3Value;
    std::vector<float> numberValues;
    std::vector<std::string> stringValues;
    std::string rawValue;
};

struct Mm9LightSourceObject
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    std::vector<Mm9LightSourceProperty> properties;
};

struct Mm9LightLayerDiagnostic
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    std::string propertyName;
    std::string message;
};

struct Mm9WorldLightingInfo
{
    std::string rawPropertyString;
    float sourceLightMapGridSize = 0.0f;
    Mm9LightColor ambientLight;
    bool hasAmbientLight = false;
    float lmGridSize = 0.0f;
    bool hasLmGridSize = false;
    float maxLmSize = 0.0f;
    bool hasMaxLmSize = false;
    float pBlockSize = 0.0f;
    bool hasPBlockSize = false;
    std::vector<Mm9LightLayerDiagnostic> diagnostics;
};

struct Mm9LightObject
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    Mm9DatVec3 positionLt;
    bool hasPosition = false;
    Mm9DatVec3 rotationLt;
    bool hasRotation = false;
    float lightRadius = 0.0f;
    bool hasLightRadius = false;
    Mm9LightColor lightColor;
    bool hasLightColor = false;
    Mm9LightColor innerColor;
    bool hasInnerColor = false;
    Mm9LightColor outerColor;
    bool hasOuterColor = false;
    float brightScale = 1.0f;
    bool hasBrightScale = false;
    float objectBrightScale = 1.0f;
    bool hasObjectBrightScale = false;
    std::vector<float> attCoefs;
    std::vector<float> attExps;
    std::string attenuation = "Quartic";
    bool hasAttenuation = false;
    bool validAttenuation = true;
    float size = 0.0f;
    bool hasSize = false;
    std::string attType;
    bool hasAttType = false;
    bool castShadowMesh = false;
    bool hasCastShadowMesh = false;
    bool lightObjects = false;
    bool hasLightObjects = false;
    bool fastLightObjects = false;
    bool hasFastLightObjects = false;
    bool castShadows = false;
    bool hasCastShadows = false;
    bool clipLight = false;
    bool hasClipLight = false;
    float convertToAmbient = 0.0f;
    bool hasConvertToAmbient = false;
    float fov = 0.0f;
    bool hasFov = false;
    float time = 0.0f;
    bool hasTime = false;
    std::string lightGroup;
    bool hasLightGroup = false;
    Mm9LightColor effectiveColor;
    bool hasEffectiveColor = false;
    Mm9LightColor effectiveObjectLightColor;
    bool hasEffectiveObjectLightColor = false;
    std::vector<float> effectiveAttCoefs;
    float effectiveFovCos = 0.0f;
    bool hasEffectiveFovCos = false;
    bool effectiveLightObjects = false;
    bool effectiveFastLightObjects = false;
    bool effectiveCastShadows = false;
    bool effectiveClipLight = false;
    bool staticObjectLightEligible = false;
    bool fastObjectLightingSource = false;
    std::vector<Mm9LightSourceProperty> sourceProperties;
    std::vector<std::string> unsupportedProperties;
};

struct Mm9LightLayer
{
    Mm9WorldLightingInfo worldInfo;
    std::vector<Mm9LightObject> lights;
    std::vector<Mm9LightLayerDiagnostic> diagnostics;
};

Mm9LightSourceProperty mm9LightStringProperty(const std::string &name, const std::string &value);
Mm9LightSourceProperty mm9LightIntegerProperty(const std::string &name, int value);
Mm9LightSourceProperty mm9LightNumberProperty(const std::string &name, float value);
Mm9LightSourceProperty mm9LightBooleanProperty(const std::string &name, bool value);
Mm9LightSourceProperty mm9LightVec3Property(const std::string &name, const Mm9DatVec3 &value);
Mm9LightSourceProperty mm9LightNumberListProperty(const std::string &name, const std::vector<float> &values);
Mm9LightSourceProperty mm9LightStringListProperty(
    const std::string &name,
    const std::vector<std::string> &values);

Mm9WorldLightingInfo parseMm9WorldLightingInfo(const Mm9DatWorldInfo &worldInfo);

Mm9LightLayer buildMm9LightLayer(
    const Mm9DatWorldInfo &worldInfo,
    const std::vector<Mm9LightSourceObject> &sourceObjects);

std::optional<RenderLight> convertMm9LightObjectToRenderLight(
    const Mm9LightObject &lightObject,
    float scale = Mm9DatToOpenYammScale);

std::vector<RenderLight> buildMm9StaticRenderLights(
    const Mm9LightLayer &lightLayer,
    float scale = Mm9DatToOpenYammScale);
}
