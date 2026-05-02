-- Corlagon's Estate
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [42] = {1},
    [43] = {2},
    [44] = {3},
    [45] = {4},
    [46] = {5},
    [47] = {6},
    [48] = {7},
    [49] = {8},
    [50] = {9, 8},
    [51] = {10},
    [75] = {0},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Door", function()
    evt.SetDoorState(1, DoorAction.Close)
end, "Door")

RegisterEvent(2, "Door", function()
    evt.SetDoorState(2, DoorAction.Close)
end, "Door")

RegisterEvent(3, "Door", function()
    evt.SetDoorState(3, DoorAction.Close)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Close)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(6, DoorAction.Close)
end, "Door")

RegisterEvent(7, "Legacy event 7", function()
    evt.SetDoorState(7, DoorAction.Close)
end)

RegisterEvent(8, "Door", function()
    evt.SetDoorState(8, DoorAction.Close)
end, "Door")

RegisterEvent(9, "Door", function()
    evt.SetDoorState(9, DoorAction.Close)
    SetValue(MapVar(3), 1)
end, "Door")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(10, DoorAction.Close)
end, "Door")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(11, DoorAction.Close)
end, "Door")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(12, DoorAction.Close)
end, "Door")

RegisterEvent(14, "Switch", function()
    evt.SetDoorState(14, DoorAction.Trigger)
    evt.SetDoorState(15, DoorAction.Trigger)
end, "Switch")

RegisterEvent(16, "Switch", function()
    evt.SetDoorState(16, DoorAction.Trigger)
    evt.SetDoorState(4, DoorAction.Trigger)
end, "Switch")

RegisterEvent(17, "Door", function()
    evt.SetDoorState(17, DoorAction.Close)
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(18, DoorAction.Close)
end, "Door")

RegisterEvent(19, "Door", function()
    evt.SetDoorState(19, DoorAction.Close)
end, "Door")

RegisterEvent(20, "Switch", function()
    evt.SetDoorState(20, DoorAction.Trigger)
    evt.SetDoorState(13, DoorAction.Trigger)
end, "Switch")

RegisterEvent(21, "Door", function()
    evt.SetDoorState(21, DoorAction.Close)
end, "Door")

RegisterEvent(22, "Door", function()
    evt.SetDoorState(22, DoorAction.Close)
end, "Door")

RegisterEvent(23, "Wall", function()
    evt.SetDoorState(23, DoorAction.Close)
end, "Wall")

RegisterEvent(24, "Legacy event 24", function()
    evt.SetDoorState(24, DoorAction.Close)
end)

RegisterEvent(25, "Wall", function()
    evt.SetDoorState(25, DoorAction.Close)
end, "Wall")

RegisterEvent(26, "Switch", function()
    evt.SetDoorState(26, DoorAction.Trigger)
    evt.SetDoorState(27, DoorAction.Trigger)
end, "Switch")

RegisterEvent(28, "Door", function()
    evt.SetDoorState(28, DoorAction.Close)
end, "Door")

RegisterEvent(29, "Door", function()
    evt.SetDoorState(29, DoorAction.Close)
end, "Door")

RegisterEvent(30, "Door", function()
    evt.SetDoorState(30, DoorAction.Close)
end, "Door")

RegisterEvent(31, "Door", function()
    evt.SetDoorState(31, DoorAction.Close)
end, "Door")

RegisterEvent(32, "Door", function()
    evt.SetDoorState(32, DoorAction.Close)
end, "Door")

RegisterEvent(33, "Door", function()
    evt.SetDoorState(33, DoorAction.Close)
end, "Door")

RegisterEvent(34, "Door", function()
    evt.SetDoorState(34, DoorAction.Close)
end, "Door")

RegisterEvent(35, "Door", function()
    evt.SetDoorState(35, DoorAction.Close)
end, "Door")

RegisterEvent(42, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(43, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(44, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(45, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(46, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(47, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(48, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(49, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(50, "Chest", function()
    if not IsAtLeast(MapVar(2), 1) then
        if not IsQBitSet(QBit(1026)) then -- 2 D11, given for glass shard for staff of terrax quest
            evt.OpenChest(9)
            SetValue(MapVar(2), 1)
            SetQBit(QBit(1026)) -- 2 D11, given for glass shard for staff of terrax quest
            SetQBit(QBit(1210)) -- Quest item bits for seer
            return
        end
        evt.OpenChest(8)
    end
    evt.OpenChest(9)
    SetValue(MapVar(2), 1)
    SetQBit(QBit(1026)) -- 2 D11, given for glass shard for staff of terrax quest
    SetQBit(QBit(1210)) -- Quest item bits for seer
end, "Chest")

RegisterEvent(51, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(52, "Door", nil, "Door")

RegisterEvent(53, "Door", function()
    evt.StatusText("This Door won't budge.")
end, "Door")

RegisterEvent(60, "Exit", function()
    evt.MoveToMap(-19677, -17439, 96, 0, 0, 0, 0, 0, "outd3.odm")
end, "Exit")

RegisterEvent(65, "Legacy event 65", function()
    evt.MoveToMap(-5768, 656, -1296, 1536, 0, 0, 0, 0)
end)

RegisterEvent(66, "Legacy event 66", function()
    evt.MoveToMap(-6416, 7560, -1296, 512, 0, 0, 0, 0)
end)

RegisterEvent(69, "Legacy event 69", function()
    evt.MoveToMap(6538, 114, -255, 1536, 0, 0, 0, 0)
end)

RegisterEvent(70, "Legacy event 70", function()
    evt.MoveToMap(6537, 5945, -255, 512, 0, 0, 0, 0)
end)

RegisterEvent(71, "Legacy event 71", function()
    if IsAtLeast(MapVar(3), 1) then
        evt.MoveToMap(3584, -5248, -832, 512, 0, 0, 0, 0)
        SubtractValue(MapVar(3), 1)
        evt.SummonMonsters(1, 1, 1, 1408, -4992, -832, 0, 0) -- encounter slot 1 "BGhost" tier A, count 1, pos=(1408, -4992, -832), actor group 0, no unique actor name
        evt.SummonMonsters(1, 2, 1, 1408, -4864, -832, 0, 0) -- encounter slot 1 "BGhost" tier B, count 1, pos=(1408, -4864, -832), actor group 0, no unique actor name
        evt.SummonMonsters(1, 3, 1, 1408, -4736, -832, 0, 0) -- encounter slot 1 "BGhost" tier C, count 1, pos=(1408, -4736, -832), actor group 0, no unique actor name
    end
end)

RegisterEvent(75, "Legacy event 75", function()
    evt.OpenChest(0)
end)

