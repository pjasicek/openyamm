#pragma once

#include <algorithm>
#include <cstdint>

namespace OpenYAMM::Game
{
struct LightingStats
{
    uint32_t inputLights = 0;
    uint32_t inputStaticLights = 0;
    uint32_t inputDynamicLights = 0;
    uint32_t clusteredFxLights = 0;
    uint32_t outputLights = 0;

    uint32_t visibleSectors = 0;
    uint32_t selectionCalls = 0;
    uint32_t candidateEvaluations = 0;
    uint32_t maxCandidatesPerSelection = 0;
    uint32_t selectedLights = 0;
    uint32_t omittedTailLights = 0;
    uint32_t billboardSamples = 0;

    uint32_t outdoorUniformApplications = 0;
    uint32_t outdoorEmitterInputs = 0;
    uint32_t outdoorEmitterFiltered = 0;
    uint32_t outdoorRankedCandidates = 0;
    uint32_t outdoorSelectedUniformLights = 0;

    uint64_t buildFrameNanoseconds = 0;
    uint64_t clusteringNanoseconds = 0;
    uint64_t selectionNanoseconds = 0;
    uint64_t billboardSampleNanoseconds = 0;
    uint64_t outdoorEmitterScanNanoseconds = 0;
    uint64_t outdoorUniformSelectionNanoseconds = 0;
};

inline void resetLightingStats(LightingStats &stats)
{
    stats = {};
}

inline void addLightingStats(LightingStats &target, const LightingStats &source)
{
    target.inputLights += source.inputLights;
    target.inputStaticLights += source.inputStaticLights;
    target.inputDynamicLights += source.inputDynamicLights;
    target.clusteredFxLights += source.clusteredFxLights;
    target.outputLights += source.outputLights;
    target.visibleSectors += source.visibleSectors;
    target.selectionCalls += source.selectionCalls;
    target.candidateEvaluations += source.candidateEvaluations;
    target.maxCandidatesPerSelection =
        std::max(target.maxCandidatesPerSelection, source.maxCandidatesPerSelection);
    target.selectedLights += source.selectedLights;
    target.omittedTailLights += source.omittedTailLights;
    target.billboardSamples += source.billboardSamples;
    target.outdoorUniformApplications += source.outdoorUniformApplications;
    target.outdoorEmitterInputs += source.outdoorEmitterInputs;
    target.outdoorEmitterFiltered += source.outdoorEmitterFiltered;
    target.outdoorRankedCandidates += source.outdoorRankedCandidates;
    target.outdoorSelectedUniformLights += source.outdoorSelectedUniformLights;
    target.buildFrameNanoseconds += source.buildFrameNanoseconds;
    target.clusteringNanoseconds += source.clusteringNanoseconds;
    target.selectionNanoseconds += source.selectionNanoseconds;
    target.billboardSampleNanoseconds += source.billboardSampleNanoseconds;
    target.outdoorEmitterScanNanoseconds += source.outdoorEmitterScanNanoseconds;
    target.outdoorUniformSelectionNanoseconds += source.outdoorUniformSelectionNanoseconds;
}

inline void recordLightingSelection(
    LightingStats &stats,
    uint32_t candidateCount,
    uint32_t selectedCount,
    uint32_t omittedTailCount)
{
    ++stats.selectionCalls;
    stats.candidateEvaluations += candidateCount;
    stats.maxCandidatesPerSelection = std::max(stats.maxCandidatesPerSelection, candidateCount);
    stats.selectedLights += selectedCount;
    stats.omittedTailLights += omittedTailCount;
}
}
