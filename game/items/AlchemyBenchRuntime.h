#pragma once

#include "game/items/InventoryItemMixingRuntime.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"

#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <span>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;
class MergedPotionSettingTable;
class MergedReagentSettingTable;
class PotionMixingTable;
class PotionNoteTable;

struct AlchemyBenchTables
{
    const ItemTable &itemTable;
    const PotionMixingTable &potionMixingTable;
    const PotionNoteTable &potionNoteTable;
    const MergedPotionSettingTable &potionSettingTable;
    const MergedReagentSettingTable &reagentSettingTable;
};

enum class AlchemyIngredientKind : uint8_t
{
    Bottle,
    Reagent,
    Potion
};

// Every item of one kind the party carries, across all packs.
struct AlchemyIngredient
{
    uint32_t itemId = 0;
    AlchemyIngredientKind kind = AlchemyIngredientKind::Potion;
    uint32_t count = 0;
    uint16_t bestPower = 0;
};

// The held item is mixed into the target item, as when dropping one item onto another in a pack.
struct AlchemyRecipe
{
    uint32_t targetItemId = 0;
    uint32_t heldItemId = 0;
};

// One potion in the recipe book with the recipes the party knows for it.
struct AlchemyBookEntry
{
    uint32_t resultItemId = 0;
    uint8_t requiredMastery = 0;
    bool reagentRecipe = false;
    bool masteryAllows = true;
    uint32_t brewableCount = 0;
    std::vector<AlchemyRecipe> recipes;
};

struct AlchemyBook
{
    std::vector<AlchemyBookEntry> entries;
    size_t totalResultCount = 0;
    // Potions brewed from two potions by any recipe, known or not, apart from the bottle-and-reagent ones: what the
    // Workbench leaves in the packs when it keeps mixed potions (GameSettings::workbenchKeepMixedPotions).
    std::unordered_set<uint32_t> mixedPotionItemIds;

    bool isMixedPotion(uint32_t itemId) const
    {
        return mixedPotionItemIds.contains(itemId);
    }

    bool usesMixedPotion(const AlchemyRecipe &recipe) const
    {
        return isMixedPotion(recipe.targetItemId) || isMixedPotion(recipe.heldItemId);
    }
};

struct AlchemistInfo
{
    std::optional<size_t> memberIndex;
    SkillMastery mastery = SkillMastery::None;
    uint32_t level = 0;
};

enum class AlchemyPreviewOutcome : uint8_t
{
    Incomplete,
    MissingIngredient,
    Unknown,
    Known,
    TooDifficult,
    // The party saw this exact mixture explode, and the alchemist would still fail it.
    KnownExplosive
};

struct AlchemyPreview
{
    AlchemyPreviewOutcome outcome = AlchemyPreviewOutcome::Incomplete;
    uint32_t resultItemId = 0;
    uint16_t resultPower = 0;
    uint8_t requiredMastery = 0;
    uint16_t targetPower = 0;
    uint16_t heldPower = 0;
    bool returnsBottle = false;
    // What the result's rules ask (potion_effects.yml): the power it needs to work and the drinks in its bottle.
    int minimumPower = 0;
    int charges = 1;
};

struct AlchemyMixOutcome
{
    InventoryItemMixResult result;
    // The potion the mix produced, when it succeeded.
    InventoryItem resultItem;
    // A returned bottle that no pack had room for.
    std::optional<InventoryItem> overflowItem;
};

enum class AlchemyChainBlock : uint8_t
{
    None,
    MissingBottle,
    MissingReagent,
    UnknownRecipe,
    NeedsMastery
};

struct AlchemyChainStep
{
    AlchemyRecipe recipe;
    uint32_t resultItemId = 0;
};

struct AlchemyItemCount
{
    uint32_t itemId = 0;
    uint32_t count = 0;
};

// One carried copy of an item, by its power.
struct AlchemyItemPower
{
    uint32_t itemId = 0;
    uint16_t power = 0;
};

// How to brew a potion from what the party carries, brewing any missing ingredient first from known recipes.
struct AlchemyChainPlan
{
    uint32_t brewCount = 0;
    // The expected power of the first potion; later ones can differ as stronger ingredients run out.
    uint16_t resultPower = 0;
    std::vector<AlchemyChainStep> steps;
    // The pair the first potion is finally mixed from.
    AlchemyRecipe finalRecipe;
    // Carried items the plan uses up, and potions it brews along the way.
    std::vector<AlchemyItemCount> used;
    std::vector<AlchemyItemCount> brewedFirst;
    // Carried mixed potions the plan leaves alone (keepMixedPotions): its mixes take the copies it brews.
    std::vector<AlchemyItemPower> kept;
    // Why not even one potion can be brewed.
    AlchemyChainBlock block = AlchemyChainBlock::None;
    uint32_t blockItemId = 0;
};

struct AlchemyChainOutcome
{
    uint32_t stepsDone = 0;
    uint32_t brewedCount = 0;
    InventoryItem lastBrewed;
    AlchemyMixOutcome lastMix;
};

// Plans brewing chains over a snapshot of the party's ingredients. Only known recipes the alchemist can safely mix
// are used, so a plan never explodes. Carried potions are used before brewing replacements, strongest first; keeping
// mixed potions, the carried ones (AlchemyBook::isMixedPotion) are left out and brewed fresh from reagents and the
// basic potions.
class AlchemyChainPlanner
{
public:
    AlchemyChainPlanner(
        const Party &party,
        const AlchemyBook &book,
        const AlchemistInfo &alchemist,
        const AlchemyBenchTables &tables,
        bool keepMixedPotions = false);

    AlchemyChainPlan plan(uint32_t resultItemId, uint32_t maxBrews) const;

private:
    class Stock;
    struct Search;

    bool obtain(uint32_t itemId, Stock &stock, Search &search, int depth) const;
    bool brew(uint32_t resultItemId, Stock &stock, Search &search, int depth) const;
    bool tryRecipe(
        const AlchemyBookEntry &entry,
        const AlchemyRecipe &recipe,
        Stock &stock,
        Search &search,
        int depth) const;

    const AlchemyBook &m_book;
    const AlchemyBenchTables &m_tables;
    uint32_t m_alchemistLevel = 0;
    uint32_t m_bottleItemId = 0;
    std::vector<std::pair<uint32_t, uint16_t>> m_carried;
    std::vector<AlchemyItemPower> m_kept;
};

class AlchemyBenchRuntime
{
public:
    using AutonoteLookup = std::function<bool(uint32_t)>;

    // The party's best conscious alchemist mixes; without one, only bottle and reagent mixes are safe.
    static AlchemistInfo resolveAlchemist(const Party &party);

    static std::vector<AlchemyIngredient> collectIngredients(const Party &party, const AlchemyBenchTables &tables);
    static const AlchemyIngredient *findIngredient(
        const std::vector<AlchemyIngredient> &ingredients,
        uint32_t itemId);
    static uint32_t brewableCount(const AlchemyRecipe &recipe, const std::vector<AlchemyIngredient> &ingredients);
    // Case-insensitive substring match; an empty search matches everything.
    static bool matchesSearch(const std::string &name, const std::string &search);

    // The potion a recipe scroll teaches: "Divine Restoration Recipe" teaches the Divine Restoration potion.
    static std::optional<uint32_t> recipeScrollPotionItemId(uint32_t scrollItemId, const AlchemyBenchTables &tables);
    // The notes of every mix that brews the potion; unlocking them teaches the bench all of its recipes.
    static std::vector<uint32_t> potionNoteIds(uint32_t potionItemId, const AlchemyBenchTables &tables);

    // Bottle and reagent recipes are always known; potion recipes are known once their potion note is. Keeping mixed
    // potions, the entries' direct counts leave out the recipes that would use carried mixed potions.
    static AlchemyBook buildBook(
        const AlchemyBenchTables &tables,
        const std::vector<AlchemyIngredient> &ingredients,
        SkillMastery alchemistMastery,
        const AutonoteLookup &isAutonoteUnlocked,
        bool keepMixedPotions = false);
    // The ingredients without the book's mixed potions: what the bench picks recipes from while keeping them.
    static std::vector<AlchemyIngredient> withoutMixedPotions(
        const std::vector<AlchemyIngredient> &ingredients,
        const AlchemyBook &book);

    // The entry's recipe that brews the most potions, preferring stronger ingredients.
    static std::optional<AlchemyRecipe> pickRecipe(
        const AlchemyBookEntry &entry,
        const std::vector<AlchemyIngredient> &ingredients);

    static AlchemyPreview preview(
        const Party &party,
        const AlchemyRecipe &recipe,
        const AlchemyBenchTables &tables,
        const AutonoteLookup &isAutonoteUnlocked);

    // Mixes the strongest carried held item into the strongest carried target item, past the kept copies. Unhandled
    // results leave both items where they were.
    static AlchemyMixOutcome mix(
        Party &party,
        const AlchemyRecipe &recipe,
        const AlchemyBenchTables &tables,
        std::span<const AlchemyItemPower> kept = {});

    // Runs a plan's steps as real mixes, stopping at the first one that does not succeed.
    static AlchemyChainOutcome brewChain(Party &party, const AlchemyChainPlan &plan, const AlchemyBenchTables &tables);
};
}
