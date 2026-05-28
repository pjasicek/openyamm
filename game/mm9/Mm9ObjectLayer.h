#pragma once

#include "game/mm9/Mm9DatWorld.h"

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9ObjectSourceObject
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    Mm9DatVec3 positionLt;
    bool hasPosition = false;
    Mm9DatVec3 rotationLt;
    bool hasRotation = false;
    float scale = 1.0f;
    bool hasScale = false;
    Mm9DatVec3 dimsLt;
    bool hasDims = false;
    float radius = 0.0f;
    bool hasRadius = false;
    std::optional<bool> visible;
    std::optional<bool> solid;
    std::optional<bool> trigger;
};

struct Mm9Object
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    Mm9DatVec3 positionLt;
    bool hasPosition = false;
    Mm9DatVec3 rotationLt;
    bool hasRotation = false;
    float scale = 1.0f;
    bool hasScale = false;
    Mm9DatVec3 dimsLt;
    bool hasDims = false;
    float radius = 0.0f;
    bool hasRadius = false;
    std::optional<bool> visible;
    std::optional<bool> solid;
    std::optional<bool> trigger;
    bool hasBoundsEvidence = false;
    bool triggerVolume = false;
};

struct Mm9ObjectLayer
{
    std::vector<Mm9Object> objects;
    size_t positionedObjectCount = 0;
    size_t rotatedObjectCount = 0;
    size_t scaledObjectCount = 0;
    size_t dimensionedObjectCount = 0;
    size_t radiusObjectCount = 0;
    size_t boundsEvidenceObjectCount = 0;
    size_t visibleObjectCount = 0;
    size_t solidObjectCount = 0;
    size_t triggerObjectCount = 0;
    size_t triggerVolumeCount = 0;
};

Mm9ObjectLayer buildMm9ObjectLayer(const std::vector<Mm9ObjectSourceObject> &sourceObjects);
}
