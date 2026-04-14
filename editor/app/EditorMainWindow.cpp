#include "editor/app/EditorMainWindow.h"
#include "editor/import/ObjModelImport.h"

#include "game/maps/TerrainTileData.h"
#include "game/SpawnPreview.h"
#include "game/data/ActorNameResolver.h"
#include "game/events/EvtEnums.h"
#include "game/outdoor/OutdoorGeometryUtils.h"

#include <imgui.h>
#include <imgui_internal.h>
#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cfloat>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <limits>
#include <optional>
#include <sstream>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#if defined(_WIN32)
#include <process.h>
#else
#include <sys/types.h>
#include <unistd.h>
#endif

namespace OpenYAMM::Editor
{
namespace
{
ImGuiID editorDockspaceId()
{
    return ImGui::GetID("EditorDockspace");
}

std::filesystem::path editorStatePath()
{
    return std::filesystem::current_path() / ".openyamm-editor.ini";
}

std::filesystem::path editorBasePath()
{
    const char *pBasePath = SDL_GetBasePath();

    if (pBasePath == nullptr || *pBasePath == '\0')
    {
        return std::filesystem::current_path();
    }

    return std::filesystem::path(pBasePath);
}

std::filesystem::path defaultGameExecutablePath()
{
#if defined(_WIN32)
    static constexpr const char *ExecutableName = "openyamm.exe";
#else
    static constexpr const char *ExecutableName = "openyamm";
#endif

    const std::filesystem::path basePath = editorBasePath();
    const std::array<std::filesystem::path, 3> candidates = {{
        std::filesystem::current_path() / "build" / "game" / ExecutableName,
        basePath / ".." / "game" / ExecutableName,
        basePath / ExecutableName
    }};

    for (const std::filesystem::path &candidate : candidates)
    {
        std::error_code error;

        if (std::filesystem::exists(candidate, error))
        {
            return std::filesystem::weakly_canonical(candidate, error);
        }
    }

    return {};
}

bool launchDetachedProcess(
    const std::filesystem::path &executablePath,
    const std::vector<std::string> &arguments,
    std::string &errorMessage)
{
    if (executablePath.empty())
    {
        errorMessage = "game executable path is empty";
        return false;
    }

    const std::string executableText = executablePath.string();

#if defined(_WIN32)
    std::vector<const char *> argv;
    argv.reserve(arguments.size() + 2);
    argv.push_back(executableText.c_str());

    for (const std::string &argument : arguments)
    {
        argv.push_back(argument.c_str());
    }

    argv.push_back(nullptr);
    const intptr_t processHandle = _spawnv(_P_NOWAIT, executableText.c_str(), argv.data());

    if (processHandle == -1)
    {
        errorMessage = "could not launch " + executableText;
        return false;
    }

    return true;
#else
    const pid_t childPid = fork();

    if (childPid < 0)
    {
        errorMessage = "could not fork for playtest launch";
        return false;
    }

    if (childPid == 0)
    {
        std::vector<char *> argv;
        argv.reserve(arguments.size() + 2);
        argv.push_back(const_cast<char *>(executableText.c_str()));

        for (const std::string &argument : arguments)
        {
            argv.push_back(const_cast<char *>(argument.c_str()));
        }

        argv.push_back(nullptr);
        execv(executableText.c_str(), argv.data());
        _exit(127);
    }

    return true;
#endif
}

std::string toLowerCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return result;
}

std::string trimCopy(const std::string &value)
{
    const auto begin = std::find_if_not(value.begin(), value.end(), [](unsigned char character)
    {
        return std::isspace(character) != 0;
    });
    const auto end = std::find_if_not(value.rbegin(), value.rend(), [](unsigned char character)
    {
        return std::isspace(character) != 0;
    }).base();

    if (begin >= end)
    {
        return {};
    }

    return std::string(begin, end);
}

bool canSplitImportedModelPathByMesh(const std::string &pathText)
{
    const std::string trimmedPath = trimCopy(pathText);

    if (trimmedPath.empty())
    {
        return false;
    }

    const std::string extension = toLowerCopy(std::filesystem::path(trimmedPath).extension().string());
    return extension == ".gltf" || extension == ".glb";
}

std::string importedModelSummaryText(size_t modelCount)
{
    if (modelCount == 0)
    {
        return "No named meshes found.";
    }

    if (modelCount == 1)
    {
        return "1 named mesh found.";
    }

    return std::to_string(modelCount) + " named meshes found.";
}

size_t countImportedModelMaterials(const ImportedModel &model)
{
    std::unordered_set<std::string> materials;

    for (const ImportedModelFace &face : model.faces)
    {
        const std::string materialName = trimCopy(face.materialName);

        if (!materialName.empty())
        {
            materials.insert(toLowerCopy(materialName));
        }
    }

    return materials.size();
}

EditorMainWindow::ModelImportInspectionState::Entry buildImportedModelInspectionEntry(const ImportedModel &model)
{
    EditorMainWindow::ModelImportInspectionState::Entry entry = {};
    entry.name = model.name;
    entry.vertexCount = model.positions.size();
    entry.faceCount = model.faces.size();
    entry.materialCount = countImportedModelMaterials(model);

    if (model.positions.empty())
    {
        return entry;
    }

    entry.minX = model.positions.front().x;
    entry.minY = model.positions.front().y;
    entry.minZ = model.positions.front().z;
    entry.maxX = model.positions.front().x;
    entry.maxY = model.positions.front().y;
    entry.maxZ = model.positions.front().z;

    for (const ImportedModelPosition &position : model.positions)
    {
        entry.minX = std::min(entry.minX, position.x);
        entry.minY = std::min(entry.minY, position.y);
        entry.minZ = std::min(entry.minZ, position.z);
        entry.maxX = std::max(entry.maxX, position.x);
        entry.maxY = std::max(entry.maxY, position.y);
        entry.maxZ = std::max(entry.maxZ, position.z);
    }

    return entry;
}

std::optional<EditorMainWindow::ModelImportInspectionState::Entry> mergedImportedModelInspectionEntry(
    const EditorMainWindow::ModelImportInspectionState &state)
{
    if (state.entries.empty())
    {
        return std::nullopt;
    }

    EditorMainWindow::ModelImportInspectionState::Entry merged = {};
    merged.name = "<Merged Scene>";
    merged.minX = state.entries.front().minX;
    merged.minY = state.entries.front().minY;
    merged.minZ = state.entries.front().minZ;
    merged.maxX = state.entries.front().maxX;
    merged.maxY = state.entries.front().maxY;
    merged.maxZ = state.entries.front().maxZ;

    for (const EditorMainWindow::ModelImportInspectionState::Entry &entry : state.entries)
    {
        merged.vertexCount += entry.vertexCount;
        merged.faceCount += entry.faceCount;
        merged.materialCount += entry.materialCount;
        merged.minX = std::min(merged.minX, entry.minX);
        merged.minY = std::min(merged.minY, entry.minY);
        merged.minZ = std::min(merged.minZ, entry.minZ);
        merged.maxX = std::max(merged.maxX, entry.maxX);
        merged.maxY = std::max(merged.maxY, entry.maxY);
        merged.maxZ = std::max(merged.maxZ, entry.maxZ);
    }

    return merged;
}

const EditorMainWindow::ModelImportInspectionState::Entry *findImportedModelInspectionEntry(
    const EditorMainWindow::ModelImportInspectionState &state,
    const std::string &selectedModelName)
{
    const std::string normalizedSelection = toLowerCopy(trimCopy(selectedModelName));

    if (normalizedSelection.empty())
    {
        return nullptr;
    }

    for (const EditorMainWindow::ModelImportInspectionState::Entry &entry : state.entries)
    {
        if (toLowerCopy(trimCopy(entry.name)) == normalizedSelection)
        {
            return &entry;
        }
    }

    return nullptr;
}

std::vector<std::string> collectOutdoorMapFileNames(const Engine::AssetFileSystem &assetFileSystem)
{
    const std::vector<std::string> entries = assetFileSystem.enumerate("Data/games");
    std::unordered_set<std::string> seenMapFiles;
    std::vector<std::string> mapFiles;

    for (const std::string &entry : entries)
    {
        std::string mapFileName;

        if (entry.ends_with(".map.yml") || entry.ends_with(".scene.yml"))
        {
            mapFileName = std::filesystem::path(entry).stem().stem().string() + ".odm";
        }
        else if (entry.ends_with(".odm"))
        {
            mapFileName = std::filesystem::path(entry).filename().string();
        }

        if (mapFileName.empty())
        {
            continue;
        }

        const std::string normalized = toLowerCopy(mapFileName);

        if (!seenMapFiles.insert(normalized).second)
        {
            continue;
        }

        mapFiles.push_back(mapFileName);
    }

    std::sort(mapFiles.begin(), mapFiles.end());
    return mapFiles;
}

std::string suggestAvailableMapId(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &preferredBaseId)
{
    const std::vector<std::string> mapFiles = collectOutdoorMapFileNames(assetFileSystem);
    std::unordered_set<std::string> existingIds;

    for (const std::string &mapFile : mapFiles)
    {
        existingIds.insert(toLowerCopy(std::filesystem::path(mapFile).stem().string()));
    }

    std::string baseId = toLowerCopy(trimCopy(preferredBaseId));

    if (baseId.empty())
    {
        baseId = "out16";
    }

    if (!existingIds.contains(baseId))
    {
        return baseId;
    }

    for (int suffix = 1; suffix < 1000; ++suffix)
    {
        const std::string candidate = baseId + "_" + std::to_string(suffix);

        if (!existingIds.contains(candidate))
        {
            return candidate;
        }
    }

    return baseId + "_copy";
}

bool parseBoolValue(const std::string &value)
{
    const std::string normalized = toLowerCopy(trimCopy(value));
    return normalized == "1" || normalized == "true" || normalized == "yes" || normalized == "on";
}

ImVec4 colorFromRgb(uint32_t rgb)
{
    const float red = static_cast<float>((rgb >> 16) & 0xff) / 255.0f;
    const float green = static_cast<float>((rgb >> 8) & 0xff) / 255.0f;
    const float blue = static_cast<float>(rgb & 0xff) / 255.0f;
    return ImVec4(red, green, blue, 1.0f);
}

enum class UiIcon
{
    None,
    Select,
    Face,
    Terrain,
    Entity,
    Spawn,
    Actor,
    Object,
    Move,
    Rotate,
    World,
    Local,
    Snap,
    Paint,
    Rectangle,
    Fill,
    Raise,
    Lower,
    Flatten,
    Smooth,
    Noise,
    Ramp,
    Clay,
    Grid,
    Wireframe,
    Textured
};

void drawArrowHead(ImDrawList *pDrawList, const ImVec2 &tip, const ImVec2 &direction, float size, ImU32 color)
{
    const float length = std::sqrt(direction.x * direction.x + direction.y * direction.y);

    if (length <= 0.0001f)
    {
        return;
    }

    const ImVec2 normal = {direction.x / length, direction.y / length};
    const ImVec2 perpendicular = {-normal.y, normal.x};
    const ImVec2 base = {tip.x - normal.x * size, tip.y - normal.y * size};
    const ImVec2 left = {base.x + perpendicular.x * size * 0.55f, base.y + perpendicular.y * size * 0.55f};
    const ImVec2 right = {base.x - perpendicular.x * size * 0.55f, base.y - perpendicular.y * size * 0.55f};
    pDrawList->AddTriangleFilled(tip, left, right, color);
}

void drawUiIcon(ImDrawList *pDrawList, UiIcon icon, const ImVec2 &origin, float size, ImU32 color)
{
    const float stroke = std::max(1.4f, size * 0.11f);
    const float x = origin.x;
    const float y = origin.y;
    const float s = size;
    const float cX = x + s * 0.5f;
    const float cY = y + s * 0.5f;

    switch (icon)
    {
    case UiIcon::Select:
        pDrawList->AddTriangle(ImVec2(x + s * 0.18f, y + s * 0.12f), ImVec2(x + s * 0.76f, y + s * 0.52f),
            ImVec2(x + s * 0.44f, y + s * 0.60f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.44f, y + s * 0.60f), ImVec2(x + s * 0.63f, y + s * 0.90f), color, stroke);
        break;

    case UiIcon::Face:
        pDrawList->AddQuad(
            ImVec2(x + s * 0.22f, y + s * 0.28f),
            ImVec2(x + s * 0.78f, y + s * 0.20f),
            ImVec2(x + s * 0.72f, y + s * 0.78f),
            ImVec2(x + s * 0.16f, y + s * 0.72f),
            color,
            stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.22f, y + s * 0.28f), ImVec2(x + s * 0.72f, y + s * 0.78f), color, stroke);
        break;

    case UiIcon::Terrain:
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.08f, y + s * 0.70f),
            ImVec2(x + s * 0.30f, y + s * 0.56f),
            ImVec2(x + s * 0.48f, y + s * 0.30f),
            ImVec2(x + s * 0.64f, y + s * 0.40f),
            color,
            stroke);
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.64f, y + s * 0.40f),
            ImVec2(x + s * 0.76f, y + s * 0.46f),
            ImVec2(x + s * 0.84f, y + s * 0.62f),
            ImVec2(x + s * 0.92f, y + s * 0.58f),
            color,
            stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.08f, y + s * 0.70f), ImVec2(x + s * 0.92f, y + s * 0.70f), color, stroke);
        break;

    case UiIcon::Entity:
        pDrawList->AddCircle(ImVec2(cX, y + s * 0.28f), s * 0.14f, color, 0, stroke);
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.20f, y + s * 0.86f),
            ImVec2(x + s * 0.28f, y + s * 0.62f),
            ImVec2(x + s * 0.40f, y + s * 0.56f),
            ImVec2(cX, y + s * 0.56f),
            color,
            stroke);
        pDrawList->AddBezierCubic(
            ImVec2(cX, y + s * 0.56f),
            ImVec2(x + s * 0.60f, y + s * 0.56f),
            ImVec2(x + s * 0.72f, y + s * 0.62f),
            ImVec2(x + s * 0.80f, y + s * 0.86f),
            color,
            stroke);
        break;

    case UiIcon::Spawn:
        pDrawList->AddCircle(ImVec2(cX, y + s * 0.40f), s * 0.20f, color, 0, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.60f), ImVec2(cX, y + s * 0.90f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.90f), ImVec2(x + s * 0.38f, y + s * 0.72f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.90f), ImVec2(x + s * 0.62f, y + s * 0.72f), color, stroke);
        break;

    case UiIcon::Actor:
        pDrawList->AddCircle(ImVec2(cX, y + s * 0.26f), s * 0.14f, color, 0, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.40f), ImVec2(cX, y + s * 0.66f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.30f, y + s * 0.52f), ImVec2(cX, y + s * 0.62f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.62f), ImVec2(x + s * 0.70f, y + s * 0.52f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.66f), ImVec2(x + s * 0.36f, y + s * 0.90f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.66f), ImVec2(x + s * 0.64f, y + s * 0.90f), color, stroke);
        break;

    case UiIcon::Object:
        pDrawList->AddRect(
            ImVec2(x + s * 0.20f, y + s * 0.28f),
            ImVec2(x + s * 0.80f, y + s * 0.80f),
            color,
            0.0f,
            0,
            stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.20f, y + s * 0.44f), ImVec2(x + s * 0.80f, y + s * 0.44f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.40f, y + s * 0.28f), ImVec2(x + s * 0.40f, y + s * 0.80f), color, stroke);
        break;

    case UiIcon::Move:
        pDrawList->AddLine(ImVec2(cX, y + s * 0.14f), ImVec2(cX, y + s * 0.86f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.14f, cY), ImVec2(x + s * 0.86f, cY), color, stroke);
        drawArrowHead(pDrawList, ImVec2(cX, y + s * 0.10f), ImVec2(0.0f, -1.0f), s * 0.10f, color);
        drawArrowHead(pDrawList, ImVec2(cX, y + s * 0.90f), ImVec2(0.0f, 1.0f), s * 0.10f, color);
        drawArrowHead(pDrawList, ImVec2(x + s * 0.10f, cY), ImVec2(-1.0f, 0.0f), s * 0.10f, color);
        drawArrowHead(pDrawList, ImVec2(x + s * 0.90f, cY), ImVec2(1.0f, 0.0f), s * 0.10f, color);
        break;

    case UiIcon::Rotate:
        pDrawList->PathArcTo(ImVec2(cX, cY), s * 0.30f, 3.3f, 7.3f, 24);
        pDrawList->PathStroke(color, 0, stroke);
        drawArrowHead(pDrawList, ImVec2(x + s * 0.24f, y + s * 0.30f), ImVec2(-0.8f, -0.6f), s * 0.10f, color);
        break;

    case UiIcon::World:
        pDrawList->AddCircle(ImVec2(cX, cY), s * 0.34f, color, 0, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.16f, cY), ImVec2(x + s * 0.84f, cY), color, stroke);
        pDrawList->AddBezierCubic(
            ImVec2(cX, y + s * 0.16f),
            ImVec2(x + s * 0.74f, y + s * 0.30f),
            ImVec2(x + s * 0.74f, y + s * 0.70f),
            ImVec2(cX, y + s * 0.84f),
            color,
            stroke);
        pDrawList->AddBezierCubic(
            ImVec2(cX, y + s * 0.16f),
            ImVec2(x + s * 0.26f, y + s * 0.30f),
            ImVec2(x + s * 0.26f, y + s * 0.70f),
            ImVec2(cX, y + s * 0.84f),
            color,
            stroke);
        break;

    case UiIcon::Local:
        pDrawList->AddTriangle(ImVec2(cX, y + s * 0.16f), ImVec2(x + s * 0.18f, y + s * 0.84f),
            ImVec2(x + s * 0.82f, y + s * 0.84f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.16f), ImVec2(cX, y + s * 0.84f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.34f, y + s * 0.60f), ImVec2(x + s * 0.66f, y + s * 0.60f), color, stroke);
        break;

    case UiIcon::Snap:
        pDrawList->AddRect(ImVec2(x + s * 0.28f, y + s * 0.28f), ImVec2(x + s * 0.72f, y + s * 0.72f), color, 0.0f,
            0, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.10f), ImVec2(cX, y + s * 0.28f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.72f), ImVec2(cX, y + s * 0.90f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.10f, cY), ImVec2(x + s * 0.28f, cY), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.72f, cY), ImVec2(x + s * 0.90f, cY), color, stroke);
        break;

    case UiIcon::Paint:
        pDrawList->AddLine(ImVec2(x + s * 0.65f, y + s * 0.18f), ImVec2(x + s * 0.86f, y + s * 0.39f), color, stroke);
        pDrawList->AddRect(ImVec2(x + s * 0.44f, y + s * 0.30f), ImVec2(x + s * 0.67f, y + s * 0.62f), color, 0.0f,
            0, stroke);
        pDrawList->AddTriangle(ImVec2(x + s * 0.22f, y + s * 0.82f), ImVec2(x + s * 0.44f, y + s * 0.30f),
            ImVec2(x + s * 0.56f, y + s * 0.42f), color, stroke);
        break;

    case UiIcon::Rectangle:
        pDrawList->AddRect(
            ImVec2(x + s * 0.18f, y + s * 0.24f),
            ImVec2(x + s * 0.82f, y + s * 0.76f),
            color,
            0.0f,
            0,
            stroke);
        break;

    case UiIcon::Fill:
        pDrawList->AddRectFilled(ImVec2(x + s * 0.20f, y + s * 0.24f), ImVec2(x + s * 0.80f, y + s * 0.78f), color);
        break;

    case UiIcon::Raise:
        pDrawList->AddLine(ImVec2(cX, y + s * 0.18f), ImVec2(cX, y + s * 0.82f), color, stroke);
        drawArrowHead(pDrawList, ImVec2(cX, y + s * 0.14f), ImVec2(0.0f, -1.0f), s * 0.12f, color);
        break;

    case UiIcon::Lower:
        pDrawList->AddLine(ImVec2(cX, y + s * 0.18f), ImVec2(cX, y + s * 0.82f), color, stroke);
        drawArrowHead(pDrawList, ImVec2(cX, y + s * 0.86f), ImVec2(0.0f, 1.0f), s * 0.12f, color);
        break;

    case UiIcon::Flatten:
        pDrawList->AddLine(ImVec2(x + s * 0.16f, y + s * 0.72f), ImVec2(x + s * 0.84f, y + s * 0.72f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.20f), ImVec2(cX, y + s * 0.54f), color, stroke);
        drawArrowHead(pDrawList, ImVec2(cX, y + s * 0.18f), ImVec2(0.0f, -1.0f), s * 0.10f, color);
        break;

    case UiIcon::Smooth:
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.12f, y + s * 0.62f),
            ImVec2(x + s * 0.28f, y + s * 0.32f),
            ImVec2(x + s * 0.46f, y + s * 0.32f),
            ImVec2(cX, y + s * 0.62f),
            color,
            stroke);
        pDrawList->AddBezierCubic(
            ImVec2(cX, y + s * 0.62f),
            ImVec2(x + s * 0.62f, y + s * 0.92f),
            ImVec2(x + s * 0.76f, y + s * 0.92f),
            ImVec2(x + s * 0.88f, y + s * 0.62f),
            color,
            stroke);
        break;

    case UiIcon::Noise:
        pDrawList->AddPolyline(
            std::array<ImVec2, 8> {{
                ImVec2(x + s * 0.10f, y + s * 0.70f),
                ImVec2(x + s * 0.22f, y + s * 0.46f),
                ImVec2(x + s * 0.34f, y + s * 0.76f),
                ImVec2(x + s * 0.46f, y + s * 0.34f),
                ImVec2(x + s * 0.58f, y + s * 0.80f),
                ImVec2(x + s * 0.70f, y + s * 0.50f),
                ImVec2(x + s * 0.82f, y + s * 0.68f),
                ImVec2(x + s * 0.90f, y + s * 0.40f)
            }}.data(),
            8,
            color,
            0,
            stroke);
        break;

    case UiIcon::Ramp:
        pDrawList->AddLine(ImVec2(x + s * 0.14f, y + s * 0.78f), ImVec2(x + s * 0.88f, y + s * 0.78f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.22f, y + s * 0.78f), ImVec2(x + s * 0.76f, y + s * 0.30f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.76f, y + s * 0.30f), ImVec2(x + s * 0.76f, y + s * 0.78f), color, stroke);
        break;

    case UiIcon::Clay:
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.12f, y + s * 0.70f),
            ImVec2(x + s * 0.26f, y + s * 0.40f),
            ImVec2(x + s * 0.44f, y + s * 0.34f),
            ImVec2(x + s * 0.56f, y + s * 0.58f),
            color,
            stroke);
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.56f, y + s * 0.58f),
            ImVec2(x + s * 0.66f, y + s * 0.40f),
            ImVec2(x + s * 0.78f, y + s * 0.36f),
            ImVec2(x + s * 0.88f, y + s * 0.58f),
            color,
            stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.12f, y + s * 0.70f), ImVec2(x + s * 0.88f, y + s * 0.70f), color, stroke);
        break;

    case UiIcon::Grid:
        for (int index = 0; index < 4; ++index)
        {
            const float offset = x + s * (0.18f + 0.18f * static_cast<float>(index));
            pDrawList->AddLine(ImVec2(offset, y + s * 0.12f), ImVec2(offset, y + s * 0.88f), color, stroke);
            pDrawList->AddLine(
                ImVec2(x + s * 0.12f, offset - x + y), ImVec2(x + s * 0.88f, offset - x + y), color, stroke);
        }
        break;

    case UiIcon::Wireframe:
        pDrawList->AddLine(ImVec2(cX, y + s * 0.14f), ImVec2(x + s * 0.82f, y + s * 0.32f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.82f, y + s * 0.32f), ImVec2(x + s * 0.82f, y + s * 0.72f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.82f, y + s * 0.72f), ImVec2(cX, y + s * 0.90f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.90f), ImVec2(x + s * 0.18f, y + s * 0.72f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.18f, y + s * 0.72f), ImVec2(x + s * 0.18f, y + s * 0.32f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.18f, y + s * 0.32f), ImVec2(cX, y + s * 0.14f), color, stroke);
        pDrawList->AddLine(ImVec2(cX, y + s * 0.14f), ImVec2(cX, y + s * 0.90f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.18f, y + s * 0.32f), ImVec2(x + s * 0.82f, y + s * 0.72f), color, stroke);
        pDrawList->AddLine(ImVec2(x + s * 0.82f, y + s * 0.32f), ImVec2(x + s * 0.18f, y + s * 0.72f), color, stroke);
        break;

    case UiIcon::Textured:
        pDrawList->AddRect(ImVec2(x + s * 0.14f, y + s * 0.18f), ImVec2(x + s * 0.86f, y + s * 0.82f), color, 0.0f,
            0, stroke);
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.18f, y + s * 0.44f),
            ImVec2(x + s * 0.30f, y + s * 0.34f),
            ImVec2(x + s * 0.42f, y + s * 0.34f),
            ImVec2(x + s * 0.54f, y + s * 0.44f),
            color,
            stroke);
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.54f, y + s * 0.44f),
            ImVec2(x + s * 0.66f, y + s * 0.54f),
            ImVec2(x + s * 0.74f, y + s * 0.54f),
            ImVec2(x + s * 0.86f, y + s * 0.44f),
            color,
            stroke);
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.18f, y + s * 0.66f),
            ImVec2(x + s * 0.30f, y + s * 0.56f),
            ImVec2(x + s * 0.42f, y + s * 0.56f),
            ImVec2(x + s * 0.54f, y + s * 0.66f),
            color,
            stroke);
        pDrawList->AddBezierCubic(
            ImVec2(x + s * 0.54f, y + s * 0.66f),
            ImVec2(x + s * 0.66f, y + s * 0.76f),
            ImVec2(x + s * 0.74f, y + s * 0.76f),
            ImVec2(x + s * 0.86f, y + s * 0.66f),
            color,
            stroke);
        break;

    case UiIcon::None:
    default:
        break;
    }
}

bool renderTogglePill(const char *pLabel, bool active, const ImVec2 &size = ImVec2(0.0f, 0.0f))
{
    const ImVec4 buttonColor = active ? colorFromRgb(0x56401F) : colorFromRgb(0x1E2328);
    const ImVec4 buttonHovered = active ? colorFromRgb(0x785225) : colorFromRgb(0x252B31);
    const ImVec4 buttonActive = active ? colorFromRgb(0xA86F2E) : colorFromRgb(0x14181C);
    const ImVec4 borderColor = active ? colorFromRgb(0xE0B167) : colorFromRgb(0x323A44);
    const ImVec4 textColor = active ? colorFromRgb(0xFFF0D6) : colorFromRgb(0xBEC6CF);

    ImGui::PushStyleColor(ImGuiCol_Button, buttonColor);
    ImGui::PushStyleColor(ImGuiCol_ButtonHovered, buttonHovered);
    ImGui::PushStyleColor(ImGuiCol_ButtonActive, buttonActive);
    ImGui::PushStyleColor(ImGuiCol_Border, borderColor);
    ImGui::PushStyleColor(ImGuiCol_Text, textColor);
    ImGui::PushStyleVar(ImGuiStyleVar_FrameBorderSize, 1.0f);
    const bool clicked = ImGui::Button(pLabel, size);
    ImGui::PopStyleVar();
    ImGui::PopStyleColor(5);
    return clicked;
}

bool renderIconTogglePill(
    const char *pId,
    const char *pLabel,
    UiIcon icon,
    bool active,
    const ImVec2 &size = ImVec2(0.0f, 0.0f))
{
    ImDrawList *pDrawList = ImGui::GetWindowDrawList();
    const ImGuiStyle &style = ImGui::GetStyle();
    const ImVec2 textSize = ImGui::CalcTextSize(pLabel);
    const float iconSize = 14.0f;
    const float horizontalPadding = style.FramePadding.x + 2.0f;
    const float verticalPadding = style.FramePadding.y;
    const float spacing = 6.0f;
    const ImVec2 buttonSize = size.x > 0.0f || size.y > 0.0f
        ? ImVec2(
            size.x > 0.0f ? size.x : horizontalPadding * 2.0f + iconSize + spacing + textSize.x,
            size.y > 0.0f ? size.y : std::max(iconSize, textSize.y) + verticalPadding * 2.0f)
        : ImVec2(horizontalPadding * 2.0f + iconSize + spacing + textSize.x,
            std::max(iconSize, textSize.y) + verticalPadding * 2.0f);

    ImGui::PushID(pId);
    const bool clicked = ImGui::InvisibleButton("##IconPill", buttonSize);
    const bool hovered = ImGui::IsItemHovered();
    const bool held = ImGui::IsItemActive();
    ImGui::PopID();

    const uint32_t bg = active ? 0x56401F : 0x1E2328;
    const uint32_t bgHover = active ? 0x785225 : 0x252B31;
    const uint32_t bgPressed = active ? 0xA86F2E : 0x14181C;
    const uint32_t border = active ? 0xE0B167 : 0x323A44;
    const uint32_t text = active ? 0xFFF0D6 : 0xBEC6CF;
    const ImU32 bgColor = ImGui::ColorConvertFloat4ToU32(colorFromRgb(held ? bgPressed : hovered ? bgHover : bg));
    const ImU32 borderColor = ImGui::ColorConvertFloat4ToU32(colorFromRgb(border));
    const ImU32 textColor = ImGui::ColorConvertFloat4ToU32(colorFromRgb(text));
    const ImRect rect(ImGui::GetItemRectMin(), ImGui::GetItemRectMax());
    pDrawList->AddRectFilled(rect.Min, rect.Max, bgColor, 4.0f);
    pDrawList->AddRect(rect.Min, rect.Max, borderColor, 4.0f, 0, 1.0f);

    const ImVec2 iconOrigin = {
        rect.Min.x + horizontalPadding,
        rect.Min.y + (buttonSize.y - iconSize) * 0.5f
    };
    drawUiIcon(pDrawList, icon, iconOrigin, iconSize, textColor);
    pDrawList->AddText(
        ImVec2(iconOrigin.x + iconSize + spacing, rect.Min.y + (buttonSize.y - textSize.y) * 0.5f),
        textColor,
        pLabel);
    return clicked;
}

bool renderSecondaryTogglePill(const char *pLabel, bool active, const ImVec2 &size = ImVec2(0.0f, 0.0f))
{
    const ImVec4 buttonColor = active ? colorFromRgb(0x232931) : colorFromRgb(0x13171B);
    const ImVec4 buttonHovered = active ? colorFromRgb(0x2A313B) : colorFromRgb(0x161A1E);
    const ImVec4 buttonActive = active ? colorFromRgb(0x313A45) : colorFromRgb(0x101317);
    const ImVec4 borderColor = active ? colorFromRgb(0x4A5664) : colorFromRgb(0x1F252C);
    const ImVec4 textColor = active ? colorFromRgb(0xC5CED8) : colorFromRgb(0x79828D);

    ImGui::PushStyleColor(ImGuiCol_Button, buttonColor);
    ImGui::PushStyleColor(ImGuiCol_ButtonHovered, buttonHovered);
    ImGui::PushStyleColor(ImGuiCol_ButtonActive, buttonActive);
    ImGui::PushStyleColor(ImGuiCol_Border, borderColor);
    ImGui::PushStyleColor(ImGuiCol_Text, textColor);
    ImGui::PushStyleVar(ImGuiStyleVar_FrameBorderSize, 1.0f);
    const bool clicked = ImGui::Button(pLabel, size);
    ImGui::PopStyleVar();
    ImGui::PopStyleColor(5);
    return clicked;
}

bool renderSecondaryIconTogglePill(
    const char *pId,
    const char *pLabel,
    UiIcon icon,
    bool active,
    const ImVec2 &size = ImVec2(0.0f, 0.0f))
{
    ImDrawList *pDrawList = ImGui::GetWindowDrawList();
    const ImGuiStyle &style = ImGui::GetStyle();
    const ImVec2 textSize = ImGui::CalcTextSize(pLabel);
    const float iconSize = 14.0f;
    const float horizontalPadding = style.FramePadding.x + 2.0f;
    const float verticalPadding = style.FramePadding.y;
    const float spacing = 6.0f;
    const ImVec2 buttonSize = size.x > 0.0f || size.y > 0.0f
        ? ImVec2(
            size.x > 0.0f ? size.x : horizontalPadding * 2.0f + iconSize + spacing + textSize.x,
            size.y > 0.0f ? size.y : std::max(iconSize, textSize.y) + verticalPadding * 2.0f)
        : ImVec2(horizontalPadding * 2.0f + iconSize + spacing + textSize.x,
            std::max(iconSize, textSize.y) + verticalPadding * 2.0f);

    ImGui::PushID(pId);
    const bool clicked = ImGui::InvisibleButton("##SecondaryIconPill", buttonSize);
    const bool hovered = ImGui::IsItemHovered();
    const bool held = ImGui::IsItemActive();
    ImGui::PopID();

    const uint32_t bg = active ? 0x232931 : 0x13171B;
    const uint32_t bgHover = active ? 0x2A313B : 0x161A1E;
    const uint32_t bgPressed = active ? 0x313A45 : 0x101317;
    const uint32_t border = active ? 0x4A5664 : 0x1F252C;
    const uint32_t text = active ? 0xC5CED8 : 0x79828D;
    const ImU32 bgColor = ImGui::ColorConvertFloat4ToU32(colorFromRgb(held ? bgPressed : hovered ? bgHover : bg));
    const ImU32 borderColor = ImGui::ColorConvertFloat4ToU32(colorFromRgb(border));
    const ImU32 textColor = ImGui::ColorConvertFloat4ToU32(colorFromRgb(text));
    const ImRect rect(ImGui::GetItemRectMin(), ImGui::GetItemRectMax());
    pDrawList->AddRectFilled(rect.Min, rect.Max, bgColor, 4.0f);
    pDrawList->AddRect(rect.Min, rect.Max, borderColor, 4.0f, 0, 1.0f);

    const ImVec2 iconOrigin = {
        rect.Min.x + horizontalPadding,
        rect.Min.y + (buttonSize.y - iconSize) * 0.5f
    };
    drawUiIcon(pDrawList, icon, iconOrigin, iconSize, textColor);
    pDrawList->AddText(
        ImVec2(iconOrigin.x + iconSize + spacing, rect.Min.y + (buttonSize.y - textSize.y) * 0.5f),
        textColor,
        pLabel);
    return clicked;
}

UiIcon selectionKindIcon(EditorSelectionKind kind)
{
    switch (kind)
    {
    case EditorSelectionKind::Terrain:
        return UiIcon::Terrain;

    case EditorSelectionKind::InteractiveFace:
        return UiIcon::Face;

    case EditorSelectionKind::Entity:
        return UiIcon::Entity;

    case EditorSelectionKind::Spawn:
        return UiIcon::Spawn;

    case EditorSelectionKind::Actor:
        return UiIcon::Actor;

    case EditorSelectionKind::SpriteObject:
        return UiIcon::Object;

    case EditorSelectionKind::None:
    default:
        return UiIcon::Select;
    }
}

UiIcon terrainPaintModeIcon(EditorTerrainPaintMode mode)
{
    switch (mode)
    {
    case EditorTerrainPaintMode::Brush:
        return UiIcon::Paint;

    case EditorTerrainPaintMode::Rectangle:
        return UiIcon::Rectangle;

    case EditorTerrainPaintMode::Fill:
    default:
        return UiIcon::Fill;
    }
}

UiIcon terrainSculptModeIcon(EditorTerrainSculptMode mode)
{
    switch (mode)
    {
    case EditorTerrainSculptMode::Raise:
        return UiIcon::Raise;

    case EditorTerrainSculptMode::Lower:
        return UiIcon::Lower;

    case EditorTerrainSculptMode::Flatten:
        return UiIcon::Flatten;

    case EditorTerrainSculptMode::Smooth:
        return UiIcon::Smooth;

    case EditorTerrainSculptMode::Noise:
        return UiIcon::Noise;

    case EditorTerrainSculptMode::Ramp:
    default:
        return UiIcon::Ramp;
    }
}

bool matchesSceneFilter(const char *pFilterText, const std::string &label)
{
    const std::string filter = toLowerCopy(trimCopy(pFilterText != nullptr ? pFilterText : ""));

    if (filter.empty())
    {
        return true;
    }

    return toLowerCopy(label).find(filter) != std::string::npos;
}

void beginToolbarCard(const char *pTitle, float width = 0.0f)
{
    ImGui::PushStyleColor(ImGuiCol_ChildBg, colorFromRgb(0x171B1F));
    ImGui::PushStyleColor(ImGuiCol_Border, colorFromRgb(0x303741));
    ImGui::BeginChild(pTitle, ImVec2(width, 0.0f), ImGuiChildFlags_Borders, ImGuiWindowFlags_NoScrollbar);
    ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0x97A0AC));
    ImGui::TextUnformatted(pTitle);
    ImGui::PopStyleColor();
    ImGui::Dummy(ImVec2(0.0f, 1.0f));
}

void endToolbarCard()
{
    ImGui::EndChild();
    ImGui::PopStyleColor(2);
}

void renderStatusPill(const char *pLabel, uint32_t textColorRgb, uint32_t borderColorRgb, uint32_t fillColorRgb)
{
    ImGui::PushStyleColor(ImGuiCol_Button, colorFromRgb(fillColorRgb));
    ImGui::PushStyleColor(ImGuiCol_ButtonHovered, colorFromRgb(fillColorRgb));
    ImGui::PushStyleColor(ImGuiCol_ButtonActive, colorFromRgb(fillColorRgb));
    ImGui::PushStyleColor(ImGuiCol_Border, colorFromRgb(borderColorRgb));
    ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(textColorRgb));
    ImGui::PushStyleVar(ImGuiStyleVar_FrameBorderSize, 1.0f);
    ImGui::Button(pLabel);
    ImGui::PopStyleVar();
    ImGui::PopStyleColor(5);
}

void renderToolbarSubLabel(const char *pLabel)
{
    ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0x8C95A0));
    ImGui::TextUnformatted(pLabel);
    ImGui::PopStyleColor();
}

std::string activeEditorContextSummary(const EditorSession &session, const EditorOutdoorViewport &viewport)
{
    if (viewport.placementKind() == EditorSelectionKind::Terrain)
    {
        if (session.terrainSculptEnabled())
        {
            const char *pTool = "Raise";

            switch (session.terrainSculptMode())
            {
            case EditorTerrainSculptMode::Lower:
                pTool = "Lower";
                break;
            case EditorTerrainSculptMode::Flatten:
                pTool = "Flatten";
                break;
            case EditorTerrainSculptMode::Smooth:
                pTool = "Smooth";
                break;
            case EditorTerrainSculptMode::Noise:
                pTool = "Noise";
                break;
            case EditorTerrainSculptMode::Ramp:
                pTool = "Ramp";
                break;
            case EditorTerrainSculptMode::Raise:
            default:
                break;
            }

            return std::string("Terrain  ·  Sculpt  ·  ") + pTool;
        }

        return "Terrain  ·  Paint";
    }

    const char *pMode = "Select";

    switch (viewport.placementKind())
    {
    case EditorSelectionKind::InteractiveFace:
        pMode = "Face";
        break;
    case EditorSelectionKind::BModel:
        pMode = "BModel Place";
        break;
    case EditorSelectionKind::Entity:
        pMode = "Entity Place";
        break;
    case EditorSelectionKind::Spawn:
        pMode = "Spawn Place";
        break;
    case EditorSelectionKind::Actor:
        pMode = "Actor Place";
        break;
    case EditorSelectionKind::SpriteObject:
        pMode = "Object Place";
        break;
    case EditorSelectionKind::None:
    default:
        break;
    }

    const char *pTransform = viewport.transformGizmoMode() == EditorOutdoorViewport::TransformGizmoMode::Rotate
        ? "Rotate"
        : "Move";
    const char *pSpace = viewport.transformSpaceMode() == EditorOutdoorViewport::TransformSpaceMode::Local
        ? "Local"
        : "World";
    return std::string(pMode) + "  ·  " + pTransform + "  ·  " + pSpace;
}

std::string inspectorFieldId(const char *pLabel);
void beginInspectorFieldRow(const char *pLabel);

std::string actorDisplayLabel(
    const Game::MonsterTable *pMonsterTable,
    const Game::MapDeltaActor &actor,
    size_t actorIndex)
{
    if (pMonsterTable != nullptr)
    {
        const std::string resolvedName = Game::resolveMapDeltaActorName(*pMonsterTable, actor);

        if (!resolvedName.empty())
        {
            return resolvedName;
        }
    }

    if (actor.uniqueNameIndex > 0)
    {
        return "Unique Actor " + std::to_string(actor.uniqueNameIndex);
    }

    if (actor.monsterInfoId > 0)
    {
        return "Monster Info " + std::to_string(actor.monsterInfoId);
    }

    if (actor.monsterId > 0)
    {
        return "Monster " + std::to_string(actor.monsterId);
    }

    return "Actor " + std::to_string(actorIndex);
}

std::string actorMonsterTemplateLabel(const Game::MonsterTable *pMonsterTable, const Game::MapDeltaActor &actor)
{
    if (pMonsterTable == nullptr)
    {
        return {};
    }

    const Game::MonsterTable::MonsterDisplayNameEntry *pDisplayEntry =
        pMonsterTable->findDisplayEntryById(actor.monsterInfoId);

    if (pDisplayEntry != nullptr && !pDisplayEntry->displayName.empty())
    {
        return pDisplayEntry->displayName;
    }

    const int16_t effectiveMonsterId = actor.monsterInfoId > 0 ? actor.monsterInfoId : actor.monsterId;
    const Game::MonsterTable::MonsterStatsEntry *pStats = pMonsterTable->findStatsById(effectiveMonsterId);

    if (pStats != nullptr && !pStats->name.empty())
    {
        return pStats->name;
    }

    return {};
}

std::string hostilityTypeLabel(uint8_t hostilityType)
{
    if (hostilityType == 0)
    {
        return "Auto/Default (0)";
    }

    return "Raw " + std::to_string(hostilityType);
}

EditorBModelSourceTransform sourceTransformFromBModel(const Game::OutdoorBModel &bmodel)
{
    EditorBModelSourceTransform transform = {};

    if (bmodel.vertices.empty())
    {
        transform.originX = static_cast<float>(bmodel.boundingCenterX);
        transform.originY = static_cast<float>(bmodel.boundingCenterY);
        transform.originZ = static_cast<float>(bmodel.boundingCenterZ);
        return transform;
    }

    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float minZ = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();
    float maxZ = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        minX = std::min(minX, static_cast<float>(vertex.x));
        minY = std::min(minY, static_cast<float>(vertex.y));
        minZ = std::min(minZ, static_cast<float>(vertex.z));
        maxX = std::max(maxX, static_cast<float>(vertex.x));
        maxY = std::max(maxY, static_cast<float>(vertex.y));
        maxZ = std::max(maxZ, static_cast<float>(vertex.z));
    }

    transform.originX = (minX + maxX) * 0.5f;
    transform.originY = (minY + maxY) * 0.5f;
    transform.originZ = (minZ + maxZ) * 0.5f;
    return transform;
}

std::array<float, 3> rotateVectorByEulerDegrees(
    const std::array<float, 3> &vector,
    float rotationXDegrees,
    float rotationYDegrees,
    float rotationZDegrees)
{
    const float rotationXRadians = rotationXDegrees * 3.14159265358979323846f / 180.0f;
    const float rotationYRadians = rotationYDegrees * 3.14159265358979323846f / 180.0f;
    const float rotationZRadians = rotationZDegrees * 3.14159265358979323846f / 180.0f;
    const float cosX = std::cos(rotationXRadians);
    const float sinX = std::sin(rotationXRadians);
    const float cosY = std::cos(rotationYRadians);
    const float sinY = std::sin(rotationYRadians);
    const float cosZ = std::cos(rotationZRadians);
    const float sinZ = std::sin(rotationZRadians);
    const float rotatedXY = vector[1] * cosX - vector[2] * sinX;
    const float rotatedXZ = vector[1] * sinX + vector[2] * cosX;
    const float rotatedYX = vector[0] * cosY + rotatedXZ * sinY;
    const float rotatedYZ = -vector[0] * sinY + rotatedXZ * cosY;
    const float rotatedZX = rotatedYX * cosZ - rotatedXY * sinZ;
    const float rotatedZY = rotatedYX * sinZ + rotatedXY * cosZ;
    return {rotatedZX, rotatedZY, rotatedYZ};
}

std::string spriteObjectDisplayLabel(const Game::MapDeltaSpriteObject &spriteObject, size_t objectIndex)
{
    if (spriteObject.objectDescriptionId != 0)
    {
        return "Object " + std::to_string(spriteObject.objectDescriptionId);
    }

    if (spriteObject.spriteId != 0)
    {
        return "Sprite " + std::to_string(spriteObject.spriteId);
    }

    return "Sprite Object " + std::to_string(objectIndex);
}

std::pair<std::string, std::string> inspectorSelectionSummary(const EditorSession &session)
{
    if (!session.hasDocument())
    {
        return {"No document", {}};
    }

    const EditorDocument &document = session.document();
    const EditorSelection &selection = session.selection();

    switch (selection.kind)
    {
    case EditorSelectionKind::None:
    case EditorSelectionKind::Summary:
        return {"Level Summary", document.displayName()};

    case EditorSelectionKind::Environment:
        return {"Environment", document.displayName()};

    case EditorSelectionKind::Terrain:
    {
        if (selection.index == std::numeric_limits<size_t>::max())
        {
            return {"Terrain", "Map-wide terrain settings"};
        }

        const int cellX = static_cast<int>(selection.index % Game::OutdoorMapData::TerrainWidth);
        const int cellY = static_cast<int>(selection.index / Game::OutdoorMapData::TerrainWidth);
        return {"Terrain Cell", std::to_string(cellX) + ", " + std::to_string(cellY)};
    }

    case EditorSelectionKind::BModel:
        return {"BModel", "Index " + std::to_string(selection.index)};

    case EditorSelectionKind::InteractiveFace:
        return {"Face Selection", std::to_string(session.selectedInteractiveFaceIndices().size()) + " selected"};

    case EditorSelectionKind::Entity:
    {
        const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();

        if (selection.index < sceneData.entities.size())
        {
            const Game::OutdoorSceneEntity &entity = sceneData.entities[selection.index];
            const std::string name = entity.entity.name.empty()
                ? "Entity " + std::to_string(entity.entityIndex)
                : entity.entity.name;
            return {"Entity", name};
        }

        break;
    }

    case EditorSelectionKind::Spawn:
        return {"Spawn", "Index " + std::to_string(selection.index)};

    case EditorSelectionKind::Actor:
    {
        const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();

        if (selection.index < sceneData.initialState.actors.size())
        {
            return {
                "Actor",
                actorDisplayLabel(&session.monsterTable(), sceneData.initialState.actors[selection.index], selection.index)
            };
        }

        break;
    }

    case EditorSelectionKind::SpriteObject:
    {
        const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();

        if (selection.index < sceneData.initialState.spriteObjects.size())
        {
            return {
                "Sprite Object",
                spriteObjectDisplayLabel(sceneData.initialState.spriteObjects[selection.index], selection.index)
            };
        }

        break;
    }

    case EditorSelectionKind::Chest:
        return {"Chest", "Index " + std::to_string(selection.index)};
    }

    return {"Selection", {}};
}

const EditorIdLabelOption *findOptionById(
    const std::vector<EditorIdLabelOption> &options,
    uint32_t id)
{
    for (const EditorIdLabelOption &option : options)
    {
        if (option.id == id)
        {
            return &option;
        }
    }

    return nullptr;
}

std::string selectorPreviewLabel(
    uint32_t value,
    const std::vector<EditorIdLabelOption> &options,
    const char *pZeroLabel,
    const char *pFallbackPrefix)
{
    if (value == 0 && pZeroLabel != nullptr)
    {
        return pZeroLabel;
    }

    const EditorIdLabelOption *pOption = findOptionById(options, value);

    if (pOption != nullptr)
    {
        return pOption->label;
    }

    return std::string(pFallbackPrefix) + " #" + std::to_string(value);
}

std::string canonicalBitmapTextureName(
    const std::vector<std::string> &options,
    const std::string &value)
{
    const std::string loweredValue = toLowerCopy(value);

    for (const std::string &option : options)
    {
        if (toLowerCopy(option) == loweredValue)
        {
            return option;
        }
    }

    return value;
}

bool optionMatchesFilter(const EditorIdLabelOption &option, const std::string &filter)
{
    if (filter.empty())
    {
        return true;
    }

    const std::string lowerLabel = toLowerCopy(option.label);
    const std::string lowerId = std::to_string(option.id);
    return lowerLabel.find(filter) != std::string::npos || lowerId.find(filter) != std::string::npos;
}

bool editOptionField(
    EditorSession &session,
    const char *pLabel,
    uint32_t &value,
    const std::vector<EditorIdLabelOption> &options,
    const char *pZeroLabel,
    const char *pFallbackPrefix)
{
    beginInspectorFieldRow(pLabel);

    const std::string comboId = inspectorFieldId(pLabel);
    const std::string preview = selectorPreviewLabel(value, options, pZeroLabel, pFallbackPrefix);

    if (!ImGui::BeginCombo(comboId.c_str(), preview.c_str()))
    {
        return false;
    }

    const ImGuiID filterStorageId = ImGui::GetID((comboId + "/filter").c_str());
    static std::unordered_map<ImGuiID, std::string> filters;
    std::string &filter = filters[filterStorageId];
    char filterBuffer[128] = {};
    std::snprintf(filterBuffer, sizeof(filterBuffer), "%s", filter.c_str());
    ImGui::SetNextItemWidth(-FLT_MIN);

    if (ImGui::InputText("##Filter", filterBuffer, sizeof(filterBuffer)))
    {
        filter = filterBuffer;
    }

    const std::string normalizedFilter = toLowerCopy(filter);
    bool changed = false;

    if (pZeroLabel != nullptr)
    {
        const bool selected = value == 0;

        if ((normalizedFilter.empty() || toLowerCopy(pZeroLabel).find(normalizedFilter) != std::string::npos)
            && ImGui::Selectable(pZeroLabel, selected))
        {
            if (value != 0)
            {
                session.captureUndoSnapshot();
                value = 0;
                changed = true;
            }
        }

        if (selected)
        {
            ImGui::SetItemDefaultFocus();
        }
    }

    for (const EditorIdLabelOption &option : options)
    {
        if (!optionMatchesFilter(option, normalizedFilter))
        {
            continue;
        }

        const bool selected = option.id == value;

        if (ImGui::Selectable(option.label.c_str(), selected))
        {
            if (option.id != value)
            {
                session.captureUndoSnapshot();
                value = option.id;
                changed = true;
            }
        }

        if (selected)
        {
            ImGui::SetItemDefaultFocus();
        }
    }

    ImGui::EndCombo();
    return changed;
}

bool editTransientOptionField(
    const char *pLabel,
    uint32_t &value,
    const std::vector<EditorIdLabelOption> &options,
    const char *pZeroLabel,
    const char *pFallbackPrefix)
{
    beginInspectorFieldRow(pLabel);

    const std::string comboId = inspectorFieldId(pLabel);
    const std::string preview = selectorPreviewLabel(value, options, pZeroLabel, pFallbackPrefix);

    if (!ImGui::BeginCombo(comboId.c_str(), preview.c_str()))
    {
        return false;
    }

    const ImGuiID filterStorageId = ImGui::GetID((comboId + "/filter").c_str());
    static std::unordered_map<ImGuiID, std::string> filters;
    std::string &filter = filters[filterStorageId];
    char filterBuffer[128] = {};
    std::snprintf(filterBuffer, sizeof(filterBuffer), "%s", filter.c_str());
    ImGui::SetNextItemWidth(-FLT_MIN);

    if (ImGui::InputText("##Filter", filterBuffer, sizeof(filterBuffer)))
    {
        filter = filterBuffer;
    }

    const std::string normalizedFilter = toLowerCopy(filter);
    bool changed = false;

    if (pZeroLabel != nullptr)
    {
        const bool selected = value == 0;

        if ((normalizedFilter.empty() || toLowerCopy(pZeroLabel).find(normalizedFilter) != std::string::npos)
            && ImGui::Selectable(pZeroLabel, selected))
        {
            value = 0;
            changed = true;
        }

        if (selected)
        {
            ImGui::SetItemDefaultFocus();
        }
    }

    for (const EditorIdLabelOption &option : options)
    {
        if (!optionMatchesFilter(option, normalizedFilter))
        {
            continue;
        }

        const bool selected = option.id == value;

        if (ImGui::Selectable(option.label.c_str(), selected))
        {
            value = option.id;
            changed = true;
        }

        if (selected)
        {
            ImGui::SetItemDefaultFocus();
        }
    }

    ImGui::EndCombo();
    return changed;
}

constexpr float InspectorMinLabelColumnWidth = 170.0f;
constexpr float InspectorMaxLabelColumnWidth = 260.0f;
constexpr float InspectorFieldMaxWidth = 240.0f;
constexpr uint32_t MonsterBitShowOnMap = 0x00008000u;
constexpr uint32_t MonsterBitInvisible = 0x00010000u;
constexpr uint32_t MonsterBitNoFlee = 0x00020000u;
constexpr uint32_t MonsterBitHostile = 0x00080000u;
constexpr uint32_t MonsterBitOnAlertMap = 0x00100000u;
constexpr uint32_t MonsterBitTreasureGenerated = 0x00800000u;
constexpr uint32_t MonsterBitShowAsHostile = 0x01000000u;
constexpr uint16_t ObjectBitVisible = 0x0001u;
constexpr uint16_t ObjectBitTemporary = 0x0002u;
constexpr uint16_t ObjectBitHaltTurnBased = 0x0004u;
constexpr uint16_t ObjectBitDroppedByPlayer = 0x0008u;
constexpr uint16_t ObjectBitIgnoreRange = 0x0010u;
constexpr uint16_t ObjectBitNoZBuffer = 0x0020u;
constexpr uint16_t ObjectBitSkipAFrame = 0x0040u;
constexpr uint16_t ObjectBitAttachToHead = 0x0080u;
constexpr uint16_t ObjectBitMissile = 0x0100u;
constexpr uint16_t ObjectBitRemoved = 0x0200u;
constexpr uint16_t ChestBitTrapped = 0x0001u;
constexpr uint16_t ChestBitItemsPlaced = 0x0002u;
constexpr uint16_t ChestBitIdentified = 0x0004u;
constexpr uint32_t FaceAttributeFluid = 0x00000010u;
constexpr uint32_t FaceAttributeInvisible = static_cast<uint32_t>(Game::EvtFaceAttribute::Invisible);
constexpr uint32_t FaceAttributeHasHint = static_cast<uint32_t>(Game::EvtFaceAttribute::HasHint);
constexpr uint32_t FaceAttributeClickable = static_cast<uint32_t>(Game::EvtFaceAttribute::Clickable);
constexpr uint32_t FaceAttributePressurePlate = static_cast<uint32_t>(Game::EvtFaceAttribute::PressurePlate);
constexpr uint32_t FaceAttributeUntouchable = static_cast<uint32_t>(Game::EvtFaceAttribute::Untouchable);
constexpr uint32_t EditableFaceAttributeMask =
    FaceAttributeFluid
    | FaceAttributeInvisible
    | FaceAttributeHasHint
    | FaceAttributeClickable
    | FaceAttributePressurePlate
    | FaceAttributeUntouchable;
constexpr size_t ChestItemRecordSize = 36;
constexpr size_t ChestItemRecordCount = 140;

enum class BModelBulkFaceScope
{
    All = 0,
    Walkable = 1,
    Blocking = 2
};

std::string inspectorFieldId(const char *pLabel)
{
    return "##" + std::string(pLabel);
}

bool beginInspectorPropertyTable(const char *pId)
{
    if (!ImGui::BeginTable(
            pId,
            2,
            ImGuiTableFlags_SizingStretchProp
                | ImGuiTableFlags_NoSavedSettings
                | ImGuiTableFlags_BordersInnerV
                | ImGuiTableFlags_BordersInnerH
                | ImGuiTableFlags_RowBg))
    {
        return false;
    }

    const float availableWidth = ImGui::GetContentRegionAvail().x;
    const float labelWidth = std::clamp(
        availableWidth * 0.42f,
        InspectorMinLabelColumnWidth,
        InspectorMaxLabelColumnWidth);
    ImGui::TableSetupColumn("Label", ImGuiTableColumnFlags_WidthFixed, labelWidth);
    ImGui::TableSetupColumn("Value", ImGuiTableColumnFlags_WidthStretch);
    return true;
}

void beginInspectorFieldRow(const char *pLabel)
{
    ImGui::TableNextRow();
    ImGui::TableSetColumnIndex(0);
    ImGui::AlignTextToFramePadding();
    ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0xAAB3BD));
    ImGui::TextUnformatted(pLabel);
    ImGui::PopStyleColor();
    ImGui::TableSetColumnIndex(1);
    ImGui::SetNextItemWidth(std::min(ImGui::GetContentRegionAvail().x, InspectorFieldMaxWidth));
}

void renderInspectorReadOnlyField(const char *pLabel, const std::string &value)
{
    beginInspectorFieldRow(pLabel);
    ImGui::TextUnformatted(value.c_str());
}

void renderInspectorReadOnlyField(const char *pLabel, const char *pValue)
{
    beginInspectorFieldRow(pLabel);
    ImGui::TextUnformatted(pValue);
}

const char *bmodelBulkFaceScopeLabel(BModelBulkFaceScope scope)
{
    switch (scope)
    {
    case BModelBulkFaceScope::Walkable:
        return "Walkable Faces";
    case BModelBulkFaceScope::Blocking:
        return "Blocking Faces";
    case BModelBulkFaceScope::All:
    default:
        return "All Faces";
    }
}

const char *outdoorTilesetPresetLabel(EditorOutdoorMapTilesetPreset preset)
{
    switch (preset)
    {
    case EditorOutdoorMapTilesetPreset::Shadowspire:
        return "Shadowspire";
    case EditorOutdoorMapTilesetPreset::IronsandDesert:
        return "Ironsand Desert";
    case EditorOutdoorMapTilesetPreset::Grassland:
    default:
        return "Grassland";
    }
}

bool bmodelFaceMatchesScope(const Game::OutdoorBModelFace &face, BModelBulkFaceScope scope)
{
    switch (scope)
    {
    case BModelBulkFaceScope::Walkable:
        return Game::isOutdoorWalkablePolygonType(face.polygonType);
    case BModelBulkFaceScope::Blocking:
        return !Game::isOutdoorWalkablePolygonType(face.polygonType);
    case BModelBulkFaceScope::All:
    default:
        return true;
    }
}

void repairOutdoorSceneFaceReferencesAfterDelete(
    Game::OutdoorSceneData &sceneData,
    size_t bmodelIndex,
    size_t deletedFaceIndex)
{
    sceneData.interactiveFaces.erase(
        std::remove_if(
            sceneData.interactiveFaces.begin(),
            sceneData.interactiveFaces.end(),
            [bmodelIndex, deletedFaceIndex](Game::OutdoorSceneInteractiveFace &face)
            {
                if (face.bmodelIndex != bmodelIndex)
                {
                    return false;
                }

                if (face.faceIndex == deletedFaceIndex)
                {
                    return true;
                }

                if (face.faceIndex > deletedFaceIndex)
                {
                    --face.faceIndex;
                }

                return false;
            }),
        sceneData.interactiveFaces.end());

    sceneData.initialState.faceAttributeOverrides.erase(
        std::remove_if(
            sceneData.initialState.faceAttributeOverrides.begin(),
            sceneData.initialState.faceAttributeOverrides.end(),
            [bmodelIndex, deletedFaceIndex](Game::OutdoorSceneFaceAttributeOverride &face)
            {
                if (face.bmodelIndex != bmodelIndex)
                {
                    return false;
                }

                if (face.faceIndex == deletedFaceIndex)
                {
                    return true;
                }

                if (face.faceIndex > deletedFaceIndex)
                {
                    --face.faceIndex;
                }

                return false;
            }),
        sceneData.initialState.faceAttributeOverrides.end());
}

bool renderTerrainTilePreviewButton(
    const EditorOutdoorViewport &viewport,
    uint8_t tileId,
    bool selected,
    const ImVec2 &size)
{
    float u0 = 0.0f;
    float v0 = 0.0f;
    float u1 = 0.0f;
    float v1 = 0.0f;
    const bool hasPreview =
        bgfx::isValid(viewport.terrainTextureAtlasHandle())
        && viewport.tryGetTerrainTilePreviewUv(tileId, u0, v0, u1, v1);

    ImGui::PushID(static_cast<int>(tileId));

    if (!hasPreview)
    {
        char label[8] = {};
        std::snprintf(label, sizeof(label), "%02X", tileId);
        const bool clicked = ImGui::Button(label, size);
        ImGui::PopID();
        return clicked;
    }

    const ImVec2 cursorPosition = ImGui::GetCursorScreenPos();
    const bool clicked = ImGui::InvisibleButton("##TerrainTilePreview", size);
    const ImGuiID itemId = ImGui::GetItemID();
    const bool hovered = ImGui::IsItemHovered();
    const ImU32 borderColor = ImGui::GetColorU32(
        selected
            ? ImVec4(0.92f, 0.72f, 0.22f, 1.0f)
            : (hovered ? ImVec4(0.82f, 0.62f, 0.22f, 0.95f) : ImVec4(0.16f, 0.16f, 0.16f, 1.0f)));
    const ImU32 backgroundColor = ImGui::GetColorU32(ImVec4(0.08f, 0.08f, 0.08f, 1.0f));
    ImDrawList *pDrawList = ImGui::GetWindowDrawList();
    const ImVec2 endPosition = ImVec2(cursorPosition.x + size.x, cursorPosition.y + size.y);
    pDrawList->AddRectFilled(cursorPosition, endPosition, backgroundColor, 3.0f);
    pDrawList->AddImage(
        static_cast<ImTextureID>(static_cast<uintptr_t>(viewport.terrainTextureAtlasHandle().idx + 1)),
        ImVec2(cursorPosition.x + 2.0f, cursorPosition.y + 2.0f),
        ImVec2(endPosition.x - 2.0f, endPosition.y - 2.0f),
        ImVec2(u0, v0),
        ImVec2(u1, v1));
    pDrawList->AddRect(cursorPosition, endPosition, borderColor, 3.0f, 0, selected ? 2.0f : 1.0f);

    if (hovered)
    {
        ImGui::SetTooltip("Tile %u (0x%02X)", static_cast<unsigned>(tileId), static_cast<unsigned>(tileId));
    }

    ImGui::PopID();
    return clicked;
}

std::optional<std::vector<uint8_t>> loadBitmapPreviewPixels(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::vector<std::string> &bitmapTextureNames,
    const std::string &textureName,
    int &width,
    int &height)
{
    const std::string canonicalName = canonicalBitmapTextureName(bitmapTextureNames, textureName);

    if (canonicalName.empty())
    {
        return std::nullopt;
    }

    const std::string virtualPath = "Data/bitmaps/" + canonicalName + ".bmp";
    const std::optional<std::vector<uint8_t>> bitmapBytes = assetFileSystem.readBinaryFile(virtualPath);

    if (!bitmapBytes || bitmapBytes->empty())
    {
        return std::nullopt;
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bitmapBytes->data(), bitmapBytes->size());

    if (pIoStream == nullptr)
    {
        return std::nullopt;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        return std::nullopt;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        return std::nullopt;
    }

    width = pConvertedSurface->w;
    height = pConvertedSurface->h;
    std::vector<uint8_t> pixels(static_cast<size_t>(width * height * 4));
    std::memcpy(pixels.data(), pConvertedSurface->pixels, pixels.size());
    SDL_DestroySurface(pConvertedSurface);
    return pixels;
}

std::optional<std::string> findDirectoryEntryPath(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &directoryPath,
    const std::string &fileName)
{
    const std::vector<std::string> entries = assetFileSystem.enumerate(directoryPath);
    const std::string normalizedFileName = toLowerCopy(fileName);

    for (const std::string &entry : entries)
    {
        if (toLowerCopy(entry) == normalizedFileName)
        {
            return directoryPath + "/" + entry;
        }
    }

    return std::nullopt;
}

std::optional<std::array<uint8_t, 256 * 3>> loadActPalettePreview(
    const Engine::AssetFileSystem &assetFileSystem,
    int16_t paletteId)
{
    if (paletteId <= 0)
    {
        return std::nullopt;
    }

    char paletteFileName[32] = {};
    std::snprintf(paletteFileName, sizeof(paletteFileName), "pal%03d.act", static_cast<int>(paletteId));
    const std::optional<std::string> palettePath =
        findDirectoryEntryPath(assetFileSystem, "Data/bitmaps", paletteFileName);

    if (!palettePath)
    {
        return std::nullopt;
    }

    const std::optional<std::vector<uint8_t>> paletteBytes = assetFileSystem.readBinaryFile(*palettePath);

    if (!paletteBytes || paletteBytes->size() < 256 * 3)
    {
        return std::nullopt;
    }

    std::array<uint8_t, 256 * 3> palette = {};
    std::memcpy(palette.data(), paletteBytes->data(), palette.size());
    return palette;
}

std::optional<std::vector<uint8_t>> loadSpritePreviewPixels(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &textureName,
    int16_t paletteId,
    int &width,
    int &height)
{
    const std::optional<std::string> bitmapPath =
        findDirectoryEntryPath(assetFileSystem, "Data/sprites", textureName + ".bmp");

    if (!bitmapPath)
    {
        return std::nullopt;
    }

    const std::optional<std::vector<uint8_t>> bitmapBytes = assetFileSystem.readBinaryFile(*bitmapPath);

    if (!bitmapBytes || bitmapBytes->empty())
    {
        return std::nullopt;
    }

    SDL_IOStream *pIoStream = SDL_IOFromConstMem(bitmapBytes->data(), bitmapBytes->size());

    if (pIoStream == nullptr)
    {
        return std::nullopt;
    }

    SDL_Surface *pLoadedSurface = SDL_LoadBMP_IO(pIoStream, true);

    if (pLoadedSurface == nullptr)
    {
        return std::nullopt;
    }

    SDL_Palette *pBasePalette = SDL_GetSurfacePalette(pLoadedSurface);
    const std::optional<std::array<uint8_t, 256 * 3>> overridePalette =
        loadActPalettePreview(assetFileSystem, paletteId);
    const bool canApplyPalette =
        overridePalette.has_value()
        && pLoadedSurface->format == SDL_PIXELFORMAT_INDEX8
        && pBasePalette != nullptr;

    if (canApplyPalette)
    {
        width = pLoadedSurface->w;
        height = pLoadedSurface->h;
        std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4);

        for (int row = 0; row < height; ++row)
        {
            const uint8_t *pSourceRow = static_cast<const uint8_t *>(pLoadedSurface->pixels)
                + static_cast<ptrdiff_t>(row * pLoadedSurface->pitch);

            for (int column = 0; column < width; ++column)
            {
                const uint8_t paletteIndex = pSourceRow[column];
                const SDL_Color sourceColor =
                    paletteIndex < pBasePalette->ncolors
                        ? pBasePalette->colors[paletteIndex]
                        : SDL_Color{0, 0, 0, 255};
                const bool isMagentaKey =
                    sourceColor.r >= 248 && sourceColor.g <= 8 && sourceColor.b >= 248;
                const bool isTealKey =
                    sourceColor.r <= 8 && sourceColor.g >= 248 && sourceColor.b >= 248;
                const size_t paletteOffset = static_cast<size_t>(paletteIndex) * 3;
                const size_t pixelOffset =
                    (static_cast<size_t>(row) * static_cast<size_t>(width) + static_cast<size_t>(column)) * 4;

                pixels[pixelOffset + 0] = (*overridePalette)[paletteOffset + 2];
                pixels[pixelOffset + 1] = (*overridePalette)[paletteOffset + 1];
                pixels[pixelOffset + 2] = (*overridePalette)[paletteOffset + 0];
                pixels[pixelOffset + 3] = (isMagentaKey || isTealKey) ? 0 : 255;
            }
        }

        SDL_DestroySurface(pLoadedSurface);
        return pixels;
    }

    SDL_Surface *pConvertedSurface = SDL_ConvertSurface(pLoadedSurface, SDL_PIXELFORMAT_BGRA32);
    SDL_DestroySurface(pLoadedSurface);

    if (pConvertedSurface == nullptr)
    {
        return std::nullopt;
    }

    width = pConvertedSurface->w;
    height = pConvertedSurface->h;
    std::vector<uint8_t> pixels(static_cast<size_t>(width) * static_cast<size_t>(height) * 4);

    for (int row = 0; row < height; ++row)
    {
        const uint8_t *pSourceRow = static_cast<const uint8_t *>(pConvertedSurface->pixels)
            + static_cast<ptrdiff_t>(row * pConvertedSurface->pitch);
        uint8_t *pTargetRow = pixels.data() + static_cast<size_t>(row) * static_cast<size_t>(width) * 4;
        std::memcpy(pTargetRow, pSourceRow, static_cast<size_t>(width) * 4);
    }

    for (size_t pixelOffset = 0; pixelOffset < pixels.size(); pixelOffset += 4)
    {
        const uint8_t blue = pixels[pixelOffset + 0];
        const uint8_t green = pixels[pixelOffset + 1];
        const uint8_t red = pixels[pixelOffset + 2];
        const bool isMagentaKey = red >= 248 && green <= 8 && blue >= 248;
        const bool isTealKey = red <= 8 && green >= 248 && blue >= 248;

        if (isMagentaKey || isTealKey)
        {
            pixels[pixelOffset + 3] = 0;
        }
    }

    SDL_DestroySurface(pConvertedSurface);
    return pixels;
}

int16_t clampToInt16(int value)
{
    return static_cast<int16_t>(std::clamp(value, -32768, 32767));
}

std::pair<int, int> faceTextureCoordinateRange(const std::vector<int16_t> &coordinates)
{
    if (coordinates.empty())
    {
        return {0, 0};
    }

    int minimum = coordinates.front();
    int maximum = coordinates.front();

    for (int16_t value : coordinates)
    {
        minimum = std::min(minimum, static_cast<int>(value));
        maximum = std::max(maximum, static_cast<int>(value));
    }

    return {minimum, maximum};
}

void flipFaceTextureAxis(std::vector<int16_t> &coordinates)
{
    const auto [minimum, maximum] = faceTextureCoordinateRange(coordinates);

    for (int16_t &value : coordinates)
    {
        value = clampToInt16(minimum + maximum - static_cast<int>(value));
    }
}

void scaleFaceTextureAxis(std::vector<int16_t> &coordinates, float scale)
{
    if (coordinates.empty())
    {
        return;
    }

    const auto [minimum, maximum] = faceTextureCoordinateRange(coordinates);
    const float center = (static_cast<float>(minimum) + static_cast<float>(maximum)) * 0.5f;

    for (int16_t &value : coordinates)
    {
        const float scaled = center + (static_cast<float>(value) - center) * scale;
        value = clampToInt16(static_cast<int>(std::lround(scaled)));
    }
}

void fitFaceTextureAxis(std::vector<int16_t> &coordinates, int extent)
{
    if (coordinates.empty() || extent <= 0)
    {
        return;
    }

    const auto [minimum, maximum] = faceTextureCoordinateRange(coordinates);

    if (minimum == maximum)
    {
        coordinates.front() = 0;

        for (size_t index = 1; index < coordinates.size(); ++index)
        {
            coordinates[index] = static_cast<int16_t>(extent);
        }

        return;
    }

    const float sourceRange = static_cast<float>(maximum - minimum);

    for (int16_t &value : coordinates)
    {
        const float normalized = (static_cast<float>(value) - static_cast<float>(minimum)) / sourceRange;
        value = clampToInt16(static_cast<int>(std::lround(normalized * static_cast<float>(extent))));
    }
}

void resetFaceTextureMappingFromGeometry(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    Game::OutdoorBModelFace &face)
{
    if (face.vertexIndices.size() < 3)
    {
        return;
    }

    const auto vertexAt = [&vertices](uint16_t index) -> const Game::OutdoorBModelVertex &
    {
        return vertices[index];
    };

    const Game::OutdoorBModelVertex &a = vertexAt(face.vertexIndices[0]);
    const Game::OutdoorBModelVertex &b = vertexAt(face.vertexIndices[1]);
    const Game::OutdoorBModelVertex &c = vertexAt(face.vertexIndices[2]);
    const float abX = static_cast<float>(b.x - a.x);
    const float abY = static_cast<float>(b.y - a.y);
    const float abZ = static_cast<float>(b.z - a.z);
    const float acX = static_cast<float>(c.x - a.x);
    const float acY = static_cast<float>(c.y - a.y);
    const float acZ = static_cast<float>(c.z - a.z);
    const float normalX = abY * acZ - abZ * acY;
    const float normalY = abZ * acX - abX * acZ;
    const float normalZ = abX * acY - abY * acX;
    const float absNormalX = std::fabs(normalX);
    const float absNormalY = std::fabs(normalY);
    const float absNormalZ = std::fabs(normalZ);

    face.textureUs.clear();
    face.textureVs.clear();
    face.textureUs.reserve(face.vertexIndices.size());
    face.textureVs.reserve(face.vertexIndices.size());

    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex >= vertices.size())
        {
            face.textureUs.push_back(0);
            face.textureVs.push_back(0);
            continue;
        }

        const Game::OutdoorBModelVertex &vertex = vertices[vertexIndex];
        int16_t textureU = 0;
        int16_t textureV = 0;

        if (absNormalZ >= absNormalX && absNormalZ >= absNormalY)
        {
            textureU = clampToInt16(vertex.x);
            textureV = clampToInt16(-vertex.y);
        }
        else if (absNormalX >= absNormalY)
        {
            textureU = clampToInt16(vertex.y);
            textureV = clampToInt16(-vertex.z);
        }
        else
        {
            textureU = clampToInt16(vertex.x);
            textureV = clampToInt16(-vertex.z);
        }

        face.textureUs.push_back(textureU);
        face.textureVs.push_back(textureV);
    }

    face.textureDeltaU = 0;
    face.textureDeltaV = 0;
}

bx::Vec3 faceNormal(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    const Game::OutdoorBModelFace &face)
{
    if (face.vertexIndices.size() < 3)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    const auto vertexAt = [&vertices](uint16_t index) -> const Game::OutdoorBModelVertex &
    {
        return vertices[index];
    };

    const Game::OutdoorBModelVertex &a = vertexAt(face.vertexIndices[0]);
    const Game::OutdoorBModelVertex &b = vertexAt(face.vertexIndices[1]);
    const Game::OutdoorBModelVertex &c = vertexAt(face.vertexIndices[2]);
    const bx::Vec3 edge1 = {
        static_cast<float>(b.x - a.x),
        static_cast<float>(b.y - a.y),
        static_cast<float>(b.z - a.z)};
    const bx::Vec3 edge2 = {
        static_cast<float>(c.x - a.x),
        static_cast<float>(c.y - a.y),
        static_cast<float>(c.z - a.z)};
    const bx::Vec3 normal = {
        edge1.y * edge2.z - edge1.z * edge2.y,
        edge1.z * edge2.x - edge1.x * edge2.z,
        edge1.x * edge2.y - edge1.y * edge2.x};
    const float length = std::sqrt(normal.x * normal.x + normal.y * normal.y + normal.z * normal.z);

    if (length <= 0.0001f)
    {
        return {0.0f, 0.0f, 0.0f};
    }

    const float invLength = 1.0f / length;
    return {
        normal.x * invLength,
        normal.y * invLength,
        normal.z * invLength};
}

float faceOutwardDot(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    const Game::OutdoorBModelFace &face,
    float modelCenterX,
    float modelCenterY,
    float modelCenterZ)
{
    if (face.vertexIndices.empty())
    {
        return 0.0f;
    }

    bx::Vec3 normal = faceNormal(vertices, face);
    bx::Vec3 center = {0.0f, 0.0f, 0.0f};
    int validVertexCount = 0;

    for (uint16_t vertexIndex : face.vertexIndices)
    {
        if (vertexIndex >= vertices.size())
        {
            continue;
        }

        center.x += static_cast<float>(vertices[vertexIndex].x);
        center.y += static_cast<float>(vertices[vertexIndex].y);
        center.z += static_cast<float>(vertices[vertexIndex].z);
        ++validVertexCount;
    }

    if (validVertexCount == 0)
    {
        return 0.0f;
    }

    const float invCount = 1.0f / static_cast<float>(validVertexCount);
    center.x *= invCount;
    center.y *= invCount;
    center.z *= invCount;

    return normal.x * (center.x - modelCenterX)
        + normal.y * (center.y - modelCenterY)
        + normal.z * (center.z - modelCenterZ);
}

void reverseFaceWinding(Game::OutdoorBModelFace &face)
{
    std::reverse(face.vertexIndices.begin(), face.vertexIndices.end());
    std::reverse(face.textureUs.begin(), face.textureUs.end());
    std::reverse(face.textureVs.begin(), face.textureVs.end());
}

void orientFaceWindingOutward(
    const std::vector<Game::OutdoorBModelVertex> &vertices,
    Game::OutdoorBModelFace &face,
    float modelCenterX,
    float modelCenterY,
    float modelCenterZ)
{
    if (face.vertexIndices.size() < 3)
    {
        return;
    }

    bool shouldReverse = false;

    if (face.polygonType == 0x3 || face.polygonType == 0x4)
    {
        const bx::Vec3 normal = faceNormal(vertices, face);
        shouldReverse = normal.z < 0.0f;
    }
    else
    {
        shouldReverse = faceOutwardDot(vertices, face, modelCenterX, modelCenterY, modelCenterZ) < 0.0f;
    }

    if (shouldReverse)
    {
        reverseFaceWinding(face);
    }
}

void renderInspectorSectionHeader(const char *pLabel)
{
    ImGui::Spacing();
    ImGui::PushStyleColor(ImGuiCol_Separator, colorFromRgb(0x37414D));
    ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0xF8E4C7));
    ImGui::SeparatorText(pLabel);
    ImGui::PopStyleColor(2);
}

bool beginInspectorSectionBlock(const char *pLabel, bool defaultOpen = true)
{
    ImGui::PushStyleColor(ImGuiCol_Header, colorFromRgb(0x23292F));
    ImGui::PushStyleColor(ImGuiCol_HeaderHovered, colorFromRgb(0x2A3139));
    ImGui::PushStyleColor(ImGuiCol_HeaderActive, colorFromRgb(0x4B3318));
    ImGui::PushStyleColor(ImGuiCol_Border, colorFromRgb(0x404854));
    ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0xF8E4C7));
    ImGui::PushStyleVar(ImGuiStyleVar_FramePadding, ImVec2(10.0f, 7.0f));
    ImGui::PushStyleVar(ImGuiStyleVar_FrameBorderSize, 1.0f);
    const bool open = ImGui::CollapsingHeader(
        pLabel,
        (defaultOpen ? ImGuiTreeNodeFlags_DefaultOpen : ImGuiTreeNodeFlags_None) | ImGuiTreeNodeFlags_Framed);
    ImGui::PopStyleVar(2);
    ImGui::PopStyleColor(5);

    if (open)
    {
        ImGui::Indent(8.0f);
        ImGui::Spacing();
    }

    return open;
}

void endInspectorSectionBlock()
{
    ImGui::Unindent(8.0f);
    ImGui::Spacing();
}

bool editStringField(EditorSession &session, const char *pLabel, std::string &value, size_t capacity)
{
    const size_t bufferSize = std::max(capacity, value.size() + 1);
    std::vector<char> buffer(bufferSize, '\0');
    std::copy(value.begin(), value.end(), buffer.begin());

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputText(inspectorFieldId(pLabel).c_str(), buffer.data(), buffer.size()))
    {
        return false;
    }

    session.captureUndoSnapshot();
    value = buffer.data();
    return true;
}

bool editTransientStringField(const char *pLabel, std::string &value, size_t capacity)
{
    const size_t bufferSize = std::max(capacity, value.size() + 1);
    std::vector<char> buffer(bufferSize, '\0');
    std::copy(value.begin(), value.end(), buffer.begin());

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputText(inspectorFieldId(pLabel).c_str(), buffer.data(), buffer.size()))
    {
        return false;
    }

    value = buffer.data();
    return true;
}

bool editIntField(EditorSession &session, const char *pLabel, int &value, int minimum, int maximum)
{
    int editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt(inspectorFieldId(pLabel).c_str(), &editedValue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, minimum, maximum);

    if (editedValue == value)
    {
        return false;
    }

    session.captureUndoSnapshot();
    value = editedValue;
    return true;
}

bool editTransientIntField(const char *pLabel, int &value, int minimum, int maximum)
{
    int editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt(inspectorFieldId(pLabel).c_str(), &editedValue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, minimum, maximum);

    if (editedValue == value)
    {
        return false;
    }

    value = editedValue;
    return true;
}

bool editUInt8Field(EditorSession &session, const char *pLabel, uint8_t &value)
{
    int editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt(inspectorFieldId(pLabel).c_str(), &editedValue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, 0, 255);

    if (editedValue == value)
    {
        return false;
    }

    session.captureUndoSnapshot();
    value = static_cast<uint8_t>(editedValue);
    return true;
}

bool editUInt16Field(EditorSession &session, const char *pLabel, uint16_t &value)
{
    int editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt(inspectorFieldId(pLabel).c_str(), &editedValue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, 0, 65535);

    if (editedValue == value)
    {
        return false;
    }

    session.captureUndoSnapshot();
    value = static_cast<uint16_t>(editedValue);
    return true;
}

bool editTransientUInt16Field(const char *pLabel, uint16_t &value)
{
    int editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt(inspectorFieldId(pLabel).c_str(), &editedValue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, 0, 65535);

    if (editedValue == value)
    {
        return false;
    }

    value = static_cast<uint16_t>(editedValue);
    return true;
}

bool editMapEventField(EditorSession &session, const char *pLabel, uint16_t &value)
{
    const std::vector<EditorIdLabelOption> &options = session.mapEventOptions();

    beginInspectorFieldRow(pLabel);

    bool changed = false;
    uint32_t selectedValue = value;
    const std::string comboId = inspectorFieldId(pLabel) + "/combo";
    const std::string preview = selectorPreviewLabel(selectedValue, options, "<none>", "Event");
    const float inputWidth = 90.0f;
    const float spacing = ImGui::GetStyle().ItemInnerSpacing.x;
    const float comboWidth = std::max(80.0f, ImGui::GetContentRegionAvail().x - inputWidth - spacing);

    ImGui::SetNextItemWidth(comboWidth);

    if (ImGui::BeginCombo(comboId.c_str(), preview.c_str()))
    {
        const ImGuiID filterStorageId = ImGui::GetID((comboId + "/filter").c_str());
        static std::unordered_map<ImGuiID, std::string> filters;
        std::string &filter = filters[filterStorageId];
        char filterBuffer[128] = {};
        std::snprintf(filterBuffer, sizeof(filterBuffer), "%s", filter.c_str());
        ImGui::SetNextItemWidth(-FLT_MIN);

        if (ImGui::InputText("##Filter", filterBuffer, sizeof(filterBuffer)))
        {
            filter = filterBuffer;
        }

        const std::string normalizedFilter = toLowerCopy(filter);
        const bool zeroSelected = selectedValue == 0;

        if ((normalizedFilter.empty() || std::string("<none>").find(normalizedFilter) != std::string::npos)
            && ImGui::Selectable("<none>", zeroSelected))
        {
            if (value != 0)
            {
                session.captureUndoSnapshot();
                value = 0;
                changed = true;
            }
        }

        if (zeroSelected)
        {
            ImGui::SetItemDefaultFocus();
        }

        for (const EditorIdLabelOption &option : options)
        {
            if (!optionMatchesFilter(option, normalizedFilter))
            {
                continue;
            }

            const bool selected = option.id == selectedValue;

            if (ImGui::Selectable(option.label.c_str(), selected))
            {
                if (option.id != value)
                {
                    session.captureUndoSnapshot();
                    value = static_cast<uint16_t>(option.id);
                    changed = true;
                }
            }

            if (selected)
            {
                ImGui::SetItemDefaultFocus();
            }
        }

        ImGui::EndCombo();
    }

    ImGui::SameLine();

    int editedValue = value;
    ImGui::SetNextItemWidth(inputWidth);

    if (ImGui::InputInt((inspectorFieldId(pLabel) + "/raw").c_str(), &editedValue))
    {
        editedValue = std::clamp(editedValue, 0, 65535);

        if (editedValue != value)
        {
            session.captureUndoSnapshot();
            value = static_cast<uint16_t>(editedValue);
            changed = true;
        }
    }

    return changed;
}

void renderResolvedMapEventField(EditorSession &session, const char *pLabel, uint16_t eventId)
{
    const std::optional<std::string> description = session.describeMapEvent(eventId);

    if (description)
    {
        renderInspectorReadOnlyField(pLabel, *description);
        return;
    }

    renderInspectorReadOnlyField(pLabel, eventId == 0 ? "<none>" : "<unresolved>");
}

bool editInt16Field(EditorSession &session, const char *pLabel, int16_t &value)
{
    int editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt(inspectorFieldId(pLabel).c_str(), &editedValue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, -32768, 32767);

    if (editedValue == value)
    {
        return false;
    }

    session.captureUndoSnapshot();
    value = static_cast<int16_t>(editedValue);
    return true;
}

bool editTransientInt16Field(const char *pLabel, int16_t &value)
{
    int editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt(inspectorFieldId(pLabel).c_str(), &editedValue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, -32768, 32767);

    if (editedValue == value)
    {
        return false;
    }

    value = static_cast<int16_t>(editedValue);
    return true;
}

bool editUInt32Field(EditorSession &session, const char *pLabel, uint32_t &value)
{
    uint32_t editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputScalar(inspectorFieldId(pLabel).c_str(), ImGuiDataType_U32, &editedValue))
    {
        return false;
    }

    if (editedValue == value)
    {
        return false;
    }

    session.captureUndoSnapshot();
    value = editedValue;
    return true;
}

bool editTransientUInt32Field(const char *pLabel, uint32_t &value)
{
    uint32_t editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputScalar(inspectorFieldId(pLabel).c_str(), ImGuiDataType_U32, &editedValue))
    {
        return false;
    }

    if (editedValue == value)
    {
        return false;
    }

    value = editedValue;
    return true;
}

bool editFloatField(EditorSession &session, const char *pLabel, float &value, float step = 1.0f)
{
    float editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputFloat(inspectorFieldId(pLabel).c_str(), &editedValue, step, step * 10.0f, "%.2f"))
    {
        return false;
    }

    if (std::fabs(editedValue - value) <= 0.0001f)
    {
        return false;
    }

    session.captureUndoSnapshot();
    value = editedValue;
    return true;
}

bool editBufferedIntField(
    EditorSession &session,
    const char *pLabel,
    int &value,
    int minimum,
    int maximum)
{
    int editedValue = value;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt(
            inspectorFieldId(pLabel).c_str(),
            &editedValue,
            1,
            100,
            ImGuiInputTextFlags_EnterReturnsTrue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, minimum, maximum);

    if (editedValue == value)
    {
        return false;
    }

    session.captureUndoSnapshot();
    value = editedValue;
    return true;
}

int32_t readChestRecordId(const Game::MapDeltaChest &chest, size_t recordIndex)
{
    if ((recordIndex + 1) * ChestItemRecordSize > chest.rawItems.size())
    {
        return 0;
    }

    int32_t rawItemId = 0;
    std::memcpy(&rawItemId, chest.rawItems.data() + recordIndex * ChestItemRecordSize, sizeof(rawItemId));
    return rawItemId;
}

void writeChestRecordId(Game::MapDeltaChest &chest, size_t recordIndex, int32_t rawItemId)
{
    if (chest.rawItems.size() < ChestItemRecordCount * ChestItemRecordSize)
    {
        chest.rawItems.resize(ChestItemRecordCount * ChestItemRecordSize, 0);
    }

    std::memcpy(chest.rawItems.data() + recordIndex * ChestItemRecordSize, &rawItemId, sizeof(rawItemId));
}

void clearChestRecord(Game::MapDeltaChest &chest, size_t recordIndex)
{
    if ((recordIndex + 1) * ChestItemRecordSize > chest.rawItems.size())
    {
        return;
    }

    std::fill(
        chest.rawItems.begin() + static_cast<ptrdiff_t>(recordIndex * ChestItemRecordSize),
        chest.rawItems.begin() + static_cast<ptrdiff_t>((recordIndex + 1) * ChestItemRecordSize),
        0);

    for (int16_t &cellValue : chest.inventoryMatrix)
    {
        if (cellValue == static_cast<int16_t>(recordIndex + 1))
        {
            cellValue = 0;
        }
    }
}

std::optional<size_t> findFirstEmptyChestRecord(const Game::MapDeltaChest &chest)
{
    for (size_t recordIndex = 0; recordIndex < ChestItemRecordCount; ++recordIndex)
    {
        if (readChestRecordId(chest, recordIndex) == 0)
        {
            return recordIndex;
        }
    }

    return std::nullopt;
}

bool editPositionField(EditorSession &session, const char *pLabel, int &x, int &y, int &z)
{
    std::array<int, 3> values = {x, y, z};

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt3(inspectorFieldId(pLabel).c_str(), values.data()))
    {
        return false;
    }

    if (values[0] == x && values[1] == y && values[2] == z)
    {
        return false;
    }

    session.captureUndoSnapshot();
    x = values[0];
    y = values[1];
    z = values[2];
    return true;
}

void recomputeBModelMetadata(Game::OutdoorBModel &bmodel)
{
    if (bmodel.vertices.empty())
    {
        bmodel.positionX = 0;
        bmodel.positionY = 0;
        bmodel.positionZ = 0;
        bmodel.minX = 0;
        bmodel.minY = 0;
        bmodel.minZ = 0;
        bmodel.maxX = 0;
        bmodel.maxY = 0;
        bmodel.maxZ = 0;
        bmodel.boundingCenterX = 0;
        bmodel.boundingCenterY = 0;
        bmodel.boundingCenterZ = 0;
        bmodel.boundingRadius = 0;
        return;
    }

    float minX = std::numeric_limits<float>::max();
    float minY = std::numeric_limits<float>::max();
    float minZ = std::numeric_limits<float>::max();
    float maxX = std::numeric_limits<float>::lowest();
    float maxY = std::numeric_limits<float>::lowest();
    float maxZ = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        minX = std::min(minX, static_cast<float>(vertex.x));
        minY = std::min(minY, static_cast<float>(vertex.y));
        minZ = std::min(minZ, static_cast<float>(vertex.z));
        maxX = std::max(maxX, static_cast<float>(vertex.x));
        maxY = std::max(maxY, static_cast<float>(vertex.y));
        maxZ = std::max(maxZ, static_cast<float>(vertex.z));
    }

    const float centerX = (minX + maxX) * 0.5f;
    const float centerY = (minY + maxY) * 0.5f;
    const float centerZ = (minZ + maxZ) * 0.5f;
    float maxRadiusSquared = 0.0f;

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        const float deltaX = static_cast<float>(vertex.x) - centerX;
        const float deltaY = static_cast<float>(vertex.y) - centerY;
        const float deltaZ = static_cast<float>(vertex.z) - centerZ;
        maxRadiusSquared = std::max(maxRadiusSquared, deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
    }

    bmodel.positionX = static_cast<int>(std::lround(centerX));
    bmodel.positionY = static_cast<int>(std::lround(centerY));
    bmodel.positionZ = static_cast<int>(std::lround(centerZ));
    bmodel.minX = static_cast<int>(std::floor(minX));
    bmodel.minY = static_cast<int>(std::floor(minY));
    bmodel.minZ = static_cast<int>(std::floor(minZ));
    bmodel.maxX = static_cast<int>(std::ceil(maxX));
    bmodel.maxY = static_cast<int>(std::ceil(maxY));
    bmodel.maxZ = static_cast<int>(std::ceil(maxZ));
    bmodel.boundingCenterX = static_cast<int>(std::lround(centerX));
    bmodel.boundingCenterY = static_cast<int>(std::lround(centerY));
    bmodel.boundingCenterZ = static_cast<int>(std::lround(centerZ));
    bmodel.boundingRadius = static_cast<int>(std::ceil(std::sqrt(maxRadiusSquared)));
}

bool editInt16PositionField(EditorSession &session, const char *pLabel, int16_t &x, int16_t &y, int16_t &z)
{
    std::array<int, 3> values = {x, y, z};

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt3(inspectorFieldId(pLabel).c_str(), values.data()))
    {
        return false;
    }

    values[0] = std::clamp(values[0], -32768, 32767);
    values[1] = std::clamp(values[1], -32768, 32767);
    values[2] = std::clamp(values[2], -32768, 32767);

    if (values[0] == x && values[1] == y && values[2] == z)
    {
        return false;
    }

    session.captureUndoSnapshot();
    x = static_cast<int16_t>(values[0]);
    y = static_cast<int16_t>(values[1]);
    z = static_cast<int16_t>(values[2]);
    return true;
}

bool editLookupIndicesField(EditorSession &session, const char *pLabel, std::array<uint16_t, 4> &values)
{
    std::array<int, 4> editedValues = {
        static_cast<int>(values[0]),
        static_cast<int>(values[1]),
        static_cast<int>(values[2]),
        static_cast<int>(values[3])
    };

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt4(inspectorFieldId(pLabel).c_str(), editedValues.data()))
    {
        return false;
    }

    bool changed = false;

    for (size_t index = 0; index < editedValues.size(); ++index)
    {
        const int clampedValue = std::clamp(editedValues[index], 0, 65535);

        if (clampedValue != values[index])
        {
            values[index] = static_cast<uint16_t>(clampedValue);
            changed = true;
        }
    }

    if (changed)
    {
        session.captureUndoSnapshot();
    }

    return changed;
}

bool editStringOptionField(
    EditorSession &session,
    const char *pLabel,
    std::string &value,
    const std::vector<std::string> &options)
{
    beginInspectorFieldRow(pLabel);

    const std::string comboId = inspectorFieldId(pLabel);
    const char *pPreview = value.empty() ? "<none>" : value.c_str();

    if (!ImGui::BeginCombo(comboId.c_str(), pPreview))
    {
        return false;
    }

    const ImGuiID filterStorageId = ImGui::GetID((comboId + "/filter").c_str());
    static std::unordered_map<ImGuiID, std::string> filters;
    std::string &filter = filters[filterStorageId];
    char filterBuffer[128] = {};
    std::snprintf(filterBuffer, sizeof(filterBuffer), "%s", filter.c_str());
    ImGui::SetNextItemWidth(-FLT_MIN);

    if (ImGui::InputText("##Filter", filterBuffer, sizeof(filterBuffer)))
    {
        filter = filterBuffer;
    }

    const std::string normalizedFilter = toLowerCopy(filter);
    bool changed = false;

    if ((normalizedFilter.empty() || std::string("<none>").find(normalizedFilter) != std::string::npos)
        && ImGui::Selectable("<none>", value.empty()))
    {
        if (!value.empty())
        {
            session.captureUndoSnapshot();
            value.clear();
            changed = true;
        }
    }

    for (const std::string &option : options)
    {
        if (!normalizedFilter.empty() && toLowerCopy(option).find(normalizedFilter) == std::string::npos)
        {
            continue;
        }

        const bool selected = option == value;

        if (ImGui::Selectable(option.c_str(), selected))
        {
            if (option != value)
            {
                session.captureUndoSnapshot();
                value = option;
                changed = true;
            }
        }

        if (selected)
        {
            ImGui::SetItemDefaultFocus();
        }
    }

    ImGui::EndCombo();
    return changed;
}

bool editBitCheckbox(EditorSession &session, const char *pLabel, int32_t &bitField, int32_t bitMask)
{
    bool enabled = (bitField & bitMask) != 0;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::Checkbox(inspectorFieldId(pLabel).c_str(), &enabled))
    {
        return false;
    }

    session.captureUndoSnapshot();

    if (enabled)
    {
        bitField |= bitMask;
    }
    else
    {
        bitField &= ~bitMask;
    }

    return true;
}

bool editBitCheckbox(EditorSession &session, const char *pLabel, uint32_t &bitField, uint32_t bitMask)
{
    bool enabled = (bitField & bitMask) != 0;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::Checkbox(inspectorFieldId(pLabel).c_str(), &enabled))
    {
        return false;
    }

    session.captureUndoSnapshot();

    if (enabled)
    {
        bitField |= bitMask;
    }
    else
    {
        bitField &= ~bitMask;
    }

    return true;
}

bool editBitCheckbox(EditorSession &session, const char *pLabel, uint8_t &bitField, uint8_t bitMask)
{
    bool enabled = (bitField & bitMask) != 0;
    beginInspectorFieldRow(pLabel);

    if (!ImGui::Checkbox(inspectorFieldId(pLabel).c_str(), &enabled))
    {
        return false;
    }

    session.captureUndoSnapshot();

    if (enabled)
    {
        bitField = static_cast<uint8_t>(bitField | bitMask);
    }
    else
    {
        bitField = static_cast<uint8_t>(bitField & ~bitMask);
    }

    return true;
}

bool editBitCheckbox(EditorSession &session, const char *pLabel, uint16_t &bitField, uint16_t bitMask)
{
    bool enabled = (bitField & bitMask) != 0;

    beginInspectorFieldRow(pLabel);

    if (!ImGui::Checkbox(inspectorFieldId(pLabel).c_str(), &enabled))
    {
        return false;
    }

    session.captureUndoSnapshot();

    if (enabled)
    {
        bitField |= bitMask;
    }
    else
    {
        bitField &= ~bitMask;
    }

    return true;
}

bool editActorHostilityTypeField(EditorSession &session, uint8_t &hostilityType)
{
    int editedValue = hostilityType;

    beginInspectorFieldRow("Hostility Type");

    if (!ImGui::InputInt("##Hostility Type", &editedValue))
    {
        return false;
    }

    editedValue = std::clamp(editedValue, 0, 255);

    if (editedValue == hostilityType)
    {
        return false;
    }

    session.captureUndoSnapshot();
    hostilityType = static_cast<uint8_t>(editedValue);
    return true;
}

void applyMonsterTemplateSelection(EditorSession &session, Game::MapDeltaActor &actor, int16_t previousMonsterInfoId);

bool editMonsterTemplateField(EditorSession &session, Game::MapDeltaActor &actor)
{
    const int16_t previousMonsterInfoId = actor.monsterInfoId;
    uint32_t selectedId = actor.monsterInfoId > 0 ? static_cast<uint32_t>(actor.monsterInfoId) : 0;

    if (!editOptionField(
            session,
            "Monster Template",
            selectedId,
            session.monsterOptions(),
            "<none>",
            "Monster Template"))
    {
        return false;
    }

    actor.monsterInfoId = static_cast<int16_t>(std::min<uint32_t>(selectedId, 32767));
    applyMonsterTemplateSelection(session, actor, previousMonsterInfoId);
    return true;
}

void applyMonsterTemplateSelection(EditorSession &session, Game::MapDeltaActor &actor, int16_t previousMonsterInfoId)
{
    const Game::MonsterTable &monsterTable = session.monsterTable();

    if (actor.monsterId <= 0 || actor.monsterId == previousMonsterInfoId)
    {
        actor.monsterId = actor.monsterInfoId;
    }

    const Game::MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(actor.monsterInfoId);
    const Game::MonsterEntry *pMonsterEntry = monsterTable.findById(actor.monsterId);

    if (pStats != nullptr)
    {
        actor.hp = static_cast<int16_t>(std::clamp(pStats->hitPoints, 0, 32767));
        actor.hostilityType = static_cast<uint8_t>(std::clamp(pStats->hostility, 0, 255));
    }
    else
    {
        actor.hp = 0;
        actor.hostilityType = 0;
    }

    if (pMonsterEntry != nullptr)
    {
        actor.radius = pMonsterEntry->radius;
        actor.height = pMonsterEntry->height;
        actor.moveSpeed = pMonsterEntry->movementSpeed;
    }
    else
    {
        actor.radius = 0;
        actor.height = 0;
        actor.moveSpeed = 0;
    }

    actor.spriteIds = {};
}

bool editTransientMonsterTemplateField(EditorSession &session, Game::MapDeltaActor &actor)
{
    const int16_t previousMonsterInfoId = actor.monsterInfoId;
    uint32_t selectedId = actor.monsterInfoId > 0 ? static_cast<uint32_t>(actor.monsterInfoId) : 0;

    if (!editTransientOptionField(
            "Monster Template",
            selectedId,
            session.monsterOptions(),
            "<none>",
            "Monster Template"))
    {
        return false;
    }

    actor.monsterInfoId = static_cast<int16_t>(std::min<uint32_t>(selectedId, 32767));
    applyMonsterTemplateSelection(session, actor, previousMonsterInfoId);
    return true;
}

bool editObjectDescriptionField(EditorSession &session, uint16_t &objectDescriptionId)
{
    uint32_t selectedId = objectDescriptionId;

    if (!editOptionField(
            session,
            "Object Description",
            selectedId,
            session.objectOptions(),
            nullptr,
            "Object"))
    {
        return false;
    }

    objectDescriptionId = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));
    return true;
}

bool editDecorationField(EditorSession &session, uint16_t &decorationListId)
{
    uint32_t selectedId = decorationListId;

    if (!editOptionField(
            session,
            "Decoration",
            selectedId,
            session.decorationOptions(),
            nullptr,
            "Decoration"))
    {
        return false;
    }

    decorationListId = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));
    return true;
}

bool editChestPictureField(EditorSession &session, uint16_t &chestTypeId)
{
    uint32_t selectedId = chestTypeId;

    if (!editOptionField(
            session,
            "Chest Picture",
            selectedId,
            session.chestOptions(),
            nullptr,
            "Chest"))
    {
        return false;
    }

    chestTypeId = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));
    return true;
}

bool editFixedItemSelectorField(EditorSession &session, const char *pLabel, int &itemId)
{
    uint32_t selectedId = itemId > 0 ? static_cast<uint32_t>(itemId) : 0;

    if (!editOptionField(
            session,
            pLabel,
            selectedId,
            session.itemOptions(),
            "<none>",
            "Item"))
    {
        return false;
    }

    itemId = static_cast<int>(selectedId);
    return true;
}

const Game::MapEncounterInfo *spawnEncounterInfo(const Game::MapStatsEntry &mapEntry, int encounterSlot)
{
    if (encounterSlot == 1)
    {
        return &mapEntry.encounter1;
    }

    if (encounterSlot == 2)
    {
        return &mapEntry.encounter2;
    }

    if (encounterSlot == 3)
    {
        return &mapEntry.encounter3;
    }

    return nullptr;
}

std::vector<EditorIdLabelOption> buildActorSpawnIndexOptions(const Game::MapStatsEntry &mapEntry)
{
    std::vector<EditorIdLabelOption> options;
    options.reserve(12);

    for (int encounterSlot = 1; encounterSlot <= 3; ++encounterSlot)
    {
        const Game::MapEncounterInfo *pEncounter = spawnEncounterInfo(mapEntry, encounterSlot);

        if (pEncounter == nullptr)
        {
            continue;
        }

        EditorIdLabelOption option = {};
        option.id = static_cast<uint32_t>(encounterSlot);
        option.label = "Encounter " + std::to_string(encounterSlot) + " Random";

        if (!pEncounter->monsterName.empty())
        {
            option.label += " - " + pEncounter->monsterName;
        }

        option.label += " (#" + std::to_string(option.id) + ")";
        options.push_back(std::move(option));
    }

    for (int encounterSlot = 1; encounterSlot <= 3; ++encounterSlot)
    {
        const Game::MapEncounterInfo *pEncounter = spawnEncounterInfo(mapEntry, encounterSlot);

        if (pEncounter == nullptr)
        {
            continue;
        }

        for (int tierIndex = 0; tierIndex < 3; ++tierIndex)
        {
            EditorIdLabelOption option = {};
            option.id = static_cast<uint32_t>(4 + (tierIndex * 3) + (encounterSlot - 1));
            const char tierSuffix = static_cast<char>('A' + tierIndex);
            option.label = "Encounter " + std::to_string(encounterSlot) + " Tier " + std::string(1, tierSuffix);

            if (!pEncounter->monsterName.empty())
            {
                option.label += " - " + pEncounter->monsterName;
            }

            option.label += " (#" + std::to_string(option.id) + ")";
            options.push_back(std::move(option));
        }
    }

    return options;
}

bool editSpawnTypeField(EditorSession &session, Game::OutdoorSpawn &spawn)
{
    beginInspectorFieldRow("Spawn Type");

    int selectedKind = 2;

    if (spawn.typeId == 3)
    {
        selectedKind = 0;
    }
    else if (spawn.typeId == 2)
    {
        selectedKind = 1;
    }

    static const char *Kinds[] = {"Actor Encounter", "Sprite / Item", "Legacy Raw"};

    if (!ImGui::Combo("##SpawnType", &selectedKind, Kinds, IM_ARRAYSIZE(Kinds)))
    {
        return false;
    }

    session.captureUndoSnapshot();

    if (selectedKind == 0)
    {
        spawn.typeId = 3;

        if (spawn.index == 0)
        {
            spawn.index = 1;
        }
    }
    else if (selectedKind == 1)
    {
        spawn.typeId = 2;
    }

    return true;
}

bool editTransientSpawnTypeField(Game::OutdoorSpawn &spawn)
{
    beginInspectorFieldRow("Spawn Type");

    int selectedKind = 2;

    if (spawn.typeId == 3)
    {
        selectedKind = 0;
    }
    else if (spawn.typeId == 2)
    {
        selectedKind = 1;
    }

    static const char *Kinds[] = {"Actor Encounter", "Sprite / Item", "Legacy Raw"};

    if (!ImGui::Combo("##SpawnType", &selectedKind, Kinds, IM_ARRAYSIZE(Kinds)))
    {
        return false;
    }

    if (selectedKind == 0)
    {
        spawn.typeId = 3;

        if (spawn.index == 0)
        {
            spawn.index = 1;
        }
    }
    else if (selectedKind == 1)
    {
        spawn.typeId = 2;
    }

    return true;
}

bool editActorSpawnEncounterField(
    EditorSession &session,
    const Game::MapStatsEntry &mapEntry,
    Game::OutdoorSpawn &spawn)
{
    std::vector<EditorIdLabelOption> options = buildActorSpawnIndexOptions(mapEntry);
    uint32_t selectedId = spawn.index;

    if (!editOptionField(
            session,
            "Encounter",
            selectedId,
            options,
            nullptr,
            "Encounter"))
    {
        return false;
    }

    spawn.typeId = 3;
    spawn.index = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));
    return true;
}

bool editTransientActorSpawnEncounterField(
    const Game::MapStatsEntry &mapEntry,
    Game::OutdoorSpawn &spawn)
{
    std::vector<EditorIdLabelOption> options = buildActorSpawnIndexOptions(mapEntry);
    uint32_t selectedId = spawn.index;

    if (!editTransientOptionField(
            "Encounter",
            selectedId,
            options,
            nullptr,
            "Encounter"))
    {
        return false;
    }

    spawn.typeId = 3;
    spawn.index = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));
    return true;
}

bool editUInt16Array4Field(EditorSession &session, const char *pLabel, std::array<uint16_t, 4> &values)
{
    std::array<int, 4> editedValues = {
        static_cast<int>(values[0]),
        static_cast<int>(values[1]),
        static_cast<int>(values[2]),
        static_cast<int>(values[3])
    };

    beginInspectorFieldRow(pLabel);

    if (!ImGui::InputInt4(inspectorFieldId(pLabel).c_str(), editedValues.data()))
    {
        return false;
    }

    bool changed = false;

    for (size_t index = 0; index < values.size(); ++index)
    {
        const uint16_t clampedValue = static_cast<uint16_t>(std::clamp(editedValues[index], 0, 65535));

        if (clampedValue != values[index])
        {
            values[index] = clampedValue;
            changed = true;
        }
    }

    if (changed)
    {
        session.captureUndoSnapshot();
    }

    return changed;
}

bool isObjectLifecycleKind(EditorSelectionKind kind)
{
    return kind == EditorSelectionKind::BModel
        || kind == EditorSelectionKind::Entity
        || kind == EditorSelectionKind::Spawn
        || kind == EditorSelectionKind::Actor
        || kind == EditorSelectionKind::SpriteObject;
}

size_t terrainCellFlatIndex(int x, int y)
{
    return static_cast<size_t>(y) * Game::OutdoorMapData::TerrainWidth + static_cast<size_t>(x);
}

bool decodeTerrainCellFlatIndex(size_t flatIndex, int &x, int &y)
{
    if (flatIndex >= static_cast<size_t>(Game::OutdoorMapData::TerrainWidth * Game::OutdoorMapData::TerrainHeight))
    {
        return false;
    }

    x = static_cast<int>(flatIndex % Game::OutdoorMapData::TerrainWidth);
    y = static_cast<int>(flatIndex / Game::OutdoorMapData::TerrainWidth);
    return true;
}

bool tryPickFlattenTargetFromSelectedTerrainCell(EditorSession &session)
{
    if (!session.hasDocument() || session.document().kind() != EditorDocument::Kind::Outdoor)
    {
        return false;
    }

    if (session.selection().kind != EditorSelectionKind::Terrain)
    {
        return false;
    }

    int cellX = 0;
    int cellY = 0;

    if (!decodeTerrainCellFlatIndex(session.selection().index, cellX, cellY))
    {
        return false;
    }

    const size_t sampleIndex = terrainCellFlatIndex(cellX, cellY);
    const Game::OutdoorMapData &outdoorGeometry = session.document().outdoorGeometry();

    if (sampleIndex >= outdoorGeometry.heightMap.size())
    {
        return false;
    }

    session.setTerrainFlattenTargetMode(EditorTerrainFlattenTargetMode::Sampled);
    session.setTerrainFlattenSampledTargetHeight(outdoorGeometry.heightMap[sampleIndex]);
    return true;
}

size_t flattenedOutdoorFaceIndex(const Game::OutdoorMapData &outdoorMapData, size_t bmodelIndex, size_t faceIndex)
{
    size_t flattenedIndex = 0;

    for (size_t index = 0; index < bmodelIndex && index < outdoorMapData.bmodels.size(); ++index)
    {
        flattenedIndex += outdoorMapData.bmodels[index].faces.size();
    }

    return flattenedIndex + faceIndex;
}

bool decodeFlattenedOutdoorFaceIndex(
    const Game::OutdoorMapData &outdoorMapData,
    size_t flattenedIndex,
    size_t &bmodelIndex,
    size_t &faceIndex)
{
    size_t runningIndex = 0;

    for (size_t currentBModelIndex = 0; currentBModelIndex < outdoorMapData.bmodels.size(); ++currentBModelIndex)
    {
        const size_t faceCount = outdoorMapData.bmodels[currentBModelIndex].faces.size();

        if (flattenedIndex < runningIndex + faceCount)
        {
            bmodelIndex = currentBModelIndex;
            faceIndex = flattenedIndex - runningIndex;
            return true;
        }

        runningIndex += faceCount;
    }

    return false;
}

Game::OutdoorSceneTerrainAttributeOverride *findTerrainOverride(
    Game::OutdoorSceneData &sceneData,
    int x,
    int y)
{
    for (Game::OutdoorSceneTerrainAttributeOverride &overrideEntry : sceneData.terrainAttributeOverrides)
    {
        if (overrideEntry.x == x && overrideEntry.y == y)
        {
            return &overrideEntry;
        }
    }

    return nullptr;
}

const Game::OutdoorSceneTerrainAttributeOverride *findTerrainOverride(
    const Game::OutdoorSceneData &sceneData,
    int x,
    int y)
{
    for (const Game::OutdoorSceneTerrainAttributeOverride &overrideEntry : sceneData.terrainAttributeOverrides)
    {
        if (overrideEntry.x == x && overrideEntry.y == y)
        {
            return &overrideEntry;
        }
    }

    return nullptr;
}

Game::OutdoorSceneInteractiveFace *findInteractiveFace(
    Game::OutdoorSceneData &sceneData,
    size_t bmodelIndex,
    size_t faceIndex)
{
    for (Game::OutdoorSceneInteractiveFace &interactiveFace : sceneData.interactiveFaces)
    {
        if (interactiveFace.bmodelIndex == bmodelIndex && interactiveFace.faceIndex == faceIndex)
        {
            return &interactiveFace;
        }
    }

    return nullptr;
}

const Game::OutdoorSceneInteractiveFace *findInteractiveFace(
    const Game::OutdoorSceneData &sceneData,
    size_t bmodelIndex,
    size_t faceIndex)
{
    for (const Game::OutdoorSceneInteractiveFace &interactiveFace : sceneData.interactiveFaces)
    {
        if (interactiveFace.bmodelIndex == bmodelIndex && interactiveFace.faceIndex == faceIndex)
        {
            return &interactiveFace;
        }
    }

    return nullptr;
}

}

void EditorMainWindow::render(
    EditorSession &session,
    uint32_t frameNumber,
    float deltaSeconds,
    const std::string &rendererName)
{
    ensureEditorStateLoaded(session);
    const ImGuiID dockspaceId = editorDockspaceId();
    ImGui::DockSpaceOverViewport(
        dockspaceId,
        ImGui::GetMainViewport(),
        ImGuiDockNodeFlags_PassthruCentralNode);
    ensureDefaultDockLayout();
    handleGlobalShortcuts(session);
    syncImportedModelPreview(session);

    renderMenuBar(session);
    ImGui::SetNextWindowDockID(dockspaceId, ImGuiCond_FirstUseEver);
    renderViewportPanel(session, deltaSeconds);
    renderToolbar(session);
    renderSceneOutliner(session);
    renderInspector(session);
    renderLogPanel(session, frameNumber, deltaSeconds, rendererName);
    renderNewOutdoorMapModal(session);
    renderOpenOutdoorMapModal(session);
    renderMapPackageActionModal(session);
    renderDeleteCurrentMapModal(session);
    renderModelImportModal(session);
    renderModelFileBrowserPopup(session);
    persistEditorStateIfNeeded(session);
}

void EditorMainWindow::syncImportedModelPreview(EditorSession &session)
{
    const bool importModalVisible =
        m_openImportNewBModelModal || m_showImportNewBModelWindow;

    if (importModalVisible)
    {
        const std::string sourcePath = trimCopy(m_globalBModelImportPath);

        if (!sourcePath.empty())
        {
            EditorOutdoorViewport::ImportedModelPreviewRequest request = {};
            request.sourcePath = sourcePath;
            request.sourceMeshName = canSplitImportedModelPathByMesh(sourcePath) ? m_globalBModelImportSelectedMeshName : "";
            request.importScale = m_globalBModelImportScale;
            request.mergeCoplanarFaces = m_globalBModelImportMergeCoplanarFaces;
            request.targetMode = EditorOutdoorViewport::ImportedModelPreviewRequest::TargetMode::NewImportPlacement;
            m_viewport.setImportedModelPreviewRequest(request);
            return;
        }
    }

    if (session.selection().kind == EditorSelectionKind::BModel)
    {
        const std::string sourcePath = trimCopy(m_bmodelImportPath);

        if (!sourcePath.empty())
        {
            EditorOutdoorViewport::ImportedModelPreviewRequest request = {};
            request.sourcePath = sourcePath;
            request.sourceMeshName = canSplitImportedModelPathByMesh(sourcePath) ? m_bmodelImportSelectedMeshName : "";
            request.importScale = m_bmodelImportScale;
            request.mergeCoplanarFaces = m_bmodelImportMergeCoplanarFaces;
            request.targetMode = EditorOutdoorViewport::ImportedModelPreviewRequest::TargetMode::ReplaceSelectedBModel;
            request.bmodelIndex = session.selection().index;
            m_viewport.setImportedModelPreviewRequest(request);
            return;
        }
    }

    m_viewport.setImportedModelPreviewRequest(std::nullopt);
}

void EditorMainWindow::handleGlobalShortcuts(EditorSession &session)
{
    const ImGuiIO &io = ImGui::GetIO();

    if (io.KeyCtrl && ImGui::IsKeyPressed(ImGuiKey_N, false))
    {
        openNewOutdoorMapModal(session);
    }

    if (io.KeyCtrl && ImGui::IsKeyPressed(ImGuiKey_O, false))
    {
        openOpenOutdoorMapModal();
    }

    if (!session.hasDocument())
    {
        return;
    }

    if (io.KeyCtrl && ImGui::IsKeyPressed(ImGuiKey_S, false))
    {
        std::string errorMessage;

        if (session.saveActiveDocument(errorMessage))
        {
            setStatusMessage(StatusMessageKind::Success, "Saved source.");
        }
        else
        {
            session.logError(errorMessage);
            setStatusMessage(StatusMessageKind::Error, errorMessage);
        }
    }

    if (io.KeyCtrl && ImGui::IsKeyPressed(ImGuiKey_B, false))
    {
        std::string errorMessage;

        if (session.buildActiveDocument(errorMessage))
        {
            setStatusMessage(StatusMessageKind::Success, "Built runtime ODM.");
        }
        else
        {
            session.logError(errorMessage);
            setStatusMessage(StatusMessageKind::Error, errorMessage);
        }
    }

    if (ImGui::IsKeyPressed(ImGuiKey_F5, false))
    {
        std::string errorMessage;

        if (playtestCurrentMap(session, errorMessage))
        {
            setStatusMessage(StatusMessageKind::Success, "Launched playtest.");
        }
        else
        {
            session.logError(errorMessage);
            setStatusMessage(StatusMessageKind::Error, errorMessage);
        }
    }
}

void EditorMainWindow::shutdown()
{
    if (m_shutdownComplete)
    {
        return;
    }

    m_shutdownComplete = true;
    destroyBitmapPreviewTextures();
    m_viewport.shutdown();
}

void EditorMainWindow::ensureEditorStateLoaded(EditorSession &session)
{
    if (m_editorStateLoaded)
    {
        return;
    }

    m_editorStateLoaded = true;
    std::ifstream input(editorStatePath());

    if (!input)
    {
        return;
    }

    std::unordered_map<std::string, std::string> values;
    std::string line;

    while (std::getline(input, line))
    {
        const size_t separator = line.find('=');

        if (separator == std::string::npos)
        {
            continue;
        }

        values[trimCopy(line.substr(0, separator))] = trimCopy(line.substr(separator + 1));
    }

    if (const auto iterator = values.find("placement_kind"); iterator != values.end())
    {
        const int rawKind = std::clamp(std::atoi(iterator->second.c_str()), 0, static_cast<int>(EditorSelectionKind::Chest));
        m_viewport.setPlacementKind(static_cast<EditorSelectionKind>(rawKind));
    }

    if (const auto iterator = values.find("transform_mode"); iterator != values.end())
    {
        const int rawMode = std::clamp(std::atoi(iterator->second.c_str()), 0, 1);
        m_viewport.setTransformGizmoMode(static_cast<EditorOutdoorViewport::TransformGizmoMode>(rawMode));
    }

    if (const auto iterator = values.find("transform_space"); iterator != values.end())
    {
        const int rawMode = std::clamp(std::atoi(iterator->second.c_str()), 0, 1);
        m_viewport.setTransformSpaceMode(static_cast<EditorOutdoorViewport::TransformSpaceMode>(rawMode));
    }

    if (const auto iterator = values.find("snap_enabled"); iterator != values.end())
    {
        m_viewport.setSnapEnabled(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("snap_step"); iterator != values.end())
    {
        m_viewport.setSnapStep(std::atoi(iterator->second.c_str()));
    }

    if (const auto iterator = values.find("show_terrain"); iterator != values.end())
    {
        m_viewport.setShowTerrainFill(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_terrain_grid"); iterator != values.end())
    {
        m_viewport.setShowTerrainGrid(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("preview_material_mode"); iterator != values.end())
    {
        const int rawMode = std::clamp(std::atoi(iterator->second.c_str()), 0, 2);
        m_viewport.setPreviewMaterialMode(static_cast<EditorOutdoorViewport::PreviewMaterialMode>(rawMode));
    }

    if (const auto iterator = values.find("preview_selected_only"); iterator != values.end())
    {
        m_viewport.setForcePreviewOnSelectedOnly(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_bmodels"); iterator != values.end())
    {
        m_viewport.setShowBModels(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_bmodel_wire"); iterator != values.end())
    {
        m_viewport.setShowBModelWireframe(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_entities"); iterator != values.end())
    {
        m_viewport.setShowEntities(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_entity_billboards"); iterator != values.end())
    {
        m_viewport.setShowEntityBillboards(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_spawns"); iterator != values.end())
    {
        m_viewport.setShowSpawns(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_actors"); iterator != values.end())
    {
        m_viewport.setShowActors(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_actor_billboards"); iterator != values.end())
    {
        m_viewport.setShowActorBillboards(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_objects"); iterator != values.end())
    {
        m_viewport.setShowSpriteObjects(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_spawn_actor_billboards"); iterator != values.end())
    {
        m_viewport.setShowSpawnActorBillboards(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_events"); iterator != values.end())
    {
        m_viewport.setShowEventMarkers(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("show_chest_links"); iterator != values.end())
    {
        m_viewport.setShowChestLinks(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("terrain_paint_enabled"); iterator != values.end())
    {
        session.setTerrainPaintEnabled(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("terrain_paint_tile"); iterator != values.end())
    {
        session.setTerrainPaintTileId(static_cast<uint8_t>(std::clamp(std::atoi(iterator->second.c_str()), 0, 255)));
    }

    if (const auto iterator = values.find("terrain_paint_mode"); iterator != values.end())
    {
        const int rawMode = std::clamp(std::atoi(iterator->second.c_str()), 0, 2);
        session.setTerrainPaintMode(static_cast<EditorTerrainPaintMode>(rawMode));
    }

    if (const auto iterator = values.find("terrain_paint_radius"); iterator != values.end())
    {
        session.setTerrainPaintRadius(std::atoi(iterator->second.c_str()));
    }

    if (const auto iterator = values.find("terrain_paint_edge_noise"); iterator != values.end())
    {
        session.setTerrainPaintEdgeNoise(std::atoi(iterator->second.c_str()));
    }

    if (const auto iterator = values.find("terrain_sculpt_enabled"); iterator != values.end())
    {
        session.setTerrainSculptEnabled(parseBoolValue(iterator->second));
    }

    if (const auto iterator = values.find("terrain_sculpt_mode"); iterator != values.end())
    {
        const int rawMode = std::clamp(std::atoi(iterator->second.c_str()), 0, 5);
        session.setTerrainSculptMode(static_cast<EditorTerrainSculptMode>(rawMode));
    }
    else if (const auto iterator = values.find("terrain_sculpt_lower"); iterator != values.end())
    {
        session.setTerrainSculptMode(
            parseBoolValue(iterator->second) ? EditorTerrainSculptMode::Lower : EditorTerrainSculptMode::Raise);
    }

    if (const auto iterator = values.find("terrain_sculpt_radius"); iterator != values.end())
    {
        session.setTerrainSculptRadius(std::atoi(iterator->second.c_str()));
    }

    if (const auto iterator = values.find("terrain_sculpt_strength"); iterator != values.end())
    {
        session.setTerrainSculptStrength(std::atoi(iterator->second.c_str()));
    }

    if (const auto iterator = values.find("terrain_sculpt_falloff"); iterator != values.end())
    {
        const int rawMode = std::clamp(std::atoi(iterator->second.c_str()), 0, 2);
        session.setTerrainSculptFalloffMode(static_cast<EditorTerrainFalloffMode>(rawMode));
    }

    if (const auto iterator = values.find("terrain_flatten_target_mode"); iterator != values.end())
    {
        const int rawMode = std::clamp(std::atoi(iterator->second.c_str()), 0, 1);
        session.setTerrainFlattenTargetMode(static_cast<EditorTerrainFlattenTargetMode>(rawMode));
    }

    if (const auto iterator = values.find("terrain_flatten_target_height"); iterator != values.end())
    {
        session.setTerrainFlattenTargetHeight(std::atoi(iterator->second.c_str()));
    }

    if (const auto iterator = values.find("terrain_flatten_sampled_valid"); iterator != values.end()
        && parseBoolValue(iterator->second))
    {
        session.setTerrainFlattenSampledTargetHeight(session.terrainFlattenTargetHeight());
    }

    if (const auto iterator = values.find("import_directory"); iterator != values.end())
    {
        m_modelBrowserDirectory = iterator->second;
    }
}

void EditorMainWindow::persistEditorStateIfNeeded(const EditorSession &session)
{
    std::ostringstream output;
    output << "placement_kind=" << static_cast<int>(m_viewport.placementKind()) << '\n';
    output << "transform_mode=" << static_cast<int>(m_viewport.transformGizmoMode()) << '\n';
    output << "transform_space=" << static_cast<int>(m_viewport.transformSpaceMode()) << '\n';
    output << "snap_enabled=" << (m_viewport.snapEnabled() ? 1 : 0) << '\n';
    output << "snap_step=" << m_viewport.snapStep() << '\n';
    output << "show_terrain=" << (m_viewport.showTerrainFill() ? 1 : 0) << '\n';
    output << "show_terrain_grid=" << (m_viewport.showTerrainGrid() ? 1 : 0) << '\n';
    output << "preview_material_mode=" << static_cast<int>(m_viewport.previewMaterialMode()) << '\n';
    output << "preview_selected_only=" << (m_viewport.forcePreviewOnSelectedOnly() ? 1 : 0) << '\n';
    output << "show_bmodels=" << (m_viewport.showBModels() ? 1 : 0) << '\n';
    output << "show_bmodel_wire=" << (m_viewport.showBModelWireframe() ? 1 : 0) << '\n';
    output << "show_entities=" << (m_viewport.showEntities() ? 1 : 0) << '\n';
    output << "show_entity_billboards=" << (m_viewport.showEntityBillboards() ? 1 : 0) << '\n';
    output << "show_spawns=" << (m_viewport.showSpawns() ? 1 : 0) << '\n';
    output << "show_actors=" << (m_viewport.showActors() ? 1 : 0) << '\n';
    output << "show_actor_billboards=" << (m_viewport.showActorBillboards() ? 1 : 0) << '\n';
    output << "show_objects=" << (m_viewport.showSpriteObjects() ? 1 : 0) << '\n';
    output << "show_spawn_actor_billboards=" << (m_viewport.showSpawnActorBillboards() ? 1 : 0) << '\n';
    output << "show_events=" << (m_viewport.showEventMarkers() ? 1 : 0) << '\n';
    output << "show_chest_links=" << (m_viewport.showChestLinks() ? 1 : 0) << '\n';
    output << "terrain_paint_enabled=" << (session.terrainPaintEnabled() ? 1 : 0) << '\n';
    output << "terrain_paint_tile=" << static_cast<int>(session.terrainPaintTileId()) << '\n';
    output << "terrain_paint_mode=" << static_cast<int>(session.terrainPaintMode()) << '\n';
    output << "terrain_paint_radius=" << session.terrainPaintRadius() << '\n';
    output << "terrain_paint_edge_noise=" << session.terrainPaintEdgeNoise() << '\n';
    output << "terrain_sculpt_enabled=" << (session.terrainSculptEnabled() ? 1 : 0) << '\n';
    output << "terrain_sculpt_mode=" << static_cast<int>(session.terrainSculptMode()) << '\n';
    output << "terrain_sculpt_radius=" << session.terrainSculptRadius() << '\n';
    output << "terrain_sculpt_strength=" << session.terrainSculptStrength() << '\n';
    output << "terrain_sculpt_falloff=" << static_cast<int>(session.terrainSculptFalloffMode()) << '\n';
    output << "terrain_flatten_target_mode=" << static_cast<int>(session.terrainFlattenTargetMode()) << '\n';
    output << "terrain_flatten_target_height=" << session.terrainFlattenTargetHeight() << '\n';
    output << "terrain_flatten_sampled_valid=" << (session.hasTerrainFlattenSampledTarget() ? 1 : 0) << '\n';
    output << "import_directory=" << m_modelBrowserDirectory.generic_string() << '\n';
    const std::string serialized = output.str();

    if (serialized == m_lastSavedEditorState)
    {
        return;
    }

    std::ofstream file(editorStatePath(), std::ios::binary | std::ios::trunc);

    if (!file)
    {
        return;
    }

    file << serialized;
    m_lastSavedEditorState = serialized;
}

int EditorMainWindow::viewportX() const
{
    return m_viewportX;
}

int EditorMainWindow::viewportY() const
{
    return m_viewportY;
}

uint16_t EditorMainWindow::viewportWidth() const
{
    return m_viewportWidth;
}

uint16_t EditorMainWindow::viewportHeight() const
{
    return m_viewportHeight;
}

void EditorMainWindow::ensureDefaultDockLayout()
{
    if (m_dockLayoutInitialized)
    {
        return;
    }

    const ImGuiViewport *pViewport = ImGui::GetMainViewport();
    const ImGuiID dockspaceId = editorDockspaceId();
    ImGui::DockBuilderRemoveNode(dockspaceId);
    ImGui::DockBuilderAddNode(dockspaceId, ImGuiDockNodeFlags_DockSpace);
    ImGui::DockBuilderSetNodeSize(dockspaceId, pViewport->WorkSize);

    ImGuiID leftNode = 0;
    ImGuiID rightNode = 0;
    ImGuiID bottomNode = 0;
    ImGuiID topNode = 0;
    ImGuiID centerNode = dockspaceId;

    ImGui::DockBuilderSplitNode(centerNode, ImGuiDir_Up, 0.10f, &topNode, &centerNode);
    ImGui::DockBuilderSplitNode(centerNode, ImGuiDir_Left, 0.18f, &leftNode, &centerNode);
    ImGui::DockBuilderSplitNode(centerNode, ImGuiDir_Right, 0.24f, &rightNode, &centerNode);
    ImGui::DockBuilderSplitNode(centerNode, ImGuiDir_Down, 0.23f, &bottomNode, &centerNode);

    ImGui::DockBuilderDockWindow("Tools", topNode);
    ImGui::DockBuilderDockWindow("Scene", leftNode);
    ImGui::DockBuilderDockWindow("Inspector", rightNode);
    ImGui::DockBuilderDockWindow("Viewport", centerNode);
    ImGui::DockBuilderDockWindow("Log", bottomNode);
    ImGui::DockBuilderFinish(dockspaceId);
    m_dockLayoutInitialized = true;
}

void EditorMainWindow::renderMenuBar(EditorSession &session)
{
    if (!ImGui::BeginMainMenuBar())
    {
        return;
    }

    if (ImGui::BeginMenu("File"))
    {
        if (ImGui::MenuItem("New Outdoor Map...", "Ctrl+N"))
        {
            openNewOutdoorMapModal(session);
        }
        if (ImGui::MenuItem("Open...", "Ctrl+O"))
        {
            openOpenOutdoorMapModal();
        }
        if (ImGui::MenuItem("Save Current Map As...", nullptr, false, session.hasDocument()))
        {
            openMapPackageActionModal(session, MapPackageAction::SaveAs);
        }
        if (ImGui::MenuItem("Duplicate Current Map...", nullptr, false, session.hasDocument()))
        {
            openMapPackageActionModal(session, MapPackageAction::Duplicate);
        }
        if (ImGui::MenuItem("Save Source", "Ctrl+S", false, session.hasDocument()))
        {
            std::string errorMessage;

            if (session.saveActiveDocument(errorMessage))
            {
                setStatusMessage(StatusMessageKind::Success, "Saved source.");
            }
            else
            {
                session.logError(errorMessage);
                setStatusMessage(StatusMessageKind::Error, errorMessage);
            }
        }
        if (ImGui::MenuItem("Delete Current Map...", nullptr, false, session.hasDocument()))
        {
            openDeleteCurrentMapModal();
        }
        ImGui::MenuItem("Save All", "Ctrl+Shift+S", false, false);
        ImGui::Separator();
        ImGui::MenuItem("Quit", "Ctrl+Q", false, false);
        ImGui::EndMenu();
    }

    if (ImGui::BeginMenu("Build"))
    {
        if (ImGui::MenuItem("Build Current Map", "Ctrl+B", false, session.hasDocument()))
        {
            std::string errorMessage;

            if (session.buildActiveDocument(errorMessage))
            {
                setStatusMessage(StatusMessageKind::Success, "Built runtime ODM.");
            }
            else
            {
                session.logError(errorMessage);
                setStatusMessage(StatusMessageKind::Error, errorMessage);
            }
        }

        ImGui::Separator();
        ImGui::MenuItem("Validate Scene", nullptr, false, false);
        if (ImGui::MenuItem("Playtest Current Map", "F5", false, session.hasDocument()))
        {
            std::string errorMessage;

            if (playtestCurrentMap(session, errorMessage))
            {
                setStatusMessage(StatusMessageKind::Success, "Launched playtest.");
            }
            else
            {
                session.logError(errorMessage);
                setStatusMessage(StatusMessageKind::Error, errorMessage);
            }
        }
        ImGui::EndMenu();
    }

    if (ImGui::BeginMenu("Edit"))
    {
        if (ImGui::MenuItem("Undo", "Ctrl+Z", false, session.canUndo()))
        {
            std::string errorMessage;

            if (!session.undo(errorMessage))
            {
                session.logError(errorMessage);
            }
        }

        if (ImGui::MenuItem("Redo", "Ctrl+Shift+Z", false, session.canRedo()))
        {
            std::string errorMessage;

            if (!session.redo(errorMessage))
            {
                session.logError(errorMessage);
            }
        }

        ImGui::EndMenu();
    }

    if (ImGui::BeginMenu("View"))
    {
        ImGui::MenuItem("Scene", nullptr, true, false);
        ImGui::MenuItem("Inspector", nullptr, true, false);
        ImGui::MenuItem("Log", nullptr, true, false);
        ImGui::EndMenu();
    }

    ImGui::EndMainMenuBar();
}

void EditorMainWindow::renderToolbar(EditorSession &session)
{
    ImGui::SetNextWindowDockID(editorDockspaceId(), ImGuiCond_FirstUseEver);

    const ImGuiWindowFlags windowFlags = ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_NoScrollbar |
        ImGuiWindowFlags_NoScrollWithMouse;

    if (!ImGui::Begin("Tools", nullptr, windowFlags))
    {
        ImGui::End();
        return;
    }

    ImGui::PushStyleVar(ImGuiStyleVar_FramePadding, ImVec2(6.0f, 1.0f));
    ImGui::PushStyleVar(ImGuiStyleVar_ItemSpacing, ImVec2(4.0f, 2.0f));
    const ImGuiStyle &style = ImGui::GetStyle();
    const float iconSize = 14.0f;
    const float iconTextSpacing = 6.0f;
    const float iconPillPadding = style.FramePadding.x + 2.0f;
    const float cardInnerPadding = 12.0f;
    const float columnSpacing = 10.0f;
    const auto iconPillWidth = [&](const char *pLabel)
    {
        return iconPillPadding * 2.0f + iconSize + iconTextSpacing + ImGui::CalcTextSize(pLabel).x;
    };
    const auto textPillWidth = [&](const char *pLabel)
    {
        return style.FramePadding.x * 2.0f + ImGui::CalcTextSize(pLabel).x;
    };
    const auto rowWidth = [&](std::initializer_list<float> widths)
    {
        float width = 0.0f;
        bool first = true;

        for (float value : widths)
        {
            if (!first)
            {
                width += style.ItemSpacing.x;
            }

            width += value;
            first = false;
        }

        return width;
    };
    const float modeCreateWidth = std::max(
        rowWidth({iconPillWidth("Select"), iconPillWidth("Terrain"), iconPillWidth("Face")}),
        std::max(
            rowWidth({iconPillWidth("Entity"), iconPillWidth("Spawn"), iconPillWidth("Actor")}),
            rowWidth({
                iconPillWidth("Object"),
                iconPillWidth("Import BModel"),
                textPillWidth("Duplicate"),
                textPillWidth("Delete")
            }))) + cardInnerPadding;
    const float transformWidth = std::max(
        rowWidth({iconPillWidth("Move"), iconPillWidth("Rotate")}),
        std::max(
            rowWidth({iconPillWidth("World"), iconPillWidth("Local"), iconPillWidth("Snap")}),
            ImGui::CalcTextSize("Snap Step").x + style.ItemSpacing.x + 64.0f)) + cardInnerPadding;
    const float viewWidth = std::max(
        rowWidth({
            iconPillWidth("Terrain"),
            iconPillWidth("Grid"),
            iconPillWidth("Textured"),
            iconPillWidth("Clay"),
            iconPillWidth("Entities"),
            iconPillWidth("Actors"),
            iconPillWidth("Events")
        }),
        rowWidth({
            iconPillWidth("BModels"),
            iconPillWidth("Wire"),
            iconPillWidth("Grid Preview"),
            iconPillWidth("Selected"),
            iconPillWidth("Spawns"),
            iconPillWidth("Objects")
        })) + cardInnerPadding;

    renderToolbarStatus(session);
    ImGui::Separator();
    ImGui::BeginTable("ToolbarContextBands", 4, ImGuiTableFlags_SizingFixedFit);
    ImGui::TableSetupColumn("ModeCreate", ImGuiTableColumnFlags_WidthFixed, modeCreateWidth);
    ImGui::TableSetupColumn("Transform", ImGuiTableColumnFlags_WidthFixed, transformWidth);
    ImGui::TableSetupColumn("View", ImGuiTableColumnFlags_WidthFixed, viewWidth);
    ImGui::TableSetupColumn("Spacer", ImGuiTableColumnFlags_WidthStretch);
    ImGui::TableNextRow();

    ImGui::TableNextColumn();
    beginToolbarCard("Mode", modeCreateWidth);
    renderToolModeButtons(session);
    ImGui::Dummy(ImVec2(0.0f, 1.0f));
    renderToolbarSubLabel("Create");
    renderCreateButtons(session);
    endToolbarCard();

    ImGui::TableNextColumn();
    beginToolbarCard("Transform", transformWidth);
    renderTransformToolbar();
    endToolbarCard();

    ImGui::TableNextColumn();
    beginToolbarCard("View", viewWidth);
    renderViewToolbar();
    endToolbarCard();
    ImGui::TableNextColumn();
    ImGui::EndTable();
    ImGui::PopStyleVar(2);

    ImGuiWindow *pWindow = ImGui::GetCurrentWindowRead();

    if (pWindow != nullptr && pWindow->DockNode != nullptr)
    {
        const float desiredHeight = std::clamp(
            ImGui::GetCursorPosY() + ImGui::GetStyle().WindowPadding.y,
            32.0f,
            180.0f);

        if (std::fabs(m_toolsDockTargetHeight - desiredHeight) > 1.0f)
        {
            pWindow->DockNode->SizeRef.y = desiredHeight;
            m_toolsDockTargetHeight = desiredHeight;
        }
    }

    ImGui::End();
}

void EditorMainWindow::renderToolModeButtons(EditorSession &session)
{
    const auto renderModeButton = [this](const char *pLabel, EditorSelectionKind kind)
    {
        const bool selected = m_viewport.placementKind() == kind;

        if (renderIconTogglePill(pLabel, pLabel, selectionKindIcon(kind), selected))
        {
            m_viewport.setPlacementKind(selected ? EditorSelectionKind::None : kind);
        }
    };

    if (renderIconTogglePill("Select", "Select", UiIcon::Select, m_viewport.placementKind() == EditorSelectionKind::None))
    {
        m_viewport.setPlacementKind(EditorSelectionKind::None);
    }

    ImGui::SameLine();
    renderModeButton("Terrain", EditorSelectionKind::Terrain);
    ImGui::SameLine();
    renderModeButton("Face", EditorSelectionKind::InteractiveFace);
}

void EditorMainWindow::renderTransformToolbar()
{
    const auto renderTransformModeButton =
        [this](const char *pLabel, EditorOutdoorViewport::TransformGizmoMode mode)
    {
        const bool isSelected = m_viewport.transformGizmoMode() == mode;
        const UiIcon icon = mode == EditorOutdoorViewport::TransformGizmoMode::Translate ? UiIcon::Move : UiIcon::Rotate;

        if (renderIconTogglePill(pLabel, pLabel, icon, isSelected))
        {
            m_viewport.setTransformGizmoMode(mode);
        }
    };

    renderTransformModeButton("Move", EditorOutdoorViewport::TransformGizmoMode::Translate);
    ImGui::SameLine();
    renderTransformModeButton("Rotate", EditorOutdoorViewport::TransformGizmoMode::Rotate);
    ImGui::NewLine();

    const auto renderTransformSpaceButton =
        [this](const char *pLabel, EditorOutdoorViewport::TransformSpaceMode mode)
    {
        const bool isSelected = m_viewport.transformSpaceMode() == mode;
        const UiIcon icon = mode == EditorOutdoorViewport::TransformSpaceMode::World ? UiIcon::World : UiIcon::Local;

        if (renderIconTogglePill(pLabel, pLabel, icon, isSelected))
        {
            m_viewport.setTransformSpaceMode(mode);
        }
    };

    renderTransformSpaceButton("World", EditorOutdoorViewport::TransformSpaceMode::World);
    ImGui::SameLine();
    renderTransformSpaceButton("Local", EditorOutdoorViewport::TransformSpaceMode::Local);
    ImGui::SameLine();

    bool snapEnabled = m_viewport.snapEnabled();

    if (renderIconTogglePill("Snap", "Snap", UiIcon::Snap, snapEnabled))
    {
        m_viewport.setSnapEnabled(!snapEnabled);
    }

    ImGui::NewLine();
    int snapStep = m_viewport.snapStep();
    renderToolbarSubLabel("Snap Step");
    ImGui::SameLine();
    ImGui::SetNextItemWidth(64.0f);

    if (ImGui::InputInt("Step", &snapStep))
    {
        m_viewport.setSnapStep(snapStep);
    }
}

void EditorMainWindow::renderTerrainToolbar(EditorSession &session)
{
    ImGui::BeginDisabled(m_viewport.placementKind() != EditorSelectionKind::Terrain);
    static constexpr const char *FalloffModeLabels[] = {"Flat", "Linear", "Smooth"};
    static constexpr const char *FlattenTargetModeLabels[] = {"Sampled", "Numeric"};
    const bool paintEnabled = session.terrainPaintEnabled();
    const bool sculptEnabled = session.terrainSculptEnabled();

    ImGui::BeginGroup();

    if (renderIconTogglePill("PaintModeEnabled", "Paint", UiIcon::Paint, paintEnabled))
    {
        session.setTerrainPaintEnabled(!paintEnabled);

        if (!paintEnabled)
        {
            session.setTerrainSculptEnabled(false);
        }
    }

    if (ImGui::SameLine(), renderIconTogglePill("SculptModeEnabled", "Sculpt", UiIcon::Flatten, sculptEnabled))
    {
        session.setTerrainSculptEnabled(!sculptEnabled);

        if (!sculptEnabled)
        {
            session.setTerrainPaintEnabled(false);
        }
    }

    if (sculptEnabled)
    {
        ImGui::NewLine();
        renderToolbarSubLabel("Tool");
        ImGui::SameLine();
        const std::array<std::pair<const char *, EditorTerrainSculptMode>, 6> sculptModes = {{
            {"Raise", EditorTerrainSculptMode::Raise},
            {"Lower", EditorTerrainSculptMode::Lower},
            {"Flatten", EditorTerrainSculptMode::Flatten},
            {"Smooth", EditorTerrainSculptMode::Smooth},
            {"Noise", EditorTerrainSculptMode::Noise},
            {"Ramp", EditorTerrainSculptMode::Ramp}
        }};

        for (size_t index = 0; index < sculptModes.size(); ++index)
        {
            const auto &[pLabel, mode] = sculptModes[index];
            const bool selected = session.terrainSculptMode() == mode;

            if (renderIconTogglePill(pLabel, pLabel, terrainSculptModeIcon(mode), selected))
            {
                session.setTerrainSculptMode(mode);
            }

            if ((index % 3) != 2 && index + 1 < sculptModes.size())
            {
                ImGui::SameLine();
            }
        }
    }

    ImGui::EndGroup();
    ImGui::SameLine(0.0f, 10.0f);
    ImGui::BeginGroup();

    if (paintEnabled)
    {
        int tileId = static_cast<int>(session.terrainPaintTileId());
        renderToolbarSubLabel("Tile");
        ImGui::SameLine();
        ImGui::SetNextItemWidth(54.0f);

        if (ImGui::InputInt("##TerrainTile", &tileId))
        {
            tileId = std::clamp(tileId, 0, 255);
            session.setTerrainPaintTileId(static_cast<uint8_t>(tileId));
        }

        ImGui::SameLine();
        renderTerrainTilePreviewButton(
            m_viewport,
            session.terrainPaintTileId(),
            true,
            ImVec2(28.0f, 28.0f));

        ImGui::NewLine();
        renderToolbarSubLabel("Brush");
        ImGui::SameLine();

        const std::array<std::pair<const char *, EditorTerrainPaintMode>, 3> paintModes = {{
            {"Brush", EditorTerrainPaintMode::Brush},
            {"Rect", EditorTerrainPaintMode::Rectangle},
            {"Fill", EditorTerrainPaintMode::Fill}
        }};

        for (size_t index = 0; index < paintModes.size(); ++index)
        {
            const auto &[pLabel, mode] = paintModes[index];
            const bool selected = session.terrainPaintMode() == mode;

            if (renderIconTogglePill(pLabel, pLabel, terrainPaintModeIcon(mode), selected))
            {
                session.setTerrainPaintMode(mode);
            }

            if (index + 1 < paintModes.size())
            {
                ImGui::SameLine();
            }
        }

        if (session.terrainPaintMode() == EditorTerrainPaintMode::Brush)
        {
            ImGui::NewLine();
            int radius = session.terrainPaintRadius();
            renderToolbarSubLabel("Radius");
            ImGui::SameLine();
            ImGui::SetNextItemWidth(56.0f);

            if (ImGui::InputInt("##TerrainPaintRadius", &radius))
            {
                session.setTerrainPaintRadius(radius);
            }

            ImGui::SameLine();
            int edgeNoise = session.terrainPaintEdgeNoise();
            renderToolbarSubLabel("Edge");
            ImGui::SameLine();
            ImGui::SetNextItemWidth(52.0f);

            if (ImGui::InputInt("##TerrainPaintEdgeNoise", &edgeNoise))
            {
                session.setTerrainPaintEdgeNoise(edgeNoise);
            }
        }
    }
    else if (sculptEnabled)
    {
        renderToolbarSubLabel("Brush");
        ImGui::SameLine();
        int radius = session.terrainSculptRadius();
        ImGui::SetNextItemWidth(56.0f);

        if (ImGui::InputInt("##TerrainRadius", &radius))
        {
            session.setTerrainSculptRadius(radius);
        }

        ImGui::SameLine();
        int strength = session.terrainSculptStrength();
        renderToolbarSubLabel("Strength");
        ImGui::SameLine();
        ImGui::SetNextItemWidth(56.0f);

        if (ImGui::InputInt("##TerrainStrength", &strength))
        {
            session.setTerrainSculptStrength(strength);
        }

        ImGui::NewLine();
        renderToolbarSubLabel("Falloff");
        ImGui::SameLine();
        ImGui::AlignTextToFramePadding();
        ImGui::SetNextItemWidth(80.0f);
        int falloffMode = static_cast<int>(session.terrainSculptFalloffMode());

        if (ImGui::Combo("##TerrainFalloffMode", &falloffMode, FalloffModeLabels, IM_ARRAYSIZE(FalloffModeLabels)))
        {
            session.setTerrainSculptFalloffMode(static_cast<EditorTerrainFalloffMode>(falloffMode));
        }

        if (session.terrainSculptMode() == EditorTerrainSculptMode::Flatten)
        {
            ImGui::SameLine();
            int targetMode = static_cast<int>(session.terrainFlattenTargetMode());
            renderToolbarSubLabel("Target");
            ImGui::SameLine();
            ImGui::SetNextItemWidth(80.0f);

            if (ImGui::Combo(
                    "##TerrainFlattenTargetMode",
                    &targetMode,
                    FlattenTargetModeLabels,
                    IM_ARRAYSIZE(FlattenTargetModeLabels)))
            {
                session.setTerrainFlattenTargetMode(static_cast<EditorTerrainFlattenTargetMode>(targetMode));
            }

            if (session.terrainFlattenTargetMode() == EditorTerrainFlattenTargetMode::Numeric)
            {
                ImGui::NewLine();
                int targetHeight = session.terrainFlattenTargetHeight();
                renderToolbarSubLabel("Height");
                ImGui::SameLine();
                ImGui::SetNextItemWidth(56.0f);

                if (ImGui::InputInt("##TerrainFlattenTargetHeight", &targetHeight))
                {
                    session.setTerrainFlattenTargetHeight(targetHeight);
                }
            }
            else
            {
                ImGui::NewLine();
                ImGui::TextDisabled("H %d", session.terrainFlattenTargetHeight());

                const bool canPickSelected =
                    session.selection().kind == EditorSelectionKind::Terrain
                    && session.selection().index
                        < static_cast<size_t>(Game::OutdoorMapData::TerrainWidth * Game::OutdoorMapData::TerrainHeight);
                ImGui::BeginDisabled(!canPickSelected);

                if (ImGui::Button("Pick Selected"))
                {
                    tryPickFlattenTargetFromSelectedTerrainCell(session);
                }

                ImGui::EndDisabled();
                ImGui::SameLine();
                ImGui::TextDisabled("Alt+LMB");
            }
        }
    }

    ImGui::EndGroup();

    ImGui::EndDisabled();
}

void EditorMainWindow::renderViewToolbar()
{
    renderToolbarSubLabel("Primary");
    bool showTerrain = m_viewport.showTerrainFill();
    if (renderIconTogglePill("ViewTerrain", "Terrain", UiIcon::Terrain, showTerrain))
    {
        m_viewport.setShowTerrainFill(!showTerrain);
    }

    ImGui::SameLine();
    bool showTerrainGrid = m_viewport.showTerrainGrid();
    if (renderIconTogglePill("ViewGrid", "Grid", UiIcon::Grid, showTerrainGrid))
    {
        m_viewport.setShowTerrainGrid(!showTerrainGrid);
    }

    ImGui::SameLine();
    if (renderIconTogglePill(
            "PreviewTextured",
            "Textured",
            UiIcon::Textured,
            m_viewport.previewMaterialMode() == EditorOutdoorViewport::PreviewMaterialMode::Textured))
    {
        m_viewport.setPreviewMaterialMode(EditorOutdoorViewport::PreviewMaterialMode::Textured);
    }

    ImGui::SameLine();
    if (renderIconTogglePill(
            "PreviewClay",
            "Clay",
            UiIcon::Clay,
            m_viewport.previewMaterialMode() == EditorOutdoorViewport::PreviewMaterialMode::Clay))
    {
        m_viewport.setPreviewMaterialMode(EditorOutdoorViewport::PreviewMaterialMode::Clay);
    }

    ImGui::SameLine();
    bool showEntities = m_viewport.showEntities();
    if (renderIconTogglePill("ViewEntities", "Entities", UiIcon::Entity, showEntities))
    {
        m_viewport.setShowEntities(!showEntities);
    }

    ImGui::SameLine();
    bool showSpawns = m_viewport.showSpawns();
    bool showActors = m_viewport.showActors();
    if (renderIconTogglePill("ViewActors", "Actors", UiIcon::Actor, showActors))
    {
        m_viewport.setShowActors(!showActors);
    }

    ImGui::SameLine();
    bool showEvents = m_viewport.showEventMarkers();
    if (renderIconTogglePill("ViewEvents", "Events", UiIcon::Select, showEvents))
    {
        m_viewport.setShowEventMarkers(!showEvents);
    }

    ImGui::NewLine();
    renderToolbarSubLabel("Secondary");
    bool showBModels = m_viewport.showBModels();
    if (renderSecondaryIconTogglePill("ViewBModels", "BModels", UiIcon::Face, showBModels))
    {
        m_viewport.setShowBModels(!showBModels);
    }

    ImGui::SameLine();
    bool showBModelWire = m_viewport.showBModelWireframe();
    if (renderSecondaryIconTogglePill("ViewWire", "Wire", UiIcon::Wireframe, showBModelWire))
    {
        m_viewport.setShowBModelWireframe(!showBModelWire);
    }

    ImGui::SameLine();
    if (renderSecondaryIconTogglePill(
            "PreviewGrid",
            "Grid",
            UiIcon::Grid,
            m_viewport.previewMaterialMode() == EditorOutdoorViewport::PreviewMaterialMode::Grid))
    {
        m_viewport.setPreviewMaterialMode(EditorOutdoorViewport::PreviewMaterialMode::Grid);
    }

    ImGui::SameLine();
    bool previewSelectedOnly = m_viewport.forcePreviewOnSelectedOnly();
    if (renderSecondaryIconTogglePill("PreviewSelected", "Selected", UiIcon::Select, previewSelectedOnly))
    {
        m_viewport.setForcePreviewOnSelectedOnly(!previewSelectedOnly);
    }

    ImGui::SameLine();
    if (renderSecondaryIconTogglePill("ViewSpawns", "Spawns", UiIcon::Spawn, showSpawns))
    {
        m_viewport.setShowSpawns(!showSpawns);
    }

    ImGui::SameLine();
    bool showObjects = m_viewport.showSpriteObjects();
    if (renderSecondaryIconTogglePill("ViewObjects", "Objects", UiIcon::Object, showObjects))
    {
        m_viewport.setShowSpriteObjects(!showObjects);
    }

    ImGui::NewLine();
    bool showEntityBillboards = m_viewport.showEntityBillboards();
    if (renderSecondaryTogglePill("Entity Preview", showEntityBillboards))
    {
        m_viewport.setShowEntityBillboards(!showEntityBillboards);
    }

    ImGui::SameLine();
    bool showActorBillboards = m_viewport.showActorBillboards();
    if (renderSecondaryTogglePill("Actor Preview", showActorBillboards))
    {
        m_viewport.setShowActorBillboards(!showActorBillboards);
    }

    ImGui::SameLine();
    bool showSpawnActorBillboards = m_viewport.showSpawnActorBillboards();
    if (renderSecondaryTogglePill("Spawn Preview", showSpawnActorBillboards))
    {
        m_viewport.setShowSpawnActorBillboards(!showSpawnActorBillboards);
    }

    ImGui::SameLine();
    bool showChestLinks = m_viewport.showChestLinks();
    if (renderSecondaryTogglePill("Chest Links", showChestLinks))
    {
        m_viewport.setShowChestLinks(!showChestLinks);
    }
}

bool EditorMainWindow::playtestCurrentMap(EditorSession &session, std::string &errorMessage) const
{
    if (!session.hasDocument())
    {
        errorMessage = "no document is loaded";
        return false;
    }

    if (session.document().isDirty() && !session.saveActiveDocument(errorMessage))
    {
        return false;
    }

    if (session.document().isRuntimeBuildDirty() && !session.buildActiveDocument(errorMessage))
    {
        return false;
    }

    const std::filesystem::path gameExecutablePath = defaultGameExecutablePath();

    if (gameExecutablePath.empty())
    {
        errorMessage = "could not locate build/game/openyamm for playtest launch";
        return false;
    }

    const std::string mapFileName = session.document().displayName();

    if (mapFileName.empty())
    {
        errorMessage = "document has no runtime map file";
        return false;
    }

    const std::vector<std::string> arguments = {"--map", mapFileName};

    if (!launchDetachedProcess(gameExecutablePath, arguments, errorMessage))
    {
        return false;
    }

    session.logInfo("Launched playtest for " + mapFileName);
    return true;
}

void EditorMainWindow::renderToolbarStatus(const EditorSession &session)
{
    if (session.hasDocument())
    {
        const EditorDocument &document = session.document();
        const bool sourceDirty = document.isDirty();
        const bool buildDirty = document.isRuntimeBuildDirty();
        const EditorOutdoorMapPackageMetadata &packageMetadata = document.outdoorMapPackageMetadata();

        ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0xE6E8EB));
        ImGui::Text(
            "%s  ·  %s v%u  ·  %s",
            document.displayName().c_str(),
            document.hasMapPackageRoot() ? packageMetadata.packageId.c_str() : "legacy",
            packageMetadata.version,
            document.sceneVirtualPath().c_str());
        ImGui::PopStyleColor();

        if (ImGui::IsItemHovered())
        {
            ImGui::BeginTooltip();
            ImGui::Text("Package Path: %s", document.mapPackagePhysicalPath().string().c_str());
            ImGui::Text("Display Name: %s", packageMetadata.displayName.c_str());
            ImGui::Text("Source Fingerprint: %s", packageMetadata.sourceFingerprint.c_str());
            ImGui::Text("Built Fingerprint: %s", packageMetadata.builtSourceFingerprint.c_str());
            ImGui::EndTooltip();
        }

        ImGui::SameLine();
        renderStatusPill(
            sourceDirty ? "Source · Dirty" : "Source · Saved",
            sourceDirty ? 0xF2DEC2 : 0xD7F0DB,
            sourceDirty ? 0xB9873D : 0x5FA36A,
            sourceDirty ? 0x3A2B18 : 0x1A2B1D);
        ImGui::SameLine();
        renderStatusPill(
            buildDirty ? "Build · Stale" : "Build · Ready",
            buildDirty ? 0xF2DEC2 : 0xD7F0DB,
            buildDirty ? 0xB9873D : 0x5FA36A,
            buildDirty ? 0x3A2B18 : 0x1A2B1D);
        ImGui::SameLine();
        renderStatusPill(
            ("Validation · " + std::to_string(session.validationMessages().size())).c_str(),
            session.validationMessages().empty() ? 0xD7F0DB : 0xF2DEC2,
            session.validationMessages().empty() ? 0x5FA36A : 0xD0A44C,
            session.validationMessages().empty() ? 0x1A2B1D : 0x332814);

        if (!m_statusMessage.empty())
        {
            ImGui::SameLine();

            if (m_statusMessageKind == StatusMessageKind::Success)
            {
                renderStatusPill(m_statusMessage.c_str(), 0xD7F0DB, 0x5FA36A, 0x1A2B1D);
            }
            else if (m_statusMessageKind == StatusMessageKind::Error)
            {
                renderStatusPill(m_statusMessage.c_str(), 0xF5D3D3, 0xCC6666, 0x301A1A);
            }
            else
            {
                renderStatusPill(m_statusMessage.c_str(), 0xE7D8B8, 0xD0A44C, 0x332814);
            }
        }

        if (!session.validationMessages().empty())
        {
            ImGui::SameLine();
            ImGui::TextDisabled("hover validation");

            if (ImGui::IsItemHovered())
            {
                ImGui::BeginTooltip();
                ImGui::TextUnformatted("Validation");

                for (const std::string &message : session.validationMessages())
                {
                    ImGui::BulletText("%s", message.c_str());
                }

                ImGui::EndTooltip();
            }
        }
    }
    else
    {
        ImGui::TextUnformatted("No document loaded.");
    }
}

void EditorMainWindow::setStatusMessage(StatusMessageKind kind, const std::string &message)
{
    m_statusMessageKind = kind;
    m_statusMessage = message;
}

std::optional<bgfx::TextureHandle> EditorMainWindow::ensureBitmapPreviewTexture(
    const EditorSession &session,
    const std::string &textureName,
    int16_t paletteId,
    bool spriteTexture) const
{
    const Engine::AssetFileSystem *pAssetFileSystem = session.assetFileSystem();

    if (pAssetFileSystem == nullptr)
    {
        return std::nullopt;
    }

    const std::string normalizedName =
        (spriteTexture ? "sprite|" : "bitmap|") + toLowerCopy(textureName) + "|" + std::to_string(static_cast<int>(paletteId));
    const auto existingIt = m_bitmapPreviewTextures.find(normalizedName);

    if (existingIt != m_bitmapPreviewTextures.end())
    {
        if (bgfx::isValid(existingIt->second))
        {
            return existingIt->second;
        }

        return std::nullopt;
    }

    int width = 0;
    int height = 0;
    const std::optional<std::vector<uint8_t>> pixels = spriteTexture
        ? loadSpritePreviewPixels(*pAssetFileSystem, textureName, paletteId, width, height)
        : loadBitmapPreviewPixels(*pAssetFileSystem, session.bitmapTextureNames(), textureName, width, height);

    if (!pixels || width <= 0 || height <= 0)
    {
        const bgfx::TextureHandle invalidHandle = BGFX_INVALID_HANDLE;
        m_bitmapPreviewTextures.emplace(normalizedName, invalidHandle);
        m_bitmapPreviewTextureSizes.emplace(normalizedName, std::pair<int, int>{0, 0});
        return std::nullopt;
    }

    const bgfx::TextureHandle textureHandle = bgfx::createTexture2D(
        static_cast<uint16_t>(width),
        static_cast<uint16_t>(height),
        false,
        1,
        bgfx::TextureFormat::BGRA8,
        BGFX_SAMPLER_MIN_POINT | BGFX_SAMPLER_MAG_POINT | BGFX_SAMPLER_MIP_POINT,
        bgfx::copy(pixels->data(), static_cast<uint32_t>(pixels->size())));

    m_bitmapPreviewTextures.emplace(normalizedName, textureHandle);
    m_bitmapPreviewTextureSizes.emplace(normalizedName, std::pair<int, int>{width, height});

    if (!bgfx::isValid(textureHandle))
    {
        return std::nullopt;
    }

    return textureHandle;
}

std::optional<std::pair<int, int>> EditorMainWindow::bitmapPreviewTextureSize(
    const std::string &textureName,
    int16_t paletteId,
    bool spriteTexture) const
{
    const std::string normalizedName =
        (spriteTexture ? "sprite|" : "bitmap|") + toLowerCopy(textureName) + "|" + std::to_string(static_cast<int>(paletteId));
    const auto existingIt = m_bitmapPreviewTextureSizes.find(normalizedName);

    if (existingIt == m_bitmapPreviewTextureSizes.end())
    {
        return std::nullopt;
    }

    if (existingIt->second.first <= 0 || existingIt->second.second <= 0)
    {
        return std::nullopt;
    }

    return existingIt->second;
}

void EditorMainWindow::renderBitmapPreviewTooltip(
    const EditorSession &session,
    const std::string &label,
    const std::string &textureName,
    int16_t paletteId,
    bool spriteTexture) const
{
    const std::optional<bgfx::TextureHandle> textureHandle =
        ensureBitmapPreviewTexture(session, textureName, paletteId, spriteTexture);

    if (!textureHandle || !bgfx::isValid(*textureHandle))
    {
        return;
    }

    const std::optional<std::pair<int, int>> textureSize =
        bitmapPreviewTextureSize(textureName, paletteId, spriteTexture);
    const ImVec2 imageSize = textureSize
        ? ImVec2(static_cast<float>(textureSize->first), static_cast<float>(textureSize->second))
        : ImVec2(96.0f, 96.0f);

    const ImVec2 mousePosition = ImGui::GetMousePos();
    ImGui::SetNextWindowPos(
        ImVec2(mousePosition.x - 200.0f, mousePosition.y),
        ImGuiCond_Always,
        ImVec2(1.0f, 0.0f));
    ImGui::BeginTooltip();
    ImGui::TextUnformatted(label.c_str());
    ImGui::TextUnformatted(textureName.c_str());
    ImGui::Image(
        static_cast<ImTextureID>(static_cast<uintptr_t>(textureHandle->idx + 1)),
        imageSize,
        ImVec2(0.0f, 0.0f),
        ImVec2(1.0f, 1.0f));
    ImGui::EndTooltip();
}

bool EditorMainWindow::renderIdOptionSelectorWithBitmapPreview(
    EditorSession &session,
    const char *pLabel,
    uint32_t &value,
    const std::vector<EditorIdLabelOption> &options,
    const char *pZeroLabel,
    const char *pFallbackPrefix,
    bool transient,
    const std::function<std::optional<std::pair<std::string, int16_t>>(uint32_t)> &resolveTexture) const
{
    beginInspectorFieldRow(pLabel);

    const std::string comboId = inspectorFieldId(pLabel);
    const std::string preview = selectorPreviewLabel(value, options, pZeroLabel, pFallbackPrefix);

    if (!ImGui::BeginCombo(comboId.c_str(), preview.c_str()))
    {
        return false;
    }

    const ImGuiID filterStorageId = ImGui::GetID((comboId + "/filter").c_str());
    static std::unordered_map<ImGuiID, std::string> filters;
    std::string &filter = filters[filterStorageId];
    char filterBuffer[128] = {};
    std::snprintf(filterBuffer, sizeof(filterBuffer), "%s", filter.c_str());
    ImGui::SetNextItemWidth(-FLT_MIN);

    if (ImGui::InputText("##Filter", filterBuffer, sizeof(filterBuffer)))
    {
        filter = filterBuffer;
    }

    const std::string normalizedFilter = toLowerCopy(filter);
    bool changed = false;

    if (pZeroLabel != nullptr)
    {
        const bool selected = value == 0;

        if ((normalizedFilter.empty() || toLowerCopy(pZeroLabel).find(normalizedFilter) != std::string::npos)
            && ImGui::Selectable(pZeroLabel, selected))
        {
            if (value != 0)
            {
                if (!transient)
                {
                    session.captureUndoSnapshot();
                }

                value = 0;
                changed = true;
            }
        }

        if (selected)
        {
            ImGui::SetItemDefaultFocus();
        }
    }

    for (const EditorIdLabelOption &option : options)
    {
        if (!optionMatchesFilter(option, normalizedFilter))
        {
            continue;
        }

        const bool selected = option.id == value;

        if (ImGui::Selectable(option.label.c_str(), selected))
        {
            if (option.id != value)
            {
                if (!transient)
                {
                    session.captureUndoSnapshot();
                }

                value = option.id;
                changed = true;
            }
        }

        if (ImGui::IsItemHovered())
        {
            const std::optional<std::pair<std::string, int16_t>> preview = resolveTexture(option.id);

            if (preview)
            {
                renderBitmapPreviewTooltip(session, option.label, preview->first, preview->second, true);
            }
        }

        if (selected)
        {
            ImGui::SetItemDefaultFocus();
        }
    }

    ImGui::EndCombo();
    return changed;
}

bool EditorMainWindow::renderDecorationSelector(
    EditorSession &session,
    const char *pLabel,
    uint16_t &decorationListId,
    bool transient) const
{
    uint32_t selectedId = decorationListId;

    if (!renderIdOptionSelectorWithBitmapPreview(
            session,
            pLabel,
            selectedId,
            session.decorationOptions(),
            nullptr,
            "Decoration",
            transient,
            [&session](uint32_t optionId)
            {
                return session.previewDecorationTexture(static_cast<uint16_t>(std::min<uint32_t>(optionId, 65535)));
            }))
    {
        return false;
    }

    decorationListId = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));
    return true;
}

bool EditorMainWindow::renderObjectSelector(
    EditorSession &session,
    const char *pLabel,
    uint16_t &objectDescriptionId,
    bool transient) const
{
    uint32_t selectedId = objectDescriptionId;

    if (!renderIdOptionSelectorWithBitmapPreview(
            session,
            pLabel,
            selectedId,
            session.objectOptions(),
            nullptr,
            "Object",
            transient,
            [&session](uint32_t optionId)
            {
                return session.previewObjectTexture(static_cast<uint16_t>(std::min<uint32_t>(optionId, 65535)));
            }))
    {
        return false;
    }

    objectDescriptionId = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));
    return true;
}

bool EditorMainWindow::renderMonsterTemplateSelector(
    EditorSession &session,
    const char *pLabel,
    Game::MapDeltaActor &actor,
    bool transient) const
{
    const int16_t previousMonsterInfoId = actor.monsterInfoId;
    uint32_t selectedId = actor.monsterInfoId > 0 ? static_cast<uint32_t>(actor.monsterInfoId) : 0;

    if (!renderIdOptionSelectorWithBitmapPreview(
            session,
            pLabel,
            selectedId,
            session.monsterOptions(),
            "<none>",
            "Monster Template",
            transient,
            [&session, &actor](uint32_t optionId)
            {
                const int16_t resolvedId = static_cast<int16_t>(std::min<uint32_t>(optionId, 32767));
                return session.previewMonsterTexture(resolvedId, actor.monsterId);
            }))
    {
        return false;
    }

    actor.monsterInfoId = static_cast<int16_t>(std::min<uint32_t>(selectedId, 32767));
    applyMonsterTemplateSelection(session, actor, previousMonsterInfoId);
    return true;
}

void EditorMainWindow::destroyBitmapPreviewTextures()
{
    for (const auto &[name, textureHandle] : m_bitmapPreviewTextures)
    {
        if (bgfx::isValid(textureHandle))
        {
            bgfx::destroy(textureHandle);
        }
    }

    m_bitmapPreviewTextures.clear();
    m_bitmapPreviewTextureSizes.clear();
}

bool EditorMainWindow::renderBitmapTextureSelector(
    EditorSession &session,
    const char *pLabel,
    std::string &value,
    std::optional<size_t> bmodelIndex) const
{
    beginInspectorFieldRow(pLabel);

    const std::string popupId = inspectorFieldId(pLabel) + "/popup";
    const ImVec2 previewSize(56.0f, 56.0f);
    bool changed = false;

    if (session.assetFileSystem() != nullptr && !value.empty())
    {
        const std::optional<bgfx::TextureHandle> textureHandle =
            ensureBitmapPreviewTexture(session, value);

        if (textureHandle && bgfx::isValid(*textureHandle))
        {
            ImGui::Image(
                static_cast<ImTextureID>(static_cast<uintptr_t>(textureHandle->idx + 1)),
                previewSize,
                ImVec2(0.0f, 0.0f),
                ImVec2(1.0f, 1.0f));
        }
        else
        {
            ImGui::Button(value.c_str(), previewSize);
        }
    }
    else
    {
        ImGui::Button(value.empty() ? "<none>" : value.c_str(), previewSize);
    }

    ImGui::SameLine();

    if (ImGui::Button("Browse..."))
    {
        ImGui::OpenPopup(popupId.c_str());
    }

    ImGui::SameLine();
    ImGui::TextUnformatted(value.empty() ? "<none>" : value.c_str());

    if (ImGui::BeginPopup(popupId.c_str()))
    {
        const ImGuiID filterStorageId = ImGui::GetID((popupId + "/filter").c_str());
        const ImGuiID sourceStorageId = ImGui::GetID((popupId + "/source").c_str());
        static std::unordered_map<ImGuiID, std::string> filters;
        static std::unordered_map<ImGuiID, int> sourceModeByPopup;
        std::string &filter = filters[filterStorageId];
        int &sourceMode = sourceModeByPopup[sourceStorageId];
        char filterBuffer[128] = {};
        std::snprintf(filterBuffer, sizeof(filterBuffer), "%s", filter.c_str());
        ImGui::SetNextItemWidth(-FLT_MIN);

        if (ImGui::InputText("##Filter", filterBuffer, sizeof(filterBuffer)))
        {
            filter = filterBuffer;
        }

        std::vector<std::string> availableTextures;

        if (!bmodelIndex.has_value() && sourceMode == 0)
        {
            sourceMode = 1;
        }

        if (sourceMode == 2)
        {
            availableTextures = session.bitmapTextureNames();
        }
        else if (sourceMode == 0 && bmodelIndex.has_value())
        {
            availableTextures = session.usedBitmapTextureNamesForBModel(*bmodelIndex);

            if (availableTextures.empty())
            {
                availableTextures = session.usedBitmapTextureNamesInMap();
            }
        }
        else
        {
            availableTextures = session.usedBitmapTextureNamesInMap();
        }

        ImGui::Spacing();
        ImGui::TextUnformatted("Source:");
        ImGui::SameLine();

        if (bmodelIndex.has_value())
        {
            ImGui::RadioButton("On This BModel##TextureSource", &sourceMode, 0);
            ImGui::SameLine();
        }

        ImGui::RadioButton("Used In Map##TextureSource", &sourceMode, 1);
        ImGui::SameLine();
        ImGui::RadioButton("All Textures##TextureSource", &sourceMode, 2);

        const std::string normalizedFilter = toLowerCopy(filter);

        if (ImGui::BeginChild("TextureBrowserList", ImVec2(560.0f, 420.0f), ImGuiChildFlags_Borders))
        {
            int tilesOnRow = 0;

            for (const std::string &option : availableTextures)
            {
                if (!normalizedFilter.empty() && toLowerCopy(option).find(normalizedFilter) == std::string::npos)
                {
                    continue;
                }

                ImGui::PushID(option.c_str());
                const bool selected = toLowerCopy(option) == toLowerCopy(value);
                const std::optional<bgfx::TextureHandle> textureHandle =
                    session.assetFileSystem() != nullptr ? ensureBitmapPreviewTexture(session, option) : std::nullopt;

                if (selected)
                {
                    ImGui::PushStyleColor(ImGuiCol_ChildBg, ImVec4(0.18f, 0.16f, 0.12f, 1.0f));
                }

                if (ImGui::BeginChild("TextureTile", ImVec2(96.0f, 112.0f), ImGuiChildFlags_Borders))
                {
                    if (textureHandle && bgfx::isValid(*textureHandle))
                    {
                        ImGui::ImageButton(
                            "##TextureImage",
                            static_cast<ImTextureID>(static_cast<uintptr_t>(textureHandle->idx + 1)),
                            ImVec2(80.0f, 80.0f),
                            ImVec2(0.0f, 0.0f),
                            ImVec2(1.0f, 1.0f));
                    }
                    else
                    {
                        ImGui::Button(option.c_str(), ImVec2(80.0f, 80.0f));
                    }

                    if (ImGui::IsItemClicked())
                    {
                        session.captureUndoSnapshot();
                        value = option;
                        changed = true;
                        ImGui::CloseCurrentPopup();
                    }

                    ImGui::PushTextWrapPos(ImGui::GetCursorPos().x + 80.0f);
                    ImGui::TextUnformatted(option.c_str());
                    ImGui::PopTextWrapPos();
                }
                ImGui::EndChild();

                if (selected)
                {
                    ImGui::PopStyleColor();
                }

                ++tilesOnRow;
                if ((tilesOnRow % 5) != 0)
                {
                    ImGui::SameLine();
                }

                ImGui::PopID();
            }
        }
        ImGui::EndChild();

        ImGui::EndPopup();
    }

    return changed;
}

bool EditorMainWindow::renderInlineBitmapTextureSelector(
    EditorSession &session,
    const char *pId,
    std::string &value,
    std::optional<size_t> bmodelIndex) const
{
    const std::string popupId = std::string(pId) + "/popup";
    bool changed = false;

    if (ImGui::Button((value.empty() ? "<none>" : value).c_str(), ImVec2(-FLT_MIN, 0.0f)))
    {
        ImGui::OpenPopup(popupId.c_str());
    }

    if (ImGui::BeginPopup(popupId.c_str()))
    {
        const ImGuiID filterStorageId = ImGui::GetID((popupId + "/filter").c_str());
        const ImGuiID sourceStorageId = ImGui::GetID((popupId + "/source").c_str());
        static std::unordered_map<ImGuiID, std::string> filters;
        static std::unordered_map<ImGuiID, int> sourceModeByPopup;
        std::string &filter = filters[filterStorageId];
        int &sourceMode = sourceModeByPopup[sourceStorageId];
        char filterBuffer[128] = {};
        std::snprintf(filterBuffer, sizeof(filterBuffer), "%s", filter.c_str());
        ImGui::SetNextItemWidth(320.0f);

        if (ImGui::InputText("##Filter", filterBuffer, sizeof(filterBuffer)))
        {
            filter = filterBuffer;
        }

        std::vector<std::string> availableTextures;

        if (!bmodelIndex.has_value() && sourceMode == 0)
        {
            sourceMode = 1;
        }

        if (sourceMode == 2)
        {
            availableTextures = session.bitmapTextureNames();
        }
        else if (sourceMode == 0 && bmodelIndex.has_value())
        {
            availableTextures = session.usedBitmapTextureNamesForBModel(*bmodelIndex);

            if (availableTextures.empty())
            {
                availableTextures = session.usedBitmapTextureNamesInMap();
            }
        }
        else
        {
            availableTextures = session.usedBitmapTextureNamesInMap();
        }

        ImGui::Spacing();

        if (bmodelIndex.has_value())
        {
            ImGui::RadioButton("This BModel##InlineTextureSource", &sourceMode, 0);
            ImGui::SameLine();
        }

        ImGui::RadioButton("Map##InlineTextureSource", &sourceMode, 1);
        ImGui::SameLine();
        ImGui::RadioButton("All##InlineTextureSource", &sourceMode, 2);

        const std::string normalizedFilter = toLowerCopy(filter);

        if (ImGui::BeginChild("InlineTextureBrowserList", ImVec2(360.0f, 260.0f), ImGuiChildFlags_Borders))
        {
            for (const std::string &option : availableTextures)
            {
                if (!normalizedFilter.empty() && toLowerCopy(option).find(normalizedFilter) == std::string::npos)
                {
                    continue;
                }

                if (ImGui::Selectable(option.c_str(), toLowerCopy(option) == toLowerCopy(value)))
                {
                    value = option;
                    changed = true;
                    ImGui::CloseCurrentPopup();
                    break;
                }

                if (ImGui::IsItemHovered() && session.assetFileSystem() != nullptr)
                {
                    const std::optional<bgfx::TextureHandle> textureHandle =
                        ensureBitmapPreviewTexture(session, option);

                    if (textureHandle && bgfx::isValid(*textureHandle))
                    {
                        ImGui::BeginTooltip();
                        ImGui::TextUnformatted(option.c_str());
                        ImGui::Image(
                            static_cast<ImTextureID>(static_cast<uintptr_t>(textureHandle->idx + 1)),
                            ImVec2(96.0f, 96.0f),
                            ImVec2(0.0f, 0.0f),
                            ImVec2(1.0f, 1.0f));
                        ImGui::EndTooltip();
                    }
                }
            }
        }

        ImGui::EndChild();
        ImGui::EndPopup();
    }

    return changed;
}

void EditorMainWindow::renderPlacementButtons(EditorSession &session)
{
    const auto renderPlacementButton =
        [this](const char *pId, const char *pLabel, EditorSelectionKind kind)
    {
        const bool selected = m_viewport.placementKind() == kind;
        return renderIconTogglePill(pId, pLabel, selectionKindIcon(kind), selected);
    };

    const bool entityPlacementSelected = m_viewport.placementKind() == EditorSelectionKind::Entity;
    if (renderIconTogglePill("PlaceEntity", "Entity", UiIcon::Entity, entityPlacementSelected))
    {
        if (entityPlacementSelected)
        {
            m_viewport.setPlacementKind(EditorSelectionKind::None);
        }
        else
        {
            if (session.selection().kind == EditorSelectionKind::Entity)
            {
                const Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();

                if (session.selection().index < sceneData.entities.size())
                {
                    session.setPendingEntityDecorationListId(
                        sceneData.entities[session.selection().index].entity.decorationListId);
                }
            }

            m_viewport.setPlacementKind(EditorSelectionKind::Entity);
        }
    }

    ImGui::SameLine();
    if (renderPlacementButton("PlaceSpawn", "Spawn", EditorSelectionKind::Spawn))
    {
        const bool selected = m_viewport.placementKind() == EditorSelectionKind::Spawn;

        if (selected)
        {
            m_viewport.setPlacementKind(EditorSelectionKind::None);
        }
        else
        {
            if (session.selection().kind == EditorSelectionKind::Spawn)
            {
                const Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();

                if (session.selection().index < sceneData.spawns.size())
                {
                    session.setPendingSpawn(sceneData.spawns[session.selection().index].spawn);
                }
            }

            m_viewport.setPlacementKind(EditorSelectionKind::Spawn);
        }
    }

    ImGui::SameLine();
    if (renderPlacementButton("PlaceActor", "Actor", EditorSelectionKind::Actor))
    {
        const bool selected = m_viewport.placementKind() == EditorSelectionKind::Actor;

        if (selected)
        {
            m_viewport.setPlacementKind(EditorSelectionKind::None);
        }
        else
        {
            if (session.selection().kind == EditorSelectionKind::Actor)
            {
                const Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();

                if (session.selection().index < sceneData.initialState.actors.size())
                {
                    session.setPendingActor(sceneData.initialState.actors[session.selection().index]);
                }
            }

            m_viewport.setPlacementKind(EditorSelectionKind::Actor);
        }
    }

    ImGui::SameLine();
    const bool selected = m_viewport.placementKind() == EditorSelectionKind::SpriteObject;
    if (renderIconTogglePill("PlaceObject", "Object", UiIcon::Object, selected))
    {
        if (selected)
        {
            m_viewport.setPlacementKind(EditorSelectionKind::None);
        }
        else
        {
            if (session.selection().kind == EditorSelectionKind::SpriteObject)
            {
                const Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();

                if (session.selection().index < sceneData.initialState.spriteObjects.size())
                {
                    session.setPendingSpriteObjectDescriptionId(
                        sceneData.initialState.spriteObjects[session.selection().index].objectDescriptionId);
                }
            }

            m_viewport.setPlacementKind(EditorSelectionKind::SpriteObject);
        }
    }
}

void EditorMainWindow::renderCreateButtons(EditorSession &session)
{
    const auto renderPlacementButton =
        [this](EditorSession &session, const char *pId, const char *pLabel, EditorSelectionKind kind)
    {
        if (kind == EditorSelectionKind::Entity)
        {
            const bool selected = m_viewport.placementKind() == EditorSelectionKind::Entity;

            if (renderIconTogglePill(pId, pLabel, UiIcon::Entity, selected))
            {
                if (selected)
                {
                    m_viewport.setPlacementKind(EditorSelectionKind::None);
                }
                else
                {
                    if (session.selection().kind == EditorSelectionKind::Entity)
                    {
                        const Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();

                        if (session.selection().index < sceneData.entities.size())
                        {
                            session.setPendingEntityDecorationListId(
                                sceneData.entities[session.selection().index].entity.decorationListId);
                        }
                    }

                    m_viewport.setPlacementKind(EditorSelectionKind::Entity);
                }
            }

            return;
        }

        if (kind == EditorSelectionKind::SpriteObject)
        {
            const bool selected = m_viewport.placementKind() == EditorSelectionKind::SpriteObject;

            if (renderIconTogglePill(pId, pLabel, UiIcon::Object, selected))
            {
                if (selected)
                {
                    m_viewport.setPlacementKind(EditorSelectionKind::None);
                }
                else
                {
                    if (session.selection().kind == EditorSelectionKind::SpriteObject)
                    {
                        const Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();

                        if (session.selection().index < sceneData.initialState.spriteObjects.size())
                        {
                            session.setPendingSpriteObjectDescriptionId(
                                sceneData.initialState.spriteObjects[session.selection().index].objectDescriptionId);
                        }
                    }

                    m_viewport.setPlacementKind(EditorSelectionKind::SpriteObject);
                }
            }

            return;
        }

        const bool selected = m_viewport.placementKind() == kind;

        if (renderIconTogglePill(pId, pLabel, selectionKindIcon(kind), selected))
        {
            m_viewport.setPlacementKind(selected ? EditorSelectionKind::None : kind);
        }
    };

    renderPlacementButton(session, "CreateEntity", "Entity", EditorSelectionKind::Entity);
    ImGui::SameLine();
    renderPlacementButton(session, "CreateSpawn", "Spawn", EditorSelectionKind::Spawn);
    ImGui::SameLine();
    renderPlacementButton(session, "CreateActor", "Actor", EditorSelectionKind::Actor);
    ImGui::NewLine();
    renderPlacementButton(session, "CreateObject", "Object", EditorSelectionKind::SpriteObject);
    ImGui::SameLine();

    if (renderIconTogglePill("ImportBModel", "Import BModel", UiIcon::Face, false))
    {
        m_openImportNewBModelModal = true;
    }

    const bool canMutateSelection = isObjectLifecycleKind(session.selection().kind);

    ImGui::BeginDisabled(!canMutateSelection);
    ImGui::SameLine();
    if (renderTogglePill("Duplicate", false))
    {
        duplicateSelected(session);
    }

    ImGui::SameLine();

    if (renderTogglePill("Delete", false))
    {
        deleteSelected(session);
    }

    ImGui::EndDisabled();
}

const EditorMainWindow::ModelImportInspectionState &EditorMainWindow::ensureModelImportInspection(
    const char *pPath,
    ModelImportInspectionState &state) const
{
    const std::string pathText = trimCopy(pPath != nullptr ? pPath : "");

    if (state.cachedPath == pathText)
    {
        return state;
    }

    state.cachedPath = pathText;
    state.entries.clear();
    state.errorMessage.clear();

    if (pathText.empty())
    {
        return state;
    }

    std::vector<ImportedModel> models;

    if (!loadImportedModelsFromFile(std::filesystem::path(pathText), models, state.errorMessage))
    {
        return state;
    }

    state.entries.reserve(models.size());

    for (const ImportedModel &model : models)
    {
        state.entries.push_back(buildImportedModelInspectionEntry(model));
    }

    return state;
}

bool EditorMainWindow::renderImportedModelSelector(
    const char *pId,
    const ModelImportInspectionState &state,
    std::string &selectedModelName) const
{
    const std::string previewText =
        trimCopy(selectedModelName).empty() ? "<Merged Scene>" : selectedModelName;
    bool changed = false;

    if (ImGui::BeginCombo(pId, previewText.c_str()))
    {
        const bool mergedSelected = trimCopy(selectedModelName).empty();

        if (ImGui::Selectable("<Merged Scene>", mergedSelected))
        {
            selectedModelName.clear();
            changed = true;
        }

        if (mergedSelected)
        {
            ImGui::SetItemDefaultFocus();
        }

        for (const ModelImportInspectionState::Entry &entry : state.entries)
        {
            const bool selected = toLowerCopy(trimCopy(entry.name)) == toLowerCopy(trimCopy(selectedModelName));

            if (ImGui::Selectable(entry.name.c_str(), selected))
            {
                selectedModelName = entry.name;
                changed = true;
            }

            if (selected)
            {
                ImGui::SetItemDefaultFocus();
            }
        }

        ImGui::EndCombo();
    }

    return changed;
}

void EditorMainWindow::renderImportedModelInspectionTable(
    const char *pId,
    const ModelImportInspectionState &state,
    std::string &selectedModelName,
    float height) const
{
    if (state.entries.empty())
    {
        return;
    }

    if (!ImGui::BeginChild(pId, ImVec2(0.0f, height), ImGuiChildFlags_Borders))
    {
        ImGui::EndChild();
        return;
    }

    ImGui::PushID(pId);

    if (ImGui::BeginTable(
            "ImportedModelInspectionTable",
            4,
            ImGuiTableFlags_SizingStretchProp | ImGuiTableFlags_RowBg | ImGuiTableFlags_ScrollY))
    {
        ImGui::TableSetupColumn("Mesh", ImGuiTableColumnFlags_WidthStretch, 0.48f);
        ImGui::TableSetupColumn("Verts", ImGuiTableColumnFlags_WidthStretch, 0.17f);
        ImGui::TableSetupColumn("Faces", ImGuiTableColumnFlags_WidthStretch, 0.17f);
        ImGui::TableSetupColumn("Mats", ImGuiTableColumnFlags_WidthStretch, 0.18f);
        ImGui::TableHeadersRow();

        for (const ModelImportInspectionState::Entry &entry : state.entries)
        {
            const bool selected = toLowerCopy(trimCopy(entry.name)) == toLowerCopy(trimCopy(selectedModelName));
            ImGui::TableNextRow();
            ImGui::TableSetColumnIndex(0);

            if (ImGui::Selectable(entry.name.c_str(), selected, ImGuiSelectableFlags_SpanAllColumns))
            {
                selectedModelName = entry.name;
            }

            ImGui::TableSetColumnIndex(1);
            ImGui::Text("%zu", entry.vertexCount);
            ImGui::TableSetColumnIndex(2);
            ImGui::Text("%zu", entry.faceCount);
            ImGui::TableSetColumnIndex(3);
            ImGui::Text("%zu", entry.materialCount);
        }

        ImGui::EndTable();
    }

    ImGui::PopID();
    ImGui::EndChild();
}

void EditorMainWindow::renderImportedModelInspectionSummary(
    const ModelImportInspectionState &state,
    const std::string &selectedModelName) const
{
    std::optional<ModelImportInspectionState::Entry> mergedEntry;
    const ModelImportInspectionState::Entry *pEntry = findImportedModelInspectionEntry(state, selectedModelName);

    if (pEntry == nullptr)
    {
        mergedEntry = mergedImportedModelInspectionEntry(state);
        pEntry = mergedEntry ? &*mergedEntry : nullptr;
    }

    if (pEntry == nullptr)
    {
        return;
    }

    ImGui::TextDisabled("Preview Target");
    ImGui::PushID(pEntry->name.c_str());

    if (beginInspectorPropertyTable("ImportedModelInspectionSummary"))
    {
        renderInspectorReadOnlyField("Name", pEntry->name);
        renderInspectorReadOnlyField("Vertices", std::to_string(pEntry->vertexCount));
        renderInspectorReadOnlyField("Faces", std::to_string(pEntry->faceCount));
        renderInspectorReadOnlyField("Materials", std::to_string(pEntry->materialCount));
        renderInspectorReadOnlyField(
            "Bounds Min",
            std::to_string(static_cast<int>(std::floor(pEntry->minX))) + ", "
                + std::to_string(static_cast<int>(std::floor(pEntry->minY))) + ", "
                + std::to_string(static_cast<int>(std::floor(pEntry->minZ))));
        renderInspectorReadOnlyField(
            "Bounds Max",
            std::to_string(static_cast<int>(std::ceil(pEntry->maxX))) + ", "
                + std::to_string(static_cast<int>(std::ceil(pEntry->maxY))) + ", "
                + std::to_string(static_cast<int>(std::ceil(pEntry->maxZ))));
        renderInspectorReadOnlyField(
            "Size",
            std::to_string(static_cast<int>(std::ceil(pEntry->maxX - pEntry->minX))) + " x "
                + std::to_string(static_cast<int>(std::ceil(pEntry->maxY - pEntry->minY))) + " x "
                + std::to_string(static_cast<int>(std::ceil(pEntry->maxZ - pEntry->minZ))));
        ImGui::EndTable();
    }

    ImGui::PopID();
}

void EditorMainWindow::renderModelImportModal(EditorSession &session)
{
    if (m_openImportNewBModelModal)
    {
        m_showImportNewBModelWindow = true;
        m_openImportNewBModelModal = false;
    }

    if (!m_showImportNewBModelWindow)
    {
        return;
    }

    const ImGuiViewport *pViewport = ImGui::GetMainViewport();
    ImGui::SetNextWindowPos(
        ImVec2(
            pViewport->WorkPos.x + pViewport->WorkSize.x * 0.5f,
            pViewport->WorkPos.y + pViewport->WorkSize.y * 0.5f),
        ImGuiCond_Appearing,
        ImVec2(0.5f, 0.5f));
    ImGui::SetNextWindowSize(ImVec2(900.0f, 0.0f), ImGuiCond_FirstUseEver);
    bool keepImportWindowOpen = m_showImportNewBModelWindow;

    if (!ImGui::Begin(
            "Import New BModel",
            &keepImportWindowOpen,
            ImGuiWindowFlags_NoDocking | ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_AlwaysAutoResize))
    {
        ImGui::End();
        m_showImportNewBModelWindow = keepImportWindowOpen;
        return;
    }

    m_showImportNewBModelWindow = keepImportWindowOpen;

    if (m_closeImportNewBModelModal)
    {
        m_closeImportNewBModelModal = false;
        m_showImportNewBModelWindow = false;
        ImGui::End();
        return;
    }

    ImGui::TextUnformatted("Import a new outdoor bmodel from an OBJ, glTF, or GLB file.");
    ImGui::Separator();
    const bool canSplitByMesh = canSplitImportedModelPathByMesh(m_globalBModelImportPath);
    const ModelImportInspectionState &inspection =
        ensureModelImportInspection(m_globalBModelImportPath, m_globalBModelImportInspection);

    if (!trimCopy(m_globalBModelImportSelectedMeshName).empty())
    {
        bool foundSelectedMesh = false;

        for (const ModelImportInspectionState::Entry &entry : inspection.entries)
        {
            if (toLowerCopy(trimCopy(entry.name)) == toLowerCopy(trimCopy(m_globalBModelImportSelectedMeshName)))
            {
                foundSelectedMesh = true;
                break;
            }
        }

        if (!foundSelectedMesh)
        {
            m_globalBModelImportSelectedMeshName.clear();
        }
    }

    if (beginInspectorPropertyTable("ImportNewBModelFields"))
    {
        beginInspectorFieldRow("Model Path");
        const float browseButtonWidth = 30.0f;
        ImGui::SetNextItemWidth(-browseButtonWidth - ImGui::GetStyle().ItemSpacing.x);
        ImGui::InputText("##GlobalBModelImportPath", m_globalBModelImportPath, sizeof(m_globalBModelImportPath));
        ImGui::SameLine();

        if (ImGui::Button("...", ImVec2(browseButtonWidth, 0.0f)))
        {
            openModelFileBrowser(ModelImportTarget::ImportNewBModel, m_globalBModelImportPath);
        }

        beginInspectorFieldRow("Import Scale");
        ImGui::InputFloat("##GlobalBModelImportScale", &m_globalBModelImportScale, 0.1f, 1.0f, "%.3f");

        std::string defaultTextureName = m_globalBModelImportDefaultTexture;
        const bool texturePickerChanged =
            renderBitmapTextureSelector(session, "Default Texture (Optional)", defaultTextureName);

        beginInspectorFieldRow("Default Texture Raw");
        char defaultTextureBuffer[64] = {};
        std::snprintf(defaultTextureBuffer, sizeof(defaultTextureBuffer), "%s", defaultTextureName.c_str());
        const bool rawTextureChanged = ImGui::InputText(
            "##GlobalBModelImportDefaultTextureRaw",
            defaultTextureBuffer,
            sizeof(defaultTextureBuffer));

        if (rawTextureChanged)
        {
            defaultTextureName = defaultTextureBuffer;
        }

        if (texturePickerChanged || rawTextureChanged)
        {
            std::snprintf(
                m_globalBModelImportDefaultTexture,
                sizeof(m_globalBModelImportDefaultTexture),
                "%s",
                defaultTextureName.c_str());
        }

        beginInspectorFieldRow("Split Meshes");
        ImGui::BeginDisabled(!canSplitByMesh);
        ImGui::Checkbox("##GlobalBModelImportSplitByMesh", &m_globalBModelImportSplitByMesh);
        ImGui::EndDisabled();

        beginInspectorFieldRow("Merge Coplanar");
        ImGui::Checkbox("##GlobalBModelImportMergeCoplanarFaces", &m_globalBModelImportMergeCoplanarFaces);

        if (canSplitByMesh)
        {
            beginInspectorFieldRow("Source Mesh");
            ImGui::BeginDisabled(m_globalBModelImportSplitByMesh || inspection.entries.empty());
            renderImportedModelSelector(
                "##GlobalBModelImportSourceMesh",
                inspection,
                m_globalBModelImportSelectedMeshName);
            ImGui::EndDisabled();
        }

        ImGui::EndTable();
    }

    if (canSplitByMesh)
    {
        if (!inspection.errorMessage.empty())
        {
            ImGui::TextColored(colorFromRgb(0xE7A46C), "%s", inspection.errorMessage.c_str());
        }
        else
        {
            ImGui::TextDisabled("%s", importedModelSummaryText(inspection.entries.size()).c_str());

            if (!inspection.entries.empty())
            {
                renderImportedModelInspectionTable(
                    "GlobalModelImportMeshes",
                    inspection,
                    m_globalBModelImportSelectedMeshName,
                    110.0f);
                renderImportedModelInspectionSummary(inspection, m_globalBModelImportSelectedMeshName);
            }
        }
    }

    if (ImGui::Button("Import", ImVec2(120.0f, 0.0f)))
    {
        std::string errorMessage;
        const std::string sourceMeshName =
            canSplitByMesh ? m_globalBModelImportSelectedMeshName : std::string();

        if (session.importNewBModelFromModel(
                m_globalBModelImportPath,
                m_globalBModelImportScale,
                m_globalBModelImportDefaultTexture,
                sourceMeshName,
                m_globalBModelImportSplitByMesh,
                m_globalBModelImportMergeCoplanarFaces,
                errorMessage))
        {
            rememberModelImportDirectory(m_globalBModelImportPath);
            m_viewport.setPlacementKind(EditorSelectionKind::BModel);
            m_showImportNewBModelWindow = false;
            m_showModelBrowserWindow = false;
        }
        else
        {
            session.logError(errorMessage);
        }
    }

    ImGui::SameLine();

    if (ImGui::Button("Cancel", ImVec2(120.0f, 0.0f)))
    {
        m_showImportNewBModelWindow = false;
        m_showModelBrowserWindow = false;
    }

    ImGui::End();
}

void EditorMainWindow::openModelFileBrowser(ModelImportTarget target, const char *pCurrentPath) const
{
    m_modelBrowserTarget = target;
    m_modelBrowserFilter[0] = '\0';
    const std::string currentPath = trimCopy(pCurrentPath != nullptr ? pCurrentPath : "");

    if (!currentPath.empty())
    {
        const std::filesystem::path path = std::filesystem::path(currentPath);
        const std::filesystem::path directory = std::filesystem::is_directory(path) ? path : path.parent_path();

        if (!directory.empty() && std::filesystem::exists(directory))
        {
            m_modelBrowserDirectory = directory;
        }
    }

    if (m_modelBrowserDirectory.empty() || !std::filesystem::exists(m_modelBrowserDirectory))
    {
        m_modelBrowserDirectory = std::filesystem::current_path();
    }

    m_openModelBrowserPopup = true;
}

void EditorMainWindow::assignModelBrowserSelectionPath(const std::filesystem::path &path) const
{
    const std::string normalizedPath = path.lexically_normal().string();

    if (m_modelBrowserTarget == ModelImportTarget::ReplaceSelectedBModel)
    {
        std::snprintf(m_bmodelImportPath, sizeof(m_bmodelImportPath), "%s", normalizedPath.c_str());
    }
    else if (m_modelBrowserTarget == ModelImportTarget::ImportNewBModel)
    {
        std::snprintf(m_globalBModelImportPath, sizeof(m_globalBModelImportPath), "%s", normalizedPath.c_str());
    }

    rememberModelImportDirectory(normalizedPath.c_str());
}

void EditorMainWindow::rememberModelImportDirectory(const char *pPath) const
{
    const std::string pathText = trimCopy(pPath != nullptr ? pPath : "");

    if (pathText.empty())
    {
        return;
    }

    const std::filesystem::path path(pathText);
    const std::filesystem::path directory = std::filesystem::is_directory(path) ? path : path.parent_path();

    if (!directory.empty() && std::filesystem::exists(directory))
    {
        m_modelBrowserDirectory = directory;
    }
}

void EditorMainWindow::openNewOutdoorMapModal(EditorSession &session)
{
    std::string suggestedMapId = "out16";

    if (const Engine::AssetFileSystem *pAssetFileSystem = session.assetFileSystem())
    {
        const std::vector<std::string> entries = pAssetFileSystem->enumerate("Data/games");
        std::unordered_set<std::string> existingIds;

        for (const std::string &entry : entries)
        {
            if (entry.ends_with(".map.yml"))
            {
                existingIds.insert(toLowerCopy(std::filesystem::path(entry).stem().stem().string()));
            }
            else if (entry.ends_with(".scene.yml"))
            {
                existingIds.insert(toLowerCopy(std::filesystem::path(entry).stem().stem().string()));
            }
            else if (entry.ends_with(".odm"))
            {
                existingIds.insert(toLowerCopy(std::filesystem::path(entry).stem().string()));
            }
        }

        for (int index = 1; index < 1000; ++index)
        {
            char candidate[32] = {};
            std::snprintf(candidate, sizeof(candidate), "out%02d", index);

            if (!existingIds.contains(candidate))
            {
                suggestedMapId = candidate;
                break;
            }
        }
    }

    std::snprintf(m_newOutdoorMapId, sizeof(m_newOutdoorMapId), "%s", suggestedMapId.c_str());
    std::snprintf(m_newOutdoorDisplayName, sizeof(m_newOutdoorDisplayName), "%s", suggestedMapId.c_str());
    m_newOutdoorMapSizePreset = 0;
    m_newOutdoorTilesetPreset = static_cast<int>(EditorOutdoorMapTilesetPreset::Grassland);
    m_openNewOutdoorMapModal = true;
    m_closeNewOutdoorMapModal = false;
}

void EditorMainWindow::openOpenOutdoorMapModal() const
{
    m_openOutdoorMapFilter[0] = '\0';
    m_openOpenOutdoorMapModal = true;
}

void EditorMainWindow::openMapPackageActionModal(EditorSession &session, MapPackageAction action) const
{
    m_mapPackageAction = action;
    std::string suggestedMapId = "out16";
    std::string suggestedDisplayName = "out16";

    if (const Engine::AssetFileSystem *pAssetFileSystem = session.assetFileSystem())
    {
        const std::string currentMapId =
            session.hasDocument() ? std::filesystem::path(session.document().displayName()).stem().string() : "out16";
        suggestedMapId = suggestAvailableMapId(*pAssetFileSystem, currentMapId + "_copy");
        suggestedDisplayName = session.hasDocument()
            ? session.document().outdoorMapPackageMetadata().displayName
            : suggestedMapId;
    }

    std::snprintf(m_mapPackageActionMapId, sizeof(m_mapPackageActionMapId), "%s", suggestedMapId.c_str());
    std::snprintf(
        m_mapPackageActionDisplayName,
        sizeof(m_mapPackageActionDisplayName),
        "%s",
        suggestedDisplayName.c_str());
    m_openMapPackageActionModal = true;
}

void EditorMainWindow::openDeleteCurrentMapModal() const
{
    m_openDeleteCurrentMapModal = true;
}

void EditorMainWindow::renderNewOutdoorMapModal(EditorSession &session)
{
    if (m_openNewOutdoorMapModal)
    {
        ImGui::OpenPopup("New Outdoor Map");
        m_openNewOutdoorMapModal = false;
    }

    if (!ImGui::BeginPopupModal("New Outdoor Map", nullptr, ImGuiWindowFlags_AlwaysAutoResize))
    {
        return;
    }

    if (m_closeNewOutdoorMapModal)
    {
        m_closeNewOutdoorMapModal = false;
        ImGui::CloseCurrentPopup();
        ImGui::EndPopup();
        return;
    }

    ImGui::TextUnformatted("Create a new source-native outdoor map package.");
    ImGui::Separator();

    if (beginInspectorPropertyTable("NewOutdoorMapFields"))
    {
        beginInspectorFieldRow("Map Id");
        ImGui::InputText("##NewOutdoorMapId", m_newOutdoorMapId, sizeof(m_newOutdoorMapId));

        beginInspectorFieldRow("Display Name");
        ImGui::InputText("##NewOutdoorDisplayName", m_newOutdoorDisplayName, sizeof(m_newOutdoorDisplayName));

        beginInspectorFieldRow("Map Size");
        const char *sizeLabel = "Classic 128x128";
        ImGui::SetNextItemWidth(220.0f);
        ImGui::Combo("##NewOutdoorMapSize", &m_newOutdoorMapSizePreset, &sizeLabel, 1);

        beginInspectorFieldRow("Tileset");
        const char *tilesetPreview = outdoorTilesetPresetLabel(
            static_cast<EditorOutdoorMapTilesetPreset>(m_newOutdoorTilesetPreset));

        if (ImGui::BeginCombo("##NewOutdoorTilesetPreset", tilesetPreview))
        {
            for (int presetIndex = 0; presetIndex < 3; ++presetIndex)
            {
                const EditorOutdoorMapTilesetPreset preset = static_cast<EditorOutdoorMapTilesetPreset>(presetIndex);
                const bool selected = presetIndex == m_newOutdoorTilesetPreset;

                if (ImGui::Selectable(outdoorTilesetPresetLabel(preset), selected))
                {
                    m_newOutdoorTilesetPreset = presetIndex;
                }

                if (selected)
                {
                    ImGui::SetItemDefaultFocus();
                }
            }

            ImGui::EndCombo();
        }

        ImGui::EndTable();
    }

    ImGui::TextDisabled("Creates .map.yml, .scene.yml, .geometry.yml, .terrain.yml, and a compiled ODM.");

    if (ImGui::Button("Create", ImVec2(120.0f, 0.0f)))
    {
        std::string errorMessage;

        if (session.createNewOutdoorMap(
                m_newOutdoorMapId,
                m_newOutdoorDisplayName,
                static_cast<EditorOutdoorMapTilesetPreset>(m_newOutdoorTilesetPreset),
                errorMessage))
        {
            setStatusMessage(StatusMessageKind::Success, "Created new outdoor map.");
            m_closeNewOutdoorMapModal = true;
        }
        else
        {
            session.logError(errorMessage);
            setStatusMessage(StatusMessageKind::Error, errorMessage);
        }
    }

    ImGui::SameLine();

    if (ImGui::Button("Cancel", ImVec2(120.0f, 0.0f)))
    {
        ImGui::CloseCurrentPopup();
    }

    ImGui::EndPopup();
}

void EditorMainWindow::renderOpenOutdoorMapModal(EditorSession &session)
{
    if (m_openOpenOutdoorMapModal)
    {
        ImGui::OpenPopup("Open Outdoor Map");
        m_openOpenOutdoorMapModal = false;
    }

    if (!ImGui::BeginPopupModal("Open Outdoor Map", nullptr, ImGuiWindowFlags_AlwaysAutoResize))
    {
        return;
    }

    const Engine::AssetFileSystem *pAssetFileSystem = session.assetFileSystem();

    if (pAssetFileSystem == nullptr)
    {
        ImGui::TextUnformatted("Asset file system is not initialized.");

        if (ImGui::Button("Close", ImVec2(120.0f, 0.0f)))
        {
            ImGui::CloseCurrentPopup();
        }

        ImGui::EndPopup();
        return;
    }

    const std::vector<std::string> mapFiles = collectOutdoorMapFileNames(*pAssetFileSystem);
    ImGui::TextUnformatted("Open an outdoor source package or legacy scene map.");
    ImGui::Separator();
    ImGui::SetNextItemWidth(320.0f);
    ImGui::InputTextWithHint("##OpenOutdoorMapFilter", "Filter maps", m_openOutdoorMapFilter, sizeof(m_openOutdoorMapFilter));
    const std::string filter = toLowerCopy(trimCopy(m_openOutdoorMapFilter));

    if (ImGui::BeginChild("OpenOutdoorMapList", ImVec2(520.0f, 320.0f), ImGuiChildFlags_Borders))
    {
        bool anyVisible = false;

        for (const std::string &mapFileName : mapFiles)
        {
            if (!filter.empty() && toLowerCopy(mapFileName).find(filter) == std::string::npos)
            {
                continue;
            }

            anyVisible = true;

            if (ImGui::Selectable(mapFileName.c_str(), false))
            {
                std::string errorMessage;

                if (session.openOutdoorMap(mapFileName, errorMessage))
                {
                    setStatusMessage(StatusMessageKind::Success, "Opened " + mapFileName + ".");
                    ImGui::CloseCurrentPopup();
                    break;
                }

                session.logError(errorMessage);
                setStatusMessage(StatusMessageKind::Error, errorMessage);
            }
        }

        if (!anyVisible)
        {
            ImGui::TextUnformatted("No outdoor maps match the current filter.");
        }
    }
    ImGui::EndChild();

    if (ImGui::Button("Close", ImVec2(120.0f, 0.0f)))
    {
        ImGui::CloseCurrentPopup();
    }

    ImGui::EndPopup();
}

void EditorMainWindow::renderMapPackageActionModal(EditorSession &session)
{
    if (m_openMapPackageActionModal)
    {
        ImGui::OpenPopup("Map Package Action");
        m_openMapPackageActionModal = false;
    }

    if (!ImGui::BeginPopupModal("Map Package Action", nullptr, ImGuiWindowFlags_AlwaysAutoResize))
    {
        return;
    }

    const char *pTitle =
        m_mapPackageAction == MapPackageAction::Duplicate ? "Duplicate current outdoor map package." : "Save current outdoor map to a new package.";
    ImGui::TextUnformatted(pTitle);
    ImGui::Separator();

    if (beginInspectorPropertyTable("MapPackageActionFields"))
    {
        beginInspectorFieldRow("Map Id");
        ImGui::InputText("##MapPackageActionMapId", m_mapPackageActionMapId, sizeof(m_mapPackageActionMapId));

        beginInspectorFieldRow("Display Name");
        ImGui::InputText(
            "##MapPackageActionDisplayName",
            m_mapPackageActionDisplayName,
            sizeof(m_mapPackageActionDisplayName));

        ImGui::EndTable();
    }

    const char *pConfirmLabel = m_mapPackageAction == MapPackageAction::Duplicate ? "Duplicate" : "Save As";

    if (ImGui::Button(pConfirmLabel, ImVec2(120.0f, 0.0f)))
    {
        std::string errorMessage;
        bool succeeded = false;

        if (m_mapPackageAction == MapPackageAction::Duplicate)
        {
            succeeded = session.duplicateActiveDocumentAs(
                m_mapPackageActionMapId,
                m_mapPackageActionDisplayName,
                errorMessage);
        }
        else
        {
            succeeded = session.saveActiveDocumentAs(
                m_mapPackageActionMapId,
                m_mapPackageActionDisplayName,
                errorMessage);
        }

        if (succeeded)
        {
            setStatusMessage(
                StatusMessageKind::Success,
                std::string(pConfirmLabel) + " complete: " + session.document().displayName());
            ImGui::CloseCurrentPopup();
        }
        else
        {
            session.logError(errorMessage);
            setStatusMessage(StatusMessageKind::Error, errorMessage);
        }
    }

    ImGui::SameLine();

    if (ImGui::Button("Cancel", ImVec2(120.0f, 0.0f)))
    {
        ImGui::CloseCurrentPopup();
    }

    ImGui::EndPopup();
}

void EditorMainWindow::renderDeleteCurrentMapModal(EditorSession &session)
{
    if (m_openDeleteCurrentMapModal)
    {
        ImGui::OpenPopup("Delete Current Map");
        m_openDeleteCurrentMapModal = false;
    }

    if (!ImGui::BeginPopupModal("Delete Current Map", nullptr, ImGuiWindowFlags_AlwaysAutoResize))
    {
        return;
    }

    if (!session.hasDocument())
    {
        ImGui::TextUnformatted("No map is currently open.");
    }
    else
    {
        const EditorDocument &document = session.document();
        ImGui::Text("Delete current map package '%s'?", document.displayName().c_str());
        ImGui::TextWrapped("This removes the current map files from Data/games and then opens another map.");
        ImGui::Separator();
        ImGui::Text("Runtime: %s", document.geometryPhysicalPath().filename().string().c_str());
        ImGui::Text("Scene: %s", document.scenePhysicalPath().filename().string().c_str());
        ImGui::Text("Package: %s", document.mapPackagePhysicalPath().filename().string().c_str());
        ImGui::Text("Geometry: %s", document.geometryMetadataPhysicalPath().filename().string().c_str());
        ImGui::Text("Terrain: %s", document.terrainMetadataPhysicalPath().filename().string().c_str());
    }

    if (ImGui::Button("Delete", ImVec2(120.0f, 0.0f)))
    {
        std::string errorMessage;

        if (session.deleteActiveDocumentPackage(errorMessage))
        {
            setStatusMessage(StatusMessageKind::Success, "Deleted current map package.");
            ImGui::CloseCurrentPopup();
        }
        else
        {
            session.logError(errorMessage);
            setStatusMessage(StatusMessageKind::Error, errorMessage);
        }
    }

    ImGui::SameLine();

    if (ImGui::Button("Cancel", ImVec2(120.0f, 0.0f)))
    {
        ImGui::CloseCurrentPopup();
    }

    ImGui::EndPopup();
}

void EditorMainWindow::renderModelFileBrowserPopup(EditorSession &session)
{
    if (m_openModelBrowserPopup)
    {
        m_showModelBrowserWindow = true;
        m_openModelBrowserPopup = false;
        ImGui::SetNextWindowFocus();
    }

    if (!m_showModelBrowserWindow)
    {
        return;
    }

    const ImGuiViewport *pViewport = ImGui::GetMainViewport();
    ImGui::SetNextWindowPos(
        ImVec2(
            pViewport->WorkPos.x + pViewport->WorkSize.x * 0.5f,
            pViewport->WorkPos.y + pViewport->WorkSize.y * 0.5f),
        ImGuiCond_Appearing,
        ImVec2(0.5f, 0.5f));
    ImGui::SetNextWindowSize(ImVec2(820.0f, 520.0f), ImGuiCond_FirstUseEver);
    bool keepBrowserWindowOpen = m_showModelBrowserWindow;

    if (!ImGui::Begin(
            "Model Browser",
            &keepBrowserWindowOpen,
            ImGuiWindowFlags_NoDocking | ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_AlwaysAutoResize))
    {
        ImGui::End();
        m_showModelBrowserWindow = keepBrowserWindowOpen;
        return;
    }

    m_showModelBrowserWindow = keepBrowserWindowOpen;

    if (m_modelBrowserDirectory.empty() || !std::filesystem::exists(m_modelBrowserDirectory))
    {
        m_modelBrowserDirectory = std::filesystem::current_path();
    }

    ImGui::TextWrapped("Directory: %s", m_modelBrowserDirectory.string().c_str());
    ImGui::InputText("Filter", m_modelBrowserFilter, sizeof(m_modelBrowserFilter));

    if (ImGui::Button("Up", ImVec2(90.0f, 0.0f)))
    {
        if (m_modelBrowserDirectory.has_parent_path())
        {
            m_modelBrowserDirectory = m_modelBrowserDirectory.parent_path();
        }
    }

    ImGui::SameLine();

    if (ImGui::Button("Refresh", ImVec2(90.0f, 0.0f)))
    {
    }

    std::vector<std::filesystem::path> directories;
    std::vector<std::filesystem::path> modelFiles;
    const std::string normalizedFilter = toLowerCopy(trimCopy(m_modelBrowserFilter));

    try
    {
        for (const std::filesystem::directory_entry &entry :
             std::filesystem::directory_iterator(m_modelBrowserDirectory))
        {
            const std::filesystem::path path = entry.path();
            const std::string fileName = path.filename().string();

            if (entry.is_directory())
            {
                if (!normalizedFilter.empty() && toLowerCopy(fileName).find(normalizedFilter) == std::string::npos)
                {
                    continue;
                }

                directories.push_back(path);
            }
            else
            {
                const std::string extension = toLowerCopy(path.extension().string());

                if (extension != ".obj" && extension != ".gltf" && extension != ".glb")
                {
                    continue;
                }

                std::error_code existsError;

                if (!std::filesystem::exists(path, existsError) || std::filesystem::is_directory(path, existsError))
                {
                    continue;
                }

                if (!normalizedFilter.empty() && toLowerCopy(fileName).find(normalizedFilter) == std::string::npos)
                {
                    continue;
                }

                modelFiles.push_back(path);
            }
        }
    }
    catch (const std::filesystem::filesystem_error &)
    {
    }

    std::sort(directories.begin(), directories.end());
    std::sort(modelFiles.begin(), modelFiles.end());

    if (ImGui::BeginChild("ModelBrowserEntries", ImVec2(760.0f, 420.0f), ImGuiChildFlags_Borders))
    {
        for (const std::filesystem::path &path : directories)
        {
            const std::string label = "[DIR] " + path.filename().string();

            if (ImGui::Selectable(label.c_str(), false))
            {
                m_modelBrowserDirectory = path;
            }
        }

        for (const std::filesystem::path &path : modelFiles)
        {
            const std::string label = path.filename().string();

            if (ImGui::Selectable(label.c_str(), false))
            {
                assignModelBrowserSelectionPath(path);
                m_showModelBrowserWindow = false;
            }
        }
    }

    ImGui::EndChild();

    if (ImGui::Button("Cancel", ImVec2(120.0f, 0.0f)))
    {
        m_showModelBrowserWindow = false;
    }

    ImGui::End();
}

void EditorMainWindow::duplicateSelected(EditorSession &session)
{
    std::string errorMessage;
    const EditorSelectionKind duplicatedKind = session.selection().kind;

    if (!session.duplicateSelectedObject(errorMessage))
    {
        session.logError(errorMessage);
        return;
    }

    if (duplicatedKind == EditorSelectionKind::BModel)
    {
        m_viewport.setPlacementKind(EditorSelectionKind::BModel);
    }
}

void EditorMainWindow::deleteSelected(EditorSession &session)
{
    std::string errorMessage;

    if (!session.deleteSelectedObject(errorMessage))
    {
        session.logError(errorMessage);
        return;
    }

    if (session.selection().kind != EditorSelectionKind::BModel && m_viewport.placementKind() == EditorSelectionKind::BModel)
    {
        m_viewport.setPlacementKind(EditorSelectionKind::None);
    }
}

void EditorMainWindow::renderSceneOutliner(EditorSession &session)
{
    ImGui::SetNextWindowDockID(editorDockspaceId(), ImGuiCond_FirstUseEver);

    if (!ImGui::Begin("Scene"))
    {
        ImGui::End();
        return;
    }

    if (!session.hasDocument())
    {
        ImGui::TextUnformatted("No document loaded.");
        ImGui::End();
        return;
    }

    const Game::OutdoorSceneData &sceneData = session.document().outdoorSceneData();
    bool pendingDuplicate = false;
    bool pendingDelete = false;
    const auto focusOutlinerSelection = [this, &session](EditorSelectionKind kind, size_t index)
    {
        if (ImGui::IsItemHovered() && ImGui::IsMouseDoubleClicked(ImGuiMouseButton_Left))
        {
            session.select(kind, index);
            m_viewport.focusSelection(session.document(), {kind, index});
        }
    };

    ImGui::PushStyleColor(ImGuiCol_Header, colorFromRgb(0x2B2318));
    ImGui::PushStyleColor(ImGuiCol_HeaderHovered, colorFromRgb(0x3A2F1F));
    ImGui::PushStyleColor(ImGuiCol_HeaderActive, colorFromRgb(0x5B4323));
    ImGui::PushStyleColor(ImGuiCol_ChildBg, colorFromRgb(0x171B1F));
    ImGui::PushStyleColor(ImGuiCol_Border, colorFromRgb(0x313944));
    if (ImGui::BeginChild("SceneHeaderCard", ImVec2(0.0f, 38.0f), ImGuiChildFlags_Borders))
    {
        ImGui::SetNextItemWidth(-1.0f);
        ImGui::InputTextWithHint("##SceneFilter", "Search scene...", m_sceneFilter, sizeof(m_sceneFilter));
    }
    ImGui::EndChild();
    ImGui::PopStyleColor(5);
    ImGui::Spacing();

    ImGui::PushStyleColor(ImGuiCol_Header, colorFromRgb(0x3C2D18));
    ImGui::PushStyleColor(ImGuiCol_HeaderHovered, colorFromRgb(0x4E3B21));
    ImGui::PushStyleColor(ImGuiCol_HeaderActive, colorFromRgb(0x654A27));
    ImGui::PushStyleColor(ImGuiCol_TextSelectedBg, ImVec4(0.34f, 0.24f, 0.12f, 0.72f));

    const bool summarySelected = session.selection().kind == EditorSelectionKind::Summary;

    if (matchesSceneFilter(m_sceneFilter, "Level Summary") && ImGui::Selectable("Level Summary", summarySelected))
    {
        session.select(EditorSelectionKind::Summary);
    }

    if (matchesSceneFilter(m_sceneFilter, "Environment")
        && ImGui::Selectable("Environment", session.selection().kind == EditorSelectionKind::Environment))
    {
        session.select(EditorSelectionKind::Environment);
    }

    if (matchesSceneFilter(m_sceneFilter, "Terrain Overrides")
        && ImGui::Selectable("Terrain Overrides", session.selection().kind == EditorSelectionKind::Terrain))
    {
        session.select(EditorSelectionKind::Terrain, std::numeric_limits<size_t>::max());
    }

    const std::string terrainOverrideLabel =
        "Terrain Override Cells (" + std::to_string(sceneData.terrainAttributeOverrides.size()) + ")";

    if (ImGui::TreeNodeEx(terrainOverrideLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
    {
        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(sceneData.terrainAttributeOverrides.size()));

        while (clipper.Step())
        {
            for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
            {
                const Game::OutdoorSceneTerrainAttributeOverride &overrideEntry =
                    sceneData.terrainAttributeOverrides[itemIndex];
                const size_t flatIndex = terrainCellFlatIndex(overrideEntry.x, overrideEntry.y);
                const bool isSelected =
                    session.selection().kind == EditorSelectionKind::Terrain
                    && session.selection().index == flatIndex;
                const std::string label =
                    "(" + std::to_string(overrideEntry.x) + ", " + std::to_string(overrideEntry.y) + ")";

                if (!matchesSceneFilter(m_sceneFilter, label))
                {
                    continue;
                }

                if (ImGui::Selectable(label.c_str(), isSelected))
                {
                    session.select(EditorSelectionKind::Terrain, flatIndex);
                }

                focusOutlinerSelection(EditorSelectionKind::Terrain, flatIndex);
            }
        }

        ImGui::TreePop();
    }

    const Game::OutdoorMapData &outdoorGeometry = session.document().outdoorGeometry();
    const std::string bmodelsLabel = "BModels (" + std::to_string(outdoorGeometry.bmodels.size()) + ")";

    if (ImGui::TreeNodeEx(bmodelsLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
    {
        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(outdoorGeometry.bmodels.size()));

        while (clipper.Step())
        {
            for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
            {
                const size_t bmodelIndex = static_cast<size_t>(itemIndex);
                const Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];
                const std::string label =
                    "BModel " + std::to_string(bmodelIndex)
                    + " (" + std::to_string(bmodel.faces.size()) + " faces)";

                if (!matchesSceneFilter(m_sceneFilter, label))
                {
                    continue;
                }

                const bool isSelected =
                    session.selection().kind == EditorSelectionKind::BModel && session.selection().index == bmodelIndex;

                if (ImGui::Selectable(label.c_str(), isSelected, ImGuiSelectableFlags_SpanAvailWidth))
                {
                    session.select(EditorSelectionKind::BModel, bmodelIndex);
                }

                if (ImGui::IsItemHovered() && ImGui::IsMouseDoubleClicked(ImGuiMouseButton_Left))
                {
                    session.select(EditorSelectionKind::BModel, bmodelIndex);
                    m_viewport.focusBModel(session.document(), bmodelIndex);
                }

                if (ImGui::BeginPopupContextItem())
                {
                    session.select(EditorSelectionKind::BModel, bmodelIndex);
                    pendingDuplicate = ImGui::MenuItem("Duplicate");
                    pendingDelete = ImGui::MenuItem("Delete");
                    ImGui::EndPopup();
                }
            }
        }

        ImGui::TreePop();
    }

    const std::string entitiesLabel = "Entities (" + std::to_string(sceneData.entities.size()) + ")";

    if (ImGui::TreeNodeEx(entitiesLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
    {
        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(sceneData.entities.size()));

        while (clipper.Step())
        {
            for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
            {
                const size_t entityIndex = static_cast<size_t>(itemIndex);
                const bool isSelected =
                    session.selection().kind == EditorSelectionKind::Entity
                    && session.selection().index == entityIndex;
                const Game::OutdoorSceneEntity &entity = sceneData.entities[entityIndex];
                std::string label = entity.entity.name.empty()
                    ? "Entity " + std::to_string(entity.entityIndex)
                    : entity.entity.name + "##entity" + std::to_string(entity.entityIndex);

                if (entity.entity.eventIdPrimary != 0 || entity.entity.eventIdSecondary != 0)
                {
                    label += " [evt]";
                }

                if (!matchesSceneFilter(m_sceneFilter, label))
                {
                    continue;
                }

                if (ImGui::Selectable(label.c_str(), isSelected))
                {
                    session.select(EditorSelectionKind::Entity, entityIndex);
                }

                focusOutlinerSelection(EditorSelectionKind::Entity, entityIndex);

                if (ImGui::BeginPopupContextItem())
                {
                    session.select(EditorSelectionKind::Entity, entityIndex);
                    pendingDuplicate = ImGui::MenuItem("Duplicate");
                    pendingDelete = ImGui::MenuItem("Delete");
                    ImGui::EndPopup();
                }
            }
        }

        ImGui::TreePop();
    }

    const std::string spawnsLabel = "Spawns (" + std::to_string(sceneData.spawns.size()) + ")";

    if (ImGui::TreeNodeEx(spawnsLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
    {
        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(sceneData.spawns.size()));

        while (clipper.Step())
        {
            for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
            {
                const size_t spawnIndex = static_cast<size_t>(itemIndex);
                const bool isSelected =
                    session.selection().kind == EditorSelectionKind::Spawn
                    && session.selection().index == spawnIndex;
                const Game::OutdoorSceneSpawn &spawn = sceneData.spawns[spawnIndex];
                const Game::MapStatsEntry *pMapEntry = session.currentMapStatsEntry();
                const Game::SpawnPreview preview = pMapEntry != nullptr
                    ? Game::SpawnPreviewResolver::describe(
                        *pMapEntry,
                        &session.monsterTable(),
                        spawn.spawn.typeId,
                        spawn.spawn.index,
                        spawn.spawn.attributes,
                        spawn.spawn.group)
                    : Game::SpawnPreview {};
                std::string label = "Spawn " + std::to_string(spawn.spawnIndex);

                if (!preview.summary.empty())
                {
                    label += " - " + preview.summary;
                }

                if (!matchesSceneFilter(m_sceneFilter, label))
                {
                    continue;
                }

                if (ImGui::Selectable(label.c_str(), isSelected))
                {
                    session.select(EditorSelectionKind::Spawn, spawnIndex);
                }

                focusOutlinerSelection(EditorSelectionKind::Spawn, spawnIndex);

                if (ImGui::BeginPopupContextItem())
                {
                    session.select(EditorSelectionKind::Spawn, spawnIndex);
                    pendingDuplicate = ImGui::MenuItem("Duplicate");
                    pendingDelete = ImGui::MenuItem("Delete");
                    ImGui::EndPopup();
                }
            }
        }

        ImGui::TreePop();
    }

    const std::string actorsLabel = "Actors (" + std::to_string(sceneData.initialState.actors.size()) + ")";

    if (ImGui::TreeNodeEx(actorsLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
    {
        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(sceneData.initialState.actors.size()));

        while (clipper.Step())
        {
            for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
            {
                const size_t actorIndex = static_cast<size_t>(itemIndex);
                const bool isSelected =
                    session.selection().kind == EditorSelectionKind::Actor
                    && session.selection().index == actorIndex;
                const Game::MapDeltaActor &actor = sceneData.initialState.actors[actorIndex];
                const std::string label = actorDisplayLabel(
                    &session.monsterTable(),
                    actor,
                    actorIndex)
                    + "##actor" + std::to_string(actorIndex);

                if (!matchesSceneFilter(m_sceneFilter, label))
                {
                    continue;
                }

                if (ImGui::Selectable(label.c_str(), isSelected))
                {
                    session.select(EditorSelectionKind::Actor, actorIndex);
                }

                focusOutlinerSelection(EditorSelectionKind::Actor, actorIndex);

                if (ImGui::BeginPopupContextItem())
                {
                    session.select(EditorSelectionKind::Actor, actorIndex);
                    pendingDuplicate = ImGui::MenuItem("Duplicate");
                    pendingDelete = ImGui::MenuItem("Delete");
                    ImGui::EndPopup();
                }
            }
        }

        ImGui::TreePop();
    }

    const std::string objectsLabel =
        "Sprite Objects (" + std::to_string(sceneData.initialState.spriteObjects.size()) + ")";

    if (ImGui::TreeNodeEx(objectsLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
    {
        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(sceneData.initialState.spriteObjects.size()));

        while (clipper.Step())
        {
            for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
            {
                const size_t spriteObjectIndex = static_cast<size_t>(itemIndex);
                const bool isSelected =
                    session.selection().kind == EditorSelectionKind::SpriteObject
                    && session.selection().index == spriteObjectIndex;
                const Game::MapDeltaSpriteObject &spriteObject = sceneData.initialState.spriteObjects[spriteObjectIndex];
                const std::string label =
                    spriteObjectDisplayLabel(spriteObject, spriteObjectIndex)
                    + "##object"
                    + std::to_string(spriteObjectIndex);

                if (!matchesSceneFilter(m_sceneFilter, label))
                {
                    continue;
                }

                if (ImGui::Selectable(label.c_str(), isSelected))
                {
                    session.select(EditorSelectionKind::SpriteObject, spriteObjectIndex);
                }

                focusOutlinerSelection(EditorSelectionKind::SpriteObject, spriteObjectIndex);

                if (ImGui::BeginPopupContextItem())
                {
                    session.select(EditorSelectionKind::SpriteObject, spriteObjectIndex);
                    pendingDuplicate = ImGui::MenuItem("Duplicate");
                    pendingDelete = ImGui::MenuItem("Delete");
                    ImGui::EndPopup();
                }
            }
        }

        ImGui::TreePop();
    }

    const std::string chestsLabel = "Chests (" + std::to_string(sceneData.initialState.chests.size()) + ")";

    if (ImGui::TreeNodeEx(chestsLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
    {
        ImGuiListClipper clipper;
        clipper.Begin(static_cast<int>(sceneData.initialState.chests.size()));

        while (clipper.Step())
        {
            for (int itemIndex = clipper.DisplayStart; itemIndex < clipper.DisplayEnd; ++itemIndex)
            {
                const size_t chestIndex = static_cast<size_t>(itemIndex);
                const bool isSelected =
                    session.selection().kind == EditorSelectionKind::Chest
                    && session.selection().index == chestIndex;
                const Game::MapDeltaChest &chest = sceneData.initialState.chests[chestIndex];
                const Game::ChestEntry *pChestEntry = session.chestTable().get(chest.chestTypeId);
                std::string label = "Chest " + std::to_string(chestIndex);

                if (pChestEntry != nullptr && !pChestEntry->name.empty())
                {
                    label += " - " + pChestEntry->name;
                }

                const std::vector<EditorChestLink> chestLinks = session.findChestLinks(chestIndex);

                if (!chestLinks.empty())
                {
                    label += " [";
                    label += std::to_string(chestLinks.size());
                    label += " opener";
                    if (chestLinks.size() != 1)
                    {
                        label += "s";
                    }
                    label += "]";
                }

                if (!matchesSceneFilter(m_sceneFilter, label))
                {
                    continue;
                }

                if (ImGui::Selectable(label.c_str(), isSelected))
                {
                    session.select(EditorSelectionKind::Chest, chestIndex);
                }

                focusOutlinerSelection(EditorSelectionKind::Chest, chestIndex);
            }
        }

        ImGui::TreePop();
    }

    if (pendingDuplicate)
    {
        duplicateSelected(session);
    }

    if (pendingDelete)
    {
        deleteSelected(session);
    }

    ImGui::PopStyleColor(4);

    ImGui::End();
}

void EditorMainWindow::renderInspector(EditorSession &session)
{
    ImGui::SetNextWindowDockID(editorDockspaceId(), ImGuiCond_FirstUseEver);

    if (!ImGui::Begin("Inspector"))
    {
        ImGui::End();
        return;
    }

    if (!session.hasDocument())
    {
        ImGui::TextUnformatted("No document loaded.");
        ImGui::End();
        return;
    }

    std::pair<std::string, std::string> selectionSummary = inspectorSelectionSummary(session);

    switch (m_viewport.placementKind())
    {
    case EditorSelectionKind::Entity:
        selectionSummary = {"Entity Placement", "Click in the viewport to place a decoration"};
        break;
    case EditorSelectionKind::Spawn:
        selectionSummary = {"Spawn Placement", "Click in the viewport to place a spawn marker"};
        break;
    case EditorSelectionKind::Actor:
        selectionSummary = {"Actor Placement", "Click in the viewport to place an actor"};
        break;
    case EditorSelectionKind::SpriteObject:
        selectionSummary = {"Object Placement", "Click in the viewport to place a sprite object"};
        break;
    case EditorSelectionKind::Terrain:
        selectionSummary = {"Terrain", "Terrain editing tools"};
        break;
    case EditorSelectionKind::None:
    case EditorSelectionKind::Summary:
    case EditorSelectionKind::Environment:
    case EditorSelectionKind::BModel:
    case EditorSelectionKind::InteractiveFace:
    case EditorSelectionKind::Chest:
        break;
    }

    const std::string &selectionTitle = selectionSummary.first;
    const std::string &selectionSubtitle = selectionSummary.second;
    ImGui::PushStyleColor(ImGuiCol_ChildBg, colorFromRgb(0x171B1F));
    ImGui::PushStyleColor(ImGuiCol_Border, colorFromRgb(0x313944));
    if (ImGui::BeginChild("InspectorSelectionHeader", ImVec2(0.0f, 56.0f), ImGuiChildFlags_Borders))
    {
        ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0xF2DEC2));
        ImGui::TextUnformatted(selectionTitle.c_str());
        ImGui::PopStyleColor();

        if (!selectionSubtitle.empty())
        {
            ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0xB5BDC8));
            ImGui::TextUnformatted(selectionSubtitle.c_str());
            ImGui::PopStyleColor();
        }
    }
    ImGui::EndChild();
    ImGui::PopStyleColor(2);
    ImGui::Spacing();

    if (m_viewport.placementKind() == EditorSelectionKind::Entity)
    {
        renderEntityPlacementInspector(session);
        ImGui::End();
        return;
    }

    if (m_viewport.placementKind() == EditorSelectionKind::Spawn)
    {
        renderSpawnPlacementInspector(session);
        ImGui::End();
        return;
    }

    if (m_viewport.placementKind() == EditorSelectionKind::Actor)
    {
        renderActorPlacementInspector(session);
        ImGui::End();
        return;
    }

    if (m_viewport.placementKind() == EditorSelectionKind::SpriteObject)
    {
        renderSpriteObjectPlacementInspector(session);
        ImGui::End();
        return;
    }

    if (m_viewport.placementKind() == EditorSelectionKind::Terrain)
    {
        renderTerrainInspector(session);
        ImGui::End();
        return;
    }

    switch (session.selection().kind)
    {
    case EditorSelectionKind::None:
    case EditorSelectionKind::Summary:
        renderDocumentSummary(session);
        break;

    case EditorSelectionKind::Environment:
        renderEnvironmentInspector(session);
        break;

    case EditorSelectionKind::Terrain:
        renderTerrainInspector(session);
        break;

    case EditorSelectionKind::BModel:
        renderBModelInspector(session, session.selection().index);
        break;

    case EditorSelectionKind::Entity:
        renderEntityInspector(session, session.selection().index);
        break;

    case EditorSelectionKind::Spawn:
        renderSpawnInspector(session, session.selection().index);
        break;

    case EditorSelectionKind::Actor:
        renderActorInspector(session, session.selection().index);
        break;

    case EditorSelectionKind::SpriteObject:
        renderSpriteObjectInspector(session, session.selection().index);
        break;

    case EditorSelectionKind::Chest:
        renderChestInspector(session, session.selection().index);
        break;

    case EditorSelectionKind::InteractiveFace:
        renderInteractiveFaceInspector(session);
        break;
    }

    ImGui::End();
}

void EditorMainWindow::renderLogPanel(
    const EditorSession &session,
    uint32_t frameNumber,
    float deltaSeconds,
    const std::string &rendererName)
{
    ImGui::SetNextWindowDockID(editorDockspaceId(), ImGuiCond_FirstUseEver);

    if (!ImGui::Begin("Log"))
    {
        ImGui::End();
        return;
    }

    ImGui::Text("Frame: %u", frameNumber);
    ImGui::Text("Delta: %.3f ms", deltaSeconds * 1000.0f);
    ImGui::Text("Renderer: %s", rendererName.c_str());

    for (const std::string &message : session.logMessages())
    {
        ImGui::TextWrapped("%s", message.c_str());
    }

    if (!session.validationMessages().empty())
    {
        ImGui::Separator();
        ImGui::Text("Validation Issues: %zu", session.validationMessages().size());

        for (const std::string &message : session.validationMessages())
        {
            ImGui::BulletText("%s", message.c_str());
        }
    }

    ImGui::End();
}

void EditorMainWindow::renderViewportPanel(EditorSession &session, float deltaSeconds)
{
    const ImGuiWindowFlags flags = ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse;
    ImGui::SetNextWindowBgAlpha(0.08f);

    if (!ImGui::Begin("Viewport", nullptr, flags))
    {
        ImGui::End();
        return;
    }

    const ImVec2 viewportOrigin = ImGui::GetCursorScreenPos();
    const ImVec2 viewportSize = ImGui::GetContentRegionAvail();
    m_viewportX = static_cast<int>(viewportOrigin.x);
    m_viewportY = static_cast<int>(viewportOrigin.y);
    m_viewportWidth = static_cast<uint16_t>(std::max(viewportSize.x, 1.0f));
    m_viewportHeight = static_cast<uint16_t>(std::max(viewportSize.y, 1.0f));

    ImGui::InvisibleButton(
        "ViewportSurface",
        viewportSize,
        ImGuiButtonFlags_MouseButtonLeft | ImGuiButtonFlags_MouseButtonRight);
    const bool isHovered = ImGui::IsItemHovered();
    const bool isFocused = ImGui::IsWindowFocused(ImGuiFocusedFlags_RootAndChildWindows);
    const bool leftMouseClicked = isHovered && ImGui::IsMouseClicked(ImGuiMouseButton_Left);
    const bool leftMouseDown = isHovered && ImGui::IsMouseDown(ImGuiMouseButton_Left);
    const ImVec2 mousePosition = ImGui::GetIO().MousePos;
    m_viewport.updateAndRender(
        session,
        m_viewportX,
        m_viewportY,
        m_viewportWidth,
        m_viewportHeight,
        isHovered,
        isFocused,
        leftMouseClicked,
        leftMouseDown,
        mousePosition.x,
        mousePosition.y,
        deltaSeconds);
    if (bgfx::isValid(m_viewport.viewportTextureHandle()))
    {
        ImGui::GetWindowDrawList()->AddImage(
            static_cast<ImTextureID>(static_cast<uintptr_t>(m_viewport.viewportTextureHandle().idx + 1)),
            viewportOrigin,
            ImVec2(viewportOrigin.x + viewportSize.x, viewportOrigin.y + viewportSize.y),
            ImVec2(0.0f, 1.0f),
            ImVec2(1.0f, 0.0f));
    }

    ImGui::SetCursorScreenPos(ImVec2(viewportOrigin.x + 12.0f, viewportOrigin.y + 12.0f));
    ImGui::PushStyleColor(ImGuiCol_ChildBg, ImVec4(0.06f, 0.07f, 0.08f, 0.80f));
    ImGui::PushStyleColor(ImGuiCol_Border, colorFromRgb(0x343B45));
    if (ImGui::BeginChild(
            "ViewportOverlay",
            ImVec2(328.0f, 74.0f),
            ImGuiChildFlags_Borders,
            ImGuiWindowFlags_NoScrollbar | ImGuiWindowFlags_NoScrollWithMouse))
    {
        m_viewport.renderOverlayUi(session);
    }
    ImGui::EndChild();
    ImGui::PopStyleColor(2);
    ImGui::End();
}

void EditorMainWindow::renderDocumentSummary(const EditorSession &session) const
{
    const EditorDocument &document = session.document();
    const Game::OutdoorMapData &outdoorGeometry = document.outdoorGeometry();
    const Game::OutdoorSceneData &sceneData = document.outdoorSceneData();

    size_t totalFaceCount = 0;

    for (const Game::OutdoorBModel &bmodel : outdoorGeometry.bmodels)
    {
        totalFaceCount += bmodel.faces.size();
    }

    ImGui::Text("Map: %s", document.displayName().c_str());
    ImGui::Text("Scene: %s", document.sceneVirtualPath().c_str());
    ImGui::Spacing();
    ImGui::Text("BModels: %zu", outdoorGeometry.bmodels.size());
    ImGui::Text("Faces: %zu", totalFaceCount);
    ImGui::Text("Entities: %zu", sceneData.entities.size());
    ImGui::Text("Spawns: %zu", sceneData.spawns.size());
    ImGui::Text("Actors: %zu", sceneData.initialState.actors.size());
    ImGui::Text("Sprite Objects: %zu", sceneData.initialState.spriteObjects.size());
    ImGui::Text("Chests: %zu", sceneData.initialState.chests.size());
    ImGui::Text("Terrain Overrides: %zu", sceneData.terrainAttributeOverrides.size());
    ImGui::Text("Dirty: %s", document.isDirty() ? "yes" : "no");

    if (!session.validationMessages().empty())
    {
        ImGui::Spacing();
        ImGui::Text("Validation Issues: %zu", session.validationMessages().size());

        const size_t issueCountToShow = std::min<size_t>(session.validationMessages().size(), 6);

        for (size_t index = 0; index < issueCountToShow; ++index)
        {
            ImGui::BulletText("%s", session.validationMessages()[index].c_str());
        }
    }
}

void EditorMainWindow::renderEnvironmentInspector(EditorSession &session) const
{
    EditorDocument &document = session.document();
    Game::OutdoorSceneData &sceneData = document.mutableOutdoorSceneData();
    Game::OutdoorSceneEnvironment &environment = session.document().mutableOutdoorSceneData().environment;
    EditorOutdoorMapPackageMetadata &packageMetadata = document.mutableOutdoorMapPackageMetadata();
    bool changed = false;

    if (beginInspectorPropertyTable("EnvironmentFields"))
    {
        changed = editStringField(session, "Sky Texture", environment.skyTexture, 128) || changed;
        changed = editStringField(session, "Ground Tileset", environment.groundTilesetName, 128) || changed;
        changed = editUInt8Field(session, "Master Tile", environment.masterTile) || changed;
        changed = editLookupIndicesField(session, "Lookup Indices", environment.tileSetLookupIndices) || changed;
        changed = editIntField(
            session,
            "Day Bits Raw",
            environment.dayBitsRaw,
            0,
            std::numeric_limits<int32_t>::max()) || changed;
        changed = editUInt32Field(session, "Map Extra Bits Raw", environment.mapExtraBitsRaw) || changed;
        changed = editIntField(
            session,
            "Fog Weak Distance",
            environment.fogWeakDistance,
            0,
            std::numeric_limits<int>::max())
            || changed;
        changed = editIntField(
            session,
            "Fog Strong Distance",
            environment.fogStrongDistance,
            0,
            std::numeric_limits<int>::max())
            || changed;
        changed = editIntField(
            session,
            "Ceiling",
            environment.ceiling,
            std::numeric_limits<int>::min(),
            std::numeric_limits<int>::max())
            || changed;
        ImGui::EndTable();
    }

    ImGui::Separator();
    ImGui::TextUnformatted("Flags");

    if (beginInspectorPropertyTable("EnvironmentFlags"))
    {
        changed = editBitCheckbox(session, "Foggy", environment.dayBitsRaw, 0x1) || changed;
        changed = editBitCheckbox(session, "Raining", environment.mapExtraBitsRaw, 0x1) || changed;
        changed = editBitCheckbox(session, "Snowing", environment.mapExtraBitsRaw, 0x2) || changed;
        changed = editBitCheckbox(session, "Underwater", environment.mapExtraBitsRaw, 0x4) || changed;
        changed = editBitCheckbox(session, "No Terrain", environment.mapExtraBitsRaw, 0x8) || changed;
        changed = editBitCheckbox(session, "Always Dark", environment.mapExtraBitsRaw, 0x10) || changed;
        changed = editBitCheckbox(session, "Always Light", environment.mapExtraBitsRaw, 0x20) || changed;
        changed = editBitCheckbox(session, "Always Foggy", environment.mapExtraBitsRaw, 0x40) || changed;
        changed = editBitCheckbox(session, "Red Fog", environment.mapExtraBitsRaw, 0x80) || changed;
        ImGui::EndTable();
    }

    ImGui::Separator();
    ImGui::TextUnformatted("Party Start");

    size_t partyStartSceneIndex = sceneData.entities.size();

    for (size_t entityIndex = 0; entityIndex < sceneData.entities.size(); ++entityIndex)
    {
        if (toLowerCopy(sceneData.entities[entityIndex].entity.name) == "party start")
        {
            partyStartSceneIndex = entityIndex;
            break;
        }
    }

    if (partyStartSceneIndex >= sceneData.entities.size())
    {
        ImGui::TextUnformatted("No party start entity is present.");

        if (ImGui::Button("Create Party Start"))
        {
            session.captureUndoSnapshot();
            Game::OutdoorSceneEntity entity = {};
            entity.entityIndex = sceneData.entities.size();
            entity.entity.name = "party start";
            sceneData.entities.push_back(entity);
            changed = true;
            partyStartSceneIndex = sceneData.entities.size() - 1;
        }
    }

    if (partyStartSceneIndex < sceneData.entities.size())
    {
        Game::OutdoorSceneEntity &partyStart = sceneData.entities[partyStartSceneIndex];
        ImGui::Text("Entity Index: %zu", partyStart.entityIndex);

        if (beginInspectorPropertyTable("PartyStartFields"))
        {
            changed = editIntField(
                session,
                "Start X",
                partyStart.entity.x,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(
                session,
                "Start Y",
                partyStart.entity.y,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(
                session,
                "Start Z",
                partyStart.entity.z,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(session, "Facing", partyStart.entity.facing, -3600, 3600) || changed;
            ImGui::EndTable();
        }

        if (ImGui::Button("Select Party Start"))
        {
            session.select(EditorSelectionKind::Entity, partyStartSceneIndex);
        }
    }

    if (document.hasMapPackageRoot())
    {
        ImGui::Separator();
        ImGui::TextUnformatted("Runtime Defaults");

        if (beginInspectorPropertyTable("PackageRuntimeDefaults"))
        {
            changed = editIntField(
                session,
                "Map Stats Id",
                packageMetadata.mapStatsId,
                1,
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(
                session,
                "Redbook Track",
                packageMetadata.redbookTrack,
                0,
                std::numeric_limits<int>::max()) || changed;
            changed = editStringField(session, "Environment Name", packageMetadata.environmentName, 64) || changed;
            ImGui::EndTable();
        }

        bool isTopLevelArea = packageMetadata.isTopLevelArea;

        if (ImGui::Checkbox("Top Level Area", &isTopLevelArea))
        {
            session.captureUndoSnapshot();
            packageMetadata.isTopLevelArea = isTopLevelArea;
            changed = true;
        }

        ImGui::Separator();
        ImGui::TextUnformatted("Outdoor Bounds");

        if (beginInspectorPropertyTable("PackageOutdoorBounds"))
        {
            changed = editIntField(
                session,
                "Min X",
                packageMetadata.outdoorBounds.minX,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(
                session,
                "Max X",
                packageMetadata.outdoorBounds.maxX,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(
                session,
                "Min Y",
                packageMetadata.outdoorBounds.minY,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            changed = editIntField(
                session,
                "Max Y",
                packageMetadata.outdoorBounds.maxY,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            ImGui::EndTable();
        }

        packageMetadata.outdoorBounds.enabled = true;

        auto renderTransitionEditor =
            [&](const char *pLabel, std::optional<Game::MapEdgeTransition> &transition) -> bool
        {
            bool localChanged = false;
            const std::string headerId = std::string(pLabel) + " Transition";

            if (!ImGui::CollapsingHeader(headerId.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
            {
                return false;
            }

            bool enabled = transition.has_value();

            if (ImGui::Checkbox((std::string("Enable ") + pLabel).c_str(), &enabled))
            {
                session.captureUndoSnapshot();

                if (enabled)
                {
                    Game::MapEdgeTransition newTransition = {};
                    newTransition.travelDays = 1;
                    newTransition.useMapStartPosition = true;
                    transition = newTransition;
                }
                else
                {
                    transition.reset();
                }

                localChanged = true;
            }

            if (!transition.has_value())
            {
                return localChanged;
            }

            const std::string destinationLabel = std::string(pLabel) + " Destination";
            const std::string travelDaysLabel = std::string(pLabel) + " Travel Days";
            const std::string headingLabel = std::string(pLabel) + " Heading";
            const std::string useStartLabel = std::string(pLabel) + " Use Map Start";
            const std::string arrivalXLabel = std::string(pLabel) + " Arrival X";
            const std::string arrivalYLabel = std::string(pLabel) + " Arrival Y";
            const std::string arrivalZLabel = std::string(pLabel) + " Arrival Z";
            Game::MapEdgeTransition &value = *transition;

            if (beginInspectorPropertyTable((std::string("TransitionFields_") + pLabel).c_str()))
            {
                localChanged = editStringField(session, destinationLabel.c_str(), value.destinationMapFileName, 64)
                    || localChanged;
                localChanged = editIntField(
                    session,
                    travelDaysLabel.c_str(),
                    value.travelDays,
                    0,
                    std::numeric_limits<int>::max()) || localChanged;

                int headingDegrees = value.directionDegrees.value_or(0);

                if (editIntField(session, headingLabel.c_str(), headingDegrees, -3600, 3600))
                {
                    value.directionDegrees = headingDegrees == 0 ? std::nullopt : std::optional<int>(headingDegrees);
                    localChanged = true;
                }

                ImGui::EndTable();
            }

            bool useMapStartPosition = value.useMapStartPosition;

            if (ImGui::Checkbox(useStartLabel.c_str(), &useMapStartPosition))
            {
                session.captureUndoSnapshot();
                value.useMapStartPosition = useMapStartPosition;

                if (useMapStartPosition)
                {
                    value.arrivalX.reset();
                    value.arrivalY.reset();
                    value.arrivalZ.reset();
                }
                else
                {
                    value.arrivalX = value.arrivalX.value_or(0);
                    value.arrivalY = value.arrivalY.value_or(0);
                    value.arrivalZ = value.arrivalZ.value_or(0);
                }

                localChanged = true;
            }

            if (!value.useMapStartPosition)
            {
                int arrivalX = value.arrivalX.value_or(0);
                int arrivalY = value.arrivalY.value_or(0);
                int arrivalZ = value.arrivalZ.value_or(0);

                if (beginInspectorPropertyTable((std::string("TransitionArrival_") + pLabel).c_str()))
                {
                    if (editIntField(
                            session,
                            arrivalXLabel.c_str(),
                            arrivalX,
                            std::numeric_limits<int>::min(),
                            std::numeric_limits<int>::max()))
                    {
                        value.arrivalX = arrivalX;
                        localChanged = true;
                    }

                    if (editIntField(
                            session,
                            arrivalYLabel.c_str(),
                            arrivalY,
                            std::numeric_limits<int>::min(),
                            std::numeric_limits<int>::max()))
                    {
                        value.arrivalY = arrivalY;
                        localChanged = true;
                    }

                    if (editIntField(
                            session,
                            arrivalZLabel.c_str(),
                            arrivalZ,
                            std::numeric_limits<int>::min(),
                            std::numeric_limits<int>::max()))
                    {
                        value.arrivalZ = arrivalZ;
                        localChanged = true;
                    }

                    ImGui::EndTable();
                }
            }

            return localChanged;
        };

        ImGui::Separator();
        ImGui::TextUnformatted("Map Transitions");
        changed = renderTransitionEditor("North", packageMetadata.northTransition) || changed;
        changed = renderTransitionEditor("South", packageMetadata.southTransition) || changed;
        changed = renderTransitionEditor("East", packageMetadata.eastTransition) || changed;
        changed = renderTransitionEditor("West", packageMetadata.westTransition) || changed;
    }

    if (changed)
    {
        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderTerrainInspector(EditorSession &session) const
{
    EditorDocument &document = session.document();
    Game::OutdoorSceneData &sceneData = document.mutableOutdoorSceneData();
    Game::OutdoorMapData &outdoorGeometry = document.mutableOutdoorGeometry();
    int cellX = 0;
    int cellY = 0;
    const bool hasSelectedCell = decodeTerrainCellFlatIndex(session.selection().index, cellX, cellY);
    const size_t cellIndex = hasSelectedCell ? terrainCellFlatIndex(cellX, cellY) : 0;
    const uint8_t currentTileId =
        hasSelectedCell && cellIndex < outdoorGeometry.tileMap.size() ? outdoorGeometry.tileMap[cellIndex] : 0;
    const uint8_t baseAttributes =
        hasSelectedCell && cellIndex < outdoorGeometry.attributeMap.size() ? outdoorGeometry.attributeMap[cellIndex] : 0;
    const uint8_t sampleHeight =
        hasSelectedCell && cellIndex < outdoorGeometry.heightMap.size() ? outdoorGeometry.heightMap[cellIndex] : 0;
    Game::OutdoorSceneTerrainAttributeOverride *pOverride =
        hasSelectedCell ? findTerrainOverride(sceneData, cellX, cellY) : nullptr;
    const uint8_t effectiveAttributes = pOverride != nullptr ? pOverride->legacyAttributes : baseAttributes;
    const std::optional<std::vector<std::string>> tileTextureNames =
        session.assetFileSystem() != nullptr
        ? Game::loadTerrainTileTextureNames(*session.assetFileSystem(), outdoorGeometry)
        : std::nullopt;
    bool changed = false;

    static constexpr const char *FalloffModeLabels[] = {"Flat", "Linear", "Smooth"};
    static constexpr const char *FlattenTargetModeLabels[] = {"Sampled", "Numeric"};
    const auto renderTerrainTileBitmapHoverPreview = [this, &session, &tileTextureNames](uint8_t tileId)
    {
        if (!ImGui::IsItemHovered(ImGuiHoveredFlags_Stationary | ImGuiHoveredFlags_DelayShort))
        {
            return;
        }

        if (!tileTextureNames || tileId >= tileTextureNames->size())
        {
            return;
        }

        const std::string &textureName = (*tileTextureNames)[tileId];

        if (textureName.empty() || textureName == "pending")
        {
            return;
        }

        const std::optional<bgfx::TextureHandle> textureHandle = ensureBitmapPreviewTexture(session, textureName);
        const std::optional<std::pair<int, int>> textureSize = bitmapPreviewTextureSize(textureName);

        if (!textureHandle || !textureSize || !bgfx::isValid(*textureHandle))
        {
            return;
        }

        ImGui::BeginTooltip();
        ImGui::Text("Tile %u (0x%02X)", static_cast<unsigned>(tileId), static_cast<unsigned>(tileId));
        ImGui::TextDisabled("%s", textureName.c_str());
        ImGui::Image(
            static_cast<ImTextureID>(static_cast<uintptr_t>(textureHandle->idx + 1)),
            ImVec2(static_cast<float>(textureSize->first), static_cast<float>(textureSize->second)));
        ImGui::EndTooltip();
    };

    if (beginInspectorSectionBlock("Height Sculpt"))
    {
        bool terrainSculptEnabled = session.terrainSculptEnabled();

        if (beginInspectorPropertyTable("TerrainSculptFields"))
        {
            beginInspectorFieldRow("Sculpt In Viewport");
            if (ImGui::Checkbox("##TerrainSculptEnabled", &terrainSculptEnabled))
            {
                session.setTerrainSculptEnabled(terrainSculptEnabled);

                if (terrainSculptEnabled)
                {
                    session.setTerrainPaintEnabled(false);
                }
            }

            const std::array<std::pair<const char *, EditorTerrainSculptMode>, 6> sculptModes = {{
                {"Raise", EditorTerrainSculptMode::Raise},
                {"Lower", EditorTerrainSculptMode::Lower},
                {"Flatten", EditorTerrainSculptMode::Flatten},
                {"Smooth", EditorTerrainSculptMode::Smooth},
                {"Noise", EditorTerrainSculptMode::Noise},
                {"Ramp", EditorTerrainSculptMode::Ramp}
            }};

            beginInspectorFieldRow("Tool");
            for (size_t index = 0; index < sculptModes.size(); ++index)
            {
                const auto &[pLabel, mode] = sculptModes[index];
                const bool selected = session.terrainSculptMode() == mode;

                if (renderIconTogglePill(
                        std::string("TerrainInspectorSculptMode" + std::to_string(index)).c_str(),
                        pLabel,
                        terrainSculptModeIcon(mode),
                        selected))
                {
                    session.setTerrainSculptMode(mode);
                }

                if ((index % 3) != 2 && index + 1 < sculptModes.size())
                {
                    ImGui::SameLine();
                }
            }

            if (session.terrainSculptMode() == EditorTerrainSculptMode::Flatten)
            {
                int flattenTargetMode = static_cast<int>(session.terrainFlattenTargetMode());
                beginInspectorFieldRow("Flatten Target");
                ImGui::SetNextItemWidth(160.0f);

                if (ImGui::Combo(
                        "##TerrainFlattenTargetMode",
                        &flattenTargetMode,
                        FlattenTargetModeLabels,
                        IM_ARRAYSIZE(FlattenTargetModeLabels)))
                {
                    session.setTerrainFlattenTargetMode(static_cast<EditorTerrainFlattenTargetMode>(flattenTargetMode));
                }

                if (session.terrainFlattenTargetMode() == EditorTerrainFlattenTargetMode::Numeric)
                {
                    int targetHeight = session.terrainFlattenTargetHeight();
                    beginInspectorFieldRow("Target Height");
                    ImGui::SetNextItemWidth(120.0f);

                    if (ImGui::InputInt("##TerrainFlattenTargetHeight", &targetHeight, 1, 8))
                    {
                        session.setTerrainFlattenTargetHeight(targetHeight);
                    }
                }
                else
                {
                    beginInspectorFieldRow("Sampled Target");
                    ImGui::Text(
                        "%d (%d world units)",
                        session.terrainFlattenTargetHeight(),
                        session.terrainFlattenTargetHeight() * Game::OutdoorMapData::TerrainHeightScale);

                    beginInspectorFieldRow("Pick Height");
                    const bool canPickSelected =
                        session.selection().kind == EditorSelectionKind::Terrain
                        && session.selection().index
                            < static_cast<size_t>(Game::OutdoorMapData::TerrainWidth * Game::OutdoorMapData::TerrainHeight);
                    ImGui::BeginDisabled(!canPickSelected);

                    if (ImGui::Button("Pick From Selected"))
                    {
                        tryPickFlattenTargetFromSelectedTerrainCell(session);
                    }

                    ImGui::EndDisabled();
                    ImGui::SameLine();
                    ImGui::TextDisabled("Alt+LMB in viewport");
                }
            }

            int terrainSculptRadius = session.terrainSculptRadius();
            beginInspectorFieldRow("Sculpt Radius");
            ImGui::SetNextItemWidth(120.0f);

            if (ImGui::InputInt("##TerrainSculptRadius", &terrainSculptRadius, 1, 4))
            {
                session.setTerrainSculptRadius(terrainSculptRadius);
            }

            int terrainSculptStrength = session.terrainSculptStrength();
            beginInspectorFieldRow("Sculpt Strength");
            ImGui::SetNextItemWidth(120.0f);

            if (ImGui::InputInt("##TerrainSculptStrength", &terrainSculptStrength, 1, 4))
            {
                session.setTerrainSculptStrength(terrainSculptStrength);
            }

            int terrainSculptFalloffMode = static_cast<int>(session.terrainSculptFalloffMode());
            beginInspectorFieldRow("Sculpt Falloff");
            ImGui::SetNextItemWidth(160.0f);

            if (ImGui::Combo(
                    "##TerrainSculptFalloff",
                    &terrainSculptFalloffMode,
                    FalloffModeLabels,
                    IM_ARRAYSIZE(FalloffModeLabels)))
            {
                session.setTerrainSculptFalloffMode(static_cast<EditorTerrainFalloffMode>(terrainSculptFalloffMode));
            }

            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Tile Paint"))
    {
        bool terrainPaintEnabled = session.terrainPaintEnabled();

        if (beginInspectorPropertyTable("TerrainPaintFields"))
        {
            beginInspectorFieldRow("Paint In Viewport");
            if (ImGui::Checkbox("##TerrainPaintEnabled", &terrainPaintEnabled))
            {
                session.setTerrainPaintEnabled(terrainPaintEnabled);

                if (terrainPaintEnabled)
                {
                    session.setTerrainSculptEnabled(false);
                }
            }

            beginInspectorFieldRow("Use Cell Tile");
            ImGui::BeginDisabled(!hasSelectedCell);
            if (ImGui::Button("Use Selected Cell"))
            {
                session.setTerrainPaintTileId(currentTileId);
            }
            ImGui::EndDisabled();

            const std::array<std::pair<const char *, EditorTerrainPaintMode>, 3> paintModes = {{
                {"Brush", EditorTerrainPaintMode::Brush},
                {"Rect", EditorTerrainPaintMode::Rectangle},
                {"Fill", EditorTerrainPaintMode::Fill}
            }};

            beginInspectorFieldRow("Tool");
            for (size_t index = 0; index < paintModes.size(); ++index)
            {
                const auto &[pLabel, mode] = paintModes[index];
                const bool selected = session.terrainPaintMode() == mode;

                if (renderIconTogglePill(
                        std::string("TerrainInspectorPaintMode" + std::to_string(index)).c_str(),
                        pLabel,
                        terrainPaintModeIcon(mode),
                        selected))
                {
                    session.setTerrainPaintMode(mode);
                }

                if (index + 1 < paintModes.size())
                {
                    ImGui::SameLine();
                }
            }

            int terrainPaintTileId = static_cast<int>(session.terrainPaintTileId());
            beginInspectorFieldRow("Paint Tile Id");
            ImGui::SetNextItemWidth(120.0f);

            if (ImGui::InputInt("##TerrainPaintTileId", &terrainPaintTileId, 1, 16))
            {
                terrainPaintTileId = std::clamp(terrainPaintTileId, 0, 255);
                session.setTerrainPaintTileId(static_cast<uint8_t>(terrainPaintTileId));
            }

            beginInspectorFieldRow("Tile Preview");
            renderTerrainTilePreviewButton(
                m_viewport,
                session.terrainPaintTileId(),
                true,
                ImVec2(36.0f, 36.0f));
            renderTerrainTileBitmapHoverPreview(session.terrainPaintTileId());

            if (session.terrainPaintMode() == EditorTerrainPaintMode::Brush)
            {
                int terrainPaintRadius = session.terrainPaintRadius();
                beginInspectorFieldRow("Paint Brush Radius");
                ImGui::SetNextItemWidth(120.0f);

                if (ImGui::InputInt("##TerrainPaintRadius", &terrainPaintRadius, 1, 4))
                {
                    session.setTerrainPaintRadius(terrainPaintRadius);
                }

                int terrainPaintEdgeNoise = session.terrainPaintEdgeNoise();
                beginInspectorFieldRow("Paint Edge Noise");
                ImGui::SetNextItemWidth(120.0f);

                if (ImGui::SliderInt("##TerrainPaintEdgeNoise", &terrainPaintEdgeNoise, 0, 100))
                {
                    session.setTerrainPaintEdgeNoise(terrainPaintEdgeNoise);
                }
            }

            ImGui::EndTable();
        }

        if (ImGui::BeginChild("TerrainTilePalette", ImVec2(0.0f, 220.0f), ImGuiChildFlags_Borders))
        {
            int visibleTileCountInRow = 0;

            for (int tileId = 0; tileId < 256; ++tileId)
            {
                float u0 = 0.0f;
                float v0 = 0.0f;
                float u1 = 0.0f;
                float v1 = 0.0f;

                if (!m_viewport.tryGetTerrainTilePreviewUv(static_cast<uint8_t>(tileId), u0, v0, u1, v1))
                {
                    continue;
                }

                const bool isSelected = session.terrainPaintTileId() == static_cast<uint8_t>(tileId);

                if (renderTerrainTilePreviewButton(
                        m_viewport,
                        static_cast<uint8_t>(tileId),
                        isSelected,
                        ImVec2(34.0f, 34.0f)))
                {
                    session.setTerrainPaintTileId(static_cast<uint8_t>(tileId));
                }

                renderTerrainTileBitmapHoverPreview(static_cast<uint8_t>(tileId));

                ++visibleTileCountInRow;

                if ((visibleTileCountInRow % 8) != 0)
                {
                    ImGui::SameLine();
                }
            }
        }
        ImGui::EndChild();
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Cell Summary"))
    {
        ImGui::Text("Terrain Attribute Overrides: %zu", sceneData.terrainAttributeOverrides.size());

        if (hasSelectedCell)
        {
            ImGui::Text("Cell: (%d, %d)", cellX, cellY);
            ImGui::Text(
                "Current Tile: %u (0x%02X)",
                static_cast<unsigned>(currentTileId),
                static_cast<unsigned>(currentTileId));
            ImGui::Text(
                "Sample Height: %u (%d world units)",
                static_cast<unsigned>(sampleHeight),
                static_cast<int>(sampleHeight) * Game::OutdoorMapData::TerrainHeightScale);
            ImGui::Text("Base Attributes: %u", baseAttributes);
            ImGui::Text("Has Override: %s", pOverride != nullptr ? "yes" : "no");
        }
        else
        {
            ImGui::TextUnformatted("Terrain mode active.");
            ImGui::TextDisabled("Click a terrain cell to inspect its tile, height, and override data.");
        }

        endInspectorSectionBlock();
    }

    if (hasSelectedCell && beginInspectorSectionBlock("Cell Override", false))
    {
        if (pOverride == nullptr)
        {
            if (ImGui::Button("Add Override"))
            {
                session.captureUndoSnapshot();
                sceneData.terrainAttributeOverrides.push_back({cellX, cellY, baseAttributes});
                pOverride = &sceneData.terrainAttributeOverrides.back();
                changed = true;
            }

            ImGui::SameLine();
            ImGui::TextUnformatted("Edits create a scene override for this cell.");
        }
        else if (ImGui::Button("Remove Override"))
        {
            session.captureUndoSnapshot();
            sceneData.terrainAttributeOverrides.erase(
                std::remove_if(
                    sceneData.terrainAttributeOverrides.begin(),
                    sceneData.terrainAttributeOverrides.end(),
                    [cellX, cellY](const Game::OutdoorSceneTerrainAttributeOverride &overrideEntry)
                    {
                        return overrideEntry.x == cellX && overrideEntry.y == cellY;
                    }),
                sceneData.terrainAttributeOverrides.end());
            changed = true;
            pOverride = nullptr;
        }

        if (pOverride != nullptr)
        {
            if (beginInspectorPropertyTable("TerrainOverrideFields"))
            {
                changed = editUInt8Field(session, "Legacy Attributes", pOverride->legacyAttributes) || changed;
                changed = editBitCheckbox(session, "Burn", pOverride->legacyAttributes, static_cast<uint8_t>(0x01))
                    || changed;
                changed = editBitCheckbox(session, "Water", pOverride->legacyAttributes, static_cast<uint8_t>(0x02))
                    || changed;
                ImGui::EndTable();
            }
        }
        else
        {
            ImGui::Text("Effective Attributes: %u", effectiveAttributes);
            ImGui::Text("Burn: %s", ((effectiveAttributes & 0x01) != 0) ? "true" : "false");
            ImGui::Text("Water: %s", ((effectiveAttributes & 0x02) != 0) ? "true" : "false");
        }
        endInspectorSectionBlock();
    }

    if (changed)
    {
        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderBModelInspector(EditorSession &session, size_t bmodelIndex) const
{
    EditorDocument &document = session.document();
    Game::OutdoorMapData &outdoorGeometry = document.mutableOutdoorGeometry();
    Game::OutdoorSceneData &sceneData = document.mutableOutdoorSceneData();

    if (bmodelIndex >= outdoorGeometry.bmodels.size())
    {
        ImGui::TextUnformatted("Selected bmodel is out of range.");
        return;
    }

    Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];

    if (m_bmodelTransformEditorIndex != bmodelIndex)
    {
        m_bmodelTransformEditorIndex = bmodelIndex;
        m_bmodelMoveBy[0] = 0;
        m_bmodelMoveBy[1] = 0;
        m_bmodelMoveBy[2] = 0;
        m_bmodelRotateByDegrees[0] = 0.0f;
        m_bmodelRotateByDegrees[1] = 0.0f;
        m_bmodelRotateByDegrees[2] = 0.0f;
    }

    if (m_bmodelBulkEditorIndex != bmodelIndex)
    {
        m_bmodelBulkEditorIndex = bmodelIndex;
        m_bmodelBulkFaceScope = static_cast<int>(BModelBulkFaceScope::All);
        m_bmodelBulkFaceAttributes = 0;
        m_bmodelBulkCogNumber = 0;
        m_bmodelBulkCogTriggeredNumber = 0;
        m_bmodelBulkCogTrigger = 0;

        if (!bmodel.faces.empty())
        {
            m_bmodelBulkFaceAttributes = bmodel.faces.front().attributes & EditableFaceAttributeMask;
            m_bmodelBulkCogNumber = bmodel.faces.front().cogNumber;
            m_bmodelBulkCogTriggeredNumber = bmodel.faces.front().cogTriggeredNumber;
            m_bmodelBulkCogTrigger = bmodel.faces.front().cogTrigger;
        }
    }

    if (m_bmodelImportEditorIndex != bmodelIndex)
    {
        m_bmodelImportEditorIndex = bmodelIndex;
        const std::optional<EditorBModelImportSource> importSource = session.bmodelImportSource(bmodelIndex);
        std::string importPath;
        std::string importDefaultTexture;

        if (importSource)
        {
            importPath = importSource->sourcePath;
            importDefaultTexture = importSource->defaultTextureName;
            m_bmodelImportSelectedMeshName = importSource->sourceMeshName;
            m_bmodelImportScale = importSource->importScale;
            m_bmodelImportMergeCoplanarFaces = importSource->mergeCoplanarFaces;
        }
        else
        {
            m_bmodelImportSelectedMeshName.clear();
            m_bmodelImportScale = 1.0f;
            m_bmodelImportMergeCoplanarFaces = false;

            for (const Game::OutdoorBModelFace &face : bmodel.faces)
            {
                if (!face.textureName.empty())
                {
                    importDefaultTexture = face.textureName;
                    break;
                }
            }

            if (importDefaultTexture.empty())
            {
                const std::vector<std::string> mapTextureNames = session.usedBitmapTextureNamesInMap();
                importDefaultTexture = mapTextureNames.empty() ? "grastyl" : mapTextureNames.front();
            }
        }

        std::snprintf(m_bmodelImportPath, sizeof(m_bmodelImportPath), "%s", importPath.c_str());
        std::snprintf(m_bmodelImportDefaultTexture, sizeof(m_bmodelImportDefaultTexture), "%s", importDefaultTexture.c_str());
    }

    if (beginInspectorSectionBlock("Overview"))
    {
        ImGui::Text("BModel %zu", bmodelIndex);
        ImGui::Text("Name: %s", bmodel.name.empty() ? "<unnamed>" : bmodel.name.c_str());
        ImGui::Text("Faces: %zu", bmodel.faces.size());
        ImGui::Text("Vertices: %zu", bmodel.vertices.size());

        if (beginInspectorPropertyTable("BModelInspector"))
        {
            renderInspectorReadOnlyField("Position", std::to_string(bmodel.positionX) + ", "
                + std::to_string(bmodel.positionY) + ", "
                + std::to_string(bmodel.positionZ));
            renderInspectorReadOnlyField("Bounds Min", std::to_string(bmodel.minX) + ", "
                + std::to_string(bmodel.minY) + ", "
                + std::to_string(bmodel.minZ));
            renderInspectorReadOnlyField("Bounds Max", std::to_string(bmodel.maxX) + ", "
                + std::to_string(bmodel.maxY) + ", "
                + std::to_string(bmodel.maxZ));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    const bool hasMove = m_bmodelMoveBy[0] != 0 || m_bmodelMoveBy[1] != 0 || m_bmodelMoveBy[2] != 0;
    const bool hasRotation =
        std::fabs(m_bmodelRotateByDegrees[0]) > 0.0001f
        || std::fabs(m_bmodelRotateByDegrees[1]) > 0.0001f
        || std::fabs(m_bmodelRotateByDegrees[2]) > 0.0001f;
    float actualMinX = std::numeric_limits<float>::max();
    float actualMinY = std::numeric_limits<float>::max();
    float actualMinZ = std::numeric_limits<float>::max();
    float actualMaxX = std::numeric_limits<float>::lowest();
    float actualMaxY = std::numeric_limits<float>::lowest();
    float actualMaxZ = std::numeric_limits<float>::lowest();

    for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
    {
        actualMinX = std::min(actualMinX, static_cast<float>(vertex.x));
        actualMinY = std::min(actualMinY, static_cast<float>(vertex.y));
        actualMinZ = std::min(actualMinZ, static_cast<float>(vertex.z));
        actualMaxX = std::max(actualMaxX, static_cast<float>(vertex.x));
        actualMaxY = std::max(actualMaxY, static_cast<float>(vertex.y));
        actualMaxZ = std::max(actualMaxZ, static_cast<float>(vertex.z));
    }

    if (bmodel.vertices.empty())
    {
        actualMinX = static_cast<float>(bmodel.minX);
        actualMinY = static_cast<float>(bmodel.minY);
        actualMinZ = static_cast<float>(bmodel.minZ);
        actualMaxX = static_cast<float>(bmodel.maxX);
        actualMaxY = static_cast<float>(bmodel.maxY);
        actualMaxZ = static_cast<float>(bmodel.maxZ);
    }

    const float bmodelCenterX = (actualMinX + actualMaxX) * 0.5f;
    const float bmodelCenterY = (actualMinY + actualMaxY) * 0.5f;
    const float terrainHeightAtCenter = Game::sampleOutdoorTerrainHeight(outdoorGeometry, bmodelCenterX, bmodelCenterY);
    const int snapBaseZ = static_cast<int>(std::lround(actualMinZ));
    const int snapToGroundDeltaZ = static_cast<int>(std::lround(terrainHeightAtCenter)) - snapBaseZ;

    if (beginInspectorSectionBlock("Transform"))
    {
        if (beginInspectorPropertyTable("BModelTransformFields"))
        {
            beginInspectorFieldRow("Move By");
            ImGui::InputInt3("##Move By", m_bmodelMoveBy);

            beginInspectorFieldRow("Rotate By XYZ");
            ImGui::InputFloat3("##Rotate By XYZ", m_bmodelRotateByDegrees, "%.2f");
            ImGui::EndTable();
        }

        if (ImGui::Button("Apply Transform", ImVec2(160.0f, 0.0f)))
        {
            if (hasMove || hasRotation)
            {
                session.captureUndoSnapshot();
                const bool trackSourceTransform =
                    session.bmodelImportSource(bmodelIndex).has_value()
                    || session.document().outdoorBModelSourceTransform(bmodelIndex).has_value();
                EditorBModelSourceTransform sourceTransform =
                    session.document().outdoorBModelSourceTransform(bmodelIndex).value_or(sourceTransformFromBModel(bmodel));

                float minX = std::numeric_limits<float>::max();
                float minY = std::numeric_limits<float>::max();
                float minZ = std::numeric_limits<float>::max();
                float maxX = std::numeric_limits<float>::lowest();
                float maxY = std::numeric_limits<float>::lowest();
                float maxZ = std::numeric_limits<float>::lowest();

                for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
                {
                    minX = std::min(minX, static_cast<float>(vertex.x));
                    minY = std::min(minY, static_cast<float>(vertex.y));
                    minZ = std::min(minZ, static_cast<float>(vertex.z));
                    maxX = std::max(maxX, static_cast<float>(vertex.x));
                    maxY = std::max(maxY, static_cast<float>(vertex.y));
                    maxZ = std::max(maxZ, static_cast<float>(vertex.z));
                }

                const float pivotX = (minX + maxX) * 0.5f;
                const float pivotY = (minY + maxY) * 0.5f;
                const float pivotZ = (minZ + maxZ) * 0.5f;
                const float rotationXRadians = m_bmodelRotateByDegrees[0] * 3.14159265358979323846f / 180.0f;
                const float rotationYRadians = m_bmodelRotateByDegrees[1] * 3.14159265358979323846f / 180.0f;
                const float rotationZRadians = m_bmodelRotateByDegrees[2] * 3.14159265358979323846f / 180.0f;
                const float cosX = std::cos(rotationXRadians);
                const float sinX = std::sin(rotationXRadians);
                const float cosY = std::cos(rotationYRadians);
                const float sinY = std::sin(rotationYRadians);
                const float cosZ = std::cos(rotationZRadians);
                const float sinZ = std::sin(rotationZRadians);

                for (Game::OutdoorBModelVertex &vertex : bmodel.vertices)
                {
                    const float localX = static_cast<float>(vertex.x) - pivotX;
                    const float localY = static_cast<float>(vertex.y) - pivotY;
                    const float localZ = static_cast<float>(vertex.z) - pivotZ;

                    const float rotatedXY = localY * cosX - localZ * sinX;
                    const float rotatedXZ = localY * sinX + localZ * cosX;
                    const float rotatedYX = localX * cosY + rotatedXZ * sinY;
                    const float rotatedYZ = -localX * sinY + rotatedXZ * cosY;
                    const float rotatedZX = rotatedYX * cosZ - rotatedXY * sinZ;
                    const float rotatedZY = rotatedYX * sinZ + rotatedXY * cosZ;

                    const float worldX = pivotX + rotatedZX + static_cast<float>(m_bmodelMoveBy[0]);
                    const float worldY = pivotY + rotatedZY + static_cast<float>(m_bmodelMoveBy[1]);
                    const float worldZ = pivotZ + rotatedYZ + static_cast<float>(m_bmodelMoveBy[2]);
                    vertex.x = static_cast<int>(std::lround(worldX));
                    vertex.y = static_cast<int>(std::lround(worldY));
                    vertex.z = static_cast<int>(std::lround(worldZ));
                }

                recomputeBModelMetadata(bmodel);

                if (trackSourceTransform)
                {
                    sourceTransform.basisX = rotateVectorByEulerDegrees(
                        sourceTransform.basisX,
                        m_bmodelRotateByDegrees[0],
                        m_bmodelRotateByDegrees[1],
                        m_bmodelRotateByDegrees[2]);
                    sourceTransform.basisY = rotateVectorByEulerDegrees(
                        sourceTransform.basisY,
                        m_bmodelRotateByDegrees[0],
                        m_bmodelRotateByDegrees[1],
                        m_bmodelRotateByDegrees[2]);
                    sourceTransform.basisZ = rotateVectorByEulerDegrees(
                        sourceTransform.basisZ,
                        m_bmodelRotateByDegrees[0],
                        m_bmodelRotateByDegrees[1],
                        m_bmodelRotateByDegrees[2]);
                    sourceTransform.originX += static_cast<float>(m_bmodelMoveBy[0]);
                    sourceTransform.originY += static_cast<float>(m_bmodelMoveBy[1]);
                    sourceTransform.originZ += static_cast<float>(m_bmodelMoveBy[2]);
                    session.document().setOutdoorBModelSourceTransform(bmodelIndex, sourceTransform);
                }

                m_bmodelMoveBy[0] = 0;
                m_bmodelMoveBy[1] = 0;
                m_bmodelMoveBy[2] = 0;
                m_bmodelRotateByDegrees[0] = 0.0f;
                m_bmodelRotateByDegrees[1] = 0.0f;
                m_bmodelRotateByDegrees[2] = 0.0f;
                session.noteDocumentMutated({});
            }
        }

        ImGui::SameLine();

        if (ImGui::Button("Snap To Ground", ImVec2(150.0f, 0.0f)))
        {
            if (snapToGroundDeltaZ != 0)
            {
                session.captureUndoSnapshot();
                const bool trackSourceTransform =
                    session.bmodelImportSource(bmodelIndex).has_value()
                    || session.document().outdoorBModelSourceTransform(bmodelIndex).has_value();
                EditorBModelSourceTransform sourceTransform =
                    session.document().outdoorBModelSourceTransform(bmodelIndex).value_or(sourceTransformFromBModel(bmodel));

                for (Game::OutdoorBModelVertex &vertex : bmodel.vertices)
                {
                    vertex.z += snapToGroundDeltaZ;
                }

                bmodel.positionZ += snapToGroundDeltaZ;
                bmodel.minZ += snapToGroundDeltaZ;
                bmodel.maxZ += snapToGroundDeltaZ;
                bmodel.boundingCenterZ += snapToGroundDeltaZ;

                if (trackSourceTransform)
                {
                    sourceTransform.originZ += static_cast<float>(snapToGroundDeltaZ);
                    session.document().setOutdoorBModelSourceTransform(bmodelIndex, sourceTransform);
                }

                session.noteDocumentMutated({});
            }
        }

        ImGui::SameLine();

        if (ImGui::Button("Reset Fields", ImVec2(120.0f, 0.0f)))
        {
            m_bmodelMoveBy[0] = 0;
            m_bmodelMoveBy[1] = 0;
            m_bmodelMoveBy[2] = 0;
            m_bmodelRotateByDegrees[0] = 0.0f;
            m_bmodelRotateByDegrees[1] = 0.0f;
            m_bmodelRotateByDegrees[2] = 0.0f;
        }

        ImGui::Text(
            "Terrain Center: %.0f  |  Base Z: %d  |  Snap Delta Z: %d",
            terrainHeightAtCenter,
            snapBaseZ,
            snapToGroundDeltaZ);

        if (!hasMove && !hasRotation)
        {
            ImGui::TextDisabled("Enter a move delta and/or XYZ rotation delta, then click Apply Transform.");
        }

        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Face Defaults"))
    {
        if (beginInspectorPropertyTable("BModelFaceDefaults"))
        {
            beginInspectorFieldRow("Scope");
            const char *scopePreview =
                bmodelBulkFaceScopeLabel(static_cast<BModelBulkFaceScope>(m_bmodelBulkFaceScope));

            if (ImGui::BeginCombo("##BModelFaceScope", scopePreview))
            {
                for (int scopeIndex = 0; scopeIndex < 3; ++scopeIndex)
                {
                    const BModelBulkFaceScope scope = static_cast<BModelBulkFaceScope>(scopeIndex);
                    const bool selected = scopeIndex == m_bmodelBulkFaceScope;

                    if (ImGui::Selectable(bmodelBulkFaceScopeLabel(scope), selected))
                    {
                        m_bmodelBulkFaceScope = scopeIndex;
                    }

                    if (selected)
                    {
                        ImGui::SetItemDefaultFocus();
                    }
                }

                ImGui::EndCombo();
            }

            beginInspectorFieldRow("COG Number");
            int bulkCogNumber = m_bmodelBulkCogNumber;
            if (ImGui::InputInt("##BModelBulkCogNumber", &bulkCogNumber))
            {
                m_bmodelBulkCogNumber = static_cast<uint16_t>(std::clamp(bulkCogNumber, 0, 65535));
            }

            uint16_t bulkCogTriggeredNumber = m_bmodelBulkCogTriggeredNumber;
            if (editMapEventField(session, "COG Triggered Number", bulkCogTriggeredNumber))
            {
                m_bmodelBulkCogTriggeredNumber = bulkCogTriggeredNumber;
            }

            renderResolvedMapEventField(session, "Resolved Event", m_bmodelBulkCogTriggeredNumber);

            beginInspectorFieldRow("COG Trigger");
            int bulkCogTrigger = m_bmodelBulkCogTrigger;
            if (ImGui::InputInt("##BModelBulkCogTrigger", &bulkCogTrigger))
            {
                m_bmodelBulkCogTrigger = static_cast<uint16_t>(std::clamp(bulkCogTrigger, 0, 65535));
            }

            const auto editBulkAttributeCheckbox = [this](const char *pLabel, uint32_t mask)
            {
                bool enabled = (m_bmodelBulkFaceAttributes & mask) != 0;
                beginInspectorFieldRow(pLabel);

                if (!ImGui::Checkbox(inspectorFieldId(pLabel).c_str(), &enabled))
                {
                    return;
                }

                if (enabled)
                {
                    m_bmodelBulkFaceAttributes |= mask;
                }
                else
                {
                    m_bmodelBulkFaceAttributes &= ~mask;
                }
            };

            editBulkAttributeCheckbox("Fluid", FaceAttributeFluid);
            editBulkAttributeCheckbox("Invisible", FaceAttributeInvisible);
            editBulkAttributeCheckbox("Has Hint", FaceAttributeHasHint);
            editBulkAttributeCheckbox("Clickable", FaceAttributeClickable);
            editBulkAttributeCheckbox("Pressure Plate", FaceAttributePressurePlate);
            editBulkAttributeCheckbox("Untouchable", FaceAttributeUntouchable);
            ImGui::EndTable();
        }

        const auto bulkFaceScope = static_cast<BModelBulkFaceScope>(m_bmodelBulkFaceScope);
        size_t scopedFaceCount = 0;

        for (const Game::OutdoorBModelFace &face : bmodel.faces)
        {
            if (bmodelFaceMatchesScope(face, bulkFaceScope))
            {
                ++scopedFaceCount;
            }
        }

        if (ImGui::Button("Apply To Faces", ImVec2(140.0f, 0.0f)))
        {
            if (scopedFaceCount > 0)
            {
                session.captureUndoSnapshot();

                for (size_t currentFaceIndex = 0; currentFaceIndex < bmodel.faces.size(); ++currentFaceIndex)
                {
                    Game::OutdoorBModelFace &face = bmodel.faces[currentFaceIndex];

                    if (!bmodelFaceMatchesScope(face, bulkFaceScope))
                    {
                        continue;
                    }

                    Game::OutdoorSceneInteractiveFace *pInteractiveFace =
                        findInteractiveFace(sceneData, bmodelIndex, currentFaceIndex);

                    if (pInteractiveFace == nullptr)
                    {
                        sceneData.interactiveFaces.push_back({
                            bmodelIndex,
                            currentFaceIndex,
                            face.attributes,
                            face.cogNumber,
                            face.cogTriggeredNumber,
                            face.cogTrigger});
                        pInteractiveFace = &sceneData.interactiveFaces.back();
                    }

                    pInteractiveFace->legacyAttributes = (pInteractiveFace->legacyAttributes & ~EditableFaceAttributeMask)
                        | (m_bmodelBulkFaceAttributes & EditableFaceAttributeMask);
                    pInteractiveFace->cogNumber = m_bmodelBulkCogNumber;
                    pInteractiveFace->cogTriggeredNumber = m_bmodelBulkCogTriggeredNumber;
                    pInteractiveFace->cogTrigger = m_bmodelBulkCogTrigger;
                }

                session.noteDocumentMutated({});
            }
        }
    
        ImGui::SameLine();

        if (ImGui::Button("Reset Faces", ImVec2(140.0f, 0.0f)))
        {
            if (scopedFaceCount > 0)
            {
                session.captureUndoSnapshot();
                sceneData.interactiveFaces.erase(
                    std::remove_if(
                        sceneData.interactiveFaces.begin(),
                        sceneData.interactiveFaces.end(),
                        [&bmodel, bmodelIndex, bulkFaceScope](const Game::OutdoorSceneInteractiveFace &interactiveFace)
                        {
                            return interactiveFace.bmodelIndex == bmodelIndex
                                && interactiveFace.faceIndex < bmodel.faces.size()
                                && bmodelFaceMatchesScope(bmodel.faces[interactiveFace.faceIndex], bulkFaceScope);
                        }),
                    sceneData.interactiveFaces.end());

                session.noteDocumentMutated({});
            }
        }
        ImGui::TextDisabled("%zu faces in current scope.", scopedFaceCount);
        endInspectorSectionBlock();
    }

    const bool hasRememberedImportSource = session.bmodelImportSource(bmodelIndex).has_value();
    const bool hasModelImportPath = m_bmodelImportPath[0] != '\0';
    const bool canSplitByMesh = canSplitImportedModelPathByMesh(m_bmodelImportPath);
    const ModelImportInspectionState &inspection =
        ensureModelImportInspection(m_bmodelImportPath, m_bmodelImportInspection);

    if (!trimCopy(m_bmodelImportSelectedMeshName).empty())
    {
        bool foundSelectedMesh = false;

        for (const ModelImportInspectionState::Entry &entry : inspection.entries)
        {
            if (toLowerCopy(trimCopy(entry.name)) == toLowerCopy(trimCopy(m_bmodelImportSelectedMeshName)))
            {
                foundSelectedMesh = true;
                break;
            }
        }

        if (!foundSelectedMesh)
        {
            m_bmodelImportSelectedMeshName.clear();
        }
    }

    if (beginInspectorSectionBlock("Model Import", false))
    {
        if (beginInspectorPropertyTable("BModelModelImport"))
        {
            beginInspectorFieldRow("Model Path");
            ImGui::InputText("##BModelImportPath", m_bmodelImportPath, sizeof(m_bmodelImportPath));

            beginInspectorFieldRow("Import Scale");
            ImGui::InputFloat("##BModelImportScale", &m_bmodelImportScale, 0.1f, 1.0f, "%.3f");

            std::string defaultTextureName = m_bmodelImportDefaultTexture;
            const bool texturePickerChanged =
                renderBitmapTextureSelector(session, "Default Texture (Optional)", defaultTextureName);

            beginInspectorFieldRow("Default Texture Raw");
            char defaultTextureBuffer[64] = {};
            std::snprintf(defaultTextureBuffer, sizeof(defaultTextureBuffer), "%s", defaultTextureName.c_str());
            const bool rawTextureChanged =
                ImGui::InputText("##BModelImportDefaultTextureRaw", defaultTextureBuffer, sizeof(defaultTextureBuffer));

            if (rawTextureChanged)
            {
                defaultTextureName = defaultTextureBuffer;
            }

            if (texturePickerChanged || rawTextureChanged)
            {
                std::snprintf(
                    m_bmodelImportDefaultTexture,
                    sizeof(m_bmodelImportDefaultTexture),
                    "%s",
                    defaultTextureName.c_str());
            }

            beginInspectorFieldRow("Merge Coplanar");
            ImGui::Checkbox("##BModelImportMergeCoplanarFaces", &m_bmodelImportMergeCoplanarFaces);

            if (canSplitByMesh)
            {
                beginInspectorFieldRow("Source Mesh");
                ImGui::BeginDisabled(inspection.entries.empty());
                renderImportedModelSelector(
                    "##BModelImportSourceMesh",
                    inspection,
                    m_bmodelImportSelectedMeshName);
                ImGui::EndDisabled();
            }

            ImGui::EndTable();
        }

        if (canSplitByMesh)
        {
            if (!inspection.errorMessage.empty())
            {
                ImGui::TextColored(colorFromRgb(0xE7A46C), "%s", inspection.errorMessage.c_str());
            }
            else
            {
                ImGui::TextDisabled("%s", importedModelSummaryText(inspection.entries.size()).c_str());

                if (!inspection.entries.empty())
                {
                    renderImportedModelInspectionTable(
                        "BModelImportMeshes",
                        inspection,
                        m_bmodelImportSelectedMeshName,
                        108.0f);
                    renderImportedModelInspectionSummary(inspection, m_bmodelImportSelectedMeshName);
                }
            }
        }

        if (ImGui::Button("Browse...", ImVec2(120.0f, 0.0f)))
        {
            openModelFileBrowser(ModelImportTarget::ReplaceSelectedBModel, m_bmodelImportPath);
        }

        ImGui::SameLine();

        if (ImGui::Button("Replace From Model", ImVec2(150.0f, 0.0f)))
        {
            std::string errorMessage;
            const std::string sourceMeshName =
                canSplitByMesh ? m_bmodelImportSelectedMeshName : std::string();

            if (!session.replaceSelectedBModelFromModel(
                    m_bmodelImportPath,
                    m_bmodelImportScale,
                    m_bmodelImportDefaultTexture,
                    sourceMeshName,
                    m_bmodelImportMergeCoplanarFaces,
                    errorMessage))
            {
                session.logError(errorMessage);
            }
            else
            {
                rememberModelImportDirectory(m_bmodelImportPath);
            }
        }

        ImGui::SameLine();

        if (!hasRememberedImportSource)
        {
            ImGui::BeginDisabled();
        }

        if (ImGui::Button("Reimport", ImVec2(110.0f, 0.0f)))
        {
            std::string errorMessage;
            const std::optional<EditorBModelImportSource> importSource = session.bmodelImportSource(bmodelIndex);

            if (!session.reimportSelectedBModel(errorMessage))
            {
                session.logError(errorMessage);
            }
            else if (importSource)
            {
                rememberModelImportDirectory(importSource->sourcePath.c_str());
            }
        }

        if (!hasRememberedImportSource)
        {
            ImGui::EndDisabled();
        }

        if (const std::optional<EditorBModelImportSource> importSource = session.bmodelImportSource(bmodelIndex))
        {
            ImGui::TextWrapped("Remembered Source: %s", importSource->sourcePath.c_str());

            EditorBModelImportSource updatedImportSource = *importSource;
            bool importSourceChanged = false;

            if (beginInspectorPropertyTable("BModelRememberedImportSettings"))
            {
                if (!trimCopy(updatedImportSource.sourceMeshName).empty())
                {
                    beginInspectorFieldRow("Remembered Mesh");
                    ImGui::TextUnformatted(updatedImportSource.sourceMeshName.c_str());
                }

                std::string rememberedDefaultTextureName = updatedImportSource.defaultTextureName;
                const bool rememberedTexturePickerChanged =
                    renderBitmapTextureSelector(
                        session,
                        "Remembered Default Texture (Optional)",
                        rememberedDefaultTextureName);

                beginInspectorFieldRow("Remembered Default Raw");
                char rememberedTextureBuffer[64] = {};
                std::snprintf(
                    rememberedTextureBuffer,
                    sizeof(rememberedTextureBuffer),
                    "%s",
                    rememberedDefaultTextureName.c_str());
                const bool rememberedTextureRawChanged = ImGui::InputText(
                    "##BModelRememberedDefaultTextureRaw",
                    rememberedTextureBuffer,
                    sizeof(rememberedTextureBuffer));

                if (rememberedTextureRawChanged)
                {
                    rememberedDefaultTextureName = rememberedTextureBuffer;
                }

                if (rememberedTexturePickerChanged || rememberedTextureRawChanged)
                {
                    updatedImportSource.defaultTextureName = rememberedDefaultTextureName;
                    importSourceChanged = true;
                }

                ImGui::EndTable();
            }

            const std::vector<EditorImportedMaterialDiagnostic> materialDiagnostics =
                session.importedMaterialDiagnostics(bmodelIndex);
            std::unordered_map<std::string, EditorImportedMaterialDiagnostic> diagnosticByMaterial;

            for (const EditorImportedMaterialDiagnostic &diagnostic : materialDiagnostics)
            {
                diagnosticByMaterial.emplace(
                    toLowerCopy(trimCopy(diagnostic.sourceMaterialName)),
                    diagnostic);
            }

            ImGui::TextDisabled("Material Remaps");

            if (ImGui::BeginTable("BModelMaterialRemaps", 3, ImGuiTableFlags_SizingStretchProp))
            {
                ImGui::TableSetupColumn("Material", ImGuiTableColumnFlags_WidthStretch, 0.45f);
                ImGui::TableSetupColumn("Texture", ImGuiTableColumnFlags_WidthStretch, 0.45f);
                ImGui::TableSetupColumn("Action", ImGuiTableColumnFlags_WidthFixed, 64.0f);
                ImGui::TableHeadersRow();

                for (size_t remapIndex = 0; remapIndex < updatedImportSource.materialRemaps.size(); ++remapIndex)
                {
                    EditorMaterialTextureRemap &remap = updatedImportSource.materialRemaps[remapIndex];
                    const std::string remapKey = toLowerCopy(trimCopy(remap.sourceMaterialName));
                    const auto diagnosticIt = diagnosticByMaterial.find(remapKey);
                    const bool hasDiagnostic = diagnosticIt != diagnosticByMaterial.end();
                    const bool unresolvedRow = hasDiagnostic && !diagnosticIt->second.resolvesToKnownBitmap;
                    const bool defaultFallbackRow = hasDiagnostic && diagnosticIt->second.usesDefaultFallback;
                    ImGui::PushID(static_cast<int>(remapIndex));
                    ImGui::TableNextRow();

                    if (unresolvedRow)
                    {
                        ImGui::TableSetBgColor(ImGuiTableBgTarget_RowBg0, ImGui::GetColorU32(colorFromRgb(0x3E2A24)));
                    }
                    else if (defaultFallbackRow)
                    {
                        ImGui::TableSetBgColor(ImGuiTableBgTarget_RowBg0, ImGui::GetColorU32(colorFromRgb(0x353123)));
                    }

                    ImGui::TableSetColumnIndex(0);
                    char materialBuffer[128] = {};
                    std::snprintf(materialBuffer, sizeof(materialBuffer), "%s", remap.sourceMaterialName.c_str());

                    if (ImGui::InputText("##Material", materialBuffer, sizeof(materialBuffer)))
                    {
                        remap.sourceMaterialName = materialBuffer;
                        importSourceChanged = true;
                    }

                    if (hasDiagnostic && ImGui::IsItemHovered())
                    {
                        ImGui::SetTooltip(
                            "%s",
                            unresolvedRow ? "Material does not resolve to a known bitmap."
                            : (defaultFallbackRow
                                ? "Material currently falls back to the remembered default texture."
                                : "Material resolves cleanly."));
                    }

                    ImGui::TableSetColumnIndex(1);
                    if (renderInlineBitmapTextureSelector(session, "##Texture", remap.textureName, bmodelIndex))
                    {
                        importSourceChanged = true;
                    }

                    ImGui::TableSetColumnIndex(2);

                    if (ImGui::Button("Remove"))
                    {
                        updatedImportSource.materialRemaps.erase(
                            updatedImportSource.materialRemaps.begin() + static_cast<ptrdiff_t>(remapIndex));
                        importSourceChanged = true;
                        ImGui::PopID();
                        break;
                    }

                    ImGui::PopID();
                }

                ImGui::EndTable();
            }

            if (ImGui::Button("Add Remap", ImVec2(120.0f, 0.0f)))
            {
                updatedImportSource.materialRemaps.push_back({});
                importSourceChanged = true;
            }

            ImGui::SameLine();

            if (ImGui::Button("Apply Default To Unresolved", ImVec2(190.0f, 0.0f)))
            {
                for (EditorMaterialTextureRemap &remap : updatedImportSource.materialRemaps)
                {
                    const std::string remapKey = toLowerCopy(trimCopy(remap.sourceMaterialName));
                    const auto diagnosticIt = diagnosticByMaterial.find(remapKey);
                    const bool unresolvedRow =
                        diagnosticIt != diagnosticByMaterial.end()
                        && (!diagnosticIt->second.resolvesToKnownBitmap || diagnosticIt->second.usesDefaultFallback);

                    if (unresolvedRow || trimCopy(remap.textureName).empty())
                    {
                        remap.textureName = updatedImportSource.defaultTextureName;
                        importSourceChanged = true;
                    }
                }
            }

            ImGui::SameLine();

            if (ImGui::Button("Clear Remaps", ImVec2(120.0f, 0.0f)))
            {
                if (!updatedImportSource.materialRemaps.empty())
                {
                    updatedImportSource.materialRemaps.clear();
                    importSourceChanged = true;
                }
            }

            if (!materialDiagnostics.empty())
            {
                ImGui::Spacing();
                ImGui::TextDisabled("Source Material Status");

                if (ImGui::BeginTable("BModelMaterialDiagnostics", 3, ImGuiTableFlags_SizingStretchProp))
                {
                    ImGui::TableSetupColumn("Material", ImGuiTableColumnFlags_WidthStretch, 0.4f);
                    ImGui::TableSetupColumn("Resolved", ImGuiTableColumnFlags_WidthStretch, 0.35f);
                    ImGui::TableSetupColumn("Status", ImGuiTableColumnFlags_WidthStretch, 0.25f);
                    ImGui::TableHeadersRow();

                    for (const EditorImportedMaterialDiagnostic &diagnostic : materialDiagnostics)
                    {
                        const ImVec4 statusColor = !diagnostic.resolvesToKnownBitmap
                            ? colorFromRgb(0xE7A46C)
                            : (diagnostic.usesDefaultFallback
                                ? colorFromRgb(0xD8C38A)
                                : colorFromRgb(0xC7D2DC));
                        const char *pStatusText = !diagnostic.resolvesToKnownBitmap
                            ? "Missing"
                            : (diagnostic.usesDefaultFallback
                                ? "Default"
                                : (diagnostic.hasExplicitRemap ? "Remapped" : "Direct"));

                        ImGui::TableNextRow();
                        ImGui::TableSetColumnIndex(0);
                        ImGui::TextUnformatted(diagnostic.sourceMaterialName.c_str());
                        ImGui::TableSetColumnIndex(1);
                        ImGui::TextUnformatted(
                            diagnostic.resolvedTextureName.empty() ? "<none>" : diagnostic.resolvedTextureName.c_str());
                        ImGui::TableSetColumnIndex(2);
                        ImGui::TextColored(statusColor, "%s", pStatusText);
                    }

                    ImGui::EndTable();
                }

                if (ImGui::Button("Add Unresolved To Remaps", ImVec2(190.0f, 0.0f)))
                {
                    std::unordered_set<std::string> existingRemaps;

                    for (const EditorMaterialTextureRemap &remap : updatedImportSource.materialRemaps)
                    {
                        existingRemaps.insert(toLowerCopy(trimCopy(remap.sourceMaterialName)));
                    }

                    for (const EditorImportedMaterialDiagnostic &diagnostic : materialDiagnostics)
                    {
                        const std::string remapKey = toLowerCopy(trimCopy(diagnostic.sourceMaterialName));

                        if (existingRemaps.contains(remapKey))
                        {
                            continue;
                        }

                        if (diagnostic.resolvesToKnownBitmap && !diagnostic.usesDefaultFallback)
                        {
                            continue;
                        }

                        updatedImportSource.materialRemaps.push_back(
                            {diagnostic.sourceMaterialName, updatedImportSource.defaultTextureName});
                        existingRemaps.insert(remapKey);
                        importSourceChanged = true;
                    }
                }
            }

            if (ImGui::Button("Capture Current Face Textures", ImVec2(220.0f, 0.0f)))
            {
                std::string errorMessage;

                if (!session.captureSelectedBModelMaterialRemaps(errorMessage))
                {
                    session.logError(errorMessage);
                }
            }

            if (importSourceChanged)
            {
                session.captureUndoSnapshot();
                session.document().setOutdoorBModelImportSource(bmodelIndex, updatedImportSource);
                session.noteDocumentMutated({});
            }
        }
        else if (!hasModelImportPath)
        {
            ImGui::TextDisabled("Enter a model path or use Browse... .");
        }

        ImGui::TextDisabled("Use Create -> Import BModel... to append a new bmodel.");
        endInspectorSectionBlock();
    }
}

void EditorMainWindow::renderInteractiveFaceInspector(EditorSession &session) const
{
    EditorDocument &document = session.document();
    Game::OutdoorSceneData &sceneData = document.mutableOutdoorSceneData();
    Game::OutdoorMapData &outdoorGeometry = document.mutableOutdoorGeometry();
    size_t bmodelIndex = 0;
    size_t faceIndex = 0;

    if (!decodeFlattenedOutdoorFaceIndex(outdoorGeometry, session.selection().index, bmodelIndex, faceIndex))
    {
        ImGui::TextUnformatted("Select a bmodel face from the viewport in Face mode.");
        return;
    }

    if (bmodelIndex >= outdoorGeometry.bmodels.size() || faceIndex >= outdoorGeometry.bmodels[bmodelIndex].faces.size())
    {
        ImGui::TextUnformatted("Selected face is out of range.");
        return;
    }

    Game::OutdoorBModelFace &baseFace = outdoorGeometry.bmodels[bmodelIndex].faces[faceIndex];
    Game::OutdoorSceneInteractiveFace *pInteractiveFace = findInteractiveFace(sceneData, bmodelIndex, faceIndex);
    const std::vector<size_t> &selectedFaceIndices = session.selectedInteractiveFaceIndices();
    bool changed = false;

    ImGui::Text("BModel: %zu", bmodelIndex);
    ImGui::Text("Face: %zu", faceIndex);
    ImGui::Text("Texture: %s", baseFace.textureName.empty() ? "<none>" : baseFace.textureName.c_str());
    ImGui::Text("Polygon Type: %u", baseFace.polygonType);
    ImGui::Text("Walkable: %s", Game::isOutdoorWalkablePolygonType(baseFace.polygonType) ? "yes" : "no");
    ImGui::Text("Has Scene Entry: %s", pInteractiveFace != nullptr ? "yes" : "no");

    const auto forEachSelectedFace =
        [&](const auto &callback)
    {
        for (size_t flatIndex : selectedFaceIndices)
        {
            size_t selectedBModelIndex = 0;
            size_t selectedFaceIndex = 0;

            if (!decodeFlattenedOutdoorFaceIndex(
                    outdoorGeometry,
                    flatIndex,
                    selectedBModelIndex,
                    selectedFaceIndex))
            {
                continue;
            }

            callback(
                flatIndex,
                selectedBModelIndex,
                selectedFaceIndex,
                outdoorGeometry.bmodels[selectedBModelIndex].faces[selectedFaceIndex]);
        }
    };

    renderInspectorSectionHeader("Selection");
    ImGui::Text("Selected Faces: %zu", selectedFaceIndices.size());

    if (ImGui::Button("Select All On BModel", ImVec2(170.0f, 0.0f)))
    {
        session.clearInteractiveFaceSelection();

        for (size_t currentFaceIndex = 0; currentFaceIndex < outdoorGeometry.bmodels[bmodelIndex].faces.size(); ++currentFaceIndex)
        {
            session.addInteractiveFaceSelection(flattenedOutdoorFaceIndex(outdoorGeometry, bmodelIndex, currentFaceIndex));
        }
    }

    ImGui::SameLine();

    if (ImGui::Button("Keep Only Current", ImVec2(160.0f, 0.0f)))
    {
        session.replaceInteractiveFaceSelection(flattenedOutdoorFaceIndex(outdoorGeometry, bmodelIndex, faceIndex));
    }

    renderInspectorSectionHeader("Selection Actions");

    if (ImGui::Button("Apply Texture To Selected", ImVec2(190.0f, 0.0f)))
    {
        session.captureUndoSnapshot();
        forEachSelectedFace(
            [&](size_t, size_t, size_t, Game::OutdoorBModelFace &selectedFace)
            {
                selectedFace.textureName = baseFace.textureName;
            });
        changed = true;
    }

    ImGui::SameLine();

    if (ImGui::Button("Apply Mapping To Selected", ImVec2(190.0f, 0.0f)))
    {
        session.captureUndoSnapshot();
        forEachSelectedFace(
            [&](size_t, size_t, size_t, Game::OutdoorBModelFace &selectedFace)
            {
                if (selectedFace.vertexIndices.size() != baseFace.vertexIndices.size())
                {
                    return;
                }

                selectedFace.textureUs = baseFace.textureUs;
                selectedFace.textureVs = baseFace.textureVs;
                selectedFace.textureDeltaU = baseFace.textureDeltaU;
                selectedFace.textureDeltaV = baseFace.textureDeltaV;
            });
        changed = true;
    }

    if (ImGui::Button("Apply Scene Override To Selected", ImVec2(220.0f, 0.0f)))
    {
        if (pInteractiveFace != nullptr)
        {
            session.captureUndoSnapshot();
            forEachSelectedFace(
                [&](size_t, size_t selectedBModelIndex, size_t selectedFaceIndex, Game::OutdoorBModelFace &selectedFace)
                {
                    Game::OutdoorSceneInteractiveFace *pSelectedInteractiveFace =
                        findInteractiveFace(sceneData, selectedBModelIndex, selectedFaceIndex);

                    if (pSelectedInteractiveFace == nullptr)
                    {
                        sceneData.interactiveFaces.push_back({
                            selectedBModelIndex,
                            selectedFaceIndex,
                            selectedFace.attributes,
                            selectedFace.cogNumber,
                            selectedFace.cogTriggeredNumber,
                            selectedFace.cogTrigger});
                        pSelectedInteractiveFace = &sceneData.interactiveFaces.back();
                    }

                    pSelectedInteractiveFace->legacyAttributes = pInteractiveFace->legacyAttributes;
                    pSelectedInteractiveFace->cogNumber = pInteractiveFace->cogNumber;
                    pSelectedInteractiveFace->cogTriggeredNumber = pInteractiveFace->cogTriggeredNumber;
                    pSelectedInteractiveFace->cogTrigger = pInteractiveFace->cogTrigger;
                });
            changed = true;
        }
    }

    ImGui::BeginDisabled(pInteractiveFace == nullptr);
    ImGui::SameLine();
    if (ImGui::Button("Reset Selected Scene Overrides", ImVec2(230.0f, 0.0f)))
    {
        session.captureUndoSnapshot();
        sceneData.interactiveFaces.erase(
            std::remove_if(
                sceneData.interactiveFaces.begin(),
                sceneData.interactiveFaces.end(),
                [&session, &outdoorGeometry](const Game::OutdoorSceneInteractiveFace &interactiveFace)
                {
                    const size_t flatIndex = flattenedOutdoorFaceIndex(
                        outdoorGeometry,
                        interactiveFace.bmodelIndex,
                        interactiveFace.faceIndex);
                    return session.isInteractiveFaceSelected(flatIndex);
                }),
            sceneData.interactiveFaces.end());
        changed = true;
        pInteractiveFace = findInteractiveFace(sceneData, bmodelIndex, faceIndex);
    }
    ImGui::EndDisabled();

    renderInspectorSectionHeader("Clipboard");

    if (ImGui::Button("Copy Face Setup", ImVec2(150.0f, 0.0f)))
    {
        m_faceClipboard.valid = true;
        m_faceClipboard.textureName = baseFace.textureName;
        m_faceClipboard.textureUs = baseFace.textureUs;
        m_faceClipboard.textureVs = baseFace.textureVs;
        m_faceClipboard.textureDeltaU = baseFace.textureDeltaU;
        m_faceClipboard.textureDeltaV = baseFace.textureDeltaV;
        m_faceClipboard.hasSceneOverride = pInteractiveFace != nullptr;
        m_faceClipboard.sceneLegacyAttributes = pInteractiveFace != nullptr ? pInteractiveFace->legacyAttributes : 0;
        m_faceClipboard.sceneCogNumber = pInteractiveFace != nullptr ? pInteractiveFace->cogNumber : 0;
        m_faceClipboard.sceneCogTriggeredNumber = pInteractiveFace != nullptr ? pInteractiveFace->cogTriggeredNumber : 0;
        m_faceClipboard.sceneCogTrigger = pInteractiveFace != nullptr ? pInteractiveFace->cogTrigger : 0;
    }

    ImGui::BeginDisabled(!m_faceClipboard.valid);
    ImGui::SameLine();
    if (ImGui::Button("Paste Visual", ImVec2(120.0f, 0.0f)))
    {
        session.captureUndoSnapshot();
        forEachSelectedFace(
            [this](size_t, size_t, size_t, Game::OutdoorBModelFace &selectedFace)
            {
                selectedFace.textureName = m_faceClipboard.textureName;

                if (selectedFace.vertexIndices.size() == m_faceClipboard.textureUs.size())
                {
                    selectedFace.textureUs = m_faceClipboard.textureUs;
                    selectedFace.textureVs = m_faceClipboard.textureVs;
                }

                selectedFace.textureDeltaU = m_faceClipboard.textureDeltaU;
                selectedFace.textureDeltaV = m_faceClipboard.textureDeltaV;
            });
        changed = true;
    }

    if (ImGui::Button("Paste Gameplay", ImVec2(130.0f, 0.0f)))
    {
        if (m_faceClipboard.hasSceneOverride)
        {
            session.captureUndoSnapshot();
            forEachSelectedFace(
                [this, &sceneData](size_t, size_t selectedBModelIndex, size_t selectedFaceIndex, Game::OutdoorBModelFace &selectedFace)
                {
                    Game::OutdoorSceneInteractiveFace *pSelectedInteractiveFace =
                        findInteractiveFace(sceneData, selectedBModelIndex, selectedFaceIndex);

                    if (pSelectedInteractiveFace == nullptr)
                    {
                        sceneData.interactiveFaces.push_back({
                            selectedBModelIndex,
                            selectedFaceIndex,
                            selectedFace.attributes,
                            selectedFace.cogNumber,
                            selectedFace.cogTriggeredNumber,
                            selectedFace.cogTrigger});
                        pSelectedInteractiveFace = &sceneData.interactiveFaces.back();
                    }

                    pSelectedInteractiveFace->legacyAttributes = m_faceClipboard.sceneLegacyAttributes;
                    pSelectedInteractiveFace->cogNumber = m_faceClipboard.sceneCogNumber;
                    pSelectedInteractiveFace->cogTriggeredNumber = m_faceClipboard.sceneCogTriggeredNumber;
                    pSelectedInteractiveFace->cogTrigger = m_faceClipboard.sceneCogTrigger;
                });
            changed = true;
            pInteractiveFace = findInteractiveFace(sceneData, bmodelIndex, faceIndex);
        }
    }

    ImGui::SameLine();

    if (ImGui::Button("Paste All", ImVec2(110.0f, 0.0f)))
    {
        session.captureUndoSnapshot();
        forEachSelectedFace(
            [this, &sceneData](size_t, size_t selectedBModelIndex, size_t selectedFaceIndex, Game::OutdoorBModelFace &selectedFace)
            {
                selectedFace.textureName = m_faceClipboard.textureName;

                if (selectedFace.vertexIndices.size() == m_faceClipboard.textureUs.size())
                {
                    selectedFace.textureUs = m_faceClipboard.textureUs;
                    selectedFace.textureVs = m_faceClipboard.textureVs;
                }

                selectedFace.textureDeltaU = m_faceClipboard.textureDeltaU;
                selectedFace.textureDeltaV = m_faceClipboard.textureDeltaV;

                if (!m_faceClipboard.hasSceneOverride)
                {
                    return;
                }

                Game::OutdoorSceneInteractiveFace *pSelectedInteractiveFace =
                    findInteractiveFace(sceneData, selectedBModelIndex, selectedFaceIndex);

                if (pSelectedInteractiveFace == nullptr)
                {
                    sceneData.interactiveFaces.push_back({
                        selectedBModelIndex,
                        selectedFaceIndex,
                        selectedFace.attributes,
                        selectedFace.cogNumber,
                        selectedFace.cogTriggeredNumber,
                        selectedFace.cogTrigger});
                    pSelectedInteractiveFace = &sceneData.interactiveFaces.back();
                }

                pSelectedInteractiveFace->legacyAttributes = m_faceClipboard.sceneLegacyAttributes;
                pSelectedInteractiveFace->cogNumber = m_faceClipboard.sceneCogNumber;
                pSelectedInteractiveFace->cogTriggeredNumber = m_faceClipboard.sceneCogTriggeredNumber;
                pSelectedInteractiveFace->cogTrigger = m_faceClipboard.sceneCogTrigger;
            });
        changed = true;
        pInteractiveFace = findInteractiveFace(sceneData, bmodelIndex, faceIndex);
    }
    ImGui::EndDisabled();

    renderInspectorSectionHeader("Visual");
    if (beginInspectorPropertyTable("InteractiveFaceVisualFields"))
    {
        changed = renderBitmapTextureSelector(session, "Texture", baseFace.textureName, bmodelIndex) || changed;
        changed = editStringField(session, "Texture Name Raw", baseFace.textureName, 11) || changed;
        ImGui::EndTable();
    }

    if (pInteractiveFace == nullptr)
    {
        if (ImGui::Button("Add Interactive Face Entry"))
        {
            session.captureUndoSnapshot();
            sceneData.interactiveFaces.push_back({
                bmodelIndex,
                faceIndex,
                baseFace.attributes,
                baseFace.cogNumber,
                baseFace.cogTriggeredNumber,
                baseFace.cogTrigger});
            pInteractiveFace = &sceneData.interactiveFaces.back();
            changed = true;
        }
    }
    else if (ImGui::Button("Remove Interactive Face Entry"))
    {
        session.captureUndoSnapshot();
        sceneData.interactiveFaces.erase(
            std::remove_if(
                sceneData.interactiveFaces.begin(),
                sceneData.interactiveFaces.end(),
                [bmodelIndex, faceIndex](const Game::OutdoorSceneInteractiveFace &interactiveFace)
                {
                    return interactiveFace.bmodelIndex == bmodelIndex && interactiveFace.faceIndex == faceIndex;
                }),
            sceneData.interactiveFaces.end());
        changed = true;
        pInteractiveFace = nullptr;
    }

    ImGui::SameLine();

    if (ImGui::Button("Delete Face", ImVec2(140.0f, 0.0f)))
    {
        session.captureUndoSnapshot();
        Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];
        bmodel.faces.erase(bmodel.faces.begin() + static_cast<ptrdiff_t>(faceIndex));
        bmodel.bspNodes.clear();
        repairOutdoorSceneFaceReferencesAfterDelete(sceneData, bmodelIndex, faceIndex);
        recomputeBModelMetadata(bmodel);

        if (!bmodel.faces.empty())
        {
            const size_t replacementFaceIndex = std::min(faceIndex, bmodel.faces.size() - 1);
            session.select(
                EditorSelectionKind::InteractiveFace,
                flattenedOutdoorFaceIndex(outdoorGeometry, bmodelIndex, replacementFaceIndex));
        }
        else
        {
            session.select(EditorSelectionKind::BModel, bmodelIndex);
        }

        changed = true;
        pInteractiveFace = nullptr;
    }

    if (pInteractiveFace != nullptr)
    {
        renderInspectorSectionHeader("Scene Override");
        ImGui::PushID("SceneOverride");
        if (beginInspectorPropertyTable("InteractiveFaceFields"))
        {
            changed = editBitCheckbox(session, "Fluid", pInteractiveFace->legacyAttributes, FaceAttributeFluid) || changed;
            changed =
                editBitCheckbox(session, "Invisible", pInteractiveFace->legacyAttributes, FaceAttributeInvisible)
                || changed;
            changed =
                editBitCheckbox(session, "Has Hint", pInteractiveFace->legacyAttributes, FaceAttributeHasHint)
                || changed;
            changed =
                editBitCheckbox(session, "Clickable", pInteractiveFace->legacyAttributes, FaceAttributeClickable)
                || changed;
            changed = editBitCheckbox(
                session,
                "Pressure Plate",
                pInteractiveFace->legacyAttributes,
                FaceAttributePressurePlate) || changed;
            changed = editBitCheckbox(
                session,
                "Untouchable",
                pInteractiveFace->legacyAttributes,
                FaceAttributeUntouchable) || changed;
            changed = editUInt32Field(session, "Legacy Attributes", pInteractiveFace->legacyAttributes) || changed;
            changed = editUInt16Field(session, "COG Number", pInteractiveFace->cogNumber) || changed;
            changed = editMapEventField(
                session,
                "COG Triggered Number",
                pInteractiveFace->cogTriggeredNumber) || changed;
            renderResolvedMapEventField(session, "Resolved Event", pInteractiveFace->cogTriggeredNumber);
            changed = editUInt16Field(session, "COG Trigger", pInteractiveFace->cogTrigger) || changed;
            ImGui::EndTable();
        }
        ImGui::PopID();
    }
    else
    {
        ImGui::Spacing();
        ImGui::TextDisabled("No scene override. Add an Interactive Face Entry for gameplay-visible changes.");
    }

    ImGui::SetNextItemOpen(false, ImGuiCond_FirstUseEver);
    if (ImGui::CollapsingHeader("Base ODM Face"))
    {
        if (beginInspectorPropertyTable("InteractiveFaceBaseFields"))
        {
            const bx::Vec3 baseNormal = faceNormal(outdoorGeometry.bmodels[bmodelIndex].vertices, baseFace);
            const float outwardDot = faceOutwardDot(
                outdoorGeometry.bmodels[bmodelIndex].vertices,
                baseFace,
                static_cast<float>(outdoorGeometry.bmodels[bmodelIndex].boundingCenterX),
                static_cast<float>(outdoorGeometry.bmodels[bmodelIndex].boundingCenterY),
                static_cast<float>(outdoorGeometry.bmodels[bmodelIndex].boundingCenterZ));
            renderInspectorReadOnlyField(
                "Normal",
                std::to_string(baseNormal.x).substr(0, 5) + ", "
                    + std::to_string(baseNormal.y).substr(0, 5) + ", "
                    + std::to_string(baseNormal.z).substr(0, 5));
            renderInspectorReadOnlyField("Outward Dot", std::to_string(outwardDot));
            renderInspectorReadOnlyField("Legacy Attributes Raw", std::to_string(baseFace.attributes));
            renderInspectorReadOnlyField("COG Number", std::to_string(baseFace.cogNumber));
            renderInspectorReadOnlyField("COG Triggered Number", std::to_string(baseFace.cogTriggeredNumber));
            renderInspectorReadOnlyField("COG Trigger", std::to_string(baseFace.cogTrigger));
            renderInspectorReadOnlyField("Fluid", (baseFace.attributes & FaceAttributeFluid) != 0 ? "true" : "false");
            renderInspectorReadOnlyField(
                "Invisible",
                (baseFace.attributes & FaceAttributeInvisible) != 0 ? "true" : "false");
            renderInspectorReadOnlyField(
                "Has Hint",
                (baseFace.attributes & FaceAttributeHasHint) != 0 ? "true" : "false");
            renderInspectorReadOnlyField(
                "Clickable",
                (baseFace.attributes & FaceAttributeClickable) != 0 ? "true" : "false");
            renderInspectorReadOnlyField(
                "Pressure Plate",
                (baseFace.attributes & FaceAttributePressurePlate) != 0 ? "true" : "false");
            renderInspectorReadOnlyField(
                "Untouchable",
                (baseFace.attributes & FaceAttributeUntouchable) != 0 ? "true" : "false");
            ImGui::EndTable();
        }

        ImGui::TextDisabled("Outdoor gameplay uses the scene override entry above, not the raw ODM face values.");

        if (ImGui::Button("Flip Selected Faces", ImVec2(170.0f, 0.0f)))
        {
            session.captureUndoSnapshot();
            forEachSelectedFace(
                [&](size_t, size_t, size_t, Game::OutdoorBModelFace &selectedFace)
                {
                    reverseFaceWinding(selectedFace);
                });
            changed = true;
        }

        ImGui::SameLine();

        if (ImGui::Button("Recompute Outward On BModel", ImVec2(230.0f, 0.0f)))
        {
            session.captureUndoSnapshot();
            Game::OutdoorBModel &bmodel = outdoorGeometry.bmodels[bmodelIndex];
            const float modelCenterX = static_cast<float>(bmodel.boundingCenterX);
            const float modelCenterY = static_cast<float>(bmodel.boundingCenterY);
            const float modelCenterZ = static_cast<float>(bmodel.boundingCenterZ);

            for (Game::OutdoorBModelFace &face : bmodel.faces)
            {
                orientFaceWindingOutward(bmodel.vertices, face, modelCenterX, modelCenterY, modelCenterZ);
            }

            changed = true;
        }
    }

    ImGui::SetNextItemOpen(false, ImGuiCond_FirstUseEver);
    if (ImGui::CollapsingHeader("Texture Mapping"))
    {
        int textureWidth = 256;
        int textureHeight = 256;
        ensureBitmapPreviewTexture(session, baseFace.textureName);

        if (const std::optional<std::pair<int, int>> size = bitmapPreviewTextureSize(baseFace.textureName))
        {
            textureWidth = size->first;
            textureHeight = size->second;
        }

        if (beginInspectorPropertyTable("InteractiveFaceTextureMappingFields"))
        {
            changed = editInt16Field(session, "Offset U", baseFace.textureDeltaU) || changed;
            changed = editInt16Field(session, "Offset V", baseFace.textureDeltaV) || changed;

            const auto [minU, maxU] = faceTextureCoordinateRange(baseFace.textureUs);
            const auto [minV, maxV] = faceTextureCoordinateRange(baseFace.textureVs);
            renderInspectorReadOnlyField("U Range", std::to_string(minU) + " .. " + std::to_string(maxU));
            renderInspectorReadOnlyField("V Range", std::to_string(minV) + " .. " + std::to_string(maxV));
            renderInspectorReadOnlyField(
                "Texture Size",
                std::to_string(textureWidth) + " x " + std::to_string(textureHeight));
            ImGui::EndTable();
        }

        const auto applyTextureMappingAction = [&session, &changed](auto action)
        {
            session.captureUndoSnapshot();
            action();
            changed = true;
        };

        if (ImGui::Button("Flip U", ImVec2(110.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace]()
            {
                flipFaceTextureAxis(baseFace.textureUs);
            });
        }

        ImGui::SameLine();

        if (ImGui::Button("Flip V", ImVec2(110.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace]()
            {
                flipFaceTextureAxis(baseFace.textureVs);
            });
        }

        ImGui::SameLine();

        if (ImGui::Button("Rotate UV 90", ImVec2(120.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace, textureWidth, textureHeight]()
            {
                for (size_t index = 0; index < baseFace.textureUs.size() && index < baseFace.textureVs.size(); ++index)
                {
                    const int oldU = baseFace.textureUs[index];
                    const int oldV = baseFace.textureVs[index];
                    baseFace.textureUs[index] = clampToInt16(textureWidth - oldV);
                    baseFace.textureVs[index] = clampToInt16(oldU);
                }
            });
        }

        if (ImGui::Button("Fit Once", ImVec2(110.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace, textureWidth, textureHeight]()
            {
                fitFaceTextureAxis(baseFace.textureUs, textureWidth);
                fitFaceTextureAxis(baseFace.textureVs, textureHeight);
                baseFace.textureDeltaU = 0;
                baseFace.textureDeltaV = 0;
            });
        }

        ImGui::SameLine();

        if (ImGui::Button("Reset Mapping", ImVec2(120.0f, 0.0f)))
        {
            applyTextureMappingAction([&outdoorGeometry, &baseFace, bmodelIndex]()
            {
                resetFaceTextureMappingFromGeometry(outdoorGeometry.bmodels[bmodelIndex].vertices, baseFace);
            });
        }

        ImGui::SameLine();

        if (ImGui::Button("Tile U x2", ImVec2(110.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace]()
            {
                scaleFaceTextureAxis(baseFace.textureUs, 2.0f);
            });
        }

        ImGui::SameLine();

        if (ImGui::Button("Tile V x2", ImVec2(110.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace]()
            {
                scaleFaceTextureAxis(baseFace.textureVs, 2.0f);
            });
        }

        if (ImGui::Button("Stretch U", ImVec2(110.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace]()
            {
                scaleFaceTextureAxis(baseFace.textureUs, 0.5f);
            });
        }

        ImGui::SameLine();

        if (ImGui::Button("Stretch V", ImVec2(110.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace]()
            {
                scaleFaceTextureAxis(baseFace.textureVs, 0.5f);
            });
        }

        ImGui::SameLine();

        if (ImGui::Button("Reset Offset", ImVec2(120.0f, 0.0f)))
        {
            applyTextureMappingAction([&baseFace]()
            {
                baseFace.textureDeltaU = 0;
                baseFace.textureDeltaV = 0;
            });
        }
    }

    if (changed)
    {
        if (baseFace.textureName.size() > 10)
        {
            baseFace.textureName.resize(10);
        }

        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderEntityInspector(EditorSession &session, size_t entityIndex) const
{
    std::vector<Game::OutdoorSceneEntity> &entities = session.document().mutableOutdoorSceneData().entities;

    if (entityIndex >= entities.size())
    {
        ImGui::TextUnformatted("Selected entity index is out of range.");
        return;
    }

    Game::OutdoorSceneEntity &entity = entities[entityIndex];
    bool changed = false;

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("EntityFields"))
        {
            const uint16_t originalDecorationListId = entity.entity.decorationListId;
            const bool decorationChanged = renderDecorationSelector(
                session,
                "Decoration",
                entity.entity.decorationListId,
                false);
            changed = decorationChanged || changed;

            if (decorationChanged)
            {
                if (const Game::DecorationEntry *pDecoration = session.decorationTable().get(entity.entity.decorationListId))
                {
                    entity.entity.name = pDecoration->internalName;
                }
                else if (entity.entity.decorationListId != originalDecorationListId)
                {
                    entity.entity.name.clear();
                }
            }

            renderInspectorReadOnlyField("Entity Index", std::to_string(entity.entityIndex));
            changed = editStringField(session, "Name", entity.entity.name, 128) || changed;
            renderInspectorReadOnlyField("Decoration List Id", std::to_string(entity.entity.decorationListId));
            renderInspectorReadOnlyField(
                "Resolved Hint",
                [&session, &entity]()
                {
                    const Game::DecorationEntry *pDecoration = session.decorationTable().get(entity.entity.decorationListId);
                    return pDecoration != nullptr && !pDecoration->hint.empty() ? pDecoration->hint : std::string("<none>");
                }());
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Placement"))
    {
        if (beginInspectorPropertyTable("EntityPlacementFields"))
        {
            changed = editPositionField(session, "Position", entity.entity.x, entity.entity.y, entity.entity.z) || changed;
            changed = editIntField(
                session,
                "Facing",
                entity.entity.facing,
                std::numeric_limits<int>::min(),
                std::numeric_limits<int>::max()) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Behavior"))
    {
        if (beginInspectorPropertyTable("EntityBehaviorFields"))
        {
            changed = editUInt16Field(session, "AI Attributes", entity.entity.aiAttributes) || changed;
            changed = editUInt16Field(session, "Variable Primary", entity.entity.variablePrimary) || changed;
            changed = editUInt16Field(session, "Variable Secondary", entity.entity.variableSecondary) || changed;
            changed = editUInt16Field(session, "Special Trigger", entity.entity.specialTrigger) || changed;
            changed = editUInt16Field(session, "Initial Decoration Flag", entity.initialDecorationFlag) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Events"))
    {
        if (beginInspectorPropertyTable("EntityEventFields"))
        {
            changed = editMapEventField(session, "Event Primary", entity.entity.eventIdPrimary) || changed;
            renderResolvedMapEventField(session, "Primary Event Label", entity.entity.eventIdPrimary);
            changed = editMapEventField(session, "Event Secondary", entity.entity.eventIdSecondary) || changed;
            renderResolvedMapEventField(session, "Secondary Event Label", entity.entity.eventIdSecondary);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (changed)
    {
        session.setPendingEntityDecorationListId(entity.entity.decorationListId);
        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderEntityPlacementInspector(EditorSession &session) const
{
    uint32_t selectedId = session.pendingEntityDecorationListId();

    ImGui::TextUnformatted("Entity Placement");
    ImGui::Separator();
    ImGui::TextWrapped("Choose a decoration, then click in the viewport to place the entity. The entity preview "
                       "follows the cursor while placement mode is active.");

    renderInspectorSectionHeader("Decoration");

    if (beginInspectorPropertyTable("EntityPlacementSelection"))
    {
        uint16_t pendingDecorationId = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));

        if (renderDecorationSelector(session, "Decoration", pendingDecorationId, true))
        {
            selectedId = pendingDecorationId;
            session.setPendingEntityDecorationListId(pendingDecorationId);
        }

        renderInspectorReadOnlyField("Pending Decoration Id", std::to_string(selectedId));

        const Game::DecorationEntry *pDecoration =
            session.decorationTable().get(static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535)));
        renderInspectorReadOnlyField("Sprite Id", pDecoration != nullptr ? std::to_string(pDecoration->spriteId) : "0");
        renderInspectorReadOnlyField(
            "Internal Name",
            pDecoration != nullptr && !pDecoration->internalName.empty() ? pDecoration->internalName : "(none)");
        renderInspectorReadOnlyField(
            "Hint",
            pDecoration != nullptr && !pDecoration->hint.empty() ? pDecoration->hint : "(none)");
        ImGui::EndTable();
    }
}

void EditorMainWindow::renderSpawnPlacementInspector(EditorSession &session) const
{
    Game::OutdoorSpawn &spawn = session.mutablePendingSpawn();
    const Game::MapStatsEntry *pMapEntry = session.currentMapStatsEntry();
    const Game::SpawnPreview preview = pMapEntry != nullptr
        ? Game::SpawnPreviewResolver::describe(
            *pMapEntry,
            &session.monsterTable(),
            spawn.typeId,
            spawn.index,
            spawn.attributes,
            spawn.group)
        : Game::SpawnPreview {};

    ImGui::TextUnformatted("Spawn Placement");
    ImGui::Separator();
    ImGui::TextWrapped("Configure the spawn defaults, then click in the viewport to place it. The full placed spawn "
                       "can still be edited afterward.");

    if (pMapEntry == nullptr)
    {
        ImGui::Spacing();
        ImGui::PushStyleColor(ImGuiCol_Text, colorFromRgb(0xD8B277));
        ImGui::TextUnformatted("Map stats entry is unavailable. Encounter labels may be incomplete.");
        ImGui::PopStyleColor();
    }

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("SpawnPlacementOverview"))
        {
            editTransientSpawnTypeField(spawn);

            if (spawn.typeId == 3 && pMapEntry != nullptr)
            {
                editTransientActorSpawnEncounterField(*pMapEntry, spawn);
            }
            else if (spawn.typeId == 2)
            {
                renderObjectSelector(session, "Object Description", spawn.index, true);
            }
            else
            {
                editTransientUInt16Field("Index", spawn.index);
            }

            renderInspectorReadOnlyField("Type Label", preview.typeName.empty() ? "<unknown>" : preview.typeName);
            renderInspectorReadOnlyField("Summary", preview.summary.empty() ? "<unresolved>" : preview.summary);
            renderInspectorReadOnlyField("Detail", preview.detail.empty() ? "<none>" : preview.detail);
            const Game::ObjectEntry *pObjectEntry = spawn.typeId == 2 ? session.objectTable().get(spawn.index) : nullptr;
            renderInspectorReadOnlyField(
                "Object Label",
                pObjectEntry != nullptr && !pObjectEntry->internalName.empty() ? pObjectEntry->internalName : "<none>");
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Defaults"))
    {
        if (beginInspectorPropertyTable("SpawnPlacementDefaults"))
        {
            editTransientUInt16Field("Radius", spawn.radius);
            editTransientUInt32Field("Group", spawn.group);
            editTransientUInt16Field("Attributes", spawn.attributes);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }
}

void EditorMainWindow::renderSpawnInspector(EditorSession &session, size_t spawnIndex) const
{
    std::vector<Game::OutdoorSceneSpawn> &spawns = session.document().mutableOutdoorSceneData().spawns;

    if (spawnIndex >= spawns.size())
    {
        ImGui::TextUnformatted("Selected spawn index is out of range.");
        return;
    }

    Game::OutdoorSceneSpawn &spawn = spawns[spawnIndex];
    const Game::MapStatsEntry *pMapEntry = session.currentMapStatsEntry();
    const Game::SpawnPreview preview = pMapEntry != nullptr
        ? Game::SpawnPreviewResolver::describe(
            *pMapEntry,
            &session.monsterTable(),
            spawn.spawn.typeId,
            spawn.spawn.index,
            spawn.spawn.attributes,
            spawn.spawn.group)
        : Game::SpawnPreview {};
    bool changed = false;

    if (pMapEntry == nullptr)
    {
        ImGui::TextUnformatted("Map stats entry is unavailable. Spawn semantics may be incomplete.");
    }

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("SpawnIdentityFields"))
        {
            renderInspectorReadOnlyField("Spawn Index", std::to_string(spawn.spawnIndex));
            changed = editSpawnTypeField(session, spawn.spawn) || changed;

            if (spawn.spawn.typeId == 3 && pMapEntry != nullptr)
            {
                changed = editActorSpawnEncounterField(session, *pMapEntry, spawn.spawn) || changed;
            }
            else if (spawn.spawn.typeId == 2)
            {
                changed = renderObjectSelector(session, "Object Description", spawn.spawn.index, false) || changed;
            }
            else
            {
                changed = editUInt16Field(session, "Index", spawn.spawn.index) || changed;
            }

            renderInspectorReadOnlyField("Type Label", preview.typeName.empty() ? "<unknown>" : preview.typeName);
            renderInspectorReadOnlyField("Summary", preview.summary.empty() ? "<unresolved>" : preview.summary);
            renderInspectorReadOnlyField("Detail", preview.detail.empty() ? "<none>" : preview.detail);
            const Game::ObjectEntry *pObjectEntry =
                spawn.spawn.typeId == 2 ? session.objectTable().get(spawn.spawn.index) : nullptr;
            renderInspectorReadOnlyField(
                "Object Label",
                pObjectEntry != nullptr && !pObjectEntry->internalName.empty() ? pObjectEntry->internalName : "<none>");
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Placement"))
    {
        if (beginInspectorPropertyTable("SpawnPlacementFields"))
        {
            changed = editPositionField(session, "Position", spawn.spawn.x, spawn.spawn.y, spawn.spawn.z) || changed;
            changed = editUInt16Field(session, "Radius", spawn.spawn.radius) || changed;
            changed = editUInt32Field(session, "Group", spawn.spawn.group) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Behavior"))
    {
        if (beginInspectorPropertyTable("SpawnBehaviorFields"))
        {
            changed = editUInt16Field(session, "Attributes", spawn.spawn.attributes) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Overrides And Legacy", false))
    {
        if (beginInspectorPropertyTable("SpawnLegacyFields"))
        {
            changed = editUInt16Field(session, "Type Id Raw", spawn.spawn.typeId) || changed;
            changed = editUInt16Field(session, "Index Raw", spawn.spawn.index) || changed;
            renderInspectorReadOnlyField("Resolved Type", preview.typeName.empty() ? "<unknown>" : preview.typeName);
            renderInspectorReadOnlyField("Resolved Summary", preview.summary.empty() ? "<unresolved>" : preview.summary);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (changed)
    {
        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderActorPlacementInspector(EditorSession &session) const
{
    Game::MapDeltaActor &actor = session.mutablePendingActor();
    const Game::MonsterTable &monsterTable = session.monsterTable();
    const std::string displayLabel = actorDisplayLabel(&monsterTable, actor, 0);
    const std::string templateLabel = actorMonsterTemplateLabel(&monsterTable, actor);
    const std::string npcIdLabel = actor.npcId == 0 ? "<none>" : std::to_string(actor.npcId);

    ImGui::TextUnformatted("Actor Placement");
    ImGui::Separator();
    ImGui::TextWrapped("Configure the actor defaults, then click in the viewport to place it. The full placed actor "
                       "can still be edited afterward.");

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("ActorPlacementOverview"))
        {
            renderMonsterTemplateSelector(session, "Monster Template", actor, true);
            editTransientInt16Field("NPC Id", actor.npcId);
            editTransientIntField(
                "Unique Name Index",
                actor.uniqueNameIndex,
                std::numeric_limits<int32_t>::min(),
                std::numeric_limits<int32_t>::max());
            editTransientStringField("Raw Name Override", actor.name, 128);
            renderInspectorReadOnlyField("Resolved Name", displayLabel);
            renderInspectorReadOnlyField("Template", templateLabel.empty() ? "<unresolved>" : templateLabel);
            renderInspectorReadOnlyField("Monster Info Id", std::to_string(actor.monsterInfoId));
            renderInspectorReadOnlyField("Monster Id", std::to_string(actor.monsterId));
            renderInspectorReadOnlyField("NPC Link", npcIdLabel);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Defaults"))
    {
        if (beginInspectorPropertyTable("ActorPlacementDefaults"))
        {
            int hostilityType = actor.hostilityType;

            if (editTransientIntField("Hostility Type", hostilityType, 0, 255))
            {
                actor.hostilityType = static_cast<uint8_t>(hostilityType);
            }

            editTransientUInt16Field("Radius", actor.radius);
            editTransientUInt16Field("Height", actor.height);
            editTransientUInt16Field("Move Speed", actor.moveSpeed);
            editTransientUInt32Field("Group", actor.group);
            editTransientUInt32Field("Ally", actor.ally);
            renderInspectorReadOnlyField("Hostility Label", hostilityTypeLabel(actor.hostilityType));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }
}

void EditorMainWindow::renderActorInspector(EditorSession &session, size_t actorIndex) const
{
    std::vector<Game::MapDeltaActor> &actors = session.document().mutableOutdoorSceneData().initialState.actors;

    if (actorIndex >= actors.size())
    {
        ImGui::TextUnformatted("Selected actor index is out of range.");
        return;
    }

    Game::MapDeltaActor &actor = actors[actorIndex];
    const Game::MonsterTable &monsterTable = session.monsterTable();
    const std::string displayLabel = actorDisplayLabel(&monsterTable, actor, actorIndex);
    const std::string templateLabel = actorMonsterTemplateLabel(&monsterTable, actor);
    const std::string npcIdLabel = actor.npcId == 0 ? "<none>" : std::to_string(actor.npcId);
    bool changed = false;

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("ActorIdentityFields"))
        {
            changed = renderMonsterTemplateSelector(session, "Monster Template", actor, false) || changed;
            changed = editInt16Field(session, "NPC Id", actor.npcId) || changed;
            changed = editIntField(
                session,
                "Unique Name Index",
                actor.uniqueNameIndex,
                std::numeric_limits<int32_t>::min(),
                std::numeric_limits<int32_t>::max()) || changed;
            changed = editStringField(session, "Raw Name Override", actor.name, 128) || changed;
            renderInspectorReadOnlyField("Resolved Name", displayLabel);
            renderInspectorReadOnlyField("Template", templateLabel.empty() ? "<unresolved>" : templateLabel.c_str());
            renderInspectorReadOnlyField("Monster Info Id", std::to_string(actor.monsterInfoId));
            renderInspectorReadOnlyField("Monster Id", std::to_string(actor.monsterId));
            renderInspectorReadOnlyField("NPC Link", npcIdLabel);
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Placement"))
    {
        if (beginInspectorPropertyTable("ActorPlacementFields"))
        {
            changed = editPositionField(session, "Position", actor.x, actor.y, actor.z) || changed;
            changed = editUInt16Field(session, "Radius", actor.radius) || changed;
            changed = editUInt16Field(session, "Height", actor.height) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Behavior"))
    {
        if (beginInspectorPropertyTable("ActorBehaviorFields"))
        {
            changed = editActorHostilityTypeField(session, actor.hostilityType) || changed;
            changed = editUInt32Field(session, "Group", actor.group) || changed;
            changed = editUInt32Field(session, "Ally", actor.ally) || changed;
            renderInspectorReadOnlyField("Hostility Label", hostilityTypeLabel(actor.hostilityType));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Visibility And Faction"))
    {
        if (beginInspectorPropertyTable("ActorFlags"))
        {
            changed = editBitCheckbox(session, "Show On Map", actor.attributes, MonsterBitShowOnMap) || changed;
            changed = editBitCheckbox(session, "Invisible", actor.attributes, MonsterBitInvisible) || changed;
            changed = editBitCheckbox(session, "No Flee", actor.attributes, MonsterBitNoFlee) || changed;
            changed = editBitCheckbox(session, "Hostile", actor.attributes, MonsterBitHostile) || changed;
            changed = editBitCheckbox(session, "On Alert Map", actor.attributes, MonsterBitOnAlertMap) || changed;
            changed = editBitCheckbox(session, "Treasure Generated", actor.attributes, MonsterBitTreasureGenerated)
                || changed;
            changed = editBitCheckbox(session, "Show As Hostile", actor.attributes, MonsterBitShowAsHostile)
                || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Overrides And Legacy", false))
    {
        if (beginInspectorPropertyTable("ActorLegacyFields"))
        {
            changed = editInt16Field(session, "Monster Info Id Raw", actor.monsterInfoId) || changed;
            changed = editInt16Field(session, "Monster Id Raw", actor.monsterId) || changed;
            changed = editInt16Field(session, "HP Override", actor.hp) || changed;
            changed = editUInt16Field(session, "Move Speed Override", actor.moveSpeed) || changed;
            changed = editUInt16Array4Field(session, "Sprite Id Overrides", actor.spriteIds) || changed;
            changed = editInt16Field(session, "Sector Id", actor.sectorId) || changed;
            changed = editUInt16Field(session, "Current Animation", actor.currentActionAnimation) || changed;
            changed = editUInt32Field(session, "Attributes Raw", actor.attributes) || changed;
            renderInspectorReadOnlyField("Display Label", displayLabel);
            renderInspectorReadOnlyField("NPC Link", npcIdLabel);
            renderInspectorReadOnlyField("Hostility Label", hostilityTypeLabel(actor.hostilityType));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (changed)
    {
        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderSpriteObjectPlacementInspector(EditorSession &session) const
{
    uint32_t selectedId = session.pendingSpriteObjectDescriptionId();

    ImGui::TextUnformatted("Decoration Placement");
    ImGui::Separator();
    ImGui::TextWrapped("Choose a decoration, then click in the viewport to place it. The sprite preview follows "
                       "the cursor while placement mode is active.");

    renderInspectorSectionHeader("Decoration");

    if (beginInspectorPropertyTable("SpriteObjectPlacementSelection"))
    {
        uint16_t pendingObjectDescriptionId = static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535));

        if (renderObjectSelector(session, "Object Description", pendingObjectDescriptionId, true))
        {
            selectedId = pendingObjectDescriptionId;
            session.setPendingSpriteObjectDescriptionId(pendingObjectDescriptionId);
        }

        renderInspectorReadOnlyField("Pending Object Description Id", std::to_string(selectedId));

        const Game::ObjectEntry *pObjectEntry =
            session.objectTable().get(static_cast<uint16_t>(std::min<uint32_t>(selectedId, 65535)));
        renderInspectorReadOnlyField("Sprite Id", pObjectEntry != nullptr ? std::to_string(pObjectEntry->spriteId) : "0");
        renderInspectorReadOnlyField(
            "Sprite Name",
            pObjectEntry != nullptr && !pObjectEntry->spriteName.empty() ? pObjectEntry->spriteName : "(none)");
        renderInspectorReadOnlyField(
            "Flags",
            pObjectEntry != nullptr ? std::to_string(pObjectEntry->flags) : "0");
        ImGui::EndTable();
    }
}

void EditorMainWindow::renderSpriteObjectInspector(EditorSession &session, size_t spriteObjectIndex) const
{
    std::vector<Game::MapDeltaSpriteObject> &spriteObjects =
        session.document().mutableOutdoorSceneData().initialState.spriteObjects;

    if (spriteObjectIndex >= spriteObjects.size())
    {
        ImGui::TextUnformatted("Selected sprite object index is out of range.");
        return;
    }

    Game::MapDeltaSpriteObject &spriteObject = spriteObjects[spriteObjectIndex];
    bool changed = false;

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("SpriteObjectIdentityFields"))
        {
            const uint16_t originalObjectDescriptionId = spriteObject.objectDescriptionId;
            const bool objectDescriptionChanged = renderObjectSelector(
                session,
                "Object Description",
                spriteObject.objectDescriptionId,
                false);
            changed = objectDescriptionChanged || changed;

            if (objectDescriptionChanged)
            {
                if (const Game::ObjectEntry *pObjectEntry = session.objectTable().get(spriteObject.objectDescriptionId))
                {
                    spriteObject.spriteId = pObjectEntry->spriteId;

                    if (spriteObject.temporaryLifetime == 0 && pObjectEntry->lifetimeTicks > 0)
                    {
                        spriteObject.temporaryLifetime = pObjectEntry->lifetimeTicks;
                    }
                }
                else if (spriteObject.objectDescriptionId != originalObjectDescriptionId)
                {
                    spriteObject.spriteId = 0;
                }
            }

            renderInspectorReadOnlyField(
                "Display Name",
                spriteObjectDisplayLabel(spriteObject, spriteObjectIndex));
            changed = editUInt16Field(session, "Yaw Angle", spriteObject.yawAngle) || changed;
            changed = editUInt16Field(session, "Sound Id", spriteObject.soundId) || changed;
            renderInspectorReadOnlyField("Object Description Id", std::to_string(spriteObject.objectDescriptionId));
            renderInspectorReadOnlyField("Sprite Id", std::to_string(spriteObject.spriteId));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Placement"))
    {
        if (beginInspectorPropertyTable("SpriteObjectPlacementFields"))
        {
            changed = editPositionField(session, "Position", spriteObject.x, spriteObject.y, spriteObject.z) || changed;
            changed = editPositionField(
                session,
                "Initial Position",
                spriteObject.initialX,
                spriteObject.initialY,
                spriteObject.initialZ) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Motion And Lifetime"))
    {
        if (beginInspectorPropertyTable("SpriteObjectMotionFields"))
        {
            changed = editInt16PositionField(
                session,
                "Velocity",
                spriteObject.velocityX,
                spriteObject.velocityY,
                spriteObject.velocityZ) || changed;
            changed = editUInt16Field(session, "Time Since Created", spriteObject.timeSinceCreated) || changed;
            changed = editInt16Field(session, "Temporary Lifetime", spriteObject.temporaryLifetime) || changed;
            changed = editInt16Field(session, "Glow Radius Multiplier", spriteObject.glowRadiusMultiplier) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Visibility And Object Flags"))
    {
        if (beginInspectorPropertyTable("SpriteObjectFlags"))
        {
            changed = editBitCheckbox(session, "Visible", spriteObject.attributes, ObjectBitVisible) || changed;
            changed = editBitCheckbox(session, "Temporary", spriteObject.attributes, ObjectBitTemporary) || changed;
            changed = editBitCheckbox(session, "Halt Turn-Based", spriteObject.attributes, ObjectBitHaltTurnBased)
                || changed;
            changed = editBitCheckbox(session, "Dropped By Player", spriteObject.attributes, ObjectBitDroppedByPlayer)
                || changed;
            changed = editBitCheckbox(session, "Ignore Range", spriteObject.attributes, ObjectBitIgnoreRange)
                || changed;
            changed = editBitCheckbox(session, "No Z-Buffer", spriteObject.attributes, ObjectBitNoZBuffer)
                || changed;
            changed = editBitCheckbox(session, "Skip A Frame", spriteObject.attributes, ObjectBitSkipAFrame)
                || changed;
            changed = editBitCheckbox(session, "Attach To Head", spriteObject.attributes, ObjectBitAttachToHead)
                || changed;
            changed = editBitCheckbox(session, "Missile", spriteObject.attributes, ObjectBitMissile) || changed;
            changed = editBitCheckbox(session, "Removed", spriteObject.attributes, ObjectBitRemoved) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Spell And Ownership"))
    {
        if (beginInspectorPropertyTable("SpriteObjectPayloadFields"))
        {
            changed = editIntField(
                session,
                "Spell Id",
                spriteObject.spellId,
                std::numeric_limits<int32_t>::min(),
                std::numeric_limits<int32_t>::max()) || changed;
            changed = editIntField(
                session,
                "Spell Level",
                spriteObject.spellLevel,
                std::numeric_limits<int32_t>::min(),
                std::numeric_limits<int32_t>::max()) || changed;
            changed = editIntField(
                session,
                "Spell Skill",
                spriteObject.spellSkill,
                std::numeric_limits<int32_t>::min(),
                std::numeric_limits<int32_t>::max()) || changed;
            changed = editIntField(
                session,
                "Field54",
                spriteObject.field54,
                std::numeric_limits<int32_t>::min(),
                std::numeric_limits<int32_t>::max()) || changed;
            changed = editIntField(
                session,
                "Spell Caster PID",
                spriteObject.spellCasterPid,
                std::numeric_limits<int32_t>::min(),
                std::numeric_limits<int32_t>::max()) || changed;
            changed = editIntField(
                session,
                "Spell Target PID",
                spriteObject.spellTargetPid,
                std::numeric_limits<int32_t>::min(),
                std::numeric_limits<int32_t>::max()) || changed;
            renderInspectorReadOnlyField("Lod Distance", std::to_string(static_cast<int>(spriteObject.lodDistance)));
            renderInspectorReadOnlyField(
                "Spell Caster Ability",
                std::to_string(static_cast<int>(spriteObject.spellCasterAbility)));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Overrides And Legacy", false))
    {
        if (beginInspectorPropertyTable("SpriteObjectLegacyPayload"))
        {
            changed = editUInt16Field(session, "Object Description Id Raw", spriteObject.objectDescriptionId) || changed;
            changed = editUInt16Field(session, "Sprite Id Raw", spriteObject.spriteId) || changed;
            changed = editInt16Field(session, "Sector Id", spriteObject.sectorId) || changed;
            changed = editUInt16Field(session, "Attributes Raw", spriteObject.attributes) || changed;
            renderInspectorReadOnlyField("Containing Item Bytes", std::to_string(spriteObject.rawContainingItem.size()));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (changed)
    {
        session.setPendingSpriteObjectDescriptionId(spriteObject.objectDescriptionId);
        session.noteDocumentMutated({});
    }
}

void EditorMainWindow::renderChestInspector(EditorSession &session, size_t chestIndex) const
{
    std::vector<Game::MapDeltaChest> &chests =
        session.document().mutableOutdoorSceneData().initialState.chests;

    if (chestIndex >= chests.size())
    {
        ImGui::TextUnformatted("Selected chest index is out of range.");
        return;
    }

    Game::MapDeltaChest &chest = chests[chestIndex];
    const Game::ChestEntry *pChestEntry = session.chestTable().get(chest.chestTypeId);
    size_t occupiedSlots = 0;
    bool changed = false;

    for (int16_t itemIndex : chest.inventoryMatrix)
    {
        if (itemIndex > 0)
        {
            ++occupiedSlots;
        }
    }

    if (beginInspectorSectionBlock("Overview"))
    {
        if (beginInspectorPropertyTable("ChestIdentity"))
        {
            changed = editChestPictureField(session, chest.chestTypeId) || changed;
            renderInspectorReadOnlyField(
                "Chest Type Name",
                pChestEntry != nullptr && !pChestEntry->name.empty() ? pChestEntry->name : "<unknown>");
            renderInspectorReadOnlyField("Chest Type Id", std::to_string(chest.chestTypeId));
            renderInspectorReadOnlyField("Occupied Inventory Slots", std::to_string(occupiedSlots));
            renderInspectorReadOnlyField("Inventory Cells", std::to_string(chest.inventoryMatrix.size()));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Flags"))
    {
        if (beginInspectorPropertyTable("ChestFlags"))
        {
            changed = editBitCheckbox(session, "Trapped", chest.flags, ChestBitTrapped) || changed;
            changed = editBitCheckbox(session, "Items Placed", chest.flags, ChestBitItemsPlaced) || changed;
            changed = editBitCheckbox(session, "Identified", chest.flags, ChestBitIdentified) || changed;
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Contents", false))
    {
        const std::vector<EditorChestContentRecord> contentRecords = session.decodeChestContents(chestIndex);
        size_t fixedRecordCount = 0;
        size_t randomRecordCount = 0;

        for (const EditorChestContentRecord &record : contentRecords)
        {
            if (record.rawItemId > 0)
            {
                ++fixedRecordCount;
            }
            else if (record.rawItemId < 0)
            {
                ++randomRecordCount;
            }
        }

        ImGui::Text("Decoded Records: %zu", contentRecords.size());
        ImGui::Text("Fixed: %zu", fixedRecordCount);
        ImGui::SameLine();
        ImGui::Text("Random: %zu", randomRecordCount);

        if (ImGui::Button("Add Fixed Item"))
        {
            const std::optional<size_t> recordIndex = findFirstEmptyChestRecord(chest);

            if (recordIndex)
            {
                session.captureUndoSnapshot();
                clearChestRecord(chest, *recordIndex);
                writeChestRecordId(chest, *recordIndex, 1);
                changed = true;
            }
            else
            {
                session.logError("Chest has no free item records.");
            }
        }

        ImGui::SameLine();

        if (ImGui::BeginCombo("Add Random Treasure", "Select Level"))
        {
            for (int treasureLevel = 1; treasureLevel <= 7; ++treasureLevel)
            {
                const std::string levelLabel = "Level " + std::to_string(treasureLevel);

                if (ImGui::Selectable(levelLabel.c_str()))
                {
                    const std::optional<size_t> recordIndex = findFirstEmptyChestRecord(chest);

                    if (recordIndex)
                    {
                        session.captureUndoSnapshot();
                        clearChestRecord(chest, *recordIndex);
                        writeChestRecordId(chest, *recordIndex, -treasureLevel);
                        changed = true;
                    }
                    else
                    {
                        session.logError("Chest has no free item records.");
                    }
                }
            }

            ImGui::EndCombo();
        }

        if (contentRecords.empty())
        {
            ImGui::TextUnformatted("No non-empty chest records.");
        }
        else
        {
            for (const EditorChestContentRecord &record : contentRecords)
            {
                ImGui::PushID(static_cast<int>(record.recordIndex));
                const std::string headerLabel =
                    "Record " + std::to_string(record.recordIndex) + " - " + record.summary;

                if (ImGui::TreeNodeEx(headerLabel.c_str(), ImGuiTreeNodeFlags_DefaultOpen))
                {
                    int recordMode = 2;

                    if (record.rawItemId > 0)
                    {
                        recordMode = 0;
                    }
                    else if (record.rawItemId >= -7)
                    {
                        recordMode = 1;
                    }

                    if (beginInspectorPropertyTable("ChestRecordEditor"))
                    {
                        renderInspectorReadOnlyField("Anchor", record.anchor);

                        beginInspectorFieldRow("Mode");
                        static const char *Modes[] = {"Fixed Item", "Random Treasure", "Legacy Raw"};

                        if (ImGui::Combo("##ChestRecordMode", &recordMode, Modes, IM_ARRAYSIZE(Modes)))
                        {
                            session.captureUndoSnapshot();

                            if (recordMode == 0)
                            {
                                writeChestRecordId(chest, record.recordIndex, 1);
                            }
                            else if (recordMode == 1)
                            {
                                writeChestRecordId(chest, record.recordIndex, -1);
                            }

                            changed = true;
                        }

                        int rawValue = record.rawItemId;

                        if (recordMode == 0)
                        {
                            changed = editFixedItemSelectorField(session, "Item", rawValue) || changed;

                            if (rawValue != record.rawItemId)
                            {
                                writeChestRecordId(chest, record.recordIndex, rawValue);
                            }

                            renderInspectorReadOnlyField("Item Id", std::to_string(rawValue));
                            renderInspectorReadOnlyField("Item Name", session.itemDisplayName(rawValue));
                        }
                        else if (recordMode == 1)
                        {
                            int treasureLevel = std::clamp(-record.rawItemId, 1, 7);
                            beginInspectorFieldRow("Treasure Level");

                            if (ImGui::SliderInt("##ChestRandomLevel", &treasureLevel, 1, 7))
                            {
                                session.captureUndoSnapshot();
                                writeChestRecordId(chest, record.recordIndex, -treasureLevel);
                                changed = true;
                            }
                        }
                        else
                        {
                            beginInspectorFieldRow("Raw Item Id");

                            if (ImGui::InputInt("##ChestLegacyRawId", &rawValue))
                            {
                                if (rawValue != record.rawItemId)
                                {
                                    session.captureUndoSnapshot();
                                    writeChestRecordId(chest, record.recordIndex, rawValue);
                                    changed = true;
                                }
                            }
                        }

                        ImGui::EndTable();
                    }

                    if (ImGui::Button("Clear Record"))
                    {
                        session.captureUndoSnapshot();
                        clearChestRecord(chest, record.recordIndex);
                        changed = true;
                    }

                    ImGui::TreePop();
                }

                ImGui::PopID();
            }
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Linked Openers", false))
    {
        const std::vector<EditorChestLink> chestLinks = session.findChestLinks(chestIndex);

        if (chestLinks.empty())
        {
            ImGui::TextUnformatted("No linked entity or face opener found.");
        }
        else
        {
            for (const EditorChestLink &link : chestLinks)
            {
                if (link.kind == EditorChestLink::Kind::Entity)
                {
                    std::string buttonLabel = "Select Entity " + std::to_string(link.entityIndex)
                        + "##ChestLinkEntity" + std::to_string(chestIndex) + "_" + std::to_string(link.entityIndex);

                    if (ImGui::Button(buttonLabel.c_str()))
                    {
                        session.select(EditorSelectionKind::Entity, link.entityIndex);
                    }

                    ImGui::SameLine();
                    ImGui::Text("event %u", link.eventId);
                }
                else
                {
                    const size_t flatIndex = flattenedOutdoorFaceIndex(
                        session.document().outdoorGeometry(),
                        link.bmodelIndex,
                        link.faceIndex);
                    std::string buttonLabel = "Select Face "
                        + std::to_string(link.bmodelIndex)
                        + ":"
                        + std::to_string(link.faceIndex)
                        + "##ChestLinkFace"
                        + std::to_string(chestIndex)
                        + "_"
                        + std::to_string(link.bmodelIndex)
                        + "_"
                        + std::to_string(link.faceIndex);

                    if (ImGui::Button(buttonLabel.c_str()))
                    {
                        session.select(EditorSelectionKind::InteractiveFace, flatIndex);
                    }

                    ImGui::SameLine();
                    ImGui::Text("event %u", link.eventId);
                }
            }
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Layout And Matrix", false))
    {
        if (ImGui::BeginTable("ChestInventoryMatrix", 14, ImGuiTableFlags_Borders | ImGuiTableFlags_SizingFixedFit))
        {
            for (size_t slotIndex = 0; slotIndex < chest.inventoryMatrix.size(); ++slotIndex)
            {
                if ((slotIndex % 14) == 0)
                {
                    ImGui::TableNextRow();
                }

                ImGui::TableSetColumnIndex(static_cast<int>(slotIndex % 14));
                ImGui::Text("%d", chest.inventoryMatrix[slotIndex]);
            }

            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (beginInspectorSectionBlock("Overrides And Legacy", false))
    {
        if (beginInspectorPropertyTable("ChestLegacyFields"))
        {
            changed = editUInt16Field(session, "Chest Type Id Raw", chest.chestTypeId) || changed;
            changed = editUInt16Field(session, "Flags Raw", chest.flags) || changed;
            renderInspectorReadOnlyField("Raw Item Bytes", std::to_string(chest.rawItems.size()));
            renderInspectorReadOnlyField("Raw Record Count", std::to_string(chest.rawItems.size() / 36));
            ImGui::EndTable();
        }
        endInspectorSectionBlock();
    }

    if (changed)
    {
        session.noteDocumentMutated({});
    }
}
}
