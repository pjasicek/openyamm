#include "game/render/FirstPersonViewModel.h"

#include "engine/AssetFileSystem.h"
#include "engine/BgfxContext.h"
#include "engine/models/GltfModelLoader.h"
#include "engine/render/ModelRenderer.h"
#include "game/render/WaterMath.h"

#include <bx/math.h>
#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <iostream>
#include <sstream>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
// Vertical field of view of the arms (the world keeps its own), and a slight downward look so the lowered weapon of
// the idle and walk clips stays in frame.
constexpr float ViewModelFovDegrees = 60.0f;
constexpr float ViewModelPitchRadians = 0.0f;
constexpr float ViewModelNearClip = 1.0f;
constexpr float ViewModelFarClip = 1000.0f;
// The arms' own key light where the scene has no sun (indoors), as a multiple of the room's ambient.
constexpr float HeldKeyStrength = 1.0f;
// Crossfades between clips, where a clip names none (Blend: N).
constexpr float LoopTransitionSeconds = 0.25f;
constexpr float ActionTransitionSeconds = 0.2f;
// Party speed (units per second, smoothed) above which the arms walk, and run.
constexpr float WalkSpeedThreshold = 60.0f;
constexpr float RunSpeedThreshold = 700.0f;

const char *setPrefix(FirstPersonViewModel::WeaponSet set)
{
    switch (set)
    {
        case FirstPersonViewModel::WeaponSet::OneHand:
            return "onehand";
        case FirstPersonViewModel::WeaponSet::TwoHand:
            return "twohand";
        case FirstPersonViewModel::WeaponSet::Staff:
            return "staff";
        case FirstPersonViewModel::WeaponSet::Bow:
            return "bow";
        case FirstPersonViewModel::WeaponSet::Dual:
            return "dual";
        case FirstPersonViewModel::WeaponSet::Crossbow:
            return "crossbow";
        case FirstPersonViewModel::WeaponSet::Pole:
            return "pole";
        case FirstPersonViewModel::WeaponSet::Claws:
            return "claws";
        case FirstPersonViewModel::WeaponSet::HandToHand:
            break;
    }
    return "handtohand";
}

// The sets whose attack shoots (a missile leaves at the clip's Release) rather than swings.
bool shoots(FirstPersonViewModel::WeaponSet set)
{
    return set == FirstPersonViewModel::WeaponSet::Bow || set == FirstPersonViewModel::WeaponSet::Crossbow;
}

// A dragon's spells cast from the mouth (Flame Blast): how far in front of the eye their glow sits (the arms' units) and
// its height on screen (normalized device y). The camera is the dragon's eyes, so its jaws are just below the
// crosshair.
constexpr float BreathGlowDistance = 24.0f;
constexpr float BreathScreenHeight = -0.3f;

// The inverse of a node's world matrix (a rotation, a uniform scale and a translation).
Engine::ModelMatrix inverseNodeMatrix(const Engine::ModelMatrix &matrix)
{
    const float scaleSquared = matrix[0] * matrix[0] + matrix[1] * matrix[1] + matrix[2] * matrix[2];
    Engine::ModelMatrix inverse = {};
    for (int row = 0; row < 3; ++row)
    {
        for (int column = 0; column < 3; ++column)
        {
            inverse[size_t(column * 4 + row)] = matrix[size_t(row * 4 + column)] / scaleSquared;
        }
    }
    for (int row = 0; row < 3; ++row)
    {
        inverse[size_t(12 + row)] = -(inverse[size_t(row)] * matrix[12] + inverse[size_t(4 + row)] * matrix[13]
            + inverse[size_t(8 + row)] * matrix[14]);
    }
    inverse[15] = 1.0f;
    return inverse;
}

// The world's light at the eye in the arms' space: they look along +Y with +Z up wherever the camera looks, so world
// directions turn by the camera's inverse (rows: its right, forward and up), and lights keep their offset from the eye.
Engine::ModelRenderLighting sceneViewModelLighting(const Engine::ModelRenderLighting &scene, float yaw, float pitch,
    const bx::Vec3 &eye)
{
    const bx::Vec3 forward = {std::cos(yaw) * std::cos(pitch), std::sin(yaw) * std::cos(pitch), std::sin(pitch)};
    const bx::Vec3 right = {std::sin(yaw), -std::cos(yaw), 0.0f};
    const bx::Vec3 up = bx::cross(right, forward);
    const auto turn = [&](const std::array<float, 3> &v)
    {
        const bx::Vec3 vector = {v[0], v[1], v[2]};
        return std::array<float, 3>{bx::dot(right, vector), bx::dot(forward, vector), bx::dot(up, vector)};
    };
    Engine::ModelRenderLighting lighting = scene;
    lighting.pLightGrid = nullptr;
    lighting.sector = -1;
    lighting.lightDirection = turn(scene.lightDirection);
    lighting.keyDirection = turn(scene.keyDirection);
    for (uint32_t light = 0; light < lighting.pointCount; ++light)
    {
        const std::array<float, 3> offset = turn({scene.pointPositions[light * 4], scene.pointPositions[light * 4 + 1],
            scene.pointPositions[light * 4 + 2]});
        lighting.pointPositions[light * 4] = eye.x + offset[0];
        lighting.pointPositions[light * 4 + 1] = eye.y + offset[1];
        lighting.pointPositions[light * 4 + 2] = eye.z + offset[2];
    }
    // The arms are a step from the eye: no fog between.
    lighting.fogDensities = {};
    lighting.fogDistances = {1.0e9f, 1.0e9f, 1.0e9f, 0};
    // Indoors there is no sun, and a metal blade takes almost none of the room's ambient: lit only by it, a held sword
    // reads black in a dungeon. The arms get a soft key of their own from above, left and in front of the eye, in the
    // room's colour and as strong as its ambient, so steel shows its highlight and edges yet stays as dark as the room.
    if (scene.direct <= 0.0f)
    {
        const bx::Vec3 key = bx::normalize(bx::Vec3{-0.4f, -0.55f, 0.75f});
        lighting.lightDirection = {key.x, key.y, key.z};
        lighting.direct = scene.ambient * HeldKeyStrength;
        lighting.directColor = scene.ambientColor;
    }
    // The sky reflection without its tint: a held blade fills a third of the screen, and a blue sky cast on all of it
    // reads as blue steel. Its strength stays.
    const float environment = (lighting.environmentScale[0] + lighting.environmentScale[1]
        + lighting.environmentScale[2]) / 3.0f;
    lighting.environmentScale = {environment, environment, environment};
    return lighting;
}

Engine::ModelRenderLighting viewModelLighting()
{
    // Key light from above, in front and to the left of the eye (the model looks along +Y, Z up).
    const bx::Vec3 light = bx::normalize(bx::Vec3{-0.4f, -0.55f, 0.75f});
    Engine::ModelRenderLighting lighting;
    lighting.displaySpaceLighting = true;
    lighting.ambient = 0.55f;
    lighting.direct = 0.6f;
    lighting.lightDirection = {light.x, light.y, light.z};
    return lighting;
}

// A rigid world matrix (column-major) as a transform: the bow's root on its node.
Engine::ModelTransform transformFromMatrix(const Engine::ModelMatrix &matrix)
{
    Engine::ModelTransform transform;
    transform.translation = {matrix[12], matrix[13], matrix[14]};
    std::array<float, 3> scale = {};
    float m[3][3] = {};
    for (int column = 0; column < 3; ++column)
    {
        scale[column] = std::sqrt(matrix[column * 4] * matrix[column * 4] + matrix[column * 4 + 1] * matrix[column * 4 + 1]
            + matrix[column * 4 + 2] * matrix[column * 4 + 2]);
        for (int row = 0; row < 3; ++row)
        {
            m[row][column] = matrix[column * 4 + row] / std::max(scale[column], 1.0e-8f);
        }
    }
    transform.scale = scale;
    const float trace = m[0][0] + m[1][1] + m[2][2];
    float x = 0.0f, y = 0.0f, z = 0.0f, w = 1.0f;
    if (trace > 0.0f)
    {
        const float root = std::sqrt(trace + 1.0f) * 2.0f;
        w = 0.25f * root;
        x = (m[2][1] - m[1][2]) / root;
        y = (m[0][2] - m[2][0]) / root;
        z = (m[1][0] - m[0][1]) / root;
    }
    else if (m[0][0] > m[1][1] && m[0][0] > m[2][2])
    {
        const float root = std::sqrt(1.0f + m[0][0] - m[1][1] - m[2][2]) * 2.0f;
        w = (m[2][1] - m[1][2]) / root;
        x = 0.25f * root;
        y = (m[0][1] + m[1][0]) / root;
        z = (m[0][2] + m[2][0]) / root;
    }
    else if (m[1][1] > m[2][2])
    {
        const float root = std::sqrt(1.0f + m[1][1] - m[0][0] - m[2][2]) * 2.0f;
        w = (m[0][2] - m[2][0]) / root;
        x = (m[0][1] + m[1][0]) / root;
        y = 0.25f * root;
        z = (m[1][2] + m[2][1]) / root;
    }
    else
    {
        const float root = std::sqrt(1.0f + m[2][2] - m[0][0] - m[1][1]) * 2.0f;
        w = (m[1][0] - m[0][1]) / root;
        x = (m[0][2] + m[2][0]) / root;
        y = (m[1][2] + m[2][1]) / root;
        z = 0.25f * root;
    }
    const float length = std::sqrt(x * x + y * y + z * z + w * w);
    transform.rotation = {x / length, y / length, z / length, w / length};
    return transform;
}

std::array<float, 3> transformPoint(const Engine::ModelMatrix &matrix, const std::array<float, 3> &point)
{
    return {matrix[0] * point[0] + matrix[4] * point[1] + matrix[8] * point[2] + matrix[12],
        matrix[1] * point[0] + matrix[5] * point[1] + matrix[9] * point[2] + matrix[13],
        matrix[2] * point[0] + matrix[6] * point[1] + matrix[10] * point[2] + matrix[14]};
}
}

Engine::ModelLoadResult FirstPersonViewModel::loadArmsFile(const std::filesystem::path &path) const
{
    return m_pArmsAssets != nullptr ? Engine::GltfModelLoader().load(*m_pArmsAssets, path.generic_string())
                                    : Engine::GltfModelLoader().loadStandaloneFile(path);
}

bool FirstPersonViewModel::ensureLoaded(const std::string &path, const Engine::AssetFileSystem *pAssets)
{
    if (path == m_loadedPath)
    {
        return !m_failed;
    }
    shutdown();
    m_loadedPath = path;
    m_pArmsAssets = pAssets;
    m_directory = std::filesystem::path(path).parent_path();
    const Engine::ModelLoadResult result = loadArmsFile(path);
    if (!result)
    {
        std::cerr << "View model not loaded: " << result.error << '\n';
        m_failed = true;
        return false;
    }
    m_asset = result.asset;
    for (size_t index = 0; index < m_asset->clips.size(); ++index)
    {
        m_clips[m_asset->clips[index].name] = {uint32_t(index), m_asset->clips[index].durationSeconds, -1.0f};
    }
    std::filesystem::path keysPath = path;
    keysPath.replace_extension(".textkeys.json");
    try
    {
        std::optional<std::string> keysText;
        if (m_pArmsAssets != nullptr)
        {
            keysText = m_pArmsAssets->readTextFile(keysPath.generic_string());
        }
        const YAML::Node keys = m_pArmsAssets != nullptr ? YAML::Load(keysText.value_or(std::string()))
                                                         : YAML::LoadFile(keysPath.string());
        for (const auto &entry : keys)
        {
            const auto found = m_clips.find(entry.first.as<std::string>());
            if (found == m_clips.end())
            {
                continue;
            }
            ClipInfo &info = found->second;
            for (const YAML::Node &key : entry.second["keys"])
            {
                std::string text = key[1].as<std::string>();
                std::transform(text.begin(), text.end(), text.begin(), [](unsigned char c) { return std::tolower(c); });
                text.erase(text.find_last_not_of(' ') + 1);
                const float seconds = key[0].as<float>();
                if ((text == "hit" || text == "release") && info.hitSeconds < 0.0f)
                {
                    info.hitSeconds = seconds;
                }
                else if ((text == "a:l" || text == "a:r") && info.chainSeconds < 0.0f)
                {
                    info.chainSeconds = seconds;
                    info.chainSide = text == "a:l" ? 'L' : 'R';
                }
                else if (text.starts_with("blend:"))
                {
                    info.blendSeconds = std::stof(text.substr(6)) / 30.0f;
                }
                else if (text == "attach" && info.attachSeconds < 0.0f)
                {
                    info.attachSeconds = seconds;
                }
            }
        }
    }
    catch (const std::exception &error)
    {
        std::cerr << "View model text keys not read (" << keysPath.string() << "): " << error.what() << '\n';
    }
    for (size_t node = 0; node < m_asset->nodes.size(); ++node)
    {
        const std::string &name = m_asset->nodes[node].name;
        if (name == "Camera01")
        {
            m_cameraNode = uint32_t(node);
        }
        else if (name == "Weapon")
        {
            m_weaponNode = uint32_t(node);
        }
        else if (name == "Bip01 L Hand")
        {
            m_leftHandNode = uint32_t(node);
        }
        else if (name == "Torch")
        {
            m_torchNode = uint32_t(node);
        }
        else if (name == "Bip01 R Hand")
        {
            m_rightHandNode = uint32_t(node);
        }
        else if (name == "OffHandWeapon")
        {
            m_offHandNode = uint32_t(node);
        }
        else if (name == "ClawTipR")
        {
            m_clawTipRightNode = uint32_t(node);
        }
        else if (name == "ClawTipL")
        {
            m_clawTipLeftNode = uint32_t(node);
        }
        else if (name == "Mouth")
        {
            m_mouthNode = uint32_t(node);
        }
        else if (name.size() == 15 && name.starts_with("Bip01 ") && name.substr(8, 6) == "Finger" && name[14] >= '1'
            && name[14] <= '4' && (name[6] == 'L' || name[6] == 'R'))
        {
            // Bip01 L Finger1 .. Finger4 (not their child joints, Finger11 and on): the knuckles.
            std::array<uint32_t, 4> &knuckles = name[6] == 'L' ? m_leftKnuckles : m_rightKnuckles;
            knuckles[size_t(name[14] - '1')] = uint32_t(node);
        }
    }
    // The arms idle bare-handed; a dragon's forelegs have only their claws set.
    if ((!clip("handtohandidle") && !clip("clawsidle")) || m_cameraNode == UINT32_MAX || m_weaponNode == UINT32_MAX)
    {
        std::cerr << "View model " << path << " lacks the handtohandidle (or clawsidle) clip or its Camera01/Weapon "
                  << "nodes.\n";
        m_failed = true;
        return false;
    }
    if (const std::optional<ClipInfo> crossbowIdle = clip("crossbowidle"); crossbowIdle && m_torchNode != UINT32_MAX)
    {
        // Where the crossbow clips keep the left hand's Torch frame (the foregrip) in the Weapon node's space.
        const Engine::ModelInstanceHandle probe = m_instances.create(m_asset);
        m_instances.sample(probe, crossbowIdle->index, 0.0f, *m_instances.rootTransform(probe));
        const Engine::ModelMatrix *pWeapon = m_instances.nodeMatrix(probe, m_weaponNode);
        const Engine::ModelMatrix *pTorch = m_instances.nodeMatrix(probe, m_torchNode);
        if (pWeapon != nullptr && pTorch != nullptr)
        {
            m_crossbowGrip = Engine::multiplyModelMatrices(inverseNodeMatrix(*pWeapon), *pTorch);
        }
        m_instances.destroy(probe);
    }
    // The model's own Z-up space, looking along +Y: the placement turns glTF forward (+Z) to +Y, which puts the
    // model's forward (glTF -Z, from its Z-up source) at -Y; half a turn brings it back.
    m_handle = m_instances.create(m_asset, Engine::gltfModelPlacement({0.0f, 0.0f, 0.0f}, bx::kPi));
    std::cout << "View model loaded: " << path << " (" << m_asset->clips.size() << " clips)\n";
    return true;
}

std::optional<FirstPersonViewModel::ClipInfo> FirstPersonViewModel::clip(const std::string &name) const
{
    const auto found = m_clips.find(name);
    return found != m_clips.end() ? std::optional<ClipInfo>(found->second) : std::nullopt;
}

std::optional<FirstPersonViewModel::ClipInfo> FirstPersonViewModel::setClip(const char *pAction) const
{
    WeaponSet set = m_kit ? m_kit->set : WeaponSet::HandToHand;
    if (set == WeaponSet::Dual && !dualReady())
    {
        set = WeaponSet::OneHand;
    }
    if (std::optional<ClipInfo> own = clip(std::string(setPrefix(set)) + pAction))
    {
        return own;
    }
    // The dual set has no casts, recoils or staggers of its own: the one-handed ones.
    if (set == WeaponSet::Dual)
    {
        if (std::optional<ClipInfo> oneHand = clip(std::string("onehand") + pAction))
        {
            return oneHand;
        }
    }
    // Arms without the pole clips hold a pole with the two-handed set, as before it had its own.
    if (set == WeaponSet::Pole)
    {
        if (std::optional<ClipInfo> twoHand = clip(std::string("twohand") + pAction))
        {
            return twoHand;
        }
    }
    return clip(std::string("handtohand") + pAction);
}

bool FirstPersonViewModel::dualReady() const
{
    return m_offHandNode != UINT32_MAX && clip("dualidle").has_value();
}

std::shared_ptr<const Engine::ModelAsset> FirstPersonViewModel::attachment(const std::string &file)
{
    const auto found = m_attachments.find(file);
    if (found != m_attachments.end())
    {
        return found->second;
    }
    const Engine::ModelLoadResult result = loadArmsFile(m_directory / file);
    if (!result)
    {
        std::cerr << "View model attachment not loaded: " << result.error << '\n';
    }
    m_attachments[file] = result.asset;
    return result.asset;
}

std::shared_ptr<const Engine::ModelAsset> FirstPersonViewModel::heldAsset(const std::string &path)
{
    const auto found = m_heldAssets.find(path);
    if (found != m_heldAssets.end())
    {
        return found->second;
    }
    std::shared_ptr<const Engine::ModelAsset> asset;
    if (m_pHeldAssets != nullptr)
    {
        const Engine::ModelLoadResult result = Engine::GltfModelLoader().load(*m_pHeldAssets, path);
        if (result)
        {
            asset = result.asset;
        }
        else
        {
            std::cerr << "Held weapon model " << path << " not loaded: " << result.error << '\n';
        }
    }
    m_heldAssets[path] = asset;
    return asset;
}

std::string FirstPersonViewModel::heldKind(const std::string &icon)
{
    const HeldWeaponGrip *pGrip = heldGrip(icon);
    return pGrip != nullptr ? pGrip->kind : std::string();
}

const HeldWeaponGrip *FirstPersonViewModel::heldGrip(const std::string &icon)
{
    if (icon.empty() || m_pHeldAssets == nullptr)
    {
        return nullptr;
    }
    if (!m_heldGrips)
    {
        m_heldGrips.emplace();
        std::string error;
        if (!loadHeldWeaponGrips(*m_pHeldAssets, "engine/world_items/held.yml", *m_heldGrips, error))
        {
            std::cerr << "Held weapon table not read: " << error << '\n';
        }
    }
    const auto grip = m_heldGrips->find(icon);
    return grip != m_heldGrips->end() ? &grip->second : nullptr;
}

std::string FirstPersonViewModel::kindTemplate(const std::string &icon, const std::string &weaponFile, uint8_t &tier)
{
    const HeldWeaponGrip *pGrip = heldGrip(icon);
    const HeldKindTemplate *pOwn = pGrip != nullptr ? heldKindTemplate(skinRules(), pGrip->kind) : nullptr;
    if (pOwn == nullptr)
    {
        return weaponFile;
    }
    if (pOwn->maxTier > 0)
    {
        tier = std::min(tier, pOwn->maxTier);
    }
    return pOwn->file;
}

std::optional<Engine::ModelAttachment> FirstPersonViewModel::heldAttachment(const std::string &path,
    const std::string &icon, uint32_t node, const HeldWeaponGrip **ppGrip)
{
    if (m_templateWeapons || path.empty() || icon.empty() || m_pHeldAssets == nullptr || node == UINT32_MAX)
    {
        return std::nullopt;
    }
    const HeldWeaponGrip *pFound = heldGrip(icon);
    if (pFound == nullptr || (m_templateWeapons && heldSkinUsesTemplate(skinRules(), pFound->kind)))
    {
        return std::nullopt;
    }
    const auto grip = m_heldGrips->find(icon);
    std::shared_ptr<const Engine::ModelAsset> asset = heldAsset(path);
    const std::optional<Engine::ModelMatrix> matrix =
        asset != nullptr ? heldWeaponMatrix(asset->staticBounds, grip->second) : std::nullopt;
    if (!matrix)
    {
        return std::nullopt;
    }
    if (ppGrip != nullptr)
    {
        *ppGrip = &grip->second;
    }
    return Engine::ModelAttachment{asset, node, 0, *matrix};
}

void FirstPersonViewModel::setHeldAssets(const Engine::AssetFileSystem *pAssets)
{
    if (pAssets != m_pHeldAssets)
    {
        m_pHeldAssets = pAssets;
        m_heldGrips.reset();
        m_skinRules.reset();
        m_heldAssets.clear();
    }
}

const HeldSkinRules &FirstPersonViewModel::skinRules()
{
    if (!m_skinRules)
    {
        m_skinRules.emplace();
        std::string error;
        if (m_pHeldAssets != nullptr
            && !loadHeldSkinRules(*m_pHeldAssets, "engine/world_items/held_tiers.yml", *m_skinRules, error))
        {
            std::cerr << "Held weapon tiers not read: " << error << '\n';
            m_skinRules.emplace();
            m_skinRules->tierCount = 0;
        }
    }
    return *m_skinRules;
}

uint8_t FirstPersonViewModel::skinTier(const HeldSkinItem &item)
{
    const HeldSkinRules &rules = skinRules();
    return rules.tierCount > 0 ? heldSkinTier(rules, item) : 0;
}

void FirstPersonViewModel::forceSkinTier(std::optional<uint8_t> tier)
{
    m_forcedTier = tier;
    m_kit.reset();
}

std::shared_ptr<const Engine::ModelAsset> FirstPersonViewModel::skinAttachment(const std::string &file, uint8_t tier)
{
    const std::string skin = heldSkinFile(file, m_forcedTier.value_or(tier));
    if (skin != file)
    {
        const std::filesystem::path path = m_directory / skin;
        const bool exists = m_pArmsAssets != nullptr ? m_pArmsAssets->exists(path.generic_string())
                                                     : std::filesystem::exists(path);
        if (exists)
        {
            return attachment(skin);
        }
    }
    return attachment(file);
}

void FirstPersonViewModel::useTemplateWeapons(bool templates)
{
    m_templateWeapons = templates;
    m_kit.reset();
}

void FirstPersonViewModel::applyKit(const Kit &kit, bool weaponInHand)
{
    std::vector<Engine::ModelAttachment> attachments;
    m_bladeTip = {};
    m_offBladeTip = {};
    m_weaponHidden = !weaponInHand;
    m_bowShown = false;
    const HeldWeaponGrip *pGrip = nullptr;
    const std::optional<Engine::ModelAttachment> heldBow = kit.set == WeaponSet::Bow
        ? heldAttachment(kit.heldModel, kit.heldIcon, m_torchNode, &pGrip) : std::nullopt;
    if (heldBow)
    {
        // Our bow (or crossbow) is a rigid model in the left hand: no string or arrow animation, unlike Oblivion's.
        if (weaponInHand)
        {
            attachments.push_back(*heldBow);
        }
    }
    else if (kit.set == WeaponSet::Bow && !kit.weapon.empty() && m_torchNode != UINT32_MAX)
    {
        // The bow animates (string, arrow): its own instance, not a rigid attachment. A template without clips (the
        // crossbow, built in the Torch node's space at the bow's full draw) hangs rigidly on the left hand.
        uint8_t bowTier = kit.weaponTier;
        const std::string bowFile = kindTemplate(kit.heldIcon, kit.weapon, bowTier);
        std::shared_ptr<const Engine::ModelAsset> bow = skinAttachment(bowFile, bowTier);
        if (bow != nullptr && bow->clips.empty())
        {
            if (weaponInHand)
            {
                attachments.push_back({bow, m_torchNode, 0});
            }
            bow = nullptr;
        }
        if (bow != nullptr && bow != m_bowAsset)
        {
            if (m_instances.contains(m_bowHandle))
            {
                m_instances.destroy(m_bowHandle);
            }
            m_bowAsset = bow;
            m_bowClips.clear();
            for (size_t index = 0; index < bow->clips.size(); ++index)
            {
                m_bowClips[bow->clips[index].name] = uint32_t(index);
            }
            m_bowHandle = m_instances.create(bow);
        }
        m_bowShown = bow != nullptr && weaponInHand;
    }
    else if (weaponInHand)
    {
        // The main hand's weapon on the Weapon node and, dual wielding, the off hand's on OffHandWeapon (the Weapon
        // node mirrored onto the left hand, its flat side turned over: the same placement holds either hand).
        const bool dual = kit.set == WeaponSet::Dual && dualReady();
        if (kit.set == WeaponSet::Crossbow)
        {
            holdCrossbow(kit, attachments);
        }
        else
        {
            holdWeapon(kit.heldModel, kit.heldIcon, kit.weapon, kit.weaponTier, m_weaponNode, attachments,
                m_bladeTip);
        }
        if (dual)
        {
            holdWeapon(kit.offHeldModel, kit.offHeldIcon, kit.offWeapon, kit.offTier, m_offHandNode, attachments,
                m_offBladeTip);
        }
    }
    m_instances.setAttachments(m_handle, std::move(attachments));
    if (m_instances.contains(m_bowHandle))
    {
        m_instances.setVisible(m_bowHandle, m_bowShown);
    }
    m_kit = kit;
    m_lastBladePoint.reset();
}

void FirstPersonViewModel::holdWeapon(const std::string &heldModel, const std::string &heldIcon,
    const std::string &weaponFile, uint8_t tier, uint32_t node, std::vector<Engine::ModelAttachment> &attachments,
    std::array<float, 3> &bladeTip)
{
    const std::string file = kindTemplate(heldIcon, weaponFile, tier);
    const HeldWeaponGrip *pGrip = nullptr;
    if (std::optional<Engine::ModelAttachment> held = heldAttachment(heldModel, heldIcon, node, &pGrip))
    {
        // Our model points along +Y from the palm: the tip is at the held length less the grip.
        attachments.push_back(*held);
        bladeTip = {0.0f, pGrip->length * (1.0f - pGrip->grip), 0.0f};
    }
    else if (std::shared_ptr<const Engine::ModelAsset> weapon = file.empty() ? nullptr : skinAttachment(file, tier))
    {
        // A template listed in template_scales is scaled about the grip (the node's origin), its tip with it.
        const float scale = heldTemplateScale(skinRules(), file);
        Engine::ModelAttachment attachment{weapon, node, 0};
        if (scale != 1.0f)
        {
            Engine::ModelMatrix matrix = Engine::identityModelMatrix();
            matrix[0] = scale;
            matrix[5] = scale;
            matrix[10] = scale;
            attachment.localMatrix = matrix;
        }
        attachments.push_back(attachment);
        // The positive end of the model's longest axis: the blade's tip or a club's head (Oblivion's weapons point
        // along +Y from the grip; a staff's butt reaches further the other way).
        const Engine::ModelBounds &bounds = weapon->staticBounds;
        size_t axis = 0;
        for (size_t candidate = 1; candidate < 3; ++candidate)
        {
            if (bounds.max[candidate] - bounds.min[candidate] > bounds.max[axis] - bounds.min[axis])
            {
                axis = candidate;
            }
        }
        for (size_t index = 0; index < 3; ++index)
        {
            bladeTip[index] =
                scale * (index == axis ? bounds.max[index] : (bounds.min[index] + bounds.max[index]) * 0.5f);
        }
    }
}

void FirstPersonViewModel::holdCrossbow(const Kit &kit, std::vector<Engine::ModelAttachment> &attachments)
{
    // Our ground crossbow, gripped on its foregrip by held.yml's Crossbow mount (the Torch frame), rides on the Weapon
    // node where the clips keep that frame, so it follows the right hand while the left spans the cord or casts.
    std::optional<Engine::ModelAttachment> held =
        m_crossbowGrip ? heldAttachment(kit.heldModel, kit.heldIcon, m_weaponNode, nullptr) : std::nullopt;
    if (held && held->localMatrix)
    {
        held->localMatrix = Engine::multiplyModelMatrices(*m_crossbowGrip, *held->localMatrix);
        attachments.push_back(*held);
        return;
    }
    holdWeapon(std::string(), kit.heldIcon, kit.weapon, kit.weaponTier, m_weaponNode, attachments, m_bladeTip);
}

void FirstPersonViewModel::startAction(const ClipInfo &info, bool waitsForBlow, float rate)
{
    m_actionRestart = m_action && m_action->index == info.index;
    m_action = info;
    m_actionSeconds = 0.0f;
    m_actionRate = rate;
    m_actionWaitsForBlow = waitsForBlow;
    m_actionIsSwing = false;
    m_actionTrails = false;
    m_actionGlint = false;
    m_actionIsCast = false;
    m_actionIsBite = false;
}

std::optional<FirstPersonViewModel::ClipInfo> FirstPersonViewModel::nextSwing(char side, float forward, float left)
{
    // The power attack has no chain key, so the next blow starts a new round from the right. With a weapon in each
    // hand the chain keys alternate the leading hand (dualattackright hands on to dualattackleft and back).
    const std::string action = m_kit && m_kit->set == WeaponSet::Claws ? clawsAction(m_comboStep++, side)
                                                                        : comboAction(m_comboStep++, side, forward, left);
    if (std::optional<ClipInfo> chosen = setClip(action.c_str()))
    {
        return chosen;
    }
    const std::string base = side == 'L' ? "attackleft" : "attackright";
    if (std::optional<ClipInfo> plain = setClip(base.c_str()))
    {
        return plain;
    }
    return setClip("attackright");
}

std::optional<std::array<float, 2>> FirstPersonViewModel::nodeScreenPoint(uint32_t node) const
{
    const Engine::ModelMatrix *pNode = node != UINT32_MAX ? m_instances.nodeMatrix(m_handle, node) : nullptr;
    if (pNode == nullptr || !m_hasViewProjection)
    {
        return std::nullopt;
    }
    const bx::Vec3 clip = bx::mulH({(*pNode)[12], (*pNode)[13], (*pNode)[14]}, m_viewProjection.data());
    return std::array<float, 2>{clip.x, clip.y};
}

void FirstPersonViewModel::startTalent(const std::string &talent, const Kit &kit, float recoverySeconds)
{
    // Each talent borrows a clip of the set (devdocs/solo_action/TALENTS.md): Cleave a sideways power attack,
    // Whirlwind two sweeps at speed, Charge the forward lunge, Volley the bow shot, the rest a cast.
    constexpr float TalentRate = 1.6f;
    constexpr float WhirlwindRate = 2.4f;
    m_actionQueue.clear();
    std::optional<ClipInfo> first;
    if (talent == "cleave")
    {
        first = setClip("attackleftpower");
        first = first ? first : setClip("attackrightpower");
        // A dragon's forelegs have no power attacks: the sideways claw swipe.
        first = first ? first : setClip("attackleft");
    }
    else if (talent == "whirlwind")
    {
        first = setClip("attackleftpower");
        if (std::optional<ClipInfo> second = setClip("attackrightpower"))
        {
            m_actionQueue.emplace_back(*second, WhirlwindRate);
        }
    }
    else if (talent == "charge" || talent == "heroic_strike")
    {
        first = setClip("attackforwardpower");
        // A dragon's forelegs have no power attacks: Heroic Strike is a claw swipe.
        first = first || talent == "charge" ? first : setClip("attackleft");
    }
    else if (talent == "volley")
    {
        first = shoots(kit.set) ? setClip("attack") : std::nullopt;
    }
    else
    {
        first = castClip(false, kit);
    }
    if (first)
    {
        // Cleave's strike and the bow talents' shot wait for this clip's blow or release (gameplay's talentAtBlow), as
        // an ordinary attack does, and play fitted to the member's recovery like it: the talent costs the time of an
        // attack and quickens with attack speed.
        const bool waited = talent == "cleave" || talent == "heroic_strike" || talent == "volley";
        float rate = talent == "whirlwind" ? WhirlwindRate : TalentRate;
        if (waited && recoverySeconds > 0.0f)
        {
            const float span = first->chainSeconds >= 0.0f ? first->chainSeconds
                : first->hitSeconds >= 0.0f ? std::min(first->duration, first->hitSeconds + 0.3f) : first->duration;
            rate = std::clamp(span / recoverySeconds, 1.0f, 3.5f);
        }
        startAction(*first, waited, rate);
        m_actionTrails =
            talent == "cleave" || talent == "whirlwind" || talent == "charge" || talent == "heroic_strike";
        if (!m_actionTrails && talent != "volley")
        {
            // Blink, Spell Surge, Purify ...: a cast with the hand's arcane glow.
            m_actionIsCast = true;
            m_actionCastHands = castHands(m_asset->clips[first->index].name);
            m_actionCastColor = schoolColor("");
        }
        // Cleave, Charge, Multishot, Power Shot: the weapon glints (a cast already glows in the hand).
        m_actionGlint = !m_actionIsCast;
        if (m_trace)
        {
            std::cout << "viewmodel trace t=" << m_clock << " talent " << talent << " "
                      << m_asset->clips[first->index].name << " hit at +"
                      << (first->hitSeconds >= 0.0f ? first->hitSeconds / m_actionRate : -1.0f) << '\n';
        }
    }
}

std::array<float, 3> FirstPersonViewModel::schoolColor(const std::string &school)
{
    std::string name = school;
    std::transform(name.begin(), name.end(), name.begin(), [](unsigned char c) { return std::tolower(c); });
    const auto has = [&](const char *pWord) { return name.find(pWord) != std::string::npos; };
    if (has("fire"))
    {
        return {1.0f, 0.42f, 0.12f};
    }
    if (has("air"))
    {
        return {0.75f, 0.88f, 1.0f};
    }
    if (has("water"))
    {
        return {0.25f, 0.85f, 1.0f};
    }
    if (has("earth"))
    {
        return {0.74f, 0.8f, 0.22f};
    }
    if (has("spirit"))
    {
        return {1.0f, 0.8f, 0.3f};
    }
    if (has("mind"))
    {
        return {0.72f, 0.42f, 1.0f};
    }
    if (has("body"))
    {
        return {0.35f, 1.0f, 0.45f};
    }
    if (has("light"))
    {
        return {1.0f, 0.95f, 0.72f};
    }
    if (has("dark"))
    {
        // Additive light cannot darken: a deep violet stands for darkness.
        return {0.42f, 0.08f, 0.72f};
    }
    return {0.85f, 0.8f, 1.0f};
}

std::array<float, 3> FirstPersonViewModel::elementColor(uint8_t element)
{
    // MeleeWeaponElement: None, Fire, Air, Water, Body, Light, Dark.
    static constexpr std::array<std::array<float, 3>, 7> Colors = {{
        {0.82f, 0.88f, 1.0f},
        {1.0f, 0.5f, 0.2f},
        {0.75f, 0.88f, 1.0f},
        {0.3f, 0.85f, 1.0f},
        {0.4f, 1.0f, 0.5f},
        {1.0f, 0.95f, 0.7f},
        {0.6f, 0.25f, 0.85f},
    }};
    return Colors[std::min<size_t>(element, Colors.size() - 1)];
}

std::optional<FirstPersonViewModel::ClipInfo> FirstPersonViewModel::castClip(bool self, const Kit &kit) const
{
    // A dragon casts at a target with its breath clip (Flame Blast leaves the mouth); a self cast shows nothing.
    if (kit.set == WeaponSet::Claws)
    {
        return self ? std::nullopt : setClip("breath");
    }
    if (kit.set == WeaponSet::Bow)
    {
        return clip(self ? "castselfalt" : "casttargetalt");
    }
    // The crossbow's and the pole's own casts: the left hand casts, the right holds the weapon low (arms without them:
    // Oblivion's one-handed casts below).
    if (kit.set == WeaponSet::Crossbow || kit.set == WeaponSet::Pole)
    {
        if (std::optional<ClipInfo> own = clip(std::string(setPrefix(kit.set)) + (self ? "castself" : "casttarget")))
        {
            return own;
        }
    }
    // Any weapon in the right hand stays still at the side (Oblivion's one-handed casts); the bare-handed clips lift
    // the right hand too, which with a two-handed weapon or staff swings its shaft across the view.
    if (kit.set != WeaponSet::HandToHand)
    {
        return clip(self ? "onehandcastself" : "onehandcasttarget");
    }
    return clip(self ? "castself" : "casttarget");
}

uint8_t FirstPersonViewModel::castHands(const std::string &clipName)
{
    // Measured on the clips (devdocs/solo_action/README.md "Casting"): the *alt clips cast from the right hand, the
    // one-handed ones from the left with the weapon hand still, the bare-handed self and touch casts with both; a
    // dragon breathes from the mouth.
    if (clipName == "clawsbreath")
    {
        return 4;
    }
    if (clipName.ends_with("alt"))
    {
        return 2;
    }
    if (clipName.starts_with("onehand"))
    {
        return 1;
    }
    if (clipName.starts_with("castself") || clipName.starts_with("casttouch"))
    {
        return 3;
    }
    return 1;
}

std::optional<std::array<float, 3>> FirstPersonViewModel::palmPoint(bool left) const
{
    const uint32_t handNode = left ? m_leftHandNode : m_rightHandNode;
    const Engine::ModelMatrix *pHand = handNode != UINT32_MAX ? m_instances.nodeMatrix(m_handle, handNode) : nullptr;
    if (pHand == nullptr)
    {
        return std::nullopt;
    }
    const std::array<float, 3> wrist = {(*pHand)[12], (*pHand)[13], (*pHand)[14]};
    std::array<float, 3> knuckles = {};
    int count = 0;
    for (const uint32_t node : left ? m_leftKnuckles : m_rightKnuckles)
    {
        if (const Engine::ModelMatrix *pKnuckle = node != UINT32_MAX ? m_instances.nodeMatrix(m_handle, node) : nullptr)
        {
            knuckles = {knuckles[0] + (*pKnuckle)[12], knuckles[1] + (*pKnuckle)[13], knuckles[2] + (*pKnuckle)[14]};
            ++count;
        }
    }
    if (count == 0)
    {
        return wrist;
    }
    constexpr float PalmShare = 0.55f;
    std::array<float, 3> palm;
    for (size_t axis = 0; axis < 3; ++axis)
    {
        palm[axis] = wrist[axis] + (knuckles[axis] / float(count) - wrist[axis]) * PalmShare;
    }
    return palm;
}

std::optional<std::array<float, 3>> FirstPersonViewModel::breathPoint() const
{
    const Engine::ModelMatrix *pMouth = m_mouthNode != UINT32_MAX ? m_instances.nodeMatrix(m_handle, m_mouthNode)
                                                                  : nullptr;
    const Engine::ModelMatrix *pCamera = m_instances.nodeMatrix(m_handle, m_cameraNode);
    if (pMouth == nullptr || pCamera == nullptr)
    {
        return std::nullopt;
    }
    // The eye looks along +Y with +Z up (render): the mouth's direction across, at the jaws' height on screen.
    const std::array<float, 3> eye = {(*pCamera)[12], (*pCamera)[13], (*pCamera)[14]};
    const std::array<float, 3> mouth = {(*pMouth)[12] - eye[0], (*pMouth)[13] - eye[1], (*pMouth)[14] - eye[2]};
    const float forward = std::max(mouth[1], 1.0f);
    const float halfTan = std::tan(ViewModelFovDegrees * 0.5f * bx::kPi / 180.0f);
    const float down = BreathScreenHeight * halfTan;
    const float across = std::clamp(mouth[0] / forward, -halfTan, halfTan);
    return std::array<float, 3>{eye[0] + across * BreathGlowDistance, eye[1] + BreathGlowDistance,
        eye[2] + down * BreathGlowDistance};
}

std::vector<std::array<float, 3>> FirstPersonViewModel::castPalms(uint8_t hands) const
{
    std::vector<std::array<float, 3>> palms;
    if ((hands & 4) != 0)
    {
        if (const std::optional<std::array<float, 3>> mouth = breathPoint())
        {
            palms.push_back(*mouth);
        }
    }
    for (const bool left : {true, false})
    {
        if ((hands & (left ? 1 : 2)) != 0)
        {
            if (const std::optional<std::array<float, 3>> palm = palmPoint(left))
            {
                palms.push_back(*palm);
            }
        }
    }
    return palms;
}

std::vector<std::array<float, 3>> FirstPersonViewModel::handPoints() const
{
    if (m_kit && m_kit->set == WeaponSet::Claws)
    {
        std::vector<std::array<float, 3>> points;
        for (const uint32_t node : {m_clawTipLeftNode, m_clawTipRightNode})
        {
            if (const Engine::ModelMatrix *pTip = node != UINT32_MAX ? m_instances.nodeMatrix(m_handle, node) : nullptr)
            {
                points.push_back({(*pTip)[12], (*pTip)[13], (*pTip)[14]});
            }
        }
        return points;
    }
    return castPalms(3);
}

void FirstPersonViewModel::updateTalentEffects(const Input &input, float delta)
{
    // Gold, apart from every school's and element's colour.
    constexpr std::array<float, 3> GlintColor = {1.0f, 0.82f, 0.4f};
    m_fx.setHandEmbers(input.onslaught > 0.0f ? handPoints() : std::vector<std::array<float, 3>>(), input.onslaught);
    if (m_action && m_actionGlint)
    {
        bool weapon = false;
        for (const bool offHand : {false, true})
        {
            if (const auto points = bladePoints(offHand))
            {
                m_fx.sparkle(points->first, points->second, 0.8f, GlintColor, delta);
                weapon = true;
            }
        }
        if (!weapon)
        {
            // Fists and talons: around the hands.
            for (const std::array<float, 3> &point : handPoints())
            {
                m_fx.sparkle(point, point, 2.5f, GlintColor, delta);
            }
        }
    }
}

std::optional<std::pair<std::array<float, 3>, std::array<float, 3>>> FirstPersonViewModel::bladePoints(
    bool offHand) const
{
    const uint32_t node = offHand ? m_offHandNode : m_weaponNode;
    const std::array<float, 3> &bladeTip = offHand ? m_offBladeTip : m_bladeTip;
    const Engine::ModelMatrix *pWeapon = node != UINT32_MAX ? m_instances.nodeMatrix(m_handle, node) : nullptr;
    const bool noTip = bladeTip[0] == 0.0f && bladeTip[1] == 0.0f && bladeTip[2] == 0.0f;
    if (pWeapon == nullptr || m_weaponHidden || noTip)
    {
        return std::nullopt;
    }
    return std::make_pair(transformPoint(*pWeapon, {0.0f, 0.0f, 0.0f}), transformPoint(*pWeapon, bladeTip));
}

void FirstPersonViewModel::startCast(const ClipInfo &info, bool waitsForBlow, float rate,
    const std::array<float, 3> &color)
{
    startAction(info, waitsForBlow, rate);
    m_actionIsCast = true;
    m_actionCastHands = castHands(m_asset->clips[info.index].name);
    m_actionCastColor = color;
}

void FirstPersonViewModel::updateTrail(float delta, const Kit &kit, bool heldPose, uint32_t clipIndex, float time)
{
    const bool armed = m_trailEnabled && !kit.weapon.empty() && !shoots(kit.set);
    // A tip moving this fast (the arms' units per second) starts to leave a trail; this fast, it leaves all of it.
    constexpr float TrailSlowSpeed = 140.0f;
    constexpr float TrailFastSpeed = 420.0f;
    const auto strengthOf = [](float speed)
    {
        const float t = std::clamp((speed - TrailSlowSpeed) / (TrailFastSpeed - TrailSlowSpeed), 0.0f, 1.0f);
        return t * t * (3.0f - 2.0f * t);
    };
    const auto distance = [](const std::array<float, 3> &a, const std::array<float, 3> &b)
    {
        return std::sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]) + (a[2] - b[2]) * (a[2] - b[2]));
    };
    if (!armed || clipIndex == UINT32_MAX)
    {
        m_lastTipPoints = {};
        return;
    }
    // Each blade leaves its own trail: the main hand's, and dual wielding the off hand's.
    const size_t blades = kit.set == WeaponSet::Dual ? 2 : 1;
    if (heldPose)
    {
        // A held pose shows the trail the clip would have left over the last tenth of a second (captures, review).
        constexpr int Steps = 8;
        constexpr float StepSeconds = 0.0125f;
        m_fx.clearTrail();
        std::array<std::optional<std::array<float, 3>>, 2> previousTips;
        for (int step = Steps; step >= 0; --step)
        {
            const float sampleTime = std::max(0.0f, time - StepSeconds * float(step));
            m_instances.sampleBlended(m_handle, clipIndex, sampleTime, *m_instances.rootTransform(m_handle), 0.0f, 0.0f,
                {}, true);
            for (size_t blade = 0; blade < blades; ++blade)
            {
                const auto points = bladePoints(blade == 1);
                if (!points)
                {
                    continue;
                }
                const float strength = previousTips[blade]
                    ? strengthOf(distance(points->second, *previousTips[blade]) / StepSeconds) : 0.0f;
                m_fx.addTrailSample(blade, m_clock - StepSeconds * float(step), points->first, points->second,
                    strength);
                previousTips[blade] = points->second;
            }
        }
        return;
    }
    if (!(m_action && m_actionTrails))
    {
        m_lastTipPoints = {};
        return;
    }
    for (size_t blade = 0; blade < blades; ++blade)
    {
        const auto points = bladePoints(blade == 1);
        if (!points)
        {
            continue;
        }
        std::optional<std::array<float, 3>> &lastTip = m_lastTipPoints[blade];
        const float strength = lastTip && delta > 0.0f ? strengthOf(distance(points->second, *lastTip) / delta) : 0.0f;
        m_fx.addTrailSample(blade, m_clock, points->first, points->second, strength);
        lastTip = points->second;
    }
}

std::optional<std::array<float, 2>> FirstPersonViewModel::bladeScreenPoint(bool offHand) const
{
    // A dragon's blow follows its talon tips: the right rake's, or the left's.
    if (m_kit && m_kit->set == WeaponSet::Claws && m_clawTipRightNode != UINT32_MAX && m_clawTipLeftNode != UINT32_MAX)
    {
        return nodeScreenPoint(offHand ? m_clawTipLeftNode : m_clawTipRightNode);
    }
    const uint32_t node = offHand ? m_offHandNode : m_weaponNode;
    const Engine::ModelMatrix *pWeapon = node != UINT32_MAX ? m_instances.nodeMatrix(m_handle, node) : nullptr;
    if (pWeapon == nullptr || !m_hasViewProjection)
    {
        return std::nullopt;
    }
    const std::array<float, 3> tip = transformPoint(*pWeapon, offHand ? m_offBladeTip : m_bladeTip);
    const bx::Vec3 clip = bx::mulH({tip[0], tip[1], tip[2]}, m_viewProjection.data());
    return std::array<float, 2>{clip.x, clip.y};
}

FirstPersonViewModel::Output FirstPersonViewModel::update(const Input &input)
{
    Output output;
    if (m_failed || !m_instances.contains(m_handle))
    {
        return output;
    }
    const float delta = std::max(input.deltaSeconds, 0.0f);
    m_clock += delta;
    if (m_trace && (input.memberRecoverySeconds > 0.0f) != (m_lastMemberRecovery > 0.0f))
    {
        std::cout << "viewmodel trace t=" << m_clock << (input.memberRecoverySeconds > 0.0f ? " recovery "
            + std::to_string(input.memberRecoverySeconds) : std::string(" ready")) << '\n';
    }
    if (input.memberRecoverySeconds <= 0.0f && m_lastMemberRecovery > 0.0f)
    {
        m_readyClock = m_clock;
    }
    m_lastMemberRecovery = input.memberRecoverySeconds;
    if (m_hasPartyPosition && delta > 0.0f)
    {
        const std::array<float, 2> velocity = {(input.partyX - m_lastPartyX) / delta,
            (input.partyY - m_lastPartyY) / delta};
        // Teleports and map moves read as one frame of huge speed: ignore them.
        if (std::hypot(velocity[0], velocity[1]) < 20000.0f)
        {
            const float blend = std::min(1.0f, delta * 8.0f);
            m_moveVelocity[0] += (velocity[0] - m_moveVelocity[0]) * blend;
            m_moveVelocity[1] += (velocity[1] - m_moveVelocity[1]) * blend;
        }
    }
    m_lastPartyX = input.partyX;
    m_lastPartyY = input.partyY;
    m_hasPartyPosition = true;

    const Kit kit = m_kitOverride.value_or(input.kit);
    if (!m_kit || kit != *m_kit)
    {
        // A new weapon is drawn: the equip clip brings the hand to it and the weapon appears at its Attach key.
        const bool drawing = m_kit.has_value() || std::exchange(m_resumed, false);
        m_kit = kit;
        const std::optional<ClipInfo> equip = drawing ? setClip("equip") : std::nullopt;
        applyKit(kit, !(equip && equip->attachSeconds > 0.0f));
        if (equip)
        {
            startAction(*equip, false);
        }
    }
    if (m_weaponHidden && !(m_action && m_actionSeconds < m_action->attachSeconds))
    {
        applyKit(kit, true);
    }
    output.meleeSwings = true;

    m_trailEnabled = input.trailEnabled;
    m_fx.setTrailColor(input.trailColor, input.trailIntensity);
    if (m_seenSerials && input.swingSerial != m_lastSwingSerial)
    {
        m_swingQueued = true;
        m_queuedIsCast = input.swingIsCast;
        m_queuedCastSelf = input.castSelf;
        m_queuedCastColor = input.castColor;
        m_queuedRecovery = input.swingRecoverySeconds;
    }
    // A swing starts from rest with the right-hand cut; during a swing it waits for the chain key (a:L, a:R) and
    // continues to that side, as Oblivion's attacks combine. A bow shot draws an arrow from the quiver, nocks, draws
    // and looses it at Release (bowattack); the next waits for that release. A crossbow's shot is raised, loosed at
    // Release and spanned again; the next waits for the span (its chain key, at the bow shot's span).
    const std::optional<ClipInfo> shot = shoots(kit.set) ? setClip("attack") : std::nullopt;
    const bool shooting = shot && m_action && m_action->index == shot->index;
    const bool swinging = !shot && m_action && m_action->chainSeconds >= 0.0f;
    const float shotReady = shooting && m_action->chainSeconds >= 0.0f ? m_action->chainSeconds
        : shooting ? m_action->hitSeconds : 0.0f;
    if (m_swingQueued && (shooting ? m_actionSeconds >= shotReady
                                   : !swinging || m_actionSeconds >= m_action->chainSeconds))
    {
        // A slow recovery outlasts the swing: the combo still continues to the other side when the next blow comes
        // soon after the last ended, and starts over from the right after a pause.
        // A pause is longer than a second after the swing ended and after the member was ready again: a held key on a
        // slow recovery (a MAW dragon's 1.8 s, or a recovery a blow taken lengthened) keeps the combo going.
        constexpr float ComboPauseSeconds = 1.0f;
        const bool continuing = swinging || m_clock - m_lastSwingEnd <= ComboPauseSeconds
            || (m_readyClock >= m_lastSwingEnd && m_clock - m_readyClock <= ComboPauseSeconds);
        const char side = swinging ? m_action->chainSide : continuing ? m_nextSwingSide : 'R';
        if (!continuing)
        {
            m_comboStep = 0;
        }
        const float forward = m_moveVelocity[0] * std::cos(input.yawRadians)
            + m_moveVelocity[1] * std::sin(input.yawRadians);
        const float left = -m_moveVelocity[0] * std::sin(input.yawRadians)
            + m_moveVelocity[1] * std::cos(input.yawRadians);
        // A waited cast: the cast clip for the kit, fitted to the spell's recovery like a swing, released at its Hit.
        const std::optional<ClipInfo> cast = m_queuedIsCast ? castClip(m_queuedCastSelf, kit) : std::nullopt;
        const std::optional<ClipInfo> swing = m_queuedIsCast ? std::nullopt : shot ? shot : nextSwing(side, forward, left);
        m_swingQueued = false;
        if (cast)
        {
            const float span = cast->hitSeconds >= 0.0f ? std::min(cast->duration, cast->hitSeconds + 0.3f)
                                                        : cast->duration;
            const float rate = m_queuedRecovery > 0.0f ? std::clamp(span / m_queuedRecovery, 1.0f, 3.5f) : 1.0f;
            startCast(*cast, true, rate, m_queuedCastColor);
            if (m_trace)
            {
                std::cout << "viewmodel trace t=" << m_clock << " cast " << m_asset->clips[cast->index].name
                          << " rate " << rate << " recovery " << m_queuedRecovery << '\n';
            }
        }
        else if (swing)
        {
            // MM's recovery counts from the press: the swing reaches the point where the next one may chain (or,
            // without a chain key, a moment after its blow) as the recovery ends, never slower than Oblivion's own
            // speed and at most 3.5 times faster.
            const float span = swing->chainSeconds >= 0.0f ? swing->chainSeconds
                : swing->hitSeconds >= 0.0f ? std::min(swing->duration, swing->hitSeconds + 0.3f) : swing->duration;
            // Two-handed axes swung one in each hand (a Minotaur's) may play slower than Oblivion's own pace when the
            // recovery is long: heavier blades.
            const float slowest = kit.heavy ? 0.7f : 1.0f;
            const float rate = input.swingRecoverySeconds > 0.0f
                ? std::clamp(span / input.swingRecoverySeconds, slowest, 3.5f) : 1.0f;
            startAction(*swing, true, rate);
            m_actionIsSwing = true;
            m_actionTrails = !shot;
            m_actionIsBite = kit.set == WeaponSet::Claws && m_asset->clips[swing->index].name == "clawsbite";
            m_nextSwingSide = swing->chainSide != 0 ? swing->chainSide : 'R';
            if (m_trace)
            {
                std::cout << "viewmodel trace t=" << m_clock << " swing " << m_asset->clips[swing->index].name
                          << " rate " << rate << " recovery " << input.swingRecoverySeconds << " hit at +"
                          << (swing->hitSeconds >= 0.0f ? swing->hitSeconds / rate : -1.0f) << '\n';
            }
        }
        else
        {
            output.blowReleased = true;
        }
    }
    if (m_seenSerials && input.actionSerial != m_lastActionSerial)
    {
        std::optional<ClipInfo> shown;
        if (input.action == Action::Melee)
        {
            shown = setClip(m_action && m_action->chainSide == 'L' ? "attackleft" : "attackright");
        }
        else if (input.action == Action::Cast)
        {
            // A cast gameplay already made (an upkeep spell, a scroll): shown at once, its glow released at the Hit.
            const std::optional<ClipInfo> cast = castClip(input.castSelf, kit);
            if (cast && !(m_action && m_actionWaitsForBlow))
            {
                startCast(*cast, false, 1.0f, input.castColor);
            }
        }
        else if (kit.set == WeaponSet::Claws)
        {
            // A dragon's breath leaves at once with no inhale (devdocs/solo_action/DRAGON.md): the forelegs show
            // nothing more.
        }
        else if (shot && !shooting)
        {
            // A shot gameplay made at a released bowattack (or crossbowattack) is that very missile: nothing more to
            // show.
            shown = shot;
        }
        if (shown && !(m_action && m_actionWaitsForBlow))
        {
            startAction(*shown, false);
        }
    }
    if (m_seenSerials && input.talentSerial != m_lastTalentSerial && !(m_action && m_actionWaitsForBlow))
    {
        startTalent(input.talentClip, kit, input.swingRecoverySeconds);
    }
    m_lastTalentSerial = input.talentSerial;
    m_lastSwingSerial = input.swingSerial;
    m_lastActionSerial = input.actionSerial;
    m_seenSerials = true;

    bool releaseBlow = false;
    if (m_action)
    {
        const float previous = m_actionSeconds;
        m_actionSeconds += delta * m_actionRate;
        if (m_actionIsCast && m_action->hitSeconds > 0.0f)
        {
            const std::vector<std::array<float, 3>> palms = castPalms(m_actionCastHands);
            if (!palms.empty() && m_hasViewProjection)
            {
                const bx::Vec3 clip =
                    bx::mulH({palms.front()[0], palms.front()[1], palms.front()[2]}, m_viewProjection.data());
                output.castHandScreen = std::array<float, 2>{clip.x, clip.y};
            }
            // The glow gathers on the casting palms until the Hit, where the spell leaves in a flash.
            if (previous < m_action->hitSeconds && m_actionSeconds >= m_action->hitSeconds)
            {
                m_fx.releaseCast(castPalms(m_actionCastHands), m_actionCastColor);
            }
            else if (m_actionSeconds < m_action->hitSeconds)
            {
                m_fx.setCastGlow(castPalms(m_actionCastHands), m_actionCastColor,
                    m_actionSeconds / m_action->hitSeconds);
            }
        }
        if (m_actionWaitsForBlow && m_action->hitSeconds >= 0.0f && previous < m_action->hitSeconds
            && m_actionSeconds >= m_action->hitSeconds)
        {
            releaseBlow = true;
            m_actionWaitsForBlow = false;
        }
        if (m_actionIsSwing)
        {
            m_lastSwingEnd = m_clock;
        }
        if (m_actionSeconds >= m_action->duration)
        {
            // A clip without a Hit key lands its blow at the end.
            releaseBlow = releaseBlow || m_actionWaitsForBlow;
            m_actionWaitsForBlow = false;
            m_action.reset();
            if (!m_actionQueue.empty())
            {
                const std::pair<ClipInfo, float> next = m_actionQueue.front();
                m_actionQueue.erase(m_actionQueue.begin());
                const bool trails = m_actionTrails;
                const bool glint = m_actionGlint;
                startAction(next.first, false, next.second);
                m_actionTrails = trails;
                m_actionGlint = glint;
            }
        }
    }

    uint32_t clipIndex = UINT32_MAX;
    float time = 0.0f;
    float transition = LoopTransitionSeconds;
    bool restart = false;
    if (m_heldPose)
    {
        if (std::optional<ClipInfo> held = clip(m_heldPose->first))
        {
            clipIndex = held->index;
            time = std::clamp(m_heldPose->second, 0.0f, held->duration);
            transition = 0.0f;
        }
    }
    else if (m_action)
    {
        clipIndex = m_action->index;
        time = m_actionSeconds;
        transition = (m_action->blendSeconds >= 0.0f ? m_action->blendSeconds : ActionTransitionSeconds) / m_actionRate;
        restart = m_actionRestart;
        m_actionRestart = false;
    }
    if (clipIndex == UINT32_MAX)
    {
        std::optional<ClipInfo> loop;
        const float speed = std::hypot(m_moveVelocity[0], m_moveVelocity[1]);
        if (!loop && speed > WalkSpeedThreshold)
        {
            const float forward = m_moveVelocity[0] * std::cos(input.yawRadians)
                + m_moveVelocity[1] * std::sin(input.yawRadians);
            const float left = -m_moveVelocity[0] * std::sin(input.yawRadians)
                + m_moveVelocity[1] * std::cos(input.yawRadians);
            const char *pDirection = std::abs(forward) >= std::abs(left)
                ? (forward >= 0.0f ? "forward" : "backward") : (left >= 0.0f ? "left" : "right");
            const std::string action = std::string(speed > RunSpeedThreshold ? "fast" : "") + pDirection;
            loop = setClip(action.c_str());
            if (!loop)
            {
                loop = setClip("forward");
            }
        }
        if (!loop)
        {
            loop = setClip("idle");
        }
        if (loop)
        {
            m_loopSeconds += delta;
            clipIndex = loop->index;
            time = std::fmod(m_loopSeconds, std::max(loop->duration, 0.001f));
        }
    }
    if (clipIndex != UINT32_MAX)
    {
        m_instances.sampleBlended(m_handle, clipIndex, time, *m_instances.rootTransform(m_handle), delta, transition,
            {}, restart);
        updateBow(clipIndex, time, delta, transition, restart);
    }
    updateTrail(delta, kit, m_heldPose.has_value(), clipIndex, time);
    updateTalentEffects(input, delta);
    if (m_heldPose && m_fxPreview && clipIndex != UINT32_MAX)
    {
        m_fx.setCastGlow(castPalms(castHands(m_asset->clips[clipIndex].name)), *m_fxPreview, 1.0f);
    }
    else if (!(m_action && m_actionIsCast))
    {
        m_fx.stopCastGlow();
    }
    m_fx.update(delta);

    const std::optional<std::array<float, 2>> bladePoint = bladeScreenPoint();
    // Bare fists strike with either hand, and so do two blades: the left fist's (or the off-hand blade's) path too,
    // and the blow follows the one that travelled further since the swing began (at contact the punching fist slows,
    // so speed alone can pick the other).
    const bool dualShown = kit.set == WeaponSet::Dual && dualReady();
    const std::optional<std::array<float, 2>> leftPoint = kit.set == WeaponSet::Claws ? bladeScreenPoint(true)
        : kit.weapon.empty() ? nodeScreenPoint(m_leftHandNode)
        : dualShown ? bladeScreenPoint(true) : std::nullopt;
    if (m_action && m_actionIsSwing && m_actionSeconds <= delta * m_actionRate + 1.0e-4f)
    {
        m_swingStartBlade = bladePoint;
        m_swingStartLeft = leftPoint;
    }
    if (releaseBlow)
    {
        output.blowReleased = true;
        if (m_trace)
        {
            std::cout << "viewmodel trace t=" << m_clock << " blow (clip " << m_actionSeconds << ", frame "
                      << delta << ")\n";
        }
        const auto motion = [](const std::optional<std::array<float, 2>> &now,
                                const std::optional<std::array<float, 2>> &before) -> std::array<float, 2>
        {
            return now && before ? std::array<float, 2>{(*now)[0] - (*before)[0], (*now)[1] - (*before)[1]}
                                 : std::array<float, 2>{};
        };
        std::array<float, 2> direction = motion(bladePoint, m_lastBladePoint);
        const std::array<float, 2> rightTravel = motion(bladePoint, m_swingStartBlade);
        const std::array<float, 2> leftTravel = motion(leftPoint, m_swingStartLeft);
        if (std::hypot(leftTravel[0], leftTravel[1]) > std::hypot(rightTravel[0], rightTravel[1]))
        {
            direction = motion(leftPoint, m_lastLeftPoint);
        }
        // A bite's jaw closes down the screen: its rake runs downwards.
        if (m_actionIsBite)
        {
            direction = {0.0f, -1.0f};
        }
        if (std::hypot(direction[0], direction[1]) > 1.0e-4f)
        {
            output.blowDirection = direction;
        }
    }
    m_lastBladePoint = bladePoint;
    m_lastLeftPoint = leftPoint;
    return output;
}

void FirstPersonViewModel::updateBow(uint32_t clipIndex, float time, float delta, float transition, bool restart)
{
    if (!m_bowShown || !m_instances.contains(m_bowHandle))
    {
        return;
    }
    const Engine::ModelMatrix *pTorch = m_instances.nodeMatrix(m_handle, m_torchNode);
    if (pTorch == nullptr)
    {
        return;
    }
    const auto found = m_bowClips.find(m_asset->clips[clipIndex].name);
    const auto rest = m_bowClips.find("rest");
    if (found == m_bowClips.end() && rest == m_bowClips.end())
    {
        return;
    }
    const bool own = found != m_bowClips.end();
    m_instances.sampleBlended(m_bowHandle, own ? found->second : rest->second, own ? time : 0.0f,
        transformFromMatrix(*pTorch), delta, transition, {}, restart);
}

void FirstPersonViewModel::render(Engine::ModelRenderer &renderer, bgfx::FrameBufferHandle target, uint16_t width,
    uint16_t height, const Engine::ModelRenderLighting *pScene, float yawRadians, float pitchRadians)
{
    if (m_failed || !m_instances.contains(m_handle) || width == 0 || height == 0
        || bgfx::getRendererType() == bgfx::RendererType::Noop)
    {
        return;
    }
    const Engine::ModelMatrix *pCamera = m_instances.nodeMatrix(m_handle, m_cameraNode);
    if (pCamera == nullptr)
    {
        return;
    }
    const bx::Vec3 eye = {(*pCamera)[12], (*pCamera)[13], (*pCamera)[14]};
    const bx::Vec3 forward = {0.0f, std::cos(ViewModelPitchRadians), -std::sin(ViewModelPitchRadians)};
    float view[16];
    float projection[16];
    bx::mtxLookAt(view, eye, bx::add(eye, forward), {0.0f, 0.0f, 1.0f}, bx::Handedness::Right);
    bx::mtxProj(projection, ViewModelFovDegrees, float(width) / float(height), ViewModelNearClip, ViewModelFarClip,
        bgfx::getCaps()->homogeneousDepth, bx::Handedness::Right);
    bx::mtxMul(m_viewProjection.data(), view, projection);
    m_hasViewProjection = true;
    m_aspect = float(width) / float(height);

    const uint16_t viewId = FirstPersonViewModelView;
    bgfx::setViewName(viewId, "First-person view model");
    bgfx::setViewFrameBuffer(viewId, target);
    bgfx::setViewRect(viewId, 0, 0, width, height);
    bgfx::setViewClear(viewId, BGFX_CLEAR_DEPTH, 0x00000000u, 1.0f, 0);
    bgfx::setViewMode(viewId, bgfx::ViewMode::Sequential);
    bgfx::setViewTransform(viewId, view, projection);
    bgfx::touch(viewId);
    if (!bgfx::isValid(m_worldClipPlaneUniform))
    {
        m_worldClipPlaneUniform = bgfx::createUniform("u_worldClipPlane", bgfx::UniformType::Vec4);
    }
    // The water reflection's clip plane may still be set from an earlier view: the arms clip nothing.
    const float noClip[4] = {};
    bgfx::setUniform(m_worldClipPlaneUniform, noClip);
    const Engine::ModelRenderLighting lighting = pScene != nullptr
        ? sceneViewModelLighting(*pScene, yawRadians, pitchRadians, eye) : viewModelLighting();
    renderer.renderPortrait(m_instances, m_handle, viewId, {eye.x, eye.y, eye.z}, lighting);
    if (m_bowShown && m_instances.contains(m_bowHandle))
    {
        renderer.renderPortrait(m_instances, m_bowHandle, viewId, {eye.x, eye.y, eye.z}, lighting);
    }
    m_fx.render(viewId, m_clock);
}

void FirstPersonViewModel::resume()
{
    m_action.reset();
    m_actionQueue.clear();
    m_actionWaitsForBlow = false;
    m_swingQueued = false;
    m_seenSerials = false;
    m_hasPartyPosition = false;
    m_moveVelocity = {};
    m_comboStep = 0;
    m_lastBladePoint.reset();
    m_lastLeftPoint.reset();
    m_lastTipPoints = {};
    m_fx.stopCastGlow();
    m_kit.reset();
    m_resumed = true;
}

bool FirstPersonViewModel::holdPose(const std::string &clipName, float seconds)
{
    if (!clip(clipName))
    {
        return false;
    }
    m_heldPose = std::make_pair(clipName, seconds);
    return true;
}

void FirstPersonViewModel::releasePose()
{
    m_heldPose.reset();
}

void FirstPersonViewModel::overrideKit(std::optional<Kit> kit)
{
    m_kitOverride = std::move(kit);
}

std::string FirstPersonViewModel::clipList() const
{
    std::vector<std::string> names;
    for (const auto &[name, info] : m_clips)
    {
        std::ostringstream entry;
        entry << name << " " << info.duration;
        if (info.hitSeconds >= 0.0f)
        {
            entry << " hit " << info.hitSeconds;
        }
        names.push_back(entry.str());
    }
    std::sort(names.begin(), names.end());
    std::string out;
    for (const std::string &name : names)
    {
        out += name + "\n";
    }
    return out;
}

std::string FirstPersonViewModel::pathJson(const std::string &clipName, int samples)
{
    const std::optional<ClipInfo> info = clip(clipName);
    if (!info || !m_instances.contains(m_handle) || samples < 2)
    {
        return {};
    }
    const auto point = [](const float *pViewProjection, const Engine::ModelMatrix *pNode,
                           const std::array<float, 3> &local) -> std::string
    {
        if (pNode == nullptr)
        {
            return "null";
        }
        const std::array<float, 3> world = transformPoint(*pNode, local);
        // Behind the eye (w at or below the near plane) a point has no place on screen.
        const float w = pViewProjection[3] * world[0] + pViewProjection[7] * world[1] + pViewProjection[11] * world[2]
            + pViewProjection[15];
        if (w <= ViewModelNearClip)
        {
            return "null";
        }
        const bx::Vec3 clipPoint = bx::mulH({world[0], world[1], world[2]}, pViewProjection);
        std::ostringstream out;
        out << '[' << clipPoint.x << ',' << clipPoint.y << ']';
        return out.str();
    };
    std::ostringstream json;
    json << "{\"clip\":\"" << clipName << "\",\"duration\":" << info->duration << ",\"hit\":" << info->hitSeconds
         << ",\"chain\":" << info->chainSeconds << ",\"aspect\":" << m_aspect << ",\"samples\":[";
    float projection[16];
    bx::mtxProj(projection, ViewModelFovDegrees, m_aspect, ViewModelNearClip, ViewModelFarClip, false,
        bx::Handedness::Right);
    for (int sample = 0; sample < samples; ++sample)
    {
        const float time = info->duration * float(sample) / float(samples - 1);
        m_instances.sampleBlended(m_handle, info->index, time, *m_instances.rootTransform(m_handle), 0.0f, 0.0f, {},
            true);
        const Engine::ModelMatrix *pCamera = m_instances.nodeMatrix(m_handle, m_cameraNode);
        if (pCamera == nullptr)
        {
            return {};
        }
        // The eye moves with the clip (Camera01): each sample uses its own view, as the render does.
        const bx::Vec3 eye = {(*pCamera)[12], (*pCamera)[13], (*pCamera)[14]};
        const bx::Vec3 forward = {0.0f, std::cos(ViewModelPitchRadians), -std::sin(ViewModelPitchRadians)};
        float view[16];
        float viewProjection[16];
        bx::mtxLookAt(view, eye, bx::add(eye, forward), {0.0f, 0.0f, 1.0f}, bx::Handedness::Right);
        bx::mtxMul(viewProjection, view, projection);
        const Engine::ModelMatrix *pWeapon = m_instances.nodeMatrix(m_handle, m_weaponNode);
        const Engine::ModelMatrix *pLeft = m_leftHandNode != UINT32_MAX
            ? m_instances.nodeMatrix(m_handle, m_leftHandNode) : nullptr;
        const Engine::ModelMatrix *pOffHand = m_offHandNode != UINT32_MAX
            ? m_instances.nodeMatrix(m_handle, m_offHandNode) : nullptr;
        json << (sample == 0 ? "" : ",") << "{\"t\":" << time << ",\"tip\":" << point(viewProjection, pWeapon, m_bladeTip)
             << ",\"hilt\":" << point(viewProjection, pWeapon, {0.0f, 0.0f, 0.0f})
             << ",\"left\":" << point(viewProjection, pLeft, {0.0f, 0.0f, 0.0f})
             << ",\"offTip\":" << point(viewProjection, pOffHand, m_offBladeTip) << '}';
    }
    json << "]}";
    return json.str();
}

void FirstPersonViewModel::shutdown()
{
    m_instances.clear();
    m_handle = {};
    m_bowHandle = {};
    m_bowAsset.reset();
    m_bowClips.clear();
    m_bowShown = false;
    m_torchNode = UINT32_MAX;
    m_asset.reset();
    m_clips.clear();
    m_attachments.clear();
    m_loadedPath.clear();
    m_failed = false;
    m_cameraNode = UINT32_MAX;
    m_weaponNode = UINT32_MAX;
    m_kit.reset();
    m_action.reset();
    m_seenSerials = false;
    m_hasPartyPosition = false;
    m_moveVelocity = {};
    m_lastBladePoint.reset();
    m_lastLeftPoint.reset();
    m_leftHandNode = UINT32_MAX;
    m_rightHandNode = UINT32_MAX;
    m_leftKnuckles = {UINT32_MAX, UINT32_MAX, UINT32_MAX, UINT32_MAX};
    m_rightKnuckles = {UINT32_MAX, UINT32_MAX, UINT32_MAX, UINT32_MAX};
    m_lastTipPoints = {};
    m_offHandNode = UINT32_MAX;
    m_clawTipRightNode = UINT32_MAX;
    m_clawTipLeftNode = UINT32_MAX;
    m_mouthNode = UINT32_MAX;
    m_offBladeTip = {};
    m_crossbowGrip.reset();
    m_fx.shutdown();
    m_hasViewProjection = false;
    if (bgfx::isValid(m_worldClipPlaneUniform) && Engine::BgfxContext::isBgfxInitialized())
    {
        bgfx::destroy(m_worldClipPlaneUniform);
    }
    m_worldClipPlaneUniform = BGFX_INVALID_HANDLE;
}
}
