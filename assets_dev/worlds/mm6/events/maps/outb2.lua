-- Blackshire
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {213},
    onLeave = {},
    openedChestIds = {
    [68] = {1, 2},
    [69] = {3},
    [70] = {4},
    [71] = {5},
    [72] = {6},
    [73] = {8, 7, 9},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {6},
    timers = {
    { eventId = 210, repeating = true, intervalGameMinutes = 5, remainingGameMinutes = 5 },
    },
})

RegisterEvent(2, "You pray at the shrine.", function()
    evt.EnterHouse(34) -- Amulets of Power
end, "You pray at the shrine.")

RegisterEvent(3, "You pray at the shrine.", nil, "You pray at the shrine.")

RegisterEvent(4, "Placeholder", function()
    evt.EnterHouse(71) -- Placeholder
end, "Placeholder")

RegisterEvent(5, "Placeholder", nil, "Placeholder")

RegisterEvent(6, "Placeholder", function()
    evt.EnterHouse(106) -- Placeholder
end, "Placeholder")

RegisterEvent(7, "Placeholder", nil, "Placeholder")

RegisterEvent(8, "Legacy event 8", function()
    evt.EnterHouse(1289)
end)

RegisterEvent(9, "Legacy event 9", nil)

RegisterEvent(10, "House Understone", function()
    evt.EnterHouse(478) -- House Understone
end, "House Understone")

RegisterEvent(11, "House Understone", nil, "House Understone")

RegisterEvent(12, "Keldon's Cottage", function()
    evt.EnterHouse(327) -- Keldon's Cottage
end, "Keldon's Cottage")

RegisterEvent(13, "Legacy event 13", function()
    evt.EnterHouse(1588)
end)

RegisterEvent(14, "Legacy event 14", nil)

RegisterEvent(15, "Hostel", function()
    evt.EnterHouse(277) -- Hostel
end, "Hostel")

RegisterEvent(16, "Hostel", nil, "Hostel")

RegisterEvent(17, "Brigham's Home", function()
    evt.EnterHouse(278) -- Brigham's Home
end, "Brigham's Home")

RegisterEvent(18, "Brigham's Home", nil, "Brigham's Home")

RegisterEvent(19, "Watershed Cottage", function()
    evt.EnterHouse(302) -- Watershed Cottage
end, "Watershed Cottage")

RegisterEvent(20, "Watershed Cottage", nil, "Watershed Cottage")

RegisterEvent(21, "Wererat Smuggler Leader", function()
    evt.EnterHouse(174) -- Wererat Smuggler Leader
end, "Wererat Smuggler Leader")

RegisterEvent(22, "Wererat Smuggler Leader", nil, "Wererat Smuggler Leader")

RegisterEvent(23, "Dyson Leland's Room", function()
    evt.EnterHouse(181) -- Dyson Leland's Room
end, "Dyson Leland's Room")

RegisterEvent(24, "Dyson Leland's Room", nil, "Dyson Leland's Room")

RegisterEvent(25, "Dragon Hunter Camp", function()
    evt.EnterHouse(202) -- Dragon Hunter Camp
end, "Dragon Hunter Camp")

RegisterEvent(26, "Dragon Hunter Camp", nil, "Dragon Hunter Camp")

RegisterEvent(27, "Inside the Crystal", function()
    evt.EnterHouse(196) -- Inside the Crystal
end, "Inside the Crystal")

RegisterEvent(28, "Inside the Crystal", nil, "Inside the Crystal")

RegisterEvent(30, "Legacy event 30", function()
    if IsAtLeast(DayOfYear, 84) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 85) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 86) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 87) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 88) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 89) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 90) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 91) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 92) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 93) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 94) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 95) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 96) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 97) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 98) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 99) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 100) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 101) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 102) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 103) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 104) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 105) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 106) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 107) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 108) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 109) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 110) then
        evt.EnterHouse(1595)
    elseif IsAtLeast(DayOfYear, 111) then
        evt.EnterHouse(1595)
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end)

RegisterEvent(31, "+10 Magic permanent", function()
    if IsAtLeast(DayOfYear, 84) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 85) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 86) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 87) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 88) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 89) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 90) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 91) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 92) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 93) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 94) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 95) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 96) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 97) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 98) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 99) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 100) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 101) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 102) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 103) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 104) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 105) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 106) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 107) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 108) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 109) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 110) then
        evt.EnterHouse(1596)
    elseif IsAtLeast(DayOfYear, 111) then
        evt.EnterHouse(1596)
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "+10 Magic permanent")

RegisterEvent(32, "Legacy event 32", function()
    if IsAtLeast(DayOfYear, 84) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 85) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 86) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 87) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 88) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 89) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 90) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 91) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 92) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 93) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 94) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 95) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 96) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 97) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 98) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 99) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 100) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 101) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 102) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 103) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 104) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 105) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 106) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 107) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 108) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 109) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 110) then
        evt.EnterHouse(1598)
    elseif IsAtLeast(DayOfYear, 111) then
        evt.EnterHouse(1598)
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end)

RegisterEvent(33, "Legacy event 33", function()
    if IsAtLeast(DayOfYear, 84) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 85) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 86) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 87) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 88) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 89) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 90) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 91) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 92) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 93) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 94) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 95) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 96) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 97) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 98) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 99) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 100) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 101) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 102) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 103) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 104) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 105) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 106) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 107) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 108) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 109) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 110) then
        evt.EnterHouse(1601)
    elseif IsAtLeast(DayOfYear, 111) then
        evt.EnterHouse(1601)
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end)

RegisterEvent(34, "+3 Magic permanent", function()
    if IsAtLeast(DayOfYear, 84) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 85) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 86) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 87) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 88) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 89) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 90) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 91) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 92) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 93) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 94) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 95) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 96) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 97) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 98) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 99) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 100) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 101) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 102) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 103) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 104) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 105) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 106) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 107) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 108) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 109) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 110) then
        evt.EnterHouse(1597)
    elseif IsAtLeast(DayOfYear, 111) then
        evt.EnterHouse(1597)
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "+3 Magic permanent")

RegisterEvent(35, "Legacy event 35", function()
    if IsAtLeast(DayOfYear, 84) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 85) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 86) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 87) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 88) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 89) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 90) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 91) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 92) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 93) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 94) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 95) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 96) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 97) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 98) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 99) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 100) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 101) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 102) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 103) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 104) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 105) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 106) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 107) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 108) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 109) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 110) then
        evt.EnterHouse(1599)
    elseif IsAtLeast(DayOfYear, 111) then
        evt.EnterHouse(1599)
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end)

RegisterEvent(36, "Legacy event 36", function()
    if IsAtLeast(DayOfYear, 84) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 85) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 86) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 87) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 88) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 89) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 90) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 91) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 92) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 93) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 94) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 95) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 96) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 97) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 98) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 99) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 100) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 101) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 102) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 103) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 104) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 105) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 106) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 107) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 108) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 109) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 110) then
        evt.EnterHouse(1600)
    elseif IsAtLeast(DayOfYear, 111) then
        evt.EnterHouse(1600)
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end)

RegisterEvent(50, "Legacy event 50", function()
    evt.EnterHouse(1264)
end)

RegisterEvent(51, "Legacy event 51", function()
    evt.EnterHouse(1279)
end)

RegisterEvent(52, "Legacy event 52", function()
    evt.EnterHouse(1294)
end)

RegisterEvent(53, "Legacy event 53", function()
    evt.EnterHouse(1307)
end)

RegisterEvent(54, "Legacy event 54", function()
    evt.EnterHouse(1319)
end)

RegisterEvent(55, "Legacy event 55", function()
    evt.EnterHouse(1330)
end)

RegisterEvent(56, "Legacy event 56", function()
    evt.EnterHouse(1342)
end)

RegisterEvent(57, "Legacy event 57", function()
    evt.EnterHouse(1354)
end)

RegisterEvent(58, "Legacy event 58", function()
    evt.EnterHouse(1365)
end)

RegisterEvent(59, "Legacy event 59", function()
    evt.EnterHouse(1376)
end)

RegisterEvent(60, "Drink from Well.", function()
    evt.EnterHouse(1387)
end, "Drink from Well.")

RegisterEvent(61, "+50 Luck temporary.", function()
    evt.EnterHouse(1397)
end, "+50 Luck temporary.")

RegisterEvent(62, "+5 Magic resistance permanent.", function()
    evt.EnterHouse(1407)
end, "+5 Magic resistance permanent.")

RegisterEvent(63, "Legacy event 63", function()
    evt.EnterHouse(1431)
end)

RegisterEvent(64, "Legacy event 64", function()
    evt.EnterHouse(1440)
end)

RegisterEvent(65, "Legacy event 65", function()
    evt.EnterHouse(1449)
end)

RegisterEvent(66, "Legacy event 66", function()
    evt.EnterHouse(1457)
end)

RegisterEvent(67, "Legacy event 67", function()
    evt.EnterHouse(1464)
end)

RegisterEvent(68, "Chest", function()
    if not IsAtLeast(MapVar(3), 1) then
        if not IsQBitSet(QBit(1328)) then -- NPC
            SetValue(MapVar(3), 1)
            evt.OpenChest(1)
            SetQBit(QBit(1328)) -- NPC
            SetQBit(QBit(1206)) -- Quest item bits for seer
            return
        end
        evt.OpenChest(2)
    end
    evt.OpenChest(1)
    SetQBit(QBit(1328)) -- NPC
    SetQBit(QBit(1206)) -- Quest item bits for seer
end, "Chest")

RegisterEvent(69, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(70, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(71, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(72, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(73, "Chest", function()
    if not IsQBitSet(QBit(1245)) then -- NPC
        if not IsQBitSet(QBit(1244)) then -- NPC
            evt.OpenChest(8)
            return
        end
        if IsAtLeast(MapVar(4), 1) then
            evt.OpenChest(7)
            SetQBit(QBit(1251)) -- NPC
            return
        elseif IsQBitSet(QBit(1251)) then -- NPC
            evt.OpenChest(8)
        else
            SetValue(MapVar(4), 1)
            evt.OpenChest(7)
            SetQBit(QBit(1251)) -- NPC
        end
        return
    end
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(90, "Legacy event 90", function()
    evt.MoveToMap(-4158, 1792, 1233, 0, 0, 0, 181, 1, "6t8.blv")
end)

RegisterEvent(91, "Legacy event 91", function()
    evt.MoveToMap(-9600, 22127, 1, 512, 0, 0, 190, 1, "6d17.blv")
end)

RegisterEvent(92, "Hovel of Mist", function()
    evt.EnterHouse(334) -- Hovel of Mist
end, "Hovel of Mist")

RegisterEvent(100, "Drink from Well.", function()
    if IsAtLeast(LuckBonus, 50) then return end
    SetValue(LuckBonus, 50)
    evt.StatusText("+50 Luck temporary.")
    SetAutonote(429) -- 50 Points of temporary luck from the well in the north of Blackshire.
end, "Drink from Well.")

RegisterEvent(101, "Drink from Well.", function()
    if not IsPlayerBitSet(PlayerBit(65)) then
        SetPlayerBit(PlayerBit(65))
        AddValue(FireResistance, 5)
        SetValue(Unconscious, 0)
        evt.StatusText("+5 Magic resistance permanent.")
        SetAutonote(430) -- 5 Points of permanent magic resistance from the well in the southeast of Blackshire.
        return
    end
    SetValue(Unconscious, 0)
end, "Drink from Well.")

RegisterEvent(102, "Drink from Fountain", function()
    if not IsPlayerBitSet(PlayerBit(66)) then
        SetPlayerBit(PlayerBit(66))
        AddValue(BaseIntellect, 5)
        AddValue(BasePersonality, 5)
        SetValue(Unconscious, 0)
        evt.StatusText("+5 Intellect and Personality permanent.")
        SetAutonote(431) -- 5 Points of permanent intellect and personality from the fountain north of the Temple of the Snake.
        return
    end
    SetValue(Unconscious, 0)
end, "Drink from Fountain")

RegisterEvent(103, "Drink from Fountain", function()
    if not IsAtLeast(WaterResistanceBonus, 30) then
        SetValue(WaterResistanceBonus, 30)
        SetValue(MajorCondition, 0)
        evt.StatusText("+30 Magic resistance temporary.")
        SetAutonote(432) -- 30 Points of temporary magic resistance from the fountain in the south side of Blackshire.
        return
    end
    SetValue(MajorCondition, 0)
end, "Drink from Fountain")

RegisterEvent(104, "Drink from Fountain", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("Refreshing!")
        SetAutonote(433) -- 50 Spell points restored from the central fountain in Blackshire.
        return
    end
    SubtractValue(MapVar(2), 1)
    AddValue(CurrentSpellPoints, 50)
    evt.StatusText("+50 Spell points restored.")
    SetAutonote(433) -- 50 Spell points restored from the central fountain in Blackshire.
end, "Drink from Fountain")

RegisterEvent(210, "Legacy event 210", function()
    if IsQBitSet(QBit(1184)) then -- NPC
        return
    elseif IsAtLeast(IsFlying, 0) then
        evt.CastSpell(6, 5, 3, -17921, 9724, 2742, 0, 0, 0) -- Fireball
    else
        return
    end
end)

RegisterEvent(211, "Legacy event 211", function()
    evt.ForPlayer(Players.All)
    if IsQBitSet(QBit(1184)) then -- NPC
        return
    elseif HasItem(2106) then -- Dragon Tower Keys
        SetQBit(QBit(1184)) -- NPC
        evt.ShowMovie("t1swbu", true)
    else
        return
    end
end)

RegisterEvent(212, "Obelisk", function()
    evt.SimpleMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            hd_scawehSfdewee")
    SetQBit(QBit(1388)) -- NPC
    SetAutonote(446) -- Obelisk Message # 5: hd_scawehSfdewee
end, "Obelisk")

RegisterEvent(213, "Legacy event 213", function()
    if IsQBitSet(QBit(1184)) then -- NPC
    end
end)

RegisterEvent(261, "Shrine of Magic", function()
    if not IsAtLeast(MonthIs, 11) then
        evt.StatusText("You pray at the shrine.")
        return
    end
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1242)) then -- NPC
            SetQBit(QBit(1242)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(FireResistance, 10)
            evt.StatusText("+10 Magic permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(FireResistance, 3)
        evt.StatusText("+3 Magic permanent")
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Magic")

