-- Temple of the Light
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {},
    openedChestIds = {
    [176] = {1},
    [177] = {2},
    [178] = {3},
    [179] = {4},
    [180] = {5},
    [181] = {6},
    [182] = {7},
    [183] = {8},
    [184] = {9},
    [185] = {10},
    [186] = {11},
    [187] = {12},
    [188] = {13},
    [189] = {14},
    [190] = {15},
    [191] = {16},
    [192] = {17},
    [193] = {18},
    [194] = {19},
    [195] = {20},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        return
    elseif IsQBitSet(QBit(611)) then -- Chose the path of Light
        return
    else
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        return
    end
end)

RegisterEvent(3, "Legacy event 3", function()
    if not IsAtLeast(MapVar(5), 1) then
        AddValue(MapVar(5), 1)
        evt.SetDoorState(5, DoorAction.Close)
        return
    end
    SubtractValue(MapVar(5), 1)
    evt.SetDoorState(5, DoorAction.Open)
end)

RegisterEvent(4, "Legacy event 4", function()
    evt.SetDoorState(6, DoorAction.Trigger)
    SetValue(MapVar(2), 1)
end)

RegisterEvent(5, "Legacy event 5", function()
    if not IsAtLeast(MapVar(11), 1) then
        AddValue(MapVar(11), 1)
        evt.SetDoorState(7, DoorAction.Close)
        return
    end
    SubtractValue(MapVar(11), 1)
    evt.SetDoorState(7, DoorAction.Open)
end)

RegisterEvent(6, "Legacy event 6", function()
    evt.SetDoorState(8, DoorAction.Trigger)
    SetValue(MapVar(3), 1)
end)

RegisterEvent(7, "Legacy event 7", function()
    if not IsAtLeast(MapVar(7), 1) then
        evt.SetDoorState(9, DoorAction.Close)
        AddValue(MapVar(7), 1)
        return
    end
    SubtractValue(MapVar(7), 1)
    evt.SetDoorState(9, DoorAction.Open)
end)

RegisterEvent(8, "Legacy event 8", function()
    if not IsAtLeast(MapVar(8), 1) then
        evt.SetDoorState(10, DoorAction.Close)
        AddValue(MapVar(8), 1)
        return
    end
    SubtractValue(MapVar(8), 1)
    evt.SetDoorState(10, DoorAction.Open)
end)

RegisterEvent(9, "Legacy event 9", function()
    if not IsAtLeast(MapVar(9), 1) then
        evt.SetDoorState(11, DoorAction.Close)
        AddValue(MapVar(9), 1)
        return
    end
    SubtractValue(MapVar(9), 1)
    evt.SetDoorState(11, DoorAction.Open)
end)

RegisterEvent(10, "Legacy event 10", function()
    if not IsAtLeast(MapVar(10), 1) then
        evt.SetDoorState(12, DoorAction.Close)
        AddValue(MapVar(10), 1)
        return
    end
    SubtractValue(MapVar(10), 1)
    evt.SetDoorState(12, DoorAction.Open)
end)

RegisterEvent(11, "Legacy event 11", function()
    evt.SetDoorState(13, DoorAction.Trigger)
    SetValue(MapVar(4), 1)
end)

RegisterEvent(12, "Altar", function()
    if not IsAtLeast(MapVar(2), 1) then return end
    if not IsAtLeast(MapVar(3), 1) then return end
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(14, DoorAction.Trigger)
    end
end, "Altar")

RegisterEvent(13, "Door", function()
    evt.SetDoorState(15, DoorAction.Open)
end, "Door")

RegisterEvent(176, "Chest", function()
    local function Step_0()
        if IsQBitSet(QBit(611)) then return 6 end -- Chose the path of Light
        return 1
    end
    local function Step_1()
        if IsAtLeast(MapVar(6), 2) then return 7 end
        return 2
    end
    local function Step_2()
        SetValue(MapVar(6), 2)
        return 3
    end
    local function Step_3()
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        return 4
    end
    local function Step_4()
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        return 5
    end
    local function Step_5()
        return 7
    end
    local function Step_6()
        evt.SetChestBit(0, 1, 0)
        return 7
    end
    local function Step_7()
        evt.OpenChest(1)
        return 8
    end
    local function Step_8()
        SetQBit(QBit(744)) -- Altar Piece (Good) - I lost it
        return nil
    end
    local step = 0
    while step ~= nil do
        if step == 0 then
            step = Step_0()
        elseif step == 1 then
            step = Step_1()
        elseif step == 2 then
            step = Step_2()
        elseif step == 3 then
            step = Step_3()
        elseif step == 4 then
            step = Step_4()
        elseif step == 5 then
            step = Step_5()
        elseif step == 6 then
            step = Step_6()
        elseif step == 7 then
            step = Step_7()
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Chest")

RegisterEvent(177, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(2)
        return
    end
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(178, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(3)
        return
    end
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(179, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(4)
        return
    end
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(180, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(5)
        return
    end
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(181, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(6)
        return
    end
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(182, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(7)
        return
    end
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(183, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(8)
        return
    end
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(184, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(9)
        return
    end
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(185, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(10)
        return
    end
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(186, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(11)
        return
    end
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(187, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(12)
        return
    end
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(188, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(13)
        return
    end
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(189, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(14)
        return
    end
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(190, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(15)
        return
    end
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(191, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(16)
        return
    end
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(192, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(17)
        return
    end
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(193, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(18)
        return
    end
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(194, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(19)
        return
    end
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(195, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(20)
        return
    end
    evt.OpenChest(20)
end, "Chest")

RegisterEvent(451, "Legacy event 451", function()
    if IsAtLeast(MapVar(6), 1) then return end
    evt.SpeakNPC(614) -- Guard
    SetValue(MapVar(6), 1)
end)

RegisterEvent(452, "Legacy event 452", function()
    if IsAtLeast(MapVar(6), 2) then return end
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
    SetValue(MapVar(6), 2)
end)

RegisterEvent(453, "Legacy event 453", function()
    if IsAtLeast(MapVar(6), 2) then return end
    SetValue(MapVar(6), 0)
end)

RegisterEvent(454, "Legacy event 454", function()
    evt.SetDoorState(1, DoorAction.Open)
    evt.SetDoorState(2, DoorAction.Open)
    evt.SetDoorState(3, DoorAction.Open)
    evt.SetDoorState(4, DoorAction.Close)
end)

RegisterEvent(501, "Leave the Temple of Light", function()
    evt.MoveToMap(-5779, 15131, 225, 1536, 0, 0, 0, 0, "7d25.blv")
end, "Leave the Temple of Light")

