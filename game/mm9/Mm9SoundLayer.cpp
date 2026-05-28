#include "game/mm9/Mm9SoundLayer.h"

#include <utility>

namespace OpenYAMM::Game
{
Mm9SoundLayer buildMm9SoundLayer(const std::vector<Mm9SoundSourceObject> &sourceObjects)
{
    Mm9SoundLayer layer = {};
    layer.objects.reserve(sourceObjects.size());

    for (const Mm9SoundSourceObject &sourceObject : sourceObjects)
    {
        if (sourceObject.references.empty())
        {
            continue;
        }

        Mm9SoundObject object = {};
        object.sourceObjectIndex = sourceObject.sourceObjectIndex;
        object.sourceClass = sourceObject.sourceClass;
        object.sourceName = sourceObject.sourceName;
        object.positionLt = sourceObject.positionLt;
        object.hasPosition = sourceObject.hasPosition;
        object.soundPositionLt = sourceObject.soundPositionLt;
        object.hasSoundPosition = sourceObject.hasSoundPosition;
        object.soundRadius = sourceObject.soundRadius;
        object.hasSoundRadius = sourceObject.hasSoundRadius;
        object.references = sourceObject.references;

        for (const Mm9SoundSourceReference &reference : object.references)
        {
            ++layer.referenceCount;

            if (reference.resolved)
            {
                ++layer.resolvedReferenceCount;
            }

            if (reference.ambiguous)
            {
                ++layer.ambiguousReferenceCount;
            }

            if (reference.required && !reference.resolved)
            {
                ++layer.unresolvedRequiredReferenceCount;
            }

            if (reference.sourceFamily == "voices")
            {
                ++layer.voiceReferenceCount;
            }
            else
            {
                ++layer.soundReferenceCount;
            }
        }

        layer.objects.push_back(std::move(object));
    }

    return layer;
}
}
