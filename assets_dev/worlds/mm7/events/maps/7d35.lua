-- Nighon Tunnels
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {65535, 65534, 65533},
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
    textureNames = {"cwb1"},
    spriteNames = {},
    castSpellIds = {6, 15, 18, 24},
    timers = {
    { eventId = 452, repeating = true, intervalGameMinutes = 2.5, remainingGameMinutes = 2.5 },
    { eventId = 454, repeating = true, intervalGameMinutes = 4, remainingGameMinutes = 4 },
    { eventId = 456, repeating = true, intervalGameMinutes = 3.5, remainingGameMinutes = 3.5 },
    },
})

RegisterEvent(3, "Legacy event 3", function()
    evt.SetDoorState(1, DoorAction.Trigger)
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

RegisterEvent(196, "Legacy event 196", function()
    if IsQBitSet(QBit(740)) then return end -- Dwarf Bones - I lost it
    AddValue(InventoryItem(1428), 1428) -- Zokarr IV's Skull
    SetQBit(QBit(740)) -- Dwarf Bones - I lost it
end)

RegisterEvent(197, "Legacy event 197", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(16), 1) then return 11 end
        return 1
    end
    local function Step_1()
        return PickRandomOption(197, 1, {2, 4, 6, 8, 2, 2})
    end
    local function Step_2()
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
        return 3
    end
    local function Step_3()
        return 9
    end
    local function Step_4()
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
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
        -- Missing legacy status text 13
        return 8
    end
    local function Step_8()
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
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
end)

RegisterEvent(198, "Legacy event 198", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(17), 1) then return 11 end
        return 1
    end
    local function Step_1()
        return PickRandomOption(198, 1, {2, 4, 6, 8, 2, 2})
    end
    local function Step_2()
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
        return 3
    end
    local function Step_3()
        return 9
    end
    local function Step_4()
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
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
        -- Missing legacy status text 13
        return 8
    end
    local function Step_8()
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
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
end)

RegisterEvent(199, "Legacy event 199", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(18), 1) then return 11 end
        return 1
    end
    local function Step_1()
        return PickRandomOption(199, 1, {2, 4, 6, 8, 2, 2})
    end
    local function Step_2()
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
        return 3
    end
    local function Step_3()
        return 9
    end
    local function Step_4()
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
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
        -- Missing legacy status text 13
        return 8
    end
    local function Step_8()
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
        return 9
    end
    local function Step_9()
        SetValue(MapVar(18), 1)
        return 10
    end
    local function Step_10()
        evt.SetTexture(4, "cwb1")
        return 11
    end
    local function Step_11()
        return nil
    end
    local function Step_13()
        if IsAtLeast(MapVar(18), 1) then return 15 end
        return 14
    end
    local function Step_14()
        return 11
    end
    local function Step_15()
        evt.SetTexture(4, "cwb1")
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
end)

RegisterEvent(451, "Legacy event 451", function()
    evt.MoveToMap(1168, 9584, -143, 0, 0, 0, 0, 0)
end)

RegisterEvent(452, "Legacy event 452", function()
    evt.MoveToMap(1232, 6896, -384, 0, 0, 0, 0, 0)
    evt.CastSpell(6, 7, 4, 13891, 229, 161, 13891, 4912, 161) -- Fireball
    evt.CastSpell(6, 7, 4, 14618, 857, 161, 9284, 857, 161) -- Fireball
end)

RegisterEvent(454, "Legacy event 454", function()
    evt.CastSpell(18, 8, 4, -9861, -3949, -479, -9861, -106, -479) -- Lightning Bolt
end)

RegisterEvent(455, "Legacy event 455", function()
    evt.CastSpell(15, 4, 4, -10624, 3456, -639, -10624, 3456, -639) -- Sparks
end)

RegisterEvent(456, "Legacy event 456", function()
    if evt.CheckSkill(33, 3, 40) then return end
    evt.CastSpell(24, 5, 4, 12023, 15154, -639, 11704, 15854, -479) -- Poison Spray
    evt.CastSpell(24, 5, 4, 11398, 15726, -639, 11673, 15051, -479) -- Poison Spray
    evt.CastSpell(24, 5, 4, 11066, 15649, -639, 11360, 14922, -479) -- Poison Spray
    evt.CastSpell(24, 5, 4, 11179, 14849, -639, 11047, 15637, -479) -- Poison Spray
    evt.CastSpell(24, 5, 4, 10704, 15259, -639, 11620, 15422, -479) -- Poison Spray
end)

RegisterEvent(501, "Leave the Cave", function()
    evt.MoveToMap(-4324, 1811, 3905, 172, 0, 0, 48, 0, "7d07.blv")
end, "Leave the Cave")

RegisterEvent(502, "Leave the Cave", function()
    evt.MoveToMap(-7766, 7703, -1535, 1792, 0, 0, 0, 0, "7d24.blv")
end, "Leave the Cave")

RegisterEvent(65535, "", function()
    return evt.map[197](13)
end)

RegisterEvent(65534, "", function()
    return evt.map[198](13)
end)

RegisterEvent(65533, "", function()
    return evt.map[199](13)
end)

