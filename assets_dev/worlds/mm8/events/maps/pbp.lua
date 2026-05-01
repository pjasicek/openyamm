-- Plane Between Planes
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

RegisterNoOpEvent(6, "Legacy event 6")

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterNoOpEvent(10, "Legacy event 10")

RegisterEvent(81, "Legacy event 81", function()
    evt.OpenChest(0)
    return
end)

RegisterEvent(82, "Legacy event 82", function()
    evt.OpenChest(1)
    return
end)

RegisterEvent(83, "Legacy event 83", function()
    evt.OpenChest(2)
    return
end)

RegisterEvent(84, "Legacy event 84", function()
    evt.OpenChest(3)
    return
end)

RegisterEvent(85, "Legacy event 85", function()
    evt.OpenChest(4)
    return
end)

RegisterEvent(86, "Legacy event 86", function()
    evt.OpenChest(5)
    return
end)

RegisterEvent(87, "Legacy event 87", function()
    evt.OpenChest(6)
    return
end)

RegisterEvent(88, "Legacy event 88", function()
    evt.OpenChest(7)
    return
end)

RegisterEvent(89, "Legacy event 89", function()
    evt.OpenChest(8)
    return
end)

RegisterEvent(90, "Legacy event 90", function()
    evt.OpenChest(9)
    return
end)

RegisterEvent(91, "Legacy event 91", function()
    evt.OpenChest(10)
    return
end)

RegisterEvent(92, "Legacy event 92", function()
    evt.OpenChest(11)
    return
end)

RegisterEvent(93, "Legacy event 93", function()
    evt.OpenChest(12)
    return
end)

RegisterEvent(94, "Legacy event 94", function()
    evt.OpenChest(13)
    return
end)

RegisterEvent(95, "Legacy event 95", function()
    evt.OpenChest(14)
    return
end)

RegisterEvent(96, "Legacy event 96", function()
    evt.OpenChest(15)
    return
end)

RegisterEvent(97, "Legacy event 97", function()
    evt.OpenChest(16)
    return
end)

RegisterEvent(98, "Legacy event 98", function()
    evt.OpenChest(17)
    return
end)

RegisterEvent(99, "Legacy event 99", function()
    evt.OpenChest(18)
    return
end)

RegisterEvent(100, "Legacy event 100", function()
    evt.OpenChest(19)
    return
end)

RegisterEvent(401, "Escaton's Palace", nil, "Escaton's Palace")

RegisterEvent(402, "Prison of the Air Lord", nil, "Prison of the Air Lord")

RegisterEvent(403, "Prison of the Earth Lord", nil, "Prison of the Earth Lord")

RegisterEvent(404, "Prison of the Fire Lord", nil, "Prison of the Fire Lord")

RegisterEvent(405, "Prison of the Water Lord", nil, "Prison of the Water Lord")

RegisterEvent(406, "Escaton's Crystal", nil, "Escaton's Crystal")

RegisterEvent(501, "Enter Escaton's Palace", function()
    evt.MoveToMap(-704, -5312, 1, 512, 0, 0, 218, 0, "d35.blv")
    return
end, "Enter Escaton's Palace")

RegisterEvent(502, "Enter the Prison of the Air Lord", function()
    evt.ForPlayer(Players.All)
    if not HasItem(629) then -- Ring of Keys
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.MoveToMap(-733, -2563, -1051, 960, 0, 0, 219, 0, "d36.blv")
    return
end, "Enter the Prison of the Air Lord")

RegisterEvent(503, "Enter the Prison of the Fire Lord", function()
    evt.ForPlayer(Players.All)
    if not HasItem(629) then -- Ring of Keys
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.MoveToMap(-128, 896, 1, 1536, 0, 0, 199, 1, "d37.blv")
    return
end, "Enter the Prison of the Fire Lord")

RegisterEvent(504, "Enter the Prison of the Water Lord", function()
    evt.ForPlayer(Players.All)
    if not HasItem(629) then -- Ring of Keys
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.MoveToMap(2393, -10664, 1, 520, 0, 0, 200, 1, "d38.blv")
    return
end, "Enter the Prison of the Water Lord")

RegisterEvent(505, "Enter the Prison of the Earth Lord", function()
    evt.ForPlayer(Players.All)
    if not HasItem(629) then -- Ring of Keys
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.MoveToMap(-2, 118, 1, 2047, 0, 0, 198, 1, "d39.blv")
    return
end, "Enter the Prison of the Earth Lord")

RegisterEvent(506, "Enter Escaton's Crystal", function()
    evt.MoveToMap(-14232, -2956, 800, 432, 0, 0, 0, 0, "D10.blv")
    return
end, "Enter Escaton's Crystal")

RegisterEvent(507, "A giant's sword", function()
    if not HasItem(634) then return end -- Flute
    evt.MoveToMap(19, -601, 1, 1552, 0, 0, 0, 0, "d50.blv")
    return
end, "A giant's sword")

