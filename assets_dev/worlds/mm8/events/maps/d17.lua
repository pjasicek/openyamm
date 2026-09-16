-- Dragon Cave
-- generated from legacy EVT/STR

SetMapMetadata({
    levitateTrapFaceMask = 0x08000000,
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
    contextActions = {
    [81] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [82] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [83] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [84] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [85] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [86] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [87] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [88] = { kind = "open_chest", source = "opcode", chestIds = {7} },
    [89] = { kind = "open_chest", source = "opcode", chestIds = {8} },
    [90] = { kind = "open_chest", source = "opcode", chestIds = {9} },
    [91] = { kind = "open_chest", source = "opcode", chestIds = {10} },
    [92] = { kind = "open_chest", source = "opcode", chestIds = {11} },
    [93] = { kind = "open_chest", source = "opcode", chestIds = {12} },
    [94] = { kind = "open_chest", source = "opcode", chestIds = {13} },
    [95] = { kind = "open_chest", source = "opcode", chestIds = {14} },
    [96] = { kind = "open_chest", source = "opcode", chestIds = {15} },
    [97] = { kind = "open_chest", source = "opcode", chestIds = {16} },
    [98] = { kind = "open_chest", source = "opcode", chestIds = {17} },
    [99] = { kind = "open_chest", source = "opcode", chestIds = {18} },
    [100] = { kind = "open_chest", source = "opcode", chestIds = {19} },
    [131] = { kind = "enter_house", source = "opcode", houseId = 572, targetName = "Ishton's Cave" },
    [132] = { kind = "enter_house", source = "opcode", houseId = 573, targetName = "Ithilgore's Cave" },
    [133] = { kind = "enter_house", source = "opcode", houseId = 574, targetName = "Scarwing's Cave" },
    [201] = { kind = "enter_house", source = "opcode", houseId = 774, targetName = "Dragon Leader's Cavern " },
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "out05.odm", targetName = "Garrote Gorge" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 9, sourceEventId = 9, triggerStep = 1, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 20 },
    },
})

RegisterNoOpEvent(1, nil)

RegisterNoOpEvent(2, nil)

RegisterNoOpEvent(3, nil)

RegisterNoOpEvent(4, nil)

RegisterEvent(5, nil, function()
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

RegisterNoOpEvent(6, nil)

RegisterNoOpEvent(7, nil)

RegisterEvent(8, nil, function()
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

RegisterEvent(9, nil, function()
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

RegisterEvent(10, nil, function()
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

RegisterEvent(131, "Ishton's Cave", function()
    evt.EnterHouse(572) -- Ishton's Cave
end, "Ishton's Cave")

RegisterEvent(132, "Ithilgore's Cave", function()
    evt.EnterHouse(573) -- Ithilgore's Cave
end, "Ithilgore's Cave")

RegisterEvent(133, "Scarwing's Cave", function()
    evt.EnterHouse(574) -- Scarwing's Cave
end, "Scarwing's Cave")

RegisterEvent(201, "Dragon Leader's Cavern ", function()
    evt.EnterHouse(774) -- Dragon Leader's Cavern
end, "Dragon Leader's Cavern ")

RegisterEvent(451, nil, function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SpeakNPC(35) -- Guard
    SetValue(MapVar(11), 1)
end)

RegisterEvent(452, nil, function()
    if IsAtLeast(MapVar(11), 2) then return end
    SetValue(MapVar(11), 0)
end)

RegisterEvent(453, nil, function()
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

