-- Beethoven, MM9 rework (level_generation/projects/mm9r_beethoven/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {HedgeDoor1 = 31, HedgeDoor2 = 32, HedgeDoor3 = 33, LeftDoor10 = 1, LeftDoor12 = 3, LeftDoor14 = 5, LeftDoor15 = 7, LeftDoor16 = 9, LeftDoor18 = 11, LeftDoor19 = 13, LeftDoor2 = 15, LeftDoor21 = 17, LeftDoor22 = 19, LeftDoor3 = 21, LeftDoor5 = 23, LeftDoor9 = 25, Lever5 = 29, Lever6 = 30, RightDoor10 = 2, RightDoor12 = 4, RightDoor14 = 6, RightDoor15 = 8, RightDoor16 = 10, RightDoor18 = 12, RightDoor19 = 14, RightDoor2 = 16, RightDoor21 = 18, RightDoor22 = 20, RightDoor3 = 22, RightDoor5 = 24, RightDoor9 = 26, RotatingDoor18 = 34, SDoor11 = 27, SDoor12 = 28}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}, [45] = {4}, [46] = {5}, [47] = {6}, [48] = {7}, [49] = {8}, [50] = {9}, [51] = {10}}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) evt.SetDoorState(2, DoorAction.Trigger) end   -- Door10
handlers[102] = function() evt.SetDoorState(3, DoorAction.Trigger) evt.SetDoorState(4, DoorAction.Trigger) end   -- Door12
handlers[103] = function() evt.SetDoorState(5, DoorAction.Trigger) evt.SetDoorState(6, DoorAction.Trigger) end   -- Door14
handlers[104] = function() evt.SetDoorState(7, DoorAction.Trigger) evt.SetDoorState(8, DoorAction.Trigger) end   -- Door15
handlers[105] = function() evt.SetDoorState(9, DoorAction.Trigger) evt.SetDoorState(10, DoorAction.Trigger) end   -- Door16
handlers[106] = function() evt.SetDoorState(11, DoorAction.Trigger) evt.SetDoorState(12, DoorAction.Trigger) end   -- Door18
handlers[107] = function() evt.SetDoorState(13, DoorAction.Trigger) evt.SetDoorState(14, DoorAction.Trigger) end   -- Door19
handlers[108] = function() evt.SetDoorState(15, DoorAction.Trigger) evt.SetDoorState(16, DoorAction.Trigger) end   -- Door2
handlers[109] = function() evt.SetDoorState(17, DoorAction.Trigger) evt.SetDoorState(18, DoorAction.Trigger) end   -- Door21
handlers[110] = function() evt.SetDoorState(19, DoorAction.Trigger) evt.SetDoorState(20, DoorAction.Trigger) end   -- Door22
handlers[111] = function() evt.SetDoorState(21, DoorAction.Trigger) evt.SetDoorState(22, DoorAction.Trigger) end   -- Door3
handlers[112] = function() evt.SetDoorState(23, DoorAction.Trigger) evt.SetDoorState(24, DoorAction.Trigger) end   -- Door5
handlers[113] = function() evt.SetDoorState(25, DoorAction.Trigger) evt.SetDoorState(26, DoorAction.Trigger) end   -- Door9
handlers[114] = function() evt.SetDoorState(34, DoorAction.Trigger) end   -- SewerDoorE

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- Treasurechest4
handlers[42] = function() evt.OpenChest(1) end   -- Treasurechest3
handlers[43] = function() evt.OpenChest(2) end   -- Treasurechest2
handlers[44] = function() evt.OpenChest(3) end   -- Treasurechest1
handlers[45] = function() evt.OpenChest(4) end   -- Treasurechest0
handlers[46] = function() evt.OpenChest(5) end   -- TreasureChest5
handlers[47] = function() evt.OpenChest(6) end   -- TreasureChest4
handlers[48] = function() evt.OpenChest(7) end   -- TreasureChest3
handlers[49] = function() evt.OpenChest(8) end   -- TreasureChest2
handlers[50] = function() evt.OpenChest(9) end   -- TreasureChest1
handlers[51] = function() evt.OpenChest(10) end   -- TreasureChest0

-- Bits every handler below shares. One-shot timers: the map's timers run from load (RegisterMapTimerEvent
-- repeats), so each is armed by a variable when started and acts only when armed.
local function arm(timer, delay) set("Armed" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end
local function fired(timer)
    evt.StopTimer(timer)
    if var("Armed" .. timer) ~= 1 then return false end
    set("Armed" .. timer, 0)
    return true
end

-- The great door to the maze (Door SDoor11/12, Lever5/6): either lever (they are one double door, Lever6
-- carries the triggers) parts the two halves for good: MM9 locks the door and the lever behind it.
handlers[91] = function()   -- Lever5, Lever6
    if var("GreatDoor") == 1 then return end
    set("GreatDoor", 1)
    open("Lever5"); open("Lever6"); open("SDoor11"); open("SDoor12")
end

-- The maze's stone doors (RotatingDoor HedgeDoor1-3): MM9 swings them on a push.
handlers[92] = function() evt.SetDoorState(DOORS.HedgeDoor1, DoorAction.Trigger) end
handlers[93] = function() evt.SetDoorState(DOORS.HedgeDoor2, DoorAction.Trigger) end
handlers[94] = function() evt.SetDoorState(DOORS.HedgeDoor3, DoorAction.Trigger) end

-- Ludwig's manuscript (Ludwigsmanuscript.scr): a world item (248, dungeon/pickups.py); its pickup gives key 16 if the party
-- has spoken to Ludwig (key 14), else key 110.
local function manuscriptTaken()
    return MM9.hasKey(16) == 1 or MM9.hasKey(110) == 1
end
handlers[90] = function()   -- Manuscript
    if manuscriptTaken() then return end
    MM9.giveKey(MM9.hasKey(14) == 1 and 16 or 110)
    MM9.playSound("sounds/events/quest.wav")
end

-- The coffins (CoffinRaise.scr, CoffinMummy.scr): touching a coffin's trigger opens its lid with a stone
-- groan (the lid part's open clip). Its mummy lies inside, dormant (LoopAnim coffin2); when the lid is up it
-- wakes (PlayAnim wakeup2), and at the clip's kick (AtKick) the coffin breaks (the destructible: its
-- crumble and debris; rubble stays) and the mummy fights. Coffin<k>: 0 shut, 1 lid opening, 3 waking, 2 broken.
-- coffin k -> its mummy's actor index (CoffinMummy.scr: CanDamage 0 until it kicks free), its destructible
local MUMMIES = {[0] = 70, [1] = 71, [2] = 81, [3] = 72, [4] = 73, [5] = 74, [6] = 75, [7] = 76}
local COFFINS = {[0] = 1153, [1] = 1156, [2] = 1159, [3] = 1161, [4] = 1164, [5] = 1167, [6] = 1170, [7] = 1173}
local function coffin(k)   -- 150 + k
    if var("Coffin" .. k) ~= 0 then return end
    set("Coffin" .. k, 1)
    evt.PlaySoundName("sounds/door/stone_door02.wav", 0, 0, 0)
    evt.PlayDecorationClip(310 + k, "open")
    evt.SetMonGroupBit(80 + k, MonsterBits.Invisible, false)
    evt.PlayActorClip(MUMMIES[k], "coffin_idle", true)
    arm(200 + k, 1)
end
local function mummy(k)
    if not fired(200 + k) or var("Coffin" .. k) ~= 1 then return end
    set("Coffin" .. k, 3)
    evt.PlayActorClip(MUMMIES[k], "wakeup2", "hold")
    arm(220 + k, 3.232)
end
-- :OnPostDestroy (the kick): the coffin's destroy, SetPropNumber CanDamage, TRUE, gravity, then baseMelee.
local function kicked(k)
    set("Coffin" .. k, 2)
    evt.DestroyDestructible(COFFINS[k])
    evt.SetSprite(330 + k, true)
    evt.ClearActorPresentation(MUMMIES[k])
    evt.SetMonGroupBit(80 + k, MonsterBits.Invisible, false)
    evt.SetMonGroupBit(80 + k, MonsterBits.Hostile, true)
    MM9.setCanDamage(MUMMIES[k], true)
    evt.WakeActor(MUMMIES[k])
end
local function kick(k)
    if not fired(220 + k) or var("Coffin" .. k) ~= 3 then return end
    kicked(k)
end
handlers[150] = function() coffin(0) end   -- Trigger7 -> CoffinRaised9
handlers[200] = function() mummy(0) end   -- PetrifiedMummy7 wakes
handlers[220] = function() kick(0) end   -- PetrifiedMummy7 kicks free
handlers[151] = function() coffin(1) end   -- Trigger6 -> CoffinRaised8
handlers[201] = function() mummy(1) end   -- PetrifiedMummy6 wakes
handlers[221] = function() kick(1) end   -- PetrifiedMummy6 kicks free
handlers[152] = function() coffin(2) end   -- Trigger3 -> CoffinRaised6
handlers[202] = function() mummy(2) end   -- PetrifiedMummy3 wakes
handlers[222] = function() kick(2) end   -- PetrifiedMummy3 kicks free
handlers[153] = function() coffin(3) end   -- Trigger5 -> CoffinRaised7
handlers[203] = function() mummy(3) end   -- PetrifiedMummy5 wakes
handlers[223] = function() kick(3) end   -- PetrifiedMummy5 kicks free
handlers[154] = function() coffin(4) end   -- Trigger1 -> CoffinRaised5
handlers[204] = function() mummy(4) end   -- PetrifiedMummy1 wakes
handlers[224] = function() kick(4) end   -- PetrifiedMummy1 kicks free
handlers[155] = function() coffin(5) end   -- Trigger0 -> CoffinRaised3
handlers[205] = function() mummy(5) end   -- PetrifiedMummy0 wakes
handlers[225] = function() kick(5) end   -- PetrifiedMummy0 kicks free
handlers[156] = function() coffin(6) end   -- Trigger2 -> CoffinRaised15
handlers[206] = function() mummy(6) end   -- PetrifiedMummy2 wakes
handlers[226] = function() kick(6) end   -- PetrifiedMummy2 kicks free
handlers[157] = function() coffin(7) end   -- Trigger4 -> CoffinRaised4
handlers[207] = function() mummy(7) end   -- PetrifiedMummy4 wakes
handlers[227] = function() kick(7) end   -- PetrifiedMummy4 kicks free

-- The bottle (BottleFollow.scr): when the party arrives, the start's bottle bobs on the sewage six seconds,
-- then drifts along the channels (MarkerSW/NW/NE/SE) to the shaft of the Grand Entrance, on from the
-- MarkerLower path under the catacombs to Ludwig's manuscript, and starts again: it shows the way. The
-- other three are removed. The bottle is one looping model (scripts/bottle.py in the props project), which
-- the map spawns again on each load: Bottle says which, reset at load.
local BOTTLE_STARTS = {{-9830, 543, 655}, {-16425, 13102, 655}, {4465, 17567, 205}, {-1720, 2867, 410}}
local BOTTLE_CLIPS = {"sw", "nw", "ne", "se"}
local function startBottle(k)
    if var("Bottle") ~= 0 then return end
    set("Bottle", k)
    evt.SpawnWorldModel("engine/models/mm9_bottlefloat.glb", 0, 0, 0, 1, 0, BOTTLE_CLIPS[k])
end
handlers[170] = function() startBottle(1) end   -- TriggerBottleSW
handlers[171] = function() startBottle(2) end   -- TriggerBottleNW
handlers[172] = function() startBottle(3) end   -- TriggerBottleNE
handlers[173] = function() startBottle(4) end   -- TriggerBottleSE
handlers[1] = function()   -- map load
    for k = 0, 7 do
        -- a save taken while a coffin opened: its mummy is up and the coffin broken
        if var("Coffin" .. k) == 1 or var("Coffin" .. k) == 3 then kicked(k) end
        evt.SetSprite(310 + k, var("Coffin" .. k) ~= 2)
        evt.SetSprite(330 + k, var("Coffin" .. k) == 2)
    end
    set("Bottle", 0)
    local x, y, z = evt.GetPartyPosition()
    for k, p in ipairs(BOTTLE_STARTS) do
        if math.abs(x - p[1]) < 300 and math.abs(y - p[2]) < 300 and math.abs(z - p[3]) < 500 then startBottle(k) end
    end
end

-- MM9's BonePile objects (dungeon/objects.py): a click searches the pile (evt.SearchLootProp: its
-- TreasureLevel loot once, DiseaseChance; the pile stays).
handlers[30852] = function() evt.SearchLootProp("mm9:beethoven:object:852") end   -- BonePile0
handlers[30853] = function() evt.SearchLootProp("mm9:beethoven:object:853") end   -- BonePile1
handlers[30854] = function() evt.SearchLootProp("mm9:beethoven:object:854") end   -- BonePile2
handlers[30855] = function() evt.SearchLootProp("mm9:beethoven:object:855") end   -- Trashpile
handlers[30856] = function() evt.SearchLootProp("mm9:beethoven:object:856") end   -- Trashpile0
handlers[30857] = function() evt.SearchLootProp("mm9:beethoven:object:857") end   -- Trashpile1

-- MM9's bonus props (dungeon/objects.py bonus_lines; the use of each class, object.lto): wells, cauldrons,
-- cook pots and clovers.
handlers[31104] = function() MM9.useWell(1104, 2, 4, 5, 0, 4) end   -- WellMMIX0 (WellMMIX)

-- MM9's breaking destructibles: an urn's SpawnObject TreasureBag drops (evt.SpawnLootContainer).
handlers[31185] = function() evt.SpawnLootContainer("mm9:beethoven:object:1185") end   -- Urn0


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
RegisterEvent(113, "Door", handlers[113], "Door")
RegisterEvent(114, "Door", handlers[114], "Door")
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(44, "Chest", handlers[44], "Chest")
RegisterEvent(45, "Chest", handlers[45], "Chest")
RegisterEvent(46, "Chest", handlers[46], "Chest")
RegisterEvent(47, "Chest", handlers[47], "Chest")
RegisterEvent(48, "Chest", handlers[48], "Chest")
RegisterEvent(49, "Chest", handlers[49], "Chest")
RegisterEvent(50, "Chest", handlers[50], "Chest")
RegisterEvent(51, "Chest", handlers[51], "Chest")
RegisterEvent(91, "Lever", handlers[91], "Lever")
RegisterEvent(90, "Manuscript", handlers[90])
RegisterEvent(92, "Stone door", handlers[92], "Door")
RegisterEvent(93, "Stone door", handlers[93], "Door")
RegisterEvent(94, "Stone door", handlers[94], "Door")
RegisterEvent(150, "Trigger7", handlers[150])
RegisterMapTimerEvent(200, seconds(3), handlers[200], "PetrifiedMummy7 wakes", "", seconds(3))
RegisterMapTimerEvent(220, seconds(3), handlers[220], "PetrifiedMummy7 kicks free", "", seconds(3))
RegisterEvent(151, "Trigger6", handlers[151])
RegisterMapTimerEvent(201, seconds(3), handlers[201], "PetrifiedMummy6 wakes", "", seconds(3))
RegisterMapTimerEvent(221, seconds(3), handlers[221], "PetrifiedMummy6 kicks free", "", seconds(3))
RegisterEvent(152, "Trigger3", handlers[152])
RegisterMapTimerEvent(202, seconds(3), handlers[202], "PetrifiedMummy3 wakes", "", seconds(3))
RegisterMapTimerEvent(222, seconds(3), handlers[222], "PetrifiedMummy3 kicks free", "", seconds(3))
RegisterEvent(153, "Trigger5", handlers[153])
RegisterMapTimerEvent(203, seconds(3), handlers[203], "PetrifiedMummy5 wakes", "", seconds(3))
RegisterMapTimerEvent(223, seconds(3), handlers[223], "PetrifiedMummy5 kicks free", "", seconds(3))
RegisterEvent(154, "Trigger1", handlers[154])
RegisterMapTimerEvent(204, seconds(3), handlers[204], "PetrifiedMummy1 wakes", "", seconds(3))
RegisterMapTimerEvent(224, seconds(3), handlers[224], "PetrifiedMummy1 kicks free", "", seconds(3))
RegisterEvent(155, "Trigger0", handlers[155])
RegisterMapTimerEvent(205, seconds(3), handlers[205], "PetrifiedMummy0 wakes", "", seconds(3))
RegisterMapTimerEvent(225, seconds(3), handlers[225], "PetrifiedMummy0 kicks free", "", seconds(3))
RegisterEvent(156, "Trigger2", handlers[156])
RegisterMapTimerEvent(206, seconds(3), handlers[206], "PetrifiedMummy2 wakes", "", seconds(3))
RegisterMapTimerEvent(226, seconds(3), handlers[226], "PetrifiedMummy2 kicks free", "", seconds(3))
RegisterEvent(157, "Trigger4", handlers[157])
RegisterMapTimerEvent(207, seconds(3), handlers[207], "PetrifiedMummy4 wakes", "", seconds(3))
RegisterMapTimerEvent(227, seconds(3), handlers[227], "PetrifiedMummy4 kicks free", "", seconds(3))
RegisterEvent(170, "TriggerBottleSW", handlers[170])
RegisterEvent(171, "TriggerBottleNW", handlers[171])
RegisterEvent(172, "TriggerBottleNE", handlers[172])
RegisterEvent(173, "TriggerBottleSE", handlers[173])
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(30852, "Bone Pile", handlers[30852], "Bone Pile")
RegisterEvent(30853, "Bone Pile", handlers[30853], "Bone Pile")
RegisterEvent(30854, "Bone Pile", handlers[30854], "Bone Pile")
RegisterEvent(30855, "Trash Pile", handlers[30855], "Trash Pile")
RegisterEvent(30856, "Trash Pile", handlers[30856], "Trash Pile")
RegisterEvent(30857, "Trash Pile", handlers[30857], "Trash Pile")
RegisterEvent(31104, "Well", handlers[31104], "Drink")
RegisterEvent(31185, "Urn0", handlers[31185])
