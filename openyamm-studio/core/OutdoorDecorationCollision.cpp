#include "core/OutdoorDecorationCollision.h"

#include "core/OutdoorModel.h"
#include "game/FaceEnums.h"

#include <cgltf/cgltf.h>
#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <map>
#include <memory>
#include <numbers>
#include <optional>
#include <regex>

namespace OpenYAMM::Studio
{
namespace
{
// The texture the hidden faces carry (never drawn): a stone every world mounts.
constexpr const char *CollisionTexture = "cwb1";

using CollisionBinding = DecorationCollisionModels::Binding;
using CollisionShape = DecorationCollisionModels::Shape;

std::string lowercase(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return text;
}

// The game's placement randomness (DecorationModelSet.cpp placementRandom): the same number for the same spot.
double placementRandom(int x, int y, uint32_t salt)
{
    uint32_t hash = uint32_t(x) * 0x9e3779b1u ^ uint32_t(y) * 0x85ebca77u ^ salt * 0xc2b2ae3du;
    hash ^= hash >> 15;
    hash *= 0x2c1b3c6du;
    hash ^= hash >> 12;
    hash *= 0x297a2d39u;
    hash ^= hash >> 15;
    return double(hash & 0xffffffu) / double(0x1000000u);
}

// The bindings that ask for collision, by decoration name: the engine's, each replaced by the world's of that name (a
// world entry without `collision` or with `model: null` takes the engine's away).
std::map<std::string, CollisionBinding> collisionBindings(const std::filesystem::path &assetRoot,
    const std::string &world, const std::string &mapStem, bool indoors)
{
    std::map<std::string, CollisionBinding> bindings;
    const std::string manifest = indoors ? "indoor_decorations.yml" : "decorations.yml";

    for (const std::filesystem::path &path : {assetRoot / "engine" / "models" / manifest,
             assetRoot / "worlds" / world / "models" / manifest})
    {
        std::error_code error;

        if (!std::filesystem::exists(path, error))
        {
            continue;
        }

        YAML::Node root;

        try
        {
            root = YAML::LoadFile(path.string());
        }
        catch (const YAML::Exception &)
        {
            continue;
        }

        const YAML::Node entries = root["decorations"];
        std::map<std::string, bool> seen;

        for (size_t index = 0; entries && entries.IsSequence() && index < entries.size(); ++index)
        {
            const YAML::Node entry = entries[index];

            if (!entry.IsMap() || !entry["name"])
            {
                continue;
            }

            const YAML::Node maps = entry["maps"];

            if (maps && maps.IsSequence())
            {
                bool listed = false;

                for (const YAML::Node &map : maps)
                {
                    const std::string name = lowercase(map.as<std::string>(""));
                    listed = listed || name == lowercase(mapStem) || name == lowercase(mapStem + (indoors ? ".blv" : ".odm"));
                }

                if (!listed)
                {
                    continue;
                }
            }

            const std::string name = lowercase(entry["name"].as<std::string>(""));

            // A world's entry for a name replaces every entry of that name before it (the engine's).
            if (!seen[name])
            {
                bindings.erase(name);
                seen[name] = true;
            }

            if (!entry["model"] || entry["model"].IsNull() || entry["collision"].as<std::string>("") != "model"
                || entry["mount"].as<std::string>("ground") != "ground")
            {
                continue;
            }

            CollisionBinding binding;
            binding.model = entry["model"].as<std::string>("");
            binding.collisionModel = entry["collision_model"].as<std::string>("");
            binding.scatter = entry["collision_scatter"].as<bool>(false);
            binding.height = entry["height"].as<double>(0.0);
            binding.heightJitter = entry["height_jitter"].as<double>(0.0);
            binding.randomYaw = entry["yaw"].as<std::string>("random") == "random";
            binding.yawOffset = entry["yaw_offset"].as<double>(0.0);
            binding.zOffset = entry["z_offset"].as<double>(0.0);

            if (!binding.model.empty() && binding.height > 0.0)
            {
                bindings[name] = binding;
            }
        }
    }

    return bindings;
}

// The last mesh of a mesh's `openyamm_lods` chain (the engine's LOD metadata in its extras), or the mesh itself.
const cgltf_mesh *coarsestLodOf(const cgltf_data &data, const cgltf_mesh &mesh)
{
    cgltf_size size = 0;
    cgltf_copy_extras_json(&data, &mesh.extras, nullptr, &size);

    if (size <= 1)
    {
        return &mesh;
    }

    std::string json(size, '\0');

    if (cgltf_copy_extras_json(&data, &mesh.extras, json.data(), &size) != cgltf_result_success)
    {
        return &mesh;
    }

    try
    {
        const YAML::Node lods = YAML::Load(json.c_str())["openyamm_lods"];

        if (lods && lods.IsSequence() && lods.size() > 0)
        {
            const size_t index = lods[lods.size() - 1].as<size_t>();

            if (index < data.meshes_count)
            {
                return &data.meshes[index];
            }
        }
    }
    catch (const YAML::Exception &)
    {
    }

    return &mesh;
}

// `coarsestLod`: each node's mesh is replaced by the coarsest of its LODs (a model without LODs keeps its mesh).
std::optional<CollisionShape> readCollisionShape(const std::filesystem::path &glbPath, bool boundsOnly = false,
    bool coarsestLod = false)
{
    cgltf_options options = {};
    cgltf_data *pData = nullptr;
    const std::string path = glbPath.string();

    if (cgltf_parse_file(&options, path.c_str(), &pData) != cgltf_result_success)
    {
        return std::nullopt;
    }

    const std::unique_ptr<cgltf_data, decltype(&cgltf_free)> owned(pData, &cgltf_free);

    if (cgltf_load_buffers(&options, pData, path.c_str()) != cgltf_result_success)
    {
        return std::nullopt;
    }

    static const std::regex lodWords("_lod[0-9]");
    CollisionShape shape;
    bool any = false;

    for (size_t nodeIndex = 0; nodeIndex < pData->nodes_count; ++nodeIndex)
    {
        const cgltf_node &node = pData->nodes[nodeIndex];

        if (node.mesh == nullptr || node.skin != nullptr || std::regex_search(lowercase(
                std::string(node.mesh->name ? node.mesh->name : "") + (node.name ? node.name : "")), lodWords))
        {
            continue;
        }

        const cgltf_mesh &mesh = coarsestLod ? *coarsestLodOf(*pData, *node.mesh) : *node.mesh;
        float matrix[16];
        cgltf_node_transform_world(&node, matrix);
        const auto toAsset = [&matrix](const float *local)
        {
            return std::array<double, 3>{
                double(matrix[0] * local[0] + matrix[4] * local[1] + matrix[8] * local[2] + matrix[12]),
                double(matrix[1] * local[0] + matrix[5] * local[1] + matrix[9] * local[2] + matrix[13]),
                double(matrix[2] * local[0] + matrix[6] * local[1] + matrix[10] * local[2] + matrix[14])};
        };

        for (size_t primitiveIndex = 0; primitiveIndex < mesh.primitives_count; ++primitiveIndex)
        {
            const cgltf_primitive &primitive = mesh.primitives[primitiveIndex];
            const cgltf_accessor *pPositions = nullptr;

            for (size_t attributeIndex = 0; attributeIndex < primitive.attributes_count; ++attributeIndex)
            {
                if (primitive.attributes[attributeIndex].type == cgltf_attribute_type_position)
                {
                    pPositions = primitive.attributes[attributeIndex].data;
                }
            }

            if (pPositions == nullptr || primitive.type != cgltf_primitive_type_triangles)
            {
                continue;
            }

            std::vector<std::array<double, 3>> points(pPositions->count);

            for (size_t vertex = 0; vertex < pPositions->count; ++vertex)
            {
                float local[3] = {0.0f, 0.0f, 0.0f};
                cgltf_accessor_read_float(pPositions, vertex, local, 3);
                points[vertex] = toAsset(local);

                if (!any || points[vertex][1] < shape.low)
                {
                    shape.low = points[vertex][1];
                }

                if (!any || points[vertex][1] > shape.high)
                {
                    shape.high = points[vertex][1];
                }

                any = true;
            }

            if (boundsOnly)
            {
                continue;
            }

            const size_t count = primitive.indices ? primitive.indices->count : points.size();

            for (size_t corner = 0; corner + 2 < count; corner += 3)
            {
                for (size_t offset = 0; offset < 3; ++offset)
                {
                    const size_t index = primitive.indices
                        ? cgltf_accessor_read_index(primitive.indices, corner + offset) : corner + offset;

                    if (index < points.size())
                    {
                        shape.triangles.push_back(points[index]);
                    }
                }
            }
        }
    }

    if (!any || shape.high - shape.low <= 0.0 || (!boundsOnly && shape.triangles.size() < 3))
    {
        return std::nullopt;
    }

    shape.triangles.resize(shape.triangles.size() / 3 * 3);
    return shape;
}
}

DecorationCollisionModels::DecorationCollisionModels(const std::filesystem::path &assets,
    const std::string &world, const std::string &mapStem, bool indoors)
    : m_assets(assets), m_bindings(collisionBindings(assets, world, mapStem, indoors))
{
}

std::vector<std::array<double, 3>> DecorationCollisionModels::place(const std::string &name, double x, double y,
    double z, double facing, bool scattered, std::vector<std::string> &warnings)
{
    const auto found = m_bindings.find(lowercase(name));
    if (found == m_bindings.end() || (scattered && !found->second.scatter))
    {
        return {};
    }
    const Binding &binding = found->second;
    // `collision_model: lod`: the visible model's coarsest LOD (its base mesh when it has none).
    const bool coarsestLod = binding.collisionModel == "lod";
    const std::string &file = binding.collisionModel.empty() || coarsestLod ? binding.model : binding.collisionModel;
    // A proxy is in the visible model's coordinate system. Its own height can exclude the plume or tall thin trim.
    const std::string key = binding.model + "|" + binding.collisionModel;
    auto [cached, inserted] = m_shapes.try_emplace(key);
    if (inserted)
    {
        cached->second = readCollisionShape(m_assets / file, false, coarsestLod);
        if (cached->second && !binding.collisionModel.empty())
        {
            const auto visible = readCollisionShape(m_assets / binding.model, true);
            if (visible)
            {
                cached->second->low = visible->low;
                cached->second->high = visible->high;
            }
            else
            {
                cached->second.reset();
            }
        }
        if (!cached->second)
        {
            warnings.push_back("decoration collision: " + file + " (`collision: model` of " + name
                + ") cannot be read as a glTF model of triangles: no collision under it");
        }
    }
    if (!cached->second)
    {
        return {};
    }
    const Shape &shape = *cached->second;
    const double jitter = 1.0 + binding.heightJitter * (2.0 * placementRandom(int(x), int(y), 1) - 1.0);
    const double scale = binding.height / (shape.high - shape.low) * jitter;
    const double yaw = (binding.randomYaw ? placementRandom(int(x), int(y), 2) * 2.0 * std::numbers::pi
        : facing * std::numbers::pi / 180.0) + binding.yawOffset;
    const double cosine = std::cos(yaw);
    const double sine = std::sin(yaw);
    std::vector<std::array<double, 3>> triangles;
    triangles.reserve(shape.triangles.size());
    for (const auto &point : shape.triangles)
    {
        const double a = -scale * point[0];
        const double b = scale * point[2];
        triangles.push_back({x + a * cosine - b * sine, y + a * sine + b * cosine, z + binding.zOffset + scale * point[1]});
    }
    return triangles;
}

std::vector<Game::OutdoorBModel> raiseDecorationCollision(const std::filesystem::path &assetRoot,
    const std::string &world, const std::string &mapStem, const std::vector<OutdoorPlacedDecoration> &decorations,
    const std::vector<std::string> &ids, const std::vector<bool> &hidden, std::vector<std::string> &warnings,
    const std::vector<OutdoorPlacedDecoration> &scatter)
{
    DecorationCollisionModels library(assetRoot, world, mapStem, false);
    std::vector<Game::OutdoorBModel> models;
    const auto add = [&](const OutdoorPlacedDecoration &decoration, const std::string &id, bool scattered)
    {
        const auto triangles = library.place(decoration.name, decoration.x, decoration.y, decoration.z,
            decoration.facing, scattered, warnings);
        Game::OutdoorBModel model;
        model.name = "collision:" + id;
        OutdoorModelBuilder builder(model);
        for (size_t corner = 0; corner + 2 < triangles.size(); corner += 3)
        {
            builder.hide(builder.addSurface({triangles[corner], triangles[corner + 1], triangles[corner + 2]}, CollisionTexture, 0));
        }
        if (builder.faceCount() > 0)
        {
            builder.finish();
            models.push_back(std::move(model));
        }
    };
    for (size_t i = 0; i < decorations.size(); ++i)
    {
        if (i >= hidden.size() || !hidden[i])
        {
            add(decorations[i], i < ids.size() ? ids[i] : decorations[i].name, false);
        }
    }
    for (size_t i = 0; i < scatter.size(); ++i)
    {
        add(scatter[i], "scatter_" + std::to_string(i), true);
    }
    return models;
}
}
