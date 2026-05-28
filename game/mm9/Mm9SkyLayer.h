#pragma once

#include "game/mm9/Mm9DatWorld.h"

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
enum class Mm9SkySourcePropertyKind
{
    String,
    Integer,
    Number,
    Vec3,
};

struct Mm9SkySourceProperty
{
    std::string name;
    Mm9SkySourcePropertyKind kind = Mm9SkySourcePropertyKind::String;
    std::string stringValue;
    int integerValue = 0;
    float numberValue = 0.0f;
    Mm9DatVec3 vec3Value;
};

struct Mm9SkySourceObject
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    std::vector<Mm9SkySourceProperty> properties;
};

struct Mm9SkyDef
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    Mm9DatVec3 positionLt;
    Mm9DatVec3 skyDimsLt;
    Mm9DatVec3 innerPercentLt;
    Mm9DatVec3 minLt;
    Mm9DatVec3 maxLt;
    Mm9DatVec3 viewMinLt;
    Mm9DatVec3 viewMaxLt;
    int flags = 0;
    int index = 0;
    bool valid = false;
};

struct Mm9SkyObject
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    std::string skyObjectName;
    size_t sourceModelIndex = 0;
    int flags = 0;
    int index = 0;
    bool hasSourceModel = false;
};

struct Mm9SkyLayerDiagnostic
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    std::string propertyName;
    std::string message;
};

struct Mm9SkyLayer
{
    std::vector<Mm9SkyDef> definitions;
    std::vector<Mm9SkyObject> objects;
    std::vector<size_t> skyModelIndices;
    std::vector<Mm9SkyLayerDiagnostic> diagnostics;
};

struct Mm9SkyCameraMap
{
    Mm9DatVec3 worldMinLt;
    Mm9DatVec3 reciprocalWorldSizeLt;
    Mm9DatVec3 viewMinLt;
    Mm9DatVec3 viewSizeLt;
};

Mm9SkySourceProperty mm9SkyStringProperty(const std::string &name, const std::string &value);
Mm9SkySourceProperty mm9SkyIntegerProperty(const std::string &name, int value);
Mm9SkySourceProperty mm9SkyNumberProperty(const std::string &name, float value);
Mm9SkySourceProperty mm9SkyVec3Property(const std::string &name, const Mm9DatVec3 &value);

Mm9SkyDef makeMm9SkyDef(
    size_t sourceObjectIndex,
    const std::string &sourceClass,
    const std::string &sourceName,
    const Mm9DatVec3 &positionLt,
    const Mm9DatVec3 &skyDimsLt,
    const Mm9DatVec3 &innerPercentLt,
    int flags,
    int index);

Mm9SkyLayer buildMm9SkyLayer(
    const Mm9DatWorld &world,
    const std::vector<Mm9SkySourceObject> &sourceObjects,
    const std::vector<Mm9DatModelRenderRole> &modelRoles = {});

std::optional<Mm9SkyDef> selectActiveMm9SkyDef(const Mm9SkyLayer &skyLayer);

std::optional<Mm9SkyCameraMap> buildMm9SkyCameraMap(
    const Mm9DatWorldInfo &worldInfo,
    const Mm9SkyDef &skyDef);

Mm9DatVec3 computeMm9SkyCameraPositionLt(
    const Mm9SkyCameraMap &cameraMap,
    const Mm9DatVec3 &cameraPositionLt);

std::optional<Mm9DatVec3> computeMm9SkyCameraPositionLt(
    const Mm9DatWorldInfo &worldInfo,
    const Mm9SkyDef &skyDef,
    const Mm9DatVec3 &cameraPositionLt);
}
