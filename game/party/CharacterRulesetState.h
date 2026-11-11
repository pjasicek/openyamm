#pragma once

#include "game/party/InventoryItem.h"
#include "game/party/SkillData.h"

#include <algorithm>
#include <array>
#include <cstdint>
#include <map>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
// What a ruleset keeps per character (devdocs/maw/HANDOFF.md §3.9); empty under Standard, and saves store it only for
// characters that have it.
// What a potion left on its drinker for a while (potion_effects.yml immunity, skill_bonus, aura_buff, regeneration):
// the key is the condition, the skill id or the aura's spell id; the amount the bonus levels, the potion power or the
// regeneration skill.
struct TimedPotionEffect
{
    enum class Kind : uint8_t
    {
        Immunity,
        SkillBonus,
        Aura,
        Regeneration,
    };

    Kind kind = Kind::Immunity;
    uint32_t key = 0;
    int amount = 0;
    // Game seconds left.
    float remainingSeconds = 0;

    bool operator==(const TimedPotionEffect &) const = default;
};

// The rules' state of a character between hits and casts. It lives with the character, so hiring, dismissal and
// loading carry it along (nothing keyed by address or slot); runtime only, never saved, and no part of the
// ruleset state's equality. MAW: the Assassin's combo points and Subtlety stacks, the Elementalist's stacks and
// rotation, Cover and Retaliation, and the regeneration and dragon refill timers (audit CLS-11, CMB-23, SKL-8).
struct CharacterRulesRuntime
{
    // The Assassin's combo points (0-5) and Subtlety speed stacks (0-5), which lapse 8 seconds after the last paid
    // hit.
    double comboPoints = 0;
    double subtletyStacks = 0;
    float subtletySeconds = 0;
    double energyCarry = 0;
    // The Elementalist's casting stacks and the seconds since the last offensive cast.
    int elementalStacks = 0;
    float elementalIdleSeconds = 0;
    float elementalDecaySeconds = 0;
    // The recovery of the Elementalist's last cast, in ticks: stacks start to fade after four of them.
    int elementalLastDelayTicks = 0;
    // The Elementalist's rotation of the quick and attack spells: the kind of spell the player bound to each and the
    // spell the rotation put there (a different spell there means the player bound a new one).
    std::array<int, 2> rotationKinds = {};
    std::array<std::string, 2> rotationSpells;
    // Retaliation stacks from covering and their seconds left; a Grandmaster coverer's melee hit adds 15 % to their
    // next cover roll.
    int retaliationStacks = 0;
    float retaliationSeconds = 0;
    bool coverBonus = false;
    // Regeneration: HP and SP each wait 20 seconds after a loss of their own; the parts of a point carried over.
    int lastHealth = -1;
    float secondsSinceHealthLoss = 0;
    int lastSpellPoints = -1;
    float secondsSinceSpellLoss = 0;
    double healthCarry = 0;
    double spellCarry = 0;
    // A dragon's spell points at the last refill and the seconds since they last fell.
    int dragonLastSpellPoints = -1;
    float dragonSecondsSinceLoss = 0;

    bool operator==(const CharacterRulesRuntime &) const
    {
        return true;
    }
};

// What a tagged bag takes when the party picks an item up from the ground (ItemRules::bagTag): MAW's crafting bag
// (zzzMaw_CraftingBag.lua) and our alchemy bag.
enum class BagTag : uint8_t
{
    Crafting,
    Alchemy,
};

struct CharacterRulesetState
{
    // The highest mastery each skill had before a respec (MAW), by canonical skill name: it returns, one rank per
    // raise, once the skill reaches the rank's requirement again.
    std::unordered_map<std::string, SkillMastery> rememberedMasteries;
    // The masteries a switch from free to horizontal progression took (MAW's storedMasteries), given back when the
    // game switches back.
    std::unordered_map<std::string, SkillMastery> progressionStoredMasteries;
    // The masteries a lone character's utility skills had before their solo ones replaced them (soloMiscMasteries),
    // given back when the party grows.
    std::unordered_map<std::string, SkillMastery> soloStoredMasteries;
    // MAW's Cover and Mana Shield, switched off by the player (MawSkillRules::skillSwitch).
    bool coverDisabled = false;
    bool manaShieldDisabled = false;
    // An Elementalist's random rotation of the quick and attack spells, switched off by the player (R on the skills
    // page); it also stops the casting stacks.
    bool elementalRotationDisabled = false;
    // The Death Knight's switched-on spells (Blood Leech, Superior Blood Leech, Death Grasp), by spell id.
    std::vector<uint32_t> classToggles;
    // An Elementalist's progress in Fire, Air, Water and Earth from casting.
    std::array<double, 4> elementalProgress = {};
    std::vector<TimedPotionEffect> potionEffects;
    // The strongest step of each best-step potion the character drank (MAW's black potions), by item id.
    std::unordered_map<uint32_t, int> potionSteps;
    // MAW's real-time poison: seconds until the poison wears off (vars.poisonTime).
    float poisonSeconds = 0;
    // MAW's multibag (zzMaw-MultiBag.lua): the bag the character's inventory is (0-4, a solo character's 0-24 as tab
    // x 5 + bag), and the other bags' items by bag, each laid out on its own grid.
    uint8_t currentBag = 0;
    std::map<uint8_t, std::vector<InventoryItem>> storedBags;
    // The bags tagged as crafting and alchemy bags, a bit per bag (a solo character's 25 too: OY-344).
    uint32_t craftingBags = 0;
    uint32_t alchemyBags = 0;
    // The game minute from which a Seraphim's Divine Protection works again (vars.divineProtectionCooldown).
    float divineProtectionReadyGameMinutes = 0;
    // The same for legendary 15 (vars.legendaryProtectionCooldown).
    float legendaryProtectionReadyGameMinutes = 0;

    // The strongest timed potion effect of this kind and key in force, or 0.
    int potionEffect(TimedPotionEffect::Kind kind, uint32_t key) const
    {
        int best = 0;

        for (const TimedPotionEffect &effect : potionEffects)
        {
            if (effect.kind == kind && effect.key == key && effect.remainingSeconds > 0)
            {
                best = std::max(best, std::max(effect.amount, 1));
            }
        }

        return best;
    }

    bool classToggleOn(uint32_t spellId) const
    {
        return std::find(classToggles.begin(), classToggles.end(), spellId) != classToggles.end();
    }

    bool empty() const
    {
        return *this == CharacterRulesetState{};
    }

    // The rules' runtime state between hits and casts (not saved).
    mutable CharacterRulesRuntime runtime;

    bool operator==(const CharacterRulesetState &) const = default;
};
}
