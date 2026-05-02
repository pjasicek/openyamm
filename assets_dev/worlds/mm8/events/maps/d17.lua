-- Dragon Cave
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 2, 3, 4, 5},
    onLeave = {6, 7, 8, 65535, 10},
    openedChestIds = {
    [81] = {0},
    [82] = {1},
    [83] = {2},
    [84] = {3},
    [85] = {4},
    [86] = {5},
    [87] = {6},
    [88] = {7},
    [89] = {8},
    [90] = {9},
    [91] = {10},
    [92] = {11},
    [93] = {12},
    [94] = {13},
    [95] = {14},
    [96] = {15},
    [97] = {16},
    [98] = {17},
    [99] = {18},
    [100] = {19},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 9, repeating = true, intervalGameMinutes = 10, remainingGameMinutes = 10 },
    },
})

RegisterNoOpEvent(1, "Legacy event 1")

RegisterNoOpEvent(2, "Legacy event 2")

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterEvent(5, "Legacy event 5", function()
    if IsQBitSet(QBit(21)) then -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
        evt.SetMonGroupBit(44, MonsterBits.Hostile, 1) -- actor group 44: Dragon Flightleader, Great Wyrm, spawn Dragon A, spawn Wimpy Dragon A
        evt.SetMonGroupBit(11, MonsterBits.Invisible, 0) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
        evt.SetMonGroupBit(11, MonsterBits.Hostile, 1) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
        SetValue(MapVar(11), 2)
        evt.SetMonGroupBit(45, MonsterBits.Hostile, 1) -- actor group 45: spawn Wimpy Dragon A
        return
    elseif IsQBitSet(QBit(233)) then -- You have Pissed of the Dragons
        if not IsAtLeast(Counter(10), 1344) then
            evt.SetMonGroupBit(44, MonsterBits.Hostile, 1) -- actor group 44: Dragon Flightleader, Great Wyrm, spawn Dragon A, spawn Wimpy Dragon A
            evt.SetMonGroupBit(11, MonsterBits.Invisible, 0) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
            evt.SetMonGroupBit(11, MonsterBits.Hostile, 1) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
            SetValue(MapVar(11), 2)
            evt.SetMonGroupBit(45, MonsterBits.Hostile, 1) -- actor group 45: spawn Wimpy Dragon A
            return
        end
        evt.SetMonGroupBit(44, MonsterBits.Hostile, 0) -- actor group 44: Dragon Flightleader, Great Wyrm, spawn Dragon A, spawn Wimpy Dragon A
        evt.SetMonGroupBit(11, MonsterBits.Invisible, 1) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
        evt.SetMonGroupBit(11, MonsterBits.Hostile, 0) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
        ClearQBit(QBit(233)) -- You have Pissed of the Dragons
        SetValue(MapVar(11), 0)
        evt.SetMonGroupBit(45, MonsterBits.Hostile, 0) -- actor group 45: spawn Wimpy Dragon A
        return
    else
        return
    end
end)

RegisterNoOpEvent(6, "Legacy event 6")

RegisterNoOpEvent(7, "Legacy event 7")

RegisterEvent(8, "Legacy event 8", function()
    if IsQBitSet(QBit(233)) then -- You have Pissed of the Dragons
        return
    end
    if not IsAtLeast(MapVar(11), 2) then
        SetValue(MapVar(11), 0)
        return
    end
    SetQBit(QBit(233)) -- You have Pissed of the Dragons
    SetValue(Counter(10), 0)
end)

RegisterEvent(9, "Legacy event 9", function(continueStep)
    local function Step_2()
        if IsQBitSet(QBit(22)) then return 25 end -- Allied with Dragons. Return Dragon Egg to Dragons done.
        return 3
    end
    local function Step_3()
        if IsQBitSet(QBit(155)) then return 25 end -- Killed all Dragons in Garrote Gorge Area
        return 4
    end
    local function Step_4()
        if evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 189, 0, false) then return 6 end -- monster 189 "Hatchling"; all matching actors defeated
        return 5
    end
    local function Step_5()
        return 25
    end
    local function Step_6()
        if evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 190, 0, false) then return 8 end -- monster 190 "Dragonette"; all matching actors defeated
        return 7
    end
    local function Step_7()
        return 25
    end
    local function Step_8()
        if evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 191, 0, false) then return 10 end -- monster 191 "Young Dragon"; all matching actors defeated
        return 9
    end
    local function Step_9()
        return 25
    end
    local function Step_10()
        if evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 69, 0, false) then return 12 end -- monster 69 "Dragon"; all matching actors defeated
        return 11
    end
    local function Step_11()
        return 25
    end
    local function Step_12()
        if evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 70, 0, false) then return 14 end -- monster 70 "Dragon Flightleader"; all matching actors defeated
        return 13
    end
    local function Step_13()
        return 25
    end
    local function Step_14()
        if evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 71, 0, false) then return 16 end -- monster 71 "Great Wyrm"; all matching actors defeated
        return 15
    end
    local function Step_15()
        return 25
    end
    local function Step_16()
        if IsQBitSet(QBit(156)) then return 21 end -- Questbit set for Riki
        return 17
    end
    local function Step_17()
        SetQBit(QBit(156)) -- Questbit set for Riki
        return 18
    end
    local function Step_18()
        evt.SummonMonsters(2, 1, 223, -8, 170, 0, 1, 0) -- encounter slot 2 "Wimpy Dragon" tier A, count 223, pos=(-8, 170, 0), actor group 1, no unique actor name
        return 19
    end
    local function Step_19()
        evt.SetMonGroupBit(1, MonsterBits.Invisible, 1)
        return 20
    end
    local function Step_20()
        return 25
    end
    local function Step_21()
        SetQBit(QBit(155)) -- Killed all Dragons in Garrote Gorge Area
        return 22
    end
    local function Step_22()
        SetQBit(QBit(225)) -- dead questbit for internal use(bling)
        return 23
    end
    local function Step_23()
        ClearQBit(QBit(225)) -- dead questbit for internal use(bling)
        return 24
    end
    local function Step_24()
        evt.StatusText("You have killed all of the Dragons")
        return 25
    end
    local function Step_25()
        return nil
    end
    local step = continueStep or 2
    while step ~= nil do
        if step == 2 then
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
        elseif step == 14 then
            step = Step_14()
        elseif step == 15 then
            step = Step_15()
        elseif step == 16 then
            step = Step_16()
        elseif step == 17 then
            step = Step_17()
        elseif step == 18 then
            step = Step_18()
        elseif step == 19 then
            step = Step_19()
        elseif step == 20 then
            step = Step_20()
        elseif step == 21 then
            step = Step_21()
        elseif step == 22 then
            step = Step_22()
        elseif step == 23 then
            step = Step_23()
        elseif step == 24 then
            step = Step_24()
        elseif step == 25 then
            step = Step_25()
        else
            step = nil
        end
    end
end)

RegisterEvent(10, "Legacy event 10", function()
    if IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        evt.MoveNPC(17, 0) -- Deftclaw Redreaver -> removed
        evt.MoveNPC(53, 751) -- Deftclaw Redreaver -> Council Chamber Door
    end
end)

RegisterEvent(81, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(82, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(83, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(84, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(85, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(86, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(87, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(88, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(89, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(90, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(91, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(92, "Chest", function()
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(93, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(94, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(95, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(96, "Chest", function()
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(97, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(98, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(99, "Chest", function()
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(100, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(131, "Cave Entrance", function()
    evt.EnterHouse(572) -- Ishton's Cave
end, "Cave Entrance")

RegisterEvent(132, "Cave Entrance", function()
    evt.EnterHouse(573) -- Ithilgore's Cave
end, "Cave Entrance")

RegisterEvent(133, "Cave Entrance", function()
    evt.EnterHouse(574) -- Scarwing's Cave
end, "Cave Entrance")

RegisterEvent(201, "Dragon Leader's Cavern ", function()
    evt.EnterHouse(774) -- Dragon Leader's Cavern
end, "Dragon Leader's Cavern ")

RegisterEvent(451, "Legacy event 451", function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SpeakNPC(35) -- Guard
    SetValue(MapVar(11), 1)
end)

RegisterEvent(452, "Legacy event 452", function()
    if IsAtLeast(MapVar(11), 2) then return end
    SetValue(MapVar(11), 0)
end)

RegisterEvent(453, "Legacy event 453", function()
    if IsAtLeast(MapVar(11), 2) then return end
    evt.SetMonGroupBit(44, MonsterBits.Hostile, 1) -- actor group 44: Dragon Flightleader, Great Wyrm, spawn Dragon A, spawn Wimpy Dragon A
    evt.SetMonGroupBit(11, MonsterBits.Invisible, 0) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
    evt.SetMonGroupBit(11, MonsterBits.Hostile, 1) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
    SetValue(MapVar(11), 2)
    evt.SetMonGroupBit(45, MonsterBits.Hostile, 1) -- actor group 45: spawn Wimpy Dragon A
end)

RegisterEvent(501, "Leave the dragon cave", function()
    evt.MoveToMap(6376, 12420, 1616, 0, 0, 0, 0, 1, "out05.odm") -- Garrote Gorge
end, "Leave the dragon cave")

RegisterEvent(65535, "", function()
    return evt.map[9](1)
end)

