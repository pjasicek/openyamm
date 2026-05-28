#include "game/mm9/Mm9AnimatedActorBinding.h"

#include <string>

namespace OpenYAMM::Game
{
namespace
{
void addBindingDiagnostic(
    std::vector<AnimatedModelDiagnostic> &diagnostics,
    const Mm9ScriptedObject &object,
    const std::string &reason)
{
    diagnostics.push_back(AnimatedModelDiagnostic{
        .message = "MM9 animated actor binding failed"
            + std::string(" map=") + object.mapId
            + " object_id=" + object.objectId
            + " source_object_index=" + std::to_string(object.sourceObjectIndex)
            + " source_class=" + object.sourceClass
            + " source_name=" + object.sourceName
            + ": " + reason,
        .error = true,
    });
}
}

std::string mm9AnimatedActorSemanticStateForScriptedObject(
    const Mm9ScriptedObject &object)
{
    if (object.movement.flying)
    {
        return "flying";
    }
    if (object.movement.running || object.movement.fleeing || object.movement.returning)
    {
        return "running";
    }
    if (object.movement.walking || object.movement.scriptedPath)
    {
        return "walking";
    }
    return "idle";
}

Mm9AnimatedActorVisualSource makeMm9AnimatedActorVisualSource(
    const Mm9ScriptedObject &object,
    size_t maxBoneMatrices)
{
    Mm9AnimatedActorVisualSource source = {};
    source.mapId = object.mapId;
    source.objectId = object.objectId;
    source.sourceObjectIndex = object.sourceObjectIndex;
    source.sourceClass = object.sourceClass;
    source.sourceName = object.sourceName;
    source.sourceModel = object.sourceModel;
    source.sourceSkin = object.sourceSkin;
    if (!object.currentClip.empty() && object.currentClip != "placeholder")
    {
        source.requestedClip = object.currentClip;
    }
    source.semanticState = mm9AnimatedActorSemanticStateForScriptedObject(object);
    source.visible = object.visible;
    source.solid = object.solid;
    source.rayHit = object.rayHit;
    source.pickable = object.pickable;
    source.x = object.x;
    source.y = object.y;
    source.z = object.z;
    source.facingRadians = object.facingRadians;
    source.scale = object.scale;
    source.radius = object.radius;
    source.height = object.height;
    source.verticalOffset = object.verticalOffset;
    source.maxBoneMatrices = maxBoneMatrices;
    return source;
}

std::optional<Mm9AnimatedActorResolvedSource> resolveMm9AnimatedActorVisualSource(
    const Mm9ScriptedObject &object,
    const Mm9AnimatedModelResolver &resolver,
    std::vector<AnimatedModelDiagnostic> &diagnostics,
    size_t maxBoneMatrices)
{
    std::optional<Mm9AnimatedModelResolution> resolution = object.modelAsset.empty()
        ? resolver.resolve(object.sourceModel, object.sourceSkin, diagnostics)
        : resolver.resolveModelAsset(
            object.modelAsset,
            object.modelSkinBinding,
            object.sourceModel,
            object.sourceSkin,
            diagnostics);
    if (!resolution.has_value())
    {
        const std::string sourceDescription = object.modelAsset.empty()
            ? "Filename/Skin model='" + object.sourceModel + "' skin='" + object.sourceSkin + "'"
            : "model_asset='" + object.modelAsset + "' model_skin_binding='" + object.modelSkinBinding
                + "' source_model='" + object.sourceModel + "' source_skin='" + object.sourceSkin + "'";
        addBindingDiagnostic(
            diagnostics,
            object,
            "unresolved " + sourceDescription);
        return std::nullopt;
    }

    return Mm9AnimatedActorResolvedSource{
        .source = makeMm9AnimatedActorVisualSource(object, maxBoneMatrices),
        .resolution = *resolution,
    };
}

bool mm9AnimatedActorCanBePicked(
    const Mm9AnimatedActorVisual &visual)
{
    return visual.visible && visual.pickable && visual.rayHit && !visual.objectId.empty();
}

bool mm9AnimatedActorBlocksMovement(
    const Mm9AnimatedActorVisual &visual)
{
    return visual.solid && visual.radius > 0.0f && visual.height > 0.0f;
}

std::optional<Mm9AnimatedActorPickIdentity> mm9AnimatedActorPickIdentity(
    const Mm9AnimatedActorVisual &visual)
{
    if (!mm9AnimatedActorCanBePicked(visual))
    {
        return std::nullopt;
    }

    return Mm9AnimatedActorPickIdentity{
        .mapId = visual.mapId,
        .objectId = visual.objectId,
        .sourceObjectIndex = visual.sourceObjectIndex,
        .sourceClass = visual.sourceClass,
        .sourceName = visual.sourceName,
    };
}
}
