#pragma once

#include "game/mm9/Mm9AnimatedActorVisual.h"
#include "game/mm9/Mm9ScriptedObjectRuntime.h"

#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9AnimatedActorPickIdentity
{
    std::string mapId;
    std::string objectId;
    size_t sourceObjectIndex = 0;
    std::string sourceClass;
    std::string sourceName;
};

struct Mm9AnimatedActorResolvedSource
{
    Mm9AnimatedActorVisualSource source;
    Mm9AnimatedModelResolution resolution;
};

std::string mm9AnimatedActorSemanticStateForScriptedObject(
    const Mm9ScriptedObject &object);

Mm9AnimatedActorVisualSource makeMm9AnimatedActorVisualSource(
    const Mm9ScriptedObject &object,
    size_t maxBoneMatrices = 128);

std::optional<Mm9AnimatedActorResolvedSource> resolveMm9AnimatedActorVisualSource(
    const Mm9ScriptedObject &object,
    const Mm9AnimatedModelResolver &resolver,
    std::vector<AnimatedModelDiagnostic> &diagnostics,
    size_t maxBoneMatrices = 128);

bool mm9AnimatedActorCanBePicked(
    const Mm9AnimatedActorVisual &visual);

bool mm9AnimatedActorBlocksMovement(
    const Mm9AnimatedActorVisual &visual);

std::optional<Mm9AnimatedActorPickIdentity> mm9AnimatedActorPickIdentity(
    const Mm9AnimatedActorVisual &visual);
}
