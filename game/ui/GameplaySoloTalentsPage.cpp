#include "game/ui/GameplaySoloTalentsPage.h"

#include "engine/Localization.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/party/Party.h"
#include "game/rules/SoloTalents.h"
#include "game/ui/GameplayObsidianPainter.h"

#include <algorithm>
#include <array>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
using GameplayObsidianColors::abgr;

// The page fills the window (user, 2026-11-14: the Skills page's frame was too small to read): a 800 x 450 canvas
// scaled to fit and centred, over a dark backdrop. Layout A of the talent tree v2 mockups
// (level_generation/ui/solo_talents_v2_20261114/): the points header, the keystone strip, the three trees, the Any-tree
// line, and the detail card at the right. Lone Discipline (innate) is not shown (user, 2026-11-14). Only learned
// talents wear a rim; a talent not yet learned shows none, and a locked one is greyed.
constexpr float CanvasWidth = 800;
constexpr float CanvasHeight = 450;
constexpr float ColumnLeft = 24;
constexpr float ColumnWidth = 186;
constexpr float KeystoneTop = 80;
constexpr float KeystoneLeft = 150;
constexpr float KeystoneWidth = 200;
constexpr float TreeHeaderTop = 126;
constexpr float RowTop = 152;
constexpr float RowHeight = 36;
constexpr float AnyTop = 374;
constexpr float RowWidth = ColumnWidth - 8;
constexpr float IconSize = 30;
constexpr float CardLeft = 594;
constexpr float CardTop = 78;
constexpr float CardWidth = 184;
constexpr float CardBottom = 432;
constexpr float BackX = 640;
constexpr float BackY = 18;
constexpr float BackWidth = 138;
constexpr float BackHeight = 28;
// The Skills page's Talents switch: the bottom-right panel's slot above the Workbench button (CharacterAlchemyButton),
// where the inventory page has Sort.
constexpr float SwitchAboveWorkbench = 34;

constexpr uint32_t Ivory = abgr(0xefe0bc);
constexpr uint32_t Gold = abgr(0xf2d27a);
constexpr uint32_t Grey = abgr(0x7c807a);
constexpr uint32_t Body = abgr(0xc8c7a7);
constexpr uint32_t Refusal = abgr(0xe49a8c);
constexpr uint32_t Rule = abgr(0x907d9a, 0xab);
constexpr uint32_t HoverFill = abgr(0xe3c185, 0x22);
constexpr uint32_t IconBack = abgr(0x151b1c);
constexpr uint32_t PipOff = abgr(0x3a3428);
constexpr uint32_t Backdrop = abgr(0x0b0e10, 0xf4);
constexpr uint32_t CardFill = abgr(0x000000, 0x50);

const std::array<TalentTree, 3> Trees = {TalentTree::Arms, TalentTree::Archery, TalentTree::Arcana};

std::string treeName(TalentTree tree)
{
    return tree == TalentTree::Arms  ? Engine::tr("Arms")
        : tree == TalentTree::Archery ? Engine::tr("Archery")
        : tree == TalentTree::Arcana  ? Engine::tr("Arcana")
                                      : Engine::tr("Any tree");
}

// What a hover index names: the table's talents first, then its keystones.
enum class EntryKind : uint8_t
{
    None,
    Talent,
    Keystone,
};

struct Entry
{
    EntryKind kind = EntryKind::None;
    const TalentDefinition *pDefinition = nullptr;
};

Entry entryAt(const SoloTalentTable &table, size_t index)
{
    if (index < table.talents().size())
    {
        return {EntryKind::Talent, &table.talents()[index]};
    }
    index -= table.talents().size();
    if (index < table.keystones().size())
    {
        return {EntryKind::Keystone, &table.keystones()[index]};
    }
    return {};
}

// A row on the page: its hover index (see entryAt) and its top-left corner in page units.
struct TalentRow
{
    size_t index = 0;
    float x = 0;
    float y = 0;
};

std::vector<TalentRow> layoutRows()
{
    std::vector<TalentRow> rows;
    const SoloTalentTable &table = soloTalentTable();
    const std::vector<TalentDefinition> &talents = table.talents();
    for (size_t column = 0; column < Trees.size(); ++column)
    {
        float y = RowTop;
        for (size_t index = 0; index < talents.size(); ++index)
        {
            if (talents[index].tree == Trees[column])
            {
                rows.push_back({index, ColumnLeft + float(column) * ColumnWidth, y});
                y += RowHeight;
            }
        }
    }
    // The Any-tree line.
    float x = ColumnLeft + 96;
    for (size_t index = 0; index < talents.size(); ++index)
    {
        if (talents[index].tree == TalentTree::Any)
        {
            rows.push_back({index, x, AnyTop});
            x += ColumnWidth;
        }
    }
    // The keystones' strip.
    for (size_t keystone = 0; keystone < table.keystones().size(); ++keystone)
    {
        rows.push_back({talents.size() + keystone, KeystoneLeft + float(keystone) * KeystoneWidth, KeystoneTop});
    }
    return rows;
}

// The canvas in the window: scaled to fit, centred.
GameplayResolvedHudLayoutElement canvasRect(int width, int height)
{
    const float scale = std::max(0.01f, std::min(float(width) / CanvasWidth, float(height) / CanvasHeight));
    return {(float(width) - CanvasWidth * scale) / 2, (float(height) - CanvasHeight * scale) / 2,
        CanvasWidth * scale, CanvasHeight * scale, scale};
}

// The Skills page's Talents switch, above the Workbench button (window pixels).
std::optional<GameplayResolvedHudLayoutElement> switchRect(const GameplayScreenRuntime &context, int width, int height)
{
    std::optional<GameplayResolvedHudLayoutElement> button =
        const_cast<GameplayScreenRuntime &>(context).resolveHudLayoutElement("CharacterAlchemyButton", width, height,
            0, 0);
    if (button)
    {
        button->y -= SwitchAboveWorkbench * button->scale;
    }
    return button;
}

bool inside(const GameplayResolvedHudLayoutElement &box, float x, float y)
{
    return x >= box.x && x <= box.x + box.width && y >= box.y && y <= box.y + box.height;
}

// Wrapped lines from y down; returns the y below them.
float paragraph(const GameplayObsidianPainter &painter, const std::string &font, float height, uint32_t colour,
    const std::string &value, float x, float y, float width, float lineHeight)
{
    for (const std::string &line : painter.wrapped(font, height, value, width))
    {
        painter.text(font, height, colour, line, x, y);
        y += lineHeight;
    }
    return y;
}

Character *shownCharacter(GameplayScreenRuntime &context)
{
    return const_cast<Character *>(context.selectedCharacterScreenCharacter());
}

void drawIcon(GameplayScreenRuntime &context, const GameplayObsidianPainter &painter, const TalentDefinition &talent,
    const GameplayObsidianRect &box, bool dim)
{
    painter.fill(box, IconBack);
    if (talent.iconSpell != 0)
    {
        painter.spellIcon(talent.iconSpell, box, dim);
    }
    else if (const std::optional<GameplayHudTextureHandle> texture =
                 context.gameplayUiRuntime().ensureItemIconTextureLoaded(talent.iconItem);
             texture && texture->width > 0 && texture->height > 0)
    {
        const float fit = std::min(box.width / texture->width, box.height / texture->height);
        context.gameplayUiRuntime().submitHudTexturedQuad(texture->textureHandle,
            box.x + (box.width - texture->width * fit) / 2, box.y + (box.height - texture->height * fit) / 2,
            texture->width * fit, texture->height * fit);
        if (dim)
        {
            painter.fill(box, abgr(0x000000, 0x90));
        }
    }
}

// Puts an active talent on the first free key of the bar's main row, unless it is there already.
bool putOnBar(Character &member, size_t talentIndex)
{
    for (const ActionBarSlot &slot : member.actionBar)
    {
        if (slot.kind == ActionBarSlotKind::Talent && slot.id == talentIndex)
        {
            return false;
        }
    }
    for (size_t slot = 0; slot < ActionBarSlotCount / 2; ++slot)
    {
        if (member.actionBar[slot].kind == ActionBarSlotKind::Empty)
        {
            member.actionBar[slot] = {ActionBarSlotKind::Talent, uint32_t(talentIndex), {}};
            return true;
        }
    }
    return false;
}
}

bool GameplaySoloTalentsPage::switchShown(const GameplayScreenRuntime &context)
{
    const GameplayUiController::CharacterScreenState &screen = context.characterScreenReadOnly();
    return context.soloTalents() && screen.open && screen.page == GameplayUiController::CharacterPage::Skills
        && screen.source == GameplayUiController::CharacterScreenSource::Party && !soloTalentTable().talents().empty();
}

bool GameplaySoloTalentsPage::pageShown(const GameplayScreenRuntime &context)
{
    return switchShown(context) && context.characterScreenReadOnly().talentsView;
}

void GameplaySoloTalentsPage::render(GameplayScreenRuntime &context, int width, int height)
{
    if (!switchShown(context))
    {
        return;
    }
    const Character *pMember = context.selectedCharacterScreenCharacter();
    if (pMember == nullptr)
    {
        return;
    }
    const GameplayUiController::CharacterScreenState &screen = context.characterScreenReadOnly();
    const GameplayInputFrame *pInput = context.currentGameplayInputFrame();
    const float pointerX = pInput != nullptr ? pInput->pointerX : -1.0f;
    const float pointerY = pInput != nullptr ? pInput->pointerY : -1.0f;

    if (!screen.talentsView)
    {
        // The switch to the talents, in the bottom-right panel above the Workbench button.
        if (const std::optional<GameplayResolvedHudLayoutElement> button = switchRect(context, width, height))
        {
            const GameplayObsidianPainter painter(context, *button);
            const bool hovered = inside(*button, pointerX, pointerY);
            const GameplayObsidianRect box = painter.rect(0, 0, button->width / button->scale,
                button->height / button->scale);
            painter.texture(hovered ? "obsidian_button_tab_hover" : "obsidian_button_tab_normal", box);
            painter.text("Fondamento", 13, abgr(0xe8d1a4), Engine::tr("Talents"), box.width / button->scale / 2,
                5.5f, 1);
        }
        return;
    }

    const GameplayResolvedHudLayoutElement canvas = canvasRect(width, height);
    const GameplayObsidianPainter backdrop(context, {0, 0, float(width), float(height), 1.0f});
    backdrop.fill(backdrop.rect(0, 0, float(width), float(height)), Backdrop);
    const GameplayObsidianPainter painter(context, canvas);
    painter.texture("obsidian_skills_surface", painter.rect(0, 0, CanvasWidth, CanvasHeight));
    painter.frame(painter.rect(0, 0, CanvasWidth, CanvasHeight), Rule);

    const SoloTalentTable &table = soloTalentTable();
    painter.text("Fondamento", 26, Gold, Engine::tr("Talents"), 28, 12);
    const int available = talentPointsAvailable(table, *pMember);
    painter.text("Lucida", 12, available > 0 ? Gold : Body,
        Engine::tr("{name}: {available} of {total} points to spend · the next at level {level}",
            {{"name", pMember->name}, {"available", int64_t(available)},
                {"total", int64_t(talentPointsTotal(table, *pMember))},
                {"level", int64_t(nextTalentPointLevel(table, *pMember))}}),
        30, 46);
    const bool backHovered = painter.rect(BackX, BackY, BackWidth, BackHeight).contains(pointerX, pointerY);
    painter.button(painter.rect(BackX, BackY, BackWidth, BackHeight), Engine::tr("Back to Skills"), false, true,
        backHovered, false);
    painter.text("Lucida", 9, Grey, Engine::tr("or Esc"), BackX + BackWidth / 2, BackY + BackHeight + 3, 1);
    painter.fill(painter.rect(24, 68, CardLeft - 40, 0.8f), Rule);

    const int slots = keystoneSlots(table, *pMember);
    painter.text("Fondamento", 17, Gold, Engine::tr("Keystones"), ColumnLeft + 2, KeystoneTop + 1);
    painter.text("Lucida", 10, Grey, Engine::tr("{bound} of {slots} bound",
        {{"bound", int64_t(keystonesBound(table, *pMember))}, {"slots", int64_t(slots)}}), ColumnLeft + 2,
        KeystoneTop + 22);
    painter.fill(painter.rect(24, TreeHeaderTop - 8, CardLeft - 40, 0.8f), Rule);

    for (size_t column = 0; column < Trees.size(); ++column)
    {
        painter.text("Fondamento", 17, Gold, treeName(Trees[column]), ColumnLeft + float(column) * ColumnWidth + 2,
            TreeHeaderTop);
    }
    painter.text("Fondamento", 17, Gold, treeName(TalentTree::Any), ColumnLeft + 2, AnyTop + 4);

    for (const TalentRow &row : layoutRows())
    {
        const Entry entry = entryAt(table, row.index);
        const bool hovered = screen.talentHover && *screen.talentHover == row.index;
        if (hovered)
        {
            painter.fill(painter.rect(row.x - 3, row.y - 2, RowWidth, RowHeight - 2), HoverFill);
        }
        const GameplayObsidianRect icon = painter.rect(row.x, row.y, IconSize, IconSize);
        const TalentDefinition &talent = *entry.pDefinition;
        const float textX = row.x + IconSize + 8;
        const float textWidth = RowWidth - IconSize - 12;
        if (entry.kind == EntryKind::Keystone)
        {
            const bool bound = hasKeystone(*pMember, talent.id);
            const bool open = keystoneBindRefusal(table, *pMember, talent).empty();
            drawIcon(context, painter, talent, icon, !bound && !open);
            if (bound)
            {
                painter.frame(icon, Gold);
                painter.frame(painter.rect(row.x - 2, row.y - 2, IconSize + 4, IconSize + 4), Gold);
            }
            painter.text("Fondamento", 15, bound ? Ivory : open ? Body : Grey,
                painter.fitted("Fondamento", 15, Engine::tr(talent.name), textWidth), textX, row.y);
            painter.text("Lucida", 10, bound ? Gold : open ? Body : Grey,
                bound ? Engine::tr("bound") : open ? Engine::tr("click to bind") : Engine::tr("no open slot"),
                textX, row.y + 19);
            continue;
        }
        const int rank = talentRank(*pMember, talent.id);
        const bool learnable = talentLearnRefusal(table, *pMember, talent).empty();
        const bool locked = !learnable && rank == 0;
        drawIcon(context, painter, talent, icon, locked);
        // Learned: a gold rim (a double one on actives). Not learned: none.
        if (rank > 0)
        {
            painter.frame(icon, Gold);
            if (talent.kind == TalentKind::Active)
            {
                painter.frame(painter.rect(row.x - 2, row.y - 2, IconSize + 4, IconSize + 4), Gold);
            }
        }
        const std::string rankText = std::to_string(rank) + "/" + std::to_string(talent.maxRank);
        const float rankWidth = painter.width("Lucida", 11, rankText) + 4;
        painter.text("Fondamento", 14, locked ? Grey : rank > 0 ? Ivory : Body,
            painter.fitted("Fondamento", 14, Engine::tr(talent.name), textWidth - rankWidth), textX, row.y);
        painter.text("Lucida", 11, rank > 0 ? Gold : Grey, rankText, row.x + RowWidth - 4, row.y + 2, 2);
        for (int pip = 0; pip < talent.maxRank; ++pip)
        {
            painter.fill(painter.rect(textX + float(pip) * 11, row.y + 21, 7, 7), pip < rank ? Gold : PipOff);
        }
    }

    // The detail card at the right.
    painter.fill(painter.rect(CardLeft - 6, CardTop - 6, CardWidth + 12, CardBottom - CardTop + 12), CardFill);
    painter.frame(painter.rect(CardLeft - 6, CardTop - 6, CardWidth + 12, CardBottom - CardTop + 12), Rule);
    const std::optional<size_t> hover = screen.talentHover;
    const Entry entry = hover ? entryAt(table, *hover) : Entry{};
    constexpr float Line = 17;
    if (hover && entry.kind == EntryKind::Talent && entry.pDefinition != nullptr)
    {
        const TalentDefinition &talent = *entry.pDefinition;
        const int rank = talentRank(*pMember, talent.id);
        float y = paragraph(painter, "Fondamento", 18, Ivory, Engine::tr(talent.name), CardLeft, CardTop, CardWidth,
            22);
        const std::string kind = talent.kind == TalentKind::Active
            ? Engine::tr("Active · cooldown {seconds} s",
                  {{"seconds", int64_t(std::lround(talentCooldownSeconds(talent, std::max(rank, 1))))}})
            : Engine::tr("Passive");
        y = paragraph(painter, "Lucida", 11, Gold, treeName(talent.tree) + " · " + kind, CardLeft, y + 2, CardWidth,
            15) + 8;
        if (rank > 0)
        {
            y = paragraph(painter, "Lucida", 12, Body, Engine::tr("Now (rank {rank}): {effect}",
                {{"rank", int64_t(rank)}, {"effect", talentEffectText(talent, rank)}}), CardLeft, y, CardWidth, Line)
                + 8;
        }
        if (rank < talent.maxRank)
        {
            y = paragraph(painter, "Lucida", 12, Ivory, Engine::tr("Next (rank {rank}): {effect}",
                {{"rank", int64_t(rank + 1)}, {"effect", talentEffectText(talent, rank + 1)}}), CardLeft, y,
                CardWidth, Line) + 8;
        }
        const std::string refusal = talentLearnRefusal(table, *pMember, talent);
        if (!refusal.empty())
        {
            paragraph(painter, "Lucida", 12, Refusal, refusal, CardLeft, y, CardWidth, Line);
        }
        paragraph(painter, "Lucida", 10, Grey,
            talent.kind == TalentKind::Active ? Engine::tr("Click: learn a rank. Right click: put on the action bar.")
                                              : Engine::tr("Click: learn a rank."),
            CardLeft, CardBottom - 28, CardWidth, 13);
    }
    else if (hover && entry.kind == EntryKind::Keystone && entry.pDefinition != nullptr)
    {
        const TalentDefinition &keystone = *entry.pDefinition;
        float y = paragraph(painter, "Fondamento", 18, Ivory, Engine::tr(keystone.name), CardLeft, CardTop,
            CardWidth, 22);
        y = paragraph(painter, "Lucida", 11, Gold, Engine::tr("Keystone · costs no points · one per open slot"),
            CardLeft, y + 2, CardWidth, 15) + 8;
        y = paragraph(painter, "Lucida", 12, Body, Engine::tr(keystone.text), CardLeft, y, CardWidth, Line) + 8;
        const std::string refusal = keystoneBindRefusal(table, *pMember, keystone);
        if (!refusal.empty() && !hasKeystone(*pMember, keystone.id))
        {
            paragraph(painter, "Lucida", 12, Refusal, refusal, CardLeft, y, CardWidth, Line);
        }
        paragraph(painter, "Lucida", 10, Grey,
            Engine::tr("Click: bind it (until you forget your talents at a training hall)."), CardLeft,
            CardBottom - 28, CardWidth, 13);
    }
    else
    {
        const uint32_t nextSlot = nextKeystoneLevel(table, *pMember);
        float y = paragraph(painter, "Fondamento", 18, Ivory, Engine::tr("Talents"), CardLeft, CardTop, CardWidth,
            22) + 4;
        y = paragraph(painter, "Lucida", 12, Body, Engine::tr("One point every {levels} levels. Forget them for free "
            "at any training hall.", {{"levels", int64_t(table.levelsPerPoint())}}), CardLeft, y, CardWidth, Line)
            + 8;
        y = paragraph(painter, "Lucida", 12, Body, nextSlot > 0
                ? Engine::tr("Keystone slots: {slots} open; the next opens at level {level}.",
                      {{"slots", int64_t(slots)}, {"level", int64_t(nextSlot)}})
                : Engine::tr("Keystone slots: {slots} open.", {{"slots", int64_t(slots)}}),
            CardLeft, y, CardWidth, Line) + 8;
        paragraph(painter, "Lucida", 12, Grey, Engine::tr("Point at a talent to read it."), CardLeft, y, CardWidth,
            Line);
    }
}

bool GameplaySoloTalentsPage::coversPointer(const GameplayScreenRuntime &context, const GameplayInputFrame &)
{
    // The page fills the window.
    return pageShown(context);
}

bool GameplaySoloTalentsPage::handleInput(GameplayScreenRuntime &context, const GameplayInputFrame &input)
{
    if (!switchShown(context))
    {
        return false;
    }
    Character *pMember = shownCharacter(context);
    if (pMember == nullptr)
    {
        return false;
    }
    GameplayUiController::CharacterScreenState &screen = context.characterScreen();
    const bool anyButton = input.leftMouseButton.pressed || input.leftMouseButton.held
        || input.leftMouseButton.released || input.rightMouseButton.pressed || input.rightMouseButton.held
        || input.rightMouseButton.released;

    if (!screen.talentsView)
    {
        const std::optional<GameplayResolvedHudLayoutElement> button =
            switchRect(context, input.screenWidth, input.screenHeight);
        if (button && inside(*button, input.pointerX, input.pointerY))
        {
            if (input.leftMouseButton.pressed)
            {
                screen.talentsView = true;
                screen.talentHover.reset();
            }
            return anyButton;
        }
        return false;
    }

    // Esc goes back to the skills (the character screen stays open while it is held: the alchemy bench's latch).
    // The same key state the character screen's own Esc check reads.
    const bool *pKeys = input.keyboardState();
    if (pKeys != nullptr && pKeys[SDL_SCANCODE_ESCAPE] && !context.interactionState().alchemyBenchEscapeLatch)
    {
        context.interactionState().alchemyBenchEscapeLatch = true;
        screen.talentsView = false;
        screen.talentHover.reset();
        return true;
    }

    const GameplayResolvedHudLayoutElement canvas = canvasRect(input.screenWidth, input.screenHeight);
    const float localX = (input.pointerX - canvas.x) / canvas.scale;
    const float localY = (input.pointerY - canvas.y) / canvas.scale;
    if (localX >= BackX && localX <= BackX + BackWidth && localY >= BackY && localY <= BackY + BackHeight)
    {
        screen.talentHover.reset();
        if (input.leftMouseButton.pressed)
        {
            screen.talentsView = false;
        }
        return true;
    }

    screen.talentHover.reset();
    for (const TalentRow &row : layoutRows())
    {
        if (localX >= row.x - 3 && localX <= row.x + RowWidth - 3 && localY >= row.y - 2
            && localY <= row.y + RowHeight - 4)
        {
            screen.talentHover = row.index;
        }
    }
    const SoloTalentTable &table = soloTalentTable();
    const Entry entry = screen.talentHover ? entryAt(table, *screen.talentHover) : Entry{};
    if (entry.kind == EntryKind::Keystone && entry.pDefinition != nullptr && input.leftMouseButton.pressed)
    {
        const TalentDefinition &keystone = *entry.pDefinition;
        if (bindKeystone(table, *pMember, keystone.id))
        {
            context.setStatusBarEvent(Engine::tr("{name} binds {keystone}",
                {{"name", pMember->name}, {"keystone", Engine::tr(keystone.name)}}));
        }
        else
        {
            context.setStatusBarEvent(keystoneBindRefusal(table, *pMember, keystone));
        }
    }
    if (entry.kind == EntryKind::Talent)
    {
        const TalentDefinition &talent = table.talents()[*screen.talentHover];
        if (input.leftMouseButton.pressed)
        {
            if (learnTalent(table, *pMember, talent.id))
            {
                if (Party *pParty = context.party())
                {
                    pParty->refreshDerivedState();
                }
                context.setStatusBarEvent(Engine::tr("{name} learns {talent} (rank {rank})",
                    {{"name", pMember->name}, {"talent", Engine::tr(talent.name)},
                        {"rank", int64_t(talentRank(*pMember, talent.id))}}));
            }
            else
            {
                context.setStatusBarEvent(talentLearnRefusal(table, *pMember, talent));
            }
        }
        else if (input.rightMouseButton.pressed && talent.kind == TalentKind::Active
            && talentRank(*pMember, talent.id) > 0)
        {
            context.setStatusBarEvent(putOnBar(*pMember, *screen.talentHover)
                    ? Engine::tr("{talent} is on the action bar", {{"talent", Engine::tr(talent.name)}})
                    : Engine::tr("{talent} is already on the bar, or the bar is full",
                          {{"talent", Engine::tr(talent.name)}}));
        }
    }
    // The page fills the window: every click is its own.
    return true;
}
}
