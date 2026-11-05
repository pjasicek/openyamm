#include "game/events/ScriptedEventTimer.h"

#include <algorithm>
#include <cmath>
#include <limits>

namespace OpenYAMM::Game
{
namespace
{
constexpr double LegacyTicksPerGameMinute = 256.0;
constexpr double GameMinutesPerDay = 24.0 * 60.0;
constexpr double GameMinutesPerWeek = 7.0 * GameMinutesPerDay;
constexpr double GameMinutesPerMonth = 28.0 * GameMinutesPerDay;
constexpr double GameMinutesPerYear = 12.0 * GameMinutesPerMonth;
constexpr double LegacyTimerPollDelayGameMinutes = 0.5;
constexpr double MinimumNativeTimerIntervalGameMinutes = 0.5;

double calendarPeriodGameMinutes(ScriptedEventTimerScheduleKind scheduleKind)
{
    switch (scheduleKind)
    {
        case ScriptedEventTimerScheduleKind::Daily: return GameMinutesPerDay;
        case ScriptedEventTimerScheduleKind::Weekly: return GameMinutesPerWeek;
        case ScriptedEventTimerScheduleKind::Monthly: return GameMinutesPerMonth;
        case ScriptedEventTimerScheduleKind::Yearly: return GameMinutesPerYear;
        case ScriptedEventTimerScheduleKind::Relative: return GameMinutesPerDay;
        case ScriptedEventTimerScheduleKind::Interval:
            return 0.0;
    }

    return 0.0;
}

double dailyStartOffsetGameMinutes(const ScriptedEventTimerDefinition &definition)
{
    return static_cast<double>(definition.startHour) * 60.0
        + static_cast<double>(definition.startMinute)
        + static_cast<double>(definition.startSecond) / 60.0;
}

double nextExactAlarmGameMinutes(double startGameMinutes, double periodGameMinutes, double currentGameMinutes)
{
    if (startGameMinutes > currentGameMinutes)
    {
        return startGameMinutes;
    }

    const double elapsedPeriods = std::floor((currentGameMinutes - startGameMinutes) / periodGameMinutes) + 1.0;
    return startGameMinutes + elapsedPeriods * periodGameMinutes;
}

ScriptedEventTimerState initializeTimer(
    const ScriptedEventTimerDefinition &definition,
    double currentGameMinutes,
    int64_t lastVisitTime)
{
    ScriptedEventTimerState state = {};
    state.definition = definition;

    if (definition.origin == ScriptedEventTimerOrigin::Native)
    {
        state.nextAlarmGameMinutes = currentGameMinutes + std::max(0.0, definition.initialDelayGameMinutes);
        state.eligibleGameMinutes = currentGameMinutes;
        return state;
    }

    state.eligibleGameMinutes = currentGameMinutes + LegacyTimerPollDelayGameMinutes;

    if (definition.scheduleKind == ScriptedEventTimerScheduleKind::Interval)
    {
        const double intervalGameMinutes = static_cast<double>(definition.intervalHalfMinutes) * 0.5;
        state.nextAlarmGameMinutes = currentGameMinutes + intervalGameMinutes;
        return state;
    }

    const double periodGameMinutes = calendarPeriodGameMinutes(definition.scheduleKind);

    // Legacy OnTimer records are normal Timer calls. OnLongTimer records are refill timers and follow the
    // first-visit/last-visit path below.
    if (definition.triggerKind == ScriptedEventTimerTriggerKind::Timer)
    {
        if (definition.scheduleKind == ScriptedEventTimerScheduleKind::Daily)
        {
            state.nextAlarmGameMinutes = nextExactAlarmGameMinutes(
                dailyStartOffsetGameMinutes(definition),
                periodGameMinutes,
                currentGameMinutes);
            return state;
        }

        state.nextAlarmGameMinutes = currentGameMinutes + periodGameMinutes;
        return state;
    }

    const bool hasLastVisit = lastVisitTime != 0;
    const double lastVisitGameMinutes = legacyTimerGameMinutesFromTicks(lastVisitTime);
    state.nextAlarmGameMinutes = hasLastVisit
        ? lastVisitGameMinutes + periodGameMinutes
        : currentGameMinutes;
    state.initialCalendarFirePending = !hasLastVisit;
    return state;
}

void advanceTimerAfterFire(ScriptedEventTimerState &state, double currentGameMinutes)
{
    const ScriptedEventTimerDefinition &definition = state.definition;

    if (definition.origin == ScriptedEventTimerOrigin::Native)
    {
        if (definition.repeating)
        {
            const double intervalGameMinutes =
                std::max(MinimumNativeTimerIntervalGameMinutes, definition.intervalGameMinutes);
            state.nextAlarmGameMinutes += intervalGameMinutes;

            // Rest, waiting and map re-entry advance time without running timers; drop the missed intervals
            // instead of replaying one per frame.
            if (state.nextAlarmGameMinutes <= currentGameMinutes)
            {
                state.nextAlarmGameMinutes = currentGameMinutes + intervalGameMinutes;
            }
        }
        else
        {
            state.hasFired = true;
        }

        return;
    }

    if (definition.scheduleKind == ScriptedEventTimerScheduleKind::Interval)
    {
        state.nextAlarmGameMinutes = currentGameMinutes
            + static_cast<double>(definition.intervalHalfMinutes) * 0.5;
        state.initialCalendarFirePending = false;
        return;
    }

    const double periodGameMinutes = calendarPeriodGameMinutes(definition.scheduleKind);

    if (state.initialCalendarFirePending)
    {
        state.nextAlarmGameMinutes = currentGameMinutes + periodGameMinutes;
        state.initialCalendarFirePending = false;
        return;
    }

    while (state.nextAlarmGameMinutes <= currentGameMinutes)
    {
        state.nextAlarmGameMinutes += periodGameMinutes;
    }
}
}

double legacyTimerGameMinutesFromTicks(int64_t legacyTicks)
{
    return static_cast<double>(legacyTicks) / LegacyTicksPerGameMinute;
}

int64_t legacyTimerTicksFromGameMinutes(double gameMinutes)
{
    const double nonnegativeGameMinutes = std::max(0.0, gameMinutes);
    const double legacyTicks = nonnegativeGameMinutes * LegacyTicksPerGameMinute;

    if (legacyTicks >= static_cast<double>(std::numeric_limits<int64_t>::max()))
    {
        return std::numeric_limits<int64_t>::max();
    }

    return static_cast<int64_t>(std::llround(legacyTicks));
}

bool sameScriptedEventTimerIdentity(
    const ScriptedEventTimerDefinition &left,
    const ScriptedEventTimerDefinition &right)
{
    if (left.scope != right.scope || left.origin != right.origin || left.sourceEventId != right.sourceEventId)
    {
        return false;
    }

    if (left.origin == ScriptedEventTimerOrigin::Legacy)
    {
        return left.triggerStep == right.triggerStep && left.triggerKind == right.triggerKind;
    }

    return left.registrationIndex == right.registrationIndex;
}

std::vector<ScriptedEventTimerState> reconcileScriptedEventTimers(
    const std::vector<ScriptedEventTimerState> &savedStates,
    const std::vector<ScriptedEventTimerDefinition> &definitions,
    double currentGameMinutes,
    int64_t lastVisitTime,
    bool resetLegacyTimers)
{
    std::vector<ScriptedEventTimerState> states;
    states.reserve(definitions.size());
    std::vector<bool> usedSavedStates(savedStates.size(), false);

    for (const ScriptedEventTimerDefinition &definition : definitions)
    {
        size_t matchedIndex = savedStates.size();

        if (!(resetLegacyTimers && definition.origin == ScriptedEventTimerOrigin::Legacy))
        {
            for (size_t savedIndex = 0; savedIndex < savedStates.size(); ++savedIndex)
            {
                if (!usedSavedStates[savedIndex]
                    && sameScriptedEventTimerIdentity(savedStates[savedIndex].definition, definition))
                {
                    matchedIndex = savedIndex;
                    break;
                }
            }

            if (matchedIndex == savedStates.size())
            {
                for (size_t savedIndex = 0; savedIndex < savedStates.size(); ++savedIndex)
                {
                    if (!usedSavedStates[savedIndex]
                        && savedStates[savedIndex].migratedFromLegacySave
                        && savedStates[savedIndex].definition.eventId == definition.eventId)
                    {
                        matchedIndex = savedIndex;
                        break;
                    }
                }
            }
        }

        if (matchedIndex == savedStates.size())
        {
            states.push_back(initializeTimer(definition, currentGameMinutes, lastVisitTime));
            continue;
        }

        ScriptedEventTimerState state = savedStates[matchedIndex];
        state.definition = definition;
        if (state.migratedFromLegacySave)
        {
            state.nextAlarmGameMinutes =
                currentGameMinutes + state.migratedRemainingGameMinutes;
            state.eligibleGameMinutes = currentGameMinutes;
            state.migratedFromLegacySave = false;
            state.migratedRemainingGameMinutes = 0.0;
        }
        usedSavedStates[matchedIndex] = true;
        states.push_back(std::move(state));
    }

    return states;
}

void controlScriptedEventTimers(
    std::vector<ScriptedEventTimerState> &states,
    uint16_t eventId,
    bool start,
    double delayGameMinutes,
    double currentGameMinutes)
{
    for (ScriptedEventTimerState &state : states)
    {
        if (state.definition.eventId != eventId)
        {
            continue;
        }

        state.stopped = !start;

        if (start)
        {
            const double intervalGameMinutes =
                std::max(MinimumNativeTimerIntervalGameMinutes, state.definition.intervalGameMinutes);
            state.nextAlarmGameMinutes =
                currentGameMinutes + (delayGameMinutes >= 0.0 ? delayGameMinutes : intervalGameMinutes);
            state.eligibleGameMinutes = std::min(state.eligibleGameMinutes, currentGameMinutes);
            state.hasFired = false;
        }
    }
}

namespace
{
// Apply and clear the queued requests. firedEventId / firedAlarmGameMinutes: the timer whose handler just made them
// (0: none), whose own restart counts from its alarm while that alarm is less than the delay behind the clock.
void applyScriptedEventTimerControls(
    std::vector<ScriptedEventTimerState> &states,
    std::vector<ScriptedEventTimerControl> &controls,
    double currentGameMinutes,
    uint16_t firedEventId,
    double firedAlarmGameMinutes)
{
    for (const ScriptedEventTimerControl &control : controls)
    {
        double fromGameMinutes = currentGameMinutes;

        if (control.start && firedEventId != 0 && control.eventId == firedEventId && control.delayGameMinutes >= 0.0
            && firedAlarmGameMinutes + control.delayGameMinutes > currentGameMinutes)
        {
            fromGameMinutes = firedAlarmGameMinutes;
        }

        controlScriptedEventTimers(states, control.eventId, control.start, control.delayGameMinutes, fromGameMinutes);
    }

    controls.clear();
}
}

bool updateScriptedEventTimers(
    std::vector<ScriptedEventTimerState> &states,
    double currentGameMinutes,
    const std::function<bool(const ScriptedEventTimerDefinition &)> &executeTimer,
    std::vector<ScriptedEventTimerControl> *pControls)
{
    if (pControls != nullptr)
    {
        applyScriptedEventTimerControls(states, *pControls, currentGameMinutes, 0, 0.0);
    }

    bool executedAny = false;

    for (ScriptedEventTimerState &state : states)
    {
        if (state.stopped
            || (state.hasFired && !state.definition.repeating)
            || currentGameMinutes < state.eligibleGameMinutes
            || currentGameMinutes < state.nextAlarmGameMinutes)
        {
            continue;
        }

        const uint16_t eventId = state.definition.eventId;
        const double alarmGameMinutes = state.nextAlarmGameMinutes;
        executedAny = executeTimer(state.definition) || executedAny;
        advanceTimerAfterFire(state, currentGameMinutes);

        if (pControls != nullptr)
        {
            applyScriptedEventTimerControls(states, *pControls, currentGameMinutes, eventId, alarmGameMinutes);
        }
    }

    return executedAny;
}
}
