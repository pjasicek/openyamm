#include "game/mm9/Mm9SkyLayer.h"

#include <algorithm>
#include <cctype>
#include <unordered_map>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float DefaultInnerPercent = 0.1f;
constexpr float DegenerateExtentEpsilon = 0.0001f;

std::string normalizedKey(const std::string &value)
{
    std::string result;
    result.reserve(value.size());

    for (char character : value)
    {
        result.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
    }

    return result;
}

bool equalsIgnoreCase(const std::string &left, const std::string &right)
{
    if (left.size() != right.size())
    {
        return false;
    }

    for (size_t index = 0; index < left.size(); ++index)
    {
        const char leftCharacter =
            static_cast<char>(std::tolower(static_cast<unsigned char>(left[index])));
        const char rightCharacter =
            static_cast<char>(std::tolower(static_cast<unsigned char>(right[index])));
        if (leftCharacter != rightCharacter)
        {
            return false;
        }
    }

    return true;
}

const Mm9SkySourceProperty *findProperty(const Mm9SkySourceObject &object, const char *pName)
{
    for (const Mm9SkySourceProperty &property : object.properties)
    {
        if (equalsIgnoreCase(property.name, pName))
        {
            return &property;
        }
    }

    return nullptr;
}

std::string stringProperty(const Mm9SkySourceObject &object, const char *pName, const std::string &fallback)
{
    const Mm9SkySourceProperty *pProperty = findProperty(object, pName);
    if (pProperty == nullptr || pProperty->kind != Mm9SkySourcePropertyKind::String)
    {
        return fallback;
    }

    return pProperty->stringValue;
}

int integerProperty(const Mm9SkySourceObject &object, const char *pName, int fallback)
{
    const Mm9SkySourceProperty *pProperty = findProperty(object, pName);
    if (pProperty == nullptr)
    {
        return fallback;
    }

    if (pProperty->kind == Mm9SkySourcePropertyKind::Integer)
    {
        return pProperty->integerValue;
    }
    if (pProperty->kind == Mm9SkySourcePropertyKind::Number)
    {
        return static_cast<int>(pProperty->numberValue);
    }

    return fallback;
}

float numberProperty(const Mm9SkySourceObject &object, const char *pName, float fallback)
{
    const Mm9SkySourceProperty *pProperty = findProperty(object, pName);
    if (pProperty == nullptr)
    {
        return fallback;
    }

    if (pProperty->kind == Mm9SkySourcePropertyKind::Number)
    {
        return pProperty->numberValue;
    }
    if (pProperty->kind == Mm9SkySourcePropertyKind::Integer)
    {
        return static_cast<float>(pProperty->integerValue);
    }

    return fallback;
}

Mm9DatVec3 vec3Property(const Mm9SkySourceObject &object, const char *pName, const Mm9DatVec3 &fallback)
{
    const Mm9SkySourceProperty *pProperty = findProperty(object, pName);
    if (pProperty == nullptr || pProperty->kind != Mm9SkySourcePropertyKind::Vec3)
    {
        return fallback;
    }

    return pProperty->vec3Value;
}

bool nonZeroDims(const Mm9DatVec3 &value)
{
    return value.x != 0.0f && value.y != 0.0f && value.z != 0.0f;
}

Mm9DatVec3 add(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return {left.x + right.x, left.y + right.y, left.z + right.z};
}

Mm9DatVec3 subtract(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return {left.x - right.x, left.y - right.y, left.z - right.z};
}

Mm9DatVec3 multiply(const Mm9DatVec3 &left, const Mm9DatVec3 &right)
{
    return {left.x * right.x, left.y * right.y, left.z * right.z};
}

std::optional<size_t> findModelIndexByName(
    const std::unordered_map<std::string, size_t> &modelIndexByName,
    const std::string &name)
{
    const std::unordered_map<std::string, size_t>::const_iterator modelIterator =
        modelIndexByName.find(normalizedKey(name));
    if (modelIterator == modelIndexByName.end())
    {
        return std::nullopt;
    }

    return modelIterator->second;
}

void addUniqueModelIndex(std::vector<size_t> &modelIndices, size_t modelIndex)
{
    if (std::find(modelIndices.begin(), modelIndices.end(), modelIndex) == modelIndices.end())
    {
        modelIndices.push_back(modelIndex);
    }
}

void addDiagnostic(
    Mm9SkyLayer &layer,
    const Mm9SkySourceObject &sourceObject,
    const std::string &propertyName,
    const std::string &message)
{
    Mm9SkyLayerDiagnostic diagnostic = {};
    diagnostic.sourceObjectIndex = sourceObject.sourceObjectIndex;
    diagnostic.sourceClass = sourceObject.sourceClass;
    diagnostic.sourceName = sourceObject.sourceName;
    diagnostic.propertyName = propertyName;
    diagnostic.message = message;
    layer.diagnostics.push_back(std::move(diagnostic));
}

}

Mm9SkySourceProperty mm9SkyStringProperty(const std::string &name, const std::string &value)
{
    Mm9SkySourceProperty property = {};
    property.name = name;
    property.kind = Mm9SkySourcePropertyKind::String;
    property.stringValue = value;
    return property;
}

Mm9SkySourceProperty mm9SkyIntegerProperty(const std::string &name, int value)
{
    Mm9SkySourceProperty property = {};
    property.name = name;
    property.kind = Mm9SkySourcePropertyKind::Integer;
    property.integerValue = value;
    property.numberValue = static_cast<float>(value);
    return property;
}

Mm9SkySourceProperty mm9SkyNumberProperty(const std::string &name, float value)
{
    Mm9SkySourceProperty property = {};
    property.name = name;
    property.kind = Mm9SkySourcePropertyKind::Number;
    property.numberValue = value;
    property.integerValue = static_cast<int>(value);
    return property;
}

Mm9SkySourceProperty mm9SkyVec3Property(const std::string &name, const Mm9DatVec3 &value)
{
    Mm9SkySourceProperty property = {};
    property.name = name;
    property.kind = Mm9SkySourcePropertyKind::Vec3;
    property.vec3Value = value;
    return property;
}

Mm9SkyDef makeMm9SkyDef(
    size_t sourceObjectIndex,
    const std::string &sourceClass,
    const std::string &sourceName,
    const Mm9DatVec3 &positionLt,
    const Mm9DatVec3 &skyDimsLt,
    const Mm9DatVec3 &innerPercentLt,
    int flags,
    int index)
{
    Mm9SkyDef skyDef = {};
    skyDef.sourceObjectIndex = sourceObjectIndex;
    skyDef.sourceClass = sourceClass;
    skyDef.sourceName = sourceName;
    skyDef.positionLt = positionLt;
    skyDef.skyDimsLt = skyDimsLt;
    skyDef.innerPercentLt = innerPercentLt;
    skyDef.flags = flags;
    skyDef.index = index;

    if (!nonZeroDims(skyDimsLt))
    {
        return skyDef;
    }

    const Mm9DatVec3 innerDimsLt = multiply(skyDimsLt, innerPercentLt);
    skyDef.minLt = subtract(positionLt, skyDimsLt);
    skyDef.maxLt = add(positionLt, skyDimsLt);
    skyDef.viewMinLt = subtract(positionLt, innerDimsLt);
    skyDef.viewMaxLt = add(positionLt, innerDimsLt);
    skyDef.valid = true;
    return skyDef;
}

Mm9SkyLayer buildMm9SkyLayer(
    const Mm9DatWorld &world,
    const std::vector<Mm9SkySourceObject> &sourceObjects,
    const std::vector<Mm9DatModelRenderRole> &modelRoles)
{
    Mm9SkyLayer layer = {};
    layer.definitions.reserve(sourceObjects.size());
    layer.objects.reserve(sourceObjects.size());
    layer.skyModelIndices.reserve(modelRoles.size() + sourceObjects.size());

    std::unordered_map<std::string, size_t> modelIndexByName;
    modelIndexByName.reserve(world.worldModels.size());

    for (size_t modelIndex = 0; modelIndex < world.worldModels.size(); ++modelIndex)
    {
        modelIndexByName[normalizedKey(world.worldModels[modelIndex].name)] = modelIndex;
    }

    for (const Mm9DatModelRenderRole &role : modelRoles)
    {
        if (role.sky && role.sourceModelIndex < world.worldModels.size())
        {
            addUniqueModelIndex(layer.skyModelIndices, role.sourceModelIndex);
        }
    }

    for (const Mm9SkySourceObject &sourceObject : sourceObjects)
    {
        const bool demoSkyWorldModel = equalsIgnoreCase(sourceObject.sourceClass, "DemoSkyWorldModel");
        const bool skyPointer = equalsIgnoreCase(sourceObject.sourceClass, "SkyPointer");
        const bool todSky = equalsIgnoreCase(sourceObject.sourceClass, "TOD_Sky");
        if (!demoSkyWorldModel && !skyPointer && !todSky)
        {
            continue;
        }

        const std::string sourceName = stringProperty(sourceObject, "Name", sourceObject.sourceName);
        const Mm9DatVec3 positionLt = vec3Property(sourceObject, "Pos", {});
        const Mm9DatVec3 skyDimsLt = vec3Property(sourceObject, "SkyDims", {});
        const Mm9DatVec3 innerPercentLt = {
            numberProperty(sourceObject, "InnerPercentX", DefaultInnerPercent),
            numberProperty(sourceObject, "InnerPercentY", DefaultInnerPercent),
            numberProperty(sourceObject, "InnerPercentZ", DefaultInnerPercent),
        };
        const int flags = integerProperty(sourceObject, "Flags", 0);
        const int index = integerProperty(sourceObject, "Index", 0);
        if (demoSkyWorldModel && findProperty(sourceObject, "SkyDims") == nullptr)
        {
            addDiagnostic(layer, sourceObject, "SkyDims", "missing_sky_dimensions");
        }

        Mm9SkyObject skyObject = {};
        skyObject.sourceObjectIndex = sourceObject.sourceObjectIndex;
        skyObject.sourceClass = sourceObject.sourceClass;
        skyObject.sourceName = sourceName;
        skyObject.skyObjectName =
            skyPointer ? stringProperty(sourceObject, "SkyObjectName", sourceName) : sourceName;
        skyObject.flags = flags;
        skyObject.index = index;

        const std::optional<size_t> modelIndex = findModelIndexByName(modelIndexByName, skyObject.skyObjectName);
        if (modelIndex)
        {
            skyObject.sourceModelIndex = *modelIndex;
            skyObject.hasSourceModel = true;
            addUniqueModelIndex(layer.skyModelIndices, *modelIndex);
        }
        else
        {
            addDiagnostic(layer, sourceObject, skyObject.skyObjectName, "unlinked_sky_model");
        }

        layer.objects.push_back(std::move(skyObject));
        if (demoSkyWorldModel || skyPointer)
        {
            layer.definitions.push_back(makeMm9SkyDef(
                sourceObject.sourceObjectIndex,
                sourceObject.sourceClass,
                sourceName,
                positionLt,
                skyDimsLt,
                innerPercentLt,
                flags,
                index));
        }
    }

    std::sort(
        layer.definitions.begin(),
        layer.definitions.end(),
        [](const Mm9SkyDef &left, const Mm9SkyDef &right)
        {
            if (left.index != right.index)
            {
                return left.index < right.index;
            }
            return left.sourceObjectIndex < right.sourceObjectIndex;
        });

    std::sort(
        layer.objects.begin(),
        layer.objects.end(),
        [](const Mm9SkyObject &left, const Mm9SkyObject &right)
        {
            if (left.index != right.index)
            {
                return left.index < right.index;
            }
            return left.sourceObjectIndex < right.sourceObjectIndex;
        });

    std::sort(layer.skyModelIndices.begin(), layer.skyModelIndices.end());
    return layer;
}

std::optional<Mm9SkyDef> selectActiveMm9SkyDef(const Mm9SkyLayer &skyLayer)
{
    const Mm9SkyDef *pBestDefinition = nullptr;

    for (const Mm9SkyDef &definition : skyLayer.definitions)
    {
        if (!definition.valid)
        {
            continue;
        }

        if (pBestDefinition == nullptr
            || definition.index < pBestDefinition->index
            || (definition.index == pBestDefinition->index
                && definition.sourceObjectIndex < pBestDefinition->sourceObjectIndex))
        {
            pBestDefinition = &definition;
        }
    }

    if (pBestDefinition == nullptr)
    {
        return std::nullopt;
    }

    return *pBestDefinition;
}

Mm9DatVec3 computeMm9SkyCameraPositionLt(
    const Mm9SkyCameraMap &cameraMap,
    const Mm9DatVec3 &cameraPositionLt)
{
    return {
        cameraMap.viewMinLt.x
            + ((cameraPositionLt.x - cameraMap.worldMinLt.x)
                * cameraMap.reciprocalWorldSizeLt.x
                * cameraMap.viewSizeLt.x),
        cameraMap.viewMinLt.y
            + ((cameraPositionLt.y - cameraMap.worldMinLt.y)
                * cameraMap.reciprocalWorldSizeLt.y
                * cameraMap.viewSizeLt.y),
        cameraMap.viewMinLt.z
            + ((cameraPositionLt.z - cameraMap.worldMinLt.z)
                * cameraMap.reciprocalWorldSizeLt.z
                * cameraMap.viewSizeLt.z),
    };
}

std::optional<Mm9SkyCameraMap> buildMm9SkyCameraMap(
    const Mm9DatWorldInfo &worldInfo,
    const Mm9SkyDef &skyDef)
{
    const Mm9DatVec3 worldSize = subtract(worldInfo.extentsMaxLt, worldInfo.extentsMinLt);
    if (worldSize.x <= DegenerateExtentEpsilon
        || worldSize.y <= DegenerateExtentEpsilon
        || worldSize.z <= DegenerateExtentEpsilon
        || !skyDef.valid)
    {
        return std::nullopt;
    }

    Mm9SkyCameraMap cameraMap = {};
    cameraMap.worldMinLt = worldInfo.extentsMinLt;
    cameraMap.reciprocalWorldSizeLt = {1.0f / worldSize.x, 1.0f / worldSize.y, 1.0f / worldSize.z};
    cameraMap.viewMinLt = skyDef.viewMinLt;
    cameraMap.viewSizeLt = subtract(skyDef.viewMaxLt, skyDef.viewMinLt);
    return cameraMap;
}

std::optional<Mm9DatVec3> computeMm9SkyCameraPositionLt(
    const Mm9DatWorldInfo &worldInfo,
    const Mm9SkyDef &skyDef,
    const Mm9DatVec3 &cameraPositionLt)
{
    const std::optional<Mm9SkyCameraMap> cameraMap = buildMm9SkyCameraMap(worldInfo, skyDef);
    if (!cameraMap)
    {
        return std::nullopt;
    }

    return computeMm9SkyCameraPositionLt(*cameraMap, cameraPositionLt);
}
}
