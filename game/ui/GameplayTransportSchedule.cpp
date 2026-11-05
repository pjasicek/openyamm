#include "game/ui/GameplayTransportSchedule.h"

#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/party/Party.h"
#include "game/tables/HouseTable.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayUiController.h"
#include "game/ui/GameplayUiRuntime.h"
#include "game/ui/GameplayUiSkin.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t abgr(uint32_t rgb, uint32_t alpha = 0xff)
{
    return (alpha << 24) | ((rgb & 0xff) << 16) | (rgb & 0xff00) | ((rgb >> 16) & 0xff);
}

// The Carved Obsidian reading colours: soft ivory text, gold accents, semantic green and red.
constexpr uint32_t Veil = abgr(0x000000, 0x88);
constexpr uint32_t Rule = abgr(0x8c815f, 0x70);
constexpr uint32_t RowRule = abgr(0xffffff, 0x10);
constexpr uint32_t Ivory = abgr(0xefe0bc);
constexpr uint32_t Bright = abgr(0xfff4d8);
constexpr uint32_t Label = abgr(0xe8d1a4);
constexpr uint32_t Muted = abgr(0xa9a690);
constexpr uint32_t Faint = abgr(0x77725f);
constexpr uint32_t Gold = abgr(0xe3c185);
constexpr uint32_t Good = abgr(0x8fe08a);
constexpr uint32_t Bad = abgr(0xff6a5a);
constexpr uint32_t Disabled = abgr(0x968b7e);
constexpr uint32_t TodayFill = abgr(0x3a3221, 0xb0);
constexpr uint32_t SelectedFill = abgr(0x5c4a27, 0xd8);
constexpr uint32_t HoverFill = abgr(0xe3c185, 0x26);
constexpr uint32_t HoverBorder = abgr(0xe3c185, 0x70);
constexpr uint32_t TodayHoverFill = abgr(0x4a3f27, 0xd0);

constexpr char TitleFont[] = "Fondamento";
constexpr char TextFont[] = "alegreya_semibold";

constexpr std::array<const char *, 7> DayNames = {
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"};

// The popup's sizes in the dialogue's 640x480 units. The panel fills the house's scene; the text sizes land on the
// faces' raster heights (Fondamento 32, Alegreya 24 pixels) at 1600x900, so the main text draws pixel for pixel.
constexpr float AreaInset = 3.0f;
constexpr float BorderScale = 0.75f;
constexpr float Padding = 22.0f;
constexpr float HeaderTop = 12.0f;
constexpr float SubtitleGap = 7.0f;
constexpr float HeaderHeight = 62.0f;
constexpr float FooterHeight = 70.0f;
constexpr float MaxRowHeight = 36.0f;
constexpr float DayColumn = 128.0f;
constexpr float TitleSize = 21.5f;
constexpr float DaySize = 17.0f;
// The weekday names, a little under the raster height (below the unscaled band).
constexpr float RowDaySize = 14.5f;
constexpr float NameSize = 12.8f;
constexpr float SmallSize = 10.5f;
constexpr float FactSize = 12.0f;
constexpr float ButtonLabelSize = 13.5f;
// The carved buttons keep their art's proportions: the wide rest button and the close button.
constexpr float TravelButtonWidth = 168.0f;
constexpr float TravelButtonAspect = 544.0f / 84.0f;
constexpr float CloseButtonWidth = 76.0f;
constexpr float CloseButtonAspect = 207.0f / 51.0f;

// Click targets: the close button, the travel button, a day's row and one of its destinations.
constexpr int TargetNone = -1;
constexpr int TargetClose = 0;
constexpr int TargetTravel = 1;
constexpr int TargetOutside = 2;
constexpr int TargetRowBase = 100;
constexpr int TargetDestinationBase = 1000;

struct Box
{
    float x = 0;
    float y = 0;
    float width = 0;
    float height = 0;

    bool contains(float pointX, float pointY) const
    {
        return pointX >= x && pointX < x + width && pointY >= y && pointY < y + height;
    }

    GameplayResolvedHudLayoutElement rect(float scale) const
    {
        return {x, y, width, height, scale};
    }
};

class Painter
{
public:
    explicit Painter(GameplayScreenRuntime &context)
        : m_context(context)
    {
    }

    void fill(const Box &box, uint32_t colour) const
    {
        char name[40] = {};
        std::snprintf(name, sizeof(name), "__transport_schedule_%08x", colour);

        if (const std::optional<GameplayHudTextureHandle> texture =
                m_context.gameplayUiRuntime().ensureSolidHudTextureLoaded(name, colour))
        {
            m_context.submitHudTexturedQuad(*texture, box.x, box.y, box.width, box.height);
        }
    }

    void frame(const Box &box, float line, uint32_t colour) const
    {
        fill({box.x, box.y, box.width, line}, colour);
        fill({box.x, box.y + box.height - line, box.width, line}, colour);
        fill({box.x, box.y, line, box.height}, colour);
        fill({box.x + box.width - line, box.y, line, box.height}, colour);
    }

    // Text of a pixel height; align 0 left, 1 centred on x, 2 ending at x.
    void text(const char *pFont, float height, uint32_t colour, const std::string &value, float x, float y,
        int align = 0) const
    {
        const float scale = fontScale(pFont, height);
        const float textWidth = m_context.measureHudTextWidth(pFont, value) * scale;
        x -= align == 1 ? textWidth / 2 : align == 2 ? textWidth : 0;
        m_context.renderHudTextLine(pFont, colour, value, std::round(x), std::round(y), scale);
    }

    float width(const char *pFont, float height, const std::string &value) const
    {
        return m_context.measureHudTextWidth(pFont, value) * fontScale(pFont, height);
    }

    // The value shortened with an ellipsis to fit the width.
    std::string fitted(const char *pFont, float height, const std::string &value, float maxWidth) const
    {
        if (width(pFont, height, value) <= maxWidth)
        {
            return value;
        }

        std::string result = value;

        while (result.size() > 1 && width(pFont, height, result + "...") > maxWidth)
        {
            result.pop_back();
        }

        return result + "...";
    }

    // The drawn height of text asked at a pixel height.
    float lineHeight(const char *pFont, float height) const
    {
        return float(m_context.hudFontHeight(pFont)) * fontScale(pFont, height);
    }

private:
    // A size near the face's raster height draws at it exactly, unscaled and sharp; others scale smoothly.
    float fontScale(const char *pFont, float height) const
    {
        const float wanted = height / float(std::max(1, m_context.hudFontHeight(pFont)));

        if (wanted >= 0.86f && wanted <= 1.14f)
        {
            return 1.0f;
        }

        return wanted >= 1.0f ? GameplayHudCommon::snappedHudFontScale(wanted) : std::max(0.5f, wanted);
    }

    GameplayScreenRuntime &m_context;
};

std::string daysText(int days)
{
    return std::to_string(days) + (days == 1 ? " day" : " days");
}

const HouseEntry *scheduleHouse(GameplayScreenRuntime &context)
{
    const GameplayUiController::TransportScheduleState &state = context.transportSchedule();
    const EventDialogContent &dialog = context.activeEventDialog();

    if (!state.active || !dialog.isActive || !dialog.isHouseDialog || dialog.sourceId != state.houseId
        || context.houseTable() == nullptr)
    {
        return nullptr;
    }

    return context.houseTable()->get(state.houseId);
}

TransportSchedule currentSchedule(GameplayScreenRuntime &context, const HouseEntry &house)
{
    return buildTransportSchedule(house, context.partyReadOnly(), context.worldRuntime());
}

// The routes leaving on a weekday, in route order.
std::vector<const TransportScheduleRoute *> departures(const TransportSchedule &schedule, int day)
{
    std::vector<const TransportScheduleRoute *> routes;

    for (const TransportScheduleRoute &route : schedule.routes)
    {
        if (route.daysAvailable[size_t(day)])
        {
            routes.push_back(&route);
        }
    }

    return routes;
}

const TransportScheduleRoute *selectedRoute(GameplayScreenRuntime &context, const TransportSchedule &schedule)
{
    const GameplayUiController::TransportScheduleState &state = context.transportSchedule();

    if (!state.selectedDay)
    {
        return nullptr;
    }

    for (const TransportScheduleRoute *pRoute : departures(schedule, *state.selectedDay))
    {
        if (pRoute->routeIndex == state.selectedRouteIndex)
        {
            return pRoute;
        }
    }

    return nullptr;
}

struct Layout
{
    Box panel;
    Box close;
    std::array<Box, 7> rows = {};
    Box footer;
    Box travel;
    float k = 1;
};

// The panel over the house's whole scene (the dialogue's video area), its seven rows sharing what the header and
// footer leave.
std::optional<Layout> layoutFor(GameplayScreenRuntime &context, int width, int height)
{
    const std::optional<GameplayResolvedHudLayoutElement> area =
        context.resolveHudLayoutElement("DialogueVideoArea", width, height, 0, 0);

    if (!area || area->scale <= 0)
    {
        return std::nullopt;
    }

    Layout layout;
    const float k = area->scale;
    layout.k = k;
    const float rowHeight =
        std::min(MaxRowHeight * k, (area->height - 2 * AreaInset * k - (HeaderHeight + FooterHeight + 8) * k) / 7);
    const float panelHeight = (HeaderHeight + FooterHeight + 8) * k + 7 * rowHeight;
    layout.panel = {area->x + AreaInset * k, area->y + std::max(AreaInset * k, (area->height - panelHeight) / 2),
        area->width - 2 * AreaInset * k, panelHeight};
    const Box &panel = layout.panel;
    const float closeHeight = CloseButtonWidth / CloseButtonAspect * k;
    // Close sits level with the title's line, right of it.
    const float titleHeight = Painter(context).lineHeight(TitleFont, TitleSize * k);
    layout.close = {panel.x + panel.width - (Padding + CloseButtonWidth) * k,
        panel.y + HeaderTop * k + (titleHeight - closeHeight) / 2, CloseButtonWidth * k, closeHeight};

    for (size_t day = 0; day < layout.rows.size(); ++day)
    {
        layout.rows[day] = {panel.x + (Padding - 8) * k, panel.y + (HeaderHeight + 4) * k + float(day) * rowHeight,
            panel.width - 2 * (Padding - 8) * k, rowHeight};
    }

    layout.footer = {panel.x, panel.y + panel.height - FooterHeight * k, panel.width, FooterHeight * k};
    const float travelHeight = TravelButtonWidth / TravelButtonAspect * k;
    // The button sits beside the destination's name, leaving the full width to the facts below them.
    layout.travel = {panel.x + panel.width - (Padding + TravelButtonWidth) * k, layout.footer.y + 6 * k,
        TravelButtonWidth * k, travelHeight};
    return layout;
}

// The boxes of a row's destination names, for picking one of several.
std::vector<Box> destinationBoxes(GameplayScreenRuntime &context, const Layout &layout, const Box &row,
    const std::vector<const TransportScheduleRoute *> &routes)
{
    Painter paint(context);
    const float k = layout.k;
    std::vector<Box> boxes;
    float x = row.x + DayColumn * k;

    for (const TransportScheduleRoute *pRoute : routes)
    {
        const float nameWidth = paint.width(TextFont, NameSize * k, pRoute->destinationName);
        const float daysWidth = paint.width(TextFont, SmallSize * k, daysText(pRoute->travelDays));
        const float boxWidth = nameWidth + 6 * k + daysWidth;
        boxes.push_back({x, row.y, boxWidth, row.height});
        x += boxWidth + 22 * k;
    }

    return boxes;
}

// Why the selected trip cannot be taken now, if it cannot.
std::string tripRefusal(const Party *pParty, const TransportSchedule &schedule, int waitFood)
{
    if (pParty == nullptr)
    {
        return "Travel is unavailable right now.";
    }

    if (pParty->gold() < schedule.fare)
    {
        return "You don't have enough gold.";
    }

    if (pParty->food() < waitFood)
    {
        return "Not enough food to wait: buy some at a tavern.";
    }

    return {};
}

std::string travelLabel(GameplayScreenRuntime &context, const TransportSchedule &schedule)
{
    const std::optional<int> day = context.transportSchedule().selectedDay;
    const int wait = day ? transportWaitDays(schedule.today, *day) : 0;
    return wait == 0 ? "Travel now" : "Wait " + daysText(wait) + " and travel";
}

int targetAt(GameplayScreenRuntime &context, const Layout &layout, const TransportSchedule &schedule, float x,
    float y)
{
    if (!layout.panel.contains(x, y))
    {
        return TargetOutside;
    }

    if (layout.close.contains(x, y))
    {
        return TargetClose;
    }

    if (selectedRoute(context, schedule) != nullptr && layout.travel.contains(x, y))
    {
        return TargetTravel;
    }

    for (int day = 0; day < 7; ++day)
    {
        const Box &row = layout.rows[size_t(day)];

        if (!row.contains(x, y))
        {
            continue;
        }

        const std::vector<const TransportScheduleRoute *> routes = departures(schedule, day);

        if (routes.empty())
        {
            return TargetNone;
        }

        if (routes.size() > 1)
        {
            const std::vector<Box> boxes = destinationBoxes(context, layout, row, routes);

            for (size_t index = 0; index < boxes.size(); ++index)
            {
                if (boxes[index].contains(x, y))
                {
                    return TargetDestinationBase + day * 16 + int(index);
                }
            }
        }

        return TargetRowBase + day;
    }

    return TargetNone;
}

// Selects a day's departure: the named one, else the next of several when the day is already selected, else the
// first.
void selectDay(GameplayScreenRuntime &context, const TransportSchedule &schedule, int day,
    std::optional<size_t> destination)
{
    GameplayUiController::TransportScheduleState &state = context.transportSchedule();
    const std::vector<const TransportScheduleRoute *> routes = departures(schedule, day);

    if (routes.empty())
    {
        return;
    }

    size_t index = 0;

    if (destination && *destination < routes.size())
    {
        index = *destination;
    }
    else if (state.selectedDay == day)
    {
        for (size_t current = 0; current < routes.size(); ++current)
        {
            if (routes[current]->routeIndex == state.selectedRouteIndex)
            {
                index = (current + 1) % routes.size();
            }
        }
    }

    state.selectedDay = day;
    state.selectedRouteIndex = routes[index]->routeIndex;
}

// Up and Down step through the days that have departures, from the selected day (or from before Monday, so Down
// starts at the first).
void stepDay(GameplayScreenRuntime &context, const TransportSchedule &schedule, int step)
{
    const std::optional<int> selected = context.transportSchedule().selectedDay;
    int day = selected ? *selected : (step > 0 ? -1 : 7);

    for (day += step; day >= 0 && day < 7; day += step)
    {
        if (!departures(schedule, day).empty())
        {
            selectDay(context, schedule, day, std::nullopt);
            return;
        }
    }
}

void travel(GameplayScreenRuntime &context, const TransportSchedule &schedule)
{
    const TransportScheduleRoute *pRoute = selectedRoute(context, schedule);
    const std::optional<int> day = context.transportSchedule().selectedDay;

    if (pRoute == nullptr || !day)
    {
        return;
    }

    const int waitFood = transportWaitDays(schedule.today, *day) * schedule.foodPerWaitDay;

    if (!tripRefusal(context.partyReadOnly(), schedule, waitFood).empty())
    {
        return;
    }

    EventDialogAction action;
    action.kind = EventDialogActionKind::HouseService;
    action.id = uint32_t(HouseActionId::TransportScheduledTrip);
    action.label = pRoute->destinationName;
    action.argument = transportScheduledTripArgument(pRoute->routeIndex, *day);
    context.closeTransportSchedule();
    context.executeDialogAction(action);
}

void activate(GameplayScreenRuntime &context, const TransportSchedule &schedule, int target)
{
    if (target == TargetClose || target == TargetOutside)
    {
        context.closeTransportSchedule();
    }
    else if (target == TargetTravel)
    {
        travel(context, schedule);
    }
    else if (target >= TargetDestinationBase)
    {
        const int day = (target - TargetDestinationBase) / 16;
        selectDay(context, schedule, day, size_t((target - TargetDestinationBase) % 16));
    }
    else if (target >= TargetRowBase)
    {
        selectDay(context, schedule, target - TargetRowBase, std::nullopt);
    }
}

// A carved button: its art by state (greyed text when it cannot act) and a centred Fondamento label.
void renderButton(GameplayScreenRuntime &context, const Painter &paint, const Box &box, float k, const char *pArt,
    const std::string &label, bool enabled, bool hovered, bool pressed, float labelSize)
{
    const std::string state = !enabled ? "normal" : pressed ? "pressed" : hovered ? "hover" : "normal";
    GameplayUiSkin::renderTexture(context, std::string(pArt) + state, box.rect(k));
    const float textHeight = paint.lineHeight(TitleFont, labelSize * k);
    paint.text(TitleFont, labelSize * k, !enabled ? Disabled : hovered ? Gold : Label, label,
        box.x + box.width / 2, box.y + (box.height - textHeight) / 2 + (pressed ? k : 0), 1);
}

void renderRow(GameplayScreenRuntime &context, const Painter &paint, const Layout &layout,
    const TransportSchedule &schedule, int day, int hovered)
{
    const GameplayUiController::TransportScheduleState &state = context.transportSchedule();
    const Box &row = layout.rows[size_t(day)];
    const float k = layout.k;
    const std::vector<const TransportScheduleRoute *> routes = departures(schedule, day);
    const bool today = day == schedule.today;
    const bool selected = state.selectedDay == day && !routes.empty();
    const bool rowHovered = !routes.empty()
        && (hovered == TargetRowBase + day || (hovered >= TargetDestinationBase
            && (hovered - TargetDestinationBase) / 16 == day));
    const float line = std::max(1.0f, std::round(k * 0.6f));

    // A row with departures lights up under the pointer, as a button does.
    if (selected)
    {
        paint.fill(row, SelectedFill);
        paint.frame(row, line, Gold);
    }
    else if (rowHovered)
    {
        paint.fill(row, today ? TodayHoverFill : HoverFill);
        paint.frame(row, line, HoverBorder);
    }
    else if (today)
    {
        paint.fill(row, TodayFill);
    }

    if (today)
    {
        paint.fill({row.x, row.y, 3 * k, row.height}, Gold);
    }

    if (day < 6 && !selected && state.selectedDay != day + 1)
    {
        paint.fill({row.x + 8 * k, row.y + row.height - line, row.width - 16 * k, line}, RowRule);
    }

    const std::string &dayName = DayNames[size_t(day)];
    const float dayHeight = paint.lineHeight(TitleFont, RowDaySize * k);
    const float dayY = row.y + (row.height - dayHeight) / 2;
    paint.text(TitleFont, RowDaySize * k, selected ? Gold : Ivory, dayName, row.x + 10 * k, dayY);

    if (today)
    {
        paint.text(TextFont, SmallSize * k, Gold, "TODAY",
            row.x + 16 * k + paint.width(TitleFont, RowDaySize * k, dayName),
            row.y + (row.height - paint.lineHeight(TextFont, SmallSize * k)) / 2 + 1 * k);
    }

    const float nameHeight = paint.lineHeight(TextFont, NameSize * k);
    const float nameY = row.y + (row.height - nameHeight) / 2;

    if (routes.empty())
    {
        paint.text(TextFont, NameSize * k, Faint, "No departures", row.x + DayColumn * k, nameY);
        return;
    }

    const std::vector<Box> boxes = destinationBoxes(context, layout, row, routes);
    const bool several = routes.size() > 1;
    const float smallHeight = paint.lineHeight(TextFont, SmallSize * k);

    for (size_t index = 0; index < routes.size(); ++index)
    {
        const TransportScheduleRoute &route = *routes[index];
        const Box &box = boxes[index];
        const bool picked = selected && route.routeIndex == state.selectedRouteIndex;
        const bool dimmed = selected && several && !picked;
        paint.text(TextFont, NameSize * k, dimmed ? Muted : selected ? Bright : Ivory, route.destinationName, box.x,
            nameY);
        const float nameWidth = paint.width(TextFont, NameSize * k, route.destinationName);
        // The days share the name's baseline.
        paint.text(TextFont, SmallSize * k, dimmed ? Faint : selected ? Ivory : Muted, daysText(route.travelDays),
            box.x + nameWidth + 6 * k, nameY + (nameHeight - smallHeight) * 0.78f);

        // Of several departures, the picked one is underlined (and a hovered one faintly).
        const bool underline = several
            && (picked || hovered == TargetDestinationBase + day * 16 + int(index));

        if (underline)
        {
            paint.fill({box.x, nameY + nameHeight * 0.92f, nameWidth, line}, picked ? Gold : Muted);
        }
    }
}

void renderFooter(GameplayScreenRuntime &context, const Painter &paint, const Layout &layout,
    const TransportSchedule &schedule, int hovered)
{
    const Box &footer = layout.footer;
    const float k = layout.k;
    const float left = footer.x + Padding * k;
    paint.fill({left - 4 * k, footer.y, footer.width - 2 * (Padding - 4) * k, std::max(1.0f, std::round(k * 0.6f))},
        Rule);
    const TransportScheduleRoute *pRoute = selectedRoute(context, schedule);
    const std::optional<int> day = context.transportSchedule().selectedDay;

    if (pRoute == nullptr || !day)
    {
        paint.text(TextFont, FactSize * k, Muted, "Click a day to see the wait, the trip and the cost.", left,
            footer.y + (footer.height - paint.lineHeight(TextFont, FactSize * k)) / 2 - 3 * k);
        return;
    }

    const Party *pParty = context.partyReadOnly();
    const int wait = transportWaitDays(schedule.today, *day);
    const int waitFood = wait * schedule.foodPerWaitDay;
    const std::string refusal = tripRefusal(pParty, schedule, waitFood);
    const float maxRight = footer.x + footer.width - Padding * k;
    const Box &button = layout.travel;
    paint.text(TitleFont, DaySize * k, Gold, pRoute->destinationName, left,
        button.y + (button.height - paint.lineHeight(TitleFont, DaySize * k)) / 2);

    // Under the name and the button, the trip on one line and its costs on the next, label muted and value bright;
    // the fare and the waiting food red when the party is short, and why after them.
    const float factHeight = paint.lineHeight(TextFont, FactSize * k);
    float x = left;
    float y = button.y + button.height + 3 * k;
    const auto fact = [&](const std::string &name, const std::string &value, uint32_t colour)
    {
        const std::string spaced = name + " ";
        const float needed = paint.width(TextFont, FactSize * k, spaced + value);

        if (x > left && x + needed > maxRight)
        {
            return;
        }

        paint.text(TextFont, FactSize * k, Muted, spaced, x, y);
        x += paint.width(TextFont, FactSize * k, spaced);
        paint.text(TextFont, FactSize * k, colour, value, x, y);
        x += paint.width(TextFont, FactSize * k, value) + 14 * k;
    };
    const int arrival = (*day + pRoute->travelDays) % 7;
    const int gold = pParty != nullptr ? pParty->gold() : 0;
    const int food = pParty != nullptr ? pParty->food() : 0;
    fact("Departs", DayNames[size_t(*day)], Ivory);
    fact("On the road", daysText(pRoute->travelDays), Ivory);
    fact("Arrives", DayNames[size_t(arrival)], Ivory);
    x = left;
    y += factHeight;
    fact("Fare", std::to_string(schedule.fare) + " gold", gold < schedule.fare ? Bad : Good);
    fact("Food to wait", wait == 0 ? "none" : std::to_string(waitFood) + " of " + std::to_string(food),
        wait == 0 ? Ivory : food < waitFood ? Bad : Good);

    if (!refusal.empty())
    {
        paint.text(TextFont, SmallSize * k, Bad, refusal, x, y + (factHeight - paint.lineHeight(TextFont,
            SmallSize * k)) * 0.78f);
    }

    const bool pressed = hovered == TargetTravel && context.transportSchedule().pressedTarget == TargetTravel;
    renderButton(context, paint, layout.travel, k, "obsidian_button_rest_", travelLabel(context, schedule),
        refusal.empty(), hovered == TargetTravel, pressed, ButtonLabelSize);
}
}

bool GameplayTransportSchedule::isOpen(GameplayScreenRuntime &context)
{
    if (!context.transportSchedule().active)
    {
        return false;
    }

    if (scheduleHouse(context) == nullptr)
    {
        context.closeTransportSchedule();
        return false;
    }

    return true;
}

void GameplayTransportSchedule::render(GameplayScreenRuntime &context, int width, int height)
{
    if (context.currentHudScreenState() != GameplayHudScreenState::Dialogue || !isOpen(context))
    {
        return;
    }

    const HouseEntry &house = *scheduleHouse(context);
    const TransportSchedule schedule = currentSchedule(context, house);
    const std::optional<Layout> layout = layoutFor(context, width, height);

    if (!layout)
    {
        return;
    }

    const Painter paint(context);
    const float k = layout->k;
    const GameplayInputFrame *pInput = context.currentGameplayInputFrame();
    const int hovered = pInput != nullptr ? targetAt(context, *layout, schedule, pInput->pointerX, pInput->pointerY)
                                          : TargetNone;
    paint.fill({0, 0, float(width), float(height)}, Veil);

    // The carved Obsidian frame on the dark reading surface.
    const Box &panel = layout->panel;
    GameplayUiSkin::renderPanel(context, panel.rect(k), false, BorderScale);

    // Header: the house's name (shortened clear of Close), today and the costs, the close button.
    const float left = panel.x + Padding * k;
    const float titleY = panel.y + HeaderTop * k;
    paint.text(TitleFont, TitleSize * k, Gold,
        paint.fitted(TitleFont, TitleSize * k, house.name, layout->close.x - 14 * k - left), left, titleY);
    paint.text(TextFont, FactSize * k, Muted, "Today is " + std::string(DayNames[size_t(schedule.today)])
            + "  \xB7  fare " + std::to_string(schedule.fare) + " gold  \xB7  waiting costs "
            + std::to_string(schedule.foodPerWaitDay) + " food a day",
        left, titleY + paint.lineHeight(TitleFont, TitleSize * k) + SubtitleGap * k);
    const bool closePressed = hovered == TargetClose && context.transportSchedule().pressedTarget == TargetClose;
    renderButton(context, paint, layout->close, k, "obsidian_button_close_", "Close", true, hovered == TargetClose,
        closePressed, 12.5f);
    paint.fill({left - 4 * k, panel.y + HeaderHeight * k, panel.width - 2 * (Padding - 4) * k,
                   std::max(1.0f, std::round(k * 0.6f))},
        Rule);

    for (int day = 0; day < 7; ++day)
    {
        renderRow(context, paint, *layout, schedule, day, hovered);
    }

    renderFooter(context, paint, *layout, schedule, hovered);
}

void GameplayTransportSchedule::handleInput(GameplayScreenRuntime &context, const GameplayInputFrame &input)
{
    if (!isOpen(context))
    {
        return;
    }

    GameplayUiController::TransportScheduleState &state = context.transportSchedule();
    const HouseEntry &house = *scheduleHouse(context);
    const TransportSchedule schedule = currentSchedule(context, house);
    const std::optional<Layout> layout = layoutFor(context, input.screenWidth, input.screenHeight);
    const bool *pKeys = input.keyboardState();
    const bool escape = pKeys[SDL_SCANCODE_ESCAPE];
    const bool accept = pKeys[SDL_SCANCODE_RETURN] || pKeys[SDL_SCANCODE_KP_ENTER] || pKeys[SDL_SCANCODE_SPACE];
    const bool up = pKeys[SDL_SCANCODE_UP];
    const bool down = pKeys[SDL_SCANCODE_DOWN];
    const bool left = pKeys[SDL_SCANCODE_LEFT];
    const bool right = pKeys[SDL_SCANCODE_RIGHT];
    const bool pointer = input.leftMouseButton.held;
    const bool escapePressed = escape && !state.escapeHeld;
    const bool acceptPressed = accept && !state.acceptHeld;
    const bool upPressed = up && !state.upHeld;
    const bool downPressed = down && !state.downHeld;
    const bool sidePressed = (left && !state.leftHeld) || (right && !state.rightHeld);
    const bool pointerPressed = pointer && !state.pointerHeld;
    const bool pointerReleased = !pointer && state.pointerHeld;
    state.escapeHeld = escape;
    state.acceptHeld = accept;
    state.upHeld = up;
    state.downHeld = down;
    state.leftHeld = left;
    state.rightHeld = right;
    state.pointerHeld = pointer;

    // The dialogue under the popup sees these keys and the click as already used, so none acts on it when the popup
    // closes.
    GameplayOverlayInteractionState &interaction = context.interactionState();
    interaction.closeOverlayLatch = escape;
    interaction.eventDialogAcceptLatch = accept;
    interaction.eventDialogSelectUpLatch = up;
    interaction.eventDialogSelectDownLatch = down;
    interaction.dialogueClickLatch = false;
    interaction.dialoguePressedTarget = {};

    if (escapePressed)
    {
        interaction.menuToggleLatch = true;
        context.closeTransportSchedule();
        return;
    }

    if (!layout)
    {
        return;
    }

    if (upPressed || downPressed)
    {
        stepDay(context, schedule, upPressed ? -1 : 1);
    }
    else if (sidePressed && state.selectedDay)
    {
        selectDay(context, schedule, *state.selectedDay, std::nullopt);
    }
    else if (acceptPressed)
    {
        travel(context, schedule);
        return;
    }

    const int target = targetAt(context, *layout, schedule, input.pointerX, input.pointerY);

    if (pointerPressed)
    {
        state.pressedTarget = target;
    }
    else if (pointerReleased)
    {
        const int pressed = state.pressedTarget;
        state.pressedTarget = TargetNone;

        if (pressed != TargetNone && pressed == target)
        {
            activate(context, schedule, target);
        }
    }
}
}
