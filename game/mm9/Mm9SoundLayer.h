#pragma once

#include "game/mm9/Mm9DatWorld.h"

#include <cstddef>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9SoundSourceReference
{
    std::string propertyName;
    std::string sourceFamily;
    std::string sourceValue;
    std::string normalizedKey;
    std::string resolvedSourcePath;
    bool required = false;
    bool resolved = false;
    bool ambiguous = false;
};

struct Mm9SoundSourceObject
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    Mm9DatVec3 positionLt;
    bool hasPosition = false;
    Mm9DatVec3 soundPositionLt;
    bool hasSoundPosition = false;
    float soundRadius = 0.0f;
    bool hasSoundRadius = false;
    std::vector<Mm9SoundSourceReference> references;
};

struct Mm9SoundObject
{
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
    Mm9DatVec3 positionLt;
    bool hasPosition = false;
    Mm9DatVec3 soundPositionLt;
    bool hasSoundPosition = false;
    float soundRadius = 0.0f;
    bool hasSoundRadius = false;
    std::vector<Mm9SoundSourceReference> references;
};

struct Mm9SoundLayer
{
    std::vector<Mm9SoundObject> objects;
    size_t referenceCount = 0;
    size_t resolvedReferenceCount = 0;
    size_t unresolvedRequiredReferenceCount = 0;
    size_t ambiguousReferenceCount = 0;
    size_t soundReferenceCount = 0;
    size_t voiceReferenceCount = 0;
};

Mm9SoundLayer buildMm9SoundLayer(const std::vector<Mm9SoundSourceObject> &sourceObjects);
}
