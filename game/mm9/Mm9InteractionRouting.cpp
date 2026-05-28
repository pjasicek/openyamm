#include "game/mm9/Mm9InteractionRouting.h"

#include <utility>

namespace OpenYAMM::Game
{
GameplayWorldHit buildMm9ScriptedObjectWorldHit(const Mm9InteractionObjectBinding &binding)
{
    GameplayEventTargetContextActionMetadata metadata = {};
    metadata.kind = "mm9_scripted_object";
    metadata.source = binding.objectId;
    metadata.targetMap = binding.mapId;
    metadata.targetName = binding.sourceName.empty() ? binding.visualId : binding.sourceName;
    if (!binding.objectId.empty())
    {
        metadata.mm9ObjectId = binding.objectId;
    }
    if (binding.sourceObjectIndex >= 0)
    {
        metadata.mm9SourceObjectIndex = binding.sourceObjectIndex;
    }
    if (!binding.sourceClass.empty())
    {
        metadata.mm9SourceClass = binding.sourceClass;
    }
    if (!binding.sourceName.empty())
    {
        metadata.mm9SourceName = binding.sourceName;
    }
    if (!binding.visualId.empty())
    {
        metadata.mm9VisualId = binding.visualId;
    }
    if (!binding.scriptName.empty())
    {
        metadata.mm9ScriptName = binding.scriptName;
    }
    if (!binding.scriptParams.empty())
    {
        metadata.mm9ScriptParams = binding.scriptParams;
    }

    GameplayEventTargetHit eventTargetHit = {};
    eventTargetHit.targetKind = GameplayWorldEventTargetKind::Object;
    eventTargetHit.targetIndex = binding.routerTargetIndex;
    eventTargetHit.name = binding.sourceName.empty() ? binding.visualId : binding.sourceName;
    eventTargetHit.hitPoint = binding.hitPoint;
    eventTargetHit.distance = binding.distance;
    eventTargetHit.contextActionMetadata = std::move(metadata);

    GameplayWorldHit hit = {};
    hit.hasHit = true;
    hit.kind = GameplayWorldHitKind::EventTarget;
    hit.eventTarget = std::move(eventTargetHit);
    return hit;
}

std::optional<Mm9InteractionObjectBinding> mm9InteractionObjectBindingFromWorldHit(const GameplayWorldHit &hit)
{
    if (!hit.hasHit
        || hit.kind != GameplayWorldHitKind::EventTarget
        || !hit.eventTarget
        || hit.eventTarget->targetKind != GameplayWorldEventTargetKind::Object
        || !hit.eventTarget->contextActionMetadata
        || hit.eventTarget->contextActionMetadata->kind != "mm9_scripted_object")
    {
        return std::nullopt;
    }

    const GameplayEventTargetHit &eventTargetHit = *hit.eventTarget;
    const GameplayEventTargetContextActionMetadata &metadata = *eventTargetHit.contextActionMetadata;
    if (!metadata.targetMap || !metadata.mm9SourceObjectIndex)
    {
        return std::nullopt;
    }

    Mm9InteractionObjectBinding binding = {};
    binding.mapId = *metadata.targetMap;
    binding.objectId = metadata.mm9ObjectId.value_or(metadata.source);
    binding.sourceObjectIndex = *metadata.mm9SourceObjectIndex;
    binding.sourceClass = metadata.mm9SourceClass.value_or("");
    binding.sourceName = metadata.mm9SourceName.value_or(metadata.targetName.value_or(eventTargetHit.name));
    binding.visualId = metadata.mm9VisualId.value_or("");
    binding.scriptName = metadata.mm9ScriptName.value_or("");
    binding.scriptParams = metadata.mm9ScriptParams.value_or("");
    binding.routerTargetIndex = eventTargetHit.targetIndex;
    binding.hitPoint = eventTargetHit.hitPoint;
    binding.distance = eventTargetHit.distance;
    return binding;
}
}
