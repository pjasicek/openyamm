#include "game/render/HeldWeapons.h"

#include "engine/AssetFileSystem.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
// Where Oblivion's steel shield sits on the forearm (reference/oblivion_poc/glb/s_steelshield.glb bounds): our
// shields are centred there.
constexpr std::array<float, 3> ShieldCentre = {21.8f, -3.8f, 4.3f};

std::optional<HeldWeaponMount> parseMount(const std::string &kind)
{
    if (kind == "shield")
    {
        return HeldWeaponMount::Shield;
    }
    if (kind == "bow")
    {
        return HeldWeaponMount::Bow;
    }
    if (kind == "crossbow")
    {
        return HeldWeaponMount::Crossbow;
    }
    if (kind == "blaster")
    {
        return HeldWeaponMount::Gun;
    }
    return HeldWeaponMount::Hand;
}

int parseSign(const YAML::Node &node, const char *pKey, int fallback)
{
    if (!node[pKey])
    {
        return fallback;
    }
    return node[pKey].as<int>() < 0 ? -1 : 1;
}
}

bool parseHeldWeaponGrips(const std::string &text, const std::string &path, HeldWeaponGrips &grips,
    std::string &error)
{
    try
    {
        const YAML::Node root = YAML::Load(text);
        if (!root["schema"] || root["schema"].as<std::string>() != "openyamm.heldWeapons.v1")
        {
            error = path + ": schema must be openyamm.heldWeapons.v1";
            return false;
        }
        for (const YAML::Node &entry : root["held"])
        {
            const std::string icon = entry["icon"].as<std::string>();
            HeldWeaponGrip grip;
            grip.kind = entry["kind"].as<std::string>();
            grip.mount = *parseMount(grip.kind);
            const std::string axis = entry["long"].as<std::string>("x");
            if (axis != "x" && axis != "z")
            {
                error = path + ": " + icon + ": long must be x or z";
                return false;
            }
            grip.longAxis = axis == "x" ? 0 : 2;
            grip.head = parseSign(entry, "head", 1);
            grip.edge = parseSign(entry, "edge", 1);
            grip.grip = entry["grip"].as<float>(0.2f);
            grip.length = entry["length"].as<float>(80.0f);
            grip.rollDegrees = entry["roll"].as<float>(0.0f);
            grip.across = entry["across"].as<float>(0.5f);
            grip.girth = entry["girth"].as<float>(1.0f);
            if (grip.length <= 0.0f || grip.grip < 0.0f || grip.grip > 1.0f || grip.across < 0.0f || grip.across > 1.0f
                || grip.girth <= 0.0f || grip.girth > 1.0f)
            {
                error = path + ": " + icon + ": length must be positive, grip and across within 0..1, girth in (0, 1]";
                return false;
            }
            if (!grips.emplace(icon, grip).second)
            {
                error = path + ": " + icon + " listed twice";
                return false;
            }
        }
    }
    catch (const std::exception &exception)
    {
        error = path + ": " + exception.what();
        return false;
    }
    return true;
}

bool loadHeldWeaponGrips(const Engine::AssetFileSystem &assets, const std::string &path, HeldWeaponGrips &grips,
    std::string &error)
{
    const std::optional<std::string> text = assets.readTextFile(path);
    if (!text)
    {
        error = path + ": missing or unreadable";
        return false;
    }
    return parseHeldWeaponGrips(*text, path, grips, error);
}

std::optional<Engine::ModelMatrix> heldWeaponMatrix(const Engine::ModelBounds &bounds, const HeldWeaponGrip &grip)
{
    const int longAxis = grip.longAxis;
    const int edgeAxis = 2 - longAxis;
    const int thinAxis = 1;
    const float longExtent = bounds.max[longAxis] - bounds.min[longAxis];
    if (!bounds.valid || longExtent <= 1.0e-4f)
    {
        return std::nullopt;
    }
    const float scale = grip.length / longExtent;
    const float butt = grip.head > 0 ? bounds.min[longAxis] : bounds.max[longAxis];
    // The palm (a bow's riser, a shield's centre) along the shaft, across it, and through the thickness.
    const float alongPoint = butt + grip.head * grip.grip * longExtent;
    const float acrossPoint = bounds.min[edgeAxis] + grip.across * (bounds.max[edgeAxis] - bounds.min[edgeAxis]);
    const float thinPoint = (bounds.min[thinAxis] + bounds.max[thinAxis]) * 0.5f;

    // Which node axis each model axis turns into, with its sign; the third sign keeps the turn a rotation (no
    // mirroring, which would turn the faces inside out).
    std::array<int, 3> target = {};
    std::array<float, 3> sign = {};
    std::array<float, 3> offset = {};
    if (grip.mount == HeldWeaponMount::Shield)
    {
        // The long side stands up (the forearm's -Z), the face (the model's top, +Y) looks out toward -Y.
        target[longAxis] = 2;
        sign[longAxis] = -float(grip.head);
        target[thinAxis] = 1;
        sign[thinAxis] = -1.0f;
        target[edgeAxis] = 0;
        offset = ShieldCentre;
    }
    else if (grip.mount == HeldWeaponMount::Gun)
    {
        // The muzzle out of the knuckles (+X), the handle down through the fist. Until 2026-11-14 the muzzle went to
        // -X, which points it back at the eye (devdocs/solo_action/WEAPONS.md "Gun mount").
        target[longAxis] = 0;
        sign[longAxis] = float(grip.head);
        target[edgeAxis] = 1;
        sign[edgeAxis] = -float(grip.edge);
        target[thinAxis] = 2;
    }
    else if (grip.mount == HeldWeaponMount::Crossbow)
    {
        // The stock points the way the bow shoots, the limbs lie across, the flat side stays level.
        target[longAxis] = 0;
        sign[longAxis] = float(grip.head);
        target[edgeAxis] = 2;
        target[thinAxis] = 1;
        sign[thinAxis] = 1.0f;
    }
    else
    {
        target[longAxis] = 1;
        sign[longAxis] = float(grip.head);
        target[edgeAxis] = 0;
        sign[edgeAxis] = float(grip.edge);
        target[thinAxis] = 2;
    }
    const int free = grip.mount == HeldWeaponMount::Shield || grip.mount == HeldWeaponMount::Crossbow ? edgeAxis
                                                                                                    : thinAxis;
    sign[free] = 1.0f;
    // The determinant of the signed axis permutation; flip the free axis if it mirrors.
    std::array<std::array<float, 3>, 3> rotation = {};
    for (int axis = 0; axis < 3; ++axis)
    {
        rotation[target[axis]][axis] = sign[axis];
    }
    const float determinant = rotation[0][0] * (rotation[1][1] * rotation[2][2] - rotation[1][2] * rotation[2][1])
        - rotation[0][1] * (rotation[1][0] * rotation[2][2] - rotation[1][2] * rotation[2][0])
        + rotation[0][2] * (rotation[1][0] * rotation[2][1] - rotation[1][1] * rotation[2][0]);
    if (determinant < 0.0f)
    {
        sign[free] = -1.0f;
        rotation[target[free]][free] = -1.0f;
    }

    std::array<float, 3> modelPivot = {};
    modelPivot[longAxis] = grip.mount == HeldWeaponMount::Shield
        ? (bounds.min[longAxis] + bounds.max[longAxis]) * 0.5f : alongPoint;
    modelPivot[edgeAxis] = acrossPoint;
    modelPivot[thinAxis] = thinPoint;

    // Node point = R * scale * (model point - pivot) + offset, then the roll about the node's Y (the shaft).
    const float roll = grip.rollDegrees * 3.14159265f / 180.0f;
    const float cosine = std::cos(roll);
    const float sine = std::sin(roll);
    const std::array<std::array<float, 3>, 3> turn = {{{cosine, 0.0f, sine}, {0.0f, 1.0f, 0.0f}, {-sine, 0.0f, cosine}}};
    std::array<std::array<float, 3>, 3> linear = {};
    for (int row = 0; row < 3; ++row)
    {
        for (int column = 0; column < 3; ++column)
        {
            float sum = 0.0f;
            for (int index = 0; index < 3; ++index)
            {
                sum += turn[row][index] * rotation[index][column];
            }
            // The shaft (long) axis keeps the length's scale; the two cross axes take the girth.
            linear[row][column] = sum * scale * (column == longAxis ? 1.0f : grip.girth);
        }
    }
    Engine::ModelMatrix matrix = {};
    for (int row = 0; row < 3; ++row)
    {
        float translation = 0.0f;
        for (int column = 0; column < 3; ++column)
        {
            matrix[size_t(column * 4 + row)] = linear[row][column];
            translation -= linear[row][column] * modelPivot[column];
        }
        float turnedOffset = 0.0f;
        for (int index = 0; index < 3; ++index)
        {
            turnedOffset += turn[row][index] * offset[index];
        }
        matrix[size_t(12 + row)] = translation + turnedOffset;
    }
    matrix[15] = 1.0f;
    return matrix;
}
}

namespace OpenYAMM::Game
{
bool parseHeldSkinRules(const std::string &text, const std::string &path, HeldSkinRules &rules, std::string &error)
{
    try
    {
        const YAML::Node root = YAML::Load(text);
        if (!root["schema"] || root["schema"].as<std::string>() != "openyamm.heldTiers.v1")
        {
            error = path + ": schema must be openyamm.heldTiers.v1";
            return false;
        }
        HeldSkinRules parsed;
        parsed.templateKinds = root["template_kinds"].as<std::vector<std::string>>(std::vector<std::string>());
        const int tierCount = root["tiers"].as<int>(3);
        parsed.valueBands = root["value_bands"].as<std::vector<int>>(std::vector<int>());
        const int uniqueTier = root["unique_tier"].as<int>(tierCount);
        const int enchantedBonus = root["enchanted_bonus"].as<int>(0);
        const int enchantedMaxTier = root["enchanted_max_tier"].as<int>(tierCount);
        if (tierCount < 1 || tierCount > 9 || int(parsed.valueBands.size()) != tierCount - 1 || uniqueTier < 1
            || uniqueTier > tierCount || enchantedBonus < 0 || enchantedMaxTier < 1 || enchantedMaxTier > tierCount)
        {
            error = path + ": tiers must be 1..9 with one value band fewer, unique_tier and enchanted_max_tier within "
                          "them, enchanted_bonus not negative";
            return false;
        }
        for (size_t index = 1; index < parsed.valueBands.size(); ++index)
        {
            if (parsed.valueBands[index] <= parsed.valueBands[index - 1])
            {
                error = path + ": value_bands must rise";
                return false;
            }
        }
        if (root["value_scale"])
        {
            for (const auto &entry : root["value_scale"])
            {
                const float scale = entry.second.as<float>();
                if (!(scale > 0.0f))
                {
                    error = path + ": value_scale " + entry.first.as<std::string>() + " must be positive";
                    return false;
                }
                parsed.valueScale[entry.first.as<std::string>()] = scale;
            }
        }
        if (root["kind_templates"])
        {
            for (const auto &entry : root["kind_templates"])
            {
                HeldKindTemplate own;
                own.file = entry.second["file"].as<std::string>(std::string());
                const int maxTier = entry.second["max_tier"].as<int>(0);
                if (own.file.empty() || maxTier < 0 || maxTier > tierCount)
                {
                    error = path + ": kind_templates " + entry.first.as<std::string>()
                        + " needs a file and a max_tier within the tiers";
                    return false;
                }
                own.maxTier = uint8_t(maxTier);
                parsed.kindTemplates[entry.first.as<std::string>()] = own;
            }
        }
        for (const int tier : root["loot_rarity_tiers"].as<std::vector<int>>(std::vector<int>()))
        {
            if (tier < 1 || tier > tierCount)
            {
                error = path + ": loot_rarity_tiers must be within the tiers";
                return false;
            }
            parsed.lootRarityTiers.push_back(uint8_t(tier));
        }
        parsed.tierCount = uint8_t(tierCount);
        parsed.uniqueTier = uint8_t(uniqueTier);
        parsed.enchantedBonus = uint8_t(enchantedBonus);
        parsed.enchantedMaxTier = uint8_t(enchantedMaxTier);
        rules = std::move(parsed);
    }
    catch (const std::exception &exception)
    {
        error = path + ": " + exception.what();
        return false;
    }
    return true;
}

bool loadHeldSkinRules(const Engine::AssetFileSystem &assets, const std::string &path, HeldSkinRules &rules,
    std::string &error)
{
    const std::optional<std::string> text = assets.readTextFile(path);
    if (!text)
    {
        error = path + ": missing or unreadable";
        return false;
    }
    return parseHeldSkinRules(*text, path, rules, error);
}

uint8_t heldSkinTier(const HeldSkinRules &rules, const HeldSkinItem &item)
{
    if (item.unique)
    {
        return rules.uniqueTier;
    }
    const auto scale = rules.valueScale.find(item.equipStat);
    const float value = float(item.value) * (scale != rules.valueScale.end() ? scale->second : 1.0f);
    int tier = 1;
    for (const int band : rules.valueBands)
    {
        if (value >= float(band))
        {
            ++tier;
        }
    }
    if (item.enchanted)
    {
        tier = std::max(tier, std::min(tier + int(rules.enchantedBonus), int(rules.enchantedMaxTier)));
    }
    if (item.lootRarity > 0 && item.lootRarity <= rules.lootRarityTiers.size())
    {
        tier = std::max(tier, int(rules.lootRarityTiers[item.lootRarity - 1]));
    }
    return uint8_t(std::clamp(tier, 1, int(rules.tierCount)));
}

bool heldSkinUsesTemplate(const HeldSkinRules &rules, const std::string &kind)
{
    return std::find(rules.templateKinds.begin(), rules.templateKinds.end(), kind) != rules.templateKinds.end();
}

const HeldKindTemplate *heldKindTemplate(const HeldSkinRules &rules, const std::string &kind)
{
    const auto found = rules.kindTemplates.find(kind);
    return found != rules.kindTemplates.end() ? &found->second : nullptr;
}

std::string heldSkinFile(const std::string &templateFile, uint8_t tier)
{
    const size_t dot = templateFile.rfind('.');
    if (tier == 0 || dot == std::string::npos)
    {
        return templateFile;
    }
    return templateFile.substr(0, dot) + "_t" + std::to_string(tier) + templateFile.substr(dot);
}
}
