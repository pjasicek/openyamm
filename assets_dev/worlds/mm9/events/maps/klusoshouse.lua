-- Klusos House, MM9 rework (level_generation/projects/mm9r_klusoshouse/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {RDoor10a = 1, RDoor10b = 2, RDoor11a = 3, RDoor11b = 4, RDoor12a = 5, RDoor12b = 6, RDoor13a = 7, RDoor13b = 8, RDoor14a = 9, RDoor14b = 10, RDoor15a = 11, RDoor15b = 12, RDoor16a = 13, RDoor16b = 14, RDoor2 = 15, RDoor4 = 17, RDoor5 = 18, RDoor6 = 16, RDoor9a = 19, RDoor9b = 20, RotatingDoor0a = 21, RotatingDoor0b = 22, RotatingDoor3a = 23, RotatingDoor3b = 24, RotatingDoor7 = 25, RotatingDoor8 = 26}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) evt.SetDoorState(2, DoorAction.Trigger) end   -- RDoor10
handlers[102] = function() evt.SetDoorState(3, DoorAction.Trigger) evt.SetDoorState(4, DoorAction.Trigger) end   -- RDoor11
handlers[103] = function() evt.SetDoorState(5, DoorAction.Trigger) evt.SetDoorState(6, DoorAction.Trigger) end   -- RDoor12
handlers[104] = function() evt.SetDoorState(7, DoorAction.Trigger) evt.SetDoorState(8, DoorAction.Trigger) end   -- RDoor13
handlers[105] = function() evt.SetDoorState(9, DoorAction.Trigger) evt.SetDoorState(10, DoorAction.Trigger) end   -- RDoor14
handlers[106] = function() evt.SetDoorState(11, DoorAction.Trigger) evt.SetDoorState(12, DoorAction.Trigger) end   -- RDoor15
handlers[107] = function() evt.SetDoorState(13, DoorAction.Trigger) evt.SetDoorState(14, DoorAction.Trigger) end   -- RDoor16
handlers[108] = function() evt.SetDoorState(17, DoorAction.Trigger) evt.SetDoorState(18, DoorAction.Trigger) end   -- RDoor4
handlers[109] = function() evt.SetDoorState(19, DoorAction.Trigger) evt.SetDoorState(20, DoorAction.Trigger) end   -- RDoor9
handlers[110] = function() evt.SetDoorState(21, DoorAction.Trigger) evt.SetDoorState(22, DoorAction.Trigger) end   -- RotatingDoor0
handlers[111] = function() evt.SetDoorState(23, DoorAction.Trigger) evt.SetDoorState(24, DoorAction.Trigger) end   -- RotatingDoor3
handlers[112] = function() evt.SetDoorState(25, DoorAction.Trigger) evt.SetDoorState(26, DoorAction.Trigger) end   -- RotatingDoor7

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest1

-- RDoor2/RDoor6, the great hall's east door: a click swings both leaves (no doorway portal: the hall is one
-- room with the gallery above it).
handlers[120] = function() evt.SetDoorState(DOORS.RDoor2, DoorAction.Trigger); evt.SetDoorState(DOORS.RDoor6, DoorAction.Trigger) end

-- The Blackheart (Blackheart.scr :OnUse): a world item (29); its pickup gives key 223 and rings the alarm bell.
-- Removing it breaks the guards' object link (KlusosHidden.scr, KlusosSleeper.scr :OnObjectLinkBroken): the hidden guards
-- become visible and solid, the sleepers stand up; all run baseMelee.scr.
local SLEEPERS = {12, 13, 14, 15, 16, 17, 18, 19}
local function linkBroken()
    evt.SetMonGroupBit(1, MonsterBits.Invisible, false)
    for _, index in ipairs(SLEEPERS) do evt.WakeActor(index) end
end
handlers[75] = function()
    if MM9.hasKey(223) == 1 then return end
    MM9.giveKey(223)
    evt.PlaySoundName("events/alarmbell.wav", 0, 0, 0)
    linkBroken()
end

-- The letter on the kitchen table (BookLetter.scr, ScriptParams "456 Letter": DoLetter 456).
handlers[76] = function() evt.SimpleMessage("Post to the Kitchen\n\nTo the Kitchen:\nThe meals as of late have been increasingly foul in flavor.  You know I am not one who makes threats idly.  If you value your jobs, I would suspect you would be doing what you can to better the taste of the meals you deliver to me.\nLord Kluso") end


RegisterEvent(101, "Door", handlers[101], "Door")
RegisterEvent(102, "Door", handlers[102], "Door")
RegisterEvent(103, "Door", handlers[103], "Door")
RegisterEvent(104, "Door", handlers[104], "Door")
RegisterEvent(105, "Door", handlers[105], "Door")
RegisterEvent(106, "Door", handlers[106], "Door")
RegisterEvent(107, "Door", handlers[107], "Door")
RegisterEvent(108, "Door", handlers[108], "Door")
RegisterEvent(109, "Door", handlers[109], "Door")
RegisterEvent(110, "Door", handlers[110], "Door")
RegisterEvent(111, "Door", handlers[111], "Door")
RegisterEvent(112, "Door", handlers[112], "Door")
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(120, "Door", handlers[120], "Door")
RegisterEvent(75, "Blackheart", handlers[75])
RegisterEvent(76, "Letter", handlers[76], "Letter")
