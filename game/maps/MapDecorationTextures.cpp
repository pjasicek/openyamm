#include "game/maps/MapDecorationTextures.h"
#include "engine/ImageAssetLoader.h"
#include "game/StringUtils.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <set>
#include <stdexcept>

namespace OpenYAMM::Game
{
namespace
{
bool isFileComponent(const std::string &name)
{
    return !name.empty() && name != "." && name.find("..") == std::string::npos
        && name.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_.-") == std::string::npos;
}
}

std::optional<std::vector<MapDecorationTexture>> parseMapDecorationTextures(
    const std::string &yaml, std::string &error)
{
    error.clear();
    try
    {
        const YAML::Node root = YAML::Load(yaml);
        if (root["schema_version"].as<int>() != 1 || !root["textures"].IsSequence())
        {
            throw std::runtime_error("Expected decoration texture schema_version 1 and textures sequence");
        }
        std::vector<MapDecorationTexture> textures;
        std::set<std::pair<std::string, int16_t>> keys;
        for (const YAML::Node &node : root["textures"])
        {
            MapDecorationTexture texture;
            texture.name = node["name"].as<std::string>();
            texture.file = node["file"].as<std::string>();
            texture.paletteId = node["palette_id"].as<int16_t>();
            texture.pixelScale = node["pixel_scale"].as<int>();
            const YAML::Node size = node["logical_size"];
            if (!size.IsSequence() || size.size() != 2)
            {
                throw std::runtime_error("Expected logical_size: [width, height]");
            }
            texture.width = size[0].as<int>();
            texture.height = size[1].as<int>();
            if (!isFileComponent(texture.name) || !isFileComponent(texture.file)
                || !texture.file.ends_with(".png") || texture.paletteId < 0
                || texture.pixelScale < 1 || texture.pixelScale > 4
                || texture.width < 1 || texture.width > 8192 / texture.pixelScale
                || texture.height < 1 || texture.height > 8192 / texture.pixelScale
                || !keys.emplace(texture.name, texture.paletteId).second)
            {
                throw std::runtime_error("Invalid or duplicate decoration texture: " + texture.name);
            }
            textures.push_back(std::move(texture));
        }
        return textures;
    }
    catch (const std::exception &exception)
    {
        error = exception.what();
        return std::nullopt;
    }
}

std::optional<std::vector<OutdoorBitmapTexture>> loadMapDecorationTextures(
    const Engine::AssetFileSystem &assets, const std::string &worldId, const std::string &mapFile,
    std::string &error)
{
    error.clear();
    const std::string world = toLowerCopy(worldId);
    const std::string map = toLowerCopy(mapFile);
    // Legacy unscoped maps have no world-local presentation package.
    if (world.empty())
    {
        return std::vector<OutdoorBitmapTexture>();
    }
    if (!isFileComponent(world) || !isFileComponent(map))
    {
        error = "Invalid world/map decoration texture scope";
        return std::nullopt;
    }
    const std::string directory = "worlds/" + world + "/rendering/decoration_overrides/" + map + "/";
    const std::string path = directory + "manifest.yml";
    if (!assets.exists(path))
    {
        return std::vector<OutdoorBitmapTexture>();
    }
    const std::optional<std::string> text = assets.readTextFile(path);
    if (!text)
    {
        error = "Cannot read " + path;
        return std::nullopt;
    }
    const std::optional<std::vector<MapDecorationTexture>> entries = parseMapDecorationTextures(*text, error);
    if (!entries)
    {
        error = path + ": " + error;
        return std::nullopt;
    }
    std::vector<OutdoorBitmapTexture> textures;
    for (const MapDecorationTexture &entry : *entries)
    {
        const std::string imagePath = directory + entry.file;
        const std::optional<std::vector<uint8_t>> bytes = assets.readBinaryFile(imagePath);
        // These are final RGBA images: no native indexed palette or color key applies.
        const std::optional<Engine::ImagePixelsBgra> image = bytes
            ? Engine::decodeImagePixelsBgra(*bytes, imagePath) : std::nullopt;
        if (!image || image->width != entry.width * entry.pixelScale
            || image->height != entry.height * entry.pixelScale)
        {
            error = "Missing, invalid or incorrectly sized decoration PNG: " + imagePath;
            return std::nullopt;
        }
        OutdoorBitmapTexture texture;
        texture.textureName = entry.name;
        texture.resourceIdentity = imagePath;
        texture.paletteId = entry.paletteId;
        texture.width = entry.width;
        texture.height = entry.height;
        texture.physicalWidth = image->width;
        texture.physicalHeight = image->height;
        texture.pixels = image->pixels;
        for (size_t i = 3; i < texture.pixels.size(); i += 4)
        {
            const uint8_t alpha = texture.pixels[i];
            texture.hasTransparentPixels |= alpha < 255;
            texture.hasPartialAlphaPixels |= alpha > 0 && alpha < 255;
        }
        textures.push_back(std::move(texture));
    }
    return textures;
}
}
