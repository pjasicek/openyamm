-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- Deyja's nights (§3.2): after 21:30 a warning, and between 22:00 and 04:00 a one-in-ten chance each check (sure
-- shortly before midnight) that the dead rise around the party, in ten waves of rotting corpses, once a night.
local DayMinutes = 24 * 60

local function night(minutes)
    local time = minutes % DayMinutes
    return time > 22 * 60 or time < 4 * 60
end

-- The night's number changes at noon, so an evening and the small hours after it are one night (Maps/7out05.lua:17).
local function nightNumber(minutes)
    return math.floor((minutes + 12 * 60) / DayMinutes)
end

RegisterMapTimerEvent(60001, 300, function()
    local minutes = CurrentGameMinutes()
    local day = nightNumber(minutes)
    if evt.GetMapVar("MawRiseDay", -1) == day then
        return
    end
    if evt.GetMapVar("MawWarnDay", -1) ~= day and minutes % DayMinutes >= 21.5 * 60 then
        evt.SetMapVar("MawWarnDay", day)
        evt.StatusText("The night is dark and full of terrors")
    end
    if night(minutes) and (math.random() < 0.1 or minutes % DayMinutes > 23.9 * 60) then
        evt.SetMapVar("MawRiseDay", day)
        evt.SetMapVar("MawRiseWaves", 10)
        evt.SetMapVar("MawRiseFirst", 1)
        evt.StatusText("In the night the dead rise")
    end
end, "MAW Deyja night")

RegisterMapTimerEvent(60002, 300, function()
    -- Waves left at dawn die with the night.
    local waves = evt.GetMapVar("MawRiseWaves", 0)
    if waves <= 0 or not night(CurrentGameMinutes())
        or evt.GetMapVar("MawRiseDay", -1) ~= nightNumber(CurrentGameMinutes()) then
        return
    end
    local x, y = evt.GetPartyPosition()
    local function rise(dx, dy, count, radius)
        evt.SummonMonstersById{monster = 427, x = x + dx, y = y + dy, z = 0, count = count, tiers = {50, 35, 15},
            radius = radius, group = 2, speed = 350}
    end
    local around = {{4000, 4000}, {4000, -4000}, {-4000, 4000}, {-4000, -4000}, {0, 4000}, {4000, 0}, {-4000, 0},
        {0, -4000}}
    if evt.GetMapVar("MawRiseFirst", 0) ~= 0 then
        evt.SetMapVar("MawRiseFirst", 0)
        rise(0, 0, 5, 4000)
        for _, offset in ipairs(around) do
            rise(offset[1], offset[2], 1, 1160)
        end
    end
    rise(0, 0, 3, 4000)
    for _, offset in ipairs(around) do
        rise(offset[1], offset[2], 1, 4160)
    end
    evt.SetMapVar("MawRiseWaves", waves - 1)
end, "MAW rising dead")
