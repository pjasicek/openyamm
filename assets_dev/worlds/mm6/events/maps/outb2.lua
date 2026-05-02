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
    evt.EnterHouse(34) -- Stout Heart Staff and Spear
end, "You pray at the shrine.")

RegisterEvent(3, "You pray at the shrine.", nil, "You pray at the shrine.")

RegisterEvent(4, "Mail and Greaves", function()
    evt.EnterHouse(71) -- Mail and Greaves
end, "Mail and Greaves")

RegisterEvent(5, "Mail and Greaves", nil, "Mail and Greaves")

RegisterEvent(6, "Ty's Trinkets", function()
    evt.EnterHouse(106) -- Ty's Trinkets
end, "Ty's Trinkets")

RegisterEvent(7, "Ty's Trinkets", nil, "Ty's Trinkets")

RegisterEvent(8, "Outland Trading Post", function()
    evt.EnterHouse(1289) -- Outland Trading Post
end, "Outland Trading Post")

RegisterEvent(9, "Outland Trading Post", nil, "Outland Trading Post")

RegisterEvent(10, "Blackshire Coach and Buggy", function()
    evt.EnterHouse(478) -- Blackshire Coach and Buggy
end, "Blackshire Coach and Buggy")

RegisterEvent(11, "Blackshire Coach and Buggy", nil, "Blackshire Coach and Buggy")

RegisterEvent(12, "Blackshire Temple", function()
    evt.EnterHouse(327) -- Blackshire Temple
end, "Blackshire Temple")

RegisterEvent(13, "Wolf's Den", function()
    evt.EnterHouse(1588) -- Wolf's Den
end, "Wolf's Den")

RegisterEvent(14, "Wolf's Den", nil, "Wolf's Den")

RegisterEvent(15, "The Oasis", function()
    evt.EnterHouse(277) -- The Oasis
end, "The Oasis")

RegisterEvent(16, "The Oasis", nil, "The Oasis")

RegisterEvent(17, "The Howling Moon", function()
    evt.EnterHouse(278) -- The Howling Moon
end, "The Howling Moon")

RegisterEvent(18, "The Howling Moon", nil, "The Howling Moon")

RegisterEvent(19, "The Depository", function()
    evt.EnterHouse(302) -- The Depository
end, "The Depository")

RegisterEvent(20, "The Depository", nil, "The Depository")

RegisterEvent(21, "Adept Guild of Light", function()
    evt.EnterHouse(174) -- Adept Guild of Light
end, "Adept Guild of Light")

RegisterEvent(22, "Adept Guild of Light", nil, "Adept Guild of Light")

RegisterEvent(23, "Adept Guild of Dark", function()
    evt.EnterHouse(181) -- Adept Guild of Dark
end, "Adept Guild of Dark")

RegisterEvent(24, "Adept Guild of Dark", nil, "Adept Guild of Dark")

RegisterEvent(25, "Berserkers' Fury", function()
    evt.EnterHouse(202) -- Berserkers' Fury
end, "Berserkers' Fury")

RegisterEvent(26, "Berserkers' Fury", nil, "Berserkers' Fury")

RegisterEvent(27, "Smugglers' Guild", function()
    evt.EnterHouse(196) -- Smugglers' Guild
end, "Smugglers' Guild")

RegisterEvent(28, "Smugglers' Guild", nil, "Smugglers' Guild")

RegisterEvent(30, "Circus", function()
    if IsAtLeast(DayOfYear, 84) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 85) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 86) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 87) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 88) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 89) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 90) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 91) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 92) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 93) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 94) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 95) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 96) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 97) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 98) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 99) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 100) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 101) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 102) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 103) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 104) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 105) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 106) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 107) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 108) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 109) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 110) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 111) then
        evt.EnterHouse(1595) -- Circus
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Circus")

RegisterEvent(31, "+10 Magic permanent", function()
    if IsAtLeast(DayOfYear, 84) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 85) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 86) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 87) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 88) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 89) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 90) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 91) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 92) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 93) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 94) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 95) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 96) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 97) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 98) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 99) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 100) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 101) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 102) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 103) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 104) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 105) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 106) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 107) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 108) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 109) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 110) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 111) then
        evt.EnterHouse(1596) -- Tent
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "+10 Magic permanent")

RegisterEvent(32, "Tent", function()
    if IsAtLeast(DayOfYear, 84) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 85) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 86) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 87) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 88) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 89) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 90) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 91) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 92) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 93) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 94) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 95) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 96) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 97) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 98) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 99) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 100) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 101) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 102) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 103) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 104) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 105) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 106) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 107) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 108) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 109) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 110) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 111) then
        evt.EnterHouse(1598) -- Tent
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Tent")

RegisterEvent(33, "Tent", function()
    if IsAtLeast(DayOfYear, 84) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 85) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 86) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 87) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 88) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 89) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 90) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 91) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 92) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 93) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 94) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 95) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 96) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 97) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 98) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 99) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 100) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 101) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 102) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 103) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 104) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 105) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 106) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 107) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 108) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 109) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 110) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 111) then
        evt.EnterHouse(1601) -- Tent
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Tent")

RegisterEvent(34, "+3 Magic permanent", function()
    if IsAtLeast(DayOfYear, 84) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 85) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 86) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 87) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 88) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 89) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 90) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 91) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 92) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 93) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 94) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 95) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 96) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 97) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 98) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 99) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 100) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 101) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 102) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 103) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 104) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 105) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 106) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 107) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 108) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 109) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 110) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 111) then
        evt.EnterHouse(1597) -- Wagon
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "+3 Magic permanent")

RegisterEvent(35, "Wagon", function()
    if IsAtLeast(DayOfYear, 84) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 85) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 86) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 87) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 88) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 89) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 90) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 91) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 92) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 93) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 94) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 95) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 96) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 97) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 98) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 99) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 100) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 101) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 102) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 103) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 104) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 105) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 106) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 107) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 108) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 109) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 110) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 111) then
        evt.EnterHouse(1599) -- Wagon
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Wagon")

RegisterEvent(36, "Wagon", function()
    if IsAtLeast(DayOfYear, 84) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 85) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 86) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 87) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 88) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 89) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 90) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 91) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 92) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 93) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 94) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 95) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 96) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 97) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 98) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 99) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 100) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 101) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 102) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 103) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 104) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 105) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 106) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 107) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 108) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 109) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 110) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 111) then
        evt.EnterHouse(1600) -- Wagon
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Wagon")

RegisterEvent(50, "House", function()
    evt.EnterHouse(1264) -- House
end, "House")

RegisterEvent(51, "House", function()
    evt.EnterHouse(1279) -- House
end, "House")

RegisterEvent(52, "House", function()
    evt.EnterHouse(1294) -- House
end, "House")

RegisterEvent(53, "House", function()
    evt.EnterHouse(1307) -- House
end, "House")

RegisterEvent(54, "House", function()
    evt.EnterHouse(1319) -- House
end, "House")

RegisterEvent(55, "House", function()
    evt.EnterHouse(1330) -- House
end, "House")

RegisterEvent(56, "House", function()
    evt.EnterHouse(1342) -- House
end, "House")

RegisterEvent(57, "House", function()
    evt.EnterHouse(1354) -- House
end, "House")

RegisterEvent(58, "House", function()
    evt.EnterHouse(1365) -- House
end, "House")

RegisterEvent(59, "Legacy event 59", function()
    evt.EnterHouse(1376) -- House
end)

RegisterEvent(60, "Drink from Well.", function()
    evt.EnterHouse(1387) -- House
end, "Drink from Well.")

RegisterEvent(61, "+50 Luck temporary.", function()
    evt.EnterHouse(1397) -- House
end, "+50 Luck temporary.")

RegisterEvent(62, "+5 Magic resistance permanent.", function()
    evt.EnterHouse(1407) -- House
end, "+5 Magic resistance permanent.")

RegisterEvent(63, "House", function()
    evt.EnterHouse(1431) -- House
end, "House")

RegisterEvent(64, "House", function()
    evt.EnterHouse(1440) -- House
end, "House")

RegisterEvent(65, "House", function()
    evt.EnterHouse(1449) -- House
end, "House")

RegisterEvent(66, "House", function()
    evt.EnterHouse(1457) -- House
end, "House")

RegisterEvent(67, "House", function()
    evt.EnterHouse(1464) -- House
end, "House")

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

RegisterEvent(92, "Temple Baa", function()
    evt.EnterHouse(334) -- Temple Baa
end, "Temple Baa")

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

