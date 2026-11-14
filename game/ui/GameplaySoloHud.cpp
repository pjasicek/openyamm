#include "game/ui/GameplaySoloHud.h"

#include "game/rules/SoloTalents.h"

#include "engine/Localization.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/items/QuickItemSlots.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SkillData.h"
#include "game/party/SpellIds.h"
#include "game/rules/GameRules.h"
#include "game/tables/ItemTable.h"
#include "game/tables/SpellTable.h"
#include "game/ui/GameplayBuffHud.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayMapProgressBar.h"
#include "game/ui/GameplayObsidianPainter.h"
#include "game/ui/GameplayUiRuntime.h"
#include "game/ui/GameplayUiSkin.h"
#include "game/ui/SoloHudLayout.h"

#include <SDL3/SDL_scancode.h>
#include <SDL3/SDL_timer.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
using GameplayObsidianColors::abgr;

constexpr uint32_t NameGold = abgr(0xf2d27a);
constexpr uint32_t Ivory = abgr(0xefe0bc);
constexpr uint32_t Muted = abgr(0xb8b49c);
constexpr uint32_t Dark = abgr(0x040708);
constexpr uint32_t BoxRule = abgr(0xa8925f, 0x66);
constexpr uint32_t Brass = abgr(0x8a7a52);
constexpr uint32_t Backing = abgr(0x161d1c);
constexpr uint32_t SlotFill = abgr(0x0b1012);
constexpr uint32_t EmptyFill = abgr(0x0a0e0f);
constexpr uint32_t EmptyEdge = abgr(0x4a4434);
constexpr uint32_t ManaText = abgr(0xa8d0ff);
constexpr uint32_t RecoveryShade = abgr(0x040608, 0x9c);
// A talent's cooldown shade, and the gold frame of a talent whose effect runs.
constexpr uint32_t CooldownShade = abgr(0x040608, 0xbc);
constexpr uint32_t TalentGold = abgr(0xf2d27a);
constexpr uint32_t NoManaVeil = abgr(0x2050c0, 0x60);
constexpr uint32_t DebuffEdge = abgr(0xc6473a);
constexpr uint32_t TileEdge = abgr(0xa58f5f);
constexpr uint32_t TrailFill = abgr(0xe4c793);
constexpr uint32_t ReservedFill = abgr(0x0d1a14, 0xd0);
constexpr uint32_t ShieldLine = abgr(0x4ad2f0);
constexpr uint32_t Expiring = abgr(0xf2c66b);

constexpr std::array<SDL_Scancode, 10> BarKeys = {SDL_SCANCODE_1, SDL_SCANCODE_2, SDL_SCANCODE_3, SDL_SCANCODE_4,
    SDL_SCANCODE_5, SDL_SCANCODE_6, SDL_SCANCODE_7, SDL_SCANCODE_8, SDL_SCANCODE_9, SDL_SCANCODE_0};
constexpr std::array<const char *, 10> BarKeyNames = {"1", "2", "3", "4", "5", "6", "7", "8", "9", "0"};

// The Obsidian painter with its ellipse open to the solo HUD.
class SoloPainter : public GameplayObsidianPainter
{
public:
    using GameplayObsidianPainter::GameplayObsidianPainter;

    void oval(uint32_t colour, const Rect &box) const
    {
        ellipse(solid(colour), box);
    }

    Rect at(const SoloHudRect &rect) const
    {
        return this->rect(rect.x, rect.y, rect.width, rect.height);
    }
};

GameplayResolvedHudLayoutElement resolved(const GameplayObsidianRect &rect, float scale)
{
    return {rect.x, rect.y, rect.width, rect.height, scale};
}

// A brass ring drawn round a box, as the party frame's rims are.
void ring(GameplayScreenRuntime &context, const GameplayObsidianRect &box, float scale, float stroke)
{
    GameplayUiSkin::renderArc(context, resolved(box, scale), stroke, 0, 360, GameplayUiSkin::ArcMaterial::NormalRim);
}

std::string durationText(float seconds)
{
    const int whole = int(std::ceil(std::max(seconds, 0.0f)));
    return whole >= 3600 ? std::to_string((whole + 3599) / 3600) + "h"
        : whole >= 60 ? std::to_string((whole + 59) / 60) + "m" : std::to_string(whole) + "s";
}

// One tile of the buff rows: what it shows and where it points.
struct BuffTile
{
    uint32_t key = 0;
    std::string icon;
    std::optional<uint32_t> spellIcon;
    float remainingSeconds = 0;
    bool debuff = false;
    GameplayHudPointerTarget target;
};

const char *characterBuffIcon(CharacterBuffId id)
{
    switch (id)
    {
        case CharacterBuffId::Bless: return "obsidian_buff_sbs02a";
        case CharacterBuffId::Fate: return "obsidian_buff_sbs03a";
        case CharacterBuffId::Preservation: return "obsidian_buff_sbl08a";
        case CharacterBuffId::Regeneration: return "obsidian_buff_sbb07a";
        case CharacterBuffId::FireAura: return "obsidian_buff_sbf08a";
        case CharacterBuffId::PainReflection:
        case CharacterBuffId::VampiricWeapon:
        case CharacterBuffId::Hammerhands: return "obsidian_buff_sbdk07a";
        case CharacterBuffId::Mistform: return "obsidian_buff_sba08a";
        case CharacterBuffId::Glamour: return "obsidian_buff_sbde01a";
        case CharacterBuffId::Haste: return "obsidian_buff_sbf05a";
        case CharacterBuffId::Heroism: return "obsidian_buff_sbs07a";
        case CharacterBuffId::Shield: return "obsidian_buff_sba06a";
        case CharacterBuffId::Stoneskin: return "obsidian_buff_sbe05a";
        case CharacterBuffId::WaterBreathing: return "obsidian_buff_sbw05a";
        case CharacterBuffId::FireResistance: return "obsidian_buff_sbf03a";
        case CharacterBuffId::AirResistance: return "obsidian_buff_sba03a";
        case CharacterBuffId::WaterResistance: return "obsidian_buff_sbw03a";
        case CharacterBuffId::EarthResistance: return "obsidian_buff_sbe03a";
        case CharacterBuffId::MindResistance: return "obsidian_buff_sbm03a";
        case CharacterBuffId::BodyResistance: return "obsidian_buff_sbb03a";
        default: return "obsidian_buff_sbl09a";
    }
}

// The conditions the rows show (the medallion greys the face for the incapacitating ones): an icon each, from the
// enemy bars' debuff set, or the curing spell's icon where that set has none (poison, disease).
std::optional<BuffTile> conditionTile(CharacterCondition condition)
{
    BuffTile tile;
    tile.key = 300 + uint32_t(condition);
    tile.debuff = true;
    switch (condition)
    {
        case CharacterCondition::Cursed: tile.icon = "obsidian_debuff_dark_grasp"; break;
        case CharacterCondition::Weak: tile.icon = "obsidian_debuff_slow"; break;
        case CharacterCondition::Asleep: tile.icon = "obsidian_debuff_stun"; break;
        case CharacterCondition::Fear: tile.icon = "obsidian_debuff_fear"; break;
        case CharacterCondition::Drunk: tile.icon = "obsidian_debuff_charm"; break;
        case CharacterCondition::Insane: tile.icon = "obsidian_debuff_berserk"; break;
        case CharacterCondition::Paralyzed: tile.icon = "obsidian_debuff_paralyze"; break;
        case CharacterCondition::PoisonWeak:
        case CharacterCondition::PoisonMedium:
        case CharacterCondition::PoisonSevere: tile.spellIcon = spellIdValue(SpellId::CurePoison); break;
        case CharacterCondition::DiseaseWeak:
        case CharacterCondition::DiseaseMedium:
        case CharacterCondition::DiseaseSevere: tile.spellIcon = spellIdValue(SpellId::CureDisease); break;
        default: return std::nullopt;
    }
    return tile;
}

// The rows' contents, read from the party where they are drawn: party buffs (the movement ones keep their animated
// indicators), the member's own buffs and timed potion effects, then the conditions.
std::pair<std::vector<BuffTile>, std::vector<BuffTile>> buffTiles(const Party &party, size_t memberIndex,
    const Character &member)
{
    std::vector<BuffTile> buffs;
    std::vector<BuffTile> debuffs;
    for (size_t index = 0; index < PartyBuffCount; ++index)
    {
        const PartyBuffId id = PartyBuffId(index);
        const PartyBuffState *pBuff = party.partyBuff(id);
        const GameplayBuffHudDefinition &definition = GameplayBuffHudDefinitions[index];
        if (pBuff == nullptr || definition.presentation == GameplayBuffPresentation::Movement
            || definition.presentation == GameplayBuffPresentation::Special)
        {
            continue;
        }
        buffs.push_back({uint32_t(index), definition.pIcon, std::nullopt, pBuff->remainingSeconds, false,
            {GameplayHudPointerTargetType::PartyBuff, index}});
    }
    for (size_t index = 0; index < CharacterBuffCount; ++index)
    {
        const CharacterBuffState *pBuff = party.characterBuff(memberIndex, CharacterBuffId(index));
        if (pBuff == nullptr || !pBuff->active())
        {
            continue;
        }
        buffs.push_back({100 + uint32_t(index), characterBuffIcon(CharacterBuffId(index)), std::nullopt,
            pBuff->remainingSeconds, false, {GameplayHudPointerTargetType::PersonalBuffs, memberIndex}});
    }
    const std::vector<GameplayPotionEffectLine> potions = gameplayPotionEffectLines(member, nullptr);
    for (size_t index = 0; index < potions.size(); ++index)
    {
        buffs.push_back({200 + uint32_t(index), "obsidian_buff_combat", std::nullopt, potions[index].remainingSeconds,
            false, {GameplayHudPointerTargetType::PersonalBuffs, memberIndex}});
    }
    std::stable_sort(buffs.begin(), buffs.end(),
        [](const BuffTile &left, const BuffTile &right) { return left.remainingSeconds < right.remainingSeconds; });
    for (size_t index = 0; index < CharacterConditionCount; ++index)
    {
        if (member.conditions.test(index))
        {
            if (std::optional<BuffTile> tile = conditionTile(CharacterCondition(index)))
            {
                debuffs.push_back(*tile);
            }
        }
    }
    return {std::move(buffs), std::move(debuffs)};
}

// The sweep's whole for a tile: the longest remaining time seen while it has been shown.
float longestSeen(GameplayScreenRuntime &context, uint32_t key, float remaining)
{
    std::vector<std::pair<uint32_t, float>> &seen = context.interactionState().soloBuffLongestSeconds;
    for (std::pair<uint32_t, float> &entry : seen)
    {
        if (entry.first == key)
        {
            entry.second = std::max(entry.second, remaining);
            return entry.second;
        }
    }
    seen.emplace_back(key, remaining);
    return remaining;
}

void forgetUnshown(GameplayScreenRuntime &context, const std::vector<BuffTile> &shown)
{
    std::erase_if(context.interactionState().soloBuffLongestSeconds, [&shown](const std::pair<uint32_t, float> &entry)
    {
        return std::none_of(shown.begin(), shown.end(), [&entry](const BuffTile &tile) { return tile.key == entry.first; });
    });
}

void renderTile(GameplayScreenRuntime &context, const SoloPainter &painter, const BuffTile &tile, float x, float y,
    float size)
{
    const GameplayObsidianRect box = painter.rect(x, y, size, size);
    painter.fill(box, abgr(0x1b1f22));
    if (tile.spellIcon)
    {
        painter.spellIcon(*tile.spellIcon, box, false);
    }
    else
    {
        GameplayUiSkin::renderTexture(context, tile.icon, resolved(box, painter.scale()));
    }
    if (!tile.debuff && tile.remainingSeconds > 0)
    {
        const float spent = soloBuffSpent(tile.remainingSeconds, longestSeen(context, tile.key, tile.remainingSeconds));
        painter.fill({box.x, box.y, box.width, box.height * spent}, abgr(0x06080a, 0x9e));
        painter.text("SMALLNUM", 5.4f, tile.remainingSeconds < 30 ? Expiring : Ivory,
            durationText(tile.remainingSeconds), x + size / 2, y + size + 0.8f, 1);
    }
    painter.frame(box, tile.debuff ? DebuffEdge : TileEdge);
}

void renderMeter(GameplayScreenRuntime &context, const SoloPainter &painter, const SoloHudRect &area, float amount,
    float trail, float reserved, bool health, const std::string &label)
{
    const GameplayObsidianRect box = painter.at(area);
    painter.fill(box, Dark);
    const float inset = std::max(1.0f, painter.scale() * 0.5f);
    const GameplayResolvedHudLayoutElement inner = {box.x + inset, box.y + inset, box.width - 2 * inset,
        box.height - 2 * inset, painter.scale()};
    if (health && trail > amount)
    {
        const GameplayResolvedHudLayoutElement segment = GameplayUiSkin::meterSegment(inner, amount, trail, false);
        painter.fill({segment.x, segment.y, segment.width, segment.height}, TrailFill);
    }
    const std::optional<GameplayHudTextureHandle> texture = health
        ? GameplayUiSkin::healthMeterTexture(context, amount)
        : context.gameplayUiRuntime().ensureHudTextureLoaded("obsidian_hud_meter_sp");
    if (texture && amount > 0)
    {
        const GameplayResolvedHudLayoutElement segment = GameplayUiSkin::meterSegment(inner, 0, amount, false);
        context.gameplayUiRuntime().submitHudTexturedQuad(texture->textureHandle, segment.x, segment.y,
            segment.width, segment.height, 0, 0, amount, 1);
    }
    if (reserved > 0)
    {
        const GameplayResolvedHudLayoutElement segment = GameplayUiSkin::meterSegment(inner, 1 - reserved, 1, false);
        painter.fill({segment.x, segment.y, segment.width, segment.height}, ReservedFill);
    }
    painter.frame(box, Brass);
    painter.text("Arrus", area.height * 0.66f, Ivory, label, area.x + area.width / 2,
        area.y + area.height * 0.14f, 1);
}

// How far the buff rows move down, in layout units, to clear MAW's progress tab hanging under the box.
float buffRowShift(GameplayScreenRuntime &context, int width, int height, const GameplayResolvedHudLayoutElement &frame,
    const SoloUnitFrameLayout &layout)
{
    const std::optional<std::array<float, 4>> tab = GameplayMapProgressBar::tabBounds(context, width, height);
    if (!tab || frame.scale <= 0)
    {
        return 0;
    }
    return std::max(0.0f, ((*tab)[3] - frame.y) / frame.scale + 3.0f - layout.buffY);
}

void renderUnitFrame(GameplayScreenRuntime &context, const Party &party, size_t memberIndex,
    const Character &member, const GameplayResolvedHudLayoutElement &frame, float buffShift)
{
    const SoloPainter painter(context, frame);
    const SoloUnitFrameLayout layout = soloUnitFrameLayout();
    const float scale = frame.scale;

    // The box: the native Obsidian frame pieces at half the menu border.
    const GameplayObsidianRect box = painter.at(layout.box);
    GameplayUiSkin::renderPanel(context, resolved(box, scale), false, 0.5f);
    painter.fill(painter.rect(layout.name.x, layout.name.y + layout.name.height, layout.name.width, 0.6f), BoxRule);

    const std::string name = painter.fitted("Fondamento", 10.5f, member.name, layout.name.width * 0.62f);
    painter.text("Fondamento", 10.5f, NameGold, name, layout.name.x + 1, layout.name.y + 0.4f);
    painter.text("Lucida", 6.4f, Muted, Engine::localize(displayClassName(member.className), "class"),
        layout.name.x + layout.name.width - 1, layout.name.y + 3.6f, 2);

    const int maximumHealth = GameMechanics::calculateEffectiveCharacterMaxHealth(member);
    const int maximumMana = GameMechanics::calculateEffectiveCharacterMaxSpellPoints(member);
    const float health = std::clamp(float(member.health) / float(std::max(1, maximumHealth)), 0.0f, 1.0f);
    const float mana = std::clamp(float(member.spellPoints) / float(std::max(1, maximumMana)), 0.0f, 1.0f);
    // The damage trail the party's HP arc shows: where the bar stood before the latest loss, fading over 96 ticks.
    GameplayPortraitMeterState &meter =
        context.gameplayUiRuntime().portraitPresentationState().meters[std::min<size_t>(memberIndex, 7)];
    const uint32_t now = context.animationTicks();
    if (meter.health >= 0 && health < meter.health)
    {
        meter.damageFrom = meter.health;
        meter.damagedTicks = now;
    }
    meter.health = health;
    const float trail = health + std::max(0.0f, meter.damageFrom - health)
        * std::max(0.0f, 1.0f - float(now - meter.damagedTicks) / 96.0f);
    const float reservedHealth = std::clamp(float(party.rules().spells.reservedHitPoints(party, memberIndex))
        / float(std::max(1, maximumHealth)), 0.0f, 1.0f);
    renderMeter(context, painter, layout.health, health, trail, reservedHealth, true,
        std::to_string(member.health) + " / " + std::to_string(maximumHealth));
    if (member.personalShieldCapacity > 0)
    {
        const float shield = std::clamp(member.personalShield / float(member.personalShieldCapacity), 0.0f, 1.0f);
        painter.fill(painter.rect(layout.health.x, layout.health.y - 1.4f, layout.health.width * shield, 1.0f),
            ShieldLine);
    }
    if (maximumMana > 0)
    {
        const float reservedMana = std::clamp(float(party.rules().spells.reservedSpellPoints(party, memberIndex))
            / float(maximumMana), 0.0f, 1.0f);
        renderMeter(context, painter, layout.mana, mana, 0, reservedMana, false,
            std::to_string(member.spellPoints) + " / " + std::to_string(maximumMana));
    }

    // The medallion: a dark oval, the whole head, one brass ring.
    const GameplayObsidianRect medallion = painter.at(layout.medallion);
    painter.oval(Backing, medallion);
    if (const std::optional<GameplayHudTextureHandle> portrait =
            context.gameplayUiRuntime().ensureHudTextureLoaded(context.resolvePortraitTextureName(member)))
    {
        bgfx::TextureHandle texture = portrait->textureHandle;
        if (party.hasCharacterBuff(memberIndex, CharacterBuffId::Mistform)
            || party.hasPartyBuff(PartyBuffId::Invisibility))
        {
            texture = context.gameplayUiRuntime().ensureHudTextureColorModulated(*portrait, 0x80ffffffu);
        }
        if (!GameMechanics::canAct(member))
        {
            texture = context.gameplayUiRuntime().ensureHudTextureColorModulated(*portrait, 0xff888888u);
        }
        const GameplayObsidianRect face = painter.at(layout.face);
        context.gameplayUiRuntime().submitHudTexturedEllipse(texture, face.x, face.y, face.width, face.height);
        context.renderPortraitFx(memberIndex, face.x, face.y, face.width, face.height);
    }
    ring(context, medallion, scale, 2.2f);

    // The level on a brass coin at the medallion's foot.
    const GameplayObsidianRect coin = painter.at(layout.coin);
    painter.oval(abgr(0x0d1213), coin);
    ring(context, coin, scale, 1.6f);
    painter.text("Arrus", 8.5f, NameGold, std::to_string(member.level),
        layout.coin.x + layout.coin.width / 2, layout.coin.y + layout.coin.height * 0.26f, 1);

    // The weapon in hand in a small socket at its shoulder.
    const GameplayObsidianRect socket = painter.at(layout.weapon);
    painter.oval(abgr(0x0d1213), socket);
    if (const ItemTable *pItemTable = context.itemTable(); pItemTable != nullptr && member.equipment.mainHand != 0)
    {
        if (const ItemDefinition *pWeapon = pItemTable->get(member.equipment.mainHand))
        {
            if (const std::optional<GameplayHudTextureHandle> icon =
                    context.gameplayUiRuntime().ensureItemIconTextureLoaded(pWeapon->iconName);
                icon && icon->width > 0 && icon->height > 0)
            {
                const float side = socket.width * 0.72f;
                const float fit = std::min(side / icon->width, side / icon->height);
                context.gameplayUiRuntime().submitHudTexturedQuad(icon->textureHandle,
                    socket.x + (socket.width - icon->width * fit) / 2, socket.y + (socket.height - icon->height * fit) / 2,
                    icon->width * fit, icon->height * fit);
            }
        }
    }
    ring(context, socket, scale, 1.2f);

    // The buff and debuff rows under the box.
    const auto [buffs, debuffs] = buffTiles(party, memberIndex, member);
    float x = layout.buffX;
    for (const BuffTile &tile : buffs)
    {
        renderTile(context, painter, tile, x, layout.buffY + buffShift, layout.tile);
        x += layout.tile + layout.tileGap;
    }
    x = layout.buffX;
    for (const BuffTile &tile : debuffs)
    {
        renderTile(context, painter, tile, x, layout.debuffY + buffShift, layout.tile);
        x += layout.tile + layout.tileGap;
    }
    forgetUnshown(context, buffs);
}

std::optional<SoloActionBarGrid> barGrid(GameplayScreenRuntime &context)
{
    const GameplayScreenRuntime::HudLayoutElement *pBar = context.findHudLayoutElement("SoloActionBar");
    const GameplayScreenRuntime::HudLayoutElement *pSlot = context.findHudLayoutElement("SoloActionSlot");
    const GameplayScreenRuntime::HudLayoutElement *pRight = context.findHudLayoutElement("SoloActionSlotRight");
    const GameplayScreenRuntime::HudLayoutElement *pBelow = context.findHudLayoutElement("SoloActionSlotBelow");
    if (pBar == nullptr || pSlot == nullptr || pRight == nullptr || pBelow == nullptr)
    {
        return std::nullopt;
    }
    // A child's offsets from its parent are its gapX and gapY (UiLayoutManager).
    return soloActionBarGrid(pBar->width, pBar->height, pSlot->width, pRight->gapX - pSlot->gapX - pSlot->width,
        pBelow->gapY - pSlot->gapY - pSlot->height, pSlot->gapX, pSlot->gapY);
}

// The bar's panel on screen and its grid. A screen too short for the column gives it less height (the resolver):
// everything in it then shrinks by the same factor, so the panel's width and scale shrink with it.
struct ResolvedBar
{
    GameplayResolvedHudLayoutElement panel;
    SoloActionBarGrid grid;
    float layoutWidth = 0;
};

std::optional<ResolvedBar> resolveBar(GameplayScreenRuntime &context, int width, int height)
{
    std::optional<GameplayResolvedHudLayoutElement> bar =
        context.resolveHudLayoutElement("SoloActionBar", width, height, 0, 0);
    const GameplayScreenRuntime::HudLayoutElement *pBarLayout = context.findHudLayoutElement("SoloActionBar");
    const std::optional<SoloActionBarGrid> grid = barGrid(context);
    if (!bar || !grid || pBarLayout == nullptr || bar->scale <= 0)
    {
        return std::nullopt;
    }
    const float fit = std::min(1.0f, bar->height / (pBarLayout->height * bar->scale));
    bar->width *= fit;
    bar->scale *= fit;
    return ResolvedBar{*bar, *grid, pBarLayout->width};
}

void drawItemIcon(GameplayScreenRuntime &context, const std::string &iconName, const GameplayObsidianRect &icon)
{
    if (const std::optional<GameplayHudTextureHandle> texture =
            context.gameplayUiRuntime().ensureItemIconTextureLoaded(iconName);
        texture && texture->width > 0 && texture->height > 0)
    {
        const float fit = std::min(icon.width / texture->width, icon.height / texture->height);
        context.gameplayUiRuntime().submitHudTexturedQuad(texture->textureHandle,
            icon.x + (icon.width - texture->width * fit) / 2, icon.y + (icon.height - texture->height * fit) / 2,
            texture->width * fit, texture->height * fit);
    }
}

// MAW caps a spell's cost at 65000: thousands print as "65k" so the tab stays inside the slot.
std::string compactCost(uint32_t cost)
{
    return cost >= 10000 ? std::to_string(cost / 1000) + "k" : std::to_string(cost);
}

void renderTalentIcon(GameplayScreenRuntime &context, const GameplayObsidianPainter &painter,
    const TalentDefinition &talent, const GameplayObsidianRect &icon)
{
    if (talent.iconSpell != 0)
    {
        painter.spellIcon(talent.iconSpell, icon, false);
        return;
    }
    drawItemIcon(context, talent.iconItem, icon);
}

// The self combat text (WoW's scrolling text about the player): what befell the member, taken from the party's queue
// where the HUD draws, as lines below and right of the crosshair; newest at the bottom, older ones rise and fade.
std::string selfTextLine(const Party::SelfTextEvent &event)
{
    switch (event.kind)
    {
        case Party::SelfTextEvent::Kind::Damage:
            return event.blocked > 0
                ? Engine::tr("-{damage} ({blocked} blocked)", {{"damage", int64_t(event.amount)},
                    {"blocked", int64_t(event.blocked)}})
                : "-" + std::to_string(event.amount);
        case Party::SelfTextEvent::Kind::Heal:
            return "+" + std::to_string(event.amount);
        case Party::SelfTextEvent::Kind::ConditionGained:
            return Engine::localizeKnown(GameMechanics::conditionName(event.condition));
        case Party::SelfTextEvent::Kind::ConditionCleared:
            return Engine::tr("{condition} fades",
                {{"condition", Engine::localizeKnown(GameMechanics::conditionName(event.condition))}});
    }
    return {};
}

uint32_t selfTextColour(Party::SelfTextEvent::Kind kind)
{
    switch (kind)
    {
        case Party::SelfTextEvent::Kind::Damage: return abgr(0xff7a66);
        case Party::SelfTextEvent::Kind::Heal: return abgr(0x8fe07a);
        case Party::SelfTextEvent::Kind::ConditionGained: return abgr(0xf0c45a);
        case Party::SelfTextEvent::Kind::ConditionCleared: return abgr(0xb8b49c);
    }
    return Ivory;
}

void renderSelfText(GameplayScreenRuntime &context, int width, int height)
{
    constexpr size_t MaximumLines = 8;
    constexpr uint64_t HoldMilliseconds = 1400;
    constexpr uint64_t FadeMilliseconds = 800;
    std::vector<GameplayOverlayInteractionState::SoloSelfTextLine> &lines = context.interactionState().soloSelfText;
    const uint64_t now = SDL_GetTicks();
    if (Party *pParty = context.party())
    {
        const size_t activeMember = pParty->activeMemberIndex();
        const Character *pMember = pParty->activeMember();
        // Below 1 % of maximum HP a tick (MAW's regeneration and auras, a leech) would only flicker: left out.
        const int floor = pMember != nullptr
            ? GameMechanics::calculateEffectiveCharacterMaxHealth(*pMember) / 100 : 0;
        for (const Party::SelfTextEvent &event : pParty->takeSelfTextEvents())
        {
            const bool amount = event.kind == Party::SelfTextEvent::Kind::Damage
                || event.kind == Party::SelfTextEvent::Kind::Heal;
            if (event.memberIndex == activeMember && (!amount || event.amount + event.blocked > floor))
            {
                lines.push_back({selfTextLine(event), selfTextColour(event.kind), now});
            }
        }
    }
    std::erase_if(lines, [now](const GameplayOverlayInteractionState::SoloSelfTextLine &line)
        { return now - line.startTicks > HoldMilliseconds + FadeMilliseconds; });
    if (lines.size() > MaximumLines)
    {
        lines.erase(lines.begin(), lines.end() - MaximumLines);
    }
    const std::optional<GameplayHudFontHandle> font = context.findHudFont("alegreya_semibold");
    if (lines.empty() || !font || font->fontHeight <= 0
        || context.currentHudScreenState() != GameplayHudScreenState::Gameplay)
    {
        return;
    }
    // At 1600 x 900: 19 px lines, the column centred 70 px right of the crosshair, its newest line 170 px below it.
    const float k = float(height) / 900.0f;
    const float lineHeight = 22.0f * k;
    const float fontScale = 19.0f * k / float(font->fontHeight);
    const float centerX = float(width) * 0.5f + 70.0f * k;
    const float newestY = float(height) * 0.5f + 170.0f * k;
    const float outline = std::max(1.0f, 1.2f * k);
    constexpr std::array<std::array<float, 2>, 4> Outline = {{{-1, 0}, {1, 0}, {0, -1}, {0, 1}}};
    for (size_t index = 0; index < lines.size(); ++index)
    {
        const GameplayOverlayInteractionState::SoloSelfTextLine &line = lines[index];
        const uint64_t age = now - line.startTicks;
        const float alpha = age <= HoldMilliseconds ? 1.0f
            : std::max(0.0f, 1.0f - float(age - HoldMilliseconds) / float(FadeMilliseconds));
        const uint32_t alphaBits = uint32_t(std::lround(255.0f * alpha)) << 24;
        const float textX = centerX - context.measureHudTextWidth(*font, line.text) * fontScale * 0.5f;
        const float textY = newestY - float(lines.size() - 1 - index) * lineHeight;
        const GameplayHudFontLayer shadow(font->shadowTextureHandle, 0x00ffffffu | alphaBits);
        for (const std::array<float, 2> &direction : Outline)
        {
            context.renderHudFontLayer(*font, shadow, line.text, textX + direction[0] * outline,
                textY + direction[1] * outline, fontScale);
        }
        context.renderHudFontLayer(*font, context.hudFontMainLayer(*font, (line.colorAbgr & 0x00ffffffu) | alphaBits),
            line.text, textX, textY, fontScale);
    }
}

void renderSlot(GameplayScreenRuntime &context, const SoloPainter &painter, const Party &party,
    const Character &member, const ActionBarSlot &slot, const SoloHudRect &area, std::optional<size_t> key,
    float recoveryProgress)
{
    const GameplayObsidianRect box = painter.at(area);
    if (slot.kind == ActionBarSlotKind::Empty)
    {
        painter.fill(box, EmptyFill);
        painter.frame(box, EmptyEdge);
    }
    else
    {
        painter.fill(box, SlotFill);
        const float inset = 1.6f;
        const GameplayObsidianRect icon = painter.rect(area.x + inset, area.y + inset, area.width - 2 * inset,
            area.height - 2 * inset);
        bool noMana = false;
        std::optional<uint32_t> cost;
        std::optional<size_t> count;
        // A talent's cooldown: the share still to run (0: ready) and its seconds.
        float cooldownShare = 0.0f;
        float cooldownLeft = 0.0f;
        bool talentEffectOn = false;
        if (slot.kind == ActionBarSlotKind::Spell && context.spellTable() != nullptr)
        {
            cost = PartySpellSystem::manaCost(party, member, *context.spellTable(), slot.id);
            noMana = cost && int(*cost) > member.spellPoints;
            painter.spellIcon(slot.id, icon, noMana);
        }
        else if (slot.kind == ActionBarSlotKind::Talent && slot.id < soloTalentTable().talents().size())
        {
            const TalentDefinition &talent = soloTalentTable().talents()[slot.id];
            renderTalentIcon(context, painter, talent, icon);
            const auto found = member.talentState.cooldownSeconds.find(talent.id);
            cooldownLeft = found != member.talentState.cooldownSeconds.end() ? found->second : 0.0f;
            const float total = talentCooldownSeconds(talent, std::max(1, talentRank(member, talent.id)));
            cooldownShare = cooldownLeft > 0.0f ? std::clamp(cooldownLeft / total, 0.0f, 1.0f) : 0.0f;
            const SoloTalentState &state = member.talentState;
            talentEffectOn = (talent.id == "frenzy" && state.frenzySeconds > 0.0f)
                || (talent.id == "shield_wall" && state.shieldWallSeconds > 0.0f)
                || (talent.id == "spell_surge" && state.spellSurgeArmed);
        }
        else if ((slot.kind == ActionBarSlotKind::Item || slot.kind == ActionBarSlotKind::Weapon)
            && context.itemTable() != nullptr)
        {
            // The swap slot shows what it swaps to: the bow while the melee weapon is drawn, and back.
            const bool swapSlot = slot.kind == ActionBarSlotKind::Weapon && slot.id == ActionBarWeaponSwapId;
            const uint32_t itemId = slot.kind == ActionBarSlotKind::Item ? slot.item.itemId
                : swapSlot && !context.viewModelLink().bowSelected ? member.equipment.bow
                : member.equipment.mainHand;
            const ItemDefinition *pItem = itemId != 0 ? context.itemTable()->get(itemId) : nullptr;
            if (pItem != nullptr)
            {
                drawItemIcon(context, pItem->iconName, icon);
            }
            if (slot.kind == ActionBarSlotKind::Item)
            {
                count = QuickItemSlots::countPartyItems(party, slot.item,
                    std::max(1, party.rules().items.bagCount(party)));
            }
        }
        if (noMana)
        {
            painter.fill(icon, NoManaVeil);
        }
        // The member's recovery: the slots that need a ready member darken from the top until it runs out.
        if (recoveryProgress < 1)
        {
            painter.fill({icon.x, icon.y, icon.width, icon.height * (1 - recoveryProgress)}, RecoveryShade);
        }
        if (cooldownShare > 0.0f)
        {
            painter.fill({icon.x, icon.y, icon.width, icon.height * cooldownShare}, CooldownShade);
            const std::string seconds = std::to_string(int(std::ceil(cooldownLeft)));
            painter.text("SMALLNUM", 7.0f, Ivory, seconds, area.x + area.width / 2,
                area.y + area.height / 2 - 3.5f, 1);
        }
        if (cost)
        {
            const std::string costText = compactCost(*cost);
            painter.fill(painter.rect(area.x + 0.8f, area.y + 0.8f, painter.width("SMALLNUM", 5.2f, costText) + 1.6f,
                6.2f), abgr(0x08101c, 0xcc));
            painter.text("SMALLNUM", 5.2f, noMana ? abgr(0xff8a78) : ManaText, costText, area.x + 1.6f,
                area.y + 1.2f);
        }
        if (count)
        {
            painter.text("SMALLNUM", 6.0f, *count == 0 ? abgr(0xff8a78) : Ivory, std::to_string(*count),
                area.x + area.width - 1.4f, area.y + area.height - 7.4f, 2);
        }
        painter.frame(box, talentEffectOn ? TalentGold : Brass);
    }
    if (key)
    {
        painter.text("SMALLNUM", 6.0f, Ivory, BarKeyNames[*key], area.x + area.width - 1.4f, area.y + 1.0f, 2);
    }
}
}

void GameplaySoloHud::renderHud(GameplayScreenRuntime &context, int width, int height)
{
    const Party *pParty = context.partyReadOnly();
    const Character *pMember = pParty != nullptr ? pParty->activeMember() : nullptr;
    if (pMember == nullptr || !context.soloHud())
    {
        return;
    }
    const size_t memberIndex = pParty->activeMemberIndex();
    if (const std::optional<GameplayResolvedHudLayoutElement> frame =
            context.resolveHudLayoutElement("SoloUnitFrame", width, height, 0, 0))
    {
        renderUnitFrame(context, *pParty, memberIndex, *pMember, *frame,
            buffRowShift(context, width, height, *frame, soloUnitFrameLayout()));
    }
    // The action bar: a column of keys 1-0 down the left edge (the SoloActionBar element), in the native frame pieces
    // as the unit frame's box.
    const std::optional<ResolvedBar> resolvedBar = resolveBar(context, width, height);
    if (!resolvedBar)
    {
        return;
    }
    const GameplayResolvedHudLayoutElement *bar = &resolvedBar->panel;
    const SoloActionBarGrid *grid = &resolvedBar->grid;
    const SoloPainter painter(context, *bar);
    if (context.settingsSnapshot().partyFrame || context.currentHudScreenState() != GameplayHudScreenState::Gameplay)
    {
        GameplayUiSkin::renderPanel(context, *bar, false, 0.5f);
    }
    else
    {
        // With the frame setting off the slots stand on a soft shadow, as the party's portraits keep a backing.
        painter.fill(painter.rect(0, 0, resolvedBar->layoutWidth, bar->height / bar->scale), abgr(0x000000, 0x60));
    }
    // A thin brass rule between keys 5 and 6 splits the column into two blocks of five.
    if (grid->columns == 1 && grid->rows == 10)
    {
        const float ruleY = grid->padY + 5 * (grid->slot + grid->gapY) - grid->gapY / 2 - 0.3f;
        painter.fill(painter.rect(grid->padX + 2, ruleY, grid->slot - 4, 0.6f), abgr(0xa8925f, 0xb0));
    }
    const float progress = soloRecoveryProgress(pMember->recoverySecondsRemaining, pMember->recoveryTotalSeconds);
    for (size_t row = 0; row < grid->rows; ++row)
    {
        for (size_t column = 0; column < grid->columns; ++column)
        {
            const size_t slot = soloActionBarSlotAt(*grid, row, column);
            renderSlot(context, painter, *pParty, *pMember, pMember->actionBar[slot],
                soloActionSlotRect(*grid, row, column), soloActionBarKeyOfSlot(slot), progress);
        }
    }
    renderSelfText(context, width, height);
}

void GameplaySoloHud::renderCrosshairBrackets(GameplayScreenRuntime &context, float centerX, float centerY,
    float scale)
{
    const Party *pParty = context.partyReadOnly();
    const Character *pMember = pParty != nullptr ? pParty->activeMember() : nullptr;
    if (pMember == nullptr || !context.soloHud())
    {
        return;
    }
    // Faint when ready; the bright part fills as the recovery runs out (left from the bottom, right from the top).
    const float radius = 15.0f * scale;
    const GameplayResolvedHudLayoutElement circle = {centerX - radius, centerY - radius, 2 * radius, 2 * radius,
        scale};
    const float progress = soloRecoveryProgress(pMember->recoverySecondsRemaining, pMember->recoveryTotalSeconds);
    for (const float start : {140.0f, -40.0f})
    {
        GameplayUiSkin::renderArc(context, circle, 1.4f, start, 80, GameplayUiSkin::ArcMaterial::Track);
        if (progress < 1)
        {
            GameplayUiSkin::renderArc(context, circle, 1.1f, start, 80, GameplayUiSkin::ArcMaterial::SelectedRim, 0,
                progress);
        }
    }
}

std::optional<GameplayHudPointerTarget> GameplaySoloHud::buffTargetAt(GameplayScreenRuntime &context, int width,
    int height, float x, float y)
{
    const Party *pParty = context.partyReadOnly();
    const Character *pMember = pParty != nullptr ? pParty->activeMember() : nullptr;
    const std::optional<GameplayResolvedHudLayoutElement> frame = pMember != nullptr && context.soloHud()
        ? context.resolveHudLayoutElement("SoloUnitFrame", width, height, 0, 0)
        : std::nullopt;
    if (!frame || frame->scale <= 0)
    {
        return std::nullopt;
    }
    const SoloUnitFrameLayout layout = soloUnitFrameLayout();
    const float unitX = (x - frame->x) / frame->scale;
    const float unitY = (y - frame->y) / frame->scale;
    const auto [buffs, debuffs] = buffTiles(*pParty, pParty->activeMemberIndex(), *pMember);
    const float buffY = layout.buffY + buffRowShift(context, width, height, *frame, layout);
    for (size_t index = 0; index < buffs.size(); ++index)
    {
        const SoloHudRect tile = {layout.buffX + float(index) * (layout.tile + layout.tileGap), buffY,
            layout.tile, layout.tile};
        if (tile.contains(unitX, unitY))
        {
            return buffs[index].target;
        }
    }
    return std::nullopt;
}

std::optional<size_t> GameplaySoloHud::heldBarSlot(const GameplayInputFrame &input)
{
    // Shift is kept for a second row; Ctrl and a key opens the slot selector (GameplaySoloBarSelector).
    if (input.isScancodeHeld(SDL_SCANCODE_LSHIFT) || input.isScancodeHeld(SDL_SCANCODE_RSHIFT)
        || input.isScancodeHeld(SDL_SCANCODE_LCTRL) || input.isScancodeHeld(SDL_SCANCODE_RCTRL))
    {
        return std::nullopt;
    }
    for (size_t slot = 0; slot < BarKeys.size(); ++slot)
    {
        if (input.isScancodeHeld(BarKeys[slot]))
        {
            return slot;
        }
    }
    return std::nullopt;
}

bool GameplaySoloHud::barSlotPressed(const GameplayInputFrame &input, size_t slot)
{
    return slot < BarKeys.size() && input.scancodePressCount(BarKeys[slot]) > 0;
}

std::string GameplaySoloHud::barKeyName(size_t slot)
{
    return slot < BarKeyNames.size() ? BarKeyNames[slot] : std::string();
}

std::optional<GameplayResolvedHudLayoutElement> GameplaySoloHud::barPanelRect(GameplayScreenRuntime &context,
    int width, int height)
{
    const std::optional<ResolvedBar> bar = context.soloHud() ? resolveBar(context, width, height) : std::nullopt;
    return bar ? std::optional<GameplayResolvedHudLayoutElement>(bar->panel) : std::nullopt;
}

std::optional<SoloHudRect> GameplaySoloHud::barSlotRect(GameplayScreenRuntime &context, int width, int height,
    size_t slot)
{
    const std::optional<ResolvedBar> bar = context.soloHud() ? resolveBar(context, width, height) : std::nullopt;
    for (size_t row = 0; bar && row < bar->grid.rows; ++row)
    {
        for (size_t column = 0; column < bar->grid.columns; ++column)
        {
            if (soloActionBarSlotAt(bar->grid, row, column) == slot)
            {
                const SoloHudRect unit = soloActionSlotRect(bar->grid, row, column);
                const float scale = bar->panel.scale;
                return SoloHudRect{bar->panel.x + unit.x * scale, bar->panel.y + unit.y * scale, unit.width * scale,
                    unit.height * scale};
            }
        }
    }
    return std::nullopt;
}

std::optional<size_t> GameplaySoloHud::barSlotAt(GameplayScreenRuntime &context, int width, int height, float x,
    float y)
{
    const std::optional<GameplayResolvedHudLayoutElement> panel = barPanelRect(context, width, height);
    if (!panel || x < panel->x || y < panel->y || x >= panel->x + panel->width || y >= panel->y + panel->height)
    {
        return std::nullopt;
    }
    for (size_t slot = 0; slot < ActionBarSlotCount / 2; ++slot)
    {
        if (const std::optional<SoloHudRect> rect = barSlotRect(context, width, height, slot);
            rect && rect->contains(x, y))
        {
            return slot;
        }
    }
    return std::nullopt;
}

void GameplaySoloHud::renderSlotIcon(GameplayScreenRuntime &context, const GameplayObsidianPainter &painter,
    const Character &member, const ActionBarSlot &slot, const GameplayObsidianRect &icon, bool dim)
{
    if (slot.kind == ActionBarSlotKind::Spell)
    {
        painter.spellIcon(slot.id, icon, dim);
    }
    else if (slot.kind == ActionBarSlotKind::Talent && slot.id < soloTalentTable().talents().size())
    {
        renderTalentIcon(context, painter, soloTalentTable().talents()[slot.id], icon);
    }
    else if ((slot.kind == ActionBarSlotKind::Item || slot.kind == ActionBarSlotKind::Weapon)
        && context.itemTable() != nullptr)
    {
        const uint32_t itemId = slot.kind == ActionBarSlotKind::Item ? slot.item.itemId
            : slot.id == ActionBarWeaponSwapId ? member.equipment.bow
            : member.equipment.mainHand;
        if (const ItemDefinition *pItem = itemId != 0 ? context.itemTable()->get(itemId) : nullptr)
        {
            drawItemIcon(context, pItem->iconName, icon);
        }
    }
    if (dim && slot.kind != ActionBarSlotKind::Spell)
    {
        painter.fill(icon, abgr(0x000000, 0x90));
    }
}
}
