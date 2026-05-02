-- Mire of the Damned
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {222},
    onLeave = {},
    openedChestIds = {
    [77] = {1},
    [78] = {2},
    [79] = {3},
    },
    textureNames = {},
    spriteNames = {"ped04"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(2, "No one is here.  The Circus has moved.", function()
    evt.EnterHouse(27) -- Blunt Trauma Weapons
end, "No one is here.  The Circus has moved.")

RegisterEvent(3, "No one is here.  The Circus has moved.", nil, "No one is here.  The Circus has moved.")

RegisterEvent(4, "Mailed fist Armory", function()
    evt.EnterHouse(66) -- Mailed fist Armory
end, "Mailed fist Armory")

RegisterEvent(5, "Mailed fist Armory", nil, "Mailed fist Armory")

RegisterEvent(6, "Smoke and Mirrors", function()
    evt.EnterHouse(102) -- Smoke and Mirrors
end, "Smoke and Mirrors")

RegisterEvent(7, "Smoke and Mirrors", nil, "Smoke and Mirrors")

RegisterEvent(8, "Darkmoor Travel", function()
    evt.EnterHouse(474) -- Darkmoor Travel
end, "Darkmoor Travel")

RegisterEvent(9, "Darkmoor Travel", nil, "Darkmoor Travel")

RegisterEvent(10, "The Haunt", function()
    evt.EnterHouse(270) -- The Haunt
end, "The Haunt")

RegisterEvent(11, "The Haunt", nil, "The Haunt")

RegisterEvent(12, "The Rusted Shield", function()
    evt.EnterHouse(271) -- The Rusted Shield
end, "The Rusted Shield")

RegisterEvent(13, "The Rusted Shield", nil, "The Rusted Shield")

RegisterEvent(14, "Circus", function()
    if IsAtLeast(DayOfYear, 196) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 197) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 198) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 199) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 200) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 201) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 202) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 203) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 204) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 205) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 206) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 207) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 208) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 209) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 210) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 211) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 212) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 213) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 214) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 215) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 216) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 217) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 218) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 219) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 220) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 221) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 222) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 223) then
        evt.EnterHouse(1595) -- Circus
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Circus")

RegisterEvent(15, "Tent", function()
    if IsAtLeast(DayOfYear, 196) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 197) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 198) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 199) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 200) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 201) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 202) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 203) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 204) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 205) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 206) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 207) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 208) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 209) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 210) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 211) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 212) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 213) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 214) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 215) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 216) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 217) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 218) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 219) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 220) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 221) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 222) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 223) then
        evt.EnterHouse(1596) -- Tent
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Tent")

RegisterEvent(16, "Tent", function()
    if IsAtLeast(DayOfYear, 196) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 197) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 198) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 199) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 200) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 201) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 202) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 203) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 204) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 205) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 206) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 207) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 208) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 209) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 210) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 211) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 212) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 213) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 214) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 215) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 216) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 217) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 218) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 219) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 220) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 221) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 222) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 223) then
        evt.EnterHouse(1598) -- Tent
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Tent")

RegisterEvent(17, "Tent", function()
    if IsAtLeast(DayOfYear, 196) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 197) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 198) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 199) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 200) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 201) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 202) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 203) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 204) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 205) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 206) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 207) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 208) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 209) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 210) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 211) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 212) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 213) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 214) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 215) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 216) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 217) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 218) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 219) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 220) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 221) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 222) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 223) then
        evt.EnterHouse(1601) -- Tent
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Tent")

RegisterEvent(18, "Wagon", function()
    if IsAtLeast(DayOfYear, 196) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 197) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 198) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 199) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 200) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 201) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 202) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 203) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 204) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 205) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 206) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 207) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 208) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 209) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 210) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 211) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 212) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 213) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 214) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 215) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 216) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 217) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 218) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 219) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 220) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 221) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 222) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 223) then
        evt.EnterHouse(1597) -- Wagon
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Wagon")

RegisterEvent(19, "Wagon", function()
    if IsAtLeast(DayOfYear, 196) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 197) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 198) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 199) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 200) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 201) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 202) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 203) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 204) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 205) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 206) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 207) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 208) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 209) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 210) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 211) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 212) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 213) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 214) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 215) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 216) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 217) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 218) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 219) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 220) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 221) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 222) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 223) then
        evt.EnterHouse(1599) -- Wagon
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Wagon")

RegisterEvent(20, "Wagon", function()
    if IsAtLeast(DayOfYear, 196) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 197) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 198) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 199) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 200) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 201) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 202) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 203) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 204) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 205) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 206) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 207) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 208) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 209) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 210) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 211) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 212) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 213) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 214) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 215) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 216) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 217) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 218) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 219) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 220) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 221) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 222) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 223) then
        evt.EnterHouse(1600) -- Wagon
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Wagon")

RegisterEvent(50, "House", function()
    evt.EnterHouse(1222) -- House
end, "House")

RegisterEvent(51, "House", function()
    evt.EnterHouse(1237) -- House
end, "House")

RegisterEvent(52, "House", function()
    evt.EnterHouse(1252) -- House
end, "House")

RegisterEvent(53, "House", function()
    evt.EnterHouse(1267) -- House
end, "House")

RegisterEvent(54, "House", function()
    evt.EnterHouse(1282) -- House
end, "House")

RegisterEvent(55, "House", function()
    evt.EnterHouse(1297) -- House
end, "House")

RegisterEvent(56, "House", function()
    evt.EnterHouse(1310) -- House
end, "House")

RegisterEvent(57, "House", function()
    evt.EnterHouse(1322) -- House
end, "House")

RegisterEvent(58, "House", function()
    evt.EnterHouse(1333) -- House
end, "House")

RegisterEvent(59, "House", function()
    evt.EnterHouse(1345) -- House
end, "House")

RegisterEvent(60, "House", function()
    evt.EnterHouse(1357) -- House
end, "House")

RegisterEvent(61, "House", function()
    evt.EnterHouse(1369) -- House
end, "House")

RegisterEvent(62, "House", function()
    evt.EnterHouse(1380) -- House
end, "House")

RegisterEvent(63, "House", function()
    evt.EnterHouse(1391) -- House
end, "House")

RegisterEvent(64, "House", function()
    evt.EnterHouse(1401) -- House
end, "House")

RegisterEvent(65, "House", function()
    evt.EnterHouse(1410) -- House
end, "House")

RegisterEvent(66, "House", function()
    evt.EnterHouse(1419) -- House
end, "House")

RegisterEvent(67, "House", function()
    evt.EnterHouse(1427) -- House
end, "House")

RegisterEvent(68, "House", function()
    evt.EnterHouse(1436) -- House
    evt.EnterHouse(1445) -- House
end, "House")

RegisterEvent(70, "House", function()
    evt.EnterHouse(1454) -- House
end, "House")

RegisterEvent(71, "House", function()
    evt.EnterHouse(1461) -- House
end, "House")

RegisterEvent(72, "House", function()
    evt.EnterHouse(1467) -- House
end, "House")

RegisterEvent(73, "House", function()
    evt.EnterHouse(1472) -- House
end, "House")

RegisterEvent(74, "House", function()
    evt.EnterHouse(1477) -- House
end, "House")

RegisterEvent(75, "House", function()
    evt.EnterHouse(1482) -- House
end, "House")

RegisterEvent(76, "House", function()
    evt.EnterHouse(1487) -- House
end, "House")

RegisterEvent(77, "Crate", function()
    evt.OpenChest(1)
end, "Crate")

RegisterEvent(78, "Crate", function()
    evt.OpenChest(2)
end, "Crate")

RegisterEvent(79, "Crate", function()
    evt.OpenChest(3)
end, "Crate")

RegisterEvent(90, "Legacy event 90", function()
    evt.MoveToMap(-3714, 1250, 1, 0, 0, 0, 182, 1, "6d09.blv")
end)

RegisterEvent(91, "Legacy event 91", function()
    evt.MoveToMap(21169, 1920, -689, 1024, 0, 0, 168, 1, "cd2.blv")
end)

RegisterEvent(92, "Temple Baa", function()
    evt.EnterHouse(334) -- Temple Baa
end, "Temple Baa")

RegisterEvent(93, "Dragon's Lair", function()
    evt.MoveToMap(-622, 239, 1, 128, 0, 0, 0, 0, "zddb01.blv")
end, "Dragon's Lair")

RegisterEvent(100, "Drink from Fountain", function()
    if not IsAtLeast(BaseEndurance, 15) then
        if not IsAtLeast(MapVar(6), 1) then
            evt.StatusText("Refreshing!")
            return
        end
        SubtractValue(MapVar(6), 1)
        AddValue(BaseEndurance, 2)
        evt.StatusText("+2 Endurance permenant.")
        SetAutonote(417) -- 2 Points of permanent endurance from the fountain in the south of the Mire of the Damned.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(210, "Legacy event 210", function()
    if IsAtLeast(MapVar(2), 1) then return end
    SetValue(MapVar(2), 1)
    evt.SummonMonsters(2, 3, 4, -304, 9904, 3000, 0, 0) -- encounter slot 2 "BHarpy" tier C, count 4, pos=(-304, 9904, 3000), actor group 0, no unique actor name
    evt.SummonMonsters(2, 3, 4, 480, 7904, 256, 0, 0) -- encounter slot 2 "BHarpy" tier C, count 4, pos=(480, 7904, 256), actor group 0, no unique actor name
    evt.SummonMonsters(2, 3, 4, -1200, 6480, 2500, 0, 0) -- encounter slot 2 "BHarpy" tier C, count 4, pos=(-1200, 6480, 2500), actor group 0, no unique actor name
    evt.SummonMonsters(2, 3, 4, -4336, 8552, 1750, 0, 0) -- encounter slot 2 "BHarpy" tier C, count 4, pos=(-4336, 8552, 1750), actor group 0, no unique actor name
    evt.SummonMonsters(2, 3, 4, -2784, 10000, 1945, 0, 0) -- encounter slot 2 "BHarpy" tier C, count 4, pos=(-2784, 10000, 1945), actor group 0, no unique actor name
end)

RegisterEvent(220, "Legacy event 220", function()
    if not IsAtLeast(MapVar(11), 1) then
        SetValue(MapVar(11), 1)
        evt.SetFacetBit(4, FacetBits.Invisible, 0)
        return
    end
    SetValue(MapVar(11), 0)
    evt.SetFacetBit(4, FacetBits.Invisible, 1)
end)

RegisterEvent(221, "Pedestal", function()
    if HasItem(2072) then -- Wolf Statuette
        RemoveItem(2072) -- Wolf Statuette
        evt.SetSprite(394, 1, "ped04")
        SetQBit(QBit(1249)) -- NPC
        if not IsQBitSet(QBit(1247)) then return end -- NPC
        if not IsQBitSet(QBit(1248)) then return end -- NPC
        if not IsQBitSet(QBit(1246)) then return end -- NPC
        if IsQBitSet(QBit(1250)) then -- NPC
            evt.MoveNPC(872, 0) -- Twillen -> removed
            evt.MoveNPC(826, 1342) -- Twillen -> House
        end
        return
    elseif HasItem(2073) then -- Eagle Statuette
        if not IsQBitSet(QBit(1248)) then return end -- NPC
        RemoveItem(2073) -- Eagle Statuette
        evt.SetSprite(394, 1, "ped04")
        SetQBit(QBit(1249)) -- NPC
        if not IsQBitSet(QBit(1247)) then return end -- NPC
        if not IsQBitSet(QBit(1248)) then return end -- NPC
        if not IsQBitSet(QBit(1246)) then return end -- NPC
        if IsQBitSet(QBit(1250)) then -- NPC
            evt.MoveNPC(872, 0) -- Twillen -> removed
            evt.MoveNPC(826, 1342) -- Twillen -> House
        end
        return
    else
        return
    end
end, "Pedestal")

RegisterEvent(222, "Legacy event 222", function()
    if IsQBitSet(QBit(1249)) then -- NPC
        evt.SetSprite(394, 1, "ped04")
    end
end)

RegisterEvent(223, "Obelisk", function()
    evt.SimpleMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            aoflo'h.hbtid_p_")
    SetQBit(QBit(1392)) -- NPC
    SetAutonote(450) -- Obelisk Message # 9: aoflo'h.hbtid_p_
end, "Obelisk")

RegisterEvent(261, "Shrine of Speed", function()
    if not IsAtLeast(MonthIs, 5) then
        evt.StatusText("You pray at the shrine.")
        return
    end
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1236)) then -- NPC
            SetQBit(QBit(1236)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(BaseSpeed, 10)
            evt.StatusText("+10 Speed permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(BaseSpeed, 3)
        evt.StatusText("+3 Speed permanent")
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Speed")

