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
    contextActions = {
    [3] = { kind = "open_door", source = "opcode" },
    [4] = { kind = "open_door", source = "opcode" },
    [5] = { kind = "open_door", source = "opcode" },
    [6] = { kind = "open_door", source = "opcode" },
    [7] = { kind = "open_door", source = "opcode" },
    [8] = { kind = "open_door", source = "opcode" },
    [9] = { kind = "open_door", source = "title" },
    [10] = { kind = "open_door", source = "title" },
    [11] = { kind = "open_door", source = "opcode" },
    [12] = { kind = "open_door", source = "title" },
    [176] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [177] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [178] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [179] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [180] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [181] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [182] = { kind = "open_chest", source = "opcode", chestIds = {7, 19} },
    [183] = { kind = "open_chest", source = "opcode", chestIds = {0, 8} },
    [184] = { kind = "open_chest", source = "opcode", chestIds = {9} },
    [185] = { kind = "open_chest", source = "opcode", chestIds = {10} },
    [186] = { kind = "open_chest", source = "opcode", chestIds = {11} },
    [187] = { kind = "open_chest", source = "opcode", chestIds = {12} },
    [188] = { kind = "open_chest", source = "opcode", chestIds = {13} },
    [189] = { kind = "open_chest", source = "opcode", chestIds = {14} },
    [190] = { kind = "open_chest", source = "opcode", chestIds = {15} },
    [191] = { kind = "open_chest", source = "opcode", chestIds = {16} },
    [192] = { kind = "open_chest", source = "opcode", chestIds = {17} },
    [193] = { kind = "open_chest", source = "opcode", chestIds = {18} },
    [416] = { kind = "enter_house", source = "opcode", houseId = 220, targetName = "Throne Room" },
    [501] = { kind = "passage", source = "opcode", targetMap = "7d25.blv", targetName = "Celeste" },
    },
    textureNames = {"cwb"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    if IsQBitSet(QBit(611)) then -- Chose the path of Light
        if IsQBitSet(QBit(782)) then -- Your friends are mad at you
            if IsAtLeast(Counter(10), 720) then
                ClearQBit(QBit(782)) -- Your friends are mad at you
                SetValue(MapVar(6), 0)
                evt.SetMonGroupBit(56, MonsterBits.Hostile, 0) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
                evt.SetMonGroupBit(55, MonsterBits.Hostile, 0) -- actor group 55: Wizard
                return
            end
            SetValue(MapVar(6), 2)
            evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
            evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
            return
        elseif IsAtLeast(MapVar(6), 2) then
            evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
            evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
            return
        else
            return
        end
        return
    end
    SetValue(MapVar(6), 2)
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
    evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
end)

RegisterEvent(3, nil, function()
    evt.SetDoorState(3, DoorAction.Open)
end)

RegisterEvent(4, nil, function()
    evt.SetDoorState(4, DoorAction.Open)
end)

RegisterEvent(5, nil, function()
    evt.SetDoorState(5, DoorAction.Open)
end)

RegisterEvent(6, nil, function()
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

RegisterEvent(7, nil, function()
    evt.SetDoorState(8, DoorAction.Trigger)
end)

RegisterEvent(8, nil, function()
    evt.SetDoorState(9, DoorAction.Trigger)
end)

RegisterEvent(9, "Door", function()
    evt.SetDoorState(10, DoorAction.Trigger)
    evt.SetDoorState(11, DoorAction.Trigger)
end, "Door")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(2, DoorAction.Open)
end, "Door")

RegisterEvent(11, nil, function()
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
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
        evt.OpenChest(1)
        return
    end
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(177, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
        evt.OpenChest(2)
        return
    end
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(178, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
        evt.OpenChest(3)
        return
    end
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(179, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
        evt.OpenChest(4)
        return
    end
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(180, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
        evt.OpenChest(5)
        return
    end
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(181, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
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
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        return 4
    end
    local function Step_4()
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
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
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        return 4
    end
    local function Step_4()
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
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
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
        evt.OpenChest(9)
        return
    end
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(185, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
        evt.OpenChest(10)
        return
    end
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(186, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
        evt.OpenChest(11)
        return
    end
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(187, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
        evt.OpenChest(12)
        return
    end
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(188, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
        evt.OpenChest(13)
        return
    end
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(189, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
        evt.OpenChest(14)
        return
    end
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(190, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
        evt.OpenChest(15)
        return
    end
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(191, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
        evt.OpenChest(16)
        return
    end
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(192, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
        evt.OpenChest(17)
        return
    end
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(193, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
        evt.OpenChest(18)
        return
    end
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(376, nil, function()
    if IsQBitSet(QBit(711)) then return end -- Take the Associate's Tapestry
    if IsQBitSet(QBit(611)) and IsQBitSet(QBit(694)) then -- Chose the path of Light
        evt.SetTexture(10, "cwb")
        AddValue(InventoryItem(1422), 1422) -- Big Tapestry
        SetQBit(QBit(711)) -- Take the Associate's Tapestry
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
        SetValue(MapVar(6), 2)
    else
    end
end)

RegisterEvent(377, nil, function()
    if IsQBitSet(QBit(711)) then -- Take the Associate's Tapestry
        evt.SetTexture(15, "cwb")
    end
end)

RegisterEvent(416, "Throne Room", function()
    if not IsAtLeast(MapVar(6), 2) then
        evt.EnterHouse(220) -- Throne Room
        return
    end
    evt.StatusText("The Door is Locked")
end, "Throne Room")

RegisterEvent(451, nil, function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 1) then return end
    evt.SpeakNPC(618) -- Castle Guard
    SetValue(MapVar(6), 1)
end)

RegisterEvent(452, nil, function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 2) then return end
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Angel A, spawn Golem A, spawn Mage A
    evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Wizard
    SetValue(MapVar(6), 2)
    SetValue(Counter(10), 0)
    SetQBit(QBit(782)) -- Your friends are mad at you
end)

RegisterEvent(453, nil, function()
    if IsAtLeast(MapVar(6), 2) then return end
    SetValue(MapVar(6), 0)
end)

RegisterEvent(501, "Leave Castle Lambent", function()
    evt.MoveToMap(-1264, 19718, 225, 1536, 0, 0, 0, 8, "7d25.blv") -- Celeste
end, "Leave Castle Lambent")

