#include "core/GlbWriter.h"

#include "core/Json.h"

#include <algorithm>
#include <cstring>
#include <map>

namespace OpenYAMM::Studio
{
namespace
{
void appendUInt32(std::vector<uint8_t> &bytes, uint32_t value)
{
    for (int shift = 0; shift < 32; shift += 8)
    {
        bytes.push_back(static_cast<uint8_t>((value >> shift) & 0xff));
    }
}

void appendFloat(std::vector<uint8_t> &bytes, float value)
{
    uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    appendUInt32(bytes, bits);
}

void pad(std::vector<uint8_t> &bytes, uint8_t filler)
{
    while (bytes.size() % 4 != 0)
    {
        bytes.push_back(filler);
    }
}
}

std::vector<uint8_t> writeGlb(const std::vector<GlbNode> &nodes, const std::string &generator)
{
    std::vector<uint8_t> binary;
    std::vector<std::string> materials;
    std::map<std::string, size_t> materialIndexByName;

    struct View
    {
        size_t offset = 0;
        size_t length = 0;
        int target = 0;
    };

    struct Primitive
    {
        size_t positionAccessor = 0;
        size_t uvAccessor = 0;
        size_t indexAccessor = 0;
        size_t material = 0;
    };

    struct Accessor
    {
        size_t view = 0;
        size_t count = 0;
        // 0 positions, 1 texture coordinates, 2 indices.
        int kind = 0;
        std::array<float, 3> minimum = {};
        std::array<float, 3> maximum = {};
    };

    std::vector<View> views;
    std::vector<Accessor> accessors;
    std::vector<std::vector<Primitive>> meshes;

    for (const GlbNode &node : nodes)
    {
        std::vector<Primitive> primitives;

        for (const GlbFace &face : node.faces)
        {
            Primitive primitive;
            const std::map<std::string, size_t>::const_iterator known = materialIndexByName.find(face.material);

            if (known == materialIndexByName.end())
            {
                primitive.material = materials.size();
                materialIndexByName[face.material] = materials.size();
                materials.push_back(face.material);
            }
            else
            {
                primitive.material = known->second;
            }

            Accessor positions;
            positions.kind = 0;
            positions.count = face.positions.size();
            positions.minimum = face.positions.front();
            positions.maximum = face.positions.front();
            pad(binary, 0);
            views.push_back({binary.size(), face.positions.size() * 12, 34962});

            for (const std::array<float, 3> &position : face.positions)
            {
                for (size_t axis = 0; axis < 3; ++axis)
                {
                    appendFloat(binary, position[axis]);
                    positions.minimum[axis] = std::min(positions.minimum[axis], position[axis]);
                    positions.maximum[axis] = std::max(positions.maximum[axis], position[axis]);
                }
            }

            positions.view = views.size() - 1;
            accessors.push_back(positions);
            primitive.positionAccessor = accessors.size() - 1;

            pad(binary, 0);
            views.push_back({binary.size(), face.uvs.size() * 8, 34962});

            for (const std::array<float, 2> &uv : face.uvs)
            {
                appendFloat(binary, uv[0]);
                appendFloat(binary, uv[1]);
            }

            accessors.push_back({views.size() - 1, face.uvs.size(), 1, {}, {}});
            primitive.uvAccessor = accessors.size() - 1;

            pad(binary, 0);
            views.push_back({binary.size(), face.positions.size() * 4, 34963});

            for (size_t index = 0; index < face.positions.size(); ++index)
            {
                appendUInt32(binary, static_cast<uint32_t>(index));
            }

            accessors.push_back({views.size() - 1, face.positions.size(), 2, {}, {}});
            primitive.indexAccessor = accessors.size() - 1;
            primitives.push_back(primitive);
        }

        meshes.push_back(primitives);
    }

    pad(binary, 0);

    JsonWriter json;
    json.beginObject();
    json.key("asset");
    json.beginObject();
    json.field("version", "2.0");
    json.field("generator", generator);
    json.endObject();
    json.field("scene", 0);
    json.key("scenes");
    json.beginArray();
    json.beginObject();
    json.key("nodes");
    json.beginArray();

    for (size_t index = 0; index < nodes.size(); ++index)
    {
        json.value(static_cast<uint64_t>(index));
    }

    json.endArray();
    json.endObject();
    json.endArray();
    json.key("nodes");
    json.beginArray();

    for (size_t index = 0; index < nodes.size(); ++index)
    {
        json.beginObject();
        json.field("name", nodes[index].name);
        json.field("mesh", static_cast<uint64_t>(index));
        json.endObject();
    }

    json.endArray();
    json.key("meshes");
    json.beginArray();

    for (size_t index = 0; index < nodes.size(); ++index)
    {
        json.beginObject();
        json.field("name", nodes[index].name);
        json.key("primitives");
        json.beginArray();

        for (const Primitive &primitive : meshes[index])
        {
            json.beginObject();
            json.key("attributes");
            json.beginObject();
            json.field("POSITION", static_cast<uint64_t>(primitive.positionAccessor));
            json.field("TEXCOORD_0", static_cast<uint64_t>(primitive.uvAccessor));
            json.endObject();
            json.field("indices", static_cast<uint64_t>(primitive.indexAccessor));
            json.field("material", static_cast<uint64_t>(primitive.material));
            // Triangle fan: one convex polygon.
            json.field("mode", 6);
            json.endObject();
        }

        json.endArray();
        json.endObject();
    }

    json.endArray();
    json.key("materials");
    json.beginArray();

    for (const std::string &material : materials)
    {
        json.beginObject();
        json.field("name", material);
        json.endObject();
    }

    json.endArray();
    json.key("accessors");
    json.beginArray();

    for (const Accessor &accessor : accessors)
    {
        json.beginObject();
        json.field("bufferView", static_cast<uint64_t>(accessor.view));
        json.field("componentType", accessor.kind == 2 ? 5125 : 5126);
        json.field("count", static_cast<uint64_t>(accessor.count));
        json.field("type", accessor.kind == 0 ? "VEC3" : (accessor.kind == 1 ? "VEC2" : "SCALAR"));

        if (accessor.kind == 0)
        {
            json.key("min");
            json.beginArray();

            for (const float value : accessor.minimum)
            {
                json.value(value);
            }

            json.endArray();
            json.key("max");
            json.beginArray();

            for (const float value : accessor.maximum)
            {
                json.value(value);
            }

            json.endArray();
        }

        json.endObject();
    }

    json.endArray();
    json.key("bufferViews");
    json.beginArray();

    for (const View &view : views)
    {
        json.beginObject();
        json.field("buffer", 0);
        json.field("byteOffset", static_cast<uint64_t>(view.offset));
        json.field("byteLength", static_cast<uint64_t>(view.length));
        json.field("target", view.target);
        json.endObject();
    }

    json.endArray();
    json.key("buffers");
    json.beginArray();
    json.beginObject();
    json.field("byteLength", static_cast<uint64_t>(binary.size()));
    json.endObject();
    json.endArray();
    json.endObject();

    const std::string &jsonText = json.text();
    std::vector<uint8_t> jsonBytes(jsonText.begin(), jsonText.end());
    pad(jsonBytes, ' ');

    std::vector<uint8_t> file;
    appendUInt32(file, 0x46546c67);
    appendUInt32(file, 2);
    appendUInt32(file, static_cast<uint32_t>(12 + 8 + jsonBytes.size() + 8 + binary.size()));
    appendUInt32(file, static_cast<uint32_t>(jsonBytes.size()));
    appendUInt32(file, 0x4e4f534a);
    file.insert(file.end(), jsonBytes.begin(), jsonBytes.end());
    appendUInt32(file, static_cast<uint32_t>(binary.size()));
    appendUInt32(file, 0x004e4942);
    file.insert(file.end(), binary.begin(), binary.end());
    return file;
}
}
