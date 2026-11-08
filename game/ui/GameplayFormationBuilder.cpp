#include "game/ui/GameplayFormationBuilder.h"

#include "engine/Localization.h"

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/mm9/Mm9Formation.h"
#include "game/party/Party.h"
#include "game/ui/GameplayBenchPainter.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiRuntime.h"
#include "game/ui/GameplayUiSkin.h"

#include <algorithm>
#include <cmath>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
using Rect = GameplayResolvedHudLayoutElement;

// The study's colours (mm9_formation_20261106 index.html), as ABGR.
constexpr uint32_t abgr(uint32_t rgb, uint32_t alpha = 0xff)
{
    return alpha << 24 | (rgb & 0xffu) << 16 | (rgb & 0xff00u) | (rgb >> 16 & 0xffu);
}

constexpr uint32_t Shade = abgr(0x000000, 0x73);
constexpr uint32_t Brass = abgr(0xc9b27a);
constexpr uint32_t BrassRule = abgr(0x8f7b4b);
constexpr uint32_t Gold = abgr(0xe2c46e);
constexpr uint32_t CellFill = abgr(0x000000, 0x73);
constexpr uint32_t CellInset = abgr(0x000000, 0x59);
constexpr uint32_t CellBorder = abgr(0x6f5d36);
constexpr uint32_t EmptyFill = abgr(0x000000, 0x40);
constexpr uint32_t EmptyBorder = abgr(0x5a503a);
constexpr uint32_t TargetGlow = abgr(0xe2c46e, 0x48);
constexpr uint32_t MarkEdge = abgr(0x3a3020);
constexpr uint32_t TipFill = abgr(0x0a0e0c, 0xeb);
constexpr uint32_t TipBorder = abgr(0x8a7546);
constexpr uint32_t GhostShadow = abgr(0x000000, 0x70);
constexpr uint32_t SlabTop = abgr(0x26302a);
constexpr uint32_t SlabBottom = abgr(0x141916);
constexpr uint32_t SlabBorder = abgr(0x8f7b4b);
constexpr uint32_t SlabShadow = abgr(0x000000, 0x80);
constexpr uint32_t RearDiamond = abgr(0xa8956a);
constexpr uint32_t FaceBacking = abgr(0x0b1110);
constexpr uint32_t GreyedPortrait = 0xff888888u;

// The dragged face is drawn a little larger than a seated one (the study's 42 x 57 for 40 x 54).
constexpr float DragGrowth = 1.05f;

GameplayOverlayInteractionState &interaction(const GameplayScreenRuntime &context)
{
    return context.interactionState();
}

Mm9FormationBuilderState &state(const GameplayScreenRuntime &context)
{
    return interaction(context).formationBuilder;
}

std::optional<GameplayHudTextureHandle> solid(const GameplayScreenRuntime &context, uint32_t colour)
{
    return context.gameplayUiRuntime().ensureSolidHudTextureLoaded("__mm9_formation_" + std::to_string(colour) + "__",
        colour);
}

void fill(const GameplayScreenRuntime &context, float x, float y, float width, float height, uint32_t colour)
{
    if (const std::optional<GameplayHudTextureHandle> texture = solid(context, colour);
        texture && width > 0 && height > 0)
    {
        context.submitHudTexturedQuad(*texture, x, y, width, height);
    }
}

void frame(const GameplayScreenRuntime &context, const Mm9FormationRect &box, float line, uint32_t colour)
{
    fill(context, box.x, box.y, box.width, line, colour);
    fill(context, box.x, box.y + box.height - line, box.width, line, colour);
    fill(context, box.x, box.y + line, line, box.height - 2 * line, colour);
    fill(context, box.x + box.width - line, box.y + line, line, box.height - 2 * line, colour);
}

// A dashed border (an empty cell's): dashes of `dash` with gaps of `gap` along each edge.
void dashedFrame(const GameplayScreenRuntime &context, const Mm9FormationRect &box, float line, float dash, float gap,
    uint32_t colour)
{
    for (float offset = 0; offset < box.width; offset += dash + gap)
    {
        const float length = std::min(dash, box.width - offset);
        fill(context, box.x + offset, box.y, length, line, colour);
        fill(context, box.x + offset, box.y + box.height - line, length, line, colour);
    }

    for (float offset = 0; offset < box.height; offset += dash + gap)
    {
        const float length = std::min(dash, box.height - offset);
        fill(context, box.x, box.y + offset, line, length, colour);
        fill(context, box.x + box.width - line, box.y + offset, line, length, colour);
    }
}

// A diamond of half-diagonal `half` about a centre: a square on its corner, as one line quad as thick as it is long.
void diamond(const GameplayScreenRuntime &context, float x, float y, float half, uint32_t colour)
{
    const std::optional<GameplayHudTextureHandle> texture = solid(context, colour);

    if (!texture || half <= 0)
    {
        return;
    }

    GameplayHudBatchQuad quad;
    quad.textureHandle = texture->textureHandle;
    quad.line = true;
    quad.x = x - half / 2;
    quad.y = y - half / 2;
    quad.x2 = x + half / 2;
    quad.y2 = y + half / 2;
    quad.width = half * std::sqrt(2.0f);
    context.submitHudQuadBatch({quad});
}

const UiLayoutManager::LayoutElement *element(const GameplayScreenRuntime &context, const char *pId)
{
    return context.findHudLayoutElement(pId);
}

std::optional<Mm9FormationGrid> grid(const GameplayScreenRuntime &context, int width, int height)
{
    const std::optional<Rect> area = context.resolveHudLayoutElement("Mm9FormationGrid", width, height, 0, 0);
    const UiLayoutManager::LayoutElement *pCell = element(context, "Mm9FormationCell");

    if (!area || pCell == nullptr)
    {
        return std::nullopt;
    }

    return Mm9FormationGrid{{area->x, area->y, area->width, area->height}, pCell->width * area->scale,
        pCell->height * area->scale};
}

float gridScale(const GameplayScreenRuntime &context, int width, int height)
{
    const std::optional<Rect> area = context.resolveHudLayoutElement("Mm9FormationGrid", width, height, 0, 0);
    return area ? area->scale : 1.0f;
}

// A part of a cell laid out by its own element's offset and size (the face, the hireling mark).
Mm9FormationRect cellPart(const GameplayScreenRuntime &context, const Mm9FormationRect &cell, const char *pId,
    float scale)
{
    const UiLayoutManager::LayoutElement *pPart = element(context, pId);

    if (pPart == nullptr)
    {
        return cell;
    }

    return {cell.x + pPart->gapX * scale, cell.y + pPart->gapY * scale, pPart->width * scale, pPart->height * scale};
}

// The combatant's oval face: the members' portrait animation for both members and hirelings, a dead or eradicated
// one with their own face (not the tombstone), greyed while they cannot act; a brass ring round it.
void renderFace(GameplayScreenRuntime &context, const Party &party, size_t combatant, const Mm9FormationRect &box,
    float scale)
{
    const Character *pCharacter = party.combatant(combatant);

    if (pCharacter == nullptr)
    {
        return;
    }

    GameplayUiRuntime &uiRuntime = context.gameplayUiRuntime();

    // A dark oval under the face (the portraits' edges are transparent), the face, then the party's brass rim.
    if (const std::optional<GameplayHudTextureHandle> backing = solid(context, FaceBacking))
    {
        uiRuntime.submitHudTexturedEllipse(backing->textureHandle, box.x, box.y, box.width, box.height);
    }

    const bool down = pCharacter->portraitState == PortraitId::Dead
        || pCharacter->portraitState == PortraitId::Eradicated;
    const std::optional<GameplayHudTextureHandle> portrait = uiRuntime.ensureHudTextureLoaded(
        down ? pCharacter->portraitTextureName : context.resolvePortraitTextureName(*pCharacter));

    if (!portrait)
    {
        return;
    }

    const bgfx::TextureHandle texture = GameMechanics::canAct(*pCharacter)
        ? portrait->textureHandle : uiRuntime.ensureHudTextureColorModulated(*portrait, GreyedPortrait);
    uiRuntime.submitHudTexturedEllipse(texture, box.x, box.y, box.width, box.height);
    constexpr float Rim = 1.1f;
    GameplayUiSkin::renderArc(context,
        {box.x - Rim * scale / 2, box.y - Rim * scale / 2, box.width + Rim * scale, box.height + Rim * scale, scale},
        Rim, 0, 360, GameplayUiSkin::ArcMaterial::NormalRim);
}

void renderLabel(GameplayScreenRuntime &context, const char *pId, int width, int height,
    const std::string *pText = nullptr)
{
    const UiLayoutManager::LayoutElement *pLayout = element(context, pId);
    const std::optional<Rect> rect = context.resolveHudLayoutElement(pId, width, height, 0, 0);

    if (pLayout != nullptr && rect)
    {
        context.renderLayoutLabel(*pLayout, *rect, pText != nullptr ? *pText : pLayout->labelText, false);
    }
}

// The brass rule under the title, fading at both ends.
void renderTitleRule(GameplayScreenRuntime &context, int width, int height)
{
    const std::optional<Rect> rule = context.resolveHudLayoutElement("Mm9FormationTitleRule", width, height, 0, 0);

    if (!rule)
    {
        return;
    }

    constexpr int Segments = 24;
    const float segment = rule->width / Segments;
    const float line = std::max(1.0f, rule->height);

    for (int index = 0; index < Segments; ++index)
    {
        const float middle = (float(index) + 0.5f) / Segments;
        const float strength = 1.0f - std::abs(middle * 2 - 1);
        const uint32_t alpha = uint32_t(std::lround(255.0f * strength));
        fill(context, rule->x + float(index) * segment, rule->y, segment, line, (alpha << 24) | (BrassRule & 0xffffff));
    }
}

void renderTooltip(GameplayScreenRuntime &context, const std::string &name, const Mm9FormationRect &cell, float scale,
    int width)
{
    const UiLayoutManager::LayoutElement *pStyle = element(context, "Mm9FormationTooltip");

    if (pStyle == nullptr || name.empty())
    {
        return;
    }

    const float textWidth = context.measureHudTextWidth(pStyle->fontName, name) * scale * pStyle->textScale;
    const float boxWidth = textWidth + 10 * scale;
    const float boxHeight = 16 * scale;
    const float x = std::min(cell.x + cell.width * 0.55f, float(width) - boxWidth - 2 * scale);
    const float y = cell.y - 10 * scale;
    fill(context, x, y, boxWidth, boxHeight, TipFill);
    frame(context, {x, y, boxWidth, boxHeight}, std::max(1.0f, 0.7f * scale), TipBorder);
    context.renderLayoutLabel(*pStyle, Rect{x, y, boxWidth, boxHeight, scale}, name, false);
}

std::optional<Rect> buttonRect(const GameplayScreenRuntime &context, int width, int height)
{
    return context.resolveHudLayoutElement("Mm9FormationButton", width, height, 0, 0);
}

Mm9FormationButton controlAt(const GameplayScreenRuntime &context, int width, int height, float x, float y)
{
    for (const auto &[pId, button] : {std::pair{"Mm9FormationCancelButton", Mm9FormationButton::Cancel},
             std::pair{"Mm9FormationAcceptButton", Mm9FormationButton::Accept}})
    {
        const std::optional<Rect> rect = context.resolveHudLayoutElement(pId, width, height, 0, 0);

        if (rect && GameplayHudCommon::isPointerInsideResolvedElement(*rect, x, y))
        {
            return button;
        }
    }

    return Mm9FormationButton::None;
}
}

bool GameplayFormationBuilder::available(const GameplayScreenRuntime &context)
{
    const Party *pParty = context.partyReadOnly();
    return pParty != nullptr && pParty->formationTargetingActive();
}

bool GameplayFormationBuilder::isOpen(const GameplayScreenRuntime &context)
{
    return state(context).open;
}

void GameplayFormationBuilder::open(GameplayScreenRuntime &context)
{
    const Party *pParty = context.partyReadOnly();

    if (!available(context) || pParty == nullptr)
    {
        return;
    }

    Mm9FormationBuilderState &builder = state(context);
    builder = {};
    builder.open = true;
    builder.cells = pParty->formationCells();
}

void GameplayFormationBuilder::close(GameplayScreenRuntime &context)
{
    state(context) = {};
}

bool GameplayFormationBuilder::accept(GameplayScreenRuntime &context)
{
    Mm9FormationBuilderState &builder = state(context);
    Party *pParty = context.party();

    if (!builder.open || pParty == nullptr)
    {
        return false;
    }

    // MM9 checks on Exit and stays open until the front line is covered (MM9_HIRELINGS.md 10.1).
    if (!mm9FormationFrontLineCovered(builder.cells))
    {
        builder.refused = true;
        pParty->requestSound(SoundId::Error);
        return false;
    }

    pParty->setFormationCells(builder.cells);
    close(context);
    return true;
}

void GameplayFormationBuilder::renderButton(GameplayScreenRuntime &context, int width, int height)
{
    const std::optional<Rect> rect = buttonRect(context, width, height);

    if (!available(context) || !rect)
    {
        return;
    }

    const float s = rect->scale;
    const GameplayInputFrame *pInput = context.currentGameplayInputFrame();
    const bool hovered = pInput != nullptr
        && GameplayHudCommon::isPointerInsideResolvedElement(*rect, pInput->pointerX, pInput->pointerY);

    // The carved slab: a dark green-black gradient in a brass border, a soft shadow round it.
    frame(context, {rect->x - s, rect->y - s, rect->width + 2 * s, rect->height + 2 * s}, s, SlabShadow);
    constexpr int Bands = 8;

    for (int band = 0; band < Bands; ++band)
    {
        const float t = float(band) / (Bands - 1);
        const auto channel = [t](uint32_t top, uint32_t bottom, int shift)
        {
            const float from = float(top >> shift & 0xffu);
            const float to = float(bottom >> shift & 0xffu);
            return uint32_t(std::lround(from + (to - from) * t)) << shift;
        };
        const uint32_t colour = 0xff000000u | channel(SlabTop, SlabBottom, 0) | channel(SlabTop, SlabBottom, 8)
            | channel(SlabTop, SlabBottom, 16);
        fill(context, rect->x, rect->y + rect->height * float(band) / Bands, rect->width, rect->height / Bands + 0.5f,
            colour);
    }

    frame(context, {rect->x, rect->y, rect->width, rect->height}, std::max(1.0f, 0.9f * s),
        hovered || isOpen(context) ? Gold : SlabBorder);

    // A 3 x 3 grid of brass diamonds, the front rank larger and gold.
    for (int rank = 0; rank < Mm9FormationRankSize; ++rank)
    {
        for (int column = 0; column < Mm9FormationRankSize; ++column)
        {
            const float unit = rect->width / 24.0f;
            diamond(context, rect->x + (6 + 6 * column) * unit, rect->y + (6 + 6 * rank) * unit,
                (rank == 0 ? 2.4f : 1.8f) * unit, rank == 0 ? Gold : RearDiamond);
        }
    }
}

bool GameplayFormationBuilder::buttonContains(const GameplayScreenRuntime &context, int width, int height, float x,
    float y)
{
    const std::optional<Rect> rect = buttonRect(context, width, height);
    return available(context) && rect && GameplayHudCommon::isPointerInsideResolvedElement(*rect, x, y);
}

void GameplayFormationBuilder::render(GameplayScreenRuntime &context, int width, int height)
{
    Mm9FormationBuilderState &builder = state(context);
    const Party *pParty = context.partyReadOnly();

    if (!builder.open || pParty == nullptr || !context.hasHudRenderResources() || width <= 0 || height <= 0)
    {
        return;
    }

    // A change of party under the open builder (a load) leaves nothing to edit.
    if (builder.cells.size() != pParty->combatantCount())
    {
        close(context);
        return;
    }

    const std::optional<Rect> panel = context.resolveHudLayoutElement("Mm9FormationPanel", width, height, 0, 0);
    const std::optional<Mm9FormationGrid> cells = grid(context, width, height);

    if (!panel || !cells)
    {
        return;
    }

    context.prepareHudView(width, height);
    // The HUD under the builder must not answer item inspection.
    context.gameplayUiRuntime().clearRenderedInspectableHudItems();
    const float s = gridScale(context, width, height);
    fill(context, 0, 0, float(width), float(height), Shade);
    GameplayUiSkin::renderPanel(context, *panel, false, 0.75f);
    renderLabel(context, "Mm9FormationTitle", width, height);
    renderTitleRule(context, width, height);

    for (const char *pId : {"Mm9FormationFrontRank", "Mm9FormationFrontChance", "Mm9FormationMiddleRank",
             "Mm9FormationMiddleChance", "Mm9FormationRearRank", "Mm9FormationRearChance"})
    {
        renderLabel(context, pId, width, height);
    }

    const GameplayInputFrame *pInput = context.currentGameplayInputFrame();
    const float pointerX = pInput != nullptr ? pInput->pointerX : -1.0f;
    const float pointerY = pInput != nullptr ? pInput->pointerY : -1.0f;
    const std::optional<int32_t> pointedCell = mm9FormationCellAt(*cells, pointerX, pointerY);

    for (int32_t cell = 0; cell < Mm9FormationCellCount; ++cell)
    {
        const Mm9FormationRect box = mm9FormationCellRect(*cells, cell);
        const std::optional<size_t> occupant = mm9FormationOccupant(builder.cells, cell);
        const bool seated = occupant && occupant != builder.dragged;
        const bool target = builder.dragged && !occupant && pointedCell == cell;

        if (seated)
        {
            fill(context, box.x, box.y, box.width, box.height, CellFill);
            frame(context, box, std::max(1.0f, 2.0f * s), CellInset);
            frame(context, box, std::max(1.0f, 0.8f * s), CellBorder);
            renderFace(context, *pParty, *occupant, cellPart(context, box, "Mm9FormationFace", s), s);

            if (pParty->isHirelingCombatant(*occupant))
            {
                const Mm9FormationRect mark = cellPart(context, box, "Mm9FormationHirelingMark", s);
                const float x = mark.x + mark.width / 2;
                const float y = mark.y + mark.height / 2;
                diamond(context, x, y, mark.width * 0.5f, MarkEdge);
                diamond(context, x, y, mark.width * 0.43f, Brass);
            }
        }
        else if (target)
        {
            frame(context, {box.x - 2 * s, box.y - 2 * s, box.width + 4 * s, box.height + 4 * s}, 2 * s, TargetGlow);
            fill(context, box.x, box.y, box.width, box.height, EmptyFill);
            frame(context, box, std::max(1.0f, 1.2f * s), Gold);
        }
        else
        {
            fill(context, box.x, box.y, box.width, box.height, EmptyFill);
            dashedFrame(context, box, std::max(1.0f, 0.8f * s), 3 * s, 2 * s, EmptyBorder);
        }
    }

    renderLabel(context, builder.refused ? "Mm9FormationRefusal" : "Mm9FormationInstruction", width, height);
    const GameplayBenchPainter painter(context, width, height);
    painter.button("Mm9FormationCancelButton", Engine::tr("Cancel"), true);
    painter.button("Mm9FormationAcceptButton", Engine::tr("Accept"), true);

    if (builder.dragged)
    {
        // The taken face follows the pointer, a little larger, with a shadow under it.
        const UiLayoutManager::LayoutElement *pFace = element(context, "Mm9FormationFace");
        const float faceWidth = (pFace != nullptr ? pFace->width : 40.0f) * s * DragGrowth;
        const float faceHeight = (pFace != nullptr ? pFace->height : 54.0f) * s * DragGrowth;
        const float x = pointerX - builder.grabOffsetX * DragGrowth;
        const float y = pointerY - builder.grabOffsetY * DragGrowth;

        if (const std::optional<GameplayHudTextureHandle> shadow = solid(context, GhostShadow))
        {
            context.gameplayUiRuntime().submitHudTexturedEllipse(shadow->textureHandle, x + 1 * s, y + 4 * s,
                faceWidth, faceHeight);
        }

        renderFace(context, *pParty, *builder.dragged, {x, y, faceWidth, faceHeight}, s);
    }
    else if (pointedCell)
    {
        // Pointing at a face shows the member's name (MM9).
        if (const std::optional<size_t> occupant = mm9FormationOccupant(builder.cells, *pointedCell))
        {
            if (const Character *pCharacter = pParty->combatant(*occupant))
            {
                renderTooltip(context, pCharacter->name, mm9FormationCellRect(*cells, *pointedCell), s, width);
            }
        }
    }
}

void GameplayFormationBuilder::handleInput(
    GameplayScreenRuntime &context,
    const GameplayInputFrame &input,
    int width,
    int height)
{
    Mm9FormationBuilderState &builder = state(context);
    const std::optional<Mm9FormationGrid> cells = grid(context, width, height);

    if (!builder.open || !cells)
    {
        return;
    }

    const float x = input.pointerX;
    const float y = input.pointerY;

    if (input.leftMouseButton.pressed)
    {
        builder.pressedButton = controlAt(context, width, height, x, y);
        const std::optional<int32_t> cell = mm9FormationCellAt(*cells, x, y);
        const std::optional<size_t> occupant = cell ? mm9FormationOccupant(builder.cells, *cell) : std::nullopt;

        if (occupant)
        {
            const Mm9FormationRect face =
                cellPart(context, mm9FormationCellRect(*cells, *cell), "Mm9FormationFace", gridScale(context, width,
                    height));
            builder.dragged = occupant;
            builder.grabOffsetX = x - face.x;
            builder.grabOffsetY = y - face.y;
        }
    }

    if (!input.leftMouseButton.released)
    {
        return;
    }

    if (builder.dragged)
    {
        // Dropped on an empty cell it stays there; anywhere else (an occupied cell, outside the grid) it returns.
        const std::optional<int32_t> cell = mm9FormationCellAt(*cells, x, y);

        if (cell && mm9FormationMove(builder.cells, *builder.dragged, *cell))
        {
            builder.refused = false;
        }

        builder.dragged.reset();
        return;
    }

    const Mm9FormationButton pressed = builder.pressedButton;
    builder.pressedButton = Mm9FormationButton::None;

    if (pressed == Mm9FormationButton::None || controlAt(context, width, height, x, y) != pressed)
    {
        return;
    }

    if (pressed == Mm9FormationButton::Cancel)
    {
        close(context);
    }
    else
    {
        accept(context);
    }
}
}
