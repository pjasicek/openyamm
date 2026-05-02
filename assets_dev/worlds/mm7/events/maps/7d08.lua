-- The Tularean Caves
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 65535, 65534},
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
    [195] = {0},
    },
    textureNames = {"cwb1", "trim11_16"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 151, repeating = true, intervalGameMinutes = 2, remainingGameMinutes = 2 },
    { eventId = 152, repeating = true, intervalGameMinutes = 2.5, remainingGameMinutes = 2.5 },
    { eventId = 153, repeating = true, intervalGameMinutes = 2, remainingGameMinutes = 2 },
    { eventId = 154, repeating = true, intervalGameMinutes = 1.5, remainingGameMinutes = 1.5 },
    { eventId = 155, repeating = true, intervalGameMinutes = 2, remainingGameMinutes = 2 },
    { eventId = 156, repeating = true, intervalGameMinutes = 1, remainingGameMinutes = 1 },
    },
})

RegisterEvent(1, "Legacy event 1", function()
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
    if IsAtLeast(MapVar(3), 1) then
        evt.SetFacetBit(1, FacetBits.Untouchable, 1)
        evt.SetFacetBit(1, FacetBits.Fluid, 1)
        evt.SetTexture(1, "trim11_16")
    end
end)

RegisterEvent(3, "Door", function()
    evt.SetDoorState(12, DoorAction.Trigger)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(4, DoorAction.Trigger)
end, "Door")

RegisterEvent(151, "Legacy event 151", function()
    evt.SetDoorState(9, DoorAction.Trigger)
end)

RegisterEvent(152, "Legacy event 152", function()
    evt.SetDoorState(10, DoorAction.Trigger)
end)

RegisterEvent(153, "Legacy event 153", function()
    evt.SetDoorState(11, DoorAction.Trigger)
end)

RegisterEvent(154, "Legacy event 154", function()
    evt.SetDoorState(1, DoorAction.Trigger)
end)

RegisterEvent(155, "Legacy event 155", function()
    evt.SetDoorState(2, DoorAction.Trigger)
end)

RegisterEvent(156, "Legacy event 156", function()
    evt.SetDoorState(3, DoorAction.Trigger)
end)

RegisterEvent(157, "Legacy event 157", function()
    evt.MoveToMap(-5248, -7552, 768, 0, 0, 0, 0, 0)
end)

RegisterEvent(158, "Legacy event 158", function()
    evt.MoveToMap(-4640, -7901, 768, 0, 0, 0, 0, 0)
end)

RegisterEvent(159, "Legacy event 159", function()
    evt.MoveToMap(-5248, -8320, 768, 0, 0, 0, 0, 0)
end)

RegisterEvent(160, "Legacy event 160", function()
    evt.MoveToMap(-6912, 14592, -576, 0, 0, 0, 0, 0)
end)

RegisterEvent(161, "Legacy event 161", function()
    evt.SetDoorState(8, DoorAction.Trigger)
    SetValue(MapVar(3), 1)
    AddValue(MapVar(4), 1)
    evt.SetFacetBit(1, FacetBits.Untouchable, 1)
    evt.SetFacetBit(1, FacetBits.Fluid, 1)
    evt.SetTexture(1, "trim11_16")
end)

RegisterEvent(162, "Legacy event 162", function()
    if not IsAtLeast(MapVar(3), 1) then return end
    local randomStep = PickRandomOption(162, 3, {4, 6, 8})
    if randomStep == 4 then
        evt.MoveToMap(256, -128, 1, 0, 0, 0, 0, 0)
        return
    elseif randomStep == 6 then
        evt.MoveToMap(-10624, 2304, -832, 0, 0, 0, 0, 0)
        return
    elseif randomStep == 8 then
        evt.MoveToMap(-4096, -10624, 832, 0, 0, 0, 0, 0)
        return
    end
end)

RegisterEvent(163, "Legacy event 163", function()
    if not IsAtLeast(MapVar(3), 1) then return end
    local randomStep = PickRandomOption(163, 3, {4, 6, 8})
    if randomStep == 4 then
        evt.MoveToMap(256, -128, 1, 0, 0, 0, 0, 0)
        return
    elseif randomStep == 6 then
        evt.MoveToMap(-10624, 2304, -832, 0, 0, 0, 0, 0)
        return
    elseif randomStep == 8 then
        evt.MoveToMap(-4096, -10624, 832, 0, 0, 0, 0, 0)
        return
    end
end)

RegisterEvent(164, "Legacy event 164", function()
    if IsAtLeast(MapVar(3), 1) then
        evt.MoveToMap(6016, 6528, 1528, 0, 0, 0, 0, 0)
    end
end)

RegisterEvent(165, "Legacy event 165", function()
    evt.MoveToMap(2816, 7552, 288, 0, 0, 0, 0, 0)
end)

RegisterEvent(176, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(177, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(178, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(179, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(180, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(181, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(182, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(183, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(184, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(185, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(186, "Chest", function()
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(187, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(188, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(189, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(190, "Chest", function()
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(191, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(192, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(193, "Chest", function()
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(194, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(195, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(196, "Ore Vein", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(16), 1) then return 11 end
        return 1
    end
    local function Step_1()
        return PickRandomOption(196, 1, {2, 4, 6, 8, 2, 2})
    end
    local function Step_2()
        AddValue(InventoryItem(1488), 1488) -- Iron-laced ore
        return 3
    end
    local function Step_3()
        return 9
    end
    local function Step_4()
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
        return 5
    end
    local function Step_5()
        return 9
    end
    local function Step_6()
        evt.DamagePlayer(5, 0, 50)
        return 7
    end
    local function Step_7()
        evt.StatusText("Cave In !")
        return 8
    end
    local function Step_8()
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
        return 9
    end
    local function Step_9()
        SetValue(MapVar(16), 1)
        return 10
    end
    local function Step_10()
        evt.SetTexture(2, "cwb1")
        return 11
    end
    local function Step_11()
        return nil
    end
    local function Step_13()
        if IsAtLeast(MapVar(16), 1) then return 15 end
        return 14
    end
    local function Step_14()
        return 11
    end
    local function Step_15()
        evt.SetTexture(2, "cwb1")
        return nil
    end
    local step = continueStep or 0
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
        elseif step == 13 then
            step = Step_13()
        elseif step == 14 then
            step = Step_14()
        elseif step == 15 then
            step = Step_15()
        else
            step = nil
        end
    end
end, "Ore Vein")

RegisterEvent(197, "Ore Vein", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(17), 1) then return 11 end
        return 1
    end
    local function Step_1()
        return PickRandomOption(197, 1, {2, 4, 6, 8, 2, 2})
    end
    local function Step_2()
        AddValue(InventoryItem(1488), 1488) -- Iron-laced ore
        return 3
    end
    local function Step_3()
        return 9
    end
    local function Step_4()
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
        return 5
    end
    local function Step_5()
        return 9
    end
    local function Step_6()
        evt.DamagePlayer(5, 0, 50)
        return 7
    end
    local function Step_7()
        evt.StatusText("Cave In !")
        return 8
    end
    local function Step_8()
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
        return 9
    end
    local function Step_9()
        SetValue(MapVar(17), 1)
        return 10
    end
    local function Step_10()
        evt.SetTexture(3, "cwb1")
        return 11
    end
    local function Step_11()
        return nil
    end
    local function Step_13()
        if IsAtLeast(MapVar(17), 1) then return 15 end
        return 14
    end
    local function Step_14()
        return 11
    end
    local function Step_15()
        evt.SetTexture(3, "cwb1")
        return nil
    end
    local step = continueStep or 0
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
        elseif step == 13 then
            step = Step_13()
        elseif step == 14 then
            step = Step_14()
        elseif step == 15 then
            step = Step_15()
        else
            step = nil
        end
    end
end, "Ore Vein")

RegisterEvent(376, "Door", function()
    if not IsQBitSet(QBit(1696)) then -- Replacement for NPCs ¹72 ver. 7
        if IsQBitSet(QBit(1695)) then -- Replacement for NPCs ¹71 ver. 7
            return
        elseif IsQBitSet(QBit(593)) then -- Gave Loren to Catherine
            evt.FaceAnimation(FaceAnimation.DoorLocked)
        elseif IsQBitSet(QBit(595)) then -- Gave false Loren to Catherine (betray)
            return
        elseif IsQBitSet(QBit(605)) then -- Tularean Caves. Got Loren
            evt.FaceAnimation(FaceAnimation.DoorLocked)
        else
            SetQBit(QBit(1695)) -- Replacement for NPCs ¹71 ver. 7
            evt.ForPlayer(Players.All)
            SetQBit(QBit(605)) -- Tularean Caves. Got Loren
            evt.SpeakNPC(410) -- Loren Steel
            return
        end
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Door")

RegisterEvent(501, "Exit the Tularean Caves", function()
    evt.MoveToMap(-13798, 19726, 4192, 1024, 0, 0, 0, 0, "7out04.odm")
end, "Exit the Tularean Caves")

RegisterEvent(502, "Exit the Tularean Caves", function()
    evt.MoveToMap(-10183, 12574, -1967, 1792, 0, 0, 0, 0, "\t7d32.blv")
end, "Exit the Tularean Caves")

RegisterEvent(65535, "", function()
    return evt.map[196](13)
end)

RegisterEvent(65534, "", function()
    return evt.map[197](13)
end)

