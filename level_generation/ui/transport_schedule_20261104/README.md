# Stable and ship schedule — 4 November 2026

A player request: stables and boats should show their timetable in game, so nobody waits day after day for a
destination the house never serves, and a trip on another day can be booked by waiting for it.

The user approved the browser [mockup](mockup.html) (third revision) on 2026-11-04 and asked for it natively:
- a **Schedule** topic on every stable and boat, above today's routes;
- a popup that can be closed, listing **Monday to Sunday** with today marked;
- **no "By destination" tab** and **no "in N days" notes** (removed in the second revision);
- the **whole row is clickable** and the selected row is framed (third revision);
- the fare and food line stays.

After the first native version the user asked (2026-11-04) for a bigger popup filling the scene, larger and sharper
text, the Obsidian frame, surface and buttons, and a fixed **one food per day** of waiting (waiting until morning and
resting costs about that on average).

## In game

| Opened (first Obsidian version) | A day selected, another hovered |
| --- | --- |
| ![Opened](captures/topic.jpg) | ![Wednesday](captures/selected.jpg) |

| Not enough food | After the trip (2 days waiting + 3 on the road, 2 food) |
| --- | --- |
| ![Refused](captures/not_enough_food.jpg) | ![Arrived](captures/arrived.jpg) |

Captured at Free Haven Travel East (MM6 `outc2.odm`, `event 14`) with `debug.menu_input_tour_path`.

## Behaviour

- **Rows:** a day lists its departures (destination and days on the road); a day without any says "No departures".
  Today has a gold bar and the "Today" tag; the selected day is framed in gold.
- **Selecting:** a click on a row selects its departure. On a day with several, a click on a name picks it, a click
  elsewhere on the row (or Left/Right) moves to the next; the picked name is underlined and the others dimmed.
  Up and Down step through the days that have departures.
- **Footer:** the destination, departure day, days on the road, arrival day, fare and the food the wait costs. The fare
  or the food turns red, with the reason below, when the party is short.
- **Travel:** the button reads "Travel now" or "Wait N days and travel" (Enter does the same). Waiting eats one food
  a day and advances whole days, so the house stays open; then the existing route travel runs unchanged (fare, rest
  and heal for the trip, map move, speech).
- **Look:** the shared carved Obsidian frame on the dark reading surface (`GameplayUiSkin::renderPanel`), the wide
  rest button art for the travel button and the close button art for Close. The main text sizes land on the faces'
  raster heights (Fondamento 32, Alegreya 24 pixels at 1600x900), so it draws unscaled.
- **Closing:** the Close button, a click outside the panel, or Escape. Escape closes only the popup.
- **Routes shown:** the same as the dialogue's: event overrides, quest bits (a locked route stays hidden) and hireling
  day reductions apply.
- **MM9 docks (2026-11-06):** the same popup opens from the **Schedule** row of an MM9 dock's talk (the talk bar, no
  house dialogue), centred on the screen, with the dock's one boat a weekday from `transport_routes.txt`
  (`buildMm9TransportSchedule`, its raw-key conditions applied); its trip is the talk's `Mm9RudeTransportRoute` with
  the departure weekday (`secondaryId` day + 1), which waits and eats as here. Tests: `tests/Mm9TransportRouteTests.cpp`.

## Code

- `game/gameplay/HouseInteraction.*`: `HouseActionId::TransportSchedule` (the topic) and `TransportScheduledTrip`
  (argument `route:day`, day 0 Monday), `buildTransportSchedule`, `transportWaitDays`; the trip shares
  `travelByTransport` with `TransportRoute`.
- `game/ui/GameplayTransportSchedule.*`: the popup's drawing and input, centred on the dialogue's `DialogueVideoArea`.
  It takes the dialogue's input while open (`GameplayOverlayInputController::handleDialogueOverlayInput`) and runs
  the trip through `GameplayScreenRuntime::executeDialogAction`, the clicked-topic path.
- State: `GameplayUiController::TransportScheduleState`.
- Tests: `tests/HouseDialogueRegressionTests.cpp` ("transport schedule lists the week and a scheduled trip waits for
  its day", "a scheduled trip on a day the route does not run is refused").
