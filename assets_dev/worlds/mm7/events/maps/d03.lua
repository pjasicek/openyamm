-- Castle Gloaming
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 377},
    onLeave = {},
    openedChestIds = {
    [176] = {1, 0},
    [177] = {2},
    [178] = {3},
    [179] = {4},
    [180] = {5},
    [181] = {18, 6},
    [182] = {19, 7},
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
    contextActions = {
    [5] = { kind = "enter_house", source = "opcode", houseId = 219, targetName = "Throne Room" },
    [151] = { kind = "teleport", source = "heuristic" },
    [152] = { kind = "teleport", source = "heuristic" },
    [153] = { kind = "teleport", source = "heuristic" },
    [176] = { kind = "open_chest", source = "opcode", chestIds = {0, 1} },
    [177] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [178] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [179] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [180] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [181] = { kind = "open_chest", source = "opcode", chestIds = {6, 18} },
    [182] = { kind = "open_chest", source = "opcode", chestIds = {7, 19} },
    [183] = { kind = "open_chest", source = "opcode", chestIds = {8} },
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
    [194] = { kind = "open_chest", source = "opcode", chestIds = {19} },
    [195] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [501] = { kind = "passage", source = "opcode", targetMap = "7d26.blv", targetName = "The Pit" },
    [502] = { kind = "passage", source = "opcode", targetMap = "7d26.blv", targetName = "The Pit" },
    },
    textureNames = {"cnb"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    if IsQBitSet(QBit(612)) then -- Chose the path of Dark
        if IsQBitSet(QBit(782)) then -- Your friends are mad at you
            if IsAtLeast(Counter(10), 720) then
                ClearQBit(QBit(782)) -- Your friends are mad at you
                SetValue(MapVar(6), 0)
                evt.SetMonGroupBit(56, MonsterBits.Hostile, 0) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
                evt.SetMonGroupBit(55, MonsterBits.Hostile, 0) -- actor group 55: Speaker for the Dead
                return
            end
            SetValue(MapVar(6), 2)
            evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
            evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
            return
        elseif IsAtLeast(MapVar(6), 2) then
            evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
            evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
            return
        else
            return
        end
        return
    end
    SetValue(MapVar(6), 2)
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
    evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
end)

RegisterEvent(5, "Throne Room", function()
    if not IsAtLeast(MapVar(6), 2) then
        if not IsQBitSet(QBit(710)) then -- Archibald in Clankers Lab now
            evt.EnterHouse(219) -- Throne Room
            return
        end
        evt.EnterHouse(221) -- Throne Room
        return
    end
    evt.StatusText("The Door is Locked")
end, "Throne Room")

RegisterEvent(151, nil, function()
    evt.MoveToMap(-8684, -15996, -2327, 0, 0, 0, 0, 0)
end)

RegisterEvent(152, nil, function()
    evt.MoveToMap(-902, 1001, -191, 0, 0, 0, 0, 0)
end)

RegisterEvent(153, nil, function()
    evt.MoveToMap(-9244, 2123, -1943, 0, 0, 0, 0, 0)
end)

RegisterEvent(176, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
    end
    if not IsQBitSet(QBit(611)) then -- Chose the path of Light
        evt.OpenChest(1)
        return
    end
    if not HasAward(Award(24)) then -- Retrieved Soul Jars
        evt.OpenChest(0)
        SetQBit(QBit(743)) -- Lich Jar Case - I lost it
        SetQBit(QBit(662)) -- Got Lich Jar from Castle Gloaming
        return
    end
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(177, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(2)
        return
    end
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(178, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(3)
        return
    end
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(179, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(4)
        return
    end
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(180, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(5)
        return
    end
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(181, "Chest", function()
    local function Step_0()
        if IsQBitSet(QBit(612)) then return 6 end -- Chose the path of Dark
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
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        return 4
    end
    local function Step_4()
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        return 5
    end
    local function Step_5()
        return 7
    end
    local function Step_6()
        if IsQBitSet(QBit(643)) then return 9 end -- Go to the Lincoln in the sea west of Avlee and retrieve the Oscillation Overthruster and return it to Kastore in the Pit.
        return 7
    end
    local function Step_7()
        evt.OpenChest(18)
        return 8
    end
    local function Step_8()
        return nil
    end
    local function Step_9()
        evt.SetChestBit(6, 1, 0)
        return 10
    end
    local function Step_10()
        evt.OpenChest(6)
        return 11
    end
    local function Step_11()
        SetQBit(QBit(747)) -- Wetsuit - I lost it
        return 12
    end
    local function Step_12()
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
        else
            step = nil
        end
    end
end, "Chest")

RegisterEvent(182, "Chest", function()
    local function Step_0()
        if IsQBitSet(QBit(612)) then return 6 end -- Chose the path of Dark
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
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        return 4
    end
    local function Step_4()
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        return 5
    end
    local function Step_5()
        return 7
    end
    local function Step_6()
        if IsQBitSet(QBit(643)) then return 9 end -- Go to the Lincoln in the sea west of Avlee and retrieve the Oscillation Overthruster and return it to Kastore in the Pit.
        return 7
    end
    local function Step_7()
        evt.OpenChest(19)
        return 8
    end
    local function Step_8()
        return nil
    end
    local function Step_9()
        evt.SetChestBit(7, 1, 0)
        return 10
    end
    local function Step_10()
        evt.OpenChest(7)
        return 11
    end
    local function Step_11()
        SetQBit(QBit(747)) -- Wetsuit - I lost it
        return 12
    end
    local function Step_12()
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
        else
            step = nil
        end
    end
end, "Chest")

RegisterEvent(183, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(8)
        return
    end
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(184, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(9)
        return
    end
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(185, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(10)
        return
    end
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(186, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(11)
        return
    end
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(187, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(12)
        return
    end
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(188, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(13)
        return
    end
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(189, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(14)
        return
    end
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(190, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(15)
        return
    end
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(191, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(16)
        return
    end
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(192, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(17)
        return
    end
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(193, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(18)
        return
    end
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(194, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(19)
        return
    end
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(195, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.OpenChest(0)
        return
    end
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(376, nil, function()
    if IsQBitSet(QBit(711)) then return end -- Take the Associate's Tapestry
    if IsQBitSet(QBit(612)) and IsQBitSet(QBit(694)) then -- Chose the path of Dark
        evt.SetTexture(10, "cnb")
        AddValue(InventoryItem(1422), 1422) -- Big Tapestry
        SetQBit(QBit(711)) -- Take the Associate's Tapestry
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
        SetValue(MapVar(6), 2)
    else
    end
end)

RegisterEvent(377, nil, function()
    if IsQBitSet(QBit(711)) then -- Take the Associate's Tapestry
        evt.SetTexture(15, "cnb")
    end
end)

RegisterEvent(451, nil, function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 1) then return end
    evt.SpeakNPC(619) -- Castle Guard
    SetValue(MapVar(6), 1)
end)

RegisterEvent(452, nil, function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 2) then return end
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Lich A, spawn Necromancer A, spawn Vampire A
    evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Speaker for the Dead
    SetValue(MapVar(6), 2)
    SetValue(Counter(10), 0)
    SetQBit(QBit(782)) -- Your friends are mad at you
end)

RegisterEvent(453, nil, function()
    if IsAtLeast(MapVar(6), 2) then return end
    SetValue(MapVar(6), 0)
end)

RegisterEvent(454, nil, function()
    if not IsAtLeast(FireResistanceBonus, 50) then
        if not IsAtLeast(FireResistance, 50) then
            evt.ForPlayer(Players.All)
            SetValue(Eradicated, 0)
            return
        end
    end
    local randomStep = PickRandomOption(454, 6, {6, 8})
    if randomStep == 6 then
        evt.ForPlayer(Players.All)
        SetValue(Eradicated, 0)
    end
end)

RegisterEvent(501, nil, function()
    evt.MoveToMap(-11435, -20277, 1, 0, 0, 0, 0, 8, "7d26.blv") -- The Pit
end)

RegisterEvent(502, nil, function()
    evt.MoveToMap(-10656, -23968, -384, 0, 0, 0, 0, 8, "7d26.blv") -- The Pit
end)

