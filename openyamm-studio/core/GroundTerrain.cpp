#include "core/GroundTerrain.h"

#include "core/CanonicalYaml.h"
#include "core/CoreMath.h"
#include "core/Json.h"
#include "core/RgbaPng.h"

#include "game/render/TerrainMaterialConfig.h"

#include <algorithm>
#include <array>
#include <charconv>
#include <cmath>
#include <limits>
#include <map>
#include <set>

namespace OpenYAMM::Studio
{
namespace
{
// The weight image (as the outdoor maps'): 128 cells of 16 texels over the 65 536-unit frame, 32 units a texel.
constexpr int MapCells = 128;
constexpr int TexelsPerCell = 16;
constexpr double Frame = 65536.0;
// A ground floor this far under the ground over it at its centre and around it is a tunnel's, not the ground
// (terrain_blend.py COVER, FLOOR_NORMAL_Z).
constexpr double Cover = 128.0;
constexpr double FloorNormalZ = 0.7;
constexpr std::array<double, 3> Luma = {0.2126, 0.7152, 0.0722};
// One channel's tint may rise to this times the brightness ratio (terrain_blend.py MAX_CHANNEL_LIFT).
constexpr double MaxChannelLift = 1.0;

YAML::Node childOf(const YAML::Node &node, const char *pKey)
{
    return node.IsDefined() && node.IsMap() ? node[pKey] : YAML::Node(YAML::NodeType::Undefined);
}

std::string textOf(const YAML::Node &node, const char *pKey, const std::string &fallback)
{
    const YAML::Node value = childOf(node, pKey);
    return value.IsDefined() && value.IsScalar() ? value.Scalar() : fallback;
}

double numberOf(const YAML::Node &node, const char *pKey, double fallback)
{
    const YAML::Node value = childOf(node, pKey);
    return value.IsDefined() && value.IsScalar() ? value.as<double>() : fallback;
}

std::optional<std::array<double, 3>> tripleOf(const YAML::Node &node, const char *pKey)
{
    const YAML::Node value = childOf(node, pKey);

    if (!value.IsDefined() || !value.IsSequence() || value.size() != 3)
    {
        return std::nullopt;
    }

    return std::array<double, 3>{value[0].as<double>(), value[1].as<double>(), value[2].as<double>()};
}

std::string lowerCopy(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char letter)
    {
        return char(std::tolower(letter));
    });
    return text;
}

// round(value, 4) as Python rounds: the decimal nearest the double, read back.
double round4(double value)
{
    char buffer[64];
    const std::to_chars_result written =
        std::to_chars(buffer, buffer + sizeof(buffer), value, std::chars_format::fixed, 4);
    double result = 0.0;
    std::from_chars(buffer, written.ptr, result);
    return result == 0.0 ? 0.0 : result;
}

YAML::Node numberNode(double value)
{
    return YAML::Node(formatNumber(value));
}

YAML::Node tripleNode(const std::array<double, 3> &values)
{
    YAML::Node node(YAML::NodeType::Sequence);

    for (const double value : values)
    {
        node.push_back(numberNode(value));
    }

    return node;
}

// A ground material: a world material with the project's changes, or the project's own.
struct GroundMaterial
{
    std::string name;
    std::string library;
    double repeat = 512.0;
    double heightContrast = 0.35;
    double normalStrength = 1.0;
    double cavity = 0.0;
    double macroBrightness = 0.15;
    std::array<double, 3> macroTint = {1.0, 1.0, 1.0};
    std::array<double, 3> tintScale = {1.0, 1.0, 1.0};
    double fringe = 1.0;
    double meadow = 0.0;
    std::string variant;
    double variantAmount = 0.4;
};

void applyMaterialKeys(const YAML::Node &node, GroundMaterial &material)
{
    material.library = textOf(node, "library", material.library);
    material.repeat = numberOf(node, "repeat", material.repeat);
    material.heightContrast = numberOf(node, "height_contrast", material.heightContrast);
    material.normalStrength = numberOf(node, "normal_strength", material.normalStrength);
    material.cavity = numberOf(node, "cavity", material.cavity);
    material.macroBrightness = numberOf(node, "macro_brightness", material.macroBrightness);
    material.macroTint = tripleOf(node, "macro_tint").value_or(material.macroTint);
    material.tintScale = tripleOf(node, "tint_scale").value_or(material.tintScale);
    material.fringe = numberOf(node, "fringe", material.fringe);
    material.meadow = numberOf(node, "meadow", material.meadow);
    material.variantAmount = numberOf(node, "variant_amount", material.variantAmount);

    if (const std::string variant = textOf(node, "variant", "\x01"); variant != "\x01")
    {
        material.variant = variant == "none" ? std::string() : variant;
    }
}

struct LibraryEntry
{
    std::array<double, 3> mean = {0.5, 0.5, 0.5};
    std::vector<std::string> pictures;
};

bool readLibrary(const std::string &text, std::map<std::string, LibraryEntry> &library, std::string &errorMessage)
{
    try
    {
        const YAML::Node root = YAML::Load(text);
        const YAML::Node materials = childOf(root, "materials");

        if (!materials.IsDefined() || !materials.IsMap())
        {
            errorMessage = "engine/terrain_materials/library.yml has no materials";
            return false;
        }

        for (const auto &pair : materials)
        {
            LibraryEntry entry;
            const std::optional<std::array<double, 3>> mean = tripleOf(pair.second, "mean_color");

            if (mean)
            {
                entry.mean = *mean;
            }

            for (const char *pKind : {"albedo_height", "normal_ao_rough"})
            {
                if (const std::string file = textOf(pair.second, pKind, ""); !file.empty())
                {
                    entry.pictures.push_back(file);
                }
            }

            library[pair.first.as<std::string>()] = entry;
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("engine/terrain_materials/library.yml: ") + exception.what();
        return false;
    }

    return true;
}

// numpy's sum of a float64 array (pairwise, eight partial sums under 128 elements).
double numpySum(const std::vector<double> &values)
{
    const size_t count = values.size();

    if (count < 8)
    {
        double sum = 0.0;

        for (const double value : values)
        {
            sum += value;
        }

        return sum;
    }

    std::array<double, 8> partial = {};

    for (size_t index = 0; index < 8; ++index)
    {
        partial[index] = values[index];
    }

    size_t index = 8;

    for (; index < count - count % 8; index += 8)
    {
        for (size_t lane = 0; lane < 8; ++lane)
        {
            partial[lane] += values[index + lane];
        }
    }

    double sum = ((partial[0] + partial[1]) + (partial[2] + partial[3]))
        + ((partial[4] + partial[5]) + (partial[6] + partial[7]));

    for (; index < count; ++index)
    {
        sum += values[index];
    }

    return sum;
}

using Feature = std::array<int32_t, 2>;

// One line of scipy's Voronoi feature transform (ni_morphology.c _VoronoiFT, sampling none): `line` holds each
// texel's nearest feature found so far ([row, column], row -1 for none), `axis` the axis the line runs along and
// `fixed` the line's coordinate on the other axis.
void voronoiLine(std::vector<Feature> &line, int axis, int fixed, std::vector<Feature> &features,
    std::vector<int32_t> &stack)
{
    const int other = 1 - axis;
    const int32_t length = int32_t(line.size());
    features = line;
    stack.assign(line.size(), 0);
    int32_t top = -1;

    for (int32_t index = 0; index < length; ++index)
    {
        if (features[size_t(index)][0] < 0)
        {
            continue;
        }

        const double along = features[size_t(index)][size_t(axis)];
        const double across = double(features[size_t(index)][size_t(other)] - fixed);
        const double wR = across * across;

        while (top >= 1)
        {
            const Feature &last = features[size_t(stack[size_t(top)])];
            const Feature &before = features[size_t(stack[size_t(top - 1)])];
            const double f1 = last[size_t(axis)];
            const double a = f1 - double(before[size_t(axis)]);
            const double b = along - f1;
            const double tu = double(before[size_t(other)] - fixed);
            const double tv = double(last[size_t(other)] - fixed);
            const double uR = tu * tu;
            const double vR = tv * tv;
            const double c = a + b;

            if (c * vR - b * uR - a * wR - a * b * c <= 0.0)
            {
                break;
            }

            --top;
        }

        ++top;
        stack[size_t(top)] = index;
    }

    if (top < 0)
    {
        return;
    }

    const int32_t last = top;
    int32_t current = 0;

    const auto distance = [&](int32_t entry, int32_t position)
    {
        const Feature &feature = features[size_t(stack[size_t(entry)])];
        double sum = 0.0;

        for (int component = 0; component < 2; ++component)
        {
            const double t = component == axis ? double(feature[size_t(component)] - position)
                                                : double(feature[size_t(component)] - fixed);
            sum += t * t;
        }

        return sum;
    };

    for (int32_t position = 0; position < length; ++position)
    {
        double nearest = distance(current, position);

        while (current < last)
        {
            const double next = distance(current + 1, position);

            if (nearest <= next)
            {
                break;
            }

            nearest = next;
            ++current;
        }

        line[size_t(position)] = features[size_t(stack[size_t(current)])];
    }
}

// The scene's covered rule: the floor-like faces of `ground` lying Cover or more under the topmost ground face at
// their centre and at points three quarters of the way out to each vertex.
std::vector<uint32_t> coveredFaces(
    const std::vector<std::pair<std::vector<std::array<double, 3>>, int>> &faces,
    const std::vector<uint32_t> &faceIndices,
    int size)
{
    std::vector<int16_t> layers;
    std::vector<double> heights;
    std::vector<std::pair<std::vector<std::array<double, 3>>, int>> flat;

    for (const auto &face : faces)
    {
        flat.emplace_back(face.first, 0);
    }

    GroundSteps::rasteriseTopmost(flat, size, layers, heights);
    const double units = Frame / double(size);
    std::vector<uint32_t> result;

    for (size_t index = 0; index < faces.size(); ++index)
    {
        const std::vector<std::array<double, 3>> &points = faces[index].first;
        std::array<double, 3> normal = {0.0, 0.0, 0.0};

        for (size_t corner = 0; corner < points.size(); ++corner)
        {
            const std::array<double, 3> &p = points[corner];
            const std::array<double, 3> &q = points[(corner + 1) % points.size()];
            normal[0] += p[1] * q[2] - p[2] * q[1];
            normal[1] += p[2] * q[0] - p[0] * q[2];
            normal[2] += p[0] * q[1] - p[1] * q[0];
        }

        const double length = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]);

        if (length <= 0.0 || std::fabs(normal[2]) / length < FloorNormalZ)
        {
            continue;
        }

        std::array<double, 3> centre = {0.0, 0.0, 0.0};

        for (const std::array<double, 3> &point : points)
        {
            for (size_t axis = 0; axis < 3; ++axis)
            {
                centre[axis] += point[axis];
            }
        }

        for (double &value : centre)
        {
            value /= double(points.size());
        }

        std::vector<std::array<double, 3>> samples = {centre};

        for (const std::array<double, 3> &point : points)
        {
            samples.push_back({centre[0] + (point[0] - centre[0]) * 0.75, centre[1] + (point[1] - centre[1]) * 0.75,
                centre[2] + (point[2] - centre[2]) * 0.75});
        }

        bool covered = true;

        for (const std::array<double, 3> &sample : samples)
        {
            const int column = std::clamp(int((sample[0] + Frame / 2.0) / units), 0, size - 1);
            const int row = std::clamp(int((Frame / 2.0 - sample[1]) / units), 0, size - 1);

            if (!(heights[size_t(row) * size_t(size) + size_t(column)] > sample[2] + Cover))
            {
                covered = false;
                break;
            }
        }

        if (covered)
        {
            result.push_back(faceIndices[index]);
        }
    }

    std::sort(result.begin(), result.end());
    return result;
}
}

namespace GroundSteps
{
void rasteriseTopmost(
    const std::vector<std::pair<std::vector<std::array<double, 3>>, int>> &faces,
    int size,
    std::vector<int16_t> &layerMap,
    std::vector<double> &heights)
{
    const double units = Frame / double(size);
    layerMap.assign(size_t(size) * size_t(size), -1);
    heights.assign(size_t(size) * size_t(size), -std::numeric_limits<double>::infinity());

    for (const auto &face : faces)
    {
        const std::vector<std::array<double, 3>> &points = face.first;

        for (size_t index = 1; index + 1 < points.size(); ++index)
        {
            const std::array<const std::array<double, 3> *, 3> triangle = {&points[0], &points[index],
                &points[index + 1]};
            std::array<double, 3> column = {};
            std::array<double, 3> row = {};

            // Texel space: column from the frame's west edge, row from its north edge.
            for (size_t corner = 0; corner < 3; ++corner)
            {
                column[corner] = ((*triangle[corner])[0] + Frame / 2.0) / units - 0.5;
                row[corner] = (Frame / 2.0 - (*triangle[corner])[1]) / units - 0.5;
            }

            int x0 = int(std::floor(std::min({column[0], column[1], column[2]})));
            int x1 = int(std::ceil(std::max({column[0], column[1], column[2]})));
            int y0 = int(std::floor(std::min({row[0], row[1], row[2]})));
            int y1 = int(std::ceil(std::max({row[0], row[1], row[2]})));
            x0 = std::max(x0, 0);
            y0 = std::max(y0, 0);
            x1 = std::min(x1, size - 1);
            y1 = std::min(y1, size - 1);

            if (x1 < x0 || y1 < y0)
            {
                continue;
            }

            const double ax = column[0], bx = column[1], cx = column[2];
            const double ay = row[0], by = row[1], cy = row[2];
            const double denominator = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy);

            // Seen edge-on from above (a wall of cliff).
            if (std::fabs(denominator) < 1e-9)
            {
                continue;
            }

            for (int y = y0; y <= y1; ++y)
            {
                for (int x = x0; x <= x1; ++x)
                {
                    const double wa = ((by - cy) * (double(x) - cx) + (cx - bx) * (double(y) - cy)) / denominator;
                    const double wb = ((cy - ay) * (double(x) - cx) + (ax - cx) * (double(y) - cy)) / denominator;
                    const double wc = 1.0 - wa - wb;

                    if (wa < -1e-6 || wb < -1e-6 || wc < -1e-6)
                    {
                        continue;
                    }

                    const double z = wa * (*triangle[0])[2] + wb * (*triangle[1])[2] + wc * (*triangle[2])[2];
                    const size_t texel = size_t(y) * size_t(size) + size_t(x);

                    if (z > heights[texel])
                    {
                        heights[texel] = z;
                        layerMap[texel] = int16_t(face.second);
                    }
                }
            }
        }
    }
}

void fillNearest(std::vector<int16_t> &layerMap, int size)
{
    const size_t count = size_t(size) * size_t(size);
    std::vector<Feature> nearest(count, Feature{-1, -1});
    std::vector<Feature> line(size_t(size), Feature{-1, -1});
    std::vector<Feature> features;
    std::vector<int32_t> stack;

    // Along the rows' axis first (each column), then along the columns' (each row), as scipy's _ComputeFT.
    for (int column = 0; column < size; ++column)
    {
        for (int row = 0; row < size; ++row)
        {
            const size_t texel = size_t(row) * size_t(size) + size_t(column);
            line[size_t(row)] = layerMap[texel] >= 0 ? Feature{row, column} : Feature{-1, column};
        }

        voronoiLine(line, 0, column, features, stack);

        for (int row = 0; row < size; ++row)
        {
            nearest[size_t(row) * size_t(size) + size_t(column)] = line[size_t(row)];
        }
    }

    for (int row = 0; row < size; ++row)
    {
        std::copy(nearest.begin() + std::ptrdiff_t(size_t(row) * size_t(size)),
            nearest.begin() + std::ptrdiff_t(size_t(row + 1) * size_t(size)), line.begin());
        voronoiLine(line, 1, row, features, stack);
        std::copy(line.begin(), line.end(), nearest.begin() + std::ptrdiff_t(size_t(row) * size_t(size)));
    }

    const std::vector<int16_t> original = layerMap;

    for (size_t texel = 0; texel < count; ++texel)
    {
        if (original[texel] < 0 && nearest[texel][0] >= 0)
        {
            layerMap[texel] = original[size_t(nearest[texel][0]) * size_t(size) + size_t(nearest[texel][1])];
        }
    }
}

void gaussianBlur(std::vector<float> &field, int size, double sigma)
{
    // scipy's _gaussian_kernel1d: exp(-0.5 / sigma^2 * x^2) over [-radius, radius], radius int(4 sigma + 0.5),
    // divided by its sum.
    const int radius = int(4.0 * sigma + 0.5);
    const double factor = -0.5 / (sigma * sigma);
    std::vector<double> kernel;

    for (int x = -radius; x <= radius; ++x)
    {
        kernel.push_back(oy::pow(2.718281828459045, factor * double(x * x)));
    }

    const double sum = numpySum(kernel);

    for (double &value : kernel)
    {
        value /= sum;
    }

    // Weights from the centre out (symmetric).
    const std::vector<double> weights(kernel.begin() + radius, kernel.end());
    const size_t width = size_t(size);
    std::vector<float> pass(field.size());
    std::vector<double> accumulator(width);

    // Axis 0 (down the columns), then axis 1 (along the rows); each tap pair added from the outermost in, in double,
    // the result stored as float (ni_filters.c NI_Correlate1D's symmetric case).
    for (int y = 0; y < size; ++y)
    {
        const float *pCentre = field.data() + size_t(y) * width;

        for (size_t x = 0; x < width; ++x)
        {
            accumulator[x] = double(pCentre[x]) * weights[0];
        }

        for (int tap = radius; tap >= 1; --tap)
        {
            const float *pUp = field.data() + size_t(std::max(y - tap, 0)) * width;
            const float *pDown = field.data() + size_t(std::min(y + tap, size - 1)) * width;
            const double weight = weights[size_t(tap)];

            for (size_t x = 0; x < width; ++x)
            {
                accumulator[x] += (double(pUp[x]) + double(pDown[x])) * weight;
            }
        }

        float *pOut = pass.data() + size_t(y) * width;

        for (size_t x = 0; x < width; ++x)
        {
            pOut[x] = float(accumulator[x]);
        }
    }

    std::vector<double> line(width + 2 * size_t(radius));

    for (int y = 0; y < size; ++y)
    {
        const float *pRow = pass.data() + size_t(y) * width;

        for (size_t index = 0; index < line.size(); ++index)
        {
            const int x = std::clamp(int(index) - radius, 0, size - 1);
            line[index] = double(pRow[x]);
        }

        float *pOut = field.data() + size_t(y) * width;

        for (size_t x = 0; x < width; ++x)
        {
            const double *pCentre = line.data() + x + size_t(radius);
            double value = pCentre[0] * weights[0];

            for (int tap = radius; tap >= 1; --tap)
            {
                value += (pCentre[-tap] + pCentre[tap]) * weights[size_t(tap)];
            }

            pOut[x] = float(value);
        }
    }
}
}

GroundAssets readGroundAssets(const std::filesystem::path &assetRoot, const std::string &world)
{
    GroundAssets assets;
    assets.assetRoot = assetRoot;

    if (!assetRoot.empty())
    {
        readTextFile(assetRoot / "worlds" / world / "terrain_materials" / "world.yml", assets.worldMaterialsText);
        readTextFile(assetRoot / "engine" / "terrain_materials" / "library.yml", assets.libraryText);
    }

    return assets;
}

bool buildGroundTerrain(
    const YAML::Node &ground,
    const Game::IndoorMapData &map,
    const GroundAssets &assets,
    const std::string &stem,
    const GroundOptions &options,
    GroundTerrain &result,
    std::string &errorMessage)
{
    result = {};
    const std::string name = stem + "_blv";
    result.materialsFile = name + ".yml";
    result.weightsFile = name + "_weights0.png";

    std::map<std::string, LibraryEntry> library;

    if (assets.libraryText.empty())
    {
        errorMessage = "ground needs the terrain material library (engine/terrain_materials/library.yml of the asset "
            "root)";
        return false;
    }

    if (!readLibrary(assets.libraryText, library, errorMessage))
    {
        return false;
    }

    // The materials: the world's in its order, the project's own after them; the project's keys replace the world's.
    YAML::Node world;
    std::vector<GroundMaterial> materials;

    const auto findMaterial = [&materials](const std::string &materialName) -> GroundMaterial *
    {
        for (GroundMaterial &material : materials)
        {
            if (material.name == materialName)
            {
                return &material;
            }
        }

        return nullptr;
    };

    try
    {
        world = assets.worldMaterialsText.empty() ? YAML::Node(YAML::NodeType::Map)
                                                  : YAML::Load(assets.worldMaterialsText);
        const YAML::Node worldMaterials = childOf(world, "materials");

        if (worldMaterials.IsDefined() && worldMaterials.IsMap())
        {
            for (const auto &pair : worldMaterials)
            {
                GroundMaterial material;
                material.name = pair.first.as<std::string>();
                applyMaterialKeys(pair.second, material);
                materials.push_back(material);
            }
        }

        const YAML::Node own = childOf(ground, "materials");

        for (size_t index = 0; own.IsDefined() && own.IsSequence() && index < own.size(); ++index)
        {
            const YAML::Node entry = own[index];
            const std::string materialName = textOf(entry, "name", "");
            GroundMaterial *pMaterial = findMaterial(materialName);

            if (pMaterial == nullptr)
            {
                GroundMaterial material;
                material.name = materialName;
                materials.push_back(material);
                pMaterial = &materials.back();
            }

            applyMaterialKeys(entry, *pMaterial);
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("the world's terrain materials (world.yml): ") + exception.what();
        return false;
    }

    // The layers: each names its material and textures; a texture belongs to one layer.
    struct Layer
    {
        std::string material;
        std::vector<std::string> textures;
        std::optional<std::array<double, 3>> color;
        std::optional<std::array<double, 3>> tint;
        std::optional<std::array<double, 3>> cliffTint;
    };

    std::vector<Layer> layers;
    std::map<std::string, size_t> layerOfTexture;
    const YAML::Node layerNodes = childOf(ground, "layers");

    for (size_t index = 0; layerNodes.IsDefined() && layerNodes.IsSequence() && index < layerNodes.size(); ++index)
    {
        const YAML::Node node = layerNodes[index];
        Layer layer;
        layer.material = textOf(node, "material", "");
        layer.color = tripleOf(node, "color");
        layer.tint = tripleOf(node, "tint");
        layer.cliffTint = tripleOf(node, "cliff_tint");

        if (layer.color && layer.tint)
        {
            errorMessage = "ground layer " + layer.material + " has both color and tint: give one";
            return false;
        }

        if (findMaterial(layer.material) == nullptr)
        {
            errorMessage = "ground layer " + layer.material + ": no such material in the world's terrain materials "
                "(worlds/<world>/terrain_materials/world.yml) or the ground's `materials`";
            return false;
        }

        for (const Layer &other : layers)
        {
            if (other.material == layer.material)
            {
                errorMessage = "the material " + layer.material + " is in two ground layers: list its textures in one";
                return false;
            }
        }

        const YAML::Node textures = childOf(node, "textures");

        for (size_t texture = 0; textures.IsDefined() && textures.IsSequence() && texture < textures.size(); ++texture)
        {
            const std::string textureName = lowerCopy(textures[texture].as<std::string>());

            if (layerOfTexture.contains(textureName) && layerOfTexture[textureName] != layers.size())
            {
                errorMessage = "the texture " + textureName + " is in two ground layers";
                return false;
            }

            layerOfTexture[textureName] = layers.size();
            layer.textures.push_back(textureName);
        }

        layers.push_back(layer);
    }

    if (layers.empty() || layers.size() > 4)
    {
        errorMessage = "ground needs one to four layers (one weight image holds four)";
        return false;
    }

    // The faces of the built map that are ground.
    std::vector<std::pair<std::vector<std::array<double, 3>>, int>> groundFaces;
    std::vector<uint32_t> groundIndices;

    for (size_t faceIndex = 0; faceIndex < map.faces.size(); ++faceIndex)
    {
        const Game::IndoorFace &face = map.faces[faceIndex];
        const std::map<std::string, size_t>::const_iterator layer = layerOfTexture.find(lowerCopy(face.textureName));

        if (layer == layerOfTexture.end() || face.isPortal || face.vertexIndices.size() < 3)
        {
            continue;
        }

        std::vector<std::array<double, 3>> points;

        for (const uint16_t vertex : face.vertexIndices)
        {
            if (vertex >= map.vertices.size())
            {
                errorMessage = "face " + std::to_string(faceIndex) + " names a vertex the map does not have";
                return false;
            }

            const Game::IndoorVertex &point = map.vertices[vertex];
            points.push_back({double(point.x), double(point.y), double(point.z)});
        }

        groundFaces.emplace_back(std::move(points), int(layer->second));
        groundIndices.push_back(uint32_t(faceIndex));
    }

    if (groundFaces.empty())
    {
        errorMessage = "no face of the built map carries a texture of the ground's layers";
        return false;
    }

    const int size = MapCells * TexelsPerCell;
    result.size = size;

    if (options.excludedFaces)
    {
        result.excludedFaces = *options.excludedFaces;
        std::sort(result.excludedFaces.begin(), result.excludedFaces.end());
    }
    else if (textOf(ground, "covered", "textured") == "textured")
    {
        result.excludedFaces = coveredFaces(groundFaces, groundIndices, size);
    }

    std::vector<std::pair<std::vector<std::array<double, 3>>, int>> weighed;
    std::set<std::string> textures;
    std::vector<bool> layerUsed(layers.size(), false);

    for (size_t index = 0; index < groundFaces.size(); ++index)
    {
        if (std::binary_search(result.excludedFaces.begin(), result.excludedFaces.end(), groundIndices[index]))
        {
            continue;
        }

        weighed.push_back(groundFaces[index]);
        textures.insert(lowerCopy(map.faces[groundIndices[index]].textureName));
        layerUsed[size_t(groundFaces[index].second)] = true;
    }

    result.groundFaces = weighed.size();

    if (weighed.empty())
    {
        errorMessage = "every ground face lies under another (covered): no ground is left to weigh";
        return false;
    }

    for (const Layer &layer : layers)
    {
        for (const std::string &texture : layer.textures)
        {
            if (!textures.contains(texture))
            {
                result.warnings.push_back("ground: the texture " + texture + " of layer " + layer.material
                    + " is on no ground face of the map");
            }
        }
    }

    for (size_t index = 0; index < layers.size(); ++index)
    {
        if (!layerUsed[index])
        {
            result.warnings.push_back("ground: layer " + layers[index].material + " has no face: its weight is empty");
        }
    }

    // The weights: the topmost face's layer per texel, the empty texels their nearest, each layer blurred over the
    // edge softness, normalised, quantised.
    std::vector<int16_t> layerMap;
    std::vector<double> heights;
    GroundSteps::rasteriseTopmost(weighed, size, layerMap, heights);

    if (std::none_of(layerMap.begin(), layerMap.end(), [](int16_t layer) { return layer >= 0; }))
    {
        errorMessage = "the ground faces lie outside the 65 536-unit map frame";
        return false;
    }

    GroundSteps::fillNearest(layerMap, size);
    const double softness = numberOf(ground, "edge_softness", numberOf(world, "edge_softness", 0.0));
    const size_t texels = size_t(size) * size_t(size);
    std::vector<std::vector<float>> fields(layers.size(), std::vector<float>(texels, 0.0f));

    for (size_t texel = 0; texel < texels; ++texel)
    {
        fields[size_t(layerMap[texel])][texel] = 1.0f;
    }

    if (softness > 0.0)
    {
        for (std::vector<float> &field : fields)
        {
            GroundSteps::gaussianBlur(field, size, softness / (Frame / double(size)));
        }
    }

    result.weights.assign(texels * 4, 0);

    for (size_t texel = 0; texel < texels; ++texel)
    {
        float sum = fields[0][texel];

        for (size_t layer = 1; layer < fields.size(); ++layer)
        {
            sum += fields[layer][texel];
        }

        const float denominator = std::max(sum, 1e-6f);

        for (size_t layer = 0; layer < fields.size(); ++layer)
        {
            const float value = fields[layer][texel] / denominator;
            const float scaled = value * 255.0f + 0.5f;
            result.weights[texel * 4 + layer] = uint8_t(std::clamp(scaled, 0.0f, 255.0f));
        }
    }

    fields.clear();
    result.weightsPng = encodeRgbaPng(size, size, result.weights);

    // The material file's layers: the weighted, then the slope material, then the variants of those.
    std::vector<std::string> names;

    for (const Layer &layer : layers)
    {
        names.push_back(layer.material);
    }

    const YAML::Node slopeNode = childOf(ground, "slope");
    const YAML::Node worldSlope = childOf(world, "slope");
    std::string slopeMaterial;
    double slopeStart = numberOf(worldSlope, "start", 0.3);
    double slopeEnd = numberOf(worldSlope, "end", 0.5);

    if (!(childOf(slopeNode, "off").IsDefined() && childOf(slopeNode, "off").as<bool>()))
    {
        slopeMaterial = textOf(slopeNode, "material", textOf(worldSlope, "material", ""));
        slopeStart = numberOf(slopeNode, "start", slopeStart);
        slopeEnd = numberOf(slopeNode, "end", slopeEnd);
    }

    if (!slopeMaterial.empty())
    {
        if (findMaterial(slopeMaterial) == nullptr)
        {
            errorMessage = "the ground's slope material " + slopeMaterial + " is no material of the world or the "
                "ground's `materials`";
            return false;
        }

        if (slopeEnd <= slopeStart)
        {
            errorMessage = "the ground's slope must end above its start";
            return false;
        }

        if (std::find(names.begin(), names.end(), slopeMaterial) == names.end())
        {
            names.push_back(slopeMaterial);
        }
    }

    const std::vector<std::string> beforeVariants = names;

    for (const std::string &materialName : beforeVariants)
    {
        const std::string variant = findMaterial(materialName)->variant;

        if (variant.empty() || std::find(names.begin(), names.end(), variant) != names.end())
        {
            continue;
        }

        if (findMaterial(variant) == nullptr)
        {
            errorMessage = "the material " + materialName + " names a variant " + variant
                + " that is no material of the world or the ground's `materials`";
            return false;
        }

        names.push_back(variant);
    }

    if (names.size() > Game::OutdoorTerrainMaterialConfig::MaxLayers)
    {
        errorMessage = std::to_string(names.size()) + " terrain material layers (the weighted, slope and variants): "
            "the game draws at most 8";
        return false;
    }

    // Library materials and their cooked pictures.
    for (const std::string &materialName : names)
    {
        const GroundMaterial &material = *findMaterial(materialName);
        const std::map<std::string, LibraryEntry>::const_iterator entry = library.find(material.library);

        if (material.library.empty() || entry == library.end())
        {
            errorMessage = "the material " + materialName + " draws the library material '" + material.library
                + "', which engine/terrain_materials/library.yml does not have (the game refuses an unknown terrain "
                "material)";
            return false;
        }

        for (const std::string &picture : entry->second.pictures)
        {
            std::error_code missing;

            if (!assets.assetRoot.empty()
                && !std::filesystem::exists(assets.assetRoot / "engine" / "terrain_materials" / picture, missing))
            {
                errorMessage = "the library material " + material.library + "'s picture engine/terrain_materials/"
                    + picture + " is not in the asset root (the game refuses the map's terrain without it)";
                return false;
            }
        }
    }

    const auto layerOfMaterial = [&layers](const std::string &materialName) -> const Layer *
    {
        for (const Layer &layer : layers)
        {
            if (layer.material == materialName)
            {
                return &layer;
            }
        }

        return nullptr;
    };

    const auto meanOf = [&](const std::string &materialName)
    {
        return library.at(findMaterial(materialName)->library).mean;
    };

    const auto display = [&](const std::string &materialName) -> std::optional<std::array<double, 3>>
    {
        const Layer *pLayer = layerOfMaterial(materialName);

        if (pLayer == nullptr || !pLayer->color)
        {
            return std::nullopt;
        }

        return std::array<double, 3>{(*pLayer->color)[0] / 255.0, (*pLayer->color)[1] / 255.0,
            (*pLayer->color)[2] / 255.0};
    };

    // Which material each variant varies (the last in the materials' order, as terrain_blend.py's dict).
    std::map<std::string, std::string> variantParent;

    for (const GroundMaterial &material : materials)
    {
        if (!material.variant.empty()
            && std::find(names.begin(), names.end(), material.variant) != names.end()
            && std::find(names.begin(), names.end(), material.name) != names.end())
        {
            variantParent[material.variant] = material.name;
        }
    }

    YAML::Node layerList(YAML::NodeType::Sequence);

    for (const std::string &materialName : names)
    {
        const GroundMaterial &material = *findMaterial(materialName);
        const std::array<double, 3> mean = meanOf(materialName);
        const Layer *pLayer = layerOfMaterial(materialName);
        std::array<double, 3> tint = {1.0, 1.0, 1.0};

        if (pLayer != nullptr && pLayer->tint)
        {
            tint = *pLayer->tint;
        }
        else if (const std::optional<std::array<double, 3>> colour = display(materialName))
        {
            const double luminance = (Luma[0] * (*colour)[0] + Luma[1] * (*colour)[1] + Luma[2] * (*colour)[2])
                / std::max(Luma[0] * mean[0] + Luma[1] * mean[1] + Luma[2] * mean[2], 1e-3);

            for (size_t channel = 0; channel < 3; ++channel)
            {
                // No channel rises over the brightness ratio: per-channel tints cannot desaturate.
                tint[channel] = std::min((*colour)[channel] / std::max(mean[channel], 1e-3), luminance * MaxChannelLift);
            }
        }
        else if (variantParent.contains(materialName))
        {
            // A variant keeps its own tones under its parent's tint.
            const std::string &parent = variantParent[materialName];
            const std::array<double, 3> parentMean = meanOf(parent);
            const Layer *pParent = layerOfMaterial(parent);
            const std::optional<std::array<double, 3>> parentColour = display(parent);

            for (size_t channel = 0; channel < 3; ++channel)
            {
                const double base = pParent != nullptr && pParent->tint ? (*pParent->tint)[channel]
                    : (parentColour ? (*parentColour)[channel] : parentMean[channel])
                        / std::max(parentMean[channel], 1e-3);
                tint[channel] = base * material.tintScale[channel];
            }
        }

        for (double &value : tint)
        {
            value = round4(std::clamp(value, 0.0, 4.0));
        }

        YAML::Node entry(YAML::NodeType::Map);
        entry["name"] = materialName;
        entry["library"] = material.library;
        entry["tint"] = tripleNode(tint);
        entry["repeat"] = numberNode(material.repeat);
        entry["height_contrast"] = numberNode(material.heightContrast);
        entry["normal_strength"] = numberNode(material.normalStrength);
        entry["cavity"] = numberNode(material.cavity);
        entry["macro_brightness"] = numberNode(material.macroBrightness);
        entry["macro_tint"] = tripleNode(material.macroTint);
        entry["fringe"] = numberNode(material.fringe);

        if (material.meadow != 0.0)
        {
            entry["meadow"] = numberNode(material.meadow);
        }

        if (!material.variant.empty())
        {
            const std::vector<std::string>::const_iterator variant =
                std::find(names.begin(), names.end(), material.variant);

            if (variant != names.end())
            {
                entry["variant"] = int(variant - names.begin());
                entry["variant_amount"] = numberNode(material.variantAmount);
            }
            else
            {
                result.warnings.push_back("ground: the variant " + material.variant + " of " + materialName
                    + " is left out (a variant's own variant is not drawn)");
            }
        }

        if (!slopeMaterial.empty() && pLayer != nullptr)
        {
            std::optional<std::array<double, 3>> cliff = pLayer->cliffTint;

            if (!cliff)
            {
                // Steep ground of every layer takes the slope material's colour, else this layer's.
                const std::optional<std::array<double, 3>> source =
                    display(slopeMaterial) ? display(slopeMaterial) : display(materialName);

                if (source)
                {
                    const std::array<double, 3> cliffMean = meanOf(slopeMaterial);
                    cliff = std::array<double, 3>{};

                    for (size_t channel = 0; channel < 3; ++channel)
                    {
                        (*cliff)[channel] = (*source)[channel] / std::max(cliffMean[channel], 1e-3);
                    }
                }
            }

            if (cliff)
            {
                for (double &value : *cliff)
                {
                    value = round4(std::clamp(value, 0.0, 4.0));
                }

                entry["cliff_tint"] = tripleNode(*cliff);
            }
        }

        layerList.push_back(entry);
    }

    YAML::Node config(YAML::NodeType::Map);
    config["version"] = 1;
    config["texels_per_cell"] = TexelsPerCell;
    config["weights"].push_back(result.weightsFile);
    config["weighted_layers"] = int(layers.size());
    YAML::Node fringe(YAML::NodeType::Map);
    const YAML::Node fringeNode = childOf(ground, "fringe").IsDefined() ? childOf(ground, "fringe")
                                                                      : childOf(world, "fringe");
    fringe["strength"] = numberNode(numberOf(fringeNode, "strength", 0.0));
    fringe["scale"] = numberNode(numberOf(fringeNode, "scale", 2048.0));
    config["fringe"] = fringe;
    config["layers"] = layerList;
    const YAML::Node meadowNode = childOf(ground, "meadow").IsDefined() ? childOf(ground, "meadow")
                                                                      : childOf(world, "meadow");

    if (const std::optional<std::array<double, 3>> dry = tripleOf(meadowNode, "dry"))
    {
        if (const std::optional<std::array<double, 3>> lush = tripleOf(meadowNode, "lush"))
        {
            YAML::Node meadow(YAML::NodeType::Map);
            meadow["dry"] = tripleNode(*dry);
            meadow["lush"] = tripleNode(*lush);
            config["meadow"] = meadow;
        }
    }

    if (!slopeMaterial.empty())
    {
        YAML::Node slope(YAML::NodeType::Map);
        slope["layer"] = int(std::find(names.begin(), names.end(), slopeMaterial) - names.begin());
        slope["start"] = numberNode(slopeStart);
        slope["end"] = numberNode(slopeEnd);
        config["slope"] = slope;
    }

    std::string textureList;

    for (const std::string &texture : textures)
    {
        textureList += (textureList.empty() ? "" : ", ") + texture;
    }

    result.materialsText = "# Written by " + options.writtenBy + " for " + stem + ".blv's ground faces\n# ("
        + textureList + ").\n" + writeCanonicalYaml(config);
    result.layers = names;
    result.weightedLayers = layers.size();

    // The game's own reader must take the file.
    std::string parseError;
    const std::string directory = "worlds/terrain_materials/";

    if (!Game::parseTerrainMaterialConfig(result.materialsText, directory, directory + result.materialsFile,
            parseError))
    {
        errorMessage = "the game refuses the ground's material file: " + parseError;
        return false;
    }

    YAML::Node terrain(YAML::NodeType::Map);
    terrain["materials"] = result.materialsFile;

    for (const std::string &texture : textures)
    {
        terrain["textures"].push_back(texture);
    }

    if (!result.excludedFaces.empty())
    {
        for (const uint32_t face : result.excludedFaces)
        {
            terrain["exclude_faces"].push_back(int(face));
        }
    }

    if (const std::string grass = textOf(ground, "grass", ""); !grass.empty())
    {
        terrain["grass"] = grass;
        std::error_code missing;

        if (!assets.assetRoot.empty() && !std::filesystem::exists(assets.assetRoot / grass, missing))
        {
            result.warnings.push_back("ground: the grass file " + grass + " is not in the asset root (the game "
                "grows no grass unless a mount gives it)");
        }
    }

    result.sceneTerrain = terrain;
    return true;
}

void checkProjectGround(const Project &project, std::vector<ProjectIssue> &issues)
{
    if (!project.has("atmosphere.yml"))
    {
        return;
    }

    const YAML::Node atmosphere = project.document("atmosphere.yml");

    if (!childOf(atmosphere, "ground").IsDefined())
    {
        return;
    }

    const YAML::Node card = project.document("project.yml");

    if (childOf(card, "base").IsDefined())
    {
        issues.push_back({"atmosphere.yml", "ground", "ground is for new maps: an overlay replaces the base map's "
            "terrain block with `terrain`", "ground"});
    }
    else if (textOf(card, "kind", "") != "indoor")
    {
        issues.push_back({"atmosphere.yml", "ground", "ground is for indoor maps open to the sky: an outdoor map's "
            "ground is its land", "ground"});
    }

    if (childOf(atmosphere, "terrain").IsDefined())
    {
        issues.push_back({"atmosphere.yml", "terrain", "terrain and ground together: ground writes the scene's "
            "terrain block itself", "ground"});
    }
}

bool buildProjectGround(
    const Project &project,
    const Game::IndoorMapData &map,
    const std::filesystem::path &assetRoot,
    const std::string &stem,
    std::optional<GroundTerrain> &ground,
    std::vector<ProjectIssue> &issues)
{
    ground.reset();

    if (!project.has("atmosphere.yml"))
    {
        return true;
    }

    const YAML::Node atmosphere = project.document("atmosphere.yml");
    const YAML::Node groundNode = childOf(atmosphere, "ground");

    if (!groundNode.IsDefined())
    {
        return true;
    }

    if (assetRoot.empty())
    {
        issues.push_back({"atmosphere.yml", "ground", "ground needs an asset root (--assets): the world's terrain "
            "materials and the material library", "ground"});
        return false;
    }

    const GroundAssets assets = readGroundAssets(assetRoot, textOf(project.document("project.yml"), "world", ""));
    GroundTerrain terrain;
    std::string errorMessage;

    if (!buildGroundTerrain(groundNode, map, assets, stem, GroundOptions{}, terrain, errorMessage))
    {
        issues.push_back({"atmosphere.yml", "ground", errorMessage, "ground"});
        return false;
    }

    if (!childOf(atmosphere, "open_sky").IsDefined())
    {
        terrain.warnings.push_back("ground without open_sky: the terrain is drawn, but under the map's own ceiling "
            "and without daylight");
    }

    ground = std::move(terrain);
    return true;
}

bool writeGroundFiles(
    const std::optional<GroundTerrain> &ground,
    const std::filesystem::path &outputDirectory,
    const std::string &stem,
    std::vector<std::string> &files,
    std::string &errorMessage)
{
    const std::string materialsFile = stem + "_blv.yml";
    const std::string weightsFile = stem + "_blv_weights0.png";

    if (!ground)
    {
        std::error_code staleError;
        std::filesystem::remove(outputDirectory / materialsFile, staleError);
        std::filesystem::remove(outputDirectory / weightsFile, staleError);
        return true;
    }

    if (!writeTextFileAtomically(outputDirectory / materialsFile, ground->materialsText, errorMessage)
        || !writeBinaryFileAtomically(outputDirectory / weightsFile, ground->weightsPng, errorMessage))
    {
        return false;
    }

    files.push_back(materialsFile);
    files.push_back(weightsFile);
    return true;
}

bool installGroundFiles(
    const std::filesystem::path &buildDirectory,
    const std::filesystem::path &assetRoot,
    const std::string &world,
    const std::string &stem,
    std::vector<std::string> &installedFiles,
    std::string &errorMessage)
{
    const std::filesystem::path directory = assetRoot / "worlds" / world / "terrain_materials";
    const std::string materialsFile = stem + "_blv.yml";
    const std::string weightsFile = stem + "_blv_weights0.png";
    std::error_code error;

    if (!std::filesystem::exists(buildDirectory / materialsFile, error))
    {
        // An old pair of this studio map goes; a file another tool wrote under the name stays.
        std::string text;

        if (readTextFile(directory / materialsFile, text) && text.starts_with("# Written by oymap"))
        {
            std::filesystem::remove(directory / materialsFile, error);
            std::filesystem::remove(directory / weightsFile, error);
        }

        return true;
    }

    std::filesystem::create_directories(directory, error);

    for (const std::string &file : {materialsFile, weightsFile})
    {
        std::vector<uint8_t> bytes;
        std::string text;

        if (!readTextFile(buildDirectory / file, text))
        {
            errorMessage = "could not read " + (buildDirectory / file).string();
            return false;
        }

        bytes.assign(text.begin(), text.end());

        if (!writeBinaryFileAtomically(directory / file, bytes, errorMessage))
        {
            return false;
        }

        installedFiles.push_back("worlds/" + world + "/terrain_materials/" + file);
    }

    return true;
}
}
