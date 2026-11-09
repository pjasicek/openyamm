#pragma once

#include "game/render/TextureFiltering.h"
#include "game/ui/GameplayOverlayTypes.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
class CombatLog;
struct CombatLogEntry;
class GameplayScreenRuntime;

// Which hits the docked log lists.
enum class CombatLogFilter : uint8_t
{
    All,
    Dealt,
    Taken,
};

// The docked combat log (devdocs/maw/GAPS.md H.3, level_generation/ui/maw_combat_log_20261024/, layout A): a titled
// panel above the party frame with All / Dealt / Taken filters, the last hits newest at the bottom as compact rows
// ("Gerrard <bow> Goblin   58!": names shortened to fit, the amount right-aligned, each part in its colour), a
// scrollbar, and a clicked hit's whole sentence and damage steps under it. The text is laid out into glyph quads once and kept; a frame resubmits them and lays them out again only when the
// log gains a hit, the view scrolls, filters or opens a hit, or the panel moves or rescales. Closed, or with the
// combat_log setting off, it draws and costs nothing.
class GameplayCombatLogPanel
{
public:
    bool open() const;
    void toggle();
    // Mouse wheel over the panel: older hits up, newer down.
    void scroll(int lines, const CombatLog &log);
    // A click on a hit opens its damage steps; a second click closes them.
    void toggleEntry(uint32_t entryId);
    void setFilter(CombatLogFilter filter);

    void render(GameplayScreenRuntime &context, int width, int height);

    // Where the panel, its hits and its filter chips were last drawn, for the pointer.
    bool contains(float x, float y) const;
    std::optional<uint32_t> entryAt(float x, float y) const;
    std::optional<CombatLogFilter> filterAt(float x, float y) const;

private:
    struct CacheKey
    {
        uint64_t revision = 0;
        size_t scroll = 0;
        uint32_t openEntry = 0;
        CombatLogFilter filter = CombatLogFilter::All;
        float x = 0;
        float y = 0;
        float width = 0;
        float height = 0;
        float scale = 0;

        bool operator==(const CacheKey &) const = default;
    };

    bool shows(const CombatLogEntry &entry) const;
    void layOut(GameplayScreenRuntime &context, const CombatLog &log);
    // A line glyph (combat_log_*), tinted, into m_glyphQuads.
    void appendGlyph(GameplayScreenRuntime &context, const char *pName, float x, float y, float size, uint32_t tint);

    bool m_open = false;
    size_t m_scroll = 0;
    uint32_t m_openEntry = 0;
    CombatLogFilter m_filter = CombatLogFilter::All;
    bool m_drawn = false;
    // Where the panel was placed (the cache key) and where it is drawn: trimmed at the top to whole lines.
    GameplayResolvedHudLayoutElement m_placedPanel;
    GameplayResolvedHudLayoutElement m_panel;
    std::optional<CacheKey> m_cacheKey;
    // Laid out once per change and drawn in two batches: the fills (panel, open hit, rule, chips, scrollbar) in palette
    // colours, then the text, its shadows first and its glyphs grouped by colour so each batch is a few draws.
    struct Fill
    {
        GameplayResolvedHudLayoutElement rect;
        uint32_t colorAbgr = 0;
    };
    std::vector<Fill> m_fills;
    std::vector<GameplayHudBatchQuad> m_fillQuads;
    std::vector<GameplayHudBatchQuad> m_textQuads;
    // The line glyphs (sword, bow, skull), drawn after the text.
    std::vector<GameplayHudBatchQuad> m_glyphQuads;
    TextureFilterProfile m_textFilter = TextureFilterProfile::Text;
    std::vector<std::pair<GameplayResolvedHudLayoutElement, uint32_t>> m_entryRects;
    std::vector<std::pair<GameplayResolvedHudLayoutElement, CombatLogFilter>> m_filterRects;
};
}
