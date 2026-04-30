-- Dragon Cave
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 2, 3, 4, 5},
    onLeave = {6, 7, 8, 9, 10},
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
        if not IsAtLeast(88080640, 1344) then
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
    else
        evt.SetMonGroupBit(44, MonsterBits.Hostile, 0) -- actor group 44: Dragon Flightleader, Great Wyrm, spawn Dragon A, spawn Wimpy Dragon A
        evt.SetMonGroupBit(11, MonsterBits.Invisible, 1) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
        evt.SetMonGroupBit(11, MonsterBits.Hostile, 0) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
        ClearQBit(QBit(233)) -- You have Pissed of the Dragons
        SetValue(MapVar(11), 0)
        evt.SetMonGroupBit(45, MonsterBits.Hostile, 0) -- actor group 45: spawn Wimpy Dragon A
    end
return
end)

RegisterNoOpEvent(6, "Legacy event 6")

RegisterNoOpEvent(7, "Legacy event 7")

RegisterEvent(8, "Legacy event 8", function()
    if IsQBitSet(QBit(233)) then -- You have Pissed of the Dragons
        return
    elseif IsAtLeast(MapVar(11), 2) then
        SetQBit(QBit(233)) -- You have Pissed of the Dragons
        SetValue(256, 0)
        return
    else
        return
    end
end)

RegisterEvent(9, "Legacy event 9", function()
    if IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        return
    elseif IsQBitSet(QBit(155)) then -- Killed all Dragons in Garrote Gorge Area
        return
    else
        if not evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 189, 0, false) then return end -- monster 189 "Hatchling"; all matching actors defeated
        if not evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 190, 0, false) then return end -- monster 190 "Dragonette"; all matching actors defeated
        if not evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 191, 0, false) then return end -- monster 191 "Young Dragon"; all matching actors defeated
        if not evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 69, 0, false) then return end -- monster 69 "Dragon"; all matching actors defeated
        if not evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 70, 0, false) then return end -- monster 70 "Dragon Flightleader"; all matching actors defeated
        if not evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 71, 0, false) then return end -- monster 71 "Great Wyrm"; all matching actors defeated
        if not IsQBitSet(QBit(156)) then -- Questbit set for Riki
            SetQBit(QBit(156)) -- Questbit set for Riki
            evt.SummonMonsters(2, 1, 223, -8, 170, 0, 1, 0) -- encounter slot 2 "Wimpy Dragon" tier A, count 223, pos=(-8, 170, 0), actor group 1, no unique actor name
            evt.SetMonGroupBit(1, MonsterBits.Invisible, 1)
            return
        end
        SetQBit(QBit(155)) -- Killed all Dragons in Garrote Gorge Area
        SetQBit(QBit(225)) -- dead questbit for internal use(bling)
        ClearQBit(QBit(225)) -- dead questbit for internal use(bling)
        evt.StatusText("You have killed all of the Dragons")
        return
    end
end)

RegisterEvent(10, "Legacy event 10", function()
    if not IsQBitSet(QBit(22)) then return end -- Allied with Dragons. Return Dragon Egg to Dragons done.
    evt.MoveNPC(21, 0) -- Deftclaw Redreaver -> removed
    evt.MoveNPC(66, 175) -- Deftclaw Redreaver -> Council Chamber Door
    return
end)

RegisterEvent(81, "Chest", function()
    evt.OpenChest(0)
    return
end, "Chest")

RegisterEvent(82, "Chest", function()
    evt.OpenChest(1)
    return
end, "Chest")

RegisterEvent(83, "Chest", function()
    evt.OpenChest(2)
    return
end, "Chest")

RegisterEvent(84, "Chest", function()
    evt.OpenChest(3)
    return
end, "Chest")

RegisterEvent(85, "Chest", function()
    evt.OpenChest(4)
    return
end, "Chest")

RegisterEvent(86, "Chest", function()
    evt.OpenChest(5)
    return
end, "Chest")

RegisterEvent(87, "Chest", function()
    evt.OpenChest(6)
    return
end, "Chest")

RegisterEvent(88, "Chest", function()
    evt.OpenChest(7)
    return
end, "Chest")

RegisterEvent(89, "Chest", function()
    evt.OpenChest(8)
    return
end, "Chest")

RegisterEvent(90, "Chest", function()
    evt.OpenChest(9)
    return
end, "Chest")

RegisterEvent(91, "Chest", function()
    evt.OpenChest(10)
    return
end, "Chest")

RegisterEvent(92, "Chest", function()
    evt.OpenChest(11)
    return
end, "Chest")

RegisterEvent(93, "Chest", function()
    evt.OpenChest(12)
    return
end, "Chest")

RegisterEvent(94, "Chest", function()
    evt.OpenChest(13)
    return
end, "Chest")

RegisterEvent(95, "Chest", function()
    evt.OpenChest(14)
    return
end, "Chest")

RegisterEvent(96, "Chest", function()
    evt.OpenChest(15)
    return
end, "Chest")

RegisterEvent(97, "Chest", function()
    evt.OpenChest(16)
    return
end, "Chest")

RegisterEvent(98, "Chest", function()
    evt.OpenChest(17)
    return
end, "Chest")

RegisterEvent(99, "Chest", function()
    evt.OpenChest(18)
    return
end, "Chest")

RegisterEvent(100, "Chest", function()
    evt.OpenChest(19)
    return
end, "Chest")

RegisterEvent(131, "Cave Entrance", function()
    evt.EnterHouse(350) -- Ishton's Cave
    return
end, "Cave Entrance")

RegisterEvent(132, "Cave Entrance", function()
    evt.EnterHouse(351) -- Ithilgore's Cave
    return
end, "Cave Entrance")

RegisterEvent(133, "Cave Entrance", function()
    evt.EnterHouse(352) -- Scarwing's Cave
    return
end, "Cave Entrance")

RegisterEvent(201, "Dragon Leader's Cavern ", function()
    evt.EnterHouse(178) -- Dragon Leader's Cavern
    return
end, "Dragon Leader's Cavern ")

RegisterEvent(451, "Legacy event 451", function()
    if IsAtLeast(316, 0) then return end
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SpeakNPC(39) -- Guard
    SetValue(MapVar(11), 1)
    return
end)

RegisterEvent(452, "Legacy event 452", function()
    if IsAtLeast(MapVar(11), 2) then return end
    SetValue(MapVar(11), 0)
    return
end)

RegisterEvent(453, "Legacy event 453", function()
    if IsAtLeast(MapVar(11), 2) then return end
    evt.SetMonGroupBit(44, MonsterBits.Hostile, 1) -- actor group 44: Dragon Flightleader, Great Wyrm, spawn Dragon A, spawn Wimpy Dragon A
    evt.SetMonGroupBit(11, MonsterBits.Invisible, 0) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
    evt.SetMonGroupBit(11, MonsterBits.Hostile, 1) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
    SetValue(MapVar(11), 2)
    evt.SetMonGroupBit(45, MonsterBits.Hostile, 1) -- actor group 45: spawn Wimpy Dragon A
    return
end)

RegisterEvent(501, "Leave the dragon cave", function()
    evt.MoveToMap(6376, 12420, 1616, 0, 0, 0, 0, 0, "Out05.odm")
    return
end, "Leave the dragon cave")

