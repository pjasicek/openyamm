#include "game/ui/GameplayAlchemyBenchRenderer.h"

#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/tables/ItemTable.h"
#include "game/ui/GameplayAlchemyBenchView.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiRuntime.h"
#include "game/ui/GameplayUiSkin.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t WellFillColor = 0x60000000u;
constexpr uint32_t WellBorderColor = 0xff36464du;
constexpr uint32_t SelectedBorderColor = 0xff4890b8u;
constexpr uint32_t SelectedRowColor = 0x5050a0c8u;
constexpr uint32_t HoverColor = 0x18ffffffu;
constexpr uint32_t DimTextColor = 0xff95abb7u;
constexpr uint32_t HeaderTextColor = 0xff5a7d8fu;
constexpr uint32_t DisabledTextColor = 0xff70808au;
constexpr uint32_t WarningTextColor = 0xff4aa8e0u;
constexpr uint32_t ChipOnColor = 0xff5ea6c9u;
constexpr uint32_t ChipOnTextColor = 0xff0a141au;

using Rect = GameplayResolvedHudLayoutElement;

class BenchPainter
{
public:
    BenchPainter(GameplayScreenRuntime &context, int width, int height)
        : m_context(context)
        , m_width(width)
        , m_height(height)
        , m_pInput(context.currentGameplayInputFrame())
    {
    }

    std::optional<Rect> rect(const char *pLayoutId) const
    {
        return m_context.resolveHudLayoutElement(pLayoutId, m_width, m_height, 0, 0);
    }

    bool hovered(const Rect &area) const
    {
        return m_pInput != nullptr
            && GameplayHudCommon::isPointerInsideResolvedElement(area, m_pInput->pointerX, m_pInput->pointerY);
    }

    bool pressed(const Rect &area) const
    {
        return hovered(area) && m_pInput->leftMouseButton.held;
    }

    void fill(const Rect &area, uint32_t colorAbgr) const
    {
        const std::string name = "__alchemy_bench_" + std::to_string(colorAbgr) + "__";
        const std::optional<GameplayHudTextureHandle> texture =
            m_context.gameplayUiRuntime().ensureSolidHudTextureLoaded(name, colorAbgr);

        if (texture && area.width > 0 && area.height > 0)
        {
            m_context.submitHudTexturedQuad(*texture, area.x, area.y, area.width, area.height);
        }
    }

    void frame(const Rect &area, uint32_t colorAbgr) const
    {
        const float line = std::max(1.0f, std::round(area.scale * 0.75f));
        fill({area.x, area.y, area.width, line, area.scale}, colorAbgr);
        fill({area.x, area.y + area.height - line, area.width, line, area.scale}, colorAbgr);
        fill({area.x, area.y + line, line, area.height - 2 * line, area.scale}, colorAbgr);
        fill({area.x + area.width - line, area.y + line, line, area.height - 2 * line, area.scale}, colorAbgr);
    }

    void well(const Rect &area, uint32_t borderAbgr = WellBorderColor) const
    {
        fill(area, WellFillColor);
        frame(area, borderAbgr);
    }

    // Draws text with a layout element's font, scale and alignment in any rectangle.
    void text(const char *pStyleId, const Rect &area, const std::string &value,
        std::optional<uint32_t> colorAbgr = std::nullopt) const
    {
        const UiLayoutManager::LayoutElement *pStyle = m_context.findHudLayoutElement(pStyleId);

        if (pStyle == nullptr || value.empty())
        {
            return;
        }

        UiLayoutManager::LayoutElement style = *pStyle;

        if (colorAbgr)
        {
            style.textColorAbgr = *colorAbgr;
        }

        m_context.renderLayoutLabel(style, area, value, false);
    }

    void label(const char *pLayoutId, const std::string &value, std::optional<uint32_t> colorAbgr = std::nullopt) const
    {
        if (const std::optional<Rect> area = rect(pLayoutId))
        {
            text(pLayoutId, *area, value, colorAbgr);
        }
    }

    // Wraps text to the element's width, one line per font height, starting at lineY.
    float paragraph(const char *pLayoutId, const std::string &value, uint32_t colorAbgr, float lineY) const
    {
        const UiLayoutManager::LayoutElement *pStyle = m_context.findHudLayoutElement(pLayoutId);
        const std::optional<Rect> area = rect(pLayoutId);

        if (pStyle == nullptr || !area)
        {
            return lineY;
        }

        const float fontScale = area->scale * std::max(0.1f, pStyle->textScale);
        const float lineHeight = static_cast<float>(m_context.hudFontHeight(pStyle->fontName)) * fontScale;

        const std::string localizedValue = m_context.localizeHudText(value);
        for (const std::string &line :
            m_context.wrapHudTextToWidth(pStyle->fontName, localizedValue, area->width / fontScale))
        {
            // Lines past the element's bottom would run into the buttons below.
            if (lineY + lineHeight > area->y + area->height + 0.5f)
            {
                break;
            }

            text(pLayoutId, {area->x, lineY, area->width, lineHeight, area->scale}, line, colorAbgr);
            lineY += lineHeight;
        }

        return lineY;
    }

    void button(const char *pLayoutId, const std::string &value, bool enabled, bool selected = false) const
    {
        const UiLayoutManager::LayoutElement *pLayout = m_context.findHudLayoutElement(pLayoutId);
        const std::optional<Rect> area = rect(pLayoutId);

        if (pLayout == nullptr || !area)
        {
            return;
        }

        const bool hover = enabled && hovered(*area);
        const bool down = hover && m_pInput->leftMouseButton.held;
        const std::string &asset = !enabled && !pLayout->disabledAsset.empty() ? pLayout->disabledAsset
            : down && !pLayout->pressedAsset.empty() ? pLayout->pressedAsset
            : hover && !pLayout->hoverAsset.empty() ? pLayout->hoverAsset
            : selected && !pLayout->selectedAsset.empty() ? pLayout->selectedAsset : pLayout->primaryAsset;
        GameplayUiSkin::renderTexture(m_context, asset, *area);
        Rect labelArea = *area;
        labelArea.y += down ? area->scale : 0.0f;
        text(pLayoutId, labelArea, value,
            !enabled ? 0xff7e8b96u : hover ? 0xffd4efffu : selected ? GameplayUiSkin::Gold : pLayout->textColorAbgr);
    }

    void chip(const char *pLayoutId, const std::string &value, bool active) const
    {
        const std::optional<Rect> area = rect(pLayoutId);

        if (!area)
        {
            return;
        }

        if (active)
        {
            fill(*area, ChipOnColor);
        }
        else
        {
            well(*area);

            if (hovered(*area))
            {
                fill(*area, HoverColor);
            }
        }

        text(pLayoutId, *area, value, active ? ChipOnTextColor : DimTextColor);
    }

    void itemIcon(const ItemDefinition *pDefinition, const Rect &box, uint8_t alpha = 255) const
    {
        if (pDefinition == nullptr || pDefinition->iconName.empty())
        {
            return;
        }

        const std::optional<GameplayHudTextureHandle> texture =
            m_context.gameplayUiRuntime().ensureItemIconTextureLoaded(pDefinition->iconName);

        if (!texture || texture->width <= 0 || texture->height <= 0)
        {
            return;
        }

        const float fit = std::min(box.width / texture->width, box.height / texture->height);
        const float iconWidth = std::round(texture->width * fit);
        const float iconHeight = std::round(texture->height * fit);
        const float x = std::round(box.x + (box.width - iconWidth) * 0.5f);
        const float y = std::round(box.y + (box.height - iconHeight) * 0.5f);
        if (alpha == 255)
        {
            m_context.submitHudTexturedQuad(*texture, x, y, iconWidth, iconHeight);
            return;
        }

        // Faded icons are tinted at draw time rather than copied per alpha.
        GameplayHudBatchQuad quad = {};
        quad.textureHandle = texture->textureHandle;
        quad.x = x;
        quad.y = y;
        quad.width = iconWidth;
        quad.height = iconHeight;
        quad.tintAbgr = (uint32_t(alpha) << 24) | 0x00ffffffu;
        m_context.submitHudQuadBatch({quad});
    }

private:
    GameplayScreenRuntime &m_context;
    int m_width = 0;
    int m_height = 0;
    const GameplayInputFrame *m_pInput = nullptr;
};

std::string itemName(const ItemTable &itemTable, uint32_t itemId)
{
    const ItemDefinition *pDefinition = itemTable.get(itemId);
    return pDefinition != nullptr ? pDefinition->name : "";
}

std::string statusHeadline(const GameplayAlchemyBenchModel &model)
{
    switch (model.preview.outcome)
    {
        case AlchemyPreviewOutcome::Incomplete:
            return "Choose two ingredients or a recipe.";
        case AlchemyPreviewOutcome::MissingIngredient:
            return "Not enough ingredients.";
        case AlchemyPreviewOutcome::Unknown:
            return "Untried mixture";
        case AlchemyPreviewOutcome::Known:
            return "Known recipe";
        case AlchemyPreviewOutcome::TooDifficult:
            return "Too difficult";
        case AlchemyPreviewOutcome::KnownExplosive:
            return "Known to explode";
    }

    return "";
}

std::string statusBody(const GameplayScreenRuntime &context, const GameplayAlchemyBenchModel &model)
{
    const std::string alchemist = model.alchemistName.empty() ? "Nobody in the party" : model.alchemistName;
    const std::string mastery = model.alchemist.mastery == SkillMastery::None
        ? "no Alchemy skill"
        : GameplayAlchemyBenchView::masteryName(static_cast<uint8_t>(model.alchemist.mastery));

    switch (model.preview.outcome)
    {
        case AlchemyPreviewOutcome::Unknown:
            return model.alchemist.mastery == SkillMastery::None
                ? "Potions that clash explode, and without Alchemy skill so does any real recipe."
                : "Potions that clash explode, and so does a recipe beyond " + mastery + " Alchemy.";
        case AlchemyPreviewOutcome::Known:
        {
            std::string body = model.preview.requiredMastery > 1
                ? "Needs " + GameplayAlchemyBenchView::masteryName(model.preview.requiredMastery)
                    + " Alchemy. Safe for " + alchemist + "."
                : "Safe to mix.";
            body = context.localizeHudText(body);
            if (model.preview.returnsBottle)
            {
                body += " " + context.localizeHudText("The empty bottle is returned.");
            }
            return body;
        }
        case AlchemyPreviewOutcome::TooDifficult:
            return "Needs " + GameplayAlchemyBenchView::masteryName(model.preview.requiredMastery) + " Alchemy; "
                + alchemist + " has " + mastery + ".";
        case AlchemyPreviewOutcome::KnownExplosive:
            return "This mixture blew up before, and " + alchemist + " would fail it again.";
        default:
            return "";
    }
}

std::string countList(const std::vector<AlchemyItemCount> &counts, const ItemTable &itemTable)
{
    std::string list;

    for (const AlchemyItemCount &count : counts)
    {
        list += (list.empty() ? "" : ", ") + std::to_string(count.count) + " " + itemName(itemTable, count.itemId);
    }

    return list;
}

std::string chainBody(
    const GameplayScreenRuntime &context, const GameplayAlchemyBenchModel &model, const ItemTable &itemTable)
{
    const AlchemyChainPlan &chain = *model.chain;

    if (model.chainMode)
    {
        std::string body = context.localizeHudText("Uses: " + countList(chain.used, itemTable) + ".");

        if (!chain.brewedFirst.empty())
        {
            body += " " + context.localizeHudText("Brews first: " + countList(chain.brewedFirst, itemTable) + ".");
        }

        return body;
    }

    const std::string name = itemName(itemTable, chain.blockItemId);

    switch (chain.block)
    {
        case AlchemyChainBlock::MissingBottle:
            return "No empty bottle left to fill.";
        case AlchemyChainBlock::MissingReagent:
            return "Missing a reagent for " + name + ".";
        case AlchemyChainBlock::UnknownRecipe:
            return "Unknown step: the " + name + " recipe.";
        case AlchemyChainBlock::NeedsMastery:
        {
            const auto entry = std::find_if(model.book.entries.begin(), model.book.entries.end(),
                [&chain](const AlchemyBookEntry &candidate)
                {
                    return candidate.resultItemId == chain.blockItemId;
                });
            return name + " needs "
                + (entry != model.book.entries.end()
                    ? GameplayAlchemyBenchView::masteryName(entry->requiredMastery) : std::string("higher mastery"))
                + " Alchemy.";
        }
        case AlchemyChainBlock::None:
            break;
    }

    return "Not enough ingredients.";
}

uint32_t statusColor(AlchemyPreviewOutcome outcome)
{
    switch (outcome)
    {
        case AlchemyPreviewOutcome::Known:
            return GameplayUiSkin::Bonus;
        case AlchemyPreviewOutcome::Unknown:
            return WarningTextColor;
        case AlchemyPreviewOutcome::TooDifficult:
        case AlchemyPreviewOutcome::MissingIngredient:
        case AlchemyPreviewOutcome::KnownExplosive:
            return GameplayUiSkin::Penalty;
        default:
            return DimTextColor;
    }
}
}

void GameplayAlchemyBenchRenderer::render(GameplayScreenRuntime &context, int width, int height)
{
    const GameplayUiController::CharacterScreenState &characterScreen = context.characterScreenReadOnly();
    const ItemTable *pItemTable = context.itemTable();

    if (!characterScreen.open
        || !characterScreen.alchemyBench.active
        || context.currentHudScreenState() != GameplayHudScreenState::Character
        || pItemTable == nullptr
        || width <= 0
        || height <= 0)
    {
        return;
    }

    const std::optional<GameplayAlchemyBenchModel> model = GameplayAlchemyBenchView::buildModel(context);
    const BenchPainter painter(context, width, height);
    const std::optional<Rect> panel = painter.rect("AlchemyBenchPanel");

    if (!model || !panel)
    {
        return;
    }

    const GameplayUiController::AlchemyBenchState &state = characterScreen.alchemyBench;
    const AlchemyPreview &preview = model->preview;
    context.prepareHudView(width, height);
    // The pages under the bench must not answer item inspection.
    context.gameplayUiRuntime().clearRenderedInspectableHudItems();
    GameplayUiSkin::renderPanel(context, *panel, false, 0.75f);

    painter.label("AlchemyBenchTitle", "Alchemy Bench");
    painter.label("AlchemyBenchRecipeHeader", "Recipes");
    painter.label("AlchemyBenchRecipeCount", std::to_string(model->book.entries.size()) + " / "
        + std::to_string(model->book.totalResultCount) + " known");
    painter.chip("AlchemyBenchRecipeFilterBrewable", "Can brew", !state.showAllRecipes);
    painter.chip("AlchemyBenchRecipeFilterAll", "All known", state.showAllRecipes);

    if (const std::optional<Rect> search = painter.rect("AlchemyBenchRecipeSearch"))
    {
        painter.well(*search, state.recipeSearchActive ? SelectedBorderColor : WellBorderColor);

        if (!state.recipeSearchActive && painter.hovered(*search))
        {
            painter.fill(*search, HoverColor);
        }

        if (state.recipeSearch.empty() && !state.recipeSearchActive)
        {
            painter.text("AlchemyBenchRecipeSearch", *search, "Search recipes", DisabledTextColor);
        }
        else
        {
            // A steady caret; blinking would need a clock the bench does not otherwise use.
            painter.text("AlchemyBenchRecipeSearch", *search,
                state.recipeSearch + (state.recipeSearchActive ? "_" : ""));
        }
    }

    if (const std::optional<Rect> list = painter.rect("AlchemyBenchRecipeList"))
    {
        painter.well(*list);
        const float maximumScroll = GameplayAlchemyBenchView::maximumRecipeScroll(*model, *list);
        const float scroll = std::clamp(state.recipeScrollOffset, 0.0f, maximumScroll);

        for (const GameplayAlchemyBenchRowRect &rowRect : GameplayAlchemyBenchView::visibleRows(*model, *list, scroll))
        {
            const GameplayAlchemyBenchRow &row = model->rows[rowRect.rowIndex];
            const Rect &area = rowRect.rect;
            const float s = area.scale;

            if (row.kind == GameplayAlchemyBenchRowKind::Header)
            {
                painter.text("AlchemyBenchIngredientHint", {area.x + 4 * s, area.y + s, area.width, area.height, s},
                    row.text, HeaderTextColor);
                continue;
            }

            if (row.kind == GameplayAlchemyBenchRowKind::Undiscovered)
            {
                painter.text("AlchemyBenchIngredientHint", {area.x + 4 * s, area.y + 3 * s, area.width, area.height, s},
                    row.text, DisabledTextColor);
                continue;
            }

            const AlchemyBookEntry &entry = model->book.entries[row.entryIndex];
            const bool selected = model->selectedEntryIndex == row.entryIndex;

            if (selected)
            {
                painter.fill(area, SelectedRowColor);
                painter.frame(area, SelectedBorderColor);
            }
            else if (painter.hovered(area))
            {
                painter.fill(area, HoverColor);
            }

            const uint32_t chainCount = model->chainCounts[row.entryIndex];
            const bool brewable = entry.masteryAllows && (entry.brewableCount > 0 || chainCount > 0);
            const uint32_t color = !entry.masteryAllows ? GameplayUiSkin::Penalty
                : brewable ? GameplayUiSkin::Ivory : DisabledTextColor;
            painter.itemIcon(pItemTable->get(entry.resultItemId), {area.x + 3 * s, area.y + 1.5f * s, 10 * s,
                14 * s, s});
            painter.text("AlchemyBenchRowLabel", {area.x + 17 * s, area.y + 3 * s, area.width - 60 * s,
                area.height, s}, itemName(*pItemTable, entry.resultItemId), color);
            // "1 +3": one from carried ingredients, three more by brewing missing ingredients first.
            const uint32_t extra = chainCount > entry.brewableCount ? chainCount - entry.brewableCount : 0;
            const std::string count = !entry.masteryAllows
                ? GameplayAlchemyBenchView::masteryName(entry.requiredMastery)
                : extra == 0 ? std::to_string(entry.brewableCount)
                : entry.brewableCount > 0 ? std::to_string(entry.brewableCount) + " +" + std::to_string(extra)
                : "+" + std::to_string(extra);

            if (std::find(state.newRecipeResultIds.begin(), state.newRecipeResultIds.end(), entry.resultItemId)
                != state.newRecipeResultIds.end())
            {
                painter.text("AlchemyBenchRowCount", {area.x, area.y + 3 * s, area.width - 24 * s, area.height, s},
                    "NEW", GameplayUiSkin::Gold);
            }
            painter.text("AlchemyBenchRowCount", {area.x, area.y + 3 * s, area.width - 4 * s, area.height, s},
                count, color);
        }

        if (model->rows.empty())
        {
            painter.text("AlchemyBenchSlotNameLabel", {list->x, list->y + 10 * list->scale, list->width,
                12 * list->scale, list->scale},
                state.showAllRecipes ? "No recipes known yet." : "Nothing to brew yet.", DimTextColor);
        }

        const float visibleHeight = list->height / list->scale - 2 * GameplayAlchemyBenchView::RecipeListPadding;
        GameplayUiSkin::renderScrollbar(context, *list, maximumScroll > 0 ? scroll / maximumScroll : 0.0f,
            model->rowsHeight > 0 ? visibleHeight / model->rowsHeight : 1.0f,
            context.interactionState().alchemyBenchScrollDrag == 1);
    }

    const bool previewNamesResult =
        preview.outcome == AlchemyPreviewOutcome::Known || preview.outcome == AlchemyPreviewOutcome::TooDifficult;
    painter.label("AlchemyBenchMixHeader", previewNamesResult
        ? "Mix: " + itemName(*pItemTable, preview.resultItemId)
        : preview.outcome == AlchemyPreviewOutcome::Unknown ? "Experiment" : "Mix");

    if (model->alchemistName.empty())
    {
        painter.label("AlchemyBenchAlchemistLabel", "No alchemist: only bottle and reagent mixes are safe.");
    }
    else
    {
        painter.label("AlchemyBenchAlchemistLabel", "Alchemist: " + model->alchemistName + " - "
            + GameplayAlchemyBenchView::masteryName(static_cast<uint8_t>(model->alchemist.mastery)) + " "
            + std::to_string(model->alchemist.level) + " (best in party)");
    }

    const GameplayOverlayInteractionState &interaction = context.interactionState();
    const uint32_t draggedItemId = interaction.alchemyBenchDragging ? interaction.alchemyBenchPressedTarget.itemId : 0;
    const auto addInspectable =
        [&context, pItemTable](uint32_t itemId, uint16_t power, const Rect &area)
        {
            const ItemDefinition *pDefinition = pItemTable->get(itemId);

            if (pDefinition == nullptr)
            {
                return;
            }

            GameplayRenderedInspectableHudItem inspectable = {};
            inspectable.objectDescriptionId = itemId;
            inspectable.hasItemState = true;
            inspectable.itemState.objectDescriptionId = itemId;
            inspectable.itemState.standardEnchantPower = power;
            inspectable.textureName = pDefinition->iconName;
            inspectable.x = area.x;
            inspectable.y = area.y;
            inspectable.width = area.width;
            inspectable.height = area.height;
            context.addRenderedInspectableHudItem(inspectable);
        };
    const uint64_t brewedElapsedTicks = SDL_GetTicks() - state.brewedTicks;
    const auto renderSlot =
        [&](const char *pLayoutId, uint32_t itemId, uint16_t power, bool heldSlot)
        {
            const std::optional<Rect> slot = painter.rect(pLayoutId);

            if (!slot)
            {
                return;
            }

            const float s = slot->scale;
            const bool highlighted = draggedItemId != 0 ? painter.hovered(*slot)
                : itemId != 0 && painter.hovered(*slot);
            painter.well(*slot, highlighted ? SelectedBorderColor : WellBorderColor);

            if (itemId == 0)
            {
                return;
            }

            // A used-up ingredient stays visible, faded, so the player still sees what was mixed.
            const AlchemyIngredient *pIngredient = AlchemyBenchRuntime::findIngredient(model->ingredients, itemId);
            const bool missing = pIngredient == nullptr
                || (heldSlot && state.targetItemId == state.heldItemId && pIngredient->count < 2);
            painter.itemIcon(pItemTable->get(itemId), {slot->x + 8 * s, slot->y + 6 * s, slot->width - 16 * s,
                slot->height - 12 * s, s}, missing ? 100 : 255);
            addInspectable(itemId,
                pIngredient != nullptr && pIngredient->kind == AlchemyIngredientKind::Potion ? power : 0, *slot);

            const Rect nameArea = {slot->x - 12 * s, slot->y + slot->height + 2 * s, slot->width + 24 * s, 11 * s, s};
            painter.text("AlchemyBenchSlotNameLabel", nameArea, itemName(*pItemTable, itemId),
                missing ? DisabledTextColor : GameplayUiSkin::Ivory);
            const bool powerKnown = preview.outcome != AlchemyPreviewOutcome::MissingIngredient
                && preview.outcome != AlchemyPreviewOutcome::Incomplete
                && power > 0;
            const bool brewedFirst = missing && model->chainMode;
            painter.text("AlchemyBenchSlotPowerLabel", {nameArea.x, nameArea.y + 10 * s, nameArea.width, 10 * s, s},
                brewedFirst ? "brewed first" : missing ? "missing" : powerKnown ? "power " + std::to_string(power) : "",
                brewedFirst ? GameplayUiSkin::Gold : missing ? GameplayUiSkin::Penalty : DimTextColor);
        };

    renderSlot("AlchemyBenchTargetSlot", state.targetItemId, preview.targetPower, false);
    painter.label("AlchemyBenchPlusLabel", "+");
    renderSlot("AlchemyBenchHeldSlot", state.heldItemId, preview.heldPower, true);
    painter.label("AlchemyBenchEqualsLabel", "=");

    if (const std::optional<Rect> resultSlot = painter.rect("AlchemyBenchResultSlot"))
    {
        const float s = resultSlot->scale;
        const Rect nameArea = {resultSlot->x - 12 * s, resultSlot->y + resultSlot->height + 2 * s,
            resultSlot->width + 24 * s, 11 * s, s};
        const Rect banner = {resultSlot->x + s, resultSlot->y + s, resultSlot->width - 2 * s, 12 * s, s};
        const Rect bannerIconBox = {resultSlot->x + 8 * s, resultSlot->y + 14 * s, resultSlot->width - 16 * s,
            resultSlot->height - 18 * s, s};

        if (state.brewedExploded)
        {
            painter.well(*resultSlot, GameplayUiSkin::Penalty);
            painter.fill(banner, 0xa0000000u);
            painter.text("AlchemyBenchSlotNameLabel", {banner.x, banner.y + s, banner.width, banner.height, s},
                "Exploded!", GameplayUiSkin::Penalty);
            painter.text("AlchemyBenchPlusLabel", *resultSlot, "!", GameplayUiSkin::Penalty);
            painter.text("AlchemyBenchSlotNameLabel", nameArea, "Exploded", GameplayUiSkin::Penalty);
        }
        else if (state.brewedItemId != 0)
        {
            // What the last Mix produced, with a short glow; it stays until a slot changes.
            painter.well(*resultSlot, SelectedBorderColor);
            const float glowSeconds = state.brewedDiscovery ? 1.6f : 0.9f;
            const float elapsed = float(brewedElapsedTicks) * 0.001f;

            if (elapsed < glowSeconds)
            {
                const float strength = 1.0f - elapsed / glowSeconds;
                painter.fill(*resultSlot, (uint32_t(std::lround(0x90 * strength)) << 24) | 0x0050c8f0u);
            }

            painter.fill(banner, 0xa0000000u);
            const std::string bannerText = state.brewedDiscovery ? "New recipe!"
                : state.brewedCount > 1 ? "Brewed x" + std::to_string(state.brewedCount) : "Brewed";
            painter.text("AlchemyBenchSlotNameLabel", {banner.x, banner.y + s, banner.width, banner.height, s},
                bannerText, GameplayUiSkin::Gold);
            painter.itemIcon(pItemTable->get(state.brewedItemId), bannerIconBox);
            addInspectable(state.brewedItemId, state.brewedPower, *resultSlot);
            painter.text("AlchemyBenchSlotNameLabel", nameArea, itemName(*pItemTable, state.brewedItemId));
            painter.text("AlchemyBenchSlotPowerLabel", {nameArea.x, nameArea.y + 10 * s, nameArea.width, 10 * s, s},
                state.brewedPower > 0 ? "power " + std::to_string(state.brewedPower) : "", DimTextColor);
        }
        else if (model->chainMode)
        {
            const uint32_t chainResultItemId = model->chain->steps.back().resultItemId;
            painter.well(*resultSlot, SelectedBorderColor);
            painter.fill(banner, 0xa0000000u);
            painter.text("AlchemyBenchSlotNameLabel", {banner.x, banner.y + s, banner.width, banner.height, s},
                "Chain", GameplayUiSkin::Gold);
            painter.itemIcon(pItemTable->get(chainResultItemId), bannerIconBox);
            addInspectable(chainResultItemId, model->chain->resultPower, *resultSlot);
            painter.text("AlchemyBenchSlotNameLabel", nameArea, itemName(*pItemTable, chainResultItemId));
            painter.text("AlchemyBenchSlotPowerLabel", {nameArea.x, nameArea.y + 10 * s, nameArea.width, 10 * s, s},
                model->chain->resultPower > 0 ? "power ~" + std::to_string(model->chain->resultPower) : "",
                DimTextColor);
        }
        else if (previewNamesResult)
        {
            painter.well(*resultSlot, SelectedBorderColor);
            const bool tooDifficult = preview.outcome == AlchemyPreviewOutcome::TooDifficult;
            painter.itemIcon(pItemTable->get(preview.resultItemId), {resultSlot->x + 8 * s, resultSlot->y + 6 * s,
                resultSlot->width - 16 * s, resultSlot->height - 12 * s, s}, tooDifficult ? 110 : 255);

            if (!tooDifficult)
            {
                addInspectable(preview.resultItemId, preview.resultPower, *resultSlot);
            }

            painter.text("AlchemyBenchSlotNameLabel", nameArea, itemName(*pItemTable, preview.resultItemId));
            painter.text("AlchemyBenchSlotPowerLabel", {nameArea.x, nameArea.y + 10 * s, nameArea.width, 10 * s, s},
                tooDifficult ? "needs " + GameplayAlchemyBenchView::masteryName(preview.requiredMastery)
                    : preview.resultPower > 0 ? "power " + std::to_string(preview.resultPower) : "",
                tooDifficult ? GameplayUiSkin::Penalty : DimTextColor);
        }
        else if (preview.outcome == AlchemyPreviewOutcome::Unknown)
        {
            painter.well(*resultSlot);
            painter.text("AlchemyBenchPlusLabel", *resultSlot, "?");
            painter.text("AlchemyBenchSlotNameLabel", nameArea, "Unknown");
        }
        else if (preview.outcome == AlchemyPreviewOutcome::KnownExplosive)
        {
            painter.well(*resultSlot, GameplayUiSkin::Penalty);
            painter.text("AlchemyBenchPlusLabel", *resultSlot, "!", GameplayUiSkin::Penalty);
            painter.text("AlchemyBenchSlotNameLabel", nameArea, "Explodes", GameplayUiSkin::Penalty);
        }
        else
        {
            painter.well(*resultSlot);
        }
    }

    if (const std::optional<Rect> status = painter.rect("AlchemyBenchStatus"))
    {
        if (model->chain)
        {
            const float lineY = painter.paragraph("AlchemyBenchStatus",
                model->chainMode ? "Brew chain" : "Can't brew yet",
                model->chainMode ? GameplayUiSkin::Bonus : GameplayUiSkin::Penalty, status->y);
            painter.paragraph("AlchemyBenchStatus", chainBody(context, *model, *pItemTable), DimTextColor,
                lineY + 3 * status->scale);
        }
        else
        {
            const float lineY = painter.paragraph("AlchemyBenchStatus", statusHeadline(*model),
                statusColor(preview.outcome), status->y);
            painter.paragraph("AlchemyBenchStatus", statusBody(context, *model), DimTextColor, lineY + 3 * status->scale);
        }
    }

    const std::string mixLabel = model->chainMode ? "Brew chain"
        : preview.outcome == AlchemyPreviewOutcome::Unknown ? "Try Mix" : "Mix";
    const std::string mixAllLabel = model->chainMode ? "Brew All" : "Mix All";
    painter.button("AlchemyBenchMixButton", mixLabel, GameplayAlchemyBenchView::mixEnabled(*model));
    painter.button("AlchemyBenchMixAllButton",
        model->mixAllCount > 1
            ? context.localizeHudText(mixAllLabel) + " (" + std::to_string(model->mixAllCount) + ")" : mixAllLabel,
        model->mixAllCount > 1);
    painter.button("AlchemyBenchClearButton", "Clear", state.targetItemId != 0 || state.heldItemId != 0);
    painter.button("AlchemyBenchCloseButton", "Close", true);

    painter.label("AlchemyBenchIngredientHeader", "Ingredients");
    painter.label("AlchemyBenchIngredientHint", "whole party, click or drag to place");
    const GameplayUiController::AlchemyIngredientFilter filter = state.ingredientFilter;
    painter.chip("AlchemyBenchIngredientFilterAll", "All",
        filter == GameplayUiController::AlchemyIngredientFilter::All);
    painter.chip("AlchemyBenchIngredientFilterPotions", "Potions",
        filter == GameplayUiController::AlchemyIngredientFilter::Potions);
    painter.chip("AlchemyBenchIngredientFilterReagents", "Reagents",
        filter == GameplayUiController::AlchemyIngredientFilter::Reagents);

    if (const std::optional<Rect> grid = painter.rect("AlchemyBenchIngredientGrid"))
    {
        painter.well(*grid);
        const size_t maximumRow = GameplayAlchemyBenchView::maximumIngredientScrollRow(*model, *grid);
        const size_t scrollRow = std::min(state.ingredientScrollRow, maximumRow);

        const std::vector<GameplayAlchemyBenchCellRect> cells =
            GameplayAlchemyBenchView::visibleCells(*model, *grid, scrollRow);

        for (const GameplayAlchemyBenchCellRect &cell : cells)
        {
            const AlchemyIngredient &ingredient = model->ingredients[cell.ingredientIndex];
            const Rect &area = cell.rect;
            const float s = area.scale;
            const bool placed = ingredient.itemId == state.targetItemId || ingredient.itemId == state.heldItemId;
            painter.well(area, placed ? SelectedBorderColor : WellBorderColor);

            // The freshly brewed potion pulses twice where it landed.
            constexpr float PulseSeconds = 1.2f;
            const float pulseElapsed = float(brewedElapsedTicks) * 0.001f;

            if (ingredient.itemId == state.brewedItemId && pulseElapsed < PulseSeconds)
            {
                const float wave = std::abs(std::sin(pulseElapsed / PulseSeconds * 2.0f * 3.14159265f));
                const float strength = wave * (1.0f - pulseElapsed / PulseSeconds);
                painter.fill(area, (uint32_t(std::lround(0xa0 * strength)) << 24) | 0x0050c8f0u);
                painter.frame(area, GameplayUiSkin::Gold);
            }

            if (painter.hovered(area))
            {
                painter.fill(area, HoverColor);
            }

            const ItemDefinition *pDefinition = pItemTable->get(ingredient.itemId);
            const Rect iconBox = {area.x + 3 * s, area.y + 3 * s, area.width - 6 * s, area.height - 9 * s, s};
            painter.itemIcon(pDefinition, iconBox);
            painter.text("AlchemyBenchRowCount", {area.x, area.y + area.height - 10 * s, area.width - 2 * s,
                10 * s, s}, std::to_string(ingredient.count), GameplayUiSkin::Ivory);

            if (pDefinition != nullptr)
            {
                GameplayRenderedInspectableHudItem inspectable = {};
                inspectable.objectDescriptionId = ingredient.itemId;
                inspectable.hasItemState = true;
                inspectable.itemState.objectDescriptionId = ingredient.itemId;
                inspectable.itemState.standardEnchantPower =
                    ingredient.kind == AlchemyIngredientKind::Potion ? ingredient.bestPower : 0;
                inspectable.textureName = pDefinition->iconName;
                inspectable.x = area.x;
                inspectable.y = area.y;
                inspectable.width = area.width;
                inspectable.height = area.height;
                context.addRenderedInspectableHudItem(inspectable);
            }
        }

        if (model->visibleIngredients.empty())
        {
            painter.text("AlchemyBenchSlotNameLabel", {grid->x, grid->y + 10 * grid->scale, grid->width,
                12 * grid->scale, grid->scale}, "The party carries no bottles, reagents or potions.", DimTextColor);
        }

        const size_t visibleRows = GameplayAlchemyBenchView::ingredientVisibleRows(*grid);
        GameplayUiSkin::renderScrollbar(context, *grid, maximumRow > 0 ? float(scrollRow) / float(maximumRow) : 0.0f,
            float(visibleRows) / float(visibleRows + maximumRow), interaction.alchemyBenchScrollDrag == 2);
    }

    if (draggedItemId != 0)
    {
        if (const GameplayInputFrame *pInput = context.currentGameplayInputFrame())
        {
            const float s = panel->scale;
            const float iconWidth = GameplayAlchemyBenchView::IngredientCellWidth * s;
            const float iconHeight = GameplayAlchemyBenchView::IngredientCellHeight * s;
            painter.itemIcon(pItemTable->get(draggedItemId),
                {pInput->pointerX - iconWidth * 0.5f, pInput->pointerY - iconHeight * 0.5f, iconWidth, iconHeight, s});
        }
    }
}
}
