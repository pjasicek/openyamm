#include "editor/import/ObjModelImport.h"

#include <algorithm>
#include <charconv>
#include <cctype>
#include <fstream>
#include <sstream>

namespace OpenYAMM::Editor
{
namespace
{
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
    ImportedObjFaceVertex &vertex,
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
}

bool loadObjModelFromFile(
    const std::filesystem::path &path,
    ImportedObjModel &model,
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

            ImportedObjPosition position = {};

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
            ImportedObjFace face = {};
            face.materialName = activeMaterialName;
            std::string token;

            while (lineStream >> token)
            {
                ImportedObjFaceVertex faceVertex = {};

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
}
