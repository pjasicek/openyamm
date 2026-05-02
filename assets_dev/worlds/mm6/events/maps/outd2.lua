-- Bootleg Bay
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {122},
    onLeave = {},
    openedChestIds = {
    [60] = {1},
    [61] = {2},
    [62] = {3},
    [63] = {4},
    [64] = {5},
    },
    textureNames = {},
    spriteNames = {"ped05"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(2, "Refreshing!", function()
    evt.EnterHouse(23) -- Hammer and Tongs
end, "Refreshing!")

RegisterEvent(3, "Refreshing!", nil, "Refreshing!")

RegisterEvent(4, "Pedestal", function()
    evt.EnterHouse(65) -- Abraham's Metalworks
end, "Pedestal")

RegisterEvent(5, "Pedestal", nil, "Pedestal")

RegisterEvent(6, "The Little Magic Shop", function()
    evt.EnterHouse(99) -- The Little Magic Shop
end, "The Little Magic Shop")

RegisterEvent(7, "The Little Magic Shop", nil, "The Little Magic Shop")

RegisterEvent(8, "Training-by-the-Sea", function()
    evt.EnterHouse(1587) -- Training-by-the-Sea
end, "Training-by-the-Sea")

RegisterEvent(9, "Training-by-the-Sea", nil, "Training-by-the-Sea")

RegisterEvent(10, "The Goblin's Tooth", function()
    evt.EnterHouse(266) -- The Goblin's Tooth
end, "The Goblin's Tooth")

RegisterEvent(11, "The Goblin's Tooth", nil, "The Goblin's Tooth")

RegisterEvent(12, "The Broken Cutlass", function()
    evt.EnterHouse(267) -- The Broken Cutlass
end, "The Broken Cutlass")

RegisterEvent(13, "The Broken Cutlass", nil, "The Broken Cutlass")

RegisterEvent(14, "Circus", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1595) -- Circus
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1595) -- Circus
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Circus")

RegisterEvent(15, "House of Healing", function()
    evt.EnterHouse(333) -- House of Healing
end, "House of Healing")

RegisterEvent(16, "Valkyrie", function()
    evt.EnterHouse(506) -- Valkyrie
end, "Valkyrie")

RegisterEvent(17, "Tsunami", function()
    evt.EnterHouse(505) -- Tsunami
end, "Tsunami")

RegisterEvent(18, "Obelisk", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1596) -- Tent
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1596) -- Tent
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Obelisk")

RegisterEvent(19, "Freehaven", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1598) -- Tent
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1598) -- Tent
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Freehaven")

RegisterEvent(20, "Tent", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1601) -- Tent
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1601) -- Tent
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Tent")

RegisterEvent(21, "Ironfist Castle", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1597) -- Wagon
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1597) -- Wagon
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Ironfist Castle")

RegisterEvent(22, "Circus (Winter)", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1599) -- Wagon
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1599) -- Wagon
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Circus (Winter)")

RegisterEvent(23, "Drink from Fountain", function()
    if IsAtLeast(DayOfYear, 308) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 309) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 310) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 311) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 312) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 313) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 314) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 315) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 316) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 317) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 318) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 319) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 320) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 321) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 322) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 323) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 324) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 325) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 326) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 327) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 328) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 329) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 330) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 331) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 332) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 333) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 334) then
        evt.EnterHouse(1600) -- Wagon
    elseif IsAtLeast(DayOfYear, 335) then
        evt.EnterHouse(1600) -- Wagon
    else
        evt.StatusText("No one is here.  The Circus has moved.")
        return
    end
end, "Drink from Fountain")

RegisterEvent(24, "Ironfist Castle", function()
    evt.StatusText("Ironfist Castle")
end, "Ironfist Castle")

RegisterEvent(25, "Freehaven", function()
    evt.StatusText("Freehaven")
end, "Freehaven")

RegisterEvent(26, "Circus (Winter)", function()
    evt.StatusText("Circus (Winter)")
end, "Circus (Winter)")

RegisterEvent(50, "House", function()
    evt.EnterHouse(1224) -- House
end, "House")

RegisterEvent(51, "House", function()
    evt.EnterHouse(1239) -- House
end, "House")

RegisterEvent(52, "House", function()
    evt.EnterHouse(1254) -- House
end, "House")

RegisterEvent(53, "House", function()
    evt.EnterHouse(1269) -- House
end, "House")

RegisterEvent(54, "House", function()
    evt.EnterHouse(1284) -- House
end, "House")

RegisterEvent(55, "House", function()
    evt.EnterHouse(1299) -- House
end, "House")

RegisterEvent(56, "House", function()
    evt.EnterHouse(1312) -- House
end, "House")

RegisterEvent(57, "House", function()
    evt.EnterHouse(1324) -- House
end, "House")

RegisterEvent(58, "House", function()
    evt.EnterHouse(1335) -- House
end, "House")

RegisterEvent(59, "House", function()
    evt.EnterHouse(1347) -- House
end, "House")

RegisterEvent(60, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(61, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(62, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(63, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(64, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(90, "Legacy event 90", function()
    evt.MoveToMap(-1792, -19, 1, 0, 0, 0, 172, 1, "6d04.blv")
end)

RegisterEvent(91, "Drink from Well.", function()
    evt.MoveToMap(0, -2231, 513, 512, 0, 0, 167, 1, "6t2.blv")
end, "Drink from Well.")

RegisterEvent(92, "Drink from Well.", function()
    evt.MoveToMap(-3258, 483, 49, 0, 0, 0, 173, 1, "6t4.blv")
end, "Drink from Well.")

RegisterEvent(93, "Drink from Well.", function()
    evt.MoveToMap(2817, -4748, -639, 512, 0, 0, 170, 1, "6t3.blv")
end, "Drink from Well.")

RegisterEvent(94, "Temple Baa", function()
    evt.EnterHouse(334) -- Temple Baa
end, "Temple Baa")

RegisterEvent(100, "Drink from Well.", function()
    if IsAtLeast(MightBonus, 20) then return end
    SetValue(MightBonus, 20)
    evt.StatusText("+20 Might temporary.")
    SetAutonote(410) -- 20 Points of temporary might from the well near the Goblin's Tooth in Bootleg Bay.
end, "Drink from Well.")

RegisterEvent(101, "Drink from Well.", function()
    evt.DamagePlayer(7, 2, 40)
    SetValue(PoisonedYellow, 1)
    evt.StatusText("Poison!")
end, "Drink from Well.")

RegisterEvent(102, "Drink from Fountain", function()
    if not IsAtLeast(BaseIntellect, 15) then
        if not IsAtLeast(MapVar(3), 1) then
            evt.StatusText("Refreshing!")
            return
        end
        SubtractValue(MapVar(3), 1)
        AddValue(BaseIntellect, 2)
        evt.StatusText("+2 Intellect permanent.")
        SetAutonote(411) -- 2 Points of permanent intellect from the north fountain in Bootleg Bay.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(103, "Drink from Fountain", function()
    if not IsAtLeast(BasePersonality, 15) then
        if not IsAtLeast(MapVar(4), 1) then
            evt.StatusText("Refreshing!")
            return
        end
        SubtractValue(MapVar(4), 1)
        AddValue(BasePersonality, 2)
        evt.StatusText("+2 Personality permanent.")
        SetAutonote(412) -- 2 Points of permanent personality from the south fountain in Bootleg Bay.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(104, "Legacy event 104", function()
    SetValue(MapVar(3), 8)
    SetValue(MapVar(4), 8)
end)

RegisterEvent(122, "Legacy event 122", function()
    if IsQBitSet(QBit(1250)) then -- NPC
        evt.SetSprite(347, 1, "ped05")
    end
end)

RegisterEvent(219, "Legacy event 219", function()
    SetValue(MapVar(11), 0)
end)

RegisterEvent(220, "Drink from Fountain of Magic", function()
    if IsQBitSet(QBit(1135)) then -- Drink from the Fountain of Magic and return to Lord Albert Newton in Mist. - NPC
        evt.SetNPCTopic(790, 1, 1371) -- Albert Newton topic 1: Wizards
        SetQBit(QBit(1260)) -- NPC
    end
    if not IsAtLeast(MaxSpellPoints, 0) then
        AddValue(CurrentSpellPoints, 20)
        evt.StatusText("+20 Spell points restored.")
        SetAutonote(400)
        return
    end
    evt.StatusText("Refreshing!")
    SetAutonote(400)
end, "Drink from Fountain of Magic")

RegisterEvent(221, "Pedestal", function()
    if not HasItem(2074) then return end -- Dragon Statuette
    RemoveItem(2074) -- Dragon Statuette
    evt.SetSprite(347, 1, "ped05")
    SetQBit(QBit(1250)) -- NPC
    if not IsQBitSet(QBit(1247)) then return end -- NPC
    if not IsQBitSet(QBit(1248)) then return end -- NPC
    if not IsQBitSet(QBit(1249)) then return end -- NPC
    if IsQBitSet(QBit(1246)) then -- NPC
        evt.MoveNPC(872, 0) -- Twillen -> removed
        evt.MoveNPC(826, 1342) -- Twillen -> House
    end
end, "Pedestal")

RegisterEvent(223, "Obelisk", function()
    evt.SimpleMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            d_re_e_Hpfotyhz_")
    SetQBit(QBit(1394)) -- NPC
    SetAutonote(452) -- Obelisk Message # 11: d_re_e_Hpfotyhz_
end, "Obelisk")

RegisterEvent(261, "Shrine of Might", function()
    if not IsAtLeast(MonthIs, 0) then
        evt.StatusText("You pray at the shrine.")
        return
    end
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1231)) then -- NPC
            SetQBit(QBit(1231)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(BaseMight, 10)
            evt.StatusText("+10 Might permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(BaseMight, 3)
        evt.StatusText("+3 Might permanent")
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Might")

