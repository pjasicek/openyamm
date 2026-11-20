-- Sturmford, MM9 rework (level_generation/projects/mm9r_sturmford/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {DoorChain4 = 1, Hatch1 = 2, Hatch2 = 3, Portcullis = 4, Portcullislever = 5, RotatingDoor13 = 6, RotatingDoor14 = 7, RotatingDoor15 = 9, RotatingDoor16 = 8, RotatingDoor7 = 10, RotatingDoor8 = 11, drawbridge = 12}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 902}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[103] = function() evt.SetDoorState(5, DoorAction.Trigger) evt.SetDoorState(4, DoorAction.Trigger) evt.SetDoorState(1, DoorAction.Trigger) end   -- Portcullislever
handlers[104] = function() evt.SetDoorState(6, DoorAction.Trigger) evt.SetDoorState(7, DoorAction.Trigger) end   -- RotatingDoor13
handlers[105] = function() evt.SetDoorState(8, DoorAction.Trigger) evt.SetDoorState(9, DoorAction.Trigger) end   -- RotatingDoor16

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest3
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest0
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest1
handlers[44] = function() evt.OpenChest(3) end   -- TreasureChest2

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end

-- Doors MM9 never opens (RotatingDoor7): a click says so (doorlock01.wav).
local function lockedDoor() evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0); evt.StatusText("The door is locked.") end
handlers[106] = lockedDoor
-- doorlock.scr (Hatch1): it opens only while the party carries item 596.
handlers[101] = function()
    if MM9.hasItem(596, "sturmford:Hatch1") == 1 then evt.SetDoorState(2, DoorAction.Trigger)
    else evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0); evt.StatusText("The door is locked.") end
end
-- doorlock.scr (Hatch2): it opens only while the party carries item 596.
handlers[102] = function()
    if MM9.hasItem(596, "sturmford:Hatch2") == 1 then evt.SetDoorState(3, DoorAction.Trigger)
    else evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0); evt.StatusText("The door is locked.") end
end
-- drawbridge is barred by DestructableBrush0, DestructableBrush1 (destructibles whose DeathTrigger opens it): a click says so until they are broken; breaking the last opens the door (and tells the region's
-- handlers.barredOpened).
handlers[360] = function()
    if not (evt.IsDestructibleDestroyed(315) and evt.IsDestructibleDestroyed(316)) then return end
    evt.SetDoorState(12, DoorAction.Open)
    if handlers.barredOpened then handlers.barredOpened("drawbridge") end
end
handlers[107] = function()
    if evt.IsDestructibleDestroyed(315) and evt.IsDestructibleDestroyed(316) then evt.SetDoorState(12, DoorAction.Open)
    else evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0); evt.StatusText("It is barred.") end
end
-- ForadWorld.scr (ScriptObject0, "sturmford"): key 1026 is the party's location while here (keys
-- 1024-1033), and key 5017 closes the shops from 20:00 to 06:00 (MM9's dialogues test it).
local function shopHours()
    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24
    local closed = hour >= 20 or hour < 6
    if closed and not has(5017) then MM9.giveKey(5017) elseif not closed and has(5017) then MM9.takeKey(5017) end
end
handlers[260] = function() shopHours() end

-- StatStone0 (StatStone: Stat 3 Accuracy, +10 for 3600 s)
handlers[390] = function()
    if evt.CurrentGameMinutes() < var("StatStoneUntil0") then
        evt.StatusText("The stone's power is still with you.") return
    end
    evt.ApplyPartyPrimaryStatBuff(5, 10, 3600)
    set("StatStoneUntil0", evt.CurrentGameMinutes() + 60)
    evt.PlaySoundName("events/dingbell.wav", 0, 0, 0)
    evt.StatusText("+10 Accuracy for 1 hour")
end
-- ak_disable.scr :Init ("defense"): Anskram Keep's defences are down (key 47, or 372 when done before the
-- quest): the drawbridge, the portcullis and its chain door stand open, the chains gone (:Setup).
handlers.regionLoad = function()
    if has(47) or has(372) then evt.SetDoorState(12, DoorAction.Open) evt.SetDoorState(4, DoorAction.Open) evt.SetDoorState(1, DoorAction.Open) evt.SetDoorState(5, DoorAction.Open) evt.DestroyDestructible(315) evt.DestroyDestructible(316) evt.DestroyDestructible(317) end
end

-- ak_disable.scr :Award, once both the drawbridge (its chains broken) and the portcullis are down.
local function defencesAward()
    if MM9.scrValue(203, "bDrawbridge") == 0 or MM9.scrValue(203, "bPortcullis") == 0 then return end
    if has(47) or has(372) then return end
    MM9.giveKey(has(44) and 47 or 372); MM9.giveExperience(10000); quest()
end
-- :OnDraw: both chains broken, the drawbridge falls and Drawbridgechain goes (DestructOn.scr)
handlers.barredOpened = function(group)
    if group ~= "drawbridge" then return end
    evt.DestroyDestructible(317)
    MM9.setScrValue(203, "bDrawbridge", 1)
    defencesAward()
end
local portcullisClick103 = handlers[103]
handlers[103] = function()
    portcullisClick103()
    MM9.setScrValue(203, "bPortcullis", 1)
    defencesAward()
end

handlers[1] = function()
    for k = 1024, 1033 do MM9.takeKey(k) end
    MM9.giveKey(1026)
    shopHours()
    if handlers.regionLoad then handlers.regionLoad() end
end

-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[53103] = function() MM9.playSound("voices/npc/npc_060.wav"); MM9.openRude(60) end   -- CommonerHumanMaleA0

-- MM9's BonePile objects (dungeon/objects.py): a click searches the pile (evt.SearchLootProp: its
-- TreasureLevel loot once, DiseaseChance; the pile stays).
handlers[30181] = function() evt.SearchLootProp("mm9:sturmford:object:181") end   -- BonePile0
handlers[30182] = function() evt.SearchLootProp("mm9:sturmford:object:182") end   -- BonePile1
handlers[30255] = function() evt.SearchLootProp("mm9:sturmford:object:255") end   -- BonePile2
handlers[30256] = function() evt.SearchLootProp("mm9:sturmford:object:256") end   -- BonePile3
handlers[30257] = function() evt.SearchLootProp("mm9:sturmford:object:257") end   -- BonePile4
handlers[30258] = function() evt.SearchLootProp("mm9:sturmford:object:258") end   -- BonePile5
handlers[30259] = function() evt.SearchLootProp("mm9:sturmford:object:259") end   -- BonePile6

-- MM9's breaking destructibles: an urn's SpawnObject TreasureBag drops (evt.SpawnLootContainer).
handlers[30199] = function() set("HintOff23200", 1); evt.SetFacetBit(23200, FacetBits.Invisible, true) end   -- Weakwall

handlers[34315] = function() set("HintOff23202", 1); evt.SetFacetBit(23202, FacetBits.Invisible, true) end   -- DestructableBrush0 damaged: its hint off
handlers[34316] = function() set("HintOff23201", 1); evt.SetFacetBit(23201, FacetBits.Invisible, true) end   -- DestructableBrush1 damaged: its hint off

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[23093] = 1, [23183] = 1, [23184] = 1, [23185] = 1, [23200] = 1, [23201] = 5, [23202] = 5}
handlers[901] = function()
    for cog, value in pairs(HINTS) do
        local want = (var("HintOff" .. cog) == 0 and evt.CheckSkill(29, 0, value)) and 2 or 1
        if var("Hint" .. cog) ~= want then
            set("Hint" .. cog, want)
            evt.SetFacetBit(cog, FacetBits.Invisible, want == 1)
        end
    end
end
handlers[902] = function()   -- map load: the shared objects
    for cog, _ in pairs(HINTS) do set("Hint" .. cog, 0) end
    handlers[901]()
end

RegisterEvent(103, "Door", handlers[103], "Door")
RegisterEvent(104, "Door", handlers[104], "Door")
RegisterEvent(105, "Door", handlers[105], "Door")
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(44, "Chest", handlers[44], "Chest")
RegisterEvent(106, "Locked door", handlers[106], "Door")
RegisterEvent(101, "Locked door", handlers[101], "Door")
RegisterEvent(102, "Locked door", handlers[102], "Door")
RegisterEvent(360, "drawbridge unbarred", handlers[360])
RegisterEvent(107, "Barred door", handlers[107], "Door")
RegisterMapTimerEvent(260, seconds(3), handlers[260], "Shop hours", "", seconds(3))
RegisterEvent(390, "Stat stone", handlers[390], "Touch")
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(53103, "Olaf the Thronish", handlers[53103])
RegisterEvent(30181, "Bone Pile", handlers[30181], "Bone Pile")
RegisterEvent(30182, "Bone Pile", handlers[30182], "Bone Pile")
RegisterEvent(30255, "Bone Pile", handlers[30255], "Bone Pile")
RegisterEvent(30256, "Bone Pile", handlers[30256], "Bone Pile")
RegisterEvent(30257, "Bone Pile", handlers[30257], "Bone Pile")
RegisterEvent(30258, "Bone Pile", handlers[30258], "Bone Pile")
RegisterEvent(30259, "Bone Pile", handlers[30259], "Bone Pile")
RegisterEvent(30199, "Weakwall", handlers[30199])
RegisterEvent(34315, "DestructableBrush0", handlers[34315])
RegisterEvent(34316, "DestructableBrush1", handlers[34316])
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
