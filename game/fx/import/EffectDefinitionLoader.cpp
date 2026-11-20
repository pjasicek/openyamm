#include "game/fx/import/EffectDefinitionLoader.h"

#include "engine/AssetFileSystem.h"
#include "game/fx/EffectSystem.h"

#include <yaml-cpp/yaml.h>

#include <array>
#include <exception>
#include <functional>
#include <unordered_set>
#include <unordered_map>

namespace OpenYAMM::Game
{
namespace
{
template <typename Value>
bool readRequired(const YAML::Node &node, const char *pName, Value &value, std::string &error)
{
    const YAML::Node valueNode = node[pName];
    if (!valueNode || !valueNode.IsScalar())
    {
        error = std::string("missing scalar field '") + pName + "'";
        return false;
    }
    try
    {
        value = valueNode.as<Value>();
        return true;
    }
    catch (const YAML::Exception &exception)
    {
        error = std::string("invalid field '") + pName + "': " + exception.what();
        return false;
    }
}

template <typename Value>
bool readOptional(const YAML::Node &node, const char *pName, Value &value, std::string &error)
{
    if (!node[pName])
    {
        return true;
    }
    return readRequired(node, pName, value, error);
}

bool readVector(const YAML::Node &node, const char *pName, std::array<float, 3> &value, std::string &error)
{
    const YAML::Node valueNode = node[pName];
    if (!valueNode || !valueNode.IsSequence() || valueNode.size() != value.size())
    {
        error = std::string("field '") + pName + "' must be a three-number sequence";
        return false;
    }
    try
    {
        for (size_t index = 0; index < value.size(); ++index)
        {
            value[index] = valueNode[index].as<float>();
        }
        return true;
    }
    catch (const YAML::Exception &exception)
    {
        error = std::string("invalid vector field '") + pName + "': " + exception.what();
        return false;
    }
}

bool readOptionalVector(
    const YAML::Node &node,
    const char *pName,
    std::array<float, 3> &value,
    std::string &error)
{
    return !node[pName] || readVector(node, pName, value, error);
}

bool parseLink(const YAML::Node &node, EffectComponentLink &link, std::string &error)
{
    if (!node["linked_component_id"])
    {
        return true;
    }
    uint32_t componentId = 0;
    if (!readRequired(node, "linked_component_id", componentId, error) ||
        !readRequired(node, "linked_node", link.nodeName, error) || link.nodeName.empty())
    {
        if (error.empty())
        {
            error = "linked component requires a non-empty linked_node";
        }
        return false;
    }
    link.componentId = componentId;
    return true;
}

bool parseColorKeys(const YAML::Node &node, std::vector<EffectColorKey> &keys, std::string &error)
{
    if (!node || !node.IsSequence())
    {
        error = "field 'color_keys' must be a sequence";
        return false;
    }
    for (const YAML::Node &keyNode : node)
    {
        EffectColorKey key;
        std::array<uint32_t, 3> rgb = {};
        uint32_t transparency = 0;
        const YAML::Node rgbNode = keyNode["rgb"];
        if (!readRequired(keyNode, "time", key.time, error) || !rgbNode || !rgbNode.IsSequence() ||
            rgbNode.size() != rgb.size() || !readRequired(keyNode, "transparency", transparency, error))
        {
            if (error.empty())
            {
                error = "field 'rgb' must be a three-integer sequence";
            }
            return false;
        }
        try
        {
            for (size_t index = 0; index < rgb.size(); ++index)
            {
                rgb[index] = rgbNode[index].as<uint32_t>();
                if (rgb[index] > 255 || transparency > 255)
                {
                    error = "color channels must be in [0, 255]";
                    return false;
                }
                key.rgb[index] = static_cast<uint8_t>(rgb[index]);
            }
            key.transparency = static_cast<uint8_t>(transparency);
        }
        catch (const YAML::Exception &exception)
        {
            error = std::string("invalid color key: ") + exception.what();
            return false;
        }
        keys.push_back(key);
    }
    return true;
}

bool parseScaleKeys(const YAML::Node &node, std::vector<EffectScalarKey> &keys, std::string &error)
{
    if (!node || !node.IsSequence())
    {
        error = "field 'scale_keys' must be a sequence";
        return false;
    }
    for (const YAML::Node &keyNode : node)
    {
        EffectScalarKey key;
        if (!readRequired(keyNode, "time", key.time, error) ||
            !readRequired(keyNode, "value", key.value, error))
        {
            return false;
        }
        keys.push_back(key);
    }
    return true;
}

bool parseMotionKeys(const YAML::Node &node, std::vector<EffectVectorKey> &keys, std::string &error)
{
    if (!node || !node.IsSequence())
    {
        error = "field 'motion_keys' must be a sequence";
        return false;
    }
    for (const YAML::Node &keyNode : node)
    {
        EffectVectorKey key;
        if (!readRequired(keyNode, "time", key.time, error) ||
            !readVector(keyNode, "value", key.value, error))
        {
            return false;
        }
        keys.push_back(key);
    }
    return true;
}

bool parseSpriteOrientation(
    const YAML::Node &node,
    EffectSpriteAlignment &alignment,
    std::array<float, 3> &planeRight,
    std::array<float, 3> &planeUp,
    std::string &error)
{
    std::string alignmentName = "camera_facing";
    if (!readOptional(node, "alignment", alignmentName, error))
    {
        return false;
    }
    if (alignmentName == "camera_facing")
    {
        alignment = EffectSpriteAlignment::CameraFacing;
        return true;
    }
    if (alignmentName == "velocity")
    {
        alignment = EffectSpriteAlignment::Velocity;
        return true;
    }
    if (alignmentName != "world_plane")
    {
        error = "sprite component has an unknown alignment value";
        return false;
    }
    alignment = EffectSpriteAlignment::WorldPlane;
    return readVector(node, "plane_right", planeRight, error) &&
        readVector(node, "plane_up", planeUp, error);
}

bool parseEmitter(const YAML::Node &node, EffectSpriteEmitterDefinition &emitter, std::string &error)
{
    std::string emissionShape;
    std::string blendMode = "alpha";
    std::string particleSpace = "world";
    if (!readRequired(node, "id", emitter.componentId, error) ||
        !readRequired(node, "start_seconds", emitter.startSeconds, error) ||
        !readRequired(node, "end_seconds", emitter.endSeconds, error) ||
        !readRequired(node, "sprite_resource", emitter.spriteResource, error) ||
        !readRequired(node, "emission_shape", emissionShape, error) ||
        !readOptional(node, "repeat_count", emitter.repeatCount, error) ||
        !readOptional(node, "sprites_per_emission", emitter.spritesPerEmission, error) ||
        !readOptional(node, "emission_interval_seconds", emitter.emissionIntervalSeconds, error) ||
        !readOptional(node, "emission_distance", emitter.emissionDistance, error) ||
        !readOptional(node, "random_roll", emitter.randomRoll, error) ||
        !readOptional(node, "spin_speed", emitter.spinSpeed, error) ||
        !readOptional(node, "particle_lifetime_seconds", emitter.particleLifetimeSeconds, error) ||
        !readOptional(node, "radius", emitter.radius, error) ||
        !readOptionalVector(node, "plane_direction", emitter.planeDirection, error) ||
        !readOptional(node, "velocity", emitter.velocity, error) ||
        !readOptionalVector(node, "wind_direction", emitter.windDirection, error) ||
        !readOptional(node, "wind_amount", emitter.windAmount, error) ||
        !readOptional(node, "gravity", emitter.gravity, error) ||
        !readOptionalVector(node, "offset", emitter.offset, error) ||
        !readOptionalVector(node, "rotation_per_tick", emitter.rotationPerTick, error) ||
        !readOptional(node, "stretch_u", emitter.stretchU, error) ||
        !readOptional(node, "stretch_v", emitter.stretchV, error) ||
        !readOptional(node, "blend", blendMode, error) ||
        !readOptional(node, "additive_texture_alpha", emitter.additiveTextureAlpha, error) ||
        !readOptional(node, "particle_space", particleSpace, error) ||
        !readOptional(node, "body_anchor", emitter.bodyAnchor, error) ||
        !parseSpriteOrientation(node, emitter.alignment, emitter.planeRight, emitter.planeUp, error) ||
        !parseLink(node, emitter.link, error) ||
        !parseColorKeys(node["color_keys"], emitter.colorKeys, error) ||
        !parseScaleKeys(node["scale_keys"], emitter.scaleKeys, error) ||
        !parseMotionKeys(node["motion_keys"], emitter.motionKeys, error))
    {
        return false;
    }

    static const std::unordered_map<std::string, EffectEmissionShape> EmissionShapes = {
        {"point", EffectEmissionShape::Point},
        {"plane", EffectEmissionShape::Plane},
        {"sphere", EffectEmissionShape::Sphere},
        {"plane_in", EffectEmissionShape::PlaneIn},
        {"plane_out", EffectEmissionShape::PlaneOut},
        {"cone", EffectEmissionShape::Cone},
        {"circle", EffectEmissionShape::Circle},
    };
    static const std::unordered_map<std::string, EffectBlendMode> BlendModes = {
        {"alpha", EffectBlendMode::Alpha},
        {"additive", EffectBlendMode::Additive},
        {"multiply", EffectBlendMode::Multiply},
    };
    const auto shapeIterator = EmissionShapes.find(emissionShape);
    const auto blendIterator = BlendModes.find(blendMode);
    if (shapeIterator == EmissionShapes.end() || blendIterator == BlendModes.end() ||
        (particleSpace != "world" && particleSpace != "local"))
    {
        error = "sprite component has an unknown emission_shape, blend, or particle_space value";
        return false;
    }
    emitter.emissionShape = shapeIterator->second;
    emitter.blendMode = blendIterator->second;
    emitter.particleSpace = particleSpace == "local" ? EffectParticleSpace::Local : EffectParticleSpace::World;
    return true;
}

bool parseModel(const YAML::Node &node, EffectModelDefinition &model, std::string &error)
{
    return readRequired(node, "id", model.componentId, error) &&
        readRequired(node, "start_seconds", model.startSeconds, error) &&
        readRequired(node, "end_seconds", model.endSeconds, error) &&
        readRequired(node, "model_resource", model.modelResource, error) &&
        readRequired(node, "animation_clip", model.animationClip, error) &&
        readOptional(node, "repeat_count", model.repeatCount, error) &&
        readOptionalVector(node, "offset", model.offset, error) &&
        readOptional(node, "visible", model.visible, error) &&
        parseLink(node, model.link, error);
}

bool parseNull(const YAML::Node &node, EffectNullDefinition &null, std::string &error)
{
    return readRequired(node, "id", null.componentId, error) &&
        readRequired(node, "start_seconds", null.startSeconds, error) &&
        readRequired(node, "end_seconds", null.endSeconds, error) &&
        readOptional(node, "repeat_count", null.repeatCount, error) &&
        readOptionalVector(node, "offset", null.offset, error) &&
        readOptionalVector(node, "rotation_per_tick", null.rotationPerTick, error) &&
        parseLink(node, null.link, error) &&
        parseScaleKeys(node["scale_keys"], null.scaleKeys, error) &&
        parseMotionKeys(node["motion_keys"], null.motionKeys, error);
}

bool parseSprite(const YAML::Node &node, EffectSpriteDefinition &sprite, std::string &error)
{
    std::string blendMode = "additive";
    if (!readRequired(node, "id", sprite.componentId, error) ||
        !readRequired(node, "start_seconds", sprite.startSeconds, error) ||
        !readRequired(node, "end_seconds", sprite.endSeconds, error) ||
        !readRequired(node, "sprite_resource", sprite.spriteResource, error) ||
        !readOptional(node, "repeat_count", sprite.repeatCount, error) ||
        !readOptionalVector(node, "offset", sprite.offset, error) ||
        !readOptional(node, "stretch_u", sprite.stretchU, error) ||
        !readOptional(node, "stretch_v", sprite.stretchV, error) ||
        !readOptional(node, "blend", blendMode, error) ||
        !readOptional(node, "additive_texture_alpha", sprite.additiveTextureAlpha, error) ||
        !parseSpriteOrientation(node, sprite.alignment, sprite.planeRight, sprite.planeUp, error) ||
        !parseLink(node, sprite.link, error) ||
        !parseColorKeys(node["color_keys"], sprite.colorKeys, error) ||
        !parseScaleKeys(node["scale_keys"], sprite.scaleKeys, error) ||
        !parseMotionKeys(node["motion_keys"], sprite.motionKeys, error))
    {
        return false;
    }
    if (blendMode == "alpha")
    {
        sprite.blendMode = EffectBlendMode::Alpha;
    }
    else if (blendMode == "additive")
    {
        sprite.blendMode = EffectBlendMode::Additive;
    }
    else if (blendMode == "multiply")
    {
        sprite.blendMode = EffectBlendMode::Multiply;
    }
    else
    {
        error = "sprite component has an unknown blend value";
        return false;
    }
    return true;
}

bool parseRibbon(const YAML::Node &node, EffectRibbonDefinition &ribbon, std::string &error)
{
    std::string blendMode = "additive";
    if (!readRequired(node, "id", ribbon.componentId, error) ||
        !readRequired(node, "start_seconds", ribbon.startSeconds, error) ||
        !readRequired(node, "end_seconds", ribbon.endSeconds, error) ||
        !readRequired(node, "sprite_resource", ribbon.spriteResource, error) ||
        !readRequired(node, "lifetime_seconds", ribbon.lifetimeSeconds, error) ||
        !readRequired(node, "width", ribbon.width, error) ||
        !readOptional(node, "blend", blendMode, error) ||
        !readOptionalVector(node, "offset", ribbon.offset, error) ||
        !readOptional(node, "max_length", ribbon.maxLength, error) ||
        !readOptional(node, "sample_distance", ribbon.sampleDistance, error) ||
        !readOptional(node, "texture_length", ribbon.textureLength, error) ||
        !readOptional(node, "scroll_speed", ribbon.scrollSpeed, error) ||
        !readOptional(node, "fill", ribbon.fill, error) ||
        !readOptional(node, "erosion", ribbon.erosion, error) ||
        !readOptional(node, "core", ribbon.core, error) ||
        !readOptional(node, "jitter", ribbon.jitter, error) ||
        !readOptional(node, "jitter_rate", ribbon.jitterRate, error) ||
        !readOptional(node, "beam", ribbon.beam, error) ||
        !parseScaleKeys(node["width_keys"], ribbon.widthKeys, error) ||
        !parseColorKeys(node["color_keys"], ribbon.colorKeys, error))
    {
        return false;
    }
    if (blendMode == "additive")
    {
        ribbon.blendMode = EffectBlendMode::Additive;
    }
    else if (blendMode == "alpha")
    {
        ribbon.blendMode = EffectBlendMode::Alpha;
    }
    else
    {
        error = "ribbon component blend must be additive or alpha";
        return false;
    }
    return true;
}

bool parseSound(const YAML::Node &node, EffectSoundDefinition &sound, std::string &error)
{
    return readRequired(node, "id", sound.componentId, error) &&
        readRequired(node, "start_seconds", sound.startSeconds, error) &&
        readRequired(node, "end_seconds", sound.endSeconds, error) &&
        readRequired(node, "sound_resource", sound.soundResource, error) &&
        readOptional(node, "spatial", sound.spatial, error) &&
        readOptional(node, "loop", sound.loop, error) &&
        readOptional(node, "volume", sound.volume, error) &&
        readOptional(node, "pitch", sound.pitch, error) &&
        readOptional(node, "inner_radius", sound.innerRadius, error) &&
        readOptional(node, "outer_radius", sound.outerRadius, error) &&
        readOptional(node, "follows_emitter", sound.followsEmitter, error);
}

std::shared_ptr<EffectDefinition> parseDefinition(const YAML::Node &node, std::string &error)
{
    std::shared_ptr<EffectDefinition> definition = std::make_shared<EffectDefinition>();
    std::string compatibilityProfile;
    if (!node.IsMap() || !readRequired(node, "id", definition->id, error) ||
        !readRequired(node, "duration_seconds", definition->durationSeconds, error) ||
        !readRequired(node, "compatibility_profile", compatibilityProfile, error))
    {
        return nullptr;
    }
    if (compatibilityProfile == "predictable")
    {
        definition->timingProfile = EffectTimingProfile::Predictable;
    }
    else if (compatibilityProfile == "mm9_native_60hz")
    {
        definition->timingProfile = EffectTimingProfile::Mm9Native;
    }
    else
    {
        error = "unknown compatibility_profile '" + compatibilityProfile + "'";
        return nullptr;
    }

    const YAML::Node componentsNode = node["components"];
    if (!componentsNode || !componentsNode.IsSequence())
    {
        error = "field 'components' must be a sequence";
        return nullptr;
    }
    for (const YAML::Node &componentNode : componentsNode)
    {
        std::string type;
        if (!readRequired(componentNode, "type", type, error))
        {
            return nullptr;
        }
        if (type == "sprite_system")
        {
            EffectSpriteEmitterDefinition emitter;
            if (!parseEmitter(componentNode, emitter, error))
            {
                return nullptr;
            }
            definition->spriteEmitters.push_back(std::move(emitter));
        }
        else if (type == "model_path")
        {
            EffectModelDefinition model;
            if (!parseModel(componentNode, model, error))
            {
                return nullptr;
            }
            definition->models.push_back(std::move(model));
        }
        else if (type == "null_transform")
        {
            EffectNullDefinition null;
            if (!parseNull(componentNode, null, error))
            {
                return nullptr;
            }
            definition->nulls.push_back(std::move(null));
        }
        else if (type == "sprite")
        {
            EffectSpriteDefinition sprite;
            if (!parseSprite(componentNode, sprite, error))
            {
                return nullptr;
            }
            definition->sprites.push_back(std::move(sprite));
        }
        else if (type == "ribbon")
        {
            EffectRibbonDefinition ribbon;
            if (!parseRibbon(componentNode, ribbon, error))
            {
                return nullptr;
            }
            definition->ribbons.push_back(std::move(ribbon));
        }
        else if (type == "sound")
        {
            EffectSoundDefinition sound;
            if (!parseSound(componentNode, sound, error))
            {
                return nullptr;
            }
            definition->sounds.push_back(std::move(sound));
        }
        else
        {
            error = "unsupported effect component type '" + type + "'";
            return nullptr;
        }
    }
    return definition;
}
}

EffectDefinitionLoader::EffectDefinitionLoader(const Engine::AssetFileSystem *pAssetFileSystem)
    : m_pAssetFileSystem(pAssetFileSystem)
{
}

std::optional<std::vector<std::shared_ptr<const EffectDefinition>>> EffectDefinitionLoader::load(
    const std::string &virtualPath,
    std::string &error) const
{
    if (m_pAssetFileSystem == nullptr)
    {
        error = "effect definition loader has no asset filesystem";
        return std::nullopt;
    }
    std::vector<std::shared_ptr<const EffectDefinition>> definitions;
    std::unordered_set<std::string> visited;
    const std::function<bool(const std::string &)> readLibrary = [&](const std::string &path)
    {
        if (!visited.insert(path).second)
        {
            error = "repeated effect library import: " + path;
            return false;
        }
        const std::optional<std::string> text = m_pAssetFileSystem->readTextFile(path);
        if (!text)
        {
            error = "failed to read effect library '" + path + "'";
            return false;
        }
        const auto parsed = parse(*text, error);
        if (!parsed)
        {
            return false;
        }
        definitions.insert(definitions.end(), parsed->begin(), parsed->end());
        const YAML::Node imports = YAML::Load(*text)["imports"];
        if (imports)
        {
            if (!imports.IsSequence())
            {
                error = "effect library imports must be a sequence: " + path;
                return false;
            }
            for (const YAML::Node &entry : imports)
            {
                if (!entry.IsScalar() || !readLibrary(entry.as<std::string>()))
                {
                    if (error.empty())
                    {
                        error = "effect library import must be an asset path: " + path;
                    }
                    return false;
                }
            }
        }
        return true;
    };
    try
    {
        EffectLibrary validator;
        if (!readLibrary(virtualPath) || !validator.replace(definitions, error))
        {
            return std::nullopt;
        }
        return definitions;
    }
    catch (const YAML::Exception &exception)
    {
        error = std::string("invalid effect library imports: ") + exception.what();
        return std::nullopt;
    }
}

std::optional<std::vector<std::shared_ptr<const EffectDefinition>>> EffectDefinitionLoader::parse(
    const std::string &text,
    std::string &error)
{
    try
    {
        const YAML::Node root = YAML::Load(text);
        std::string schema;
        if (!root.IsMap() || !readRequired(root, "schema", schema, error) ||
            schema != "openyamm.effectLibrary.v1")
        {
            if (error.empty())
            {
                error = "unsupported effect library schema '" + schema + "'";
            }
            return std::nullopt;
        }
        const YAML::Node effectsNode = root["effects"];
        if (!effectsNode || !effectsNode.IsSequence())
        {
            error = "field 'effects' must be a sequence";
            return std::nullopt;
        }
        std::vector<std::shared_ptr<const EffectDefinition>> definitions;
        definitions.reserve(effectsNode.size());
        for (size_t index = 0; index < effectsNode.size(); ++index)
        {
            std::shared_ptr<EffectDefinition> definition = parseDefinition(effectsNode[index], error);
            if (definition == nullptr)
            {
                error = "effect index " + std::to_string(index) + ": " + error;
                return std::nullopt;
            }
            definitions.push_back(std::move(definition));
        }
        EffectLibrary validator;
        if (!validator.replace(definitions, error))
        {
            return std::nullopt;
        }
        return definitions;
    }
    catch (const YAML::Exception &exception)
    {
        error = std::string("invalid effect library YAML: ") + exception.what();
        return std::nullopt;
    }
    catch (const std::exception &exception)
    {
        error = std::string("failed to parse effect library: ") + exception.what();
        return std::nullopt;
    }
}
}
