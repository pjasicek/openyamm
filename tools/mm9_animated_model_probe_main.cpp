#include "game/mm9/Mm9AnimatedModelResolver.h"
#include "game/mm9/Mm9AnimatedModelSidecar.h"
#include "game/render/AnimatedModelAsset.h"

#include <filesystem>
#include <iostream>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace
{
struct ProbeOptions
{
    std::filesystem::path modelPath;
    std::filesystem::path sidecarPath;
    std::filesystem::path registryPath;
    std::string sourceModel;
    std::string sourceSkin;
    std::string modelAsset;
    std::string modelSkinBinding;
    std::string clipName;
    std::string socketName;
    uint32_t timeMs = 0;
    bool loop = true;
    size_t maxBones = 128;
    bool dumpClips = false;
    bool dumpSockets = false;
    bool dumpMaterialOverrides = false;
    bool json = false;
};

void printUsage()
{
    std::cerr
        << "Usage:\n"
        << "  mm9_animated_model_probe --model <file.glb> --sidecar <file.model.yml> [--clip <name>]\n"
        << "  mm9_animated_model_probe --registry <model_registry.yml> --filename <Filename> [--skin <Skin>]\n"
        << "                            [--clip <name>] [--time-ms <ms>] [--socket <name>]\n"
        << "                            [--max-bones <count>] [--dump-clips]\n"
        << "                            [--dump-sockets] [--dump-material-overrides] [--json]\n";
    std::cerr
        << "  mm9_animated_model_probe --registry <model_registry.yml> --model-asset <models/name.glb>\n"
        << "                            [--model-skin-binding <id>] [--filename <source Filename>]\n"
        << "                            [--skin <source Skin>] [--clip <name>] [--json]\n";
}

bool readNextValue(int argc, char **argv, int &index, std::string &value)
{
    if (index + 1 >= argc)
    {
        return false;
    }

    ++index;
    value = argv[index];
    return true;
}

bool parseOptions(int argc, char **argv, ProbeOptions &options)
{
    for (int index = 1; index < argc; ++index)
    {
        const std::string argument = argv[index];
        std::string value;
        if (argument == "--model" && readNextValue(argc, argv, index, value))
        {
            options.modelPath = value;
        }
        else if (argument == "--sidecar" && readNextValue(argc, argv, index, value))
        {
            options.sidecarPath = value;
        }
        else if (argument == "--registry" && readNextValue(argc, argv, index, value))
        {
            options.registryPath = value;
        }
        else if (argument == "--filename" && readNextValue(argc, argv, index, value))
        {
            options.sourceModel = value;
        }
        else if (argument == "--skin" && readNextValue(argc, argv, index, value))
        {
            options.sourceSkin = value;
        }
        else if (argument == "--model-asset" && readNextValue(argc, argv, index, value))
        {
            options.modelAsset = value;
        }
        else if (argument == "--model-skin-binding" && readNextValue(argc, argv, index, value))
        {
            options.modelSkinBinding = value;
        }
        else if (argument == "--clip" && readNextValue(argc, argv, index, value))
        {
            options.clipName = value;
        }
        else if (argument == "--time-ms" && readNextValue(argc, argv, index, value))
        {
            options.timeMs = static_cast<uint32_t>(std::stoul(value));
        }
        else if (argument == "--socket" && readNextValue(argc, argv, index, value))
        {
            options.socketName = value;
        }
        else if (argument == "--max-bones" && readNextValue(argc, argv, index, value))
        {
            options.maxBones = static_cast<size_t>(std::stoull(value));
        }
        else if (argument == "--no-loop")
        {
            options.loop = false;
        }
        else if (argument == "--dump-clips")
        {
            options.dumpClips = true;
        }
        else if (argument == "--dump-sockets")
        {
            options.dumpSockets = true;
        }
        else if (argument == "--dump-material-overrides")
        {
            options.dumpMaterialOverrides = true;
        }
        else if (argument == "--json")
        {
            options.json = true;
        }
        else if (argument == "--help" || argument == "-h")
        {
            printUsage();
            return false;
        }
        else
        {
            std::cerr << "Unknown or incomplete option: " << argument << "\n";
            printUsage();
            return false;
        }
    }

    if (!options.registryPath.empty() || !options.sourceModel.empty() || !options.modelAsset.empty())
    {
        return !options.registryPath.empty() && (!options.sourceModel.empty() || !options.modelAsset.empty());
    }

    return !options.modelPath.empty() && !options.sidecarPath.empty();
}

void applyMaterialOverrides(
    const std::vector<OpenYAMM::Game::Mm9AnimatedModelMaterialOverride> &overrides,
    OpenYAMM::Game::AnimatedModelAsset &asset)
{
    for (const OpenYAMM::Game::Mm9AnimatedModelMaterialOverride &materialOverride : overrides)
    {
        if (materialOverride.materialIndex >= asset.materials.size())
        {
            asset.diagnostics.push_back(OpenYAMM::Game::AnimatedModelDiagnostic{
                .message = "resolved material override index is outside loaded material range",
                .error = true,
            });
            continue;
        }

        asset.materials[materialOverride.materialIndex].baseColorTextureUri = materialOverride.runtimeTexture;
    }
}

bool printDiagnostics(const std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> &diagnostics)
{
    bool hasErrors = false;
    for (const OpenYAMM::Game::AnimatedModelDiagnostic &diagnostic : diagnostics)
    {
        std::cout << (diagnostic.error ? "error: " : "warning: ") << diagnostic.message << "\n";
        hasErrors = hasErrors || diagnostic.error;
    }
    return hasErrors;
}

bool diagnosticsHaveErrors(const std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> &diagnostics)
{
    bool hasErrors = false;
    for (const OpenYAMM::Game::AnimatedModelDiagnostic &diagnostic : diagnostics)
    {
        hasErrors = hasErrors || diagnostic.error;
    }
    return hasErrors;
}

size_t firstSkinJointCount(const OpenYAMM::Game::AnimatedModelAsset &asset)
{
    if (asset.skins.empty())
    {
        return 0;
    }
    return asset.skins.front().joints.size();
}

size_t totalVertexCount(const OpenYAMM::Game::AnimatedModelAsset &asset)
{
    size_t count = 0;
    for (const OpenYAMM::Game::AnimatedModelPrimitive &primitive : asset.primitives)
    {
        count += primitive.vertices.size();
    }
    return count;
}

size_t totalIndexCount(const OpenYAMM::Game::AnimatedModelAsset &asset)
{
    size_t count = 0;
    for (const OpenYAMM::Game::AnimatedModelPrimitive &primitive : asset.primitives)
    {
        count += primitive.indices.size();
    }
    return count;
}

void printBounds(
    const char *pLabel,
    const OpenYAMM::Game::AnimatedModelBounds &bounds)
{
    if (!bounds.valid)
    {
        std::cout << pLabel << ": invalid\n";
        return;
    }

    std::cout << pLabel << ".min: "
        << bounds.min.x << " " << bounds.min.y << " " << bounds.min.z << "\n";
    std::cout << pLabel << ".max: "
        << bounds.max.x << " " << bounds.max.y << " " << bounds.max.z << "\n";
}

void printLod(const OpenYAMM::Game::AnimatedModelLodInfo &lod)
{
    if (!lod.valid)
    {
        std::cout << "lod: invalid\n";
        return;
    }

    std::cout << "lod.exported_index: " << lod.exportedIndex << "\n";
    std::cout << "lod.distance_count: " << lod.distances.size() << "\n";
    for (size_t index = 0; index < lod.distances.size(); ++index)
    {
        std::cout << "lod.distance[" << index << "]: " << lod.distances[index] << "\n";
    }
}

void printClips(const OpenYAMM::Game::AnimatedModelAsset &asset)
{
    std::cout << "clip_dump.count: " << asset.clips.size() << "\n";
    for (size_t clipIndex = 0; clipIndex < asset.clips.size(); ++clipIndex)
    {
        const OpenYAMM::Game::AnimatedModelClip &clip = asset.clips[clipIndex];
        std::cout << "clip[" << clipIndex << "].name: " << clip.name << "\n";
        std::cout << "clip[" << clipIndex << "].duration_seconds: " << clip.durationSeconds << "\n";
        std::cout << "clip[" << clipIndex << "].channel_count: " << clip.channels.size() << "\n";
        std::cout << "clip[" << clipIndex << "].event_count: " << clip.events.size() << "\n";
        for (size_t eventIndex = 0; eventIndex < clip.events.size(); ++eventIndex)
        {
            const OpenYAMM::Game::AnimatedModelEvent &event = clip.events[eventIndex];
            std::cout << "clip[" << clipIndex << "].event[" << eventIndex << "].time_seconds: "
                      << event.timeSeconds << "\n";
            std::cout << "clip[" << clipIndex << "].event[" << eventIndex << "].key: "
                      << event.key << "\n";
        }
    }
}

void printSockets(const OpenYAMM::Game::AnimatedModelAsset &asset)
{
    std::cout << "socket_dump.count: " << asset.sockets.size() << "\n";
    for (size_t socketIndex = 0; socketIndex < asset.sockets.size(); ++socketIndex)
    {
        const OpenYAMM::Game::AnimatedModelSocket &socket = asset.sockets[socketIndex];
        std::cout << "socket[" << socketIndex << "].name: " << socket.name << "\n";
        std::cout << "socket[" << socketIndex << "].node: " << socket.nodeIndex << "\n";
        std::cout << "socket[" << socketIndex << "].translation: "
                  << socket.localTransform.translation.x << " "
                  << socket.localTransform.translation.y << " "
                  << socket.localTransform.translation.z << "\n";
        std::cout << "socket[" << socketIndex << "].rotation: "
                  << socket.localTransform.rotation.x << " "
                  << socket.localTransform.rotation.y << " "
                  << socket.localTransform.rotation.z << " "
                  << socket.localTransform.rotation.w << "\n";
    }
}

void printMaterialOverrides(
    const OpenYAMM::Game::Mm9AnimatedModelSidecar &sidecar,
    const std::optional<OpenYAMM::Game::Mm9AnimatedModelResolution> &resolution)
{
    if (resolution.has_value())
    {
        std::cout << "resolved_skin_binding: " << resolution->skinBindingId << "\n";
        std::cout << "resolved_skin_count: " << resolution->normalizedSourceSkins.size() << "\n";
        for (size_t skinIndex = 0; skinIndex < resolution->normalizedSourceSkins.size(); ++skinIndex)
        {
            std::cout << "resolved_skin[" << skinIndex << "]: "
                      << resolution->normalizedSourceSkins[skinIndex] << "\n";
        }

        std::cout << "resolved_material_override_count: " << resolution->materialOverrides.size() << "\n";
        for (size_t overrideIndex = 0; overrideIndex < resolution->materialOverrides.size(); ++overrideIndex)
        {
            const OpenYAMM::Game::Mm9AnimatedModelMaterialOverride &materialOverride =
                resolution->materialOverrides[overrideIndex];
            std::cout << "resolved_material_override[" << overrideIndex << "].material: "
                      << materialOverride.materialIndex << "\n";
            std::cout << "resolved_material_override[" << overrideIndex << "].runtime_texture: "
                      << materialOverride.runtimeTexture << "\n";
        }
    }

    std::cout << "sidecar_material_ref_count: " << sidecar.materials.size() << "\n";
    for (size_t materialIndex = 0; materialIndex < sidecar.materials.size(); ++materialIndex)
    {
        const OpenYAMM::Game::Mm9AnimatedModelMaterialRef &material = sidecar.materials[materialIndex];
        std::cout << "sidecar_material_ref[" << materialIndex << "].material: " << material.index << "\n";
        std::cout << "sidecar_material_ref[" << materialIndex << "].runtime_texture: "
                  << material.runtimeTexture << "\n";
        std::cout << "sidecar_material_ref[" << materialIndex << "].preview_texture: "
                  << material.previewTexture << "\n";
    }
}

void writeJsonString(std::ostream &output, std::string_view value)
{
    output << '"';
    for (const char character : value)
    {
        switch (character)
        {
        case '"':
            output << "\\\"";
            break;
        case '\\':
            output << "\\\\";
            break;
        case '\b':
            output << "\\b";
            break;
        case '\f':
            output << "\\f";
            break;
        case '\n':
            output << "\\n";
            break;
        case '\r':
            output << "\\r";
            break;
        case '\t':
            output << "\\t";
            break;
        default:
            if (static_cast<unsigned char>(character) < 0x20)
            {
                constexpr char HexDigits[] = "0123456789abcdef";
                output << "\\u00"
                       << HexDigits[(static_cast<unsigned char>(character) >> 4) & 0x0f]
                       << HexDigits[static_cast<unsigned char>(character) & 0x0f];
            }
            else
            {
                output << character;
            }
            break;
        }
    }
    output << '"';
}

void writeJsonBounds(
    std::ostream &output,
    const OpenYAMM::Game::AnimatedModelBounds &bounds)
{
    output << "{\"valid\":" << (bounds.valid ? "true" : "false");
    if (bounds.valid)
    {
        output << ",\"min\":[" << bounds.min.x << ',' << bounds.min.y << ',' << bounds.min.z << ']';
        output << ",\"max\":[" << bounds.max.x << ',' << bounds.max.y << ',' << bounds.max.z << ']';
    }
    output << '}';
}

void writeJsonDiagnostics(
    std::ostream &output,
    const std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> &diagnostics)
{
    output << '[';
    for (size_t index = 0; index < diagnostics.size(); ++index)
    {
        if (index != 0)
        {
            output << ',';
        }
        output << "{\"error\":" << (diagnostics[index].error ? "true" : "false") << ",\"message\":";
        writeJsonString(output, diagnostics[index].message);
        output << '}';
    }
    output << ']';
}

void writeJsonStringArray(std::ostream &output, const std::vector<std::string> &values)
{
    output << '[';
    for (size_t index = 0; index < values.size(); ++index)
    {
        if (index != 0)
        {
            output << ',';
        }
        writeJsonString(output, values[index]);
    }
    output << ']';
}

void writeJsonProbeReport(
    const ProbeOptions &options,
    const OpenYAMM::Game::AnimatedModelAsset &asset,
    const OpenYAMM::Game::Mm9AnimatedModelSidecar &sidecar,
    const std::optional<OpenYAMM::Game::Mm9AnimatedModelResolution> &resolution,
    const std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> &resolverDiagnostics,
    const OpenYAMM::Game::AnimatedModelClip *pClip,
    const OpenYAMM::Game::AnimatedModelPose *pPose,
    const OpenYAMM::Game::AnimatedModelRenderPrep *pRenderPrep,
    const OpenYAMM::Game::AnimatedModelMat4 *pSocketTransform,
    bool hasErrors)
{
    std::cout << "{";
    std::cout << "\"ok\":" << (hasErrors ? "false" : "true");
    std::cout << ",\"model_path\":";
    writeJsonString(std::cout, options.modelPath.generic_string());
    std::cout << ",\"sidecar_path\":";
    writeJsonString(std::cout, options.sidecarPath.generic_string());
    std::cout << ",\"model_id\":";
    writeJsonString(std::cout, resolution.has_value() ? resolution->modelId : sidecar.id);

    if (resolution.has_value())
    {
        std::cout << ",\"source_model\":";
        writeJsonString(std::cout, resolution->normalizedSourceModel);
        std::cout << ",\"skin_binding\":";
        writeJsonString(std::cout, resolution->skinBindingId);
        std::cout << ",\"source_skins\":";
        writeJsonStringArray(std::cout, resolution->normalizedSourceSkins);
        std::cout << ",\"material_overrides\":[";
        for (size_t index = 0; index < resolution->materialOverrides.size(); ++index)
        {
            if (index != 0)
            {
                std::cout << ',';
            }
            const OpenYAMM::Game::Mm9AnimatedModelMaterialOverride &materialOverride =
                resolution->materialOverrides[index];
            std::cout << "{\"material\":" << materialOverride.materialIndex << ",\"runtime_texture\":";
            writeJsonString(std::cout, materialOverride.runtimeTexture);
            std::cout << '}';
        }
        std::cout << ']';
    }

    std::cout << ",\"primitive_count\":" << asset.primitives.size();
    std::cout << ",\"vertex_count\":" << totalVertexCount(asset);
    std::cout << ",\"index_count\":" << totalIndexCount(asset);
    std::cout << ",\"bounds\":";
    writeJsonBounds(std::cout, asset.bounds);
    std::cout << ",\"lod\":{\"valid\":" << (asset.lod.valid ? "true" : "false")
              << ",\"exported_index\":" << asset.lod.exportedIndex
              << ",\"distances\":[";
    for (size_t index = 0; index < asset.lod.distances.size(); ++index)
    {
        if (index != 0)
        {
            std::cout << ',';
        }
        std::cout << asset.lod.distances[index];
    }
    std::cout << "]}";

    std::cout << ",\"materials\":[";
    for (size_t index = 0; index < asset.materials.size(); ++index)
    {
        if (index != 0)
        {
            std::cout << ',';
        }
        std::cout << "{\"texture\":";
        writeJsonString(std::cout, asset.materials[index].baseColorTextureUri);
        std::cout << '}';
    }
    std::cout << ']';

    std::cout << ",\"node_count\":" << asset.nodes.size();
    std::cout << ",\"skin_count\":" << asset.skins.size();
    std::cout << ",\"first_skin_joint_count\":" << firstSkinJointCount(asset);
    std::cout << ",\"animation_count\":" << asset.clips.size();
    std::cout << ",\"socket_count\":" << asset.sockets.size();

    if (options.dumpClips)
    {
        std::cout << ",\"clips\":[";
        for (size_t clipIndex = 0; clipIndex < asset.clips.size(); ++clipIndex)
        {
            if (clipIndex != 0)
            {
                std::cout << ',';
            }
            const OpenYAMM::Game::AnimatedModelClip &clip = asset.clips[clipIndex];
            std::cout << "{\"name\":";
            writeJsonString(std::cout, clip.name);
            std::cout << ",\"duration_seconds\":" << clip.durationSeconds
                      << ",\"channel_count\":" << clip.channels.size()
                      << ",\"event_count\":" << clip.events.size() << '}';
        }
        std::cout << ']';
    }

    if (options.dumpSockets)
    {
        std::cout << ",\"sockets\":[";
        for (size_t socketIndex = 0; socketIndex < asset.sockets.size(); ++socketIndex)
        {
            if (socketIndex != 0)
            {
                std::cout << ',';
            }
            const OpenYAMM::Game::AnimatedModelSocket &socket = asset.sockets[socketIndex];
            std::cout << "{\"name\":";
            writeJsonString(std::cout, socket.name);
            std::cout << ",\"node\":" << socket.nodeIndex << '}';
        }
        std::cout << ']';
    }

    if (pClip != nullptr && pPose != nullptr && pRenderPrep != nullptr)
    {
        std::cout << ",\"sample\":{\"clip\":";
        writeJsonString(std::cout, pClip->name);
        std::cout << ",\"duration_seconds\":" << pClip->durationSeconds
                  << ",\"time_ms\":" << options.timeMs
                  << ",\"loop\":" << (options.loop ? "true" : "false")
                  << ",\"global_transform_count\":" << pPose->globalTransforms.size()
                  << ",\"skinning_matrix_count\":" << pPose->skinningMatrices.size()
                  << ",\"render_prep\":{\"max_bones\":" << options.maxBones
                  << ",\"draw_items\":" << pRenderPrep->drawItems.size()
                  << ",\"skinned_draw_calls\":" << pRenderPrep->counters.skinnedDrawCalls
                  << ",\"skinned_triangles\":" << pRenderPrep->counters.skinnedTriangles
                  << ",\"uploaded_bone_matrices\":" << pRenderPrep->counters.uploadedBoneMatrices
                  << "}}";
    }

    if (pSocketTransform != nullptr)
    {
        std::cout << ",\"socket_transform\":[";
        for (size_t index = 0; index < pSocketTransform->values.size(); ++index)
        {
            if (index != 0)
            {
                std::cout << ',';
            }
            std::cout << pSocketTransform->values[index];
        }
        std::cout << ']';
    }

    std::cout << ",\"resolver_diagnostics\":";
    writeJsonDiagnostics(std::cout, resolverDiagnostics);
    std::cout << ",\"asset_diagnostics\":";
    writeJsonDiagnostics(std::cout, asset.diagnostics);
    std::cout << ",\"render_prep_diagnostics\":";
    if (pRenderPrep != nullptr)
    {
        writeJsonDiagnostics(std::cout, pRenderPrep->diagnostics);
    }
    else
    {
        std::cout << "[]";
    }
    std::cout << "}\n";
}
}

int main(int argc, char **argv)
{
    ProbeOptions options = {};
    if (!parseOptions(argc, argv, options))
    {
        return 2;
    }

    std::optional<OpenYAMM::Game::Mm9AnimatedModelResolution> resolution;
    std::vector<OpenYAMM::Game::AnimatedModelDiagnostic> resolverDiagnostics;
    if (!options.registryPath.empty())
    {
        OpenYAMM::Game::Mm9AnimatedModelResolver resolver = {};
        std::string errorMessage;
        if (!resolver.loadRegistry(options.registryPath, errorMessage))
        {
            std::cerr << errorMessage << "\n";
            return 1;
        }

        if (!options.modelAsset.empty())
        {
            resolution = resolver.resolveModelAsset(
                options.modelAsset,
                options.modelSkinBinding,
                options.sourceModel,
                options.sourceSkin,
                resolverDiagnostics);
        }
        else
        {
            resolution = resolver.resolve(options.sourceModel, options.sourceSkin, resolverDiagnostics);
        }
        if (!resolution.has_value())
        {
            printDiagnostics(resolverDiagnostics);
            return 1;
        }

        options.modelPath = resolution->modelAssetPath;
        options.sidecarPath = resolution->modelSidecarPath;
    }

    std::string errorMessage;
    std::optional<OpenYAMM::Game::AnimatedModelAsset> asset =
        OpenYAMM::Game::loadAnimatedModelAsset(options.modelPath, errorMessage);
    if (!asset.has_value())
    {
        std::cerr << errorMessage << "\n";
        return 1;
    }

    std::optional<OpenYAMM::Game::Mm9AnimatedModelSidecar> sidecar =
        OpenYAMM::Game::loadMm9AnimatedModelSidecar(options.sidecarPath, errorMessage);
    if (!sidecar.has_value())
    {
        std::cerr << errorMessage << "\n";
        return 1;
    }

    OpenYAMM::Game::mergeMm9AnimatedModelSidecar(*sidecar, *asset);
    if (resolution.has_value())
    {
        applyMaterialOverrides(resolution->materialOverrides, *asset);
    }

    bool hasErrors = diagnosticsHaveErrors(resolverDiagnostics);
    hasErrors = diagnosticsHaveErrors(asset->diagnostics) || hasErrors;

    const OpenYAMM::Game::AnimatedModelClip *pSelectedClip = nullptr;
    std::optional<OpenYAMM::Game::AnimatedModelPose> sampledPose;
    std::optional<OpenYAMM::Game::AnimatedModelRenderPrep> renderPrep;
    std::optional<OpenYAMM::Game::AnimatedModelMat4> socketTransform;

    if (!options.clipName.empty())
    {
        pSelectedClip = asset->findClip(options.clipName);
        if (pSelectedClip == nullptr)
        {
            std::cerr << "clip not found: " << options.clipName << "\n";
            return 1;
        }

        const float sampleTimeSeconds = static_cast<float>(options.timeMs) / 1000.0f;
        sampledPose = OpenYAMM::Game::sampleAnimatedModelPose(
            *asset,
            pSelectedClip,
            sampleTimeSeconds,
            options.loop);

        for (const OpenYAMM::Game::AnimatedModelMat4 &matrix : sampledPose->globalTransforms)
        {
            hasErrors = !OpenYAMM::Game::animatedModelMatrixIsFinite(matrix) || hasErrors;
        }
        for (const OpenYAMM::Game::AnimatedModelMat4 &matrix : sampledPose->skinningMatrices)
        {
            hasErrors = !OpenYAMM::Game::animatedModelMatrixIsFinite(matrix) || hasErrors;
        }

        renderPrep = OpenYAMM::Game::buildAnimatedModelRenderPrep(*asset, *sampledPose, options.maxBones);
        hasErrors = diagnosticsHaveErrors(renderPrep->diagnostics) || hasErrors;

        if (!options.socketName.empty())
        {
            socketTransform = OpenYAMM::Game::animatedModelSocketTransform(*asset, *sampledPose, options.socketName);
            if (!socketTransform.has_value())
            {
                std::cerr << "socket not found: " << options.socketName << "\n";
                return 1;
            }

            hasErrors = !OpenYAMM::Game::animatedModelMatrixIsFinite(*socketTransform) || hasErrors;
        }
    }

    if (options.json)
    {
        writeJsonProbeReport(
            options,
            *asset,
            *sidecar,
            resolution,
            resolverDiagnostics,
            pSelectedClip,
            sampledPose ? &*sampledPose : nullptr,
            renderPrep ? &*renderPrep : nullptr,
            socketTransform ? &*socketTransform : nullptr,
            hasErrors);
        return hasErrors ? 1 : 0;
    }

    std::cout << "model_path: " << options.modelPath.generic_string() << "\n";
    std::cout << "sidecar_path: " << options.sidecarPath.generic_string() << "\n";
    if (resolution.has_value())
    {
        std::cout << "model_id: " << resolution->modelId << "\n";
        std::cout << "source_model: " << resolution->normalizedSourceModel << "\n";
        std::cout << "skin_binding: " << resolution->skinBindingId << "\n";
    }
    else
    {
        std::cout << "model_id: " << sidecar->id << "\n";
    }
    std::cout << "primitive_count: " << asset->primitives.size() << "\n";
    std::cout << "vertex_count: " << totalVertexCount(*asset) << "\n";
    std::cout << "index_count: " << totalIndexCount(*asset) << "\n";
    printBounds("bounds", asset->bounds);
    printLod(asset->lod);
    std::cout << "material_count: " << asset->materials.size() << "\n";
    for (size_t index = 0; index < asset->materials.size(); ++index)
    {
        std::cout << "material[" << index << "].texture: "
            << asset->materials[index].baseColorTextureUri << "\n";
    }
    std::cout << "node_count: " << asset->nodes.size() << "\n";
    std::cout << "skin_count: " << asset->skins.size() << "\n";
    std::cout << "first_skin_joint_count: " << firstSkinJointCount(*asset) << "\n";
    std::cout << "animation_count: " << asset->clips.size() << "\n";
    std::cout << "socket_count: " << asset->sockets.size() << "\n";

    if (options.dumpClips)
    {
        printClips(*asset);
    }
    if (options.dumpSockets)
    {
        printSockets(*asset);
    }
    if (options.dumpMaterialOverrides)
    {
        printMaterialOverrides(*sidecar, resolution);
    }

    printDiagnostics(resolverDiagnostics);
    printDiagnostics(asset->diagnostics);

    if (!options.clipName.empty())
    {
        std::cout << "selected_clip: " << pSelectedClip->name << "\n";
        std::cout << "selected_clip_duration_seconds: " << pSelectedClip->durationSeconds << "\n";
        std::cout << "sample_time_ms: " << options.timeMs << "\n";
        std::cout << "sample_loop: " << (options.loop ? "true" : "false") << "\n";
        std::cout << "sample_global_transform_count: " << sampledPose->globalTransforms.size() << "\n";
        std::cout << "sample_skinning_matrix_count: " << sampledPose->skinningMatrices.size() << "\n";
        std::cout << "render_prep.max_bones: " << options.maxBones << "\n";
        std::cout << "render_prep.draw_items: " << renderPrep->drawItems.size() << "\n";
        std::cout << "render_prep.skinned_draw_calls: "
            << renderPrep->counters.skinnedDrawCalls << "\n";
        std::cout << "render_prep.skinned_triangles: "
            << renderPrep->counters.skinnedTriangles << "\n";
        std::cout << "render_prep.uploaded_bone_matrices: "
            << renderPrep->counters.uploadedBoneMatrices << "\n";
        printDiagnostics(renderPrep->diagnostics);

        if (!options.socketName.empty())
        {
            std::cout << "socket: " << options.socketName << "\n";
            std::cout << "socket_transform:";
            for (const float value : socketTransform->values)
            {
                std::cout << " " << value;
            }
            std::cout << "\n";
        }
    }

    return hasErrors ? 1 : 0;
}
