#include "engine/BgfxContext.h"
#include "game/debug/GameImGuiBgfxRenderer.h"
#include "game/mm9/Mm9AnimatedModelSidecar.h"
#include "game/mm9/Mm9DtxTexture.h"
#include "game/render/AnimatedModelAsset.h"
#include "game/render/AnimatedModelRenderer.h"
#include "game/render/TextureFiltering.h"

#include <SDL3/SDL.h>
#include <backends/imgui_impl_sdl3.h>
#include <bgfx/bgfx.h>
#include <bx/math.h>
#include <imgui.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <optional>
#include <string>
#include <vector>

namespace
{
constexpr uint16_t ViewerViewId = 0;
constexpr int DefaultWindowWidth = 1280;
constexpr int DefaultWindowHeight = 800;

struct Arguments
{
    std::filesystem::path modelPath;
    std::filesystem::path sidecarPath;
    std::filesystem::path textureRoot = "assets_dev/worlds/mm9/source";
    std::filesystem::path dumpImagePath;
    std::string clipName;
    float timeSeconds = 0.0f;
    std::optional<float> cameraYaw;
    std::optional<float> cameraPitch;
    std::optional<float> cameraDistance;
    std::optional<float> modelRotationX;
    std::optional<float> modelRotationY;
    std::optional<float> modelRotationZ;
    uint32_t maxFrames = 0;
    bool forceWhiteTexture = false;
};

struct ViewerState
{
    size_t clipIndex = 0;
    float timeSeconds = 0.0f;
    bool playing = true;
    bool loop = true;
    bool showSkeleton = false;
    bool showSockets = false;
    bool showBounds = false;
    bool showDiagnostics = true;
    bool fullbright = true;
    float cameraYaw = 0.6f;
    float cameraPitch = -45.0f;
    float cameraDistance = 2.98f;
    float modelRotationX = -37.6f;
    float modelRotationY = 180.0f;
    float modelRotationZ = -180.0f;
};

struct CameraMatrices
{
    float view[16] = {};
    float projection[16] = {};
    float viewProjection[16] = {};
};

struct PixelStats
{
    uint8_t maxRed = 0;
    uint8_t maxGreen = 0;
    uint8_t maxBlue = 0;
    size_t litPixels = 0;
};

void printUsage()
{
    std::cerr
        << "usage: mm9_animated_model_viewer"
        << " --model <path.glb>"
        << " --sidecar <path.model.yml>"
        << " [--texture-root <assets_dev/worlds/mm9/source>]"
        << " [--clip <name>]"
        << " [--time-ms <ms>]"
        << " [--camera-yaw <degrees>]"
        << " [--camera-pitch <degrees>]"
        << " [--camera-distance <bounds-radius-multiple>]"
        << " [--model-rot-x <degrees>]"
        << " [--model-rot-y <degrees>]"
        << " [--model-rot-z <degrees>]"
        << " [--dump-image </tmp/viewer.bmp>]"
        << " [--force-white-texture]"
        << " [--frames <count>]\n";
}

bool readArgumentValue(int argc, char **argv, int &index, std::string &value)
{
    if (index + 1 >= argc)
    {
        return false;
    }

    value = argv[++index];
    return true;
}

bool parseArguments(int argc, char **argv, Arguments &arguments)
{
    for (int index = 1; index < argc; ++index)
    {
        const std::string name = argv[index];
        std::string value;

        if (name == "--model" && readArgumentValue(argc, argv, index, value))
        {
            arguments.modelPath = value;
        }
        else if (name == "--sidecar" && readArgumentValue(argc, argv, index, value))
        {
            arguments.sidecarPath = value;
        }
        else if (name == "--texture-root" && readArgumentValue(argc, argv, index, value))
        {
            arguments.textureRoot = value;
        }
        else if (name == "--clip" && readArgumentValue(argc, argv, index, value))
        {
            arguments.clipName = value;
        }
        else if (name == "--time-ms" && readArgumentValue(argc, argv, index, value))
        {
            arguments.timeSeconds = std::stof(value) / 1000.0f;
        }
        else if (name == "--camera-yaw" && readArgumentValue(argc, argv, index, value))
        {
            arguments.cameraYaw = std::stof(value);
        }
        else if (name == "--camera-pitch" && readArgumentValue(argc, argv, index, value))
        {
            arguments.cameraPitch = std::stof(value);
        }
        else if (name == "--camera-distance" && readArgumentValue(argc, argv, index, value))
        {
            arguments.cameraDistance = std::stof(value);
        }
        else if (name == "--model-rot-x" && readArgumentValue(argc, argv, index, value))
        {
            arguments.modelRotationX = std::stof(value);
        }
        else if (name == "--model-rot-y" && readArgumentValue(argc, argv, index, value))
        {
            arguments.modelRotationY = std::stof(value);
        }
        else if (name == "--model-rot-z" && readArgumentValue(argc, argv, index, value))
        {
            arguments.modelRotationZ = std::stof(value);
        }
        else if (name == "--dump-image" && readArgumentValue(argc, argv, index, value))
        {
            arguments.dumpImagePath = value;
        }
        else if (name == "--force-white-texture")
        {
            arguments.forceWhiteTexture = true;
        }
        else if (name == "--frames" && readArgumentValue(argc, argv, index, value))
        {
            arguments.maxFrames = static_cast<uint32_t>(std::stoul(value));
        }
        else if (name == "--help" || name == "-h")
        {
            printUsage();
            return false;
        }
        else
        {
            std::cerr << "unknown or incomplete argument: " << name << '\n';
            return false;
        }
    }

    return !arguments.modelPath.empty() && !arguments.sidecarPath.empty();
}

PixelStats bgraPixelStats(const std::vector<uint8_t> &pixels)
{
    PixelStats stats = {};
    for (size_t index = 0; index + 3 < pixels.size(); index += 4)
    {
        const uint8_t blue = pixels[index + 0];
        const uint8_t green = pixels[index + 1];
        const uint8_t red = pixels[index + 2];
        const uint8_t alpha = pixels[index + 3];
        stats.maxRed = std::max(stats.maxRed, red);
        stats.maxGreen = std::max(stats.maxGreen, green);
        stats.maxBlue = std::max(stats.maxBlue, blue);
        if (alpha != 0 && (red > 4 || green > 4 || blue > 4))
        {
            ++stats.litPixels;
        }
    }

    return stats;
}

bool writeBmpBgra(
    const std::filesystem::path &path,
    uint32_t width,
    uint32_t height,
    const std::vector<uint8_t> &pixelsBgra,
    std::string &errorMessage)
{
    if (pixelsBgra.size() < static_cast<size_t>(width) * height * 4u)
    {
        errorMessage = "not enough pixels for BMP output";
        return false;
    }

    if (path.has_parent_path())
    {
        std::filesystem::create_directories(path.parent_path());
    }

    std::ofstream file(path, std::ios::binary);
    if (!file)
    {
        errorMessage = "could not write BMP: " + path.string();
        return false;
    }

    const uint32_t rowStride = width * 4u;
    const uint32_t pixelDataBytes = rowStride * height;
    const uint32_t fileHeaderBytes = 14u;
    const uint32_t dibHeaderBytes = 40u;
    const uint32_t pixelOffset = fileHeaderBytes + dibHeaderBytes;
    const uint32_t fileSize = pixelOffset + pixelDataBytes;
    const auto writeU16 =
        [&file](uint16_t value)
        {
            file.put(static_cast<char>(value & 0xffu));
            file.put(static_cast<char>((value >> 8) & 0xffu));
        };
    const auto writeU32 =
        [&file](uint32_t value)
        {
            file.put(static_cast<char>(value & 0xffu));
            file.put(static_cast<char>((value >> 8) & 0xffu));
            file.put(static_cast<char>((value >> 16) & 0xffu));
            file.put(static_cast<char>((value >> 24) & 0xffu));
        };

    file.put('B');
    file.put('M');
    writeU32(fileSize);
    writeU16(0);
    writeU16(0);
    writeU32(pixelOffset);
    writeU32(dibHeaderBytes);
    writeU32(width);
    writeU32(height);
    writeU16(1);
    writeU16(32);
    writeU32(0);
    writeU32(pixelDataBytes);
    writeU32(2835);
    writeU32(2835);
    writeU32(0);
    writeU32(0);

    for (uint32_t y = 0; y < height; ++y)
    {
        const uint32_t sourceY = height - 1u - y;
        const size_t rowOffset = static_cast<size_t>(sourceY) * rowStride;
        file.write(
            reinterpret_cast<const char *>(pixelsBgra.data() + rowOffset),
            static_cast<std::streamsize>(rowStride));
    }

    return true;
}

float boundsRadius(const OpenYAMM::Game::AnimatedModelBounds &bounds)
{
    if (!bounds.valid)
    {
        return 1.0f;
    }

    const float dx = bounds.max.x - bounds.min.x;
    const float dy = bounds.max.y - bounds.min.y;
    const float dz = bounds.max.z - bounds.min.z;
    return std::max(std::sqrt(dx * dx + dy * dy + dz * dz) * 0.5f, 1.0f);
}

bx::Vec3 boundsCenter(const OpenYAMM::Game::AnimatedModelBounds &bounds)
{
    if (!bounds.valid)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    return {
        (bounds.min.x + bounds.max.x) * 0.5f,
        (bounds.min.y + bounds.max.y) * 0.5f,
        (bounds.min.z + bounds.max.z) * 0.5f};
}

OpenYAMM::Game::AnimatedModelMat4 identityMatrix()
{
    OpenYAMM::Game::AnimatedModelMat4 matrix = {};
    matrix.values[0] = 1.0f;
    matrix.values[5] = 1.0f;
    matrix.values[10] = 1.0f;
    matrix.values[15] = 1.0f;
    return matrix;
}

OpenYAMM::Game::AnimatedModelMat4 multiplyMatrix(
    const OpenYAMM::Game::AnimatedModelMat4 &a,
    const OpenYAMM::Game::AnimatedModelMat4 &b)
{
    OpenYAMM::Game::AnimatedModelMat4 result = {};
    result.values.fill(0.0f);

    for (size_t column = 0; column < 4; ++column)
    {
        for (size_t row = 0; row < 4; ++row)
        {
            for (size_t index = 0; index < 4; ++index)
            {
                result.values[column * 4 + row] +=
                    a.values[index * 4 + row] * b.values[column * 4 + index];
            }
        }
    }

    return result;
}

OpenYAMM::Game::AnimatedModelMat4 rotationXMatrix(float degrees)
{
    const float radians = bx::toRad(degrees);
    const float cosine = std::cos(radians);
    const float sine = std::sin(radians);
    OpenYAMM::Game::AnimatedModelMat4 matrix = identityMatrix();
    matrix.values[5] = cosine;
    matrix.values[6] = sine;
    matrix.values[9] = -sine;
    matrix.values[10] = cosine;
    return matrix;
}

OpenYAMM::Game::AnimatedModelMat4 rotationYMatrix(float degrees)
{
    const float radians = bx::toRad(degrees);
    const float cosine = std::cos(radians);
    const float sine = std::sin(radians);
    OpenYAMM::Game::AnimatedModelMat4 matrix = identityMatrix();
    matrix.values[0] = cosine;
    matrix.values[2] = -sine;
    matrix.values[8] = sine;
    matrix.values[10] = cosine;
    return matrix;
}

OpenYAMM::Game::AnimatedModelMat4 rotationZMatrix(float degrees)
{
    const float radians = bx::toRad(degrees);
    const float cosine = std::cos(radians);
    const float sine = std::sin(radians);
    OpenYAMM::Game::AnimatedModelMat4 matrix = identityMatrix();
    matrix.values[0] = cosine;
    matrix.values[1] = sine;
    matrix.values[4] = -sine;
    matrix.values[5] = cosine;
    return matrix;
}

OpenYAMM::Game::AnimatedModelMat4 modelRotationMatrix(const ViewerState &state)
{
    return multiplyMatrix(
        rotationZMatrix(state.modelRotationZ),
        multiplyMatrix(rotationYMatrix(state.modelRotationY), rotationXMatrix(state.modelRotationX)));
}

OpenYAMM::Game::AnimatedModelVec3 transformPoint(
    const OpenYAMM::Game::AnimatedModelMat4 &matrix,
    const OpenYAMM::Game::AnimatedModelVec3 &point)
{
    return {
        matrix.values[0] * point.x + matrix.values[4] * point.y + matrix.values[8] * point.z + matrix.values[12],
        matrix.values[1] * point.x + matrix.values[5] * point.y + matrix.values[9] * point.z + matrix.values[13],
        matrix.values[2] * point.x + matrix.values[6] * point.y + matrix.values[10] * point.z + matrix.values[14]};
}

bx::Vec3 transformPoint(
    const OpenYAMM::Game::AnimatedModelMat4 &matrix,
    const bx::Vec3 &point)
{
    const OpenYAMM::Game::AnimatedModelVec3 source = {point.x, point.y, point.z};
    const OpenYAMM::Game::AnimatedModelVec3 transformed =
        transformPoint(matrix, source);
    return {transformed.x, transformed.y, transformed.z};
}

bx::Vec3 matrixOrigin(const OpenYAMM::Game::AnimatedModelMat4 &matrix)
{
    return {matrix.values[12], matrix.values[13], matrix.values[14]};
}

bx::Vec3 matrixAxisEnd(const OpenYAMM::Game::AnimatedModelMat4 &matrix, size_t column, float length)
{
    const size_t offset = column * 4;
    return {
        matrix.values[12] + matrix.values[offset + 0] * length,
        matrix.values[13] + matrix.values[offset + 1] * length,
        matrix.values[14] + matrix.values[offset + 2] * length};
}

bool projectPoint(
    const bx::Vec3 &point,
    const float *pViewProjection,
    uint16_t width,
    uint16_t height,
    ImVec2 &screenPoint)
{
    const float clipW =
        point.x * pViewProjection[3]
        + point.y * pViewProjection[7]
        + point.z * pViewProjection[11]
        + pViewProjection[15];

    if (clipW <= 0.0001f)
    {
        return false;
    }

    const float clipX =
        point.x * pViewProjection[0]
        + point.y * pViewProjection[4]
        + point.z * pViewProjection[8]
        + pViewProjection[12];
    const float clipY =
        point.x * pViewProjection[1]
        + point.y * pViewProjection[5]
        + point.z * pViewProjection[9]
        + pViewProjection[13];
    const float inverseW = 1.0f / clipW;
    const float ndcX = clipX * inverseW;
    const float ndcY = clipY * inverseW;

    if (ndcX < -1.25f || ndcX > 1.25f || ndcY < -1.25f || ndcY > 1.25f)
    {
        return false;
    }

    screenPoint.x = ((ndcX + 1.0f) * 0.5f) * static_cast<float>(width);
    screenPoint.y = ((1.0f - ndcY) * 0.5f) * static_cast<float>(height);
    return true;
}

std::string lowerCopy(const std::string &value)
{
    std::string output = value;
    std::transform(output.begin(), output.end(), output.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return output;
}

std::vector<std::string> splitTextureRef(const std::string &textureRef)
{
    std::string normalized = textureRef;
    std::replace(normalized.begin(), normalized.end(), '\\', '/');
    while (!normalized.empty() && normalized.front() == '/')
    {
        normalized.erase(normalized.begin());
    }

    std::vector<std::string> components;
    size_t cursor = 0;
    while (cursor < normalized.size())
    {
        const size_t separator = normalized.find('/', cursor);
        const size_t end = separator == std::string::npos ? normalized.size() : separator;
        if (end > cursor)
        {
            components.push_back(normalized.substr(cursor, end - cursor));
        }
        if (separator == std::string::npos)
        {
            break;
        }
        cursor = separator + 1;
    }
    return components;
}

std::optional<std::filesystem::path> resolveCaseInsensitivePath(
    const std::filesystem::path &root,
    const std::string &textureRef)
{
    std::filesystem::path current = root;
    if (!std::filesystem::exists(current))
    {
        return std::nullopt;
    }

    for (const std::string &component : splitTextureRef(textureRef))
    {
        const std::string componentKey = lowerCopy(component);
        bool found = false;
        for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(current))
        {
            if (lowerCopy(entry.path().filename().string()) == componentKey)
            {
                current = entry.path();
                found = true;
                break;
            }
        }
        if (!found)
        {
            return std::nullopt;
        }
    }

    return current;
}

bgfx::TextureHandle createWhiteTexture()
{
    const uint8_t pixelsBgra[4] = {255, 255, 255, 255};
    return OpenYAMM::Game::createBgraTexture2D(
        1,
        1,
        pixelsBgra,
        sizeof(pixelsBgra),
        OpenYAMM::Game::TextureFilterProfile::BModel);
}

std::optional<bgfx::TextureHandle> loadTextureHandle(
    const std::filesystem::path &textureRoot,
    const std::string &textureRef,
    std::string &errorMessage)
{
    const std::optional<std::filesystem::path> texturePath = resolveCaseInsensitivePath(textureRoot, textureRef);
    if (!texturePath)
    {
        errorMessage = "could not resolve texture: " + textureRef;
        return std::nullopt;
    }

    std::optional<OpenYAMM::Game::Mm9DtxTexture> texture =
        OpenYAMM::Game::loadMm9DtxTexture(*texturePath, errorMessage);
    if (!texture)
    {
        errorMessage = "could not decode texture " + texturePath->string() + ": " + errorMessage;
        return std::nullopt;
    }

    return OpenYAMM::Game::createBgraTexture2D(
        static_cast<uint16_t>(texture->width),
        static_cast<uint16_t>(texture->height),
        texture->pixelsBgra.data(),
        static_cast<uint32_t>(texture->pixelsBgra.size()),
        OpenYAMM::Game::TextureFilterProfile::BModel);
}

CameraMatrices configureView(
    const OpenYAMM::Game::AnimatedModelAsset &asset,
    const ViewerState &state,
    uint16_t width,
    uint16_t height)
{
    CameraMatrices matrices = {};
    const bx::Vec3 center = boundsCenter(asset.bounds);
    const float radius = boundsRadius(asset.bounds);
    const float yaw = bx::toRad(state.cameraYaw);
    const float pitch = bx::toRad(state.cameraPitch);
    const float distance = radius * std::max(state.cameraDistance, 0.25f);
    const bx::Vec3 eye = {
        center.x + std::sin(yaw) * std::cos(pitch) * distance,
        center.y - std::cos(yaw) * std::cos(pitch) * distance,
        center.z + std::sin(pitch) * distance};
    const bx::Vec3 up = {0.0f, 0.0f, 1.0f};

    bx::mtxLookAt(matrices.view, eye, center, up, bx::Handedness::Right);
    bx::mtxProj(
        matrices.projection,
        60.0f,
        static_cast<float>(width) / static_cast<float>(height),
        1.0f,
        std::max(radius * 8.0f, 1000.0f),
        bgfx::getCaps()->homogeneousDepth,
        bx::Handedness::Right);
    bx::mtxMul(matrices.viewProjection, matrices.view, matrices.projection);

    bgfx::setViewName(ViewerViewId, "MM9AnimatedModelViewer");
    bgfx::setViewRect(ViewerViewId, 0, 0, width, height);
    bgfx::setViewClear(ViewerViewId, BGFX_CLEAR_COLOR | BGFX_CLEAR_DEPTH, 0x101114ff, 1.0f, 0);
    bgfx::setViewTransform(ViewerViewId, matrices.view, matrices.projection);
    bgfx::touch(ViewerViewId);
    return matrices;
}

void drawProjectedLine(
    ImDrawList &drawList,
    const CameraMatrices &camera,
    uint16_t width,
    uint16_t height,
    const bx::Vec3 &from,
    const bx::Vec3 &to,
    ImU32 color)
{
    ImVec2 projectedFrom = {};
    ImVec2 projectedTo = {};
    if (projectPoint(from, camera.viewProjection, width, height, projectedFrom)
        && projectPoint(to, camera.viewProjection, width, height, projectedTo))
    {
        drawList.AddLine(projectedFrom, projectedTo, color, 1.5f);
    }
}

void drawSkeletonOverlay(
    ImDrawList &drawList,
    const OpenYAMM::Game::AnimatedModelAsset &asset,
    const OpenYAMM::Game::AnimatedModelPose &pose,
    const OpenYAMM::Game::AnimatedModelMat4 &modelToWorld,
    const CameraMatrices &camera,
    uint16_t width,
    uint16_t height)
{
    const ImU32 lineColor = IM_COL32(255, 214, 94, 220);
    const size_t count = std::min(asset.nodes.size(), pose.globalTransforms.size());
    for (size_t nodeIndex = 0; nodeIndex < count; ++nodeIndex)
    {
        const int parentIndex = asset.nodes[nodeIndex].parentIndex;
        if (parentIndex < 0 || static_cast<size_t>(parentIndex) >= count)
        {
            continue;
        }

        drawProjectedLine(
            drawList,
            camera,
            width,
            height,
            transformPoint(modelToWorld, matrixOrigin(pose.globalTransforms[static_cast<size_t>(parentIndex)])),
            transformPoint(modelToWorld, matrixOrigin(pose.globalTransforms[nodeIndex])),
            lineColor);
    }
}

void drawBoundsOverlay(
    ImDrawList &drawList,
    const OpenYAMM::Game::AnimatedModelBounds &bounds,
    const OpenYAMM::Game::AnimatedModelMat4 &modelToWorld,
    const CameraMatrices &camera,
    uint16_t width,
    uint16_t height)
{
    if (!bounds.valid)
    {
        return;
    }

    const bx::Vec3 corners[8] = {
        {bounds.min.x, bounds.min.y, bounds.min.z},
        {bounds.max.x, bounds.min.y, bounds.min.z},
        {bounds.max.x, bounds.max.y, bounds.min.z},
        {bounds.min.x, bounds.max.y, bounds.min.z},
        {bounds.min.x, bounds.min.y, bounds.max.z},
        {bounds.max.x, bounds.min.y, bounds.max.z},
        {bounds.max.x, bounds.max.y, bounds.max.z},
        {bounds.min.x, bounds.max.y, bounds.max.z},
    };
    const size_t edges[12][2] = {
        {0, 1}, {1, 2}, {2, 3}, {3, 0},
        {4, 5}, {5, 6}, {6, 7}, {7, 4},
        {0, 4}, {1, 5}, {2, 6}, {3, 7},
    };

    for (const auto &edge : edges)
    {
        drawProjectedLine(
            drawList,
            camera,
            width,
            height,
            transformPoint(modelToWorld, corners[edge[0]]),
            transformPoint(modelToWorld, corners[edge[1]]),
            IM_COL32(126, 198, 255, 220));
    }
}

void drawSocketOverlay(
    ImDrawList &drawList,
    const OpenYAMM::Game::AnimatedModelAsset &asset,
    const OpenYAMM::Game::AnimatedModelPose &pose,
    const OpenYAMM::Game::AnimatedModelMat4 &modelToWorld,
    const CameraMatrices &camera,
    uint16_t width,
    uint16_t height)
{
    const float axisLength = boundsRadius(asset.bounds) * 0.08f;
    for (const OpenYAMM::Game::AnimatedModelSocket &socket : asset.sockets)
    {
        const std::optional<OpenYAMM::Game::AnimatedModelMat4> socketTransform =
            OpenYAMM::Game::animatedModelSocketTransform(asset, pose, socket.name);
        if (!socketTransform)
        {
            continue;
        }

        const OpenYAMM::Game::AnimatedModelMat4 worldSocketTransform =
            multiplyMatrix(modelToWorld, *socketTransform);
        const bx::Vec3 origin = matrixOrigin(worldSocketTransform);
        drawProjectedLine(
            drawList,
            camera,
            width,
            height,
            origin,
            matrixAxisEnd(worldSocketTransform, 0, axisLength),
            IM_COL32(255, 88, 88, 240));
        drawProjectedLine(
            drawList,
            camera,
            width,
            height,
            origin,
            matrixAxisEnd(worldSocketTransform, 1, axisLength),
            IM_COL32(90, 220, 114, 240));
        drawProjectedLine(
            drawList,
            camera,
            width,
            height,
            origin,
            matrixAxisEnd(worldSocketTransform, 2, axisLength),
            IM_COL32(96, 156, 255, 240));

        ImVec2 projectedOrigin = {};
        if (projectPoint(origin, camera.viewProjection, width, height, projectedOrigin))
        {
            drawList.AddText(projectedOrigin, IM_COL32(235, 239, 245, 245), socket.name.c_str());
        }
    }
}

void drawOverlays(
    const ViewerState &state,
    const OpenYAMM::Game::AnimatedModelAsset &asset,
    const OpenYAMM::Game::AnimatedModelPose &pose,
    const OpenYAMM::Game::AnimatedModelMat4 &modelToWorld,
    const CameraMatrices &camera,
    uint16_t width,
    uint16_t height)
{
    ImDrawList *pDrawList = ImGui::GetBackgroundDrawList();
    if (pDrawList == nullptr)
    {
        return;
    }

    if (state.showBounds)
    {
        drawBoundsOverlay(*pDrawList, asset.bounds, modelToWorld, camera, width, height);
    }

    if (state.showSkeleton)
    {
        drawSkeletonOverlay(*pDrawList, asset, pose, modelToWorld, camera, width, height);
    }

    if (state.showSockets)
    {
        drawSocketOverlay(*pDrawList, asset, pose, modelToWorld, camera, width, height);
    }
}

void renderControls(
    ViewerState &state,
    const OpenYAMM::Game::AnimatedModelAsset &asset,
    const OpenYAMM::Game::AnimatedModelClip &clip,
    const OpenYAMM::Game::AnimatedModelRenderPrep &renderPrep,
    bgfx::RendererType::Enum rendererType)
{
    ImGui::SetNextWindowPos(ImVec2(16.0f, 16.0f), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(430.0f, 520.0f), ImGuiCond_FirstUseEver);
    if (!ImGui::Begin("MM9 Animated Model Viewer"))
    {
        ImGui::End();
        return;
    }

    ImGui::Text("Renderer: %s", bgfx::getRendererName(rendererType));
    ImGui::Text("Model: %s", asset.sourcePath.filename().string().c_str());
    ImGui::Text("Clip: %s  %.0f / %.0f ms", clip.name.c_str(), state.timeSeconds * 1000.0f,
        clip.durationSeconds * 1000.0f);
    ImGui::Separator();

    const char *pPreview = asset.clips[state.clipIndex].name.c_str();
    if (ImGui::BeginCombo("Clip", pPreview))
    {
        for (size_t clipIndex = 0; clipIndex < asset.clips.size(); ++clipIndex)
        {
            const bool selected = clipIndex == state.clipIndex;
            if (ImGui::Selectable(asset.clips[clipIndex].name.c_str(), selected))
            {
                state.clipIndex = clipIndex;
                state.timeSeconds = 0.0f;
            }
            if (selected)
            {
                ImGui::SetItemDefaultFocus();
            }
        }
        ImGui::EndCombo();
    }

    ImGui::Checkbox("Play", &state.playing);
    ImGui::SameLine();
    ImGui::Checkbox("Loop", &state.loop);
    const float maxTime = std::max(clip.durationSeconds, 0.001f);
    ImGui::SliderFloat("Time", &state.timeSeconds, 0.0f, maxTime, "%.3f s");
    ImGui::Separator();

    ImGui::Checkbox("Skeleton", &state.showSkeleton);
    ImGui::SameLine();
    ImGui::Checkbox("Sockets", &state.showSockets);
    ImGui::SameLine();
    ImGui::Checkbox("Bounds", &state.showBounds);
    ImGui::Checkbox("Diagnostics", &state.showDiagnostics);
    ImGui::SameLine();
    ImGui::Checkbox("Fullbright", &state.fullbright);
    ImGui::SliderFloat("Camera Yaw", &state.cameraYaw, -180.0f, 180.0f, "%.1f deg");
    ImGui::SliderFloat("Camera Pitch", &state.cameraPitch, -45.0f, 75.0f, "%.1f deg");
    ImGui::SliderFloat("Camera Distance", &state.cameraDistance, 0.8f, 8.0f, "%.2f x");
    ImGui::SliderFloat("Model X", &state.modelRotationX, -180.0f, 180.0f, "%.1f deg");
    ImGui::SliderFloat("Model Y", &state.modelRotationY, -180.0f, 180.0f, "%.1f deg");
    ImGui::SliderFloat("Model Z", &state.modelRotationZ, -180.0f, 180.0f, "%.1f deg");
    ImGui::Separator();

    ImGui::Text("Nodes: %zu", asset.nodes.size());
    ImGui::Text("Sockets: %zu", asset.sockets.size());
    ImGui::Text("Draw items: %zu", renderPrep.drawItems.size());
    ImGui::Text("Triangles: %zu", renderPrep.counters.skinnedTriangles);
    ImGui::Text("Bone matrices: %zu", renderPrep.counters.uploadedBoneMatrices);

    if (state.showDiagnostics)
    {
        ImGui::Separator();
        ImGui::TextUnformatted("Diagnostics");
        if (asset.diagnostics.empty() && renderPrep.diagnostics.empty())
        {
            ImGui::TextUnformatted("None");
        }

        for (const OpenYAMM::Game::AnimatedModelDiagnostic &diagnostic : asset.diagnostics)
        {
            ImGui::TextWrapped("%s: %s", diagnostic.error ? "error" : "warning", diagnostic.message.c_str());
        }

        for (const OpenYAMM::Game::AnimatedModelDiagnostic &diagnostic : renderPrep.diagnostics)
        {
            ImGui::TextWrapped("%s: %s", diagnostic.error ? "error" : "warning", diagnostic.message.c_str());
        }
    }

    ImGui::End();
}

void destroyTextureHandles(std::map<std::string, bgfx::TextureHandle> &textureHandles)
{
    for (const auto &entry : textureHandles)
    {
        if (bgfx::isValid(entry.second))
        {
            bgfx::destroy(entry.second);
        }
    }
    textureHandles.clear();
}
}

int main(int argc, char **argv)
{
    Arguments arguments = {};
    if (!parseArguments(argc, argv, arguments))
    {
        printUsage();
        return 2;
    }

    std::string errorMessage;
    std::optional<OpenYAMM::Game::AnimatedModelAsset> asset =
        OpenYAMM::Game::loadAnimatedModelAsset(arguments.modelPath, errorMessage);
    if (!asset)
    {
        std::cerr << errorMessage << '\n';
        return 1;
    }

    std::optional<OpenYAMM::Game::Mm9AnimatedModelSidecar> sidecar =
        OpenYAMM::Game::loadMm9AnimatedModelSidecar(arguments.sidecarPath, errorMessage);
    if (!sidecar)
    {
        std::cerr << errorMessage << '\n';
        return 1;
    }

    OpenYAMM::Game::mergeMm9AnimatedModelSidecar(*sidecar, *asset);
    if (asset->clips.empty())
    {
        std::cerr << "model has no animation clips\n";
        return 1;
    }

    ViewerState state = {};
    state.timeSeconds = arguments.timeSeconds;
    if (arguments.cameraYaw)
    {
        state.cameraYaw = *arguments.cameraYaw;
    }
    if (arguments.cameraPitch)
    {
        state.cameraPitch = *arguments.cameraPitch;
    }
    if (arguments.cameraDistance)
    {
        state.cameraDistance = *arguments.cameraDistance;
    }
    if (arguments.modelRotationX)
    {
        state.modelRotationX = *arguments.modelRotationX;
    }
    if (arguments.modelRotationY)
    {
        state.modelRotationY = *arguments.modelRotationY;
    }
    if (arguments.modelRotationZ)
    {
        state.modelRotationZ = *arguments.modelRotationZ;
    }
    if (!arguments.dumpImagePath.empty())
    {
        state.playing = false;
        state.showSkeleton = false;
        state.showSockets = false;
        state.showBounds = false;
    }
    if (!arguments.clipName.empty())
    {
        const OpenYAMM::Game::AnimatedModelClip *pClip = asset->findClip(arguments.clipName);
        if (pClip == nullptr)
        {
            std::cerr << "clip not found: " << arguments.clipName << '\n';
            return 1;
        }

        for (size_t index = 0; index < asset->clips.size(); ++index)
        {
            if (&asset->clips[index] == pClip)
            {
                state.clipIndex = index;
                break;
            }
        }
    }

    if (!SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS))
    {
        std::cerr << "SDL_Init failed: " << SDL_GetError() << '\n';
        return 1;
    }

    SDL_Window *pWindow = SDL_CreateWindow(
        "MM9 Animated Model Viewer",
        DefaultWindowWidth,
        DefaultWindowHeight,
        SDL_WINDOW_RESIZABLE);
    if (pWindow == nullptr)
    {
        std::cerr << "SDL_CreateWindow failed: " << SDL_GetError() << '\n';
        SDL_Quit();
        return 1;
    }

    int drawableWidth = 0;
    int drawableHeight = 0;
    SDL_GetWindowSizeInPixels(pWindow, &drawableWidth, &drawableHeight);

    OpenYAMM::Engine::BgfxContext bgfxContext;
    if (!bgfxContext.initialize(pWindow, drawableWidth, drawableHeight, true))
    {
        SDL_DestroyWindow(pWindow);
        SDL_Quit();
        return 1;
    }

    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO &io = ImGui::GetIO();
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;
    io.IniFilename = nullptr;

    if (!ImGui_ImplSDL3_InitForOther(pWindow))
    {
        std::cerr << "ImGui SDL backend init failed\n";
        ImGui::DestroyContext();
        bgfxContext.shutdown();
        SDL_DestroyWindow(pWindow);
        SDL_Quit();
        return 1;
    }

    OpenYAMM::Game::GameImGuiBgfxRenderer imguiRenderer;
    if (!imguiRenderer.initialize())
    {
        std::cerr << "ImGui bgfx renderer init failed\n";
        ImGui_ImplSDL3_Shutdown();
        ImGui::DestroyContext();
        bgfxContext.shutdown();
        SDL_DestroyWindow(pWindow);
        SDL_Quit();
        return 1;
    }

    OpenYAMM::Game::AnimatedModelRenderResources renderResources;
    OpenYAMM::Game::AnimatedModelRenderer::initializeResources(renderResources);
    const bgfx::TextureHandle whiteTexture = createWhiteTexture();
    std::map<std::string, bgfx::TextureHandle> textureHandles;
    bool running = true;
    uint64_t lastTick = SDL_GetTicksNS();
    uint32_t renderedFrames = 0;
    std::string lastClipName;
    size_t lastDrawItems = 0;
    size_t lastSubmittedDraws = 0;
    while (running)
    {
        const uint64_t currentTick = SDL_GetTicksNS();
        const float deltaSeconds = currentTick > lastTick
            ? static_cast<float>(currentTick - lastTick) / 1000000000.0f
            : 1.0f / 60.0f;
        lastTick = currentTick;

        SDL_Event event;
        while (SDL_PollEvent(&event))
        {
            ImGui_ImplSDL3_ProcessEvent(&event);
            if (event.type == SDL_EVENT_QUIT || event.type == SDL_EVENT_WINDOW_CLOSE_REQUESTED)
            {
                running = false;
            }
            else if (event.type == SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED)
            {
                SDL_GetWindowSizeInPixels(pWindow, &drawableWidth, &drawableHeight);
                bgfxContext.resize(drawableWidth, drawableHeight);
            }
            else if (event.type == SDL_EVENT_KEY_DOWN && !io.WantCaptureKeyboard)
            {
                if (event.key.key == SDLK_ESCAPE)
                {
                    running = false;
                }
                else if (event.key.key == SDLK_SPACE)
                {
                    state.playing = !state.playing;
                }
                else if (event.key.key == SDLK_LEFT)
                {
                    state.timeSeconds = std::max(state.timeSeconds - 0.05f, 0.0f);
                }
                else if (event.key.key == SDLK_RIGHT)
                {
                    state.timeSeconds += 0.05f;
                }
            }
        }

        SDL_GetWindowSizeInPixels(pWindow, &drawableWidth, &drawableHeight);
        const uint16_t viewWidth = static_cast<uint16_t>(std::max(drawableWidth, 1));
        const uint16_t viewHeight = static_cast<uint16_t>(std::max(drawableHeight, 1));
        const OpenYAMM::Game::AnimatedModelClip &clip = asset->clips[state.clipIndex];
        lastClipName = clip.name;
        if (state.playing)
        {
            state.timeSeconds += deltaSeconds;
        }
        if (clip.durationSeconds > 0.0f)
        {
            if (state.loop)
            {
                state.timeSeconds = std::fmod(std::max(state.timeSeconds, 0.0f), clip.durationSeconds);
            }
            else
            {
                state.timeSeconds = std::clamp(state.timeSeconds, 0.0f, clip.durationSeconds);
            }
        }

        const OpenYAMM::Game::AnimatedModelPose pose =
            OpenYAMM::Game::sampleAnimatedModelPose(*asset, &clip, state.timeSeconds, state.loop);
        const OpenYAMM::Game::AnimatedModelRenderPrep renderPrep =
            OpenYAMM::Game::buildAnimatedModelRenderPrep(
                *asset,
                pose,
                OpenYAMM::Game::AnimatedModelRenderer::MaxShaderBoneMatrices);
        lastDrawItems = renderPrep.drawItems.size();
        lastSubmittedDraws = 0;
        const CameraMatrices camera = configureView(*asset, state, viewWidth, viewHeight);

        const OpenYAMM::Game::AnimatedModelMat4 modelToWorld = modelRotationMatrix(state);
        OpenYAMM::Game::AnimatedModelLightParameters previewLight = {};
        previewLight.values = state.fullbright
            ? std::array<float, 4>{1.45f, 1.45f, 1.45f, 0.15f}
            : std::array<float, 4>{0.78f, 0.78f, 0.78f, 0.32f};
        for (const OpenYAMM::Game::AnimatedModelDrawItem &drawItem : renderPrep.drawItems)
        {
            OpenYAMM::Game::AnimatedModelDrawItem previewDrawItem = drawItem;
            previewDrawItem.doubleSided = true;
            bgfx::TextureHandle textureHandle = whiteTexture;
            if (!arguments.forceWhiteTexture && !drawItem.texture.empty())
            {
                auto textureIterator = textureHandles.find(drawItem.texture);
                if (textureIterator == textureHandles.end())
                {
                    std::optional<bgfx::TextureHandle> loadedTexture =
                        loadTextureHandle(arguments.textureRoot, drawItem.texture, errorMessage);
                    if (loadedTexture)
                    {
                        textureIterator = textureHandles.emplace(drawItem.texture, *loadedTexture).first;
                    }
                    else
                    {
                        std::cerr << errorMessage << '\n';
                    }
                }

                if (textureIterator != textureHandles.end())
                {
                    textureHandle = textureIterator->second;
                }
            }

            if (OpenYAMM::Game::AnimatedModelRenderer::submitDrawItem(
                renderResources,
                ViewerViewId,
                previewDrawItem,
                modelToWorld,
                textureHandle,
                nullptr,
                &previewLight))
            {
                ++lastSubmittedDraws;
            }
        }

        if (!arguments.dumpImagePath.empty())
        {
            if (renderedFrames < 3)
            {
                bgfx::frame();
                ++renderedFrames;
                continue;
            }

            const std::string screenshotToken = "mm9_animated_model_viewer_dump";
            bgfx::requestScreenShot(BGFX_INVALID_HANDLE, screenshotToken.c_str());
            bgfx::frame();
            bgfx::frame();
            bgfx::frame();
            const std::optional<OpenYAMM::Engine::BgfxContext::ScreenshotCapture> screenshot =
                OpenYAMM::Engine::BgfxContext::consumeScreenshot(screenshotToken);
            if (screenshot)
            {
                if (!writeBmpBgra(
                        arguments.dumpImagePath,
                        screenshot->width,
                        screenshot->height,
                        screenshot->bgraPixels,
                        errorMessage))
                {
                    std::cerr << errorMessage << '\n';
                    running = false;
                    continue;
                }

                const PixelStats stats = bgraPixelStats(screenshot->bgraPixels);
                std::cout << "viewer.dump_image: " << arguments.dumpImagePath.string() << '\n';
                std::cout << "viewer.dump_draw_items: " << lastDrawItems << '\n';
                std::cout << "viewer.dump_submitted_draws: " << lastSubmittedDraws << '\n';
                std::cout
                    << "viewer.dump_model_rotation: "
                    << state.modelRotationX << ' '
                    << state.modelRotationY << ' '
                    << state.modelRotationZ << '\n';
                std::cout << "viewer.dump_lit_pixels: " << stats.litPixels << '\n';
                std::cout
                    << "viewer.dump_max_rgb: "
                    << static_cast<uint32_t>(stats.maxRed) << ' '
                    << static_cast<uint32_t>(stats.maxGreen) << ' '
                    << static_cast<uint32_t>(stats.maxBlue) << '\n';
            }
            else
            {
                std::cerr << "viewer backbuffer screenshot was unavailable\n";
            }
            running = false;
            continue;
        }

        ImGui_ImplSDL3_NewFrame();
        imguiRenderer.newFrame();
        ImGui::NewFrame();
        drawOverlays(state, *asset, pose, modelToWorld, camera, viewWidth, viewHeight);
        renderControls(state, *asset, clip, renderPrep, bgfxContext.getRendererType());
        ImGui::Render();
        imguiRenderer.renderDrawData(ImGui::GetDrawData());
        bgfx::frame();

        ++renderedFrames;
        if (arguments.maxFrames != 0 && renderedFrames >= arguments.maxFrames)
        {
            running = false;
        }
    }

    destroyTextureHandles(textureHandles);
    if (bgfx::isValid(whiteTexture))
    {
        bgfx::destroy(whiteTexture);
    }

    if (arguments.maxFrames != 0)
    {
        std::cout << "viewer.model: " << arguments.modelPath.string() << '\n';
        std::cout << "viewer.clip: " << lastClipName << '\n';
        std::cout << "viewer.frames: " << renderedFrames << '\n';
        std::cout << "viewer.renderer: " << bgfx::getRendererName(bgfxContext.getRendererType()) << '\n';
        std::cout << "viewer.draw_items: " << lastDrawItems << '\n';
        std::cout << "viewer.submitted_draws: " << lastSubmittedDraws << '\n';
    }

    renderResources.shutdown();
    imguiRenderer.shutdown();
    ImGui_ImplSDL3_Shutdown();
    ImGui::DestroyContext();
    bgfxContext.shutdown();
    SDL_DestroyWindow(pWindow);
    SDL_Quit();
    return 0;
}
