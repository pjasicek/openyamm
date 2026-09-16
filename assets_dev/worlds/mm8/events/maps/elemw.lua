-- Plane of Water
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
    [11] = { kind = "enter_house", source = "opcode", houseId = 691, targetName = "Riverglass' House" },
    [13] = { kind = "enter_house", source = "opcode", houseId = 692, targetName = "Clearcreek's House" },
    [15] = { kind = "enter_house", source = "opcode", houseId = 693, targetName = "Empty House" },
    [17] = { kind = "enter_house", source = "opcode", houseId = 694, targetName = "Empty House" },
    [19] = { kind = "enter_house", source = "opcode", houseId = 695, targetName = "Empty House" },
    [21] = { kind = "enter_house", source = "opcode", houseId = 545, targetName = "Black Current's House" },
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
    [451] = { kind = "generic_event", source = "opcode" },
    [505] = { kind = "travel", source = "opcode", targetMap = "out08.odm", targetName = "Ravage Roaming" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterNoOpEvent(1, nil)

RegisterNoOpEvent(2, nil)

RegisterNoOpEvent(3, nil)

RegisterNoOpEvent(4, nil)

RegisterNoOpEvent(5, nil)

RegisterEvent(6, nil, function()
    if IsQBitSet(QBit(241)) then return end -- Got the heart of water
    evt.ForPlayer(Players.All)
    if HasItem(607) then -- Heart of Water
        SetQBit(QBit(241)) -- Got the heart of water
        AddValue(Experience, 100000)
        SetQBit(QBit(206)) -- Heart of Water - I lost it
    end
end)

RegisterNoOpEvent(7, nil)

RegisterNoOpEvent(8, nil)

RegisterNoOpEvent(9, nil)

RegisterNoOpEvent(10, nil)

RegisterEvent(11, "Riverglass' House", function()
    evt.EnterHouse(691) -- Riverglass' House
end, "Riverglass' House")

RegisterEvent(12, "Riverglass' House", nil, "Riverglass' House")

RegisterEvent(13, "Clearcreek's House", function()
    evt.EnterHouse(692) -- Clearcreek's House
end, "Clearcreek's House")

RegisterEvent(14, "Clearcreek's House", nil, "Clearcreek's House")

RegisterEvent(15, "Empty House", function()
    evt.EnterHouse(693) -- Empty House
end, "Empty House")

RegisterEvent(16, "Empty House", nil, "Empty House")

RegisterEvent(17, "Empty House", function()
    evt.EnterHouse(694) -- Empty House
end, "Empty House")

RegisterEvent(18, "Empty House", nil, "Empty House")

RegisterEvent(19, "Empty House", function()
    evt.EnterHouse(695) -- Empty House
end, "Empty House")

RegisterEvent(20, "Empty House", nil, "Empty House")

RegisterEvent(21, "Black Current's House", function()
    evt.EnterHouse(545) -- Black Current's House
end, "Black Current's House")

RegisterEvent(22, "Black Current's House", nil, "Black Current's House")

RegisterEvent(81, nil, function()
    evt.OpenChest(0)
end)

RegisterEvent(82, nil, function()
    evt.OpenChest(1)
end)

RegisterEvent(83, nil, function()
    evt.OpenChest(2)
end)

RegisterEvent(84, nil, function()
    evt.OpenChest(3)
end)

RegisterEvent(85, nil, function()
    evt.OpenChest(4)
end)

RegisterEvent(86, nil, function()
    evt.OpenChest(5)
end)

RegisterEvent(87, nil, function()
    evt.OpenChest(6)
end)

RegisterEvent(88, nil, function()
    evt.OpenChest(7)
end)

RegisterEvent(89, nil, function()
    evt.OpenChest(8)
end)

RegisterEvent(90, nil, function()
    evt.OpenChest(9)
end)

RegisterEvent(91, nil, function()
    evt.OpenChest(10)
end)

RegisterEvent(92, nil, function()
    evt.OpenChest(11)
end)

RegisterEvent(93, nil, function()
    evt.OpenChest(12)
end)

RegisterEvent(94, nil, function()
    evt.OpenChest(13)
end)

RegisterEvent(95, nil, function()
    evt.OpenChest(14)
end)

RegisterEvent(96, nil, function()
    evt.OpenChest(15)
end)

RegisterEvent(97, nil, function()
    evt.OpenChest(16)
end)

RegisterEvent(98, nil, function()
    evt.OpenChest(17)
end)

RegisterEvent(99, nil, function()
    evt.OpenChest(18)
end)

RegisterEvent(100, nil, function()
    evt.OpenChest(19)
end)

RegisterEvent(401, "Gate out of the Plane of Water", nil, "Gate out of the Plane of Water")

RegisterEvent(451, "Take a Drink", function()
    if not IsAtLeast(WaterResistance, 10) then
        AddValue(WaterResistance, 2)
        evt.StatusText("Water Resistance +10 (Permanent)")
        SetAutonote(230) -- Well in the Plane of Water gives a permanent Water Resistance bonus up to an Water Resistance of 10.
        return
    end
    evt.StatusText("Refreshing")
end, "Take a Drink")

RegisterEvent(505, "Leave the Plane of Water", function()
    evt.MoveToMap(-22162, 2886, 689, 0, 0, 0, 0, 1, "out08.odm") -- Ravage Roaming
end, "Leave the Plane of Water")

