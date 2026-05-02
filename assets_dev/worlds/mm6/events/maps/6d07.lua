-- Silver Helm Outpost
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [16] = {1, 6},
    [17] = {2},
    [18] = {3},
    [48] = {4},
    [49] = {5},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Wooden Door", function()
    evt.SetDoorState(1, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(2, "Wooden Door", function()
    evt.SetDoorState(2, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(3, "Wooden Door", function()
    evt.SetDoorState(3, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(4, "Wooden Door", function()
    evt.SetDoorState(4, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(5, "Wooden Door", function()
    evt.SetDoorState(5, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(6, "Legacy event 6", function()
    evt.SetDoorState(6, DoorAction.Close)
end)

RegisterEvent(7, "Switch", function()
    evt.SetDoorState(7, DoorAction.Trigger)
    evt.SetDoorState(16, DoorAction.Trigger)
end, "Switch")

RegisterEvent(8, "Wooden Door", function()
    evt.SetDoorState(8, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(9, "Wooden Door", function()
    evt.SetDoorState(9, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(10, "Wooden Door", function()
    evt.SetDoorState(10, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(11, "Wooden Door", function()
    evt.SetDoorState(11, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(12, "Wooden Door", function()
    evt.SetDoorState(12, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(13, "Wooden Door", function()
    evt.SetDoorState(13, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(14, "Wooden Door", function()
    evt.SetDoorState(14, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(15, "Wooden Door", function()
    evt.SetDoorState(15, DoorAction.Close)
end, "Wooden Door")

RegisterEvent(16, "Chest", function()
    if not IsAtLeast(MapVar(6), 1) then
        if not IsQBitSet(QBit(1035)) then -- 11 D7, opens tomb in D18.
            evt.OpenChest(1)
            SetValue(MapVar(6), 1)
            SetQBit(QBit(1035)) -- 11 D7, opens tomb in D18.
            SetQBit(QBit(1223)) -- Quest item bits for seer
            return
        end
        evt.OpenChest(6)
    end
    evt.OpenChest(1)
    SetValue(MapVar(6), 1)
    SetQBit(QBit(1035)) -- 11 D7, opens tomb in D18.
    SetQBit(QBit(1223)) -- Quest item bits for seer
end, "Chest")

RegisterEvent(17, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(18, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(19, "Legacy event 19", function()
    evt.SetDoorState(6, DoorAction.Open)
    evt.SetDoorState(7, DoorAction.Open)
    evt.SetDoorState(16, DoorAction.Close)
end)

RegisterEvent(20, "Exit", function()
    evt.MoveToMap(8266, -16632, 480, 1024, 0, 0, 0, 0, "oute2.odm")
end, "Exit")

RegisterEvent(21, "Switch", function()
    evt.SetDoorState(21, DoorAction.Trigger)
    evt.SetDoorState(22, DoorAction.Trigger)
    evt.SetDoorState(23, DoorAction.Trigger)
    evt.SetDoorState(24, DoorAction.Close)
    evt.SetDoorState(25, DoorAction.Close)
    evt.SetDoorState(26, DoorAction.Close)
    evt.SetDoorState(27, DoorAction.Close)
    evt.SetDoorState(29, DoorAction.Close)
    evt.SetDoorState(30, DoorAction.Close)
    evt.SetDoorState(31, DoorAction.Close)
    evt.SetDoorState(32, DoorAction.Close)
    evt.SetDoorState(33, DoorAction.Close)
    evt.SetDoorState(34, DoorAction.Close)
    evt.SetDoorState(36, DoorAction.Close)
    evt.SetDoorState(37, DoorAction.Close)
    evt.SetDoorState(38, DoorAction.Close)
    evt.SetDoorState(39, DoorAction.Close)
    evt.SetDoorState(40, DoorAction.Close)
    evt.SetDoorState(41, DoorAction.Close)
    evt.SetDoorState(43, DoorAction.Open)
end, "Switch")

RegisterEvent(22, "Legacy event 22", function()
    evt.SetDoorState(24, DoorAction.Trigger)
end)

RegisterEvent(23, "Legacy event 23", function()
    evt.SetDoorState(25, DoorAction.Trigger)
end)

RegisterEvent(24, "Legacy event 24", function()
    evt.SetDoorState(23, DoorAction.Trigger)
    evt.SetDoorState(26, DoorAction.Trigger)
    evt.SetDoorState(21, DoorAction.Trigger)
    evt.SetDoorState(22, DoorAction.Trigger)
end)

RegisterEvent(25, "Legacy event 25", function()
    evt.SetDoorState(24, DoorAction.Trigger)
    evt.SetDoorState(27, DoorAction.Trigger)
end)

RegisterEvent(26, "Legacy event 26", function()
    evt.SetDoorState(25, DoorAction.Trigger)
end)

RegisterEvent(27, "Legacy event 27", function()
    evt.SetDoorState(26, DoorAction.Trigger)
end)

RegisterEvent(28, "Legacy event 28", function()
    evt.SetDoorState(29, DoorAction.Trigger)
    evt.SetDoorState(30, DoorAction.Trigger)
    evt.SetDoorState(27, DoorAction.Trigger)
end)

RegisterEvent(29, "Legacy event 29", function()
    evt.SetDoorState(31, DoorAction.Trigger)
    evt.SetDoorState(27, DoorAction.Close)
end)

RegisterEvent(30, "Legacy event 30", function()
    evt.SetDoorState(32, DoorAction.Trigger)
end)

RegisterEvent(31, "Legacy event 31", function()
    evt.SetDoorState(29, DoorAction.Trigger)
    evt.SetDoorState(30, DoorAction.Trigger)
    evt.SetDoorState(33, DoorAction.Trigger)
end)

RegisterEvent(32, "Legacy event 32", function()
    evt.SetDoorState(31, DoorAction.Trigger)
    evt.SetDoorState(34, DoorAction.Trigger)
end)

RegisterEvent(33, "Legacy event 33", function()
    evt.SetDoorState(32, DoorAction.Trigger)
end)

RegisterEvent(34, "Legacy event 34", function()
    evt.SetDoorState(33, DoorAction.Trigger)
end)

RegisterEvent(35, "Legacy event 35", function()
    evt.SetDoorState(34, DoorAction.Trigger)
    evt.SetDoorState(36, DoorAction.Trigger)
    evt.SetDoorState(37, DoorAction.Trigger)
end)

RegisterEvent(36, "Legacy event 36", function()
    evt.SetDoorState(38, DoorAction.Trigger)
    evt.SetDoorState(34, DoorAction.Close)
end)

RegisterEvent(37, "Legacy event 37", function()
    evt.SetDoorState(39, DoorAction.Trigger)
end)

RegisterEvent(38, "Legacy event 38", function()
    evt.SetDoorState(36, DoorAction.Trigger)
    evt.SetDoorState(37, DoorAction.Trigger)
    evt.SetDoorState(40, DoorAction.Trigger)
end)

RegisterEvent(39, "Legacy event 39", function()
    evt.SetDoorState(38, DoorAction.Trigger)
    evt.SetDoorState(41, DoorAction.Trigger)
end)

RegisterEvent(40, "Legacy event 40", function()
    evt.SetDoorState(39, DoorAction.Trigger)
end)

RegisterEvent(41, "Legacy event 41", function()
    evt.SetDoorState(40, DoorAction.Trigger)
end)

RegisterEvent(42, "Legacy event 42", function()
    evt.SetDoorState(41, DoorAction.Trigger)
    evt.SetDoorState(42, DoorAction.Trigger)
end)

RegisterEvent(43, "Legacy event 43", function()
    evt.SetDoorState(43, DoorAction.Close)
end)

RegisterEvent(44, "Legacy event 44", function()
    evt.SetDoorState(44, DoorAction.Close)
end)

RegisterEvent(45, "Legacy event 45", function()
    evt.SetDoorState(45, DoorAction.Close)
end)

RegisterEvent(46, "Legacy event 46", function()
    evt.SetDoorState(21, DoorAction.Close)
    evt.SetDoorState(22, DoorAction.Close)
    evt.SetDoorState(23, DoorAction.Close)
    evt.SetDoorState(24, DoorAction.Close)
    evt.SetDoorState(25, DoorAction.Close)
    evt.SetDoorState(26, DoorAction.Close)
    evt.SetDoorState(27, DoorAction.Close)
    evt.SetDoorState(29, DoorAction.Close)
    evt.SetDoorState(30, DoorAction.Close)
    evt.SetDoorState(31, DoorAction.Close)
    evt.SetDoorState(32, DoorAction.Close)
    evt.SetDoorState(33, DoorAction.Close)
    evt.SetDoorState(34, DoorAction.Close)
    evt.SetDoorState(36, DoorAction.Close)
    evt.SetDoorState(37, DoorAction.Close)
    evt.SetDoorState(38, DoorAction.Close)
    evt.SetDoorState(39, DoorAction.Close)
    evt.SetDoorState(40, DoorAction.Close)
    evt.SetDoorState(41, DoorAction.Close)
    evt.SetDoorState(42, DoorAction.Open)
end)

RegisterEvent(47, "Mural", function()
    if not IsAtLeast(MapVar(3), 3) then
        evt.MoveToMap(7, 3107, 1, 0, 0, 0, 0, 0)
        evt.SummonMonsters(1, 2, 2, 4, 2120, 1, 0, 0) -- encounter slot 1 "Nobleman" tier B, count 2, pos=(4, 2120, 1), actor group 0, no unique actor name
        evt.SummonMonsters(3, 1, 3, 1630, 3072, 350, 0, 0) -- encounter slot 3 "Guard" tier A, count 3, pos=(1630, 3072, 350), actor group 0, no unique actor name
        AddValue(MapVar(3), 1)
        return
    end
    evt.MoveToMap(7, 3107, 1, 0, 0, 0, 0, 0)
end, "Mural")

RegisterEvent(48, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(49, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(50, "Mural", function()
    if IsAtLeast(MapVar(4), 3) then return end
    evt.MoveToMap(-1635, 5470, 257, 0, 0, 0, 0, 0)
    evt.SummonMonsters(3, 1, 2, -1418, 4986, 257, 0, 0) -- encounter slot 3 "Guard" tier A, count 2, pos=(-1418, 4986, 257), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, -1418, 4811, 257, 0, 0) -- encounter slot 3 "Guard" tier B, count 1, pos=(-1418, 4811, 257), actor group 0, no unique actor name
    evt.SetDoorState(44, DoorAction.Open)
    evt.SetDoorState(45, DoorAction.Open)
    AddValue(MapVar(4), 1)
end, "Mural")

RegisterEvent(51, "Legacy event 51", function()
    evt.SetDoorState(43, DoorAction.Close)
    evt.SummonMonsters(1, 1, 4, 10, 2120, 1, 0, 0) -- encounter slot 1 "Nobleman" tier A, count 4, pos=(10, 2120, 1), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 2, 1630, 3072, 350, 0, 0) -- encounter slot 3 "Guard" tier B, count 2, pos=(1630, 3072, 350), actor group 0, no unique actor name
end)

RegisterEvent(55, "Legacy event 55", function()
    if IsQBitSet(QBit(1196)) then return end -- NPC
    SetQBit(QBit(1196)) -- NPC
    evt.SpeakNPC(859) -- Oliver Wendell
end)

RegisterEvent(56, "Legacy event 56", function()
    if IsQBitSet(QBit(1195)) then return end -- NPC
    SetQBit(QBit(1699)) -- Replacement for NPCs ¹11 ver. 6
    SetQBit(QBit(1195)) -- NPC
    evt.SpeakNPC(796) -- Melody Silver
end)

RegisterEvent(57, "Legacy event 57", function()
    if IsAtLeast(MapVar(11), 1) then return end
    SetValue(MapVar(11), 1)
    AddValue(InventoryItem(1935), 1935) -- Recharge Item
end)

