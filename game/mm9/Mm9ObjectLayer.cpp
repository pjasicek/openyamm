#include "game/mm9/Mm9ObjectLayer.h"

#include <utility>

namespace OpenYAMM::Game
{
Mm9ObjectLayer buildMm9ObjectLayer(const std::vector<Mm9ObjectSourceObject> &sourceObjects)
{
    Mm9ObjectLayer layer = {};
    layer.objects.reserve(sourceObjects.size());

    for (const Mm9ObjectSourceObject &sourceObject : sourceObjects)
    {
        Mm9Object object = {};
        object.sourceObjectIndex = sourceObject.sourceObjectIndex;
        object.sourceClass = sourceObject.sourceClass;
        object.sourceName = sourceObject.sourceName;
        object.positionLt = sourceObject.positionLt;
        object.hasPosition = sourceObject.hasPosition;
        object.rotationLt = sourceObject.rotationLt;
        object.hasRotation = sourceObject.hasRotation;
        object.scale = sourceObject.scale;
        object.hasScale = sourceObject.hasScale;
        object.dimsLt = sourceObject.dimsLt;
        object.hasDims = sourceObject.hasDims;
        object.radius = sourceObject.radius;
        object.hasRadius = sourceObject.hasRadius;
        object.visible = sourceObject.visible;
        object.solid = sourceObject.solid;
        object.trigger = sourceObject.trigger;
        object.hasBoundsEvidence = object.hasDims || object.hasRadius || object.hasScale;
        object.triggerVolume =
            object.sourceClass == "Trigger"
            || (object.trigger && *object.trigger)
            || (object.hasDims && object.sourceClass.find("Trigger") != std::string::npos);

        if (object.hasPosition)
        {
            ++layer.positionedObjectCount;
        }

        if (object.hasRotation)
        {
            ++layer.rotatedObjectCount;
        }

        if (object.hasScale)
        {
            ++layer.scaledObjectCount;
        }

        if (object.hasDims)
        {
            ++layer.dimensionedObjectCount;
        }

        if (object.hasRadius)
        {
            ++layer.radiusObjectCount;
        }

        if (object.hasBoundsEvidence)
        {
            ++layer.boundsEvidenceObjectCount;
        }

        if (object.visible && *object.visible)
        {
            ++layer.visibleObjectCount;
        }

        if (object.solid && *object.solid)
        {
            ++layer.solidObjectCount;
        }

        if (object.trigger && *object.trigger)
        {
            ++layer.triggerObjectCount;
        }

        if (object.triggerVolume)
        {
            ++layer.triggerVolumeCount;
        }

        layer.objects.push_back(std::move(object));
    }

    return layer;
}
}
