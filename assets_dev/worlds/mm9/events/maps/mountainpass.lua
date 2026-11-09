-- Mountain Pass, MM9 rework (level_generation/projects/mm9r_mountainpass/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}}})

-- Doors: each MM9 door group opens and closes on a click.

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest0

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end

-- MountainPass.scr :OnStep (Trigger0, Trigger1 send "Use" once each) and :OnAward on the second.
local PASS_TRIGGERS = {{name = "Trigger0", low = {15461, -5163, -328}, high = {17427, -4508, 983}}, {name = "Trigger1", low = {-11900, 12368, 0}, high = {-11245, 14334, 1311}}}
local function inPassBox(b, x, y, z)
    return x >= b.low[1] - 37 and x <= b.high[1] + 37 and y >= b.low[2] - 37 and y <= b.high[2] + 37
        and z + 170 >= b.low[3] and z <= b.high[3] + 37
end
local function passAward()
    if has(80) or has(176) then return end   -- once (MM9 paid key 176's branch again after key 80)
    local xp = 12500 -- MM9 GiveExp 14000, mm9_quest_xp_profile.yml
    if has(79) then reward(80, xp, 0) else reward(176, xp, 0) end
end
handlers[600] = function()
    local x, y, z = evt.GetPartyPosition()
    for _, b in ipairs(PASS_TRIGGERS) do
        if var("Stepped" .. b.name) == 0 and inPassBox(b, x, y, z) then
            set("Stepped" .. b.name, 1)   -- the trigger turns itself off
            set("PassSteps", var("PassSteps") + 1)
            if var("PassSteps") == 2 then passAward() end
        end
    end
end

handlers[1] = function()
    if handlers.regionLoad then handlers.regionLoad() end
end

-- MM9's BonePile objects (dungeon/objects.py): a click searches the pile (evt.SearchLootProp: its
-- TreasureLevel loot once, DiseaseChance; the pile stays).
handlers[30263] = function() evt.SearchLootProp("mm9:mountainpass:object:263") end   -- BonePile0
handlers[30264] = function() evt.SearchLootProp("mm9:mountainpass:object:264") end   -- BonePile1
handlers[30265] = function() evt.SearchLootProp("mm9:mountainpass:object:265") end   -- BonePile2
handlers[30266] = function() evt.SearchLootProp("mm9:mountainpass:object:266") end   -- BonePile3
handlers[30267] = function() evt.SearchLootProp("mm9:mountainpass:object:267") end   -- BonePile4


RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(30263, "Bone Pile", handlers[30263], "Bone Pile")
RegisterEvent(30264, "Bone Pile", handlers[30264], "Bone Pile")
RegisterEvent(30265, "Bone Pile", handlers[30265], "Bone Pile")
RegisterEvent(30266, "Bone Pile", handlers[30266], "Bone Pile")
RegisterEvent(30267, "Bone Pile", handlers[30267], "Bone Pile")
RegisterMapTimerEvent(600, seconds(0.5), handlers[600], "Mountain Pass triggers", "", seconds(0.5))
