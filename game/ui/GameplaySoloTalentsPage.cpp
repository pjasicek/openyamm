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

// Page units of CharacterSkillsPage (468 x 346).
constexpr float SwitchX = 372;
constexpr float SwitchY = 7;
constexpr float SwitchWidth = 82;
constexpr float SwitchHeight = 20;
constexpr float ColumnLeft = 14;
constexpr float ColumnWidth = 148;
constexpr float RowTop = 64;
constexpr float RowHeight = 29;
constexpr float IconSize = 22;
constexpr float CardTop = 246;

constexpr uint32_t Ivory = abgr(0xefe0bc);
constexpr uint32_t Gold = abgr(0xf2d27a);
constexpr uint32_t Teal = abgr(0x59d2c8);
constexpr uint32_t Grey = abgr(0x7c807a);
constexpr uint32_t Body = abgr(0xc8c7a7);
constexpr uint32_t Refusal = abgr(0xe49a8c);
constexpr uint32_t Rule = abgr(0x907d9a, 0xab);
constexpr uint32_t HoverFill = abgr(0xe3c185, 0x22);
constexpr uint32_t IconBack = abgr(0x151b1c);
constexpr uint32_t PipOff = abgr(0x3a3428);

const std::array<TalentTree, 3> Trees = {TalentTree::Melee, TalentTree::Ranged, TalentTree::Caster};

std::string treeName(TalentTree tree)
{
    return tree == TalentTree::Melee ? Engine::tr("Melee")
        : tree == TalentTree::Ranged ? Engine::tr("Ranged")
                                     : Engine::tr("Caster");
}

// A talent's row on the page: its index in the table and its rectangle in page units.
struct TalentRow
{
    size_t index = 0;
    float x = 0;
    float y = 0;
};

std::vector<TalentRow> layoutRows()
{
    std::vector<TalentRow> rows;
    const std::vector<TalentDefinition> &talents = soloTalentTable().talents();
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
    return rows;
}

std::optional<GameplayResolvedHudLayoutElement> pageRect(const GameplayScreenRuntime &context, int width, int height)
{
    return const_cast<GameplayScreenRuntime &>(context).resolveHudLayoutElement("CharacterSkillsPage", width, height,
        0, 0);
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
    const std::optional<GameplayResolvedHudLayoutElement> page = pageRect(context, width, height);
    const Character *pMember = context.selectedCharacterScreenCharacter();
    if (!page || pMember == nullptr)
    {
        return;
    }
    const GameplayObsidianPainter painter(context, *page);
    const GameplayUiController::CharacterScreenState &screen = context.characterScreenReadOnly();
    const bool talents = screen.talentsView;

    if (talents)
    {
        const SoloTalentTable &table = soloTalentTable();
        painter.texture("obsidian_skills_surface", painter.rect(0, 0, 468, 346));
        painter.text("Fondamento", 15, Gold, Engine::tr("Talents"), 20, 9);
        const int available = talentPointsAvailable(table, *pMember);
        painter.text("Lucida", 8.5f, available > 0 ? Teal : Body,
            Engine::tr("{available} of {total} points to spend · the next at level {level}",
                {{"available", int64_t(available)}, {"total", int64_t(talentPointsTotal(table, *pMember))},
                    {"level", int64_t(nextTalentPointLevel(table, *pMember))}}),
            20, 29);
        painter.fill(painter.rect(18, 42, 432, 0.6f), Rule);

        for (size_t column = 0; column < Trees.size(); ++column)
        {
            painter.text("Arrus", 10, Gold, treeName(Trees[column]), ColumnLeft + float(column) * ColumnWidth + 2, 47);
        }

        for (const TalentRow &row : layoutRows())
        {
            const TalentDefinition &talent = table.talents()[row.index];
            const int rank = talentRank(*pMember, talent.id);
            const bool learnable = talentLearnRefusal(table, *pMember, talent).empty();
            const bool locked = !learnable && rank == 0;
            if (screen.talentHover && *screen.talentHover == row.index)
            {
                painter.fill(painter.rect(row.x - 2, row.y - 1, ColumnWidth - 4, RowHeight - 2), HoverFill);
            }
            const GameplayObsidianRect icon = painter.rect(row.x, row.y + 2, IconSize, IconSize);
            drawIcon(context, painter, talent, icon, locked);
            // Actives wear a double rim, passives a single one; gold when learned, teal when learnable now.
            const uint32_t rim = rank > 0 ? Gold : learnable ? Teal : Grey;
            painter.frame(icon, rim);
            if (talent.kind == TalentKind::Active)
            {
                painter.frame(painter.rect(row.x - 1.5f, row.y + 0.5f, IconSize + 3, IconSize + 3), rim);
            }
            painter.text("Arrus", 9, locked ? Grey : learnable ? Teal : Ivory, Engine::tr(talent.name), row.x + 28,
                row.y + 2);
            for (int pip = 0; pip < talent.maxRank; ++pip)
            {
                const uint32_t colour = pip < rank ? Gold : pip == rank && learnable ? Teal : PipOff;
                painter.fill(painter.rect(row.x + 28 + float(pip) * 7, row.y + 16, 4.5f, 4.5f), colour);
            }
            painter.text("SMALLNUM", 6.5f, rank > 0 ? Gold : Grey,
                std::to_string(rank) + "/" + std::to_string(talent.maxRank), row.x + ColumnWidth - 8, row.y + 3, 2);
        }

        painter.fill(painter.rect(18, CardTop - 6, 432, 0.6f), Rule);
        if (screen.talentHover && *screen.talentHover < table.talents().size())
        {
            const TalentDefinition &talent = table.talents()[*screen.talentHover];
            const int rank = talentRank(*pMember, talent.id);
            painter.text("Fondamento", 12, Ivory, Engine::tr(talent.name), 20, CardTop);
            std::string kind = talent.kind == TalentKind::Active
                ? Engine::tr("Active · cooldown {seconds} s",
                      {{"seconds", int64_t(std::lround(talentCooldownSeconds(talent, std::max(rank, 1))))}})
                : Engine::tr("Passive");
            painter.text("Lucida", 8, Gold, treeName(talent.tree) + " · " + kind, 20, CardTop + 16);
            float y = CardTop + 30;
            if (rank > 0)
            {
                painter.text("Lucida", 8.5f, Body, Engine::tr("Now (rank {rank}): {effect}",
                    {{"rank", int64_t(rank)}, {"effect", talentEffectText(talent, rank)}}), 20, y);
                y += 13;
            }
            if (rank < talent.maxRank)
            {
                painter.text("Lucida", 8.5f, Teal, Engine::tr("Next (rank {rank}): {effect}",
                    {{"rank", int64_t(rank + 1)}, {"effect", talentEffectText(talent, rank + 1)}}), 20, y);
                y += 13;
            }
            const std::string refusal = talentLearnRefusal(soloTalentTable(), *pMember, talent);
            if (!refusal.empty())
            {
                painter.text("Lucida", 8.5f, Refusal, refusal, 20, y);
                y += 13;
            }
            painter.text("Lucida", 7.5f, Grey,
                talent.kind == TalentKind::Active ? Engine::tr("Click: learn a rank · Right click: put on the action bar")
                                                  : Engine::tr("Click: learn a rank"),
                20, 330);
        }
        else
        {
            painter.text("Lucida", 8.5f, Body, Engine::tr("One point every 10 levels. Forget them for free at any "
                "training hall."), 20, CardTop);
        }
    }

    const GameplayObsidianRect switchBox = painter.rect(SwitchX, SwitchY, SwitchWidth, SwitchHeight);
    painter.button(switchBox, talents ? Engine::tr("Skills") : Engine::tr("Talents"), false, true, false, false);
}

bool GameplaySoloTalentsPage::coversPointer(const GameplayScreenRuntime &context, const GameplayInputFrame &input)
{
    if (!pageShown(context))
    {
        return false;
    }
    const std::optional<GameplayResolvedHudLayoutElement> page =
        pageRect(context, input.screenWidth, input.screenHeight);
    return page && input.pointerX >= page->x && input.pointerX <= page->x + page->width && input.pointerY >= page->y
        && input.pointerY <= page->y + page->height;
}

bool GameplaySoloTalentsPage::handleInput(GameplayScreenRuntime &context, const GameplayInputFrame &input)
{
    if (!switchShown(context))
    {
        return false;
    }
    const std::optional<GameplayResolvedHudLayoutElement> page =
        pageRect(context, input.screenWidth, input.screenHeight);
    Character *pMember = shownCharacter(context);
    if (!page || pMember == nullptr)
    {
        return false;
    }
    GameplayUiController::CharacterScreenState &screen = context.characterScreen();
    const float localX = (input.pointerX - page->x) / page->scale;
    const float localY = (input.pointerY - page->y) / page->scale;
    const bool onSwitch = localX >= SwitchX && localX <= SwitchX + SwitchWidth && localY >= SwitchY
        && localY <= SwitchY + SwitchHeight;
    const bool anyButton = input.leftMouseButton.pressed || input.leftMouseButton.held
        || input.leftMouseButton.released || input.rightMouseButton.pressed || input.rightMouseButton.held
        || input.rightMouseButton.released;

    if (onSwitch)
    {
        if (input.leftMouseButton.pressed)
        {
            screen.talentsView = !screen.talentsView;
            screen.talentHover.reset();
        }
        return anyButton;
    }
    if (!screen.talentsView)
    {
        return false;
    }

    const bool insidePage = localX >= 0 && localX <= 468 && localY >= 0 && localY <= 346;
    screen.talentHover.reset();
    for (const TalentRow &row : layoutRows())
    {
        if (localX >= row.x - 2 && localX <= row.x + ColumnWidth - 6 && localY >= row.y - 1
            && localY <= row.y + RowHeight - 3)
        {
            screen.talentHover = row.index;
        }
    }
    if (screen.talentHover && insidePage)
    {
        const SoloTalentTable &table = soloTalentTable();
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
    return insidePage && anyButton;
}
}
