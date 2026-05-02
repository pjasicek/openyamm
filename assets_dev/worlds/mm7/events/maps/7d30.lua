-- Castle Lambent
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 377},
    onLeave = {},
    openedChestIds = {
    [176] = {1},
    [177] = {2},
    [178] = {3},
    [179] = {4},
    [180] = {5},
    [181] = {6},
    [182] = {19, 7},
    [183] = {0, 8},
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
    },
    textureNames = {"cwb"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(611)) then -- Chose the path of Light
        if IsQBitSet(QBit(782)) then -- Your friends are mad at you
            if IsAtLeast(Counter(10), 720) then
                ClearQBit(QBit(782)) -- Your friends are mad at you
                SetValue(MapVar(6), 0)
                evt.SetMonGroupBit(56, MonsterBits.Hostile, 0)
                evt.SetMonGroupBit(55, MonsterBits.Hostile, 0)
            end
            SetValue(MapVar(6), 2)
            evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
            evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
            return
        elseif IsAtLeast(MapVar(6), 2) then
            evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
            evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
            return
        else
            return
        end
    end
    SetValue(MapVar(6), 2)
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
end)

RegisterEvent(3, "Legacy event 3", function()
    evt.SetDoorState(3, DoorAction.Open)
end)

RegisterEvent(4, "Legacy event 4", function()
    evt.SetDoorState(4, DoorAction.Open)
end)

RegisterEvent(5, "Legacy event 5", function()
    evt.SetDoorState(5, DoorAction.Open)
end)

RegisterEvent(6, "Legacy event 6", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.SetDoorState(6, DoorAction.Trigger)
        evt.SetDoorState(7, DoorAction.Trigger)
        evt.SetFacetBit(1, FacetBits.Invisible, 1)
        evt.SetFacetBit(1, FacetBits.Untouchable, 1)
        evt.SetDoorState(12, DoorAction.Open)
        evt.SetDoorState(13, DoorAction.Open)
        SetValue(MapVar(2), 1)
        return
    end
    evt.SetDoorState(6, DoorAction.Trigger)
    evt.SetDoorState(7, DoorAction.Trigger)
    evt.SetFacetBit(1, FacetBits.Invisible, 0)
    evt.SetFacetBit(1, FacetBits.Untouchable, 0)
    SetValue(MapVar(2), 0)
end)

RegisterEvent(7, "Legacy event 7", function()
    evt.SetDoorState(8, DoorAction.Trigger)
end)

RegisterEvent(8, "Legacy event 8", function()
    evt.SetDoorState(9, DoorAction.Trigger)
end)

RegisterEvent(9, "Door", function()
    evt.SetDoorState(10, DoorAction.Trigger)
    evt.SetDoorState(11, DoorAction.Trigger)
end, "Door")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(2, DoorAction.Open)
end, "Door")

RegisterEvent(11, "Legacy event 11", function()
    evt.SetDoorState(14, DoorAction.Trigger)
    if IsAtLeast(MapVar(2), 1) then return end
    evt.SetDoorState(12, DoorAction.Trigger)
    evt.SetDoorState(13, DoorAction.Trigger)
end)

RegisterEvent(12, "Door", function()
    evt.SetDoorState(1, DoorAction.Open)
end, "Door")

RegisterEvent(176, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.OpenChest(1)
        return
    end
    evt.OpenChest(1)
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
        return 8
    end
    local function Step_6()
        if IsQBitSet(QBit(642)) then return 10 end -- Go to the Lincoln in the sea west of Avlee and retrieve the Oscillation Overthruster and return it to Resurectra in Celeste.
        return 7
    end
    local function Step_7()
        evt.SetChestBit(19, 1, 0)
        return 8
    end
    local function Step_8()
        evt.OpenChest(19)
        return 9
    end
    local function Step_9()
        return nil
    end
    local function Step_10()
        evt.SetChestBit(7, 1, 0)
        return 11
    end
    local function Step_11()
        evt.OpenChest(7)
        return 12
    end
    local function Step_12()
        SetQBit(QBit(747)) -- Wetsuit - I lost it
        return 13
    end
    local function Step_13()
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
        elseif step == 9 then
            step = Step_9()
        elseif step == 10 then
            step = Step_10()
        elseif step == 11 then
            step = Step_11()
        elseif step == 12 then
            step = Step_12()
        elseif step == 13 then
            step = Step_13()
        else
            step = nil
        end
    end
end, "Chest")

RegisterEvent(183, "Chest", function()
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
        return 8
    end
    local function Step_6()
        if IsQBitSet(QBit(642)) then return 10 end -- Go to the Lincoln in the sea west of Avlee and retrieve the Oscillation Overthruster and return it to Resurectra in Celeste.
        return 7
    end
    local function Step_7()
        evt.SetChestBit(0, 1, 0)
        return 8
    end
    local function Step_8()
        evt.OpenChest(0)
        return 9
    end
    local function Step_9()
        return nil
    end
    local function Step_10()
        evt.SetChestBit(8, 1, 0)
        return 11
    end
    local function Step_11()
        evt.OpenChest(8)
        return 12
    end
    local function Step_12()
        SetQBit(QBit(747)) -- Wetsuit - I lost it
        return 13
    end
    local function Step_13()
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
        elseif step == 9 then
            step = Step_9()
        elseif step == 10 then
            step = Step_10()
        elseif step == 11 then
            step = Step_11()
        elseif step == 12 then
            step = Step_12()
        elseif step == 13 then
            step = Step_13()
        else
            step = nil
        end
    end
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

RegisterEvent(376, "Legacy event 376", function()
    if IsQBitSet(QBit(711)) then return end -- Take the Associate's Tapestry
    if IsQBitSet(QBit(611)) and IsQBitSet(QBit(694)) then -- Chose the path of Light
        evt.SetTexture(10, "cwb")
        AddValue(InventoryItem(1422), 1422) -- Big Tapestry
        SetQBit(QBit(711)) -- Take the Associate's Tapestry
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        SetValue(MapVar(6), 2)
    else
    end
end)

RegisterEvent(377, "Legacy event 377", function()
    if IsQBitSet(QBit(711)) then -- Take the Associate's Tapestry
        evt.SetTexture(15, "cwb")
    end
end)

RegisterEvent(416, "Enter the Throne Room", function()
    if not IsAtLeast(MapVar(6), 2) then
        evt.EnterHouse(220) -- Throne Room
        return
    end
    evt.StatusText("The Door is Locked")
end, "Enter the Throne Room")

RegisterEvent(451, "Legacy event 451", function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 1) then return end
    evt.SpeakNPC(618) -- Castle Guard
    SetValue(MapVar(6), 1)
end)

RegisterEvent(452, "Legacy event 452", function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 2) then return end
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
    SetValue(MapVar(6), 2)
    SetValue(Counter(10), 0)
    SetQBit(QBit(782)) -- Your friends are mad at you
end)

RegisterEvent(453, "Legacy event 453", function()
    if IsAtLeast(MapVar(6), 2) then return end
    SetValue(MapVar(6), 0)
end)

RegisterEvent(501, "Leave Castle Lambent", function()
    evt.MoveToMap(-1264, 19718, 225, 1536, 0, 0, 0, 0, "7d25.blv")
end, "Leave Castle Lambent")

