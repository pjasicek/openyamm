-- Connecting Tunnels, MM9 rework (level_generation/projects/mm9r_connectingtunnels/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {coffin_door_left = 1, coffin_door_right = 2}
local function sound(name) evt.PlaySoundName(name, 0, 0, 0) end
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end
SetMapMetadata({onLoad = {}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}}})


-- Doors: each MM9 door group opens and closes on a click.

-- The coffin (RotatingDoor pair 'coffin door left/right', Sticky, PushOpen): a click swings both lids; opening
-- it unlocks TreasureChest1 inside (OpenTriggerTarget0 'unlock'), closing it locks it again (CloseTrigger0 'lock').
handlers[60] = function()
    evt.SetDoorState(1, DoorAction.Trigger) evt.SetDoorState(2, DoorAction.Trigger)
    set("CoffinOpen", 1 - var("CoffinOpen"))
end

-- The rock fall (DestructableBrush0, HitPoints 10, DeathTriggerTarget DestructableBrush1 'Destroy'): scene
-- destructibles; weapons (or a click) break DestructableBrush0, whose death breaks DestructableBrush1.
handlers[61] = function()
    set("RockFall", 1)
    evt.DestroyDestructible(669)
    evt.SpawnWorldEffect("mm9:smoke", -10517, -2446, -297, 2)
end

-- Chests (MM9 TreasureChest objects; loot records in the scene).
-- TreasureChest1 (Locked 1) lies in the coffin: it opens only while the coffin is open.
handlers[41] = function()
    if var("CoffinOpen") == 1 then evt.OpenChest(0) else sound("door/locked_door01.wav") evt.StatusText("The chest is locked.") end
end
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest0

-- MM9's BonePile objects (dungeon/objects.py): a click searches the pile (evt.SearchLootProp: its
-- TreasureLevel loot once, DiseaseChance; the pile stays).
handlers[30513] = function() evt.SearchLootProp("mm9:connectingtunnels:object:513") end   -- BonePile0
handlers[30514] = function() evt.SearchLootProp("mm9:connectingtunnels:object:514") end   -- BonePile1
handlers[30515] = function() evt.SearchLootProp("mm9:connectingtunnels:object:515") end   -- BonePile2
handlers[30516] = function() evt.SearchLootProp("mm9:connectingtunnels:object:516") end   -- BonePile3
handlers[30517] = function() evt.SearchLootProp("mm9:connectingtunnels:object:517") end   -- BonePile4
handlers[30518] = function() evt.SearchLootProp("mm9:connectingtunnels:object:518") end   -- BonePile5
handlers[30519] = function() evt.SearchLootProp("mm9:connectingtunnels:object:519") end   -- BonePile6
handlers[30520] = function() evt.SearchLootProp("mm9:connectingtunnels:object:520") end   -- BonePile7
handlers[30521] = function() evt.SearchLootProp("mm9:connectingtunnels:object:521") end   -- BonePile8

-- MM9's breakable brushes once built as click movers (destructibles.build_breakables): weapons break
-- them; a click still does, as a killing blow (refused while MM9's CanDamage is off).
handlers[38127] = function() evt.DamageDestructible(127, 1000000) end   -- DestructableBrush0


RegisterEvent(60, "Coffin", handlers[60], "Coffin")
RegisterEvent(61, "Rocks", handlers[61])
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(30513, "Bone Pile", handlers[30513], "Bone Pile")
RegisterEvent(30514, "Bone Pile", handlers[30514], "Bone Pile")
RegisterEvent(30515, "Bone Pile", handlers[30515], "Bone Pile")
RegisterEvent(30516, "Bone Pile", handlers[30516], "Bone Pile")
RegisterEvent(30517, "Bone Pile", handlers[30517], "Bone Pile")
RegisterEvent(30518, "Bone Pile", handlers[30518], "Bone Pile")
RegisterEvent(30519, "Bone Pile", handlers[30519], "Bone Pile")
RegisterEvent(30520, "Bone Pile", handlers[30520], "Bone Pile")
RegisterEvent(30521, "Bone Pile", handlers[30521], "Bone Pile")
RegisterEvent(38127, "DestructableBrush0", handlers[38127], "Rocks")
