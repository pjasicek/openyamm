#include "game/mm9/Mm9SpawnLayer.h"

#include <utility>

namespace OpenYAMM::Game
{
Mm9SpawnLayer buildMm9SpawnLayer(const std::vector<Mm9SpawnSourceObject> &sourceObjects)
{
    Mm9SpawnLayer layer = {};
    layer.objects.reserve(sourceObjects.size());

    for (const Mm9SpawnSourceObject &sourceObject : sourceObjects)
    {
        if (!sourceObject.spawnLevel
            && !sourceObject.spawnObject
            && !sourceObject.hasSpawnObjectVelocity
            && !sourceObject.npcProps
            && !sourceObject.npcNumber)
        {
            continue;
        }

        Mm9SpawnObject object = {};
        object.sourceObjectIndex = sourceObject.sourceObjectIndex;
        object.sourceClass = sourceObject.sourceClass;
        object.sourceName = sourceObject.sourceName;
        object.positionLt = sourceObject.positionLt;
        object.hasPosition = sourceObject.hasPosition;
        object.rotationLt = sourceObject.rotationLt;
        object.hasRotation = sourceObject.hasRotation;
        object.spawnLevel = sourceObject.spawnLevel;
        object.spawnObject = sourceObject.spawnObject;
        object.spawnObjectVelocityLt = sourceObject.spawnObjectVelocityLt;
        object.hasSpawnObjectVelocity = sourceObject.hasSpawnObjectVelocity;
        object.npcProps = sourceObject.npcProps;
        object.npcNumber = sourceObject.npcNumber;

        if (object.spawnLevel)
        {
            ++layer.spawnLevelCount;
        }

        if (object.spawnObject)
        {
            ++layer.spawnObjectCount;
        }

        if (object.hasSpawnObjectVelocity)
        {
            ++layer.spawnObjectVelocityCount;
        }

        if (object.npcProps)
        {
            ++layer.npcPropertyCount;
        }

        if (object.npcNumber)
        {
            ++layer.npcNumberCount;
        }

        layer.objects.push_back(std::move(object));
    }

    return layer;
}
}
