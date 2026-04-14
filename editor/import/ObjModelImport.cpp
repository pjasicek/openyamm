#include "editor/import/ObjModelImport.h"

#define CGLTF_IMPLEMENTATION
#include <cgltf/cgltf.h>

#include <algorithm>
#include <array>
#include <charconv>
#include <cctype>
#include <cmath>
#include <cstring>
#include <fstream>
#include <sstream>
#include <unordered_map>
#include <unordered_set>

namespace OpenYAMM::Editor
{
namespace
{
enum class ImportedModelFileType
{
    Obj,
    Gltf,
    Glb
};

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

std::string removeComment(const std::string &line)
{
    const size_t commentOffset = line.find('#');

    if (commentOffset == std::string::npos)
    {
        return line;
    }

    return line.substr(0, commentOffset);
}

bool parseFloatToken(const std::string &text, float &value)
{
    const char *pBegin = text.data();
    const char *pEnd = text.data() + text.size();
    const std::from_chars_result result = std::from_chars(pBegin, pEnd, value);
    return result.ec == std::errc() && result.ptr == pEnd;
}

bool parseIntToken(const std::string &text, int &value)
{
    const char *pBegin = text.data();
    const char *pEnd = text.data() + text.size();
    const std::from_chars_result result = std::from_chars(pBegin, pEnd, value);
    return result.ec == std::errc() && result.ptr == pEnd;
}

bool resolveObjIndex(int rawIndex, size_t count, size_t &resolvedIndex)
{
    if (rawIndex > 0)
    {
        const size_t candidateIndex = static_cast<size_t>(rawIndex - 1);

        if (candidateIndex >= count)
        {
            return false;
        }

        resolvedIndex = candidateIndex;
        return true;
    }

    if (rawIndex < 0)
    {
        const ptrdiff_t candidateIndex = static_cast<ptrdiff_t>(count) + static_cast<ptrdiff_t>(rawIndex);

        if (candidateIndex < 0 || static_cast<size_t>(candidateIndex) >= count)
        {
            return false;
        }

        resolvedIndex = static_cast<size_t>(candidateIndex);
        return true;
    }

    return false;
}

bool parseFaceVertexToken(
    const std::string &token,
    size_t positionCount,
    const std::vector<std::pair<float, float>> &texCoords,
    ImportedModelFaceVertex &vertex,
    std::string &errorMessage)
{
    const size_t firstSlash = token.find('/');

    std::string positionIndexText = token;
    std::string textureIndexText;

    if (firstSlash != std::string::npos)
    {
        positionIndexText = token.substr(0, firstSlash);
        const size_t secondSlash = token.find('/', firstSlash + 1);
        textureIndexText = token.substr(
            firstSlash + 1,
            secondSlash == std::string::npos ? std::string::npos : secondSlash - firstSlash - 1);
    }

    int rawPositionIndex = 0;

    if (!parseIntToken(positionIndexText, rawPositionIndex))
    {
        errorMessage = "invalid OBJ face position index: " + token;
        return false;
    }

    if (!resolveObjIndex(rawPositionIndex, positionCount, vertex.positionIndex))
    {
        errorMessage = "OBJ face position index out of range: " + token;
        return false;
    }

    if (!textureIndexText.empty())
    {
        int rawTextureIndex = 0;
        size_t resolvedTextureIndex = 0;

        if (!parseIntToken(textureIndexText, rawTextureIndex))
        {
            errorMessage = "invalid OBJ face texture index: " + token;
            return false;
        }

        if (!resolveObjIndex(rawTextureIndex, texCoords.size(), resolvedTextureIndex))
        {
            errorMessage = "OBJ face texture index out of range: " + token;
            return false;
        }

        vertex.hasUv = true;
        vertex.u = texCoords[resolvedTextureIndex].first;
        vertex.v = texCoords[resolvedTextureIndex].second;
    }

    return true;
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

bool readBinaryFile(const std::filesystem::path &path, std::vector<uint8_t> &bytes)
{
    std::ifstream input(path, std::ios::binary);

    if (!input)
    {
        return false;
    }

    input.seekg(0, std::ios::end);
    const std::streamoff length = input.tellg();

    if (length < 0)
    {
        return false;
    }

    input.seekg(0, std::ios::beg);
    bytes.resize(static_cast<size_t>(length));

    if (!bytes.empty())
    {
        input.read(reinterpret_cast<char *>(bytes.data()), length);

        if (!input)
        {
            bytes.clear();
            return false;
        }
    }

    return true;
}

bool decodeBase64DataUri(std::string_view text, std::vector<uint8_t> &bytes)
{
    static constexpr int DecodeTable[256] = {
        -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
        -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
        -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,62,-1,-1,-1,63,
        52,53,54,55,56,57,58,59,60,61,-1,-1,-1,-2,-1,-1,
        -1,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,
        15,16,17,18,19,20,21,22,23,24,25,-1,-1,-1,-1,-1,
        -1,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,
        41,42,43,44,45,46,47,48,49,50,51,-1,-1,-1,-1,-1,
        -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
        -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
        -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
        -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
        -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
        -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
        -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
        -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1
    };

    bytes.clear();
    int accumulator = 0;
    int bits = 0;

    for (char character : text)
    {
        const unsigned char value = static_cast<unsigned char>(character);
        const int decoded = DecodeTable[value];

        if (decoded == -1)
        {
            if (std::isspace(value) != 0)
            {
                continue;
            }

            return false;
        }

        if (decoded == -2)
        {
            break;
        }

        accumulator = (accumulator << 6) | decoded;
        bits += 6;

        if (bits >= 8)
        {
            bits -= 8;
            bytes.push_back(static_cast<uint8_t>((accumulator >> bits) & 0xff));
        }
    }

    return true;
}

bool loadGltfImageBytes(const std::filesystem::path &path, const cgltf_image &image, std::vector<uint8_t> &bytes)
{
    bytes.clear();

    if (image.buffer_view != nullptr)
    {
        const cgltf_buffer_view &bufferView = *image.buffer_view;

        if (bufferView.buffer == nullptr || bufferView.buffer->data == nullptr)
        {
            return false;
        }

        const uint8_t *pBufferData = static_cast<const uint8_t *>(bufferView.buffer->data);
        bytes.assign(
            pBufferData + bufferView.offset,
            pBufferData + bufferView.offset + bufferView.size);
        return true;
    }

    if (image.uri == nullptr || image.uri[0] == '\0')
    {
        return false;
    }

    const std::string uri = trimCopy(image.uri);

    if (uri.rfind("data:", 0) == 0)
    {
        const size_t commaIndex = uri.find(',');

        if (commaIndex == std::string::npos)
        {
            return false;
        }

        const std::string metadata = toLowerCopy(uri.substr(0, commaIndex));

        if (metadata.find(";base64") == std::string::npos)
        {
            return false;
        }

        return decodeBase64DataUri(uri.substr(commaIndex + 1), bytes);
    }

    const std::filesystem::path imagePath = path.parent_path() / std::filesystem::path(uri);
    return readBinaryFile(imagePath, bytes);
}

std::string composeGltfMaterialName(const cgltf_data &data, const cgltf_material *pMaterial)
{
    if (pMaterial == nullptr || data.materials == nullptr || pMaterial < data.materials)
    {
        return {};
    }

    const size_t materialIndex = static_cast<size_t>(pMaterial - data.materials);
    const std::string materialName =
        pMaterial->name != nullptr && pMaterial->name[0] != '\0'
        ? trimCopy(pMaterial->name)
        : std::string();

    if (!materialName.empty())
    {
        return materialName + " [" + std::to_string(materialIndex) + "]";
    }

    return "material_" + std::to_string(materialIndex);
}

ImportedModelMaterial *findImportedMaterial(ImportedModel &model, const std::string &materialName)
{
    for (ImportedModelMaterial &material : model.materials)
    {
        if (material.name == materialName)
        {
            return &material;
        }
    }

    return nullptr;
}

std::string defaultTextureLabelForGltfImage(const cgltf_image &image, const std::string &materialName)
{
    if (image.name != nullptr && image.name[0] != '\0')
    {
        return trimCopy(image.name);
    }

    if (image.uri != nullptr && image.uri[0] != '\0')
    {
        return trimCopy(std::filesystem::path(image.uri).stem().string());
    }

    return materialName;
}

void appendGltfMaterialToImportedModel(
    const std::filesystem::path &path,
    const cgltf_data &data,
    const cgltf_material *pMaterial,
    ImportedModel &model)
{
    if (pMaterial == nullptr)
    {
        return;
    }

    const std::string materialName = composeGltfMaterialName(data, pMaterial);

    if (materialName.empty())
    {
        return;
    }

    ImportedModelMaterial *pImportedMaterial = findImportedMaterial(model, materialName);

    if (pImportedMaterial == nullptr)
    {
        ImportedModelMaterial material = {};
        material.name = materialName;
        model.materials.push_back(std::move(material));
        pImportedMaterial = &model.materials.back();
    }

    const cgltf_texture *pTexture = pMaterial->has_pbr_metallic_roughness
        ? pMaterial->pbr_metallic_roughness.base_color_texture.texture
        : nullptr;

    if (pTexture == nullptr || pTexture->image == nullptr)
    {
        return;
    }

    if (pImportedMaterial->textureLabel.empty())
    {
        pImportedMaterial->textureLabel = defaultTextureLabelForGltfImage(*pTexture->image, materialName);
    }

    if (pImportedMaterial->textureMimeType.empty() && pTexture->image->mime_type != nullptr)
    {
        pImportedMaterial->textureMimeType = trimCopy(pTexture->image->mime_type);
    }

    if (!pImportedMaterial->textureBytes.empty())
    {
        return;
    }

    std::vector<uint8_t> bytes;

    if (loadGltfImageBytes(path, *pTexture->image, bytes))
    {
        pImportedMaterial->textureBytes = std::move(bytes);
    }
}

ImportedModelFileType importedModelFileTypeFromPath(const std::filesystem::path &path)
{
    const std::string extension = toLowerCopy(path.extension().string());

    if (extension == ".gltf")
    {
        return ImportedModelFileType::Gltf;
    }

    if (extension == ".glb")
    {
        return ImportedModelFileType::Glb;
    }

    return ImportedModelFileType::Obj;
}

std::string effectiveImportedModelName(
    const std::filesystem::path &path,
    const std::string &candidateName)
{
    const std::string trimmedName = trimCopy(candidateName);

    if (!trimmedName.empty())
    {
        return trimmedName;
    }

    const std::string fallbackName = trimCopy(path.stem().string());
    return fallbackName.empty() ? "model" : fallbackName;
}

void ensureUniqueImportedModelNames(const std::filesystem::path &path, std::vector<ImportedModel> &models)
{
    std::vector<std::string> baseNames;
    baseNames.reserve(models.size());
    std::unordered_map<std::string, size_t> nameCounts;

    for (ImportedModel &model : models)
    {
        const std::string baseName = effectiveImportedModelName(path, model.name);
        baseNames.push_back(baseName);
        ++nameCounts[toLowerCopy(baseName)];
    }

    std::unordered_map<std::string, size_t> seenCounts;

    for (size_t index = 0; index < models.size(); ++index)
    {
        const std::string normalizedName = toLowerCopy(baseNames[index]);
        const size_t totalCount = nameCounts[normalizedName];

        if (totalCount <= 1)
        {
            models[index].name = baseNames[index];
            continue;
        }

        const size_t instanceIndex = ++seenCounts[normalizedName];
        models[index].name = baseNames[index] + " [" + std::to_string(instanceIndex) + "]";
    }
}

std::string composeGltfImportedModelName(const cgltf_node &node)
{
    const std::string nodeName =
        node.name != nullptr && node.name[0] != '\0'
        ? trimCopy(node.name)
        : std::string();
    const std::string meshName =
        node.mesh != nullptr && node.mesh->name != nullptr && node.mesh->name[0] != '\0'
        ? trimCopy(node.mesh->name)
        : std::string();

    if (!nodeName.empty() && !meshName.empty())
    {
        if (toLowerCopy(nodeName) == toLowerCopy(meshName))
        {
            return nodeName;
        }

        return nodeName + " :: " + meshName;
    }

    if (!nodeName.empty())
    {
        return nodeName;
    }

    if (!meshName.empty())
    {
        return meshName;
    }

    return "mesh";
}

ImportedModel mergeImportedModels(const std::filesystem::path &path, const std::vector<ImportedModel> &models)
{
    ImportedModel mergedModel = {};
    mergedModel.name = effectiveImportedModelName(path, path.stem().string());

    if (models.size() == 1)
    {
        return models.front();
    }

    size_t totalPositionCount = 0;
    size_t totalFaceCount = 0;
    size_t totalMaterialCount = 0;

    for (const ImportedModel &model : models)
    {
        totalPositionCount += model.positions.size();
        totalFaceCount += model.faces.size();
        totalMaterialCount += model.materials.size();
    }

    mergedModel.positions.reserve(totalPositionCount);
    mergedModel.faces.reserve(totalFaceCount);
    mergedModel.materials.reserve(totalMaterialCount);
    std::unordered_set<std::string> seenMaterialNames;

    for (const ImportedModel &model : models)
    {
        const size_t basePositionIndex = mergedModel.positions.size();
        mergedModel.positions.insert(mergedModel.positions.end(), model.positions.begin(), model.positions.end());

        for (const ImportedModelMaterial &material : model.materials)
        {
            const std::string normalizedMaterialName = toLowerCopy(trimCopy(material.name));

            if (!normalizedMaterialName.empty() && seenMaterialNames.insert(normalizedMaterialName).second)
            {
                mergedModel.materials.push_back(material);
            }
        }

        for (const ImportedModelFace &sourceFace : model.faces)
        {
            ImportedModelFace face = sourceFace;

            for (ImportedModelFaceVertex &vertex : face.vertices)
            {
                vertex.positionIndex += basePositionIndex;
            }

            mergedModel.faces.push_back(std::move(face));
        }
    }

    return mergedModel;
}

bool selectImportedModelByName(
    const std::filesystem::path &path,
    const std::vector<ImportedModel> &models,
    const std::string &sourceMeshName,
    ImportedModel &model,
    std::string &errorMessage)
{
    const std::string normalizedSourceMeshName = toLowerCopy(trimCopy(sourceMeshName));

    if (normalizedSourceMeshName.empty())
    {
        model = mergeImportedModels(path, models);
        return true;
    }

    for (const ImportedModel &candidate : models)
    {
        if (toLowerCopy(trimCopy(candidate.name)) == normalizedSourceMeshName)
        {
            model = candidate;
            return true;
        }
    }

    errorMessage = "model file does not contain mesh/node '" + sourceMeshName + "'";
    return false;
}

bool applyNodeTransform(const float matrix[16], float x, float y, float z, ImportedModelPosition &position)
{
    if (!std::isfinite(x) || !std::isfinite(y) || !std::isfinite(z))
    {
        return false;
    }

    position.x = matrix[0] * x + matrix[4] * y + matrix[8] * z + matrix[12];
    position.y = matrix[1] * x + matrix[5] * y + matrix[9] * z + matrix[13];
    position.z = matrix[2] * x + matrix[6] * y + matrix[10] * z + matrix[14];
    return std::isfinite(position.x) && std::isfinite(position.y) && std::isfinite(position.z);
}

const cgltf_accessor *findAttributeAccessor(const cgltf_primitive &primitive, cgltf_attribute_type type)
{
    for (cgltf_size attributeIndex = 0; attributeIndex < primitive.attributes_count; ++attributeIndex)
    {
        const cgltf_attribute &attribute = primitive.attributes[attributeIndex];

        if (attribute.type == type && attribute.data != nullptr)
        {
            return attribute.data;
        }
    }

    return nullptr;
}

bool readAccessorFloatComponents(
    const cgltf_accessor &accessor,
    cgltf_size index,
    cgltf_size componentCount,
    float *pValues)
{
    if (index >= accessor.count || pValues == nullptr)
    {
        return false;
    }

    float values[4] = {};

    if (cgltf_accessor_read_float(&accessor, index, values, 4) == 0)
    {
        return false;
    }

    for (cgltf_size componentIndex = 0; componentIndex < componentCount; ++componentIndex)
    {
        pValues[componentIndex] = values[componentIndex];
    }

    return true;
}

bool appendPrimitiveTriangleFace(
    const std::vector<std::pair<float, float>> &texCoords,
    const std::vector<bool> &hasTexCoord,
    size_t basePositionIndex,
    size_t i0,
    size_t i1,
    size_t i2,
    const std::string &materialName,
    ImportedModel &model,
    std::string &errorMessage)
{
    ImportedModelFace face = {};
    face.materialName = materialName;

    const size_t indices[3] = {i0, i1, i2};

    for (size_t localIndex : indices)
    {
        if (basePositionIndex + localIndex >= model.positions.size())
        {
            errorMessage = "glTF primitive position index out of range";
            return false;
        }

        ImportedModelFaceVertex vertex = {};
        vertex.positionIndex = basePositionIndex + localIndex;

        if (localIndex < texCoords.size() && localIndex < hasTexCoord.size() && hasTexCoord[localIndex])
        {
            vertex.hasUv = true;
            vertex.u = texCoords[localIndex].first;
            vertex.v = texCoords[localIndex].second;
        }

        face.vertices.push_back(vertex);
    }

    model.faces.push_back(std::move(face));
    return true;
}

bool appendPrimitiveFaces(
    const cgltf_primitive &primitive,
    const std::vector<std::pair<float, float>> &texCoords,
    const std::vector<bool> &hasTexCoord,
    size_t basePositionIndex,
    size_t localVertexCount,
    const std::string &materialName,
    ImportedModel &model,
    std::string &errorMessage)
{
    std::vector<size_t> indices;
    const size_t indexCount = primitive.indices != nullptr ? primitive.indices->count : localVertexCount;
    indices.reserve(indexCount);

    for (size_t index = 0; index < indexCount; ++index)
    {
        const size_t vertexIndex = primitive.indices != nullptr
            ? cgltf_accessor_read_index(primitive.indices, index)
            : index;

        if (vertexIndex >= localVertexCount)
        {
            errorMessage = "glTF primitive index out of range";
            return false;
        }

        indices.push_back(vertexIndex);
    }

    switch (primitive.type)
    {
    case cgltf_primitive_type_triangles:
        if (indices.size() % 3 != 0)
        {
            errorMessage = "glTF triangle primitive index count is not divisible by 3";
            return false;
        }

        for (size_t triangleIndex = 0; triangleIndex + 2 < indices.size(); triangleIndex += 3)
        {
            if (!appendPrimitiveTriangleFace(
                    texCoords,
                    hasTexCoord,
                    basePositionIndex,
                    indices[triangleIndex],
                    indices[triangleIndex + 1],
                    indices[triangleIndex + 2],
                    materialName,
                    model,
                    errorMessage))
            {
                return false;
            }
        }
        return true;

    case cgltf_primitive_type_triangle_strip:
        if (indices.size() < 3)
        {
            errorMessage = "glTF triangle strip primitive has fewer than 3 indices";
            return false;
        }

        for (size_t index = 0; index + 2 < indices.size(); ++index)
        {
            const bool oddTriangle = (index & 1) != 0;
            const size_t i0 = oddTriangle ? indices[index + 1] : indices[index];
            const size_t i1 = oddTriangle ? indices[index] : indices[index + 1];
            const size_t i2 = indices[index + 2];

            if (i0 == i1 || i1 == i2 || i2 == i0)
            {
                continue;
            }

            if (!appendPrimitiveTriangleFace(
                    texCoords,
                    hasTexCoord,
                    basePositionIndex,
                    i0,
                    i1,
                    i2,
                    materialName,
                    model,
                    errorMessage))
            {
                return false;
            }
        }
        return true;

    case cgltf_primitive_type_triangle_fan:
        if (indices.size() < 3)
        {
            errorMessage = "glTF triangle fan primitive has fewer than 3 indices";
            return false;
        }

        for (size_t index = 1; index + 1 < indices.size(); ++index)
        {
            if (!appendPrimitiveTriangleFace(
                    texCoords,
                    hasTexCoord,
                    basePositionIndex,
                    indices[0],
                    indices[index],
                    indices[index + 1],
                    materialName,
                    model,
                    errorMessage))
            {
                return false;
            }
        }
        return true;

    default:
        errorMessage = "glTF primitive type is not supported for bmodel import";
        return false;
    }
}

bool appendPrimitiveToImportedModel(
    const std::filesystem::path &path,
    const cgltf_data &data,
    const cgltf_primitive &primitive,
    const float worldTransform[16],
    ImportedModel &model,
    std::string &errorMessage)
{
    const cgltf_accessor *pPositionAccessor = findAttributeAccessor(primitive, cgltf_attribute_type_position);

    if (pPositionAccessor == nullptr)
    {
        errorMessage = "glTF primitive has no POSITION attribute";
        return false;
    }

    if (pPositionAccessor->type != cgltf_type_vec3)
    {
        errorMessage = "glTF POSITION attribute is not vec3";
        return false;
    }

    const cgltf_accessor *pTexCoordAccessor = findAttributeAccessor(primitive, cgltf_attribute_type_texcoord);
    const size_t localVertexCount = pPositionAccessor->count;
    const size_t basePositionIndex = model.positions.size();
    std::vector<std::pair<float, float>> texCoords(localVertexCount);
    std::vector<bool> hasTexCoord(localVertexCount, false);
    model.positions.reserve(model.positions.size() + localVertexCount);

    for (size_t vertexIndex = 0; vertexIndex < localVertexCount; ++vertexIndex)
    {
        float positionValues[3] = {};

        if (!readAccessorFloatComponents(*pPositionAccessor, vertexIndex, 3, positionValues))
        {
            errorMessage = "glTF could not read POSITION attribute";
            return false;
        }

        ImportedModelPosition position = {};

        if (!applyNodeTransform(worldTransform, positionValues[0], positionValues[1], positionValues[2], position))
        {
            errorMessage = "glTF POSITION attribute contains invalid values";
            return false;
        }

        model.positions.push_back(position);

        if (pTexCoordAccessor != nullptr && vertexIndex < pTexCoordAccessor->count)
        {
            float texCoordValues[2] = {};

            if (readAccessorFloatComponents(*pTexCoordAccessor, vertexIndex, 2, texCoordValues))
            {
                texCoords[vertexIndex] = {texCoordValues[0], 1.0f - texCoordValues[1]};
                hasTexCoord[vertexIndex] = true;
            }
        }
    }

    const std::string materialName = composeGltfMaterialName(data, primitive.material);
    appendGltfMaterialToImportedModel(path, data, primitive.material, model);

    return appendPrimitiveFaces(
        primitive,
        texCoords,
        hasTexCoord,
        basePositionIndex,
        localVertexCount,
        materialName,
        model,
        errorMessage);
}

bool appendNodeMeshesToImportedModels(
    const std::filesystem::path &path,
    const cgltf_data &data,
    const cgltf_node &node,
    std::vector<ImportedModel> &models,
    std::string &errorMessage)
{
    float worldTransform[16] = {};
    cgltf_node_transform_world(&node, worldTransform);

    if (node.mesh != nullptr)
    {
        ImportedModel model = {};
        model.name = composeGltfImportedModelName(node);

        for (cgltf_size primitiveIndex = 0; primitiveIndex < node.mesh->primitives_count; ++primitiveIndex)
        {
            if (!appendPrimitiveToImportedModel(
                    path,
                    data,
                    node.mesh->primitives[primitiveIndex],
                    worldTransform,
                    model,
                    errorMessage))
            {
                return false;
            }
        }

        if (!model.positions.empty() && !model.faces.empty())
        {
            models.push_back(std::move(model));
        }
    }

    for (cgltf_size childIndex = 0; childIndex < node.children_count; ++childIndex)
    {
        if (!appendNodeMeshesToImportedModels(path, data, *node.children[childIndex], models, errorMessage))
        {
            return false;
        }
    }

    return true;
}

bool loadGltfModelsFromFile(
    const std::filesystem::path &path,
    std::vector<ImportedModel> &models,
    std::string &errorMessage)
{
    models.clear();
    cgltf_options options = {};
    cgltf_data *pData = nullptr;
    const cgltf_result parseResult = cgltf_parse_file(&options, path.string().c_str(), &pData);

    if (parseResult != cgltf_result_success || pData == nullptr)
    {
        errorMessage = "could not parse glTF file: " + path.string();
        return false;
    }

    const cgltf_result bufferResult = cgltf_load_buffers(&options, pData, path.string().c_str());

    if (bufferResult != cgltf_result_success)
    {
        cgltf_free(pData);
        errorMessage = "could not load glTF buffers: " + path.string();
        return false;
    }

    const cgltf_scene *pScene = pData->scene;

    if (pScene == nullptr && pData->scenes_count > 0)
    {
        pScene = &pData->scenes[0];
    }

    if (pScene != nullptr && pScene->nodes_count > 0)
    {
        for (cgltf_size nodeIndex = 0; nodeIndex < pScene->nodes_count; ++nodeIndex)
        {
            if (!appendNodeMeshesToImportedModels(path, *pData, *pScene->nodes[nodeIndex], models, errorMessage))
            {
                cgltf_free(pData);
                return false;
            }
        }
    }
    else
    {
        for (cgltf_size nodeIndex = 0; nodeIndex < pData->nodes_count; ++nodeIndex)
        {
            if (pData->nodes[nodeIndex].parent != nullptr)
            {
                continue;
            }

            if (!appendNodeMeshesToImportedModels(path, *pData, pData->nodes[nodeIndex], models, errorMessage))
            {
                cgltf_free(pData);
                return false;
            }
        }
    }

    cgltf_free(pData);

    if (models.empty())
    {
        errorMessage = "glTF file contains no mesh geometry: " + path.string();
        return false;
    }

    ensureUniqueImportedModelNames(path, models);
    return true;
}

constexpr float ImportedModelMergePlaneEpsilon = 0.01f;
constexpr float ImportedModelMergeUvEpsilon = 0.0001f;
constexpr float ImportedModelMergeNormalDotThreshold = 0.999f;

struct ImportedModelMergeVector3
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

struct ImportedModelSharedEdgeMatch
{
    size_t faceAEdgeIndex = 0;
    size_t faceBEdgeIndex = 0;
};

struct ImportedModelBoundaryEdge
{
    ImportedModelFaceVertex start = {};
    ImportedModelFaceVertex end = {};
};

ImportedModelMergeVector3 importedModelPositionAt(const ImportedModel &model, size_t index)
{
    const ImportedModelPosition &position = model.positions[index];
    return {position.x, position.y, position.z};
}

ImportedModelMergeVector3 subtractImportedModelVectors(
    const ImportedModelMergeVector3 &lhs,
    const ImportedModelMergeVector3 &rhs)
{
    return {lhs.x - rhs.x, lhs.y - rhs.y, lhs.z - rhs.z};
}

float dotImportedModelVectors(const ImportedModelMergeVector3 &lhs, const ImportedModelMergeVector3 &rhs)
{
    return lhs.x * rhs.x + lhs.y * rhs.y + lhs.z * rhs.z;
}

ImportedModelMergeVector3 crossImportedModelVectors(
    const ImportedModelMergeVector3 &lhs,
    const ImportedModelMergeVector3 &rhs)
{
    return {
        lhs.y * rhs.z - lhs.z * rhs.y,
        lhs.z * rhs.x - lhs.x * rhs.z,
        lhs.x * rhs.y - lhs.y * rhs.x,
    };
}

float lengthImportedModelVector(const ImportedModelMergeVector3 &vector)
{
    return std::sqrt(dotImportedModelVectors(vector, vector));
}

bool normalizeImportedModelVector(ImportedModelMergeVector3 &vector)
{
    const float length = lengthImportedModelVector(vector);

    if (length <= ImportedModelMergePlaneEpsilon)
    {
        return false;
    }

    vector.x /= length;
    vector.y /= length;
    vector.z /= length;
    return true;
}

bool nearlyEqualImportedModelFloat(float lhs, float rhs, float epsilon)
{
    return std::fabs(lhs - rhs) <= epsilon;
}

bool importedFaceVerticesCompatible(const ImportedModelFaceVertex &lhs, const ImportedModelFaceVertex &rhs)
{
    if (lhs.positionIndex != rhs.positionIndex || lhs.hasUv != rhs.hasUv)
    {
        return false;
    }

    if (!lhs.hasUv)
    {
        return true;
    }

    return nearlyEqualImportedModelFloat(lhs.u, rhs.u, ImportedModelMergeUvEpsilon)
        && nearlyEqualImportedModelFloat(lhs.v, rhs.v, ImportedModelMergeUvEpsilon);
}

bool computeImportedTrianglePlane(
    const ImportedModel &model,
    const ImportedModelFace &face,
    ImportedModelMergeVector3 &normal,
    float &planeDistance)
{
    if (face.vertices.size() != 3)
    {
        return false;
    }

    for (const ImportedModelFaceVertex &vertex : face.vertices)
    {
        if (vertex.positionIndex >= model.positions.size())
        {
            return false;
        }
    }

    const ImportedModelMergeVector3 a = importedModelPositionAt(model, face.vertices[0].positionIndex);
    const ImportedModelMergeVector3 b = importedModelPositionAt(model, face.vertices[1].positionIndex);
    const ImportedModelMergeVector3 c = importedModelPositionAt(model, face.vertices[2].positionIndex);
    normal = crossImportedModelVectors(subtractImportedModelVectors(b, a), subtractImportedModelVectors(c, a));

    if (!normalizeImportedModelVector(normal))
    {
        return false;
    }

    planeDistance = dotImportedModelVectors(normal, a);
    return true;
}

bool importedTriangleFaceVerticesAreCoplanar(
    const ImportedModel &model,
    const ImportedModelFace &face,
    const ImportedModelMergeVector3 &normal,
    float planeDistance)
{
    for (const ImportedModelFaceVertex &vertex : face.vertices)
    {
        if (vertex.positionIndex >= model.positions.size())
        {
            return false;
        }

        const ImportedModelMergeVector3 position = importedModelPositionAt(model, vertex.positionIndex);

        if (!nearlyEqualImportedModelFloat(
                dotImportedModelVectors(normal, position),
                planeDistance,
                ImportedModelMergePlaneEpsilon))
        {
            return false;
        }
    }

    return true;
}

bool importedTrianglePlanesAreCompatible(
    const ImportedModel &model,
    const ImportedModelFace &faceA,
    const ImportedModelFace &faceB)
{
    if (faceA.materialName != faceB.materialName)
    {
        return false;
    }

    ImportedModelMergeVector3 normalA = {};
    ImportedModelMergeVector3 normalB = {};
    float planeDistanceA = 0.0f;
    float planeDistanceB = 0.0f;

    if (!computeImportedTrianglePlane(model, faceA, normalA, planeDistanceA)
        || !computeImportedTrianglePlane(model, faceB, normalB, planeDistanceB))
    {
        return false;
    }

    if (dotImportedModelVectors(normalA, normalB) < ImportedModelMergeNormalDotThreshold)
    {
        return false;
    }

    return importedTriangleFaceVerticesAreCoplanar(model, faceA, normalA, planeDistanceA)
        && importedTriangleFaceVerticesAreCoplanar(model, faceB, normalA, planeDistanceA)
        && importedTriangleFaceVerticesAreCoplanar(model, faceA, normalB, planeDistanceB)
        && importedTriangleFaceVerticesAreCoplanar(model, faceB, normalB, planeDistanceB);
}

bool findSharedImportedTriangleEdge(
    const ImportedModelFace &faceA,
    const ImportedModelFace &faceB,
    ImportedModelSharedEdgeMatch &match)
{
    bool found = false;

    for (size_t edgeIndexA = 0; edgeIndexA < faceA.vertices.size(); ++edgeIndexA)
    {
        const ImportedModelFaceVertex &startA = faceA.vertices[edgeIndexA];
        const ImportedModelFaceVertex &endA = faceA.vertices[(edgeIndexA + 1) % faceA.vertices.size()];

        for (size_t edgeIndexB = 0; edgeIndexB < faceB.vertices.size(); ++edgeIndexB)
        {
            const ImportedModelFaceVertex &startB = faceB.vertices[edgeIndexB];
            const ImportedModelFaceVertex &endB = faceB.vertices[(edgeIndexB + 1) % faceB.vertices.size()];

            if (!importedFaceVerticesCompatible(startA, endB)
                || !importedFaceVerticesCompatible(endA, startB))
            {
                continue;
            }

            if (found)
            {
                return false;
            }

            match.faceAEdgeIndex = edgeIndexA;
            match.faceBEdgeIndex = edgeIndexB;
            found = true;
        }
    }

    return found;
}

bool buildMergedQuadBoundary(
    const ImportedModelFace &faceA,
    const ImportedModelFace &faceB,
    const ImportedModelSharedEdgeMatch &sharedEdge,
    std::vector<ImportedModelBoundaryEdge> &orderedEdges)
{
    std::vector<ImportedModelBoundaryEdge> boundaryEdges;
    boundaryEdges.reserve(4);

    for (size_t edgeIndex = 0; edgeIndex < faceA.vertices.size(); ++edgeIndex)
    {
        if (edgeIndex == sharedEdge.faceAEdgeIndex)
        {
            continue;
        }

        boundaryEdges.push_back({
            faceA.vertices[edgeIndex],
            faceA.vertices[(edgeIndex + 1) % faceA.vertices.size()]
        });
    }

    for (size_t edgeIndex = 0; edgeIndex < faceB.vertices.size(); ++edgeIndex)
    {
        if (edgeIndex == sharedEdge.faceBEdgeIndex)
        {
            continue;
        }

        boundaryEdges.push_back({
            faceB.vertices[edgeIndex],
            faceB.vertices[(edgeIndex + 1) % faceB.vertices.size()]
        });
    }

    if (boundaryEdges.size() != 4)
    {
        return false;
    }

    orderedEdges.clear();
    orderedEdges.reserve(boundaryEdges.size());
    std::vector<bool> usedEdges(boundaryEdges.size(), false);
    orderedEdges.push_back(boundaryEdges[0]);
    usedEdges[0] = true;

    while (orderedEdges.size() < boundaryEdges.size())
    {
        const ImportedModelFaceVertex currentVertex = orderedEdges.back().end;
        size_t nextEdgeIndex = boundaryEdges.size();

        for (size_t candidateIndex = 0; candidateIndex < boundaryEdges.size(); ++candidateIndex)
        {
            if (usedEdges[candidateIndex])
            {
                continue;
            }

            if (!importedFaceVerticesCompatible(currentVertex, boundaryEdges[candidateIndex].start))
            {
                continue;
            }

            if (nextEdgeIndex != boundaryEdges.size())
            {
                return false;
            }

            nextEdgeIndex = candidateIndex;
        }

        if (nextEdgeIndex == boundaryEdges.size())
        {
            return false;
        }

        orderedEdges.push_back(boundaryEdges[nextEdgeIndex]);
        usedEdges[nextEdgeIndex] = true;
    }

    return importedFaceVerticesCompatible(orderedEdges.back().end, orderedEdges.front().start);
}

bool isConvexImportedQuad(const ImportedModel &model, const ImportedModelFace &face)
{
    if (face.vertices.size() != 4)
    {
        return false;
    }

    ImportedModelFace triangleFace = {};
    triangleFace.materialName = face.materialName;
    triangleFace.vertices = {face.vertices[0], face.vertices[1], face.vertices[2]};
    ImportedModelMergeVector3 normal = {};
    float planeDistance = 0.0f;

    if (!computeImportedTrianglePlane(model, triangleFace, normal, planeDistance))
    {
        return false;
    }

    ImportedModelMergeVector3 axis = std::fabs(normal.z) < 0.9f
        ? ImportedModelMergeVector3 {0.0f, 0.0f, 1.0f}
        : ImportedModelMergeVector3 {0.0f, 1.0f, 0.0f};
    ImportedModelMergeVector3 tangent = crossImportedModelVectors(axis, normal);

    if (!normalizeImportedModelVector(tangent))
    {
        axis = ImportedModelMergeVector3 {1.0f, 0.0f, 0.0f};
        tangent = crossImportedModelVectors(axis, normal);

        if (!normalizeImportedModelVector(tangent))
        {
            return false;
        }
    }

    const ImportedModelMergeVector3 bitangent = crossImportedModelVectors(normal, tangent);
    float sign = 0.0f;

    for (size_t index = 0; index < face.vertices.size(); ++index)
    {
        const ImportedModelMergeVector3 previous = importedModelPositionAt(
            model,
            face.vertices[(index + face.vertices.size() - 1) % face.vertices.size()].positionIndex);
        const ImportedModelMergeVector3 current = importedModelPositionAt(model, face.vertices[index].positionIndex);
        const ImportedModelMergeVector3 next = importedModelPositionAt(
            model,
            face.vertices[(index + 1) % face.vertices.size()].positionIndex);
        const float previousU = dotImportedModelVectors(previous, tangent);
        const float previousV = dotImportedModelVectors(previous, bitangent);
        const float currentU = dotImportedModelVectors(current, tangent);
        const float currentV = dotImportedModelVectors(current, bitangent);
        const float nextU = dotImportedModelVectors(next, tangent);
        const float nextV = dotImportedModelVectors(next, bitangent);
        const float crossZ = (currentU - previousU) * (nextV - currentV)
            - (currentV - previousV) * (nextU - currentU);

        if (std::fabs(crossZ) <= ImportedModelMergePlaneEpsilon)
        {
            continue;
        }

        if (sign == 0.0f)
        {
            sign = crossZ;
            continue;
        }

        if ((crossZ > 0.0f) != (sign > 0.0f))
        {
            return false;
        }
    }

    return sign != 0.0f;
}

bool tryMergeImportedTriangleFaces(
    const ImportedModel &model,
    const ImportedModelFace &faceA,
    const ImportedModelFace &faceB,
    ImportedModelFace &mergedFace)
{
    if (faceA.vertices.size() != 3 || faceB.vertices.size() != 3)
    {
        return false;
    }

    if (!importedTrianglePlanesAreCompatible(model, faceA, faceB))
    {
        return false;
    }

    ImportedModelSharedEdgeMatch sharedEdge = {};

    if (!findSharedImportedTriangleEdge(faceA, faceB, sharedEdge))
    {
        return false;
    }

    std::vector<ImportedModelBoundaryEdge> orderedEdges;

    if (!buildMergedQuadBoundary(faceA, faceB, sharedEdge, orderedEdges))
    {
        return false;
    }

    mergedFace = {};
    mergedFace.materialName = faceA.materialName;
    mergedFace.vertices.reserve(4);

    for (const ImportedModelBoundaryEdge &edge : orderedEdges)
    {
        mergedFace.vertices.push_back(edge.start);
    }

    if (mergedFace.vertices.size() != 4)
    {
        return false;
    }

    std::unordered_set<size_t> uniquePositions;

    for (const ImportedModelFaceVertex &vertex : mergedFace.vertices)
    {
        uniquePositions.insert(vertex.positionIndex);
    }

    if (uniquePositions.size() != 4)
    {
        return false;
    }

    const size_t sharedPositionA = faceA.vertices[sharedEdge.faceAEdgeIndex].positionIndex;
    const size_t sharedPositionB = faceA.vertices[(sharedEdge.faceAEdgeIndex + 1) % faceA.vertices.size()].positionIndex;
    bool diagonalPreserved = false;

    for (size_t rotation = 0; rotation < mergedFace.vertices.size(); ++rotation)
    {
        const size_t diagonalStart = mergedFace.vertices[0].positionIndex;
        const size_t diagonalEnd = mergedFace.vertices[2].positionIndex;

        if ((diagonalStart == sharedPositionA && diagonalEnd == sharedPositionB)
            || (diagonalStart == sharedPositionB && diagonalEnd == sharedPositionA))
        {
            diagonalPreserved = true;
            break;
        }

        std::rotate(mergedFace.vertices.begin(), mergedFace.vertices.begin() + 1, mergedFace.vertices.end());
    }

    return diagonalPreserved && isConvexImportedQuad(model, mergedFace);
}

void mergeImportedModelCoplanarFaces(ImportedModel &model)
{
    if (model.faces.size() < 2)
    {
        return;
    }

    bool merged = true;

    while (merged)
    {
        merged = false;

        for (size_t faceIndexA = 0; faceIndexA < model.faces.size() && !merged; ++faceIndexA)
        {
            for (size_t faceIndexB = faceIndexA + 1; faceIndexB < model.faces.size(); ++faceIndexB)
            {
                ImportedModelFace mergedFace = {};

                if (!tryMergeImportedTriangleFaces(model, model.faces[faceIndexA], model.faces[faceIndexB], mergedFace))
                {
                    continue;
                }

                model.faces[faceIndexA] = std::move(mergedFace);
                model.faces.erase(model.faces.begin() + faceIndexB);
                merged = true;
                break;
            }
        }
    }
}

}

bool loadImportedModelsFromFile(
    const std::filesystem::path &path,
    std::vector<ImportedModel> &models,
    std::string &errorMessage,
    bool mergeCoplanarFaces)
{
    switch (importedModelFileTypeFromPath(path))
    {
    case ImportedModelFileType::Obj:
    {
        ImportedModel model = {};

        if (!loadObjModelFromFile(path, model, errorMessage))
        {
            return false;
        }

        models.clear();
        models.push_back(std::move(model));
        ensureUniqueImportedModelNames(path, models);

        if (mergeCoplanarFaces)
        {
            for (ImportedModel &loadedModel : models)
            {
                mergeImportedModelCoplanarFaces(loadedModel);
            }
        }

        return true;
    }

    case ImportedModelFileType::Gltf:
    case ImportedModelFileType::Glb:
        if (!loadGltfModelsFromFile(path, models, errorMessage))
        {
            return false;
        }

        if (mergeCoplanarFaces)
        {
            for (ImportedModel &loadedModel : models)
            {
                mergeImportedModelCoplanarFaces(loadedModel);
            }
        }

        return true;
    }

    errorMessage = "unsupported model format: " + path.string();
    return false;
}

bool loadObjModelFromFile(
    const std::filesystem::path &path,
    ImportedModel &model,
    std::string &errorMessage)
{
    std::ifstream input(path);

    if (!input)
    {
        errorMessage = "could not open OBJ file: " + path.string();
        return false;
    }

    model = {};
    std::vector<std::pair<float, float>> texCoords;
    std::string activeMaterialName;
    std::string line;
    size_t lineNumber = 0;

    while (std::getline(input, line))
    {
        ++lineNumber;
        const std::string trimmedLine = trimCopy(removeComment(line));

        if (trimmedLine.empty())
        {
            continue;
        }

        std::istringstream lineStream(trimmedLine);
        std::string keyword;
        lineStream >> keyword;

        if (keyword == "v")
        {
            std::string xText;
            std::string yText;
            std::string zText;

            if (!(lineStream >> xText >> yText >> zText))
            {
                errorMessage = "OBJ line " + std::to_string(lineNumber) + ": malformed vertex";
                return false;
            }

            ImportedModelPosition position = {};

            if (!parseFloatToken(xText, position.x)
                || !parseFloatToken(yText, position.y)
                || !parseFloatToken(zText, position.z))
            {
                errorMessage = "OBJ line " + std::to_string(lineNumber) + ": invalid vertex coordinates";
                return false;
            }

            model.positions.push_back(position);
            continue;
        }

        if (keyword == "vt")
        {
            std::string uText;
            std::string vText;

            if (!(lineStream >> uText >> vText))
            {
                errorMessage = "OBJ line " + std::to_string(lineNumber) + ": malformed texture coordinate";
                return false;
            }

            float u = 0.0f;
            float v = 0.0f;

            if (!parseFloatToken(uText, u) || !parseFloatToken(vText, v))
            {
                errorMessage = "OBJ line " + std::to_string(lineNumber) + ": invalid texture coordinates";
                return false;
            }

            texCoords.emplace_back(u, v);
            continue;
        }

        if (keyword == "usemtl")
        {
            std::getline(lineStream, activeMaterialName);
            activeMaterialName = trimCopy(activeMaterialName);
            continue;
        }

        if (keyword == "o" || keyword == "g")
        {
            if (model.name.empty())
            {
                std::string objectName;
                std::getline(lineStream, objectName);
                model.name = trimCopy(objectName);
            }

            continue;
        }

        if (keyword == "f")
        {
            ImportedModelFace face = {};
            face.materialName = activeMaterialName;
            std::string token;

            while (lineStream >> token)
            {
                ImportedModelFaceVertex faceVertex = {};

                if (!parseFaceVertexToken(token, model.positions.size(), texCoords, faceVertex, errorMessage))
                {
                    errorMessage = "OBJ line " + std::to_string(lineNumber) + ": " + errorMessage;
                    return false;
                }

                face.vertices.push_back(faceVertex);
            }

            if (face.vertices.size() < 3)
            {
                errorMessage = "OBJ line " + std::to_string(lineNumber) + ": face has fewer than 3 vertices";
                return false;
            }

            if (face.vertices.size() > 20)
            {
                errorMessage = "OBJ line " + std::to_string(lineNumber) + ": face exceeds ODM limit of 20 vertices";
                return false;
            }

            model.faces.push_back(std::move(face));
        }
    }

    if (model.name.empty())
    {
        model.name = path.stem().string();
    }

    if (model.positions.empty())
    {
        errorMessage = "OBJ file contains no vertices: " + path.string();
        return false;
    }

    if (model.faces.empty())
    {
        errorMessage = "OBJ file contains no faces: " + path.string();
        return false;
    }

    return true;
}

bool loadImportedModelFromFile(
    const std::filesystem::path &path,
    ImportedModel &model,
    std::string &errorMessage,
    const std::string &sourceMeshName,
    bool mergeCoplanarFaces)
{
    std::vector<ImportedModel> models;

    if (!loadImportedModelsFromFile(path, models, errorMessage, mergeCoplanarFaces))
    {
        return false;
    }

    return selectImportedModelByName(path, models, sourceMeshName, model, errorMessage);
}
}
