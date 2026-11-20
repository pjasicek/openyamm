#pragma once

#include "engine/models/ModelAsset.h"

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
// How a ground item model (engine/world_items/items.yml) is held by the solo run's first-person arms
// (devdocs/solo_action/WEAPONS.md "Grip alignment"). A ground model lies flat: its longest side along glTF X or Z,
// its thinnest along Y. The table (engine/world_items/held.yml, written by
// level_generation/solo_action_weapons_20261113/scripts/make_held_table.py, hand corrections kept in that script)
// says which horizontal axis is the shaft, which end is the head, which side the edge faces, where the hand grips
// and how long the held weapon is. The matrix is built from the loaded model's bounds, so a re-cooked model keeps
// its grip.
enum class HeldWeaponMount
{
    // In the right hand's Weapon node: the palm at the origin, the head along +Y, the edge along +X.
    Hand,
    // On the left forearm (Oblivion's Bip01 L ForearmTwist): the face toward -Y, the top along -Z (Oblivion's steel
    // shield is widest there).
    Shield,
    // In the left hand's Torch node, where Oblivion's bow hangs: the limbs along Y, the riser at the origin, the
    // limbs' tips bending toward -X (the archer).
    Bow,
    // In the same left hand: a crossbow's stock along +X (where Oblivion's bow shoots), its limbs across along Z.
    Crossbow,
    // In the right hand's Weapon node like a pistol: the muzzle along +X (out of the knuckles, forward when the arm
    // aims), the handle down through the fist (-Y). `edge` names the side the handle hangs to in the model.
    Gun,
};

struct HeldWeaponGrip
{
    std::string kind;
    HeldWeaponMount mount = HeldWeaponMount::Hand;
    // The model's long (shaft) axis: 0 (glTF X) or 2 (glTF Z).
    int longAxis = 0;
    // +1: the head (blade tip, axe head, a shield's top) is at the long axis' maximum; -1: at its minimum.
    int head = 1;
    // +1: the edge (an axe's blade, the bow's riser side) is at the other horizontal axis' maximum; -1: minimum.
    int edge = 1;
    // Where the palm closes, as a fraction of the length from the butt (a bow and a shield: the centre).
    float grip = 0.2f;
    // The held length (shields: height) in the arms' units (Oblivion units, about 1.43 cm).
    float length = 80.0f;
    // A turn about the shaft, in degrees, after the placement.
    float rollDegrees = 0.0f;
    // The cross-section's scale against the length's (1: uniform). The ground models of staves and polearms are drawn
    // from their icons, which makes their shafts about twice as thick as a hand can close around; this thins them.
    float girth = 1.0f;
    // Where the riser (a bow) or the centre of the face (a shield) lies across the model, as a fraction of the edge
    // axis from its minimum; 0.5 for anything symmetric.
    float across = 0.5f;
};

using HeldWeaponGrips = std::unordered_map<std::string, HeldWeaponGrip>;

// The table from YAML text (schema openyamm.heldWeapons.v1); false with a message on a malformed entry.
bool parseHeldWeaponGrips(const std::string &text, const std::string &path, HeldWeaponGrips &grips,
    std::string &error);
bool loadHeldWeaponGrips(const Engine::AssetFileSystem &assets, const std::string &path, HeldWeaponGrips &grips,
    std::string &error);

// The model's placement in its mount node's space, from its bounds and grip (a rotation without mirroring, a uniform
// scale and a translation); none for invalid bounds.
std::optional<Engine::ModelMatrix> heldWeaponMatrix(const Engine::ModelBounds &bounds, const HeldWeaponGrip &grip);

// A held.yml kind's own template (held_tiers.yml kind_templates): drawn instead of the skill group's template.
struct HeldKindTemplate
{
    std::string file;
    // The highest skin tier it is drawn in (0: any); clubs draw the mace's low tier.
    uint8_t maxTier = 0;
};

// Tier skins of the view model's weapon templates (engine/world_items/held_tiers.yml, schema
// openyamm.heldTiers.v1; devdocs/solo_action/WEAPONS.md "Tier skins"): which held kinds the templates draw, and
// which skin tier an item gets. A template w_<name>.glb has its skins beside it as w_<name>_t<tier>.glb.
struct HeldSkinRules
{
    // held.yml kinds drawn with the templates; every other kind is held as our own ground model.
    std::vector<std::string> templateKinds;
    // Kinds with a template of their own (spears, tridents, halberds, crossbows, wands, blasters, clubs).
    std::unordered_map<std::string, HeldKindTemplate> kindTemplates;
    uint8_t tierCount = 4;
    // The item's value (times its equip stat's scale) at or above valueBands[i] gives tier i + 2; below the first,
    // tier 1.
    std::vector<int> valueBands;
    std::unordered_map<std::string, float> valueScale;
    // Artifacts, relics and special items.
    uint8_t uniqueTier = 4;
    // An enchanted copy is raised by this many tiers, at most to enchantedMaxTier (never lowered by it).
    uint8_t enchantedBonus = 1;
    uint8_t enchantedMaxTier = 3;
    // The least tier of an item rolled with a loot rarity (ItemRulesetFields::lootRarity, MAW's Common 1 to Celestial
    // 8), at index lootRarity - 1: such an item's value grows with its level, so its rarity speaks for its look.
    std::vector<uint8_t> lootRarityTiers;
};

// The item facts the tier depends on.
struct HeldSkinItem
{
    int value = 0;
    std::string equipStat;
    bool unique = false;
    bool enchanted = false;
    // The copy's loot rarity, 0 for none (ItemRulesetFields::lootRarity).
    uint8_t lootRarity = 0;
};

bool parseHeldSkinRules(const std::string &text, const std::string &path, HeldSkinRules &rules, std::string &error);
bool loadHeldSkinRules(const Engine::AssetFileSystem &assets, const std::string &path, HeldSkinRules &rules,
    std::string &error);
// The skin tier, 1..tierCount.
uint8_t heldSkinTier(const HeldSkinRules &rules, const HeldSkinItem &item);
bool heldSkinUsesTemplate(const HeldSkinRules &rules, const std::string &kind);
// The kind's own template, or null when it draws its skill group's.
const HeldKindTemplate *heldKindTemplate(const HeldSkinRules &rules, const std::string &kind);
// The skin file of a template for a tier: "w_longsword.glb", 2 -> "w_longsword_t2.glb"; tier 0 keeps the template.
std::string heldSkinFile(const std::string &templateFile, uint8_t tier);
}
