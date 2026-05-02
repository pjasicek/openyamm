-- Plane of Air
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 2, 3, 4},
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

RegisterEvent(6, "Legacy event 6", function()
    if IsQBitSet(QBit(243)) then return end -- Got the heart of air
    evt.ForPlayer(Players.All)
    if HasItem(608) then -- Heart of Air
        SetQBit(QBit(243)) -- Got the heart of air
        AddValue(Experience, 100000)
        SetQBit(QBit(207)) -- Heart of Air - I lost it
    end
end)

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterNoOpEvent(10, "Legacy event 10")

RegisterEvent(11, "Wingsail's House", function()
    evt.EnterHouse(665) -- Wingsail's House
end, "Wingsail's House")

RegisterEvent(12, "Wingsail's House", nil, "Wingsail's House")

RegisterEvent(13, "Vapor's House", function()
    evt.EnterHouse(666) -- Vapor's House
end, "Vapor's House")

RegisterEvent(14, "Vapor's House", nil, "Vapor's House")

RegisterEvent(15, "Zephyr's House", function()
    evt.EnterHouse(667) -- Zephyr's House
end, "Zephyr's House")

RegisterEvent(16, "Zephyr's House", nil, "Zephyr's House")

RegisterEvent(17, "Empty House", function()
    evt.EnterHouse(668) -- Empty House
end, "Empty House")

RegisterEvent(18, "Empty House", nil, "Empty House")

RegisterEvent(19, "Empty House", function()
    evt.EnterHouse(669) -- Empty House
end, "Empty House")

RegisterEvent(20, "Empty House", nil, "Empty House")

RegisterEvent(21, "Empty House", function()
    evt.EnterHouse(670) -- Empty House
end, "Empty House")

RegisterEvent(22, "Empty House", nil, "Empty House")

RegisterEvent(23, "Empty House", function()
    evt.EnterHouse(671) -- Empty House
end, "Empty House")

RegisterEvent(24, "Empty House", nil, "Empty House")

RegisterEvent(25, "Nedlon's House", function()
    evt.EnterHouse(672) -- Nedlon's House
end, "Nedlon's House")

RegisterEvent(26, "Nedlon's House", nil, "Nedlon's House")

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

RegisterEvent(401, "Castle of Air", nil, "Castle of Air")

RegisterEvent(402, "Raven Man Nest", nil, "Raven Man Nest")

RegisterEvent(403, "Gate out of the Plane of Air", nil, "Gate out of the Plane of Air")

RegisterEvent(451, "Take a Drink", function()
    if not IsAtLeast(AirResistance, 10) then
        AddValue(AirResistance, 2)
        evt.StatusText("Air Resistance +10 (Permanent)")
        SetAutonote(229) -- Well in the Plane of Air gives a permanent Air Resistance bonus up to an Air Resistance of 10.
        return
    end
    evt.StatusText("Refreshing")
end, "Take a Drink")

RegisterEvent(501, "Enter the Castle of Air", function()
    evt.MoveToMap(-545, -2124, 0, 512, 0, 0, 373, 1, "d27.blv") -- Castle of Air
end, "Enter the Castle of Air")

RegisterEvent(505, "Leave the Plane of Air", function()
    evt.MoveToMap(-334, 21718, 385, 1536, 0, 0, 0, 1, "out07.odm") -- Murmurwoods
end, "Leave the Plane of Air")

