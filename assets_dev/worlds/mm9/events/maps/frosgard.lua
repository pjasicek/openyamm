-- Frosgard, MM9 rework (level_generation/projects/mm9r_frosgard/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 902}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}}})

-- Doors: each MM9 door group opens and closes on a click.

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest0
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest1

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end

-- StatStone0 (StatStone: Stat 2 Endurance, +20 for 3700 s)
handlers[390] = function()
    if evt.CurrentGameMinutes() < var("StatStoneUntil0") then
        evt.StatusText("The stone's power is still with you.") return
    end
    evt.ApplyPartyPrimaryStatBuff(3, 20, 3700)
    set("StatStoneUntil0", evt.CurrentGameMinutes() + 62)
    evt.PlaySoundName("events/dingbell.wav", 0, 0, 0)
    evt.StatusText("+20 Endurance for 1.02778 hours")
end
-- NPC221.scr :OnRude -> :Promo, :PromoteDruid (the Green Man, RUDE 221): his tasks done (key 279): key 280,
-- 63 000 experience, 5 000 gold, item 213; each character holding key 445-448 becomes a Druid (key taken).
handlers[50103] = function()
    if has(280) or not has(279) then return end
    reward(280, 37500, 5000); MM9.giveItem(213, "frosgard:GreenMan") -- MM9 GiveExp 63000, mm9_quest_xp_profile.yml
    MM9.promoteParty("Druid")   -- every eligible member (not MM9's per-character keys 445-448)
end

handlers[1] = function()
    if handlers.regionLoad then handlers.regionLoad() end
end

-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[53008] = function() MM9.playSound("voices/npc/npc_189.wav"); MM9.openRude(189) end   -- CommonerElfMaleA0
handlers[53103] = function() MM9.playSound("voices/npc/npc_221.wav"); MM9.openRude(221) end   -- GreenMan0

-- MM9's bonus props (dungeon/objects.py bonus_lines; the use of each class, object.lto): wells, cauldrons,
-- cook pots and clovers.
handlers[30083] = function() MM9.useCauldron(83, 4, 5) end   -- obj_non-solid tree0 (Cauldron)
handlers[30120] = function() MM9.useCookpot(120, 25, 4, 10, 16) end   -- obj_Cookpot0 (Cookpot)
handlers[30121] = function() MM9.useCookpot(121, 50, 4, 15, 16) end   -- obj_Cookpot1 (Cookpot)

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[23104] = 1, [23105] = 1}
handlers[901] = function()
    for cog, value in pairs(HINTS) do
        local want = (var("HintOff" .. cog) == 0 and evt.CheckSkill(29, 0, value)) and 2 or 1
        if var("Hint" .. cog) ~= want then
            set("Hint" .. cog, want)
            evt.SetFacetBit(cog, FacetBits.Invisible, want == 1)
        end
    end
end
-- MM9's WeatherMan switched by touch Triggers (dungeon/objects.py weather_triggers): entering a box sends its
-- On / Off; On fades to the WeatherMan's FogOn state, Off to its FogOff state (evt.SetFog / evt.ClearFog, over the
-- state's TransitionTime). Map variable Weather<index>: 1 on, 2 off; set again on load without the fade.
local WEATHER = {
    [267] = {off = function(fade) evt.ClearFog(fade and 8 or 0) end, on = function(fade) evt.SetFog(127, 127, 127, 3, 16640, fade and 1 or 0, 1) end},
}
local WEATHER_TRIGGERS = {
    {name = "Trigger2", box = {{-15562, 10702, 1386}, {-15324, 11759, 2212}}, switches = {{267, true}}},
    {name = "Trigger1", box = {{-15071, 10702, 1386}, {-14833, 11759, 2212}}, switches = {{267, false}}},
    {name = "Trigger3", box = {{-15562, 10702, 1386}, {-15324, 11759, 2212}}, switches = {{267, true}}},
    {name = "Trigger4", box = {{-15071, 10702, 1386}, {-14833, 11759, 2212}}, switches = {{267, false}}},
}
local weatherInside = {}
handlers[905] = function()
    local x, y, z = evt.GetPartyPosition()
    for _, t in ipairs(WEATHER_TRIGGERS) do
        local b = t.box
        local now = x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] and z >= b[1][3] and z <= b[2][3]
        if now and not weatherInside[t.name] then
            for _, s in ipairs(t.switches) do
                set("Weather" .. s[1], s[2] and 1 or 2)
                if s[2] then WEATHER[s[1]].on(true) else WEATHER[s[1]].off(true) end
            end
        end
        weatherInside[t.name] = now
    end
    evt.StartTimer(905, seconds(0.25))
end
handlers[902] = function()   -- map load: the shared objects
    for cog, _ in pairs(HINTS) do set("Hint" .. cog, 0) end
    handlers[901]()
    for k, w in pairs(WEATHER) do
        local f = w.on
        if var("Weather" .. k) == 2 then f = w.off elseif var("Weather" .. k) ~= 1 then f = nil end
        if f ~= nil then f(false) end
    end
    for _, t in ipairs(WEATHER_TRIGGERS) do weatherInside[t.name] = false end
    handlers[905]()
end

RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(390, "Stat stone", handlers[390], "Touch")
RegisterEvent(50103, "The Green Man", handlers[50103])
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(53008, "Fland de Allasan A'Lanth a'ryshar", handlers[53008])
RegisterEvent(53103, "The Green Man", handlers[53103])
RegisterEvent(30083, "Cauldron", handlers[30083], "Drink")
RegisterEvent(30120, "Cook pot", handlers[30120], "Eat")
RegisterEvent(30121, "Cook pot", handlers[30121], "Eat")
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterMapTimerEvent(905, seconds(3), handlers[905], "Weather triggers", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
