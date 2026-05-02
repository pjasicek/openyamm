-- Warlord's Fortress
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {48},
    onLeave = {},
    openedChestIds = {
    [25] = {0},
    [26] = {1},
    [27] = {2},
    [28] = {3},
    [29] = {4},
    [30] = {5},
    [31] = {6},
    [32] = {7},
    [33] = {8},
    [34] = {9},
    [35] = {10},
    [36] = {11, 0},
    [37] = {12},
    [38] = {13},
    [39] = {14},
    [40] = {15},
    [41] = {16},
    [42] = {17},
    [43] = {18},
    [44] = {19},
    },
    textureNames = {"d8s2on"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    evt.SetDoorState(1, DoorAction.Close)
end)

RegisterEvent(2, "Door", function()
    evt.SetDoorState(2, DoorAction.Close)
end, "Door")

RegisterEvent(3, "Door", function()
    evt.SetDoorState(3, DoorAction.Close)
end, "Door")

RegisterEvent(4, "Legacy event 4", function()
    evt.SetDoorState(4, DoorAction.Close)
end)

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Close)
end, "Door")

RegisterEvent(6, "Door", function()
    if not HasItem(2185) then -- Storage Key
        evt.StatusText("The door is double locked.")
        return
    end
    if not HasItem(2191) then -- Storage Key
        evt.StatusText("The door is double locked.")
        return
    end
    if not IsAtLeast(MapVar(11), 10) then
        SetValue(MapVar(11), 10)
        evt.SetDoorState(6, DoorAction.Close)
        return
    end
    RemoveItem(2185) -- Storage Key
    RemoveItem(2191) -- Storage Key
    evt.SetDoorState(6, DoorAction.Close)
end, "Door")

RegisterEvent(7, "Door", function()
    if not HasItem(2185) then -- Storage Key
        evt.StatusText("The door is double locked.")
        return
    end
    if not HasItem(2191) then -- Storage Key
        evt.StatusText("The door is double locked.")
        return
    end
    if not IsAtLeast(MapVar(11), 10) then
        SetValue(MapVar(11), 10)
        evt.SetDoorState(7, DoorAction.Close)
        return
    end
    RemoveItem(2185) -- Storage Key
    RemoveItem(2191) -- Storage Key
    evt.SetDoorState(7, DoorAction.Close)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(8, DoorAction.Close)
end, "Door")

RegisterEvent(9, "Door", function()
    if not HasItem(2184) then -- Warlord's Key
        evt.StatusText("The door is locked.")
        return
    end
    evt.SetDoorState(9, DoorAction.Close)
    RemoveItem(2184) -- Warlord's Key
end, "Door")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(10, DoorAction.Close)
end, "Door")

RegisterEvent(11, "Legacy event 11", function()
    evt.SetDoorState(11, DoorAction.Close)
end)

RegisterEvent(12, "Door", function()
    evt.SetDoorState(12, DoorAction.Close)
end, "Door")

RegisterEvent(13, "Door", function()
    evt.SetDoorState(13, DoorAction.Close)
end, "Door")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(14, DoorAction.Close)
end, "Door")

RegisterEvent(15, "Door", function()
    evt.SetDoorState(15, DoorAction.Close)
end, "Door")

RegisterEvent(16, "Door", function()
    evt.SetDoorState(16, DoorAction.Close)
end, "Door")

RegisterEvent(17, "Legacy event 17", function()
    evt.SetDoorState(17, DoorAction.Close)
end)

RegisterEvent(18, "Door", function()
    evt.SetDoorState(18, DoorAction.Close)
end, "Door")

RegisterEvent(19, "Switch", function()
    evt.SetTexture(960, "d8s2on")
    evt.SetDoorState(19, DoorAction.Close)
    SetValue(MapVar(21), 1)
end, "Switch")

RegisterEvent(20, "Door", function()
    local randomStep = PickRandomOption(20, 1, {3, 5, 7, 9})
    if randomStep == 3 then
        evt.MoveToMap(-2539, -512, -255, 1024, 0, 0, 0, 0)
    elseif randomStep == 5 then
        evt.MoveToMap(-1537, -788, -255, 512, 0, 0, 0, 0)
    elseif randomStep == 7 then
        evt.MoveToMap(-1012, -1284, -255, 1024, 0, 0, 0, 0)
    elseif randomStep == 9 then
        evt.MoveToMap(-1036, -1775, -255, 1536, 0, 0, 0, 0)
    end
    evt.StatusText("You are pulled through the door!")
end, "Door")

RegisterEvent(21, "Door", function()
    local randomStep = PickRandomOption(21, 1, {1, 5, 7, 9})
    if randomStep == 1 then
        evt.MoveToMap(-3586, -789, -255, 512, 0, 0, 0, 0)
    elseif randomStep == 5 then
        evt.MoveToMap(-1537, -788, -255, 512, 0, 0, 0, 0)
    elseif randomStep == 7 then
        evt.MoveToMap(-1012, -1284, -255, 1024, 0, 0, 0, 0)
    elseif randomStep == 9 then
        evt.MoveToMap(-1036, -1775, -255, 1536, 0, 0, 0, 0)
    end
    evt.StatusText("You are pulled through the door!")
end, "Door")

RegisterEvent(22, "Door", function()
    local randomStep = PickRandomOption(22, 1, {1, 3, 7, 9})
    if randomStep == 1 then
        evt.MoveToMap(-3586, -789, -255, 512, 0, 0, 0, 0)
    elseif randomStep == 3 then
        evt.MoveToMap(-2539, -512, -255, 1024, 0, 0, 0, 0)
    elseif randomStep == 7 then
        evt.MoveToMap(-1012, -1284, -255, 1024, 0, 0, 0, 0)
    elseif randomStep == 9 then
        evt.MoveToMap(-1036, -1775, -255, 1536, 0, 0, 0, 0)
    end
    evt.StatusText("You are pulled through the door!")
end, "Door")

RegisterEvent(23, "Door", function()
    local randomStep = PickRandomOption(23, 1, {1, 3, 5, 9})
    if randomStep == 1 then
        evt.MoveToMap(-3586, -789, -255, 512, 0, 0, 0, 0)
    elseif randomStep == 3 then
        evt.MoveToMap(-2539, -512, -255, 1024, 0, 0, 0, 0)
    elseif randomStep == 5 then
        evt.MoveToMap(-1537, -788, -255, 512, 0, 0, 0, 0)
    elseif randomStep == 9 then
        evt.MoveToMap(-1036, -1775, -255, 1536, 0, 0, 0, 0)
    end
    evt.StatusText("You are pulled through the door!")
end, "Door")

RegisterEvent(24, "Door", function()
    local randomStep = PickRandomOption(24, 1, {1, 3, 5, 7})
    if randomStep == 1 then
        evt.MoveToMap(-3586, -789, -255, 512, 0, 0, 0, 0)
    elseif randomStep == 3 then
        evt.MoveToMap(-2539, -512, -255, 1024, 0, 0, 0, 0)
    elseif randomStep == 5 then
        evt.MoveToMap(-1537, -788, -255, 512, 0, 0, 0, 0)
    elseif randomStep == 7 then
        evt.MoveToMap(-1012, -1284, -255, 1024, 0, 0, 0, 0)
    end
    evt.StatusText("You are pulled through the door!")
end, "Door")

RegisterEvent(25, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(26, "Cabinet", function()
    evt.OpenChest(1)
end, "Cabinet")

RegisterEvent(27, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(28, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(29, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(30, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(31, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(32, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(33, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(34, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(35, "Cabinet", function()
    evt.OpenChest(10)
end, "Cabinet")

RegisterEvent(36, "Chest", function()
    if not IsQBitSet(QBit(1076)) then -- 52 D16, Given when characters find the Eagle Statuette
        evt.OpenChest(11)
        SetQBit(QBit(1076)) -- 52 D16, Given when characters find the Eagle Statuette
        SetQBit(QBit(1211)) -- Quest item bits for seer
        SetValue(MapVar(22), 1)
        return
    end
    if not IsAtLeast(MapVar(22), 1) then
        evt.OpenChest(0)
    end
    evt.OpenChest(11)
    SetQBit(QBit(1076)) -- 52 D16, Given when characters find the Eagle Statuette
    SetQBit(QBit(1211)) -- Quest item bits for seer
    SetValue(MapVar(22), 1)
end, "Chest")

RegisterEvent(37, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(38, "Cabinet", function()
    evt.OpenChest(13)
end, "Cabinet")

RegisterEvent(39, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(40, "Chest", function()
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(41, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(42, "Cabinet", function()
    evt.OpenChest(17)
end, "Cabinet")

RegisterEvent(43, "Cabinet", function()
    evt.OpenChest(18)
end, "Cabinet")

RegisterEvent(44, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(45, "Chest of Drawers", function()
    if IsAtLeast(MapVar(2), 1) then return end
    evt.StatusText("You have found two keys!")
    AddValue(InventoryItem(2184), 2184) -- Warlord's Key
    AddValue(InventoryItem(2185), 2185) -- Storage Key
    SetValue(MapVar(2), 1)
end, "Chest of Drawers")

RegisterEvent(46, "Chest of Drawers", function()
    if IsAtLeast(MapVar(3), 1) then return end
    evt.StatusText("You have found a key!")
    AddValue(InventoryItem(2191), 2191) -- Storage Key
    SetValue(MapVar(3), 1)
end, "Chest of Drawers")

RegisterEvent(47, "Door", function()
    evt.StatusText("This door won't open.")
end, "Door")

RegisterEvent(48, "Legacy event 48", function()
    if IsAtLeast(MapVar(21), 1) then
        evt.SetTexture(960, "d8s2on")
    end
end)

RegisterEvent(50, "Exit", function()
    evt.MoveToMap(-18606, 9831, 160, 1536, 0, 0, 0, 0, "outd1.odm")
end, "Exit")

RegisterEvent(51, "Legacy event 51", function()
    if IsAtLeast(MapVar(51), 1) then return end
    SetValue(MapVar(51), 1)
    evt.GiveItem(6, 25)
end)

