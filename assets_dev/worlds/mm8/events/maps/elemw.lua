-- Plane of Water
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
    },
})

RegisterNoOpEvent(1, "Legacy event 1")

RegisterNoOpEvent(2, "Legacy event 2")

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterNoOpEvent(5, "Legacy event 5")

RegisterEvent(6, "Legacy event 6", function()
    if IsQBitSet(QBit(241)) then return end -- Got the heart of water
    evt.ForPlayer(Players.All)
    if HasItem(607) then -- Heart of Water
        SetQBit(QBit(241)) -- Got the heart of water
        AddValue(Experience, 100000)
        SetQBit(QBit(206)) -- Heart of Water - I lost it
    end
end)

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterNoOpEvent(10, "Legacy event 10")

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

RegisterEvent(81, "Legacy event 81", function()
    evt.OpenChest(0)
end)

RegisterEvent(82, "Legacy event 82", function()
    evt.OpenChest(1)
end)

RegisterEvent(83, "Legacy event 83", function()
    evt.OpenChest(2)
end)

RegisterEvent(84, "Legacy event 84", function()
    evt.OpenChest(3)
end)

RegisterEvent(85, "Legacy event 85", function()
    evt.OpenChest(4)
end)

RegisterEvent(86, "Legacy event 86", function()
    evt.OpenChest(5)
end)

RegisterEvent(87, "Legacy event 87", function()
    evt.OpenChest(6)
end)

RegisterEvent(88, "Legacy event 88", function()
    evt.OpenChest(7)
end)

RegisterEvent(89, "Legacy event 89", function()
    evt.OpenChest(8)
end)

RegisterEvent(90, "Legacy event 90", function()
    evt.OpenChest(9)
end)

RegisterEvent(91, "Legacy event 91", function()
    evt.OpenChest(10)
end)

RegisterEvent(92, "Legacy event 92", function()
    evt.OpenChest(11)
end)

RegisterEvent(93, "Legacy event 93", function()
    evt.OpenChest(12)
end)

RegisterEvent(94, "Legacy event 94", function()
    evt.OpenChest(13)
end)

RegisterEvent(95, "Legacy event 95", function()
    evt.OpenChest(14)
end)

RegisterEvent(96, "Legacy event 96", function()
    evt.OpenChest(15)
end)

RegisterEvent(97, "Legacy event 97", function()
    evt.OpenChest(16)
end)

RegisterEvent(98, "Legacy event 98", function()
    evt.OpenChest(17)
end)

RegisterEvent(99, "Legacy event 99", function()
    evt.OpenChest(18)
end)

RegisterEvent(100, "Legacy event 100", function()
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

